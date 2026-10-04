"""Stage 1 of the interface schedule: what one IFC drawing shows, and where.

Every word in the drawing's model space is read -- TEXT and MTEXT, block
attributes, and the words inside blocks at any depth (a Revit export keeps
its tags in nested blocks; a bound architectural xref keeps its room names
there) -- and each word the interface matrix has a row for is placed on the
sheet whose viewport shows it (app.ifc.dxf.sheets, as the fire alarm BOQ
places its devices). The sheet's title gives the floor.

Nothing here counts signals or decides what is scheduled: that is
app.interfaces.service, against the matrix. This says only: this label,
this equipment, on this sheet, at this point, in this drawing.
"""
from __future__ import annotations

import ezdxf

from app.ifc.dxf import geometry as G
from app.ifc.dxf import sheets as S
from app.interfaces import detect
from app.interfaces import geometry
from app.interfaces.matrix import ACS, ARCH, FF, GB, rules_for

# Model space read as one drawing when no sheet has a viewport on it (a
# drawing issued as model space only): its floor comes from the file name.
WHOLE = "(whole drawing)"
SCAN_VERSION = "5"     # 2: dampers by their code (MD, MSD, SD ...); 3: the fire fighting drawings' pump rooms;
                       # 4: each label's physical symbol, and gate barriers by their fire alarm connection points;
                       # 5: each sheet's viewport windows (W-4: a floor is aligned only where they are the same)
_MAX_DEPTH = 8
_UNITS = {1: "in", 2: "ft", 4: "mm", 5: "cm", 6: "m"}
_METRE = {"mm": 1000.0, "cm": 100.0, "m": 1.0, "in": 39.37, "ft": 3.281}
GATE_CONTEXT_M = 5.0      # a connection note on an ACS / architecture drawing counts only this near a barrier


def _texts(doc) -> list[tuple[str, float, float]]:
    """(text, x, y) of every word in model space, blocks opened: a block's
    words are read once and placed through each insert's transform."""
    cache: dict[str, list[tuple[str, float, float]]] = {}

    def in_block(name: str, depth: int) -> list[tuple[str, float, float]]:
        if name in cache:
            return cache[name]
        out: list[tuple[str, float, float]] = []
        cache[name] = out          # a block that inserts itself is read once
        block = doc.blocks.get(name)
        if block is None or depth > _MAX_DEPTH:
            return out
        for e in block:
            _collect(e, out, depth)
        return out

    def _collect(e, out: list, depth: int) -> None:
        kind = e.dxftype()
        if kind in ("TEXT", "MTEXT"):
            try:
                x, y = S._position(e)
                out.append((G.plain_text(e), x, y))
            except Exception:  # noqa: BLE001 -- a malformed text is skipped, not the drawing
                pass
        elif kind == "INSERT":
            for a in getattr(e, "attribs", []):
                try:
                    out.append((str(a.dxf.get("text", "")), float(a.dxf.insert.x), float(a.dxf.insert.y)))
                except Exception:  # noqa: BLE001
                    pass
            try:
                m = e.matrix44()
                for text, x, y in in_block(e.dxf.name, depth + 1):
                    v = m.transform((x, y, 0))
                    out.append((text, float(v.x), float(v.y)))
            except Exception:  # noqa: BLE001
                pass

    found: list[tuple[str, float, float]] = []
    for e in doc.modelspace():
        _collect(e, found, 0)
    return [(t, x, y) for t, x, y in found if t and t.strip()]


def read(path: str, discipline: str, check=None) -> dict:
    """The drawing's sheets, and every interface item its words name.

    `items`: {key, kind, confidence, tag, detail, text, sheet, x, y}.
    For the architecture also `lifts` (each lift label, where) and
    `machine_rooms`; for fire fighting `pump_rooms`."""
    doc = ezdxf.readfile(path)
    if check:
        check()
    sheets = S.read_sheets(doc)
    wanted = rules_for(discipline)
    items: list[dict] = []
    lifts: list[dict] = []
    machine_rooms: list[dict] = []
    pump_rooms: list[dict] = []
    seen: set[tuple] = set()
    texts = _texts(doc)
    for i, (text, x, y) in enumerate(texts):
        if check and i % 5000 == 0:
            check()
        sheet = S.sheet_for(sheets, x, y) if sheets else WHOLE
        for d in detect.detect(text, wanted):
            # the same words drawn twice at one spot (a block inserted twice over itself) are one
            key = (d.key, d.tag, sheet, round(x, 1), round(y, 1))
            if key in seen:
                continue
            seen.add(key)
            items.append({"key": d.key, "kind": d.kind, "confidence": d.confidence, "tag": d.tag, "detail": d.detail,
                          "text": detect.normalize(text)[:160], "sheet": sheet, "x": round(x, 2), "y": round(y, 2)})
        if discipline == ARCH:
            lift = detect.lift_label(text)
            if lift:
                lifts.append({"label": lift, "sheet": sheet, "x": round(x, 2), "y": round(y, 2)})
            elif detect.is_machine_room(text):
                machine_rooms.append({"text": detect.normalize(text), "sheet": sheet, "x": round(x, 2), "y": round(y, 2)})
        if discipline == FF and detect.is_pump_room(text):
            pump_rooms.append({"text": detect.normalize(text), "sheet": sheet, "x": round(x, 2), "y": round(y, 2)})
    units = _UNITS.get(int(doc.header.get("$INSUNITS", 0) or 0), "unitless")
    metre = _METRE.get(units, 1.0)
    # the physical symbol beside each label: the label is where the words are, the symbol where it stands
    labels = [it for it in items if it["kind"] == "label"]
    symbols: list = []
    if labels:
        symbols = geometry.symbols_near(doc, [(it["x"], it["y"]) for it in labels], metre)
        for it, a in zip(labels, geometry.associate([(it["text"], it["x"], it["y"]) for it in labels], symbols, metre)):
            it["association"] = a
        if check:
            check()
    # gate barriers: one per fire alarm connection point the drawing shows, with its lane
    if "gate_barrier" in wanted and discipline in (GB, ACS, ARCH):
        context = [(it["x"], it["y"]) for it in items if it["key"] == "gate_barrier"
                   and not geometry.NOTE_ONLY.search(it["text"])]
        for e in doc.modelspace().query("LWPOLYLINE"):
            if "LOOP" in (e.dxf.layer or "").upper():
                pts = [(px, py) for px, py, *_ in e.get_points("xy")]
                if pts:
                    context.append((sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)))
        for pt in geometry.gate_points(texts, geometry.leaders(doc), metre):
            if discipline != GB and not any(((cx - pt["x"]) ** 2 + (cy - pt["y"]) ** 2) ** 0.5 <= GATE_CONTEXT_M * metre
                                            for cx, cy in context):
                continue
            sheet = S.sheet_for(sheets, pt["x"], pt["y"]) if sheets else WHOLE
            anchor = pt["equipment_anchor"]
            items.append({"key": "gate_barrier", "kind": "instance", "confidence": detect.HIGH if pt["settled"] else detect.MEDIUM,
                          "tag": None, "detail": "", "text": detect.normalize(pt["text"])[:160], "sheet": sheet,
                          "x": round(pt["x"], 2), "y": round(pt["y"], 2), "role": pt["role"], "settled": pt["settled"],
                          "why": pt["why"], "role_d": pt["role_d"], "margin": pt["margin"],
                          "equipment_anchor": [round(anchor[0], 3), round(anchor[1], 3)] if anchor else None})
    return {
        "scan_version": SCAN_VERSION,
        "units": units,
        "symbols": len(symbols),
        "landmarks": geometry.landmarks(texts),
        "sheets": [{**s.to_dict(), "height": max((w.h for w in s.windows), default=0.0),
                    "windows": [[round(v, 4) for v in (w.cx, w.cy, w.w, w.h, w.twist, w.tx, w.ty)] for w in s.windows]}
                   for s in sheets],
        "texts": len(texts),
        "items": items,
        "lifts": lifts,
        "machine_rooms": machine_rooms,
        "pump_rooms": pump_rooms,
    }
