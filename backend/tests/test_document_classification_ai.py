"""The model's look at weakly classified documents (app.services.document_classification_ai):
only weak, fresh, readable documents with text are sent, several per call; the answer is
kept beside the rules' (source "ai"); the same content is never asked twice; nothing is
sent with the switch off; a failed call writes nothing."""
from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from app.ai import provider as provider_module
from app.ai.provider import RecordingProvider
from app.core.config import get_settings
from app.models import DocumentClassification, Project, ProjectDocument, User
from app.services import document_classification as DC
from app.services import document_classification_ai as AI

settings = get_settings()


@pytest.fixture()
def switched_on(monkeypatch):
    monkeypatch.setattr(settings, "document_classification_v2", True)
    monkeypatch.setattr(settings, "document_classification_ai_enabled", True)
    monkeypatch.setattr(settings, "document_classification_ai_batch", 2)
    yield


@pytest.fixture()
def recording():
    provider = RecordingProvider()
    provider_module.set_provider(provider)
    yield provider
    provider_module.set_provider(None)


def _pdf(path: Path, text: str) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(40, 40, 560, 800), text, fontsize=10)
    doc.save(path)
    doc.close()
    return path


def _project(db, tmp_path: Path, ep: str) -> Project:
    creator = db.query(User).order_by(User.id).first()
    project = Project(ep_number=ep, project_name="Classification", source_folder_path=str(tmp_path),
                      created_by_id=creator.id)
    db.add(project)
    db.commit()
    return project


def _doc(db, project: Project, tmp_path: Path, relative: str, text: str | None, sha: str) -> ProjectDocument:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if relative.endswith(".pdf"):
        _pdf(path, text or "")
    else:
        path.write_bytes(b"x")
    row = ProjectDocument(project_id=project.id, role="document", path=str(path), relative_path=relative,
                          filename=path.name, state="fresh", sha256=sha, findings=[], acknowledged=[],
                          extracted={"records": [], "notes": []})
    db.add(row)
    db.commit()
    DC.assess_row(db, project, row)    # the rules' answer, as processing writes it
    db.commit()
    return row


DATASHEET_TEXT = ("TECHNICAL DATA SHEET\nAddressable optical smoke detector, model 2251. Operating voltage 15-32 V DC. "
                  "Approvals: UL 268, EN 54-7. Fire alarm system component.")
CERTIFICATE_TEXT = ("CERTIFICATE OF APPROVAL\nDubai Civil Defence hereby certifies the emergency lighting luminaire "
                    "listed below for use in buildings in the Emirate of Dubai.")


def _answer(*docs):
    return {"documents": [{"i": i, "primary_type": t, "component_types": [], "system_code": s, "discipline": d,
                           "confidence": c, "reason": r} for i, (t, s, d, c, r) in enumerate(docs)]}


def test_weak_documents_are_sent_in_batches_and_the_answer_is_kept_beside_the_rules(db_session, tmp_path, switched_on, recording):
    project = _project(db_session, tmp_path, "94001")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 001.pdf", DATASHEET_TEXT, "sha-a")
    b = _doc(db_session, project, tmp_path, "05- Misc/scan 002.pdf", CERTIFICATE_TEXT, "sha-b")
    c = _doc(db_session, project, tmp_path, "05- Misc/copy of scan 001.pdf", DATASHEET_TEXT, "sha-a")   # same bytes as a
    empty = _doc(db_session, project, tmp_path, "05- Misc/blank.pdf", "", "sha-e")
    _doc(db_session, project, tmp_path, "05- Misc/sheet.xlsx", None, "sha-x")
    assert all(DC.current(db_session, r).stage in AI.WEAK_STAGES for r in (a, b, c, empty))

    p = AI.plan(db_session, project)
    assert [x.row.id for x in p.to_send] == [a.id, b.id]
    assert [x.row.id for x in p.followers["sha-a"]] == [c.id]
    assert p.skipped == {AI.NO_TEXT: 1, "not a PDF or Word file": 1}
    est = p.estimate()
    assert est["files"] == 2 and est["calls"] == 1 and est["input_tokens"] > AI.ROUTE_OVERHEAD_TOKENS

    recording.answers = [_answer(("DATASHEET", "FAS", "fire_alarm", "high", "'TECHNICAL DATA SHEET', smoke detector"),
                                 ("CERTIFICATE", "ELS", "emergency_lighting", "medium", "'CERTIFICATE OF APPROVAL'"))]
    result = AI.run(db_session, project)
    assert recording.calls == 1 and result["sent"] == 2 and result["answered"] == 2 and result["written"] == 3
    request = recording.requests[0]
    assert request.task == AI.TASK and "TECHNICAL DATA SHEET" in request.parts[0].text and "sheet.xlsx" not in request.parts[0].text

    db_session.expire_all()
    first = DC.current(db_session, a)
    # Review-only: the model's reading alone is a hint at most (moderate when it is sure), never supported.
    assert (first.source, first.stage, first.primary_type, first.system_code, first.evidence_strength) == (
        "ai", "hint", "DATASHEET", "FAS", "moderate")
    assert first.assessment["ai"]["verdict"]["confidence"] == "high" and first.assessment["rules"]["stage"] in AI.WEAK_STAGES
    assert "ai_page_text" in first.evidence_sources and first.evidence[0].startswith("the model read the first page")
    assert DC.current(db_session, c).source == "ai" and DC.current(db_session, c).assessment["ai"]["reused"] is True
    second = DC.current(db_session, b)
    assert (second.stage, second.primary_type, second.evidence_strength) == ("hint", "CERTIFICATE", "weak")
    # The rules' answers are kept, superseded: history, not lost.
    assert db_session.query(DocumentClassification).filter(DocumentClassification.document_id == a.id).count() == 2

    # Nothing is asked again: a second run sends nothing.
    again = AI.run(db_session, project)
    assert recording.calls == 1 and again["sent"] == 0


def test_an_earlier_answer_is_reused_after_the_rules_answer_again(db_session, tmp_path, switched_on, recording):
    project = _project(db_session, tmp_path, "94002")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 003.pdf", DATASHEET_TEXT, "sha-r")
    recording.answers = [_answer(("DATASHEET", "FAS", None, "high", "data sheet"))]
    AI.run(db_session, project)
    assert recording.calls == 1
    # The rules answer again (new rules, a backfill): the AI answer is superseded ...
    entry = DC.current(db_session, a)
    entry.superseded_at = entry.created_at
    db_session.commit()
    DC.record(db_session, project, a, DC.assess(a), source="backfill")
    db_session.commit()
    assert DC.current(db_session, a).source == "backfill"
    # ... and comes back from the stored verdict, with no call.
    result = AI.run(db_session, project)
    assert recording.calls == 1 and result["reused"] == 1 and DC.current(db_session, a).source == "ai"


def test_nothing_is_sent_with_the_switch_off_and_a_failed_call_writes_nothing(db_session, tmp_path, monkeypatch, recording):
    monkeypatch.setattr(settings, "document_classification_v2", True)
    project = _project(db_session, tmp_path, "94003")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 004.pdf", DATASHEET_TEXT, "sha-f")
    assert AI.run(db_session, project)["skipped_run"].startswith("AI is off")
    assert recording.calls == 0

    monkeypatch.setattr(settings, "document_classification_ai_enabled", True)
    recording.answers = [{"documents": []}]          # an answer for no document: refused, nothing written
    result = AI.run(db_session, project)
    assert result["failed_calls"] == 1 and result["written"] == 0
    assert DC.current(db_session, a).source != "ai"


def test_the_intake_types_are_not_the_models_and_a_named_other_is_known(db_session, tmp_path, switched_on, recording):
    items = AI.SCHEMA["properties"]["documents"]["items"]["properties"]
    assert "DESIGN_SHEET" not in items["primary_type"]["enum"] and "DRF" not in items["primary_type"]["enum"]
    project = _project(db_session, tmp_path, "94004")
    a = _doc(db_session, project, tmp_path, "03- MS/calc/VOLTAGE DROP.pdf", "VOLTAGE DROP CALCULATION. Loop 1: 24 devices, 2.5 mm2 cable, end of line voltage 21.4 V.", "sha-v")
    b = _doc(db_session, project, tmp_path, "03- MS/calc/OTHER.pdf", "Some text that names nothing in particular here.", "sha-o")
    recording.answers = [_answer(("OTHER", "FAS", "fire_alarm", "medium", "calculation: voltage drop for loop 1"),
                                 ("UNKNOWN", None, None, "low", "the text names nothing"))]
    AI.run(db_session, project)
    db_session.expire_all()
    assert (DC.current(db_session, a).primary_type, DC.current(db_session, a).stage) == ("OTHER", "hint")
    assert (DC.current(db_session, b).primary_type, DC.current(db_session, b).stage) == ("UNKNOWN", "unknown")
    # An intake type outside the schema is refused with the whole answer; were one to arrive, it reads as unknown.
    candidate = AI.Candidate(row=b, entry=DC.current(db_session, b))
    assert AI._assessment(candidate, {"primary_type": "DESIGN_SHEET", "confidence": "high"}).primary_type == DC.DocumentType.UNKNOWN


# --- ORCH-047: corrections F-02 and F-03, the stop, review-only answers and the pass's own daily cap -----------


def test_a_failure_after_the_insert_leaves_no_row_or_a_whole_one(db_session, tmp_path, switched_on, recording, monkeypatch):
    """F-02: the provenance travels in the row's one insert. On SQLite the
    usage log's commit makes the savepoint's release final, so whatever
    fails afterwards, a source "ai" row is either absent or carries
    assessment["ai"] and ["rules"]."""
    project = _project(db_session, tmp_path, "94011")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 011.pdf", DATASHEET_TEXT, "sha-f2")
    recording.answers = [_answer(("DATASHEET", "FAS", "fire_alarm", "high", "data sheet"))]
    real_record = DC.record

    def record_then_fail(*args, **kwargs):
        real_record(*args, **kwargs)
        raise RuntimeError("a failure after the row's insert")

    monkeypatch.setattr(DC, "record", record_then_fail)
    with pytest.raises(RuntimeError):
        AI.run(db_session, project)
    db_session.rollback()      # as the processing hook does
    db_session.expire_all()
    rows = (db_session.query(DocumentClassification)
            .filter(DocumentClassification.document_id == a.id, DocumentClassification.source == "ai").all())
    for row in rows:
        assert row.assessment.get("ai", {}).get("verdict") and row.assessment.get("rules", {}).get("stage"), row.assessment
        assert row.assessment["ai"]["prompt_version"] == AI.PROMPT_VERSION and row.assessment["ai"]["model"] == "recording"


def _supersede_with_the_rules(db_session, project, row):
    entry = DC.current(db_session, row)
    entry.superseded_at = entry.created_at
    db_session.commit()
    DC.record(db_session, project, row, DC.assess(row), source="backfill")
    db_session.commit()


def test_a_compatible_earlier_answer_is_reused_with_the_model_prompt_and_page_size_it_came_from(
        db_session, tmp_path, switched_on, recording, monkeypatch):
    """F-03: reuse copies the original model, prompt version and page size;
    nothing current is stamped on an old answer."""
    project = _project(db_session, tmp_path, "94012")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 012.pdf", DATASHEET_TEXT, "sha-f3a")
    recording.answers = [_answer(("DATASHEET", "FAS", None, "high", "data sheet"))]
    AI.run(db_session, project)
    first = DC.current(db_session, a).assessment["ai"]
    assert (first["model"], first["prompt_version"], first["page_chars"], first["reused"]) == (
        "recording", AI.PROMPT_VERSION, 2500, False)

    _supersede_with_the_rules(db_session, project, a)
    monkeypatch.setattr(settings, "document_classification_ai_page_chars", 900)
    monkeypatch.setattr(settings, "document_classification_ai_model", "another-model")
    monkeypatch.setattr(AI, "PROMPT_VERSION", "document-classification-ai-test.3")
    monkeypatch.setattr(AI, "COMPATIBLE_PROMPT_VERSIONS", ("document-classification-ai-test.3", first["prompt_version"]))
    result = AI.run(db_session, project)
    assert recording.calls == 1 and result["reused"] == 1
    db_session.expire_all()
    again = DC.current(db_session, a)
    assert again.source == "ai"
    assert (again.assessment["ai"]["model"], again.assessment["ai"]["prompt_version"], again.assessment["ai"]["page_chars"],
            again.assessment["ai"]["reused"]) == ("recording", first["prompt_version"], 2500, True)
    assert again.assessment["ai"]["verdict"] == first["verdict"] and again.assessment["rules"]["stage"] in AI.WEAK_STAGES


def test_an_answer_from_an_incompatible_prompt_version_is_not_reused(db_session, tmp_path, switched_on, recording, monkeypatch):
    """F-03: a prompt version left out of COMPATIBLE_PROMPT_VERSIONS is
    asked again, and the new row carries the new version."""
    project = _project(db_session, tmp_path, "94013")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 013.pdf", DATASHEET_TEXT, "sha-f3b")
    recording.answers = [_answer(("DATASHEET", "FAS", None, "high", "data sheet"))]
    AI.run(db_session, project)
    old = DC.current(db_session, a).assessment["ai"]["prompt_version"]

    _supersede_with_the_rules(db_session, project, a)
    monkeypatch.setattr(AI, "PROMPT_VERSION", "document-classification-ai-test.4")
    monkeypatch.setattr(AI, "COMPATIBLE_PROMPT_VERSIONS", ("document-classification-ai-test.4",))
    assert AI.plan(db_session, project).reused == []
    recording.answers = [_answer(("CERTIFICATE", "FAS", None, "medium", "certificate"))]
    result = AI.run(db_session, project)
    assert recording.calls == 2 and result["reused"] == 0 and result["written"] == 1
    db_session.expire_all()
    meta = DC.current(db_session, a).assessment["ai"]
    assert meta["prompt_version"] == "document-classification-ai-test.4" != old and meta["reused"] is False
    assert meta["verdict"]["primary_type"] == "CERTIFICATE"


def test_the_models_answer_is_review_only_and_never_supported_on_its_own(db_session, tmp_path, switched_on, recording):
    """A-15 1(b): a model reading alone reaches at most hint / moderate, and
    every AI row is flagged for a person; supported needs the rules or an
    engineer's confirmation."""
    project = _project(db_session, tmp_path, "94014")
    a = _doc(db_session, project, tmp_path, "05- Misc/scan 014.pdf", DATASHEET_TEXT, "sha-ro-a")
    b = _doc(db_session, project, tmp_path, "05- Misc/scan 015.pdf", CERTIFICATE_TEXT, "sha-ro-b")
    recording.answers = [_answer(("DATASHEET", "FAS", "fire_alarm", "high", "'TECHNICAL DATA SHEET'"),
                                 ("CERTIFICATE", "ELS", "emergency_lighting", "medium", "'CERTIFICATE OF APPROVAL'"))]
    AI.run(db_session, project)
    db_session.expire_all()
    ai_rows = db_session.query(DocumentClassification).filter(DocumentClassification.source == "ai",
                                                              DocumentClassification.project_id == project.id).all()
    assert len(ai_rows) == 2 and all(r.stage != DC.Stage.SUPPORTED.value for r in ai_rows)
    assert {(r.stage, r.evidence_strength) for r in ai_rows} == {("hint", "moderate"), ("hint", "weak")}
    for row in (a, b):
        shown = DC.as_dict(DC.current(db_session, row), row, project)
        assert shown["source"] == "ai" and shown["needs_review"] is True
        assert DC.AI_REVIEW_REASON in shown["review_reasons"]
    # Every confidence the model can give: never supported.
    candidate = AI.Candidate(row=a, entry=ai_rows[0])
    for confidence in AI.CONFIDENCE:
        for kind in AI.MODEL_TYPES:
            assessment = AI._assessment(candidate, {"primary_type": kind, "confidence": confidence,
                                                    "component_types": ["DATASHEET"]})
            assert assessment.stage != DC.Stage.SUPPORTED, (kind, confidence)


def test_the_pass_has_its_own_daily_cap_apart_from_the_platforms(db_session, tmp_path, switched_on, recording, monkeypatch):
    """A-15 1(a): DOCUMENT_CLASSIFICATION_AI_MAX_CALLS_PER_PROJECT_PER_DAY
    counts the pass's own calls and stops it before the next batch; other
    tasks' calls do not count against it (they count against the platform's)."""
    from app.models import AiUsage

    assert settings.document_classification_ai_max_calls_per_project_per_day < settings.ai_max_calls_per_project_per_day
    monkeypatch.setattr(settings, "document_classification_ai_max_calls_per_project_per_day", 1)
    project = _project(db_session, tmp_path, "94015")
    for n in range(4):
        _doc(db_session, project, tmp_path, f"05- Misc/cap {n}.pdf", DATASHEET_TEXT + f" Sheet {n}.", f"sha-cap-{n}")
    # Another task's calls today: the platform's cap counts them, the pass's does not.
    for _ in range(3):
        db_session.add(AiUsage(project_id=project.id, task="drawings_chat", model="recording", estimated_cost=0.0,
                               latency_ms=1, cache_hit=False, escalated=False, outcome="ok"))
    db_session.commit()
    assert AI.calls_today_for_task(db_session, project) == 0
    recording.answers = [_answer(("DATASHEET", "FAS", None, "high", "data sheet"), ("DATASHEET", "FAS", None, "high", "data sheet"))]
    result = AI.run(db_session, project)
    assert recording.calls == 1 and result["calls"] == 1 and result["written"] == 2
    assert "daily limit (1 calls a project)" in result["stopped"]
    assert AI.calls_today_for_task(db_session, project) == 1
    # The next run the same day sends nothing more.
    again = AI.run(db_session, project)
    assert recording.calls == 1 and again["calls"] == 0 and "daily limit" in again["stopped"]


class _StopAfter:
    """A job context whose stop is asked for at the n-th check."""

    def __init__(self, at: int):
        self.at, self.checks, self.steps = at, 0, []

    def progress(self, done, total, message, **extra):
        self.steps.append((done, total, message, extra))

    def check(self):
        from app.services import jobs

        self.checks += 1
        if self.checks >= self.at:
            raise jobs.Cancelled()


def test_a_stop_is_honoured_between_batches(db_session, tmp_path, switched_on, recording):
    from app.services import jobs

    project = _project(db_session, tmp_path, "94016")
    rows = [_doc(db_session, project, tmp_path, f"05- Misc/stop {n}.pdf", DATASHEET_TEXT + f" Sheet {n}.", f"sha-stop-{n}")
            for n in range(4)]
    recording.answers = [_answer(("DATASHEET", "FAS", None, "high", "data sheet"), ("DATASHEET", "FAS", None, "high", "data sheet"))]
    ctx = _StopAfter(2)
    with pytest.raises(jobs.Cancelled):
        AI.run(db_session, project, ctx=ctx)
    assert recording.calls == 1 and ctx.checks == 2
    db_session.rollback()
    db_session.expire_all()
    # The first batch's answers stand (committed with it); the second batch was never sent.
    assert [DC.current(db_session, r).source == "ai" for r in rows] == [True, True, False, False]


def test_the_processing_hook_hands_the_pass_its_job_context_and_a_stop_stops_the_job(client, db_session, tmp_path, monkeypatch):
    """The classify phase is given the job's context, so a stop asked for
    is honoured between its batches; the stop is not swallowed as a pass
    failure."""
    from app.services import document_classification_ai, document_processing, document_sync, jobs

    from .test_document_sync import _DRAWINGS
    from .test_document_sync import _pdf as _sync_pdf
    from .test_document_sync import _project as _client_project

    folder = tmp_path / "EP-94017"
    for relative, text in _DRAWINGS.items():
        _sync_pdf(folder / relative, text)
    project = db_session.get(Project, _client_project(client, folder, "94017"))
    document_sync.sync(db_session, project, ctx=_StopAfter(10 ** 6))
    monkeypatch.setattr(provider_module, "classification_ai_on", lambda: True)
    handed = {}

    def stopped_pass(db, project, *, max_calls=None, ctx=None):
        handed["ctx"] = ctx
        raise jobs.Cancelled()

    monkeypatch.setattr(document_classification_ai, "run", stopped_pass)
    recorder = _StopAfter(10 ** 6)
    with pytest.raises(jobs.Cancelled):
        document_processing.run(db_session, project, ctx=recorder)
    assert handed["ctx"] is recorder
    assert any(step[3].get("phase") == "classify" for step in recorder.steps)
