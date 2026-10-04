"""R30-02 field-population feasibility, before any label or prediction. Prevalence comes from the frozen r26.2 labels
(27 documents, exploration projects): resolved documents carrying an identity fact 16/27, a revision fact 16/27, a
consultant-decision fact 6/27. Rates for a fresh pool are UNKNOWN; a planning range is used: identity / revision 0.45-0.70;
decision 0.20-0.45 in review-signal paths and 0.05-0.15 elsewhere (the pool oversamples review-signal paths by file name).
For each design the table gives the expected count and a min / max = the 5th percentile at the low rate and the 95th at the
high rate (binomial). Writes FIELD-POPULATION.json."""
import json
import math
import pathlib


def binom_q(n, p, q):
    acc = 0.0
    for k in range(n + 1):
        acc += math.comb(n, k) * p ** k * (1 - p) ** (n - k)
        if acc >= q:
            return k
    return n


def mix_q(parts, q, draws=0):
    """Quantile of a sum of independent binomials (exact convolution)."""
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


POOL = {"review_signal": 40, "drawing_signal": 20, "other": 12}            # first labelling pool: 72 documents
EXT = {"review_signal": 36}                                                # one predeclared seeded extension
RATES = {"identity": (0.45, 16 / 27, 0.70), "revision": (0.45, 16 / 27, 0.70)}
DEC = {"review_signal": (0.20, 0.30, 0.45), "drawing_signal": (0.05, 0.10, 0.15), "other": (0.05, 0.10, 0.15)}
rows = []
for label, pool in (("first pool (72)", POOL), ("pool + extension (108)", {k: POOL.get(k, 0) + EXT.get(k, 0) for k in POOL})):
    n = sum(pool.values())
    for f, (lo, mid, hi) in RATES.items():
        rows.append({"design": label, "field": f, "pool_documents": n, "expected": round(n * mid, 1),
                     "min_p5_at_low_rate": binom_q(n, lo, 0.05), "max_p95_at_high_rate": binom_q(n, hi, 0.95)})
    parts = lambda i: [(pool[s], DEC[s][i]) for s in pool]
    rows.append({"design": label, "field": "decision", "pool_documents": n, "expected": round(sum(pool[s] * DEC[s][1] for s in pool), 1),
                 "min_p5_at_low_rate": mix_q(parts(0), 0.05), "max_p95_at_high_rate": mix_q(parts(2), 0.95)})
out = {"source_rates_r26_2": {"identity": "16/27", "revision": "16/27", "decision": "6/27", "resolved_documents": "17/27"},
       "planning_ranges": {"identity": RATES["identity"], "revision": RATES["revision"], "decision_by_stratum": DEC},
       "first_pool": POOL, "extension": EXT, "target_per_field": 16, "minimum_matched_per_field": 12, "rows": rows}
pathlib.Path(__file__).resolve().parent.joinpath("FIELD-POPULATION.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
for r in rows:
    print(r)
