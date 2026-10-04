"""Dump title-block label lines (drawing no / rev) with neighbourhood, in display (rotated) coordinates."""
import json, re, sys, pymupdf
R = sys.argv[1]
fs = json.load(open(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\FROZEN-SAMPLE.json", encoding="utf-8"))
staged = {f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/"): d["staged_path"] for d in fs["documents"]}
LABEL = re.compile(r"^(?:DRAWING\s*(?:NO|NUMBER)|DWG\.?\s*(?:NO|NUMBER)|SHEET\s*NO|REV(?:ISION)?\b|Rev\.?)", re.I)
def lines_of(pg):
    m = pg.rotation_matrix; out = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            s = " ".join(sp["text"] for sp in l["spans"]).strip()
            if not s: continue
            r = pymupdf.Rect(l["bbox"]) * m
            dx, dy = l["dir"]; ddx = dx * m.a + dy * m.c; ddy = dx * m.b + dy * m.d
            out.append((r, s, (round(ddx), round(ddy))))
    return out
for name in sys.argv[2:]:
    doc = next(k for k in staged if k.endswith(name)); pdf = pymupdf.open(staged[doc]); pn = 0
    if "#" in name: pass
    pg = pdf[pn]; lines = lines_of(pg); W, H = pg.rect.width, pg.rect.height
    print("=====", name, round(W), round(H), "rot", pg.rotation, "lines", len(lines))
    for r, s, d in lines:
        if LABEL.match(s) and d == (1, 0):
            print(f"  LABEL {r.x0:7.1f} {r.y0:7.1f} {r.x1:7.1f} {r.y1:7.1f} | {s[:60]}")
            for rr, t, dd in lines:
                if t is s or dd != (1, 0): continue
                if (-4 < rr.y0 - r.y0 < 40 and rr.x1 > r.x0 - 30 and rr.x0 < r.x1 + 200) or (abs(rr.y0 - r.y0) < 5 and 0 <= rr.x0 - r.x1 < 250):
                    print(f"      {rr.x0:7.1f} {rr.y0:7.1f} {rr.x1:7.1f} {rr.y1:7.1f} | {t[:70]}")
