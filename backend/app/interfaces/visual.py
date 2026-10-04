"""The interface schedule's damper labels looked at on the drawing itself
(platform owner, 2 October 2026: "verification visually must be done").

A damper is read from its label alone -- MSD, MD, SD, SMD written beside a
duct -- and a label is not always a damper: EP-30880's ventilation layout
has an architect's door tag "SD 04" in the 3rd basement, read as a smoke
damper, and two MSDs a metre apart at its pump room, counted as one. So each
piece of the smoke management and ventilation plans with damper labels on it
is drawn from the drawing itself (its DXF, every line at any depth -- the
architect's background too -- in its own colours; AutoCAD's plot of such a
drawing can take over half an hour), and the model (Opus, as the review) is
shown it with the labels ringed and numbered: for each, whether it names a
damper drawn on a duct, and where that damper is. A label that is not a
damper's is set aside, with what it is; each one that is, is a damper of its
own, at the damper -- where the redesign puts its module.

What the model said is kept with the drawing's reading, by the file's hash:
a drawing read again unchanged is not looked at again.
"""
from __future__ import annotations

import io
import logging
import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.ai.provider import ImagePart, TextPart, get_provider
from app.compliance import assist
from app.core.config import get_settings
from app.database import SessionLocal

log = logging.getLogger(__name__)
VERSION = 3
PROMPT_VERSION = "interface-dampers-visual-2026-10-04.3"
TASK = "fa_interfaces_visual"
KEYS = ("motorized_smoke_fire_damper",)
DISCIPLINES = ("SM", "HVAC")
WINDOW_M = 10.0          # the piece of plan one look covers
MARGIN_M = 2.5           # and around it
IMAGE_PX = 1400
CELL_M = 5.0             # the drawing's lines kept in a grid of these
_METRE = {"mm": 1000.0, "cm": 100.0, "m": 1.0, "in": 39.37, "ft": 3.281}

SYSTEM = """You check the dampers of a smoke management / ventilation (HVAC) floor plan for a fire alarm contractor in
the UAE: every motorized, smoke or fire/smoke damper is interfaced to the fire alarm system (a relay module each), so
each one must be found -- and nothing that is not a damper may be counted.

The plan was read for its words. Each red ring with a red number marks a text the reading took for a damper's label
(MSD, MFSD, MD, SD, SMD and the like). Look at the drawing around each one:
- A damper's label names a damper symbol drawn on a duct close to it: a small box or rectangle across the duct, often
  crossed by a diagonal or with an actuator, sometimes joined to the label by a leader.
- Not a damper: a door tag (a code with a number, at a door: "SD 04"), a room or area tag, a smoke detector, a duct
  size or air flow, a note, a legend entry, a schedule.
- Two labels side by side may name two dampers side by side: each label its own damper.

For each number: damper true or false; for a damper the point of ITS damper symbol (x, y as fractions 0..1 of this
image's width and height), else -1, -1; what it is in at most 8 words; your confidence (low whenever unsure).
Answer every number you are given, and only those."""

SCHEMA = {
    "type": "object",
    "properties": {
        "labels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer"},
                    "damper": {"type": "boolean"},
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "what": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["n", "damper", "x", "y", "what", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["labels"],
    "additionalProperties": False,
}


def item_id(it: dict) -> str:
    """A label read on a drawing, the same every time the drawing is read."""
    return f"{it['sheet']}|{it['x']:.2f},{it['y']:.2f}|{it['text'][:40]}"


def wanted(src: dict) -> list[dict]:
    """The labels of a reading that are looked at."""
    if src.get("discipline") not in DISCIPLINES or src.get("status") != "read":
        return []
    return [it for it in (src.get("result") or {}).get("items", []) if it["key"] in KEYS]


def _quick_box(e) -> tuple[float, float, float, float] | None:
    """An entity's extents, cheaply for the common ones; None for the rest."""
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return min(a.x, b.x), min(a.y, b.y), max(a.x, b.x), max(a.y, b.y)
        if t == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in e.get_points("xy")]
            if not pts:
                return None
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return min(xs), min(ys), max(xs), max(ys)
        if t in ("CIRCLE", "ARC"):
            c, r = e.dxf.center, e.dxf.radius
            return c.x - r, c.y - r, c.x + r, c.y + r
        if t == "TEXT":
            p, h = e.dxf.insert, e.dxf.height or 0.0
            width = len(e.dxf.text or "") * h
            return p.x - width, p.y - h, p.x + width, p.y + 2 * h
        if t == "MTEXT":
            p, h = e.dxf.insert, e.dxf.get("char_height", 0.0) or 0.0
            width = e.dxf.get("width", 0.0) or len(e.text or "") * h
            return p.x - width, p.y - 4 * h, p.x + width, p.y + 4 * h
        if t == "SPLINE":
            pts = list(e.control_points) or list(e.fit_points)
            if pts:
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                return min(xs), min(ys), max(xs), max(ys)
        if t == "ELLIPSE":
            c, m = e.dxf.center, e.dxf.major_axis
            r = (m.x ** 2 + m.y ** 2) ** 0.5
            return c.x - r, c.y - r, c.x + r, c.y + r
        if t == "HATCH":
            xs, ys = [], []
            for path in e.paths:
                for v in getattr(path, "vertices", None) or ():
                    xs.append(v[0])
                    ys.append(v[1])
                for edge in getattr(path, "edges", None) or ():
                    for name in ("start", "end", "center"):
                        q = getattr(edge, name, None)
                        if q is not None:
                            xs.append(q[0])
                            ys.append(q[1])
            if xs:
                return min(xs), min(ys), max(xs), max(ys)
    except Exception:  # noqa: BLE001
        return None
    return None


class Plan:
    """The drawing's lines, at any depth, around the pieces of plan to be
    looked at -- in its own colours on black, as AutoCAD shows it."""

    def __init__(self, dxf: Path, boxes: list[tuple[float, float, float, float]], metre: float, check=None):
        import ezdxf
        from ezdxf import bbox, disassemble

        self.doc = ezdxf.readfile(dxf)
        self.cell = CELL_M * metre
        wanted: set[tuple[int, int]] = set()
        for x0, y0, x1, y1 in boxes:
            for i in range(int(x0 // self.cell), int(x1 // self.cell) + 1):
                for j in range(int(y0 // self.cell), int(y1 // self.cell) + 1):
                    wanted.add((i, j))
        self.cells: dict[tuple[int, int], list] = defaultdict(list)
        limit = 40 * self.cell
        for n, e in enumerate(disassemble.recursive_decompose(self.doc.modelspace())):
            if check and n % 20000 == 0:
                check()
            if e.dxftype() in ("ATTDEF", "VIEWPORT", "IMAGE", "WIPEOUT", "POINT"):
                continue
            box = _quick_box(e)
            if box is None:
                try:
                    found = bbox.extents([e], fast=True)
                except Exception:  # noqa: BLE001 -- what cannot be measured is not drawn
                    continue
                if not found.has_data:
                    continue
                box = (found.extmin.x, found.extmin.y, found.extmax.x, found.extmax.y)
            if box[2] - box[0] > limit or box[3] - box[1] > limit:
                continue                      # a sheet frame, a grid line across the plan
            cells = [(i, j) for i in range(int(box[0] // self.cell), int(box[2] // self.cell) + 1)
                     for j in range(int(box[1] // self.cell), int(box[3] // self.cell) + 1)]
            for c in cells:
                if c in wanted:
                    self.cells[c].append((e, box))

    def picture(self, x0: float, y0: float, x1: float, y1: float, px: int) -> bytes:
        from ezdxf.addons.drawing import Frontend, RenderContext, layout
        from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration
        from ezdxf.addons.drawing.pymupdf import PyMuPdfBackend
        from ezdxf.math import BoundingBox2d

        seen, entities = set(), []
        for i in range(int(x0 // self.cell), int(x1 // self.cell) + 1):
            for j in range(int(y0 // self.cell), int(y1 // self.cell) + 1):
                for e, box in self.cells.get((i, j), ()):
                    if id(e) in seen or box[2] < x0 or box[0] > x1 or box[3] < y0 or box[1] > y1:
                        continue
                    seen.add(id(e))
                    entities.append(e)
        backend = PyMuPdfBackend()
        Frontend(RenderContext(self.doc), backend,
                 config=Configuration(background_policy=BackgroundPolicy.BLACK)).draw_entities(entities)
        side_mm = 300.0
        return backend.get_pixmap_bytes(layout.Page(side_mm, side_mm, layout.Units.mm), fmt="png",
                                        dpi=int(px / (side_mm / 25.4)),
                                        render_box=BoundingBox2d([(x0, y0), (x1, y1)]))


def _windows(labels: list[tuple[str, float, float]], metre: float) -> list[dict]:
    """The labels grouped into pieces of plan: each label joins the first
    piece it fits in (no wider than WINDOW_M either way), so labels side by
    side are looked at together; each piece seen with MARGIN_M around it."""
    size, margin = WINDOW_M * metre, MARGIN_M * metre
    groups: list[list] = []
    for label in sorted(labels, key=lambda m: (m[1], m[2])):
        for g in groups:
            xs, ys = [m[1] for m in g] + [label[1]], [m[2] for m in g] + [label[2]]
            if max(xs) - min(xs) <= size and max(ys) - min(ys) <= size:
                g.append(label)
                break
        else:
            groups.append([label])
    out = []
    for members in groups:
        xs, ys = [m[1] for m in members], [m[2] for m in members]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        half = max((max(xs) - min(xs)) / 2 + margin, (max(ys) - min(ys)) / 2 + margin, size / 2)
        out.append({"box": (cx - half, cy - half, cx + half, cy + half), "labels": members})
    return out


def _picture(plan: Plan, window: dict) -> bytes:
    x0, y0, x1, y1 = window["box"]
    img = Image.open(io.BytesIO(plan.picture(x0, y0, x1, y1, IMAGE_PX))).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    r = max(10, int(w / 90))
    try:
        font = ImageFont.load_default(size=max(18, int(w / 50)))
    except TypeError:                   # an older Pillow: its one small font
        font = ImageFont.load_default()
    for n, (_iid, x, y) in enumerate(window["labels"], 1):
        px, py = (x - x0) / (x1 - x0) * w, (y1 - y) / (y1 - y0) * h
        draw.ellipse((px - r, py - r, px + r, py + r), outline=(255, 40, 40), width=3)
        draw.text((px + r + 3, py - 2 * r - 4), str(n), fill=(255, 40, 40), font=font)
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def _ask(project_id: int, png: bytes, sha: str, window: dict, budget, drawing: str) -> dict:
    s = get_settings()
    db = SessionLocal()
    try:
        x0, y0, _x1, _y1 = window["box"]
        session = assist.AssistSession(db=db, project_id=project_id,
                                       document_sha256=f"{sha}:visual:{x0:.1f},{y0:.1f}",
                                       budget=budget, provider=get_provider())
        parts = [ImagePart("the plan, the labels ringed and numbered", png),
                 TextPart("labels", f"Drawing: {drawing}\n" + "\n".join(
                     f"{n}: {iid.split('|')[-1]}" for n, (iid, _x, _y) in enumerate(window["labels"], 1)))]
        result = assist.call_task(session, TASK, SYSTEM, parts, SCHEMA, 1500, prompt_version=PROMPT_VERSION,
                                  model=s.drawing_review_model, effort=s.drawing_review_effort, exact_model=True,
                                  timeout_s=s.drawing_review_timeout_s)
        db.commit()
        if result.data is None:
            return {"error": result.error or "no answer"}
        return {"answers": result.data.get("labels") or []}
    finally:
        db.close()


def check(db, project, sources: list[dict], *, progress=None, check=None) -> int:
    """Look at the damper labels of every smoke management and ventilation
    drawing read, on the drawing; each source's `visual` is filled in place.
    Returns how many labels were looked at."""
    from app.interfaces.service import cache_folder
    from app.review import service as review

    s = get_settings()
    if not s.ai_enabled:
        return 0                        # no model to look: the labels are scheduled as read
    looked = 0
    for src in sources:
        labels = wanted(src)
        if not labels:
            continue
        old = src.get("visual") or {}
        expected = {item_id(it) for it in labels}
        answered = set((old.get("items") or {}).keys())
        if (old.get("version") == VERSION and old.get("sha256") == src.get("sha256")
                and old.get("status") == "complete" and expected <= answered):
            continue
        dxf = cache_folder(project) / f"{src['sha256'][:24]}.dxf"
        if not dxf.is_file():
            continue
        metre = _METRE.get((src.get("result") or {}).get("units", "m"), 1.0)
        if progress:
            progress(0, 1, f"Reading {src['filename']} to look at its dampers", src["filename"])
        windows = _windows([(item_id(it), it["x"], it["y"]) for it in labels], metre)
        plan = Plan(dxf, [w["box"] for w in windows], metre, check=check)
        items: dict[str, dict] = {}
        budget = review._budget(db, project)
        done = 0
        pool = ThreadPoolExecutor(max_workers=max(1, s.drawing_review_parallel))
        try:
            # the pictures drawn here, one after another (the drawing is not shared across threads);
            # the model asked about them side by side
            futures = {pool.submit(_ask, project.id, _picture(plan, w), src["sha256"], w, budget, src["filename"]): w
                       for w in windows}
            for future in as_completed(futures):
                if check:
                    check()
                w = futures[future]
                try:
                    reply = future.result()
                except Exception as exc:  # noqa: BLE001 -- one look failing is that piece, not the drawing
                    reply = {"error": f"{type(exc).__name__}: {exc}"[:300]}
                done += 1
                if progress:
                    progress(done, len(windows), f"Looking at the dampers of {src['filename']} ({done} of {len(windows)})",
                             src["filename"])
                if "answers" not in reply:
                    continue
                x0, y0, x1, y1 = w["box"]
                by_n = {a["n"]: a for a in reply["answers"]}
                for n, (iid, _px, _py) in enumerate(w["labels"], 1):
                    a = by_n.get(n)
                    if a is None:
                        continue
                    at = None
                    if a["damper"] and 0 <= a["x"] <= 1 and 0 <= a["y"] <= 1:
                        at = [round(x0 + a["x"] * (x1 - x0), 3), round(y1 - a["y"] * (y1 - y0), 3)]
                    items[iid] = {"damper": bool(a["damper"]), "at": at, "what": (a.get("what") or "")[:80],
                                  "confidence": a.get("confidence")}
                    looked += 1
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        missing = sorted(expected - set(items))
        src["visual"] = {"version": VERSION, "sha256": src.get("sha256"), "items": items,
                         "windows": len(windows), "expected": len(expected), "missing": missing,
                         "status": "complete" if not missing else "incomplete"}
    return looked


def verdict(src: dict, it: dict) -> dict | None:
    """What the look said of a label, None when it was not looked at."""
    v = src.get("visual") or {}
    if v.get("version") != VERSION or v.get("sha256") != src.get("sha256"):
        return None
    return (v.get("items") or {}).get(item_id(it))


def near(a: list[float], b: list[float], metre: float) -> bool:
    return math.dist(a, b) <= 0.3 * metre
