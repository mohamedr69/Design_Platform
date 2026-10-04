"""Read-only per-arm report: the runner's RUN.json, the ledger scope totals, the rolling counter, the terminal-stop file and
the next eligible resume time of every deferred project (when the oldest calls in its 24 h window expire far enough that the
project's worst case fits). Appends to RUN-LOG.jsonl and writes REPORT-<arm>-<n>.json. Usage: arm_report.py <arm> <tag>"""
import datetime
import json
import pathlib
import sqlite3
import sys
import time

arm, tag = sys.argv[1], sys.argv[2]
HERE = pathlib.Path(__file__).resolve().parent
d = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
OUT = pathlib.Path("C:/t/r2x/runs") / tag / "out"
run = json.loads((OUT / "RUN.json").read_text(encoding="utf-8")) if (OUT / "RUN.json").exists() else {}
stop = json.loads((OUT / "TERMINAL-STOP.json").read_text(encoding="utf-8")) if (OUT / "TERMINAL-STOP.json").exists() else None
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat(timespec="seconds") if t else None
now = time.time()
scope = d["ledger"]["scopes"][arm]["scope"]
lc = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
srow = lc.execute("select limits, created_at, breaker from scopes where scope = ?", (scope,)).fetchone()
states = dict(lc.execute("select state, count(*) from entries where scope = ? group by state", (scope,)).fetchall())
t = lc.execute("select count(*), coalesce(sum(est_in),0), coalesce(sum(est_out),0), coalesce(sum(act_in),0), coalesce(sum(act_out),0), "
               "coalesce(sum(cached_in),0), sum(usage_unknown), max(act_in), max(act_out) from entries where scope = ?", (scope,)).fetchone()
models = dict(lc.execute("select coalesce(model,'?'), count(*) from entries where scope = ? group by model", (scope,)).fetchall())
lc.close()
pc = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
eps = sorted(d["authorization"]["projects_resolved"])
used = {ep: pc.execute("select count(*) from calls where ep = ? and at >= ?", (ep, now - 86400)).fetchone()[0] for ep in eps}
deferred = []
for rec in run.get("deferred", []):
    ep, need = str(rec["ep"]), rec["needed_worst_case"]
    ats = [a for (a,) in pc.execute("select at from calls where ep = ? and at >= ? order by at", (ep, now - 86400))]
    k = len(ats) - (60 - need)                      # calls that must leave the window
    eligible = now if k <= 0 else (ats[k - 1] + 86400 if need <= 60 else None)
    deferred.append({"ep": ep, "needed_worst_case": need, "capacity_now": max(0, 60 - len(ats)), "next_eligible_utc": iso(eligible) if eligible else "never (worst case exceeds 60)"})
pc.close()
cap = d["ledger"]["caps"][arm]
crit = [x for x in run.get("tripwire", []) if x.get("critical_on_resolved")]
rep = {"utc": iso(now), "arm": arm, "tag": tag, "status": run.get("status"), "scope": scope,
       "requests_sent_ledger": t[0], "requests_remaining": cap - t[0], "cap": cap, "states": states, "models": models,
       "tokens": {"estimated_in": t[1], "estimated_out": t[2], "actual_in": t[3], "actual_out": t[4], "cached_in": t[5], "usage_unknown_entries": t[6],
                  "max_actual_in_one_request": t[7], "max_actual_out_one_request": t[8],
                  "scope_thresholds": {k: d["ledger"]["scopes"][arm]["limits"][k] for k in ("input_tokens", "output_tokens", "per_request_input", "per_request_output")}},
       "breaker": srow[2] if srow else None, "elapsed_s": round(now - srow[1]) if srow else 0, "elapsed_limit_s": d["ledger"]["scopes"][arm]["limits"]["elapsed_s"],
       "scope_expires_utc": iso(srow[1] + d["ledger"]["scopes"][arm]["limits"]["elapsed_s"]) if srow else None,
       "projects_completed": sorted(run.get("projects", {})), "projects_deferred": deferred,
       "not_attempted": [{"ep": x["ep"], "documents": len(x.get("documents", [])), "reason": x.get("reason")} for x in run.get("not_attempted", [])],
       "per_project_requests": {ep: v.get("requests") for ep, v in run.get("projects", {}).items()},
       "terminal_stop": stop, "critical_acceptances": crit, "rolling_used_24h": used,
       "next_resume_utc": min((x["next_eligible_utc"] for x in deferred if x["next_eligible_utc"].startswith("20")), default=None)}
n = len(list(HERE.glob(f"REPORT-{arm}-*.json"))) + 1
(HERE / f"REPORT-{arm}-{n}.json").write_text(json.dumps(rep, indent=1, default=str) + "\n", encoding="utf-8")
with open(HERE / "RUN-LOG.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"event": "arm-report", **{k: rep[k] for k in ("utc", "arm", "tag", "status", "requests_sent_ledger", "requests_remaining", "breaker", "next_resume_utc")}}) + "\n")
print(json.dumps(rep, indent=1, default=str))
