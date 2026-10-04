"""A SYNTHETIC dry-run stage for the harness v4 runner probes (no real document, no model): C:/t/r2x/dry-runs/r22-stage.
Every drawing-sheet page carries the title-block LABELS as vector text (DRAWING NO / REV: the reader's form cues) with the
VALUES as a small raster image, so the deterministic reading finds no identity and EV1 triggers a read on every page:
  EP-16830/synth/raster-6pages.pdf   6 pages: 4 in the reader's scope (enough attempted reads to hit the 12-per-document cap), 2 beyond
  EP-16830/synth/raster-1page.pdf    1 page
  EP-17428/synth/raster-2pages.pdf   2 pages
  EP-17428/synth/text-sheet.pdf      1 page with a fully vector title block (deterministic identity present: a no-trigger control)
  EP-17428/synth/note.docx           a minimal Word file: an unsupported input for the evidence reader
Writes R22-DRY-STAGE.json (sha256, pages, extension per file)."""
import hashlib
import io
import json
import pathlib
import sys
import zipfile

import pymupdf
from PIL import Image, ImageDraw, ImageFont

DST = pathlib.Path("C:/t/r2x/dry-runs/r22-stage")
if DST.exists():
    sys.exit("the dry stage exists; never rebuilt in place")
LABELS = ["PROJECT EXAMPLE TOWER", "CLIENT EXAMPLE COMPANY", "SCALE 1:100", "DRAWN AB", "CHECKED CD", "DRAWING NO", "REV"]


def raster(text: str, w: int = 260, h: int = 40) -> bytes:
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    d.text((6, 4), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def sheet_page(doc, *, identity="X-DRY-1", revision="01", values_as_raster=True, sheet=1):
    page = doc.new_page(width=1684, height=1190)
    W, H = page.rect.width, page.rect.height
    # a per-page line inside every crop the reader takes (title block, discovery clip): pages never share a cache fingerprint
    page.insert_text(pymupdf.Point(W * 0.74, H * 0.925), f"SHEET {sheet} OF {doc.page_count}", fontsize=9)
    page.insert_text(pymupdf.Point(W * 0.77, H * 0.775), f"SHEET {sheet}", fontsize=9)
    page.insert_text(pymupdf.Point(W * 0.91, H * 0.93), f"S{sheet}", fontsize=9)      # inside the scripted revision region as well
    for i, t in enumerate(LABELS):
        page.insert_text(pymupdf.Point(W * 0.74, H * 0.70 + 18 * i), t, fontsize=9)
    if values_as_raster:
        page.insert_image(pymupdf.Rect(W * 0.80, H * 0.70 + 18 * 5 - 10, W * 0.80 + 130, H * 0.70 + 18 * 5 + 10), stream=raster(identity))
        page.insert_image(pymupdf.Rect(W * 0.80, H * 0.70 + 18 * 6 - 10, W * 0.80 + 130, H * 0.70 + 18 * 6 + 10), stream=raster(revision))
    else:
        page.insert_text(pymupdf.Point(W * 0.80, H * 0.70 + 18 * 5), identity, fontsize=9)
        page.insert_text(pymupdf.Point(W * 0.80, H * 0.70 + 18 * 6), revision, fontsize=9)
    return page


files = {}
d = pymupdf.open()
for n in range(6):
    sheet_page(d, sheet=n + 1)
files["EP-16830/synth/raster-6pages.pdf"] = d
d = pymupdf.open(); sheet_page(d); files["EP-16830/synth/raster-1page.pdf"] = d
d = pymupdf.open(); sheet_page(d, sheet=1); sheet_page(d, sheet=2); files["EP-17428/synth/raster-2pages.pdf"] = d
d = pymupdf.open(); sheet_page(d, identity="X-SD-7", revision="02", values_as_raster=False); files["EP-17428/synth/text-sheet.pdf"] = d
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
(DST / "R22-DRY-STAGE.json").write_text(json.dumps({"synthetic": True, "files": out}, indent=1) + "\n", encoding="utf-8")
print(len(out), "files;", [(f["doc_key"].split("/")[-1], f["pages"]) for f in out])
