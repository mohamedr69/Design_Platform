"""E, evaluated OFFLINE and independently of any model call: for every drawing-size page of the original 12 pilot
documents and the 3 new continuation documents (hash-checked staged copies), the candidate's `locate_title_block`
(C:/t/iso/cand-ai2, deterministic; bounded local OCR where the text layer is thin) -> route, located area share, and
whether the LABELLED own identity (and revision) is inside the located area (found by the page's text layer; by the
located-area OCR for a scan). Also the discovery image's resolution: the accepted full-page render (1600 px long side)
versus E's located crop (<= 1568 px). Labels are used only here, in the evaluation -- never by the locator.
Writes locator/LOCATOR-EVAL.json."""
import hashlib
import json
import os
import pathlib
import sys
import time

os.environ["AI_ENABLED"] = "false"
sys.path.insert(0, "C:/t/iso/cand-ai2/backend")
os.chdir("C:/t/iso/cand-ai2/backend")
import pymupdf  # noqa: E402

from app.ai import evidence_reader as er  # noqa: E402
from app.services import title_block as tb  # noqa: E402

W = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
sha = lambda b: hashlib.sha256(b).hexdigest()
pilot = json.loads(pathlib.Path("C:/t/iso/work/r2x/ai-pilot/PILOT-SAMPLE.json").read_text(encoding="utf-8"))["documents"]
cont = json.loads((W / "CONTINUATION-SAMPLE.json").read_text(encoding="utf-8"))["documents"]
reg = {d["sha256"]: d for d in json.loads((W / "labels-v2/PILOT-REGISTER-LABELS.v2.json").read_text(encoding="utf-8"))["documents"]}
reg.update({d["sha256"]: d for d in json.loads((W / "labels-continuation/CONT-REGISTER-LABELS.json").read_text(encoding="utf-8"))["documents"]})
seen, rows = set(), []
for d in pilot + cont:
    if d["sha256"] in seen:
        continue
    seen.add(d["sha256"])
    data = open("\\\\?\\" + d["staged_path"].replace("/", "\\"), "rb").read()
    assert sha(data) == d["sha256"]
    doc = pymupdf.open(stream=data, filetype="pdf")
    page = doc[0]
    lab = reg[d["sha256"]]["labels"]
    t0 = time.perf_counter()
    clip, route = er.locate_title_block(page, None, ocr_timeout=20.0)
    secs = round(time.perf_counter() - t0, 2)
    row = {"doc": d["doc_key"], "sha256": d["sha256"], "set": "continuation" if d in cont else "pilot", "size_pt": [round(page.rect.width), round(page.rect.height)],
           "rotation": page.rotation, "drawing_sheet": tb.is_drawing_sheet(page), "route": route, "locate_s": secs}
    if clip is None:
        row["note"] = "not a drawing sheet: discovered whole, as accepted"
        rows.append(row)
        continue
    row["area_share"] = round(clip.get_area() / page.rect.get_area(), 3)
    row["full_page_px_per_pt"] = round(1600 / max(page.rect.width, page.rect.height), 3)
    row["located_px_per_pt"] = round(min(300 / 72, 1568 / max(clip.width, clip.height)), 3)
    found = {}
    for field, value in (("identity", lab.get("reference")), ("revision", lab.get("revision"))):
        if not value or value in ("absent", "n/a"):
            continue
        hits = [r * page.rotation_matrix for r in page.search_for(value)] if page.get_text().strip() else []
        how = "text_layer"
        if not hits:
            words = tb.ocr_word_lines(page, clip, dpi=200)
            hits = [pymupdf.Rect(l.x0, l.y0, l.x1, l.y1) for l in words if value.replace(" ", "") in l.text.replace(" ", "")]
            how = "located_area_ocr"
        inside = [h for h in hits if clip.contains(h) or clip.intersects(h)]
        found[field] = {"value": value, "how": how, "occurrences": len(hits), "inside_located_area": len(inside) > 0}
    row["labelled_in_located_area"] = found
    rows.append(row)
drawing = [r for r in rows if r.get("drawing_sheet")]
summary = {"drawing_sheets": len(drawing), "routes": {r["route"]: sum(1 for x in drawing if x["route"] == r["route"]) for r in drawing},
           "identity_inside": sum(1 for r in drawing if r.get("labelled_in_located_area", {}).get("identity", {}).get("inside_located_area")),
           "identity_checked": sum(1 for r in drawing if "identity" in r.get("labelled_in_located_area", {})),
           "revision_inside": sum(1 for r in drawing if r.get("labelled_in_located_area", {}).get("revision", {}).get("inside_located_area")),
           "revision_checked": sum(1 for r in drawing if "revision" in r.get("labelled_in_located_area", {})),
           "median_sharpening": sorted(r["located_px_per_pt"] / r["full_page_px_per_pt"] for r in drawing)[len(drawing) // 2] if drawing else None}
(W / "locator").mkdir(exist_ok=True)
(W / "locator/LOCATOR-EVAL.json").write_text(json.dumps({"mode": "OFFLINE, deterministic (no model call)", "candidate": "C:/t/iso/cand-ai2",
                                                        "summary": summary, "pages": rows}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for r in rows:
    print(r["sha256"][:12], r["size_pt"], r["route"], r.get("area_share"), r.get("full_page_px_per_pt"), "->", r.get("located_px_per_pt"),
          {k: (v["inside_located_area"], v["how"], v["occurrences"]) for k, v in r.get("labelled_in_located_area", {}).items()}, r["locate_s"], "s")
print(json.dumps(summary))
