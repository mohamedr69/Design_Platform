# Regression and Tests (RD-M2)

## Method

- `base` (an unchanged copy of the live backend) and `cand` (the candidate) were each run with the full backend suite, using the same interpreter the G services use (CPython 3.12.10, the Desktop venv). Flags: `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, `--junitxml`. Results are compared **test by test** from the JUnit files (`evidence/tests/regression-comparison*.json`).
- One test was deselected in every run: `tests/test_ifc_boq.py::test_real_dwg_converts_to_the_same_symbols_as_a_hand_saved_dxf`. It would run the real AutoCAD on a drawing from the owner's Desktop if that file existed, which would be an unauthorised AutoCAD run. The file is not on this PC, so the test would skip anyway.
- The frontend page was type-checked with the project's TypeScript (`tsc -p` with `noEmit`, `tsBuildInfoFile` removed). The live `node_modules/.tmp` hashes were unchanged afterwards.

## Results

| Run | Tests | Passed | Failed | Skipped | Errors | Collection errors | Duration | State changes vs base (on the 1,298 shared tests) |
|---|---|---|---|---|---|---|---|---|
| base | 1,298 (+1 deselected) | 1,262 | 2 | 34 | 0 | 0 | 22 m 41 s | – |
| candidate v1 | 1,331 | 1,295 | 2 | 34 | 0 | 0 | 20 m 20 s | **0** |
| candidate v2 | 1,333 | 1,296 | 3 | 34 | 0 | 0 | 17 m 38 s | **0** |
| **candidate v2.1 (delivered)** | 1,333 | **1,297** | 2 | 34 | 0 | 0 | 17 m 22 s | **0**; all 35 new tests pass |

### The two failures in every run (pre-existing, unrelated to Redesign)

Both reproduce standalone on base and on the candidate (`evidence/tests/flaky-reruns.txt`):
- `tests/test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index`: `sqlalchemy.exc.IntegrityError: FOREIGN KEY constraint failed [SQL: DROP TABLE users]`
- `tests/test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it`: `AssertionError` (part numbers not in the catalogue set)

### Intermittent, pre-existing

`tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows` (a BOQ read job, not Redesign) failed once in a discarded early candidate run. Standalone it fails intermittently on **base** too (1 of 8) and on the candidate (2 of 5). Its own comment says it is timing-sensitive. It passed in every full run above.

### The third failure in v2: a defect in a new test, fixed in v2.1

`tests/test_redesign_apply.py::test_proposed_and_skipped_changes_stay_out_of_the_apply` asserted that the skipped REMOVE's handle string (`"45"`, a short ezdxf handle in the test fixture) did not occur **anywhere** in the script. That run's random nonce was `dadf64445c4ddfe2`, which contains `45`. v2.1 asserts the exact erase step instead (`(ep_erase "<handle>" ` absent for the skipped REMOVE, present for the approved one). The fixed test passed 10/10 in repeats. No application code changed: v2.1's application files are byte-identical to the AutoCAD-validated v2.

## The 20 required tests

| # | Required | Test(s) in `tests/test_redesign_apply.py` (unless noted) |
|---|---|---|
| 1 | CT1, CT2 and CR resolve from the current library | `test_ct1_ct2_and_cr_resolve_from_this_installations_library` |
| 2 | A stored office-PC path never in the script | `test_a_stored_office_pc_path_never_reaches_the_script`; `test_redesign.py::test_a_library_block_is_brought_in_from_its_file_only_by_the_first_insert_and_noted` (updated) |
| 3 | Unknown module code refused | `test_an_unknown_module_code_is_refused` |
| 4 | Missing library file refused before AutoCAD | `test_a_missing_library_file_is_refused_before_autocad` |
| 5 | Only approved included | `test_only_explicitly_approved_changes_are_drawn`, `test_proposed_and_skipped_changes_stay_out_of_the_apply` |
| 6 | Proposed review changes excluded | the same two tests; `test_redesign.py::test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved` (updated); `test_nothing_approved_means_no_apply_job` |
| 7 | Skipped low-confidence REMOVE excluded | `test_a_skipped_low_confidence_remove_like_rd_m1_f003_is_never_drawn`, `test_proposed_and_skipped_changes_stay_out_of_the_apply` |
| 8 | `confirm`-required excluded until confirmed | `test_a_spot_to_confirm_is_drawn_only_once_confirmed`, `test_the_page_says_a_proposed_change_is_not_drawn_and_asks_for_approval_before_an_apply` |
| 9 | Insert failure aborts before `entdel` and `QSAVE` | `test_a_failed_insert_stops_before_any_entdel_or_save`, `test_an_insert_failure_in_autocad_publishes_nothing`, `test_a_script_cancelled_by_autocad_has_no_outcome_and_is_refused`; `test_redesign.py::test_the_autocad_script_erases_inserts_at_the_true_scale_and_marks_each_change` (updated); real AutoCAD: scenario B |
| 10 | Erase target verification | `test_an_erase_is_made_only_on_the_symbol_meant`, `test_an_unexpected_erasure_in_the_read_back_fails_the_apply`; real AutoCAD: control C |
| 11 | Completion/failure markers | `test_the_markers_are_this_runs_and_never_the_echo`, `test_the_core_consoles_echo_of_a_printed_marker_is_not_a_second_outcome` |
| 12 | Unreadable or unchanged output refused | `test_an_unchanged_unreadable_or_incomplete_output_is_refused` (5 cases) |
| 13 | Unique names for two Applies in one minute | `test_two_applies_in_the_same_minute_get_two_files` |
| 14 | No overwrite on collision | `test_an_existing_output_is_never_overwritten` |
| 15 | Relative persisted path, traversal refused | `test_the_output_is_stored_relative_and_read_back_safely`, `test_an_older_absolute_path_from_another_pc_is_found_under_this_uploads_folder` |
| 16 | Completed Apply not re-run after recovery | `test_a_completed_apply_is_not_run_again_after_worker_recovery`, `test_the_same_approved_set_is_not_made_twice_by_a_second_job` |
| 17 | Source-hash mismatch refused | `test_a_changed_source_is_refused` |
| 18 | Cancellation before and during AutoCAD | `test_a_cancel_before_autocad_runs_nothing`, `test_a_cancel_while_autocad_works_stops_it_and_publishes_nothing` |
| 19 | Changed snapshot refuses publication | `test_approvals_changed_while_autocad_worked_are_not_published`, `test_a_job_asked_for_before_the_approvals_changed_is_refused` |
| 20 | Existing successful paths compatible | `test_the_approved_changes_are_made_checked_and_kept`, `test_the_source_is_read_back_by_the_same_converter_once_per_source`, the 16 tests of `test_redesign.py`, and the unchanged results of `test_drawing_review`, `test_fa_interfaces` and `test_ifc_worker_and_ai` inside the full suite |

Focused runs:
- `test_redesign.py` and `test_redesign_apply.py` together: 51 passed (16 + 35).
- Job/worker recovery: `test_ifc_worker_and_ai.py` (41) unchanged, plus test 16 above.
- Drawing-output endpoint: tests 15 and 20 call `GET …/output.dwg` through the API.

## Assertions changed in existing tests

Three tests in `test_redesign.py` asserted behaviour the owner reversed. Each assertion was replaced by a stricter one (`CHANGE-MAP.md`); none was dropped.
