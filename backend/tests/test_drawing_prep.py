"""Drawings Preparation: the rooms filled from the plan's walls, the detection's
coverage at its radius, the columns kept clear of, the coordination agent's
answer checked against the plan, the orchestrator's review kept to the ids it
was given, and the gate. The model is not called here."""

from app.redesign import agents as AG
from app.redesign import coverage as C
from app.redesign import prepare as PR
from app.redesign import service as R
from app.redesign.walls import Walls

GEOMETRY = {"v": 1, "a": 0.1, "bx": 0.0, "by": 100.0, "residual": 0.4}      # 1 pt = 0.1 m, page y down
SHEET = {"index": 0, "name": "FA 101", "floor": "GROUND FLOOR", "plan": [0, 0, 2000, 2000], "geometry": GEOMETRY}


def _grid(segs) -> dict:
    cells = {}
    for s in segs:
        for i in range(-3, 30):
            for j in range(-3, 30):
                cells.setdefault((i, j), []).append(s)
    return cells


def _room_walls() -> Walls:
    """A 20 x 10 m room (double walls, 0.2 m thick) with a 1 m door at the top
    into a corridor, and a pump set's single outline inside it."""
    inner = [(0, 0, 20, 0), (20, 0, 20, 10), (0, 10, 9, 10), (10, 10, 20, 10), (0, 0, 0, 10)]
    outer = [(-0.2, -0.2, 20.2, -0.2), (20.2, -0.2, 20.2, 10.2), (-0.2, 10.2, 9, 10.2), (10, 10.2, 20.2, 10.2),
             (-0.2, -0.2, -0.2, 10.2)]
    jambs = [(9, 10, 9, 10.2), (10, 10, 10, 10.2)]
    corridor = [(-0.2, 12, 40, 12), (-0.2, 12.2, 40, 12.2)]
    pump = [(4, 4, 6, 4), (6, 4, 6, 6), (6, 6, 4, 6), (4, 6, 4, 4)]          # single lines: not a wall
    return Walls(_grid(inner + outer + jambs + corridor + pump))


def test_a_room_is_filled_inside_its_walls_its_door_closed_and_a_pump_sets_outline_not_a_wall():
    walls = _room_walls()
    # from inside the pump set's outline: still the room, not the box
    room = C.room_at(walls, None, 5.0, 5.0)
    assert not room.open
    assert 190 <= room.area <= 205
    assert room.contains(15.0, 5.0) and not room.contains(15.0, 11.0)       # the corridor is another space


def test_coverage_is_measured_at_the_radius_and_the_best_spots_cover_the_room():
    room = C.room_at(_room_walls(), None, 5.0, 5.0)
    one = C.measure(room, [(10.0, 5.0)], 6.3)
    assert not one["ok"] and one["uncovered_m2"] > 10                        # corners further than 6.3 m
    spots = C.best_spots(room, [], 6.3)
    assert len(spots) == 3                                                   # 20 m long at 6.3 m: three
    assert C.measure(room, spots, 6.3)["ok"]
    # every spot half a metre clear of the walls
    assert all(0.5 <= x <= 19.5 and 0.5 <= y <= 9.5 for x, y in spots)
    # asked for more than the room needs: spread out, never on top of each other
    many = C.best_spots(room, spots, 6.3, count=2)
    assert len(set(many)) == 2 and all(p not in spots for p in many)


def test_a_detector_spot_keeps_off_the_columns():
    columns = C.Columns({(i, j): [(9.7, 4.7, 10.3, 5.3)] for i in range(3, 7) for j in range(1, 4)})
    room = C.room_at(_room_walls(), columns, 2.0, 2.0)
    for x, y in C.best_spots(room, [], 6.3, count=3):
        assert columns.hit((x - 0.1, y - 0.1, x + 0.1, y + 0.1)) is None
    assert columns.hit((10.0, 5.0, 10.1, 5.1)) is not None


def test_the_coordination_moves_a_ceiling_device_off_a_column_and_a_wall_device_along_its_wall():
    columns = C.Columns({(i, j): [(9.7, 4.7, 10.3, 5.3)] for i in range(3, 7) for j in range(1, 4)})
    ceiling = {"id": "c", "status": "proposed", "page": 0, "candidates": [],
               "insert": {"block": "SD", "seen": [10.0, 5.0], "placed": [10.0, 5.0], "model": [10.0, 5.0],
                          "offset": [0, 0], "radius": 0.2}}
    R.coordinate([ceiling], {0: SHEET}, None, None, columns)
    x, y = ceiling["insert"]["seen"]
    assert columns.hit((x - 0.2, y - 0.2, x + 0.2, y + 0.2), R.GAP_M) is None and ceiling.get("coordinated")


def _detector(cid, x, y, status="proposed", moved=False):
    return {"id": cid, "page": 0, "sheet": "FA 101", "floor": "GROUND FLOOR", "room": "STORE", "system": "detection",
            "system_name": "Detection", "action": "add", "device": "smoke detector", "status": status, "moved": moved,
            "box": [0, 0, 400, 400], "candidates": [],
            "insert": {"symbol": 1, "name": "Smoke Detector", "block": "SD", "seen": [x, y], "placed": [x, y],
                       "model": [x, y], "offset": [0, 0], "radius": 0.2, "page": R._page(GEOMETRY, x, y)}}


def test_the_platform_proposes_the_best_spots_and_the_detectors_the_room_still_needs():
    walls = _room_walls()
    a, b = _detector("a", 2.0, 2.0), _detector("b", 3.0, 2.0)
    group = PR.rooms([a, b], {0: SHEET}, walls, None)
    assert len(group) == 1 and len(group[0]["changes"]) == 2                  # one room, both in it
    plan = PR.propose(group[0], {0: SHEET}, [], set(), None)
    assert not plan["open"] and set(plan["moves"]) == {"a", "b"}             # spread out: they covered little
    assert len(plan["extra"]) == 1 and plan["after"]["ok"]                    # and one more needed
    assert any("more detector" in i for i in plan["issues"])
    # a detector the engineer placed is never moved
    c = _detector("c", 2.0, 2.0, moved=True)
    plan = PR.propose(PR.rooms([c], {0: SHEET}, walls, None)[0], {0: SHEET}, [], set(), None)
    assert "c" not in plan["moves"]


def test_the_coordination_agents_layout_is_refused_when_it_covers_less_than_the_platforms():
    walls = _room_walls()
    a = _detector("a", 2.0, 2.0)
    group = PR.rooms([a], {0: SHEET}, walls, None)[0]
    plan = PR.propose(group, {0: SHEET}, [], set(), None)
    group["view"] = [0, 0, 400, 400]
    # the agent keeps it in the corner and asks for nothing more
    reply = {"answer": {"devices": {"N1": {"decision": "keep", "spot": None, "x": None, "y": None, "reason": "fine"}},
                        "extra": [], "confidence": "high", "note": "", "notes": []},
             "labels": [("N1", a)], "spots": {f"S{k}": p for k, p in enumerate(list(plan["moves"].values()) + plan["extra"], 1)}}
    chosen, extra, refused = PR._decide(R, group, SHEET, plan, reply, None)
    assert "room" in refused and chosen["a"][0] == plan["moves"]["a"] and extra == plan["extra"]
    # taking the platform's spots is accepted, as the agent's
    every = list(reply["spots"])
    reply["answer"]["devices"]["N1"] = {"decision": "spot", "spot": every[0], "x": None, "y": None, "reason": "covers"}
    reply["answer"]["extra"] = every[1:]
    chosen, extra, refused = PR._decide(R, group, SHEET, plan, reply, None)
    assert not refused and chosen["a"][1] == "agent" and len(extra) == len(every) - 1


def test_the_agents_answers_are_kept_to_what_they_were_shown_and_their_words_checked():
    coordination = AG.read_coordination({"devices": [{"n": "N1", "decision": "spot", "spot": "S9", "x": 0, "y": 0, "reason": "x"},
                                                     {"n": "N7", "decision": "keep", "spot": "", "x": 0, "y": 0, "reason": ""},
                                                     {"n": "N2", "decision": "point", "x": 1.5, "y": 0.2, "spot": "", "reason": ""}],
                                         "extra": ["S1", "S1", "S8"], "confidence": "sure", "note": "ok"},
                                        {"N1", "N2"}, {"S1", "S2"})
    assert coordination["devices"]["N1"]["decision"] == "keep"              # an unknown spot: kept
    assert coordination["devices"]["N2"]["decision"] == "keep"              # a point off the image: kept
    assert "N7" not in coordination["devices"] and coordination["extra"] == ["S1"]
    assert coordination["confidence"] == "low"
    review = AG.read_review({"verdicts": [{"id": "a", "verdict": "reject", "reason": "duplicate of b"},
                                          {"id": "zzz", "verdict": "ok", "reason": ""}],
                             "summary": "See https://example.com", "open_questions": ["Is the pump room wet?"],
                             "recommendation": "needs_engineer"}, {"a", "b"})
    assert review["verdicts"] == {"a": {"verdict": "reject", "reason": "duplicate of b"}}
    assert review["summary"].startswith("[withheld") and review["notes"]
    assert AG.review_problem({"verdicts": [], "summary": "", "open_questions": [], "recommendation": "maybe"})


def test_a_detector_added_for_coverage_or_rejected_by_the_orchestrator_is_drawn_only_once_approved():
    base = {"action": "add", "insert": {"block": "SD"}, "remove": None}
    # a placement the agents proposed is the engineer's to approve first (6 October 2026)
    assert not R._drawn({**base, "status": "proposed"})
    assert R._drawn({**base, "status": "approved"})
    assert not R._drawn({**base, "status": "proposed", "source": PR.COVERAGE})
    assert R._drawn({**base, "status": "approved", "source": PR.COVERAGE})
    assert not R._drawn({**base, "status": "proposed", "check": {"verdict": "reject", "reason": ""}})
    assert R._drawn({**base, "status": "approved", "check": {"verdict": "reject", "reason": ""}})


def test_with_the_agents_off_a_change_goes_to_the_reviews_point_with_the_drawings_symbol_named_like_it():
    symbols = [{"id": 1, "name": "Smoke Detector (Addressable)", "count": 40},
               {"id": 2, "name": "Heat Detector (Addressable)", "count": 9},
               {"id": 3, "name": "Ceiling Speaker", "count": 50}]
    assert PR.guess_symbol("addressable heat detector (H)", symbols) == 2
    assert PR.guess_symbol("beam", symbols) == 0
    change = {"action": "replace", "device": "heat detector", "box": [0, 0, 100, 100], "at": [25, 75],
              "candidates": [{"n": 1, "name": "Ceiling Speaker"}, {"n": 2, "name": "Smoke Detector"}]}
    answer = PR.fallback_answer(change, symbols)
    assert answer["candidate"] == 2 and answer["symbol"] == 2 and (answer["x"], answer["y"]) == (0.25, 0.75)


def test_the_gate_is_the_platforms_count():
    changes = [{"id": "a", "status": "failed", "action": "add"},
               {"id": "b", "status": "proposed", "action": "add", "check": {"verdict": "reject", "reason": ""}},
               {"id": "c", "status": "proposed", "action": "add", "source": PR.COVERAGE},
               {"id": "d", "status": "proposed", "action": "add", "source": R.INTERFACE, "check": {"verdict": "reject"}}]
    gate = PR.gate(changes, {"gaps_left": 1, "open_rooms": 0}, {"state": "done"}, None)
    assert gate["state"] == "needs_engineer"
    text = " ".join(gate["reasons"])
    assert "1 change could not be placed" in text and "1 rejected" in text and "1 room short" in text
    assert "added for coverage" in text
    ok = PR.gate([{"id": "a", "status": "approved", "action": "add", "check": {"verdict": "ok", "reason": ""}}],
                 {"gaps_left": 0, "open_rooms": 0}, {"state": "done"}, None)
    assert ok == {"state": "ready", "reasons": []}


# --- the agents, through the platform's call path (a fake model) -----------------------------------------------

import json  # noqa: E402
import math  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import pymupdf  # noqa: E402

from app.ai import provider as ai_provider  # noqa: E402
from app.ai.provider import AiResponse, TextPart, Usage  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.models import Project, RoleEnum, User  # noqa: E402
from tests.conftest import make_user  # noqa: E402


class FakeOpus:
    name, ready, status = "fake", True, "a fake provider (tests)"

    def __init__(self):
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        texts = {p.label: p.text for p in request.parts if isinstance(p, TextPart)}
        if request.task == AG.COORDINATION_TASK:
            spots = [s for s in texts["lettered spots"].splitlines() if s.startswith("S")]
            data = {"devices": [{"n": "N1", "decision": "spot", "spot": spots[0], "x": 0, "y": 0,
                                 "reason": "the middle of the store"}],
                    "extra": spots[1:], "confidence": "high", "note": "two more for the far ends"}
        else:
            payload = json.loads(next(iter(texts.values())))
            ids = [c["id"] for c in payload["changes"]]
            data = {"verdicts": [{"id": i, "verdict": "check" if i == ids[0] else "ok", "reason": "look at it"}
                                 for i in ids],
                    "summary": "The store is covered.", "open_questions": ["Is there a false ceiling?"],
                    "recommendation": "needs_engineer"}
        return AiResponse(data=data, usage=Usage(input_tokens=500, output_tokens=60), model=request.model, latency_ms=1)


def test_the_coordination_agent_and_the_orchestrator_run_side_by_side_through_the_call_path(db_session, tmp_path,
                                                                                             monkeypatch):
    from app.review import service as review

    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", True)
    monkeypatch.setattr(PR, "prep_ai_on", lambda: True)
    fake = FakeOpus()
    ai_provider.set_provider(fake)
    try:
        plot = pymupdf.open()
        plot.new_page(width=2000, height=2000)
        pdf = str(tmp_path / "plot.pdf")
        plot.save(pdf)
        user = db_session.query(User).first() or make_user(db_session, "prep@x.com", RoleEnum.fire_alarm_design_engineer)
        project = Project(ep_number="40777", project_name="Prep", created_by_id=user.id)
        db_session.add(project)
        db_session.commit()
        row = SimpleNamespace(calls=0, changes=[], run=None)
        agents = []
        a = _detector("a", 2.0, 2.0)
        a["at"] = R._page(GEOMETRY, 2.0, 2.0)
        budget = review._budget(db_session, project)
        changes, stats = PR.coordinate(db_session, project, pdf, "sha", {0: SHEET}, [a], [], _room_walls(), None, [],
                                       None, budget, row, agents.append, lambda *_: None, None, {})
        assert stats["agent_rooms"] == 1 and stats["refused"] == 0
        assert a["coordination"]["by"] == "agent" and a["coordination"]["reason"] == "the middle of the store"
        added = [c for c in changes if c.get("source") == PR.COVERAGE]
        assert added and all(c["status"] == "proposed" and c["coordination"]["by"] == "agent" for c in added)
        assert all(c["coverage"]["ok"] for c in [a] + added)                  # the room covered at 6.3 m
        reviewed = PR.review(db_session, project, "sha", {0: SHEET}, changes, None, budget, row, agents.append,
                             lambda *_: None, None)
        assert reviewed["state"] == "done" and reviewed["floors"][0]["recommendation"] == "needs_engineer"
        assert sum(1 for c in changes if (c.get("check") or {}).get("verdict") == "check") == 1
        assert {r.task for r in fake.requests} == {AG.COORDINATION_TASK, AG.REVIEW_TASK}
        assert all(r.model == settings.prep_model for r in fake.requests)
        assert [x["stage"] for x in agents] == ["coordination", "review"] and row.calls == 2
        gate = PR.gate(changes, stats, reviewed, None)
        assert gate["state"] == "needs_engineer" and any("check" in r for r in gate["reasons"])
    finally:
        ai_provider.set_provider(None)


# --- the Devices job itself: POST .../plan/jobs, the job runner, app.redesign.service.plan -----------------------


def _reviewed_drawing(client, db_session, tmp_path, ep):
    """A project with a reviewed FA drawing: one plan sheet tied to the drawing
    (1 pt = 0.1 m), a 20 x 10 m store on it, and the review's changes accepted
    -- a smoke detector to add in the store, a speaker to add beside it."""
    from app.models import ProjectDrawingReview, ProjectIfcDrawing
    from app.review import geometry as G
    from tests.conftest import login

    settings = get_settings()
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": ep, "project_name": "Prep", "design_sheets": []}).json()["id"]
    plot = pymupdf.open()
    plot.new_page(width=2000, height=2000)
    pdf = str(tmp_path / "plot.pdf")
    plot.save(pdf)
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA.dwg", stored_path="x.dxf", revision="R0", meta={}, groups=[])
    db_session.add(drawing)
    db_session.commit()
    box = [0, 850, 400, 1050]                             # model x 0..40, y -5..15: the store and the corridor

    def frac(x, y):                                      # a model point as a fraction of the window
        px, py = x / 0.1, (100 - y) / 0.1
        return (px - box[0]) / (box[2] - box[0]), (py - box[1]) / (box[3] - box[1])

    dx, dy = frac(2.0, 2.0)
    sx, sy = frac(5.0, 8.0)
    sheet = {"index": 0, "name": "FA 101", "title": "GROUND FLOOR", "floor": "GROUND FLOOR", "kind": "plan",
             "multiplier": 1, "plan": [0, 0, 2000, 2000], "legend": None, "sheet_status": "done", "sheet_findings": [],
             "geometry": {**GEOMETRY, "v": G.FIT_VERSION},
             "windows": [{"id": "0:0:0", "box": box, "status": "done",
                          "rooms": [{"id": "0:1", "name": "STORE", "x": 50, "y": 950, "n": 1}],
                          "answers": {"1": {"room_type": "store", "checks": {
                              "detection": {"status": "absent", "seen": "", "action": "add", "device": "smoke detector",
                                            "instruction": "Add smoke detector in the store", "x": dx, "y": dy},
                              "speaker": {"status": "absent", "seen": "", "action": "add", "device": "ceiling speaker",
                                          "instruction": "Add ceiling speaker in the store", "x": sx, "y": sy}}}}}]}
    db_session.add(ProjectDrawingReview(project_id=pid, drawing_id=drawing.id, status="done", sheets=[sheet],
                                        decisions={}, pdf_path=pdf))
    db_session.commit()
    url = f"/projects/{pid}/drawing-review/{drawing.id}"
    ids = [f["id"] for f in client.get(url).json()["findings"] if f["action"] == "add"]
    assert len(ids) == 2
    assert client.post(f"{url}/decisions/bulk", json={"ids": ids, "status": "accepted"}).status_code == 200
    return pid, drawing.id


def _devices_job(client, monkeypatch, tmp_path, pid, did):
    """The Devices step as the page starts it, run inline by the job runner;
    the drawing's walls and columns as the job would have read them."""
    from app.redesign import service
    from app.review import render
    from app.routers import jobs as jobs_router

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    source = tmp_path / "FA.dxf"
    source.write_bytes(b"0\nEOF\n")
    monkeypatch.setattr(render, "source_file", lambda project, drawing: source)
    walls = _room_walls()
    columns = C.Columns({(i, j): [(9.7, 4.7, 10.3, 5.3)] for i in range(3, 7) for j in range(1, 4)})
    monkeypatch.setattr(service, "_walls", lambda *a, **k: walls)
    monkeypatch.setattr(PR, "columns", lambda *a, **k: columns)
    job = client.post(f"/projects/{pid}/redesign/{did}/plan/jobs").json()
    job = client.get(f"/jobs/{job['id']}").json()
    view = client.get(f"/projects/{pid}/redesign/{did}").json()
    return job, view, columns


def test_the_devices_job_with_the_agents_off_places_coordinates_and_covers_without_a_model(client, db_session, tmp_path,
                                                                                          monkeypatch):
    from app.ai.provider import RecordingProvider

    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", False)
    monkeypatch.setattr(settings, "prep_ai_enabled", False)
    recording = RecordingProvider()
    ai_provider.set_provider(recording)                    # any model call at all would land here
    try:
        pid, did = _reviewed_drawing(client, db_session, tmp_path, "40881")
        job, view, columns = _devices_job(client, monkeypatch, tmp_path, pid, did)
        assert job["status"] == "succeeded", job.get("error")
        assert recording.calls == 0 and not view["agents_on"]
        run = view["run"]
        assert run["ai"] is False and run["placement"]["by"] == "platform" and run["placement"]["placed"] == 2
        assert run["review"]["state"] == "off" and run["gate"]["state"] == "needs_engineer"
        mine = [c for c in view["changes"] if c.get("source") != "interface"]
        detectors = [c for c in mine if c["system"] == "detection"]
        assert len(detectors) >= 3                                   # the review's one, and what the store needs
        assert all(c["coverage"]["ok"] for c in detectors)           # the store covered at 6.3 m
        for c in mine:
            x, y = R._model(GEOMETRY, *c["insert"]["page"])
            assert columns.hit((x - 0.2, y - 0.2, x + 0.2, y + 0.2), 0.0) is None
        # the engineer's word, then the job again (a retry): kept as they left it, nothing doubled
        added = next(c for c in detectors if c.get("source") == PR.COVERAGE)
        speaker = next(c for c in mine if c["system"] == "speaker")
        base = f"/projects/{pid}/redesign/{did}/changes"
        assert client.patch(f"{base}/{added['id']}", json={"status": "approved"}).status_code == 200
        assert client.patch(f"{base}/{speaker['id']}", json={"status": "skipped"}).status_code == 200
        first = client.get(f"/projects/{pid}/redesign/{did}").json()["changes"]
        job, again, _ = _devices_job(client, monkeypatch, tmp_path, pid, did)
        assert job["status"] == "succeeded", job.get("error")
        by_id = {c["id"]: c for c in again["changes"]}
        assert len(by_id) == len(again["changes"])                    # no change twice
        assert by_id[added["id"]]["status"] == "approved" and by_id[speaker["id"]]["status"] == "skipped"
        assert by_id[added["id"]]["insert"] == next(c for c in first if c["id"] == added["id"])["insert"]
        # the detectors not settled yet are placed afresh around the approved one: never more, never on top of it
        now = [c for c in again["changes"] if c["system"] == "detection"]
        assert len(now) <= len([c for c in first if c["system"] == "detection"])
        points = [R._model(GEOMETRY, *c["insert"]["page"]) for c in now]
        assert all(math.dist(p, q) > 1.0 for i, p in enumerate(points) for q in points[i + 1:])
        assert all(c["coverage"]["ok"] for c in now) and recording.calls == 0
    finally:
        ai_provider.set_provider(None)


class FakePrepOpus(FakeOpus):
    """Placement as well: each change put where the review put it."""

    def complete(self, request):
        from app.redesign import ai as A

        if request.task == A.TASK:
            self.requests.append(request)
            return AiResponse(data={"candidate": 0, "symbol": 0, "x": 0.5, "y": 0.5, "facing": "none",
                                    "confidence": "high", "note": "where the review put it"},
                              usage=Usage(input_tokens=500, output_tokens=40), model=request.model, latency_ms=1)
        return super().complete(request)


def test_the_devices_job_with_the_agents_on_runs_them_on_the_preparation_route(client, db_session, tmp_path, monkeypatch):
    from app.redesign import ai as A

    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", False)              # the rest of the platform: off
    monkeypatch.setattr(settings, "prep_ai_enabled", True)
    ai_provider.set_provider(None)
    fake = FakePrepOpus()
    monkeypatch.setattr(ai_provider, "_prep_provider", fake)
    try:
        assert isinstance(ai_provider.get_provider(), ai_provider.NullProvider)
        assert ai_provider.get_prep_provider() is fake
        pid, did = _reviewed_drawing(client, db_session, tmp_path, "40882")
        job, view, _columns = _devices_job(client, monkeypatch, tmp_path, pid, did)
        assert job["status"] == "succeeded", job.get("error")
        tasks = [r.task for r in fake.requests]
        assert tasks.count(A.TASK) == 2 and AG.COORDINATION_TASK in tasks and AG.REVIEW_TASK in tasks
        assert all(r.model == settings.prep_model for r in fake.requests)
        run = view["run"]
        assert run["ai"] and run["placement"]["calls"] == 2 and run["coordination"]["agent_rooms"] >= 1
        assert run["review"]["state"] == "done"
        assert {a["stage"] for a in run["agents"]} == {"placement", "coordination", "review"}
        assert any((c.get("check") or {}).get("verdict") == "check" for c in view["changes"])
    finally:
        ai_provider.set_provider(None)


def test_a_devices_job_after_the_review_lost_its_answers_keeps_every_change_and_the_engineers_word(
        client, db_session, tmp_path, monkeypatch):
    """EP-30880, 6 October 2026: the review run again without its model kept
    every look "done" with no answer, so no finding was accepted any more; the
    Devices job after it dropped the 187 changes with their approvals and skips."""
    from app.ai.provider import RecordingProvider
    from app.models import ProjectDrawingReview

    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", False)
    monkeypatch.setattr(settings, "prep_ai_enabled", False)
    ai_provider.set_provider(RecordingProvider())
    try:
        pid, did = _reviewed_drawing(client, db_session, tmp_path, "40883")
        job, view, _ = _devices_job(client, monkeypatch, tmp_path, pid, did)
        assert job["status"] == "succeeded", job.get("error")
        review_changes = [c for c in view["changes"] if c.get("source") is None]
        approved, skipped = review_changes[0], review_changes[1]
        base = f"/projects/{pid}/redesign/{did}/changes"
        client.patch(f"{base}/{approved['id']}", json={"status": "approved"})
        client.patch(f"{base}/{skipped['id']}", json={"status": "skipped"})
        # the review emptied as the model-less run left it
        row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
        sheets = json.loads(json.dumps(row.sheets))
        for w in sheets[0]["windows"]:
            w.update(answers={}, other=[], model="null")
        row.sheets = sheets
        db_session.commit()
        assert not [f for f in client.get(f"/projects/{pid}/drawing-review/{did}").json()["findings"] if f["action"] == "add"]
        job, again, _ = _devices_job(client, monkeypatch, tmp_path, pid, did)
        assert job["status"] == "succeeded", job.get("error")
        by_id = {c["id"]: c for c in again["changes"]}
        assert {c["id"] for c in review_changes} <= set(by_id)
        assert by_id[approved["id"]]["status"] == "approved" and by_id[skipped["id"]]["status"] == "skipped"
        assert by_id[approved["id"]]["insert"] == approved["insert"]
        assert len(by_id) == len(again["changes"])
    finally:
        ai_provider.set_provider(None)
