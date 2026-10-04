"""Contract tests of the AI evidence reader (M2 review 06, section 4) with a scripted provider -- no real model.

What they hold: the variants' reach (off / EV1 targeted + frozen audit / EV2 broad), that the blind reads never carry
a proposed value, the validation policy's states, budgets, the cache (no repeated call for the same question, and
separate identities per variant), failures kept as failures, and that records are never touched."""
import copy

import pymupdf
import pytest

from app.ai import evidence_reader as er
from app.ai.budget import open_budget
from app.ai.provider import RecordingProvider, TextPart
from app.models import AiUsage

DRAWING = "EP-1234-E-001"


def _pdf():
    doc = pymupdf.open()
    sheet = doc.new_page(width=1190, height=842)
    sheet.insert_text((900, 760), "DRAWING NO.", fontsize=8)
    sheet.insert_text((900, 775), DRAWING, fontsize=9)
    sheet.insert_text((1100, 760), "REV", fontsize=8)
    sheet.insert_text((1100, 775), "01", fontsize=9)
    form = doc.new_page(width=595, height=842)
    form.insert_text((60, 80), "CONSTRUCTION REVIEW FORM", fontsize=12)
    form.insert_text((60, 120), "Review Reference: CRS-DOC-02006", fontsize=9)
    for i, option in enumerate(("APPROVED", "APPROVED AS NOTED", "REVISE AND RESUBMIT")):
        form.insert_text((80, 400 + 16 * i), option, fontsize=9)
    return doc


def _discover(identity="", revision="", options=(), marked="", mark="none", actor="unknown"):
    return {"page_kind": "drawing_sheet", "own_identity": identity, "own_identity_label": "DRAWING NO." if identity else "",
            "own_identity_region": [740, 880, 900, 930] if identity else [], "own_revision": revision,
            "own_revision_label": "REV" if revision else "", "own_revision_region": [900, 880, 960, 930] if revision else [],
            "decision_options_printed": list(options), "decision_marked_option": marked, "decision_mark_type": mark,
            "decision_actor": actor, "decision_region": [100, 450, 600, 520] if options else [], "other_numbers": [], "notes": ""}


def _read(value, legible=True):
    return {"label_text": "DRAWING NO.", "value": value, "legible": legible, "other_values_in_crop": []}


def _run(db, provider, variant="EV1", **kw):
    return er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant=variant, **kw)


def _sha_with_audit(selected: bool, page: int = 1) -> str:
    for i in range(1000):
        sha = f"{i:064x}"
        if er.audit_selected(sha, page) is selected:
            return sha
    raise AssertionError


CONFIDENT = [{"page": 1, "reference": DRAWING, "printed_revision": "01", "status": "UR"}]


def test_off_makes_no_call(db_session):
    provider = RecordingProvider()
    observations, coverage = er.read_document(_run(db_session, provider, "off"), _pdf(), sha256="a" * 64, records=[], observations=[])
    assert provider.calls == 0 and observations == [] and coverage["outcome"] == "off"


def test_audit_selection_is_frozen_and_near_the_rate():
    picks = [er.audit_selected(f"{i:064x}", 1) for i in range(2000)]
    assert picks == [er.audit_selected(f"{i:064x}", 1) for i in range(2000)]
    assert 0.17 < sum(picks) / len(picks) < 0.23


def test_triggers_reach_a_page_with_no_record():
    facts = er.PageFacts(2, "CONSTRUCTION REVIEW FORM\nReview Reference: CRS-DOC-02006\nAPPROVED\nAPPROVED AS NOTED\nREVISE AND RESUBMIT", [], [])
    why = er.triggers(facts, document_empty=True, variant="EV1", sha256="a" * 64)
    assert "form_or_title_block_without_identity" in why and "decision_block_unread" in why
    # A confident page is read by EV1 only when it is in the frozen audit sample, by EV2 always.
    confident = er.PageFacts(1, "DRAWING NO. EP-1234-E-001 REV 01", CONFIDENT, [])
    assert er.triggers(confident, document_empty=False, variant="EV1", sha256=_sha_with_audit(False)) == []
    assert er.triggers(confident, document_empty=False, variant="EV1", sha256=_sha_with_audit(True)) == ["audit_confident_output"]
    assert er.triggers(confident, document_empty=False, variant="EV2", sha256=_sha_with_audit(False)) == ["broad_verification"]


def test_blind_reads_never_carry_a_proposed_value(db_session):
    provider = RecordingProvider([_discover(DRAWING, "01"), _read(DRAWING), _read("01")])
    pdf = _pdf()
    pdf.delete_page(1)
    observations, _ = er.read_document(_run(db_session, provider, "EV2"), pdf, sha256=_sha_with_audit(False),
                                       records=copy.deepcopy(CONFIDENT), observations=[])
    tasks = [r.task for r in provider.requests]
    assert tasks == ["discover_page", "read_identity", "read_revision"]
    for request in provider.requests:
        for part in request.parts:
            if isinstance(part, TextPart):
                assert DRAWING not in part.text and "01" not in part.text.replace("0..1000", "")
        if request.task.startswith("read_"):
            assert [p.text for p in request.parts if isinstance(p, TextPart)] == [er.READ_TEXTS[request.task]]
    states = {o["field"]: o["state"] for o in observations}
    assert states == {"identity": "validated", "revision": "validated"}


def test_records_and_observations_are_never_modified(db_session):
    records = copy.deepcopy(CONFIDENT)
    observations = [{"page": 1, "kind": "title_block", "number": DRAWING, "revision": "01"}]
    before = copy.deepcopy((records, observations))
    provider = RecordingProvider([_discover("EP-9999-E-001", "02"), _read("EP-9999-E-001"), _read("02")])
    out, _ = er.read_document(_run(db_session, provider, "EV1"), _pdf(), sha256=_sha_with_audit(True),
                              records=records, observations=observations)
    assert (records, observations) == before
    # A contradiction of the deterministic reading stays a contradiction; it is not resolved either way.
    assert {o["field"]: o["state"] for o in out if o["page"] == 1} == {"identity": "conflict", "revision": "conflict"}


def test_model_agreement_without_source_support_is_only_a_candidate():
    texts = [("text", "nothing printed here"), ("ocr", "")]
    readings = [{"source": "discovery", "value": "AB-77-001"}, {"source": "blind_small", "value": "AB-77-001", "legible": True}]
    assert er.validate_value("identity", readings, texts, None)["state"] == "candidate"
    assert er.validate_value("identity", readings, [("text", "Drawing No AB-77-001")], None)["state"] == "validated"
    assert er.validate_value("identity", readings[:1], [("text", "AB-77-001")], None)["state"] == "candidate"
    disagree = readings + [{"source": "blind_standard", "value": "AB-77-00I", "legible": True}]
    assert er.validate_value("identity", disagree, [("text", "AB-77-001")], None)["state"] == "conflict"
    assert er.validate_value("identity", [{"source": "blind_small", "value": "", "legible": False}], texts, None)["state"] == "unreadable"
    # One OCR character apart is support of its own kind, reported as such.
    near = er.validate_value("identity", readings, [("ocr", "Reference ICDS-DOC-01943")], None)
    assert near["support"] is None
    near = er.validate_value("identity", [{"source": "blind_small", "value": "CDS-DOC-01943", "legible": True}],
                             [("ocr", "Reference ICDS-DOC-01943")], None)
    assert near["support"] == "ocr" and near["state"] == "validated"


def test_decision_policy():
    options = ["A = NO OBJECTION", "B = NO OBJECTION AS NOTED", "C = REVISE AND RESUBMIT"]
    marked = {"options_printed": options, "marked_option": "B = NO OBJECTION AS NOTED", "mark_type": "tick", "actor": "consultant", "legible": True}
    assert er.validate_decision([{"source": "discovery", **marked}, {"source": "blind_small", **marked}]) == \
        {"state": "validated", "decision": "ANN", "reasons": []}
    assert er.validate_decision([{"source": "discovery", **marked}])["state"] == "candidate"
    contractor = dict(marked, actor="contractor")
    assert er.validate_decision([{"source": "blind_small", **contractor}])["state"] == "candidate"
    blank = dict(marked, marked_option="", mark_type="none")
    assert er.validate_decision([{"source": "blind_small", **blank}])["state"] == "no_decision_marked"
    other = dict(marked, marked_option="C = REVISE AND RESUBMIT")
    assert er.validate_decision([{"source": "discovery", **marked}, {"source": "blind_small", **other}])["state"] == "conflict"


def test_the_same_question_is_not_asked_twice_and_variants_do_not_share_answers(db_session):
    pdf = _pdf()
    answers = [_discover(), _discover("CRS-DOC-02006")]
    provider = RecordingProvider(copy.deepcopy(answers) + [_read("CRS-DOC-02006")])
    er.read_document(_run(db_session, provider, "EV1"), pdf, sha256="b" * 64, records=[], observations=[])
    first = provider.calls
    assert first >= 2
    db_session.commit()
    again = RecordingProvider()
    er.read_document(_run(db_session, again, "EV1"), pdf, sha256="b" * 64, records=[], observations=[])
    assert again.calls == 0
    other = RecordingProvider(copy.deepcopy(answers) + [_read("CRS-DOC-02006")])
    er.read_document(_run(db_session, other, "EV2"), pdf, sha256="b" * 64, records=[], observations=[])
    assert other.calls >= 2
    fresh = RecordingProvider(copy.deepcopy(answers) + [_read("CRS-DOC-02006")])
    er.read_document(_run(db_session, fresh, "EV1", fresh=True), pdf, sha256="b" * 64, records=[], observations=[])
    assert fresh.calls == first


def test_a_failed_call_is_recorded_as_failed_not_as_a_negative(db_session):
    error = RuntimeError("timed out")
    error.kind = "transport"
    provider = RecordingProvider([error, error])
    observations, coverage = er.read_document(_run(db_session, provider, "EV1"), _pdf(), sha256="c" * 64, records=[], observations=[])
    assert observations == []
    assert [p["outcome"] for p in coverage["pages"]] == ["failed", "failed"]
    db_session.commit()
    assert {u.outcome for u in db_session.query(AiUsage).all()} == {"transport"}
    # Nothing is cached from a failure: the next run asks again.
    retry = RecordingProvider([_discover(), _discover()])
    er.read_document(_run(db_session, retry, "EV1"), _pdf(), sha256="c" * 64, records=[], observations=[])
    assert retry.calls == 2


def test_budget_stops_calls_and_says_so(db_session, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "ai_max_calls_per_document", 1)
    provider = RecordingProvider([_discover("CRS-DOC-02006"), _read("CRS-DOC-02006")])
    run = _run(db_session, provider, "EV1")
    observations, coverage = er.read_document(run, _pdf(), sha256="d" * 64, records=[], observations=[])
    assert provider.calls == 1
    assert coverage["outcome"] == "budget" and run.exhausted == "calls_per_document"
    assert all(o["state"] != "validated" for o in observations)
    assert any(str(p["outcome"]).startswith("budget") for p in coverage["pages"])
    assert any(str(entry["outcome"]).startswith("budget") for entry in run.log)


def test_unknown_price_is_not_reported_as_zero_cost(db_session):
    provider = RecordingProvider([_discover(), _discover()])
    run = _run(db_session, provider, "EV1")
    er.read_document(run, _pdf(), sha256="e" * 64, records=[], observations=[])
    assert run.log and all(entry.get("cost") is None for entry in run.log if not entry.get("cache_hit"))


@pytest.mark.parametrize("row, blind, state", [
    ({"part_number": "FC-501", "quantity": "4"}, {"part_number": "FC-501", "quantity": "4", "legible": True, "row_is_heading": False}, "validated"),
    ({"part_number": "FC-501", "quantity": "4"}, {"part_number": "FC501", "quantity": "4", "legible": True, "row_is_heading": False}, "conflict"),
    ({"part_number": "FC-501", "quantity": "4"}, {"part_number": "FC-501", "quantity": "14", "legible": True, "row_is_heading": False}, "conflict"),
    ({"part_number": "FC-501", "quantity": "4"}, None, "unverified"),
    ({"part_number": None, "quantity": "2"}, {"part_number": "", "quantity": "", "legible": True, "row_is_heading": True}, "conflict"),
])
def test_boq_row_policy(row, blind, state):
    assert er.validate_boq_row(row, blind)["state"] == state


def test_boq_rows_selected_by_variant():
    lines = [{"page": 1, "catalog_no": f"P-{i}", "quantity": "1"} for i in range(200)]
    held = [{"page": 1, "part_number": "X", "quantity": "2"}]
    ev1 = er.boq_rows_to_verify(lines, held, variant="EV1", sha256="f" * 64)
    assert ev1[0] == (held[0], "held_row") and 20 < len(ev1) - 1 < 65
    assert len(er.boq_rows_to_verify(lines, held, variant="EV2", sha256="f" * 64)) == 201
    assert er.boq_rows_to_verify(lines, held, variant="off", sha256="f" * 64) == []


def test_stage_is_off_by_default_and_writes_only_its_own_key(db_session, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app.ai import submittal_reader

    path = tmp_path / "sheet.pdf"
    _pdf().save(path)
    records = copy.deepcopy(CONFIDENT)
    row = SimpleNamespace(sha256="9" * 64, extracted={"records": records, "observations": [], "parser_version": "p"},
                          reference=DRAWING, status="UR")
    project = SimpleNamespace(id=None)
    assert er.configured_variant() == "off"
    assert er.evidence_stage(db_session, project, [(row, path)], provider=RecordingProvider()) == \
        {"variant": "off", "documents": 0, "calls": 0, "cache_hits": 0, "failed": 0, "budget_stopped": 0}
    assert "ai_evidence" not in row.extracted
    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    provider = RecordingProvider([_discover(), _discover("CRS-DOC-02006"), _read("CRS-DOC-02006")])
    counts = er.evidence_stage(db_session, project, [(row, path)], provider=provider, variant="EV1")
    assert counts["documents"] == 1 and counts["calls"] == provider.calls
    assert row.extracted["records"] == CONFIDENT and row.reference == DRAWING and row.status == "UR"
    assert row.extracted["parser_version"] == "p"
    stored = row.extracted["ai_evidence"]
    assert stored["variant"] == "EV1" and stored["read_sha256"] == row.sha256 and stored["calls"]
    # Blocked by the application's gate (AI disabled, project policy, provider): not run, and says why.
    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: "AI assistance is disabled")
    assert er.evidence_stage(db_session, project, [(row, path)], provider=RecordingProvider(), variant="EV1")["not_run"]


def test_no_get_handler_reaches_the_evidence_reader():
    import pathlib
    import re as _re

    routers = pathlib.Path(er.__file__).resolve().parents[1] / "routers"
    for source in routers.glob("*.py"):
        assert "evidence_reader" not in source.read_text(encoding="utf-8"), source.name
    assert not _re.search(r"evidence_reader", (pathlib.Path(er.__file__).resolve().parents[1] / "services" / "document_sync.py").read_text(encoding="utf-8"))


def test_boq_rows_are_read_blind_and_compared_afterwards(db_session):
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)
    page.insert_text((60, 100), "1   Smoke detector        SIGA-PS     75", fontsize=9)
    extraction = {"lines": [{"page": 1, "catalog_no": "SIGA-PS", "quantity": "15", "description": "Smoke detector", "y_px": 410,
                             "table_span": [200, 3300], "quantity_span": [200, 420]}],
                  "issues": [{"target": "boq_line:1:1", "page": 1, "region": [200, 500, 900, 560],
                              "detail": {"catalog_no": "FSB-PC4", "raw_quantity": "]", "description": "Bridge"}}]}
    provider = RecordingProvider([{"part_number": "FSB-PC4", "quantity": "1", "description": "Bridge", "legible": True, "row_is_heading": False},
                                  {"part_number": "SIGA-PS", "quantity": "75", "description": "Smoke detector", "legible": True, "row_is_heading": False}])
    results = er.verify_boq_rows(_run(db_session, provider, "EV2"), doc, sha256="7" * 64, extraction=extraction, render_dpi=300)
    for request in provider.requests:
        texts = " ".join(p.text for p in request.parts if isinstance(p, TextPart))
        assert "SIGA-PS" not in texts and "15" not in texts and "FSB-PC4" not in texts
    by_part = {r["row"]["part_number"]: r for r in results}
    assert by_part["SIGA-PS"]["state"] == "conflict" and by_part["SIGA-PS"]["accepted_by_reader"] is True
    assert by_part["FSB-PC4"]["accepted_by_reader"] is False and by_part["FSB-PC4"]["blind"]["quantity"] == "1"


def test_boq_part_is_compared_literally_and_the_quantity_cell_is_its_own_image(db_session):
    # "PT-1S" is not "PT-1S+": the .1 normalisation dropped the "+" and validated a wrong accepted part (EP-30088)
    assert er.validate_boq_row({"part_number": "PT-1S", "quantity": "1"},
                               {"part_number": "PT-1S+", "quantity": "1", "legible": True, "row_is_heading": False})["state"] == "conflict"
    assert er.validate_boq_row({"part_number": "SL2-42D3D-CGL-M +SL23I", "quantity": "48"},
                               {"part_number": "SL2-42D3D-CGL-M+SL23I", "quantity": "48", "legible": True, "row_is_heading": False})["state"] == "validated"
    doc = pymupdf.open()
    doc.new_page(width=842, height=595)
    provider = RecordingProvider([{"part_number": "X-1", "quantity": "2", "description": "", "legible": True, "row_is_heading": False}])
    er.verify_boq_rows(_run(db_session, provider, "EV2"), doc, sha256="8" * 64, render_dpi=300, extraction={"lines": [
        {"page": 1, "catalog_no": "X-1", "quantity": "2", "y_px": 400, "table_span": [100, 3000], "quantity_span": [100, 300]}], "issues": []})
    assert [p.label for p in provider.requests[0].parts] == ["task", "quantity_cell", "row"]
    # no quantity column known: not read, recorded as no geometry (never a guess)
    none = er.verify_boq_rows(_run(db_session, RecordingProvider(), "EV2"), doc, sha256="9" * 64, render_dpi=300, extraction={"lines": [
        {"page": 1, "catalog_no": "X-1", "quantity": "2", "y_px": 400, "table_span": [100, 3000]}], "issues": []})
    assert none[0]["state"] == "no_geometry"
