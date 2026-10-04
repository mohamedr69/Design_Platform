"""Checker for review23/: manifest complete, markdown links, trees unchanged (no application change), harness v4.1 frozen
hashes equal the packaged files and the scoring files equal review22's frozen v4, reviewer files unchanged, earlier
packages and labels unchanged, recorded tests (harness 19 / runner 8 / lifecycle 5 green; the reviewer's stop regressions
1 failed on v4 and 3 passed on v4.1), the lifecycle and runner evidence flags, and the live ledger untouched (128 settled
original-experiment entries; no r21 / r22 / r23 live scope). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review23")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.rglob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
b = load(PKG / "bindings/SOURCE-BINDINGS.json")
fz = load(PKG / "bindings/FROZEN-HARNESS.json")
res["trees"] = {"accepted": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == b["accepted"]["commit"] and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                "frozen_r21_candidate": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == b["frozen_r21_candidate"]["commit"] == "719e8de661b8b10427ef6cff5d2d277a53b64dc6" and not git("C:/t/iso/cand-ai4", "status", "--porcelain"),
                "reader_unchanged": sha("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py") == b["frozen_r21_candidate"]["evidence_reader_sha256"], "application_change": b["application_change"]}
res["harness_frozen"] = {"packaged_files_equal_frozen_hashes": all(sha(PKG / "harness-v4.1" / f) == h for f, h in fz["files"].items()), "runner": fz["runner_version"], "lifecycle": fz["lifecycle_contract"],
                         "scoring_files_unchanged_vs_review22": all(fz["scoring_files_unchanged_vs_review22"].values()), "changed_vs_v4": fz["changed_vs_review22_v4"], "new_vs_v4": fz["new_vs_review22_v4"],
                         "durable_allowance_module_unchanged": sha(fz["durable_allowance_module"]["file"]) == fz["durable_allowance_module"]["sha256"]}
res["reviewer_files_unchanged"] = all((MR / "reviews/M2-review-23" / n).exists() and sha(MR / "reviews/M2-review-23" / n) == h for n, h in b["reviewer_files_review23"].items())
earlier = {}
for pk, h in b["earlier_package_manifests"].items():
    mp = PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json"
    earlier[pk] = sha(mp) == h and all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in load(mp)["files"].items())
res["earlier_packages_unchanged"] = earlier
res["labels_r21_unchanged"] = all(sha(PKG.parent / "review21/labels-r21" / n) == h for n, h in b["labels_r21_files"].items())
res["dry_inputs_unchanged"] = b["dry_inputs_unchanged"]


def junit(p):
    r = ET.parse(p).getroot()
    s = r if r.tag == "testsuite" else r.find("testsuite")
    return {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}


t = {"HARNESS-V4": junit(PKG / "harness-v4.1/logs/HARNESS-V4.xml"), "RUNNER-V4": junit(PKG / "harness-v4.1/logs/RUNNER-V4.xml"), "LIFECYCLE-V4.1": junit(PKG / "harness-v4.1/logs/LIFECYCLE-V4.1.xml"),
     "REVIEWER-STOP-REGRESSIONS-on-v4": junit(PKG / "repro/on-v4/REVIEW23-REGRESSIONS.xml"), "REVIEWER-STOP-REGRESSIONS-on-v4.1": junit(PKG / "repro/on-v4.1/REVIEW23-REGRESSIONS.xml")}
res["tests"] = t
res["tests_ok"] = (t["HARNESS-V4"] == {"tests": 19, "failures": 0, "errors": 0, "skipped": 0} and t["RUNNER-V4"] == {"tests": 8, "failures": 0, "errors": 0, "skipped": 0}
                   and t["LIFECYCLE-V4.1"] == {"tests": 5, "failures": 0, "errors": 0, "skipped": 0}
                   and t["REVIEWER-STOP-REGRESSIONS-on-v4"] == {"tests": 3, "failures": 1, "errors": 0, "skipped": 0} and t["REVIEWER-STOP-REGRESSIONS-on-v4.1"] == {"tests": 3, "failures": 0, "errors": 0, "skipped": 0})
life = load(PKG / "lifecycle-evidence/LIFECYCLE.json")["scenarios"]
res["lifecycle_evidence"] = {n: all(v for v in s["checks"].values()) for n, s in life.items()}
ev = load(PKG / "runner-evidence/RUNNER-INTEGRATION.json")["scenarios"]
res["runner_controls"] = {"S2_kill_resume_only_remaining_allowance": ev["S2_kill_resume"]["resumed"]["six_page_doc"]["capped_at_12"] and ev["S2_kill_resume"]["resumed"]["one_page_doc_not_resent"],
                          "S7_deferral_resumes_when_eligible": ev["S7_deferral"]["first"]["zero_requests_for_deferred_project"] and ev["S7_deferral"]["resumed"]["status"] == "completed",
                          "all_eight": {"S1": ev["S1_baseline"]["charged_equals_sent"], "S3": ev["S3_new_tag"]["refused"]["refused_before_dispatch"], "S4": ev["S4_second_writer"]["second_refused_before_dispatch"],
                                        "S5": all(v["fresh_equals_charge_delta"] for v in ev["S5_cache_hit"]["per_document"].values()), "S6": ev["S6_scope_exhaust"]["exhaustion_is_a_budget_stop"], "S8": ev["S8_refusals"]["both_refused_before_dispatch"]}}
p4 = load(PKG / "repro/on-v4/CRITICAL-STOP-PROBE.json")
p41 = load(PKG / "repro/on-v4.1/CRITICAL-STOP-PROBE.json")
res["stop_probe"] = {"v4_resume_sent": sum(p4["resume"]["requests_this_invocation"].values()), "v4_1_resume_sent": sum(p41["resume"]["requests_this_invocation"].values()),
                     "v4_1_stop_preserved": p41["resume"]["stopped"] == p41["initial"]["stopped"] and p41["initial"]["stopped"] == p4["initial"]["stopped"], "v4_1_initial_requests": p41["initial"]["requests_this_invocation"]}
L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = L.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
live = L.execute("select count(*) from entries where scope like 'r22%' or scope like 'r21-four-arm%' or scope like 'r23%'").fetchone()[0]
scopes = [s for (s,) in L.execute("select scope from scopes") if s.startswith(("r22", "r21-four-arm", "r23"))]
L.close()
res["ledger"] = {"settled_original_experiment": settled, "r21_r22_r23_live_entries": live, "r21_r22_r23_live_scopes": scopes}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(v for v in res["trees"].values() if isinstance(v, bool))
             and res["harness_frozen"]["packaged_files_equal_frozen_hashes"] and res["harness_frozen"]["scoring_files_unchanged_vs_review22"] and res["harness_frozen"]["durable_allowance_module_unchanged"]
             and res["reviewer_files_unchanged"] and all(earlier.values()) and res["labels_r21_unchanged"] and all(res["dry_inputs_unchanged"].values()) and res["tests_ok"]
             and all(res["lifecycle_evidence"].values()) and res["runner_controls"]["S2_kill_resume_only_remaining_allowance"] and res["runner_controls"]["S7_deferral_resumes_when_eligible"]
             and all(res["runner_controls"]["all_eight"].values()) and res["stop_probe"]["v4_resume_sent"] == 8 and res["stop_probe"]["v4_1_resume_sent"] == 0 and res["stop_probe"]["v4_1_stop_preserved"]
             and settled == 128 and live == 0 and not scopes)
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "tests"}, indent=1, default=str)[:3500])
print("tests", t)
print("OK" if res["ok"] else "NOT OK")
