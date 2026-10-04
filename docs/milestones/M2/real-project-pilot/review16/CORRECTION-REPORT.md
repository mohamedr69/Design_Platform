# Closing Independent M2 Review 16: preserving BOQ row boundaries and held outcomes

**Status: READY FOR INDEPENDENT CORRECTION REVIEW.** This is not self-approved. Validation and packaging finished; see §5.

**Task.** `TASK-CLOSE-REVIEW-16.md` (`reviews/M2-review-16/`), authorized by the owner, done offline and in isolation.

**What was not done.**
- No model request.
- No change to application source, live services, settings or data.
- No sealed-project access.
- No commit or push to the owner's repository.
- The accepted application `3d5607d99fcebf08ac45f5df937ad615ecc16fb3` is unchanged: its tree is clean, and 9 of its source-file hashes are in `evidence/r16/FREEZE-R16.json`.

**This folder is a new package.** `review05`–`review15`, the reviewer's files, the labels and packet v2 are unchanged. The AI accuracy experiment was **not** started.

## States, reported separately

| State | Status |
|---|---|
| **Correction readiness** | R16-01 and R16-02 are corrected in harness `r16.1` (frozen). Focused tests: **66 passed, 0 failed, 0 errors, 0 skipped, exit code 0.** The reviewer's regression test passes on r16.1 (5/5) and still fails on r15.1 (2 failures + 3 controls). **READY FOR INDEPENDENT CORRECTION REVIEW.** |
| **Extraction accuracy** | Unresolved (B-1, B-2, B-5, B-6). No variant is selected. The synthetic tests measure the harness only. |
| **AI-review provenance and label ambiguities** | Unchanged: an owner-delegated independent AI review, not human and not blind. The holds remain: F09, F10, F06 revision, `+SL23I` / `+SL231`, the `P06/TRANS/R1` role, the divider `Rev.0` target and the page-2 association proposal. |
| **Bounded evaluation permission** | Unchanged. No budget was used, and no allowance was replenished or cap raised. The historical deviation marker is re-copied byte-identically. |
| **Sealed-validation readiness** | Not ready. The sealed cohort is unopened. |

M2 remains **CHANGES STILL REQUIRED**. There is no M3 and no production adoption.

## 1. Baseline, recorded before any edit

The submitted r15.1 source hashes are those of `review15/evidence/r15/FREEZE-R15.json`; the checker confirms the Review 15 package is unchanged.

**The reviewer's regression test** was run byte-identically on r15.1 (`evidence/r16/regression/review16_contract_on_r15.*`):
- **2 failed:** `test_verified_source_position_constrains_all_fallback_matches[True]` and `[False]`. Both fail with `assert ('below-anchor', 1) not in [...]`.
- **3 passed:** these are **controls** (`test_above_anchor_positive_control[False|True]`, `test_scored_values_still_cannot_choose_a_truth_row`).
- **Exit code 1.**

**The reviewer's association probe** on r15.1 (`evidence/r16/probes/assoc-r15/`):
- the lower row crosses the verified row, with and without the anchor emitted;
- the two geometry-held rows are reported as `extra_row`.

**One invocation error is recorded, not hidden.** The first run of the reviewer's test used the copy named `test_review16_contract.reviewer-original.py`, which pytest cannot import. That gave a collection error (exit code 2) and ran no tests. Its logs are kept as `*.invocation-error.*`. The recorded runs use a byte-identical copy under the original filename (sha256 `eb79ef1e…`, equal to the reviewer's file).

## 2. R16-01: the combined matching contract (r16.1)

**The rule** (`boq_contract.join_rows`, contract `r2x-boq-contract-2026-09-30.r16.1`): on a page, **every verified truth row is a boundary for every confirmed association**, whether or not an emitted row was matched to it. In order:

1. **Consistency check.** Verified positions must increase with print order. If they contradict it, the whole page is held (reason: `verified positions contradict print order`). Nothing is guessed.
2. **Geometry.** Pairing on verified position (physical identity) works exactly as in r15.1. A verified row with nothing emitted near it is **missed**, and it **remains a boundary**.
3. **Intervals.** Unpositioned truth rows are placed by print order, and unpositioned emitted rows by their position (the same render coordinates as the verified rows), each into the interval between the enclosing verified rows.
4. **Fallback.** Order and description only, **inside one interval**. A tie within the interval is held, with every candidate and a reason.

**Unchanged:**
- **Part number and quantity never choose a truth row.**
- Punctuation-sensitive part comparison and typed quantity comparison are unchanged; a test checks this against r15.1.
- The geometry tolerance is unchanged, and no verified position is removed.
- `boq_harness.py` (the R15-01 durable allowance) and `overlay.py` (R15-03 annotation-only) are **byte-identical to r15.1**.

**Tests** (`tests/test_r16_boundaries.py`, 11). They assert the **global property**: no confirmed pair crosses any verified row. They cover:
- the reviewer's lower-row case, with and without the middle row. The row is never matched to ordinal 1; it is matched to ordinal 3 (description evidence) or held; ordinal 1 is missed; and the verified middle row, when not emitted, is missed but still bounds the match;
- the above-anchor control in both input orders;
- a mixed page with three verified rows and unpositioned rows, with exact expected pairs;
- 20 shuffled input orders giving the same join;
- **300 seeded random pages** with the property checked on each, and complete emitted accounting;
- unchanged joins when only the scored values change;
- the sparse and full duplicate controls;
- contradictory verified positions;
- value comparisons unchanged from r15.1.

A companion test shows **r15.1 crossing** the verified row on the same inputs.

## 3. R16-02: held rows are carried through the actual replay path

**The fix.**
- **`replay_core.py`** is the reporting path. `replay_boq_r16.py` calls `replay_core.replay_sheet`; a test checks this.
- An emitted row in the join's `held` map keeps `join = held`, its **candidate truth ordinals** and its **reason** in the row outcome (`held_ambiguous_join`) and in the summary.
- It gets **no match, value-accuracy or blind-accuracy credit** (`truth`, `reader_right` and `blind_right` are all null).
- `extra_row` is reserved for rows the join lists as unmatched. A stored row that cannot be linked to any emitted row is `unlinked_row`.
- **Accounting:** every emitted row is exactly one of matched / held / unmatched, and every truth row is exactly one of matched / held candidate / missed. Both are checked on every replay.

**The integration test** (`tests/test_r16_replay_integration.py`, 5) runs `replay_sheet` on a synthetic extraction, a synthetic stored run and verified truth:
- rows at y = 95 and y = 105 against the verified row 6 at y = 100: both **held**, candidates `[6]`, reason `geometry…`, no credit;
- **controls:** a genuine extra row gives `extra_row`; truth row 9 is **missed**; an unambiguous geometry match (truth 8, emitted quantity 4 against 1) gives `caught_wrong_accepted`;
- summary `{held_ambiguous_join: 2, caught_wrong_accepted: 1, extra_row: 1}`; emitted accounting 1 matched / 2 held / 1 unmatched; truth accounting 1 matched / 1 held candidate / 1 missed;
- **on r15.1** the same inputs give `held = {L0: [6], L1: [6]}`, yet both are reported as `extra_row` (the defect).

## 4. Saved outputs and earlier probes (re-run on the frozen r16.1)

| Check | Result |
|---|---|
| **Stored BOQ replay** (B/C × original / amended labels × H-06 geometry off / on; 8 runs) | **0 row deltas** against both the recorded r14 replay and the r15 replay: truth assignment, join state, outcome and `blind_right` all equal. 0 held rows. Accounting complete in all 8. Outcomes: B {caught 2, confirmed 5, held-blind-right 17, extra 1}; C {confirmed 16, caught 4, held-blind-right 14, extra 1, held-unread 3}. |
| **Review 15 probes on r16.1** | Allowance **5 persisted + 7 on resume = 12**. The sparse duplicate is still held at `[6, 37]`. **All 5 overlay cases keep their error.** |
| **Review 16 association probe** | r15.1: crossed (anchor emitted and not); held rows reported as extra. **r16.1: no crossing; both held rows `held_ambiguous_join`** (via the r16 reporting path). |
| **Stored small-batch overlay** (evaluator `.9`, original and amended labels) | **B = 3, C = 2**, each fact found in its own context (`default|EV1`, `default|EV2`); det / A = 0. Unchanged. |

These exposed runs **do not validate unseen accuracy**.

## 5. Validation and freeze

- **Frozen:** `evidence/r16/FREEZE-R16.json`. It lists 19 files and the application source hashes; `boq_harness` and `overlay` are recorded as byte-identical to r15.1.
- **Focused tests:** the 51 existing plus 15 new tests, run once on the frozen version. Result: **66 passed, 0 failed, 0 errors, 0 skipped. Pytest's own exit code: 0.** Full log and JUnit are in `evidence/r16/regression/`.
- **Diffs** (`evidence/r16/diff/`, line endings ignored):
  - `boq_contract.py`: +60 / −28 (`join_rows` only);
  - `replay_core.py`, against the r15 replay script: the reporting path extracted into a module, with held-state propagation and accounting.
- **Not run:** the full backend suite. This is a harness-only correction with no changed application dependency.
- **The package checker** was run after the final edit: `evidence/PACKAGE-CHECK.json`, `ok`.
