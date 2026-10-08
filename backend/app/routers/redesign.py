"""Drawings Redesign (app.redesign).

  GET   /projects/{id}/redesign                               the drawings that can be redesigned
  GET   /projects/{id}/redesign/{did}                         the changes, placed, and the copy made
  POST  /projects/{id}/redesign/{did}/plan/jobs               place the accepted changes (the model; IFC worker)
  PATCH /projects/{id}/redesign/{did}/changes/{cid}           approve / skip / move / another symbol
  PATCH /projects/{id}/redesign/{did}/changes                 approve / skip / undo many at once
  POST  /projects/{id}/redesign/{did}/interfaces              the interface schedule's modules, brought in again
  GET   /projects/{id}/redesign/{did}/changes/{cid}/image     the change on its piece of plan (PNG)
  POST  /projects/{id}/redesign/{did}/apply/jobs              make the redesigned copy (AutoCAD; IFC worker), refused
                                                              (422) unless the drawing is ready for the draftsman
  GET   /projects/{id}/redesign/{did}/output.dwg              the redesigned drawing (the platform's copy)
  POST  /projects/{id}/redesign/{did}/publish                 a verified copy put into the project archive, under a
                                                              name never overwritten (the engineer's own action)
  GET   /projects/{id}/redesign/{did}/markup.pdf              the draftsman's PDF: each floor marked, and the schedule
"""
from __future__ import annotations

import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai import project_policy
from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import ProjectDrawingReview, ProjectIfcDrawing, User
from app.redesign import service
from app.routers.projects import CREATOR_ROLES, _get_project_or_404
from app.services import activity, jobs

router = APIRouter(tags=["drawings redesign"])


def _drawing(db: Session, project, drawing_id: int) -> ProjectIfcDrawing:
    drawing = db.get(ProjectIfcDrawing, drawing_id)
    if drawing is None or drawing.project_id != project.id:
        raise HTTPException(404, "Drawing not found")
    return drawing


@router.get("/projects/{project_id}/redesign")
def drawings(project_id: int, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The fire alarm IFC drawings in force, with how far each one's review
    and redesign have got."""
    from app.ifc.services import revisions
    from app.models import ProjectRedesign
    from app.review import service as review_service

    project = _get_project_or_404(db, project_id)
    out = []
    for drawing in revisions.in_force(db, project.id):
        review = (db.query(ProjectDrawingReview)
                  .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing.id).first())
        row = (db.query(ProjectRedesign)
               .filter(ProjectRedesign.project_id == project.id, ProjectRedesign.drawing_id == drawing.id).first())
        out.append({"id": drawing.id, "filename": drawing.filename, "revision": drawing.revision or "R0",
                    "review_status": review.status if review else None,
                    # what the review comes to (the Review step's mark): a plot no model answered is not reviewed
                    "review_state": review_service.outcome(review)[0] if review else "not_reviewed",
                    "redesign_status": row.status if row else "none",
                    "output_status": row.output_status if row else "none"})
    return {"drawings": out}


@router.get("/projects/{project_id}/redesign/{drawing_id}")
def get_redesign(project_id: int, drawing_id: int, _current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    return service.view(db, project, drawing_id)


def _start(db: Session, project, drawing, kind: str, user: User, what: str, extra: dict | None = None):
    from app.routers import jobs as jobs_router
    from app.routers.ifc_boq import _queue_note, _run_inline, _started

    key = f"{kind}:{project.id}:{drawing.id}"
    existing = jobs.active_by_key(db, key)
    if existing is not None:
        return _started(db, existing, False)
    job, created = jobs.enqueue(db, kind=kind, project_id=project.id, user_id=user.id, dedup_key=key,
                                params={"drawing_id": drawing.id, "user_id": user.id, **(extra or {})},
                                progress=_queue_note(db), message="")
    if created:
        activity.record(db, user, f"redesign.{what}", f"Started the redesign {what} of {drawing.filename} "
                                                       f"{drawing.revision or ''}".strip(),
                        project=project, entity_type="ifc_drawing", entity_id=drawing.id)
    if created and jobs_router.RUN_INLINE:
        _run_inline(job.id)
        db.expire_all()
        job = db.get(type(job), job.id)
    return _started(db, job, created)


@router.post("/projects/{project_id}/redesign/{drawing_id}/plan/jobs", status_code=status.HTTP_202_ACCEPTED)
def start_plan(project_id: int, drawing_id: int, current_user: User = Depends(require_role(*CREATOR_ROLES)),
               db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    try:   # the project's AI policy, fail closed, before anything is queued (ORCH-053)
        project_policy.enforce(db, project.id, task=service.A.TASK)
    except project_policy.AiPolicyRefused as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _start(db, project, _drawing(db, project, drawing_id), service.KIND_PLAN, current_user, "plan")


@router.post("/projects/{project_id}/redesign/{drawing_id}/apply/jobs", status_code=status.HTTP_202_ACCEPTED)
def start_apply(project_id: int, drawing_id: int, current_user: User = Depends(require_role(*CREATOR_ROLES)),
                db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    drawing = _drawing(db, project, drawing_id)
    # the gate at the server boundary (M5): never queued while an engineering check is open
    ready = service.readiness(db, project, drawing, service.state(db, project, drawing.id))
    if not ready["ready"]:
        raise HTTPException(422, "Not ready for the draftsman: " + " ".join(ready["blockers"]))
    # the source and the decision snapshot as they are now: the job refuses to run
    # when either has changed by the time it starts (RD-M2)
    request = service.apply_request(db, project, drawing)
    if not request["drawn"]:
        raise HTTPException(422, "No change is approved to make: approve the changes first (a proposed change is never drawn).")
    return _start(db, project, drawing, service.KIND_APPLY, current_user, "drawing", extra=request)


class ChangeIn(BaseModel):
    # approved | skipped | proposed (undo)
    status: str | None = Field(default=None, pattern="^(approved|skipped|proposed)$")
    candidate: int | None = Field(default=None, ge=0, le=100)
    symbol: int | None = Field(default=None, ge=0)
    # a point on the change's picture, as fractions of its width and height
    point: list[float] | None = Field(default=None, min_length=2, max_length=2)
    rotation: float | None = None
    # the engineer confirms a spot placed less exactly than the plot allows (RD-M2)
    confirmed: bool | None = None


def _not_while_running(db: Session, project, drawing_id: int) -> None:
    """An engineer's change while a plan or the output is being made would be
    written over by it: refused until it ends."""
    from app.services import jobs

    for kind in (service.KIND_PLAN, service.KIND_APPLY):
        if jobs.active_by_key(db, f"{kind}:{project.id}:{drawing_id}") is not None:
            raise HTTPException(409, "The plan or the drawing is being made: change it once that has finished.")


@router.patch("/projects/{project_id}/redesign/{drawing_id}/changes/{change_id}")
def change(project_id: int, drawing_id: int, change_id: str, body: ChangeIn,
           current_user: User = Depends(require_role(*CREATOR_ROLES)), db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    _not_while_running(db, project, drawing_id)
    try:
        service.adjust(db, project, drawing_id, change_id, status=body.status, candidate=body.candidate,
                       symbol=body.symbol, point=body.point, rotation=body.rotation, confirmed=body.confirmed)
    except service.RedesignError as exc:
        raise HTTPException(422, str(exc)) from exc
    return service.view(db, project, drawing_id)


class ManyIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=5000)
    status: str = Field(pattern="^(approved|skipped|proposed)$")


@router.patch("/projects/{project_id}/redesign/{drawing_id}/changes")
def change_many(project_id: int, drawing_id: int, body: ManyIn,
                current_user: User = Depends(require_role(*CREATOR_ROLES)), db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    _not_while_running(db, project, drawing_id)
    service.set_status(db, project, drawing_id, body.ids, body.status)
    return service.view(db, project, drawing_id)


@router.post("/projects/{project_id}/redesign/{drawing_id}/interfaces")
def interfaces(project_id: int, drawing_id: int, current_user: User = Depends(require_role(*CREATOR_ROLES)),
               db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    drawing = _drawing(db, project, drawing_id)
    try:
        done = service.add_interfaces(db, project, drawing_id)
    except service.RedesignError as exc:
        raise HTTPException(422, str(exc)) from exc
    activity.record(db, current_user, "redesign.interfaces",
                    f"Brought the interface schedule's {done['modules']} modules into the redesign of {drawing.filename}",
                    project=project, entity_type="ifc_drawing", entity_id=drawing.id)
    return service.view(db, project, drawing_id)


@router.get("/projects/{project_id}/redesign/{drawing_id}/changes/{change_id}/image")
def change_image(project_id: int, drawing_id: int, change_id: str, width: int = 900,
                 v: str | None = None, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    row = service.state(db, project, drawing_id)
    try:
        png = service.image(project, drawing_id, row, change_id, max(300, min(width, 2000)))
    except service.RedesignError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(png, media_type="image/png", headers={"Cache-Control": "private, max-age=600"})


@router.get("/projects/{project_id}/redesign/{drawing_id}/output.dwg")
def output(project_id: int, drawing_id: int, _current_user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    row = service.state(db, project, drawing_id)
    # the last copy made, whatever the last attempt came to: a failed, stale or
    # refused attempt never hides an earlier valid copy (U2M5-09)
    path = service.last_output(row, project)
    if path is None:
        raise HTTPException(404, "No redesigned drawing has been made yet")
    name = path.name
    plain = re.sub(r"[^A-Za-z0-9 ._()-]", "_", name)
    return FileResponse(path, media_type="application/acad",
                        headers={"Content-Disposition": f"attachment; filename=\"{plain}\"; "
                                                        f"filename*=UTF-8''{quote(name)}"})


class PublishIn(BaseModel):
    # the copy as the redesign stored it (its path under the uploads folder); the current one when not given
    output: str | None = Field(default=None, max_length=1000)


@router.post("/projects/{project_id}/redesign/{drawing_id}/publish")
def publish(project_id: int, drawing_id: int, body: PublishIn | None = None,
            current_user: User = Depends(require_role(*CREATOR_ROLES)), db: Session = Depends(get_db)):
    """The engineer's explicit publication of a verified copy into the
    project archive (OD-15 a): a unique name, never overwritten (409), and
    recorded -- who, when, which copy -- as an activity event."""
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    try:
        done = service.publish(db, project, drawing_id, current_user, (body or PublishIn()).output)
    except service.PublishRefused as exc:
        raise HTTPException(exc.status, str(exc)) from exc
    return {**service.view(db, project, drawing_id), "published": done}


@router.get("/projects/{project_id}/redesign/{drawing_id}/markup.pdf")
def draftsman_pdf(project_id: int, drawing_id: int, _current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    _drawing(db, project, drawing_id)
    data, name = service.draftsman_pdf(db, project, drawing_id)
    plain = re.sub(r"[^A-Za-z0-9 ._()-]", "_", name)
    return Response(data, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"{plain}\"; filename*=UTF-8''{quote(name)}"})
