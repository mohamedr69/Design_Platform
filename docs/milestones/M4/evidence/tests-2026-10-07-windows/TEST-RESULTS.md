# M4 evidence: first full test-suite run on Windows

Date: 7 October 2026. Branch `claude/upbeat-lovelace-sa9j3w`. HEAD `2e407f87350f867f141e8ff1f076c0b9dc4bc781` ("Agent hooks call python, not python3, on the owner's Windows PC; session log", 2026-10-07T09:06:51+04:00).

Git status --short, before this run:

```
 M .claude/agents/ep-implementer.md
 M README.md
 M backend/.env.example
 M frontend/vite.config.ts
 M stop-backend.bat
?? docs/milestones/M4/evidence/m2-closure-package-2026-10-06/
```

Git status --short, after this run:

```
 M .claude/agents/ep-implementer.md
 M README.md
 M backend/.env.example
 M backend/library/symbols/symbol_library.json
 M frontend/vite.config.ts
 M stop-backend.bat
?? docs/milestones/M4/evidence/m2-closure-package-2026-10-06/
?? docs/milestones/M4/evidence/policy-2026-10-07/
?? docs/milestones/M4/evidence/tests-2026-10-07-windows/
```

Two differences from "before" are not this agent's edits: `backend/library/symbols/symbol_library.json` picked up a one-line change (`exported_at` timestamp only, `2026-10-06T21:29:34` -> `2026-10-07T09:08:49`) as a side effect of running the backend test suite — some test or fixture exports the symbol library to its real repository path rather than a tmp_path, and the full suite was never run on this branch on Windows before now. `docs/milestones/M4/evidence/policy-2026-10-07/` is untracked and was not created by this agent; it was present by the time of the second status check, presumably written by another process during this run. Neither was touched, reverted, or staged by this agent, per the no-checkout-mutation rule.

## Result

**9 failed, 1748 passed, 35 skipped, 27 errors, 855 warnings, 1819 tests, in 1605.69s (0:26:45)**

## Environment

- OS: Windows 10 Home 10.0.19045 (Git Bash / MINGW64, `LAPTOP-IL4L4UAJ`, kernel string `3.6.10-710e5275.x86_64`).
- Python: `backend/venv/Scripts/python.exe` — Python 3.12.10.
- Node: v24.14.0. npm: 11.9.0.
- Tesseract: present, not on PATH, found via `app/core/config.py:49-52`. `"/c/Program Files/Tesseract-OCR/tesseract.exe" --version` -> `tesseract v5.4.0.20240606`, leptonica-1.84.1 (libgif 5.2.1, libjpeg-turbo 3.0.1, libpng 1.6.43, libtiff 4.6.0, zlib 1.3, libwebp 1.4.0, libopenjp2 2.5.2), libarchive 3.7.4.
- No AutoCAD. No PostgreSQL. `EP_PLATFORM_LIVE_ARCHIVE_ROOT` unset (no live archive). `AI_ENABLED=false`, `DATA_ROOT=` (empty) passed on the command line.
- Packages: pytest 8.3.4, fastapi 0.115.6, starlette 0.41.3, SQLAlchemy 2.0.36, pydantic 2.10.4, httpx 0.28.1, pymupdf 1.28.2.

## Commands

Backend, from `backend/`:

```
cd "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend" && PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= ./venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider \
  --basetemp="C:/Users/moham/AppData/Local/Temp/claude/g--dev--2--dev-ep-platform-merged/d223f746-dc1e-49c3-9577-b38529525a1e/scratchpad/pytest-temp-full" \
  --junitxml="G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M4/evidence/tests-2026-10-07-windows/full-suite.xml" \
  2>&1 | tee "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M4/evidence/tests-2026-10-07-windows/full-suite.log"
```

Frontend, from `frontend/` (node_modules already present; `npm install` was not run):

```
cd "G:/dev (2)/dev/ep-platform-merged/ep-platform/frontend" && npm run build 2>&1 | tee "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M4/evidence/tests-2026-10-07-windows/frontend-build.log"
```

## Per-file results (from full-suite.xml)

Only files with a failure or error are shown inline; the complete 129-file table is below.

| test file | passed | failed | error | skipped |
|---|---|---|---|---|
| tests/test_compliance.py | 3 | 1 | 0 | 0 |
| tests/test_ep_archive_models.py | 5 | 1 | 0 | 0 |
| tests/test_ep_directory.py | 1 | 0 | 27 | 0 |
| tests/test_ep_directory_rebind.py | 1 | 1 | 0 | 0 |
| tests/test_extraction_m2_review.py | 21 | 1 | 0 | 0 |
| tests/test_migrations.py | 0 | 1 | 0 | 0 |
| tests/test_persistence.py | 2 | 1 | 0 | 0 |
| tests/test_proposed_materials.py | 15 | 1 | 0 | 0 |
| tests/test_submittal_package.py | 63 | 2 | 0 | 0 |

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
| tests/test_compliance.py | 3 | 1 | 0 | 0 |
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
| tests/test_ep_archive_models.py | 5 | 1 | 0 | 0 |
| tests/test_ep_directory.py | 1 | 0 | 27 | 0 |
| tests/test_ep_directory_rebind.py | 1 | 1 | 0 | 0 |
| tests/test_ep_resolver.py | 25 | 0 | 0 | 0 |
| tests/test_equipment_currents.py | 10 | 0 | 0 | 0 |
| tests/test_estimation.py | 2 | 0 | 0 | 0 |
| tests/test_extraction_m2.py | 12 | 0 | 0 | 0 |
| tests/test_extraction_m2_review.py | 21 | 1 | 0 | 0 |
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
| tests/test_migrations.py | 0 | 1 | 0 | 0 |
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
| tests/test_submittal_package.py | 63 | 2 | 0 | 0 |
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

## Failures (9), verbatim assertion/traceback tail

1. **tests/test_compliance.py::test_the_specification_of_each_system_is_found**

   ```
   venv\Lib\site-packages\pymupdf\mupdf.py:60655: in pdf_save_document
   >       return _mupdf.pdf_save_document(doc, filename, opts)
   E       pymupdf.mupdf.FzErrorSystem: code=2: cannot open file 'C:\Users\moham\AppData\Local\Temp\claude\g--dev--2--dev-ep-platform-merged\d223f746-dc1e-49c3-9577-b38529525a1e\scratchpad\pytest-temp-full\test_the_specification_of_each0\EP-30784\02- inputs\Specification\283111 - ADDRESSABLE FIRE DETEC...'
   ```
   The full path under this run's `--basetemp` plus the test's own nested folder names exceeds the Windows path-length limit; MuPDF's `save()` cannot open the destination file. Root cause is the length of the mandated `--basetemp`, not application code.

2. **tests/test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index**

   ```
   venv\Lib\site-packages\sqlalchemy\engine\default.py:941: in do_execute
   >       cursor.execute(statement, parameters)
   E       sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
   E       [SQL:
   E       DROP TABLE users]
   E       (Background on this error at: https://sqlalche.me/e/20/gkpj)
   ```
   Matches the pre-existing failure recorded in `docs/milestones/M4/evidence/diagnosis-2026-10-07/FIVE-PREEXISTING-FAILURES.md`.

3. **tests/test_ep_directory_rebind.py::test_rebinds_only_existing_relative_project_folders**

   ```
   tests\test_ep_directory_rebind.py:10: in test_rebinds_only_existing_relative_project_folders
   >       present.mkdir(parents=True)
   ...
   C:\Users\moham\AppData\Local\Programs\Python\Python312\Lib\pathlib.py:1311: FileNotFoundError
   E       FileNotFoundError: [WinError 206] The filename or extension is too long: 'C:\\Users\\moham\\AppData\\Local\\Temp\\claude\\g--dev--2--dev-ep-platform-merged\\d223f746-dc1e-49c3-9577-b38529525a1e\\scratchpad\\pytest-temp-full\\test_rebinds_only_existing_rel0\\current\\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects\\Contractor\\EP-40001 Tower'
   ```
   Same path-length root cause as (1).

4. **tests/test_extraction_m2_review.py::test_an_engineer_confirmed_revision_survives_a_new_reading_that_says_otherwise**

   ```
   tests\test_document_sync.py:67: in _pdf
       doc.save(path)
   venv\Lib\site-packages\pymupdf\mupdf.py:60655: in pdf_save_document
   >       return _mupdf.pdf_save_document(doc, filename, opts)
   E       pymupdf.mupdf.FzErrorSystem: code=2: cannot open file 'C:\Users\moham\AppData\Local\Temp\claude\g--dev--2--dev-ep-platform-merged\d223f746-dc1e-49c3-9577-b38529525a1e\scratchpad\pytest-temp-full\test_an_engineer_confirmed_rev0\EP-30906\03- Drawings\SD\FA\05. Ground Floor\R0\Submitted\BBY006-...'
   ```
   Same path-length root cause as (1). This is a different test than the Linux OCR failure recorded for this file (see "Comparison with the Linux runs" below); `test_an_ocr_failure_on_one_page_is_noted_and_the_batch_continues` no longer exists in `test_extraction_m2_review.py` under that name.

5. **tests/test_migrations.py::test_migrations_build_the_schema_the_models_describe**

   ```
   >       assert compare_metadata(context, Base.metadata) == []
   E       AssertionError: assert [('remove_tab...schema=None))] == []
   E
   E         Left contains one more item: ('remove_table', Table('_alembic_tmp_project_redesign', MetaData(), Column('id', INTEGER(), table=<_alembic_tmp_projec...ject_redesign>), Column('updated_at', DATETIME(), table=<_alembic_tmp_project_redesign>, nullable=False), schema=None))
   E         Use -v to get more diff
   tests\test_migrations.py:15: AssertionError
   ```
   Matches the pre-existing failure in `FIVE-PREEXISTING-FAILURES.md`.

6. **tests/test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches**

   ```
   s = Settings(secret_key="x")
   >       assert s.data_root is None and s.database_url == "sqlite:///./ep_platform.db" and s.backups_root.endswith("backups")
   E       AssertionError: assert ('G:\\dev (2)\\dev\\ep-platform-merged\\data' is None)
   E        +  where 'G:\\dev (2)\\dev\\ep-platform-merged\\data' = Settings(app_name='Engineering Project Platform', ...).data_root
   tests\test_persistence.py:119: AssertionError
   ```
   The test clears `DATA_ROOT` (and other env vars) with `monkeypatch.delenv` and then builds `Settings(secret_key="x")` expecting no data_root; on this machine `Settings` still resolved `data_root` to the real `G:\dev (2)\dev\ep-platform-merged\data` path, i.e. pydantic's `Settings` read it from `backend/.env` once the environment variable itself was deleted. The command-line `DATA_ROOT=` only prevents the live value from being picked up via the environment; it does not stop this test's own `delenv` + default-`.env`-fallback path from reaching the real `DATA_ROOT` value recorded in `backend/.env`. Not among the nine known failures; not a path-length artifact.

7. **tests/test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it**

   ```
   numbers = {e.part_no for e in part_catalog.catalog(db_session, "EDWARDS")}
   >       assert {"4-CPU", "3-SDDC2", "3-SSDC2", "SIGA-OSD-FCN", "SIGA-PS"} <= numbers    # datasheet names, the BOQ
   E       AssertionError: assert {'3-SDDC2', '...N', 'SIGA-PS'} <= {'3-CAB14B', ...3-CHAS4', ...}
   E
   E         Extra items in the left set:
   E         '3-SSDC2'
   E         '3-SDDC2'
   E         'SIGA-OSD-FCN'
   tests\test_proposed_materials.py:108: AssertionError
   ```
   Matches the pre-existing failure in `FIVE-PREEXISTING-FAILURES.md`.

8. **tests/test_submittal_package.py::test_a_built_package_is_filed_in_the_project_folder_and_entered_in_the_register_and_the_log**

   ```
   filed = root / "02- Material Submittals" / "FA" / "R0" / "Submitted" / "EP-30785 - Material Submittal - FA - R0.pdf"
   >       assert filed.is_file() and filed.read_bytes() == resp.content
   E       AssertionError: assert (False)
   E        +  where False = is_file()
   E        +    where is_file = WindowsPath('C:/Users/moham/AppData/Local/Temp/claude/g--dev--2--dev-ep-platform-merged/d223f746-dc1e-49c3-9577-b38529...built_package_is_filed_0/EP-30785/02- Material Submittals/FA/R0/Submitted/EP-30785 - Material Submittal - FA - R0.pdf').is_file
   tests\test_submittal_package.py:1167: AssertionError
   ```
   The HTTP response (200, PDF content) was produced, but the file was not found on disk at the expected nested path under the long `--basetemp`; consistent with the same path-length limit as (1), silently swallowed by the write path rather than raised, but not independently confirmed (no exception captured in this test's own traceback).

9. **tests/test_submittal_package.py::test_a_revision_already_prepared_is_refused_unless_replaced_and_deleting_takes_the_file_with_it**

   ```
   filed = root / "02- Material Submittals" / "FA" / "R0" / "Submitted" / "EP-30786 - Material Submittal - FA - R0.pdf"
   >       assert filed.is_file()
   E       AssertionError: assert False
   E        +  where False = is_file()
   E        +    where is_file = WindowsPath('C:/Users/moham/AppData/Local/Temp/claude/g--dev--2--dev-ep-platform-merged/d223f746-dc1e-49c3-9577-b38529...revision_already_prepar0/EP-30786/02- Material Submittals/FA/R0/Submitted/EP-30786 - Material Submittal - FA - R0.pdf').is_file
   tests\test_submittal_package.py:1266: AssertionError
   ```
   Same pattern as (8).

## Errors (27), all in tests/test_ep_directory.py

All 27 errors are `ERROR at setup`, same root cause: the `archive` fixture (tests/test_ep_directory.py:19) does `(tmp_path / "SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects" / "Client A" / "EP-29495 IVY Garden 2" / "Scan Document").mkdir(parents=True)`, and under this run's long `--basetemp` the resulting path exceeds the Windows limit:

```
E           FileNotFoundError: [WinError 206] The filename or extension is too long: 'C:\\Users\\moham\\AppData\\Local\\Temp\\claude\\g--dev--2--dev-ep-platform-merged\\d223f746-dc1e-49c3-9577-b38529525a1e\\scratchpad\\pytest-temp-full\\<test-name>0\\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects\\Client A\\EP-29495 IVY Garden 2'
```

Affected test ids (all errors, no passes among these 27):
test_scan_indexes_every_ep_folder_and_never_descends_into_one, test_scan_stores_paths_below_the_root_so_the_index_is_not_one_users, test_the_same_archive_under_another_profile_reuses_the_index, test_rescanning_adds_the_new_folder_and_leaves_the_rest_alone, test_a_removed_folder_is_kept_as_history_and_stops_being_suggested, test_a_scan_that_read_nothing_concludes_nothing_is_gone, test_one_unreadable_folder_does_not_hold_the_rest_of_the_index_back, test_a_folder_that_comes_back_is_the_same_row_again, test_search_suggests_while_the_number_is_still_being_typed, test_search_reads_the_ep_prefix_the_way_it_is_typed[EP-294], test_search_reads_the_ep_prefix_the_way_it_is_typed[ep 294], test_search_reads_the_ep_prefix_the_way_it_is_typed[EP294], test_search_reads_the_ep_prefix_the_way_it_is_typed[ 294 ], test_search_finds_a_project_by_its_name, test_search_says_when_the_platform_already_has_the_project, test_search_ignores_a_query_too_short_to_narrow_anything, test_search_puts_the_exact_number_first, test_the_search_endpoint_serves_suggestions_to_anyone_signed_in, test_the_status_endpoint_reports_what_is_indexed, test_only_the_project_roles_may_rebuild_the_index, test_a_search_with_nothing_indexed_suggests_nothing_rather_than_failing, test_find_project_answers_from_the_index_without_walking, test_a_number_added_since_the_last_scan_is_still_found_and_then_indexed, test_duplicate_ep_numbers_still_reach_the_folder_picker, test_the_refresh_is_due_only_once_the_last_scan_is_old_enough, test_a_scan_that_trips_on_a_folder_still_paces_the_next_one, test_a_dry_run_names_the_new_numbers_and_writes_nothing.

This is an artifact of the mandated `--basetemp` path length (the scratchpad path itself is ~140 characters before the test adds its own nested folder names of up to ~95 more characters), not a code regression. It was not retried with a shorter `--basetemp`, per instructions to run the exact command given.

## Skips (35)

| count | reason |
|---|---|
| 33 | "Set EP_PLATFORM_LIVE_ARCHIVE_ROOT to run against the real archive" |
| 1 | "the Menvier library is not held on this machine" |
| 1 | "needs a DWG converter and the FA-105 DWG/DXF pair" |

By file: test_datasheet_currents.py (14), test_design_sheet_extractor.py (7), test_ve_workbook_reader.py (5), test_drf_extractor.py (3), test_brands.py (1), test_datasheet_library.py (1), test_ifc_boq.py (1), test_reextraction.py (1), test_spec_finder.py (1), test_submittal_scanner.py (1). None are Tesseract-related — Tesseract is present on this machine.

## Frontend build

**Succeeded.**

```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.2.2 building client environment for production...
transforming...
✓ 120 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     0.49 kB │ gzip:   0.31 kB
dist/assets/index-DuAyB9mb.css     81.22 kB │ gzip:  14.42 kB
dist/assets/index-Dkb7kX2i.js   1,209.91 kB │ gzip: 296.91 kB

✓ built in 1.62s
```

`node_modules` was already present; `npm install`/`npm ci` was not run.

## Comparison with the Linux runs

The Linux full suite on this branch gave 9 failures (`docs/milestones/M4/README.md`; `docs/milestones/M4/evidence/diagnosis-2026-10-07/FIVE-PREEXISTING-FAILURES.md`):

| # | Test | Category (Linux) | Result on this Windows run |
|---|---|---|---|
| 1 | test_ifc_zip_import.py::test_a_member_that_climbs_out_of_the_folder_is_left_behind | (a) Windows-only, accepted failing on Linux | **passed** (all 6 parametrized cases: `../../evil.dxf`, `/etc/evil.dxf`, `C:/evil.dxf`, `sub/../../evil.dxf`, `\\etc\\evil.dxf`, `..\\..\\evil.dxf`) |
| 2 | test_provider_honesty.py::test_the_cli_path_expands_the_users_own_folders | (a) Windows-only, accepted failing on Linux | **passed** |
| 3 | test_drawing_log.py::test_a_drawing_down_a_long_path_can_still_be_opened | (a) Windows-only, accepted failing on Linux | **passed** |
| 4 | test_extraction_m2_review.py::test_an_ocr_failure_on_one_page_is_noted_and_the_batch_continues | (b) needs Tesseract | **not found** — no test of this name exists in tests/test_extraction_m2_review.py on this HEAD (checked by name and by grep of `def test_` in the file). The file's two OCR-failure-shaped tests present now — test_an_ocr_failure_on_a_changed_scan_keeps_the_previous_complete_reading_as_a_partial_attempt and test_a_changed_scan_without_ocr_is_a_partial_attempt_not_an_empty_complete_reading — both **passed** with Tesseract present. |
| 5 | test_migrations.py::test_migrations_build_the_schema_the_models_describe | (c) pre-existing | **failed**, same assertion (`_alembic_tmp_project_redesign` leftover table) — see Failure 5 above |
| 6 | test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index | (c) pre-existing | **failed**, same error (`IntegrityError: FOREIGN KEY constraint failed` on `DROP TABLE users`) — see Failure 2 above |
| 7 | test_ai_assist.py::test_unprocessed_pages_trigger_attention_even_when_rows_look_valid | (c) pre-existing | **passed** |
| 8 | test_drawings_module.py::test_open_folder_is_the_systems_own_and_only_for_a_browser_on_this_pc | (c) pre-existing | **passed** |
| 9 | test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it | (c) pre-existing | **failed**, same assertion (extra part numbers `3-SSDC2`, `3-SDDC2`, `SIGA-OSD-FCN`) — see Failure 7 above |

Of the nine, 3 of 3 Windows-only tests (1-3) now pass as expected on their native platform; the Tesseract-dependent test (4) could not be checked under its recorded name because that test no longer exists under that name on this HEAD — its likely successors pass with Tesseract present; and 3 of the 5 pre-existing failures (5, 6, 9) reproduce unchanged on Windows. Two of the five pre-existing failures (7, 8) did not reproduce here — they passed on this run.

### New on Windows (not among the nine)

| # | Test | Cause |
|---|---|---|
| 1 | test_compliance.py::test_the_specification_of_each_system_is_found | Windows `MAX_PATH` exceeded under the mandated long `--basetemp` (pymupdf `FzErrorSystem`, "cannot open file") |
| 2 | test_ep_directory_rebind.py::test_rebinds_only_existing_relative_project_folders | Windows `MAX_PATH` exceeded under the mandated long `--basetemp` (`WinError 206`) |
| 3 | test_extraction_m2_review.py::test_an_engineer_confirmed_revision_survives_a_new_reading_that_says_otherwise | Windows `MAX_PATH` exceeded under the mandated long `--basetemp` (pymupdf `FzErrorSystem`) |
| 4 | test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches | `Settings(secret_key="x")` resolved `data_root` to the real `backend/.env` value (`G:\dev (2)\dev\ep-platform-merged\data`) after the test's own `monkeypatch.delenv`, instead of `None` |
| 5 | test_submittal_package.py::test_a_built_package_is_filed_in_the_project_folder_and_entered_in_the_register_and_the_log | Filed PDF not found on disk at the expected path under the long `--basetemp`; HTTP response itself was correct |
| 6 | test_submittal_package.py::test_a_revision_already_prepared_is_refused_unless_replaced_and_deleting_takes_the_file_with_it | Same as (5) |
| — | 27 errors, all tests/test_ep_directory.py (listed above) | Windows `MAX_PATH` exceeded in the `archive` fixture under the long `--basetemp` |

6 of the 9 Windows failures (1, 2, 3, 5, 6, and the 27 errors) share one root cause: the mandated `--basetemp` is itself long (the scratchpad path alone is well over 100 characters), and several tests build further nested folder/file names on top of it (client/project/system folder names of 40-95 characters) that push the combined path past the Windows 260-character `MAX_PATH` limit. This was not worked around (no shorter `--basetemp` was substituted) because the task specified the exact `--basetemp` value to use. Test 4 (`test_persistence`) is unrelated to path length and is a genuine environment-leak finding: this machine's `backend/.env` sets a real `DATA_ROOT`, and the test's reliance on `monkeypatch.delenv` plus `Settings()`'s own `.env` fallback surfaces that real value instead of `None`.

## Limits

This run does not establish: real-model accuracy (`AI_ENABLED=false`, scripted/no AI providers used); AutoCAD-dependent behaviour (no AutoCAD on this machine, not exercised); PostgreSQL behaviour (fixtures use SQLite); behaviour against production data or the live archive (`EP_PLATFORM_LIVE_ARCHIVE_ROOT` unset, 33 tests skipped for this reason, and the live database under `G:/dev (2)/dev/ep-platform-merged/data/` and the OneDrive project archive were never opened, read, or written); or milestone acceptance. It also does not establish behaviour at normal (short) temp-directory path lengths, since 6 of the 9 failures and all 27 errors trace to the specific long `--basetemp` used for this evidence run, not to the code under test.

## Files

`full-suite.xml`, `full-suite.log`, `frontend-build.log`, this file, all under `docs/milestones/M4/evidence/tests-2026-10-07-windows/`.
