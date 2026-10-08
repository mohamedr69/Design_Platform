"""M8 exit fixes (ORCH-044): the engineer's eight decisions on the wall index
(A-16, 8 October 2026), implemented literally, and the ORCH-042 conditions
U2M8V-02/03/04.

  1 title / frame / border blocks (and DIM_TEXT-class content inherited onto
    a wall layer) are neither walls nor boundaries: reason title_frame (f8)
  2 an INSERT on an off / no-plot layer hides only its layer-"0" content; a
    frozen one all of it (f3, f6: test_redesign_walls_layers.py)
  3 200 m kept; lengths in metres by $INSUNITS; unknown unit: held (u1..u4)
  4 MLINE not read: mline_unsupported in the report and the gate (f9)
  5 TAG is not a boundary
  6 the rotation term in the plot-to-model tie, the viewport passed (f12)
  7 arcs are wall candidates; meshes not read, counted (f10)
  8 the allow-list regex pinned

Fixtures: tests/fixtures_m8 (make_fixtures.py, ezdxf, no AutoCAD). No model
is called; nothing here reads the live platform."""
from __future__ import annotations

import math
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings, get_settings
from app.redesign import coverage as C
from app.redesign import layers as L
from app.redesign import prepare as PR
from app.redesign import service as R
from app.redesign import walls as W
from app.review import geometry as G

FIX = Path(__file__).resolve().parent / "fixtures_m8"
GEOMETRY = {"v": 1, "a": 0.1, "bx": 0.0, "by": 100.0, "residual": 0.4}
SHEET = {"index": 0, "name": "FA 101", "floor": "GROUND FLOOR", "plan": [0, 0, 2000, 2000], "geometry": GEOMETRY}


def _build(tmp_path, name, **kw) -> W.Walls:
    return W.build(FIX / name, tmp_path / (name + ".pkl"), detail=True, **kw)


def _cols(tmp_path, name, **kw) -> C.Columns:
    return C.build_columns(FIX / name, tmp_path / (name + ".cols.pkl"), get_settings().prep_column_layers, **kw)


def _kept(walls) -> set:
    return {r["seg"] for r in walls.detail if r["reason"] is None}


def _bounds(cols) -> set:
    return {s for segs in cols.bounds.cells.values() for s in segs} if cols.bounds is not None else set()


def _detector(cid, x, y):
    return {"id": cid, "page": 0, "sheet": "FA 101", "floor": "GROUND FLOOR", "room": "STORE", "system": "detection",
            "system_name": "Detection", "action": "add", "device": "smoke detector", "status": "proposed",
            "moved": False, "box": [0, 0, 400, 400], "candidates": [],
            "insert": {"symbol": 1, "name": "Smoke Detector", "block": "SD", "seen": [x, y], "placed": [x, y],
                       "model": [x, y], "offset": [0, 0], "radius": 0.2, "page": R._page(GEOMETRY, x, y)}}


REVIEWED_ON = {"state": "passed"}


# --- decision 1: title, frame and border ---------------------------------------------------


def test_a16_d1_the_frame_block_default_is_a_setting_beside_the_wall_allow_list():
    fields = list(Settings.model_fields)
    assert fields.index("prep_frame_blocks") == fields.index("prep_wall_layers") + 1
    assert Settings.model_fields["prep_frame_blocks"].default == r"T\.FRAM|TITLE|FRAME|BORDER|SHEET"
    assert get_settings().prep_frame_blocks == r"T\.FRAM|TITLE|FRAME|BORDER|SHEET" == L.FRAME_BLOCKS
    rule = re.compile(get_settings().prep_frame_blocks, re.I)
    for name in ("T.FRAM", "X-REF_TITLE BLOCK A1", "Frame", "A1-BORDER", "SHEET-01"):
        assert rule.search(L.local_name(name)), name
    assert L.local_name("X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM") == "T.FRAM"
    for name in ("WALLPAIR", "X-REF_ FILE ALL FLOORS PLANS", "CCSD", "TFRAM"):
        assert not rule.search(name), name


def test_a16_d1_f8_a_title_frame_inheriting_a_wall_layer_is_neither_wall_nor_boundary(tmp_path):
    walls = _build(tmp_path, "f8_title_frame.dxf")
    assert _kept(walls) == {(0.0, 10.0, 120.0, 10.0), (0.0, 10.2, 120.0, 10.2),       # the real walls
                            (10.0, 41.0, 14.0, 41.0)}                                   # DIM_TEXT's own 06-WALL line
    framed = [r for r in walls.detail if r["reason"] == "title_frame"]
    assert len(framed) == 7 and {r["layer"] for r in framed} == {"06-WALL", "A-WALL"}
    rep = walls.report
    assert rep["totals"]["included_length_m"] == 244.0 and rep["totals"]["excluded"] == {"title_frame": 7}
    assert rep["title_frame_blocks"] == {
        "BORDER-A1": {"segments": 2, "length_m": 100.0, "layers": {"A-WALL": 2}},              # explicit wall lines
        "X-REF_ DIM_TEXT": {"segments": 1, "length_m": 5.0, "layers": {"06-WALL": 1}},          # layer "0" only
        "X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM": {"segments": 4, "length_m": 420.0, "layers": {"06-WALL": 4}}}
    assert rep["rules"]["deny_blocks"] == get_settings().prep_frame_blocks
    assert rep["rules"]["annotation_blocks"] == L.ANNOTATION_BLOCKS
    # the boundary index (the one room_at prefers) by the same rule
    cols = _cols(tmp_path, "f8_title_frame.dxf")
    assert cols.report["bounds_length_m"] == 244.0 and cols.report["hidden"] == {"title_frame": 4}
    assert not any(s[1] in (0.0, 90.0, -10.0, -10.2) for s in _bounds(cols))


def test_a16_d1_the_frame_rule_is_overridable_per_build_and_in_the_index_name(tmp_path, monkeypatch):
    off = _build(tmp_path, "f8_title_frame.dxf", deny_blocks="", annotation_blocks="")
    assert off.report["totals"]["included_length_m"] == 769.0 and "title_frame" not in off.report["totals"]["excluded"]
    frame_only = _build(tmp_path, "f8_title_frame.dxf", deny_blocks=r"T\.FRAM", annotation_blocks="")
    assert frame_only.report["title_frame_blocks"].keys() == {"X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM"}
    cols = _cols(tmp_path, "f8_title_frame.dxf", deny_blocks="", annotation_blocks="")
    assert cols.report["bounds_length_m"] == 769.0
    assert W.fingerprint(deny_blocks="") != W.fingerprint() != W.fingerprint(deny_blocks=r"T\.FRAM")
    from app.ifc import storage

    monkeypatch.setattr(storage, "uploads_root", lambda: tmp_path)
    project, drawing = SimpleNamespace(ep_number=1), SimpleNamespace(id=1)
    assert W.path_for(project, drawing, "s", deny_blocks="") != W.path_for(project, drawing, "s")
    assert C.columns_path(project, drawing, "s", deny_blocks="") != C.columns_path(project, drawing, "s")


# --- decision 3: units ------------------------------------------------------------------------


@pytest.mark.parametrize("name, unit, factor", [("u1_metres.dxf", "m", 1.0), ("u2_millimetres.dxf", "mm", 0.001),
                                                ("u3_inches.dxf", "in", 0.0254)])
def test_a16_d3_lengths_are_metres_by_the_drawings_unit_before_the_threshold_and_the_report(tmp_path, name, unit,
                                                                                           factor):
    walls = _build(tmp_path, name)
    u = walls.report["units"]
    assert (u["unit"], u["factor_to_m"], u["known"], u["source"], u["lengths_in"]) == (unit, factor, True,
                                                                                       "$INSUNITS", "m")
    assert walls.report["totals"]["included_length_m"] == pytest.approx(301.6, abs=1e-3)
    assert walls.report["totals"]["excluded"]["below_min_length"] == 1          # the 0.25 m stub, in every unit
    assert walls.report["sparse"] is False and not walls.sparse and walls.held is None
    assert walls.report["rules"]["min_walls_m"] == W.MIN_WALLS_M == 200.0       # decision 3 A: kept at 200 m
    cols = _cols(tmp_path, name)
    assert len(cols) == 1 and cols.report["held"] is None and cols.bounds is not None    # a 0.4 m column
    assert cols.report["bounds_length_m"] == pytest.approx(303.45, abs=1e-3)


def test_a16_d3_a_unitless_drawing_is_held_not_measured_units_unknown_never_measured(tmp_path):
    walls = _build(tmp_path, "u4_unitless.dxf")
    u = walls.report["units"]
    assert (u["insunits"], u["known"], u["factor_to_m"], u["unit"]) == (0, False, None, None)
    assert "measurement" in u and "lunits" in u                                 # read and reported
    assert walls.report["sparse"] is None and walls.report["held"] == "units_unknown"
    assert walls.held == "units_unknown" and walls.sparse
    # the same lines are there (evidence) but offered to nothing: no room, no face, no snap (F-07 where unknown)
    assert walls.cells and walls.near(25.0, 0.0, 5.0) == []
    assert walls.face_behind(25.0, 0.1, (0.0, 1.0)) is None and not walls.thick(25.0, 0.0, (0.0, 1.0))
    assert C.room_at(walls, None, 25.0, 12.0) is None
    known = _build(tmp_path, "u1_metres.dxf")
    assert known.face_behind(25.0, 0.1, (0.0, 1.0)) is not None and C.room_at(known, None, 25.0, 12.0) is not None
    cols = _cols(tmp_path, "u4_unitless.dxf")
    assert cols.report["held"] == "units_unknown" and cols.bounds is None and len(cols) == 0
    assert cols.report["columns_found"] == 1 and C.room_at(walls, cols, 25.0, 12.0) is None
    group = PR.rooms([_detector("a", 25.0, 12.0)], {0: SHEET}, walls, cols)[0]
    assert group["room"] is None and group["index"].startswith("not measured, units unknown ($INSUNITS 0")
    plan = PR.propose(group, {0: SHEET}, [], set(), cols)
    assert plan["open"] and plan["issues"] == [f"the drawing's wall index is {group['index']}: no room can be "
                                               "closed from it, coverage not measured"]
    state = PR.index_state(walls, cols)
    assert state["walls"] == "units_unknown" and state["columns"] == "units_unknown"
    gate = PR.gate([], {"wall_index": state}, REVIEWED_ON, cols)
    assert gate["state"] == "needs_engineer"
    assert gate["reasons"] == [f"the drawing's wall index is {walls.held_detail()}: coverage and wall placement "
                               "not measured"]


def test_a16_d3_the_unit_table_and_the_header_reading():
    import ezdxf

    doc = ezdxf.new("R2018", setup=False)
    for code, factor, unit in ((1, 0.0254, "in"), (2, 0.3048, "ft"), (4, 0.001, "mm"), (5, 0.01, "cm"),
                               (6, 1.0, "m"), (21, 1200 / 3937, "us_ft")):
        doc.header["$INSUNITS"] = code
        assert (L.drawing_units(doc)["factor_to_m"], L.drawing_units(doc)["unit"]) == (factor, unit)
    for code in (0,):
        doc.header["$INSUNITS"] = code
        doc.header["$MEASUREMENT"] = 1          # metric -- but millimetres or metres? not a unit: held
        doc.header["$LUNITS"] = 2
        got = L.drawing_units(doc)
        assert not got["known"] and got["measurement"] == 1 and got["lunits"] == 2 and got["factor_to_m"] is None


# --- decision 4: MLINE ---------------------------------------------------------------------------


def test_a16_d4_f9_mline_walls_are_not_read_and_the_report_and_the_gate_say_mline_unsupported(tmp_path):
    walls = _build(tmp_path, "f9_mline.dxf")
    m = walls.report["mline_unsupported"]
    assert (m["count"], m["length_m"], m["hidden"], m["layers"]) == (3, 30.0, 1, {"06-WALL": 3})   # A-FURN not counted
    assert walls.report["totals"]["included_length_m"] == 5.0                  # only the LINE: MLINE not geometry
    assert all(r["kind"] != "MLINE" for r in walls.detail)
    assert walls.sparse and walls.held == "mline_unsupported" and walls.report["held"] == "mline_unsupported"
    assert walls.held_detail() == "sparse, mline_unsupported (3 MLINE on wall layers, 30.0 m, not read as walls)"
    # the preparation: not measured with that reason -- even where named boundaries would close the room
    by_hand = W.Walls({(0, 0): [(0.0, 0.0, 1.0, 0.0)]})
    cols = C.Columns({}, by_hand)
    group = PR.rooms([_detector("a", 5.0, 3.0)], {0: SHEET}, walls, cols)[0]
    assert group["room"] is None and "mline_unsupported" in group["index"]
    plan = PR.propose(group, {0: SHEET}, [], set(), cols)
    assert plan["open"] and "mline_unsupported" in plan["issues"][0] and "not measured" in plan["issues"][0]
    state = PR.index_state(walls, cols)
    assert state["walls"] == "mline_unsupported" and state["mline_unsupported"]["count"] == 3
    gate = PR.gate([], {"wall_index": state}, REVIEWED_ON, cols)
    assert gate["state"] == "needs_engineer" and len(gate["reasons"]) == 1
    assert "mline_unsupported" in gate["reasons"][0] and "not measured" in gate["reasons"][0]
    # a sparse index without MLINE stays "sparse" (unchanged wording), and a measured one adds no reason
    f1 = _build(tmp_path, "f1_simple.dxf")
    assert f1.held == "sparse" and PR.gate([], {"wall_index": PR.index_state(f1, None)}, REVIEWED_ON, None)["reasons"] == []


# --- decision 5: TAG -------------------------------------------------------------------------------


def test_a16_d5_a_door_tag_layer_is_no_boundary_and_doors_still_are():
    tag = L.local_name("X-REF_ TAG$0$49-DOOR-TAG")
    assert C.BOUND_LAYERS.search(tag) and C.NOT_BOUNDS.search(tag)
    assert C.NOT_BOUNDS.pattern == r"TILE|HTCH|HATCH|TEXT|DIM|FINISH|TAG"
    for door in ("14-DOOR", "X-REF_ FILE ALL FLOORS PLANS$0$14-DOOR", "X-REF_LANDSCAPE$0$14-DOOR"):
        assert C.BOUND_LAYERS.search(L.local_name(door)) and not C.NOT_BOUNDS.search(L.local_name(door))


# --- decision 6: the rotation term (F021) ------------------------------------------------------------


class _Page:
    """A plotted page's text lines, as pymupdf's get_text("dict") gives them."""

    def __init__(self, lines):
        self.lines = lines

    def get_text(self, _kind):
        return {"blocks": [{"lines": [{"spans": [{"text": t}], "bbox": (x - 10, y - 3, x + 10, y + 3)}
                                      for t, x, y in self.lines]}]}


def _turned(a, rot_deg, bx, by, x, y):
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    u, v = x, -y
    return a * (c * u - s * v) + bx, a * (s * u + c * v) + by


def test_a16_d6_a_twisted_view_fits_only_with_the_rotation_term():
    names = ["STORE ROOM", "PUMP ROOM", "ELEC ROOM", "LOBBY HALL", "CORRIDOR", "MEETING ROOM", "OFFICE 01", "PANTRY"]
    pts = [(100, 120), (400, 90), (700, 160), (150, 420), (450, 380), (760, 450), (260, 650), (620, 700)]
    page = _Page([(n, x, y) for n, (x, y) in zip(names, pts)])
    model = [(n, *_turned(0.2, -30.0, 1000.0, 500.0, x, y)) for n, (x, y) in zip(names, pts)]
    assert G.fit(page, model) is None                                     # without the rotation: not tied
    g = G.fit(page, model, {"handle": "AB", "twist_deg": 30.0, "frozen_layers": []})
    assert g is not None and g["rot_deg"] == -30.0 and abs(g["a"] - 0.2) < 1e-9 and g["residual"] == 0.0
    assert g["view"]["handle"] == "AB"
    for (n, x, y), (_n, mx, my) in zip(page.lines, model):
        assert math.dist(G.to_model(g, x, y), (mx, my)) < 1e-6
        assert math.dist(G.to_page(g, mx, my), (x, y)) < 1e-6
        assert R._page(g, mx, my) == [round(x, 2), round(y, 2)]
    # a twist the texts do not bear out ties nothing; viewports twisted differently tie nothing
    assert G.fit(page, model, {"twist_deg": -30.0}) is None
    assert G.fit(page, model, {"mixed": True, "viewports": []}) is None


def test_a16_d6_an_untwisted_view_gives_the_fit_it_gave_before():
    names = ["STORE ROOM", "PUMP ROOM", "ELEC ROOM", "LOBBY HALL", "CORRIDOR"]
    pts = [(100, 120), (400, 90), (700, 160), (150, 420), (450, 380)]
    page = _Page([(n, x, y) for n, (x, y) in zip(names, pts)])
    model = [(n, 0.0617 * x + 1000 + 0.01 * k, -0.0617 * y + 500) for k, (n, (x, y)) in enumerate(zip(names, pts))]
    before = G.fit(page, model)
    after = G.fit(page, model, {"handle": "1", "twist_deg": 0.0, "frozen_layers": []})
    assert {k: v for k, v in after.items() if k != "view"} == before and "rot_deg" not in after
    assert G.to_model(before, 10, 20) == (before["a"] * 10 + before["bx"], -before["a"] * 20 + before["by"])
    assert R._page(before, 1000.0, 500.0) == [round((1000.0 - before["bx"]) / before["a"], 2),
                                               round((before["by"] - 500.0) / before["a"], 2)]


def test_a16_d6_f12_the_plot_of_a_twisted_viewport_is_tied_through_the_sheets_view(tmp_path, monkeypatch):
    """End to end: the page is drawn from the fixture through ezdxf's own
    viewport transform (model -> paper), then tied back by fit_sheets."""
    import ezdxf
    import pymupdf

    from app.ifc import storage

    dxf = FIX / "f12_rotated_view.dxf"
    doc = ezdxf.readfile(dxf)
    vp = next(v for v in doc.layouts.get("FA-201").query("VIEWPORT"))
    m = vp.get_transformation_matrix()
    width, height = 420.0 * 72 / 25.4, 297.0 * 72 / 25.4
    pdf = pymupdf.open()
    page = pdf.new_page(width=width, height=height)
    model = {}
    for e in doc.modelspace().query("TEXT"):
        p = m.transform(e.dxf.insert)
        x, y = p.x * 72 / 25.4, height - p.y * 72 / 25.4
        w = pymupdf.get_text_length(e.dxf.text, fontsize=6)
        page.insert_text((x - w / 2, y + 2.0), e.dxf.text, fontsize=6)
        model[e.dxf.text] = (e.dxf.insert.x, e.dxf.insert.y)
    path = tmp_path / "plot.pdf"
    pdf.save(path)
    pdf.close()
    monkeypatch.setattr(storage, "dxf_path", lambda drawing: dxf)
    sheets = [{"index": 0, "name": "FA-201"}]
    G.fit_sheets(SimpleNamespace(ep_number=1), SimpleNamespace(id=1), str(path), sheets)
    g = sheets[0]["geometry"]
    assert "error" not in g, g
    assert g["rot_deg"] == -30.0 and g["view"]["twist_deg"] == 30.0 and g["view"]["handle"] == vp.dxf.handle
    assert g["view"]["scale"] == pytest.approx(260.0 / 100.0) and g["residual"] < 0.5
    check = pymupdf.open(path)
    try:
        for line in (ln for b in check[0].get_text("dict")["blocks"] for ln in b.get("lines", [])):
            text = "".join(s["text"] for s in line["spans"])
            cx, cy = (line["bbox"][0] + line["bbox"][2]) / 2, (line["bbox"][1] + line["bbox"][3]) / 2
            assert math.dist(G.to_model(g, cx, cy), model[text]) < 0.5, text
    finally:
        check.close()
    # without its view the same sheet is not tied (the old fit)
    assert G.fit(pymupdf.open(path)[0], [(t, x, y) for t, (x, y) in model.items()]) is None


def test_a16_d6_the_wall_index_is_built_for_the_sheets_viewport_where_one_index_serves_them_all(tmp_path, monkeypatch):
    from app.ifc import storage

    view = lambda h, frozen: {"geometry": {"a": 1, "view": {"handle": h, "twist_deg": 0.0, "frozen_layers": frozen}}}
    assert R._index_viewport({0: view("B1", ["A-PARTITION"]), 1: view("A7", ["A-PARTITION"])}) == "A7"
    assert R._index_viewport({0: view("B1", ["A-PARTITION"]), 1: view("A7", [])}) is None    # sheets differ
    assert R._index_viewport({0: view("B1", []), 1: {"geometry": {"a": 1}}}) is None          # nothing frozen
    assert R._index_viewport([]) is None
    # the call passes it on to the build: the twisted viewport's frozen partition is not a wall
    import ezdxf

    handle = next(iter(ezdxf.readfile(FIX / "f5_viewport.dxf").layouts.get("FA-101").query("VIEWPORT"))).dxf.handle
    monkeypatch.setattr(storage, "uploads_root", lambda: tmp_path)
    monkeypatch.setattr(storage, "dxf_path", lambda drawing: FIX / "f5_viewport.dxf")
    monkeypatch.setattr(R, "_WALLS", {})
    project, drawing = SimpleNamespace(ep_number=7), SimpleNamespace(id=3)
    walls = R._walls(project, drawing, "sha", build=True, sheets={0: view(handle, ["A-PARTITION"])})
    assert walls.report["viewport"]["handle"] == handle and walls.report["viewport"]["view_twist_deg"] == 30.0
    plain = R._walls(project, drawing, "sha", build=True)
    assert plain.report["viewport"] is None and plain is not walls


# --- decision 7: arcs and meshes --------------------------------------------------------------------


def test_a16_d7_f10_arcs_are_wall_candidates_and_meshes_are_counted_never_read(tmp_path):
    walls = _build(tmp_path, "f10_meshes.dxf")
    meshes = walls.report["mesh_not_read"]
    assert (meshes["polyface"], meshes["polygon_mesh"], meshes["on_wall_layers"]) == (1, 1, 2)
    assert {r["kind"] for r in walls.detail} == {"LINE", "ARC"}               # no POLYLINE mesh read as a line
    arcs = [r for r in walls.detail if r["kind"] == "ARC" and r["reason"] is None]
    assert len(arcs) == 16 and all(abs(math.dist((0.0, 40.0), r["seg"][:2]) - 5.0) < 2 * L.FLATTEN for r in arcs)
    assert not any(20 <= r["seg"][0] <= 30 and r["seg"][1] <= 10 for r in walls.detail)   # the polygon mesh
    cols = _cols(tmp_path, "f10_meshes.dxf")
    assert cols.report["mesh_not_read"] == {"polyface": 1, "polygon_mesh": 1}
    assert W.KINDS == {"LINE", "LWPOLYLINE", "POLYLINE", "ARC"}


# --- decision 8: TILE / FINISH -----------------------------------------------------------------------


def test_a16_d8_the_allow_list_regex_is_pinned():
    pinned = r"^(?!.*(?:TILE|FINISH)).*(?:WALL|PARTITION|CURTAIN|GLASS|GLAZ|SILL)"
    assert Settings.model_fields["prep_wall_layers"].default == pinned == get_settings().prep_wall_layers
    allow = re.compile(pinned, re.I)
    for name in ("23-WALL-TILES", "WALL FINISH", "22-FINISH", "A-WALL-TILE"):
        assert not allow.search(L.local_name(name)), name
    for name in ("06-WALL", "X-REF_ FILE ALL FLOORS PLANS$0$06-WALL", "11-GLASS-1", "10-SILL", "A-PARTITION"):
        assert allow.search(L.local_name(name)), name


# --- U2M8V-04: visibility in the named-boundary index -------------------------------------------------


def test_u2m8v04_f11_the_boundary_index_honours_layer_and_insert_visibility(tmp_path):
    import ezdxf
    from ezdxf import disassemble

    cols = _cols(tmp_path, "f11_bounds_hidden.dxf")
    assert cols.report["bounds_length_m"] == 300.0 and cols.bounds is not None
    assert cols.report["hidden"] == {"insert_layer_frozen": 1, "invisible": 1, "layer_frozen": 1}
    assert {s[1] for s in _bounds(cols)} == {0.0, 0.2, 10.0}                  # the frozen, invisible and inserted: out
    # the raw-layer rule of the base code (no visibility, layer "0" not named) found 400 m
    raw = 0.0
    for e in disassemble.recursive_decompose(ezdxf.readfile(FIX / "f11_bounds_hidden.dxf").modelspace()):
        layer = e.dxf.get("layer", "")
        if e.dxftype() == "LINE" and C.BOUND_LAYERS.search(layer) and not C.NOT_BOUNDS.search(layer):
            raw += math.dist(e.dxf.start, e.dxf.end)
    assert raw == 400.0


# --- Golden GC-01 ------------------------------------------------------------------------------------

GC01 = Path("G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dxf")


@pytest.mark.skipif(not GC01.is_file(), reason="the owner's EP-30880 GC-01 DXF is not on this machine")
def test_golden_gc01_the_engineers_decisions_on_the_wall_and_boundary_indexes(tmp_path):
    """Read-only; indexes built into tmp_path. Decision 1: the 72 T.FRAM and 4
    DIM_TEXT segments leave the kept walls; decision 3: metres by $INSUNITS 6;
    decision 5: the door-tag layer is no boundary."""
    walls = W.build(GC01, tmp_path / "gc01.pkl")
    rep = walls.report
    assert rep["units"]["unit"] == "m" and rep["units"]["factor_to_m"] == 1.0 and walls.held is None
    frames = rep["title_frame_blocks"]
    t_fram = frames["X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM"]
    assert t_fram["layers"]["06-WALL"] >= 72 and frames["X-REF_ DIM_TEXT"]["segments"] >= 4
    assert rep["layers"]["06-WALL"]["excluded"].get("title_frame") == 76 and rep["layers"]["06-WALL"]["included"] == 19
    assert rep["totals"]["included"] == 16569 and rep["totals"]["included_length_m"] == pytest.approx(24877.578, abs=0.01)
    assert rep["mline_unsupported"]["count"] == 0 and not rep["sparse"]
    cols = C.build_columns(GC01, tmp_path / "cols.pkl", get_settings().prep_column_layers)
    assert len(cols) == 338 and cols.report["hidden"].get("title_frame") == 76
    assert "X-REF_ TAG$0$49-DOOR-TAG" not in cols.report["bounds_layers"]
    assert not any(abs(s[1] - 95.7254) < 1e-3 and abs(s[3] - 95.7254) < 1e-3 and abs(abs(s[2] - s[0]) - 119.83) < 0.01
                   for s in _bounds(cols))
