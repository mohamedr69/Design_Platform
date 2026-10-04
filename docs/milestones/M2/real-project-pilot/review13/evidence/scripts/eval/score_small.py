"""Round 2 small batch: per-profile scores with the reviewed evaluator (.9, frozen-r12) against the PROVISIONAL labels,
plus usage / latency / failure accounting and the cross-profile critical disagreements for the worklist.

Inputs: the declaration (hash-checked), the evaluator label files (register-derived + page labels eval-derived), each
track's rows.json / usage.json / RUN.json, the ledger (read only), the BOQ outputs when present.
Outputs (C:/t/iso/work/r2x/eval): eval-<track>.json (the evaluator's own output), SMALL-METRICS.json, DISAGREEMENTS.json."""
import collections
import hashlib
import json
import pathlib
import sqlite3
import statistics
import subprocess
import sys

W = pathlib.Path("C:/t/iso/work/r2x")
E = W / "eval"
RUNS = pathlib.Path("C:/t/r2x/runs")
DECL = W / "run/EXPERIMENT-DECLARATION-SMALL.json"
DECL_SHA = "c146e5752003a890256a0c612ceaa6f164766cb7e8683bf120fdd875e0f9c988"
assert hashlib.sha256(DECL.read_bytes()).hexdigest() == DECL_SHA
REG = W / "labels/SMALL-BATCH-REGISTER-LABELS.json"
PAGE = W / "labels/SMALL-BATCH-LABELS.eval.json"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python"
TRACKS = {"det": "r2x-small-det", "A": "r2x-small-A", "B": "r2x-small-B", "C": "r2x-small-C"}
FIELDS = ("identity", "revision", "decision")
TRUTH_STATUS = "PROVISIONAL: AI-drafted proposal labels, no human review; not accuracy evidence"


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


# the evaluator in-process, as the accepted Review 12 re-score ran it (rescore_r12.py): each run is scored under its
# DECLARED context -- no AI stage for det / A, the declared variant and profile for B / C -- so another run's AI evidence
# is never scored for it (R8-02)
import os  # noqa: E402

os.environ.setdefault("AI_ENABLED", "false")
sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
os.chdir("C:/t/iso/frozen-r12/backend")
from scripts import m2_eval5 as EV  # noqa: E402

DET = {"variant": None, "declared": "no AI evidence stage in this run (r2x-small declaration: det / profile A)"}
CONTEXT = {"det": DET, "A": DET, "B": {"variant": "EV1", "profile": "default", "declared": "r2x-small declaration: default profile, EV1"},
           "C": {"variant": "EV2", "profile": "default", "declared": "r2x-small declaration: default profile, EV2"}}
REG_J = json.loads(REG.read_text(encoding="utf-8"))
PAGE_J = json.loads(PAGE.read_text(encoding="utf-8"))
metrics = {"truth_status": TRUTH_STATUS, "declaration_sha256": DECL_SHA, "labels": {"register": sha(REG), "page_eval": sha(PAGE)},
           "evaluator": None, "profiles": {}}
asserted = collections.defaultdict(dict)       # (doc, page, field) -> {track: set(values)}
for track, tag in TRACKS.items():
    rows = RUNS / tag / "out/rows.json"
    if not rows.exists():
        metrics["profiles"][track] = {"status": "not run"}
        continue
    out = E / f"eval-{track}.json"
    ev = EV.evaluate(REG_J, PAGE_J, json.loads(rows.read_text(encoding="utf-8")), PAGE_J.get("page1_corrections"), ai_context=CONTEXT[track])
    out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    metrics["evaluator"] = ev["evaluator"]
    t = ev["totals"]["evidence"]
    fields = {}
    for f in FIELDS:
        v = t["fields"][f]
        rc = v["recovery_counts"]
        fields[f] = {"readable_denominator": v["readable"], "recovered_clean": rc.get("recovered_clean", 0), "recovered_mixed": rc.get("recovered_mixed", 0),
                     "held_only (not recovered)": rc.get("held_only", 0), "wrong_only": rc.get("wrong_only", 0), "missed": rc.get("missed", 0),
                     "known_negatives_tn": rc.get("tn", 0), "false_positives_fp": rc.get("fp", 0), "unscorable": rc.get("unscorable", 0),
                     "accepted_on_conflict (critical)": rc.get("accepted_on_conflict", 0), "conflict_held": rc.get("conflict_held", 0),
                     "asserted_distinct": v["asserted_distinct"], "precision_counts": v["precision_counts"],
                     "accepted_precision": v["accepted_precision"], "automatic_recovery": v["recovery"]}
    per_doc = []
    for d in ev["documents"]:
        lay = d["layers"]["evidence"]
        per_doc.append({"doc": d["doc"], "ep": d["ep"], "stratum": d.get("stratum"), "execution": d.get("execution"), "ai_state": d.get("ai_evidence_state"),
                        "components": [{"page": c["page"], "fields": c["fields"]} for c in lay["components"]],
                        "critical": lay["critical"], "observed_errors": len(lay["observed_errors"]),
                        "unscored_page_facts": len(d.get("unvalidated") or [])})
        for j in lay["judged"]:
            if j.get("state") in ("accepted", "observed", "validated"):
                asserted[(d["doc"], j.get("page"), j["field"])].setdefault(track, set()).add(str(j.get("value")))
    by = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for d in per_doc:
        for c in d["components"]:
            for f, s in c["fields"].items():
                by["project"][f"EP-{d['ep']}:{f}"][s] += 1
                by["stratum"][f"{d['stratum']}:{f}"][s] += 1
    usage_f = RUNS / tag / "out/usage.json"
    usage = json.loads(usage_f.read_text(encoding="utf-8")) if usage_f.exists() else []
    mine = [u for u in usage if (track in ("B", "C") and str(u["task"]).startswith("evidence:")) or (track == "A" and not str(u["task"]).startswith("evidence:"))]
    fresh = [u for u in mine if not u["cache_hit"]]
    lat = [u["latency_ms"] for u in fresh if u["latency_ms"]]
    run = json.loads((RUNS / tag / "out/RUN.json").read_text(encoding="utf-8"))
    metrics["profiles"][track] = {
        "fields": fields, "critical": t["critical"], "critical_count": len(t["critical"]), "observed_errors": len(t["observed_errors"]),
        "ai_evidence_states": ev["totals"].get("ai_evidence_states"), "by_project": {k: dict(v) for k, v in by["project"].items()},
        "by_stratum": {k: dict(v) for k, v in by["stratum"].items()}, "documents": per_doc,
        "usage": {"requests_fresh": len(fresh), "cache_hits": sum(1 for u in mine if u["cache_hit"]),
                  "by_task": dict(collections.Counter(u["task"] for u in fresh)), "by_model": dict(collections.Counter(u["model"] for u in fresh)),
                  "outcomes": dict(collections.Counter(u["outcome"] for u in fresh)), "escalated": sum(1 for u in fresh if u["escalated"]),
                  "input_tokens_actual": sum(u["input_tokens"] or 0 for u in fresh), "output_tokens_actual": sum(u["output_tokens"] or 0 for u in fresh),
                  "cached_input_tokens_actual": sum(u["cached_input_tokens"] or 0 for u in fresh),
                  "latency_ms": {"n": len(lat), "median": statistics.median(lat) if lat else None, "p90": pct(lat, 0.9), "max": max(lat) if lat else None},
                  "cost": "unknown (no trustworthy price configured)"},
        "run": {k: run.get(k) for k in ("seconds", "runner_state", "fresh_requests", "fresh_requests_this_track", "tables")},
        "budget_stops": sum((p or {}).get("budget_stopped", 0) for p in (run.get("projects") or {}).values() if isinstance(p, dict)),
    }
# controls: a run scored under a context it did not run in must show no AI evidence
metrics["controls"] = {}
for name, track, ctx in (("B-as-EV2", "B", CONTEXT["C"]), ("C-as-EV1", "C", CONTEXT["B"]), ("B-without-context", "B", None)):
    rows = RUNS / TRACKS[track] / "out/rows.json"
    if rows.exists():
        c = EV.evaluate(REG_J, PAGE_J, json.loads(rows.read_text(encoding="utf-8")), PAGE_J.get("page1_corrections"), ai_context=ctx)
        metrics["controls"][name] = {"ai_evidence_states": c["totals"].get("ai_evidence_states"),
                                     "ai_layer_asserted": {f: c["totals"]["ai"]["fields"][f]["asserted_distinct"] for f in FIELDS}}
# the ledger, read only
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
ent = con.execute("select task, model, state, est_in, est_out, act_in, act_out, cached_in, turns, latency_ms, outcome, usage_unknown from entries where scope = ?",
                  ("r2x-small-2026-09-29",)).fetchall()
scope = con.execute("select limits, breaker from scopes where scope = ?", ("r2x-small-2026-09-29",)).fetchone()
con.close()
settled = [e for e in ent if e[2] == "settled"]
metrics["ledger"] = {"scope": "r2x-small-2026-09-29", "limits": json.loads(scope[0]), "breaker": scope[1], "entries": len(ent),
                     "by_state": dict(collections.Counter(e[2] for e in ent)), "by_outcome": dict(collections.Counter(e[10] for e in ent)),
                     "requests_settled": len(settled), "usage_unknown": sum(1 for e in ent if e[11]),
                     "input_tokens_actual": sum(e[5] or 0 for e in settled), "output_tokens_actual": sum(e[6] or 0 for e in settled),
                     "cached_input_tokens_actual": sum(e[7] or 0 for e in settled), "turns_reported": sum(e[8] or 0 for e in settled),
                     "input_tokens_estimated": sum(e[3] or 0 for e in ent), "output_tokens_estimated": sum(e[4] or 0 for e in ent),
                     "models_reported": dict(collections.Counter(e[1] for e in settled)),
                     "note": "actual = provider-reported; estimated = the ledger's preflight reservation; neither is a provider-enforced cap (CLI adapter)"}
app_fresh = sum(p.get("usage", {}).get("requests_fresh", 0) for p in metrics["profiles"].values() if isinstance(p, dict))
boq_usage = 0
for tag in ("r2x-small-boq-B", "r2x-small-boq-C"):
    f = RUNS / tag / "out/usage.json"
    if f.exists():
        boq_usage += sum(1 for u in json.loads(f.read_text(encoding="utf-8")) if not u["cache_hit"])
metrics["accounting"] = {"fresh_ai_usage_all_tracks": app_fresh + boq_usage, "ledger_settled_plus_unknown": len(settled),
                         "reconciles": app_fresh + boq_usage == len(settled)}
# cross-profile critical disagreements (identity / revision / decision asserted differently by two profiles on one page)
dis = []
for (doc, page, field), per in sorted(asserted.items(), key=lambda kv: str(kv[0])):
    vals = {t: sorted(v) for t, v in per.items()}
    if len({tuple(v) for v in vals.values()}) > 1 or any(len(v) > 1 for v in vals.values()):
        dis.append({"doc": doc, "page": page, "field": field, "asserted_by_profile": vals})
crit = [dict(c, profile=t) for t, p in metrics["profiles"].items() if isinstance(p, dict) for c in p.get("critical", [])]
(E / "DISAGREEMENTS.json").write_text(json.dumps({"truth_status": TRUTH_STATUS, "critical_false_accepts": crit, "cross_profile": dis}, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
metrics["disagreements"] = {"critical_false_accepts": len(crit), "cross_profile": len(dis)}
(E / "SMALL-METRICS.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
for track, p in metrics["profiles"].items():
    if "fields" not in p:
        print(track, p)
        continue
    print(track, "critical", p["critical_count"], "| requests", p["usage"]["requests_fresh"], "| budget stops", p["budget_stops"],
          "|", {f: f"{v['recovered_clean'] + v['recovered_mixed']}/{v['readable_denominator']} held {v['held_only (not recovered)']} tn {v['known_negatives_tn']} fp {v['false_positives_fp']}"
                for f, v in p["fields"].items()})
print("ledger", {k: metrics["ledger"][k] for k in ("requests_settled", "by_state", "input_tokens_actual", "output_tokens_actual", "models_reported")})
print("controls", metrics["controls"])
print("accounting", metrics["accounting"], "| disagreements", metrics["disagreements"])
