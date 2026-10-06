"""ORCH-05.1 (Review 33 C-5): build an isolated B sandbox and register staged files WITHOUT processing.

ingest(root, pool_ids, truth) -- root must be a NEW folder under C:/t/r2x/r33-sandbox/ (never reused):
  1. stage: each staged file C:/t/r2x/r32-stage/files/<pool id>.pdf is copied to root/s/EP-<ep>/<relative path> (the
     relative path is a KEY that the application indexes; it is never label evidence); its sha256 is checked against
     SOURCE-MANIFEST before and after the copy;
  2. registration: sandbox_child_r32.py runs inside the frozen baseline tree (B's code) with every root in the sandbox,
     AI disabled and a refusing provider: schema by the application's upgrade_to_head, one project per EP number, one
     PENDING index row per staged file (document_sync.listing; nothing opened, hashed or read);
  3. checks (read-only): rows = files, every row PENDING with no hash, no reading, no record; no ai_usage, no
     document_readings, no background job, no result_cache row; then the B file sha256 is recorded, a C copy is made
     with the sqlite backup API and state_check.check_c_start must pass on it.
Never touches backend/ep_platform.db, a live service, OneDrive, the AI ledger or the staging area (read-only).
ORCH-08C (R39-04): sandbox_env() also sets APPLICATION_ENV -- the declared non-AI_* application settings; today exactly
DRAWINGS_AI_REVIEW_ENABLED=false, so the baseline's drawings-AI review (document_processing.run -> shop_drawings.reconcile
-> drawing_ai_review) is off in every application process the harness starts (lanes, ingestion child, scoring). This is
the only change to this module since review33 (the run's declaration binds the same allowlist; every lane verifies it).
ORCH-10 (R42, portability): PY is the bound interpreter of the MERGED installation (the Desktop venv is absent; the live
declaration binds this path, its sha256 and its version, and the preflight refuses any other interpreter); sandbox_env
also drops the shell's bookkeeping variables PWD / OLDPWD (a shell started in the merged installation would otherwise hand
its folder to every application process; preflight_r32.verify_isolation refuses any other value under the merged root)."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess

import state_check

PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"
SHELL_BOOKKEEPING = ("PWD", "OLDPWD")
SANDBOX_BASE = pathlib.Path("C:/t/r2x/r33-sandbox")
STAGE_FILES = pathlib.Path("C:/t/r2x/r32-stage/files")
BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")
HERE = pathlib.Path(__file__).resolve().parent
LONG = "\\\\?\\"
C_MARKERS = ["identity-role-guard-2026-10-02.2", "conflict-adjudication-2026-10-02.2", "decision-region-2026-10-02.1", "page-association-2026-10-02.1"]
APPLICATION_ENV = {"DRAWINGS_AI_REVIEW_ENABLED": "false"}       # ORCH-08C: preflight_r32.APPLICATION_ENV (contract 4) is this
EVIDENCE_TASKS = ["discover_page", "read_identity", "read_revision", "read_decision", "read_field_context"]


def _long(p) -> str:
    s = str(pathlib.Path(p)).replace("/", "\\")
    return s if s.startswith(LONG) else LONG + s


def sha256_long(p) -> str:
    h = hashlib.sha256()
    with open(_long(p), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sandbox_env(root: pathlib.Path, *, ai_enabled: bool = False, extra: dict | None = None) -> dict:
    """The environment of an application process confined to the sandbox (no ledger, no data root, no autodetection;
    temporary files in <root>/tmp)."""
    os.makedirs(root / "tmp", exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AI_", "DATABASE_", "DATA_ROOT", "PROJECTS_ROOT", "CACHE_ROOT",
                                                                     "LIBRARY_ROOT", "UPLOADS_ROOT", "COMPLIANCE_", "DATASHEET_"))
           and k.upper() not in SHELL_BOOKKEEPING}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "DATABASE_URL": f"sqlite:///{(root / 'db' / 'default.db').as_posix()}",
                "CACHE_ROOT": str(root / "cache"), "LIBRARY_ROOT": str(root / "lib"), "UPLOADS_ROOT": str(root / "up"), "DATA_ROOT": "",
                "AI_ENABLED": "true" if ai_enabled else "false", "AI_PROVIDER": "r33-none", "AI_LEDGER_PATH": "", "AI_EVIDENCE_VARIANT": "off",
                "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
                "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}",
                "ARCHIVE_SUBMITTAL_LIBRARY": "", "LIBRARY_RESCAN_SECONDS": "0", "SYNC_FILE_WORKERS": "0", "DOCUMENT_CLASSIFICATION_V2": "false",
                "EXTRACTION_PROMOTE_OBSERVATIONS": "false", "TEMP": str(root / "tmp"), "TMP": str(root / "tmp")})
    env.update(APPLICATION_ENV)
    env.update(extra or {})
    return env


def stage(root: pathlib.Path, pool_ids, truth, stage_files=STAGE_FILES) -> dict:
    out = {}
    for pid in pool_ids:
        d = truth["documents"][pid]
        src = pathlib.Path(stage_files) / f"{pid}.pdf"
        before = sha256_long(src)
        if before != d["staged_sha256"]:
            raise RuntimeError(f"PACKET MISMATCH: staged {pid} {before} != {d['staged_sha256']}")
        dst = root / "s" / f"EP-{d['ep']}" / pathlib.PurePosixPath(d["relative_path"])
        os.makedirs(_long(dst.parent), exist_ok=True)
        if os.path.exists(_long(dst)):
            raise RuntimeError(f"two pool documents map to one sandbox path: {dst}")
        shutil.copyfile(_long(src), _long(dst))
        after = sha256_long(dst)
        if after != before:
            raise RuntimeError(f"copy of {pid} changed its bytes")
        out[pid] = {"ep": d["ep"], "doc_key": d["doc_key"], "sandbox_path": str(dst), "sha256": after}
    return out


def _ro(path):
    con = sqlite3.connect(f"file:{pathlib.Path(path).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def check_registration(db_path, staged: dict) -> dict:
    con = _ro(db_path)
    try:
        tables = {r[0] for r in con.execute("select name from sqlite_master where type = 'table'")}
        rows = [dict(r) for r in con.execute("select d.id, p.ep_number, d.relative_path, d.state, d.sha256, d.extracted, d.reference, "
                                             "d.revision, d.status, d.reading_id, d.role from project_documents d join projects p on p.id = d.project_id")]
        counts = {t: con.execute(f'select count(*) from "{t}"').fetchone()[0] for t in
                  ("ai_usage", "document_readings", "background_jobs", "result_cache", "extraction_runs", "project_submittals") if t in tables}
    finally:
        con.close()
    keys = {f"EP-{r['ep_number']}/{r['relative_path']}" for r in rows}
    want = {v["doc_key"] for v in staged.values()}
    problems = []
    if keys != want:
        problems.append(f"registered keys differ: missing {sorted(want - keys)[:5]}, extra {sorted(keys - want)[:5]}")
    for r in rows:
        if r["state"] != "pending" or r["sha256"] or r["extracted"] or r["reference"] or r["revision"] or r["status"] or r["reading_id"]:
            problems.append(f"row {r['id']} is not a bare pending registration")
    for t, n in counts.items():
        if n:
            problems.append(f"{t} has {n} row(s): something was processed")
    return {"ok": not problems, "rows": len(rows), "by_state": dict(__import__("collections").Counter(r["state"] for r in rows)),
            "by_project": dict(__import__("collections").Counter(r["ep_number"] for r in rows)), "table_counts": counts, "problems": problems}


def c_copy(b_db, c_db):
    os.makedirs(pathlib.Path(c_db).parent, exist_ok=True)
    src = sqlite3.connect(f"file:{pathlib.Path(b_db).as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(str(c_db))
    src.backup(dst)
    dst.close()
    src.close()


def ingest(root, pool_ids, truth, *, python=PY, stage_files=STAGE_FILES) -> dict:
    root = pathlib.Path(root)
    if not root.is_absolute() or not root.as_posix().startswith(SANDBOX_BASE.as_posix() + "/"):
        raise RuntimeError(f"a sandbox lives under {SANDBOX_BASE}: {root}")
    if root.exists():
        raise RuntimeError(f"{root} exists: a sandbox is never reused")
    for d in ("db", "cache", "lib", "up", "out", "s"):
        (root / d).mkdir(parents=True)
    t0 = datetime.datetime.now(datetime.timezone.utc)
    staged = stage(root, list(pool_ids), truth, stage_files)
    projects = {}
    for v in staged.values():
        projects[v["ep"]] = str(root / "s" / f"EP-{v['ep']}")
    pj = root / "out" / "PROJECTS.json"
    pj.write_text(json.dumps(projects, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    log = root / "out" / "ingest-child.log"
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([python, str(HERE / "sandbox_child_r32.py"), str(root), str(pj)], cwd=str(BASELINE_BACKEND),
                           env=sandbox_env(root), stdout=fh, stderr=subprocess.STDOUT)
    if r.returncode:
        raise RuntimeError(f"ingestion child failed ({r.returncode}); see {log}")
    db = root / "db" / "default.db"
    reg = check_registration(db, staged)
    b_sha = state_check.file_sha256(db)
    c_db = root / "c-check" / "default.db"
    c_copy(db, c_db)
    sc = state_check.check_c_start(db, b_sha, c_db, C_MARKERS, EVIDENCE_TASKS)
    report = {"root": str(root), "started_utc": t0.isoformat(timespec="seconds"), "documents": len(staged), "projects": sorted(projects),
              "staged": staged, "registration": reg, "b_database_sha256": b_sha, "state_check": sc,
              "baseline_tree": str(BASELINE_BACKEND), "model_requests": 0, "processing_run": False,
              "ok": reg["ok"] and sc["ok"]}
    (root / "out" / "INGEST-REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    return report
