# M4 — Extraction Reliability (unified; historical Platform M2)

Status: **not accepted; CHANGES STILL REQUIRED** (roadmap section 8, M4). The accepted historical package is `docs/milestones/M2/` (frozen; never convert its line endings). This folder holds the unified-M4 records that follow it.

## Readiness survey, 7 October 2026

[evidence/S8-m4-readiness-2026-10-07.md](evidence/S8-m4-readiness-2026-10-07.md) maps the repository against the roadmap's six M4 closure items (read-only; nothing run):

| Closure item | Status term | What is missing in this repository |
|---|---|---|
| 1. Residual defects resolved or scope amendments recorded | not accepted | Defect lists are present (`M2-DEFECTS-AND-FIXES.md`, review responses); no scope-amendment record |
| 2. Fresh validation with frozen code, labels, models, bounds, denominators | implemented / partial | R32 v3 declaration and the Verification 42 harness are frozen and not authorised; no accuracy measured |
| 3. Dates/sections, BOQ evaluation, expanded sealed pilot (30 projects / 1,200 documents / 40 sheets) | missing (pilot, dates/sections); partial (BOQ metrics) | Largest staged set is 415 exploration documents; no 30-project cohort |
| 4. Label review outside the run-specific amendment | not accepted | R32 reviewed-2 labels (72 documents) are AI-reviewed only; `AI-ACCURACY-POLICY-AMENDMENT-R32-01` text not in the repository; source pages not in the repository |
| 5. Profile selection and rollback proposal | missing | No promotion or rollback proposal found |
| 6. Port accepted candidate changes; compatibility and independent acceptance | candidate only / not accepted | Candidate and baseline trees (commits a8aaced, 3d5607d) are outside the repository; `app/ai/evidence_reader.py` and `app/ai/ledger.py` absent at HEAD |

Facts confirmed at HEAD: `PARSER_VERSION = "parse-2026-10-05.5"` (document_control.py:431) and `TITLE_BLOCK_VERSION = "titleblock-2"` (title_block.py:34); the accepted package ends at `parse-2026-09-28.6` and `titleblock-1`, so none of its evidence covers the current parser versions. All 15 extraction files match the roadmap's snapshot hashes. "CHANGES STILL REQUIRED" is recorded at `M2-REVIEW-RESPONSE.md:1513`. The order-dependent test the package names was fixed by a file-backed test database in `conftest.py`, present at HEAD; not re-run here.

## Defect delta and test health, 7 October 2026

[evidence/S9-defect-delta-2026-10-07.md](evidence/S9-defect-delta-2026-10-07.md) classifies the accepted package's 64 defect ids against the code (static reading plus the test run; synthetic fixtures only, no client originals): SUPERSEDED BY VERIFIED BEHAVIOR 47, FIXED 1 (D-METRIC-1, a script with no test), STILL OPEN 9 (G-M2-1, G-M2-1b, G-M2-2, G-M2-3, G-M2-6, P-obs-2, H-01, H-02, H-03), NOT REPRODUCED 6 (G-M2-4, G-M2-5, B-04, H-04, H-05, H-06; need originals, stored data or a model run), n/a 1. The six residuals that keep the verdict at CHANGES STILL REQUIRED (`M2-REVIEW-RESPONSE.md:1514`) are B-1 recovery under 90%, B-2 identity precision under 98% with flagged references keyed as register identities, B-3 labels AI-reviewed not human-signed, B-4 project AI eligibility, B-5 no variant choice and an unauthorised fresh-validation declaration, B-6 BOQ misreads; none is closed by code at HEAD (B-6 has partial code answers). The package's later candidates (`parse-2026-09-29.x`, `titleblock-3`, `evidence_reader`) are not in the tree; the five `parse-2026-10-05.x` changes answer no listed defect. G-01 (`sync_register` overwrites an engineer-set submittal status, `submittal_reader.py:750`) is still present.

Test health ([evidence/tests-2026-10-07/](evidence/tests-2026-10-07/TEST-RESULTS.md), [evidence/diagnosis-2026-10-07/](evidence/diagnosis-2026-10-07/OCR-TEST-FAILURES.md)): 18 extraction suites at c2f2671 gave 214 passed, 13 skipped, 3 failed. All three failures were test defects and are repaired on the branch: a hand-built provider fixture missing the later `_max_turns` attribute (commit 32d8d55) and two OCR tests that faked the OCR call without stubbing `ocr_available` (commit 58c838a; precedent `test_extraction_m2_review02.py:61`). The test the package recorded as order-dependent passed in three isolated runs. A fourth, platform-dependent failure was found by the S9 survey: `test_m2_review05_boq.py::test_a_reread_never_offers_an_unread_sheets_lines_for_removal` expects a file name and receives a Windows path literal on Linux; not yet diagnosed as test or code.

Code question raised by the OCR diagnosis (M4 closure item 1, roadmap section 6 "Unknown is never complete"): on the main processing path, when Tesseract is absent, a changed file whose new content is a scan is stored as an empty "complete" reading with no note or coverage marker; the only "OCR unavailable" warning is in the older whole-folder scan (`document_control.py:2248`). Assigned to the implementer as the first M4 code change (see the task record below when it lands).

## Inputs M4 needs from the owner before it can advance

1. The 17-gate acceptance matrix and closure decision from the G: drive (`m2-closure/M2-ACCEPTANCE-MATRIX.md`, `M2-CLOSURE-DECISION-2026-10-06.md`), added to this repository or made readable.
2. The candidate and baseline trees (a8aaced, 3d5607d) or the candidate files themselves, for the controlled port (item 6).
3. The source documents and labelled pages of the R32 cohort, and a human label reviewer, for items 2 and 4; a model budget authorisation for any fresh run.
4. The policy amendment text `AI-ACCURACY-POLICY-AMENDMENT-R32-01`.

Work that can proceed here without those inputs: re-running the extraction test suites on the current tree as evidence; a defect-by-defect delta of `M2-DEFECTS-AND-FIXES.md` against HEAD (fixed / still open), in the M2-refresh style; and a compatibility map of the current parser versions against the accepted package's. None of it closes a gate.
