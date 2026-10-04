"""BOQ evaluator .3 (M2 review 06): the absence / denominator classes of mistake R6-03 found in the document
evaluator, checked on the BOQ path. Pure: no OCR, no sheet is read."""
from scripts import m2_boq_eval as ev

LABEL = {"ep": "1", "relative_path": "s.pdf", "pages": 1, "rows": [
    {"page": 1, "kind": "heading", "description": "Field Devices", "quantity": None, "part_number": None},
    {"page": 1, "kind": "line", "description": "Smoke detector", "quantity": "12", "part_number": "SIGA-PD"},
    {"page": 1, "kind": "component", "description": "Loop card", "quantity": "absent (merged '1 set')", "part_number": "absent"}]}


def extraction(lines, issues=()):
    return {"state": "completed", "outcome": "VALID", "failure": None, "lines": list(lines), "issues": list(issues)}


def line(part, qty, desc, y):
    return {"page": 1, "row_bounds": [y, y + 20], "catalog_no": part, "quantity": qty, "description": desc}


def test_an_explicit_absence_is_a_negative_that_can_fail():
    s = ev.score_sheet(LABEL, extraction([line("SIGA-PD", "12", "Smoke detector", 10), line("4-LOOP", "2", "Loop card", 40)]))
    assert s["fields"]["part_number"]["fp"] == 1 and s["fields"]["quantity"]["fp"] == 1
    none = ev.score_sheet(LABEL, extraction([line("SIGA-PD", "12", "Smoke detector", 10), line(None, None, "Loop card", 40)]))
    assert none["fields"]["part_number"]["tn"] == 1 and none["fields"]["part_number"]["missed"] == 0


def test_a_sheet_that_yielded_nothing_keeps_its_denominators_and_absences_stay_negative():
    s = ev.score_sheet(LABEL, {"state": "failed", "outcome": "FAILED", "failure": "not read", "lines": [], "issues": []})
    assert s["fields"]["part_number"]["missed"] == 1 and s["fields"]["part_number"]["tn"] == 1
    assert s["fields"]["quantity"]["missed"] == 1 and s["rows"]["heading (not emitted)"] == 1


def test_a_second_emitted_row_with_a_wrong_quantity_is_not_hidden_by_the_right_one():
    s = ev.score_sheet(LABEL, extraction([line("SIGA-PD", "12", "Smoke detector", 10), line("SIGA-PD", "21", "Smoke detector", 25),
                                          line(None, None, "Loop card", 40)]))
    assert s["critical"], "the extra accepted row is critical"
    assert s["fields"]["quantity"]["tp"] == 1
