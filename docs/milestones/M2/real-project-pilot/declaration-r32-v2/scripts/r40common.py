"""ORCH-09 (R40DECL-IMPL): shared paths, constants, hashing and JSON writing for the corrected declaration package
`PILOT/declaration-r32-v2/` (bound to the review39 harness).

Nothing here writes outside the work folder, the package, the scratchpad or C:/t/r2x/r40-sandbox. The AI ledger is only
ever opened as file:...?mode=ro with uri=True. No provider, model, network or ledger scope is touched by this module."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
M2 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2")
WORK = pathlib.Path("C:/t/iso/work/r2x/r40")
PACKAGE = PILOT / "declaration-r32-v2"
SUPERSEDED = PILOT / "declaration-r32"
SCRATCH = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40decl")
SANDBOX_BASE = pathlib.Path("C:/t/r2x/r40-sandbox")       # this task's dry sandboxes AND the declared live sandbox base
AI_LEDGER = pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite")
RESPONSE_LEDGER = M2 / "M2-REVIEW-RESPONSE.md"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r29/backend")
BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")

# the bound harness: review39 (BINDING-MANIFEST-R39 binds the package copy as harness_r39_package and the work copy
# C:/t/iso/work/r2x/r39/harness-r32 as harness_r39; byte-identical). The runbook runs the PACKAGE copy.
REVIEW39 = PILOT / "review39"
HARNESS = REVIEW39 / "scripts" / "harness-r32"
BINDING = REVIEW39 / "BINDING-MANIFEST-R39.json"
BINDING_SHA = "a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b"
REVIEW39_MANIFEST_SHA = "2430fa2bf6bcb5bf3775efe143575dcd9cdc55723ab994cfaec5f63fbdded990"
RUN_SET = PILOT / "review34" / "RUN-SET-PROPOSAL.json"
RUN_SET_SHA = "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"
TRUTH = PILOT / "review34" / "dry-run" / "TRUTH-R32.json"
TRUTH_SHA = "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"
BOUNDS = REVIEW39 / "PROJECT-REQUEST-BOUNDS.json"
BOUNDS_SHA = "99be01fbf25ed6e6219cc6b09b56aa9cd728ad9b30379e6b4b157aa394131721"

DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V2.json"
RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json"     # produced ONLY by the owner (fill_owner_digest), never here
AUTH_NAME = "OWNER-DISPATCH-AUTHORIZATION.json"               # written ONLY by the owner, never here
TOKEN_ENV = "R34_OWNER_DISPATCH_TOKEN"
TOKEN_PLACEHOLDER = "TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION"
DUMMY_DIGEST = "0" * 63 + "1"        # in memory only; syntactically valid, never written to disk, never a real token digest

SUPERSEDED_SHA = "38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0"
SUPERSEDED_MANIFEST_SHA = "59361b9331cf3d28979129dfa1749b10f345e5ad24f26b9691012423fd1be2c8"
BUILD_R37 = SUPERSEDED / "scripts" / "build_declaration_r37.py"
BUILD_R37_SHA = "775d1e5107d4bb43130eec550487d44959b6e47d494900a726cd4ebd3acd03f8"
R37COMMON_SHA = "ec64b5e5664d5b0b8909b7566c095d4fc3433ffaa3330c4208f312d8af5cfe86"
ESTIMATES_R37_SHA = "d87fe3454aa5e9652129df311c1b4e086271347758d37b3f46a0b8ab8443eb69"

STAMP = "r32-v2"
SCOPE = "m2-fresh-validation-r32-v2-2026-10-04"
RUN_FOLDER = SANDBOX_BASE / STAMP
APPLICATION_LEDGER_PY = CANDIDATE_BACKEND / "app" / "ai" / "ledger.py"
APPLICATION_LEDGER_PY_SHA = "d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca"   # equal in both trees

CANDIDATE = ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d")
BASELINE = ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")
LEDGER_EXPECTED = {"entries": 483, "scopes": 17, "limit_amendments": 0}
RESPONSE_BEFORE = ("caf949b2f878253049e0ae65421cad78b8d169009e3b2a024a4eb01d5aed10e4", 213865)
CLI_EXE = pathlib.Path("C:/Users/moham/AppData/Local/Microsoft/WinGet/Packages/Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe/claude.exe")
CLI_EXE_SHA = "0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03"
CLI_EXE_BYTES = 218746016
CLI_VERSION_LINE = "2.1.263 (Claude Code)"


class PacketMismatch(RuntimeError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
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


def forbidden_files(roots=(PILOT, MR, pathlib.Path("C:/t"), SCRATCH)) -> list:
    """Every file named like an owner authorization, a runnable declaration or a token (names only; nothing opened)."""
    hits = []
    for root in roots:
        root = pathlib.Path(root)
        if not root.exists():
            continue
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                low = f.lower()
                if "dispatch-authorization" in low or low.endswith(".run.json") or "owner-token" in low:
                    hits.append((pathlib.Path(dirpath) / f).as_posix())
    return sorted(hits)


def harness_import_path() -> str:
    """Put the bound review39 harness (package copy) on sys.path after checking every module file against the binding."""
    import sys

    man = json.loads(BINDING.read_text(encoding="utf-8"))
    if sha256_file(BINDING) != BINDING_SHA:
        raise PacketMismatch("PACKET MISMATCH: BINDING-MANIFEST-R39.json")
    bound = man["files"]["harness_r39_package"]
    bad = [p for p, want in bound.items() if sha256_file(p) != want]
    if bad:
        raise PacketMismatch(f"PACKET MISMATCH: harness files differ: {bad[:3]}")
    sys.dont_write_bytecode = True
    if str(HARNESS) not in sys.path:
        sys.path.insert(0, str(HARNESS))
    return str(HARNESS)
