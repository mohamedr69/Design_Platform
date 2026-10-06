"""Pictures of pieces of a plan, drawn from its DXF, in a time box that can be stopped.

The interface schedule's damper look (interfaces.visual) shows the model a
piece of plan around each damper label. Drawing such a piece used to run in
the job's own thread, with nothing to stop it. On 2026-10-04 one 10 m window
of EP-30880's SMOKE LAYOUT (the label SM-104) took over 12 minutes and never
finished: a ~150 x 60 m tile-pattern HATCH from the architect's survey xref
was expanded into lines. ezdxf gave up on the pattern twice (its 30 s hatching
timeout), and drawing what it had produced then ran on with no limit. Stop
could not interrupt it, and the "stopped" job kept its thread for ~90 minutes.

Here a drawing is opened and its pictures drawn in a child process
(`RenderSession`):
- every picture has a deadline (`FA_RENDER_WINDOW_TIMEOUT_S`) and so has
  opening the drawing (`FA_RENDER_PLAN_TIMEOUT_S`);
- the caller's stop check runs while it waits;
- a child that overruns is terminated; that window is reported unread
  (`render_timeout`), never as empty;
- after a timeout the drawing is opened again at most `FA_RENDER_RESTARTS`
  times; after that every window left is reported `render_unavailable`.

Hatches are drawn as the drawing shows them, except that:
- a pattern hatch reaching beyond the window is left out; it is background,
  not a damper's symbol;
- pattern lines closer together than about a pixel are not generated;
- ezdxf's own hatching timeout is short.

`FA_RENDER_IN_PROCESS=true` draws in the caller's thread instead: the same
answers, the stop check between pictures only and no time box. It is for
rollback and for tests.
"""
from __future__ import annotations

import io
import multiprocessing as mp
import queue
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

CELL_M = 5.0             # the drawing's lines kept in a grid of these
IMAGE_PX = 1400


class RenderTimeout(Exception):
    """A picture, or opening the drawing, overran its deadline."""


class RenderUnavailable(Exception):
    """The drawing cannot be drawn any more in this run (it failed to open, or
    its restarts are spent)."""


class RenderFailed(Exception):
    """One picture could not be drawn; the next may still be."""


@dataclass(frozen=True)
class RenderLimits:
    window_timeout_s: float = 120.0
    plan_timeout_s: float = 900.0
    restarts: int = 1
    hatching_timeout_s: float = 2.0
    in_process: bool = False

    @classmethod
    def from_settings(cls) -> "RenderLimits":
        from app.core.config import get_settings

        s = get_settings()
        return cls(window_timeout_s=s.fa_render_window_timeout_s, plan_timeout_s=s.fa_render_plan_timeout_s,
                   restarts=s.fa_render_restarts, hatching_timeout_s=s.fa_render_hatching_timeout_s,
                   in_process=s.fa_render_in_process)


def _quick_box(e) -> tuple[float, float, float, float] | None:
    """An entity's extents, cheaply for the common ones; None for the rest."""
    t = e.dxftype()
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            return min(a.x, b.x), min(a.y, b.y), max(a.x, b.x), max(a.y, b.y)
        if t == "LWPOLYLINE":
            pts = [(x, y) for x, y, *_ in e.get_points("xy")]
            if not pts:
                return None
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return min(xs), min(ys), max(xs), max(ys)
        if t in ("CIRCLE", "ARC"):
            c, r = e.dxf.center, e.dxf.radius
            return c.x - r, c.y - r, c.x + r, c.y + r
        if t == "TEXT":
            p, h = e.dxf.insert, e.dxf.height or 0.0
            width = len(e.dxf.text or "") * h
            return p.x - width, p.y - h, p.x + width, p.y + 2 * h
        if t == "MTEXT":
            p, h = e.dxf.insert, e.dxf.get("char_height", 0.0) or 0.0
            width = e.dxf.get("width", 0.0) or len(e.text or "") * h
            return p.x - width, p.y - 4 * h, p.x + width, p.y + 4 * h
        if t == "SPLINE":
            pts = list(e.control_points) or list(e.fit_points)
            if pts:
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                return min(xs), min(ys), max(xs), max(ys)
        if t == "ELLIPSE":
            c, m = e.dxf.center, e.dxf.major_axis
            r = (m.x ** 2 + m.y ** 2) ** 0.5
            return c.x - r, c.y - r, c.x + r, c.y + r
        if t == "HATCH":
            xs, ys = [], []
            for path in e.paths:
                for v in getattr(path, "vertices", None) or ():
                    xs.append(v[0])
                    ys.append(v[1])
                for edge in getattr(path, "edges", None) or ():
                    for name in ("start", "end", "center"):
                        q = getattr(edge, name, None)
                        if q is not None:
                            xs.append(q[0])
                            ys.append(q[1])
            if xs:
                return min(xs), min(ys), max(xs), max(ys)
    except Exception:  # noqa: BLE001
        return None
    return None


def is_background_pattern(e, box, window) -> bool:
    """A pattern-filled HATCH that reaches beyond the window: floor tiles, a
    plot, a survey -- never a damper's symbol, and the one kind of entity whose
    drawing has no bound."""
    if e.dxftype() != "HATCH":
        return False
    try:
        if e.dxf.solid_fill:
            return False
    except Exception:  # noqa: BLE001
        return False
    x0, y0, x1, y1 = window
    return box[0] < x0 or box[1] < y0 or box[2] > x1 or box[3] > y1


class Plan:
    """The drawing's lines, at any depth, around the pieces of plan to be
    looked at -- in its own colours on black, as AutoCAD shows it."""

    def __init__(self, dxf: Path | str, boxes: list[tuple[float, float, float, float]], metre: float, check=None,
                 hatching_timeout_s: float = 2.0):
        import ezdxf
        from ezdxf import bbox, disassemble

        self.doc = ezdxf.readfile(str(dxf))
        self.cell = CELL_M * metre
        self.hatching_timeout_s = hatching_timeout_s
        self.skipped_hatches = 0
        wanted: set[tuple[int, int]] = set()
        for x0, y0, x1, y1 in boxes:
            for i in range(int(x0 // self.cell), int(x1 // self.cell) + 1):
                for j in range(int(y0 // self.cell), int(y1 // self.cell) + 1):
                    wanted.add((i, j))
        self.cells: dict[tuple[int, int], list] = defaultdict(list)
        limit = 40 * self.cell
        for n, e in enumerate(disassemble.recursive_decompose(self.doc.modelspace())):
            if check and n % 20000 == 0:
                check()
            if e.dxftype() in ("ATTDEF", "VIEWPORT", "IMAGE", "WIPEOUT", "POINT"):
                continue
            box = _quick_box(e)
            if box is None:
                try:
                    found = bbox.extents([e], fast=True)
                except Exception:  # noqa: BLE001 -- what cannot be measured is not drawn
                    continue
                if not found.has_data:
                    continue
                box = (found.extmin.x, found.extmin.y, found.extmax.x, found.extmax.y)
            if box[2] - box[0] > limit or box[3] - box[1] > limit:
                continue                      # a sheet frame, a grid line across the plan
            cells = [(i, j) for i in range(int(box[0] // self.cell), int(box[2] // self.cell) + 1)
                     for j in range(int(box[1] // self.cell), int(box[3] // self.cell) + 1)]
            for c in cells:
                if c in wanted:
                    self.cells[c].append((e, box))

    def picture(self, x0: float, y0: float, x1: float, y1: float, px: int = IMAGE_PX) -> bytes:
        from ezdxf.addons.drawing import Frontend, RenderContext, layout
        from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration
        from ezdxf.addons.drawing.pymupdf import PyMuPdfBackend
        from ezdxf.math import BoundingBox2d

        seen, entities = set(), []
        for i in range(int(x0 // self.cell), int(x1 // self.cell) + 1):
            for j in range(int(y0 // self.cell), int(y1 // self.cell) + 1):
                for e, box in self.cells.get((i, j), ()):
                    if id(e) in seen or box[2] < x0 or box[0] > x1 or box[3] < y0 or box[1] > y1:
                        continue
                    seen.add(id(e))
                    if is_background_pattern(e, box, (x0, y0, x1, y1)):
                        self.skipped_hatches += 1
                        continue
                    entities.append(e)
        backend = PyMuPdfBackend()
        config = Configuration(background_policy=BackgroundPolicy.BLACK,
                               hatching_timeout=self.hatching_timeout_s,
                               # pattern lines closer than ~a pixel are invisible anyway
                               min_hatch_line_distance=max((x1 - x0) / px, 1e-4))
        Frontend(RenderContext(self.doc), backend, config=config).draw_entities(entities)
        side_mm = 300.0
        return backend.get_pixmap_bytes(layout.Page(side_mm, side_mm, layout.Units.mm), fmt="png",
                                        dpi=int(px / (side_mm / 25.4)),
                                        render_box=BoundingBox2d([(x0, y0), (x1, y1)]))


def annotate(png: bytes, window: dict, start: int = 1) -> bytes:
    """The picture with the window's labels ringed and numbered in red, from `start`."""
    from PIL import Image, ImageDraw, ImageFont

    x0, y0, x1, y1 = window["box"]
    img = Image.open(io.BytesIO(png)).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    r = max(10, int(w / 90))
    try:
        font = ImageFont.load_default(size=max(18, int(w / 50)))
    except TypeError:                   # an older Pillow: its one small font
        font = ImageFont.load_default()
    for n, (_iid, x, y) in enumerate(window["labels"], start):
        px, py = (x - x0) / (x1 - x0) * w, (y1 - y) / (y1 - y0) * h
        draw.ellipse((px - r, py - r, px + r, py + r), outline=(255, 40, 40), width=3)
        draw.text((px + r + 3, py - 2 * r - 4), str(n), fill=(255, 40, 40), font=font)
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


# --- the child process ------------------------------------------------------------------------------------------


def _serve(dxf: str, boxes: list, metre: float, hatching_timeout_s: float, requests, replies,
           delay_s: float = 0.0) -> None:
    """The child: open the drawing once, then draw the windows asked for.
    `delay_s` exists for tests (a picture that takes that long)."""
    try:
        plan = Plan(dxf, boxes, metre, hatching_timeout_s=hatching_timeout_s)
    except Exception as exc:  # noqa: BLE001 -- reported to the parent, which decides
        replies.put(("failed", None, f"{type(exc).__name__}: {exc}"[:300]))
        return
    replies.put(("ready", None, None))
    while True:
        index = requests.get()
        if index is None:
            return
        try:
            if delay_s:
                time.sleep(delay_s)
            png = plan.picture(*boxes[index])
            replies.put(("ok", index, png))
        except Exception as exc:  # noqa: BLE001
            replies.put(("error", index, f"{type(exc).__name__}: {exc}"[:300]))


class RenderSession:
    """One drawing's pictures, drawn on request in a killable child process.

        with RenderSession(dxf, boxes, metre, check=job_check) as pictures:
            png = pictures.picture(i)      # RenderTimeout / RenderUnavailable / the stop check's exception

    The child opens the drawing once and keeps it for every window. A picture
    that overruns kills the child; the next picture opens the drawing again,
    while restarts last."""

    POLL_S = 0.25

    def __init__(self, dxf: Path | str, boxes: list[tuple[float, float, float, float]], metre: float, *,
                 check=None, limits: RenderLimits | None = None, _delay_s: float = 0.0):
        self.dxf, self.boxes, self.metre = str(dxf), [tuple(b) for b in boxes], metre
        self.check = check
        self.limits = limits or RenderLimits.from_settings()
        self.restarts_left = self.limits.restarts
        self.timeouts = 0
        self._delay_s = _delay_s
        self._proc = None
        self._requests = self._replies = None
        self._plan: Plan | None = None
        self._dead: str | None = None

    # -- lifecycle --

    def __enter__(self) -> "RenderSession":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and getattr(proc, "_popen", None) is not None:   # never started: nothing to stop
            try:
                self._requests.put_nowait(None)
            except Exception:  # noqa: BLE001
                pass
            proc.join(2)
            if proc.is_alive():
                proc.terminate()
                proc.join(5)
        self._plan = None

    def _kill(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and getattr(proc, "_popen", None) is not None and proc.is_alive():
            proc.terminate()
            proc.join(5)

    def _wait(self, deadline_s: float, what: str):
        """The child's next reply, the stop check running while waiting."""
        started = time.monotonic()
        while True:
            if self.check:
                try:
                    self.check()
                except BaseException:
                    self._kill()
                    raise
            try:
                return self._replies.get(timeout=self.POLL_S)
            except queue.Empty:
                pass
            if self._proc is not None and not self._proc.is_alive():
                raise RenderUnavailable(f"the drawing process stopped while {what}")
            if time.monotonic() - started > deadline_s:
                self._kill()
                raise RenderTimeout(f"{what} took over {deadline_s:.0f} s")

    def _open(self) -> None:
        if self._dead:
            raise RenderUnavailable(self._dead)
        if self.limits.in_process:
            if self._plan is None:
                try:
                    self._plan = Plan(self.dxf, self.boxes, self.metre, check=self.check,
                                      hatching_timeout_s=self.limits.hatching_timeout_s)
                except Exception as exc:  # noqa: BLE001
                    if type(exc).__name__ in ("Cancelled", "Interrupted"):
                        raise
                    self._dead = f"the drawing could not be opened: {type(exc).__name__}: {exc}"[:300]
                    raise RenderUnavailable(self._dead) from exc
            return
        if self._proc is not None:
            return
        ctx = mp.get_context("spawn")
        self._requests, self._replies = ctx.Queue(), ctx.Queue()
        self._proc = ctx.Process(target=_serve, daemon=True,
                                 args=(self.dxf, self.boxes, self.metre, self.limits.hatching_timeout_s,
                                       self._requests, self._replies, self._delay_s))
        try:
            self._proc.start()
        except Exception as exc:  # noqa: BLE001 -- e.g. spawned from a module without a __main__ guard
            self._proc = None
            self._dead = f"the drawing process could not be started: {type(exc).__name__}: {exc}"[:300]
            raise RenderUnavailable(self._dead) from exc
        try:
            kind, _index, detail = self._wait(self.limits.plan_timeout_s, "opening the drawing")
        except RenderTimeout as exc:
            self._dead = str(exc)
            raise RenderUnavailable(self._dead) from exc
        if kind != "ready":
            self._kill()
            self._dead = f"the drawing could not be opened: {detail}"
            raise RenderUnavailable(self._dead)

    def picture(self, index: int) -> bytes:
        """The picture of window `index` (plain, not yet ringed)."""
        if self.check:
            self.check()
        self._open()
        if self.limits.in_process:
            return self._plan.picture(*self.boxes[index])
        self._requests.put(index)
        try:
            kind, got, detail = self._wait(self.limits.window_timeout_s, f"drawing window {index + 1}")
        except RenderTimeout:
            self.timeouts += 1
            if self.restarts_left > 0:
                self.restarts_left -= 1
            else:
                self._dead = f"drawing stopped after {self.timeouts} window(s) overran their time"
            raise
        if kind == "ok" and got == index:
            return detail
        raise RenderFailed(detail or "the drawing process gave no picture")
