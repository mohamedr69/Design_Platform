"""Compare the M5 full suite with the M4 Windows run 2 baseline by failing
test name and message; write full-suite-comparison.json beside the run."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

WT = Path("G:/dev (2)/dev/ep-platform-merged/wt-m5")
BASE = WT / "docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.xml"
RUN = WT / "docs/milestones/M5/evidence/safe-apply/full-suite.xml"


def read(path: Path) -> tuple[dict, dict]:
    root = ET.parse(path).getroot()
    suite = next(root.iter("testsuite"))
    bad = {}
    for tc in root.iter("testcase"):
        for kind in ("failure", "error"):
            e = tc.find(kind)
            if e is not None:
                bad[f"{tc.get('classname')}::{tc.get('name')}"] = {"kind": kind,
                                                                   "message": (e.get("message") or "")[:300]}
    totals = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    totals["time_s"] = float(suite.get("time", 0))
    return totals, bad


base_totals, base_bad = read(BASE)
run_totals, run_bad = read(RUN)
out = {"baseline": {"file": str(BASE.relative_to(WT)).replace("\\", "/"), "totals": base_totals,
                    "failing": base_bad},
       "m5": {"file": str(RUN.relative_to(WT)).replace("\\", "/"), "totals": run_totals, "failing": run_bad},
       "new_failures": sorted(set(run_bad) - set(base_bad)),
       "fixed_since_baseline": sorted(set(base_bad) - set(run_bad)),
       "same_name": {k: {"same_message": base_bad[k]["message"][:120] == run_bad[k]["message"][:120]}
                     for k in sorted(set(base_bad) & set(run_bad))}}
path = RUN.with_name("full-suite-comparison.json")
path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("new_failures", "fixed_since_baseline", "same_name")}, indent=1))
print("baseline", base_totals, "m5", run_totals)
