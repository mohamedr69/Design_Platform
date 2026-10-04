"""Locate text on a STAGED pool page (no model call): print the page's text-layer words (optionally only those matching a
regular expression) with their positions in fractions of the DISPLAYED page (0..1, origin top-left), so a crop can be
taken there and the value confirmed visually. The text layer locates; only a visible rendering is label evidence.
Usage: words_r32.py <F###> <page> [regex] [x0 y0 x1 y1]"""
import hashlib
import json
import pathlib
import re
import sys

import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
pid, pno = sys.argv[1], int(sys.argv[2])
pat = re.compile(sys.argv[3], re.I) if len(sys.argv) > 3 and sys.argv[3] else None
box = [float(v) for v in sys.argv[4:8]] if len(sys.argv) > 7 else None
man = {}
for f in ("SOURCE-MANIFEST.json", "SOURCE-MANIFEST.extension-1.json", "SOURCE-MANIFEST.extension-2.json"):
    if (HERE / f).exists():
        man |= {r["pool_id"]: r for r in json.loads((HERE / f).read_text(encoding="utf-8"))["files"]}
m = man[pid]
b = pathlib.Path(m["staged_path"]).read_bytes()
assert hashlib.sha256(b).hexdigest() == m["staged_sha256"]
page = pymupdf.open(stream=b, filetype="pdf")[pno - 1]
W, H = page.rect.width, page.rect.height
rm = page.rotation_matrix
lines = {}
for w in page.get_text("words"):
    r = pymupdf.Rect(w[:4]) * rm
    fx0, fy0, fx1, fy1 = r.x0 / W, r.y0 / H, r.x1 / W, r.y1 / H
    if box and not (box[0] <= fx0 <= box[2] and box[1] <= fy0 <= box[3]):
        continue
    key = (w[5], w[6])
    lines.setdefault(key, []).append((fx0, fy0, fx1, fy1, w[4]))
for key, ws in sorted(lines.items(), key=lambda kv: (round(min(x[1] for x in kv[1]), 3), min(x[0] for x in kv[1]))):
    text = " ".join(x[4] for x in ws)
    if pat and not pat.search(text):
        continue
    print(f"[{min(x[0] for x in ws):.3f},{min(x[1] for x in ws):.3f},{max(x[2] for x in ws):.3f},{max(x[3] for x in ws):.3f}] {text}")
