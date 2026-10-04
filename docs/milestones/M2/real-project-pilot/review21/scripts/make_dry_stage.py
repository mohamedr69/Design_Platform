"""A SYNTHETIC dry-run stage for the four-arm harness (no real document, no model): C:/t/r2x/dry-runs/r21-stage.
  EP-16830/synth/rot270-sheet.pdf   1 page, A2 drawing sheet rotated 270, title block bottom-right, decision block inside it
  EP-16830/synth/long-6pages.pdf    6 pages of A2 drawing sheets (each page triggers a read): 4 in the reader's scope, 2 beyond
  EP-17428/synth/a4-letter.pdf      1 page A4 letter with a reference (whole-page discovery), no drawing
  EP-17428/synth/stamp-outside.pdf  1 page A2 sheet with a raster decision stamp OUTSIDE the title block
  EP-17428/synth/note.docx          a minimal Word file: an unsupported input for the evidence reader
Writes R21-DRY-STAGE.json (sha256, pages, extension per file)."""
import hashlib
import io
import json
import pathlib
import sys
import zipfile

import pymupdf
from PIL import Image, ImageDraw, ImageFont

DST = pathlib.Path("C:/t/r2x/dry-runs/r21-stage")
if DST.exists():
    sys.exit("the dry stage exists; never rebuilt in place")
TB = ["PROJECT EXAMPLE TOWER", "CLIENT EXAMPLE COMPANY", "SCALE 1:100", "DRAWN AB", "CHECKED CD", "DRAWING NO X-SD-{n}", "REV 02"]
LEGEND = ["A = APPROVED", "B = APPROVED AS NOTED", "C = REVISE AND RESUBMIT", "MARKED: B  CONSULTANT"]


def sheet_page(doc, n, *, rotation=0, decision_in_block=False, stamp=False):
    page = doc.new_page(width=1684, height=1190)
    if rotation:
        page.set_rotation(rotation)
    W, H = page.rect.width, page.rect.height
    lines = [t.format(n=n) for t in TB] + (LEGEND if decision_in_block else [])
    for i, t in enumerate(lines):
        page.insert_text(pymupdf.Point(W * 0.78, H * 0.70 + 16 * i) * page.derotation_matrix, t, fontsize=8, rotate=rotation)
    if stamp:
        img = Image.new("RGB", (600, 160), "white")
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
        d.text((12, 10), "CONSULTANT - CODE B", fill="black", font=font)
        d.text((12, 60), "APPROVED AS NOTED", fill="black", font=font)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        page.insert_image(pymupdf.Rect(W * 0.06, H * 0.08, W * 0.06 + 420, H * 0.08 + 112) * page.derotation_matrix, stream=buf.getvalue(), rotate=rotation)
    return page


files = {}
d = pymupdf.open(); sheet_page(d, 1, rotation=270, decision_in_block=True); files["EP-16830/synth/rot270-sheet.pdf"] = d
d = pymupdf.open()
for n in range(1, 7):
    sheet_page(d, 10 + n)
files["EP-16830/synth/long-6pages.pdf"] = d
d = pymupdf.open(); p = d.new_page(width=595, height=842)
for i, t in enumerate(["TRANSMITTAL", "DOCUMENT NO TR-001", "REV 00", "Dear Sir, please find attached the documents listed below for your review."]):
    p.insert_text((60, 90 + 20 * i), t, fontsize=10)
files["EP-17428/synth/a4-letter.pdf"] = d
d = pymupdf.open(); sheet_page(d, 7, stamp=True); files["EP-17428/synth/stamp-outside.pdf"] = d
out = []
for rel, doc in files.items():
    path = DST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    out.append({"doc_key": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "path": str(path), "pages": doc.page_count, "extension": ".pdf"})
docx = DST / "EP-17428/synth/note.docx"
with zipfile.ZipFile(docx, "w") as z:
    z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
               '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               '<w:body><w:p><w:r><w:t>Transmittal note TR-002 rev 00</w:t></w:r></w:p></w:body></w:document>')
out.append({"doc_key": "EP-17428/synth/note.docx", "sha256": hashlib.sha256(docx.read_bytes()).hexdigest(), "path": str(docx), "pages": None, "extension": ".docx"})
(DST / "R21-DRY-STAGE.json").write_text(json.dumps({"synthetic": True, "files": out}, indent=1) + "\n", encoding="utf-8")
print(len(out), "files;", [(f["doc_key"].split("/")[-1], f["pages"]) for f in out])
