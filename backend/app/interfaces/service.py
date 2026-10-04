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

from app.core.timeutils import utc_now
from app.ifc import storage
from app.ifc.dxf import sheets as S
from app.interfaces import detect, scan, visual
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


def discover(db: Session, project: Project) -> list[dict]:
    """Every drawing the schedule reads, discipline by discipline: the
    files in each IFC folder (a later revision of the same drawing stands
    for it -- the earlier is listed as superseded), and the fire alarm IFC
    drawings in force for their architecture."""
    out: list[dict] = []
    root = Path(project.source_folder_path) if project.source_folder_path else None
    for d in DISCIPLINES:
        if root is None:
            continue
        folder = root / d.folder
        files: list[tuple[Path, float, int]] = []
        for dirpath, _dirs, names in os.walk(document_control._os_path(folder)):
            for name in names:
                if not name.lower().endswith((".dwg", ".dxf")) or name.startswith("~$") or name.lower().endswith(_SKIP_FILE):
                    continue
                full = Path(dirpath) / name
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                files.append((full, st.st_mtime, st.st_size))
        latest: dict[str, tuple[int, float, str]] = {}
        for full, mtime, _size in files:
            drawing, rev = _stem(full.name)
            # a DXF beside its DWG is the same drawing: the DWG is the issued file
            rank = (rev, mtime, 1 if full.suffix.lower() == ".dwg" else 0)
            if drawing not in latest or rank > latest[drawing][:3]:
                latest[drawing] = (*rank, str(full))
        for full, mtime, size in sorted(files, key=lambda f: f[0].name.lower()):
            drawing, _rev = _stem(full.name)
            relative = _relative(root, full)
            out.append({"discipline": d.code, "kind": "folder", "path": str(full), "relative_path": relative,
                        "filename": full.name, "size": size, "mtime": mtime,
                        "superseded": latest[drawing][3] != str(full)})
    from app.ifc.services import revisions

    for fa in revisions.in_force(db, project.id):
        path = storage.dxf_path(fa)
        out.append({"discipline": ARCH, "kind": "fa_ifc", "path": str(path),
                    "relative_path": fa.archive_path or fa.filename, "filename": fa.filename,
                    "revision": fa.revision or "R0", "fa_drawing_id": fa.id, "sha256": fa.source_sha256,
                    "size": path.stat().st_size if path.is_file() else None,
                    "mtime": fa.uploaded_at.timestamp() if fa.uploaded_at else None, "superseded": False})
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


def scan_project(db: Session, project: Project, user_id: int | None = None, progress=None, check=None) -> dict:
    """Stage 1 for every drawing: a file read before, unchanged (same hash,
    same reading rules), is not read again."""
    from app.ifc.dxf import convert

    row = state(db, project)
    # A first read makes the project's row: committed now, not held open through
    # minutes of reading while the job's progress is written beside it.
    db.commit()
    before = {(s.get("discipline"), s.get("relative_path")): s for s in row.sources or []}
    found = discover(db, project)
    todo = [s for s in found if not s["superseded"]]
    converter = None
    done: list[dict] = []
    for i, src in enumerate(found):
        if check:
            check()
        if src["superseded"]:
            done.append({**_public(src), "status": "superseded"})
            continue
        n = todo.index(src) + 1
        if progress:
            progress(n - 1, len(todo), f"Reading {src['filename']} ({DISCIPLINE_NAMES[src['discipline']]})", src["filename"])
        path = Path(src["path"])
        try:
            sha = src.get("sha256") if src["kind"] == "fa_ifc" and src.get("sha256") else _sha256(path)
        except OSError as exc:
            done.append({**_public(src), "status": "failed", "error": f"The file could not be opened: {exc}"})
            continue
        old = before.get((src["discipline"], src["relative_path"]))
        if (old and old.get("sha256") == sha and old.get("status") == "read"
                and (old.get("result") or {}).get("scan_version") == scan.SCAN_VERSION):
            done.append({**old, **_public(src), "sha256": sha})
            continue
        entry = {**_public(src), "sha256": sha}
        try:
            dxf = path
            if src["kind"] == "folder" and path.suffix.lower() == ".dwg":
                dxf = cache_folder(project) / f"{sha[:24]}.dxf"
                if not dxf.is_file():
                    converter = converter or convert.find_converter()
                    if converter is None:
                        raise RuntimeError("No DWG converter on the PC the IFC worker runs on: install AutoCAD or the "
                                           "free ODA File Converter, or file the drawing as DXF too.")
                    dxf.parent.mkdir(parents=True, exist_ok=True)
                    started = datetime.now()
                    convert.convert_dwg_to_dxf(path, dxf, converter)
                    entry["converted_in"] = round((datetime.now() - started).total_seconds(), 1)
            elif not dxf.is_file():
                raise RuntimeError("The drawing's DXF is not on this PC: import the fire alarm IFC drawing again.")
            result = scan.read(str(dxf), src["discipline"], check=check)
            done.append({**entry, "status": "read", "result": result, "read_at": utc_now().isoformat()})
        except Exception as exc:  # noqa: BLE001 -- one drawing that cannot be read is named; the rest are read
            from app.services import jobs

            if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)):
                raise
            done.append({**entry, "status": "failed", "error": str(exc) or type(exc).__name__})
    done.extend(_read_schedules(project))
    if any(visual.wanted(s) for s in done):
        try:
            visual.check(db, project, done, check=check,
                         progress=(lambda d, t, m, f=None: progress(d, t, m, f)) if progress else None)
        except Exception as exc:  # noqa: BLE001 -- the reading stands; the labels are scheduled as read, said so
            from app.services import jobs

            if isinstance(exc, (jobs.Cancelled, jobs.Interrupted)):
                raise
            log.warning("The dampers could not be looked at on the drawings: %s", exc)
    row.sources = done
    row.scanned_at = utc_now()
    row.scanned_by_id = user_id
    db.commit()
    if progress:
        progress(len(todo), len(todo), "Read", None)
    return {"drawings": len(todo), "read": sum(1 for s in done if s["status"] == "read"),
            "failed": [{"filename": s["filename"], "error": s.get("error")} for s in done if s["status"] == "failed"]}


SCHEDULE = "SCHED"


def _read_schedules(project: Project) -> list[dict]:
    """The mechanical equipment schedules (Excel) in the project's mechanical
    IFC folders: a moment each, read every time."""
    if not project.source_folder_path:
        return []
    root = Path(project.source_folder_path)
    out = []
    for path in SCH.discover(root):
        try:
            st = os.stat(path)
            entry = {"discipline": SCHEDULE, "kind": "schedule", "relative_path": _relative(root, path),
                     "filename": path.name, "size": st.st_size, "mtime": st.st_mtime, "superseded": False}
        except OSError:
            continue
        try:
            out.append({**entry, "status": "read", "result": SCH.read(path), "read_at": utc_now().isoformat()})
        except Exception as exc:  # noqa: BLE001 -- a workbook that cannot be opened is named, the rest read
            out.append({**entry, "status": "failed", "error": f"The workbook could not be read: {exc}"})
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
    drawings read and the engineer's answers."""
    row = state(db, project)
    floors = Floors(db, project)
    groups: list[dict] = []
    conflicts: list[str] = []
    excluded_found: list[dict] = []
    equipment: list[dict] = []
    tags_on_plans: dict[str, dict] = {}
    # The discipline's own drawing first: it stands over the architecture for the same item.
    read = [s for s in row.sources or [] if s.get("status") == "read"]
    sched = Schedule([s for s in read if s["discipline"] == SCHEDULE], floors)
    sources = sorted((s for s in read if s["discipline"] != SCHEDULE), key=lambda s: _PRIORITY.get(s["discipline"], 9))
    for src in sources:
        _read_source(src, floors, equipment, groups, conflicts, excluded_found, tags_on_plans, sched)

    conflicts.extend(_repeated_tags(tags_on_plans))
    rows = _equipment_rows(equipment, floors, conflicts, sched)
    groups.extend(_schedule_checks(rows, sched, floors, conflicts))
    decisions: dict = row.decisions or {}
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
        if d:
            g["status"] = d.get("status", "open")
            g["decision"] = {k: v for k, v in d.items() if k != "status"}
        if g["status"] == "resolved":
            rows.extend(_resolved_rows(g, d, floors))
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
        "project": {"id": project.id, "ep_number": project.ep_number, "name": project.project_name},
        "scanned_at": row.scanned_at.isoformat() if row.scanned_at else None,
        "coverage": coverage(db, project, row),
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
        if key in SYSTEM_KEYS:
            groups.append(_group(src, key, sheet_name, floors_obj=floors, keys=keys,
                                 qty=len(_clusters(items, _radius(sheet, units, notes=True))),
                                 label=label, ref=ref, items=items,
                                 reason="The drawing shows the system by a note or label, not by its panel: say how many "
                                        "systems / panels the fire alarm serves here"))
            continue
        if key in visual.KEYS:
            # looked at on the drawing: a label that is not a damper's set aside (with
            # what it is); each that is, a damper of its own, where the damper is
            seen_at, kept, pending = [], [], []
            for it in items:
                v = visual.verdict(src, it)
                if v is None:
                    pending.append(it)
                elif not v["damper"]:
                    equipment.append({**_item(src, it, key, keys, label, ref, sheet_name, 1), "radius": radius,
                                      "visual_reject": v.get("what") or "not a damper"})
                else:
                    at = v.get("at")
                    # A text insertion point is evidence of a label, never the equipment's
                    # physical location. A positive answer without a located symbol is held.
                    if not (isinstance(at, list) and len(at) == 2
                            and all(isinstance(n, (int, float)) for n in at)):
                        pending.append(it)
                        continue
                    collision = next((other for other in seen_at
                                      if visual.near(at, other, _METRE.get(units, 1.0))), None)
                    if collision is not None:
                        # Do not silently merge two labels. The visual association is ambiguous
                        # until a reread assigns distinct physical symbols (or confirms one).
                        pending.append(it)
                        continue
                    seen_at.append(at)
                    kept.append({**it, "label_anchor": [it["x"], it["y"]],
                                 "x": at[0], "y": at[1], "equipment_anchor": list(at),
                                 "confidence": detect.HIGH, "visual": True})
            if pending:
                groups.append(_group(src, key, sheet_name, floors_obj=floors, keys=keys, qty=None,
                                     label=label, ref=ref, items=pending,
                                     reason="The label was found, but its physical equipment symbol was not "
                                            "located unambiguously. Visually confirm each symbol; the label text "
                                            "position is not an equipment position."))
            items = kept
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
    if it.get("label_anchor") is not None:
        out["label_anchor"] = list(it["label_anchor"])
    if it.get("equipment_anchor") is not None:
        out["equipment_anchor"] = list(it["equipment_anchor"])
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


def _equipment_rows(equipment: list[dict], floors: Floors, conflicts: list[str], sched: Schedule) -> list[dict]:
    """A line per item per floor it stands for. One piece of equipment shown
    on several drawings is counted once: per floor and kind, the untagged
    items of the drawing that shows the most are counted -- the discipline's
    own drawing before the architecture on a tie -- and the other drawings
    are its evidence, said in one note."""
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
        if e["tag"]:
            continue
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
    winner = {kf: max(by, key=lambda sid: (by[sid], -_PRIORITY.get(source[sid]["src"]["discipline"], 9)))
              for kf, by in shown.items()}
    notes: dict[tuple, list[str]] = {}
    for kf, by in shown.items():
        if len(by) > 1:
            win = winner[kf]
            others = tuple(sorted(f"{source[sid]['label']} ({n})" for sid, n in by.items() if sid != win))
            notes.setdefault((kf[0], f"{source[win]['label']} ({by[win]})", others), []).append(kf[1])
    for e in equipment:
        if not e["tag"]:
            sid = f"{e['src']['discipline']}|{e['src']['relative_path']}"
            e["skip"] |= {k for k in e["keys"] if (e["key"], k) in winner and winner[(e["key"], k)] != sid}
    for (key, win, others), keys in notes.items():
        conflicts.append(f"{BY_KEY[key].name} on {', '.join(floors.name(k) for k in sorted(keys, key=floors.order))}: "
                         f"shown on several drawings, counted once from {win}; also on {', '.join(others)}.")
    rows = []
    for e in equipment:
        skipped = e["skip"]
        x, y = e["anchor"]
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
            # where it is drawn: the fire alarm drawing shares the trades' coordinates,
            # so the redesign puts its modules there
            rows[-1]["anchor"], rows[-1]["sheet"] = [round(x, 3), round(y, 3)], e["sheet"]
            if e.get("label_anchor") is not None:
                rows[-1]["label_anchor"] = [round(float(n), 3) for n in e["label_anchor"]]
            if e.get("equipment_anchor") is not None:
                rows[-1]["equipment_anchor"] = [round(float(n), 3) for n in e["equipment_anchor"]]
            if e.get("visual"):
                rows[-1]["evidence"] += "; seen on the drawing (AI visual check): a damper, here"
            if e.get("visual_reject"):
                rows[-1]["visual_reject"] = e["visual_reject"]
            if hit:
                rows[-1]["schedule"] = hit["where"]
    return rows


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


def received(db: Session, project: Project, row: ProjectFaInterfaces) -> list[dict]:
    """The drawings and schedules in the project's IFC folders now, as the
    folder sync sees them -- a stat each, nothing read -- each with its last
    reading while the file is unchanged, else "unread". A drawing is received
    when it is filed, not when a reading of it finished (EP-30880: a reading
    stopped on the dampers left every discipline "missing" with its drawings
    in the folder). The folder out of reach: the last reading's list."""
    saved = row.sources or []
    root = Path(project.source_folder_path) if project.source_folder_path else None
    if root is None or not os.path.isdir(document_control._os_path(root)):
        return saved
    found = discover(db, project)
    for path in SCH.discover(root):
        try:
            st = os.stat(path)
        except OSError:
            continue
        found.append({"discipline": SCHEDULE, "kind": "schedule", "relative_path": _relative(root, path),
                      "filename": path.name, "size": st.st_size, "mtime": st.st_mtime, "superseded": False})
    before = {(s.get("discipline"), s.get("relative_path")): s for s in saved}
    out = []
    for src in found:
        if src["superseded"]:
            out.append({**_public(src), "status": "superseded"})
            continue
        old = before.get((src["discipline"], src["relative_path"]))
        if (old and old.get("status") in ("read", "failed")
                and (old.get("size"), old.get("mtime")) == (src.get("size"), src.get("mtime"))):
            out.append({**old, **_public(src)})
        else:
            out.append({**_public(src), "status": "unread"})
    return out


def coverage(db: Session, project: Project, row: ProjectFaInterfaces) -> list[dict]:
    """Per discipline: whether its drawings were received (filed in its
    folder), whether any was read into the schedule, and each file with
    what reading it gave."""
    listed = received(db, project, row)
    out = []
    for d in DISCIPLINES:
        files = [s for s in listed if s.get("discipline") == d.code]
        out.append({
            "discipline": d.code, "name": DISCIPLINE_NAMES[d.code], "folder": d.folder, "purpose": d.purpose,
            "status": "available" if files else "missing",
            "read": any(f.get("status") == "read" for f in files),
            "files": [{"filename": f["filename"], "relative_path": f.get("relative_path"), "kind": f.get("kind"),
                       "revision": f.get("revision"), "status": f.get("status"), "error": f.get("error"),
                       "modified": datetime.fromtimestamp(f["mtime"]).isoformat() if f.get("mtime") else None,
                       "size": f.get("size"),
                       "sheets": len((f.get("result") or {}).get("sheets", [])),
                       "plans": sum(1 for s in (f.get("result") or {}).get("sheets", []) if _sheet_kind(s) == "plan"),
                       "items": len((f.get("result") or {}).get("items", [])),
                       "lifts": len({l["label"] for l in (f.get("result") or {}).get("lifts", [])})}
                      for f in files],
        })
    files = [s for s in listed if s.get("discipline") == SCHEDULE]
    out.append({
        "discipline": SCHEDULE, "name": "Equipment Schedules", "folder": f"{DRAWINGS}/IFC/Mechanical (Excel)",
        "purpose": "Schedules of fans, FAHU, AHU ...: the plans' fans and air handling units checked against them",
        "status": "available" if files else "missing",
        "read": any(f.get("status") == "read" for f in files),
        "files": [{"filename": f["filename"], "relative_path": f.get("relative_path"), "kind": "schedule", "revision": None,
                   "status": f.get("status"), "error": f.get("error"),
                   "modified": datetime.fromtimestamp(f["mtime"]).isoformat() if f.get("mtime") else None,
                   "size": f.get("size"), "sheets": len((f.get("result") or {}).get("items", [])), "plans": 0,
                   "items": sum(len(i["tags"]) for i in (f.get("result") or {}).get("items", [])), "lifts": 0}
                  for f in files]})
    out.append({"discipline": "MATRIX", "name": "Interface Matrix", "folder": None, "status": "available", "read": True,
                "purpose": f"{MATRIX_NAME}: {len(RULES)} rows" + (f"; rows {', '.join(map(str, UNCLEAR_ROWS))} not legible "
                                                                   "on the copy transcribed" if UNCLEAR_ROWS else ""),
                "files": []})
    # No Cause & Effect input: it is made from this schedule, not read into it.
    return out
