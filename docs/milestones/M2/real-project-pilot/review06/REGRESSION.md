# M2 Review 06: regression evidence

All runs were made in the isolated copy with:
- temporary databases, library, cache and uploads;
- AI disabled, except in the tests that use a scripted provider;
- no production endpoint called.

JUnit files and logs are in `evidence/suite/`.

## Environment note: one isolation artefact

The isolated copy's `.env` pins `DATABASE_URL` and the sandbox roots so that nothing can reach the live data. `tests/test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches` expects the default data-root layout, so it fails under that `.env`.

Isolated baseline worktree (Candidate C, commit `c692f1e`), running `test_persistence.py`:

| `.env` | Result |
|---|---|
| isolated `.env` present | 1 failed, 2 passed |
| isolated `.env` removed | 3 passed |

It is an artefact of the isolation, not of the candidate. It appears in the baseline and in the candidate alike.

## Runs

| Suite | Tree | Result |
|---|---|---|
| Reviewer's 28-module set (the list from `r7__suite_submitted.xml`) | candidate | **339 passed, 7 skipped, 0 failed**. Identical to Review 05. `suite/r8__suite_reviewer_set.xml` |
| New and changed modules: `test_extraction_pilot`, `test_m2_review05`, `test_m2_review05_boq`, `test_m2_pilot_eval`, `test_m2_eval4`, `test_m2_boq_eval3`, `test_evidence_reader` | candidate | **84 passed**. `suite/r8__suite_new.xml` |
| `test_m2_review06_titleblock` (8), `test_m2_review06_boq` (3), and the BOQ modules re-run after the hold rule (`test_design_sheet_extractor`, `test_m2_review05_boq`, `test_boq_verification_v2`, `test_boq_extraction_v2`) | candidate | 8 passed; 55 passed, 7 skipped |
| **Full suite** | isolated baseline (Candidate C) | 1,447 passed, 35 skipped, **3 failed**. `suite/full_baseline.log` |
| **Full suite** | candidate, before the Review 02 contract change below | 1,493 passed, 35 skipped, **4 failed**. `suite/full_candidate.log` |
| **Full suite, final** | final candidate | **1,496 passed, 35 skipped, 3 failed**: exactly the baseline's three (two pre-existing plus the isolation artefact), **no new failure**. `suite/full_candidate_final.log`, `suite/r8__suite_full_candidate_final.xml` |

## Failures, tracked separately from the M2 reader gate

| Test | Baseline | Candidate | Status |
|---|---|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` (migration downgrade, FOREIGN KEY) | fails | fails | **Pre-existing** (Review 05: pre-M1). Unchanged. |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` (stale part catalogue) | fails | fails | **Pre-existing** (Review 05). Unchanged. |
| `test_persistence.py::test_a_data_root_gathers_…` | fails | fails | **Isolation artefact** (see above). |
| `test_design_sheet_extractor.py::test_a_longer_independent_reading_sends_a_cut_digit_to_review` | passes | failed, then **updated** | **Deliberate contract change** (H-06). The Review 02 contract kept the strip's 60–90% quantity when two passes agreed on another value (the printed-48 / passes-86 case). The candidate holds such rows for review with both readings instead, because on EP-8430 the strip was the wrong reader (printed 2, strip read "\| 9"). The test's assertion was changed to the new contract, and the comment says why. This trades recovery for no false accepts, and a reviewer should confirm it. |

The Review 05 package reported the full suite as 1,448 passed, 35 skipped and 2 failed, on the live-configured tree. The third failure here is the isolation artefact.

## Test changes that alter an earlier assertion

These are listed so that a reviewer can check each one.

1. `test_extraction_pilot.py::test_parser_identity_moved_with_the_pilot_fixes`: `parse-2026-09-28.6` → `parse-2026-09-29.8`, with a comment for `.7` and `.8`. This is a version assertion only.
2. `test_design_sheet_extractor.py::test_a_longer_independent_reading_sends_a_cut_digit_to_review`: the 48/86 case, from "kept" to "held". This is the contract change above.

No other existing assertion was changed.

## Final full suite

- **Result:** 1,496 passed, 35 skipped, 3 failed, in 1,098 s. The failures are the same three as the isolated baseline.
- **Test count:** the candidate adds tests (evaluator .4, evidence reader, the review06 title-block and BOQ tests), hence 1,534 tests against the baseline's 1,485.
- **Late patch:** the last `evidence_reader` change, which passes sheet geometry to held-row batches, landed after this run had started. `tests/test_evidence_reader.py` was re-run after it: 21 passed.
