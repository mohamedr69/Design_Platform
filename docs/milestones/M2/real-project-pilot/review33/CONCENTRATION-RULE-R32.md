# Concentration rule R32 (replacement for the stratum leg; owner decision A-05)

| | |
|---|---|
| **Version** | `concentration-r32-2026-10-03.1` |
| **Code** | `scripts/harness-r32/concentration_r32.py`, 12 tests in `tests/test_concentration_r32.xml`. Its hash is bound in `BINDING-MANIFEST-R33.json` |
| **When it was frozen** | Before any prediction. No prediction exists for the cohort, and this task made none |
| **Reference set** | Every figure computed with this rule carries the statement "reference set independently AI-reviewed (Claude agents), not human-signed" |
| **Review** | The rule goes to the independent read-only review ORCH-05R. It is not self-approved |

## 1. What the rule replaces, and why

**The plan rule.** Plan v2 §5.5 and `review31/score_bcr.concentration` say: "C is not eligible if more than half of its net gain in a field comes from one project **or one stratum**."

**Why it fails (Review 33, R33-01 and D4-07):**

- 37 of the 38 decision-bearing documents are `review_signal`. The 16 decision documents of the proposed run set are 15 review_signal and 1 other.
- Any positive decision gain is therefore "concentrated", so decision ELIGIBLE is unreachable.
- The single outcome then made the **whole comparison** NOT ELIGIBLE.

**What the owner decided (A-05):**

> "Keep the safety objective but replace the unreachable stratum leg. The executable replacement must measure: project concentration; contractor concentration; layout/template concentration; decision-type concentration; positive and negative decision controls; whether gains or failures come mainly from one project, contractor or layout. Decision-positive documents may come from review-signal paths. Do not require positive decisions inside strata that contain no decision evidence by construction."

## 2. What is measured (every field, every time)

**Matched population.** For field *f*, the matched documents are the canonical documents that:

- have *f* resolved for scoring (per field);
- carry *f*;
- were attempted by B **and** by C.

The run set may restrict this further.

**Per-document gain.** g(doc) = y_C(doc, f) − y_B(doc, f), where y is the clean, correctly associated recovery of the scorer (0 or 1). NOT_SCORABLE rows never enter y.

**Net gain.** The net gain is Σ g.

**Failures of C in f.** Failures are counted in two ways:

- **wrong acceptances:** C's critical acceptances on resolved truth in *f*, on every attempted run-set document, controls included;
- **lost facts:** matched documents with y_B = 1 and y_C = 0.

**Groupings.** Each matched document belongs to a group in every grouping. Only the first three groupings can block (§3).

| Grouping | Source (adapter) | Blocking? |
|---|---|---|
| project | `EP-<ep>` | yes |
| contractor | `PROJECT-VERIFICATION.json` `results[ep].contractor` | yes |
| layout / template key | ADAPTER-CONTRACT §5 (labels' `kind` and page-1 `page_role`, and the drafting helpers' fixed strings) | yes |
| decision type | the class of the document's scorable present decision rows, or `none` | reported only |
| stratum | `FROZEN-SELECTION.json` `stratum` | reported only |

For each group the rule reports:

- the number of matched documents;
- the net gain, gains and losses;
- the share of the net gain (when the net gain is positive);
- the failures and the share of failures.

**Decision controls.** These are counted per lane (B, C and R when given).

- **Positive control:** the decision truth is present and resolved, so the document carries the decision.
- **Negative control:** the decision is resolved and **every** in-scope decision row is a scorable ABSENT (`blank_decision_area` or `no_decision_area`).
- **Counts per lane:**
  - attempted;
  - correct: a clean decision recovery for positives, and no decision false positive for negatives;
  - false accept: a wrong decision acceptance for positives, and any accepted decision for negatives. A held value or `UR` / `n/a` is not an acceptance.
- **By stratum:** the counts are also broken down by stratum. Positives may come from review-signal paths. **No stratum is required to hold a positive.**

**Attribution statement.** One sentence per field states:

- the net gain;
- the largest project, contractor and layout share of the gain;
- the failures and the largest share of failures;
- whether gains or failures come **mainly** (more than half) from one project, contractor or layout.

## 3. Outcome and thresholds

| Outcome | Rule |
|---|---|
| **NOT ELIGIBLE** | Any one of these holds: (1) net gain ≥ **4** and one project, one contractor or one layout key holds **more than half** of it (group net > net/2); (2) failures ≥ **2**, **more than half** of them in one project, contractor or layout key, **and** that group's own net gain is **negative**; (3) decision field only: **any** false acceptance by C on a negative decision control (the threshold is 0) |
| **UNDETERMINED** | None of the above holds, and the net gain is **< 4**. The distribution of a gain this small is not judged. It is reported and **never blocks**; the field's other gates still apply |
| **ELIGIBLE** | None of the above holds, and the net gain is ≥ 4 |

**How the outcome feeds the scorer.** In `score_bcr_r32.evaluate`, only NOT ELIGIBLE adds reasons, and only to its own field. ELIGIBLE and UNDETERMINED add none.

## 4. Why these thresholds

**The more-than-half threshold (0.5).** This is the safety objective of plan v2 §5.5, kept as the owner asked. Exactly half is not concentration (tested).

**The minimum net gain of 4.** This is the smallest net gain whose bootstrap interval can exclude zero at the realistic matched size.

- The run set gives exactly 16 matched documents for decision and for revision (`RUN-SET-PROPOSAL.json`).
- Each document contributes g ∈ {−1, 0, 1}. With all gains on single documents, a resample of 16 draws contains no gaining document with probability:
  - (13/16)^16 ≈ 0.036 > 0.025 at a net gain of 3;
  - (12/16)^16 ≈ 0.010 < 0.025 at a net gain of 4.
- So at a net gain of 3 the lower 2.5% bound is 0, and at 4 it can be positive. The test `test_net_gain_four_is_the_smallest_whose_interval_can_exclude_zero` checks both with the scorer's own seeded bootstrap.
- **Effect.** Below 4, the field's gain is not established anyway, so judging its distribution would only re-run the stratum problem on 1–3 documents. At net gain 1 a single project is always "more than half".
- The field is still bound by the precision, recovery, matched, critical and request gates.

**The failure leg (failures ≥ 2, more than half in one group, negative group net).** This catches a candidate whose aggregate gain hides a systematic regression on one template or project.

- One failure can never be "concentrated", since it is trivially 100%.
- A failure group whose own net gain is ≥ 0 (C gains as much as it loses there) is reported and does not block.

**The negative controls (0 false acceptances).** An accepted decision where the truth has none is a false acceptance of a critical field. It is also a critical acceptance on resolved truth, which the safety gate already refuses. The leg makes the control explicit for the decision field.

**Decision type and stratum are reported only.**

- In the proposed run set the 16 decision documents are:
  - by type: approved as noted 13, approved 2, revise and resubmit 1;
  - by stratum: review_signal 15, other 1.
- A blocking leg on either would fire on **any** uniform gain (13/16 or 15/16 is more than half). That is exactly the unreachability R33-01 found.
- They stay in the output so that a reader sees whether gains or failures sit in one decision type.

**Contractor.** In this cohort each project has exactly one contractor (`PROJECT-VERIFICATION.json`), so the contractor leg equals the project leg. The output says so (`contractor_equals_project`). The leg is kept for cohorts where they differ.

## 5. Reachability on the proposed run set

These are synthetic figures, not results. They come from `dry-run/SCORER-SCENARIOS.json` and use the real truth and run set with synthetic lane results.

| Field | Matched | Largest project share at a uniform gain | Largest layout share | Outcome at a uniform gain (S1) |
|---|---|---|---|---|
| identity | 23 | EP-27331 6/23 = 0.26 | emaar 6/23 = 0.26 | ELIGIBLE |
| revision | 16 | EP-27331 6/16 = 0.375 | emaar 6/16 = 0.375 | ELIGIBLE |
| decision | 16 | EP-27331 6/16 = 0.375 | emaar 6/16 = 0.375 | ELIGIBLE |

**ELIGIBLE is reachable for every field.**

**Other scenarios in the same file:**

- **S2:** a gain only in EP-27331 is NOT ELIGIBLE, by project, contractor and layout.
- **S4:** a decision false acceptance on a negative control (F042) makes decision NOT ELIGIBLE.
- **S6:** a decision gain of 3 is UNDETERMINED.

## 6. What the rule never does

- It never requires a positive decision inside a stratum that has no decision evidence by construction (drawing_signal holds 0 of the 38).
- It never selects a default.
- It never changes a label.
- It never reads a prediction. No prediction exists.
- It never turns UNDETERMINED into ELIGIBLE or NOT ELIGIBLE.
