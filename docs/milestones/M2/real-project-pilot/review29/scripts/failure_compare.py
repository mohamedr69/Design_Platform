"""Compare full-suite failures by test name AND message between the accepted baseline (3d5607d) and the final candidate.
Usage: failure_compare.py <baseline.xml> <candidate.xml> -> logs/FAILURE-COMPARISON.json"""
import json
import pathlib
import sys
import xml.etree.ElementTree as ET


def failures(path):
    root = ET.parse(path).getroot()
    out, totals = {}, {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for suite in root.iter("testsuite"):
        for k in totals:
            totals[k] += int(suite.get(k, 0))
    for case in root.iter("testcase"):
        for tag in ("failure", "error"):
            for f in case.findall(tag):
                name = f"{case.get('classname')}::{case.get('name')}"
                out[name] = {"kind": tag, "message": (f.get("message") or "").strip()[:300]}
    return out, totals


b, bt = failures(sys.argv[1])
c, ct = failures(sys.argv[2])
import re


def norm(msg):
    # Python randomises set iteration order per process (PYTHONHASHSEED): an assertion listing set members prints them in a
    # different order each run. Normalised key: the exception type plus the SORTED set of quoted items in the message.
    return (msg.split(":", 1)[0], sorted(set(re.findall(r"'[^']*'", msg))))


res = {"baseline": {"file": sys.argv[1], "totals": bt, "failures": b}, "candidate": {"file": sys.argv[2], "totals": ct, "failures": c},
       "same_tests": set(b) == set(c), "same_messages_raw": all(b[k]["message"] == c[k]["message"] for k in set(b) & set(c)),
       "same_messages": all(norm(b[k]["message"]) == norm(c[k]["message"]) for k in set(b) & set(c)),
       "only_in_candidate": sorted(set(c) - set(b)), "only_in_baseline": sorted(set(b) - set(c))}
res["identical_failures"] = res["same_tests"] and res["same_messages"]
out = pathlib.Path("C:/t/iso/work/r2x/r29/logs/FAILURE-COMPARISON.json")
out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: res[k] for k in ("same_tests", "same_messages", "same_messages_raw", "only_in_candidate", "only_in_baseline", "identical_failures")}),
      "baseline", bt, "candidate", ct)
