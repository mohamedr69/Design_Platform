"""ORCH-049: compare the full suite on the merged tree (task/m6-merge) with
the ORCH-047 merged-tree result (roadmap/u2 tree c865993a, the owner's work
merged; copied here as baseline-orch047-merged-full.xml) and with the M6
branch's own run (ORCH-043), by test name and failure message; write
full-suite-comparison.json beside this evidence."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1]
WT = EVIDENCE.parents[4]
BASE = EVIDENCE / "baseline-orch047-merged-full.xml"
M6 = WT / "docs/milestones/M6/evidence/attribution/full-suite.xml"
RUN = EVIDENCE / "full-suite.xml"


def read(path: Path) -> tuple[dict, dict, set]:
    root = ET.parse(path).getroot()
    suite = next(root.iter("testsuite"))
    bad, names = {}, set()
    for tc in root.iter("testcase"):
        name = f"{tc.get('classname')}::{tc.get('name')}"
        names.add(name)
        for kind in ("failure", "error"):
            e = tc.find(kind)
            if e is not None:
                bad[name] = {"kind": kind, "message": (e.get("message") or "")[:300]}
    totals = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    totals["time_s"] = float(suite.get("time", 0))
    return totals, bad, names


def rel(path: Path) -> str:
    return str(path.relative_to(WT)).replace("\\", "/")


base_totals, base_bad, base_names = read(BASE)
run_totals, run_bad, run_names = read(RUN)
m6_totals, m6_bad, m6_names = read(M6)
out = {
    "baseline": {"file": rel(BASE), "source": "C:/t/tmp/owner-work/merged-full.xml (ORCH-047, tree c865993a)",
                 "sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(), "totals": base_totals, "failing": base_bad},
    "merged": {"file": rel(RUN), "totals": run_totals, "failing": run_bad},
    "new_failures_vs_baseline": sorted(set(run_bad) - set(base_bad)),
    "fixed_since_baseline": sorted(set(base_bad) - set(run_bad)),
    "same_name_vs_baseline": {k: {"same_message": base_bad[k]["message"][:120] == run_bad[k]["message"][:120]}
                              for k in sorted(set(base_bad) & set(run_bad))},
    "tests_missing_vs_baseline": sorted(base_names - run_names),
    "tests_added_vs_baseline": sorted(run_names - base_names),
    "m6_branch": {"file": rel(M6), "totals": m6_totals, "failing": m6_bad,
                  "tests_missing_in_merged": sorted(m6_names - run_names),
                  "new_failures_in_merged": sorted(set(run_bad) - set(m6_bad))},
}
path = EVIDENCE / "full-suite-comparison.json"
path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("new_failures_vs_baseline", "fixed_since_baseline", "same_name_vs_baseline",
                                      "tests_missing_vs_baseline")}, indent=1))
print("added vs baseline:", len(out["tests_added_vs_baseline"]))
print("baseline", base_totals)
print("merged  ", run_totals)
print("m6 branch", m6_totals, "missing in merged:", out["m6_branch"]["tests_missing_in_merged"],
      "new failures:", out["m6_branch"]["new_failures_in_merged"])
