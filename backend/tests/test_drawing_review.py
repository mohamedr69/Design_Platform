"""Drawings Review (app.review): the FA IFC drawing plotted, its named rooms
looked at by the model, the answers checked and kept, the engineer's word
on each finding."""
from __future__ import annotations

import io

import openpyxl
import pymupdf

from app.ai.provider import RecordingProvider, set_provider
from app.core.config import get_settings
from app.review import ai as A
from app.review import pages as P
from tests.conftest import login

settings = get_settings()


def _plan_pdf(path):
    """An A1 sheet: two rooms named on the plan, a legend and a title in the panel."""
    doc = pymupdf.open()
    page = doc.new_page(width=2384, height=1684)
    page.insert_text((400, 500), "LOBBY", fontsize=10)
    page.insert_text((900, 500), "ELECTRICAL", fontsize=10)
    page.insert_text((900, 512), "ROOM", fontsize=10)
    page.insert_text((400, 520), "+0.30 FFL", fontsize=6)        # a level: not a room
    page.insert_text((700, 800), "LIFT 3", fontsize=8)            # a lift car: not a room
    page.insert_text((2100, 300), "LEGENDS", fontsize=9)
    page.insert_text((2100, 1500), "GROUND FLOOR PLAN", fontsize=12)
    doc.save(path)
    return path


def test_rooms_are_read_off_the_plotted_plan(tmp_path):
    doc = pymupdf.open(_plan_pdf(tmp_path / "s.pdf"))
    info = P.read(doc, 0)
    assert [r.name for r in info.rooms] == ["LOBBY", "ELECTRICAL ROOM"]       # two lines, one name
    assert info.legend is not None and info.plan[2] < 2100
    assert len(P.windows(info)) >= 1


def test_the_models_answer_is_kept_only_where_it_is_well_formed():
    def c(system, status, action="none", device="", x=-1, y=-1):
        return {"system": system, "status": status, "seen": "", "action": action, "device": device,
                "instruction": "", "x": x, "y": y}
    data = {"rooms": [{"n": 1, "room_type": "pump room", "checks": [
        c("detection", "wrong", "add", "heat detector (H)", 0.5, 0.5),     # a wrong device is replaced, not added
        c("speaker", "absent", "none", "sounder-flasher"),                 # an absent device is added
        c("emergency_light", "present", "add"),                            # a present one needs nothing
        c("nonsense", "present")]},
        {"n": 9, "room_type": "made up", "checks": []}], "other": []}
    rooms, _other = A.read_window_answer(data, {1, 2})
    assert set(rooms) == {1}                                   # room 9 was never asked about
    checks = rooms[1].checks
    assert (checks["detection"]["action"], checks["speaker"]["action"], checks["emergency_light"]["action"]) == (
        "replace", "add", "none")
    assert checks["fire_telephone"]["status"] == "unclear"     # said nothing: unclear, not assumed
    assert checks["speaker"]["x"] == -1 and checks["detection"]["x"] == 0.5


def test_a_drawing_is_reviewed_and_each_finding_is_the_engineers_to_settle(client, db_session, monkeypatch, tmp_path):
    import app.routers.jobs as jobs_router
    from app.models import ProjectIfcDrawing
    from app.review import render, service

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    pdf = _plan_pdf(tmp_path / "sheets.pdf")
    monkeypatch.setattr(render, "render", lambda project, drawing: (pdf, "a" * 64))
    monkeypatch.setattr(service.storage, "relative", lambda path: str(path))
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40950", "project_name": "Tower", "design_sheets": []}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA LAYOUT.dwg", stored_path="x.dxf", revision="R0",
                                meta={"sheets": [{"name": "FA-104", "title": "GROUND FLOOR PLAN", "kind": "plan"}]},
                                groups=[])
    db_session.add(drawing)
    db_session.commit()

    overview = client.get(f"/projects/{pid}/drawing-review").json()
    assert overview["drawings"][0]["pages"] == [{"page": 0, "sheet": "FA-104", "title": "GROUND FLOOR PLAN",
                                                 "floor": "GROUND FLOOR"}]
    assert {r["system"] for r in overview["rules"]} == set(A.SYSTEMS)

    def c(system, status, action="none", device="", instruction="", x=-1, y=-1):
        return {"system": system, "status": status, "seen": "", "action": action, "device": device,
                "instruction": instruction, "x": x, "y": y}
    window = {"rooms": [
        {"n": 1, "room_type": "entrance lobby", "checks": [
            c(s, "present") for s in ("detection", "speaker", "emergency_light")]},
        {"n": 2, "room_type": "electrical room", "checks": [
            c("detection", "present"),
            c("speaker", "wrong", "remove", "ceiling speaker (CS)", "Remove CS: no speaker in electrical rooms", 0.4, 0.4),
            c("emergency_light", "absent", "add", "emergency light (E)", "Add E by the door")]}],
        "other": [{"image": 1, "system": "exit_sign", "where": "main entrance", "issue": "No exit sign over the doors",
                   "action": "add", "device": "exit sign", "instruction": "Add exit sign over the doors", "x": 0.2,
                   "y": 0.3}]}
    sheet = {"findings": [{"system": "manual_call_point", "where": "STAIR-1 door", "issue": "No MCP at the stair door",
                           "severity": "high", "action": "add", "device": "manual call point",
                           "instruction": "Add MCP at STAIR-1 door", "x": 0.1, "y": 0.1}]}
    provider = RecordingProvider([window, sheet])
    set_provider(provider)
    try:
        started = client.post(f"/projects/{pid}/drawing-review/{drawing.id}/jobs", json={"pages": None})
        assert started.status_code == 202, started.text
        job = client.get(f"/jobs/{started.json()['id']}").json()
        assert job["status"] == "succeeded", job
    finally:
        set_provider(None)
    # the review asked Opus 5.5 by name
    assert {r.model for r in provider.requests} == {settings.drawing_review_model}

    review = client.get(f"/projects/{pid}/drawing-review/{drawing.id}").json()
    assert review["status"] == "done" and review["counts"]["rooms"] == 2 and review["counts"]["reviewed"] == 2
    found = {(f["room"], f["system"], f["action"]) for f in review["findings"]}
    assert ("ELECTRICAL ROOM", "emergency_light", "add") in found
    assert ("ELECTRICAL ROOM", "speaker", "remove") in found
    assert ("ELECTRICAL ROOM", "fire_telephone", "none") in found       # not answered: unclear, to check by eye
    assert ("main entrance", "exit_sign", "add") in found
    assert ("STAIR-1 door", "manual_call_point", "add") in found
    assert not any(f["room"] == "LOBBY" and f["system"] == "detection" for f in review["findings"])
    assert review["counts"]["add"] == 3 and review["counts"]["remove"] == 1
    speaker = next(f for f in review["findings"] if f["system"] == "speaker" and f["action"] == "remove")
    assert speaker["instruction"] == "Remove CS: no speaker in electrical rooms" and speaker["at"] is not None

    # nothing for the draftsman until the engineer accepts it
    url = f"/projects/{pid}/drawing-review/{drawing.id}"
    assert client.get(f"{url}/markup.pdf").status_code == 409

    light = next(f for f in review["findings"] if f["system"] == "emergency_light")
    url = f"/projects/{pid}/drawing-review/{drawing.id}/decisions"
    assert client.post(url, json={"id": light["id"], "status": "dismissed"}).status_code == 422   # say why
    after = client.post(url, json={"id": light["id"], "status": "accepted",
                                   "instruction": "Add E above the electrical room door"}).json()
    assert after["counts"]["accepted"] == 1
    assert next(f for f in after["findings"] if f["id"] == light["id"])["instruction"] == "Add E above the electrical room door"
    many = client.post(f"{url}/bulk", json={"ids": [f["id"] for f in after["findings"]], "status": "accepted"}).json()
    assert many["counts"]["accepted"] == 4 and many["counts"]["open"] == 0      # the unclear one is not a change
    markup = client.get(f"/projects/{pid}/drawing-review/{drawing.id}/markup.pdf")
    assert markup.status_code == 200
    marked = pymupdf.open(stream=markup.content, filetype="pdf")
    assert marked.page_count == 1                                      # the schedule, no whole plans
    text = marked[0].get_text()
    assert "Add E above the electrical room door" in text and "REMOVE" in text and "LOCATION" in text
    # each change with its piece of the plot beside it, drawn from the plot itself
    assert len(marked[0].get_xobjects()) >= 1

    png = client.get(f"/projects/{pid}/drawing-review/{drawing.id}/image",
                     params={"page": 0, "box": ",".join(map(str, light["box"])), "mark": ",".join(map(str, light["mark"]))})
    assert png.status_code == 200 and png.content.startswith(b"\x89PNG")
    xlsx = client.get(f"/projects/{pid}/drawing-review/{drawing.id}/export.xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(xlsx.content))
    assert wb.sheetnames == ["Findings", "Rooms"]

    # the engineer's decisions became rulings: the next review asks again, with them ...
    provider2 = RecordingProvider([window, sheet])
    set_provider(provider2)
    try:
        client.post(f"/projects/{pid}/drawing-review/{drawing.id}/jobs", json={"pages": None})
    finally:
        set_provider(None)
    assert provider2.calls == 2 and "ENGINEERS' RULINGS" in provider2.requests[0].system
    # ... and one after it, with nothing new, asks nothing
    provider3 = RecordingProvider([])
    set_provider(provider3)
    try:
        client.post(f"/projects/{pid}/drawing-review/{drawing.id}/jobs", json={"pages": None})
    finally:
        set_provider(None)
    assert provider3.calls == 0
    assert client.get(f"/projects/{pid}/drawing-review/{drawing.id}").json()["counts"]["accepted"] == 4


def test_stair_detection_is_wanted_about_every_five_floors_not_on_each():
    from app.review.service import _spacing

    def sheet(index, floor, multiplier=1):
        return {"index": index, "floor": floor, "name": f"FA-{index}", "plan": [0, 0, 100, 100], "multiplier": multiplier}

    def room():
        return {"name": "STAIR-1", "mark": [10, 10]}
    # B3 has one, then GF..L2 (4 floors) none: fine; then a typical sheet for 14 floors with none: one ADD
    spaced = [(sheet(0, "3RD BASEMENT"), room(), True), (sheet(1, "GROUND FLOOR"), room(), False),
              (sheet(2, "1ST PODIUM"), room(), False), (sheet(3, "1ST FLOOR"), room(), False),
              (sheet(4, "2ND FLOOR"), room(), False), (sheet(5, "MECHANICAL FLOOR"), room(), True),
              (sheet(6, "TYPICAL 3RD TO 16TH FLOOR", 14), room(), False)]
    out = _spacing(spaced)
    assert len(out) == 1 and out[0]["action"] == "add" and out[0]["page"] == 6
    assert "none for 14 floors" in out[0]["instruction"]


def test_the_engineers_rulings_settle_the_same_change_elsewhere_and_go_to_the_model(client, db_session):
    from app.models import ProjectDrawingReview, ProjectIfcDrawing
    from app.review import rulings as R

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40951", "project_name": "Tower", "design_sheets": []}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA.dwg", stored_path="x.dxf", revision="R0", meta={}, groups=[])
    db_session.add(drawing)
    db_session.commit()

    def sheet(index, floor):
        speaker = {"status": "wrong", "seen": "CS", "action": "remove", "device": "ceiling speaker (CS)",
                   "instruction": "Remove CS", "x": 0.5, "y": 0.5}
        return {"index": index, "name": f"FA-{index}", "title": floor, "floor": floor, "kind": "plan", "multiplier": 1,
                "plan": [0, 0, 1000, 800], "legend": None, "sheet_status": "done", "sheet_findings": [],
                "windows": [{"id": f"{index}:0:0", "box": [0, 0, 400, 400], "status": "done",
                             "rooms": [{"id": f"{index}:1", "name": "ELECTRICAL ROOM", "x": 100, "y": 100, "n": 1}],
                             "answers": {"1": {"room_type": "electrical room", "checks": {"speaker": speaker}}}}]}
    db_session.add(ProjectDrawingReview(project_id=pid, drawing_id=drawing.id, status="done", sheets=[
        sheet(0, "GROUND FLOOR"), sheet(1, "1ST FLOOR")], decisions={}))
    db_session.commit()

    url = f"/projects/{pid}/drawing-review/{drawing.id}"
    review = client.get(url).json()
    first, second = [f for f in review["findings"] if f["system"] == "speaker"]
    assert first["decision"] == second["decision"] == "open"
    _text, before = R.prompt(db_session)

    after = client.post(f"{url}/decisions", json={"id": first["id"], "status": "dismissed",
                                                  "note": "Electrical rooms have no speakers"}).json()
    one, two = [f for f in after["findings"] if f["system"] == "speaker"]
    assert one["decision"] == "dismissed" and not one["by_ruling"]
    # the same comment on the other floor goes with it
    assert two["decision"] == "dismissed" and "As on GROUND FLOOR: Electrical rooms have no speakers" in two["note"]
    assert after["applied"] == {"count": 1, "floors": ["1ST FLOOR"]}
    assert [r["decision"] for r in after["rulings"]] == ["dismissed"]
    db_session.expire_all()
    text, version = R.prompt(db_session)
    assert "NOT NEEDED: REMOVE ceiling speaker (CS) in ELECTRICAL ROOM" in text and version != before

    # the other floor reopened: open, whatever the ruling
    reopened = client.post(f"{url}/decisions", json={"id": second["id"], "status": "open"}).json()
    assert next(f for f in reopened["findings"] if f["id"] == second["id"])["decision"] == "open"
    # the first reopened: its ruling goes
    cleared = client.post(f"{url}/decisions", json={"id": first["id"], "status": "open"}).json()
    assert cleared["rulings"] == []


def test_the_ifc_signs_are_checked_against_the_fls_drawing_of_the_same_floor(client, db_session, monkeypatch, tmp_path):
    import app.routers.jobs as jobs_router
    from app.models import ProjectIfcDrawing
    from app.review import render, service

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    pdf = _plan_pdf(tmp_path / "sheets.pdf")
    real_render_file = render.render_file
    monkeypatch.setattr(render, "render", lambda project, drawing: (pdf, "b" * 64))
    monkeypatch.setattr(service.storage, "relative", lambda path: str(path))
    root = tmp_path / "EP-40952 Tower"
    fls_folder = root / "03- Drawings" / "IFC" / "FLS"
    fls_folder.mkdir(parents=True)
    fls = pymupdf.open()
    page = fls.new_page(width=2384, height=1684)
    page.insert_text((300, 400), "EXIT", fontsize=10)
    page.insert_text((2000, 1500), "GROUND FLOOR FLS PLAN", fontsize=12)
    fls.save(fls_folder / "FLS-GF.pdf")
    assert real_render_file is render.render_file          # a PDF is read as it is, nothing plotted

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40952", "project_name": "Tower", "design_sheets": [],
                                         "source_folder_path": str(root)}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA.dwg", stored_path="x.dxf", revision="R0",
                                meta={"sheets": [{"name": "FA-104", "title": "GROUND FLOOR PLAN", "kind": "plan"}]},
                                groups=[])
    db_session.add(drawing)
    db_session.commit()

    window = {"rooms": [], "other": []}
    sheet = {"findings": []}
    against = {"findings": [{"system": "exit_sign", "where": "STAIR-1 door", "issue": "FLS exit with no exit sign",
                             "severity": "high", "action": "add", "device": "exit sign",
                             "instruction": "Add exit sign above STAIR-1 door, as the FLS", "x": 0.2, "y": 0.3}]}
    provider = RecordingProvider([window, sheet, against])
    set_provider(provider)
    try:
        assert client.post(f"/projects/{pid}/drawing-review/{drawing.id}/jobs", json={}).status_code == 202
    finally:
        set_provider(None)
    fls_call = provider.requests[-1]
    assert fls_call.task == "fa_drawing_review_fls" and "FLS" in fls_call.system
    assert [p.label for p in fls_call.parts if p.label.startswith("image")] == ["image 1: FLS plan", "image 2: IFC plan"]

    review = client.get(f"/projects/{pid}/drawing-review/{drawing.id}").json()
    assert review["fls"]["files"] == ["FLS-GF.pdf"] and review["fls"]["floors_matched"] == 1
    assert review["floors"][0]["fls"]["file"] == "FLS-GF.pdf"
    found = next(f for f in review["findings"] if f["kind"] == "fls")
    assert (found["action"], found["system"], found["instruction"]) == ("add", "exit_sign",
                                                                         "Add exit sign above STAIR-1 door, as the FLS")


# --- the driveway's sounder-flashers: only where the nearest is over 12 m ------


def test_the_plot_is_tied_to_the_drawing_by_the_texts_both_carry():
    import pymupdf

    from app.review import geometry as G

    doc = pymupdf.open()
    page = doc.new_page(width=1190, height=842)
    names = ["PUMP ROOM", "DRIVEWAY NORTH", "STAIR 01", "LIFT LOBBY", "ELECTRICAL ROOM", "STORE 12", "GENSET"]
    model = []
    for i, name in enumerate(names):
        x, y = 100 + i * 130, 120 + (i % 3) * 200
        page.insert_text((x, y), name, fontsize=8)
        line = next(l for b in page.get_text("dict")["blocks"] for l in b.get("lines", [])
                    if "".join(s["text"] for s in l["spans"]) == name)
        cx, cy = (line["bbox"][0] + line["bbox"][2]) / 2, (line["bbox"][1] + line["bbox"][3]) / 2
        model.append((name, 0.0617 * cx + 1000, -0.0617 * cy + 500))     # 1:175 on A3, page y down
    g = G.fit(page, model)
    assert g is not None and abs(g["a"] - 0.0617) < 1e-4
    assert G.nearest(g, [(1000 + 0.0617 * 300, 500 - 0.0617 * 300, "Sounder Strobe WP")], (300, 300))[0] < 0.01


def test_a_driveway_sounder_flasher_is_asked_for_only_past_12_m(monkeypatch):
    from types import SimpleNamespace

    from app.review import geometry as G
    from app.review import service

    geometry = {"v": G.FIT_VERSION, "a": 0.1, "bx": 0.0, "by": 0.0}      # 1 pt = 0.1 m
    row = SimpleNamespace(sheets=[{"index": 0, "geometry": geometry}])
    monkeypatch.setattr(G, "notifiers", lambda db, drawing: {"FA 101": [(10.0, -10.0, "Sounder Strobe WP")]})

    def finding(at, room="Driveway between parking rows", system="speaker"):
        return {"system": system, "action": "add", "room": room, "room_type": "", "instruction": "Add sounder strobe",
                "issue": "No sounder-flasher", "page": 0, "sheet": "FA 101", "at": at}

    near, far, pump = finding([150, 100]), finding([300, 100]), finding([150, 100], room="PUMP ROOM")
    service._sounder_spacing(None, None, row, [near, far, pump])
    assert near["nearest_m"] == 5.0 and "within 12 m" in near["covered"]
    assert far["nearest_m"] == 20.0 and "covered" not in far and "more than 12 m" in far["issue"]
    # a pump room's sounder-flasher is not a driveway's: not measured
    assert "nearest_m" not in pump


def test_a_decision_goes_to_the_same_comment_on_the_other_floors_and_is_undone_with_it(client, db_session):
    from app.models import ProjectDrawingReview, ProjectIfcDrawing

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40952", "project_name": "Tower", "design_sheets": []}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA.dwg", stored_path="x.dxf", revision="R0", meta={}, groups=[])
    db_session.add(drawing)
    db_session.commit()

    def sheet(index, floor, room):
        jack = {"status": "absent", "seen": "", "action": "add", "device": "fire phone jack",
                "instruction": "Add fire phone jack by the lift door", "x": 0.5, "y": 0.5}
        return {"index": index, "name": f"FA-{index}", "title": floor, "floor": floor, "kind": "plan", "multiplier": 1,
                "plan": [0, 0, 1000, 800], "legend": None, "sheet_status": "done", "sheet_findings": [],
                "windows": [{"id": f"{index}:0:0", "box": [0, 0, 400, 400], "status": "done",
                             "rooms": [{"id": f"{index}:1", "name": room, "x": 100, "y": 100, "n": 1}],
                             "answers": {"1": {"room_type": "lobby", "checks": {"fire_telephone": jack}}}}]}
    db_session.add(ProjectDrawingReview(project_id=pid, drawing_id=drawing.id, status="done", sheets=[
        sheet(0, "B3", "FIRE LIFT LOBBY 1"), sheet(1, "B2", "FIRE LIFT LOBBY 2"), sheet(2, "B1", "FIRE LIFT LOBBY"),
        sheet(3, "GF", "STAIR LOBBY")], decisions={}))
    db_session.commit()
    url = f"/projects/{pid}/drawing-review/{drawing.id}"
    jacks = [f for f in client.get(url).json()["findings"] if f["system"] == "fire_telephone"]
    b3, b2, b1, gf = jacks

    # B1 settled by hand first: it goes to B3 and B2 as well ...
    first = client.post(f"{url}/decisions", json={"id": b1["id"], "status": "dismissed", "note": "Jack is on the riser"})
    assert first.json()["applied"] == {"count": 2, "floors": ["B2", "B3"]}
    # ... until B3 is decided on its own: that goes to B2, and B1's own word is kept
    after = client.post(f"{url}/decisions", json={"id": b3["id"], "status": "accepted",
                                                  "instruction": "Add FTJ beside the fire lift door"}).json()
    by_id = {f["id"]: f for f in after["findings"]}
    assert after["applied"] == {"count": 1, "floors": ["B2"]}
    assert by_id[b2["id"]]["decision"] == "accepted"
    assert by_id[b2["id"]]["instruction"] == "Add FTJ beside the fire lift door"
    assert by_id[b1["id"]]["decision"] == "dismissed"            # not overruled
    assert by_id[gf["id"]]["decision"] == "open"                 # another room: not the same comment

    # undone on B3: what it carried to B2 goes, and B2 is back to what B1's ruling says of it
    undone = client.post(f"{url}/decisions", json={"id": b3["id"], "status": "open"}).json()
    by_id = {f["id"]: f for f in undone["findings"]}
    assert undone["applied"]["count"] == 1
    assert by_id[b3["id"]]["decision"] == "open"
    assert by_id[b2["id"]]["decision"] == "dismissed" and by_id[b2["id"]]["by_ruling"]
    assert by_id[b1["id"]]["decision"] == "dismissed" and not by_id[b1["id"]]["by_ruling"]


# --- staircase speakers on alternate floors; no emergency light in garbage / ELV / locker rooms ---


def test_staircase_speakers_go_on_alternate_floors():
    from app.review import service

    def stair(index, floor, seen, multiplier=1):
        sh = {"index": index, "name": f"FA-{index}", "floor": floor, "multiplier": multiplier,
              "plan": [0, 0, 1000, 800]}
        return sh, {"name": "STAIR-1", "mark": [100, 100]}, seen

    found = service._alternate([
        stair(0, "3RD BASEMENT", False), stair(1, "2ND BASEMENT", False), stair(2, "1ST BASEMENT", False),
        stair(3, "GROUND FLOOR", True), stair(4, "1ST FLOOR", True), stair(5, "2ND FLOOR", None),
        stair(6, "TYPICAL 3RD TO 16TH FLOOR", False, multiplier=14)])
    got = [(f["floor"], f["action"]) for f in found]
    # B3 none, B2 none: add on B2; B1 none beside B2 (corrected): fine; GF and 1st both: delete on 1st;
    # the unread 2nd breaks the run; the typical plan stands for 14 floors in a row
    assert got == [("2ND BASEMENT", "add"), ("1ST FLOOR", "remove"), ("TYPICAL 3RD TO 16TH FLOOR", "add")]
    assert "Ground Floor has one" in found[1]["instruction"] and "2nd Basement" in found[0]["instruction"]
    assert all(f["kind"] == "spacing" and f["system"] == "speaker" for f in found)


def test_an_emergency_light_in_a_garbage_room_is_to_be_deleted(client, db_session):
    from app.models import ProjectDrawingReview, ProjectIfcDrawing

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40953", "project_name": "Tower", "design_sheets": []}).json()["id"]
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA.dwg", stored_path="x.dxf", revision="R0", meta={}, groups=[])
    db_session.add(drawing)
    db_session.commit()
    light = lambda status, action: {"status": status, "seen": "E" if status == "present" else "",  # noqa: E731
                                    "action": action, "device": "emergency light", "instruction": "", "x": 0.5, "y": 0.5}
    rooms = [("GARBAGE ROOM", light("present", "none")), ("ELV ROOM", light("absent", "add")),
             ("CORRIDOR", light("absent", "add"))]
    sheet = {"index": 0, "name": "FA-0", "title": "GF", "floor": "GROUND FLOOR", "kind": "plan", "multiplier": 1,
             "plan": [0, 0, 1000, 800], "legend": None, "sheet_status": "done", "sheet_findings": [],
             "windows": [{"id": "0:0:0", "box": [0, 0, 400, 400], "status": "done",
                          "rooms": [{"id": f"0:{n}", "name": name, "x": 100, "y": 100, "n": n}
                                    for n, (name, _c) in enumerate(rooms, 1)],
                          "answers": {str(n): {"room_type": "", "checks": {"emergency_light": check}}
                                      for n, (_name, check) in enumerate(rooms, 1)}}]}
    db_session.add(ProjectDrawingReview(project_id=pid, drawing_id=drawing.id, status="done", sheets=[sheet], decisions={}))
    db_session.commit()

    found = {(f["room"], f["action"]) for f in client.get(f"/projects/{pid}/drawing-review/{drawing.id}").json()["findings"]
             if f["system"] == "emergency_light"}
    # the garbage room's light is to go; the ELV room gets none added; the corridor still gets its light
    assert found == {("GARBAGE ROOM", "remove"), ("CORRIDOR", "add")}
