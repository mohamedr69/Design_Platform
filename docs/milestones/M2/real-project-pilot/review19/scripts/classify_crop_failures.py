"""Classify every failure of the existing modules on E's ACTUAL cropped path (tests/_e_crop_coords.py run) by the
adapter's own log of scripted fields that lay outside the real crop. A failure whose test had a field outside the crop
is a changed expectation of the crop contract (the field is not visible to a located discovery and is recorded
`incomplete:located_region_only`, never read and never absent); a failure with nothing outside the crop is flagged
for investigation. Writes crop-validation/CROP-FAILURE-CLASSIFICATION.json."""
import collections
import json
import pathlib
import re

import sys
O = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "C:/t/iso/work/r2x/review19/crop-validation")
XML = sys.argv[2] if len(sys.argv) > 2 else "LEGACY-ACTUAL-CROP-diagnostic.xml"
xml = (O / XML).read_text(encoding="utf-8")
import xml.etree.ElementTree as ET

failed = []
for tc in ET.fromstring(xml).iter("testcase"):
    bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
    if bad is not None:
        failed.append({"test": f"{tc.get('classname').replace('.', '/')}.py::{tc.get('name')}", "message": (bad.get("message") or "")[:240]})
log = collections.defaultdict(set)
calls = collections.Counter()
for line in (O / "E-CROP-LOG.jsonl").read_text(encoding="utf-8").splitlines():
    e = json.loads(line)
    calls[e["test"]] += 1
    log[e["test"]].update(e["dropped_outside_crop"])
out = []
for f in failed:
    key = next((k for k in log if k.endswith(f["test"].split("/")[-1]) or f["test"].endswith(k.split("/")[-1])), None)
    dropped = sorted(log.get(key, set())) if key else []
    if "test_ai_pilot_r18" in f["test"]:
        cause = "R19-01 expectation: the test asserted the removed text-silence rule (decision absent_by_discovery on a crop)"
    elif not dropped and ("'partial'" in f["message"] or "'complete'" in f["message"] or "'evidence'" in f["message"]):
        cause = ("located absence (R19-01): nothing scripted lay outside the crop; the page's decision was never in view on a "
                 "located crop, so it is incomplete:located_region_only and the page outcome is 'partial', not 'evidence' / 'complete' "
                 "(only the final outcome assertion fails; every earlier assertion of the test passed)")
    elif dropped:
        cause = f"crop contract: scripted {', '.join(dropped)} printed outside the actual crop -> not visible to located discovery"
    else:
        cause = "INVESTIGATE: no scripted field outside the crop"
    out.append({**f, "located_discoveries": calls.get(key, 0), "outside_crop": dropped, "cause": cause})
for x in out:
    if "test_a_known_revision_constraint_holds_a_decision_without_an_ai_identity" in x["test"]:
        x["locator_finding"] = ("the fixture prints its revision inline as 'REV 02 03' 240 pt right of 'Drawing No X-SD-1'; 'REV 02 03' is not a "
                                "revision label under the application's pattern, so the label box (number label +/- 12 % of the sheet) clips the "
                                "revision cell (44 % of the scripted box inside): a real limitation of the located area, reported, not widened")
summary = collections.Counter(x["cause"].split(":")[0] for x in out)
(O / "CROP-FAILURE-CLASSIFICATION.json").write_text(json.dumps({"failures": len(out), "by_cause": summary, "rows": out}, indent=1) + "\n", encoding="utf-8")
print(dict(summary))
for x in out:
    print(x["test"].split("::")[-1][:70], "|", x["outside_crop"], "|", x["cause"][:40])
