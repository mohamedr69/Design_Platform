"""Crops for every critical false accept in eval/DISAGREEMENTS.json (small batch, provisional truth), from the
small-stage copies (hash-checked): the accepted literal located in the text layer, else by local Tesseract OCR, else
the page's top and title-block regions. Each item gets a neutral `review_note` saying what a person must decide;
nothing is re-classified here. Writes DISAGREEMENTS-WITH-CROPS.json for build_worklist.py --disagreements."""
import hashlib
import io
import json
import pathlib
import re

import pymupdf
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
E = pathlib.Path("C:/t/iso/work/r2x/eval")
OUT = pathlib.Path("C:/t/r2x/worklist/critical")
OUT.mkdir(parents=True, exist_ok=True)
STAGE = {f["doc_key"]: f for f in json.loads(pathlib.Path("C:/t/r2x/small-stage/SMALL-STAGE.json").read_text(encoding="utf-8"))["files"]}
PREFIX = "\\\\?\\"
NOTES = {  # (doc suffix, page, field) -> what a person must decide (neutral; written from the source and the labels)
    ("1-7.pdf", 4, "identity"): "The divider header prints 'Submittal No.:' with only 'Rev.0' after it. Is 'Rev.0' this page's identity? (The proposed label: no identity; a revision literal is not an identity.)",
    ("1-7.pdf", 3, "revision"): "The divider header prints 'Rev.0'. Is each divider a component of the method statement (blank number, revision 0), or a no-record page as proposed? (Open CONFIRM item SB/535ffbdabfcf/u1.)",
    ("1-7.pdf", 2, "revision"): "Same divider header ('Submittal No.:' followed only by 'Rev.0') on page 2: a component of the method statement with revision 0, or a no-record page as proposed? (SB/535ffbdabfcf/u1.)",
    ("Previous Project List.pdf", 1, "identity"): "The footer 'P06/TRANS/R1' on every page: the list's own identity, or the letterhead / form code as proposed (open CONFIRM item SB/d8ba80a74660/u1)?",
    ("DCH-M-MHT-CAL-IFC-ELE-0001-00.pdf", 2, "revision"): "Page 2 is the Document History of the same calculation (revision 00). Should revision 00 be scored on page 2 (a component page), or only on the page-1 cover as proposed?",
}
d = json.loads((E / "DISAGREEMENTS.json").read_text(encoding="utf-8"))
for c in d["critical_false_accepts"]:
    f = STAGE[c["doc"]]
    data = open(PREFIX + f["path"].replace("/", "\\"), "rb").read()
    assert hashlib.sha256(data).hexdigest() == f["sha256"]
    note = next((v for (suf, pg, fld), v in NOTES.items() if c["doc"].endswith(suf) and pg == c["page"] and fld == c["field"]), None)
    c["review_note"] = note or "A person must decide whether this accepted value is right for this page and component (no note written)."
    c["crops"] = []
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        page = pdf[c["page"] - 1]
        zoom = 200 / 72
        img = Image.open(io.BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))).convert("RGB")
        lit = str(c["value"])
        rects = page.search_for(lit) if page.rotation == 0 and len(lit) >= 2 else []
        boxes = [(r.x0 * zoom, r.y0 * zoom, r.x1 * zoom, r.y1 * zoom) for r in rects[:2]]
        how = "text layer" if boxes else None
        if not boxes and len(re.sub(r"[^A-Za-z0-9]", "", lit)) >= 2:
            ocr = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config="--psm 11")
            k = re.sub(r"[^A-Za-z0-9]", "", lit).upper()
            boxes = [(ocr["left"][i], ocr["top"][i], ocr["left"][i] + ocr["width"][i], ocr["top"][i] + ocr["height"][i])
                     for i, w in enumerate(ocr["text"]) if k and re.sub(r"[^A-Za-z0-9]", "", w).upper() == k][:2]
            how = "local OCR" if boxes else None
        tag = hashlib.sha256(f"{c['profile']}|{c['doc']}|{c['page']}|{c['field']}".encode()).hexdigest()[:10]
        for n, (x0, y0, x1, y1) in enumerate(boxes):
            name = f"{tag}-{n + 1}.jpg"
            img.crop((int(max(0, x0 - 600)), int(max(0, y0 - 250)), int(min(img.width, x1 + 800)), int(min(img.height, y1 + 300)))).save(OUT / name, quality=88)
            c["crops"].append(name)
        if not boxes:
            name = f"{tag}-top.jpg"
            img.crop((0, 0, img.width, int(img.height * 0.4))).save(OUT / name, quality=85)
            c["crops"].append(name)
            how = "region crop (literal not located)"
        c["located_by"] = how
    print(c["profile"], c["doc"][-40:], c["page"], c["field"], c["value"], how, len(c["crops"]))
(E / "DISAGREEMENTS-WITH-CROPS.json").write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
