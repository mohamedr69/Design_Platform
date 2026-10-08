"""M8 wall index (ORCH-036): the walls are the lines whose effective layer is
shown and named a wall -- layer "0" inside a block on its INSERT's layer, the
INSERT chain's transforms composed, hidden layers, invisible entities and
viewport-frozen layers left out, an allow-list first and NOT_WALLS second --
and every segment is accounted for in the index's layer composition report.

Fixtures: tests/fixtures_m8/*.dxf, written by tests/fixtures_m8/make_fixtures.py
(ezdxf, no AutoCAD). The Golden GC-01 test reads the owner's EP-30880 DXF
read-only and is skipped where it is absent. No model is called here."""
from __future__ import annotations

import json
import math
import pickle
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

FIX = Path(__file__).resolve().parent / "fixtures_m8"
GC01 = Path("G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dxf")
RD_M1 = Path(__file__).resolve().parents[2] / "docs" / "milestones" / "redesign" / "RD-M1" / "evidence"

GEOMETRY = {"v": 1, "a": 0.1, "bx": 0.0, "by": 100.0, "residual": 0.4}
SHEET = {"index": 0, "name": "FA 101", "floor": "GROUND FLOOR", "plan": [0, 0, 2000, 2000], "geometry": GEOMETRY}


def _build(tmp_path, name, **kw) -> W.Walls:
    return W.build(FIX / name, tmp_path / (name + ".pkl"), detail=True, **kw)


def _kept(walls) -> set:
    return {r["seg"] for r in walls.detail if r["reason"] is None}


def _indexed(walls) -> set:
    return {s for segs in walls.cells.values() for s in segs}


def _reasons(walls) -> dict:
    out: dict = {}
    for r in walls.detail:
        if r["reason"] is not None:
            out[(r["layer"], r["reason"])] = out.get((r["layer"], r["reason"]), 0) + 1
    return out


def _r(seg, nd=3):
    return tuple(round(v, nd) for v in seg)


def _place(p, ins, base=(0.0, 0.0), rot=0.0, sx=1.0, sy=1.0):
    """An INSERT's placement by hand (not Matrix44): (p - base) scaled, rotated, moved."""
    x, y = (p[0] - base[0]) * sx, (p[1] - base[1]) * sy
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return ins[0] + x * c - y * s, ins[1] + x * s + y * c


# --- the rules --------------------------------------------------------------------------


def test_the_wall_allow_list_is_a_setting_beside_the_column_layers_and_reads_the_layers_own_name():
    default = Settings.model_fields["prep_wall_layers"].default
    assert get_settings().prep_wall_layers == default
    allow = re.compile(default, re.I)
    for name in ("06-WALL", "A-WALL", "11-GLASS-1", "12-GLASS-2", "10-SILL", "A-PARTITION", "CURTAIN WALL", "A-GLAZING"):
        assert allow.search(name), name
    for name in ("23-WALL-TILES", "WALL FINISH", "02-CAB", "21-HIDDEN", "0", "-Ext", "08-COLUMN"):
        assert not allow.search(name), name
    assert L.local_name("X-REF_ FILE ALL FLOORS PLANS$0$06-WALL") == "06-WALL"
    assert L.local_name("ARCH|A-WALL") == "A-WALL" and L.local_name("06-WALL") == "06-WALL"
    assert L.effective_layer("0", "X$0$06-WALL") == "X$0$06-WALL" and L.effective_layer("A", "B") == "A"
    assert L.effective_layer("0", None) == "0"


# --- the seven fixtures -------------------------------------------------------------------


def test_f1_a_simple_sheet_keeps_the_double_walls_and_accounts_for_every_other_line(tmp_path):
    walls = _build(tmp_path, "f1_simple.dxf")
    inner = {(0.0, 0.0, 10.0, 0.0), (10.0, 0.0, 10.0, 6.0), (10.0, 6.0, 0.0, 6.0), (0.0, 6.0, 0.0, 0.0)}
    outer = {(-0.2, -0.2, 10.2, -0.2), (10.2, -0.2, 10.2, 6.2), (10.2, 6.2, -0.2, 6.2), (-0.2, 6.2, -0.2, -0.2)}
    wide = {(0.0, -6.0, 10.0, -6.0)}                                       # its centre line, not its width's outline
    assert _kept(walls) == inner | outer | wide == _indexed(walls)
    assert _reasons(walls) == {("A-WALL", "below_min_length"): 1, ("A-FURN", "deny_listed"): 4,
                               ("A-EQPM", "not_allow_listed"): 1, ("0", "not_allow_listed"): 1}
    rep = walls.report
    assert rep["layers"]["A-WALL"] == {"segments": 10, "length_m": 75.7, "included": 9, "included_length_m": 75.6,
                                       "excluded": {"below_min_length": 1}, "via_insert": 0, "top_level": 10,
                                       "included_via_insert": 0}
    assert rep["totals"]["segments"] == 16 and rep["totals"]["included"] == 9
    assert rep["totals"]["excluded"] == {"below_min_length": 1, "deny_listed": 4, "not_allow_listed": 2}
    assert rep["sparse"] and walls.sparse                                  # 75.6 m: too little to close rooms by
    assert walls.thick(5.0, 0.0, (0.0, 1.0))                               # both faces of the wall are kept


def test_f2_nested_inserts_compose_base_point_scale_rotation_and_mirror_and_layer_0_inherits(tmp_path):
    walls = _build(tmp_path, "f2_nested.dxf")
    room = dict(ins=(100.0, 50.0), base=(1.0, 1.0), rot=30.0, sx=2.0, sy=2.0)
    pairs = [dict(ins=(1.0, 1.0)), dict(ins=(5.0, 1.0), rot=90.0, sx=0.5, sy=0.5), dict(ins=(1.0, 8.0), sx=-1.0)]
    expected = set()
    for pair in pairs:
        for a, b in (((0, 0), (4, 0)), ((0, 0.2), (4, 0.2))):
            pa, pb = _place(_place(a, **pair), **room), _place(_place(b, **pair), **room)
            expected.add(_r((*pa, *pb)))
    expected.add((0.0, -20.0, 2.0, -20.0))                                 # LOOP's own line, once
    lines = {_r(r["seg"]) for r in walls.detail if r["reason"] is None and r["kind"] == "LINE"}
    assert lines == expected
    # the arcs (layer "0", so 06-WALL) stay on their circles: radius 5 x the chain's scale
    for pair, radius in zip(pairs, (10.0, 5.0, 10.0)):
        centre = _place(_place((0, 0), **pair), **room)
        arc = [r for r in walls.detail if r["kind"] == "ARC" and r["reason"] is None
               and abs(math.dist(centre, r["seg"][:2]) - radius) < 2 * L.FLATTEN]
        assert len(arc) == 16                                               # flattened in its block: 17 vertices
        assert all(abs(math.dist(centre, r["seg"][2:]) - radius) < 2 * L.FLATTEN for r in arc)
    # explicit layers keep their own layer; layer "0" under an A-EQPM insert is A-EQPM
    assert _reasons(walls) == {("A-EQPM", "not_allow_listed"): 22, ("08-COLUMN", "not_allow_listed"): 4}
    assert all(r["layer"] == "06-WALL" and r["raw_layer"] == "0" for r in walls.detail if r["reason"] is None)
    # the self-insert is refused once, the chain deeper than the cap is not followed
    assert walls.report["walk"]["self_inserts"] == 1 and walls.report["walk"]["depth_capped"] == 1
    assert not any(r["seg"][0] >= 300 for r in walls.detail)
    row = walls.report["layers"]["06-WALL"]
    assert row["segments"] == row["included"] == row["via_insert"] == row["included_via_insert"] == 55
    assert row["top_level"] == 0 and row["included_length_m"] == walls.report["totals"]["included_length_m"]
    # a wall face through the chain still has its other face behind it (0.2 m x 2)
    (ax, ay), (bx, by) = _place(_place((0, 0), **pairs[0]), **room), _place(_place((4, 0), **pairs[0]), **room)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    n = (-(by - ay) / math.dist((ax, ay), (bx, by)), (bx - ax) / math.dist((ax, ay), (bx, by)))
    assert walls.thick(mx, my, (-n[0], -n[1]))


def test_f2_the_transforms_agree_with_ezdxfs_own_explosion(tmp_path):
    """An independent check of the composition: ezdxf's recursive_decompose
    (what walls.build used before M8), on the inserts without a cycle or a
    capped chain, places every line where the index does."""
    import ezdxf
    from ezdxf import disassemble

    walls = _build(tmp_path, "f2_nested.dxf")
    doc = ezdxf.readfile(FIX / "f2_nested.dxf")
    top = [e for e in doc.modelspace() if e.dxf.name not in ("LOOP", "D0")]
    theirs = set()
    for e in disassemble.recursive_decompose(top):
        if e.dxftype() in ("LINE", "LWPOLYLINE"):
            vs = list(disassemble.make_primitive(e).vertices())
            theirs |= {_r((a.x, a.y, b.x, b.y)) for a, b in zip(vs, vs[1:])}
    ours = {_r(r["seg"]) for r in walls.detail if r["kind"] in ("LINE", "LWPOLYLINE") and r["chain"][0] != "LOOP"}
    assert ours == theirs


def test_f3_layers_off_frozen_and_no_plot_and_inserts_on_hidden_layers_are_not_walls(tmp_path):
    walls = _build(tmp_path, "f3_states.dxf")
    # Engineer decision 2 (A-16, ORCH-044), the AutoCAD rule: B0 on an off layer hides
    # only its layer-"0" line; its explicit A-WALL line (20,1)-(23,1) is shown and kept
    # (was insert_layer_off under ORCH-036 item 3). B0 on a frozen layer hides both.
    assert _kept(walls) == {(0.0, 0.0, 3.0, 0.0), (30.0, 0.0, 33.0, 0.0), (30.0, 1.0, 33.0, 1.0),
                            (20.0, 1.0, 23.0, 1.0)}
    assert _reasons(walls) == {
        ("A-WALL-OFF", "layer_off"): 1, ("A-WALL-FROZEN", "layer_frozen"): 1, ("A-WALL-NOPLOT", "layer_no_plot"): 1,
        ("Defpoints", "layer_no_plot"): 1,
        # B0 on a frozen layer: insert_layer_frozen for all its content (decision 2; the
        # inherited line was layer_frozen)
        ("X-INS-FROZEN", "insert_layer_frozen"): 1, ("A-WALL", "insert_layer_frozen"): 1,
        # B0 on an off layer: insert_layer_off for the inherited line only (decision 2)
        ("X-INS-OFF", "insert_layer_off"): 1,
        ("08-COLUMN", "not_allow_listed"): 4, ("08-COLUMN-OFF", "layer_off"): 4}
    assert walls.report["layers"]["A-WALL"]["excluded"] == {"insert_layer_frozen": 1}
    # the columns index reads by the same rules: the column on the off layer is not kept clear of
    cols = C.build_columns(FIX / "f3_states.dxf", tmp_path / "cols.pkl", get_settings().prep_column_layers)
    assert {b for boxes in cols.cells.values() for b in boxes} == {(40.0, 0.0, 40.5, 0.5)}
    assert cols.report["hidden"]["layer_off"] >= 1 and cols.bounds is None


def test_f4_the_invisible_flag_hides_a_line_and_everything_in_an_invisible_insert(tmp_path):
    walls = _build(tmp_path, "f4_invisible.dxf")
    assert _kept(walls) == {(0.0, 0.0, 4.0, 0.0), (10.0, 0.0, 14.0, 0.0)}
    assert _reasons(walls) == {("A-WALL", "invisible"): 1, ("A-WALL", "insert_invisible"): 1}


def _viewports(name):
    import ezdxf

    doc = ezdxf.readfile(FIX / name)
    return {layout: next(iter(doc.layouts.get(layout).query("VIEWPORT"))).dxf.handle for layout in ("FA-101", "FA-102")}


def test_f5_a_layer_frozen_in_the_twisted_viewport_is_left_out_and_the_index_stays_in_model_space(tmp_path):
    vps = _viewports("f5_viewport.dxf")
    model = W.build(FIX / "f5_viewport.dxf", tmp_path / "m.pkl", detail=True)
    twisted = W.build(FIX / "f5_viewport.dxf", tmp_path / "t.pkl", detail=True, viewport=vps["FA-101"])
    plain = W.build(FIX / "f5_viewport.dxf", tmp_path / "p.pkl", detail=True, viewport=vps["FA-102"])
    partition = (6.0, 0.0, 6.0, 8.0)
    assert partition in _kept(model) and partition in _kept(plain) and partition not in _kept(twisted)
    assert _reasons(twisted) == {("A-PARTITION", "viewport_frozen"): 1}
    # the 30 degree twist does not turn the index: model coordinates, as before (F021 untouched)
    assert _kept(twisted) == _kept(model) - {partition}
    vp = twisted.report["viewport"]
    assert vp["view_twist_deg"] == 30.0 and vp["frozen_layers"] == ["A-PARTITION"] and vp["layout"] == "FA-101"
    assert model.report["viewport"] is None and plain.report["viewport"]["frozen_layers"] == []
    assert W.fingerprint(viewport=vps["FA-101"]) != W.fingerprint()
    with pytest.raises(ValueError):
        W.build(FIX / "f5_viewport.dxf", tmp_path / "x.pkl", viewport="FFFF")


def test_f6_bound_xref_layers_are_read_by_their_own_name_and_inherit_through_the_xref_block(tmp_path):
    walls = _build(tmp_path, "f6_xref.dxf")
    assert _kept(walls) == {(0.0, 0.0, 120.0, 0.0), (0.0, 0.2, 120.0, 0.2),     # layer "0" in the xref block
                            (0.0, 20.0, 4.0, 20.0),                              # FIRE ALARM only in the prefix
                            (0.0, 50.0, 4.0, 50.0)}                              # 11-GLASS-1
    # the frozen copy's layer-"0" lines: insert_layer_frozen (engineer decision 2, A-16; was layer_frozen)
    assert _reasons(walls) == {("X-ARCH$0$02-CAB", "not_allow_listed"): 1, ("X-ARCH$0$02-CAB", "insert_layer_frozen"): 1,
                               ("X-FRZ-XREF", "insert_layer_frozen"): 2, ("X-ARCH$0$29-PARKING", "deny_listed"): 1,
                               ("X-PLOT$0$A-NORTH", "layer_frozen"): 1}
    assert walls.report["layers"]["X-ARCH$0$06-WALL"]["via_insert"] == 2
    # the named boundaries: 248 m, reachable only through layer "0" inheritance
    cols = C.build_columns(FIX / "f6_xref.dxf", tmp_path / "cols.pkl", get_settings().prep_column_layers)
    assert cols.bounds is not None and cols.report["bounds_length_m"] == 248.0
    bounds = {s for segs in cols.bounds.cells.values() for s in segs}
    assert (0.0, 0.0, 120.0, 0.0) in bounds and not any(s[1] >= 100 for s in bounds)   # the frozen copy: not
    # the raw-layer rule it replaces found 8 m (the "0" lines are not named), so no boundaries at all
    import ezdxf
    from ezdxf import disassemble

    raw = 0.0
    for e in disassemble.recursive_decompose(ezdxf.readfile(FIX / "f6_xref.dxf").modelspace()):
        layer = e.dxf.get("layer", "")
        if C.BOUND_LAYERS.search(layer) and not C.NOT_BOUNDS.search(layer) and e.dxftype() == "LINE":
            raw += math.dist(e.dxf.start, e.dxf.end)
    assert raw == 8.0 < C.MIN_BOUNDS_M


def test_f7_the_allow_list_ends_the_deny_lists_false_negatives_and_an_override_its_false_positives(tmp_path):
    walls = _build(tmp_path, "f7_denylist.dxf")
    by_layer = {r["layer"]: r["reason"] for r in walls.detail}
    assert by_layer == {"06-WALL": None, "A-WALL-WING": "deny_listed", "STOREROOM-PARTITION": "deny_listed",
                        "CARGO-WALL": "deny_listed", "02-CAB": "not_allow_listed", "21-HIDDEN": "not_allow_listed",
                        "41-ELE-5": "not_allow_listed", "-Ext": "not_allow_listed", "55-RAMP": "not_allow_listed",
                        "23-WALL-TILES": "not_allow_listed"}
    # what the raw-layer deny-list alone kept (walls.py v1): seven layers, six of them not walls
    old = {name for name in by_layer if not W.NOT_WALLS.search(name)}
    assert old == {"06-WALL", "02-CAB", "21-HIDDEN", "41-ELE-5", "-Ext", "55-RAMP", "23-WALL-TILES"}
    # a per-build deny-list on whole words keeps the three walls NOT_WALLS refuses
    words = W.build(FIX / "f7_denylist.dxf", tmp_path / "w.pkl", detail=True,
                    deny=r"\b(?:GRID|DIM|TEXT|FURN|CAR|PARK|DOOR|WIN|ROOM|STAIR)\b")
    assert {r["layer"] for r in words.detail if r["reason"] is None} == {
        "06-WALL", "A-WALL-WING", "STOREROOM-PARTITION", "CARGO-WALL"}
    # and a per-build allow-list (a later per-project store feeds this)
    hidden = W.build(FIX / "f7_denylist.dxf", tmp_path / "h.pkl", detail=True, allow=r"WALL|HIDDEN")
    assert {r["layer"] for r in hidden.detail if r["reason"] is None} == {"06-WALL", "21-HIDDEN", "23-WALL-TILES"}
    assert hidden.report["rules"]["allow"] == "WALL|HIDDEN"
    assert hidden.report["rules"]["fingerprint"] != walls.report["rules"]["fingerprint"]


# --- the stored index ------------------------------------------------------------------------


def test_the_saved_index_carries_its_report_and_its_name_its_version_and_rules(tmp_path, monkeypatch):
    from app.ifc import storage

    monkeypatch.setattr(storage, "uploads_root", lambda: tmp_path)
    project, drawing = SimpleNamespace(ep_number=30880), SimpleNamespace(id=1)
    sha = "66043c11fab9eaf5" + "0" * 48
    path = W.path_for(project, drawing, sha)
    # version 3 (ORCH-044): the engineer's decisions 1-4 and 7 (A-16) change what a build keeps
    assert W.VERSION == 3 and path.name == f"walls-1-66043c11fab9eaf5-v3-{W.fingerprint()}.pkl"
    assert W.path_for(project, drawing, sha, allow="WALL") != path
    assert W.path_for(project, drawing, sha, deny="GRID") != path
    assert W.path_for(project, drawing, sha) == path
    built = W.build(FIX / "f1_simple.dxf", path)
    loaded = W.load(path)
    assert loaded.cells == built.cells and loaded.report == built.report and loaded.detail is None
    # an index saved by version 1 (a bare pickle of the cells) or another version is built again
    with open(path, "wb") as f:
        pickle.dump(built.cells, f)
    assert W.load(path) is None
    with open(path, "wb") as f:
        pickle.dump({"format": "walls", "version": 1, "cells": built.cells, "report": None}, f)
    assert W.load(path) is None
    # the columns index too: its rules in its name, a new version
    cpath = C.columns_path(project, drawing, sha)
    # version 4 (ORCH-044): decisions 1, 3, 5 and 7 (A-16) change what a build keeps
    assert C.VERSION == 4 and cpath.name.startswith("columns-1-66043c11fab9eaf5-v4-")
    assert C.columns_path(project, drawing, sha, layers="PILLAR") != cpath


def test_the_walls_interface_is_unchanged_for_its_consumers():
    cells = {(0, 0): [(0.0, 0.0, 1.0, 0.0)]}
    walls = W.Walls(cells)
    assert walls.cells is cells and walls.report is None and not walls.sparse
    assert walls.near(0.5, 0.0, 1.0) == [(0.0, 0.0, 1.0, 0.0)]
    for name in ("near", "faces_behind", "face_behind", "thick", "face_span"):
        assert callable(getattr(walls, name))


def _detector(cid, x, y):
    return {"id": cid, "page": 0, "sheet": "FA 101", "floor": "GROUND FLOOR", "room": "STORE", "system": "detection",
            "system_name": "Detection", "action": "add", "device": "smoke detector", "status": "proposed",
            "moved": False, "box": [0, 0, 400, 400], "candidates": [],
            "insert": {"symbol": 1, "name": "Smoke Detector", "block": "SD", "seen": [x, y], "placed": [x, y],
                       "model": [x, y], "offset": [0, 0], "radius": 0.2, "page": R._page(GEOMETRY, x, y)}}


def test_a_sparse_or_missing_wall_index_leaves_coverage_not_measured_never_measured_against_no_walls(tmp_path):
    built = _build(tmp_path, "f1_simple.dxf")
    assert built.sparse
    # the same lines made by hand close the room: the sparse index is what says "not measured"
    by_hand = W.Walls(built.cells)
    room = C.room_at(by_hand, None, 5.0, 3.0)
    assert room is not None and not room.open
    assert C.room_at(built, None, 5.0, 3.0) is None
    for walls, word in ((built, "sparse"), (None, "missing")):
        group = PR.rooms([_detector("a", 5.0, 3.0)], {0: SHEET}, walls, None)[0]
        assert group["room"] is None and group["index"] == word
        plan = PR.propose(group, {0: SHEET}, [], set(), None)
        assert plan["open"] and plan["before"] is None
        assert plan["issues"] == [f"the drawing's wall index is {word}: no room can be closed from it, "
                                  "coverage not measured"]
    # named boundaries, where the drawing has them, still close the room
    cols = C.Columns({}, by_hand)
    assert "index" not in PR.rooms([_detector("a", 5.0, 3.0)], {0: SHEET}, built, cols)[0]


# --- Golden GC-01 ------------------------------------------------------------------------------


@pytest.mark.skipif(not GC01.is_file(), reason="the owner's EP-30880 GC-01 DXF is not on this machine")
def test_golden_gc01_layer_composition_against_rd_m1_e10_and_e11(tmp_path):
    """Read-only: the index is built into tmp_path. E10/E11 are the RD-M1
    before-values; the differences are reported (M8 implementation report),
    only what the rules decide is asserted here."""
    walls = W.build(GC01, tmp_path / "gc01.pkl", detail=True)
    rep = walls.report
    layers = rep["layers"]
    e10 = json.loads((RD_M1 / "E10-wall-index-layers.json").read_text(encoding="utf-8"))
    e11 = json.loads((RD_M1 / "E11-effective-layers.json").read_text(encoding="utf-8"))
    xref = "X-REF_ FILE ALL FLOORS PLANS$0$"
    # E10: the frozen xref layer the v1 index kept (342 segments) is out, as frozen
    north = layers["X-REF_PLOT$0$A-NORTH"]
    assert north["included"] == 0 and north["excluded"].get("layer_frozen", 0) >= \
        e10["non_plotting_layers_in_wall_index"]["X-REF_PLOT$0$A-NORTH"]["n"]
    # E10's largest non-wall layers are no longer walls; its wall layer is
    for name in ("02-CAB", "21-HIDDEN", "41-ELE-5", "55-RAMP", "17-FIXTURE", "23-WALL-TILES"):
        assert layers.get(xref + name, {"included": 0})["included"] == 0, name
    assert layers[xref + "06-WALL"]["included"] > 0
    assert rep["totals"]["excluded"].get("invisible", 0) > 0
    # E11: the raw "0" lines of the "invisible rectangle" are 29-PARKING by inheritance -- not walls
    probe = [d for d in e11["detail"]["invisible-rect-left-edge"] if d["raw_layer"] == "0"]
    assert probe
    ours = [r for r in walls.detail if r["raw_layer"] == "0"]
    for d in probe:
        match = [r for r in ours if all(abs(a - b) < 2e-3 for a, b in zip(r["seg"], d["seg"]))]
        assert match and {r["layer"] for r in match} == {d["effective_layer"]}, d
        assert all(r["reason"] is not None for r in match if "PARKING" in r["layer"])
    assert not walls.sparse
