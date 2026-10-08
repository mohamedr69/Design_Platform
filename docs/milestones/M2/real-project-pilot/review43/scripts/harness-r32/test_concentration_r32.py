"""concentration_r32 version 2 (owner decision A-05; Review 34 RC-1 / R34-01 and RC-6 / R34-08): every leg on synthetic
results, Review 34's scenarios S3a / S3b / S3c on the real truth and run set, monotonicity, and failures counted once per
(document, field). Run: python -m pytest -q test_concentration_r32.py"""
import itertools

import pytest

import concentration_r32 as K
import r32_test_helpers as H
import r34_scenarios as SC
import score_bcr_r32 as S


def gains(T, ids, fields=("identity", "revision", "decision")):
    return {pid: set(fields) for pid in T["documents"] if pid in ids}


@pytest.fixture(scope="module")
def real():
    T, run = SC.load()
    return T, run, SC.build(T, run)


def _real(real, name):
    T, run, sc = real
    B, C, R, stop, _ = sc[name]
    return T, run, B, C, R, stop


# ---- version and thresholds -----------------------------------------------------------------------------------------
def test_version_two_has_no_net_gain_floor():
    assert K.RULE_VERSION == "concentration-r32-2026-10-03.2" and K.PREVIOUS_VERSION == "concentration-r32-2026-10-03.1"
    assert "min_net_gain" not in K.THRESHOLDS
    assert K.THRESHOLDS == {"gain_share_max": 0.5, "min_failures": 2, "failure_share_max": 0.5, "negative_control_false_accepts_max": 0}
    assert K.BLOCKING_GROUPINGS == ("project", "contractor", "layout_key") and K.REPORTED_GROUPINGS == ("decision_type", "stratum")


# ---- the gain legs at every size --------------------------------------------------------------------------------------
def test_spread_gain_is_eligible():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, "decision")
    assert r["net_gain"] == 16 and r["outcome"] == "ELIGIBLE" and r["groupings"]["project"]["largest_gain_share"] == 0.25
    assert "do not come mainly from one" in r["attribution_statement"]


def test_project_leg_more_than_half_of_the_net_gain():
    T = H.truth(n=16, projects=4)
    ids = [pid for pid, d in T["documents"].items() if d["project"] == "p0"] + ["D01"]
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "identity")
    assert r["net_gain"] == 5 and r["outcome"] == "NOT ELIGIBLE"
    assert any("one project (p0)" in x for x in r["reasons"]) and r["mainly_from"]["project"]["gains_mainly_from"] == "p0"


@pytest.mark.parametrize("k", [1, 2, 3, 4])
def test_a_gain_inside_one_project_is_never_eligible_at_any_size(k):
    """RC-1: no floor. The whole gain in p0 (k documents of p0's four) is NOT ELIGIBLE for k = 1, 2, 3 and 4."""
    T = H.truth(n=16, projects=4)
    ids = [pid for pid, d in sorted(T["documents"].items()) if d["project"] == "p0"][:k]
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "revision")
    assert r["net_gain"] == k and r["outcome"] == "NOT ELIGIBLE", r
    assert any("one project (p0)" in x for x in r["reasons"]) and r["notes"] == []


def test_a_net_gain_of_one_is_always_concentrated():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ["D05"])), T, "identity")
    assert r["net_gain"] == 1 and r["outcome"] == "NOT ELIGIBLE"
    assert r["groupings"]["project"]["largest_gain_share"] == 1.0


def test_a_small_gain_spread_over_projects_and_layouts_is_eligible():
    T = H.truth(n=16, projects=4)                       # layouts L0..L3 follow projects p0..p3
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ["D00", "D01", "D02"])), T, "revision")
    assert r["net_gain"] == 3 and r["outcome"] == "ELIGIBLE" and r["reasons"] == []
    assert r["groupings"]["project"]["largest_gain_share"] == pytest.approx(0.3333, abs=1e-4)


def test_exactly_half_is_not_concentrated():
    T = H.truth(n=16, projects=4)
    ids = ["D00", "D04", "D01", "D02"]          # p0 holds 2 of 4
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "identity")
    assert r["net_gain"] == 4 and r["outcome"] == "ELIGIBLE"
    r2 = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ["D00", "D01"])), T, "identity")
    assert r2["net_gain"] == 2 and r2["outcome"] == "ELIGIBLE", "two gains in two projects and two layouts: exactly half each"


def test_layout_leg_blocks_a_gain_spread_over_projects_but_from_one_template():
    lay = ["TPL" if i < 8 else f"L{i}" for i in range(16)]
    T = H.truth(n=16, projects=4, layouts=lay)
    ids = [f"D{i:02d}" for i in range(8)] + ["D10", "D12"]
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "decision")
    assert r["groupings"]["project"]["largest_gain_share"] <= 0.5
    assert r["outcome"] == "NOT ELIGIBLE" and any("one layout_key (TPL)" in x for x in r["reasons"])
    small = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ["D00", "D01", "D02"])), T, "decision")
    assert small["net_gain"] == 3 and small["outcome"] == "NOT ELIGIBLE" and any("one layout_key (TPL)" in x for x in small["reasons"]), \
        "three projects but one template: blocked at net 3 too"


def test_contractor_leg_when_two_projects_share_a_contractor():
    con = ["K1" if i % 4 in (0, 1) else f"K{i % 4}" for i in range(16)]
    T = H.truth(n=16, projects=4, contractors=con)
    ids = ["D00", "D04", "D08", "D01", "D05", "D02"]     # p0 3, p1 2, p2 1: no project > half; contractor K1 = 5 of 6
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ids)), T, "identity")
    assert r["groupings"]["project"]["largest_gain_share"] == 0.5
    assert r["outcome"] == "NOT ELIGIBLE" and any("one contractor (K1)" in x for x in r["reasons"])
    two = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=gains(T, ["D00", "D01"])), T, "identity")
    assert two["outcome"] == "NOT ELIGIBLE" and any("one contractor (K1)" in x for x in two["reasons"]), "net 2, both from K1"
    e = K.evaluate(H.lane("B", T), H.lane("C", T), T)
    assert e["contractor_equals_project"] is False


# ---- UNDETERMINED only without a gain; it never overturns NOT ELIGIBLE -------------------------------------------------
def test_undetermined_only_when_there_is_no_gain():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T), T, "revision")
    assert r["net_gain"] == 0 and r["outcome"] == "UNDETERMINED" and r["reasons"] == [] and r["notes"]
    B = H.lane("B", T, correct=gains(T, ["D00"]))
    r2 = K.field_concentration(B, H.lane("C", T), T, "revision")
    assert r2["net_gain"] == -1 and r2["outcome"] == "UNDETERMINED" and r2["failures"] == 1


def test_undetermined_never_turns_not_eligible_into_eligible():
    T = H.truth(n=16, projects=4, negatives=4)
    fa = {"N00": [{"page": "1", "field": "decision", "value": "approved", "state": "accepted"}]}
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, extra_facts=fa), T, "decision")
    assert r["net_gain"] == 0 and r["outcome"] == "NOT ELIGIBLE", "net 0 with a negative-control false acceptance is NOT ELIGIBLE"
    B = H.lane("B", T, correct=gains(T, ["D00", "D04", "D08"]))
    r2 = K.field_concentration(B, H.lane("C", T), T, "identity")
    assert r2["net_gain"] == -3 and r2["outcome"] == "NOT ELIGIBLE" and any("failures (> half) in one project (p0)" in x for x in r2["reasons"])


# ---- monotonicity --------------------------------------------------------------------------------------------------------
def test_monotonic_adding_a_gain_to_the_dominant_group_never_makes_it_eligible():
    """For every gain set over a 12-document truth (3 projects x 4, layouts by project), whenever the outcome is NOT ELIGIBLE
    by a gain leg, adding any further gain document of the dominant project keeps it NOT ELIGIBLE; and a gain that lies
    entirely inside one project is NOT ELIGIBLE at every size."""
    T = H.truth(n=12, projects=3)
    ids = sorted(T["documents"])
    B = H.lane("B", T)
    memo = {}

    def outcome(gs):
        key = frozenset(gs)
        if key not in memo:
            memo[key] = K.field_concentration(B, H.lane("C", T, correct=gains(T, key, ("identity",))), T, "identity")
        return memo[key]

    checked = 0
    for k in range(1, 6):
        for gs in itertools.combinations(ids, k):
            r = outcome(gs)
            if r["outcome"] != "NOT ELIGIBLE":
                continue
            top = r["groupings"]["project"]["largest_gain_group"]
            for extra in ids:
                if extra not in gs and T["documents"][extra]["project"] == top:
                    assert outcome(set(gs) | {extra})["outcome"] == "NOT ELIGIBLE", (gs, extra)
                    checked += 1
    assert checked > 100
    for p in ("p0", "p1", "p2"):
        mine = [pid for pid in ids if T["documents"][pid]["project"] == p]
        for k in range(1, len(mine) + 1):
            assert outcome(mine[:k])["outcome"] == "NOT ELIGIBLE"


def test_monotonic_on_the_real_run_set_ep27331_decision_gain_of_every_size(real):
    """The concentrated EP-27331 decision gain is NOT ELIGIBLE (field and candidate) at sizes 1 to 6 (version 1 let 1-3 pass)."""
    T, run, sc = real
    _, has, by_proj = SC.groups(T, run)
    big = by_proj["EP-27331"]
    assert len(big) == 6
    for k in range(1, 7):
        g = {(p, "decision") for p in big[:k]}
        B, C = SC.lane(T, run, "B", miss=g, own=100), SC.lane(T, run, "C", own=20, inherited=100)
        res = S.evaluate(B, C, None, T, caps={"B": 240, "C": 240}, extensions_used=0, docs=set(run))
        assert res["concentration"]["fields"]["decision"]["net_gain"] == k
        assert res["concentration"]["fields"]["decision"]["outcome"] == "NOT ELIGIBLE", k
        assert res["outcome"] == "NOT ELIGIBLE", k


# ---- Review 34 scenarios on the real truth and run set --------------------------------------------------------------------
def test_s3a_decision_gain_of_two_inside_one_project_is_not_eligible(real):
    T, run, B, C, R, stop = _real(real, "S3a decision gain 2 inside one project")
    r = K.field_concentration(B, C, T, "decision", docs=set(run))
    assert r["net_gain"] == 2 and r["groupings"]["project"]["largest_gain_group"] == "EP-22349"
    assert r["outcome"] == "NOT ELIGIBLE" and any("one project (EP-22349)" in x for x in r["reasons"])


def test_s3b_decision_gain_of_three_on_f037_f009_f032_of_ep27331_is_not_eligible(real):
    T, run, B, C, R, stop = _real(real, "S3b decision gain 3 inside EP-27331")
    r = K.field_concentration(B, C, T, "decision", docs=set(run))
    assert sorted(p for p, v in r["per_document"].items() if v == 1) == ["F009", "F032", "F037"]
    assert r["net_gain"] == 3 and r["outcome"] == "NOT ELIGIBLE"
    assert {g: r["groupings"][g]["largest_gain_share"] for g in ("project", "contractor", "layout_key")} == {"project": 1.0, "contractor": 1.0, "layout_key": 1.0}
    assert any("one project (EP-27331)" in x for x in r["reasons"]) and any("one layout_key (emaar-mirage-document-submittal)" in x for x in r["reasons"])
    res = S.evaluate(B, C, R, T, caps={"B": 240, "C": 240}, extensions_used=0, stop_state=stop, docs=set(run))
    assert res["request_gate"]["passes"] is True, "the gate passes, as Review 34 found; the concentration leg must block"
    assert res["outcome_by_field"]["decision"] == "NOT ELIGIBLE" and res["outcome"] == "NOT ELIGIBLE"


def test_s3c_decision_gain_of_four_inside_ep27331_stays_not_eligible_and_a_spread_gain_of_four_is_eligible(real):
    T, run, B, C, R, stop = _real(real, "S3c decision gain 4 inside EP-27331")
    r = K.field_concentration(B, C, T, "decision", docs=set(run))
    assert r["net_gain"] == 4 and r["outcome"] == "NOT ELIGIBLE"
    T, run, B, C, R, stop = _real(real, "S3c-spread decision gain 4 over four projects")
    r2 = K.field_concentration(B, C, T, "decision", docs=set(run))
    assert r2["net_gain"] == 4 and r2["outcome"] == "ELIGIBLE" and r2["groupings"]["project"]["largest_gain_share"] == 0.25


# ---- failures once per (document, field) (RC-6) ------------------------------------------------------------------------
def test_a_wrong_acceptance_that_loses_the_fact_is_one_failure():
    T = H.truth(n=16, projects=4)
    B = H.lane("B", T, correct=H.all_fields(T))
    C = H.lane("C", T, correct=H.all_fields(T), wrong={"D03": {"revision"}})
    r = K.field_concentration(B, C, T, "revision")
    assert r["lost_facts"] == ["D03"] and len(r["wrong_acceptances"]) == 1
    assert r["failures"] == 1 and r["failure_documents"] == [{"pool_id": "D03", "field": "revision", "kinds": ["wrong_acceptance", "lost_fact"],
                                                               "wrong_acceptance_pages": ["1"]}]


def test_wrong_acceptances_on_several_pages_of_one_document_are_one_failure():
    T = H.truth(n=16, projects=4)
    T["rows"]["D03|2|revision"] = H.row("D03", 2, "revision", "value", "01")
    T["documents"]["D03"]["labelled_pages"] = ["1", "2"]
    extra = {"D03": [{"page": "1", "field": "revision", "value": "77", "state": "accepted"},
                     {"page": "2", "field": "revision", "value": "78", "state": "accepted"}]}
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, extra_facts=extra), T, "revision")
    assert len(r["wrong_acceptances"]) == 2 and r["failures"] == 1
    assert r["failure_documents"][0]["wrong_acceptance_pages"] == ["1", "2"]


def test_s1_one_wrong_revision_acceptance_is_one_failure_on_the_real_run_set(real):
    T, run, B, C, R, stop = _real(real, "S1 one wrong revision acceptance in C")
    r = K.field_concentration(B, C, T, "revision", docs=set(run))
    assert r["failures"] == 1 and r["failure_documents"][0]["kinds"] == ["wrong_acceptance", "lost_fact"]
    assert not any("failures (> half)" in x for x in r["reasons"]), "one incident can never be concentrated"


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


# ---- negative and positive decision controls; reported-only groupings -----------------------------------------------------
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


def test_decision_type_and_stratum_are_reported_and_never_block():
    T = H.truth(n=16, projects=4)
    r = K.field_concentration(H.lane("B", T), H.lane("C", T, correct=H.all_fields(T)), T, "decision")
    assert r["groupings"]["decision_type"]["largest_gain_share"] == 1.0 and r["groupings"]["decision_type"]["blocking"] is False
    assert r["groupings"]["stratum"]["largest_gain_share"] == 1.0 and r["groupings"]["stratum"]["blocking"] is False
    assert r["outcome"] == "ELIGIBLE"


def test_unattempted_documents_are_not_matched_and_outputs_carry_the_statement():
    T = H.truth(n=16, projects=4)
    C = H.lane("C", T, correct=H.all_fields(T), attempted=set(list(T["documents"])[:10]))
    r = K.field_concentration(H.lane("B", T), C, T, "identity")
    assert r["matched"] == 10 and r["reference_set_statement"].endswith("not human-signed")
    e = K.evaluate(H.lane("B", T), C, T)
    assert e["contractor_equals_project"] is True and e["rule_version"] == "concentration-r32-2026-10-03.2" and "R34-07" in e["contractor_note"]
