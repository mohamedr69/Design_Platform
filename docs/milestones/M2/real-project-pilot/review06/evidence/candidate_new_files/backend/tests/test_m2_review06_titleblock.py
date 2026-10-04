"""M2 review 06: an OCR-read title-block number is evidence; it becomes the sheet's number (a register key) only when
it is one clean, unambiguous identity-shaped token (EP-29076 LAC-653 sheets: "XY) LAC-653-GEN-ZZZ-ELV-FA-211")."""
import pymupdf
import pytest

from app.services import title_block as tb


@pytest.mark.parametrize("literal, candidate, trusted", [
    ("AGC-DF-MEP-SD-PAS-02-D", "AGC-DF-MEP-SD-PAS-02-D", True),
    ("XY) LAC-653-GEN-ZZZ-ELV-FA-211", "LAC-653-GEN-ZZZ-ELV-FA-211", False),
    ("XS) LAC-653-PLN-LO8-ELV-FA-115 C 1", "LAC-653-PLN-LO8-ELV-FA-115", False),
    ("LAC-653-PLN-LO8-ELV-FA-115", "LAC-653-PLN-LO8-ELV-FA-115", False),
    ("SCALE 1:100", None, False),
    ("AB-100-01 AB-100-02", None, False),
])
def test_ocr_number_trust(literal, candidate, trusted):
    got, why = tb.ocr_number(literal)
    assert got == candidate and (why is None) is trusted


def _sheet(ocr_value):
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)      # A2 landscape: a drawing-sized page with no text layer
    x = page.rect.width * 0.8
    y = page.rect.height - 140

    def ocr_lines(page, clip):
        return [tb.Line(x, y, x + 40, y + 8, "DRG. NO."), tb.Line(x, y + 12, x + 160, y + 22, ocr_value),
                tb.Line(x + 170, y, x + 185, y + 8, "REV"), tb.Line(x + 170, y + 12, x + 182, y + 22, "00"),
                tb.Line(x, y - 100, x + 60, y - 92, "PROJECT"), tb.Line(x, y - 80, x + 60, y - 72, "CLIENT")]
    return doc, page, ocr_lines


def test_an_untrusted_ocr_number_is_kept_as_evidence_not_as_the_number():
    doc, page, ocr_lines = _sheet("XY) LAC-653-GEN-ZZZ-ELV-FA-211")
    block = tb.read_page(page, ocr_lines=ocr_lines)
    assert block is not None and block.source == "ocr"
    assert block.number is None
    assert block.number_literal == "XY) LAC-653-GEN-ZZZ-ELV-FA-211" and block.number_candidate == "LAC-653-GEN-ZZZ-ELV-FA-211"
    observation = block.observation()
    assert observation["number"] is None and observation["number_literal"] and any("not taken" in n for n in observation["notes"])


def test_a_clean_ocr_number_is_the_sheets_number():
    doc, page, ocr_lines = _sheet("AGC-DF-MEP-SD-PAS-02-D")
    block = tb.read_page(page, ocr_lines=ocr_lines)
    assert block.number == "AGC-DF-MEP-SD-PAS-02-D" and block.number_literal == "AGC-DF-MEP-SD-PAS-02-D"
