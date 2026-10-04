"""Every failure of the Review 11 frozen run against the Review 10 frozen run: by test identity and failure message."""
import json
import xml.etree.ElementTree as ET


def failures(path):
    out = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        node = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if node is not None:
            msg = (node.get("message") or "").strip().splitlines()[0][:200]
            out[f"{tc.get('classname')}::{tc.get('name')}"] = {"kind": node.tag, "message": msg}
    return out


def counts(path):
    cases = list(ET.parse(path).getroot().iter("testcase"))
    return {"tests": len(cases), "failed": sum(c.find("failure") is not None for c in cases),
            "errors": sum(c.find("error") is not None for c in cases), "skipped": sum(c.find("skipped") is not None for c in cases)}


r10 = "C:/t/iso/work/r10/suite/r10__suite_full_frozen_hermetic.xml"
r11 = "C:/t/iso/work/r11/suite/r11__suite_full_frozen_hermetic.xml"
a, b = failures(r10), failures(r11)
result = {"review10_counts": counts(r10), "review11_counts": counts(r11), "failures": {}}
for test in sorted(set(a) | set(b)):
    result["failures"][test] = {"review10": a.get(test), "review11": b.get(test),
                                "same_identity_and_message": a.get(test) == b.get(test)}
print(json.dumps(result, indent=1))
json.dump(result, open("C:/t/iso/work/r11/investigation/failure-comparison.json", "w", encoding="utf-8"), indent=1)
