"""The voice evacuation amplifier schedule, from the BOQ as per Shop Drawings.

The quantities are the BOQ as per Shop Drawings' (app.services.shop_boq)
once the project has one -- the shop drawings are what is installed
(platform owner, 1 October 2026); until then, the BOQ Floor Wise's, and
the page says so. Both are kept in one form, so either is read the same way.

  GET /projects/{id}/design/amplifier          the schedule as it stands
  PUT /projects/{id}/design/amplifier          set tappings and hand counts
  GET /design/speakers                         the speaker database

The schedule itself is never stored: it is worked out from the floor-wise
BOQ each time the tab is opened, so a speaker added to a floor shows in
the amplifier loading without anything being re-imported
(`app.services.amplifier_calculation`). What a project stores is only
what cannot be derived -- the tapping each speaker is set to, and any
quantity an engineer has adjusted by hand.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import DesignRule, ProjectAmplifierDesign, ProjectFloorSchedule, ProjectShopBoq, User
from app.routers.projects import CREATOR_ROLES, _get_project_or_404
from app.services import activity, amplifier_calculation

router = APIRouter(tags=["amplifier"])

# The rule that says how hard an amplifier may be loaded.
LIMIT_CATEGORY, LIMIT_KEY = "ve.limit", "amplifier_max_load"
MODULE_CATEGORY, MODULE_KEY = "ve.module", "audio_riser"
SUPPLY_CATEGORY, SUPPLY_KEY = "power.supply", "booster"
NAC_CATEGORY, NAC_KEY = "power.module", "nac"
CURRENT_CATEGORY = "power.device"
SPEAKER_CATEGORY = "ve.speaker"
STAIRCASE_CATEGORY, STAIRCASE_KEY = "ve.staircase", "speakers"


def _current(db: Session, category: str) -> list[DesignRule]:
    """The rules in force: the newest version of each key."""
    rows = (db.query(DesignRule)
            .filter(DesignRule.category == category, DesignRule.superseded_at.is_(None))
            .order_by(DesignRule.key, DesignRule.version).all())
    return list({row.key: row for row in rows}.values())


def speaker_database(db: Session) -> dict[str, dict]:
    """Every speaker the platform knows a tapping for, by part number."""
    return {row.key.upper(): dict(row.data or {}) for row in _current(db, SPEAKER_CATEGORY)}


def _staircase(db: Session) -> dict | None:
    """Which speakers are a staircase's, or None where no rule says."""
    rule = next((row for row in _current(db, STAIRCASE_CATEGORY) if row.key == STAIRCASE_KEY), None)
    return dict(rule.data or {}) if rule else None


def _module(db: Session) -> dict:
    """The audio riser module a floor is fed through, and what one carries."""
    rule = next((row for row in _current(db, MODULE_CATEGORY) if row.key == MODULE_KEY), None)
    return dict(rule.data or {}) if rule else {}


def current_database(db: Session) -> dict[str, dict]:
    """Every 24 V appliance the platform knows a current for."""
    return {row.key.upper(): dict(row.data or {}) for row in _current(db, CURRENT_CATEGORY)}


def _supply(db: Session) -> dict:
    rule = next((row for row in _current(db, SUPPLY_CATEGORY) if row.key == SUPPLY_KEY), None)
    return dict(rule.data or {}) if rule else {}


def _nac_module(db: Session) -> dict:
    rule = next((row for row in _current(db, NAC_CATEGORY) if row.key == NAC_KEY), None)
    return dict(rule.data or {}) if rule else {}


def _fraction(db: Session) -> float:
    rule = next((row for row in _current(db, LIMIT_CATEGORY) if row.key == LIMIT_KEY), None)
    return float((rule.data or {}).get("fraction", 0.8)) if rule else 0.8


class PowerOut(BaseModel):
    result: dict
    schedule_file: str | None
    updated_at: datetime | None


Source = ProjectShopBoq | ProjectFloorSchedule


def _source(db: Session, project) -> Source | None:
    """The quantities the amplifier and power schedules are worked out
    from: the BOQ as per Shop Drawings, else the BOQ Floor Wise."""
    shop = db.query(ProjectShopBoq).filter(ProjectShopBoq.project_id == project.id).first()
    if shop is not None and shop.result:
        return shop
    return db.query(ProjectFloorSchedule).filter(ProjectFloorSchedule.project_id == project.id).first()


def _tab(schedule: Source | None) -> str:
    return "BOQ as per Shop Drawings" if isinstance(schedule, ProjectShopBoq) else "BOQ Floor Wise"


def _from_floor_wise(result, schedule: Source | None) -> None:
    """Said on the page while the quantities are not the shop drawings'."""
    if isinstance(schedule, ProjectFloorSchedule):
        result.warnings.insert(0, (
            "These quantities are the BOQ Floor Wise's: the BOQ as per Shop Drawings has not been made yet. "
            "Open that tab on the BOQ page to make it from the IFC drawings; this schedule then follows it."
        ))


def _power(db: Session, project, design: ProjectAmplifierDesign | None,
           schedule: Source | None) -> PowerOut:
    from app.services import power_calculation
    from app.services.schedule_materials import sounder_bases

    result = power_calculation.calculate(
        (schedule.result if schedule else {}) or {},
        currents=current_database(db),
        chosen={key: float(value) for key, value in ((design.currents if design else {}) or {}).items()},
        supply=_supply(db),
        module=_nac_module(db),
        bases=sounder_bases(db, project),
    )
    if schedule is None:
        result.warnings.insert(0, (
            "No BOQ as per Shop Drawings has been made for this project, so there are no devices to draw "
            "from a power supply. Make it on the BOQ page's BOQ as per Shop Drawings tab."
        ))
    _from_floor_wise(result, schedule)
    out = result.as_dict()
    names = {supply["name"] for supply in out["supplies"]}
    out["locations"] = {supply: floor for supply, floor in ((design.locations if design else {}) or {}).items()
                        if supply in names}
    return PowerOut(result=out, schedule_file=schedule.file_name if schedule else None,
                    updated_at=design.updated_at if design else None)


@router.get("/projects/{project_id}/design/power", response_model=PowerOut)
def get_power(
    project_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PowerOut:
    """The 24 V power schedule the project's BOQ as per Shop Drawings makes (see `_source`)."""
    project = _get_project_or_404(db, project_id)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    schedule = _source(db, project)
    return _power(db, project, design, schedule)


class PowerIn(BaseModel):
    """The current this project takes each 24 V appliance at."""

    # {part number: milliamps}
    currents: dict[str, float] = Field(default_factory=dict)


@router.put("/projects/{project_id}/design/power", response_model=PowerOut)
def set_power(
    project_id: int,
    payload: PowerIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> PowerOut:
    """Set the current each appliance is taken at. Only a figure its own
    datasheet gives may be chosen."""
    project = _get_project_or_404(db, project_id)
    known = current_database(db)
    for part, milliamps in payload.currents.items():
        offered = [float(entry["ma"]) for entry in (known.get(part.upper(), {}).get("currents") or [])]
        if offered and float(milliamps) not in offered:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"{part} does not draw {milliamps:g} mA. Its datasheet gives "
                       f"{', '.join(f'{ma:g}' for ma in offered)} mA.",
            )
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    if design is None:
        design = ProjectAmplifierDesign(project_id=project.id)
        db.add(design)
    design.currents = {part: float(ma) for part, ma in payload.currents.items()}
    design.created_by_id = current_user.id
    db.commit()
    db.refresh(design)
    schedule = _source(db, project)
    out = _power(db, project, design, schedule)
    activity.record(db, current_user, "power.set",
                    f"Set the 24 V power schedule: {out.result['total_devices']} devices, "
                    f"{out.result['total_amps']:g} A over {len(out.result['supplies'])} "
                    f"{out.result['supply_part']}",
                    project=project, entity_type="power",
                    detail={"currents": design.currents, "supplies": len(out.result["supplies"])})
    return out


class CountIn(BaseModel):
    """How many of one speaker sit on one floor."""

    floor: str
    part_no: str
    count: int = Field(ge=0)


@router.patch("/projects/{project_id}/design/power/counts", response_model=PowerOut)
def set_power_count(
    project_id: int,
    payload: CountIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> PowerOut:
    """Change how many of a 24 V device a floor has -- on the floor-wise
    BOQ, as the amplifier tab changes a speaker's."""
    from app.services import power_calculation
    from app.services.schedule_materials import sounder_bases

    project = _get_project_or_404(db, project_id)
    schedule = _schedule_or_404(db, project)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    result = power_calculation.calculate(
        schedule.result or {}, currents=current_database(db),
        chosen={key: float(value) for key, value in ((design.currents if design else {}) or {}).items()},
        supply=_supply(db), module=_nac_module(db), bases=sounder_bases(db, project),
    )
    _set_floor_count(db, project, schedule, result.columns, payload, current_user, "24 V device", "power.count")
    return _power(db, project, design, schedule)


class SupplyLocationIn(BaseModel):
    """Where one booster power supply is installed; null to clear it."""

    supply: str = Field(max_length=40)
    floor: str | None = Field(default=None, max_length=160)


@router.patch("/projects/{project_id}/design/power/locations", response_model=PowerOut)
def set_supply_location(
    project_id: int,
    payload: SupplyLocationIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> PowerOut:
    """The floor a BPS is installed on: the engineer's decision."""
    project = _get_project_or_404(db, project_id)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    schedule = _source(db, project)
    current = _power(db, project, design, schedule).result
    if payload.supply not in {supply["name"] for supply in current["supplies"]}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{payload.supply} is not a supply of this schedule")
    floor = (payload.floor or "").strip() or None
    if floor is not None and floor not in {row["floor"] for row in current["floors"]}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"{floor} is not a floor of this schedule")
    if design is None:
        design = ProjectAmplifierDesign(project_id=project.id)
        db.add(design)
    locations = dict(design.locations or {})
    if floor is None:
        locations.pop(payload.supply, None)
    else:
        locations[payload.supply] = floor
    design.locations = locations
    design.created_by_id = current_user.id
    db.commit()
    db.refresh(design)
    activity.record(db, current_user, "power.location",
                    f"Put {payload.supply} on {floor}" if floor else f"Cleared where {payload.supply} is",
                    project=project, entity_type="power", detail={"supply": payload.supply, "floor": floor})
    return _power(db, project, design, schedule)


class DeviceCurrentOut(BaseModel):
    part_no: str
    description: str | None
    currents: list[dict]


@router.get("/design/device-currents", response_model=list[DeviceCurrentOut])
def device_currents(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DeviceCurrentOut]:
    """What each 24 V appliance draws, off its datasheet."""
    return [
        DeviceCurrentOut(part_no=data.get("part_no", key), description=data.get("description"),
                         currents=list(data.get("currents", [])))
        for key, data in sorted(current_database(db).items())
    ]


@router.get("/projects/{project_id}/design/power/export.pdf")
def export_power(
    project_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The 24 V power calculation as a document."""
    from app.services import power_export

    project = _get_project_or_404(db, project_id)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    schedule = _source(db, project)
    if schedule is None or not schedule.result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No BOQ as per Shop Drawings has been made yet")
    doc = power_export.build(project, _power(db, project, design, schedule).result)
    pdf = doc.tobytes()
    doc.close()
    name = f"EP-{project.ep_number} - 24V Power Calculation.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"{name}\"; "
                                                    f"filename*=UTF-8''{quote(name)}"})


class SpeakerOut(BaseModel):
    part_no: str
    description: str | None
    taps: list[float]
    default_tap: float | None


@router.get("/design/speakers", response_model=list[SpeakerOut])
def speakers(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SpeakerOut]:
    """The speaker database: what each speaker can be tapped at, off its
    datasheet, and what the company sets it to."""
    return [
        SpeakerOut(part_no=data.get("part_no", key), description=data.get("description"),
                   taps=[float(tap) for tap in data.get("taps", [])],
                   default_tap=data.get("default_tap"))
        for key, data in sorted(speaker_database(db).items())
    ]


class AmplifierOut(BaseModel):
    result: dict
    # The floor-wise BOQ the schedule is worked out from; null when none
    # has been read, which is the one thing that stops this tab working.
    schedule_file: str | None
    updated_at: datetime | None


def _out(db: Session, project, design: ProjectAmplifierDesign | None,
         schedule: Source | None) -> AmplifierOut:
    result = amplifier_calculation.calculate(
        (schedule.result if schedule else {}) or {},
        taps=speaker_database(db),
        chosen={key: float(value) for key, value in ((design.taps if design else {}) or {}).items()},
        fraction=_fraction(db),
        module=_module(db),
        staircase=_staircase(db),
    )
    if schedule is None:
        result.warnings.insert(0, (
            "No BOQ as per Shop Drawings has been made for this project, so there are no speakers to load "
            "an amplifier with. Make it on the BOQ page's BOQ as per Shop Drawings tab."
        ))
    _from_floor_wise(result, schedule)
    out = result.as_dict()
    # Where each APS cabinet is put: the engineer's, for the cabinets the
    # schedule has now (a cabinet the loading no longer makes drops out).
    names = {cabinet["name"] for cabinet in out["cabinets"]}
    out["locations"] = {cabinet: floor for cabinet, floor in ((design.locations if design else {}) or {}).items()
                        if cabinet in names}
    return AmplifierOut(
        result=out,
        schedule_file=schedule.file_name if schedule else None,
        updated_at=design.updated_at if design else None,
    )


@router.get("/projects/{project_id}/design/amplifier/export.pdf")
def export_amplifier(
    project_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The amplifier calculation as a document, laid out to be issued."""
    from app.services import amplifier_export

    project = _get_project_or_404(db, project_id)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    schedule = _source(db, project)
    if schedule is None or not schedule.result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No BOQ as per Shop Drawings has been made yet")
    doc = amplifier_export.build(project, _out(db, project, design, schedule).result)
    pdf = doc.tobytes()
    doc.close()
    name = f"EP-{project.ep_number} - Amplifier Calculation.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"{name}\"; "
                                                    f"filename*=UTF-8''{quote(name)}"})


@router.patch("/projects/{project_id}/design/amplifier/counts", response_model=AmplifierOut)
def set_count(
    project_id: int,
    payload: CountIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> AmplifierOut:
    """Change how many speakers a floor has.

    The change is made on the BOQ the schedule reads (`_source`), because that is where the
    quantity lives: the two tabs are two views of one number, and a
    speaker added here appears on that BOQ's tab as well. It is
    kept as a correction (`ProjectFloorSchedule.edits`), so re-reading the
    workbook does not undo it.
    """
    project = _get_project_or_404(db, project_id)
    schedule = _schedule_or_404(db, project)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    result = amplifier_calculation.calculate(
        schedule.result or {}, taps=speaker_database(db),
        chosen={key: float(value) for key, value in ((design.taps if design else {}) or {}).items()},
        fraction=_fraction(db),
        module=_module(db),
        staircase=_staircase(db),
    )
    # A staircase speaker's count is changed from its own tab the same way.
    columns = result.columns + (result.staircase.columns if result.staircase else [])
    _set_floor_count(db, project, schedule, columns, payload, current_user, "speaker", "amplifier.count")
    return _out(db, project, design, schedule)


def _schedule_or_404(db: Session, project) -> Source:
    schedule = _source(db, project)
    if schedule is None or not schedule.result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No BOQ as per Shop Drawings has been made yet")
    return schedule


def _set_floor_count(db: Session, project, schedule: Source, columns, payload: CountIn,
                     current_user: User, what: str, action: str) -> None:
    """How many of one part a floor has, set on the BOQ line the part is
    ordered for -- the amplifier and power tabs and the BOQ they read (the
    BOQ as per Shop Drawings, else the BOQ Floor Wise) are views of that one
    number. On the BOQ Floor Wise it is kept as a correction (`edits`), so
    re-reading the workbook does not undo it."""
    from app.services import floor_schedule as floor_schedule_service

    column = next((c for c in columns if c.key == payload.part_no), None)
    if column is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f"{payload.part_no} is not a {what} on this schedule")
    if len(column.lines) != 1:
        # Two BOQ lines settled as the same part: which of them gained a
        # speaker is a question only the engineer can answer.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"{payload.part_no} is ordered for {len(column.lines)} lines of the BOQ "
                   f"({', '.join(column.lines)}). Change the quantity on the {_tab(schedule)} tab, "
                   "where each line is its own row.",
        )
    line = next((item for item in schedule.result.get("items", [])
                 if item.get("description") == column.lines[0]), None)
    if line is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{column.lines[0]} is not on the schedule")

    try:
        schedule.result = floor_schedule_service.set_quantity(
            dict(schedule.result), row=line["row"], floor=payload.floor, quantity=payload.count or None,
        )
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc.args[0])) from exc
    if isinstance(schedule, ProjectFloorSchedule):
        edits = {key: dict(value) for key, value in (schedule.edits or {}).items()}
        edits.setdefault(line["description"], {})[payload.floor] = payload.count
        schedule.edits = edits
    schedule.created_by_id = current_user.id
    db.commit()
    db.refresh(schedule)
    activity.record(db, current_user, action, f"Set {payload.part_no} on {payload.floor} to {payload.count}",
                    project=project, entity_type=action.split(".")[0],
                    detail={"floor": payload.floor, "part_no": payload.part_no, "count": payload.count})


@router.get("/projects/{project_id}/design/amplifier", response_model=AmplifierOut)
def get_amplifier(
    project_id: int,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AmplifierOut:
    """The amplifier schedule the project's BOQ as per Shop Drawings makes (see `_source`)."""
    project = _get_project_or_404(db, project_id)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    schedule = _source(db, project)
    return _out(db, project, design, schedule)


class LocationIn(BaseModel):
    """Where one APS cabinet is installed; null to clear it."""

    cabinet: str = Field(max_length=40)
    floor: str | None = Field(default=None, max_length=160)


@router.patch("/projects/{project_id}/design/amplifier/locations", response_model=AmplifierOut)
def set_location(
    project_id: int,
    payload: LocationIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> AmplifierOut:
    """The floor an APS cabinet -- and the amplifiers in it -- is installed
    on: the engineer's decision, one of the building's floors."""
    project = _get_project_or_404(db, project_id)
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    schedule = _source(db, project)
    current = _out(db, project, design, schedule).result
    if payload.cabinet not in {cabinet["name"] for cabinet in current["cabinets"]}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{payload.cabinet} is not a cabinet of this schedule")
    floor = (payload.floor or "").strip() or None
    if floor is not None and floor not in {row["floor"] for row in current["floors"]}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"{floor} is not a floor of this schedule")
    if design is None:
        design = ProjectAmplifierDesign(project_id=project.id)
        db.add(design)
    locations = dict(design.locations or {})
    if floor is None:
        locations.pop(payload.cabinet, None)
    else:
        locations[payload.cabinet] = floor
    design.locations = locations          # a fresh dict: written
    design.created_by_id = current_user.id
    db.commit()
    db.refresh(design)
    activity.record(db, current_user, "amplifier.location",
                    f"Put {payload.cabinet} on {floor}" if floor else f"Cleared where {payload.cabinet} is",
                    project=project, entity_type="amplifier", detail={"cabinet": payload.cabinet, "floor": floor})
    return _out(db, project, design, schedule)


class AmplifierIn(BaseModel):
    """What a project sets, over what the BOQ already says.

    Only the tappings. How many speakers a floor has belongs to the
    floor-wise BOQ, and is changed through `PATCH .../amplifier/counts`,
    which edits the BOQ itself.
    """

    # {part number: watts}
    taps: dict[str, float] = Field(default_factory=dict)


@router.put("/projects/{project_id}/design/amplifier", response_model=AmplifierOut)
def set_amplifier(
    project_id: int,
    payload: AmplifierIn,
    current_user: User = Depends(require_role(*CREATOR_ROLES)),
    db: Session = Depends(get_db),
) -> AmplifierOut:
    """Set the tapping each speaker is used at, and any quantity adjusted
    by hand. The schedule is worked out again from the BOQ."""
    project = _get_project_or_404(db, project_id)
    known = speaker_database(db)
    for part, watts in payload.taps.items():
        offered = [float(tap) for tap in (known.get(part.upper(), {}).get("taps") or [])]
        if offered and float(watts) not in offered:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"{part} is not tapped at {watts:g} W. Its datasheet offers "
                       f"{', '.join(f'{tap:g}' for tap in offered)} W.",
            )
    design = db.query(ProjectAmplifierDesign).filter(
        ProjectAmplifierDesign.project_id == project.id).first()
    if design is None:
        design = ProjectAmplifierDesign(project_id=project.id)
        db.add(design)
    # Fresh dicts: a JSON column that is mutated in place, or assigned a
    # value equal to what is there, is never written.
    design.taps = {part: float(watts) for part, watts in payload.taps.items()}
    design.created_by_id = current_user.id
    db.commit()
    db.refresh(design)
    schedule = _source(db, project)
    out = _out(db, project, design, schedule)
    activity.record(db, current_user, "amplifier.set",
                    f"Set the amplifier schedule: {out.result['total_speakers']} speakers, "
                    f"{out.result['total_watts']:g} W over {len(out.result['amplifiers'])} "
                    f"{amplifier_calculation.AMPLIFIER_PART}",
                    project=project, entity_type="amplifier",
                    detail={"taps": design.taps, "amplifiers": len(out.result["amplifiers"]),
                            "cabinets": len(out.result["cabinets"])})
    return out
