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
"""
from __future__ import annotations

from pathlib import Path

import ezdxf

HERE = Path(__file__).resolve().parent


def new():
    doc = ezdxf.new("R2018", setup=False)
    doc.header["$INSUNITS"] = 6
    return doc, doc.modelspace()


def layers(doc, *names):
    for n in names:
        if n not in doc.layers:
            doc.layers.add(n)


def save(doc, name: str) -> Path:
    path = HERE / name
    doc.saveas(path)
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


ALL = (f1_simple, f2_nested, f3_states, f4_invisible, f5_viewport, f6_xref, f7_denylist)


def main() -> list[Path]:
    ezdxf.options.write_fixed_meta_data_for_testing = True
    try:
        return [make() for make in ALL]
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing = False


if __name__ == "__main__":
    for p in main():
        print(p.name)
