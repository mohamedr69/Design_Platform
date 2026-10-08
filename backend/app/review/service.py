"""The Drawings Review of a fire alarm IFC drawing: plotted, read, looked at.

The job (`run`, in the IFC worker):
  1. the drawing is plotted to PDF by AutoCAD (app.review.render), once per file;
  2. each PDF page is matched to the drawing's sheet (tab order, checked by its
     title); riser and schematic sheets are left out;
  3. each floor plan's named rooms (app.review.pages) are looked at by the model
     in windows, two windows a call, and the whole sheet once (app.review.ai);
  4. every answer is saved as it comes, so a review stopped part-way keeps what
     it read and goes on from there when started again.

The page reads `build`: per floor, each room and what the model saw for each
system, and the findings -- a system the rules require that the model did not
see, a room it could not tell, what the sheet pass reported -- each for the
engineer to accept or dismiss.
"""
from __future__ import annotations

import dataclasses
import difflib
import hashlib
import json
import logging
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import pymupdf
from sqlalchemy.orm import Session

from app.ai import project_policy
from app.ai.budget import JobBudget, Limits, calls_today
from app.ai.provider import ImagePart, TextPart, get_review_provider
from app.compliance import assist
from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.database import SessionLocal
from app.ifc import storage
from app.ifc.dxf import sheets as S
from app.models import Project, ProjectDrawingReview, ProjectIfcDrawing
from app.review import ai as A
from app.review import pages as P
from app.review import render
from app.review import fls as F
from app.review import geometry as G
from app.review import rulings as R

log = logging.getLogger(__name__)
TASK_WINDOW, TASK_SHEET, TASK_FLS = "fa_drawing_review_window", "fa_drawing_review_sheet", "fa_drawing_review_fls"


def state(db: Session, project: Project, drawing_id: int) -> ProjectDrawingReview:
    row = (db.query(ProjectDrawingReview)
           .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing_id)
           .one_or_none())
    if row is None:
        row = ProjectDrawingReview(project_id=project.id, drawing_id=drawing_id, sheets=[], decisions={})
        db.add(row)
        db.flush()
    return row


# The per-project daily caps of the drawing workflows (rolling 24 hours), each counted on its own tasks only
# (ORCH-053, LC-10): the review's looks, the FA Interfaces damper look, the preparation agents. Settings, so the
# owner sets the numbers; a job still has its own bound (DRAWING_REVIEW_MAX_CALLS).
DAILY_CAPS = {
    "review": ("drawing_review_max_calls_per_project_per_day", (TASK_WINDOW, TASK_SHEET, TASK_FLS)),
    "fa_visual": ("fa_visual_max_calls_per_project_per_day", ("fa_interfaces_visual",)),
    "prep": ("prep_max_calls_per_project_per_day", ("fa_drawing_redesign", "fa_prep_coordination",
                                                    "fa_prep_orchestrator")),
}


def _budget(db: Session, project: Project, feature: str = "review") -> JobBudget:
    s = get_settings()
    setting, tasks = DAILY_CAPS[feature]
    limits = dataclasses.replace(
        Limits.from_settings(), max_input_tokens_per_task=80_000, max_output_tokens_per_task=8_000,
        max_calls_per_document=s.drawing_review_max_calls, max_calls_per_project_per_day=getattr(s, setting),
        max_elapsed_s_per_job=s.drawing_review_max_elapsed_s, max_cost_per_job=s.drawing_review_max_cost)
    return JobBudget(limits=limits, calls_today_before=calls_today(db, project.id, tasks=tasks))


def _match_pages(doc: pymupdf.Document, drawing: ProjectIfcDrawing) -> list[dict]:
    """Each page with the sheet it is: the drawing's sheets in tab order, as
    the layouts plot; checked by the sheet's title in the page's text."""
    known = (drawing.meta or {}).get("sheets") or []
    out = []
    for index in range(doc.page_count):
        text = " ".join(doc[index].get_text().upper().split())
        sheet = known[index] if index < len(known) else None
        title = (sheet or {}).get("title") or ""
        if sheet is None or (title and " ".join(title.upper().split()) not in text):
            sheet = next((s for s in known if s.get("title") and " ".join(s["title"].upper().split()) in text), None)
        title = (sheet or {}).get("title") or ""
        kind = (sheet or {}).get("kind") or ("diagram" if S.DIAGRAM.search(text[:2000]) else "plan")
        out.append({"index": index, "name": (sheet or {}).get("name") or f"Page {index + 1}", "title": title,
                    "kind": kind, "floor": S.identify_floor(title) or title or f"Page {index + 1}",
                    "multiplier": max(1, int((sheet or {}).get("multiplier") or 1))})
    return out


def plan_job(db: Session, project: Project, drawing: ProjectIfcDrawing, pages_wanted: list[int] | None):
    """What a review will look at, without asking the model anything."""
    pdf, sha = render.render(project, drawing)
    doc = pymupdf.open(pdf)
    try:
        pages = _match_pages(doc, drawing)
        sheets = []
        for p in pages:
            if p["kind"] != "plan" or (pages_wanted is not None and p["index"] not in pages_wanted):
                continue
            info = P.read(doc, p["index"])
            if not info.rooms:
                continue
            wins = P.windows(info)
            n = 0
            windows = []
            for w in wins:
                rooms = []
                for r in w.rooms:
                    n += 1
                    rooms.append({"id": r.id, "name": r.name, "x": round(r.x, 1), "y": round(r.y, 1), "n": n})
                windows.append({"id": w.id, "box": [round(v, 1) for v in w.box], "rooms": rooms})
            sheets.append({**p, "size": [info.width, info.height], "plan": [round(v, 1) for v in info.plan],
                           "legend": [round(v, 1) for v in info.legend] if info.legend else None,
                           "windows": windows})
    finally:
        doc.close()
    _match_fls(project, sheets)
    return pdf, sha, sheets


def _match_fls(project: Project, sheets: list[dict]) -> None:
    """Each IFC floor plan with the FLS page of the same floor, where the
    FLS drawings have one (`sheet["fls"]`)."""
    pages = []
    for path in F.files(project):
        try:
            pdf, _sha = render.render_file(project, path)
            doc = pymupdf.open(pdf)
        except Exception as exc:  # noqa: BLE001 -- an FLS file that cannot be read is named, the rest are used
            log.warning("FLS drawing %s could not be read: %s", path.name, exc)
            continue
        try:
            for page in F.page_floors(doc):
                if page["keys"]:
                    pages.append({**page, "file": path.name, "pdf": str(pdf)})
        finally:
            doc.close()
    for sh in sheets:
        mine = F.keys(sh["title"])
        if not mine:
            continue
        best = max(pages, key=lambda pg: (set(pg["keys"]) == mine, len(set(pg["keys"]) & mine)), default=None)
        if best is not None and set(best["keys"]) & mine:
            sh["fls"] = {"file": best["file"], "pdf": best["pdf"], "page": best["page"], "title": best["title"]}


def run(db: Session, project: Project, drawing_id: int, *, pages_wanted: list[int] | None = None, progress=None,
        check=None, keep_answered: bool = False, fresh: bool = False) -> dict:
    """The review, saved as it goes: Plotting -> Preparing the review inputs ->
    Reviewing -> Saving the results -> Completed. A review no model answered
    is never "done": with no model to call it is `blocked` before anything is
    asked, and when every look fails it is `failed` -- each raising
    `ReviewIncomplete`, with what the review held before (its answers, the
    engineers' decisions) kept as it was."""
    s = get_settings()
    # the project's AI policy first, fail closed: a refused review plots nothing and changes nothing (ORCH-053)
    project_policy.enforce(db, project.id, task=TASK_WINDOW)
    drawing = db.get(ProjectIfcDrawing, drawing_id)
    if drawing is None or drawing.project_id != project.id:
        raise ValueError("That drawing is not this project's")
    row = state(db, project, drawing_id)
    _keep_bases(db, project, drawing, row)
    row.status, row.error, row.started_at, row.finished_at = "running", None, utc_now(), None
    db.commit()
    previous = None              # what the review held before this run: put back when nothing is answered
    answered = 0
    plotted = False

    def say(done: int, total: int, message: str) -> None:
        if progress:
            progress(done, total, message)

    try:
        say(0, 1, "Plotting the drawing with AutoCAD (about 6 minutes, once per revision)")
        pdf, sha, planned = plan_job(db, project, drawing, pages_wanted)
        plotted = True
        say(0, 1, "Plotting completed. Preparing the review inputs: the rooms and windows of each floor plan")
        # the engineers' rulings go with the rules; a new ruling is a new question
        extra, ruled = R.prompt(db)
        version = f"{A.PROMPT_VERSION}+{ruled}"
        sheets, tasks = plan_looks(row, planned, sha, version, pages_wanted, keep_answered=keep_answered,
                                   fresh=fresh)
        total = len(tasks)
        rooms = sum(len(w["rooms"]) for sh in sheets for w in sh["windows"])
        provider = get_review_provider()
        if tasks and not getattr(provider, "ready", True):
            # no model to call: nothing is asked, and nothing the review held is touched
            row.status, row.finished_at = "blocked", utc_now()
            row.error = (f"{NOT_COMPLETED}: no model can be called ({getattr(provider, 'status', '') or 'AI is off'}; "
                         "the drawing review's own switch is DRAWING_REVIEW_AI_ENABLED). "
                         f"Nothing was asked of the {rooms} rooms; the previous answers and the engineers' decisions "
                         "are kept.")
            db.commit()
            raise ReviewIncomplete(row.error)
        previous = (json.loads(json.dumps(row.sheets)), row.source_sha256, row.pdf_path, row.model)
        row.sheets, row.source_sha256, row.model = sheets, sha, s.drawing_review_model
        row.pdf_path = storage.relative(pdf)
        _fit(project, drawing, row, pdf)
        db.commit()

        say(0, max(total, 1), f"Reviewing {rooms} rooms in {total} looks" if total else
            "Nothing new to ask: every room was reviewed before, with the same drawing and rules")
        budget = _budget(db, project)
        by_index = {sh["index"]: sh for sh in sheets}
        done = 0
        errors: list[str] = []
        calls: list[dict] = []                # each look's call, as the route told it
        stopped: str | None = None
        width = max(1, s.drawing_review_parallel)
        pool = ThreadPoolExecutor(max_workers=width)
        waiting = list(tasks)
        running: dict = {}

        def send_more() -> None:
            # a look is sent only once the replies before it were read: a stop keeps the next from going
            while waiting and len(running) < width and not stopped:
                t = waiting.pop(0)
                running[pool.submit(_ask, project.id, str(pdf), sha, by_index[t[1]], t, budget, extra, version,
                                    fresh)] = t

        def replies():
            while running:
                finished, _ = wait(list(running), return_when=FIRST_COMPLETED)
                for future in finished:
                    yield future, running.pop(future)
                send_more()

        try:
            send_more()
            if check:
                check()
            for future, (kind, index, ids, mode) in replies():
                sh = by_index[index]
                try:
                    answer = future.result()
                except project_policy.AiPolicyRefused as exc:
                    # the project was blocked while the review ran: nothing more is sent (ORCH-053)
                    answer = {"error": str(exc)}
                    if not stopped:
                        stopped = f"Stopped: {str(exc).rstrip('.')}"
                        waiting.clear()
                except Exception as exc:  # noqa: BLE001 -- one look that fails is named; the rest go on
                    answer = {"error": str(exc) or type(exc).__name__}
                cli = answer.pop("_cli", None)
                if cli is not None:
                    calls.append({"kind": kind, "floor": sh["floor"], **cli})
                if kind == "window":
                    for w in sh["windows"]:
                        if w["id"] in ids:
                            new = answer.get(w["id"]) or {"status": "failed", "error": answer.get("error")}
                            if _usable(w) and (new.get("status") == "failed"
                                               or (mode == "anew" and new.get("status") != "done")):
                                # what it was answered before stays until it is answered in full anew
                                w["last_error"] = new.get("error") or "answered for only some rooms: kept as was"
                            else:
                                w.update(new)
                    mine = [w for w in sh["windows"] if w["id"] in ids]
                    # answered by this look -- not what a window held before and keeps after a failed re-ask
                    ok = any((answer.get(i) or {}).get("status") in ("done", "incomplete") for i in ids)
                    error = answer.get("error") or next((w.get("error") for w in mine if w.get("error")), None)
                else:
                    prefix = "fls" if kind == "fls" else "sheet"
                    ok = "findings" in answer
                    error = answer.get("error")
                    if ok or not _pass_done(sh, prefix):
                        sh[f"{prefix}_findings"] = answer.get("findings")
                        sh[f"{prefix}_status"] = "done" if ok else "failed"
                        sh[f"{prefix}_model"] = answer.get("model")
                        sh[f"{prefix}_cli"] = cli
                        sh[f"{prefix}_prompt_version"] = version if ok else None
                    sh[f"{prefix}_error"] = error           # a failed re-ask: the pass's findings before stay
                answered += 1 if ok else 0
                if error and not ok:
                    errors.append(str(error))
                done += 1
                row.calls = (row.calls or 0) + 1
                row.sheets = json.loads(json.dumps(sheets))       # a fresh value: written
                db.commit()
                say(done, total, f"Reviewed {done} of {total} ({sh['floor']})")
                why = _stop_reason(error, cli, s)
                if why and not stopped:
                    # asking more would not change it: the looks not yet sent are not sent
                    stopped = f"Stopped after {done} of {total} looks: {why}"
                    waiting.clear()
                    say(done, total, stopped)
                if check:
                    check()
        finally:
            # a stop stops: the looks still waiting are dropped, only the ones under way finish
            pool.shutdown(wait=False, cancel_futures=True)
        say(total, max(total, 1), "Saving the results")
        if tasks and not answered:
            # not one look answered: the review keeps what it held before, and says so
            row.sheets, row.source_sha256, row.pdf_path, row.model = previous
            row.status, row.finished_at = "failed", utc_now()
            row.error = (f"{NOT_COMPLETED}: none of the {total} looks was answered"
                         + (f" ({errors[0][:200]})" if errors else "")
                         + ". The previous answers and the engineers' decisions are kept.")
            db.commit()
            raise ReviewIncomplete(row.error)
        failed = sum(1 for sh in sheets for w in sh["windows"] if w.get("status") == "failed")
        incomplete = sum(1 for sh in sheets for w in sh["windows"] if w.get("status") == "incomplete")
        row.status, row.finished_at = ("stopped" if stopped else "done"), utc_now()
        row.error = " ".join(
            ([stopped + "."] if stopped else [])
            + ([f"{failed} window(s) could not be reviewed."] if failed else [])
            + ([f"{incomplete} window(s) were answered for only some of their rooms."] if incomplete else [])
            + (["Run the review again to retry them."] if failed or incomplete or stopped else [])) or None
        db.commit()
        reviewed = sum(1 for sh in sheets for w in sh["windows"] if _usable(w) for r in w["rooms"]
                       if str(r["n"]) in (w.get("answers") or {}))
        say(total, max(total, 1), "Stopped" if stopped else "Completed")
        # what the route said of the calls: invocations, the turns they reported, the models that answered --
        # a reported turn is not a model request, and the CLI does not count those
        route = {"cli_calls": len(calls), "reported_turns": sum(c.get("turns") or 0 for c in calls),
                 "models": sorted({m for c in calls for m in (c.get("models_used") or {})}),
                 "errors": sorted({c["error"] for c in calls if c.get("error")}),
                 "duration_api_ms": sum(c.get("duration_api_ms") or 0 for c in calls)}
        return {"sheets": len(sheets), "calls": total, "answered": answered, "failed_windows": failed,
                "incomplete_windows": incomplete, "rooms": rooms, "rooms_reviewed": reviewed,
                "stopped": stopped, "fresh": fresh, "route": route}
    except ReviewIncomplete:
        raise
    except Exception as exc:
        from app.services import jobs

        db.rollback()
        row = state(db, project, drawing_id)
        if previous is not None and not answered:
            # stopped or broken before any answer came back: what was there before stays
            row.sheets, row.source_sha256, row.pdf_path, row.model = previous
        row.status = "stopped" if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)) else "failed"
        row.error = None if row.status == "stopped" else (f"{NOT_COMPLETED}: {exc}" if plotted else str(exc))
        row.finished_at = utc_now()
        db.commit()
        raise


def plan_looks(row: ProjectDrawingReview, planned: list[dict], sha: str, version: str,
               pages_wanted: list[int] | None, *, keep_answered: bool = False,
               fresh: bool = False) -> tuple[list[dict], list[tuple]]:
    """The sheets the review will hold and the looks it will ask, from what
    it holds now. A model's answers (a window's, in full or for some of its
    rooms; a floor-plan or FLS pass's) are kept on show whatever happens next.
    They count as current -- not asked again -- only when the drawing (its
    file's hash), the prompt and rules (`version`, per window and pass) and the
    model are the ones they were answered with; `keep_answered` (a
    continuation) takes them as current whatever the prompt; `fresh` (review
    from the beginning) takes none as current. An answer not current is asked
    again in full, and stays as it was until the new one is complete."""
    s = get_settings()
    # the model configuration the answers were asked with (each answer's own model is checked when it comes)
    same_model = row.model in (None, s.drawing_review_model)
    before = {sh["index"]: sh for sh in (row.sheets or []) if row.source_sha256 == sha and same_model}
    sheets = []
    for sh in planned:
        old = before.get(sh["index"])
        if old:
            old_version = old.get("prompt_version")
            kept = {w["id"]: {**w, "prompt_version": w.get("prompt_version") or old_version}
                    for w in old.get("windows", []) if _usable(w)}
            sh["windows"] = [kept.get(w["id"], w) for w in sh["windows"]]
            for prefix in ("sheet", "fls"):
                if prefix == "fls":
                    same = (old.get("fls") or {}).get("file"), (old.get("fls") or {}).get("page")
                    if not sh.get("fls") or same != (sh["fls"]["file"], sh["fls"]["page"]):
                        continue
                if _pass_done(old, prefix):
                    for k in ("findings", "status", "model", "cli"):
                        sh[f"{prefix}_{k}"] = old.get(f"{prefix}_{k}")
                    sh[f"{prefix}_prompt_version"] = old.get(f"{prefix}_prompt_version") or old_version
        sh["prompt_version"] = version
        sheets.append(sh)
    # sheets the engineer did not ask for this time keep what they had
    sheets += [old for idx, old in before.items() if idx not in {sh["index"] for sh in sheets}]
    sheets.sort(key=lambda sh: sh["index"])

    def current(answered_with: str | None) -> bool:
        return not fresh and (keep_answered or answered_with == version)

    tasks = []
    per = max(1, s.drawing_review_windows_per_call)
    for sh in sheets:
        if pages_wanted is not None and sh["index"] not in pages_wanted:
            continue
        left, anew = [], []
        for w in sh["windows"]:
            if _answered(w) and current(w.get("prompt_version")):
                continue                                      # current: reused
            if _usable(w) and not current(w.get("prompt_version")):
                anew.append(w)                                # answered before: asked again in full
            else:
                left.append(w)                                # never answered, or the rooms left of a current one
        for group, mode in ((left, ""), (anew, "anew")):
            for i in range(0, len(group), per):
                tasks.append(("window", sh["index"], [w["id"] for w in group[i:i + per]], mode))
        for prefix in ("sheet", "fls"):
            if prefix == "fls" and not sh.get("fls"):
                continue
            if not (_pass_done(sh, prefix) and current(sh.get(f"{prefix}_prompt_version"))):
                tasks.append((prefix, sh["index"], [], ""))
    return sheets, tasks


def rooms_to_ask(w: dict, anew: bool = False) -> list[dict]:
    """The rooms of a window still to ask: all of them, or -- when a model
    answered some (`incomplete`) -- only the rest; asked anew, all."""
    if _usable(w) and not anew:
        answered = w.get("answers") or {}
        return [r for r in w["rooms"] if str(r["n"]) not in answered]
    return list(w["rooms"])


# Two findings are one change only when all of it agrees: the system, the action, the device, the place
# (in metres, by the plot's own scale -- EP-30880's plans: 1:175 on A3, fitted to half a metre), and the
# recommendation; and their decisions do not disagree. Nearness alone never makes them one.
EQUIVALENT_M = 2.0
POSSIBLE_M = 8.0                   # nearer than this, the same device: possibly one change
SAME_WORDING = 0.6
_SOURCE_ORDER = {"room": 0, "spacing": 1, "other": 2, "sheet": 3, "fls": 4}


def _metres(sh: dict | None, a, b) -> float | None:
    g = (sh or {}).get("geometry") or {}
    if not a or not b or not g.get("a"):
        return None
    return round(g["a"] * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5, 1)


def _same_place(a: str, b: str) -> bool:
    """Described as the same place: the same place named before any detail in
    brackets ("Driveway bend, top-right (...)"), or one names the other's room
    ("LOBBY" / "Main entrance airlock at top of LOBBY"). Wording that is merely
    alike is not the same place ("bend, top-right" / "bend, right-lower")."""
    def words(t: str) -> str:
        return " ".join(re.sub(r"[^a-z0-9 ]", " ", t).split())

    a_full, b_full = words(_norm(a)), words(_norm(b))
    a_head, b_head = (words(_norm(t).split("(")[0]) for t in (a, b))
    if not a_full or not b_full:
        return False
    if a_head and a_head == b_head:
        return True
    short, long = sorted((a_full, b_full), key=len)
    # one names the other's room: a short place name (a room's, at most three words) inside the other
    return (len(short) >= 4 and len(short.split()) <= 3
            and re.search(r"\b" + re.escape(short) + r"\b", long) is not None)


def _in_force(f: dict) -> str | None:
    """The engineer's decision that stands on this finding as it is now."""
    return f["decision"] if f["decision"] in ("accepted", "dismissed") and not f.get("by_ruling") else None


def reconcile_duplicates(findings: list[dict], decisions: dict, sheets: dict) -> tuple[int, list[dict]]:
    """The same change proposed by more than one look (a room's window, the
    floor-plan pass, the FLS pass). Where it is shown to be one change -- see
    above -- one actionable finding stays, with every other source and every
    decision made on them in its `sources`; the one kept is the one an
    engineer's standing decision is on, so no decision is moved onto another
    proposal. Where it may be one change but is not shown to be, both stay,
    each naming the other (`possible_duplicates`) and why it is not
    certain -- the decision endpoint will not accept the second without the
    engineer saying it is a separate change. Two rooms' own findings are
    never one. Returns (findings merged away, the pairs flagged)."""
    live = [f for f in findings if f["action"] != "none" and f["kind"] in _SOURCE_ORDER]
    parent = {f["id"]: f["id"] for f in live}

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    flagged = []
    for i, f in enumerate(live):
        for g in live[i + 1:]:
            if (f["page"], f["system"], f["action"]) != (g["page"], g["system"], g["action"]):
                continue
            if f["kind"] in ("room", "spacing") and g["kind"] in ("room", "spacing"):
                continue                                        # each room's own finding is its own
            distinct = {x for d in (decisions.get(f["id"]), decisions.get(g["id"])) if d
                        for x in d.get("distinct_from") or []}
            if f["id"] in distinct or g["id"] in distinct:
                continue                                        # the engineer said: two changes
            metres = _metres(sheets.get(f["page"]), f.get("at"), g.get("at"))
            same_device = not _norm(f["device"]) or not _norm(g["device"]) or _norm(f["device"]) == _norm(g["device"])
            wording = difflib.SequenceMatcher(None, _norm(f.get("proposal")), _norm(g.get("proposal"))).ratio()
            place = _same_place(f["room"], g["room"])
            fd, gd = _in_force(f), _in_force(g)
            reasons = []
            if not same_device:
                reasons.append(f"device differs ({f['device']} / {g['device']})")
            if metres is None:
                reasons.append("distance unknown (the plot has no scale)")
            elif metres > EQUIVALENT_M:
                reasons.append(f"{metres} m apart")
            if wording < SAME_WORDING:
                reasons.append("recommendations worded differently")
            if fd and gd and fd != gd:
                reasons.append(f"decided differently ({fd} / {gd})")
            if not reasons:
                parent[root(g["id"])] = root(f["id"])
                continue
            if place and metres is not None and metres > EQUIVALENT_M:
                reasons.append("described as the same place, but the points disagree")
            # possibly one change: the same device, near, or described as the same place however far apart
            if same_device and ((metres is not None and metres <= POSSIBLE_M) or place):
                pair = {"a": f["id"], "b": g["id"], "metres": metres, "reasons": reasons}
                flagged.append(pair)
                for x, y in ((f, g), (g, f)):
                    x.setdefault("possible_duplicates", []).append(
                        {"id": y["id"], "kind": y["kind"], "room": y["room"], "metres": metres, "reasons": reasons,
                         "decision": y["decision"]})
    groups: dict[str, list[dict]] = {}
    for f in live:
        groups.setdefault(root(f["id"]), []).append(f)
    merged_away = []
    for members in groups.values():
        if len(members) < 2:
            continue
        standing = {_in_force(m) for m in members} - {None}
        if len(standing) > 1:
            # decided differently somewhere in the group: never one; each pair is the engineer's
            for i, f in enumerate(members):
                for g in members[i + 1:]:
                    reasons = [f"decided differently ({_in_force(f)} / {_in_force(g)})"]
                    flagged.append({"a": f["id"], "b": g["id"], "metres": None, "reasons": reasons})
                    for x, y in ((f, g), (g, f)):
                        x.setdefault("possible_duplicates", []).append(
                            {"id": y["id"], "kind": y["kind"], "room": y["room"], "metres": None,
                             "reasons": reasons, "decision": y["decision"]})
            continue
        # the one kept: the one a standing decision is on, else the most specific source
        keep = min(members, key=lambda m: (_in_force(m) is None, _SOURCE_ORDER[m["kind"]]))
        for m in members:
            if m is keep:
                continue
            keep.setdefault("sources", []).append({
                "id": m["id"], "kind": m["kind"], "room": m["room"], "proposal": m.get("proposal"),
                "device": m["device"], "at": m.get("at"),
                "metres": _metres(sheets.get(m["page"]), keep.get("at"), m.get("at")),
                "decision": _in_force(m), "previous_decision": m.get("previous_decision"),
                "history": (decisions.get(m["id"]) or {}).get("history") or []})
            merged_away.append(m)
    for m in merged_away:
        findings.remove(m)
    # the pairs as they stand after the merging: each side the finding that is on show (one merged away is
    # its kept one's), a pair whose two sides became one dropped, each pair once
    shown = {f["id"]: f for f in findings}
    kept_as = {m["id"]: keep["id"] for keep in findings for m in keep.get("sources") or []}
    final, seen = [], set()
    for pair in flagged:
        a_id, b_id = kept_as.get(pair["a"], pair["a"]), kept_as.get(pair["b"], pair["b"])
        key = tuple(sorted((a_id, b_id)))
        if a_id == b_id or key in seen or a_id not in shown or b_id not in shown:
            continue
        if shown[a_id]["kind"] in ("room", "spacing") and shown[b_id]["kind"] in ("room", "spacing"):
            continue                                        # two rooms' own findings are never one
        seen.add(key)
        final.append({**pair, "a": a_id, "b": b_id})
    for f in live:
        f.pop("possible_duplicates", None)
    for pair in final:
        x, y = shown[pair["a"]], shown[pair["b"]]
        for one, other in ((x, y), (y, x)):
            one.setdefault("possible_duplicates", []).append(
                {"id": other["id"], "kind": other["kind"], "room": other["room"], "metres": pair["metres"],
                 "reasons": pair["reasons"], "decision": other["decision"]})
    return len(merged_away), final


NOT_COMPLETED = "Plotting completed; review has not completed"


class ReviewIncomplete(Exception):
    """The review did not complete -- no model to call, or no look answered:
    its message is for the engineer; the review row already says it."""


def _answered(w: dict) -> bool:
    """A window a model answered in full: done (every room of it answered),
    and not the disabled provider's placeholder (saved as done before the
    placeholder was refused)."""
    return w.get("status") == "done" and w.get("model") != assist.NULL_MODEL


def _usable(w: dict) -> bool:
    """A window with a model's answers to show: in full, or for some of its
    rooms (`incomplete` -- asked again on the next run)."""
    return w.get("status") in ("done", "incomplete") and w.get("model") != assist.NULL_MODEL


def _pass_done(sh: dict, prefix: str) -> bool:
    """The floor's sheet or FLS pass answered by a model. One saved before the
    pass kept its model counts when no window of the floor holds the
    placeholder: the same run asked both."""
    if sh.get(f"{prefix}_status") != "done":
        return False
    model = sh.get(f"{prefix}_model")
    if model is not None:
        return model != assist.NULL_MODEL
    return not any(w.get("model") == assist.NULL_MODEL for w in sh.get("windows", []))


_ENDED = {"blocked": "was blocked", "failed": "failed", "stopped": "was stopped"}


def outcome(row: ProjectDrawingReview | None) -> tuple[str, str | None]:
    """What the review comes to, said as it is: (state, message). `done` only
    when a model answered every part of every plan reviewed; `partial` when it
    answered some; `not_reviewed` when it answered none -- a plot alone is not
    a review. While a run is under way, `running`. A run that was blocked,
    failed or stopped changed nothing a model had answered: the review is what
    those answers come to, and the message says what became of the last
    attempt; with no such answers, the attempt's own state (blocked, failed,
    stopped) is the review's."""
    if row is None or row.status is None:
        return "not_reviewed", None
    if row.status == "running":
        return "running", row.error
    attempt = row.status in ("blocked", "failed", "stopped")
    sheets = row.sheets or []
    windows = [w for sh in sheets for w in sh.get("windows", [])]
    answered = sum(1 for w in windows if _answered(w))
    usable = any(_usable(w) for w in windows)
    if attempt and not usable:
        return row.status, row.error
    if not windows:
        return "not_reviewed", (f"{NOT_COMPLETED}: no floor plan of the drawing names a room to review."
                                if row.pdf_path else None)
    if not usable:
        placeholder = any(w.get("model") == assist.NULL_MODEL for w in windows)
        return "not_reviewed", (f"{NOT_COMPLETED}: no room was answered by a model"
                                + (" -- the earlier run's replies came from the disabled AI provider, not from a "
                                   "model. Run the review again once the drawing review's AI is enabled."
                                   if placeholder else "."))
    plans_done = sum(1 for sh in sheets if _pass_done(sh, "sheet"))
    with_fls = [sh for sh in sheets if sh.get("fls")]
    fls_done = sum(1 for sh in with_fls if _pass_done(sh, "fls"))
    if answered < len(windows) or plans_done < len(sheets) or fls_done < len(with_fls):
        rooms = sum(len(w["rooms"]) for w in windows)
        reviewed = sum(len(w.get("answers") or {}) for w in windows if _usable(w))
        # each unit named: rooms; the review windows the rooms are asked in; the floor-plan and FLS passes
        said = (f"{reviewed} of {rooms} rooms reviewed ({answered} of {len(windows)} review windows answered in "
                f"full; floor-plan passes {plans_done} of {len(sheets)}, FLS passes {fls_done} of {len(with_fls)} "
                "done): run the review again to finish the rest.")
        return "partial", said + (f" {row.error}" if row.error and not attempt else "")
    return "done", None if attempt else row.error


def last_attempt(row: ProjectDrawingReview | None) -> dict | None:
    """The last review run, when it changed nothing a model had answered
    (blocked, failed, stopped): shown apart from what the review holds."""
    if row is None or row.status not in _ENDED:
        return None
    return {"status": row.status, "message": row.error,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None}


# Replies that stop a review: asking further would not change them (no model, the subscription's limit,
# another model answering, a call that took more turns than allowed).
_STOP_KINDS = ("unavailable", "auth", "rate_limit", "quota", "unsupported_model", "model_unverified",
               "model_substituted", "max_turns", "budget")


def _stop_reason(error: str | None, cli: dict | None, s) -> str | None:
    kind = (error or "").split(":", 1)[0].strip()
    if kind in _STOP_KINDS:
        return (error or kind)[:200]
    turns = (cli or {}).get("turns")
    if isinstance(turns, int) and turns > s.drawing_review_max_reported_turns:
        return f"a look reported {turns} turns, more than the {s.drawing_review_max_reported_turns} allowed"
    others = [m for m in (cli or {}).get("models_used") or {} if m != s.drawing_review_model]
    if others:
        return f"other models took part ({', '.join(others)})"
    return None


def _call_account(result) -> dict | None:
    """A call's account for the review's record: the model and what the route
    said (turns, subtype, stop reason, durations, models that took part, its
    own cost estimate); None when nothing was sent (a stored answer)."""
    if result.from_cache or result.meta is None:
        return None
    return {"model": result.model, **{k: v for k, v in result.meta.items() if v is not None}}


def _ask(project_id: int, pdf: str, sha: str, sheet: dict, task: tuple, budget: JobBudget, extra: str = "",
         version: str = A.PROMPT_VERSION, fresh: bool = False) -> dict:
    """One look, in a session of its own (it runs beside others)."""
    s = get_settings()
    kind, index, ids = task[:3]
    anew = len(task) > 3 and task[3] == "anew"
    route = dict(max_turns=s.drawing_review_cli_max_turns, inline_images=s.drawing_review_inline_images,
                 fresh=fresh)
    db = SessionLocal()
    try:
        # re-read per look, before the drawing is cut into pictures: a project blocked mid-run sends nothing more
        project_policy.enforce(db, project_id, task={"fls": TASK_FLS, "sheet": TASK_SHEET}.get(kind, TASK_WINDOW))
    except project_policy.AiPolicyRefused:
        db.close()
        raise
    doc = pymupdf.open(pdf)
    try:
        session = assist.AssistSession(db=db, project_id=project_id, document_sha256=f"{sha}:{index}", budget=budget,
                                       provider=get_review_provider())
        parts: list = []
        if sheet.get("legend"):
            parts.append(ImagePart("legend", P.crop(doc, index, tuple(sheet["legend"]),
                                                    P.dpi_for(tuple(sheet["legend"]), 1100))))
        if kind == "fls":
            plan = tuple(sheet["plan"])
            fls = sheet["fls"]
            fdoc = pymupdf.open(fls["pdf"])
            try:
                fplan = P.read(fdoc, fls["page"]).plan
                fls_png = P.crop(fdoc, fls["page"], fplan, P.dpi_for(fplan, 1700))
            finally:
                fdoc.close()
            parts.append(TextPart("floor", f"{sheet['floor']} -- IFC {sheet['title']} -- FLS {fls['title']}"))
            parts.append(ImagePart("image 1: FLS plan", fls_png))
            parts.append(ImagePart("image 2: IFC plan", P.crop(doc, index, plan, P.dpi_for(plan, 1700))))
            result = assist.call_task(session, TASK_FLS, A.SYSTEM_FLS + extra, parts, A.SHEET_SCHEMA, 3000,
                                      prompt_version=version, model=s.drawing_review_model, effort=s.drawing_review_effort, exact_model=True,
                                      timeout_s=s.drawing_review_timeout_s, **route)
            db.commit()
            if result.data is None or result.model == assist.NULL_MODEL:
                return {"error": result.error or "no answer from a model", "_cli": _call_account(result)}
            return {"findings": A.read_sheet_answer(result.data), "model": result.model, "_cli": _call_account(result)}
        if kind == "sheet":
            plan = tuple(sheet["plan"])
            parts.append(TextPart("floor", f"{sheet['floor']} -- {sheet['title']}"))
            parts.append(ImagePart("floor plan", P.crop(doc, index, plan, P.dpi_for(plan, 1900))))
            names = sorted({r["name"] for w in sheet["windows"] for r in w["rooms"]})
            parts.append(TextPart("rooms named on the plan", ", ".join(names)[:3000]))
            result = assist.call_task(session, TASK_SHEET, A.SYSTEM_SHEET + extra, parts, A.SHEET_SCHEMA, 3000,
                                      prompt_version=version, model=s.drawing_review_model, effort=s.drawing_review_effort, exact_model=True,
                                      timeout_s=s.drawing_review_timeout_s, **route)
            db.commit()
            if result.data is None or result.model == assist.NULL_MODEL:
                return {"error": result.error or "no answer from a model", "_cli": _call_account(result)}
            return {"findings": A.read_sheet_answer(result.data), "model": result.model, "_cli": _call_account(result)}
        wins = [w for w in sheet["windows"] if w["id"] in ids]
        # a partly answered window: only its other rooms; asked anew: all of them
        asked = {w["id"]: rooms_to_ask(w, anew) for w in wins}
        parts.append(TextPart("floor", f"{sheet['floor']} -- {sheet['title']}"))
        for k, w in enumerate(wins, 1):
            box = tuple(w["box"])
            dpi = P.dpi_for(box, 1500)
            scale = dpi / 72.0
            marks = [(r["n"], (r["x"] - box[0]) * scale, (r["y"] - box[1]) * scale) for r in asked[w["id"]]]
            parts.append(ImagePart(f"image {k}", A.numbered(P.crop(doc, index, box, dpi), marks)))
            parts.append(TextPart(f"image {k} rooms", "\n".join(f"{r['n']}: {r['name']}" for r in asked[w["id"]])))
        result = assist.call_task(session, TASK_WINDOW, A.SYSTEM_WINDOW + extra, parts, A.WINDOW_SCHEMA, 6000,
                                  prompt_version=version, model=s.drawing_review_model, effort=s.drawing_review_effort, exact_model=True,
                                  timeout_s=s.drawing_review_timeout_s, **route)
        db.commit()
        account = _call_account(result)
        if result.data is None or result.model == assist.NULL_MODEL:
            failed = {w["id"]: {"status": "failed", "error": result.error or "no answer from a model"} for w in wins}
            return {**failed, "error": result.error or "no answer from a model", "_cli": account}
        numbers = {r["n"] for w in wins for r in asked[w["id"]]}
        answers, other = A.read_window_answer(result.data, numbers)
        out = {}
        for k, w in enumerate(wins, 1):
            # what was answered before stays and the new answers join it; asked anew, the new answers alone
            merged = dict(w.get("answers") or {}) if _usable(w) and not anew else {}
            merged.update({str(r["n"]): dataclasses.asdict(answers[r["n"]]) for r in asked[w["id"]]
                           if r["n"] in answers})
            # every room of the window answered, or the window is not done: the rooms skipped are named
            # and asked again, never kept as reviewed
            missing = [r["name"] for r in w["rooms"] if str(r["n"]) not in merged]
            fresh = [o for o in other if o.get("image") == k or (o.get("image") not in range(1, len(wins) + 1)
                                                                 and k == 1)]
            subset = _usable(w) and not anew
            out[w["id"]] = {
                "status": "incomplete" if missing else "done",
                "error": (f"the model did not answer {len(missing)} of {len(w['rooms'])} rooms: "
                          + ", ".join(missing))[:300] if missing else None,
                "model": result.model,
                "answers": merged,
                # asked about some of its rooms only: what else the model says was not asked for -- kept apart,
                # with where it came from, and applied to no finding and no decision
                "other": list(w.get("other") or []) if subset else fresh,
                "unsolicited": (list(w.get("unsolicited") or []) + [
                    {**o, "asked_rooms": [r["name"] for r in asked[w["id"]]], "model": result.model,
                     "at": utc_now().isoformat()} for o in fresh]) if subset else [],
                "asked_rooms": [r["name"] for r in asked[w["id"]]],
                # where the answer came from: the prompt and rules it was asked under, the call that gave it
                "prompt_version": version, "cli": account, "answered_at": utc_now().isoformat(),
            }
        out["_cli"] = account
        return out
    finally:
        doc.close()
        db.close()


# --- what the page reads ------------------------------------------------------------------------


def _fid(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def _fit(project: Project, drawing: ProjectIfcDrawing, row: ProjectDrawingReview, pdf=None) -> bool:
    """Tie each reviewed sheet's plot to the drawing (`geometry.fit_sheets`),
    so a distance on the page can be had in metres. Returns whether anything
    changed; a review read before this existed gets it the first time it is shown."""
    sheets = [dict(sh) for sh in row.sheets or []]
    if not sheets or all((sh.get("geometry") or {}).get("v") == G.FIT_VERSION for sh in sheets):
        return False
    path = pdf or (storage.absolute(row.pdf_path) if row.pdf_path else None)
    if path is None:
        return False
    try:
        G.fit_sheets(project, drawing, str(path), sheets)
    except Exception as exc:  # noqa: BLE001 -- the review is shown all the same, unmeasured
        log.warning("The plot of %s could not be tied to the drawing: %s", drawing.filename, exc)
        for sh in sheets:
            sh["geometry"] = {"v": G.FIT_VERSION, "error": str(exc)[:200]}
    row.sheets = sheets
    return True


def _driveway_sounder(f: dict) -> bool:
    """A sounder-flasher asked for in a car-park driveway."""
    if f["system"] != "speaker" or f["action"] != "add":
        return False
    where = " ".join(f.get(k) or "" for k in ("room", "room_type", "issue", "instruction"))
    return bool(G.DRIVEWAY.search(where))


def _sounder_spacing(db: Session, drawing: ProjectIfcDrawing, row: ProjectDrawingReview, findings: list[dict]) -> None:
    """A driveway sounder-flasher is asked for only where the nearest one on
    the plan is more than 12 m away: measured, and said on the finding
    (`nearest_m`, `covered` when it is within 12 m)."""
    wanted = [f for f in findings if _driveway_sounder(f)]
    if not wanted:
        return
    geometry = {sh["index"]: sh.get("geometry") for sh in row.sheets or []}
    try:
        devices = G.notifiers(db, drawing)
    except Exception as exc:  # noqa: BLE001
        log.warning("The sounder-flashers of %s could not be placed: %s", drawing.filename, exc)
        return
    for f in wanted:
        found = G.nearest(geometry.get(f["page"]), devices.get(f["sheet"], []), f.get("at"))
        if found is None:
            f["issue"] = f"{f['issue']} (the distance to the nearest sounder-flasher could not be measured)"
            continue
        metres, name = found
        f["nearest_m"] = round(metres, 1)
        if metres <= G.SOUNDER_SPACING_M:
            f["covered"] = (f"The nearest sounder-flasher ({name}) is {metres:.1f} m away, within "
                            f"{G.SOUNDER_SPACING_M:g} m: none is needed here.")
        else:
            f["issue"] = (f"{f['issue']} -- the nearest sounder-flasher is {metres:.1f} m away, more than "
                          f"{G.SOUNDER_SPACING_M:g} m")


def build(db: Session, project: Project, drawing: ProjectIfcDrawing) -> dict:
    row = state(db, project, drawing.id)
    if _fit(project, drawing, row):
        db.commit()
    decisions = row.decisions or {}
    floors, findings = [], []
    stats = {key: {status: 0 for status in A.STATUSES} for key in A.SYSTEMS}
    spaced: list[tuple[dict, dict, bool | None]] = []      # (sheet, room, detector seen) for stairs / lift lobbies
    stair_speakers: list[tuple[dict, dict, bool | None]] = []   # (sheet, room, speaker seen) for staircases
    for sh in row.sheets or []:
        rooms = []
        for w in sh.get("windows", []):
            wbox = w["box"]
            answered = _usable(w)
            # the disabled provider's placeholder is not an answer: the room is still to review
            wstatus = w.get("status", "pending") if answered or w.get("status") != "done" else "pending"
            for r in w["rooms"]:
                answer = (w.get("answers") or {}).get(str(r["n"])) if answered else None
                checks = (answer or {}).get("checks") or {}
                # a room the model skipped in a window it answered is not reviewed, whatever the window says
                rstatus = "done" if answer else ("incomplete" if wstatus in ("done", "incomplete") and answered
                                                 else wstatus)
                room = {"id": r["id"], "name": r["name"], "room_type": (answer or {}).get("room_type", ""),
                        "checks": checks or None, "status": rstatus, "error": w.get("error"),
                        "mark": [r["x"], r["y"]]}
                rooms.append(room)
                is_spaced = bool(A.SPACED.search(r["name"]))
                is_stair = bool(_STAIR.search(r["name"]))
                no_light = bool(_NO_EMERGENCY_LIGHT.search(f"{r['name']} {room['room_type']}"))
                for system, check in checks.items():
                    stats[system][check["status"]] = stats[system].get(check["status"], 0) + 1
                    if system == "detection" and is_spaced:
                        # spacing across floors is checked below, never room by room
                        continue
                    if system == "speaker" and is_stair:
                        # alternate floors, checked across the floors below
                        stair_speakers.append((sh, room, _present(check)))
                        continue
                    if system == "emergency_light" and no_light:
                        # none wanted here: one that is there is to go, none is to be added
                        if _present(check):
                            findings.append(_finding(
                                sh, f"{r['id']}|emergency_light|remove", room=r["name"], room_type=room["room_type"],
                                system="emergency_light", kind="room", action="remove", device="emergency light",
                                instruction=f"Remove the emergency light in {r['name'].title()}: none is required in "
                                            "garbage, ELV or locker rooms",
                                issue=f"An emergency light in {r['name'].title()}, where none is required",
                                seen=check.get("seen", ""), at=_at(wbox, check, (r["x"], r["y"]))))
                        continue
                    action = check.get("action", "none")
                    if action == "none" and check["status"] != "unclear":
                        continue
                    at = _at(wbox, check, (r["x"], r["y"]))
                    findings.append(_finding(
                        sh, f"{r['id']}|{system}", room=r["name"], room_type=room["room_type"], system=system,
                        kind="unclear" if action == "none" else "room", action=action, device=check.get("device", ""),
                        instruction=check.get("instruction") or _default_instruction(action, system, r["name"]),
                        issue=_issue(check["status"], system, r["name"]), seen=check.get("seen", ""), at=at))
                if is_spaced and checks:
                    spaced.append((sh, room, checks.get("detection", {}).get("status") == "present"
                                   if checks.get("detection", {}).get("status") in ("present", "absent") else None))
            for o in w.get("other") or []:
                findings.append(_finding(
                    sh, f"{w['id']}|other|{o['system']}|{o['issue']}", room=o.get("where", ""), room_type="",
                    system=o["system"], kind="other", action=o.get("action", "add"), device=o.get("device", ""),
                    instruction=o.get("instruction") or o["issue"], issue=o["issue"], seen="",
                    at=_at(wbox, o, None)))
        for f in sh.get("sheet_findings") or []:
            findings.append(_finding(
                sh, f"sheet|{f['system']}|{f['issue']}", room=f.get("where", ""), room_type="", system=f["system"],
                kind="sheet", action=f.get("action", "add"), device=f.get("device", ""),
                instruction=f.get("instruction") or f["issue"], issue=f["issue"], seen="", at=_at(sh["plan"], f, None),
                severity=f.get("severity")))
        for f in sh.get("fls_findings") or []:
            findings.append(_finding(
                sh, f"fls|{f['system']}|{f['issue']}", room=f.get("where", ""), room_type="", system=f["system"],
                kind="fls", action=f.get("action", "add"), device=f.get("device", ""),
                instruction=f.get("instruction") or f["issue"], issue=f["issue"], seen="", at=_at(sh["plan"], f, None),
                severity=f.get("severity")))
        windows = sh.get("windows", [])
        floors.append({"page": sh["index"], "sheet": sh["name"], "title": sh["title"], "floor": sh["floor"],
                       "fls": {k: v for k, v in (sh.get("fls") or {}).items() if k != "pdf"} or None,
                       "fls_status": "done" if _pass_done(sh, "fls") else (
                           sh.get("fls_status") if sh.get("fls_status") not in (None, "done") else
                           ("pending" if sh.get("fls") else None)),
                       "multiplier": sh.get("multiplier", 1), "rooms": rooms, "windows": len(windows),
                       "windows_done": sum(1 for w in windows if _answered(w)),
                       "windows_failed": sum(1 for w in windows if w.get("status") == "failed"),
                       "windows_incomplete": sum(1 for w in windows if w.get("status") == "incomplete"),
                       # what a model said that it was not asked: kept, applied to nothing
                       "unsolicited": [{"window": w["id"], **{k: u.get(k) for k in (
                           "system", "where", "issue", "action", "device", "asked_rooms", "model", "at")}}
                           for w in windows for u in w.get("unsolicited") or []],
                       "sheet_status": "done" if _pass_done(sh, "sheet") else (
                           sh.get("sheet_status") if sh.get("sheet_status") not in (None, "done") else "pending")})
    findings += _spacing(spaced)
    findings += _alternate(stair_speakers)
    _sounder_spacing(db, drawing, row, findings)
    ruled = R.not_needed(db)
    for f in findings:
        f["proposal"] = f["instruction"]                 # the model's, before any engineer's wording
        d = decisions.get(f["id"]) or {}
        f["previous_decision"] = None
        if d.get("status") in ("accepted", "dismissed"):
            changed = _changed(d, f, row)
            if changed is not None:
                # the engineer decided on another proposal (or one not shown to be this one): decided
                # again, the earlier decision kept and shown
                f["previous_decision"] = {k: d.get(k) for k in ("status", "note", "instruction", "by", "at")}
                if d.get("basis") is None:
                    # nothing kept of what it was made on, and a review has run since
                    f["previous_decision"].update(changed=[], reason="not_verifiable", message=(
                        "Made before decisions kept their proposal, and the drawing has been reviewed since: "
                        "it cannot be shown to be this proposal."))
                else:
                    f["previous_decision"].update(changed=changed, reason="proposal_changed", message=(
                        "The proposal changed: " + ", ".join(changed) + "."))
                d = {}
        status = d.get("status", "open")
        f["decision"] = "open" if status == "reopened" else status
        f["note"] = d.get("note", "")
        f["by_ruling"] = False
        if d.get("instruction"):
            f["instruction"] = d["instruction"]
        # a driveway sounder-flasher with one within 12 m: not asked for, unless reopened
        if status == "open" and f.get("covered"):
            f["decision"], f["by_ruling"], f["note"] = "dismissed", True, f["covered"]
            continue
        # not needed in this kind of room before: settled here too, unless reopened
        if status == "open" and f["action"] != "none" and f["kind"] in ("room", "spacing"):
            rule = ruled.get((R.room_key(f["room"]), f["system"], f["action"]))
            if rule is not None and rule.finding_id != f["id"]:
                f["decision"], f["by_ruling"] = "dismissed", True
                f["note"] = f"By ruling ({rule.room}): {rule.note}" if rule.note else f"By ruling ({rule.room})"
    # the same change proposed by two looks: one actionable proposal with every source and decision in its
    # history -- or, when that is not shown, the pair flagged for the engineer
    merged_dupes, flagged_pairs = reconcile_duplicates(findings, decisions, {sh["index"]: sh for sh in row.sheets or []})
    actionable = [f for f in findings if f["action"] != "none"]
    rooms_total = sum(len(f["rooms"]) for f in floors)
    reviewed = sum(1 for f in floors for r in f["rooms"] if r["checks"])
    review_state, message = outcome(row)
    if review_state == "done" and not actionable:
        # a review that found nothing to change says so, with how much it read
        unclear = len(findings) - len(actionable)
        message = (f"Review completed: no changes proposed. {reviewed} of {rooms_total} rooms reviewed"
                   + (f"; {unclear} to check by eye" if unclear else "") + ".")
    # the models that actually answered -- the configured one is only what was asked for
    answered_by = sorted({w.get("model") for sh in row.sheets or [] for w in sh.get("windows", [])
                          if _usable(w) and w.get("model")})
    return {
        "drawing": {"id": drawing.id, "filename": drawing.filename, "revision": drawing.revision or "R0"},
        "status": row.status, "error": row.error, "model": row.model or get_settings().drawing_review_model,
        "state": review_state, "state_message": message, "answered_by": answered_by,
        "calls": row.calls or 0,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "floors": floors, "findings": findings, "stats": stats, "merged_duplicates": merged_dupes,
        "possible_duplicate_pairs": flagged_pairs, "last_attempt": last_attempt(row),
        "fls": {"folder": F.FOLDER, "files": [p.name for p in F.files(project)],
                "floors_matched": sum(1 for f in floors if f.get("fls")), "floors": len(floors)},
        "systems": A.SYSTEMS,
        "rules": [{"system": k, "name": A.SYSTEMS[k], "rule": t + (_MEASURED.get(k) or "")} for k, t in A.RULES],
        "rulings": [{"id": r.id, "decision": r.decision, "room": r.room, "system": r.system,
                     "system_name": A.SYSTEMS.get(r.system, r.system), "action": r.action, "device": r.device,
                     "instruction": r.instruction, "note": r.note, "project_id": r.project_id,
                     "at": r.created_at.isoformat() if r.created_at else None} for r in R.listed(db)],
        "counts": {"rooms": rooms_total, "reviewed": reviewed,
                   "open": sum(1 for f in actionable if f["decision"] == "open"),
                   "accepted": sum(1 for f in actionable if f["decision"] == "accepted"),
                   "dismissed": sum(1 for f in actionable if f["decision"] == "dismissed"),
                   "unclear": sum(1 for f in findings if f["action"] == "none" and f["decision"] == "open"),
                   "add": sum(1 for f in actionable if f["action"] == "add"),
                   "remove": sum(1 for f in actionable if f["action"] == "remove"),
                   "replace": sum(1 for f in actionable if f["action"] == "replace")},
    }


# --- the engineer's decisions, kept to the proposal they were made on ----------------------------

# A device point the model gives moves a little from one review to the next; further than this
# (PDF points on the plotted sheet: half an inch) it is another location.
LOCATION_TOLERANCE_PT = 36.0
_SUBSTANCE = ("action", "kind", "system", "device", "room", "recommendation", "location")


def _norm(text) -> str:
    return " ".join(str(text or "").lower().split()).strip(" .;:,")


def substance(f: dict) -> dict:
    """What a finding proposes, as a decision on it is kept against: the
    action, what kind and which system, the device, the room, the model's
    recommendation (its wording, which carries any quantity) and where."""
    at = f.get("at")
    return {"action": f.get("action"), "kind": f.get("kind"), "system": f.get("system"),
            "device": _norm(f.get("device")), "room": _norm(f.get("room")),
            "recommendation": _norm(f.get("proposal", f.get("instruction"))),
            "location": [round(float(v), 1) for v in at] if at else None}


def _changed(d: dict, f: dict, row: ProjectDrawingReview) -> list[str] | None:
    """None when decision `d` stands for finding `f` as it is now; otherwise
    what is not shown to be the same. A decision without its proposal (made
    before they were kept) stands only while no review has run since it."""
    basis = d.get("basis")
    if basis is None:
        at = d.get("at") or ""
        finished = row.finished_at.isoformat() if row.finished_at else ""
        return None if finished and at >= finished else ["decided before the proposal was recorded with it"]
    now = substance(f)
    changed = [k for k in _SUBSTANCE if k != "location" and basis.get(k) != now[k]]
    before, after = basis.get("location"), now["location"]
    if (before is None) != (after is None) or (before and after and (
            (before[0] - after[0]) ** 2 + (before[1] - after[1]) ** 2) ** 0.5 > LOCATION_TOLERANCE_PT):
        changed.append("location")
    return changed or None


def record_decision(decisions: dict, fid: str, record: dict, finding: dict | None = None) -> None:
    """Put the engineer's decision on a finding, with the proposal it was made
    on; the decision it replaces goes into its history, never lost."""
    if finding is not None and record.get("status") in ("accepted", "dismissed"):
        record["basis"] = substance(finding)
    previous = decisions.get(fid)
    if previous:
        record["history"] = (previous.get("history") or []) + [{k: v for k, v in previous.items() if k != "history"}]
    decisions[fid] = record


def _keep_bases(db: Session, project: Project, drawing: ProjectIfcDrawing, row: ProjectDrawingReview) -> None:
    """Before a review replaces its answers: each decision made on the
    answers now shown, but without its proposal (made before they were kept),
    gets that proposal -- so it can still be told apart afterwards."""
    decisions = dict(row.decisions or {})
    missing = {fid for fid, d in decisions.items() if d.get("status") in ("accepted", "dismissed") and not d.get("basis")}
    if not missing:
        return
    kept = 0
    for f in build(db, project, drawing)["findings"]:
        if f["id"] in missing and f["previous_decision"] is None:
            decisions[f["id"]] = {**decisions[f["id"]], "basis": substance(f)}
            kept += 1
    if kept:
        # an engineer may have decided since this was read: write onto the decisions as they are now
        db.refresh(row, attribute_names=["decisions"])
        now = dict(row.decisions or {})
        for fid, d in decisions.items():
            if d.get("basis") and fid in now and not now[fid].get("basis") and now[fid].get("at") == d.get("at"):
                now[fid] = {**now[fid], "basis": d["basis"]}
        row.decisions = now
        db.commit()


_ACTION_WORD = {"add": "Add", "remove": "Remove", "replace": "Replace"}


def _same_key(f: dict) -> tuple | None:
    """What makes two findings the same comment: the same kind of room
    (numbers and punctuation aside, as the rulings compare rooms), the same
    system, action and device. None for a finding with no room to compare."""
    room = R.room_key(f.get("room") or "")
    if not room:
        return None
    device = " ".join(re.sub(r"[^A-Z ]", " ", (f.get("device") or "").upper()).split())
    return room, f["system"], f["action"], device


def same_elsewhere(findings: list[dict], finding: dict) -> list[dict]:
    """The same comment on the drawing's other floors (`_same_key`)."""
    key = _same_key(finding)
    if key is None:
        return []
    return [f for f in findings if f["page"] != finding["page"] and f["id"] != finding["id"] and _same_key(f) == key]
# What the platform measures itself, said with the rule it applies to.
_MEASURED = {"speaker": f" Driveways: a sounder-flasher is asked for only where the nearest one is more than "
                        f"{G.SOUNDER_SPACING_M:g} m away (measured on the drawing by the platform)."}


def _default_instruction(action: str, system: str, room: str) -> str:
    if action == "none":
        return ""
    return f"{_ACTION_WORD[action]} {A.SYSTEMS[system].lower()} in {room.title()}"


def _issue(status: str, system: str, room: str) -> str:
    name = A.SYSTEMS[system].lower()
    return {"absent": f"No {name} in {room.title()}",
            "wrong": f"The {name} in {room.title()} is not what the rules want there",
            "unclear": f"{A.SYSTEMS[system]} in {room.title()} could not be told from the drawing"}.get(status, "")


def _at(box, change: dict, fallback) -> list[float] | None:
    """Where on the page a change is: the model's point in its image, mapped
    back onto the page; else the room's name; else nowhere."""
    x, y = change.get("x", -1), change.get("y", -1)
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and 0 <= x <= 1 and 0 <= y <= 1:
        return [round(box[0] + x * (box[2] - box[0]), 1), round(box[1] + y * (box[3] - box[1]), 1)]
    return [round(fallback[0], 1), round(fallback[1], 1)] if fallback else None


def _finding(sh: dict, key: str, *, room: str, room_type: str, system: str, kind: str, action: str, device: str,
             instruction: str, issue: str, seen: str, at, severity: str | None = None) -> dict:
    box = ([at[0] - 100, at[1] - 100, at[0] + 100, at[1] + 100] if at else list(sh["plan"]))
    return {"id": _fid(sh["index"], key), "page": sh["index"], "floor": sh["floor"], "sheet": sh["name"],
            "room": room, "room_type": room_type, "system": system, "system_name": A.SYSTEMS[system], "kind": kind,
            "action": action, "device": device, "instruction": instruction, "issue": issue, "seen": seen,
            "severity": severity, "at": at, "box": [round(v, 1) for v in box], "mark": at}


_STAIR = re.compile(r"\bSTAIR", re.I)
# Rooms an emergency light is not wanted in (platform owner, 2 October 2026).
_NO_EMERGENCY_LIGHT = re.compile(r"\bGARBAGE\b|\bREFUSE\b|\bTRASH\b|\bELV\b|\bLOCKER", re.I)


def _present(check: dict) -> bool | None:
    """Whether the room has the device, from the model's answer: True, False,
    or None where it could not tell."""
    status = check.get("status")
    if status in ("present", "wrong"):
        return True
    if status in ("absent", "not_required"):
        return False
    return None


def _nice(text: str) -> str:
    """A name in title case with its ordinals as written: "2nd Basement",
    not "2Nd Basement"."""
    return re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), (text or "").title())


def _stair_key(name: str) -> str:
    n = re.sub(r"[^A-Z0-9]", "", name.upper())
    digits = re.search(r"\d+", n)
    return f"STAIR{int(digits.group()) if digits else ''}"


def _alternate(entries: list[tuple[dict, dict, bool | None]]) -> list[dict]:
    """Staircases: a wall-mounted speaker on alternate floors -- one floor
    with, the next without (platform owner, 2 October 2026). Per staircase,
    floors in building order: a floor like the one below it (both with a
    speaker, or both without) is a REMOVE or an ADD on it, each for the
    engineer to confirm -- and judged against the floor below as corrected,
    so a run of empty floors asks for every other one, not each. A typical
    sheet stands for several floors in a row: with or without the speaker,
    it is to show it on alternate floors. A floor the model could not read
    breaks the run."""
    by_key: dict[str, list[tuple[dict, dict, bool | None]]] = {}
    for sh, room, seen in entries:
        by_key.setdefault(_stair_key(room["name"]), []).append((sh, room, seen))
    out = []
    for key, rows in by_key.items():
        rows.sort(key=lambda e: e[0]["index"])
        below: tuple[str, bool] | None = None        # (floor, has a speaker once corrected)
        for sh, room, seen in rows:
            floors = max(1, int(sh.get("multiplier") or 1))
            at = [room["mark"][0], room["mark"][1]]
            name, floor = _nice(room["name"]), _nice(sh["floor"])

            def finding(action: str, device: str, instruction: str, issue: str) -> None:
                out.append(_finding(sh, f"alternate|{key}|{sh['index']}", room=room["name"], room_type="",
                                    system="speaker", kind="spacing", action=action, device=device,
                                    instruction=instruction, issue=issue, seen="", at=at))

            if seen is None:
                below = None
                continue
            if floors > 1:
                finding("remove" if seen else "add", "wall-mounted speaker (alternate floors)",
                        f"{floor} stands for {floors} floors: show the speaker in {name} on alternate floors only"
                        if seen else
                        f"{floor} stands for {floors} floors: add a wall-mounted speaker in {name} on alternate floors",
                        f"A speaker in {name} on every one of {floors} typical floors" if seen else
                        f"No speaker in {name} on any of {floors} typical floors")
                below = None            # which of its floors ends with one is the drawing's to say
                continue
            if below is not None and below[1] == seen:
                if seen:
                    finding("remove", "wall-mounted speaker",
                            f"Delete the speaker in {name} on {floor}: {below[0]} has one; staircase speakers go on "
                            "alternate floors",
                            f"A speaker in {name} on both {below[0]} and {floor}")
                else:
                    finding("add", "wall-mounted speaker",
                            f"Add a wall-mounted speaker in {name} on {floor}: {below[0]} has none; staircase "
                            "speakers go on alternate floors",
                            f"No speaker in {name} on {below[0]} or {floor}")
                below = (floor, not seen)
            else:
                below = (floor, seen)
    return out


def _spacing(spaced: list[tuple[dict, dict, bool | None]]) -> list[dict]:
    """Stairs and lift lobbies: a smoke detector about every 5 floors (23 m),
    not on each -- floors counted in building order, a typical sheet as
    many floors as it stands for. A run of more than 5 floors with none is
    one ADD, placed on the sheet in the middle of the run."""
    def key(name: str) -> str:
        n = re.sub(r"[^A-Z0-9]", "", name.upper())
        digits = re.search(r"\d+", n)
        if "STAIR" in n:
            return f"STAIR{int(digits.group()) if digits else ''}"
        return "FIRELIFTLOBBY" if "FIRE" in n else "LIFTLOBBY"

    by_key: dict[str, list[tuple[dict, dict, bool | None]]] = {}
    for sh, room, seen in spaced:
        by_key.setdefault(key(room["name"]), []).append((sh, room, seen))
    out = []
    for k, entries in by_key.items():
        entries.sort(key=lambda e: e[0]["index"])
        run: list[tuple[dict, dict, int]] = []

        def close():
            floors = sum(m for _sh, _room, m in run)
            if floors > 5:
                sh, room, _m = run[len(run) // 2]
                names = f"{run[0][0]['floor']} to {run[-1][0]['floor']}" if len(run) > 1 else run[0][0]["floor"]
                at = [room["mark"][0], room["mark"][1]]
                out.append(_finding(
                    sh, f"spacing|{k}|{run[0][0]['index']}", room=room["name"], room_type="", system="detection",
                    kind="spacing", action="add", device="smoke detector",
                    instruction=f"Add a smoke detector in {room['name'].title()} on {sh['floor'].title()}: none for "
                                f"{floors} floors ({names.title()}); one is required about every 5 floors (23 m)",
                    issue=f"No smoke detector in {room['name'].title()} for {floors} floors", seen="", at=at))

        for sh, room, seen in entries:
            if seen is True:
                close()
                run = []
            elif seen is False:
                run.append((sh, room, max(1, int(sh.get("multiplier") or 1))))
        close()
    return out


def pages_of(db: Session, project: Project, drawing: ProjectIfcDrawing) -> list[dict]:
    """The drawing's floor-plan sheets, to choose what to review -- from the
    drawing's own sheet list, before anything is plotted."""
    out = []
    for index, sheet in enumerate((drawing.meta or {}).get("sheets") or []):
        if sheet.get("kind") == "plan":
            out.append({"page": index, "sheet": sheet.get("name"), "title": sheet.get("title"),
                        "floor": S.identify_floor(sheet.get("title") or "") or sheet.get("title")})
    return out


def image(project: Project, row: ProjectDrawingReview, page: int, box: tuple, width: int,
          mark: tuple[float, float] | None) -> bytes:
    """A piece of the plotted drawing, `width` pixels wide, with the room marked."""
    if not row.pdf_path:
        raise ValueError("The drawing has not been plotted yet")
    doc = pymupdf.open(storage.absolute(row.pdf_path))
    try:
        if not 0 <= page < doc.page_count:
            raise ValueError("No such page")
        dpi = P.dpi_for(box, width)
        png = P.crop(doc, page, box, dpi)
        if mark:
            scale = dpi / 72.0
            png = _ring(png, (mark[0] - box[0]) * scale, (mark[1] - box[1]) * scale)
        return png
    finally:
        doc.close()


def _ring(png: bytes, x: float, y: float) -> bytes:
    import io

    from PIL import Image, ImageDraw

    im = Image.open(io.BytesIO(png)).convert("RGB")
    d = ImageDraw.Draw(im)
    r = max(18, im.width // 14)
    d.ellipse((x - r, y - r, x + r, y + r), outline=(220, 38, 38), width=max(3, im.width // 200))
    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue()
