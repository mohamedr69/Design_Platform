"""M6 (ORCH-043): document attribution as a field of its own, conflict
records against engineer-confirmed rows, the engineer's confirmation
endpoint, the stage-record fields, and the offline shadow-evaluation
harness on a synthetic clone. No model is called; the harness runs on a
database built here, never on the platform's own."""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.models import (
    ActivityEvent, DocumentClassification, DocumentClassificationConflict, Project, ProjectDocument, ProjectShopDrawing,
    RoleEnum,
)
from app.services import document_attribution as da
from app.services import document_classification as dc

from .conftest import login, make_user
from .test_document_classification_v2 import _classifications, _sync, classification_on  # noqa: F401 -- fixture
from .test_document_sync import _pdf, _project, ai  # noqa: F401 -- fixture
from .test_file_sync_v2_processing import _processing_job, _states

settings = get_settings()
T, A = dc.DocumentType, da.Attribution
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "scripts"))
import m6_shadow_eval as harness  # noqa: E402

DRAWING = "Drawing title\nBBY006-GME-SDW-EL-FA-0001\nREV. 01\nGround Floor Layout"
IFC_DRAWING = "Drawing title\nBBY006-GME-DWG-EL-FA-0009\nREV. 00\nFirst Floor Fire Alarm Layout"
SPEC = "SECTION 28 31 00\nFIRE DETECTION AND ALARM\nPART 1 GENERAL\n"


def _row(path: str, *, role: str = "document", extracted: dict | None = None, state: str = "fresh"):
    return SimpleNamespace(id=1, relative_path=path, filename=path.rsplit("/", 1)[-1], role=role, extracted=extracted,
                           state=state, sha256="0" * 64, system_code=None)


def _hint(path: str, role: str = "document"):
    return dc.hint(path, path.rsplit("/", 1)[-1], role)


def _block(**fields) -> dict:
    return {"observations": [{"page": 1, "kind": "title_block", "version": "titleblock-2", **fields}]}


# --- 1. the attribution rules, one per basis -----------------------------------------------------------------


def test_the_intake_association_is_our_scope():
    row = _row("01- DRF/DRF.pdf", role="drf")
    result = da.attribute(row, dc.hint(row.relative_path, row.filename, "drf", intake_role="drf"), da.ProjectFacts("30001"))
    assert result.state is A.OUR_SCOPE and result.basis["rule"] == "intake" and result.conflict is None


def test_a_stored_title_block_originator_decides_ours_or_another_partys(monkeypatch):
    monkeypatch.setattr(settings, "company_name", "Al Arabia for Safety & Security LLC")
    monkeypatch.setattr(settings, "attribution_own_originators", "Al Arabia SSD; Juma Al Majid")
    facts = da.ProjectFacts("30002", ("FAS",), True)
    ours = _row("05- Drawings/FA/L01.pdf", extracted=_block(originator="AL ARABIA FOR SAFETY AND SECURITY L.L.C"))
    result = da.attribute(ours, _hint(ours.relative_path), facts)
    assert result.state is A.OUR_SCOPE and result.basis["rule"] == "originator" and result.basis["originator"]["own"] is True
    alias = _row("05- Drawings/FA/L02.pdf", extracted=_block(originator="Al Arabia SSD"))
    assert da.attribute(alias, _hint(alias.relative_path), facts).state is A.OUR_SCOPE
    # Another originator: related to a system of ours (the FA folder names FAS, which the project has) ...
    other = _row("09- Received/FA/L03.pdf", extracted=_block(originator="Kling Consult"))
    assert da.attribute(other, _hint(other.relative_path), facts).state is A.RELATED_EXTERNAL
    # ... or nothing ties it to one: reference only.
    loose = _row("09- Received/L04.pdf", extracted=_block(originator="Kling Consult"))
    result = da.attribute(loose, _hint(loose.relative_path), facts)
    assert result.state is A.REFERENCE_ONLY and result.basis["originator"]["own"] is False
    # Al Arabia Electro Mechanical is another company: never "ours" by a shared word.
    assert not da.is_own_originator("Al Arabia Electro Mechanical LLC", ("al arabia safety security",))


def test_a_title_block_discipline_that_is_not_ours_is_reference_only_and_ours_says_nothing_alone():
    other = _row("09- Other/A-101.pdf", extracted=_block(discipline="Architectural"))
    result = da.attribute(other, _hint(other.relative_path), da.ProjectFacts("30003"))
    assert result.state is A.REFERENCE_ONLY and result.basis["rule"] == "discipline"
    assert result.basis["title_block"] == {"discipline": "Architectural", "ours": False, "page": 1}
    ours = _row("09- Other/FA-101.pdf", extracted=_block(discipline="Fire Alarm"))
    assert da.attribute(ours, _hint(ours.relative_path), da.ProjectFacts("30003")).state is A.UNKNOWN


def test_a_folder_of_drawings_given_to_us_is_external_related_by_the_system():
    facts = da.ProjectFacts("30004", ("FAS", "ELS"), True)
    ifc = _row("00- IFC/FA/IFC-L01.pdf")
    result = da.attribute(ifc, _hint(ifc.relative_path), facts)
    assert result.state is A.RELATED_EXTERNAL and result.basis["rule"] == "folder" and result.basis["folder"]["given_to_us"]
    tender = _row("07- Tender/A-101.pdf")
    assert da.attribute(tender, _hint(tender.relative_path), facts).state is A.REFERENCE_ONLY
    # A system the rules name but the project does not have: reference only.
    pava = _row("00- IFC/PAVA/L01.pdf")
    result = da.attribute(pava, _hint(pava.relative_path), facts)
    assert result.state is A.REFERENCE_ONLY and result.basis["system"]["related"] is False


def test_a_shop_drawing_outside_those_folders_is_likely_ours_unless_the_drf_says_another_party_draws():
    drawing = _row("05- Drawings/L01.pdf")
    assessment = _hint(drawing.relative_path)
    assert assessment.primary_type is T.SHOP_DRAWING and assessment.stage is dc.Stage.HINT
    likely = da.attribute(drawing, assessment, da.ProjectFacts("30005", (), None))
    assert likely.state is A.LIKELY_OUR_SCOPE and likely.basis["rule"] == "type" and likely.basis["drawings_in_scope"] is None
    not_ours = da.attribute(drawing, assessment, da.ProjectFacts("30005", ("FAS",), False))
    assert not_ours.state is A.RELATED_EXTERNAL and not_ours.basis["drawings_in_scope"] is False
    # An ambiguous type is no claim of whose it is.
    ambiguous = dc.Assessment(T.SHOP_DRAWING, dc.Stage.AMBIGUOUS, dc.Strength.CONFLICTING, basis=dc.Basis.CONTENT)
    assert da.attribute(drawing, ambiguous, da.ProjectFacts("30005")).state is A.UNKNOWN


def test_nothing_to_go_on_is_unknown_and_disagreeing_evidence_is_kept_not_resolved(monkeypatch):
    monkeypatch.setattr(settings, "company_name", "Al Arabia for Safety & Security LLC")
    spec = _row("06- Specifications/28 31 00.pdf", role="spec")
    result = da.attribute(spec, _hint(spec.relative_path, "spec"), da.ProjectFacts("30006"))
    assert result.state is A.UNKNOWN and result.basis["rule"] == "no_evidence" and result.conflict is None
    # Our originator on a sheet filed among the IFC drawings: two sides; UNKNOWN, both claims kept.
    mixed = _row("00- IFC/FA/L01.pdf", extracted=_block(originator="Al Arabia for Safety & Security"))
    result = da.attribute(mixed, _hint(mixed.relative_path), da.ProjectFacts("30006", ("FAS",)))
    assert result.state is A.UNKNOWN and result.basis["rule"] == "conflict"
    assert {c["rule"] for c in result.conflict["claims"]} == {"originator", "folder"}
    # The intake association is authoritative: it stands, and the disagreement is still kept.
    drf = _row("07- Tender/DRF.pdf", role="drf")
    result = da.attribute(drf, dc.hint(drf.relative_path, drf.filename, "drf", intake_role="drf"), da.ProjectFacts("30006"))
    assert result.state is A.OUR_SCOPE and result.conflict is not None


def test_unknown_is_never_in_or_out_of_scope():
    assert da.in_scope(A.UNKNOWN) is None and da.scope_reading("UNKNOWN") == "unknown"
    assert da.in_scope(None) is None and da.in_scope("anything else") is None
    assert da.in_scope(A.LIKELY_OUR_SCOPE) is None and da.scope_reading(A.LIKELY_OUR_SCOPE) == "likely_in_scope"
    assert da.in_scope(A.OUR_SCOPE) is True and da.scope_reading(A.OUR_SCOPE) == "in_scope"
    assert da.in_scope(A.RELATED_EXTERNAL) is False and da.in_scope(A.REFERENCE_ONLY) is False
    # The harness never counts an UNKNOWN as ours or as not ours.
    assert harness._side("UNKNOWN") == "unknown"
    items = [{"cohort": "x", "truth_type": None, "truth_system": None, "truth_attribution": "RELATED_EXTERNAL", "joined": True,
              "pred": {"type": "OTHER", "stage": "hint", "system": None, "attribution": "UNKNOWN"}}]
    m = harness.metrics(items)
    assert m["false_our_scope_rate"] == {"numerator": 0, "denominator": 0, "value": None}
    assert m["attribution_side_accuracy"]["numerator"] == 0 and m["attribution_unknown"]["numerator"] == 1


def test_attribution_never_fails_the_classification_and_the_processing(client, db_session, tmp_path, ai, classification_on,
                                                                       monkeypatch, caplog):
    def broken(*_args, **_kwargs):
        raise RuntimeError("attribution exploded")

    monkeypatch.setattr(da, "attribute", broken)
    caplog.set_level(logging.WARNING, logger="app.services.document_attribution")
    folder = tmp_path / "EP-30940"
    _pdf(folder / "05- Drawings" / "L01.pdf", DRAWING)
    project_id = _project(client, folder, "30940")
    _sync(client, project_id)
    assert _states(db_session, project_id) == {"fresh": 1}
    assert _processing_job(db_session, project_id).result["processed"] == 1
    entry = _classifications(db_session, project_id)["05- Drawings/L01.pdf"]
    assert entry.source == "assessment" and entry.primary_type == "SHOP_DRAWING", "the classification was still written"
    assert entry.attribution == "UNKNOWN" and entry.attribution_basis["rule"] == "error"
    assert "attribution exploded" in entry.attribution_basis["error"] and "Attribution failed" in caplog.text


# --- 2. persisted beside the classification: attribution and the stage record ---------------------------------


def _folder(tmp_path, ep: str) -> Path:
    folder = tmp_path / f"EP-{ep}"
    _pdf(folder / "05- Drawings" / "L01.pdf", DRAWING)
    _pdf(folder / "00- IFC" / "FA" / "IFC-L01.pdf", IFC_DRAWING)
    _pdf(folder / "06- Specifications" / "28 31 00 Fire Alarm.pdf", SPEC)
    return folder


def test_the_attribution_and_the_stage_record_are_stored_and_listed(client, db_session, tmp_path, ai, classification_on):
    project_id = _project(client, _folder(tmp_path, "30941"), "30941")
    _sync(client, project_id)
    c = _classifications(db_session, project_id)
    drawing, ifc, spec = c["05- Drawings/L01.pdf"], c["00- IFC/FA/IFC-L01.pdf"], c["06- Specifications/28 31 00 Fire Alarm.pdf"]
    assert drawing.primary_type == "SHOP_DRAWING" and drawing.attribution == "LIKELY_OUR_SCOPE"
    assert ifc.primary_type == "IFC_DRAWING" and ifc.attribution == "RELATED_EXTERNAL" and ifc.attribution_basis["rule"] == "folder"
    assert spec.attribution == "UNKNOWN" and spec.attribution_basis["rule"] == "no_evidence"
    for entry in c.values():
        # The four stage strings are untouched; attribution is a field of its own.
        assert entry.stage in ("hint", "supported", "ambiguous", "unknown") and entry.stage != entry.attribution
        assert entry.attribution_version == da.ATTRIBUTION_VERSION and entry.rules_version == dc.RULES_VERSION
        assert entry.stage_status == "complete" and len(entry.input_fingerprint) == 64
        assert entry.model is None and entry.prompt_version is None and entry.page_chars is None
    listing = {r["path"]: r["classification"] for r in client.get(f"/projects/{project_id}/documents/classification").json()}
    out = listing["00- IFC/FA/IFC-L01.pdf"]
    assert out["attribution"] == "RELATED_EXTERNAL" and out["scope_reading"] == "out_of_scope" and out["conflicts"] == []
    assert out["stage_record"]["stage_status"] == "complete" and out["stage_record"]["rules_version"] == dc.RULES_VERSION
    assert listing["06- Specifications/28 31 00 Fire Alarm.pdf"]["scope_reading"] == "unknown"
    metrics = client.get(f"/projects/{project_id}/documents/classification/metrics").json()
    assert metrics["by_attribution"] == {"LIKELY_OUR_SCOPE": 1, "RELATED_EXTERNAL": 1, "UNKNOWN": 1}
    # Nothing the attribution says made a domain record: the IFC drawing is not a shop drawing.
    drawn = {d.drawing_reference for d in db_session.query(ProjectShopDrawing).filter(ProjectShopDrawing.project_id == project_id)}
    assert "BBY006-GME-DWG-EL-FA-0009" not in drawn


def test_a_producing_stage_fills_its_stage_record_slots_and_the_backfill_its_job(client, db_session, tmp_path, ai,
                                                                                 classification_on):
    project_id = _project(client, _folder(tmp_path, "30942"), "30942")
    _sync(client, project_id)
    project = db_session.get(Project, project_id)
    row = db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id,
                                                   ProjectDocument.relative_path == "05- Drawings/L01.pdf").one()
    answer = dc.Assessment(T.SHOP_DRAWING, dc.Stage.SUPPORTED, dc.Strength.MODERATE, basis=dc.Basis.CONTENT,
                           source_state=row.state, reason="a model's reading")
    entry = dc.record(db_session, project, row, answer, source="ai",
                      stage_record={"model": "scripted-model", "prompt_version": "p-1", "page_chars": 2500,
                                    "producing_job_id": 77, "stage_status": "partial", "ignored": "x"})
    db_session.commit()
    db_session.expire_all()
    stored = db_session.get(DocumentClassification, entry.id)
    assert (stored.model, stored.prompt_version, stored.page_chars, stored.producing_job_id, stored.stage_status) == \
        ("scripted-model", "p-1", 2500, 77, "partial")
    assert stored.superseded_at is None and stored.attribution == "LIKELY_OUR_SCOPE"
    # A rules change: the backfill re-assesses from stored data and records the job that produced each row.
    stale = _classifications(db_session, project_id)["06- Specifications/28 31 00 Fire Alarm.pdf"]
    stale.rules_version = "classify-earlier"
    db_session.commit()
    job = client.post(f"/projects/{project_id}/jobs/classify-documents").json()
    assert job["status"] == "succeeded" and job["result"]["assessed"] >= 1
    refreshed = _classifications(db_session, project_id)["06- Specifications/28 31 00 Fire Alarm.pdf"]
    assert refreshed.source == "backfill" and refreshed.producing_job_id == job["id"] and refreshed.stage_status == "complete"


def test_freshness_keeps_its_semantics_under_a_rules_bump_and_ignores_the_attribution_version(client, db_session, tmp_path,
                                                                                             ai, classification_on, monkeypatch):
    project_id = _project(client, _folder(tmp_path, "30943"), "30943")
    _sync(client, project_id)
    project = db_session.get(Project, project_id)
    rows = {r.relative_path: r for r in db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)}
    row = rows["05- Drawings/L01.pdf"]
    entry = _classifications(db_session, project_id)["05- Drawings/L01.pdf"]
    fingerprint = dc.context_fingerprint(row, project)
    assert dc.freshness(entry, row, fingerprint) == dc.CURRENT
    # Another attribution version, other project facts, another stored attribution: freshness unmoved.
    monkeypatch.setattr(da, "ATTRIBUTION_VERSION", "attribution-next")
    entry.attribution, entry.attribution_version = "OUR_SCOPE", "attribution-earlier"
    assert dc.freshness(entry, row, dc.context_fingerprint(row, project)) == dc.CURRENT
    assert dc.context_fingerprint(row, project) == fingerprint, "the context fingerprint does not carry the attribution"
    db_session.rollback()
    # A rules bump still marks every stored row rules_changed, and the backfill re-assesses them.
    monkeypatch.setattr(dc, "RULES_VERSION", "classify-next")
    entry = _classifications(db_session, project_id)["05- Drawings/L01.pdf"]
    assert dc.freshness(entry, row, dc.context_fingerprint(row, project)) == dc.RULES_CHANGED
    result = dc.backfill(db_session, project)
    assert result["assessed"] == 3 and result["skipped"] == 0
    assert all(e.rules_version == "classify-next" for e in _classifications(db_session, project_id).values())


# --- 3. the engineer's confirmation, conflicts, supersession ----------------------------------------------------


def _engineer(client, db, role=RoleEnum.fire_alarm_design_engineer, email="engineer@example.com"):
    user = make_user(db, email, role)
    assert login(client, email).status_code == 200
    return user


def _confirm(client, project_id, document_id, **body):
    payload = {"primary_type": "IFC_DRAWING", "system_code": "FAS", "attribution": "RELATED_EXTERNAL",
               "reason": "the consultant's IFC sheet, issued to us", **body}
    return client.post(f"/projects/{project_id}/documents/{document_id}/classification/confirm", json=payload)


def _doc(db, project_id, path) -> ProjectDocument:
    return db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id, ProjectDocument.relative_path == path).one()


@pytest.mark.parametrize("role", [RoleEnum.admin, RoleEnum.viewer, RoleEnum.draftsman, RoleEnum.fire_alarm_estimation_engineer])
def test_only_engineers_confirm_and_admin_gains_no_engineering_authority(client, db_session, tmp_path, ai, classification_on, role):
    project_id = _project(client, _folder(tmp_path, "30944"), "30944")
    _sync(client, project_id)
    document = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    if role is not RoleEnum.admin:
        _engineer(client, db_session, role, email=f"{role.value}@example.com")
    response = _confirm(client, project_id, document.id)
    assert response.status_code == 403, response.text
    assert db_session.query(DocumentClassification).filter(DocumentClassification.engineer_confirmed.is_(True)).count() == 0
    assert db_session.query(ActivityEvent).filter(ActivityEvent.action == "classification.confirmed").count() == 0


def test_a_confirmation_is_refused_when_classification_is_off_or_the_request_is_not_a_confirmation(client, db_session, tmp_path,
                                                                                                   ai, classification_on,
                                                                                                   monkeypatch):
    project_id = _project(client, _folder(tmp_path, "30945"), "30945")
    _sync(client, project_id)
    document = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    _engineer(client, db_session)
    assert _confirm(client, project_id, document.id, primary_type="UNKNOWN").status_code == 422
    assert _confirm(client, project_id, document.id, primary_type="BLUEPRINT").status_code == 422
    assert _confirm(client, project_id, document.id, attribution="MAYBE_OURS").status_code == 422
    assert _confirm(client, project_id, document.id, reason="   ").status_code == 422
    assert _confirm(client, project_id, 999999).status_code == 404
    monkeypatch.setattr(settings, "document_classification_v2", False)
    assert _confirm(client, project_id, document.id).status_code == 409
    assert db_session.query(DocumentClassification).filter(DocumentClassification.engineer_confirmed.is_(True)).count() == 0


def test_an_engineer_confirms_with_an_audit_event_and_no_automated_run_supersedes_it(client, db_session, tmp_path, ai,
                                                                                    classification_on):
    project_id = _project(client, _folder(tmp_path, "30946"), "30946")
    _sync(client, project_id)
    document = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    automatic = _classifications(db_session, project_id)["05- Drawings/L01.pdf"]
    assert automatic.primary_type == "SHOP_DRAWING" and automatic.attribution == "LIKELY_OUR_SCOPE"
    engineer = _engineer(client, db_session)

    response = _confirm(client, project_id, document.id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["engineer_confirmed"] is True and body["source"] == "engineer" and body["primary_type"] == "IFC_DRAWING"
    assert body["attribution"] == "RELATED_EXTERNAL" and body["confirmed_by_id"] == engineer.id and body["basis"] == "engineer"
    assert body["stage"] == "supported", "a confirmation is no new stage string"
    db_session.expire_all()
    confirmed = db_session.get(DocumentClassification, body["id"])
    assert confirmed.superseded_at is None and db_session.get(DocumentClassification, automatic.id).superseded_at is not None
    event = db_session.query(ActivityEvent).filter(ActivityEvent.action == "classification.confirmed").one()
    assert event.user_id == engineer.id and event.entity_type == "document_classification" and event.entity_id == confirmed.id
    assert event.detail["before"]["primary_type"] == "SHOP_DRAWING" and event.detail["after"]["attribution"] == "RELATED_EXTERNAL"
    assert event.detail["reason"] == "the consultant's IFC sheet, issued to us" and event.project_id == project_id
    frozen = (confirmed.primary_type, confirmed.system_code, confirmed.attribution, confirmed.reason, confirmed.engineer_confirmed)

    # Every automated writer runs again: the assessment, the backfill (rules changed), the sync's hint.
    project = db_session.get(Project, project_id)
    row = db_session.get(ProjectDocument, document.id)
    assert dc.assess_row(db_session, project, row) is not None
    db_session.commit()
    assert dc.assess_row(db_session, project, row) is not None, "seen again: history row, the same conflict counted"
    db_session.commit()
    assert dc.backfill(db_session, project)["assessed"] >= 0
    assert dc.hint_rows(db_session, project, [row]) == 1
    db_session.commit()

    db_session.expire_all()
    current = _classifications(db_session, project_id)["05- Drawings/L01.pdf"]
    assert current.id == confirmed.id, "nothing automatic superseded the engineer's row"
    assert (current.primary_type, current.system_code, current.attribution, current.reason, current.engineer_confirmed) == frozen
    later = (db_session.query(DocumentClassification).filter(DocumentClassification.document_id == document.id,
                                                             DocumentClassification.id > confirmed.id).all())
    assert later and all(e.superseded_at is not None and not e.engineer_confirmed for e in later), "history only"
    conflicts = (db_session.query(DocumentClassificationConflict)
                 .filter(DocumentClassificationConflict.confirmed_classification_id == confirmed.id).all())
    by_field = {(c.field, c.source): c for c in conflicts}
    assessed = by_field[("primary_type", "assessment")]
    assert (assessed.confirmed_value, assessed.proposed_value, assessed.version) == ("IFC_DRAWING", "SHOP_DRAWING", dc.RULES_VERSION)
    assert assessed.seen_count == 2 and assessed.proposed_classification_id in {e.id for e in later}
    assert by_field[("attribution", "assessment")].proposed_value == "LIKELY_OUR_SCOPE"
    assert by_field[("attribution", "assessment")].version == da.ATTRIBUTION_VERSION
    assert ("primary_type", "hint") in by_field
    assert not any(c.field == "system_code" and c.proposed_value is None for c in conflicts), "no evidence is no disagreement"
    # The inspector sees the conflicts against the current confirmed row, and a reason to look.
    listing = {r["path"]: r["classification"] for r in client.get(f"/projects/{project_id}/documents/classification").json()}
    shown = listing["05- Drawings/L01.pdf"]
    assert shown["engineer_confirmed"] is True and len(shown["conflicts"]) == len(conflicts)
    assert shown["needs_review"] and any("disagree with the engineer" in r for r in shown["review_reasons"])


def test_a_later_confirmation_supersedes_the_earlier_one_and_agreement_is_no_conflict(client, db_session, tmp_path, ai,
                                                                                     classification_on):
    project_id = _project(client, _folder(tmp_path, "30947"), "30947")
    _sync(client, project_id)
    document = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    _engineer(client, db_session, RoleEnum.design_manager, email="manager@example.com")
    first = _confirm(client, project_id, document.id).json()
    second = _confirm(client, project_id, document.id, primary_type="SHOP_DRAWING", attribution="OUR_SCOPE", system_code=None,
                      reason="our shop drawing after all").json()
    db_session.expire_all()
    assert db_session.get(DocumentClassification, first["id"]).superseded_at is not None, "the earlier confirmation is history"
    assert second["engineer_confirmed"] and second["system_code"] is None and second["attribution"] == "OUR_SCOPE"
    # The rules now agree on the type (no conflict); their LIKELY_OUR_SCOPE is a different attribution.
    project = db_session.get(Project, project_id)
    dc.assess_row(db_session, project, db_session.get(ProjectDocument, document.id))
    db_session.commit()
    conflicts = db_session.query(DocumentClassificationConflict).filter(
        DocumentClassificationConflict.confirmed_classification_id == second["id"]).all()
    # The engineer said no system; the records name FAS: that disagreement is recorded too.
    assert {c.field for c in conflicts} == {"attribution", "system_code"}
    assert _classifications(db_session, project_id)["05- Drawings/L01.pdf"].id == second["id"]


def test_the_confirmation_and_its_audit_event_are_one_transaction(client, db_session, tmp_path, ai, classification_on, monkeypatch):
    from app.services import activity

    project_id = _project(client, _folder(tmp_path, "30948"), "30948")
    _sync(client, project_id)
    project = db_session.get(Project, project_id)
    row = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    engineer = make_user(db_session, "engineer2@example.com", RoleEnum.elv_design_engineer)

    def refused(*_args, **_kwargs):
        raise RuntimeError("the audit write failed")

    def confirmed_rows() -> int:
        return db_session.query(DocumentClassification).filter(DocumentClassification.engineer_confirmed.is_(True)).count()

    def events() -> int:
        return db_session.query(ActivityEvent).filter(ActivityEvent.action == "classification.confirmed").count()

    # The audit write fails: no confirmation.
    with monkeypatch.context() as patch:
        patch.setattr(activity, "record", refused)
        with pytest.raises(RuntimeError):
            dc.confirm(db_session, project, row, engineer, primary_type="IFC_DRAWING", system_code="FAS",
                       attribution="RELATED_EXTERNAL", reason="test")
        db_session.rollback()
    assert confirmed_rows() == 0 and events() == 0
    # The classification write fails after the audit event: no event either.
    original = dc.record

    def record_then_fail(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("the transaction failed after the confirmation was written")

    with monkeypatch.context() as patch:
        patch.setattr(dc, "record", record_then_fail)
        with pytest.raises(RuntimeError):
            dc.confirm(db_session, project, row, engineer, primary_type="IFC_DRAWING", system_code="FAS",
                       attribution="RELATED_EXTERNAL", reason="test")
        db_session.rollback()
    assert confirmed_rows() == 0 and events() == 0
    assert _classifications(db_session, project_id)["05- Drawings/L01.pdf"].source in ("hint", "assessment")
    # Both succeed: both are there.
    dc.confirm(db_session, project, row, engineer, primary_type="IFC_DRAWING", system_code="FAS",
               attribution="RELATED_EXTERNAL", reason="test")
    db_session.commit()
    assert confirmed_rows() == 1 and events() == 1


def test_a_project_with_confirmations_and_conflicts_can_still_be_deleted(client, db_session, tmp_path, ai, classification_on):
    from app.services import project_deletion

    project_id = _project(client, _folder(tmp_path, "30949"), "30949")
    _sync(client, project_id)
    document = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    _engineer(client, db_session, RoleEnum.design_manager, email="manager2@example.com")
    assert _confirm(client, project_id, document.id).status_code == 200
    project = db_session.get(Project, project_id)
    dc.assess_row(db_session, project, db_session.get(ProjectDocument, document.id))
    db_session.commit()
    assert db_session.query(DocumentClassificationConflict).count() >= 1
    project_deletion.delete_project(db_session, project)
    db_session.commit()
    assert db_session.query(DocumentClassificationConflict).count() == 0
    assert db_session.query(DocumentClassification).filter(DocumentClassification.project_id == project_id).count() == 0


# --- 4. the offline shadow-evaluation harness on a synthetic clone ---------------------------------------------


def _clone(path: Path, stored: bool = True) -> Path:
    """A synthetic platform database: one project, five documents (not
    processed: their answers are the rules' hints), and, for the stored
    arm, a current classification row per document."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.database import Base
    from app.models import User

    engine = create_engine(f"sqlite:///{path.as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        user = User(email="clone@example.com", full_name="clone", hashed_password="x", role=RoleEnum.viewer)
        s.add(user)
        s.flush()
        project = Project(ep_number="90001", project_name="Synthetic", created_by_id=user.id)
        s.add(project)
        s.flush()
        docs = [("05- Drawings/L01.pdf", "document", "a1"), ("00- IFC/FA/IFC-L02.pdf", "document", "a2"),
                ("06- Specifications/28 31 00 Fire Alarm.pdf", "spec", "a3"), ("02- MS/FA/form.pdf", "submittal_form", "a4"),
                ("07- Tender/A-101.pdf", "document", "a5")]
        rows = []
        for relative, role, sha in docs:
            row = ProjectDocument(project_id=project.id, role=role, path=f"C:/x/{relative}", relative_path=relative,
                                  filename=relative.rsplit("/", 1)[-1], sha256=sha * 32, state="fresh", extracted=None)
            s.add(row)
            rows.append(row)
        s.add(ProjectDocument(project_id=project.id, role="document", path="C:/x/gone.pdf", relative_path="gone.pdf",
                              filename="gone.pdf", sha256="a6" * 32, state="removed"))
        s.flush()
        if stored:
            answers = [("SHOP_DRAWING", "supported", "ELS", "OUR_SCOPE"), ("SHOP_DRAWING", "supported", "FAS", "OUR_SCOPE"),
                       ("SPECIFICATION", "supported", None, "UNKNOWN"), ("TRANSMITTAL", "hint", "FAS", "LIKELY_OUR_SCOPE"),
                       ("OTHER", "supported", None, "REFERENCE_ONLY")]
            for row, (kind, stage, system, attribution) in zip(rows, answers):
                s.add(DocumentClassification(project_id=project.id, document_id=row.id, content_sha256=row.sha256,
                                             context_fingerprint="f" * 64, rules_version="r", stage=stage, primary_type=kind,
                                             component_types=[], evidence_strength="moderate", evidence=[], evidence_sources=[],
                                             reason="", system_code=system, source="assessment", assessment={},
                                             created_at=utc_now(), attribution=attribution))
        s.commit()
    engine.dispose()
    return path


def _labels() -> dict:
    def doc(sha, cohort, kind, system, originator, path):
        return {"doc": f"EP-90001/{path}", "sha256": sha * 32, "ep": "90001", "cohort": cohort,
                "labels": {"kind": kind, "system": system, "originator": originator}}

    return {"at_utc": "2026-10-08T00:00:00+00:00", "labeller": "synthetic", "documents": [
        doc("a1", "regression", "drawing sheet (shop drawing, no cover)", "FAS", "Al Arabia Safety & Security", "05- Drawings\\L01.pdf"),
        doc("a2", "regression", "consultant IFC drawing sheet (fire alarm)", "FAS", "Kling Consult; wasl", "00- IFC\\FA\\IFC-L02.pdf"),
        doc("a3", "exploration", "specification section (tender, 14 pages)", "other (whole-project specification; non-FAS control)",
            "unknown", "06- Specifications\\28 31 00 Fire Alarm.pdf"),
        doc("a4", "exploration", "material submittal cover (Materials Submittal Form)", "FAS", "Italtech Contracting LLC", "02- MS\\FA\\form.pdf"),
        doc("a5", "holdout", "consultant tender drawing sheet (architectural)", "other (architectural; non-FAS)", "Kling Consult; BSBG",
            "07- Tender\\A-101.pdf"),
        doc("a6", "holdout", "transmittal (document transmittal, scanned, signed as received)", "FAS", "Al Arabia", "gone.pdf"),
    ]}


def _rate(n, d):
    return {"numerator": n, "denominator": d, "value": round(n / d, 4) if d else None}


def test_the_kind_map_is_reviewed_data_covering_every_labelled_kind_with_the_unmapped_listed():
    kind_map = harness.load_kind_map()
    labels_path = harness.DEFAULT_LABELS
    labels = json.loads(labels_path.read_text(encoding="utf-8"))["documents"]
    assert kind_map["_about"]["labels_sha256"] == hashlib.sha256(labels_path.read_bytes()).hexdigest()
    assert {d["labels"].get("kind") for d in labels} == set(kind_map["kinds"])
    assert {d["labels"].get("system") for d in labels} == set(kind_map["systems"])
    assert sorted(k for k, v in kind_map["kinds"].items() if v["type"] is None) == kind_map["unmapped"]
    assert all(v["why"] for v in kind_map["kinds"].values())
    coverage = harness.kind_map_coverage(kind_map, labels)
    assert (coverage["kinds"], coverage["mapped_kinds"], coverage["unmapped_kinds"]) == (241, 175, 66)
    assert (coverage["documents"], coverage["mapped_documents"]) == (380, 292)
    assert {c: sum(1 for d in labels if d["cohort"] == c) for c in harness.COHORTS} == {"regression": 80, "exploration": 192, "holdout": 108}


def test_the_derived_attribution_truth_is_provisional_and_rule_bound():
    assert harness.derive_attribution("Al Arabia (to M/s NAFFCO)", "FAS")[0] == "OUR_SCOPE"
    assert harness.derive_attribution("Granada Europe Construction; Al Arabia Safety & Security", "FAS")[0] == "OUR_SCOPE"
    assert harness.derive_attribution("MOHAMMED AMEER, JUMA AL MAJID", "PAVA")[0] == "OUR_SCOPE"
    # Another company of a similar name, a stamp, a recipient: not the originator.
    assert harness.derive_attribution("Al Arabia Electro Mechanical; Naresco; LACASA", "FAS")[0] == "RELATED_EXTERNAL"
    assert harness.derive_attribution("BK Gulf LLC; Dutco Construction; Al Arabia round stamp", "PAVA")[0] == "RELATED_EXTERNAL"
    assert harness.derive_attribution("SMET (Sales) to Al Arabia For Safety & Security LLC", "ELS")[0] == "RELATED_EXTERNAL"
    assert harness.derive_attribution("Kling Consult; BSBG", "NONE")[0] == "REFERENCE_ONLY"
    assert harness.derive_attribution("unknown (Al Arabia correspondence)", "FAS")[0] is None
    assert harness.derive_attribution("Kling Consult", None)[0] is None


def test_the_harness_on_a_synthetic_clone_stored_arm(tmp_path):
    clone = _clone(tmp_path / "clone.db")
    before = hashlib.sha256(clone.read_bytes()).hexdigest()
    engine = harness.open_clone(clone, live_url="sqlite:///" + (tmp_path / "live.db").as_posix())
    report = harness.evaluate(engine, _labels(), harness.load_kind_map(), arm="stored")
    engine.dispose()
    assert hashlib.sha256(clone.read_bytes()).hexdigest() == before, "the clone is never written"
    m = report["all"]
    assert (m["labelled"], m["joined"], m["answered"], m["type_truth"], m["type_unmapped"]) == (6, 5, 5, 4, 1)
    assert m["type_accuracy"] == _rate(2, 4)
    assert m["per_type"]["SHOP_DRAWING"] == {"true_positive": 1, "precision": _rate(1, 2), "recall": _rate(1, 1)}
    assert m["per_type"]["IFC_DRAWING"] == {"true_positive": 0, "precision": _rate(0, 0), "recall": _rate(0, 1)}
    assert m["per_type"]["SPECIFICATION"] == {"true_positive": 1, "precision": _rate(1, 1), "recall": _rate(1, 1)}
    assert m["per_type"]["MATERIAL_SUBMITTAL"]["recall"] == _rate(0, 1)
    assert m["per_type"]["TRANSMITTAL"]["precision"] == _rate(0, 1)
    assert m["system_accuracy"] == _rate(4, 5) and m["system_excluded"] == 0
    assert m["attribution_accuracy"] == _rate(2, 4) and m["attribution_accuracy_answered"] == _rate(2, 4)
    assert m["attribution_side_accuracy"] == _rate(2, 4) and m["attribution_unknown"] == _rate(0, 4)
    assert m["false_supported_rate"] == _rate(1, 3)
    assert m["false_our_scope_rate"] == _rate(1, 2) and m["false_our_scope_rate_incl_likely"] == _rate(2, 3)
    assert m["attribution_confusion"] == {"OUR_SCOPE": {"OUR_SCOPE": 1}, "RELATED_EXTERNAL": {"OUR_SCOPE": 1, "LIKELY_OUR_SCOPE": 1},
                                          "REFERENCE_ONLY": {"REFERENCE_ONLY": 1}}
    regression, exploration, holdout = (report["cohorts"][c] for c in harness.COHORTS)
    assert (regression["labelled"], regression["joined"]) == (2, 2) and regression["false_supported_rate"] == _rate(1, 2)
    assert regression["false_our_scope_rate"] == _rate(1, 2) and regression["type_accuracy"] == _rate(1, 2)
    assert (exploration["labelled"], exploration["type_accuracy"]) == (2, _rate(1, 2))
    assert (holdout["labelled"], holdout["joined"], holdout["type_truth"], holdout["type_unmapped"]) == (2, 1, 0, 1)
    assert report["kind_map"]["documents"] == 6 and report["kind_map"]["mapped_documents"] == 5
    assert report["provisional"] and report["truth_version"] == harness.TRUTH_VERSION


def test_the_harness_rules_arm_reruns_this_checkouts_rules_on_the_stored_reading(tmp_path):
    engine = harness.open_clone(_clone(tmp_path / "clone.db", stored=False), live_url="sqlite:///:memory:")
    report = harness.evaluate(engine, _labels(), harness.load_kind_map(), arm="rules")
    engine.dispose()
    m = report["all"]
    assert m["type_accuracy"] == _rate(4, 4) and m["false_supported_rate"] == _rate(0, 0)
    assert m["system_accuracy"] == _rate(4, 5)
    assert m["attribution_accuracy"] == _rate(2, 4) and m["attribution_accuracy_answered"] == _rate(2, 3)
    assert m["attribution_side_accuracy"] == _rate(3, 4) and m["attribution_unknown"] == _rate(1, 4)
    assert m["false_our_scope_rate"] == _rate(0, 0) and m["false_our_scope_rate_incl_likely"] == _rate(0, 1)


def test_the_harness_ai_arm_asks_only_a_scripted_provider_and_only_for_weak_answers(tmp_path):
    from app.ai.provider import NullProvider, RecordingProvider

    engine = harness.open_clone(_clone(tmp_path / "clone.db", stored=False), live_url="sqlite:///:memory:")
    with pytest.raises(RuntimeError, match="scripted RecordingProvider"):
        harness.evaluate(engine, _labels(), harness.load_kind_map(), arm="ai", provider=NullProvider())
    provider = RecordingProvider([
        {"primary_type": "SHOP_DRAWING", "system_code": "FAS", "confidence": "high"},
        {"primary_type": "SHOP_DRAWING", "confidence": "medium"},
        {"primary_type": "SPECIFICATION"},
        {"primary_type": "OTHER", "confidence": "low"},
        {"primary_type": "IFC_DRAWING", "confidence": "low"},
    ])
    report = harness.evaluate(engine, _labels(), harness.load_kind_map(), arm="ai", provider=provider)
    engine.dispose()
    assert provider.calls == 5 and report["ai"]["asked"] == 5 and report["ai"]["answered"] == 4 and report["ai"]["failed"] == 1
    assert all(r.task == "m6_shadow_classify" for r in provider.requests)
    m = report["all"]
    assert m["type_accuracy"] == _rate(2, 4) and m["false_supported_rate"] == _rate(1, 2)
    assert m["system_accuracy"] == _rate(5, 5)
    assert m["attribution_accuracy"] == _rate(2, 4) and m["false_our_scope_rate_incl_likely"] == _rate(0, 1)


def test_the_harness_refuses_the_platforms_own_database_and_a_missing_clone(tmp_path):
    live = _clone(tmp_path / "live.db", stored=False)
    with pytest.raises(harness.LiveDatabaseRefused):
        harness.open_clone(live, live_url=f"sqlite:///{live.as_posix()}")
    with pytest.raises(FileNotFoundError):
        harness.open_clone(tmp_path / "missing.db", live_url="sqlite:///:memory:")
    engine = harness.open_clone(live, live_url="sqlite:///:memory:")
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    with pytest.raises(OperationalError), engine.connect() as conn:
        conn.execute(text("DELETE FROM project_documents"))
    engine.dispose()
    with pytest.raises(SystemExit):
        harness.main(["--database", str(live), "--arm", "ai"])
