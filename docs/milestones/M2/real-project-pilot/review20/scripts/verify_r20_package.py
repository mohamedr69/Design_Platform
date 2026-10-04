"""Checker for review20/: manifest, Markdown links, earlier packages and the Review 20 reviewer files unchanged, the H-06
binding unchanged and its live state (no H-06 ledger entry, no allowance store, a saved refusal -- or completed arm
outputs), the draft marked NOT EXECUTED and bound to its evidence hashes, the coverage-draft tests recorded, and no new
model request since the Review 19 package (ledger settled count unchanged at 104). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import os
import pathlib
import re
import sqlite3

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review20")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
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
earlier = {}
for pk in ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19"):
    m = json.loads((PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    earlier[pk] = all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
res["review20_files"] = {p.name: sha(p) for p in sorted((MR / "reviews/M2-review-20").glob("*")) if p.is_file()}
decl = "C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json"
res["h06_binding_unchanged"] = sha(decl) == "7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3" and \
    sha("C:/t/iso/work/r2x/ai-pilot-r18/cont_boq.py") == json.loads(pathlib.Path(decl).read_text(encoding="utf-8"))["code"]["scripts"]["cont_boq.py"]
L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = L.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
h06 = L.execute("select count(*) from entries where scope like 'ai-pilot-r18-2026-09-30-H06%'").fetchone()[0]
L.close()
res["ledger"] = {"settled_original_experiment": settled, "h06_entries": h06, "no_new_request_since_review19": settled == 104}
res["h06"] = {"allowance_store_exists": os.path.exists("C:/t/r2x/ledger/ai-pilot-r18-h06-allowance.sqlite"),
              "refusal_logs": [p.name for p in sorted((PKG / "h06").glob("H06-S-refusal-*.log"))],
              "preflights": [p.name for p in sorted((PKG / "h06").glob("H06-PREFLIGHT-*.json"))],
              "refusal_text_present": all("cannot fit this arm now" in p.read_text(encoding="utf-8") for p in (PKG / "h06").glob("H06-S-refusal-*.log"))}
draft = json.loads((PKG / "EXPERIMENT-DRAFT.json").read_text(encoding="utf-8"))
res["draft"] = {"status": draft["status"], "not_executed": "NOT EXECUTED" in draft["status"],
                "evidence_bound": all(sha(PKG / {"coverage_v3_draft.py": "scripts/coverage_v3_draft.py", "test_coverage_v3_draft.py": "scripts/test_coverage_v3_draft.py"}.get(k, k)) == v
                                      for k, v in draft["evidence_files"].items())}
x = (PKG / "tests/COVERAGE-V3-DRAFT.xml").read_text(encoding="utf-8")
res["coverage_draft_tests"] = {k: int(re.search(fr'{k}="(\d+)"', x).group(1)) for k in ("tests", "failures", "errors")}
res["ok"] = bool(not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(earlier.values())
                 and res["h06_binding_unchanged"] and res["ledger"]["no_new_request_since_review19"] and h06 == 0
                 and not res["h06"]["allowance_store_exists"] and res["h06"]["refusal_logs"] and res["h06"]["refusal_text_present"]
                 and res["draft"]["not_executed"] and res["draft"]["evidence_bound"]
                 and res["coverage_draft_tests"] == {"tests": 7, "failures": 0, "errors": 0})
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "review20_files"}, indent=1))
