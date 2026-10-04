"""The BOQ as per Shop Drawings: made from the BOQ as per IFC Drawings, then
the engineer's to edit as the shop drawings move on.

It is kept in the floor-wise schedule's own form (`floor_schedule.Schedule`
as JSON: floors, items with `per_floor`, totals), so everything that reads a
floor-wise BOQ reads it the same way -- the BOQ page's table, the amplifier
schedule and the 24 V power schedule, which take their quantities from it
once it exists (platform owner, 1 October 2026).

**Made from the IFC drawings in force**, the same drawings the Comparison
tab counts: each drawing's latest revision whose symbols are all answered.
A line per IFC device type ("Ceiling Speaker", "Smoke Detector
(Addressable)"), fire alarm and emergency lighting; a typical plan's count
is put on each floor it stands for.

**Floors are named the way the BOQ Floor Wise names them** where it names
the same floor ("3rd Basement", "Level 14") -- so the floor an APS or BPS
cabinet was put on still means the same floor -- else the platform's
own name for it (`comparison.floor_key`).

**A line keeps the part it is ordered as** from the BOQ Floor Wise line of
the same name ("Ceiling Speaker" is EST-S186C there, so here), and the
project's own materials settle the rest where they leave no choice.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ifc.comparison import floor_key
from app.services import floor_schedule
from app.services.symbol_taxonomy import device_in, family_of, system_of

NAME = "BOQ as per Shop Drawings"
_CATEGORIES = {"fire_alarm": "FAS", "emergency_light": "ELS"}


def drawings_in_force(db: Session, project) -> tuple[list[dict], list[dict]]:
    """(the IFC drawings counted, the ones whose symbols are still being
    answered) -- as the Comparison tab takes them."""
    from app.ifc.resolve import resolved_drawing
    from app.ifc.services import revisions

    in_force, pending = [], []
    for d in revisions.in_force(db, project.id):
        r = resolved_drawing(db, d, with_occurrences=False)
        summary = {"id": d.id, "filename": d.filename, "revision": d.revision or "R0"}
        if r["review"]["required"]:
            pending.append({**summary, "review_required": r["review"]["required"]})
        else:
            in_force.append({**r, **summary})
    return in_force, pending


def _norm(text: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def build(drawings: list[dict], floor_wise: dict | None = None) -> dict:
    """The shop drawings BOQ the IFC drawings make, as a floor-wise schedule.
    `floor_wise` is the BOQ Floor Wise as stored, for its floor names and
    the parts its lines are ordered as."""
    floor_wise = floor_wise or {}
    names: dict[str, str] = {}
    for name in floor_wise.get("floors") or []:
        names.setdefault(floor_key(name)[0], name)

    floors: dict[str, tuple[float, str]] = {}      # label -> (order, label)
    warnings: list[str] = []

    def floor(label: str) -> str:
        key, order, nice = floor_key(label)
        shown = names.get(key, nice)
        floors.setdefault(shown, (order, shown))
        return shown

    lines: dict[int, dict] = {}
    for d in drawings:
        for category, system in _CATEGORIES.items():
            for sheet in ((d.get("floor_boq") or {}).get(category) or {"floors": []})["floors"]:
                mult = int(sheet.get("multiplier") or 0)
                numbers = [int(n) for n in sheet.get("floors") or []]
                typical = mult > 1
                placeable = not typical or len(numbers) == mult
                if typical and not placeable and sheet.get("rows"):
                    # Its floors are not known one by one: a column of its own.
                    label = f"{sheet['floor_name']} (x{mult})"
                    floors.setdefault(label, (floor_key(sheet["floor_name"])[1] + 0.001, label))
                    note = (f"{d['filename']} {sheet['sheet']} ({sheet['floor_name']}) stands for {mult} floors "
                            "that its title does not name, so it is one column here; set its floors on the "
                            "BOQ as per IFC Drawings tab and make this BOQ again to spread it.")
                    if note not in warnings:
                        warnings.append(note)
                for row in sheet.get("rows") or []:
                    dt = row["device_type"]
                    line = lines.get(dt["id"])
                    if line is None:
                        device = device_in(dt["name"])
                        line = lines[dt["id"]] = {
                            "description": dt["name"], "catalog_no": None, "unit": dt.get("unit") or "Nos",
                            "manufacturer": None, "remarks": None, "device": device,
                            "family": family_of(device) if device else None,
                            "system": system_of(device) or system, "ifc_code": dt["code"],
                            "per_floor": defaultdict(float), "stated_total": None,
                        }
                    if typical and placeable:
                        for n in numbers:
                            line["per_floor"][floor(f"Level {n}")] += float(row.get("per_floor") or 0)
                    elif typical:
                        line["per_floor"][f"{sheet['floor_name']} (x{mult})"] += float(row.get("qty") or 0)
                    else:
                        line["per_floor"][floor(sheet["floor_name"])] += float(row.get("qty") or 0)

    # The part each line is ordered as: the BOQ Floor Wise line of the same
    # name's, else the one part that BOQ orders the same device as.
    parts: dict[str, dict] = {}
    by_device: dict[str, dict[str, dict]] = defaultdict(dict)
    for item in floor_wise.get("items") or []:
        material = item.get("material")
        if material and material.get("part_no"):
            parts.setdefault(_norm(item.get("description")), material)
            if item.get("device"):
                by_device[item["device"]][material["part_no"]] = material

    # The BOQ Floor Wise's own floor order; a floor only the drawings name
    # goes after its floors below it.
    known = {label: i for i, label in enumerate(floor_wise.get("floors") or [])}

    def place(entry: tuple[float, str]) -> tuple:
        level, label = entry
        if label in known:
            return (known[label], 0.0)
        below = [i for name, i in known.items() if floor_key(name)[1] <= level]
        return (max(below) if below else -1, 0.5 + level / 1e6)

    floor_names = [label for _o, label in sorted(floors.values(), key=place)]
    items = []
    systems_order = {"FAS": 0, "ELS": 1}
    for line in sorted(lines.values(), key=lambda l: systems_order.get(l["system"] or "", 2)):
        counts = {f: floor_schedule.tidy(n) for f, n in line["per_floor"].items() if n}
        if not counts:
            continue
        item = {**line, "per_floor": counts, "row": len(items) + 1}
        material = parts.get(_norm(line["description"]))
        if material is None and len(by_device.get(line["device"] or "", {})) == 1:
            material = next(iter(by_device[line["device"]].values()))
        if material:
            item["material"] = dict(material)
        items.append(item)
    result = {
        "sheet": NAME,
        "floors": floor_names,
        "items": items,
        "columns": [{"heading": f, "kind": "floor", "floors": [f], "typical": False} for f in floor_names],
        "typical_reading": floor_schedule.PER_FLOOR,
        "typical_reason": "",
        "warnings": warnings,
        "devices": sorted({item["device"] for item in items if item.get("device")}),
    }
    return floor_schedule.recompute(result)


def make(db: Session, project, user=None):
    """Make (or make again) the project's shop drawings BOQ from the IFC
    drawings in force. Returns (the row, the drawings still being answered).
    Raises LookupError when no IFC drawing can be counted yet."""
    from app.models import ProjectFloorSchedule, ProjectShopBoq
    from app.services.schedule_materials import settle_unambiguous

    drawings, pending = drawings_in_force(db, project)
    if not drawings:
        raise LookupError(
            "No IFC drawing can be counted yet: read the fire alarm IFC drawings on the BOQ as per IFC "
            "Drawings tab and answer their symbols first."
            + (f" {len(pending)} drawing{'s are' if len(pending) != 1 else ' is'} still being answered." if pending else "")
        )
    floor_wise = db.query(ProjectFloorSchedule).filter(ProjectFloorSchedule.project_id == project.id).first()
    result = build(drawings, floor_wise.result if floor_wise is not None else None)
    if pending:
        result["warnings"] = result["warnings"] + [
            f"{d['filename']} is not counted: {d['review_required']} of its symbols still need an answer "
            "on the BOQ as per IFC Drawings tab." for d in pending]
    row = db.query(ProjectShopBoq).filter(ProjectShopBoq.project_id == project.id).first()
    if row is None:
        row = ProjectShopBoq(project_id=project.id, result=result, source={})
        db.add(row)
    row.result = result
    row.source = {"drawings": [{k: d[k] for k in ("id", "filename", "revision")} for d in drawings],
                  "made_at": datetime.now(timezone.utc).isoformat()}
    row.created_by_id = user.id if user is not None else row.created_by_id
    db.flush()
    settle_unambiguous(db, project, row)
    db.commit()
    db.refresh(row)
    return row, pending
