"""MANIFEST.json for the M5 safe-Apply evidence (ORCH-039): sha256 of each
evidence file and of each changed file (working-tree bytes and git blob of
the committed version), the commands, UTC times, interpreter and HEAD."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WT = Path("G:/dev (2)/dev/ep-platform-merged/wt-m5")
EVIDENCE = WT / "docs/milestones/M5/evidence/safe-apply"
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(WT), *args], capture_output=True, text=True, check=True).stdout.strip()


def main(base: str, impl_commit: str, times: dict, commands: list[str]) -> None:
    changed = git("diff", "--name-only", base, impl_commit).splitlines()
    files = {}
    for name in changed:
        p = WT / name
        entry = {"git_blob": git("rev-parse", f"{impl_commit}:{name}")}
        blob = subprocess.run(["git", "-C", str(WT), "cat-file", "blob", f"{impl_commit}:{name}"],
                              capture_output=True, check=True).stdout
        entry["sha256_committed"] = hashlib.sha256(blob).hexdigest()
        entry["bytes_committed"] = len(blob)
        if p.is_file():
            entry["sha256_worktree"] = sha(p)
        files[name] = entry
    evidence = {p.relative_to(EVIDENCE).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
                for p in sorted(EVIDENCE.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    version = subprocess.run([PY, "-B", "-c", "import sys,sqlite3,sqlalchemy,pytest;print(sys.version.split()[0],"
                              "sqlite3.sqlite_version,sqlalchemy.__version__,pytest.__version__)"],
                             capture_output=True, text=True).stdout.split()
    out = {"task": "ORCH-039 (U2-M5-SAFE-APPLY), ep-implementer, Claude Opus 5.5",
           "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "base": {"branch": "roadmap/u2", "commit": base, "code_equals": "668f92f"},
           "branch": "task/m5-safe-apply", "implementation_commit": impl_commit,
           "interpreter": {"path": PY + " -B", "python": version[0], "sqlite": version[1],
                           "sqlalchemy": version[2], "pytest": version[3]},
           "pytest_flags": "-p no:cacheprovider --basetemp=C:/t/tmp/m5/bt",
           "times_utc": times, "commands": commands,
           "changed_files": files, "evidence": evidence,
           "report": {"path": "docs/milestones/M5/M5-SAFE-APPLY-IMPLEMENTATION.md",
                      "sha256": sha(WT / "docs/milestones/M5/M5-SAFE-APPLY-IMPLEMENTATION.md")},
           "note": "Evidence classes: FUNCTIONAL-MOCKED (stand-in AutoCAD and read-back), SQLITE (real file-backed "
                   "WAL database, two connections). No REAL-AUTOCAD and no REAL-MODEL claim."}
    (EVIDENCE / "MANIFEST.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("written", len(files), "changed files,", len(evidence), "evidence files")


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    main(spec["base"], spec["impl"], spec["times"], spec["commands"])
