"""Offline replay deltas (review 22): (1) the saved R21 four-arm dry outputs scored by the submitted v3 scorer (the stored
review21 package result) and by the v4 scorer (repro/on-v4/score-control, the reviewer's own control call) -- per arm, the
recovery counts, the eligibility the v4 contract reports and the coverage summary; (2) the same under the reviewer's
all-hashes-mismatched declaration (v3 stored in repro/on-r21, v4 in repro/on-v4); (3) the r22 dry four-arm chain scored by
v4 (C:/t/r2x/dry-runs/r22/score); (4) the H-06 replay comparison (h06-replay/H06-REPLAY-DELTAS.json). Writes replays/REPLAY-DELTAS.json."""
import json
import pathlib

R = pathlib.Path("C:/t/iso/work/r2x/review22")
PKG21 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review21")
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
v3_ctrl = load(PKG21 / "dry/score/ARMS-METRICS.v3.json")
v4_ctrl = load(R / "repro/on-v4/score-control/ARMS-METRICS.v4.json")
v3_mis = load(R / "repro/on-r21/score-mismatch/ARMS-METRICS.v3.json")
v4_mis = load(R / "repro/on-v4/score-mismatch/ARMS-METRICS.v4.json")
r22 = load("C:/t/r2x/dry-runs/r22/score/ARMS-METRICS.v4.json")
h06 = load(R / "h06-replay/H06-REPLAY-DELTAS.json")


def rec(m, arm):
    a = m["arms"].get(arm, {})
    if "recovery_all_planned" not in a:
        return {"status": a.get("status")}
    return {f: dict(v["recovery"]) if isinstance(v["recovery"], dict) else v["recovery"] for f, v in a["recovery_all_planned"].items()}


out = {"r21_dry_outputs": {}, "r21_dry_outputs_all_hashes_mismatched": {}, "r22_dry_chain_v4": {}, "h06_replay": h06}
for arm in ("A", "L1", "L2", "L3", "L4"):
    a3, a4 = rec(v3_ctrl, arm), rec(v4_ctrl, arm)
    out["r21_dry_outputs"][arm] = {"v3_recovery": a3, "v4_recovery": a4, "recovery_equal": a3 == a4, "v4_valid_accuracy_claim": v4_ctrl["arms"][arm].get("valid_accuracy_claim"),
                                   "v4_eligibility_counts": v4_ctrl["arms"][arm].get("eligibility_counts"),
                                   "coverage_summary_equal": (v3_ctrl["coverage"].get(arm, {}).get("summary") == v4_ctrl["coverage"].get(arm, {}).get("summary")) if arm != "A" else "n/a"}
    m3, m4 = rec(v3_mis, arm), rec(v4_mis, arm)
    out["r21_dry_outputs_all_hashes_mismatched"][arm] = {"v3_recovery_(defect: credit despite rejected sources)": m3, "v4_recovery": m4, "v4_valid_accuracy_claim": v4_mis["arms"][arm].get("valid_accuracy_claim"),
                                                          "v4_invalid_reason": (v4_mis["arms"][arm].get("recovery_all_planned") or {}).get("identity", {}).get("invalid_reason"),
                                                          "v4_eligibility_counts": v4_mis["arms"][arm].get("eligibility_counts"), "v4_rejected_evidence": len(v4_mis["arms"][arm].get("rejected_evidence") or [])}
    a = r22["arms"].get(arm, {})
    out["r22_dry_chain_v4"][arm] = {"valid_accuracy_claim": a.get("valid_accuracy_claim"), "eligibility_counts": a.get("eligibility_counts"), "requests": (a.get("usage") or {}).get("requests"),
                                    "coverage_summary": (r22["coverage"].get(arm) or {}).get("summary"), "extra_facts_outside_scope": len((r22["coverage"].get(arm) or {}).get("extra_facts_outside_scope") or []),
                                    "runner": a.get("runner"), "recovery": rec(r22, arm)}
out["r22_dry_chain_v4"]["pairs"] = r22.get("pairs")
out["r22_dry_chain_v4"]["no_business_change"] = r22.get("no_business_change")
out["summary"] = {"r21_dry_recovery_unchanged_under_v4_with_correct_sources": all(v["recovery_equal"] for v in out["r21_dry_outputs"].values()),
                  "r21_dry_mismatched_sources_v3_still_credited": {arm: (m.get("identity") or {}).get("recovered_clean") for arm, m in ((a, rec(v3_mis, a)) for a in ("L1", "L2", "L3", "L4"))},
                  "r21_dry_mismatched_sources_v4_credited": {arm: (m.get("identity") or {}).get("recovered_clean", 0) for arm, m in ((a, rec(v4_mis, a)) for a in ("L1", "L2", "L3", "L4"))},
                  "h06_replay_all_json_equal": all(v["json_equal"] for v in h06["files"].values())}
(R / "replays").mkdir(exist_ok=True)
(R / "replays/REPLAY-DELTAS.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(out["summary"], indent=1))
