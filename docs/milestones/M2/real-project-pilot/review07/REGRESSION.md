# M2 Review 07: regression evidence

## Hermetic full suite on the frozen candidate

- **Tree:** the worktree `C:/t/iso/frozen-r7` at commit `c9a1a14`. It has **no `.env`**: the test configuration (`tests/conftest.py`) points the database, library, cache and uploads at temporary folders and turns AI off, so nothing depends on the developer's or the sandbox's configuration.
- **Command:** `python -m pytest tests` from `frozen-r7/backend`, with a temporary base directory. JUnit: `evidence/suite/r9__suite_full_frozen_hermetic.xml`; log: `full_frozen_hermetic.log`.
- **Result: 1,600 tests, 1,563 passed, 35 skipped, 2 failed.**

| Failure | Status |
|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` (migration downgrade, FOREIGN KEY) | **Pre-existing** (Review 05: pre-M1), unchanged |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` (stale part catalogue) | **Pre-existing**, unchanged |

The Review 06 isolation artefact (`test_persistence.py::test_a_data_root_gathers_…`, which failed only because the isolated `.env` pinned `DATABASE_URL`) **passes** in the hermetic run.

**Unlike Review 06's full run, this run tested the final application bytes.** The one later change is the evaluator amendment (`1455f8b`, scripts and tests only). Its `tests/test_m2_eval5.py` gives **13 passed** at `1455f8b`.

## New and changed test modules (Review 07)

| Module | Tests | Result |
|---|---|---|
| `tests/test_m2_eval5.py` | 13 | pass (at `1455f8b`) |
| `tests/test_evidence_reader_r7.py` | 36 | pass |
| `tests/test_evidence_reader.py` (three assertions moved to policy `.2`, listed below) | 21 | pass |
| `tests/test_ai_ledger.py` | 9 | pass |
| `tests/test_m2_review07_extraction.py` | 6 | pass |
| `tests/test_m2_review07_boq.py` | 3 | pass |
| BOQ modules re-run after the description-count change (`test_design_sheet_extractor`, `test_m2_review06_boq`, `test_m2_review05_boq`, `test_boq_*_v2`) | 76 passed, 7 skipped | pass |
| AI modules (`test_ai_assist`, `test_ai_sheet_reader` with the ledger, evidence reader, evaluator) | 116 | pass |

## Assertions changed from an earlier version

These are listed for the reviewer.

1. `test_extraction_pilot.py::test_parser_identity_moved_with_the_pilot_fixes`: `parse-2026-09-29.8` → `parse-2026-09-29.9`. A version assertion only.
2. `test_evidence_reader.py::test_model_agreement_without_source_support_is_only_a_candidate`: a one-character OCR near match is now a **candidate** (was validated). This is policy `.2`, R7-02.
3. `test_evidence_reader.py::test_decision_policy`: validation now needs a target component; the contractor case is corroborated and is still a candidate. Policy `.2`.
4. `test_evidence_reader.py::test_stage_is_off_by_default_and_writes_only_its_own_key`: reads the lifecycle envelope (`current_evidence`) and the attempt log. R7-03.
5. `test_evidence_reader.py::test_boq_row_policy`: `FC-501` against `FC501` is now a **conflict**, because parts compare literally. Policy `.2`.

No application behaviour test outside the reader, evaluator and ledger changed its assertion.
