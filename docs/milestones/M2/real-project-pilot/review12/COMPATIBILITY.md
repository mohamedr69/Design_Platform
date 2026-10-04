# M2 Review 12: legacy anchor reconstruction contract and results

**These expectations were frozen before any code changed.**
- The original, [`evidence/COMPATIBILITY-EXPECTATIONS.md`](evidence/COMPATIBILITY-EXPECTATIONS.md), was saved at 2026-09-29 20:34 (+04:00), after the reviewer's probes had been reproduced on `a977364`.
- The first source patch, `er_patch_r12.py`, came afterwards.
- The contract is implemented by `evidence-reader-2026-09-29.7` (candidate `3d5607d`) and changes **reconstruction only**. These are unchanged:
  - read-time anchors, explicit targets and target revisions;
  - `attempt_seq` and the bounds (12 summaries, 4 history entries per field);
  - evaluator `.9`, and R9, R10 and R11 behaviour.

## The contract

1. **The exact entry, carried.** A pre-`.6` fact's anchor is rebuilt from the exact historical entries in effect at its attempt. They are selected by their recorded order, never looked up again by printed value and never picked by list position. The anchor records them as `identity_entry` and `revision_entry`, each with its value, target, `attempt` / `seq` and `at`.
2. **Reliable order for every entry used,** the context entries as well as the fact. That means one of:
   - `seq` (reader `.6` and later), which is later than every pre-`.6` attempt;
   - a unique numbered attempt: not recorded by two summaries, and not stamped at different times;
   - the **explicit flat `legacy` format**: the single Review 06 reading, ordered before every numbered attempt.

   A missing or non-numeric order is **never** attempt 0. Two different entries with the same order are ambiguous. Either makes the context `unavailable`.
3. **Four distinct outcomes:**

| Outcome | Meaning | Anchor |
|---|---|---|
| **found** | a reliably ordered entry was in effect | its value is used |
| **established absence** | nothing at or before the attempt, and the field's history is below its bound, so nothing can have been pruned | `revision: null`, `revision_known: true` |
| **incompatible** | the revision then in effect was read for another component | `revision_known: false` |
| **unavailable** | order missing or ambiguous, or possibly pruned | `revision_known: false` |

   Only the first two are known. A failed reconstruction never becomes an absence.
4. **Holds.**
   - Identity context `unavailable` gives `held:context_unavailable`.
   - A revision context that is not known gives `held:revision_unverifiable`, when a compatible revision was read after the fact.
5. **Anchors `.6` already saved.** A `.6` reconstructed anchor has no `rule`.
   - It is **re-derived by rule `reconstruct-2` from recorded history**, never from current context. The original is kept as `replaced_anchor`.
   - The next merge stamps the re-derived anchor before it prunes anything; a selection that is not followed by a merge re-derives it on the fly.
   - If the re-derivation is not determinate, the anchor is `unavailable` and the association is held until a genuine re-read.
   - Read-time anchors and `.6` `unavailable` anchors are kept as they are, so neither can be loosened.

## Expected vs actual

**Where "actual" comes from:** `tests/test_m2_review12.py`, run on `3d5607d`, and the reviewer's `legacy_anchor_probe.py` on `frozen-r12`.

| # | Case | Expected (frozen) | Actual on `a977364` | Actual on `3d5607d` |
|---|---|---|---|---|
| E1 | X-SD-1 / rev 02 / ANN (Review 10 reader); X-SD-7 / rev 02; candidate read X-SD-1 / rev 03 | anchor rev `02` from the attempt-1 entry (target X-SD-1); `held:revision_changed`; not recovered | anchor `revision: null, revision_known: true`; ANN `validated`/`correct`; decision `recovered_clean` | anchor rev `02`, `revision_entry.target` X-SD-1, attempt 1; ANN `held`/`held_correct`; `held_only` |
| E2 | As E1 with X-SD-7's revision `09` | identical to E1 | `held_correct` / `held_only` (**differed from E1**) | identical to E1 |
| E3 | E1 with the physical history order shuffled (6 seeds) | identical to E1 | `current` / `recovered_clean` | identical to E1 for all seeds |
| E4 | Identity entry with no attempt number; targetless revision 02 at attempt 1 | `held:context_unavailable` | revision `validated`/`correct`, `recovered_clean` | `held:context_unavailable`; revision `held_unassociated` (still held after a stage merge and reload) |
| E5 | Two different identity entries with the same attempt number | held | held (the test passes there; it is a control, not a demonstration) | held (`unavailable`: ambiguous order) |
| E6 | Control: the flat Review 06 `legacy` reading, before and after a new merge | recovered as before | recovered | recovered |
| E7 | Control: reliable numbered single-attempt history | recovered as before | recovered | recovered |
| E8 | Known absence: no revision when ANN was read; a revision read later | not held for revision | not held | not held; `revision_status: absent` |
| E9 | Revision context may have been pruned; a compatible revision read later | `held:revision_unverifiable` | held (`.6` also treated a full history as indeterminate) | `held:revision_unverifiable` |
| E10 | An erroneous anchor saved by `a977364` (pinned `.6` reader) | re-derived → rev `02` → held; `replaced_anchor` kept | `current` / `recovered_clean` | `held:revision_changed`; anchor rev `02`; `replaced_anchor` = the `.6` anchor |
| E11 | As E10, with the history since pruned | held; a genuine re-read resolves it | `current` / `recovered_clean` | held; after a genuine decision re-read: `current`, `recovered_clean` |
| E12 | Controls: explicit `target_revision`, same context, a read-time anchor over the attempt limit | unchanged | unchanged | unchanged; the read-time anchor is byte-identical |
