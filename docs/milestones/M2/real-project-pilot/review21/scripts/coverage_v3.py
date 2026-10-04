"""Page / field-aware coverage, version 3 (the review20 draft made caller-safe):

  select_attempt(row, planned, ctx)   binds the arm's attempt to the DECLARED source hash, profile, variant and policy;
                                      anything else is 'not attempted' with a reason (never scored as read)
  document_coverage(planned, attempt, max_pages)   every declared page: unsupported input / beyond-scope pages / missing
                                      pages (fail closed) / not selected / budget / failed / per-field classes
  extra_facts(row, planned, ctx, max_pages)   emitted facts OUTSIDE the declared supported scope (pages beyond scope,
                                      unplanned documents, other contexts) -- counted, never ignored
  summarize(docs)
Field classes: completed_read | discovery_absent | located_incomplete | no_region | unusable | failed | budget |
not_attempted | missing_page | not_selected_by_policy | unsupported:beyond_reader_scope. Only completed_read and
discovery_absent are usable; discovery_absent is never a read. Transport state is not coverage (kept elsewhere)."""
from __future__ import annotations

import collections

COVERAGE_VERSION = "coverage-2026-09-30.v3"
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


def select_attempt(row: dict | None, planned: dict, ctx: dict) -> tuple[dict | None, str]:
    """(attempt, reason). The attempt must have been read from the planned bytes (read_sha256 == planned sha256) under
    the declared profile / variant / policy. The row's own sha256 must equal the planned one too."""
    if not row:
        return None, "no_row"
    if row.get("sha256") != planned["sha256"]:
        return None, "source_mismatch"
    ai = ((row.get("extracted") or {}).get("ai_evidence") or {})
    atts = [a for a in ai.get("attempts") or []
            if a.get("policy") == ctx["policy"] and a.get("profile") == ctx["profile"] and a.get("variant") == ctx["variant"]
            and a.get("read_sha256") == planned["sha256"]]
    if not atts:
        others = [a for a in ai.get("attempts") or [] if a.get("read_sha256") == planned["sha256"]]
        return None, "context_mismatch" if others else "not_attempted"
    return atts[-1], "bound"


def page_coverage(page_entry) -> dict:
    if page_entry is None:
        return {f: "missing_page" for f in REQUIRED_FIELDS}
    if not isinstance(page_entry, dict):                      # legacy string outcomes
        page_entry = {"outcome": str(page_entry), "fields": {}}
    outcome = str(page_entry.get("outcome") or "")
    if outcome == "no_trigger":
        return {f: "not_selected_by_policy" for f in REQUIRED_FIELDS}
    fields = page_entry.get("fields") or {}
    if not fields and outcome.startswith("budget"):
        return {f: "budget" for f in REQUIRED_FIELDS}
    if not fields and outcome == "failed":
        return {f: "failed" for f in REQUIRED_FIELDS}
    return {f: field_class(fields.get(f)) for f in REQUIRED_FIELDS}


def document_coverage(planned: dict, attempt: dict | None, *, max_pages: int, reason: str = "") -> dict:
    doc, pages = planned["doc"], planned.get("pages")
    if planned.get("extension", ".pdf") != ".pdf" or not pages:
        return {"doc": doc, "state": "unsupported_input", "pages": {}, "unsupported": planned.get("extension"), "reason": reason}
    in_scope = list(range(1, min(pages, max_pages) + 1))
    beyond = list(range(max_pages + 1, pages + 1))
    per_page = {}
    if attempt is None:
        per_page = {str(p): {f: "not_attempted" for f in REQUIRED_FIELDS} for p in in_scope}
    else:
        stored = attempt.get("pages") or {}
        for p in in_scope:
            per_page[str(p)] = page_coverage(stored.get(str(p)))
    for p in beyond:
        per_page[str(p)] = {f: "unsupported:beyond_reader_scope" for f in REQUIRED_FIELDS}
    in_scope_usable = attempt is not None and all(c in USABLE for p in in_scope for c in per_page[str(p)].values())
    # 'complete' only when the WHOLE document is within the reader scope and every required field of every page is usable;
    # 'complete_in_scope' when every in-scope page is usable but pages beyond the scope exist (never hidden)
    state = "complete" if in_scope_usable and not beyond else "complete_in_scope" if in_scope_usable else "incomplete"
    return {"doc": doc, "state": state, "pages": per_page, "in_scope_pages": len(in_scope),
            "pages_beyond_reader_scope": len(beyond), "attempted": attempt is not None, "reason": reason}


def extra_facts(row: dict | None, planned: dict | None, ctx: dict, *, max_pages: int) -> list[dict]:
    """Emitted AI facts outside the declared supported scope: on pages beyond the reader scope of a planned document, on
    an unplanned document, or under another context (profile / variant / policy) than the declared one."""
    if not row:
        return []
    ai = ((row.get("extracted") or {}).get("ai_evidence") or {})
    out = []
    for key, env in (ai.get("envelopes") or {}).items():
        for pno, pg in (env.get("pages") or {}).items():
            for fk, fe in (pg.get("fields") or {}).items():
                for o in fe.get("observations") or []:
                    why = []
                    if planned is None:
                        why.append("unplanned_document")
                    elif planned.get("extension", ".pdf") != ".pdf":
                        why.append("unsupported_input")
                    elif int(pno) > max_pages:
                        why.append("page_beyond_reader_scope")
                    if env.get("profile") != ctx["profile"] or env.get("variant") != ctx["variant"]:
                        why.append("other_context")
                    elif o.get("policy") not in (None, ctx["policy"]):
                        why.append("other_policy")
                    if why:
                        out.append({"doc": planned["doc"] if planned else row.get("doc"), "page": pno, "field": fk, "value": o.get("value"), "state": o.get("state"), "why": why})
    return out


def summarize(docs: list[dict]) -> dict:
    per_class = {f: collections.Counter() for f in REQUIRED_FIELDS}
    reasons = collections.Counter(d.get("reason") for d in docs if d.get("reason"))
    for d in docs:
        for pc in d["pages"].values():
            for f, c in pc.items():
                per_class[f][c] += 1
    return {"documents_planned": len(docs), "documents_required_complete": sum(1 for d in docs if d["state"] == "complete"),
            "documents_unsupported_input": sum(1 for d in docs if d["state"] == "unsupported_input"),
            "documents_unattempted": sum(1 for d in docs if d["state"] != "unsupported_input" and not d.get("attempted")),
            "documents_complete_in_scope_only": sum(1 for d in docs if d["state"] == "complete_in_scope"),
            "binding_reasons": dict(reasons), "page_field_classes": {f: dict(c) for f, c in per_class.items()},
            "complete_ids": [d["doc"] for d in docs if d["state"] == "complete"],
            "complete_in_scope_ids": [d["doc"] for d in docs if d["state"] == "complete_in_scope"]}
