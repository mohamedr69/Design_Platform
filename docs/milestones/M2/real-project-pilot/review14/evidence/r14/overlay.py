"""The r14 evaluation overlay (OVERLAY_VERSION r2x-overlay-2026-09-30.1): types every critical fact of evaluator .9's
evidence layer against the amended labels' `supported_observations` and the AI target the stored row recorded.
See rescore_r14.py for the contract. Pure functions; no application import."""
import re

OVERLAY_VERSION = "r2x-overlay-2026-09-30.1"


def rev_norm(v):
    return re.sub(r"^REV\.?\s*", "", str(v or "").strip().upper()).replace(".", "")


def recorded_target(row, page, field, value):
    """(target, anchor identity) of the AI observation that asserted this value, from the stored row."""
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    for env in (ai.get("envelopes") or {}).values():
        for key, fld in ((env.get("pages") or {}).get(str(page), {}).get("fields") or {}).items():
            for o in fld.get("observations") or []:
                if o.get("field") == field and str(o.get("value")) == str(value):
                    return o.get("target"), (fld.get("anchor") or {}).get("identity"), key
    return "not_found", None, None


def overlay(result, page_labels, rows):
    sup = {k.replace("\\", "/"): (v.get("supported_observations") or {}) for k, v in page_labels["documents"].items()}
    rows = {k.replace("\\", "/"): v for k, v in rows.items()}
    typed, supported_facts = [], 0
    for d in result["documents"]:
        s = sup.get(d["doc"], {})
        for j in d["layers"]["evidence"]["judged"]:
            if j.get("state") in ("accepted", "observed", "validated", "held") and any(
                    o["field"] == j["field"] and (rev_norm(o["literal"]) == rev_norm(j.get("value")) if j["field"] == "revision" else o["literal"] == j.get("value"))
                    for o in s.get(str(j.get("page")), [])):
                supported_facts += 1
        for c in d["layers"]["evidence"]["critical"]:
            obs = s.get(str(c.get("page")), [])
            same = [o for o in obs if o["field"] == c["field"] and (rev_norm(o["literal"]) == rev_norm(c.get("value")) if c["field"] == "revision" else o["literal"] == c.get("value"))]
            other = [o for o in obs if o["field"] != c["field"] and rev_norm(o["literal"]) == rev_norm(c.get("value"))]
            target, anchor, key = recorded_target(rows.get(d["doc"]), c.get("page"), c["field"], c.get("value"))
            if same and "HELD" in (same[0].get("role") or "") and "candidate" in (same[0].get("role") or ""):
                kind = "role not established (held footer / control code accepted as identity)"
            elif same and target is None and anchor is None:
                kind = "correct literal, accepted without a supported target"
            elif same and target and target == same[0].get("association_target"):
                kind = "held association matching the proposal"
            elif other:
                kind = f"role error (a supported {other[0]['field']} literal accepted as {c['field']})"
            else:
                kind = "literal false accept"
            typed.append({"doc": d["doc"], "page": c.get("page"), "field": c["field"], "value": c.get("value"), "recorded_target": target,
                          "recorded_anchor_identity": anchor, "ai_field_key": key, "type": kind,
                          "critical": kind != "held association matching the proposal"})
    return {"overlay": OVERLAY_VERSION, "critical_typed": typed, "critical_after_overlay": sum(t["critical"] for t in typed),
            "supported_raw_observations": supported_facts}


