"""Zoomed crop of a staged source page for labelling (no model call): crop.py Dnn page x0 y0 x1 y1 [px]
Region in fractions of the DISPLAYED page (0..1, origin top-left). Renders from the hash-checked staged bytes at a scale
that gives the crop's long side `px` pixels (default 1600). Writes renders/crops/Dnn-pP-x0_y0_x1_y1.png and prints its
path and sha256; the crop log renders/crops/CROPS.jsonl records every crop used as label evidence."""
import hashlib
import json
import pathlib
import sys

import pymupdf

R = pathlib.Path(__file__).parent
did, pno = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7])
px = int(sys.argv[7]) if len(sys.argv) > 7 else 1600
rot = int(sys.argv[8]) if len(sys.argv) > 8 else 0          # optional: rotate the crop for reading (degrees counter-clockwise)
meta = {d["id"]: d for d in json.loads((R / "renders/RENDERS.json").read_text(encoding="utf-8"))["documents"]}[did]
st = {f["doc_key"]: f for f in json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))["files"]}
LONG = "\\\\?\\"
b = open(LONG + st[meta["doc"]]["path"], "rb").read()
assert hashlib.sha256(b).hexdigest() == meta["sha256"]
doc = pymupdf.open(stream=b, filetype="pdf")
page = doc[pno - 1]
W, H = page.rect.width, page.rect.height                      # displayed (rotation applied)
clip_disp = pymupdf.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
clip = clip_disp                                               # get_pixmap(clip=) takes displayed (rotated) page coordinates
scale = px / max(clip_disp.width, clip_disp.height)
pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip)
out = R / "renders/crops"
out.mkdir(parents=True, exist_ok=True)
f = out / f"{did}-p{pno}-{x0:.2f}_{y0:.2f}_{x1:.2f}_{y1:.2f}{'-r' + str(rot) if rot else ''}.png"
pix.save(f)
if rot:
    from PIL import Image
    Image.open(f).rotate(rot, expand=True).save(f)
h = hashlib.sha256(f.read_bytes()).hexdigest()
with open(out / "CROPS.jsonl", "a", encoding="utf-8") as log:
    log.write(json.dumps({"id": did, "page": pno, "region": [x0, y0, x1, y1], "rotate_for_reading": rot, "png": f.name, "sha256": h, "source_sha256": meta["sha256"]}) + "\n")
print(f, h[:16])
