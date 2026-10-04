# RD-M2 — Apply Fails Closed and Draws Only Approved Changes

Written for the RD-M2 implementation reviewer and the platform owner. All statements are the implementer's, pending independent review. Nothing here approves an engineering design or says the Redesign feature is production-ready.

## 1. Candidate identity and verdict

**Verdict: READY FOR INDEPENDENT RD-M2 REVIEW.** The owner's condition is met: the successful output of the authorised v2 AutoCAD session passed marker validation, read-back and change reconciliation (`AUTOCAD-VALIDATION.md`).

| | |
|---|---|
| Delivered candidate | **v2.1**: `evidence/candidate-files.json` (382 files). The patch is `evidence/rdm2-candidate.patch`; hashes are in `PACKAGE-MANIFEST.json` |
| AutoCAD-validated build | **v2**, manifest sha256 `5345c1e7998a40c821ed830e736e163cf3bb261b1dcd350bc7b67fe2d3a48a21`. v2.1's application code is byte-identical to v2; only one test assertion differs (`application_code_differs_from_v2 = []`) |
| Earlier build | v1 (AutoCAD session 1; a log-parsing defect refused a correct result). Fixed in v2 |
| Base | `ep-platform` HEAD `13eb73ce85e5ac55c14303efe9d8511090ace723` (`main`) plus the untracked working tree as hashed at RD-M2 T0. The Redesign code is untracked, so identity is by file hash |
| Applied to the live tree? | **No.** The :8001 API hot-reloads `backend/app`. Integration is the owner's step (`NEXT-MILESTONE-HANDOFF.md` §1) |

## 2. Package

`G:\dev (2)\dev\ep-platform\docs\milestones\redesign\RD-M2\`

## 3. Application files changed

- `backend/app/redesign/service.py`
- `backend/app/redesign/cad.py`
- `backend/app/redesign/verify.py` (new)
- `backend/app/routers/redesign.py`
- `backend/app/ifc/services/runners.py`
- `frontend/src/pages/ProjectRedesignPage.tsx`

Tests: `backend/tests/test_redesign.py` (3 assertions made stricter) and `backend/tests/test_redesign_apply.py` (new, 35 tests). No migration. Details are in `CHANGE-MAP.md`.

## 4. Findings

| Status | Findings |
|---|---|
| **Closed** (in the candidate) | **F001** (portable module resolution) · **F002** (approved-only) · **F004** (fail-closed script; the hazard is also shown not to occur in this AutoCAD build) · **F016** (relative output paths, legacy rebase, traversal refusal) · **F017** (a completed or stale Apply is not re-run) · **F023** (output verification with read-back) · **F033** (unique names, exclusive create) · **F034** (cancellation) · **F035** (confirmation gate) |
| **Partly closed** | **F003**: exposure closed; AI acceptance is unchanged. **F032**: Apply snapshot guard only; Plan/PATCH races remain. **F030**: Apply no longer re-places or re-coordinates; Plan's behaviour is unchanged. **F024**: per-run folders are kept as evidence; no retention policy. **F031**: archive writing removed; controlled promotion is not designed |
| **Open** (out of scope) | F005–F014, F018–F022, F025–F029 |

## 5. Approved-only drawn set

`_drawn` is `status == "approved"`, plus something to make, plus confirmation where `residual > 1.0 m`. It applies to review changes and modules alike. The page wording now says "Proposed, not drawn until approved" and shows a "Confirm this spot" control. The Apply POST returns 422 when nothing is approved. GC-01's drawn set is 11 under both the old and new rules (`APPROVED-DRAWN-SET.md`).

## 6. Portable library

CT1, CT2 and CR are resolved by interface code from this installation's `app/redesign/library`. Each file must be listed in `modules.json`, sit inside that folder, end in `.dwg` and exist; otherwise the Apply is refused before AutoCAD starts. The stored office-PC paths stay in the database untouched. With the real AutoCAD, the script referenced only `…/code (2)/backend/app/redesign/library/{CR,CT1,CT2}.dwg` (`PORTABLE-LIBRARY-RESOLUTION.md`).

## 7. Fail-closed and output verification

- **Script.** Each step is guarded by `ep_failed` and checked by the next line. `entdel` is used only on a just-verified new INSERT of the expected block. An erase happens only on an INSERT of the expected block, in model space, at the read insertion point. A count check runs before the only, guarded `QSAVE`. Markers are built at run time and bound to the run's nonce.
- **Verification.** A result counts only when all of these hold:
  - exit code 0;
  - no FAIL or NOSAVE marker;
  - exactly one standalone OK marker with the expected counts;
  - the copy changed;
  - the read-back, made by the same converter for source and copy, reconciles by handle: every erase gone, nothing else gone, every insert present, no other insert.
- **Partial results.** A partial or unverified copy stays in the run folder as evidence and is never published (`CAD-FAIL-CLOSED-CONTRACT.md`, `OUTPUT-VERIFICATION.md`).

## 8. Idempotency, cancellation, snapshot guard

- **The job carries what was asked:** the source hash, the decision fingerprint and the drawn count. Before anything runs, the Apply is refused when:
  - the row's output was made after the job was created (RD-M1 job 119, reproduced in a test);
  - the source changed;
  - the decisions changed;
  - the same set was already made and the file still exists.
- **Cancellation:** `check()` runs at every stage and about once a second while AutoCAD works. On a cancel, AutoCAD is killed, its log kept, and the status set to `cancelled`.
- **Snapshot guard:** the decision snapshot is recomputed before publication, and a change in it gives `stale` with nothing published (`IDEMPOTENCY-AND-RECOVERY.md`, `CONCURRENCY-GUARD.md`).

## 9. AutoCAD isolated runs

| Session | Build | A: 11 approved GC-01 changes | B: missing block first | C: synthetic approved erase |
|---|---|---|---|---|
| 1 | v1 | inserts verified, saved; **refused** by a parser defect (echoed marker counted twice); nothing published | script aborted; nothing saved or published | not run |
| 2 | v2 | **made and verified**: standalone OK 11/0; read-back 11/11 inserts, 0 unexpected erasures; added exactly 11 INSERT, 11 CIRCLE, 18 TEXT; published only in the isolated output (sha256 `32b90f64…`) | aborted at the first insert; copy = source; **nothing saved or published** | **made and verified**: OK 0/1; read-back: exactly `5DD10` erased, nothing else |

Attribute-level comparison of all ~4,800 common entities found only AutoCAD's renumbering of 43 anonymous `*U` blocks (identical content) and one floating-point normalisation. The output **differs from the source only as expected**. Source DWG `66043c11…` was unchanged before and after, live and isolated.

## 10. Tests

| Run | Tests | Passed | Failed | Skipped | Errors | Collection errors | State changes vs base |
|---|---|---|---|---|---|---|---|
| base (unchanged) | 1,298 | 1,262 | 2 | 34 | 0 | 0 | – |
| **v2.1** | 1,333 | **1,297** | 2 | 34 | 0 | 0 | **0** |

- The 2 failures are pre-existing, identical on base, and unrelated to Redesign.
- One deselected test would run the real AutoCAD on a Desktop file.
- Focused: Redesign 51/51.
- Frontend type check: 0 errors (base 0).

Details are in `REGRESSION.md`.

## 11. Proof of non-mutation

`PACKAGE-CHECK.json` (14/14 checks pass) and `DATA-SAFETY-REPORT.md` cover:
- the live code (0 changed);
- source drawings and library (unchanged; GC-01 DWG `66043c11…`);
- the RD-M1 package (78/78 unchanged);
- no archive path;
- the running services (same PIDs on the same ports);
- no private names.

**The owner used the live platform during RD-M2.** User 5 ran 16 Applies and 1 Plan through the browser (jobs 122–138). The first two failed with RD-M1's CT2 error; the next 14 succeeded with the old code. The live DB and uploads changed accordingly. Every live change is attributed to that activity: the 14 added uploads are exactly those jobs' outputs, every job and activity row has a user, and none of the candidate's names or markers appear in live data. This audit never signed in to the live API.

## 12. Limitations and blockers

- No blocker.
- The candidate is not integrated; the owner's step is needed.
- Not proven with the real AutoCAD: a **wrong-target** erase (unit and script tests only), cancellation of a real Core Console (tested with a real child process standing in for it), and a real `*U`-tolerant attribute check, which the product does not yet perform.
- AutoCAD left a few `%TEMP%` files; they are listed, not deleted when uncertain or locked.
- The intermittent `test_ai_sheet_reader` test is pre-existing.
- **Live risk until integration:** the owner's 14 successful live Applies (jobs 124–138) ran the **old** code:
  - they draw review changes still `proposed` (F002);
  - they have no output verification (F023);
  - they use minute-resolution names (F033).

  Those output files were not inspected in RD-M2. They are evidence of the old behaviour, not of the candidate.

## 13. Proposed next bounded milestone

**RD-M3, "Wall geometry the drawing actually shows" (F005/F006), proposal only and not started.** The wall index would be built from effective layers with visibility, and the deny-list would become an allow-list. It needs two more Golden Cases first (`NEXT-MILESTONE-HANDOFF.md` §3).
