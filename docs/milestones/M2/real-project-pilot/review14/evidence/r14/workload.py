"""Per-project workload and remaining allowance for the remaining exploration batch UNDER THE CORRECTED CONTRACT
(per document per profile: 12 calls / 120 s; evidence reader cap 8 calls per document; per project per rolling 24 h:
60 across all tracks; ledger: a new declared scope). Two figures per project, never a single calendar date:
  observed  : the small batch's measured requests per document (B 24/12, C 29/12; A 0 on non-form documents)
  cap-bound : the most the caps allow (B and C: 8 per PDF; BOQ: 12 per sheet per profile)
Minimum rolling days per project = ceil(requests / 60): the day limit binds per project, so projects are not summed
into one daily total; the ledger scope's request cap and provider latency bind in addition (not modelled)."""
import collections
import json
import math
import pathlib
import time

W = pathlib.Path("C:/t/iso/work/r2x")
m = json.loads((W / "EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
tri = json.loads((W / "r14/BOQ-CANDIDATE-TRIAGE.json").read_text(encoding="utf-8"))
small = {x["doc_key"] for x in json.loads((W / "SMALL-BATCH.json").read_text(encoding="utf-8"))["documents"]}
docs = [d for d in m["documents"] if d["doc_key"] not in small]
pdfs = collections.Counter(d["ep"] for d in docs if d["extension"] == ".pdf")
words = collections.Counter(d["ep"] for d in docs if d["extension"] != ".pdf")
boq = collections.Counter(c["doc_key"].split("/", 1)[0][3:] for c in tri["candidates"] if c["class"] != "not_boq")
RATE = {"B": 24 / 12, "C": 29 / 12}
out = {"contract": "corrected (R14-01)", "method": __doc__, "projects": {}}
for ep in sorted(set(pdfs) | set(boq)):
    obs = pdfs[ep] * (RATE["B"] + RATE["C"]) + boq[ep] * 2 * 12 * 0.5
    cap = pdfs[ep] * (8 + 8) + boq[ep] * 2 * 12
    out["projects"][ep] = {"pdf_documents": pdfs[ep], "word_documents": words[ep], "boq_sheets": boq[ep],
                           "requests_observed_rate": round(obs), "requests_cap_bound": cap,
                           "min_rolling_days_observed": math.ceil(obs / 60), "min_rolling_days_cap_bound": math.ceil(cap / 60)}
out["totals"] = {k: sum(p[k] for p in out["projects"].values()) for k in ("pdf_documents", "boq_sheets", "requests_observed_rate", "requests_cap_bound")}
out["longest_project_min_days"] = {"observed": max(p["min_rolling_days_observed"] for p in out["projects"].values()),
                                   "cap_bound": max(p["min_rolling_days_cap_bound"] for p in out["projects"].values())}
import sqlite3
con = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
now = time.time()
out["project_day_used_now"] = dict(con.execute("select ep, count(*) from calls where at >= ? group by ep", (now - 86400,)).fetchall())
con.close()
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
lim = json.loads(con.execute("select limits from scopes where scope = 'r2x-small-2026-09-29'").fetchone()[0])
used = con.execute("select count(*) from entries where scope = 'r2x-small-2026-09-29' and state = 'settled'").fetchone()[0]
con.close()
out["ledger_small_scope"] = {"limit": lim["requests"], "settled": used, "remaining": lim["requests"] - used,
                             "note": "the small scope is not reused for the next batch; a new declaration names its own scope (nothing reset)"}
out["BOQ_note"] = "BOQ observed rate unknown under the corrected contract (the stored runs exceeded 12); estimated at half the 12-call cap per sheet per profile"
(W / "r14/WORKLOAD-ESTIMATE.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
for ep, p in out["projects"].items():
    print(ep, p)
print(out["totals"], out["longest_project_min_days"], out["project_day_used_now"], out["ledger_small_scope"])
