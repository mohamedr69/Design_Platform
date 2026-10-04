"""Crops for the 13 unresolved Review 07 source findings (packet v2 FINDINGS-INDEX.json, unchanged): for every item,
the staged exposed copy (pilot / holdout stage, hash-checked) is opened at the item's page and each literal the finding
names (the value read and the label) is searched in the page's text layer; each hit is cropped with context
(200 dpi, 110 pt around it) and the finding's two literals are also shown together when both are found. When a
literal is not in the text layer (a scan), the crop is the page's title-block quadrant plus the top-left quadrant,
marked 'literal not located'. Exposed documents only; nothing is sent to a model; the page images of packet v2 stay the
reference."""
import hashlib
import json
import pathlib
import re

import pymupdf

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
FIND = PILOT / "review08/human-review-packet-v2/FINDINGS-INDEX.json"
OUT = pathlib.Path("C:/t/r2x/worklist/findings")
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = "\\\\?\\"
staged = {}
for f in ("FROZEN-SAMPLE.json", "review05/holdout/HOLDOUT-SAMPLE.json"):
    for d in json.loads((PILOT / f).read_text(encoding="utf-8"))["documents"]:
        staged[f"EP-{d['ep']}/{d['relative_path']}".replace("\\", "/")] = d
groups = json.loads(FIND.read_text(encoding="utf-8"))["groups"]


def literals(text: str) -> list[str]:
    """The distinct literals a finding cell names ('A / -B / -C', 'A, B', 'A & ...')."""
    out = []
    for part in re.split(r"\s*(?:,|/ -|&)\s*", str(text or "")):
        part = part.strip(" `.")
        if part.isdigit() and out and "-" in out[-1]:
            part = out[-1].rsplit("-", 1)[0] + "-" + part      # 'K&A-WTRAN-017671 / -000913': the shared prefix
        if len(part) >= 4 and not part.lower().startswith(("page ", "no component", "n/a", "the sheet")):
            out.append(part)
    return out


index = {"findings_index_sha256": hashlib.sha256(FIND.read_bytes()).hexdigest(), "items": []}
for g in groups:
    wanted = literals(g.get("value_read")) + literals(g.get("label"))
    for it in g["items"]:
        d = staged[it["doc"].replace("\\", "/")]
        path = PREFIX + d["staged_path"].replace("/", "\\")
        data = open(path, "rb").read()
        assert hashlib.sha256(data).hexdigest() == d["sha256"], it["doc"]
        pno = int(it["page"])
        rec = {"group": g["group"], "status": g["status"], "item": it["item"], "doc": it["doc"], "page": pno, "page_image_v2": it["page_image"], "crops": [], "not_located": []}
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            page = pdf[pno - 1]
            hits = []
            for lit in wanted:
                rects = page.search_for(lit) or page.search_for(lit.replace(" ", ""))
                if not rects and "-" in lit:
                    rects = page.search_for(lit.split("-")[0] + "-" + lit.split("-")[1]) if len(lit.split("-")) > 1 else []
                if rects:
                    r = rects[0]
                    hits.append((lit, r))
                    clip = pymupdf.Rect(r.x0 - 110, r.y0 - 110, r.x1 + 110, r.y1 + 110) & page.rect
                    name = f"{g['group']}-{it['item']}-p{pno}-{len(rec['crops']) + 1}.jpg"
                    try:
                        page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72), clip=clip).save(str(OUT / name), jpg_quality=88)
                        rec["crops"].append({"file": name, "literal_searched": lit, "rect_pt": [round(v, 1) for v in r]})
                    except Exception as exc:  # noqa: BLE001 -- a rotated page's hit outside the clip space: region crops below
                        rec["not_located"].append(lit)
                        rec.setdefault("crop_errors", []).append(f"{lit}: {type(exc).__name__}")
                else:
                    rec["not_located"].append(lit)
            if len(hits) >= 2 and not rec.get("crop_errors"):
                u = pymupdf.Rect(hits[0][1])
                for _, r in hits[1:]:
                    u |= r
                clip = pymupdf.Rect(u.x0 - 60, u.y0 - 60, u.x1 + 60, u.y1 + 60) & page.rect
                name = f"{g['group']}-{it['item']}-p{pno}-together.jpg"
                zoom = min(200 / 72, 3000 / max(clip.width, clip.height))
                page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip).save(str(OUT / name), jpg_quality=85)
                rec["crops"].append({"file": name, "literal_searched": " + ".join(h[0] for h in hits)})
            if rec["not_located"] or not rec["crops"]:
                r = page.rect
                for tag, clip in (("tb", pymupdf.Rect(r.x0 + r.width * 0.5, r.y0 + r.height * 0.55, r.x1, r.y1)),
                                  ("top", pymupdf.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * 0.35))):
                    name = f"{g['group']}-{it['item']}-p{pno}-{tag}.jpg"
                    zoom = min(200 / 72, 2600 / max(clip.width, clip.height))
                    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip).save(str(OUT / name), jpg_quality=85)
                    rec["crops"].append({"file": name, "region": tag, "note": "literal not located in the text layer: region crop"})
        index["items"].append(rec)
        print(g["group"], it["item"], "crops", len(rec["crops"]), "not located", rec["not_located"])
(OUT / "FINDING-CROPS.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
