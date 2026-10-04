"""Assemble the ai-accuracy-pilot package (new folder under the M2 pilot docs; no earlier package is touched) and write
evidence/EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
RUNS = pathlib.Path("C:/t/r2x/runs")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/ai-accuracy-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; it is never rebuilt in place")


def cp(src, dst):
    dst = PKG / dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def cptree(src, dst, skip=()):
    src = pathlib.Path(src)
    for p in sorted(src.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and not any(s in p.as_posix() for s in skip):
            cp(p, f"{dst}/{p.relative_to(src).as_posix()}")


cp(A / "pkg-src/AI-PILOT-REPORT.md", "AI-PILOT-REPORT.md")
cp(A / "pkg-src/CHANGE-MAP.md", "CHANGE-MAP.md")
for f in ("PILOT-DECLARATION.json", "PILOT-SHARES.json", "PILOT-SHARES.sha256"):
    cp(A / f, f"declaration/{f}")
cp("C:/t/r2x/dry-runs/PILOT-DECLARATION.dry.json", "declaration/dry-run/PILOT-DECLARATION.dry.json")
cptree("C:/t/r2x/dry-runs/score", "declaration/dry-run/score")
cp(A / "PILOT-SAMPLE.json", "sample/PILOT-SAMPLE.json")
cp("C:/t/r2x/pilot-stage/PILOT-STAGE.json", "sample/PILOT-STAGE.json")
cptree(A / "labels", "labels")
cptree(A / "pkg-src/labels-crops", "labels/crops")
cp(A / "boq/PILOT-BOQ-A-extraction.json", "boq/PILOT-BOQ-A-extraction.json")
# candidate: the commit as a patch, the changed files
CAND = "C:/t/iso/cand-ai"
patch = subprocess.run(["git", "-C", CAND, "format-patch", "-1", "--stdout", "e5a0a94"], capture_output=True).stdout
(PKG / "candidate").mkdir(parents=True, exist_ok=True)
(PKG / "candidate/e5a0a94.patch").write_bytes(patch)
for f in ("backend/app/ai/evidence_reader.py", "backend/tests/test_ai_pilot_2026_09_30.py"):
    cp(f"{CAND}/{f}", f"candidate/{pathlib.PurePosixPath(f).name}")
cptree(A / "tests-out", "tests")
for f in ("declare_pilot.py", "make_pilot_stage.py", "pilot_a.py", "pilot_shares.py", "pilot_ev.py", "pilot_boq.py", "boq_queue.py", "dry_provider.py",
          "score_pilot.py", "matched_subset.py", "select_pilot.py", "labels_pilot.py", "patch_candidate.py", "patch_candidate_2.py", "zoom.py",
          "package_pilot.py", "verify_pilot_package.py", "tests/test_boq_queue.py"):
    cp(A / f, f"scripts/{f}")
cptree(A / "logs", "logs")
for tag in ("ai-pilot-A", "ai-pilot-S", "ai-pilot-G", "ai-pilot-T", "ai-pilot-boq-S", "ai-pilot-boq-T"):
    cptree(RUNS / tag / "out", f"runs/{tag}/out")
    cptree(RUNS / tag / "db", f"runs/{tag}/db")
cptree(A / "results", "results")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
(PKG / "evidence/REVIEWER-FILES-SHA256.json").write_text(json.dumps({
    "task": {"file": str(MR / "reviews/M2-review-17/TASK-TARGETED-AI-ACCURACY.md").replace("\\", "/"), "sha256": sha(MR / "reviews/M2-review-17/TASK-TARGETED-AI-ACCURACY.md")},
    "review_17": {"file": str(MR / "reviews/M2-review-17/REVIEW-17-REPORT.md").replace("\\", "/"), "sha256": sha(MR / "reviews/M2-review-17/REVIEW-17-REPORT.md")},
    "permission": {"file": str(MR / "OWNER-AI-PERMISSION-ROUND2.md").replace("\\", "/"), "sha256": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md")}}, indent=1) + "\n", encoding="utf-8")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "ai-accuracy-pilot", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
