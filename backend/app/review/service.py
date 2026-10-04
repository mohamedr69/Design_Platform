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
import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf
from sqlalchemy.orm import Session

from app.ai.budget import JobBudget, Limits, calls_today
from app.ai.provider import ImagePart, TextPart, get_provider
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


def _budget(db: Session, project: Project) -> JobBudget:
    s = get_settings()
    limits = dataclasses.replace(
        Limits.from_settings(), max_input_tokens_per_task=80_000, max_output_tokens_per_task=8_000,
        max_calls_per_document=s.drawing_review_max_calls, max_calls_per_project_per_day=10 ** 6,
        max_elapsed_s_per_job=s.drawing_review_max_elapsed_s, max_cost_per_job=s.drawing_review_max_cost)
    return JobBudget(limits=limits, calls_today_before=calls_today(db, project.id))


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
        check=None) -> dict:
    """The review, saved as it goes."""
    s = get_settings()
    drawing = db.get(ProjectIfcDrawing, drawing_id)
    if drawing is None or drawing.project_id != project.id:
        raise ValueError("That drawing is not this project's")
    row = state(db, project, drawing_id)
    row.status, row.error, row.started_at, row.finished_at = "running", None, utc_now(), None
    db.commit()

    def say(done: int, total: int, message: str) -> None:
        if progress:
            progress(done, total, message)

    try:
        say(0, 1, "Plotting the drawing with AutoCAD (about 6 minutes, once per revision)")
        pdf, sha, planned = plan_job(db, project, drawing, pages_wanted)
        # the engineers' rulings go with the rules; a new ruling is a new question
        extra, ruled = R.prompt(db)
        version = f"{A.PROMPT_VERSION}+{ruled}"
        before = {sh["index"]: sh for sh in (row.sheets or []) if row.source_sha256 == sha}
        sheets = []
        for sh in planned:
            old = before.get(sh["index"])
            if old and old.get("prompt_version") == version:
                # read before with the same drawing and prompt: keep its answers
                done_ids = {w["id"] for w in old.get("windows", []) if w.get("status") == "done"}
                sh["windows"] = [next((o for o in old["windows"] if o["id"] == w["id"]), w) if w["id"] in done_ids
                                 else w for w in sh["windows"]]
                sh["sheet_findings"] = old.get("sheet_findings")
                sh["sheet_status"] = old.get("sheet_status")
                same = (old.get("fls") or {}).get("file"), (old.get("fls") or {}).get("page")
                if sh.get("fls") and same == (sh["fls"]["file"], sh["fls"]["page"]):
                    sh["fls_findings"] = old.get("fls_findings")
                    sh["fls_status"] = old.get("fls_status")
            sh["prompt_version"] = version
            sheets.append(sh)
        # sheets the engineer did not ask for this time keep what they had
        sheets += [old for idx, old in before.items() if idx not in {sh["index"] for sh in sheets}]
        sheets.sort(key=lambda sh: sh["index"])
        row.sheets, row.source_sha256, row.model = sheets, sha, s.drawing_review_model
        row.pdf_path = storage.relative(pdf)
        _fit(project, drawing, row, pdf)
        db.commit()

        tasks = []
        per = max(1, s.drawing_review_windows_per_call)
        for sh in sheets:
            if pages_wanted is not None and sh["index"] not in pages_wanted:
                continue
            todo = [w for w in sh["windows"] if w.get("status") != "done"]
            for i in range(0, len(todo), per):
                tasks.append(("window", sh["index"], [w["id"] for w in todo[i:i + per]]))
            if sh.get("sheet_status") != "done":
                tasks.append(("sheet", sh["index"], []))
            if sh.get("fls") and sh.get("fls_status") != "done":
                tasks.append(("fls", sh["index"], []))
        total = len(tasks)
        say(0, max(total, 1), f"Reviewing {sum(len(w['rooms']) for sh in sheets for w in sh['windows'])} rooms "
                              f"in {total} looks")
        budget = _budget(db, project)
        by_index = {sh["index"]: sh for sh in sheets}
        done = 0
        pool = ThreadPoolExecutor(max_workers=max(1, s.drawing_review_parallel))
        try:
            futures = {pool.submit(_ask, project.id, str(pdf), sha, by_index[t[1]], t, budget, extra, version): t
                       for t in tasks}
            if check:
                check()
            for future in as_completed(futures):
                kind, index, ids = futures[future]
                sh = by_index[index]
                try:
                    answer = future.result()
                except Exception as exc:  # noqa: BLE001 -- one look that fails is named; the rest go on
                    answer = {"error": str(exc) or type(exc).__name__}
                if kind == "window":
                    for w in sh["windows"]:
                        if w["id"] in ids:
                            w.update(answer.get(w["id"]) or {"status": "failed", "error": answer.get("error")})
                else:
                    prefix = "fls" if kind == "fls" else "sheet"
                    sh[f"{prefix}_findings"] = answer.get("findings")
                    sh[f"{prefix}_status"] = "done" if "findings" in answer else "failed"
                    sh[f"{prefix}_error"] = answer.get("error")
                done += 1
                row.calls = (row.calls or 0) + 1
                row.sheets = json.loads(json.dumps(sheets))       # a fresh value: written
                db.commit()
                say(done, total, f"Reviewed {done} of {total} ({sh['floor']})")
                if check:
                    check()
        finally:
            # a stop stops: the looks still waiting are dropped, only the ones under way finish
            pool.shutdown(wait=False, cancel_futures=True)
        failed = sum(1 for sh in sheets for w in sh["windows"] if w.get("status") == "failed")
        row.status, row.finished_at = "done", utc_now()
        row.error = f"{failed} window(s) could not be reviewed: run the review again to retry them." if failed else None
        db.commit()
        return {"sheets": len(sheets), "calls": total, "failed_windows": failed}
    except Exception as exc:
        from app.services import jobs

        db.rollback()
        row = state(db, project, drawing_id)
        row.status = "stopped" if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)) else "failed"
        row.error = None if row.status == "stopped" else str(exc)
        row.finished_at = utc_now()
        db.commit()
        raise


def _ask(project_id: int, pdf: str, sha: str, sheet: dict, task: tuple, budget: JobBudget, extra: str = "",
         version: str = A.PROMPT_VERSION) -> dict:
    """One look, in a session of its own (it runs beside others)."""
    s = get_settings()
    kind, index, ids = task
    db = SessionLocal()
    doc = pymupdf.open(pdf)
    try:
        session = assist.AssistSession(db=db, project_id=project_id, document_sha256=f"{sha}:{index}", budget=budget,
                                       provider=get_provider())
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
                                      prompt_version=version, model=s.drawing_review_model,
                                      timeout_s=s.drawing_review_timeout_s)
            db.commit()
            if result.data is None:
                return {"error": result.error or "no answer"}
            return {"findings": A.read_sheet_answer(result.data)}
        if kind == "sheet":
            plan = tuple(sheet["plan"])
            parts.append(TextPart("floor", f"{sheet['floor']} -- {sheet['title']}"))
            parts.append(ImagePart("floor plan", P.crop(doc, index, plan, P.dpi_for(plan, 1900))))
            names = sorted({r["name"] for w in sheet["windows"] for r in w["rooms"]})
            parts.append(TextPart("rooms named on the plan", ", ".join(names)[:3000]))
            result = assist.call_task(session, TASK_SHEET, A.SYSTEM_SHEET + extra, parts, A.SHEET_SCHEMA, 3000,
                                      prompt_version=version, model=s.drawing_review_model,
                                      timeout_s=s.drawing_review_timeout_s)
            db.commit()
            if result.data is None:
                return {"error": result.error or "no answer"}
            return {"findings": A.read_sheet_answer(result.data)}
        wins = [w for w in sheet["windows"] if w["id"] in ids]
        parts.append(TextPart("floor", f"{sheet['floor']} -- {sheet['title']}"))
        for k, w in enumerate(wins, 1):
            box = tuple(w["box"])
            dpi = P.dpi_for(box, 1500)
            scale = dpi / 72.0
            marks = [(r["n"], (r["x"] - box[0]) * scale, (r["y"] - box[1]) * scale) for r in w["rooms"]]
            parts.append(ImagePart(f"image {k}", A.numbered(P.crop(doc, index, box, dpi), marks)))
            parts.append(TextPart(f"image {k} rooms", "\n".join(f"{r['n']}: {r['name']}" for r in w["rooms"])))
        result = assist.call_task(session, TASK_WINDOW, A.SYSTEM_WINDOW + extra, parts, A.WINDOW_SCHEMA, 6000,
                                  prompt_version=version, model=s.drawing_review_model,
                                  timeout_s=s.drawing_review_timeout_s)
        db.commit()
        if result.data is None:
            return {w["id"]: {"status": "failed", "error": result.error or "no answer"} for w in wins}
        numbers = {r["n"] for w in wins for r in w["rooms"]}
        answers, other = A.read_window_answer(result.data, numbers)
        out = {}
        for k, w in enumerate(wins, 1):
            out[w["id"]] = {
                "status": "done", "error": None, "model": result.model,
                "answers": {str(r["n"]): dataclasses.asdict(answers[r["n"]]) for r in w["rooms"] if r["n"] in answers},
                "other": [o for o in other if o.get("image") == k or (o.get("image") not in range(1, len(wins) + 1)
                                                                       and k == 1)],
            }
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
            for r in w["rooms"]:
                answer = (w.get("answers") or {}).get(str(r["n"]))
                checks = (answer or {}).get("checks") or {}
                room = {"id": r["id"], "name": r["name"], "room_type": (answer or {}).get("room_type", ""),
                        "checks": checks or None, "status": w.get("status", "pending"), "error": w.get("error"),
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
                       "fls_status": sh.get("fls_status"),
                       "multiplier": sh.get("multiplier", 1), "rooms": rooms, "windows": len(windows),
                       "windows_done": sum(1 for w in windows if w.get("status") == "done"),
                       "windows_failed": sum(1 for w in windows if w.get("status") == "failed"),
                       "sheet_status": sh.get("sheet_status") or "pending"})
    findings += _spacing(spaced)
    findings += _alternate(stair_speakers)
    _sounder_spacing(db, drawing, row, findings)
    ruled = R.not_needed(db)
    for f in findings:
        d = decisions.get(f["id"]) or {}
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
    actionable = [f for f in findings if f["action"] != "none"]
    return {
        "drawing": {"id": drawing.id, "filename": drawing.filename, "revision": drawing.revision or "R0"},
        "status": row.status, "error": row.error, "model": row.model or get_settings().drawing_review_model,
        "calls": row.calls or 0,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "floors": floors, "findings": findings, "stats": stats,
        "fls": {"folder": F.FOLDER, "files": [p.name for p in F.files(project)],
                "floors_matched": sum(1 for f in floors if f.get("fls")), "floors": len(floors)},
        "systems": A.SYSTEMS,
        "rules": [{"system": k, "name": A.SYSTEMS[k], "rule": t + (_MEASURED.get(k) or "")} for k, t in A.RULES],
        "rulings": [{"id": r.id, "decision": r.decision, "room": r.room, "system": r.system,
                     "system_name": A.SYSTEMS.get(r.system, r.system), "action": r.action, "device": r.device,
                     "instruction": r.instruction, "note": r.note, "project_id": r.project_id,
                     "at": r.created_at.isoformat() if r.created_at else None} for r in R.listed(db)],
        "counts": {"rooms": sum(len(f["rooms"]) for f in floors),
                   "reviewed": sum(1 for f in floors for r in f["rooms"] if r["checks"]),
                   "open": sum(1 for f in actionable if f["decision"] == "open"),
                   "accepted": sum(1 for f in actionable if f["decision"] == "accepted"),
                   "dismissed": sum(1 for f in actionable if f["decision"] == "dismissed"),
                   "unclear": sum(1 for f in findings if f["action"] == "none" and f["decision"] == "open"),
                   "add": sum(1 for f in actionable if f["action"] == "add"),
                   "remove": sum(1 for f in actionable if f["action"] == "remove"),
                   "replace": sum(1 for f in actionable if f["action"] == "replace")},
    }


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
