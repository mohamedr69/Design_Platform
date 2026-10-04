"""Score the matched run (frozen c9a1a14 application, the same 12 source hashes, default profile) with evaluator .6:
the model-disabled baseline (det9 on those 12 documents), AI-EV0, AI-EV1, AI-EV2 -- per field, per project; and the
ledger's usage per track."""
import collections
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
from scripts import m2_eval5 as ev  # noqa: E402

P = Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot")
decl = json.load(open(r"C:\t\iso\work\r7\matched\MATCHED-DECLARATION.json", encoding="utf-8"))
docs = {d.replace("\\", "/") for d in decl["selection"]["files_sha256"]}
gold = json.load(open(P / "GOLDEN-LABELS.json", encoding="utf-8"))
pages = json.load(open(P / "review05" / "labels" / "GOLDEN-LABELS-v2-PAGES.json", encoding="utf-8"))
labels = {**gold, "documents": [d for d in gold["documents"] if d["doc"].replace("\\", "/") in docs]}
plabels = {**pages, "documents": {k: v for k, v in pages["documents"].items() if k.replace("\\", "/") in docs}}
assert len(labels["documents"]) == 12, len(labels["documents"])

RUNS = {"model-disabled (det9)": r"C:\t\r6\det9-pilot\out\rows-default.json", "AI-EV0": r"C:\t\r7\m-ev0\out\rows-default.json",
        "AI-EV1": r"C:\t\r7\m-ev1\out\rows-default.json", "AI-EV2": r"C:\t\r7\m-ev2\out\rows-default.json"}
out = {"evaluator": ev.EVALUATOR_VERSION, "documents": sorted(docs), "runs": {}}
for name, path in RUNS.items():
    if not Path(path).exists():
        out["runs"][name] = {"not_run": path}
        continue
    rows = {k: v for k, v in json.load(open(path, encoding="utf-8")).items() if k.replace("\\", "/") in docs}
    r = ev.evaluate(labels, plabels, rows, plabels.get("page1_corrections"))
    t = r["totals"]
    per_project = {}
    for d in r["documents"]:
        pc = per_project.setdefault(d["ep"], collections.Counter())
        for comp in d["layers"]["evidence"]["components"]:
            for f, s in comp["fields"].items():
                pc[f"{f}:{s}"] += 1
    ai_pages = collections.Counter()
    for k, row in rows.items():
        env = ev.ai_envelope(row)
        for pg in (env.get("pages") or {}).values():
            ai_pages[str((pg.get("coverage") or {}).get("outcome"))] += 1
        ai = ((row.get("extracted") or {}).get("ai_evidence") or {})
        for a in ai.get("attempts") or []:
            for o in (a.get("pages") or {}).values():
                ai_pages["attempt:" + str(o)] += 1
    mirror = {k: (v.get("mirror") or {}) for k, v in rows.items()}
    out["runs"][name] = {"register_critical": [c["kind"] for c in t["register"]["critical"]],
                         "register": {f: {k: t["register"]["register"].get(f, {}).get(k) for k in ("tp", "accepted", "readable")} for f in ("reference", "revision", "decision")},
                         "evidence": {f: {k: t["evidence"]["fields"][f][k] for k in ("recovery", "clean_recovery", "accepted_precision", "readable", "recovery_counts", "precision_counts")} for f in ev.FIELDS},
                         "raw": {f: {k: t["raw"]["fields"][f][k] for k in ("recovery", "accepted_precision", "readable")} for f in ev.FIELDS},
                         "evidence_critical": t["evidence"]["critical"], "introduced_ai_errors": t["introduced_ai_errors"],
                         "observed_errors": len(t["raw"]["observed_errors"]), "per_project": {k: dict(v) for k, v in per_project.items()},
                         "ai_page_outcomes": dict(ai_pages), "mirror": mirror}
    json.dump(r, open(rf"C:\t\iso\work\r7\matched\eval6-{name.split()[0]}.json", "w", encoding="utf-8"), indent=1, default=str)
base = out["runs"].get("AI-EV0", {}).get("mirror")
for name in ("AI-EV1", "AI-EV2"):
    if base is not None and "mirror" in out["runs"].get(name, {}):
        out["runs"][name]["mirror_identical_to_ev0"] = out["runs"][name]["mirror"] == base
for v in out["runs"].values():
    v.pop("mirror", None)
# ledger usage per track (by entry order: EV0 first, then EV1, then EV2 -- tracks ran one after another)
con = sqlite3.connect(r"file:C:/t/r7/ledger/matched.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
entries = [dict(e) for e in con.execute("select * from entries order by id")]
out["ledger"] = {"breaker": con.execute("select breaker from scopes").fetchone()[0],
                 "totals": {"requests": sum(1 for e in entries if e["state"] == "settled"), "refused": sum(1 for e in entries if e["state"] == "refused"),
                            "cache_hits": sum(1 for e in entries if e["state"] == "cache_hit"), "input": sum(e["act_in"] or 0 for e in entries),
                            "output": sum(e["act_out"] or 0 for e in entries), "estimated_input": sum(e["est_in"] or 0 for e in entries if e["state"] == "settled"),
                            "usage_unknown": sum(e["usage_unknown"] or 0 for e in entries),
                            "under_estimated": sum(1 for e in entries if e["state"] == "settled" and (e["act_in"] or 0) > (e["est_in"] or 0)),
                            "latency_s": round(sum(e["latency_ms"] or 0 for e in entries) / 1000),
                            "models": dict(collections.Counter(e["model"] for e in entries if e["state"] == "settled")),
                            "outcomes": dict(collections.Counter(e["outcome"] for e in entries if e["state"] in ("settled", "refused")))}}
json.dump(out, open(r"C:\t\iso\work\r7\matched\MATCHED-RESULTS.json", "w", encoding="utf-8"), indent=1, default=str)
for name, v in out["runs"].items():
    if "not_run" in v:
        print(name, "NOT RUN"); continue
    e = v["evidence"]
    print(f"{name:24s} reg-crit {len(v['register_critical'])} evid-crit {len(v['evidence_critical'])} introduced {len(v['introduced_ai_errors'])} | "
          + " | ".join(f"{f} {e[f]['recovery']}/{e[f]['accepted_precision']} (n={e[f]['readable']})" for f in ev.FIELDS), "| pages", v["ai_page_outcomes"], v.get("mirror_identical_to_ev0"))
print(json.dumps(out["ledger"], indent=1))
