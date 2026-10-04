"""The reported FA Interfaces cases (FI-P1 r2 CASES.md), reproduced on synthetic
drawings that carry EP-30880's geometry:

1. two smoke-damper drawings: both are accounted for (an aligned union, not the
   drawing with the most labels per floor);
2. equipment located at its drawn symbol, apart from its label; unclear held;
3. a gate barrier drawing with separate ENTRY and EXIT barriers: two CR
   interfaces from the drawing's own fire alarm connection points -- not one,
   not a hard-coded two, and not one per repeated label.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import ezdxf
import pytest

from app.core.config import get_settings
from app.interfaces import geometry, scan, service
from app.models import Project
from tests.conftest import login

settings = get_settings()


def _sheet(doc, name: str, title: str, centre: tuple[float, float], height: float = 97.0):
    lay = doc.layouts.new(name)
    lay.add_viewport(center=(420, 297), size=(800, 560), view_center_point=centre, view_height=height)
    lay.add_text(title, height=5).set_placement((10, 10))


LANDMARK_WORDS = [("RMU ROOM", 1168.47, 166.72), ("MAIN ENTRANCE", 1147.48, 170.49), ("FIRE EXIT", 1194.81, 161.03),
                  ("DROP OFF", 1156.86, 174.99), ("LANDSCAPING AREA", 1150.33, 176.71), ("CONOPY ABOVE", 1153.04, 171.02)]


def _gate_layout(path: Path, *, lanes="ep30880", shift=(0.0, 0.0)) -> Path:
    """EP-30880's GB layout, ground floor: two lanes, each with a dry-contact fire alarm
    note, two leaders, a safety loop; role labels PARKING ENTRY / ENT. / EXIT."""
    dx, dy = shift
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for text, x, y in LANDMARK_WORDS:                                   # the architect's background, shared
        msp.add_text(text, height=0.2).set_placement((x, y))

    def note(text, x, y, tails):
        msp.add_text(text, height=0.12).set_placement((x + dx, y + dy))
        for tx, ty in tails:
            msp.add_leader([(x + dx + 0.4, y + dy + 0.14), (tx + dx, ty + dy)])

    if lanes == "ep30880":
        note("DRY CONTACT BY THIRD PARTY (2 Core) FIRE ALARM CABLE", 1162.25, 181.70, [(1163.26, 179.28), (1163.07, 179.28)])
        note("DRY CONTACT BY THIRD PARTY (2 Core) FIRE ALARM CABLE", 1164.55, 177.04, [(1163.54, 178.69), (1163.73, 178.69)])
        # the same note drawn twice over itself: one point
        msp.add_text("DRY CONTACT BY THIRD PARTY (2 Core) FIRE ALARM CABLE", height=0.12).set_placement((1164.6 + dx, 177.1 + dy))
        for text, x, y in (("PARKING ENTRY", 1159.30, 180.74), ("PARKING ENT.", 1159.65, 178.70),
                           ("PARKING EXIT.", 1165.06, 178.28), ("SAFETY LOOP", 1165.80, 179.06),
                           ("SAFETY LOOP", 1159.99, 179.02), ("PRESIDENTIAL LOOP FOR EXIT", 1169.89, 176.18),
                           ("GATE BARRIER", 1165.69, 178.70), ("GATE BARRIER NETWORK", 1171.9, 152.0)):
            msp.add_text(text, height=0.12).set_placement((x + dx, y + dy))
        for x0 in (1159.68, 1165.48):
            msp.add_lwpolyline([(x0 + dx, 178.9 + dy), (x0 + 1.8 + dx, 178.9 + dy), (x0 + 1.8 + dx, 179.6 + dy),
                                (x0 + dx, 179.6 + dy)], close=True, dxfattribs={"layer": "CPMS LOOP"})
    elif lanes == "three":
        for i, (role, x) in enumerate((("ENTRY", 1150.0), ("ENTRY", 1160.0), ("EXIT", 1170.0))):
            note("FIRE ALARM CABLE", x, 180.0, [(x + 1.0, 178.0)])
            msp.add_text(f"LANE {i + 1} {role}", height=0.12).set_placement((x - 1.5 + dx, 182.0 + dy))
    elif lanes == "both_near":
        note("FIRE ALARM CABLE", 1162.0, 180.0, [(1163.0, 178.0)])
        msp.add_text("ENTRY", height=0.12).set_placement((1160.0 + dx, 180.0 + dy))
        msp.add_text("EXIT", height=0.12).set_placement((1164.2 + dx, 180.0 + dy))
    # traps: a detail sheet's typical lane, and library blocks outside every viewport
    msp.add_text("FIRE ALARM CABLE", height=0.12).set_placement((1300.0, 60.0))
    msp.add_text("ENTRY", height=0.12).set_placement((1298.0, 61.0))
    lib = doc.blocks.new("ENTRY A")
    lib.add_lwpolyline([(0, 0), (3, 0), (3, 0.2), (0, 0.2)], close=True)
    msp.add_blockref("ENTRY A", (800.0, -235.0))
    _sheet(doc, "gf", "GROUND FLOOR PLAN GATEBARRIER SYSTEM LAYOUT", (1182.99, 142.21), 96.95)
    _sheet(doc, "det", "TYPICAL DETAILS GATEBARRIER SYSTEM", (1300.0, 60.0), 20.0)
    doc.saveas(path)
    return path


def _metre_read(path: Path, discipline="GB") -> dict:
    return scan.read(str(path), discipline)


# --- case 3: gate barriers ------------------------------------------------------------------------------------


def test_case3_the_entry_and_exit_barriers_are_two_settled_connection_points(tmp_path):
    result = _metre_read(_gate_layout(tmp_path / "gb.dxf"))
    points = [it for it in result["items"] if it["kind"] == "instance" and it["sheet"] == "gf"]
    assert sorted((p["role"], p["settled"]) for p in points) == [("entry", True), ("exit", True)]
    assert all(p["margin"] >= 5.0 for p in points)                       # 4.44 m vs 9.60 m swapped: 5.16 m
    entry = next(p for p in points if p["role"] == "entry")
    assert entry["equipment_anchor"] == pytest.approx([1163.165, 179.28], abs=0.01)   # where its leaders point
    # the repeated note is one point; the detail sheet's and the library blocks are not barriers on a plan
    assert len([it for it in result["items"] if it["kind"] == "instance"]) == 3
    assert next(it for it in result["items"] if it["kind"] == "instance" and it["sheet"] != "gf")["sheet"] == "det"


def test_case3_no_hard_coded_two_three_lanes_give_three_and_a_lone_point_near_both_roles_is_held(tmp_path):
    three = [it for it in _metre_read(_gate_layout(tmp_path / "g3.dxf", lanes="three"))["items"]
             if it["kind"] == "instance" and it["sheet"] == "gf"]
    assert sorted(p["role"] for p in three) == ["entry", "entry", "exit"] and all(p["settled"] for p in three)
    lone = [it for it in _metre_read(_gate_layout(tmp_path / "g1.dxf", lanes="both_near"))["items"]
            if it["kind"] == "instance" and it["sheet"] == "gf"]
    assert len(lone) == 1 and lone[0]["settled"] is False and "both an entry and an exit" in lone[0]["why"]


@pytest.fixture
def gb(client, db_session, tmp_path):
    login(client, settings.default_admin_email, settings.default_admin_password)
    root = tmp_path / "EP-30880 Titania"
    folder = root / "03- Drawings" / "IFC" / "Electrical" / "GB"
    folder.mkdir(parents=True)
    pid = client.post("/projects", json={"ep_number": "30880", "project_name": "Titania", "design_sheets": [],
                                         "source_folder_path": str(root)}).json()["id"]
    return SimpleNamespace(client=client, db=db_session, pid=pid, folder=folder)


def _read(gb) -> dict:
    gb.db.expire_all()
    service.scan_project(gb.db, gb.db.get(Project, gb.pid))
    return gb.client.get(f"/projects/{gb.pid}/fa-interfaces").json()


def test_case3_the_schedule_has_two_CR_lines_entry_closes_exit_opens(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    view = _read(gb)
    gates = [r for r in view["rows"] if r["key"] == "gate_barrier"]
    assert sorted(r["role"] for r in gates) == ["entry", "exit"]
    assert all(r["contacts"] == "CR" and r["control"] == 1 for r in gates)
    assert {r["role"]: r["action"] for r in gates} == {
        "exit": "To open the exit gate barrier", "entry": "To close the entrance gate barrier (additional control module)"}
    assert all(r["location_state"] == "leader" and r["anchor"] != r["label_anchor"] for r in gates)
    assert view["totals"]["control"] >= 2
    # the words "GATE BARRIER" / "... NETWORK" are context, not a third barrier
    assert not any(g["key"] == "gate_barrier" for g in view["verification"])


def test_case3_a_second_drawing_showing_other_barriers_holds_the_floor_until_the_engineer_chooses(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    # the shop drawing: the same frame (shared landmarks) but its barriers elsewhere, and more of them
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for text, x, y in LANDMARK_WORDS:
        msp.add_text(text, height=0.2).set_placement((x, y))
    for x, y in ((1190.57, 175.95), (1195.76, 175.76), (1174.72, 162.55), (1172.33, 166.59)):
        msp.add_text("FIRE ALARM CABLE", height=0.12).set_placement((x, y))
    _sheet(doc, "BGF", "GROUND FLOOR PLAN GATEBARRIER SYSTEM LAYOUT", (1182.99, 142.21), 96.95)
    doc.saveas(gb.folder / "Shop Drawings-Titania rev01.dxf")
    view = _read(gb)
    assert not [r for r in view["rows"] if r["key"] == "gate_barrier"]      # held: no credit while they disagree
    (conflict,) = [g for g in view["verification"] if g["id"].startswith("GATE|")]
    assert {d["points"] for d in conflict["drawings"]} == {2, 4}
    layout = next(d["relative_path"] for d in conflict["drawings"] if d["points"] == 2)
    assert gb.client.post(f"/projects/{gb.pid}/fa-interfaces/decisions",
                          json={"id": conflict["id"], "action": "govern", "relative_path": layout}).status_code == 422
    after = gb.client.post(f"/projects/{gb.pid}/fa-interfaces/decisions",
                           json={"id": conflict["id"], "action": "govern", "relative_path": layout,
                                 "reason": "The IFC layout is the issued design"}).json()
    assert sorted(r["role"] for r in after["rows"] if r["key"] == "gate_barrier") == ["entry", "exit"]
    assert any("the engineer's choice" in c for c in after["conflicts"])


def test_case3_the_same_barriers_on_two_aligned_drawings_count_once(gb):
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT.dxf")
    _gate_layout(gb.folder / "GATEBARRIER SYSTEM LAYOUT COPY.dxf")
    view = _read(gb)
    assert sorted(r["role"] for r in view["rows"] if r["key"] == "gate_barrier") == ["entry", "exit"]
    assert any("the drawings agree" in c for c in view["conflicts"])


# --- case 2: located at the symbol ---------------------------------------------------------------------------


def test_case2_two_adjacent_msd_labels_are_tied_to_their_own_symbols(tmp_path):
    """EP-30880 3rd basement: MSD labels 0.86 m apart; their damper symbols 1.10 m apart."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    blk = doc.blocks.new("A$C0e331ec6")
    blk.add_lwpolyline([(-0.02, -0.12), (0.02, -0.12), (0.02, 0.12), (-0.02, 0.12)], close=True)
    msp = doc.modelspace()
    msp.add_blockref("A$C0e331ec6", (719.448, 154.226))
    msp.add_blockref("A$C0e331ec6", (720.532, 154.724))
    msp.add_text("MSD", height=0.12).set_placement((719.25, 154.40))
    msp.add_text("MSD", height=0.12).set_placement((720.07, 154.66))
    tag = doc.blocks.new("TAG-DOOR")                          # a door tag block: carries text, never a symbol
    tag.add_attdef("T", (0, 0))
    msp.add_blockref("TAG-DOOR", (712.85, 159.05)).add_auto_attribs({"T": "SD"})
    _sheet(doc, "M-07-V101", "3RD BASEMENT FLOOR PLAN VENTILATION LAYOUT", (733.0, 135.3), 97.0)
    doc.saveas(tmp_path / "v.dxf")
    result = scan.read(str(tmp_path / "v.dxf"), "HVAC")
    msd = sorted((it for it in result["items"] if it["text"] == "MSD"), key=lambda it: it["x"])
    assert [it["association"]["state"] for it in msd] == ["settled", "settled"]
    assert [it["association"]["symbol"]["centre"] for it in msd] == [
        pytest.approx([719.448, 154.226], abs=0.001), pytest.approx([720.532, 154.724], abs=0.001)]
    assert msd[0]["association"]["symbol"]["id"] != msd[1]["association"]["symbol"]["id"]
    sd = next(it for it in result["items"] if it["text"] == "SD")
    assert sd["association"]["state"] != "settled" or sd["association"]["symbol"]["block"] != "TAG-DOOR"


# --- case 1: two smoke-damper drawings -----------------------------------------------------------------------


def _union_entries(aligned: bool):
    from app.interfaces import service as I

    shared = {f"ROOM {i}": [700.0 + i, 150.0] for i in range(5)}
    other = shared if aligned else {k: [v[0] + 30.0, v[1]] for k, v in shared.items()}
    sm = {"discipline": "SM", "relative_path": "SM/SMOKE.dwg", "result": {"units": "m", "landmarks": shared}}
    hv = {"discipline": "HVAC", "relative_path": "HVAC/VENT.dwg", "result": {"units": "m", "landmarks": other}}

    def e(src, x, y, label):
        return {"key": "motorized_smoke_fire_damper", "tag": None, "keys": ["B3"], "src": src, "label": label,
                "ref": "B3", "sheet": "S", "detail": "", "text": "MSD", "confidence": "high", "anchor": (x, y),
                "count": 1, "visual": True, "label_anchor": [x, y], "equipment_anchor": [x + 0.2, y - 0.2],
                "location_state": "symbol", "radius": 0.97}
    # SM: one damper both drawings show, and one only SM shows; HVAC: the shared one and two of its own
    return [e(sm, 701.8, 154.4, "SMOKE.dwg"), e(sm, 760.0, 150.0, "SMOKE.dwg"),
            e(hv, 701.9, 154.4, "VENT.dwg"), e(hv, 719.25, 154.4, "VENT.dwg"), e(hv, 720.07, 154.66, "VENT.dwg")], I


def _floors():
    class Floors:
        def name(self, k): return k
        def order(self, k): return (0, k)
    return Floors()


def test_case1_both_damper_drawings_count_their_union_once_when_their_frames_align():
    entries, I = _union_entries(aligned=True)
    held: list = []
    rows = I._equipment_rows(entries, _floors(), conflicts := [], I.Schedule([], _floors()), held)
    assert len(rows) == 4 and held == []                      # 1 shared + 1 SM-only + 2 HVAC-only, not max(2, 3)
    assert any("union" in c for c in conflicts)
    assert any("also drawn on VENT.dwg" in r["evidence"] for r in rows)


def test_case1_drawings_not_verified_in_one_frame_are_held_not_one_drawings_count():
    entries, I = _union_entries(aligned=False)
    held: list = []
    rows = I._equipment_rows(entries, _floors(), [], I.Schedule([], _floors()), held)
    assert rows == [] and len(held) == 1
    assert held[0]["counts"] == {"SMOKE.dwg": 2, "VENT.dwg": 3}
    (group,) = I._conflict_groups(held, _floors())
    assert group["proposed_qty"] is None and group["conflict"] is True


def test_landmarks_decide_alignment_not_viewports():
    a = {"MAIN ENTRANCE": [1147.48, 170.49], "FIRE EXIT": [1194.81, 161.03], "RMU ROOM": [1168.47, 166.72]}
    assert geometry.aligned(a, dict(a), 1.0)["aligned"]
    assert not geometry.aligned(a, {k: [v[0] + 30, v[1]] for k, v in a.items()}, 1.0)["aligned"]
    assert not geometry.aligned(a, {"MAIN ENTRANCE": a["MAIN ENTRANCE"]}, 1.0)["aligned"]   # one match is not proof
