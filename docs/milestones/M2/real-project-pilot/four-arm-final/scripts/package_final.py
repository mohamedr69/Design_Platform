"""Assemble docs/milestones/M2/real-project-pilot/four-arm-final/ (NEW folder, never rebuilt in place) from the frozen run
evidence, the final offline scoring, the analysis outputs, the reports and the scripts, then write the evidence manifest."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/four-arm-final")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst):
    shutil.copytree(src, PKG / dst)


for f in ("FINAL-EXPERIMENT-REPORT.md", "ARM-COMPARISON.md", "POST-RUN-ADJUDICATION.md"):
    cp(R / "pkg" / f, f)
for f in ("ACCURACY-AND-COVERAGE.json", "USAGE-AND-BUDGET.json", "CRITICAL-AND-HELD-EVIDENCE.json", "ARM-COMPARISON.json", "ADOPTION-GATES.json"):
    cp(R / "final-analysis" / f, f)
cptree(R / "final-score", "final-score")
cp(R / "final-score.log", "final-score/SCORE.log")
cp(R / "final-score.exit", "final-score/SCORE.exit")
for a in ("A", "L1", "L2", "L3", "L4"):
    cptree(R / f"evidence-{a}", f"arms/{a}")
    cptree(pathlib.Path("C:/t/r2x/runs") / f"final-{a}" / "db", f"arms/{a}/sandbox-db")
for a in ("L2", "L3", "L4"):
    if (R / f"{a}-REPORT.md").exists() and not (PKG / f"arms/{a}/{a}-REPORT.md").exists():
        cp(R / f"{a}-REPORT.md", f"arms/{a}/{a}-REPORT.md")
for a in ("L3", "L4"):
    cp(R / f"TARGETED-{a}.json", f"targeted/TARGETED-{a}.json")
cp("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json", "declaration/FINAL-DECLARATION.v2.json")
cp("C:/t/iso/work/r2x/r27/AUTHORIZATION-2026-10-01.md", "authorization/AUTHORIZATION-2026-10-01.md")
cp(R / "RUN-LOG.jsonl", "run/RUN-LOG.jsonl")
for p in sorted(R.glob("PREFLIGHT-*.json")):
    cp(p, f"run/preflights/{p.name}")
cp(R / "POST-RUN-BINDINGS.json", "run/POST-RUN-BINDINGS.json")
for f in ("preflight.py", "snapshot.py", "arm_report.py", "l2_report.py", "arm_extra.py", "targeted_calls.py", "save_evidence.py", "final_analysis.py",
          "post_run_bindings.py", "package_final.py", "verify_final_package.py", "append_response_final.py"):
    cp(R / f, f"scripts/{f}")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*")) if p.is_file()}
man = {k: v for k, v in man.items() if k not in ("evidence/EVIDENCE-MANIFEST.json", "evidence/PACKAGE-CHECK.json")}
(PKG / "evidence").mkdir(exist_ok=True)
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "four-arm-final (M2 four-arm accuracy experiment, declaration 6c0189b3)", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
