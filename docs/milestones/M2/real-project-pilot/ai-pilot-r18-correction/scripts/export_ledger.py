"""Read-only export of the usage accounting for the package: every ledger scope of the pilot and of this continuation
(scopes, entries, amendments), the cross-track project-day rows of the pilot / continuation tracks, and the
reconciliation of the original 150. Writes ledger/LEDGER-EXPORT.json."""
import json
import pathlib
import sqlite3
import time

L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
L.row_factory = sqlite3.Row
scopes = [dict(r) for r in L.execute("select * from scopes where scope like 'ai-pilot%' order by scope")]
entries = [dict(r) for r in L.execute("select * from entries where scope like 'ai-pilot%' order by id")]
amend = [dict(r) for r in L.execute("select * from limit_amendments where scope like 'ai-pilot%' order by id")]
earlier = L.execute("select count(*) from entries where scope = 'r2x-small-2026-09-29'").fetchone()[0]
L.close()
X = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
xt = [dict(zip(("ep", "at", "track", "task", "source"), r)) for r in X.execute(
    "select ep, at, track, task, source from calls where track like 'pilot-%' or track like 'cont-%' order by id")]
now = time.time()
window = {ep: X.execute("select count(*) from calls where ep = ? and at >= ?", (ep, now - 86400)).fetchone()[0]
          for ep in ("8430", "16830", "17428", "19144", "22510", "23323", "26208", "27421", "30549")}
X.close()
settled = {}
for e in entries:
    if e["state"] == "settled":
        settled[e["scope"]] = settled.get(e["scope"], 0) + 1
pilot = sum(v for k, v in settled.items() if not k.startswith("ai-pilot-r18"))
cont = sum(v for k, v in settled.items() if k.startswith("ai-pilot-r18"))
out = {"exported_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "settled_by_scope": settled,
       "original_150": {"pilot_settled": pilot, "continuation_settled": cont, "total_settled": pilot + cont, "left": 150 - pilot - cont,
                        "reserved_for_h06": 24, "breaker_refusals_never_sent": sum(1 for e in entries if e["state"] == "refused")},
       "earlier_scope_r2x_small_entries": earlier, "project_day_now": window, "scopes": scopes, "entries": entries, "limit_amendments": amend,
       "project_day_rows": xt}
d = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/ledger")
d.mkdir(exist_ok=True)
(d / "LEDGER-EXPORT.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("settled_by_scope", "original_150", "project_day_now")}, indent=1))
