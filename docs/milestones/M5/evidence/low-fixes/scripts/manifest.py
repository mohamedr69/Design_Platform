"""MANIFEST.json for the ORCH-041 evidence (M5 low fixes): sha256 of each
evidence file and of each changed file (git blob of the committed version
and working-tree bytes), the protected files, commands, UTC times,
interpreter and commits."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WT = Path("G:/dev (2)/dev/ep-platform-merged/wt-m5b")
EVIDENCE = WT / "docs/milestones/M5/evidence/low-fixes"
REPORT = WT / "docs/milestones/M5/M5-LOW-FIXES-IMPLEMENTATION.md"
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(WT), *args], capture_output=True, text=True, check=True).stdout.strip()


def blob(commit: str, name: str) -> bytes:
    return subprocess.run(["git", "-C", str(WT), "cat-file", "blob", f"{commit}:{name}"],
                          capture_output=True, check=True).stdout


def main(spec: dict) -> None:
    base, impl = spec["base"], spec["impl"]
    files = {}
    for name in git("diff", "--name-only", base, impl).splitlines():
        data = blob(impl, name)
        files[name] = {"git_blob": git("rev-parse", f"{impl}:{name}"), "sha256_committed": hashlib.sha256(data).hexdigest(),
                       "bytes_committed": len(data), "crlf_committed": b"\r\n" in data,
                       "bom_committed": data.startswith(b"\xef\xbb\xbf")}
    protected = {}
    for name in ("backend/app/redesign/cad.py", "backend/app/redesign/verify.py"):
        protected[name] = {"sha256_impl": hashlib.sha256(blob(impl, name)).hexdigest(),
                           "sha256_orch039_c274205": hashlib.sha256(blob("c274205", name)).hexdigest()}
        protected[name]["byte_equal"] = protected[name]["sha256_impl"] == protected[name]["sha256_orch039_c274205"]
    evidence = {p.relative_to(EVIDENCE).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
                for p in sorted(EVIDENCE.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    version = subprocess.run([PY, "-B", "-c", "import sys,sqlite3,sqlalchemy,pytest;print(sys.version.split()[0],"
                              "sqlite3.sqlite_version,sqlalchemy.__version__,pytest.__version__)"],
                             capture_output=True, text=True).stdout.split()
    out = {"task": "ORCH-041 (U2-M5-LOW-FIXES), ep-implementer, Claude Opus 5.5",
           "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "base": {"branch": "roadmap/u2", "commit": base, "contains": ["fcc5ddd (M5 merge)", "f95a3f4 (M8 merge)"]},
           "branch": "task/m5-low-fixes", "implementation_commit": impl,
           "interpreter": {"path": PY + " -B", "python": version[0], "sqlite": version[1],
                           "sqlalchemy": version[2], "pytest": version[3]},
           "pytest_flags": "-p no:cacheprovider --basetemp=C:/t/tmp/m5b/bt (TEMP/TMP=C:/t/tmp/m5b/tmp)",
           "times_utc": spec["times"], "commands": spec["commands"],
           "changed_files": files, "protected_files": protected, "evidence": evidence,
           "report": {"path": REPORT.relative_to(WT).as_posix(), "sha256": sha(REPORT)},
           "note": "Evidence classes: FUNCTIONAL-MOCKED (stand-in AutoCAD and read-back), SQLITE (real file-backed "
                   "WAL database, two connections). No REAL-AUTOCAD and no REAL-MODEL claim."}
    (EVIDENCE / "MANIFEST.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("written", len(files), "changed files,", len(evidence), "evidence files")


if __name__ == "__main__":
    main(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
