"""lane_judge_r32: per (pool id, page, field) outcomes; (ORCH-08, A-09 point 4) the EVIDENCED cross-page identity rule
CP-R38 of page_relations_r38. Synthetic truth, plus the frozen reviewed-2 relations (hash-checked) for F001, F009, F016,
F037 -- no prediction: every value offered is a truth string. Run: python -m pytest -q test_lane_judge_r32.py"""
import copy

import pytest

import inputs_r32 as I
import labels_adapter_r32 as A
import lane_judge_r32 as J
import page_relations_r38 as REL
import r32_test_helpers as H

SRC = "D00" * 4          # r32_test_helpers.doc: staged_sha256 = pool id x 4


def two_page_truth(compilation=False, relations=None, identity_resolved=True):
    T = H.truth(n=1, projects=1)
    T["rows"]["D00|2|identity"] = H.row("D00", 2, "identity", "value", "DWG-77")
    T["rows"]["D00|2|revision"] = H.row("D00", 2, "revision", "absent")
    T["rows"]["D00|2|decision"] = H.row("D00", 2, "decision", "absent")
    T["rows"]["D00|3|identity"] = H.row("D00", 3, "identity", "absent")
    T["rows"]["D00|3|revision"] = H.row("D00", 3, "revision", "absent")
    T["rows"]["D00|3|decision"] = H.row("D00", 3, "decision", "absent")
    T["documents"]["D00"]["compilation"] = compilation
    T["documents"]["D00"]["labelled_pages"] = ["1", "2", "3"]
    T["documents"]["D00"]["in_scope_pages"] = 3
    T["documents"]["D00"]["fields"]["identity"]["primary"] = identity_resolved
    T["page_relations"] = relations if relations is not None else {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": []},
                                                                          "3": {"own": None, "related": []}}}
    return T


def judge(T, facts, src=SRC):
    return J.judge_document(T, "D00", {"facts": facts, "source_sha256": src})


def fact(page, field, value, state="accepted"):
    return {"page": str(page), "field": field, "value": value, "state": state}


def test_outcomes_on_a_value_row():
    T = H.truth(n=1, projects=1)
    assert judge(T, [fact(1, "identity", "ID-0")])["fields"]["identity"]["recovery"] == {"recovered_clean": 1}
    assert judge(T, [fact(1, "identity", "ID-0"), fact(1, "identity", "ID-9")])["fields"]["identity"]["recovery"] == {"recovered_mixed": 1}
    assert judge(T, [fact(1, "identity", "ID-9")])["fields"]["identity"]["recovery"] == {"wrong_only": 1}
    assert judge(T, [fact(1, "identity", "ID-0", "held")])["fields"]["identity"]["recovery"] == {"held_only": 1}
    assert judge(T, [])["fields"]["identity"]["recovery"] == {"missed": 1}


def test_precision_counts_distinct_automatic_acceptances_and_observations_are_not_critical():
    T = H.truth(n=1, projects=1)
    j = judge(T, [fact(1, "identity", "ID-0"), fact(1, "identity", "id-0"), fact(1, "identity", "ID-9", "observed")])
    assert j["fields"]["identity"]["accepted"] == {"correct": 1, "wrong": 0}, "a redundant copy is one fact; an observation is no acceptance"
    assert j["fields"]["identity"]["critical"] == [] and j["fields"]["identity"]["recovery"] == {"recovered_mixed": 1}


def test_a_false_positive_on_an_absent_row_is_critical():
    T = two_page_truth()
    j = judge(T, [fact(3, "revision", "02")])
    assert j["fields"]["revision"]["negatives"] == {"tn": 1, "fp": 1} and j["fields"]["revision"]["critical"][0]["outcome"] == "fp"


# ---- ORCH-08 (A-09 point 4): cross-page association only when evidenced ------------------------------------------------
def test_same_file_is_not_evidence_a_copy_on_an_absent_page_without_a_recorded_relationship_is_a_false_positive():
    j = judge(two_page_truth(), [fact(3, "identity", "ID-0")])
    assert j["fields"]["identity"]["negatives"].get("fp") == 1 and j["fields"]["identity"]["critical"][0]["page"] == "3"
    chk = j["rows"][6]["cross_page_checks"][0]
    assert not chk["permitted"] and "no relationship" in chk["why"] and chk["target_page"] == "1"


def test_same_file_is_not_evidence_on_a_value_row_either():
    j = judge(two_page_truth(), [fact(2, "identity", "ID-0")])
    assert [c["page"] for c in j["fields"]["identity"]["critical"]] == ["2"] and j["rows"][3]["cross_page"] == 0


def test_r1_a_value_the_labels_list_on_the_page_is_an_evidenced_association():
    rel = {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": []}, "3": {"own": None, "related": [{"literal": "ID-0", "role": "form template number"}]}}}
    j = judge(two_page_truth(relations=rel), [fact(3, "identity", "ID-0")])
    assert j["fields"]["identity"]["critical"] == [] and j["fields"]["identity"]["negatives"] == {"tn": 1}
    assert j["rows"][6]["cross_page"] == 1 and j["rows"][6]["cross_page_checks"][0]["relationship"] == "R1"


def test_r2_an_enclosure_listed_on_the_package_page_may_carry_the_package_identity():
    rel = {"D00": {"1": {"own": "ID-0", "related": [{"literal": "DWG-77", "role": "listed enclosure"}]}, "2": {"own": "DWG-77", "related": []},
                   "3": {"own": None, "related": []}}}
    j = judge(two_page_truth(relations=rel), [fact(2, "identity", "ID-0")])
    assert j["fields"]["identity"]["critical"] == [] and j["rows"][3]["cross_page_checks"][0]["relationship"] == "R2"
    assert j["fields"]["identity"]["recovery"] == {"missed": 2}, "neither page earns anything from the association"
    rel2 = {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": []}, "3": {"own": None, "related": []}}}
    j1 = judge(two_page_truth(relations=rel2), [fact(1, "identity", "DWG-77")])
    assert [c["page"] for c in j1["fields"]["identity"]["critical"]] == ["1"], "without a listing the cover never takes the enclosure's number"


def test_r3_the_same_document_identity_on_two_pages_permits_the_other_pages_printed_form():
    T = two_page_truth()
    T["rows"]["D00|2|identity"] = H.row("D00", 2, "identity", "value", "ID-0", alternates=("ID-0-Rev.00",))
    T["page_relations"]["D00"]["2"]["own"] = "ID-0"
    j = judge(T, [fact(1, "identity", "ID-0-Rev.00")])
    assert j["fields"]["identity"]["critical"] == [] and j["rows"][0]["cross_page_checks"][0]["relationship"] == "R3"


def test_no_source_hash_or_another_source_gives_no_association():
    rel = {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": []}, "3": {"own": None, "related": [{"literal": "ID-0", "role": "x"}]}}}
    for src in (None, "", "f" * 64):
        j = judge(two_page_truth(relations=rel), [fact(3, "identity", "ID-0")], src=src)
        assert j["fields"]["identity"]["negatives"].get("fp") == 1, src
        assert "source" in j["rows"][6]["cross_page_checks"][0]["why"]


def test_an_unresolved_document_identity_or_a_compilation_gives_no_association():
    rel = {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": []}, "3": {"own": None, "related": [{"literal": "ID-0", "role": "x"}]}}}
    j = judge(two_page_truth(relations=rel, identity_resolved=False), [fact(3, "identity", "ID-0")])
    assert j["fields"]["identity"]["negatives"].get("fp") == 1 and "not resolved" in j["rows"][6]["cross_page_checks"][0]["why"]
    jc = judge(two_page_truth(compilation=True, relations=rel), [fact(3, "identity", "ID-0")])
    assert jc["fields"]["identity"]["negatives"].get("fp") == 1 and "compilation" in jc["rows"][6]["cross_page_checks"][0]["why"]


def test_an_uncertain_or_not_scorable_target_is_no_target():
    rel = {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": []}, "3": {"own": None, "related": [{"literal": "ID-0", "role": "x"}]}}}
    T = two_page_truth(relations=rel)
    T["rows"]["D00|1|identity"] = H.row("D00", 1, "identity", "not_scorable", "ID-0")
    j = judge(T, [fact(3, "identity", "ID-0")])
    assert j["fields"]["identity"]["negatives"].get("fp") == 1 and "no resolved identity" in j["rows"][6]["cross_page_checks"][0]["why"]


def test_a_conflicting_identity_earns_no_recovery_credit_and_a_held_identity_none_either():
    rel = {"D00": {"1": {"own": "ID-0", "related": []}, "2": {"own": "DWG-77", "related": [{"literal": "ID-0", "role": "listed"}]}, "3": {"own": None, "related": []}}}
    T = two_page_truth(relations=rel)
    j = judge(T, [fact(2, "identity", "DWG-77"), fact(2, "identity", "ID-0")])
    assert j["rows"][3]["outcome"] == "recovered_conflict" and j["fields"]["identity"]["critical"] == []
    T1 = H.truth(n=1, projects=1)
    assert judge(T1, [fact(1, "identity", "ID-0", "held")])["fields"]["identity"]["y"] == 0
    jj = judge(T, [fact(1, "identity", "ID-0"), fact(2, "identity", "DWG-77"), fact(2, "identity", "ID-0")])
    assert jj["fields"]["identity"]["y"] == 0, "a document with a conflicting page earns no clean recovery"


def test_cross_page_never_applies_to_revision_or_decision():
    T = two_page_truth()
    j = judge(T, [fact(2, "revision", "01")])
    assert j["fields"]["revision"]["negatives"].get("fp") == 1 and "cross_page_checks" not in j["rows"][4]


def test_negative_decision_words_are_not_decisions():
    T = H.truth(n=1, projects=1)
    j = judge(T, [fact(1, "decision", "UR"), fact(1, "decision", "n/a")])
    assert j["fields"]["decision"]["recovery"] == {"missed": 1} and j["fields"]["decision"]["critical"] == []
    T2 = two_page_truth()
    assert judge(T2, [fact(2, "decision", "UR")])["fields"]["decision"]["negatives"] == {"tn": 2}


def test_y_is_clean_recovery_only():
    T = H.truth(n=1, projects=1)
    assert judge(T, [fact(1, "revision", "1")])["fields"]["revision"]["y"] == 1, "'1' equals '01' by value"
    assert judge(T, [fact(1, "revision", "01"), fact(1, "revision", "02")])["fields"]["revision"]["y"] == 0


# ---- the frozen reference set (relations built from the hash-checked reviewed-2 labels) ---------------------------------
@pytest.fixture(scope="module")
def real():
    x = I.load_all()
    return A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])


def _real(T, pid, facts, src=True):
    return J.judge_document(T, pid, {"facts": facts, "source_sha256": T["documents"][pid]["staged_sha256"] if src else None})


def _lit(T, pid, page):
    return T["rows"][f"{pid}|{page}|identity"]["literal"]


def test_real_relations_are_built_from_the_hash_checked_labels(real):
    rel = REL.relations(real)
    assert rel["F037"]["2"]["related"] == [{"literal": _lit(real, "F037", 3), "role": "listed enclosure"}]
    assert "page_relations" not in real, "the truth file is unchanged (TRUTH-R32 4e237a4e); relations come from the labels"
    assert REL.relations(copy.deepcopy(real) | {"source_version": "something-else"}) == {}, "an unknown truth has no relations: fail closed"


def test_real_f037_the_enclosed_drawing_may_carry_the_package_reference_r2(real):
    j = _real(real, "F037", [fact(3, "identity", _lit(real, "F037", 1))])
    row = next(r for r in j["rows"] if r["page"] == "3" and r["field"] == "identity")
    assert row["cross_page"] == 1 and row["cross_page_checks"][0]["relationship"] == "R2" and j["fields"]["identity"]["critical"] == []


def test_real_f037_the_register_lists_the_enclosure_r1_but_the_cover_does_not(real):
    j2 = _real(real, "F037", [fact(2, "identity", _lit(real, "F037", 3))])
    assert next(r for r in j2["rows"] if r["page"] == "2" and r["field"] == "identity")["cross_page_checks"][0]["relationship"] == "R1"
    j1 = _real(real, "F037", [fact(1, "identity", _lit(real, "F037", 3))])
    assert [c["page"] for c in j1["fields"]["identity"]["critical"]] == ["1"]


def test_real_drawing_set_f016_sheets_never_borrow_each_others_numbers(real):
    j = _real(real, "F016", [fact(2, "identity", _lit(real, "F016", 1))])
    assert [c["page"] for c in j["fields"]["identity"]["critical"]] == ["2"]


def test_real_f001_and_f009_pages_without_identity_never_borrow_the_cover_identity(real):
    j = _real(real, "F001", [fact(2, "identity", _lit(real, "F001", 1))])
    assert j["fields"]["identity"]["negatives"].get("fp") == 1
    j9 = _real(real, "F009", [fact(2, "identity", _lit(real, "F009", 1))])
    assert j9["fields"]["identity"]["negatives"].get("fp") == 1


def test_real_without_the_source_hash_nothing_is_associated(real):
    j = _real(real, "F037", [fact(3, "identity", _lit(real, "F037", 1))], src=False)
    assert [c["page"] for c in j["fields"]["identity"]["critical"]] == ["3"]


def test_the_tripwire_passes_the_source_hash_so_it_judges_like_the_scorer(real):
    import tripwire_r32 as TW
    facts = [fact(3, "identity", _lit(real, "F037", 1))]
    assert TW.tripwire(real, "F037", facts, real["documents"]["F037"]["staged_sha256"])["resolved"] == []
    assert [c["page"] for c in TW.tripwire(real, "F037", facts)["resolved"]] == ["3"], "without the row's hash: no association (fail closed)"


def test_r_and_p_judged_documents_carry_no_credit():
    T = H.truth(n=2, projects=1)
    for name, credit in (("B", "scored"), ("C", "scored"), ("R", "none"), ("P", "none")):
        jl = J.judge_lane(H.lane(name, T, correct=H.all_fields(T)), T)
        assert {d["credit"] for d in jl.values()} == {credit}, name
