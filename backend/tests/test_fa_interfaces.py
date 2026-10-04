"""The Fire Alarm Interface Schedule (BOQ > FA Interfaces, app.interfaces):
the other trades' equipment read off their IFC drawings, given the
interface matrix's signals floor by floor, with what the drawings do not
settle left for the engineer."""
from __future__ import annotations

import io
from pathlib import Path

import ezdxf
import openpyxl

from app.core.config import get_settings
from app.interfaces import detect
from app.interfaces.matrix import BY_KEY, RULES, modules
from app.models import RoleEnum
from tests.conftest import login, make_user

settings = get_settings()


# --- the matrix and the words -----------------------------------------------------------------


def test_the_matrix_keeps_the_sheets_contacts_and_reads_its_modules_off_them():
    assert modules("CT2") == {"CT1": 0, "CT2": 1, "CR": 0}
    assert modules("2 NOS CT2") == {"CT1": 0, "CT2": 2, "CR": 0}
    assert modules("CT2,CT1") == {"CT1": 1, "CT2": 1, "CR": 0}
    assert modules("CT2,CR") == {"CT1": 0, "CT2": 1, "CR": 1}
    assert modules("2NO.CR FOR EACH LIFT") == {"CT1": 0, "CT2": 0, "CR": 2}
    zcv, lift, gas = BY_KEY["zone_control_valve"], BY_KEY["lift_system"], BY_KEY["gas_control_panel"]
    assert (zcv.contacts, zcv.monitoring, zcv.control) == ("CT2", 2, 0)
    assert (lift.monitoring, lift.control, lift.per_lift) == (0, 2, True)
    assert (gas.monitoring, gas.control, gas.action) == (2, 1, "To Close Solenoid Valve")
    # CO2, kitchen hood, PA/BGM, BMS and escalators are never scheduled
    assert {r.key for r in RULES if r.excluded} == {"co2_system", "kitchen_hood", "public_address", "bms", "escalator"}
    # the illegible rows are not made up
    assert {r.no for r in RULES}.isdisjoint({36, 38})


def _keys(text: str, wanted=None) -> list[tuple]:
    wanted = wanted or set(BY_KEY)
    return [(d.key, d.tag, d.confidence, d.kind) for d in detect.detect(text, wanted)]


def test_tags_and_names_are_read_and_nothing_is_read_into_them():
    assert _keys("PEF-B4-01") == [("parking_extract_fan", "PEF-B4-01", "high", "label")]
    assert _keys("FAHU-L3-01 FRESH AIR HANDLING UNIT") == [("fahu", "FAHU-L3-01", "high", "label")]
    assert _keys("AHU 02") == [("ahu", "AHU 02", "high", "label")]
    assert detect.tag_key("AHU 02") == detect.tag_key("AHU-02") == "AHU02"
    assert _keys("JF-B1-01, JF-B1-02") == [("jet_fan", "JF-B1-01", "high", "label"), ("jet_fan", "JF-B1-02", "high", "label")]
    assert _keys("%%C150 ZCV") == [("zone_control_valve", None, "medium", "label")]
    assert detect.detect("Ø150 ZCV", set(BY_KEY))[0].detail == "Ø150"
    assert _keys("MOTORIZED SMOKE FIRE DAMPER") == [("motorized_smoke_fire_damper", None, "medium", "label")]
    # a note says a system protects a room -- evidence, with the room it names
    note = detect.detect("LV ROOM IS PROTECTED BY FM200 SYSTEM", set(BY_KEY))
    assert [(d.key, d.kind, d.detail) for d in note] == [("fm200_system", "note", "Lv Room")]
    # one text, several pumps
    assert [k for k, *_ in _keys("THREE PUMPS : DIESEL PUMP, ELECTRIC PUMP AND JOCKEY PUMP")] == [
        "electric_fire_pump", "diesel_fire_pump", "jockey_pump"]
    # not equipment: an extinguisher, a detail title, the fire alarm's own module notes, a spec note
    assert _keys("10 LBS CO2 FIRE EXTINGUISHER") == []
    assert _keys("ALARM CHECK VALVE DETAIL") == []
    assert _keys("CONTROL MODULE FOR GATE BARRIER") == []
    assert _keys("1. ALL ZCV SHALL BE SUPERVISED") == []
    # a door is interfaced only when the words say so
    assert _keys("AUTOMATIC SLIDING DOOR") == [("sliding_door", None, "medium", "label")]
    assert _keys("SLIDING DOOR") == [("sliding_door", None, "low", "label")]
    assert _keys("DOOR") == [] and _keys("EF-01") == []
    # a quantity is not a tag
    assert _keys("ZCV 2 NOS") == [("zone_control_valve", None, "medium", "label")]
    assert _keys("ZCV 2") == [("zone_control_valve", "ZCV 2", "high", "label")]
    # only the discipline's rows are read
    assert _keys("AHU-01", {"zone_control_valve"}) == []


def test_lift_labels_are_lifts_and_rooms_named_for_lifts_are_not():
    assert detect.lift_label("LIFT 1") == "LIFT 1"
    assert detect.lift_label("LIFT-A") == "LIFT A"
    assert detect.lift_label("FIRE LIFT") == "FIRE LIFT"
    assert detect.lift_label("PASSENGER ELEVATOR 3") == "PASSENGER LIFT 3"
    assert detect.lift_label("LIFT LOBBY") is None and detect.lift_label("LIFT PIT") is None
    assert detect.is_machine_room("LIFT MACHINE ROOM") and not detect.is_machine_room("PUMP ROOM")


# --- the schedule from a project's drawings -------------------------------------------------------


def _sheet(doc, name: str, title: str, at: tuple[float, float]):
    """A paper-space sheet whose viewport shows model space around `at`, titled `title`."""
    lay = doc.layouts.new(name)
    lay.add_viewport(center=(200, 150), size=(400, 300), view_center_point=at, view_height=30_000)
    lay.add_text(title, height=5).set_placement((10, 10))


def _smoke_management(path: Path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    # Revit-style tags: an attribute on a tag block, and a tag nested two blocks deep
    tag = doc.blocks.new("FAN TAG")
    tag.add_attdef("TAG", (0, 0), dxfattribs={"height": 200})
    for i, x in enumerate((0, 5000, 10000), 1):
        msp.add_blockref("FAN TAG", (x, 0)).add_auto_attribs({"TAG": f"PEF-B1-0{i}"})
    inner = doc.blocks.new("JF LABEL")
    inner.add_text("JF-B1-01", height=200)
    outer = doc.blocks.new("JF GROUP")
    outer.add_blockref("JF LABEL", (0, 0))
    msp.add_blockref("JF GROUP", (2000, 3000))
    msp.add_text("SPF-01", height=200).set_placement((100_000, 0))                # on the roof plan
    msp.add_text("MOTORIZED SMOKE DAMPER", height=200).set_placement((200_000, 0))  # on a typical plan
    msp.add_text("SEF-R-01", height=200).set_placement((300_000, 0))              # on the riser only
    _sheet(doc, "SM-101", "1ST BASEMENT FLOOR PLAN SMOKE MANAGEMENT LAYOUT", (5000, 0))
    _sheet(doc, "SM-117", "ROOF FLOOR PLAN SMOKE MANAGEMENT LAYOUT", (100_000, 0))
    _sheet(doc, "SM-111", "TYPICAL 3RD TO 5TH FLOOR PLAN SMOKE MANAGEMENT LAYOUT", (200_000, 0))
    _sheet(doc, "SM-120", "SMOKE MANAGEMENT SCHEMATIC DIAGRAM", (300_000, 0))
    doc.saveas(path)


def _fire_fighting(path: Path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    msp.add_text("Ø150 ZCV", height=200).set_placement((0, 0))
    msp.add_text("ZCV", height=200).set_placement((200, 0))       # the same valve labelled twice, side by side
    msp.add_text("Ø150 ZCV", height=200).set_placement((100_000, 0))
    msp.add_text("THIS ROOM IS PROTECTED BY PRE-ACTION SYSTEM", height=200).set_placement((100_000, 5000))
    msp.add_text("ELECTRIC PUMP", height=200).set_placement((300_000, 0))
    msp.add_text("DIESEL PUMP", height=200).set_placement((300_000, 2000))
    msp.add_text("10 LBS CO2 FIRE EXTINGUISHER", height=200).set_placement((0, 5000))
    _sheet(doc, "FF-101", "1ST BASEMENT FLOOR PLAN FIRE FIGHTING LAYOUT", (0, 0))
    _sheet(doc, "FF-111", "TYPICAL 3RD TO 5TH FLOOR PLAN FIRE FIGHTING LAYOUT", (100_000, 0))
    _sheet(doc, "FF-119", "SCHEMATIC RISER DIAGRAM FIRE FIGHTING LAYOUT", (300_000, 0))
    doc.saveas(path)


def _ventilation(path: Path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    msp.add_text("AHU-01", height=200).set_placement((0, 0))
    msp.add_text("FAHU-01", height=200).set_placement((5000, 0))
    msp.add_text("EF-01", height=200).set_placement((8000, 0))   # an exhaust fan the matrix has no row for
    doc.saveas(path)                                             # model space only: the floor is in the file name


def _project(client, tmp_path: Path) -> tuple[int, Path]:
    root = tmp_path / "EP-40900 Tower"
    root.mkdir()
    pid = client.post("/projects", json={"ep_number": "40900", "project_name": "Tower", "design_sheets": [],
                                         "source_folder_path": str(root)}).json()["id"]
    ifc = root / "03- Drawings" / "IFC"
    for sub in ("Mechanical/SM", "Mechanical/FF", "Mechanical/HVAC"):
        (ifc / sub).mkdir(parents=True, exist_ok=True)
    _smoke_management(ifc / "Mechanical/SM" / "SM LAYOUT.dxf")
    _fire_fighting(ifc / "Mechanical/FF" / "FF LAYOUT R1.dxf")
    (ifc / "Mechanical/FF" / "FF LAYOUT R0.dxf").write_bytes((ifc / "Mechanical/FF" / "FF LAYOUT R1.dxf").read_bytes())
    _ventilation(ifc / "Mechanical/HVAC" / "GROUND FLOOR VENTILATION LAYOUT.dxf")
    return pid, root


def test_the_schedule_is_read_floor_by_floor_from_each_disciplines_drawings(client, monkeypatch, tmp_path):
    import app.routers.jobs as jobs_router

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid, _root = _project(client, tmp_path)

    before = client.get(f"/projects/{pid}/fa-interfaces").json()
    assert before["rows"] == [] and before["scanned_at"] is None
    # received when filed, before any reading: as the folder holds it
    sm = {c["discipline"]: c for c in before["coverage"]}["SM"]
    assert (sm["status"], sm["read"]) == ("available", False)
    assert [f["status"] for f in sm["files"]] == ["unread"]
    assert {c["discipline"]: c["status"] for c in before["coverage"]}["ACS"] == "missing"

    started = client.post(f"/projects/{pid}/fa-interfaces/scan/jobs")
    assert started.status_code == 202, started.text
    job = client.get(f"/jobs/{started.json()['id']}").json()
    assert job["status"] == "succeeded", job
    view = client.get(f"/projects/{pid}/fa-interfaces").json()

    coverage = {c["discipline"]: c for c in view["coverage"]}
    assert coverage["SM"]["status"] == coverage["FF"]["status"] == coverage["HVAC"]["status"] == "available"
    assert coverage["SM"]["read"] and coverage["FF"]["read"] and coverage["HVAC"]["read"]
    assert coverage["ACS"]["status"] == "missing" and coverage["ARCH"]["status"] == "missing"
    # the earlier revision in the folder is listed, not read
    assert {f["filename"]: f["status"] for f in coverage["FF"]["files"]} == {"FF LAYOUT R0.dxf": "superseded",
                                                                            "FF LAYOUT R1.dxf": "read"}

    lines = [(r["floor_key"], r["key"], r["tag"]) for r in view["rows"]]
    # tags from attributes and from nested blocks, each once
    assert ("B1", "parking_extract_fan", "PEF-B1-01") in lines and ("B1", "parking_extract_fan", "PEF-B1-03") in lines
    assert ("B1", "jet_fan", "JF-B1-01") in lines
    assert ("RF", "staircase_pressurization_fan", "SPF-01") in lines
    # A damper text label without a completed visual symbol location is held.
    # Its text insertion point is not accepted as the physical equipment position.
    assert [f for f, k, _ in lines if k == "motorized_smoke_fire_damper"] == []
    assert sorted(f for f, k, _ in lines if k == "zone_control_valve") == ["B1", "L3", "L4", "L5"]
    # a model-space-only drawing: its floor from the file name; EF-01 has no matrix row
    assert ("GF", "ahu", "AHU-01") in lines and ("GF", "fahu", "FAHU-01") in lines
    assert not any("EF-01" in t for *_, t in lines)
    # every line carries the matrix and its source
    ahu = next(r for r in view["rows"] if r["key"] == "ahu")
    assert (ahu["contacts"], ahu["monitoring"], ahu["control"], ahu["action"]) == ("CR", 0, 1, "To Shut Down AHU")
    assert ahu["system"] == "Ventilation / HVAC" and ahu["source"] == "GROUND FLOOR VENTILATION LAYOUT.dxf"
    zcv = next(r for r in view["rows"] if r["key"] == "zone_control_valve")
    assert zcv["tag"] == "Tag Not Identified" and zcv["confidence"] == "Medium" and zcv["modules"]["CT2"] == 1
    assert zcv["drawing_ref"].startswith("FF-101") and zcv["location"] == ""
    # in building order, basement first
    order = [r["floor_key"] for r in view["rows"]]
    assert order.index("B1") < order.index("GF") < order.index("L3") < order.index("RF")

    # Verification Required: the riser-only fans and pumps, and the pre-action system shown by a note
    open_items = {(g["key"], tuple(g["proposed_floor_keys"])): g for g in view["verification"]}
    assert ("smoke_exhaust_fan", ()) in open_items and open_items[("smoke_exhaust_fan", ())]["tags"] == ["SEF-R-01"]
    assert ("electric_fire_pump", ()) in open_items and ("diesel_fire_pump", ()) in open_items
    pre = open_items[("preaction_system", ("L3", "L4", "L5"))]
    assert pre["proposed_qty"] == 1
    assert not any(r["key"] in ("preaction_system", "electric_fire_pump", "smoke_exhaust_fan") for r in view["rows"])
    assert view["excluded_found"] == []           # an extinguisher is not a CO2 system

    # totals are the lines' own sums
    t = view["totals"]
    assert t["items"] == len(view["rows"])
    assert t["monitoring"] == sum(r["monitoring"] for r in view["rows"])
    assert t["control"] == sum(r["control"] for r in view["rows"])
    assert sum(f["total"] for f in view["floor_summary"]) == t["interface_points"]
    assert sum(s["qty"] for s in view["type_summary"]) == t["items"]

    # The engineer settles the pump: one, in the pump room on B1.
    pump = open_items[("electric_fire_pump", ())]
    assert client.post(f"/projects/{pid}/fa-interfaces/decisions",
                       json={"id": pump["id"], "action": "resolve", "qty": 1}).status_code == 422   # no floor
    after = client.post(f"/projects/{pid}/fa-interfaces/decisions",
                        json={"id": pump["id"], "action": "resolve", "floor_keys": ["B1"], "qty": 1,
                              "location": "Pump Room"}).json()
    line = next(r for r in after["rows"] if r["key"] == "electric_fire_pump")
    assert (line["floor_key"], line["confidence"], line["location"], line["monitoring"]) == ("B1", "Engineer verified", "Pump Room", 2)
    assert pump["id"] not in {g["id"] for g in after["verification"]}
    # ... says the diesel pump is not in this building, and takes a damper line out
    assert client.post(f"/projects/{pid}/fa-interfaces/decisions",
                       json={"id": open_items[("diesel_fire_pump", ())]["id"], "action": "dismiss"}).status_code == 422
    after = client.post(f"/projects/{pid}/fa-interfaces/decisions",
                        json={"id": open_items[("diesel_fire_pump", ())]["id"], "action": "dismiss",
                              "reason": "Electric pumps only"}).json()
    # The engineer first resolves the held labels to equipment; only then can a row be rejected.
    damper_check = next(g for g in after["verification"] if g["key"] == "motorized_smoke_fire_damper")
    after = client.post(f"/projects/{pid}/fa-interfaces/decisions",
                        json={"id": damper_check["id"], "action": "resolve",
                              "floor_keys": ["L3", "L4", "L5"], "qty": 1}).json()
    assert [r["floor_key"] for r in after["rows"] if r["key"] == "motorized_smoke_fire_damper"] == ["L3", "L4", "L5"]
    # ... and adds a gas control panel the drawings do not show, with where it was seen
    assert client.post(f"/projects/{pid}/fa-interfaces/manual",
                       json={"key": "gas_control_panel", "floor_keys": ["GF"], "source": " "}).status_code == 422
    after = client.post(f"/projects/{pid}/fa-interfaces/manual",
                        json={"key": "gas_control_panel", "floor_keys": ["GF"], "qty": 1, "tags": ["GCP-01"],
                              "source": "LPG LAYOUT.pdf", "location": "FCC"}).json()
    gas = next(r for r in after["rows"] if r["key"] == "gas_control_panel")
    assert (gas["tag"], gas["monitoring"], gas["control"], gas["basis"]) == ("GCP-01", 2, 1, "manual")

    # The answers survive a read of the drawings again.
    client.post(f"/projects/{pid}/fa-interfaces/scan/jobs")
    again = client.get(f"/projects/{pid}/fa-interfaces").json()
    assert [r["id"] for r in again["rows"]] == [r["id"] for r in after["rows"]]
    assert len(again.get("rejected", [])) == 0

    # The workbook: floor-wise, its totals the schedule's.
    xlsx = client.get(f"/projects/{pid}/fa-interfaces/export.xlsx")
    assert xlsx.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(xlsx.content))
    assert wb.sheetnames == ["A. Drawing Coverage", "B. Building Floors", "C. Interface Schedule", "D. Floor Summary",
                             "E. Equipment Summary", "F. Totals", "G. Verification Required", "H. Conflicts & Missing",
                             "Interface Matrix"]
    ws = wb["C. Interface Schedule"]
    header = [c.value for c in ws[4]]
    assert header[:4] == ["S.No", "Floor", "Location", "Equipment Tag"] and "Source Drawing" in header
    lines = [r for r in ws.iter_rows(min_row=5, values_only=True) if isinstance(r[0], int)]
    assert len(lines) == again["totals"]["items"]
    mon = header.index("Monitoring Signals")
    assert sum(r[mon] for r in lines) == again["totals"]["monitoring"]
    total = next(r for r in ws.iter_rows(min_row=5, values_only=True) if r[1] == "BUILDING TOTAL")
    assert total[mon] == again["totals"]["monitoring"]
    coverage_rows = list(wb["A. Drawing Coverage"].iter_rows(min_row=5, values_only=True))
    assert any(r[0] == "Access Control" and r[1] == "Missing" for r in coverage_rows)
    assert any(r[3] == "SM LAYOUT.dxf" for r in coverage_rows)
    # ... and as a document to issue
    pdf = client.get(f"/projects/{pid}/fa-interfaces/export.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_a_viewer_reads_the_schedule_but_does_not_answer(client, db_session, tmp_path):
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid, _root = _project(client, tmp_path)
    make_user(db_session, "viewer@example.com", RoleEnum.viewer)
    client.post("/auth/logout")
    assert login(client, "viewer@example.com", "Password123!").status_code == 200
    assert client.get(f"/projects/{pid}/fa-interfaces").status_code == 200
    assert client.post(f"/projects/{pid}/fa-interfaces/scan/jobs").status_code == 403
    assert client.post(f"/projects/{pid}/fa-interfaces/decisions", json={"id": "x", "action": "reject"}).status_code == 403


# --- the mechanical equipment schedules -------------------------------------------------------------


def test_schedule_tags_are_read_as_written_and_runs_expanded():
    from app.interfaces import schedules as SCH

    assert SCH.expand("B3-SEF-1 TO 4") == ["B3-SEF-1", "B3-SEF-2", "B3-SEF-3", "B3-SEF-4"]
    assert SCH.expand("CHILLER- 01 TO 04") == ["CHILLER-01", "CHILLER-02", "CHILLER-03", "CHILLER-04"]
    assert SCH.expand("SPF-1A") == ["SPF-1A"]
    assert SCH.base_tag("B3-SEF-1") == ("B3", "SEF-1") and SCH.base_tag("FAHU-01") == (None, "FAHU-01")
    assert SCH.same_tag("FAHU-01", "FAHU-1") and not SCH.same_tag("FAHU-01", "FAHU-11")


def test_the_plans_are_checked_against_the_equipment_schedule(client, monkeypatch, tmp_path):
    import app.routers.jobs as jobs_router
    from openpyxl import Workbook

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    root = tmp_path / "EP-40901 Mall"
    pid = client.post("/projects", json={"ep_number": "40901", "project_name": "Mall", "design_sheets": [],
                                         "source_folder_path": str(root)}).json()["id"]
    hvac = root / "03- Drawings" / "IFC" / "Mechanical" / "HVAC"
    hvac.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    for x in (0, 100_000):                       # the same tag on each basement's plan
        msp.add_text("SEF-1", height=200).set_placement((x, 0))
    msp.add_text("FAHU-1", height=200).set_placement((200_000, 0))
    msp.add_text("SEF-9", height=200).set_placement((200_000, 3000))   # not in the fan schedule
    _sheet(doc, "V-101", "2ND BASEMENT FLOOR PLAN VENTILATION LAYOUT", (0, 0))
    _sheet(doc, "V-102", "1ST BASEMENT FLOOR PLAN VENTILATION LAYOUT", (100_000, 0))
    _sheet(doc, "V-117", "ROOF FLOOR PLAN VENTILATION LAYOUT", (200_000, 0))
    doc.saveas(hvac / "VENTILATION LAYOUT.dxf")
    folder = root / "03- Drawings" / "IFC" / "Mechanical" / "MECHANICAL SCHEDULE"
    folder.mkdir(parents=True)
    wb = Workbook()
    ws = wb.active
    ws.append(["SMOKE MANAGEMENT / VENTILATION FANS"])
    ws.append(["SN", "FAN TAG", "FAN LOCATION", "QTY (No.'s)", "REMARKS"])
    ws.append([1, "B2-SEF-1", "BASEMENT-2", 1, "400°C/2HR"])
    ws.append([2, "B1-SEF-1", "BASEMENT-1", 1, "400°C/2HR"])
    ws.append([3, "CSEF-1 TO 2", "ROOF FLOOR", 2, "400°C/2HR"])
    ws.append([4, "GEF-1", "ROOF FLOOR", 1, "General exhaust"])                # no matrix row
    wb.save(folder / "Schedule of Fans.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.append(["SR. NO.", "FAHU REF", "MODEL NAME"])
    ws.append([1, "FAHU-01", "TAH-190"])
    wb.save(folder / "Schedule of FAHU.xlsx")

    client.post(f"/projects/{pid}/fa-interfaces/scan/jobs")
    view = client.get(f"/projects/{pid}/fa-interfaces").json()

    lines = {(r["floor_key"], r["tag"]): r for r in view["rows"]}
    # SEF-1 on each basement is that basement's fan, as the schedule names it
    assert {("B2", "B2-SEF-1"), ("B1", "B1-SEF-1"), ("RF", "FAHU-1"), ("RF", "SEF-9")} <= set(lines)
    assert "Schedule of Fans.xlsx" in lines[("B1", "B1-SEF-1")]["evidence"]
    assert "Schedule of FAHU.xlsx" in lines[("RF", "FAHU-1")]["evidence"]
    # in the schedule, on no plan: asked about, with its floor and quantity proposed -- not scheduled
    csef = next(g for g in view["verification"] if g["system"] == "Equipment Schedule")
    assert (csef["key"], csef["proposed_floor_keys"], csef["proposed_qty"], csef["tags"]) == (
        "smoke_exhaust_fan", ["RF"], 2, ["CSEF-1", "CSEF-2"])
    assert not any(r["tag"].startswith("CSEF") for r in view["rows"])
    # on the plans, not in the schedule: said
    assert any("not in the equipment schedules: SEF-9" in c for c in view["conflicts"])
    sched = next(c for c in view["coverage"] if c["discipline"] == "SCHED")
    assert sched["status"] == "available" and {f["filename"] for f in sched["files"]} == {"Schedule of Fans.xlsx",
                                                                                          "Schedule of FAHU.xlsx"}


def test_one_piece_of_equipment_on_several_drawings_is_counted_once(client, monkeypatch, tmp_path):
    import app.routers.jobs as jobs_router

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    root = tmp_path / "EP-40902 Hotel"
    pid = client.post("/projects", json={"ep_number": "40902", "project_name": "Hotel", "design_sheets": [],
                                         "source_folder_path": str(root)}).json()["id"]
    mech = root / "03- Drawings" / "IFC" / "Mechanical"
    for sub in ("HVAC", "SM"):
        (mech / sub).mkdir(parents=True, exist_ok=True)
    # Ventilation: FAHU-01 with its name written beside it, and SEF-1 tagged
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    msp.add_text("FAHU-01", height=200).set_placement((0, 0))
    msp.add_text("FRESH AIR HANDLING UNIT", height=200).set_placement((0, -250))
    msp.add_text("SEF-1", height=200).set_placement((5000, 0))
    _sheet(doc, "V-104", "GROUND FLOOR PLAN VENTILATION LAYOUT", (0, 0))
    doc.saveas(mech / "HVAC" / "VENTILATION.dxf")
    # Smoke management: the same FAHU as "FAHU-1", the same fan named but not tagged
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    msp.add_text("FAHU-1", height=200).set_placement((0, 0))
    msp.add_text("SMOKE EXHAUST FAN", height=200).set_placement((5000, 0))
    _sheet(doc, "SM-104", "GROUND FLOOR PLAN SMOKE MANAGEMENT LAYOUT", (0, 0))
    doc.saveas(mech / "SM" / "SMOKE.dxf")

    client.post(f"/projects/{pid}/fa-interfaces/scan/jobs")
    view = client.get(f"/projects/{pid}/fa-interfaces").json()
    gf = [(r["key"], r["tag"]) for r in view["rows"] if r["floor_key"] == "GF"]
    assert sorted(gf) == [("fahu", "FAHU-01"), ("smoke_exhaust_fan", "SEF-1")]
    assert any("names it without a tag" in c for c in view["conflicts"])
    # an added line with a tag a drawing already places is the same item
    after = client.post(f"/projects/{pid}/fa-interfaces/manual",
                        json={"key": "fahu", "floor_keys": ["GF"], "tags": ["FAHU-1"], "source": "FAHU schedule"}).json()
    assert [r["tag"] for r in after["rows"] if r["key"] == "fahu"] == ["FAHU-01"]
    assert any("FAHU-1 is given twice" in c for c in after["conflicts"])


def test_a_fire_pump_room_drawn_but_not_named_gets_the_schematics_pumps_where_it_is():
    from app.interfaces import detect
    from app.interfaces import service as I

    assert detect.is_pump_room("PUMP ROOM") and detect.is_pump_room("FIRE PUMP ROOM")
    assert not detect.is_pump_room("DOMESTIC PUMP ROOM") and not detect.is_pump_room("SUMP PUMP ROOM")

    class Floors:
        def of_title(self, title):
            return ["B3"] if "3RD BASEMENT" in title else ["B2"] if "2ND BASEMENT" in title else []

    sheets = [{"name": "FF-101", "title": "3RD BASEMENT FLOOR PLAN", "kind": "plan"},
              {"name": "FF-102", "title": "2ND BASEMENT FLOOR PLAN", "kind": "plan"},
              {"name": "FF-119", "title": "SCHEMATIC RISER DIAGRAM", "kind": "diagram"}]
    result = {"units": "m", "sheets": sheets,
              "items": [{"key": "alarm_check_valve", "sheet": "FF-101", "x": 719.3, "y": 157.6},
                        {"key": "electric_fire_pump", "sheet": "FF-119", "x": 3216.0, "y": -161.0},
                        {"key": "jockey_pump", "sheet": "FF-119", "x": 3216.0, "y": -166.0},
                        {"key": "jockey_pump", "sheet": "FF-102", "x": 10.0, "y": 10.0},
                        {"key": "alarm_check_valve", "sheet": "FF-102", "x": 11.0, "y": 10.0}],
              "pump_rooms": [{"text": "PUMP ROOM", "sheet": "FF-101", "x": 717.17, "y": 158.69},
                             {"text": "PUMP ROOM", "sheet": "FF-102", "x": 12.0, "y": 10.0}]}
    pumps = I._pump_room_pumps(result, Floors())
    # B3: drawn, named only on the schematic -- the schematic's pumps, in the room; B2 names its own: none added
    assert [(key, keys, sheet) for key, keys, _it, sheet, _ref in pumps] == [
        ("electric_fire_pump", ["B3"], "FF-101"), ("jockey_pump", ["B3"], "FF-101")]
    it = pumps[0][2]
    assert (it["x"], it["y"], it["detail"], it["confidence"]) == (717.17, 158.69, "Pump Room", "medium")


def test_a_damper_label_is_scheduled_as_the_drawing_shows_it_once_looked_at():
    from app.interfaces import service as I
    from app.interfaces import visual

    class Floors:
        def of_title(self, title):
            return ["B3"] if "3RD BASEMENT" in title else []

        def note(self, key, where):
            pass

        def name(self, key):
            return key

    def label(text, x, y):
        return {"key": "motorized_smoke_fire_damper", "kind": "label", "confidence": "medium", "tag": None,
                "detail": "", "text": text, "sheet": "M-07-V101", "x": x, "y": y}

    door, msd_1, msd_2 = label("SD", 712.85, 159.05), label("MSD", 719.25, 154.4), label("MSD", 720.07, 154.66)
    src = {"discipline": "HVAC", "relative_path": "HVAC/VENTILATION LAYOUT.dwg", "filename": "VENTILATION LAYOUT.dwg",
           "sha256": "abc", "status": "read",
           "result": {"units": "m", "sheets": [{"name": "M-07-V101", "title": "3RD BASEMENT FLOOR PLAN VENTILATION LAYOUT",
                                                "kind": "plan", "height": 97.0}],
                      "items": [door, msd_1, msd_2]},
           "visual": {"version": visual.VERSION, "sha256": "abc", "items": {
               visual.item_id(door): {"damper": False, "at": None, "what": "door tag SD 04"},
               visual.item_id(msd_1): {"damper": True, "at": [719.6, 154.1]},
               visual.item_id(msd_2): {"damper": True, "at": [720.2, 154.1]}}}}
    floors = Floors()
    equipment, groups, conflicts = [], [], []
    I._read_source(src, floors, equipment, groups, conflicts, [], {}, I.Schedule([], floors))
    rows = I._equipment_rows(equipment, floors, conflicts, I.Schedule([], floors))
    dampers = [r for r in rows if not r.get("visual_reject")]
    # the two MSDs a metre apart: two dampers, each where its damper is drawn
    assert sorted(r["anchor"] for r in dampers) == [[719.6, 154.1], [720.2, 154.1]]
    assert all("seen on the drawing" in r["evidence"] for r in dampers)
    # the door tag: set aside, saying what it is
    (door_row,) = [r for r in rows if r.get("visual_reject")]
    assert door_row["visual_reject"] == "door tag SD 04"


def test_damper_without_visual_result_is_held_and_text_is_not_equipment_location():
    from app.interfaces import service as I

    class Floors:
        def of_title(self, title): return ["B3"]
        def note(self, key, where): pass
        def name(self, key): return key

    def label(x, y):
        return {"key": "motorized_smoke_fire_damper", "kind": "label", "confidence": "medium",
                "tag": None, "detail": "", "text": "MSD", "sheet": "M-07-V101", "x": x, "y": y}

    src = {"discipline": "HVAC", "relative_path": "HVAC/VENTILATION LAYOUT.dwg",
           "filename": "VENTILATION LAYOUT.dwg", "sha256": "abc", "status": "read",
           "result": {"units": "m", "sheets": [{"name": "M-07-V101", "title": "3RD BASEMENT",
                      "kind": "plan", "height": 97.0}], "items": [label(719.25,154.4), label(720.07,154.66)]}}
    equipment, groups, conflicts = [], [], []
    floors = Floors()
    I._read_source(src, floors, equipment, groups, conflicts, [], {}, I.Schedule([], floors))
    assert equipment == []
    assert len(groups) == 1
    assert groups[0]["proposed_qty"] is None
    assert groups[0]["labels"] == 2
    assert "text position is not an equipment position" in groups[0]["reason"]


def test_visual_damper_keeps_label_and_physical_equipment_anchors_separate():
    from app.interfaces import service as I
    from app.interfaces import visual

    class Floors:
        def of_title(self, title): return ["B3"]
        def note(self, key, where): pass
        def name(self, key): return key
        def order(self, key): return (0, key)

    it = {"key": "motorized_smoke_fire_damper", "kind": "label", "confidence": "medium", "tag": None,
          "detail": "", "text": "MSD", "sheet": "M-07-V101", "x": 719.25, "y": 154.4}
    src = {"discipline": "HVAC", "relative_path": "HVAC/VENTILATION LAYOUT.dwg",
           "filename": "VENTILATION LAYOUT.dwg", "sha256": "abc", "status": "read",
           "result": {"units": "m", "sheets": [{"name": "M-07-V101", "title": "3RD BASEMENT",
                      "kind": "plan", "height": 97.0}], "items": [it]},
           "visual": {"version": visual.VERSION, "sha256": "abc", "status": "complete",
                      "items": {visual.item_id(it): {"damper": True, "at": [721.1, 153.8]}}}}
    equipment, groups, conflicts = [], [], []
    floors = Floors()
    I._read_source(src, floors, equipment, groups, conflicts, [], {}, I.Schedule([], floors))
    rows = I._equipment_rows(equipment, floors, conflicts, I.Schedule([], floors))
    assert rows[0]["anchor"] == [721.1, 153.8]
    assert rows[0]["equipment_anchor"] == [721.1, 153.8]
    assert rows[0]["label_anchor"] == [719.25, 154.4]
