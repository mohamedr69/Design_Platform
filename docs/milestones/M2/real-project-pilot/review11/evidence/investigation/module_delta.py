import collections
import xml.etree.ElementTree as ET


def mods(p):
    c, s = collections.Counter(), collections.Counter()
    for tc in ET.parse(p).getroot().iter("testcase"):
        c[tc.get("classname")] += 1
        s[tc.get("classname")] += tc.find("skipped") is not None
    return c, s


(a, sa), (b, sb) = mods("C:/t/iso/work/r10/suite/r10__suite_full_frozen_hermetic.xml"), mods("C:/t/iso/work/r11/suite/r11__suite_full_frozen_hermetic.xml")
print("count delta:", {m: (a.get(m, 0), b.get(m, 0)) for m in set(a) | set(b) if a.get(m, 0) != b.get(m, 0)})
print("skip delta:", {m: (sa.get(m, 0), sb.get(m, 0)) for m in set(sa) | set(sb) if sa.get(m, 0) != sb.get(m, 0)})
