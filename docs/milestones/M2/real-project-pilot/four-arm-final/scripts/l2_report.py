"""Read-only, offline per-arm report for a document arm (the owner's twelve items). Inputs: the arm's run folder, the live
ledger (read-only), the rolling counter (read-only), the frozen labels, and an offline interim scoring folder produced by the
frozen scorer (score_arms_v4.py, AI disabled) over A + the comparison arm + this arm. No model request.
Usage: l2_report.py <arm> <tag> <compare_arm> <score_dir>   ->  REPORT-<arm>-FULL.json (+ printed summary)"""
import ast
import collections
import datetime
import hashlib
import json
import pathlib
import sqlite3
import sys
import time

arm, tag, cmp_arm, score_dir = sys.argv[1], sys.argv[2], sys.argv[3], pathlib.Path(sys.argv[4])
HERE = pathlib.Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat(timespec="seconds") if t else None
D = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
OUT = pathlib.Path("C:/t/r2x/runs") / tag / "out"
run = json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
stop = json.loads((OUT / "TERMINAL-STOP.json").read_text(encoding="utf-8")) if (OUT / "TERMINAL-STOP.json").exists() else None
rows = json.loads((OUT / "rows.json").read_text(encoding="utf-8"))
M = json.loads((score_dir / "ARMS-METRICS.v4.json").read_text(encoding="utf-8"))
EV = json.loads((score_dir / f"eval-{arm}.json").read_text(encoding="utf-8"))
EVc = json.loads((score_dir / f"eval-{cmp_arm}.json").read_text(encoding="utf-8"))
LD = pathlib.Path(D["harness_dir"]) / D["labels"]["dir"]
REG = json.loads((LD / D["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((LD / D["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((LD / D["labels"]["uncertainty"]).read_text(encoding="utf-8"))
did = {x["doc"]: x["draft_id"] for x in REG["documents"]}
conf = {x["doc"]: x["confidence"] for x in REG["documents"]}
unresolved_docs = {u["doc"] for u in UNC["uncertainty"]}
planned = D["sources"]["sample"]["documents_planned"]
ctx = {"variant": "EV1", "profile": "default", "policy": D["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]}
lim = D["ledger"]["scopes"][arm]["limits"]
scope = D["ledger"]["scopes"][arm]["scope"]
now = time.time()
R = {"generated_utc": iso(now), "arm": arm, "tag": tag, "declaration_sha256": run["declaration_sha256"], "scoring_dir": str(score_dir),
     "scorer": M["scorer"], "evaluator": M["evaluator"], "note": "interim offline scoring with the frozen scorer; the final scoring runs after all arms"}

# ---- ledger (read-only)
lc = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
lc.row_factory = sqlite3.Row
srow = lc.execute("select * from scopes where scope = ?", (scope,)).fetchone()
ents = [dict(r) for r in lc.execute("select * from entries where scope = ? order by id", (scope,))]
lc.close()
known = [e for e in ents if not e["usage_unknown"]]
unknown = [e for e in ents if e["usage_unknown"]]
breaker = srow["breaker"] if srow else None

# ---- runner state (RUN.json runner_state, else the log's last line)
rs = run.get("runner_state") or {}
if not rs:
    for line in reversed((HERE / f"{arm}.log").read_text(encoding="utf-8").splitlines()):
        if line.startswith("done ") and " state " in line:
            rs = ast.literal_eval(line.split(" state ", 1)[1].rsplit("} {", 1)[0] + "}")
            break

# 1. status
status = ("terminally stopped" if stop else "budget-stopped (breaker open)" if breaker else "deferred" if run.get("deferred") else "completed")
R["1_status"] = {"classification": status, "runner_status_field": run.get("status"), "breaker": breaker, "terminal_stop": stop}

# 2. requests
cap = D["ledger"]["caps"][arm]
budget_calls = []
for k, r in rows.items():
    for a in (((r.get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or []):
        if a.get("policy") == ctx["policy"]:
            budget_calls += [dict(c, doc=k) for c in a.get("calls") or [] if str(c.get("outcome", "")).startswith("budget")]
R["2_requests"] = {"sent_ledger_entries": len(ents), "states": dict(collections.Counter(e["state"] for e in ents)), "cap": cap,
                   "refused_before_dispatch": {"ledger_precheck": rs.get("ledger_precheck_refusals"), "rolling_counter": rs.get("xtrack_refusals"),
                                               "durable_allowance": rs.get("allowance_refusals"), "reader_calls_with_budget_outcome": len(budget_calls)},
                   "nominal_remaining": cap - len(ents), "usable_remaining": 0 if (breaker or stop) else cap - len(ents),
                   "note": "a request refused before dispatch is not a sent request and consumes no provider tokens"}

# 3. tokens
s = lambda xs, k: sum((x[k] or 0) for x in xs)
R["3_tokens"] = {"provider_reported": {"requests": len(known), "input": s(known, "act_in"), "output": s(known, "act_out"), "cached_input_within_input": s(known, "cached_in")},
                 "estimated_charge_unknown_usage": {"requests": len(unknown), "outcomes": dict(collections.Counter(e["outcome"] for e in unknown)),
                                                    "input": s(unknown, "est_in"), "output": s(unknown, "est_out")},
                 "ledger_total_accounted": {"input": s(ents, "act_in"), "output": s(ents, "act_out")},
                 "pre_dispatch_estimates_all": {"input": s(ents, "est_in"), "output": s(ents, "est_out")},
                 "scope_thresholds": {k: lim[k] for k in ("per_request_input", "per_request_output", "input_tokens", "output_tokens")}}
u = json.loads((OUT / "usage.json").read_text(encoding="utf-8"))
ev_ok = [x for x in u if not x["cache_hit"] and str(x["task"]).startswith("evidence:") and x["input_tokens"] is not None and x["outcome"] == "ok"]
R["3_tokens"]["check_app_usage_vs_ledger"] = {"app_evidence_input_incl_cached": sum(x["input_tokens"] for x in ev_ok), "ledger_known_input": s(known, "act_in"),
                                              "app_rows_inherited_from_A": sum(1 for x in u if not str(x["task"]).startswith("evidence:"))}

# 4. largest
big_in = max(known, key=lambda e: e["act_in"] or 0, default=None)
big_out = max(known, key=lambda e: e["act_out"] or 0, default=None)
R["4_largest"] = {"by_input": big_in and {k: big_in[k] for k in ("id", "task", "model", "act_in", "act_out", "cached_in", "turns", "latency_ms", "outcome")},
                  "by_output": big_out and {k: big_out[k] for k in ("id", "task", "model", "act_in", "act_out")},
                  "crossed_per_request_input": bool(big_in and big_in["act_in"] > lim["per_request_input"]),
                  "crossed_per_request_output": bool(big_out and big_out["act_out"] > lim["per_request_output"]),
                  "requests_over_per_request_input": [e["id"] for e in known if (e["act_in"] or 0) > lim["per_request_input"]],
                  "requests_over_per_request_output": [e["id"] for e in known if (e["act_out"] or 0) > lim["per_request_output"]]}

# 5. events in order
ev5 = [{"at": iso(e["at"]), "kind": "provider_failure", "ledger_id": e["id"], "task": e["task"], "outcome": e["outcome"], "usage_unknown": bool(e["usage_unknown"])}
       for e in ents if e["outcome"] != "ok"]
if breaker:
    trip = next((e for e in ents if str(e["id"]) in breaker), None)
    ev5.append({"at": iso(trip["at"]) if trip else None, "kind": "breaker_open", "reason": breaker})
if stop:
    ev5.append({"at": stop.get("at_utc") or stop.get("at"), "kind": "terminal_stop", "reason": stop.get("reason")})
R["5_events_in_order"] = sorted(ev5, key=lambda x: x["at"] or "")
R["5_consecutive_failures_at_end"] = rs.get("consecutive_failures")

# 6. grouping
deferred_eps = {str(x["ep"]) for x in run.get("deferred", [])}
na_eps = {str(x["ep"]) for x in run.get("not_attempted", [])}
groups = collections.defaultdict(list)
docinfo = {}
for p in planned:
    k, ep = p["doc"], p["doc"].split("/", 1)[0].replace("EP-", "")
    r = rows.get(k)
    atts = [a for a in (((r or {}).get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or [] if a.get("policy") == ctx["policy"] and a.get("read_sha256") == p["sha256"]]
    a = atts[-1] if atts else None
    calls = (a or {}).get("calls") or []
    sent = [c for c in calls if not str(c.get("outcome", "")).startswith("budget") and not c.get("cache_hit")]
    bud = [c for c in calls if str(c.get("outcome", "")).startswith("budget")]
    page_budget = any(str(pg.get("outcome", "")).startswith("budget") for pg in ((a or {}).get("pages") or {}).values() if isinstance(pg, dict))
    if p["extension"] != ".pdf":
        g = "not attempted (unsupported input)"
    elif ep in deferred_eps and not a:
        g = "deferred"
    elif ep in na_eps or not a:
        g = "not attempted"
    elif (bud or page_budget) and not sent:
        g = "budget-stopped"
    elif bud or page_budget or a.get("outcome") == "budget":
        g = "partially processed"
    else:
        g = "fully processed"          # the attempt ran to its end with no budget refusal; per-field gaps are in item 7
    groups[g].append(f"{did.get(k)} {k}")
    docinfo[k] = {"group": g, "requests_sent": len(sent), "budget_refused_calls": len(bud), "attempt_outcome": (a or {}).get("outcome")}
proj = collections.defaultdict(collections.Counter)
for k, v in docinfo.items():
    proj["EP-" + k.split("/", 1)[0].replace("EP-", "")][v["group"]] += 1
R["6_grouping"] = {"documents": {g: sorted(v) for g, v in groups.items()}, "counts": {g: len(v) for g, v in groups.items()},
                   "projects": {ep: dict(c) for ep, c in sorted(proj.items())}, "per_document": docinfo,
                   "runner_projects": {ep: {k: v.get(k) for k in ("documents_in", "requests", "budget_stopped", "calls", "seconds")} for ep, v in run.get("projects", {}).items()},
                   "deferred": run.get("deferred", []), "not_attempted": run.get("not_attempted", [])}

# 7. coverage
cov = M["coverage"][arm]
docs = cov["documents"]
F = ("own:identity", "own:revision", "own:decision")
USABLE = ("completed_read", "discovery_absent")


def coverage_block(docs):
    out = {}
    for f in F:
        insc = [(d["doc"], pn, pc[f]) for d in docs for pn, pc in d["pages"].items() if not pc[f].startswith("unsupported")]
        beyond = sum(1 for d in docs for pc in d["pages"].values() if pc[f].startswith("unsupported"))
        doc_full = [d["doc"] for d in docs if d["state"] != "unsupported_input" and d.get("attempted") and all(d["pages"][str(i)][f] in USABLE for i in range(1, d["in_scope_pages"] + 1))]
        out[f] = {"documents_planned": len(docs), "documents_field_usable_on_all_in_scope_pages": len(doc_full),
                  "documents_unsupported_input": sum(1 for d in docs if d["state"] == "unsupported_input"),
                  "in_scope_pages": len(insc), "in_scope_completed_read": sum(1 for x in insc if x[2] == "completed_read"),
                  "in_scope_discovery_absent": sum(1 for x in insc if x[2] == "discovery_absent"),
                  "in_scope_usable": sum(1 for x in insc if x[2] in USABLE),
                  "in_scope_classes": dict(collections.Counter(x[2] for x in insc)), "pages_beyond_reader_scope_retained": beyond}
    return out


R["7_coverage"] = {"this_arm": coverage_block(docs), "compare_arm": coverage_block(M["coverage"][cmp_arm]["documents"]),
                   "documents_required_complete": cov["summary"]["documents_required_complete"], "complete_ids": cov["summary"]["complete_ids"],
                   "note": "denominators keep all 27 planned documents, every in-scope page (budget, not attempted, failed, no region and unusable included) and the pages beyond the reader scope"}

# 8. critical + held
crit_eval = M["arms"][arm]["critical"]
held = []
for d in EV["documents"]:
    for j in ((d.get("layers") or {}).get("evidence") or {}).get("judged") or []:
        if "held" in str(j.get("outcome", "")) or j.get("state") in ("held", "conflict_held"):
            held.append({"draft_id": did.get(d["doc"]), "page": j.get("page"), "field": j["field"], "value": j.get("value"), "truth": j.get("truth"),
                         "state": j.get("state"), "outcome": j.get("outcome")})
R["8_critical_and_held"] = {"critical_acceptances_scored": crit_eval, "runner_tripwire_critical": [x for x in run.get("tripwire", []) if x.get("critical_on_resolved")],
                            "introduced_ai_errors": M["arms"][arm]["introduced_ai_errors"], "held": held,
                            "held_counts": dict(collections.Counter(h["outcome"] for h in held)),
                            "observed_errors": EV["totals"]["evidence"]["observed_errors"]}

# 9. matched comparison
pair = next((v for v in M["pairs"].values() if set(v["arms"]) == {arm, cmp_arm}), None)


def rec(evd, doc, fld):
    d = next((x for x in evd["documents"] if x["doc"] == doc), None)
    return dict(((d or {}).get("layers") or {}).get("evidence", {}).get("recovery", {}).get(fld, {})) if d else None


matched = {}
if pair:
    for f in F:
        fld = f.split(":")[1]
        rows9 = []
        for doc in pair["field_read_in_both"][f]:
            a, b = rec(EVc, doc, fld), rec(EV, doc, fld)
            rows9.append({"draft_id": did.get(doc), "label_resolved": conf.get(doc) == "high" and doc not in unresolved_docs, cmp_arm: a, arm: b, "same": a == b})
        matched[f] = {"documents_read_in_both": len(rows9), "rows": rows9, "differences": [x for x in rows9 if not x["same"]]}
R["9_matched"] = {"pair": pair and pair["arms"], "valid_both": pair and pair["valid"], "fields": matched,
                  "required_complete_in_both": pair and pair["required_complete_in_both"],
                  "inconclusive_rule": "a pair with fewer than 12 documents attempted by both arms is INCONCLUSIVE (Review 21 plan 4)",
                  "documents_attempted_by_both": sum(1 for k in docinfo if docinfo[k]["requests_sent"] > 0
                                                     and k in {d["doc"] for d in M["coverage"][cmp_arm]["documents"] if d.get("attempted")}),
                  "whole_sample_coverage_kept_in_item_7": True}

# 10. no change
st = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))
R["10_no_change"] = {"business_rows_and_roles_equal_A": M.get("no_business_change", {}).get(arm),
                     "stage_files_unchanged": sha("C:/t/r2x/r21-stage/R21-STAGE.json") == D["stage"]["manifest_sha256"] and all(sha(f["path"]) == f["sha256"] for f in st["files"]),
                     "planned_source_hashes_equal_rows": all((rows.get(p["doc"]) or {}).get("sha256") == p["sha256"] for p in planned if p["doc"] in rows),
                     "run_database": str(pathlib.Path("C:/t/r2x/runs") / tag / "db"), "tables": run.get("tables"),
                     "production": "the runner opens only its sandbox database under C:/t/r2x/runs/<tag>; no production database, live service, .env or source folder is written by it"}

# 11. ROI gate
dec_pages = []
for k, pdoc in PAGE["documents"].items():
    for r in pdoc["records"]:
        if r.get("decision") not in (None, "UR", "n/a", "") and r["page"] <= 4:
            dec_pages.append((k, r["page"], r.get("decision"), r.get("decision_location")))


def dec_class(covdocs, doc, page):
    d = next((x for x in covdocs if x["doc"] == doc), None)
    return (d or {}).get("pages", {}).get(str(page), {}).get("own:decision", "no_document")


gate_rows = [{"draft_id": did.get(k), "page": pg, "label": dval, "location": loc, cmp_arm: dec_class(M["coverage"][cmp_arm]["documents"], k, pg),
              arm: dec_class(docs, k, pg)} for k, pg, dval, loc in sorted(dec_pages, key=lambda x: (did.get(x[0]), x[1]))]
for x in gate_rows:   # every listed page HAS a labelled decision, so 'discovery_absent' there is a false absence
    x["false_absence"] = [a for a in (cmp_arm, arm) if x[a] == "discovery_absent"]
cnt = lambda a: sum(1 for x in gate_rows if x[a] in USABLE)
cnt_read = lambda a: sum(1 for x in gate_rows if x[a] == "completed_read")
both_attempted = [x for x in gate_rows if x[cmp_arm] not in ("budget", "not_attempted", "no_document") and x[arm] not in ("budget", "not_attempted", "no_document")]
R["11_roi_gate"] = {"rule": "ROI arm decision coverage (completed read or verified absence, including decisions outside the title block) >= matching whole-page arm; located_incomplete is not coverage (Review 21 plan 5)",
                    "decision_pages": gate_rows, f"{cmp_arm}_usable": cnt(cmp_arm), f"{arm}_usable": cnt(arm),
                    f"{cmp_arm}_completed_read": cnt_read(cmp_arm), f"{arm}_completed_read": cnt_read(arm),
                    "gate_by_rule": cnt(arm) >= cnt(cmp_arm), "gate_completed_read_only": cnt_read(arm) >= cnt_read(cmp_arm),
                    "pages_attempted_by_both": len(both_attempted), "pages_total": len(gate_rows),
                    "crop_eligible_D16_D17_D18": [x for x in gate_rows if x["draft_id"] in ("D16", "D17", "D18")]}

# 12. scope state
R["12_scope"] = {"scope": scope, "exists": srow is not None, "limits_equal_declared": srow is not None and json.loads(srow["limits"]) == lim,
                 "created_utc": iso(srow["created_at"]) if srow else None, "expires_utc": iso(srow["created_at"] + lim["elapsed_s"]) if srow else None,
                 "breaker": breaker, "entries": len(ents), "in_flight": sum(1 for e in ents if e["state"] not in ("settled", "released", "refused")),
                 "resume_permitted": not (breaker or stop) and bool(run.get("deferred")),
                 "why": "breaker open: budget stop, never raised" if breaker else "terminal stop preserved" if stop else "deferred projects remain" if run.get("deferred") else "nothing left to resume"}
(HERE / f"REPORT-{arm}-FULL.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(R, indent=1, default=str, ensure_ascii=False)[:60000])
