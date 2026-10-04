"""Zoomed crop of a STAGED pool page for labelling (no model call). Recipe CROP-R32-1: PyMuPDF, region given in fractions
of the DISPLAYED page (0..1, origin top-left, /Rotate applied), rendered from the hash-checked staged bytes at a scale
giving the crop's long side `px` pixels (default 1600), optionally rotated for reading (degrees counter-clockwise, 0/90/
180/270, applied to the PNG only). Writes C:/t/r2x/r32-stage/crops/<id>-p<n>-<x0>_<y0>_<x1>_<y1>[-r<rot>].png and appends
the binding (pool id, staged sha256, page, region, px, rotation, recipe, png sha256) to CROPS.jsonl in the work folder.
Usage: crop_r32.py <F###> <page> <x0> <y0> <x1> <y1> [px] [rot]"""
import datetime
import hashlib
import json
import pathlib
import sys

import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
pid, pno = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7])
px = int(sys.argv[7]) if len(sys.argv) > 7 else 1600
rot = int(sys.argv[8]) if len(sys.argv) > 8 else 0
man = {}
for f in ("SOURCE-MANIFEST.json", "SOURCE-MANIFEST.extension-1.json", "SOURCE-MANIFEST.extension-2.json"):
    if (HERE / f).exists():
        man |= {r["pool_id"]: r for r in json.loads((HERE / f).read_text(encoding="utf-8"))["files"]}
m = man[pid]
b = pathlib.Path(m["staged_path"]).read_bytes()
assert hashlib.sha256(b).hexdigest() == m["staged_sha256"]
doc = pymupdf.open(stream=b, filetype="pdf")
page = doc[pno - 1]
W, H = page.rect.width, page.rect.height
disp = pymupdf.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
clip = disp                                                   # get_pixmap(clip=) takes displayed (rotated) page coordinates (verified)
scale = px / max(disp.width, disp.height)
pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip)
if rot:
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(pix.tobytes("png"))).rotate(rot, expand=True)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
else:
    data = pix.tobytes("png")
out = pathlib.Path("C:/t/r2x/r32-stage/crops")
out.mkdir(parents=True, exist_ok=True)
name = f"{pid}-p{pno}-{x0:g}_{y0:g}_{x1:g}_{y1:g}" + (f"-r{rot}" if rot else "") + ".png"
(out / name).write_bytes(data)
h = hashlib.sha256(data).hexdigest()
with open(HERE / "CROPS.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"pool_id": pid, "staged_sha256": m["staged_sha256"], "page": pno, "region_display_fraction": [x0, y0, x1, y1], "px": px, "rotate_ccw": rot,
                        "recipe": "CROP-R32-1", "png": name, "sha256": h, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}) + "\n")
print(str(out / name), h)
