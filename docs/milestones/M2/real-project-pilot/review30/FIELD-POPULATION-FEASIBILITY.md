# Field-population feasibility (R30-02)

This table was computed **before any label or prediction exists** for a fresh cohort. No document content was opened. The source is [field-population/FIELD-POPULATION.json](field-population/FIELD-POPULATION.json), produced by `scripts/feasibility.py`.

## The rule

A conclusive claim for a field needs **at least 12 resolved documents carrying that fact and attempted by both arms**. The rule applies separately to identity, revision and consultant decision.

- **Selection target:** 16 per field, so a 25% shortfall in attempts still leaves 12. In the four-arm experiment, the whole-page arm attempted 24 of 26 PDFs and ROI attempted 24.
- **Below the minimum:** a field with fewer than 12 matched documents after the run is reported INCONCLUSIVE, under a rule fixed before prediction.

## Prevalence evidence

The only labelled prevalence available comes from the frozen r26.2 labels, which cover 27 documents from the exploration projects:

| Fact | Resolved documents carrying it |
|---|---|
| Identity | 16 / 27 |
| Revision | 16 / 27 |
| Consultant decision | 6 / 27 (D04, D16, D17, D18, D19, D22) |

A fresh pool's rates are unknown, so the plan uses these ranges:

| Field | Planning range (low, mid, high) |
|---|---|
| Identity and revision | 0.45, 0.59, 0.70 |
| Decision, in paths whose names carry a review or approval signal | 0.20, 0.30, 0.45 |
| Decision, elsewhere | 0.05, 0.10, 0.15 |

## Expected, minimum and maximum resolved documents carrying the fact

The minimum is the 5th percentile at the low rate, and the maximum the 95th percentile at the high rate.

| Design | Field | Pool | Expected | Minimum | Maximum | Target 16 reachable? |
|---|---|---|---|---|---|---|
| First labelling pool (40 review-signal, 20 drawing-signal, 12 other paths) | identity | 72 | 42.7 | 25 | 57 | yes, even at the minimum |
| | revision | 72 | 42.7 | 25 | 57 | yes |
| | **decision** | 72 | 15.2 | **5** | 29 | **not guaranteed** |
| First pool plus one predeclared extension (36 more review-signal paths) | identity | 108 | 64.0 | 40 | 83 | yes |
| | revision | 108 | 64.0 | 40 | 83 | yes |
| | **decision** | 108 | 26.0 | **11** | 47 | likely, **but the worst case (11) is below 12** |

## Consequence, declared now

- **Identity and revision:** a conclusive claim is feasible with the first pool.
- **Decision:** a conclusive claim is feasible only if the labelled pool contains at least 12 resolved decision-bearing documents. That is checked **after independent label review and before any prediction**, with the extension used at most once. If the count stays below 12, **decision accuracy is out of scope for the run**. The run then **cannot close the M2 decision gate**, and the report must say so. Decision outcomes would still be reported descriptively, without a conclusion.

## Run-set sizes that follow (upper bounds)

| Part of the run set | Documents |
|---|---|
| Resolved decision-bearing, which also count toward identity and revision | up to 16 |
| Resolved identity and revision documents without a decision, for layout balance | 8 |
| Resolved negative or no-record controls | 4 |
| Unsupported-input controls | 2 |
| **Total** | **at most 30** |

All 30 stay in every denominator. Their pages beyond the reader scope are counted, and unresolved labels are reported separately.

Request caps follow from the 30 documents: [BUDGET-DECISION-CARD.md](BUDGET-DECISION-CARD.md).
