"""The walls a wall-mounted device is fixed to, from the drawing itself.

A sounder flasher, a call point, a telephone jack is fixed on a wall: its
back plate on the wall's face, facing into the room (platform owner, 2
October 2026). The model points at roughly the right spot; the platform
puts the symbol's back on the face of the wall behind it.

The walls are the drawing's own lines -- most inside the architectural
background, one large block -- so they are read once per drawing, every
line and polyline at any depth, kept in a grid of 2 m cells, and saved
beside the drawing's other working files: every later placement, and every
click of the engineer's, reads that rather than the drawing.

Which lines are walls (M8, ORCH-036): a line, polyline or arc whose
effective layer (app.redesign.layers: layer "0" inside a block takes its
INSERT's layer) is shown -- on, thawed, plottable, not frozen in the
viewport the index is built for, the entity and every INSERT above it
visible -- and whose layer's own name is on the wall allow-list
(settings.prep_wall_layers) and not on NOT_WALLS. Every segment met is
counted in the index's layer composition report, kept or not and why.

The engineer's decisions (A-16, 8 October 2026; ORCH-044):
  1 a title block's, sheet frame's or border's content (any block of the
    INSERT chain named like settings.prep_frame_blocks), and layer-"0"
    content of a dimension / text block put on a wall layer, is no wall:
    reason title_frame (layers.FrameRule; per build: deny_blocks=);
  2 an INSERT on an off / no-plot layer hides only its layer-"0" content,
    a frozen one all of it (layers.walk);
  3 lengths are converted to metres by the drawing's $INSUNITS before the
    200 m threshold and the report; a drawing without a known unit gives an
    index held "not measured, units unknown" (Walls.held), never measured;
    the cells stay in the drawing's own coordinates;
  4 MLINE is not read as wall geometry: the report counts the MLINEs on
    wall layers (mline_unsupported), and a sparse index with them is held
    for that reason;
  7 arcs are wall candidates; polyface / polygon meshes are not read and are
    counted (mesh_not_read).
"""
from __future__ import annotations

import hashlib
import json
import math
import pickle
import re
from pathlib import Path

CELL = 2.0
MIN_LENGTH = 0.3
# Lines that are not walls: grids, text and dimensions, furniture and cars,
# doors and windows, and the fire alarm's and lighting's own symbols.
NOT_WALLS = re.compile(r"GRID|AXIS|DIM|TEXT|NAME|ANNO|TAG|FURN|CAR|PARK|SYMBOL|FIRE|ALARM|SPK|SPEAKER|LIGHT|\bEM\b|-EM"
                       r"|EXIT|SIGN|DOOR|WIN|TITLE|LEVEL|ROOM|HATCH|ARROW|STAIR", re.I)
# 1: every line not on NOT_WALLS by its raw layer. 2 (M8): effective layer,
# visibility, allow-list, composition report; the rules' fingerprint in the name.
# 3 (ORCH-044, A-16): title/frame rule, the AutoCAD off-layer INSERT rule, lengths
# in metres by $INSUNITS (held when unknown), MLINE and meshes reported.
VERSION = 3
KINDS = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC"}
# met in the walk only to be counted, never read as a line (decision 4)
UNREAD_KINDS = {"MLINE"}
# Under this much kept wall the index cannot close a room: coverage is "not
# measured" (M3 P-07), never measured against no walls (as coverage.MIN_BOUNDS_M).
# Metres (engineer decision 3, A-16: kept at 200 m, lengths converted first).
MIN_WALLS_M = 200.0
# Why a built index is held "not measured" (Walls.held), the first that applies.
UNITS_UNKNOWN, MLINE_UNSUPPORTED, SPARSE = "units_unknown", "mline_unsupported", "sparse"


class Walls:
    def __init__(self, cells: dict[tuple[int, int], list[tuple[float, float, float, float]]],
                 report: dict | None = None):
        self.cells = cells
        # the layer composition report of a built index; None for one made by hand
        self.report = report
        # per-segment records, only when built with detail=True (never saved)
        self.detail: list[dict] | None = None

    @property
    def units_unknown(self) -> bool:
        """A built index of a drawing whose length unit is not known (A-16 3)."""
        return self.report is not None and not (self.report.get("units") or {}).get("known", True)

    @property
    def sparse(self) -> bool:
        """A built index with too little kept wall to close a room by -- or
        one whose length cannot be had in metres (units unknown), which is
        never taken for enough."""
        if self.report is None:
            return False
        if self.units_unknown:
            return True
        return self.report["totals"]["included_length_m"] < MIN_WALLS_M

    @property
    def held(self) -> str | None:
        """Why the index is held "not measured" (M3 P-07), or None: units
        unknown (A-16 3); MLINE walls not read and a sparse line index
        (A-16 4, mline_unsupported); sparse."""
        if self.report is None:
            return None
        if self.units_unknown:
            return UNITS_UNKNOWN
        if not self.sparse:
            return None
        if (self.report.get("mline_unsupported") or {}).get("count"):
            return MLINE_UNSUPPORTED
        return SPARSE

    def held_detail(self) -> str:
        """The held reason in words, for the issue and the gate."""
        why = self.held
        if why == UNITS_UNKNOWN:
            u = self.report.get("units") or {}
            return (f"not measured, units unknown ($INSUNITS {u.get('insunits')}, $MEASUREMENT "
                    f"{u.get('measurement')}, $LUNITS {u.get('lunits')})")
        if why == MLINE_UNSUPPORTED:
            m = self.report["mline_unsupported"]
            return (f"sparse, mline_unsupported ({m['count']} MLINE on wall layers, {m['length_m']} m, "
                    "not read as walls)")
        return why or ""

    def near(self, x: float, y: float, radius: float) -> list[tuple[float, float, float, float]]:
        if self.units_unknown:
            # held (A-16 3): no wall of an unknown unit is offered to a placement,
            # a snap or a room (ORCH-044, U2-prep-fallback F-07 where it is "unknown")
            return []
        out = []
        r = int(math.ceil(radius / CELL))
        cx, cy = int(math.floor(x / CELL)), int(math.floor(y / CELL))
        for i in range(cx - r, cx + r + 1):
            for j in range(cy - r, cy + r + 1):
                out.extend(self.cells.get((i, j), ()))
        return out

    def faces_behind(self, x: float, y: float, facing: tuple[float, float], *, back: float = 1.5,
                     front: float = 0.3) -> list[tuple[float, float]]:
        """Every face behind (x, y) as face_behind finds one, the nearest first."""
        fx, fy = facing
        found = []
        for ax, ay, bx, by in self.near(x, y, back + front + 0.5):
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length < MIN_LENGTH or abs((dx * fx + dy * fy) / length) > 0.2:
                continue
            t = ((x - ax) * dx + (y - ay) * dy) / (length * length)
            if t < -0.02 or t > 1.02:
                continue
            qx, qy = ax + t * dx, ay + t * dy
            along = (qx - x) * fx + (qy - y) * fy
            if -back <= along <= front:
                found.append((-along, (qx, qy)))
        return [q for _d, q in sorted(found)]

    def _behind(self, x: float, y: float, facing: tuple[float, float], back: float, front: float):
        fx, fy = facing
        best = None
        for seg in self.near(x, y, back + front + 0.5):
            ax, ay, bx, by = seg
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length < MIN_LENGTH or abs((dx * fx + dy * fy) / length) > 0.2:
                continue                                  # not square to the facing
            t = ((x - ax) * dx + (y - ay) * dy) / (length * length)
            if t < -0.02 or t > 1.02:
                continue                                  # does not run across the spot
            qx, qy = ax + t * dx, ay + t * dy
            along = (qx - x) * fx + (qy - y) * fy         # < 0: behind the spot
            if -back <= along <= front and (best is None or along > best[0]):
                best = (along, qx, qy, seg)
        return best

    def face_behind(self, x: float, y: float, facing: tuple[float, float], *, back: float = 1.5,
                    front: float = 0.3) -> tuple[float, float] | None:
        """The point on the face of the wall behind (x, y) -- a line square
        to the way the device faces, at most `back` behind it (or `front`
        in front, when the spot is inside the wall), across the spot. The
        room's side of the wall: the face nearest the room. None when there
        is none."""
        best = self._behind(x, y, facing, back, front)
        return (best[1], best[2]) if best else None

    def thick(self, x: float, y: float, facing: tuple[float, float], *, least: float = 0.05,
              most: float = 0.6) -> bool:
        """Whether the face at (x, y) is a wall's: drawn with its other face
        behind it, a wall's thickness away -- not a single line (a pump set's
        outline, a parking bay, a duct)."""
        fx, fy = facing
        for ax, ay, bx, by in self.near(x, y, most + 0.5):
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length < MIN_LENGTH or abs((dx * fx + dy * fy) / length) > 0.05:
                continue                                  # not along the face
            t = ((x - ax) * dx + (y - ay) * dy) / (length * length)
            if t < 0 or t > 1:
                continue
            behind = (x - (ax + t * dx)) * fx + (y - (ay + t * dy)) * fy
            if least <= behind <= most:
                return True
        return False

    def face_span(self, x: float, y: float, facing: tuple[float, float], *, back: float = 1.0,
                  front: float = 0.1) -> tuple[float, float, float] | None:
        """(the face's offset along `facing`, and from where to where it runs
        along the wall, square to `facing`) -- the face behind (x, y) and the
        lines that carry it on in a straight line. A corner, a step in the
        wall, an opening end it: a device slid along its wall stays on it."""
        best = self._behind(x, y, facing, back, front)
        if best is None:
            return None
        fx, fy = facing
        tx, ty = -fy, fx
        offset = best[1] * fx + best[2] * fy

        def run(seg):
            ax, ay, bx, by = seg
            a, b = ax * tx + ay * ty, bx * tx + by * ty
            return min(a, b), max(a, b)

        lo, hi = run(best[3])
        grew = True
        while grew:
            grew = False
            for seg in self.near(x, y, max(hi - lo, 1.0) + 1.0):
                ax, ay, bx, by = seg
                length = math.hypot(bx - ax, by - ay)
                if length < MIN_LENGTH or abs(((bx - ax) * fx + (by - ay) * fy) / length) > 0.02:
                    continue
                if abs(ax * fx + ay * fy - offset) > 0.01 or abs(bx * fx + by * fy - offset) > 0.01:
                    continue                              # not on the same line
                a, b = run(seg)
                if a <= hi + 0.02 and b >= lo - 0.02 and (a < lo - 1e-6 or b > hi + 1e-6):
                    lo, hi, grew = min(lo, a), max(hi, b), True
        return offset, lo, hi


def rules(allow: str | None = None, deny: str | None = None) -> tuple[str, str]:
    """The allow-list and deny-list a build uses: the given ones (a later
    per-project store feeds them), else the setting and NOT_WALLS."""
    if allow is None:
        from app.core.config import get_settings

        allow = get_settings().prep_wall_layers
    return allow, (NOT_WALLS.pattern if deny is None else deny)


def frame_rules(deny_blocks: str | None = None, annotation_blocks: str | None = None) -> tuple[str, str]:
    """The title/frame block rule a build uses (engineer decision 1, A-16):
    the given one, else settings.prep_frame_blocks; and the dimension / text
    block rule for inherited content, else layers.ANNOTATION_BLOCKS."""
    from app.redesign import layers as L

    if deny_blocks is None:
        from app.core.config import get_settings

        deny_blocks = get_settings().prep_frame_blocks
    return deny_blocks, (L.ANNOTATION_BLOCKS if annotation_blocks is None else annotation_blocks)


def fingerprint(allow: str | None = None, deny: str | None = None, viewport: str | None = None, *,
                deny_blocks: str | None = None, annotation_blocks: str | None = None) -> str:
    """The rules' fingerprint, in the saved index's name: an index built under
    other rules is never read for these."""
    allow, deny = rules(allow, deny)
    deny_blocks, annotation_blocks = frame_rules(deny_blocks, annotation_blocks)
    text = json.dumps({"v": VERSION, "allow": allow, "deny": deny, "viewport": viewport, "kinds": sorted(KINDS),
                       "min": MIN_LENGTH, "deny_blocks": deny_blocks, "annotation_blocks": annotation_blocks,
                       "units": "INSUNITS->m", "min_walls_m": MIN_WALLS_M}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def path_for(project, drawing, sha: str | None, *, allow: str | None = None, deny: str | None = None,
             viewport: str | None = None, deny_blocks: str | None = None) -> Path:
    from app.ifc import storage

    return (storage.uploads_root() / f"EP-{project.ep_number}" / "redesign"
            / f"walls-{drawing.id}-{(sha or 'x')[:16]}-v{VERSION}-"
              f"{fingerprint(allow, deny, viewport, deny_blocks=deny_blocks)}.pkl").resolve()


def _add(cells: dict, seg: tuple[float, float, float, float]) -> None:
    ax, ay, bx, by = seg
    # every cell the segment passes, so a query finds it wherever it looks
    steps = max(1, int(math.hypot(bx - ax, by - ay) / CELL) + 1)
    seen = set()
    for k in range(steps + 1):
        px, py = ax + (bx - ax) * k / steps, ay + (by - ay) * k / steps
        cell = (int(math.floor(px / CELL)), int(math.floor(py / CELL)))
        if cell not in seen:
            seen.add(cell)
            cells.setdefault(cell, []).append(seg)


def build(dxf_path: Path, out: Path, check=None, *, allow: str | None = None, deny: str | None = None,
          viewport: str | None = None, detail: bool = False, deny_blocks: str | None = None,
          annotation_blocks: str | None = None) -> Walls:
    """Read every line of the drawing, at any depth, into the grid (a minute
    or two for a large drawing), and save it with its layer composition.

    `allow` / `deny`: the wall layers' regular expressions for this build
    (default: settings.prep_wall_layers and NOT_WALLS), matched,
    case-insensitively, on the effective layer's own name. `deny_blocks`:
    the title/frame/border block names of this build (default:
    settings.prep_frame_blocks; "" turns the rule off), `annotation_blocks`
    the dimension / text blocks whose layer-"0" content is no wall (default
    layers.ANNOTATION_BLOCKS). `viewport`: the handle of the paper-space
    VIEWPORT the index is built for (its frozen layers are not walls); the
    index stays in model coordinates. `detail`: keep every segment's record
    on the returned index (tests, evidence). Lengths are in metres by the
    drawing's $INSUNITS; without a known unit the index is held (Walls.held)."""
    import ezdxf

    from app.redesign import layers as L

    allow, deny = rules(allow, deny)
    deny_blocks, annotation_blocks = frame_rules(deny_blocks, annotation_blocks)
    wanted, refused = re.compile(allow, re.I), re.compile(deny, re.I)
    frame = L.FrameRule(deny_blocks, annotation_blocks)
    doc = ezdxf.readfile(dxf_path)
    units = L.drawing_units(doc)
    factor = units["factor_to_m"] or 1.0          # unknown: kept in drawing units, and held
    vp = L.viewport_info(doc, viewport) if viewport else None
    table = L.LayerTable(doc, vp["frozen_layers"] if vp else ())
    stats = L.WalkStats()
    cells: dict[tuple[int, int], list] = {}
    composition: dict[str, dict] = {}
    records: list[dict] | None = [] if detail else None
    verdicts: dict[str, str | None] = {}
    mline = {"count": 0, "length_m": 0.0, "hidden": 0, "title_frame": 0, "layers": {}}
    meshes = {"polyface": 0, "polygon_mesh": 0, "on_wall_layers": 0, "layers": {}}
    frames: dict[str, dict] = {}

    def layer_verdict(layer: str) -> str | None:
        if layer not in verdicts:
            own = L.local_name(layer)
            verdicts[layer] = ("deny_listed" if refused.search(own) else
                               None if wanted.search(own) else "not_allow_listed")
        return verdicts[layer]

    for item in L.walk(doc, KINDS | UNREAD_KINDS, table, check=check, stats=stats):
        kind = item.entity.dxftype()
        framed = frame.reason(item)
        if kind in UNREAD_KINDS:
            # decision 4: an MLINE is not read; one on a wall layer is reported
            if layer_verdict(item.layer) is None:
                if item.reason:
                    mline["hidden"] += 1
                elif framed:
                    mline["title_frame"] += 1
                else:
                    mline["count"] += 1
                    mline["length_m"] += L.mline_length(item) * factor
                    mline["layers"][item.layer] = mline["layers"].get(item.layer, 0) + 1
            continue
        if L.is_mesh(item.entity):
            # decision 7: a polyface / polygon mesh is not read as a line, and is counted
            meshes[L.mesh_kind(item.entity)] += 1
            meshes["layers"][item.layer] = meshes["layers"].get(item.layer, 0) + 1
            if layer_verdict(item.layer) is None:
                meshes["on_wall_layers"] += 1
            continue
        vertices = L.model_vertices(item)
        row = composition.get(item.layer)
        if row is None:
            row = composition[item.layer] = {"segments": 0, "length_m": 0.0, "included": 0, "included_length_m": 0.0,
                                             "excluded": {}, "via_insert": 0, "top_level": 0,
                                             "included_via_insert": 0}
        for a, b in zip(vertices, vertices[1:]):
            length = math.hypot(b.x - a.x, b.y - a.y) * factor
            reason = ("below_min_length" if length < MIN_LENGTH else
                      (item.reason or framed or layer_verdict(item.layer)))
            seg = (round(a.x, 4), round(a.y, 4), round(b.x, 4), round(b.y, 4))
            row["segments"] += 1
            row["length_m"] += length
            row["via_insert" if item.via_insert else "top_level"] += 1
            if reason is None:
                row["included"] += 1
                row["included_length_m"] += length
                row["included_via_insert"] += item.via_insert
                _add(cells, seg)
            else:
                row["excluded"][reason] = row["excluded"].get(reason, 0) + 1
            if reason == "title_frame":
                for block in frame.blocks(item)[:1]:
                    f = frames.setdefault(block, {"segments": 0, "length_m": 0.0, "layers": {}})
                    f["segments"] += 1
                    f["length_m"] += length
                    f["layers"][item.layer] = f["layers"].get(item.layer, 0) + 1
            if records is not None:
                records.append({"seg": seg, "layer": item.layer, "raw_layer": item.raw_layer, "reason": reason,
                                "kind": kind, "chain": list(item.chain), "length_m": round(length, 6)})
    report = _report(composition, stats, allow, deny, vp, units=units, frame=frame.rules(), mline=mline,
                     meshes=meshes, frames=frames)
    walls = Walls(cells, report)
    walls.detail = records
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump({"format": "walls", "version": VERSION, "cells": cells, "report": report}, f,
                    protocol=pickle.HIGHEST_PROTOCOL)
    return walls


def _report(composition: dict, stats, allow: str, deny: str, vp: dict | None, *, units: dict, frame: dict,
            mline: dict, meshes: dict, frames: dict) -> dict:
    layers = {}
    totals = {"segments": 0, "length_m": 0.0, "included": 0, "included_length_m": 0.0, "excluded": {},
              "via_insert": 0, "included_via_insert": 0}
    for name in sorted(composition):
        row = composition[name]
        row["length_m"] = round(row["length_m"], 3)
        row["included_length_m"] = round(row["included_length_m"], 3)
        row["excluded"] = dict(sorted(row["excluded"].items()))
        layers[name] = row
        totals["segments"] += row["segments"]
        totals["length_m"] += row["length_m"]
        totals["included"] += row["included"]
        totals["included_length_m"] += row["included_length_m"]
        totals["via_insert"] += row["via_insert"]
        totals["included_via_insert"] += row["included_via_insert"]
        for reason, n in row["excluded"].items():
            totals["excluded"][reason] = totals["excluded"].get(reason, 0) + n
    totals["length_m"] = round(totals["length_m"], 3)
    totals["included_length_m"] = round(totals["included_length_m"], 3)
    totals["excluded"] = dict(sorted(totals["excluded"].items()))
    mline = {**mline, "length_m": round(mline["length_m"], 3), "layers": dict(sorted(mline["layers"].items()))}
    meshes = {**meshes, "layers": dict(sorted(meshes["layers"].items()))}
    frames = {k: {**v, "length_m": round(v["length_m"], 3), "layers": dict(sorted(v["layers"].items()))}
              for k, v in sorted(frames.items())}
    # units unknown: the length is not in metres, so "sparse" cannot be decided -- held instead
    sparse = None if not units["known"] else totals["included_length_m"] < MIN_WALLS_M
    held = (UNITS_UNKNOWN if not units["known"] else
            (MLINE_UNSUPPORTED if mline["count"] else SPARSE) if sparse else None)
    return {"version": VERSION, "rules": {"allow": allow, "deny": deny, **frame,
                                          "fingerprint": fingerprint(allow, deny, vp and vp["handle"],
                                                                     deny_blocks=frame["deny_blocks"],
                                                                     annotation_blocks=frame["annotation_blocks"]),
                                          "min_length": MIN_LENGTH, "min_walls_m": MIN_WALLS_M,
                                          "kinds": sorted(KINDS)},
            "units": units, "viewport": vp, "walk": stats.to_dict(), "totals": totals,
            "sparse": sparse, "held": held, "mline_unsupported": mline, "mesh_not_read": meshes,
            "title_frame_blocks": frames, "layers": layers}


def load(path: Path) -> Walls | None:
    """The saved index, or None -- also for one saved in another format or
    version (it is built again, never read under other rules)."""
    if not path.is_file():
        return None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
    except Exception:  # noqa: BLE001 -- a file that cannot be read is built again
        return None
    if not isinstance(data, dict) or data.get("format") != "walls" or data.get("version") != VERSION:
        return None
    return Walls(data["cells"], data.get("report"))
