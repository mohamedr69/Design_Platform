"""Synthetic r32 truth and lanes for the scorer and concentration tests (no real label value is used)."""
from __future__ import annotations

FIELDS = ("identity", "revision", "decision")


def row(pid, page, field, kind, literal=None, cls=None, reasons=None, resub=False, alternates=(), candidates=()):
    return {"pool_id": pid, "page": str(page), "field": field, "state": {"value": "present", "absent": "absent", "not_scorable": "ambiguous"}[kind],
            "association": "resolved" if kind != "absent" else None, "literal": literal, "class": cls if field == "decision" else None,
            "actor": None, "actor_state": None, "absent_kind": "no_decision_area" if kind == "absent" and field == "decision" else None,
            "location": None, "printed_label": None, "semantic_role": None, "resubmission_required": resub, "excluded_from_scoring": False,
            "review_status": "accepted", "candidates": list(candidates), "doc_resolved_for_scoring": "yes", "doc_carries_fact": "yes",
            "truth_kind": kind, "scorable": kind != "not_scorable", "not_scorable_reasons": list(reasons or ([] if kind != "not_scorable" else ["ambiguous"])),
            "alternates": list(alternates), "alternate_kinds": {}, "count_once_alias_of": None}


def doc(pid, project="p0", contractor=None, layout="L0", stratum="review_signal", decision=True, identity=True, revision=True,
        decision_resolved=True, alias_of=None, dtype=None):
    has = {"identity": identity, "revision": revision, "decision": decision}
    fields = {f: {"resolved_for_scoring": "yes" if (f != "decision" or decision_resolved) else "no",
                  "carries_fact": "yes" if has[f] else "no", "primary": f != "decision" or decision_resolved,
                  "has_fact": has[f] and (f != "decision" or decision_resolved)} for f in FIELDS}
    return {"pool_id": pid, "canonical_id": alias_of or pid, "is_alias": alias_of is not None, "alias_kind": None, "ep": project,
            "project": project, "contractor": contractor or f"contractor-{project}", "doc_key": f"{project}/{pid}.pdf", "relative_path": f"{pid}.pdf",
            "staged_sha256": pid * 4, "stratum": stratum, "how": stratum, "selection_order": 1, "in_scope_pages": 1, "page_count": 1,
            "labelled_pages": ["1"], "compilation": False, "layout_key": layout, "layout_rule": "test", "kind": "test", "independent_review": True,
            "fields": fields, "decision_type": dtype or ("approved" if decision else "none"),
            "decision_control": "positive" if decision and decision_resolved else ("negative" if decision_resolved else "none")}


def truth(n=16, projects=4, layouts=None, negatives=0, contractors=None):
    docs, rows = {}, {}
    for i in range(n):
        pid = f"D{i:02d}"
        p = f"p{i % projects}"
        lay = layouts[i] if layouts else f"L{i % projects}"
        docs[pid] = doc(pid, project=p, layout=lay, contractor=(contractors[i] if contractors else None))
        rows[f"{pid}|1|identity"] = row(pid, 1, "identity", "value", f"ID-{i}")
        rows[f"{pid}|1|revision"] = row(pid, 1, "revision", "value", "01")
        rows[f"{pid}|1|decision"] = row(pid, 1, "decision", "value", "APPROVED", cls="approved")
    for j in range(negatives):
        pid = f"N{j:02d}"
        docs[pid] = doc(pid, project=f"p{j % projects}", layout="LN", decision=False, revision=False, stratum="drawing_signal")
        rows[f"{pid}|1|identity"] = row(pid, 1, "identity", "value", f"NID-{j}")
        rows[f"{pid}|1|revision"] = row(pid, 1, "revision", "absent")
        rows[f"{pid}|1|decision"] = row(pid, 1, "decision", "absent")
    return {"schema": "r32-truth-1", "aliases": {}, "compilations": [], "documents": docs, "rows": rows}


def facts_for(T, pid, *, correct=(), wrong=(), state="accepted"):
    out = []
    for f in FIELDS:
        r = T["rows"].get(f"{pid}|1|{f}")
        if f in correct and r and r["truth_kind"] == "value":
            out.append({"page": "1", "field": f, "value": r["literal"] if f != "decision" else "approved", "state": state})
        if f in wrong:
            out.append({"page": "1", "field": f, "value": "WRONG-1" if f != "decision" else "rejected", "state": state})
    return out


def lane(name, T, *, correct=None, wrong=None, extra_facts=None, requests=0, inherited=0, cov=None, attempted=None):
    """correct / wrong: {pid: set(fields)}; every truth document is in the lane (attempted unless attempted excludes it)."""
    docs = {}
    for pid in T["documents"]:
        fs = facts_for(T, pid, correct=(correct or {}).get(pid, ()), wrong=(wrong or {}).get(pid, ()))
        fs += (extra_facts or {}).get(pid, [])
        docs[pid] = {"attempted": attempted is None or pid in attempted, "unsupported": False, "facts": fs,
                     "coverage": {"1": (cov or {}).get(pid, {"decision": "completed_read"})}}
    return {"lane": name, "documents": docs, "requests": {"own_dispatched": requests, "inherited_from_b": inherited}}


def all_fields(T, ids=None):
    return {pid: set(FIELDS) for pid in T["documents"] if ids is None or pid in ids}
