"""Final cross-arm analysis (offline, read-only; no model request) over the frozen scorer's output for A, L1..L4.
Writes ACCURACY-AND-COVERAGE.json, USAGE-AND-BUDGET.json, CRITICAL-AND-HELD-EVIDENCE.json and ARM-COMPARISON.json into
<out>. Concepts kept apart per arm / field over the 42 in-scope pages: field read completed, verified absence (absence by
discovery where the frozen truth has no fact), wrong absence (absence where the truth has a fact), accepted fact (validated
emission) split correct / wrong, held candidate split held correct / held wrong / held on a no-record page, and correct fact
recovered (the evaluator's clean, correctly associated recovery). Pairs follow the Review 21 analysis plan: document is the
unit, resolved labels primary, cluster (document) paired bootstrap, 2,000 resamples stratified by project, seed fixed.
Usage: final_analysis.py <score_dir> <out_dir>"""
import collections
import json
import pathlib
import random
import sqlite3
import sys

score, OUTD = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUTD.mkdir(parents=True, exist_ok=True)
HERE = pathlib.Path(__file__).resolve().parent
D = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
LD = pathlib.Path(D["harness_dir"]) / D["labels"]["dir"]
REG = json.loads((LD / D["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((LD / D["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((LD / D["labels"]["uncertainty"]).read_text(encoding="utf-8"))
M = json.loads((score / "ARMS-METRICS.v4.json").read_text(encoding="utf-8"))
TAGS = M["tags"]
ARMS = [a for a in D["doc_arms"] if a in M["coverage"]]
EV = {a: json.loads((score / f"eval-{a}.json").read_text(encoding="utf-8")) for a in ["A"] + ARMS}
did = {x["doc"]: x["draft_id"] for x in REG["documents"]}
conf = {x["doc"]: x["confidence"] for x in REG["documents"]}
unc = {u["doc"] for u in UNC["uncertainty"]}
resolved = lambda doc: conf.get(doc) == "high" and doc not in unc
planned = D["sources"]["sample"]["documents_planned"]
proj = lambda doc: doc.split("/", 1)[0]
F = ("identity", "revision", "decision")
NO_DECISION = (None, "", "UR", "n/a")


def fact(doc, page, f):
    recs = [r for r in PAGE["documents"].get(doc, {}).get("records", []) if r["page"] == page]
    if not recs:
        return None
    v = recs[0].get({"identity": "reference", "revision": "printed_revision", "decision": "decision"}[f])
    return None if (f == "decision" and v in NO_DECISION) or v in (None, "") else v


def judged(a, doc):
    d = next((x for x in EV[a]["documents"] if x["doc"] == doc), None)
    return [j for j in ((d or {}).get("layers") or {}).get("evidence", {}).get("judged") or [] if str(j.get("group", "")).endswith(":own")]


def doc_recovery(a, doc, f):
    d = next((x for x in EV[a]["documents"] if x["doc"] == doc), None)
    return dict(((d or {}).get("layers") or {}).get("evidence", {}).get("recovery", {}).get(f, {})) if d else {}


# ---------------- accuracy and coverage
acc = {"declaration_sha256": M["declaration_sha256"], "scorer": M["scorer"], "evaluator": M["evaluator"], "contract": M["contract"],
       "denominators": {"documents_planned": len(planned), "pdf_documents": sum(1 for p in planned if p["extension"] == ".pdf"),
                        "in_scope_pages": sum(min(p["pages"], 4) for p in planned if p["extension"] == ".pdf"),
                        "pages_beyond_reader_scope": sum(max(0, p["pages"] - 4) for p in planned if p["extension"] == ".pdf"),
                        "unsupported_documents": [did[p["doc"]] for p in planned if p["extension"] != ".pdf"]},
       "decision_no_fact_values": "UR and n/a are treated as 'no consultant decision' for absence classification", "arms": {}}
for a in ARMS:
    covd = {d["doc"]: d for d in M["coverage"][a]["documents"]}
    per = {}
    for f in F:
        c = collections.Counter()
        wrong_abs = []
        for p in planned:
            d = covd[p["doc"]]
            if d["state"] == "unsupported_input":
                c["unsupported_document"] += 1
                continue
            for pn in range(1, d["in_scope_pages"] + 1):
                cls = d["pages"][str(pn)][f"own:{f}"]
                c["pages"] += 1
                c["class:" + cls] += 1
                if cls == "completed_read":
                    c["field_read_completed"] += 1
                if cls == "discovery_absent":
                    if fact(p["doc"], pn, f) is None:
                        c["verified_absence"] += 1
                    else:
                        c["wrong_absence"] += 1
                        wrong_abs.append(f"{did[p['doc']]} p{pn}")
                if fact(p["doc"], pn, f) is not None:
                    c["pages_with_fact"] += 1
        js = [(p["doc"], j) for p in planned for j in judged(a, p["doc"]) if j["field"] == f]
        for doc, j in js:
            o, s = str(j.get("outcome")), str(j.get("state"))
            if s == "validated":
                c["accepted_fact"] += 1
                c["accepted_correct" if o == "correct" else "accepted_wrong"] += 1
            elif "held" in o or s in ("held", "conflict"):
                c["held_candidate"] += 1
                c[o] += 1
        rec = M["arms"][a]["recovery_all_planned"].get(f, {})
        per[f] = {"counts": dict(c), "wrong_absence_pages": wrong_abs, "evaluator_recovery_counts": rec.get("recovery"),
                  "accepted_precision": (f"{rec.get('precision_numerator')}/{rec.get('precision_denominator')}" if rec.get("precision_denominator") else "no accepted fact"),
                  "documents_usable_on_all_in_scope_pages": sum(1 for d in covd.values() if d["state"] != "unsupported_input" and d.get("attempted")
                                                               and all(d["pages"][str(i)][f"own:{f}"] in ("completed_read", "discovery_absent") for i in range(1, d["in_scope_pages"] + 1)))}
    states = collections.Counter(d["state"] for d in covd.values())
    pg_classes = collections.Counter(c for d in covd.values() for pc in d["pages"].values() for c in pc.values())
    acc["arms"][a] = {"tag": TAGS[a], "fields": per, "document_states": dict(states), "required_complete_documents": [did[x] for x in M["coverage"][a]["summary"]["complete_ids"]],
                      "populations": {"unsupported_documents": states.get("unsupported_input", 0), "incomplete_documents": states.get("incomplete", 0),
                                      "page_fields_budget": pg_classes.get("budget", 0), "page_fields_not_attempted": pg_classes.get("not_attempted", 0),
                                      "page_fields_beyond_scope": sum(v for k, v in pg_classes.items() if k.startswith("unsupported"))},
                      "valid_accuracy_claim_flag": M["arms"][a]["valid_accuracy_claim"],
                      "valid_flag_meaning": "technical only: some eligible evidence exists; it is not statistical or product validity"}
acc["A"] = {"note": "the accepted application path, evidence reader off; deterministic + existing AI layer only",
            "recovery_all_planned": M["arms"]["A"]["recovery_all_planned"]}
(OUTD / "ACCURACY-AND-COVERAGE.json").write_text(json.dumps(acc, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------------- usage
lc = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
lc.row_factory = sqlite3.Row
use = {"cost": "unknown (no authoritative price for the declared provider)", "caps": D["ledger"]["caps"], "scopes": {}}
tot = collections.Counter()
for a in ["A"] + list(D["doc_arms"]):
    sc = D["ledger"]["scopes"][a]["scope"]
    s = lc.execute("select * from scopes where scope = ?", (sc,)).fetchone()
    es = [dict(r) for r in lc.execute("select * from entries where scope = ? order by id", (sc,))]
    kn = [e for e in es if not e["usage_unknown"]]
    un = [e for e in es if e["usage_unknown"]]
    sm = lambda xs, k: sum(x[k] or 0 for x in xs)
    run = json.loads((pathlib.Path("C:/t/r2x/runs") / TAGS.get(a, "-") / "out/RUN.json").read_text(encoding="utf-8")) if a in TAGS else {}
    rs = run.get("runner_state") or {}
    big = max(kn, key=lambda e: e["act_in"] or 0, default=None)
    entry = {"scope": sc, "exists": s is not None, "limits": json.loads(s["limits"]) if s else None, "breaker": s["breaker"] if s else None,
             "dispatched": len(es), "cap": D["ledger"]["caps"][a], "states": dict(collections.Counter(e["state"] for e in es)),
             "refused_before_dispatch": {k: rs.get(k) for k in ("ledger_precheck_refusals", "xtrack_refusals", "allowance_refusals")} if rs else None,
             "provider_reported": {"requests": len(kn), "input": sm(kn, "act_in"), "output": sm(kn, "act_out"), "cached_input_within_input": sm(kn, "cached_in")},
             "estimated_charge_unknown_usage": {"requests": len(un), "outcomes": dict(collections.Counter(e["outcome"] for e in un)), "input": sm(un, "est_in"), "output": sm(un, "est_out")},
             "ledger_total": {"input": sm(es, "act_in"), "output": sm(es, "act_out")}, "pre_dispatch_estimates": {"input": sm(es, "est_in"), "output": sm(es, "est_out")},
             "largest_request": big and {k: big[k] for k in ("id", "task", "model", "act_in", "act_out", "cached_in")},
             "threshold_breaches": [e["id"] for e in kn if (e["act_in"] or 0) > D["ledger"]["scopes"][a]["limits"]["per_request_input"] or (e["act_out"] or 0) > D["ledger"]["scopes"][a]["limits"]["per_request_output"]],
             "models": dict(collections.Counter(f"{e['model']} / {e['outcome']}" for e in es)),
             "first_at": es[0]["at"] if es else None, "last_at": es[-1]["at"] if es else None}
    use["scopes"][a] = entry
    for k in ("dispatched",):
        tot[k] += entry[k]
    for k in ("input", "output"):
        tot["provider_" + k] += entry["provider_reported"][k]
        tot["estimated_unknown_" + k] += entry["estimated_charge_unknown_usage"][k]
        tot["ledger_" + k] += entry["ledger_total"][k]
    tot["cached_input"] += entry["provider_reported"]["cached_input_within_input"]
use["totals"] = dict(tot, cap=D["ledger"]["sum_caps"])
use["original_150_request_experiment_settled"] = lc.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
use["undeclared_family_scopes"] = [r[0] for r in lc.execute("select scope from scopes") if r[0].startswith(D["ledger"]["scope_family"]) and r[0] not in {v["scope"] for v in D["ledger"]["scopes"].values()}]
lc.close()
(OUTD / "USAGE-AND-BUDGET.json").write_text(json.dumps(use, indent=1, default=str) + "\n", encoding="utf-8")

# ---------------- critical and held
crit = {"rule": "terminal stop only for a critical acceptance on a resolved label (confidence high, not on the declared uncertainty list)", "arms": {}}
for a in ARMS:
    rows = json.loads((pathlib.Path("C:/t/r2x/runs") / TAGS[a] / "out/rows.json").read_text(encoding="utf-8"))

    def region(doc, page, field):
        obs = ((((rows.get(doc) or {}).get("extracted") or {}).get("ai_evidence") or {}).get("envelopes") or {}).get("default|EV1", {}).get("observations") or []
        o = next((x for x in obs if x.get("page") == page and x.get("field") == field and x.get("component") == "own"), None)
        return o and {"region_pt": o.get("region"), "support": o.get("support"), "read": o.get("read"), "reasons": o.get("reasons")}
    cl = [dict(c, draft_id=did.get(c["doc"]), label_resolved=resolved(c["doc"]), evidence=region(c["doc"], c["page"], c["field"])) for c in M["arms"][a]["critical"]]
    held = [{"draft_id": did.get(doc), "label_resolved": resolved(doc), "page": j.get("page"), "field": j["field"], "value": j.get("value"), "truth": j.get("truth"),
             "state": j.get("state"), "outcome": j.get("outcome")} for p in planned for doc in [p["doc"]] for j in judged(a, doc) if "held" in str(j.get("outcome"))]
    crit["arms"][a] = {"critical": cl, "critical_on_resolved": [c for c in cl if c["label_resolved"]], "held": held,
                       "held_counts": dict(collections.Counter(h["outcome"] for h in held)),
                       "accepted_wrong": [{"draft_id": did.get(doc), "page": j.get("page"), "field": j["field"], "value": j.get("value"), "truth": j.get("truth"), "outcome": j.get("outcome")}
                                          for p in planned for doc in [p["doc"]] for j in judged(a, doc) if j.get("state") == "validated" and j.get("outcome") != "correct"],
                       "observed_deterministic_errors": EV[a]["totals"]["evidence"]["observed_errors"],
                       "runner_tripwire": [x for x in json.loads((pathlib.Path("C:/t/r2x/runs") / TAGS[a] / "out/RUN.json").read_text(encoding="utf-8")).get("tripwire", []) if x.get("critical_on_resolved")]}
(OUTD / "CRITICAL-AND-HELD-EVIDENCE.json").write_text(json.dumps(crit, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------------- pairs
PAIRS = {"ROI effect without targeted reads": ("L1", "L2"), "Targeted-read effect on whole-page discovery": ("L1", "L3"),
         "Targeted-read effect under ROI": ("L2", "L4"), "ROI effect with targeted reads": ("L3", "L4")}
rng = random.Random(20261001)


def attempted(a):
    return {d["doc"] for d in M["coverage"][a]["documents"] if d.get("attempted") and d["state"] != "unsupported_input"
            and any(c not in ("not_attempted", "budget") for pc in d["pages"].values() for c in pc.values() if not c.startswith("unsupported"))}


def y(a, doc, f):
    r = doc_recovery(a, doc, f)
    return 1 if r.get("recovered_clean", 0) > 0 else 0


def boot(diffs_by_proj, n=2000):
    projs = sorted(diffs_by_proj)
    allv = [v for p in projs for v in diffs_by_proj[p]]
    if not allv:
        return None
    est = sum(allv) / len(allv)
    bs = []
    for _ in range(n):
        s = [rng.choice(diffs_by_proj[p]) for p in projs for _ in diffs_by_proj[p]]
        bs.append(sum(s) / len(s))
    bs.sort()
    return {"estimate": round(est, 4), "ci95": [round(bs[int(0.025 * n)], 4), round(bs[int(0.975 * n) - 1], 4)], "n_documents": len(allv)}


def readings(a):
    rows = json.loads((pathlib.Path("C:/t/r2x/runs") / TAGS[a] / "out/rows.json").read_text(encoding="utf-8"))
    out = {}
    for doc, r in rows.items():
        obs = ((((r.get("extracted") or {}).get("ai_evidence") or {}).get("envelopes") or {}).get("default|EV1", {}).get("observations") or [])
        for o in obs:
            if o.get("component") == "own":
                for rd in o.get("readings") or []:
                    if rd.get("source") in ("discovery", "blind_small"):
                        out[(doc, o["page"], o["field"], rd["source"])] = " ".join(str(rd.get("value") or "").upper().split())
    return out


comp = {"plan": "Review 21 ANALYSIS-PLAN: document unit, resolved labels primary, cluster bootstrap 2,000 stratified by project; fewer than 12 documents attempted by both arms is INCONCLUSIVE; four contrasts x three fields, pre-ordered: ROI alone on decision coverage first, then X on identity / revision",
        "seed": 20261001, "pairs": {}}
for name, (a, b) in PAIRS.items():
    if a not in ARMS or b not in ARMS:
        comp["pairs"][name] = {"arms": [a, b], "status": "not run"}
        continue
    both = attempted(a) & attempted(b)
    sp = next((v for v in M["pairs"].values() if v["arms"] == [a, b]), {})
    fields = {}
    for f in F:
        readable = [p["doc"] for p in planned if p["extension"] == ".pdf" and any(fact(p["doc"], pn, f) for pn in range(1, min(p["pages"], 4) + 1))]
        prim = [doc for doc in readable if resolved(doc) and doc in both]
        sec = [doc for doc in readable if not resolved(doc) and doc in both]
        dp = collections.defaultdict(list)
        for doc in prim:
            dp[proj(doc)].append(y(b, doc, f) - y(a, doc, f))
        gains = {did[doc]: y(b, doc, f) - y(a, doc, f) for doc in prim if y(b, doc, f) != y(a, doc, f)}
        by_proj = collections.Counter()
        for doc in prim:
            if y(b, doc, f) != y(a, doc, f):
                by_proj[proj(doc)] += y(b, doc, f) - y(a, doc, f)
        bt = boot(dp)
        n_m = len(sp.get("field_read_in_both", {}).get(f"own:{f}", []))
        if len(both) < 12:
            verdict = "INCONCLUSIVE (fewer than 12 documents attempted by both arms)"
        elif len(prim) < 12:
            verdict = f"INCONCLUSIVE (too few matched facts: {len(prim)} resolved documents with this fact attempted by both arms)"
        elif bt and bt["ci95"][0] > 0:
            verdict = "SUPPORTED (interval excludes zero, in favour of " + b + ")"
        elif bt and bt["ci95"][1] < 0:
            verdict = "CONTRADICTED (interval excludes zero, in favour of " + a + ")"
        else:
            verdict = "INCONCLUSIVE (interval includes zero)"
        fields[f] = {"resolved_documents_with_fact_attempted_by_both": len(prim), "unresolved_reported_separately": len(sec),
                     "matched_field_read_in_both_all_in_scope_pages": n_m, "paired_difference_resolved": bt,
                     "documents_that_differ": gains, "net_difference_by_project": dict(by_proj),
                     "gain_clustered_in_one_project": bool(by_proj) and max(abs(v) for v in by_proj.values()) >= max(1, abs(sum(by_proj.values()))) and len([v for v in by_proj.values() if v]) == 1,
                     "unresolved_differences": {did[doc]: y(b, doc, f) - y(a, doc, f) for doc in sec if y(b, doc, f) != y(a, doc, f)},
                     "verdict": verdict}
    ca, cb = acc["arms"][a], acc["arms"][b]
    ra, rb = readings(a), readings(b)
    common = [k for k in ra if k in rb]
    same_path = name.startswith("Targeted")
    ua, ub = use["scopes"][a], use["scopes"][b]
    entry = {"arms": [a, b], "documents_attempted_by_both": len(both), "minimum_documents": 12, "minimum_reached": len(both) >= 12,
             "required_complete_in_both": [did[x] for x in sp.get("required_complete_in_both", [])], "fields": fields,
             "coverage_imbalance": {arm: {"page_fields_budget": acc["arms"][arm]["populations"]["page_fields_budget"],
                                          "page_fields_not_attempted": acc["arms"][arm]["populations"]["page_fields_not_attempted"],
                                          "documents_attempted": len(attempted(arm)),
                                          "in_scope_completed_read": {f: acc["arms"][arm]["fields"][f]["counts"].get("field_read_completed", 0) for f in F}} for arm in (a, b)},
             "breaker_and_timeouts": {arm: {"breaker": use["scopes"][arm]["breaker"], "timeouts": use["scopes"][arm]["estimated_charge_unknown_usage"]["requests"]} for arm in (a, b)},
             "run_to_run_variation": {"common_first_readings": len(common), "differing": sum(1 for k in common if ra[k] != rb[k]),
                                      "examples": [{"draft_id": did.get(k[0]), "page": k[1], "field": k[2], "source": k[3], a: ra[k], b: rb[k]} for k in common if ra[k] != rb[k]][:12],
                                      "interpretation": ("same discovery input and first-read path in both arms, so differences are run-to-run model variation" if same_path
                                                         else "discovery inputs differ (whole page versus title block), so differences mix treatment and variation")},
             "requests": {a: ua["dispatched"], b: ub["dispatched"]}}
    if name.startswith("Targeted"):
        gained = sum(y(b, doc, f) - y(a, doc, f) for f in F for doc in both if resolved(doc))
        extra = ub["dispatched"] - ua["dispatched"]
        new_false = [c for c in crit["arms"][b]["critical"] if not any(c["doc"] == x["doc"] and c["page"] == x["page"] and c["field"] == x["field"] for x in crit["arms"][a]["critical"])]
        entry["x_gate"] = {"rule": ">= 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero",
                           "net_correct_facts_resolved": gained, "extra_requests": extra, "facts_per_8_extra": None if extra <= 0 else round(8 * gained / extra, 3),
                           "new_false_accepts": new_false,
                           "passes": extra > 0 and gained * 8 >= extra and not new_false and all((fields[f]["paired_difference_resolved"] or {}).get("ci95", [0, 0])[0] > 0 for f in ("identity", "revision"))}
    if name.startswith("ROI"):
        dp_rows = []
        for p in planned:
            for pn in range(1, min(p["pages"], 4) + 1) if p["extension"] == ".pdf" else []:
                if fact(p["doc"], pn, "decision"):
                    g = lambda arm: next(d for d in M["coverage"][arm]["documents"] if d["doc"] == p["doc"])["pages"][str(pn)]["own:decision"]
                    dp_rows.append({"draft_id": did[p["doc"]], "page": pn, a: g(a), b: g(b)})
        usable = lambda arm: sum(1 for r in dp_rows if r[arm] in ("completed_read", "discovery_absent"))
        read = lambda arm: sum(1 for r in dp_rows if r[arm] == "completed_read")
        entry["roi_decision_gate"] = {"rule": "ROI arm decision coverage (completed read or verified absence, incl. outside the title block) >= matching whole-page arm; located_incomplete is not coverage",
                                      "decision_pages": dp_rows, "usable_by_rule": {a: usable(a), b: usable(b)}, "completed_read": {a: read(a), b: read(b)},
                                      "note": "every listed page carries a labelled decision, so 'discovery_absent' on it is a wrong absence; the strict count uses completed reads only",
                                      "passes_by_rule": usable(b) >= usable(a), "passes_completed_read_only": read(b) >= read(a)}
    comp["pairs"][name] = entry
(OUTD / "ARM-COMPARISON.json").write_text(json.dumps(comp, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------------- adoption gates (per arm, against the accepted path A where a baseline is needed)
gates = {}
for a in ARMS:
    dec_a = acc["arms"][a]["fields"]["decision"]["counts"]
    gates[a] = {"no_critical_on_resolved_truth": not crit["arms"][a]["critical_on_resolved"],
                "critical_on_uncertain_truth": [f"{c['draft_id']} p{c['page']} {c['field']}" for c in crit["arms"][a]["critical"] if not c["label_resolved"]],
                "decision_completed_reads": dec_a.get("field_read_completed", 0), "decision_wrong_absences": dec_a.get("wrong_absence", 0),
                "denominators_retained": True}
summary = {"gates": gates, "default_selected": None,
           "statement": "No default variant is selected or deployed. Coverage or request-count differences alone are not grounds for a default; pairs with too few matched facts are inconclusive."}
(OUTD / "ADOPTION-GATES.json").write_text(json.dumps(summary, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({n: {"min": v.get("minimum_reached"), "attempted_both": v.get("documents_attempted_by_both"),
                      "fields": {f: (x["resolved_documents_with_fact_attempted_by_both"], x["matched_field_read_in_both_all_in_scope_pages"], x["paired_difference_resolved"], x["verdict"]) for f, x in v.get("fields", {}).items()},
                      "x_gate": v.get("x_gate"), "roi_gate": v.get("roi_decision_gate") and {k: v["roi_decision_gate"][k] for k in ("usable_by_rule", "completed_read", "passes_by_rule", "passes_completed_read_only")},
                      "variation": v.get("run_to_run_variation", {}).get("differing"), "common": v.get("run_to_run_variation", {}).get("common_first_readings")}
                  for n, v in comp["pairs"].items()}, indent=1, default=str))
print(json.dumps(gates, indent=1))
