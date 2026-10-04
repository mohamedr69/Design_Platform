"""Every reviewer literal (observations with a digit, >= 5 chars) checked against the hash-verified source page's text
layer (exposed documents): present / absent / no text layer (a scan). Informs the amendment: a CONFIRMED ruling whose
literal differs from the label is not applied silently."""
import hashlib
import json
import pathlib
import re

import pymupdf

P = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
R = json.load(open("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-14/AI-SOURCE-REVIEW.json", encoding="utf-8"))
PREFIX = "\\\\?\\"
staged = {}
for f in ("FROZEN-SAMPLE.json", "review05/holdout/HOLDOUT-SAMPLE.json", "review05/holdout/HOLDOUT-BOQ-SET.json"):
    d = json.load(open(P / f, encoding="utf-8"))
    for x in d.get("documents") or d.get("sheets"):
        staged[f"EP-{x['ep']}/{x['relative_path']}".replace("\\", "/")] = (x["staged_path"], x["sha256"])
for x in json.load(open("C:/t/r2x/small-stage/SMALL-STAGE.json", encoding="utf-8"))["files"]:
    staged[x["doc_key"]] = (x["path"], x["sha256"])
out = []
for a in R["answers"]:
    doc = a["worklist_entry"]["doc"].replace("\\", "/")
    if doc.endswith(".docx"):
        continue
    path, h = staged[doc]
    data = open(PREFIX + path.replace("/", "\\"), "rb").read()
    assert hashlib.sha256(data).hexdigest() == h
    pdf = pymupdf.open(stream=data, filetype="pdf")
    pg = 9 if a["id"] == "F11/C0244" else int(a["worklist_entry"].get("page") or 1)
    text = pdf[pg - 1].get_text()
    flat = re.sub(r"\s+", "", text)
    for k, v in (a["observations"] or {}).items():
        if isinstance(v, str) and len(v) >= 5 and re.search(r"\d", v):
            state = "no_text_layer" if len(text.strip()) < 40 else ("present" if (v in text or re.sub(r"\s+", "", v) in flat) else "absent")
            out.append({"unit": a["id"], "status": a["status"], "field": k, "literal": v, "page": pg, "text_layer": state})
            print(a["id"], a["status"], k, repr(v), state)
pathlib.Path("C:/t/iso/work/r2x/r14/LITERAL-CHECK.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
