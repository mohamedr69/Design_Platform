"""Read-only additions to a document arm's report: (7) the targeted-read effect, (9) D26 page 2 revision, (10) decision
pages D04 D16 D17 D18 D19 D22 page by page across arms, (11) the matched comparison with a base arm and the model mix.
Uses the frozen labels, the run rows and an offline interim scoring folder. No model request.
Usage: arm_extra.py <arm> <tag> <base_arm> <score_dir> [other_arm=tag ...]  ->  REPORT-<arm>-EXTRA.json"""
import collections
import json
import pathlib
import sqlite3
import sys

arm, tag, base, score = sys.argv[1], sys.argv[2], sys.argv[3], pathlib.Path(sys.argv[4])
TAGS = {arm: tag, **dict(a.split("=", 1) for a in sys.argv[5:])}
HERE = pathlib.Path(__file__).resolve().parent
D = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
LD = pathlib.Path(D["harness_dir"]) / D["labels"]["dir"]
REG = json.loads((LD / D["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((LD / D["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((LD / D["labels"]["uncertainty"]).read_text(encoding="utf-8"))
M = json.loads((score / "ARMS-METRICS.v4.json").read_text(encoding="utf-8"))
did = {x["doc"]: x["draft_id"] for x in REG["documents"]}
doc_of = {v: k for k, v in did.items()}
unc_docs = {u["doc"] for u in UNC["uncertainty"]}
conf = {x["doc"]: x["confidence"] for x in REG["documents"]}
resolved = lambda doc: conf.get(doc) == "high" and doc not in unc_docs
EV = {a: json.loads((score / f"eval-{a}.json").read_text(encoding="utf-8")) for a in M["arms"] if (score / f"eval-{a}.json").exists()}


def judged(a, doc, page, field):
    d = next((x for x in EV[a]["documents"] if x["doc"] == doc), None)
    return [j for j in ((d or {}).get("layers") or {}).get("evidence", {}).get("judged") or []
            if j.get("page") == page and j.get("field") == field and str(j.get("group", "")).endswith(":own")]


def attempt(a, doc):
    rows = json.loads((pathlib.Path("C:/t/r2x/runs") / TAGS[a] / "out/rows.json").read_text(encoding="utf-8"))
    pol = D["arms"][a]["identities"]["EVIDENCE_POLICY_VERSION"]
    r = rows.get(doc) or {}
    atts = [x for x in ((r.get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or [] if x.get("policy") == pol]
    return (atts[-1] if atts else None), r


R = {"arm": arm, "tag": tag, "base_arm": base, "scoring_dir": str(score)}

# 7. targeted reads
rows = json.loads((pathlib.Path("C:/t/r2x/runs") / tag / "out/rows.json").read_text(encoding="utf-8"))
pol = D["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]
t_calls, t_fields = [], []
for doc, r in rows.items():
    for a in [x for x in ((r.get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or [] if x.get("policy") == pol][-1:]:
        for c in a.get("calls") or []:
            if c.get("task") == "read_field_context":
                t_calls.append({"draft_id": did.get(doc), "page": c.get("page"), "reason": c.get("reason"), "outcome": c.get("outcome"), "cache_hit": c.get("cache_hit")})
        for pn, pg in (a.get("pages") or {}).items():
            fl = (pg or {}).get("fields") or {} if isinstance(pg, dict) else {}
            for f in ("identity", "revision"):
                tk = fl.get(f"own:{f}:targeted")
                if tk is None:
                    continue
                prim = fl.get(f"own:{f}:primary")
                js = judged(arm, doc, int(pn), f)
                t_fields.append({"draft_id": did.get(doc), "page": int(pn), "field": f, "label_resolved": resolved(doc), "primary": prim, "targeted": tk,
                                 "final": fl.get(f"own:{f}"), "eval": [(j.get("state"), j.get("value"), j.get("outcome")) for j in js],
                                 "completed_by_targeted": tk == "completed" and prim != "completed",
                                 "changed_nothing": tk != "completed" or prim == "completed"})
dispatched = [c for c in t_calls if not str(c["outcome"]).startswith("budget") and not c["cache_hit"]]
ev_out = collections.Counter(o for x in t_fields if x["completed_by_targeted"] for (_, _, o) in x["eval"])
R["7_targeted"] = {"targeted_calls": len(t_calls), "dispatched": len(dispatched), "refused_before_dispatch": len(t_calls) - len(dispatched) - sum(1 for c in t_calls if c["cache_hit"]),
                   "cache_hits": sum(1 for c in t_calls if c["cache_hit"]), "call_outcomes": dict(collections.Counter(str(c["outcome"])[:40] for c in t_calls)),
                   "fields_with_targeted_state": len(t_fields), "targeted_states": dict(collections.Counter(str(x["targeted"]) for x in t_fields)),
                   "fields_completed_by_targeted": sum(1 for x in t_fields if x["completed_by_targeted"]),
                   "eval_outcomes_on_fields_completed_by_targeted": dict(ev_out),
                   "eval_outcomes_on_all_targeted_fields": dict(collections.Counter(o for x in t_fields for (_, _, o) in x["eval"])),
                   "targeted_calls_that_changed_nothing": sum(1 for x in t_fields if x["changed_nothing"] and x["targeted"] not in ("not_attempted:after_failure", "not_attempted:budget")),
                   "fields": t_fields, "calls": t_calls,
                   "definitions": {"completed_by_targeted": "the targeted read completed a field whose primary read had not completed",
                                   "changed_nothing": "a targeted read ran but did not complete the field, or the primary had already completed it"}}

# 9. D26 page 2 revision
d26 = doc_of["D26"]
a26, r26 = attempt(arm, d26)
obs = [o for o in (((r26.get("extracted") or {}).get("ai_evidence") or {}).get("envelopes") or {}).get("default|EV1", {}).get("observations") or []
       if o.get("page") == 2 and o.get("field") == "revision"]
lab26 = PAGE["documents"][d26]
R["9_D26"] = {"draft_id": "D26", "label_confidence": conf.get(d26), "on_uncertainty_list": d26 in unc_docs,
              "frozen_label_page2": {"no_record_pages": lab26.get("no_record_pages"), "records_on_page2": [x for x in lab26["records"] if x["page"] == 2]},
              "emitted_page2_revision": [{k: o.get(k) for k in ("component", "role", "value", "value_literal", "state", "read", "targeted", "region", "reasons", "support")} for o in obs],
              "attempt_page2": (a26 or {}).get("pages", {}).get("2"),
              "eval_page2_revision": {a: judged(a, d26, 2, "revision") for a in EV if a != "A"},
              "labels_unchanged": "labels r26.2 bound by hash in the declaration and re-checked by the preflight; no relabelling or post-result adjudication during the run"}

# 10. decision pages
decs = []
for did_ in ("D04", "D16", "D17", "D18", "D19", "D22"):
    doc = doc_of[did_]
    for rec in [x for x in PAGE["documents"][doc]["records"] if x["page"] <= 4]:
        row = {"draft_id": did_, "page": rec["page"], "label_decision": rec.get("decision"), "location": rec.get("decision_location"), "label_resolved": resolved(doc)}
        for a in [x for x in M["coverage"]]:
            cov = next((d for d in M["coverage"][a]["documents"] if d["doc"] == doc), None)
            row[a] = {"coverage": (cov or {}).get("pages", {}).get(str(rec["page"]), {}).get("own:decision"),
                      "eval": [(j.get("state"), j.get("value"), j.get("outcome")) for j in judged(a, doc, rec["page"], "decision")]}
        decs.append(row)
R["10_decisions"] = decs

# 11. matched comparison and model mix
pair = next((v for v in M["pairs"].values() if v["arms"] == [base, arm]), None)


def rec(a, doc, fld):
    d = next((x for x in EV[a]["documents"] if x["doc"] == doc), None)
    return dict(((d or {}).get("layers") or {}).get("evidence", {}).get("recovery", {}).get(fld, {})) if d else None


matched = {}
if pair:
    for f, docs in pair["field_read_in_both"].items():
        fld = f.split(":")[1]
        rs = [{"draft_id": did.get(doc), "label_resolved": resolved(doc), base: rec(base, doc, fld), arm: rec(arm, doc, fld)} for doc in docs]
        matched[f] = {"n": len(rs), "rows": rs, "differences": [x for x in rs if x[base] != x[arm]]}
attempted = lambda a: {d["doc"] for d in M["coverage"][a]["documents"] if d.get("attempted") and d["state"] != "unsupported_input"
                       and any(c not in ("not_attempted", "budget") for pc in d["pages"].values() for c in pc.values() if not c.startswith("unsupported"))}
both = attempted(base) & attempted(arm)
lc = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
models = {a: dict(lc.execute("select coalesce(model,'?') || ' / ' || outcome, count(*) from entries where scope = ? group by 1", (D["ledger"]["scopes"][a]["scope"],)).fetchall())
          for a in D["doc_arms"]}
lc.close()
R["11_matched"] = {"pair": pair and pair["arms"], "valid": pair and pair["valid"], "fields": matched, "required_complete_in_both": pair and pair["required_complete_in_both"],
                   "documents_with_some_read_in_both": len(both), "minimum_for_a_conclusive_pair": 12,
                   "conclusive": len(both) >= 12 and all(v["n"] >= 12 for v in matched.values()),
                   "models_by_scope": models}
(HERE / f"REPORT-{arm}-EXTRA.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in R.items() if k != "7_targeted"}, indent=1, default=str, ensure_ascii=False)[:20000])
print(json.dumps({k: v for k, v in R["7_targeted"].items() if k not in ("fields", "calls")}, indent=1, default=str))
