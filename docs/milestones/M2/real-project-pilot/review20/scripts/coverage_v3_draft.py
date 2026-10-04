"""DRAFT page / field-aware coverage (proposed for the next experiment; offline prototype, not an application change).

Unlike the accepted single-page continuation replay (v2), every DECLARED page of every PLANNED document is accounted for:
  * a planned document with no row or no attempt of the arm        -> every in-scope page: not_attempted
  * a file the reader cannot take (non-PDF, unreadable)            -> unsupported_input (never dropped)
  * PDF pages beyond the reader's page scope (MAX_PAGES_PER_DOCUMENT) -> unsupported:beyond_reader_scope, per page
  * an in-scope page with no entry in the attempt's coverage       -> missing_page (FAIL CLOSED: never treated as read)
  * an in-scope page the EV policy did not select                  -> not_selected_by_policy
  * a page-level budget / failure                                  -> budget / failed
  * otherwise each REQUIRED field by class: completed_read / discovery_absent / located_incomplete / no_region /
    unusable / failed / budget / not_attempted  (same classes as v2; discovery absence is never a read)
A document's required coverage is 'complete' only when every in-scope page has every required field completed_read or
discovery_absent and no page is missing / unsupported / unattempted. Transport state stays a separate report.
Functions are pure (inputs: planned documents, arm rows, attempt selector) so they can be unit-tested."""
from __future__ import annotations

import collections

REQUIRED_FIELDS = ("own:identity", "own:revision", "own:decision")
USABLE = ("completed_read", "discovery_absent")


def field_class(outcome) -> str:
    o = str(outcome or "not_attempted")
    if o == "completed":
        return "completed_read"
    if o == "absent_by_discovery":
        return "discovery_absent"
    if o == "incomplete:located_region_only":
        return "located_incomplete"
    if o == "incomplete:no_region":
        return "no_region"
    for p, k in (("unusable", "unusable"), ("failed", "failed"), ("budget", "budget")):
        if o.startswith(p):
            return k
    return "not_attempted"


def page_coverage(page_entry: dict | None) -> dict:
    """Required-field classes of one in-scope page from its attempt coverage entry (None: missing)."""
    if page_entry is None:
        return {f: "missing_page" for f in REQUIRED_FIELDS}
    outcome = str(page_entry.get("outcome") or "")
    if outcome == "no_trigger":
        return {f: "not_selected_by_policy" for f in REQUIRED_FIELDS}
    fields = page_entry.get("fields") or {}
    if not fields and outcome.startswith("budget"):
        return {f: "budget" for f in REQUIRED_FIELDS}
    if not fields and outcome == "failed":
        return {f: "failed" for f in REQUIRED_FIELDS}
    return {f: field_class(fields.get(f)) for f in REQUIRED_FIELDS}


def document_coverage(planned: dict, attempt: dict | None, *, max_pages: int) -> dict:
    """planned: {'doc', 'extension', 'pages'}; attempt: the arm's latest attempt for the context, or None."""
    doc, pages = planned["doc"], planned.get("pages")
    if planned.get("extension", ".pdf") != ".pdf" or not pages:
        return {"doc": doc, "state": "unsupported_input", "pages": {}, "unsupported": planned.get("extension")}
    in_scope = list(range(1, min(pages, max_pages) + 1))
    beyond = list(range(max_pages + 1, pages + 1))
    per_page = {}
    if attempt is None:
        per_page = {str(p): {f: "not_attempted" for f in REQUIRED_FIELDS} for p in in_scope}
    else:
        stored = attempt.get("pages") or {}
        for p in in_scope:
            entry = stored.get(str(p))
            if entry is not None and not isinstance(entry, dict):      # legacy string outcomes
                entry = {"outcome": str(entry), "fields": {}}
            per_page[str(p)] = page_coverage(entry)
    for p in beyond:
        per_page[str(p)] = {f: "unsupported:beyond_reader_scope" for f in REQUIRED_FIELDS}
    complete = all(c in USABLE for pc in per_page.values() for c in pc.values())
    return {"doc": doc, "state": "complete" if complete else "incomplete", "pages": per_page, "in_scope_pages": len(in_scope),
            "pages_beyond_reader_scope": len(beyond), "attempted": attempt is not None}


def summarize(docs: list[dict]) -> dict:
    per_class = {f: collections.Counter() for f in REQUIRED_FIELDS}
    for d in docs:
        for pc in d["pages"].values():
            for f, c in pc.items():
                per_class[f][c] += 1
    return {"documents_planned": len(docs), "documents_required_complete": sum(1 for d in docs if d["state"] == "complete"),
            "documents_unsupported_input": sum(1 for d in docs if d["state"] == "unsupported_input"),
            "page_field_classes": {f: dict(c) for f, c in per_class.items()},
            "complete_ids": [d["doc"] for d in docs if d["state"] == "complete"]}
