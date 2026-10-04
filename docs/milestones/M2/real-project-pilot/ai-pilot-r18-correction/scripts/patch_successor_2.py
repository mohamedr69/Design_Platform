"""Successor patch 2 (before freeze): an absence is verified when discovery saw the whole page -- also when the located
area is the whole sheet (found by running the existing modules under E with a whole-sheet locator)."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai2/backend/app/ai/evidence_reader.py")
s = P.read_bytes().decode("utf-8").replace("\r\n", "\n")
pairs = [('''    if not located or not located.get("located"):
        return ABSENT_BY_DISCOVERY''', '''    if not located or not located.get("located") or located.get("whole_page"):
        return ABSENT_BY_DISCOVERY'''),
         ('''            located = {"located": True, "route": route, "clip": [round(v, 2) for v in clip]}''',
          '''            located = {"located": True, "route": route, "clip": [round(v, 2) for v in clip],
                       "whole_page": clip.get_area() >= 0.98 * page.rect.get_area()}''')]
for o, n in pairs:
    assert s.count(o) == 1, o
    s = s.replace(o, n)
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("patched 2")
