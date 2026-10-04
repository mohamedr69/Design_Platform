"""R14-03 binding check: document sha256 -> page -> image, for every evidence image of the AI source review.

For each image: the unit's document is resolved to its staged copy (FROZEN-SAMPLE / HOLDOUT-SAMPLE for exposed
documents, SMALL-STAGE for the small batch), the copy's SHA-256 is checked against the manifest, the claimed page is
rendered from it, and the image is located in that render by normalised cross-correlation (FFT, multi-scale, then
refined at full resolution). A whole-page image is compared to the page render resized to its size.
CONTROL: the same search on other pages of the document (up to 2), or on another document's page 1 when the document
has one page. Bound = claimed-page NCC >= 0.90 AND at least 0.10 above the best control.
Nothing is sent anywhere; the reviewer's files are only read (their hashes are checked against REVIEW-MANIFEST.json)."""
import hashlib
import io
import json
import pathlib
import re
import sys

import numpy as np
import pymupdf
from PIL import Image

R = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-14")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
OUT = pathlib.Path("C:/t/iso/work/r2x/r14/BINDING.json")
# run 1 (BINDING.defective-run-1.json) accumulated the local variance in float32 -- scores > 1, discarded; kept as history
PREFIX = "\\\\?\\"
sha = lambda b: hashlib.sha256(b).hexdigest()

man = json.loads((R / "REVIEW-MANIFEST.json").read_text(encoding="utf-8"))
files = man.get("files") or man
for k, v in files.items():
    assert sha((R / k).read_bytes()) == (v["sha256"] if isinstance(v, dict) else v), k
review = json.loads((R / "AI-SOURCE-REVIEW.json").read_text(encoding="utf-8"))

staged = {}
for f in ("FROZEN-SAMPLE.json", "review05/holdout/HOLDOUT-SAMPLE.json", "review05/holdout/HOLDOUT-BOQ-SET.json"):
    d = json.loads((PILOT / f).read_text(encoding="utf-8"))
    for x in d.get("documents") or d.get("sheets"):
        staged[f"EP-{x['ep']}/{x['relative_path']}".replace("\\", "/")] = (x["staged_path"], x["sha256"])
for x in json.loads(pathlib.Path("C:/t/r2x/small-stage/SMALL-STAGE.json").read_text(encoding="utf-8"))["files"]:
    staged[x["doc_key"]] = (x["path"], x["sha256"])
crit = {c: it["page"] for it in json.loads(pathlib.Path("C:/t/iso/work/r2x/eval/DISAGREEMENTS-WITH-CROPS.json").read_text(encoding="utf-8"))["critical_false_accepts"]
        for c in it["crops"]}
docs_cache, pages_cache = {}, {}


def open_doc(key):
    if key not in docs_cache:
        path, h = staged[key]
        data = open(PREFIX + path.replace("/", "\\"), "rb").read()
        assert sha(data) == h, key
        docs_cache[key] = (pymupdf.open(stream=data, filetype="pdf"), h)
    return docs_cache[key]


def render(key, page):
    ck = (key, page)
    if ck not in pages_cache:
        pdf, _ = open_doc(key)
        p = pdf[page - 1]
        z = min(200 / 72, 6000 / max(p.rect.width, p.rect.height))
        pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z), colorspace=pymupdf.csGRAY)
        pages_cache[ck] = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).astype(np.float32)
    return pages_cache[ck]


def resize(a, w, h):
    return np.asarray(Image.fromarray(a.astype(np.uint8)).resize((max(1, int(w)), max(1, int(h))), Image.BILINEAR), dtype=np.float32)


def ncc_map(img, tpl):
    """Normalised cross-correlation of tpl over img ('valid' positions), by FFT."""
    img = img.astype(np.float64)
    tpl = tpl.astype(np.float64)
    H, W = img.shape
    h, w = tpl.shape
    if h > H or w > W or h < 4 or w < 4:
        return None
    t = tpl - tpl.mean()
    tn = np.sqrt((t * t).sum())
    if tn == 0:
        return None
    fs = (H + h, W + w)
    corr = np.fft.irfft2(np.fft.rfft2(img, fs) * np.conj(np.fft.rfft2(t, fs)), fs)[:H - h + 1, :W - w + 1]
    c1 = np.cumsum(np.cumsum(np.pad(img, ((1, 0), (1, 0))), 0), 1)
    c2 = np.cumsum(np.cumsum(np.pad(img * img, ((1, 0), (1, 0))), 0), 1)
    s1 = c1[h:, w:] - c1[:-h, w:] - c1[h:, :-w] + c1[:-h, :-w]
    s2 = c2[h:, w:] - c2[:-h, w:] - c2[h:, :-w] + c2[:-h, :-w]
    var = np.maximum(s2 - s1 * s1 / (h * w), 1e-6)
    return corr / (tn * np.sqrt(var))


def locate(page_img, crop):
    """Best NCC of crop inside page_img over scales; coarse (page max 900 px) then refined at full resolution."""
    H, W = page_img.shape
    f = max(1.0, max(H, W) / 900)
    small = resize(page_img, W / f, H / f)
    best = (-1, None, None)
    for s in np.geomspace(0.12, 2.2, 48):                 # crop pixel size -> page-render pixel size
        ch, cw = crop.shape[0] * s, crop.shape[1] * s
        if ch > H or cw > W or ch / f < 6 or cw / f < 6:
            continue
        m = ncc_map(small, resize(crop, cw / f, ch / f))
        if m is None:
            continue
        idx = np.unravel_index(np.argmax(m), m.shape)
        if m[idx] > best[0]:
            best = (float(m[idx]), s, (idx[0] * f, idx[1] * f))
    if best[1] is None:
        return 0.0, None
    score, s0, (y0, x0) = best
    top = -1.0
    for s in np.linspace(s0 * 0.97, s0 * 1.03, 5):
        t = resize(crop, crop.shape[1] * s, crop.shape[0] * s)
        pad = int(3 * f) + 4
        ya, xa = int(max(0, y0 - pad)), int(max(0, x0 - pad))
        win = page_img[ya:int(min(H, y0 + t.shape[0] + pad)), xa:int(min(W, x0 + t.shape[1] + pad))]
        m = ncc_map(win, t)
        if m is not None:
            top = max(top, float(m.max()))
    return max(top, score), float(s0)


def whole_page(page_img, img):
    """Both reduced to the same small size (max 600 px, anti-aliased) so thin drawing lines do not decide the score."""
    k = 600 / max(img.shape)
    w, h = max(1, int(img.shape[1] * k)), max(1, int(img.shape[0] * k))
    a = np.asarray(Image.fromarray(page_img.astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=np.float64)
    b = np.asarray(Image.fromarray(img.astype(np.uint8)).resize((w, h), Image.LANCZOS), dtype=np.float64)
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))


def page_of(unit_page, name):
    m = re.search(r"-p(\d+)", name)
    if m:
        return int(m.group(1))
    if name in crit:
        return crit[name]
    return unit_page


results = []
CONTROL_DOC = "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf"
for a in review["answers"]:
    w = a["worklist_entry"]
    doc = (w.get("doc") or "").replace("\\", "/")
    for ev in a["evidence"]:
        p = pathlib.Path(ev["image"])
        data = p.read_bytes()
        assert sha(data) == ev["sha256"], p
        img = np.asarray(Image.open(io.BytesIO(data)).convert("L"), dtype=np.float32)
        page = page_of(int(w.get("page") or 1), p.name)
        pdf, h = open_doc(doc)
        full = render(doc, page)
        is_whole = abs(img.shape[1] / img.shape[0] - full.shape[1] / full.shape[0]) < 0.02 and ("-tb" not in p.name) and \
            re.fullmatch(r"[0-9a-f]{12,16}-p\d+\.jpg", p.name) is not None
        score = whole_page(full, img) if is_whole else locate(full, img)[0]
        controls = [q for q in range(1, pdf.page_count + 1) if q != page][:2]
        ctrl = []
        for q in controls:
            other = render(doc, q)
            ctrl.append(("page", q, whole_page(other, img) if is_whole else locate(other, img)[0]))
        if not controls:
            other = render(CONTROL_DOC, 1) if doc != CONTROL_DOC else render("EP-26208/Lux Calculation/Lux calculation/LUX CALCULATIN17.7.23.pdf", 1)
            ctrl.append(("other_document_p1", None, whole_page(other, img) if is_whole else locate(other, img)[0]))
        best_ctrl = max(c[2] for c in ctrl)
        bound = score >= 0.90 and score - best_ctrl >= 0.10
        results.append({"unit": a["id"], "image": p.name, "image_sha256": ev["sha256"], "doc": doc, "doc_sha256": h, "page": page,
                        "mode": "whole_page" if is_whole else "located_crop", "ncc_claimed_page": round(score, 4),
                        "controls": [{"kind": c[0], "page": c[1], "ncc": round(c[2], 4)} for c in ctrl], "bound": bound})
        print(a["id"], p.name, page, round(score, 3), "ctrl", round(best_ctrl, 3), "BOUND" if bound else "NOT BOUND", flush=True)
summary = {"images": len(results), "bound": sum(r["bound"] for r in results), "not_bound": [r for r in results if not r["bound"]]}
OUT.write_text(json.dumps({"method": __doc__, "summary": {k: v for k, v in summary.items() if k != "not_bound"},
                           "not_bound": summary["not_bound"], "results": results}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(summary["images"], "image uses;", summary["bound"], "bound;", len(summary["not_bound"]), "not bound")
