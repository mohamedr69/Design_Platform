# Concentration rule R32, version 2 (owner decision A-05; Review 34 RC-1 and RC-6)

| | |
|---|---|
| **Version** | `concentration-r32-2026-10-03.2` |
| **Supersedes** | `concentration-r32-2026-10-03.1` (`review33/CONCENTRATION-RULE-R32.md`, sha256 `6ad703632b6b8abb3f34d6269f060b5892a0ea20ac1b5f3b73c8ffa94200df7c`; code `6908e80a…3e4d`) |
| **Code** | `scripts/harness-r32/concentration_r32.py`, sha256 `fc5052f80ea6d2454feadb84ccc863877cdc9851921f7c4dd551c58da914dffe`, bound in `BINDING-MANIFEST-R34.json` |
| **Tests** | `tests/test_concentration_r32.xml` (28 tests) and the RC-1 / RC-6 tests in `tests/test_score_bcr_r32.xml` |
| **Answers** | Review 34 **R34-01** (blocker, RC-1) and **R34-08** (minor, RC-6) |
| **When it was frozen** | Before any prediction. No prediction exists for the cohort, and this task made none |
| **Reference set** | Every figure computed with this rule carries the statement "reference set independently AI-reviewed (Claude agents), not human-signed" |
| **Review** | Goes to the independent read-only Review 35 (ORCH-05R2). It is not self-approved |
| **Owner** | The owner may override this rule at ORCH-07 (for example, accept a floor with the corrected justification). This package does not weaken it |

## 1. What the rule replaces, and why

**The plan rule.** Plan v2 §5.5 and `review31/score_bcr.concentration`: "C is not eligible if more than half of its net gain in a field comes from one project **or one stratum**."

**Why the stratum leg had to go** (Review 33, R33-01): 37 of the 38 decision-bearing documents are `review_signal`, so any decision gain was "concentrated" and decision ELIGIBLE was unreachable.

**What the owner decided (A-05):**

> "Keep the safety objective but replace the unreachable stratum leg. The executable replacement must measure: project concentration; contractor concentration; layout/template concentration; decision-type concentration; positive and negative decision controls; whether gains or failures come mainly from one project, contractor or layout. Decision-positive documents may come from review-signal paths. Do not require positive decisions inside strata that contain no decision evidence by construction."

**What version 1 got wrong (R34-01).** Version 1 also switched off the project, contractor and layout legs below a net gain of 4. Review 34 showed (S3b) that a decision gain of 3, all from EP-27331, one contractor and the EMAAR template, came out ELIGIBLE for every field, while the same gain on 4 documents was blocked. Version 1 was non-monotonic, weakened legs A-05 kept, and rested on a refuted justification (§4).

## 2. What is measured (every field, every time)

**Matched population.** For field *f*: the canonical documents that have *f* resolved for scoring, carry *f*, and were attempted by B **and** by C (restricted to the run set when one is given).

**Per-document gain.** g(doc) = y_C(doc, f) − y_B(doc, f), where y is the scorer's clean, correctly associated recovery (0 or 1). NOT_SCORABLE rows never enter y.

**Net gain.** Σ g.

**Failures of C in f, counted once per (document, field)** (RC-6, R34-08). A document is **one** failure of *f* when C made a wrong acceptance on resolved truth of *f* on it (any attempted run-set document, controls included), or lost the fact (matched, y_B = 1 and y_C = 0), or both. A wrong acceptance that also loses the fact is **one** failure (version 1 counted two). Wrong acceptances on several pages of one document are one failure. Each failure lists its kinds (`wrong_acceptance`, `lost_fact`) and pages.

**Groupings.**

| Grouping | Source (adapter) | Blocking? |
|---|---|---|
| project | `EP-<ep>` | yes |
| contractor | `PROJECT-VERIFICATION.json` `results[ep].contractor` | yes |
| layout / template key | ADAPTER-CONTRACT §5 | yes |
| decision type | the class of the document's scorable present decision rows, or `none` | reported only |
| stratum | `FROZEN-SELECTION.json` `stratum` | reported only |

For each group: matched documents, net gain, gains, losses, share of the net gain (net gain > 0), failures and share of the failures.

**Decision controls** (per lane B, C and R): positive = decision truth present and resolved; negative = every in-scope decision row a scorable ABSENT with the field resolved. Attempted / correct / false-accept counts, also by stratum. Positives may come from review-signal paths; **no stratum is required to hold a positive.**

**Attribution statement.** One sentence per field: the net gain, the largest project / contractor / layout share of the gain, the failures (once per document) and their largest share, and whether gains or failures come **mainly** (more than half) from one project, contractor or layout.

## 3. Outcome (version 2: no net-gain floor on any leg)

| Outcome | Rule |
|---|---|
| **NOT ELIGIBLE** | Any one of: (1) the net gain is **positive** and one project, one contractor or one layout key holds **more than half** of it (that group's own net gain > net / 2), **whatever the size of the gain** (1, 2, 3, … documents); (2) failures ≥ **2** (once per document), **more than half** of them in one project, contractor or layout key, **and** that group's own net gain is negative; (3) decision field only: **any** false acceptance by C on a negative decision control (threshold 0) |
| **UNDETERMINED** | None of the above, and the net gain is **0 or negative**: there is no gain to attribute. It adds no reason and does not block by itself; the field's other gates (precision, recovery, matched, critical, request gate, decision coverage) still apply. Because every NOT ELIGIBLE leg is decided first, UNDETERMINED can never turn NOT ELIGIBLE into ELIGIBLE |
| **ELIGIBLE** | None of the above, and the net gain is positive: no project, contractor or layout key holds more than half of it |

Thresholds in code: `{"gain_share_max": 0.5, "min_failures": 2, "failure_share_max": 0.5, "negative_control_false_accepts_max": 0}`. There is no `min_net_gain`.

**How it feeds the scorer.** In `score_bcr_r32.evaluate`, only NOT ELIGIBLE adds reasons, to its own field; the candidate-level outcome (RC-2, `SCORER-CHANGES.md`) then makes the whole candidate NOT ELIGIBLE.

## 4. Why there is no floor: the scorer's project-stratified bootstrap

**Version 1's justification is withdrawn.** It said a net gain of 4 is the smallest whose bootstrap interval can exclude zero, from (13/16)^16 ≈ 0.036 and (12/16)^16 ≈ 0.010 for one group of 16 documents, and its test bootstrapped **one unstratified group**. The scorer does not do that: `score_bcr_r32.bootstrap` resamples documents **within each project** (2,000 resamples, seed `m2-r30-bootstrap-2026-10-02`).

**What the stratified bootstrap does with a concentrated gain.** A project stratum with *m* matched documents of which *k* gained contributes a gain of zero to a resample only with probability ((m − k)/m)^m. When the gain fills the stratum (k = m) it contributes the same amount to **every** resample. So the interval measures only within-project variation; a gain caused by something specific to one project or template (between-project variation) is treated as fixed. On the real run set (decision strata EP-27331 6, EP-26687 3, EP-3563 3, EP-22349 2, EP-29255 2):

| Gain | Paired decision interval (scorer) | Request-gate interval |
|---|---|---|
| 2 documents, all of EP-22349 (S3a) | [0.125, 0.125] — excludes zero | [0.0, 0.1739] |
| 3 documents of EP-27331 (S3b) | [0.0625, 0.3125] — excludes zero | [0.0435, 0.2174] — **passes** |
| 4 documents of EP-27331 (S3c) | [0.125, 0.375] | [0.087, 0.2609] — passes |
| 1 document in a one-document project (synthetic) | [0.0625, 0.0625] | — |

(From `dry-run/SCORER-SCENARIOS.json` and `test_score_bcr_r32.py::test_the_project_stratified_bootstrap_excludes_zero_for_a_gain_concentrated_in_one_project`, `::test_version_one_floor_rested_on_an_unstratified_bootstrap_that_the_scorer_does_not_use`.)

**Consequence.** The interval is **narrowest exactly where the gain is concentrated**, so it cannot be what protects against a concentrated gain; "the gain is too small to judge" is the opposite of what the scorer's interval says. The likeliest real pattern (Review 34 §6) is a switch that fixes one consultant template and gains on a few EP-27331 EMAAR documents; that gain passes the request gate at 3 documents. The safety objective A-05 kept therefore needs the project, contractor and layout legs **at every size**. That is review31's own project leg (`net > 0 and max(by_project) > net / 2`), without the stratum leg.

**What this implies, disclosed for ORCH-07:**
- a net gain of **1** in a field is always NOT ELIGIBLE (one document is 100 % of it);
- a net gain of **2** is ELIGIBLE only when the two documents differ in project, contractor (equal to project in this cohort) **and** layout key;
- in general ELIGIBLE needs the net gain spread so that no project, contractor or layout key holds more than half of it;
- a field with no gain (net 0, for example identity when B and C both read every identity) is UNDETERMINED and does not block by itself.

**Monotonicity.** If a group holds more than half of the net gain *n* (g_A > n/2), adding a gaining document to that group keeps it so: 2(g_A + 1) > n + 1 because 2g_A > n. Tested exhaustively on a 12-document synthetic truth (every gain set of size 1–5 and every extension in the dominant project) and on the real run set (EP-27331 decision gain of size 1 to 6: NOT ELIGIBLE at every size, field and candidate).

**The failure leg** (failures ≥ 2 once per document, more than half in one group, negative group net) catches an aggregate gain that hides a regression on one template or project. One failure can never be "concentrated"; with RC-6 a single wrong acceptance is one failure, never two.

**The negative controls (0 false acceptances).** An accepted decision where the truth has none is also a critical acceptance on resolved truth, which the candidate-level safety gate already refuses; the leg keeps the control explicit for the decision field.

**Decision type and stratum stay report-only** (A-05 says "measure"): in the run set the 16 decision documents are 13 approved as noted, 2 approved, 1 revise and resubmit, and 15 review_signal; a blocking leg on either would fire on any uniform gain, which is R33-01 again.

**Contractor (R34-07, disclosed).** Each project has exactly one contractor in `PROJECT-VERIFICATION.json`, so the contractor leg equals the project leg here (`contractor_equals_project`). The cross-project issuing subcontractor visible in label text (Al Arabia, in EP-3563, EP-22349, EP-15744 and EP-26687) is not measured; the owner accepts this at ORCH-07 or asks for an issuer grouping frozen before any prediction.

## 5. Review 34's scenarios on version 2 (synthetic, not results)

Real truth `4e237a4e…e064` and run set `9058f3d6…7ce8`; lanes made from the truth (`scripts/harness-r32/r34_scenarios.py`); full output `dry-run/SCORER-SCENARIOS.json`.

| Scenario | Version 1 (Review 34 §6) | Version 2: decision concentration | Version 2: candidate outcome |
|---|---|---|---|
| S1 one wrong revision acceptance | NOT ELIGIBLE ×3; "2 of 2 failures" | revision UNDETERMINED (net −1), **1 failure** | NOT ELIGIBLE |
| S2 identity +8, one wrong decision acceptance | NOT ELIGIBLE ×3 | decision UNDETERMINED (net −1, 1 failure) | NOT ELIGIBLE |
| S3a decision +2, EP-22349 | NOT ELIGIBLE ×3 (gate fails); concentration UNDETERMINED | **NOT ELIGIBLE** (EP-22349 1.0) | NOT ELIGIBLE |
| **S3b decision +3, F037 F009 F032 of EP-27331** | **ELIGIBLE ×3** | **NOT ELIGIBLE** (project, contractor, layout 1.0) | **NOT ELIGIBLE** |
| S3c decision +4, EP-27331 | identity, revision ELIGIBLE; decision NOT ELIGIBLE | NOT ELIGIBLE (unchanged) | NOT ELIGIBLE |
| S3c-spread decision +4, one document in each of four projects | ELIGIBLE (largest share 0.25) | ELIGIBLE (project 0.25, layout 0.25) | **ELIGIBLE FOR A SEPARATE SELECTION DECISION** |
| S3d every field +, two documents of EP-22349 | NOT ELIGIBLE ×3 | NOT ELIGIBLE in all three fields | NOT ELIGIBLE |
| S4a C skips five decision documents | NOT ELIGIBLE ×3 | UNDETERMINED | NOT ELIGIBLE (matched 11 < 12) |
| S4b as S4a, INCOMPLETE | INCOMPLETE ×3 | UNDETERMINED | INCOMPLETE |
| S5 identity +8, decision recovery 0.7576 | ELIGIBLE / ELIGIBLE / NOT ELIGIBLE | UNDETERMINED | **NOT ELIGIBLE** (RC-2) |
| S6 revision +6, −2 in EP-26687 | NOT ELIGIBLE ×3 (failure leg) | revision NOT ELIGIBLE (gain and failure legs) | NOT ELIGIBLE |
| S7 decision accepted on negative control F060 | NOT ELIGIBLE ×3 | NOT ELIGIBLE (negative-control leg) | NOT ELIGIBLE |
| S8 decision +2 in one project, identity −1 | — | NOT ELIGIBLE | NOT ELIGIBLE |

**EP-27331 decision gain of every size** (`ep27331_decision_gain_sweep`): sizes 1 to 6 are NOT ELIGIBLE (concentration and candidate); the request gate passes from size 3, which is why the floor was unsafe.

**ELIGIBLE stays reachable** on the real run set for a spread gain (S3c-spread).

## 6. Change record from version 1

| # | Version 1 (`…03.1`) | Version 2 (`…03.2`) | Reason | Finding |
|---|---|---|---|---|
| 1 | Gain legs (project, contractor, layout) only when net gain ≥ 4 | Gain legs whenever the net gain is positive | A concentrated gain of 1–3 passed every gate (S3b); non-monotonic | R34-01 / RC-1 |
| 2 | UNDETERMINED when net gain < 4 (non-blocking) | UNDETERMINED only when net gain ≤ 0 (no gain to attribute); decided after every NOT ELIGIBLE leg | UNDETERMINED must never let a positive concentrated gain through | R34-01 / RC-1 |
| 3 | `THRESHOLDS["min_net_gain"] = 4` | removed | — | R34-01 / RC-1 |
| 4 | §4 justification: one unstratified bootstrap group (refuted) | §4: the scorer's project-stratified bootstrap narrows on concentrated gains; no floor | The test did not use the scorer's stratification | R34-01 / RC-1 |
| 5 | Failures = wrong acceptances + lost facts (one incident could count twice) | Failures once per (document, field), with kinds and pages | "One failure can never be concentrated" must hold | R34-08 / RC-6 |
| 6 | Contractor note | Contractor note names the unmeasured cross-project issuer (R34-07) | Disclosure for the declaration | R34-07 |
| — | Failure leg, negative-control leg, decision type and stratum report-only, attribution, controls | **unchanged** | A-05 | — |

## 7. What the rule never does

- It never requires a positive decision inside a stratum that has no decision evidence by construction.
- It never selects a default, changes a label or reads a prediction (none exists).
- It never turns UNDETERMINED into ELIGIBLE, and UNDETERMINED never overrides NOT ELIGIBLE.
