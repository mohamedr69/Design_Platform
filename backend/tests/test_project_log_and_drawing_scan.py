"""What the unmerged branch `g/project-log-and-drawing-scan` (297fbaa, 2e7b061, 8ff68cb) added to the project log and
the drawing scan, ported onto the merged reader (merge/branch-audit/AUDIT.md, items B1, B3, B4, B5, B7, C1). Each test
here failed on the merged line before its item was ported, except the ones marked as regression tests: those pin
behaviour the merged line already had, so the port cannot quietly undo it."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
import pymupdf

import app.routers.jobs as jobs_router
from app.models import ProjectDocument
from app.services import document_control as dc
from app.services import document_sync

from .test_document_sync import _project, _result

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)

FORM = """Material Submittal for Fire Alarm
MAS Reference No.: BBY006-GME-MAS-EL-FA-0001
MAS Rev.: 00
ENGINEERING CONSULTANT COMMENTS AND APPROVAL STATUS
"""

DRAWING = """Drawing No: BBY006-GME-SDW-FP-FA-BSM-B01-010001
Drawing Title: BASEMENT-1 FLOOR PLAN FIRE ALARM LAYOUT
"""


def _pages(path, pages, size=None):
    """A PDF of text pages (A4 unless `size` says otherwise); an empty string is a blank page."""
    os.makedirs(dc._os_path(path.parent), exist_ok=True)
    with pymupdf.open() as document:
        for text in pages:
            page = document.new_page(**({"width": size[0], "height": size[1]} if size else {}))
            if text:
                page.insert_text((30, 30), text)
        document.save(dc._os_path(path))
    return path


# --- B7: a folder past the Windows path limit is listed, not silently skipped ----------------------------------------


@pytest.mark.skipif(os.name != "nt", reason="the 260-character path limit is Windows'")
def test_a_folder_past_the_windows_path_limit_is_listed_read_and_indexed(client, db_session, tmp_path, monkeypatch):
    """The archive nests a consultant's returned drawings five and six folders deep, and the folder's own path passes
    260 characters long before the file name does. `root.rglob` cannot open such a folder on a PC without the long
    path setting and returned nothing from it -- no error, no warning -- so the listing, the scan and the sync all
    went on as if the folder were empty. Listed from the long-path name, it is read like any other."""
    root = tmp_path / "EP-30850"
    deep = root.joinpath("04- Drawings", "08-Shop Drawing", "1.FAVE", "R1", "0" * 90, "1" * 90, "2" * 60)
    os.makedirs(dc._os_path(deep), exist_ok=True)
    drawing = _pages(deep / "BBY006-GME-SDW-FP-FA-BSM-B01-010001.pdf", [DRAWING])
    assert len(str(deep)) > 260, "the folder itself has to be past the limit to test anything"
    relative = drawing.relative_to(root).as_posix()

    # The listing: the file, under its own name and relative path, in path order beside a shallow one.
    _pages(root / "05- Submittals" / "MAS-0001.pdf", [FORM])
    listed = document_sync.listing(root)
    assert [rel for _path, rel, _size, _mtime in listed] == [relative, "05- Submittals/MAS-0001.pdf"]
    assert listed[0][0] == root / relative, "the index is keyed on the path: the same name rglob gave"

    # The scan reads it.
    rows, warnings = dc.scan_document_control(root, use_ocr=False)
    assert ("drawings", "BBY006-GME-SDW-FP-FA-BSM-B01-010001") in {(r.category, r.reference) for r in rows}
    assert [r.path for r in rows if r.category == "drawings"] == [relative]

    # And a sync indexes it.
    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    project_id = _project(client, root, "30850")
    result = _result(client, client.post(f"/projects/{project_id}/jobs/sync-documents"))
    assert result["files"] == 2 and result["unlisted_folders"] == []
    indexed = {row.relative_path for row in db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)}
    assert relative in indexed


def test_a_folder_that_cannot_be_listed_is_named_not_dropped(tmp_path, monkeypatch):
    """A folder the walk cannot open at all -- no permission, gone mid-walk -- is said, by the scan and the listing;
    the files the walk did reach are still listed."""
    root = tmp_path / "EP-30851"
    _pages(root / "a" / "MAS-0001.pdf", [FORM])
    real_walk = os.walk

    def walk(top, onerror=None, **kwargs):
        for folder, dirs, names in real_walk(top, onerror=onerror, **kwargs):
            if folder.endswith("locked"):
                onerror(PermissionError(13, "Access is denied", folder))
                dirs[:] = []
                continue
            yield folder, dirs, names

    (root / "locked").mkdir()
    monkeypatch.setattr(dc.os, "walk", walk)
    unlisted: list[str] = []
    assert [rel for _p, rel, _s, _m in document_sync.listing(root, unlisted=unlisted)] == ["a/MAS-0001.pdf"]
    assert unlisted == ["locked"]
    _rows, warnings = dc.scan_document_control(root, use_ocr=False)
    assert dc.unlisted_note("locked") in warnings


# --- B1: the first form in a file settles what the file is ----------------------------------------------------------

SAMPLE = ("Sample Approval Form\nSAF Reference No.: BBY006-GME-SAR-EL-FA-0001\nSAF Rev.: 00\n"
          "Sample Approval Request for Fire Alarm & Voice Evacuation System")


def _reading(path):
    with pymupdf.open(path) as pdf:
        return dc.read_open_pdf(pdf, str(path), NOW, False, None, full=True)


def test_a_form_bound_into_another_submission_is_not_a_submission(tmp_path):
    """The branch's test, on the merged reader: a sample board's submission carries the material submittal it was
    approved under as backup, behind the board's photo. That form is part of the sample's file, not a second
    submittal -- it is kept as an observation of the page, with the record it would have been."""
    _pages(tmp_path / "sample.pdf", [SAMPLE, "SAMPLE BOARD PHOTO", FORM])
    rows, _ = dc.scan_document_control(tmp_path, use_ocr=False)
    row, = rows
    assert (row.category, row.reference) == ("samples", "BBY006-GME-SAR-EL-FA-0001")
    reading = _reading(tmp_path / "sample.pdf")
    [bound] = [o for o in reading.observations if o["kind"] == "bound_form"]
    assert (bound["page"], bound["settled_by"]) == (3, "samples")
    assert (bound["record"]["category"], bound["record"]["reference"]) == ("submittals", "BBY006-GME-MAS-EL-FA-0001")


def test_a_sample_form_bound_behind_a_material_submittal_is_backup_too(tmp_path):
    _pages(tmp_path / "mas.pdf", [FORM, "DATASHEET - SMOKE DETECTOR", SAMPLE])
    rows, _ = dc.scan_document_control(tmp_path, use_ocr=False)
    assert [(r.category, r.reference) for r in rows] == [("submittals", "BBY006-GME-MAS-EL-FA-0001")]


def test_two_forms_of_one_kind_in_one_file_are_both_submissions(tmp_path):
    """Only a form of the *other* kind is backup: a file carrying two material submittals carries two."""
    second = FORM.replace("FA-0001", "FA-0002").replace("Fire Alarm", "Fire Alarm Sounders")
    _pages(tmp_path / "two.pdf", [FORM, second])
    rows, _ = dc.scan_document_control(tmp_path, use_ocr=False)
    assert sorted(r.reference for r in rows) == ["BBY006-GME-MAS-EL-FA-0001", "BBY006-GME-MAS-EL-FA-0002"]


def test_a_material_sample_tag_citing_its_submittal_is_still_one_sample(tmp_path):
    """Regression (merged numbering, M2 review 05): a CSCEC material sample tag prints the material submittal it
    belongs to (MAR); the tag is a sample, and the MAR it cites is neither a second row nor what settles the file."""
    tag = ("R1029-CSCEC-FM-MAR-001_R01 \nVersion Date \nMaterial Sample TAG\nR1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-\nZZZ-1020 \n"
           "Material Submittal Reference\nR1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-\nZZZ-1009 \nProject\nR1029 \nEngineer's Comments:\n")
    _pages(tmp_path / "tag.pdf", [tag, "SAMPLE PHOTO"])
    rows, _ = dc.scan_document_control(tmp_path, use_ocr=False)
    assert [(r.category, r.reference) for r in rows] == [("samples", "R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020")]


# --- B4: a report quoting a drawing's number is not the drawing ------------------------------------------------------

LUX_REPORTS = [
    # quoting a controlled drawing number, as the EP-30784 lux reports do
    "LUX CALCULATION REPORT\nDrawing No: BBY006-GME-SDW-EL-LI-ZZZ-L03-010012\n"
    "Drawing Title: L03 FLOOR PLAN EMERGENCY LIGHTING LAYOUT\nAverage illuminance 1.2 lux",
    # quoting a plain drawing number
    "LUX LEVEL REPORT\nDrawing No: EL-103 LEVEL 3\nTitle: EMERGENCY LIGHTING LUX LEVELS L03\nMinimum 1 lux",
    # a calculation sheet
    "BATTERY CALCULATION\nDrawing No: BBY006-GME-SDW-FP-FA-ZZZ-ZZZ-010099\nDrawing Title: FIRE ALARM PANEL FP-01\n"
    "Standby 24 h, alarm 30 min",
]


@pytest.mark.parametrize("text", LUX_REPORTS)
def test_a_lux_report_or_calculation_quoting_a_drawing_is_not_a_drawing(tmp_path, text):
    """An A4 report filed with the sheets quotes their number and title, which is all the text reader looked for:
    EP-30784's lux reports sat in the Drawings Log as emergency lighting drawings. The report heading over it says
    what the page is; it is kept as an observation of the page, never a drawing record."""
    path = _pages(tmp_path / "04- Drawings" / "2.EML" / "R0" / "lux.pdf", [text])
    rows, _ = dc.scan_document_control(tmp_path, use_ocr=False)
    assert [r for r in rows if r.category == "drawings"] == []
    [seen] = [o for o in _reading(path).observations if o["kind"] == "not_a_sheet"]
    assert seen["page"] == 1 and seen["record"]["category"] == "drawings" and seen["reason"].startswith("a report heading")


def test_a_small_text_sheet_a_submission_cover_and_a_scanned_sheet_are_still_drawings(tmp_path, monkeypatch):
    """Regression (the M2 design keeps these): an A4 text sheet carrying a title block's words, a shop drawing
    submission cover and a scanned sheet read through OCR stay drawings -- only a report heading, or a page with no
    sheet's word on it, is turned away."""
    cover = ("SHOP DRAWING SUBMITTAL\nNo: ABC-XYZ-SPM-SD-MEP-FA-0054\nRev: 01\nsubmitting herewith\nDRAWING & DESIGN REF\n"
             "ABC-XYZ-SPM-SD-MEP/FA-104\nGROUND FLOOR FIRE ALARM LAYOUT\nSubmitted By:\nReceived By:\n")
    _pages(tmp_path / "a" / "sheet.pdf", [DRAWING])
    _pages(tmp_path / "b" / "cover.pdf", [cover])
    _pages(tmp_path / "c" / "Shop Drawing scan.pdf", [""])
    monkeypatch.setattr(dc, "ocr_available", lambda: True)
    monkeypatch.setattr(dc, "_ocr_page", lambda page, image=None: DRAWING.replace("B01-010001", "B02-010002")
                        .replace("BASEMENT-1", "BASEMENT-2"))
    rows, _ = dc.scan_document_control(tmp_path)
    assert sorted(r.reference for r in rows if r.category == "drawings") == [
        "ABC-XYZ-SPM-SD-MEP-FA-0054", "BBY006-GME-SDW-FP-FA-BSM-B01-010001", "BBY006-GME-SDW-FP-FA-BSM-B02-010002"]


def _branch_title_block(path, number, title, layout, history, box_revision="00", dx=0, dy=0, size=(900, 900)):
    """The branch's sheet (2e7b061 test_document_control.title_block): labels, then the values -- optionally moved
    onto an A1 sheet, where the merged reader reads the title block by position."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as doc:
        page = doc.new_page(width=size[0], height=size[1])
        put = lambda x, y, t: page.insert_text((x + dx, y + dy), t)  # noqa: E731
        put(400, 300, "Rev  Date  Description")
        for index, (revision, date, note) in enumerate(history):
            put(400, 320 + index * 20, f"{revision}  {date}  {note}")
        put(400, 600, "Purpose of Issue:")
        put(400, 620, "DRAWING TITLE")
        put(410, 645, title)
        put(410, 665, layout)
        for offset, label in enumerate(["SCALE", "DRAWN", "CHECKED", "DATE", "SIZE", "REV. NO."]):
            put(400 + offset * 70, 700, label)
        issued = history[-1][1] if history else "06.08.2026"
        for offset, value in enumerate(["1:100", "IS", "RAMADAN", issued, "A0", box_revision]):
            put(400 + offset * 70, 720, value)
        put(400, 760, number)
        doc.save(path)


@pytest.mark.parametrize("a1", [False, True], ids=["branch-sheet", "a1-sheet"])
def test_another_trade_drawing_is_not_ours_to_log(tmp_path, a1):
    """Regression, ported from the branch: an MEP slab-opening layout filed with ours is not a drawing of a system we
    track -- on the A1 sheet too, where the title block is read by position."""
    _branch_title_block(tmp_path / "slab.pdf", "BBY006-GME-SDW-ME-BL-ZZZ-L03-010099", "LEVEL 03 FLOOR PLAN",
                        "MEP SLAB OPENING LAYOUT", [("00", "06.02.2026", "ISSUED")],
                        **({"dx": 1500, "dy": 900, "size": (2384, 1684)} if a1 else {}))
    assert dc.scan_document_control(tmp_path, use_ocr=False)[0] == []
