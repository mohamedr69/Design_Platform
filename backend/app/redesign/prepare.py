"""Drawings Preparation: the review's accepted devices placed on the plan by
agents working side by side, coordinated, and reviewed before the engineer
approves them (platform owner, 6 October 2026).

  placement     the placement agents (Opus, app.redesign.ai): one change
                each, PREP_AGENT_PARALLEL at once; with the agents off, each
                change goes where the review put it, the drawing's own
                symbol of that device picked by its name;
  coordination  the platform first, room by room: every new detector's room
                filled from its walls (app.redesign.coverage), the coverage
                measured against the detector radius (6.3 m), the new
                detectors moved to the best spots when that covers more or
                takes one off a column, and the spots of any detector the
                room still needs. Where it found something (a column, a gap,
                a move of more than a metre, a room it could not close) the
                coordination agent (Opus) looks at the room and chooses;
                an answer that covers less than the platform's own, or puts
                a device on a column or out of the room, is refused and said.
                Then every new symbol is kept clear of the columns and of the
                others (app.redesign.service.coordinate);
  review        the orchestrator (Opus), one floor at a time, side by side:
                ok, check or reject on each change, a floor summary, the
                questions left;
  gate          the platform's own word on whether the drawing is ready for
                the draftsman: nothing failed, no room short of coverage, no
                device on a column, nothing the orchestrator rejected or asked
                to check, the orchestrator heard.

A detector the coverage adds is a change of its own (source "coverage"),
drawn only once the engineer approves it, as the interface modules are.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf
from PIL import Image, ImageDraw, ImageFont

from app.ai.provider import ImagePart, TextPart, get_prep_provider, prep_ai_on
from app.compliance import assist
from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.database import SessionLocal
from app.ifc import storage
from app.redesign import agents as AG
from app.redesign import coverage as C
from app.review import pages as P

log = logging.getLogger(__name__)

COVERAGE = "coverage"
DETECTOR = re.compile(r"DETECTOR|SMOKE|HEAT|MULTI[-\s]?SENSOR|\bOS\b|\bHD\b|\bSD\b", re.I)
HEAT = re.compile(r"HEAT|\bHD\b|RATE[-\s]?OF[-\s]?RISE|FIXED\s*TEMP", re.I)
MOVE_NOTE_M = 1.0            # a detector moved further than this by the coordination is looked at
OPEN_LOOK_M = 10.0           # the plan shown around a device whose room could not be closed
MARGIN_M = 2.0               # and around a closed room
_COLUMNS: dict[str, object] = {}
_STOP = {"the", "and", "with", "for", "new", "type", "device", "addressable", "conventional", "existing"}


def radius(name: str) -> float:
    s = get_settings()
    return s.prep_heat_radius_m if HEAT.search(name or "") else s.prep_smoke_radius_m


def columns(project, drawing, sha: str | None, *, build: bool = False, check=None):
    """The drawing's columns (app.redesign.coverage): read from the saved
    index, built from the drawing when `build` (in a job)."""
    path = C.columns_path(project, drawing, sha)
    key = str(path)
    if key in _COLUMNS:
        return _COLUMNS[key]
    found = C.load_columns(path)
    if found is None and build and storage.dxf_path(drawing).is_file():
        try:
            found = C.build_columns(storage.dxf_path(drawing), path, get_settings().prep_column_layers, check=check)
        except Exception as exc:  # noqa: BLE001 -- without its columns the plan is coordinated all the same
            log.warning("The drawing's columns could not be read: %s", exc)
            found = None
    if found is not None:
        _COLUMNS[key] = found
    return found


def _name(c: dict) -> str:
    return f"{(c.get('insert') or {}).get('name') or ''} {c.get('device') or ''}"


def is_detector(c: dict) -> bool:
    return ((c.get("system") == "detection" or c.get("source") == COVERAGE) and c.get("action") in ("add", "replace")
            and bool((c.get("insert") or {}).get("seen")) and c.get("status") in ("pending", "proposed", "approved")
            and bool(DETECTOR.search(_name(c))))


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", (text or "").lower()) if w not in _STOP}


# --- placement ---------------------------------------------------------------------------


def guess_symbol(device: str, symbols: list[dict]) -> int:
    """The drawing's symbol whose name shares the most words with the device
    (the most used of those that tie); 0 when none shares one."""
    want = _words(device)
    best = max(((len(want & _words(s["name"])), s["count"], s["id"]) for s in symbols), default=(0, 0, 0))
    return best[2] if best[0] else 0


def fallback_answer(change: dict, symbols: list[dict]) -> dict:
    """Where a change goes with the agents off: the review's point, the
    nearest symbol named like the device to erase, the drawing's own symbol
    of the device to insert."""
    candidate = 0
    if change["action"] in ("remove", "replace") and change["candidates"]:
        words = _words(change["device"])
        named = [k for k in change["candidates"] if words & _words(k["name"])]
        candidate = (named or change["candidates"])[0]["n"]
    box, at = change["box"], change["at"]
    return {"candidate": candidate, "symbol": guess_symbol(change["device"], symbols),
            "x": (at[0] - box[0]) / (box[2] - box[0]), "y": (at[1] - box[1]) / (box[3] - box[1]),
            "rotation": 0, "facing": None, "confidence": "low",
            "note": "Placed at the review's point by the platform (the agents are off)."}


def place(db, project, pdf: str, sha: str, sheets: dict, changes: list[dict], symbols: list[dict], walls,
          budget, row, record, say, check, skip: set | frozenset = frozenset()) -> dict:
    """Every pending change placed (but those in `skip`): by the placement
    agents side by side, or by the platform alone when they are off."""
    from app.redesign import service as R

    s = get_settings()
    todo = [c for c in changes if c["status"] == "pending" and c["id"] not in skip]
    stats = {"total": len(todo), "placed": 0, "failed": 0, "calls": 0, "seconds": 0.0, "by": "agents"}
    if not todo:
        return stats
    if not prep_ai_on():
        stats["by"] = "platform"
        for c in todo:
            answer = fallback_answer(c, symbols)
            c["ai"], c["confidence"], c["note"] = answer, answer["confidence"], answer["note"]
            R._place(c, sheets[c["page"]], symbols, answer, walls)
            stats["placed" if c["status"] == "proposed" else "failed"] += 1
        row.changes = [dict(c) for c in changes]
        db.commit()
        say(len(todo), len(todo), f"Placed {len(todo)} at the review's points (the agents are off)")
        return stats

    parallel = max(1, s.prep_agent_parallel)
    say(0, len(todo), f"{parallel} placement agents ({s.prep_model}) placing {len(todo)} change"
                      f"{'s' if len(todo) != 1 else ''}")

    def timed(change):
        began = time.monotonic()
        reply = R._ask(project.id, pdf, sha, sheets[change["page"]], change, symbols, budget)
        return reply, time.monotonic() - began

    started = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=parallel)
    done = 0
    try:
        futures = {pool.submit(timed, c): c for c in todo}
        for future in as_completed(futures):
            if check:
                check()
            change = futures[future]
            try:
                reply, seconds = future.result()
            except Exception as exc:  # noqa: BLE001 -- one change failing is that change, not the plan
                reply, seconds = {"error": f"{type(exc).__name__}: {exc}"[:300]}, 0.0
            row.calls = (row.calls or 0) + 1
            stats["calls"] += 1
            if "answer" in reply:
                answer = reply["answer"]
                change["ai"] = answer
                change["confidence"], change["note"] = answer["confidence"], answer["note"]
                R._place(change, sheets[change["page"]], symbols, answer, walls)
            else:
                change.update(status="failed", error=reply.get("error"))
            ok = change["status"] == "proposed"
            stats["placed" if ok else "failed"] += 1
            record({"stage": "placement", "label": f"{change['action'].upper()} {change['device'] or change['system_name']}",
                    "floor": change["floor"], "room": change["room"], "state": "done" if ok else "failed",
                    "seconds": round(seconds, 1), "outcome": change.get("confidence") if ok else (change.get("error") or "")[:160]})
            done += 1
            row.changes = [dict(c) for c in changes]
            db.commit()
            say(done, len(todo), f"Placement agents: {done} of {len(todo)} placed ({change['floor']})")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    stats["seconds"] = round(time.monotonic() - started, 1)
    return stats


# --- coordination ------------------------------------------------------------------------


def _set(R, c: dict, sheet: dict, x: float, y: float) -> None:
    """A placed symbol put at (x, y), where the next coordination starts from
    too, and its answer kept with it -- placed again, it stays there."""
    g = sheet["geometry"]
    ins = c["insert"]
    dx, dy = ins.get("offset") or [ins["seen"][0] - ins["model"][0], ins["seen"][1] - ins["model"][1]]
    ins["seen"] = [round(x, 4), round(y, 4)]
    ins["placed"] = list(ins["seen"])
    ins["model"] = [round(x - dx, 4), round(y - dy, 4)]
    ins["page"] = R._page(g, x, y)
    box = c.get("box")
    if box and not (box[0] <= ins["page"][0] <= box[2] and box[1] <= ins["page"][1] <= box[3]):
        c["box"] = box = R._box(g, ins["page"], sheet["plan"])
    if box and c.get("ai") is not None:
        c["ai"] = {**c["ai"], "x": (ins["page"][0] - box[0]) / (box[2] - box[0]),
                   "y": (ins["page"][1] - box[1]) / (box[3] - box[1])}


def _square(c: dict) -> tuple[float, float, float, float]:
    x, y = c["insert"]["seen"]
    r = c["insert"].get("radius") or 0.25
    return (x - r, y - r, x + r, y + r)


def _movable(c: dict) -> bool:
    """A new detector the coordination may move: one the engineer has not
    placed or approved, and not a replacement (that takes the old one's spot)."""
    return c["action"] == "add" and not c.get("moved") and c["status"] != "approved"


def rooms(changes: list[dict], sheets: dict, walls, cols) -> list[dict]:
    """The rooms the new detectors are in: one group a room (a device whose
    room could not be closed is a group of its own). With no named
    boundaries, a wall index that is missing or too sparse to close a room
    by leaves every room not measured (M3 P-07), and says so. A wall index
    held for a reason of its own -- the drawing's unit unknown (A-16 decision
    3), MLINE walls the index does not read with a sparse line index (A-16
    decision 4) -- leaves every room not measured whatever else closes it."""
    groups: list[dict] = []
    held = getattr(walls, "held", None) if walls is not None else None
    forced = held in ("units_unknown", "mline_unsupported")
    unmeasurable = forced or ((cols is None or cols.bounds is None)
                              and (walls is None or bool(getattr(walls, "sparse", False))))
    for c in changes:
        if not is_detector(c) or "box" not in c:
            continue
        sheet = sheets.get(c["page"])
        if not sheet or "a" not in (sheet.get("geometry") or {}):
            continue
        x, y = c["insert"]["seen"]
        group = next((g for g in groups if g["page"] == c["page"] and g["room"] is not None and not g["room"].open
                      and g["room"].contains(x, y)), None)
        if group is None:
            group = {"key": f"{c['page']}:{round(x, 1)}:{round(y, 1)}", "page": c["page"], "name": c.get("room") or "",
                     "room": None if forced else C.room_at(walls, cols, x, y), "changes": []}
            if unmeasurable:
                group["index"] = ("missing" if walls is None else walls.held_detail() if forced else "sparse")
            groups.append(group)
        group["changes"].append(c)
    return groups


def propose(group: dict, sheets: dict, occurrences: list[dict], erased: set, cols) -> dict:
    """The platform's coordination of one room, not applied yet: where its
    movable new detectors cover the most, the spots it still needs, and what
    is wrong with it as placed."""
    room, sheet = group["room"], sheets[group["page"]]
    r = min(radius(_name(c)) for c in group["changes"])
    closed = room is not None and not room.open and room.area >= C.MIN_ROOM_M2
    existing = [(o["x"], o["y"]) for o in occurrences
                if closed and o["sheet"] == sheet["name"] and o["handle"] not in erased and DETECTOR.search(o["name"] or "")
                and room.contains(o["x"], o["y"])]
    on_column = [c["id"] for c in group["changes"] if cols is not None and cols.hit(_square(c))]
    out = {"radius": r, "open": not closed, "existing": existing, "moves": {}, "extra": [], "before": None,
           "after": None, "on_column": on_column, "issues": []}
    if not closed:
        out["issues"].append(
            f"the point is in a space of {room.area:.1f} m2 (a shaft or a fixture?): check where it is"
            if room is not None and not room.open and room.mask.any() else
            f"the drawing's wall index is {group['index']}: no room can be closed from it, coverage not measured"
            if room is None and group.get("index") else
            "its room could not be closed from the plan's walls: coverage not measured")
        return out
    movable = [c for c in group["changes"] if _movable(c)]
    fixed = [tuple(c["insert"]["seen"]) for c in group["changes"] if not _movable(c)]
    now = [tuple(c["insert"]["seen"]) for c in movable]
    out["before"] = before = C.measure(room, existing + fixed + now, r)
    if movable:
        spots = C.best_spots(room, existing + fixed, r, count=len(movable))
        trial = C.measure(room, existing + fixed + spots, r) if spots else None
        if trial and (trial["uncovered_m2"] < before["uncovered_m2"] - 0.5 or any(c["id"] in on_column for c in movable)):
            left = list(spots)
            for c in sorted(movable, key=lambda c: c["id"]):
                if not left:
                    break
                spot = min(left, key=lambda p: math.dist(p, c["insert"]["seen"]))
                left.remove(spot)
                out["moves"][c["id"]] = spot
    placed = existing + fixed + [out["moves"].get(c["id"], tuple(c["insert"]["seen"])) for c in movable]
    out["extra"] = C.best_spots(room, placed, r) if not C.measure(room, placed, r)["ok"] else []
    out["after"] = C.measure(room, placed + out["extra"], r)
    far = [cid for cid, spot in out["moves"].items()
           if math.dist(spot, next(c for c in movable if c["id"] == cid)["insert"]["seen"]) > MOVE_NOTE_M]
    if on_column:
        out["issues"].append(f"{len(on_column)} on a column")
    if out["extra"]:
        out["issues"].append(f"needs {len(out['extra'])} more detector{'s' if len(out['extra']) != 1 else ''} "
                             f"for {r:g} m coverage")
    if far:
        out["issues"].append(f"{len(far)} moved more than {MOVE_NOTE_M:g} m for coverage")
    if not out["after"]["ok"]:
        out["issues"].append(f"{out['after']['uncovered_m2']:g} m2 still not covered")
    return out


def _font(size: int):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _view_box(R, group: dict, sheet: dict) -> list[float]:
    g = sheet["geometry"]
    room = group["room"]
    if room is not None and not room.open and room.area >= C.MIN_ROOM_M2:
        x0, y0, x1, y1 = room.bounds()
        m = MARGIN_M
    else:
        x0 = x1 = sum(c["insert"]["seen"][0] for c in group["changes"]) / len(group["changes"])
        y0 = y1 = sum(c["insert"]["seen"][1] for c in group["changes"]) / len(group["changes"])
        m = OPEN_LOOK_M
    a, b = R._page(g, x0 - m, y1 + m), R._page(g, x1 + m, y0 - m)
    plan = sheet["plan"]
    return [max(plan[0], a[0]), max(plan[1], a[1]), min(plan[2], b[0]), min(plan[3], b[1])]


def picture(R, doc: pymupdf.Document, group: dict, sheet: dict, plan: dict, cols, width: int = 1400) -> tuple[bytes, list]:
    """The room for the coordination agent: what is not covered tinted red,
    the columns orange, each detector's circle (grey existing, green new),
    the new devices numbered N1.., the platform's spots lettered S1.."""
    g = sheet["geometry"]
    box = group.get("view") or _view_box(R, group, sheet)
    group["view"] = box
    dpi = P.dpi_for(tuple(box), width)
    image = Image.open(io.BytesIO(P.crop(doc, sheet["index"], tuple(box), dpi))).convert("RGBA")
    scale = dpi / 72.0

    def px(x, y):
        p = R._page(g, x, y)
        return (p[0] - box[0]) * scale, (p[1] - box[1]) * scale

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    r_px = plan["radius"] / g["a"] * scale
    room = group["room"]
    news = [tuple(c["insert"]["seen"]) for c in group["changes"]]
    if room is not None and not plan["open"]:
        half = C.GRID_M / 2 / g["a"] * scale
        for x, y in room.centres(C.uncovered(room, plan["existing"] + news, plan["radius"])):
            X, Y = px(x, y)
            draw.rectangle((X - half, Y - half, X + half, Y + half), fill=(220, 38, 38, 60))
    if cols is not None:
        cx, cy = news[0]
        for c in cols.near(cx, cy, 40):
            (ax, ay), (bx, by) = px(c[0], c[3]), px(c[2], c[1])
            draw.rectangle((ax, ay, bx, by), fill=(234, 88, 12, 170), outline=(154, 52, 18, 255))
    stroke = max(2, image.width // 400)
    for x, y in plan["existing"]:
        X, Y = px(x, y)
        draw.ellipse((X - r_px, Y - r_px, X + r_px, Y + r_px), outline=(100, 116, 139, 200), width=stroke)
    font = _font(max(14, image.width // 60))
    labels = []
    for n, c in enumerate(group["changes"], 1):
        X, Y = px(*c["insert"]["seen"])
        draw.ellipse((X - r_px, Y - r_px, X + r_px, Y + r_px), outline=(22, 163, 74, 220), width=stroke)
        draw.ellipse((X - 6, Y - 6, X + 6, Y + 6), fill=(22, 163, 74, 255))
        draw.text((X + 8, Y - 8), f"N{n}", fill=(21, 128, 61, 255), font=font)
        labels.append((f"N{n}", c))
    spots = []
    for k, (x, y) in enumerate(list(plan["moves"].values()) + plan["extra"], 1):
        X, Y = px(x, y)
        draw.polygon([(X, Y - 9), (X + 9, Y), (X, Y + 9), (X - 9, Y)], fill=(126, 34, 206, 255))
        draw.text((X + 10, Y + 2), f"S{k}", fill=(107, 33, 168, 255), font=font)
        spots.append((f"S{k}", (x, y)))
    image = Image.alpha_composite(image, layer).convert("RGB")
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue(), [labels, spots]


def _ask_coordination(project_id: int, pdf: str, sha: str, group: dict, sheet: dict, plan: dict, cols, budget, R) -> dict:
    """One room put to the coordination agent, in a session of its own."""
    s = get_settings()
    db = SessionLocal()
    doc = pymupdf.open(pdf)
    try:
        png, (labels, spots) = picture(R, doc, group, sheet, plan, cols)
        session = assist.AssistSession(db=db, project_id=project_id, document_sha256=f"{sha}:coord:{group['key']}",
                                       budget=budget, provider=get_prep_provider())
        lines = [f"{n}: {c['action'].upper()} {c['device'] or c['system_name']}"
                 + (" (placed by the engineer)" if c.get("moved") else "")
                 + (" (approved)" if c["status"] == "approved" else "") for n, c in labels]
        measured = ("not measured: the room could not be closed from the walls" if plan["open"] else
                    f"{plan['before']['covered'] * 100:.0f}% covered as placed ({plan['before']['uncovered_m2']:g} m2 not), "
                    f"{plan['after']['covered'] * 100:.0f}% with the platform's spots")
        parts = [ImagePart("the room", png),
                 TextPart("room", f"Floor: {sheet.get('floor') or sheet['name']}; room: {group['name'] or '-'}; "
                                  f"detector radius {plan['radius']:g} m; coverage {measured}; "
                                  f"the platform found: {'; '.join(plan['issues']) or 'nothing'}"),
                 TextPart("numbered devices", "\n".join(lines)),
                 TextPart("lettered spots", "\n".join(n for n, _p in spots) or "none")]
        result = assist.call_task(session, AG.COORDINATION_TASK, AG.COORDINATION_SYSTEM, parts, AG.COORDINATION_SCHEMA,
                                  1500, prompt_version=AG.COORDINATION_VERSION, model=s.prep_model, effort=s.prep_effort,
                                  exact_model=True, timeout_s=s.drawing_review_timeout_s, accept=AG.coordination_problem)
        db.commit()
        if result.data is None:
            return {"error": result.error or "no answer"}
        return {"answer": AG.read_coordination(result.data, {n for n, _c in labels}, {n for n, _p in spots}),
                "labels": labels, "spots": dict(spots)}
    finally:
        doc.close()
        db.close()


def _decide(R, group: dict, sheet: dict, plan: dict, reply: dict | None, cols) -> tuple[dict, list, dict]:
    """(each device's final point and why, the extra spots, what was refused):
    the agent's answer where the plan bears it out, else the platform's."""
    platform = {c["id"]: (plan["moves"].get(c["id"]), "platform") for c in group["changes"]}
    extra = list(plan["extra"])
    refused: dict = {}
    if not reply or "answer" not in reply:
        return platform, extra, refused
    answer, labels, spots = reply["answer"], dict(reply["labels"]), reply["spots"]
    g, box, room = sheet["geometry"], group["view"], group["room"]
    chosen: dict = {}
    for n, c in labels.items():
        d = answer["devices"].get(n)
        if d is None:
            chosen[c["id"]] = platform[c["id"]]
            continue
        point = None
        if d["decision"] == "spot":
            point = spots[d["spot"]]
        elif d["decision"] == "point":
            point = tuple(R._model(g, box[0] + d["x"] * (box[2] - box[0]), box[1] + d["y"] * (box[3] - box[1])))
        if point is not None:
            r = c["insert"].get("radius") or 0.25
            if cols is not None and cols.hit((point[0] - r, point[1] - r, point[0] + r, point[1] + r)):
                refused[c["id"]] = f"{n}: the agent's point is on a column"
                point = plan["moves"].get(c["id"])
            elif room is not None and not plan["open"] and not room.contains(*point):
                refused[c["id"]] = f"{n}: the agent's point is out of the room"
                point = plan["moves"].get(c["id"])
        elif c["id"] in plan["on_column"]:
            refused[c["id"]] = f"{n}: kept on a column by the agent: the platform's spot taken"
            point = plan["moves"].get(c["id"])
        chosen[c["id"]] = (point, "agent" if c["id"] not in refused else "platform")
        if d.get("reason"):
            c["_reason"] = d["reason"]
    agent_extra = [spots[s] for s in answer["extra"]]
    if plan["open"]:
        return chosen, agent_extra, refused
    r = plan["radius"]
    placed = plan["existing"] + [chosen[c["id"]][0] or tuple(c["insert"]["seen"]) for c in group["changes"]]
    ours = plan["after"]
    theirs = C.measure(room, placed + agent_extra, r)
    if theirs["uncovered_m2"] > ours["uncovered_m2"] + max(1.0, 0.01 * ours["area_m2"]):
        refused["room"] = (f"the agent's layout left {theirs['uncovered_m2']:g} m2 not covered, the platform's "
                           f"{ours['uncovered_m2']:g} m2: the platform's kept")
        return platform, extra, refused
    return chosen, agent_extra, refused


def _extra_change(R, group: dict, sheet: dict, point, occurrences, top, symbols, plan) -> dict:
    """A detector the room's coverage needs: a change of its own, drawn only
    once the engineer approves it."""
    template = group["changes"][0]
    g = sheet["geometry"]
    at = R._page(g, *point)
    cid = "cov:" + hashlib.sha1(f"{sheet['index']}|{point[0]:.1f}|{point[1]:.1f}".encode()).hexdigest()[:12]
    finding = {"id": cid, "page": sheet["index"], "sheet": sheet["name"], "floor": template["floor"],
               "room": template["room"], "system": "detection", "system_name": template["system_name"],
               "action": "add", "device": template["device"],
               "instruction": f"Add {template['device'] or 'a detector'}: the room needs it for {plan['radius']:g} m coverage",
               "at": at}
    c = R._prepare(finding, sheet, occurrences, top)
    if "box" not in c:
        return c
    box = c["box"]
    answer = {"candidate": 0, "symbol": (template.get("insert") or {}).get("symbol") or 0,
              "x": (at[0] - box[0]) / (box[2] - box[0]), "y": (at[1] - box[1]) / (box[3] - box[1]),
              "rotation": 0, "facing": None, "picked": True, "confidence": "high",
              "note": f"Added for the room's {plan['radius']:g} m coverage."}
    R._place(c, sheet, symbols, answer, None)
    c.update(ai=answer, source=COVERAGE, status="proposed", confidence="high", note=answer["note"])
    return c


def coordinate(db, project, pdf: str, sha: str, sheets: dict, changes: list[dict], symbols: list[dict], walls, cols,
               occurrences: list[dict], top, budget, row, record, say, check, settled: dict[str, dict]) -> tuple[list, dict]:
    """The coordination of the placed devices (module docstring); returns the
    changes (with any detector the coverage adds) and what it did."""
    from app.redesign import service as R

    s = get_settings()
    erased = {(c.get("remove") or {}).get("handle") for c in changes if c.get("remove")}
    groups = rooms(changes, sheets, walls, cols)
    stats = {"rooms": len(groups), "issues": 0, "agent_rooms": 0, "agent_calls": 0, "moved": 0, "added": 0,
             "refused": 0, "open_rooms": 0, "gaps_left": 0, "columns": len(cols) if cols is not None else None,
             "wall_index": index_state(walls, cols)}
    plans = {}
    say(0, max(1, len(groups)), f"Coordination: measuring {len(groups)} room{'s' if len(groups) != 1 else ''} "
                                f"against the detector radius")
    for n, group in enumerate(groups, 1):
        if check and n % 10 == 0:
            check()
        plans[group["key"]] = propose(group, sheets, occurrences, erased, cols)
    due = [g for g in groups if plans[g["key"]]["issues"]]
    stats["issues"] = len(due)
    replies: dict[str, dict] = {}
    if due and prep_ai_on():
        say(0, len(due), f"Coordination agents ({s.prep_model}) on {len(due)} room{'s' if len(due) != 1 else ''}")
        pool = ThreadPoolExecutor(max_workers=max(1, s.prep_agent_parallel))
        try:
            def timed(group):
                began = time.monotonic()
                reply = _ask_coordination(project.id, pdf, sha, group, sheets[group["page"]], plans[group["key"]],
                                          cols, budget, R)
                return reply, time.monotonic() - began

            futures = {pool.submit(timed, g): g for g in due}
            for k, future in enumerate(as_completed(futures), 1):
                if check:
                    check()
                group = futures[future]
                try:
                    reply, seconds = future.result()
                except Exception as exc:  # noqa: BLE001 -- the platform's coordination stands for that room
                    reply, seconds = {"error": f"{type(exc).__name__}: {exc}"[:300]}, 0.0
                replies[group["key"]] = reply
                row.calls = (row.calls or 0) + 1
                stats["agent_calls"] += 1
                record({"stage": "coordination", "label": f"Room {group['name'] or '(unnamed)'}",
                        "floor": group["changes"][0]["floor"], "room": group["name"],
                        "state": "done" if "answer" in reply else "failed", "seconds": round(seconds, 1),
                        "outcome": "; ".join(plans[group["key"]]["issues"])[:160] if "answer" in reply
                        else (reply.get("error") or "")[:160]})
                db.commit()
                say(k, len(due), f"Coordination agents: {k} of {len(due)} rooms")
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
    extras: list[dict] = []
    summaries = []
    for group in groups:
        plan, sheet = plans[group["key"]], sheets[group["page"]]
        reply = replies.get(group["key"])
        if reply is not None and "view" not in group:
            group["view"] = _view_box(R, group, sheet)
        chosen, extra, refused = _decide(R, group, sheet, plan, reply, cols) if reply else (
            {c["id"]: (plan["moves"].get(c["id"]), "platform") for c in group["changes"]}, list(plan["extra"]), {})
        stats["refused"] += len(refused)
        if reply and "answer" in reply:
            stats["agent_rooms"] += 1
        for c in group["changes"]:
            point, by = chosen.get(c["id"], (None, "platform"))
            reason = c.pop("_reason", None)
            if point is not None and math.dist(point, c["insert"]["seen"]) > 0.05:
                was = list(c["insert"]["seen"])
                _set(R, c, sheet, *point)
                stats["moved"] += 1
                c["coordination"] = {"by": by, "moved_m": round(math.dist(was, point), 2),
                                     "reason": reason or ("off a column" if c["id"] in plan["on_column"]
                                                          else f"best spot for {plan['radius']:g} m coverage"),
                                     "refused": refused.get(c["id"]) or refused.get("room")}
            elif reason or c["id"] in refused:
                c["coordination"] = {"by": by, "moved_m": 0, "reason": reason, "refused": refused.get(c["id"])}
        for point in extra:
            new = _extra_change(R, group, sheet, point, occurrences, top, symbols, plan)
            if new["id"] in settled or any(x["id"] == new["id"] for x in extras):
                continue
            new["coordination"] = {"by": "agent" if reply and "answer" in reply and "room" not in refused else "platform",
                                   "moved_m": 0, "reason": f"the room needs it for {plan['radius']:g} m coverage",
                                   "refused": refused.get("room")}
            extras.append(new)
            stats["added"] += 1
        summaries.append({"key": group["key"], "page": group["page"], "floor": group["changes"][0]["floor"],
                          "room": group["name"], "radius": plan["radius"], "open": plan["open"],
                          "issues": plan["issues"], "refused": list(refused.values()),
                          "by": "agent" if reply and "answer" in reply else "platform",
                          "before": plan["before"], "devices": [c["id"] for c in group["changes"]]})
    changes = changes + extras
    say(0, 1, "Coordination: every new symbol kept clear of the columns and of each other")
    R.coordinate(changes, sheets, walls, symbols, cols)
    # the coverage as it is now, every room measured again
    for summary in summaries:
        group = next(g for g in groups if g["key"] == summary["key"])
        members = [c for c in changes if c["id"] in summary["devices"]] + [
            c for c in extras if c["page"] == group["page"] and group["room"] is not None and not group["room"].open
            and c.get("insert") and group["room"].contains(*c["insert"]["seen"])]
        after = annotate_room(group, members, occurrences, sheets, erased, summary["radius"])
        summary["after"] = after
        if summary["open"]:
            stats["open_rooms"] += 1
        elif after and not after["ok"]:
            stats["gaps_left"] += 1
    stats["rooms_detail"] = summaries
    return changes, stats


def annotate_room(group: dict, members: list[dict], occurrences, sheets, erased, r: float) -> dict | None:
    """Each member's room coverage, as placed now, on the change."""
    room, sheet = group["room"], sheets[group["page"]]
    if room is None or room.open or room.area < C.MIN_ROOM_M2:
        for c in members:
            c["coverage"] = {"open": True, "radius": r}
        return None
    existing = [(o["x"], o["y"]) for o in occurrences if o["sheet"] == sheet["name"] and o["handle"] not in erased
                and DETECTOR.search(o["name"] or "") and room.contains(o["x"], o["y"])]
    news = [tuple(c["insert"]["seen"]) for c in members if c.get("insert") and c["status"] != "skipped"]
    m = C.measure(room, existing + news, r)
    for c in members:
        c["coverage"] = {**m, "open": False, "radius": r, "detectors": len(existing) + len(news)}
    return m


def measure_again(changes: list[dict], sheets: dict, walls, cols, occurrences: list[dict]) -> None:
    """Every new detector's room coverage measured again as the changes stand
    (after the engineer moved, skipped or approved one): nothing is moved."""
    erased = {(c.get("remove") or {}).get("handle") for c in changes if c.get("remove")}
    for group in rooms(changes, sheets, walls, cols):
        r = min(radius(_name(c)) for c in group["changes"])
        annotate_room(group, group["changes"], occurrences, sheets, erased, r)


# --- the orchestrator's review -----------------------------------------------------------


def _review_input(R, changes: list[dict], sheet: dict, cols) -> dict:
    g = sheet["geometry"]
    out = []
    for c in changes:
        ins, rem = c.get("insert") or {}, c.get("remove") or {}
        from_review = None
        if ins.get("seen") and c.get("at") and "a" in g:
            from_review = round(math.dist(R._model(g, *c["at"]), ins["seen"]), 1)
        out.append({
            "id": c["id"], "action": c["action"], "device": AG.safe(c.get("device"), 120), "room": AG.safe(c.get("room"), 80),
            "source": c.get("source") or "review", "status": c["status"], "error": AG.safe(c.get("error"), 160) or None,
            "symbol": ins.get("name") if ins.get("block") else ("draftsman draws it" if ins else None),
            "erase": ({"symbol": rem.get("name"), "erasable": rem.get("erasable")} if rem else None),
            "placement_confidence": c.get("confidence"), "placement_note": AG.safe(c.get("note"), 160),
            "metres_from_review_point": from_review, "on_wall": c.get("on_wall"),
            "column_clear": (not cols.hit(_square(c))) if cols is not None and ins.get("seen") else None,
            "coordination": c.get("coordination"), "coverage": c.get("coverage"),
            "instruction": AG.safe(c.get("instruction"), 200)})
    return {"floor": sheet.get("floor") or sheet["name"], "sheet": sheet["name"], "changes": out}


def _ask_review(project_id: int, sha: str, page: int, payload: dict, budget) -> dict:
    s = get_settings()
    db = SessionLocal()
    try:
        session = assist.AssistSession(db=db, project_id=project_id, document_sha256=f"{sha}:review:{page}",
                                       budget=budget, provider=get_prep_provider())
        result = assist.call_task(session, AG.REVIEW_TASK, AG.REVIEW_SYSTEM,
                                  [TextPart("the floor's changes (data)", json.dumps(payload, default=str))],
                                  AG.REVIEW_SCHEMA, 6000, prompt_version=AG.REVIEW_VERSION, model=s.prep_orchestrator_model,
                                  effort=s.prep_effort, exact_model=True, timeout_s=s.drawing_review_timeout_s,
                                  accept=AG.review_problem)
        db.commit()
        if result.data is None:
            return {"error": result.error or "no answer"}
        return {"answer": AG.read_review(result.data, {c["id"] for c in payload["changes"]})}
    finally:
        db.close()


def review(db, project, sha: str, sheets: dict, changes: list[dict], cols, budget, row, record, say, check) -> dict:
    """The orchestrator's review, a floor at a time, side by side (module
    docstring). The interface modules are the schedule's, placed at its
    equipment: they are not reviewed here."""
    from app.redesign import service as R

    s = get_settings()
    by_page: dict[int, list[dict]] = {}
    for c in changes:
        c.pop("check", None)
        if c.get("source") != R.INTERFACE and c["status"] != "skipped" and c["page"] in sheets:
            by_page.setdefault(c["page"], []).append(c)
    out = {"state": "off", "model": s.prep_orchestrator_model, "calls": 0, "floors": []}
    if not by_page:
        out["state"] = "nothing"
        return out
    if not prep_ai_on():
        out["floors"] = [{"page": p, "floor": sheets[p].get("floor") or sheets[p]["name"], "state": "off"} for p in by_page]
        return out
    say(0, len(by_page), f"Orchestrator ({s.prep_orchestrator_model}) reviewing {len(by_page)} floor"
                         f"{'s' if len(by_page) != 1 else ''}")
    payloads = {p: _review_input(R, items, sheets[p], cols) for p, items in by_page.items()}
    pool = ThreadPoolExecutor(max_workers=max(1, min(len(by_page), s.prep_agent_parallel)))
    floors = []
    try:
        def timed(page):
            began = time.monotonic()
            reply = _ask_review(project.id, sha, page, payloads[page], budget)
            return reply, time.monotonic() - began

        futures = {pool.submit(timed, p): p for p in by_page}
        for k, future in enumerate(as_completed(futures), 1):
            if check:
                check()
            page = futures[future]
            try:
                reply, seconds = future.result()
            except Exception as exc:  # noqa: BLE001 -- that floor is left unreviewed, and said
                reply, seconds = {"error": f"{type(exc).__name__}: {exc}"[:300]}, 0.0
            row.calls = (row.calls or 0) + 1
            out["calls"] += 1
            floor = {"page": page, "floor": payloads[page]["floor"], "changes": len(by_page[page])}
            if "answer" in reply:
                answer = reply["answer"]
                for c in by_page[page]:
                    if c["id"] in answer["verdicts"]:
                        c["check"] = answer["verdicts"][c["id"]]
                floor.update(state="done", summary=answer["summary"], open_questions=answer["open_questions"],
                             recommendation=answer["recommendation"], notes=answer["notes"],
                             verdicts={v: sum(1 for x in answer["verdicts"].values() if x["verdict"] == v)
                                       for v in ("ok", "check", "reject")})
            else:
                floor.update(state="failed", reason=(reply.get("error") or "")[:300])
            floors.append(floor)
            record({"stage": "review", "label": f"Floor {floor['floor']}", "floor": floor["floor"], "room": "",
                    "state": floor["state"], "seconds": round(seconds, 1),
                    "outcome": floor.get("recommendation") or floor.get("reason") or ""})
            db.commit()
            say(k, len(by_page), f"Orchestrator: {k} of {len(by_page)} floors reviewed")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    out["floors"] = sorted(floors, key=lambda f: f["page"])
    states = {f["state"] for f in floors}
    out["state"] = "done" if states == {"done"} else ("partial" if "done" in states else "failed")
    return out


# --- the gate ---------------------------------------------------------------------------------


def index_state(walls, cols) -> dict:
    """The drawing's wall and boundary indexes as the gate reads them: held
    "not measured" for a reason of the index's own (A-16 decisions 3 and 4)
    or not -- what the index's report says, never a guess."""
    held = getattr(walls, "held", None) if walls is not None else None
    out = {"walls": "missing" if walls is None else (held or "measured"),
           "columns": None if cols is None else ((getattr(cols, "report", None) or {}).get("held") or "measured")}
    if held in ("units_unknown", "mline_unsupported"):
        out["detail"] = walls.held_detail()
    report = getattr(walls, "report", None) or {}
    for key in ("mline_unsupported", "mesh_not_read"):
        if report.get(key):
            out[key] = {k: v for k, v in report[key].items() if k != "layers"}
    if report.get("units"):
        out["units"] = {k: report["units"].get(k) for k in ("unit", "factor_to_m", "known", "insunits")}
    return out


def gate(changes: list[dict], coordination: dict, reviewed: dict, cols) -> dict:
    """Whether the drawing is ready for the draftsman, by the platform's own
    count -- never the agents' word alone."""
    from app.redesign import service as R

    mine = [c for c in changes if c.get("source") != R.INTERFACE and c["status"] != "skipped"]
    reasons = []
    index = coordination.get("wall_index") or {}
    if index.get("walls") in ("units_unknown", "mline_unsupported"):
        # A-16 decisions 3 and 4: the drawing is not measured, and says why
        reasons.append(f"the drawing's wall index is {index.get('detail') or index['walls']}: "
                       "coverage and wall placement not measured")
    elif index.get("columns") == "units_unknown":
        reasons.append("the drawing's columns and boundaries are not measured, units unknown")
    failed = sum(1 for c in mine if c["status"] == "failed")
    if failed:
        reasons.append(f"{failed} change{'s' if failed != 1 else ''} could not be placed")
    on_column = sum(1 for c in mine if (c.get("insert") or {}).get("seen") and cols is not None and cols.hit(_square(c), 0.0))
    if on_column:
        reasons.append(f"{on_column} device{'s' if on_column != 1 else ''} still on a column")
    if coordination.get("gaps_left"):
        reasons.append(f"{coordination['gaps_left']} room{'s' if coordination['gaps_left'] != 1 else ''} short of "
                       "detector coverage")
    if coordination.get("open_rooms"):
        reasons.append(f"{coordination['open_rooms']} room{'s' if coordination['open_rooms'] != 1 else ''} whose "
                       "coverage could not be measured (no closed walls)")
    added = sum(1 for c in changes if c.get("source") == COVERAGE and c["status"] == "proposed")
    if added:
        reasons.append(f"{added} detector{'s' if added != 1 else ''} added for coverage to approve")
    verdicts = [((c.get("check") or {}).get("verdict")) for c in mine]
    if verdicts.count("reject"):
        reasons.append(f"{verdicts.count('reject')} rejected by the orchestrator")
    if verdicts.count("check"):
        reasons.append(f"{verdicts.count('check')} the orchestrator asks the engineer to check")
    if reviewed["state"] == "off":
        reasons.append("not reviewed by the orchestrator (PREP_AI_ENABLED is off)")
    elif reviewed["state"] in ("failed", "partial"):
        reasons.append("the orchestrator's review did not finish on every floor")
    unplaced_symbols = sum(1 for c in mine if c.get("placeholder"))
    if unplaced_symbols:
        reasons.append(f"{unplaced_symbols} without a symbol in the drawing (the draftsman draws them)")
    return {"state": "ready" if not reasons else "needs_engineer", "reasons": reasons}


def started_run() -> dict:
    s = get_settings()
    return {"started_at": utc_now().isoformat(), "finished_at": None, "ai": prep_ai_on(), "model": s.prep_model,
            "orchestrator_model": s.prep_orchestrator_model, "parallel": max(1, s.prep_agent_parallel),
            "radius": {"smoke": s.prep_smoke_radius_m, "heat": s.prep_heat_radius_m},
            "stage": "placement", "agents": [], "placement": None, "coordination": None, "review": None, "gate": None}
