import xml.etree.ElementTree as ET
for label, path in (("review08 full (e02a8c1)", "C:/t/iso/work/r8/suite/r8__suite_full_frozen_hermetic.xml"),
                    ("review09 full (689d95e)", "C:/t/iso/work/r9/suite/r9__suite_full_frozen_hermetic.xml"),
                    ("review10 full (a34d3f8)", "C:/t/iso/work/r10/suite/r10__suite_full_frozen_hermetic.xml"),
                    ("review11 full (a977364)", "C:/t/iso/work/r11/suite/r11__suite_full_frozen_hermetic.xml")):
    root = ET.parse(path).getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    for tc in root.iter("testcase"):
        if tc.get("name") == "test_two_worker_processes_cannot_both_claim":
            status = "failed" if tc.find("failure") is not None or tc.find("error") is not None else "passed"
            print(f"{label}: {status}, {float(tc.get('time')):.1f} s  (whole suite {float(suite.get('time')) / 60:.1f} min)")
