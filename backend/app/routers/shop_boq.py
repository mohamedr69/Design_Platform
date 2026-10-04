"""The BOQ page's "BOQ as per Shop Drawings" tab (app.services.shop_boq).

  GET    /projects/{id}/shop-boq                         it, made from the IFC BOQ the first time
  POST   /projects/{id}/shop-boq/make                    make it again from the IFC BOQ
  PATCH  .../shop-boq/items/{row}                        set one floor's quantity
  PATCH  .../shop-boq/items/{row}/material               settle which part the line is
  GET    /projects/{id}/shop-boq/materials/by-line       the parts a line may be settled as
  GET    /projects/{id}/shop-boq/export.pdf              it as a document
  DELETE /projects/{id}/shop-boq                         clear it

Answered in the BOQ Floor Wise tab's own form, so the page shows both with
one table. The amplifier and power schedules read their quantities from it
once it exists (app.routers.amplifier).
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import ProjectShopBoq, User
from app.routers.floor_schedule import FloorScheduleOut, MaterialChoiceIn, MaterialOptionsOut, MaterialOut, QuantityIn
from app.routers.projects import CREATOR_ROLES, _get_project_or_404
from app.services import activity, floor_schedule, shop_boq
from app.services.schedule_materials import device_materials, rank_for_line

router = APIRouter(prefix="/projects", tags=["shop drawings BOQ"])


def _out(row: ProjectShopBoq | None, note: str | None = None) -> FloorScheduleOut:
    drawings = ((row.source or {}).get("drawings") if row else None) or []
    made = ", ".join(f"{d['filename']} ({d.get('revision') or 'R0'})" for d in drawings)
    return FloorScheduleOut(
        result=row.result if row else None,
        file_name=shop_boq.NAME if row else None,
        sheet_name=None,
        archive_path=None,
        # What it was made from, for the page to name.
        source_path=made or None,
        filed_note=note,
        updated_at=row.updated_at if row else None,
    )


def _row(db: Session, project) -> ProjectShopBoq | None:
    return db.query(ProjectShopBoq).filter(ProjectShopBoq.project_id == project.id).first()


def _row_or_404(db: Session, project) -> ProjectShopBoq:
    row = _row(db, project)
    if row is None or not row.result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="The shop drawings BOQ has not been made yet")
    return row


@router.get("/{project_id}/shop-boq", response_model=FloorScheduleOut)
def get_shop_boq(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FloorScheduleOut:
    """The shop drawings BOQ. The first time it is asked for it starts as
    the BOQ as per IFC Drawings; after that it is what the engineers made it."""
    project = _get_project_or_404(db, project_id)
    row = _row(db, project)
    if row is not None:
        return _out(row)
    try:
        row, pending = shop_boq.make(db, project)
    except LookupError as exc:
        return _out(None, str(exc))
    activity.record(db, current_user, "shop_boq.made", "Made the BOQ as per Shop Drawings from the IFC BOQ",
                    project=project, entity_type="shop_boq")
    return _out(row, "Made from the BOQ as per IFC Drawings. Edit the quantities as the shop drawings have them.")


@router.post("/{project_id}/shop-boq/make", response_model=FloorScheduleOut)
def make_again(
    project_id: int,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> FloorScheduleOut:
    """Start again from the BOQ as per IFC Drawings: every quantity set by
    hand is replaced (the page asks first)."""
    project = _get_project_or_404(db, project_id)
    try:
        row, _pending = shop_boq.make(db, project, current_user)
    except LookupError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    activity.record(db, current_user, "shop_boq.made", "Made the BOQ as per Shop Drawings again from the IFC BOQ",
                    project=project, entity_type="shop_boq")
    return _out(row, "Made again from the BOQ as per IFC Drawings.")


@router.patch("/{project_id}/shop-boq/items/{row}", response_model=FloorScheduleOut)
def set_quantity(
    project_id: int,
    row: int,
    payload: QuantityIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> FloorScheduleOut:
    project = _get_project_or_404(db, project_id)
    stored = _row_or_404(db, project)
    targets = payload.floors or ([payload.floor] if payload.floor else [])
    if not targets:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Say which floor, or floors, to set")
    try:
        stored.result = floor_schedule.set_quantity(dict(stored.result), row=row, floor=targets,
                                                    quantity=payload.quantity)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc.args[0])) from exc
    stored.created_by_id = current_user.id
    db.commit()
    db.refresh(stored)
    item = next((i for i in stored.result.get("items", []) if i.get("row") == row), {})
    activity.record(db, current_user, "shop_boq.quantity",
                    f"Set {item.get('description', f'row {row}')} on {', '.join(targets)} to {payload.quantity or 0:g}",
                    project=project, entity_type="shop_boq",
                    detail={"row": row, "floors": targets, "quantity": payload.quantity})
    return _out(stored)


@router.patch("/{project_id}/shop-boq/items/{row}/material", response_model=FloorScheduleOut)
def choose_material(
    project_id: int,
    row: int,
    payload: MaterialChoiceIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> FloorScheduleOut:
    """Which of the project's proposed materials a line is -- the part the
    amplifier schedule reads a speaker's taps from."""
    project = _get_project_or_404(db, project_id)
    stored = _row_or_404(db, project)
    result = dict(stored.result)
    items = [dict(item) for item in result.get("items", [])]
    wanted = next((item for item in items if item.get("row") == row), None)
    if wanted is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no line at row {row}")
    chosen = (payload.part_no or "").strip()
    if chosen:
        offered = {m["part_no"]: m for m in device_materials(db, project, wanted.get("system"))}
        if chosen not in offered:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                detail=f"{chosen} is not a device proposed for this project's "
                                       f"{wanted.get('system') or 'schedule'}")
        wanted["material"] = {"part_no": chosen, "description": offered[chosen].get("description"),
                              "manufacturer": offered[chosen].get("manufacturer")}
    else:
        wanted.pop("material", None)
    result["items"] = items
    stored.result = result
    stored.created_by_id = current_user.id
    db.commit()
    db.refresh(stored)
    return _out(stored)


@router.get("/{project_id}/shop-boq/materials/by-line", response_model=MaterialOptionsOut)
def material_options(
    project_id: int,
    system: str | None = None,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MaterialOptionsOut:
    project = _get_project_or_404(db, project_id)
    materials = device_materials(db, project, system)
    stored = _row(db, project)
    items = (stored.result or {}).get("items", []) if stored is not None else []
    wanted = (system or "").strip().upper()
    return MaterialOptionsOut(
        materials=[MaterialOut(**m) for m in materials],
        by_line={
            item["row"]: [m["part_no"] for m in rank_for_line(item, materials)]
            for item in items
            if item.get("row") is not None and (not wanted or (item.get("system") or "").strip().upper() == wanted)
        },
    )


@router.get("/{project_id}/shop-boq/export.pdf")
def export_pdf(
    project_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import schedule_export

    project = _get_project_or_404(db, project_id)
    stored = _row_or_404(db, project)
    doc = schedule_export.build(project, stored.result, name="BOQ AS PER SHOP DRAWINGS")
    pdf = doc.tobytes()
    doc.close()
    name = f"EP-{project.ep_number} - BOQ as per Shop Drawings.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"{name}\"; "
                                                    f"filename*=UTF-8''{quote(name)}"})


@router.delete("/{project_id}/shop-boq", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def clear(
    project_id: int,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(db, project_id)
    row = _row(db, project)
    if row is not None:
        db.delete(row)
        db.commit()
        activity.record(db, current_user, "shop_boq.cleared", "Cleared the BOQ as per Shop Drawings",
                        project=project, entity_type="shop_boq")
