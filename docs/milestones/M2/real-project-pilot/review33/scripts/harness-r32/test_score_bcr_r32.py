"""score_bcr_r32: the Review 31 rules per field, NOT_SCORABLE excluded, per-field tripwire. Synthetic lanes only.
Run: python -m pytest -q test_score_bcr_r32.py"""
import copy

import pytest

import inputs_r32 as I
import labels_adapter_r32 as A
import lane_judge_r32 as J
import r32_test_helpers as H
import score_bcr_r32 as S

CAPS = {"B": 240, "C": 240}
F = H.FIELDS


def ev(B, C, T, R=None, **kw):
    return S.evaluate(B, C, R, T, caps=kw.pop("caps", CAPS), extensions_used=kw.pop("extensions_used", 0), seed="t", **kw)


def test_population_gate_on_the_real_reference_set_is_dispatch_eligible():
    x = I.load_all()
    T = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    g = S.population_gate(T, 0)
    assert g["counts"] == {"identity": 57, "revision": 38, "decision": 38} and g["action"] == "DISPATCH_ELIGIBLE"


def test_population_gate_extends_then_blocks_and_blocked_is_never_a_result():
    T = H.truth(n=8)
    assert S.population_gate(T, 0)["action"] == "EXTEND:extension-1"
    assert S.population_gate(T, 2)["action"] == "PREPARATION BLOCKED"
    r = ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, extensions_used=2)
    assert set(r["outcome_by_field"].values()) == {"PREPARATION BLOCKED"} and r["exercise_only"] and r["default_selected"] is None


def test_all_good_and_spread_gain_is_eligible_per_field_and_never_a_default():
    T = H.truth(n=16, projects=4)
    B = H.lane("B", T, requests=6)
    C = H.lane("C", T, correct=H.all_fields(T), requests=20, inherited=6)
    r = ev(B, C, T)
    assert r["outcome_by_field"] == {f: "ELIGIBLE FOR A SEPARATE SELECTION DECISION" for f in F}, r["fields"]
    assert r["default_selected"] is None and all(v["default_selected"] is None for v in r["fields"].values())
    assert r["reference_set_statement"].startswith("reference set independently AI-reviewed")


def test_fields_are_judged_independently_for_field_level_gates():
    T = H.truth(n=16, projects=4)
    good = {pid: {"identity", "decision"} for pid in T["documents"]}
    for i, pid in enumerate(sorted(T["documents"])):
        if i < 12:
            good[pid].add("revision")
    r = ev(H.lane("B", T), H.lane("C", T, correct=good, requests=10), T)
    assert r["outcome_by_field"]["identity"].startswith("ELIGIBLE")
    assert r["outcome_by_field"]["revision"] == "NOT ELIGIBLE"
    assert any("revision: clean recovery 0.75" in x for x in r["fields"]["revision"]["reasons_not_eligible"])
    assert not any("revision" in x for x in r["fields"]["identity"]["reasons_not_eligible"])


def test_a_critical_in_c_is_attributed_to_its_field_and_document_and_fails_the_candidate():
    T = H.truth(n=16, projects=4)
    good = H.all_fields(T)
    good["D03"] = {"identity", "decision"}
    C = H.lane("C", T, correct=good, wrong={"D03": {"revision"}}, requests=10)
    r = ev(H.lane("B", T), C, T)
    assert [(c["pool_id"], c["field"], c["page"]) for c in r["fields"]["revision"]["critical_resolved_in_C"]] == [("D03", "revision", "1")]
    assert r["fields"]["identity"]["critical_resolved_in_C"] == []
    assert all(v == "NOT ELIGIBLE" for v in r["outcome_by_field"].values()), "the safety gate is candidate-level"
    assert any("revision D03 p1" in x for x in r["fields"]["identity"]["reasons_not_eligible"])


def test_not_scorable_rows_are_excluded_and_their_acceptances_are_unresolved_findings():
    T = H.truth(n=16, projects=4)
    T["rows"]["D05|1|revision"] = H.row("D05", 1, "revision", "not_scorable", literal=None, candidates=["00", "01"])
    T["documents"]["D05"]["fields"]["revision"] = {"resolved_for_scoring": "no", "carries_fact": "no", "primary": False, "has_fact": False}
    extra = {"D05": [{"page": "1", "field": "revision", "value": "07", "state": "accepted"}],
             "D06": []}
    good = H.all_fields(T)
    good["D05"] = {"identity", "decision"}
    C = H.lane("C", T, correct=good, extra_facts=extra, requests=10)
    jd = J.judge_document(T, "D05", C["documents"]["D05"])
    assert jd["fields"]["revision"]["critical"] == [] and jd["fields"]["revision"]["unresolved"][0]["kind"] == "critical_on_unresolved_truth"
    r = ev(H.lane("B", T), C, T)
    m = r["metrics"]["C"]["fields"]["revision"]
    assert m["critical_resolved"] == [] and len(m["critical_unresolved"]) == 1
    assert r["paired"]["revision"]["matched"] == 15, "a document whose field is not resolved is not matched"
    ok = copy.deepcopy(extra)
    ok["D05"][0]["value"] = "01"
    jd2 = J.judge_document(T, "D05", H.lane("C", T, correct=good, extra_facts=ok)["documents"]["D05"])
    assert jd2["fields"]["revision"]["unresolved"][0]["kind"] == "not_scorable_matching"


def test_not_scorable_is_never_a_verified_absence():
    T = H.truth(n=16, projects=4)
    T["rows"]["D02|1|decision"] = H.row("D02", 1, "decision", "not_scorable", literal="B+R?")
    cov = {pid: {"decision": "discovery_absent"} for pid in T["documents"]}
    c = J.coverage_counts(H.lane("C", T, cov=cov), T, "decision")
    assert c["not_scorable"] == 1 and c["verified_absence"] == 0 and c["wrong_absence"] == 15


def test_none_is_not_absent_an_unlabelled_page_fact_is_unscored():
    T = H.truth(n=16, projects=4)
    C = H.lane("C", T, extra_facts={"D00": [{"page": "5", "field": "identity", "value": "X", "state": "accepted"}]})
    jd = J.judge_document(T, "D00", C["documents"]["D00"])
    assert jd["unscored_facts"] == 1 and jd["fields"]["identity"]["critical"] == []


def test_request_gate_equal_caps_only_and_one_fact_per_eight():
    T = H.truth(n=16, projects=4)
    B = H.lane("B", T, requests=6)
    C = H.lane("C", T, correct={pid: {"identity"} for pid in T["documents"]}, requests=100, inherited=6)
    jB, jC = J.judge_lane(B, T), J.judge_lane(C, T)
    g = S.request_gate(B, C, T, CAPS, "t", jB, jC)
    assert g["requests"] == {"B": 6, "C": 106} and g["extra_requests"] == 100 and g["net_correct_facts"] == 16 and g["passes"]
    C2 = H.lane("C", T, correct={pid: {"identity"} for pid in T["documents"]}, requests=200, inherited=6)
    assert not S.request_gate(B, C2, T, CAPS, "t", jB, J.judge_lane(C2, T))["passes"]
    na = S.request_gate(B, C, T, {"B": 16, "C": 240}, "t", jB, jC)
    assert na["applicable"] is False and "R31-03" in na["reason"]


def test_stop_states_override_every_field():
    T = H.truth(n=16, projects=4)
    B, C = H.lane("B", T), H.lane("C", T, correct=H.all_fields(T))
    assert set(ev(B, C, T, stop_state={"comparison": "INVALID: x"})["outcome_by_field"].values()) == {"INVALID"}
    assert set(ev(B, C, T, stop_state={"comparison": "INCOMPLETE: x"})["outcome_by_field"].values()) == {"INCOMPLETE"}
    r = ev(B, C, T, stop_state={"comparison": "RESULT: candidate failed"})
    assert set(r["outcome_by_field"].values()) == {"NOT ELIGIBLE"}


def test_decision_coverage_gate_binds_only_the_decision_field():
    T = H.truth(n=16, projects=4)
    none = {pid: {"decision": "located_incomplete"} for pid in T["documents"]}
    B = H.lane("B", T)
    C = H.lane("C", T, correct=H.all_fields(T), cov=none, requests=10)
    R = H.lane("R", T)
    r = ev(B, C, T, R=R)
    assert not r["decision_coverage_gate"]["passes"]
    assert "decision coverage of C below B or R" in r["fields"]["decision"]["reasons_not_eligible"]
    assert r["outcome_by_field"]["identity"].startswith("ELIGIBLE")


def test_stratum_concentration_no_longer_blocks_decision():
    T = H.truth(n=16, projects=4)          # every document review_signal: the R33-01 situation
    r = ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T), requests=10), T)
    assert r["concentration"]["fields"]["decision"]["groupings"]["stratum"]["largest_gain_share"] == 1.0
    assert r["outcome_by_field"]["decision"].startswith("ELIGIBLE")


def test_aliases_are_never_matched():
    T = H.truth(n=16, projects=4)
    T["documents"]["D15"]["is_alias"] = True
    r = ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T)
    assert "D15" not in r["paired"]["identity"]["matched_documents"] and r["paired"]["identity"]["matched"] == 15


def test_the_bootstrap_is_seeded():
    T = H.truth(n=16, projects=4)
    B, C = H.lane("B", T), H.lane("C", T, correct={pid: {"identity"} for pid in list(T["documents"])[:9]})
    jB, jC = J.judge_lane(B, T), J.judge_lane(C, T)
    assert S.paired(B, C, T, "identity", "s", jB, jC) == S.paired(B, C, T, "identity", "s", jB, jC)


@pytest.mark.parametrize("n_gain,excludes_zero", [(3, False), (4, True)])
def test_net_gain_four_is_the_smallest_whose_interval_can_exclude_zero(n_gain, excludes_zero):
    diffs = {"p": [1] * n_gain + [0] * (16 - n_gain)}
    bt = S.bootstrap(diffs, "m2-r30-bootstrap-2026-10-02")
    assert (bt["ci95"][0] > 0) is excludes_zero
