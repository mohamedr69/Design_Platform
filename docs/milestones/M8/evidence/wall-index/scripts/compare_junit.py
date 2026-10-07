"""ORCH-036 evidence: compare a full-suite JUnit XML with the M4 Windows
baseline by test name and failure message. Usage (from wt-m8):
    python -B docs/milestones/M8/evidence/wall-index/scripts/compare_junit.py BASE.xml NEW.xml OUT.json
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET


def read(path: str) -> dict:
    root = ET.parse(path).getroot()
    out = {}
    for case in root.iter("testcase"):
        name = f"{case.get('classname')}::{case.get('name')}"
        state, message = "passed", ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                state = tag
                message = (node.get("message") or "").strip().splitlines()[0][:300] if node.get("message") else ""
                break
        out[name] = {"state": state, "message": message}
    return out


def counts(cases: dict) -> dict:
    c: dict = {}
    for v in cases.values():
        c[v["state"]] = c.get(v["state"], 0) + 1
    c["total"] = len(cases)
    return c


def main(base: str, new: str, out: str) -> None:
    a, b = read(base), read(new)
    bad = ("failure", "error")
    diff = {
        "baseline": base, "new": new, "baseline_counts": counts(a), "new_counts": counts(b),
        "failing_in_both_same_message": sorted(n for n in a if a[n]["state"] in bad and n in b
                                               and b[n]["state"] in bad and a[n]["message"] == b[n]["message"]),
        "failing_in_both_message_changed": {n: {"baseline": a[n]["message"], "new": b[n]["message"]} for n in sorted(a)
                                            if a[n]["state"] in bad and n in b and b[n]["state"] in bad
                                            and a[n]["message"] != b[n]["message"]},
        "newly_failing": {n: b[n] for n in sorted(b) if b[n]["state"] in bad and (n not in a or a[n]["state"] not in bad)},
        "fixed_or_gone": {n: {"baseline": a[n], "new": b.get(n)} for n in sorted(a)
                          if a[n]["state"] in bad and (n not in b or b[n]["state"] not in bad)},
        "only_in_new": sorted(set(b) - set(a)),
        "only_in_baseline": sorted(set(a) - set(b)),
        "skip_changes": {n: {"baseline": a[n]["state"], "new": b[n]["state"]} for n in sorted(set(a) & set(b))
                         if (a[n]["state"] == "skipped") != (b[n]["state"] == "skipped")},
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(diff, f, indent=1)
    print(json.dumps({k: (v if not isinstance(v, (list, dict)) or len(v) < 40 else f"{len(v)} items")
                      for k, v in diff.items()}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
