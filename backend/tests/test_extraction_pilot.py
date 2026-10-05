"""Real-project pilot (2026-09-28, docs/milestones/M2/real-project-pilot): the reader defects the regression and
exploration cohorts demonstrated, each pinned by the text of the document that showed it. The snippets are the
literal text runs of those originals (OCR or text layer), quoted with the source document; nothing is invented."""
from datetime import datetime

from app.services import document_control as dc


MODIFIED = datetime(2026, 9, 28)


def test_p01_a_label_ocr_glued_to_the_number_is_not_part_of_the_reference():
    # EP-29076/06- Drawings/01- FA/03- SD/.../25H-S202-NCC-SD-MEP-ELE-FA-050-00.pdf (sha 5066ef519604…), a scanned
    # LACASA shop-drawing submittal form: OCR runs the "Reference" label into the number.
    found = dc.reference_candidates("SHOPDRAWING SUBMITTAL\nReference25H-S202-NCC-SD-MEP-ELE-FA-050-00\nDate: 24th July 2026\n")
    assert [c.reference for c in found] == ["25H-S202-NCC-SD-MEP-ELE-FA-050-00"]
    assert found[0].category == "drawings" and found[0].kind == "serial"
    # the offset points at the number, so a label search behind it still sees "Reference"
    assert found[0].start == len("SHOPDRAWING SUBMITTAL\nReference")


def test_p02_an_empty_drawing_number_field_does_not_take_the_next_label_as_the_number():
    # EP-19977/EP-19977 Scan Doc/EP-19977 FA MS R1 App.pdf (sha d4a7765240…), page 2, an Emaar submittal register
    # print: "Drawing No:" is empty and the next line is the "Reference No:" label.
    text = ("Submittal Details\nSubmittal Register: 0\nContract Reference:\nSubmittal Register Line:\nLOA No: Voltas6374\n"
            "Drawing No:\nReference No: EBF-DCP-6374-VL-\nMAT-ELV-0003\nPlanned Start Date: 25/Jun/2020\n"
            "Title: Material Submittal for Fire Alarm with voice Evacuation & Fire Telephone\n")
    assert dc.drawing_number(text) is None
    assert dc.drawing_number("DRAWING NO: FA-101\nTITLE: GROUND FLOOR\n").group(1).strip() == "FA-101"
    # and the reference the page does carry is read as a material submittal, across the wrapped hyphen (P-04)
    found = dc.first_reference(text)
    assert found is not None and found.reference == "EBF-DCP-6374-VL-MAT-ELV-0003" and found.category == "submittals"
    records = dc.parse_page(text, "EP-19977 FA MS R1 App.pdf", MODIFIED, 2)
    assert all(r.reference != "Reference" for r in records)


def test_p03_an_ocr_letter_o_in_the_revision_suffix_is_the_revision_not_the_reference():
    # EP-29076/.../25H-NCC-SD-MEP-ELE-FA-024-R00 - Code C.pdf (sha …) and .../25H-S202-NCC-SD-MEP-ELE-EM-030-R00 -
    # Code B.pdf: OCR read the "-R00" suffix as "-RO".
    found = dc.reference_candidates("Reference 25H-S202-NCC-SD-MEP-ELE-FA-024-RO\nDate: 18 May 2026\n")
    assert [c.reference for c in found] == ["25H-S202-NCC-SD-MEP-ELE-FA-024-R0"]
    records = dc.parse_page("SHOP DRAWING SUBMITTAL\nReference 25H-S202-NCC-SD-MEP-ELE-EM-30-RO\nDrawing Title: 23rd Floor Emergency Lighting Layout\n",
                            "25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf", MODIFIED, 1)
    assert records and records[0].reference == "25H-S202-NCC-SD-MEP-ELE-EM-30" and records[0].revision == "R0"
    # a real trailing segment is untouched
    assert dc.reference_candidates("BBY006-GME-SDW-EL-LI-POD-P03-010031")[0].reference == "BBY006-GME-SDW-EL-LI-POD-P03-010031"


def test_p04_mat_is_a_material_submittal_code():
    # EP-13777/Approval Documents/A23-EFE-MAT-E-00033 Fire Alarm System - B.pdf (EFECO numbering) and the EP-19977
    # Emaar forms ("EBF-DCP-6374-VL-MAT-ELV-0003"): "-MAT-" numbers a material submittal.
    for text, expected in (("Ref No.: A23-EFE-MAT-E-00033 Rev. 01\nMaterial Submittal - Fire Alarm System", "A23-EFE-MAT-E-00033"),
                           ("Reference No: EBF-DCP-6374-VL-MAT-ELV-0003 Rev.No. 01", "EBF-DCP-6374-VL-MAT-ELV-0003")):
        found = dc.first_reference(text)
        assert found is not None and found.reference == expected and found.category == "submittals"
    # a date is still not a reference, and MAS / MAR are unchanged
    assert dc.first_reference("Date: 6-MAR-2026") is None
    assert dc.first_reference("BBY006-GME-MAS-EL-FA-0001").category == "submittals"


def test_parser_identity_moved_with_the_pilot_fixes():
    # .5 carried the four pilot fixes; .6 the review-05 title-block and reference-role rules (the fixes stay in force);
    # parse-2026-10-05.* the rules ported from g/project-log-and-drawing-scan, on top of them.
    assert dc.PARSER_VERSION == "parse-2026-10-05.4"
