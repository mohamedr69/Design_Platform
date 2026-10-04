"""Checker for four-arm-final/: manifest complete and matching; markdown links; declaration hash; per-arm frozen evidence
manifests; sandbox databases equal the post-run bindings; post-run bindings ok; the frozen scorer re-run offline (AI disabled,
throw-away database) reproduces final-score/ARMS-METRICS.v4.json; the analysis re-run reproduces the five JSON outputs; the
live ledger matches USAGE-AND-BUDGET.json; the labels are unchanged; required statements present. Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import sqlite3
import subprocess
import tempfile

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/four-arm-final")
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
DSHA = "6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.relative_to(PKG).as_posix() not in ("evidence/EVIDENCE-MANIFEST.json", "evidence/PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.glob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
res["declaration"] = sha(PKG / "declaration/FINAL-DECLARATION.v2.json") == DSHA == sha("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json")
arms = {}
for a in ("A", "L1", "L2", "L3", "L4"):
    m = load(PKG / f"arms/{a}/EVIDENCE-MANIFEST.json")
    arms[a] = all(sha(PKG / f"arms/{a}" / k) == h for k, h in m["files"].items())
res["arm_evidence_manifests"] = arms
prb = load(PKG / "run/POST-RUN-BINDINGS.json")
res["post_run_bindings_ok"] = prb["ok"]
res["sandbox_db_frozen"] = {a: sha(PKG / f"arms/{a}/sandbox-db/default.db") == prb["sandbox_databases"][a] for a in prb["sandbox_databases"]}
res["labels_unchanged_now"] = all(sha(pathlib.Path("C:/t/iso/work/r2x/r27/labels-r26.2") / n) == h for n, h in load(PKG / "declaration/FINAL-DECLARATION.v2.json")["labels"]["files"].items())
# re-run the frozen scorer offline
tmp = pathlib.Path(tempfile.mkdtemp(prefix="final-check-", dir="C:/t/iso/tmp"))
env = {**os.environ, "AI_ENABLED": "false", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp",
       "DATABASE_URL": f"sqlite:///{(tmp / 'no.db').as_posix()}"}
env.pop("PILOT_DRY", None)
r = subprocess.run([PY, "score_arms_v4.py", "--declaration", "C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json", "--declaration-sha", DSHA, "--runs", "C:/t/r2x/runs",
                    "--tags", "A=final-A,L1=final-L1,L2=final-L2,L3=final-L3,L4=final-L4", "--out", str(tmp / "score")],
                   cwd="C:/t/iso/work/r2x/review25/harness-v4.3", env=env, capture_output=True, text=True)
res["rescore_exit"] = r.returncode
res["rescore_equal"] = r.returncode == 0 and load(tmp / "score/ARMS-METRICS.v4.json") == load(PKG / "final-score/ARMS-METRICS.v4.json") and all(
    load(tmp / f"score/eval-{a}.json") == load(PKG / f"final-score/eval-{a}.json") for a in ("A", "L1", "L2", "L3", "L4"))
r2 = subprocess.run([PY, "C:/t/iso/work/r2x/run-final/final_analysis.py", str(tmp / "score"), str(tmp / "analysis")], env=env, capture_output=True, text=True)
outs = ("ACCURACY-AND-COVERAGE.json", "USAGE-AND-BUDGET.json", "CRITICAL-AND-HELD-EVIDENCE.json", "ARM-COMPARISON.json", "ADOPTION-GATES.json")
strip = lambda o: json.loads(json.dumps(o).replace(str(tmp / "score").replace("\\", "\\\\"), "<score>"))
res["analysis_rerun_equal"] = r2.returncode == 0 and all(load(tmp / "analysis" / n) == load(PKG / n) for n in outs)
shutil.rmtree(tmp, ignore_errors=True)
use = load(PKG / "USAGE-AND-BUDGET.json")
c = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
res["ledger_matches_usage"] = all(c.execute("select count(*) from entries where scope = ?", (v["scope"],)).fetchone()[0] == v["dispatched"] for v in use["scopes"].values())
res["ledger_total_within_688"] = use["totals"]["dispatched"] <= 688
res["original_experiment_settled_128"] = c.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0] == 128
c.close()
txt = {n: (PKG / n).read_text(encoding="utf-8") for n in ("FINAL-EXPERIMENT-REPORT.md", "ARM-COMPARISON.md", "POST-RUN-ADJUDICATION.md")}
res["statements"] = {"no_default": "No default" in txt["FINAL-EXPERIMENT-REPORT.md"], "changes_still_required": "CHANGES STILL REQUIRED" in txt["FINAL-EXPERIMENT-REPORT.md"],
                     "declaration_hash": DSHA in txt["FINAL-EXPERIMENT-REPORT.md"], "inconclusive": "INCONCLUSIVE" in txt["ARM-COMPARISON.md"],
                     "adjudication_cannot_change_score": "cannot change" in txt["POST-RUN-ADJUDICATION.md"]}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and res["declaration"] and all(arms.values())
             and res["post_run_bindings_ok"] and all(res["sandbox_db_frozen"].values()) and res["labels_unchanged_now"] and res["rescore_equal"] and res["analysis_rerun_equal"]
             and res["ledger_matches_usage"] and res["ledger_total_within_688"] and res["original_experiment_settled_128"] and all(res["statements"].values()))
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1, default=str)[:4000])
print("OK" if res["ok"] else "NOT OK")
