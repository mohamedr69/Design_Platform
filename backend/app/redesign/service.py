"""Drawings Redesign: after the review, the IFC drawing copied with the
accepted changes made on it (platform owner, 2 October 2026).

  plan     each accepted ADD / REMOVE / REPLACE of the review, placed: the
           model (Claude Opus 5.5, as the review) is shown the plotted plan
           around it with the nearby symbols numbered and picks the point,
           the symbol to erase and the drawing's own symbol to insert;
  adjust   the engineer approves, moves (a click on the picture), picks
           another symbol, or skips each one;
  apply    AutoCAD makes the changes on a copy of the DWG the review
           plotted (app.redesign.cad), filed in the project folder.

The Fire Alarm Interface Schedule's modules come in too, each an ADD beside
the equipment it serves, for the engineer to approve (see "the interface
schedule's modules" below).

Where things are: the review's plot is tied to the drawing per sheet
(app.review.geometry: page point <-> model point, to a metre or so); the
symbols are where the IFC reading found them (app.ifc.resolve: handle,
block, model point, scale), so an erased or replaced symbol is exact, and
only an added one carries the plot's error -- said on the change.
"""
from __future__ import annotations

import functools
import hashlib
import io
import json
import logging
import math
import os
import re
import zlib
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.ai.provider import ImagePart, TextPart, get_provider
from app.compliance import assist
from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.database import SessionLocal
from app.ifc import storage
from app.models import Project, ProjectDrawingReview, ProjectIfcDrawing, ProjectRedesign
from app.redesign import ai as A
from app.redesign import cad
from app.review import geometry as G
from app.review import pages as P

log = logging.getLogger(__name__)
KIND_PLAN, KIND_APPLY = "fa_redesign_plan", "fa_redesign_apply"
FOLDER = "03- Drawings/Redesign"
RADIUS_M = 8.0                 # the piece of plan the model is shown: this far around the change
MAX_CANDIDATES = 15
ACTIONS = ("add", "remove", "replace")
# The plot's own error, past which an added symbol's place is for the draftsman to confirm.
CONFIRM_ABOVE_M = 1.0


class RedesignError(RuntimeError):
    pass


def state(db: Session, project: Project, drawing_id: int) -> ProjectRedesign:
    row = (db.query(ProjectRedesign)
           .filter(ProjectRedesign.project_id == project.id, ProjectRedesign.drawing_id == drawing_id).first())
    if row is None:
        row = ProjectRedesign(project_id=project.id, drawing_id=drawing_id, status="none", changes=[], symbols=[])
        db.add(row)
        db.flush()
    return row


def _review(db: Session, project: Project, drawing: ProjectIfcDrawing) -> tuple[ProjectDrawingReview, dict]:
    from app.review import service as review

    row = (db.query(ProjectDrawingReview)
           .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing.id).first())
    if row is None or not row.sheets:
        raise RedesignError("Review the drawing first (Drawings Review): the redesign makes the changes accepted there.")
    if row.status != "done":
        raise RedesignError("The drawing's review has not finished: let it finish on Drawings Review first.")
    view = review.build(db, project, drawing)       # ties the plot to the drawing, once
    db.commit()
    return row, view


# --- the drawing's symbols ---------------------------------------------------------


def _occurrences(resolved: dict) -> list[dict]:
    out = []
    for group in resolved.get("groups") or []:
        dt = group.get("device_type") or {}
        for o in group.get("occurrences") or []:
            out.append({"handle": o["handle"], "block": o["block_name"], "sheet": o.get("sheet") or "",
                        "x": float(o.get("cx", o["x"])), "y": float(o.get("cy", o["y"])),
                        "ix": float(o["x"]), "iy": float(o["y"]),
                        "rotation": float(o.get("rotation") or 0), "scale": float(o.get("scale") or 1),
                        "layer": o.get("layer") or "", "type_id": dt.get("id"), "name": dt.get("name") or group.get("label") or o["block_name"],
                        "code": dt.get("code") or ""})
    return out


def _device(o: dict) -> bool:
    """A symbol worth numbering for the model: a device the reading knows, or
    a short label of one it does not ("E", "EX") -- not an xref'd lift, a
    stair's step numbers or a title block."""
    if o["type_id"]:
        return True
    name = (o["name"] or "").strip()
    # a parking bay's or a stair's number is not a device
    return 0 < len(name) <= 8 and "$" not in o["block"] and "+" not in name and not name.isdigit()


def _rotate(x: float, y: float, degrees: float) -> tuple[float, float]:
    r = math.radians(degrees)
    return x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)


def _drawn_centre(copies: list[dict]) -> list[float]:
    """Where a block's graphics sit from its insertion point, in the block's
    own units: the drawing's blocks are not all drawn on their base point --
    EP-30880's sounder strobe sits ~740 m from it -- so a symbol inserted
    at the spot would land far away. Learned from the copies the drawing
    has (each one's visible centre against its insertion point, its
    rotation and scale undone)."""
    xs, ys = [], []
    for o in copies:
        scale = o["scale"] or 1.0
        x, y = _rotate(o["x"] - o["ix"], o["y"] - o["iy"], -o["rotation"])
        xs.append(x / scale)
        ys.append(y / scale)
    return [statistics.median(xs), statistics.median(ys)] if xs else [0.0, 0.0]


_DIRECTIONS = {"up": 90.0, "left": 180.0, "down": 270.0, "right": 0.0}


def _facing(centre: list[float], info: dict | None) -> float | None:
    """The way a block faces at rotation 0, as an angle (0 right, 90 up):
    the side its sound-wave strokes are on (EP-30880's sounder flasher faces
    up); else, a wall device being drawn with its back on its base point,
    from that point to its drawn centre (its wall mounted sounder faces
    down). None when neither says."""
    if not info:
        return None
    if info.get("strokes") is not None:
        angle = info["strokes"]
        return min((0.0, 90.0, 180.0, 270.0, 360.0), key=lambda a: abs(a - angle % 360)) % 360
    size = info["size"]
    off = math.hypot(*centre)
    if not size or off < 0.05 * size or off > size:
        return None
    angle = math.degrees(math.atan2(centre[1], centre[0]))
    return min((0.0, 90.0, 180.0, 270.0, 360.0), key=lambda a: abs(a - angle % 360)) % 360


def _depth(facing: float | None, info: dict | None) -> float | None:
    """Half the block's depth from its back to its front, in its own units:
    how far its centre stands off the wall it is fixed to."""
    if facing is None or not info:
        return None
    x0, y0, x1, y1 = info["ext"]
    return ((y1 - y0) if facing in (90.0, 270.0) else (x1 - x0)) / 2


_VECTORS = {"up": (0.0, 1.0), "down": (0.0, -1.0), "left": (-1.0, 0.0), "right": (1.0, 0.0)}
_WALLS: dict[str, object] = {}


def _walls(project: Project, drawing: ProjectIfcDrawing, sha: str | None, *, build: bool = False, check=None):
    """The drawing's walls (app.redesign.walls): read from the saved index,
    built from the drawing when `build` (in a job -- it takes a minute)."""
    from app.redesign import walls as W

    path = W.path_for(project, drawing, sha)
    key = str(path)
    if key in _WALLS:
        return _WALLS[key]
    found = W.load(path)
    if found is None and build and storage.dxf_path(drawing).is_file():
        found = W.build(storage.dxf_path(drawing), path, check=check)
    if found is not None:
        _WALLS[key] = found
    return found


def _rotation(symbol: dict | None, answer: dict) -> float:
    """The rotation that turns the symbol to the way the model said the
    device faces; the model's (or engineer's) rotation when it said none,
    or the symbol's facing is not known."""
    facing = answer.get("facing")
    if facing and symbol is not None and symbol.get("facing") is not None and answer.get("rotation_set") is None:
        return (_DIRECTIONS[facing] - symbol["facing"]) % 360
    return float(answer.get("rotation") or 0) % 360


# What the platform owner draws a device as when the drawing has the symbol
# (2 October 2026): a sounder strobe / sounder flasher is the strobe's symbol
# (the weatherproof one for a weatherproof device), a plain sounder the wall
# mounted sounder.
PREFERRED = [
    (re.compile(r"STROBE|FLASHER", re.I), re.compile(r"STROBE|FLASHER", re.I)),
    (re.compile(r"SOUNDER", re.I), re.compile(r"WALL\s*MOUNTED\s*SOUNDER", re.I)),
    (re.compile(r"DIRECTIONAL", re.I), re.compile(r"^Directional Emergency Sign", re.I)),
    (re.compile(r"EXIT", re.I), re.compile(r"^Exit Sign", re.I)),
    (re.compile(r"EMERGENCY\s*LIGHT|\bEM\s*LIGHT", re.I), re.compile(r"^Emergency Light", re.I)),
]
WEATHER = re.compile(r"WEATHER|\bWP\b|\bIP[-\s]?(RATED|\d)", re.I)


def _weather(text: str | None) -> bool:
    return bool(WEATHER.search(text or ""))


def _preferred(device: str, symbols: list[dict]) -> dict | None:
    for wanted, name in PREFERRED:
        if wanted.search(device or ""):
            found = [x for x in symbols if name.search(x["name"])]
            if found:
                weather = _weather(device)
                return max(found, key=lambda x: (_weather(x["name"]) == weather, x["count"]))
    return None


# The emergency lighting's symbols are not device types of the fire alarm
# reading: known here by their block and layer (EP-30880: "E" on -EMERGENCY,
# "EXT WP" on Ext, "EXT-2D" on A-DIRECTIONAL EMER SIGN).
def _els_name(o: dict) -> str | None:
    block, layer = o["block"] or "", o["layer"] or ""
    if "|" in block or "$" in block or block.startswith("*"):
        return None
    both = f"{block} {layer}"
    if re.search(r"DIRECTIONAL", both, re.I):
        name = "Directional Emergency Sign"
    elif re.search(r"\bEXIT\b|^EXT\b|\bEXT\b", both, re.I):
        name = "Exit Sign"
    elif re.search(r"EMERG|(^|[-\s])EM($|[-\s])", layer, re.I) or block.upper() in ("E", "EM"):
        name = "Emergency Light"
    else:
        return None
    return name + " WP" if _weather(block) else name


def _measured(occurrences: list[dict]) -> set[str]:
    return {o["block"] for o in occurrences if o["type_id"] or _els_name(o)}


# A weatherproof emergency light where the drawing has none (platform owner,
# 2 October 2026): the drawing's emergency light with small letters "WP"
# under it, as a new block the drawing then keeps.
WP_TEXT, WP_HEIGHT, WP_GAP = "WP", 0.3, 0.1          # the letters' height and gap, of the symbol's size


def _weatherproof_variant(symbol: dict) -> dict | None:
    if not symbol.get("ext") or _weather(symbol["name"]) or not symbol["name"].startswith("Emergency Light"):
        return None
    x0, y0, x1, y1 = symbol["ext"]
    size = max(x1 - x0, y1 - y0)
    h, gap = WP_HEIGHT * size, WP_GAP * size
    ext = [x0, y0 - gap - h, x1, y1]
    return {**symbol, "name": symbol["name"] + " WP", "block": f"{symbol['block']} WP", "ext": ext,
            "size": max(ext[2] - ext[0], ext[3] - ext[1]),
            "make": {"from": symbol["block"], "text": WP_TEXT, "height": round(h, 6),
                     "at": [round((x0 + x1) / 2, 6), round(y0 - gap - h, 6)]}}


def _symbols(occurrences: list[dict], blocks: set[str] | None = None, sizes: dict[str, dict] | None = None) -> list[dict]:
    """The device types the drawing draws, each with the block it uses most,
    the layer it keeps that block on, and its scale (overall, and per sheet)
    -- only blocks the drawing defines, so each can be inserted."""
    by_type: dict[int, list[dict]] = defaultdict(list)
    names: dict[int, str] = {}
    for o in occurrences:
        if "|" in o["block"] or (blocks is not None and o["block"] not in blocks):
            continue
        if o["type_id"]:
            by_type[o["type_id"]].append(o)
        elif (els := _els_name(o)) is not None:
            # an emergency lighting symbol: an id of its own, the same every time
            key = 900000 + zlib.crc32(els.encode()) % 90000
            by_type[key].append(o)
            names[key] = els
    out = []
    for type_id, items in by_type.items():
        # an emergency light reads "E": kept upright, never turned to a wall
        upright = names.get(type_id, "").startswith("Emergency Light")
        block = Counter(o["block"] for o in items).most_common(1)[0][0]
        mine = [o for o in items if o["block"] == block]
        scales: dict[str, list[float]] = defaultdict(list)
        for o in mine:
            scales[o["sheet"]].append(o["scale"])
        out.append({"id": type_id, "name": names.get(type_id) or mine[0]["name"],
                    "code": "" if type_id in names else mine[0]["code"], "block": block,
                    "layer": Counter(o["layer"] for o in mine).most_common(1)[0][0],
                    "scale": statistics.median(o["scale"] for o in mine),
                    "scales": {sheet: statistics.median(v) for sheet, v in scales.items()},
                    "center": _drawn_centre(mine),
                    "facing": None if upright else _facing(_drawn_centre(mine), (sizes or {}).get(block)),
                    "depth": None if upright else _depth(_facing(_drawn_centre(mine), (sizes or {}).get(block)),
                                                         (sizes or {}).get(block)),
                    "size": ((sizes or {}).get(block) or {}).get("size"),
                    "ext": ((sizes or {}).get(block) or {}).get("ext"),
                    "count": len(items)})
    return sorted(out, key=lambda s: (-s["count"], s["name"]))


def _top_level(drawing: ProjectIfcDrawing, measure: set[str] | None = None
               ) -> tuple[set[str] | None, set[str] | None, dict[str, dict]]:
    """(the handles of the symbols drawn directly in model space -- only those
    can be erased: erasing one inside a block takes it out of every copy --,
    the blocks the drawing defines, the size of each block in `measure`,
    in its own units)."""
    import ezdxf
    from ezdxf import bbox

    path = storage.dxf_path(drawing)
    if not path.is_file():
        return None, None, {}
    doc = ezdxf.readfile(path)
    sizes = {}
    for name in measure or ():
        block = doc.blocks.get(name)
        if block is None:
            continue
        try:
            ext = bbox.extents(block, fast=True)
        except Exception:  # noqa: BLE001 -- a block that cannot be measured is not turned
            continue
        if not ext.has_data:
            continue
        size = max(ext.size.x, ext.size.y)
        # the short strokes a sounder's sound waves are drawn with: the side
        # they are on is the side it faces
        strokes = []
        for e in block:
            try:
                part = bbox.extents([e], fast=True)
            except Exception:  # noqa: BLE001
                continue
            if part.has_data and 0 < max(part.size.x, part.size.y) < 0.25 * size:
                strokes.append(part.center)
        stroke_angle = None
        if len(strokes) >= 3:
            sx = sum(p.x for p in strokes) / len(strokes) - ext.center.x
            sy = sum(p.y for p in strokes) / len(strokes) - ext.center.y
            if math.hypot(sx, sy) > 0.1 * size:
                stroke_angle = math.degrees(math.atan2(sy, sx))
        sizes[name] = {"size": size, "ext": [ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y],
                       "strokes": stroke_angle}
    return ({e.dxf.handle for e in doc.modelspace().query("INSERT")},
            {b.name for b in doc.blocks if not b.name.startswith("*")}, sizes)


# --- geometry -------------------------------------------------------------------------


def _page(g: dict, x: float, y: float) -> list[float]:
    return [round((x - g["bx"]) / g["a"], 2), round((g["by"] - y) / g["a"], 2)]


def _model(g: dict, px: float, py: float) -> list[float]:
    x, y = G.to_model(g, px, py)
    return [round(x, 4), round(y, 4)]


def _box(g: dict, at: list[float], plan: list[float]) -> list[float]:
    half = RADIUS_M / g["a"]
    x0, y0 = max(plan[0], at[0] - half), max(plan[1], at[1] - half)
    x1, y1 = min(plan[2], at[0] + half), min(plan[3], at[1] + half)
    return [round(v, 1) for v in (x0, y0, x1, y1)]


# --- the interface schedule's modules -------------------------------------------------------
# Every module the Fire Alarm Interface Schedule calls for (platform owner, 2 October
# 2026), put on the plan beside the equipment it serves for the engineer to approve.
# The trades' drawings share the fire alarm drawing's coordinates (EP-30880: the
# fire fighting drawing's alarm check valve is in this one's pump room), so where
# the equipment is labelled on theirs is the spot on this one. The modules are the
# platform owner's own blocks (app/redesign/library, out of the BBY006 basement-4
# shop drawing): CR, CT1, CT2, as big on paper as there, with "FOR <tag>" beside
# each, as there. A module is mounted on a surface back box on the wall: on the
# nearest wall face around its equipment, turned with its back to it, the
# modules of one item side by side along that wall (the coordination slides
# them), its note running from it into the room. Drawn only once approved; the
# loop addresses are the draftsman's.
LIBRARY = Path(__file__).parent / "library"
INTERFACE = "interface"
MODULE_NAMES = {"CR": "Control Relay Module", "CT1": "Single Input Monitor Module", "CT2": "Dual Input Monitor Module"}
MODULE_ID = 800000
MODULE_WALL_M = 3.0          # how far from its equipment's label a module looks for the wall it goes on
_PT_PER_MM = 72 / 25.4


@functools.lru_cache(maxsize=1)
def _library() -> dict:
    return json.loads((LIBRARY / "modules.json").read_text(encoding="utf-8"))


def _paper_scale(sheet: dict) -> float | None:
    """The scale a library block (the sample's, 1:100 in mm) is inserted at
    so it is as big on this sheet's paper as on the sample's."""
    a = (sheet.get("geometry") or {}).get("a")          # drawing units per point of the plot
    return _PT_PER_MM * a / _library()["sample_scale"] if a else None


def _note_height(sheet: dict) -> float | None:
    """The "FOR ..." note's height on this sheet: the sample's, on paper."""
    a = (sheet.get("geometry") or {}).get("a")
    return _library()["note_height"] / _library()["sample_scale"] * _PT_PER_MM * a if a else None


def _module_symbols(sheets: dict[int, dict], symbols: list[dict]) -> list[dict]:
    """The library's modules as symbols of this drawing, on the layer its own
    modules are kept on."""
    own = next((x for x in symbols if x["id"] < MODULE_ID and re.search(r"MODULE", x["name"], re.I)), None)
    layer = own["layer"] if own else "0"
    scales = {sh["name"]: k for sh in sheets.values() if (k := _paper_scale(sh))}
    out = []
    for i, (code, m) in enumerate(_library()["modules"].items(), 1):
        x0, y0, x1, y1 = m["ext"]
        out.append({"id": MODULE_ID + i, "name": f"{MODULE_NAMES.get(code, code)} ({code})", "code": code,
                    "block": m["block"], "layer": layer,
                    "scale": statistics.median(scales.values()) if scales else 1.0, "scales": scales,
                    # drawn on its base point with its back at the bottom: it faces up
                    "center": [(x0 + x1) / 2, (y0 + y1) / 2], "facing": 90.0, "depth": (y1 - y0) / 2,
                    "size": max(x1 - x0, y1 - y0), "ext": m["ext"], "count": 0,
                    "library": (LIBRARY / f"{code}.dwg").resolve().as_posix()})
    return out


def _all_symbols(occurrences: list[dict], blocks, sizes, sheets: dict[int, dict]) -> list[dict]:
    symbols = _symbols(occurrences, blocks, sizes)
    return symbols + _module_symbols(sheets, symbols)


def _for(row: dict, no_tag: str) -> str:
    """What the module is for, as the sample writes it: the tag, else what the
    trade's drawing calls it ("ZCV", "MD"), else the equipment."""
    if row.get("tag") and row["tag"] != no_tag:
        return row["tag"]
    drawn = re.search(r'drawn: "([^"]+)"', row.get("description") or "")
    text = re.sub(r"^[^A-Za-z]+", "", drawn.group(1)).strip() if drawn else ""
    # as the sample says it: "FOR DIESEL PUMP", not "FOR DIESEL FIRE PUMP"
    return re.sub(r"\bFIRE\s+PUMP", "PUMP", (text if 0 < len(text) <= 24 else row["equipment"]).upper())


def _nearest_wall(walls, x: float, y: float, reach: float = MODULE_WALL_M) -> tuple[str, list[float]] | None:
    """(the way a device on it faces, the point on its face) of the nearest
    wall face around (x, y), within `reach`: a face drawn double -- a wall's,
    past the single lines of a pump set's outline or a bay -- where there is
    one, else the nearest face; None when there is none."""
    double, single = None, None
    for name, vector in _VECTORS.items():
        faces = walls.faces_behind(x, y, vector, back=reach, front=0.05)
        wall = next((q for q in faces if walls.thick(*q, vector)), None)
        if wall is not None and (double is None or math.dist((x, y), wall) < double[0]):
            double = (math.dist((x, y), wall), name, list(wall))
        if faces and (single is None or math.dist((x, y), faces[0]) < single[0]):
            single = (math.dist((x, y), faces[0]), name, list(faces[0]))
    best = double or single
    return (best[1], best[2]) if best else None


def _walls_around(walls, x: float, y: float, reach: float = MODULE_WALL_M + 1.0) -> list[tuple[str, list[float]]]:
    """Every wall face around (x, y) within `reach`, one a way, nearest first:
    (the way a device on it faces, the point on its face) -- a face drawn
    double where the way has one."""
    out = []
    for name, vector in _VECTORS.items():
        faces = walls.faces_behind(x, y, vector, back=reach, front=0.05)
        face = next((q for q in faces if walls.thick(*q, vector)), faces[0] if faces else None)
        if face is not None:
            out.append((math.dist((x, y), face), name, list(face)))
    return [(name, face) for _d, name, face in sorted(out)]


def _place_module(change: dict, sheet: dict, symbols: list[dict], answer: dict, walls=None) -> None:
    """A module placed: on the nearest wall face around its point (the
    equipment's label, or where the engineer clicked), turned with its back
    to it; where no wall is near, at the point as it is."""
    if walls is not None and answer.get("x") is not None and not answer.get("facing") and "box" in change:
        box, g = change["box"], sheet["geometry"]
        x, y = _model(g, box[0] + answer["x"] * (box[2] - box[0]), box[1] + answer["y"] * (box[3] - box[1]))
        wall = _nearest_wall(walls, x, y)
        if wall is not None:
            facing, face = wall
            v = _VECTORS[facing]
            spot = _page(g, face[0] + v[0] * 0.3, face[1] + v[1] * 0.3)       # in front of it: placed against it
            answer = {**answer, "facing": facing, "x": (spot[0] - box[0]) / (box[2] - box[0]),
                      "y": (spot[1] - box[1]) / (box[3] - box[1])}
    change["ai"] = answer
    _place(change, sheet, symbols, answer, walls if answer.get("facing") else None)


def _interface_changes(db: Session, project: Project, sheets: dict[int, dict], occurrences: list[dict],
                       top: set[str] | None, symbols: list[dict], walls=None) -> list[dict]:
    """A change per module of the interface schedule: placed beside its
    equipment where the drawing has the plan it is on; a note to draw it by
    hand where not."""
    from app.interfaces import service as I

    built = I.build(db, project)
    floors = I.Floors(db, project)
    plans = []
    for sh in sheets.values():
        if "a" in (sh.get("geometry") or {}) and sh.get("kind", "plan") == "plan":
            keys = set(floors.of_title(sh.get("title") or "")) or set(floors.of_title(sh.get("floor") or ""))
            plans.append((sh, keys))
    modules = {x["code"]: x for x in symbols if x["id"] > MODULE_ID and x.get("library")}
    out: dict[str, dict] = {}
    columns: dict[tuple, list[dict]] = defaultdict(list)
    copies: Counter = Counter()          # the same kind at one spot on one floor: two pumps, two modules
    for r in built["rows"]:
        wanted = [(code, n) for code, q in (r.get("modules") or {}).items() if code in modules for n in range(q or 0)]
        if not wanted:
            continue
        who = _for(r, I.NO_TAG)
        anchor, sheet, at, why = r.get("anchor"), None, None, None
        for sh, keys in plans if anchor else ():
            px, py = _page(sh["geometry"], *anchor)
            if sh["plan"][0] <= px <= sh["plan"][2] and sh["plan"][1] <= py <= sh["plan"][3]:
                if keys and r["floor_key"] not in keys:
                    # the trade's typical plan covers this floor, this drawing's plan of it is another one
                    why = (f"{r['source']} shows it on a plan that covers {r['floor']}, but this drawing's plan there "
                           f"is {sh.get('title') or sh['name']} (other floors): draw it by hand on {r['floor']}'s plan.")
                else:
                    sheet, at = sh, [px, py]
                break
        if sheet is None:
            # nowhere on this drawing: listed, for the draftsman to draw
            floor_sheet = next((sh for sh, keys in plans if r["floor_key"] in keys), None)
            why = why or ("It has no drawn position (added by hand, or settled in verification): draw it by hand."
                          if not anchor else f"This drawing has no plan where {r['source']} shows it ({r['floor']}): "
                                             "draw it by hand.")
            base = hashlib.sha1(r["id"].encode()).hexdigest()[:12]
            for code, n in wanted:
                cid = f"if:{base}:{code}{n + 1}"
                out[cid] = {"id": cid, "page": floor_sheet["index"] if floor_sheet else -1,
                            "sheet": floor_sheet["name"] if floor_sheet else "", "floor": r["floor"],
                            "room": r.get("location") or "", "system": INTERFACE, "system_name": "FA Interfaces",
                            "action": "add", "device": f"{modules[code]['name']} for {who}",
                            "instruction": f"{code} FOR {who}: {r['equipment']} ({r['system']})", "at": None,
                            "status": "failed", "candidates": [], "remove": None, "insert": None, "placeholder": False,
                            "note": "", "error": why, "moved": False, "confidence": None, "residual": None,
                            "source": INTERFACE, "interface": {"row": r["id"], "code": code, "for": who,
                                                              "equipment": r["equipment"], "tag": r["tag"]}}
            continue
        # one change per module of the item on that plan: a typical plan's floors are one
        spot = f"{sheet['index']}|{anchor[0]:.1f},{anchor[1]:.1f}|{r['key']}|{r['tag']}"
        copy = copies[(spot, r["floor_key"])]
        copies[(spot, r["floor_key"])] += 1
        base = hashlib.sha1((spot + (f"|{copy}" if copy else "")).encode()).hexdigest()[:12]
        for code, n in wanted:
            cid = f"if:{base}:{code}{n + 1}"
            if cid in out:
                continue
            finding = {"id": cid, "page": sheet["index"], "sheet": sheet["name"], "floor": sheet.get("floor") or r["floor"],
                       "room": r.get("location") or "", "system": INTERFACE, "system_name": "FA Interfaces",
                       "action": "add", "device": f"{modules[code]['name']} for {who}",
                       "instruction": f"{code} FOR {who}: {r['equipment']} ({r['system']})", "at": at}
            change = _prepare(finding, sheet, occurrences, top)
            change["source"] = INTERFACE
            change["interface"] = {"row": r["id"], "code": code, "for": who, "equipment": r["equipment"],
                                   "tag": r["tag"], "anchor": anchor, "note_height": _note_height(sheet)}
            columns[(sheet["index"], tuple(anchor))].append(change)
            out[cid] = change
    # on the nearest wall around the item's label, all of its modules at one
    # spot: the coordination lays them side by side along the wall; with no
    # wall near, one under the other from the label down
    for (page, anchor), members in columns.items():
        sheet = sheets[page]
        walled = walls is not None and _nearest_wall(walls, *anchor) is not None
        y = anchor[1]
        for change in sorted(members, key=lambda c: c["id"]):
            m = modules[change["interface"]["code"]]
            scale = m["scales"].get(sheet["name"], m["scale"])
            if "box" not in change:
                continue
            box, spot = change["box"], _page(sheet["geometry"], anchor[0], y)
            answer = {"candidate": 0, "symbol": m["id"], "x": (spot[0] - box[0]) / (box[2] - box[0]),
                      "y": (spot[1] - box[1]) / (box[3] - box[1]), "rotation": 0, "facing": None, "picked": True,
                      "confidence": "high", "note": ""}
            _place_module(change, sheet, symbols, answer, walls)
            if not walled:
                y -= m["size"] * scale + GAP_M + 0.02
            x0, y0, x1, y1 = m["ext"]
            change["interface"]["half"] = round((x1 - x0) / 2 * scale, 4)
            change["interface"]["depth"] = round((y1 - y0) / 2 * scale, 4)
    return list(out.values())


def _merge_interfaces(changes: list[dict], generated: list[dict], before: dict[str, dict]) -> list[dict]:
    """The review's changes, then the modules: one the engineer settled
    (approved, skipped, moved, picked) as they left it."""
    out = [c for c in changes if c.get("source") != INTERFACE]
    for c in generated:
        old = before.get(c["id"])
        if old and (old.get("moved") or old.get("edited")):
            # placed by the engineer: where they left it, saying what the schedule says now
            out.append({**old, "device": c["device"], "instruction": c["instruction"],
                        "interface": {**(old.get("interface") or {}), **(c.get("interface") or {})}})
        elif old and old.get("status") in ("approved", "skipped") and c["status"] == "proposed":
            out.append({**c, "status": old["status"]})
        else:
            out.append(c)
    return out


def add_interfaces(db: Session, project: Project, drawing_id: int) -> dict:
    """The interface schedule's modules brought in (again) without placing
    the review's changes again -- for a schedule changed after the plan."""
    from app.ifc.resolve import resolved_drawing

    drawing = db.get(ProjectIfcDrawing, drawing_id)
    if drawing is None or drawing.project_id != project.id:
        raise RedesignError("That drawing is not this project's")
    row = state(db, project, drawing.id)
    review_row, _view = _review(db, project, drawing)
    sheets = {sh["index"]: sh for sh in review_row.sheets or []}
    occurrences = _occurrences(resolved_drawing(db, drawing, with_occurrences=True))
    top, blocks, sizes = _top_level(drawing, _measured(occurrences))
    symbols = _all_symbols(occurrences, blocks, sizes, sheets)
    walls = _walls(project, drawing, row.source_sha256 or review_row.source_sha256, build=True)
    generated = _interface_changes(db, project, sheets, occurrences, top, symbols, walls)
    changes = [dict(c) for c in _merge_interfaces(row.changes or [], generated, {c["id"]: c for c in row.changes or []})]
    for c in changes:
        if c.get("source") == INTERFACE and c.get("moved") and c.get("insert") and not c.get("on_wall") and c.get("ai"):
            status = c["status"]
            _place_module(c, sheets[c["page"]], symbols, {**c["ai"], "facing": None}, walls)
            c["status"] = status
    coordinate(changes, sheets, walls, symbols)
    row.changes, row.symbols = [dict(c) for c in changes], symbols
    row.source_sha256 = row.source_sha256 or review_row.source_sha256
    if row.status in (None, "none"):
        row.status = "planned"
    db.commit()
    mine = [c for c in changes if c.get("source") == INTERFACE]
    return {"modules": len(mine), "placed": sum(1 for c in mine if c.get("insert")),
            "by_hand": sum(1 for c in mine if c["status"] == "failed")}


def set_status(db: Session, project: Project, drawing_id: int, ids: list[str], status: str) -> int:
    """Approve / skip / undo many changes at once (only the placed ones are approved)."""
    row = state(db, project, drawing_id)
    wanted = set(ids)
    changes, n = [], 0
    for c in row.changes or []:
        c = dict(c)
        if c["id"] in wanted and c["status"] != status and (status != "approved" or c.get("insert") or c.get("remove")) \
                and c["status"] != "failed":
            c["status"] = status
            n += 1
        changes.append(c)
    row.changes = changes
    db.commit()
    return n


def _drawn(c: dict) -> bool:
    """Made on the copy: an approved change, or a proposed one of the review's
    -- the interface modules only once approved."""
    return (c["status"] == "approved" or (c["status"] == "proposed" and c.get("source") != INTERFACE)) \
        and bool(c.get("remove") or c.get("insert"))


# --- planning ---------------------------------------------------------------------------


def _prepare(finding: dict, sheet: dict, occurrences: list[dict], top: set[str] | None) -> dict:
    """A change ready to ask about: its piece of plan and the symbols in it."""
    g = sheet.get("geometry") or {}
    change = {
        "id": finding["id"], "page": finding["page"], "sheet": finding["sheet"], "floor": finding["floor"],
        "room": finding["room"], "system": finding["system"], "system_name": finding["system_name"],
        "action": finding["action"], "device": finding["device"], "instruction": finding["instruction"],
        "at": finding["at"], "status": "pending", "candidates": [], "remove": None, "insert": None,
        "placeholder": False, "note": "", "error": None, "moved": False, "confidence": None,
        "residual": g.get("residual"),
    }
    if not finding.get("at"):
        change.update(status="failed", error="The review did not say where on the plan this is.")
        return change
    if "a" not in g:
        change.update(status="failed", error=g.get("error") or "This sheet's plot could not be tied to the drawing.")
        return change
    box = _box(g, finding["at"], sheet["plan"])
    change["box"] = box
    near = []
    for o in occurrences:
        if o["sheet"] != sheet["name"] or not _device(o):
            continue
        px, py = _page(g, o["x"], o["y"])
        if box[0] <= px <= box[2] and box[1] <= py <= box[3]:
            near.append((math.dist((px, py), finding["at"]), o, [px, py]))
    near.sort(key=lambda t: t[0])
    change["candidates"] = [
        {"n": n, "handle": o["handle"], "block": o["block"], "name": o["name"], "code": o["code"], "page": page,
         "model": [o["x"], o["y"]], "insert_point": [o["ix"], o["iy"]], "rotation": o["rotation"],
         "scale": o["scale"], "layer": o["layer"],
         # only what is known to be drawn directly in model space is erased:
         # without the drawing's DXF to say so, nothing is
         "erasable": top is not None and o["handle"] in top}
        for n, (_d, o, page) in enumerate(near[:MAX_CANDIDATES], 1)]
    return change


def _picture(doc: pymupdf.Document, change: dict, width: int, *, markers: bool = True) -> bytes:
    """The change's piece of plan: the nearby symbols numbered in blue, the
    review's point in red, and -- once placed -- the new symbol's point in
    green and the erased one crossed out."""
    from app.review import ai as RA

    box = tuple(change["box"])
    dpi = P.dpi_for(box, width)
    png = P.crop(doc, change["page"], box, dpi)
    if not markers:
        return png
    scale = dpi / 72.0
    to_px = lambda p: ((p[0] - box[0]) * scale, (p[1] - box[1]) * scale)  # noqa: E731
    png = RA.numbered(png, [(c["n"], *to_px(c["page"])) for c in change["candidates"]])
    image = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(image)
    r = max(12, image.width // 40)
    stroke = max(2, image.width // 300)
    ax, ay = to_px(change["at"])
    draw.ellipse((ax - r, ay - r, ax + r, ay + r), outline=(220, 38, 38), width=stroke)
    if change.get("remove"):
        x, y = to_px(change["remove"]["page"])
        draw.line((x - r, y - r, x + r, y + r), fill=(220, 38, 38), width=stroke + 1)
        draw.line((x - r, y + r, x + r, y - r), fill=(220, 38, 38), width=stroke + 1)
    if change.get("insert"):
        x, y = to_px(change["insert"]["page"])
        draw.ellipse((x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7), outline=(22, 163, 74), width=stroke + 1)
        draw.line((x - r, y, x + r, y), fill=(22, 163, 74), width=stroke)
        draw.line((x, y - r, x, y + r), fill=(22, 163, 74), width=stroke)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _place(change: dict, sheet: dict, symbols: list[dict], answer: dict, walls=None) -> None:
    """The change as the model (or the engineer) settled it: what is erased,
    what is inserted, where."""
    g = sheet["geometry"]
    by_id = {s["id"]: s for s in symbols}
    candidate = next((c for c in change["candidates"] if c["n"] == answer.get("candidate")), None)
    symbol = by_id.get(answer.get("symbol") or 0)
    box = change["box"]
    point = None
    if answer.get("x") is not None and answer.get("y") is not None:
        point = [box[0] + answer["x"] * (box[2] - box[0]), box[1] + answer["y"] * (box[3] - box[1])]
    action = change["action"]
    change["remove"], change["insert"], change["placeholder"], change["error"] = None, None, False, None
    if action in ("remove", "replace"):
        if candidate is None:
            change.update(status="failed", error="No symbol near it was picked to " + action)
            return
        change["remove"] = {k: candidate[k] for k in ("n", "handle", "block", "name", "page", "model", "erasable")}
    if action in ("add", "replace"):
        # the platform owner's symbol for the device, where the drawing has it --
        # unless the engineer picked another
        if not answer.get("picked"):
            symbol = _preferred(change["device"], symbols) or symbol
        if symbol is not None and _weather(change["device"]):
            symbol = _weatherproof_variant(symbol) or symbol
        where_page = (candidate["page"] if action == "replace" and candidate else None) or point or change["at"]
        if action == "replace" and candidate:
            seen = list(candidate["model"])            # where the old symbol is seen
            rotation = candidate["rotation"]
        else:
            seen = _model(g, *where_page)
            rotation = _rotation(symbol, answer)
        if symbol is None:
            change["placeholder"] = True
            change["insert"] = {"symbol": 0, "name": change["device"] or "the device", "block": None, "layer": None,
                                "scale": None, "rotation": rotation, "page": where_page, "model": seen, "seen": seen}
        else:
            scale = symbol["scales"].get(change["sheet"], symbol["scale"])
            # a wall device fixed on the wall: its back on the face of the wall
            # behind the spot, facing into the room
            change["on_wall"] = False
            facing = _VECTORS.get(answer.get("facing") or "")
            if facing is None and action == "add" and walls is not None and symbol.get("facing") is not None:
                # a wall device whose facing was not said: away from the nearest wall face around it
                faces = []
                for name, vector in _VECTORS.items():
                    face = walls.face_behind(seen[0], seen[1], vector, back=1.0, front=0.05)
                    if face is not None:
                        faces.append((math.dist(seen, face), name, vector))
                if faces:
                    _d, name, facing = min(faces)
                    answer = {**answer, "facing": name}
                    rotation = _rotation(symbol, answer)
            if action == "add" and walls is not None and facing and symbol.get("depth") is not None:
                face = walls.face_behind(seen[0], seen[1], facing)
                if face is not None:
                    half = symbol["depth"] * scale
                    seen = [round(face[0] + facing[0] * half, 4), round(face[1] + facing[1] * half, 4)]
                    where_page = _page(g, *seen)
                    change["on_wall"] = True
            # inserted so its graphics, not its base point, land on the spot
            cx, cy = symbol.get("center") or [0.0, 0.0]
            dx, dy = _rotate(cx * scale, cy * scale, rotation)
            change["insert"] = {"symbol": symbol["id"], "name": symbol["name"], "code": symbol["code"],
                                "block": symbol["block"], "layer": symbol["layer"], "scale": scale,
                                "rotation": rotation, "page": where_page,
                                "model": [round(seen[0] - dx, 4), round(seen[1] - dy, 4)], "seen": seen,
                                "placed": list(seen), "offset": [round(dx, 4), round(dy, 4)],
                                "radius": round((symbol.get("size") or 0.4 / scale) * scale / 2, 4),
                                "make": symbol.get("make"), "library": symbol.get("library"),
                                "facing": list(facing) if change.get("on_wall") else None}
    if change["status"] in ("pending", "failed"):
        change["status"] = "proposed"


GAP_M = 0.15                 # the clearance kept between two symbols
EXISTING_RADIUS_M = 0.25     # an existing symbol's footprint, its size not being read
CHAR_WIDTH = 0.85            # a note's letter, as wide as this much of its height
NEAR_M = 15.0                # what can touch: within this of each other


def _note(c: dict) -> dict | None:
    """A module's "FOR ..." note, as the sample writes it: beside it, on its
    layer; on a wall, running from its front into the room (across a wall
    up and down the sheet, upright on a wall across it)."""
    insert, face = c.get("insert") or {}, c.get("interface") or {}
    if not insert.get("block") or not face.get("note_height"):
        return None
    h, (sx, sy) = face["note_height"], insert["seen"]
    note = {"text": f"FOR {face['for']}", "height": round(h, 4), "layer": insert.get("layer") or "0",
            "at": [round(sx + (face.get("half") or 0) + 0.4 * h, 4), round(sy - h / 2, 4)],
            "rotation": 0, "align": "left"}
    f = insert.get("facing")
    if f:
        out_m = (face.get("depth") or face.get("half") or 0) + 0.4 * h
        fx, fy = sx + f[0] * out_m, sy + f[1] * out_m
        if abs(f[0]) > 0.5:
            note.update(at=[round(fx, 4), round(sy - h / 2, 4)], align="left" if f[0] > 0 else "right")
        else:
            note.update(at=[round(sx + h / 2, 4), round(fy, 4)], rotation=90, align="left" if f[1] > 0 else "right")
    return note


def _footprint(c: dict) -> list[tuple[float, float, float, float]]:
    """What a placed change takes on the plan, as boxes: its symbol (a
    module's own rectangle, turned; else the circle round it) and its note."""
    ins = c["insert"]
    x, y = ins["seen"]
    face = c.get("interface") or {}
    if face.get("half") and face.get("depth"):
        hw, hh = face["half"], face["depth"]
        if round(float(ins.get("rotation") or 0)) % 180 == 90:
            hw, hh = hh, hw
    else:
        hw = hh = ins.get("radius") or EXISTING_RADIUS_M
    boxes = [(x - hw, y - hh, x + hw, y + hh)]
    note = _note(c)
    if note:
        (nx, ny), h = note["at"], note["height"]
        length = len(note["text"]) * h * CHAR_WIDTH
        if note["rotation"]:
            boxes.append((nx - h, ny - length, nx, ny) if note["align"] == "right" else (nx - h, ny, nx, ny + length))
        else:
            boxes.append((nx - length, ny, nx, ny + h) if note["align"] == "right" else (nx, ny, nx + length, ny + h))
    return boxes


def _overlap(a, b, gap: float) -> bool:
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def coordinate(changes: list[dict], sheets: dict[int, dict], walls=None, symbols: list[dict] | None = None) -> int:
    """Keep every new symbol -- and a module's note -- clear of the others and
    of the devices already on the plan (platform owner, 2 October 2026:
    always): two devices added at one door side by side, the modules of a
    pump room one after the other along its wall, never one on another.
    Nothing is left out: the engineer's own placings are settled first and
    keep their spot when it is clear, but give way like the rest when two of
    them meet. A symbol that clashes is moved the least it takes: a wall
    device along its wall (still on it, never past its corner), any other
    step by step around its spot. A module its wall has no room for goes on
    the next wall around its equipment, turned to it. Returns how many were
    moved."""
    def placed(c):
        return (c["status"] in ("proposed", "approved", "pending") and c.get("insert") and c["insert"].get("seen")
                and c["insert"].get("block"))

    order = sorted((c for c in changes if placed(c)),
                   key=lambda c: (not c.get("moved"), c.get("source") == INTERFACE, c["status"] != "approved",
                                  str(c["id"])))
    erased = {(c.get("remove") or {}).get("handle") for c in changes if c.get("remove")}
    existing: dict[int, dict[str, tuple[float, float]]] = defaultdict(dict)
    for c in changes:
        for k in c.get("candidates") or []:
            # a device symbol of the plan's (not a parking bay's number in the architect's xref)
            if k["handle"] not in erased and (k.get("erasable") or k.get("code")):
                existing[c["page"]][k["handle"]] = tuple(k["model"])
    fixed: dict[int, list[dict]] = defaultdict(list)            # the changes settled so far, page by page
    touched: set = set()

    def move(c, x: float, y: float) -> None:
        ins = c["insert"]
        if math.dist((x, y), ins["seen"]) < 1e-6:
            return
        dx, dy = ins.get("offset") or [ins["seen"][0] - ins["model"][0], ins["seen"][1] - ins["model"][1]]
        ins["seen"] = [round(x, 4), round(y, 4)]
        ins["model"] = [round(x - dx, 4), round(y - dy, 4)]
        ins["page"] = _page(sheets[c["page"]]["geometry"], *ins["seen"])
        c["coordinated"] = True
        touched.add(c["id"])

    def clear(c, x: float, y: float, skip=()) -> bool:
        x0, y0 = c["insert"]["seen"]
        dx, dy = x - x0, y - y0
        mine = [(a + dx, b + dy, e + dx, f + dy) for a, b, e, f in _footprint(c)]
        for f in fixed[c["page"]]:
            if f is c or f in skip or math.dist(f["insert"]["seen"], (x, y)) > NEAR_M:
                continue
            if any(_overlap(m, o, GAP_M) for m in mine for o in _footprint(f)):
                return False
        start = c["insert"].get("placed") or c["insert"]["seen"]
        for ex, ey in existing[c["page"]].values():
            if math.dist((ex, ey), (x, y)) > NEAR_M or math.dist(start, (ex, ey)) <= 0.01:
                continue                 # an existing symbol it replaces, on purpose, is not a clash
            box = (ex - EXISTING_RADIUS_M, ey - EXISTING_RADIUS_M, ex + EXISTING_RADIUS_M, ey + EXISTING_RADIUS_M)
            if any(_overlap(m, box, GAP_M) for m in mine):
                return False
        return True

    def wall_of(c):
        facing = c["insert"].get("facing")
        if not facing or walls is None:
            return None
        span = walls.face_span(*c["insert"]["seen"], tuple(facing))
        return (tuple(facing), (-facing[1], facing[0]), *span) if span else None

    def along(c, tangent):
        return c["insert"]["seen"][0] * tangent[0] + c["insert"]["seen"][1] * tangent[1]

    def reach(c, tangent) -> tuple[float, float]:
        """How far its footprint runs either way along the wall, from it."""
        t0 = along(c, tangent)
        ts = [a * tangent[0] + b * tangent[1] for x0, y0, x1, y1 in _footprint(c)
              for a, b in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        return t0 - min(ts), max(ts) - t0

    # each from where it was placed: the coordination is done afresh every time
    for c in order:
        ins = c["insert"]
        if ins.get("placed") and list(ins["seen"]) != list(ins["placed"]):
            dx, dy = ins.get("offset") or [ins["seen"][0] - ins["model"][0], ins["seen"][1] - ins["model"][1]]
            ins["seen"] = list(ins["placed"])
            ins["model"] = [round(ins["seen"][0] - dx, 4), round(ins["seen"][1] - dy, 4)]
            ins["page"] = _page(sheets[c["page"]]["geometry"], *ins["seen"])
            touched.add(c["id"])
        c.pop("coordinated", None)

    def slide(c, wall) -> bool:
        """Along its wall to the nearest clear spot, never past its end (a
        corner, an opening, a step)."""
        x0, y0 = c["insert"]["seen"]
        facing, tangent, offset, lo, hi = wall
        t0 = along(c, tangent)
        back, ahead = reach(c, tangent)
        first, last = lo + min(back, (hi - lo) / 2), hi - min(ahead, (hi - lo) / 2)
        tries = sorted({min(max(t0 + k * 0.05, first), last) for k in range(-240, 241)}, key=lambda t: abs(t - t0))
        for t in tries:
            x, y = x0 + (t - t0) * tangent[0], y0 + (t - t0) * tangent[1]
            if clear(c, x, y):
                move(c, x, y)
                return True
        return False

    def next_wall(c, wall) -> bool:
        """A module its wall has no room for: on the next wall around its
        equipment, turned to it, slid to a clear spot there."""
        face = c.get("interface") or {}
        sheet = sheets.get(c["page"])
        if not face or not symbols or walls is None or not sheet or "box" not in c or not c.get("ai"):
            return False
        ax, ay = face.get("anchor") or c["insert"]["seen"]
        facing, _tangent, offset, lo, hi = wall
        for name, point in _walls_around(walls, ax, ay):
            v = _VECTORS[name]
            if tuple(v) == tuple(facing) and abs(point[0] * v[0] + point[1] * v[1] - offset) < 0.02:
                continue                                       # the wall it is on
            box, g = c["box"], sheet["geometry"]
            spot = _page(g, point[0] + v[0] * 0.3, point[1] + v[1] * 0.3)
            answer = {**c["ai"], "facing": name, "rotation_set": None,
                      "x": (spot[0] - box[0]) / (box[2] - box[0]), "y": (spot[1] - box[1]) / (box[3] - box[1])}
            trial = json.loads(json.dumps(c))
            _place(trial, sheet, symbols, answer, walls)
            if not trial.get("on_wall"):
                continue
            trial["status"] = c["status"]
            there = wall_of(trial)
            tx, ty = trial["insert"]["seen"]
            if clear(trial, tx, ty) or (there is not None and slide(trial, there)):
                c.update(trial)
                c["coordinated"] = True
                touched.add(c["id"])
                return True
        return False

    for c in order:
        x0, y0 = c["insert"]["seen"]
        if clear(c, x0, y0):
            fixed[c["page"]].append(c)
            continue
        wall = wall_of(c)
        done = False
        if wall is not None:
            facing, tangent, offset, lo, hi = wall
            done = slide(c, wall)
            if not done:
                # no room alone: it and the devices on the same wall it meets share
                # the wall side by side, around where they were
                group = [f for f in fixed[c["page"]] if (w := wall_of(f)) is not None and w[0] == facing
                         and abs(w[2] - offset) < 0.01 and not clear(c, x0, y0, skip=[x for x in fixed[c["page"]] if x is not f])]
                group = sorted(group + [c], key=lambda g: along(g, tangent))
                extents = [reach(g, tangent) for g in group]
                need = sum(b + a for b, a in extents) + GAP_M * (len(group) - 1)
                if len(group) > 1 and need <= hi - lo + 1e-6:
                    mid = sum(along(g, tangent) for g in group) / len(group)
                    at = min(max(mid - need / 2, lo), hi - need)
                    spots = []
                    for (b, a) in extents:
                        spots.append(at + b)
                        at += b + a + GAP_M
                    trial = [(g["insert"]["seen"][0] + (t - along(g, tangent)) * tangent[0],
                              g["insert"]["seen"][1] + (t - along(g, tangent)) * tangent[1]) for g, t in zip(group, spots)]
                    if all(clear(g, *pt, skip=group) for g, pt in zip(group, trial)):
                        for g, pt in zip(group, trial):
                            move(g, *pt)
                        done = True
            if not done:
                done = next_wall(c, wall)
        if not done and (wall is None or c.get("source") == INTERFACE):
            # free standing (or a module no wall around it has room for): step by step round its spot
            step = 0.1
            for k in range(1, 61):
                for n in range(8):
                    angle = math.radians(45 * n)
                    x, y = x0 + k * step * math.cos(angle), y0 + k * step * math.sin(angle)
                    if clear(c, x, y):
                        move(c, x, y)
                        done = True
                        break
                if done:
                    break
        fixed[c["page"]].append(c)
    return len(touched)


def _ask(project_id: int, pdf: str, sha: str, sheet: dict, change: dict, symbols: list[dict], budget) -> dict:
    """One change put to the model, in a session of its own (it runs beside others)."""
    s = get_settings()
    db = SessionLocal()
    doc = pymupdf.open(pdf)
    try:
        session = assist.AssistSession(db=db, project_id=project_id, document_sha256=f"{sha}:{change['id']}",
                                       budget=budget, provider=get_provider())
        parts: list = []
        if sheet.get("legend"):
            parts.append(ImagePart("legend", P.crop(doc, change["page"], tuple(sheet["legend"]),
                                                    P.dpi_for(tuple(sheet["legend"]), 1000))))
        parts.append(ImagePart("the plan around the change", _picture(doc, change, 1400)))
        parts.append(TextPart("change", (
            f"{change['action'].upper()} -- {change['device'] or change['system_name']}\n"
            f"Floor: {change['floor']} ({change['sheet']}); room / where: {change['room'] or '-'}\n"
            f"Engineer's instruction: {change['instruction']}")))
        parts.append(TextPart("numbered symbols", "\n".join(
            f"{c['n']}: {c['name']}" for c in change["candidates"]) or "none near it"))
        parts.append(TextPart("symbols this drawing uses (id: name)", "\n".join(
            f"{x['id']}: {x['name']}" + (f" ({x['code']})" if x["code"] else "") for x in symbols)))
        result = assist.call_task(session, A.TASK, A.SYSTEM, parts, A.SCHEMA, 800, prompt_version=A.PROMPT_VERSION,
                                  model=s.drawing_review_model, effort=s.drawing_review_effort, exact_model=True,
                                  timeout_s=s.drawing_review_timeout_s)
        db.commit()
        if result.data is None:
            return {"error": result.error or "no answer"}
        return {"answer": A.read_answer(result.data, len(change["candidates"]), {x["id"] for x in symbols})}
    finally:
        doc.close()
        db.close()


def plan(db: Session, project: Project, drawing_id: int, *, progress=None, check=None) -> dict:
    """Place every accepted change of the drawing's review. A change the
    engineer already settled (approved, moved, skipped) is kept as they left
    it; the rest are asked again."""
    from app.ifc.resolve import resolved_drawing
    from app.review import service as review

    s = get_settings()
    drawing = db.get(ProjectIfcDrawing, drawing_id)
    if drawing is None or drawing.project_id != project.id:
        raise RedesignError("That drawing is not this project's")
    row = state(db, project, drawing.id)
    row.status, row.error, row.started_at, row.finished_at = "planning", None, utc_now(), None
    db.commit()

    def say(done: int, total: int, message: str) -> None:
        if progress:
            progress(done, max(total, 1), message)

    try:
        say(0, 1, "Reading the review and the drawing's symbols")
        review_row, view = _review(db, project, drawing)
        if not review_row.pdf_path:
            raise RedesignError("The drawing has not been plotted by the review yet.")
        from app.review import render

        source = render.source_file(project, drawing)
        if review_row.source_sha256 and render._sha(source) != review_row.source_sha256:
            raise RedesignError("The drawing has changed since it was reviewed: review it again before redesigning.")
        sheets = {sh["index"]: sh for sh in review_row.sheets or []}
        resolved = resolved_drawing(db, drawing, with_occurrences=True)
        occurrences = _occurrences(resolved)
        top, blocks, sizes = _top_level(drawing, _measured(occurrences))
        symbols = _all_symbols(occurrences, blocks, sizes, sheets)
        accepted = [f for f in view["findings"] if f["decision"] == "accepted" and f["action"] in ACTIONS]
        before = {c["id"]: c for c in row.changes or []}
        changes = []
        for finding in accepted:
            old = before.get(finding["id"])
            if old and (old.get("status") in ("approved", "skipped") or old.get("moved") or old.get("edited")):
                changes.append(old)
                continue
            changes.append(_prepare(finding, sheets[finding["page"]], occurrences, top))
        say(0, 1, "Reading the drawing's walls (once per drawing)")
        walls = _walls(project, drawing, review_row.source_sha256, build=True, check=check)
        say(0, 1, "Placing the interface schedule's modules")
        try:
            changes = _merge_interfaces(changes, _interface_changes(db, project, sheets, occurrences, top, symbols, walls),
                                        before)
        except Exception as exc:  # noqa: BLE001 -- the review's changes are placed all the same
            log.warning("The interface modules could not be placed: %s", exc)
        row.changes, row.symbols, row.source_sha256 = changes, symbols, review_row.source_sha256
        db.commit()

        todo = [c for c in changes if c["status"] == "pending"]
        budget = review._budget(db, project)
        pdf = str(storage.absolute(review_row.pdf_path))
        done = 0
        say(0, len(todo), f"Placing {len(todo)} change{'s' if len(todo) != 1 else ''} with {s.drawing_review_model}")
        pool = ThreadPoolExecutor(max_workers=max(1, s.drawing_review_parallel))
        try:
            futures = {pool.submit(_ask, project.id, pdf, review_row.source_sha256 or "", sheets[c["page"]], c,
                                   symbols, budget): c for c in todo}
            for future in as_completed(futures):
                if check:
                    check()
                change = futures[future]
                try:
                    reply = future.result()
                except Exception as exc:  # noqa: BLE001 -- one change failing is that change, not the plan
                    reply = {"error": f"{type(exc).__name__}: {exc}"[:300]}
                row.calls = (row.calls or 0) + 1
                if "answer" in reply:
                    answer = reply["answer"]
                    change["ai"] = answer
                    change["confidence"], change["note"] = answer["confidence"], answer["note"]
                    _place(change, sheets[change["page"]], symbols, answer, walls)
                else:
                    change.update(status="failed", error=reply.get("error"))
                done += 1
                row.changes = [dict(c) for c in changes]
                db.commit()
                say(done, len(todo), f"Placed {done} of {len(todo)} ({change['floor']})")
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        coordinate(changes, sheets, walls, symbols)
        row.changes = [dict(c) for c in changes]
        row.status, row.finished_at = "planned", utc_now()
        db.commit()
        return {"changes": len(changes), "placed": sum(1 for c in changes if c["status"] == "proposed")}
    except Exception as exc:
        db.rollback()
        row = state(db, project, drawing_id)
        row.status, row.error, row.finished_at = "failed", str(exc)[:1000], utc_now()
        db.commit()
        raise


# --- the engineer's word ---------------------------------------------------------------


def adjust(db: Session, project: Project, drawing_id: int, change_id: str, *, status: str | None = None,
           candidate: int | None = None, symbol: int | None = None, point: list[float] | None = None,
           rotation: float | None = None) -> dict:
    """Approve, skip, move (a point on the change's picture, as fractions),
    pick another symbol to erase or to insert."""
    row = state(db, project, drawing_id)
    changes = [dict(c) for c in row.changes or []]
    change = next((c for c in changes if c["id"] == change_id), None)
    if change is None:
        raise RedesignError("No such change")
    if candidate is not None or symbol is not None or point is not None or rotation is not None:
        if "box" not in change:
            raise RedesignError(change.get("error") or "This change cannot be placed on the plan.")
        review_row = (db.query(ProjectDrawingReview)
                      .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing_id).first())
        sheet = next(sh for sh in review_row.sheets if sh["index"] == change["page"])
        answer = dict(change.get("ai") or {})
        answer.setdefault("candidate", (change.get("remove") or {}).get("n", 0))
        answer.setdefault("symbol", (change.get("insert") or {}).get("symbol", 0))
        if candidate is not None:
            answer["candidate"] = candidate
        if symbol is not None:
            answer["symbol"] = symbol
            answer["picked"] = True
        if rotation is not None:
            answer["rotation"] = rotation % 360
            answer["rotation_set"] = True
        if point is not None:
            answer["x"], answer["y"] = min(max(point[0], 0), 1), min(max(point[1], 0), 1)
            change["moved"] = True
            if change.get("source") == INTERFACE:
                answer["facing"] = None             # on the wall nearest the click
        elif change.get("insert") and change["action"] == "add" and "x" not in answer:
            box, page = change["box"], change["insert"]["page"]
            answer["x"] = (page[0] - box[0]) / (box[2] - box[0])
            answer["y"] = (page[1] - box[1]) / (box[3] - box[1])
        change["ai"] = answer
        change["edited"] = True
        was = change["status"]
        change["status"] = "pending"
        drawing = db.get(ProjectIfcDrawing, drawing_id)
        walls = _walls(project, drawing, row.source_sha256)
        if change.get("source") == INTERFACE:
            _place_module(change, sheet, row.symbols or [], answer, walls)
        else:
            _place(change, sheet, row.symbols or [], answer, walls)
        coordinate(changes, {sh["index"]: sh for sh in review_row.sheets or []}, walls, row.symbols or [])
        if was == "approved" and change["status"] == "proposed":
            change["status"] = "approved"          # an approved change, adjusted, stays approved
    if status:
        change["status"] = status
    row.changes = changes
    db.commit()
    return change


def image(project: Project, drawing_id: int, row: ProjectRedesign, change_id: str, width: int) -> bytes:
    from app.models import ProjectDrawingReview as _R

    db = SessionLocal()
    try:
        review_row = db.query(_R).filter(_R.project_id == project.id, _R.drawing_id == drawing_id).first()
        pdf = str(storage.absolute(review_row.pdf_path))
    finally:
        db.close()
    change = next((c for c in row.changes or [] if c["id"] == change_id), None)
    if change is None or "box" not in change:
        raise RedesignError("No picture for this change")
    doc = pymupdf.open(pdf)
    try:
        return _picture(doc, change, width)
    finally:
        doc.close()


# --- making the redesigned drawing -----------------------------------------------------


def _units(drawing: ProjectIfcDrawing, db: Session) -> float:
    """How many drawing units a metre is."""
    from app.ifc.resolve import resolved_drawing

    units = (resolved_drawing(db, drawing, with_occurrences=False).get("units") or "m").lower()
    return {"m": 1.0, "mm": 1000.0, "cm": 100.0, "in": 39.37, "ft": 3.281}.get(units, 1.0)


def to_cad(changes: list[dict]) -> list[dict]:
    """The placed changes as AutoCAD makes them (app.redesign.cad): what to
    erase by handle, what to insert, where the marker goes and what it says."""
    out = []
    for c in changes:
        remove, insert = c.get("remove"), c.get("insert")
        handle = remove["handle"] if remove and remove.get("erasable") else None
        label = f"{cad.LABEL[c['action']]}: {c['device'] or (insert or remove or {}).get('name') or ''}"
        if remove and not remove.get("erasable"):
            label += " (erase by hand)"
        if insert and not insert.get("block"):
            label += " (draw symbol)"
        note = _note(c)
        if note:
            face = c["interface"]
            label = f"{cad.LABEL[c['action']]}: {face['code']} FOR {face['for']}"
        out.append({"action": c["action"], "remove_handle": handle,
                    "insert": insert if insert and insert.get("block") else None,
                    "at": (insert or {}).get("seen") or (insert or remove)["model"], "label": label, "note": note})
    return out


def refresh(db: Session, project: Project, drawing: ProjectIfcDrawing, row: ProjectRedesign) -> int:
    """Bring changes placed by an earlier version of the placing up to date
    -- the drawing's symbols read again (each block's drawn centre, the
    platform owner's symbol for a device), each such change placed again
    from what was decided: the model's answer and every pick or move of the
    engineer's, its status kept. Returns how many were placed again."""
    from app.ifc.resolve import resolved_drawing

    stale = [c for c in row.changes or [] if c.get("insert")
             and ("seen" not in c["insert"] or (c["insert"].get("block") and "placed" not in c["insert"])
                  or (c.get("source") == INTERFACE and not c["insert"].get("library")))]
    if not stale and all("ext" in s for s in row.symbols or []) and not any(
            s["name"].startswith("Emergency Light") and s.get("facing") is not None for s in row.symbols or []):
        # nothing to place again: only the coordination, which is cheap
        review_row = (db.query(ProjectDrawingReview)
                      .filter(ProjectDrawingReview.project_id == project.id,
                              ProjectDrawingReview.drawing_id == drawing.id).first())
        changes = [dict(c) for c in row.changes or []]
        if coordinate(changes, {sh["index"]: sh for sh in review_row.sheets or []},
                      _walls(project, drawing, row.source_sha256), row.symbols or []):
            row.changes = changes
            db.commit()
        return 0
    review_row = (db.query(ProjectDrawingReview)
                  .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing.id).first())
    sheets = {sh["index"]: sh for sh in review_row.sheets or []}
    occurrences = _occurrences(resolved_drawing(db, drawing, with_occurrences=True))
    _top, blocks, sizes = _top_level(drawing, _measured(occurrences))
    symbols = _all_symbols(occurrences, blocks, sizes, sheets)
    changes = [dict(c) for c in row.changes or []]
    walls = _walls(project, drawing, row.source_sha256, build=True)
    again = 0
    for change in changes:
        if not change.get("insert") or "box" not in change:
            continue
        answer = dict(change.get("ai") or {})
        answer.setdefault("candidate", (change.get("remove") or {}).get("n", 0))
        answer.setdefault("symbol", change["insert"].get("symbol", 0))
        answer.setdefault("rotation", change["insert"].get("rotation", 0))
        if answer.get("x") is None or answer.get("y") is None:
            box, page = change["box"], change["insert"]["page"]
            answer["x"] = (page[0] - box[0]) / (box[2] - box[0])
            answer["y"] = (page[1] - box[1]) / (box[3] - box[1])
        status = change["status"]
        if change.get("source") == INTERFACE:
            _place_module(change, sheets[change["page"]], symbols, answer, walls)
        else:
            _place(change, sheets[change["page"]], symbols, answer, walls)
        change["status"] = status
        again += 1
    coordinate(changes, sheets, walls, symbols)
    row.changes, row.symbols = changes, symbols
    db.commit()
    return again


def apply(db: Session, project: Project, drawing_id: int, user_id: int | None, *, progress=None, check=None) -> dict:
    """Make the approved and proposed changes on a copy of the DWG the review
    plotted, and file it in the project folder (03- Drawings/Redesign)."""
    from app.review import render

    drawing = db.get(ProjectIfcDrawing, drawing_id)
    row = state(db, project, drawing_id)
    row.output_status, row.output_error = "making", None
    db.commit()
    try:
        source = render.source_file(project, drawing)
        if source.suffix.lower() != ".dwg":
            raise RedesignError("The drawing's DWG is not on this PC: import the fire alarm IFC drawing again.")
        if row.source_sha256 and render._sha(source) != row.source_sha256:
            raise RedesignError("The drawing has changed since it was reviewed: review it again before redesigning.")
        metre = _units(drawing, db)
        refresh(db, project, drawing, row)
        todo = [c for c in row.changes or [] if _drawn(c)]
        if not todo:
            raise RedesignError("No change is placed to make: plan the redesign, or approve the changes first.")
        cad_changes = to_cad(todo)
        if progress:
            progress(0, 1, f"AutoCAD is making {len(cad_changes)} change{'s' if len(cad_changes) != 1 else ''} on a copy")
        stamp = datetime.now().strftime("%Y-%m-%d %H%M")
        stem = re.sub(r"\.(dwg|dxf)$", "", drawing.filename, flags=re.I)
        name = f"{stem} {drawing.revision or 'R0'} - Redesign {stamp}.dwg"
        platform_copy = (storage.uploads_root() / f"EP-{project.ep_number}" / "redesign" / name).resolve()
        cad.apply(source, platform_copy, cad_changes, marker=0.6 * metre, text_height=0.25 * metre,
                  work=platform_copy.parent / f"work-{row.id}")
        relative = None
        if project.source_folder_path:
            from app.services import document_control

            target = Path(project.source_folder_path) / FOLDER / name
            try:
                os.makedirs(document_control._os_path(target.parent), exist_ok=True)
                with open(platform_copy, "rb") as src, open(document_control._os_path(target), "wb") as out:
                    out.write(src.read())
                relative = f"{FOLDER}/{name}"
            except OSError as exc:
                log.warning("The redesigned drawing could not be filed in the project folder: %s", exc)
        row.output_status, row.output_path, row.output_relative = "made", str(platform_copy), relative
        row.output_at, row.output_changes = utc_now(), len(cad_changes)
        db.commit()
        return {"file": name, "filed": relative, "changes": len(cad_changes)}
    except Exception as exc:
        db.rollback()
        row = state(db, project, drawing_id)
        row.output_status, row.output_error = "failed", str(exc)[:1000]
        db.commit()
        raise


# --- the page ---------------------------------------------------------------------------


def view(db: Session, project: Project, drawing_id: int) -> dict:
    drawing = db.get(ProjectIfcDrawing, drawing_id)
    row = state(db, project, drawing_id)
    review_row = (db.query(ProjectDrawingReview)
                  .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing_id).first())
    undecided = 0
    if review_row is not None and review_row.status == "done" and drawing is not None:
        from app.review import service as review

        undecided = review.build(db, project, drawing)["counts"]["open"]
    db.commit()
    changes = []
    for c in row.changes or []:
        out = {k: v for k, v in c.items() if k not in ("ai",)}
        residual = c.get("residual")
        out["coordinated"] = bool(c.get("coordinated"))
        out["drawn"] = _drawn(c)
        out["confirm"] = bool(c.get("insert") and c["action"] == "add" and not c.get("moved")
                              and residual is not None and residual > CONFIRM_ABOVE_M)
        changes.append(out)
    counts = Counter(c["status"] for c in changes)
    return {
        "drawing": {"id": drawing.id, "filename": drawing.filename, "revision": drawing.revision or "R0"} if drawing else None,
        "review": {"status": review_row.status if review_row else None, "undecided": undecided},
        "status": row.status, "error": row.error, "calls": row.calls or 0,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "changes": changes, "symbols": [{k: s[k] for k in ("id", "name", "code", "block", "count")} for s in row.symbols or []],
        "counts": {k: counts.get(k, 0) for k in ("pending", "proposed", "approved", "skipped", "failed")},
        "output": {"status": row.output_status, "error": row.output_error, "relative": row.output_relative,
                   "file": Path(row.output_path).name if row.output_path else None,
                   "at": row.output_at.isoformat() if row.output_at else None, "changes": row.output_changes},
        "folder": FOLDER,
    }
