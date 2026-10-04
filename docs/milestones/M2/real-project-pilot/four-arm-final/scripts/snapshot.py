"""Runbook v2 step 2 (read-only): rolling 24 h counter for the ten declared projects and the ledger totals of the given
scope. Appends one JSON line to RUN-LOG.jsonl and prints it. Usage: snapshot.py <arm A|L1..L4> <label>"""
import json, pathlib, sqlite3, sys, time, datetime
arm, label = sys.argv[1], sys.argv[2]
d = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
eps = sorted(d["authorization"]["projects_resolved"])
now = time.time()
pc = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
used = {ep: pc.execute("select count(*) from calls where ep = ? and at >= ?", (ep, now - 86400)).fetchone()[0] for ep in eps}
last = {ep: pc.execute("select max(at) from calls where ep = ?", (ep,)).fetchone()[0] for ep in eps}
pc.close()
scope = d["ledger"]["scopes"][arm]["scope"]
lc = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
row = lc.execute("select limits, created_at, breaker from scopes where scope = ?", (scope,)).fetchone()
tot = lc.execute("select count(*), sum(case when state='settled' then 1 else 0 end), coalesce(sum(act_in),0), coalesce(sum(act_out),0), coalesce(sum(est_in),0), coalesce(sum(est_out),0) from entries where scope = ?", (scope,)).fetchone()
states = dict(lc.execute("select state, count(*) from entries where scope = ? group by state", (scope,)).fetchall())
lc.close()
cap = d["ledger"]["caps"][arm]
rec = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "label": label, "arm": arm, "scope": scope,
       "scope_exists": row is not None, "limits_match": (json.loads(row[0]) == d["ledger"]["scopes"][arm]["limits"]) if row else None,
       "elapsed_s": round(now - row[1]) if row else 0, "elapsed_limit_s": d["ledger"]["scopes"][arm]["limits"]["elapsed_s"],
       "breaker": row[2] if row else None, "entries": tot[0], "states": states, "requests_remaining": cap - tot[0],
       "actual_in": tot[2], "actual_out": tot[3], "est_in": tot[4], "est_out": tot[5],
       "rolling_used_24h": used, "rolling_capacity": {ep: max(0, 60 - n) for ep, n in used.items()}}
with open(pathlib.Path(__file__).parent / "RUN-LOG.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(rec) + "\n")
print(json.dumps(rec, indent=1))
