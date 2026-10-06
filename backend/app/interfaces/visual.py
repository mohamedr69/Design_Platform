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
a drawing read again unchanged is not looked at again -- unless the read is a
force-fresh one, which looks again and asks the model again (no stored answer).
"""
from __future__ import annotations

import hashlib
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.ai.provider import ImagePart, TextPart, fa_ai_on, get_fa_provider
from app.compliance import assist
from app.core.config import get_settings
from app.database import SessionLocal
from app.interfaces import render

log = logging.getLogger(__name__)
VERSION = 3
PROMPT_VERSION = "interface-dampers-visual-2026-10-05.4"
TASK = "fa_interfaces_visual"
KEYS = ("motorized_smoke_fire_damper",)
DISCIPLINES = ("SM", "HVAC")
WINDOW_M = 10.0          # the piece of plan one look covers
MARGIN_M = 2.5           # and around it
_METRE = {"mm": 1000.0, "cm": 100.0, "m": 1.0, "in": 39.37, "ft": 3.281}

SYSTEM = """You check the dampers of a smoke management / ventilation (HVAC) floor plan for a fire alarm contractor in
the UAE: every motorized, smoke or fire/smoke damper is interfaced to the fire alarm system (a relay module each), so
each one must be found -- and nothing that is not a damper may be counted.

The plan was read for its words. You are shown one or more pictures of pieces of it. Each red ring with a red number
marks a text the reading took for a damper's label (MSD, MFSD, MD, SD, SMD and the like); the numbers run on from one
picture to the next, and the list beside the pictures says which picture each number is in. Look at the drawing around
each one:
- A damper's label names a damper symbol drawn on a duct close to it: a small box or rectangle across the duct, often
  crossed by a diagonal or with an actuator, sometimes joined to the label by a leader.
- Not a damper: a door tag (a code with a number, at a door: "SD 04"), a room or area tag, a smoke detector, a duct
  size or air flow, a note, a legend entry, a schedule.
- Two labels side by side may name two dampers side by side: each label its own damper.

For each number: damper true or false; for a damper the point of ITS damper symbol (x, y as fractions 0..1 of the width
and height of the picture that number is in), else -1, -1; what it is in at most 8 words; your confidence (low whenever
unsure). Answer every number you are given, and only those."""

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


def _on_plan(src: dict, it: dict) -> bool:
    """Whether a label is on a floor plan -- the only place a damper is counted
    from (`service._read_source`): a riser or schematic sheet is not."""
    from app.interfaces import scan, service

    if it["sheet"] == scan.WHOLE:
        return True
    sheets = {s["name"]: s for s in (src.get("result") or {}).get("sheets", [])}
    return service._sheet_kind(sheets.get(it["sheet"])) == "plan"


def _labels(src: dict) -> list[dict]:
    if src.get("discipline") not in DISCIPLINES or src.get("status") != "read":
        return []
    return [it for it in (src.get("result") or {}).get("items", []) if it["key"] in KEYS]


def wanted(src: dict) -> list[dict]:
    """The labels of a reading that are looked at: those on floor plans (F13 --
    a look at a riser's labels is paid for and can change no count)."""
    return [it for it in _labels(src) if _on_plan(src, it)]


def not_looked(src: dict) -> list[dict]:
    """The damper labels not looked at, sheet by sheet, with why: on a sheet
    that is not a floor plan, so never counted on a floor -- reported, not lost."""
    titles = {s["name"]: s.get("title") or "" for s in (src.get("result") or {}).get("sheets", [])}
    by_sheet: dict[str, int] = {}
    for it in _labels(src):
        if not _on_plan(src, it):
            by_sheet[it["sheet"]] = by_sheet.get(it["sheet"], 0) + 1
    return [{"sheet": name, "title": titles.get(name, ""), "labels": n,
             "reason": "not a floor plan (a riser, schematic or outside every sheet): no floor is counted from it"}
            for name, n in sorted(by_sheet.items())]


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


def batch_parts(batch: list[dict], drawing: str) -> list:
    """The pictures of one look call and the list of their numbers: each
    picture's labels numbered on from the last picture's."""
    parts, lines = [], [f"Drawing: {drawing}"]
    for i, b in enumerate(batch, 1):
        first, last = b["start"], b["start"] + len(b["window"]["labels"]) - 1
        parts.append(ImagePart(f"picture {i}: the plan, labels {first} to {last} ringed and numbered", b["png"]))
        lines += [f"{n}: {iid.split('|')[-1]} (picture {i})"
                  for n, (iid, _x, _y) in enumerate(b["window"]["labels"], b["start"])]
    return parts + [TextPart("labels", "\n".join(lines))]


def _ask(project_id: int, batch: list[dict], sha: str, budget, drawing: str, fresh: bool = False) -> dict:
    """One look call for `batch` -- one or more windows ({png, window, start})."""
    s = get_settings()
    db = SessionLocal()
    try:
        corners = ";".join(f"{b['window']['box'][0]:.1f},{b['window']['box'][1]:.1f}" for b in batch)
        session = assist.AssistSession(db=db, project_id=project_id,
                                       document_sha256=f"{sha}:visual:{corners}",
                                       budget=budget, provider=get_fa_provider())
        parts = batch_parts(batch, drawing)
        result = assist.call_task(session, TASK, SYSTEM, parts, SCHEMA, 1500 * len(batch), prompt_version=PROMPT_VERSION,
                                  model=s.drawing_review_model, effort=s.drawing_review_effort, exact_model=True,
                                  timeout_s=s.drawing_review_timeout_s, fresh=fresh)
        db.commit()
        if result.data is None:
            return {"error": result.error or "no answer"}
        return {"answers": result.data.get("labels") or []}
    finally:
        db.close()


def picture_folder(project, sha: str) -> Path:
    """Where a drawing's pictures are kept, raw (before the rings), by the
    drawing's hash and how they are drawn: the finding review shows the same
    pieces of plan again without opening the drawing a second time."""
    from app.interfaces.service import cache_folder

    return cache_folder(project) / "pictures" / f"{sha[:24]}-v{VERSION}-{render.IMAGE_PX}"


def stored_box(box) -> list[float]:
    """A window's box as it is kept with the reading (and names its picture)."""
    return [round(float(v), 3) for v in box]


def picture_name(box) -> str:
    return "_".join(f"{float(v):.3f}" for v in box) + ".png"


def _drawing(project, src: dict, cache_folder) -> Path | None:
    """The DXF the look is drawn from: a DWG's converted copy, by its hash; a
    drawing filed as DXF, itself -- only while it is still the file read."""
    sha = src.get("sha256") or ""
    copy = cache_folder(project) / f"{sha[:24]}.dxf"
    if sha and copy.is_file():
        return copy
    rel = src.get("relative_path") or ""
    if not (sha and rel.lower().endswith(".dxf") and project.source_folder_path):
        return None
    path = Path(project.source_folder_path) / rel
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
    except OSError:
        return None
    return path if digest.hexdigest() == sha else None


def check(db, project, sources: list[dict], *, progress=None, check=None, limits=None, fresh: bool = False) -> int:
    """Look at the damper labels of every smoke management and ventilation
    drawing read, on the drawing; each source's `visual` is filled in place.
    Returns how many labels were looked at.

    The pictures are drawn one window at a time (`render.RenderSession`: a
    child process with a deadline per picture). Stop is checked between
    windows and while each one is drawn, and progress is reported per window.
    A window that could not be drawn is recorded with its reason in
    `visual.unread`: its labels are held, never taken as "no damper".
    `fresh`: a drawing looked at before is looked at again, every window asked
    again (no stored answer reused)."""
    from app.interfaces.service import cache_folder
    from app.review import service as review

    s = get_settings()
    if not fa_ai_on():
        return 0                        # no model to look: the labels stay held for the engineer
    looked = 0
    for src in sources:
        labels = wanted(src)
        if not labels:
            continue
        old = src.get("visual") or {}
        expected = {item_id(it) for it in labels}
        answered = set((old.get("items") or {}).keys())
        if (not fresh and old.get("version") == VERSION and old.get("sha256") == src.get("sha256")
                and old.get("status") == "complete" and expected <= answered):
            continue
        dxf = _drawing(project, src, cache_folder)
        if dxf is None:
            # nothing to draw the look from: said, never skipped silently
            src["visual"] = {"version": VERSION, "sha256": src.get("sha256"), "items": {}, "windows": 0,
                             "expected": len(expected), "missing": sorted(expected),
                             "unread": {iid: "no_drawing_copy: the drawing read is not on this PC any more"
                                        for iid in sorted(expected)},
                             "status": "incomplete"}
            continue
        metre = _METRE.get((src.get("result") or {}).get("units", "m"), 1.0)
        if progress:
            progress(0, 1, f"Opening {src['filename']} to look at its dampers", src["filename"])
        windows = _windows([(item_id(it), it["x"], it["y"]) for it in labels], metre)
        pictures_at = picture_folder(project, src.get("sha256") or "")
        if fresh and pictures_at.is_dir():
            import shutil

            shutil.rmtree(pictures_at, ignore_errors=True)        # a fresh run draws every picture again
        pictures_at.mkdir(parents=True, exist_ok=True)
        per_call = max(1, s.fa_look_windows_per_call)
        items: dict[str, dict] = {}
        unread: dict[str, str] = {}
        budget = review._budget(db, project)
        done = 0
        futures: dict = {}
        pool = ThreadPoolExecutor(max_workers=max(1, s.drawing_review_parallel))

        def take(future) -> None:
            nonlocal done, looked
            batch = futures.pop(future)
            try:
                reply = future.result()
            except Exception as exc:  # noqa: BLE001 -- one look failing is those pieces, not the drawing
                reply = {"error": f"{type(exc).__name__}: {exc}"[:300]}
            done += len(batch)
            if progress:
                progress(done, len(windows), f"Looking at the dampers of {src['filename']} ({done} of {len(windows)})",
                         src["filename"])
            if "answers" not in reply:
                for b in batch:
                    for iid, _px, _py in b["window"]["labels"]:
                        unread.setdefault(iid, f"look_failed: {reply.get('error') or 'no answer'}"[:200])
                return
            by_n = {a["n"]: a for a in reply["answers"]}
            for b in batch:
                x0, y0, x1, y1 = b["window"]["box"]
                for n, (iid, _px, _py) in enumerate(b["window"]["labels"], b["start"]):
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

        pending: list[dict] = []

        def send() -> None:
            if pending:
                futures[pool.submit(_ask, project.id, list(pending), src["sha256"], budget, src["filename"], fresh)] = \
                    list(pending)
                pending.clear()

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
                        raw = pictures.picture(index)
                    except (render.RenderTimeout, render.RenderUnavailable, render.RenderFailed) as exc:
                        reason = {render.RenderTimeout: "render_timeout", render.RenderUnavailable: "render_unavailable",
                                  render.RenderFailed: "render_failed"}[type(exc)]
                        for iid, _px, _py in w["labels"]:
                            unread[iid] = f"{reason}: {exc}"[:200]
                        log.warning("Damper window %s of %s not drawn: %s", index + 1, src["filename"], exc)
                        continue
                    try:
                        (pictures_at / picture_name(stored_box(w["box"]))).write_bytes(raw)
                    except OSError:
                        pass                            # kept for reuse only: the look goes on without it
                    start = sum(len(b["window"]["labels"]) for b in pending) + 1
                    pending.append({"png": render.annotate(raw, w, start=start), "window": w, "start": start})
                    if len(pending) >= per_call:
                        send()
                send()
            for future in as_completed(list(futures)):
                if check:
                    check()
                take(future)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        missing = sorted(expected - set(items))
        src["visual"] = {"version": VERSION, "sha256": src.get("sha256"), "items": items,
                         "windows": len(windows), "expected": len(expected), "missing": missing,
                         "boxes": [stored_box(w["box"]) for w in windows],
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
