# Addendum to run 2: the persistence test at the merged HEAD

Date: 7 October 2026, by the orchestrator. Run 2 collected `backend/tests/test_persistence.py` before the repair d47fa70 was merged (845bc02), so its one remaining `test_persistence` failure ran the pre-repair source. This targeted run settles it at the merged HEAD 5da743d, from the main clone's `backend/` with the real `backend/.env` present (it sets `DATA_ROOT`), `AI_ENABLED=false`, `DATA_ROOT=` on the command line, short basetemp:

```
cd backend && PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= ./venv/Scripts/python.exe -m pytest tests/test_persistence.py tests/test_migrations.py tests/test_ep_archive_models.py -q -p no:cacheprovider -rs --basetemp="C:/Users/moham/AppData/Local/Temp/ep-pt3"
```

Result: **10 passed, 11 warnings in 11.15s** (log: `addendum-persistence-at-5da743d.log`). With run 2 (2 failed, 1782 passed, 35 skipped, 0 errors at f5c15f2 for all other files), the Windows suite at 5da743d has one known failure left: `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it`, the code defect of FIVE-PREEXISTING-FAILURES.md item 5, which waits on the owner's answer (was the datasheet file-name source dropped on purpose?). Limits as in run 2; this addendum is a three-file run, not a full-suite run.
