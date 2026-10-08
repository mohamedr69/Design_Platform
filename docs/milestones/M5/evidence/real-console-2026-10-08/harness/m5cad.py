"""ORCH-046 harness: the merged M5 Apply code (a byte copy of roadmap/u2 at
37350bc) run against the DWG TrueView 2026 Core Console on an isolated copy
of GC-01, an isolated SQLite database and isolated uploads/archive folders.

Nothing here edits application code. What the harness sets, and why:
  * environment: database, uploads, cache, library, TEMP, AI off (as the
    suite's conftest does), and BOQ_ACCORECONSOLE -> the TrueView console;
  * cad._command (the code's own "seam for tests") is wrapped to APPEND
    `/isolate m5cad <profile>` -- the dedicated console profile OD-16 (c)
    requires; the code's own arguments are kept as they are;
  * R.readiness -> ready and R._units -> 1.0, exactly as the suite's `gc`
    fixture does: the isolated database has no drawing review to be ready
    against (readiness itself is not under test here).
No stand-in console, no stand-in read-back: convert.convert_dwg_to_dxf and
cad.run are the code's own and run the real console.

usage: python -B m5cad.py <step> [args]   (cwd: anywhere)
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\t\tmp\m5cad")
CODE = ROOT / "code" / "ep platform (m5 copy)" / "backend"
DB = ROOT / "db" / "m5cad.db"
UPLOADS = ROOT / "uploads"
ARCHIVE = ROOT / "archive"
PROFILE = ROOT / "profile"
RESULTS = ROOT / "results"
SRC_COPY = ROOT / "src" / "GC-01-copy.dwg"
LIVE_SOURCE = Path(r"G:\dev (2)\dev\ep-platform-merged\data\uploads\EP-30880\ifc\60de2a377daa.dwg")
EXE = r"C:\Program Files\Autodesk\DWG TrueView 2026 - English\accoreconsole.exe"
EP = "90880"                               # an isolated project number, not EP-30880
SRC_NAME = "60de2a377daa"

os.environ.update({
    "DATABASE_URL": "sqlite:///" + DB.as_posix(),
    "UPLOADS_ROOT": str(UPLOADS),
    "DATA_ROOT": "",
    "CACHE_ROOT": str(ROOT / "cache"),
    "LIBRARY_ROOT": str(ROOT / "emptylib"),
    "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
    "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "",
    "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
    "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DOCUMENT_CLASSIFICATION_V2": "false",
    "AI_ENABLED": "false", "FA_AI_ENABLED": "false", "PREP_AI_ENABLED": "false",
    "DRAWING_REVIEW_AI_ENABLED": "false", "SYNC_FILE_WORKERS": "0",
    "BOQ_ACCORECONSOLE": EXE, "ACCORECONSOLE_PATH": EXE,
    "TEMP": str(ROOT / "tmp"), "TMP": str(ROOT / "tmp"),
})
for d in (ROOT / "cache", ROOT / "emptylib", ROOT / "tmp", RESULTS, UPLOADS, ARCHIVE, DB.parent):
    d.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CODE))
os.chdir(CODE)

import psutil  # noqa: E402

from app.core.timeutils import utc_now  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app import models as M  # noqa: E402
from app.ifc.dxf import convert  # noqa: E402
from app.redesign import cad  # noqa: E402
from app.redesign import service as R  # noqa: E402
from app.redesign import verify as V  # noqa: E402
from app.services import jobs  # noqa: E402

COMMANDS: list[list[str]] = []
_orig_command = cad._command


def _isolated(converter, copy, script):
    cmd = _orig_command(converter, copy, script) + ["/isolate", "m5cad", str(PROFILE)]
    COMMANDS.append({"code_command": _orig_command(converter, copy, script), "issued": cmd})
    return cmd


cad._command = _isolated
R.readiness = lambda db, project, drawing, row: {"ready": True, "blockers": []}
R._units = lambda drawing, db: 1.0


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tree(folder: Path) -> list[dict]:
    out = []
    if folder.is_dir():
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                out.append({"path": p.relative_to(folder).as_posix(), "bytes": p.stat().st_size,
                            "sha256": sha(p) if p.stat().st_size < 50_000_000 else None})
    return out


def consoles() -> list[dict]:
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline", "ppid"]):
        try:
            if (p.info["name"] or "").lower() == "accoreconsole.exe":
                out.append({"pid": p.info["pid"], "ppid": p.info["ppid"], "cmdline": p.info["cmdline"]})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return out


def write(name: str, data: dict) -> None:
    (RESULTS / f"{name}.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    print(json.dumps(data, indent=1, default=str)[:6000])


# --- seed --------------------------------------------------------------------------------

def changes_for(entities: dict) -> list[dict]:
    """The redesign's changes, from real GC-01 entities read by the console (LIST)."""
    erase = entities["erase"]           # {handle, block, x, y}
    add = entities["add"]               # {block, x, y}: a block the drawing has, at a free point
    office = "C:/Users/someone-else/OneDrive - Org/Desktop/dev/ep-platform/backend/app/redesign/library"
    base = {"page": 0, "sheet": "GC-01", "floor": "GF", "room": "Isolated run", "candidates": [], "moved": True,
            "edited": False, "residual": 0.0, "confidence": "medium"}
    r_add = {**base, "id": "r1", "system": "detection", "system_name": "Detection", "action": "add",
             "device": add["block"], "instruction": "Add (M5 real-console run)", "status": "approved", "remove": None,
             "insert": {"block": add["block"], "layer": add.get("layer") or "0", "scale": 1.0, "rotation": 0.0,
                        "model": [add["x"], add["y"]], "seen": [add["x"], add["y"]], "placed": [add["x"], add["y"]],
                        "offset": [0, 0]}}
    r_rm = {**base, "id": "rm", "system": "detection", "system_name": "Detection", "action": "remove",
            "device": erase["block"], "instruction": "Remove (M5 real-console run)", "status": "approved",
            "insert": None, "moved": False,
            "candidates": [{"n": 1, "handle": erase["handle"], "block": erase["block"],
                            "insert_point": [erase["x"], erase["y"]], "page": [0, 0],
                            "model": [erase["x"], erase["y"]], "erasable": True}],
            "remove": {"n": 1, "handle": erase["handle"], "block": erase["block"], "name": erase["block"],
                       "page": [0, 0], "model": [erase["x"], erase["y"]], "erasable": True}}
    mx, my = add["x"] + 3.0, add["y"]
    m1 = {**base, "id": "m1", "system": "interface", "system_name": "FA Interfaces", "action": "add",
          "device": "CR module", "instruction": "CR FOR PUMP", "status": "approved", "source": "interface",
          "remove": None, "edited": True,
          "interface": {"code": "CR", "for": "PUMP", "note_height": 0.3, "half": 0.2, "depth": 0.1},
          "insert": {"block": "CR", "layer": "0", "scale": 0.00175, "rotation": 90.0, "model": [mx, my],
                     "seen": [mx, my], "placed": [mx, my], "offset": [0, 0], "library": f"{office}/CR.dwg",
                     "symbol": 800002}}
    px, py = add["x"] + 6.0, add["y"]
    p1 = {**r_add, "id": "p1", "status": "proposed", "instruction": "PROPOSED-ONLY-MUST-NOT-BE-DRAWN",
          "insert": {**r_add["insert"], "model": [px, py], "seen": [px, py], "placed": [px, py]}}
    other = entities["skip"]
    s1 = {**r_rm, "id": "s1", "status": "skipped", "confidence": "low",
          "candidates": [{**r_rm["candidates"][0], "handle": other["handle"], "insert_point": [other["x"], other["y"]]}],
          "remove": {**r_rm["remove"], "handle": other["handle"], "model": [other["x"], other["y"]]}}
    return [r_add, r_rm, m1, p1, s1]


def seed(entities_file: str) -> None:
    entities = json.loads(Path(entities_file).read_text(encoding="utf-8"))
    if DB.exists():
        raise SystemExit("database exists: seed once")
    Base.metadata.create_all(engine)
    ifc = UPLOADS / f"EP-{EP}" / "ifc"
    ifc.mkdir(parents=True, exist_ok=True)
    src = ifc / f"{SRC_NAME}.dwg"
    shutil.copyfile(SRC_COPY, src)
    db = SessionLocal()
    user = M.User(email="m5cad@isolated.invalid", full_name="M5 isolated run", hashed_password="!unusable",
                  role=M.RoleEnum.admin)
    db.add(user)
    db.commit()
    project = M.Project(ep_number=EP, project_name="GC-01 isolated copy (ORCH-046)", created_by_id=user.id,
                        source_folder_path=str(ARCHIVE / f"EP-{EP} project folder"))
    db.add(project)
    db.commit()
    drawing = M.ProjectIfcDrawing(project_id=project.id, filename="GC-01 FA LAYOUT.dwg",
                                  stored_path=f"EP-{EP}/ifc/{SRC_NAME}.dxf", revision="R0", meta={}, groups=[])
    db.add(drawing)
    db.commit()
    row = M.ProjectRedesign(project_id=project.id, drawing_id=drawing.id, status="planned", source_sha256=sha(src),
                            changes=changes_for(entities), symbols=[])
    db.add(row)
    db.commit()
    write("seed", {"at": now(), "db": str(DB), "user_id": user.id, "project_id": project.id, "ep": EP,
                   "drawing_id": drawing.id, "row_id": row.id, "source_in_uploads": str(src),
                   "source_sha256": sha(src), "changes": row.changes,
                   "drawn": [c["id"] for c in row.changes if R._drawn(c)],
                   "not_drawn": [c["id"] for c in row.changes if not R._drawn(c)]})


def seed_earlier_copy() -> None:
    """An earlier 'made' copy for the 'stays downloadable' check: a BYTE COPY of the
    unchanged GC-01 copy under an output-style name -- NOT an Apply result (this
    console cannot make one). Recorded as such."""
    db = SessionLocal()
    row = db.query(M.ProjectRedesign).one()
    drawing = db.get(M.ProjectIfcDrawing, row.drawing_id)
    folder = (UPLOADS / f"EP-{EP}" / "redesign").resolve()
    folder.mkdir(parents=True, exist_ok=True)
    dest = R._unique_output(folder, drawing, row.source_sha256, "j0-0000000000")
    shutil.copyfile(SRC_COPY, dest)
    row.output_status, row.output_path = "made", dest.relative_to(UPLOADS.resolve()).as_posix()
    row.output_at, row.output_changes = utc_now(), 0
    db.commit()
    write("seed-earlier-copy", {"at": now(), "file": dest.name, "sha256": sha(dest),
                                "note": "byte copy of the unchanged GC-01 copy, seeded; not made by Apply",
                                "row": {"output_status": row.output_status, "output_path": row.output_path,
                                        "output_at": row.output_at}})


# --- one Apply ---------------------------------------------------------------------------

def _job(db, project, drawing, request) -> M.BackgroundJob:
    job = M.BackgroundJob(project_id=project.id, kind=R.KIND_APPLY, status="running",
                          params={"drawing_id": drawing.id, **request}, started_at=utc_now())
    db.add(job)
    db.commit()
    return job


def _row_state(row) -> dict:
    return {k: getattr(row, k) for k in ("output_status", "output_error", "output_path", "output_relative",
                                         "output_at", "output_changes")}


def apply_once(name: str, *, on_check=None, expect_cancel: bool = False) -> dict:
    db = SessionLocal()
    row = db.query(M.ProjectRedesign).one()
    project = db.get(M.Project, row.project_id)
    drawing = db.get(M.ProjectIfcDrawing, row.drawing_id)
    redesign = UPLOADS / f"EP-{EP}" / "redesign"
    before = {"row": _row_state(row), "redesign_tree": tree(redesign), "archive_tree": tree(ARCHIVE),
              "live_source_sha256": sha(LIVE_SOURCE), "source_copy_sha256": sha(SRC_COPY),
              "consoles": consoles(), "last_output": str(R.last_output(row, project))}
    request = R.apply_request(db, project, drawing)
    job = _job(db, project, drawing, request)
    seen: dict = {"checks": 0, "events": []}

    def check():
        seen["checks"] += 1
        if on_check:
            on_check(seen)

    t0 = time.monotonic()
    outcome: dict = {}
    try:
        result = R.apply(db, project, drawing.id, None, check=check, request=request, job_id=job.id,
                         job_created_at=job.created_at)
        outcome = {"raised": None, "result": result}
        job.status, job.result = "succeeded", result
    except BaseException as exc:  # noqa: BLE001
        outcome = {"raised": type(exc).__name__, "message": str(exc),
                   "traceback": traceback.format_exc().splitlines()[-6:]}
        db.rollback()
        job = db.get(M.BackgroundJob, job.id)
        job.status = "cancelled" if isinstance(exc, jobs.Cancelled) else "failed"
        job.error = str(exc)[:1000]
    job.finished_at = utc_now()
    db.commit()
    seconds = round(time.monotonic() - t0, 2)
    db.expire_all()
    row = db.query(M.ProjectRedesign).one()
    runs = sorted((redesign / R.RUNS).iterdir(), key=lambda p: p.stat().st_mtime) if (redesign / R.RUNS).is_dir() else []
    run_dir = runs[-1] if runs else None
    run_info: dict = {}
    if run_dir is not None:
        log_path = run_dir / "autocad.log"
        script = run_dir / "redesign.scr"
        text = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
        nonce = None
        if script.is_file():
            import re
            m = re.search(r'\(setq ep_nonce "([0-9a-f]+)"', script.read_text(encoding="utf-8"))
            nonce = m.group(1) if m else None
        run_info = {"run_dir": run_dir.name, "files": tree(run_dir),
                    "parse_log": V.parse_log(text, nonce) if nonce else None, "nonce": nonce,
                    "log_lines_after_open": [l for l in text.splitlines() if l.strip()
                                             and "CoreHeartBeat" not in l][-12:],
                    "verification": json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
                    if (run_dir / "verification.json").is_file() else None}
    after = {"row": _row_state(row), "redesign_tree": tree(redesign), "archive_tree": tree(ARCHIVE),
             "live_source_sha256": sha(LIVE_SOURCE), "source_copy_sha256": sha(SRC_COPY),
             "uploads_source_sha256": sha(UPLOADS / f"EP-{EP}" / "ifc" / f"{SRC_NAME}.dwg"),
             "consoles": consoles(), "last_output": str(R.last_output(row, project)),
             "final_named_outputs": sorted(p.name for p in redesign.glob("*.dwg") if R.OUTPUT_NAME.search(p.name)),
             "parts": sorted(p.relative_to(UPLOADS).as_posix() for p in UPLOADS.rglob("*.part")),
             "view_available": None}
    try:
        v = R.view(db, project, drawing.id)
        after["view_output"] = {k: v.get(k) for k in ("available", "output", "published", "filed_earlier")
                                if k in v}
        after["view_keys"] = sorted(v)
    except Exception as exc:  # noqa: BLE001
        after["view_error"] = repr(exc)
    data = {"name": name, "at": now(), "seconds": seconds, "job_id": job.id, "job_status": job.status,
            "request": request, "commands": COMMANDS[-1:] if COMMANDS else [], "outcome": outcome,
            "checks_called": seen["checks"], "events": seen["events"], "before": before, "run": run_info,
            "after": after}
    write(name, data)
    return data


def step_apply() -> None:
    apply_once("s1-apply-approved-set")


def step_missing_block() -> None:
    lib = CODE / "app" / "redesign" / "library"
    cr, hidden = lib / "CR.dwg", lib / "CR.dwg.hidden-for-m5cad"
    h0 = sha(cr)
    os.rename(cr, hidden)
    try:
        apply_once("s2-missing-library-block")
    finally:
        os.rename(hidden, cr)
    assert sha(cr) == h0
    print("CR.dwg restored", h0)


def _find_console(run_root: Path) -> list[dict]:
    return [c for c in consoles() if any(str(run_root) in (a or "") for a in (c["cmdline"] or []))]


def step_cancel() -> None:
    run_root = (UPLOADS / f"EP-{EP}" / "redesign" / R.RUNS).resolve()

    def on_check(seen):
        live = _find_console(run_root)
        if live and seen.get("cancel_at") is None and seen["checks"] >= 2:
            seen["cancel_at"] = seen["checks"]
            seen["events"].append({"at": now(), "check": seen["checks"], "console_alive": live,
                                   "action": "raise jobs.Cancelled (the engineer's cancel)"})
            seen["killed_pids"] = [c["pid"] for c in live]
            raise jobs.Cancelled("Cancelled by the M5 real-console run (ORCH-046)")

    data = apply_once("s3-cancel-mid-run", on_check=on_check)
    time.sleep(2)
    pids = [e["console_alive"][0]["pid"] for e in data["events"] if e.get("console_alive")]
    extra = {"console_pids_at_cancel": pids, "alive_2s_after": [p for p in pids if psutil.pid_exists(p)]}
    write("s3-cancel-mid-run-pids", extra)


def step_external_kill() -> None:
    run_root = (UPLOADS / f"EP-{EP}" / "redesign" / R.RUNS).resolve()

    def on_check(seen):
        live = _find_console(run_root)
        if live and seen.get("killed") is None and seen["checks"] >= 2:
            seen["killed"] = True
            pid = live[0]["pid"]
            r = subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, text=True)
            seen["events"].append({"at": now(), "check": seen["checks"], "console_alive": live,
                                   "action": f"taskkill /F /PID {pid}", "taskkill": (r.returncode, r.stdout.strip(),
                                                                                    r.stderr.strip())})

    apply_once("s4-console-killed-externally", on_check=on_check)


def step_worker_child() -> None:
    """Run in a child process; killed hard by step_kill_worker while the console runs."""
    apply_once("s5-worker-child-never-finishes")


PARENT = "--parent" in sys.argv


def step_kill_worker() -> None:
    run_root = (UPLOADS / f"EP-{EP}" / "redesign" / R.RUNS).resolve()
    child = subprocess.Popen([sys.executable, "-B", __file__, "worker-child"], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    events = []
    t0 = time.monotonic()
    console = []
    while time.monotonic() - t0 < 120:
        console = _find_console(run_root)
        if console:
            break
        time.sleep(0.2)
    events.append({"at": now(), "worker_pid": child.pid, "console_seen": console})
    target = console[0]["ppid"] if (console and PARENT) else child.pid
    if console:
        time.sleep(1.0)
        events.append({"at": now(), "target_pid": target, "target_alive": psutil.pid_exists(target),
                       "target_name": psutil.Process(target).name() if psutil.pid_exists(target) else None,
                       "launcher_pid": child.pid})
        r = subprocess.run(["taskkill", "/F", "/PID", str(target)], capture_output=True, text=True)
        events.append({"at": now(), "action": f"taskkill /F /PID {target} (the worker, not its tree)",
                       "taskkill": (r.returncode, r.stdout.strip(), r.stderr.strip()),
                       "console_parent_alive_after": psutil.pid_exists(console[0]["ppid"])})
    child.wait(timeout=30)
    time.sleep(0.5)
    pids = [c["pid"] for c in console]
    events.append({"at": now(), "worker_exit": child.returncode,
                   "console_alive_after_worker_kill": [p for p in pids if psutil.pid_exists(p)]})
    # wait for an orphaned console to end by itself (it runs its script to the end), at most 120 s
    t1 = time.monotonic()
    while any(psutil.pid_exists(p) for p in pids) and time.monotonic() - t1 < 120:
        time.sleep(0.5)
    events.append({"at": now(), "console_alive_after_wait": [p for p in pids if psutil.pid_exists(p)],
                   "waited_s": round(time.monotonic() - t1, 1)})
    db = SessionLocal()
    row = db.query(M.ProjectRedesign).one()
    redesign = UPLOADS / f"EP-{EP}" / "redesign"
    runs = sorted((redesign / R.RUNS).iterdir(), key=lambda p: p.stat().st_mtime)
    job = db.query(M.BackgroundJob).order_by(M.BackgroundJob.id.desc()).first()
    write("s5b-worker-interpreter-killed" if PARENT else "s5-worker-killed", {"events": events, "row": _row_state(row), "job": {"id": job.id, "status": job.status},
                               "last_run_dir": runs[-1].name, "last_run_files": tree(runs[-1]),
                               "final_named_outputs": sorted(p.name for p in redesign.glob("*.dwg")
                                                             if R.OUTPUT_NAME.search(p.name)),
                               "parts": sorted(p.relative_to(UPLOADS).as_posix() for p in UPLOADS.rglob("*.part")),
                               "live_source_sha256": sha(LIVE_SOURCE), "consoles": consoles()})


def step_sweep() -> None:
    db = SessionLocal()
    # a worker would mark the killed job interrupted at recovery; until then the sweep skips the project
    active = db.query(M.BackgroundJob).filter(M.BackgroundJob.status.in_(jobs.ACTIVE)).all()
    before = tree(UPLOADS / f"EP-{EP}" / "redesign")
    first = R.sweep_orphans(db, older_than_s=0)
    for j in active:
        j.status, j.error, j.finished_at = "interrupted", "worker killed by the M5 real-console run", utc_now()
    db.commit()
    second = R.sweep_orphans(db, older_than_s=0)
    write("s6-sweep", {"at": now(), "active_jobs_before": [(j.id, "running") for j in active],
                       "sweep_with_active_job": first, "sweep_after_jobs_ended": second,
                       "before": before, "after": tree(UPLOADS / f"EP-{EP}" / "redesign")})


def step_publish_refused() -> None:
    db = SessionLocal()
    row = db.query(M.ProjectRedesign).one()
    project = db.get(M.Project, row.project_id)
    user = db.query(M.User).one()
    out = {}
    try:
        out["result"] = R.publish(db, project, row.drawing_id, user)
    except Exception as exc:  # noqa: BLE001
        out["raised"] = type(exc).__name__
        out["message"] = str(exc)
        out["status"] = getattr(exc, "status", None)
    out["archive_tree"] = tree(ARCHIVE)
    out["staging"] = tree(UPLOADS / f"EP-{EP}" / "redesign" / R.PUBLISHING)
    write("s7-publish-of-unverified-copy", out)


STEPS = {"seed": lambda: seed(sys.argv[2]), "seed-earlier-copy": seed_earlier_copy, "apply": step_apply,
         "missing-block": step_missing_block, "cancel": step_cancel, "external-kill": step_external_kill,
         "worker-child": step_worker_child, "kill-worker": step_kill_worker, "sweep": step_sweep,
         "publish-refused": step_publish_refused}

if __name__ == "__main__":
    STEPS[sys.argv[1]]()
