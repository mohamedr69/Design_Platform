"""Dump a sandbox run's stored rows and AI usage from its database (read only), for a run stopped before its own dump.
Usage: dump_run.py <tag> <profile>"""
import json, pathlib, sqlite3, sys
tag, profile = sys.argv[1], sys.argv[2]
ROOT = pathlib.Path("C:/t/r6") / tag
DB = ROOT / "db" / f"{profile}.db"
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True); con.row_factory = sqlite3.Row
rows = {}
for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted from project_documents d join projects p on p.id = d.project_id"):
    rows[f"EP-{r['ep_number']}/{r['relative_path']}"] = {"id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
                                                         "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
                                                         "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
usage = [dict(u) for u in con.execute("select project_id, task, model, input_tokens, output_tokens, cached_input_tokens, estimated_cost, latency_ms, cache_hit, escalated, outcome, at from ai_usage order by id")]
con.close()
(ROOT / "out").mkdir(exist_ok=True)
json.dump(rows, open(ROOT / "out" / f"rows-{profile}.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(ROOT / "out" / f"usage-{profile}.json", "w", encoding="utf-8"), indent=1, default=str)
print(len(rows), "rows;", len(usage), "usage;", sum(1 for r in rows.values() if (r.get("extracted") or {}).get("ai_evidence")), "rows with ai_evidence")
