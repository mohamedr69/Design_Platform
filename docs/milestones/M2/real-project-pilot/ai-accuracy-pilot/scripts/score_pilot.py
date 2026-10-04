"""AI accuracy pilot: matched scoring of A / S / G / T (documents) and BOQ-S / BOQ-T, written and dry-tested before any
real request. Documents: the accepted evaluator .9 (scripts.m2_eval5, frozen-r12, unchanged) under each arm's declared
context against the PROVISIONAL pilot labels; BOQ: the accepted r16.1 replay_core + boq_contract (unchanged).

Outputs (in --out): eval-<arm>.json (the evaluator's own output), PILOT-METRICS.json (per arm / field / project / stratum /
label status, coverage, usage), PILOT-DELTAS.json (per-case S->G and G->T changes, T gains attributed by route),
PILOT-BOQ-RESULTS.json.

Usage: score_pilot.py --declaration D --declaration-sha SHA --runs ROOT --tags A=..,S=..,G=..,T=..,BOQ-S=..,BOQ-T=.. --out DIR"""
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
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
P = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
RUNS = pathlib.Path(args.runs)
TAGS = dict(kv.split("=", 1) for kv in args.tags.split(","))
OUT = pathlib.Path(args.out)
OUT.mkdir(parents=True, exist_ok=True)
for n, h in decl["labels"]["files"].items():
    assert hashlib.sha256((P / "labels" / n).read_bytes()).hexdigest() == h, n
os.environ.setdefault("AI_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/score-no-db.db")
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED"):
    os.environ.pop(k, None)
ACC = pathlib.Path(decl["code"]["accepted_app"]["tree"])
sys.path.insert(0, str(ACC / "backend")); os.chdir(ACC / "backend")
from scripts import m2_eval5 as EV  # noqa: E402

assert hashlib.sha256(pathlib.Path(EV.__file__).read_bytes()).hexdigest() == decl["code"]["evaluator"]["sha256"]
sys.path.insert(0, "C:/t/iso/work/r2x/r16")
import boq_contract as bc  # noqa: E402
import replay_core as rc  # noqa: E402

for f, h in decl["code"]["boq_harness_r16"].items():
    assert hashlib.sha256((pathlib.Path("C:/t/iso/work/r2x/r16") / f).read_bytes()).hexdigest() == h, f

REG = json.loads((P / "labels/PILOT-REGISTER-LABELS.json").read_text(encoding="utf-8"))
PAGE = json.loads((P / "labels/PILOT-PAGE-LABELS.json").read_text(encoding="utf-8"))
UNC = json.loads((P / "labels/PILOT-UNCERTAINTY-AND-EXPOSURE.json").read_text(encoding="utf-8"))
unresolved = {u["doc"] for u in UNC["uncertainty"]} | {d["doc"] for d in REG["documents"] if d.get("confidence") != "high"}
meta = {d["doc"]: d for d in REG["documents"]}
FIELDS = EV.FIELDS
TRUTH = "PROVISIONAL: AI-drafted labels, not reviewed by a person; diagnostic only"
CTX = {"A": {"variant": None, "declared": "A base: no AI evidence stage"}}
for arm in ("S", "G", "T"):
    CTX[arm] = {"variant": "EV1", "profile": "default", "policies": [decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]], "declared": f"pilot arm {arm}"}


def add(c: collections.Counter, d: dict):
    c.update({k: v for k, v in (d or {}).items() if isinstance(v, int)})


def rates(prec: collections.Counter, rec: collections.Counter) -> dict:
    return EV.layer_rates(prec, rec)


def envelope_attempt(row: dict, arm: str):
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    atts = [a for a in ai.get("attempts") or [] if a.get("key") == "default|EV1" and a.get("policy") == (CTX.get(arm, {}).get("policies") or [None])[0]]
    env = (ai.get("envelopes") or {}).get("default|EV1") or {}
    return (atts[-1] if atts else None), env


def coverage(rows: dict, arm: str) -> dict:
    per_field = collections.defaultdict(collections.Counter)
    docs = collections.Counter()
    requests = collections.Counter()
    for doc in meta:
        row = rows.get(doc)
        if row is None:
            docs["missing_row"] += 1
            continue
        att, _ = envelope_attempt(row, arm)
        if att is None:
            docs["no_attempt (not selected by policy / not attempted)"] += 1
            continue
        docs[f"attempt:{att.get('outcome')}"] += 1
        for pno, pg in (att.get("pages") or {}).items():
            for f, st in (pg.get("fields") or {}).items():
                per_field[f][str(st).split(":")[0] if not str(st).startswith(("unusable", "incomplete")) else str(st)] += 1
            for r, st in (pg.get("requests") or {}).items():
                requests[f"{r.split(':', 1)[-1] if r.endswith(':targeted') else 'read'}|{str(st).split(':')[0]}"] += 1
    return {"documents": dict(docs), "page_fields": {f: dict(c) for f, c in per_field.items()}, "requests_by_outcome": dict(requests)}


def usage_of(tag: str, prefix: str | None) -> dict:
    u = json.loads((RUNS / tag / "out/usage.json").read_text(encoding="utf-8"))
    fresh = [x for x in u if not x["cache_hit"] and (prefix is None or str(x["task"]).startswith(prefix))]
    lat = [x["latency_ms"] for x in fresh if x.get("latency_ms")]
    return {"fresh_requests": len(fresh), "cache_hits": sum(1 for x in u if x["cache_hit"]),
            "by_task": dict(collections.Counter(x["task"] for x in fresh)), "outcomes": dict(collections.Counter(x["outcome"] for x in fresh)),
            "models": dict(collections.Counter(x["model"] for x in fresh)),
            "input_tokens": sum(x["input_tokens"] or 0 for x in fresh), "output_tokens": sum(x["output_tokens"] or 0 for x in fresh),
            "requests_without_token_usage": sum(1 for x in fresh if x["input_tokens"] is None),
            "latency_ms": {"p50": statistics.median(lat) if lat else None, "max": max(lat) if lat else None},
            "cost": "UNKNOWN (no valid price configured; never zero)"}


metrics = {"truth_status": TRUTH, "declaration_sha256": args.declaration_sha, "evaluator": EV.EVALUATOR_VERSION, "tags": TAGS,
           "unresolved_labels": sorted(unresolved), "arms": {}}
per_case = {}
for arm in ("A", "S", "G", "T"):
    if arm not in TAGS or not (RUNS / TAGS[arm] / "out/rows.json").exists():
        metrics["arms"][arm] = {"status": "not run"}
        continue
    rows = json.loads((RUNS / TAGS[arm] / "out/rows.json").read_text(encoding="utf-8"))
    run = json.loads((RUNS / TAGS[arm] / "out/RUN.json").read_text(encoding="utf-8"))
    ev = EV.evaluate(REG, PAGE, rows, PAGE.get("page1_corrections"), ai_context=CTX[arm])
    (OUT / f"eval-{arm}.json").write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    t = ev["totals"]
    groups = {"all": set(meta), "resolved": set(meta) - unresolved, "unresolved": unresolved & set(meta)}
    by = collections.defaultdict(lambda: collections.defaultdict(lambda: {"precision": collections.Counter(), "recovery": collections.Counter()}))
    for d in ev["documents"]:
        doc = d["doc"]
        m = meta[doc]
        L = d["layers"]["evidence"]
        keys = [("project", m["ep"]), ("stratum", m["stratum"]), ("label_status", "unresolved" if doc in unresolved else "resolved")]
        for f in FIELDS:
            for dim, val in keys:
                add(by[f"{dim}={val}"][f]["precision"], L["precision"].get(f))
                add(by[f"{dim}={val}"][f]["recovery"], L["recovery"].get(f))
            per_case.setdefault((doc, f), {})[arm] = {"recovery": {k: v for k, v in (L["recovery"].get(f) or {}).items() if v},
                                                      "precision": {k: v for k, v in (L["precision"].get(f) or {}).items() if v}}
    crit = t["evidence"]["critical"]
    metrics["arms"][arm] = {
        "tag": TAGS[arm], "context": CTX[arm], "ai_evidence_states": t.get("ai_evidence_states"),
        "evidence_layer": t["evidence"]["fields"], "ai_layer": t["ai"]["fields"], "raw_layer": t["raw"]["fields"],
        "raw_observation_precision_by_state": t["raw"].get("precision_by_state"),
        "evidence_precision_by_state": t["evidence"].get("precision_by_state"),
        "critical": {"all": crit, "resolved": [c for c in crit if c["doc"] not in unresolved], "unresolved_label": [c for c in crit if c["doc"] in unresolved]},
        "introduced_ai_errors": t["introduced_ai_errors"],
        "breakdowns": {k: {f: rates(v["precision"], v["recovery"]) for f, v in fs.items()} for k, fs in sorted(by.items())},
        "coverage": coverage(rows, arm) if arm != "A" else None,
        "usage": usage_of(TAGS[arm], None if arm == "A" else "evidence:"),
        "runner": {k: run.get(k) for k in ("runner_state", "not_attempted", "tripwire", "seconds", "projects", "business_hashes", "tables", "fresh_requests", "fresh_by_project")}}

# per-case deltas, and T route attribution
deltas = {"S->G": [], "G->T": [], "A->S": []}
T_rows = json.loads((RUNS / TAGS["T"] / "out/rows.json").read_text(encoding="utf-8")) if "T" in TAGS and (RUNS / TAGS["T"] / "out/rows.json").exists() else {}


def route(doc: str, field: str) -> list:
    _, env = envelope_attempt(T_rows.get(doc), "T")
    out = []
    for o in env.get("observations") or []:
        if o.get("field") != field:
            continue
        srcs = [r.get("source") for r in o.get("readings") or []]
        sup = o.get("support")
        out.append({"value": o.get("value"), "state": o.get("state"), "page": o.get("page"), "readings": srcs,
                    "support": sup, "route": ("targeted_context_read" if "blind_context" in srcs else
                                              "region_support_local_ocr" if (sup and "ocr_local" in json.dumps(sup)) else "region_support_or_unchanged"),
                    "guard": o.get("guard")})
    return out


for (doc, f), arms in sorted(per_case.items()):
    for a, b in (("A", "S"), ("S", "G"), ("G", "T")):
        if a in arms and b in arms and arms[a] != arms[b]:
            item = {"doc": doc, "field": f, "ep": meta[doc]["ep"], "stratum": meta[doc]["stratum"], "label_status": "unresolved" if doc in unresolved else "resolved",
                    a: arms[a], b: arms[b]}
            if b == "T":
                item["T_route"] = route(doc, f)
            deltas[f"{a}->{b}"].append(item)

# no business change: every arm's business tables equal A's
con = sqlite3.connect(f"file:{(RUNS / TAGS['A'] / 'db/default.db').as_posix()}?mode=ro", uri=True)
a_business = {t: hashlib.sha256(json.dumps([list(r) for r in con.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest()
              for t in ("project_submittals", "project_shop_drawings", "project_actions")}
a_business["project_documents_role"] = hashlib.sha256(json.dumps([list(r) for r in con.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
con.close()
metrics["no_business_change"] = {"A": a_business, **{arm: {"equal_to_A": (metrics["arms"][arm].get("runner") or {}).get("business_hashes") == a_business}
                                                     for arm in ("S", "G", "T") if metrics["arms"].get(arm, {}).get("runner")}}
(OUT / "PILOT-METRICS.json").write_text(json.dumps(metrics, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "PILOT-DELTAS.json").write_text(json.dumps(deltas, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

# BOQ
boq_labels = json.loads((P / "labels/PILOT-BOQ-LABELS.json").read_text(encoding="utf-8"))["sheets"][0]
truth = [dict(r, ordinal=i) for i, r in enumerate(boq_labels["rows"]) if r.get("kind") == "line"]
extraction = json.loads((P / decl["sources"]["boq_extraction_A"]["file"]).read_text(encoding="utf-8"))[decl["sources"]["boq_sheet"]["doc_key"]]
emitted = rc.build_emitted(extraction)
boq = {"truth_status": TRUTH, "contract": bc.CONTRACT_VERSION, "replay_core": rc.REPLAY_CORE_VERSION, "truth_rows": len(truth),
       "part_only_rows_not_in_replay_truth": [r for r in boq_labels["rows"] if r.get("kind") != "line"], "emitted": len(emitted),
       "reader_without_ai": rc.replay_sheet([], emitted, truth, bc)["accounting"], "arms": {}}
for arm in ("BOQ-S", "BOQ-T"):
    f = RUNS / TAGS.get(arm, "-") / "out/BOQ.json"
    if arm not in TAGS or not f.exists():
        boq["arms"][arm] = {"status": "not run"}
        continue
    b = json.loads(f.read_text(encoding="utf-8"))
    res = rc.replay_sheet(b["rows"], emitted, truth, bc)
    reached = {x["emitted_id"] for x, r in zip(res["rows"], b["rows"]) if r.get("request") == "ok"}
    entry = {"tag": TAGS[arm], "calls": b["calls"], "allowance": b["allowance"], "exhausted": b["exhausted"], "declared_order": b["declared_order"],
             "outcomes": res["outcomes"], "accounting": res["accounting"],
             "rows": [dict(x, request=r.get("request"), queue=r.get("queue"), row_state=r.get("state"), part_state=r.get("part"), quantity_state=r.get("quantity"),
                           quantity_source=r.get("quantity_source"), reasons=r.get("reasons")) for x, r in zip(res["rows"], b["rows"])],
             "verified_emitted_rows": sorted(reached), "not_reached_emitted_rows": sorted({e["id"] for e in emitted} - reached),
             "full_sheet_verified": False if ({e["id"] for e in emitted} - reached) else "all rows read (not a correctness claim)",
             "usage": usage_of(TAGS[arm], "evidence:")}
    if arm == "BOQ-T" and "BOQ-S" in boq["arms"] and boq["arms"]["BOQ-S"].get("calls") is not None:
        k = boq["arms"]["BOQ-S"]["calls"]
        pre = rc.replay_sheet(b["rows"][:k], emitted, truth, bc)
        entry["prefix_at_BOQ_S_calls"] = {"requests": k, "outcomes": pre["outcomes"]}
    boq["arms"][arm] = entry
(OUT / "PILOT-BOQ-RESULTS.json").write_text(json.dumps(boq, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")

for arm, v in metrics["arms"].items():
    if v.get("status"):
        print(arm, v["status"])
        continue
    e = v["evidence_layer"]
    print(arm, {f: (e[f]["recovery_counts"], e[f]["accepted_precision"]) for f in FIELDS}, "| critical", len(v["critical"]["all"]),
          "resolved", len(v["critical"]["resolved"]), "| requests", v["usage"]["fresh_requests"])
print("deltas", {k: len(v) for k, v in deltas.items()}, "| business", {k: v for k, v in metrics["no_business_change"].items() if k != "A"})
for arm, v in boq["arms"].items():
    print(arm, v.get("status") or (v["calls"], v["outcomes"], "not reached", len(v["not_reached_emitted_rows"])))
