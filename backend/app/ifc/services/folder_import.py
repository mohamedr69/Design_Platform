"""The IFC drawings as the project folder holds them.

The consultant's IFC drawings are filed in the project's own folder (the
SharePoint library every office PC syncs), under 03- Drawings/IFC and the
discipline's folder -- the fire alarm's under Electrical/FA. The Drawings
Log reads the IFC from there: this module lists what that folder holds,
says which of its files are read into the platform (a read drawing
records where it is filed, `archive_path`; the platform files its own
uploads there too), and queues an unread DWG or DXF for the IFC worker
exactly as an upload of the same file would be queued. Nothing is read
on a page request: the listing is the folder's names and sizes, and the
read is the worker's.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.ifc.services import revisions, upload
from app.models import BackgroundJob, ProjectIfcDrawing
from app.services import project_folders
from app.services.document_control import _os_path
from app.services.jobs import ACTIVE

# Where each system's IFC drawings are filed. Only the fire alarm's are
# read today (the BOQ as per IFC drawings); another system's log borrows
# the building's floors from them and says so.
IFC_FOLDERS = {"FAS": project_folders.IFC_FIRE_ALARM}
READABLE = ("dwg", "dxf")
READ_KIND = "ifc_read"


class FolderError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def folder_for(system: str | None) -> str | None:
    return IFC_FOLDERS.get((system or "").upper())


def _root(project) -> Path | None:
    if not project.source_folder_path:
        return None
    root = Path(project.source_folder_path)
    return root if os.path.isdir(_os_path(root)) else None


def owner_of(drawing: ProjectIfcDrawing) -> str | None:
    """The system whose IFC folder a read drawing is filed in; None for one
    filed nowhere (the project folder was not reachable when it was read)."""
    archived = (drawing.archive_path or "").replace("\\", "/")
    for system, folder in IFC_FOLDERS.items():
        if archived.startswith(folder + "/"):
            return system
    return None


def drawings_for(db: Session, project, system: str) -> tuple[list[ProjectIfcDrawing], str | None]:
    """The IFC drawings in force the log of one system reads its sheets
    from: those filed in the system's own IFC folder, and those filed
    nowhere (only the fire alarm is read, so an unfiled one is its).
    (drawings, borrowed_from): when the system has none of its own, every
    drawing in force stands in and `borrowed_from` names whose they are."""
    in_force = revisions.in_force(db, project.id)
    wanted = (system or "").upper()
    own = [d for d in in_force if owner_of(d) in (wanted, None)]
    if own or not in_force:
        return own, None
    owners = sorted({owner_of(d) or "FAS" for d in in_force})
    return in_force, owners[0]


def _drawing_out(d: ProjectIfcDrawing, in_force: set[int]) -> dict:
    return {"id": d.id, "filename": d.filename, "revision": d.revision or "R0", "reference": d.drawing_reference,
            "in_force": d.id in in_force}


def _job_out(job: BackgroundJob) -> dict:
    progress = job.progress or {}
    return {"id": job.id, "status": job.status, "message": progress.get("message"), "stage": progress.get("stage"),
            "done": progress.get("done")}


def files(db: Session, project, system: str) -> dict:
    """What the system's IFC folder holds, file by file, with the drawing
    each is read as (or the read under way), for the Drawings Log."""
    folder = folder_for(system)
    root = _root(project)
    out = {"system": system, "folder": folder, "reachable": False, "files": [], "readable": list(READABLE)}
    if folder is None or root is None:
        return out
    here = root / folder
    if not os.path.isdir(_os_path(here)):
        return out
    out["reachable"] = True
    in_force = {d.id for d in revisions.in_force(db, project.id)}
    live = revisions.live(db, project.id).all()
    by_path = {(d.archive_path or "").replace("\\", "/"): d for d in live if d.archive_path}
    by_name = {d.filename: d for d in live if d.id in in_force}
    active = {}
    for job in (db.query(BackgroundJob)
                .filter(BackgroundJob.project_id == project.id, BackgroundJob.kind == READ_KIND,
                        BackgroundJob.status.in_(ACTIVE)).order_by(BackgroundJob.id)):
        path = (job.params or {}).get("folder_path")
        if path:
            active[path] = job
    try:
        entries = sorted(os.scandir(_os_path(here)), key=lambda e: e.name.lower())
    except OSError:
        return out
    for entry in entries:
        try:
            if not entry.is_file() or entry.name.startswith(("~$", ".")):
                continue
            stat = entry.stat()
        except OSError:
            continue
        rel = f"{folder}/{entry.name}"
        ext = upload.extension(entry.name)
        drawing = by_path.get(rel) or by_name.get(entry.name)
        job = active.get(rel)
        out["files"].append({
            "path": rel, "name": entry.name, "ext": ext, "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "readable": ext in READABLE,
            "drawing": _drawing_out(drawing, in_force) if drawing is not None else None,
            "job": _job_out(job) if job is not None else None,
        })
    return out


def stage(project, path: str) -> upload.Staged:
    """Copy a file of the project's IFC folder to the upload staging
    folder, as an upload of it would be staged: the worker reads it from
    there and discards the copy. Refuses a path outside the IFC folders, a
    file that is not a DWG or DXF, an empty one, or one past the limit."""
    rel = (path or "").replace("\\", "/").strip("/")
    if ".." in rel.split("/") or not any(rel.startswith(f + "/") for f in IFC_FOLDERS.values()):
        raise FolderError(422, "The file is not in the project's IFC folder.")
    root = _root(project)
    if root is None:
        raise FolderError(409, "The project folder is not reachable on this PC.")
    source = root / rel
    name = Path(rel).name
    ext = upload.extension(name)
    if ext not in READABLE:
        raise FolderError(415, f"{name} is not a DWG or DXF drawing.")
    if not os.path.isfile(_os_path(source)):
        raise FolderError(404, f"{name} is not in the IFC folder any more.")
    size = os.path.getsize(_os_path(source))
    if size == 0:
        raise FolderError(422, f"{name} is empty.")
    if size > upload.MAX_BYTES:
        raise upload.too_large(name)
    folder = upload.staging_dir()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{uuid.uuid4().hex}.{ext}"
    digest = hashlib.sha256()
    try:
        with open(_os_path(source), "rb") as src, open(target, "wb") as out:
            head = src.read(8)
            if ext == "dwg" and not head.startswith(upload.DWG_HEADER):
                raise FolderError(422, f"{name} is not a DWG drawing (it does not start with an AutoCAD DWG header).")
            digest.update(head)
            out.write(head)
            shutil.copyfileobj(src, out, length=upload.CHUNK)
    except BaseException:
        upload.discard(target)
        raise
    with open(target, "rb") as copy:
        copy.seek(8)
        while chunk := copy.read(upload.CHUNK):
            digest.update(chunk)
    return upload.Staged(path=target, name=name, ext=ext, size=size, sha256=digest.hexdigest())
