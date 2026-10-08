"""The sheet numbers of IFC drawings read before the reader recorded them.

A read records every sheet with its title, floors and -- since the Drawings
Log listed sheets under the number their title block prints -- that
number (`app.ifc.dxf.sheets.Sheet.number`). A drawing read before then has
no number on its sheets; this reads the numbers off its stored DXF once
and writes them into the record, so the page takes them from the record
like everything else and never opens a drawing on a request.

    python -m app.ifc.services.sheet_numbers            # every live drawing without numbers
    python -m app.ifc.services.sheet_numbers --all      # every live drawing, read again
    python -m app.ifc.services.sheet_numbers --project 30880
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.ifc import storage
from app.ifc.dxf import sheets as SH
from app.ifc.services import revisions
from app.models import Project, ProjectIfcDrawing

log = logging.getLogger(__name__)


def needs_numbers(drawing: ProjectIfcDrawing) -> bool:
    """No sheet of the record carries a number field yet."""
    sheets = (drawing.meta or {}).get("sheets") or []
    return bool(sheets) and all("number" not in s for s in sheets)


def refresh(db: Session, drawing: ProjectIfcDrawing) -> dict:
    """Read the drawing's sheet numbers off its stored DXF and record them
    on its sheets (by layout name; titles and floors are left as read).
    Returns what was found: {layout: number}."""
    import ezdxf

    path = storage.absolute(drawing.stored_path)
    t0 = time.monotonic()
    doc = ezdxf.readfile(str(path))
    found = {s.name: (s.number, s.number_source) for s in SH.read_sheets(doc)}
    meta = dict(drawing.meta or {})
    sheets = []
    for s in meta.get("sheets") or []:
        number, source = found.get(s["name"], ("", ""))
        sheets.append({**s, "number": number, "number_source": source})
    meta["sheets"] = sheets
    meta["sheet_numbers_read_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    drawing.meta = meta
    flag_modified(drawing, "meta")
    db.commit()
    log.info("ifc.sheet_numbers drawing=%s file=%r sheets=%d numbered=%d seconds=%.1f", drawing.id, drawing.filename,
             len(sheets), sum(1 for s in sheets if s["number"]), time.monotonic() - t0)
    return {name: number for name, (number, _src) in found.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project", help="an EP number: only this project's drawings")
    parser.add_argument("--all", action="store_true", help="read every live drawing again, numbered or not")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        query = db.query(ProjectIfcDrawing).filter(ProjectIfcDrawing.deleted_at.is_(None))
        if args.project:
            project = db.query(Project).filter(Project.ep_number == args.project).first()
            if project is None:
                print(f"No project EP-{args.project}", file=sys.stderr)
                return 2
            query = query.filter(ProjectIfcDrawing.project_id == project.id)
        done = 0
        for drawing in query.order_by(ProjectIfcDrawing.id).all():
            if not args.all and not needs_numbers(drawing):
                continue
            if revisions.superseded(db, drawing.project_id).get(drawing.id) is not None and not args.all:
                continue    # history: the drawing in force is what the log reads
            try:
                found = refresh(db, drawing)
            except Exception as exc:  # noqa: BLE001 -- one unreadable file must not stop the rest
                print(f"{drawing.filename} (id {drawing.id}): not read: {exc}", file=sys.stderr)
                continue
            numbered = {k: v for k, v in found.items() if v}
            print(f"{drawing.filename} (id {drawing.id}): {len(numbered)} of {len(found)} sheets print a number"
                  + (f": {', '.join(sorted(set(numbered.values()))[:6])}" if numbered else ""))
            done += 1
        print(f"{done} drawing(s) updated")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
