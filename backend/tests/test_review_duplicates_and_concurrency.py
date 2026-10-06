"""After the EP-30880 Ground Floor validation (6 October 2026): the same change
proposed by two looks, what a model says that it was not asked, and what other
people do while a run saves. No model is called: recording and rehearsal
providers stand in."""
from __future__ import annotations

import json

from app.ai.provider import NullProvider, RecordingProvider
from app.review import scoped
from tests.test_drawing_review_outcome import WINDOW, _drawing, _review
from tests.test_scoped_drawing_review import _known, _placeholders, _scope, _two_floors

# EP-30880's Ground Floor scale: metres per point of the plot (1:175 on A3)
SCALE = {3: {"geometry": {"a": 0.0617741, "bx": 0, "by": 0}}}


def _f(fid, kind, room, at, *, system="manual_call_point", action="add", device="fire alarm manual call point",
       proposal="Add MCP beside main entrance exit door, inside the airlock", decision="open", previous=None):
    return {"id": fid, "page": 3, "kind": kind, "room": room, "system": system, "action": action, "device": device,
            "instruction": proposal, "proposal": proposal, "at": at, "decision": decision, "by_ruling": False,
            "previous_decision": previous}


# --- the same change from two looks --------------------------------------------------------------------------


def test_two_looks_proposing_the_same_change_become_one_with_every_source_and_decision_kept():
    from app.review import service

    earlier = {"status": "accepted", "at": "2026-10-02", "reason": "not_verifiable"}
    room = _f("r1", "room", "LOBBY", [570.1, 450.5])
    plan = _f("s1", "sheet", "Main entrance final exit doors (airlock, top of LOBBY)", [597.0, 465.0],
              proposal="Add an MCP beside the main entrance exit door, inside the airlock", previous=earlier)
    findings = [room, plan]
    merged, flagged = service.reconcile_duplicates(findings, {"s1": {"status": "accepted", "history": []}}, SCALE)
    assert merged == 1 and not flagged and findings == [room]
    source = room["sources"][0]
    assert (source["id"], source["kind"], source["metres"]) == ("s1", "sheet", 1.9)
    assert source["previous_decision"] == earlier            # the earlier acceptance kept, not carried over
    assert room["decision"] == "open"


def test_a_pair_not_shown_to_be_one_change_is_flagged_never_merged_or_dropped():
    from app.review import service

    room = _f("r1", "room", "LOBBY", [570.1, 450.5])
    fls = _f("f1", "fls", "Main entrance / airlock at top of LOBBY (final exit)", [972.0, 599.5],
             proposal="Add an MCP on the wall inside the main entrance airlock, beside the exit doors")
    sign = dict(system="exit_sign", device="single directional emergency sign")
    bend = _f("o1", "other", "Driveway bend, top-right (top driveway curving)", [1500, 300], **sign,
              proposal="Add a single directional sign at the bend")
    bend2 = _f("s2", "sheet", "Driveway bend, top-right (top 6 m two-way driveway)", [1660, 320], **sign,
               proposal="Add a directional sign at the top-right driveway bend")
    lower = _f("s3", "sheet", "Driveway bend, right-lower (right driveway)", [1900, 700], **sign,
               proposal="Add a directional sign at the right-lower bend")
    findings = [room, fls, bend, bend2, lower]
    merged, flagged = service.reconcile_duplicates(findings, {}, SCALE)
    assert merged == 0 and len(findings) == 5
    pairs = {(p["a"], p["b"]): p for p in flagged}
    assert set(pairs) == {("r1", "f1"), ("o1", "s2")}          # "right-lower" is another place
    assert "described as the same place, but the points disagree" in pairs[("r1", "f1")]["reasons"]
    assert pairs[("r1", "f1")]["metres"] == 26.5
    assert room["possible_duplicates"][0]["id"] == "f1" and fls["possible_duplicates"][0]["id"] == "r1"


def test_decisions_are_never_moved_or_overridden_by_a_merge():
    from app.review import service

    light = dict(system="emergency_light", device="emergency light (E)")
    # two rooms' own findings, side by side: never one
    a = _f("r1", "room", "POD TOILET", [100, 100], **light, proposal="Add emergency light E inside pod toilet")
    b = _f("r2", "room", "BATH", [110, 100], **light, proposal="Add emergency light E inside bath")
    assert service.reconcile_duplicates([a, b], {}, SCALE) == (0, [])
    # the same change, decided differently: both stay, flagged
    room = _f("r1", "room", "LOBBY", [570.1, 450.5], decision="accepted")
    plan = _f("s1", "sheet", "LOBBY airlock", [580.0, 455.0], decision="dismissed")
    findings = [room, plan]
    merged, flagged = service.reconcile_duplicates(findings, {}, SCALE)
    assert merged == 0 and len(findings) == 2 and "decided differently" in flagged[0]["reasons"][-1]
    # the same change, decided on the plan pass's: that one is kept, the decision stays where it was made
    room = _f("r1", "room", "LOBBY", [570.1, 450.5])
    plan = _f("s1", "sheet", "LOBBY airlock", [580.0, 455.0], decision="accepted")
    findings = [room, plan]
    service.reconcile_duplicates(findings, {}, SCALE)
    assert findings == [plan] and plan["decision"] == "accepted" and plan["sources"][0]["id"] == "r1"
    # the engineer said they are two changes: no longer flagged
    room = _f("r1", "room", "LOBBY", [570.1, 450.5])
    fls = _f("f1", "fls", "Main entrance airlock at top of LOBBY", [972.0, 599.5], decision="accepted")
    assert service.reconcile_duplicates([room, fls], {"f1": {"distinct_from": ["r1"]}}, SCALE) == (0, [])


def test_a_possible_duplicate_is_not_accepted_twice_without_the_engineers_word(client, db_session, monkeypatch,
                                                                              tmp_path):
    from app.models import ProjectDrawingReview

    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "50030")
    # the plan pass proposes the electrical room's emergency light again, elsewhere on the plan
    sheet = {"findings": [{"system": "emergency_light", "where": "ELECTRICAL ROOM door", "issue": "No E at the door",
                           "action": "add", "device": "emergency light (E)", "instruction": "Add E at the door",
                           "x": 0.95, "y": 0.95, "severity": "medium"}]}
    _job, review = _review(client, pid, did, RecordingProvider([WINDOW, sheet]))
    room = _known(review)
    plan = next(f for f in review["findings"] if f["kind"] == "sheet")
    assert room["possible_duplicates"][0]["id"] == plan["id"]
    url = f"/projects/{pid}/drawing-review/{did}/decisions"
    assert client.post(url, json={"id": room["id"], "status": "accepted"}).status_code == 200
    bulk = client.post(f"{url}/bulk", json={"ids": [plan["id"]], "status": "accepted"}).json()
    assert bulk["skipped_possible_duplicates"] == [plan["id"]]         # in bulk: left for one by one
    refused = client.post(url, json={"id": plan["id"], "status": "accepted"})
    assert refused.status_code == 409 and "Possibly the same change" in refused.json()["detail"]
    ok = client.post(url, json={"id": plan["id"], "status": "accepted", "confirm_distinct": True})
    assert ok.status_code == 200
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    assert row.decisions[plan["id"]]["distinct_from"] == [room["id"]]
    after = {f["id"]: f for f in ok.json()["findings"]}
    assert not after[plan["id"]].get("possible_duplicates") and after[plan["id"]]["decision"] == "accepted"


# --- what a model says that it was not asked ---------------------------------------------------------------


class _Asks:
    """The continuation's stand-in: answers the rooms it is asked, and talks
    about another room besides (LOBBY) that it was not asked about."""

    name, ready, status = "asks", True, "test"

    def __init__(self, hook=None):
        self.calls, self.hook = 0, hook
        self.inner = scoped.RehearsalProvider(turns=1)

    def complete(self, request):
        self.calls += 1
        if self.hook:
            self.hook(self.calls)
        response = self.inner.complete(request)
        if request.task == "fa_drawing_review_window" and response.data:
            response.data["other"] = [{"image": 1, "system": "emergency_light", "where": "LOBBY",
                                       "issue": "The lobby needs another emergency light", "action": "add",
                                       "device": "emergency light (E)", "instruction": "Add E in the lobby",
                                       "x": 0.2, "y": 0.2}]
        return response


def _half_reviewed(client, db_session, monkeypatch, tmp_path, ep):
    """Ground floor: LOBBY answered and its finding accepted; ELECTRICAL ROOM
    not answered; the plan pass not asked."""
    pid, did, sha = _two_floors(client, db_session, monkeypatch, tmp_path, ep)
    _review(client, pid, did, scoped.RehearsalProvider())
    _placeholders(db_session, pid, did)
    scoped.run(_scope(ep, did, sha, max_turns=1), lambda: scoped.RehearsalProvider(skip_rooms=1, turns=2))
    lobby = next(f for f in client.get(f"/projects/{pid}/drawing-review/{did}").json()["findings"]
                 if f["room"] == "LOBBY" and f["action"] == "add")
    assert client.post(f"/projects/{pid}/drawing-review/{did}/decisions",
                       json={"id": lobby["id"], "status": "accepted"}).status_code == 200
    return pid, did, sha, lobby


def test_what_a_room_only_reask_says_about_another_room_is_kept_apart_and_applied_to_nothing(
        client, db_session, monkeypatch, tmp_path):
    from app.models import ProjectDrawingReview

    pid, did, sha, lobby = _half_reviewed(client, db_session, monkeypatch, tmp_path, "50031")
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    decisions = json.dumps(row.decisions, sort_keys=True)

    report = scoped.run(_scope("50031", did, sha, max_turns=1, max_reported_turns=1), lambda: _Asks())

    view = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    floor = next(f for f in view["floors"] if f["page"] == 0)
    assert [u["issue"] for u in floor["unsolicited"]] == ["The lobby needs another emergency light"]
    assert floor["unsolicited"][0]["asked_rooms"] == ["ELECTRICAL ROOM"]
    after = next(f for f in view["findings"] if f["id"] == lobby["id"])
    assert after["decision"] == "accepted" and not after.get("sources") and not after.get("possible_duplicates")
    assert not [f for f in view["findings"] if "another emergency light" in (f.get("instruction") or "")]
    db_session.refresh(row)
    assert json.dumps(row.decisions, sort_keys=True) == decisions
    assert report["review"]["floor"]["rooms_not_reviewed"] == []


# --- what other people do while a run saves ----------------------------------------------------------------


def test_an_engineers_decision_and_a_review_started_during_a_continuation_both_hold(client, db_session, monkeypatch,
                                                                                   tmp_path):
    from app.models import BackgroundJob, ProjectDrawingReview

    pid, did, sha, lobby = _half_reviewed(client, db_session, monkeypatch, tmp_path, "50032")
    url = f"/projects/{pid}/drawing-review/{did}"
    first = lobby                     # accepted before the run; the engineer changes their mind during it
    seen = {}

    def during(n):
        if n == 1:
            # the engineer decides while the run is saving its answers
            seen["decision"] = client.post(f"{url}/decisions", json={"id": first["id"], "status": "dismissed",
                                                                     "note": "not needed here"}).status_code
            # and someone starts a full review: the running job is the answer, nothing new is queued
            seen["start"] = client.post(f"{url}/jobs", json={"pages": None}).json()

    report = scoped.run(_scope("50032", did, sha, max_turns=1, max_reported_turns=1), lambda: _Asks(hook=during))

    assert seen["decision"] == 200 and seen["start"]["id"] == report["job"]["id"]
    assert not db_session.query(BackgroundJob).filter(BackgroundJob.project_id == pid,
                                                      BackgroundJob.id > report["job"]["id"]).count()
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    assert row.decisions[first["id"]]["status"] == "dismissed"           # the engineer's word stands
    assert [h["status"] for h in row.decisions[first["id"]]["history"]] == ["accepted"]
    view = client.get(url).json()
    ground = next(f for f in view["floors"] if f["page"] == 0)
    assert sum(1 for r in ground["rooms"] if r["checks"]) == 2 and view["state"] == "partial"   # floor 2 not asked

    # a full review started afterwards, with the model off: blocked -- the results stay, the attempt apart
    job, after = _review(client, pid, did, NullProvider())
    assert job["status"] == "failed" and after["counts"]["reviewed"] == view["counts"]["reviewed"]
    assert after["state"] == view["state"] and after["last_attempt"]["status"] == "blocked"
    assert next(f for f in after["findings"] if f["id"] == first["id"])["decision"] == "dismissed"


def test_the_runs_own_write_to_the_decisions_never_drops_one_made_meanwhile(client, db_session, monkeypatch,
                                                                           tmp_path):
    from app.database import SessionLocal
    from app.models import Project, ProjectDrawingReview, ProjectIfcDrawing
    from app.review import service
    from tests.test_drawing_review_outcome import SHEET

    pid, did, _plots = _drawing(client, db_session, monkeypatch, tmp_path, "50033")
    _review(client, pid, did, RecordingProvider([WINDOW, SHEET]))
    fid = _known(client.get(f"/projects/{pid}/drawing-review/{did}").json())["id"]
    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    row.decisions = {fid: {"status": "accepted", "by": 1, "at": row.finished_at.isoformat() + "1"}}   # no basis yet
    db_session.commit()
    real_build = service.build

    def build_then_decide(db, project, drawing):
        out = real_build(db, project, drawing)
        other = SessionLocal()                                             # an engineer, meanwhile
        try:
            r = other.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
            r.decisions = {**r.decisions, "meanwhile": {"status": "dismissed", "note": "x", "by": 2, "at": "z"}}
            other.commit()
        finally:
            other.close()
        return out

    monkeypatch.setattr(service, "build", build_then_decide)
    fresh = SessionLocal()
    try:
        r = fresh.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
        service._keep_bases(fresh, fresh.get(Project, pid), fresh.get(ProjectIfcDrawing, did), r)
    finally:
        fresh.close()
    db_session.refresh(row)
    assert row.decisions["meanwhile"]["status"] == "dismissed"              # the engineer's, kept
    assert row.decisions[fid].get("basis") is not None                       # and the basis written


def test_a_pair_flagged_before_a_merge_names_the_finding_left_on_show_and_never_two_rooms():
    """The full EP-30880 review: 175 of 226 flags pointed at findings merged
    away. A flag follows its finding into the one kept; a pair that becomes
    two rooms' own findings, or one finding, is no pair."""
    from app.review import service

    sign = dict(system="exit_sign", device="exit sign")
    stair = _f("r1", "room", "STAIR-1", [100, 100], **sign, proposal="Add exit sign at stair 1 door")
    other = _f("o1", "other", "STAIR-1 door", [101, 100], **sign, proposal="Add exit sign at stair 1 door")
    lobby = _f("r2", "room", "LIFT LOBBY", [150, 100], **sign, proposal="Add exit sign in lift lobby")   # 3.1 m
    plan = _f("s1", "sheet", "LIFT LOBBY by stair 1", [140, 100], **sign,
              proposal="Directional sign pointing to the exit")       # 2.4 m from the other look, worded apart
    findings = [stair, other, lobby, plan]
    merged, flagged = service.reconcile_duplicates(findings, {}, SCALE)
    shown = {f["id"] for f in findings}
    assert merged == 1 and "o1" not in shown                          # the other look merged into STAIR-1
    assert all(p["a"] in shown and p["b"] in shown for p in flagged)
    assert not [p for p in flagged if {p["a"], p["b"]} == {"r1", "r2"}]  # two rooms: never a pair
    assert all(d["id"] in shown for f in findings for d in f.get("possible_duplicates") or [])
    # the other look's flag against the plan pass now names STAIR-1, the finding it was merged into
    assert {"r1", "s1"} in [{p["a"], p["b"]} for p in flagged]
