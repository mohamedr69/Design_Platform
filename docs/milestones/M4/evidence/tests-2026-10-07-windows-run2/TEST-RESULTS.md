# M4 evidence: second full test-suite run on Windows (short basetemp)

Date: 7 October 2026. Branch `claude/upbeat-lovelace-sa9j3w`.

HEAD at the start of this run: `f5c15f27b071b9d0fc8782a78d1ee6e87b4aa7ba` ("M4 evidence: first full test-suite run on Windows (at 2e407f8, before the test repairs)"). This is one commit ahead of the `f032d20` named in the task; the one commit in between adds only run 1's own evidence files (`docs/milestones/M4/evidence/tests-2026-10-07-windows/{TEST-RESULTS.md,full-suite.log,full-suite.xml,frontend-build.log}`, 4 files, no test/app/conftest code — confirmed with `git diff --stat f032d20 f5c15f27`). The repairs of `f6ab349` (archive-model test, `_alembic_tmp_` cleanup, `@requires_tesseract`) are present at both commits.

**HEAD moved while this run's pytest process was executing in the background**, from someone else's commits on the same checkout (not this agent's; no git command that changes the checkout was run by this agent). By the time the run finished, HEAD was `5da743d28b15834c4138feab13b2c64b1ec09376` ("M4 evidence: verification 02 of the persistence-test repair (ACCEPT WITH NOTES)"), three commits ahead of the start point:

```
d47fa70 M4 test health: keep the developer's .env out of the data-root settings test
845bc02 Merge the verified persistence-test repair (d47fa70, verification 02 ACCEPT WITH NOTES)
5da743d M4 evidence: verification 02 of the persistence-test repair (ACCEPT WITH NOTES)
```

`git diff --stat f5c15f27 5da743d` touches exactly two files: `backend/tests/test_persistence.py` (adds `_env_file=None` to the three `Settings(...)` calls in `test_a_data_root_gathers_the_database_uploads_backups_and_caches`) and a new evidence file, `docs/milestones/M4/evidence/test-repairs-2026-10-07/VERIFICATION-02.md`. No other test, app, or conftest file changed during the run. The JUnit XML records the session start as `2026-10-07T09:43:46+04:00`; `d47fa70` was committed at `09:45:47`, about two minutes into a 24-minute run, almost certainly after pytest's collection phase had already imported `test_persistence.py`'s original (pre-`d47fa70`) bytecode — pytest's own traceback printer re-reads the source file from disk by line number at report time, so the failure text below shows the post-commit source (`_env_file=None` already present) regardless of which version of the function actually executed. This run cannot establish, on its own, whether the failure below reflects the pre-fix or the post-fix code; see "test_persistence .env finding" below.

## Git status, before this run

```
 M .claude/agents/ep-implementer.md
 M README.md
 M backend/.env.example
 M backend/library/symbols/symbol_library.json
 M docs/SESSION-LOG-2026-10-07-windows.md
 M frontend/vite.config.ts
 M stop-backend.bat
?? docs/milestones/M4/evidence/m2-closure-package-2026-10-06/
?? docs/milestones/M4/evidence/policy-2026-10-07/
```

## Git status, after this run

```
 M .claude/agents/ep-implementer.md
 M README.md
 M backend/.env.example
 M backend/library/symbols/symbol_library.json
 M docs/SESSION-LOG-2026-10-07-windows.md
 M frontend/vite.config.ts
 M stop-backend.bat
?? docs/milestones/M4/evidence/m2-closure-package-2026-10-06/
?? docs/milestones/M4/evidence/policy-2026-10-07/
?? docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/
```

The only change attributable to this agent is the new `tests-2026-10-07-windows-run2/` evidence folder. `backend/library/symbols/symbol_library.json`, `README.md`, `backend/.env.example`, `frontend/vite.config.ts`, `stop-backend.bat`, `.claude/agents/ep-implementer.md`, and `docs/SESSION-LOG-2026-10-07-windows.md` were already modified before this run started and are not this agent's edits (owner's port edits and session log; `m2-closure-package-2026-10-06/` and `policy-2026-10-07/` were likewise already untracked before this run started).

`backend/library/symbols/symbol_library.json`: `git diff` is identical before and after this run — a single one-line change (`"exported_at": "2026-10-06T21:29:34"` → `"2026-10-07T09:08:49"`) that was already present before this run started, and the file's on-disk timestamp is `2026-10-07 09:08:49` both before and after (unchanged by this run). `start.bat` was run at `09:08:21` that day (per the task's own timeline), 28 seconds before the file's `exported_at`/mtime — consistent with the owner's live-platform start writing it, not a test. **This run did not touch or rewrite that file**, and establishes nothing new about what run 1 wrote it (run 1's "some test or fixture" guess is accordingly still not established by either run).

## Result

**2 failed, 1782 passed, 35 skipped, 0 errors, 856 warnings, 1819 tests, in 1450.65s (0:24:10)**

(Run 1, same command shape but with the long scratchpad `--basetemp`: 9 failed, 1748 passed, 35 skipped, 27 errors, 855 warnings, 1819 tests, in 1605.69s.)

## Environment

- OS: Windows 10 Home 10.0.19045 (Git Bash / MINGW64, `LAPTOP-IL4L4UAJ`).
- Python: `backend/venv/Scripts/python.exe` — Python 3.12.10 (unchanged from run 1).
- Node: v24.14.0. npm: 11.9.0 (unchanged from run 1; frontend build not repeated this run, per task).
- Tesseract: present, not on PATH, found via `app/core/config.py:49-52`. `tesseract --version` → `tesseract v5.4.0.20240606`, leptonica-1.84.1 (same build as run 1).
- No AutoCAD. No PostgreSQL. `EP_PLATFORM_LIVE_ARCHIVE_ROOT` unset. `AI_ENABLED=false`, `DATA_ROOT=` (empty) passed on the command line.
- Packages (re-checked via `pip show`): pytest 8.3.4, fastapi 0.115.6, starlette 0.41.3, SQLAlchemy 2.0.36, pydantic 2.10.4, httpx 0.28.1, pymupdf 1.28.2 — all identical to run 1.
- Basetemp for this run: `C:/Users/moham/AppData/Local/Temp/ep-pt2` — short on purpose, departing from the "under the scratchpad" convention, because run 1's long scratchpad basetemp (`.../claude/g--dev--2--dev-ep-platform-merged/<session-uuid>/scratchpad/pytest-temp-full`, ~140 characters before any test's own nested names) pushed several fixtures' combined paths past the Windows 260-character `MAX_PATH` limit.

## Command

```
cd "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend" && PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= ./venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider -rs --basetemp="C:/Users/moham/AppData/Local/Temp/ep-pt2" --junitxml="G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.xml" 2>&1 | tee "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/full-suite.log"
```

The frontend build was not repeated (unchanged since run 1, per task).

## Per-file results (from full-suite.xml)

Only files with a failure or error are shown inline; the complete 129-file table is below.

| test file | passed | failed | error | skipped |
|---|---|---|---|---|
| tests/test_persistence.py | 2 | 1 | 0 | 0 |
| tests/test_proposed_materials.py | 15 | 1 | 0 | 0 |

<details>
<summary>Full per-file table (129 files)</summary>

| test file | passed | failed | error | skipped |
|---|---|---|---|---|
| tests/test_ai_assist.py | 32 | 0 | 0 | 0 |
| tests/test_ai_evaluation.py | 20 | 0 | 0 | 0 |
| tests/test_ai_sheet_reader.py | 7 | 0 | 0 | 0 |
| tests/test_ai_verification.py | 16 | 0 | 0 | 0 |
| tests/test_amplifier_calculation.py | 31 | 0 | 0 | 0 |
| tests/test_auth.py | 11 | 0 | 0 | 0 |
| tests/test_battery_api.py | 21 | 0 | 0 | 0 |
| tests/test_battery_calculation.py | 29 | 0 | 0 | 0 |
| tests/test_boq_candidates.py | 4 | 0 | 0 | 0 |
| tests/test_boq_corrections_v2.py | 1 | 0 | 0 | 0 |
| tests/test_boq_export.py | 14 | 0 | 0 | 0 |
| tests/test_boq_extraction_v2.py | 13 | 0 | 0 | 0 |
| tests/test_boq_geometry_v2.py | 10 | 0 | 0 | 0 |
| tests/test_boq_paste.py | 15 | 0 | 0 | 0 |
| tests/test_boq_provenance.py | 5 | 0 | 0 | 0 |
| tests/test_boq_revisions.py | 15 | 0 | 0 | 0 |
| tests/test_boq_selective_v2.py | 7 | 0 | 0 | 0 |
| tests/test_boq_verification_v2.py | 4 | 0 | 0 | 0 |
| tests/test_brands.py | 15 | 0 | 0 | 1 |
| tests/test_calc_integrity.py | 5 | 0 | 0 | 0 |
| tests/test_classification_evidence.py | 12 | 0 | 0 | 0 |
| tests/test_company_library.py | 24 | 0 | 0 | 0 |
| tests/test_compliance.py | 4 | 0 | 0 | 0 |
| tests/test_compliance_ai_autofill.py | 4 | 0 | 0 | 0 |
| tests/test_compliance_knowledge.py | 11 | 0 | 0 | 0 |
| tests/test_compliance_statements.py | 12 | 0 | 0 | 0 |
| tests/test_config_paths.py | 3 | 0 | 0 | 0 |
| tests/test_data_controls.py | 8 | 0 | 0 | 0 |
| tests/test_data_location.py | 2 | 0 | 0 | 0 |
| tests/test_datasheet_currents.py | 10 | 0 | 0 | 14 |
| tests/test_datasheet_library.py | 15 | 0 | 0 | 1 |
| tests/test_design_api.py | 11 | 0 | 0 | 0 |
| tests/test_design_sheet_extractor.py | 24 | 0 | 0 | 7 |
| tests/test_details_check.py | 4 | 0 | 0 | 0 |
| tests/test_divisions.py | 3 | 0 | 0 | 0 |
| tests/test_document_classification_pilot.py | 12 | 0 | 0 | 0 |
| tests/test_document_classification_v2.py | 14 | 0 | 0 | 0 |
| tests/test_document_control.py | 25 | 0 | 0 | 0 |
| tests/test_document_intake.py | 10 | 0 | 0 | 0 |
| tests/test_document_processing_v2.py | 11 | 0 | 0 | 0 |
| tests/test_document_routing.py | 3 | 0 | 0 | 0 |
| tests/test_document_sync.py | 12 | 0 | 0 | 0 |
| tests/test_draftsman_assignment.py | 1 | 0 | 0 | 0 |
| tests/test_drawing_log.py | 24 | 0 | 0 | 0 |
| tests/test_drawing_prep.py | 14 | 0 | 0 | 0 |
| tests/test_drawing_review.py | 11 | 0 | 0 | 0 |
| tests/test_drawing_review_outcome.py | 8 | 0 | 0 | 0 |
| tests/test_drawings_module.py | 24 | 0 | 0 | 0 |
| tests/test_drf_extractor.py | 8 | 0 | 0 | 3 |
| tests/test_ep_archive_models.py | 6 | 0 | 0 | 0 |
| tests/test_ep_directory.py | 28 | 0 | 0 | 0 |
| tests/test_ep_directory_rebind.py | 2 | 0 | 0 | 0 |
| tests/test_ep_resolver.py | 25 | 0 | 0 | 0 |
| tests/test_equipment_currents.py | 10 | 0 | 0 | 0 |
| tests/test_estimation.py | 2 | 0 | 0 | 0 |
| tests/test_extraction_m2.py | 12 | 0 | 0 | 0 |
| tests/test_extraction_m2_review.py | 22 | 0 | 0 | 0 |
| tests/test_extraction_m2_review02.py | 16 | 0 | 0 | 0 |
| tests/test_extraction_m2_review03.py | 7 | 0 | 0 | 0 |
| tests/test_extraction_pilot.py | 5 | 0 | 0 | 0 |
| tests/test_extraction_repair.py | 12 | 0 | 0 | 0 |
| tests/test_fa_cases.py | 9 | 0 | 0 | 0 |
| tests/test_fa_cases_pdf.py | 6 | 0 | 0 | 0 |
| tests/test_fa_efficiency.py | 11 | 0 | 0 | 0 |
| tests/test_fa_evidence.py | 37 | 0 | 0 | 0 |
| tests/test_fa_interfaces.py | 13 | 0 | 0 | 0 |
| tests/test_fa_opus_review.py | 14 | 0 | 0 | 0 |
| tests/test_fa_review_fixes.py | 64 | 0 | 0 | 0 |
| tests/test_fa_workflow.py | 12 | 0 | 0 | 0 |
| tests/test_file_sync_v2.py | 10 | 0 | 0 | 0 |
| tests/test_file_sync_v2_processing.py | 15 | 0 | 0 | 0 |
| tests/test_floor_aliases.py | 5 | 0 | 0 | 0 |
| tests/test_floor_schedule.py | 37 | 0 | 0 | 0 |
| tests/test_floor_schedule_titania.py | 9 | 0 | 0 | 0 |
| tests/test_floors_and_devices.py | 8 | 0 | 0 | 0 |
| tests/test_identity.py | 4 | 0 | 0 | 0 |
| tests/test_ifc_boq.py | 35 | 0 | 0 | 1 |
| tests/test_ifc_platform.py | 23 | 0 | 0 | 0 |
| tests/test_ifc_worker_and_ai.py | 41 | 0 | 0 | 0 |
| tests/test_ifc_zip_import.py | 15 | 0 | 0 | 0 |
| tests/test_job_thread_sessions.py | 1 | 0 | 0 | 0 |
| tests/test_jobs_and_eligibility.py | 6 | 0 | 0 | 0 |
| tests/test_log_scan_jobs.py | 1 | 0 | 0 | 0 |
| tests/test_logs_register.py | 6 | 0 | 0 | 0 |
| tests/test_m2_pilot_eval.py | 10 | 0 | 0 | 0 |
| tests/test_m2_review05.py | 22 | 0 | 0 | 0 |
| tests/test_m2_review05_boq.py | 11 | 0 | 0 | 0 |
| tests/test_merge_integration.py | 8 | 0 | 0 | 0 |
| tests/test_migrations.py | 1 | 0 | 0 | 0 |
| tests/test_persistence.py | 2 | 1 | 0 | 0 |
| tests/test_power_calculation.py | 17 | 0 | 0 | 0 |
| tests/test_power_supply_currents.py | 3 | 0 | 0 | 0 |
| tests/test_prep_readiness.py | 4 | 0 | 0 | 0 |
| tests/test_project_directory.py | 4 | 0 | 0 | 0 |
| tests/test_project_folders.py | 6 | 0 | 0 | 0 |
| tests/test_project_log_and_drawing_scan.py | 22 | 0 | 0 | 0 |
| tests/test_project_register.py | 7 | 0 | 0 | 0 |
| tests/test_project_state.py | 8 | 0 | 0 | 0 |
| tests/test_projects.py | 39 | 0 | 0 | 0 |
| tests/test_proposed_materials.py | 15 | 1 | 0 | 0 |
| tests/test_provider_honesty.py | 17 | 0 | 0 | 0 |
| tests/test_rbac.py | 35 | 0 | 0 | 0 |
| tests/test_redesign.py | 16 | 0 | 0 | 0 |
| tests/test_reextraction.py | 20 | 0 | 0 | 1 |
| tests/test_render_bounds.py | 10 | 0 | 0 | 0 |
| tests/test_repair_tool.py | 3 | 0 | 0 | 0 |
| tests/test_review_duplicates_and_concurrency.py | 8 | 0 | 0 | 0 |
| tests/test_review_fixes.py | 47 | 0 | 0 | 0 |
| tests/test_review_production.py | 6 | 0 | 0 | 0 |
| tests/test_sample_request.py | 3 | 0 | 0 | 0 |
| tests/test_schedule_materials.py | 5 | 0 | 0 | 0 |
| tests/test_scoped_drawing_review.py | 12 | 0 | 0 | 0 |
| tests/test_shop_boq.py | 3 | 0 | 0 | 0 |
| tests/test_spec_finder.py | 6 | 0 | 0 | 1 |
| tests/test_stale_writes.py | 2 | 0 | 0 | 0 |
| tests/test_submittal.py | 27 | 0 | 0 | 0 |
| tests/test_submittal_ai.py | 9 | 0 | 0 | 0 |
| tests/test_submittal_one_per_system.py | 7 | 0 | 0 | 0 |
| tests/test_submittal_package.py | 65 | 0 | 0 | 0 |
| tests/test_submittal_scanner.py | 16 | 0 | 0 | 1 |
| tests/test_sync_worker.py | 18 | 0 | 0 | 0 |
| tests/test_system_rules.py | 1 | 0 | 0 | 0 |
| tests/test_transmittals.py | 18 | 0 | 0 | 0 |
| tests/test_user_activity.py | 10 | 0 | 0 | 0 |
| tests/test_user_delete.py | 6 | 0 | 0 | 0 |
| tests/test_values.py | 53 | 0 | 0 | 0 |
| tests/test_ve_calculation.py | 15 | 0 | 0 | 0 |
| tests/test_ve_workbook_reader.py | 26 | 0 | 0 | 5 |
| tests/test_worker_runtime.py | 11 | 0 | 0 | 0 |

</details>

## Failures (2), verbatim assertion/traceback tail

1. **tests/test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches**

   ```
   tmp_path = WindowsPath('C:/Users/moham/AppData/Local/Temp/ep-pt2/test_a_data_root_gathers_the_d0')
   monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000116A5C77860>

       def test_a_data_root_gathers_the_database_uploads_backups_and_caches(tmp_path, monkeypatch):
           # The test process sets these for the suite; a fresh Settings must not see them.
           for name in ("DATABASE_URL", "UPLOADS_ROOT", "CACHE_ROOT", "DATA_ROOT", "BACKUPS_ROOT"):
               monkeypatch.delenv(name, raising=False)
           # _env_file=None: nor may it read this PC's backend/.env, so the code's own defaults are what is tested.
           root = tmp_path / "EP Platform"
           s = Settings(data_root=str(root), secret_key="x", _env_file=None)
           assert s.database_url == "sqlite:///" + (root / "ep_platform.db").as_posix()
           assert Path(s.uploads_root) == root / "uploads"
           assert Path(s.cache_root) == root / ".cache"
           assert Path(s.backups_root) == root / "backups"
           # Set explicitly, a location is kept as set.
           s = Settings(data_root=str(root), database_url="sqlite:///elsewhere.db", uploads_root="here", secret_key="x", _env_file=None)
           assert s.database_url == "sqlite:///elsewhere.db" and s.uploads_root == "here"
           # Without it, nothing moves.
   >       s = Settings(secret_key="x", _env_file=None)
   E       AssertionError: assert ('G:\\dev (2)\\dev\\ep-platform-merged\\data' is None)
   E        +  where 'G:\\dev (2)\\dev\\ep-platform-merged\\data' = Settings(app_name='Engineering Project Platform', app_tagline='Engineering a Safer Tomorrow', company_name='Al Arabia ...detect=False, compliance_knowledge_import_on_start=False, archive_datasheet_libraries={}, archive_submittal_library='').data_root

   tests\test_persistence.py:119: AssertionError
   ```

   Same real-path assertion as run 1's failure 6. Per the HEAD note above, this run's traceback source display reflects the post-`d47fa70` text (`_env_file=None` already in all three calls), but `d47fa70` landed about two minutes into this run, almost certainly after pytest had already imported the module; whether the bytecode that actually executed was pre- or post-fix is not established by this run.

2. **tests/test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it**

   ```
   numbers = {e.part_no for e in part_catalog.catalog(db_session, "EDWARDS")}
   >       assert {"4-CPU", "3-SDDC2", "3-SSDC2", "SIGA-OSD-FCN", "SIGA-PS"} <= numbers    # datasheet names, the BOQ
   E       AssertionError: assert {'3-SDDC2', '...N', 'SIGA-PS'} <= {'3-CAB14B', ...3-CHAS4', ...}
   E
   E         Extra items in the left set:
   E         'SIGA-OSD-FCN'
   E         '3-SDDC2'
   E         '3-SSDC2'

   tests\test_proposed_materials.py:108: AssertionError
   ```

   Identical to run 1's failure 7 and to `docs/milestones/M4/evidence/diagnosis-2026-10-07/FIVE-PREEXISTING-FAILURES.md` item 5 (CODE DEFECT: `part_catalog.catalog` never reads the datasheet library by file name).

No errors this run (0, vs 27 in run 1, all in `tests/test_ep_directory.py`); that file's 28 tests all passed under the short basetemp.

## Skips (35)

| count | reason |
|---|---|
| 33 | "Set EP_PLATFORM_LIVE_ARCHIVE_ROOT to run against the real archive" |
| 1 | "the Menvier library is not held on this machine" |
| 1 | "needs a DWG converter and the FA-105 DWG/DXF pair" |

By file: test_datasheet_currents.py (14), test_design_sheet_extractor.py (7), test_ve_workbook_reader.py (5), test_drf_extractor.py (3), test_brands.py (1), test_datasheet_library.py (1), test_ifc_boq.py (1), test_reextraction.py (1), test_spec_finder.py (1), test_submittal_scanner.py (1) — identical in count and file to run 1. None are Tesseract-related.

## Expected on Linux: Windows-only behavior

Not applicable to this run (Windows). Listed here only for cross-reference with the Linux comparison table below: `test_ifc_zip_import.py::test_a_member_that_climbs_out_of_the_folder_is_left_behind` (two backslash cases), `test_provider_honesty.py::test_the_cli_path_expands_the_users_own_folders`, `test_drawing_log.py::test_a_drawing_down_a_long_path_can_still_be_opened`.

## Comparison with run 1 and the Linux runs

### Run 1's failures and errors, result in this run

| # | Test (run 1) | Run 1 result | This run's result |
|---|---|---|---|
| 1 | test_compliance.py::test_the_specification_of_each_system_is_found | failed — Windows `MAX_PATH` under the long basetemp | **passed** |
| 2 | test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index | failed — pre-existing (FIVE-PREEXISTING-FAILURES item 2) | **passed** (fixed by `f6ab349`: migrate with foreign keys off) |
| 3 | test_ep_directory_rebind.py::test_rebinds_only_existing_relative_project_folders | failed — Windows `MAX_PATH` under the long basetemp | **passed** |
| 4 | test_extraction_m2_review.py::test_an_engineer_confirmed_revision_survives_a_new_reading_that_says_otherwise | failed — Windows `MAX_PATH` under the long basetemp | **passed** |
| 5 | test_migrations.py::test_migrations_build_the_schema_the_models_describe | failed — pre-existing (FIVE-PREEXISTING-FAILURES item 1) | **passed** (fixed by `f6ab349`: conftest drops `_alembic_tmp_` tables) |
| 6 | test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches | failed — not yet diagnosed (.env leak) | **failed**, same assertion — see Failure 1 above and the HEAD-race note |
| 7 | test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it | failed — pre-existing (FIVE-PREEXISTING-FAILURES item 5, CODE DEFECT) | **failed**, same assertion — see Failure 2 above |
| 8 | test_submittal_package.py::test_a_built_package_is_filed_in_the_project_folder_and_entered_in_the_register_and_the_log | failed — Windows `MAX_PATH` under the long basetemp | **passed** |
| 9 | test_submittal_package.py::test_a_revision_already_prepared_is_refused_unless_replaced_and_deleting_takes_the_file_with_it | failed — Windows `MAX_PATH` under the long basetemp | **passed** |
| — | 27 errors, all tests/test_ep_directory.py (`archive` fixture, Windows `MAX_PATH` under the long basetemp) | 27 errors | **all 28 tests in that file passed** (0 errors) |

Of run 1's 9 failures and 27 errors, 7 failures and all 27 errors are resolved by the short basetemp alone (6 of the 9 failures, plus the 27 errors, were the path-length artifact run 1 diagnosed); 2 of the 5 pre-existing/repaired failures (archive-model, migrations) are now fixed by `f6ab349`'s repairs; 2 failures remain (test_persistence, test_proposed_materials), both already known to run 1 and neither new.

### The nine Linux failures, result in this run

| # | Test | Category (Linux) | Result on this Windows run |
|---|---|---|---|
| 1 | test_ifc_zip_import.py::test_a_member_that_climbs_out_of_the_folder_is_left_behind | Windows-only, accepted failing on Linux | **passed** (all 6 parametrized cases) |
| 2 | test_provider_honesty.py::test_the_cli_path_expands_the_users_own_folders | Windows-only, accepted failing on Linux | **passed** |
| 3 | test_drawing_log.py::test_a_drawing_down_a_long_path_can_still_be_opened | Windows-only, accepted failing on Linux | **passed** |
| 4 | test_extraction_m2_review.py::test_an_ocr_failure_on_one_page_is_noted_and_the_batch_continues | needs Tesseract | **not found under that name in that file**, as in run 1. A same-named test exists in a different file, `tests/test_file_sync_v2_processing.py::test_an_ocr_failure_on_one_page_is_noted_and_the_batch_continues` (passed), but it is a distinct, pre-existing test, not a rename — confirmed by its definition at `backend/tests/test_file_sync_v2_processing.py:465`, unrelated to the extraction-m2-review module. Its successors in `test_extraction_m2_review.py`, named as run 1 named them — `test_an_ocr_failure_on_a_changed_scan_keeps_the_previous_complete_reading_as_a_partial_attempt` and `test_a_changed_scan_without_ocr_is_a_partial_attempt_not_an_empty_complete_reading` — both **passed** with Tesseract present. |
| 5 | test_migrations.py::test_migrations_build_the_schema_the_models_describe | pre-existing | **passed** (fixed by `f6ab349`) |
| 6 | test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index | pre-existing | **passed** (fixed by `f6ab349`) |
| 7 | test_ai_assist.py::test_unprocessed_pages_trigger_attention_even_when_rows_look_valid | pre-existing | **passed** |
| 8 | test_drawings_module.py::test_open_folder_is_the_systems_own_and_only_for_a_browser_on_this_pc | pre-existing | **passed** |
| 9 | test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it | pre-existing | **failed**, same assertion — see Failure 2 above |

Of the nine: the three Windows-only tests (1-3) pass, as in run 1; the Tesseract-dependent test (4) still cannot be checked under its original name/file, and its likely successors pass, as in run 1; of the five pre-existing failures (5-9), two (5, 6) are now fixed by `f6ab349` and pass (an improvement over run 1, where they still reproduced), one (9) still fails unchanged, and two (7, 8) pass, as they did in run 1.

### Classification of the two remaining failures

- **test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it** — pre-existing and diagnosed: `docs/milestones/M4/evidence/diagnosis-2026-10-07/FIVE-PREEXISTING-FAILURES.md` item 5, a CODE DEFECT (`part_catalog.catalog` never reads the datasheet library by file name; present since the first commit, 09e943d; fails in every recorded run on every platform).
- **test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches** — the test_persistence .env finding, not yet diagnosed to a settled conclusion by this run. It is the same finding run 1 recorded (not among the original nine, not a path-length artifact: a fresh `Settings(secret_key="x", _env_file=None)` resolves `data_root` to this machine's real `backend/.env` value, `G:\dev (2)\dev\ep-platform-merged\data`, instead of `None`). Since run 1, a fix (`d47fa70`) was proposed and verified in isolation (`docs/milestones/M4/evidence/test-repairs-2026-10-07/VERIFICATION-02.md`: 3 passed with and without a one-line *scratch* `.env`), but that verification did not test against the real `backend/.env`, and this run's own result is compromised by the mid-run HEAD race described above — the displayed traceback shows the fixed source, but whether the fixed code actually executed is unknown. This finding needs a clean, isolated re-run (stable checkout, no concurrent commits) against the real `backend/.env` before it can be classified as fixed, still-open, or environment-specific.
- No failure in this run is new (not previously seen in run 1 or the Linux runs).

## Files

`full-suite.xml`, `full-suite.log`, this file, all under `docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/`. The frontend build log is not reproduced here (not re-run this time); see `docs/milestones/M4/evidence/tests-2026-10-07-windows/frontend-build.log` for run 1's.

## Limits

This run does not establish: real-model accuracy (`AI_ENABLED=false`); AutoCAD-dependent behaviour (no AutoCAD on this machine); PostgreSQL behaviour (fixtures use SQLite); behaviour against production data or the live archive (`EP_PLATFORM_LIVE_ARCHIVE_ROOT` unset, 33 tests skipped for this reason; the live database under `G:/dev (2)/dev/ep-platform-merged/data/` and the OneDrive project archive were never opened, read, or written; the live platform process running from this clone was not touched); milestone acceptance; or, for the reasons given above, a settled answer on whether `d47fa70`'s fix to `test_persistence.py` holds against the real `backend/.env` (the mid-run HEAD advance makes this run's own result for that one test inconclusive, though the assertion failure itself is verbatim and real).
