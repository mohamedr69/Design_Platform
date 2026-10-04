"""M2 review 05, R5-01: raw extraction on the real-project defect classes.

Every case is taken from a real original of the pilot (named with its content hash). The sheets are rebuilt here
from the originals' own text-run geometry (the runs, their positions and sizes as the PDF carries them), so the
tests run anywhere; where the sandbox copy of an original is present (C:/t/pilot/stage, the pilot's staged
originals), the original itself is read as well. No live data, model, worker or production endpoint."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import pytest

import app.routers.jobs as jobs_router
from app.models import ProjectDocument
from app.services import document_control as dc
from app.services import title_block as tb
from app.services import transmittals

from .test_document_sync import _project, _result

NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)
STAGE = Path("C:/t/pilot/stage")


@pytest.fixture()
def inline(monkeypatch):
    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)


def _sheet(path: Path, runs, size=(2384, 1684)) -> Path:
    """An A1 sheet whose text runs sit where the original's do: (x, baseline y, text, font size)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as document:
        page = document.new_page(width=size[0], height=size[1])
        for x, y, text, size_pt in runs:
            page.insert_text((x, y), text, fontsize=size_pt)
        document.save(path)
    return path


# AKA-BKG-ELE-B1-SD-PAVA-00010.pdf (EP-25091, sha256 fa9fede54892...): the plan's match-line callouts name the
# neighbour sheets, a reference-drawings table lists the architect's sheets, the revision history runs 00-02, and
# the title block's own cells say AKA-BKG-ELE-B1-SD-PAVA-00010 / REV 02. The reader took ...-00008 (review 05).
PAVA_00010 = [
    (900, 700, "REFER TO DWG No. AKA-BKG-ELE-B1-SD-PAVA-00008", 9), (900, 760, "REFER TO DWG No. AKA-BKG-ELE-B1-SD-PAVA-00009", 9),
    (900, 820, "PAVA PANEL-05", 9), (900, 880, "2CX2.5 sq.mm FIRE RATED CABLE(TYPICAL)", 9),
    (2168, 318, "REFERENCE DRAWINGS:", 10), (2100, 333, "DRAWING NO:", 8), (2170, 333, "REV.", 8), (2199, 333, "DRAWING TITLE:", 8),
    (2102, 355, "F-12174", 6), (2176, 355, "D0", 6), (2198, 351, "PART D UPPER ROOF FLOOR PLAN", 6),
    (2102, 386, "A 1011D", 6), (2176, 386, "D0", 6), (2102, 416, "E-06380", 6), (2176, 416, "D0", 6),
    (2105, 944, "02", 6), (2147, 944, "RE-ISSUED FOR APPROVAL", 6), (2259, 944, "06.09.25", 6),
    (2105, 964, "01", 6), (2147, 964, "ISSUED FOR APPROVAL", 6), (2259, 964, "28.08.24", 6),
    (2105, 983, "00", 6), (2147, 983, "ISSUED FOR APPROVAL", 6), (2259, 983, "27.06.24", 6),
    (2100, 1000, "REV", 7), (2153, 1000, "DESCRIPTION", 7), (2259, 1000, "DATE", 7), (2289, 1000, "DRAWN", 7), (2344, 1000, "APPR.", 7),
    (2102, 1538, "Drawing Title :", 8), (2120, 1555, "PUBLIC ADDRESS & VOICE EVAC.", 12),
    (2117, 1572, "LAYOUT - BASEMENT LEVEL B01", 12), (2155, 1590, "FLOOR PLAN - ZONE D", 12),
    (2102, 1605, "PURPOSE OF ISSUE :", 6), (2170, 1605, "FOR APPROVAL", 6), (2244, 1605, "SCALE:", 6), (2273, 1605, "1:250", 6),
    (2102, 1618, "DATE :", 6), (2129, 1618, "28/08/2024", 6), (2180, 1618, "DRAWN:", 6), (2243, 1618, "CHECKED:", 6), (2305, 1618, "APPROVED:", 6),
    (2102, 1632, "Drawing No.", 8), (2343, 1632, "REV", 8),
    (2105, 1655, "AKA-BKG-ELE-B1-SD-PAVA-00010", 12), (2345, 1655, "02", 12),
]

# JAM-SD-FA-002.pdf (EP-26369, sha256 a6624709a580...): the revision history's rows 0-7 above its header, the date
# 10.09.2024 in the cell under the "Date" label, and the title block's Rev. cell 07. The reader took R10 from the
# date (review 05, P-07).
JAM_SD_FA_002 = [
    (1900, 540, "SHOP DRAWING", 30),
    *[(1950, 1364 - 12 * n, str(n), 8) for n in range(8)],
    *[(1972, 1364 - 12 * n, d, 8) for n, d in enumerate(("10.09.24", "23.09.24", "20.11.24", "18.02.25", "10.06.25", "28.08.25", "16.09.25", "30.10.25"))],
    *[(2140, 1364 - 12 * n, "revised as per afs comments" if n else "Issue for Approval", 8) for n in range(8)],
    (1941, 1378, "Rev.", 10), (1985, 1378, "Date", 10), (2034, 1378, "Drn.", 10), (2110, 1378, "Apr.", 10), (2178, 1378, "Description", 10),
    (2064, 1393, "Revision History", 11),
    (1945, 1422, "Drawing Title", 11), (2013, 1463, "GROUND FLOOR PLAN LAYOUT", 11), (2041, 1482, "FIRE ALARM SYSTEM", 11),
    (1943, 1528, "Drawn", 11), (1994, 1528, "Checked Approved", 11), (2133, 1528, "Date", 11), (2216, 1523, "Scale/A1", 11),
    (1951, 1550, "MA", 11), (2131, 1550, "10.09.2024", 11), (2231, 1550, "1:200", 11),
    (1945, 1584, "Drawing No.", 11), (2218, 1585, "Rev.", 11),
    (2030, 1606, "JAM-SD-FA-002", 11), (2246, 1609, "07", 11),
]

# BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf, the copy filed under R01 (EP-30784, sha256 8fa6ab3b06b7...): the
# title block's REV. NO. cell prints 00 and its DATE 06.08.2026, while the revision history's latest row is 01,
# ISSUED FOR APPROVAL, 21.08.2026. The sheet contradicts itself.
L58_R01_BOXES = [   # (x0, y0, x1, y1, text): the original's own runs, display coordinates of its 3370 x 2384 sheet
    (3117, 1254, 3231, 1266, "REFERENCE DRAWINGS"), (3114, 1279, 3184, 1291, "DRAWING NO."), (3313, 1279, 3332, 1291, "REV"),
    (3114, 1297, 3290, 1306, "BBY006 - GME - SDW - EL - LI - ZZZ - L03 - 010012"), (3313, 1297, 3324, 1306, "00"),
    (3013, 1503, 3029, 1513, "Rev"), (3073, 1503, 3092, 1513, "Date"), (3210, 1503, 3256, 1513, "Description"),
    (3017, 1527, 3027, 1536, "00"), (3060, 1527, 3106, 1536, "06.08.2026"), (3179, 1527, 3287, 1536, "ISSUED FOR APPROVAL"),
    (3017, 1549, 3027, 1558, "01"), (3060, 1549, 3106, 1558, "21.08.2026"), (3179, 1549, 3287, 1558, "ISSUED FOR APPROVAL"),
    (3111, 2156, 3233, 2174, "SHOP DRAWING"), (3011, 2182, 3083, 2193, "DRAWING TITLE"),
    (3061, 2208, 3282, 2224, "L58 - RES 53 (TYP 3A) FLOOR PLAN"), (3065, 2225, 3273, 2240, "EMERGENCY LIGHTING LAYOUT"),
    (3028, 2264, 3048, 2272, "SCALE"), (3087, 2264, 3112, 2272, "DRAWN"), (3140, 2265, 3170, 2273, "CHECKED"),
    (3199, 2264, 3216, 2272, "DATE"), (3256, 2264, 3269, 2272, "SIZE"), (3301, 2264, 3329, 2272, "REV. NO."),
    (3025, 2280, 3049, 2291, "1:100"), (3098, 2280, 3106, 2291, "IS"), (3131, 2280, 3178, 2291, "RAMADAN"),
    (3186, 2280, 3233, 2291, "06.08.2026"), (3257, 2281, 3268, 2291, "A0"), (3307, 2281, 3318, 2291, "00"),
    (3013, 2298, 3122, 2307, "DRAWING CODE | ISO 19650"), (3013, 2316, 3060, 2324, "PROJECT CODE"), (3284, 2316, 3336, 2324, "SERIAL NUMBER"),
    (3063, 2334, 3280, 2347, "BBY006-GME-SDW-EL-LI-ZZZ-L58-010042"),
]
L58_R01 = [(x0, y1 - 0.22 * (y1 - y0), text, (y1 - y0) / 1.15) for x0, y0, x1, y1, text in L58_R01_BOXES]


def _read(path: Path, *, promote=False):
    with pymupdf.open(path) as pdf:
        return dc.read_open_pdf(pdf, str(path), NOW, False, None, full=True, promote=promote)


# --- the title block by position (P-06 / P-07) ---------------------------------------------------------------------


def test_pava_00010_is_its_own_number_and_revision_not_the_neighbour_it_refers_to(tmp_path):
    reading = _read(_sheet(tmp_path / "EP-25091" / "PAVA" / "B1" / "R2 B" / "AKA-BKG-ELE-B1-SD-PAVA-00010.pdf", PAVA_00010))
    [record] = reading.records
    assert record.reference == "AKA-BKG-ELE-B1-SD-PAVA-00010", "not -00008 from the match-line callout"
    assert (record.printed_revision, record.revision, record.revision_source) == ("02", "R2", "printed")
    assert record.system_code == "PAVA" and "revision_conflict" not in record.flags
    [block] = [o for o in reading.observations if o["kind"] == "title_block"]
    assert block["number"] == "AKA-BKG-ELE-B1-SD-PAVA-00010" and block["revision"] == "02"
    assert block["references"][:3] == ["F-12174", "A 1011D", "E-06380"], "the reference table is a fact of its own"
    assert [row[0] for row in block["history"]] == ["02", "01", "00"] and block["history_latest"] == "02"


def test_jam_sd_fa_002_reads_rev_07_and_the_date_under_the_label_is_not_revision_10(tmp_path):
    reading = _read(_sheet(tmp_path / "JAM" / "JAM-SD-FA-002.pdf", JAM_SD_FA_002))
    [record] = reading.records
    assert record.reference == "JAM-SD-FA-002" and record.system_code == "FAS"
    assert (record.printed_revision, record.revision, record.revision_source) == ("07", "R7", "printed")
    [block] = [o for o in reading.observations if o["kind"] == "title_block"]
    assert block["history_latest"] == "7" and not block["conflict"]
    # the text reader alone, as for a sheet with no usable title block, no longer reads a date as a revision
    assert dc.REV.search("Rev.\n10.09.2024") is None and dc.REV.search("REV: 02").group(1) == "02"


def test_a_sheet_whose_rev_cell_and_revision_history_disagree_is_flagged_not_settled(tmp_path):
    path = _sheet(tmp_path / "04- Drawings" / "2.EML" / "R01" / "L58" / "BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf", L58_R01, size=(3370, 2384))
    [record] = _read(path).records
    assert record.reference == "BBY006-GME-SDW-EL-LI-ZZZ-L58-010042"
    assert record.printed_revision == "00", "the REV. NO. cell, as printed"
    assert "revision_conflict" in record.flags
    assert (record.revision, record.revision_source) == ("R1", "folder"), "neither printed value is taken; the folder is what else there is"


def _lines(*runs):
    return [tb.Line(x0, y0, x1, y1, text) for x0, y0, x1, y1, text in runs]


def test_letters_are_a_revision_as_printed_and_are_not_mapped_to_a_number():
    # R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf (EP-26082): DRAWING NO. / REV. cells, REV. prints "AB"
    lines = _lines((3091, 2302, 3139, 2309, "DRAWING NO."), (3281, 2302, 3297, 2309, "REV."),
                   (3077, 2316, 3275, 2326, "R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208"), (3289, 2316, 3305, 2328, "AB"),
                   (3084, 1147, 3149, 1154, "DRAWING NUMBER"), (3283, 1147, 3299, 1154, "REV."),
                   (3082, 1159, 3171, 1165, "R1029-07-IBA-DWG-L08-FAS-1208"), (3292, 1160, 3298, 1166, "01"),
                   (3082, 1171, 3177, 1177, "R1029-07-KCD-DWG-L08-ARC-1208"), (3292, 1172, 3298, 1177, "03"))
    block = tb.read(lines, 3370, 2384)
    assert (block.number, block.revision) == ("R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208", "AB")
    text = "DRAWING NO.\nREV.\nR1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208\nAB\nFIRE ALARM LAYOUT\nDRAWING TITLE\nLEVEL 08 FIRE ALARM LAYOUT\n"
    [record] = dc.parse_page(text, "SD/FAVE/MGM1/AB/L8/R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf", NOW, 1, sheet=block)
    assert record.printed_revision == "AB" and "printed_revision_unmapped" in record.flags
    assert (record.revision, record.revision_source) == ("R0", "default"), "no R-number is made of letters"


def test_a_table_column_is_not_a_cell_and_a_reference_heading_excludes_a_single_row_table():
    # a CSCEC reference table: three rows under DRAWING NUMBER / REV. -- a list, never the sheet's number
    table = _lines((3053, 1146, 3117, 1153, "DRAWING NUMBER"), (3247, 1146, 3263, 1153, "REV."),
                   (3051, 1158, 3144, 1164, "R1029-03-KCD-DWG-L01-ARC-1230"), (3256, 1158, 3262, 1164, "00"),
                   (3051, 1169, 3141, 1175, "R1029-07-IBA-DWG-L01-MEC-1201"), (3256, 1170, 3262, 1175, "00"))
    assert tb.read(table, 3370, 2384) is None
    # BK Gulf CBS-00054 (rot 270, sha256 in the pilot manifest): a one-row reference table under its heading
    single = _lines((3027, 460, 3205, 476, "REFERENCE DRAWINGS:"), (2933, 480, 3012, 494, "DRAWING NO:"),
                    (3030, 480, 3057, 494, "REV."), (2937, 515, 2965, 523, "F-12728"), (3038, 515, 3048, 524, "D0"))
    assert tb.read(single, 3370, 2384) is None


def test_two_numbering_schemes_keep_the_controlled_number_and_otherwise_say_nothing():
    # R1029-01-IBA-DWG-ALL-FAS-6601-PDF [0].pdf (EP-26082): CLIENT and MUNICIPALITY drawing numbers
    lines = _lines((3043, 2287, 3123, 2295, "CLIENT DRAWING No."), (3295, 2287, 3331, 2295, "REVISION"),
                   (3047, 2302, 3241, 2315, "R1029-01-IBA-DWG-ALL-FAS-6601"), (3311, 2319, 3319, 2333, "0"),
                   (3043, 2321, 3151, 2329, "MUNICIPALITY DRAWING No."), (3047, 2336, 3105, 2349, "FA-01-001"))
    assert tb.read(lines, 3370, 2384, controlled=dc._controlled_number).number == "R1029-01-IBA-DWG-ALL-FAS-6601"
    assert tb.read(lines, 3370, 2384, controlled=dc._controlled_number).revision == "0"
    assert tb.read(lines, 3370, 2384).number is None, "without the grammar the sheet does not say which is its identity"


def test_a_number_the_export_split_into_runs_is_not_read_as_a_number():
    # R1029-08-BSB-DWG-L08-ARC-1208_Q.pdf (EP-26082 tender set): the cell's run is "R1029- -BSB-DWG- ARC-"
    lines = _lines((3043, 2287, 3123, 2295, "DRAWING No."), (3047, 2302, 3241, 2315, "R1029- -BSB-DWG- ARC-"))
    block = tb.read(lines, 3370, 2384)
    assert block is None or block.number is None


@pytest.mark.parametrize("relative, sha_prefix, reference, printed", [
    ("EP-25091/EP-25091 SD/Final SD  received on 04-02-26 from BK Gulf/ELETRICAL/PAVA/B1/R2 B/AKA-BKG-ELE-B1-SD-PAVA-00010.pdf", "fa9fede54892", "AKA-BKG-ELE-B1-SD-PAVA-00010", "02"),
    ("EP-26369/SHOP DRAWINGS/MRO SHOP DWGS/UPDATE DWGS/MRO UPDATE -3/JAM-SD-FA-002.pdf", "a6624709a580", "JAM-SD-FA-002", "07"),
])
def test_the_independently_checked_originals(relative, sha_prefix, reference, printed):
    path = STAGE / relative
    if not path.is_file():
        pytest.skip("the pilot's staged originals are not on this machine")
    assert hashlib.sha256(path.read_bytes()).hexdigest().startswith(sha_prefix), "the original the review checked"
    [record] = _read(path).records
    assert record.reference == reference and record.printed_revision == printed and record.revision == f"R{int(printed)}"


# --- the reply's own reference, the transmittal's items, wrapped labels, printed digits (P-08..P-11) -------------


REPLY_31 = ("SN\nConsultant Comments\nAl Arabia SSD Reply\nREMARKS\n1\nRefer to BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034 for\ncomments.\nComply\n"
            "Project: : BINGHATTI SKYBLADE\nReply to Consultant Comments on FA drawings\nEND\nRef No : BBY006-GME-SDW-EL-LI-POD-P01-010029\nPage 1 of 1\n")


def test_a_reply_is_the_reply_to_the_submission_its_header_names_not_a_drawing_its_comments_quote():
    # EP-30784 .../POD-1/Reply to MS Consultant Comments 31 (1).pdf (pilot P-08)
    [reply] = dc.parse_page(REPLY_31, "Reply to MS Consultant Comments 31 (1).pdf", NOW, 1)
    assert reply.source == "reply" and reply.reference == "BBY006-GME-SDW-EL-LI-POD-P01-010029"
    quoted_only = REPLY_31.replace("Ref No : BBY006-GME-SDW-EL-LI-POD-P01-010029\n", "")
    assert dc.parse_page(quoted_only, "reply.pdf", NOW, 1) == [], "a reply whose only number is quoted names nothing of its own"


TRANSMITTAL_OCR = ("DOCUMENT TRANSMITTAL\nTo || M/s.al Arabia EMW ee _ Date |: | 14/05/2026\n"
                   "atin. :| Mr. Hakem Ali/ Yousef Khan | AASS Ref. | |_18/0127/26\nProject ID il | | EP-29076 |\n"
                   ": Subject | | Material Submittal & sample Board / Fire Alarm & Voice Evacuation system\nDear Sir/ Madam,\n"
                   "ITEM | Document No. Description | No. of\n1 25H-S202-NCC-MAS-MEP- | Material Submittal / Fire Alarm, Voice Evacuation and 2No's\n"
                   "ELE-005-R3 Fire Telephone System.\n| | _ Sample Board / Central Battery System\n")


def test_a_scanned_transmittal_is_not_its_first_items_number_and_an_unread_tr_number_stays_unread(tmp_path, monkeypatch):
    # EP-29076/01- EP-29076 - Scan/EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf (pilot P-09): OCR read the TR number
    # as "18/0127/26" (re-reads: "7R", "1R", "TR") -- none is taken; the listed item is not the page's number.
    assert dc.parse_page(TRANSMITTAL_OCR, "ack.pdf", NOW, 1) == []
    assert transmittals.looks_like_transmittal(TRANSMITTAL_OCR) is False
    path = tmp_path / "EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf"
    with pymupdf.open() as document:
        document.new_page().draw_rect(pymupdf.Rect(40, 40, 500, 700))
        document.save(path)
    monkeypatch.setattr(dc, "_ocr_text", lambda page, sha256, index, renders=None: TRANSMITTAL_OCR)
    with pymupdf.open(path) as pdf:
        for promote in (False, True):
            reading = dc.read_open_pdf(pdf, str(path), NOW, True, None, full=True, promote=promote)
            assert reading.records == ()
            [seen] = [o for o in reading.observations if o["kind"] == "transmittal"]
            assert seen["reference"] is None and seen["flags"] == ["reference_unread"] and seen["raw_reference"] == "_18/0127/26"


def test_a_wrapped_number_is_not_joined_onto_the_next_fields_label_and_a_split_start_is_marked():
    # EP-26082 SCAN DOC/R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf, page 1 text layer (pilot P-10)
    text = "Material Submittal Reference\nR 1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-\nRev.01\nZZZ-1009\n"
    [candidate] = dc.reference_candidates(text)
    assert candidate.reference == "1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ", "not ...-ZZZ-Rev"
    assert candidate.incomplete and candidate.uncertain_start
    # a real wrapped segment still joins, and a label glued to its value is still a label (P-01)
    assert dc.reference_candidates("R1029-CSM-CO-ELE-FA-MAR-PJW-ZZZ-\nZZZ-1004")[0].reference == "R1029-CSM-CO-ELE-FA-MAR-PJW-ZZZ-ZZZ-1004"
    assert dc.reference_candidates("No.R1029-CSM-CO-ELE-FA-MAR-PJW-ZZZ-ZZZ-1004")[0].reference == "R1029-CSM-CO-ELE-FA-MAR-PJW-ZZZ-ZZZ-1004"
    records = dc.parse_page(text + "Material Submittal for Central Battery System\n", "MTG-1020.pdf", NOW, 1)
    assert records and {"reference_incomplete", "reference_uncertain"} <= set(records[0].flags)


def test_a_printed_number_is_read_as_printed_never_from_the_file_name():
    # 25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf (EP-29076): the cover prints "EM-30-R0"; the file says 030.
    # Pilot P-11 was the v1 label copying the file name (GOLDEN-LABELS v2 correction), not an OCR loss.
    [record] = dc.parse_page("SHOPDRAWING SUBMITTAL\nDate: 4th July 2026 Reference: 25H-S202-NCC-SD-MEP-ELE-EM-30-RO\n"
                             "Title/Subject: 23rd Floor Emergency Lighting Layout\n", "25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf", NOW, 1)
    assert record.reference == "25H-S202-NCC-SD-MEP-ELE-EM-30" and record.revision == "R0"


NCC_FULL_OCR = ("The Employer The PMC : The Engineer The Contractor MEP Contractor\nProject Name: 25hours Heimat Dubai Residences Tower\n"
                "Date: 01-May-2026\nTitle/Subject: 1st Basement Floor Plan Fire Alarm Layout\nAttachment Details:\nShop drawing Reference\n"
                "1st Basement Floor Plan Fire Alarm\nLayout Sheet - 01 of 02\n25H-AAEM-SD-ELEC-FA-B1-003\n"
                "4st Basement Floor Plan Fire Alarm\nLayout Sheet - 02 of 02\n25H-AAEM-SD-ELEC-FA-B1-003A\nTHE ENGINEER COMMENTS:\n")
NCC_BAND = "SHOPDRAWING SUBMITTAL\nDate: 01-May-2026 Reference: 25H-S202-NCC-SD-MEP-ELE-FA-003-R3\n"


def _scan(path: Path) -> Path:
    with pymupdf.open() as document:
        document.new_page().draw_rect(pymupdf.Rect(40, 40, 500, 700))
        document.save(path)
    return path


def test_a_listed_attachment_is_not_the_cover_and_a_lost_reference_line_is_read_again_in_its_band(tmp_path, monkeypatch):
    # 25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf (EP-29076): the full-page OCR lost "Reference: …-FA-003-R3"
    # and read the attachment table; the header band read on its own at the same scale has it.
    assert dc.parse_page(NCC_FULL_OCR, "cover.pdf", NOW, 1) == [], "the attachments are listed items"
    path = _scan(tmp_path / "25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf")
    monkeypatch.setattr(dc, "_ocr_text", lambda page, sha256, index, renders=None: NCC_FULL_OCR)
    bands = []
    monkeypatch.setattr(dc, "_ocr_band_text", lambda page, sha256, index: bands.append(index) or NCC_BAND)
    with pymupdf.open(path) as pdf:
        reading = dc.read_open_pdf(pdf, str(path), NOW, True, None, full=True, promote=False)
    [record] = reading.records
    assert record.reference == "25H-S202-NCC-SD-MEP-ELE-FA-003" and record.revision == "R3" and bands == [0]
    assert {"page": 1, "kind": "ocr_retry", "region": "header band", "used": True} in reading.observations
    # where the band has nothing either, nothing is made of the attachments
    monkeypatch.setattr(dc, "_ocr_band_text", lambda page, sha256, index: "Project Name: 25hours\n")
    with pymupdf.open(path) as pdf:
        reading = dc.read_open_pdf(pdf, str(path), NOW, True, None, full=True, promote=False)
    assert reading.records == () and {"page": 1, "kind": "ocr_retry", "region": "header band", "used": False} in reading.observations


def test_the_raw_floor_is_the_floor_the_title_prints_and_nothing_is_expanded():
    # EP-30088 (pilot P-05): "FIRST FLOOR FIRE ALARM LAYOUT" became the floor "FIRST FIRE ALARM" downstream
    assert dc.floor_name("FIRST FLOOR FIRE ALARM LAYOUT") == "FIRST FLOOR"
    assert dc.floor_name("HC FLOOR FIRE ALARM LAYOUT") == "HC FLOOR", "kept raw: no expansion, no elevation"
    assert dc.floor_name("GROUND FLOOR PLAN") == "GROUND FLOOR" and dc.floor_name("LIFT MACHINE ROOM  FLOOR PLAN") == "LIFT MACHINE ROOM FLOOR PLAN"
    assert dc.floor_name("FLOOR PLAN - ZONE D FIRE ALARM LAYOUT") is None


# --- persistence: the ordinary writer and the repair tool ------------------------------------------------------------


def test_the_title_block_reading_is_stored_by_processing_and_by_the_repair_tool(client, db_session, tmp_path, inline, monkeypatch):
    from scripts import repair_extraction as tool

    folder = tmp_path / "EP-30951"
    _sheet(folder / "05- Drawings" / "PAVA" / "AKA-BKG-ELE-B1-SD-PAVA-00010.pdf", PAVA_00010)
    project_id = _project(client, folder, ep="30951")
    result = _result(client, client.post(f"/projects/{project_id}/jobs/sync-documents"))
    assert result.get("failed", 0) == 0, result
    row = db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).one()
    db_session.refresh(row)
    [stored] = row.extracted["records"]
    assert stored["reference"] == "AKA-BKG-ELE-B1-SD-PAVA-00010" and stored["printed_revision"] == "02" and stored["revision"] == "R2"
    assert row.reference == "AKA-BKG-ELE-B1-SD-PAVA-00010" and row.extracted["parser_version"] == dc.PARSER_VERSION
    assert any(o["kind"] == "title_block" and o["number"] == stored["reference"] for o in row.extracted["observations"])
    json.dumps(row.extracted)

    # an earlier parser's reading of the same bytes (the neighbour's number) is repaired to the sheet's own
    old = json.loads(json.dumps(row.extracted))
    old["records"][0].update(reference="AKA-BKG-ELE-B1-SD-PAVA-00008", revision="R0", printed_revision=None, revision_source="default")
    old["parser_version"], old["observations"] = "parse-2026-09-28.5", []
    row.extracted, row.reference, row.revision = old, "AKA-BKG-ELE-B1-SD-PAVA-00008", "R0"
    db_session.commit()
    monkeypatch.setattr(tool, "root_of", lambda r: str(folder))
    entry = tool.preview(db_session, row, ["selected by id"], False)
    assert entry["outcome"] == "would_repair" and entry["new"]["reference"] == "AKA-BKG-ELE-B1-SD-PAVA-00010" and entry["new"]["revision"] == "R2"
    tool.apply_row(db_session, row, entry)
    db_session.refresh(row)
    assert row.reference == "AKA-BKG-ELE-B1-SD-PAVA-00010" and row.revision == "R2"
    assert row.extracted["records"][0]["printed_revision"] == "02" and row.extracted["parser_version"] == dc.PARSER_VERSION
    assert any(o["kind"] == "title_block" for o in row.extracted["observations"])


# --- numbers and revisions that are not the page's own (review 05 re-score of the frozen corpus) ----------------------


def test_a_forms_own_edition_and_a_tables_header_are_not_the_documents_revision():
    # EP-19977 FA MS R1 App.pdf (Emaar form): "Form No.: F-013 / Rev.0" is the template's edition
    assert dc.page_revision("MATERIAL / EQUIPMENT APPROVAL FORM\nForm No.: F-013\nRev.0\nDate: July 2016\n") is None
    # 25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf: the LACASA form's footer "(Rev.02)"
    assert dc.page_revision("Appendix D3 Page 1of1 LAC-SM-Feb. 2014 (Rev.02\n") is None
    # 25H-S202-NCC-SD-MEP-ELE-FA-031-R00 - Code B.pdf page 2 (scanned sheet): the reference table's header row
    assert dc.page_revision("REFERENCE IFC DRAWINGS\n| DRAWING No, / DOCUMENTS No. Rev\n1 os _ a 1 SEE\n") is None
    # a field and its value are still a revision
    assert dc.page_revision("Drawing No: X-SD-001 Rev: 01\n").group(1) == "01"
    assert dc.page_revision("No: ABC-XYZ-SPM-SD-MEP-FA-0054\nRev: 01\n").group(1) == "01"


def test_a_subject_line_a_citation_and_a_form_template_number_are_never_the_pages_identity():
    # A23-EFE-MAT-E-00033 ... page 3 (the consultant's comment sheet), EP-19977-Var1-Voltas.pdf (a quotation),
    # R1029-CSM-...-1020-01_CODE C.pdf page 6 (the CSCEC form's footer number)
    for text in ("Subject: Material Submittal of Fire Alarm System - Ref. A23-Effeco-MAT-E-00033\nRev.0, Dated 30 April 2018,\n"
                 "1. Selected PC is not accepted it should match with our specs.\n",
                 "Quotation\nRefrence _: [EP-19977-Var. 01\n1. Scope of Work: Supply, Testing & Commissioning as per Material Submittal "
                 "comments (Ref: EBF-DCP-6374-VL-\nMAT-ELV-0003). Any additional material required will be quoted separately.\n",
                 "Engineer's Comments:\nR1029-CSCEC-FM-MAR-001_R01 \nVersion Date \nMaterial Submittal Reference\n"):
        assert dc.first_reference(text) is None
        assert dc.parse_page(text, "page.pdf", NOW, 1) == []


def test_a_fax_cover_is_not_the_submittal_it_forwards():
    # EP-13777/Approval Documents/AAR-001 Commented Material Submittal- ... (1).pdf page 1
    text = ("EFECO\nFACSIMILE TRANSMITTAL SHEET\nTO: MR. AHAMED\nSubject: Commented Material Submittal - FIRE ALARM SYSTEM\n"
            "With reference to the above-mentioned subject, kindly find attached above captioned subject\n"
            "material submittal reference # A23-EFE-MAT-E-0033, Rev 1 dated 20.06.18 which has been\ncommented by the consultant.\n")
    assert dc.parse_page(text, "AAR-001.pdf", NOW, 1) == []


def test_a_callout_to_another_sheet_is_not_the_sheets_number(tmp_path):
    # SA-H2-BEST-ICT-00100a.pdf (EP-26369): the plan's callouts "DWG No. SA-H2-BEST-FA-00104" (label and number in
    # one run) sit in the sheet's right-hand part; the title block's DRAWING NO: cell is the sheet's own number. The
    # reader had made FA-00104 the record.
    path = _sheet(tmp_path / "SA-H2-BEST-ICT-00100a.pdf", [
        (2748, 1178, "DWG No. SA-H2-BEST-FA-00104", 7), (2416, 981, "DWG No. SA-H2-BEST-ICT-00101", 7),
        (1500, 900, "4x100mm uPVC DUCT FOR ICT/SECURITY +FIRE ALARM+EMERGENCY", 9),
        (2913, 2308, "DRAWING NO:", 9), (3129, 2308, "CONSULTANT:", 9), (3232, 2308, "REVISION:", 9),
        (2933, 2336, "SA-H2-BEST-ICT-00100a", 12), (3156, 2336, "SPEC", 12), (3296, 2336, "00", 12),
        (2913, 2078, "DRAWING TITLE:", 9), (2916, 2132, "SITE PLAN STRUCTURED CABLING LAYOUT- PART -1", 16)], size=(3370, 2384))
    reading = _read(path)
    [block] = [o for o in reading.observations if o["kind"] == "title_block"]
    assert (block["number"], block["revision"]) == ("SA-H2-BEST-ICT-00100a", "00")
    assert block["title"] == "SITE PLAN STRUCTURED CABLING LAYOUT- PART -1"
    assert all(r.reference != "SA-H2-BEST-FA-00104" for r in reading.records)
    assert reading.records == (), "a structured-cabling sheet is no tracked system's record"


def test_ocr_of_a_title_block_sheets_images_adds_no_other_identity(tmp_path, monkeypatch):
    # The same rule where OCR runs: a fire alarm sheet whose title block gives its number, with an image OCR reads
    # another sheet's number off.
    path = _sheet(tmp_path / "SA-H2-BEST-FA-00201.pdf", [
        (2913, 2308, "DRAWING NO:", 9), (3129, 2308, "CONSULTANT:", 9), (3232, 2308, "REVISION:", 9),
        (2933, 2336, "SA-H2-BEST-FA-00201", 12), (3156, 2336, "SPEC", 12), (3296, 2336, "00", 12),
        (2913, 2078, "DRAWING TITLE:", 9), (2916, 2132, "FIRE ALARM SCHEMATIC DIAGRAM", 16)], size=(3370, 2384))
    with pymupdf.open(path) as document:      # an image on the sheet, so the reader OCRs its region
        document[0].insert_image(pymupdf.Rect(400, 400, 1400, 1400), pixmap=pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 400, 400), 0))
        document.saveIncr()
    calls = []
    ocr = "DWG No. SA-H2-BEST-FA-00104\nFIRE ALARM LAYOUT\nDRAWING TITLE\nFIRE ALARM\n"
    monkeypatch.setattr(dc, "_ocr_regions_text", lambda page, regions, sha256, index, renders: calls.append("regions") or ocr)
    monkeypatch.setattr(dc, "_ocr_text", lambda page, sha256, index, renders=None: calls.append("page") or ocr)
    with pymupdf.open(path) as pdf:
        reading = dc.read_open_pdf(pdf, str(path), NOW, True, None, full=True, promote=False)
    assert calls, "the sheet's image was OCRed"
    assert [r.reference for r in reading.records] == ["SA-H2-BEST-FA-00201"]


def test_a_material_sample_tag_is_its_own_number_not_the_submittal_it_belongs_to():
    # R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf page 6 (EP-26082): the CSCEC tag form prints its own
    # number and the material submittal it belongs to; the reader took the submittal's (the grammar knew no MTG).
    text = ("R1029-CSCEC-FM-MAR-001_R01 \nVersion Date \nMaterial Sample TAG\nR1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-\nZZZ-1020 \n"
            "Material Submittal Reference\nR1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-\nZZZ-1009 \nProject\nR1029 \nEngineer's Comments:\n")
    [record] = dc.parse_page(text, "tag.pdf", NOW, 6)
    assert (record.reference, record.category) == ("R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020", "samples")
    # MAR, MAS, MAT, SAR and the drawing codes read as before
    assert dc.first_reference("BBY006-GME-MAS-EL-FA-0001").category == "submittals"
    assert dc.first_reference("ABC-XYZ-SPM-SD-MEP-FA-0054").category == "drawings"
