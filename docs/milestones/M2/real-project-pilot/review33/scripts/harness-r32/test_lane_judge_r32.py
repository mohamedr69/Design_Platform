"""lane_judge_r32: per (pool id, page, field) outcomes. Synthetic truth only. Run: python -m pytest -q test_lane_judge_r32.py"""
import lane_judge_r32 as J
import r32_test_helpers as H


def two_page_truth(compilation=False):
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
    return T


def judge(T, facts):
    return J.judge_document(T, "D00", {"facts": facts})


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


def test_a_copy_of_the_document_identity_on_an_absent_page_is_not_a_false_positive():
    T = two_page_truth()
    j = judge(T, [fact(3, "identity", "ID-0")])
    assert j["fields"]["identity"]["critical"] == [] and j["fields"]["identity"]["negatives"].get("fp") is None


def test_cross_page_identity_on_a_value_row_follows_evaluator_10_except_on_a_compilation():
    j = judge(two_page_truth(False), [fact(2, "identity", "ID-0")])
    assert j["fields"]["identity"]["critical"] == [] and j["rows"][3]["cross_page"] == 1
    jc = judge(two_page_truth(True), [fact(2, "identity", "ID-0")])
    assert [c["page"] for c in jc["fields"]["identity"]["critical"]] == ["2"], "(h): a compilation page never takes another page's identity"


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
