# M5 Safe Apply & AutoCAD Block Library: delivery and acceptance record

Prepared 8 October 2026 by ep-scribe, per `docs/UNIFIED_MASTER_ROADMAP.md` section 13. Branch `roadmap/u2`.

**Status:** M5: implemented / partial; independently verified PASS WITH CONDITIONS; not accepted (real-AutoCAD evidence and conditions C1–C3 outstanding).

This record states only what its inputs contain. It grants no acceptance, no live-validation authorisation beyond OD-16 (c), and no deployment. Historical names (RD-M2, RDM2-R1) appear only in paths and quoted evidence.

## 1. Inputs (sha256)

| File | sha256 |
|---|---|
| `docs/UNIFIED_MASTER_ROADMAP.md` section 8 M5 and section 13 | read at HEAD (no hash taken) |
| `docs/milestones/M3/M3-DECISION-PACK.md` (rows OD-14..OD-17, answer sheet) | read at HEAD (no hash taken) |
| `docs/milestones/M5/M5-SAFE-APPLY-IMPLEMENTATION.md` | `7465ccefa93dfb14a5d8b163da99ce0e2e39c9f66e90a282bd603f7ec868e268` (equals the manifest's `report.sha256`) |
| `docs/milestones/M5/evidence/safe-apply/MANIFEST.json` | `9ba30ef3cab6c2a9fb7140959843864a930e3149b86479a0d9a848c33c0c0efb` |
| `.../reviews/U2-M5-disposition/DISPOSITION.md` (ORCH-035) | `bf62446195483f434cb03a24b32eb6b2d602716cd9f720275fbd0b4a0e5a6601` |
| `.../reviews/U2-M5-disposition/FINDINGS.json` | `85594c7484a8f0a1d50fc87080fbcfd2bce0c8571a035e19f34a62e415f82622` |
| `.../reviews/U2-M5-verify/INDEPENDENT-VERIFICATION.md` (ORCH-040) | `3742125290f0e968dc8cfcaa081077d7514b6a23d05ff509261e1d5a436b2268` |
| `.../reviews/U2-M5-verify/FINDINGS.json` | `d7c6c0807c10d4eb36747cbcf62bff7ed959929fca83707e268595926596cd80` |

Review folder prefix: `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/`.

## 2. Owner decisions that bind M5 (M3 decision pack, filed 7 October 2026)

| Row | Decision | Effect on M5 |
|---|---|---|
| OD-14 | (a) approved-only drawing, confirmed as implemented by owner commit bb5871d | Drawn set is approved changes only; tests pinning the old rule were re-pinned (e4fa306). |
| OD-15 | (a) Apply writes only the platform copy; archive publication is a separate explicit engineer action with a unique non-overwriting filename | Implemented as `publish()` / `POST .../publish`; Apply no longer writes the archive. |
| OD-16 | (c) authorised with limits: one named machine, an isolated copy of GC-01, a dedicated AutoCAD profile, source hash verified unchanged afterwards, output retained as evidence only | The run has NOT happened. The machine name is to be recorded in the M5 evidence when the run is scheduled. |
| OD-17 | (b) the six stored changes stay unchanged as history; library paths resolved at script time from the active library; no migration | Implemented in `to_cad` / `module_library`. |

## 3. Requirement, implementation, gap, action, evidence

Requirements are the section 8 M5 list. All evidence cited is functional/mocked or SQLite; none is real-AutoCAD. Sources: implementation report (ORCH-039) and independent verification (ORCH-040).

| Requirement | Current implementation (c274205) | Remaining gap | Action | Acceptance evidence |
|---|---|---|---|---|
| Only approved changes with current source/approval snapshots eligible; uncertain placement needs engineer confirmation | `requires_confirmation`, `_drawn`, `_snapshot`, `apply_request`, `_refusal`, `ApplyStale` | U2M5V-01 (Low): fingerprint is checked before Apply's own "making" write; an edit in that window is drawn instead of refused | ORCH-041 (issued, not run) or owner acceptance (C2) | Targeted tests pass (93); verifier mutation V3 caught by 11 tests |
| Resolve CT1/CT2/CR against the current library | `to_cad`, `module_library` resolve at script time (OD-17 b) | Real `-INSERT` with spaces and parentheses unproven | OD-16 (c) run, item 5 | Mocked: `test_library_paths_with_spaces_are_resolved_at_script_time_from_the_active_library`, `test_a_stored_office_pc_path_never_reaches_the_script` pass |
| Fail on incomplete scripts; standalone completion markers; saved-output validation; insert/erase read-back | `cad.py`, `verify.py` (byte-equal to candidate v2.1), `_readback`, `_source_readback` | Stand-in AutoCAD and stand-in read-back only | OD-16 (c) run, items 1–4 | Mocked: parametrised `test_an_unchanged_unreadable_or_incomplete_output_is_refused` (5 cases) and marker tests pass |
| Hold conflicting/failed preparation; gates at the server boundary | `start_apply` returns 422 when `readiness()` is not ready or nothing is drawn; `readiness()` is also the first refusal inside the job | None recorded beyond the mocked level | none | Mocked: 422 tests pass; verifier mutation V5 caught by 3 tests |
| Unique exclusive outputs, cancellation, retry/idempotency, atomic publication, cleanup on commit failure | `_unique_output`, `_stage` (O_EXCL), `_finalize` (link or Windows rename), publication under `BEGIN IMMEDIATE`, commit-failure cleanup, `sweep_orphans` | U2M5V-02 (Low): publish `.part` in the archive folder is never swept; U2M5V-03 (Low): a stop between "made" and "succeeded" leaves a valid copy that cannot be published; real kill on cancel/timeout and hard links on target and archive volumes unproven | ORCH-041 or owner acceptance (C2); OD-16 (c) run items 6 and 8 | SQLite: concurrency tests (a) and (b) pass; mutations M1 and M2 caught |
| Preserve source drawings; archive publication a separate controlled action | Apply writes only under `uploads/EP-n/redesign`; `publish()` needs an editor role, only a verified copy from a succeeded Apply job, 409 if the name exists, records `redesign.published` | U2M5V-04 (Low): legacy rows show the old implicit filing as "published separately"; source sha256 unchanged after a real run unproven | ORCH-041 or owner acceptance (C2); OD-16 (c) run item 7 | Mocked: `test_apply_never_writes_into_the_project_archive`, publish tests pass; verifier mutation V4 caught by 3 tests, V6 by 1 |
| Exit: approved inserts/erases reconcile exactly; missing blocks, script errors, stale approvals and commit failure publish nothing | Covered at the mocked level only | The real-AutoCAD reconciliation is the missing exit evidence | OD-16 (c) run (C1) | Not established |
| Exit: reproduce the concurrent publication test | `test_concurrent_publication_an_edit_started_inside_the_window_waits...` and `..._an_edit_committed_before_the_lock_makes_the_apply_stale...` | Non-SQLite lock path untested (U2M5-08; C3) | Cover before any move away from SQLite | Reproduced by ORCH-040 on a byte copy |

## 4. Exact code and artifact snapshot

- Base: `roadmap/u2` at `f15ac011e14612477a805625d14446430ed75d30` (code equal to 668f92f).
- Branch `task/m5-safe-apply`: implementation commit `c274205128b3e75e73c8c9ff11440f926d5a8f29`; evidence and report commit `f859aea` (touches only `docs/milestones/M5/`).
- The candidate was rebuilt by both the implementer and the verifier from `b5c2222` plus `rdm2-candidate.patch` plus `RDM2-R1-correction.patch`; the v2.1 hashes reproduced.
- Interpreter (manifest): Python 3.12.10, SQLite 3.49.1, SQLAlchemy 2.0.36, pytest 8.3.4.
- Changed-file sha256 at c274205 (manifest):

| File | sha256 |
|---|---|
| `backend/app/redesign/service.py` | `ddccfe85003f9d0e4f8ca1c212b32a892f9f21151ed7bcb7b775c4e8f04a1dc6` |
| `backend/app/redesign/cad.py` | `43672b306083c0b362b2b10ce314dfa68ec0304135032a442dc4a67105c8ff00` |
| `backend/app/redesign/verify.py` | `449ad1af366e4c3072bcccaea36624e957bf24c9cfd81f8ddcbf02f55e97837a` |
| `backend/app/routers/redesign.py` | `e239cf466f1a62052534d223a28331e9400204f9dea1f08f30f0d037afb3424f` |
| `backend/app/models.py` | `4ced979ac830f52978aa9bfb48ab3732f37562b9ce32106c4893630bfb36a90d` |
| `backend/app/ifc/services/runners.py` | `5d334a2f0508b5c1a54257033535a779f0259d567dbffc2a379d3de296f5637b` |
| `backend/app/workers/ifc_worker.py` | `3cbeab541f8a1a52c37e4e9e4c8371b577d9bfdb65c07550ccc568411784f93c` |
| `backend/tests/test_redesign_apply.py` | `73d336e15832943e64381cb617c83bf54ae021cd9961a23108e21d46ae726010` |
| `backend/tests/test_redesign.py` | `4e6eb88a61ab4641463a0b06b4cd244f95451c054b10bfd2902e65803459642a` |
| `backend/tests/test_prep_readiness.py` | `1f20a1ab0fe94e7839ad4380aa2a7c22209b4e777a5c9d5dc13133f669fe0bfb` |
| `frontend/src/components/prep/RedesignPanel.tsx` | `a6425efe7249ff0c2f8ceafaa610e2c1283575760b7139b9b19d86f789c960b0` |
| `frontend/src/components/prep/types.ts` | `5e0231934912f9bff085859ee618ae5a3416788c736af80264c0660d9095c26b` |
| `.gitattributes` | `b1fb5030384fe9291a7cc1831ed174fc8d1f90f6270d83a238fef410b8561c7e` |

- Evidence folder `docs/milestones/M5/evidence/safe-apply/`: all file hashes (18 files) are in `MANIFEST.json`; for example `full-suite.xml` `97eca2adaaf9381fb41865dc22da518d871a2aa184d36c0769a875ee4e9729fd`, `targeted.xml` `d8e5fca5367a300e1d9a5fb721ed3b90c8be3401cfb6e0343576cee4b3468043`, `full-suite-comparison.json` `83ad3011e7b174ffdb27b65d9903dfa18916c9bb33ce0db9f4cd3e94ccf27f17`.
- No model, profile, schema or policy version applies: no model or provider request was made.

## 5. Named tests and actual results

### 5.1 Functional / mocked and SQLite

Stand-in AutoCAD = a Python script echoing the script and printing markers; stand-in read-back = the source DXF with the script's inserts and erases applied; SQLite = the suite's real file-backed WAL database with two connections.

| Run | Result | Source |
|---|---|---|
| Targeted at c274205: `test_redesign_apply`, `test_redesign`, `test_drawing_prep`, `test_prep_readiness` | 93 passed (59 + 16 + 14 + 4); ORCH-040 reproduced 93 passed in 231.7 s | report; ORCH-040 check 4 |
| Full suite at c274205 (`AI_ENABLED=false DATA_ROOT=`) | 1878 tests, 1842 passed, 1 failed, 35 skipped, 2091.65 s (implementer); ORCH-040 reproduced the same totals in 2333 s | report; ORCH-040 |
| The one failure | `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it`: same content as M4 run 2 (extra items 3-SDDC2, 3-SSDC2, SIGA-OSD-FCN); U2M5V-08 notes only the printed set order differs | ORCH-040 |
| Comparison with M4 run 2 | no new failure; 59 added tests, all in `test_redesign_apply`; per-test states identical between implementer and verifier | `full-suite-comparison.json`; ORCH-040 |
| Baseline at f15ac01 | 34 passed (16 + 14 + 4) reproduced by ORCH-040; the implementer kept no log and recorded 30 | ORCH-040 check 3; report |
| Mutation M1 (lock removed) | 2 failed (concurrency (a) and the candidate lock-primitive test); (b) passes by design | implementer; ORCH-040 |
| Mutation M2 (DWG copy inside the lock) | the unrelated-writer test fails with "database is locked" (1 failed in ORCH-040) | implementer; ORCH-040 |
| Verifier mutations V3 (proposed drawn), V4 (archive write restored), V5 (422 gate removed), V6 (publish without verified check) | 11, 3, 3, 1 failed respectively | ORCH-040 |
| Control after restore | 4 passed; final targeted control 93 passed | ORCH-040 |
| Frontend `tsc -p tsconfig.app.json --noEmit` on a scratch copy | 0 errors; a deliberate error was reported as a negative control. Type-checked only; page not rendered | `tsc-frontend.txt` (empty); ORCH-040 check 6 |

### 5.2 Real AutoCAD

None. Neither the implementation report nor ORCH-040 contains a real-AutoCAD result, and there is no real-model result. Old session evidence is supporting only, because the `apply()` integration differs.

### 5.3 What only the OD-16 (c) run can prove

1. Approved inserts and erases reconcile exactly against a Core Console read-back of the saved copy.
2. A missing block or a mid-script LISP error, and the count check before QSAVE, publish nothing.
3. The standalone completion marker is recognised against a real `autocad.log` echo (nonce-bound).
4. The saved output is a valid DWG that opens and reads back.
5. Library paths with spaces and parentheses resolve in a real `-INSERT`.
6. Cancel or timeout kills the real Core Console process and publishes nothing.
7. The source drawing's sha256 is unchanged afterwards.
8. Hard-link creation on the target volume and on the archive volume (if a synced folder).

## 6. Independent review disposition

- ORCH-035 (disposition of the RD-M2 correction package): CHANGES REQUIRED. The mechanism was accepted as the design basis; the package was not accepted as a finished correction. Reasons: apply-level concurrency test missing (U2M5-01); whole-database lock during the DWG copy on SQLite (U2M5-02); no temporary-to-final publication step (U2M5-04); hashes and `full.log` not reproducible (U2M5-05); no independent review of the correction on file (U2M5-06). These were to be discharged inside the M5 port; ORCH-040 records the port's fixes for them.
- ORCH-040 (independent verification of the port, 8 October 2026): **PASS WITH CONDITIONS**. No blocker, major or medium finding; 4 Low (U2M5V-01..04) and 7 Info (U2M5V-05..11). Every claimed run reproduced. Fit to merge into `roadmap/u2`: YES. The verifier states it did not write or review the candidate, the correction or the port.
- Conditions:
  - **C1.** M5 is not accepted until the OD-16 (c) real-AutoCAD run proves the eight items in 5.3.
  - **C2.** Fix U2M5V-01..04 before acceptance, or have the owner accept them. None touches `cad.py` or `verify.py`, so the fixes need no new AutoCAD evidence.
  - **C3.** The non-SQLite lock path (U2M5-08) must be covered before any move away from SQLite.

### Owner-only decisions and actions still required

- Schedule the OD-16 (c) run: name the machine and supply the isolated GC-01 copy and a dedicated AutoCAD profile. The decision pack and the M2 refresh record that GC-01 inputs are not in the repository.
- Accept the Low findings U2M5V-01..04 or let ORCH-041 (issued) correct them.
- Accept M5 (this record does not).
- Decide on merge into the platform branch and any deployment.

## 7. Integration status, retention, rollback, limitations

- **Integration.** Merged into `roadmap/u2` as merge commit `fcc5ddd` (`fcc5dddaef449a7d4e80cfe6940fea6f0182d2a1`, "Merge task/m5-safe-apply into roadmap/u2 (ORCH-039; verified ORCH-040 PASS WITH CONDITIONS)") on 2026-10-08; `e78d1a1` is the following session-log commit. **Not merged into the platform branch; not in the live clone; not accepted.**
- **Correction task.** ORCH-041 (low findings U2M5V-01..04) is issued, not run. Its task file `MR/orchestrator/tasks/ORCH-041-TASK.md` was not present in this worktree, so its content is not cited here.
- **Retention.** The report, manifest and evidence stay in `docs/milestones/M5/` (`.gitattributes`: `docs/milestones/M5/** -text`; `*.log` evidence force-added). Review files stay in the review folder above. OD-16 (c) requires any real-run output to be retained as evidence only.
- **Rollback.** The inputs give no rollback procedure. Facts they do give: the work is one merge commit on `roadmap/u2` (`fcc5ddd`) and nothing is merged into the platform branch; no stored data is migrated (OD-17 b); the sweep moves unreferenced outputs to `redesign/orphaned/` and never deletes final outputs.
- **Known limitations.**
  - Non-SQLite `with_for_update` path untested (U2M5-08; C3).
  - No real crash between rename and commit was produced; the sweep is tested on the files such a crash leaves.
  - Frontend type-checked, not rendered or exercised in a browser; a rendered check belongs to acceptance.
  - `refresh()` remains in the module, unused by Apply (U2M5V-11).
  - Publish is not bound to the `copy_sha256` in `verification.json` (U2M5V-07, Info).
  - Commit trailers name a model other than the report's (U2M5V-09, Info).
