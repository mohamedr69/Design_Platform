"""Checker for review21/: manifest, links, bindings (accepted / reviewed / frozen trees clean and equal; only the reader
changed in the application), the H-06 control binding unchanged, earlier packages and reviewer files unchanged, the
draft declaration marked NOT EXECUTED with no approved budget and bound to the frozen sample / stage / labels-manifest /
workload, recorded test results (flags off and T: 0 failures; the E runs' failure counts as recorded and explained),
the dry chain ok, no new model request (ledger settled unchanged at 104 unless H-06 ran), and the H-06 state (completed
outputs, or a saved refusal and zero H-06 ledger entries). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review21")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
res = {}
man = json.loads((PKG / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.rglob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists():
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
b = json.loads((PKG / "bindings/SOURCE-BINDINGS.json").read_text(encoding="utf-8"))
fr = b["frozen_r21_candidate"]
res["trees"] = {"accepted": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == b["accepted"]["commit"] and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                "reviewed": git("C:/t/iso/cand-ai3", "rev-parse", "HEAD") == b["reviewed_r19_candidate"]["commit"] and not git("C:/t/iso/cand-ai3", "status", "--porcelain"),
                "frozen": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == fr["commit"] and not git("C:/t/iso/cand-ai4", "status", "--porcelain"),
                "frozen_files": all(sha(f"C:/t/iso/cand-ai4/{f}") == h for f, h in fr["changed_files"].items()),
                "only_reader_changed_in_app": fr["application_files_changed"] == ["backend/app/ai/evidence_reader.py"],
                "packaged_reader": sha(PKG / "candidate/files/backend/app/ai/evidence_reader.py") == fr["changed_files"]["backend/app/ai/evidence_reader.py"]}
h = b["h06_control_binding_unchanged"]
res["h06_binding"] = sha(h["declaration"]) == h["sha256"] == "7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3" and h["runner_matches"] and h["boq_arm_reader"] == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
res["reviewer_files_unchanged"] = all(sha(MR / "reviews/M2-review-20" / n) == v for n, v in b["reviewer_files_review20"].items())
earlier = {}
for pk in ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19", "review20"):
    m = json.loads((PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    earlier[pk] = all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
d = json.loads((PKG / "declaration/R21-DECLARATION.draft.json").read_text(encoding="utf-8"))
res["draft"] = {"not_executed": d["executed"] is False and "NOT EXECUTED" in d["status"], "no_budget": d["new_model_budget_approved"] is False,
                "bound": sha(PKG / "declaration/R21-STAGE.json") == d["stage"]["manifest_sha256"] and all(sha(PKG / "labels-r21" / n) == v for n, v in d["labels"]["files"].items())
                and d["code"]["successor"]["commit"] == fr["commit"] and d["sources"]["sample"]["n_planned"] == 27,
                "sample_sha_matches_bindings": sha(PKG / "declaration/R21-SAMPLE.json") == b["r21"]["sample"], "caps": d["ledger"]["caps"], "sum_caps": d["ledger"]["sum_caps"]}
junit = lambda p: {k: int(re.search(fr'{k}="(\d+)"', pathlib.Path(p).read_text(encoding="utf-8")).group(1)) for k in ("tests", "failures", "errors", "skipped")}
res["tests"] = {x.stem: junit(x) for x in sorted((PKG / "tests").glob("*.xml"))}
res["exit_codes"] = {x.stem: x.read_text().strip() for x in sorted((PKG / "tests").glob("*-EXIT.txt"))}
res["dry_chain_ok"] = json.loads((PKG / "dry/DRY-CHAIN-CHECK.json").read_text(encoding="utf-8"))["ok"]
L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = L.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
h06 = L.execute("select count(*) from entries where scope like 'ai-pilot-r18-2026-09-30-H06%'").fetchone()[0]
r21 = L.execute("select count(*) from entries where scope like 'r21-four-arm-2026%'").fetchone()[0]
L.close()
res["ledger"] = {"settled_original_experiment": settled, "h06_entries": h06, "r21_live_scope_entries": r21}
res["h06"] = {"completed_runs": [p.name for p in sorted((PKG / "h06").rglob("CONT-H06.json"))] if (PKG / "h06").exists() else [],
              "refusal_logs": [p.name for p in sorted((PKG / "h06").glob("H06-S-refusal-*.log"))] if (PKG / "h06").exists() else [],
              "preflights": [p.name for p in sorted((PKG / "h06").glob("H06-PREFLIGHT-*.json"))] if (PKG / "h06").exists() else []}
t = res["tests"]
res["ok"] = bool(not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(res["trees"].values())
                 and res["h06_binding"] and res["reviewer_files_unchanged"] and all(earlier.values())
                 and res["draft"]["not_executed"] and res["draft"]["no_budget"] and res["draft"]["bound"] and res["draft"]["sample_sha_matches_bindings"]
                 and t["FOCUSED-off"]["failures"] == 0 and t["FOCUSED-off"]["errors"] == 0 and t["FOCUSED-T"]["failures"] == 0 and t["FOCUSED-T"]["errors"] == 0
                 and t["FOCUSED-L1"]["failures"] == 0 and t["FOCUSED-L3"]["failures"] == 0 and t["R16-HARNESS"]["failures"] == 0 and t["HARNESS-V3"]["failures"] == 0
                 and res["dry_chain_ok"] and r21 == 0
                 and ((h06 == 0 and settled == 104 and res["h06"]["refusal_logs"]) or (res["h06"]["completed_runs"] and settled <= 150)))
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in ("tests",)}, indent=1))
print({k: (v["tests"], v["failures"], v["errors"]) for k, v in res["tests"].items()})
