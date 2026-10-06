"""Regression tests for the FI-P1 implementation review's findings F1-F13
(docs/milestones/fa-interfaces/FI-P1-IMPL-REVIEW/REVIEW.md). Each was first
reproduced on the reviewed commit; these assert the corrected behaviour.
The orchestrator stand-in agrees with everything and recommends
complete_candidate unless a test says otherwise, so what refuses publication
here is deterministic code, never the orchestrator. No model is called."""
from __future__ import annotations

import json
import threading
from types import SimpleNamespace

import ezdxf
import pytest

from app.ai import provider as P
from app.core.config import get_settings
from app.interfaces import evidence, scan, service, visual, workflow
from app.models import BackgroundJob, FaInterfaceRun, Project, ProjectFaInterfaces
from tests.conftest import login
from tests.test_fa_cases import LANDMARK_WORDS, _floors, _gate_layout, _read, _sheet, gb  # noqa: F401  (fixture)
from tests.test_fa_workflow import (OPUS, UNSERVED, Models, _ask_with_window, _damper_drawing, _latest,  # noqa: F401
                                    _ok_review, _run, w)

settings = get_settings()


def _row(w):
    w.db.expire_all()
    return w.db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == w.pid).one()


def _accept(w, run_id):
    return w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/{run_id}/accept")


def _ff(w):
    ff = w.root / "03- Drawings" / "IFC" / "Mechanical" / "FF"
    ff.mkdir(parents=True, exist_ok=True)
    return ff


# --- F1: deterministic acceptance ------------------------------------------------------------------------------


def test_F1_a_corrupt_drawing_keeps_the_run_provisional_and_accept_is_refused(w):
    (_ff(w) / "FF LAYOUT.dxf").write_text("this is not a dxf\n")
    out = _run(w)
    run = _latest(w)
    assert run["review_state"] == "completed"                                 # the reviewer agreed with everything
    assert out["publication_state"] == "provisional"
    assert any("failed" in r and "FF LAYOUT.dxf" in r for r in run["publication_reasons"])
    r = _accept(w, run["run_id"])
    assert r.status_code == 422 and "provisional" in r.json()["detail"]
    assert _row(w).published is None


def test_F1_every_drawing_failed_is_never_an_empty_published_schedule(w):
    (w.hvac / "VENTILATION LAYOUT.dxf").write_text("not a dxf\n")
    out = _run(w)
    run = _latest(w)
    assert out["publication_state"] == "provisional"
    assert any("nothing is read and current" in r for r in run["publication_reasons"])
    assert _accept(w, run["run_id"]).status_code == 422
    assert _row(w).published is None


def test_F1_an_unread_cloud_only_drawing_blocks_acceptance(w, monkeypatch):
    _damper_drawing(_ff(w) / "FF LAYOUT.dxf")
    monkeypatch.setattr(settings, "fa_read_cloud_only_files", False)
    monkeypatch.setattr(evidence, "file_attributes",
                        lambda path, st: evidence.ATTR_RECALL_ON_DATA_ACCESS if "FF LAYOUT" in path else 0)
    out = _run(w)
    run = _latest(w)
    assert out["publication_state"] == "provisional"
    assert any("unread (not_synced)" in r for r in run["publication_reasons"])
    assert _accept(w, run["run_id"]).status_code == 422


def test_F1_a_candidate_is_checked_again_at_accept_a_drawing_that_failed_since_refuses_it(w):
    out = _run(w)
    assert out["publication_state"] == "complete_candidate"
    run_id = _latest(w)["run_id"]
    # after the run: a new drawing appears in the folder and is not read
    _damper_drawing(_ff(w) / "FF LAYOUT.dxf")
    r = _accept(w, run_id)
    assert r.status_code == 422 and "not read and current" in r.json()["detail"]
    after = _latest(w)
    assert after["publication_state"] == "provisional" and after["publication_reasons"]
    assert _row(w).published is None


def test_F1_an_unreachable_folder_at_accept_refuses_with_its_reason(w):
    _run(w)
    run_id = _latest(w)["run_id"]
    w.root.rename(w.root.with_name("moved away"))
    r = _accept(w, run_id)
    assert r.status_code == 422 and "not reachable" in r.json()["detail"]
    assert _row(w).published is None


def test_F1_a_drawing_whose_look_was_not_possible_is_partial_coverage_and_blocks(w, monkeypatch):
    monkeypatch.setattr(settings, "drawing_review_model", UNSERVED)            # the look cannot run
    out = _run(w)
    run = _latest(w)
    assert run["review_state"] == "completed" and out["publication_state"] == "provisional"
    assert any("unsupported" in r for r in run["publication_reasons"])
    assert _accept(w, run["run_id"]).status_code == 422


def test_F1_a_complete_reviewed_run_is_still_accepted(w):
    _run(w)
    run = _latest(w)
    assert run["publication_state"] == "complete_candidate" and run["publication_reasons"] == []
    assert _accept(w, run["run_id"]).status_code == 200
    assert _row(w).published_basis == "run_accepted"


# --- F2: never gate points from the fire alarm IFC drawing -------------------------------------------------------


def test_F2_the_fire_alarm_ifc_drawing_gives_no_gate_barrier_interfaces(tmp_path):
    result = scan.read(str(_gate_layout(tmp_path / "fa.dxf")), "ARCH")
    assert [it for it in result["items"] if it["kind"] == "instance"]           # the drawing has the cable notes
    src = {"discipline": "ARCH", "kind": "fa_ifc", "relative_path": "FA.dwg", "filename": "FIRE ALARM LAYOUT.dwg",
           "revision": "R0", "status": "read", "result": result}

    class F:
        registry, unregistered = {}, {}
        def of_title(self, t): return ["GF"] if "GROUND" in (t or "") else []
        def note(self, k, w): pass
        def name(self, k): return k
        def order(self, k): return (0, k)
    equipment, groups, conflicts = [], [], []
    service._read_source(src, F(), equipment, groups, conflicts, [], {}, service.Schedule([], F()))
    assert not [e for e in equipment if e.get("gate")]
    rows, _g = service._gate_rows([e for e in equipment if e.get("gate")], F(), conflicts, {})
    assert rows == []
    # what it names is held for the engineer, not counted
    assert any(g["key"] == "gate_barrier" and g["proposed_qty"] is None for g in groups)


def test_F2_a_gate_barrier_package_drawing_still_gives_its_two_interfaces(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    view = _read(gb)
    assert sorted(r["role"] for r in view["rows"] if r["key"] == "gate_barrier") == ["entry", "exit"]


# --- F3: a governing-drawing choice can be reopened and corrected, its history kept --------------------------------


def _shop(gb):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for text, x, y in LANDMARK_WORDS:
        msp.add_text(text, height=0.2).set_placement((x, y))
    for x, y in ((1190.57, 175.95), (1195.76, 175.76), (1174.72, 162.55), (1172.33, 166.59)):
        msp.add_text("FIRE ALARM CABLE", height=0.12).set_placement((x, y))
    _sheet(doc, "BGF", "GROUND FLOOR PLAN GATEBARRIER SYSTEM LAYOUT", (1182.99, 142.21), 96.95)
    doc.saveas(gb.folder / "Shop Drawings-Titania rev01.dxf")


def _decide(gb, **body):
    return gb.client.post(f"/projects/{gb.pid}/fa-interfaces/decisions", json=body)


def test_F3_a_wrong_govern_is_reopened_and_corrected_with_its_history_kept(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _shop(gb)
    view = _read(gb)
    (conflict,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    # the evidence is there to weigh: every drawing's connection points with their lane roles
    by_points = {d["points"]: d for d in conflict["drawings"]}
    assert sorted(p["role"] for p in by_points[2]["connection_points"]) == ["entry", "exit"]
    assert all(p["settled"] for p in by_points[2]["connection_points"])
    shop, layout = by_points[4]["relative_path"], by_points[2]["relative_path"]
    wrong = _decide(gb, id=conflict["id"], action="govern", relative_path=shop, reason="oops",
                    authority="engineer's mistake").json()
    assert conflict["id"] in {g["id"] for g in wrong["settled"]}               # still listed after the choice
    reopened = _decide(gb, id=conflict["id"], action="reopen", reason="wrong drawing chosen")
    assert reopened.status_code == 200
    body = reopened.json()
    assert not [r for r in body["rows"] if r["key"] == "gate_barrier"]       # held again: nothing counted
    (held,) = [g for g in body["verification"] if g["id"] == conflict["id"]]
    assert [h["status"] for h in held["history"]] == ["governed"]            # the wrong choice is kept
    fixed = _decide(gb, id=conflict["id"], action="govern", relative_path=layout,
                    reason="The IFC layout is the issued design", authority="Consultant RFI-017 reply").json()
    assert sorted(r["role"] for r in fixed["rows"] if r["key"] == "gate_barrier") == ["entry", "exit"]
    (kept,) = [g for g in fixed["settled"] if g["id"] == conflict["id"]]
    assert [h["status"] for h in kept["history"]] == ["governed", "open"]
    decisions = gb.db.query(ProjectFaInterfaces).filter_by(project_id=gb.pid).one().decisions
    gb.db.expire_all()
    assert decisions[conflict["id"]]["authority"] == "Consultant RFI-017 reply"


def test_F3_govern_needs_a_reason_and_its_authority(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _shop(gb)
    view = _read(gb)
    (conflict,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    layout = next(d["relative_path"] for d in conflict["drawings"] if d["points"] == 2)
    assert _decide(gb, id=conflict["id"], action="govern", relative_path=layout, reason="x").status_code == 422
    assert _decide(gb, id=conflict["id"], action="govern", relative_path=layout, authority="x").status_code == 422
    assert _decide(gb, id=conflict["id"], action="govern", relative_path="other.dwg", reason="x",
                   authority="y").status_code == 422


def test_F3_reopening_any_answer_keeps_what_was_decided(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    view = _read(gb)
    (line,) = [r for r in view["rows"] if r["key"] == "gate_barrier" and r["role"] == "entry"]
    _decide(gb, id=line["id"], action="reject", reason="not ours")
    restored = _decide(gb, id=line["id"], action="restore").json()
    assert line["id"] in {r["id"] for r in restored["rows"]}
    gb.db.expire_all()
    d = gb.db.query(ProjectFaInterfaces).filter_by(project_id=gb.pid).one().decisions[line["id"]]
    assert d["status"] == "restored" and [h["status"] for h in d["history"]] == ["rejected"]


# --- F4: the packages' review lowers the run --------------------------------------------------------------------


@pytest.mark.parametrize("signal", ["do_not_publish", "dispute", "rework", "suspect"])
def test_F4_a_package_level_signal_lowers_the_run_whatever_the_run_level_says(w, signal):
    def review(request):
        a = _ok_review(request)                                              # FP2 still recommends complete_candidate
        if request.parts[0].label.startswith("package_review"):
            if signal == "do_not_publish":
                a["publication_recommendation"] = "do_not_publish"
            elif signal == "dispute":
                a["coverage_assessment"] = [{**c, "verdict": "dispute", "reason": "a layout unread"}
                                            for c in a["coverage_assessment"]]
            elif signal == "rework":
                a["rework_requests"] = [{"source_id": c["source_id"], "reason": "read again"}
                                        for c in a["coverage_assessment"]]
            else:
                a["missing_or_suspect"] = [{"package": "HVAC", "issue": "coverage_gap", "detail": "a floor missing"}]
        return a
    w.models.review = review
    out = _run(w)
    run = _latest(w)
    assert out["review_state"] == "completed" and out["publication_state"] == "provisional"
    assert any("package HVAC" in r for r in run["publication_reasons"])
    assert _accept(w, run["run_id"]).status_code == 422


# --- F5: an accepted run is final -------------------------------------------------------------------------------


def test_F5_an_accepted_run_cannot_be_retried_or_accepted_again(w, monkeypatch):
    from app.routers import jobs as jobs_router

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    _run(w)
    run = _latest(w)
    assert _accept(w, run["run_id"]).status_code == 200
    again = w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/{run['run_id']}/retry-review")
    assert again.status_code == 422 and "accepted" in again.json()["detail"]
    second = _accept(w, run["run_id"])
    assert second.status_code == 422 and "already accepted" in second.json()["detail"]


# --- F6: a malformed orchestrator answer is an invalid output, not a crash ---------------------------------------


@pytest.mark.parametrize("bad", [
    {"coverage_assessment": ["not an object"]},
    {"coverage_assessment": [{"source_id": 3, "verdict": "agree", "reason": "x"}]},
    {"publication_recommendation": "publish_now"},
    {"open_questions": "not a list"},
])
def test_F6_a_malformed_answer_is_invalid_output_retried_once_never_cached_and_the_run_completes(w, bad):
    def review(request):
        return {**_ok_review(request), **bad}
    w.models.review = review
    out = _run(w)                                                             # no exception
    run = _latest(w)
    assert run["status"] == "completed" and out["review_state"] == "missing"
    assert out["publication_state"] == "provisional"
    assert run["review"]["fp2"]["state"] == "failed" and run["review"]["fp2"]["reason"].startswith("invalid_output")
    asked = [r for r in w.models.requests if r.task == workflow.TASK_REVIEW]
    assert len(asked) == 4                                                    # FP1 and FP2, each retried once
    # nothing malformed was kept: the next run asks again
    _run(w)
    assert len([r for r in w.models.requests if r.task == workflow.TASK_REVIEW]) == 8


# --- F7: one frame on every floor, and label-only items paired before a union -------------------------------------


def _union(view_b=None, offset=0.0, symbol=True):
    lm = {"MAIN ENTRANCE": [1147.48, 170.49], "FIRE EXIT": [1194.81, 161.03], "RMU ROOM": [1168.47, 166.72]}
    va = [{"name": "S", "windows": [[733.0, 135.3, 130.0, 97.0, 0.0, 0.0, 0.0]]}]
    vb = [{"name": "S", "windows": [view_b or [733.0, 135.3, 130.0, 97.0, 0.0, 0.0, 0.0]]}]
    sm = {"discipline": "SM", "relative_path": "SMOKE.dwg", "result": {"units": "m", "landmarks": lm, "sheets": va}}
    hv = {"discipline": "HVAC", "relative_path": "VENT.dwg", "result": {"units": "m", "landmarks": dict(lm), "sheets": vb}}

    def e(src, x, label):
        out = {"key": "motorized_smoke_fire_damper", "tag": None, "keys": ["B3"], "src": src, "label": label,
               "ref": "S", "sheet": "S", "detail": "", "text": "MSD", "confidence": "high", "anchor": (x, 150.0),
               "count": 1, "label_anchor": [x, 150.0], "radius": 0.97}
        if symbol:
            out.update({"equipment_anchor": [700.2, 149.8], "location_state": "symbol", "visual": True})
        return out
    held: list = []
    rows = service._equipment_rows([e(sm, 700.0, "SMOKE.dwg"), e(hv, 700.0 + offset, "VENT.dwg")], _floors(), [],
                                   service.Schedule([], _floors()), held)
    return rows, held


def test_F7_one_damper_on_both_aligned_drawings_with_the_same_view_counts_once():
    rows, held = _union()
    assert len(rows) == 1 and held == []


def test_F7_a_floor_whose_sheets_view_different_model_space_is_held():
    rows, held = _union(view_b=[760.0, 135.3, 130.0, 97.0, 0.0, 0.0, 0.0])
    assert rows == [] and held[0]["why"] == "views"
    (group,) = service._conflict_groups(held, _floors())
    assert "do not view the same piece" in group["reason"]


def test_F7_items_placed_by_label_only_that_do_not_pair_are_held_not_counted_twice():
    rows, held = _union(offset=0.8, symbol=False)
    assert rows == [] and held[0]["why"] == "positions"
    rows, held = _union(offset=0.1, symbol=False)                            # they pair: counted once
    assert len(rows) == 1 and held == []


def test_F7_door_tags_the_look_set_aside_never_hold_a_floor_of_dampers_on_symbols():
    """EP-30880 B3: both drawings show the MSDs on their symbols, and "SD" door tags the
    look called not dampers (no symbol of their own): the dampers are their union."""
    lm = {"MAIN ENTRANCE": [1147.48, 170.49], "FIRE EXIT": [1194.81, 161.03], "RMU ROOM": [1168.47, 166.72]}
    view = [{"name": "S", "windows": [[733.0, 135.3, 130.0, 97.0, 0.0, 0.0, 0.0]]}]
    sm = {"discipline": "SM", "relative_path": "SMOKE.dwg", "result": {"units": "m", "landmarks": lm, "sheets": view}}
    hv = {"discipline": "HVAC", "relative_path": "VENT.dwg", "result": {"units": "m", "landmarks": lm, "sheets": view}}

    def e(src, x, label, *, door=False):
        out = {"key": "motorized_smoke_fire_damper", "tag": None, "keys": ["B3"], "src": src, "label": label,
               "ref": "S", "sheet": "S", "detail": "", "text": "SD" if door else "MSD", "confidence": "high",
               "anchor": (x, 150.0), "count": 1, "label_anchor": [x, 150.0], "radius": 0.97}
        if door:
            out.update({"visual_reject": "door tag", "location_state": "label_only"})
        else:
            out.update({"equipment_anchor": [x + 0.2, 149.8], "location_state": "symbol", "visual": True})
        return out
    held: list = []
    rows = service._equipment_rows([e(sm, 700.0, "SMOKE.dwg"), e(sm, 690.0, "SMOKE.dwg", door=True),
                                    e(hv, 700.0, "VENT.dwg"), e(hv, 710.0, "VENT.dwg"),
                                    e(hv, 695.0, "VENT.dwg", door=True)],
                                   _floors(), [], service.Schedule([], _floors()), held)
    assert held == []
    counted = [r for r in rows if not r.get("visual_reject")]
    assert len(counted) == 2 and len([r for r in rows if r.get("visual_reject")]) == 2


def test_F7_a_reading_records_each_sheets_viewport_windows(tmp_path):
    _damper_drawing(tmp_path / "v.dxf")
    result = scan.read(str(tmp_path / "v.dxf"), "HVAC")
    (sheet,) = result["sheets"]
    assert result["scan_version"] == "5" and len(sheet["windows"]) == 1 and len(sheet["windows"][0]) == 7


# --- F8: Retry review is a job, on the frozen inputs, bounded atomically -------------------------------------------


def test_F8_retry_is_a_job_that_sends_exactly_the_frozen_inputs(w, monkeypatch):
    from app.routers.ifc_boq import _run_inline

    w.models.review_error = "unavailable"                                   # the review could not run
    _run(w)
    run = _latest(w)
    w.db.expire_all()
    frozen = w.db.get(FaInterfaceRun, run["run_id"]).review_inputs
    # the engineer's answers change the schedule meanwhile; the retry still reviews what the run was
    held = w.client.get(f"/projects/{w.pid}/fa-interfaces").json()["verification"]
    if held:
        w.client.post(f"/projects/{w.pid}/fa-interfaces/decisions",
                      json={"id": held[0]["id"], "action": "dismiss", "reason": "not ours"})
    w.models.review_error = None
    before = len(w.models.requests)
    queued = w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/{run['run_id']}/retry-review")
    assert queued.status_code == 202 and queued.json()["kind"] == "fa_interfaces_review"
    assert len(w.models.requests) == before                                 # nothing asked inside the request
    _run_inline(queued.json()["id"])
    sent = {q.parts[0].label: json.loads(q.parts[0].text) for q in w.models.requests[before:]}
    assert sent["package_review:HVAC"] == frozen["packages"]["HVAC"]
    assert {k: sent["run_review"][k] for k in frozen["view"]} == frozen["view"]
    assert _latest(w)["review_state"] == "completed"


def test_F8_the_daily_retry_bound_is_claimed_by_compare_and_set(w, monkeypatch):
    monkeypatch.setattr(settings, "fa_orchestrator_retries_per_day", 3)
    w.models.review_error = "unavailable"
    _run(w)
    w.db.expire_all()
    project = w.db.get(Project, w.pid)
    run = w.db.get(FaInterfaceRun, _latest(w)["run_id"])
    stale = SimpleNamespace(**{c: getattr(run, c) for c in ("id", "publication_state", "status", "review_state",
                                                           "sources_digest", "review_retries", "review_retry_day")})
    workflow.claim_retry(w.db, project, run)                                 # takes one
    with pytest.raises(ValueError, match="same moment"):
        workflow.claim_retry(w.db, project, stale)                           # a request that read the old count
    w.db.expire_all()
    assert w.db.get(FaInterfaceRun, run.id).review_retries == 1


def test_F8_a_retry_while_a_read_runs_is_refused(w):
    _run(w)
    run = _latest(w)
    w.models.review_error = "unavailable"
    w.client.post(f"/projects/{w.pid}/fa-interfaces/scan/jobs")             # queued, not run
    r = w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/{run['run_id']}/retry-review")
    assert r.status_code == 409


# --- F9: an exact answer counts only when the model itself is seen answering ----------------------------------------


@pytest.mark.parametrize("usage", [None, {}, {"claude-haiku-4-5-20251001": {"outputTokens": 40}},
                                   {"claude-opus-5-5": {"outputTokens": 0}}])
def test_F9_no_or_haiku_only_model_usage_is_unverified(monkeypatch, tmp_path, usage):
    import subprocess

    from tests.test_provider_honesty import FakeCli, _reply, _req

    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    fake = FakeCli(reply=_reply(usage))
    monkeypatch.setattr(subprocess, "run", fake)
    out = P.ClaudeCodeProvider().complete(_req("claude-opus-5-5", exact_model=True))
    assert out.data is None and out.error == "model_unverified"


def test_F9_the_requested_model_answering_is_accepted(monkeypatch, tmp_path):
    import subprocess

    from tests.test_provider_honesty import FakeCli, _reply, _req

    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    monkeypatch.setattr(subprocess, "run", FakeCli(reply=_reply(
        {"claude-opus-5-5": {"outputTokens": 7}, "claude-haiku-4-5-20251001": {"outputTokens": 3}})))
    out = P.ClaudeCodeProvider().complete(_req("claude-opus-5-5", exact_model=True))
    assert out.error is None and out.data == {"answer": "ok"}


def test_F9_an_unverified_reviewer_answer_is_never_its_review(w):
    w.models.review_error = "model_unverified"
    out = _run(w)
    run = _latest(w)
    assert out["review_state"] == "missing" and run["review"]["fp2"]["state"] == "unverified"
    assert out["publication_state"] == "provisional"


# --- F10: one read or review at a time, atomically; the day's calls counted ---------------------------------------


def test_F10_a_scan_and_a_run_cannot_both_be_queued_even_when_both_look_first(w, monkeypatch):
    from app.routers import fa_interfaces as R
    from app.services import jobs

    a = w.client.post(f"/projects/{w.pid}/fa-interfaces/scan/jobs")
    # the run request looked before the scan was queued: its own checks find nothing, so the
    # insert itself must be refused by the shared key's unique index
    real, first = jobs.active_by_key, [True]

    def late_look(db, key):
        if first[0]:
            first[0] = False
            return None
        return real(db, key)
    monkeypatch.setattr(R, "_active_read", lambda db, pid: None)
    monkeypatch.setattr(jobs, "active_by_key", late_look)
    b = w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/jobs")
    active = w.db.query(BackgroundJob).filter(BackgroundJob.status.in_(("queued", "running"))).all()
    assert [j.kind for j in active] == ["fa_interfaces_scan"]
    assert b.json()["id"] == a.json()["id"] and b.json()["already_active"] is True


def test_F10_the_agents_looks_never_consume_the_orchestrators_reserved_allowance(w, monkeypatch):
    monkeypatch.setattr(settings, "ai_max_calls_per_project_per_day", 2)     # the general cap: not the review's
    out = _run(w)
    assert [r for r in w.models.requests if r.task == visual.TASK]
    assert out["review_state"] == "completed" and out["publication_state"] == "complete_candidate"


def test_F10_the_orchestrators_own_calls_of_the_day_bound_it_and_no_look_is_paid_for_without_room(w, monkeypatch):
    from app.core.timeutils import utc_now
    from app.models import AiUsage

    monkeypatch.setattr(settings, "fa_orchestrator_max_calls_per_day", 10)
    for _ in range(9):                                                      # earlier reviews today
        w.db.add(AiUsage(project_id=w.pid, task=workflow.TASK_REVIEW, model=OPUS, at=utc_now(), cache_hit=False,
                         outcome="ok"))
    w.db.commit()
    out = _run(w)
    run = _latest(w)
    assert not [r for r in w.models.requests if r.task == visual.TASK]      # nothing paid for that cannot be reviewed
    (agent,) = run["agent_reports"]
    assert agent["coverage_state"] == "unsupported" and "daily allowance" in agent["coverage_reason"]
    assert out["publication_state"] == "provisional"
    assert out["review_state"] != "completed" and "calls_per_project_per_day" in json.dumps(run["review"])


# --- F11: references and text the orchestrator gives are checked --------------------------------------------------


def test_F11_unknown_packages_are_dropped_and_links_or_markup_withheld():
    answer = {"coverage_assessment": [], "conflict_proposals": [], "rework_requests": [],
              "missing_or_suspect": [{"package": "NOT_A_PACKAGE", "issue": "other", "detail": "x"},
                                     {"package": "HVAC", "issue": "coverage_gap", "detail": "see https://x.example/a"}],
              "publication_recommendation": "provisional",
              "summary": "Read [this](https://evil.example/p) <b>now</b>", "open_questions": ["<script>x</script>"]}
    assert workflow.shape_problem(answer) is None
    out, notes = workflow._validate(answer, {"sources": set(), "conflicts": set(), "packages": {"HVAC"}})
    assert [m["package"] for m in out["missing_or_suspect"]] == ["HVAC"]
    assert out["missing_or_suspect"][0]["detail"] == "[withheld: link or markup]"
    assert out["summary"] == "[withheld: link or markup]" and out["open_questions"] == ["[withheld: link or markup]"]
    assert any("NOT_A_PACKAGE" in n for n in notes)
    bad = {**answer, "missing_or_suspect": [{"package": "HVAC", "issue": "made_up", "detail": "x"}]}
    assert "issue" in workflow.shape_problem(bad)


# --- F12 (kept on the safe side): equal totals at different places are never counted from one drawing ------------


def test_F12_equal_gate_totals_at_different_places_stay_held(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _gate_layout(gb.folder / "GATEBARRIER ELSEWHERE.dxf", shift=(40.0, 0.0))     # two settled points, 40 m away
    view = _read(gb)
    assert not [r for r in view["rows"] if r["key"] == "gate_barrier"]
    assert [g for g in view["verification"] if g["id"].startswith("GATE|") and g["conflict"]]


# --- F13: no paid looks on sheets that cannot count; the skipped sheets said ---------------------------------------


def _riser(src_items):
    return {"discipline": "SM", "status": "read", "filename": "SMOKE LAYOUT.dwg",
            "result": {"sheets": [{"name": "SM-101", "title": "3RD BASEMENT FLOOR PLAN", "kind": "plan"},
                                  {"name": "SM-119", "title": "SCHEMATIC RISER DIAGRAM", "kind": "diagram"}],
                       "items": src_items}}


def test_F13_riser_labels_are_not_looked_at_and_are_reported_sheet_by_sheet():
    items = ([{"key": "motorized_smoke_fire_damper", "sheet": "SM-119", "x": float(i), "y": 1.0, "text": "MSD",
               "kind": "label"} for i in range(268)]
             + [{"key": "motorized_smoke_fire_damper", "sheet": "SM-101", "x": 5.0, "y": 5.0, "text": "MSD",
                 "kind": "label"}])
    src = _riser(items)
    assert [it["sheet"] for it in visual.wanted(src)] == ["SM-101"]
    (skipped,) = visual.not_looked(src)
    assert skipped["sheet"] == "SM-119" and skipped["labels"] == 268 and "not a floor plan" in skipped["reason"]
    report = workflow._agent_report(1, {**src, "relative_path": "SM/SMOKE LAYOUT.dwg"}, looked=None, model_ok=True,
                                    model_why=None, started=0.0)
    assert report["not_looked"] == [skipped] and report["look"]["labels_expected"] is None


def test_F13_a_drawing_with_only_riser_labels_asks_the_model_nothing(w):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for i in range(5):
        msp.add_text("MSD", height=0.12).set_placement((3000.0 + i, 10.0))
    lay = doc.layouts.new("SM-119")
    lay.add_viewport(center=(420, 297), size=(800, 560), view_center_point=(3002.0, 10.0), view_height=97.0)
    lay.add_text("SCHEMATIC RISER DIAGRAM", height=5).set_placement((10, 10))
    (w.hvac / "VENTILATION LAYOUT.dxf").unlink()
    doc.saveas(w.hvac / "RISER.dxf")
    _run(w)
    assert not [r for r in w.models.requests if r.task == visual.TASK]
    (agent,) = _latest(w)["agent_reports"]
    assert agent["coverage_state"] == "complete" and agent["not_looked"][0]["labels"] == 5


# --- explicit coverage limitations: unread PDFs and labels with no block symbol ----------------------------------


def test_unread_pdfs_and_symbol_less_labels_are_limitations_not_absent_equipment(w, monkeypatch):
    monkeypatch.setattr(settings, "fa_agent_parallel", 1)       # two drawings, one shared in-memory connection
    sm = w.root / "03- Drawings" / "IFC" / "Mechanical" / "SM" / "SD"
    sm.mkdir(parents=True, exist_ok=True)
    (sm / "MAJ002-GME-SDW-MH-KS-ZZZ-B01-010042 B1.pdf").write_bytes(b"%PDF-1.4\n")
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    doc.modelspace().add_text("MSD", height=0.12).set_placement((719.25, 154.4))      # a label, no symbol drawn
    lay = doc.layouts.new("SM-101")
    lay.add_viewport(center=(420, 297), size=(800, 560), view_center_point=(733.0, 135.3), view_height=97.0)
    lay.add_text("3RD BASEMENT FLOOR PLAN", height=5).set_placement((10, 10))
    doc.saveas(sm.parent / "SMOKE LAYOUT.dxf")
    _run(w)
    view = w.client.get(f"/projects/{w.pid}/fa-interfaces").json()
    kinds = {(x["package"], x["kind"]) for x in view["limitations"]}
    assert ("SM", "unsupported_files") in kinds and ("SM", "no_block_symbol") in kinds
    pdf = next(x for x in view["limitations"] if x["kind"] == "unsupported_files")
    assert "neither counted nor ruled out" in pdf["text"] and pdf["files"] == ["MAJ002-GME-SDW-MH-KS-ZZZ-B01-010042 B1.pdf"]
    (pkg,) = [p for p in _latest(w)["package_reports"] if p["package"] == "SM"]
    assert {x["kind"] for x in pkg["limitations"]} == {"unsupported_files", "no_block_symbol"}
    from app.interfaces.export import evidence_note

    assert "NOT SHOWN BY THE DRAWINGS READ" in evidence_note(view) and "PDF" in evidence_note(view)
    assert w.client.get(f"/projects/{w.pid}/fa-interfaces/export.xlsx").status_code == 200


# --- end to end: both MSD drawings together ---------------------------------------------------------------------

ROOMS = [("STORE ROOM NORTH", 700.0, 160.0), ("CORRIDOR WEST", 705.0, 140.0), ("LOBBY EAST", 760.0, 150.0),
         ("STAIR CORE TWO", 740.0, 120.0)]


def _msd_drawing(path, dampers, centre=(733.0, 135.3)):
    """A B3 plan in the project's frame: the same rooms written at the same
    places, the same viewport, and a damper symbol 0.2 m right of and below
    each MSD label (the symbol is where the damper stands)."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    blk = doc.blocks.new("DAMPER")
    blk.add_lwpolyline([(-0.02, -0.12), (0.02, -0.12), (0.02, 0.12), (-0.02, 0.12)], close=True)
    msp = doc.modelspace()
    for text, x, y in ROOMS:
        msp.add_text(text, height=0.2).set_placement((x, y))
    for x, y in dampers:
        msp.add_blockref("DAMPER", (x + 0.2, y - 0.2))
        msp.add_text("MSD", height=0.12).set_placement((x, y))
    lay = doc.layouts.new("B3")
    lay.add_viewport(center=(420, 297), size=(800, 560), view_center_point=centre, view_height=97.0)
    lay.add_text("3RD BASEMENT FLOOR PLAN", height=5).set_placement((10, 10))
    doc.saveas(path)


def test_end_to_end_both_msd_drawings_are_read_and_their_dampers_counted_once_each_at_their_symbols(w, monkeypatch):
    # one agent and one window at a time here: the tests' in-memory database is one connection shared by every
    # thread (StaticPool), which two agents' writes at once would misuse; agents side by side
    # are tested in test_fa_workflow, and ran on a file database in the real-data run
    monkeypatch.setattr(settings, "fa_agent_parallel", 1)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    sm = w.root / "03- Drawings" / "IFC" / "Mechanical" / "SM"
    sm.mkdir(parents=True, exist_ok=True)
    (w.hvac / "VENTILATION LAYOUT.dxf").unlink()
    shared, sm_only, hvac_only = (719.25, 154.4), (705.0, 150.0), (725.0, 154.4)
    _msd_drawing(sm / "SMOKE LAYOUT.dxf", [shared, sm_only])
    _msd_drawing(w.hvac / "VENTILATION LAYOUT.dxf", [shared, hvac_only])
    out = _run(w)
    run = _latest(w)
    # both drawings discovered, each with its own agent and a complete look
    agents = {a["filename"]: a for a in run["agent_reports"]}
    assert set(agents) == {"SMOKE LAYOUT.dxf", "VENTILATION LAYOUT.dxf"}
    assert all(a["coverage_state"] == "complete" and a["look"]["labels_looked"] == 2 for a in agents.values())
    assert {r.model for r in w.models.requests if r.task == visual.TASK} == {OPUS}
    view = w.client.get(f"/projects/{w.pid}/fa-interfaces").json()
    dampers = [r for r in view["rows"] if r["key"] == "motorized_smoke_fire_damper"]
    # the union: the damper both show once, each drawing's own once -- 3, not 2 + 2 and not max(2, 2)
    assert len(dampers) == 3
    assert any("union" in c for c in view["conflicts"])
    by_label = {tuple(r["label_anchor"]): r for r in dampers}
    assert set(by_label) == {(719.25, 154.4), (705.0, 150.0), (725.0, 154.4)}
    for (lx, ly), r in by_label.items():
        # where it stands is its symbol, not where its tag text is written
        assert r["location_state"] == "symbol" and r["anchor"] == r["equipment_anchor"]
        assert r["equipment_anchor"] == [round(lx + 0.2, 3), round(ly - 0.2, 3)]
        assert r["equipment_anchor"] != r["label_anchor"]
    assert "also drawn on" in by_label[(719.25, 154.4)]["evidence"]
    assert {r["source"].split(" ")[0] for r in dampers} >= {"SMOKE", "VENTILATION"}
    assert out["publication_state"] == "complete_candidate"


# --- found in the real-data evidence (EP-30880): a published reading made by older code ---------------------------


def _fa(sha, **kw):
    return {"discipline": "ARCH", "kind": "fa_ifc", "relative_path": "03- Drawings/IFC/Electrical/FA/FA.dwg",
            "filename": "FA.dwg", "revision": "R0", "fa_drawing_id": 1, "sha256": sha, "size": 100, "mtime": 5.0,
            "status": "read", **kw}


def test_N2_an_unchanged_fire_alarm_ifc_drawing_read_by_older_code_is_still_the_published_one():
    listing = evidence.Listing(root="ok")
    in_force = {"03- Drawings/IFC/Electrical/FA/FA.dwg": {"dxf_exists": True, "sha256": None}}
    now = [_fa(None)]
    assert evidence.snapshot_source_current(_fa("dbe7900f" + "0" * 56), now, listing, in_force)
    # another register record, revision or file is not the same drawing
    assert not evidence.snapshot_source_current(_fa("dbe7900f" + "0" * 56, fa_drawing_id=2), now, listing, in_force)
    assert not evidence.snapshot_source_current(_fa("dbe7900f" + "0" * 56, revision="R1"), now, listing, in_force)
    assert not evidence.snapshot_source_current(_fa("dbe7900f" + "0" * 56, size=101), now, listing, in_force)
    # two hashes that differ are two files
    assert not evidence.snapshot_source_current(_fa("a" * 64), [_fa("b" * 64)], listing, in_force)


def test_N1_the_gate_checks_the_published_drawings_by_path_as_the_scans_own_advance_does(w):
    _run(w)
    assert _accept(w, _latest(w)["run_id"]).status_code == 200
    # the published reading of the drawing carries another hash (as one made by older code does)
    row = _row(w)
    published = json.loads(json.dumps(row.published))
    for s in published["sources"]:
        s["sha256"] = "f" * 64
    row.published = published
    w.db.commit()
    out = _run(w)
    assert out["publication_state"] == "complete_candidate", _latest(w)["publication_reasons"]
    # a published drawing that is gone and not confirmed removed still blocks
    (w.hvac / "VENTILATION LAYOUT.dxf").rename(w.hvac / "VENTILATION LAYOUT.old")
    _damper_drawing(w.hvac / "OTHER.dxf")
    out = _run(w)
    assert out["publication_state"] == "provisional"
    assert any("of the published schedule" in r or "stale" in r for r in _latest(w)["publication_reasons"])


# --- the independent re-review of 180fd1f (A3, A5, F8, F10, W-4) -------------------------------------------------


def test_A5_a_gate_conflict_is_not_settled_by_a_count_or_dismissed_without_its_authority(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _shop(gb)
    view = _read(gb)
    (conflict,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    count = {"id": conflict["id"], "action": "resolve", "qty": 2, "floor_keys": conflict["proposed_floor_keys"]}
    assert _decide(gb, **count).status_code == 422                            # no reason, no authority
    assert _decide(gb, **count, reason="two lanes").status_code == 422           # no authority
    assert _decide(gb, id=conflict["id"], action="dismiss", reason="not ours").status_code == 422
    body = gb.client.get(f"/projects/{gb.pid}/fa-interfaces").json()
    assert not [r for r in body["rows"] if r["key"] == "gate_barrier"]        # still held: nothing counted
    assert [g for g in body["verification"] if g["id"] == conflict["id"]]
    done = _decide(gb, **count, reason="two lanes per the consultant", authority="Consultant RFI-021").json()
    gates = [r for r in done["rows"] if r["key"] == "gate_barrier"]
    assert len(gates) == 2 and all("Consultant RFI-021" in r["evidence"] for r in gates)
    gb.db.expire_all()
    d = gb.db.query(ProjectFaInterfaces).filter_by(project_id=gb.pid).one().decisions[conflict["id"]]
    assert d["status"] == "resolved" and d["authority"] == "Consultant RFI-021"


def test_W4_a_views_conflict_is_settled_by_a_count_on_an_authority_and_the_run_can_then_be_accepted(w, monkeypatch):
    monkeypatch.setattr(settings, "fa_agent_parallel", 1)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    sm = w.root / "03- Drawings" / "IFC" / "Mechanical" / "SM"
    sm.mkdir(parents=True, exist_ok=True)
    (w.hvac / "VENTILATION LAYOUT.dxf").unlink()
    _msd_drawing(sm / "SMOKE LAYOUT.dxf", [(719.25, 154.4)])
    _msd_drawing(w.hvac / "VENTILATION LAYOUT.dxf", [(719.25, 154.4)], centre=(735.0, 135.3))   # another view
    assert _run(w)["publication_state"] == "provisional"
    view = w.client.get(f"/projects/{w.pid}/fa-interfaces").json()
    (conflict,) = [g for g in view["verification"] if g.get("conflict")]
    assert conflict["id"].startswith("CONFLICT|") and not conflict.get("drawings")   # the page offers the count
    count = {"id": conflict["id"], "action": "resolve", "qty": 1, "floor_keys": conflict["proposed_floor_keys"]}
    assert w.client.post(f"/projects/{w.pid}/fa-interfaces/decisions", json=count).status_code == 422
    r = w.client.post(f"/projects/{w.pid}/fa-interfaces/decisions",
                      json={**count, "reason": "one damper, both drawings", "authority": "Site survey 12"})
    assert r.status_code == 200
    out = _run(w)
    assert out["publication_state"] == "complete_candidate", _latest(w)["publication_reasons"]
    assert _accept(w, _latest(w)["run_id"]).status_code == 200


def test_F8_a_retry_refused_when_its_job_cannot_be_queued_does_not_spend_the_days_bound(w, monkeypatch):
    from app.routers import fa_interfaces as R

    w.models.review_error = "unavailable"
    _run(w)
    run = _latest(w)
    w.client.post(f"/projects/{w.pid}/fa-interfaces/scan/jobs")             # queued under the shared key
    monkeypatch.setattr(R, "_active_read", lambda db, pid: None)              # the request looked before it
    r = w.client.post(f"/projects/{w.pid}/fa-interfaces/runs/{run['run_id']}/retry-review")
    assert r.status_code == 409
    w.db.expire_all()
    assert (w.db.get(FaInterfaceRun, run["run_id"]).review_retries or 0) == 0


def test_F10_no_look_is_paid_for_when_the_route_cannot_serve_the_orchestrator(w, monkeypatch):
    monkeypatch.setattr(settings, "fa_orchestrator_model", UNSERVED)         # the drawing model yes, the reviewer not
    out = _run(w)
    run = _latest(w)
    assert not [r for r in w.models.requests if r.task == visual.TASK]
    (agent,) = run["agent_reports"]
    assert agent["coverage_state"] == "unsupported" and "reviewer" in agent["coverage_reason"]
    assert out["review_state"] == "missing" and out["publication_state"] == "provisional"


def _names_absent(packages_to_name):
    def review(request):
        a = _ok_review(request)
        payload = json.loads(request.parts[0].text)
        if payload.get("scope") == "run":
            a["missing_or_suspect"] = [{"package": k, "issue": "source_missing", "detail": "no drawing"}
                                       for k in packages_to_name(payload["packages"])]
        return a
    return review


def test_A3_naming_a_package_that_has_no_drawing_at_all_as_the_prompt_asks_does_not_lower_the_run(w):
    w.models.review = _names_absent(lambda ps: [p["package"] for p in ps if not p["sources"]])
    out = _run(w)
    run = _latest(w)
    assert run["review"]["fp2"]["proposal"]["missing_or_suspect"]               # said, and shown to the engineer
    assert out["publication_state"] == "complete_candidate", run["publication_reasons"]
    assert _accept(w, run["run_id"]).status_code == 200


@pytest.mark.parametrize("which", ["read", "unread_only"])
def test_A3_a_source_missing_claim_on_a_package_with_files_still_lowers_the_run(w, which):
    if which == "unread_only":
        (_ff(w) / "FF SHOP DRAWING.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")      # a file it cannot read
        name = "FF"
    else:
        name = "HVAC"                                                         # read and covered
    w.models.review = _names_absent(lambda ps: [name])
    out = _run(w)
    run = _latest(w)
    assert out["publication_state"] == "provisional"
    assert "Opus (run) names 1 missing or suspect item(s)" in run["publication_reasons"]


# --- the independent review of ac314de (R3-1, R3-2, R3-3, R3-5, R3-7, R3-8) ---------------------------------------


def _gb_drawing(path, points):
    """Another gate barrier drawing of the ground floor in the layout's frame: a fire
    alarm connection point at each of `points`."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for text, x, y in LANDMARK_WORDS:
        msp.add_text(text, height=0.2).set_placement((x, y))
    for x, y in points:
        msp.add_text("FIRE ALARM CABLE", height=0.12).set_placement((x, y))
        msp.add_text("GATE BARRIER", height=0.12).set_placement((x + 0.5, y + 0.5))
    _sheet(doc, "BGF", "GROUND FLOOR PLAN GATEBARRIER SYSTEM LAYOUT", (1182.99, 142.21), 96.95)
    doc.saveas(path)


@pytest.mark.parametrize("name", ["AAA OTHER GB.dxf", "ZZZ OTHER GB.dxf"])
def test_R3_5_two_gate_drawings_agree_only_when_their_points_pair_one_to_one_in_either_file_order(gb, name):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")          # two points 5.2 m apart
    # one point between the layout's two (within reach of both), one 40 m away: no one-to-one pairing
    _gb_drawing(gb.folder / name, [(1163.40, 179.37), (1203.40, 179.37)])
    view = _read(gb)
    assert not [r for r in view["rows"] if r["key"] == "gate_barrier"]
    (held,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    assert held["conflict"] and len(held["drawings"]) == 2
    assert not any("the drawings agree" in c for c in view["conflicts"])


def test_R3_5_drawings_whose_points_pair_one_to_one_still_agree():
    def pts(*xy):
        return [{"anchor": p} for p in xy]
    pair = service._gate_points_pair
    assert pair(pts((0, 0), (5, 0)), pts((5.5, 0), (0.5, 0)), 3.0)
    assert not pair(pts((0, 0), (5, 0)), pts((2.5, 0), (45, 0)), 3.0)        # one-way "any" would pass this
    assert not pair(pts((2.5, 0), (45, 0)), pts((0, 0), (5, 0)), 3.0)
    assert not pair(pts((0, 0), (1, 0)), pts((0.5, 0), (0.6, 0), (9, 0)), 3.0)
    assert pair(pts((0, 0), (2, 0)), pts((1, 0), (-2, 0)), 2.5)             # one first-fit would miss


def test_R3_3_a_governing_choice_reopens_when_a_new_drawing_joins_its_conflict(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _shop(gb)
    view = _read(gb)
    (c,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    layout = next(d["relative_path"] for d in c["drawings"] if d["points"] == 2)
    done = _decide(gb, id=c["id"], action="govern", relative_path=layout, reason="issued", authority="RFI-1").json()
    assert len([r for r in done["rows"] if r["key"] == "gate_barrier"]) == 2
    _gate_layout(gb.folder / "GATEBARRIER ELSEWHERE.dxf", shift=(40.0, 0.0))  # a third drawing, other points
    view = _read(gb)
    assert not [r for r in view["rows"] if r["key"] == "gate_barrier"]     # nothing counted until chosen again
    (g,) = [x for x in view["verification"] if x["id"] == c["id"]]
    assert g["decision_not_applied"] and len(g["drawings"]) == 3 and "joined" in g["reason"]
    again = _decide(gb, id=c["id"], action="govern", relative_path=layout, reason="still the IFC", authority="RFI-2")
    assert len([r for r in again.json()["rows"] if r["key"] == "gate_barrier"]) == 2


def test_R3_3_a_governing_choice_that_did_not_record_its_drawings_is_not_applied(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _shop(gb)
    view = _read(gb)
    (c,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    layout = next(d["relative_path"] for d in c["drawings"] if d["points"] == 2)
    row = gb.db.query(ProjectFaInterfaces).filter_by(project_id=gb.pid).one()
    row.decisions = {c["id"]: {"status": "governed", "relative_path": layout, "reason": "x", "authority": "y"}}
    gb.db.commit()
    view = gb.client.get(f"/projects/{gb.pid}/fa-interfaces").json()
    assert not [r for r in view["rows"] if r["key"] == "gate_barrier"]
    assert [g for g in view["verification"] if g["id"] == c["id"] and g.get("decision_not_applied")]


def test_R3_1_a_package_whose_drawings_were_all_removed_is_empty_for_the_review(w):
    ff = _ff(w)
    _damper_drawing(ff / "FF LAYOUT.dxf")
    _run(w)
    (ff / "FF LAYOUT.dxf").unlink()                                          # removed on purpose
    w.db.expire_all()
    service.scan_project(w.db, w.db.get(Project, w.pid), look=False, advance=False)
    rel = next(e["relative_path"] for e in _row(w).sources if e.get("filename") == "FF LAYOUT.dxf")
    assert w.client.post(f"/projects/{w.pid}/fa-interfaces/sources/confirm-removed",
                         json={"relative_paths": [rel]}).status_code == 200
    w.models.review = _names_absent(lambda ps: [p["package"] for p in ps if p["package"] == "FF"])
    w.models.requests.clear()
    out = _run(w)
    run = _latest(w)
    assert not [q for q in w.models.requests
                if q.task == workflow.TASK_REVIEW and q.parts[0].label == "package_review:FF"]
    assert out["publication_state"] == "complete_candidate", run["publication_reasons"]


def test_R3_2_a_restored_look_rejected_damper_is_counted_once_beside_its_twin(w, monkeypatch):
    monkeypatch.setattr(settings, "fa_agent_parallel", 1)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    sm = w.root / "03- Drawings" / "IFC" / "Mechanical" / "SM"
    sm.mkdir(parents=True, exist_ok=True)
    (w.hvac / "VENTILATION LAYOUT.dxf").unlink()
    _msd_drawing(sm / "SMOKE LAYOUT.dxf", [(719.25, 154.4)])
    _msd_drawing(w.hvac / "VENTILATION LAYOUT.dxf", [(719.25, 154.4)])
    real = w.models.complete

    def complete(request):
        out = real(request)
        if request.task == visual.TASK and any("SMOKE" in getattr(p, "text", "") for p in request.parts):
            out = P.AiResponse(data={"labels": [{**a, "damper": False, "what": "not a damper"}
                                                for a in out.data["labels"]]}, model=request.model,
                               usage=P.Usage(input_tokens=900, output_tokens=60))
        return out
    w.models.complete = complete
    _run(w)
    view = w.client.get(f"/projects/{w.pid}/fa-interfaces").json()
    dampers = [r for r in view["rows"] if r["key"] == "motorized_smoke_fire_damper"]
    rejected = [r for r in view["rejected"] if r["key"] == "motorized_smoke_fire_damper"]
    assert len(dampers) == 1 and len(rejected) == 1
    after = w.client.post(f"/projects/{w.pid}/fa-interfaces/decisions",
                          json={"id": rejected[0]["id"], "action": "restore"}).json()
    again = [r for r in after["rows"] if r["key"] == "motorized_smoke_fire_damper"]
    assert len(again) == 1                                                  # one damper at one symbol: once
    assert again[0]["location_state"] == "symbol" and again[0]["equipment_anchor"] != again[0]["label_anchor"]
    assert "also drawn on" in again[0]["evidence"]


def test_R3_7_an_api_reply_that_does_not_say_its_model_is_not_an_exact_answer():
    import dataclasses

    import anthropic

    class Msgs:
        def create(self, **params):
            return SimpleNamespace(model=None, stop_reason="end_turn",
                                   usage=SimpleNamespace(input_tokens=5, output_tokens=3, cache_read_input_tokens=0,
                                                         output_tokens_details=None),
                                   content=[SimpleNamespace(type="text", text='{"answer": "ok"}')])
        stream = None

    class Client:
        messages = Msgs()
        beta = SimpleNamespace(messages=Msgs())

        def with_options(self, **kw):
            return self
    p = object.__new__(P.ClaudeProvider)
    p._anthropic, p._client, p._models, p._effort = anthropic, Client(), {"small": "x", "standard": "y"}, "high"
    p._semaphore, p._credential = threading.BoundedSemaphore(1), True
    req = P.AiRequest(task="t", system="s", parts=[P.TextPart("a", "b")], schema={"type": "object"},
                      max_output_tokens=100, model="claude-fable-5-1", exact_model=True, effort="high")
    out = p.complete(req)
    assert out.data is None and out.error == "model_unverified"
    assert p.complete(dataclasses.replace(req, exact_model=False)).error is None   # only an exact request needs it


def test_R3_8_a_folder_part_not_listed_at_accept_is_said_as_such_not_as_changed_drawings(w, monkeypatch):
    out = _run(w)
    assert out["publication_state"] == "complete_candidate"
    real = evidence.attributes
    monkeypatch.setattr(evidence, "attributes",
                        lambda path: evidence.ATTR_RECALL_ON_OPEN if str(path).rstrip("\\/").endswith("HVAC")
                        else real(path))
    r = _accept(w, _latest(w)["run_id"])
    assert r.status_code == 422 and "could not be listed" in r.json()["detail"]
    assert _row(w).published is None


@pytest.mark.parametrize("copy", ["AAA COPY.dxf", "ZZZ COPY.dxf"])
def test_R4_1_agreeing_gate_drawings_tied_on_settled_points_count_the_first_by_path_stably(gb, copy):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _gate_layout(gb.folder / copy)                                          # the same drawing under another name
    view = _read(gb)
    gates = [r for r in view["rows"] if r["key"] == "gate_barrier"]
    first = min("GATEBARRIER SYSTEM LAYOUT.dxf", copy)
    assert len(gates) == 2 and all(first in r["id"] for r in gates)
    assert any("the drawings agree" in c for c in view["conflicts"])
    # the engineer's answer on a counted row keeps applying when the drawings are read again
    entry = next(r for r in gates if r["role"] == "entry")
    _decide(gb, id=entry["id"], action="reject", reason="not ours")
    again = _read(gb)
    assert entry["id"] in {r["id"] for r in again["rejected"]}
    assert [r["id"] for r in again["rows"] if r["key"] == "gate_barrier"] == [r["id"] for r in gates if r is not entry]
