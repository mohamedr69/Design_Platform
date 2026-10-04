"""Unit tests for the DRAFT page / field-aware coverage (synthetic inputs; offline)."""
import coverage_v3_draft as cv

PLAN = {"doc": "d", "extension": ".pdf", "pages": 3}


def att(pages):
    return {"pages": pages}


def full(p="completed"):
    return {"outcome": "evidence", "fields": {"own:identity": p, "own:revision": p, "own:decision": "absent_by_discovery"}}


def test_every_declared_page_is_counted_and_a_missing_page_fails_closed():
    got = cv.document_coverage(PLAN, att({"1": full(), "2": full()}), max_pages=4)
    assert set(got["pages"]) == {"1", "2", "3"} and got["pages"]["3"] == {f: "missing_page" for f in cv.REQUIRED_FIELDS}
    assert got["state"] == "incomplete"


def test_first_page_complete_is_not_document_complete():
    got = cv.document_coverage(PLAN, att({"1": full(), "2": {"outcome": "no_trigger"}, "3": full()}), max_pages=4)
    assert got["pages"]["2"]["own:identity"] == "not_selected_by_policy" and got["state"] == "incomplete"


def test_all_pages_usable_is_complete():
    assert cv.document_coverage(PLAN, att({"1": full(), "2": full(), "3": full()}), max_pages=4)["state"] == "complete"


def test_pages_beyond_the_reader_scope_are_declared_unsupported_not_truncated():
    got = cv.document_coverage({"doc": "d", "extension": ".pdf", "pages": 6}, att({str(i): full() for i in range(1, 5)}), max_pages=4)
    assert got["pages"]["5"]["own:identity"] == "unsupported:beyond_reader_scope" and got["pages_beyond_reader_scope"] == 2
    assert got["state"] == "incomplete"


def test_unattempted_and_unsupported_documents_stay_in_the_denominator():
    a = cv.document_coverage(PLAN, None, max_pages=4)
    b = cv.document_coverage({"doc": "w", "extension": ".docx", "pages": None}, None, max_pages=4)
    s = cv.summarize([a, b])
    assert s["documents_planned"] == 2 and s["documents_unsupported_input"] == 1 and a["pages"]["1"]["own:decision"] == "not_attempted"


def test_timeouts_budget_and_located_absence_are_not_usable():
    got = cv.document_coverage({"doc": "d", "extension": ".pdf", "pages": 1},
                               att({"1": {"outcome": "partial", "fields": {"own:identity": "failed:timeout", "own:revision": "budget",
                                                                            "own:decision": "incomplete:located_region_only"}}}), max_pages=4)
    assert got["pages"]["1"] == {"own:identity": "failed", "own:revision": "budget", "own:decision": "located_incomplete"}
    assert got["state"] == "incomplete"


def test_page_level_budget_and_discovery_failure():
    got = cv.document_coverage({"doc": "d", "extension": ".pdf", "pages": 2},
                               att({"1": {"outcome": "failed", "fields": {}}, "2": {"outcome": "budget: calls per document"}}), max_pages=4)
    assert got["pages"]["1"]["own:identity"] == "failed" and got["pages"]["2"]["own:identity"] == "budget"
