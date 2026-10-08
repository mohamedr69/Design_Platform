"""ORCH-036 evidence: MANIFEST.json -- sha256 of every evidence file and every
changed source file, the commands, start/end UTC, interpreter and HEAD.
Run from wt-m8:
    python -B docs/milestones/M8/evidence/wall-index/scripts/manifest.py START_UTC END_UTC
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
EVIDENCE = ROOT / "docs" / "milestones" / "M8" / "evidence" / "wall-index"
BASE = "5270773a469e31f5cad0b7d7a170e168a1d918ba"
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe -B"
COMMANDS = [
    "git -C roadmap-u2 worktree add -b task/m8-wall-index wt-m8 " + BASE,
    f"{PY} tests/fixtures_m8/make_fixtures.py   (cwd backend; run twice, byte-identical)",
    f"{PY} -m pytest -p no:cacheprovider --basetemp=C:/t/tmp/m8/bt --junitxml=<evidence>/targeted.xml -q "
    "tests/test_redesign_walls_layers.py tests/test_redesign.py tests/test_drawing_prep.py tests/test_fa_interfaces.py "
    "tests/test_fa_cases.py tests/test_fa_evidence.py tests/test_fa_review_fixes.py tests/test_ifc_boq.py "
    "tests/test_render_bounds.py   (cwd backend; log targeted.log)",
    f"{PY} -m pytest -p no:cacheprovider --basetemp=C:/t/tmp/m8/bt --junitxml=<evidence>/full-suite.xml -q   "
    "(cwd backend; log full-suite.log)",
    f"{PY} ../docs/milestones/M8/evidence/wall-index/scripts/gc01_composition.py   (cwd backend; GC-01 read-only)",
    f"{PY} docs/milestones/M8/evidence/wall-index/scripts/compare_junit.py "
    "docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.xml <evidence>/full-suite.xml "
    "<evidence>/full-suite-vs-baseline.json",
    f"{PY} docs/milestones/M8/evidence/wall-index/scripts/manifest.py START END",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(start: str, end: str) -> None:
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    changed = sorted(set(git("diff", "--name-only", BASE, "--", "backend").splitlines())
                     | set(git("ls-files", "--others", "--exclude-standard", "--", "backend").splitlines()))
    evidence = sorted(p for p in EVIDENCE.rglob("*") if p.is_file() and p.name != "MANIFEST.json")
    report = ROOT / "docs" / "milestones" / "M8" / "M8-WALL-INDEX-IMPLEMENTATION.md"
    gc01 = Path("G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dxf")
    manifest = {
        "task": "ORCH-036 (U2-M8-WALL-INDEX)",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "head": git("rev-parse", "HEAD"),
        "base": BASE, "base_code_equals": "668f92f",
        "start_utc": start, "end_utc": end,
        "interpreter": PY, "python": sys.version.split()[0], "platform": platform.platform(),
        "ezdxf": __import__("ezdxf").__version__,
        "golden_input": {"path": str(gc01), "sha256": sha(gc01) if gc01.is_file() else None, "access": "read-only"},
        "commands": COMMANDS,
        "changed_source": {p: sha(ROOT / p) for p in changed if (ROOT / p).is_file()},
        "report": {str(report.relative_to(ROOT)).replace("\\", "/"): sha(report)} if report.is_file() else {},
        "evidence": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in evidence},
    }
    (EVIDENCE / "MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("head", "start_utc", "end_utc")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
