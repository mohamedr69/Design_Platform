"""M2 review 07, E: extraction safety within existing ownership.

1. An incomplete / uncertain extracted reference is source-linked candidate evidence under a stable internal key: it
   neither sets the row mirror nor reaches the register builders -- while a business row already filed under that
   exact value is preserved as it is (no delete, rename or false "missing"), and listed for adjudication.
2. A transmittal's listed submittal is not the transmittal's identity (EP-29076 "FA MS & Sam B CBS Ack"), on the
   application's own processing path, with its reading kept across a second sync."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pymupdf

from app.models import Project, ProjectDocument, ProjectShopDrawing, ProjectSubmittal, RoleEnum
from app.services import document_control, document_sync

from .conftest import make_user

from .test_document_sync import _project, _result, ai  # noqa: F401  (fixture)
from .test_submittal import _reading

NOW = datetime(2026, 9, 29, tzinfo=timezone.utc)


def _record(reference, *, flags=(), category="submittals", page=1, status="UR", path="a.pdf"):
    return document_control.ControlledDocument("FAS", "Fire alarm", path, NOW, reference, "R0", status, page=page,
                                               category=category, flags=tuple(flags))


# --- 1. incomplete / uncertain references -------------------------------------------------------------------------------


def test_a_flagged_reference_does_not_set_the_mirror_and_is_kept_as_pending_evidence():
    row = SimpleNamespace(id=7, reference=None, revision=None, status=None, system_code=None)
    pending = document_sync.mirror_from(row, [_record("A23-EFECO-MAT-E", flags=["reference_incomplete"], page=4)])
    assert row.reference is None and row.system_code == "FAS"
    assert pending == [{"key": "doc:7:p4:r0", "reference_literal": "A23-EFECO-MAT-E", "flags": ["reference_incomplete"],
                        "page": 4, "printed_revision": None, "status": "UR"}]
    # an existing mirror is neither renamed nor cleared by an uncertain reading
    row.reference, row.status = "A23-EFE-MAT-E-00033", "approved"
    document_sync.mirror_from(row, [_record("A23-EFECO-MAT-E", flags=["reference_uncertain"])])
    assert (row.reference, row.status) == ("A23-EFE-MAT-E-00033", "approved")
    # a settled record beside it still sets the mirror as before
    document_sync.mirror_from(row, [_record("V-EL-MTG-PJW-ZZZ", flags=["reference_incomplete"]), _record("R1029-CSM-CO-1020", status="rejected")])
    assert (row.reference, row.status) == ("R1029-CSM-CO-1020", "rejected")


def _project_with(db, records_by_doc: dict, *, ep="R7E1") -> Project:
    user = make_user(db, f"{ep.lower()}@test.local", RoleEnum.admin)
    project = Project(ep_number=ep, project_name="r7", source_folder_path="C:/nowhere", created_by_id=user.id)
    db.add(project)
    db.flush()
    for i, (name, records) in enumerate(records_by_doc.items()):
        db.add(ProjectDocument(project_id=project.id, path=f"C:/nowhere/{name}", relative_path=name, filename=name, role="document",
                               state="fresh", extracted={"records": [document_sync._record_dict(r, Path(".")) for r in records], "notes": []}))
    db.commit()
    return project


def test_log_records_hold_a_flagged_reference_unless_a_business_row_already_carries_it(db_session):
    project = _project_with(db_session, {
        "A23-EFE-MAT-E-00033.pdf": [_record("A23-EFECO-MAT-E", flags=["reference_incomplete"], page=4)],
        "MTG-1020.pdf": [_record("V-EL-MTG-PJW-ZZZ", flags=["reference_incomplete"])],
        "ok.pdf": [_record("BBY006-GME-MAS-EL-FA-0002")]})
    records, warnings = document_sync.log_records(db_session, project)
    assert [r.reference for r in records] == ["BBY006-GME-MAS-EL-FA-0002"]
    assert any("held as evidence" in w for w in warnings)
    # an existing business row already filed under the uncertain key is preserved: its record still reaches the
    # builders (no false "missing"), and nothing renames or deletes it
    db_session.add(ProjectSubmittal(project_id=project.id, title="A23", reference="A23-EFECO-MAT-E", system_code="FAS"))
    db_session.commit()
    records, _w = document_sync.log_records(db_session, project)
    assert sorted(r.reference for r in records) == ["A23-EFECO-MAT-E", "BBY006-GME-MAS-EL-FA-0002"]
    cases = {c["reference_literal"]: c for c in document_sync.uncertain_reference_cases(db_session, project)}
    assert cases["A23-EFECO-MAT-E"]["existing_business_row"] is True and cases["A23-EFECO-MAT-E"]["key"].endswith(":p4:r0")
    assert cases["V-EL-MTG-PJW-ZZZ"]["existing_business_row"] is False
    assert db_session.query(ProjectSubmittal).filter_by(project_id=project.id, reference="A23-EFECO-MAT-E").count() == 1


def test_an_engineer_confirmed_drawing_under_an_uncertain_key_is_left_alone(db_session):
    project = _project_with(db_session, {"sheet.pdf": [_record("AB-SD-10", flags=["reference_uncertain"], category="drawings")]}, ep="R7E2")
    engineer = make_user(db_session, "engineer@test.local", RoleEnum.admin)
    drawing = ProjectShopDrawing(project_id=project.id, system_code="FAS", drawing_reference="AB-SD-10", confirmed_by_id=engineer.id,
                                 floor_keys=[], created_at=NOW, updated_at=NOW)
    db_session.add(drawing)
    db_session.commit()
    kept, held = document_sync.hold_uncertain_references(db_session, project, [_record("AB-SD-10", flags=["reference_uncertain"], category="drawings")])
    assert [r.reference for r in kept] == ["AB-SD-10"] and held == 0
    assert db_session.get(ProjectShopDrawing, drawing.id).drawing_reference == "AB-SD-10"


def test_generic_incomplete_references_never_create_business_keys(db_session):
    project = _project_with(db_session, {f"d{i}.pdf": [_record(ref, flags=[flag])] for i, (ref, flag) in enumerate(
        [("X-SD", "reference_incomplete"), ("-0012", "reference_uncertain"), ("AB-", "reference_incomplete")])}, ep="R7E3")
    records, _w = document_sync.log_records(db_session, project)
    assert records == []
    assert len(document_sync.uncertain_reference_cases(db_session, project)) == 3


# --- 2. a transmittal's listed submittal, on the application path ---------------------------------------------------------

ACK = """DOCUMENT TRANSMITTAL
To : M/s. Al Arabia EMW                     Date : 14/05/2026
Attn. : Mr. Hakem Ali                       AASS Ref. : TR/0127/26
Project ID : EP-29076
Subject : Material Submittal & sample Board / Fire Alarm & Voice Evacuation system
With reference to the above subject, please find attached herewith the following:
ITEM   Document No.              Description                                         No. of Copies
1 | 25H-S202-NCC-MAS-MEP- | Material Submittal / Fire Alarm, Voice Evacuation and | 2 No's
  | ELE-005-R3 | Fire Telephone System.
Received By:                       Signature:
"""


def test_a_transmittals_listed_submittal_is_not_filed_as_its_identity(client, db_session, tmp_path, ai):  # noqa: F811
    folder = tmp_path / "EP-29076"
    path = folder / "01- EP-29076 - Scan" / "EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf"
    path.parent.mkdir(parents=True)
    # a scan, as the real acknowledgement is: the text rendered to an image, no text layer
    source = pymupdf.open()
    page = source.new_page()
    for i, line in enumerate(ACK.splitlines()):
        page.insert_text((30, 40 + 14 * i), line, fontsize=8)
    pix = page.get_pixmap(dpi=200)
    doc = pymupdf.open()
    doc.new_page(width=page.rect.width, height=page.rect.height).insert_image(page.rect, pixmap=pix)
    doc.save(path)
    ai.answers = [_reading("25H-S202-NCC-MAS-MEP-ELE-005-R3", 3, title="Material Submittal / Fire Alarm, Voice Evacuation")] * 3
    project_id = _project(client, folder, ep="29076")
    result = _result(client, client.post(f"/projects/{project_id}/jobs/sync-documents"))
    assert result["processing_status"] == "succeeded"
    row = db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).one()
    db_session.refresh(row)
    assert row.role == "submittal_form", f"classified {row.role}: the form reader would not be asked"
    assert any(o.get("kind") == "transmittal" for o in row.extracted.get("observations") or []), row.extracted
    assert row.reference != "25H-S202-NCC-MAS-MEP-ELE-005-R3", ([o.get("items") for o in row.extracted.get("observations") or []], [(r.get("reference"), r.get("source")) for r in row.extracted["records"]], row.extracted.get("submission"))
    assert not [r for r in row.extracted["records"] if r.get("source") == "submittal form"]
    submission = row.extracted["submission"]
    assert submission["relationship"] == "transmits" and submission["listed_item"] == "25H-S202-NCC-MAS-MEP-ELE-005-R3"
    assert submission["listed_item_literal"].startswith("25H-S202-NCC-MAS-MEP-")
    assert submission["transmittal_reference"] == "TR/0127/26"
    logs = client.get(f"/projects/{project_id}/logs").json()
    from app.models import DocumentReading
    maps = [r.reading.get("warnings") for r in db_session.query(DocumentReading).filter(DocumentReading.kind == "submittal_map")]
    subs = [(x.reference, x.document_path) for x in db_session.query(ProjectSubmittal).filter(ProjectSubmittal.project_id == project_id)]
    assert "25H-S202-NCC-MAS-MEP-ELE-005-R3" not in [m["reference"] for m in logs["material_submittals"]], (len(maps), subs)
    # no loss on a second sync: the reading and the relationship stay
    _result(client, client.post(f"/projects/{project_id}/jobs/sync-documents"))
    db_session.refresh(row)
    assert row.extracted["submission"]["listed_item"] == "25H-S202-NCC-MAS-MEP-ELE-005-R3" and row.extracted.get("form")


def test_listed_item_matching_needs_the_transmittals_own_item_table():
    reading = {"is_submittal": True, "reference": "25H-S202-NCC-MAS-MEP-ELE-005-R3"}
    table = {"observations": [{"kind": "transmittal", "page": 1, "reference": None, "raw_reference": "_18/0127/26",
                               "items": [{"item": "1", "document_no": "25H-S202-NCC-MAS-MEP-"}]}]}
    got = document_sync.listed_by_transmittal(table, reading)
    assert got["listed_item"] == reading["reference"] and got["transmittal_reference_unread"] is True
    assert document_sync.listed_by_transmittal({"observations": []}, reading) is None
    short = {"observations": [{"kind": "transmittal", "items": [{"document_no": "25H-S"}]}]}
    assert document_sync.listed_by_transmittal(short, reading) is None, "a fragment shorter than 12 characters proves nothing"
