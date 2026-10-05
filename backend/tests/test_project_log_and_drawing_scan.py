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
