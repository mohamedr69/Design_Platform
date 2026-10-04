"""Assemble docs/milestones/M2/real-project-pilot/review19/ (a NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil
import sys

W = pathlib.Path("C:/t/iso/work/r2x/review19")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review19")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; it is never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst):
    src = pathlib.Path(src)
    for p in sorted(src.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts:
            cp(p, f"{dst}/{p.relative_to(src).as_posix()}")


for f in ("CORRECTION-REPORT.md", "CHANGE-MAP.md", "PROSPECTIVE-EXPERIMENT-PROPOSAL.md"):
    cp(W / "pkg-src" / f, f)
cptree(W / "pkg-src/candidate", "candidate")
for f in ("backend/app/ai/evidence_reader.py", "backend/tests/test_ai_pilot_r19.py", "backend/tests/_e_crop_coords.py", "backend/tests/test_ai_pilot_r18.py"):
    cp(f"C:/t/iso/cand-ai3/{f}", f"candidate/files/{f}")
for d in ("repro", "results-v2", "tests-out", "crop-validation", "bindings", "h06"):
    cptree(W / d, {"tests-out": "tests", "crop-validation": "tests/development-crop-validation"}.get(d, d))
for f in ("patch_r19_01.py", "score_cont_v2.py", "classify_crop_failures.py", "h06_preflight.py", "bindings.py", "package_r19.py", "verify_r19_package.py"):
    cp(W / f, f"scripts/{f}")
cp(W / "repro/run_reviewer_contracts.py", "scripts/run_reviewer_contracts.py")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review19", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
