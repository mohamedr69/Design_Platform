"""Assemble docs/milestones/M2/real-project-pilot/review21/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review21")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review21")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst):
    for p in sorted(pathlib.Path(src).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts:
            cp(p, f"{dst}/{p.relative_to(src).as_posix()}")


for f in ("CORRECTION-AND-PREP-REPORT.md", "CHANGE-MAP.md", "ANALYSIS-PLAN.md", "STATUS.md"):
    cp(R / "pkg-src" / f, f)
cptree(R / "pkg-src/candidate", "candidate")
frozen = (R / "FROZEN-COMMIT.txt").read_text().strip()
for f in ("backend/app/ai/evidence_reader.py", "backend/tests/test_ai_pilot_r21.py", "backend/tests/_e_crop_coords.py", "backend/tests/_e_frame_shim.py"):
    cp(f"C:/t/iso/cand-ai4/{f}", f"candidate/files/{f}")
cp(R / "FROZEN-COMMIT.txt", "candidate/FROZEN-COMMIT.txt")
for f in ("R21-DECLARATION.draft.json", "R21-SAMPLE.json", "R21-PAGE-CLASSES.json"):
    cp(R / f, f"declaration/{f}")
cp("C:/t/r2x/r21-stage/R21-STAGE.json", "declaration/R21-STAGE.json")
cp("C:/t/r2x/dry-runs/R21-DECLARATION.dry.json", "dry/R21-DECLARATION.dry.json")
cptree("C:/t/r2x/dry-runs/r21-score", "dry/score")
for arm in ("A", "L1", "L2", "L3", "L4", "L1-restart", "L2-restart"):
    cptree(f"C:/t/r2x/dry-runs/r21dry-{arm}/out", f"dry/runs/r21dry-{arm}/out")
cp("C:/t/r2x/dry-runs/r21-stage/R21-DRY-STAGE.json", "dry/R21-DRY-STAGE.json")
cp("C:/t/r2x/dry-runs/R21-SHARES.json", "dry/R21-SHARES.json")
for d in ("labels-r21", "labels-dry", "workload", "bindings", "tests-out", "dry", "h06", "logs"):
    if (R / d).exists():
        cptree(R / d, "tests" if d == "tests-out" else d)
for f in ("patch_r21.py", "patch_r21_2.py", "coverage_v3.py", "score_arms_v3.py", "test_harness_v3.py", "test_coverage_v3_draft_compat.py", "arm_a.py", "arm_shares.py",
          "arm_ev.py", "derive_r21_runners.py", "declare_r21.py", "make_dry_stage.py", "dry_labels.py", "check_dry_chain.py", "select_r21_sample.py", "make_r21_stage.py",
          "workload_r21.py", "label_manifest_r21.py", "bindings_r21.py", "package_r21.py", "verify_r21_package.py"):
    cp(R / f, f"scripts/{f}")
cp("C:/t/iso/work/r2x/review19/h06_preflight.py", "scripts/h06_preflight.py")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review21", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
