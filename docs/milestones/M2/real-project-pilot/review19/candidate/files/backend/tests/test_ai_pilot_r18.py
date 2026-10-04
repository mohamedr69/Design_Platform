"""M2 review 18 successor (isolated candidate): R18-01 completion from usable targeted evidence, R18-02 no targeted read
after a failed / refused primary or escalation request, the required-first scheduling contract, E (located discovery,
deadline-bound requests / OCR) and the guard's offline replay. Scripted, keyed providers only (tests/_keyed_provider);
synthetic pages. Flags are set per test on the module (the reader reads them at call time)."""
import pymupdf
import pytest

from app.ai import evidence_reader as er
from app.ai.budget import JobBudget, Limits, open_budget

from ._keyed_provider import KeyedProvider, failure
from .test_m2_review08 import APPROVAL, attempt_page, decision_read, discover, doc_row, read, stage, value  # noqa: F401

SHA = "8" * 64


def _flags(monkeypatch, *, T=True, E=False):
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    monkeypatch.setattr(er, "TARGETED_ENABLED", T)
    monkeypatch.setattr(er, "EFFICIENT_ENABLED", E)
    monkeypatch.setattr(er, "PROMPTS", {**er.PROMPTS, "read_field_context": "read-field-context-2026-09-30.1",
                                        "discover_region": "discover-region-2026-09-30.1"})


def ctx(value, role="own_identity", legible=True):
    return {"value": value, "printed_label": "Drawing No", "role": role, "region": [0, 0, 1000, 1000], "legible": legible}


def illegible():
    return {"label_text": "", "value": "", "legible": False, "other_values_in_crop": []}


def empty():
    return {"label_text": "", "value": "", "legible": True, "other_values_in_crop": []}


def _page(text="Drawing No X-SD-1  REV 02", size=(1684, 1190)):
    doc = pymupdf.open()
    page = doc.new_page(width=size[0], height=size[1])
    page.insert_text((1300, 1100) if size[0] > 1300 else (400, 700), text, fontsize=9)
    return doc, page


def _sheet(number_line="DRAWING NO X-SD-1"):
    """A drawing sheet with a text-layer title block of several runs (the locator reads >= 5 runs from the text layer)."""
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    for i, t in enumerate(["PROJECT  EXAMPLE TOWER", "CLIENT  EXAMPLE", "SCALE 1:100", "DRAWN  AB", "CHECKED  CD"]):
        page.insert_text((1300, 1000 + 16 * i), t, fontsize=9)
    page.insert_text((1300, 1100), number_line, fontsize=9)
    return doc, page


def _run(db, provider, variant="EV1", budget=None):
    return er.EvidenceRun(db=db, project_id=None, provider=provider, budget=budget or open_budget(db, None), variant=variant, fresh=True)


def _own(out, field="identity"):
    return next(o for o in out["_observations"] if o["field"] == field and o["component"] == "own")


def _selected(ai, key):
    got = er.evidence_for(ai, sha256=SHA, profile="default", variant="EV1")
    assert got["state"] == "current", got
    return next(o for o in got["observations"] if er._field_key(o) == key)


# --- R18-01: a genuine targeted recovery completes the field; persisted, reloaded and selected ---------------------------


@pytest.mark.parametrize("primary", [illegible(), empty()], ids=["illegible", "empty"])
def test_targeted_rescue_completes_the_field_and_is_selected_after_reload(doc_row, monkeypatch, primary):
    _flags(monkeypatch)
    p = KeyedProvider({("discover", None, "small"): discover("X-SD-1", revision="02"), ("read_identity", "identity", "small"): primary,
                       ("read_revision", "revision", "small"): read("02"), ("read_field_context", "identity", "small"): ctx("X-SD-1")})
    ai = stage(doc_row, None, provider=p)                   # evidence_stage, persisted, reloaded from the database
    assert value(ai, "own:identity") == ("X-SD-1", "validated", 1, "completed")
    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "completed" and f["own:identity:targeted"] == "completed"
    assert f["own:identity:primary"] == ("unusable:illegible" if not primary["legible"] else "unusable:empty")
    req = attempt_page(ai)["requests"]
    assert req["own:identity"] == "ok" and req["own:identity:targeted"] == "ok"
    # the revision is associated with the identity the targeted read established (the page's completed target)
    assert _selected(ai, "own:revision").get("target") == "X-SD-1"
    assert [k[0] for k in p.requests][1:] == ["read_identity", "read_revision", "read_field_context"]


def _good_first(doc_row):
    stage(doc_row, None, provider=KeyedProvider({("discover", None, "small"): discover("X-SD-1", revision="02", decision=APPROVAL),
                                                 ("read_identity", "identity", "small"): read("X-SD-1"),
                                                 ("read_revision", "revision", "small"): read("02"),
                                                 ("read_decision", "decision", "small"): decision_read()}))


@pytest.mark.parametrize("answer, outcome", [
    ({"value": "", "printed_label": "", "role": "own_identity", "region": [0, 0, 1000, 1000], "legible": True}, "unusable:empty"),
    (ctx("X-SD-1", legible=False), "unusable:illegible"),
    (failure("timeout"), "failed:timeout"),
    (failure("refused"), "failed:refused"),
    (ctx("X-SD-1", role="referenced_identity"), "unusable:wrong_role"),
], ids=["empty", "illegible", "timeout", "refusal", "wrong_role"])
def test_unsuccessful_targeted_reads_never_complete_and_keep_the_last_good(doc_row, monkeypatch, answer, outcome):
    _flags(monkeypatch)
    _good_first(doc_row)
    p = KeyedProvider({("discover", None, "small"): discover("X-SD-1"), ("read_identity", "identity", "small"): illegible(),
                       ("read_field_context", "identity", "small"): answer})
    ai = stage(doc_row, None, provider=p)
    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "unusable:illegible" and f["own:identity:targeted"] == outcome
    assert value(ai, "own:identity") == ("X-SD-1", "validated", 1, "completed"), "the last-good identity is kept"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1)


def test_a_disagreeing_targeted_read_completes_as_a_conflict_never_a_validation(doc_row, monkeypatch):
    _flags(monkeypatch)
    _good_first(doc_row)
    ai = stage(doc_row, None, provider=KeyedProvider({("discover", None, "small"): discover("X-SD-1"),
                                                       ("read_identity", "identity", "small"): illegible(),
                                                       ("read_field_context", "identity", "small"): ctx("X-SD-7")}))
    got = value(ai, "own:identity")
    assert got[1] == "conflict" and got[2] == 2, "a completed disagreement supersedes as a conflict (accepted completed-read rule)"
    assert attempt_page(ai)["fields"]["own:identity:targeted"] == "completed"


def test_an_unsupported_targeted_read_completes_as_a_candidate_never_a_validation(doc_row, monkeypatch):
    _flags(monkeypatch)
    ai = stage(doc_row, None, provider=KeyedProvider({("discover", None, "small"): discover("X-SD-5"),
                                                       ("read_identity", "identity", "small"): illegible(),
                                                       ("read_field_context", "identity", "small"): ctx("X-SD-5")}))
    got = value(ai, "own:identity")
    assert got[:2] == ("X-SD-5", "candidate"), "X-SD-5 is printed nowhere on the page: agreement without support is a candidate"


# --- R18-02: no targeted read after a failed / refused primary or escalation ----------------------------------------------


def _ev2(db, answers, budget=None):
    p = KeyedProvider(answers)
    doc, page = _page("Drawing No X-SD-1 X-SD-2")
    run = _run(db, p, variant="EV2", budget=budget)
    out = er._read_page(run, page, sha256="a" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    return out, p, run


def test_no_targeted_read_after_a_failed_standard_escalation(db_session, monkeypatch):
    _flags(monkeypatch)
    out, p, run = _ev2(db_session, {("discover", None, "small"): discover("X-SD-1"), ("read_identity", "identity", "small"): read("X-SD-2"),
                                    ("read_identity", "identity", "standard"): failure("timeout")})
    assert [k[:3] for k in p.requests][1:] == [("read_identity", "identity", "small"), ("read_identity", "identity", "standard")]
    f = out["_fields"]
    assert f["own:identity:escalation"] == "failed:timeout" and f["own:identity:targeted"] == "not_attempted:after_failure"
    assert _own(out)["state"] == "conflict"


def test_no_targeted_read_after_a_budget_refused_escalation_and_the_exhaustion_stays(db_session, monkeypatch):
    _flags(monkeypatch)
    tight = JobBudget(limits=Limits(100000, 100000, 2, 1000, 0.0, 120.0, 2, 0.0, 0.0, 0.0), calls_today_before=0)
    out, p, run = _ev2(db_session, {("discover", None, "small"): discover("X-SD-1"), ("read_identity", "identity", "small"): read("X-SD-2")},
                       budget=tight)
    assert [k[0] for k in p.requests] == ["discover_page", "read_identity"], "the escalation never left the process"
    assert out["_fields"]["own:identity:escalation"] == "budget" and out["_fields"]["own:identity:targeted"] == "not_attempted:after_failure"
    assert run.exhausted == "calls_per_document", "the exhaustion is kept"


def test_primary_timeout_control_suppresses_the_targeted_read(db_session, monkeypatch):
    _flags(monkeypatch)
    doc, page = _page("Drawing No X-SD-1")
    p = KeyedProvider({("discover", None, "small"): discover("X-SD-1"), ("read_identity", "identity", "small"): failure("timeout")})
    out = er._read_page(_run(db_session, p), page, sha256="b" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert out["_fields"]["own:identity"] == "failed:timeout" and out["_fields"]["own:identity:targeted"] == "not_attempted:after_failure"
    assert [k[0] for k in p.requests] == ["discover_page", "read_identity"]


# --- the scheduling contract: required reads before optional targeted reads --------------------------------------------


def test_required_reads_come_before_the_optional_targeted_read(db_session, monkeypatch):
    """Contract: discovery, then identity / revision / decision primary reads, then the optional targeted reads."""
    _flags(monkeypatch)
    doc, page = _page("Drawing No X-SD-1  REV 02  B = APPROVED AS NOTED")
    p = KeyedProvider({("discover", None, "small"): discover("X-SD-9", revision="02", decision=APPROVAL),
                       ("read_identity", "identity", "small"): read("X-SD-9"), ("read_revision", "revision", "small"): read("02"),
                       ("read_decision", "decision", "small"): decision_read(), ("read_field_context", "identity", "small"): ctx("X-SD-9")})
    er._read_page(_run(db_session, p), page, sha256="c" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert [k[0] for k in p.requests] == ["discover_page", "read_identity", "read_revision", "read_decision", "read_field_context"]


def test_an_optional_read_cannot_take_the_budget_a_required_read_needs(db_session, monkeypatch):
    """The e5a0a94 order (identity, its targeted read, revision, decision) with a 4-call budget spent the fourth call on
    the optional read and refused the decision; required-first gives it to the decision and refuses the optional read."""
    _flags(monkeypatch)
    doc, page = _page("Drawing No X-SD-1  REV 02  B = APPROVED AS NOTED")
    four = JobBudget(limits=Limits(100000, 100000, 4, 1000, 0.0, 120.0, 2, 0.0, 0.0, 0.0), calls_today_before=0)
    p = KeyedProvider({("discover", None, "small"): discover("X-SD-9", revision="02", decision=APPROVAL),
                       ("read_identity", "identity", "small"): read("X-SD-9"), ("read_revision", "revision", "small"): read("02"),
                       ("read_decision", "decision", "small"): decision_read(), ("read_field_context", "identity", "small"): ctx("X-SD-9")})
    out = er._read_page(_run(db_session, p, budget=four), page, sha256="d" * 64, number=1,
                        facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    f = out["_fields"]
    assert f["own:identity"] == f["own:revision"] == f["own:decision"] == "completed"
    assert f["own:identity:targeted"] == "budget" and "read_field_context" not in [k[0] for k in p.requests]


def test_every_page_s_required_reads_come_before_any_optional_read(db_session, monkeypatch):
    """Document level: page 2's required reads are made before page 1's optional targeted read."""
    _flags(monkeypatch)
    pdf = pymupdf.open()
    for _ in range(2):
        pdf.new_page(width=1684, height=1190).insert_text((1300, 1100), "Drawing No X-SD-1", fontsize=9)
    p = KeyedProvider({("discover", None, "small"): [discover("X-SD-9"), discover("X-SD-8")],
                       ("read_identity", "identity", "small"): [read("X-SD-9"), read("X-SD-8")],
                       ("read_field_context", "identity", "small"): [ctx("X-SD-9"), ctx("X-SD-8")]})
    run = _run(db_session, p)
    obs, cov = er.read_document(run, pdf, sha256="e" * 64, records=[], observations=[])
    assert [k[0] for k in p.requests] == ["discover_page", "read_identity", "discover_page", "read_identity", "read_field_context", "read_field_context"]
    assert [pg["page"] for pg in cov["pages"]] == [1, 2] and all(pg["fields"]["own:identity:targeted"] == "completed" for pg in cov["pages"])


# --- E: located discovery, located absence, deadline-bound requests and OCR ----------------------------------------------


def test_locator_uses_title_block_labels_then_the_strip_never_the_whole_sheet():
    doc, page = _sheet()
    clip, route = er.locate_title_block(page)
    assert route == "located:labels:text" and clip.contains(pymupdf.Point(1310, 1097)) and clip.get_area() <= 0.45 * page.rect.get_area()
    doc, bare = _sheet("GENERAL ARRANGEMENT")                   # no number / revision label anywhere
    clip, route = er.locate_title_block(bare, ocr_timeout=0)
    assert route.startswith("located:strip") and clip.width < bare.rect.width
    doc, a4 = _page("DRAWING NO X-SD-1", size=(595, 842))
    assert er.locate_title_block(a4) == (None, "not_a_drawing_sheet")


def test_located_discovery_maps_its_regions_back_to_the_page(db_session, monkeypatch):
    _flags(monkeypatch, T=True, E=True)
    doc, page = _sheet()
    clip, _ = er.locate_title_block(page)
    # the value's place in the CROP's 0..1000 frame
    box = [int((1300 - clip.x0) / clip.width * 1000) - 5, int((1090 - clip.y0) / clip.height * 1000) - 5,
           int((1400 - clip.x0) / clip.width * 1000) + 5, int((1103 - clip.y0) / clip.height * 1000) + 5]
    answer = {**discover("X-SD-1"), "own_identity_region": box}
    p = KeyedProvider({("discover_region", None, "small"): answer, ("read_identity", "identity", "small"): read("X-SD-1")})
    out = er._read_page(_run(db_session, p), page, sha256="f" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    ident = _own(out)
    assert ident["state"] == "validated" and ident["support"] == "text"
    assert out["_fields"]["discovery:route"] == "located:labels:text"
    assert out["_fields"]["own:revision"] == er.LOCATED_ABSENCE, "absent from a located crop is not a verified absence"
    # M2 review 19 (R19-01): the page's text being silent about a decision is no evidence about what lies outside the
    # crop (a raster stamp, a mark) -- the decision of a located page is unknown, never absent (was absent_by_discovery)
    assert out["_fields"]["own:decision"] == er.LOCATED_ABSENCE, "a located crop never establishes a decision's absence"
    assert [k[0] for k in p.requests] == ["discover_region", "read_identity"]


def test_located_decision_absence_is_incomplete_where_the_page_prints_decision_words(db_session, monkeypatch):
    _flags(monkeypatch, T=True, E=True)
    doc, page = _page("DRAWING NO X-SD-1")
    page.insert_text((100, 100), "B = APPROVED AS NOTED    stamp of the consultant, reviewed for the project", fontsize=9)
    p = KeyedProvider({("discover_region", None, "small"): discover(""), ("read_field_context", "identity", "small"): ctx("", legible=False)})
    out = er._read_page(_run(db_session, p), page, sha256="1" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert out["_fields"]["own:decision"] == er.LOCATED_ABSENCE and out["_outcome"] == "partial"


def test_non_drawing_pages_are_discovered_whole_with_e(db_session, monkeypatch):
    _flags(monkeypatch, T=True, E=True)
    doc, page = _page("DRAWING NO X-SD-1", size=(595, 842))
    p = KeyedProvider({("discover_page", None, "small"): discover(""), ("read_field_context", "identity", "small"): ctx("", legible=False)})
    out = er._read_page(_run(db_session, p), page, sha256="2" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert out["_fields"]["discovery:route"] == "full_page" and out["_fields"]["own:identity"] == "absent_by_discovery"


class _Clock:
    """A job budget with a fixed remaining time (the application's JobBudget interface)."""

    def __init__(self, remaining):
        self.inner = JobBudget(limits=Limits(100000, 100000, 12, 1000, 0.0, 120.0, 2, 0.0, 0.0, 0.0), calls_today_before=0)
        self.left = remaining

    def remaining_s(self):
        return self.left

    def __getattr__(self, name):
        return getattr(self.inner, name)


class _Capture(KeyedProvider):
    def complete(self, request):
        self.timeouts = getattr(self, "timeouts", []) + [request.timeout_s]
        return super().complete(request)


def test_the_request_timeout_is_the_job_s_remaining_time_and_a_floor_stops_new_requests(db_session, monkeypatch):
    _flags(monkeypatch, T=False, E=True)
    p = _Capture({("discover_page", None, "small"): discover("")})
    doc, page = _page("DRAWING NO X-SD-1", size=(595, 842))
    run = _run(db_session, p, budget=_Clock(50.0))
    er._read_page(run, page, sha256="3" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert p.timeouts == [50.0] and run.log[-1]["timeout_s"] == 50.0
    p2 = _Capture({})
    run2 = _run(db_session, p2, budget=_Clock(12.0))
    out = er._read_page(run2, page, sha256="4" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert p2.calls == 0 and run2.exhausted == "elapsed_time" and out["_fields"]["discovery"] == "budget"
    assert "minimum request time" in run2.log[-1]["outcome"]


def test_e_off_keeps_the_provider_timeout_and_the_full_page(db_session, monkeypatch):
    _flags(monkeypatch, T=False, E=False)
    p = _Capture({("discover_page", None, "small"): discover("")})
    doc, page = _page("DRAWING NO X-SD-1")
    er._read_page(_run(db_session, p, budget=_Clock(50.0)), page, sha256="5" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="p")
    assert p.timeouts == [None] and [k[0] for k in p.requests] == ["discover_page"]


def test_ocr_inside_a_job_is_bounded_by_the_remaining_time(monkeypatch):
    _flags(monkeypatch, T=True, E=True)
    run = type("R", (), {"budget": _Clock(35.0)})()
    assert er._ocr_timeout(run) == 15.0
    run.budget.left = 10.0
    assert er._ocr_timeout(run) == 0.0
    called = []
    monkeypatch.setattr("app.services.document_control._tesseract", lambda: called.append(1))
    doc, page = _page("x")
    assert er._local_ocr(page, page.rect, 0.0) == "" and not called, "no time left: no OCR is started"


# --- G: the confirmed Rev.0 acceptance, replayed OFFLINE through the guard (no model call) -------------------------------

# the stored readings of the accepted EV1 run (review 13 package, r2x-small-B, EP-17428 FA MS/Rev.01/1-7.pdf page 4,
# sha256 535ffbda...): discovery and the blind read both gave "Rev.0" in the "Submittal No." cell, supported by the text
REV0_READINGS = [{"source": "discovery", "value": "Rev.0", "legible": True},
                 {"source": "blind_small", "value": "Rev.0", "legible": True, "label": "Submittal No."}]


def test_offline_replay_of_the_confirmed_rev0_acceptance(monkeypatch):
    texts = [("text", "Submittal No.: Rev.0")]
    monkeypatch.setattr(er, "GUARD_ENABLED", False)
    assert er.validate_value("identity", REV0_READINGS, texts, None)["state"] == "validated", "accepted behaviour reproduced"
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    got = er.validate_value("identity", REV0_READINGS, texts, None)
    assert got["state"] == "candidate" and got["guard"] == "bare_revision_token"


@pytest.mark.parametrize("value", ["FAS-09", "3105", "P10781", "AR-101", "2836", "E", "R1029-07-W&A-DWG-TYP-GRO-INT-9011-01"])
def test_valid_short_identifiers_pass_the_guard(monkeypatch, value):
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    readings = [{"source": "discovery", "value": value, "legible": True}, {"source": "blind_small", "value": value, "legible": True}]
    assert er.validate_value("identity", readings, [("text", f"No. {value}")], None)["state"] == "validated"
