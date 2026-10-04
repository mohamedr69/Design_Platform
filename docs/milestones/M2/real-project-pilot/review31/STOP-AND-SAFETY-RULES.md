# Stop and safety rules, shared-response contract and C-from-B check (R31-04)

All three are executable code with tests. The code ships in `scripts/harness/`, and the tests in `tests/*.xml` are re-run by the package checker.

## 1. Stop rules: `stop_rules.StopController` (8 tests)

| Event | Lane | Effect on the lane | Effect on the comparison |
|---|---|---|---|
| Critical acceptance on **resolved** truth | **B** | terminal | **INVALID**: the baseline is incomplete. C does not start, or stops if running. |
| Critical acceptance on **resolved** truth | **C** | terminal, never resumed | **RESULT**: the candidate failed the safety gate. This is a valid comparison outcome, and the scorer reports NOT ELIGIBLE. |
| Critical acceptance on **resolved** truth | **R** (replay or reference-only) or **P** | none | none. It is recorded as a **reference finding**: no live arm stops, and it is never reported as a live safety stop. |
| Critical acceptance on **unresolved** truth | any | none | none. It is reported. |
| Three consecutive provider failures | B | terminal | **INVALID** |
| Three consecutive provider failures | C | terminal | **INCOMPLETE** |
| Three consecutive provider failures | R or P | that lane only | none. The R contrast is incomplete. |
| Breaker, ledger, allowance or counter refusal | any | budget stop, **never raised or reset** | INCOMPLETE if the lane is B or C |
| Binding difference or second writer | any | refused before dispatch | none |

- **Streaks are per lane.** An R or P failure never counts toward B's or C's streak (tested).
- **Tripwire timing.** In a live run, the tripwire checks each B or C document against the frozen labels after the document finishes. In the dry run, the controller replays the lane events and then the post-hoc criticals, and says so.

## 2. Shared responses: `capture_store` (21 tests)

**Keys:**
- `content_key` = sha256 over the document sha256, page, task, tier, profile, variant, model alias, model override, effort, output limit, system-prompt hash, prompt text, image sha256s and schema hash.
- `bound_key` = sha256 over the lane, policy and content key.

| Requirement (R31-04) | How it is met | Test |
|---|---|---|
| One provider dispatch per identical bound fingerprint | a row is **reserved before dispatch** (`BEGIN IMMEDIATE`, unique `bound_key`) and settled after it. A repeat is served from the row. | `test_one_dispatch_per_identical_bound_fingerprint` |
| B and C never share across a different source hash, page, crop, prompt, tier, profile or policy context | lane and policy are part of the bound key, and every context item is part of the content key | `test_lanes_never_share_b_and_c`, `test_any_context_difference_is_a_new_fingerprint` (8 cases), `test_request_settings_are_part_of_the_fingerprint` (4 cases) |
| R is served C's response, and its own requests never reach C or B | R reads C by content key, whatever the outcome, including failures and interrupted dispatches. R-only requests are dispatched once in lane R. | `test_the_reference_lane_reads_c_by_content_and_its_own_requests_never_reach_c`, `test_the_reference_is_served_a_failure_of_c_and_never_resends_it` |
| Reference-only and probe requests cannot alter B or C scores | B and C serve only their own lane. The probe writes only lane-P rows, and C's rows are byte-identical before and after. | `test_the_probe_lane_is_never_served_to_b_or_c`, `test_the_probe_resends_a_seeded_sample_in_its_own_lane_and_never_touches_c` |
| An interrupted capture or resume cannot dispatch the same fingerprint again or lose a charged request | a reserved row without an answer is **charged** and served as `interrupted_charged`. A failed row is served as its failure. | `test_an_interrupted_dispatch_is_charged_and_never_sent_again`, `test_a_failed_request_is_not_redispatched_and_is_served_as_its_failure`, plus the dry run's **resume drill** |
| Every replayed answer keeps its provenance | the serve log records the original seq, lane, policy, model and usage | `test_served_answers_keep_their_original_provenance` |

## 3. C starts from B: `state_check.check_c_start` (5 tests)

C's sandbox is refused unless all of the following hold:
1. B's database **file** still has the sha256 recorded when B finished;
2. the copy has the same **logical** content, meaning every table hashed in rowid order;
3. no document carries evidence whose attempt policy or reader version contains an IG, CA, DR or PA marker;
4. no evidence envelope exists without an attributing attempt;
5. no result-cache row exists for an evidence-reader task.

In the dry run, C, R and the resume sandbox all passed against the recorded final-A hash `2161297e…41b6`.
