"""Pilot step 4 (truth): render, independently of the parser, the parts of each sampled original a reader labels from:
page 1 whole (small) plus the bands holding a reference/revision/date/recommendation cue (found from one word
extraction per page, not repeated searches), the title-block corner for drawing sheets, page 2 for scans; laid out on
contact sheets of four documents each. Resumable: a document whose crops exist is not rendered again."""
import json, sys, pathlib, re, time
import pymupdf
from PIL import Image, ImageDraw

S = pathlib.Path(sys.argv[1]); OUT = S / "crops"; OUT.mkdir(exist_ok=True)
frozen = json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))
CUE = re.compile(r"^(no\.?:?|ref\.?:?|reference|rev\.?:?|revision|date:?|recommendation|approved|submittal|transmittal|status:?|drawing|title:?|subject:?|comments?|action)$", re.I)
index = []; tiles = []; t0 = time.time()
for n, d in enumerate(frozen["documents"]):
    if d["extension"] != ".pdf" or "sha256" not in d or "staged_path" not in d:
        continue
    key = f"EP-{d['ep']}/{d['relative_path']}"; tag = d["sha256"][:12]
    meta = OUT / f"{tag}.json"
    if meta.is_file():
        entry = json.load(open(meta)); index.append(entry); tiles.append((key, tag, entry["crops"])); continue
    try:
        pdf = pymupdf.open(d["staged_path"]); page = pdf[0]; r = page.rect
        whole = page.get_pixmap(dpi=40 if r.width > 900 else 55); whole.save(OUT / f"{tag}-p1.png")
        words = page.get_text("words")
        hits = [pymupdf.Rect(w[:4]) for w in words if CUE.match(w[4])][:40]
        bands = []
        for h in sorted(hits, key=lambda h: h.y0):
            band = pymupdf.Rect(0, max(0, h.y0 - 8), r.width, min(r.height, h.y1 + 14))
            if bands and band.y0 <= bands[-1].y1 + 4:
                bands[-1] = pymupdf.Rect(0, bands[-1].y0, r.width, max(bands[-1].y1, band.y1))
            else:
                bands.append(band)
        crops = []
        for i, b in enumerate(bands[:6]):
            b = b & r
            if b.is_empty or b.height < 8: continue
            pix = page.get_pixmap(dpi=100 if r.width < 900 else 60, clip=b); name = f"{tag}-b{i}.png"; pix.save(OUT / name); crops.append(name)
        if r.width > 900 or not hits:
            corner = pymupdf.Rect(r.width * 0.62, r.height * 0.72, r.width, r.height) & r
            page.get_pixmap(dpi=55 if r.width > 900 else 80, clip=corner).save(OUT / f"{tag}-tb.png"); crops.append(f"{tag}-tb.png")
        if pdf.page_count > 1 and (d.get("scan_like") or not hits):
            pdf[1].get_pixmap(dpi=45).save(OUT / f"{tag}-p2.png"); crops.append(f"{tag}-p2.png")
        entry = {"doc": key, "sha256": d["sha256"], "tag": tag, "pages": pdf.page_count, "scan_like": d.get("scan_like"), "whole": f"{tag}-p1.png", "crops": crops, "cues_found": len(hits)}
        pdf.close()
    except Exception as exc:  # noqa: BLE001
        entry = {"doc": key, "sha256": d["sha256"], "tag": tag, "error": str(exc)[:100], "crops": [], "whole": None}
    json.dump(entry, open(meta, "w")); index.append(entry)
    if entry.get("whole"): tiles.append((key, tag, entry["crops"]))
    if n % 20 == 0: print(n, round(time.time() - t0), "s", flush=True)
sheet_no = 0
for start in range(0, len(tiles), 4):
    group = tiles[start:start + 4]; W = 1800; row_h = 470
    sheet = Image.new("RGB", (W, row_h * len(group) + 10), "white"); draw = ImageDraw.Draw(sheet)
    for k, (key, tag, crops) in enumerate(group):
        y = k * row_h + 6
        draw.text((4, y), f"[{start + k}] {key[-80:]}  #{tag}", fill="red")
        whole = Image.open(OUT / f"{tag}-p1.png"); whole.thumbnail((560, row_h - 24)); sheet.paste(whole, (4, y + 14))
        cy = y + 14
        for c in crops[:5]:
            im = Image.open(OUT / c); im.thumbnail((1220, 120))
            if cy + im.height > y + row_h - 4: break
            sheet.paste(im, (580, cy)); cy += im.height + 4
    sheet_no += 1; sheet.save(OUT / f"sheet-{sheet_no:03d}.png")
json.dump(index, open(OUT / "index.json", "w"), indent=1)
print("docs", len(tiles), "sheets", sheet_no, "errors", sum(1 for x in index if "error" in x), round(time.time() - t0), "s")
