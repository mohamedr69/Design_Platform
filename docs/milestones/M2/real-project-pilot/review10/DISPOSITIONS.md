# M2 Review 10: dispositions

- **Candidate:** `a34d3f8` on the isolated scratch repository; parent `689d95e`, the Review 09 candidate the independent review inspected.
- **Versions:** `evidence-reader-2026-09-29.5` (selection and association only) and evaluator `m2-pilot-eval-2026-09-29.9`.
- **Unchanged:** evidence policy `.4` (usable reads, heading and item presence), the ledger, the parser, profiles, register and request cache.
- **Contract:** [COMPATIBILITY.md](COMPATIBILITY.md), whose table was written before implementation.
- **Regressions:** [`tests/test_m2_review10.py`](evidence/tests/test_m2_review10.py), 12 tests. On `689d95e`, 7 fail, all on behaviour, and 5 controls pass. On `a34d3f8`, all pass.

## R10-01A: a targetless legacy fact inherited a later identity — **Fixed**

**Reproduced.** The reviewer's `association_probe.py` was run unchanged on `frozen-r9`, and its output reproduces their `association-probe-results.json` exactly.

- **`review08_revision_without_target`.** A Review 08 revision 02 has no target. After identity X-SD-9 is re-read, it was emitted as `not_recorded`, `validated`, `correct`, and the revision was `recovered_clean` for X-SD-9.
- **`legacy_changed_identity`.** The same happened to the Review 07 decision ANN.

**Now.**
- **The component a targetless fact was read with** is taken from recorded evidence. It is the identity in effect at the fact's own attempt, from the identity field's current entry or its history, with attempt numbers from provenance. It is never invented, and never assumed from `page + component=own`.
- **When that context differs from the current identity,** the fact is `held:context_changed`, with its recorded `context_identity`.
- **When no identity was known at the fact's attempt** but one has been read since, it is `held:context_unknown`.
- **A targetless decision whose component's compatible revision changed** is `held:revision_changed`.
- **What evaluator .9 does with held targetless facts.** They form their own unassociated group, are judged `held_unassociated`, stay visible, and never count as accepted or recovered. The stored fact, its provenance and its (absent) target are unchanged.
- **Compatibility is preserved, and bounded.** A targetless fact whose recorded context is the current identity (the same attempt, or a reread of the same literal) remains `not_recorded` and is grouped exactly as before, as is a component that never had an AI identity.
  - This is the supported behaviour for unchanged historical single-attempt evidence, and the only exception.
  - It rests on recorded provenance, not on the expected label matching.
- **Probes on the successor:**
  - `review08_revision_without_target`: revision 02 `held`, `held_unassociated`, `held:context_changed`; revision recovery `missed`.
  - `legacy_changed_identity`: ANN `held_unassociated`.
  - `legacy_unchanged_control` is unchanged: ANN `correct`, `recovered_clean`.

**Tests:**

| Case | Test | `689d95e` |
|---|---|---|
| Review 08 revision without a target; identity re-read as X-SD-9 (persisted stage) | `test_a_review08_revision_without_a_target_is_held_when_the_identity_changes` | fails: `correct` / `recovered_clean` |
| Review 07 decision without a target; identity changed (persisted stage) | `test_a_review07_decision_without_a_target_is_held_when_the_identity_changes` | fails |
| Targetless decision; its component's revision changed (persisted stage) | `test_a_targetless_decision_is_held_when_its_components_revision_changes` | fails |
| Targetless fact read before any identity; an identity read since | `test_a_targetless_fact_read_before_any_identity_is_unresolved_once_one_is_read` | fails |
| Same-context retry (persisted stage) | `test_control_a_same_context_retry_keeps_the_legacy_association` | control, passes |
| No-op legacy migration (Review 07 page shape and Review 06 flat shape) | `test_control_unchanged_legacy_evidence_scores_as_before` | control, passes |
| A reread that records its target establishes the association (persisted stage) | `test_control_a_reread_that_records_its_target_establishes_the_association` | control, passes |

## R10-01B: a missing identity bypassed a known revision constraint — **Fixed**

**Reproduced** by the reviewer's case `known_revision_without_identity`.
- **The setup:** a decision ANN for X-SD-1 / revision 02, with no AI identity, and a later revision 03 for X-SD-1.
- **The result on `689d95e`:** `by_target`, `validated`, `correct`, and the decision was `recovered_clean` for revision 03.

**Now.**
- **Every known constraint is checked before an association is accepted.** The identity check (rule 2) and then the revision check (rule 3) come before any `current` or `by_target` answer. A missing identity no longer returns early.
- **The revision anchor.** It is the decision's `target_revision`, or else the revision compatible with its target at its own attempt. It is compared only with the revision now **compatible with the same target**: a revision recorded for that target, or a targetless one whose identity at its attempt was that target.
- **Unrelated revisions supply no anchor.** Another component's revision, or one of unknown context, is not compared.
- **An anchor that is not established cannot make a fact `current`** (rule 11). A candidate or conflicting identity equal to the target gives `by_target`; a different literal gives held.
- **Metadata carried.** `target_revision`, the association and the recorded context travel through selection, evaluator grouping and every judgement.
- **Probe on the successor:** `known_revision_without_identity` gives ANN `held`, `held_correct`, `held:revision_changed`, decision recovery `held_only` (not recovered), revision `recovered_clean`.

**Tests:**

| Case | Test | `689d95e` |
|---|---|---|
| The decision's target comes from the deterministic reading; no AI identity field; the same target then reads revision 03 (persisted stage, real `evidence_stage`) | `test_a_known_revision_constraint_holds_a_decision_without_an_ai_identity` | fails: `correct` / `recovered_clean` |
| The reviewer's synthetic shape | `test_the_reviewers_synthetic_revision_case` | fails |
| An unrelated component's revision, and a revision of unknown context | `test_an_unrelated_revision_never_supplies_an_anchor` | control, passes |
| Candidate anchor: explicit (same literal) and targetless (different literal) | `test_a_candidate_anchor_never_establishes_an_association` | fails: `current` on a candidate anchor |
| An explicit compatible target stays current (persisted stage) | `test_control_an_explicit_compatible_target_stays_current` | control, passes |

## Accepted work carried forward, unchanged

**Code.** R9-01 (usable reads), R9-03 (source identity), R9-04 (BOQ item presence) and the ledger wording are untouched: evidence policy `.4`, ledger `.2`, and no change to `_read_page`, `merge_evidence`, the source checks in `evidence_for`, or `validate_boq_row`.

**Evidence:**
- The Review 09 module (34 tests) and the Review 08 module (27 tests) pass unchanged.
- The reviewer's earlier independent probes (`probes.py` in the Review 10 folder) give **identical** results on `frozen-r9` and on `frozen-r10`. On `frozen-r9` they reproduce the reviewer's `probe-results.json` exactly.

**Packet v2, permissions and precision separation** are unchanged. Packet v2 has blank reviewer fields. Project permissions are as recorded. Automatic-acceptance precision is still reported separately from raw-observation precision. No owner answer has been received, and none is assumed.
