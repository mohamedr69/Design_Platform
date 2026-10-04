"""R31-02 / R31-03 / R30-04 scorer contract on synthetic lanes. Run: python -m pytest -q test_score_bcr.py (cwd harness)."""
import score_bcr as S

F = ("identity", "revision", "decision")


def labels(n=14, projects=7, decision=True, resolved=True, reviewed=True):
    docs = {}
    for i in range(n):
        docs[f"d{i}"] = {"project": f"p{i % projects}", "stratum": f"s{i % 3}", "resolved": resolved, "independent_review": reviewed,
                         "in_scope_pages": 1, "facts": {"1": {"identity": f"ID-{i}", "revision": "A", "decision": "A" if decision else None}}}
    return {"documents": docs}


def lane(name, L, clean=(), wrong=(), crit=(), requests=0, inherited=0, cov=None):
    docs = {}
    for doc in L["documents"]:
        rec = {}
        for f in F:
            if (doc, f) in clean:
                rec[f] = {"recovered_clean": 1}
            elif (doc, f) in wrong:
                rec[f] = {"wrong_only": 1}
            else:
                rec[f] = {"missed": 1}
        acc = {f: {"correct": int((doc, f) in clean), "wrong": int((doc, f) in wrong)} for f in F}
        docs[doc] = {"attempted": True, "unsupported": False, "recovery": rec, "accepted": acc,
                     "critical": [{"page": 1, "field": f, "outcome": "wrong"} for (d, f) in crit if d == doc],
                     "coverage": {"1": (cov or {}).get(doc, {f: "completed_read" for f in F})}}
    return {"lane": name, "documents": docs, "requests": {"own_dispatched": requests, "inherited_from_b": inherited}}


def all_clean(L):
    return {(d, f) for d in L["documents"] for f in F}


def test_population_gate_needs_twelve_for_every_field_then_extends_then_blocks():
    L = labels(n=14, decision=False)
    assert S.population_gate(L, 0)["action"] == "EXTEND:extension-1"
    assert S.population_gate(L, 1)["action"] == "EXTEND:extension-2"
    assert S.population_gate(L, 2)["action"] == "PREPARATION BLOCKED"
    assert S.population_gate(labels(n=12), 0)["action"] == "DISPATCH_ELIGIBLE"
    assert S.population_gate(labels(n=11), 0)["short"] == {f: 11 for f in F}


def test_unreviewed_or_unresolved_labels_never_count():
    assert S.population_gate(labels(n=20, reviewed=False), 2)["action"] == "PREPARATION BLOCKED"
    assert S.population_gate(labels(n=20, resolved=False), 0)["counts"] == {f: 0 for f in F}


def test_a_blocked_population_is_never_a_result():
    L = labels(n=8)
    B, C = lane("B", L), lane("C", L, clean=all_clean(L), requests=40)
    r = S.evaluate(B, C, None, L, caps={"B": 240, "C": 240}, extensions_used=2, seed="t")
    assert r["outcome"] == "PREPARATION BLOCKED" and r["exercise_only"] and r["default_selected"] is None


def test_the_request_gate_is_not_applicable_at_unequal_caps():
    L = labels()
    g = S.request_gate(lane("B", L), lane("C", L, clean=all_clean(L), requests=10), L, {"B": 16, "C": 240}, "t")
    assert g["applicable"] is False and g["passes"] is False and "R31-03" in g["reason"]


def test_the_request_gate_counts_inherited_requests_and_needs_one_fact_per_eight():
    L = labels()
    B = lane("B", L, requests=6)
    C = lane("C", L, clean={(d, "identity") for d in L["documents"]}, requests=100, inherited=6)
    g = S.request_gate(B, C, L, {"B": 240, "C": 240}, "t")
    assert g["requests"] == {"B": 6, "C": 106} and g["extra_requests"] == 100 and g["net_correct_facts"] == 14
    assert g["passes"] is True and g["facts_per_8_extra"] == 1.12
    C2 = lane("C", L, clean={(d, "identity") for d in L["documents"]}, requests=200, inherited=6)
    assert S.request_gate(B, C2, L, {"B": 240, "C": 240}, "t")["passes"] is False, "14 facts for 200 extra requests is below 1 per 8"


def test_a_new_false_acceptance_fails_the_request_gate():
    L = labels()
    C = lane("C", L, clean=all_clean(L) - {("d0", "identity")}, wrong={("d0", "identity")}, crit={("d0", "identity")}, requests=10)
    g = S.request_gate(lane("B", L), C, L, {"B": 240, "C": 240}, "t")
    assert g["new_false_accepts"] and g["passes"] is False


def test_wrong_absences_are_never_decision_coverage():
    L = labels()
    absent = {d: {"identity": "completed_read", "revision": "completed_read", "decision": "discovery_absent"} for d in L["documents"]}
    g = S.decision_coverage_gate(lane("B", L), lane("C", L, cov=absent), L)
    assert g["C"]["coverage"] == 0 and g["C"]["wrong_absence"] == 14 and g["passes"] is False


def test_concentration_in_one_project_blocks_eligibility():
    L = labels(n=14, projects=7)
    gain = {(d, f) for d in L["documents"] if L["documents"][d]["project"] == "p0" for f in F}
    c = S.concentration(lane("B", L), lane("C", L, clean=gain), L)
    assert all(c[f]["concentrated"] for f in F)


def test_a_c_critical_on_resolved_truth_and_the_thresholds_decide_eligibility():
    L = labels()
    B = lane("B", L, requests=6)
    C = lane("C", L, clean=all_clean(L), requests=20, inherited=6)
    ok = S.evaluate(B, C, None, L, caps={"B": 240, "C": 240}, extensions_used=0, seed="t")
    assert ok["outcome"] == "ELIGIBLE FOR A SEPARATE SELECTION DECISION" and ok["default_selected"] is None, ok["reasons_not_eligible"]
    bad = lane("C", L, clean=all_clean(L) - {("d1", "revision")}, wrong={("d1", "revision")}, crit={("d1", "revision")}, requests=20, inherited=6)
    r = S.evaluate(B, bad, None, L, caps={"B": 240, "C": 240}, extensions_used=0, seed="t")
    assert r["outcome"] == "NOT ELIGIBLE" and "critical acceptance on resolved truth in C" in r["reasons_not_eligible"]


def test_stop_states_override_the_outcome():
    L = labels()
    B, C = lane("B", L), lane("C", L, clean=all_clean(L), requests=10)
    assert S.evaluate(B, C, None, L, caps={"B": 1, "C": 1}, extensions_used=0, seed="t", stop_state={"comparison": "INVALID: x"})["outcome"] == "INVALID"
    assert S.evaluate(B, C, None, L, caps={"B": 1, "C": 1}, extensions_used=0, seed="t", stop_state={"comparison": "INCOMPLETE: x"})["outcome"] == "INCOMPLETE"


def test_r_is_compared_on_revision_and_never_enters_the_gates():
    L = labels()
    B = lane("B", L)
    C = lane("C", L, clean=all_clean(L) - {("d2", "revision")}, requests=10)
    R = lane("R", L, clean=all_clean(L), crit={("d3", "identity")})
    r = S.evaluate(B, C, R, L, caps={"B": 240, "C": 240}, extensions_used=0, seed="t")
    assert r["primary_outcomes"]["revision_under_PA_C_vs_R"]["lost"] == ["d2"]
    assert r["primary_outcomes"]["critical"]["R"]["resolved"] == 1
    assert "critical acceptance on resolved truth in C" not in r["reasons_not_eligible"], "a reference critical is a finding, never a C result"


def test_the_bootstrap_is_seeded():
    L = labels()
    B, C = lane("B", L), lane("C", L, clean={(d, "identity") for d in list(L["documents"])[:9]})
    assert S.paired(B, C, L, "identity", "s") == S.paired(B, C, L, "identity", "s")


def test_decision_coverage_must_not_fall_below_the_reference():
    L = labels()
    absent = {d: {"identity": "completed_read", "revision": "completed_read", "decision": "located_incomplete"} for d in L["documents"]}
    none = {d: {f: "not_attempted" for f in F} for d in L["documents"]}
    g = S.decision_coverage_gate(lane("B", L, cov=none), lane("C", L, cov=absent), L, lane("R", L))
    assert g["B"]["coverage"] == 0 and g["R"]["coverage"] == 14 and g["C"]["coverage"] == 0 and g["passes"] is False
