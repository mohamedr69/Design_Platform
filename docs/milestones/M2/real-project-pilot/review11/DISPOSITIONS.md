# M2 Review 11: dispositions

- **Candidate:** `a977364` on the isolated scratch repository; parent `a34d3f8`, the Review 10 candidate the independent review inspected.
- **Versions:** `evidence-reader-2026-09-29.6`. Evaluator `.9` is unchanged, as are evidence policy `.4`, the ledger, the parser and all business logic.
- **Contract:** [CONTRACT.md](CONTRACT.md).
- **Sequences before and after:** [SEQUENCES.md](SEQUENCES.md).
- **Regressions:** [`tests/test_m2_review11.py`](evidence/tests/test_m2_review11.py), 9 tests.
  - Every one runs through the real `evidence_stage` on a persisted row reloaded after each attempt, or selects a persisted stored row, and every one asserts the full evaluator's judgement.
  - Rows as the Review 10 reader stored them are built with that exact reader, pinned byte-identical as `tests/fixtures/evidence_reader_r10.py` (SHA-256 `4404abfa…`, the same as `a34d3f8:backend/app/ai/evidence_reader.py`).
  - On `a34d3f8`, 5 fail, all on behaviour, and 4 pass (3 controls, plus one hold that `a34d3f8` already produced). On `a977364`, all 9 pass.

**What caused R11-01.** At `a34d3f8`, selection reconstructed a retained fact's context from bounded field history and from attempt numbers taken from a bounded list. Both can drop or repeat what the reconstruction needed.

**What `.6` does:**
1. Attempts are ordered by a persistent per-row sequence.
2. Each retained dependent fact carries its own durable context (`anchor`), stamped before anything can be pruned.
3. Evidence stored before `.6` is reconstructed once, and only from reliably ordered history. Anything else is held with its reason.

## R11-01A: a held decision became accepted when its old revision left history — **Fixed**

**Reproduced.** The reviewer's `retention_probe.py` was run unchanged on `frozen-r10`, and its output reproduces their `retention-probe-results.json` exactly. ANN (target X-SD-1, no `target_revision`, read with revision 02) is held while revision 03 is re-read. At actual read 6, revision 02 leaves the four-entry history, and ANN becomes `current`, `validated`/`correct`, `recovered_clean`.

**Now.**
- **The anchor.** The decision's `anchor.revision` is `02`, stamped when it was read.
- **For evidence already stored before `.6`,** the anchor is reconstructed from the history at the next merge, before that merge prunes anything.
- **The anchor never changes,** so ANN stays `held:revision_changed` through every re-read (actual reads 2–7 in the probe; 8 in the persisted test).
- **Only a genuine re-read of the decision block** with revision 03 makes it `current` and recovered again.

**Tests:**

| Case | Test | On `a34d3f8` |
|---|---|---|
| Legacy decision (the Review 07 matched-run shape: a target, no target revision), revision 03 re-read eight times past `MAX_FIELD_HISTORY`; then a genuine decision re-read | `test_a_legacy_decision_stays_held_as_its_old_revision_leaves_history` | **fails**: accepted after re-read 5 |
| Explicit `target_revision`, past the history limit | `test_an_explicit_target_revision_stays_held_past_the_history_limit` | control, passes |
| More than two cycles of both limits, with timed-out and ledger budget-stopped attempts interleaved | `test_retention_cycles_with_failed_and_budget_stopped_attempts_never_improve_acceptance` | **fails**: improved at step 8, `held_only` → `recovered_clean` |
| Same-context retries past both limits keep legacy recovery | `test_control_same_context_retries_past_both_limits_keep_legacy_recovery` | control, passes |

## R11-01B: repeated attempt numbers made newer identity evidence look contemporaneous — **Fixed**

**Reproduced.** In the same probe, after the 12-entry cap every new attempt is numbered 13, and the legacy targetless revision 02, read with X-SD-1 at attempt 13, becomes `not_recorded`, `validated`/`correct`, `recovered_clean` for X-SD-9 at actual read 15. In the persisted test on `a34d3f8`, attempt numbers go `… 12, 13, 13, 13, 13`.

**Now.**
- **Attempt order is `seq`,** a persistent per-row sequence. It starts above every attempt number the row has ever recorded, is stored in the row and does not reset on restart. Its uniqueness holds for writes serialized by the existing job contract; overlapping writers can allocate the same number (CONTRACT.md §4). `evidence_stage` numbers attempts with it.
- **The legacy revision's context** is reconstructed once, from its unique attempt 13, and stamped as `anchor.identity = X-SD-1`. It stays `held:context_changed` through every later read (reads 14–20 in the probe; 14–25 in the persisted test).
- **Rows already stored with colliding or missing numbers:** reconstruction refuses to order by them (`unavailable`), and the fact is held.

**Tests:**

| Case | Test | On `a34d3f8` |
|---|---|---|
| Targetless legacy revision stored at attempt 13; identity re-read as X-SD-9 over 12 more reads (the independent collision sequence) | `test_a_targetless_legacy_revision_is_never_recovered_across_the_attempt_limit` | **fails**: recovered at actual read 15 |
| Restart / reload past both limits: numbers unique and increasing; the retained decision's evidence and provenance stable; summaries still bounded | `test_attempt_identity_is_persistent_and_unique_across_reloads_past_both_limits` | **fails**: numbers repeat 13 |
| A row already stored by the Review 10 reader with repeated 13s: no chronology invented, held, still held after reprocessing | `test_a_stored_row_with_colliding_attempt_numbers_invents_no_chronology` | **fails**: recovered |
| Missing attempt order: held. Controls: historical single-attempt Review 07 pages (with and without a target) score as before | `test_missing_attempt_order_is_held_and_single_attempt_history_is_unchanged` | passes (`a34d3f8` already held this row; kept as a control, not claimed as a demonstration) |
| A genuine re-read establishes the association | `test_control_a_legacy_targetless_revision_is_resolved_only_by_a_genuine_reread` | control, passes |

## Accepted work carried forward, unchanged

- **R10-01A/B:** the reviewer's association probe gives identical results on `frozen-r10` and `frozen-r11`, and the Review 10 module (12 tests) passes unchanged.
- **R9-01, R9-03, R9-04 and the ledger wording:** the reviewer's earlier probes give identical results before and after, and the Review 09 module (34 tests) passes unchanged. No read, source-hash, BOQ or ledger code changed.
- **Also unchanged:** packet v2 (blank reviewer fields), the recorded project permissions, and the separation of automatic-acceptance precision from raw-observation precision. No owner answer has been received, and none is assumed.
