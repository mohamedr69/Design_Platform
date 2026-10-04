"""The Fire Alarm Interface Schedule, from the other trades' IFC drawings.

Two stages, never mixed:

  1. Discovery (`scan_project`, run by the IFC worker): the IFC drawings of
     each discipline, from the project folder's own IFC tree, are read
     (app.interfaces.scan) for what equipment they show and where. The
     architecture is read from the fire alarm IFC drawings in force --
     their architectural background -- and from 03- Drawings/IFC/Architectural
     when the contractor has filed one there.
  2. The schedule (`build`): each item found on a floor plan is given the
     interface matrix's contacts, signals and action (app.interfaces.matrix),
     one line per item per floor -- a typical plan for eleven floors is
     eleven lines. What the drawings do not settle goes to Verification
     Required, with what is missing, and is scheduled only once an engineer
     says where and how many: an item shown only on a riser or schematic,
     outside every sheet or on a plan whose floor is not identified; a
     system seen only as a note ("THIS ROOM IS PROTECTED BY PRE-ACTION
     SYSTEM"); a door the words do not say is automatic; the lifts.

Nothing is invented: no tag ("Tag Not Identified" where there is none), no
floor, no quantity. The floors are the Building Floor Registry's; a floor a
drawing names that the registry does not have is reported, not merged.
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.ifc import storage
from app.ifc.dxf import sheets as S
from app.interfaces import detect, evidence, geometry, scan, visual
from app.interfaces import schedules as SCH
from app.interfaces.matrix import (ACS, ARCH, BY_KEY, DISCIPLINE_NAMES, FF, GB, HVAC, MATRIX_NAME, RULES, SM,
                                   UNCLEAR_ROWS, modules)
from app.models import Project, ProjectFaInterfaces
from app.services import building_floors, document_control, drawing_log
from app.services.project_folders import DRAWINGS

log = logging.getLogger(__name__)
NO_TAG = "Tag Not Identified"


@dataclass(frozen=True)
class Discipline:
    code: str
    folder: str
    purpose: str


DISCIPLINES: tuple[Discipline, ...] = (
    Discipline(ARCH, f"{DRAWINGS}/IFC/Architectural",
               "Floors, lifts and machine rooms, automatic doors, rolling shutters, gate barriers"),
    Discipline(FF, f"{DRAWINGS}/IFC/Mechanical/FF",
               "Fire pumps, alarm check and zone control valves, FM200 / clean agent, pre-action, deluge, foam"),
    Discipline(SM, f"{DRAWINGS}/IFC/Mechanical/SM",
               "Smoke extract, pressurization, makeup air and jet fans, motorized smoke dampers, curtains"),
    Discipline(HVAC, f"{DRAWINGS}/IFC/Mechanical/HVAC",
               "AHU, FAHU, fresh air fans, motorized smoke/fire dampers"),
    Discipline(ACS, f"{DRAWINGS}/IFC/Electrical/ACS",
               "Access card control panels, entrance doors, gate barriers"),
    Discipline(GB, f"{DRAWINGS}/IFC/Electrical/GB",
               "Gate barriers: open the exit barrier, close the entrance barrier"),
)
BY_CODE = {d.code: d for d in DISCIPLINES}
# Where each discipline's items would normally come from, first: the
# discipline's own drawing wins over the architecture for the same item.
_PRIORITY = {FF: 0, SM: 0, HVAC: 0, ACS: 0, GB: 0, ARCH: 1}

# Systems scheduled per system, not per label: a note or label says a system
# protects an area, not how many panels it has -- the engineer says how many.
SYSTEM_KEYS = {"foam_system", "fm200_system", "clean_agent_system", "deluge_system", "preaction_system", "co2_system",
               "kitchen_hood"}
_DIAGRAM = re.compile(r"RISER|SCHEMATIC|DIAGRAM|SINGLE\s*LINE|FLOW\s*CHART", re.I)
_NOT_READ = re.compile(r"DETAIL|LEGEND|SECTION|ELEVATION|KEY\s*PLAN|WIRING|NOTES", re.I)
_REVISION = re.compile(r"[\s_-]*(\(.*\)|R(?:EV)?\.?\s*(\d+))\s*$", re.I)
_SKIP_FILE = (".dwl", ".dwl2", ".bak", ".tmp", ".sv$")


# --- sources: the drawings of each discipline -------------------------------------------------


def _stem(name: str) -> tuple[str, int]:
    """(the drawing, its revision) from a file name: "FF LAYOUT R2.dwg" is
    ("FF LAYOUT", 2); no revision in the name is -1."""
    base = re.sub(r"\.(dwg|dxf)$", "", name, flags=re.I)
    m = _REVISION.search(base)
    rev = int(m.group(2)) if m and m.group(2) else -1
    return (_REVISION.sub("", base).strip().upper() if m else base.strip().upper()), rev


class SourceUnreachable(Exception):
    """The project folder cannot be reached (or the project has none): a read
    of it would say nothing, so nothing is written."""


class SourcesChanged(Exception):
    """The schedule's evidence changed while it was being read (another read,
    a confirmation, a publication): this one is not written over it."""


def fa_in_force(db: Session, project: Project) -> dict[str, dict]:
    """The fire alarm IFC drawings in force, by the path the schedule files them
    under: their evidence is the drawing register and the DXF on this PC, never
    the project folder."""
    from app.ifc.services import revisions

    out: dict[str, dict] = {}
    for fa in revisions.in_force(db, project.id):
        path = storage.dxf_path(fa)
        exists = path.is_file()
        out[fa.archive_path or fa.filename] = {
            "path": str(path), "dxf_exists": exists, "sha256": fa.source_sha256, "filename": fa.filename,
            "revision": fa.revision or "R0", "fa_drawing_id": fa.id,
            "size": path.stat().st_size if exists else None,
            "mtime": fa.uploaded_at.timestamp() if fa.uploaded_at else None}
    return out


def discover(db: Session, project: Project, listing: "evidence.Listing | None" = None) -> list[dict]:
    """Every drawing the schedule reads, discipline by discipline: the
    files in each IFC folder (a later revision of the same drawing stands
    for it -- the earlier is listed as superseded), and the fire alarm IFC
    drawings in force for their architecture. Stat only (evidence.take)."""
    listing = listing or evidence.take(project, DISCIPLINES)
    out: list[dict] = []
    for d in DISCIPLINES:
        fs = listing.folders.get(d.code)
        if fs is None:
            continue
        latest: dict[str, tuple] = {}
        for item in fs.supported:
            drawing, rev = _stem(item.filename)
            # a DXF beside its DWG is the same drawing: the DWG is the issued file
            rank = (rev, item.mtime, 1 if item.filename.lower().endswith(".dwg") else 0)
            if drawing not in latest or rank > latest[drawing][:3]:
                latest[drawing] = (*rank, item.relative_path)
        for item in sorted(fs.supported, key=lambda i: i.filename.lower()):
            drawing, _rev = _stem(item.filename)
            out.append({"discipline": d.code, "kind": "folder", "path": item.path, "relative_path": item.relative_path,
                        "filename": item.filename, "size": item.size, "mtime": item.mtime,
                        "cloud_only": item.cloud_only, "superseded": latest[drawing][3] != item.relative_path})
    for rel, fa in fa_in_force(db, project).items():
        out.append({"discipline": ARCH, "kind": "fa_ifc", "path": fa["path"], "relative_path": rel,
                    "filename": fa["filename"], "revision": fa["revision"], "fa_drawing_id": fa["fa_drawing_id"],
                    "sha256": fa["sha256"], "size": fa["size"], "mtime": fa["mtime"], "dxf_exists": fa["dxf_exists"],
                    "superseded": False})
    return out


def _relative(root: Path, full: Path) -> str:
    try:
        return full.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return full.name


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(document_control._os_path(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_folder(project: Project) -> Path:
    """<uploads>/EP-<number>/interfaces: each DWG's DXF, by its hash."""
    return storage.uploads_root() / f"EP-{project.ep_number}" / "interfaces"


def state(db: Session, project: Project) -> ProjectFaInterfaces:
    row = db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == project.id).one_or_none()
    if row is None:
        row = ProjectFaInterfaces(project_id=project.id, sources=[], decisions={}, manual=[])
        db.add(row)
        db.flush()
    return row


_READING = ("result", "visual", "read_at", "converted_in")
_STATE = ("retired_by", "stale_reason", "last_known", "error", "removed_at", "confirmed_by_id")


def _pub(src: dict) -> dict:
    return {k: v for k, v in src.items() if k not in ("path", "dxf_exists")}


def _bare(entry: dict) -> dict:
    """An entry without its reading or its state: what the file is."""
    return {k: v for k, v in entry.items() if k not in _READING + _STATE + ("status",)}


def _last_known(old: dict | None) -> dict | None:
    """The last good reading an entry carries: its own when it is read, else the
    one it kept when it stopped being current."""
    if not old:
        return None
    if old.get("status") == "read" and old.get("result") is not None:
        return {"result": old.get("result"), "visual": old.get("visual"), "sha256": old.get("sha256"),
                "read_at": old.get("read_at"),
                "scan_version": (old.get("result") or {}).get("scan_version")
                or (old.get("result") or {}).get("schedule_version")}
    return old.get("last_known")


def _not_current(pub: dict, old: dict | None, reason: str, error: str | None = None, *, never_read: str) -> dict:
    """S4.2: a file that has a last good reading becomes stale (kept, not counted);
    one that never had one is `never_read` (failed / unread)."""
    known = _last_known(old)
    if known is not None:
        out = {**_bare(pub), "status": "stale", "stale_reason": reason, "last_known": known}
    else:
        out = {**_bare(pub), "status": never_read}
        if reason == "not_synced":
            out["stale_reason"] = "not_synced"
    if error:
        out["error"] = error[:500]
    return out


def _gone_reason(old: dict, listing: "evidence.Listing", folder_of: dict[str, "evidence.FolderState"]) -> str:
    """Why a previously listed file is not listed now (S4.1 precedence, C1)."""
    if listing.root == "ifc_root_missing":
        return "ifc_root_missing"
    fs = folder_of.get(old.get("discipline"))
    if fs is None or fs.state == "absent_or_empty":
        return "folder_missing"
    if fs.failed_for(old.get("relative_path") or ""):
        return "listing_failed"
    return "missing"


def _read_folder_file(db, project, src: dict, old: dict | None, *, open_cloud: bool, check, converter_box: list) -> dict:
    """One listed drawing (S4.2 E1/E2/E3): carried forward unchanged without
    opening it (C6), or hashed (a cloud-only file is downloaded by that) and read."""
    from app.ifc.dxf import convert

    pub = _pub(src)
    if (old and old.get("status") == "read" and old.get("size") == src.get("size") and old.get("mtime") == src.get("mtime")
            and (old.get("result") or {}).get("scan_version") == scan.SCAN_VERSION):
        return {**old, **pub}
    if src.get("cloud_only") and not open_cloud:
        return _not_current(pub, old, "not_synced", never_read="unread")
    path = Path(src["path"])
    try:
        sha = _sha256(path)
    except OSError as exc:
        if src.get("cloud_only"):
            return _not_current(pub, old, "not_synced", f"OneDrive could not bring the file down: {exc}", never_read="unread")
        return _not_current(pub, old, "read_failed", f"The file could not be opened: {exc}", never_read="failed")
    if (old and old.get("status") == "read" and old.get("sha256") == sha
            and (old.get("result") or {}).get("scan_version") == scan.SCAN_VERSION):
        return {**old, **pub, "sha256": sha}          # touched, not changed
    entry = {**_bare(pub), "sha256": sha}
    try:
        dxf = path
        if path.suffix.lower() == ".dwg":
            dxf = cache_folder(project) / f"{sha[:24]}.dxf"
            if not dxf.is_file():
                converter_box[0] = converter_box[0] or convert.find_converter()
                if converter_box[0] is None:
                    raise RuntimeError("No DWG converter on the PC the IFC worker runs on: install AutoCAD or the "
                                       "free ODA File Converter, or file the drawing as DXF too.")
                dxf.parent.mkdir(parents=True, exist_ok=True)
                started = datetime.now()
                convert.convert_dwg_to_dxf(path, dxf, converter_box[0])
                entry["converted_in"] = round((datetime.now() - started).total_seconds(), 1)
        result = scan.read(str(dxf), src["discipline"], check=check)
        return {**entry, "status": "read", "result": result, "read_at": utc_now().isoformat()}
    except Exception as exc:  # noqa: BLE001 -- one drawing that cannot be read is named; the rest are read
        from app.services import jobs

        if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)):
            raise
        return _not_current(entry, old, "read_failed", str(exc) or type(exc).__name__, never_read="failed")


def _read_fa_ifc(src: dict, old: dict | None, *, check) -> dict:
    """A fire alarm IFC drawing in force (S4.2 F1-F3)."""
    pub = _pub(src)
    if not src.get("dxf_exists"):
        return _not_current(pub, old, "read_failed",
                            "The drawing's DXF is not on this PC: import the fire alarm IFC drawing again.",
                            never_read="failed")
    if (old and old.get("status") == "read" and old.get("sha256") == src.get("sha256")
            and (old.get("result") or {}).get("scan_version") == scan.SCAN_VERSION):
        return {**old, **pub}
    try:
        result = scan.read(str(src["path"]), src["discipline"], check=check)
        return {**_bare(pub), "status": "read", "result": result, "read_at": utc_now().isoformat()}
    except Exception as exc:  # noqa: BLE001
        from app.services import jobs

        if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)):
            raise
        return _not_current(pub, old, "read_failed", str(exc) or type(exc).__name__, never_read="failed")


def scan_project(db: Session, project: Project, user_id: int | None = None, progress=None, check=None,
                 hydrate: bool | None = None, job_id: int | None = None, look: bool = True,
                 advance: bool = True) -> dict:
    """Read the project's drawings into the schedule's evidence (FI-P1 r3 Stage 0.1).

    The folder is listed first (stat only). An unreachable folder fails the job
    with nothing written. A file read before and unchanged (same size and time)
    is carried forward without opening it. Every other file is read, and every
    entry moves by the transition table of CORRECTION-R3 S4 with conditions
    C1/C3/C6. A missing file is not "removed" unless the engineer confirms it or
    a newer revision of it is read. The whole result is written in one commit,
    only if no one else wrote the evidence meanwhile. The published schedule
    moves to this reading only when every rule of S7/C2 holds."""
    row = state(db, project)
    # A first read makes the project's row: committed now, not held open through
    # minutes of reading while the job's progress is written beside it.
    db.commit()
    seen = row.generation or 0
    listing = evidence.take(project, DISCIPLINES)
    if listing.root in ("not_configured", "unreachable"):
        raise SourceUnreachable("The project folder cannot be reached from the IFC worker"
                                if listing.root == "unreachable" else "This project has no folder")
    settings = get_settings()
    open_cloud = settings.fa_read_cloud_only_files if hydrate is None else bool(hydrate)
    before = {(e.get("discipline"), e.get("relative_path")): e for e in row.sources or []}
    found = discover(db, project, listing)
    todo = [s for s in found if not s["superseded"]]
    done: dict[tuple, dict] = {}
    converter_box: list = [None]
    for src in found:
        if check:
            check()
        key = (src["discipline"], src["relative_path"])
        old = before.get(key)
        if src["superseded"]:
            done[key] = {**_bare(_pub(src)), "status": "superseded", "last_known": _last_known(old)}
            continue
        n = todo.index(src) + 1
        if progress:
            progress(n - 1, len(todo), f"Reading {src['filename']} ({DISCIPLINE_NAMES[src['discipline']]})", src["filename"])
        if src["kind"] == "fa_ifc":
            done[key] = _read_fa_ifc(src, old, check=check)
        else:
            done[key] = _read_folder_file(db, project, src, old, open_cloud=open_cloud, check=check,
                                          converter_box=converter_box)
    # C3: an older revision is retired only by a newer one that was read
    read_stems: dict[tuple, tuple[str, int]] = {}
    for e in done.values():
        if e.get("status") == "read" and e.get("kind") == "folder":
            stem, rev = _stem(e["filename"])
            if (e["discipline"], stem) not in read_stems or rev > read_stems[(e["discipline"], stem)][1]:
                read_stems[(e["discipline"], stem)] = (e["relative_path"], rev)

    def successor(entry: dict) -> str | None:
        """A read revision of the same drawing newer than this one (C1/C3)."""
        stem, rev = _stem(entry.get("filename") or "")
        found = read_stems.get((entry.get("discipline"), stem))
        return found[0] if found and found[1] > rev else None

    for e in done.values():
        if e.get("status") == "superseded":
            e["retired_by"] = successor(e)
    # files the pipeline cannot read: listed, never counted
    for code, fs in listing.folders.items():
        for item in fs.unsupported:
            done[(code, item.relative_path)] = {
                "discipline": code, "kind": "unsupported", "relative_path": item.relative_path,
                "filename": item.filename, "size": item.size, "mtime": item.mtime, "cloud_only": item.cloud_only,
                "status": "unsupported"}
    done.update(_read_schedules(project, listing, before))
    # entries not listed now (S4.2 E4-E6, EL; F4/F5; C1)
    now = utc_now().isoformat()
    in_force = {e["relative_path"] for e in done.values() if e.get("kind") == "fa_ifc"}
    for key, old in before.items():
        if key in done:
            continue
        kind = old.get("kind")
        if old.get("status") == "removed":
            done[key] = old
        elif kind == "fa_ifc":
            replaced = bool(in_force)
            done[key] = {**_bare(old), "status": "superseded" if replaced else "removed",
                         "retired_by": "a newer fire alarm IFC drawing is in force" if replaced else None,
                         "last_known": _last_known(old), "removed_at": None if replaced else now}
        elif kind == "unsupported":
            # gone from a folder that is there: removed; a folder not seen: still listed, not present
            if _gone_reason(old, listing, listing.folders) == "missing":
                done[key] = {**_bare(old), "status": "removed", "removed_at": now}
            else:
                done[key] = {**_bare(old), "status": "unsupported", "present": False}
        elif kind == "schedule":
            continue                                    # decided in _read_schedules
        else:
            reason = _gone_reason(old, listing, listing.folders)
            newer = successor(old)
            if reason == "missing" and newer:
                done[key] = {**_bare(old), "status": "removed", "retired_by": newer,
                             "last_known": _last_known(old), "removed_at": now}
            else:
                done[key] = _not_current(old, old, reason, never_read="stale")
                if done[key]["status"] == "stale" and "stale_reason" not in done[key]:
                    done[key]["stale_reason"] = reason
    sources = list(done.values())
    read_now = [e for e in sources if e.get("status") == "read"]
    # S5: the same bytes at two paths -- said, not changed: each path is still read and counted as today
    order = {d.code: i for i, d in enumerate(DISCIPLINES)}
    first_of: dict[str, str] = {}
    for e in sorted(read_now, key=lambda e: (order.get(e.get("discipline"), 99), e.get("relative_path") or "")):
        e.pop("duplicate_of", None)
        if e.get("sha256"):
            if e["sha256"] in first_of:
                e["duplicate_of"] = first_of[e["sha256"]]
            else:
                first_of[e["sha256"]] = e["relative_path"]
    if look and any(visual.wanted(s) for s in read_now):
        try:
            visual.check(db, project, read_now, check=check,
                         progress=(lambda d, t, m, f=None: progress(d, t, m, f)) if progress else None)
        except Exception as exc:  # noqa: BLE001 -- the reading stands; the dampers stay held, said so
            from app.services import jobs

            if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)):
                raise
            log.warning("The dampers could not be looked at on the drawings: %s", exc)
    # the legacy read publishes by the S7 rules; the drawing workflow publishes only on the
    # engineer's acceptance of a reviewed run (fa_interfaces_run)
    publish = _advance(row.published, sources, listing, fa_in_force(db, project), job_id) if advance else None
    stamp = utc_now()
    values = {"sources": sources, "scanned_at": stamp, "scanned_by_id": user_id, "generation": seen + 1}
    if publish is not None:
        values.update(published=publish, published_at=stamp, published_basis="complete_scan",
                      published_by_id=user_id, published_reason=None)
    changed = (db.query(ProjectFaInterfaces)
               .filter(ProjectFaInterfaces.id == row.id, ProjectFaInterfaces.generation == seen)
               .update(values, synchronize_session=False))
    if changed != 1:
        db.rollback()
        raise SourcesChanged("The schedule's drawings changed while they were being read (another read, a "
                             "confirmation or a publication): read the drawings again")
    db.commit()
    db.expire(row)
    if progress:
        progress(len(todo), len(todo), "Read", None)
    return {"drawings": len(todo), "read": len(read_now), "published": publish is not None,
            "failed": [{"filename": s["filename"], "error": s.get("error")} for s in sources
                       if s.get("status") == "failed" or (s.get("status") == "stale" and s.get("error"))]}


def _advance(published: dict | None, sources: list[dict], listing: "evidence.Listing", fa_now: dict,
             job_id: int | None) -> dict | None:
    """S7 auto-advance with C1/C2: the published schedule moves to this reading
    only when the folder was fully listed, every drawing present now is read,
    every drawing of the published schedule is read now or retired for good,
    and the reading is not empty."""
    if listing.root != "ok":
        return None                                                           # A1
    folders = list(listing.folders.values()) + ([listing.mechanical] if listing.mechanical else [])
    if any(fs.state == "listing_failed" or fs.failed_dirs for fs in folders):
        return None                                                           # A2
    if evidence.not_current_present(sources, listing, fa_now):
        return None                                                           # A3
    read_now = [e for e in sources if e.get("status") == "read"]
    if not read_now:
        return None                                                           # C2: never publish an empty reading
    by_key = {(e.get("kind"), e.get("discipline"), e.get("relative_path")): e for e in sources}
    files = listing.files()
    for s in (published or {}).get("sources") or []:                          # A4
        now = by_key.get((s.get("kind"), s.get("discipline"), s.get("relative_path")))
        # read now and current (its content may have changed and been read again), or retired for good
        if now is not None and evidence.current_now(now, listing, fa_now, files):
            continue
        if not evidence.retired(now):
            return None
    return evidence.snapshot(sources, job_id)


def publish_current(db: Session, project: Project, user_id: int, *, reason: str, expected_sources_digest: str,
                    override: bool = False) -> dict:
    """S7 / C5: the engineer publishes what is read and current now -- the way
    out when a drawing keeps failing, or a project's only evidence is its fire
    alarm IFC drawing. Refuses an empty set, or one with drawings still in
    the cloud, unless overridden with a reason."""
    row = state(db, project)
    seen = row.generation or 0
    listing = evidence.take(project, DISCIPLINES)
    if listing.root not in ("ok", "ifc_root_missing"):
        raise ValueError("The project folder cannot be reached: nothing current to publish")
    if not (reason or "").strip():
        raise ValueError("Say why the current reading is published")
    folders = list(listing.folders.values()) + ([listing.mechanical] if listing.mechanical else [])
    if any(fs.state == "listing_failed" or fs.failed_dirs for fs in folders):
        raise ValueError("Part of the drawings folder could not be listed: read the drawings again first")
    fa_now = fa_in_force(db, project)
    files = listing.files() if listing.root == "ok" else {}
    current = [e for e in row.sources or [] if evidence.current_now(e, listing, fa_now, files)]
    if evidence.digest(current) != expected_sources_digest:
        raise SourcesChanged("The drawings changed since the page was shown: look again before publishing")
    if not current and not override:
        raise ValueError("Nothing is read and current: an empty schedule is published only on purpose (override)")
    cloud = [e for e in row.sources or [] if e.get("stale_reason") == "not_synced" and e.get("status") in ("stale", "unread")]
    if cloud and not override:
        raise ValueError(f"{len(cloud)} drawing(s) are still in the cloud (not synced): read them first, or override")
    stamp = utc_now()
    changed = (db.query(ProjectFaInterfaces)
               .filter(ProjectFaInterfaces.id == row.id, ProjectFaInterfaces.generation == seen)
               .update({"published": evidence.snapshot(current), "published_at": stamp,
                        "published_basis": "engineer_accepted", "published_by_id": user_id,
                        "published_reason": reason.strip()[:1000], "generation": seen + 1},
                       synchronize_session=False))
    if changed != 1:
        db.rollback()
        raise SourcesChanged("The schedule's drawings changed meanwhile: look again before publishing")
    db.commit()
    db.expire(row)
    return {"published_sources": len(current)}


def confirm_removed(db: Session, project: Project, user_id: int, relative_paths: list[str]) -> int:
    """C5: the engineer says files missing from a present folder (or a folder
    gone) were removed on purpose. Sync states cannot be confirmed away."""
    row = state(db, project)
    seen = row.generation or 0
    wanted = set(relative_paths)
    stamp = utc_now().isoformat()
    sources, n = [], 0
    for e in row.sources or []:
        if (e.get("relative_path") in wanted and e.get("status") == "stale"
                and e.get("stale_reason") in ("missing", "folder_missing")):
            e = {**e, "status": "removed", "removed_at": stamp, "confirmed_by_id": user_id}
            n += 1
        sources.append(e)
    if not n:
        return 0
    changed = (db.query(ProjectFaInterfaces)
               .filter(ProjectFaInterfaces.id == row.id, ProjectFaInterfaces.generation == seen)
               .update({"sources": sources, "generation": seen + 1}, synchronize_session=False))
    if changed != 1:
        db.rollback()
        raise SourcesChanged("The schedule's drawings changed meanwhile: look again")
    db.commit()
    db.expire(row)
    return n


SCHEDULE = "SCHED"


def _read_schedules(project: Project, listing: "evidence.Listing", before: dict) -> dict[tuple, dict]:
    """The mechanical equipment schedules (Excel) in the project's mechanical
    IFC folders: read again unless unchanged, hashed so the published
    reading's identity changes with them (C8). A workbook not listed now
    moves by the folder rules (S4.2), never silently out."""
    out: dict[tuple, dict] = {}
    if listing.root == "ok" and listing.mechanical is not None:
        for item in listing.mechanical.workbooks:
            key = (SCHEDULE, item.relative_path)
            old = before.get(key)
            pub = {"discipline": SCHEDULE, "kind": "schedule", "relative_path": item.relative_path,
                   "filename": item.filename, "size": item.size, "mtime": item.mtime, "cloud_only": item.cloud_only,
                   "superseded": False}
            if (old and old.get("status") == "read" and old.get("size") == item.size and old.get("mtime") == item.mtime
                    and (old.get("result") or {}).get("schedule_version") == SCH.SCHEDULE_VERSION and old.get("sha256")):
                out[key] = {**old, **pub}
                continue
            if item.cloud_only and not get_settings().fa_read_cloud_only_files:
                out[key] = _not_current(pub, old, "not_synced", never_read="unread")
                continue
            path = Path(item.path)
            try:
                sha = _sha256(path)
                out[key] = {**pub, "sha256": sha, "status": "read", "result": SCH.read(path),
                            "read_at": utc_now().isoformat()}
            except Exception as exc:  # noqa: BLE001 -- a workbook that cannot be opened is named, the rest read
                reason = "not_synced" if item.cloud_only and isinstance(exc, OSError) else "read_failed"
                out[key] = _not_current(pub, old, reason, f"The workbook could not be read: {exc}",
                                        never_read="unread" if reason == "not_synced" else "failed")
    for key, old in before.items():
        if old.get("kind") != "schedule" or key in out:
            continue
        if old.get("status") == "removed":
            out[key] = old
            continue
        if listing.root == "ifc_root_missing":
            reason = "ifc_root_missing"
        elif listing.mechanical is None or listing.mechanical.state == "absent_or_empty":
            reason = "folder_missing"
        elif listing.mechanical.failed_for(old.get("relative_path") or ""):
            reason = "listing_failed"
        else:
            reason = "missing"
        entry = _not_current(old, old, reason, never_read="stale")
        entry.setdefault("stale_reason", reason)
        out[key] = entry
    return out


class Schedule:
    """The equipment schedules' tags, to check the plans' tags against: by
    tag, and by tag on a floor ("SEF-1" on the 3rd basement plan is the
    schedule's "B3-SEF-1")."""

    def __init__(self, sources: list[dict], floors: "Floors"):
        self.entries: list[dict] = []
        for src in sources:
            for it in (src.get("result") or {}).get("items", []):
                at = floors.of_title(it["location"]) if it.get("location") else []
                for tag in it["tags"]:
                    prefix, base = SCH.base_tag(tag)
                    own = sorted(drawing_log.floors_named(prefix)) if prefix else []
                    self.entries.append({
                        "key": it["key"], "tag": tag, "identity": SCH.tag_identity(tag),
                        "base": SCH.tag_identity(base), "prefix_floor": own[0] if len(own) == 1 else None,
                        "floors": own or at, "location": it.get("location") or "",
                        "where": f"{src['filename']} · {it['sheet']} row {it['row']}",
                        "row_id": f"{src['relative_path']}|{it['sheet']}|{it['row']}", "source": src["filename"]})
        self.by_identity = {e["identity"]: e for e in self.entries}
        self.by_floor = {(e["base"], e["prefix_floor"]): e for e in self.entries if e["prefix_floor"]}
        self.keys = {e["key"] for e in self.entries}
        self.matched: set[str] = set()
        self.plan_bases: set[str] = set()     # the plans' own tags, as written

    def resolve(self, tag: str, keys: list[str]) -> dict | None:
        ident = SCH.tag_identity(tag)
        if ident in self.by_identity:
            return self.by_identity[ident]
        if len(keys) == 1:
            return self.by_floor.get((ident, keys[0]))
        return None


def _public(src: dict) -> dict:
    return {k: v for k, v in src.items() if k != "path"}


# --- floors ---------------------------------------------------------------------------------------


class Floors:
    """The building's floors, the Building Floor Registry's: a key per
    physical floor, its name and its place in the building."""

    def __init__(self, db: Session, project: Project):
        self.registry = {r.floor_key: r for r in building_floors.registry(db, project.id)}
        self.aliases = building_floors.project_aliases(db, project)
        self.unregistered: dict[str, list[str]] = {}

    def of_title(self, title: str) -> list[str]:
        """The floor keys a sheet title names, in building order ([] when none)."""
        name = S.identify_floor(title or "")
        if not name:
            return []
        return sorted(drawing_log.floor_identity(name, title, self.aliases), key=self.order)

    def name(self, key: str) -> str:
        r = self.registry.get(key)
        return r.display_name if r is not None else building_floors.alias_label(key)

    def order(self, key: str) -> tuple:
        r = self.registry.get(key)
        if r is not None:
            return (0, r.sort_order, key)
        elevation = drawing_log._elevation(key)
        return (1, elevation if elevation is not None else 1e9, key)

    def note(self, key: str, where: str) -> None:
        """A floor a drawing's plan names: one the registry does not have is
        reported (and still offered, so an item can be placed on it)."""
        if key not in self.registry:
            self.unregistered.setdefault(key, [])
            if where not in self.unregistered[key]:
                self.unregistered[key].append(where)

    def listed(self) -> list[dict]:
        """The floors an item may be placed on: the registry's, then any
        other a drawing names."""
        out = [{"key": k, "name": r.display_name, "order": r.sort_order, "ifc_sheet": r.ifc_sheet, "registered": True}
               for k, r in sorted(self.registry.items(), key=lambda kv: kv[1].sort_order)]
        out += [{"key": k, "name": self.name(k), "order": None, "ifc_sheet": "; ".join(w[:1]), "registered": False}
                for k, w in sorted(self.unregistered.items(), key=lambda kv: self.order(kv[0]))]
        return out


# --- stage 2: the schedule ------------------------------------------------------------------------


def _radius(sheet: dict | None, units: str, notes: bool = False) -> float:
    """How near two labels of the same thing are to be one. A note repeated
    in a room: 3% of the sheet's view (a floor plan 80 m across: 2.4 m). An
    equipment label: 1% -- two doors side by side in a lobby stay two."""
    share = 0.03 if notes else 0.01
    if sheet and sheet.get("height"):
        return share * float(sheet["height"])
    return {"mm": 2000.0, "cm": 200.0, "in": 80.0, "ft": 6.5}.get(units, 2.0) * share / 0.03


def _clusters(items: list[dict], radius: float) -> list[list[dict]]:
    """Labels within `radius` of one another, as one: a note written three
    times in one room is one room."""
    groups: list[list[dict]] = []
    for it in items:
        for g in groups:
            if any(math.hypot(it["x"] - o["x"], it["y"] - o["y"]) <= radius for o in g):
                g.append(it)
                break
        else:
            groups.append([it])
    return groups


def _sheet_kind(sheet: dict | None) -> str:
    """plan | diagram | detail (not read) | outside."""
    if sheet is None:
        return "outside"
    title = sheet.get("title") or ""
    if sheet.get("kind") == "diagram" or _DIAGRAM.search(title):
        return "detail" if _NOT_READ.search(title) and not _DIAGRAM.search(title) else "diagram"
    return "plan"


def _source_label(src: dict) -> str:
    if src.get("kind") == "fa_ifc":
        return f"{src['filename']} {src.get('revision', '')} (fire alarm IFC, architectural background)".replace("  ", " ")
    return src["filename"]


def _row(rule_key: str, *, floor: str, floors: Floors, tag: str | None, location: str, description: str,
         discipline: str, source: str, drawing_ref: str, confidence: str, basis: str, row_id: str,
         evidence: str = "", typical: bool = False) -> dict:
    r = BY_KEY[rule_key]
    mods = modules(r.contacts)
    return {"id": row_id, "floor_key": floor, "floor": floors.name(floor), "location": location or "",
            "tag": tag or NO_TAG, "key": r.key, "equipment": r.name, "description": description,
            "discipline": discipline, "system": DISCIPLINE_NAMES.get(discipline, discipline), "contacts": r.contacts,
            "monitoring": r.monitoring, "control": r.control, "alarm": r.alarm, "supervisory": r.supervisory,
            "action": r.action, "modules": mods, "module_qty": sum(mods.values()), "source": source,
            "drawing_ref": drawing_ref, "confidence": confidence, "basis": basis, "evidence": evidence,
            "typical": typical, "status": "scheduled"}


def build(db: Session, project: Project) -> dict:
    """The schedule, its summaries and what is left to verify, from the
    drawings read and the engineer's answers -- the **primary** view (S8):
    built from the readings current now, or, when the evidence behind the
    published schedule is not verified now, from the published readings,
    said so. Decisions and manual items always apply live to either view.
    Stale readings are listed apart and never counted."""
    row = state(db, project)
    floors = Floors(db, project)
    listing = evidence.take(project, DISCIPLINES)
    fa_now = fa_in_force(db, project)
    sources = row.sources or []
    view = evidence.choose(sources, row.published, listing, fa_now)
    current = _assemble(row, view.current, floors)
    if view.primary == "published":
        primary = _assemble(row, (row.published or {}).get("sources") or [], Floors(db, project))
    elif view.primary == "none":
        primary = _assemble(row, [], Floors(db, project), manual=False)
    else:
        primary = current
    files = listing.files() if listing.root == "ok" else {}
    current_keys = {(e.get("discipline"), e.get("relative_path")) for e in view.current}
    out = {
        "project": {"id": project.id, "ep_number": project.ep_number, "name": project.project_name},
        "scanned_at": row.scanned_at.isoformat() if row.scanned_at else None,
        "coverage": coverage(row, listing, fa_now, view, current_keys),
        **primary,
        "view_state": view.view_state, "primary": view.primary, "view_reasons": view.reasons,
        "publish_offered": view.publish_offered,
        "totals_known": view.primary != "none",
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "published_basis": row.published_basis,
        "published_by": _user_name(db, row.published_by_id),
        "published_reason": row.published_reason,
        "current_sources_digest": evidence.digest(view.current),
        "current_summary": ({"totals": current["totals"], "rows": len(current["rows"])}
                            if listing.root == "ok" else None),
        "last_known": _last_known_list(sources, current_keys, listing.root),
        "decisions_not_applied": _decisions_not_applied(row, sources, current_keys),
        "evidence": _evidence_counts(sources, listing, current_keys, files),
    }
    out["limitations"] = limitations(out)
    return out


def limitations(view: dict) -> list[dict]:
    """What the evidence cannot show, package by package -- said, never taken
    as "no equipment": files of a kind not read (PDF), and labels not settled
    on one drawn block symbol (a symbol drawn as loose lines is not
    recognised). Neither blocks publication; neither is counted or ruled out."""
    out = []
    for c in view["coverage"]:
        code = c["discipline"]
        unsupported = [f for f in c["files"] if f["status"] == "unsupported" and f.get("present", True)]
        if unsupported:
            out.append({"package": code, "kind": "unsupported_files", "count": len(unsupported),
                        "files": [f["filename"] for f in unsupported][:20],
                        "text": f"{c['name']}: {len(unsupported)} file(s) of a kind not read (PDF) -- what is shown "
                                "only on them is neither counted nor ruled out"})
        no_symbol = [g for g in view["verification"] if g.get("discipline") == code and "|no_symbol|" in g["id"]]
        if no_symbol:
            labels = sum(int(g.get("labels") or 0) for g in no_symbol)
            out.append({"package": code, "kind": "no_block_symbol", "count": labels, "files": [],
                        "text": f"{c['name']}: {labels} label(s) not settled on one drawn block symbol (none near "
                                "them, or two about as near; a symbol drawn as loose lines is not recognised) -- held "
                                "for the engineer, neither counted nor ruled out"})
    return out


def _user_name(db: Session, user_id: int | None) -> str | None:
    if not user_id:
        return None
    from app.models import User

    user = db.get(User, user_id)
    return (user.full_name or user.email) if user else None


def _last_known_list(sources: list[dict], current_keys: set, root: str = "ok") -> list[dict]:
    """The readings kept for audit that do not count now (S8.3)."""
    out = []
    for e in sources:
        if (e.get("discipline"), e.get("relative_path")) in current_keys or e.get("kind") == "unsupported":
            continue
        if e.get("status") == "read":
            # read at the last scan, not verifiable now: the folder unseen, or the file changed since
            reason = "changed_since_read" if root == "ok" or e.get("kind") == "fa_ifc" else root
            known = {"result": e.get("result"), "read_at": e.get("read_at")}
        elif e.get("status") == "stale" and e.get("last_known"):
            known, reason = e["last_known"], e.get("stale_reason")
        else:
            continue
        counts: dict[str, int] = {}
        for it in (known.get("result") or {}).get("items", []):
            counts[it["key"]] = counts.get(it["key"], 0) + 1
        out.append({"package": e.get("discipline"), "relative_path": e.get("relative_path"), "filename": e.get("filename"),
                    "reason": reason, "last_known_at": known.get("read_at"), "counts_by_key": counts})
    return out


def _decisions_not_applied(row: ProjectFaInterfaces, sources: list[dict], current_keys: set) -> dict[str, int]:
    """Engineer decisions kept on readings that do not count now, per package."""
    not_current = {(e.get("discipline"), e.get("relative_path")) for e in sources
                   if (e.get("discipline"), e.get("relative_path")) not in current_keys and e.get("kind") != "unsupported"}
    out: dict[str, int] = {}
    for decision_id in (row.decisions or {}):
        parts = decision_id.split("|")
        if len(parts) >= 2 and (parts[0], parts[1]) in not_current:
            out[parts[0]] = out.get(parts[0], 0) + 1
    return out


def _evidence_counts(sources: list[dict], listing: "evidence.Listing", current_keys: set, files: dict) -> dict:
    counts = {"root": listing.root, "read_current": len(current_keys), "stale": 0, "failed": 0, "unread": 0,
              "removed": 0, "superseded": 0, "unsupported": 0, "cloud_only": 0, "changed_since_read": 0,
              "listing_failed": sorted({d for fs in listing.folders.values() for d in fs.failed_dirs}
                                       | {fs.folder for fs in listing.folders.values() if fs.state == "listing_failed"})}
    for e in sources:
        status = e.get("status")
        if status == "read" and (e.get("discipline"), e.get("relative_path")) not in current_keys:
            counts["changed_since_read"] += 1
        elif status in counts and status != "read":
            counts[status] += 1
        if e.get("cloud_only"):
            counts["cloud_only"] += 1
    return counts


def _assemble(row: ProjectFaInterfaces, readings: list[dict], floors: "Floors", *, manual: bool = True) -> dict:
    """The schedule from a set of readings and the engineer's live answers."""
    groups: list[dict] = []
    conflicts: list[str] = []
    excluded_found: list[dict] = []
    equipment: list[dict] = []
    tags_on_plans: dict[str, dict] = {}
    # The discipline's own drawing first: it stands over the architecture for the same item.
    read = [s for s in readings if s.get("status") == "read"]
    sched = Schedule([s for s in read if s["discipline"] == SCHEDULE], floors)
    sources = sorted((s for s in read if s["discipline"] != SCHEDULE), key=lambda s: _PRIORITY.get(s["discipline"], 9))
    for src in sources:
        _read_source(src, floors, equipment, groups, conflicts, excluded_found, tags_on_plans, sched)

    conflicts.extend(_repeated_tags(tags_on_plans))
    decisions: dict = row.decisions or {}
    held_conflicts: list[dict] = []
    rows = _equipment_rows(equipment, floors, conflicts, sched, held_conflicts)
    gate_rows, gate_groups = _gate_rows([e for e in equipment if e.get("gate")], floors, conflicts, decisions)
    rows.extend(gate_rows)
    groups.extend(gate_groups)
    groups.extend(_conflict_groups(held_conflicts, floors))
    groups.extend(_schedule_checks(rows, sched, floors, conflicts))
    for r in rows:
        d = decisions.get(r["id"]) or {}
        if d.get("status") == "rejected":
            r["status"], r["reason"] = "rejected", d.get("reason", "")
        elif d.get("status") == "confirmed":
            r["confidence"] = "Engineer verified"
        elif r.get("visual_reject"):
            r["status"] = "rejected"
            r["reason"] = f"Not a damper on the drawing (AI visual check): {r['visual_reject']}"
    for g in groups:
        d = decisions.get(g["id"])
        if d and not g.get("decision_not_applied"):
            g["status"] = d.get("status", "open")
            g["decision"] = {k: v for k, v in d.items() if k not in ("status", "history")}
        if d and d.get("history"):
            g["history"] = d["history"][-20:]
        if g["status"] == "resolved":
            rows.extend(_resolved_rows(g, d, floors))
    if manual:
        for m in row.manual or []:
            rows.extend(_manual_rows(m, floors))

    for k, where in floors.unregistered.items() if floors.registry else ():
        conflicts.append(f"The floor \"{floors.name(k)}\" ({'; '.join(where[:2])}) is not in the Building Floor Registry: "
                         "check whether it is another name for a floor of the building (Drawings > Floors).")

    rows = _once(rows, conflicts)
    rows.sort(key=lambda r: (floors.order(r["floor_key"]), BY_KEY[r["key"]].no, r["tag"] == NO_TAG, r["tag"], r["id"]))
    scheduled = [r for r in rows if r["status"] == "scheduled"]
    for i, r in enumerate(scheduled, 1):
        r["no"] = i
    open_groups = [g for g in groups if g["status"] == "open"]
    return {
        "floors": floors.listed(),
        "rows": scheduled,
        "rejected": [r for r in rows if r["status"] == "rejected"],
        "verification": open_groups,
        "settled": [g for g in groups if g["status"] != "open"],
        "manual": row.manual or [],
        "floor_summary": floor_summary(scheduled, floors),
        "type_summary": type_summary(scheduled),
        "totals": totals(scheduled, len(open_groups)),
        "conflicts": conflicts,
        "excluded_found": excluded_found,
        "matrix": {"name": MATRIX_NAME, "rules": [r.to_dict() for r in RULES], "unclear_rows": list(UNCLEAR_ROWS)},
    }


def _read_source(src: dict, floors: Floors, equipment: list, groups: list, conflicts: list, excluded_found: list,
                 tags_on_plans: dict, sched: Schedule) -> None:
    """One drawing's items, sorted: on a floor plan (equipment), a question
    (Verification Required), or evidence for what a plan shows."""
    result = src.get("result") or {}
    units = result.get("units", "unitless")
    sheets = {s["name"]: s for s in result.get("sheets", [])}
    label = _source_label(src)
    by_sheet: dict[tuple[str, str], list[dict]] = {}
    for it in result.get("items", []):
        by_sheet.setdefault((it["sheet"], it["key"]), []).append(it)
    on_plans: set[str] = set()                               # what this drawing's plans show
    off_plan: dict[str, list[tuple[dict, str]]] = {}
    placed: dict[str, int] = {}                              # items placed, floor by floor
    for (sheet_name, key), items in by_sheet.items():
        rule = BY_KEY[key]
        sheet = sheets.get(sheet_name)
        whole = sheet_name == scan.WHOLE
        kind = "plan" if whole else _sheet_kind(sheet)
        title = src["filename"] if whole else (sheet or {}).get("title", "")
        if kind == "detail":
            continue
        if rule.excluded:
            excluded_found.append({"equipment": rule.name, "source": label, "sheet": sheet_name, "count": len(items),
                                   "text": items[0]["text"]})
            continue
        keys = floors.of_title(title) if kind == "plan" else []
        if not keys:
            why = ("outside every sheet" if kind == "outside" else
                   f"only on {sheet_name} {title} (riser / schematic), not on a floor plan" if kind == "diagram" else
                   f"on {sheet_name} {title}, whose floor is not identified")
            off_plan.setdefault(key, []).extend((it, why) for it in items)
            continue
        for k in keys:
            floors.note(k, f"{label} · {sheet_name} {title}")
        ref = title if whole else f"{sheet_name} · {title}"
        radius = _radius(sheet, units)
        on_plans.add(key)
        if key == "gate_barrier":
            # W-5: one barrier per fire alarm connection point; the words "gate barrier" are context.
            # Never from the fire alarm IFC drawing itself (S13 W-5): its own cable notes are the
            # fire alarm's design, not the gate barrier package's evidence of how many barriers.
            instances = [it for it in items if it.get("kind") == "instance" and src.get("kind") != "fa_ifc"]
            for it in instances:
                equipment.append({**_item(src, it, key, keys, label, ref, sheet_name, 1), "radius": radius,
                                  "gate": {"role": it.get("role"), "settled": bool(it.get("settled")),
                                           "why": it.get("why"), "margin": it.get("margin"), "role_d": it.get("role_d")}})
            named = [it for it in items if (it.get("kind") != "instance" or src.get("kind") == "fa_ifc")
                     and not geometry.NOTE_ONLY.search(it["text"])]
            if named and not instances:
                groups.append(_group(src, key, sheet_name, floors_obj=floors, keys=keys, qty=None, label=label, ref=ref,
                                     items=named,
                                     reason="The drawing names gate barriers but shows no fire alarm connection point "
                                            "for them: say how many barriers the fire alarm controls here (none is "
                                            "counted from a name alone)"))
            continue
        if key in SYSTEM_KEYS:
            groups.append(_group(src, key, sheet_name, floors_obj=floors, keys=keys,
                                 qty=len(_clusters(items, _radius(sheet, units, notes=True))),
                                 label=label, ref=ref, items=items,
                                 reason="The drawing shows the system by a note or label, not by its panel: say how many "
                                        "systems / panels the fire alarm serves here"))
            continue
        if key in visual.KEYS:
            # W-3: a damper counts when the drawing looked at says its label is a damper's,
            # and that label is settled on a damper symbol drawn here -- the symbol is where
            # it is. Each symbol is one damper; two labels on one symbol with different
            # words, and every label without a settled symbol, are held.
            metre = _METRE.get(units, 1.0)
            kept, held = [], {}
            for it in items:
                v = visual.verdict(src, it)
                assoc = it.get("association") or {}
                symbol = assoc.get("symbol") if assoc.get("state") == "settled" else None
                if v is not None and not v["damper"]:
                    equipment.append({**_item(src, it, key, keys, label, ref, sheet_name, 1), "radius": radius,
                                      "visual_reject": v.get("what") or "not a damper"})
                    continue
                if symbol is not None and "$0$" in (symbol.get("block") or ""):
                    held.setdefault("architecture", []).append(it)        # a door, a wall: the architect's block
                    continue
                if v is None:
                    held.setdefault("unseen", []).append(it)
                    continue
                if symbol is None:
                    held.setdefault("no_symbol", []).append(it)
                    continue
                at = v.get("at")
                if isinstance(at, list) and len(at) == 2 and all(isinstance(n, (int, float)) for n in at):
                    x0, y0, x1, y1 = symbol["bounds"]
                    gap = math.hypot(max(x0 - at[0], 0.0, at[0] - x1), max(y0 - at[1], 0.0, at[1] - y1))
                    if gap > DAMPER_SNAP_M * metre:
                        held.setdefault("elsewhere", []).append(it)
                        continue
                kept.append({**it, "label_anchor": [it["x"], it["y"]], "equipment_anchor": list(symbol["centre"]),
                             "symbol": symbol, "confidence": detect.HIGH, "visual": True})
            by_symbol: dict[str, list[dict]] = {}
            for it in kept:
                by_symbol.setdefault(it["symbol"]["id"], []).append(it)
            items = []
            for claims in by_symbol.values():
                if len({detect.normalize(c["text"]) for c in claims}) > 1:
                    held.setdefault("shared", []).extend(claims)
                else:
                    items.append({**claims[0], "labels_on_symbol": len(claims)})
            reasons = {
                "unseen": "The label was found but not looked at on the drawing yet (AI visual check): confirm "
                          "each damper symbol; a label's text position is not a damper position.",
                "no_symbol": "Looked at and called a damper, but the label is not settled on one drawn symbol "
                             "(none near it, or two about as near): confirm which symbol it names.",
                "architecture": "The label sits on an architectural block (a door or wall from the architect's "
                                "drawing), not a damper symbol: confirm whether it is a damper at all.",
                "elsewhere": "Looked at and called a damper, but the point the model gave is not on the symbol "
                             "the label names: confirm the damper.",
                "shared": "Different labels name one drawn symbol: confirm which damper each label means.",
            }
            for why, its in held.items():
                groups.append(_group(src, key, f"{sheet_name}|{why}" if why != "unseen" else sheet_name,
                                     floors_obj=floors, keys=keys, qty=None, label=label, ref=ref, items=its,
                                     reason=reasons[why]))
        unsure = [it for it in items if it["confidence"] == detect.LOW]
        if unsure:
            groups.append(_group(src, key, sheet_name, floors_obj=floors, keys=keys,
                                 qty=len(_clusters(unsure, radius)), label=label, ref=ref, items=unsure,
                                 reason="The drawing does not say it is automatic, motorized or held open: confirm it "
                                        "is interfaced before it is scheduled"))
        sure = [it for it in items if it["confidence"] != detect.LOW]
        for it in (it for it in sure if it.get("tag")):
            # The schedule tells a tag repeated on each floor's plan apart:
            # "SEF-1" on the 2nd basement plan is its "B2-SEF-1".
            sched.plan_bases.add(SCH.tag_identity(it["tag"]))
            hit = sched.resolve(it["tag"], keys)
            if hit and hit["prefix_floor"]:
                it = {**it, "tag": hit["tag"]}
            tk = SCH.tag_identity(it["tag"])
            if tk in tags_on_plans:
                held = tags_on_plans[tk]
                if held["keys"] != keys and ref not in held["also"]:
                    held["also"].append(ref)
                continue
            tags_on_plans[tk] = {"keys": keys, "ref": ref, "tag": it["tag"], "also": []}
            equipment.append({**_item(src, it, key, keys, label, ref, sheet_name, 1), "schedule": hit, "radius": radius})
            placed[key] = placed.get(key, 0) + len(keys)
        for it in (it for it in sure if it.get("visual") and not it.get("tag")):
            equipment.append({**_item(src, it, key, keys, label, ref, sheet_name, 1), "radius": radius, "visual": True})
            placed[key] = placed.get(key, 0) + len(keys)
        for cluster in _clusters([it for it in sure if not it.get("tag") and not it.get("visual")], radius):
            equipment.append({**_item(src, cluster[0], key, keys, label, ref, sheet_name, len(cluster)), "radius": radius})
            placed[key] = placed.get(key, 0) + len(keys)

    if src["discipline"] == FF:
        for key, keys, it, sheet_name, ref in _pump_room_pumps(result, floors):
            on_plans.add(key)
            equipment.append({**_item(src, it, key, keys, label, ref, sheet_name, 1),
                              "radius": _radius(sheets.get(sheet_name), units)})
            placed[key] = placed.get(key, 0) + len(keys)

    for key, entries in off_plan.items():
        if key in on_plans:
            # Evidence for the plans. A riser that labels more than the plans
            # place is reported; a tag no plan shows is still asked about.
            riser = sum(1 for it, why in entries if "riser" in why and not it.get("tag"))
            if riser > placed.get(key, 0) and key not in SYSTEM_KEYS:
                conflicts.append(f"{BY_KEY[key].name}: the riser / schematic of {label} labels {riser}, the floor "
                                 f"plans place {placed.get(key, 0)} -- check the floors whose plan has no label.")
            entries = [(it, why) for it, why in entries
                       if it.get("tag") and SCH.tag_identity(it["tag"]) not in tags_on_plans
                       and SCH.tag_identity(it["tag"]) not in sched.plan_bases]
            if not entries:
                continue
        items = [it for it, _why in entries]
        tags = sorted({it["tag"] for it in items if it.get("tag")})
        whys = sorted({why for _it, why in entries})
        groups.append(_group(src, key, "off-plan", floors_obj=floors, keys=[], qty=len(tags) or None, label=label,
                             ref="; ".join(whys), items=items, tags=tags,
                             reason=f"Shown {'; '.join(whys)}: say which floor it is on and how many"))

    if src["discipline"] == ARCH:
        lift = _lift_group(src, result, floors, label)
        if lift:
            groups.append(lift)


def _item(src: dict, it: dict, key: str, keys: list[str], label: str, ref: str, sheet: str, count: int) -> dict:
    out = {"key": key, "tag": it.get("tag"), "keys": keys, "src": src, "label": label, "ref": ref,
           "sheet": sheet, "detail": it.get("detail", ""), "text": it["text"],
           "confidence": it["confidence"], "anchor": (it["x"], it["y"]), "count": count}
    out["label_anchor"] = list(it["label_anchor"]) if it.get("label_anchor") is not None else [it["x"], it["y"]]
    assoc = it.get("association") or {}
    symbol = assoc.get("symbol") if assoc.get("state") == "settled" else None
    if it.get("equipment_anchor") is not None:
        out["equipment_anchor"] = list(it["equipment_anchor"])
        out["location_state"] = "leader" if it.get("kind") == "instance" else "symbol"
        if it.get("symbol"):
            out["symbol"] = it["symbol"]
    elif symbol is not None and "$0$" not in (symbol.get("block") or ""):
        out["equipment_anchor"] = list(symbol["centre"])
        out["location_state"] = "symbol"
        out["symbol"] = symbol
    else:
        out["location_state"] = "held" if assoc.get("state") == "ambiguous" else "label_only"
    return out


def _repeated_tags(tags_on_plans: dict) -> list[str]:
    """One note per set of tags a drawing repeats on other floors' plans
    ("SEF-1 ... MAF-4 are on the 3rd, 2nd and 1st basement plans"): each is
    scheduled once, on the first plan that shows it."""
    groups: dict[tuple, list[str]] = {}
    for held in tags_on_plans.values():
        if held["also"]:
            groups.setdefault((held["ref"], tuple(held["also"])), []).append(held["tag"])
    return [f"{', '.join(sorted(tags))} {'is' if len(tags) == 1 else 'are'} on {first} and also on {'; '.join(also)}: "
            f"each scheduled once, on {first.split(' · ')[0]} -- check which floor each serves."
            for (first, also), tags in groups.items()]


def _landmarks(e: dict) -> dict:
    return (e["src"].get("result") or {}).get("landmarks") or {}


def _sid(e: dict) -> str:
    return f"{e['src']['discipline']}|{e['src']['relative_path']}"


def _windows_of(e: dict) -> list | None:
    """The model-space windows of the sheet an item is on (None: not recorded)."""
    if e["sheet"] == scan.WHOLE:
        return []
    for sh in (e["src"].get("result") or {}).get("sheets", []):
        if sh.get("name") == e["sheet"]:
            return sh.get("windows")
    return None


def _same_view(a: list[dict], b: list[dict], metre: float) -> bool:
    """W-4 (S13): a floor counts as one frame on two drawings only where the
    sheets it is drawn on view the same piece of model space in both. A sheet
    whose windows were not recorded is not the same as anything."""
    def views(entries):
        out = []
        for e in entries:
            w = _windows_of(e)
            if w is None:
                return None
            out.extend(tuple(x) for x in w)
        return sorted(set(out))

    va, vb = views(a), views(b)
    if va is None or vb is None or len(va) != len(vb):
        return False
    tol = geometry.ALIGN_MATCH_M * metre
    for x, y in zip(va, vb):
        cx, cy, w, h, twist, tx, ty = x
        cx2, cy2, w2, h2, twist2, tx2, ty2 = y
        if max(abs(cx - cx2), abs(cy - cy2), abs(w - w2), abs(h - h2), abs(tx - tx2), abs(ty - ty2)) > tol \
                or abs(twist - twist2) > 1e-3:
            return False
    return True


def _paired(entries: list[dict], sids: list[str], tolerance: float) -> bool:
    """Whether the drawings place the same number of items here and every one
    of each drawing has its own partner on every other within `tolerance`:
    then items placed by their label only are counted once. Otherwise a label's
    offset could count one item twice, or two as one."""
    per = {sid: [e for e in entries if _sid(e) == sid] for sid in sids}
    if len({len(v) for v in per.values()}) != 1:
        return False

    def point(e):
        return e.get("equipment_anchor") or e.get("label_anchor") or list(e["anchor"])

    base = per[sids[0]]
    for sid in sids[1:]:
        free = list(per[sid])
        for e in base:
            twin = min(free, key=lambda o: math.dist(point(e), point(o)), default=None)
            if twin is None or math.dist(point(e), point(twin)) > tolerance:
                return False
            free.remove(twin)
    return True


def _equipment_rows(equipment: list[dict], floors: Floors, conflicts: list[str], sched: Schedule,
                    held_conflicts: list | None = None) -> list[dict]:
    """A line per item per floor it stands for. One piece of equipment shown
    on several drawings is counted once: per floor and kind, the untagged
    items of the drawing that shows the most are counted -- the discipline's
    own drawing before the architecture on a tie -- and the other drawings
    are its evidence, said in one note."""
    equipment = [e for e in equipment if not e.get("gate")]   # gate barriers: _gate_rows
    held_conflicts = held_conflicts if held_conflicts is not None else []
    shown: dict[tuple[str, str], dict[str, int]] = {}
    source: dict[str, dict] = {}
    tagged_by: dict[tuple[str, str], set[str]] = {}       # (kind, floor) -> the drawings that tag it there
    shadow: dict[tuple[str, str], set[str]] = {}          # (kind, drawing) -> floors it names what others tag
    for e in equipment:
        if e["tag"]:
            for k in e["keys"]:
                tagged_by.setdefault((e["key"], k), set()).add(f"{e['src']['discipline']}|{e['src']['relative_path']}")
    for e in equipment:
        e["skip"] = set()
        if e["tag"] or e.get("visual_reject"):
            continue                    # a tagged item is its own; one the look set aside is never counted
        sid = f"{e['src']['discipline']}|{e['src']['relative_path']}"
        # Its name written beside a tagged item of the same kind on the same sheet: that item.
        x, y = e["anchor"]
        if any(o["tag"] and o["key"] == e["key"] and o["sheet"] == e["sheet"] and o["src"] is e["src"]
               and math.hypot(o["anchor"][0] - x, o["anchor"][1] - y) <= e.get("radius", 0) for o in equipment):
            e["skip"] = set(e["keys"])
            continue
        # Named only, on a floor where another drawing tags this kind: the tagged ones are these.
        shadowed = {k for k in e["keys"] if tagged_by.get((e["key"], k), set()) - {sid}}
        if shadowed:
            e["skip"] = shadowed
            shadow.setdefault((e["key"], e["label"]), set()).update(shadowed)
        if not set(e["keys"]) - shadowed:
            continue
        source[sid] = e
        for k in set(e["keys"]) - e["skip"]:
            by = shown.setdefault((e["key"], k), {})
            by[sid] = by.get(sid, 0) + 1
    for (key, label), keys in shadow.items():
        conflicts.append(f"{BY_KEY[key].name} on {', '.join(floors.name(k) for k in sorted(keys, key=floors.order))}: "
                         f"{label} names it without a tag, another drawing tags it there -- the tagged ones are "
                         "counted, once.")
    # W-4: one kind on one floor drawn untagged on several drawings. Drawings whose frames
    # are verified the same (their landmarks coincide) give the union of their items, an
    # item drawn on both counted once. Drawings not verified the same are held as a
    # conflict -- never one drawing's count taken as the floor's.
    unions: dict[tuple, list[str]] = {}
    for kf, by in shown.items():
        if len(by) < 2:
            continue
        sids = sorted(by, key=lambda sid: _PRIORITY.get(source[sid]["src"]["discipline"], 9))
        metre = _METRE.get((source[sids[0]]["src"].get("result") or {}).get("units"), 1.0)
        entries = [e for e in equipment if not e["tag"] and not e.get("visual_reject")
                   and kf[1] in set(e["keys"]) - e["skip"] and e["key"] == kf[0]]
        # F7: the pair's frame (landmarks), and this floor's sheets viewed the same in both
        why = None
        for i, a in enumerate(sids):
            for b in sids[i + 1:]:
                if not geometry.aligned(_landmarks(source[a]), _landmarks(source[b]), metre)["aligned"]:
                    why = why or "frames"
                elif not _same_view([e for e in entries if _sid(e) == a], [e for e in entries if _sid(e) == b], metre):
                    why = why or "views"
        if why is None and any(e.get("equipment_anchor") is None for e in entries) \
                and not _paired(entries, sids, UNION_TOLERANCE_M * metre):
            why = "positions"          # placed by its label only: counted once only when every label pairs up
        if why is not None:
            for e in entries:
                e["skip"] = set(e["skip"]) | {kf[1]}
            held_conflicts.append({"key": kf[0], "floor": kf[1], "entries": entries, "why": why,
                                   "counts": {source[sid]["label"]: n for sid, n in by.items()}})
            continue
        kept: list[dict] = []
        for e in sorted(entries, key=lambda e: _PRIORITY.get(e["src"]["discipline"], 9)):
            point = e.get("equipment_anchor") or e.get("label_anchor") or list(e["anchor"])
            twin = next((o for o in kept if o["src"] is not e["src"]
                         and math.dist(point, o.get("equipment_anchor") or o.get("label_anchor") or list(o["anchor"]))
                         <= UNION_TOLERANCE_M * metre), None)
            if twin is not None:
                e["skip"] = set(e["skip"]) | {kf[1]}
                twin.setdefault("also_on", set()).add(e["label"])
            else:
                kept.append(e)
        unions.setdefault((kf[0], tuple(sorted(f"{source[sid]['label']} ({n})" for sid, n in by.items())),
                           len([e for e in kept])), []).append(kf[1])
    for (key, labels, n), keys in unions.items():
        conflicts.append(f"{BY_KEY[key].name} on {', '.join(floors.name(k) for k in sorted(keys, key=floors.order))}: "
                         f"drawn on several drawings in one verified frame ({', '.join(labels)}): counted as their "
                         f"union, an item drawn on both once.")
    rows = []
    for e in equipment:
        skipped = e["skip"]
        x, y = e["anchor"]                     # the label's point: the row's identity, never its location
        anchor = (detect.tag_key(e["tag"]) if e["tag"] else
                  f"{x:.1f},{y:.1f}" if e.get("visual") or e.get("visual_reject") else f"{round(x)},{round(y)}")
        base = f"{e['src']['discipline']}|{e['src']['relative_path']}|{e['sheet']}|{e['key']}|{anchor}"
        size = e["detail"] if e["detail"].startswith("Ø") else ""
        room = e["detail"] if e["detail"] and not size else ""
        typical = len(e["keys"]) > 1
        hit = e.get("schedule")
        if hit:
            sched.matched.add(hit["identity"])
        for k in e["keys"]:
            if k in skipped:
                continue
            if hit and hit["floors"] and k not in hit["floors"]:
                conflicts.append(f"{e['tag']}: the plan places it on {floors.name(k)}, the schedule ({hit['where']}) "
                                 f"says {hit['location'] or ', '.join(floors.name(f) for f in hit['floors'])}.")
            rows.append(_row(e["key"], floor=k, floors=floors, tag=e["tag"], location=room,
                             description=f"{BY_KEY[e['key']].name}{f' {size}' if size else ''} (drawn: \"{e['text']}\")",
                             discipline=e["src"]["discipline"], source=e["label"], drawing_ref=e["ref"],
                             confidence="High" if e["confidence"] == detect.HIGH else "Medium", basis="drawing",
                             row_id=f"{base}|{k}", typical=typical,
                             evidence=f"{e['count']} label{'s' if e['count'] > 1 else ''} on {e['sheet']}"
                                      + (f", a plan for {len(e['keys'])} floors" if typical else "")
                                      + (f"; in the schedule: {hit['where']}" if hit else "")))
            # where it stands: its drawn symbol (W-3), apart from where its label is written.
            # No settled symbol: no location (the redesign then asks for the module by hand).
            rows[-1]["sheet"] = e["sheet"]
            rows[-1]["label_anchor"] = [round(float(n), 3) for n in (e.get("label_anchor") or (x, y))]
            if e.get("equipment_anchor") is not None:
                rows[-1]["equipment_anchor"] = [round(float(n), 3) for n in e["equipment_anchor"]]
            rows[-1]["anchor"] = rows[-1].get("equipment_anchor")
            rows[-1]["location_state"] = e.get("location_state") or ("symbol" if e.get("equipment_anchor") else "label_only")
            if e.get("symbol"):
                rows[-1]["symbol_id"] = e["symbol"]["id"]
            if e.get("also_on"):
                rows[-1]["evidence"] += f"; also drawn on {', '.join(sorted(e['also_on']))}"
            if e.get("labels_on_symbol", 1) > 1:
                rows[-1]["evidence"] += f"; {e['labels_on_symbol']} labels on one symbol"
            if e.get("visual"):
                rows[-1]["evidence"] += "; seen on the drawing (AI visual check): a damper, here"
            if e.get("visual_reject"):
                rows[-1]["visual_reject"] = e["visual_reject"]
            if hit:
                rows[-1]["schedule"] = hit["where"]
    return rows


GATE_ACTIONS = {"exit": "To open the exit gate barrier",
                "entry": "To close the entrance gate barrier (additional control module)"}


def _gate_row(e: dict, k: str, floors: Floors, governed: dict | None = None) -> dict:
    role = e["gate"]["role"]
    x, y = e["anchor"]
    r = _row("gate_barrier", floor=k, floors=floors, tag=None, location=f"{role.title()} lane" if role else "",
             description=f"Gate Barrier, {role} (drawn: \"{e['text']}\")", discipline=e["src"]["discipline"],
             source=e["label"], drawing_ref=e["ref"], confidence="High", basis="drawing",
             row_id=f"{e['src']['discipline']}|{e['src']['relative_path']}|{e['sheet']}|gate_barrier|{role}@{x:.1f},{y:.1f}|{k}",
             evidence=f"Fire alarm connection point on {e['sheet']}, lane role {role} settled "
                      f"(assignment margin {e['gate'].get('margin')} m)"
                      + (f"; counted from this drawing on the engineer's choice, on the authority of "
                         f"{governed.get('authority')}: {governed.get('reason')}" if governed else ""))
    r["action"] = GATE_ACTIONS.get(role, r["action"])
    r["role"] = role
    r["sheet"] = e["sheet"]
    r["label_anchor"] = [round(float(n), 3) for n in e.get("label_anchor") or (x, y)]
    if e.get("equipment_anchor"):
        r["equipment_anchor"] = [round(float(n), 3) for n in e["equipment_anchor"]]
    r["anchor"] = r.get("equipment_anchor")
    r["location_state"] = "leader" if e.get("equipment_anchor") else "label_only"
    return r


def _gate_points(entries: list[dict]) -> list[dict]:
    """A drawing's gate barrier evidence as the engineer weighs it: each fire
    alarm connection point, its lane role (ENTRY / EXIT) and whether it settles."""
    return [{"x": round(e["anchor"][0], 3), "y": round(e["anchor"][1], 3), "sheet": e["sheet"],
             "role": e["gate"]["role"], "settled": e["gate"]["settled"], "why": e["gate"].get("why"),
             "margin": e["gate"].get("margin"),
             "equipment_anchor": [round(float(n), 3) for n in e["equipment_anchor"]] if e.get("equipment_anchor") else None}
            for e in entries]


def _gate_rows(gates: list[dict], floors: Floors, conflicts: list[str], decisions: dict) -> tuple[list, list]:
    """W-5: gate barriers, floor by floor. One drawing's settled connection points
    are one barrier each (a CR each, its action by its lane). Several drawings on a
    floor must agree -- the same frame and every point matched -- or they are held
    together as a conflict, until the engineer says which drawing governs, on whose
    authority. The conflict stays listed after that choice, with every drawing's
    points, so the choice can be reopened or changed (F3); a choice whose drawing is
    no longer among them is not applied."""
    rows, groups = [], []
    by_floor: dict[str, dict[str, list[dict]]] = {}
    for e in gates:
        for k in e["keys"]:
            by_floor.setdefault(k, {}).setdefault(f"{e['src']['discipline']}|{e['src']['relative_path']}", []).append(e)
    for k, per in sorted(by_floor.items(), key=lambda kv: floors.order(kv[0])):
        gid = f"GATE|{k}|conflict"
        decision = decisions.get(gid) or {}
        governing = decision.get("relative_path") if decision.get("status") == "governed" else None
        sids = list(per)
        chosen, agreed = None, False
        if len(sids) == 1:
            chosen = sids[0]
        else:
            first = per[sids[0]][0]
            metre = _METRE.get((first["src"].get("result") or {}).get("units"), 1.0)
            same_frame = all(geometry.aligned(_landmarks(per[a][0]), _landmarks(per[b][0]), metre)["aligned"]
                             for i, a in enumerate(sids) for b in sids[i + 1:])

            def matched(xs, ys):
                return len(xs) == len(ys) and all(
                    any(math.dist(list(p["anchor"]), list(q["anchor"])) <= GATE_MATCH_M * metre for q in ys) for p in xs)

            if same_frame and all(matched(per[sids[0]], per[sid]) for sid in sids[1:]):
                chosen = max(sids, key=lambda sid: sum(1 for e in per[sid] if e["gate"]["settled"]))
                agreed = True
            elif governing:
                chosen = next((sid for sid in sids if sid.split("|", 1)[1] == governing), None)
        if len(sids) > 1 and not agreed:
            summary = "; ".join(f"{per[sid][0]['label']}: {len(per[sid])} connection point(s) at "
                                + ", ".join(f"({e['anchor'][0]:.1f}, {e['anchor'][1]:.1f})" for e in per[sid][:6])
                                for sid in sids)
            rule = BY_KEY["gate_barrier"]
            group = {"id": gid, "key": "gate_barrier", "equipment": rule.name, "discipline": GB,
                     "system": DISCIPLINE_NAMES[GB], "source": ", ".join(per[sid][0]["label"] for sid in sids),
                     "ref": floors.name(k), "proposed_floor_keys": [k], "proposed_floors": [floors.name(k)],
                     "proposed_qty": None, "tags": [], "location": "", "labels": sum(len(v) for v in per.values()),
                     "reason": "The drawings disagree on this floor's gate barriers (different points or counts): "
                               "say which drawing governs, on whose authority (the consultant, the site); until "
                               "then none is counted.",
                     "evidence": summary, "contacts": rule.contacts, "monitoring": rule.monitoring,
                     "control": rule.control, "status": "open", "conflict": True,
                     "drawings": [{"relative_path": sid.split("|", 1)[1], "label": per[sid][0]["label"],
                                   "revision": per[sid][0]["src"].get("revision"),
                                   "points": len(per[sid]),
                                   "settled": sum(1 for e in per[sid] if e["gate"]["settled"]),
                                   "connection_points": _gate_points(per[sid])} for sid in sids]}
            if governing and chosen is None:
                group["decision_not_applied"] = True
                group["reason"] = (f"The engineer chose {governing} to govern, but it is not among this floor's "
                                   "drawings now: say again which drawing governs; until then none is counted.")
            groups.append(group)
            if chosen is None:
                conflicts.append(f"Gate barriers on {floors.name(k)}: {summary} -- held until the governing drawing "
                                 "is chosen.")
                continue
        if len(sids) > 1:
            others = [per[sid][0]["label"] for sid in sids if sid != chosen]
            conflicts.append(f"Gate barriers on {floors.name(k)}: counted from {per[chosen][0]['label']}"
                             + (" (the drawings agree)" if agreed else
                                f" (the engineer's choice, on the authority of {decision.get('authority') or 'not given'})")
                             + f"; also shown on {', '.join(others)}.")
        settled = [e for e in per[chosen] if e["gate"]["settled"]]
        unsettled = [e for e in per[chosen] if not e["gate"]["settled"]]
        for e in settled:
            rows.append(_gate_row(e, k, floors, None if agreed or len(sids) == 1 else decision))
        if unsettled:
            e0 = unsettled[0]
            groups.append(_group(e0["src"], "gate_barrier", f"{e0['sheet']}|gate", floors_obj=floors, keys=[k],
                                 qty=len(unsettled), label=e0["label"], ref=e0["ref"],
                                 items=[{"text": e["text"], "detail": ""} for e in unsettled],
                                 reason="Fire alarm connection points of gate barriers whose lane (entry / exit) the "
                                        "drawing does not settle: " + "; ".join(sorted({e["gate"]["why"] or "" for e in unsettled}))))
    return rows, groups


_CONFLICT_WHY = {
    "frames": "Drawn on several drawings whose frames are not verified to be the same: say how many there are "
              "(none is counted from one drawing's count alone).",
    "views": "Drawn on several drawings that share a frame, but this floor's sheets do not view the same piece of "
             "it on both: say how many there are (none is counted from one drawing's count alone).",
    "positions": "Drawn on several drawings, placed by their labels only, and the labels do not pair up one to one: "
                 "say how many there are (an item is never counted twice, nor two as one, from label positions).",
}


def _conflict_groups(held: list[dict], floors: Floors) -> list[dict]:
    """W-4: what drawings in unverified frames show of one kind on one floor, held."""
    out = []
    for c in held:
        rule = BY_KEY[c["key"]]
        counts = "; ".join(f"{label}: {n}" for label, n in sorted(c["counts"].items()))
        out.append({"id": f"CONFLICT|{c['key']}|{c['floor']}", "key": c["key"], "equipment": rule.name,
                    "discipline": c["entries"][0]["src"]["discipline"] if c["entries"] else "",
                    "system": DISCIPLINE_NAMES.get(c["entries"][0]["src"]["discipline"], "") if c["entries"] else "",
                    "source": ", ".join(sorted(c["counts"])), "ref": floors.name(c["floor"]),
                    "reason": _CONFLICT_WHY.get(c.get("why"), _CONFLICT_WHY["frames"]),
                    "proposed_floor_keys": [c["floor"]], "proposed_floors": [floors.name(c["floor"])],
                    "proposed_qty": None, "tags": [], "location": "", "labels": len(c["entries"]),
                    "evidence": counts, "contacts": rule.contacts, "monitoring": rule.monitoring,
                    "control": rule.control, "status": "open", "conflict": True})
    return out


def _schedule_checks(rows: list[dict], sched: Schedule, floors: Floors, conflicts: list[str]) -> list[dict]:
    """The plans against the equipment schedules (§35): a tag the plans
    place that no schedule lists is reported; what a schedule lists that no
    plan places is asked about -- one question a schedule row, its floor
    and quantity proposed from the schedule -- never scheduled on its word."""
    if not sched.entries:
        return []
    missing = sorted({r["tag"] for r in rows if r["basis"] == "drawing" and r["tag"] != NO_TAG
                      and r["key"] in sched.keys and not r.get("schedule")})
    if missing:
        conflicts.append(f"On the plans, not in the equipment schedules: {', '.join(missing)} -- check the schedule "
                         "is complete, or the tag.")
    out, by_row = [], {}
    for e in sched.entries:
        if e["identity"] not in sched.matched:
            by_row.setdefault(e["row_id"], []).append(e)
    for row_id, entries in by_row.items():
        first = entries[0]
        rule = BY_KEY[first["key"]]
        keys = first["floors"]
        out.append({
            "id": f"{SCHEDULE}|{row_id}|verify", "key": first["key"], "equipment": rule.name,
            "discipline": rule.disciplines[0] if rule.disciplines else HVAC,
            "system": "Equipment Schedule", "source": first["source"], "ref": first["where"],
            "reason": f"In the equipment schedule ({first['where']}{', ' + first['location'] if first['location'] else ''}), "
                      "not placed on any plan read: confirm the floor and quantity before it is scheduled",
            "proposed_floor_keys": keys[:1] if len(keys) == 1 else [],
            "proposed_floors": [floors.name(k) for k in keys[:1]] if len(keys) == 1 else [],
            "proposed_qty": len(entries) if len(keys) == 1 else None, "tags": [e["tag"] for e in entries],
            "location": first["location"].title(), "labels": len(entries),
            "evidence": f"{len(entries)} in the schedule: {', '.join(e['tag'] for e in entries)}",
            "contacts": rule.contacts, "monitoring": rule.monitoring, "control": rule.control, "status": "open"})
    return out


def _once(rows: list[dict], conflicts: list[str]) -> list[dict]:
    """One line per tagged piece of equipment, whatever gave it: a tag a
    drawing places, an engineer confirmed from a schedule and added again is
    the one item. The drawing's line stands, then the engineer's, then an
    added one; the other is dropped and said."""
    order = {"drawing": 0, "engineer": 1, "manual": 2}
    kept: dict[tuple[str, str], dict] = {}
    out = []
    for r in sorted(rows, key=lambda r: order.get(r["basis"], 9)):
        if r["tag"] == NO_TAG or r["status"] != "scheduled":
            out.append(r)
            continue
        ident = (r["key"], SCH.tag_identity(r["tag"]))
        held = kept.get(ident)
        if held is None:
            kept[ident] = r
            out.append(r)
            continue
        conflicts.append(f"{r['tag']} is given twice -- {held['source']} ({held['floor']}) and {r['source']} "
                         f"({r['floor']}): counted once, from {held['source']}.")
    return out


def _resolved_rows(g: dict, d: dict, floors: Floors) -> list[dict]:
    """A verification item the engineer settled: its quantity on each floor
    they named, tagged as the drawing labels them where it does."""
    tags = [t for t in (d.get("tags") or []) if t] or g.get("tags") or []
    rows, n = [], 0
    for k in d.get("floor_keys") or []:
        for i in range(int(d.get("qty") or 0)):
            rows.append(_row(g["key"], floor=k, floors=floors, tag=tags[n] if n < len(tags) else None,
                             location=d.get("location") or g.get("location", ""),
                             description=f"{BY_KEY[g['key']].name} (confirmed by the engineer)",
                             discipline=g["discipline"], source=g["source"], drawing_ref=g["ref"],
                             confidence="Engineer verified", basis="engineer", row_id=f"{g['id']}|{k}|{i}",
                             evidence=g["evidence"]))
            if g.get("anchor"):
                rows[-1]["anchor"], rows[-1]["sheet"] = g["anchor"], g.get("sheet")
            n += 1
    return rows


def _manual_rows(m: dict, floors: Floors) -> list[dict]:
    """An item the engineer added, with the drawing they saw it on."""
    rule = BY_KEY[m["key"]]
    tags = [t for t in (m.get("tags") or []) if t]
    discipline = m.get("discipline") or (rule.disciplines[0] if rule.disciplines else ARCH)
    rows, n = [], 0
    for k in m.get("floor_keys") or []:
        for i in range(int(m.get("qty") or 1)):
            r = _row(m["key"], floor=k, floors=floors, tag=tags[n] if n < len(tags) else None,
                     location=m.get("location", ""), description=f"{rule.name} (added by the engineer)",
                     discipline=discipline, source=m.get("source", ""), drawing_ref=m.get("drawing_ref", ""),
                     confidence="Engineer verified", basis="manual", row_id=f"manual|{m['id']}|{k}|{i}",
                     evidence=m.get("remarks", ""))
            r["manual_id"] = m["id"]
            rows.append(r)
            n += 1
    return rows


def _group(src: dict, key: str, where: str, *, floors_obj: Floors, keys: list[str], qty: int | None, label: str,
           ref: str, reason: str, items: list[dict], tags: list[str] | None = None) -> dict:
    rule = BY_KEY[key]
    texts = sorted({it["text"] for it in items})
    location = next((it["detail"] for it in items if it.get("detail") and not it["detail"].startswith("Ø")), "")
    return {"id": f"{src['discipline']}|{src['relative_path']}|verify|{where}|{key}", "key": key, "equipment": rule.name,
            "discipline": src["discipline"], "system": DISCIPLINE_NAMES[src["discipline"]], "source": label, "ref": ref,
            "reason": reason, "proposed_floor_keys": keys, "proposed_floors": [floors_obj.name(k) for k in keys],
            "proposed_qty": qty, "tags": tags or [], "location": location, "labels": len(items),
            "evidence": f"{len(items)} label{'s' if len(items) != 1 else ''}: " + "; ".join(t[:80] for t in texts[:4]),
            "contacts": rule.contacts, "monitoring": rule.monitoring, "control": rule.control, "status": "open"}


FIRE_PUMPS = (("electric_fire_pump", 1), ("diesel_fire_pump", 1), ("jockey_pump", 1))
_SPRINKLER_VALVES = ("alarm_check_valve", "zone_control_valve", "gate_valve")
_METRE = {"mm": 1000.0, "cm": 100.0, "m": 1.0, "in": 39.37, "ft": 3.281}
DAMPER_SNAP_M = 0.15          # W-3: a model's point within this of the damper symbol's bounds (EXAMPLE)
UNION_TOLERANCE_M = 0.5       # W-4: one item drawn on two aligned drawings (EXAMPLE)
GATE_MATCH_M = 3.0            # W-5: one barrier's connection point on two aligned drawings (EXAMPLE)


def _pump_room_pumps(result: dict, floors: Floors) -> list[tuple[str, list[str], dict, str, str]]:
    """The fire pumps of a pump room the plan draws but does not name
    (platform owner, 2 October 2026: EP-30880's 3rd basement pump set is
    drawn as graphics, its pumps named only on the schematic): a pump room on
    a fire fighting plan, beside the sprinkler valves (ACV, ZCV, OS&Y), on a
    floor where no fire pump is named -- scheduled with the pumps the
    drawing's schematic names (else a fire pump set's usual three), one each,
    in the room. (key, floor keys, item, sheet, ref) each."""
    sheets = {s["name"]: s for s in result.get("sheets", [])}
    metre = _METRE.get(result.get("units", "m"), 1.0)
    items = result.get("items", [])
    named_on_plans: set[str] = set()
    on_schematic: list[str] = []
    for it in items:
        if it["key"] not in dict(FIRE_PUMPS):
            continue
        s = sheets.get(it["sheet"])
        if s and _sheet_kind(s) == "plan":
            named_on_plans.update(floors.of_title(s["title"]))
        elif it["key"] not in on_schematic:
            on_schematic.append(it["key"])
    pumps = [k for k, _q in FIRE_PUMPS if k in on_schematic] or [k for k, _q in FIRE_PUMPS]
    valves = [it for it in items if it["key"] in _SPRINKLER_VALVES]
    out, done = [], set()
    for room in result.get("pump_rooms") or []:
        s = sheets.get(room["sheet"])
        if not s or _sheet_kind(s) != "plan" or room["sheet"] in done:
            continue
        keys = floors.of_title(s["title"])
        if not keys or set(keys) & named_on_plans:
            continue
        fire = "FIRE" in room["text"].upper() or any(
            v["sheet"] == room["sheet"] and math.hypot(v["x"] - room["x"], v["y"] - room["y"]) <= 12 * metre
            for v in valves)
        if not fire:
            continue
        done.add(room["sheet"])
        ref = f"{room['sheet']} · {s['title']}"
        said = "named on the schematic" if on_schematic else "a fire pump set's usual pumps"
        for key in pumps:
            it = {"tag": None, "detail": "Pump Room", "confidence": detect.MEDIUM,
                  "text": f"pump set drawn in the {room['text'].lower()}, {said}", "x": room["x"], "y": room["y"]}
            out.append((key, keys, it, room["sheet"], ref))
    return out


def _lift_group(src: dict, result: dict, floors: Floors, label: str) -> dict | None:
    """The lifts, once per lift (never floor by floor): the lift labels the
    architecture carries, and the machine room where the interface sits."""
    lifts = result.get("lifts") or []
    if not lifts:
        return None
    sheets = {s["name"]: s for s in result.get("sheets", [])}
    names = sorted({l["label"] for l in lifts}, key=lambda n: (not re.search(r"\d", n), [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", n)]))
    numbered = [n for n in names if re.search(r"\d|\b[A-Z]$", n)]      # LIFT 1, LIFT A: not FIRE LIFT
    named = [n for n in names if n not in numbered]
    rooms = {}
    for m in result.get("machine_rooms") or []:
        s = sheets.get(m["sheet"])
        for k in floors.of_title(s["title"]) if s else []:
            rooms[k] = rooms.get(k, 0) + 1
    served = set()
    for l in lifts:
        s = sheets.get(l["sheet"])
        if s and _sheet_kind(s) == "plan":
            served.update(floors.of_title(s["title"]))
    served_names = [floors.name(k) for k in sorted(served, key=floors.order)]
    room_keys = sorted(rooms, key=floors.order)
    notes = [f"Lift labels: {', '.join(names)}"]
    if served_names:
        notes.append(f"shown on {served_names[0]} to {served_names[-1]}")
    notes.append(f"lift machine room on {', '.join(floors.name(k) for k in room_keys)}" if room_keys
                 else "no lift machine room identified")
    if named and numbered:
        notes.append(f"{', '.join(named)} is labelled too: count it only if it is not one of {numbered[0]}–{numbered[-1]}")
    rule = BY_KEY["lift_system"]
    return {"id": f"{ARCH}|{src['relative_path']}|verify|lifts|lift_system", "key": "lift_system", "equipment": rule.name,
            "discipline": ARCH, "system": DISCIPLINE_NAMES[ARCH], "source": label,
            "ref": "Lift labels on the architectural plans" + (f"; machine room on {', '.join(floors.name(k) for k in room_keys)}" if room_keys else ""),
            "reason": "The lift interface is scheduled once per lift at its controller, not floor by floor: confirm the "
                      "number of lifts and where their controllers are" + ("" if room_keys else " (no machine room found)"),
            "proposed_floor_keys": room_keys[:1] if len(room_keys) == 1 else [],
            "proposed_floors": [floors.name(k) for k in room_keys[:1]] if len(room_keys) == 1 else [],
            "proposed_qty": len(numbered) or len(named) or None, "tags": numbered or named,
            "location": "Lift Machine Room" if room_keys else "", "labels": len(lifts),
            "evidence": "; ".join(notes), "contacts": rule.contacts, "monitoring": rule.monitoring,
            "control": rule.control, "status": "open"}


# --- summaries --------------------------------------------------------------------------------------


def _mods(rows: list[dict]) -> dict[str, int]:
    out = {"CT1": 0, "CT2": 0, "CR": 0}
    for r in rows:
        for k, v in r["modules"].items():
            out[k] += v
    return out


def floor_summary(rows: list[dict], floors: Floors) -> list[dict]:
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["floor_key"], []).append(r)
    out = []
    for k in sorted(by, key=floors.order):
        rs = by[k]
        m, c = sum(r["monitoring"] for r in rs), sum(r["control"] for r in rs)
        out.append({"floor_key": k, "floor": floors.name(k), "items": len(rs), "monitoring": m, "control": c,
                    "total": m + c, "modules": _mods(rs), "module_qty": sum(r["module_qty"] for r in rs)})
    return out


def type_summary(rows: list[dict]) -> list[dict]:
    out = []
    for rule in RULES:
        rs = [r for r in rows if r["key"] == rule.key]
        if not rs:
            continue
        out.append({"key": rule.key, "equipment": rule.name, "contacts": rule.contacts, "qty": len(rs),
                    "monitoring": sum(r["monitoring"] for r in rs), "control": sum(r["control"] for r in rs),
                    "modules": _mods(rs), "module_qty": sum(r["module_qty"] for r in rs)})
    return out


def totals(rows: list[dict], to_verify: int) -> dict:
    m, c = sum(r["monitoring"] for r in rows), sum(r["control"] for r in rows)
    mods = _mods(rows)
    return {"items": len(rows), "monitoring": m, "control": c, "interface_points": m + c, "modules": mods,
            "monitoring_modules": mods["CT1"] + mods["CT2"], "control_modules": mods["CR"],
            "module_qty": sum(mods.values()), "to_verify": to_verify}


# --- coverage: which drawings were received ---------------------------------------------------------


BADGES = {
    "unreachable": "Unreachable", "no_folder": "No project folder", "not_synced": "Not synced",
    "missing_last_known": "Missing, last known kept", "missing": "Missing",
    "received_not_read": "Received, not read", "received_unreadable": "Received, not readable (PDF)",
    "received": "Received", "received_fa_only": "Received (fire alarm IFC only)",
}
_RECEIVED = ("received_not_read", "received_unreadable", "received", "received_fa_only")


def _file_row(e: dict, *, present: bool, status: str, reason: str | None = None) -> dict:
    result = e.get("result") or ((e.get("last_known") or {}).get("result") if status == "stale" else None) or {}
    sheets = result.get("sheets", []) if e.get("kind") != "schedule" else []
    return {"filename": e.get("filename"), "relative_path": e.get("relative_path"), "kind": e.get("kind"),
            "revision": e.get("revision"), "status": status, "reason": reason or e.get("stale_reason"),
            "error": e.get("error"), "present": present, "cloud_only": bool(e.get("cloud_only")),
            "last_known_at": (e.get("last_known") or {}).get("read_at") if status == "stale" else None,
            "modified": datetime.fromtimestamp(e["mtime"]).isoformat() if e.get("mtime") else None,
            "size": e.get("size"),
            "sheets": len(sheets) if e.get("kind") != "schedule" else len(result.get("items", [])),
            "plans": sum(1 for s in sheets if _sheet_kind(s) == "plan"),
            "items": (len(result.get("items", [])) if e.get("kind") != "schedule"
                      else sum(len(i["tags"]) for i in result.get("items", []))),
            "lifts": len({l["label"] for l in result.get("lifts", [])})}


def _package(code: str, name: str, folder: str | None, purpose: str, entries: list[dict], listed: list,
             listing: "evidence.Listing", current_keys: set, fa_present: list[str]) -> dict:
    """One package's badge (S9 ordered, C8) and its files."""
    by_path = {e.get("relative_path"): e for e in entries}
    files, present_supported, present_unsupported, pending = [], 0, 0, 0
    for item in listed:
        e = by_path.get(item.relative_path)
        supported = item.filename.lower().endswith(evidence.SUPPORTED + evidence.WORKBOOKS)
        if not supported:
            present_unsupported += 1
            files.append(_file_row(e or {"filename": item.filename, "relative_path": item.relative_path,
                                         "kind": "unsupported", "size": item.size, "mtime": item.mtime},
                                   present=True, status="unsupported"))
            continue
        present_supported += 1
        if e is not None and (code, item.relative_path) in current_keys:
            files.append(_file_row({**e, "cloud_only": item.cloud_only}, present=True, status="read"))
        elif e is not None and e.get("status") == "superseded":
            files.append(_file_row(e, present=True, status="superseded"))
        else:
            pending += 1
            if e is None:
                files.append(_file_row({"filename": item.filename, "relative_path": item.relative_path, "kind": "folder",
                                        "size": item.size, "mtime": item.mtime}, present=True, status="unread"))
            elif e.get("status") == "read":
                files.append(_file_row(e, present=True, status="stale", reason="changed_since_read"))
            else:
                files.append(_file_row(e, present=True, status=e.get("status") or "unread"))
    listed_paths = {i.relative_path for i in listed}
    fa_current = 0
    for e in entries:
        if e.get("relative_path") in listed_paths:
            continue
        if e.get("kind") == "fa_ifc" and e.get("relative_path") in fa_present:
            is_current = (code, e.get("relative_path")) in current_keys
            fa_current += is_current
            if not is_current:
                pending += 1
            files.append(_file_row(e, present=True, status="read" if is_current else (e.get("status") if e.get("status") != "read" else "stale")))
            continue
        if e.get("status") in ("removed",) or e.get("kind") == "unsupported":
            continue
        status = "stale" if e.get("status") in ("read", "stale", "failed", "unread", "superseded") else e.get("status")
        files.append(_file_row(e, present=False, status=status,
                               reason=e.get("stale_reason") or ("changed_since_read" if e.get("status") == "read" else None)))
    for path in fa_present:
        if path not in by_path:
            pending += 1
            files.append(_file_row({"filename": path.rsplit("/", 1)[-1], "relative_path": path, "kind": "fa_ifc"},
                                   present=True, status="unread"))
    kept = any(not f["present"] and f["status"] == "stale" for f in files)
    if listing.root in ("unreachable", "not_configured", "ifc_root_missing"):
        badge = ("received_fa_only" if fa_current else
                 {"unreachable": "unreachable", "not_configured": "no_folder", "ifc_root_missing": "not_synced"}[listing.root])
    elif not present_supported and not present_unsupported and not fa_present:
        badge = "missing_last_known" if kept else "missing"
    elif pending:
        badge = "received_not_read"
    elif not present_supported and not fa_present:
        badge = "received_unreadable"
    else:
        badge = "received"
    received = badge in _RECEIVED
    return {"discipline": code, "name": name, "folder": folder, "purpose": purpose,
            "status": "available" if received else "missing", "received": received,
            "read": any((code, e.get("relative_path")) in current_keys for e in entries),
            "badge": badge, "badge_text": BADGES[badge] + (f" ({pending})" if badge == "received_not_read" else ""),
            "pending": pending, "files": files}


def coverage(row: ProjectFaInterfaces, listing: "evidence.Listing", fa_now: dict, view: "evidence.View",
             current_keys: set) -> list[dict]:
    """Per discipline: whether its drawings were received **now** (S9: only the
    current listing decides; saved readings never make a package Received),
    whether any is read and current, and each file with what it gave."""
    sources = row.sources or []
    out = []
    for d in DISCIPLINES:
        fs = listing.folders.get(d.code)
        listed = (fs.supported + fs.unsupported) if fs else []
        out.append(_package(d.code, DISCIPLINE_NAMES[d.code], d.folder, d.purpose,
                            [e for e in sources if e.get("discipline") == d.code], listed, listing, current_keys,
                            list(fa_now) if d.code == ARCH else []))
    listed = listing.mechanical.workbooks if listing.mechanical else []
    out.append(_package(SCHEDULE, "Equipment Schedules", f"{DRAWINGS}/IFC/Mechanical (Excel)",
                        "Schedules of fans, FAHU, AHU ...: the plans' fans and air handling units checked against them",
                        [e for e in sources if e.get("discipline") == SCHEDULE], listed, listing, current_keys, []))
    out.append({"discipline": "MATRIX", "name": "Interface Matrix", "folder": None, "status": "available", "read": True,
                "received": True, "badge": "received", "badge_text": "Received", "pending": 0,
                "purpose": f"{MATRIX_NAME}: {len(RULES)} rows" + (f"; rows {', '.join(map(str, UNCLEAR_ROWS))} not legible "
                                                                   "on the copy transcribed" if UNCLEAR_ROWS else ""),
                "files": []})
    # No Cause & Effect input: it is made from this schedule, not read into it.
    return out
