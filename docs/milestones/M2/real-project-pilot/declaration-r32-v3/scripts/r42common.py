"""ORCH-10 (R42PORT-IMPL): shared paths, constants, hashing and JSON writing for the corrected harness package
`PILOT/review42/` and the corrected declaration package `PILOT/declaration-r32-v3/` in the MERGED installation.

Nothing here writes outside the work folder C:/t/iso/work/r2x/r42, the two new packages, the session scratchpad or the
dry sandbox base C:/t/r2x/r42-sandbox. The AI ledger is only ever opened as file:...?mode=ro with uri=True. No provider,
model, network, CLI process or ledger scope is touched by this module. The installed claude.exe is only ever READ AS BYTES
(its sha256); it is never executed."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess

MERGED = pathlib.Path("G:/dev (2)/dev/ep-platform-merged")
EP = MERGED / "ep-platform"
PILOT = EP / "docs/milestones/M2/real-project-pilot"
M2 = EP / "docs/milestones/M2"
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
DESKTOP_EP = "C:/Users/moham/Desktop/dev/dev/ep-platform"          # the ABSENT installation the v2 bindings name
DESKTOP_PILOT = DESKTOP_EP + "/docs/milestones/M2/real-project-pilot"
MERGED_EP = EP.as_posix()                                         # "G:/dev (2)/dev/ep-platform-merged/ep-platform"
WORK = pathlib.Path("C:/t/iso/work/r2x/r42")
SANDBOX_BASE = pathlib.Path("C:/t/r2x/r42-sandbox")               # this task's dry sandboxes AND the declared live base
STAMP = "r32-v3"
RUN_FOLDER = SANDBOX_BASE / STAMP                                  # never created by this task
DECLARATION_DATE = "2026-10-06"                                    # the ORCH-10 issue date (owner's local date, +04)
SCOPE = f"m2-fresh-validation-r32-v3-{DECLARATION_DATE}"
AI_LEDGER = pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite")
RESPONSE_LEDGER = M2 / "M2-REVIEW-RESPONSE.md"
RESPONSE_BEFORE = ("1143c6856c9f55a0bb450b19f0ff43ba58f47af0593a3fc1e98f07a037d182e0", 219716)

# the bound interpreter (A-11 / ORCH-10 2.1.1): the merged installation's backend venv
PY = (EP / "backend/venv/Scripts/python.exe").as_posix()
VENV = (EP / "backend/venv").as_posix()
VENV_FREEZE_RECORD = MERGED / "merge/reports/merged-venv-freeze.txt"
DESKTOP_PY = DESKTOP_EP + "/backend/venv/Scripts/python.exe"

CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r29/backend")
BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")
CANDIDATE = ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d")
BASELINE = ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")
LEDGER_EXPECTED = {"entries": 483, "scopes": 17, "limit_amendments": 0}

# the frozen v2 package and its bound harness (byte-identical in the merged installation; never changed)
V2 = PILOT / "declaration-r32-v2"
V2_NAME = "FRESH-VALIDATION-DECLARATION-R32-V2.json"
V2_SHA = "f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af"
V2_MANIFEST_SHA = "6fa552ebd7561ed519e58a95c45ea6e2427cb0b13c94dc3739df4e868e0b6bfb"
REVIEW39 = PILOT / "review39"
HARNESS39 = REVIEW39 / "scripts" / "harness-r32"
BINDING39 = REVIEW39 / "BINDING-MANIFEST-R39.json"
BINDING39_SHA = "a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b"
REVIEW39_MANIFEST_SHA = "2430fa2bf6bcb5bf3775efe143575dcd9cdc55723ab994cfaec5f63fbdded990"
BOUNDS39 = REVIEW39 / "PROJECT-REQUEST-BOUNDS.json"
BOUNDS39_SHA = "99be01fbf25ed6e6219cc6b09b56aa9cd728ad9b30379e6b4b157aa394131721"

# the new packages
REVIEW42 = PILOT / "review42"
HARNESS42 = REVIEW42 / "scripts" / "harness-r32"
WORK_HARNESS = WORK / "harness-r32"
BINDING42 = REVIEW42 / "BINDING-MANIFEST-R42.json"
BOUNDS42 = REVIEW42 / "PROJECT-REQUEST-BOUNDS.json"
PACKAGE = PILOT / "declaration-r32-v3"
DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V3.json"
RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json"       # produced ONLY by the owner (fill_owner_digest), never here
AUTH_NAME = "OWNER-DISPATCH-AUTHORIZATION.json"                 # written ONLY by the owner, never here
TOKEN_ENV = "R34_OWNER_DISPATCH_TOKEN"
TOKEN_PLACEHOLDER = "TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION"
DUMMY_DIGEST = "0" * 63 + "1"        # in memory only; never written to disk, never a real token digest

RUN_SET = PILOT / "review34" / "RUN-SET-PROPOSAL.json"
RUN_SET_SHA = "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"
TRUTH = PILOT / "review34" / "dry-run" / "TRUTH-R32.json"
TRUTH_SHA = "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"
LABELS_SHA = "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"

CLI_EXE = pathlib.Path("C:/Users/moham/AppData/Local/Microsoft/WinGet/Packages/Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe/claude.exe")
CLI_EXE_SHA = "0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03"
CLI_EXE_BYTES = 218746016
CLI_VERSION_LINE = "2.1.263 (Claude Code)"
BUNDLED_CLI_NOT_USED = MERGED / "tools/claude-2.1.289/claude.exe"   # the merged installation's own FA-workflow CLI: NEVER used
MERGED_ENV_FILE = EP / "backend/.env"                              # NEVER read (existence only, by name)

MIN_FREE_BYTES = 2 * 1024 ** 3                                      # 2 GiB: the C1 disk precondition, configurable only upward

R40_WORK_RECORDS = {
    "C:/t/iso/work/r2x/r40/AUDIT-LOG.md": "5ff67138444b49f1b92f67355d289bf99b470917db52b94f41d246cf401bb09c",
    "C:/t/iso/work/r2x/r40/PROGRESS.md": "265ba73777540713826e02726d22246a3ce59048db823772ee2616137853b0c6",
    "C:/t/iso/work/r2x/r40/RESPONSE-APPEND-RECORD.json": "568d68173ac8d92b1611cd9a68752d5df159754e52a6ef1794bfa00a4c6d464e",
    "C:/t/iso/work/r2x/r40/FROZEN-INPUTS-FINAL.json": "8e5596cd2b55795ca1d079ec5c66429e61dca82a8c99d5bd9d467f4555d435c4",
}
POLICY = {"AI-ACCURACY-POLICY.md": "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47",
          "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md": "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6",
          "MASTER-ROADMAP.md": "f6dba0b2fce767955aed2b7508cfe7480637b02c44f502c3702c7862116e4c86"}
TASK_FILE = MR / "orchestrator/NEXT-BOUNDED-TASK.md"
TASK_FILE_SHA = "4ee96b8a42289c3c70f2f5075eb98dbfaeee3b119dae5a604107abd85fc59b89"


class PacketMismatch(RuntimeError):
    pass


LONG = "\\\\?\\"


def long_path(p) -> str:
    """The extended-length form of an absolute Windows path (LongPathsEnabled = 0: ordinary APIs fail at 260)."""
    s = os.path.abspath(str(p)).replace("/", "\\")
    return s if s.startswith(LONG) else LONG + s


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(long_path(path), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def json_text(obj) -> str:
    """The package JSON form (canonical): sort_keys, indent 1, ensure_ascii False, LF, one trailing newline."""
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def write_once(path, text: str) -> str:
    """Create a NEW file (O_EXCL; never overwrite) with LF line ends; return its sha256."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0))
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return sha256_bytes(data)


def write_json_once(path, obj) -> str:
    return write_once(path, json_text(obj))


def write_text(path, text: str) -> str:
    """(Re)write a work-folder or package output (LF); return its sha256."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    path.write_bytes(data)
    return sha256_bytes(data)


def write_json(path, obj) -> str:
    return write_text(path, json_text(obj))


def ledger_state(path=AI_LEDGER) -> dict:
    """The AI ledger, read-only (mode=ro, uri=True)."""
    con = sqlite3.connect(f"file:{pathlib.Path(path).as_posix()}?mode=ro", uri=True)
    try:
        scopes = [r[0] for r in con.execute("select scope from scopes order by scope")]
        return {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": len(scopes),
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "scope_names_sha256": sha256_bytes("|".join(scopes).encode("utf-8")), "scope_names": scopes}
    finally:
        con.close()


def ledger_counts(path=AI_LEDGER) -> dict:
    s = ledger_state(path)
    return {k: s[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")}


def git_state(repo: str) -> dict:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
    dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
    return {"repo": repo, "head": head, "clean": not dirty}


def free_bytes(path="C:/") -> int:
    import shutil
    return shutil.disk_usage(str(path)).free


def long_paths_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as k:
            return winreg.QueryValueEx(k, "LongPathsEnabled")[0]
    except OSError:
        return None


def forbidden_files(roots=(PILOT, MR, pathlib.Path("C:/t"))) -> list:
    """Every file named like an owner authorization, a runnable declaration or a token (names only; nothing opened)."""
    hits = []
    for root in roots:
        root = pathlib.Path(root)
        if not root.exists():
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "venv")]
            for f in files:
                low = f.lower()
                if "dispatch-authorization" in low or low.endswith(".run.json") or "owner-token" in low:
                    hits.append((pathlib.Path(dirpath) / f).as_posix())
    return sorted(hits)


def manifest_check(package: pathlib.Path) -> dict:
    """Every file listed in <package>/evidence/EVIDENCE-MANIFEST.json re-hashed (and the unlisted files named)."""
    man_path = package / "evidence" / "EVIDENCE-MANIFEST.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    files = man["files"]
    bad = [rel for rel, v in files.items() if sha256_file(package / rel) != v["sha256"]]
    on_disk = sorted(p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file())
    unlisted = [p for p in on_disk if p not in files]
    return {"package": package.as_posix(), "manifest_sha256": sha256_file(man_path), "entries": len(files), "equal": len(files) - len(bad),
            "differ": bad, "unlisted": unlisted}
