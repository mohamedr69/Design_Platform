"""ORCH-07 (R37DECL-IMPL): shared paths, hashing and JSON writing for the declaration package `declaration-r32`.

Nothing here writes outside the work folder, the package, the scratchpad or C:/t/r2x/r37-sandbox. The AI ledger is only
ever opened as file:...?mode=ro with uri=True. No provider, model, network or ledger scope is touched."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
M2 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2")
WORK = pathlib.Path("C:/t/iso/work/r2x/r37")
PACKAGE = PILOT / "declaration-r32"
SCRATCH = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r37decl")
DRY_SANDBOX_BASE = pathlib.Path("C:/t/r2x/r37-sandbox")
LIVE_SANDBOX_BASE = pathlib.Path("C:/t/r2x/r34-sandbox")
AI_LEDGER = pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite")
RESPONSE_LEDGER = M2 / "M2-REVIEW-RESPONSE.md"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"

# the bound harness (BINDING-MANIFEST-R36): the work-folder copy is the one the binding names as harness_r36; the package
# copy review36/scripts/harness-r32 is byte-identical (harness_r36_package)
HARNESS_BOUND = pathlib.Path("C:/t/iso/work/r2x/r36/harness-r32")
HARNESS_PACKAGE = PILOT / "review36" / "scripts" / "harness-r32"
BINDING = PILOT / "review36" / "BINDING-MANIFEST-R36.json"
RUN_SET = PILOT / "review34" / "RUN-SET-PROPOSAL.json"

DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32.json"
AUTH_NAME = "OWNER-DISPATCH-AUTHORIZATION.json"
TOKEN_PLACEHOLDER = "TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION"
DUMMY_DIGEST = "0" * 63 + "1"          # in memory only; syntactically valid, never written to disk, never a real token digest

# task-time frozen inputs (recomputed before acting; a difference is PACKET MISMATCH)
FROZEN = {
    "review36_manifest": (PILOT / "review36/evidence/EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0"),
    "binding_manifest_r36": (BINDING, "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568"),
    "literal_compare_r32": (HARNESS_PACKAGE / "literal_compare_r32.py", "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"),
    "run_set_proposal": (RUN_SET, "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"),
    "reviewed2_labels": (PILOT / "fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json", "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    "policy": (MR / "AI-ACCURACY-POLICY.md", "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47"),
    "policy_amendment_r32_01": (MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6"),
    "evaluator_10": (pathlib.Path("C:/t/iso/cand-r29/backend/scripts/m2_eval6.py"), "268d86231260392dc5592a6937803b8fcd15a41e9590b442f3f0a70dc57b4b4f"),
}
RESPONSE_BEFORE_SHA256 = "b055b6a67cbad7e0abef195c68422551129ddffc26c2d1c1ec18b2557a1872e8"
CANDIDATE = ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d")
BASELINE = ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")
LEDGER_EXPECTED = {"entries": 483, "scopes": 17, "limit_amendments": 0}


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
    """The package JSON form: sort_keys, indent 1, ensure_ascii False, LF, trailing newline."""
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


def check_frozen() -> dict:
    """Recompute every task hash; raise PacketMismatch on any difference."""
    out = {}
    for name, (path, want) in FROZEN.items():
        got = sha256_file(path)
        if got != want:
            raise PacketMismatch(f"PACKET MISMATCH: {name} {path} {got} != {want}")
        out[name] = {"path": pathlib.Path(path).as_posix(), "sha256": got}
    return out


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


def git_state(repo: str) -> dict:
    import subprocess

    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
    dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
    return {"repo": repo, "head": head, "clean": not dirty, "porcelain_lines": len(dirty.splitlines()) if dirty else 0}


def authorization_files(roots) -> list:
    """Every file whose name contains DISPATCH-AUTHORIZATION (case-insensitive) under the roots (names only)."""
    hits = []
    for root in roots:
        root = pathlib.Path(root)
        if not root.exists():
            continue
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                if "dispatch-authorization" in f.lower():
                    hits.append((pathlib.Path(dirpath) / f).as_posix())
    return sorted(hits)
