"""Continuation scoring (written and dry-tested before any continuation request). Documents: accepted evaluator .9
(frozen-r12, unchanged) with the continuation labels under each arm's declared context; complete planned coverage and
the matched completed subset; per-case S -> T2 changes with their route (targeted read / region support / located
discovery); discovery timing S vs T2 (and S's pilot timings for the controls). H-06: accepted r16.1 replay_core +
boq_contract with the r14.1 amended labels and the verified row geometry; the wrong-quantity targets and the control are
identified HERE only; reached / unreached rows; at equal requests and at each arm's cap.
Usage: score_cont.py --declaration D --declaration-sha SHA --runs ROOT --tags A=..,S=..,T2=..[,BOQ-S=..,BOQ-T=..] --out DIR"""
import argparse
import collections
import hashlib
import json
import os
import pathlib
import sqlite3
import statistics
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--declaration", required=True); ap.add_argument("--declaration-sha", required=True)
ap.add_argument("--runs", required=True); ap.add_argument("--tags", required=True); ap.add_argument("--out", required=True)
args = ap.parse_args()
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
R = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
RUNS = pathlib.Path(args.runs)
TAGS = dict(kv.split("=", 1) for kv in args.tags.split(","))
OUT = pathlib.Path(args.out)
OUT.mkdir(parents=True, exist_ok=True)
L = decl["labels"]
for n, h in L["files"].items():
    assert hashlib.sha256((R / L["dir"] / n).read_bytes()).hexdigest() == h, n
os.environ.setdefault("AI_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/score-no-db.db")
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):
    os.environ.pop(k, None)
sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
os.chdir("C:/t/iso/frozen-r12/backend")
from scripts import m2_eval5 as EV  # noqa: E402

assert hashlib.sha256(pathlib.Path(EV.__file__).read_bytes()).hexdigest() == decl["code"]["evaluator"]["sha256"]
sys.path.insert(0, "C:/t/iso/work/r2x/r16")
import boq_contract as bc  # noqa: E402
import replay_core as rc  # noqa: E402

REG = json.loads((R / L["dir"] / L["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((R / L["dir"] / L["page"]).read_text(encoding="utf-8"))
UNC = json.loads((R / L["dir"] / L["uncertainty"]).read_text(encoding="utf-8"))
unresolved = {u["doc"] for u in UNC["uncertainty"]} | {d["doc"] for d in REG["documents"] if d.get("confidence") != "high"}
meta = {d["doc"]: d for d in REG["documents"]}
roles = decl["sources"]["sample"]["roles"]
CTX = {"A": {"variant": None}}
for arm in decl["doc_arms"]:
    CTX[arm] = {"variant": "EV1", "profile": "default", "policies": [decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]]}


def attempt(row, arm):
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    pol = (CTX.get(arm, {}).get("policies") or [None])[0]
    atts = [a for a in ai.get("attempts") or [] if a.get("policy") == pol]
    return (atts[-1] if atts else None), ((ai.get("envelopes") or {}).get("default|EV1") or {})


def calls_of(att):
    return [c for c in (att or {}).get("calls") or [] if not c.get("cache_hit")]


def stop_of(att):
    if att is None:
        return "not_selected_or_not_attempted"
    bad = sorted({str(c.get("outcome")) for c in att.get("calls") or [] if str(c.get("outcome", "")) != "ok"})
    return "complete" if not bad else "stopped: " + "; ".join(b[:80] for b in bad)


metrics = {"truth_status": "PROVISIONAL (AI-drafted / AI-reviewed labels; not human truth)", "declaration_sha256": args.declaration_sha,
           "evaluator": EV.EVALUATOR_VERSION, "tags": TAGS, "unresolved_labels": sorted(unresolved), "arms": {}}
per_case, cover, timing = {}, {}, collections.defaultdict(dict)
for arm in ["A"] + decl["doc_arms"]:
    f = RUNS / TAGS.get(arm, "-") / "out/rows.json"
    if arm not in TAGS or not f.exists():
        metrics["arms"][arm] = {"status": "not run"}
        continue
    rows = json.loads(f.read_text(encoding="utf-8"))
    run = json.loads((RUNS / TAGS[arm] / "out/RUN.json").read_text(encoding="utf-8"))
    usage = json.loads((RUNS / TAGS[arm] / "out/usage.json").read_text(encoding="utf-8"))
    ev = EV.evaluate(REG, PAGE, rows, PAGE.get("page1_corrections"), ai_context=CTX[arm])
    (OUT / f"eval-{arm}.json").write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    t = ev["totals"]
    for d in ev["documents"]:
        for fld in EV.FIELDS:
            per_case.setdefault((d["doc"], fld), {})[arm] = {"evidence": {k: n for k, n in (d["layers"]["evidence"]["recovery"].get(fld) or {}).items() if n},
                                                           "ai": {k: n for k, n in (d["layers"]["ai"]["recovery"].get(fld) or {}).items() if n},
                                                           "precision": {k: n for k, n in (d["layers"]["evidence"]["precision"].get(fld) or {}).items() if n}}
    if arm != "A":
        for doc in meta:
            att, env = attempt(rows.get(doc), arm)
            cs = calls_of(att)
            pages = (att or {}).get("pages") or {}
            cover.setdefault(doc, {})[arm] = {"state": stop_of(att), "requests": len(cs), "tasks": [c["task"] for c in cs],
                                              "fields": {p: {k: v for k, v in (pg.get("fields") or {}).items() if not k.startswith("ref")} for p, pg in pages.items()}}
            disc = [c for c in cs if str(c["task"]).startswith("discover")]
            timing[doc][arm] = {"discovery_ms": [c.get("latency_ms") for c in disc], "discovery_task": [c["task"] for c in disc],
                                "discovery_input_tokens": [c.get("input_tokens") for c in disc], "all_ms": sum(c.get("latency_ms") or 0 for c in cs)}
    fresh = [u for u in usage if not u["cache_hit"]]
    by_task = collections.defaultdict(list)
    for u in fresh:
        by_task[u["task"]].append(u)
    crit = t["evidence"]["critical"]
    metrics["arms"][arm] = {
        "tag": TAGS[arm], "context": CTX[arm],
        "evidence_layer": {fld: {**x, "precision_numerator": x["precision_counts"].get("correct", 0), "precision_denominator": x["asserted_distinct"]}
                           for fld, x in t["evidence"]["fields"].items()},
        "ai_layer": t["ai"]["fields"], "raw_layer": t["raw"]["fields"],
        "critical": {"resolved": [c for c in crit if c["doc"] not in unresolved], "unresolved_label": [c for c in crit if c["doc"] in unresolved]},
        "introduced_ai_errors": t["introduced_ai_errors"],
        "usage": {"requests": len(fresh), "outcomes": dict(collections.Counter(u["outcome"] for u in fresh)),
                  "models": dict(collections.Counter(u["model"] for u in fresh)),
                  "by_task": {k: {"n": len(v), "latency_ms_median": statistics.median([x["latency_ms"] or 0 for x in v]),
                                  "latency_ms_max": max(x["latency_ms"] or 0 for x in v), "input_tokens_total_incl_cached": sum(x["input_tokens"] or 0 for x in v),
                                  "cached_input_tokens": sum(x["cached_input_tokens"] or 0 for x in v), "output_tokens": sum(x["output_tokens"] or 0 for x in v)}
                              for k, v in by_task.items()},
                  "cost": "UNKNOWN"},
        "runner": {k: run.get(k) for k in ("runner_state", "not_attempted", "tripwire", "seconds", "projects", "business_hashes", "tables", "fresh_requests")}}

# the pilot's S timings for the exposed controls (earlier run, same accepted code)
pilot_rows = json.loads(pathlib.Path("C:/t/r2x/runs/ai-pilot-S/out/rows.json").read_text(encoding="utf-8"))
pilot_pol = json.loads(pathlib.Path("C:/t/iso/work/r2x/ai-pilot/PILOT-DECLARATION.json").read_text(encoding="utf-8"))["arms"]["S"]["identities"]["EVIDENCE_POLICY_VERSION"]
for doc in meta:
    ai = ((pilot_rows.get(doc) or {}).get("extracted") or {}).get("ai_evidence") or {}
    atts = [a for a in ai.get("attempts") or [] if a.get("policy") == pilot_pol]
    if atts:
        cs = calls_of(atts[-1])
        timing[doc]["S_pilot"] = {"discovery_ms": [c.get("latency_ms") for c in cs if str(c["task"]).startswith("discover")],
                                  "outcomes": [str(c.get("outcome"))[:60] for c in cs]}

arms_run = [a for a in decl["doc_arms"] if metrics["arms"].get(a, {}).get("status") != "not run"]
matched = [d for d in meta if arms_run and all(cover.get(d, {}).get(a, {}).get("state") == "complete" for a in arms_run)]
deltas = []
for (doc, fld), a in sorted(per_case.items()):
    if "S" in a and "T2" in a and a["S"] != a["T2"]:
        routes = []
        rows = json.loads((RUNS / TAGS["T2"] / "out/rows.json").read_text(encoding="utf-8"))
        att, env = attempt(rows.get(doc), "T2")
        for pg in (env.get("pages") or {}).values():
            for fk, fe in (pg.get("fields") or {}).items():
                for o in fe.get("observations") or []:
                    if o.get("field") == fld and o.get("component") == "own":
                        srcs = [r.get("source") for r in o.get("readings") or []]
                        routes.append({"value": o.get("value"), "state": o.get("state"), "read": o.get("read"), "targeted": o.get("targeted"),
                                       "readings": srcs, "support": o.get("support"),
                                       "route": "targeted_context_read" if "blind_context" in srcs else "primary_reads (+ region support)"})
        deltas.append({"doc": doc, "field": fld, "role": roles.get(doc), "label_status": "unresolved" if doc in unresolved else "resolved",
                       "matched": doc in matched, "S": a["S"], "T2": a["T2"], "T2_route": routes,
                       "discovery_route_T2": {p: fs.get("discovery:route") for p, fs in cover.get(doc, {}).get("T2", {}).get("fields", {}).items()}})


def summarize(subset):
    out = {}
    for arm in ["A"] + arms_run:
        c = collections.defaultdict(collections.Counter)
        for (doc, fld), a in per_case.items():
            if doc in subset and arm in a:
                c[fld].update(a[arm]["evidence"])
        out[arm] = {f: dict(v) for f, v in c.items()}
    return out


# no business change
bh = {}
for arm in ["A"] + arms_run:
    db = RUNS / TAGS[arm] / "db/default.db"
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    h = {t: hashlib.sha256(json.dumps([list(r) for r in con.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest()
         for t in ("project_submittals", "project_shop_drawings", "project_actions")}
    h["project_documents_role"] = hashlib.sha256(json.dumps([list(r) for r in con.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
    con.close()
    bh[arm] = h
metrics.update({"coverage_planned": {d: {"role": roles.get(d), **cover.get(d, {})} for d in meta}, "matched_completed": matched,
                "summary_all_planned": summarize(set(meta)), "summary_matched_completed": summarize(set(matched)),
                "timing": timing, "no_business_change": {a: bh[a] == bh["A"] for a in arms_run}, "business_hashes": bh})
(OUT / "CONT-METRICS.json").write_text(json.dumps(metrics, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "CONT-DELTAS.json").write_text(json.dumps(deltas, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

# --- H-06 --------------------------------------------------------------------------------------------------------------
H = decl["sources"]
KEY = H["boq_sheet"]["doc_key"]
GEO = {6: 980.5, 23: 1795.5, 40: 2861.0, 37: 2718.5}        # verified by byte-identical crop regeneration (Review 14)
labels = [s for s in json.loads(pathlib.Path(H["h06_labels"]["file"]).read_text(encoding="utf-8"))["sheets"] if s["ep"] == "8430"][0]
truth = [dict(r, ordinal=i, **({"y": GEO[i]} if i in GEO else {})) for i, r in enumerate(labels["rows"]) if r.get("kind") == "line"]
extraction = [v for k, v in json.loads(pathlib.Path(H["boq_extraction_A"]["file"]).read_text(encoding="utf-8")).items() if k.replace("\\", "/") == KEY][0]
emitted = rc.build_emitted(extraction)
base = rc.replay_sheet([], emitted, truth, bc)
by_id = {e["id"]: e for e in emitted}
targets = []
for eid, t_ord, st in base["join"]["pairs"]:
    tr = next(t for t in truth if t["ordinal"] == t_ord)
    e = by_id[eid]
    if t_ord in GEO:
        wrong = e["accepted"] and not (bc.parts_equal(e["part_number"], tr["part_number"]) and bc.quantities_equal(e["quantity"], tr["quantity"]))
        targets.append({"emitted_id": eid, "truth_ordinal": t_ord, "join": st, "emitted": {"part": e["part_number"], "quantity": e["quantity"]},
                        "truth": {"part": tr["part_number"], "quantity": tr["quantity"]}, "kind": "wrong_accepted_target" if wrong else "control"})
h06 = {"truth_status": "r14.1 amended labels (AI source review; H-06 quantity crop-confirmed), PROVISIONAL", "contract": bc.CONTRACT_VERSION,
       "replay_core": rc.REPLAY_CORE_VERSION, "targets_evaluation_only": targets, "arms": {}}
for arm in ("BOQ-S", "BOQ-T"):
    f = RUNS / TAGS.get(arm, "-") / "out/BOQ.json"
    if arm not in TAGS or not f.exists():
        h06["arms"][arm] = {"status": "not run"}
        continue
    b = json.loads(f.read_text(encoding="utf-8"))
    res = rc.replay_sheet(b["rows"], emitted, truth, bc)
    reached = [x["emitted_id"] for x, r in zip(res["rows"], b["rows"]) if r.get("request") == "ok"]
    tg = {t["emitted_id"]: next((x["outcome"] for x in res["rows"] if x["emitted_id"] == t["emitted_id"]), "not_reached") for t in targets}
    h06["arms"][arm] = {"calls": b["calls"], "allowance": b["allowance"], "exhausted": b["exhausted"], "declared_order": b["declared_order"],
                        "outcomes": res["outcomes"], "accounting": res["accounting"], "reached": reached,
                        "not_reached": sorted({e["id"] for e in emitted} - set(reached)), "targets": tg,
                        "wrong_targets_detected": sum(1 for t in targets if t["kind"] == "wrong_accepted_target" and tg[t["emitted_id"]] == "caught_wrong_accepted"),
                        "wrong_targets_total": sum(1 for t in targets if t["kind"] == "wrong_accepted_target"),
                        "full_sheet_verified": False if set(e["id"] for e in emitted) - set(reached) else "all rows read (not a correctness claim)",
                        "rows": res["rows"]}
if all(h06["arms"].get(a, {}).get("calls") is not None for a in ("BOQ-S", "BOQ-T")):
    k = min(h06["arms"]["BOQ-S"]["calls"], h06["arms"]["BOQ-T"]["calls"])
    for arm in ("BOQ-S", "BOQ-T"):
        b = json.loads((RUNS / TAGS[arm] / "out/BOQ.json").read_text(encoding="utf-8"))
        sent = [r for r in b["rows"] if r.get("request") == "ok"][:k]
        pre = rc.replay_sheet(sent, emitted, truth, bc)
        h06["arms"][arm]["at_equal_requests"] = {"requests": k, "outcomes": pre["outcomes"],
                                                 "wrong_targets_detected": sum(1 for x in pre["rows"] if x["outcome"] == "caught_wrong_accepted"
                                                                               and x["emitted_id"] in {t["emitted_id"] for t in targets if t["kind"] == "wrong_accepted_target"})}
(OUT / "CONT-H06.json").write_text(json.dumps(h06, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
for arm, v in metrics["arms"].items():
    if v.get("status"):
        print(arm, v["status"]); continue
    e = v["evidence_layer"]
    print(arm, {f: (e[f]["recovery_counts"], f'{e[f]["precision_numerator"]}/{e[f]["precision_denominator"]}') for f in EV.FIELDS},
          "| critical resolved", len(v["critical"]["resolved"]), "| requests", v["usage"]["requests"])
print("matched", len(matched), "| deltas", len(deltas), "| business", metrics["no_business_change"])
print("H-06 targets", [(t["emitted_id"], t["kind"], t["emitted"], t["truth"]) for t in targets])
for a, v in h06["arms"].items():
    print(a, v.get("status") or (v["calls"], v["outcomes"], v["wrong_targets_detected"], "/", v["wrong_targets_total"], v.get("at_equal_requests")))
