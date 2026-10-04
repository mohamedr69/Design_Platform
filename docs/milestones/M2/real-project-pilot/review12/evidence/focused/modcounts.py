import collections
import glob
import os
import xml.etree.ElementTree as ET
for f in sorted(glob.glob("C:/t/iso/work/r12/focused/*.xml")):
    c, s = collections.Counter(), collections.Counter()
    for tc in ET.parse(f).getroot().iter("testcase"):
        m = tc.get("classname").replace("tests.", "")
        c[m] += 1
        if tc.find("skipped") is not None:
            s[m] += 1
    print(os.path.basename(f), "; ".join(f"{m} {n}" + (f" ({s[m]} skipped)" if s[m] else "") for m, n in sorted(c.items())))
