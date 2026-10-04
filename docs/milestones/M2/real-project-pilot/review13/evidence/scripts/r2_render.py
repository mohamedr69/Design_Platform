"""M2 Round 2 exploration, step 4: renders for independent source labelling, made from the STAGED copies only (never
the originals, never a prediction). Reading scope per PDF: pages 1..4 (the evidence stage's page cap); each page as a
whole-page JPEG (long side <= 1600 px) plus, for drawing-size pages (either side > 700 pt), a 200 dpi crop of the
bottom-right title-block quadrant (right 50 %, bottom 45 %). The text layer of each page is saved beside it. Word
transmittals: their text (python-docx / antiword-free path: the application's own transmittals reader text).

Usage: r2_render.py <EXPLORATION-MANIFEST.json sha256>"""
import hashlib
import json
import pathlib
import sys

import pymupdf

MAN = pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json")
assert hashlib.sha256(MAN.read_bytes()).hexdigest() == sys.argv[1], "the staging manifest changed"
OUT = pathlib.Path("C:/t/r2x/renders")
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = "\\\\?\\"
SCOPE_PAGES = 4
man = json.loads(MAN.read_text(encoding="utf-8"))
index = []
for d in man["documents"] + [b for b in man["boq_candidates"] if b.get("sha256")]:
    tag = d["sha256"][:12]
    entry = {"doc_key": d["doc_key"], "sha256": d["sha256"], "ep": d["ep"], "stratum": d.get("stratum"), "role": d.get("role"), "pages": []}
    src = PREFIX + d["staged_path"].replace("/", "\\")
    if d["extension"] == ".pdf":
        try:
            pdf = pymupdf.open(src)
        except Exception as exc:  # noqa: BLE001
            entry["error"] = f"{type(exc).__name__}: {exc}"[:160]
            index.append(entry)
            continue
        entry["page_count"] = pdf.page_count
        scope = range(min(pdf.page_count, SCOPE_PAGES if d.get("role") != "boq_candidate" else pdf.page_count))
        for i in scope:
            page = pdf[i]
            r = page.rect
            zoom = min(1600 / max(r.width, r.height), 150 / 72)
            whole = OUT / f"{tag}-p{i + 1}.jpg"
            if not whole.exists():
                page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(str(whole), jpg_quality=80)
            rec = {"page": i + 1, "size_pt": [round(r.width), round(r.height)], "rotation": page.rotation, "whole": whole.name}
            if max(r.width, r.height) > 700:
                tb = OUT / f"{tag}-p{i + 1}-tb.jpg"
                if not tb.exists():
                    clip = pymupdf.Rect(r.x0 + r.width * 0.50, r.y0 + r.height * 0.55, r.x1, r.y1)
                    page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72), clip=clip).save(str(tb), jpg_quality=85)
                rec["title_block_crop"] = tb.name
            text = page.get_text().strip()
            (OUT / f"{tag}-p{i + 1}.txt").write_text(text, encoding="utf-8")
            rec["text_chars"] = len(text)
            entry["pages"].append(rec)
        pdf.close()
    else:
        try:
            import docx  # python-docx for .docx; .doc text via the application's reader where available
            text = "\n".join(p.text for p in docx.Document(src).paragraphs) if d["extension"] == ".docx" else ""
        except Exception as exc:  # noqa: BLE001
            text, entry["error"] = "", f"{type(exc).__name__}: {exc}"[:160]
        (OUT / f"{tag}-word.txt").write_text(text, encoding="utf-8")
        entry["word_text_chars"] = len(text)
    index.append(entry)
json.dump({"manifest_sha256": sys.argv[1], "scope_pages": SCOPE_PAGES, "documents": index}, open(OUT / "RENDER-INDEX.json", "w", encoding="utf-8"), indent=1)
print("rendered", len(index), "documents;", sum(len(e["pages"]) for e in index), "pages;", sum("error" in e for e in index), "errors")
