"""BOQ-name candidates (39): an AI visual triage from the staged renders (every page), BEFORE any label or prediction.
Provisional -- not labels; a person confirms before a BOQ batch is frozen. Classes: boq_rows (a row-per-item table with a
quantity column), boq_matrix (floor x item quantity matrix: needs its own label rules), not_boq. Non-table pages inside
BOQ documents are listed explicitly."""
import json
import pathlib

T = {  # candidate number (manifest order) -> (class, non-table pages, note)
    1: ("boq_rows", [], "EST3 design sheet, 3 pages of rows"), 2: ("boq_rows", [], "CBS design sheet"),
    3: ("boq_rows", [], "supplier proposal (WatchNET) with product code / qty; p2 also carries terms"),
    4: ("boq_rows", [2], "Honeywell BOQ; p2 is a blank letterhead page"), 5: ("boq_rows", [], "supplier quotation (vostok) with qty"),
    6: ("boq_rows", [], "CCTV BOQ"), 7: ("boq_rows", [], "ELM design sheet R1"), 8: ("boq_rows", [3], "FA design; p3 terms and conditions"),
    9: ("boq_rows", [], "VESDA design sheet, rotated"), 10: ("not_boq", [1], "emergency lighting warranty letter (draft)"),
    11: ("boq_matrix", [], "schedule of materials, floor x item"), 12: ("boq_matrix", [], "schedule of materials, floor x item"),
    13: ("boq_matrix", [], "schedule of materials, floor x item"), 14: ("boq_matrix", [], "schedule, floor x item"),
    15: ("boq_matrix", [], "schedule, floor x item, void notes"), 16: ("boq_matrix", [], "schedule, floor x item"),
    17: ("boq_matrix", [], "schedule, floor x item, void notes"), 18: ("boq_rows", [], "BOQ with description / qty, no part numbers"),
    19: ("boq_rows", [], "EML design sheet (1 row)"), 20: ("boq_rows", [], "FA design sheet"), 21: ("boq_rows", [], "EML design sheet (small batch)"),
    22: ("boq_rows", [2], "FA&EML quotation; p2 terms and conditions"), 23: ("boq_rows", [], "ASD design sheet"),
    24: ("boq_rows", [], "CBS design (Teknoware price list with qty), rotated"), 25: ("boq_rows", [], "FAS design sheet, 2 pages"),
    26: ("boq_rows", [], "CBS material schedule R1; p2 quantity column headed MOUNTING -> a person confirms it is the quantity"),
    27: ("boq_rows", [], "CBS material schedule R3 (same caveat on p2)"), 28: ("boq_rows", [], "FAS schedule of equipment, 3 pages"),
    29: ("boq_rows", [], "CBS design sheet, rotated"), 30: ("boq_rows", [], "FAS design sheet, 2 pages"), 31: ("boq_rows", [], "PAVA design sheet"),
    32: ("boq_rows", [], "PAVA design sheet"), 33: ("not_boq", [1, 2, 3], "road geometric design drawings"),
    34: ("not_boq", [1], "CBS shop drawing (WAM design)"), 35: ("boq_rows", [], "ELS design sheet"), 36: ("boq_rows", [], "Hochiki design sheet, rotated"),
    37: ("boq_rows", [], "FA design sheet R1"), 38: ("boq_rows", [], "standalone FA BOQ (description / qty)"), 39: ("boq_rows", [], "FAS design sheet, 3 pages"),
}
m = json.load(open("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json", encoding="utf-8"))
prim = {d["doc_key"]: d for d in m["documents"]}
idx = {e["doc_key"]: e for e in json.load(open("C:/t/r2x/renders/RENDER-INDEX.json", encoding="utf-8"))["documents"]}
rows = []
for n, b in enumerate(m["boq_candidates"], 1):
    d = b if b.get("sha256") else prim[b["doc_key"]]
    cls, nonpages, note = T[n]
    rows.append({"n": n, "doc_key": b["doc_key"], "sha256": d["sha256"], "pages": idx[b["doc_key"]].get("page_count"), "class": cls,
                 "non_table_pages": nonpages, "note": note, "also_in_document_sample": bool(b.get("also_primary"))})
import collections
out = {"status": "AI visual triage (Claude), provisional, before any label or prediction; confirm before freezing a BOQ batch", "candidates": rows,
       "counts": dict(collections.Counter(r["class"] for r in rows)), "pages_total": sum(r["pages"] or 0 for r in rows),
       "non_table_pages_in_boq_documents": sum(len(r["non_table_pages"]) for r in rows if r["class"] != "not_boq")}
pathlib.Path("C:/t/iso/work/r2x/r14/BOQ-CANDIDATE-TRIAGE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(out["counts"], "pages", out["pages_total"], "non-table pages in BOQ docs", out["non_table_pages_in_boq_documents"])
