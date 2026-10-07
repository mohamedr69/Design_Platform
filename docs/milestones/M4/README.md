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

## Inputs M4 needs from the owner before it can advance

1. The 17-gate acceptance matrix and closure decision from the G: drive (`m2-closure/M2-ACCEPTANCE-MATRIX.md`, `M2-CLOSURE-DECISION-2026-10-06.md`), added to this repository or made readable.
2. The candidate and baseline trees (a8aaced, 3d5607d) or the candidate files themselves, for the controlled port (item 6).
3. The source documents and labelled pages of the R32 cohort, and a human label reviewer, for items 2 and 4; a model budget authorisation for any fresh run.
4. The policy amendment text `AI-ACCURACY-POLICY-AMENDMENT-R32-01`.

Work that can proceed here without those inputs: re-running the extraction test suites on the current tree as evidence; a defect-by-defect delta of `M2-DEFECTS-AND-FIXES.md` against HEAD (fixed / still open), in the M2-refresh style; and a compatibility map of the current parser versions against the accepted package's. None of it closes a gate.
