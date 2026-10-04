# Scorer changes: Review 31 `score_bcr.py` → review33 → review34 `score_bcr_r32.py` (with `concentration_r32.py`, `lane_judge_r32.py`, `literal_compare_r32.py`, `score_lane_r32.py`)

**Unchanged originals:**
- `review31/scripts/harness/score_bcr.py`, sha256 `5a3828a57eefe8268d32c4d4a64dd03befcbcd212355ee8906088bdfa3de7d1a` (bound under `review31_harness` in `BINDING-MANIFEST-R34.json`); `score_lane.py` `17ed2ba3…` stays bound to the four-arm run and is not used.
- review33's `score_bcr_r32.py` `1ba9caaa0a681997ce928e1416ced3e6b63719a37586782ce5786023d4ad9c08` and `concentration_r32.py` `6908e80a9764c8e13a7b28dc430cf42d12cbd92efc9f6ddc2fd03659abc23e4d` are kept byte for byte in the work folder's `harness-r33-base/` (bound under `harness_r33_base`).

**review34 files:** `score_bcr_r32.py` `3436fe7df06ef15c0d5c0fdaabf728b6216b34909d00ef4be0a3b7eb9217fb63`; `concentration_r32.py` `fc5052f80ea6d2454feadb84ccc863877cdc9851921f7c4dd551c58da914dffe`. `lane_judge_r32.py` (`a0b6b7c8…ca45`), `literal_compare_r32.py` (`ec2221c8…16a3e6`) and `score_lane_r32.py` (`c25f4d89…c3c915`) are **unchanged** from review33.

## Part A. Differences from Review 31 (as of review34)

Kept exactly from Review 31 (same constants, rule text and code shape): `MINIMUM = 12`; the extensions and population-gate actions (no partial closure run); `THRESHOLDS` (accepted precision ≥ 0.98, clean recovery ≥ 0.90, 0 critical acceptances on resolved truth in C, 1 fact per 8 extra requests); the document as unit and y = clean recovery; the paired difference by document-cluster bootstrap **stratified by project**, 2,000 resamples, seed `m2-r30-bootstrap-2026-10-02`; the request gate at equal caps only (unequal caps not applicable, R31-03); the decision coverage gate C ≥ B and C ≥ R; the outcome vocabulary; `default_selected` always `None`; caps B 240 = C 240.

| # | Review 31 (`score_bcr.py`) | review34 (`score_bcr_r32.py` and helpers) | Reason | Answers |
|---|---|---|---|---|
| 1 | One document-level `resolved` flag | `primary(truth, pool, f)` per **field** | F019, F069 and F067 mix resolutions inside one document | R33-05, D4-04 |
| 2 | Page facts with None read as "truth absent" | A row per (pool id, page, field): literal, `ABSENT` or `NOT_SCORABLE`; a missing row means "not labelled" | Ambiguous, uncertain or excluded rows must not read as verified absences | R33-05 |
| 3 | `has_fact`: any non-empty page value | `resolved_for_scoring` yes **and** `carries_fact` yes (reproduces 57/38/38) | A present value can be uncertain or excluded | R33-05, D4-03 |
| 4 | `coverage_counts` over every labelled page | NOT_SCORABLE rows apart, never coverage; `discovery_absent` on ABSENT = verified absence, on a value = wrong absence | §5.1 | R33-05 |
| 5 | Per-document counters from evaluator .10 | Emitted facts judged per (pool id, page, field) by `lane_judge_r32` with .10's states | Per-field truth and NOT_SCORABLE cannot be expressed in .10's counters | R33-05, R33-06, R33-09 |
| 6 | Value comparison inside evaluator .10 | `literal_compare_r32.compare` (whitespace, dashes, case, either-form tails, suffix base form, revision by value, decision by class with the (d1) tolerance, Arabic bytes) | Review 33 §4.3 | R33-09, C-6 |
| 7 | Association by evaluator .10 | Truth keyed by (pool id, page); .10's cross-page identity copy kept except on compilations | (h) | R33-05 |
| 8 | `critical_split` per document | Per **row**: resolved criticals attributed to (pool id, page, field); NOT_SCORABLE acceptances contradicting every literal and candidate are unresolved | §5.1 | R33-05, D4-11 |
| **9** | **One outcome for the whole comparison** | **One candidate-level outcome `outcome` (RC-2)**: a comparison state other than INVALID / INCOMPLETE (PREPARATION BLOCKED, NOT DISPATCHABLE) is the outcome; otherwise ELIGIBLE FOR A SEPARATE SELECTION DECISION **only when all three fields are ELIGIBLE**, else the first of **INVALID > NOT ELIGIBLE > INCOMPLETE** among the field outcomes. Per-field outcomes (`fields[f].outcome`, `outcome_by_field`) stay, as **diagnostics** (`fields[f].role`). Comparison-level states apply to every field; candidate-level gates (a C critical on resolved truth in any field, a RESULT stop, the request gate) apply to every field; field-level gates (precision, recovery, matched ≥ 12, concentration, decision coverage for decision) to their field | C is one switch set and cannot be adopted per field; review31 had one outcome; per-field outcomes alone weakened plan v2 §5 rule 6 | R34-02 (RC-2); R33-01 |
| **10** | `concentration()`: more than half of the net gain from one project **or one stratum** | `concentration_r32` **version 2** (`concentration-r32-2026-10-03.2`): a positive net gain is NOT ELIGIBLE while one project, contractor or layout key holds more than half of it, **at any size**; failure concentration (≥ 2 failures once per document, negative group net); any negative-control false acceptance; decision type and stratum report-only; UNDETERMINED only for net ≤ 0 | The stratum leg was unreachable (R33-01); version 1's floor let a concentrated gain through (R34-01) | R34-01 (RC-1), R34-08 (RC-6), R33-01, C-4 |
| 11 | Every labels document counts | Canonical ids only | An alias could be drawn twice | R33-07 |
| 12 | Metrics over every labelled document | `docs=` restricts metrics, matched sets and controls to the run set | The run set is ≤ 30 of 68 canonical documents | R33-06 |
| 13 | Request-gate gain over fields with `has_fact` | Summed over the fields for which the document is matched | Follows from #1 | R33-05 |
| 14 | New false acceptances: criticals of C not in B | The same, with "unresolved" per #8 | Parity with Review 31 | R33-05 |
| 15 | No reference-set statement | Every output carries it | AI-ACCURACY-POLICY-AMENDMENT-R32-01 | C-3 (A-04) |
| 16 | `primary_outcomes.critical` per lane | Adds `critical_by_field` | Per-field tripwire | R33-05 |
| 17 | `score_lane.py` bound to the four-arm run | `score_lane_r32.py` driven by the r32 truth and run set; B attempted when its row exists | Not bound to the four-arm run | R33-06, D4-05 |
| **18** | Concentration failures (n/a in Review 31) | **Counted once per (document, field)** (RC-6): a wrong acceptance that also loses the fact is one failure; several wrong pages of one document are one failure; each failure lists its kinds and pages | "One failure can never be concentrated" | R34-08 (RC-6) |
| **19** | Request-gate caps were the module constant | The runner passes the declaration's caps (equal to the plan's 240/240, enforced by the preflight) | One source of truth for the caps (RC-4) | R34-04 |

## Part B. Differences from review33 (this correction)

| Module | review33 → review34 | What changed | Finding |
|---|---|---|---|
| `concentration_r32.py` | `6908e80a…3e4d` → `fc5052f8…dffe` | `RULE_VERSION` `.2`; `min_net_gain` removed; gain legs whenever net > 0; UNDETERMINED only for net ≤ 0, decided after every NOT ELIGIBLE leg; `failures_of()` once per (document, field) with `failure_documents`; contractor note names R34-07 | R34-01 (RC-1), R34-08 (RC-6) |
| `score_bcr_r32.py` | `1ba9caaa…9c08` → `3436fe7d…fb63` | `candidate_outcome()`, `CANDIDATE_PRECEDENCE`, `CANDIDATE_RULE`; `result["outcome"]` and `result["candidate"]`; per-field `role` = diagnostic | R34-02 (RC-2) |
| `lane_judge_r32.py` | unchanged `a0b6b7c8…ca45` | Its per-row `critical` list is a report of distinct wrong accepted values, not a failure count; the failure count is `concentration_r32.failures_of()` (RC-6) | R34-08 |
| tests | `test_concentration_r32.py` (12 → 28 tests), `test_score_bcr_r32.py` (16 → 28) | S3a, S3b, S3c, S3c-spread, S5, S1 on the real truth and run set (`r34_scenarios.py`); monotonicity; the stratified-bootstrap justification replaces the refuted `test_net_gain_four_is_the_smallest_whose_interval_can_exclude_zero`; candidate precedence; RC-6 | RC-1, RC-2, RC-6 |

The runner, lane, guard and allowance changes (RC-3, RC-4, RC-5) are in `CORRECTION-REPORT.md` §2 and `LIVE-RUN-CONTRACT.md`; they do not change any scoring rule.

## Interpretation choices carried (Review 34 item-13 rulings in `CORRECTION-REPORT.md` §3)

- The unlabelled `- R0n` suffix base form is accepted as identity on 8 rows (ACCEPT).
- Candidate-level gates apply to every field (ACCEPT; now completed by the conjunctive candidate outcome, RC-2).
- Cross-page identity follows evaluator .10 except on compilations (ACCEPT for cover and enclosure packages; drawing sets F016, F038, F014 ESCALATED to the declaration, R34-06).
- An application `rejected` matches truth `revise and resubmit` and `rejected` ((d1) tolerance, R34-15).
- F069 p2 and p4 identity are NOT_SCORABLE (32 rows; R34-11).
