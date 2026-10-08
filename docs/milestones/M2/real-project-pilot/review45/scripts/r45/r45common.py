"""R43-42 (review45, new): shared paths and read-only helpers of the task's own scripts (snapshot, copy record, drivers,
manifest, self-check). Nothing here writes outside C:/t/r2x/r42-sandbox/r45p (the one work folder) except where a caller
names an output path. The AI ledger is opened only as file:...?mode=ro (uri=True). No provider, model, network or CLI.
These scripts are run only from byte copies under C:/t/r2x/r42-sandbox/r45p/run (recorded in evidence/RUN-COPY-R45.json)."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess

EP = pathlib.Path("G:/dev (2)/dev/ep-platform-merged/ep-platform")
PILOT = EP / "docs/milestones/M2/real-project-pilot"
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
PY = (EP / "backend/venv/Scripts/python.exe").as_posix()
SANDBOX_BASE = pathlib.Path("C:/t/r2x/r42-sandbox")
WORK = SANDBOX_BASE / "r45p"
RUN = WORK / "run"
REVIEW43 = PILOT / "review43"
REVIEW45 = PILOT / "review45"
BINDING43 = REVIEW43 / "BINDING-MANIFEST-R43-HARNESS.json"
BINDING43_SHA = "f35355aa8a8bca16803db3576fda8260a470915fee9c905b035f8d8bd9a374a7"
LOG = EP / "docs/R43-SESSION-LOG.md"
AI_LEDGER = pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite")
LEDGER_EXPECTED = {"entries": 484, "scopes": 18, "limit_amendments": 0}
PIP_FREEZE_SHA = "bd424a5c4692ab4c1f634705e59ded3784549a6f6c9072ffea9860fbf611bf7f"
V3_RUN_FOLDER = SANDBOX_BASE / "r32-v3"
V4_RUN_FOLDER = SANDBOX_BASE / "r32-v4"
OWNER_RECORDS = SANDBOX_BASE / "r32-v3-owner-records"
V4_SCOPE = "m2-fresh-validation-r32-v4-2026-10-08"
V3_SCOPE = "m2-fresh-validation-r32-v3-2026-10-06"
TREES = ("C:/t/iso/frozen-r12", "C:/t/iso/cand-r29", "C:/t/iso/frozen-r13", "C:/t/iso/cand-r30", "C:/t/iso/cand-r30n")
PROTECTED = {"review42": PILOT / "review42", "review43": REVIEW43, "declaration_r32": PILOT / "declaration-r32",
             "declaration_r32_v2": PILOT / "declaration-r32-v2", "declaration_r32_v3": PILOT / "declaration-r32-v3",
             "declaration_r32_v4": PILOT / "declaration-r32-v4", "r43_review_package": SANDBOX_BASE / "R43-REVIEW-PACKAGE",
             "owner_records": OWNER_RECORDS}
LONG = "\\\\?\\"


def long_path(p) -> str:
    s = str(pathlib.Path(p)).replace("/", "\\")
    return s if s.startswith(LONG) else LONG + s


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(long_path(p), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now_local() -> str:
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def write_json(path, obj):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")


def aggregate(root) -> dict:
    """sha256 over the sorted lines '<relative path>\\t<size>\\t<sha256>' (extended-length opens): one value per folder."""
    root = pathlib.Path(root)
    if not root.exists():
        return {"path": root.as_posix(), "exists": False}
    lines = []
    base = long_path(root)
    for dp, _ds, fs in os.walk(base):
        for f in fs:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, base).replace("\\", "/")
            lines.append(f"{rel}\t{os.path.getsize(full)}\t{sha256_file(full)}")
    lines.sort()
    return {"path": root.as_posix(), "exists": True, "files": len(lines), "sha256": sha256_bytes("\n".join(lines).encode("utf-8"))}


def stat_listing(root) -> dict:
    """A live run folder, by os.stat only (names, sizes, mtimes): no file is opened."""
    root = pathlib.Path(root)
    if not root.exists():
        return {"path": root.as_posix(), "exists": False}
    lines = []
    base = long_path(root)
    for dp, _ds, fs in os.walk(base):
        for f in fs:
            full = os.path.join(dp, f)
            st = os.stat(full)
            lines.append(f"{os.path.relpath(full, base).replace(chr(92), '/')}\t{st.st_size}\t{st.st_mtime_ns}")
    lines.sort()
    return {"path": root.as_posix(), "exists": True, "files": len(lines), "stat_sha256": sha256_bytes("\n".join(lines).encode("utf-8")),
            "method": "os.stat only (relative path, size, mtime_ns); no file opened"}


def ledger_state() -> dict:
    con = sqlite3.connect(f"file:{AI_LEDGER.as_posix()}?mode=ro", uri=True)
    try:
        c = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in ("entries", "scopes", "limit_amendments")}
        names = sorted(r[0] for r in con.execute("select scope from scopes"))
    finally:
        con.close()
    return c | {"scope_names_sha256": sha256_bytes("\n".join(names).encode("utf-8")), "v3_scope_present": V3_SCOPE in names,
                "v4_scope_present": V4_SCOPE in names, "opened": "file:...?mode=ro (uri=True)"}


def pip_freeze() -> dict:
    env = {**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_CACHE_DIR": "1", "PIP_NO_INPUT": "1"}
    r = subprocess.run([PY, "-B", "-m", "pip", "freeze"], capture_output=True, env=env)
    return {"sha256": sha256_bytes(r.stdout), "lines": len(r.stdout.splitlines()), "returncode": r.returncode,
            "equals_precondition": sha256_bytes(r.stdout) == PIP_FREEZE_SHA, "command": f'"{PY}" -B -m pip freeze'}


def tree_state(repo: str) -> dict:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    g = lambda *a: subprocess.run(["git", "--no-optional-locks", "-C", repo, *a], capture_output=True, text=True, env=env).stdout.strip()  # noqa: E731
    idx = g("rev-parse", "--path-format=absolute", "--git-path", "index")
    return {"repo": repo, "head": g("rev-parse", "HEAD"), "status_lines": len([x for x in g("status", "--porcelain").splitlines() if x.strip()]),
            "index_sha256": sha256_file(idx) if idx and os.path.isfile(idx) else None}


def free_bytes(drive="C:/") -> int:
    return shutil.disk_usage(drive).free


def folder_bytes(root) -> int:
    total = 0
    for dp, _ds, fs in os.walk(long_path(root)):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total


def clean_env(guard_dir, guard_log, roots: str, extra: dict | None = None) -> dict:
    """The environment of every guarded process of this task: AI_* / ANTHROPIC* / OPENAI* / CLAUDE* / owner-token /
    R38_SANDBOX_BASE variables removed, PWD / OLDPWD removed, the guard loaded through PYTHONPATH, TEMP inside the work folder."""
    strip = ("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER", "R36_OWNER", "R38_SANDBOX_BASE", "R42_GUARD_ALLOW_EXTRA", "R43_GUARD", "R43_HARNESS_RUN")
    env = {k: v for k, v in os.environ.items() if not k.startswith(strip) and k.upper() not in ("PWD", "OLDPWD")}
    tmp = WORK / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(guard_dir), "TEMP": str(tmp), "TMP": str(tmp),
            "TMPDIR": str(tmp), "GIT_OPTIONAL_LOCKS": "0", "R43_GUARD_ROOTS": roots, "R43_GUARD_LOG": str(guard_log)}
    env |= extra or {}
    return env
