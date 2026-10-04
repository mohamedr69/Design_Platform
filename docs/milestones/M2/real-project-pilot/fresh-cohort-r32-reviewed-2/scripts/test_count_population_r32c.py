"""Synthetic tests for count_population_r32c.count_population (no frozen data used)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_population_r32c as C  # noqa: E402
import test_apply_review33_r32 as TA  # noqa: E402  (synthetic reviewed-1 / rulings fixtures)
import apply_review33_r32 as A  # noqa: E402


def present():
    return {"state": "present", "association": "resolved", "excluded_from_scoring": False}


def absent():
    return {"state": "absent", "excluded_from_scoring": False}


def doc(pid, rs=("yes", "yes", "yes"), cf=("yes", "yes", "yes"), ep="P1", pages=None):
    review = {f: {"resolved_for_scoring": rs[i], "carries_fact": cf[i]} for i, f in enumerate(C.FIELDS)}
    if pages is None:
        pages = {"1": {f: (present() if cf[i] == "yes" else absent()) for i, f in enumerate(C.FIELDS)}}
    return {"pool_id": pid, "ep": ep, "review": review, "pages": pages}


def reviewed(docs, aliases=None):
    return {"documents": {d["pool_id"]: d for d in docs}, "count_once_aliases": aliases or {}}


def n_docs(n, start=1, **kw):
    return [doc("F%03d" % i, **kw) for i in range(start, start + n)]


def test_yes_yes_required():
    r = reviewed([doc("F001"), doc("F002", rs=("no", "yes", "yes"), cf=("no", "yes", "yes")),
                  doc("F003", cf=("no", "yes", "yes"))])
    out = C.count_population(r)
    assert out["gate_counts"] == {"identity": 1, "revision": 3, "decision": 3}
    assert out["counted_documents"]["identity"] == ["F001"]
    assert out["excluded_unresolved"] == {}


def test_aliases_count_once_under_canonical():
    r = reviewed([doc("F001"), doc("F031"), doc("F052", rs=(None,) * 3, cf=(None,) * 3, pages={})],
                 aliases={"F031": "F001", "F052": "F001"})
    out = C.count_population(r)
    assert out["gate_counts"] == {"identity": 1, "revision": 1, "decision": 1}
    assert out["counted_documents"]["decision"] == ["F001"]
    assert out["distinct_documents"] == {"staged_files": 3, "documents_with_own_rulings": 2,
                                         "distinct_after_count_once": 1}
    assert out["alias_agreement_check"]["disagreements"] == []
    r2 = reviewed([doc("F001", cf=("no",) * 3), doc("F031")], aliases={"F031": "F001"})
    out2 = C.count_population(r2)
    assert out2["counted_documents"]["identity"] == ["F001"]  # the alias's yes counts under the canonical id
    assert len(out2["alias_agreement_check"]["disagreements"]) == 3


def test_unresolved_excluded_listed_and_upper_bound():
    docs = [doc("F001"), doc("F019", rs=("yes", "unresolved", "yes"), cf=("yes", "unresolved", "yes")),
            doc("F069", rs=("unresolved", "yes", "yes"), cf=("no", "yes", "yes"))]
    out = C.count_population(reviewed(docs))
    assert out["excluded_unresolved"] == {"identity": ["F069"], "revision": ["F019"]}
    assert out["gate_counts"] == {"identity": 2, "revision": 2, "decision": 3}
    assert out["upper_bound_if_resolved"] == {"identity": 2, "revision": 3, "decision": 3}
    docs[1]["review"]["revision"] = {"resolved_for_scoring": "no", "carries_fact": "no"}
    docs[1]["pages"]["1"]["revision"] = {"state": "ambiguous", "excluded_from_scoring": True}
    docs[2]["review"]["identity"] = {"resolved_for_scoring": "no", "carries_fact": "no"}
    out = C.count_population(reviewed(docs))
    assert out["excluded_unresolved"] == {}
    assert out["upper_bound_if_resolved"] == out["gate_counts"] == {"identity": 2, "revision": 2, "decision": 3}


def test_gate_at_twelve():
    out = C.count_population(reviewed(n_docs(12)))
    assert out["gate_counts"] == {"identity": 12, "revision": 12, "decision": 12} and out["gate_action"] == C.READY
    docs = n_docs(12)
    docs[0]["review"]["decision"]["carries_fact"] = "no"
    docs[0]["pages"]["1"]["decision"] = absent()
    out = C.count_population(reviewed(docs))
    assert out["gate_counts"]["decision"] == 11 and out["gate_action"] == C.EXTEND
    assert out["status"] == "COUNTED" and out["extensions_used"] == 0 and out["gate_minimum"] == 12
    docs = n_docs(13)
    docs[0]["review"]["revision"]["resolved_for_scoring"] = "unresolved"
    out = C.count_population(reviewed(docs))
    assert out["gate_counts"]["revision"] == 12 and out["gate_action"] == C.READY


def test_consistency_both_directions_and_scope():
    d_bad = doc("F003", ep="P2")
    d_bad["pages"]["1"]["decision"] = {"state": "present", "association": "uncertain"}
    d_excl = doc("F004", ep="P2")
    d_excl["pages"]["1"]["identity"]["excluded_from_scoring"] = True
    d_rev = doc("F005", cf=("yes", "no", "yes"))
    d_rev["pages"]["1"]["revision"] = present()
    d_scope = doc("F006")
    d_scope["pages"] = {"5": d_scope["pages"]["1"]}
    docs = [doc("F001"), doc("F002", ep="P2"), d_bad, d_excl, d_rev, d_scope]
    out = C.count_population(reviewed(docs))
    cc = out["consistency_check"]
    assert {(i["pool_id"], i["field"]) for i in cc["yes_without_supporting_page"]} == {("F003", "decision"),
                                                                                      ("F004", "identity")}
    assert [(i["pool_id"], i["field"]) for i in cc["no_with_supporting_page"]] == [("F005", "revision")]
    assert cc["ok"] is False
    scope = {p: ["1"] for p in ("F001", "F002", "F003", "F004", "F005", "F006")}
    out = C.count_population(reviewed(docs), scope)
    cc = out["consistency_check"]
    assert cc["labelled_pages_outside_scope"] == ["F006/p5"]
    assert cc["in_scope_pages_without_labels"] == {"F006": ["1"]}
    assert ("F006", "identity") in {(i["pool_id"], i["field"]) for i in cc["yes_without_supporting_page"]}
    clean = [doc("F001"), doc("F002", cf=("no", "yes", "no"))]
    out = C.count_population(reviewed(clean), {"F001": ["1"], "F002": ["1"]})
    assert out["consistency_check"]["ok"] is True
    assert out["consistency_check"]["checked_carries_fact_yes"] == 4
    assert out["consistency_check"]["checked_carries_fact_no"] == 2


def test_by_project_lists_zero_projects():
    docs = [doc("F001"), doc("F002", ep="P2"), doc("F003", ep="P3", cf=("yes", "yes", "no"))]
    docs[2]["pages"]["1"]["decision"] = absent()
    out = C.count_population(reviewed(docs))
    assert out["by_project_decision"] == {"P1": 1, "P2": 1, "P3": 0}


def test_synthetic_reviewed2_has_nothing_unresolved():
    r1 = TA.make_r1()
    before = C.count_population(r1)
    assert before["excluded_unresolved"] == {"identity": ["F069"], "revision": ["F019"]}
    r2 = A.build_reviewed2(r1, TA.make_er(), dict(TA.H), dict(TA.META))
    after = C.count_population(r2)
    assert after["excluded_unresolved"] == {}
    assert after["gate_counts"] == before["gate_counts"]
    assert after["upper_bound_if_resolved"] == after["gate_counts"]
    assert after["count_once_aliases"] == A.EXPECTED_ALIASES
    assert after["consistency_check"]["ok"] is True
