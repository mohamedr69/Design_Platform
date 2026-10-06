"""Where a device may go and what a detector covers, from the drawing itself
(platform owner, 6 October 2026): a device never lands on a column or on
another device, and every room a detector is added to is covered -- no
point of it further than the detector's radius (6.3 m) from one.

  columns   the drawing's columns: closed shapes, hatches and solids on its
            column layers, column-sized; read once per drawing and saved
            beside its walls (app.redesign.walls);
  room      the room around a point: the plan's walls drawn on a grid of
            0.2 m cells, thickened enough to close its doorways, and filled
            from the point. A room the fill leaks out of (no door closed, an
            open car park) is "open": its coverage is not measured, the
            agent and the engineer judge it;
  coverage  what share of a room no detector reaches, and the best spots
            for its new detectors -- each covering the most of what is not
            covered yet, half a metre clear of the walls, clear of the
            columns.

Distances are in the drawing's units, taken as metres (as the walls).
"""
from __future__ import annotations

import math
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

VERSION = 2
CELL = 2.0                  # the columns' grid, as the walls'
MIN_SIDE, MAX_SIDE = 0.15, 2.5
MAX_ASPECT = 5.0
COLUMN_GAP_M = 0.3          # how far a device keeps from a column

GRID_M = 0.2                # a room's cell
CLOSE_M = 0.6               # a doorway up to twice this wide is closed when the room is filled
REACH_M = 30.0              # the furthest a room is looked for from its point
WALL_CLEAR_M = 0.5          # a ceiling detector keeps this far from a wall
GAP_TOLERANCE = 0.01        # a room is covered when no more than this share of it is not


# What closes a room on the architect's plan: its walls, doors, glazing and
# sills, and the columns -- read by layer where the drawing names them so
# (EP-30880: 06-WALL, 14-DOOR, 11-GLASS-1, 10-SILL, 08-COLUMN); a drawing
# that does not is closed by its double lines alone (double_lines).
BOUND_LAYERS = re.compile(r"WALL|DOOR|GLASS|GLAZ|SILL|WINDOW|WIN|CURTAIN|PARTITION|COLUMN|COLS?|S-COL", re.I)
NOT_BOUNDS = re.compile(r"TILE|HTCH|HATCH|TEXT|DIM|FINISH", re.I)
MIN_BOUNDS_M = 200.0        # the named boundaries trusted only when the drawing has this much of them


class Columns:
    def __init__(self, cells: dict[tuple[int, int], list[tuple[float, float, float, float]]], bounds=None):
        self.cells = cells
        # the room boundaries (app.redesign.walls.Walls), or None
        self.bounds = bounds

    def __len__(self) -> int:
        return len({b for boxes in self.cells.values() for b in boxes})

    def near(self, x: float, y: float, radius: float) -> list[tuple[float, float, float, float]]:
        out, r = set(), int(math.ceil(radius / CELL))
        cx, cy = int(math.floor(x / CELL)), int(math.floor(y / CELL))
        for i in range(cx - r, cx + r + 1):
            for j in range(cy - r, cy + r + 1):
                out.update(self.cells.get((i, j), ()))
        return list(out)

    def hit(self, box: tuple[float, float, float, float], gap: float = COLUMN_GAP_M):
        """The column the box comes within `gap` of, or None."""
        x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        for c in self.near(x, y, max(box[2] - box[0], box[3] - box[1]) + MAX_SIDE):
            if box[0] < c[2] + gap and c[0] < box[2] + gap and box[1] < c[3] + gap and c[1] < box[3] + gap:
                return c
        return None


def columns_path(project, drawing, sha: str | None) -> Path:
    from app.ifc import storage

    return (storage.uploads_root() / f"EP-{project.ep_number}" / "redesign"
            / f"columns-{drawing.id}-{(sha or 'x')[:16]}-v{VERSION}.pkl").resolve()


def _column_box(entity) -> tuple[float, float, float, float] | None:
    from ezdxf import bbox

    kind = entity.dxftype()
    if kind in ("LWPOLYLINE", "POLYLINE") and not entity.is_closed:
        return None
    if kind not in ("LWPOLYLINE", "POLYLINE", "HATCH", "SOLID", "CIRCLE"):
        return None
    try:
        ext = bbox.extents([entity], fast=True)
    except Exception:  # noqa: BLE001 -- a shape that cannot be measured is not a column here
        return None
    if not ext.has_data:
        return None
    w, h = ext.size.x, ext.size.y
    if not (MIN_SIDE <= w <= MAX_SIDE and MIN_SIDE <= h <= MAX_SIDE) or max(w, h) / min(w, h) > MAX_ASPECT:
        return None
    return (round(ext.extmin.x, 3), round(ext.extmin.y, 3), round(ext.extmax.x, 3), round(ext.extmax.y, 3))


def _add_segment(cells: dict, seg: tuple[float, float, float, float]) -> None:
    ax, ay, bx, by = seg
    steps = max(1, int(math.hypot(bx - ax, by - ay) / CELL) + 1)
    seen = set()
    for k in range(steps + 1):
        px, py = ax + (bx - ax) * k / steps, ay + (by - ay) * k / steps
        cell = (int(math.floor(px / CELL)), int(math.floor(py / CELL)))
        if cell not in seen:
            seen.add(cell)
            cells.setdefault(cell, []).append(seg)


def build_columns(dxf_path: Path, out: Path, layers: str, check=None) -> Columns:
    """Every column-sized shape on a column layer, and every line of the
    room boundaries (BOUND_LAYERS), at any depth (the architect's background
    is one large block), kept in a 2 m grid."""
    import ezdxf
    from ezdxf import disassemble

    from app.redesign.walls import Walls

    wanted = re.compile(layers, re.I)
    doc = ezdxf.readfile(dxf_path)
    cells: dict[tuple[int, int], list] = {}
    bounds: dict[tuple[int, int], list] = {}
    total = 0.0
    seen = set()
    for n, entity in enumerate(disassemble.recursive_decompose(doc.modelspace())):
        if check and n % 20000 == 0:
            check()
        layer = entity.dxf.get("layer", "") or ""
        if BOUND_LAYERS.search(layer) and not NOT_BOUNDS.search(layer)                 and entity.dxftype() in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
            try:
                vertices = list(disassemble.make_primitive(entity).vertices())
            except Exception:  # noqa: BLE001 -- a line that cannot be read does not close a room
                vertices = []
            for a, b in zip(vertices, vertices[1:]):
                length = math.hypot(b.x - a.x, b.y - a.y)
                if length >= 0.05:
                    _add_segment(bounds, (round(a.x, 4), round(a.y, 4), round(b.x, 4), round(b.y, 4)))
                    total += length
        if not wanted.search(layer):
            continue
        box = _column_box(entity)
        if box is None or box in seen:
            continue
        seen.add(box)
        for i in range(int(math.floor(box[0] / CELL)), int(math.floor(box[2] / CELL)) + 1):
            for j in range(int(math.floor(box[1] / CELL)), int(math.floor(box[3] / CELL)) + 1):
                cells.setdefault((i, j), []).append(box)
    kept = bounds if total >= MIN_BOUNDS_M else {}
    found = Columns(cells, Walls(kept) if kept else None)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump({"columns": cells, "bounds": kept}, f, protocol=pickle.HIGHEST_PROTOCOL)
    return found


def load_columns(path: Path) -> Columns | None:
    if not path.is_file():
        return None
    try:
        from app.redesign.walls import Walls

        with open(path, "rb") as f:
            data = pickle.load(f)
        return Columns(data["columns"], Walls(data["bounds"]) if data.get("bounds") else None)
    except Exception:  # noqa: BLE001 -- a file that cannot be read is built again
        return None


# --- the room around a point ---------------------------------------------------------


@dataclass
class Room:
    x0: float                   # the grid's lower-left corner, model
    y0: float
    mask: np.ndarray            # [row (y), col (x)]: the room's cells
    blocked: np.ndarray         # a wall's or a column's cell
    open: bool                  # the fill leaked out: no closed room here

    @property
    def area(self) -> float:
        return float(self.mask.sum()) * GRID_M * GRID_M

    def centres(self, mask: np.ndarray | None = None) -> np.ndarray:
        rows, cols = np.nonzero(self.mask if mask is None else mask)
        return np.stack([self.x0 + (cols + 0.5) * GRID_M, self.y0 + (rows + 0.5) * GRID_M], axis=1)

    def contains(self, x: float, y: float) -> bool:
        c, r = int((x - self.x0) / GRID_M), int((y - self.y0) / GRID_M)
        return 0 <= r < self.mask.shape[0] and 0 <= c < self.mask.shape[1] and bool(self.mask[r, c])

    def bounds(self) -> tuple[float, float, float, float]:
        rows, cols = np.nonzero(self.mask)
        return (float(self.x0 + cols.min() * GRID_M), float(self.y0 + rows.min() * GRID_M),
                float(self.x0 + (cols.max() + 1) * GRID_M), float(self.y0 + (rows.max() + 1) * GRID_M))


def _grow(mask: np.ndarray, steps: int, square: bool = True) -> np.ndarray:
    out = mask.copy()
    for _ in range(steps):
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        if square:
            g[1:, 1:] |= out[:-1, :-1]
            g[:-1, :-1] |= out[1:, 1:]
            g[1:, :-1] |= out[:-1, 1:]
            g[:-1, 1:] |= out[1:, :-1]
        out = g
    return out


def _rasterise(segments, x0: float, y0: float, n: int) -> np.ndarray:
    grid = np.zeros((n, n), dtype=bool)
    for ax, ay, bx, by in segments:
        steps = max(2, int(math.hypot(bx - ax, by - ay) / (GRID_M / 2)) + 1)
        t = np.linspace(0.0, 1.0, steps)
        cols = ((ax + (bx - ax) * t - x0) / GRID_M).astype(int)
        rows = ((ay + (by - ay) * t - y0) / GRID_M).astype(int)
        keep = (cols >= 0) & (cols < n) & (rows >= 0) & (rows < n)
        grid[rows[keep], cols[keep]] = True
    return grid


def double_lines(segments, least: float = 0.05, most: float = 0.6) -> list:
    """The lines drawn as a wall is, with another along them a wall's
    thickness away -- not a pump set's or a parking bay's single outline,
    which would shut a detector in a box of its own."""
    if not segments:
        return []
    s = np.asarray(segments, dtype=np.float64)
    d = s[:, 2:] - s[:, :2]
    length = np.hypot(d[:, 0], d[:, 1])
    keep = length >= 0.3
    s, d, length = s[keep], d[keep], length[keep]
    u = d / length[:, None]
    mid = (s[:, :2] + s[:, 2:]) / 2
    out = np.zeros(len(s), dtype=bool)
    for a in range(0, len(s), 400):
        b = min(len(s), a + 400)
        cross = np.abs(u[a:b, None, 0] * u[None, :, 1] - u[a:b, None, 1] * u[None, :, 0])
        rel = mid[None, :, :] - s[a:b, None, :2]
        off = np.abs(rel[..., 0] * u[a:b, None, 1] - rel[..., 1] * u[a:b, None, 0])
        # how much of the other runs alongside this one
        t0 = (s[None, :, 0] - s[a:b, None, 0]) * u[a:b, None, 0] + (s[None, :, 1] - s[a:b, None, 1]) * u[a:b, None, 1]
        t1 = (s[None, :, 2] - s[a:b, None, 0]) * u[a:b, None, 0] + (s[None, :, 3] - s[a:b, None, 1]) * u[a:b, None, 1]
        lo, hi = np.maximum(np.minimum(t0, t1), 0.0), np.minimum(np.maximum(t0, t1), length[a:b, None])
        beside = (cross < 0.03) & (off >= least) & (off <= most) & (hi - lo >= np.minimum(0.3, 0.5 * length[a:b, None]))
        out[a:b] = beside.any(axis=1)
    return [tuple(x) for x in s[out]]


MAX_ROOM_M2 = 1500.0        # past this the fill has run out into a car park or a whole floor
MIN_ROOM_M2 = 2.0           # under this the point is in a shaft or a fixture, not a room


def room_at(walls, columns: Columns | None, x: float, y: float, reach: float = REACH_M) -> Room | None:
    """The room around (x, y), filled from it inside its boundaries -- the
    architect's walls, doors, glazing and columns where the drawing names
    them, else the plan's double lines --, its doorways closed: the
    narrowest closing that shuts it, up to a 2 m double door; None when
    there is nothing near it at all."""
    if columns is not None and columns.bounds is not None:
        segments = columns.bounds.near(x, y, reach)
    else:
        segments = double_lines(walls.near(x, y, reach)) if walls is not None else []
    if not segments:
        return None
    room = None
    for close_m in (0.5, 0.75, 1.0):
        room = _fill(segments, columns, x, y, reach, close_m)
        if not room.open and room.area <= MAX_ROOM_M2:
            return room
    return room


def _fill(segments, columns: Columns | None, x: float, y: float, reach: float, close_m: float) -> Room:
    n = int(2 * reach / GRID_M)
    x0, y0 = x - reach, y - reach
    lines = _rasterise(segments, x0, y0, n)
    close = max(1, int(round(close_m / GRID_M)))
    thick = _grow(lines, close)
    blocked = lines.copy()
    if columns is not None:
        for c in columns.near(x, y, reach):
            c0, r0 = max(0, int((c[0] - x0) / GRID_M)), max(0, int((c[1] - y0) / GRID_M))
            c1, r1 = min(n, int(math.ceil((c[2] - x0) / GRID_M))), min(n, int(math.ceil((c[3] - y0) / GRID_M)))
            if c0 < c1 and r0 < r1:
                blocked[r0:r1, c0:c1] = True
    sc, sr = int((x - x0) / GRID_M), int((y - y0) / GRID_M)
    if thick[sr, sc]:
        # the point is in a wall's band (a detector half a metre off its wall):
        # the nearest cell out of it, a little past the band
        k = close + 3
        free = np.argwhere(~thick[max(0, sr - k):sr + k + 1, max(0, sc - k):sc + k + 1])
        if not len(free):
            return Room(x0, y0, np.zeros_like(lines), blocked, True)
        dr, dc = min(free, key=lambda rc: (rc[0] - min(k, sr)) ** 2 + (rc[1] - min(k, sc)) ** 2)
        sr, sc = max(0, sr - k) + dr, max(0, sc - k) + dc
    region = np.zeros_like(lines)
    region[sr, sc] = True
    free = ~thick
    size = 1
    while True:
        for _ in range(8):                  # a cell a step, never across a wall
            region = _grow(region, 1, square=False) & free
        grown = int(region.sum())
        if grown == size:
            break
        size = grown
    leaked = bool(region[0, :].any() or region[-1, :].any() or region[:, 0].any() or region[:, -1].any())
    # the band the thickening took, given back up to the wall lines themselves
    region = _grow(region, close, square=False) & ~lines
    return Room(x0, y0, region, blocked, leaked)


# --- coverage ----------------------------------------------------------------------------


def uncovered(room: Room, detectors: list[tuple[float, float]], radius: float) -> np.ndarray:
    """The room's cells no detector reaches (columns excepted)."""
    need = room.mask & ~room.blocked
    if not detectors:
        return need
    pts = room.centres(need)
    far = np.ones(len(pts), dtype=bool)
    for dx, dy in detectors:
        far &= (pts[:, 0] - dx) ** 2 + (pts[:, 1] - dy) ** 2 > radius * radius
    out = np.zeros_like(need)
    rows, cols = np.nonzero(need)
    out[rows[far], cols[far]] = True
    return out


def measure(room: Room, detectors: list[tuple[float, float]], radius: float) -> dict:
    need = room.mask & ~room.blocked
    left = uncovered(room, detectors, radius)
    area = float(need.sum()) * GRID_M * GRID_M
    gap = float(left.sum()) * GRID_M * GRID_M
    return {"area_m2": round(area, 1), "uncovered_m2": round(gap, 1),
            "covered": round(1.0 - gap / area, 3) if area else 1.0,
            "ok": area == 0 or gap / area <= GAP_TOLERANCE or gap <= 0.5}


def _spots(room: Room, step: float) -> np.ndarray:
    """Where a ceiling detector may go: in the room, half a metre clear of
    its walls and clear of its columns, every `step` metres."""
    clear = room.mask & ~_grow(room.blocked, max(1, int(round(WALL_CLEAR_M / GRID_M))))
    if not clear.any():
        clear = room.mask & ~room.blocked
    k = max(1, int(round(step / GRID_M)))
    thin = np.zeros_like(clear)
    thin[::k, ::k] = clear[::k, ::k]
    return room.centres(thin)


def best_spots(room: Room, fixed: list[tuple[float, float]], radius: float, *, count: int | None = None,
               most: int = 12) -> list[tuple[float, float]]:
    """New detectors' spots, one at a time, each where it covers the most of
    what is still not covered (the nearer the uncovered part's middle, the
    better, when two cover as much): `count` of them, or as many as the room
    needs to be covered (at most `most`)."""
    need = room.mask & ~room.blocked
    if not need.any():
        return []
    area = float(need.sum()) * GRID_M * GRID_M
    # at most ~900 spots tried against ~3000 points scored: half a metre or so
    # is plenty to choose between spots, and a car park's floor stays quick
    spots = _spots(room, max(0.4, math.sqrt(area / 900))).astype(np.float32)
    if not len(spots):
        return []
    k = max(1, int(round(max(0.5, math.sqrt(area / 3000)) / GRID_M)))
    sample = np.zeros_like(need)
    sample[::k, ::k] = need[::k, ::k]
    cells = room.centres(sample).astype(np.float32)
    if not len(cells):
        cells = room.centres(need).astype(np.float32)
    open_ = np.ones(len(cells), dtype=bool)
    for dx, dy in fixed:
        open_ &= (cells[:, 0] - dx) ** 2 + (cells[:, 1] - dy) ** 2 > radius * radius
    chosen: list[tuple[float, float]] = []
    r2 = radius * radius
    while (count is None and open_.mean() > GAP_TOLERANCE and len(chosen) < most) or \
            (count is not None and len(chosen) < count):
        left = cells[open_]
        if not len(left):
            if count is None:
                break
            # all covered already: the rest spread over the room, each furthest from the others
            others = np.array(list(fixed) + chosen, dtype=np.float32)
            far = np.min((spots[:, None, 0] - others[None, :, 0]) ** 2 + (spots[:, None, 1] - others[None, :, 1]) ** 2,
                         axis=1)
            best = int(np.argmax(far))
            chosen.append((round(float(spots[best, 0]), 3), round(float(spots[best, 1]), 3)))
            continue
        d2 = ((spots[:, None, 0] - left[None, :, 0]) ** 2 + (spots[:, None, 1] - left[None, :, 1]) ** 2)
        gain = (d2 <= r2).sum(axis=1)
        middle = left.mean(axis=0)
        off = np.hypot(spots[:, 0] - middle[0], spots[:, 1] - middle[1])
        best = int(np.lexsort((off, -gain))[0])
        x, y = float(spots[best, 0]), float(spots[best, 1])
        chosen.append((round(x, 3), round(y, 3)))
        open_ &= (cells[:, 0] - x) ** 2 + (cells[:, 1] - y) ** 2 > r2
    return chosen
