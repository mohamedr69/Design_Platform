"""Page / field-aware coverage and ONE eligibility contract, version 4 (M2 review 22).

CONTRACT_VERSION harness-contract-2026-09-30.v4

Eligibility (R22-01): evidence is evaluated ONLY when bound to the declared document (planned doc key), the declared
source hash (row sha256 == planned sha256 AND the attempt's read_sha256 == planned sha256) and the arm context (profile,
variant, policy). `eligible_rows` applies this once, before accuracy, coverage, matched subsets and the runner's
tripwire; an ineligible document contributes no evaluated evidence (it stays in the denominator as missed / not
attempted) and its rejected evidence is kept for diagnostics. Documents whose deterministic (raw) layer is from the right
bytes but whose AI attempt is of another context are 'raw_only' eligible: the evaluator scores the raw layer and no AI
evidence (the ai_context policies already exclude it; the AI envelope is removed here so nothing can leak).

Pages (R22-02): a fact's page is validated against the declared document's REAL page range and the reader's allowed
range: page_not_in_document (page > pages, or < 1), page_beyond_reader_scope (pages >= page > max_pages), invalid page
identifier (fail closed: reported with a diagnostic, never treated as in-scope). Field classes as v3."""
from __future__ import annotations

import collections
import copy

CONTRACT_VERSION = "harness-contract-2026-09-30.v4"
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
    if not row:
        return None, "no_row"
    if not planned.get("sha256"):
        return None, "planned_hash_missing"
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


def eligible_rows(rows: dict, planned: list[dict], ctx: dict | None) -> tuple[dict, dict, list]:
    """(rows to evaluate, eligibility per planned doc, rejected evidence diagnostics). ctx None = no AI context (the A
    base): only the source binding applies. An unplanned row is never evaluated (kept as rejected, 'unplanned')."""
    out, elig, rejected = {}, {}, []
    planned_by = {p["doc"]: p for p in planned}
    for p in planned:
        row = rows.get(p["doc"])
        if ctx is None:
            state = "no_row" if not row else "planned_hash_missing" if not p.get("sha256") else "source_mismatch" if row.get("sha256") != p["sha256"] else "bound"
        else:
            _, state = select_attempt(row, p, ctx)
        if state == "bound":
            out[p["doc"]] = row
            elig[p["doc"]] = {"state": "eligible", "reason": "bound"}
        elif state in ("context_mismatch", "not_attempted") and row is not None:
            r = copy.deepcopy(row)                       # the raw layer is from the declared bytes; no AI evidence of another context may leak
            (r.get("extracted") or {}).pop("ai_evidence", None)
            out[p["doc"]] = r
            elig[p["doc"]] = {"state": "raw_only", "reason": state}
            if state == "context_mismatch":
                rejected.append({"doc": p["doc"], "why": "ai_evidence_of_another_context", "attempts": [{k: a.get(k) for k in ("policy", "profile", "variant", "read_sha256")}
                                                                                                        for a in (((row.get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or [])]})
        else:
            elig[p["doc"]] = {"state": "ineligible", "reason": state}
            if row is not None:
                rejected.append({"doc": p["doc"], "why": state, "row_sha256": row.get("sha256"), "planned_sha256": p.get("sha256")})
    for key, row in rows.items():
        if key not in planned_by:
            rejected.append({"doc": key, "why": "unplanned", "row_sha256": (row or {}).get("sha256")})
    return out, elig, rejected


def page_coverage(page_entry) -> dict:
    if page_entry is None:
        return {f: "missing_page" for f in REQUIRED_FIELDS}
    if not isinstance(page_entry, dict):
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
    state = "complete" if in_scope_usable and not beyond else "complete_in_scope" if in_scope_usable else "incomplete"
    return {"doc": doc, "state": state, "pages": per_page, "in_scope_pages": len(in_scope), "pages_beyond_reader_scope": len(beyond),
            "attempted": attempt is not None, "reason": reason}


def page_position(page_id, planned: dict | None, max_pages: int) -> list[str]:
    """Why an emitted page is outside the declared supported scope ([] when it is a real in-scope page)."""
    if planned is None:
        return ["unplanned_document"]
    if planned.get("extension", ".pdf") != ".pdf":
        return ["unsupported_input"]
    try:
        n = int(str(page_id))
        if str(n) != str(page_id).strip() or n < 1:
            raise ValueError
    except (TypeError, ValueError):
        return ["invalid_page_identifier"]
    pages = planned.get("pages")
    if not pages or n > pages:
        return ["page_not_in_document"]
    if n > max_pages:
        return ["page_beyond_reader_scope"]
    return []


def extra_facts(row: dict | None, planned: dict | None, ctx: dict, *, max_pages: int) -> list[dict]:
    """Emitted AI facts outside the declared supported scope: nonexistent pages, pages beyond the reader scope,
    unplanned / unsupported documents, invalid page identifiers, other contexts / policies -- counted, never ignored."""
    if not row:
        return []
    ai = ((row.get("extracted") or {}).get("ai_evidence") or {})
    out = []
    for key, env in (ai.get("envelopes") or {}).items():
        for pno, pg in (env.get("pages") or {}).items():
            for fk, fe in ((pg or {}).get("fields") or {}).items():
                for o in fe.get("observations") or []:
                    why = page_position(pno, planned, max_pages)
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
