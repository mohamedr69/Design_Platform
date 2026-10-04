"""Labelling helper (before any prediction for these files): for a continuation document (hash-checked staged copy),
print the title-block text runs (application's page_lines, in the title-block zone) and render a region of the
displayed page (fractions) at high resolution. Usage: label_view.py <sha12> <x0> <y0> <x1> <y1> [out.png]"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
import pymupdf  # noqa: E402

from app.services import title_block as tb  # noqa: E402

S = json.loads(pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/CONTINUATION-SAMPLE.json").read_text(encoding="utf-8"))
d = [x for x in S["documents"] if x["sha256"].startswith(sys.argv[1])][0]
data = open("\\\\?\\" + d["staged_path"].replace("/", "\\"), "rb").read()
assert hashlib.sha256(data).hexdigest() == d["sha256"]
page = pymupdf.open(stream=data, filetype="pdf")[0]
w, h = page.rect.width, page.rect.height
lines = tb.page_lines(page)
print(d["doc_key"], "| rotation", page.rotation, "| size", round(w), round(h), "| runs", len(lines))
for l in sorted([l for l in lines if tb._in_zone(l, w, h)], key=lambda l: (round(l.y0 / 10), l.x0))[:400]:
    print(f"  {l.x0:7.1f} {l.y0:7.1f}  {l.text}")
if len(sys.argv) > 5:
    x0, y0, x1, y1 = map(float, sys.argv[2:6])
    clip = pymupdf.Rect(x0 * w, y0 * h, x1 * w, y1 * h)
    zoom = min(300 / 72, 2000 / max(clip.width, clip.height))
    out = sys.argv[6] if len(sys.argv) > 6 else f"C:/t/iso/tmp/lv-{sys.argv[1]}.png"
    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip).save(out)
    print(out)
