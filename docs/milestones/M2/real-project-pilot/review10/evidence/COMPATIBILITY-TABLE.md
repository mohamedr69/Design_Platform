# M2 Review 10: association compatibility table (written before implementation)

**Scope.** This covers a *dependent* fact of a page's own component (a revision or a decision) that is retained across attempts, and how it relates to the component as it is read now. Anchors come only from AI evidence and its provenance: the current `own:identity` and `own:revision` fields, their history, and the attempt numbers in their provenance. Golden labels and business statuses never enter.

## Terms

**Fact attempt.** The attempt in the fact's own provenance. Review 06 flat evidence is `legacy` and counts as attempt 0; Review 07 pages carry their page provenance.

**Current identity value.** The value of the `own:identity` field when its status is `completed` or `legacy`. An `incomplete` field is an unusable read and anchors nothing.

**Established identity.** The current identity value when its current state is `validated`. A `candidate` or `conflict` anchor is never established: its first literal is not proof.

**Identity at the fact's attempt.** The value of the `own:identity` entry (the current one or one in its history) with the greatest attempt ≤ the fact attempt. It is recorded evidence of the component the fact was read with, not an invented target.

**Revision compatible with a target T.** The current `own:revision` field (`completed` or `legacy`) qualifies when:
- its recorded `target` is T; or
- it has no target and its identity at its own attempt is T.

Any other revision (another component's, or one whose context is unknown) is **unrelated** and never supplies an anchor.

**Revision anchor of a decision.**
- Its recorded `target_revision`.
- Otherwise, for a retained decision, the compatible revision value at the decision's attempt (from the revision field's current entry or history), when one exists.

## Rules, checked in order. A fact is `current` only when every known constraint passes.

| # | Retained fact | Current evidence | Association | Evaluator |
|---|---|---|---|---|
| 1 | Explicit target T; the identity and, where known and comparable, the revision are compatible | Established identity = T | `current` | Judged with its component; legitimate recovery kept |
| 2 | Explicit target T | Current identity value ≠ T (established or not) | `held:target_changed` | Held, associated only by T; never recovered for the new identity |
| 3 | Explicit target T and revision anchor R | Revision compatible with T ≠ R (whether or not an identity is present) | `held:revision_changed` | Held, associated only by T |
| 4 | Explicit target T | No current identity value, or a non-established one equal to T; no revision conflict | `by_target` | Associated only by T, never by the page's other component |
| 5 | Targetless legacy fact | Identity at the fact's attempt = current identity value (for example the same attempt, or a reread of the same literal), and no relevant revision changed | `not_recorded` (context unchanged) | Grouped as before: the supported compatibility behaviour for unchanged historical single-attempt evidence |
| 6 | Targetless retained fact | Identity at the fact's attempt ≠ current identity value | `held:context_changed` (the recorded context identity is kept) | Held and unassociated: no target is invented, and it is never reassigned |
| 7 | Targetless retained fact | No identity was known at the fact's attempt, but a later attempt read one | `held:context_unknown` | Held and unassociated |
| 8 | Targetless decision | A compatible revision at the decision's attempt ≠ the current compatible revision | `held:revision_changed` | Held and unassociated |
| 9 | Targetless fact on a component that never had an AI identity | — | `not_recorded` | Grouped as before (nothing to compare) |
| 10 | Known target T | Only an unrelated revision exists (another target, or an unknown context) | Revision not compared; rules 1, 2 and 4 decide | — |
| 11 | Any dependent fact | Candidate or conflicting identity anchor | Never `current` on that anchor: a different literal gives rule 2 or 6 (held); the same literal gives rule 4 or 5 | No accepted association from the anchor's first literal |

## Positive controls

- **Same-context retry:** the identity is re-read as the same literal, so the fact stays `current` or `not_recorded`.
- **No-op legacy migration:** unchanged single-attempt Review 06/07 evidence is `not_recorded` and scores exactly as before.
- **Successful reread that genuinely establishes the association:** a later completed read of the dependent fact records a target equal to the established identity, and the fact becomes `current`.

## Every fact stays visible

A held fact is never dropped. It is judged `held_*` (`held_unassociated` when it has no target) and is never counted as automatically accepted or recovered. `target`, `target_revision`, `association` and the recorded context identity travel into every judgement.
