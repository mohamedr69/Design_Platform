# M2 refresh — RD-M1 findings delta

| Item | Value |
|---|---|
| Date | 6 October 2026 |
| Milestone | Unified M2 (Baseline & Error Inventory), refresh of the accepted redesign baseline RD-M1 |
| Repository HEAD | `457c8159c7c587a36e40f0ba2af711a55cc3f00a` (457c815). Code under `backend/` and `frontend/` is identical to commit 771001e (orchestrator statement; the surveys recorded an empty `git diff --stat 771001e HEAD -- backend frontend` at 4bab8d2, S6 section 1, and at f828ca1, S7 section 0) |
| Companion files | `M2R-FINDINGS-DELTA.csv` (the 35 RD-M1 rows, 24 original columns unchanged plus 6 appended), `M2R-GOLDEN-STATUS.md` |
| Evidence | `evidence/surveys/S6-findings-delta.md` (the delta, "S6"), `evidence/surveys/S7-new-surface.md` ("S7"), `evidence/TEST-RESULTS.md`, `evidence/tests/` |
| Baseline refreshed | `docs/milestones/redesign/RD-M1/` (RD-M1-REPORT.md section 1, FAILURE-INVENTORY.csv and .md, GOLDEN-CASE-SELECTION.md). RD-M1 is retained unchanged: its 35-finding inventory and frozen Golden evidence are not edited |

**Snapshot statement.** This is a static reading of the branch. The surveys read source and ran nothing. The tests were run by ep-test-runner as recorded in `evidence/TEST-RESULTS.md` (116 passed, seven files, `AI_ENABLED=false`, synthetic fixtures). No model call, no AutoCAD, no database snapshot and no Golden drawing was used by anyone in this refresh. Every finding stays UNREVIEWED, as in RD-M1. This file records what S6 found; the scribe did not re-verify code.

**Result in one line.** Of the 35 findings, none is fixed, 32 are still open, 1 is superseded by verified behavior for detector coverage only (F027) and 2 are not reproduced (F026, F028). Both Critical and all nine High findings are still open.

## 1. Reading guide

### 1.1 The four classifications

S6 Table A assigns one class per finding. The definitions below are the ones this document uses to read those classes. Qualifiers that S6 attached to a class (for example "narrowed" or "columns added") are kept in the CSV column `refresh_note`; the column `refresh_classification` holds only the four base values.

| Class | Meaning | What it requires |
|---|---|---|
| FIXED | The code or data path that RD-M1 named as the cause has been changed in the active tree, so the defect cannot occur by that route. | A reading of the changed lines at HEAD that shows the cause is gone. New UI or new AI code that sits beside the cause does not qualify, and neither does a historical RD-M2 candidate that is not in the tree. Count: 0. |
| STILL OPEN | The cause code is present at HEAD, unchanged, moved or narrowed. The defect can still occur. | A file:line at HEAD that shows the cause. A model verdict that mitigates the defect only sometimes (F003) does not close it. |
| SUPERSEDED BY VERIFIED BEHAVIOR | The behavior RD-M1 described has been replaced by different behavior in the active tree, and that new behavior is pinned by a test. | A test in `backend/tests` that pins the corrected behavior and exercises the code, named in `tests_now`, and shown as passed in `evidence/TEST-RESULTS.md`. The scope is stated with the class. "Verified" means verified on the tests' synthetic input, not on a real drawing. Count: 1 (F027, detector coverage only; the named tests are in `test_drawing_prep.py`, 14 passed). |
| NOT REPRODUCED | S6 could neither show the defect in HEAD code nor show it gone. | Either no code defect can be cited (F028), or the input that produced the RD-M1 instance has changed and only a re-run on the owner's inputs can decide (F026). The finding stays in the inventory and is not closed. |

A test that passes is not enough on its own to supersede a finding. Two tests pass for F002 (`test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved` and `test_a_detector_added_for_coverage_or_rejected_by_the_orchestrator_is_drawn_only_once_approved`), but S6 records that they "pin the current behavior, not an approved-only rule", so F002 stays STILL OPEN.

### 1.2 How the CSV is built

- Columns 1 to 24 are copied cell for cell from `docs/milestones/redesign/RD-M1/FAILURE-INVENTORY.csv`. Nothing in them was edited, including the RD-M1 `recommended_milestone` text (for example "RD-M4 coordination (proposed)").
- Columns 25 to 30 are new: `refresh_classification`, `current_location` (file:line at HEAD, one reference per line, S6's short names expanded to repository paths), `current_quote` (one or two lines taken from S6 Table A), `tests_now` (test functions, as `file::function`), `owner_milestone` (unified M-number; the first is the primary owner), `refresh_note`.
- A test marked "[not in the 116-test run]" is cited by S6 but its file was not among the seven files run by ep-test-runner, so `evidence/TEST-RESULTS.md` holds no pass result for it.
- References such as "S6 Table B" and "S6 section 6" in the notes point into `evidence/surveys/S6-findings-delta.md`.
- Line numbers are S6's (taken at 4bab8d2). Code under `backend/` and `frontend/` is unchanged since, so they are expected to hold at 457c815; the scribe did not re-check them.
- Format: UTF-8, LF line endings, every cell quoted. The file is cell-equal, not byte-equal, to the RD-M1 CSV (see M2R-GOLDEN-STATUS.md, section 5).

## 2. Summary table, F001 to F035

| ID | Severity | RD-M1 cause status | Classification | Owner | Note |
|---|---|---|---|---|---|
| RD-M1-F001 | High | CONFIRMED (code + preserved script + DB) | STILL OPEN | M5 | Absolute library path still stored per change; the RD-M2 resolve-from-running-library change is absent. |
| RD-M1-F002 | Critical | CONFIRMED (code) | STILL OPEN | M5 | Proposed review changes with verdict ok, check or none are still drawn; an orchestrator reject and coverage detectors are now excluded. |
| RD-M1-F003 | Critical | CONFIRMED (code + stored answer) | STILL OPEN | M5 + M12 | No room or confidence gate on a REMOVE; only a model reject stops it, and the agents-off path takes the first candidate. |
| RD-M1-F004 | High | CONFIRMED (code); consequence SUSPECTED (not reproduced) | STILL OPEN | M5 | Bare `entdel (entlast)` after every `-INSERT`; `cad.py` is byte-identical to the RD-M1 base. |
| RD-M1-F005 | High | CONFIRMED (code + DXF attribution) | STILL OPEN | M8 | Wall index is still a layer-name deny-list with no invisible, frozen or viewport test; `walls.py` unchanged. |
| RD-M1-F006 | High | CONFIRMED: modules sit on parking-block geometry (data + code). Not plotting: PROPOSED (visual), explained by the invisible flag for the ZCV segment only. Engineering judgement: PROPOSED (AI) | STILL OPEN | M8 | Nearest-wall snap still uses the F005 index; the GC-01 instance needs a plan re-run. |
| RD-M1-F007 | High | SUSPECTED (shared-coordinates assumption not verified; no registration check exists - confirmed by code) | STILL OPEN | M8 | Row anchor is now the equipment symbol centre; the shared-coordinates assumption and the missing building-outline check are unchanged. |
| RD-M1-F008 | High | CONFIRMED (code) | STILL OPEN | M8 | Columns added as an obstacle; text, doors, windows, equipment and other disciplines are still not inputs. |
| RD-M1-F009 | Medium | CONFIRMED cause class (F008); instance PROPOSED (visual) | STILL OPEN | M8 | Text is not a coordination input; the GC-01 instance needs a fresh render. |
| RD-M1-F010 | Medium | CONFIRMED cause class (F008); instance PROPOSED (visual) | STILL OPEN | M8 | Note footprint is estimated and is not tested against columns or existing text. |
| RD-M1-F011 | Medium | CONFIRMED cause class (F008: doors excluded); instance PROPOSED (visual) | STILL OPEN | M8 | Door and window layers are excluded from the wall index and not modelled as obstacles. |
| RD-M1-F012 | Medium | CONFIRMED (code) | STILL OPEN | M8 | An unresolved clash is appended with no flag; the gate has no clash reason. |
| RD-M1-F013 | Medium | CONFIRMED (stored answers + code) | STILL OPEN | M12 | Orientation uncertainty is not gated; the orchestrator may mark `check`. |
| RD-M1-F014 | Medium | SUSPECTED (whether the list sent at plan time contained these symbols is not stored) | STILL OPEN | M12 | The preferred-symbol override is still silent; nothing is recorded on the change. |
| RD-M1-F015 | Medium | CONFIRMED (data); visual result UNVERIFIED (applied output not rendered) | STILL OPEN | M8 + M13 | Bound `$0$` xref blocks are not excluded from the block list. |
| RD-M1-F016 | Medium | CONFIRMED (code + data) | STILL OPEN | M5 | Absolute output path still stored; the download route opens `Path(output_path)` directly. |
| RD-M1-F017 | Medium | CONFIRMED (log + DB) | STILL OPEN | M5; M11 secondary | Stale running jobs are requeued by heartbeat age; `apply()` does not compare output time with job creation. |
| RD-M1-F018 | Medium | CONFIRMED (code + data) | STILL OPEN | M18 + M7 | No `decided_by` or `decided_at` on any decision. |
| RD-M1-F019 | Medium | CONFIRMED (code) | STILL OPEN | M10 | `view()` and the sibling GET routes still insert a row and commit. |
| RD-M1-F020 | Low | CONFIRMED (data); origin of the 7 calls UNKNOWN | STILL OPEN | M7 + M18 | AI calls are still not linked to the job (`run_id=None` in `ai_usage`). |
| RD-M1-F021 | Medium | CONFIRMED (code); rotated-drawing failure NOT REPRODUCED (no rotated case available) | STILL OPEN | M8 | `fit()` has no rotation term; no rotated Golden Case exists. |
| RD-M1-F022 | High | CONFIRMED (code + data) | STILL OPEN | M8 | `_place` has no containment test; room fill exists for detector coverage only. |
| RD-M1-F023 | High | CONFIRMED (code) | STILL OPEN | M5 | Output check is file existence and mtime; the AutoCAD log is discarded on success. |
| RD-M1-F024 | Low | CONFIRMED (filesystem + code) | STILL OPEN | M5 | Leftover cleanup runs only on success and cannot remove a directory. |
| RD-M1-F025 | Low | CONFIRMED (data) | STILL OPEN | M7 + M10 | A failed module uses `r["floor"]`, a placed module uses the sheet floor. |
| RD-M1-F026 | Medium | CONFIRMED (data); typical-plan cause SUSPECTED | NOT REPRODUCED | M8 | The producing code is unchanged but its anchor input changed, so the 47-of-200 count does not carry over. |
| RD-M1-F027 | Medium | CONFIRMED (code) | SUPERSEDED BY VERIFIED BEHAVIOR | M8 | Detector coverage is measured at the radius, re-measured after moves (SUPERSEDED for plan-time detector coverage only; the re-check after an engineer move is untested by assertion and spacing is not re-checked; first verification N1) and gated; other rules are not. |
| RD-M1-F028 | Low | CONFIRMED (cache data) | NOT REPRODUCED | M12 | Code-level basis: nothing records answer variation (ai.py:12 PROMPT_VERSION; config.py:426-428); kept NOT REPRODUCED because the instance needs the RD-M1 database snapshot; needs the stored cache or fresh model calls. |
| RD-M1-F029 | Medium | CONFIRMED (stored answer); no containment check (F022) | STILL OPEN | M8 + M12 | The answer is kept whatever its note says; no containment test. |
| RD-M1-F030 | Medium | CONFIRMED (code) | STILL OPEN | M5 | `apply()` calls `refresh()` before it builds the draw list. |
| RD-M1-F031 | Medium | CONFIRMED (code + job results) | STILL OPEN | M5 | Apply still writes the output into the project archive folder. |
| RD-M1-F032 | High | CONFIRMED (code); NOT REPRODUCED | STILL OPEN | M5; M11 secondary + M7 + M10 | Whole-row writes and read-modify-write with no version guard; the race itself was not reproduced. |
| RD-M1-F033 | Medium | CONFIRMED (code); NOT REPRODUCED | STILL OPEN | M5 | Minute-resolution output name and a plain `open(..., "wb")`; no exclusive create. |
| RD-M1-F034 | Low | CONFIRMED (code) | STILL OPEN | M5 | `apply()` never reads `check`; blocking `subprocess.run`, 1,200 s timeout. |
| RD-M1-F035 | Low | CONFIRMED (code) | STILL OPEN | M5 | The `confirm` flag is display only; `_drawn` ignores it. |

The note column is a one-line summary of S6 Table A column "Note" and column "Current file:line and decisive quote". The full quotes, locations and tests are in the CSV.

## 3. Totals

By classification (35 findings; S6 section 5):

| Classification | Count | Findings |
|---|---|---|
| FIXED | 0 | none |
| STILL OPEN | 32 | all others |
| SUPERSEDED BY VERIFIED BEHAVIOR | 1 | F027 (detector coverage only) |
| NOT REPRODUCED | 2 | F026, F028 |

By severity (RD-M1 counts Critical 2, High 9, Medium 18, Low 6 are reproduced; they match the RD-M1 CSV):

| Severity | Total | STILL OPEN | SUPERSEDED | NOT REPRODUCED | FIXED |
|---|---|---|---|---|---|
| Critical | 2 | 2 | 0 | 0 | 0 |
| High | 9 | 9 | 0 | 0 | 0 |
| Medium | 18 | 16 | 1 (F027) | 1 (F026) | 0 |
| Low | 6 | 5 | 0 | 1 (F028) | 0 |
| All | 35 | 32 | 1 | 2 | 0 |

By owner milestone (counted from the CSV column `owner_milestone`; a shared finding counts once under its primary owner and once more under each secondary owner):

| Owner | As primary owner | In any role |
|---|---|---|
| M5 Safe Apply & AutoCAD Block Library | 14 | 14 |
| M8 Deterministic Geometry, Placement & Coordination | 14 | 14 |
| M12 Multi-Stage AI & Visual Review | 3 | 5 |
| M7 Central Processing, Relationships & Domain Records | 2 | 4 |
| M10 Database-Driven Tab Migration | 1 | 3 |
| M18 Durable Engineering Events & Timeline | 1 | 2 |
| M13 Real-Project Accuracy Validation & Release | 0 | 1 |

S6 section 5 groups F018, F020 and F025 together under "M18/M7". Table A gives F025 as "M7 (floor aliases) / M10", and the CSV follows Table A, so the primary counts above differ from S6's grouping line for M7, M10 and M18 (S6: M10 1, M18/M7 3; here: M7 2, M10 1, M18 1; the totals still sum to 35 together with M5 14, M8 14 and M12 3).

## 4. Critical and High findings

Each paragraph quotes S6 Table A, the survey's own evidence. "S" is `backend/app/redesign/service.py`, "PR" is `backend/app/redesign/prepare.py`, "CAD" is `backend/app/redesign/cad.py`, "W" is `backend/app/redesign/walls.py`, "AI" is `backend/app/redesign/ai.py`.

**RD-M1-F002 (Critical) — STILL OPEN, narrowed, M5.** S6: `S:695-701` reads `proposed = (c["status"] == "proposed" and c.get("source") not in (INTERFACE, PR.COVERAGE) and (c.get("check") or {}).get("verdict") != "reject")` and `return (c["status"] == "approved" or proposed) and bool(c.get("remove") or c.get("insert"))`. It is used at Apply (`S:1496`), the draftsman PDF (`S:1378`) and `out["drawn"]` (`S:1551`). What narrowed since RD-M1: a change the orchestrator marked `reject`, and coverage-added detectors, now need approval. Still drawn while `proposed`: review changes with verdict `ok`, `check`, or no verdict (agents off, or review failed). Two tests assert this and so "pin the current behavior, not an approved-only rule". RD-M2 change 4 is absent (Table B, B1). Owner decision A in the RD-M1 handoff is still the open question. The page wording is in section 6 below. Not settled by static reading: whether earlier Apply outputs contained unapproved review placements; that needs the 17 applied DWGs (S6 section 6).

**RD-M1-F003 (Critical) — STILL OPEN, AI-dependent mitigation only, M5 + M12.** S6: `AI:74` `"candidate": candidate if 1 <= candidate <= candidates else 0`; `AI:79` confidence is only normalised, never gating; `S:811` `change["remove"] = {k: candidate[k] for k in ("n", "handle", ...)}` with no room check; `S:699-700` only an orchestrator `reject` stops drawing. S6: "Exposure now depends on a model verdict": `PR._review_input` (`PR:629-647`) gives the orchestrator `placement_confidence` and `placement_note`, and its prompt says reject "a REMOVE of a device that is not the one meant" (`agents.py` REVIEW_SYSTEM), but "Not deterministic; `check` verdicts are still drawn." New exposure: with agents off, `PR:125` `candidate = (named or change["candidates"])[0]["n"]` picks the nearest candidate even if no name matches, with no orchestrator; `prep_ai_enabled` defaults False (`config.py:425`). Not settled statically: whether the new orchestrator would reject the lift-lobby REMOVE (change `d89599d510abfedf`); that needs a model call.

**RD-M1-F001 (High) — STILL OPEN, M5.** S6: `S:435` `"library": (LIBRARY / f"{code}.dwg").resolve().as_posix()` stores an absolute path per change; `S:629-632` keeps a moved or edited module's old insert; `S:1184-1185` Plan keeps approved, skipped, moved and edited changes verbatim; `S:1430-1432` refresh re-places only when `"library"` is missing; `CAD:114-117` emits `insert["block"] + "=" + insert["library"]`. RD-M2 change 1 (resolve from the running library) is absent. S6 adds that the new code "makes the stale path more durable" (`keep_interfaces/restore_kept`, `S:513-523`). No test covers a missing path. The defect is decided statically; the AutoCAD "Function cancelled" outcome needs AutoCAD.

**RD-M1-F004 (High) — STILL OPEN, M5.** S6: `CAD:119-121` `(setq ep_f (cdr (assoc 41 (entget (entlast)))))` then `(entdel (entlast))` unconditionally after every `-INSERT`. `cad.py` is byte-identical to the RD-M1 base (sha256 starts `031e760a`); the RD-M2 fail-closed AutoLISP (`ep_new_insert`, `ep_erase`) is absent. The only test checks script text. Not settled: whether AutoCAD continues after a LISP error (owner decision C).

**RD-M1-F005 (High) — STILL OPEN, M8.** S6: `W:25-26` `NOT_WALLS = re.compile(r"GRID|AXIS|DIM|...")` is a deny-list; `W:159` and `W:164` read every decomposed entity and test only the layer name. "No `invisible`, layer on/frozen/plot or viewport state anywhere in `walls.py` or `coverage.py` (grep empty)". `walls.py` is unchanged since RD-M1, and the new room and coverage code is built on this index, so it inherits the defect. The tests use synthetic walls. The layer composition of the real index needs GC-01 `source.dxf`.

**RD-M1-F006 (High) — STILL OPEN, M8.** S6: `S:455-469` `_nearest_wall` snaps to `walls.faces_behind(...)`, the nearest indexed face with no layer test of its own; `S:485-500` `_place_module` uses it; the faces come from the F005 index. The only test is synthetic. Whether the interface anchor change (F007) moved the two approved CT2 modules needs a GC-01 plan re-run.

**RD-M1-F007 (High) — STILL OPEN, anchor source changed, M8.** S6: `S:384-386` the comment still says "The trades' drawings share the fire alarm drawing's coordinates"; `S:550-551` `px, py = _page(sh["geometry"], *anchor)` then `if sh["plan"][0] <= px <= sh["plan"][2] ...`, the plan box being `review/pages.py:110` `plan = (w * 0.02, h * 0.02, panel, h * 0.98)` (whole sheet minus title panel). No transform or plausibility check. Changed since RD-M1: the row anchor is now the settled equipment symbol's centre, or None (`interfaces/service.py:1116`, `:1440`), which "addresses the 'label is not at the fan' alternative only". The cross-drawing coordinate assumption and the lack of a building-outline check are untouched, "so an anchor outside the PLOT LIMIT still passes".

**RD-M1-F008 (High) — STILL OPEN, columns added as an input, M8 (visual check M12).** S6: `S:952` existing devices come only from change `candidates`; `S:982` each is `EXISTING_RADIUS_M` (0.25 m) square; `S:976` `if columns is not None and columns.hit(mine[0], GAP_M): return False` is the only new obstacle. "No text, notes, doors, windows, equipment, ceilings or other disciplines." Columns (6 October 2026, `coverage.py`, `PR.columns`) narrow the finding; "nothing else changed". Four tests cover the movement rules (two in `test_redesign.py`, two in `test_drawing_prep.py`); none covers text, notes, doors or equipment.

**RD-M1-F022 (High) — STILL OPEN, room fill for detector coverage only, M8.** S6: `review/pages.py:110` plan box is the whole sheet; `S:794-866` `_place` has no containment test; `S:551` the interface plan test uses the same box. New: `coverage.room_at(walls, ...)` and `PR.rooms` (`PR:235`) fill rooms from the wall index for detector coverage, and the coordination agent's point is refused when out of its room (`PR._decide`), "but a placement answer is never checked against the room it names". Room polygons depend on the F005 wall index.

**RD-M1-F023 (High) — STILL OPEN, M5.** S6: `CAD:167` `if not copy.is_file() or copy.stat().st_mtime <= before:` is the only check; `CAD:176` returns the log but `S:1506` calls `cad.apply(...)` without using it, so the log is discarded on success. RD-M2 `verify.py` is absent (the file does not exist). No test.

**RD-M1-F032 (High) — STILL OPEN, NOT REPRODUCED as a race, M5 + M7 + M10.** S6: `PR:151` and `PR:193` `row.changes = [dict(c) for c in changes]` after each placement answer; `S:1216`, `S:1239`, `S:1248` whole-row writes from the Plan's start-time list; `S:690` `set_status` and `S:1319` `adjust` read-modify-write "with no version or status guard"; `R:78` Plan and Apply keys differ by `kind`; `S:1443` and `S:1475` Apply's `refresh` commits. RD-M2 `content_fingerprint`, `_snapshot` and the R1 `BEGIN IMMEDIATE` publication lock are absent. "The Plan now runs longer (more agent stages), widening the window." The tests show that Plan keeps settled changes, not concurrency. The race itself needs concurrent live requests (S6 section 6). The RD-M1 CSV already carried "NOT REPRODUCED" in its cause status for this finding; S6 classifies it STILL OPEN because the code that permits the race is present.

## 5. RD-M2 candidate changes (S6 Table B)

The RD-M2 candidate (v2.1: 6 changed and 2 added files, `RD-M2/evidence/candidate-files.json`) and the RDM2-R1 correction (changes `service.py` and `test_redesign_apply.py` only) were written against the RD-M1 code. S6: `git apply --check` of the v2.1 patch on the active tree fails (`backend/app/redesign/service.py: patch does not apply`, and `frontend/src/pages/ProjectRedesignPage.tsx: No such file or directory`); the R1 patch also fails. "The candidate cannot be applied as is; it needs a port" (M5). Active `service.py` is not the RD-M2 base either, because the preparation work was added.

| # | Candidate change | In the active tree? | Evidence (S6) | Tests present? |
|---|---|---|---|---|
| B1 | `_drawn()` approved-only plus `requires_confirmation()`; `adjust(confirmed=)` | ABSENT | `S:695-701` still draws proposed review changes; no `requires_confirmation` outside unrelated `services/shop_drawings.py`; `R:110-117` `ChangeIn` has no `confirmed` | Contrary tests present: both F002 tests assert the old rule |
| B2 | `module_library()` and `to_cad()` resolve CT1/CT2/CR from the running library | ABSENT | `S:435` stores the absolute path; `S:1400-1419` `to_cad` passes `insert` unchanged; `CAD:114-117` | none |
| B3 | `ApplyError`, `ApplyRefused`, `ApplyStale` | ABSENT | grep finds none; `S:66-67` only `RedesignError` | none |
| B4 | `content_fingerprint`, `_snapshot`, `apply_request`, `_refusal` (approval snapshot guard) | ABSENT | no such names; `R:103-107` `start_apply` takes no snapshot | none |
| B5 | `output_file_for`, `_unique_output`, `_publish` (exclusive create), relative `output_path`, legacy rebase | ABSENT | `S:1502-1507`, `S:1520`; `R:175-187` plain `Path(row.output_path)` | none |
| B6 | `_readback` DXF read-back and `verify.py` (log parsing bound to a nonce) | ABSENT | `backend/app/redesign/verify.py` does not exist; `CAD:164-168` mtime check only | none |
| B7 | Fail-closed AutoLISP (`ep_new_insert`, `ep_erase`, `ep_make`, `ep_fail`, count check before `QSAVE`, nonce markers); `cad.run()` with `Popen` polling and kill on cancel or timeout | ABSENT | `cad.py` byte-identical to base; `CAD:119-120` bare `entdel (entlast)`; `CAD:143-176` uses `subprocess.run` | The RD-M1 test still asserts the old text (`(entdel (handent "5DD03"))`); the candidate's stricter assertions are absent |
| B8 | Apply no longer calls `refresh()` and refuses stale placements | ABSENT | `S:1495` `refresh(db, project, drawing, row)` | none |
| B9 | Archive copy removed from Apply (owner decision 2) | ABSENT | `S:1509-1519` still writes `<source folder>/03- Drawings/Redesign/<name>`; page says "filed in the project folder" (`RP:391`) | none |
| B10 | Runner passes `request=job.params`, `job_id`, `job_created_at` to `apply()` | ABSENT | `ifc/services/runners.py:282-283` forwards only `check` and `progress` | none |
| B11 | Frontend wording ("Proposed, not drawn until approved", "Confirm this spot", output states, no "filed in") | ABSENT, and its target file is gone | the candidate edits `ProjectRedesignPage.tsx`, deleted in `b844adc`; `RP:246` still "Placed, to approve", `RP:391` still "filed in the project folder" | no frontend tests |
| B12 | RDM2-R1: final snapshot compare, exclusive publication and `made` transition in one serialized transaction (`BEGIN IMMEDIATE` on SQLite, `FOR UPDATE` elsewhere) | ABSENT | `grep -rn "BEGIN IMMEDIATE\|with_for_update" backend/app` returns nothing | none |
| B13 | New test file `backend/tests/test_redesign_apply.py` (35 tests, plus 2 from R1) | ABSENT | the file does not exist; `test_redesign.py` is the unchanged 16-test RD-M1 file | n/a |
| B14 | Edits to `test_redesign.py` (3 tests made stricter) | ABSENT | file hash equals the RD-M2 base (`60e0482c...`) | n/a |

Conclusion (S6): no RD-M2 or R1 change is present in the active tree. `cad.py`, `test_redesign.py` and the router's Apply behavior are the RD-M1 versions. This is why no RD-M1 Apply finding (F001, F004, F016, F017, F023, F024, F030, F031, F033, F034, F035) is FIXED. S6 did not re-open the verdicts of the RD-M2 independent review or the R1 "READY FOR INDEPENDENT CORRECTION REVIEW" status.

## 6. Frontend wording on F002 (S6 Table C)

| Item | Where today | What it says | Does Apply draw it? |
|---|---|---|---|
| Count card for review-sourced and coverage-sourced `proposed` changes | `RP:246` `["Placed, to approve", ofSection.filter((c) => c.status === "proposed").length]` (same string as the old `ProjectRedesignPage.tsx:292`) | "Placed, to approve" | Review-sourced `proposed` with verdict `ok`, `check` or none: yes (`S:695-701`). Coverage-added and interface `proposed`: no. Orchestrator `reject`: no |
| Per-change chip | `RP:487-489` shown only when `(c.source === "interface" \|\| c.source === "coverage") && c.status === "proposed"` | "drawn once approved" | Review-sourced `proposed` changes carry no such note and are drawn |
| Reject note | `RP:498` | "Orchestrator: ... left off the drawing unless you approve it." | Consistent with `S:699-700` |
| Output step counts | `RP:157` `ready = all.filter((c) => c.drawn).length`; `RP:393-396` | "{ready} change(s) to make", "N module or coverage detector(s) not approved yet (left off)", "N rejected by the orchestrator (left off unless approved)" | The "to make" count includes proposed review changes; the page never says so |
| Header text | `RP:3-13`; `ProjectDrawingPrepPage.tsx:7-9` | "the engineer approves" | Implies approval gates drawing; not true for review-sourced proposed changes |
| Archive wording | `RP:390-391` | "filed in the project folder ({data.folder})" | Confirmed by `S:1509-1517` |
| Approve-all button | `RP:292` (and its Skip twin) | approves or skips the `proposed` changes shown | Approved changes are drawn |

S6 verdict on the F002 wording claim: still true. The page calls proposed review changes "Placed, to approve" (the RD-M1 label), and only interface and coverage changes carry "drawn once approved". The truth is narrower than RD-M1 recorded because orchestrator-rejected changes are now excluded and described as such. A `check` verdict is shown as "Needs a look" but is drawn.

## 7. New observations relevant to M5 (S6)

These are not RD-M1 findings. S7 records them as candidate findings C01 to C03 (UNREVIEWED); S6 says N1 to N3 are the same points.

- **N1.** The preparation gate is stored and never enforced at Apply. `PR.gate` is called at `S:1246` and written to `row.run`; `apply()` (`S:1479-1523`) and `_drawn` do not read `row.run`, and `R:103-107` `start_apply` has no gate check. S6: "Confirms the roadmap statement."
- **N2.** The agents-off path (`prep_ai_enabled=False`, `ai_enabled=False`, the shipped default) places every change at the review's point as `confidence: "low"` and, for REMOVE and REPLACE, erases the first candidate if no candidate name matches (`PR:117-130`). With `_drawn` (F002) those are drawn while `proposed`, and no orchestrator exists to reject. The Plan's gate then reads "not reviewed by the orchestrator" but is not enforced.
- **N3.** `to_cad` and `_drawn` have no reference to `check.verdict == "check"`, so changes the orchestrator asked the engineer to look at are drawn unless rejected.

## 8. Mapping decisions recorded

**(a) Coordination findings F008 to F012.** The RD-M1 CSV recommended "RD-M4 coordination (proposed)" for these five. In the unified roadmap RD-M4 is M12 (Multi-Stage AI & Visual Review) and the coordination scope sits in M8 (Deterministic Geometry, Placement & Coordination). Orchestrator decision: M8 owns F008 to F012; M12 owns only the rendered visual check of the instances (F009, F010, F011). The CSV column `owner_milestone` therefore reads M8 for all five, and each note says so. S6 had listed F008 to F010 as "M8 / M12" and F011 and F012 as M8 only; the decision settles the difference.

**(b) RD-M1 milestone names to unified milestones**, per the roadmap's historical cross-reference (appendix, `docs/UNIFIED_MASTER_ROADMAP.md`, section 12):

| RD-M1 recommended_milestone text | Unified milestone | Source |
|---|---|---|
| RD-M2 | M5 Safe Apply & AutoCAD Block Library | roadmap appendix |
| RD-M3 | M8 Deterministic Geometry, Placement & Coordination | roadmap appendix |
| RD-M4 | M12 Multi-Stage AI & Visual Review (but see decision (a) for F008 to F012) | roadmap appendix |
| RD-M5 | M13 Real-Project Accuracy Validation & Release | roadmap appendix |
| "RD-M6 workflow" (F018, F019, F020, F025, F032) | M7, M10, M18 as in the CSV: F018 M18 + M7; F019 M10; F020 M7 + M18; F025 M7 + M10; F032 M5 + M7 + M10 | orchestrator decision; the roadmap appendix has no RD-M6 row |
| "AI-validation milestone" (F013, F014, F028; also F003 and F029 in part) | M12 | orchestrator reading; S6 owners |
| "later engineering-rules milestone" (F027) | M8 | S6 Table A owner |

## 9. Limitations

- **Static reading.** S6 and S7 read source and ran nothing. S6 states "No test was executed" and that test coverage "is by reading the test source". The scribe re-verified no code.
- **Tests pin current behavior.** The 116 passing tests show the code does what the tests assert. `evidence/TEST-RESULTS.md` says the added tests "were not mapped to those findings" and that the run is "not acceptance". A passing test for F002 pins the defect (S7 section 7, unknown 1).
- **No model, AutoCAD, database or Golden drawing.** The test run used `AI_ENABLED=false`, stubbed models and synthetic fixtures. No test exercises `apply()` or the Apply job (S7 section 1) or a real DXF, plot, wall index or the library DWGs (S7 section 6).
- **HEAD drift across the evidence.** S6 was taken at 4bab8d2. S7 started at 4bab8d2 and ended at f828ca1. `evidence/TEST-RESULTS.md` ran at 4bab8d2, and records that HEAD had moved to c1f962a afterwards and that the runner did not check whether c1f962a changed `backend/`. This file is written at 457c815. The orchestrator states that code under `backend/` and `frontend/` is identical to 771001e, and S6 and S7 recorded the same equality at 4bab8d2 and f828ca1, so the code under the tests is expected to be the code at 457c815. The scribe did not compare the trees.
- **Test counts that disagree.** S6 header says `test_drawing_prep.py` has "25 test functions on the preparation". `evidence/TEST-RESULTS.md` records 14 passed in that file, and S7 counts 14 (62 functions across five files). The scribe counted the `def test_` lines in the file: 14. This document uses 14. The S6 figure is unexplained.
- **Cited tests that were not run.** S6 cites `test_fa_evidence.py::test_C4_kept_interface_changes_are_restored_byte_for_byte` (F001, F032) and `test_sync_worker.py::test_a_job_left_running_by_a_dead_worker_is_recovered` (F017). Their files were not among the seven files ep-test-runner ran, so no pass result is recorded for them. They are marked in `tests_now`.
- **Truncated test name.** S6 writes the F002 test as `test_interface_modules_are_...`. The CSV gives the full name, matched by the scribe to the single test of that prefix cited for F001 in the same S6 table.
- **S6 short names.** S6 uses `jobs.py` and `runners.py` without a directory. The CSV expands them to `backend/app/services/jobs.py` and `backend/app/ifc/services/runners.py` (found by file name). S6 section 6 gives the E-numbers of the RD-M1 evidence; nothing was opened.
- **S7 cross-check.** S7 Table C-bis re-checked the findings independently and defers to S6. It tallies 29 open, 1 superseded in part, 2 not reproduced and 3 not re-read (F015, F020, F025). S6 classifies those three STILL OPEN, which gives 32. The two surveys agree on F026, F027 and F028 and on every finding they both read.
- **F027 is partial.** S6: no spacing check for non-detector devices (the sounder 12 m rule lives in the review, `review/service.py` `_sounder_spacing`), none for speakers and call points; `_measure_again` has no direct test; verified only on synthetic walls; depends on F005. S6: "A reviewer may prefer to keep it open for the non-detector rules."
- **Engineering rules.** The radius 6.3 m, the tolerance, the wall clearance and the other limits in the new code are set "by the engineers, 6 October 2026" with no standard cited in code (S7 section 7, unknown 5). They were not assessed against NFPA 72, the UAE Fire Code or a project specification.
- **Unknowns that need the owner's inputs** are listed finding by finding in S6 section 6 and reproduced, with the RD-M1 evidence file that pins each input, in `M2R-GOLDEN-STATUS.md`, section 6.
- **Unreviewed.** All 35 findings keep the RD-M1 status "UNREVIEWED - awaiting independent RD-M1 review". This file does not review them and does not grant any later milestone.
