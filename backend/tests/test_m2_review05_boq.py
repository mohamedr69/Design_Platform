"""M2 review 05, R5-04: the deterministic BOQ reader and the BOQ read's completion contract.

The reader: agreement between OCR passes over the same pixels is not independent confirmation; a column that reads
as item numbers, or crossed columns, is held for review, never dropped. The contract: a read that attempted no sheet
is not stamped as the project's BOQ read; a re-read never offers a sheet's lines for removal because the sheet
could not be read, and a re-read that read nothing fails. Disposable data only (the file-backed test harness)."""
from PIL import Image, ImageDraw

import app.routers.projects as projects_router
from app.models import BoqCandidate, ExtractionRun, Project
from app.services import design_sheet_extractor as dse
from app.services.design_sheet_extractor import DesignSheetExtractionError, ExtractedBoqLine

from .test_ai_sheet_reader import _login, _project
from .test_projects import _login_admin, _valid_project_payload


def _line(catalog, description, quantity, *, y=0, span=(0, 100), page=1, confidence=None):
    return ExtractedBoqLine(catalog_no=catalog, description=description, quantity=quantity, group_heading="Main",
                            confidence=90.0, page=page, raw_quantity=quantity, y_px=y, table_span=span, catalog_confidence=confidence)


# --- the reader: correlated agreement ------------------------------------------------------------------------------


def _check(strip: str, confidence: float, monkeypatch, passes: list[str], height: int = 60):
    """The part-number check on one cell, the two passes' readings fixed (the OCR engine is the seam)."""
    image = Image.new("L", (900, height), 255)
    ImageDraw.Draw(image).text((20, 10), strip, fill=0)
    line = _line(strip, "Emergency light", "4", y=height // 2, confidence=confidence)
    line.row_bounds = (0, height)
    readings = iter(passes)
    monkeypatch.setattr(dse.pytesseract, "image_to_string", lambda *a, **k: next(readings))
    dse._confirm_catalog(image, line, (0, 900))
    return line


def test_a_confident_strip_read_is_not_second_guessed():
    # the check runs only under RECHECK_QUANTITY_BELOW: a strip read at 90 % or more stands on its own word, as before
    assert dse.RECHECK_QUANTITY_BELOW == 90


def test_passes_repeating_an_unsure_strip_read_are_not_a_confirmation(monkeypatch):
    # EP-19977 CBS Design (sha256 ebca6cb9...): the strip read the printed KCW019ML-IP65 as KCWO019ML-IP65 at 51 %,
    # and both passes on the same cell read the same. Repeated, not independent: the row is held with every reading.
    line = _check("KCWO019ML-IP65", 51.0, monkeypatch, ["KCWO019ML-IP65", "KCWO019ML-IP65"])
    assert line.catalog_uncertain and line.catalog_check["agreement"] == "correlated" and not line.catalog_check["confirmed"]
    assert line.catalog_no == "KCWO019ML-IP65", "the literal reading stays; nothing is substituted, O is not turned into 0"
    assert [r["value"] for r in line.catalog_alternates] == ["KCWO019ML-IP65", "KCWO019ML-IP65"]
    issue = dse._uncertain_part_issue(line, 1)
    assert issue.detail["catalog_no"] == "KCWO019ML-IP65" and issue.detail["quantity"] == "4" and issue.detail["catalog_cell"]
    assert "same pixels" in issue.detail["reason"]


def test_a_pass_reading_another_part_still_makes_the_row_uncertain(monkeypatch):
    line = _check("4-CABI6D", 70.0, monkeypatch, ["4-CAB16D", "4-CAB16D"])
    assert line.catalog_uncertain and "another part number" in line.catalog_check["reason"]


def test_a_split_multiline_identity_is_read_as_a_block_and_held_when_unsure(monkeypatch):
    # EP-30784 EML: "SL2MNM65D3C-M" over "+SL23I" in one tall cell: the block passes read it whole
    line = _check("SL2MNM65D3C-M +SL23I", 81.5, monkeypatch, ["SL2MNM65D3C-M +SL23I", "SL2MNM65D3C-M +SL23I"], height=120)
    assert line.catalog_check["multiline"] and line.catalog_uncertain and line.catalog_check["agreement"] == "correlated"


# --- the reader: columns that do not read as a BOQ's -----------------------------------------------------------------


def test_an_item_number_column_read_as_quantities_is_held_for_review_on_every_page():
    # EP-26369 MS FAS\BOQ.pdf: Item | Model | Description | Quantity -- items 1-13 read as quantities 1-13, and the
    # shorter sections (items 1-4) in the same column layout, on page 1 and page 2.
    span = (201, 2189)
    rows = [_line(f"P-{n}", f"Part {n}", str(n), y=100 + 40 * n, span=span) for n in range(1, 14)]
    short = [_line(f"Q-{n}", f"Other {n}", str(n), y=900 + 40 * n, span=span) for n in range(1, 4)]
    page2 = [_line("SIGA-CT1", "Single input module", "1", y=100, span=span, page=2)]
    other = [_line("X-1", "Elsewhere", "7", y=100, span=(5, 1500), page=2)]
    notes = []
    dse._hold_implausible_columns(rows + short + page2 + other, notes)
    assert all(l.quantity is None and l.quantity_parse["held_quantity"] for l in rows + short + page2)
    assert other[0].quantity == "7", "another column layout is not touched"
    assert "counts 1..13 down 13 rows" in notes[0]
    # nothing is dropped: each held row becomes a review row with its cell
    assert all(dse._dropped_row_issue(l, i) is not None for i, l in enumerate(rows + short + page2, 1))


def test_real_quantities_that_happen_to_repeat_or_vary_are_not_item_numbers():
    rows = [_line(f"P-{n}", f"Part {n}", q, y=40 * n) for n, q in enumerate(["1", "1", "2", "1", "6", "12", "3"], 1)]
    dse._hold_implausible_columns(rows, [])
    assert [l.quantity for l in rows] == ["1", "1", "2", "1", "6", "12", "3"]


def test_duplicate_parts_with_different_quantities_stay_two_lines():
    rows = [_line("SIGA-CT1", "Single input module", "14", y=40), _line("SIGA-CT1", "Single input module", "6", y=80)]
    dse._hold_implausible_columns(rows, [])
    assert [(l.catalog_no, l.quantity) for l in rows] == [("SIGA-CT1", "14"), ("SIGA-CT1", "6")]


def test_a_table_whose_descriptions_are_numbers_has_crossed_columns_and_is_held():
    # EP-26082 Aspiration Design: part numbers read as quantities ("910900"), quantities as descriptions ("2000")
    rows = [_line("Pipe-Red, ABS, 3/4\", 3m", "2000", "910900", y=40), _line("Socket-Red, ABS, 3/4", "2000", "910908", y=80),
            _line("End cap-Red, ABS, 3/4", "240", "910927", y=120)]
    notes = []
    dse._hold_implausible_columns(rows, notes)
    assert all(l.quantity is None for l in rows) and "descriptions are numbers" in notes[0]


# --- the completion contract -----------------------------------------------------------------------------------------


def test_a_first_read_that_attempted_no_sheet_is_not_stamped_and_is_tried_again(client, db_session, tmp_path, monkeypatch):
    sheet = tmp_path / "EP-70105 FAS Design.pdf"
    sheet.write_bytes(b"%PDF-1.4 sheet")
    project = _project(db_session, sheet, ep="70105")
    _login(client)
    first = client.post(f"/projects/{project.id}/boq/ensure").json()
    assert not first["extracted"] and first["items"] == [] and "Not read: AI assistance is disabled" in first["warnings"][0]
    db_session.expire_all()
    assert db_session.get(Project, project.id).boq_extracted_at is None, "nothing read, nothing stamped"
    again = client.post(f"/projects/{project.id}/boq/ensure").json()
    assert not again["extracted"]
    assert db_session.query(ExtractionRun).filter(ExtractionRun.project_id == project.id).count() == 1, "recorded once, not per open"
    # a reader that can read the sheet (the test seam) reads it on the next open
    monkeypatch.setattr(projects_router, "extract_boq_lines", lambda path: [_line("SIGA-PS", "Smoke detector", "12")])
    read = client.post(f"/projects/{project.id}/boq/ensure").json()
    assert read["extracted"] and [i["catalog_no"] for i in read["items"]] == ["SIGA-PS"]


def _two_sheet_project(client, monkeypatch, ep):
    reads = {"FAS": [_line("4-CPU", "Central Processor Module", "1"), _line("SIGA-PS", "Smoke detector", "120")],
             "ELS": [_line("SL-1", "Emergency light", "40")]}
    fail: set = set()

    def extract(path):
        code = "ELS" if "ELS" in str(path) else "FAS"
        if code in fail:
            raise DesignSheetExtractionError("Could not find a line-item table in this Design Sheet")
        return list(reads[code])

    monkeypatch.setattr(projects_router, "extract_boq_lines", extract)
    _login_admin(client)
    payload = _valid_project_payload(ep)
    payload["design_sheets"] = [{"system_code": "FAS", "document_path": r"C:\archive\x\FAS Design.pdf"},
                                {"system_code": "ELS", "document_path": r"C:\archive\x\ELS Design.pdf"}]
    pid = client.post("/projects", json=payload).json()["id"]
    body = client.post(f"/projects/{pid}/boq/ensure").json()
    assert body["extracted"] and len(body["items"]) == 3
    return pid, body, fail


def test_a_reread_never_offers_an_unread_sheets_lines_for_removal(client, db_session, monkeypatch):
    pid, body, fail = _two_sheet_project(client, monkeypatch, "61105")
    fail.add("ELS")
    built = client.post(f"/projects/{pid}/boq/candidates")
    assert built.status_code == 201, built.text
    candidate = built.json()
    assert candidate["summary"]["failed_sheets"] == ["ELS Design.pdf"] and candidate["summary"]["not_reread"] == 1
    assert not [c for c in candidate["changes"] if c["kind"] == "removed"], "SL-1 was not re-read, so it is not 'no longer yielded'"
    applied = client.post(f"/projects/{pid}/boq/candidates/{candidate['id']}/apply", json={"decisions": {}})
    assert applied.status_code == 200, applied.text
    assert sorted(i["catalog_no"] for i in client.get(f"/projects/{pid}/boq").json()) == ["4-CPU", "SIGA-PS", "SL-1"]


def test_a_reread_that_read_no_sheet_fails_and_leaves_the_good_boq_as_it_was(client, db_session, monkeypatch):
    pid, body, fail = _two_sheet_project(client, monkeypatch, "61106")
    fail.update({"FAS", "ELS"})
    before = client.get(f"/projects/{pid}/boq").json()
    built = client.post(f"/projects/{pid}/boq/candidates")
    assert built.status_code == 409 and "No Design Sheet could be read" in built.json()["detail"]
    assert client.get(f"/projects/{pid}/boq").json() == before
    assert db_session.query(BoqCandidate).filter(BoqCandidate.project_id == pid, BoqCandidate.status == "pending").count() == 0
    # the job route: the job fails, it does not succeed with every sheet failed
    import app.routers.jobs as jobs_router

    monkeypatch.setattr(jobs_router, "RUN_INLINE", True)
    job = client.post(f"/projects/{pid}/jobs/boq-reread").json()
    finished = client.get(f"/jobs/{job['id']}").json()
    assert finished["status"] == "failed" and "No Design Sheet could be read" in (finished.get("error") or "")
    assert client.get(f"/projects/{pid}/boq").json() == before
