"""The Review 12 planned full run vs the Review 11 and Review 10 runs: counts, every failure by test identity and
message, the sync-worker test that timed out in Review 11, and per-module test / skip deltas."""
import collections
import json
import xml.etree.ElementTree as ET

RUNS = {"review10 (a34d3f8)": "C:/t/iso/work/r10/suite/r10__suite_full_frozen_hermetic.xml",
        "review11 (a977364)": "C:/t/iso/work/r11/suite/r11__suite_full_frozen_hermetic.xml",
        "review12 (3d5607d)": "C:/t/iso/work/r12/suite/r12__suite_full_frozen_hermetic.xml"}


def load(path):
    cases = list(ET.parse(path).getroot().iter("testcase"))
    fails, mods, skips, sync = {}, collections.Counter(), collections.Counter(), None
    for tc in cases:
        key = f"{tc.get('classname')}::{tc.get('name')}"
        mods[tc.get("classname")] += 1
        skips[tc.get("classname")] += tc.find("skipped") is not None
        node = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if node is not None:
            fails[key] = {"kind": node.tag, "message": (node.get("message") or "").strip().splitlines()[0][:160]}
        if tc.get("name") == "test_two_worker_processes_cannot_both_claim":
            sync = {"status": "failed" if node is not None else "passed", "seconds": round(float(tc.get("time")), 1)}
    counts = {"tests": len(cases), "failed": sum(c.find("failure") is not None for c in cases),
              "errors": sum(c.find("error") is not None for c in cases), "skipped": sum(c.find("skipped") is not None for c in cases)}
    counts["passed"] = counts["tests"] - counts["failed"] - counts["errors"] - counts["skipped"]
    return counts, fails, mods, skips, sync


data = {k: load(v) for k, v in RUNS.items()}
out = {"counts": {k: v[0] for k, v in data.items()}, "sync_worker_claim_test": {k: v[4] for k, v in data.items()}, "failures": {}}
r10, r11, r12 = (data[k] for k in RUNS)
for test in sorted(set(r10[1]) | set(r11[1]) | set(r12[1])):
    out["failures"][test] = {k: data[k][1].get(test) for k in RUNS}
out["module_delta_vs_review11"] = {m: (r11[2].get(m, 0), r12[2].get(m, 0)) for m in set(r11[2]) | set(r12[2]) if r11[2].get(m, 0) != r12[2].get(m, 0)}
out["skip_delta_vs_review11"] = {m: (r11[3].get(m, 0), r12[3].get(m, 0)) for m in set(r11[3]) | set(r12[3]) if r11[3].get(m, 0) != r12[3].get(m, 0)}
out["review12_failures_identical_to_review10"] = all(r12[1][t] == r10[1].get(t) for t in r12[1])
json.dump(out, open("C:/t/iso/work/r12/suite_analysis/comparison.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
