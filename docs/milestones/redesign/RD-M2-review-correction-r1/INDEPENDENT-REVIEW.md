# Independent RD-M2 Review

Reviewer: Codex, independent of the Claude implementation session  
Date: 2026-10-04  
Candidate: RD-M2 v2.1 (`evidence/candidate-files.json`)

## Verdict

**CHANGES REQUIRED.** The package is internally consistent and the isolated AutoCAD evidence is valid, but the Apply snapshot guarantee still has a time-of-check/time-of-use window before publication.

Candidate v2 successfully made and read back the 11 approved GC-01 inserts, refused the missing-block case, and made and verified the isolated erase control. The finding below concerns concurrent approval changes after verification.

## Independent checks completed

- Recomputed all 68 package file hashes: 68 match, 0 missing, 0 mismatched.
- Confirmed the package checker reports all checks passing.
- Confirmed candidate regression: 1,297 passed, 2 failed, 34 skipped; base: 1,262 passed, 2 failed, 34 skipped. The two failures match by test and message.
- Inspected the delivered patch and frozen candidate source for approval filtering, block resolution, AutoCAD execution, marker parsing, read-back, publication, cancellation and recovery.
- Inspected all packaged verification records. The v2 success and erase records pass, the missing-block case is refused, and the v1 parser defect is preserved as history.

## RDM2-R1 — approval can change after the last snapshot check

**Severity: major. Status: open.**

`service.apply()` refreshes and compares the snapshot, then chooses a destination, calls `_publish()`, sets the output fields and commits (`service.py:1665-1676` in the frozen candidate). There is no row lock, version compare, conditional update, or second snapshot check covering publication and commit.

A PATCH committed after the comparison can therefore change an approval or placing before publication. Apply can still publish the output made from the previous snapshot and report `made`. The existing test changes approval during `_readback()`, before the final check. It does not exercise this publication window. The queue deduplication prevents two active Apply jobs for one drawing, but it does not prevent a concurrent approval PATCH.

This contradicts the owner decision and package claim that Apply never publishes a result made from a snapshot that is no longer current.

### Required correction

Make publication and the state transition conditional on the same snapshot. Use an optimistic version or compare-and-set update, an exclusive temporary/final publication protocol, and cleanup if conditional finalization or commit fails. A stale attempt must not replace an earlier valid output.

Add an integration test that changes approval from a second database session inside `_publish()`, after the current last snapshot comparison. It must prove that no final output remains, the result is not `made`, and the newer approval is preserved. Also cover database commit failure after exclusive file creation so it cannot leave an unreferenced published output.

## Accepted parts

Subject to RDM2-R1, the evidence supports approved-only drawing, local CT1/CT2/CR resolution, fail-closed AutoCAD behavior, the standalone marker fix, insert/erase read-back, unique relative output paths, sequential recovery/idempotency, cancellation and pre-publication stale checks. It also supports that the live tree, live database, source drawings and RD-M1 package were not modified by the candidate work.

## Next step

Do not apply the patch to the live G tree and do not start RD-M3. Correct RDM2-R1 in the isolated candidate, run focused and full candidate tests, then submit a small correction for independent re-review. A new real AutoCAD run is unnecessary if the correction does not change CAD generation, verification, or the AutoCAD-facing application code.
