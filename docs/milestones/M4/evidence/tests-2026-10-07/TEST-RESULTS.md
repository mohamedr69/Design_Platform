# M4 evidence: extraction-related test suites

Date: 7 October 2026. Branch claude/upbeat-lovelace-sa9j3w. HEAD c2f26719c108f5099b17dc0434bb705e7bc0b876 (backend/ and frontend/ identical to 771001e, as stated by the orchestrator; not re-verified here).

Git status --short before: `?? docs/milestones/M4/evidence/tests-2026-10-07/` (only the evidence directory just created). After: identical. No source file was edited, skipped or patched.

Result: **3 failed, 214 passed, 13 skipped, 0 errors, 67 warnings in 98.43 s** (230 tests, 18 files).

## Environment

Linux 6.18.44-fc-v77; Python 3.13.16; node v22.22.0 (not used); Tesseract not on PATH; no live archive (EP_PLATFORM_LIVE_ARCHIVE_ROOT unset); no AutoCAD; AI_ENABLED=false, DATA_ROOT empty. Packages: pytest 8.3.4, fastapi 0.115.6, starlette 0.41.3, SQLAlchemy 2.0.36, pydantic 2.10.4, httpx 0.28.1, pillow 12.3.0, pymupdf 1.28.2.

## Per-file results

Counts from the JUnit XML. The accepted package (M2-ACCEPTANCE-REPORT.md, Correction 1) recorded only whole-suite totals (317 tests, 309 passed, 7 skipped, 1 failed), so there are no per-file figures to compare. The comparison column uses what the package states.

| File | Tests | Passed | Failed | Skipped | Comparison with accepted package |
|---|---:|---:|---:|---:|---|
| test_extraction_m2 | 12 | 12 | 0 | 0 | no per-file figure |
| test_extraction_m2_review | 21 | 20 | 1 | 0 | package: 21 new tests, whole suite had no failure here; this run differs (1 failed) |
| test_extraction_m2_review02 | 16 | 16 | 0 | 0 | no per-file figure |
| test_extraction_m2_review03 | 7 | 7 | 0 | 0 | no per-file figure |
| test_ai_sheet_reader | 7 | 7 | 0 | 0 | package: its one failure was in this file; here 7/7 pass |
| test_ai_verification | 16 | 16 | 0 | 0 | no per-file figure |
| test_ai_evaluation | 20 | 20 | 0 | 0 | no per-file figure |
| test_boq_extraction_v2 | 13 | 11 | 2 | 0 | package: no failure recorded in this file; here 2 failed |
| test_boq_verification_v2 | 4 | 4 | 0 | 0 | no per-file figure |
| test_boq_selective_v2 | 7 | 7 | 0 | 0 | no per-file figure |
| test_boq_geometry_v2 | 10 | 10 | 0 | 0 | no per-file figure |
| test_boq_corrections_v2 | 1 | 1 | 0 | 0 | no per-file figure |
| test_design_sheet_extractor | 31 | 23 | 0 | 8 | package: skips were live-archive BOQ sheets (7 skips total); here 7 live-archive + 1 Tesseract |
| test_drf_extractor | 11 | 6 | 0 | 5 | here 3 live-archive + 2 Tesseract |
| test_document_control | 25 | 25 | 0 | 0 | no per-file figure |
| test_extraction_pilot | 5 | 5 | 0 | 0 | no per-file figure |
| test_extraction_repair | 12 | 12 | 0 | 0 | no per-file figure |
| test_classification_evidence | 12 | 12 | 0 | 0 | no per-file figure |
| Total | 230 | 214 | 3 | 13 | package whole suite: 317 / 309 / 1 failed / 7 skipped |

Skips (13, all environment facts): 10 "Set EP_PLATFORM_LIVE_ARCHIVE_ROOT to run against the real archive" (test_design_sheet_extractor.py lines 98, 131, 157, 183, 205, 262, 290; test_drf_extractor.py lines 200, 231, 268) and 3 "tesseract is not installed/configured in this environment" (test_design_sheet_extractor.py:341; test_drf_extractor.py:164, 183). The package noted 7 skips; this run has 6 more, 3 of them Tesseract-dependent and 3 additional live-archive skips in test_drf_extractor.py.

## Failures (from extraction-suites.log)

1. tests/test_extraction_m2_review.py::test_an_ocr_failure_on_a_changed_scan_keeps_the_previous_complete_reading_as_a_partial_attempt

        >       assert result["changed"] == 1 and processed.get("partial", 0) == 1 and processed.get("failed", 0) == 0
        E       AssertionError: assert (1 == 1 and 0 == 1)
        E        +  where 0 = <built-in method get of dict object at 0x7f04bc6cb880>('partial', 0)
        tests/test_extraction_m2_review.py:121: AssertionError

   The test monkeypatches dc._ocr_text to raise; it was not diagnosed whether the absence of Tesseract changes the path taken. Recorded as a failure, not classified as an environment gap.

2. tests/test_boq_extraction_v2.py::test_a_temporary_folder_that_cannot_be_removed_does_not_fail_the_call

        app/ai/provider.py:805: if self._max_turns:
        E           AttributeError: 'ClaudeCodeProvider' object has no attribute '_max_turns'
        (tests/test_boq_extraction_v2.py:350 into app/ai/provider.py:805)

3. tests/test_boq_extraction_v2.py::test_a_cli_timeout_is_a_timeout_not_an_answer

        app/ai/provider.py:805: if self._max_turns:
        E           AttributeError: 'ClaudeCodeProvider' object has no attribute '_max_turns'
        (tests/test_boq_extraction_v2.py:374 into app/ai/provider.py:805)

   For 2 and 3: provider.py:659 sets `self._max_turns = settings.ai_cli_max_turns` in `__init__`; the tests reach line 805 with an object lacking the attribute (the tests appear to build the provider without running `__init__`; not investigated further). Full tracebacks are in the log.

## test_ai_sheet_reader.py alone, three runs

Each run used a separate --basetemp (pytest-temp-r1..r3); output in ai_sheet_reader-run1.txt .. run3.txt.

| Run | Result | test_the_first_read_runs_as_a_job_the_page_follows |
|---|---|---|
| 1 | 7 passed, 7 warnings in 9.26 s | PASSED |
| 2 | 7 passed, 7 warnings in 9.00 s | PASSED |
| 3 | 7 passed, 7 warnings in 8.99 s | PASSED |

It also passed in the combined run (7/7 in the file).

## Commands

Working directory /home/user/Design_Platform/backend, scratch S=/tmp/claude-0/-home-user-Design-Platform/32737463-7564-5f1d-b606-2274610299d6/scratchpad/m4/tests, evidence E=docs/milestones/M4/evidence/tests-2026-10-07.

    PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= python3 -m pytest tests/test_extraction_m2.py tests/test_extraction_m2_review.py tests/test_extraction_m2_review02.py tests/test_extraction_m2_review03.py tests/test_ai_sheet_reader.py tests/test_ai_verification.py tests/test_ai_evaluation.py tests/test_boq_extraction_v2.py tests/test_boq_verification_v2.py tests/test_boq_selective_v2.py tests/test_boq_geometry_v2.py tests/test_boq_corrections_v2.py tests/test_design_sheet_extractor.py tests/test_drf_extractor.py tests/test_document_control.py tests/test_extraction_pilot.py tests/test_extraction_repair.py tests/test_classification_evidence.py -q -rA -p no:cacheprovider --basetemp=$S/pytest-temp --junitxml=$E/extraction-suites.xml 2>&1 | tee $E/extraction-suites.log

    PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= python3 -m pytest tests/test_ai_sheet_reader.py -q -rA -p no:cacheprovider --basetemp=$S/pytest-temp-r<n> > $E/ai_sheet_reader-run<n>.txt 2>&1     (n = 1, 2, 3)

## Files

extraction-suites.xml, extraction-suites.log, ai_sheet_reader-run1.txt, run2.txt, run3.txt, this file. Note: `*.log` is gitignored (.gitignore:17), so extraction-suites.log is untracked-ignored and must be force-added by the orchestrator. Nothing was force-added here.

## Limits

This is a subset (18 files, 230 tests) of the suite, not the full suite, so the package's 317-test totals are not comparable. It does not establish real-model accuracy (AI_ENABLED=false, scripted providers), live-archive BOQ sheet behaviour (10 tests skipped), OCR behaviour (no Tesseract, 3 tests skipped, one failure possibly related and not diagnosed), AutoCAD, PostgreSQL, production data, the frontend build, or milestone acceptance. Three runs of one test show no order or timing failure in this container; they do not prove its absence elsewhere.
