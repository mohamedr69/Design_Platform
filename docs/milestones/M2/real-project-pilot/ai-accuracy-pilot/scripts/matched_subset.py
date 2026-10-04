"""AI accuracy pilot, post-run analysis (written after the runs; adds no new metric definition -- it re-reads the frozen
evaluator's per-document output): (1) matched-arm coverage -- per document and arm, whether the arm's evidence attempt
completed or which limit stopped it (elapsed job budget, ledger token breaker, provider timeout, not selected); (2) the
S / G / T comparison restricted to documents every compared arm actually processed (the declared 'record matched-arm
coverage separately if one arm exhausts its cap'); (3) the ledger / cross-track usage reconciliation.
Writes results/PILOT-MATCHED.json."""
import collections
import json
import pathlib
import sqlite3

P = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
R = P / "results"
RUNS = pathlib.Path("C:/t/r2x/runs")
TAGS = {"A": "ai-pilot-A", "S": "ai-pilot-S", "G": "ai-pilot-G", "T": "ai-pilot-T"}
decl = json.loads((P / "PILOT-DECLARATION.json").read_text(encoding="utf-8"))
REG = json.loads((P / "labels/PILOT-REGISTER-LABELS.json").read_text(encoding="utf-8"))
docs = [d["doc"] for d in REG["documents"]]
UNC = {u["doc"]: u["item"] for u in json.loads((P / "labels/PILOT-UNCERTAINTY-AND-EXPOSURE.json").read_text(encoding="utf-8"))["uncertainty"]}
conf = {d["doc"]: d.get("confidence") for d in REG["documents"]}


def stop_cause(text: str) -> str:
    t = str(text or "")
    if "breaker" in t:
        return "ledger token breaker (scope closed)"
    if "elapsed" in t:
        return "per-document elapsed budget (120 s)"
    if "timeout" in t:
        return "provider timeout (300 s)"
    if t.startswith("budget"):
        return "budget: " + t.split(":", 1)[-1].strip()[:60]
    return t


coverage = {}
for arm in ("S", "G", "T"):
    rows = json.loads((RUNS / TAGS[arm] / "out/rows.json").read_text(encoding="utf-8"))
    pol = decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]
    for doc in docs:
        ai = ((rows.get(doc) or {}).get("extracted") or {}).get("ai_evidence") or {}
        atts = [a for a in ai.get("attempts") or [] if a.get("policy") == pol]
        if not atts:
            coverage.setdefault(doc, {})[arm] = {"state": "not selected by EV1 triggers (no request)", "requests": 0}
            continue
        a = atts[-1]
        calls = a.get("calls") or []
        sent = [c for c in calls if not c.get("cache_hit") and not str(c.get("outcome", "")).startswith("budget")]
        stops = sorted({stop_cause(c.get("outcome")) for c in calls if str(c.get("outcome", "")).startswith("budget") or c.get("outcome") == "timeout"})
        own = {}
        for pno, pg in (a.get("pages") or {}).items():
            for f in ("own:identity", "own:revision", "own:decision"):
                own[f"p{pno}:{f}"] = (pg.get("fields") or {}).get(f)
        coverage.setdefault(doc, {})[arm] = {"state": "complete" if not stops else "stopped", "stops": stops, "requests": len(sent),
                              "tasks": [c["task"] for c in sent], "own_fields": own}

ev = {arm: {d["doc"]: d for d in json.loads((R / f"eval-{arm}.json").read_text(encoding="utf-8"))["documents"]} for arm in ("A", "S", "G", "T")}


def outcome(arm, doc, f, layer="evidence"):
    L = ev[arm][doc]["layers"][layer]
    return {k: v for k, v in (L["recovery"].get(f) or {}).items() if v}


matched = [d for d in docs if all(coverage[d][a]["state"] == "complete" for a in ("S", "G", "T"))]
t_complete = [d for d in docs if coverage[d]["T"]["state"] == "complete"]
table = []
for d in docs:
    for f in ("identity", "revision", "decision"):
        table.append({"doc": d, "field": f, "label_confidence": conf[d], "uncertainty": UNC.get(d), "matched_all_arms": d in matched,
                      **{arm: outcome(arm, d, f) for arm in ("A", "S", "G", "T")},
                      **{f"{arm}_ai_layer": outcome(arm, d, f, "ai") for arm in ("S", "G", "T")}})


def summarize(subset):
    out = {}
    for arm in ("A", "S", "G", "T"):
        c = collections.defaultdict(collections.Counter)
        for row in table:
            if row["doc"] in subset:
                c[row["field"]].update(row[arm])
        out[arm] = {f: dict(v) for f, v in c.items()}
    return out


con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
ledger = {}
entries = []
for s in decl["ledger"]["scopes"].values():
    rows = [dict(r) for r in con.execute("select * from entries where scope = ? order by id", (s["scope"],))]
    entries += rows
    sc = con.execute("select limits, breaker from scopes where scope = ?", (s["scope"],)).fetchone()
    ledger[s["scope"]] = {"cap": s["limits"]["requests"], "settled": sum(1 for r in rows if r["state"] == "settled"),
                          "refused": sum(1 for r in rows if r["state"] == "refused"), "other": sum(1 for r in rows if r["state"] not in ("settled", "refused")),
                          "usage_unknown": sum(1 for r in rows if r["usage_unknown"]), "act_in": sum(r["act_in"] or 0 for r in rows if r["state"] == "settled"),
                          "act_out": sum(r["act_out"] or 0 for r in rows if r["state"] == "settled"), "breaker": sc["breaker"] if sc else None,
                          "models": dict(collections.Counter(r["model"] for r in rows if r["state"] == "settled"))}
earlier = con.execute("select count(*) from entries where scope = 'r2x-small-2026-09-29'").fetchone()[0]
con.close()
x = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
xt = [dict(zip(("ep", "track", "n"), r)) for r in x.execute("select ep, track, count(*) from calls where track like 'pilot-%' group by ep, track order by ep, track")]
x.close()
total_settled = sum(v["settled"] for v in ledger.values())
out = {"note": "post-run analysis over the frozen evaluator's output; no metric redefined",
       "coverage": coverage, "matched_all_arms_documents": matched, "T_complete_documents": t_complete,
       "summary_all_documents": summarize(set(docs)), "summary_matched_S_G_T": summarize(set(matched)),
       "summary_T_complete": summarize(set(t_complete)), "per_case": table,
       "ledger": ledger, "ledger_total_settled_requests": total_settled, "ledger_total_cap": 150,
       "earlier_scope_r2x_small_entries_unchanged": earlier, "cross_track_pilot_rows": xt, "ledger_entries": entries}
(R / "PILOT-MATCHED.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
print("matched S/G/T:", len(matched), [m.split("/")[-1][:40] for m in matched])
print("T complete:", len(t_complete))
print("matched summary", json.dumps(out["summary_matched_S_G_T"]))
print("ledger", {k: (v["cap"], v["settled"], v["refused"], v["usage_unknown"], v["breaker"]) for k, v in ledger.items()}, "total settled", total_settled, "earlier", earlier)
for d in docs:
    print(d.split("/")[0], d.split("/")[-1][:38], {a: (coverage[d][a]["state"], coverage[d][a].get("stops"), coverage[d][a]["requests"]) for a in ("S", "G", "T")})
