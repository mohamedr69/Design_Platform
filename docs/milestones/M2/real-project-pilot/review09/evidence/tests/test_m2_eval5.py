"""Evaluator .5 (M2 review 07, R7-01). The reviewer's evaluator probes are frozen here as negative tests: each is shown
to be hidden by .4 and counted by .5. Permutation invariance, several components on one page, redundant copies and
mixed correct / wrong emissions are tested too."""
import copy
import itertools

from scripts import m2_eval4 as ev4
from scripts import m2_eval5 as ev5

DOC = {"doc": "EP-1/a.pdf", "ep": "1", "cohort": "c", "stratum": "s", "extension": ".pdf", "scan_like": False, "confidence": "high",
       "labels": {"kind": "shop-drawing cover", "reference": "X-SD-1", "revision": "00", "decision": "rejected"}}
LABELS = {"documents": [DOC]}


def labels(**changes):
    lab = copy.deepcopy(LABELS)
    lab["documents"][0]["labels"].update(changes)
    return lab


def obs(field, value, state="validated", page=1, **kw):
    return {"page": page, "kind": "ai_evidence", "field": field, "value": value, "state": state, **kw}


SOURCE = "a" * 64   # the fixture's bytes: its AI evidence records the hash it was read from (review 09, R9-03)


def rows(ai=(), records=(), observations=()):
    return {"EP-1/a.pdf": {"state": "fresh", "sha256": SOURCE,
                           "extracted": {"records": list(records), "observations": list(observations), "coverage": {"outcome": "complete"},
                                         "ai_evidence": {"observations": list(ai), "read_sha256": SOURCE}}}}


LEGACY_AI = {"profile": None, "variant": None}   # the tests' AI rows are flat review 06 envelopes: context "unknown|unknown"


def evaluate(*a, **k):
    """Evaluator .7 scores AI evidence only for a declared run context; these tests declare the legacy one."""
    return ev5.evaluate(*a, ai_context=k.pop("ai_context", LEGACY_AI), **k)


def fields(result, layer="evidence"):
    return result["totals"][layer]["fields"]


# --- the reviewer's probes (R7-01), .4 hides them, .5 counts them ------------------------------------------------------


def test_a_wrong_validated_identity_is_a_wrong_accepted_fact_not_a_missed_read():
    r = rows([obs("identity", "WRONG-99")])
    t4 = ev4.evaluate(LABELS, None, r)["totals"]
    assert t4["evidence"]["identity"]["missed"] == 1 and t4["evidence_introduced_errors"] == []
    t5 = evaluate(LABELS, None, r)
    f = fields(t5)["identity"]
    assert f["precision_counts"] == {"wrong": 1, "redundant": 0} and f["accepted_precision"] == 0.0
    assert f["recovery_counts"] == {"wrong_only": 1}
    assert [(c["field"], c["value"], c["outcome"]) for c in t5["totals"]["introduced_ai_errors"]] == [("identity", "WRONG-99", "wrong")]


def test_validated_facts_on_a_no_record_page_are_false_positives():
    lab = labels(reference="absent", revision="absent", decision="n/a")
    r = rows([obs("identity", "WRONG-99"), obs("decision", "approved")])
    t4 = ev4.evaluate(lab, None, r)["totals"]
    assert t4["evidence_introduced_errors"] == [] and not t4["evidence"]
    t5 = evaluate(lab, None, r)["totals"]
    assert sorted((c["field"], c["outcome"]) for c in t5["introduced_ai_errors"]) == [("decision", "fp"), ("identity", "fp")]


def test_a_correct_baseline_does_not_hide_a_wrong_ai_revision_and_decision():
    base = [dict(page=1, reference="X-SD-1", printed_revision="00", status="rejected")]
    r = rows([obs("identity", "X-SD-1"), obs("revision", "09"), obs("decision", "approved")], records=base)
    t4 = ev4.evaluate(LABELS, None, r)["totals"]
    assert t4["evidence"]["revision"]["tp"] == 1 and t4["evidence_introduced_errors"] == []
    t5 = evaluate(LABELS, None, r)["totals"]
    for field in ("revision", "decision"):
        assert t5["evidence"]["fields"][field]["recovery_counts"] == {"recovered_mixed": 1}
        assert t5["evidence"]["fields"][field]["precision_counts"]["wrong"] == 1
    assert sorted((c["field"], c["value"]) for c in t5["introduced_ai_errors"]) == [("decision", "approved"), ("revision", "09")]
    # the raw layer alone (no AI) is clean
    assert t5["raw"]["critical"] == []


def test_two_identities_on_one_page_are_both_kept_and_order_does_not_matter():
    a, b = obs("identity", "WRONG-99"), obs("identity", "X-SD-1")
    t4 = [ev4.evaluate(LABELS, None, rows(order))["totals"]["evidence"]["identity"] for order in ((a, b), (b, a))]
    assert t4[0] != t4[1], ".4 overwrote one identity with the other, so the order changed the result"
    t5 = [evaluate(LABELS, None, rows(order))["totals"] for order in ((a, b), (b, a))]
    assert t5[0]["evidence"]["fields"] == t5[1]["evidence"]["fields"]
    f = t5[0]["evidence"]["fields"]["identity"]
    assert f["precision_counts"]["correct"] == 1 and f["precision_counts"]["wrong"] == 1
    assert f["recovery_counts"] == {"recovered_mixed": 1}


# --- further contracts ---------------------------------------------------------------------------------------------------


def test_permutation_invariance_over_mixed_layers():
    ai = [obs("identity", "X-SD-1"), obs("revision", "00"), obs("decision", "approved"), obs("identity", "OTHER-1", state="candidate")]
    recs = [dict(page=1, reference="X-SD-1", printed_revision="00", status="rejected"),
            dict(page=1, reference="X-SD-1", printed_revision="00", status="rejected")]
    results = {str(evaluate(LABELS, None, rows(list(p), recs))["totals"]["evidence"]["fields"]) for p in itertools.permutations(ai)}
    assert len(results) == 1


def test_redundant_identical_facts_do_not_inflate_recovery_or_precision():
    recs = [dict(page=1, reference="X-SD-1", printed_revision="00", status="rejected")] * 3
    t = evaluate(LABELS, None, rows(records=recs))["totals"]["raw"]["fields"]["identity"]
    assert t["precision_counts"] == {"correct": 1, "redundant": 2} and t["recovery_counts"] == {"recovered_clean": 1}


def test_multiple_components_on_a_page_and_unknown_association():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "cover", "reference": "X-SD-1", "printed_revision": "00", "decision": "rejected"},
        {"page": 1, "component": "reply", "reference": "CR-9", "printed_revision": "01", "decision": "approved"}]}}}
    ai = [obs("identity", "CR-9", component="c1"), obs("decision", "approved", component="c1"),
          obs("identity", "ZZ-404", component="c2"), obs("decision", "rejected", component="c2")]
    t = evaluate(LABELS, pages, rows(ai))["totals"]["evidence"]
    assert t["association"] == {"identity": 1, "unassociated": 1}
    outcomes = sorted((c["field"], c["value"], c["outcome"]) for c in t["critical"])
    # the unknown identity is a wrong identity of no component; its decision is association-unknown, not right or wrong
    assert outcomes == [("identity", "ZZ-404", "wrong_unassociated")]
    assert t["fields"]["decision"]["precision_counts"].get("association_unknown") == 1
    comps = {c["expected"]["component"]: c["fields"] for c in evaluate(LABELS, pages, rows(ai))["documents"][0]["layers"]["evidence"]["components"]}
    assert comps["reply"]["decision"] == "recovered_clean" and comps["cover"]["identity"] == "missed"


def test_held_facts_earn_evidence_credit_only_and_are_never_precision_errors():
    t = evaluate(LABELS, None, rows([obs("identity", "X-SD-1", state="candidate"), obs("revision", "07", state="conflict")]))["totals"]["evidence"]
    assert t["fields"]["identity"]["recovery_counts"] == {"held_only": 1} and t["fields"]["identity"]["asserted_distinct"] == 0
    assert t["fields"]["revision"]["recovery_counts"] == {"missed": 1} and t["critical"] == []


def test_a_known_wrong_identity_on_a_single_component_page_is_wrong_and_judges_its_other_facts():
    t = evaluate(LABELS, None, rows(records=[dict(page=1, reference="Y-SD-7", printed_revision="00", status="approved")]))["totals"]["raw"]
    assert t["association"] == {"single_component_wrong_identity": 1}
    assert sorted((c["field"], c["outcome"]) for c in t["critical"]) == [("decision", "wrong"), ("identity", "wrong")]


def test_conflict_truth_and_unscored_pages():
    t = evaluate(labels(decision="conflict"), None, rows([obs("decision", "approved")]))["totals"]["evidence"]
    assert t["fields"]["decision"]["recovery_counts"] == {"accepted_on_conflict": 1}
    assert [c["outcome"] for c in t["critical"]] == ["accepted_on_conflict"]
    t = evaluate(LABELS, None, rows([obs("identity", "Q-1", page=3)]))["totals"]["evidence"]
    assert t["association"] == {"unscored_page": 1} and t["critical"] == []


def test_retained_stale_ai_evidence_is_not_scored_as_current():
    row = rows()
    row["EP-1/a.pdf"]["extracted"]["ai_evidence"] = {"current": {"stale": "source bytes changed", "observations": [obs("identity", "WRONG-99")]}}
    t = evaluate(LABELS, None, row)["totals"]
    assert t["introduced_ai_errors"] == [] and t["evidence"]["fields"]["identity"]["recovery_counts"] == {"missed": 1}


def test_a_record_held_as_pending_evidence_is_no_register_emission_but_stays_raw_evidence():
    flagged = dict(page=1, reference="X-SD", printed_revision="00", status="rejected", flags=["reference_incomplete"])
    r = rows(records=[flagged])
    t = evaluate(LABELS, None, r)["totals"]
    assert [c["kind"] for c in t["register"]["critical"]] == ["reference: wrong"], "before the guard: filed under the cut key"
    r["EP-1/a.pdf"]["extracted"]["pending_evidence"] = [{"key": "doc:1:p1:r0", "reference_literal": "X-SD"}]
    t = evaluate(LABELS, None, r)["totals"]
    assert t["register"]["critical"] == [] and t["register"]["register"]["reference"]["missed"] == 1
    assert t["raw"]["fields"]["identity"]["recovery_counts"] == {"missed": 1}, "the cut reference is held raw evidence, not a match"


def test_a_cross_page_copy_on_a_no_record_page_associates_and_an_invented_one_is_a_false_positive():
    pages = {"documents": {"EP-1/a.pdf": {"records": [
        {"page": 1, "component": "cover", "reference": "X-SD-1", "printed_revision": "00", "decision": "rejected"}],
        "no_record_pages": {"2": "the reply behind the cover"}}}}
    copy_ = dict(page=2, reference="X-SD-1", printed_revision="00", status="rejected")
    t = evaluate(LABELS, pages, rows(records=[dict(copy_, page=1), copy_]))["totals"]["raw"]
    assert t["critical"] == [] and t["association"] == {"identity": 1, "cross_page": 1}
    t = evaluate(LABELS, pages, rows([obs("identity", "INVENTED-9", page=2), obs("decision", "approved", page=2)]))["totals"]
    assert sorted((c["field"], c["outcome"]) for c in t["introduced_ai_errors"]) == [("decision", "fp"), ("identity", "fp")]
