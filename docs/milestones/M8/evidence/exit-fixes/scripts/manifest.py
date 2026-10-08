"""ORCH-044 evidence: MANIFEST.json, hashed from the COMMITTED bytes (U2M8V-02).

Every changed source file (against the snapshot BASE) and every evidence
file is recorded by its git blob id and the sha256 of the blob's bytes as
committed -- not of this checkout's files, which a Windows autocrlf checkout
turns to CRLF. check_manifest.py recomputes the same from any commit and from
any fresh checkout (Windows or not).

Run from the worktree root after the evidence is committed:
    python -B docs/milestones/M8/evidence/exit-fixes/scripts/manifest.py START_UTC END_UTC
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
EVIDENCE = "docs/milestones/M8/evidence/exit-fixes"
REPORT = "docs/milestones/M8/M8-EXIT-FIXES-IMPLEMENTATION.md"
CORRECTED = "docs/milestones/M8/M8-WALL-INDEX-IMPLEMENTATION.md"
BASE = "1708692084f2253fa0eb792910f7c8b685680da7"
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe -B"
BT = "-p no:cacheprovider --basetemp=C:/t/tmp/m8b/bt"
COMMANDS = [
    f"git -C roadmap-u2 worktree add -b task/m8-exit-fixes wt-m8b {BASE}",
    f"{PY} tests/fixtures_m8/make_fixtures.py   (cwd backend)",
    f"{PY} docs/milestones/M8/evidence/exit-fixes/scripts/fixtures_determinism.py "
    "<evidence>/fixtures-determinism.json   (8 runs, 7 PYTHONHASHSEED values and none)",
    f"{PY} -m pytest {BT} --junitxml=<evidence>/targeted.xml -q tests/test_redesign_walls_layers.py "
    "tests/test_redesign_exit_fixes.py tests/test_redesign.py tests/test_drawing_prep.py tests/test_redesign_apply.py "
    "tests/test_prep_readiness.py tests/test_drawing_review.py tests/test_fa_interfaces.py   (cwd backend; targeted.log)",
    f"{PY} -m pytest {BT} --junitxml=<evidence>/full-suite.xml -q   (cwd backend; full-suite.log)",
    f"{PY} docs/milestones/M8/evidence/wall-index/scripts/compare_junit.py "
    "docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.xml <evidence>/full-suite.xml "
    "<evidence>/full-suite-vs-m4-baseline.json",
    f"{PY} docs/milestones/M8/evidence/wall-index/scripts/compare_junit.py "
    "docs/milestones/M6/evidence/merge-and-conditions/full-suite.xml <evidence>/full-suite.xml "
    "<evidence>/full-suite-vs-roadmap-u2-latest.json",
    f"{PY} ../docs/milestones/M8/evidence/exit-fixes/scripts/gc01_exit_fixes.py   (cwd backend; GC-01 read-only)",
    f"{PY} docs/milestones/M8/evidence/exit-fixes/scripts/manifest.py START END",
    f"{PY} docs/milestones/M8/evidence/exit-fixes/scripts/check_manifest.py [REV]",
]


def git(*args: str, binary: bool = False):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8").strip()


def entry(head: str, path: str) -> dict:
    blob = git("rev-parse", f"{head}:{path}")
    return {"blob": blob, "sha256": hashlib.sha256(git("cat-file", "blob", blob, binary=True)).hexdigest()}


def main(start: str, end: str) -> None:
    head = git("rev-parse", "HEAD")
    changed = sorted(p for p in git("diff", "--name-only", BASE, head).splitlines()
                     if not p.startswith(EVIDENCE + "/") and p not in (REPORT, CORRECTED))
    evidence = sorted(p for p in git("ls-tree", "-r", "--name-only", head, "--", EVIDENCE).splitlines()
                      if not p.endswith("/MANIFEST.json"))
    gc01 = Path("G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dxf")
    h = hashlib.sha256()
    if gc01.is_file():
        with open(gc01, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    manifest = {
        "task": "ORCH-044 (U2-M8-EXIT-FIXES), authority A-16 (engineer decisions 1-8)",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"), "head": head, "base": BASE,
        "hashing": "sha256 of the committed blob bytes (git cat-file blob), and the blob id; never the checkout's "
                   "bytes (U2M8V-02). check_manifest.py recomputes both from a commit and from a checkout.",
        "start_utc": start, "end_utc": end,
        "interpreter": PY, "python": sys.version.split()[0], "platform": platform.platform(),
        "ezdxf": __import__("ezdxf").__version__,
        "golden_input": {"path": str(gc01), "sha256": h.hexdigest() if gc01.is_file() else None, "access": "read-only"},
        "commands": COMMANDS,
        "changed_source": {p: entry(head, p) for p in changed},
        "reports": {p: entry(head, p) for p in (REPORT, CORRECTED) if p in git("ls-tree", "-r", "--name-only", head,
                                                                               "--", "docs/milestones/M8").splitlines()},
        "evidence": {p: entry(head, p) for p in evidence},
    }
    out = ROOT / EVIDENCE / "MANIFEST.json"
    out.write_bytes((json.dumps(manifest, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({"head": head, "changed_source": len(manifest["changed_source"]),
                      "evidence": len(manifest["evidence"]), "reports": len(manifest["reports"])}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
