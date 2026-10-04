"""Step 6: render every in-scope page (pages 1..4, the reader scope) of every staged pool document from the hash-checked
STAGED copy -- never from the OneDrive original. Recipe RENDER-R32-1: PyMuPDF 1.28.2, page as displayed (its /Rotate
applied), scale so the long side is 1800 px, RGB PNG, no annotations suppressed; plus the page text layer
(get_text("text")) and its words with coordinates in displayed-page points (get_text("words")) for locating regions.
Each render is bound to the staged sha256, page number and recipe. A document that cannot be opened (encrypted, damaged)
is recorded as 'unsupported' with the error; pages beyond 4 are counted, not rendered.
Usage: render_r32.py [pool|extension-1|extension-2]. Writes C:/t/r2x/r32-stage/renders/<id>-p<n>.png|.txt|.words.json and
RENDERS.json (or RENDERS.<extension>.json) in the work folder."""
import hashlib
import json
import pathlib
import sys

import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
part = sys.argv[1] if len(sys.argv) > 1 else "pool"
MAN = json.loads((HERE / ("SOURCE-MANIFEST.json" if part == "pool" else f"SOURCE-MANIFEST.{part}.json")).read_text(encoding="utf-8"))
OUTD = pathlib.Path("C:/t/r2x/r32-stage/renders")
OUTD.mkdir(parents=True, exist_ok=True)
OUT = HERE / ("RENDERS.json" if part == "pool" else f"RENDERS.{part}.json")
if OUT.exists():
    raise SystemExit(f"{OUT.name} exists")
RECIPE = {"id": "RENDER-R32-1", "library": f"PyMuPDF {pymupdf.__version__}", "orientation": "displayed (/Rotate applied)", "long_side_px": 1800,
          "format": "PNG RGB", "text": "get_text('text') and get_text('words') in displayed-page points", "pages": "1..4 (reader scope)"}
docs = []
for f in MAN["files"]:
    rec = {"pool_id": f["pool_id"], "ep": f["ep"], "relative_path": f["relative_path"], "staged_sha256": f.get("staged_sha256"), "rendered": []}
    if f["state"] != "staged":
        rec |= {"state": "unsupported", "reason": f"not staged: {f.get('error')}"}
        docs.append(rec)
        continue
    b = pathlib.Path(f["staged_path"]).read_bytes()
    assert hashlib.sha256(b).hexdigest() == f["staged_sha256"]
    try:
        doc = pymupdf.open(stream=b, filetype="pdf")
        if doc.needs_pass:
            raise RuntimeError("encrypted: needs a password")
        rec |= {"state": "rendered", "page_count": doc.page_count, "pages_in_scope": min(doc.page_count, 4), "pages_beyond_reader_scope": max(0, doc.page_count - 4)}
        for n in range(1, min(doc.page_count, 4) + 1):
            page = doc[n - 1]
            scale = 1800 / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
            stem = f"{f['pool_id']}-p{n}"
            pix.save(OUTD / f"{stem}.png")
            txt = page.get_text("text")
            (OUTD / f"{stem}.txt").write_text(txt, encoding="utf-8")
            words = [[round(w[0], 1), round(w[1], 1), round(w[2], 1), round(w[3], 1), w[4]] for w in page.get_text("words")]
            (OUTD / f"{stem}.words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            rec["rendered"].append({"page": n, "png": f"{stem}.png", "png_sha256": hashlib.sha256((OUTD / f"{stem}.png").read_bytes()).hexdigest(),
                                    "txt_sha256": hashlib.sha256((OUTD / f"{stem}.txt").read_bytes()).hexdigest(), "rotation": page.rotation,
                                    "size_pt": [round(page.rect.width, 1), round(page.rect.height, 1)], "png_px": [pix.width, pix.height],
                                    "text_chars": len(txt.strip()), "images": len(page.get_images())})
    except Exception as e:  # noqa: BLE001 -- recorded, never dropped
        rec |= {"state": "unsupported", "reason": f"{type(e).__name__}: {e}"}
    docs.append(rec)
    print(rec["pool_id"], rec["state"], rec.get("page_count"), [(r["page"], r["size_pt"], r["rotation"], r["text_chars"]) for r in rec["rendered"]], flush=True)
out = {"part": part, "recipe": RECIPE, "source_manifest_sha256": hashlib.sha256((HERE / ("SOURCE-MANIFEST.json" if part == "pool" else f"SOURCE-MANIFEST.{part}.json")).read_bytes()).hexdigest(),
       "render_dir": str(OUTD), "documents": docs}
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("pages rendered", sum(len(d["rendered"]) for d in docs), "unsupported", sum(d["state"] == "unsupported" for d in docs))
