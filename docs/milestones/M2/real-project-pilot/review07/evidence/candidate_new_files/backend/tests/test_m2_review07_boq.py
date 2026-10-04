"""M2 review 07, E: a count printed in a description ("( 2 ) Dual Input Module") is a located source fact of its own,
and a quantity cell that says otherwise is held with both literals -- neither is chosen."""
from app.extraction import values
from app.services import design_sheet_extractor as dse


def _inline(text):
    return dse.INLINE_QUANTITY_RE.match(text)


def test_an_empty_cell_takes_the_descriptions_count_with_its_source():
    parsed, quantity, provenance = dse._inline_count(_inline("( 1 ) Audio and Telephone Interface"), "")
    assert quantity == "1" and provenance["source"] == "description_count" and provenance["description_literal"] == "( 1 )"
    assert provenance["cell_literal"] is None and provenance.get("status") != values.AMBIGUOUS


def test_a_cell_that_agrees_keeps_the_count_and_both_literals():
    _parsed, quantity, provenance = dse._inline_count(_inline("(2) Zoned Amplifier"), "2")
    assert quantity == "2" and provenance["cell_literal"] == "2"


def test_a_cell_that_contradicts_the_description_holds_the_row():
    _parsed, quantity, provenance = dse._inline_count(_inline("( 1 ) Paging Microphone"), "4")
    assert quantity is None and provenance["status"] == values.AMBIGUOUS
    assert "'4'" in provenance["rule"] and "( 1 )" in provenance["rule"]
