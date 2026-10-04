# M2 Review 09: correction package

These four statements are made separately. None of them implies another.

| Question | Status |
|---|---|
| **Correction readiness** | **READY FOR INDEPENDENT CORRECTION REVIEW.** R9-01 to R9-04 and the ledger wording are implemented in the isolated candidate `689d95e`, frozen, tested and re-scored. |
| **Accuracy** | **Unresolved.** No correction here changes an accuracy figure: every stored run re-scores identically under evaluator .8. Recovery is below 90% (B-1), identity precision is below 98% (B-2), there is no supported variant choice (B-5), and the H-06 BOQ misreads remain (B-6). |
| **Human truth** | **Pending.** Packet v2 is prepared and unchanged. No reviewer is named, and the appointment is the owner's choice (B-3). No AI adjudication was done. |
| **Project permission** | **Pending, as recorded.** Model use covers 29076, 30088 and 30784 only (B-4). No owner answer was received and none is assumed; nothing was re-asked. |

**M2 remains CHANGES STILL REQUIRED.** No M3 work and no production promotion is authorized, and this package does not approve M2.

## Boundaries kept

| Item | Status |
|---|---|
| Owner's tree | No code change: HEAD `2221b43`, and the original 11 Candidate C hashes match. The only additions are this folder and the appended response in `M2-REVIEW-RESPONSE.md`. |
| Services, database, settings, symbol library, OneDrive originals, sealed cohort | Not touched. No source document was opened. |
| Where the work happened | The isolated scratch repository `C:/t/iso/ep-platform`. Candidate `689d95e`, frozen at `C:/t/iso/frozen-r9` with no `.env`. |
| Review 08 | Kept as history: `e02a8c1`, its worktree `frozen-r8` (clean) and the `review08/` package and evaluator .7 outputs (hashes checked). |
| Models | **None called.** No accuracy experiment was run, no corpus expanded, and no backfill or migration was done. |
| Commits | Only on the scratch branch. None in the owner's repository, and no push. |

## Package

| Document | Contents |
|---|---|
| [DISPOSITIONS.md](DISPOSITIONS.md) | R9-01 to R9-04 and the ledger wording: how each was reproduced, what changed, and each test with its result on `e02a8c1` |
| [CONTRACT.md](CONTRACT.md) | The contract: read usability, fact association, source identity and item presence |
| [RESCORE.md](RESCORE.md) | Evaluator .8 on every stored output. It equals .7 in all 33 runs; the associations it now records; the BOQ heading replay. |
| [REGRESSION.md](REGRESSION.md) | The failures reproduced before the fix; the module on `e02a8c1` (fails) and `689d95e` (passes); the reviewer's probes before and after; the focused modules; the hermetic full suite; the changed fixture |
| [PROVENANCE-AND-FREEZE.md](PROVENANCE-AND-FREEZE.md) | Commits, freeze, the SHA-256 of every changed file, test commands, the temporary environment and the status of every tree |
| `evidence/` | `EVIDENCE-MANIFEST.json` (evidence files, package files, candidate hashes, the Candidate C check); tests; the before and after runs; the probes; the re-score; the BOQ replay; freeze and diff; patch scripts; suite and focused JUnit |

## Results in brief

**R9-01: Fixed.**
- A returned response is not a usable read. The request outcome and the field outcome are now recorded separately.
- An illegible blind answer (`unusable:illegible`), or a legible answer with no value (`unusable:empty`), supersedes nothing. Discovery-only candidates and negatives never replace good evidence, and they are kept with the attempt.
- A completed, legible negative still supersedes, and completed conflicting evidence stays an explicit conflict.

**R9-02: Fixed.**
- Dependent facts record their `target` (and a decision its `target_revision`). Selection labels each one's association, and evaluator .8 judges held and `by_target` facts only under their own target.
- A decision for X-SD-1 is never accepted or recovered for X-SD-9, and it stays visible as held.
- Same-identity retries are unaffected, and legacy facts are never given a target.

**R9-03: Fixed.**
- Source identity is decided per field. Missing, mismatched and matching bytes are distinct states (`unknown_source`, `stale`, `current`), and a request without a hash gets `source_required`.
- The unknown-profile declaration no longer implies anything about bytes.
- Retained fields are never relabelled.
- Historical compatibility is a separate, manifest-backed mode. No stored run needed it.

**R9-04: Fixed.**
- The normal verifier passes the reader's description. A count, part or present quantity on either side (0 and "0" included) against a heading answer is a held conflict.
- An illegible answer stays unverified, and a true heading with no item evidence is `not_an_item`.
- Lines and literals are kept.

**Ledger: wording corrected.**
- An already-open handle reads the saved, amended policy.
- A newly opened handle supplying the old limits is refused.
- The behaviour is unchanged, and the run of 120 requests is not claimed to have overspent.

**Tests.** All new, on the frozen candidate:
- **Review 09 module:** 34 passed. On `e02a8c1` the same module fails 22 of 34: 20 on behaviour, one on dropped metadata, one on the ledger wording.
- **The reviewer's seven-module set:** 115 passed.
- **BOQ, extraction and AI compatibility modules:** 157 passed, 7 skipped.
- **Hermetic full suite:** 1,662 tests, 1,625 passed, 35 skipped, 2 failed. Both failures are the same pre-existing ones as in Review 08, and the only change in test count is the new module.

The reviewer's probes on `e02a8c1` reproduce their results exactly, and on the candidate every defect case flips. See [REGRESSION.md](REGRESSION.md).
