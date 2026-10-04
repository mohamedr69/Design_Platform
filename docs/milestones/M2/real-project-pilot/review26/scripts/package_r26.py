"""Assemble docs/milestones/M2/real-project-pilot/review26/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json. Full-page renders are not copied (regenerable by render_r26.py from the hash-checked
stage; their hashes are in RENDERS.json); the zoom crops used as label evidence are copied."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review26")
DRY = pathlib.Path("C:/t/r2x/dry-runs/r26-preflight")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst, skip=("__pycache__", "io")):
    for p in sorted(pathlib.Path(src).rglob("*")):
        rel = p.relative_to(src)
        if p.is_file() and not any(x in skip for x in rel.parts) and not p.name.endswith((".sqlite", ".lock", ".tmp")):
            cp(p, f"{dst}/{rel.as_posix()}")


for f in ("READINESS-REPORT.md", "BUDGET-PROPOSAL.md", "LABELS-SUMMARY.md", "RUNBOOK.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
cp(R / "FINAL-DECLARATION.json", "declaration/FINAL-DECLARATION.json")
cptree(R / "labels-r26", "labels-r26")
cptree(R / "drafts", "label-evidence/drafts")
cptree(R / "renders/crops", "label-evidence/crops")
cp(R / "renders/RENDERS.json", "label-evidence/RENDERS.json")
for d in ("bindings", "enforcement", "preflight"):
    cptree(R / d, d)
cp(DRY / "FINAL-DECLARATION.dry.json", "preflight/FINAL-DECLARATION.dry.json")
for run in sorted((DRY / "runs").iterdir()):
    if (run / "out").exists():
        cptree(run / "out", f"preflight/runs/{run.name}/out")
for f in ("render_r26.py", "crop.py", "labels_r26.py", "review_pass_r26.py", "declare_final.py", "enforcement_r26.py", "preflight_r26.sh", "bindings_r26.py",
          "package_r26.py", "verify_r26_package.py", "append_response_r26.py"):
    cp(R / f, f"scripts/{f}")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review26 (four-arm readiness)", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
