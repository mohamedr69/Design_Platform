"""ORCH-036 evidence: the Golden GC-01 wall index's layer composition under the
M8 rules, compared with RD-M1 E10 / E11 (the v1 index), and the named-boundary
(columns) index before and after.

Reads the owner's EP-30880 DXF READ-ONLY; every pickle goes to C:/t/tmp/m8.
Run from wt-m8/backend:
    python -B ../docs/milestones/M8/evidence/wall-index/scripts/gc01_composition.py
Writes gc01-composition.json and gc01-vs-rd-m1.json beside this script's folder.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

BACKEND = Path.cwd()
sys.path.insert(0, str(BACKEND))

from app.core.config import get_settings  # noqa: E402
from app.redesign import coverage as C  # noqa: E402
from app.redesign import walls as W  # noqa: E402

GC01 = Path("G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dxf")
OUT = Path(__file__).resolve().parents[1]
TMP = Path("C:/t/tmp/m8")
RD_M1 = BACKEND.parent / "docs" / "milestones" / "redesign" / "RD-M1" / "evidence"
XREF = "X-REF_ FILE ALL FLOORS PLANS$0$"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    dxf_sha = sha256(GC01)
    t0 = time.time()
    walls = W.build(GC01, TMP / "gc01-walls.pkl", detail=True)
    t_walls = time.time() - t0
    rep = walls.report
    detail = walls.detail

    # the v1 rule, re-applied to the same walk: raw layer not on NOT_WALLS, LINE/LWPOLYLINE/POLYLINE,
    # >= MIN_LENGTH, no visibility -- what walls.py v1 kept (E10: 92,093 segments)
    v1 = [r for r in detail if r["kind"] != "ARC" and r["reason"] != "below_min_length"
          and not W.NOT_WALLS.search(r["raw_layer"] or "")]
    v1_by_raw = Counter(r["raw_layer"] for r in v1)
    v1_kept_now = Counter(r["reason"] or "included" for r in v1)
    # E10's largest "layer": raw "0", resolved now to the layer its INSERTs give it
    raw0 = Counter((r["layer"], r["reason"] or "included") for r in v1 if r["raw_layer"] == "0")

    e10 = json.loads((RD_M1 / "E10-wall-index-layers.json").read_text(encoding="utf-8"))
    e11 = json.loads((RD_M1 / "E11-effective-layers.json").read_text(encoding="utf-8"))
    e10_top = dict(e10["top_layers_in_wall_index"])
    top_compare = {name: {"e10_v1_raw_layer_segments": n, "v1_rule_reapplied_now": v1_by_raw.get(name, 0),
                          "m8_effective_layer": rep["layers"].get(name)} for name, n in e10_top.items()}
    probes = {}
    for probe, rows in e11["detail"].items():
        out = []
        for d in rows:
            match = [r for r in detail if all(abs(a - b) < 2e-3 for a, b in zip(r["seg"], d["seg"]))]
            out.append({"e11_raw": d["raw_layer"], "e11_effective": d["effective_layer"], "e11_visible": d["visible"],
                        "m8": sorted({(r["raw_layer"], r["layer"], r["reason"] or "included") for r in match})})
        probes[probe] = out

    # the named-boundary (columns) index: M8 rules vs the code it replaces (roadmap/u2 HEAD)
    t1 = time.time()
    cols = C.build_columns(GC01, TMP / "gc01-cols.pkl", get_settings().prep_column_layers)
    t_cols = time.time() - t1
    base =subprocess.run(["git", "merge-base", "HEAD", "roadmap/u2"], cwd=BACKEND, capture_output=True, text=True,
                          check=True).stdout.strip()
    old_src = subprocess.run(["git", "show", f"{base}:backend/app/redesign/coverage.py"], cwd=BACKEND,
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
    old_path = TMP / "coverage_v2_base.py"
    old_path.write_text(old_src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("coverage_v2_base", old_path)
    old = importlib.util.module_from_spec(spec)
    sys.modules["coverage_v2_base"] = old
    spec.loader.exec_module(old)
    t2 = time.time()
    old_cols = old.build_columns(GC01, TMP / "gc01-cols-v2.pkl", get_settings().prep_column_layers)
    t_old = time.time() - t2

    def bounds_len(c):
        if c.bounds is None:
            return 0.0
        segs = {s for v in c.bounds.cells.values() for s in v}
        return round(sum(((s[2] - s[0]) ** 2 + (s[3] - s[1]) ** 2) ** 0.5 for s in segs), 3)

    composition = {"dxf": str(GC01), "dxf_sha256": dxf_sha, "seconds": round(t_walls, 1), "report": rep}
    (OUT / "gc01-composition.json").write_text(json.dumps(composition, indent=1), encoding="utf-8")
    included_layers = sorted(((k, v["included"], v["included_length_m"]) for k, v in rep["layers"].items()
                              if v["included"]), key=lambda t: -t[1])
    diff = {
        "dxf_sha256": dxf_sha,
        "rules": rep["rules"],
        "totals_m8": rep["totals"],
        "walk": rep["walk"],
        "sparse": rep["sparse"],
        "e10_segments_kept_total_v1": e10["segments_kept_total"],
        "v1_rule_reapplied_to_this_walk": len(v1),
        "v1_rule_segments_now": dict(v1_kept_now),
        "m8_included_layers": included_layers,
        "e10_top_layers_compared": top_compare,
        "e10_raw_layer_0_resolved": [[layer, reason, n] for (layer, reason), n in raw0.most_common(25)],
        "e10_non_plotting": {k: {"e10": v, "m8": rep["layers"].get(k)}
                             for k, v in e10["non_plotting_layers_in_wall_index"].items()},
        "e11_probes": probes,
        "columns_index": {
            "m8": {**{k: v for k, v in cols.report.items() if k != "walk"}, "columns": len(cols),
                   "bounds_length_dedup_m": bounds_len(cols), "seconds": round(t_cols, 1)},
            "base_v2": {"columns": len(old_cols), "bounds_kept": old_cols.bounds is not None,
                        "bounds_length_dedup_m": bounds_len(old_cols), "seconds": round(t_old, 1),
                        "base_commit": base},
        },
    }
    (OUT / "gc01-vs-rd-m1.json").write_text(json.dumps(diff, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: diff[k] for k in ("totals_m8", "e10_segments_kept_total_v1", "v1_rule_reapplied_to_this_walk",
                                            "v1_rule_segments_now", "columns_index", "sparse")}, indent=1, default=str))
    print("included layers:", included_layers[:20])


if __name__ == "__main__":
    main()
