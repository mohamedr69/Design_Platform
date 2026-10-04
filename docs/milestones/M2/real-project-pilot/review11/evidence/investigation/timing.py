import datetime
import xml.etree.ElementTree as ET
root = ET.parse("C:/t/iso/work/r11/suite/r11__suite_full_frozen_hermetic.xml").getroot()
suite = root.find("testsuite") if root.tag == "testsuites" else root
start = datetime.datetime.fromisoformat(suite.get("timestamp"))
print("suite start (JUnit timestamp):", start, "| suite time s:", suite.get("time"))
elapsed = 0.0
for tc in suite.iter("testcase"):
    t = float(tc.get("time") or 0)
    if tc.get("name") == "test_two_worker_processes_cannot_both_claim":
        print("failing test begins about", start + datetime.timedelta(seconds=elapsed), "and took", round(t, 1), "s")
    elapsed += t
by_module = {}
for tc in suite.iter("testcase"):
    m = tc.get("classname")
    by_module[m] = by_module.get(m, 0) + float(tc.get("time") or 0)
print("sum of test times s:", round(elapsed))
for m in ("tests.test_sync_worker",):
    print(m, "total s:", round(by_module[m], 1))
