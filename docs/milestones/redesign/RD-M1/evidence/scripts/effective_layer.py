"""Effective layer + visibility of the wall-index segments in probe windows.

AutoCAD draws an entity on layer "0" inside a block on the layer of the INSERT
that places it; an entity is not plotted when its effective layer, or the layer
of any INSERT above it, is off / frozen / no-plot. ezdxf's recursive_decompose
(as used by walls.build) keeps the raw "0". Reads only the COPIED DXF."""
import json
import math
import os
import sys

import ezdxf

HERE = os.path.dirname(os.path.abspath(__file__))
DXF = os.path.join(HERE, "..", "src", "EP-30880", "source.dxf")
PROBES = json.loads(sys.argv[1])

doc = ezdxf.readfile(DXF)
state = {l.dxf.name: (l.is_on(), l.is_frozen(), bool(l.dxf.get("plot", 1))) for l in doc.layers}


def visible(layer):
    on, frozen, plot = state.get(layer, (True, False, True))
    return on and not frozen and plot


def bbox_hit(a, b, p):
    _, x0, y0, x1, y1 = p
    return max(a[0], b[0]) >= x0 and min(a[0], b[0]) <= x1 and max(a[1], b[1]) >= y0 and min(a[1], b[1]) <= y1


results = {p[0]: [] for p in PROBES}


def walk(entities, parent_layer, chain, depth):
    for e in entities:
        t = e.dxftype()
        raw = e.dxf.get("layer", "0") or "0"
        eff = parent_layer if (raw == "0" and parent_layer) else raw
        if t == "INSERT":
            if depth > 12:
                continue
            try:
                walk(e.virtual_entities(), eff, chain + [(e.dxf.name, eff)], depth + 1)
            except Exception:  # noqa: BLE001
                pass
            continue
        if t not in ("LINE", "LWPOLYLINE", "POLYLINE"):
            continue
        try:
            if t == "LINE":
                pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            elif t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points("xy")]
            else:
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        except Exception:  # noqa: BLE001
            continue
        for a, b in zip(pts, pts[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 0.3:
                continue
            for p in PROBES:
                if bbox_hit(a, b, p):
                    vis = visible(eff) and all(visible(l) for _n, l in chain)
                    results[p[0]].append({"raw_layer": raw, "effective_layer": eff, "visible": vis,
                                          "chain": [n for n, _l in chain][-3:],
                                          "seg": [round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)]})


walk(doc.modelspace(), None, [], 0)
summary = {}
for k, v in results.items():
    agg = {}
    for r in v:
        key = f"{r['raw_layer']} -> {r['effective_layer']} | visible={r['visible']} | via {' > '.join(r['chain'])}"
        agg[key] = agg.get(key, 0) + 1
    summary[k] = agg
json.dump({"summary": summary, "detail": results}, open(os.path.join(HERE, "..", "work", "effective-layers.json"), "w"), indent=1)
print(json.dumps(summary, indent=1)[:5000])
