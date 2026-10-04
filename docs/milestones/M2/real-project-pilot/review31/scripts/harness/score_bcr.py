"""Review 31 (R30-04 / R31-02 / R31-03 / R31-04): the B / C / R scorer and gates, as pure functions over normalised lanes.

Normalised labels  {"documents": {doc: {"project", "stratum", "resolved": bool, "independent_review": bool,
                                         "in_scope_pages": n, "facts": {"<page>": {field: value | None}}}}}
Normalised lane    {"lane": "B"|"C"|"R", "requests": {"own_dispatched", "inherited_from_b", "served_same_fingerprint",
                    "served_reference", "refused_before_dispatch"}, "tokens": {...},
                    "documents": {doc: {"attempted": bool, "unsupported": bool,
                                        "recovery": {field: {"recovered_clean": n, "recovered_mixed": n, "wrong_only": n,
                                                             "held_only": n, "missed": n, "tn": n, "fp": n, ...}},
                                        "accepted": {field: {"correct": n, "wrong": n}},   # distinct AUTOMATIC acceptances
                                        "critical": [{"page", "field", "outcome"}], "association": {counter},
                                        "coverage": {"<page>": {field: class}}}}}
Every rule below is fixed before any prediction exists; nothing here reads a model, a provider or a ledger.
  * population gate (R31-02): an M2-closure run dispatches only when identity, revision AND decision each have >= 12
    resolved, independently reviewed documents carrying the fact; otherwise the next predeclared extension, or
    PREPARATION BLOCKED when none is left. There is no partial closure run.
  * document outcome y(doc, field) = 1 iff the evaluator records a clean recovery (a correct automatic value and no
    wrong one) for a labelled component of the document; the unit is the document; resolved labels are primary.
  * request-normalised gate (R31-03): defined ONLY at equal maximum allowances for B and C; >= 1 net correctly associated
    fact per 8 extra requests, no new false acceptance, bootstrap interval of the net gain excluding zero. The request
    count of C is its whole application-visible total (inherited from B + its own); the difference is the policy cost.
  * decision coverage: completed read, or verified absence where the frozen truth has no decision; a wrong absence is
    never coverage; the coverage of C must be >= that of B and >= that of the reference R.
  * concentration: no eligibility when more than half of the net gain of C in a field comes from one project or stratum.
  * thresholds verbatim (AI-ACCURACY-POLICY section 1, M2-ACCEPTANCE-REPORT): zero critical acceptance on resolved
    truth; >= 98 % precision of accepted critical facts; >= 90 % correct automatic (clean) recovery of readable facts.
  * the outcome is never a default: ELIGIBLE FOR A SEPARATE SELECTION DECISION, NOT ELIGIBLE, INCOMPLETE, INVALID or
    PREPARATION BLOCKED."""
from __future__ import annotations

import collections
import random

FIELDS = ("identity", "revision", "decision")
MINIMUM = 12
EXTENSIONS = ("extension-1", "extension-2")
THRESHOLDS = {"accepted_precision_min": 0.98, "clean_recovery_min": 0.90, "critical_on_resolved_max": 0, "facts_per_extra_requests": 8}


def has_fact(ldoc, f) -> bool:
    return any(p.get(f) not in (None, "") for p in (ldoc.get("facts") or {}).values())


def primary(labels, doc) -> bool:
    d = labels["documents"].get(doc) or {}
    return bool(d.get("resolved")) and bool(d.get("independent_review"))


def population_gate(labels, extensions_used: int, minimum=MINIMUM, extensions=EXTENSIONS) -> dict:
    counts = {f: sum(1 for doc, d in labels["documents"].items() if primary(labels, doc) and has_fact(d, f)) for f in FIELDS}
    short = {f: n for f, n in counts.items() if n < minimum}
    if not short:
        action = "DISPATCH_ELIGIBLE"
    elif extensions_used < len(extensions):
        action = f"EXTEND:{extensions[extensions_used]}"
    else:
        action = "PREPARATION BLOCKED"
    return {"rule": f">= {minimum} resolved, independently reviewed documents per field (identity, revision, decision); no partial closure run",
            "counts": counts, "short": short, "extensions_used": extensions_used, "action": action}


def y(lane, doc, f) -> int:
    r = ((lane["documents"].get(doc) or {}).get("recovery") or {}).get(f) or {}
    return int(r.get("recovered_clean", 0) > 0 and not r.get("recovered_mixed") and not r.get("wrong_only"))


def attempted(lane, doc) -> bool:
    d = lane["documents"].get(doc) or {}
    return bool(d.get("attempted")) and not d.get("unsupported")


def critical_split(lane, labels):
    out = {"resolved": [], "unresolved": []}
    for doc, d in lane["documents"].items():
        for c in d.get("critical") or []:
            out["resolved" if primary(labels, doc) else "unresolved"].append({"doc": doc, **c})
    return out


def coverage_counts(lane, labels, f, docs=None):
    c = collections.Counter()
    for doc, ld in labels["documents"].items():
        if docs is not None and doc not in docs:
            continue
        cov = (lane["documents"].get(doc) or {}).get("coverage") or {}
        for page, facts in (ld.get("facts") or {}).items():
            cls = (cov.get(str(page)) or {}).get(f, "not_attempted")
            fact = facts.get(f) not in (None, "")
            c["pages"] += 1
            if cls == "completed_read":
                c["completed_read"] += 1
            elif cls == "discovery_absent":
                c["wrong_absence" if fact else "verified_absence"] += 1
            else:
                c["other:" + cls] += 1
    c["coverage"] = c["completed_read"] + c["verified_absence"]
    return dict(c)


def lane_metrics(lane, labels) -> dict:
    res = {d for d in labels["documents"] if primary(labels, d)}
    out = {"fields": {}, "critical": critical_split(lane, labels)}
    for f in FIELDS:
        rec, acc = collections.Counter(), collections.Counter()
        for doc in res:
            d = lane["documents"].get(doc) or {}
            rec.update((d.get("recovery") or {}).get(f) or {})
            acc.update((d.get("accepted") or {}).get(f) or {})
        readable = sum(rec[k] for k in ("recovered_clean", "recovered_mixed", "wrong_only", "held_only", "missed"))
        asserted = acc["correct"] + acc["wrong"]
        out["fields"][f] = {"recovery_counts": dict(rec), "readable": readable,
                            "clean_recovery": round(rec["recovered_clean"] / readable, 4) if readable else None,
                            "accepted": dict(acc), "accepted_precision": round(acc["correct"] / asserted, 4) if asserted else None,
                            "coverage_resolved": coverage_counts(lane, labels, f, res)}
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


def matched(B, C, labels, f):
    return [doc for doc, d in labels["documents"].items() if primary(labels, doc) and has_fact(d, f) and attempted(B, doc) and attempted(C, doc)]


def paired(B, C, labels, f, seed) -> dict:
    docs = matched(B, C, labels, f)
    dp = collections.defaultdict(list)
    for doc in docs:
        dp[labels["documents"][doc]["project"]].append(y(C, doc, f) - y(B, doc, f))
    bt = bootstrap(dp, seed)
    if len(docs) < MINIMUM:
        verdict = f"INCONCLUSIVE (matched resolved documents {len(docs)} < {MINIMUM})"
    elif bt["ci95"][0] > 0:
        verdict = "SUPPORTED (interval excludes zero, in favour of C)"
    elif bt["ci95"][1] < 0:
        verdict = "CONTRADICTED (interval excludes zero, in favour of B)"
    else:
        verdict = "INCONCLUSIVE (interval includes zero)"
    return {"matched": len(docs), "paired_difference": bt, "verdict": verdict}


def requests_total(lane) -> int:
    r = lane.get("requests") or {}
    return int(r.get("own_dispatched", 0)) + int(r.get("inherited_from_b", 0))


def _key(c):
    return (c["doc"], c.get("page"), c.get("field"))


def request_gate(B, C, labels, caps, seed) -> dict:
    rule = ">= 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero"
    if caps.get("B") != caps.get("C"):
        return {"rule": rule, "applicable": False, "passes": False,
                "reason": f"caps unequal (B {caps.get('B')}, C {caps.get('C')}): the gate is defined only at equal maximum allowances (R31-03)"}
    docs = sorted({doc for f in FIELDS for doc in matched(B, C, labels, f)})
    dp = collections.defaultdict(list)
    gain = 0
    for doc in docs:
        g = sum(y(C, doc, f) - y(B, doc, f) for f in FIELDS if has_fact(labels["documents"][doc], f))
        gain += g
        dp[labels["documents"][doc]["project"]].append(g)
    bt = bootstrap(dp, seed)
    extra = requests_total(C) - requests_total(B)
    sb, sc = critical_split(B, labels), critical_split(C, labels)
    cb = {_key(c) for c in sb["resolved"] + sb["unresolved"]}
    new_false = [c for c in sc["resolved"] + sc["unresolved"] if _key(c) not in cb]
    ratio_ok = extra <= 0 or gain * THRESHOLDS["facts_per_extra_requests"] >= extra
    interval_ok = bool(bt) and bt["ci95"][0] > 0
    return {"rule": rule, "applicable": True, "caps": caps, "net_correct_facts": gain, "requests": {"B": requests_total(B), "C": requests_total(C)},
            "extra_requests": extra, "facts_per_8_extra": None if extra <= 0 else round(8 * gain / extra, 3), "net_gain_per_document": bt,
            "new_false_accepts": new_false, "passes": ratio_ok and interval_ok and not new_false,
            "policy_cost_note": "the request difference is part of the policy; nothing is reported as equal-budget accuracy"}


def decision_coverage_gate(B, C, labels, R=None) -> dict:
    """C >= B, and C >= R when the reference is scored: B runs the accepted path without evidence reads, so its evidence
    coverage can be zero; the reference (the same reader without IG / CA / DR / PA) keeps the gate meaningful for DR."""
    res = {d for d in labels["documents"] if primary(labels, d)}
    cb, cc = coverage_counts(B, labels, "decision", res), coverage_counts(C, labels, "decision", res)
    out = {"rule": "completed read or verified absence (incl. outside the title block); a wrong absence and located_incomplete are never coverage; C >= B and C >= R",
           "B": cb, "C": cc, "passes": cc["coverage"] >= cb["coverage"]}
    if R is not None:
        cr = coverage_counts(R, labels, "decision", res)
        out["R"] = cr
        out["passes"] = out["passes"] and cc["coverage"] >= cr["coverage"]
    return out


def concentration(B, C, labels) -> dict:
    out = {}
    for f in FIELDS:
        by_p, by_s = collections.Counter(), collections.Counter()
        for doc in matched(B, C, labels, f):
            g = y(C, doc, f) - y(B, doc, f)
            by_p[labels["documents"][doc]["project"]] += g
            by_s[labels["documents"][doc].get("stratum", "unknown")] += g
        net = sum(by_p.values())
        conc = net > 0 and (max(by_p.values()) > net / 2 or max(by_s.values()) > net / 2)
        out[f] = {"net_gain": net, "by_project": dict(by_p), "by_stratum": dict(by_s), "concentrated": bool(conc)}
    return out


def _sum(counters):
    t = collections.Counter()
    for c in counters:
        t.update(c or {})
    return dict(t)


def primary_outcomes(B, C, R, labels) -> dict:
    lanes = {"B": B, "C": C} | ({"R": R} if R else {})
    out = {"association": {k: _sum(d.get("association") for d in L["documents"].values()) for k, L in lanes.items()},
           "critical": {k: {s: len(v) for s, v in critical_split(L, labels).items()} for k, L in lanes.items()},
           "decision": {k: coverage_counts(L, labels, "decision") | {"accepted": _sum((d.get("accepted") or {}).get("decision") for d in L["documents"].values())}
                        for k, L in lanes.items()},
           "requests": {k: L.get("requests") for k, L in lanes.items()}, "tokens": {k: L.get("tokens") for k, L in lanes.items()}}
    if R:
        rev = [doc for doc, d in labels["documents"].items() if has_fact(d, "revision")]
        out["revision_under_PA_C_vs_R"] = {"lost": sorted(d for d in rev if y(R, d, "revision") and not y(C, d, "revision")),
                                           "gained": sorted(d for d in rev if y(C, d, "revision") and not y(R, d, "revision")),
                                           "note": "identical captured responses wherever both asked the same request (content key)"}
    return out


def evaluate(B, C, R, labels, *, caps, extensions_used, seed, stop_state=None) -> dict:
    gate = population_gate(labels, extensions_used)
    result = {"thresholds": THRESHOLDS, "population_gate": gate}
    comp = (stop_state or {}).get("comparison", "PENDING")
    if gate["action"] != "DISPATCH_ELIGIBLE":
        result["outcome"] = "PREPARATION BLOCKED" if gate["action"] == "PREPARATION BLOCKED" else f"NOT DISPATCHABLE ({gate['action']})"
        result["exercise_only"] = "the population gate refuses dispatch; any figure below exercises the scorer and is not a result"
    if comp.startswith("INVALID"):
        result.setdefault("outcome", "INVALID")
    elif comp.startswith("INCOMPLETE"):
        result.setdefault("outcome", "INCOMPLETE")
    mb, mc = lane_metrics(B, labels), lane_metrics(C, labels)
    result["metrics"] = {"B": mb, "C": mc} | ({"R": lane_metrics(R, labels)} if R else {})
    result["paired"] = {f: paired(B, C, labels, f, f"{seed}:{f}") for f in FIELDS}
    result["request_gate"] = request_gate(B, C, labels, caps, f"{seed}:requests")
    result["decision_coverage_gate"] = decision_coverage_gate(B, C, labels, R)
    result["concentration"] = concentration(B, C, labels)
    result["primary_outcomes"] = primary_outcomes(B, C, R, labels)
    reasons = []
    if mc["critical"]["resolved"] or comp.startswith("RESULT"):
        reasons.append("critical acceptance on resolved truth in C")
    for f in FIELDS:
        m = mc["fields"][f]
        if m["accepted_precision"] is not None and m["accepted_precision"] < THRESHOLDS["accepted_precision_min"]:
            reasons.append(f"{f}: accepted precision {m['accepted_precision']} < 0.98")
        if m["clean_recovery"] is None or m["clean_recovery"] < THRESHOLDS["clean_recovery_min"]:
            reasons.append(f"{f}: clean recovery {m['clean_recovery']} < 0.90")
        if result["paired"][f]["matched"] < MINIMUM:
            reasons.append(f"{f}: matched {result['paired'][f]['matched']} < {MINIMUM}")
        if result["concentration"][f]["concentrated"]:
            reasons.append(f"{f}: more than half the net gain from one project or stratum")
    if not result["request_gate"]["passes"]:
        reasons.append("request-normalised gate not met" + ("" if result["request_gate"]["applicable"] else " (not applicable: unequal caps)"))
    if not result["decision_coverage_gate"]["passes"]:
        reasons.append("decision coverage of C below B or R")
    result["reasons_not_eligible"] = reasons
    result.setdefault("outcome", "NOT ELIGIBLE" if reasons else "ELIGIBLE FOR A SEPARATE SELECTION DECISION")
    result["default_selected"] = None
    return result
