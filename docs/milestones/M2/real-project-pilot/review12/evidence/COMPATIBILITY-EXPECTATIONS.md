# M2 Review 12: compatibility expectations for legacy anchor reconstruction (frozen before code changes)

**Scope.** This covers the reconstruction of a durable `anchor` for a retained dependent fact (`own:revision` or `own:decision`) stored before reader `.6`, together with the handling of anchors that reader `.6` (`a977364`) already reconstructed and saved.

**Unchanged.** Read-time anchors, explicit targets and target revisions, persistent `attempt_seq`, the bounds (12 summaries, 4 history entries per field), and R9/R10/R11 behaviour.

## Principles

1. **Carry the exact entry.** Reconstruction carries the **exact** historical entry in effect at the fact's attempt: its value, target, and its order evidence (`attempt` / `seq`). Nothing is looked up again by printed value.
2. **Order must be reliable for every entry used.** It must hold for the dependent fact **and** for every context entry used, whether identity or revision. Reliable means one of:
   - a unique numbered attempt: not recorded by two attempt summaries, and not stamped at different times on field entries;
   - `seq` (reader `.6` and later), which is always later than any pre-`.6` attempt;
   - the explicit flat `legacy` format: the single Review 06 reading of its envelope, which precedes every numbered attempt.

   A missing or non-numeric order never becomes attempt 0. Two different entries with the same order are ambiguous. Neither is picked by list position.
3. **Four outcomes stay distinct:**

| Outcome | Meaning |
|---|---|
| **found** | a reliably ordered entry was in effect |
| **absent (established)** | no entry at or before the attempt, and nothing can have been pruned: the field's history is below its bound |
| **incompatible** | the revision in effect then was read for another component |
| **unavailable** | order is missing or ambiguous, or the entry may have been pruned |

   Only *found* and *absent* are known. *Incompatible* and *unavailable* never become `revision=null, revision_known=true`.
4. **Holds.**
   - A targetless fact whose identity context is *unavailable* is held (`held:context_unavailable`).
   - A decision whose revision context is *incompatible* or *unavailable* is held (`held:revision_unverifiable`) when a compatible revision was read after it. It is never accepted by default.
5. **Anchors `.6` already saved.** A `.6` reconstructed anchor carries no rule marker and may have been selected by value.
   - It is **re-derived from the recorded history** under these rules, never from current context. The original is kept as `replaced_anchor` for audit.
   - If the re-derivation is not determinate, the anchor becomes *unavailable* and the association is held until a genuine re-read.
   - Read-time anchors (`source: read`) are trustworthy and never rewritten.

## Expected results (frozen)

| # | Case | Expected association / evaluator |
|---|---|---|
| E1 | Review 10 reader: X-SD-1 / rev 02 / ANN (target X-SD-1, no target revision); then X-SD-7 / rev 02; then the candidate reads X-SD-1 / rev 03, with no decision re-read | anchor revision `02`, from the exact attempt-1 entry (target X-SD-1); ANN `held:revision_changed`; evaluator ANN `held`, not `correct`; decision recovery not `recovered_clean` |
| E2 | As E1, but X-SD-7's revision is `09` | **identical outcome to E1** |
| E3 | As E1, with the physical history order shuffled (reliable numbered attempts) | identical anchor and outcome to E1 |
| E4 | Targetless revision 02 at attempt 1; its identity entry has **no** attempt number | `held:context_unavailable`; not recovered |
| E5 | Two different identity entries recorded with the same attempt number | context `unavailable`, held |
| E6 | Control: the flat Review 06 `legacy` single reading, unchanged | `not_recorded`; recovered as before |
| E7 | Control: reliable numbered single-attempt history, unchanged | `not_recorded` / `current`; recovered as before |
| E8 | Known absence: the decision was read when no revision existed, history below its bound, and a revision was read later | not held for revision (an established absence imposes no constraint) |
| E9 | Unavailable / pruned: the revision entry in effect at the decision's attempt may have been pruned, and a compatible revision was read later | `held:revision_unverifiable` |
| E10 | An anchor saved by `a977364` with the erroneous `revision=null, revision_known=true` (built by the pinned `.6` reader) | re-derived from history → revision `02` → held; `replaced_anchor` kept |
| E11 | As E10, but the history has since been pruned so that no re-derivation is possible | anchor unavailable → `held:revision_unverifiable`; a genuine decision re-read resolves it (current, recovered) |
| E12 | Controls: explicit `target_revision`, same-context retry, a genuine compatible re-read, read-time anchors not rewritten | unchanged: held / recovered / current / anchors byte-identical |
