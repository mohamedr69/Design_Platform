"""Integration tests of the four-arm harness (offline, synthetic rows): binding of the selected attempt to the declared
source hash / profile / variant / policy (enforced by the caller), mixed supported / unsupported pages, missing pages,
wrong-context attempts, unattempted documents, transport success with unusable fields, extra facts outside scope, and
the field-specific matched subsets. Run: pytest test_harness_v3.py (cwd review21)."""
import coverage_v3 as cv
import score_arms_v3 as sa

CTX = {"variant": "EV1", "profile": "default", "policy": "pol-L1"}
PLAN = [{"doc": "d1", "sha256": "a" * 64, "pages": 1, "extension": ".pdf"}, {"doc": "d6", "sha256": "b" * 64, "pages": 6, "extension": ".pdf"},
        {"doc": "w", "sha256": "c" * 64, "pages": None, "extension": ".docx"}, {"doc": "gone", "sha256": "d" * 64, "pages": 2, "extension": ".pdf"}]


def full(ident="completed", rev="completed", dec="absent_by_discovery"):
    return {"outcome": "evidence", "fields": {"own:identity": ident, "own:revision": rev, "own:decision": dec}}


def attempt(pages, *, policy="pol-L1", read="a" * 64, calls=None):
    return {"policy": policy, "profile": "default", "variant": "EV1", "read_sha256": read, "pages": pages, "calls": calls or [{"outcome": "ok"}]}


def row(sha, attempts, obs=None):
    env = {"default|EV1": {"profile": "default", "variant": "EV1", "pages": obs or {}}}
    return {"sha256": sha, "extracted": {"ai_evidence": {"attempts": attempts, "envelopes": env}}}


def test_binding_rejects_source_context_and_policy_mismatches():
    p = PLAN[0]
    assert cv.select_attempt(None, p, CTX) == (None, "no_row")
    assert cv.select_attempt(row("z" * 64, [attempt({"1": full()})]), p, CTX)[1] == "source_mismatch"
    assert cv.select_attempt(row("a" * 64, [attempt({"1": full()}, policy="pol-L2")]), p, CTX)[1] == "context_mismatch"
    assert cv.select_attempt(row("a" * 64, [attempt({"1": full()}, read="q" * 64)]), p, CTX)[1] == "not_attempted"
    att, why = cv.select_attempt(row("a" * 64, [attempt({"1": full()}, policy="pol-L2"), attempt({"1": full()})]), p, CTX)
    assert why == "bound" and att["policy"] == "pol-L1"


def test_mixed_supported_unsupported_and_missing_pages_and_unattempted_documents():
    rows = {"d1": row("a" * 64, [attempt({"1": full()})]),
            "d6": row("b" * 64, [attempt({"1": full(), "2": full(), "3": {"outcome": "no_trigger"}}, read="b" * 64)]),
            "w": row("c" * 64, []), "gone": None}
    c = sa.arm_coverage(PLAN, {k: v for k, v in rows.items() if v}, CTX, max_pages=4)
    s = c["summary"]
    assert s["documents_planned"] == 4 and s["documents_unsupported_input"] == 1 and s["documents_unattempted"] == 1
    d6 = next(d for d in c["documents"] if d["doc"] == "d6")
    assert d6["pages"]["4"]["own:identity"] == "missing_page" and d6["pages"]["3"]["own:identity"] == "not_selected_by_policy"
    assert d6["pages"]["5"]["own:identity"] == "unsupported:beyond_reader_scope" and d6["pages_beyond_reader_scope"] == 2 and d6["state"] == "incomplete"
    ok6 = sa.arm_coverage([PLAN[1]], {"d6": row("b" * 64, [attempt({str(i): full() for i in range(1, 5)}, read="b" * 64)])}, CTX, max_pages=4)["documents"][0]
    assert ok6["state"] == "complete_in_scope", "all in-scope pages usable, two pages beyond the scope: in-scope only, never 'complete'"
    assert s["complete_ids"] == ["d1"] and s["binding_reasons"]["no_row"] == 1
    assert c["transport"]["gone"] == "not_attempted" and c["transport"]["d1"] == "no_transport_stop"


def test_transport_success_with_unusable_fields_is_not_coverage():
    rows = {"d1": row("a" * 64, [attempt({"1": full("unusable:illegible", "incomplete:no_region", "incomplete:located_region_only")})])}
    c = sa.arm_coverage(PLAN[:1], rows, CTX, max_pages=4)
    assert c["transport"]["d1"] == "no_transport_stop" and c["summary"]["documents_required_complete"] == 0
    assert c["documents"][0]["pages"]["1"] == {"own:identity": "unusable", "own:revision": "no_region", "own:decision": "located_incomplete"}


def test_budget_timeout_and_discovery_failure_earn_nothing():
    rows = {"gone": row("d" * 64, [attempt({"1": {"outcome": "failed", "fields": {}}, "2": {"outcome": "budget: calls per document"}}, read="d" * 64,
                                            calls=[{"outcome": "timeout"}, {"outcome": "budget: calls_per_document"}])])}
    c = sa.arm_coverage([PLAN[3]], rows, CTX, max_pages=4)
    d = c["documents"][0]
    assert d["pages"]["1"]["own:identity"] == "failed" and d["pages"]["2"]["own:identity"] == "budget" and d["state"] == "incomplete"
    assert c["transport"]["gone"].startswith("transport_stop")


def test_extra_facts_outside_the_declared_scope_are_counted():
    obs = {"5": {"fields": {"own:identity": {"observations": [{"field": "identity", "value": "X-5", "state": "validated", "policy": "pol-L1"}]}}},
           "1": {"fields": {"own:identity": {"observations": [{"field": "identity", "value": "X-1", "state": "validated", "policy": "pol-OTHER"}]}}}}
    rows = {"d6": row("b" * 64, [attempt({str(i): full() for i in range(1, 5)}, read="b" * 64)], obs),
            "unplanned": {"sha256": "e" * 64, "extracted": {"ai_evidence": {"attempts": [], "envelopes": {"default|EV1": {"profile": "default", "variant": "EV1", "pages": {
                "1": {"fields": {"own:identity": {"observations": [{"field": "identity", "value": "U", "state": "candidate"}]}}}}}}}}}}
    c = sa.arm_coverage([PLAN[1]], rows, CTX, max_pages=4)
    why = sorted(tuple(x["why"]) for x in c["extra_facts_outside_scope"])
    assert why == [("other_policy",), ("page_beyond_reader_scope",), ("unplanned_document",)]
    assert c["summary"]["complete_ids"] == [] and c["summary"]["complete_in_scope_ids"] == ["d6"], "pages beyond the scope are never hidden"


def test_field_specific_matched_subsets_with_ids():
    a = sa.arm_coverage(PLAN[:2], {"d1": row("a" * 64, [attempt({"1": full()})]), "d6": row("b" * 64, [attempt({str(i): full() for i in range(1, 5)}, read="b" * 64)])}, CTX, max_pages=4)
    b = sa.arm_coverage(PLAN[:2], {"d1": row("a" * 64, [attempt({"1": full(rev="budget")})]), "d6": row("b" * 64, [attempt({str(i): full() for i in range(1, 5)}, read="b" * 64)])}, CTX, max_pages=4)
    assert sa.field_read_in_both(a, b, "own:identity", PLAN[:2]) == ["d1", "d6"]
    assert sa.field_read_in_both(a, b, "own:revision", PLAN[:2]) == ["d6"]
    assert sa.field_read_in_both(a, b, "own:decision", PLAN[:2]) == []       # discovery absence is never a read
