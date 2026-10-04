"""Checker for review22/: manifest complete (no mismatch, missing or unlisted file), markdown links, bindings (accepted /
reviewed / frozen trees clean and unchanged; no application change; harness v4 frozen hashes equal the packaged files;
reviewer files unchanged), earlier packages unchanged, the draft declaration marked NOT EXECUTED with no approved budget and
bound to the frozen candidate / sample / stage / labels manifest / workload v2 / harness contract, the three request
figures kept apart, recorded test results (harness v4 19 / runner v4 8 / v3 unchanged 13 / r16.1 66 all green; the
reviewer's regressions 2 failed on the submitted harness and 5 passed on v4), replay deltas (r21 dry recovery unchanged
with correct sources, no credit under mismatched sources, H-06 replay equal), the runner evidence flags, and the live
ledger untouched (128 settled original-experiment entries; no r22 scope). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review22")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.rglob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":   # written by this checker
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
b = load(PKG / "bindings/SOURCE-BINDINGS.json")
fz = load(PKG / "bindings/FROZEN-HARNESS.json")
res["trees"] = {"accepted": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == b["accepted"]["commit"] and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                "reviewed": git("C:/t/iso/cand-ai3", "rev-parse", "HEAD") == b["reviewed_r19_candidate"]["commit"] and not git("C:/t/iso/cand-ai3", "status", "--porcelain"),
                "frozen_r21_candidate": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == b["frozen_r21_candidate"]["commit"] == "719e8de661b8b10427ef6cff5d2d277a53b64dc6" and not git("C:/t/iso/cand-ai4", "status", "--porcelain"),
                "reader_unchanged": sha("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py") == b["frozen_r21_candidate"]["evidence_reader_sha256"],
                "application_change": b["application_change"]}
res["harness_frozen"] = {"packaged_files_equal_frozen_hashes": all(sha(PKG / "harness-v4" / f) == h for f, h in fz["files"].items()), "contract": fz["contract_version"], "scorer": fz["scorer_version"], "runner": fz["runner_version"],
                         "durable_allowance_module_unchanged": sha(fz["durable_allowance_module"]["file"]) == fz["durable_allowance_module"]["sha256"],
                         "submitted_r21_harness_equals_package": all(sha(PKG / "harness-r21-submitted" / f) == h for f, h in b["submitted_r21_harness"].items())}
res["reviewer_files_unchanged"] = all((MR / "reviews/M2-review-22" / n).exists() and sha(MR / "reviews/M2-review-22" / n) == h for n, h in b["reviewer_files_review22"].items())
earlier = {}
for pk, h in b["earlier_package_manifests"].items():
    mp = PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json"
    m = load(mp)["files"]
    earlier[pk] = sha(mp) == h and all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
res["labels_r21_unchanged"] = all(sha(PKG.parent / "review21/labels-r21" / n) == h for n, h in b["r21_inputs"]["labels_r21_files"].items())
d = load(PKG / "declaration/R22-DECLARATION.draft.json")
w = load(PKG / "workload/R22-WORKLOAD.json")
res["draft"] = {"not_executed": d["executed"] is False and "NOT EXECUTED" in d["status"], "no_budget": d["new_model_budget_approved"] is False,
                "candidate_719e8de": d["code"]["successor"]["commit"] == "719e8de661b8b10427ef6cff5d2d277a53b64dc6", "contract_v4": d.get("harness_contract") == fz["contract_version"],
                "rule_v4": d["project_day"].get("rule_version") == "whole-project-reservation-2026-09-30.v4", "no_static_share": "floor((60" not in json.dumps(d["project_day"]) and "rule_version" in d["project_day"],
                "bound": sha(PKG / "declaration/R21-STAGE.json") == d["stage"]["manifest_sha256"] and all(sha(PKG.parent / "review21/labels-r21" / n) == v for n, v in d["labels"]["files"].items())
                and d["sources"]["sample"]["n_planned"] == 27 and d["workload"] == w and d["code"]["coverage_scorer"]["sha256"] == fz["files"]["score_arms_v4.py"]
                and d["code"]["runners"]["harness-v4/arm_ev.py"] == fz["files"]["arm_ev.py"],
                "caps": d["ledger"]["caps"], "sum_caps": d["ledger"]["sum_caps"]}
f3 = w["budget"]["three_request_figures"]
res["workload_v2"] = {"three_figures": f3, "distinct_and_labelled": f3["expected_workload_requests"] == 509 and f3["proposed_authorized_maximum_requests_IF_APPROVED"] == 688 and f3["uncapped_structural_maximum_requests"] == 1256,
                      "p90_labelled_estimate": "ESTIMATE" in w["budget"]["p90_label"] and "core_p90_based_input_tokens_ESTIMATE" in w["budget"], "price_unknown": w["budget"]["price"].startswith("UNKNOWN"),
                      "schedule_simulated": all(v["complete"] for v in w["schedule"]["simulations"].values()), "elapsed_hours": {k: v["elapsed_hours_to_last_batch_start"] for k, v in w["schedule"]["simulations"].items()},
                      "fake_clock_example_present": isinstance(w["schedule"]["fake_clock_example"]["dry_runner_evidence_S7"], dict)}


def junit(p):
    r = ET.parse(p).getroot()
    s = r if r.tag == "testsuite" else r.find("testsuite")
    return {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}


t = {"HARNESS-V4": junit(PKG / "harness-v4/logs/HARNESS-V4.xml"), "RUNNER-V4": junit(PKG / "harness-v4/logs/RUNNER-V4.xml"), "HARNESS-V3-UNCHANGED": junit(PKG / "tests/HARNESS-V3-UNCHANGED.xml"),
     "R16-HARNESS": junit(PKG / "tests/R16-HARNESS.xml"), "REVIEWER-REGRESSIONS-on-r21": junit(PKG / "repro/on-r21/REVIEW22-REGRESSIONS.xml"), "REVIEWER-REGRESSIONS-on-v4": junit(PKG / "repro/on-v4/REVIEW22-REGRESSIONS.xml")}
res["tests"] = t
res["tests_ok"] = (t["HARNESS-V4"]["tests"] == 19 and t["HARNESS-V4"]["failures"] == t["HARNESS-V4"]["errors"] == 0 and t["RUNNER-V4"]["tests"] == 8 and t["RUNNER-V4"]["failures"] == t["RUNNER-V4"]["errors"] == 0
                   and t["HARNESS-V3-UNCHANGED"]["tests"] == 13 and t["HARNESS-V3-UNCHANGED"]["failures"] == 0 and t["R16-HARNESS"]["tests"] == 66 and t["R16-HARNESS"]["failures"] == t["R16-HARNESS"]["errors"] == 0
                   and t["REVIEWER-REGRESSIONS-on-r21"] == {"tests": 5, "failures": 2, "errors": 0, "skipped": 0} and t["REVIEWER-REGRESSIONS-on-v4"] == {"tests": 5, "failures": 0, "errors": 0, "skipped": 0})
rd = load(PKG / "replays/REPLAY-DELTAS.json")["summary"]
res["replays"] = {**rd, "ok": rd["r21_dry_recovery_unchanged_under_v4_with_correct_sources"] and all(v == 0 for v in rd["r21_dry_mismatched_sources_v4_credited"].values()) and rd["h06_replay_all_json_equal"]}
ev = load(PKG / "runner-evidence/RUNNER-INTEGRATION.json")["scenarios"]
res["runner_evidence"] = {"S1_charged_equals_sent": ev["S1_baseline"]["charged_equals_sent"], "S2_capped_at_12_across_kill_resume": ev["S2_kill_resume"]["resumed"]["six_page_doc"]["capped_at_12"] and ev["S2_kill_resume"]["resumed"]["six_page_doc"]["attempted_beyond_cap"],
                          "S3_new_tag_refused": ev["S3_new_tag"]["refused"]["refused_before_dispatch"], "S4_second_writer_refused": ev["S4_second_writer"]["second_refused_before_dispatch"],
                          "S5_cache_hits_charge_nothing": all(v["fresh_equals_charge_delta"] for v in ev["S5_cache_hit"]["per_document"].values()), "S6_scope_exhaustion_budget_stop": ev["S6_scope_exhaust"]["exhaustion_is_a_budget_stop"],
                          "S7_deferred_zero_requests_then_resumed": ev["S7_deferral"]["first"]["zero_requests_for_deferred_project"] and ev["S7_deferral"]["resumed"]["status"] == "completed",
                          "S8_refusals_before_dispatch": ev["S8_refusals"]["both_refused_before_dispatch"]}
L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = L.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
r22 = L.execute("select count(*) from entries where scope like 'r22%' or scope like 'r21-four-arm%'").fetchone()[0]
scopes = [s for (s,) in L.execute("select scope from scopes") if s.startswith(("r22", "r21-four-arm"))]
L.close()
res["ledger"] = {"settled_original_experiment": settled, "r21_r22_live_entries": r22, "r21_r22_live_scopes": scopes}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken
             and all(v for k, v in res["trees"].items() if isinstance(v, bool)) and res["harness_frozen"]["packaged_files_equal_frozen_hashes"] and res["harness_frozen"]["durable_allowance_module_unchanged"]
             and res["harness_frozen"]["submitted_r21_harness_equals_package"] and res["reviewer_files_unchanged"] and all(earlier.values()) and res["labels_r21_unchanged"]
             and all(v for k, v in res["draft"].items() if isinstance(v, bool)) and all(v for k, v in res["workload_v2"].items() if isinstance(v, bool)) and res["tests_ok"] and res["replays"]["ok"]
             and all(res["runner_evidence"].values()) and settled == 128 and r22 == 0 and not scopes)
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in ("tests",)}, indent=1, default=str)[:3000])
print("tests", t)
print("OK" if res["ok"] else "NOT OK")
