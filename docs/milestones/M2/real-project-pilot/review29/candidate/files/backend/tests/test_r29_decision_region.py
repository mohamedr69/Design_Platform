"""Review 29 C3 -- the bounded decision-region path (DR). D16 / D18-shaped scans (a consultant stamp outside the title
block, discovery reporting an unclear mark and no option words), a D17-shaped handwritten code read twice through the
stamp's printed legend, rotations, a no-decision control, a receipt stamp, conflicting marks, the locator for located
(ROI) discovery and for scans, and the request bound. Unknown is never absent. No model."""
import pymupdf
import pytest

from app.ai import evidence_reader as er

from ._keyed_provider import KeyedProvider, failure
from ._r29 import (configure, decision_read, discovery, envelope_obs, frac_region, no_submittal_reader, norm_region, scan_with_stamp,  # noqa: F401
                   text_page, value_read)
from .test_ai_pilot_r19 import Stage

LEGEND = ["A - APPROVED", "B - APPROVED AS NOTED, RESUBMIT", "C - REVISE AND RESUBMIT", "D - REJECTED"]


@pytest.fixture(autouse=True)
def _ready(no_submittal_reader, monkeypatch):
    # the processing run's cached OCR text of a scan (as test_ai_pilot_r19 does): what makes a scanned page a reading candidate
    monkeypatch.setattr(er, "cached_ocr", lambda sha, i: "DWG NO. QQ-77-01 REV 01 PROJECT EXAMPLE")
    yield


def _scan_answers(*, decision_region=True, mark="unclear", identity=True):
    disc = discovery(page_kind="drawing_sheet",
                     own_identity="QQ-77-01" if identity else "", own_identity_label="DWG NO." if identity else "",
                     own_identity_region=frac_region(0.79, 0.88, 0.95, 0.91) if identity else [],
                     decision_mark_type=mark, decision_actor="consultant" if mark != "none" else "unknown",
                     decision_region=frac_region(0.61, 0.07, 0.92, 0.20) if decision_region else [])
    return {("discover_page", None, "small"): disc, ("read_identity", "identity", "small"): value_read("QQ-77-01", "DWG NO.")}


def _run(db, tmp_path, doc, name, answers):
    s = Stage(db, tmp_path, doc, name)
    p = KeyedProvider(answers)
    ai = s.run(p)
    att = ai["attempts"][-1]
    assert not att.get("error") and att.get("outcome") != "failed", (att.get("error"), att.get("outcome"))
    return s, p, ai, s.page_fields(ai)


@pytest.mark.parametrize("dr", [False, True])
def test_d16_shape_a_stamp_discovery_saw_but_could_not_name_is_read_not_absent(db_session, tmp_path, monkeypatch, dr):
    configure(monkeypatch, dr=dr)
    answers = {**_scan_answers(), ("read_decision", "decision", "small"): [decision_read("B", LEGEND), decision_read("B", LEGEND)]}
    s, p, ai, f = _run(db_session, tmp_path, scan_with_stamp(["CONSULTANT REVIEW", "B - APPROVED AS NOTED", "STAMP"]), f"d16{int(dr)}", answers)
    if not dr:
        assert f["own:decision"] == er.ABSENT_BY_DISCOVERY and ("read_decision", "decision", "small") not in p.requests, \
            "the frozen defect: a decision signal without option words became a verified absence"
        return
    assert f["own:decision"] == er.COMPLETED and p.requests.count(("read_decision", "decision", "small")) == 2
    d = envelope_obs(s, ai, field="decision")[0]
    assert d["value"] == "ANN" and d["decision_path"]["candidates"][0]["origin"] == "discovery" and d["decision_path"]["candidates"][0]["wide"] == "ok"
    assert {r["source"] for r in d["readings"]} >= {"blind_small", "blind_wide"}


def test_d18_shape_a_failed_read_is_a_failure_never_absence(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    answers = {**_scan_answers(), ("read_decision", "decision", "small"): failure("timeout")}
    _s, _p, _ai, f = _run(db_session, tmp_path, scan_with_stamp(["APPROVED AS NOTED"]), "d18", answers)
    assert f["own:decision"].startswith("failed") and f["own:decision"] != er.ABSENT_BY_DISCOVERY


def test_a_signal_without_region_goes_to_the_locator_and_a_failed_locator_is_unknown(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    answers = {**_scan_answers(decision_region=False), ("locate_decision", None, "small"): failure("timeout")}
    _s, p, _ai, f = _run(db_session, tmp_path, scan_with_stamp(["APPROVED"]), "noreg", answers)
    assert ("locate_decision", None, "small") in p.requests and f["own:decision"] == er.DECISION_UNKNOWN


def test_a_scan_with_no_signal_is_unknown_after_an_empty_locator_never_absent(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    answers = {**_scan_answers(decision_region=False, mark="none"), ("locate_decision", None, "small"): {"stamps": [], "notes": ""}}
    _s, p, _ai, f = _run(db_session, tmp_path, scan_with_stamp(["(faint stamp)"]), "nosig", answers)
    assert p.requests.count(("locate_decision", None, "small")) == 1 and f["own:decision"] == er.DECISION_UNKNOWN


def test_no_decision_control_a_fully_texted_letter_keeps_its_verified_absence(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    lines = [(0.1, 0.06 + 0.035 * i, f"Paragraph {i} of an ordinary covering letter about delivery dates and site access.", 10) for i in range(26)]
    lines.append((0.1, 0.04, "Ref No. LTR-0091", 10))
    lines.append((0.72, 0.04, "Date: 12 March 2024", 10))      # a letter runs margin to margin
    doc = text_page(lines)
    page = doc[0]
    answers = {("discover_page", None, "small"): discovery(page_kind="letter", own_identity="LTR-0091", own_identity_label="Ref No.",
                                                           own_identity_region=norm_region(page, "LTR-0091")),
               ("read_identity", "identity", "small"): value_read("LTR-0091", "Ref No.")}
    _s, p, _ai, f = _run(db_session, tmp_path, doc, "letter", answers)
    assert f["own:decision"] == er.ABSENT_BY_DISCOVERY and ("locate_decision", None, "small") not in p.requests


def _form_with_status(rotation=0):
    return text_page([(0.1, 0.10, "DOCUMENT NO. QX-500", 11), (0.6, 0.10, "REV 02", 11),
                      (0.1, 0.55, "CONSULTANT STATUS: A - APPROVED   B - APPROVED AS NOTED   C - REVISE AND RESUBMIT", 9),
                      *[(0.1, 0.15 + 0.012 * i, f"Item {i} cable tray support bracket detail and fixing schedule", 8) for i in range(30)]],
                     rotation=rotation)


@pytest.mark.parametrize("rotation", [0, 90, 270])
def test_d17_shape_a_written_code_read_twice_through_the_printed_legend_is_validated(db_session, tmp_path, monkeypatch, rotation):
    """Text-layer form (any rotation): discovery reports no decision; the decision vocabulary in the text layer gives the
    candidate region (display coordinates); two blind reads agree on the written code; the legend maps it; the actor is
    the consultant; the page's identity is validated on the page."""
    configure(monkeypatch, dr=True, pa=True)
    doc = _form_with_status(rotation)
    page = doc[0]
    regions = er._decision_vocab_regions(page, [])
    assert regions and all(0 <= v for v in regions[0]) and regions[0][2] <= page.rect.width + 1 and regions[0][3] <= page.rect.height + 1
    answers = {("discover_page", None, "small"): discovery(page_kind="review_form", own_identity="QX-500", own_identity_label="DOCUMENT NO.",
                                                           own_identity_region=norm_region(page, "DOCUMENT NO. QX-500"), own_revision="02",
                                                           own_revision_label="REV", own_revision_region=norm_region(page, "REV 02")),
               ("read_identity", "identity", "small"): value_read("QX-500", "DOCUMENT NO."), ("read_revision", "revision", "small"): value_read("02", "REV"),
               ("read_decision", "decision", "small"): [decision_read("B", LEGEND, mark="handwriting"), decision_read("B", LEGEND, mark="handwriting")]}
    s, _p, ai, f = _run(db_session, tmp_path, doc, f"d17r{rotation}", answers)
    d = envelope_obs(s, ai, field="decision")[0]
    assert f["own:decision"] == er.COMPLETED and d["value"] == "ANN" and d["state"] == "validated" and d["target"] == "QX-500"
    assert d["decision_path"]["candidates"][0]["origin"] == "text"


def test_a_single_read_is_not_corroborated(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    doc = _form_with_status()
    page = doc[0]
    answers = {("discover_page", None, "small"): discovery(own_identity="QX-500", own_identity_label="DOCUMENT NO.", own_identity_region=norm_region(page, "DOCUMENT NO. QX-500")),
               ("read_identity", "identity", "small"): value_read("QX-500", "DOCUMENT NO."),
               ("read_decision", "decision", "small"): [decision_read("B", LEGEND), failure("timeout")]}
    s, _p, ai, _f = _run(db_session, tmp_path, doc, "single", answers)
    d = envelope_obs(s, ai, field="decision")[0]
    assert d["state"] == "candidate" and any("not corroborated" in r for r in d["reasons"])


def test_conflicting_marks_are_a_conflict_and_a_receipt_stamp_is_no_decision(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    doc = _form_with_status()
    page = doc[0]
    base = {("discover_page", None, "small"): discovery(own_identity="QX-500", own_identity_label="DOCUMENT NO.", own_identity_region=norm_region(page, "DOCUMENT NO. QX-500")),
            ("read_identity", "identity", "small"): value_read("QX-500", "DOCUMENT NO.")}
    s, _p, ai, _f = _run(db_session, tmp_path, doc, "conflict", {**base, ("read_decision", "decision", "small"): [decision_read("B", LEGEND), decision_read("C", LEGEND)]})
    assert envelope_obs(s, ai, field="decision")[0]["state"] == "conflict"
    receipt = ["RECEIVED 12 MAR", "DOCUMENT CONTROL"]
    s, _p, ai, _f = _run(db_session, tmp_path, _form_with_status(), "receipt",
                         {**base, ("read_decision", "decision", "small"): [decision_read("RECEIVED", receipt), decision_read("RECEIVED", receipt)]})
    assert envelope_obs(s, ai, field="decision")[0]["state"] == "not_a_decision"


def test_located_discovery_gives_no_decision_and_the_locator_finds_the_stamp(db_session, tmp_path, monkeypatch):
    """ROI on: the title-block discovery's decision outputs are ignored (C3.1); the whole-page locator finds the stamp."""
    configure(monkeypatch, roi=True, dr=True)
    doc = text_page([(0.80, 0.86, "DRAWING NO QQ-77-02", 9), (0.80, 0.88, "REV 03", 9), (0.80, 0.90, "SCALE 1:100", 9),
                     (0.80, 0.92, "DRAWN AB", 9), (0.80, 0.94, "CHECKED CD", 9)], width=2384, height=1684)
    page = doc[0]
    stamp_region = frac_region(0.05, 0.05, 0.30, 0.15)
    answers = {("discover", None, "small"): discovery(page_kind="drawing_sheet", own_identity="QQ-77-02", own_identity_label="DRAWING NO",
                                                      own_identity_region=[100, 100, 600, 300], decision_options_printed=LEGEND,
                                                      decision_marked_option="A", decision_mark_type="tick", decision_actor="consultant",
                                                      decision_region=[100, 400, 600, 600]),
               ("read_identity", "identity", "small"): value_read("QQ-77-02", "DRAWING NO"),
               ("locate_decision", None, "small"): {"stamps": [{"region": stamp_region, "options_printed": LEGEND, "marked_option": "B",
                                                                "mark_type": "stamp", "actor": "consultant", "legible": True}], "notes": ""},
               ("read_decision", "decision", "small"): [decision_read("B", LEGEND), decision_read("B", LEGEND)]}
    s, p, ai, f = _run(db_session, tmp_path, doc, "roi", answers)
    assert p.requests.count(("locate_decision", None, "small")) == 1 and f["own:decision"] == er.COMPLETED
    d = envelope_obs(s, ai, field="decision")[0]
    assert d["value"] == "ANN" and d["decision_path"]["candidates"][0]["origin"] == "locator" and not d["decision_path"]["whole_page_discovery"]
    assert not any(r.get("source") == "discovery" for r in d["readings"]), "the located discovery's decision reading is not used"


def test_the_decision_path_is_bounded(db_session, tmp_path, monkeypatch):
    configure(monkeypatch, dr=True)
    answers = {**_scan_answers(decision_region=False, mark="none"),
               ("locate_decision", None, "small"): {"stamps": [{"region": frac_region(0.05, 0.05, 0.25, 0.15), "options_printed": LEGEND, "marked_option": "B",
                                                                "mark_type": "stamp", "actor": "consultant", "legible": True},
                                                               {"region": frac_region(0.40, 0.05, 0.60, 0.15), "options_printed": LEGEND, "marked_option": "B",
                                                                "mark_type": "stamp", "actor": "consultant", "legible": True},
                                                               {"region": frac_region(0.70, 0.05, 0.90, 0.15), "options_printed": LEGEND, "marked_option": "B",
                                                                "mark_type": "stamp", "actor": "consultant", "legible": True}], "notes": ""},
               ("read_decision", "decision", "small"): [decision_read("B", LEGEND)] * 6}
    _s, p, _ai, _f = _run(db_session, tmp_path, scan_with_stamp(["B"]), "bound", answers)
    assert p.requests.count(("locate_decision", None, "small")) == 1
    assert p.requests.count(("read_decision", "decision", "small")) <= er.DECISION_READS_PER_PAGE


def test_decision_region_off_is_the_accepted_decision_block(monkeypatch):
    """DR off: validate_decision is unchanged and _decision_region_read is never reached (identity check)."""
    monkeypatch.setattr(er, "DECISION_REGION_ENABLED", False)
    rs = [{"source": "discovery", "options_printed": LEGEND, "marked_option": "B", "mark_type": "tick", "actor": "consultant", "legible": True},
          {"source": "blind_small", "options_printed": LEGEND, "marked_option": "B", "mark_type": "tick", "actor": "consultant", "legible": True}]
    assert er.validate_decision(rs, "QX-500")["state"] == "validated"
    assert er.validate_decision_dr(rs, "QX-500")["state"] == "validated"
    assert er.validate_decision_dr(rs[:1], "QX-500")["state"] == "candidate", "one source is never corroboration"
