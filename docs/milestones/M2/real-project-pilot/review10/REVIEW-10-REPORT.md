# M2 Review 10: association compatibility correction

These four statements are made separately. None of them implies another.

| Question | Status |
|---|---|
| **Correction readiness** | **READY FOR INDEPENDENT CORRECTION REVIEW.** R10-01A and R10-01B are implemented in the isolated candidate `a34d3f8`, frozen, tested and re-scored. The accepted R9-01, R9-03, R9-04 and ledger-wording work is carried forward unchanged. |
| **Accuracy** | **Unresolved.** No accuracy figure changes: every stored run has identical totals under evaluator .9. Recovery is below 90% (B-1), identity precision is below 98% (B-2), there is no supported variant choice (B-5), and the H-06 BOQ misreads remain (B-6). |
| **Human truth** | **Pending.** Packet v2 is unchanged, and no reviewer is named. The appointment is the owner's choice (B-3). No AI adjudication was done. |
| **Project permission** | **Pending, as recorded.** 29076, 30088 and 30784 only (B-4). No owner answer has been received; none is inferred, and nothing was re-asked. |

**M2 remains CHANGES STILL REQUIRED.** No M3 work and no production promotion is authorized, and this package does not approve M2.

## Scope kept

- **Only association logic changed:** `association_of` and its helpers in the reader (selection), and the grouping and carried metadata in the evaluator.
- **Nothing else:** no change to the read, merge, source-identity, BOQ or ledger code, no business-status policy, and no use of Golden labels at runtime.
- **Boundaries.** No model call, no corpus expansion, no production migration, no backfill and no AI adjudication. The owner's code, services, data, settings, libraries, originals and sealed projects are untouched. Commits exist only on the scratch branch.

## Package

| Document | Contents |
|---|---|
| [COMPATIBILITY.md](COMPATIBILITY.md) | The compatibility table, written before implementation (original in `evidence/`), with each rule's test and its result on `689d95e` |
| [DISPOSITIONS.md](DISPOSITIONS.md) | R10-01A and R10-01B: how each was reproduced, what changed, the probes, the tests; the accepted work carried forward |
| [RESCORE.md](RESCORE.md) | Evaluator .9 on every stored output: totals identical in all 33 runs; 5 documents change only their association route (rule 11), with every outcome unchanged; the association counts |
| [REGRESSION.md](REGRESSION.md) | What was reproduced, what is new and what is submitted: the probes before and after, the module on `689d95e` (fails) and on `a34d3f8` (passes), the focused modules, the hermetic full suite |
| [PROVENANCE-AND-FREEZE.md](PROVENANCE-AND-FREEZE.md) | Commit, freeze, the SHA-256 of every changed file, the diff hunks, test commands, the temporary environment, and the status of every tree |
| `evidence/` | `EVIDENCE-MANIFEST.json`, the original table, tests, the before and after runs, the probes, the re-score, freeze and diff, patch scripts, and suite and focused JUnit |

## Results in brief

**R10-01A: Fixed.**
- **The context of a targetless retained fact** (a Review 06/07 decision, or a revision before reader .4) is the identity in effect at its own attempt, read from recorded provenance and history.
- **When that context differs from the current identity,** or was unknown, the fact is held and unassociated. It is never reassigned, it gets no invented target, and it stays visible.
- **An unchanged context** (a single attempt, or a same-literal retry) keeps the supported original grouping.
- **The reviewer's case:** revision 02 is now `held_unassociated`, and revision recovery for X-SD-9 is `missed`, no longer `recovered_clean`.

**R10-01B: Fixed.**
- **Constraints are checked together.** The identity constraint and then the revision constraint are checked before any `current` or `by_target` association, so a missing identity no longer skips the revision check.
- **Revisions are compared only when compatible** with the same target; unrelated revisions supply no anchor.
- **A candidate or conflicting identity** never establishes `current`.
- **The reviewer's case:** ANN is now `held:revision_changed`, `held_correct`; decision recovery is `held_only`, no longer `recovered_clean`.

**Tests.** New, on the frozen candidate:
- **Review 10 module:** 12 passed. On `689d95e` the same module fails 7 of 12, every one on behaviour; the 5 controls pass there.
- **The reviewer's eight-module set:** 149 passed.
- **Affected BOQ, extraction and AI modules:** 116 passed, 7 skipped.
- **Hermetic full suite:** 1,674 tests, 1,637 passed, 35 skipped, 2 failed. Both failures are the same pre-existing ones, and the only change in test count is the new module.
- **Probes:** the reviewer's association probe and earlier probes reproduce exactly on `689d95e`. On `a34d3f8` both R10-01 cases are held, the controls are unchanged, and the earlier probes are identical.

See [REGRESSION.md](REGRESSION.md).
