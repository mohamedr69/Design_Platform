"""Drawings > Assign Draftsman (app.services.draftsman_assignment).

  GET  /projects/{id}/draftsman                 the ten items, the draftsman, the log
  PUT  /projects/{id}/draftsman/items/{key}     skip / unskip, or mark a manual item ready / not ready
  POST /projects/{id}/draftsman/assign          assign: the Outlook draft (.eml), and a log entry
"""
from __future__ import annotations

import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import User
from app.routers.projects import CREATOR_ROLES, _get_project_or_404
from app.services import activity
from app.services import draftsman_assignment as service

router = APIRouter(prefix="/projects", tags=["draftsman"])
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _view(db: Session, project) -> dict:
    row = service.state(db, project)
    entries = service.items(db, project)
    db.commit()
    return {
        "items": entries,
        "ready": not any(e["state"] == "missing" for e in entries),
        "draftsman": {"name": row.draftsman_name or service.DEFAULT_NAME,
                      "email": row.draftsman_email or service.DEFAULT_EMAIL},
        "known": service.known_draftsmen(db),
        "log": list(reversed(row.log or [])),
    }


@router.get("/{project_id}/draftsman")
def get_assignment(project_id: int, _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _view(db, _get_project_or_404(db, project_id))


class ItemIn(BaseModel):
    # skip | unskip | ready | not_ready
    action: str = Field(pattern="^(skip|unskip|ready|not_ready)$")


@router.put("/{project_id}/draftsman/items/{key}")
def set_item(project_id: int, key: str, body: ItemIn, current_user: User = Depends(require_role(*CREATOR_ROLES)),
             db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    item = service.BY_KEY.get(key)
    if item is None:
        raise HTTPException(404, "No such item")
    if body.action in ("ready", "not_ready") and not item.manual:
        raise HTTPException(422, f"{item.name} is checked by the platform: skip it instead")
    row = service.state(db, project)
    skipped, ready = list(row.skipped or []), list(row.ready or [])
    if body.action == "skip" and key not in skipped:
        skipped.append(key)
    elif body.action == "unskip":
        skipped = [k for k in skipped if k != key]
    elif body.action == "ready" and key not in ready:
        ready.append(key)
    elif body.action == "not_ready":
        ready = [k for k in ready if k != key]
    row.skipped, row.ready = skipped, ready
    db.commit()
    words = {"skip": "skipped", "unskip": "un-skipped", "ready": "marked ready", "not_ready": "marked not ready"}
    activity.record(db, current_user, "draftsman.item", f"{item.name} {words[body.action]} for the draftsman",
                    project=project, entity_type="draftsman", detail={"key": key, "action": body.action})
    return _view(db, project)


class AssignIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)


@router.post("/{project_id}/draftsman/assign")
def assign(project_id: int, body: AssignIn, current_user: User = Depends(require_role(*CREATOR_ROLES)),
           db: Session = Depends(get_db)):
    """Assign the project to the draftsman: the email as an Outlook draft,
    the schedules attached, to check and send -- and a log entry."""
    project = _get_project_or_404(db, project_id)
    email = body.email.strip()
    if not _EMAIL.match(email):
        raise HTTPException(422, "That is not an email address")
    try:
        eml, entry = service.assign(db, project, current_user, body.name.strip(), email)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    db.commit()
    activity.record(db, current_user, "draftsman.assigned",
                    f"Assigned the shop drawings to {entry['name']} ({entry['email']}), "
                    f"{len(entry['files'])} file{'s' if len(entry['files']) != 1 else ''} attached",
                    project=project, entity_type="draftsman", detail={"email": entry["email"], "files": entry["files"]})
    name = f"EP-{project.ep_number} - Shop drawings assignment - {entry['name']}.eml"
    return Response(eml, media_type="message/rfc822",
                    headers={"Content-Disposition": f"attachment; filename=\"{re.sub(r'[^A-Za-z0-9 ._-]', '_', name)}\"; "
                                                    f"filename*=UTF-8''{quote(name)}"})
