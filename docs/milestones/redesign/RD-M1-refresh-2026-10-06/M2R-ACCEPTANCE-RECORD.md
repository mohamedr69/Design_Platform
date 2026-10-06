# M2 refresh — acceptance record

Milestone: **M2 — Baseline & Error Inventory** (unified; historical RD-M1), refreshed for the current code.
Date: 6 October 2026. Snapshot surveyed: branch `claude/upbeat-lovelace-sa9j3w`; `backend/` and `frontend/` identical from commit **771001e** through the commits that added this folder (verified by `git diff --stat` in the source-hash file). Documentation, read-only inspection and one test run; no application code, test, migration, configuration, prompt or frozen evidence file was changed; no model, AutoCAD, database or Golden drawing was used. The accepted RD-M1 package under `docs/milestones/redesign/RD-M1/` is unchanged and verifies against its manifest (73 files exact, 5 after line-ending restoration, 0 mismatches; [evidence/M2R-SOURCE-HASHES.json](evidence/M2R-SOURCE-HASHES.json)).

Task statement (roadmap section 14):

| Element | Value |
|---|---|
| Milestone | M2 refresh |
| Bounded scope | Retain the 35-finding RD-M1 inventory and frozen Golden evidence; classify every finding against the current code as fixed, still open, superseded by verified behavior or not reproduced; add a delta baseline for the preparation, coverage, agents, markup and scoped-review code added since RD-M1; map tests to pipeline stages; state what of Golden Case GC-01 is reproducible here. |
| Snapshot changed | None in code. Records added under this folder. |
| Completion gate | Roadmap M2 exit: a reviewer can trace current findings to source/input/output hashes and reproduce bounded cases; historical findings are not treated as fixed by new UI or AI code. |
| Evidence destination | This folder. |

## 1. Requirement → current implementation → remaining gap → action → evidence

| Requirement (roadmap M2) | Delivered | Remaining gap | Action / owner | Evidence |
|---|---|---|---|---|
| Retain the 35-finding inventory | The 24 original columns are copied cell-equal from RD-M1's CSV; 6 refresh columns appended | — | — | [M2R-FINDINGS-DELTA.csv](M2R-FINDINGS-DELTA.csv) |
| Delta inventory: fixed / still open / superseded / not reproduced | 35 classified: FIXED 0, STILL OPEN 32, SUPERSEDED BY VERIFIED BEHAVIOR 1 (F027, detector coverage only, resting on the unchanged wall index), NOT REPRODUCED 2 (F026, F028). Both Critical (F002, F003) and all nine High findings are still open. Primary owner: M5 14, M8 14, M12 3, M7 2, M10 1, M18 1 | F026 and F028 need the GC-01 drawing and the RD-M1 database snapshot (owner's PC-B) | Owner reproduces on PC-B per RD-M1's runbook if the classification matters before M5/M8 | [M2R-FINDINGS-DELTA.md](M2R-FINDINGS-DELTA.md) §3–§5 |
| Delta for preparation / coverage / agents / interfaces code | File delta: 9 changed, 20 new, 1 removed, 14 same, 7 line-ending-only against RD-M1's manifest; stage delta: 14 of 25 stages unchanged, 11 changed, 18 new; 22 UNREVIEWED code-confirmed candidate findings RD-M1R-C01..C22 (Critical 1, High 8, Medium 10, Low 3) in RD-M1's schema | Candidates are code-level only; no Golden evidence exists for preparation, coverage or the gate, so no instance-level or visual finding is possible here | New Golden cases for preparation at M8/M12 (roadmap M8: "Validate a simple sheet and a rotated view") | [M2R-NEW-SURFACE-INVENTORY.csv](M2R-NEW-SURFACE-INVENTORY.csv), [.md](M2R-NEW-SURFACE-INVENTORY.md) |
| RD-M2 candidate corrections versus the active tree | None present: `service.py` hash differs, `verify.py` and `test_redesign_apply.py` absent, `cad.py` and `test_redesign.py` byte-identical to the RD-M1 base; the candidate patch no longer applies | — | M5 ports the correction onto current preparation logic in isolation (roadmap M5) | [M2R-FINDINGS-DELTA.md](M2R-FINDINGS-DELTA.md) RD-M2 table; [evidence/M2R-SOURCE-HASHES.json](evidence/M2R-SOURCE-HASHES.json) `absent_at_surveyed_commit` |
| Traceability to hashes | 83 repository files hashed at 771001e; RD-M1 package re-verified against its manifest; GC-01 input hashes pinned by RD-M1 evidence files named per missing input | GC-01 source DWG/DXF, DB snapshot, plots and AutoCAD log are not in this repository | — | [M2R-GOLDEN-STATUS.md](M2R-GOLDEN-STATUS.md) |
| Bounded reproducible cases | The seven redesign, review and interface suites: 116 passed, 0 failed, 0 skipped; RD-M1 ran 78 over four of them, the same four now give 81 (+3 in test_fa_interfaces), test_redesign's 16 ids unchanged | 12 of 43 stages have no test, 5 partial; no test reaches `apply()` | M5 adds the Apply tests (RD-M2's `test_redesign_apply.py` as the starting point) | [evidence/TEST-RESULTS.md](evidence/TEST-RESULTS.md), [M2R-TEST-COVERAGE-MAP.md](M2R-TEST-COVERAGE-MAP.md) |
| Historical findings not treated as fixed by new code | Classification rule written in the delta §1.1; FIXED requires the defect gone from the code, SUPERSEDED requires a named test that exercises the corrected code | — | — | [M2R-FINDINGS-DELTA.md](M2R-FINDINGS-DELTA.md) §1.1 |

## 2. Exit gate assessment (orchestrator's reading; the verifier's verdict is in section 6)

The gate asks that a reviewer can trace current findings to hashes and reproduce bounded cases. Every one of the 35 findings and 22 candidates carries a current file:line, the files are hashed at the surveyed commit, and the bounded cases are the 116 tests whose log and JUnit output are in evidence. What cannot be reproduced here is Golden Case GC-01 itself, whose inputs live on the owner's machine; the Golden-status record names, for each missing input, the RD-M1 evidence file that pins its hash and the runbook step that reproduces it. The orchestrator reads the gate as met for the repository-reproducible part and explicitly not claimed for GC-01 instance findings.

## 3. Decisions taken by the orchestrator (not owner decisions)

- (a) Coordination findings F008–F012 are owned by **M8**, whose scope names doors, obstacles, containment, spacing and post-change clash checks; **M12** owns only the rendered visual check. RD-M1's CSV said "RD-M4 coordination", which the appendix maps to M12; the record states both.
- (b) Historical milestone names map to unified numbers as: RD-M2 → M5, RD-M3 → M8, RD-M4 → M12, RD-M5 → M13, "AI-validation milestone" → M12, "RD-M6 workflow" → M7 / M10 / M18 by the nature of each finding. "RD-M6" has no appendix row; it was a proposal in RD-M1's handoff, not a planned milestone.

## 4. Snapshot, tests and method

| Item | Value |
|---|---|
| Surveyed commit | 771001e for code; the surveys ran on 4bab8d2 and f828ca1 and the test run on 4bab8d2, all with `backend/` and `frontend/` identical to 771001e |
| Tests | 116 passed / 0 failed / 0 skipped in 156 s; Python 3.13.16, pytest 8.3.4, ezdxf 1.4.4, pymupdf 1.28.2, SQLAlchemy 2.0.36, FastAPI 0.115.6; no Tesseract or AutoCAD path exercised |
| Method | Two read-only surveyors (S6 findings delta, S7 new surface) and one test runner wrote to the scratchpad and the evidence folder; two scribes assembled the records without re-reading code; the orchestrator wrote this record and the hash file. Roles were emulated with the built-in general-purpose agent (the project roster was not loaded in this session); the tree was checked clean after every agent |
| Counting units | "finding" = one RD-M1 row; "candidate" = one code-confirmed defect class in the added code; "stage" = one row of RD-M1's pipeline map or one new stage; "test" = one pytest function |

Known inconsistencies kept visible rather than reconciled: S6's header says test_drawing_prep.py has 25 test functions, the file defines 14 (S7 and the test run agree on 14; the records use 14). S6 cites two tests outside the 116-test run (`test_fa_evidence.py::test_C4_kept_interface_changes_are_restored_byte_for_byte`, `test_sync_worker.py::test_a_job_left_running_by_a_dead_worker_is_recovered`); the CSV marks them as not in the run. S7's cross-check lists F015, F020 and F025 as "not re-read" where S6 classifies them STILL OPEN; S7 defers to S6. S7 gives no confidence rating, so the candidates' `confidence` column says so.

## 5. Independent review disposition

**Verdict:** pending — ep-verifier (Opus, read-only) reviews this package against the gate; the verdict is appended below when received.

## 6. Owner decisions still required (not taken here)

RD-M1's handoff decisions A–D remain open and now belong to M3/M5: A, whether review-sourced changes require explicit approval before they are drawn (today `proposed` review changes with verdict ok, check or none are drawn; roadmap M5 already states approved-only as the target); B, whether Apply may keep writing to the project archive; C, whether an AutoCAD run on an isolated copy is authorised; D, what to do with the stored changes carrying PC-A library paths.

## 7. Integration status, retention, rollback, limitations

- Integration: records only; reverting the commits that added this folder restores the previous state.
- Retention: the accepted RD-M1 and RD-M2 packages are untouched and RD-M1 re-verifies against its manifest.
- Limitations: static reading plus one test run; candidates and classifications are unreviewed by an engineer; severity of candidates is a proposal; no AutoCAD, model or Golden-drawing behavior was observed; the three scribes did not re-verify code. These records establish the refreshed baseline; they do not establish any behavior as correct or any later milestone as started.
