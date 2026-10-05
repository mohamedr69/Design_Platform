"""Evaluator .4 (M2 review 06, R6-01..R6-04). Each class of mistake the reviewer probed is tested against .4, and the
submitted evaluator .3 is run on the same input to show it gets it wrong (the tests must fail on .3)."""
import copy

from scripts import m2_eval4 as ev
from scripts import m2_pilot_eval as ev3

DOC = {"doc": "EP-1/a.pdf", "ep": "1", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high",
       "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "00", "decision": "rejected"}}
LABELS = {"documents": [DOC]}
REC = {"page": 1, "reference": "X-SD-1", "printed_revision": "00", "status": "rejected"}


def rows(*records, state="fresh", outcome="complete"):
    return {"EP-1/a.pdf": {"state": state, "extracted": {"records": list(records), "coverage": {"outcome": outcome}}}}


def with_labels(**changes):
    lab = copy.deepcopy(LABELS)
    lab["documents"][0]["labels"].update(changes)
    return lab


# 1. conflicting duplicates (R6-01) -----------------------------------------------------------------------------------


def test_a_conflicting_duplicate_after_a_correct_record_fails_the_critical_gate():
    wrong = dict(REC, printed_revision="09", status="approved")
    for order in ((REC, wrong), (wrong, REC)):
        t = ev.evaluate(LABELS, None, rows(*order))["totals"]
        assert t["register"]["decision"]["wrong"] == 1 and t["register"]["revision"]["wrong"] == 1
        kinds = sorted(c["kind"] for c in t["critical"])
        assert kinds == ["decision: wrong", "revision: wrong"], "record-order invariant"
        assert t["register"]["decision"]["precision_of_accepted"] == 0.0
        assert t["conflicting_emission_sets"] == 1
    # .3 hid it: one correct decision, 100 % precision, no critical
    t3 = ev3.evaluate(LABELS, None, rows(REC, wrong))["totals"]
    assert t3["critical"] == [] and t3["fields"]["decision"]["precision_of_accepted"] == 1.0


def test_a_redundant_exact_copy_neither_inflates_recovery_nor_counts_as_an_error():
    t = ev.evaluate(LABELS, None, rows(REC, dict(REC)))["totals"]
    assert t["register"]["decision"]["tp"] == 1 and t["register"]["decision"]["readable"] == 1 and t["critical"] == []
    assert t["redundant_copies"] == 1 and t["conflicting_emission_sets"] == 0


def test_a_wrong_copy_on_another_page_of_the_same_document_is_judged_too():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "cover", "reference": "X-SD-1", "printed_revision": "00", "decision": "rejected", "register": True}],
        "no_record_pages": {"2": "the sheet behind the cover"}}}}
    # the same identity again on page 3 (a page with no truth of its own) is unvalidated ...
    t = ev.evaluate(LABELS, pages, rows(REC, dict(REC, page=3, status="approved")))["totals"]
    assert t["unvalidated_emitted_records"] == 1
    # ... and on a labelled component page of another identity-bearing record it is associated across pages and judged
    pages["documents"]["EP-1/a.pdf"]["records"].append(
        {"page": 4, "component": "sheet", "reference": "X-SD-2", "printed_revision": "00", "decision": "UR", "register": True})
    pages["documents"]["EP-1/a.pdf"]["records"].append(
        {"page": 4, "component": "sheet", "reference": "X-SD-3", "printed_revision": "00", "decision": "UR", "register": True})
    t = ev.evaluate(LABELS, pages, rows(REC, dict(REC, page=4, status="approved")))["totals"]
    assert any(c["kind"] == "decision: wrong" for c in t["critical"])


# 2. conflict truth (R6-02) ------------------------------------------------------------------------------------------


def test_an_accepted_decision_on_conflict_truth_is_a_critical_false_acceptance():
    lab = with_labels(decision="conflict")
    t = ev.evaluate(lab, None, rows(dict(REC, status="approved")))["totals"]
    assert t["register"]["decision"]["accepted_on_conflict"] == 1 and t["register"]["decision"]["accepted"] == 1
    assert [c["kind"] for c in t["critical"]] == ["decision: accepted_on_conflict"]
    held = ev.evaluate(lab, None, rows(dict(REC, status="UR", flags=["decision_conflict"])))["totals"]
    assert held["register"]["decision"]["conflict_held"] == 1 and held["critical"] == []
    # .3: accepted=0, no critical
    t3 = ev3.evaluate(lab, None, rows(dict(REC, status="approved")))["totals"]
    assert t3["critical"] == [] and t3["fields"]["decision"]["accepted"] == 0


def test_a_silently_resolved_revision_conflict_is_critical_and_a_flagged_one_is_held():
    lab = with_labels(revision_conflict=True)
    silent = ev.evaluate(lab, None, rows(dict(REC, revision="R0", revision_source="printed")))["totals"]
    assert any(c["kind"] == "revision_conflict: conflict_resolved_silently" for c in silent["critical"])
    flagged = ev.evaluate(lab, None, rows(dict(REC, revision="R1", revision_source="folder", flags=["revision_conflict"])))["totals"]
    assert flagged["register"]["revision_conflict"]["conflict_held"] == 1 and flagged["critical"] == []


def test_a_decision_attached_to_the_other_component_on_the_page_is_wrong():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "A", "reference": "X-SD-1", "printed_revision": "00", "decision": "rejected", "register": True},
        {"page": 1, "component": "B", "reference": "X-SD-2", "printed_revision": "00", "decision": "approved", "register": True}]}}}
    t = ev.evaluate(LABELS, pages, rows(dict(REC, status="approved"), dict(REC, reference="X-SD-2", status="approved")))["totals"]
    assert [c["kind"] for c in t["critical"]] == ["decision: wrong"] and t["register"]["decision"]["tp"] == 1


# 3. execution outcomes keep denominators (R6-03) --------------------------------------------------------------------


def test_a_document_that_was_not_run_or_failed_keeps_its_readable_facts_in_the_denominator():
    for r, outcome in (({}, "not_run"), (rows(state="failed", outcome=None), "failed"), (rows(outcome="partial"), "partial")):
        t = ev.evaluate(LABELS, None, r)["totals"]
        assert t["execution"] == {outcome: 1}
        for f in ("reference", "revision", "decision"):
            assert t["register"][f]["readable"] == 1 and t["register"][f]["missed"] == 1
    t3 = ev3.evaluate(LABELS, None, {})["totals"]
    assert t3["fields"] == {}, ".3 dropped the not-run document from every denominator"


# 4. absence states (R6-03) ------------------------------------------------------------------------------------------


def test_an_absent_revision_stays_a_negative_when_the_record_is_missing():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "cover", "reference": "X-SD-1", "printed_revision": "absent", "decision": "n/a", "register": True}]}}}
    t = ev.evaluate(LABELS, pages, rows())["totals"]
    assert t["register"]["revision"]["tn"] == 1 and t["register"]["revision"]["readable"] == 0
    assert t["register"]["decision"]["tn"] == 1 and t["register"]["reference"]["missed"] == 1
    t3 = ev3.evaluate(LABELS, pages, rows())["totals"]
    assert t3["fields"]["revision"]["missed"] == 1, ".3 invented a readable revision"


def test_decision_absence_labels_are_explicit_negatives():
    for word in ("UR", "n/a", "absent", "none", "no decision", "not applicable"):
        assert ev.decision_truth(word) == ("negative", None)
        t = ev.evaluate(with_labels(decision=word), None, rows(dict(REC, status="approved")))["totals"]
        assert t["register"]["decision"]["fp"] == 1 and any(c["kind"] == "decision: fp" for c in t["critical"])
    for word in ("unknown", "illegible", "ambiguous", "unlabelled"):
        assert ev.decision_truth(word)[0] == "unscorable"
    assert ev3.judge_decision("absent", "approved") == "unscorable", ".3 discarded the explicit absence"


# 5. unknown identity, clear component (R6-03) -----------------------------------------------------------------------


def test_an_unknown_identity_does_not_hide_a_known_decision_error_on_a_single_component_page():
    lab = with_labels(reference="unknown")
    t = ev.evaluate(lab, None, rows(dict(REC, status="approved")))["totals"]
    assert t["register"]["reference"]["unscorable"] == 1
    assert [c["kind"] for c in t["critical"]] == ["decision: wrong"]
    t3 = ev3.evaluate(lab, None, rows(dict(REC, status="approved")))["totals"]
    assert t3["critical"] == [], ".3 marked the whole page unvalidated"


def test_an_ambiguous_component_association_stays_unscorable_rather_than_guessed():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "A", "reference": "unknown", "printed_revision": "00", "decision": "rejected", "register": True},
        {"page": 1, "component": "B", "reference": "unknown", "printed_revision": "00", "decision": "approved", "register": True}]}}}
    t = ev.evaluate(LABELS, pages, rows(dict(REC, reference="Y-SD-9", status="approved")))["totals"]
    assert t["register"]["decision"]["tp"] == 0 and t["register"]["decision"]["wrong"] == 0
    assert t["emissions"] == {"unassociated": 1}


# 6. raw observation shapes (R6-04) ----------------------------------------------------------------------------------


def test_title_block_and_transmittal_observations_are_raw_evidence_scored_with_their_values():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "sheet", "reference": "C&M-01-E-CCTV-2001", "printed_revision": "00", "decision": "UR", "register": False},
        {"page": 2, "component": "transmittal", "reference": "TR/1995/25", "printed_revision": "absent", "decision": "n/a", "register": False}]}}}
    r = {"EP-1/a.pdf": {"state": "fresh", "extracted": {"records": [], "coverage": {"outcome": "complete"}, "observations": [
        {"page": 1, "kind": "title_block", "number": "C&M-01-E-CCTV-2001", "revision": "01"},
        {"page": 2, "kind": "transmittal", "records": [], "reference": "TR/1995/25"}]}}}
    t = ev.evaluate(LABELS, pages, r)["totals"]
    assert t["raw"]["identity"]["tp"] == 2
    assert t["raw"]["revision"]["wrong"] == 1, "the observation's revision is judged, not only its identity"
    # the register layer does not count register-ineligible truth as missing, nor observations as records
    assert t["records"] == {"unregistered": 2} and t["register"] == {}
    t3 = ev3.evaluate(LABELS, pages, r)["totals"]
    assert t3["fields"]["raw_evidence"] == {**t3["fields"]["raw_evidence"], "tp": 1, "missed": 1},         ".3 found the transmittal's top-level reference but not title_block.number, and judged no revision"


def test_a_flagged_reference_is_still_the_register_key_and_counts_as_accepted_there():
    cut = dict(REC, reference="X-SD", flags=["reference_incomplete"])
    t = ev.evaluate(LABELS, None, rows(cut))["totals"]
    assert t["register"]["reference"]["wrong"] == 1 and t["register"]["flagged_reference"]["wrong"] == 1
    assert any(c["kind"] == "reference: wrong" for c in t["critical"])
    ok = ev.evaluate(LABELS, None, rows(dict(REC, flags=["reference_uncertain"])))["totals"]
    assert ok["register"]["reference"]["tp"] == 1 and ok["critical"] == []


def test_ai_evidence_is_its_own_layer_validated_counts_candidate_is_held_and_its_errors_are_shown():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "form", "reference": "MTS E 0018", "printed_revision": "00", "decision": "UR", "register": False},
        {"page": 2, "component": "sheet", "reference": "C&M-01-E-CCTV-2001", "printed_revision": "01", "decision": "UR", "register": False}]}}}

    def ai(*observations):
        return {"EP-1/a.pdf": {"state": "fresh", "extracted": {"records": [], "coverage": {"outcome": "complete"}, "observations": [],
                                                               "ai_evidence": {"variant": "EV1", "observations": list(observations),
                                                                               "coverage": {"pages": [{"page": 1, "calls": 3, "outcome": "evidence"}]},
                                                                               "calls": [{"cache_hit": False, "outcome": "ok"}]}}}}

    validated = {"page": 1, "kind": "ai_evidence", "field": "identity", "value": "MTS E 0018", "state": "validated"}
    t = ev.evaluate(LABELS, pages, ai(validated, dict(validated, field="revision", value="00")))["totals"]
    assert t["raw"]["identity"]["missed"] == 2, "the raw layer is the reader's alone"
    assert t["evidence"]["identity"]["tp"] == 1 and t["evidence"]["revision"]["tp"] == 1
    assert t["ai"]["calls"] == 1 and t["ai"]["states"] == {"identity:validated": 1, "revision:validated": 1}
    held = ev.evaluate(LABELS, pages, ai(dict(validated, state="candidate")))["totals"]
    assert held["evidence"]["identity"].get("tp", 0) == 0 and held["evidence"]["identity"]["held"] == 1
    wrong = ev.evaluate(LABELS, pages, ai(dict(validated, page=2, value="C&M-01-E-CCTV-2001"),
                                          dict(validated, page=2, field="revision", value="00")))["totals"]
    assert wrong["evidence"]["revision"]["wrong"] == 1
    assert [e["kind"] for e in wrong["evidence_introduced_errors"]] == ["revision: wrong"]
