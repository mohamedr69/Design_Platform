import json, re, sys, pymupdf
fs = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-SAMPLE.json", encoding="utf-8"))
staged = {f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/"): d["staged_path"] for d in fs["documents"]}
for arg in sys.argv[1:]:
    name, _, pn = arg.partition("#"); pn = int(pn or 1) - 1
    doc = next(k for k in staged if k.endswith(name)); pdf = pymupdf.open(staged[doc]); pg = pdf[pn]; m = pg.rotation_matrix
    W, H = (pg.rect * m).width, (pg.rect * m).height
    rows = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            s = " ".join(sp["text"] for sp in l["spans"]).strip(); r = pymupdf.Rect(l["bbox"]) * m
            if s and r.x0 > W * 0.62 and r.y0 > H * 0.55: rows.append((round(r.y0), round(r.x0), round(r.x1), round(r.y1), s[:60]))
    print("=====", arg, round(W), round(H), "rot", pg.rotation, "text", len(pg.get_text()), "pages", pdf.page_count, "shown", len(rows))
    for r in sorted(rows)[-int(sys.argv[0] and 70):]: print("  ", r)
