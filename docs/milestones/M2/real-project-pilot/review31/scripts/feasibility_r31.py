"""Review 31 (R31-02): field-population feasibility for the first pool and TWO predeclared extensions, before any label or
prediction, plus the review-signal path capacity of the proposed cohort under the per-project caps (metadata counts from
FRESH-PROJECTS-R31.json; nothing opened). Planning ranges are those of Review 30 (r26.2 prevalence). Writes
FEASIBILITY-R31.json."""
import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def binom_q(n, p, q):
    acc = 0.0
    for k in range(n + 1):
        acc += math.comb(n, k) * p ** k * (1 - p) ** (n - k)
        if acc >= q:
            return k
    return n


def mix_q(parts, q):
    dist = [1.0]
    for n, p in parts:
        pm = [math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)]
        new = [0.0] * (len(dist) + n)
        for i, a in enumerate(dist):
            for j, b in enumerate(pm):
                new[i + j] += a * b
        dist = new
    acc = 0.0
    for k, v in enumerate(dist):
        acc += v
        if acc >= q:
            return k
    return len(dist) - 1


POOL = {"review_signal": 40, "drawing_signal": 20, "other": 12}
EXT = {"review_signal": 36}
RATES = {"identity": (0.45, 16 / 27, 0.70), "revision": (0.45, 16 / 27, 0.70)}
DEC = {"review_signal": (0.20, 0.30, 0.45), "drawing_signal": (0.05, 0.10, 0.15), "other": (0.05, 0.10, 0.15)}
CAPS = {"pool": 12, "extension-1": 18, "extension-2": 24}
designs = [("first pool (72)", POOL), ("pool + extension 1 (108)", {**POOL, "review_signal": 76}), ("pool + extensions 1 and 2 (144)", {**POOL, "review_signal": 112})]
rows = []
for label, pool in designs:
    n = sum(pool.values())
    for f, (lo, mid, hi) in RATES.items():
        rows.append({"design": label, "field": f, "pool_documents": n, "expected": round(n * mid, 1), "min_p5_at_low_rate": binom_q(n, lo, 0.05),
                     "max_p95_at_high_rate": binom_q(n, hi, 0.95), "p_below_12_at_low_rate": round(sum(math.comb(n, k) * lo ** k * (1 - lo) ** (n - k) for k in range(12)), 4)})
    parts = lambda i: [(pool[s], DEC[s][i]) for s in pool]  # noqa: E731
    lo_parts = parts(0)
    dist = [1.0]
    for m, p in lo_parts:
        pm = [math.comb(m, k) * p ** k * (1 - p) ** (m - k) for k in range(m + 1)]
        new = [0.0] * (len(dist) + m)
        for i, a in enumerate(dist):
            for j, b in enumerate(pm):
                new[i + j] += a * b
        dist = new
    rows.append({"design": label, "field": "decision", "pool_documents": n, "expected": round(sum(pool[s] * DEC[s][1] for s in pool), 1),
                 "min_p5_at_low_rate": mix_q(lo_parts, 0.05), "max_p95_at_high_rate": mix_q(parts(2), 0.95), "p_below_12_at_low_rate": round(sum(dist[:12]), 4)})
fp = json.loads((HERE / "FRESH-PROJECTS-R31.json").read_text(encoding="utf-8"))
cap_rows = []
for stage, cap in CAPS.items():
    need = {"pool": 40, "extension-1": 76, "extension-2": 112}[stage]
    picks = sum(min(r["review_signal_paths"], cap) for r in fp["picked"])
    alts = []
    have = picks
    for r in fp["alternates"]:
        if have >= need:
            break
        take = min(r["review_signal_paths"], cap)
        alts.append({"ep": r["ep"], "review_signal_paths_available": take})
        have += take
    cap_rows.append({"stage": stage, "cumulative_per_project_cap": cap, "review_signal_paths_needed_cumulative": need,
                     "available_in_picks_under_cap": picks, "alternates_entered_in_seeded_order": alts, "available_total": have, "feasible": have >= need})
out = {"planning_ranges": {"identity": RATES["identity"], "revision": RATES["revision"], "decision_by_stratum": DEC, "source": "r26.2 prevalence (Review 30)"},
       "first_pool": POOL, "extensions": {"extension-1": EXT, "extension-2": EXT, "max_extensions": 2}, "minimum_resolved_per_field": 12,
       "rows": rows, "path_capacity": cap_rows,
       "rule": "after independent label review of each stage: all three fields >= 12 -> select the run set; otherwise the next extension; after extension 2 still short -> PREPARATION BLOCKED (no dispatch, no partial closure run)"}
(HERE / "FEASIBILITY-R31.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
for r in rows:
    print(r)
for r in cap_rows:
    print(r)
