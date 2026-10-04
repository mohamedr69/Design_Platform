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

import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.ai.provider import ImagePart, TextPart, get_provider
from app.compliance import assist
from app.core.config import get_settings
from app.database import SessionLocal
from app.interfaces import render

log = logging.getLogger(__name__)
VERSION = 3
PROMPT_VERSION = "interface-dampers-visual-2026-10-04.3"
TASK = "fa_interfaces_visual"
KEYS = ("motorized_smoke_fire_damper",)
DISCIPLINES = ("SM", "HVAC")
WINDOW_M = 10.0          # the piece of plan one look covers
MARGIN_M = 2.5           # and around it
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


def check(db, project, sources: list[dict], *, progress=None, check=None, limits=None) -> int:
    """Look at the damper labels of every smoke management and ventilation
    drawing read, on the drawing; each source's `visual` is filled in place.
    Returns how many labels were looked at.

    The pictures are drawn one window at a time (`render.RenderSession`: a
    child process with a deadline per picture). Stop is checked between
    windows and while each one is drawn, and progress is reported per window.
    A window that could not be drawn is recorded with its reason in
    `visual.unread`: its labels are held, never taken as "no damper"."""
    from app.interfaces.service import cache_folder
    from app.review import service as review

    s = get_settings()
    if not s.ai_enabled:
        return 0                        # no model to look: the labels stay held for the engineer
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
            progress(0, 1, f"Opening {src['filename']} to look at its dampers", src["filename"])
        windows = _windows([(item_id(it), it["x"], it["y"]) for it in labels], metre)
        items: dict[str, dict] = {}
        unread: dict[str, str] = {}
        budget = review._budget(db, project)
        done = 0
        futures: dict = {}
        pool = ThreadPoolExecutor(max_workers=max(1, s.drawing_review_parallel))

        def take(future) -> None:
            nonlocal done, looked
            w = futures.pop(future)
            try:
                reply = future.result()
            except Exception as exc:  # noqa: BLE001 -- one look failing is that piece, not the drawing
                reply = {"error": f"{type(exc).__name__}: {exc}"[:300]}
            done += 1
            if progress:
                progress(done, len(windows), f"Looking at the dampers of {src['filename']} ({done} of {len(windows)})",
                         src["filename"])
            if "answers" not in reply:
                for iid, _px, _py in w["labels"]:
                    unread.setdefault(iid, f"look_failed: {reply.get('error') or 'no answer'}"[:200])
                return
            x0, y0, x1, y1 = w["box"]
            by_n = {a["n"]: a for a in reply["answers"]}
            for n, (iid, _px, _py) in enumerate(w["labels"], 1):
                a = by_n.get(n)
                if a is None:
                    unread.setdefault(iid, "not_answered")
                    continue
                at = None
                if a["damper"] and 0 <= a["x"] <= 1 and 0 <= a["y"] <= 1:
                    at = [round(x0 + a["x"] * (x1 - x0), 3), round(y1 - a["y"] * (y1 - y0), 3)]
                items[iid] = {"damper": bool(a["damper"]), "at": at, "what": (a.get("what") or "")[:80],
                              "confidence": a.get("confidence")}
                looked += 1

        try:
            with render.RenderSession(dxf, [w["box"] for w in windows], metre, check=check,
                                      limits=limits) as pictures:
                for index, w in enumerate(windows):
                    if check:
                        check()
                    # answers already in: take them as they come, so the count moves
                    for future in [f for f in futures if f.done()]:
                        take(future)
                    if progress:
                        progress(done, len(windows), f"Drawing {src['filename']} for its dampers "
                                 f"(window {index + 1} of {len(windows)})", src["filename"])
                    try:
                        png = render.annotate(pictures.picture(index), w)
                    except (render.RenderTimeout, render.RenderUnavailable, render.RenderFailed) as exc:
                        reason = {render.RenderTimeout: "render_timeout", render.RenderUnavailable: "render_unavailable",
                                  render.RenderFailed: "render_failed"}[type(exc)]
                        for iid, _px, _py in w["labels"]:
                            unread[iid] = f"{reason}: {exc}"[:200]
                        log.warning("Damper window %s of %s not drawn: %s", index + 1, src["filename"], exc)
                        continue
                    futures[pool.submit(_ask, project.id, png, src["sha256"], w, budget, src["filename"])] = w
            for future in as_completed(list(futures)):
                if check:
                    check()
                take(future)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        missing = sorted(expected - set(items))
        src["visual"] = {"version": VERSION, "sha256": src.get("sha256"), "items": items,
                         "windows": len(windows), "expected": len(expected), "missing": missing,
                         "unread": {iid: unread.get(iid, "not_answered") for iid in missing},
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
