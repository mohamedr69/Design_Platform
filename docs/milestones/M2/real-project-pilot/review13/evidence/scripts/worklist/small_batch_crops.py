"""Crops for the small batch's unresolved label items (SMALL-BATCH-LABELS.json `unresolved`), from the small-stage
copies (hash-checked): each item names the literal to show; it is found in the text layer, else by local Tesseract
OCR on the 200 dpi render, else the item gets a named region crop. Local only; no model."""
import hashlib
import io
import json
import pathlib
import re

import pymupdf
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LAB = pathlib.Path("C:/t/iso/work/r2x/labels/SMALL-BATCH-LABELS.json")
STAGE = json.loads(pathlib.Path("C:/t/r2x/small-stage/SMALL-STAGE.json").read_text(encoding="utf-8"))
OUT = pathlib.Path("C:/t/r2x/worklist/small-batch")
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = "\\\\?\\"
path_of = {f["doc_key"]: (f["path"], f["sha256"]) for f in STAGE["files"]}
# (doc sha prefix, unresolved index) -> (page, literal to show, region fallback as fractions x0, y0, x1, y1)
ITEMS = {
    ("535ffbdabfcf", 0): (1, "Submittal No", (0.0, 0.0, 1.0, 0.35)),
    ("0c9737211762", 0): (1, None, (0.04, 0.12, 0.62, 0.165)),   # handwritten: the field row itself
    ("0c9737211762", 1): (1, "Revision Number", (0.0, 0.0, 1.0, 0.3)),
    ("bdce7913eb15", 0): (1, "Qtn. Ref.", (0.55, 0.03, 1.0, 0.13)),
    ("bdce7913eb15", 1): (1, "SL23I", (0.0, 0.34, 0.7, 0.42)),
    ("d8ba80a74660", 0): (1, "P06/TRANS/R1", (0.6, 0.88, 1.0, 0.95)),
    ("2472d2cc65c3", 0): (1, "DCH-M-MHT-CAL-IFC-ELE-0001-00", (0.35, 0.75, 0.95, 0.85)),
}
lab = json.loads(LAB.read_text(encoding="utf-8"))
index = {"labels_sha256": hashlib.sha256(LAB.read_bytes()).hexdigest(), "items": []}
for key, d in lab["documents"].items():
    for n, question in enumerate(d["unresolved"]):
        page_no, literal, region = ITEMS[(d["sha256"][:12], n)]
        path, sha = path_of[key]
        data = open(PREFIX + path.replace("/", "\\"), "rb").read()
        assert hashlib.sha256(data).hexdigest() == sha == d["sha256"]
        rec = {"doc": key, "sha256": sha, "page": page_no, "question": question, "literal": literal, "crops": []}
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            page = pdf[page_no - 1]
            zoom = 200 / 72
            img = Image.open(io.BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))).convert("RGB")
            rects = page.search_for(literal) if (literal and page.rotation == 0) else []
            box = None
            how = None
            if rects:
                r = rects[0]
                box = (r.x0 * zoom, r.y0 * zoom, r.x1 * zoom, r.y1 * zoom)
                how = "text layer"
            elif literal:
                ocr = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config="--psm 11")
                k = max(re.findall(r"[A-Za-z0-9]+", literal), key=len).upper()
                for i, w in enumerate(ocr["text"]):
                    if k and k in re.sub(r"[^A-Za-z0-9]", "", w).upper():
                        box = (ocr["left"][i], ocr["top"][i], ocr["left"][i] + ocr["width"][i], ocr["top"][i] + ocr["height"][i])
                        how = f"local OCR, key '{k}'"
                        break
            if box:
                x0, y0, x1, y1 = box
                crop = (max(0, x0 - 500), max(0, y0 - 180), min(img.width, x1 + 700), min(img.height, y1 + 260))
            else:
                fx0, fy0, fx1, fy1 = region
                crop = (int(fx0 * img.width), int(fy0 * img.height), int(fx1 * img.width), int(fy1 * img.height))
                how = "region crop (literal not located)"
            name = f"{sha[:12]}-u{n + 1}-p{page_no}.jpg"
            img.crop(tuple(int(v) for v in crop)).save(OUT / name, quality=88)
            rec["crops"].append({"file": name, "located_by": how})
        index["items"].append(rec)
        print(sha[:12], n + 1, how)
(OUT / "SMALL-BATCH-CROPS.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
