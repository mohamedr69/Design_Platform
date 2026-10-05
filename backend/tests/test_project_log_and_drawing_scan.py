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


# --- B3: the drawing's issue date, read from its own title block (rotated sheets too) -------------------------------

def _sheet_on(path, runs, *, size=(3370, 2384), rotation=0):
    """A drawing sheet whose text runs sit where the original's do -- (x, baseline y, text, font size) in display
    coordinates -- on a page drawn with `rotation` (/Rotate), the way CAD exports a landscape sheet onto a portrait
    page: the runs are laid down rotated, and the page's rotation turns them upright for the reader."""
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = size
    with pymupdf.open() as document:
        portrait = rotation in (90, 270)
        page = document.new_page(width=height if portrait else width, height=width if portrait else height)
        page.set_rotation(rotation)
        for x, y, text, size_pt in runs:
            page.insert_text(pymupdf.Point(x, y) * page.derotation_matrix, text, fontsize=size_pt, rotate=rotation)
        document.save(path)
    return path


def _l58(drop_date_cell=False):
    from .test_m2_review05 import L58_R01, L58_R01_BOXES

    if not drop_date_cell:
        return L58_R01
    # The same sheet with no DATE cell: its label and the date under it taken out.
    gone = {(3199, 2264), (3186, 2280)}
    return [run for run, box in zip(L58_R01, L58_R01_BOXES) if (box[0], box[1]) not in gone]


@pytest.mark.parametrize("rotation", [90, 270])
def test_a_rotated_sheet_is_read_by_position_issue_date_included(tmp_path, rotation):
    """BBY006 L58, the copy filed under R01 (M2 review 05's fixture), drawn on a rotated page: the title block is
    read where the sheet shows it -- its number, its REV box, its history, its title -- and the DATE cell gives the
    date the drawing says it was issued."""
    path = _sheet_on(tmp_path / "04- Drawings" / "2.EML" / "R01" / "L58" / "BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf",
                     _l58(), rotation=rotation)
    with pymupdf.open(path) as pdf:
        page = pdf[0]
        assert page.rotation == rotation
        raw = [line["dir"] for block in page.get_text("dict")["blocks"] for line in block.get("lines", [])]
        assert raw and all(abs(dx) < 0.05 for dx, _dy in raw), "the runs really are set rotated on the page"
    reading = _reading(path)
    [record] = reading.records
    assert record.reference == "BBY006-GME-SDW-EL-LI-ZZZ-L58-010042" and record.system_code == "ELS"
    assert record.printed_revision == "00" and "revision_conflict" in record.flags
    assert record.name == "L58 - RES 53 (TYP 3A) FLOOR PLAN EMERGENCY LIGHTING LAYOUT"
    assert str(record.issued) == "2026-08-06", "the DATE cell, not the file's time"
    [block] = [o for o in reading.observations if o["kind"] == "title_block"]
    assert (block["issued"], block["issued_source"]) == ("2026-08-06", "date cell")


def test_the_issue_date_is_the_date_cell_else_the_latest_date_of_the_revision_history(tmp_path):
    from app.services import title_block as tb

    from .test_m2_review05 import JAM_SD_FA_002, PAVA_00010

    # No DATE cell: the latest date the sheet's revision history records (01, 21.08.2026).
    [record] = _reading(_sheet_on(tmp_path / "L58.pdf", _l58(drop_date_cell=True))).records
    assert str(record.issued) == "2026-08-21"
    # The date under the "Date" label -- not the history's "Date" column header, whose row names Description.
    with pymupdf.open(_sheet_on(tmp_path / "JAM.pdf", JAM_SD_FA_002, size=(2384, 1684))) as pdf:
        block = tb.read_page(pdf[0])
    assert (block.issued, block.issued_source) == (datetime(2024, 9, 10).date(), "date cell")
    # "DATE : 28/08/2024": the value beside its label, on the label's row.
    with pymupdf.open(_sheet_on(tmp_path / "PAVA.pdf", PAVA_00010, size=(2384, 1684))) as pdf:
        block = tb.read_page(pdf[0])
    assert (block.issued, block.issued_source) == (datetime(2024, 8, 28).date(), "date cell")


def test_the_issue_date_is_stored_on_the_revision_beside_its_submission(client, db_session, tmp_path):
    """The date reaches the record the Drawings page reads -- ShopDrawingRevision.issued_on -- and the page; the
    revision's `submitted_at` (when it was filed) is not touched by it."""
    from app.core.timeutils import utc_now
    from app.models import Project, ShopDrawingRevision

    folder = tmp_path / "EP-30860"
    relative = "04- Drawings/2.EML/R01/L58/BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf"
    path = _sheet_on(folder / relative, _l58())
    project_id = _project(client, folder, "30860")
    [record] = _reading(path).records
    stored = document_sync._record_dict(dc.replace(record, path=relative), folder)
    assert stored["issued"] == "2026-08-06"
    db_session.add(ProjectDocument(project_id=project_id, role="document", path=str(path), relative_path=relative,
                                   filename=path.name, state="fresh", findings=[], acknowledged=[],
                                   extracted={"records": [stored], "notes": []}))
    db_session.get(Project, project_id).documents_synced_at = utc_now()
    db_session.commit()

    [row] = [r for r in client.get(f"/projects/{project_id}/drawings/log", params={"system": "ELS"}).json()["rows"]
             if r["source"] == "shop_drawing"]
    revisions = {r.revision: r for r in db_session.query(ShopDrawingRevision)}
    assert str(revisions["R1"].issued_on) == "2026-08-06"
    # R0 is proven by R1 and has no file of its own: no date is made up for it.
    assert revisions["R0"].issued_on is None
    # When it was filed stays the file's time: the issue date is beside it, not instead of it.
    assert revisions["R1"].submitted_at == record.modified.replace(tzinfo=None)
    assert row["revisions"]["R1"]["issued_on"] == "2026-08-06"
    drawings = client.get(f"/projects/{project_id}/logs").json()["drawings"]
    assert [d["issued"] for d in drawings] == ["2026-08-06"]


# --- B5: a REV box and a revision history that disagree are said in the log -----------------------------------------

L58_RELATIVE = "04- Drawings/2.EML/R01/L58/BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf"


def test_the_log_says_when_the_rev_box_and_the_revision_history_disagree(tmp_path):
    """BBY006 L58 R01 prints REV. NO. 00 over a revision history whose latest row is 01. The reader takes neither
    (M2 review 05, R5-01) -- the revision comes from the R01 folder -- and the log now says why, in a hint of its
    own kind (not "revision_conflict", which is two files for one revision) and in the revision's note."""
    from app.services import drawing_log

    [record] = _reading(_sheet_on(tmp_path / L58_RELATIVE, _l58())).records
    assert (record.printed_revision, record.history_revision, record.revision) == ("00", "01", "R1")
    built = drawing_log.build([], [record], in_system=lambda code: code == "ELS")
    [row] = [r for r in built["rows"] if r["source"] == "shop_drawing"]
    [hint] = [h for h in row["hints"] if h["kind"] == "title_block_revision_conflict"]
    assert hint["revision"] == "R1" and hint["severity"] == "warning"
    assert "REV box prints 00" in hint["note"] and "history ends at 01" in hint["note"] and "folder" in hint["note"]
    assert row["revisions"]["R1"]["note"] == hint["note"]
    assert not [h for h in row["hints"] if h["kind"] == "revision_conflict"]


def test_a_sheet_whose_rev_box_and_history_agree_raises_nothing(tmp_path):
    from app.services import drawing_log

    from .test_m2_review05 import PAVA_00010

    [record] = _reading(_sheet_on(tmp_path / "PAVA" / "AKA-BKG-ELE-B1-SD-PAVA-00010.pdf", PAVA_00010,
                                  size=(2384, 1684))).records
    assert record.history_revision == "02" and "revision_conflict" not in record.flags
    built = drawing_log.build([], [record], in_system=lambda code: code == "PAVA")
    assert not [h for r in built["rows"] for h in r["hints"] if h["kind"] == "title_block_revision_conflict"]


def test_the_conflict_reaches_the_revision_note_and_an_issue_keyed_by_drawing_and_revision(client, db_session, tmp_path):
    from app.core.timeutils import utc_now
    from app.models import DrawingIssue, Project, ProjectShopDrawing, ShopDrawingRevision

    folder = tmp_path / "EP-30861"
    path = _sheet_on(folder / L58_RELATIVE, _l58())
    project_id = _project(client, folder, "30861")
    [record] = _reading(path).records
    db_session.add(ProjectDocument(project_id=project_id, role="document", path=str(path), relative_path=L58_RELATIVE,
                                   filename=path.name, state="fresh", findings=[], acknowledged=[],
                                   extracted={"records": [document_sync._record_dict(dc.replace(record, path=L58_RELATIVE),
                                                                                     folder)], "notes": []}))
    db_session.get(Project, project_id).documents_synced_at = utc_now()
    db_session.commit()

    [row] = [r for r in client.get(f"/projects/{project_id}/drawings/log", params={"system": "ELS"}).json()["rows"]
             if r["source"] == "shop_drawing"]
    [drawing] = db_session.query(ProjectShopDrawing).filter(ProjectShopDrawing.project_id == project_id).all()
    revision = db_session.query(ShopDrawingRevision).filter(ShopDrawingRevision.shop_drawing_id == drawing.id,
                                                            ShopDrawingRevision.revision == "R1").one()
    assert "REV box prints 00" in revision.note and "history ends at 01" in revision.note
    [issue] = db_session.query(DrawingIssue).filter(DrawingIssue.project_id == project_id,
                                                    DrawingIssue.kind == "title_block_revision_conflict").all()
    assert issue.key == f"ELS:title_block_revision_conflict:{drawing.id}:R1"
    assert issue.severity == "warning" and issue.shop_drawing_id == drawing.id
    assert any(h["kind"] == "title_block_revision_conflict" and h["label"] == "Title block revision conflict"
               for h in row["hints"])


# --- C1: a drawing submission whose sheets could not be read says so -------------------------------------------------

SUBMISSION = ("Shop Drawings Submittal Form\nSDW Reference No.: BBY006-GME-SDW-FP-FA-0007\nSDW Rev.: 00\n"
              "Shop drawing for Fire Alarm Ground Floor\nConsultant status: Approved")


def test_a_submission_whose_drawings_could_not_be_read_names_itself(tmp_path):
    """A submission form with a sheet behind it that gives nothing (a scan, here, with OCR off): the form is logged,
    and the scan says the sheets were not read -- before, the log showed the form and silence."""
    _pages(tmp_path / "sub.pdf", [SUBMISSION, ""])
    rows, warnings = dc.scan_document_control(tmp_path, use_ocr=False)
    assert [(r.category, r.reference, r.status) for r in rows] == [("drawings", "BBY006-GME-SDW-FP-FA-0007", "approved")]
    [note] = [w for w in warnings if "logged from its form only" in w]
    assert note == "sub.pdf: no drawing title block could be read in this submission; it is logged from its form only."
    # File Sync shows the file as partially read, and why.
    kind, reason = dc.describe_note(note)
    assert kind == "partial" and "logged from its form only" in reason


def test_a_submission_whose_sheet_was_read_or_that_carries_no_sheet_says_nothing(tmp_path):
    _pages(tmp_path / "a" / "package.pdf", [SUBMISSION, DRAWING])          # its sheet was read
    _pages(tmp_path / "b" / "form.pdf", [SUBMISSION])                      # a form filed on its own
    _rows, warnings = dc.scan_document_control(tmp_path, use_ocr=False)
    assert not [w for w in warnings if "logged from its form only" in w]


def test_the_issue_date_column_migrates_up_and_down_cleanly(tmp_path):
    """d4f6a8c0e2b4 adds ShopDrawingRevision.issued_on after the merge head and takes it away again, leaving no
    rebuild table behind (a downgrade that fails further down the chain rolls the rebuild back with it)."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    from app.migrations import ALEMBIC_INI

    config = Config(str(ALEMBIC_INI))
    engine = create_engine("sqlite:///" + (tmp_path / "migrate.db").as_posix())
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        assert "issued_on" in {c["name"] for c in inspect(connection).get_columns("shop_drawing_revisions")}
        command.downgrade(config, "b7d9f1a3c5e7")
        tables = inspect(connection).get_table_names()
        assert "issued_on" not in {c["name"] for c in inspect(connection).get_columns("shop_drawing_revisions")}
        assert not [t for t in tables if t.startswith("_alembic_tmp")]
        command.upgrade(config, "head")
        assert "issued_on" in {c["name"] for c in inspect(connection).get_columns("shop_drawing_revisions")}
    engine.dispose()
