# M5 low fixes: implementation of ORCH-041 (U2-M5-LOW-FIXES, condition C2)

Role: ep-implementer (Claude Opus 5.5, high effort), fresh and isolated. Date: 8 October 2026 (runs 7 October, UTC).
Branch `task/m5-low-fixes`, worktree `G:/dev (2)/dev/ep-platform-merged/wt-m5b`, created from `roadmap/u2` at
`48fe702955329fb8114ee18bf33916d7b8afed13` (contains the M5 merge `fcc5ddd` and the M8 merge `f95a3f4`).
Implementation commit: `a19b61e`. Evidence: `evidence/low-fixes/` (hashes in its `MANIFEST.json`).
Input: `MR/reviews/U2-M5-verify/INDEPENDENT-VERIFICATION.md` and `FINDINGS.json` (ORCH-040), the ORCH-039 card.

Evidence classes: FUNCTIONAL-MOCKED (stand-in AutoCAD and read-back, as in ORCH-039) and SQLITE (the suite's
file-backed WAL database, two real connections). **No REAL-AUTOCAD and no REAL-MODEL claim.** A passing suite is
evidence, not acceptance; condition C1 (the OD-16 c real-AutoCAD run) and C3 (non-SQLite lock path) are untouched.

Files changed (all in `a19b61e`): `backend/app/redesign/service.py`, `backend/app/workers/ifc_worker.py`,
`backend/tests/test_redesign_apply.py`, `frontend/src/components/prep/RedesignPanel.tsx`,
`frontend/src/components/prep/types.ts`. `cad.py` and `verify.py` are untouched and byte-equal to v2.1
(`43672b30…`, `449ad1af…`). No M8 file (`config.py`, `walls.py`, `coverage.py`, `prepare.py`) was touched; the router
(409 guard, 422 gate) is unchanged.

"Before" = the new tests run on the unmodified code of `48fe702` (`evidence/low-fixes/before-fix.log`/`.xml`,
2026-10-07 23:18 UTC: **11 failed**). "After" = the committed implementation (`targeted.*`, `full-suite.*`).

## Finding -> change -> test -> before / after

| Finding | Change (`service.py` unless named) | Test (`tests/test_redesign_apply.py`) | Before | After |
|---|---|---|---|---|
| **U2M5V-01** request checked before Apply's own "making" write | `apply()`: after the first look and the last `check()`, `_locked_publish_row` (the publication lock, `BEGIN IMMEDIATE` on SQLite) is taken; inside it `_request_changed()` compares source and fingerprint again (refusal recorded "refused" and committed), "making" is written and flushed, and the snapshot is taken from the row as that transaction wrote it, then one commit. `_refusal` now shares `_request_changed`. | `test_an_approval_committed_between_the_request_check_and_the_making_write_is_refused_not_drawn` (probe P3 as a test: approval committed on a second connection inside the first `check()`) | FAIL: made, 5 changes drawn, no refusal | pass: `ApplyRefused`, "refused", AutoCAD not run, approval kept |
| **U2M5V-02** publish `.part` in the archive | `publish()` stages `.<name>.part` in `uploads/EP-<n>/redesign/publishing/` (`PUBLISHING`), then `_into_archive()`: hard link, Windows rename (never replaces), else `_copy_exclusive()` (O_EXCL on the final name, removed on any failure). Nothing temporary is created in the archive. `sweep_orphans()` removes old `.part` files in the staging folder (the archive is never swept). 409s: "already in the project archive (the same file)", "A different file named … is already in the project archive", and, for a staging collision, "A publication … is under way, or an interrupted one left its temporary copy in the platform's staging folder". | `test_publish_stages_its_temporary_copy_in_the_platform_folder_never_in_the_archive`; `test_a_leftover_publication_temporary_is_said_as_such_swept_and_does_not_block_for_good`; `test_publishing_to_an_archive_on_another_volume_copies_exclusively_and_never_overwrites` | FAIL ×3: staged in the archive; 200 instead of 409 / "already in the archive"; `OSError` EXDEV | pass ×3 |
| **U2M5V-03** "made" committed, job never "succeeded" | `verification.json` now also records drawing, job, apply id, fingerprint, change and insert/erase counts. `_verified_run()` reads the run named by the apply id in the copy's name and accepts it only when `ok` and the copy's sha256 equals `copy_sha256`. `_reconcile_row()`: the recovered job itself returns that result (succeeds, AutoCAD not run); a job left "failed" is recorded "succeeded" with it. Called at the start of `apply()` (own and other jobs), by `publish()`, and by `reconcile_made()` in the IFC worker's housekeeping (`ifc_worker.py`). | `test_a_copy_made_whose_job_never_succeeded_is_reconciled_when_the_recovered_job_runs_again`; `test_a_made_copy_whose_job_failed_is_reconciled_by_housekeeping_only_while_it_still_verifies`; `test_a_made_copy_whose_job_failed_is_reconciled_by_the_next_publish_or_apply_request`; `test_a_made_copy_whose_job_failed_is_reconciled_when_the_next_apply_is_asked_for` | FAIL ×4: job failed "already made"; `reconcile_made` missing; 422; AutoCAD run again | pass ×4 |
| **U2M5V-04** pre-M5 filing shown as "published separately" | `view()` adds `output.published` (only from a `redesign.published` event for the current copy) and `output.filed_earlier` (a stored `output_relative` without one). Panel: "filed by an earlier version, not verified: …", no "checked", no Publish button; a published copy reads "published to the project archive by the engineer: …". | `test_a_copy_filed_by_the_pre_m5_apply_is_said_filed_by_an_earlier_version_not_published`; `test_the_panel_says_a_pre_m5_filing_apart_from_a_publication_and_keeps_the_two_meanings_apart` | FAIL ×2: `KeyError 'published'`; old wording | pass ×2 |
| U2M5V-05 (info) two meanings of "published" | Panel outcomes: "Stale, no new copy was kept: …", "No new copy was made: …"; "published" now only for the archive. Backend error strings unchanged (tests match them). | the panel test above | FAIL | pass |
| U2M5V-07 (info) publish not bound to `copy_sha256` | `_verified_job()` returns the run's checks; `publish()` refuses (422) a copy whose sha256 differs from `copy_sha256`, before anything is staged. | `test_publish_refuses_a_copy_that_is_no_longer_the_file_apply_verified` | FAIL: 200 | pass |
| U2M5V-11 (info) dead `refresh()` | **Not removed.** No caller in `backend/app`, but `test_apply_never_places_or_coordinates_again…` (`test_redesign_apply.py:1056`) patches `R.refresh` by name as a guard; removing it means editing that guard. Left for the owner. | — | — | — |

## Runs

All on HEAD `a19b61e`, interpreter `ep-platform/backend/venv/Scripts/python.exe -B` (Python 3.12.10),
`-p no:cacheprovider --basetemp=C:/t/tmp/m5b/bt`, TEMP/TMP `C:/t/tmp/m5b/tmp`; script `evidence/low-fixes/scripts/run_evidence.sh`.

- **Before** (`before-fix.*`, unmodified code + the new tests): 11 failed, each for the reason in the table.
- **Targeted** (`targeted.*`, 23:26-23:31 UTC): **104 passed** = ORCH-040's 93 (59 + 16 + 14 + 4) + the 11 new
  (`test_redesign_apply` 70, `test_redesign` 16, `test_drawing_prep` 14, `test_prep_readiness` 4). The 30 earlier
  tests in `test_redesign.py` and `test_drawing_prep.py` all pass, unchanged.
- **Full suite** (`full-suite.*`, `AI_ENABLED=false DATA_ROOT=`, 23:31-00:07 UTC): **1,902 tests: 1,866 passed,
  1 failed, 35 skipped** (exit 1).
- **Comparison** (`full-suite-comparison.json`, `scripts/compare.py`, by name, state and message):
  - against M4 run 2: no new failure, no test missing; `test_persistence::test_a_data_root…` passes now (as in
    ORCH-039); 83 added tests, all passed (70 `test_redesign_apply`, 13 M8 `test_redesign_walls_layers`);
  - against ORCH-039's `full-suite.xml`: no new failure, no test missing, **no state change** in any common test;
    24 added (11 mine, 13 M8), all passed;
  - the one failure is the pre-existing `test_proposed_materials::test_the_part_catalogue_knows_every_number…`,
    same message, same three extra items once sorted (3-SDDC2, 3-SSDC2, SIGA-OSD-FCN; U2M5V-08).
- **tsc** (`tsc-frontend.txt`): `tsc -p tsconfig.app.json --noEmit --incremental false` through a temporary junction
  to the live clone's `node_modules`: exit 0, no errors; junction removed, nothing installed.
- The implementation commit message says "10 new" tests; there are 11 (the panel wording test is the eleventh).

## Left open

- C1 (OD-16 c real-AutoCAD run) and C3 (non-SQLite `FOR UPDATE` path, now also used at Apply start) are unchanged.
- A hard process kill during the cross-volume exclusive copy can leave an incomplete file under the final name in
  the archive (no `.part`, and never over another file). A later publish then answers 409 "A different file named …";
  the engineer removes it. Same-volume archives use a link or rename and cannot leave one.
- Reconciliation accepts only a job left "failed" (or the recovered job itself). A job recovered as "cancelled"
  (cancel requested before the stop) is not reconciled; its copy stays downloadable, not publishable.
- `refresh()` kept (above); U2M5V-06 (Publish only when the last attempt is "made") not in scope.
- The frontend was type-checked, not rendered.
- Commit trailers name Claude Fable 5.1 as the card prescribes; this report's author is Claude Opus 5.5 (as U2M5V-09).
