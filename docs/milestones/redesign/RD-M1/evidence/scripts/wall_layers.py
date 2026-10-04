"""Which drawing entities fed the wall index near given model points, and whether
their layers plot. Reads only the COPIED source DXF. Mirrors walls.build's filter
(walls.py:151-187) to attribute each wall segment to its layer."""
import json
import math
import os
import sys
from collections import Counter, defaultdict

import ezdxf
from ezdxf import disassemble

sys.path.insert(0, os.path.dirname(__file__))
HERE = os.path.dirname(os.path.abspath(__file__))
DXF = os.path.join(HERE, "..", "src", "EP-30880", "source.dxf")
NOT_WALLS = __import__("re").compile(
    r"GRID|AXIS|DIM|TEXT|NAME|ANNO|TAG|FURN|CAR|PARK|SYMBOL|FIRE|ALARM|SPK|SPEAKER|LIGHT|\bEM\b|-EM"
    r"|EXIT|SIGN|DOOR|WIN|TITLE|LEVEL|ROOM|HATCH|ARROW|STAIR", __import__("re").I)  # copied from walls.py:25-26

# probe windows in model metres: (label, x0, y0, x1, y1)
PROBES = json.loads(sys.argv[1])

doc = ezdxf.readfile(DXF)
layers = {}
for lay in doc.layers:
    layers[lay.dxf.name] = {"on": lay.is_on(), "frozen": lay.is_frozen(), "plot": bool(lay.dxf.get("plot", 1)),
                            "locked": lay.is_locked()}
hits = defaultdict(Counter)
layer_total = Counter()
kept_total = 0
for e in disassemble.recursive_decompose(doc.modelspace()):
    if e.dxftype() not in ("LINE", "LWPOLYLINE", "POLYLINE"):
        continue
    layer = e.dxf.get("layer", "") or ""
    if NOT_WALLS.search(layer):
        continue
    try:
        vs = list(disassemble.make_primitive(e).vertices())
    except Exception:  # noqa: BLE001
        continue
    for a, b in zip(vs, vs[1:]):
        if math.hypot(b.x - a.x, b.y - a.y) < 0.3:
            continue
        kept_total += 1
        layer_total[layer] += 1
        for label, x0, y0, x1, y1 in PROBES:
            # segment intersects probe window (bbox test)
            if max(a.x, b.x) >= x0 and min(a.x, b.x) <= x1 and max(a.y, b.y) >= y0 and min(a.y, b.y) <= y1:
                hits[label][layer] += 1
out = {"segments_kept_total": kept_total,
       "probes": {k: {lay: {"n": n, **layers.get(lay, {"unknown": True})} for lay, n in v.most_common()} for k, v in hits.items()},
       "non_plotting_layers_in_wall_index": {lay: {"n": n, **layers[lay]} for lay, n in layer_total.most_common()
                                              if lay in layers and (not layers[lay]["on"] or layers[lay]["frozen"] or not layers[lay]["plot"])},
       "top_layers_in_wall_index": layer_total.most_common(25)}
json.dump(out, open(os.path.join(HERE, "..", "work", "wall-layers.json"), "w"), indent=1)
print(json.dumps(out, indent=1)[:6000])
