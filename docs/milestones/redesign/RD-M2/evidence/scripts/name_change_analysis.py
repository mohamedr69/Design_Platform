"""Explain existing INSERTs whose block name differs between the source read-back and the
output read-back (both made by the same Core Console). Read-only on the isolated DXFs."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import ezdxf

root = Path(sys.argv[1])
red = root / "uploads" / "EP-30880" / "redesign"
src_path = next(red.glob("source-readback-*.dxf"))
runs = sorted((red / "runs").iterdir(), key=lambda p: p.stat().st_mtime)
out_path = next(r / "readback.dxf" for r in runs if (r / "readback.dxf").is_file())
a, b = ezdxf.readfile(src_path), ezdxf.readfile(out_path)
ma = {e.dxf.handle: e for e in a.modelspace()}
mb = {e.dxf.handle: e for e in b.modelspace()}


def content(doc, name):
    """A block definition's content, independent of its name and handles: entity types,
    layers and geometry-ish attributes, sorted."""
    blk = doc.blocks.get(name)
    if blk is None:
        return None
    items = []
    for e in blk:
        d = {k: v for k, v in e.dxfattribs().items() if k not in ("handle", "owner")}
        items.append(repr((e.dxftype(), sorted((k, repr(v)) for k, v in d.items()))))
    return hashlib.sha256("\n".join(sorted(items)).encode()).hexdigest()


rows = []
for h in set(ma) & set(mb):
    x, y = ma[h], mb[h]
    if x.dxftype() == "INSERT" and y.dxftype() == "INSERT" and x.dxf.name != y.dxf.name:
        da = {k: v for k, v in x.dxfattribs().items() if k != "name"}
        db = {k: v for k, v in y.dxfattribs().items() if k != "name"}
        rows.append({"handle": h, "old": x.dxf.name, "new": y.dxf.name, "both_anonymous": x.dxf.name.startswith("*") and y.dxf.name.startswith("*"),
                     "other_attribs_equal": da == db, "same_block_content": content(a, x.dxf.name) == content(b, y.dxf.name),
                     "old_name_still_defined_in_output": y.doc.blocks.get(x.dxf.name) is not None})
other = []
for h in set(ma) & set(mb):
    x, y = ma[h], mb[h]
    if x.dxftype() != y.dxftype() or (x.dxfattribs() != y.dxfattribs() and not (x.dxftype() == "INSERT" and x.dxf.name != y.dxf.name)):
        other.append(h)
summary = {"name_changed": len(rows), "all_anonymous": all(r["both_anonymous"] for r in rows),
           "all_other_attribs_equal": all(r["other_attribs_equal"] for r in rows),
           "all_same_block_content": all(r["same_block_content"] for r in rows),
           "old_prefix": dict(Counter(r["old"][:2] for r in rows)), "new_prefix": dict(Counter(r["new"][:2] for r in rows)),
           "other_changed_entities": len(other), "examples": rows[:8],
           "content_mismatch": [r for r in rows if not r["same_block_content"]][:10]}
(root / "evidence").mkdir(exist_ok=True)
(root / "evidence" / "name-change-analysis.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1), encoding="utf-8")
print(json.dumps(summary, indent=1))
