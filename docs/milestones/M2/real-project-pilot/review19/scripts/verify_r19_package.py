"""Checker for review19/ (run after the final edit): manifest, Markdown links, bindings (accepted / reviewed / successor
commits and files clean and equal to the recorded hashes; the H-06 declaration binding unchanged), earlier packages and
the reviewer's files unchanged, reproduction (2 failed / 6 passed on c216206, probes identical to the reviewer's; 8 passed
on the frozen successor), recorded test results, the v2 replay (all-planned recovery equal to v1; required-usable matched =
1), and H-06 (either completed arms or a saved refusal with no dispatch). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review19")
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
res["trees"] = {"accepted": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == b["accepted"]["commit"] and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                "reviewed": git("C:/t/iso/cand-ai2", "rev-parse", "HEAD") == b["reviewed_candidate"]["commit"] and not git("C:/t/iso/cand-ai2", "status", "--porcelain"),
                "successor": git("C:/t/iso/cand-ai3", "rev-parse", "HEAD") == b["successor"]["commit"] and not git("C:/t/iso/cand-ai3", "status", "--porcelain"),
                "successor_files": all(sha(f"C:/t/iso/cand-ai3/{f}") == h for f, h in b["successor"]["changed_files"].items()),
                "packaged_reader": sha(PKG / "candidate/files/backend/app/ai/evidence_reader.py") == b["successor"]["changed_files"]["backend/app/ai/evidence_reader.py"]}
h = b["h06_control_binding_unchanged"]
res["h06_binding"] = sha(h["declaration"]) == h["sha256"] == "7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3" and \
    sha("C:/t/iso/work/r2x/ai-pilot-r18/cont_boq.py") == h["runner_cont_boq_sha256"] and h["boq_arm_reader"] == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
res["reviewer_files_unchanged"] = all(sha(MR / "reviews/M2-review-19" / n) == v for n, v in b["reviewer_files"].items())
earlier = {}
for pk in ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction"):
    m = json.loads((PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    earlier[pk] = all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
junit = lambda p: {k: int(re.search(fr'{k}="(\d+)"', pathlib.Path(p).read_text(encoding="utf-8")).group(1)) for k in ("tests", "failures", "errors", "skipped")}
rp = PKG / "repro"
res["repro"] = {"c216206_contracts": junit(rp / "on-c216206/REVIEW19-CONTRACTS.xml"),
                "c216206_probes_identical_to_reviewer": json.loads((rp / "on-c216206/INDEPENDENT-E-PROBES.json").read_text()) ==
                json.loads((MR / "reviews/M2-review-19/INDEPENDENT-E-PROBES.json").read_text()),
                "successor_contracts": junit(rp / "on-successor-frozen/REVIEW19-CONTRACTS.xml")}
res["tests"] = {x.stem: junit(x) for x in sorted((PKG / "tests").glob("*.xml"))}
res["exit_codes"] = {x.stem: x.read_text().strip() for x in sorted((PKG / "tests").glob("*-EXIT.txt"))}
v2 = json.loads((PKG / "results-v2/CONT-METRICS.v2.json").read_text(encoding="utf-8"))
res["v2"] = {"required_usable_matched": v2["required_usable_matched"]["n"], "under_R19_01": v2["required_usable_matched"]["under_R19_01"]["n"],
             "no_transport_stop_subgroup": v2["no_transport_stop_subgroup"]["n"], "headline_n": v2["headline_all_planned"]["n"]}
pre = sorted((PKG / "h06").glob("H06-PREFLIGHT-*.json"))
last = json.loads(pre[-1].read_text(encoding="utf-8")) if pre else {}
L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
h06_entries = L.execute("select count(*) from entries where scope like 'ai-pilot-r18-2026-09-30-H06%'").fetchone()[0]
L.close()
res["h06"] = {"preflights": len(pre), "last_preflight_dispatch_allowed": last.get("dispatch_allowed"), "h06_ledger_entries": h06_entries,
              "refusal_logs": [p.name for p in sorted((PKG / "h06").glob("*refusal*.log"))], "completed_runs": [p.name for p in sorted((PKG / "h06").glob("*BOQ*.json"))]}
t = res["tests"]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(res["trees"].values())
             and res["h06_binding"] and res["reviewer_files_unchanged"] and all(earlier.values())
             and res["repro"]["c216206_contracts"]["failures"] == 2 and res["repro"]["c216206_contracts"]["tests"] == 8
             and res["repro"]["c216206_probes_identical_to_reviewer"] and res["repro"]["successor_contracts"]["failures"] == 0
             and res["repro"]["successor_contracts"]["tests"] == 8
             and t["FOCUSED-off"]["failures"] == t["FOCUSED-T"]["failures"] == 0 and t["FOCUSED-off"]["errors"] == t["FOCUSED-T"]["errors"] == 0
             and t["FOCUSED-TE-actual-crop"]["failures"] == 22 and t["FOCUSED-TE-raw"]["failures"] == 19 and t["FOCUSED-TE-shim-compat"]["failures"] == 12
             and t["R16-HARNESS"]["failures"] == 0 and t["BOQ-QUEUE"]["failures"] == 0
             and res["v2"] == {"required_usable_matched": 1, "under_R19_01": 0, "no_transport_stop_subgroup": 4, "headline_n": 7}
             and bool((h06_entries == 0 and res["h06"]["refusal_logs"]) or res["h06"]["completed_runs"]))
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1)[:3500])
