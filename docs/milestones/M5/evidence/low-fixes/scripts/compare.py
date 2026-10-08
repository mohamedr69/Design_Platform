"""Compare the ORCH-041 full suite with the M4 Windows run 2 baseline and with
the ORCH-039 (M5 safe-Apply) full suite, by test name, state and failing
message; write full-suite-comparison.json beside the run."""
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

WT = Path("G:/dev (2)/dev/ep-platform-merged/wt-m5b")
EV = WT / "docs/milestones/M5/evidence"
RUN = EV / "low-fixes/full-suite.xml"
BASES = {"m4_run2": WT / "docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.xml",
         "orch039": EV / "safe-apply/full-suite.xml"}


def read(path: Path):
    root = ET.parse(path).getroot()
    suite = next(root.iter("testsuite"))
    states, bad = {}, {}
    for tc in root.iter("testcase"):
        name = f"{tc.get('classname')}::{tc.get('name')}"
        state = "passed"
        for kind in ("failure", "error", "skipped"):
            e = tc.find(kind)
            if e is not None:
                state = kind
                if kind != "skipped":
                    bad[name] = {"kind": kind, "message": (e.get("message") or "")[:300]}
        states[name] = state
    totals = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    totals["time_s"] = float(suite.get("time", 0))
    return totals, states, bad


def failing_set_items(message: str) -> list[str]:
    """The 'Extra items' a set comparison printed, in sorted order (their print order is hash order)."""
    return sorted(line.strip().strip("'") for line in message.split("Extra items in the left set:")[-1].splitlines()
                  if line.strip().startswith("'")) if "Extra items" in message else []


run_totals, run_states, run_bad = read(RUN)
out = {"run": {"file": RUN.relative_to(WT).as_posix(), "totals": run_totals, "failing": run_bad}, "against": {}}
for key, base in BASES.items():
    totals, states, bad = read(base)
    common = set(states) & set(run_states)
    changed = {n: {"before": states[n], "now": run_states[n]} for n in sorted(common) if states[n] != run_states[n]}
    added = sorted(set(run_states) - set(states))
    out["against"][key] = {
        "file": base.relative_to(WT).as_posix(), "totals": totals,
        "new_failures": sorted(set(run_bad) - set(bad)),
        "fixed_since": sorted(set(bad) - set(run_bad)),
        "missing_now": sorted(set(states) - set(run_states)),
        "added_now_by_file": dict(Counter(n.split("::")[0] for n in added)),
        "added_now_states": dict(Counter(run_states[n] for n in added)),
        "state_changed": changed,
        "same_failure": {n: {"same_message_first_120": bad[n]["message"][:120] == run_bad[n]["message"][:120],
                             "same_extra_items_sorted": failing_set_items(bad[n]["message"])
                             == failing_set_items(run_bad[n]["message"])}
                         for n in sorted(set(bad) & set(run_bad))},
    }
path = RUN.with_name("full-suite-comparison.json")
path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: {x: v[x] for x in ("new_failures", "fixed_since", "missing_now", "added_now_by_file",
                                          "added_now_states", "state_changed", "same_failure")}
                  for k, v in out["against"].items()}, indent=1))
print("run", run_totals)
