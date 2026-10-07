"""Where interface equipment physically is on a drawing -- the symbol, not
the words beside it (FI-P1 r2 W-3, W-5; review 2 residuals).

A label's text point is where the words are written, never where the
equipment stands. Two adjacent motorized smoke dampers on EP-30880's
ventilation layout are labelled 0.86 m apart; their symbols (two inserts of
one damper block) sit 0.26 m and 0.46 m from their own labels and 1.10 m from
each other. Counting labels within a radius made them one.

Here:
- **Symbol candidates** are the small, text-free block inserts near the
  labels (at any depth, through each insert's transform). Each has a stable
  id within its file (the handle path of its inserts), its bounds and centre.
- **Association** ties each label to one candidate. It is settled only when
  the nearest candidate is within reach and the runner-up is at least 1.5
  times farther. Two labels claiming one symbol with different words are
  both held. A label with no candidate is held for its location.
- **Gate barriers** are counted from the drawing's own fire alarm connection
  points (a "DRY CONTACT ... FIRE ALARM CABLE" note on a plan). Each point is
  tied to a lane role (entry / exit) by the one-to-one assignment of the
  nearest role labels. A point is settled only when the best assignment beats
  the next best by a clear margin; otherwise it is held. The point's leaders
  say where the barrier is.

Every distance is in drawing units scaled by `metre` (units per metre).
EXAMPLE thresholds, from the contract, are constants here.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from itertools import permutations

REACH_M = 1.0                 # a label's symbol is within this (EP-30880: 0.26-0.46 m)
SEARCH_M = 3.0                # symbol candidates are looked for this far around labels
MAX_SYMBOL_M = 3.0            # a candidate's larger side: a damper, a valve, a fan -- not a room
RATIO = 1.5                   # runner-up / best, for an association to be settled
MIN_D_M = 0.05                # distances below this compare as this (a label drawn on its symbol)
MAX_DEPTH = 4

CONNECTION = re.compile(r"FIRE\s*ALARM\s*(?:CABLE|INTERFACE|CONNECTION)|DRY\s*CONTACT", re.I)
NOTE_ONLY = re.compile(r"NETWORK|DATA\s*POINT|CAT\s*6|CONTROL\s*PANEL", re.I)
ROLE_ENTRY = re.compile(r"\bENTRY\b|\bENT\b\.?|\bENTRANCE\b|\bIN\s*GATE\b", re.I)
ROLE_EXIT = re.compile(r"\bEXIT\b|\bOUT\s*GATE\b", re.I)
NOT_A_LANE = re.compile(r"FIRE\s+EXIT|EMERGENCY\s+EXIT|EXIT\s+TO\b|EXIT\s+SIGN|DIRECT\s+EXIT|CAMERA|LPR\b", re.I)
CONNECT_MERGE_M = 1.0         # the same connection note drawn twice at one spot is one
ROLE_MERGE_M = 3.0            # "PARKING ENTRY" and "PARKING ENT." 2 m apart name one lane
ROLE_REACH_M = 6.0
ROLE_MARGIN_M = 1.0
LEADER_REACH_M = 0.8


@dataclass
class Symbol:
    id: str                    # handle path within the file
    block: str
    bounds: tuple[float, float, float, float]
    centre: tuple[float, float] = field(init=False)

    def __post_init__(self):
        x0, y0, x1, y1 = self.bounds
        self.centre = ((x0 + x1) / 2, (y0 + y1) / 2)

    def gap(self, x: float, y: float) -> float:
        """Distance from a point to the symbol's bounds (0 inside)."""
        x0, y0, x1, y1 = self.bounds
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        return math.hypot(dx, dy)

    def to_dict(self) -> dict:
        return {"id": self.id, "block": self.block, "bounds": [round(v, 3) for v in self.bounds],
                "centre": [round(v, 3) for v in self.centre]}


class _Grid:
    def __init__(self, points: list[tuple[float, float]], cell: float):
        self.cell = max(cell, 1e-6)
        self.cells: dict[tuple[int, int], int] = {}
        for x, y in points:
            k = (int(x // self.cell), int(y // self.cell))
            self.cells[k] = self.cells.get(k, 0) + 1

    def touches(self, bounds: tuple[float, float, float, float], pad: float) -> bool:
        x0, y0, x1, y1 = bounds
        i0, i1 = int((x0 - pad) // self.cell), int((x1 + pad) // self.cell)
        j0, j1 = int((y0 - pad) // self.cell), int((y1 + pad) // self.cell)
        if (i1 - i0 + 1) * (j1 - j0 + 1) > len(self.cells):
            return any(i0 <= i <= i1 and j0 <= j <= j1 for i, j in self.cells)
        return any((i, j) in self.cells for i in range(i0, i1 + 1) for j in range(j0, j1 + 1))


def symbols_near(doc, points: list[tuple[float, float]], metre: float) -> list[Symbol]:
    """The small text-free block inserts within SEARCH_M of any of `points`, at
    any depth. A block's local extent is measured once; an insert whose world
    extent is nowhere near a label is not opened."""
    from ezdxf import bbox
    from ezdxf.math import Matrix44

    from app.ifc.dxf.geometry import chain_matrix

    if not points:
        return []
    search, max_side = SEARCH_M * metre, MAX_SYMBOL_M * metre
    grid = _Grid(points, search)
    local: dict[str, tuple | None] = {}
    texty: dict[str, bool] = {}

    def world(bounds, m) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = bounds
        pts = [m.transform((x, y, 0)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        xs, ys = [p.x for p in pts], [p.y for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def block_info(name: str, depth: int = 0):
        """A block's extent in its own coordinates, measured once: its own
        primitives, and each nested block's extent through its insert -- never
        by exploding the nested blocks (a bound xref is the whole building)."""
        if name in local:
            return local[name], texty[name]
        local[name], texty[name] = None, True          # a block inserting itself is measured once
        block = doc.blocks.get(name)
        if block is None:
            return None, True
        prims, inserts, kinds = [], [], set()
        for e in block:
            kind = e.dxftype()
            kinds.add(kind)
            if kind == "INSERT":
                inserts.append(e)
            elif kind not in ("ATTDEF", "VIEWPORT", "IMAGE", "WIPEOUT"):
                prims.append(e)
        box = None
        if prims:
            try:
                ext = bbox.extents(prims, fast=True)
                if ext.has_data:
                    box = [ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y]
            except Exception:  # noqa: BLE001
                box = None
        if depth < MAX_DEPTH * 2:
            for e in inserts:
                child, _t = block_info(e.dxf.name, depth + 1)
                if child is None:
                    continue
                try:
                    cb = world(child, e.matrix44())
                except Exception:  # noqa: BLE001
                    continue
                box = list(cb) if box is None else [min(box[0], cb[0]), min(box[1], cb[1]),
                                                    max(box[2], cb[2]), max(box[3], cb[3])]
        local[name] = tuple(box) if box else None
        texty[name] = bool(kinds & {"TEXT", "MTEXT", "ATTDEF"})
        return local[name], texty[name]

    out: list[Symbol] = []

    def visit(entities, parent: Matrix44 | None, path: str, depth: int) -> None:
        for e in entities:
            if e.dxftype() != "INSERT":
                continue
            name = e.dxf.name
            bounds, has_text = block_info(name)
            if bounds is None:
                continue
            try:
                m = chain_matrix(e, parent)
            except Exception:  # noqa: BLE001
                continue
            wb = world(bounds, m)
            if not grid.touches(wb, search):
                continue
            here = f"{path}/{e.dxf.handle}" if path else str(e.dxf.handle)
            small = (wb[2] - wb[0]) <= max_side and (wb[3] - wb[1]) <= max_side
            if small and not has_text and not getattr(e, "attribs", None):
                out.append(Symbol(id=here, block=name, bounds=wb))
                continue
            if depth < MAX_DEPTH:
                block = doc.blocks.get(name)
                if block is not None:
                    visit(block, m, here, depth + 1)

    visit(doc.modelspace(), None, "", 0)
    return out


def associate(labels: list[tuple[str, float, float]], symbols: list[Symbol], metre: float) -> list[dict]:
    """Each label (text, x, y) tied to its symbol, or not: one dict per label,
    {state: settled|ambiguous|none, symbol, d, runner_up, candidates}."""
    reach, floor = REACH_M * metre, MIN_D_M * metre
    out: list[dict] = []
    for text, x, y in labels:
        near = sorted(((s.gap(x, y), s) for s in symbols if s.gap(x, y) <= max(reach * 2, SEARCH_M * metre)),
                      key=lambda t: t[0])
        if not near or near[0][0] > reach:
            out.append({"state": "none", "symbol": None, "d": None, "runner_up": None,
                        "candidates": [s.id for _d, s in near[:2]]})
            continue
        best_d, best = near[0]
        runner = near[1][0] if len(near) > 1 else None
        settled = runner is None or runner / max(best_d, floor) >= RATIO
        out.append({"state": "settled" if settled else "ambiguous", "symbol": best.to_dict(),
                    "d": round(best_d / metre, 3), "runner_up": None if runner is None else round(runner / metre, 3),
                    "candidates": [s.id for _d, s in near[:2]], "text": text})
    # one symbol, several labels: the same words are one item's labels; different words, all held
    claims: dict[str, list[int]] = {}
    for i, a in enumerate(out):
        if a["state"] == "settled":
            claims.setdefault(a["symbol"]["id"], []).append(i)
    for ids in claims.values():
        if len(ids) > 1 and len({_norm(labels[i][0]) for i in ids}) > 1:
            for i in ids:
                out[i]["state"] = "ambiguous"
                out[i]["why"] = "several different labels claim one symbol"
    for a in out:
        a.pop("text", None)
    return out


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().upper())


# --- gate barriers ------------------------------------------------------------------------------------------------


def leaders(doc) -> list[list[tuple[float, float]]]:
    """The model-space leaders' vertices (LEADER, and MULTILEADER arrow lines)."""
    out = []
    for e in doc.modelspace().query("LEADER"):
        try:
            out.append([(float(v[0]), float(v[1])) for v in e.vertices])
        except Exception:  # noqa: BLE001
            continue
    for e in doc.modelspace().query("MULTILEADER"):
        try:
            for line in e.context.leaders:
                for ll in line.lines:
                    pts = [(float(v.x), float(v.y)) for v in ll.vertices]
                    if pts:
                        out.append(pts)
        except Exception:  # noqa: BLE001
            continue
    return out


def _leader_target(x: float, y: float, all_leaders: list, reach: float) -> tuple[float, float] | None:
    """Where a note's leaders point: each leader with a vertex at the note,
    its vertex farthest from the note; the mean of those."""
    ends = []
    for pts in all_leaders:
        if not pts or min(math.hypot(px - x, py - y) for px, py in pts) > reach:
            continue
        far = max(pts, key=lambda q: math.hypot(q[0] - x, q[1] - y))
        if math.hypot(far[0] - x, far[1] - y) > reach:
            ends.append(far)
    if not ends:
        return None
    return (sum(p[0] for p in ends) / len(ends), sum(p[1] for p in ends) / len(ends))


def _role(text: str) -> str | None:
    if NOT_A_LANE.search(text):
        return None
    if ROLE_EXIT.search(text):
        return "exit"
    if ROLE_ENTRY.search(text):
        return "entry"
    return None


def gate_points(texts: list[tuple[str, float, float]], all_leaders: list, metre: float) -> list[dict]:
    """The fire alarm connection points of gate barriers, each with its lane
    role when the drawing settles it, and where its leaders point.

    Returns dicts {x, y, text, role, settled, why, equipment_anchor, role_d,
    margin}. Nothing here decides the sheet or floor; the caller does."""
    merge, rmerge = CONNECT_MERGE_M * metre, ROLE_MERGE_M * metre
    points: list[dict] = []
    for text, x, y in texts:
        if not CONNECTION.search(text) or NOTE_ONLY.search(text):
            continue
        if any(_norm(p["text"]) == _norm(text) and math.hypot(p["x"] - x, p["y"] - y) <= merge for p in points):
            continue
        points.append({"x": x, "y": y, "text": text})
    roles: list[dict] = []        # merged role labels: {role, pts}
    for text, x, y in texts:
        role = _role(text)
        if role is None:
            continue
        for r in roles:
            if r["role"] == role and min(math.hypot(px - x, py - y) for px, py in r["pts"]) <= rmerge:
                r["pts"].append((x, y))
                break
        else:
            roles.append({"role": role, "pts": [(x, y)]})
    reach = ROLE_REACH_M * metre

    def dist(p, r) -> float:
        return min(math.hypot(px - p["x"], py - p["y"]) for px, py in r["pts"])

    for p in points:
        p["equipment_anchor"] = _leader_target(p["x"], p["y"], all_leaders, LEADER_REACH_M * metre)
        p.update(role=None, settled=False, role_d=None, margin=None, why="no lane role label near it")
    # every point near the same labels is decided together: groups of points sharing role labels
    near = [[i for i, r in enumerate(roles) if dist(p, r) <= reach] for p in points]
    groups: list[set[int]] = []
    for i in range(len(points)):
        g = {i}
        for j in range(len(points)):
            if j != i and set(near[i]) & set(near[j]):
                g.add(j)
        for existing in groups:
            if existing & g:
                existing |= g
                break
        else:
            groups.append(g)
    for g in groups:
        idx = sorted(g)
        labels = sorted({k for i in idx for k in near[i]})
        if not labels:
            continue
        if len(idx) > len(labels) or len(idx) > 6:
            for i in idx:
                points[i]["why"] = "more connection points than lane labels near them"
            continue
        costs = []
        for perm in permutations(labels, len(idx)):
            d = [dist(points[i], roles[k]) for i, k in zip(idx, perm)]
            if all(v <= reach for v in d):
                costs.append((sum(d), perm, d))
        costs.sort(key=lambda t: t[0])
        if not costs:
            continue
        best = costs[0]
        second = next((c for c in costs[1:] if [roles[k]["role"] for k in c[1]] != [roles[k]["role"] for k in best[1]]),
                      None)
        margin = (second[0] - best[0]) if second else math.inf
        both_near = len(idx) == 1 and len({roles[k]["role"] for k in labels}) > 1
        for i, k, d in zip(idx, best[1], best[2]):
            points[i].update(role=roles[k]["role"], role_d=round(d / metre, 2),
                             margin=None if margin == math.inf else round(margin / metre, 2))
            if both_near:
                points[i]["why"] = "one connection point with both an entry and an exit label near it"
            elif margin >= ROLE_MARGIN_M * metre:
                points[i].update(settled=True, why=None)
            else:
                points[i]["why"] = f"the lane roles are not clear (margin {margin / metre:.2f} m)"
    return points


# --- alignment between two drawings -------------------------------------------------------------------------------

LANDMARKS = 800               # unique words kept per drawing to compare its frame with another's
ALIGN_MATCH_M = 0.5
ALIGN_MIN = 3
ALIGN_RESIDUAL_M = 0.2
_NOT_A_LANDMARK = re.compile(r"^[\d\s.,%+\-±/()mM:xX]*$")   # levels, sizes, numbers


def landmarks(texts: list[tuple[str, float, float]]) -> dict[str, list[float]]:
    """The words written exactly once in a drawing (room names, notes), each with
    where it is: two drawings that share a frame write them at the same spot."""
    seen: dict[str, list] = {}
    for text, x, y in texts:
        key = _norm(text)
        if len(key) < 4 or _NOT_A_LANDMARK.match(key):
            continue
        seen.setdefault(key, []).append((x, y))
    unique = sorted((k, v[0]) for k, v in seen.items() if len(v) == 1)
    if len(unique) > LANDMARKS:
        step = len(unique) / LANDMARKS
        unique = [unique[int(i * step)] for i in range(LANDMARKS)]
    return {k: [round(x, 3), round(y, 3)] for k, (x, y) in unique}


def aligned(a: dict[str, list[float]], b: dict[str, list[float]], metre: float) -> dict:
    """Whether two drawings share a model frame (W-4): at least ALIGN_MIN of the
    words both write once lie within ALIGN_MATCH_M of each other, with a mean
    offset under ALIGN_RESIDUAL_M. Identical viewports alone are not proof."""
    common = [k for k in a if k in b]
    close = [math.dist(a[k], b[k]) for k in common if math.dist(a[k], b[k]) <= ALIGN_MATCH_M * metre]
    residual = (sum(close) / len(close)) if close else None
    ok = len(close) >= ALIGN_MIN and residual is not None and residual <= ALIGN_RESIDUAL_M * metre
    return {"aligned": ok, "matches": len(close), "common": len(common),
            "residual": None if residual is None else round(residual / metre, 3)}
