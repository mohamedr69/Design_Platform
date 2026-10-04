"""Offline renders for RD-M1 (GC-01). Reads only the COPIED review plot PDF, the
COPIED wall index and the snapshot dump; writes PNGs only to the output folder
given. Never imports application code (no DB engine, no settings).

Each crop is rendered twice at the SAME page box and DPI:
  *-A-source.png    the review plot of the source DWG (no markers)
  *-B-plan.png      the same, with the STORED plan reconstructed on it
Overlay legend (drawn in the image footer):
  red ring          the review's point for the change ("at")
  purple box/cross  insert of an APPROVED change (drawn by Apply)
  blue   box/cross  insert of a PROPOSED change (review: drawn by Apply; interface: not drawn)
  grey   box/cross  insert of a SKIPPED change (not drawn)
  red X             symbol to be erased (remove/replace)
  pink box          a module's "FOR ..." note footprint (as service._note/_footprint compute it)
  orange lines      wall-index segments (walls.pkl) within the crop
  small cyan dots   existing device symbols known to the plan (candidates)
"""
import hashlib
import io
import json
import math
import os
import pickle
import sys

import pymupdf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PDF = os.path.join(ROOT, "src", "EP-30880", "review-plot.pdf")
WALLS = os.path.join(ROOT, "src", "EP-30880", "walls.pkl")
CASE = os.path.join(ROOT, "work", "case")

row = json.load(open(os.path.join(CASE, "project_redesign.json"), encoding="utf-8"))[0]
sheets = {s["index"]: s for s in json.load(open(os.path.join(CASE, "project_drawing_reviews.json"), encoding="utf-8"))[0]["sheets"]}
with open(WALLS, "rb") as f:
    CELLS = pickle.load(f)          # the platform's own wall index, copied; dict[(i,j)] -> [(ax,ay,bx,by)]
CELL = 2.0

COL = {"approved": (128, 0, 170), "proposed": (37, 99, 235), "skipped": (140, 140, 140), "pending": (37, 99, 235),
       "failed": (200, 0, 200)}


def page_of(g, x, y):
    return ((x - g["bx"]) / g["a"], (g["by"] - y) / g["a"])


def walls_in(g, box):
    x0, y1 = g["a"] * box[0] + g["bx"], -g["a"] * box[1] + g["by"]
    x1, y0 = g["a"] * box[2] + g["bx"], -g["a"] * box[3] + g["by"]
    seen, out = set(), []
    for i in range(int(math.floor(x0 / CELL)) - 1, int(math.floor(x1 / CELL)) + 2):
        for j in range(int(math.floor(y0 / CELL)) - 1, int(math.floor(y1 / CELL)) + 2):
            for s in CELLS.get((i, j), ()):
                if s not in seen:
                    seen.add(s)
                    out.append(s)
    return out


def note_of(c):  # read-only replica of service._note (service.py:830-849)
    ins, face = c.get("insert") or {}, c.get("interface") or {}
    if not ins.get("block") or not face.get("note_height"):
        return None
    h, (sx, sy) = face["note_height"], ins["seen"]
    text = f"FOR {face['for']}"
    note = {"text": text, "h": h, "at": [sx + (face.get("half") or 0) + 0.4 * h, sy - h / 2], "rot": 0, "align": "left"}
    f = ins.get("facing")
    if f:
        out_m = (face.get("depth") or face.get("half") or 0) + 0.4 * h
        fx, fy = sx + f[0] * out_m, sy + f[1] * out_m
        if abs(f[0]) > 0.5:
            note.update(at=[fx, sy - h / 2], align="left" if f[0] > 0 else "right")
        else:
            note.update(at=[sx + h / 2, fy], rot=90, align="left" if f[1] > 0 else "right")
    (nx, ny), length = note["at"], len(text) * h * 0.85
    if note["rot"]:
        return (nx - h, ny - length, nx, ny) if note["align"] == "right" else (nx - h, ny, nx, ny + length)
    return (nx - length, ny, nx, ny + h) if note["align"] == "right" else (nx, ny, nx + length, ny + h)


def sym_box(c):  # read-only replica of service._footprint symbol part (service.py:852-864)
    ins = c["insert"]
    x, y = ins["seen"]
    face = c.get("interface") or {}
    if face.get("half") and face.get("depth"):
        hw, hh = face["half"], face["depth"]
        if round(float(ins.get("rotation") or 0)) % 180 == 90:
            hw, hh = hh, hw
    else:
        hw = hh = ins.get("radius") or 0.25
    return (x - hw, y - hh, x + hw, y + hh)


def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def render(doc, page, box, dpi):
    pg = doc[page]
    clip = pymupdf.Rect(*box)
    pix = pg.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def caption(img, lines):
    f = font(max(14, img.width // 70))
    pad = 6
    h = (f.size + 4) * len(lines) + 2 * pad
    out = Image.new("RGB", (img.width, img.height + h), "white")
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    for k, line in enumerate(lines):
        d.text((pad, img.height + pad + k * (f.size + 4)), line, fill=(0, 0, 0), font=f)
    return out


def overlay(img, page, box, dpi, only=None, label_ids=True):
    g = sheets[page]["geometry"]
    s = dpi / 72.0
    P = lambda p: ((p[0] - box[0]) * s, (p[1] - box[1]) * s)  # noqa: E731
    PM = lambda x, y: P(page_of(g, x, y))  # noqa: E731
    d = ImageDraw.Draw(img)
    r = max(8, img.width // 90)
    w = max(2, img.width // 500)
    f = font(max(11, img.width // 110))
    for ax, ay, bx, by in walls_in(g, box):
        d.line((*PM(ax, ay), *PM(bx, by)), fill=(245, 130, 32), width=1)
    shown = []
    for c in row["changes"]:
        if c["page"] != page or (only and c["id"] not in only):
            continue
        col = COL.get(c["status"], (0, 0, 0))
        if c.get("at"):
            x, y = P(c["at"])
            if -r < x < img.width + r and -r < y < img.height + r:
                d.ellipse((x - r, y - r, x + r, y + r), outline=(220, 38, 38), width=w)
        for k in c.get("candidates") or []:
            x, y = P(k["page"])
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(0, 170, 200))
        if c.get("remove"):
            x, y = P(c["remove"]["page"])
            d.line((x - r, y - r, x + r, y + r), fill=(220, 38, 38), width=w + 1)
            d.line((x - r, y + r, x + r, y - r), fill=(220, 38, 38), width=w + 1)
            shown.append(c)
        if c.get("insert") and c["insert"].get("seen"):
            b = sym_box(c)
            p0, p1 = PM(b[0], b[1]), PM(b[2], b[3])
            d.rectangle((min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])), outline=col, width=w)
            x, y = PM(*c["insert"]["seen"])
            d.line((x - r * 0.6, y, x + r * 0.6, y), fill=col, width=w)
            d.line((x, y - r * 0.6, x, y + r * 0.6), fill=col, width=w)
            nb = note_of(c)
            if nb:
                q0, q1 = PM(nb[0], nb[1]), PM(nb[2], nb[3])
                d.rectangle((min(q0[0], q1[0]), min(q0[1], q1[1]), max(q0[0], q1[0]), max(q0[1], q1[1])),
                            outline=(255, 0, 140), width=1)
            if label_ids:
                tag = (c["interface"]["code"] + " " + c["interface"]["for"]) if c.get("interface") else c["id"][:6]
                d.text((x + r * 0.7, y - r * 1.2), tag[:28], fill=col, font=f)
            shown.append(c)
    return shown


def crop(doc, out_dir, cid, page, box, title, only=None, width_px=1400, extra=None):
    dpi = max(36, min(600, int(width_px / ((box[2] - box[0]) / 72.0))))
    a = render(doc, page, box, dpi)
    b = a.copy()
    shown = overlay(b, page, box, dpi, only=only)
    sh = sheets[page]
    base = [f"{cid}  |  GC-01 sheet {sh['name']} ({sh['floor']}), page index {page}  |  page box {list(map(lambda v: round(v, 1), box))} pt  |  {dpi} dpi"]
    ca = caption(a, base + ["IMAGE TYPE: SOURCE (review plot of source DWG sha256 66043c11...; no markers)"] + (extra or []))
    cb = caption(b, base + ["IMAGE TYPE: PLAN PREVIEW reconstructed offline from stored plan (project_redesign id 1) -- NOT applied output",
                            "red ring=review point; PURPLE=approved insert (drawn by Apply); blue=proposed; grey=skipped; red X=erase; pink=module note; orange=wall index; green boxes round E = source plot content"]
                 + (extra or []))
    pa, pb = os.path.join(out_dir, f"{cid}-A-source.png"), os.path.join(out_dir, f"{cid}-B-plan.png")
    ca.save(pa, optimize=True)
    cb.save(pb, optimize=True)
    return {"id": cid, "page": page, "box": box, "dpi": dpi, "title": title,
            "changes": [c["id"] for c in shown], "files": [os.path.basename(pa), os.path.basename(pb)]}


def bbox_of(ids, page, margin=40):
    pts = []
    for c in row["changes"]:
        if c["id"] in ids and c["page"] == page:
            for p in ([c["at"]] if c.get("at") else []) + ([c["insert"]["page"]] if c.get("insert") else []) \
                    + ([c["remove"]["page"]] if c.get("remove") else []):
                pts.append(p)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin]


def main(out_dir, spec_path):
    os.makedirs(out_dir, exist_ok=True)
    doc = pymupdf.open(PDF)
    spec = json.load(open(spec_path, encoding="utf-8"))
    results = []
    for item in spec:
        if item.get("full"):
            page = item["page"]
            box = list(sheets[page]["plan"])     # plan area only: title block / legend excluded
            r = crop(doc, out_dir, item["id"], page, box, item["title"], width_px=item.get("width", 2200),
                     extra=item.get("extra"))
        else:
            box = item.get("box") or bbox_of(set(item["changes"]), item["page"], item.get("margin", 40))
            r = crop(doc, out_dir, item["id"], item["page"], box, item["title"], only=set(item.get("only") or []) or None,
                     width_px=item.get("width", 1400), extra=item.get("extra"))
        for fn in r["files"]:
            r.setdefault("sha256", {})[fn] = hashlib.sha256(open(os.path.join(out_dir, fn), "rb").read()).hexdigest()
        results.append(r)
        print(r["id"], r["dpi"], len(r["changes"]))
    doc.close()
    json.dump(results, open(os.path.join(out_dir, "_render-index.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
