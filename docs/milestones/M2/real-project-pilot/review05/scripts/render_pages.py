"""Render the pages to label (pages_to_label.json or a given json) from the staged originals: four tiles per sheet,
each tile a whole portrait page (fit 880x990) or, for a drawing-sized page, its right-hand title-block strip.
Usage: render_pages.py <todo.json> <out_dir> [prefix]"""
import json, sys, pathlib
import pymupdf
from PIL import Image, ImageDraw

todo = json.load(open(sys.argv[1])); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True); prefix = sys.argv[3] if len(sys.argv) > 3 else "pg"
frozen = {}
for f in (r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-SAMPLE.json",):
    for d in json.load(open(f, encoding="utf-8"))["documents"]:
        frozen[f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/")] = d
extra = pathlib.Path(sys.argv[1]).with_name("staged_extra.json")
if extra.is_file():
    for k, v in json.load(open(extra)).items(): frozen[k] = v
tiles = []
for doc, pages in todo.items():
    d = frozen[doc]; pdf = pymupdf.open(d["staged_path"])
    for p in pages:
        if p > pdf.page_count: continue
        page = pdf[p - 1]; r = page.rect
        if max(r.width, r.height) > 1300:     # drawing-sized: the title-block strip (right 24 %, or bottom band for portrait drawings)
            clip = pymupdf.Rect(r.width * 0.76, 0, r.width, r.height) if r.width >= r.height else pymupdf.Rect(0, r.height * 0.80, r.width, r.height)
            zoom = min(990 / clip.height, 880 / clip.width) * 1.6
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip); kind = "titleblock"
        else:
            zoom = min(990 / r.height, 880 / r.width) * 1.5
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)); kind = "page"
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples); img.thumbnail((880, 990))
        tiles.append((doc, p, kind, img))
    pdf.close()
index = []
for n, start in enumerate(range(0, len(tiles), 4), 1):
    group = tiles[start:start + 4]; sheet = Image.new("RGB", (1780, 2030), "white"); dr = ImageDraw.Draw(sheet)
    for k, (doc, p, kind, img) in enumerate(group):
        x, y = (k % 2) * 890 + 5, (k // 2) * 1015 + 5
        dr.text((x, y), f"[{start + k}] p{p} {kind} {doc[-70:]}", fill="red"); sheet.paste(img, (x, y + 14))
        index.append({"tile": start + k, "sheet": f"{prefix}-{n:03d}.jpg", "doc": doc, "page": p, "kind": kind})
    sheet.save(OUT / f"{prefix}-{n:03d}.jpg", quality=80)
json.dump(index, open(OUT / f"{prefix}-index.json", "w"), indent=0)
print("tiles", len(tiles), "sheets", n)
