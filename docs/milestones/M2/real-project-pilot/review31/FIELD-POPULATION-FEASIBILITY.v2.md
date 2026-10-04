# Field-population feasibility v2 (R31-02)

This supersedes `review30/FIELD-POPULATION-FEASIBILITY.md`. It was computed before any label or prediction exists, with no document content opened, by `scripts/feasibility_r31.py`. The output is [field-population/FEASIBILITY-R31.json](field-population/FEASIBILITY-R31.json).

## The rule (no partial closure run)

1. **Pool:** label the first pool of 72 documents: 40 review-signal paths, 20 drawing-signal paths and 12 others, at most 12 per project, seed `m2-r30-pool-2026-10-02`.
2. **Independent review:** the labels are reviewed independently. This is the owner-delegated Codex AI review, recorded as independent AI review and never as human sign-off.
3. **Count:** for each of identity, revision and decision, count the **resolved, independently reviewed documents carrying the fact** (`score_bcr.population_gate`).
4. **All three ≥ 12:** select the run set (plan §2) and continue.
5. **Otherwise:** draw **extension-1**, 36 more review-signal paths at a cumulative cap of 18 per project, seed `m2-r31-extension-1-2026-10-02`. Label and review it the same way, then count again.
6. **Still short:** draw **extension-2**, 36 more review-signal paths at a cumulative cap of 24 per project, seed `m2-r31-extension-2-2026-10-02`. Label, review and count again.
7. **Still short after extension-2:** **PREPARATION BLOCKED**. No request is dispatched, no field is run "in scope" on its own, and the M2 gates stay open.

Every count is taken **before any prediction**. Only truth presence in the frozen labels is used.

## Feasibility (planning ranges from r26.2 prevalence, as in Review 30)

The worst case is the 5th percentile at the low rate, and the best case the 95th percentile at the high rate.

| Design | Field | Documents | Expected | Worst case | Best case | P(< 12) at low rate |
|---|---|---|---|---|---|---|
| First pool | identity / revision | 72 | 42.7 | 25 | 57 | 0.000 |
| First pool | **decision** | 72 | 15.2 | **5** | 29 | **0.757** |
| + extension-1 | identity / revision | 108 | 64.0 | 40 | 83 | 0.000 |
| + extension-1 | **decision** | 108 | 26.0 | **11** | 47 | 0.071 |
| + extension-2 | identity / revision | 144 | 85.3 | 55 | 110 | 0.000 |
| + extension-2 | **decision** | 144 | 36.8 | **17** | 65 | **0.001** |

**Consequence:** at the low planning rate, the probability of ending in PREPARATION BLOCKED is about 0.1%. Prevalence in fresh projects is still unknown, so blocking remains possible. If it happens, the outcome is reported as such, never as a partial result.

## Path capacity of the proposed cohort (metadata counts)

These figures are an upper bound. A project's cap covers all strata, while the review-signal count used here is per path name.

| Stage | Cumulative cap per project | Review-signal paths needed | Available in the picks under the cap | Alternates entered | Feasible |
|---|---|---|---|---|---|
| Pool | 12 | 40 | 60 | none | yes |
| + extension-1 | 18 | 76 | 78 | none | yes |
| + extension-2 | 24 | 112 | 96 | 22317 (24) | yes (120) |

**Labelling cost:** each extension adds 36 documents to label and independently review. The worst case is 144 labelled documents for a run set of at most 30.
