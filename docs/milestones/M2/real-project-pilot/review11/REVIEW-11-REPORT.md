# M2 Review 11: association safety across bounded history and repeated processing

These four statements are made separately. None of them implies another.

| Question | Status |
|---|---|
| **Correction readiness** | **READY FOR INDEPENDENT CORRECTION REVIEW.** R11-01A (history pruning) and R11-01B (attempt-number collision) are implemented in the isolated candidate `a977364`, frozen, probed, focused-tested and re-scored. The hermetic full-suite run completed, and the package verified. **Limitation:** the full run recorded one new failure, a `TimeoutExpired` in `test_sync_worker.py::test_two_worker_processes_cannot_both_claim`. On the evidence in REGRESSION.md §4 it is environmental, not a regression of this correction, but no second full run was made. The R10-01A/B fixes and the accepted R9 work are carried forward unchanged. |
| **Accuracy** | **Unresolved.** No figure changes: every stored run re-scores identically. Recovery is below 90% (B-1), identity precision is below 98% (B-2), there is no supported variant choice (B-5), and the H-06 BOQ misreads remain (B-6). |
| **Human truth** | **Pending.** Packet v2 is unchanged, and no reviewer is named (B-3). No AI adjudication was done. |
| **Project permission** | **Pending, as recorded.** 29076, 30088 and 30784 only (B-4). No owner answer has been received, and none is inferred. |

**M2 remains CHANGES STILL REQUIRED.** No M3 work and no production promotion is authorized, and this package does not approve M2.

## The invariant now enforced

**Dropping audit history, retrying unrelated fields, failed or budget-stopped attempts, and reopening or restarting a stored row never improve the acceptance of a retained fact. Only newly read compatible source evidence can.**

Reader `.6` enforces this as follows:
- **Attempt order** is a persistent per-row sequence, never derived from the bounded summary list.
- **Durable context.** Each retained dependent fact carries its own small association context (`anchor`). It is stamped when the fact is read, or once from reliably ordered history for evidence stored before `.6`, always before anything is pruned.
- **Unreliable legacy history is never ordered.** Duplicate or missing legacy attempt numbers, and context that may already have been pruned, give a hold with its reason.
- **Storage stays bounded:** 12 summaries and 4 history entries per field, plus one integer per row and a few keys per retained fact.

See [CONTRACT.md](CONTRACT.md), including what the job system does and does not guarantee about concurrent processing of the same row.

## Package

| Document | Contents |
|---|---|
| [CONTRACT.md](CONTRACT.md) | The durable association and attempt-order contract, the legacy rules, concurrency, scope |
| [DISPOSITIONS.md](DISPOSITIONS.md) | R11-01A and R11-01B: how each was reproduced, what changed, each test and its result on `a34d3f8`; the accepted work carried forward |
| [SEQUENCES.md](SEQUENCES.md) | The reviewer's pruning and collision sequences before (reproduced) and after, read by read; the association probe and earlier probes |
| [REGRESSION.md](REGRESSION.md) | What was reproduced, what is new and what is submitted: the module on `a34d3f8` (fails) and `a977364` (passes), focused modules, the hermetic full suite, the re-score |
| [PROVENANCE-AND-FREEZE.md](PROVENANCE-AND-FREEZE.md) | Commit, freeze, the SHA-256 of every changed file, test commands, the temporary environment, tree status |
| `evidence/` | `EVIDENCE-MANIFEST.json`, tests, before and after runs, probes, the re-score, freeze and diff, patch scripts, suite and focused JUnit |

## Results in brief

**R11-01A: Fixed.** ANN, read with revision 02, now stays `held:revision_changed` through every revision-03 re-read, past the history limit. It was accepted at read 6 before. Only a genuine re-read of the decision makes it current again.

**R11-01B: Fixed.**
- Attempts are numbered from a persistent sequence. For writes serialized by the existing job contract, the numbers are unique and increasing across reloads, past both limits. Overlapping writers can still allocate the same number; that case is not guaranteed and not tested (CONTRACT.md §4).
- The legacy targetless revision stays `held:context_changed` for X-SD-9 through every later read. It was recovered at read 15 before.
- Rows already stored with repeated numbers are held; no chronology is invented for them.

**Tests.** All new, on the frozen candidate `a977364`. All are synthetic or scripted; no model was called.
- **Review 11 module:** 9 passed. On `a34d3f8` it fails 5 of 9, all on behaviour; 4 pass there (3 controls, plus one hold `a34d3f8` already produced).
- **The reviewer's nine-module set:** 161 passed.
- **Changed persistence path and compatibility modules:** 127 passed, 7 skipped.
- **Hermetic full suite, run once:** 1,683 tests, 1,645 passed, **3 failed**, 35 skipped, 0 errors.
  - Two failures are pre-existing, with the same test identity and the same failure message as the Review 10 run.
  - The third is **new in this run**: `test_sync_worker.py::test_two_worker_processes_cannot_both_claim`, `subprocess.TimeoutExpired` (a 60 s child-process wait), during a run that was 2.3× slower than usual.
  - The changed code is not imported on that test's path, and the test passes 3/3 in isolation on both `a977364` and `a34d3f8` (the whole module 18/18 on both). It is dispositioned as environmental, not a correction regression. It stays recorded as a failure of this run, and no second full run was made.
- **The probes:** the reviewer's retention, association and earlier probes reproduce exactly on `a34d3f8`. On `a977364` both retention sequences stay held on every read, and the others are identical.

See [REGRESSION.md](REGRESSION.md) §4 for the investigation.
