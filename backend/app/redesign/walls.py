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
"""
from __future__ import annotations

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
VERSION = 1


class Walls:
    def __init__(self, cells: dict[tuple[int, int], list[tuple[float, float, float, float]]]):
        self.cells = cells

    def near(self, x: float, y: float, radius: float) -> list[tuple[float, float, float, float]]:
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


def path_for(project, drawing, sha: str | None) -> Path:
    from app.ifc import storage

    return (storage.uploads_root() / f"EP-{project.ep_number}" / "redesign"
            / f"walls-{drawing.id}-{(sha or 'x')[:16]}-v{VERSION}.pkl").resolve()


def build(dxf_path: Path, out: Path, check=None) -> Walls:
    """Read every line of the drawing, at any depth, into the grid (a minute
    or two for a large drawing), and save it."""
    import ezdxf
    from ezdxf import disassemble

    doc = ezdxf.readfile(dxf_path)
    cells: dict[tuple[int, int], list] = {}
    for n, entity in enumerate(disassemble.recursive_decompose(doc.modelspace())):
        if check and n % 20000 == 0:
            check()
        if entity.dxftype() not in ("LINE", "LWPOLYLINE", "POLYLINE"):
            continue
        if NOT_WALLS.search(entity.dxf.get("layer", "") or ""):
            continue
        try:
            vertices = list(disassemble.make_primitive(entity).vertices())
        except Exception:  # noqa: BLE001 -- a line that cannot be read is not a wall here
            continue
        for a, b in zip(vertices, vertices[1:]):
            if math.hypot(b.x - a.x, b.y - a.y) < MIN_LENGTH:
                continue
            seg = (round(a.x, 4), round(a.y, 4), round(b.x, 4), round(b.y, 4))
            # every cell the segment passes, so a query finds it wherever it looks
            steps = max(1, int(math.hypot(b.x - a.x, b.y - a.y) / CELL) + 1)
            seen = set()
            for k in range(steps + 1):
                px, py = a.x + (b.x - a.x) * k / steps, a.y + (b.y - a.y) * k / steps
                cell = (int(math.floor(px / CELL)), int(math.floor(py / CELL)))
                if cell not in seen:
                    seen.add(cell)
                    cells.setdefault(cell, []).append(seg)
    walls = Walls(cells)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(cells, f, protocol=pickle.HIGHEST_PROTOCOL)
    return walls


def load(path: Path) -> Walls | None:
    if not path.is_file():
        return None
    try:
        with open(path, "rb") as f:
            return Walls(pickle.load(f))
    except Exception:  # noqa: BLE001 -- a file that cannot be read is built again
        return None
