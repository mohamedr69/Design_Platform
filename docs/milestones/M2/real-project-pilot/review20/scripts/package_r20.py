"""Assemble docs/milestones/M2/real-project-pilot/review20/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json; then run the checker."""
import hashlib
import json
import pathlib
import shutil
import sys

W = pathlib.Path("C:/t/iso/work/r2x/review20")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review20")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; it is never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst):
    for p in sorted(pathlib.Path(src).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            cp(p, f"{dst}/{p.relative_to(src).as_posix()}")


for f in ("STATUS-AND-H06.md", "EXPERIMENT-DRAFT.md", "EXPERIMENT-DRAFT.json", "H06-RUNBOOK.md"):
    cp(W / "pkg-src" / f, f)
for d in ("h06", "isolation", "feasibility", "coverage-v3", "workload", "tests-out"):
    cptree(W / d, "tests" if d == "tests-out" else d)
for f in ("offline_isolation_replay.py", "sample_feasibility.py", "coverage_v3_draft.py", "test_coverage_v3_draft.py", "coverage_v3_on_pilot.py",
          "workload_from_ledger.py", "write_draft_json.py", "package_r20.py", "verify_r20_package.py"):
    cp(W / f, f"scripts/{f}")
cp("C:/t/iso/work/r2x/review19/h06_preflight.py", "scripts/h06_preflight.py")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review20", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
