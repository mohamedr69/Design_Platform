import math, re
from collections import Counter
import ezdxf
from ezdxf import disassemble
DXF = r"<PC-B user profile>\AppData\Local\Temp\claude\g--dev--2--dev\6f67ec6f-cb75-49d6-9946-10047734e054\scratchpad\rdm1\src\EP-30880\source.dxf"
NOT_WALLS = re.compile(r"GRID|AXIS|DIM|TEXT|NAME|ANNO|TAG|FURN|CAR|PARK|SYMBOL|FIRE|ALARM|SPK|SPEAKER|LIGHT|\bEM\b|-EM"
                       r"|EXIT|SIGN|DOOR|WIN|TITLE|LEVEL|ROOM|HATCH|ARROW|STAIR", re.I)
doc = ezdxf.readfile(DXF)
inv = Counter(); tot = 0
for e in disassemble.recursive_decompose(doc.modelspace()):
    if e.dxftype() not in ("LINE","LWPOLYLINE","POLYLINE"): continue
    lay = e.dxf.get("layer","") or ""
    if NOT_WALLS.search(lay): continue
    try: vs = list(disassemble.make_primitive(e).vertices())
    except Exception: continue
    for a,b in zip(vs, vs[1:]):
        if math.hypot(b.x-a.x,b.y-a.y) < 0.3: continue
        tot += 1
        if e.dxf.get("invisible",0): inv[lay] += 1
print("total", tot, "invisible-flag segments", sum(inv.values()), inv.most_common(5))
