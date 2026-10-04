# M2 Review 12: dispositions

- **Candidate:** `3d5607d` on the isolated scratch repository; parent `a977364`, the Review 11 candidate the independent review inspected.
- **Version:** `evidence-reader-2026-09-29.7` (reconstruction only). Evaluator `.9`, evidence policy `.4`, the ledger, the parser and all business logic are unchanged.
- **Contract, with frozen expectations and actual results:** [COMPATIBILITY.md](COMPATIBILITY.md).
- **Regressions:** [`tests/test_m2_review12.py`](evidence/tests/test_m2_review12.py), 11 tests.
  - **Prior-reader shapes:** built with the pinned readers `tests/fixtures/evidence_reader_r10.py` (`a34d3f8`) and `tests/fixtures/evidence_reader_r11.py` (`a977364`, byte-identical, SHA-256 `d9002bc1…`).
  - **Stage checks:** the real evidence stage on a persisted row, reloaded after each attempt.
  - **What every test checks:** the accessor's association and the full evaluator's judgement, not only a private helper or the serialized anchor.
  - **Results:** on `a977364`, 6 fail, all on behaviour, and 5 pass (controls). On `3d5607d`, 11 pass.

## R12-01A: a repeated revision literal selected another historical entry — **Fixed**

**Reproduced first.** The reviewer's `legacy_anchor_probe.py` on `frozen-r11` reproduces their `legacy-anchor-probe-results.json` exactly.
- **The sequence:** the Review 10 reader stores X-SD-1 / rev 02 / ANN, then X-SD-7 / rev 02; the candidate then reads X-SD-1 / rev 03.
- **The result on `a977364`:** the decision's anchor is reconstructed as `revision: null, revision_known: true`, so ANN is `validated`/`correct`, `recovered_clean`.
- **The control:** with X-SD-7's revision at `09`, the same ANN was held. The outcome depended on an unrelated drawing's literal.

**Cause.** `.6` looked up the revision *value* in effect, then searched current and history again for the first entry with that value. It found X-SD-7's `02`, judged it incompatible, and still marked the constraint known.

**Now.**
- **Reconstruction carries the exact entry** in effect at the fact's attempt, selected by reliable order.
- **Incompatible or unavailable context is never "known absence"**, and no entry is reselected by value.
- **On `frozen-r12`:** the anchor is revision `02`, `revision_status: found`, from the attempt-1 entry with target X-SD-1, so ANN is `held`/`held_correct`, `held_only`.
- **The control gives the same outcome.** Shuffling the physical history (6 seeds) leaves the outcome unchanged.

**Tests (on `a977364`):**

| Test | Result there |
|---|---|
| `test_a_repeated_revision_literal_of_another_drawing_never_removes_the_constraint` (persisted stage) | **fails:** "ANN was read with revision 02" |
| `test_the_unrelated_drawings_revision_literal_does_not_change_the_outcome` (persisted stage) | **fails:** `current` vs `held:revision_changed` |
| `test_selection_does_not_depend_on_the_physical_order_of_history` | **fails:** `current` / `recovered_clean` |
| `test_explicit_target_revision_and_same_context_controls` | control, passes |

## R12-01B: a context entry without order became attempt zero — **Fixed**

**Reproduced first** by the same probe (`missing_identity_order`). Identity X-SD-9 has no attempt number, and the targetless revision 02 is at attempt 1. On `a977364` the revision was recovered.

**Now.**
- **Every entry used for context needs reliable order:** `seq`, a unique numbered attempt, or the explicit flat `legacy` reading.
- **A missing order is never attempt 0,** and two different entries with one order are ambiguous. Either makes the context `unavailable`, and the association is held with its reason.
- **The flat `legacy` compatibility and reliable numbered history are unchanged** (controls).
- **On `frozen-r12`:** revision 02 is `held_unassociated` (`held:context_unavailable`).

**Tests (on `a977364`):**

| Test | Result there |
|---|---|
| `test_a_context_entry_without_order_is_never_attempt_zero` (probe shape, then a persisted stage merge and reload) | **fails:** `recovered_clean` |
| `test_two_different_context_entries_with_one_order_are_ambiguous` | passes there; kept as a control, **not** claimed as a demonstration |
| `test_controls_flat_legacy_numbered_history_and_known_absence` | control, passes (its `revision_status` check tolerates the key's absence there) |
| `test_a_revision_context_that_may_have_been_pruned_is_unverifiable_never_absent` | passes there (`.6` treated a full history as indeterminate); a control |

## Anchors `a977364` already saved — conservative compatibility

**The case.** `a977364` may have saved an erroneous reconstructed anchor. This is shown here only in synthetic data built with the pinned `.6` reader. It is **not** claimed to exist in production, and no live backfill was run.

**The handling.**
- **Such an anchor is not trusted.** It is re-derived from recorded history, never from current context, and the original is kept as `replaced_anchor`.
- **If history no longer allows it,** the association is held until a genuine re-read.
- **Read-time anchors are never rewritten.**

| Test | On `a977364` |
|---|---|
| `test_an_erroneous_anchor_saved_by_a977364_is_re_derived_from_history_not_trusted` | **fails:** recovered |
| `test_an_erroneous_saved_anchor_whose_history_is_gone_is_held_until_a_genuine_reread` | **fails:** recovered |
| `test_read_time_anchors_are_never_rewritten` (over the attempt limit) | control, passes |

## A defect caught during validation (inside this correction, before the freeze)

**The defect.** The first `.7` patch named the reconstruction's entry summary `_brief`. That shadowed the BOQ verifier's existing `_brief(row)`, and two BOQ verifier tests failed with `KeyError` in the 188-test set:
- `test_evidence_reader.py::test_boq_rows_are_read_blind_and_compared_afterwards`;
- `test_m2_review09.py::test_the_normal_verifier_carries_the_readers_description_and_keeps_every_line`.

**The fix.** The helper was renamed `_entry_brief` (`er_patch_r12b.py`) **before** the freeze. An AST check then confirmed that neither `evidence_reader.py` nor `m2_eval5.py` has a duplicate top-level definition. No test was changed. The frozen candidate `3d5607d` contains the fix; no reported result comes from the defective state.

## Accepted work carried forward, unchanged

**Probes (on `frozen-r11` and `frozen-r12`):**
- the retention sequences: identical, both held on every read;
- the association probe: identical;
- the R9 probes: identical.

**Behaviour.** Persistent attempt order, durable read-time anchors, the bounds, the R9 behaviour (illegible reads, source hash, BOQ item presence, ledger wording) and the R10 behaviour are unchanged.

**What the rest of the package covers:**

| Topic | Where |
|---|---|
| The full test sets | [REGRESSION.md](REGRESSION.md) |
| Re-scoring the 33 stored runs | [RESCORE.md](RESCORE.md) |
| Handoff corrections: the Review 11 timeout, the owner permission | [REVIEW-12-REPORT.md](REVIEW-12-REPORT.md) |
