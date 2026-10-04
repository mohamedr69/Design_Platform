# RD-M2 RDM2-R1 Correction Report

Written for the independent RD-M2 correction reviewer and the platform owner.

## Status

**READY FOR INDEPENDENT CORRECTION REVIEW.** This correction is not self-approved. The live G tree, services, database, drawings and the original RD-M2 package are unchanged.

## Finding corrected

RDM2-R1 identified a window after the final snapshot comparison and before file publication/database commit. An approval PATCH could commit in that interval, allowing a result made from the previous snapshot to be published.

## Correction

- Final snapshot comparison, exclusive file publication and the `made` database transition now execute in one short serialized transaction.
- SQLite uses `BEGIN IMMEDIATE`, because `SELECT FOR UPDATE` is ineffective there.
- Other database engines lock the `ProjectRedesign` row with `FOR UPDATE`.
- Approval edits remain possible during the long AutoCAD and read-back work. They are detected when the publication transaction begins.
- A database failure after exclusive file creation rolls back and deletes the newly created destination, preventing an orphan published file.
- Cleanup of the run copy and final progress reporting happen after commit and cannot convert a committed result to `failed`.

No schema migration is required. CAD generation, AutoLISP, log verification, read-back reconciliation, the frontend and AutoCAD-facing behavior are unchanged.

## New tests

1. A file-backed SQLite test opens two independent sessions. The publication session acquires the real lock; an approval writer starts but cannot commit until publication releases the transaction. The writer then commits normally.
2. A full Apply test injects a failure into the final database commit after exclusive file creation. The destination is removed, the Apply fails, and the row records `failed`.

Focused result: **53 passed**, including all 16 existing Redesign tests, 35 submitted Apply tests and 2 new correction tests. JUnit is `evidence/focused.xml`.

## Full suite

One run on the frozen correction: **1,299 passed, 2 failed, 34 skipped, 1 deselected, 0 errors** in 17 minutes. The two failures match the submitted RD-M2 baseline by test and message: the archive migration FOREIGN KEY failure and the stale part catalogue. JUnit and the complete log are in `evidence/full.xml` and `evidence/full.log`.

## Candidate

The correction patch is `evidence/RDM2-R1-correction.patch`. It applies on top of the submitted RD-M2 v2.1 candidate and changes only:

- `backend/app/redesign/service.py`
- `backend/tests/test_redesign_apply.py`

## Review request

Confirm that:

- the transaction truly covers snapshot comparison, exclusive publication and database finalization;
- the SQLite and non-SQLite locking paths are correct;
- failure after file creation cannot leave a final output;
- the two new tests demonstrate the finding and its cleanup path;
- no new real AutoCAD run is needed because AutoCAD-facing code is byte-identical to the accepted v2 evidence.

