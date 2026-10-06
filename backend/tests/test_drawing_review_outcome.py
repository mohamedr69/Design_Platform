"""Drawings Review, as it ends (EP-30880, 6 October 2026): the review ran with
AI off, the disabled provider's placeholder was taken for the model's answer,
every look was saved "done" with nothing in it, and the page said "0 / 768
rooms reviewed, no findings" under a Review checkmark.

A finding the model gives must reach the page through the worker, the
database and the API; a plot no model answered is never a review; a review
that does not complete keeps what was there before and says so."""
from __future__ import annotations

import json

from app.ai.provider import NullProvider, RecordingProvider, set_provider
from app.core.config import get_settings
from app.review import ai as A
from tests.conftest import login
from tests.test_drawing_review import _plan_pdf

settings = get_settings()
NOT_COMPLETED = "Plotting completed; review has not completed"


def _c(system, status, action="none", device="", instruction="", x=-1, y=-1):
    return {"system": system, "status": status, "seen": "", "action": action, "device": device,
            "instruction": instruction, "x": x, "y": y}


# The fake model's answers: room 2 (ELECTRICAL ROOM) has no emergency light -- one known finding.
KNOWN = "Add E by the electrical room door (fake model)"
WINDOW = {"rooms": [
    {"n": 1, "room_type": "entrance lobby", "checks": [_c(s, "present") for s in A.SYSTEMS]},
    {"n": 2, "room_type": "electrical room", "checks": [
        _c(s, "not_required") for s in A.SYSTEMS if s != "emergency_light"] + [
        _c("emergency_light", "absent", "add", "emergency light (E)", KNOWN, 0.5, 0.5)]}],
    "other": []}
CLEAN = {"rooms": [{"n": n, "room_type": "room", "checks": [_c(s, "present") for s in A.SYSTEMS]} for n in (1, 2)],
         "other": []}
SHEET = {"findings": []}


def _drawing(client, db_session, monkeypatch, tmp_path, ep):
    """A project with a one-sheet FA drawing (two named rooms) and a plot
    standing in for AutoCAD's, counted."""
    import app.routers.jobs as jobs_router
    from app.models import ProjectIfcDrawing
    from app.review import render, service

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    pdf = _plan_pdf(tmp_path / "sheets.pdf")
    plots = []
    monkeypatch.setattr(render, "render", lambda project, drawing: plots.append(1) or (pdf, "c" * 64))
    monkeypatch.setattr(service.storage, "relative", lambda path: str(path))
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": ep, "project_name": "Tower", "design_sheets": []}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA LAYOUT.dwg", stored_path="x.dxf", revision="R0",
                                meta={"sheets": [{"name": "FA-104", "title": "GROUND FLOOR PLAN", "kind": "plan"}]},
                                groups=[])
    db_session.add(drawing)
    db_session.commit()
    return pid, drawing.id, plots


def _review(client, pid, did, provider):
    """Start the review as the page does and follow it as the page does
    (useJob): the job to its end, then the review fetched again."""
    set_provider(provider)
    try:
        started = client.post(f"/projects/{pid}/drawing-review/{did}/jobs", json={"pages": None})
        assert started.status_code == 202, started.text
    finally:
        set_provider(None)
    job = client.get(f"/jobs/{started.json()['id']}").json()
    assert job["status"] not in ("queued", "running")
    return job, client.get(f"/projects/{pid}/drawing-review/{did}").json()


def _badge(client, pid, did):
    return next(d for d in client.get(f"/projects/{pid}/redesign").json()["drawings"] if d["id"] == did)


def test_the_models_finding_reaches_the_review_page_through_the_worker_the_database_and_the_api(
        client, db_session, monkeypatch, tmp_path):
    from app.database import SessionLocal
    from app.models import ProjectDrawingReview

    from app.review import service

    pid, did, plots = _drawing(client, db_session, monkeypatch, tmp_path, "40960")
    said = []
    real_run = service.run

    def run(*args, progress=None, **kw):
        return real_run(*args, progress=lambda d, t, m: (said.append(m), progress(d, t, m)), **kw)

    monkeypatch.setattr(service, "run", run)
    provider = RecordingProvider([WINDOW, SHEET])
    job, review = _review(client, pid, did, provider)

    # the worker: plotted, then asked the model (two looks), and said what it read
    assert plots and provider.calls == 2
    assert job["status"] == "succeeded", job
    assert job["result"]["answered"] == 2 and job["result"]["rooms_reviewed"] == 2
    # each stage said as it came: Plotting -> Preparing -> Reviewing -> Saving -> Completed
    stages = [m.split(" ")[0] for m in said]
    assert stages[0] == "Plotting" and said[1].startswith("Plotting completed. Preparing the review inputs")
    assert said[2] == "Reviewing 2 rooms in 2 looks" and said[-2:] == ["Saving the results", "Completed"]
    # the database, read afresh: the model's answer kept, under the model that gave it
    fresh = SessionLocal()
    try:
        row = fresh.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
        windows = row.sheets[0]["windows"]
        assert row.status == "done" and {(w["status"], w["model"]) for w in windows} == {("done", "recording")}
        window = next(w for w in windows if "2" in w["answers"])
        assert window["answers"]["2"]["checks"]["emergency_light"]["instruction"] == KNOWN
    finally:
        fresh.close()
    # the API: the finding, the rooms read, who answered
    assert review["state"] == "done" and review["answered_by"] == ["recording"]
    assert review["counts"]["reviewed"] == 2 and review["counts"]["rooms"] == 2
    found = [f for f in review["findings"] if f["action"] != "none"]
    assert [(f["room"], f["system"], f["action"], f["instruction"]) for f in found] == [
        ("ELECTRICAL ROOM", "emergency_light", "add", KNOWN)]
    assert review["counts"]["add"] == 1 and review["counts"]["open"] == 1
    # the page's refresh: the job list it picks running jobs up from, and the step's mark
    assert not [j for j in client.get(f"/projects/{pid}/jobs").json()
                if j["kind"] == "fa_drawing_review" and j["status"] in ("queued", "running")]
    assert _badge(client, pid, did)["review_state"] == "done"


def test_a_plot_with_no_model_to_call_is_blocked_and_keeps_the_answers_and_decisions_before_it(
        client, db_session, monkeypatch, tmp_path):
    from app.models import AiUsage

    pid, did, plots = _drawing(client, db_session, monkeypatch, tmp_path, "40961")
    _job, review = _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    finding = next(f for f in review["findings"] if f["action"] == "add")
    # the engineer accepts it -- a ruling, so the next review asks again
    url = f"/projects/{pid}/drawing-review/{did}/decisions"
    assert client.post(url, json={"id": finding["id"], "status": "accepted"}).json()["counts"]["accepted"] == 1
    plotted = len(plots)

    job, after = _review(client, pid, did, NullProvider())
    assert len(plots) == plotted + 1                           # the plot happened ...
    assert job["status"] == "failed"                           # ... the review did not
    assert NOT_COMPLETED in job["error"] and "no model can be called" in job["error"]
    assert after["state"] == "blocked" and NOT_COMPLETED in after["state_message"]
    # nothing was asked, nothing was logged as an answer, and what was there stays
    assert db_session.query(AiUsage).filter(AiUsage.model == "null").count() == 0
    assert after["counts"]["reviewed"] == 2
    kept = next(f for f in after["findings"] if f["id"] == finding["id"])
    assert kept["instruction"] == KNOWN and kept["decision"] == "accepted"
    assert _badge(client, pid, did)["review_state"] == "blocked"


def test_a_plot_whose_every_look_fails_is_failed_and_keeps_what_was_there(client, db_session, monkeypatch, tmp_path):
    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "40962")
    _job, review = _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    finding = next(f for f in review["findings"] if f["action"] == "add")
    url = f"/projects/{pid}/drawing-review/{did}/decisions"
    client.post(url, json={"id": finding["id"], "status": "accepted"})

    failing = RecordingProvider([RuntimeError("the route fell over"), RuntimeError("the route fell over")])
    job, after = _review(client, pid, did, failing)
    assert failing.calls == 2
    assert job["status"] == "failed"
    assert NOT_COMPLETED in job["error"] and "none of the 2 looks was answered" in job["error"]
    assert "the route fell over" in job["error"]
    assert after["state"] == "failed" and after["counts"]["reviewed"] == 2
    kept = next(f for f in after["findings"] if f["id"] == finding["id"])
    assert kept["decision"] == "accepted"


def test_a_completed_review_with_no_findings_says_so_with_the_rooms_it_read(client, db_session, monkeypatch, tmp_path):
    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "40963")
    job, review = _review(client, pid, did, RecordingProvider([CLEAN, SHEET]))
    assert job["status"] == "succeeded" and job["result"]["rooms_reviewed"] == 2
    assert review["state"] == "done" and review["findings"] == []
    assert review["counts"]["reviewed"] == 2
    assert review["state_message"] == "Review completed: no changes proposed. 2 of 2 rooms reviewed."
    assert _badge(client, pid, did)["review_state"] == "done"


def test_the_disabled_providers_placeholder_saved_as_done_is_not_a_review_and_is_asked_again(
        client, db_session, monkeypatch, tmp_path):
    """The live row's shape: every look "done", model "null", no answers."""
    from app.models import ProjectDrawingReview, ResultCache

    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "40964")
    _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    sheets = json.loads(json.dumps(row.sheets))
    for w in sheets[0]["windows"]:
        w.update(answers={}, other=[], model="null", status="done")
    sheets[0].pop("sheet_model")
    sheets[0]["sheet_findings"] = []
    row.sheets, row.status = sheets, "done"
    # and the stored answers, as the live cache holds them: the placeholder under the model's key
    placeholder = {"task_id": "x", "status": "insufficient_evidence", "proposed_changes": [],
                   "source_references": [], "unresolved_issues": ["AI assistance is disabled"]}
    for entry in db_session.query(ResultCache).filter(ResultCache.task.like("fa_drawing_review%")):
        entry.value = {"data": placeholder, "model": "null"}
    db_session.commit()

    review = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    assert review["state"] == "not_reviewed" and review["counts"]["reviewed"] == 0
    assert NOT_COMPLETED in review["state_message"] and "disabled AI provider" in review["state_message"]
    assert review["answered_by"] == []
    assert {r["status"] for f in review["floors"] for r in f["rooms"]} == {"pending"}
    badge = _badge(client, pid, did)
    assert badge["review_state"] == "not_reviewed"           # no Review checkmark for it

    # the next review asks those looks again (not "nothing to ask") and the finding comes back
    provider = RecordingProvider([WINDOW, SHEET])
    job, again = _review(client, pid, did, provider)
    assert provider.calls == 2 and job["status"] == "succeeded"
    assert again["state"] == "done" and any(f["instruction"] == KNOWN for f in again["findings"])


def test_an_exact_model_task_gets_no_answer_from_the_disabled_provider_and_none_is_stored(client, db_session,
                                                                                         monkeypatch):
    from app.ai import cache as result_cache
    from app.ai.provider import TextPart
    from app.compliance import assist
    from app.models import AiUsage

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40965", "project_name": "T", "design_sheets": []}).json()["id"]
    stored = []
    real_put = result_cache.put
    monkeypatch.setattr(result_cache, "put", lambda *a, **kw: stored.append(a) or real_put(*a, **kw))
    schema = {"type": "object"}

    def ask(provider, exact):
        session = assist.open_session(db_session, pid, "d" * 64, provider=provider)
        return assist.call_task(session, "fa_drawing_review_window", "system", [TextPart("t", "x")], schema, 100,
                                model="claude-opus-5-5", exact_model=exact)

    refused = ask(NullProvider(), True)
    assert refused.data is None and refused.error.startswith("unavailable")
    assert db_session.query(AiUsage).count() == 0            # nothing called, nothing logged as an answer
    placeholder = ask(NullProvider(), False)                 # elsewhere it still flows, as before ...
    assert placeholder.data["status"] == "insufficient_evidence"
    assert stored == []                                      # ... but is never stored under a model's key

    # a placeholder stored before this check is not reused for an exact-model task
    monkeypatch.setattr(result_cache, "get", lambda *a, **kw: {"data": {"rooms": [], "other": []}, "model": "null"})
    provider = RecordingProvider([{"rooms": [], "other": []}])
    result = ask(provider, True)
    assert provider.calls == 1 and result.model == "recording" and not result.from_cache


def test_the_drawing_reviews_own_switch_calls_the_model_for_the_review_alone(client, db_session, monkeypatch, tmp_path):
    """DRAWING_REVIEW_AI_ENABLED turns the review's looks on and nothing else:
    the platform's provider, the FA Interfaces' and Drawings Preparation's stay
    the disabled one. Off, the review is blocked."""
    from app.ai import provider as prov

    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "40966")
    built = []

    def build():
        built.append(RecordingProvider([WINDOW, SHEET]))
        return built[-1]

    monkeypatch.setattr(prov, "_BUILDERS", {"claude-code": build})
    for name, value in (("ai_enabled", False), ("fa_ai_enabled", False), ("prep_ai_enabled", False),
                        ("drawing_review_ai_enabled", False), ("ai_provider", "claude-code")):
        monkeypatch.setattr(settings, name, value)
    set_provider(None)
    try:
        off = client.post(f"/projects/{pid}/drawing-review/{did}/jobs", json={"pages": None}).json()
        assert client.get(f"/jobs/{off['id']}").json()["status"] == "failed" and not built
        assert client.get(f"/projects/{pid}/drawing-review/{did}").json()["state"] == "blocked"

        monkeypatch.setattr(settings, "drawing_review_ai_enabled", True)
        on = client.post(f"/projects/{pid}/drawing-review/{did}/jobs", json={"pages": None}).json()
        job = client.get(f"/jobs/{on['id']}").json()
        review = client.get(f"/projects/{pid}/drawing-review/{did}").json()
        for other in (prov.get_provider(), prov.get_fa_provider(), prov.get_prep_provider()):
            assert isinstance(other, NullProvider)                 # everything else stays off
    finally:
        set_provider(None)
    assert len(built) == 1 and built[0].calls == 2
    assert job["status"] == "succeeded" and review["state"] == "done"
    assert any(f["instruction"] == KNOWN for f in review["findings"])
