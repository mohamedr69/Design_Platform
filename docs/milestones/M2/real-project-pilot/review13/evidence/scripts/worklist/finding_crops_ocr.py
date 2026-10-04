"""Second pass for FINDING-CROPS.json: a literal the text layer does not hold (a scan) is located by local Tesseract
OCR on the page rendered at 200 dpi (the rotation applied), by its most distinctive alphanumeric run (the longest,
>= 4 characters; one OCR edit allowed); each hit is cropped with context. Still-unlocated literals keep their region
crops. Local OCR only; nothing is sent to a model."""
import hashlib
import io
import json
import pathlib
import re

import pymupdf
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
OUT = pathlib.Path("C:/t/r2x/worklist/findings")
IDX = OUT / "FINDING-CROPS.json"
PREFIX = "\\\\?\\"
staged = {}
for f in ("FROZEN-SAMPLE.json", "review05/holdout/HOLDOUT-SAMPLE.json"):
    for d in json.loads((PILOT / f).read_text(encoding="utf-8"))["documents"]:
        staged[f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/")] = d


def key_run(lit: str) -> str:
    runs = re.findall(r"[A-Za-z0-9]+", lit)
    return max(runs, key=len).upper() if runs else ""


def near(a: str, b: str) -> bool:
    if a in b:
        return True
    if abs(len(a) - len(b)) > 1 or len(a) < 4:
        return False
    # one substitution / insertion / deletion
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return a[i + 1:] == b[i + 1:] or a[i:] == b[i + 1:] or a[i + 1:] == b[i:]


idx = json.loads(IDX.read_text(encoding="utf-8"))
cache = {}
for rec in idx["items"]:
    if not rec["not_located"]:
        continue
    d = staged[rec["doc"].replace("\\", "/")]
    ck = (d["sha256"], rec["page"])
    if ck not in cache:
        data = open(PREFIX + d["staged_path"].replace("/", "\\"), "rb").read()
        assert hashlib.sha256(data).hexdigest() == d["sha256"]
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            page = pdf[rec["page"] - 1]
            zoom = min(200 / 72, 7000 / max(page.rect.width, page.rect.height))
            img = Image.open(io.BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))).convert("RGB")
        ocr = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config="--psm 11")
        words = [(re.sub(r"[^A-Za-z0-9]", "", w).upper(), (ocr["left"][i], ocr["top"][i], ocr["width"][i], ocr["height"][i]))
                 for i, w in enumerate(ocr["text"]) if w.strip()]
        cache[ck] = (img, words)
    img, words = cache[ck]
    still = []
    for lit in rec["not_located"]:
        k = key_run(lit)
        hits = [box for w, box in words if w and k and (near(k, w) or (len(w) >= 5 and w in k and len(w) >= len(k) * 0.6))]
        if not hits:
            still.append(lit)
            continue
        x, y, w, h = hits[0]
        pad_x, pad_y = max(420, w * 2), max(220, h * 6)
        box = (max(0, x - pad_x), max(0, y - pad_y), min(img.width, x + w + pad_x), min(img.height, y + h + pad_y))
        name = f"{rec['group']}-{rec['item']}-p{rec['page']}-ocr-{len(rec['crops']) + 1}.jpg"
        img.crop(box).save(OUT / name, quality=88)
        rec["crops"].append({"file": name, "literal_searched": lit, "located_by": f"local OCR, key '{k}'", "ocr_hits": len(hits)})
    rec["not_located"] = still
    print(rec["group"], rec["item"], "crops", len(rec["crops"]), "still not located", still)
idx["ocr_pass"] = "finding_crops_ocr.py (local Tesseract, psm 11)"
IDX.write_text(json.dumps(idx, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
