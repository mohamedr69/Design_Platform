"""labels_adapter_r32 over the real r32-labels-reviewed-2 (hash-checked) and synthetic rows.
Run: python -m pytest -q test_labels_adapter_r32.py"""
import copy
import pickle

import pytest

import inputs_r32 as I
import labels_adapter_r32 as A


@pytest.fixture(scope="module")
def raw():
    return I.load_all()


@pytest.fixture(scope="module")
def truth(raw):
    return A.build_truth(raw["reviewed2"], renders=raw["renders"], source_manifest=raw["source_manifest"],
                         selection=raw["selection"], verification=raw["verification"])


def test_population_equals_the_frozen_field_population(truth):
    fp = I.load("reviewed2_field_population")
    pop = A.population(truth)
    assert {f: len(v) for f, v in pop.items()} == {"identity": 57, "revision": 38, "decision": 38}
    assert pop == {f: fp["counted_documents"][f] for f in A.FIELDS}


def test_sentinels_are_distinct_from_none_and_from_each_other(truth):
    assert A.NOT_SCORABLE is not None and A.ABSENT is not None and A.NOT_SCORABLE is not A.ABSENT
    assert not A.NOT_SCORABLE and not A.ABSENT, "a sentinel is never a truthy value"
    assert pickle.loads(pickle.dumps(A.NOT_SCORABLE)) is A.NOT_SCORABLE
    assert A.lookup(truth, "F001", "9", "identity") is None, "an unlabelled page is None, not absent"
    assert A.truth_of(A.lookup(truth, "F001", "2", "identity")) is A.ABSENT
    assert A.truth_of(A.lookup(truth, "F001", "1", "identity")) == "MAT – 116"


def test_review33_rulings_are_not_scorable_per_field(truth):
    f019 = A.lookup(truth, "F019", "1", "revision")
    assert A.truth_of(f019) is A.NOT_SCORABLE and "ambiguous" in f019["not_scorable_reasons"]
    assert A.truth_of(A.lookup(truth, "F019", "1", "identity")) not in (A.NOT_SCORABLE, A.ABSENT, None), "F019 identity stays scorable"
    assert A.truth_of(A.lookup(truth, "F019", "1", "decision")) not in (A.NOT_SCORABLE, A.ABSENT, None), "F019 decision stays scorable"
    for pg in ("1", "2", "3", "4"):
        assert A.truth_of(A.lookup(truth, "F069", pg, "identity")) is A.NOT_SCORABLE
    assert A.primary(truth, "F019", "decision") and not A.primary(truth, "F019", "revision")


def test_uncertain_association_and_suffix_revisions_are_not_scorable(truth):
    r = A.lookup(truth, "F003", "1", "revision")
    assert r["state"] == "present" and A.truth_of(r) is A.NOT_SCORABLE and "uncertain_association" in r["not_scorable_reasons"]
    s = A.not_scorable_summary(truth)
    assert s["by_reason"]["uncertain_association"] == 21 and s["by_reason"]["ambiguous"] == 9
    assert s["documents"] == 25


def test_absent_rows_are_absent_with_their_kind(truth):
    r = A.lookup(truth, "F001", "1", "decision")
    assert A.truth_of(r) is A.ABSENT and r["absent_kind"] == "no_decision_area"


def test_compilations_are_keyed_by_page(truth):
    assert truth["compilations"] == ["F002", "F035", "F043", "F069"]
    lits = {pg: A.truth_of(A.lookup(truth, "F002", pg, "identity")) for pg in ("1", "2", "3", "4")}
    assert len({v for v in lits.values() if isinstance(v, str)}) >= 2, "different submittals on different pages"


def test_aliases_are_canonical_and_never_counted(truth):
    assert truth["aliases"] == {"F031": "F001", "F052": "F038", "F059": "F046", "F070": "F067"}
    for alias, canon in truth["aliases"].items():
        d = truth["documents"][alias]
        assert d["is_alias"] and d["canonical_id"] == canon and not any(A.has_fact(truth, alias, f) for f in A.FIELDS)
    assert truth["documents"]["F052"]["alias_kind"].startswith("byte-identical")
    assert truth["documents"]["F031"]["alias_kind"].startswith("content duplicate")


def test_document_attributes(truth, raw):
    d = truth["documents"]["F020"]
    assert d["project"] == "EP-27331" and d["contractor"] == "Euro Gulf Technoservices LLC" and d["stratum"] == "review_signal"
    assert d["layout_key"] == "emaar-mirage-document-submittal" and d["decision_type"] == "approved as noted"
    assert d["doc_key"].startswith("EP-27331/") and d["in_scope_pages"] == 4
    assert all(doc["stratum"] in ("review_signal", "drawing_signal", "other") for doc in truth["documents"].values())
    assert {doc["contractor"] for doc in truth["documents"].values()} == {r["contractor"] for ep, r in raw["verification"]["results"].items() if ep in raw["selection"]["cohort"]}
    assert truth["documents"]["F070"]["layout_key"] == truth["documents"]["F067"]["layout_key"]


def test_decision_controls(truth):
    canon = [d for d in truth["documents"].values() if not d["is_alias"]]
    assert sum(d["decision_control"] == "positive" for d in canon) == 38
    assert truth["documents"]["F045"]["decision_control"] == "negative"
    assert truth["documents"]["F067"]["decision_control"] == "none", "an ambiguous decision is neither control"


def test_g1_alternates_and_resubmission_flags(truth):
    assert A.lookup(truth, "F008", "3", "identity")["alternates"] == ["B01-ASC-SD-ELE-0102-Rev.00"]
    assert sum(r["resubmission_required"] for r in truth["rows"].values()) == 9


def test_layout_key_rule_is_deterministic_and_text_only():
    assert A.layout_key("ENCO shop drawing FA- 6001", "ENCO shop drawing (A2...)", "F046") == ("enco-shop-drawing", "helper:enco")
    assert A.layout_key("something unknown", None, "F099") == ("single:F099", "single")


def test_a_synthetic_document_field_not_resolved_makes_every_row_not_scorable(raw):
    r2 = copy.deepcopy(raw["reviewed2"])
    r2["documents"]["F045"]["review"]["decision"]["resolved_for_scoring"] = "no"
    t = A.build_truth(r2, renders=raw["renders"], source_manifest=raw["source_manifest"], selection=raw["selection"], verification=raw["verification"])
    assert A.truth_of(A.lookup(t, "F045", "1", "decision")) is A.NOT_SCORABLE
    assert t["documents"]["F045"]["decision_control"] == "none"


def test_synthetic_states_illegible_and_unsupported_are_not_scorable(raw):
    r2 = copy.deepcopy(raw["reviewed2"])
    r2["documents"]["F045"]["pages"]["1"]["identity"] = {"state": "illegible", "excluded_from_scoring": False, "review_status": "accepted"}
    r2["documents"]["F045"]["pages"]["1"]["revision"] = {"state": "unsupported", "excluded_from_scoring": False, "review_status": "accepted"}
    t = A.build_truth(r2, renders=raw["renders"], source_manifest=raw["source_manifest"], selection=raw["selection"], verification=raw["verification"])
    assert A.lookup(t, "F045", "1", "identity")["not_scorable_reasons"][0] == "illegible"
    assert "unsupported" in A.lookup(t, "F045", "1", "revision")["not_scorable_reasons"]
