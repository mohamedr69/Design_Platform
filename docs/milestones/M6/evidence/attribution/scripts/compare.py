"""Compare the M6 full suite with the M4 Windows run 2 baseline and the two
runs that roadmap/u2 merged (M5 safe-Apply, M8 wall index), by failing test
name and message; write full-suite-comparison.json beside the run (ORCH-043)."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

WT = Path("G:/dev (2)/dev/ep-platform-merged/wt-m6")
BASE = WT / "docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.xml"
OTHERS = {"m5": WT / "docs/milestones/M5/evidence/safe-apply/full-suite.xml",
          "m8": WT / "docs/milestones/M8/evidence/wall-index/full-suite.xml"}
RUN = WT / "docs/milestones/M6/evidence/attribution/full-suite.xml"


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
    totals["time_s"] = float(suite.get("time", 0))
    return totals, bad, names


def rel(path: Path) -> str:
    return str(path.relative_to(WT)).replace("\\", "/")


base_totals, base_bad, base_names = read(BASE)
run_totals, run_bad, run_names = read(RUN)
out = {"baseline": {"file": rel(BASE), "totals": base_totals, "failing": base_bad},
       "m6": {"file": rel(RUN), "totals": run_totals, "failing": run_bad},
       "new_failures_vs_baseline": sorted(set(run_bad) - set(base_bad)),
       "fixed_since_baseline": sorted(set(base_bad) - set(run_bad)),
       "same_name_vs_baseline": {k: {"same_message": base_bad[k]["message"][:120] == run_bad[k]["message"][:120]}
                                 for k in sorted(set(base_bad) & set(run_bad))},
       "tests_missing_vs_baseline": sorted(base_names - run_names),
       "tests_added_vs_baseline": len(run_names - base_names),
       "tests_added_m6": sorted(n for n in run_names - base_names if "test_m6_attribution" in n)}
for label, path in OTHERS.items():
    totals, bad, names = read(path)
    out[label] = {"file": rel(path), "totals": totals, "failing": bad,
                  "new_failures_in_m6": sorted(set(run_bad) - set(bad)),
                  "same_name": {k: {"same_message": bad[k]["message"][:120] == run_bad[k]["message"][:120]}
                                for k in sorted(set(bad) & set(run_bad))},
                  "tests_missing_in_m6": sorted(names - run_names)}
path = RUN.with_name("full-suite-comparison.json")
path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("new_failures_vs_baseline", "fixed_since_baseline", "same_name_vs_baseline",
                                      "tests_missing_vs_baseline", "tests_added_vs_baseline")}, indent=1))
for label in ("baseline", "m5", "m8", "m6"):
    print(label, out[label]["totals"], "missing in m6:", len(out[label].get("tests_missing_in_m6", [])),
          "new failures in m6:", out[label].get("new_failures_in_m6"))
