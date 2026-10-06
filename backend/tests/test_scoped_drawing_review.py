"""The validation run (app.review.scoped, EP-30880, 6 October 2026): one
floor of a drawing asked of the model on a fixed call budget, in a process of
its own -- and what such a run must not do: ask about another floor, leave a
window unasked yet counted, carry an engineer's decision over to a proposal
it was not made on, or leave the review's switch on after it ends. No model
is called here: the rehearsal provider and recording providers stand in."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess

import pymupdf
import pytest

from app.ai import provider as prov
from app.ai.provider import AiRequest, AiResponse, ClaudeCodeProvider, RecordingProvider, TextPart, set_provider
from app.core.config import get_settings
from app.review import scoped
from tests.conftest import login
from tests.test_drawing_review_outcome import KNOWN, SHEET, WINDOW, _c, _drawing, _review
from tests.test_provider_honesty import FakeCli, _reply

settings = get_settings()


def _page(doc, title, rooms):
    page = doc.new_page(width=2384, height=1684)
    for (x, y), name in rooms:
        page.insert_text((x, y), name, fontsize=10)
    page.insert_text((2100, 300), "LEGENDS", fontsize=9)
    page.insert_text((2100, 1500), title, fontsize=12)


def _two_floors(client, db_session, monkeypatch, tmp_path, ep):
    """A project whose FA drawing has two floor plans, its file, and the
    plot of that file kept where the review keeps it (so nothing is plotted)."""
    import app.routers.jobs as jobs_router
    from app.models import ProjectIfcDrawing
    from app.review import render, service

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    src = tmp_path / "fa.dwg"
    src.write_bytes(b"a drawing " + ep.encode())
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    folder = tmp_path / "review"
    folder.mkdir()
    doc = pymupdf.open()
    _page(doc, "GROUND FLOOR PLAN", [((400, 500), "LOBBY"), ((900, 500), "ELECTRICAL ROOM")])
    _page(doc, "FIRST FLOOR PLAN", [((400, 500), "OFFICE"), ((900, 500), "STORE ROOM")])
    doc.save(folder / f"{sha[:24]}.pdf")
    monkeypatch.setattr(render, "source_file", lambda project, drawing: src)
    monkeypatch.setattr(render, "folder", lambda project: folder)
    monkeypatch.setattr(service.storage, "relative", lambda path: str(path))
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": ep, "project_name": "Tower", "design_sheets": []}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA LAYOUT.dwg", stored_path="x.dxf", revision="R0",
                                meta={"sheets": [{"name": "FA-104", "title": "GROUND FLOOR PLAN", "kind": "plan"},
                                                 {"name": "FA-105", "title": "FIRST FLOOR PLAN", "kind": "plan"}]},
                                groups=[])
    db_session.add(drawing)
    db_session.commit()
    return pid, drawing.id, sha


def _placeholders(db_session, pid, did):
    """The live row's shape before the validation: every look saved "done"
    by the disabled provider, nothing in it."""
    from app.models import ProjectDrawingReview

    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    sheets = json.loads(json.dumps(row.sheets))
    for sh in sheets:
        for w in sh["windows"]:
            w.update(answers={}, other=[], model="null", status="done")
        sh.update(sheet_findings=[], sheet_status="done", sheet_model="null")
    row.sheets, row.status = sheets, "done"
    db_session.commit()


def _scope(ep, did, sha, **kw):
    values = dict(ep_number=ep, drawing_id=did, page=0, floor="GROUND FLOOR", source_sha=sha[:12], max_calls=2,
                  max_turns=2)
    values.update(kw)
    return scoped.Scope(**values)


def _restored(saved):
    s = get_settings()
    assert {k: getattr(s, k) for k in saved} == saved
    assert prov._review_provider is None
    assert not any(k in os.environ for k in scoped.CLI_ENV)
    assert type(prov.get_review_provider()).__name__ == "NullProvider"
    from app.compliance import assist
    assert assist.call_task.__name__ == "call_task"          # stored answers are reused again outside the run


SAVED = ("drawing_review_ai_enabled", "drawing_review_max_calls", "ai_cli_max_turns", "ai_cli_inline_images",
         "drawing_review_parallel")


# --- the run ---------------------------------------------------------------------------------------------------


def test_the_scoped_run_asks_about_the_named_floor_alone_and_puts_every_setting_back(
        client, db_session, monkeypatch, tmp_path):
    from app.models import BackgroundJob, BackgroundWorker

    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "50001")
    _review(client, pid, did, scoped.RehearsalProvider())
    _placeholders(db_session, pid, did)
    saved = {k: getattr(settings, k) for k in SAVED}

    seen = {}

    def factory():
        seen.update(inline=settings.ai_cli_inline_images, turns=settings.ai_cli_max_turns,
                    switch=settings.drawing_review_ai_enabled, retries=os.environ.get("CLAUDE_CODE_MAX_RETRIES"))
        return scoped.RehearsalProvider(turns=1)              # pictures inline: one turn a call

    report = scoped.run(_scope("50001", did, sha, inline_images=True, max_turns=1), factory)
    assert seen == {"inline": True, "turns": 1, "switch": True, "retries": "0"}     # on inside the run only

    # what was asked -- afresh, the seed's stored answers notwithstanding: the ground floor's window
    # call and its plan, nothing of the first floor
    assert [i["task"] for i in report["invocations"]] == ["fa_drawing_review_window", "fa_drawing_review_sheet"]
    said = json.dumps([i["evidence"] for i in report["invocations"]])
    assert "GROUND FLOOR" in said and "LOBBY" in said and "OFFICE" not in said and "FIRST FLOOR" not in said
    assert report["plan"]["rooms"] == 2 and len(report["plan"]["calls"]) == 2
    # what the page shows: the floor reviewed, room by room; the drawing partly
    floor = report["review"]["floor"]
    assert floor["rooms"] == floor["reviewed"] == 2 and floor["room_status"] == {"done": 2}
    assert report["review"]["state"] == "partial"
    assert any(f["instruction"] == scoped.RehearsalProvider.KNOWN for f in report["review"]["findings"])
    view = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    first = next(f for f in view["floors"] if f["page"] == 1)
    assert {r["status"] for r in first["rooms"]} == {"pending"}      # the other floor: not asked, not counted
    assert view["counts"]["reviewed"] == 2 and view["counts"]["rooms"] == 4
    # the job: finished, held by the run and let go
    job = db_session.get(BackgroundJob, report["job"]["id"])
    db_session.refresh(job)
    assert job.status == "succeeded" and job.params["pages"] == [0]
    assert db_session.query(BackgroundWorker).filter(BackgroundWorker.id == job.worker_id).one().stopped_at
    # everything as it was
    _restored(saved)
    assert report["env_file_unchanged"] and report["settings_after"]["drawing_review_ai_enabled"] is False


def test_a_scoped_run_whose_calls_all_fail_keeps_the_answers_and_decisions_and_puts_everything_back(
        client, db_session, monkeypatch, tmp_path):
    from app.models import ProjectDrawingReview

    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "50002")
    _job, review = _review(client, pid, did, scoped.RehearsalProvider())
    finding = next(f for f in review["findings"] if f["page"] == 0 and f["action"] == "add")
    url = f"/projects/{pid}/drawing-review/{did}/decisions"
    assert client.post(url, json={"id": finding["id"], "status": "accepted"}).status_code == 200
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    sheets = json.loads(json.dumps(row.sheets))
    sheets[0]["sheet_status"] = "failed"                     # the floor's plan pass left to ask
    row.sheets = sheets
    db_session.commit()
    before = json.dumps([row.sheets, row.decisions], sort_keys=True)
    saved = {k: getattr(settings, k) for k in SAVED}

    # the answered windows are kept (not asked again, the ruling notwithstanding); the plan pass fails
    report = scoped.run(_scope("50002", did, sha), lambda: scoped.RehearsalProvider(fail=True))

    assert report["job"]["status"] == "failed" and "review has not completed" in report["job"]["error"]
    assert [i["task"] for i in report["invocations"]] == ["fa_drawing_review_sheet"]
    db_session.refresh(row)
    assert json.dumps([row.sheets, row.decisions], sort_keys=True) == before
    kept = next(f for f in client.get(f"/projects/{pid}/drawing-review/{did}").json()["findings"]
                if f["id"] == finding["id"])
    assert kept["decision"] == "accepted"
    _restored(saved)


def test_a_run_that_breaks_off_fails_its_job_and_still_puts_everything_back(client, db_session, monkeypatch,
                                                                            tmp_path):
    from app.ifc.services import runners
    from app.models import BackgroundJob

    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "50003")
    saved = {k: getattr(settings, k) for k in SAVED}

    class Killed(BaseException):
        pass

    def boom(*_a, **_k):
        raise Killed()

    monkeypatch.setattr(runners, "run_drawing_review", boom)
    with pytest.raises(Killed):
        scoped.run(_scope("50003", did, sha), lambda: scoped.RehearsalProvider())
    job = db_session.query(BackgroundJob).filter(BackgroundJob.project_id == pid).order_by(BackgroundJob.id.desc()).first()
    db_session.refresh(job)
    assert job.status == "failed" and "without finishing" in job.error   # never left running for a worker
    _restored(saved)


def test_the_scoped_run_refuses_before_asking_anything(client, db_session, monkeypatch, tmp_path):
    from app.models import BackgroundJob, ProjectDrawingReview

    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "50004")
    built = []

    def factory():
        built.append(1)
        return scoped.RehearsalProvider()

    cases = [
        (dict(floor="FIRST FLOOR"), "not 'FIRST FLOOR'"),             # page 0 is the ground floor
        (dict(page=5), "not a floor plan"),
        (dict(source_sha="0" * 12), "not the"),                       # another file than the one named
        (dict(max_calls=1), "windows would be left unasked"),          # the window call and the plan need 2
        (dict(source_sha="abc"), "12 characters"),
    ]
    for change, said in cases:
        with pytest.raises(scoped.Refused, match=said):
            scoped.run(_scope("50004", did, sha, **change), factory)
    monkeypatch.setattr(settings, "ai_enabled", True)
    with pytest.raises(scoped.Refused, match="AI_ENABLED"):
        scoped.run(_scope("50004", did, sha), factory)
    monkeypatch.setattr(settings, "ai_enabled", False)
    # a review already running
    row = ProjectDrawingReview(project_id=pid, drawing_id=did, sheets=[], decisions={}, status="running")
    db_session.add(row)
    db_session.commit()
    with pytest.raises(scoped.Refused, match="running"):
        scoped.run(_scope("50004", did, sha), factory)
    row.status = "done"
    db_session.commit()
    # no plot of the file: AutoCAD is never started
    from app.review import render
    (render.folder(None) / f"{sha[:24]}.pdf").unlink()
    with pytest.raises(scoped.Refused, match="AutoCAD"):
        scoped.run(_scope("50004", did, sha), factory)
    assert not built and not db_session.query(BackgroundJob).filter(BackgroundJob.project_id == pid).count()


def test_the_guard_counts_every_call_refuses_one_past_the_limit_and_stops_on_more_than_it_should():
    class Inner:
        def __init__(self, **reply):
            self.reply, self.calls = reply, 0

        def complete(self, request):
            self.calls += 1
            return AiResponse(data={"ok": 1}, model="claude-opus-5-5", **self.reply)

    request = AiRequest(task="t", system="s", parts=[TextPart("floor", "GROUND FLOOR")], schema={}, max_output_tokens=1,
                        model="claude-opus-5-5")
    inner = Inner(turns=2, models_used={"claude-opus-5-5": 9})
    guard = scoped.Guard(inner, limit=2, max_turns=2)
    assert guard.complete(request).ok and guard.complete(request).ok
    assert guard.complete(request).error == "invocation_limit" and inner.calls == 2
    for reply, said in ((dict(turns=3), "3 turns"),
                        (dict(turns=1, models_used={"claude-opus-5-5": 9, "claude-haiku-4-5": 1}), "other models"),
                        (dict(turns=1, error="rate_limit", error_detail="usage limit reached"), "rate_limit")):
        inner = Inner(**reply)
        guard = scoped.Guard(inner, limit=4, max_turns=2)
        guard.complete(request)
        assert said in guard.stopped
        assert guard.complete(request).error == "stopped" and inner.calls == 1    # nothing more is asked
        assert guard.invocations[0]["evidence"] == [{"label": "floor", "text": "GROUND FLOOR"}]
    # answered under another name than the model asked for: stopped
    inner = Inner(turns=1)
    inner.complete = lambda r: AiResponse(data={"ok": 1}, model="claude-opus-5", turns=1)
    guard = scoped.Guard(inner, limit=4, max_turns=2)
    guard.complete(request)
    assert "not the 'claude-opus-5-5'" in guard.stopped and guard.complete(request).error == "stopped"
    # a request about another floor is never sent, and nothing more is
    inner = Inner(turns=1)
    guard = scoped.Guard(inner, limit=4, max_turns=2, floor="GROUND FLOOR")
    other = AiRequest(task="t", system="s", parts=[TextPart("floor", "1ST FLOOR -- 1ST FLOOR PLAN")], schema={},
                      max_output_tokens=1, model="claude-opus-5-5")
    assert guard.complete(other).error == "out_of_scope" and inner.calls == 0 and not guard.invocations
    assert guard.complete(request).error == "stopped" and inner.calls == 0
    assert scoped.Guard(Inner(turns=1), limit=4, max_turns=2, floor="GROUND FLOOR").complete(request).ok


# --- the engineer's decisions, kept to the proposal they were made on -------------------------------------------


def _moved(device=None, x=None, instruction=None):
    window = json.loads(json.dumps(WINDOW))
    check = next(c for c in window["rooms"][1]["checks"] if c["system"] == "emergency_light")
    if device is not None:
        check["device"] = device
    if x is not None:
        check["x"] = x
    if instruction is not None:
        check["instruction"] = instruction
    return window


def _accept(client, pid, did):
    review = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    finding = next(f for f in review["findings"] if f["instruction"] == KNOWN)
    assert client.post(f"/projects/{pid}/drawing-review/{did}/decisions",
                       json={"id": finding["id"], "status": "accepted"}).status_code == 200
    return finding["id"]


def _ask_again(db_session, pid, did):
    """The next review asks the floor again, as a new drawing revision or
    prompt would make it: its windows and plan pass not done, nothing stored."""
    from app.models import ProjectDrawingReview, ResultCache

    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    sheets = json.loads(json.dumps(row.sheets))
    for sh in sheets:
        for w in sh["windows"]:
            w["status"] = "pending"
        sh["sheet_status"] = None
    row.sheets = sheets
    db_session.query(ResultCache).delete()
    db_session.commit()


def _known(review):
    return next(f for f in review["findings"] if f["room"] == "ELECTRICAL ROOM" and f["system"] == "emergency_light")


def test_an_acceptance_stays_only_while_the_proposal_is_the_same(client, db_session, monkeypatch, tmp_path):
    from app.models import ProjectDrawingReview

    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "50010")
    _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    fid = _accept(client, pid, did)

    # asked again (the acceptance is a ruling: a new question) -- the same proposal: still accepted
    _job, again = _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    assert _known(again)["id"] == fid and _known(again)["decision"] == "accepted"
    assert _known(again)["previous_decision"] is None

    # the point moves a little: the same location
    _ask_again(db_session, pid, did)
    _job, nudged = _review(client, pid, did, RecordingProvider([_moved(x=0.52), SHEET]))
    assert _known(nudged)["decision"] == "accepted"

    # another device: decided again, the acceptance kept as history
    _ask_again(db_session, pid, did)
    _job, changed = _review(client, pid, did, RecordingProvider([_moved(device="maintained emergency light (EM)"),
                                                                 SHEET]))
    f = _known(changed)
    assert f["id"] == fid and f["decision"] == "open"
    assert f["previous_decision"]["status"] == "accepted" and f["previous_decision"]["changed"] == ["device"]
    assert f["previous_decision"]["reason"] == "proposal_changed"
    assert changed["counts"]["accepted"] == 0
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    assert row.decisions[fid]["status"] == "accepted"            # the record itself is not lost

    # accepted again (one by one or in bulk): in force, with the earlier one in its history
    bulk = client.post(f"/projects/{pid}/drawing-review/{did}/decisions/bulk", json={"ids": [fid], "status": "accepted"})
    assert _known(bulk.json())["decision"] == "accepted"
    db_session.refresh(row)
    assert [h["status"] for h in row.decisions[fid]["history"]] == ["accepted"]
    assert row.decisions[fid]["basis"]["device"] == "maintained emergency light (em)"

    # elsewhere on the plan, or another recommendation: decided again
    for window, what in ((_moved(device="maintained emergency light (EM)", x=0.95), "location"),
                         (_moved(device="maintained emergency light (EM)", instruction="Add two"), "recommendation")):
        _ask_again(db_session, pid, did)
        _job, view = _review(client, pid, did, RecordingProvider([window, SHEET]))
        assert _known(view)["decision"] == "open" and what in _known(view)["previous_decision"]["changed"]


def test_a_decision_made_before_proposals_were_kept_stands_only_until_a_review_runs(client, db_session, monkeypatch,
                                                                                    tmp_path):
    from app.models import ProjectDrawingReview

    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "50011")
    _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    fid = _known(client.get(f"/projects/{pid}/drawing-review/{did}").json())["id"]
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    after_run = (row.finished_at.isoformat() + "1")             # just after the run the proposal came from
    before_run = row.started_at.replace(year=2020).isoformat()
    row.decisions = {fid: {"status": "accepted", "note": "", "instruction": "", "by": 1, "at": after_run}}
    db_session.commit()
    assert _known(client.get(f"/projects/{pid}/drawing-review/{did}").json())["decision"] == "accepted"

    # a review runs: the proposal it was made on is kept first, so the same proposal keeps it
    _job, again = _review(client, pid, did, RecordingProvider([WINDOW, SHEET], ))
    db_session.refresh(row)
    assert row.decisions[fid].get("basis") is not None
    assert _known(again)["decision"] == "accepted"

    # one from before the last run, with nothing to show what it was made on: decided again
    row.decisions = {fid: {"status": "accepted", "note": "as on 1 October", "instruction": "", "by": 1,
                           "at": before_run}}
    db_session.commit()
    f = _known(client.get(f"/projects/{pid}/drawing-review/{did}").json())
    assert f["decision"] == "open" and f["previous_decision"]["note"] == "as on 1 October"
    assert f["previous_decision"]["reason"] == "not_verifiable" and f["previous_decision"]["changed"] == []
    assert "cannot be shown" in f["previous_decision"]["message"]


# --- every room of a window, or the window is not done ----------------------------------------------------------


def test_a_window_the_model_answered_for_some_rooms_is_not_done_and_is_asked_again(client, db_session, monkeypatch,
                                                                                  tmp_path):
    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "50012")
    only_lobby = {"rooms": [WINDOW["rooms"][0]], "other": []}
    _job, review = _review(client, pid, did, RecordingProvider([only_lobby, SHEET]))
    rooms = {r["name"]: r for f in review["floors"] for r in f["rooms"]}
    assert rooms["LOBBY"]["status"] == "done" and rooms["LOBBY"]["checks"]
    assert rooms["ELECTRICAL ROOM"]["status"] == "incomplete" and rooms["ELECTRICAL ROOM"]["checks"] is None
    assert "ELECTRICAL ROOM" in rooms["ELECTRICAL ROOM"]["error"]
    assert review["state"] == "partial" and review["counts"]["reviewed"] == 1

    provider = RecordingProvider([WINDOW])                       # only the window left unfinished is asked
    _job, again = _review(client, pid, did, provider)
    assert provider.calls == 1 and again["state"] == "done" and again["counts"]["reviewed"] == 2


# --- the Claude Code route: its turns, limited and counted -------------------------------------------------------


def test_the_cli_is_given_the_turn_limit_and_its_turns_are_counted(monkeypatch, tmp_path):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    monkeypatch.setattr(settings, "ai_cli_max_turns", 2)
    reply = {**_reply({"claude-opus-5-5": {"outputTokens": 7}}), "num_turns": 2}
    fake = FakeCli(reply=reply)
    monkeypatch.setattr(subprocess, "run", fake)
    request = AiRequest(task="t", system="s", parts=[TextPart("a", "b")], schema={"type": "object"},
                        max_output_tokens=100, model="claude-opus-5-5", exact_model=True)
    response = ClaudeCodeProvider().complete(request)
    assert response.ok and response.turns == 2
    assert fake.calls[0][fake.calls[0].index("--max-turns") + 1] == "2"

    fake.reply = {"type": "result", "subtype": "error_max_turns", "is_error": True, "num_turns": 3,
                  "usage": {"output_tokens": 5}, "modelUsage": {"claude-opus-5-5": {"outputTokens": 5}}}
    response = ClaudeCodeProvider().complete(request)
    assert response.error == "max_turns" and response.turns == 3 and response.data is None

    monkeypatch.setattr(settings, "ai_cli_max_turns", None)
    ClaudeCodeProvider().complete(request)
    assert "--max-turns" not in fake.calls[-1]                   # unset: the CLI's own limit, as before
    set_provider(None)


# --- one look at a time, and the continuation ----------------------------------------------------------------


def test_looks_go_one_at_a_time_so_a_stop_keeps_the_next_from_being_sent(client, db_session, monkeypatch, tmp_path):
    """Job 220 sent two looks at once, so the second was on its way before the
    first reply could be checked. The run now sends one look at a time."""
    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "50020")
    monkeypatch.setattr(settings, "drawing_review_parallel", 2)          # the platform's own setting
    _review(client, pid, did, scoped.RehearsalProvider())
    _placeholders(db_session, pid, did)
    saved = {k: getattr(settings, k) for k in SAVED + ("drawing_review_parallel",)}
    inner = scoped.RehearsalProvider(turns=2)                             # every reply reports 2 turns

    report = scoped.run(_scope("50020", did, sha, max_turns=1), lambda: inner)

    assert inner.calls == 1 and len(report["invocations"]) == 1           # the plan pass was never sent
    assert "reported 2 turns" in report["stopped"]
    floor = report["review"]["floor"]
    # what the one answered look gave is kept and counted; the pass not asked says so
    assert floor["reviewed"] == 2 and floor["rooms_not_reviewed"] == [] and floor["plan_pass"] == "failed"
    assert report["review"]["state"] == "partial"
    view = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    assert view["counts"]["reviewed"] == 2 and view["state"] == "partial"
    _restored(saved)
    assert settings.drawing_review_parallel == 2


def test_the_continuation_asks_only_what_is_left_and_keeps_what_was_answered(client, db_session, monkeypatch,
                                                                            tmp_path):
    from app.models import ProjectDrawingReview

    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, "50021")
    _review(client, pid, did, scoped.RehearsalProvider())
    _placeholders(db_session, pid, did)
    # the first run: one room left unanswered, and stopped before the plan pass
    first = scoped.run(_scope("50021", did, sha, max_turns=1), lambda: scoped.RehearsalProvider(skip_rooms=1, turns=2))
    assert first["review"]["floor"]["rooms_not_reviewed"] == ["ELECTRICAL ROOM"]
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    lobby_window = next(w for w in row.sheets[0]["windows"] if any(r["name"] == "LOBBY" for r in w["rooms"]))
    lobby_answer = json.dumps(lobby_window["answers"], sort_keys=True)
    # the engineer decides on the finding before the continuation: a ruling, so a new prompt
    found = client.get(f"/projects/{pid}/drawing-review/{did}").json()["findings"]
    fid = next(f["id"] for f in found if f["page"] == 0 and f["action"] == "add")
    assert client.post(f"/projects/{pid}/drawing-review/{did}/decisions",
                       json={"id": fid, "status": "accepted"}).status_code == 200
    db_session.refresh(row)
    decisions = json.dumps(row.decisions, sort_keys=True)

    second = scoped.run(_scope("50021", did, sha, max_turns=1, max_reported_turns=1),
                        lambda: scoped.RehearsalProvider(turns=1))

    # exactly what was left: the one room, then the plan pass -- nothing answered is asked again
    assert [(c["task"], c.get("rooms")) for c in second["plan"]["calls"]] == [("window", ["ELECTRICAL ROOM"]),
                                                                              ("sheet", 2)]
    asked = [e["text"] for i in second["invocations"] for e in i["evidence"] if e["label"].endswith(" rooms")]
    assert asked == ["2: ELECTRICAL ROOM"]
    assert second["plan"]["rooms_answered_before"] == 1 and second["plan"]["plan_pass_before"] == "to ask"
    db_session.refresh(row)
    window = next(w for w in row.sheets[0]["windows"] if any(r["name"] == "LOBBY" for r in w["rooms"]))
    assert json.dumps(window["answers"], sort_keys=True) == lobby_answer   # the earlier answer, as it was
    assert json.dumps(row.decisions, sort_keys=True) == decisions
    floor = second["review"]["floor"]
    assert floor["reviewed"] == 2 and floor["rooms_not_reviewed"] == [] and floor["plan_pass"] == "done"
    view = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    ids = [f["id"] for f in view["findings"]]
    assert len(ids) == len(set(ids)) and fid in ids                       # no duplicates; the decided one kept
    assert next(f for f in view["findings"] if f["id"] == fid)["decision"] == "accepted"
    assert view["state"] == "partial"                                      # the first floor was never asked
    # nothing left to ask: refused, not run again
    with pytest.raises(scoped.Refused, match="nothing is left"):
        scoped.run(_scope("50021", did, sha), lambda: scoped.RehearsalProvider())


def test_a_plan_pass_finding_the_room_review_has_is_merged_not_shown_twice():
    from app.review import service

    def f(fid, kind, room, system="manual_call_point", action="add"):
        return {"id": fid, "page": 3, "kind": kind, "room": room, "system": system, "action": action,
                "instruction": f"{kind} says add"}

    room = f("r1", "room", "LOBBY")
    findings = [room, f("s1", "sheet", "Lobby, beside the main entrance"),         # the same: merged
                f("s2", "sheet", "Lobby", system="detection"),                    # another system: kept
                f("s3", "fls", "Driveway bend"),                                  # another place: kept
                f("s4", "sheet", "LOBBY near the door")]                           # decided on: kept
    assert service._merge_passes(findings, {"s4": {"status": "accepted"}}) == 1
    assert [x["id"] for x in findings] == ["r1", "s2", "s3", "s4"]
    assert room["also_seen"] == [{"kind": "sheet", "id": "s1", "instruction": "sheet says add"}]


def test_the_clis_own_account_of_a_call_is_kept(monkeypatch, tmp_path):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    monkeypatch.setattr(settings, "ai_cli_max_turns", 1)
    reply = {**_reply({"claude-opus-5-5": {"outputTokens": 7}}), "num_turns": 2, "stop_reason": "end_turn",
             "duration_ms": 900, "duration_api_ms": 800, "total_cost_usd": 0.1}
    monkeypatch.setattr(subprocess, "run", FakeCli(reply=reply))
    response = ClaudeCodeProvider().complete(AiRequest(task="t", system="s", parts=[TextPart("a", "b")],
                                                       schema={"type": "object"}, max_output_tokens=100,
                                                       model="claude-opus-5-5", exact_model=True))
    assert response.ok and response.route_meta == {
        "subtype": "success", "num_turns": 2, "stop_reason": "end_turn", "duration_ms": 900, "duration_api_ms": 800,
        "total_cost_usd": 0.1, "max_turns_configured": 1, "inline_images": False}
