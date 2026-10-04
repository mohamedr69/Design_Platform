"""concentration_r32 (owner decision A-05): every leg on synthetic results. Run: python -m pytest -q test_concentration_r32.py"""
import concentration_r32 as K
import r32_test_helpers as H


def gains(T, ids, fields=("identity", "revision", "decision")):
    return {pid: set(fields) for pid in T["documents"] if pid in ids}


def test_spread_gain_is_eligible():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, "decision")
    assert r["net_gain"] == 16 and r["outcome"] == "ELIGIBLE" and r["groupings"]["project"]["largest_gain_share"] == 0.25
    assert "do not come mainly from one" in r["attribution_statement"]


def test_project_leg_more_than_half_of_a_net_gain_of_at_least_four():
    T = H.truth(n=16, projects=4)
    ids = [pid for pid, d in T["documents"].items() if d["project"] == "p0"] + ["D01"]
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "identity")
    assert r["net_gain"] == 5 and r["outcome"] == "NOT ELIGIBLE"
    assert any("one project (p0)" in x for x in r["reasons"]) and r["mainly_from"]["project"]["gains_mainly_from"] == "p0"


def test_exactly_half_is_not_concentrated():
    T = H.truth(n=16, projects=4)
    ids = ["D00", "D04", "D01", "D02"]          # p0 holds 2 of 4
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "identity")
    assert r["net_gain"] == 4 and r["outcome"] == "ELIGIBLE"


def test_layout_leg_blocks_a_gain_spread_over_projects_but_from_one_template():
    lay = ["TPL" if i < 8 else f"L{i}" for i in range(16)]
    T = H.truth(n=16, projects=4, layouts=lay)
    ids = [f"D{i:02d}" for i in range(8)] + ["D10", "D12"]
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "decision")
    assert r["groupings"]["project"]["largest_gain_share"] <= 0.5
    assert r["outcome"] == "NOT ELIGIBLE" and any("one layout_key (TPL)" in x for x in r["reasons"])


def test_contractor_leg_when_two_projects_share_a_contractor():
    con = ["K1" if i % 4 in (0, 1) else f"K{i % 4}" for i in range(16)]
    T = H.truth(n=16, projects=4, contractors=con)
    ids = ["D00", "D04", "D08", "D01", "D05", "D02"]     # p0 3, p1 2, p2 1: no project > half; contractor K1 = 5 of 6
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "identity")
    assert r["groupings"]["project"]["largest_gain_share"] == 0.5
    assert r["outcome"] == "NOT ELIGIBLE" and any("one contractor (K1)" in x for x in r["reasons"])
    e = K.evaluate(H.lane("B", T), H.lane("C", T), T)
    assert e["contractor_equals_project"] is False


def test_small_net_gain_is_undetermined_and_reported():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ["D00", "D04", "D08"])), T, "revision")
    assert r["net_gain"] == 3 and r["outcome"] == "UNDETERMINED" and r["reasons"] == [] and r["notes"]
    assert r["mainly_from"]["project"]["gains_mainly_from"] == "p0", "the attribution is still measured"


def test_failures_concentrated_in_one_layout_with_a_negative_group_net_block():
    lay = ["TPL" if i < 3 else f"L{i % 4}" for i in range(16)]
    T = H.truth(n=16, projects=4, layouts=lay)
    B = H.lane("B", T, correct=gains(T, ["D00", "D01", "D02"]))
    C = H.lane("C", T, correct=gains(T, [f"D{i:02d}" for i in range(4, 12)]))
    r = K.field_concentration(B, C, T, "identity")
    assert r["net_gain"] == 5 and r["failures"] == 3
    assert r["outcome"] == "NOT ELIGIBLE" and any("failures (> half) in one layout_key (TPL)" in x for x in r["reasons"])
    assert r["mainly_from"]["layout_key"]["failures_mainly_from"] == "TPL"


def test_a_single_failure_is_never_concentrated():
    T = H.truth(n=16, projects=4)
    B = H.lane("B", T, correct=gains(T, ["D00"]))
    C = H.lane("C", T, correct=gains(T, [f"D{i:02d}" for i in range(1, 9)]))
    r = K.field_concentration(B, C, T, "identity")
    assert r["failures"] == 1 and r["outcome"] == "ELIGIBLE"


def test_any_negative_control_false_acceptance_blocks_decision():
    T = H.truth(n=16, projects=4, negatives=4)
    fa = {"N00": [{"page": "1", "field": "decision", "value": "approved", "state": "accepted"}]}
    C = H.lane("C", T, correct=H.all_fields(T), extra_facts=fa)
    r = K.field_concentration(H.lane("B", T), C, T, "decision")
    assert r["outcome"] == "NOT ELIGIBLE" and any("negative decision controls" in x for x in r["reasons"])
    assert r["decision_controls"]["C"]["negative"] == {"documents": 4, "attempted": 4, "correct": 3, "false_accept": 1,
                                                      "false_accept_documents": ["N00"], "by_stratum": {"drawing_signal": 4}}
    held = {"N00": [{"page": "1", "field": "decision", "value": "approved", "state": "held"},
                    {"page": "1", "field": "decision", "value": "UR", "state": "accepted"}]}
    r2 = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T), extra_facts=held), T, "decision")
    assert r2["decision_controls"]["C"]["negative"]["false_accept"] == 0, "a held value or 'UR' is not a false acceptance"


def test_positive_controls_come_from_review_signal_and_no_stratum_needs_a_positive():
    T = H.truth(n=16, projects=4, negatives=4)
    ctl = K.decision_controls({"B": H.lane("B", T), "C": H.lane("C", T, correct=H.all_fields(T))}, T)
    assert ctl["C"]["positive"] == {"documents": 16, "attempted": 16, "correct": 16, "false_accept": 0, "false_accept_documents": [],
                                    "by_stratum": {"review_signal": 16}}
    assert ctl["B"]["positive"]["correct"] == 0
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, "decision")
    assert r["outcome"] == "ELIGIBLE", "drawing_signal holds no positive and nothing requires one"


def test_decision_type_is_reported_and_never_blocks():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, "decision")
    assert r["groupings"]["decision_type"]["largest_gain_share"] == 1.0 and r["groupings"]["decision_type"]["blocking"] is False
    assert r["outcome"] == "ELIGIBLE"


def test_unattempted_documents_are_not_matched_and_outputs_carry_the_statement():
    T = H.truth(n=16, projects=4)
    C = H.lane("C", T, correct=H.all_fields(T), attempted=set(list(T["documents"])[:10]))
    r = K.field_concentration(H.lane("B", T), C, T, "identity")
    assert r["matched"] == 10 and r["reference_set_statement"].endswith("not human-signed")
    e = K.evaluate(H.lane("B", T), C, T)
    assert e["contractor_equals_project"] is True and e["thresholds"]["min_net_gain"] == 4
