"""Title-block sheets for the drawing-sized documents (page wider than 900 pt): the right-hand strip of page 1 (where
these projects' title blocks and revision boxes sit) rendered large enough to read, four documents per sheet, plus the
bottom band (stamps) under each strip. Independent of the parser; tile numbers match crops/index.json."""
import json, sys, pathlib
import pymupdf
from PIL import Image, ImageDraw

S = pathlib.Path(sys.argv[1]); OUT = S / "tb"; OUT.mkdir(exist_ok=True)
frozen = {f"EP-{d['ep']}/{d['relative_path']}": d for d in json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))["documents"]}
tiles = [x for x in json.load(open(S / "crops" / "index.json")) if x.get("whole")]
drawn = []
for i, x in enumerate(tiles):
    d = frozen[x["doc"]]
    try:
        pdf = pymupdf.open(d["staged_path"]); page = pdf[0]; r = page.rect
        if r.width <= 900 and r.height <= 900:
            pdf.close(); continue
        strip = pymupdf.Rect(r.width * 0.78, 0, r.width, r.height)
        dpi = max(40, min(140, int(72 * 1700 / r.height)))
        page.get_pixmap(dpi=dpi, clip=strip).save(OUT / f"{i}-strip.png")
        band = pymupdf.Rect(0, r.height * 0.86, r.width * 0.78, r.height)
        page.get_pixmap(dpi=max(30, min(90, int(72 * 1300 / (r.width * 0.78)))), clip=band).save(OUT / f"{i}-band.png")
        drawn.append((i, x["doc"], round(r.width), round(r.height), page.rotation)); pdf.close()
    except Exception as exc:  # noqa: BLE001
        drawn.append((i, x["doc"], None, None, str(exc)[:60]))
n = 0
for start in range(0, len(drawn), 4):
    group = drawn[start:start + 4]; W = 1900
    sheet = Image.new("RGB", (W, 1990), "white"); draw = ImageDraw.Draw(sheet)
    for k, (i, doc, w, h, rot) in enumerate(group):
        x0 = k * (W // 4) + 4
        draw.text((x0, 2), f"[{i}] {doc[-52:]}", fill="red")
        p = OUT / f"{i}-strip.png"
        if p.is_file():
            im = Image.open(p); im.thumbnail((W // 4 - 12, 1700)); sheet.paste(im, (x0, 14))
            bd = Image.open(OUT / f"{i}-band.png"); bd.thumbnail((W // 4 - 12, 260)); sheet.paste(bd, (x0, 1724))
    n += 1; sheet.save(OUT / f"tb-{n:03d}.png")
json.dump(drawn, open(OUT / "index.json", "w"), indent=0)
print("drawings", len(drawn), "sheets", n)
