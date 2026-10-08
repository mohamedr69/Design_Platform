"""The M8 wall-index fixtures (ORCH-036): seven small synthetic drawings built
with ezdxf, no AutoCAD. Run from backend/:

    python -B tests/fixtures_m8/make_fixtures.py

and the .dxf files beside this script are written again, byte for byte the
same (ezdxf's fixed metadata for testing). Units are metres.

  f1_simple     one sheet: a double-walled room, furniture, equipment, a
                short wall stub, a wall drawn as a wide polyline, layer "0"
                in model space, one viewport
  f2_nested     nested INSERTs with a base point, scale, rotation and a
                mirror; layer "0" inherited through two levels; a block that
                inserts itself; an INSERT chain deeper than the cap; an arc
  f3_states     layers off, frozen, no-plot, DEFPOINTS; INSERTs on a frozen
                and an off layer holding layer-"0" and explicit-layer content;
                columns on a shown and an off layer
  f4_invisible  the entity invisible flag on a line and on an INSERT
  f5_viewport   two sheets: one viewport twisted 30 degrees with a layer
                frozen in it (VPLAYER), one plain
  f6_xref       bound-xref layer names ("X-ARCH$0$06-WALL"), layer "0"
                inside a bound xref block, a frozen xref layer, a wall layer
                whose xref prefix carries deny-list words; 240 m of
                boundary only reachable through layer-"0" inheritance
  f7_denylist   layer names NOT_WALLS gets wrong both ways

The engineer's decisions (A-16, ORCH-044) added:

  f8_title_frame    a title frame (CCSD > ...$0$T.FRAM, layer "0") inheriting
                    06-WALL, a BORDER block with explicit wall lines, an
                    X-REF_ DIM_TEXT block on 06-WALL, and 240 m of real wall
  f9_mline          walls drawn as MLINEs (and one MLINE off the wall layers,
                    one on a frozen wall layer) beside a sparse line index
  f10_meshes        a polyface and a polygon mesh on a wall layer, wall
                    lines and a wall arc
  f11_bounds_hidden named boundaries: 300 m shown, a frozen and an invisible
                    wall line and an INSERT on a frozen wall layer (400 m by
                    the raw-layer rule of the base code, 300 m now)
  u1..u4            the same 301.6 m of wall, a short stub and a 0.4 m column
                    in metres, millimetres, inches, and unitless ($INSUNITS 0)
  f12_rotated_view  eight room names in model space seen through a viewport
                    twisted 30 degrees (the plot is drawn from it by the test)

Determinism (U2M8V-03): the CLASSES section is written in a fixed order
(ezdxf adds the drawing's own entity classes from a set, whose order follows
the hash seed) and every file is written with LF line ends, so any run, any
PYTHONHASHSEED and any platform writes the same bytes (git keeps them as
written: .gitattributes "backend/tests/fixtures_m8/*.dxf -text").
"""
from __future__ import annotations

import io
import math
from pathlib import Path

import ezdxf
from ezdxf.sections.classes import REQ_R2004, REQUIRED_CLASSES

HERE = Path(__file__).resolve().parent


def new(insunits: int = 6):
    doc = ezdxf.new("R2018", setup=False)
    doc.header["$INSUNITS"] = insunits
    return doc, doc.modelspace()


def layers(doc, *names):
    for n in names:
        if n not in doc.layers:
            doc.layers.add(n)


def save(doc, name: str) -> Path:
    path = HERE / name
    doc.commit_pending_changes()
    # the CLASSES in a fixed order: the required ones, then the drawing's own types sorted
    for cls in REQUIRED_CLASSES.get(doc.dxfversion, REQ_R2004):
        doc.classes.add_class(cls)
    for dxftype in sorted(doc.entitydb.dxf_types_in_use()):
        doc.classes.add_class(dxftype)
    with io.open(path, mode="wt", encoding=doc.output_encoding, errors="dxfreplace", newline="\n") as f:
        doc.write(f)
    return path


def f1_simple():
    doc, msp = new()
    layers(doc, "A-WALL", "A-FURN", "A-EQPM")
    for a, b in (((0, 0), (10, 0)), ((10, 0), (10, 6)), ((10, 6), (0, 6)), ((0, 6), (0, 0))):
        msp.add_line(a, b, dxfattribs={"layer": "A-WALL"})
    msp.add_lwpolyline([(-0.2, -0.2), (10.2, -0.2), (10.2, 6.2), (-0.2, 6.2)], close=True,
                       dxfattribs={"layer": "A-WALL"})
    msp.add_line((20, 0), (20.1, 0), dxfattribs={"layer": "A-WALL"})          # a stub: below MIN_LENGTH
    msp.add_lwpolyline([(0, -6), (10, -6)], dxfattribs={"layer": "A-WALL", "const_width": 0.2})   # a wide line
    msp.add_lwpolyline([(2, 2), (3.2, 2), (3.2, 2.8), (2, 2.8)], close=True, dxfattribs={"layer": "A-FURN"})
    msp.add_line((5, 1), (7, 1), dxfattribs={"layer": "A-EQPM"})
    msp.add_line((0, -3), (10, -3), dxfattribs={"layer": "0"})
    sheet = doc.layouts.new("FA-101")
    sheet.add_viewport(center=(200, 150), size=(380, 260), view_center_point=(5, 3), view_height=12)
    return save(doc, "f1_simple.dxf")


def f2_nested():
    doc, msp = new()
    layers(doc, "06-WALL", "A-EQPM", "08-COLUMN")
    pair = doc.blocks.new("WALLPAIR", base_point=(0, 0))
    pair.add_line((0, 0), (4, 0), dxfattribs={"layer": "0"})
    pair.add_line((0, 0.2), (4, 0.2), dxfattribs={"layer": "0"})
    pair.add_line((1, 1), (3, 1), dxfattribs={"layer": "A-EQPM"})
    pair.add_arc((0, 0), 5, 0, 90, dxfattribs={"layer": "0"})
    col = doc.blocks.new("COLBLK", base_point=(0, 0))
    col.add_lwpolyline([(0, 0), (0.4, 0), (0.4, 0.4), (0, 0.4)], close=True, dxfattribs={"layer": "0"})
    room = doc.blocks.new("ROOM", base_point=(1, 1))
    room.add_blockref("WALLPAIR", (1, 1), dxfattribs={"layer": "0"})
    room.add_blockref("WALLPAIR", (5, 1), dxfattribs={"layer": "0", "rotation": 90, "xscale": 0.5, "yscale": 0.5})
    room.add_blockref("WALLPAIR", (1, 8), dxfattribs={"layer": "0", "xscale": -1})
    room.add_blockref("COLBLK", (3, 3), dxfattribs={"layer": "08-COLUMN", "rotation": 45})
    loop = doc.blocks.new("LOOP", base_point=(0, 0))
    loop.add_line((0, 0), (2, 0), dxfattribs={"layer": "0"})
    loop.add_blockref("LOOP", (1, 1), dxfattribs={"layer": "0"})
    for k in range(18):                       # D0 > D1 > ... > D17: deeper than layers.MAX_DEPTH
        deep = doc.blocks.new(f"D{k}", base_point=(0, 0))
        if k < 17:
            deep.add_blockref(f"D{k + 1}", (0, 0), dxfattribs={"layer": "0"})
        else:
            deep.add_line((0, 0), (3, 0), dxfattribs={"layer": "0"})
    msp.add_blockref("ROOM", (100, 50), dxfattribs={"layer": "06-WALL", "rotation": 30, "xscale": 2, "yscale": 2})
    msp.add_blockref("LOOP", (0, -20), dxfattribs={"layer": "06-WALL"})
    msp.add_blockref("WALLPAIR", (200, 0), dxfattribs={"layer": "A-EQPM"})
    msp.add_blockref("D0", (300, 0), dxfattribs={"layer": "06-WALL"})
    return save(doc, "f2_nested.dxf")


def f3_states():
    doc, msp = new()
    layers(doc, "A-WALL", "A-WALL-OFF", "A-WALL-FROZEN", "A-WALL-NOPLOT", "X-INS-FROZEN", "X-INS-OFF", "Defpoints",
           "08-COLUMN", "08-COLUMN-OFF")
    doc.layers.get("A-WALL-OFF").off()
    doc.layers.get("A-WALL-FROZEN").freeze()
    doc.layers.get("A-WALL-NOPLOT").dxf.plot = 0
    doc.layers.get("X-INS-FROZEN").freeze()
    doc.layers.get("X-INS-OFF").off()
    doc.layers.get("08-COLUMN-OFF").off()
    for y, name in enumerate(("A-WALL", "A-WALL-OFF", "A-WALL-FROZEN", "A-WALL-NOPLOT", "Defpoints")):
        msp.add_line((0, y), (3, y), dxfattribs={"layer": name})
    b0 = doc.blocks.new("B0", base_point=(0, 0))
    b0.add_line((0, 0), (3, 0), dxfattribs={"layer": "0"})
    b0.add_line((0, 1), (3, 1), dxfattribs={"layer": "A-WALL"})
    msp.add_blockref("B0", (10, 0), dxfattribs={"layer": "X-INS-FROZEN"})
    msp.add_blockref("B0", (20, 0), dxfattribs={"layer": "X-INS-OFF"})
    msp.add_blockref("B0", (30, 0), dxfattribs={"layer": "A-WALL"})
    msp.add_lwpolyline([(40, 0), (40.5, 0), (40.5, 0.5), (40, 0.5)], close=True, dxfattribs={"layer": "08-COLUMN"})
    msp.add_lwpolyline([(50, 0), (50.5, 0), (50.5, 0.5), (50, 0.5)], close=True,
                       dxfattribs={"layer": "08-COLUMN-OFF"})
    return save(doc, "f3_states.dxf")


def f4_invisible():
    doc, msp = new()
    layers(doc, "A-WALL")
    msp.add_line((0, 0), (4, 0), dxfattribs={"layer": "A-WALL"})
    msp.add_line((0, 1), (4, 1), dxfattribs={"layer": "A-WALL", "invisible": 1})
    b1 = doc.blocks.new("B1", base_point=(0, 0))
    b1.add_line((0, 0), (4, 0), dxfattribs={"layer": "A-WALL"})
    msp.add_blockref("B1", (10, 0), dxfattribs={"layer": "A-WALL"})
    msp.add_blockref("B1", (20, 0), dxfattribs={"layer": "A-WALL", "invisible": 1})
    return save(doc, "f4_invisible.dxf")


def f5_viewport():
    doc, msp = new()
    layers(doc, "A-WALL", "A-PARTITION")
    msp.add_lwpolyline([(0, 0), (12, 0), (12, 8), (0, 8)], close=True, dxfattribs={"layer": "A-WALL"})
    msp.add_line((6, 0), (6, 8), dxfattribs={"layer": "A-PARTITION"})
    twisted = doc.layouts.new("FA-101")
    vp = twisted.add_viewport(center=(200, 150), size=(380, 260), view_center_point=(6, 4), view_height=16)
    vp.dxf.view_twist_angle = 30.0
    vp.frozen_layers = ["A-PARTITION"]
    plain = doc.layouts.new("FA-102")
    plain.add_viewport(center=(200, 150), size=(380, 260), view_center_point=(6, 4), view_height=16)
    return save(doc, "f5_viewport.dxf")


def f6_xref():
    doc, msp = new()
    wall, cab, park = "X-ARCH$0$06-WALL", "X-ARCH$0$02-CAB", "X-ARCH$0$29-PARKING"
    fire_wall, north, glass = "X-FIRE ALARM$0$06-WALL", "X-PLOT$0$A-NORTH", "X-ARCH$0$11-GLASS-1"
    layers(doc, wall, cab, park, fire_wall, north, glass, "X-FRZ-XREF")
    doc.layers.get(north).freeze()
    doc.layers.get("X-FRZ-XREF").freeze()
    serv = doc.blocks.new("X-ARCH$0$BAS4- SERV", base_point=(0, 0))
    serv.add_line((0, 0), (120, 0), dxfattribs={"layer": "0"})
    serv.add_line((0, 0.2), (120, 0.2), dxfattribs={"layer": "0"})
    serv.add_line((0, 5), (2, 5), dxfattribs={"layer": cab})
    msp.add_blockref("X-ARCH$0$BAS4- SERV", (0, 0), dxfattribs={"layer": wall})
    msp.add_blockref("X-ARCH$0$BAS4- SERV", (0, 100), dxfattribs={"layer": "X-FRZ-XREF"})
    msp.add_line((0, 20), (4, 20), dxfattribs={"layer": fire_wall})
    msp.add_line((0, 30), (4, 30), dxfattribs={"layer": park})
    msp.add_line((0, 40), (4, 40), dxfattribs={"layer": north})
    msp.add_line((0, 50), (4, 50), dxfattribs={"layer": glass})
    return save(doc, "f6_xref.dxf")


DENY_LIST_LAYERS = ("06-WALL", "A-WALL-WING", "STOREROOM-PARTITION", "CARGO-WALL", "02-CAB", "21-HIDDEN", "41-ELE-5",
                    "-Ext", "55-RAMP", "23-WALL-TILES")


def f7_denylist():
    doc, msp = new()
    layers(doc, *DENY_LIST_LAYERS)
    for y, name in enumerate(DENY_LIST_LAYERS):
        msp.add_line((0, 2 * y), (3, 2 * y), dxfattribs={"layer": name})
    return save(doc, "f7_denylist.dxf")


def f8_title_frame():
    doc, msp = new()
    layers(doc, "06-WALL", "A-WALL")
    frame = doc.blocks.new("X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM", base_point=(0, 0))
    frame.add_lwpolyline([(0, 0), (120, 0), (120, 90), (0, 90)], close=True, dxfattribs={"layer": "0"})
    ccsd = doc.blocks.new("CCSD", base_point=(0, 0))
    ccsd.add_blockref("X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM", (0, 0), dxfattribs={"layer": "0"})
    border = doc.blocks.new("BORDER-A1", base_point=(0, 0))
    border.add_line((0, -10), (50, -10), dxfattribs={"layer": "A-WALL"})
    border.add_line((0, -10.2), (50, -10.2), dxfattribs={"layer": "A-WALL"})
    dim = doc.blocks.new("X-REF_ DIM_TEXT", base_point=(0, 0))
    dim.add_line((0, 0), (5, 0), dxfattribs={"layer": "0"})            # inherits 06-WALL: annotation
    dim.add_line((0, 1), (4, 1), dxfattribs={"layer": "06-WALL"})      # its own wall layer: a wall
    msp.add_blockref("CCSD", (0, 0), dxfattribs={"layer": "06-WALL"})
    msp.add_blockref("BORDER-A1", (0, 0), dxfattribs={"layer": "A-WALL"})
    msp.add_blockref("X-REF_ DIM_TEXT", (10, 40), dxfattribs={"layer": "06-WALL"})
    msp.add_line((0, 10), (120, 10), dxfattribs={"layer": "06-WALL"})
    msp.add_line((0, 10.2), (120, 10.2), dxfattribs={"layer": "06-WALL"})
    return save(doc, "f8_title_frame.dxf")


def f9_mline():
    doc, msp = new()
    layers(doc, "06-WALL", "A-FURN", "06-WALL-FROZEN")
    doc.layers.get("06-WALL-FROZEN").freeze()
    for y in (0, 5, 10):
        msp.add_mline([(0, y), (10, y)], dxfattribs={"layer": "06-WALL"})
    msp.add_mline([(0, 20), (10, 20)], dxfattribs={"layer": "A-FURN"})
    msp.add_mline([(0, 30), (10, 30)], dxfattribs={"layer": "06-WALL-FROZEN"})
    msp.add_line((0, -5), (5, -5), dxfattribs={"layer": "06-WALL"})
    return save(doc, "f9_mline.dxf")


def f10_meshes():
    doc, msp = new()
    layers(doc, "06-WALL")
    face = msp.add_polyface(dxfattribs={"layer": "06-WALL"})
    face.append_face([(0, 0, 0), (10, 0, 0), (10, 0, 3), (0, 0, 3)])
    face.append_face([(0, 0.2, 0), (10, 0.2, 0), (10, 0.2, 3), (0, 0.2, 3)])
    grid = msp.add_polymesh((3, 3), dxfattribs={"layer": "06-WALL"})
    for m in range(3):
        for n in range(3):
            grid.set_mesh_vertex((m, n), (20 + 5 * m, 5 * n, 0))
    msp.add_line((0, 20), (10, 20), dxfattribs={"layer": "06-WALL"})
    msp.add_line((0, 20.2), (10, 20.2), dxfattribs={"layer": "06-WALL"})
    msp.add_arc((0, 40), 5, 0, 90, dxfattribs={"layer": "06-WALL"})
    return save(doc, "f10_meshes.dxf")


def f11_bounds_hidden():
    doc, msp = new()
    layers(doc, "06-WALL", "A-WALL-FROZEN")
    doc.layers.get("A-WALL-FROZEN").freeze()
    for y in (0, 0.2, 10):
        msp.add_line((0, y), (100, y), dxfattribs={"layer": "06-WALL"})            # 300 m shown
    msp.add_line((0, 20), (50, 20), dxfattribs={"layer": "A-WALL-FROZEN"})        # 50 m frozen
    msp.add_line((0, 30), (50, 30), dxfattribs={"layer": "06-WALL", "invisible": 1})   # 50 m invisible
    bx = doc.blocks.new("BX", base_point=(0, 0))
    bx.add_line((0, 0), (100, 0), dxfattribs={"layer": "0"})
    msp.add_blockref("BX", (0, 40), dxfattribs={"layer": "A-WALL-FROZEN"})        # 100 m, inherits frozen
    return save(doc, "f11_bounds_hidden.dxf")


UNITS = (("u1_metres.dxf", 6, 1.0), ("u2_millimetres.dxf", 4, 1000.0), ("u3_inches.dxf", 1, 1.0 / 0.0254),
         ("u4_unitless.dxf", 0, 1.0))


def _units(name: str, insunits: int, k: float):
    """301.6 m of double wall, a 0.25 m stub, a 0.4 m column; k drawing units a metre."""
    doc, msp = new(insunits)
    layers(doc, "06-WALL", "08-COLUMN")

    def p(x, y):
        return (round(x * k, 6), round(y * k, 6))

    for o in (0.0, 0.2):
        corners = [p(-o, -o), p(50 + o, -o), p(50 + o, 25 + o), p(-o, 25 + o)]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            msp.add_line(a, b, dxfattribs={"layer": "06-WALL"})
    msp.add_line(p(60, 0), p(60.25, 0), dxfattribs={"layer": "06-WALL"})
    msp.add_lwpolyline([p(10, 10), p(10.4, 10), p(10.4, 10.4), p(10, 10.4)], close=True,
                       dxfattribs={"layer": "08-COLUMN"})
    return save(doc, name)


def u_units():
    return [_units(*spec) for spec in UNITS]


ROTATED = {"twist": 30.0, "center": (210.0, 148.5), "size": (380.0, 260.0), "view_center": (50.0, 30.0),
           "view_height": 100.0}
ROTATED_TEXTS = (("STORE ROOM", -40, -25), ("PUMP ROOM", 0, -30), ("ELEC ROOM", 45, -20), ("LOBBY HALL", -45, 10),
                 ("CORRIDOR", 5, 0), ("MEETING", 50, 15), ("OFFICE 01", -20, 30), ("PANTRY", 30, 32))


def f12_rotated_view():
    """Room names at points of the view (DCS, around its centre), placed in the
    model turned back by the twist: through the viewport they print where
    the view has them."""
    doc, msp = new()
    layers(doc, "A-ANNO")
    t = math.radians(ROTATED["twist"])
    cx, cy = ROTATED["view_center"]
    for text, dx, dy in ROTATED_TEXTS:
        u, v = cx + dx, cy + dy
        x, y = math.cos(t) * u + math.sin(t) * v, -math.sin(t) * u + math.cos(t) * v      # R(-twist)
        msp.add_text(text, height=1.0, dxfattribs={"layer": "A-ANNO", "insert": (round(x, 6), round(y, 6))})
    sheet = doc.layouts.new("FA-201")
    vp = sheet.add_viewport(center=ROTATED["center"], size=ROTATED["size"], view_center_point=ROTATED["view_center"],
                            view_height=ROTATED["view_height"])
    vp.dxf.view_twist_angle = ROTATED["twist"]
    return save(doc, "f12_rotated_view.dxf")


ALL = (f1_simple, f2_nested, f3_states, f4_invisible, f5_viewport, f6_xref, f7_denylist, f8_title_frame, f9_mline,
       f10_meshes, f11_bounds_hidden, u_units, f12_rotated_view)


def main() -> list[Path]:
    ezdxf.options.write_fixed_meta_data_for_testing = True
    try:
        out: list[Path] = []
        for make in ALL:
            made = make()
            out.extend(made if isinstance(made, list) else [made])
        return out
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing = False


if __name__ == "__main__":
    for p in main():
        print(p.name)
