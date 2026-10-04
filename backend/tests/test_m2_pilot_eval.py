"""Adversarial tests of the pilot evaluator v2 (M2 review 05, R5-02 / R5-03): every case the submitted scorer got
wrong, plus the record-matching contract."""
from scripts import m2_pilot_eval as ev


def test_known_absence_is_a_negative_control_that_can_fail():
    # n/a consultant decision + an accepted approval = a false positive (the old scorer returned unscorable)
    assert ev.judge_decision("n/a", "approved") == "fp"
    assert ev.judge_decision("n/a", "ANN") == "fp"
    assert ev.judge_decision("n/a", "UR") == "tn"
    assert ev.judge_decision("n/a", None, has_record=False) == "tn"
    # a reference labelled absent + an invented one = a false positive
    assert ev.judge_reference("absent", "WRONG-SD-001") == "fp"
    assert ev.judge_reference("absent", None) == "tn"


def test_unknown_truth_stays_unscorable_and_is_not_lumped_with_absence():
    for truth in ("unknown", "illegible", "ambiguous", "unlabelled", "unknown (rotated)"):
        assert ev.judge_decision(truth, "approved") == "unscorable"
        assert ev.judge_reference(truth, "X-SD-1") == "unscorable"


def test_ur_empty_and_positive_decisions_have_different_denominators():
    counter = ev.collections.Counter()
    for truth, status in (("UR", "UR"), ("UR", None), ("rejected", "rejected"), ("ANN", "UR"), ("n/a", "approved")):
        counter[ev.judge_decision(truth, status, has_record=status is not None)] += 1
    r = ev.rates(counter)
    assert (r["tp"], r["tn"], r["fp"], r["missed"]) == (1, 2, 1, 1)
    assert r["accepted"] == 2 and r["precision_of_accepted"] == 0.5        # the correct UR outcomes are not "accepted"
    assert r["specificity_of_negatives"] == round(2 / 3, 4)
    assert r["recovery_of_readable"] == 0.5


def test_a_conflict_needs_its_evidence_not_merely_a_default_ur():
    assert ev.judge_decision("conflict", "UR") == "conflict_missing"
    assert ev.judge_decision("conflict", "UR", flags=("decision_conflict",)) == "conflict_ok"
    assert ev.judge_decision("conflict", "UR", candidates=(("ANN", "text"), ("rejected", "ocr"))) == "conflict_ok"
    assert ev.judge_decision("conflict", "ANN", flags=("decision_conflict",)) == "conflict_missing"


def test_held_evidence_is_recovery_never_an_accepted_approval():
    state = ev.judge_decision("ANN", "UR", candidates=(("ANN", "drawn_frame", "held"),))
    assert state == "held"
    r = ev.rates(ev.collections.Counter([state]))
    assert r["accepted"] == 0 and r["held_evidence"] == 1 and r["tp"] == 0


def test_records_are_matched_by_page_and_identity_and_a_later_correct_record_does_not_hide_a_wrong_one():
    labels = {"documents": [{"doc": "EP-1/a.pdf", "ep": "1", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high",
                             "labels": {"kind": "shop-drawing cover", "reference": "X-SD-0001", "revision": "00", "decision": "rejected"}}]}
    page_labels = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "cover", "reference": "X-SD-0001", "printed_revision": "00", "decision": "rejected", "register": True},
        {"page": 2, "component": "sheet", "reference": "X-SD-0001", "printed_revision": "00", "decision": "rejected", "register": True}],
        "no_record_pages": {"3": "catalogue"}}}}
    rows = {"EP-1/a.pdf": {"state": "fresh", "extracted": {"records": [
        {"page": 1, "reference": "X-SD-0008", "revision": "R0", "revision_source": "default", "status": "rejected"},      # wrong on page 1
        {"page": 2, "reference": "X-SD-0001", "printed_revision": "00", "status": "rejected"},                             # right on page 2
        {"page": 2, "reference": "X-SD-0001", "printed_revision": "00", "status": "rejected"},                             # a duplicate
        {"page": 3, "reference": "Y-SD-9", "status": "ANN"}],                                                              # a false record
        "coverage": {"outcome": "complete"}}}}
    result = ev.evaluate(labels, page_labels, rows)
    t = result["totals"]
    assert t["records"] == {"substituted": 1, "matched": 1, "duplicate": 1, "extra": 1}
    assert t["fields"]["reference"]["wrong"] == 1 and t["fields"]["reference"]["tp"] == 1 and t["fields"]["reference"]["fp"] == 1
    kinds = sorted(c["kind"] for c in t["critical"])
    assert "false approval" in kinds and "wrong reference accepted" in kinds and "record where truth has none" in kinds
    # the default-sourced revision on the wrong record is a projection, not a raw misread
    assert t["fields"]["revision"]["missed"] == 1


def test_pages_without_truth_stay_unvalidated():
    labels = {"documents": [{"doc": "EP-1/b.pdf", "ep": "1", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high",
                             "labels": {"kind": "material submittal cover", "reference": "M-MAS-1", "revision": "00", "decision": "ANN"}}]}
    rows = {"EP-1/b.pdf": {"state": "fresh", "extracted": {"records": [
        {"page": 1, "reference": "M-MAS-1", "printed_revision": "00", "status": "ANN"},
        {"page": 7, "reference": "M-MAS-2", "status": "UR"}], "coverage": {"outcome": "complete"}}}}
    result = ev.evaluate(labels, None, rows)
    assert result["totals"]["unvalidated_emitted_records"] == 1
    assert result["totals"]["records"] == {"matched": 1}


def test_word_transmittals_are_scored():
    labels = {"documents": [{"doc": "EP-1/t.doc", "ep": "1", "cohort": "c", "stratum": "transmittal_word", "extension": ".doc", "scan_like": False, "confidence": "high",
                             "labels": {"kind": "Word transmittal (DOCUMENT TRANSMITTAL)", "reference": "TR/197/26", "revision": "absent", "decision": "n/a", "system": "ELS / CBS"}}]}
    rows = {"EP-1/t.doc": {"state": "fresh", "extracted": {"records": [{"page": 1, "reference": "TR/197/26", "revision": "R0", "status": "UR", "system_code": "ELS"}]}}}
    f = ev.evaluate(labels, None, rows)["totals"]["fields"]
    assert f["reference"]["tp"] == 1 and f["decision"]["tn"] == 1 and f["system"]["tp"] == 1
    assert f["revision"]["tn"] == 1        # no printed revision, none extracted (R0 is a default projection)


def test_system_equivalence_is_a_table_not_a_substring():
    assert ev.judge_system("FAS / VES", {"system_code": "FAS"}) == "tp"
    assert ev.judge_system("CBS", {"system_code": "ELS"}) == "tp"
    assert ev.judge_system("other (HVAC; non-FAS)", {"system_code": "FAS"}) == "fp"       # 'non-FAS' is not FAS
    assert ev.judge_system("other (HVAC; non-FAS)", {"system_code": None}) == "tn"
    assert ev.judge_system("PA/VA", {"system_code": "FAS"}) == "wrong"


def test_revision_tokens_are_compared_as_printed():
    assert ev.norm_rev("00") == ev.norm_rev("R0") == ev.norm_rev("Rev.0") == "R0"
    assert ev.norm_rev("07") == "R7" and ev.norm_rev("R10") == "R10"
    assert ev.norm_rev("AB") == "AB" and ev.norm_rev("C1") == "C1"
    # the reference's own revision suffix is the revision the reader files
    assert ev.judge_revision("R3 (suffix of the reference)", {"revision": "R3", "revision_source": "suffix"}, "25H-S202-NCC-SD-MEP-ELE-FA-003-R3") == "tp"
    assert ev.judge_reference("25H-S202-NCC-SD-MEP-ELE-FA-003-R3", "25H-S202-NCC-SD-MEP-ELE-FA-003") == "tp"
    assert ev.judge_revision("07", {"revision": "R10", "revision_source": "printed"}) == "wrong"
