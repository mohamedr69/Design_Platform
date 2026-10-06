"""FI-P1 Stage 0.3 -- the damper pictures are drawn in a time box that Stop can end.

Synthetic DXF drawings (no project drawings) and a real child process. The
reported case: EP-30880's SMOKE LAYOUT window around SM-104 never finished
drawing because a huge tile-pattern hatch from the architect's xref was being
expanded, and Stop could not interrupt it.
"""
import time
from types import SimpleNamespace

import ezdxf
import pytest

from app.interfaces import render, visual
from app.services import jobs


def _drawing(path, *, big_pattern=True, small_pattern=True, solid=True):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6                       # metres
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (20, 0), (20, 1), (0, 1)], close=True)          # a duct
    msp.add_lwpolyline([(5, 0), (5.05, 0), (5.05, 1), (5, 1)], close=True)      # a damper bar
    msp.add_text("MSD", dxfattribs={"height": 0.2, "insert": (5.2, 1.2)})
    if big_pattern:
        # the survey's floor tiles: a pattern far larger than any window
        hatch = msp.add_hatch(color=8)
        hatch.set_pattern_fill("ANSI31", scale=0.02)
        hatch.paths.add_polyline_path([(-100, -60), (100, -60), (100, 60), (-100, 60)], is_closed=True)
    if small_pattern:
        hatch = msp.add_hatch(color=3)
        hatch.set_pattern_fill("ANSI31", scale=0.5)
        hatch.paths.add_polyline_path([(8, 0.2), (8.5, 0.2), (8.5, 0.8), (8, 0.8)], is_closed=True)
    if solid:
        hatch = msp.add_hatch(color=1)
        hatch.paths.add_polyline_path([(10, 0.2), (10.3, 0.2), (10.3, 0.8), (10, 0.8)], is_closed=True)
    doc.saveas(path)
    return path


WINDOW = (0.0, -4.0, 12.0, 8.0)
LIMITS = render.RenderLimits(window_timeout_s=60, plan_timeout_s=120, restarts=1, hatching_timeout_s=2.0)


def test_a_pattern_hatch_reaching_past_the_window_is_background_and_not_drawn(tmp_path):
    dxf = _drawing(tmp_path / "sm.dxf")
    plan = render.Plan(dxf, [WINDOW], 1.0)
    started = time.monotonic()
    png = plan.picture(*WINDOW, px=400)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert plan.skipped_hatches == 1                  # the floor tiles; the small pattern and the solid fill stay
    assert time.monotonic() - started < 30
    hatches = [e for e in ezdxf.readfile(dxf).modelspace() if e.dxftype() == "HATCH"]
    box = render._quick_box
    flags = [render.is_background_pattern(h, box(h), WINDOW) for h in hatches]
    assert flags == [True, False, False]


def test_pictures_come_from_a_child_process_that_is_closed_after(tmp_path):
    dxf = _drawing(tmp_path / "sm.dxf", big_pattern=False)
    boxes = [WINDOW, (6.0, -4.0, 18.0, 8.0)]
    session = render.RenderSession(dxf, boxes, 1.0, limits=LIMITS)
    with session:
        first, second = session.picture(0), session.picture(1)
        assert session._proc is not None and session._proc.is_alive()
    assert first[:4] == b"\x89PNG" and second[:4] == b"\x89PNG"
    assert session._proc is None


def test_a_picture_that_overruns_is_killed_reported_and_restarts_are_bounded(tmp_path):
    dxf = _drawing(tmp_path / "sm.dxf", big_pattern=False)
    limits = render.RenderLimits(window_timeout_s=1.0, plan_timeout_s=120, restarts=1)
    session = render.RenderSession(dxf, [WINDOW, WINDOW, WINDOW], 1.0, limits=limits, _delay_s=30)
    with session:
        started = time.monotonic()
        with pytest.raises(render.RenderTimeout):
            session.picture(0)
        assert time.monotonic() - started < 15 and session._proc is None      # killed, not waited for
        with pytest.raises(render.RenderTimeout):
            session.picture(1)                                               # the one restart, overrun again
        with pytest.raises(render.RenderUnavailable):
            session.picture(2)                                               # restarts spent: no third child
    assert session.timeouts == 2


def test_stop_ends_a_picture_in_progress_and_kills_its_process(tmp_path):
    dxf = _drawing(tmp_path / "sm.dxf", big_pattern=False)
    asked = {"at": None}

    def check():
        if asked["at"] and time.monotonic() - asked["at"] > 1.0:
            raise jobs.Cancelled()

    session = render.RenderSession(dxf, [WINDOW], 1.0, check=check, limits=LIMITS, _delay_s=60)
    with session:
        session._open()
        asked["at"] = time.monotonic()
        with pytest.raises(jobs.Cancelled):
            session.picture(0)
        assert time.monotonic() - asked["at"] < 10
        assert session._proc is None


def test_a_drawing_that_cannot_be_opened_is_unavailable_not_a_crash(tmp_path):
    bad = tmp_path / "broken.dxf"
    bad.write_text("not a dxf")
    with render.RenderSession(bad, [WINDOW], 1.0, limits=LIMITS) as session:
        with pytest.raises(render.RenderUnavailable):
            session.picture(0)
        with pytest.raises(render.RenderUnavailable):
            session.picture(0)                        # decided once; no new process per window


def test_a_child_that_cannot_start_is_unavailable_and_closing_is_safe(tmp_path, monkeypatch):
    dxf = _drawing(tmp_path / "sm.dxf", big_pattern=False)

    class NoStart:
        def __init__(self, *a, **k):
            self._popen = None

        def start(self):
            raise RuntimeError("An attempt has been made to start a new process before bootstrapping")

    import multiprocessing as mp

    real = mp.get_context("spawn")
    monkeypatch.setattr(render.mp, "get_context", lambda kind: type("Ctx", (), {
        "Queue": staticmethod(real.Queue), "Process": staticmethod(NoStart)})())
    with render.RenderSession(dxf, [WINDOW], 1.0, limits=LIMITS) as session:
        with pytest.raises(render.RenderUnavailable, match="could not be started"):
            session.picture(0)
    assert session._proc is None                      # __exit__ did not raise


def test_in_process_rollback_draws_the_same_picture(tmp_path):
    dxf = _drawing(tmp_path / "sm.dxf", big_pattern=False)
    inline = render.RenderLimits(in_process=True)
    with render.RenderSession(dxf, [WINDOW], 1.0, limits=inline) as session:
        assert session.picture(0)[:4] == b"\x89PNG" and session._proc is None


# --- the damper look loop --------------------------------------------------------------------------------------


class FakeSession:
    """RenderSession stand-in: window 2 overruns; counts pictures."""

    drawn: list[int] = []

    def __init__(self, dxf, boxes, metre, *, check=None, limits=None):
        self.check = check

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def picture(self, index):
        FakeSession.drawn.append(index)
        if index == 1:
            raise render.RenderTimeout("drawing window 2 took over 120 s")
        return b"png"


def _labels():
    # three dampers far apart: three windows
    return [{"key": "motorized_smoke_fire_damper", "kind": "label", "confidence": "medium", "tag": None, "detail": "",
             "text": "MSD", "sheet": "SM-101", "x": float(x), "y": 0.0} for x in (0, 100, 200)]


def _setup(monkeypatch, tmp_path):
    from app.core.config import get_settings
    from app.interfaces import service

    monkeypatch.setattr(get_settings(), "ai_enabled", True)
    monkeypatch.setattr(service, "cache_folder", lambda project: tmp_path)
    sha = "a" * 64
    (tmp_path / f"{sha[:24]}.dxf").write_text("x")
    monkeypatch.setattr(render, "RenderSession", FakeSession)
    monkeypatch.setattr(render, "annotate", lambda png, w, start=1: png)
    from app.review import service as review

    monkeypatch.setattr(review, "_budget", lambda db, project: None)
    FakeSession.drawn = []
    src = {"discipline": "SM", "status": "read", "sha256": sha, "filename": "SMOKE LAYOUT.dwg",
           "result": {"units": "m", "items": _labels(),
                      "sheets": [{"name": "SM-101", "title": "3RD BASEMENT FLOOR PLAN", "kind": "plan"}]}}
    return src, SimpleNamespace(id=1)


def test_an_overrun_window_is_recorded_unread_and_the_other_windows_still_get_looked_at(monkeypatch, tmp_path):
    src, project = _setup(monkeypatch, tmp_path)
    asked = []

    def fake_ask(project_id, batch, sha, budget, drawing, fresh=False):
        asked.extend(b["window"]["labels"][0][0] for b in batch)
        return {"answers": [{"n": b["start"], "damper": True, "x": 0.5, "y": 0.5, "what": "damper", "confidence": "high"}
                            for b in batch]}

    monkeypatch.setattr(visual, "_ask", fake_ask)
    looked = visual.check(None, project, [src])
    v = src["visual"]
    assert looked == 2 and len(asked) == 2 and FakeSession.drawn == [0, 1, 2]
    assert v["status"] == "incomplete" and len(v["missing"]) == 1
    (only,) = v["missing"]
    assert v["unread"][only].startswith("render_timeout") and only.startswith("SM-101|100.00")
    assert only not in v["items"]                      # unread is not "no damper"


def test_stop_between_windows_ends_the_loop_before_the_next_picture(monkeypatch, tmp_path):
    src, project = _setup(monkeypatch, tmp_path)
    monkeypatch.setattr(visual, "_ask", lambda *a: {"answers": []})
    calls = {"n": 0}

    def check():
        calls["n"] += 1
        if FakeSession.drawn:                          # stop asked once the first window is drawn
            raise jobs.Cancelled()

    with pytest.raises(jobs.Cancelled):
        visual.check(None, project, [src], check=check)
    assert FakeSession.drawn == [0]                    # at most one window after the stop
    assert "visual" not in src                         # nothing half-written into the source


def test_progress_is_reported_per_window_while_drawing(monkeypatch, tmp_path):
    src, project = _setup(monkeypatch, tmp_path)
    monkeypatch.setattr(visual, "_ask", lambda *a: {"answers": []})
    seen = []
    visual.check(None, project, [src], progress=lambda d, t, m, f=None: seen.append(m))
    drawing = [m for m in seen if m.startswith("Drawing SMOKE LAYOUT.dwg")]
    assert drawing == [f"Drawing SMOKE LAYOUT.dwg for its dampers (window {i} of 3)" for i in (1, 2, 3)]
