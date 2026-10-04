"""M2 review 06, H-06: a strip quantity contradicted by agreeing independent passes is held, not accepted."""
from app.services import design_sheet_extractor as dse
from app.services.design_sheet_extractor import ExtractedBoqLine


def _line(q="9", conf=74.0):
    return ExtractedBoqLine(description="PC+Monitor", catalog_no=None, group_heading=None, confidence=0.9, quantity=q, raw_quantity="| " + q, quantity_confidence=conf, page=1)


def _passes(*values):
    return [{"pass": f"p{i}", "text": v or "", "value": v, "status": "ok" if v else "empty"} for i, v in enumerate(values)]


def test_agreeing_passes_against_the_strip_hold_the_row(monkeypatch):
    monkeypatch.setattr(dse, "_independent_readings", lambda image, line: _passes("2", "2", "2"))
    line = _line()
    dse._check_cut_digit(None, line)
    assert line.quantity is None and line.quantity_parse["status"] == dse.values.AMBIGUOUS
    assert "'9'" in line.quantity_parse["rule"] and "'2'" in line.quantity_parse["rule"]
    assert [a["value"] for a in line.alternates] == ["2", "2", "2"]


def test_a_pass_backing_the_strip_or_a_lone_dissent_keeps_it(monkeypatch):
    monkeypatch.setattr(dse, "_independent_readings", lambda image, line: _passes("9", "2", "2"))
    line = _line()
    dse._check_cut_digit(None, line)
    assert line.quantity == "9"
    monkeypatch.setattr(dse, "_independent_readings", lambda image, line: _passes("2", None, None))
    line = _line()
    dse._check_cut_digit(None, line)
    assert line.quantity == "9"


def test_the_rule_is_a_knob_and_the_cut_digit_rule_still_wins(monkeypatch):
    monkeypatch.setattr(dse, "_independent_readings", lambda image, line: _passes("2", "2", "2"))
    monkeypatch.setattr(dse, "HOLD_ON_PASS_DISAGREEMENT", False)
    line = _line()
    dse._check_cut_digit(None, line)
    assert line.quantity == "9"
    monkeypatch.setattr(dse, "HOLD_ON_PASS_DISAGREEMENT", True)
    monkeypatch.setattr(dse, "_independent_readings", lambda image, line: _passes("491", "491", None))
    line = _line("49", 86.0)
    dse._check_cut_digit(None, line)
    assert line.quantity is None and "cut" in line.quantity_parse["rule"]
