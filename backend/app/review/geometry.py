"""Distances on the reviewed plan, in metres: where a point on the plotted
page is in the drawing, and how far it is from the nearest device.

The review looks at the plotted PDF; the devices are counted in the DWG's
model space (`app.ifc.resolve`, in metres). The two are tied together per
sheet by the texts both carry -- the room names, labels, notes printed on
the page at the place the drawing has them: matched one to one, they give
the plot's scale and offset (`fit`). EP-30880's plans come out at one scale
throughout (1:175 on A3) to within a metre or so, which is all a 12 m rule
needs.

Used for the driveway's sounder-flashers: one is asked for only where the
nearest one on the plan is more than 12 m away (platform owner, 2 October
2026).
"""
from __future__ import annotations

import math
import re
import statistics
from collections import defaultdict

FIT_VERSION = 1
# The notification devices a driveway is covered by: sounder-flashers and the
# like, by the device type the drawing's symbols were answered as.
NOTIFIERS = re.compile(r"SOUNDER|STROBE|FLASHER|BEACON", re.I)
DRIVEWAY = re.compile(r"DRIVE\s*-?\s*WAY|CAR\s*-?\s*PARK|PARKING|\bRAMP\b", re.I)
SOUNDER_SPACING_M = 12.0


def _norm(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _turn(rot_deg: float, u: float, v: float) -> tuple[float, float]:
    if not rot_deg:
        return u, v
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    return c * u - s * v, s * u + c * v


def fit(page, model_texts: list[tuple[str, float, float]], view: dict | None = None) -> dict | None:
    """The page-to-model transform of one sheet -- X = a*x + bx, Y = -a*y + by
    (the page's y runs down) -- from the texts printed once on the page and
    once in the sheet's part of the drawing. None when too few agree.

    The rotation term (F021, engineer decision 6, A-16): a sheet plotted
    through a viewport twisted by t degrees shows the model turned by t, so
    the page (y up) is turned back by -t onto the model: (X, Y) =
    a * R(-t) * (x, -y) + (bx, by), `rot_deg` = -t on the result. `view` is
    the sheet's viewport (its twist, centre, scale and frozen layers,
    `sheet_view`); without one, or untwisted, the transform is the one above,
    unchanged. The agreement rule decides as before: a twist the printed
    texts do not bear out ties nothing (None)."""
    if view is not None and view.get("mixed"):
        return None                       # viewports turned differently on one sheet: no one transform
    rot = -float(view.get("twist_deg") or 0.0) if view else 0.0
    rot = 0.0 if abs(rot) < 1e-9 else rot
    model: dict[str, list] = defaultdict(list)
    for text, x, y in model_texts:
        key = _norm(text)
        if len(key) >= 4:
            model[key].append((x, y))
    paper: dict[str, list] = defaultdict(list)
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            key = _norm("".join(span["text"] for span in line["spans"]))
            if len(key) >= 4:
                x0, y0, x1, y1 = line["bbox"]
                paper[key].append(((x0 + x1) / 2, (y0 + y1) / 2))
    pairs = [(paper[k][0], model[k][0]) for k in paper if len(paper[k]) == 1 and len(model.get(k, [])) == 1]
    if len(pairs) < 4:
        return None
    scales = []
    for i in range(len(pairs)):
        for j in range(i + 1, min(len(pairs), i + 15)):
            (p1, m1), (p2, m2) = pairs[i], pairs[j]
            dp = math.dist(p1, p2)
            if dp > 50:
                scales.append(math.dist(m1, m2) / dp)
    if len(scales) < 3:
        return None
    a = statistics.median(scales)
    if rot:
        turned = [(_turn(rot, p[0], -p[1]), m) for p, m in pairs]
        bx = statistics.median(m[0] - a * q[0] for q, m in turned)
        by = statistics.median(m[1] - a * q[1] for q, m in turned)
        residuals = sorted(math.dist((a * q[0] + bx, a * q[1] + by), m) for q, m in turned)
    else:
        bx = statistics.median(m[0] - a * p[0] for p, m in pairs)
        by = statistics.median(m[1] + a * p[1] for p, m in pairs)
        residuals = sorted(math.dist((a * p[0] + bx, -a * p[1] + by), m) for p, m in pairs)
    agree = sum(1 for r in residuals if r <= 3.0)
    # most matched texts must land where the drawing has them
    if agree < max(4, len(pairs) // 2):
        return None
    out = {"v": FIT_VERSION, "a": a, "bx": bx, "by": by, "pairs": len(pairs),
           "residual": round(residuals[len(residuals) // 2], 2)}
    if rot:
        out["rot_deg"] = rot
    if view is not None:
        out["view"] = view
    return out


def to_model(geometry: dict, x: float, y: float) -> tuple[float, float]:
    rot = geometry.get("rot_deg") or 0.0
    if not rot:
        return geometry["a"] * x + geometry["bx"], -geometry["a"] * y + geometry["by"]
    u, v = _turn(rot, x, -y)
    return geometry["a"] * u + geometry["bx"], geometry["a"] * v + geometry["by"]


def to_page(geometry: dict, x: float, y: float) -> tuple[float, float]:
    """The inverse of to_model: where a model point is on the plotted page."""
    a, rot = geometry["a"], geometry.get("rot_deg") or 0.0
    if not rot:
        return (x - geometry["bx"]) / a, (geometry["by"] - y) / a
    u, v = _turn(-rot, (x - geometry["bx"]) / a, (y - geometry["by"]) / a)
    return u, -v


def sheet_view(doc, layout_name: str) -> dict | None:
    """The viewport information of one sheet (a paper-space layout) for the
    fit and the wall index (engineer decision 6, A-16): its model viewport's
    handle, twist, view centre, scale and frozen layers; `mixed` when its
    viewports are twisted differently; None when it has none."""
    try:
        layout = doc.layouts.get(layout_name)
    except Exception:  # noqa: BLE001 -- not a layout: no viewport
        return None
    if layout is None:
        return None
    views = []
    for v in layout.query("VIEWPORT"):
        try:
            c = v.dxf.view_center_point
            if abs(c.x - v.dxf.center.x) < 1e-6 and abs(c.y - v.dxf.center.y) < 1e-6:
                continue                  # the sheet's own paper-space viewport (as ifc.dxf.sheets)
            height = float(v.dxf.view_height or 0.0)
            views.append({"handle": str(v.dxf.handle), "twist_deg": float(v.dxf.get("view_twist_angle", 0.0) or 0.0),
                          "view_center": [float(c.x), float(c.y)], "view_height": height,
                          "scale": (float(v.dxf.height) / height) if height else None,
                          "frozen_layers": sorted(v.frozen_layers or [])})
        except Exception:  # noqa: BLE001 -- an unreadable viewport is not this sheet's view
            continue
    if not views:
        return None
    if len({round(w["twist_deg"], 6) for w in views}) > 1:
        return {"mixed": True, "viewports": views}
    if len(views) == 1:
        return views[0]
    return {**views[0], "viewports": views}


def fit_sheets(project, drawing, pdf_path: str, sheets: list[dict]) -> None:
    """Each reviewed sheet's `geometry` (its fit, or None when it cannot be
    had), read from the drawing's DXF and the plotted PDF."""
    import ezdxf
    import pymupdf

    from app.ifc import storage
    from app.ifc.dxf import sheets as S
    from app.interfaces.scan import _texts

    dxf = storage.dxf_path(drawing)
    if not dxf.is_file():
        for sh in sheets:
            sh["geometry"] = {"v": FIT_VERSION, "error": "The drawing's DXF is not on this PC."}
        return
    doc = ezdxf.readfile(dxf)
    windows = S.read_sheets(doc)
    by_sheet: dict[str, list] = defaultdict(list)
    for text, x, y in _texts(doc):
        by_sheet[S.sheet_for(windows, x, y)].append((text, x, y))
    pdf = pymupdf.open(pdf_path)
    try:
        for sh in sheets:
            view = sheet_view(doc, sh["name"])
            found = (fit(pdf[sh["index"]], by_sheet.get(sh["name"], []), view)
                     if sh["index"] < pdf.page_count else None)
            sh["geometry"] = found or {"v": FIT_VERSION, "error": "The plot could not be tied to the drawing."}
    finally:
        pdf.close()


def notifiers(db, drawing) -> dict[str, list[tuple[float, float, str]]]:
    """Every sounder-flasher (and the like) on each sheet, where the drawing
    has it: {sheet name: [(x, y, device type), ...]}."""
    from app.ifc.resolve import resolved_drawing

    out: dict[str, list] = defaultdict(list)
    for group in resolved_drawing(db, drawing, with_occurrences=True).get("groups") or []:
        name = (group.get("device_type") or {}).get("name") or ""
        if not NOTIFIERS.search(name):
            continue
        for o in group.get("occurrences") or []:
            out[o.get("sheet") or ""].append((float(o.get("cx", o["x"])), float(o.get("cy", o["y"])), name))
    return out


def nearest(geometry: dict | None, devices: list[tuple[float, float, str]], at) -> tuple[float, str] | None:
    """(metres, device type) from a point on the page to the nearest device
    on its sheet; None when the sheet has no fit, no point, or no device."""
    if not geometry or "a" not in geometry or not at or not devices:
        return None
    x, y = to_model(geometry, at[0], at[1])
    d, name = min((math.dist((x, y), (dx, dy)), n) for dx, dy, n in devices)
    return d, name
