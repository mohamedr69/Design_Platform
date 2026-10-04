"""A pytest plugin for running EXISTING modules on E's ACTUAL cropped path (M2 review 19). Unlike `_e_frame_shim` (whole
page as the located area; compatibility evidence only), the real locator and its real, partial crop stay in force. The
only thing adapted is the fixture assumption that conflicts with the crop contract: existing tests script discovery
regions in the WHOLE page's 0..1000 frame, while E's discovery answers in the crop's frame. Each scripted
`discover_region` answer is converted into what a reader of the actual crop could report:
  * a region inside the crop -> the same place in the crop's 0..1000 frame;
  * a field whose region lies outside the crop -> not visible: value and region empty (decision: no options / mark);
  * other_numbers are kept (they carry no region).
Behavioural assertions of the tests are untouched. Use: pytest -p tests._e_crop_coords ..."""
import json
import os

import pytest


def _log(nodeid, dropped, clip):
    """E_CROP_LOG=<file>: one JSON line per located discovery -- which scripted fields lay outside the actual crop."""
    path = os.environ.get("E_CROP_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"test": nodeid, "dropped_outside_crop": dropped, "clip": [round(v, 1) for v in clip]}) + "\n")


def _to_crop(page, clip, box):
    if not box or len(box) != 4:
        return None
    w, h = page.rect.width, page.rect.height
    x0, y0, x1, y1 = (float(v) / 1000 * s for v, s in zip(box, (w, h, w, h)))
    import pymupdf
    r = pymupdf.Rect(x0, y0, x1, y1)
    # a reader of the crop reports the part of a field's box it can see: a scripted box at least half inside the crop is
    # clipped to it (scripted boxes are wider than the printed text); less than half inside counts as not visible
    inside = r & clip
    if inside.is_empty or inside.get_area() < 0.5 * r.get_area():
        return None
    r = inside
    return [int((r.x0 - clip.x0) / clip.width * 1000), int((r.y0 - clip.y0) / clip.height * 1000),
            int((r.x1 - clip.x0) / clip.width * 1000), int((r.y1 - clip.y0) / clip.height * 1000)]


@pytest.fixture(autouse=True)
def _e_actual_crop_coordinates(monkeypatch, request):
    from app.ai import evidence_reader as er

    if not getattr(er, "EFFICIENT_ENABLED", False) or request.module.__name__.endswith(("test_ai_pilot_r18", "test_ai_pilot_r19")):
        yield
        return
    last = {}
    real_locate, real_call = er.locate_title_block, er.EvidenceRun.call

    def locate(page, ocr_lines=None, **kw):
        clip, route = real_locate(page, ocr_lines, **kw)
        last.update(page=page, clip=clip)
        return clip, route

    def call(self, **kw):
        got = real_call(self, **kw)
        if kw.get("task") == "discover_region" and isinstance(got, dict) and last.get("clip") is not None:
            page, clip = last["page"], last["clip"]
            got = dict(got)
            dropped = []
            for f in ("own_identity", "own_revision"):
                box = _to_crop(page, clip, got.get(f"{f}_region"))
                if not box and got.get(f):
                    dropped.append(f)
                got[f], got[f"{f}_region"] = (got.get(f), box) if box else ("", [])
            box = _to_crop(page, clip, got.get("decision_region"))
            if box:
                got["decision_region"] = box
            else:
                if got.get("decision_options_printed") or got.get("decision_marked_option"):
                    dropped.append("decision")
                got.update(decision_region=[], decision_options_printed=[], decision_marked_option="", decision_mark_type="none",
                           decision_actor="unknown")
            _log(request.node.nodeid, dropped, clip)
        return got

    monkeypatch.setattr(er, "locate_title_block", locate)
    monkeypatch.setattr(er.EvidenceRun, "call", call)
    yield
