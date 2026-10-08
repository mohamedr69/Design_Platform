"""ORCH-044 evidence: the Golden GC-01 wall and boundary indexes under the
engineer's decisions (A-16), against the ORCH-036 results committed in
docs/milestones/M8/evidence/wall-index (gc01-composition.json,
gc01-vs-rd-m1.json).

Reads the owner's EP-30880 DXF READ-ONLY; every pickle goes to
C:/t/tmp/m8b/gc. Run from wt-m8b/backend:
    python -B ../docs/milestones/M8/evidence/exit-fixes/scripts/gc01_exit_fixes.py
Writes ../docs/milestones/M8/evidence/exit-fixes/gc01-exit-fixes.json.

What it measures:
  walls      totals, per layer, exclusion classes, unit found, MLINE and
             meshes; what the title/frame rule removed (by block and layer,
             and what each segment would have been without it)
  bounds     the named-boundary index: base (ORCH-036 record), now, and the
             now-rules with the frame rule off and with TAG back in
             NOT_BOUNDS's absence, to attribute the change
  viewport   the index for FA 101's viewport (frozen 18-DIM, BUILDING) against
             the model-space index
  fit        F021: every GC-01 sheet's twist, and the plot-to-model fit of
             the base code against this one on a page drawn from the sheet's
             own viewport (ezdxf's model->paper matrix) -- the plotted PDF
             is under the live uploads and is not read
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

BACKEND = Path.cwd()
sys.path.insert(0, str(BACKEND))

from app.core.config import get_settings  # noqa: E402
from app.redesign import coverage as C  # noqa: E402
from app.redesign import layers as L  # noqa: E402
from app.redesign import walls as W  # noqa: E402

GC01 = Path("G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dxf")
OUT = Path(__file__).resolve().parents[1]
BEFORE = OUT.parent / "wall-index"
TMP = Path("C:/t/tmp/m8b/gc")
BASE_FIT_COMMIT = "1708692084f2253fa0eb792910f7c8b685680da7"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dedup_len(cols) -> float:
    if cols.bounds is None:
        return 0.0
    segs = {s for v in cols.bounds.cells.values() for s in v}
    return round(sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in segs), 3)


def walls_part() -> dict:
    t0 = time.time()
    walls = W.build(GC01, TMP / "gc01-walls.pkl", detail=True)
    seconds = round(time.time() - t0, 1)
    rep = walls.report
    allow, deny = re.compile(rep["rules"]["allow"], re.I), re.compile(rep["rules"]["deny"], re.I)
    frame = L.FrameRule(rep["rules"]["deny_blocks"], rep["rules"]["annotation_blocks"])
    removed = defaultdict(lambda: {"segments": 0, "length_m": 0.0})
    by_block_layer = defaultdict(lambda: {"segments": 0, "length_m": 0.0})
    for r in walls.detail:
        if r["reason"] != "title_frame":
            continue
        own = L.local_name(r["layer"])
        would = "deny_listed" if deny.search(own) else ("kept" if allow.search(own) else "not_allow_listed")
        item = L.Item(None, None, r["layer"], r["raw_layer"], None, tuple(r["chain"]))
        block = (frame.blocks(item) or ["?"])[0]
        for key, table in (((block, would), removed), ((block, r["layer"], would), by_block_layer)):
            table[key]["segments"] += 1
            table[key]["length_m"] += r["length_m"]
    kept_removed = {k[0]: {"segments": v["segments"], "length_m": round(v["length_m"], 3)}
                    for k, v in removed.items() if k[1] == "kept"}
    before = json.loads((BEFORE / "gc01-composition.json").read_text(encoding="utf-8"))["report"]
    layer_changes = {}
    for name in sorted(set(before["layers"]) | set(rep["layers"])):
        a, b = before["layers"].get(name, {}), rep["layers"].get(name, {})
        if (a.get("included"), a.get("excluded")) != (b.get("included"), b.get("excluded")):
            layer_changes[name] = {"before": {k: a.get(k) for k in ("included", "included_length_m", "excluded")},
                                   "now": {k: b.get(k) for k in ("included", "included_length_m", "excluded")}}
    north = rep["layers"].get("X-REF_PLOT$0$A-NORTH")
    out = {
        "seconds": seconds, "rules": rep["rules"], "units": rep["units"], "sparse": rep["sparse"], "held": rep["held"],
        "totals_before_orch036": before["totals"], "totals_now": rep["totals"],
        "kept_delta": {"segments": rep["totals"]["included"] - before["totals"]["included"],
                       "length_m": round(rep["totals"]["included_length_m"] - before["totals"]["included_length_m"], 3)},
        "title_frame_blocks": rep["title_frame_blocks"],
        "title_frame_removed_from_kept_by_block": kept_removed,
        "title_frame_by_block_and_would_be_reason": {f"{k[0]} | {k[1]}": {"segments": v["segments"],
                                                                         "length_m": round(v["length_m"], 3)}
                                                     for k, v in sorted(removed.items())},
        "title_frame_by_block_layer_reason": {f"{k[0]} | {k[1]} | {k[2]}": {"segments": v["segments"],
                                                                           "length_m": round(v["length_m"], 3)}
                                              for k, v in sorted(by_block_layer.items())},
        "mline_unsupported": rep["mline_unsupported"], "mesh_not_read": rep["mesh_not_read"],
        "walk": rep["walk"], "x_ref_plot_a_north": north,
        "layer_changes_vs_orch036": layer_changes,
        "included_layers_now": sorted(((k, v["included"], v["included_length_m"]) for k, v in rep["layers"].items()
                                       if v["included"]), key=lambda t: -t[2]),
    }
    (OUT / "gc01-composition-exit-fixes.json").write_text(json.dumps({"dxf": str(GC01), "report": rep}, indent=1),
                                                         encoding="utf-8")
    del walls
    return out


def bounds_part() -> dict:
    layers = get_settings().prep_column_layers
    runs = {}
    t0 = time.time()
    now = C.build_columns(GC01, TMP / "gc01-cols.pkl", layers)
    runs["now"] = (now, round(time.time() - t0, 1))
    t0 = time.time()
    no_frame = C.build_columns(GC01, TMP / "gc01-cols-noframe.pkl", layers, deny_blocks="", annotation_blocks="")
    runs["frame_rule_off"] = (no_frame, round(time.time() - t0, 1))
    saved = C.NOT_BOUNDS
    try:
        C.NOT_BOUNDS = re.compile(r"TILE|HTCH|HATCH|TEXT|DIM|FINISH", re.I)          # TAG not yet excluded
        t0 = time.time()
        no_tag = C.build_columns(GC01, TMP / "gc01-cols-notag.pkl", layers)
        runs["tag_still_bound"] = (no_tag, round(time.time() - t0, 1))
    finally:
        C.NOT_BOUNDS = saved
    before = json.loads((BEFORE / "gc01-vs-rd-m1.json").read_text(encoding="utf-8"))["columns_index"]
    out = {"base_v2_orch036_record": {k: before["base_v2"][k] for k in ("columns", "bounds_length_dedup_m")},
           "m8_orch036_record": {k: before["m8"][k] for k in ("columns", "bounds_length_dedup_m", "bounds_length_m",
                                                                "hidden")}}
    for name, (cols, seconds) in runs.items():
        rep = cols.report
        out[name] = {"columns": len(cols), "bounds_kept": cols.bounds is not None, "bounds_length_m": rep["bounds_length_m"],
                     "bounds_length_dedup_m": dedup_len(cols), "hidden": rep["hidden"], "held": rep["held"],
                     "units": {k: rep["units"][k] for k in ("unit", "factor_to_m", "known")},
                     "mesh_not_read": rep["mesh_not_read"], "seconds": seconds}
        if name == "now":
            out[name]["bounds_layers_top"] = sorted(rep["bounds_layers"].items(), key=lambda t: -t[1])[:15]
    tag = "X-REF_ TAG$0$49-DOOR-TAG"
    out["attribution_dedup_m"] = {
        "frame_rule": round(out["frame_rule_off"]["bounds_length_dedup_m"] - out["now"]["bounds_length_dedup_m"], 3),
        "tag": round(out["tag_still_bound"]["bounds_length_dedup_m"] - out["now"]["bounds_length_dedup_m"], 3),
        "tag_layer_undeduplicated_m": no_tag.report["bounds_layers"].get(tag),
        "now_vs_base": round(out["now"]["bounds_length_dedup_m"] - before["base_v2"]["bounds_length_dedup_m"], 3),
        "now_vs_orch036": round(out["now"]["bounds_length_dedup_m"] - before["m8"]["bounds_length_dedup_m"], 3),
    }
    return out


def viewport_part(handle: str = "71BF") -> dict:
    t0 = time.time()
    vp = W.build(GC01, TMP / "gc01-walls-vp.pkl", viewport=handle)
    model = W.load(TMP / "gc01-walls.pkl")
    changed = {k: {"model": model.report["layers"].get(k, {}).get("included"), "viewport": v["included"]}
               for k, v in vp.report["layers"].items()
               if v["included"] != model.report["layers"].get(k, {}).get("included")}
    return {"handle": handle, "viewport": vp.report["viewport"], "seconds": round(time.time() - t0, 1),
            "kept_model": [model.report["totals"]["included"], model.report["totals"]["included_length_m"]],
            "kept_viewport": [vp.report["totals"]["included"], vp.report["totals"]["included_length_m"]],
            "excluded_viewport": vp.report["totals"]["excluded"], "layers_changed": changed}


class _Page:
    def __init__(self, lines):
        self.lines = lines

    def get_text(self, _kind):
        return {"blocks": [{"lines": [{"spans": [{"text": t}], "bbox": (x - 1, y - 1, x + 1, y + 1)}
                                      for t, x, y in self.lines]}]}


def fit_part() -> dict:
    import ezdxf

    from app.ifc.dxf import sheets as S
    from app.interfaces.scan import _texts
    from app.review import geometry as G

    src = subprocess.run(["git", "show", f"{BASE_FIT_COMMIT}:backend/app/review/geometry.py"], cwd=BACKEND,
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    path = TMP / "geometry_base.py"
    path.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("geometry_base", path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    doc = ezdxf.readfile(GC01)
    # paper space is in the drawing's unit (GC-01: metres): points = paper * 72 / 0.0254 * metres per unit
    pt = 72.0 / 0.0254 * (L.drawing_units(doc)["factor_to_m"] or 0.001)
    windows = S.read_sheets(doc)
    by_sheet = defaultdict(list)
    for text, x, y in _texts(doc):
        by_sheet[S.sheet_for(windows, x, y)].append((text, x, y))
    out = {"note": "pages drawn from each sheet's own viewport through ezdxf's model->paper matrix (paper units -> "
                   "pt by $INSUNITS, y down); the plotted review PDF is under the live uploads and was not read",
           "points_per_paper_unit": round(pt, 3)}
    sheets = {}
    for sheet in windows:
        view = G.sheet_view(doc, sheet.name)
        layout = doc.layouts.get(sheet.name)
        vps = [v for v in layout.query("VIEWPORT")
               if not (abs(v.dxf.view_center_point.x - v.dxf.center.x) < 1e-6
                       and abs(v.dxf.view_center_point.y - v.dxf.center.y) < 1e-6)]
        texts = by_sheet.get(sheet.name, [])
        lines = []
        if len(vps) == 1:
            m = vps[0].get_transformation_matrix()
            for text, x, y in texts:
                p = m.transform((x, y, 0))
                lines.append((text, p.x * pt, 2000.0 - p.y * pt))
        page = _Page(lines)
        before = old.fit(page, texts) if lines else None
        after = G.fit(page, texts, view) if lines else None
        same = (before is None and after is None) or (
            before is not None and after is not None
            and all(before[k] == after[k] for k in ("a", "bx", "by", "pairs", "residual")) and "rot_deg" not in after)
        sheets[sheet.name] = {"viewports": len(vps), "twist_deg": (view or {}).get("twist_deg"),
                              "frozen_layers": (view or {}).get("frozen_layers"), "texts": len(texts),
                              "before": None if before is None else {k: before[k] for k in ("a", "bx", "by", "pairs",
                                                                                          "residual")},
                              "after": None if after is None else {k: after.get(k) for k in ("a", "bx", "by", "pairs",
                                                                                           "residual", "rot_deg")},
                              "identical": same}
    out["sheets"] = sheets
    out["twisted_sheets"] = sorted(n for n, s in sheets.items() if s["twist_deg"])
    out["all_identical"] = all(s["identical"] for s in sheets.values())
    out["fitted_before"] = sum(1 for s in sheets.values() if s["before"])
    out["fitted_after"] = sum(1 for s in sheets.values() if s["after"])
    return out


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    started = time.time()
    result = {"dxf": str(GC01), "dxf_sha256": sha256(GC01), "access": "read-only"}
    result["walls"] = walls_part()
    result["bounds"] = bounds_part()
    result["viewport_fa101"] = viewport_part()
    result["fit_f021"] = fit_part()
    result["seconds"] = round(time.time() - started, 1)
    (OUT / "gc01-exit-fixes.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    w, b = result["walls"], result["bounds"]
    print(json.dumps({"totals_now": w["totals_now"], "kept_delta": w["kept_delta"],
                      "title_frame_removed_from_kept_by_block": w["title_frame_removed_from_kept_by_block"],
                      "units": w["units"], "bounds_now": b["now"]["bounds_length_dedup_m"],
                      "attribution": b["attribution_dedup_m"], "fit_identical": result["fit_f021"]["all_identical"],
                      "twisted": result["fit_f021"]["twisted_sheets"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
