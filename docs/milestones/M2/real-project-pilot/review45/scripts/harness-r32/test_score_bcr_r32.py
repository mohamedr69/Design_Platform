"""score_bcr_r32: the Review 31 rules per field, NOT_SCORABLE excluded, per-field tripwire, and (Review 34 RC-2 / R34-02)
ONE candidate-level outcome; (RC-1) the project-stratified bootstrap that justifies the concentration rule without a floor;
(RC-6) one wrong acceptance is one failure. Synthetic lanes only (Review 34's scenarios use the real truth and run set,
with lanes made from the truth). Run: python -m pytest -q test_score_bcr_r32.py"""
import copy

import pytest

import inputs_r32 as I
import labels_adapter_r32 as A
import lane_judge_r32 as J
import r32_test_helpers as H
import r34_scenarios as SC
import score_bcr_r32 as S

ELIGIBLE = "ELIGIBLE FOR A SEPARATE SELECTION DECISION"

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
    assert r["outcome"] == "PREPARATION BLOCKED", "the comparison state is the candidate outcome"
    r1 = ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, extensions_used=0)
    assert r1["outcome"] == "NOT DISPATCHABLE (EXTEND:extension-1)" and set(r1["outcome_by_field"].values()) == {r1["outcome"]}


def test_all_good_and_spread_gain_is_eligible_for_every_field_and_the_candidate_and_never_a_default():
    T = H.truth(n=16, projects=4)
    B = H.lane("B", T, requests=6)
    C = H.lane("C", T, correct=H.all_fields(T), requests=20, inherited=6)
    r = ev(B, C, T)
    assert r["outcome_by_field"] == {f: ELIGIBLE for f in F}, r["fields"]
    assert r["outcome"] == ELIGIBLE and r["candidate"]["basis"] == "all three fields ELIGIBLE" and r["candidate"]["fields_not_eligible"] == []
    assert r["default_selected"] is None and all(v["default_selected"] is None for v in r["fields"].values())
    assert r["reference_set_statement"].startswith("reference set independently AI-reviewed")


def test_field_outcomes_are_diagnostics_and_the_candidate_outcome_is_conjunctive():
    """RC-2: revision clean recovery 0.75 makes revision NOT ELIGIBLE; identity and decision stay ELIGIBLE as diagnostics,
    and the candidate (one switch set) is NOT ELIGIBLE."""
    T = H.truth(n=16, projects=4)
    good = {pid: {"identity", "decision"} for pid in T["documents"]}
    for i, pid in enumerate(sorted(T["documents"])):
        if i < 12:
            good[pid].add("revision")
    r = ev(H.lane("B", T), H.lane("C", T, correct=good, requests=10), T)
    assert r["outcome_by_field"]["identity"] == ELIGIBLE and r["outcome_by_field"]["decision"] == ELIGIBLE
    assert r["outcome_by_field"]["revision"] == "NOT ELIGIBLE"
    assert any("revision: clean recovery 0.75" in x for x in r["fields"]["revision"]["reasons_not_eligible"])
    assert not any("revision" in x for x in r["fields"]["identity"]["reasons_not_eligible"])
    assert r["outcome"] == "NOT ELIGIBLE" and r["candidate"]["fields_not_eligible"] == ["revision"]
    assert "revision" in r["candidate"]["reasons_not_eligible"] and r["fields"]["identity"]["role"].startswith("diagnostic")


@pytest.mark.parametrize("fields,expected", [
    ({"identity": ELIGIBLE, "revision": ELIGIBLE, "decision": ELIGIBLE}, ELIGIBLE),
    ({"identity": ELIGIBLE, "revision": ELIGIBLE, "decision": "NOT ELIGIBLE"}, "NOT ELIGIBLE"),
    ({"identity": "INCOMPLETE", "revision": ELIGIBLE, "decision": ELIGIBLE}, "INCOMPLETE"),
    ({"identity": "INCOMPLETE", "revision": "NOT ELIGIBLE", "decision": ELIGIBLE}, "NOT ELIGIBLE"),
    ({"identity": "INCOMPLETE", "revision": "NOT ELIGIBLE", "decision": "INVALID"}, "INVALID"),
    ({"identity": "INVALID", "revision": ELIGIBLE, "decision": ELIGIBLE}, "INVALID"),
])
def test_candidate_precedence_invalid_over_not_eligible_over_incomplete(fields, expected):
    assert S.candidate_outcome(fields)["outcome"] == expected
    assert S.CANDIDATE_PRECEDENCE == ("INVALID", "NOT ELIGIBLE", "INCOMPLETE")


@pytest.fixture(scope="module")
def real():
    T, run = SC.load()
    return T, run, SC.build(T, run)


def _ev_real(real, name):
    T, run, sc = real
    B, C, R, stop, _ = sc[name]
    return S.evaluate(B, C, R, T, caps=CAPS, extensions_used=0, stop_state=stop, docs=set(run))


def test_s5_decision_recovery_0_7576_makes_the_candidate_not_eligible(real):
    """Review 34 S5: identity gain 8; B and C both miss three decision documents (C decision clean recovery 0.7576)."""
    r = _ev_real(real, "S5 identity gain 8 and decision recovery below 0.90")
    assert r["metrics"]["C"]["fields"]["decision"]["clean_recovery"] == 0.7576
    assert r["outcome_by_field"] == {"identity": ELIGIBLE, "revision": ELIGIBLE, "decision": "NOT ELIGIBLE"}
    assert r["outcome"] == "NOT ELIGIBLE" and r["candidate"]["fields_not_eligible"] == ["decision"]
    assert r["default_selected"] is None


def test_s3b_and_s3c_concentrated_decision_gains_make_the_candidate_not_eligible(real):
    for name in ("S3b decision gain 3 inside EP-27331", "S3c decision gain 4 inside EP-27331", "S3a decision gain 2 inside one project"):
        r = _ev_real(real, name)
        assert r["outcome_by_field"]["decision"] == "NOT ELIGIBLE" and r["outcome"] == "NOT ELIGIBLE", name
        assert any(x.startswith("concentration: decision:") for x in r["fields"]["decision"]["reasons_not_eligible"]), name


def test_s4b_incomplete_and_spread_gain_reach_their_candidate_outcomes(real):
    assert _ev_real(real, "S4b as S4a with the comparison INCOMPLETE")["outcome"] == "INCOMPLETE"
    assert _ev_real(real, "S4a C does not attempt five decision documents")["outcome"] == "NOT ELIGIBLE"
    r = _ev_real(real, "S3c-spread decision gain 4 over four projects")
    assert r["outcome"] == ELIGIBLE, "ELIGIBLE stays reachable on the real run set when the gain is spread"


def test_s1_one_wrong_acceptance_is_exactly_one_failure_and_fails_the_candidate(real):
    """RC-6: one wrong revision acceptance (that also loses the fact) is ONE failure; the candidate-level safety gate fails."""
    r = _ev_real(real, "S1 one wrong revision acceptance in C")
    c = r["concentration"]["fields"]["revision"]
    assert c["failures"] == 1 and len(c["failure_documents"]) == 1 and c["failure_documents"][0]["kinds"] == ["wrong_acceptance", "lost_fact"]
    assert len(r["metrics"]["C"]["critical"]["resolved"]) == 1 and r["outcome"] == "NOT ELIGIBLE"


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
    r = ev(B, C, T, stop_state={"comparison": "INVALID: x"})
    assert set(r["outcome_by_field"].values()) == {"INVALID"} and r["outcome"] == "INVALID"
    r = ev(B, C, T, stop_state={"comparison": "INCOMPLETE: x"})
    assert set(r["outcome_by_field"].values()) == {"INCOMPLETE"} and r["outcome"] == "INCOMPLETE"
    r = ev(B, C, T, stop_state={"comparison": "RESULT: candidate failed"})
    assert set(r["outcome_by_field"].values()) == {"NOT ELIGIBLE"} and r["outcome"] == "NOT ELIGIBLE"


def test_decision_coverage_gate_binds_only_the_decision_field():
    """ORCH-08 (A-09 point 6): the GATE is C >= B; R is no longer part of it (see the R tests below)."""
    T = H.truth(n=16, projects=4)
    none = {pid: {"decision": "located_incomplete"} for pid in T["documents"]}
    B = H.lane("B", T)
    C = H.lane("C", T, correct=H.all_fields(T), cov=none, requests=10)
    r = ev(B, C, T)
    assert not r["decision_coverage_gate"]["passes"] and "R" not in r["decision_coverage_gate"]
    assert "decision coverage of C below B" in r["fields"]["decision"]["reasons_not_eligible"]
    assert r["outcome_by_field"]["identity"].startswith("ELIGIBLE")
    assert r["outcome"] == "NOT ELIGIBLE", "the decision coverage gate fails the candidate"


def test_stratum_concentration_no_longer_blocks_decision():
    T = H.truth(n=16, projects=4)          # every document review_signal: the R33-01 situation
    r = ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T), requests=10), T)
    assert r["concentration"]["fields"]["decision"]["groupings"]["stratum"]["largest_gain_share"] == 1.0
    assert r["outcome_by_field"]["decision"].startswith("ELIGIBLE") and r["outcome"] == ELIGIBLE


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


RUN_SET_DECISION_STRATA = {"EP-27331": 6, "EP-22349": 2, "EP-26687": 3, "EP-3563": 3, "EP-29255": 2}   # 16 matched (run set)


def _strata(gained):
    return {p: [1] * gained.get(p, 0) + [0] * (n - gained.get(p, 0)) for p, n in RUN_SET_DECISION_STRATA.items()}


@pytest.mark.parametrize("gained,ci95", [({"EP-22349": 2}, [0.125, 0.125]), ({"EP-27331": 3}, None), ({"EP-27331": 4}, None)])
def test_the_project_stratified_bootstrap_excludes_zero_for_a_gain_concentrated_in_one_project(gained, ci95):
    """RC-1 justification (replaces version 1's refuted 'net gain 4 is the smallest whose interval can exclude zero'): the
    scorer's bootstrap resamples documents WITHIN each project, so a gain that fills or dominates one project has little
    or no resampling variance; its interval excludes zero at net 2 (S3a) and net 3 (S3b). The interval therefore cannot
    protect against a concentrated gain -- the concentration legs must apply at every size."""
    bt = S.bootstrap(_strata(gained), "m2-r30-bootstrap-2026-10-02:decision")
    assert bt["stratified_by"] == "project" and bt["ci95"][0] > 0, bt
    if ci95:
        assert bt["ci95"] == ci95


def test_version_one_floor_rested_on_an_unstratified_bootstrap_that_the_scorer_does_not_use():
    seed = "m2-r30-bootstrap-2026-10-02"
    one_group = S.bootstrap({"p": [1] * 3 + [0] * 13}, seed)
    stratified = S.bootstrap(_strata({"EP-27331": 3}), seed)
    assert one_group["ci95"][0] == 0, "version 1's test: one unstratified group, net 3 -> includes zero"
    assert stratified["ci95"][0] > 0, "the scorer's project-stratified bootstrap, net 3 inside one project -> excludes zero"
    single = S.bootstrap({"A": [1], "B": [0] * 15}, seed)
    assert single["ci95"] == [0.0625, 0.0625], "a gain of ONE in a one-document project is 'established' by the stratified interval"


# ---- ORCH-08 (A-09 point 6, R38-09): R and P earn no credit and never decide the candidate ------------------------------
def _strip(r):
    """The candidate-relevant part of a result (everything B and C decide)."""
    return {"outcome": r["outcome"], "outcome_by_field": r["outcome_by_field"], "fields": r["fields"], "paired": r["paired"],
            "request_gate": r["request_gate"], "decision_coverage_gate": r["decision_coverage_gate"], "concentration": r["concentration"],
            "metrics": r["metrics"], "comparison_state": r["comparison_state"]}


def _truncate(lane, keep):
    out = copy.deepcopy(lane)
    for pid, d in out["documents"].items():
        if pid not in keep:
            d.update(facts=[], attempted=False, coverage={}, status="INCOMPLETE", status_classes=["limit"], status_reason="lane R stopped (truncated)")
    return out


@pytest.mark.parametrize("c_cov", ["completed_read", "located_incomplete"])
def test_a_full_r_a_truncated_r_and_no_r_give_the_identical_candidate_outcome(c_cov):
    T = H.truth(n=16, projects=4)
    B = H.lane("B", T, requests=6)
    C = H.lane("C", T, correct=H.all_fields(T), cov={pid: {"decision": c_cov} for pid in T["documents"]}, requests=20, inherited=6)
    full_r = H.lane("R", T, correct=H.all_fields(T))                      # R reads everything
    trunc_r = _truncate(full_r, keep={"D00", "D01"})                    # R stopped after two documents
    results = [ev(B, C, T, R=x) for x in (None, full_r, trunc_r, H.lane("R", T))]
    assert all(_strip(x) == _strip(results[0]) for x in results), "the candidate outcome never reads R"
    assert results[0]["candidate"]["reads_lanes"] == ["B", "C"] and "R" not in results[1]["metrics"]


def test_the_c_ge_r_contrast_is_a_diagnostic_and_incomplete_when_r_is_truncated():
    T = H.truth(n=16, projects=4)
    B, C = H.lane("B", T), H.lane("C", T, correct=H.all_fields(T), cov={pid: {"decision": "located_incomplete"} for pid in T["documents"]})
    full_r = H.lane("R", T, correct=H.all_fields(T))
    full = ev(B, C, T, R=full_r)["diagnostics"]["R"]
    assert full["state"] == "COMPLETE" and full["C_ge_R_decision_coverage"]["holds"] is False and full["credit"].startswith("none")
    trunc = ev(B, C, T, R=_truncate(full_r, keep={"D00"}))["diagnostics"]["R"]
    assert trunc["state"] == "INCOMPLETE" and trunc["C_ge_R_decision_coverage"]["state"] == "INCOMPLETE"
    assert trunc["C_ge_R_decision_coverage"]["holds"] is None, "a truncated R never 'passes' the contrast"
    assert len(trunc["not_complete"]) == 15
    none = ev(B, C, T)["diagnostics"]
    assert none["R"]["state"] == "INCOMPLETE" and none["P"]["state"] == "INCOMPLETE"


def test_r_or_p_can_never_stand_in_for_b_or_c():
    T = H.truth(n=16, projects=4)
    with pytest.raises(ValueError, match="R or P can never stand in"):
        ev(H.lane("B", T), H.lane("R", T, correct=H.all_fields(T)), T)
    with pytest.raises(ValueError, match="R or P can never stand in"):
        ev(H.lane("P", T), H.lane("C", T), T)


def test_a_truncated_probe_is_an_incomplete_diagnostic_without_credit():
    T = H.truth(n=16, projects=4)
    P = {"sampled": 3, "of": 20, "population_state": "DEFERRED", "rows": [{"seq": 1, "status": "COMPLETE"}, {"seq": 2, "status": "DEFERRED"}]}
    d = ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, P=P)["diagnostics"]["P"]
    assert d["state"] == "DEFERRED" and d["credit"].startswith("none") and d["items_not_complete"] == [{"seq": 2, "status": "DEFERRED"}]


# ---- ORCH-08 (A-09 point 1): limit refusals and deferrals are INCOMPLETE and visible, never dropped -------------------------
def _limit(lane, pid, status="INCOMPLETE", cls="limit"):
    out = copy.deepcopy(lane)
    out["documents"][pid].update(status=status, status_classes=[cls], status_reason=f"{cls} test", limit_kinds=["lane_allowance"], limit_pages=["*"],
                                 retry_at_utc="2026-10-04T00:00:00+00:00" if status == "DEFERRED" else None)
    return out


def test_a_limit_incomplete_or_deferred_c_document_makes_the_comparison_incomplete_and_stays_in_the_denominators():
    T = H.truth(n=16, projects=4)
    B, C = H.lane("B", T, requests=6), H.lane("C", T, correct=H.all_fields(T), requests=20, inherited=6)
    assert ev(B, C, T)["outcome"] == ELIGIBLE
    for status in ("INCOMPLETE", "DEFERRED"):
        r = ev(B, _limit(C, "D03", status), T)
        assert r["outcome"] == "INCOMPLETE" and r["comparison_state"] == "INCOMPLETE", status
        assert "D03" in r["matched_exclusions"] and r["paired"]["identity"]["matched"] == 15 and r["matched_before_exclusions"]["identity"] == 16
        cov = r["metrics"]["C"]["fields"]["decision"]["coverage_resolved"]
        assert cov["pages"] == 16 and cov["status_rows"] == {f"{status.lower()}_document_rows": 1}, "the document stays in the denominator"
        assert r["metrics"]["C"]["fields"]["identity"]["readable"] == 16
        key = "deferred" if status == "DEFERRED" else "limit_incomplete"
        assert "D03" in r["limit_incomplete"]["C"][key]
        assert ("1 B/C document(s) DEFERRED" if status == "DEFERRED" else "1 INCOMPLETE by a limit") in r["comparison_detail"]


def test_a_failure_or_arm_policy_incomplete_document_is_visible_but_not_a_comparison_state():
    T = H.truth(n=16, projects=4)
    B, C = H.lane("B", T, requests=6), H.lane("C", T, correct=H.all_fields(T), requests=20, inherited=6)
    for cls in ("failure", "arm_policy"):
        r = ev(B, _limit(C, "D03", cls=cls), T)
        assert r["outcome"] == ELIGIBLE and r["limit_incomplete"]["C"]["other_incomplete"]["D03"]["classes"] == [cls]
        assert r["matched_exclusions"] == {}


def test_a_limit_in_b_makes_the_comparison_incomplete_too():
    T = H.truth(n=16, projects=4)
    r = ev(_limit(H.lane("B", T), "D07"), H.lane("C", T, correct=H.all_fields(T)), T)
    assert r["outcome"] == "INCOMPLETE" and "D07" in r["matched_exclusions"]


def test_a_document_missing_from_a_lane_is_counted_missed_never_dropped():
    T = H.truth(n=16, projects=4)
    C = H.lane("C", T, correct=H.all_fields(T))
    del C["documents"]["D05"]
    m = S.lane_metrics(C, T)["fields"]["identity"]
    assert m["readable"] == 16 and m["documents_absent_from_lane_counted_missed"] == ["D05"] and m["recovery_counts"]["missed"] == 1


# ---- ORCH-08 (A-09 point 5): the unsupported-control shortfall is a declared limitation that never disappears --------------
def test_the_scope_limitation_and_what_is_not_claimed_are_in_every_result():
    T = H.truth(n=16, projects=4)
    for r in (ev(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T), ev(H.lane("B", T), H.lane("C", T), T, stop_state={"comparison": "INVALID: x"}),
              ev(H.lane("B", T), H.lane("C", T), T, extensions_used=2)):
        assert [s["id"] for s in r["scope_limitations"]] == ["unsupported-control-shortfall"]
        assert r["scope_limitations"][0]["required"] == 2 and r["scope_limitations"][0]["found"] == 0
        assert any("unsupported-format safety" in x for x in r["not_claimed"]) and any("generalization" in x for x in r["not_claimed"])
    import inspect
    assert "scope" not in str(inspect.signature(S.evaluate)) and "limitation" not in str(inspect.signature(S.evaluate)), "no argument removes it"
    text = S.report_template(r)
    assert "unsupported-control-shortfall" in text and "unsupported-format safety" in text and "generalization" in text
    assert "not human-signed" in text


def test_the_real_scenarios_keep_their_outcomes_with_r_removed_from_the_gate(real):
    """Review 34's scenarios on the real run set: outcomes unchanged by the R / P changes (their R is None)."""
    assert _ev_real(real, "S5 identity gain 8 and decision recovery below 0.90")["outcome"] == "NOT ELIGIBLE"
    assert _ev_real(real, "S3c-spread decision gain 4 over four projects")["outcome"] == ELIGIBLE


# ---- ORCH-08C (R39-15) and owner ruling A-10: the gate is C >= B only (a change from plan v2); C >= R a mandatory diagnostic ---
def test_the_bound_gate_is_one_named_constant_c_ge_b_only_and_is_stated_as_a_change_from_plan_v2():
    assert S.DECISION_COVERAGE_GATE == "C_GE_B_ONLY" and set(S.DECISION_COVERAGE_GATE_DEFINITIONS) == {"C_GE_B_ONLY"}
    g = S.DECISION_COVERAGE_GATE_DEFINITIONS[S.DECISION_COVERAGE_GATE]
    assert g["reads_R"] is False and "A-10" in g["status"] and "plan v2" in g["change_from_plan_v2"] and "never an unchanged gate" in g["status"]
    assert "MANDATORY diagnostic" in g["text"] and "never" in g["text"]
    t = S.report_template({})
    assert "Decision coverage gate (CHANGED from plan v2; owner ruling A-10)" in t and "This is not an unchanged gate" in t
    assert "C >= R decision coverage (MANDATORY diagnostic; never an eligibility input; no credit)" in t and "missing coverage" in t


def _gate_lanes():
    T = H.truth(n=16, projects=4)
    ids = sorted(T["documents"])
    B = H.lane("B", T, correct=H.all_fields(T), cov={pid: {"decision": "located_incomplete"} for pid in ids})          # B coverage 0
    C = H.lane("C", T, correct=H.all_fields(T), cov={pid: {"decision": "completed_read" if i % 2 == 0 else "located_incomplete"}
                                                     for i, pid in enumerate(ids)})                                  # C coverage 8 of 16
    R = H.lane("R", T, correct=H.all_fields(T), cov={pid: {"decision": "completed_read"} for pid in ids})              # R coverage 16 of 16
    return T, B, C, R


def test_r_is_refused_as_an_eligibility_input_by_the_scorer_and_the_gate_never_reads_r():
    T, B, C, R = _gate_lanes()
    for bad in ("C_GE_B_AND_C_GE_R", "C_GE_R_ONLY"):
        with pytest.raises(ValueError, match="refused"):
            ev(B, C, T, R=R, gate_definition=bad)
    with pytest.raises(ValueError, match="binds R into eligibility"):
        S.decision_coverage_gate(B, C, T, definition="C_GE_B_AND_C_GE_R")
    only = ev(B, C, T, R=R)
    g = only["decision_coverage_gate"]
    assert g["definition"] == "C_GE_B_ONLY" and g["passes"] is True and g["reads_lanes"] == ["B", "C"] and "R" not in g
    assert only["candidate"]["reads_lanes"] == ["B", "C"]
    assert ev(B, C, T, R=_truncate(R, keep={"D00"}))["decision_coverage_gate"] == g == ev(B, C, T)["decision_coverage_gate"], "R never reads into it"
    hiB, loC = {**copy.deepcopy(C), "lane": "B"}, {**copy.deepcopy(B), "lane": "C"}
    low = ev(hiB, loC, T, R=R)
    assert low["decision_coverage_gate"]["passes"] is False and "decision coverage of C below B" in low["fields"]["decision"]["reasons_not_eligible"]


def test_the_c_ge_r_diagnostic_is_mandatory_with_counts_missing_coverage_per_document_and_reasons():
    T, B, C, R = _gate_lanes()
    full = ev(B, C, T, R=R)["decision_coverage_C_ge_R"]
    assert full["mandatory"] is True and full["determines_eligibility"] is False and full["credit"] == "none" and "plan v2" in full["change_from_plan_v2"]
    assert full["state"] == "COMPLETE" and full["coverage"] == {"C": 8, "R": 16} and full["holds"] is False
    assert full["counts"]["C"]["completed_read"] == 8 and full["counts"]["R"]["completed_read"] == 16
    assert len(full["missing_coverage"]) == 8 and full["C_missing_where_R_covered"] == sorted(full["missing_coverage"])
    p = next(iter(full["missing_coverage"].values()))["pages"]["1"]
    assert p["C"] == "located_incomplete" and not p["C_covered"] and "located but not read" in p["C_reason"] and p["R_covered"]
    trunc = ev(B, C, T, R=_truncate(R, keep={"D00"}))["decision_coverage_C_ge_R"]
    assert trunc["state"] == "INCOMPLETE" and trunc["holds"] is None and len(trunc["why_incomplete"]) == 15 and "truncated" in trunc["why_incomplete"][0]
    none = ev(B, C, T)["decision_coverage_C_ge_R"]
    assert none["state"] == "INCOMPLETE" and none["counts"]["R"] is None and none["why_incomplete"] == ["lane R did not run in this invocation"]
    assert len(none["missing_coverage"]) == 16, "every document: R did not run; C's own gaps are named too"
    t = S.report_template(ev(B, C, T, R=R))
    assert "State: COMPLETE" in t and "D01 p1: C located_incomplete" in t, "the report renders the counts and the per-document reasons"


def test_every_scorer_result_carries_the_mandatory_diagnostic_and_the_other_gates_are_unchanged():
    T, B, C, R = _gate_lanes()
    for x in (ev(B, C, T), ev(B, C, T, R=R), ev(B, C, T, R=_truncate(R, keep=set()))):
        assert "decision_coverage_C_ge_R" in x and "request_gate" in x and "concentration" in x and x["thresholds"] == S.THRESHOLDS
    assert S.THRESHOLDS == {"accepted_precision_min": 0.98, "clean_recovery_min": 0.90, "critical_on_resolved_max": 0, "facts_per_extra_requests": 8}
