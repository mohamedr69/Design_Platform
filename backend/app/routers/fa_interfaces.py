"""The BOQ page's "FA Interfaces" tab: the Fire Alarm Interface Schedule --
the other trades' equipment the fire alarm system monitors or controls,
floor by floor, from their IFC drawings (app.interfaces).

  GET    /projects/{id}/fa-interfaces                  the schedule, its summaries, what is left to verify, the drawings read
  POST   /projects/{id}/fa-interfaces/scan/jobs        read the IFC drawings again (the IFC worker): HTTP 202 and the job
                                                        (?hydrate=true: bring down OneDrive cloud-only files and read them)
  POST   /projects/{id}/fa-interfaces/publish-current  the engineer publishes what is read and current now (with why)
  POST   /projects/{id}/fa-interfaces/sources/confirm-removed   files missing from a present folder, removed on purpose
  POST   /projects/{id}/fa-interfaces/decisions        an engineer's answer on a line or a verification item
  POST   /projects/{id}/fa-interfaces/manual           an item the drawings did not give, with the drawing it is on
  DELETE /projects/{id}/fa-interfaces/manual/{mid}     ... taken out again
  GET    /projects/{id}/fa-interfaces/export.xlsx      the schedule as a workbook, floor-wise
  GET    /projects/{id}/fa-interfaces/export.pdf       ... as a document, laid out to be issued
  GET    /projects/{id}/fa-interfaces/review-cases.pdf the cases the Opus review could not decide, with the
                                                        drawing pictures it was shown (?item=<id>: that one)

The router checks and answers; the reading runs in the IFC worker, and the
schedule is built from the readings and the answers on every read.
"""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.timeutils import utc_now
from app.database import get_db
from app.deps import get_current_user, require_role
from app.interfaces import service
from app.interfaces.matrix import BY_KEY, DISCIPLINE_NAMES
from app.models import User
from app.routers.projects import CREATOR_ROLES, _get_project_or_404
from app.services import activity, jobs

router = APIRouter(tags=["fa-interfaces"])
KIND = "fa_interfaces_scan"
RUN_KIND = "fa_interfaces_run"
REVIEW_KIND = "fa_interfaces_review"


def read_key(project_id: int) -> str:
    """One key for every job that reads or reviews a project's interface
    evidence (scan, run, Retry review): the job table's partial unique index
    lets one of them be active at a time, atomically (F10)."""
    return f"fa_interfaces:{project_id}"


def _active_read(db: Session, project_id: int):
    for key in (read_key(project_id), f"{KIND}:{project_id}", f"{RUN_KIND}:{project_id}"):   # older jobs' own keys
        existing = jobs.active_by_key(db, key)
        if existing is not None:
            return existing
    return None
_SAFE = re.compile(r"[^\w .()-]+")


@router.get("/projects/{project_id}/fa-interfaces")
def get_schedule(project_id: int, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    out = service.build(db, project)
    db.commit()     # the project's row, made on first read
    return out


@router.post("/projects/{project_id}/fa-interfaces/scan/jobs", status_code=status.HTTP_202_ACCEPTED)
def start_scan(project_id: int, hydrate: bool = False, current_user: User = Depends(require_role(*CREATOR_ROLES)),
               db: Session = Depends(get_db)):
    """Queue the read of every discipline's IFC drawings for the IFC worker.
    The same request while one is queued or running returns that job.
    `hydrate`: OneDrive cloud-only files are brought down and read even when
    FA_READ_CLOUD_ONLY_FILES is off (the page's "Download and read")."""
    from app.routers.ifc_boq import _queue_note, _run_inline, _started
    from app.routers import jobs as jobs_router

    project = _get_project_or_404(db, project_id)
    if not project.source_folder_path:
        raise HTTPException(422, "This project has no folder: the IFC drawings are read from its 03- Drawings/IFC folders.")
    existing = _active_read(db, project.id)
    if existing is not None:
        return _started(db, existing, False)
    job, created = jobs.enqueue(db, kind=KIND, project_id=project.id, user_id=current_user.id, dedup_key=read_key(project.id),
                                params={"user_id": current_user.id, "hydrate": bool(hydrate)},
                                progress=_queue_note(db), message="")
    if created:
        activity.record(db, current_user, "fa_interfaces.scan", "Read the IFC drawings for the FA interface schedule",
                        project=project, entity_type="project", entity_id=project.id)
    if created and jobs_router.RUN_INLINE:
        _run_inline(job.id)
        db.expire_all()
        job = db.get(type(job), job.id)
    return _started(db, job, created)


@router.post("/projects/{project_id}/fa-interfaces/runs/jobs", status_code=status.HTTP_202_ACCEPTED)
def start_run(project_id: int, fresh: bool = False, current_user: User = Depends(require_role(*CREATOR_ROLES)),
              db: Session = Depends(get_db)):
    """Queue the drawing workflow (the IFC worker): read, drawing agents, the
    Opus finding review, package reports, the Opus orchestrator's review. One
    read of a project at a time: a read or a run already queued or running is
    returned instead -- except that a force-fresh run (`?fresh=true`: every
    drawing read, looked at and reviewed again, nothing reused) is never
    answered with an ordinary one: that is refused, to be asked again after it."""
    from app.routers import jobs as jobs_router
    from app.routers.ifc_boq import _queue_note, _run_inline, _started

    project = _get_project_or_404(db, project_id)
    if not project.source_folder_path:
        raise HTTPException(422, "This project has no folder: the IFC drawings are read from its 03- Drawings/IFC folders.")
    existing = _active_read(db, project.id)
    if existing is not None:
        if fresh and not (existing.kind == RUN_KIND and (existing.params or {}).get("fresh")):
            raise HTTPException(409, "The drawings are being read now: start the fresh reread when that job has "
                                     "finished (it would not read them afresh)")
        return _started(db, existing, False)
    job, created = jobs.enqueue(db, kind=RUN_KIND, project_id=project.id, user_id=current_user.id,
                                dedup_key=read_key(project.id),
                                params={"user_id": current_user.id, "fresh": bool(fresh)}, progress=_queue_note(db),
                                message="")
    if created:
        activity.record(db, current_user, "fa_interfaces.run",
                        "Ran the FA interfaces drawing workflow" + (" (force-fresh reread)" if fresh else ""),
                        project=project, entity_type="project", entity_id=project.id)
    elif fresh and not (job.params or {}).get("fresh"):
        raise HTTPException(409, "The drawings are being read now: start the fresh reread when that job has finished")
    if created and jobs_router.RUN_INLINE:
        _run_inline(job.id)
        db.expire_all()
        job = db.get(type(job), job.id)
    return _started(db, job, created)


@router.get("/projects/{project_id}/fa-interfaces/runs/latest")
def latest_run(project_id: int, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.interfaces import workflow

    project = _get_project_or_404(db, project_id)
    return {"run": workflow.view(workflow.latest(db, project))}


def _run_or_404(db: Session, project, run_id: int):
    from app.models import FaInterfaceRun

    run = db.get(FaInterfaceRun, run_id)
    if run is None or run.project_id != project.id:
        raise HTTPException(404, "That run is not this project's")
    return run


@router.post("/projects/{project_id}/fa-interfaces/runs/{run_id}/accept")
def accept_run(project_id: int, run_id: int, current_user: User = Depends(require_role(*CREATOR_ROLES)),
               db: Session = Depends(get_db)):
    """The engineer accepts a reviewed, complete run: its readings are published.
    A provisional run (review missing, coverage incomplete, a conflict open) is refused."""
    from app.interfaces import workflow

    project = _get_project_or_404(db, project_id)
    run = _run_or_404(db, project, run_id)
    try:
        workflow.accept(db, project, run, current_user.id)
    except service.SourcesChanged as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    activity.record(db, current_user, "fa_interfaces.accept_run", f"Accepted FA interfaces run {run.id}",
                    project=project, entity_type="project", entity_id=project.id)
    db.commit()
    return {"run": workflow.view(run), "schedule": service.build(db, project)}


@router.post("/projects/{project_id}/fa-interfaces/runs/{run_id}/retry-review", status_code=status.HTTP_202_ACCEPTED)
def retry_review(project_id: int, run_id: int, current_user: User = Depends(require_role(*CREATOR_ROLES)),
                 db: Session = Depends(get_db)):
    """The Opus review again (the finding review on the items it could not
    review, the orchestrator on the run's frozen inputs), as a job (the IFC worker): refused for an accepted, unfinished or fully reviewed
    run, one whose drawings changed, or past the day's bound -- counted here,
    atomically, before the job is queued (F5/F8)."""
    from app.interfaces import workflow
    from app.routers import jobs as jobs_router
    from app.routers.ifc_boq import _queue_note, _run_inline, _started

    project = _get_project_or_404(db, project_id)
    run = _run_or_404(db, project, run_id)
    existing = _active_read(db, project.id)
    if existing is not None:
        raise HTTPException(409, "The drawings are being read or reviewed now: retry when that job has finished")
    try:
        workflow.claim_retry(db, project, run)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    job, created = jobs.enqueue(db, kind=REVIEW_KIND, project_id=project.id, user_id=current_user.id,
                                dedup_key=read_key(project.id), params={"user_id": current_user.id, "run_id": run.id},
                                progress=_queue_note(db), message="")
    if not created:
        workflow.release_retry(db, run)                          # refused: the day's bound is not spent on it
        raise HTTPException(409, "The drawings are being read or reviewed now: retry when that job has finished")
    activity.record(db, current_user, "fa_interfaces.retry_review", f"Retried the review of FA interfaces run {run.id}",
                    project=project, entity_type="project", entity_id=project.id)
    if jobs_router.RUN_INLINE:
        _run_inline(job.id)
        db.expire_all()
        job = db.get(type(job), job.id)
    return _started(db, job, created)


class PublishCurrent(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
    expected_sources_digest: str = Field(min_length=64, max_length=64)
    override: bool = False


@router.post("/projects/{project_id}/fa-interfaces/publish-current")
def publish_current(project_id: int, body: PublishCurrent, current_user: User = Depends(require_role(*CREATOR_ROLES)),
                    db: Session = Depends(get_db)):
    """The engineer publishes the schedule built from what is read and current
    now (FI-P1 r3 S7/C5): the way out when a drawing keeps failing, or the
    only evidence is the fire alarm IFC drawing. The page sends the digest of
    what it showed; anything changed since is refused."""
    project = _get_project_or_404(db, project_id)
    try:
        result = service.publish_current(db, project, current_user.id, reason=body.reason,
                                         expected_sources_digest=body.expected_sources_digest, override=body.override)
    except service.SourcesChanged as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    activity.record(db, current_user, "fa_interfaces.publish",
                    f"Published the FA interface schedule from {result['published_sources']} current drawing(s): "
                    f"{body.reason.strip()[:200]}" + (" (override)" if body.override else ""),
                    project=project, entity_type="project", entity_id=project.id)
    db.commit()
    return service.build(db, project)


class ConfirmRemoved(BaseModel):
    relative_paths: list[str] = Field(min_length=1, max_length=500)


@router.post("/projects/{project_id}/fa-interfaces/sources/confirm-removed")
def confirm_removed(project_id: int, body: ConfirmRemoved, current_user: User = Depends(require_role(*CREATOR_ROLES)),
                    db: Session = Depends(get_db)):
    """Files missing from a folder that is there, or a folder gone, removed on
    purpose (C5). A file the sync has not brought down cannot be confirmed away."""
    project = _get_project_or_404(db, project_id)
    try:
        n = service.confirm_removed(db, project, current_user.id, body.relative_paths)
    except service.SourcesChanged as exc:
        raise HTTPException(409, str(exc)) from exc
    if not n:
        raise HTTPException(422, "None of those files is missing from its folder: only a missing file, or a missing "
                                 "folder's files, can be confirmed as removed")
    activity.record(db, current_user, "fa_interfaces.confirm_removed",
                    f"Confirmed {n} drawing(s) removed from the IFC folders", project=project,
                    entity_type="project", entity_id=project.id)
    db.commit()
    return service.build(db, project)


class Decision(BaseModel):
    id: str = Field(max_length=600)
    # reject | restore | confirm (a scheduled line); resolve | dismiss | reopen (a verification item);
    # govern (a conflict between drawings: which drawing counts, `relative_path`)
    action: str
    relative_path: str = Field(default="", max_length=1000)
    authority: str = Field(default="", max_length=300)        # govern: whose confirmation the choice rests on
    reason: str = Field(default="", max_length=500)
    floor_keys: list[str] = Field(default_factory=list, max_length=200)
    qty: int | None = Field(default=None, ge=1, le=500)
    tags: list[str] = Field(default_factory=list, max_length=500)
    location: str = Field(default="", max_length=160)


def _known_floors(view: dict, keys: list[str]) -> list[str]:
    known = {f["key"] for f in view["floors"]}
    unknown = [k for k in keys if known and k not in known]
    if unknown:
        raise HTTPException(422, f"Not a floor of the building: {', '.join(unknown[:5])}")
    if not keys:
        raise HTTPException(422, "Say which floor it is on")
    return keys


@router.post("/projects/{project_id}/fa-interfaces/decisions")
def decide(project_id: int, body: Decision, current_user: User = Depends(require_role(*CREATOR_ROLES)),
           db: Session = Depends(get_db)):
    """An engineer's answer. Each one is kept with the answers it replaced
    (`history`): reopening or correcting an answer never deletes what was
    decided before (F3)."""
    project = _get_project_or_404(db, project_id)
    view = service.build(db, project)
    row = service.state(db, project)
    lines = {r["id"]: r for r in view["rows"] + view["rejected"]}
    items = {g["id"]: g for g in view["verification"] + view["settled"]}
    decisions = dict(row.decisions or {})
    stamp = {"by": current_user.id, "at": utc_now().isoformat()}

    def record(new: dict) -> None:
        old = decisions.get(body.id)
        history = list((old or {}).get("history") or [])
        if old:
            history.append({k: v for k, v in old.items() if k != "history"})
        decisions[body.id] = {**new, **stamp, "history": history[-50:]}

    if body.action in ("reject", "restore", "confirm"):
        line = lines.get(body.id)
        if line is None or line["basis"] != "drawing":
            raise HTTPException(404, "That line is not in the schedule (read the drawings again?)")
        if body.action == "restore" and line.get("visual_reject"):
            # set aside by the visual check: the engineer's word puts it back
            record({"status": "confirmed", "reason": "restored by the engineer"})
        elif body.action == "restore":
            record({"status": "restored", "reason": body.reason.strip()})
        else:
            if body.action == "reject" and not body.reason.strip():
                raise HTTPException(422, "Say why it is not an interface")
            record({"status": "rejected" if body.action == "reject" else "confirmed", "reason": body.reason.strip()})
        what = f"{line['equipment']} {line['tag']} on {line['floor']}"
    elif body.action == "govern":
        item = items.get(body.id)
        if item is None or not item.get("drawings"):
            raise HTTPException(404, "That is not a conflict between drawings (read the drawings again?)")
        if body.relative_path not in {d["relative_path"] for d in item["drawings"]}:
            raise HTTPException(422, "Choose one of the drawings in the conflict")
        if not body.reason.strip():
            raise HTTPException(422, "Say why that drawing governs")
        if not body.authority.strip():
            raise HTTPException(422, "Say on whose authority that drawing governs (the consultant's confirmation, "
                                     "the site's): its barriers are then counted as interfaces")
        record({"status": "governed", "relative_path": body.relative_path, "reason": body.reason.strip(),
                "authority": body.authority.strip(),
                # the drawings weighed: one joining later reopens the choice (R3-3)
                "drawings": sorted(d["relative_path"] for d in item["drawings"])})
        what = f"{item['equipment']} on {item['ref']}: {body.relative_path} governs ({body.authority.strip()[:80]})"
    elif body.action in ("resolve", "dismiss", "reopen"):
        item = items.get(body.id)
        if item is None:
            raise HTTPException(404, "That verification item is not open (read the drawings again?)")
        # A5: settling a conflict between drawings -- by a count, or as no interface -- overrides what the
        # drawings show, as choosing the governing one does: it needs the reason and whose authority it rests on
        authority = {}
        if body.action in ("resolve", "dismiss") and item.get("conflict"):
            if not body.reason.strip():
                raise HTTPException(422, "Say why: the drawings disagree here")
            if not body.authority.strip():
                raise HTTPException(422, "Say on whose authority (the consultant's confirmation, the site's): "
                                         "the drawings disagree here")
            authority = {"authority": body.authority.strip()}
        if body.action == "reopen":
            record({"status": "open", "reason": body.reason.strip()})
        elif body.action == "dismiss":
            if not body.reason.strip():
                raise HTTPException(422, "Say why it is not scheduled")
            record({"status": "dismissed", "reason": body.reason.strip(), **authority})
        else:
            if body.qty is None:
                raise HTTPException(422, "Say how many there are on each floor")
            record({"status": "resolved", "floor_keys": _known_floors(view, body.floor_keys), "qty": body.qty,
                    "tags": [t.strip() for t in body.tags if t.strip()], "location": body.location.strip(),
                    "reason": body.reason.strip(), **authority})
        what = f"{item['equipment']} ({item['source']})" + (f" on the authority of {authority['authority'][:80]}"
                                                            if authority else "")
    else:
        raise HTTPException(422, "action is one of reject, restore, confirm, resolve, dismiss, reopen, govern")
    row.decisions = decisions
    db.commit()
    activity.record(db, current_user, f"fa_interfaces.{body.action}", f"FA interfaces: {body.action} {what}",
                    project=project, entity_type="project", entity_id=project.id, detail={"id": body.id})
    return service.build(db, project)


class ManualItem(BaseModel):
    key: str
    floor_keys: list[str] = Field(max_length=200)
    qty: int = Field(default=1, ge=1, le=500)
    tags: list[str] = Field(default_factory=list, max_length=500)
    location: str = Field(default="", max_length=160)
    discipline: str | None = None
    # Traceability: the drawing it was seen on. Required.
    source: str = Field(max_length=300)
    drawing_ref: str = Field(default="", max_length=300)
    remarks: str = Field(default="", max_length=500)


@router.post("/projects/{project_id}/fa-interfaces/manual", status_code=201)
def add_manual(project_id: int, body: ManualItem, current_user: User = Depends(require_role(*CREATOR_ROLES)),
               db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    rule = BY_KEY.get(body.key)
    if rule is None or rule.excluded:
        raise HTTPException(422, "Not an equipment the interface matrix schedules")
    if not body.source.strip():
        raise HTTPException(422, "Name the drawing it is on: every line of the schedule is traceable to one")
    if body.discipline and body.discipline not in DISCIPLINE_NAMES:
        raise HTTPException(422, f"discipline is one of {', '.join(DISCIPLINE_NAMES)}")
    view = service.build(db, project)
    item = {"id": uuid.uuid4().hex[:12], "key": body.key, "floor_keys": _known_floors(view, body.floor_keys),
            "qty": body.qty, "tags": [t.strip() for t in body.tags if t.strip()], "location": body.location.strip(),
            "discipline": body.discipline, "source": body.source.strip(), "drawing_ref": body.drawing_ref.strip(),
            "remarks": body.remarks.strip(), "by": current_user.id, "at": utc_now().isoformat()}
    row = service.state(db, project)
    row.manual = [*(row.manual or []), item]
    db.commit()
    activity.record(db, current_user, "fa_interfaces.manual_added", f"FA interfaces: added {rule.name}",
                    project=project, entity_type="project", entity_id=project.id, detail={"id": item["id"]})
    return service.build(db, project)


@router.delete("/projects/{project_id}/fa-interfaces/manual/{manual_id}")
def remove_manual(project_id: int, manual_id: str, current_user: User = Depends(require_role(*CREATOR_ROLES)),
                  db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    row = service.state(db, project)
    kept = [m for m in row.manual or [] if m.get("id") != manual_id]
    if len(kept) == len(row.manual or []):
        raise HTTPException(404, "No such item")
    row.manual = kept
    db.commit()
    activity.record(db, current_user, "fa_interfaces.manual_removed", "FA interfaces: removed an added item",
                    project=project, entity_type="project", entity_id=project.id, detail={"id": manual_id})
    return service.build(db, project)


@router.get("/projects/{project_id}/fa-interfaces/export.xlsx")
def export(project_id: int, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.interfaces.export import workbook

    project = _get_project_or_404(db, project_id)
    view = service.build(db, project)
    db.commit()
    buf = workbook(view)
    name = _SAFE.sub("_", f"EP-{project.ep_number} FA Interface Schedule.xlsx")
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/projects/{project_id}/fa-interfaces/review-cases.pdf")
def review_cases_pdf(project_id: int, item: str | None = None, _current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """The cases the Opus review could not decide, for the engineer: each item
    still in Verification Required with what remains unclear, what to verify and
    the pictures of the drawing the review was shown. `item`: that one only."""
    from fastapi.responses import Response

    from app.interfaces import cases_pdf, findings

    project = _get_project_or_404(db, project_id)
    view = service.build(db, project)
    db.commit()
    if item is not None and not any(g["id"] == item for g in view["verification"]):
        raise HTTPException(404, "That item is not in Verification Required (read the drawings again?)")
    run_id = (view.get("review") or {}).get("run_id")
    doc = cases_pdf.build(view, findings.case_folder(project, run_id) if run_id else None, item_id=item)
    pdf = doc.tobytes(deflate=True)
    doc.close()
    if item is not None:
        g = next(g for g in view["verification"] if g["id"] == item)
        stem = f"EP-{project.ep_number} FA case - {g['equipment']} {g['ref']}"
    else:
        stem = f"EP-{project.ep_number} FA Interfaces - cases to verify"
    name = _SAFE.sub("_", stem)[:140].strip() + ".pdf"
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/projects/{project_id}/fa-interfaces/export.pdf")
def export_pdf(project_id: int, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from fastapi.responses import Response

    from app.interfaces.pdf import build

    project = _get_project_or_404(db, project_id)
    view = service.build(db, project)
    db.commit()
    doc = build(view)
    pdf = doc.tobytes()
    doc.close()
    name = _SAFE.sub("_", f"EP-{project.ep_number} FA Interface Schedule.pdf")
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})
