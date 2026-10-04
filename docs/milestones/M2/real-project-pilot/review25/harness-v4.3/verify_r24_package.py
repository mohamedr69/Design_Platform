"""Checker for review24/: manifest complete, markdown links, trees unchanged (no application change), harness v4.2 files
equal the hashes frozen BEFORE the final validation, scoring files equal review22's frozen v4, reviewer files unchanged,
earlier packages (review13..review23) and labels unchanged, recorded tests (journal unit 23 / lifecycle 5 / runner 8 /
boundary 7 / scorer 19 green; the reviewer's provider regressions 1 failed on v4.1 and 3 passed on v4.2), the critical
and provider evidence flags kept apart, and the live ledger untouched (128 settled original-experiment entries; no
r21..r24 live scope). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review24")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.glob("*.md"):
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
res["harness_frozen"] = {"frozen_before_final_validation": fz.get("frozen_before_final_validation") is True,
                         "packaged_files_equal_frozen_hashes": all(sha(PKG / "harness-v4.2" / f) == h for f, h in fz["files"].items()),
                         "workspace_files_equal_frozen_hashes": all(sha(pathlib.Path("C:/t/iso/work/r2x/review24/harness-v4.2") / f) == h for f, h in fz["files"].items()),
                         "runner": fz["runner_version"], "lifecycle": fz["lifecycle_contract"], "journal": fz["journal_version"],
                         "scoring_files_unchanged_vs_review22": all(fz["scoring_files_unchanged_vs_review22"].values()), "changed_vs_v4_1": fz["changed_vs_review23_v4_1"], "new_vs_v4_1": fz["new_vs_review23_v4_1"],
                         "durable_allowance_module_unchanged": sha(fz["durable_allowance_module"]["file"]) == fz["durable_allowance_module"]["sha256"]}
res["reviewer_files_unchanged"] = all((MR / "reviews/M2-review-24" / n).exists() and sha(MR / "reviews/M2-review-24" / n) == h for n, h in b["reviewer_files_review24"].items())
res["reviewer_runner_is_submitted_v4_1"] = b["reviewer_arm_ev_equals_review23_frozen"]
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


green = lambda n: {"tests": n, "failures": 0, "errors": 0, "skipped": 0}
t = {"PROVIDER-JOURNAL": junit(PKG / "harness-v4.2/logs/PROVIDER-JOURNAL.xml"), "LIFECYCLE-V4.1": junit(PKG / "harness-v4.2/logs/LIFECYCLE-V4.1.xml"), "RUNNER-V4": junit(PKG / "harness-v4.2/logs/RUNNER-V4.xml"),
     "BOUNDARY-V4.2": junit(PKG / "harness-v4.2/logs/BOUNDARY-V4.2.xml"), "HARNESS-V4": junit(PKG / "harness-v4.2/logs/HARNESS-V4.xml"),
     "REVIEWER-PROVIDER-on-v4.1": junit(PKG / "repro/on-v4.1/REVIEW24-REGRESSIONS.xml"), "REVIEWER-PROVIDER-on-v4.2": junit(PKG / "repro/on-v4.2/REVIEW24-REGRESSIONS.xml")}
res["tests"] = t
res["tests_ok"] = (t["PROVIDER-JOURNAL"] == green(23) and t["LIFECYCLE-V4.1"] == green(5) and t["RUNNER-V4"] == green(8) and t["BOUNDARY-V4.2"] == green(7) and t["HARNESS-V4"] == green(19)
                   and t["REVIEWER-PROVIDER-on-v4.1"] == {"tests": 3, "failures": 1, "errors": 0, "skipped": 0} and t["REVIEWER-PROVIDER-on-v4.2"] == green(3))
life = load(PKG / "lifecycle-evidence/LIFECYCLE.json")["scenarios"]
bound = load(PKG / "boundary-evidence/BOUNDARY.json")["scenarios"]
allok = lambda s: all(s["checks"].values())
res["critical_stop_evidence"] = {k: allok(life[k]) for k in ("T1_critical_stop_then_plain_resume", "T2_repeated_resume", "T3_terminal_stop_no_remaining_project", "T5a_killed_before_stop_persisted", "T5b_killed_after_stop_file_before_manifest")}
res["provider_stop_evidence"] = {**{k: allok(v) for k, v in bound.items()}, "T4_three_consecutive_provider_failures": allok(life["T4_three_consecutive_provider_failures"]),
                                 "T4b_single_failed_request_is_not_terminal": allok(life["T4b_single_failed_request_is_not_terminal"])}
ev = load(PKG / "runner-evidence/RUNNER-INTEGRATION.json")["scenarios"]
res["runner_controls"] = {"S2_kill_resume_only_remaining_allowance": ev["S2_kill_resume"]["resumed"]["six_page_doc"]["capped_at_12"] and ev["S2_kill_resume"]["resumed"]["one_page_doc_not_resent"],
                          "S5_cache_hits_charge_nothing": all(v["fresh_equals_charge_delta"] for v in ev["S5_cache_hit"]["per_document"].values()),
                          "S7_deferral_resumes_when_eligible": ev["S7_deferral"]["first"]["zero_requests_for_deferred_project"] and ev["S7_deferral"]["resumed"]["status"] == "completed",
                          "S1_S3_S4_S6_S8": ev["S1_baseline"]["charged_equals_sent"] and ev["S3_new_tag"]["refused"]["refused_before_dispatch"] and ev["S4_second_writer"]["second_refused_before_dispatch"]
                          and ev["S6_scope_exhaust"]["exhaustion_is_a_budget_stop"] and ev["S8_refusals"]["both_refused_before_dispatch"]}
p1, p2 = load(PKG / "repro/on-v4.1/PROVIDER-BOUNDARY-PROBE.json"), load(PKG / "repro/on-v4.2/PROVIDER-BOUNDARY-PROBE.json")
res["reviewer_probe"] = {"v4_1_before_file": {k: p1["before_file"][k] for k in ("initial_exit", "resume_exit", "new_sends", "resume_status")},
                         "v4_2_before_file": {k: p2["before_file"][k] for k in ("initial_exit", "resume_exit", "new_sends", "resume_status")},
                         "v4_2_after_file_control": {k: p2["after_file"][k] for k in ("resume_exit", "new_sends", "resume_status")}}
L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = L.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
live = L.execute("select count(*) from entries where scope like 'r2%-four-arm%' or scope like 'r22%' or scope like 'r23%' or scope like 'r24%'").fetchone()[0]
scopes = [s for (s,) in L.execute("select scope from scopes") if s.startswith(("r22", "r21-four-arm", "r23", "r24"))]
L.close()
res["ledger"] = {"settled_original_experiment": settled, "r21_to_r24_live_entries": live, "r21_to_r24_live_scopes": scopes}
rp = res["reviewer_probe"]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(v for v in res["trees"].values() if isinstance(v, bool))
             and all(v for k, v in res["harness_frozen"].items() if isinstance(v, bool)) and res["reviewer_files_unchanged"] and res["reviewer_runner_is_submitted_v4_1"]
             and all(earlier.values()) and res["labels_r21_unchanged"] and all(res["dry_inputs_unchanged"].values()) and res["tests_ok"]
             and all(res["critical_stop_evidence"].values()) and all(res["provider_stop_evidence"].values()) and all(res["runner_controls"].values())
             and rp["v4_1_before_file"] == {"initial_exit": 98, "resume_exit": 0, "new_sends": 16, "resume_status": "completed"}
             and rp["v4_2_before_file"] == {"initial_exit": 98, "resume_exit": 4, "new_sends": 0, "resume_status": "stopped"}
             and rp["v4_2_after_file_control"] == {"resume_exit": 4, "new_sends": 0, "resume_status": "stopped"} and settled == 128 and live == 0 and not scopes)
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "tests"}, indent=1, default=str)[:4000])
print("tests", t)
print("OK" if res["ok"] else "NOT OK")
