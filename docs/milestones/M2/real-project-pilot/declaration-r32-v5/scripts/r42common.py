"""ORCH-10 (R42PORT-IMPL): shared paths, constants, hashing and JSON writing for the corrected harness package
`PILOT/review42/` and the corrected declaration package `PILOT/declaration-r32-v3/` in the MERGED installation.

Nothing here writes outside the work folder C:/t/iso/work/r2x/r42, the two new packages, the session scratchpad or the
dry sandbox base C:/t/r2x/r42-sandbox. The AI ledger is only ever opened as file:...?mode=ro with uri=True. No provider,
model, network, CLI process or ledger scope is touched by this module. The installed claude.exe is only ever READ AS BYTES
(its sha256); it is never executed.
R43-44 (declaration-r32-v5): the work folder r45q, the stamp r32-v5 and its scope, the v5 package, the review45 harness
(BINDING-MANIFEST-R45-HARNESS 9af8e07a...9ffb, group harness_r45_package) and the v4 record constants (V5-BUILD-DIFF.md)."""
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
WORK = pathlib.Path("C:/t/r2x/r42-sandbox/r45q")                  # R43-44: the one work folder of this task (v4: r43p; r42: C:/t/iso/work/r2x/r42)
SANDBOX_BASE = pathlib.Path("C:/t/r2x/r42-sandbox")               # this task's dry sandboxes AND the declared live base
STAMP = "r32-v5"                                                   # R43-44: new stamp (r32-v3 executed; r32-v4 never created, v4 superseded)
RUN_FOLDER = SANDBOX_BASE / STAMP                                  # never created by this task
DECLARATION_DATE = "2026-10-08"                                    # R43-44: the v5 freeze date (owner's local date, +04)
SCOPE = f"m2-fresh-validation-r32-v5-{DECLARATION_DATE}"           # R43-44: new scope name (the v3 scope exists; no v4 scope was ever created)
DRY_BASE = WORK / "sb"                                             # R43-40: dry / demo run folders (driver-side base redirect, r43p_base.py)
AI_LEDGER = pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite")
RESPONSE_LEDGER = M2 / "M2-REVIEW-RESPONSE.md"
RESPONSE_BEFORE = ("1143c6856c9f55a0bb450b19f0ff43ba58f47af0593a3fc1e98f07a037d182e0", 219716)

# the bound interpreter (A-11 / ORCH-10 2.1.1): the merged installation's backend venv
PY = (EP / "backend/venv/Scripts/python.exe").as_posix()
VENV = (EP / "backend/venv").as_posix()
VENV_FREEZE_RECORD = MERGED / "merge/reports/merged-venv-freeze.txt"
DESKTOP_PY = DESKTOP_EP + "/backend/venv/Scripts/python.exe"

CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r30n/backend")   # R43-40: the R43 trees (review43 re-points 1-4)
BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r13/backend")
CANDIDATE = ("C:/t/iso/cand-r30n", "436daef215c72fbe2429dcd783e087bf39756ad7")
BASELINE = ("C:/t/iso/frozen-r13", "7ec3d2cf983b70a604844beda8eb6b1ec6173d34")
LEDGER_EXPECTED = {"entries": 484, "scopes": 18, "limit_amendments": 0}   # R43-40 (R43V-04): re-pinned to the state at the v4 freeze (v3 scope present)

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
HARNESS42_PACKAGE = REVIEW42 / "scripts" / "harness-r32"          # R43-40: review42's own harness (record only; v3 ran it)
WORK_HARNESS = WORK / "harness-r32"
BINDING42 = REVIEW42 / "BINDING-MANIFEST-R42.json"
BOUNDS42 = REVIEW42 / "PROJECT-REQUEST-BOUNDS.json"
# R43-40: the review43 harness (Verification 43 VERIFIED WITH CONDITIONS) is the bound harness of v4. HARNESS42 keeps its
# name so the carried scripts run unchanged, and now names the folder the code is IMPORTED from: the bound folder, or a
# byte copy named by R43_HARNESS_RUN (checked against the bound hashes by check_run_copy before any import).
REVIEW43 = PILOT / "review43"
HARNESS43 = REVIEW43 / "scripts" / "harness-r32"                  # the bound, declared folder (isolation.allowed_under_forbidden.harness)
BINDING43 = REVIEW43 / "BINDING-MANIFEST-R43-HARNESS.json"
BINDING43_SHA = "f35355aa8a8bca16803db3576fda8260a470915fee9c905b035f8d8bd9a374a7"
HARNESS43_GROUP = "harness_r43_package"                            # R43-44: the v4 harness group (record only)
# R43-44: the review45 harness (Verification 45 VERIFIED WITH CONDITIONS) is the bound harness of v5: review43 plus the dry-only
# baseline-facts drill. HARNESS42 keeps its name and now names the folder the review45 code is IMPORTED from (the bound folder, or a
# byte copy named by R43_HARNESS_RUN, checked against BINDING-MANIFEST-R45-HARNESS by check_run_copy before any import).
REVIEW45 = PILOT / "review45"
HARNESS45 = REVIEW45 / "scripts" / "harness-r32"                  # the bound, declared folder of v5 (isolation.allowed_under_forbidden.harness)
BINDING45 = REVIEW45 / "BINDING-MANIFEST-R45-HARNESS.json"
BINDING45_SHA = "9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb"
DRILL_CRITERION_SHA = "8b183053cf10e5332f8b198a1d5b1aae5169c47671ad5e35346acf31cca5d918"
HARNESS_GROUP = "harness_r45_package"                              # R43-44
HARNESS42 = pathlib.Path(os.environ.get("R43_HARNESS_RUN") or HARNESS45)
PACKAGE = PILOT / "declaration-r32-v5"                             # R43-44
DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V5.json"
RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json"       # produced ONLY by the owner (fill_owner_digest), never here
# R43-44: the superseded v4 declaration (frozen, never authorized, never run; read-only; v5 is built from its exact bytes)
V4 = PILOT / "declaration-r32-v4"
V4_NAME = "FRESH-VALIDATION-DECLARATION-R32-V4.json"
V4_SHA = "e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9"
V4_MANIFEST_SHA = "4c7285eeea712dde9350dc5e7b1f3068eafea6becad10636bb58ff69665720ab"
V4_SCOPE = "m2-fresh-validation-r32-v4-2026-10-08"                # never created
V4_RUN_FOLDER = SANDBOX_BASE / "r32-v4"                            # never created
# R43-40: the executed v3 declaration (frozen; its RUN and authorization files committed as 7a1bf6f; never edited)
V3 = PILOT / "declaration-r32-v3"
V3_NAME = "FRESH-VALIDATION-DECLARATION-R32-V3.json"
V3_SHA = "9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40"
V3_MANIFEST_SHA = "a2df60dca2dfba5ebaff8bdc4b73ef76926cbecd7fd58c8916885e7e709a1a24"
V3_RUN_SHA = "c31cccd4eab844d738b40b07e191e064221ea3dd3a7697c01c2fc998763a2b6a"
V3_AUTH_SHA = "f2546c91912e4fefc5516158327a54c4c05776286310f61d6bea10f09b84425f"
V3_SCOPE = "m2-fresh-validation-r32-v3-2026-10-06"
V3_RUN_FOLDER = SANDBOX_BASE / "r32-v3"
OWNER_RECORDS = SANDBOX_BASE / "r32-v3-owner-records"
TASK37_BINDING_SHA = "e1735093c3852f060977b675cafcd0f78696f5e48fee2c7a3bb05d08225d83c1"
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
TASK_FILE = MR / "orchestrator/tasks/R43-44-TASK.md"               # R43-44
TASK_FILE_SHA = "1cd72eb3eaed75b8321ae7a201e0f504564137f02f67947e25b710908a6e4d0b"


def check_run_copy() -> dict:
    """R43-40 (R43V-09), R43-44: the folder the harness is imported from (HARNESS42) must hold exactly the bound bytes of the
    review45 harness: every file of the bound group harness_r45_package under scripts/harness-r32 re-hashed at its bound
    path AND at the run copy. A difference is PACKET MISMATCH."""
    man = json.loads(BINDING45.read_text(encoding="utf-8"))
    if sha256_file(BINDING45) != BINDING45_SHA:
        raise PacketMismatch(f"PACKET MISMATCH: {BINDING45.as_posix()} is not {BINDING45_SHA}")
    group = {p: w for p, w in man["files"][HARNESS_GROUP].items() if "/scripts/harness-r32/" in p}
    bad = [p for p, w in group.items() if sha256_file(p) != w]
    copy_bad = [p for p, w in group.items() if sha256_file(HARNESS42 / pathlib.Path(p).name) != w] if HARNESS42 != HARNESS45 else []
    if bad or copy_bad:
        raise PacketMismatch(f"PACKET MISMATCH: bound {bad[:3]} run copy {copy_bad[:3]}")
    return {"bound_folder": HARNESS45.as_posix(), "imported_from": HARNESS42.as_posix(), "files": len(group), "run_copy": HARNESS42 != HARNESS45}


def declared_here(PF) -> None:
    """R43-40 (Verification 43 P8), R43-44: when the harness is imported from a byte copy, preflight_r32.HERE is set to the
    bound folder in THIS process only, so isolation_binding() and validate_declaration compare the declaration with the folder
    the live runner will run from (PILOT/review45/scripts/harness-r32)."""
    PF.HERE = HARNESS45


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
