# M2 Review 10: association compatibility contract

**This table was written before any code was changed.**
- The original, [`evidence/COMPATIBILITY-TABLE.md`](evidence/COMPATIBILITY-TABLE.md), was saved at 18:08:28, SHA-256 `87e32616…`.
- The first source patch, `er_patch_r10.py`, is timestamped 18:14:04.
- The rules below are the same rules, implemented in `evidence_reader.association_of` (reader `.5`) and consumed by evaluator `.9`.

## Scope

This covers a **dependent fact** of a page's own component (a revision or a decision) that is retained across attempts, and how it relates to the component as it is read now.
- **Where anchors come from:** only from AI evidence and its provenance. That is the current `own:identity` and `own:revision` fields, their history, and the attempt numbers in their provenance.
- **What never enters:** Golden labels and business statuses.
- **Stored facts are not changed.** The association is computed at selection, and stored evidence is never rewritten.

## Terms

**Fact attempt.** The attempt in the fact's own provenance. Review 06 `legacy` counts as 0; Review 07 pages carry their page provenance.

**Current identity value.** The `own:identity` value when that field's status is `completed` or `legacy`. An `incomplete` field anchors nothing.

**Established identity.** The current identity value when its state is `validated`. A `candidate` or `conflict` anchor is never established.

**Identity at the fact's attempt.** The `own:identity` entry (the current one, or one in its history) with the greatest attempt ≤ the fact attempt. It is recorded context, never a target.

**Revision compatible with target T.** The current `own:revision` field (`completed` or `legacy`) qualifies when:
- its recorded `target` is T; or
- it has no target and its identity at its own attempt is T.

Any other revision is **unrelated** and supplies no anchor.

**Revision anchor of a decision.**
- Its recorded `target_revision`.
- Otherwise, the compatible revision in effect at the decision's attempt, when one exists.

## Rules

A fact is `current` only when every known constraint passes.

| # | Retained fact | Current evidence | Association | Evaluator `.9` | Test | On `689d95e` |
|---|---|---|---|---|---|---|
| 1 | Explicit target T, compatible identity and revision | Established identity = T | `current` | Judged with its component; legitimate recovery kept | `test_control_an_explicit_compatible_target_stays_current` | control, passes |
| 2 | Explicit target T | Current identity value ≠ T | `held:target_changed` | Held, associated only by T | Review 09 `test_a_changed_identity_does_not_inherit_the_retained_decision` | (accepted in Review 10) |
| 3 | Explicit target T and revision anchor R | Revision compatible with T ≠ R, whether or not an identity is present | `held:revision_changed` | Held, associated only by T | `test_a_known_revision_constraint_holds_a_decision_without_an_ai_identity` (persisted stage), `test_the_reviewers_synthetic_revision_case` | **fails** |
| 4 | Explicit target T | No current identity value, or a non-established one equal to T; no revision conflict | `by_target` | Associated only by T | `test_a_candidate_anchor_never_establishes_an_association` (explicit part) | **fails** (`current` there) |
| 5 | Targetless legacy fact | Identity at the fact's attempt = current identity value (same attempt, or a reread of the same literal), with no relevant revision change | `not_recorded`, with its `context_identity` | Grouped as before: the supported compatibility behaviour | `test_control_unchanged_legacy_evidence_scores_as_before`, `test_control_a_same_context_retry_keeps_the_legacy_association` | controls, pass |
| 6 | Targetless retained fact | Identity at the fact's attempt ≠ current identity value | `held:context_changed` | Held **and unassociated**: no target invented, never reassigned | `test_a_review08_revision_without_a_target_is_held_when_the_identity_changes` (persisted stage), `test_a_review07_decision_without_a_target_is_held_when_the_identity_changes` (persisted stage) | **fail** |
| 7 | Targetless retained fact | No identity was known at the fact's attempt; one has been read since | `held:context_unknown` | Held and unassociated | `test_a_targetless_fact_read_before_any_identity_is_unresolved_once_one_is_read` | **fails** |
| 8 | Targetless decision | The compatible revision at its attempt ≠ the current compatible revision | `held:revision_changed` | Held and unassociated | `test_a_targetless_decision_is_held_when_its_components_revision_changes` (persisted stage) | **fails** |
| 9 | Targetless fact on a component that never had an AI identity | — | `not_recorded` | Grouped as before | covered by the unchanged Review 06 runs (re-score) | — |
| 10 | Known target T | Only an unrelated revision (another target, or unknown context) | Revision not compared; rules 1, 2 and 4 decide | — | `test_an_unrelated_revision_never_supplies_an_anchor` | control, passes |
| 11 | Any dependent fact | Candidate or conflicting identity anchor | Never `current` on that anchor: a different literal gives rule 2 or 6, the same literal rule 4 or 5 | No accepted association from the anchor's first literal | `test_a_candidate_anchor_never_establishes_an_association` | **fails** |

**Positive controls.**
- **Same-context retry** (rule 5).
- **No-op legacy migration**: unchanged Review 06/07 evidence scores as before (rule 5, and the re-score).
- **A successful reread that genuinely establishes the association**: the revision is re-read with a recorded target equal to the established identity, and becomes `current` and recovered. Test: `test_control_a_reread_that_records_its_target_establishes_the_association`, which passes on `689d95e`.

## Visibility

A held fact is never dropped. A held fact with a target is judged `held_*` in a group anchored by that target. A held fact without a target is judged `held_unassociated`. Neither is ever counted as automatically accepted or recovered.

`target`, `target_revision`, `association` and `context_identity` travel into every judgement, on scored and unscored pages. `evidence_for` returns the full association, including `current_identity`, `current_revision` and `reason`.
