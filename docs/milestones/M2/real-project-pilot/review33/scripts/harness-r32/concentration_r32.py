"""ORCH-05.1: the C-4 replacement concentration rule (owner decision A-05), frozen before any prediction.

Per field f, over the MATCHED documents (canonical, resolved for f, carrying f, attempted by B and by C):
  g(doc) = y_C(doc, f) - y_B(doc, f)  (clean, correctly associated recovery, 0/1; NOT_SCORABLE rows never enter y)
  net gain = sum g;   failures of C in f = wrong acceptances on resolved truth in f (every attempted document, incl. controls)
                                            + lost facts (matched documents with y_B = 1 and y_C = 0)
Measured, by project, by contractor, by layout/template key and by decision type (stratum is reported only):
  gain_by_group, positive/negative contributions, share of the net gain, failures and share of the failures.
Decision controls per lane (B, C and R when given): positive = decision truth present and resolved (the document carries
the decision); negative = every in-scope decision row a scorable ABSENT (blank_decision_area / no_decision_area) with the
document field resolved. attempted / correct / false-accept counts. Positives may come from any stratum (review-signal paths
included); no stratum is required to hold a positive.

Outcome per field (THRESHOLDS, justified in CONCENTRATION-RULE-R32.md):
  NOT ELIGIBLE  (1) net gain >= 4 and one project, one contractor or one layout key holds MORE than half of it; or
                (2) failures >= 2, MORE than half of them in one project, contractor or layout key, and that group's own net
                    gain is negative (a regression concentrated in one group); or
                (3) decision field: any false acceptance by C on a negative decision control.
  UNDETERMINED  none of the above and net gain < 4: the gain is too small for its distribution to be judged; reported, never
                blocking (the field's other gates still apply).
  ELIGIBLE      none of the above and net gain >= 4.
Decision type and stratum are measured and reported but never block: by construction about 4 in 5 decision documents are
'approved as noted' and 37 of 38 are review_signal (R33-01), so a blocking leg there would be unreachable again.
Pure functions; every output carries the reference-set statement of AI-ACCURACY-POLICY-AMENDMENT-R32-01."""
from __future__ import annotations

import collections

import labels_adapter_r32 as A
import lane_judge_r32 as J

RULE_VERSION = "concentration-r32-2026-10-03.1"
THRESHOLDS = {"min_net_gain": 4, "gain_share_max": 0.5, "min_failures": 2, "failure_share_max": 0.5,
              "negative_control_false_accepts_max": 0}
BLOCKING_GROUPINGS = ("project", "contractor", "layout_key")
REPORTED_GROUPINGS = ("decision_type", "stratum")
REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"


def matched(B, C, truth, f, docs=None):
    return sorted(pid for pid in truth["documents"] if (docs is None or pid in docs) and A.has_fact(truth, pid, f)
                  and A.primary(truth, pid, f) and J.attempted(B, pid) and J.attempted(C, pid))


def _group_of(truth, pid, grouping):
    return truth["documents"][pid][grouping] or "unknown"


def _share(part, whole):
    return round(part / whole, 4) if whole else None


def field_concentration(B, C, truth, f, *, jB=None, jC=None, docs=None) -> dict:
    jB = jB if jB is not None else J.judge_lane(B, truth)
    jC = jC if jC is not None else J.judge_lane(C, truth)
    m = matched(B, C, truth, f, docs)
    g = {pid: J.y(jC, pid, f) - J.y(jB, pid, f) for pid in m}
    net = sum(g.values())
    lost = sorted(pid for pid in m if J.y(jB, pid, f) == 1 and J.y(jC, pid, f) == 0)
    wrong = [c for pid, d in jC.items() if (docs is None or pid in docs) and J.attempted(C, pid) and not truth["documents"][pid]["is_alias"]
             for c in d["fields"][f]["critical"]]
    failures = [{"pool_id": pid, "kind": "lost_fact"} for pid in lost] + [{"pool_id": c["pool_id"], "kind": "wrong_acceptance", "page": c["page"]} for c in wrong]
    groupings = {}
    for grouping in BLOCKING_GROUPINGS + REPORTED_GROUPINGS:
        gain, pos, neg, fail = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
        for pid, v in g.items():
            k = _group_of(truth, pid, grouping)
            gain[k] += v
            pos[k] += max(v, 0)
            neg[k] += -min(v, 0)
        for x in failures:
            fail[_group_of(truth, x["pool_id"], grouping)] += 1
        keys = sorted(set(gain) | set(fail))
        top_gain = max(keys, key=lambda k: (gain[k], k)) if keys and net > 0 else None
        top_fail = max(keys, key=lambda k: (fail[k], k)) if failures else None
        groupings[grouping] = {
            "groups": {k: {"matched": sum(1 for pid in g if _group_of(truth, pid, grouping) == k), "net_gain": gain[k],
                           "gains": pos[k], "losses": neg[k], "share_of_net_gain": _share(gain[k], net) if net > 0 else None,
                           "failures": fail[k], "share_of_failures": _share(fail[k], len(failures))} for k in keys},
            "largest_gain_group": top_gain, "largest_gain_share": _share(gain[top_gain], net) if top_gain is not None else None,
            "largest_failure_group": top_fail, "largest_failure_share": _share(fail[top_fail], len(failures)) if top_fail is not None else None,
            "blocking": grouping in BLOCKING_GROUPINGS}
    reasons, notes = [], []
    th = THRESHOLDS
    for grouping in BLOCKING_GROUPINGS:
        gr = groupings[grouping]
        if net >= th["min_net_gain"] and gr["largest_gain_group"] is not None and gr["groups"][gr["largest_gain_group"]]["net_gain"] > th["gain_share_max"] * net:
            reasons.append(f"{f}: {gr['groups'][gr['largest_gain_group']]['net_gain']} of the net gain {net} (> half) from one {grouping} ({gr['largest_gain_group']})")
        if len(failures) >= th["min_failures"] and gr["largest_failure_group"] is not None:
            k = gr["largest_failure_group"]
            if gr["groups"][k]["failures"] > th["failure_share_max"] * len(failures) and gr["groups"][k]["net_gain"] < 0:
                reasons.append(f"{f}: {gr['groups'][k]['failures']} of {len(failures)} failures (> half) in one {grouping} ({k}), whose net gain is {gr['groups'][k]['net_gain']}")
    controls = decision_controls({"B": B, "C": C}, truth, docs=docs) if f == "decision" else None
    if controls and controls["C"]["negative"]["false_accept"] > th["negative_control_false_accepts_max"]:
        reasons.append(f"decision: {controls['C']['negative']['false_accept']} false acceptance(s) by C on negative decision controls")
    if reasons:
        outcome = "NOT ELIGIBLE"
    elif net < th["min_net_gain"]:
        outcome = "UNDETERMINED"
        notes.append(f"net gain {net} < {th['min_net_gain']}: distribution not judged; reported, not blocking")
    else:
        outcome = "ELIGIBLE"
    mainly = {grouping: {"gains_mainly_from": groupings[grouping]["largest_gain_group"] if (net > 0 and groupings[grouping]["largest_gain_share"] or 0) > 0.5 else None,
                         "failures_mainly_from": groupings[grouping]["largest_failure_group"] if (groupings[grouping]["largest_failure_share"] or 0) > 0.5 else None}
              for grouping in BLOCKING_GROUPINGS}
    statement = _statement(f, net, len(m), failures, groupings, mainly)
    return {"field": f, "rule_version": RULE_VERSION, "thresholds": THRESHOLDS, "matched": len(m), "net_gain": net,
            "per_document": g, "lost_facts": lost, "wrong_acceptances": wrong, "failures": len(failures), "groupings": groupings,
            "mainly_from": mainly, "decision_controls": controls, "outcome": outcome, "reasons": reasons, "notes": notes,
            "attribution_statement": statement, "reference_set_statement": REFERENCE_SET_STATEMENT}


def _statement(f, net, n, failures, groupings, mainly) -> str:
    parts = [f"{f}: net gain {net} over {n} matched documents"]
    for grouping in BLOCKING_GROUPINGS:
        gr = groupings[grouping]
        if net > 0 and gr["largest_gain_group"] is not None:
            parts.append(f"largest {grouping} share of the gain {gr['largest_gain_share']} ({gr['largest_gain_group']})")
    parts.append(f"failures {len(failures)}")
    for grouping in BLOCKING_GROUPINGS:
        gr = groupings[grouping]
        if failures:
            parts.append(f"largest {grouping} share of the failures {gr['largest_failure_share']} ({gr['largest_failure_group']})")
    g_main = [f"{k}={v['gains_mainly_from']}" for k, v in mainly.items() if v["gains_mainly_from"]]
    f_main = [f"{k}={v['failures_mainly_from']}" for k, v in mainly.items() if v["failures_mainly_from"]]
    parts.append("gains come mainly from one " + ", ".join(g_main) if g_main else "gains do not come mainly from one project, contractor or layout")
    parts.append("failures come mainly from one " + ", ".join(f_main) if f_main else "failures do not come mainly from one project, contractor or layout")
    return "; ".join(parts)


def decision_controls(lanes: dict, truth, docs=None) -> dict:
    """attempted / correct / false-accept counts per lane for positive and negative decision controls, by stratum too."""
    out = {}
    for name, lane in lanes.items():
        if lane is None:
            continue
        jl = J.judge_lane(lane, truth)
        res = {}
        for ctl in ("positive", "negative"):
            ids = sorted(pid for pid, d in truth["documents"].items() if not d["is_alias"] and d["decision_control"] == ctl
                         and pid in (lane.get("documents") or {}) and (docs is None or pid in docs))
            att = [pid for pid in ids if J.attempted(lane, pid)]
            if ctl == "positive":
                correct = [pid for pid in att if J.y(jl, pid, "decision") == 1]
                fa = [pid for pid in att if jl[pid]["fields"]["decision"]["critical"]]
            else:
                fa = [pid for pid in att if jl[pid]["fields"]["decision"]["negatives"].get("fp")]
                correct = [pid for pid in att if pid not in fa]
            by_stratum = collections.Counter(truth["documents"][pid]["stratum"] for pid in ids)
            res[ctl] = {"documents": len(ids), "attempted": len(att), "correct": len(correct), "false_accept": len(fa),
                        "false_accept_documents": fa, "by_stratum": dict(by_stratum)}
        out[name] = res
    return out


def evaluate(B, C, truth, *, R=None, docs=None) -> dict:
    jB, jC = J.judge_lane(B, truth), J.judge_lane(C, truth)
    fields = {f: field_concentration(B, C, truth, f, jB=jB, jC=jC, docs=docs) for f in A.FIELDS}
    pc = {}
    for name, lane in (("B", B), ("C", C), ("R", R)):
        if lane is None:
            continue
        pc[name] = {}
        for pid in (lane.get("documents") or {}):
            d = truth["documents"].get(pid)
            if d and not d["is_alias"]:
                pc[name].setdefault(d["project"], d["contractor"])
    one_to_one = all(len(set(v.values())) == len(v) for v in pc.values())
    return {"rule_version": RULE_VERSION, "thresholds": THRESHOLDS, "fields": fields,
            "decision_controls": decision_controls({"B": B, "C": C, "R": R}, truth, docs=docs),
            "contractor_equals_project": one_to_one,
            "contractor_note": ("each project has exactly one contractor in PROJECT-VERIFICATION.json, so the contractor leg "
                                "equals the project leg for this cohort" if one_to_one else "contractors differ from projects"),
            "reference_set_statement": REFERENCE_SET_STATEMENT}
