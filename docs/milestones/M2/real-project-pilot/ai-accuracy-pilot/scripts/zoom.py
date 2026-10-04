"""Labelling helper: render a region (fractions of the displayed page) of a pilot document's hash-checked staged copy
at high resolution, optionally rotated for reading. Usage: zoom.py <sha12> <page> <x0> <y0> <x1> <y1> [rotate_deg] [out]"""
import hashlib
import json
import pathlib
import sys

import pymupdf
from PIL import Image

W = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
docs = {d["sha256"][:12]: d for d in json.loads((W / "PILOT-SAMPLE.json").read_text(encoding="utf-8"))["documents"]}
extra = {"6153dfe701f5": None}
tag, page_no = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = map(float, sys.argv[3:7])
rot = int(sys.argv[7]) if len(sys.argv) > 7 else 0
out = sys.argv[8] if len(sys.argv) > 8 else f"C:/t/iso/tmp/zoom-{tag}-{page_no}.png"
if tag in docs:
    path, sha = docs[tag]["staged_path"], docs[tag]["sha256"]
else:
    m = json.loads(pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
    d = [b for b in m["boq_candidates"] + m["documents"] if (b.get("sha256") or "").startswith(tag)][0]
    path, sha = d["staged_path"], d["sha256"]
data = open("\\\\?\\" + path.replace("/", "\\"), "rb").read()
assert hashlib.sha256(data).hexdigest() == sha
page = pymupdf.open(stream=data, filetype="pdf")[page_no - 1]
r = page.rect
clip = pymupdf.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
zoom = min(300 / 72, 2400 / max(clip.width, clip.height))
pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
if rot:
    img = img.rotate(rot, expand=True)
img.save(out)
print(out, img.size)
