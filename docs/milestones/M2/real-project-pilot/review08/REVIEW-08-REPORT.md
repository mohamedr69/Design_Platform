# M2 Review 08: correction package

**Verdict: READY FOR INDEPENDENT CORRECTION REVIEW.**

- **The four corrections** (R8-01 to R8-04) are implemented in the isolated candidate `e02a8c1`, frozen and tested:
  - field-level evidence lifecycle;
  - context-bound evidence selection;
  - authoritative persisted ledger policy;
  - heading as a non-item outcome.
- **The human-review handoff is prepared:** packet v2 and the findings index.
- **Accepting these corrections would not accept M2.** M2 stays **CHANGES STILL REQUIRED**, with its accuracy and human-truth blockers unchanged (below).
- **Nothing is authorized beyond that:** no M3 work and no production promotion.

## Boundaries kept

| Item | Status |
|---|---|
| Owner's tree | No code change: HEAD `2221b43` plus the uncommitted Candidate C, whose 11 frozen hashes still match. The only additions are this folder and the appended response in `M2-REVIEW-RESPONSE.md`. |
| Live services, settings, data, `.env`, originals, sealed projects | Not touched. The sealed cohort was not inspected. |
| Where the work happened | The isolated scratch repository `C:/t/iso/ep-platform`, which is never served. Commit `e02a8c1`, worktree `C:/t/iso/frozen-r8` (no `.env`). |
| Review 07 freeze and evaluator amendment | Kept as history: `c9a1a14`, `1455f8b`, and the `review07/` package and stored outputs unchanged |
| Real models | **None called.** Every AI answer in the tests is scripted. The metrics re-score outputs stored by earlier rounds. No new accuracy experiment was run. |
| Owner choices | Project-model permission and the reviewer appointment are **still pending**. No new reply was received; no permission was re-requested or widened. |
| Commits | Only on the scratch branch. Nothing in the owner's repository, and no push. |

## Package

| Document | Contents |
|---|---|
| [DISPOSITIONS.md](DISPOSITIONS.md) | R8-01 to R8-04 and the handoff: the rules, the before and after, and the test for each requirement |
| [METRICS.md](METRICS.md) | Evaluator .7 with declared contexts, which reproduces .6 on every stored run; automatic-acceptance and raw-observation precision kept apart; frozen and unresolved-excluded views; pending disputes by group |
| [REGRESSION.md](REGRESSION.md) | The Review 08 module on the prior candidate (fails) and on the candidate (passes); the reviewer's probes; focused and compatibility modules; the hermetic full suite; changed assertions |
| [PROVENANCE-AND-FREEZE.md](PROVENANCE-AND-FREEZE.md) | Commit, parent, frozen worktree, the SHA-256 of every changed file, and what was not touched |
| [human-review-packet-v2/](human-review-packet-v2/INSTRUCTIONS-v2.md) | Versioned successor of the Review 07 packet, with [FINDINGS-INDEX.md](human-review-packet-v2/FINDINGS-INDEX.md). Prepared, **not** reviewed. |
| `evidence/` | `EVIDENCE-MANIFEST.json` (evidence files, package files, candidate file hashes, and the owner's Candidate C check); tests; probes; prior-candidate run; re-scores; metrics; freeze and diff; patch scripts; suite logs and JUnit |

## Results in brief

**R8-01: Fixed.**
- Discovery and every required read now record their own outcome: `completed`, `absent_by_discovery`, `incomplete:*`, `failed:<kind>`, `budget` or `not_attempted`.
- A page is `evidence` only when every required read completed or was absent by discovery.
- Merging is field by field, and only a completed read replaces a field. A completed, source-supported negative supersedes. Failures, budget refusals, absence by discovery and unreadable results never do.
- Last-good evidence keeps its original provenance, replaced values go to history, and failed attempts are appended.
- Six scenarios run through the real `evidence_stage` on persisted rows with a scripted provider, reloaded after every step. The reviewer's two probes are included.

**R8-02: Fixed.**
- Evidence is requested for an explicit source hash, profile, variant and, optionally, policies (`evidence_for`). The answer is `current`, `pending`, `unavailable` or `stale`, and another context's evidence is never substituted.
- History is available only as history (`last_known`).
- An unknown legacy profile is used only when the caller declares it.
- Evaluator .7 scores AI evidence only for the run's declared context. Under each run's own context it reproduces every stored .6 result, and the wrong-context controls score no AI evidence.

**R8-03: Fixed.**
- A scope's persisted limits are authoritative. Another handle, process or restart supplying different limits, looser or stricter, is refused (`LedgerConfigMismatch`). A partial but consistent dictionary is accepted.
- Reservation and settlement read the limits from the database.
- Changing a scope's limits needs an authorised, versioned, audited amendment.
- The new race test exposed a real first-open locking defect. It is fixed, and 15 repeated runs pass.
- Review 07's matched run is **not** claimed to have overspent: 120 settled and 1 refused under one declared scope.

**R8-04: Fixed.**
- A heading answer is `not_an_item` only when neither the reader nor the reading has item data. A part, a quantity or a `( n )` count gives a held `conflict`, and an illegible reading gives `unverified`.
- Nothing is removed from a BOQ.

**Handoff: prepared.**
- Packet v2 has the same scope as Review 07: 339 components and 194 BOQ rows.
- Identities are recorded one per row, 359 rows in all, each with its literal, printed label and role.
- "Ambiguous" is reserved for an unresolved fact or association.
- The findings index covers the 13 Review 07 findings: 8 decide groups (10 items) and 5 confirm groups (13 items). It records one transcription correction: F10 is in EP-26082.
- No reviewer name is filled in.

**Tests.** All test runs are new, on the frozen candidate:
- **Review 08 module:** 27 passed. The same module fails 24 of 27 on the prior candidate `1455f8b`, each on a behavioural assertion.
- **The reviewer's six-module set:** 88 passed.
- **BOQ, extraction and AI compatibility modules:** 157 passed, 7 skipped.
- **Hermetic full suite:** 1,628 tests, 1,591 passed, 35 skipped, 2 failed. Both failures are the same pre-existing ones as in Review 07.
- **Historical:** the Review 07 submitted full-suite result is 1,600 tests, 2 pre-existing failures. See [REGRESSION.md](REGRESSION.md).

## M2 remains CHANGES STILL REQUIRED

These blockers are unchanged by this correction round. They are listed as in the Review 07 response verdict:

| Blocker | What it is |
|---|---|
| **B-1** | Recovery is below 90%. Frozen deterministic pilot: identity 0.672, revision 0.710, decision 0.325. |
| **B-2** | Identity precision is below 98%, as carried in the Review 07 verdict. [METRICS.md](METRICS.md) now reports automatic-acceptance precision (1.000 on the frozen deterministic candidate) apart from raw-observation precision (0.913 on the frozen pilot). |
| **B-3** | Human truth is unresolved: the packet is prepared, and the reviewer appointment rests with the owner. |
| **B-4** | Project-model eligibility beyond 29076, 30088 and 30784 rests with the owner. |
| **B-5** | No supported verifier variant has been chosen. |
| **B-6** | The H-06 BOQ misreads. |

Correction acceptance does not imply M2 acceptance. No M3 or production promotion is authorized.
