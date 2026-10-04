"""What the interface schedule's evidence is now: the project folder listed
(stat only, nothing opened), each saved reading judged current or not, and
which view of the schedule the page shows.

The contract is FI-P1 r3 (docs/milestones/fa-interfaces/FI-P1-R2-CORRECTION/
CORRECTION-R3.md) with its review conditions C1-C8 (REVIEW-R3.md). In short:

- A reading counts only while it is **current now**: its file is listed now
  with the size and modification time it was read at (a fire alarm IFC
  drawing: still in force, its DXF on this PC). Anything else is shown as
  last known, never counted, never "Received".
- A project folder that cannot be reached, or whose `03- Drawings/IFC` is not
  synced, never turns into an empty current schedule: the last published
  schedule is shown, labelled "not verified now".
- A file missing from a folder is not "removed" until the engineer says so
  or a newer revision of it is read: a half-synced OneDrive folder looks
  exactly like a deletion.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from app.services import document_control

DRAWINGS_IFC = "03- Drawings/IFC"
MECHANICAL = f"{DRAWINGS_IFC}/Mechanical"
SUPPORTED = (".dwg", ".dxf")
WORKBOOKS = (".xlsx", ".xlsm", ".xls")
IGNORED_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}
SKIP_SUFFIXES = (".dwl", ".dwl2", ".bak", ".tmp", ".sv$")

# Windows file attributes OneDrive's Files On-Demand sets.
ATTR_OFFLINE = 0x1000
ATTR_RECALL_ON_OPEN = 0x40000             # a folder whose listing is fetched when opened
ATTR_RECALL_ON_DATA_ACCESS = 0x400000     # a cloud-only file: reading it downloads it


def attributes(path: str) -> int:
    """The Windows file attributes of a path (0 elsewhere). A seam for tests."""
    try:
        return int(getattr(os.stat(path), "st_file_attributes", 0) or 0)
    except OSError:
        return 0


def file_attributes(path: str, st) -> int:
    """A listed file's Windows attributes, from the stat already made. A seam for tests."""
    return int(getattr(st, "st_file_attributes", 0) or 0)


def is_cloud_only(attrs: int) -> bool:
    return bool(attrs & (ATTR_RECALL_ON_DATA_ACCESS | ATTR_OFFLINE))


def ignored(name: str) -> bool:
    lowered = name.lower()
    return lowered in IGNORED_NAMES or name.startswith("~$") or lowered.endswith(SKIP_SUFFIXES)


@dataclass
class Listed:
    path: str
    relative_path: str
    filename: str
    size: int
    mtime: float
    cloud_only: bool = False


@dataclass
class FolderState:
    folder: str                      # relative to the project root
    state: str = "absent_or_empty"   # present | absent_or_empty | listing_failed
    supported: list[Listed] = field(default_factory=list)
    unsupported: list[Listed] = field(default_factory=list)
    workbooks: list[Listed] = field(default_factory=list)
    failed_dirs: list[str] = field(default_factory=list)   # relative paths whose listing failed

    def failed_for(self, relative_path: str) -> bool:
        return self.state == "listing_failed" or any(
            relative_path == d or relative_path.startswith(d.rstrip("/") + "/") for d in self.failed_dirs)


@dataclass
class Listing:
    root: str                        # ok | unreachable | not_configured | ifc_root_missing
    folders: dict[str, FolderState] = field(default_factory=dict)   # by discipline code
    mechanical: FolderState | None = None                             # the schedules' folder

    def files(self) -> dict[str, Listed]:
        out = {}
        for fs in list(self.folders.values()) + ([self.mechanical] if self.mechanical else []):
            for item in fs.supported + fs.unsupported + fs.workbooks:
                out[item.relative_path] = item
        return out


def _relative(root: Path, full: Path) -> str:
    try:
        return full.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return full.name


def _walk(root: Path, folder: str, *, workbooks: bool, ignore_workbooks: bool) -> FolderState:
    """One folder listed: supported drawings, unsupported files, workbooks;
    `present` only with a non-ignored file beneath it."""
    fs = FolderState(folder=folder)
    base = root / folder
    base_os = document_control._os_path(base)
    if not os.path.isdir(base_os):
        return fs
    errors: list[str] = []

    def onerror(exc: OSError) -> None:
        errors.append(getattr(exc, "filename", None) or str(exc))

    files = 0
    for dirpath, dirs, names in os.walk(base_os, onerror=onerror):
        if attributes(dirpath) & (ATTR_RECALL_ON_OPEN | ATTR_OFFLINE):
            # a folder whose contents OneDrive has not brought down: its listing says nothing
            fs.failed_dirs.append(_relative(root, Path(dirpath.removeprefix("\\\\?\\"))))
            dirs[:] = []
            continue
        for name in names:
            if ignored(name):
                continue
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
            except OSError as exc:
                errors.append(f"{full}: {exc}")
                continue
            files += 1
            item = Listed(path=full.removeprefix("\\\\?\\"), relative_path=_relative(root, Path(full.removeprefix("\\\\?\\"))),
                          filename=name, size=st.st_size, mtime=st.st_mtime,
                          cloud_only=is_cloud_only(file_attributes(full, st)))
            lowered = name.lower()
            if lowered.endswith(SUPPORTED):
                fs.supported.append(item)
            elif lowered.endswith(WORKBOOKS):
                if workbooks:
                    fs.workbooks.append(item)
                elif not ignore_workbooks:
                    fs.unsupported.append(item)
            else:
                fs.unsupported.append(item)
    for e in errors:
        path = Path(str(e).split(": ")[0].removeprefix("\\\\?\\"))
        fs.failed_dirs.append(_relative(root, path if path.is_absolute() else base))
    if errors and not files:
        fs.state = "listing_failed"
    elif files:
        fs.state = "present"
    if fs.failed_dirs and fs.state != "listing_failed":
        base_rel = _relative(root, base)
        if base_rel in fs.failed_dirs:
            fs.state = "listing_failed"
    return fs


def take(project, disciplines) -> Listing:
    """The project folder as it is now: stat only, nothing opened."""
    if not project.source_folder_path:
        return Listing(root="not_configured")
    root = Path(project.source_folder_path)
    if not os.path.isdir(document_control._os_path(root)):
        return Listing(root="unreachable")
    ifc = root / DRAWINGS_IFC
    ifc_os = document_control._os_path(ifc)
    try:
        has_entries = os.path.isdir(ifc_os) and any(True for _ in os.scandir(ifc_os))
    except OSError:
        has_entries = False
    if not has_entries or attributes(ifc_os) & (ATTR_RECALL_ON_OPEN | ATTR_OFFLINE):
        return Listing(root="ifc_root_missing")
    out = Listing(root="ok")
    for d in disciplines:
        out.folders[d.code] = _walk(root, d.folder, workbooks=False, ignore_workbooks=d.folder.startswith(MECHANICAL))
    out.mechanical = _walk(root, MECHANICAL, workbooks=True, ignore_workbooks=False)
    return out


# --- what counts now ------------------------------------------------------------------------------------


def listed_unchanged(entry: dict, listing: Listing, files: dict[str, Listed] | None = None) -> Listed | None:
    """The live listing of a folder/schedule entry, if it is listed now with
    the exact size and modification time it was read at."""
    if listing.root != "ok":
        return None
    item = (files if files is not None else listing.files()).get(entry.get("relative_path") or "")
    if item is None or item.size != entry.get("size") or item.mtime != entry.get("mtime"):
        return None
    return item


def current_now(entry: dict, listing: Listing, fa_in_force: dict[str, dict], files: dict[str, Listed] | None = None) -> bool:
    """C3: a stored `read` entry is current now when its evidence still stands."""
    if entry.get("status") != "read":
        return False
    if entry.get("kind") == "fa_ifc":
        live = fa_in_force.get(entry.get("relative_path") or "")
        return bool(live and live.get("dxf_exists") and (not entry.get("sha256") or live.get("sha256") in (None, entry.get("sha256"))))
    return listed_unchanged(entry, listing, files) is not None


def _key(entry: dict) -> tuple:
    return (entry.get("kind"), entry.get("discipline"), entry.get("relative_path"), entry.get("sha256"))


def digest(sources: list[dict]) -> str:
    """The identity of a set of readings: what was read, by which rules."""
    rows = sorted(
        [entry.get("kind") or "", entry.get("discipline") or "", entry.get("relative_path") or "",
         entry.get("sha256") or "", str((entry.get("result") or {}).get("scan_version") or ""),
         str((entry.get("result") or {}).get("schedule_version") or ""),
         str((entry.get("visual") or {}).get("version") or ""), str((entry.get("visual") or {}).get("status") or "")]
        for entry in sources if entry.get("status") == "read")
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def snapshot(sources: list[dict], job_id: int | None = None) -> dict:
    read = [dict(e) for e in sources if e.get("status") == "read"]
    return {"sources": read, "sources_digest": digest(read), "job_id": job_id}


def retired(entry: dict | None) -> bool:
    """A source that left the evidence for good: confirmed removed, replaced by a
    read successor, or (a fire alarm IFC) no longer in force."""
    if entry is None:
        return False
    if entry.get("status") == "removed":
        return True
    return entry.get("status") == "superseded" and bool(entry.get("retired_by"))


def snapshot_source_current(snap_entry: dict, sources: list[dict], listing: Listing, fa_in_force: dict,
                            files: dict | None = None) -> bool:
    """C3: a snapshot source is current now iff `sources` holds the same reading
    (kind, discipline, path, sha256), stored as read, and that one is current."""
    for entry in sources:
        if _key(entry) == _key(snap_entry) and entry.get("status") == "read":
            return current_now(entry, listing, fa_in_force, files)
    return False


@dataclass
class View:
    view_state: str          # current | provisional | unverified | not_read
    primary: str             # current | published | none
    current: list[dict]      # the entries current now
    reasons: list[str]
    publish_offered: bool = False


def choose(sources: list[dict], published: dict | None, listing: Listing, fa_in_force: dict) -> View:
    """S8.2 with C2: which schedule the page shows, first match wins."""
    files = listing.files() if listing.root == "ok" else {}
    current = [e for e in sources if current_now(e, listing, fa_in_force, files)]
    snap_sources = (published or {}).get("sources") or []
    if listing.root in ("not_configured", "unreachable", "ifc_root_missing"):
        why = {"not_configured": "the project has no folder", "unreachable": "the project folder cannot be reached",
               "ifc_root_missing": "the drawings folder (03- Drawings/IFC) is not synced"}[listing.root]
        return View("unverified", "published" if published else "none", current, [why])
    if not sources:
        return View("not_read", "none", current, ["the drawings have not been read yet"])
    by_key = {}
    for entry in sources:
        by_key.setdefault((entry.get("kind"), entry.get("discipline"), entry.get("relative_path")), entry)
    lost = [s for s in snap_sources
            if not snapshot_source_current(s, sources, listing, fa_in_force, files)
            and not retired(by_key.get((s.get("kind"), s.get("discipline"), s.get("relative_path"))))]
    if published and lost:
        return View("provisional", "published", current,
                    [f"{len(lost)} drawing(s) of the published schedule not verified now"])
    pending = not_current_present(sources, listing, fa_in_force, files)
    if pending:
        return View("provisional", "current" if published else "none", current,
                    [f"{len(pending)} drawing(s) not verified now"])
    if published and digest(current) != published.get("sources_digest"):
        return View("provisional", "current", current, ["the drawings read now differ from the published schedule"],
                    publish_offered=True)
    if not published:
        return View("provisional", "current" if current else "none", current,
                    ["not published yet"], publish_offered=bool(current))
    return View("current", "current", current, [])


def not_current_present(sources: list[dict], listing: Listing, fa_in_force: dict, files: dict | None = None) -> list[str]:
    """Supported drawings present now whose reading is not current: failed,
    unread, stale, changed since read, or new since the last read."""
    files = files if files is not None else (listing.files() if listing.root == "ok" else {})
    current_paths = {e.get("relative_path") for e in sources if current_now(e, listing, fa_in_force, files)}
    superseded = {e.get("relative_path") for e in sources if e.get("status") == "superseded"}
    out = []
    for fs in listing.folders.values():
        for item in fs.supported:
            if item.relative_path not in current_paths and item.relative_path not in superseded:
                out.append(item.relative_path)
    if listing.mechanical:
        for item in listing.mechanical.workbooks:
            if item.relative_path not in current_paths:
                out.append(item.relative_path)
    for path, live in fa_in_force.items():
        if path not in current_paths:
            out.append(path)
    return out
