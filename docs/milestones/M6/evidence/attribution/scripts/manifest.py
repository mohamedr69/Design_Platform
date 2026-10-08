"""MANIFEST.json for the M6 attribution evidence (ORCH-043): sha256 of each
evidence file and of each changed file (working-tree bytes and git blob of
the implementation commit), the commands, UTC times, interpreter and HEAD.

    python manifest.py <base commit> <implementation commit>"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WT = Path("G:/dev (2)/dev/ep-platform-merged/wt-m6")
EVIDENCE = WT / "docs/milestones/M6/evidence/attribution"
REPORT = WT / "docs/milestones/M6/M6-ATTRIBUTION-IMPLEMENTATION.md"
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"
FLAGS = "-p no:cacheprovider --basetemp=C:/t/tmp/m6/bt"
TARGETED = ("tests/test_m6_attribution.py tests/test_document_classification_v2.py tests/test_document_classification_pilot.py "
            "tests/test_classification_evidence.py tests/test_document_routing.py tests/test_document_processing_v2.py "
            "tests/test_file_sync_v2_processing.py tests/test_document_sync.py tests/test_worker_runtime.py "
            "tests/test_repair_tool.py tests/test_migrations.py "
            "tests/test_projects.py::test_a_project_carrying_every_kind_of_row_can_still_be_deleted")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(WT), *args], capture_output=True, text=True, check=True).stdout.strip()


def main(base: str, impl: str) -> None:
    files = {}
    for name in git("diff", "--name-only", base, impl).splitlines():
        blob = subprocess.run(["git", "-C", str(WT), "cat-file", "blob", f"{impl}:{name}"], capture_output=True, check=True).stdout
        entry = {"git_blob": git("rev-parse", f"{impl}:{name}"), "sha256_committed": hashlib.sha256(blob).hexdigest(),
                 "bytes_committed": len(blob)}
        if (WT / name).is_file():
            entry["sha256_worktree"] = sha(WT / name)
        files[name] = entry
    evidence = {p.relative_to(EVIDENCE).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
                for p in sorted(EVIDENCE.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    runs = dict(line.split(" ", 1) for line in (EVIDENCE / "runs.txt").read_text(encoding="utf-8").splitlines() if " " in line)
    version = subprocess.run([PY, "-B", "-c", "import sys,sqlite3,sqlalchemy,pytest;print(sys.version.split()[0],"
                              "sqlite3.sqlite_version,sqlalchemy.__version__,pytest.__version__)"],
                             capture_output=True, text=True).stdout.split()
    out = {"task": "ORCH-043 (U2-M6-ATTRIBUTION), ep-implementer, Claude Opus 5.5",
           "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "base": {"branch": "roadmap/u2", "commit": base, "contains": ["fcc5ddd (M5 merge)", "f95a3f4 (M8 merge)"],
                    "not_contained": "task/m5-low-fixes (a3d2d7d)"},
           "branch": "task/m6-attribution", "implementation_commit": impl,
           "interpreter": {"path": PY + " -B", "python": version[0], "sqlite": version[1], "sqlalchemy": version[2],
                           "pytest": version[3]},
           "pytest_flags": FLAGS, "env": {"TEMP": "C:/t/tmp/m6/tmp", "TMP": "C:/t/tmp/m6/tmp"},
           "runs_utc": runs,
           "commands": {"targeted": f"cd backend && {PY} -B -m pytest {FLAGS} -q {TARGETED} --junitxml=<evidence>/targeted.xml -W ignore",
                        "full": f"cd backend && {PY} -B -m pytest {FLAGS} -q tests --junitxml=<evidence>/full-suite.xml -W ignore",
                        "compare": f"{PY} -B docs/milestones/M6/evidence/attribution/scripts/compare.py"},
           "changed_files": files, "evidence": evidence,
           "report": {"path": "docs/milestones/M6/M6-ATTRIBUTION-IMPLEMENTATION.md", "sha256": sha(REPORT) if REPORT.is_file() else None},
           "note": "Evidence classes: SQLITE (file-backed test databases), SCRIPTED-PROVIDER (RecordingProvider in the harness's "
                   "AI arm), SYNTHETIC-CLONE (the harness's fixture database). No REAL-MODEL, no REAL-CLONE, no live database."}
    (EVIDENCE / "MANIFEST.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("written", len(files), "changed files,", len(evidence), "evidence files")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
