"""Observed workload (read-only) from the durable ledger entries of every scope of the original experiment: per task,
requests, total reported input tokens (INCLUDING cached input: the breaker's measure) and output tokens, latency, turns,
timeouts / refusals, and how many requests have UNKNOWN usage (charged at their estimate). Per arm: requests per planned
document. No price exists, so no cost is computed. Writes workload/OBSERVED-WORKLOAD.json."""
import collections
import json
import pathlib
import sqlite3
import statistics

L = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
L.row_factory = sqlite3.Row
rows = [dict(r) for r in L.execute("select * from entries where scope like 'ai-pilot%' order by id")]
L.close()


def pct(xs, q):
    xs = sorted(x for x in xs if x is not None)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


by_task = collections.defaultdict(list)
for r in rows:
    if r["state"] == "settled":
        by_task[r["task"]].append(r)
tasks = {}
for t, rs in sorted(by_task.items()):
    known = [r for r in rs if not r["usage_unknown"]]
    tasks[t] = {"requests": len(rs), "usage_unknown": len(rs) - len(known), "timeouts": sum(1 for r in rs if r["outcome"] == "timeout"),
                "input_total_incl_cached": {"mean": round(statistics.mean(r["act_in"] for r in known)) if known else None, "p90": pct([r["act_in"] for r in known], 0.9),
                                            "max": max((r["act_in"] for r in known), default=None)},
                "cached_input_mean": round(statistics.mean(r["cached_in"] or 0 for r in known)) if known else None,
                "output": {"mean": round(statistics.mean(r["act_out"] for r in known)) if known else None, "max": max((r["act_out"] for r in known), default=None)},
                "latency_ms": {"p50": pct([r["latency_ms"] for r in known], 0.5), "p90": pct([r["latency_ms"] for r in known], 0.9),
                               "max": max((r["latency_ms"] for r in known), default=None)},
                "turns": {"p50": pct([r["turns"] for r in known], 0.5), "max": max((r["turns"] or 0 for r in known), default=None)},
                "estimate_charged_for_unknown": sorted({r["est_in"] for r in rs if r["usage_unknown"]})}
planned = {"ai-pilot-2026-09-30-S": 12, "ai-pilot-2026-09-30-G": 12, "ai-pilot-2026-09-30-T": 12, "ai-pilot-r18-2026-09-30-S": 7, "ai-pilot-r18-2026-09-30-T2": 7,
           "ai-pilot-2026-09-30-BOQ-S": 1, "ai-pilot-2026-09-30-BOQ-T": 1}
arms = {}
for s, n in planned.items():
    rs = [r for r in rows if r["scope"] == s]
    settled = [r for r in rs if r["state"] == "settled"]
    arms[s] = {"planned_documents": n, "settled_requests": len(settled), "refused": sum(1 for r in rs if r["state"] == "refused"),
               "requests_per_planned_document": round(len(settled) / n, 2), "timeouts": sum(1 for r in settled if r["outcome"] == "timeout"),
               "input_total_incl_cached": sum(r["act_in"] or 0 for r in settled), "output_total": sum(r["act_out"] or 0 for r in settled),
               "note": {"ai-pilot-2026-09-30-T": "closed by its breaker after 9 requests: a lower bound, not a per-document rate"}.get(s)}
out = {"mode": "read-only ledger", "pricing": "unknown: no cost computed", "tasks": tasks, "arms": arms}
d = pathlib.Path("C:/t/iso/work/r2x/review20/workload")
d.mkdir(parents=True, exist_ok=True)
(d / "OBSERVED-WORKLOAD.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
for t, v in tasks.items():
    print(t, v["requests"], "unknown", v["usage_unknown"], "in mean/p90/max", v["input_total_incl_cached"], "out", v["output"]["mean"], "lat p50/p90", v["latency_ms"]["p50"], v["latency_ms"]["p90"])
for s, v in arms.items():
    print(s, v["settled_requests"], "/", v["planned_documents"], "=", v["requests_per_planned_document"], "timeouts", v["timeouts"])
