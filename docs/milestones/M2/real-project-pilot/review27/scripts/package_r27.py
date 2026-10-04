"""Assemble docs/milestones/M2/real-project-pilot/review27/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review27")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


for f in ("CORRECTION-REPORT.md", "DECISION-CARD.md", "BUDGET-PROPOSAL.md", "OWNER-CLAIMS-DIFF.md", "LABELS-SUMMARY.md", "RUNBOOK.md", "CHANGE-MAP.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
cp(R / "FINAL-DECLARATION.v2.json", "declaration/FINAL-DECLARATION.v2.json")
for p in sorted((R / "labels-r26.2").iterdir()):
    cp(p, f"labels-r26.2/{p.name}")
cp(R / "bindings/SOURCE-BINDINGS.json", "bindings/SOURCE-BINDINGS.json")
cp(R / "ROI-POPULATION.json", "evidence/ROI-POPULATION.json")
cp(R / "RESCORE-DELTA.json", "evidence/RESCORE-DELTA.json")
for p in sorted((R / "rescore").iterdir()):
    cp(p, f"evidence/rescore/{p.name}")
cp(R / "rescore.log", "evidence/rescore/RESCORE.log")
cp(R / "rescore.exit", "evidence/rescore/RESCORE.exit")
for f in ("labels_r26_2.py", "declare_final_v2.py", "roi_population_r27.py", "bindings_r27.py", "package_r27.py", "verify_r27_package.py", "append_response_r27.py"):
    cp(R / f, f"scripts/{f}")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review27 (funding clarity and independent label binding)", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
