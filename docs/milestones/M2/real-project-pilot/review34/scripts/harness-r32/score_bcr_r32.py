"""ORCH-05.1 (Review 33 C-5, R33-01/R33-05) and ORCH-05C (Review 34 RC-2 / R34-02): the Review 31 B / C / R scorer rules,
applied PER FIELD over the r32 truth, with ONE candidate-level outcome.

The Review 31 file harness-base/score_bcr.py (5a3828a5...) is unchanged; SCORER-CHANGES.md lists every difference.
Inputs: normalised r32 lanes (lane_judge_r32 format) and the r32 truth (labels_adapter_r32.build_truth).
Rules kept from Review 31 (same constants, same seeds):
  * population gate: each of identity, revision, decision >= 12 resolved, independently reviewed documents carrying the
    fact (canonical ids; count-once aliases never counted), else the next extension, else PREPARATION BLOCKED;
  * the document is the unit; y(doc, f) = 1 iff a clean recovery (a correct asserted value and no wrong one) on a
    SCORABLE row of f; resolved labels are primary -- now resolved PER FIELD (resolved_for_scoring of that field);
  * paired difference: document-cluster bootstrap stratified by project, 2,000 resamples, seed m2-r30-bootstrap-2026-10-02;
  * request gate at EQUAL caps only (240/240): net correct facts x 8 >= extra requests, no new false acceptance,
    bootstrap interval of the net gain per document excluding zero; unequal caps -> not applicable;
  * thresholds: zero critical acceptance on resolved truth in C; accepted precision >= 0.98 and clean recovery >= 0.90
    per field; matched >= 12 per field;
  * decision coverage: completed read or verified absence; wrong absence and located_incomplete never count; C >= B and
    C >= R; NOT_SCORABLE rows never count either way;
  * outcomes ELIGIBLE FOR A SEPARATE SELECTION DECISION / NOT ELIGIBLE / INCOMPLETE / INVALID / PREPARATION BLOCKED; no
    default is ever selected (default_selected is always None).
Changed for r32 (each in SCORER-CHANGES.md): per-field resolution and NOT_SCORABLE exclusion; per-field critical
tripwire attribution (pool id, page, field); per-field outcomes as DIAGNOSTICS, with comparison-level states and gates
applied to every field and field-level gates only to their field; the concentration rule of concentration_r32 version 2
(A-05, RC-1) in place of the project-or-stratum leg.
Candidate-level outcome (RC-2; result["outcome"], the ONLY comparison outcome): C is one switch set and is judged as a
whole. A comparison state that is not INVALID / INCOMPLETE (PREPARATION BLOCKED, NOT DISPATCHABLE) is the outcome;
otherwise the outcome is ELIGIBLE FOR A SEPARATE SELECTION DECISION only when ALL THREE fields are ELIGIBLE, else the
first of INVALID > NOT ELIGIBLE > INCOMPLETE found among the field outcomes. No default is ever selected.
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
                  "per-field outcomes are diagnostics; no default is ever selected")
REFERENCE_SET_STATEMENT = K.REFERENCE_SET_STATEMENT


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
    judged = judged if judged is not None else J.judge_lane(lane, truth)
    out = {"fields": {}, "critical": critical_split(judged)}
    for f in FIELDS:
        res = {pid for pid in truth["documents"] if A.primary(truth, pid, f) and (docs is None or pid in docs)}
        rec, acc, neg = collections.Counter(), collections.Counter(), collections.Counter()
        ns = 0
        for pid in res:
            d = judged.get(pid)
            if not d:
                continue
            rec.update(d["fields"][f]["recovery"])
            acc.update(d["fields"][f]["accepted"])
            neg.update(d["fields"][f]["negatives"])
            ns += d["fields"][f]["not_scorable_rows"]
        readable = sum(rec[k] for k in ("recovered_clean", "recovered_mixed", "wrong_only", "held_only", "missed"))
        asserted = acc["correct"] + acc["wrong"]
        out["fields"][f] = {"recovery_counts": dict(rec), "negatives": dict(neg), "readable": readable,
                            "clean_recovery": round(rec["recovered_clean"] / readable, 4) if readable else None,
                            "accepted": dict(acc), "accepted_precision": round(acc["correct"] / asserted, 4) if asserted else None,
                            "not_scorable_rows_excluded": ns,
                            "critical_resolved": [c for c in out["critical"]["resolved"] if c["field"] == f],
                            "critical_unresolved": [c for c in out["critical"]["unresolved"] if c["field"] == f],
                            "coverage_resolved": J.coverage_counts(lane, truth, f, res)}
    return out


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


def decision_coverage_gate(B, C, truth, R=None, docs=None) -> dict:
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cb, cc = J.coverage_counts(B, truth, "decision", res), J.coverage_counts(C, truth, "decision", res)
    out = {"rule": "completed read or verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE rows are never coverage; C >= B and C >= R",
           "B": cb, "C": cc, "passes": cc["coverage"] >= cb["coverage"]}
    if R is not None:
        cr = J.coverage_counts(R, truth, "decision", res)
        out["R"] = cr
        out["passes"] = out["passes"] and cc["coverage"] >= cr["coverage"]
    return out


def _sum(counters):
    t = collections.Counter()
    for c in counters:
        t.update(c or {})
    return dict(t)


def primary_outcomes(B, C, R, truth, judged) -> dict:
    lanes = {"B": B, "C": C} | ({"R": R} if R else {})
    out = {"association": {k: _sum(d.get("association") for d in (L.get("documents") or {}).values()) for k, L in lanes.items()},
           "critical": {k: {s: len(v) for s, v in critical_split(judged[k]).items()} for k in lanes},
           "critical_by_field": {k: {f: {s: sum(1 for c in v if c["field"] == f) for s, v in critical_split(judged[k]).items()} for f in FIELDS} for k in lanes},
           "decision": {k: J.coverage_counts(L, truth, "decision") | {"accepted": _sum(d["fields"]["decision"]["accepted"] for d in judged[k].values())}
                        for k, L in lanes.items()},
           "requests": {k: L.get("requests") for k, L in lanes.items()}, "tokens": {k: L.get("tokens") for k, L in lanes.items()}}
    if R:
        rev = [pid for pid in truth["documents"] if A.has_fact(truth, pid, "revision")]
        out["revision_under_PA_C_vs_R"] = {"lost": sorted(d for d in rev if J.y(judged["R"], d, "revision") and not J.y(judged["C"], d, "revision")),
                                           "gained": sorted(d for d in rev if J.y(judged["C"], d, "revision") and not J.y(judged["R"], d, "revision")),
                                           "note": "identical captured responses wherever both asked the same request (content key)"}
    return out


def evaluate(B, C, R, truth, *, caps, extensions_used, seed=BOOTSTRAP_SEED, stop_state=None, docs=None) -> dict:
    gate = population_gate(truth, extensions_used)
    result = {"scorer": "score_bcr_r32", "thresholds": THRESHOLDS, "population_gate": gate,
              "reference_set_statement": REFERENCE_SET_STATEMENT, "default_selected": None}
    comp = (stop_state or {}).get("comparison", "PENDING")
    judged = {"B": J.judge_lane(B, truth), "C": J.judge_lane(C, truth)} | ({"R": J.judge_lane(R, truth)} if R else {})
    jB, jC = judged["B"], judged["C"]
    result["metrics"] = {k: lane_metrics(L, truth, judged[k], docs) for k, L in (("B", B), ("C", C), ("R", R)) if L}
    result["paired"] = {f: paired(B, C, truth, f, f"{seed}:{f}", jB, jC, docs) for f in FIELDS}
    result["request_gate"] = request_gate(B, C, truth, caps, f"{seed}:requests", jB, jC, docs)
    result["decision_coverage_gate"] = decision_coverage_gate(B, C, truth, R, docs)
    result["concentration"] = K.evaluate(B, C, truth, R=R, docs=docs)
    result["primary_outcomes"] = primary_outcomes(B, C, R, truth, judged)
    c_crit = result["metrics"]["C"]["critical"]["resolved"]
    # comparison-level states and gates: apply to every field
    common = []
    if gate["action"] != "DISPATCH_ELIGIBLE":
        state = "PREPARATION BLOCKED" if gate["action"] == "PREPARATION BLOCKED" else f"NOT DISPATCHABLE ({gate['action']})"
        result["exercise_only"] = "the population gate refuses dispatch; any figure below exercises the scorer and is not a result"
    elif comp.startswith("INVALID"):
        state = "INVALID"
    elif comp.startswith("INCOMPLETE"):
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
            reasons.append("decision coverage of C below B or R")
        outcome = state or ("NOT ELIGIBLE" if reasons else OUTCOMES[0])
        fields[f] = {"outcome": outcome, "reasons_not_eligible": reasons, "critical_resolved_in_C": [c for c in c_crit if c["field"] == f],
                     "concentration_outcome": conc["outcome"], "matched": result["paired"][f]["matched"], "default_selected": None,
                     "role": "diagnostic (the comparison outcome is the candidate-level `outcome`)"}
    result["fields"] = fields
    result["comparison_state"] = state or comp
    result["outcome_by_field"] = {f: v["outcome"] for f, v in fields.items()}
    cand = candidate_outcome(result["outcome_by_field"], state)
    result["outcome"] = cand["outcome"]
    result["candidate"] = cand | {"rule": CANDIDATE_RULE,
                                  "reasons_not_eligible": {f: fields[f]["reasons_not_eligible"] for f in FIELDS if fields[f]["reasons_not_eligible"]}}
    result["default_selected"] = None
    return result
