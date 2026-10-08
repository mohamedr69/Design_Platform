"""ORCH-049: the M6 merge onto the owner's classification work, and the
ORCH-048 conditions and review findings closed with it.

  C1          the model's pass fills the M6 stage-record slots, so a conflict
              it raises against an engineer's confirmation carries the prompt
              version (not the rules version)
  C2  (V-01)  an IFC_DRAWING type outside the folders of drawings given to us
              (a model's answer, for instance) never claims OUR_SCOPE
  C3  (V-02)  the harness's AI arm is review-only like the live pass (A-15
              item 1): a model answer is never SUPPORTED; the report has a
              per-source breakdown
  V-03        a weaker claim on the same side as the engineer's attribution is
              no conflict; an opposite-side claim is
  V-04        after a rules bump a confirmed row is re-marked once, not on
              every backfill
  V-07        a changed input fingerprint marks the attribution stale, and the
              backfill re-attributes it once

No model is called: the live pass runs against app.ai.provider.RecordingProvider,
the harness on a synthetic clone built here."""

from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest

from app.ai.provider import RecordingProvider
from app.core.config import get_settings
from app.models import DocumentClassification, DocumentClassificationConflict, Project, ProjectDocument, RoleEnum, User
from app.services import document_attribution as da
from app.services import document_classification as dc
from app.services import document_classification_ai as AI

from .test_document_classification_ai import DATASHEET_TEXT, _answer, recording, switched_on  # noqa: F401 -- fixtures
from .test_document_classification_ai import _doc as _ai_doc
from .test_document_classification_ai import _project as _ai_project
from .test_document_classification_v2 import _classifications, _sync, classification_on  # noqa: F401 -- fixture
from .test_document_sync import _project, ai  # noqa: F401 -- fixture
from .test_m6_attribution import _clone, _confirm, _doc, _engineer, _folder, _labels, _rate, _row, harness

settings = get_settings()
T, A = dc.DocumentType, da.Attribution


def _ctx(job_id: int):
    return SimpleNamespace(job_id=job_id, progress=lambda *_a, **_k: None, check=lambda: None)


def _first_user(db) -> User:
    return db.query(User).order_by(User.id).first()


# --- C1: the model's pass through the stage-record slots ---------------------------------------------------------


def test_the_ai_pass_fills_the_stage_record_and_its_conflicts_carry_the_prompt_version(db_session, tmp_path, switched_on,
                                                                                       recording):
    project = _ai_project(db_session, tmp_path, "94101")
    row = _ai_doc(db_session, project, tmp_path, "05- Misc/scan 101.pdf", DATASHEET_TEXT, "sha-c1")
    rules_entry = dc.current(db_session, row)
    assert rules_entry.source == "assessment" and rules_entry.stage in AI.WEAK_STAGES
    recording.answers = [_answer(("DATASHEET", "FAS", "fire_alarm", "high", "'TECHNICAL DATA SHEET'"))]
    result = AI.run(db_session, project, ctx=_ctx(4242))
    assert result["written"] == 1
    db_session.expire_all()
    entry = dc.current(db_session, row)
    assert entry.source == "ai" and entry.stage == "hint", "review-only: the owner's rule stands"
    assert (entry.prompt_version, entry.page_chars, entry.producing_job_id, entry.stage_status) == (
        AI.PROMPT_VERSION, settings.document_classification_ai_page_chars, 4242, "complete")
    assert entry.model is not None and entry.model == entry.assessment["ai"]["model"]
    # F-02 stands: the provenance went in with the row (record(extra=...)), and the review reason is kept.
    assert entry.assessment["ai"]["prompt_version"] == AI.PROMPT_VERSION and entry.assessment["rules"]["stage"] in AI.WEAK_STAGES
    assert dc.AI_REVIEW_REASON in dc.review_reasons(entry, row, dc.CURRENT)

    # An engineer confirms another reading; the model's answer comes again: history, and conflicts under the prompt version.
    dc.confirm(db_session, project, row, _first_user(db_session), primary_type="CERTIFICATE", system_code="ELS",
               attribution="RELATED_EXTERNAL", reason="the engineer read the sheet")
    db_session.commit()
    confirmed = dc.current(db_session, row)
    verdict = {"primary_type": "DATASHEET", "system_code": "FAS", "confidence": "high", "reason": "data sheet"}
    candidate = SimpleNamespace(row=row, entry=rules_entry)
    assert AI.keep(db_session, project, candidate, verdict, model="scripted-now", reused=False, job_id=7)
    db_session.commit()
    conflicts = {c.field: c for c in db_session.query(DocumentClassificationConflict)
                 .filter(DocumentClassificationConflict.confirmed_classification_id == confirmed.id,
                         DocumentClassificationConflict.source == "ai")}
    assert set(conflicts) == {"primary_type", "system_code"}
    assert all(c.version == AI.PROMPT_VERSION for c in conflicts.values()), "the prompt version, not the rules version"
    # A reused answer: the slots carry the earlier model, prompt version and page size, never the current ones.
    earlier = {"verdict": verdict, "model": "scripted-earlier", "prompt_version": "p-earlier", "page_chars": 1500}
    assert AI.keep(db_session, project, candidate, verdict, reused=True, earlier=earlier, job_id=8)
    db_session.commit()
    latest = (db_session.query(DocumentClassification).filter(DocumentClassification.document_id == row.id)
              .order_by(DocumentClassification.id.desc()).first())
    assert (latest.model, latest.prompt_version, latest.page_chars, latest.producing_job_id) == (
        "scripted-earlier", "p-earlier", 1500, 8)
    assert latest.superseded_at is not None and dc.current(db_session, row).id == confirmed.id
    assert (db_session.query(DocumentClassificationConflict)
            .filter(DocumentClassificationConflict.confirmed_classification_id == confirmed.id,
                    DocumentClassificationConflict.version == "p-earlier").count() == 2)


# --- C2 (U2M6V-01): an IFC_DRAWING type outside the given folders -------------------------------------------------


@pytest.mark.parametrize("stage", [dc.Stage.HINT, dc.Stage.SUPPORTED])
@pytest.mark.parametrize("drawn", [True, None, False])
def test_an_ifc_drawing_type_outside_the_given_folders_never_claims_our_scope(stage, drawn):
    facts = da.ProjectFacts("30950", ("FAS",), drawn)
    for path in ("05- Drawings/L01.pdf", "09- Received/FA/L02.pdf", "L03.pdf"):
        row = _row(path)
        related = dc.Assessment(T.IFC_DRAWING, stage, dc.Strength.MODERATE, system_code="FAS", basis=dc.Basis.CONTENT)
        result = da.attribute(row, related, facts)
        assert result.state is A.RELATED_EXTERNAL and result.basis["rule"] == "type"
        assert result.basis["folder"] == {"given_to_us": False} and da.in_scope(result.state) is False
        loose = dc.Assessment(T.IFC_DRAWING, stage, dc.Strength.MODERATE, system_code=None, basis=dc.Basis.CONTENT)
        assert da.attribute(row, loose, facts).state is A.REFERENCE_ONLY


def test_a_models_ifc_answer_outside_the_given_folders_is_stored_as_not_ours(db_session, tmp_path, switched_on, recording):
    project = _ai_project(db_session, tmp_path, "94102")
    row = _ai_doc(db_session, project, tmp_path, "05- Misc/scan 102.pdf", DATASHEET_TEXT, "sha-c2")
    recording.answers = [_answer(("IFC_DRAWING", "FAS", "fire_alarm", "high", "an IFC sheet"))]
    assert AI.run(db_session, project)["written"] == 1
    db_session.expire_all()
    entry = dc.current(db_session, row)
    assert (entry.source, entry.primary_type) == ("ai", "IFC_DRAWING")
    assert entry.attribution == "RELATED_EXTERNAL" and entry.attribution_basis["rule"] == "type"


# --- C3 (U2M6V-02): the harness's AI arm, review-only, with a per-source breakdown ---------------------------------


ANSWERS = [
    {"primary_type": "SHOP_DRAWING", "system_code": "FAS", "confidence": "high"},
    {"primary_type": "SHOP_DRAWING", "confidence": "medium"},
    {"primary_type": "SPECIFICATION"},
    {"primary_type": "OTHER", "confidence": "low"},
    {"primary_type": "IFC_DRAWING", "confidence": "low"},
]


def test_the_harness_ai_arm_is_review_only_and_reports_each_source(tmp_path):
    engine = harness.open_clone(_clone(tmp_path / "clone.db", stored=False), live_url="sqlite:///:memory:")
    report = harness.evaluate(engine, _labels(), harness.load_kind_map(), arm="ai", provider=RecordingProvider(list(ANSWERS)))
    engine.dispose()
    assert report["ai"]["asked"] == 5 and report["ai"]["answered"] == 4 and report["ai"]["failed"] == 1
    assert report["ai"]["review_only"] is True and "supported" not in report["ai"]["stages"]
    assert sum(report["ai"]["stages"].values()) == 4
    m = report["all"]
    assert m["false_supported_rate"] == _rate(0, 0), "a model answer is never counted as supported"
    assert m["type_accuracy"] == _rate(2, 4) and m["system_accuracy"] == _rate(5, 5)
    by = report["by_source"]
    assert set(by) == {"ai", "rules"}
    assert (by["ai"]["answered"], by["rules"]["answered"]) == (4, 1)
    assert by["ai"]["false_supported_rate"] == _rate(0, 0) and by["ai"]["type_truth"] + by["rules"]["type_truth"] == m["type_truth"]


@pytest.mark.parametrize("confidence", ["high", "medium", "low"])
@pytest.mark.parametrize("kind", ["SHOP_DRAWING", "IFC_DRAWING", "DATASHEET", "OTHER", "UNKNOWN"])
def test_the_harness_and_the_live_pass_read_a_model_answer_the_same_way(kind, confidence):
    row = _row("05- Misc/scan.pdf")
    base = dc.hint(row.relative_path, row.filename, row.role)
    verdict = {"primary_type": kind, "system_code": "FAS", "confidence": confidence}
    ours = harness.review_only_assessment(row, base, verdict)
    entry = SimpleNamespace(primary_type=base.primary_type.value, stage=base.stage.value, evidence=list(base.evidence),
                            evidence_sources=list(base.evidence_sources), system_code=base.system_code,
                            discipline=base.discipline, assessment={"flags": []})
    live = AI._assessment(SimpleNamespace(row=row, entry=entry), verdict)
    assert (ours.primary_type, ours.stage, ours.strength) == (live.primary_type, live.stage, live.strength)
    assert ours.stage is not dc.Stage.SUPPORTED


def test_the_harness_stored_arm_caps_a_stored_ai_answer_and_reports_each_source(tmp_path):
    clone = _clone(tmp_path / "clone.db")
    with sqlite3.connect(clone) as conn:   # the second document's stored answer is the model's, stored as supported
        conn.execute("UPDATE document_classifications SET source = 'ai' WHERE document_id = "
                     "(SELECT id FROM project_documents WHERE sha256 = ?)", ("a2" * 32,))
    conn.close()
    engine = harness.open_clone(clone, live_url="sqlite:///:memory:")
    report = harness.evaluate(engine, _labels(), harness.load_kind_map(), arm="stored")
    engine.dispose()
    assert report["stored"]["ai_supported_capped"] == 1
    assert report["all"]["false_supported_rate"] == _rate(0, 2), "the model's supported answer is read as a hint"
    by = report["by_source"]
    assert set(by) == {"stored", "ai"} and (by["stored"]["answered"], by["ai"]["answered"]) == (4, 1)
    assert report["stored"]["sources"] == {"assessment": 4, "ai": 1}


# --- U2M6V-03: same-side claims are no conflict -------------------------------------------------------------------


def _conflicts(db, confirmed_id: int) -> list[DocumentClassificationConflict]:
    return (db.query(DocumentClassificationConflict)
            .filter(DocumentClassificationConflict.confirmed_classification_id == confirmed_id).all())


def test_a_weaker_claim_on_the_same_side_is_no_conflict_and_an_opposite_side_claim_is(client, db_session, tmp_path, ai,
                                                                                    classification_on):
    project_id = _project(client, _folder(tmp_path, "30951"), "30951")
    _sync(client, project_id)
    drawing = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    ifc = _doc(db_session, project_id, "00- IFC/FA/IFC-L01.pdf")
    automatic = _classifications(db_session, project_id)
    rules_drawing, rules_ifc = automatic["05- Drawings/L01.pdf"], automatic["00- IFC/FA/IFC-L01.pdf"]
    assert (rules_drawing.attribution, rules_ifc.attribution) == ("LIKELY_OUR_SCOPE", "RELATED_EXTERNAL")
    _engineer(client, db_session, RoleEnum.design_manager, email="manager3@example.com")
    project = db_session.get(Project, project_id)

    # OUR_SCOPE confirmed; the rules say LIKELY_OUR_SCOPE: the same side, no disagreement.
    ours = _confirm(client, project_id, drawing.id, primary_type=rules_drawing.primary_type,
                    system_code=rules_drawing.system_code, attribution="OUR_SCOPE", reason="our shop drawing").json()
    # REFERENCE_ONLY confirmed; the rules say RELATED_EXTERNAL: not ours either way, no disagreement.
    external = _confirm(client, project_id, ifc.id, primary_type=rules_ifc.primary_type, system_code=rules_ifc.system_code,
                        attribution="REFERENCE_ONLY", reason="the consultant's sheet, for reference").json()
    for _ in range(2):
        dc.assess_row(db_session, project, db_session.get(ProjectDocument, drawing.id))
        dc.assess_row(db_session, project, db_session.get(ProjectDocument, ifc.id))
        db_session.commit()
    assert _conflicts(db_session, ours["id"]) == [] and _conflicts(db_session, external["id"]) == []
    listing = {r["path"]: r["classification"] for r in client.get(f"/projects/{project_id}/documents/classification").json()}
    assert listing["05- Drawings/L01.pdf"]["conflicts"] == []
    assert not any("disagree with the engineer" in r for r in listing["05- Drawings/L01.pdf"]["review_reasons"])

    # The engineer says it is not ours: the rules' LIKELY_OUR_SCOPE is now on the other side, and recorded.
    not_ours = _confirm(client, project_id, drawing.id, primary_type=rules_drawing.primary_type,
                        system_code=rules_drawing.system_code, attribution="REFERENCE_ONLY", reason="another party's").json()
    dc.assess_row(db_session, project, db_session.get(ProjectDocument, drawing.id))
    db_session.commit()
    assert {(c.field, c.confirmed_value, c.proposed_value) for c in _conflicts(db_session, not_ours["id"])} == {
        ("attribution", "REFERENCE_ONLY", "LIKELY_OUR_SCOPE")}


# --- U2M6V-04: a confirmed row after a rules bump: one history row, not one per backfill -----------------------------


def test_after_a_rules_bump_a_confirmed_row_is_re_marked_once_not_on_every_backfill(client, db_session, tmp_path, ai,
                                                                                    classification_on, monkeypatch):
    project_id = _project(client, _folder(tmp_path, "30952"), "30952")
    _sync(client, project_id)
    document = _doc(db_session, project_id, "05- Drawings/L01.pdf")
    _engineer(client, db_session, RoleEnum.design_manager, email="manager4@example.com")
    confirmed = _confirm(client, project_id, document.id).json()     # IFC_DRAWING / RELATED_EXTERNAL: the rules disagree
    project = db_session.get(Project, project_id)
    monkeypatch.setattr(dc, "RULES_VERSION", "classify-next")

    def rows() -> int:
        return db_session.query(DocumentClassification).filter(DocumentClassification.document_id == document.id).count()

    before = rows()
    runs = []
    for _ in range(3):
        result = dc.backfill(db_session, project)
        runs.append((result["assessed"], result["skipped"], result["failed"], rows()))
    assert [r[3] for r in runs] == [before + 1] * 3, "one history row for the confirmed document, not one per backfill"
    assert [r[0] for r in runs] == [3, 0, 0] and [r[1] for r in runs] == [0, 3, 3] and all(r[2] == 0 for r in runs)
    db_session.expire_all()
    assert dc.current(db_session, db_session.get(ProjectDocument, document.id)).id == confirmed["id"]
    bumped = (db_session.query(DocumentClassificationConflict)
              .filter(DocumentClassificationConflict.confirmed_classification_id == confirmed["id"],
                      DocumentClassificationConflict.version == "classify-next").all())
    assert bumped and all(c.seen_count == 1 for c in bumped), "recorded once under the new rules, not recounted"


# --- U2M6V-07: the input fingerprint compared ----------------------------------------------------------------------


def test_a_changed_input_fingerprint_marks_the_attribution_stale_and_the_backfill_re_attributes_once(client, db_session,
                                                                                                    tmp_path, ai,
                                                                                                    classification_on,
                                                                                                    monkeypatch):
    project_id = _project(client, _folder(tmp_path, "30953"), "30953")
    _sync(client, project_id)
    ifc = _doc(db_session, project_id, "00- IFC/FA/IFC-L01.pdf")
    _engineer(client, db_session, RoleEnum.design_manager, email="manager5@example.com")
    confirmed = _confirm(client, project_id, ifc.id).json()

    def listing() -> dict:
        return {r["path"]: r["classification"] for r in client.get(f"/projects/{project_id}/documents/classification").json()}

    assert all(c["attribution_stale"] is False for c in listing().values())
    old = {path: e.input_fingerprint for path, e in _classifications(db_session, project_id).items()}
    # An input of the attribution changes (this company's names): the stored attributions no longer say what they rest on.
    monkeypatch.setattr(settings, "attribution_own_originators", "ORCH-049 Test Alias")
    shown = listing()
    automatic = [p for p in shown if p != "00- IFC/FA/IFC-L01.pdf"]
    assert all(shown[p]["attribution_stale"] is True for p in automatic)
    assert all(c["freshness"] == "current" for c in shown.values()), "freshness keeps its semantics"
    assert shown["00- IFC/FA/IFC-L01.pdf"]["attribution_stale"] is False, "the engineer's word is not stale by an input"
    metrics = client.get(f"/projects/{project_id}/documents/classification/metrics").json()
    assert metrics["attribution_stale"] == 2
    project = db_session.get(Project, project_id)
    first = dc.backfill(db_session, project)
    assert (first["assessed"], first["skipped"]) == (2, 1)
    after = _classifications(db_session, project_id)
    rows = {r.relative_path: r for r in db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)}
    for path in automatic:
        assert after[path].input_fingerprint != old[path]
        assert after[path].input_fingerprint == dc.input_fingerprint(rows[path], project)
    assert after["00- IFC/FA/IFC-L01.pdf"].id == confirmed["id"]
    assert all(c["attribution_stale"] is False for c in listing().values())
    again = dc.backfill(db_session, project)
    assert (again["assessed"], again["skipped"]) == (0, 3), "re-attributed once"


def test_the_backfill_never_replaces_the_models_answer_to_re_attribute_it(db_session, tmp_path, switched_on, recording,
                                                                          monkeypatch):
    project = _ai_project(db_session, tmp_path, "94103")
    row = _ai_doc(db_session, project, tmp_path, "05- Misc/scan 103.pdf", DATASHEET_TEXT, "sha-v7")
    recording.answers = [_answer(("DATASHEET", "FAS", "fire_alarm", "high", "data sheet"))]
    assert AI.run(db_session, project)["written"] == 1
    db_session.expire_all()
    answer = dc.current(db_session, row)
    assert answer.source == "ai" and not dc.attribution_stale(answer, row, project)
    monkeypatch.setattr(settings, "attribution_own_originators", "ORCH-049 Test Alias")
    assert dc.attribution_stale(answer, row, project), "shown as stale ..."
    result = dc.backfill(db_session, project)
    assert (result["assessed"], result["skipped"]) == (0, 1), "... but the model's answer is not replaced by the rules'"
    db_session.expire_all()
    assert dc.current(db_session, row).id == answer.id
