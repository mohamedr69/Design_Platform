"""ORCH-05.1 (Review 33 C-5, R33-01/R33-05), ORCH-05C (Review 34 RC-2 / R34-02) and ORCH-08 (A-09 points 1, 5, 6 and 7):
the Review 31 B / C scorer rules, applied PER FIELD over the r32 truth, with ONE candidate-level outcome.

The Review 31 file harness-base/score_bcr.py (5a3828a5...) is unchanged; SCORER-CHANGES.md (v3) lists every difference.
Inputs: normalised r32 lanes (lane_judge_r32 format, from score_lane_r32) and the r32 truth.
Rules kept from Review 31 (same constants, same seeds):
  * population gate: each of identity, revision, decision >= 12 resolved, independently reviewed documents carrying the
    fact (canonical ids; count-once aliases never counted), else the next extension, else PREPARATION BLOCKED;
  * the document is the unit; y(doc, f) = 1 iff a clean recovery on a SCORABLE row of f; resolved per field;
  * paired difference: document-cluster bootstrap stratified by project, 2,000 resamples, seed m2-r30-bootstrap-2026-10-02;
  * request gate at EQUAL caps only (240/240): net correct facts x 8 >= extra requests, no new false acceptance,
    bootstrap interval of the net gain per document excluding zero; unequal caps -> not applicable;
  * thresholds: zero critical acceptance on resolved truth in C; accepted precision >= 0.98 and clean recovery >= 0.90
    per field; matched >= 12 per field;
  * decision coverage: completed read or verified absence; wrong absence and located_incomplete never count; NOT_SCORABLE
    rows never count either way;
  * outcomes ELIGIBLE FOR A SEPARATE SELECTION DECISION / NOT ELIGIBLE / INCOMPLETE / INVALID / PREPARATION BLOCKED; no
    default is ever selected (default_selected is always None).
Candidate-level outcome (RC-2; result["outcome"], the ONLY comparison outcome): C is one switch set and is judged as a
whole; per-field outcomes are diagnostics. It reads ONLY B and C.
ORCH-08 changes:
  (A-09 point 6, R38-09) R and P earn NO accuracy or recovery credit anywhere: R's metrics, its decision controls and the
    C >= R decision-coverage contrast are DIAGNOSTICS (result["diagnostics"]["R"], credit 'none'); the decision coverage
    GATE is C >= B only -- a CHANGE FROM PLAN V2, whose gate was C >= B and C >= R (ruled by the owner, A-10); the
    candidate outcome never reads R or P (a full R, a truncated R and no R give the same outcome). When R (or P) could not complete its declared diagnostic population (the run set; P: the seeded sample) --
    a lane stop, a refusal, a deferral, a lane that never started -- the diagnostic is INCOMPLETE and the contrast says so.
  (A-09 point 1) every run-set document stays in every coverage and recovery denominator whatever happened to it; a B or C
    document that a limit refused or deferred ('limit' class, or DEFERRED) makes the comparison INCOMPLETE and is listed
    in result["limit_incomplete"]; such documents are excluded from the MATCHED sets (paired, request gate,
    concentration) with each exclusion listed in result["matched_exclusions"] -- never silently.
  (A-09 point 5) result["scope_limitations"] always carries the unsupported-control shortfall (a declared limitation that
    no argument removes) and result["not_claimed"] states that unsupported-format safety and generalization are not
    claimed.
ORCH-08C changes (Verification 39):
  (R39-15; owner ruling A-10, 2026-10-04) the decision coverage gate is ONE named constant, DECISION_COVERAGE_GATE =
    'C_GE_B_ONLY', whose definition (id and text) is in DECISION_COVERAGE_GATE_DEFINITIONS: decision coverage eligibility
    is C >= B ONLY. This is a CHANGE FROM PLAN V2 (plan v2's gate was C >= B and C >= R; PLAN_V2_DECISION_COVERAGE_GATE
    keeps its text for the record); it is never an unchanged gate. C >= R is a MANDATORY diagnostic in EVERY result
    (result["decision_coverage_C_ge_R"]): the counts of both lanes, the missing coverage per document with its reasons,
    INCOMPLETE when R did not complete its population; it never determines eligibility. A definition that binds R into
    eligibility (the plan v2 gate, or any other) is REFUSED by evaluate() and by the declaration contract
    (decision_coverage_gate must be 'C_GE_B_ONLY'). Every other safety, accuracy and completeness gate is unchanged.
  (R39-06) result["unread_pages"] reports per lane the documents with pages the application did not read under its own
    per-document limits (reader cap, JobBudget, reader exception) and the pages; such documents stay COMPLETE and their
    pages stay in every coverage denominator (they count as unread).
Pure; nothing reads a model, a provider or a ledger."""
from __future__ import annotations

import collections
import random

import concentration_r32 as K
import labels_adapter_r32 as A
import lane_judge_r32 as J

FIELDS = A.FIELDS
MINIMUM = 12
EXTENSIONS = ("extension-1", "extension-2")
THRESHOLDS = {"accepted_precision_min": 0.98, "clean_recovery_min": 0.90, "critical_on_resolved_max": 0, "facts_per_extra_requests": 8}
CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
BOOTSTRAP_SEED = "m2-r30-bootstrap-2026-10-02"
OUTCOMES = ("ELIGIBLE FOR A SEPARATE SELECTION DECISION", "NOT ELIGIBLE", "INCOMPLETE", "INVALID", "PREPARATION BLOCKED")
CANDIDATE_PRECEDENCE = ("INVALID", "NOT ELIGIBLE", "INCOMPLETE")
CANDIDATE_RULE = ("candidate-level outcome (RC-2): a comparison state other than INVALID / INCOMPLETE (PREPARATION BLOCKED, "
                  "NOT DISPATCHABLE) is the outcome; otherwise ELIGIBLE FOR A SEPARATE SELECTION DECISION only when all three "
                  "fields are ELIGIBLE, else the first of INVALID > NOT ELIGIBLE > INCOMPLETE among the field outcomes; the "
                  "per-field outcomes are diagnostics; it reads only B and C (never R or P); no default is ever selected")
REFERENCE_SET_STATEMENT = K.REFERENCE_SET_STATEMENT
SCOPE_LIMITATIONS = ({"id": "unsupported-control-shortfall", "declared_by": "A-09 point 5 (owner)", "required": 2, "found": 0,
                      "statement": ("the run set holds 0 of the 2 unsupported-format controls plan v2 section 2.3 requires: no canonical pool "
                                    "document has an in-scope page labelled 'unsupported' or 'illegible' in r32-labels-reviewed-2; the "
                                    "shortfall is accepted ONLY as a declared scope limitation; no control is replaced once a prediction "
                                    "exists for the run (run_set_selector_r32.replace_controls); this limitation is never removed from a report")},)
NOT_CLAIMED = ("unsupported-format safety (no unsupported or illegible control was read)",
               "generalization beyond the six cohort projects, their contractors and their layouts")
# ORCH-08C (R39-15) and owner ruling A-10 (2026-10-04): the decision coverage gate as ONE named constant carrying its text.
DECISION_COVERAGE_GATE_DEFINITIONS = {
    "C_GE_B_ONLY": {
        "id": "C_GE_B_ONLY",
        "text": ("decision coverage eligibility: decision coverage of C >= decision coverage of B on the resolved decision documents of "
                 "the run set (completed read or verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE "
                 "rows are never coverage). C >= R is a MANDATORY diagnostic -- reported in every result with both lanes' counts, the "
                 "missing coverage per document and its reasons, INCOMPLETE when R did not complete its population -- and it never "
                 "determines eligibility"),
        "reads_R": False, "source": "review38 (ORCH-08) and the owner's ruling A-10 (2026-10-04)",
        "change_from_plan_v2": ("CHANGED from plan v2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md), whose gate was C >= B AND C >= R: "
                                "the C >= R leg is removed from eligibility and kept as a mandatory diagnostic (owner ruling A-10)"),
        "status": "BOUND by the owner's ruling A-10 (2026-10-04); a change from plan v2, never an unchanged gate"}}
DECISION_COVERAGE_GATE = "C_GE_B_ONLY"           # the gate in force (owner ruling A-10): eligibility reads B and C only
PLAN_V2_DECISION_COVERAGE_GATE = {
    "id": "C_GE_B_AND_C_GE_R", "text": "plan v2: decision coverage of C >= that of B AND >= that of R",
    "status": "SUPERSEDED by the owner's ruling A-10: R never determines eligibility; refused if a declaration or a caller binds it"}
C_GE_R_DIAGNOSTIC_RULE = ("mandatory diagnostic (owner ruling A-10): C >= R decision coverage, reported with both lanes' counts, the missing "
                          "coverage per document and the reasons; INCOMPLETE when R did not complete its declared population (or did not "
                          "run); it never determines eligibility and earns no credit")


def refuse_r_in_eligibility(definition) -> str:
    """The bound gate id, or ValueError when a definition would bind R into eligibility (owner ruling A-10)."""
    if definition == PLAN_V2_DECISION_COVERAGE_GATE["id"]:
        raise ValueError(f"refused: decision coverage gate {definition!r} binds R into eligibility -- superseded by the owner's ruling A-10 "
                         "(C >= B only; C >= R is a mandatory diagnostic)")
    if definition not in DECISION_COVERAGE_GATE_DEFINITIONS or DECISION_COVERAGE_GATE_DEFINITIONS[definition]["reads_R"]:
        raise ValueError(f"refused: unknown decision coverage gate definition {definition!r} (only {DECISION_COVERAGE_GATE!r} is bound, A-10)")
    return definition


def candidate_outcome(outcome_by_field: dict, state=None) -> dict:
    """RC-2: the one comparison outcome of the candidate (C is one switch set; it cannot be adopted per field)."""
    vals = [outcome_by_field[f] for f in FIELDS]
    if state is not None and state not in ("INVALID", "INCOMPLETE"):
        return {"outcome": state, "basis": f"comparison state {state} (every field carries it)", "fields_not_eligible": list(FIELDS)}
    if all(v == OUTCOMES[0] for v in vals):
        return {"outcome": OUTCOMES[0], "basis": "all three fields ELIGIBLE", "fields_not_eligible": []}
    for o in CANDIDATE_PRECEDENCE:
        hit = [f for f in FIELDS if outcome_by_field[f] == o]
        if hit:
            return {"outcome": o, "basis": f"{o} in {', '.join(hit)} (precedence INVALID > NOT ELIGIBLE > INCOMPLETE)",
                    "fields_not_eligible": [f for f in FIELDS if outcome_by_field[f] != OUTCOMES[0]]}
    other = sorted({v for v in vals if v != OUTCOMES[0]})
    return {"outcome": other[0], "basis": f"field outcome {other[0]}", "fields_not_eligible": [f for f in FIELDS if outcome_by_field[f] != OUTCOMES[0]]}


def population_gate(truth, extensions_used: int, minimum=MINIMUM, extensions=EXTENSIONS) -> dict:
    counts = {f: len(v) for f, v in A.population(truth).items()}
    short = {f: n for f, n in counts.items() if n < minimum}
    if not short:
        action = "DISPATCH_ELIGIBLE"
    elif extensions_used < len(extensions):
        action = f"EXTEND:{extensions[extensions_used]}"
    else:
        action = "PREPARATION BLOCKED"
    return {"rule": f">= {minimum} resolved (per field), independently reviewed documents per field carrying the fact; canonical ids; no partial closure run",
            "counts": counts, "short": short, "extensions_used": extensions_used, "action": action}


def matched(B, C, truth, f, docs=None):
    return K.matched(B, C, truth, f, docs)


def critical_split(judged) -> dict:
    out = {"resolved": [], "unresolved": []}
    for pid, d in judged.items():
        s = J.critical_split(d)
        out["resolved"] += s["resolved"]
        out["unresolved"] += s["unresolved"]
    return out


def lane_metrics(lane, truth, judged=None, docs=None) -> dict:
    """Every run-set document of the lane stays in the denominators (readable / coverage pages), whatever its status."""
    judged = judged if judged is not None else J.judge_lane(lane, truth)
    out = {"fields": {}, "critical": critical_split(judged)}
    for f in FIELDS:
        res = {pid for pid in truth["documents"] if A.primary(truth, pid, f) and (docs is None or pid in docs)}
        rec, acc, neg = collections.Counter(), collections.Counter(), collections.Counter()
        ns, missing = 0, []
        for pid in res:
            d = judged.get(pid)
            if not d:
                missing.append(pid)
                rec["missed"] += sum(1 for r in A.doc_rows(truth, pid, f) if r["truth_kind"] == "value")
                continue
            rec.update(d["fields"][f]["recovery"])
            acc.update(d["fields"][f]["accepted"])
            neg.update(d["fields"][f]["negatives"])
            ns += d["fields"][f]["not_scorable_rows"]
        readable = sum(rec[k] for k in ("recovered_clean", "recovered_mixed", "recovered_conflict", "wrong_only", "held_only", "missed"))
        asserted = acc["correct"] + acc["wrong"]
        out["fields"][f] = {"recovery_counts": dict(rec), "negatives": dict(neg), "readable": readable,
                            "clean_recovery": round(rec["recovered_clean"] / readable, 4) if readable else None,
                            "accepted": dict(acc), "accepted_precision": round(acc["correct"] / asserted, 4) if asserted else None,
                            "not_scorable_rows_excluded": ns, "documents_absent_from_lane_counted_missed": sorted(missing),
                            "critical_resolved": [c for c in out["critical"]["resolved"] if c["field"] == f],
                            "critical_unresolved": [c for c in out["critical"]["unresolved"] if c["field"] == f],
                            "coverage_resolved": coverage_counts(lane, truth, f, res)}
    return out


def coverage_counts(lane, truth, f, docs=None) -> dict:
    """lane_judge_r32.coverage_counts, plus the rows of documents a limit or a failure left INCOMPLETE / DEFERRED, counted
    in the same denominator ('pages') and shown apart -- never removed."""
    c = J.coverage_counts(lane, truth, f, docs)
    lim = collections.Counter()
    for r in truth["rows"].values():
        if r["field"] != f or (docs is not None and r["pool_id"] not in docs) or r["truth_kind"] == "not_scorable":
            continue
        d = (lane.get("documents") or {}).get(r["pool_id"]) or {}
        st = d.get("status", "COMPLETE")
        if st != "COMPLETE":
            lim[f"{st.lower()}_document_rows"] += 1
    return c | {"status_rows": dict(lim)}


def bootstrap(diffs_by_group, seed, n=2000):
    groups = sorted(diffs_by_group)
    allv = [v for g in groups for v in diffs_by_group[g]]
    if not allv:
        return None
    rng = random.Random(seed)
    bs = sorted(sum(s) / len(s) for s in ([rng.choice(diffs_by_group[g]) for g in groups for _ in diffs_by_group[g]] for _ in range(n)))
    return {"estimate": round(sum(allv) / len(allv), 4), "ci95": [round(bs[int(0.025 * n)], 4), round(bs[int(0.975 * n) - 1], 4)],
            "n_documents": len(allv), "seed": seed, "resamples": n, "stratified_by": "project"}


def paired(B, C, truth, f, seed, jB, jC, docs=None) -> dict:
    m = matched(B, C, truth, f, docs)
    dp = collections.defaultdict(list)
    for pid in m:
        dp[truth["documents"][pid]["project"]].append(J.y(jC, pid, f) - J.y(jB, pid, f))
    bt = bootstrap(dp, seed)
    if len(m) < MINIMUM:
        verdict = f"INCONCLUSIVE (matched resolved documents {len(m)} < {MINIMUM})"
    elif bt["ci95"][0] > 0:
        verdict = "SUPPORTED (interval excludes zero, in favour of C)"
    elif bt["ci95"][1] < 0:
        verdict = "CONTRADICTED (interval excludes zero, in favour of B)"
    else:
        verdict = "INCONCLUSIVE (interval includes zero)"
    return {"matched": len(m), "matched_documents": m, "paired_difference": bt, "verdict": verdict}


def requests_total(lane) -> int:
    r = lane.get("requests") or {}
    return int(r.get("own_dispatched", 0)) + int(r.get("inherited_from_b", 0))


def _key(c):
    return (c["pool_id"], c.get("page"), c.get("field"))


def request_gate(B, C, truth, caps, seed, jB, jC, docs=None) -> dict:
    rule = ">= 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero"
    if caps.get("B") != caps.get("C"):
        return {"rule": rule, "applicable": False, "passes": False,
                "reason": f"caps unequal (B {caps.get('B')}, C {caps.get('C')}): the gate is defined only at equal maximum allowances (R31-03)"}
    docs_m = sorted({pid for f in FIELDS for pid in matched(B, C, truth, f, docs)})
    dp = collections.defaultdict(list)
    gain = 0
    for pid in docs_m:
        g = sum(J.y(jC, pid, f) - J.y(jB, pid, f) for f in FIELDS if pid in matched(B, C, truth, f, docs))
        gain += g
        dp[truth["documents"][pid]["project"]].append(g)
    bt = bootstrap(dp, seed)
    extra = requests_total(C) - requests_total(B)
    sb, sc = critical_split(jB), critical_split(jC)
    cb = {_key(c) for c in sb["resolved"] + sb["unresolved"]}
    new_false = [c for c in sc["resolved"] + sc["unresolved"] if _key(c) not in cb]
    ratio_ok = extra <= 0 or gain * THRESHOLDS["facts_per_extra_requests"] >= extra
    interval_ok = bool(bt) and bt["ci95"][0] > 0
    return {"rule": rule, "applicable": True, "caps": caps, "net_correct_facts": gain, "requests": {"B": requests_total(B), "C": requests_total(C)},
            "extra_requests": extra, "facts_per_8_extra": None if extra <= 0 else round(8 * gain / extra, 3), "net_gain_per_document": bt,
            "new_false_accepts": new_false, "passes": ratio_ok and interval_ok and not new_false,
            "policy_cost_note": "the request difference is part of the policy; nothing is reported as equal-budget accuracy"}


def decision_coverage_gate(B, C, truth, docs=None, *, definition: str = DECISION_COVERAGE_GATE) -> dict:
    """The GATE (owner ruling A-10): C >= B only -- a change from plan v2 (C >= B and C >= R). A definition binding R into
    eligibility is refused (refuse_r_in_eligibility). C >= R is the mandatory diagnostic c_ge_r_diagnostic()."""
    d = DECISION_COVERAGE_GATE_DEFINITIONS[refuse_r_in_eligibility(definition)]
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cb, cc = coverage_counts(B, truth, "decision", res), coverage_counts(C, truth, "decision", res)
    return {"definition": definition, "text": d["text"], "status": d["status"], "change_from_plan_v2": d["change_from_plan_v2"],
            "rule": "completed read or verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE rows are never coverage; "
                    "C >= B (C >= R is the mandatory diagnostic, never an eligibility input)",
            "reads_lanes": ["B", "C"], "B": cb, "C": cc, "state": "COMPLETE", "passes": cc["coverage"] >= cb["coverage"]}


_CLASS_REASON = {"completed_read": "covered: completed read", "located_incomplete": "not covered: the decision area was located but not read to completion",
                 "not_attempted": "not covered: no read was attempted", "budget": "not covered: not read under the application's own budget",
                 "missing_page": "not covered: the page was not read (the attempt failed or the page is missing)",
                 "not_scorable": "not scorable"}


def _cov_class(lane, pid, page, kind):
    cls = ((((lane or {}).get("documents") or {}).get(pid) or {}).get("coverage") or {}).get(str(page), {}).get("decision", "not_attempted")
    if cls == "discovery_absent":
        return cls, kind == "absent", ("covered: verified absence" if kind == "absent" else "not covered: wrong absence (the truth has a decision)")
    return cls, cls == "completed_read", _CLASS_REASON.get(cls, f"not covered: {cls}")


def c_ge_r_diagnostic(C, R, truth, docs=None, r_gate=None) -> dict:
    """The MANDATORY C >= R decision-coverage diagnostic (owner ruling A-10): both lanes' counts, the missing coverage per
    document with its reasons, the documents R did not complete; INCOMPLETE when R did not complete its declared population
    (or did not run). It never determines eligibility and earns no credit."""
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cc = coverage_counts(C, truth, "decision", res)
    cr = coverage_counts(R, truth, "decision", res) if R is not None else None
    if R is None:
        state, why = "INCOMPLETE", [r_gate or "lane R did not run in this invocation"]
    else:
        rs = limit_state(R, docs)
        missing_docs = sorted(pid for pid in (docs or []) if pid not in (R.get("documents") or {}))
        why = [f"{pid}: R {v.get('status', 'DEFERRED') if k != 'deferred' else 'DEFERRED'} ({v.get('reason')})"
               for k in ("deferred", "limit_incomplete", "other_incomplete") for pid, v in sorted(rs[k].items())] + \
              [f"{pid}: not in lane R" for pid in missing_docs]
        state = "INCOMPLETE" if why else "COMPLETE"
    per_doc = {}
    for r in sorted(truth["rows"].values(), key=lambda x: (x["pool_id"], str(x["page"]))):
        if r["field"] != "decision" or r["pool_id"] not in res or r["truth_kind"] == "not_scorable":
            continue
        c_cls, c_ok, c_why = _cov_class(C, r["pool_id"], r["page"], r["truth_kind"])
        if R is not None:
            r_cls, r_ok, r_why = _cov_class(R, r["pool_id"], r["page"], r["truth_kind"])
        else:
            r_cls, r_ok, r_why = None, False, "R did not run"
        if c_ok and r_ok:
            continue
        d = per_doc.setdefault(r["pool_id"], {"pages": {}, "C_status": ((C.get("documents") or {}).get(r["pool_id"]) or {}).get("status", "COMPLETE"),
                                              "R_status": None if R is None else ((R.get("documents") or {}).get(r["pool_id"]) or {}).get("status", "absent")})
        d["pages"][str(r["page"])] = {"C": c_cls, "C_covered": c_ok, "C_reason": c_why, "R": r_cls, "R_covered": r_ok, "R_reason": r_why,
                                      "C_missing_where_R_covered": (not c_ok) and r_ok}
    holds = (cc["coverage"] >= cr["coverage"]) if (state == "COMPLETE" and cr is not None) else None
    return {"mandatory": True, "determines_eligibility": False, "credit": "none", "rule": C_GE_R_DIAGNOSTIC_RULE,
            "change_from_plan_v2": DECISION_COVERAGE_GATE_DEFINITIONS[DECISION_COVERAGE_GATE]["change_from_plan_v2"],
            "state": state, "why_incomplete": why if state != "COMPLETE" else [], "counts": {"C": cc, "R": cr},
            "coverage": {"C": cc["coverage"], "R": None if cr is None else cr["coverage"]}, "holds": holds,
            "missing_coverage": per_doc,
            "C_missing_where_R_covered": sorted(pid for pid, d in per_doc.items() if any(p["C_missing_where_R_covered"] for p in d["pages"].values()))}


def unread_pages(lane: dict, docs=None) -> dict:
    """ORCH-08C (R39-06): the documents of a lane with pages the application did not read under its own per-document
    limits (reader cap, JobBudget, reader exception), with the pages; they stay COMPLETE and in every denominator."""
    out = {}
    for pid, d in sorted((lane or {}).get("documents", {}).items()):
        if docs is not None and pid not in docs:
            continue
        u = d.get("unread_pages") or {}
        if u:
            out[pid] = {"status": d.get("status"), "unread_page_count": d.get("unread_page_count"), "pages": u,
                        "partially_read_pages": d.get("partially_read_pages") or []}
    return {"documents": out, "documents_with_unread_pages": len(out), "unread_pages": sum(int(v["unread_page_count"] or 0) for v in out.values()),
            "rule": "COMPLETE with every page not read under the application's own per-document limits listed; counted as unread in every denominator"}


def _sum(counters):
    t = collections.Counter()
    for c in counters:
        t.update(c or {})
    return dict(t)


def primary_outcomes(B, C, truth, judged) -> dict:
    lanes = {"B": B, "C": C}
    return {"association": {k: _sum(d.get("association") for d in (L.get("documents") or {}).values()) for k, L in lanes.items()},
            "critical": {k: {s: len(v) for s, v in critical_split(judged[k]).items()} for k in lanes},
            "critical_by_field": {k: {f: {s: sum(1 for c in v if c["field"] == f) for s, v in critical_split(judged[k]).items()} for f in FIELDS} for k in lanes},
            "decision": {k: J.coverage_counts(L, truth, "decision") | {"accepted": _sum(d["fields"]["decision"]["accepted"] for d in judged[k].values())}
                         for k, L in lanes.items()},
            "requests": {k: L.get("requests") for k, L in lanes.items()}, "tokens": {k: L.get("tokens") for k, L in lanes.items()}}


def limit_state(lane: dict, docs) -> dict:
    """The documents of a lane that a limit refused (class 'limit') or deferred, and the others that are INCOMPLETE."""
    out = {"deferred": {}, "limit_incomplete": {}, "other_incomplete": {}}
    for pid, d in (lane.get("documents") or {}).items():
        if docs is not None and pid not in docs:
            continue
        st, classes = d.get("status", "COMPLETE"), d.get("status_classes") or []
        if st == "DEFERRED":
            out["deferred"][pid] = {"retry_at_utc": d.get("retry_at_utc"), "reason": d.get("status_reason")}
        elif st == "INCOMPLETE" and "limit" in classes:
            out["limit_incomplete"][pid] = {"reason": d.get("status_reason"), "kinds": d.get("limit_kinds"), "pages": d.get("limit_pages")}
        elif st == "INCOMPLETE":
            out["other_incomplete"][pid] = {"reason": d.get("status_reason"), "classes": classes, "kinds": d.get("limit_kinds"), "pages": d.get("limit_pages")}
    return out


def _check_lane(lane, name):
    if lane is not None and lane.get("lane") not in (None, name):
        raise ValueError(f"the {name} argument is lane {lane.get('lane')!r}: R or P can never stand in for B or C")


def diagnostics_R(R, C, truth, docs, r_gate=None) -> dict:
    """R: a reference diagnostic without credit. Its declared population is the run set; truncated -> INCOMPLETE."""
    if R is None:
        return {"credit": "none (A-09 point 6)", "state": "INCOMPLETE", "population": sorted(docs or []),
                "why": r_gate or "lane R did not run in this invocation", "C_ge_R_decision_coverage": {"state": "INCOMPLETE", "holds": None}}
    _check_lane(R, "R")
    rs = limit_state(R, docs)
    not_complete = sorted(set(rs["deferred"]) | set(rs["limit_incomplete"]) | set(rs["other_incomplete"]) |
                          {pid for pid in (docs or []) if pid not in (R.get("documents") or {})})
    state = "COMPLETE" if not not_complete else "INCOMPLETE"
    jR = J.judge_lane(R, truth)
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cc, cr = coverage_counts(C, truth, "decision", res), coverage_counts(R, truth, "decision", res)
    rev = [pid for pid in truth["documents"] if A.has_fact(truth, pid, "revision") and (docs is None or pid in docs)]
    jC = J.judge_lane(C, truth)
    return {"credit": "none: R earns no accuracy or recovery credit and decides nothing (A-09 point 6)", "state": state,
            "population": sorted(docs or []), "not_complete": not_complete, "status": rs,
            "metrics_diagnostic_only": lane_metrics(R, truth, jR, docs),
            "decision_controls_diagnostic_only": K.decision_controls({"R": R}, truth, docs=docs).get("R"),
            "C_ge_R_decision_coverage": {"state": state, "C": cc["coverage"], "R": cr["coverage"],
                                         "holds": (cc["coverage"] >= cr["coverage"]) if state == "COMPLETE" else None,
                                         "note": "diagnostic contrast; INCOMPLETE when R did not complete its population (a truncated R would "
                                                 "otherwise make it easier to hold)" if state != "COMPLETE" else "diagnostic contrast"},
            "revision_under_PA_C_vs_R": {"state": state,
                                         "lost": sorted(d for d in rev if J.y(jR, d, "revision") and not J.y(jC, d, "revision")),
                                         "gained": sorted(d for d in rev if J.y(jC, d, "revision") and not J.y(jR, d, "revision")),
                                         "note": "identical captured responses wherever both asked the same request (content key)"}}


def diagnostics_P(P) -> dict:
    if P is None:
        return {"credit": "none (A-09 point 6)", "state": "INCOMPLETE", "why": "lane P did not run in this invocation"}
    return {"credit": "none: the variation probe is report-only (A-09 point 6)", "state": P.get("population_state", "INCOMPLETE"),
            "sampled": P.get("sampled"), "of": P.get("of"),
            "items_not_complete": [i for i in P.get("rows") or [] if i.get("status") != "COMPLETE"]}


def evaluate(B, C, R, truth, *, caps, extensions_used, seed=BOOTSTRAP_SEED, stop_state=None, docs=None, P=None, r_gate=None,
             gate_definition: str = DECISION_COVERAGE_GATE) -> dict:
    _check_lane(B, "B")
    _check_lane(C, "C")
    refuse_r_in_eligibility(gate_definition)                 # owner ruling A-10: R never determines eligibility
    gate = population_gate(truth, extensions_used)
    result = {"scorer": "score_bcr_r32", "thresholds": THRESHOLDS, "population_gate": gate,
              "reference_set_statement": REFERENCE_SET_STATEMENT, "default_selected": None,
              "scope_limitations": [dict(x) for x in SCOPE_LIMITATIONS], "not_claimed": list(NOT_CLAIMED)}
    comp = (stop_state or {}).get("comparison", "PENDING")
    lim = {"B": limit_state(B, docs), "C": limit_state(C, docs)}
    excluded = {}
    for name, ls in lim.items():
        for pid, v in ls["deferred"].items():
            excluded.setdefault(pid, []).append(f"{name} DEFERRED ({v['reason']})")
        for pid, v in ls["limit_incomplete"].items():
            excluded.setdefault(pid, []).append(f"{name} INCOMPLETE by a limit ({v['reason']})")
    docs_all = set(docs) if docs is not None else {pid for pid in truth["documents"]}
    docs_m = docs_all - set(excluded)
    result["limit_incomplete"] = lim
    result["matched_exclusions"] = {pid: sorted(v) for pid, v in sorted(excluded.items())}
    judged = {"B": J.judge_lane(B, truth), "C": J.judge_lane(C, truth)}
    jB, jC = judged["B"], judged["C"]
    result["metrics"] = {k: lane_metrics(L, truth, judged[k], docs) for k, L in (("B", B), ("C", C))}
    result["paired"] = {f: paired(B, C, truth, f, f"{seed}:{f}", jB, jC, docs_m) for f in FIELDS}
    result["matched_before_exclusions"] = {f: len(matched(B, C, truth, f, docs)) for f in FIELDS}
    result["request_gate"] = request_gate(B, C, truth, caps, f"{seed}:requests", jB, jC, docs_m)
    result["decision_coverage_gate"] = decision_coverage_gate(B, C, truth, docs, definition=gate_definition)
    result["decision_coverage_C_ge_R"] = c_ge_r_diagnostic(C, R, truth, docs, r_gate)       # MANDATORY diagnostic (A-10)
    result["concentration"] = K.evaluate(B, C, truth, R=None, docs=docs_m)
    result["primary_outcomes"] = primary_outcomes(B, C, truth, judged)
    result["diagnostics"] = {"R": diagnostics_R(R, C, truth, docs, r_gate), "P": diagnostics_P(P)}
    result["unread_pages"] = {name: unread_pages(L, docs) for name, L in (("B", B), ("C", C), ("R", R)) if L is not None}
    c_crit = result["metrics"]["C"]["critical"]["resolved"]
    # comparison-level states and gates: apply to every field
    common = []
    deferred_n = len(lim["B"]["deferred"]) + len(lim["C"]["deferred"])
    limited_n = len(lim["B"]["limit_incomplete"]) + len(lim["C"]["limit_incomplete"])
    if gate["action"] != "DISPATCH_ELIGIBLE":
        state = "PREPARATION BLOCKED" if gate["action"] == "PREPARATION BLOCKED" else f"NOT DISPATCHABLE ({gate['action']})"
        result["exercise_only"] = "the population gate refuses dispatch; any figure below exercises the scorer and is not a result"
    elif comp.startswith("INVALID"):
        state = "INVALID"
    elif comp.startswith("INCOMPLETE") or ((deferred_n or limited_n) and not comp.startswith("RESULT")):
        state = "INCOMPLETE"
    else:
        state = None
    if comp.startswith("RESULT"):
        common.append("candidate failed the safety gate (C stopped by a critical acceptance on resolved truth)")
    for c in c_crit:
        common.append(f"critical acceptance on resolved truth in C: {c['field']} {c['pool_id']} p{c['page']} (candidate-level safety gate)")
    if not result["request_gate"]["passes"]:
        common.append("request-normalised gate not met" + ("" if result["request_gate"]["applicable"] else " (not applicable: unequal caps)"))
    fields = {}
    for f in FIELDS:
        m = result["metrics"]["C"]["fields"][f]
        reasons = list(common)
        if m["accepted_precision"] is not None and m["accepted_precision"] < THRESHOLDS["accepted_precision_min"]:
            reasons.append(f"{f}: accepted precision {m['accepted_precision']} < 0.98")
        if m["clean_recovery"] is None or m["clean_recovery"] < THRESHOLDS["clean_recovery_min"]:
            reasons.append(f"{f}: clean recovery {m['clean_recovery']} < 0.90")
        if result["paired"][f]["matched"] < MINIMUM:
            reasons.append(f"{f}: matched {result['paired'][f]['matched']} < {MINIMUM}")
        conc = result["concentration"]["fields"][f]
        if conc["outcome"] == "NOT ELIGIBLE":
            reasons += [f"concentration: {r}" for r in conc["reasons"]]
        if f == "decision" and not result["decision_coverage_gate"]["passes"]:
            reasons.append("decision coverage of C below B")
        outcome = state or ("NOT ELIGIBLE" if reasons else OUTCOMES[0])
        fields[f] = {"outcome": outcome, "reasons_not_eligible": reasons, "critical_resolved_in_C": [c for c in c_crit if c["field"] == f],
                     "concentration_outcome": conc["outcome"], "matched": result["paired"][f]["matched"], "default_selected": None,
                     "role": "diagnostic (the comparison outcome is the candidate-level `outcome`)"}
    result["fields"] = fields
    detail = comp
    if state == "INCOMPLETE" and (deferred_n or limited_n) and not comp.startswith("INCOMPLETE"):
        detail = (f"INCOMPLETE: {deferred_n} B/C document(s) DEFERRED by the project window"
                  f"{' (resumable after the earliest retry time)' if deferred_n else ''} and {limited_n} INCOMPLETE by a limit; "
                  "every one stays in the coverage denominators")
    result["comparison_state"] = state or comp
    result["comparison_detail"] = detail
    result["outcome_by_field"] = {f: v["outcome"] for f, v in fields.items()}
    cand = candidate_outcome(result["outcome_by_field"], state)
    result["outcome"] = cand["outcome"]
    result["candidate"] = cand | {"rule": CANDIDATE_RULE, "decision_coverage_gate": gate_definition, "reads_lanes": ["B", "C"],
                                  "reasons_not_eligible": {f: fields[f]["reasons_not_eligible"] for f in FIELDS if fields[f]["reasons_not_eligible"]}}
    result["default_selected"] = None
    return result


def report_template(result: dict) -> str:
    """The text every run report carries (A-09 point 5): the scope limitation and what is not claimed -- never removed."""
    lines = ["## Scope limitations (declared; never removed)"]
    for s in result.get("scope_limitations") or SCOPE_LIMITATIONS:
        lines.append(f"- {s['id']}: required {s['required']}, found {s['found']}. {s['statement']}")
    lines.append("## Not claimed by this run")
    for x in result.get("not_claimed") or NOT_CLAIMED:
        lines.append(f"- {x}")
    g = DECISION_COVERAGE_GATE_DEFINITIONS[DECISION_COVERAGE_GATE]
    lines.append("## Decision coverage gate (CHANGED from plan v2; owner ruling A-10)")
    lines.append(f"- Eligibility: {g['id']} -- C >= B only. {g['change_from_plan_v2']}. This is not an unchanged gate. Every other "
                 "safety, accuracy and completeness gate is unchanged.")
    lines.append("## C >= R decision coverage (MANDATORY diagnostic; never an eligibility input; no credit)")
    dg = result.get("decision_coverage_C_ge_R")
    if not dg:
        lines.append("- Every report states: the state (COMPLETE, or INCOMPLETE when R did not complete its declared population, with "
                     "why), the counts of C and R (coverage, completed reads, verified and wrong absences, other classes, scorable pages), "
                     "whether C >= R holds (only when COMPLETE), and for every document with missing coverage in C or R: the page, each "
                     "lane's coverage class, whether it is covered, and the reason.")
    else:
        lines.append(f"- State: {dg['state']}" + (f" ({'; '.join(dg['why_incomplete'])})" if dg["why_incomplete"] else "") +
                     f". Coverage C {dg['coverage']['C']}, R {dg['coverage']['R']}; holds: {dg['holds']}.")
        lines.append(f"- Counts C: {dg['counts']['C']}; counts R: {dg['counts']['R']}.")
        for pid, d in sorted(dg["missing_coverage"].items()):
            for page, p in sorted(d["pages"].items()):
                lines.append(f"- {pid} p{page}: C {p['C']} ({p['C_reason']}); R {p['R']} ({p['R_reason']}); C status {d['C_status']}, "
                             f"R status {d['R_status']}.")
    lines.append("## Pages not read under the application's own per-document limits")
    lines.append("- A document whose pages the application did not read under its own per-document limits (the reader's call cap, "
                 "the per-document JobBudget, a reader exception) stays COMPLETE; every such page is listed (result['unread_pages'] "
                 "per lane) and counted as unread in every denominator. Harness and resource refusals make a document INCOMPLETE.")
    lines.append(f"## Reference set\n- {REFERENCE_SET_STATEMENT}")
    return "\n".join(lines) + "\n"
