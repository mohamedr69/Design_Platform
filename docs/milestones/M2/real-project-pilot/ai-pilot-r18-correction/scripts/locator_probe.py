"""Development probe (offline): where the locator's labels and the labelled identity sit on the sheets it missed."""
import json
import os
import sys

os.environ["AI_ENABLED"] = "false"
sys.path.insert(0, "C:/t/iso/cand-ai2/backend")
os.chdir("C:/t/iso/cand-ai2/backend")
import pymupdf  # noqa: E402

from app.services import title_block as tb  # noqa: E402

LONG = "\\\\?\\"
P = json.load(open("C:/t/iso/work/r2x/ai-pilot/PILOT-SAMPLE.json", encoding="utf-8"))["documents"] + \
    json.load(open("C:/t/iso/work/r2x/ai-pilot-r18/CONTINUATION-SAMPLE.json", encoding="utf-8"))["documents"]
for pre, val in (("7577b344abed", "AR-101"), ("87c43a7d1395", "EML-09"), ("e740af954610", "TEL-00")):
    d = [x for x in P if x["sha256"].startswith(pre)][0]
    page = pymupdf.open(LONG + d["staged_path"].replace("/", "\\"))[0]
    w, h = page.rect.width, page.rect.height
    lines = tb.page_lines(page)
    labs = [l for l in lines if tb._in_zone(l, w, h) and (tb._NUMBER_LABEL.match(l.text) or tb._REV_LABEL.match(l.text))]
    print(pre, "runs", len(lines), "labels", [(round(l.x0), round(l.y0), l.text, "NUMBER" if tb._NUMBER_LABEL.match(l.text) else "REV") for l in labs])
    print("  value at", [(round(r.x0), round(r.y0)) for r in [r * page.rotation_matrix for r in page.search_for(val)]], "| strip", tb.title_block_strip(page))
    near = [l for l in lines if tb._in_zone(l, w, h) and any(k in l.text.upper() for k in ("NO", "NUMBER", "SHEET"))]
    print("  NO-ish runs", [(round(l.x0), round(l.y0), l.text) for l in near][:12])
