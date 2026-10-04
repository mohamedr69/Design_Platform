"""Offline: the frozen candidate's own drawing-sheet predicate (app.services.title_block.is_drawing_sheet, the gate of
ROI title-block discovery at evidence_reader.py:1045) on every in-scope page of the frozen sample, joined with the frozen
R26 labels' decision records. Reads only the hash-checked staged copies; no model request. Writes ROI-POPULATION.json."""
import hashlib, json, pathlib, sys, os
os.environ.setdefault("AI_ENABLED", "false"); os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/roi-no-db.db")
sys.path.insert(0, "C:/t/iso/cand-ai4/backend")
import pymupdf
from app.services import title_block as tb
R = pathlib.Path(__file__).resolve().parent
st = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))["files"]
ids = {d["doc"]: d["id"] for d in json.loads(pathlib.Path("C:/t/iso/work/r2x/r26/renders/RENDERS.json").read_text(encoding="utf-8"))["documents"]}
pages = json.loads(pathlib.Path("C:/t/iso/work/r2x/r26/labels-r26/R26-PAGE-LABELS.json").read_text(encoding="utf-8"))["documents"]
rows = []
for f in st:
    if f["extension"] != ".pdf":
        continue
    b = open(f["path"], "rb").read()
    assert hashlib.sha256(b).hexdigest() == f["sha256"]
    doc = pymupdf.open(stream=b, filetype="pdf")
    recs = {r["page"]: r for r in pages[f["doc_key"]]["records"]}
    for n in range(1, min(doc.page_count, 4) + 1):
        p = doc[n - 1]
        r = recs.get(n)
        rows.append({"id": ids[f["doc_key"]], "page": n, "size_pt": [round(p.rect.width, 1), round(p.rect.height, 1)], "is_drawing_sheet": tb.is_drawing_sheet(p),
                     "decision": r["decision"] if r else None, "decision_location": r["decision_location"] if r else None})
dec = [x for x in rows if x["decision"] in ("approved as noted", "rejected", "approved")]
out = {"predicate": "max(page.rect.width, page.rect.height) > title_block.MIN_SHEET_SIDE_PT", "MIN_SHEET_SIDE_PT": tb.MIN_SHEET_SIDE_PT,
       "title_block_sha256": hashlib.sha256(open(tb.__file__, "rb").read()).hexdigest(),
       "pages_in_scope": len(rows), "drawing_sized_pages": sum(x["is_drawing_sheet"] for x in rows),
       "decision_pages": dec, "decision_pages_crop_eligible": [f'{x["id"]} p{x["page"]}' for x in dec if x["is_drawing_sheet"]],
       "decision_pages_whole_page_discovery": [f'{x["id"]} p{x["page"]}' for x in dec if not x["is_drawing_sheet"]], "pages": rows}
(R / "ROI-POPULATION.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print("MIN", tb.MIN_SHEET_SIDE_PT, "| in-scope", len(rows), "| drawing-sized", out["drawing_sized_pages"], "| crop-eligible decision pages", out["decision_pages_crop_eligible"], "| whole-page", out["decision_pages_whole_page_discovery"])
