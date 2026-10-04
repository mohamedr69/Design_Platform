"""R14-03 binding, method 2 (regeneration): every evidence image the AI source review used is REGENERATED from the
hash-verified staged source, with the exact recipe that first produced it, into a temporary folder, and compared with
the reviewer's copy (byte-identical, else pixel NCC at the same size). A regenerated image that equals the evidence
image binds document sha256 -> page -> image by construction, including pages whose content repeats (identical
divider headers), which appearance matching alone cannot separate.

Recipes (each script asserts the source SHA-256 before rendering):
  findings crops       worklist/finding_crops.py + finding_crops_ocr.py (Review 13, unchanged; output folder redirected)
  small-batch crops    worklist/small_batch_crops.py (output folder redirected)
  critical crops       worklist/critical_crops.py (output folder and its JSON redirected)
  renders              r2_render.py's page recipe (whole page: zoom min(1600/max side, 150/72), JPEG 80; title-block crop:
                       right 50 % x bottom 45 %, 200 dpi, JPEG 85)
  H-06 rows            the Review 13 inline recipe (session transcript): EP-8430 page 1, row band y +/- 45 px at the
                       extractor's render dpi, x 25..2391, zoom 3, PNG
  packet v2 pages      not regenerated here (Review 07 packet renders): method 1's whole-page NCC is used for them
Method 1 (bind_images.py, appearance matching) is kept beside it; a unit is bound when every one of its images is bound
by method 2, or by method 1 where method 2 does not apply."""
import hashlib
import io
import json
import pathlib
import runpy
import shutil
import sys
import tempfile

import numpy as np
import pymupdf
from PIL import Image

R = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-14")
W = pathlib.Path("C:/t/iso/work/r2x")
TMP = pathlib.Path(tempfile.mkdtemp(prefix="r14-regen-", dir="C:/t/iso/tmp"))
PREFIX = "\\\\?\\"
sha = lambda b: hashlib.sha256(b).hexdigest()


def run_redirected(script: pathlib.Path, replacements: dict, name: str) -> None:
    src = script.read_text(encoding="utf-8")
    for a, b in replacements.items():
        assert a in src, (script, a)
        src = src.replace(a, b)
    p = TMP / f"{name}.py"
    p.write_text(src, encoding="utf-8")
    runpy.run_path(str(p), run_name="__main__")


(TMP / "findings").mkdir()
(TMP / "small-batch").mkdir()
(TMP / "critical").mkdir()
(TMP / "renders").mkdir()
(TMP / "h06").mkdir()
T = TMP.as_posix()
run_redirected(W / "worklist/finding_crops.py", {'pathlib.Path("C:/t/r2x/worklist/findings")': f'pathlib.Path("{T}/findings")'}, "finding_crops")
run_redirected(W / "worklist/finding_crops_ocr.py", {'pathlib.Path("C:/t/r2x/worklist/findings")': f'pathlib.Path("{T}/findings")'}, "finding_crops_ocr")
run_redirected(W / "worklist/small_batch_crops.py", {'pathlib.Path("C:/t/r2x/worklist/small-batch")': f'pathlib.Path("{T}/small-batch")'}, "small_batch_crops")
run_redirected(W / "worklist/critical_crops.py", {'pathlib.Path("C:/t/r2x/worklist/critical")': f'pathlib.Path("{T}/critical")',
                                                   '(E / "DISAGREEMENTS-WITH-CROPS.json")': f'pathlib.Path("{T}/critical/DISAGREEMENTS-WITH-CROPS.json")'}, "critical_crops")

# renders (r2_render.py page recipe) for the tags the review used
man = {d["sha256"][:12]: d for d in json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))["documents"]}


def regen_render(name: str) -> pathlib.Path:
    tag, rest = name.split("-p", 1)
    page_no = int(rest.split("-")[0].split(".")[0])
    d = man[tag]
    data = open(PREFIX + d["staged_path"].replace("/", "\\"), "rb").read()
    assert sha(data) == d["sha256"]
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        page = pdf[page_no - 1]
        r = page.rect
        out = TMP / "renders" / name
        if name.endswith("-tb.jpg"):
            clip = pymupdf.Rect(r.x0 + r.width * 0.50, r.y0 + r.height * 0.55, r.x1, r.y1)
            page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72), clip=clip).save(str(out), jpg_quality=85)
        else:
            zoom = min(1600 / max(r.width, r.height), 150 / 72)
            page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(str(out), jpg_quality=80)
    return out


def regen_h06() -> None:
    sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
    from app.services import design_sheet_extractor as dse
    src = pathlib.Path("C:/t/holdout/stage/EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf")
    data = src.read_bytes()
    assert sha(data) == "719f8714d2a75673c8ba390a884a2d2889b2438fd587eaa2c42f62d75f344fec"
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        page = pdf[0]
        s = 72 / dse.RENDER_DPI
        for tag, y in (("H06-1", 980.5), ("H06-2", 1795.5), ("H06-3", 2861.0), ("H06-control", 2718.5)):
            row = pymupdf.Rect(25 * s, (y - 45) * s, 2391 * s, (y + 45) * s) & page.rect
            page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=row).save(str(TMP / "h06" / f"{tag}-row.png"))


regen_h06()


def pixel_ncc(a: bytes, b: bytes) -> float | None:
    x = np.asarray(Image.open(io.BytesIO(a)).convert("L"), dtype=np.float64)
    y = np.asarray(Image.open(io.BytesIO(b)).convert("L"), dtype=np.float64)
    if x.shape != y.shape:
        return None
    x, y = x - x.mean(), y - y.mean()
    den = np.sqrt((x * x).sum() * (y * y).sum())
    return float((x * y).sum() / den) if den else None


review = json.loads((R / "AI-SOURCE-REVIEW.json").read_text(encoding="utf-8"))
m1 = {(b["unit"], b["image"]): b for b in json.loads((W / "r14/BINDING.json").read_text(encoding="utf-8"))["results"]}
results = []
for a in review["answers"]:
    for ev in a["evidence"]:
        name = pathlib.Path(ev["image"]).name
        orig = ev["original_image"].replace("\\", "/")
        evid = pathlib.Path(ev["image"]).read_bytes()
        assert sha(evid) == ev["sha256"]
        regen = None
        if "/worklist/crops/findings/" in orig or "/worklist/findings/" in orig:
            regen = TMP / "findings" / name
        elif "/crops/small-batch/" in orig or "/worklist/small-batch/" in orig:
            regen = TMP / "small-batch" / name
        elif "/crops/critical/" in orig or "/worklist/critical/" in orig:
            regen = TMP / "critical" / name
        elif "/r2x/renders/" in orig:
            regen = regen_render(name)
        elif "/h06/" in orig:
            regen = TMP / "h06" / name
        rec = {"unit": a["id"], "image": name, "image_sha256": ev["sha256"], "original_image": orig}
        if regen is None:
            b1 = m1[(a["id"], name)]
            rec.update({"method": "1 (appearance, whole page)", "ncc": b1["ncc_claimed_page"], "controls": b1["controls"], "bound": b1["bound"],
                        "doc_sha256": b1["doc_sha256"], "page": b1["page"]})
        elif not regen.exists():
            rec.update({"method": "2 (regeneration)", "bound": False, "reason": "the recipe did not regenerate this file"})
        else:
            rb = regen.read_bytes()
            ident = sha(rb) == ev["sha256"]
            ncc = 1.0 if ident else pixel_ncc(rb, evid)
            b1 = m1.get((a["id"], name), {})
            rec.update({"method": "2 (regeneration)", "byte_identical": ident, "pixel_ncc": ncc, "regenerated_sha256": sha(rb),
                        "doc_sha256": b1.get("doc_sha256"), "page": b1.get("page"), "bound": ident or (ncc is not None and ncc >= 0.999)})
        results.append(rec)
        print(a["id"], name, rec["method"], rec.get("byte_identical"), rec.get("pixel_ncc", rec.get("ncc")), "BOUND" if rec["bound"] else "NOT BOUND", flush=True)
units = {}
for r in results:
    units.setdefault(r["unit"], []).append(r["bound"])
out = {"method": __doc__, "images": len(results), "bound": sum(r["bound"] for r in results),
       "units_all_bound": sum(all(v) for v in units.values()), "units": len(units),
       "units_not_all_bound": [u for u, v in units.items() if not all(v)], "results": results}
(W / "r14/BINDING-REGEN.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
print(out["images"], "image uses;", out["bound"], "bound;", out["units_all_bound"], "of", out["units"], "units fully bound;", out["units_not_all_bound"])
shutil.rmtree(TMP, ignore_errors=True)
