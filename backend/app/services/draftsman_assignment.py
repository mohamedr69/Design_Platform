"""Drawings > Assign Draftsman: what a draftsman is handed when a project is
assigned to them, whether each is ready, and the email that hands it over.

The ten items are the company's (the design manager's letter to the
draftsmen, 2 October 2026). Seven the platform holds and checks for itself
-- the interface schedule, the drawings review, the APS and BPS
calculations, the drawings received, the title block, the shop drawings
reference; three it does not draw up yet -- the system legend, the loop
schedule, the emergency lighting circuits -- and the engineer marks those
ready. An item that is not ready is the engineer's to fix or to skip; the
project is assigned once every item is one or the other.

Assigning makes an Outlook draft (.eml, opened unsent): To the draftsman,
the letter with each item's status and the drawings received log, and the
schedules the platform draws attached. The engineer reads it and presses
Send -- nothing leaves without them. Every assignment is logged.
"""
from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.timeutils import utc_now
from app.models import Project, ProjectDraftsmanAssignment, User

DEFAULT_NAME, DEFAULT_EMAIL = "Syed Siraj", "syed.siraj@AL-MAJID.com"
# An attachment over this goes by its place in the project folder instead:
# a mail system turns away a message much over 20 MB.
MAX_ATTACHMENT = 10 * 1024 * 1024
MAX_MESSAGE = 20 * 1024 * 1024


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    detail: str            # what the letter says of it
    manual: bool = False   # the platform cannot check it: the engineer marks it ready


ITEMS: list[Item] = [
    Item("interfaces", "Fire Alarm Interface Schedule",
         "All required FA interfaces listed floor-wise. The interfaces shall be double-checked against the "
         "corresponding drawings referenced in the schedule."),
    Item("review", "Drawings Review Instructions",
         "Floor-wise review instructions. Any device that has been added, replaced, relocated or deleted is "
         "clearly identified."),
    Item("legend", "System Legend",
         "Legend based on our standard system requirements, including items such as APS, BPS, CC2A, CC1, etc.",
         manual=True),
    Item("aps", "APS Calculation", "Complete APS calculation sheet. All required circuits and modules clearly indicated."),
    Item("bps", "BPS Calculation", "Complete BPS calculation sheet with the required system details."),
    Item("loops", "Fire Alarm Loop Schedule", "Loop distribution and panel locations.", manual=True),
    Item("els_circuits", "Emergency Lighting Circuit Distribution",
         "Circuit distribution for the emergency lighting system, floor-wise / system-wise as applicable.", manual=True),
    Item("drawings_log", "Drawings Received Log",
         "A complete log of all drawings received for the project, for proper tracking and coordination."),
    Item("title_block", "Title Block", "Approved / project-specific title block to be used for the shop drawings."),
    Item("sd_reference", "Shop Drawings Reference",
         "Relevant reference drawings and information required for preparation of the shop drawings."),
]
BY_KEY = {item.key: item for item in ITEMS}


def state(db: Session, project: Project) -> ProjectDraftsmanAssignment:
    row = db.query(ProjectDraftsmanAssignment).filter(ProjectDraftsmanAssignment.project_id == project.id).first()
    if row is None:
        row = ProjectDraftsmanAssignment(project_id=project.id, skipped=[], ready=[], log=[])
        db.add(row)
        db.flush()
    return row


# --- the checks ----------------------------------------------------------------


def _requirements(db: Session, project: Project) -> list[dict]:
    """Drawings > Actions Required, every system of the project: the
    contractor's documents with whether each was received."""
    from app.services import drawing_requirements

    out = []
    for system in drawing_requirements.systems_of(project):
        status = drawing_requirements.status(db, project, system["code"])
        for group in status["groups"]:
            for item in group["items"]:
                if item.get("kind") == "document":
                    out.append({**item, "system": system["code"], "system_name": system["name"]})
    return out


def _interfaces(db: Session, project: Project) -> tuple[bool, str]:
    from app.interfaces import service

    view = service.build(db, project)
    if view.get("primary") != "current":
        # C7: last published or nothing -- not evidence the drawings show now
        state = "last published, not verified now" if view.get("primary") == "published" else "not read completely"
        why = "; ".join(view.get("view_reasons") or [])
        return False, f"The FA interface schedule is {state}" + (f" ({why})" if why else "") + " (BOQ > FA Interfaces)."
    rows = len(view.get("rows") or [])
    if not rows:
        return False, "The FA interfaces have not been read off the IFC drawings yet (BOQ > FA Interfaces)."
    if view.get("view_state") != "current":
        return True, f"{rows} interfaces, floor-wise (provisional: {'; '.join(view.get('view_reasons') or [])})"
    return True, f"{rows} interfaces, floor-wise"


def _reviews(db: Session, project: Project) -> list[tuple]:
    """(drawing, its review row or None) for every fire alarm IFC drawing in force."""
    from app.ifc.services import revisions
    from app.models import ProjectDrawingReview

    out = []
    for drawing in revisions.in_force(db, project.id):
        row = (db.query(ProjectDrawingReview)
               .filter(ProjectDrawingReview.project_id == project.id, ProjectDrawingReview.drawing_id == drawing.id).first())
        out.append((drawing, row))
    return out


def _review(db: Session, project: Project) -> tuple[bool, str]:
    from app.review import service

    reviews = _reviews(db, project)
    if not reviews:
        return False, "No fire alarm IFC drawing is in force to review."
    problems, accepted = [], 0
    for drawing, row in reviews:
        if row is None or row.status != "done":
            problems.append(f"{drawing.filename}: the review has not finished"
                            if row is not None else f"{drawing.filename}: not reviewed yet")
            continue
        counts = service.build(db, project, drawing)["counts"]
        accepted += counts["accepted"]
        if counts["open"]:
            problems.append(f"{drawing.filename}: {counts['open']} finding{'s' if counts['open'] != 1 else ''} "
                            "still to decide")
    if problems:
        return False, "; ".join(problems)
    return True, f"{accepted} change{'s' if accepted != 1 else ''} accepted for the draftsman"


def _amplifier(db: Session, project: Project) -> tuple[bool, str]:
    from app.models import ProjectAmplifierDesign
    from app.routers.amplifier import _out, _source

    schedule = _source(db, project)
    if schedule is None:
        return False, "No BOQ for the amplifier schedule (BOQ as per Shop Drawings)."
    design = db.query(ProjectAmplifierDesign).filter(ProjectAmplifierDesign.project_id == project.id).first()
    result = _out(db, project, design, schedule).result
    if not result.get("cabinets"):
        return False, "No APS cabinet is worked out yet (Calculations > Amplifier)."
    unplaced = [c["name"] for c in result["cabinets"] if not (result.get("locations") or {}).get(c["name"])]
    if unplaced:
        return False, f"No location chosen for {', '.join(unplaced[:4])} (Calculations > Amplifier)."
    return True, f"{len(result['cabinets'])} APS cabinet{'s' if len(result['cabinets']) != 1 else ''}"


def _power(db: Session, project: Project) -> tuple[bool, str]:
    from app.models import ProjectAmplifierDesign
    from app.routers.amplifier import _power, _source

    schedule = _source(db, project)
    if schedule is None:
        return False, "No BOQ for the 24 V power schedule (BOQ as per Shop Drawings)."
    design = db.query(ProjectAmplifierDesign).filter(ProjectAmplifierDesign.project_id == project.id).first()
    result = _power(db, project, design, schedule).result
    supplies = result.get("supplies") or []
    if not supplies:
        return False, "No BPS is worked out yet (Calculations > Power)."
    unplaced = [s["name"] for s in supplies if not (result.get("locations") or {}).get(s["name"])]
    if unplaced:
        return False, f"No location chosen for {', '.join(unplaced[:4])} (Calculations > Power)."
    return True, f"{len(supplies)} BPS"


def _received(requirements: list[dict], key: str) -> tuple[bool, str]:
    item = next((r for r in requirements if r["key"] == key), None)
    if item is None:
        return False, "Not on the project's list of required documents."
    if not item["received"]:
        return False, f"Not received: {item['remarks']} ({item['folder']})"
    return True, item["remarks"]


def _log(requirements: list[dict]) -> tuple[bool, str]:
    missing = [r for r in requirements if not r["received"]]
    if missing:
        names = ", ".join(f"{r['name']} ({r['system']})" for r in missing[:5])
        more = f" and {len(missing) - 5} more" if len(missing) > 5 else ""
        return False, f"{len(missing)} not received: {names}{more} (Drawings > Actions Required)"
    return True, f"All {len(requirements)} required documents received"


def items(db: Session, project: Project) -> list[dict]:
    """The ten, each {key, n, name, detail, manual, state, reason}: state
    "ready", "missing" (not received / not ready) or "skipped"."""
    row = state(db, project)
    requirements = _requirements(db, project)
    checks = {
        "interfaces": lambda: _interfaces(db, project),
        "review": lambda: _review(db, project),
        "aps": lambda: _amplifier(db, project),
        "bps": lambda: _power(db, project),
        "drawings_log": lambda: _log(requirements),
        "title_block": lambda: _received(requirements, "title_block"),
        "sd_reference": lambda: _received(requirements, "sd_reference"),
    }
    out = []
    for n, item in enumerate(ITEMS, 1):
        if item.manual:
            ready = item.key in (row.ready or [])
            reason = "Marked ready by the engineer" if ready else "To be prepared: mark it ready once it is"
        else:
            try:
                ready, reason = checks[item.key]()
            except Exception as exc:  # noqa: BLE001 -- one check failing is that item not ready, not the page
                ready, reason = False, f"Could not be checked ({type(exc).__name__}: {exc})"[:300]
        skipped = item.key in (row.skipped or [])
        out.append({"key": item.key, "n": n, "name": item.name, "detail": item.detail, "manual": item.manual,
                    "state": "skipped" if skipped else "ready" if ready else "missing",
                    "ready": ready, "reason": reason})
    return out


# --- the email -------------------------------------------------------------------


def _first_name(name: str) -> str:
    return (name or "").strip().split(" ")[0] or "Sir"


def letter(project: Project, entries: list[dict], name: str, sender: str, attached: dict[str, list[str]],
           requirements: list[dict]) -> tuple[str, str]:
    """(subject, body) -- the design manager's letter, with where each item
    stands for this project and the drawings received log."""
    title = f"EP-{project.ep_number} {project.project_name or ''}".strip()
    lines = [f"Dear {_first_name(name)},", "",
             f"The project {title} is assigned to you for the shop drawings. Please find below the documents and "
             "schedules for it, to keep the design process clear and to minimise any possible mistakes:", ""]
    for entry in entries:
        item = BY_KEY[entry["key"]]
        lines.append(f"{entry['n']}. {item.name}")
        lines.append(f"   - {item.detail}")
        if entry["state"] == "skipped":
            lines.append("   - Not provided for this project.")
        elif attached.get(item.key):
            lines.append(f"   - Attached: {', '.join(attached[item.key])}")
        elif item.manual:
            lines.append("   - Provided (project folder).")
        else:
            held = next((r for r in requirements if r["key"] == item.key and r["files"]), None)
            lines.append(f"   - In the project folder: {held['files'][0]['path']}" if held else f"   - {entry['reason']}")
        lines.append("")
    lines.append("Drawings received log:")
    for r in requirements:
        when = (r.get("received_date") or "")[:10]
        lines.append(f"   - {r['system']} | {r['name']}: "
                     + (f"received {when} ({r['file_count']} file{'s' if r['file_count'] != 1 else ''})"
                        if r["received"] else "NOT RECEIVED"))
    lines += ["",
              "Please ensure that all the above documents are reviewed carefully before starting the shop drawings. "
              "Any discrepancy, missing information, or conflict between the provided schedules and the "
              "corresponding IFC/reference drawings shall be highlighted before proceeding.", "",
              "The purpose of this arrangement is to standardize our workflow, improve coordination, and avoid "
              "unnecessary design errors or revisions.", "",
              "Best Regards,", sender]
    return f"{title} - Shop drawings assignment", "\n".join(lines)


def _received_log_xlsx(project: Project, requirements: list[dict]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Drawings Received"
    ws.append([f"EP-{project.ep_number} {project.project_name or ''} - Drawings Received Log - "
               f"{datetime.now():%d %b %Y}"])
    ws["A1"].font = Font(bold=True, size=12)
    ws.append([])
    ws.append(["System", "Document", "Purpose", "Status", "Received", "Files", "Latest file", "Folder"])
    for cell in ws[3]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="B91C1C")
    for r in requirements:
        ws.append([r["system_name"], r["name"], r["purpose"], "Received" if r["received"] else "Not received",
                   (r.get("received_date") or "")[:10], r["file_count"], (r["files"][0]["name"] if r["files"] else ""),
                   r["folder"]])
    for column, width in zip("ABCDEFGH", (22, 34, 44, 14, 12, 7, 40, 46)):
        ws.column_dimensions[column].width = width
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def attachments(db: Session, project: Project, entries: list[dict], requirements: list[dict]) -> tuple[list[tuple[str, bytes, str]], dict[str, list[str]], list[str]]:
    """(files [(name, bytes, mime)], item key -> the names attached for it,
    notes on what could not be attached). Only for the items not skipped."""
    from app.services import document_control

    wanted = {e["key"] for e in entries if e["state"] != "skipped"}
    title = f"EP-{project.ep_number}"
    files: list[tuple[str, bytes, str]] = []
    named: dict[str, list[str]] = {}
    notes: list[str] = []

    def add(key: str, name: str, data: bytes, mime: str) -> None:
        if len(data) > MAX_ATTACHMENT:
            notes.append(f"{name} is {len(data) / 1e6:.1f} MB: not attached")
            return
        files.append((name, data, mime))
        named.setdefault(key, []).append(name)

    def pdf_of(doc) -> bytes:
        data = doc.tobytes(garbage=1, deflate=True)
        doc.close()
        return data

    if "interfaces" in wanted:
        from app.interfaces import pdf as interfaces_pdf
        from app.interfaces import service as interfaces
        from app.interfaces.export import workbook

        view = interfaces.build(db, project)
        add("interfaces", f"{title} FA Interface Schedule.pdf", pdf_of(interfaces_pdf.build(view)), "application/pdf")
        add("interfaces", f"{title} FA Interface Schedule.xlsx", workbook(view).getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if "review" in wanted:
        from app.ifc import storage
        from app.review import markup
        from app.review import service as review

        for drawing, row in _reviews(db, project):
            if row is None or row.status != "done":
                continue
            view = review.build(db, project, drawing)
            doc = markup.build(view, project, str(storage.absolute(row.pdf_path)) if row.pdf_path else None)
            stem = re.sub(r"\.(dwg|dxf)$", "", drawing.filename, flags=re.I)
            add("review", f"{title} Draftsman Schedule - {stem} {drawing.revision or 'R0'}.pdf", pdf_of(doc),
                "application/pdf")
    if "aps" in wanted or "bps" in wanted:
        from app.models import ProjectAmplifierDesign
        from app.routers.amplifier import _out, _power, _source
        from app.services import amplifier_export, power_export

        schedule = _source(db, project)
        design = db.query(ProjectAmplifierDesign).filter(ProjectAmplifierDesign.project_id == project.id).first()
        if schedule is not None and "aps" in wanted:
            add("aps", f"{title} APS Calculation.pdf",
                pdf_of(amplifier_export.build(project, _out(db, project, design, schedule).result)), "application/pdf")
        if schedule is not None and "bps" in wanted:
            add("bps", f"{title} BPS Calculation.pdf",
                pdf_of(power_export.build(project, _power(db, project, design, schedule).result)), "application/pdf")
    if "drawings_log" in wanted:
        add("drawings_log", f"{title} Drawings Received Log.xlsx", _received_log_xlsx(project, requirements),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    root = Path(project.source_folder_path) if project.source_folder_path else None
    for key in ("title_block", "sd_reference"):
        item = next((r for r in requirements if r["key"] == key), None)
        if key not in wanted or item is None or not item["files"] or root is None:
            continue
        latest = item["files"][0]
        path = root / latest["path"]
        try:
            data = open(document_control._os_path(path), "rb").read()
        except OSError:
            notes.append(f"{latest['name']} could not be read from the project folder")
            continue
        add(key, latest["name"], data, "application/octet-stream")
    # The message as a whole stays under what a mail system takes.
    total = sum(len(d) for _n, d, _m in files)
    while total > MAX_MESSAGE and files:
        name, data, _mime = max(files, key=lambda f: len(f[1]))
        files = [f for f in files if f[0] != name]
        for names in named.values():
            if name in names:
                names.remove(name)
        notes.append(f"{name} ({len(data) / 1e6:.1f} MB) left out to keep the email under {MAX_MESSAGE // 2**20} MB")
        total -= len(data)
    return files, named, notes


def draft(project: Project, to_name: str, to_email: str, sender: User, subject: str, body: str,
          files: list[tuple[str, bytes, str]]) -> bytes:
    """The email as an unsent Outlook message (.eml with X-Unsent): it opens
    as a draft to check and send."""
    message = EmailMessage()
    message["To"] = formataddr((to_name, to_email)) if to_name else to_email
    message["Subject"] = subject
    message["X-Unsent"] = "1"
    message.set_content(body)
    for name, data, mime in files:
        maintype, _, subtype = mime.partition("/")
        message.add_attachment(data, maintype=maintype, subtype=subtype or "octet-stream", filename=name)
    return message.as_bytes()


def assign(db: Session, project: Project, user: User, name: str, email: str) -> tuple[bytes, dict]:
    """Assign the project: the draft email and the log entry. Raises
    ValueError when an item is neither ready nor skipped."""
    entries = items(db, project)
    missing = [e for e in entries if e["state"] == "missing"]
    if missing:
        raise ValueError("Not ready: " + "; ".join(f"{e['n']}. {e['name']}" for e in missing)
                         + ". Prepare them or skip them first.")
    requirements = _requirements(db, project)
    files, named, notes = attachments(db, project, entries, requirements)
    sender = (getattr(user, "full_name", None) or user.email or "").strip()
    subject, body = letter(project, entries, name, sender, named, requirements)
    if notes:
        body = body.replace("\nBest Regards,", "\nNot attached (see the project folder):\n"
                            + "\n".join(f"   - {n}" for n in notes) + "\n\nBest Regards,")
    eml = draft(project, name, email, user, subject, body, files)
    row = state(db, project)
    row.draftsman_name, row.draftsman_email = name, email
    entry = {"at": utc_now().isoformat(timespec="seconds"), "by": sender, "by_id": user.id, "name": name,
             "email": email, "subject": subject,
             "items": [{"key": e["key"], "name": e["name"], "state": e["state"], "reason": e["reason"]} for e in entries],
             "files": [n for n, _d, _m in files], "notes": notes, "size": len(eml)}
    row.log = [*(row.log or []), entry]
    row.updated_at = utc_now()
    db.flush()
    return eml, entry


def known_draftsmen(db: Session) -> list[dict]:
    """The draftsmen assigned before, on any project -- and the company's."""
    seen: dict[str, str] = {DEFAULT_EMAIL.lower(): DEFAULT_NAME}
    names = {DEFAULT_EMAIL.lower(): (DEFAULT_NAME, DEFAULT_EMAIL)}
    for row in db.query(ProjectDraftsmanAssignment).all():
        for entry in row.log or []:
            key = (entry.get("email") or "").lower()
            if key and key not in seen:
                seen[key] = entry.get("name") or ""
                names[key] = (entry.get("name") or "", entry.get("email"))
    return [{"name": n, "email": e} for n, e in names.values()]
