# Session handover — 7 October 2026

Written by the orchestrating session so the next session can continue without re-planning. Branch: `claude/upbeat-lovelace-sa9j3w` (default branch `merge/candidate`; pull request #1 was merged by the owner at 852c91c). Governing document: [docs/UNIFIED_MASTER_ROADMAP.md](UNIFIED_MASTER_ROADMAP.md), Revision U7.

## State of the milestones

| Milestone | State | Record |
|---|---|---|
| M1 | Refreshed, ACCEPT WITH NOTES (two verifier passes) | docs/milestones/M1/refresh-2026-10-06/ |
| M2 | Refreshed, ACCEPT WITH NOTES (two verifier passes) | docs/milestones/redesign/RD-M1-refresh-2026-10-06/ |
| M3 | OPEN on owner decisions: 5 received (OD-20..OD-24, memory history, conflicts, promotion, provenance), OD-02 partly decided, 17 open | docs/milestones/M3/M3-DECISION-PACK.md, M3-POLICY-CONTRACT-DRAFT.md |
| M4 | Not accepted; readiness survey, defect delta and test health recorded; six residuals need inputs from the owner's machine | docs/milestones/M4/README.md |
| M5+ | Not started. Note: owner commit bb5871d (on merge/candidate) changed `_drawn` in backend/app/redesign/service.py to approved-only, which is RD-M1 decision A / OD-14 option (a) implemented in code; the roadmap and the M2 record still describe the pre-bb5871d behavior at 771001e and need a Revision U8 note and OD-14 marked decided-by-code once the owner confirms. | — |

## Work in flight when the session changed

1. **Stale test assertion after bb5871d — DONE.** `backend/tests/test_redesign.py` now pins the approved-only drawn rule (commit on this branch, "Pin the approved-only drawn rule in the interface-module test"); test_redesign.py and test_drawing_prep.py give 30 passed. This fix and the forward-slash fixture fix are the two commits beyond the merged pull request; they need a new pull request into `merge/candidate`.
2. **OCR unavailable must not read complete (M4 closure item 1).** Implemented in commit 4310fc8, pushed as backup branch `claude/wip-m4-ocr-unavailable` (base de0ea1b; touches backend/app/services/document_control.py, document_sync.py and tests/test_extraction_m2_review.py). An ep-verifier was reviewing it when the session changed; not yet merged. Next: run ep-verifier on it per the gate in docs/milestones/M4/README.md ("Code question raised by the OCR diagnosis"), then cherry-pick onto the branch. The implementer narrowed the condition to pages where nothing was read (text pages with unread image stamps stay unflagged) and lists that residual as an owner decision.
3. **Diagnosis of five pre-existing failures — DONE**, filed at docs/milestones/M4/evidence/diagnosis-2026-10-07/FIVE-PREEXISTING-FAILURES.md: migrations schema test is a knock-on of the archive-model test (no migration drift on SQLite); archive-model test runs a downgrade with foreign keys on (test fix proposed); AI-assist test needs `@requires_tesseract`; open-folder test patches the global `os.name` (portable fix or Windows-only list, owner's choice); part-catalogue test exposes a CODE DEFECT present since the first commit (`part_catalog.catalog` never reads datasheet file names) plus a stale expectation — fix must not scan the library inside GET. Next session: implement the test fixes (2, 3, 4A if chosen) through ep-implementer; the part-catalogue fix is an M4/M10 code task needing the owner's answer.

## Owner decisions recorded this session
- Windows-first test suite: the Windows-only tests stay failing on Linux and are listed as expected in every Linux run (docs/milestones/M4/README.md; .claude/agents/ep-test-runner.md).
- OD-20..OD-24 on memory (roadmap U7, section 6).

## Still needed from the owner
- Three questions from the five-failure diagnosis: test 4 portable fix or Windows-only; whether the part catalogue dropped the datasheet file-name source on purpose; whether SQLite migrations should be made atomic for M7 or the pre-migration backup is the accepted safeguard.
- M3: the remaining decisions in docs/milestones/M3/M3-DECISION-PACK.md (answer sheet §2), especially OD-19 project access, OD-02 promoter and retirement, OD-18 critical confirmer, OD-01 approved-as-noted, OD-04 AI policy scope, OD-05..OD-09 workload roles, OD-10/11 archive and deletion, OD-12/13 rulings and symbol library, OD-14..OD-17 Apply (OD-14 appears implemented by bb5871d; confirm).
- M4: the G: drive 17-gate matrix and closure decision; candidate/baseline extraction trees (a8aaced, 3d5607d); R32 source documents and labels, a human label reviewer, a model budget; the amendment text AI-ACCURACY-POLICY-AMENDMENT-R32-01.

## Process notes
- Agent roster in .claude/agents/ with the write guard; one implementer at a time; every implementer change is verified by ep-verifier before merge; records use the roadmap's status terms.
- Evidence conventions: milestone folders hold records; evidence/ subfolders hold raw surveys, test outputs (force-add *.log) and verification reports.
- The session's PR #1 subscription and its safety-net check-in were ended after the merge.
