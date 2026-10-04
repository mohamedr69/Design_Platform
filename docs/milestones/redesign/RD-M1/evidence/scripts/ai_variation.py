"""AI variation from stored data only (no model calls): the result_cache answers of
fa_drawing_redesign grouped by change, compared with the answer stored on each change."""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from q import run  # noqa: E402

HERE = os.path.dirname(__file__)
row = json.load(open(os.path.join(HERE, "..", "work", "case", "project_redesign.json"), encoding="utf-8"))[0]
by_id = {c["id"]: c for c in row["changes"]}
rows = run("SELECT key, document_sha256, task, value, hits, created_at, last_hit_at FROM result_cache "
           "WHERE task='fa_drawing_redesign' ORDER BY created_at")
groups = defaultdict(list)
for r in rows:
    v = json.loads(r["value"]) if isinstance(r["value"], str) else r["value"]
    cid = r["document_sha256"].split(":", 1)[1] if ":" in r["document_sha256"] else r["document_sha256"]
    groups[cid].append({"created_at": r["created_at"], "hits": r["hits"], "value": v})


def core(v):
    d = v.get("data", v) if isinstance(v, dict) else v
    if not isinstance(d, dict):
        return d
    return {k: d.get(k) for k in ("candidate", "symbol", "x", "y", "facing", "confidence")}


report = {"cache_rows": len(rows), "changes_with_cache": len(groups), "multi_answer_changes": {}, "single": 0,
          "stored_vs_cache": {"match": 0, "differs": 0, "no_cache": 0}}
for cid, answers in groups.items():
    cores = [core(a["value"]) for a in answers]
    if len(answers) > 1:
        report["multi_answer_changes"][cid] = {
            "n": len(answers), "identical": all(c == cores[0] for c in cores),
            "answers": [{"created_at": a["created_at"], "hits": a["hits"], **(core(a["value"]) or {})} for a in answers],
            "status_now": by_id.get(cid, {}).get("status"), "device": by_id.get(cid, {}).get("device")}
    else:
        report["single"] += 1
for cid, c in by_id.items():
    if c.get("source") == "interface":
        continue
    ai = c.get("ai") or {}
    if cid not in groups:
        report["stored_vs_cache"]["no_cache"] += 1
        continue
    last = core(groups[cid][-1]["value"]) or {}
    same = all((last.get(k) == ai.get(k)) or (k in ("x", "y") and last.get(k) is not None and ai.get(k) is not None
                                               and abs(float(last[k]) - float(ai[k])) < 1e-9)
               for k in ("candidate", "symbol", "confidence"))
    report["stored_vs_cache"]["match" if same else "differs"] += 1
print(json.dumps({k: v for k, v in report.items() if k != "multi_answer_changes"}, indent=1))
print("multi:", len(report["multi_answer_changes"]))
for cid, m in list(report["multi_answer_changes"].items())[:12]:
    print(cid[:60], m["n"], "identical" if m["identical"] else "DIFFER", m["status_now"], m["device"])
    for a in m["answers"]:
        print("    ", a)
json.dump(report, open(os.path.join(HERE, "..", "work", "ai-variation.json"), "w"), indent=1, default=str)
if rows:
    print("sample value keys:", list((json.loads(rows[0]["value"]) if isinstance(rows[0]["value"], str) else rows[0]["value"]).keys()))
