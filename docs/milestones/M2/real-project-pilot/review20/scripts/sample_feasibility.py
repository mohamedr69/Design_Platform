"""OFFLINE sample feasibility for the DRAFT experiment (no model request; reads hash-checked staged copies only). From the
415-document exploration manifest (non-sealed; sealed projects are not in it), excludes every document ever predicted
or held out (small batch, pilot, continuation, the two BOQ sheets, the review05 holdout sets -- by sha256 found in those
files), and tabulates what is available per proposed stratum: layout (drawing sheet > 1300 pt / A3-A4), rotation of
page 1, text layer vs scan-like, page count vs the reader's 4-page scope, file type (unsupported input shapes listed,
never truncated silently). Writes feasibility/SAMPLE-FEASIBILITY.json."""
import collections
import hashlib
import json
import pathlib
import re

import pymupdf

W = pathlib.Path("C:/t/iso/work/r2x")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
LONG = "\\\\?\\"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
man = json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
exposed = set()
for f in [W / "SMALL-BATCH.json", W / "ai-pilot/PILOT-SAMPLE.json", W / "ai-pilot-r18/CONTINUATION-SAMPLE.json"] + sorted((PILOT / "review05/holdout").glob("*.json")):
    exposed |= set(re.findall(r"[0-9a-f]{64}", f.read_text(encoding="utf-8", errors="replace")))
exposed |= {"6153dfe701f5" + "", "719f8714d2a75673c8ba390a884a2d2889b2438fd587eaa2c42f62d75f344fec"}
docs = [d for d in man["documents"] if d.get("sha256") and d["sha256"] not in exposed and not d["sha256"].startswith("6153dfe701f5")]
rows, shapes = [], collections.Counter()
for d in docs:
    if d["extension"] != ".pdf":
        shapes[f"unsupported_input:{d['extension']}"] += 1
        rows.append({"doc": d["doc_key"], "ep": d["ep"], "shape": f"unsupported_input:{d['extension']}"})
        continue
    try:
        pdf = pymupdf.open(stream=open(LONG + d["staged_path"].replace("/", "\\"), "rb").read(), filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        rows.append({"doc": d["doc_key"], "ep": d["ep"], "shape": f"unreadable:{type(exc).__name__}"})
        shapes["unreadable"] += 1
        continue
    p = pdf[0]
    n = pdf.page_count
    text = len(p.get_text().strip())
    row = {"doc": d["doc_key"], "ep": d["ep"], "stratum": d.get("stratum"), "pages": n, "rotation": p.rotation,
           "layout": "drawing_sheet" if max(p.rect.width, p.rect.height) > 1300 else "a3_a4",
           "text_layer": "text" if text >= 80 else "scan_like", "shape": "pdf" if n <= 4 else "pdf_pages_beyond_reader_scope"}
    shapes[row["shape"]] += 1
    rows.append(row)
pdfs = [r for r in rows if r.get("layout")]
strata = collections.Counter((r["layout"], "rotated" if r["rotation"] else "rot0", r["text_layer"]) for r in pdfs if r["pages"] <= 4)
by_project = collections.Counter(r["ep"] for r in pdfs if r["pages"] <= 4)
out = {"mode": "OFFLINE feasibility (no model request)", "manifest_sha256": sha(W / "EXPLORATION-MANIFEST.json"), "excluded_exposed": len(man["documents"]) - len(docs),
       "candidates": len(docs), "input_shapes": dict(shapes),
       "strata_within_reader_scope": {" / ".join(k): v for k, v in sorted(strata.items())}, "projects_within_scope": dict(by_project), "rows": rows}
d = pathlib.Path("C:/t/iso/work/r2x/review20/feasibility")
d.mkdir(parents=True, exist_ok=True)
(d / "SAMPLE-FEASIBILITY.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("excluded_exposed", "candidates", "input_shapes", "strata_within_reader_scope", "projects_within_scope")}, indent=1))
