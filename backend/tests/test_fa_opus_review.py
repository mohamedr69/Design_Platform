"""The Opus review and the force-fresh reread (platform owner, 5 October 2026).

- Opus, not Fable, is the configured reviewer, enabled and actually asked about
  every open item, shown the original drawing views and the evidence.
- Its outcome is applied only when the evidence it cites holds: present ->
  scheduled and out of Verification Required; absent / not an interface ->
  excluded from the counts, kept for traceability; unresolved -> left for the
  engineer with what to verify. A review that fails is said, never skipped.
- A force-fresh run reads an already-read drawing again, asks every look and
  review again, replaces the derived results whole (no duplicates, nothing
  stale), keeps the drawings and the engineer's decisions, and is never said
  complete when a drawing could not be read again.
A scripted provider stands in for the models: no model is called."""
from __future__ import annotations

import json

from app.ai import provider as P
from app.core.config import get_settings
from app.interfaces import findings, service, visual, workflow
from app.models import FaInterfaceRun, Project, ProjectFaInterfaces
from tests.test_fa_workflow import OPUS, _latest, _run, unresolved_finding, unresolved_item, w  # noqa: F401

settings = get_settings()
ALONE = "MSD"                  # a damper label with no damper symbol drawn near it: held as "no_symbol"


def _with_lone_label(w):
    """The plan of the fixture, and one more damper label far from any symbol:
    after the look it is held for verification (the open item under review)."""
    import ezdxf

    path = w.hvac / "VENTILATION LAYOUT.dxf"
    doc = ezdxf.readfile(path)
    doc.modelspace().add_text(ALONE, height=0.12).set_placement((719.25 + 30, 154.4))
    doc.saveas(path)


def _view(w) -> dict:
    return w.client.get(f"/projects/{w.pid}/fa-interfaces").json()


def _payload(request) -> dict:
    return json.loads(request.parts[0].text)


def _floor_keys(payload, letter="A") -> list[str]:
    e = next(e for e in payload["evidence"] if e["id"] == f"E-{letter}")
    names = set(e.get("proposed_floors") or [])
    return [f["key"] for f in payload["floors"] if f["name"] in names]


def _answer(outcome, refs=("V1",), confidence="high", qty=1, **kw):
    """Every item asked about answered `outcome`."""
    def answer(request):
        payload = _payload(request)
        return {"items": [{**unresolved_item(f["item"]), "outcome": outcome, "confidence": confidence,
                           "floor_keys": _floor_keys(payload, f["item"]) if outcome == "present" else [],
                           "qty_per_floor": qty if outcome == "present" else 0, "evidence_refs": list(refs),
                           "rationale": f"scripted {outcome}", "unclear": "", "engineer_action": "", **kw}
                          for f in payload["findings"]]}
    return answer


def _lone_item(view) -> dict | None:
    return next((g for g in view["verification"] + view["settled"] if "|no_symbol|" in g["id"]), None)


def _finding_requests(w):
    return [r for r in w.models.requests if r.task == findings.TASK]


def _fresh(w) -> dict:
    """A force-fresh run: an ordinary run reuses the stored answer on the same evidence."""
    w.db.expire_all()
    return workflow.run_workflow(w.db, w.db.get(Project, w.pid), fresh=True)


# --- Opus is the reviewer, enabled and actually asked ---------------------------------------------------------------


def test_opus_is_the_configured_reviewer_and_is_asked_about_each_open_item_with_the_drawing_views(w):
    assert settings.fa_orchestrator_model == settings.fa_findings_model == OPUS
    _with_lone_label(w)
    out = _run(w)
    asked = _finding_requests(w)
    assert len(asked) == 1                                                      # the one open item
    r = asked[0]
    assert (r.model, r.effort, r.exact_model) == (OPUS, "high", True)
    images = [p for p in r.parts if isinstance(p, P.ImagePart)]
    assert images and images[0].label == "V1"                                  # the original drawing, drawn
    ids = {e["id"] for e in _payload(r)["evidence"]}
    assert {"E-A", "M1", "V1", "C1"} <= ids                                    # reading, matrix, view, coverage
    assert _payload(r)["findings"][0]["kind"] == "motorized_smoke_fire_damper"
    assert out["findings_review"]["state"] == "completed"
    run = _latest(w)
    assert run["review"]["findings"]["model_requested"] == OPUS


def test_a_supported_present_finding_is_scheduled_and_leaves_verification(w):
    _with_lone_label(w)
    w.models.finding = unresolved_finding
    _run(w)
    before = _view(w)
    assert _lone_item(before) in before["verification"]
    w.models.finding = _answer("present")
    _fresh(w)
    after = _view(w)
    item = _lone_item(after)
    assert item["status"] == service.REVIEW_PRESENT and item not in after["verification"]
    assert item["review"]["outcome"] == "present" and item["review"]["evidence"][0]["id"] == "V1"
    added = [r for r in after["rows"] if r["id"].startswith(item["id"])]
    assert len(added) == 1 and added[0]["basis"] == "review" and added[0]["confidence"] == "Opus reviewed"
    # recalculated by the matrix rule: a damper is one control point, one relay module
    assert after["totals"]["items"] == before["totals"]["items"] + 1
    assert after["totals"]["control"] == before["totals"]["control"] + 1
    assert after["totals"]["module_qty"] == before["totals"]["module_qty"] + 1
    assert after["totals"]["to_verify"] == before["totals"]["to_verify"] - 1


def test_a_supported_not_applicable_finding_is_excluded_and_kept_for_traceability(w):
    _with_lone_label(w)
    w.models.finding = unresolved_finding
    _run(w)
    before = _view(w)
    w.models.finding = _answer("not_applicable", rationale="the ringed text is a door tag")
    _fresh(w)
    after = _view(w)
    item = _lone_item(after)
    assert item["status"] == service.REVIEW_EXCLUDED and item in after["settled"]
    assert item["review"]["rationale"] == "the ringed text is a door tag"
    assert after["totals"]["items"] == before["totals"]["items"]              # not counted
    assert after["totals"]["to_verify"] == before["totals"]["to_verify"] - 1  # no longer asked


def test_absence_is_accepted_only_with_a_view_shown_and_no_coverage_gap(w):
    _with_lone_label(w)
    w.models.finding = _answer("absent")
    _run(w)
    assert _lone_item(_view(w))["status"] == service.REVIEW_EXCLUDED
    # a file of the package that cannot be read could show it: absence is not established
    (w.hvac / "VENTILATION SHOP DRAWING.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    _run(w)
    item = _lone_item(_view(w))
    assert item["status"] == "open" and item["review"]["outcome"] == "unresolved"
    assert "coverage" in item["review"]["downgraded"] and "VENTILATION SHOP DRAWING.pdf" in item["review"]["unclear"]


def test_an_answer_that_cites_no_drawing_view_or_unknown_ids_is_not_accepted(w):
    _with_lone_label(w)
    w.models.finding = _answer("present", refs=("E-A", "V9"))                  # the reading only, and an id not given
    _run(w)
    item = _lone_item(_view(w))
    assert item["status"] == "open" and item["review"]["outcome"] == "unresolved"
    assert item["review"]["said"] == "present" and "V9" in item["review"]["unknown_refs"]
    assert not [r for r in _view(w)["rows"] if r["basis"] == "review"]


def test_an_inconclusive_finding_stays_for_the_engineer_with_what_to_verify(w):
    _with_lone_label(w)
    w.models.finding = lambda request: {"items": [{**unresolved_item(), "evidence_refs": ["V1", "C1"],
                                                   "unclear": "the ringed label has no symbol within 2 m",
                                                   "engineer_action": "check sheet M-07-V101 near the label for a damper"}]}
    out = _run(w)
    item = _lone_item(_view(w))
    assert item in _view(w)["verification"]
    assert item["review"]["unclear"] == "the ringed label has no symbol within 2 m"
    assert item["review"]["engineer_action"].startswith("check sheet M-07-V101")
    assert out["findings_review"]["state"] == "completed"                     # reviewed: unresolved is an outcome


def test_a_failed_review_is_said_on_the_item_and_keeps_the_run_provisional(w):
    _with_lone_label(w)
    w.models.finding_error = "timeout"
    out = _run(w)
    item = _lone_item(_view(w))
    assert item in _view(w)["verification"] and item["review"]["state"] == "failed"
    assert out["findings_review"]["state"] == "missing" and out["review_state"] == "partial"
    assert out["publication_state"] == "provisional"
    assert any("Opus review is partial" in r for r in out["publication_reasons"])
    # a Retry asks again about the item it could not review, and only that
    w.models.finding_error = None
    w.models.finding = _answer("not_applicable")
    w.db.expire_all()
    project = w.db.get(Project, w.pid)
    retried = workflow.run_retry(w.db, project, w.db.get(FaInterfaceRun, out["run_id"]))
    assert retried["findings_review"]["state"] == "completed"
    assert _lone_item(_view(w))["status"] == service.REVIEW_EXCLUDED


def test_without_the_model_every_item_is_said_not_reviewed(w, monkeypatch):
    _with_lone_label(w)
    w.models.serves = set()
    out = _run(w)
    held = _view(w)["verification"]                     # not looked at either: every damper label is held
    assert held and all(g["review"]["state"] == "unavailable" and "Not reviewed by Opus" in g["review"]["unclear"]
                        for g in held)
    assert out["findings_review"]["state"] == "missing"
    assert out["review_state"] == "missing" and out["publication_state"] == "provisional"


def test_fa_ai_enabled_switches_on_this_workflow_alone(w, monkeypatch):
    P.set_provider(None)
    monkeypatch.setattr(settings, "ai_enabled", False)
    monkeypatch.setattr(settings, "fa_ai_enabled", True)
    monkeypatch.setattr(P, "_fa_provider", w.models)
    assert isinstance(P.get_provider(), P.NullProvider)                       # the rest of the platform: off
    assert P.get_fa_provider() is w.models
    out = _run(w)
    assert [r for r in w.models.requests if r.task == visual.TASK]
    assert out["review_state"] == "completed"


# --- force-fresh --------------------------------------------------------------------------------------------------


def _reading(w) -> dict:
    w.db.expire_all()
    row = w.db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == w.pid).one()
    return next(e for e in row.sources if e.get("discipline") == "HVAC")


def test_a_fresh_run_reads_an_already_read_drawing_again_and_asks_every_look_again(w):
    _with_lone_label(w)
    _run(w)
    first = _reading(w)
    looks = len([r for r in w.models.requests if r.task == visual.TASK])
    asked = len(_finding_requests(w))
    _run(w)                                                                    # an ordinary run: nothing read again
    trace = _latest(w)["trace"]
    assert trace["reread"] == [] and any(x["why"] == "carried forward unchanged" for x in trace["not_reread"])
    assert len([r for r in w.models.requests if r.task == visual.TASK]) == looks
    w.db.expire_all()
    out = workflow.run_workflow(w.db, w.db.get(Project, w.pid), fresh=True)
    trace = _latest(w)["trace"]
    assert trace["fresh"] and first["relative_path"] in trace["reread"] and trace["not_reread"] == []
    assert _reading(w)["read_at"] != first["read_at"]                          # actually read again
    assert len([r for r in w.models.requests if r.task == visual.TASK]) > looks    # looked at again
    assert len(_finding_requests(w)) > asked + 0                               # reviewed again, not from the cache
    assert trace["complete"] is True and out["fresh"] is True
    assert trace["before"]["interface_lines"] is not None and trace["after"]["interface_lines"] is not None


def test_a_fresh_run_through_the_api_carries_fresh_to_the_job_and_the_run(w, monkeypatch):
    import app.routers.jobs as jobs_router

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    _run(w)
    started = w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/jobs?fresh=true").json()
    job = w.client.get(f"/jobs/{started['id']}").json()
    assert job["status"] == "succeeded", job
    assert job["result"]["fresh"] is True and _latest(w)["trace"]["fresh"] is True
    assert _latest(w)["trace"]["reread"]


def test_a_fresh_rebuild_replaces_the_derived_results_whole(w):
    _with_lone_label(w)
    w.models.finding = _answer("present")
    _run(w)
    assert [r for r in _view(w)["rows"] if r["basis"] == "review"]
    w.models.finding = unresolved_finding                                      # the fresh review settles nothing
    w.db.expire_all()
    workflow.run_workflow(w.db, w.db.get(Project, w.pid), fresh=True)
    view = _view(w)
    assert not [r for r in view["rows"] if r["basis"] == "review"]             # no stale finding from the last run
    assert _lone_item(view) in view["verification"]
    ids = [r["id"] for r in view["rows"]]
    assert len(ids) == len(set(ids))                                           # no duplicate rows
    w.db.expire_all()
    row = w.db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == w.pid).one()
    assert row.reviews["run_id"] == _latest(w)["run_id"] and row.reviews["fresh"] is True
    assert set(row.reviews["items"]) <= {g["id"] for g in view["verification"] + view["settled"]}


def test_a_fresh_run_keeps_the_drawings_and_the_engineers_decisions_and_says_where_they_disagree(w):
    _with_lone_label(w)
    w.models.finding = _answer("not_applicable")
    _run(w)
    item = _lone_item(_view(w))
    floor = item["proposed_floor_keys"][0]
    r = w.client.post(f"/projects/{w.pid}/fa-interfaces/decisions",
                      json={"id": item["id"], "action": "resolve", "floor_keys": [floor], "qty": 1})
    assert r.status_code == 200, r.text
    orphan = "HVAC|03- Drawings/IFC/Mechanical/HVAC/VENTILATION LAYOUT.dxf|verify|GONE|no_symbol|motorized_smoke_fire_damper"
    w.db.expire_all()
    row = w.db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == w.pid).one()
    row.decisions = {**row.decisions, orphan: {"status": "dismissed", "reason": "old"}}
    w.db.commit()
    view = _view(w)
    clash = _lone_item(view)
    assert clash["status"] == "resolved" and "engineer's answer stands" in clash["review_conflict"]
    assert any(c["id"] == item["id"] for c in view["decision_conflicts"])
    drawing = (w.hvac / "VENTILATION LAYOUT.dxf").read_bytes()
    decisions = dict(row.decisions)
    w.db.expire_all()
    workflow.run_workflow(w.db, w.db.get(Project, w.pid), fresh=True)
    assert (w.hvac / "VENTILATION LAYOUT.dxf").read_bytes() == drawing        # the drawing untouched
    w.db.expire_all()
    row = w.db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == w.pid).one()
    assert {k: {kk: vv for kk, vv in v.items()} for k, v in row.decisions.items()} == decisions
    view = _view(w)
    assert _lone_item(view)["status"] == "resolved"                            # the engineer's answer stands
    assert any(c["id"] == orphan and "no longer give" in c["conflict"] for c in view["decision_conflicts"])
    assert any(c["id"] == orphan for c in _latest(w)["trace"]["decision_conflicts"])


def test_a_fresh_run_that_cannot_read_a_drawing_again_is_never_said_complete(w):
    _run(w)
    (w.hvac / "VENTILATION LAYOUT.dxf").write_bytes(b"not a drawing")       # the drawing now cannot be read
    w.db.expire_all()
    out = workflow.run_workflow(w.db, w.db.get(Project, w.pid), fresh=True)
    trace = _latest(w)["trace"]
    assert trace["complete"] is False and trace["not_reread"]
    assert any("VENTILATION LAYOUT.dxf" in x for x in trace["incomplete"])
    assert out["publication_state"] == "provisional"
    assert any("fresh reread is incomplete" in r for r in out["publication_reasons"])
