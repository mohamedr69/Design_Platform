"""Logs > Samples: the Request Material email for a project's sample board
(app.services.sample_request).

  POST /projects/{id}/samples/request-material   draft the email; nothing is sent

Offered while the fire alarm has no sample board among the project's
transmittals. The draft comes back for the engineer to edit and send from
their own mail.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import User
from app.routers.projects import CREATOR_ROLES, _get_project_or_404
from app.services import activity, sample_request

router = APIRouter(tags=["samples"])


@router.post("/projects/{project_id}/samples/request-material")
def request_material(project_id: int, current_user: User = Depends(require_role(*CREATOR_ROLES)),
                     db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    try:
        d = sample_request.draft(db, project)
    except sample_request.RequestError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.commit()     # the usage log and the stored reading
    activity.record(db, current_user, "samples.request_drafted", "Drafted the sample material request email",
                    project=project, entity_type="project", entity_id=project.id,
                    detail={"model": d.model, "from_cache": d.from_cache, "to_confirm": len(d.to_confirm),
                            "not_in_schedule": len(d.not_in_schedule)})
    return {"to": d.to, "subject": d.subject, "body": d.body, "to_confirm": d.to_confirm,
            "not_in_schedule": d.not_in_schedule, "els_in_scope": d.els_in_scope, "model": d.model,
            "from_cache": d.from_cache}
