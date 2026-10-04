"""Render every in-scope page of the frozen R21 sample (staged copies, hash-checked) for AI-drafted reference labelling:
a full-page PNG (long side 1800 px, displayed orientation) and the page's text layer. No model call. Writes
renders/Dnn-pP.png, renders/Dnn-pP.txt and renders/RENDERS.json (doc, sha256, page, class, render sha256)."""
import hashlib, json, pathlib
import pymupdf
R = pathlib.Path(__file__).parent
OUT = R / "renders"
OUT.mkdir(exist_ok=True)
st = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))
pc = json.loads(pathlib.Path("C:/t/iso/work/r2x/review21/R21-PAGE-CLASSES.json").read_text(encoding="utf-8"))["pages"]
cls = {(p["doc_key"], p["page"]): p for p in pc}
LONG = "\\\\?\\"
out = []
for i, f in enumerate(st["files"], 1):
    did = f"D{i:02d}"
    b = open(LONG + f["path"], "rb").read()
    assert hashlib.sha256(b).hexdigest() == f["sha256"]
    rec = {"id": did, "doc": f["doc_key"], "sha256": f["sha256"], "role": f["role"], "extension": f["extension"], "pages": f["pages"], "rendered": []}
    if f["extension"] == ".pdf":
        doc = pymupdf.open(stream=b, filetype="pdf")
        for n in range(1, min(doc.page_count, 4) + 1):
            page = doc[n - 1]
            scale = 1800 / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
            png = OUT / f"{did}-p{n}.png"
            pix.save(png)
            txt = page.get_text()
            (OUT / f"{did}-p{n}.txt").write_text(txt, encoding="utf-8")
            c = cls.get((f["doc_key"], n), {})
            rec["rendered"].append({"page": n, "png": png.name, "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(), "rotation": page.rotation,
                                    "size_pt": [round(page.rect.width), round(page.rect.height)], "text_chars": len(txt.strip()), "class": {k: c.get(k) for k in ("size", "rotation", "text", "screen_off_title_block_decision", "in_scope")}})
    out.append(rec)
(OUT / "RENDERS.json").write_text(json.dumps({"stage_sample_sha256": st["sample_sha256"], "documents": out}, indent=1) + "\n", encoding="utf-8")
for r in out:
    print(r["id"], r["doc"].split("/")[0], r["role"][:30], r["extension"], r["pages"], [(x["page"], x["class"]["size"], x["class"]["text"], x["rotation"], x["text_chars"], x["class"]["screen_off_title_block_decision"]) for x in r["rendered"]])
