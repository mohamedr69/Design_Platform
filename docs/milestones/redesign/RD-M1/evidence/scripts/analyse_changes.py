"""Read-only analysis of the stored Redesign plan (project_redesign row from the snapshot dump)."""
import json
import math
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(__file__)
CASE = os.path.join(HERE, "..", "work", "case")
row = json.load(open(os.path.join(CASE, "project_redesign.json"), encoding="utf-8"))[0]
changes = row["changes"]
symbols = row["symbols"]


def drawn(c):  # mirrors service._drawn (read, not imported)
    return (c["status"] == "approved" or (c["status"] == "proposed" and c.get("source") != "interface")) \
        and bool(c.get("remove") or c.get("insert"))


out = {}
d = [c for c in changes if drawn(c)]
out["drawn_total"] = len(d)
out["drawn_by_status_source"] = Counter(f"{c['status']}|{c.get('source') or 'review'}|{c['action']}" for c in d)
out["status_by_source"] = Counter(f"{c.get('source') or 'review'}|{c['status']}" for c in changes)
lib = Counter()
stale = []
for c in changes:
    p = (c.get("insert") or {}).get("library")
    if p:
        key = "G-drive" if p.startswith("G:/") else "stale-other-machine"
        lib[f"{key}|{c['status']}|moved={bool(c.get('moved'))}|edited={bool(c.get('edited'))}"] += 1
        if key != "G-drive":
            stale.append({"id": c["id"], "status": c["status"], "moved": c.get("moved"), "edited": c.get("edited"),
                          "code": c["interface"]["code"], "for": c["interface"]["for"], "drawn": drawn(c)})
out["library_paths"] = lib
out["stale_library_changes"] = stale
out["failed_errors"] = Counter((c.get("error") or "")[:110] for c in changes if c["status"] == "failed")
out["placeholders"] = sum(1 for c in changes if c.get("placeholder"))
out["confidence"] = Counter(f"{c.get('source') or 'review'}|{c.get('confidence')}" for c in changes)
out["on_wall"] = Counter(f"{c.get('source') or 'review'}|{c.get('on_wall')}" for c in changes if c.get("insert"))
out["coordinated"] = Counter(f"{c.get('source') or 'review'}|{bool(c.get('coordinated'))}" for c in changes if c.get("insert"))
out["residual"] = sorted({round(c["residual"], 3) for c in changes if c.get("residual") is not None})
out["confirm_flag(review add, residual>1m, not moved)"] = sum(
    1 for c in changes if c.get("insert") and c["action"] == "add" and not c.get("moved")
    and c.get("residual") is not None and c["residual"] > 1.0)
# interface rows: how many modules per row, duplicates by (row, code)
per_row = Counter((c["interface"]["row"], c["interface"]["code"]) for c in changes if c.get("source") == "interface")
out["interface_rows"] = len({c["interface"]["row"] for c in changes if c.get("source") == "interface"})
out["interface_row_code_multi"] = sum(1 for v in per_row.values() if v > 1)
out["interface_by_code"] = Counter(c["interface"]["code"] for c in changes if c.get("source") == "interface")
out["interface_placed_by_page"] = Counter(c["page"] for c in changes if c.get("source") == "interface" and c.get("insert"))
out["sheets_of_changes"] = Counter(f"{c['page']}|{c['sheet']}|{c['floor']}" for c in changes)
# pairwise overlaps among drawn inserts on the same page (approximate: radius / module half sizes)
def box(c):
    ins = c["insert"]
    x, y = ins["seen"]
    face = c.get("interface") or {}
    if face.get("half") and face.get("depth"):
        hw, hh = face["half"], face["depth"]
        if round(float(ins.get("rotation") or 0)) % 180 == 90:
            hw, hh = hh, hw
    else:
        hw = hh = ins.get("radius") or 0.25
    return (x - hw, y - hh, x + hw, y + hh)


def ov(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


placed = [c for c in changes if c.get("insert") and c["insert"].get("seen") and c["insert"].get("block")
          and c["status"] in ("proposed", "approved", "pending")]
pairs = []
for i, a in enumerate(placed):
    for b in placed[i + 1:]:
        if a["page"] == b["page"] and ov(box(a), box(b)):
            pairs.append((a["id"], b["id"], a["status"], b["status"], round(math.dist(a["insert"]["seen"], b["insert"]["seen"]), 3)))
out["overlapping_symbol_pairs_after_coordination(no gap)"] = len(pairs)
out["overlap_examples"] = pairs[:25]
# identical seen points
pts = defaultdict(list)
for c in placed:
    pts[(c["page"], tuple(round(v, 3) for v in c["insert"]["seen"]))].append(c["id"])
out["identical_points"] = {str(k): v for k, v in pts.items() if len(v) > 1}
out["symbols"] = [{k: s.get(k) for k in ("id", "name", "code", "block", "layer", "scale", "count", "facing", "size")} for s in symbols]
json.dump(out, open(os.path.join(HERE, "..", "work", "changes-analysis.json"), "w"), indent=1, default=str)
for k, v in out.items():
    if k in ("symbols", "overlap_examples", "stale_library_changes"):
        continue
    print(k, "=>", v if not isinstance(v, dict) or len(v) < 40 else f"<{len(v)} entries>")
print("stale:", json.dumps(stale, indent=0)[:3000])
