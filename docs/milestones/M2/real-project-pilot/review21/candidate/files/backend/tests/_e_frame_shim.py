"""A pytest plugin for running the EXISTING modules with E on (M2 review 18): those tests script discovery regions in
the whole page's 0..1000 frame, while E's located discovery answers in the title-block crop's frame -- the same
numbers then name another place, which is a property of the scripts, not of E. With this plugin E's locator returns
the whole sheet as its located area (route `located:shim_whole_page`), so a scripted region keeps its meaning and every
other part of E still runs (the discover_region task, located-absence outcomes, deadline-bound timeouts).
Use: pytest -p tests._e_frame_shim ... (only for that run; E's own tests use the real locator)."""
import pytest


@pytest.fixture(autouse=True)
def _e_whole_sheet_frame(monkeypatch, request):
    from app.ai import evidence_reader as er
    from app.services import title_block

    if (getattr(er, "EFFICIENT_ENABLED", False) or getattr(er, "ROI_ENABLED", False)) and not request.module.__name__.endswith(("test_ai_pilot_r18", "test_ai_pilot_r19", "test_ai_pilot_r21")):
        monkeypatch.setattr(er, "locate_title_block", lambda page, ocr_lines=None, *, ocr_timeout=20.0:
                            (page.rect, "located:shim_whole_page") if title_block.is_drawing_sheet(page) else (None, "not_a_drawing_sheet"))
    yield
