"""Synthetic tests for count_population_r32.count_population (no frozen data used)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_population_r32 as C  # noqa: E402


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


def test_count_once_alias_counts_once():
    r = reviewed([doc("F001"), doc("F031"), doc("F052", rs=(None,) * 3, cf=(None,) * 3, pages={})],
                 aliases={"F031": "F001", "F052": "F001"})
    out = C.count_population(r)
    assert out["gate_counts"] == {"identity": 1, "revision": 1, "decision": 1}
    assert out["distinct_documents"] == {"staged_files": 3, "documents_with_own_rulings": 2,
                                         "distinct_after_count_once": 1}
    assert out["alias_agreement_check"]["disagreements"] == []


def test_alias_yes_counts_under_canonical_id():
    r = reviewed([doc("F001", rs=("yes",) * 3, cf=("no",) * 3), doc("F031")], aliases={"F031": "F001"})
    out = C.count_population(r)
    assert out["counted_documents"]["identity"] == ["F001"]
    assert len(out["alias_agreement_check"]["disagreements"]) == 3


def test_unresolved_excluded_listed_and_upper_bound():
    docs = [doc("F001"), doc("F019", rs=("yes", "unresolved", "yes"), cf=("yes", "unresolved", "yes")),
            doc("F069", rs=("unresolved", "yes", "yes"), cf=("no", "yes", "yes"))]
    out = C.count_population(reviewed(docs))
    assert out["excluded_unresolved"] == {"identity": ["F069"], "revision": ["F019"], "decision": []}
    assert out["gate_counts"] == {"identity": 2, "revision": 2, "decision": 3}
    # F019 revision would count if resolved yes; F069 identity carries no fact either way
    assert out["upper_bound_if_resolved"] == {"identity": 2, "revision": 3, "decision": 3}


def test_gate_at_twelve():
    out = C.count_population(reviewed(n_docs(12)))
    assert out["gate_counts"]["decision"] == 12 and out["gate_action"] == C.READY
    docs = n_docs(12)
    docs[0]["review"]["decision"]["carries_fact"] = "no"
    docs[0]["pages"]["1"]["decision"] = absent()
    out = C.count_population(reviewed(docs))
    assert out["gate_counts"]["decision"] == 11 and out["gate_action"] == C.EXTEND
    assert out["status"] == "COUNTED" and out["extensions_used"] == 0


def test_by_project_and_consistency_check():
    d_bad = doc("F003", ep="P2")
    d_bad["pages"]["1"]["decision"] = {"state": "present", "association": "uncertain"}
    d_excl = doc("F004", ep="P2")
    d_excl["pages"]["1"]["identity"]["excluded_from_scoring"] = True
    out = C.count_population(reviewed([doc("F001"), doc("F002", ep="P2"), d_bad, d_excl]))
    assert out["by_project_decision"] == {"P1": 1, "P2": 3}
    inc = {(i["pool_id"], i["field"]) for i in out["consistency_check"]["inconsistencies"]}
    assert inc == {("F003", "decision"), ("F004", "identity")}
    assert out["consistency_check"]["ok"] is False
