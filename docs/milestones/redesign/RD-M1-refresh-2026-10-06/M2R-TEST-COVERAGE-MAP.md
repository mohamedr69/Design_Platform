# M2 refresh — test coverage map for the redesign surface

Date: 2026-10-06
Repository HEAD: `457c8159c7c587a36e40f0ba2af711a55cc3f00a` (457c815); code under `backend/` and `frontend/` identical to 771001e (stated by the caller; S7 recorded the same identity for its own HEAD 4bab8d2).
Sources: survey S7 Table D (`evidence/surveys/S7-new-surface.md`, s5: D1 per test, D2 per stage) and `evidence/TEST-RESULTS.md` with `evidence/tests/*.txt`. The scribe did not run a test and did not re-read the test files; the stage mapping is S7's. Stage ids S01-S25 are RD-M1's (`docs/milestones/redesign/RD-M1/CURRENT-PIPELINE.md`); N01-N18 are the new stages of `M2R-NEW-SURFACE-INVENTORY.md` section 2.

## 1. Test counts, then and now

"Then" is RD-M1's `docs/milestones/redesign/RD-M1/TEST-RESULTS.md` (Python 3.12.10 on the Windows G-drive copy, 78 tests over four files). "Now" is `evidence/TEST-RESULTS.md`: HEAD 4bab8d2 at the start and during the runs, CPython 3.13.16, pytest 8.3.4, `AI_ENABLED=false`, no AutoCAD, no Tesseract, run in the working tree with `-p no:cacheprovider`. Combined run: **116 passed, 0 failed, 0 errors, 0 skipped** in 156.14 s (68 warnings in the combined run; the per-file runs sum to 74 because pytest groups the same warnings). The JUnit file agrees (116 tests). The runner records that HEAD later moved to c1f962a and did not re-run on it; the code at 457c815 is stated identical to 771001e.

| Test file | Then | Now | Delta | Note |
|---|---|---|---|---|
| backend/tests/test_redesign.py | 16 | 16 | 0 | The 16 test ids in this run are identical to RD-M1's 16 (compared by sorted id). |
| backend/tests/test_drawing_review.py | 11 | 11 | 0 | RD-M1 recorded counts only; names cannot be compared. |
| backend/tests/test_fa_interfaces.py | 10 | 13 | +3 | RD-M1 recorded counts only; which three are new cannot be identified from the listings. Five damper tests at the end of the file look like later additions; that is an inference. |
| backend/tests/test_ifc_worker_and_ai.py | 41 | 41 | 0 | RD-M1 recorded counts only. S7: `grep redesign` finds nothing in this file, so the job runner is covered generically, not the Redesign runner. |
| **The same four files** | **78** | **81** | **+3** | 16 + 11 + 13 + 41. |
| backend/tests/test_drawing_prep.py | not run | 14 | +14 | New suite (preparation, coverage, agents, gate). |
| backend/tests/test_scoped_drawing_review.py | not run | 13 | +13 | New suite (scoped review run). |
| backend/tests/test_drawing_review_outcome.py | not run | 8 | +8 | New suite (review outcome and model route). |
| **All seven files** | **78** | **116** | **+38** | 81 + 35 = 116. The five files of S7 Table D hold 62 of these (16 + 14 + 11 + 13 + 8); `test_fa_interfaces.py` and `test_ifc_worker_and_ai.py` hold the other 54. |

The warning count for the four RD-M1 files is 50 then and 50 now (1 + 6 + 5 + 38); all are the starlette `anyio.abc.BlockingPortal` deprecation and `datetime.utcnow()` in `alembic/versions/e1f2a3b4c5d7_ifc_worker_identity_and_ai_review.py:91`.

## 2. Per test (S7 D1)

62 tests in five files; S7 checked with `ast` that every test function is in the table and none is missing, and the scribe checked that each of the 62 names appears with PASSED in `evidence/tests/*.txt`. "Pins" means the test exercises that stage's own logic; a stage reached only through a monkeypatched stub is not counted (noted in the last column).

| Test file | Line | Test function | Stages pinned | Note (S7) |
|---|---|---|---|---|
| backend/tests/test_redesign.py | 30 | test_a_change_is_prepared_with_the_devices_near_it_numbered | S07, S11 |  |
| backend/tests/test_redesign.py | 37 | test_an_add_is_placed_where_the_model_points_with_the_drawings_own_symbol | S13 |  |
| backend/tests/test_redesign.py | 48 | test_a_replace_takes_the_old_symbols_place_and_a_remove_needs_a_symbol | S13 |  |
| backend/tests/test_redesign.py | 62 | test_the_answer_is_kept_only_where_it_is_well_formed | S12, S13 |  |
| backend/tests/test_redesign.py | 68 | test_the_autocad_script_erases_inserts_at_the_true_scale_and_marks_each_change | S20 |  |
| backend/tests/test_redesign.py | 86 | test_a_block_drawn_away_from_its_base_point_is_inserted_so_it_is_seen_on_the_spot | S07, S13, S20 |  |
| backend/tests/test_redesign.py | 100 | test_a_sounder_flasher_is_the_strobe_symbol_and_a_sounder_the_wall_sounder | S13 |  |
| backend/tests/test_redesign.py | 119 | test_a_block_faces_the_side_its_sound_waves_are_on | S07, S13 |  |
| backend/tests/test_redesign.py | 128 | test_a_wall_device_is_fixed_with_its_back_on_the_wall_face | S08, S13 |  |
| backend/tests/test_redesign.py | 145 | test_two_devices_at_one_wall_share_it_side_by_side_without_passing_its_corner | S14 |  |
| backend/tests/test_redesign.py | 173 | test_an_ip_rated_emergency_light_is_the_drawings_e_made_weatherproof_as_a_new_block | S13, S20 |  |
| backend/tests/test_redesign.py | 199 | test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved | S10, S15, S18 | also PINS: a proposed review change is drawn (line 213) |
| backend/tests/test_redesign.py | 224 | test_a_library_block_is_brought_in_from_its_file_only_by_the_first_insert_and_noted | S20, S21 |  |
| backend/tests/test_redesign.py | 239 | test_a_typical_plans_floors_get_one_module_each_item_stacked_and_the_unplaceable_listed | S10 | S09 stubbed (I.build monkeypatched) |
| backend/tests/test_redesign.py | 273 | test_a_module_goes_on_the_nearest_real_wall_turned_to_it_past_an_equipment_outline | S08, S10, S14 |  |
| backend/tests/test_redesign.py | 295 | test_coordination_is_always_done_the_engineers_moves_and_the_modules_notes_included | S14, S15 |  |
| backend/tests/test_drawing_prep.py | 37 | test_a_room_is_filled_inside_its_walls_its_door_closed_and_a_pump_sets_outline_not_a_wall | N04 |  |
| backend/tests/test_drawing_prep.py | 46 | test_coverage_is_measured_at_the_radius_and_the_best_spots_cover_the_room | N05 |  |
| backend/tests/test_drawing_prep.py | 60 | test_a_detector_spot_keeps_off_the_columns | N03, N05 |  |
| backend/tests/test_drawing_prep.py | 68 | test_the_coordination_moves_a_ceiling_device_off_a_column_and_a_wall_device_along_its_wall | S14, N07 |  |
| backend/tests/test_drawing_prep.py | 86 | test_the_platform_proposes_the_best_spots_and_the_detectors_the_room_still_needs | N05, N07 |  |
| backend/tests/test_drawing_prep.py | 101 | test_the_coordination_agents_layout_is_refused_when_it_covers_less_than_the_platforms | N06 |  |
| backend/tests/test_drawing_prep.py | 121 | test_the_agents_answers_are_kept_to_what_they_were_shown_and_their_words_checked | N06, N09 |  |
| backend/tests/test_drawing_prep.py | 140 | test_a_detector_added_for_coverage_or_rejected_by_the_orchestrator_is_drawn_only_once_approved | S18, N07, N09 | PINS: a proposed review change is drawn, a rejected one is not (lines 142-146) |
| backend/tests/test_drawing_prep.py | 149 | test_with_the_agents_off_a_change_goes_to_the_reviews_point_with_the_drawings_symbol_named_like_it | N02 |  |
| backend/tests/test_drawing_prep.py | 161 | test_the_gate_is_the_platforms_count | N10 |  |
| backend/tests/test_drawing_prep.py | 215 | test_the_coordination_agent_and_the_orchestrator_run_side_by_side_through_the_call_path | N01, N06, N07, N09, N10 |  |
| backend/tests/test_drawing_prep.py | 328 | test_the_devices_job_with_the_agents_off_places_coordinates_and_covers_without_a_model | S15, S16, S18, S19, N01, N02, N03, N05, N07, N10 | plan job only; engineer approve/skip via PATCH; no Apply |
| backend/tests/test_drawing_prep.py | 389 | test_the_devices_job_with_the_agents_on_runs_them_on_the_preparation_route | S12, N01, N02, N06, N09 |  |
| backend/tests/test_drawing_prep.py | 416 | test_a_devices_job_after_the_review_lost_its_answers_keeps_every_change_and_the_engineers_word | S15, S16, N13 |  |
| backend/tests/test_drawing_review.py | 35 | test_rooms_are_read_off_the_plotted_plan | S05, S06 |  |
| backend/tests/test_drawing_review.py | 43 | test_the_models_answer_is_kept_only_where_it_is_well_formed | S06 |  |
| backend/tests/test_drawing_review.py | 62 | test_a_drawing_is_reviewed_and_each_finding_is_the_engineers_to_settle | S06, N13, N14, N16 | plot stubbed; also the review XLSX, markup PDF, bulk accept |
| backend/tests/test_drawing_review.py | 174 | test_stair_detection_is_wanted_about_every_five_floors_not_on_each | S06 |  |
| backend/tests/test_drawing_review.py | 192 | test_the_engineers_rulings_settle_the_same_change_elsewhere_and_go_to_the_model | N16 |  |
| backend/tests/test_drawing_review.py | 240 | test_the_ifc_signs_are_checked_against_the_fls_drawing_of_the_same_floor | S06 | plot/FLS render stubbed |
| backend/tests/test_drawing_review.py | 296 | test_the_plot_is_tied_to_the_drawing_by_the_texts_both_carry | S05 |  |
| backend/tests/test_drawing_review.py | 317 | test_a_driveway_sounder_flasher_is_asked_for_only_past_12_m | S05, S06 |  |
| backend/tests/test_drawing_review.py | 339 | test_a_decision_goes_to_the_same_comment_on_the_other_floors_and_is_undone_with_it | N14, N16 |  |
| backend/tests/test_drawing_review.py | 389 | test_staircase_speakers_go_on_alternate_floors | S06 |  |
| backend/tests/test_drawing_review.py | 409 | test_an_emergency_light_in_a_garbage_room_is_to_be_deleted | S06 |  |
| backend/tests/test_scoped_drawing_review.py | 107 | test_the_scoped_run_asks_about_the_named_floor_alone_and_puts_every_setting_back | N17 |  |
| backend/tests/test_scoped_drawing_review.py | 151 | test_a_scoped_run_whose_calls_all_fail_keeps_the_answers_and_decisions_and_puts_everything_back | N13, N17 |  |
| backend/tests/test_scoped_drawing_review.py | 182 | test_a_run_that_breaks_off_fails_its_job_and_still_puts_everything_back | N17 | review job (runners.run_drawing_review), not the redesign runner |
| backend/tests/test_scoped_drawing_review.py | 205 | test_the_scoped_run_refuses_before_asking_anything | N17 |  |
| backend/tests/test_scoped_drawing_review.py | 245 | test_the_guard_counts_every_call_refuses_one_past_the_limit_and_stops_on_more_than_it_should | N17 |  |
| backend/tests/test_scoped_drawing_review.py | 329 | test_an_acceptance_stays_only_while_the_proposal_is_the_same | N14 |  |
| backend/tests/test_scoped_drawing_review.py | 374 | test_a_decision_made_before_proposals_were_kept_stands_only_until_a_review_runs | N14 |  |
| backend/tests/test_scoped_drawing_review.py | 408 | test_a_window_the_model_answered_for_some_rooms_is_not_done_and_is_asked_again | N13 |  |
| backend/tests/test_scoped_drawing_review.py | 427 | test_the_cli_is_given_the_turn_limit_and_its_turns_are_counted | N18 |  |
| backend/tests/test_scoped_drawing_review.py | 455 | test_looks_go_one_at_a_time_so_a_stop_keeps_the_next_from_being_sent | N17 |  |
| backend/tests/test_scoped_drawing_review.py | 479 | test_the_continuation_asks_only_what_is_left_and_keeps_what_was_answered | N13, N17 |  |
| backend/tests/test_scoped_drawing_review.py | 526 | test_a_plan_pass_finding_the_room_review_has_is_merged_not_shown_twice | N15 |  |
| backend/tests/test_scoped_drawing_review.py | 543 | test_the_clis_own_account_of_a_call_is_kept | N18 |  |
| backend/tests/test_drawing_review_outcome.py | 82 | test_the_models_finding_reaches_the_review_page_through_the_worker_the_database_and_the_api | S02, S06, N13 | worker, DB and API; fake model |
| backend/tests/test_drawing_review_outcome.py | 131 | test_a_plot_with_no_model_to_call_is_blocked_and_keeps_the_answers_and_decisions_before_it | N13, N18 |  |
| backend/tests/test_drawing_review_outcome.py | 158 | test_a_plot_whose_every_look_fails_is_failed_and_keeps_what_was_there | N13 |  |
| backend/tests/test_drawing_review_outcome.py | 177 | test_a_completed_review_with_no_findings_says_so_with_the_rooms_it_read | N13 |  |
| backend/tests/test_drawing_review_outcome.py | 187 | test_the_disabled_providers_placeholder_saved_as_done_is_not_a_review_and_is_asked_again | N13, N18 |  |
| backend/tests/test_drawing_review_outcome.py | 223 | test_an_exact_model_task_gets_no_answer_from_the_disabled_provider_and_none_is_stored | N18 |  |
| backend/tests/test_drawing_review_outcome.py | 256 | test_the_drawing_reviews_own_switch_calls_the_model_for_the_review_alone | N01, N18 |  |
| backend/tests/test_drawing_review_outcome.py | 292 | test_a_blocked_attempt_on_a_partly_reviewed_drawing_leaves_it_partial | N13, S02 |  |

Tests that pin behaviour S7 proposes to change (S7 s5): `test_redesign.py:213` and `test_drawing_prep.py:142-146` (a proposed review change is drawn, a rejected one is not; C02) and `test_drawing_prep.py:416` (changes whose finding vanished are kept; C08). Changing C02 means changing those assertions on purpose.

## 3. Per stage (S7 D2)

Coverage mark. **none** = S7 counts 0 tests in the five files. **partial** = S7's note column says the stage is only partly pinned. **full** = S7 counts one or more tests and gives no partial note; it means only that, not that every behaviour of the stage is tested (for example N10 has 3 tests, and C06 lists gate conditions none of them asserts). The five files are `test_redesign.py`, `test_drawing_prep.py`, `test_drawing_review.py`, `test_scoped_drawing_review.py`, `test_drawing_review_outcome.py`.

| Stage | Name | Tests in the five files | Coverage (S7) | S7 note |
|---|---|---|---|---|
| S01 | Drawing registration | 0 | none |  |
| S02 | Drawing/source selection | 2 | full |  |
| S03 | Source hashing | 0 | none |  |
| S04 | CAD/PDF/IFC extraction (plot) | 0 | none |  |
| S05 | Sheet/floor detection; plot-model tie | 3 | full |  |
| S06 | Room/geometry discovery (review) | 9 | full |  |
| S07 | Existing symbol discovery | 3 | full |  |
| S08 | Wall extraction and caching | 2 | partial | query side only (Walls); build()/caching untested |
| S09 | Interface schedule ingestion | 0 | none | (none in the five files; test_fa_interfaces.py and test_fa_evidence.py cover the schedule itself) |
| S10 | Device/module identification | 3 | full |  |
| S11 | AI input construction | 1 | full |  |
| S12 | AI placement proposal | 2 | full |  |
| S13 | Deterministic placement conversion | 8 | full |  |
| S14 | Coordination | 4 | full |  |
| S15 | Manual engineer changes | 4 | partial | approve/skip through PATCH only; adjust with candidate/symbol/point/rotation untested |
| S16 | Plan persistence | 2 | full |  |
| S17 | Preview rendering | 0 | none |  |
| S18 | Approval/rejection state | 3 | full |  |
| S19 | Apply job creation | 1 | partial | plan job only; the Apply job is never started |
| S20 | CAD script generation | 4 | full |  |
| S21 | Block/library dependency | 1 | partial | script text only; a missing or unreachable library path is untested |
| S22 | AutoCAD execution | 0 | none |  |
| S23 | Output verification | 0 | none |  |
| S24 | Output registration | 0 | none |  |
| S25 | Error handling and retry | 0 | none |  |
| N01 | Prep switch, provider, run record | 4 | full |  |
| N02 | Placement agents / platform fallback | 3 | full |  |
| N03 | Column index | 2 | partial | Columns.hit/near only; build_columns/load_columns untested |
| N04 | Room fill | 1 | full |  |
| N05 | Coverage measure, best spots, grouping | 4 | full |  |
| N06 | Coordination agent | 4 | full |  |
| N07 | Platform coordination + coverage detectors | 5 | full |  |
| N08 | Coverage re-measure after edit | 0 | none |  |
| N09 | Orchestrator floor review | 4 | full |  |
| N10 | Preparation gate | 3 | full |  |
| N11 | Draftsman markup PDF | 0 | none |  |
| N12 | Interface verification gate | 0 | none |  |
| N13 | Review outcome, resumable looks | 11 | full |  |
| N14 | Decisions kept to proposal | 4 | full |  |
| N15 | Pass-finding merge | 1 | full |  |
| N16 | Rulings | 3 | full |  |
| N17 | Scoped review run | 7 | full |  |
| N18 | Review/prep model route | 6 | full |  |

Totals over 43 stages: none 12, partial 5, full 26. S7's count: 12 of 43 stages have no test in the five files (9 RD-M1 stages S01, S03, S04, S09, S17, S22, S23, S24, S25, and 3 new stages N08, N11, N12) and 5 more are only partly pinned (S08, S15, S19, S21, N03). The scribe recounted the per-stage tests from the 62-row table and every count agrees with S7's D2 column.

## 4. The 12 stages with no test, and the 5 with partial coverage

The "would need" column is the scribe's reading of S7's D2 notes and its grep statement (s5, last paragraphs); it is not an S7 statement and is not a design. S7's grep found nothing in `backend/tests` that calls `redesign.service.apply`, `cad.apply`, `POST .../apply/jobs`, `redesign.markup.build`, `PR.measure_again`, or `R.adjust` with a point, symbol or rotation. No test uses a DXF or DWG file: the geometry is hand-built (`Walls`, `Columns`), the plot is a blank 2000 x 2000 pt PDF, and `_devices_job` writes a stub DXF (`b"0\nEOF\n"`).

| Stage | Name | Coverage | What a test would need |
|---|---|---|---|
| S01 | Drawing registration | none | Registration and DWG conversion code is owned by S1's rows (IFC.*); S7 notes the only change here is the `DWG_CONVERT_PARALLEL` semaphore in `ifc/dxf/convert.py`. A test would need a registered drawing and the conversion step, which is outside the five files. |
| S03 | Source hashing | none | A test of the source hash used by the plan check (`rds:1171-1173`) and the Apply check (`rds:1492-1493`) against a changed source file. The five files stub the source as `b"0\nEOF\n"`. |
| S04 | CAD/PDF/IFC extraction (plot) | none | The plot runs AutoCAD (30-minute timeout, `render.py:19`, plot script `:79-82`); no AutoCAD in the test container. A test would need a stubbed plot runner whose output is checked, or a real plot environment. |
| S09 | Interface schedule ingestion | none | S7: `test_fa_interfaces.py` and `test_fa_evidence.py` cover the schedule itself, outside the five files. `test_redesign.py:239` stubs `I.build`. A Redesign-side test would need a real `I.build` view with the new `equipment_anchor` contract (`interfaces/service.py:1440`: a symbol centre, or None for a label-only item). |
| S17 | Preview rendering | none | A test of `image()` that loads a columns pickle and checks the overlay (columns, coverage circle) without building anything on a GET (`rds:1342-1364`). |
| S22 | AutoCAD execution | none | AutoCAD is not present. A test would need a stubbed `accoreconsole` run, or a real AutoCAD environment, to exercise timeout and failure (`cad.py` identical to RD-M1). |
| S23 | Output verification | none | A test that the check (copy exists and mtime changed) refuses an unchanged or missing output (RD-M1-F023); needs a stubbed AutoCAD run. |
| S24 | Output registration | none | A test of the copy into `<project folder>/03- Drawings/Redesign`, the minute-resolution name (`rds:1502`) and the absolute `output_path` (`rds:1520`); needs a temporary project folder. |
| S25 | Error handling and retry | none | The Redesign job runner is not exercised: `grep redesign` finds nothing in `test_ifc_worker_and_ai.py`, so RD-M1's tests-column entry for S19/S25 does not cover it. A test would start a redesign job that fails and check status, error and retry. |
| N08 | Coverage re-measure after an engineer edit | none | A test that PATCHes a detector move, runs `PR.measure_again`, and asserts `change.coverage` on the group's members and that `run.coordination` and `run.gate` are unchanged (C07). |
| N11 | Draftsman markup PDF | none | A test that calls `redesign.markup.build` / the draftsman route on a drawn set that includes a proposed, unapproved review change (C02) and reads what is listed. |
| N12 | Interface verification gate and anchor contract | none | S7 notes `test_fa_evidence.py:672-720` pins `keep_interfaces` / `restore_kept` and that `add_interfaces` refuses an unverified schedule (outside the five files). Missing: a test that Apply, which does not re-check verification (C08), still draws an approved module after the schedule stops being verified. |
| S08 | Wall extraction and caching | partial | S7: query side only (`Walls`); `build()` and the pickle caching are untested. A test would build an index from a small DXF and reload it. |
| S15 | Manual engineer changes | partial | S7: approve/skip through PATCH only. Missing: `adjust` with candidate, symbol, point and rotation (`R.adjust`). |
| S19 | Apply job creation | partial | S7: plan job only; the Apply job is never started. A test would POST the Apply job (`routers/redesign.py:103-107`) for a plan whose gate is `needs_engineer` (C01). |
| S21 | Block/library dependency | partial | S7: script text only; a missing or unreachable library path is untested (RD-M1-F001). A test would generate the script with a stored library path that does not exist. |
| N03 | Column index | partial | S7: `Columns.hit` / `near` only; `build_columns` and `load_columns` (the pickle, VERSION 2) are untested. A test would build from a small DXF, reload, and cover a read failure (C06 (a)). |

## 5. No test reaches `apply()`

S7 (s1, s5): "no test of any kind exercises `apply()` or the Apply job". The combined evidence is: S7's grep finds no call to `redesign.service.apply`, `cad.apply` or `POST .../apply/jobs` in `backend/tests`; test_drawing_prep.py:328 (`test_the_devices_job_with_the_agents_off_places_coordinates_and_covers_without_a_model`) is described as "plan job only; engineer approve/skip via PATCH; no Apply"; and `test_scoped_drawing_review.py:182` runs the review job runner, not the redesign runner. The consequences carried into the inventory: the gate (C01), the drawn set at Apply (C02, C08), the refresh that re-coordinates at Apply (C07), the script (S20) and everything after it (S21-S25) have no behavioural test at the Apply boundary. S7 also notes that the stage S19 is covered only at the plan half.

## 6. What passing tests do and do not establish for M2's exit

M2's exit for the refreshed baseline (`docs/UNIFIED_MASTER_ROADMAP.md`, M2) is that a reviewer can trace current findings to source, input and output hashes and reproduce bounded cases, without treating historical findings as fixed by new UI or AI code.

What the 116 passing tests establish:

- The code at the run's HEAD does what the 116 assertions say, on synthetic data, with the model replaced by stubs (`AI_ENABLED=false`) and without AutoCAD or Tesseract. The runner recorded no skip, xfail or error, and `test_redesign.py`'s 16 test ids are the same as at RD-M1.
- The synthetic harness (hand-built `Walls` and `Columns`, a blank 2000 x 2000 pt PDF, a stub DXF, fake agents) exists and works, so a bounded case for a deterministic helper, such as the C03 fallback, the C13 detector pattern or the C14 erase set, can be written against it. S7 wrote none, and none is claimed.

What they do not establish:

- They do not show any candidate finding is fixed or absent. Three of them assert the behaviour the inventory calls a defect: `test_redesign.py:213`, `test_drawing_prep.py:142-146` (C02) and `test_drawing_prep.py:416` (C08). A green suite is consistent with all 22 candidates.
- They do not reach Apply, the gate's enforcement, the script's execution, output verification or registration (section 5), the draftsman PDF, or the post-edit coverage re-measure; 12 of 43 stages have no test and 5 are partial.
- They do not touch a real drawing: no DXF/DWG, no real plot, no real wall index, no module-library DWG, and no real model answer. GC-01 is not reproducible from this repository (S7 Table E), so no test result is evidence about GC-01 or about the placement of any device.
- They are not acceptance and do not change any finding's `UNREVIEWED` status. `evidence/TEST-RESULTS.md` says the same: passing tests show the code does what the tests assert, not that the behaviour is right on real drawings, and RD-M1's F001-F035 gap list was not re-assessed by the run or mapped to the added tests.
- Names of RD-M1's tests in `test_drawing_review.py`, `test_fa_interfaces.py` and `test_ifc_worker_and_ai.py` were not recorded, so "no test added or removed" is established by id only for `test_redesign.py`; for the others only the counts compare.
