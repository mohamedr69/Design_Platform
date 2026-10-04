"""R15-03: the evaluation overlay as an ANNOTATION layer -- it has NO authority over acceptance or recovery.

OVERLAY_VERSION r2x-overlay-2026-09-30.r15.1   (r14.1 preserved in the Review 14 package; it could clear a critical)

Authority
  * Critical errors, acceptance and recovery are exactly the established evaluator's (m2_eval5 .9, context-bound):
    `critical_after_overlay` always equals the evaluator's count; nothing here removes, adds or re-scores a fact.
  * The overlay only ANNOTATES each critical fact with: whether the literal is supported by a labelled observation,
    that observation's explicit role / association states, and the target the reader recorded for THIS fact.

Context (never a fallback)
  * The fact's context is the run's declared context carried by the evaluator result (`result['ai_context']`:
    profile and variant) or passed explicitly, plus the document's content hash. The recorded target is read ONLY from
    that context's envelope (key '<profile>|<variant>'), only if the envelope's content hash (read_sha256 / sha256)
    equals the row's hash when both are present, only on the fact's page, component (from the evaluator's group
    'ai:<page>:<component>') and field, and only from an observation whose value equals the fact's value EXACTLY.
    No other envelope is scanned; a missing or mismatched context gives 'context_unknown' / 'context_mismatch'.
Literal support
  * exact literal equality, except ONE declared prefix normalization for revisions: a leading 'Rev' / 'Rev.' /
    'Revision' label (and following spaces) is removed. Internal punctuation is kept: 'Rev.0' ~ '0', but '1.0' != '10'.
States (explicit enums; free text is never read as authority)
  * role_state: 'revision' | 'identity' | 'footer_control_candidate_held' | 'unknown'
  * association_state: 'no_target' | 'proposal_only' | 'held' | 'approved' | 'unknown'
  * recorded_state: the reader's own state of the observation ('validated' / 'held' / ...), as stored
  * annotation types (descriptive only): 'literal supported; reader accepted without a target',
    'literal supported; reader target equals an UNAPPROVED proposal (acceptance still an error)',
    'literal of another role accepted as <field>', 'role not established (held) but accepted', 'literal not supported',
    'context unknown / mismatch'."""
import re

OVERLAY_VERSION = "r2x-overlay-2026-09-30.r15.1"
_REV_PREFIX = re.compile(r"^\s*(?:REVISION|REV)\.?\s*", re.IGNORECASE)
ROLE_STATES = {"revision", "identity", "footer_control_candidate_held", "unknown"}
ASSOCIATION_STATES = {"no_target", "proposal_only", "held", "approved", "unknown"}


def rev_literal(v) -> str:
    """The declared revision prefix normalization only; internal punctuation kept ('1.0' stays '1.0')."""
    return _REV_PREFIX.sub("", str(v or "").strip()).upper()


def literal_equal(field: str, a, b) -> bool:
    return rev_literal(a) == rev_literal(b) if field == "revision" else str(a or "").strip() == str(b or "").strip()


def _context(result, ai_context):
    ctx = ai_context if ai_context is not None else (result.get("ai_context") if isinstance(result, dict) else None)
    if not ctx or not ctx.get("variant"):
        return None
    return f"{ctx.get('profile') or 'default'}|{ctx['variant']}"


def recorded_observation(row, ctx_key, page, component, field, value):
    """(status, observation) from the ACTIVE context's envelope only."""
    if ctx_key is None:
        return "context_unknown", None
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    env = (ai.get("envelopes") or {}).get(ctx_key)
    if env is None:
        return "context_unknown", None
    env_sha = env.get("read_sha256") or env.get("sha256")
    row_sha = (row or {}).get("sha256")
    if env_sha and row_sha and env_sha != row_sha:
        return "context_mismatch", None
    fld = ((env.get("pages") or {}).get(str(page), {}).get("fields") or {}).get(f"{component}:{field}")
    if not fld:
        return "fact_not_in_context", None
    obs = [o for o in fld.get("observations") or [] if o.get("field") == field and str(o.get("value")) == str(value)]
    if len(obs) != 1:
        return ("fact_not_in_context" if not obs else "fact_ambiguous_in_context"), None
    return "found", dict(obs[0], _anchor_identity=(fld.get("anchor") or {}).get("identity"))


def _component(fact) -> str:
    g = str(fact.get("group") or "")
    parts = g.split(":")
    return parts[2] if len(parts) >= 3 and parts[0] == "ai" else "own"


def _states(o) -> tuple[str, str]:
    """Explicit states; a label without them is 'unknown' (never inferred from free text)."""
    role = o.get("role_state") if o.get("role_state") in ROLE_STATES else "unknown"
    assoc = o.get("association_state") if o.get("association_state") in ASSOCIATION_STATES else "unknown"
    return role, assoc


def overlay(result, page_labels, rows, ai_context=None):
    ctx_key = _context(result, ai_context)
    sup = {k.replace("\\", "/"): (v.get("supported_observations") or {}) for k, v in (page_labels.get("documents") or {}).items()}
    rows = {k.replace("\\", "/"): v for k, v in rows.items()}
    annotations, supported = [], 0
    evaluator_critical = 0
    for d in result["documents"]:
        s = sup.get(d["doc"], {})
        for j in d["layers"]["evidence"]["judged"]:
            if any(o.get("field") == j.get("field") and literal_equal(j.get("field"), o.get("literal"), j.get("value")) for o in s.get(str(j.get("page")), [])):
                supported += 1
        for c in d["layers"]["evidence"]["critical"]:
            evaluator_critical += 1
            obs = s.get(str(c.get("page")), [])
            same = [o for o in obs if o.get("field") == c["field"] and literal_equal(c["field"], o.get("literal"), c.get("value"))]
            other = [o for o in obs if o.get("field") != c["field"] and literal_equal("revision", o.get("literal"), c.get("value"))]
            status, rec = recorded_observation(rows.get(d["doc"]), ctx_key, c.get("page"), _component(c), c["field"], c.get("value"))
            target = rec.get("target") if rec else None
            role, assoc = _states(same[0]) if same else (_states(other[0]) if other else ("unknown", "unknown"))
            if status != "found":
                kind = status.replace("_", " ")
            elif same and role == "footer_control_candidate_held":
                kind = "role not established (held) but accepted"
            elif same and target is not None and target == same[0].get("association_target"):
                kind = "literal supported; reader target equals an UNAPPROVED proposal (acceptance still an error)" if assoc != "approved" \
                    else "literal supported; reader target equals the approved association"
            elif same and target is None:
                kind = "literal supported; reader accepted without a target"
            elif other:
                kind = f"literal of another role ({other[0].get('field')}) accepted as {c['field']}"
            elif same:
                kind = "literal supported; reader target differs from the label"
            else:
                kind = "literal not supported"
            annotations.append({"doc": d["doc"], "page": c.get("page"), "field": c["field"], "value": c.get("value"), "fact_state": c.get("state"),
                                "context": ctx_key, "context_status": status, "recorded_target": target,
                                "recorded_state": (rec or {}).get("state"), "recorded_anchor_identity": (rec or {}).get("_anchor_identity"),
                                "literal_supported": bool(same), "role_state": role, "association_state": assoc, "annotation": kind,
                                "critical": True})                        # the evaluator's verdict, unchanged
    return {"overlay": OVERLAY_VERSION, "authority": "annotation only: acceptance / recovery / critical are the evaluator's",
            "context": ctx_key, "annotations": annotations, "critical_typed": annotations,
            "critical_evaluator": evaluator_critical, "critical_after_overlay": evaluator_critical,
            "supported_raw_observations": supported}
