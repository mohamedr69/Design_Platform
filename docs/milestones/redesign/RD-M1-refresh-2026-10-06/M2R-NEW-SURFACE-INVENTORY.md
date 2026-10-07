# M2 refresh — new redesign surface since RD-M1

Date: 2026-10-06
Repository HEAD: `457c8159c7c587a36e40f0ba2af711a55cc3f00a` (457c815). The code under `backend/` and `frontend/` at this HEAD is identical to commit 771001e.
Package: unified milestone M2 (Baseline and Error Inventory, refresh), folder `docs/milestones/redesign/RD-M1-refresh-2026-10-06/`. Companion files: `M2R-NEW-SURFACE-INVENTORY.csv` (the 22 candidate findings in RD-M1's 24-column schema) and `M2R-TEST-COVERAGE-MAP.md`. The classification of RD-M1's own 35 findings is in `M2R-FINDINGS-DELTA`, which is built on survey S6.

## Snapshot statement

This document is a static reading of source. Nothing in it was run: no test, server, database, model, AutoCAD or browser was used to produce the statements about code, and every cause status in the CSV is `CONFIRMED (code)`, meaning read from source. It is a transcription and organisation of survey S7 (`evidence/surveys/S7-new-surface.md`, ep-surveyor, 2026-10-06) with S7's own section and line references kept. S7 measured the repository at HEAD 4bab8d2 and re-checked at f828ca1; it records that `git diff --stat 771001e HEAD -- backend frontend` was empty at 4bab8d2 and that `git diff --stat 4bab8d2 HEAD -- backend frontend` was empty at f828ca1, so its code statements hold at both. That this milestone's HEAD (457c815) carries the same code as 771001e is given by the caller of this document; the scribe did not run the diff. The scribe did not re-verify any file or line.

S7's method is a comparison against commit **b5c2222** (2026-10-04 13:41, "Baseline: snapshot of the live working tree ... before FI-P1"). Its blobs match RD-M1's `BASELINE-MANIFEST.json` hash for 29 of the 35 non-DWG manifest code files, so for those files "what changed since RD-M1" is an exact `git diff b5c2222 HEAD`. Six manifest files have no matching blob in history (`core/config.py`, `interfaces/export.py`, `interfaces/pdf.py`, `interfaces/service.py`, `interfaces/visual.py`, `tests/test_fa_interfaces.py`); their deltas are measured against the nearest b5c2222 blob and are lower bounds. Separately, the manifest was taken on Windows (CRLF) and this checkout is LF: seven files differ from the manifest hash only by line endings (converting LF to CRLF reproduces the manifest hash), and S7 treats them as unchanged. Those seven are listed as "same content (line endings only)" in section 1; S7 shows their baseline blob as recoverable at b5c2222, so they are not additional to the 29. (S7 s0, Table A reading notes.)

No Golden Case evidence exists for the preparation, coverage, agents or gate code. GC-01 predates Drawings Preparation: the RD-M1 snapshot is at alembic `c5e7a9b1d3f5`, so it has no `project_redesign.run` column, no columns index, no coverage figure, no orchestrator verdict and no gate (S7 Table E, last paragraph). The `golden_case_id` of every CSV row therefore reads "none (code-confirmed; no Golden evidence exists for preparation, coverage or the gate)", and `source_sha256` reads "n/a (code finding)". The traceable hashes for this milestone are the code-file hashes in section 1 and section 4.

**Abbreviations (as in S7).** S01-S25 are RD-M1's 25 stages (`docs/milestones/redesign/RD-M1/CURRENT-PIPELINE.md`). N01-N18 are the new stages of section 2. C01-C22 are the candidate findings `RD-M1R-C01` to `RD-M1R-C22`. `rds` = `backend/app/redesign/service.py`; `rsv` = `backend/app/review/service.py`; `PR` and `prepare.py` = `backend/app/redesign/prepare.py`. Line numbers are HEAD. S7 cites the M1 refresh survey `docs/milestones/M1/refresh-2026-10-06/evidence/surveys/S2-drawings-review-redesign.md` as "S2" (tables A to E there) and S1 (interfaces) and S5 (GET-side work); those citations are kept.

**Headline numbers (S7 s1).** Table A: 54 files. Table B: of RD-M1's 25 stages 14 are unchanged and 11 changed, none removed; 18 new stages N01-N18. Table C: 22 candidate findings, Critical 1, High 8, Medium 10, Low 3. Table D: 62 tests in five files; 12 of 43 stages have no test in those files, 5 more are partly pinned; no test reaches `apply()`. Test run: 116 passed in seven files (`evidence/TEST-RESULTS.md`).

## 1. File delta against RD-M1's BASELINE-MANIFEST.json (S7 Table A)

"In manifest" = listed in `code_files` (or `redesign_library`) of `docs/milestones/redesign/RD-M1/BASELINE-MANIFEST.json` (RD-M1 T0 2026-10-03T19:46+0400). Hash = first 12 hex of sha256 (manifest value then; current file now). "Then" for lines is the b5c2222 blob where its hash equals the manifest hash, otherwise the nearest b5c2222 blob (the RD-M1 documents confirm two: `service.py` 1,449 lines and `ProjectRedesignPage.tsx` 584 lines). The note gives `git diff --numstat b5c2222 HEAD` as +added/-removed.

Counts over the 54 rows: same 14, same content with line endings only 7, CHANGED 9, REMOVED 1, NEW against the manifest 20, not in the manifest but present at b5c2222 3. S7's headline splits these as 48 requested files (13 same, 7 line endings, 9 changed, 1 removed, 15 new, 3 not in manifest) plus 6 adjacent files (by subtraction 1 same and 5 new). Files changed or new in the sense of this milestone: 9 changed + 20 new + 1 removed = 30, plus the 3 files RD-M1 never compared.

| File | In manifest | Hash then | Hash now | Result | Lines then / now | Note (b5c2222 to HEAD) |
|---|---|---|---|---|---|---|
| `backend/app/redesign/__init__.py` | yes | 2250f011d362 | 2250f011d362 | same | 3 / 3 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/agents.py` | no | - | e67944545f76 | NEW vs manifest | - / 185 | added after b5c2222 |
| `backend/app/redesign/ai.py` | yes | be5b8f28cefe | be5b8f28cefe | same | 81 / 81 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/cad.py` | yes | 031e760a7f7c | 031e760a7f7c | same | 176 / 176 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/coverage.py` | no | - | 8e7d122ddaf8 | NEW vs manifest | - / 414 | added after b5c2222 |
| `backend/app/redesign/library/CR.dwg` | yes | d0b4cd2244d4 | d0b4cd2244d4 | same | 254 / 254 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/library/CT1.dwg` | yes | f43361eab514 | f43361eab514 | same | 243 / 243 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/library/CT2.dwg` | yes | 7afd3a163ec4 | 7afd3a163ec4 | same | 247 / 247 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/library/modules.json` | yes | 3dddf8e7a817 | 27acf22d8491 | same content (line endings only) | 38 / 38 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/markup.py` | no | - | 087997d44886 | NEW vs manifest | - / 80 | added after b5c2222 |
| `backend/app/redesign/prepare.py` | no | - | 31bcab786877 | NEW vs manifest | - / 781 | added after b5c2222 |
| `backend/app/redesign/service.py` | yes | 69fa173ab549 | 45eed814f832 | CHANGED | 1,449 / 1,569 | b5c2222 to HEAD: +176/-56; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/walls.py` | yes | 6433e5703d5c | 6433e5703d5c | same | 197 / 197 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/ai.py` | yes | 6e16c49d7c55 | 7b17f4fcea9b | same content (line endings only) | 253 / 253 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/fls.py` | yes | 8ea424b04ef3 | 8ea424b04ef3 | same | 78 / 78 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/geometry.py` | yes | df696208fc9c | df696208fc9c | same | 130 / 130 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/markup.py` | yes | 2ccb2d70a198 | aec489c57c8c | CHANGED | 157 / 158 | b5c2222 to HEAD: +3/-2; baseline blob recoverable at b5c2222 |
| `backend/app/review/pages.py` | yes | 5b9b9e7c7f51 | f980d6cf0f75 | same content (line endings only) | 171 / 171 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/render.py` | yes | dc676dfd9f85 | c64112d1d1a0 | same content (line endings only) | 96 / 96 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/rulings.py` | yes | 7fc8ef3a33c2 | 7fc8ef3a33c2 | same | 100 / 100 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/scoped.py` | no | - | 227001d23eda | NEW vs manifest | - / 445 | added after b5c2222 |
| `backend/app/review/service.py` | yes | 30ca4d327eb1 | d5bc9597216f | CHANGED | 753 / 1,059 | b5c2222 to HEAD: +377/-71; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/__init__.py` | yes | ebefb04dd375 | ebefb04dd375 | same | 3 / 3 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/cases_pdf.py` | no | - | 12ab9bd5ecd5 | NEW vs manifest | - / 236 | added after b5c2222 |
| `backend/app/interfaces/detect.py` | yes | 88a7a07df5dc | b200c828f2c0 | same content (line endings only) | 232 / 232 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/evidence.py` | no | - | 22ba47a88dab | NEW vs manifest | - / 332 | added after b5c2222 |
| `backend/app/interfaces/export.py` | yes | a8847d6171a3 | 2233ee34ebf4 | CHANGED | 236 / 277 | b5c2222 to HEAD: +57/-16 |
| `backend/app/interfaces/findings.py` | no | - | 755836d32597 | NEW vs manifest | - / 792 | added after b5c2222 |
| `backend/app/interfaces/geometry.py` | no | - | 53697c4fdb44 | NEW vs manifest | - / 388 | added after b5c2222 |
| `backend/app/interfaces/matrix.py` | yes | e6dcd92faa4b | eec34a66f27e | same content (line endings only) | 158 / 158 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/pdf.py` | yes | bb859583b408 | 8b05f99d4f73 | CHANGED | 274 / 285 | b5c2222 to HEAD: +20/-9 |
| `backend/app/interfaces/render.py` | no | - | 33618cca61f2 | NEW vs manifest | - / 391 | added after b5c2222 |
| `backend/app/interfaces/scan.py` | yes | c374dfda628b | c02b0bc0ac6c | CHANGED | 122 / 162 | b5c2222 to HEAD: +44/-4; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/schedules.py` | yes | acc9c1653de1 | acc9c1653de1 | same | 159 / 159 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/service.py` | yes | 1047d210cdb9 | d07bc80d50f2 | CHANGED | 1,082 / 2,150 | b5c2222 to HEAD: +1319/-251 |
| `backend/app/interfaces/visual.py` | yes | eca4bda4eef1 | ba23a58fb769 | CHANGED | 360 / 373 | b5c2222 to HEAD: +200/-187 |
| `backend/app/interfaces/workflow.py` | no | - | 1728efd52215 | NEW vs manifest | - / 1,025 | added after b5c2222 |
| `backend/app/routers/redesign.py` | yes | a7dfa7a7fce9 | 06f6793e7c64 | CHANGED | 183 / 198 | b5c2222 to HEAD: +15/-0; baseline blob recoverable at b5c2222 |
| `backend/app/routers/drawing_review.py` | no | - | f5a21843ce58 | not in manifest (existed at b5c2222) | 300 / 304 | b5c2222 to HEAD: +15/-11 |
| `backend/tests/test_redesign.py` | yes | 60e0482c7a82 | 60e0482c7a82 | same | 316 / 316 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/tests/test_drawing_prep.py` | no | - | 75759a296377 | NEW vs manifest | - / 453 | added after b5c2222 |
| `backend/tests/test_drawing_review.py` | yes | 2eaaa6e899b1 | 616b70f2f9e4 | same content (line endings only) | 434 / 434 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/tests/test_scoped_drawing_review.py` | no | - | 53fe25e1c4da | NEW vs manifest | - / 556 | added after b5c2222 |
| `backend/tests/test_drawing_review_outcome.py` | no | - | f6dc6e5347f7 | NEW vs manifest | - / 314 | added after b5c2222 |
| `frontend/src/pages/ProjectDrawingPrepPage.tsx` | no | - | b80891673b52 | NEW vs manifest | - / 143 | added after b5c2222 |
| `frontend/src/pages/ProjectRedesignPage.tsx` | yes | d62938c60b74 | - | REMOVED | 584 / - | deleted after b5c2222; baseline blob recoverable at b5c2222 |
| `frontend/src/pages/ProjectDrawingReviewPage.tsx` | no | - | 375f38bfaba1 | not in manifest (existed at b5c2222) | 773 / 848 | b5c2222 to HEAD: +94/-19 |
| `frontend/src/pages/ProjectDrawingsPage.tsx` | no | - | 0f8301316e75 | not in manifest (existed at b5c2222) | 249 / 249 | unchanged since b5c2222 |
| `frontend/src/components/prep/AgentRunPanel.tsx` | no | - | 1921006f0571 | NEW vs manifest | - / 270 | added after b5c2222 |
| `frontend/src/components/prep/RedesignPanel.tsx` | no | - | 9bf5c2a874aa | NEW vs manifest | - / 632 | added after b5c2222 |
| `frontend/src/components/prep/types.ts` | no | - | 60d4cf3eb506 | NEW vs manifest | - / 170 | added after b5c2222 |
| `backend/scripts/scoped_drawing_review.py` | no | - | c6f44d8ca7c1 | NEW vs manifest | - / 85 | added after b5c2222 |
| `backend/alembic/versions/e6a8c0b2d4f6_drawing_prep_run.py` | no | - | a0247dedab2d | NEW vs manifest | - / 28 | added after b5c2222 |
| `backend/alembic/versions/c5e7a9b1d3f5_drawing_redesign.py` | yes | 9d7f175a831a | 9d7f175a831a | same | 48 / 48 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |

Reading notes (S7 Table A):

- Unchanged by hash, and therefore by behaviour: `redesign/{ai,cad,walls}.py`, the three library DWGs, `review/{fls,geometry,rulings}.py`, `interfaces/{__init__,schedules}.py`, `test_redesign.py`. In particular `cad.py` (stages S20-S23), `walls.py` (S08), `ai.py` (prompt `drawing-redesign-2026-10-02.4`, S12/S13 parser) and `rulings.py` are exactly what RD-M1 froze. Prompt `drawing-review-2026-10-01.3` in `review/ai.py` is unchanged (line endings only).
- Changed `redesign/service.py` +176/-56 (1,449 to 1,569 lines); `review/service.py` +377/-71 (753 to 1,059); `routers/redesign.py` +15/-0; `review/markup.py` +3/-2 (a `footer` parameter). The hunks are read in section 2.
- `interfaces/service.py` grew from 1,082 (b5c2222) to 2,150 lines (+1,319/-251); the RD-M1 manifest copy was 55,493 B, b5c2222 58,153 B, HEAD 122,011 B. New modules `cases_pdf`, `evidence`, `findings`, `geometry`, `render`, `workflow` belong to FI-P1 and to S1; only the Redesign-facing contract is read here (S09, S10, N12).
- Adjacent files changed since b5c2222 that the pipeline calls (diffs read by S7, not in the manifest set above): `ai/provider.py` (+449: `get_prep_provider`, `get_review_provider`, `prep_ai_on`), `compliance/assist.py` (+50: `exact_model`, `accept`, `fresh`, `NULL_MODEL`), `core/config.py` (+160: `prep_*`, `drawing_review_*` switches), `ifc/services/runners.py` (+59: `keep_answered`, `ReviewIncomplete` mapping, interface run kinds; `_redesign` unchanged), `services/jobs.py` (+24: lanes, progress flush; `recover_stale` untouched), `ifc/dxf/convert.py` (+17: `DWG_CONVERT_PARALLEL` semaphore instead of a single lock), `models.py` (+162; `ProjectRedesign.run` at models.py:697, migration `e6a8c0b2d4f6`).
- Missing from the manifest and never compared by RD-M1: `ProjectDrawingReviewPage.tsx` (773 to 848 lines, +94/-19), `routers/drawing_review.py` (+15/-11), `ProjectDrawingsPage.tsx` (unchanged).
- The frontend page RD-M1 audited (`ProjectRedesignPage.tsx`, 584 lines, hash d62938c60b74 = the b5c2222 blob) no longer exists. Its role is split into `ProjectDrawingPrepPage.tsx` (143 lines), `components/prep/RedesignPanel.tsx` (632), `AgentRunPanel.tsx` (270) and `types.ts` (170).
- RD-M2 is not in this tree. `docs/milestones/redesign/RD-M2/` and `RD-M2-review-correction-r1/` describe a candidate (approved-only drawn set, fail-closed script, portable library, `verify.py`, `test_redesign_apply.py`); none of it is present: no `verify.py`, no `test_redesign_apply.py`, `cad.py` is byte-identical to RD-M1 (031e760a7f7c), and `_drawn` still draws proposed review changes (S7 s0).

## 2. Pipeline stage delta (S7 Table B)

### 2.1 RD-M1's 25 stages at HEAD (S7 B1)

"Changed" is read from `git diff b5c2222 HEAD`; b5c2222's redesign and review blobs are hash-identical to the RD-M1 manifest. Stage names and numbers are RD-M1's. Result: 14 unchanged, 11 changed, 0 removed. Stages marked changed: S01 (minor), S02, S06, S09 (large), S10, S12, S14, S15, S16, S17, S18. S05 is unchanged in code but its caller changed, and S25 is unchanged for Redesign; both are counted unchanged.

| # | RD-M1 stage | Mark | What changed, or why unchanged (file:line at HEAD) |
|---|---|---|---|
| S01 | Drawing registration | changed (minor) | ifc/dxf/convert.py: the one-at-a-time DWG conversion lock became a `DWG_CONVERT_PARALLEL` semaphore (+17/-2). Registration code itself is outside the diffed set; S1 rows IFC.* own it. |
| S02 | Drawing/source selection | changed | routers/redesign.py:59-60 adds `review_state = review_service.outcome(review)[0]` to the drawings list; page picks the first drawing with `review_state == "done"` (ProjectDrawingPrepPage.tsx:46-47). `_drawing` (routers/redesign.py:35-39) still has no `deleted_at` check, unlike drawing_review.py:36-40 (S2 s7.2 #9). |
| S03 | Source hashing | unchanged | review/render.py identical modulo line endings (`_sha` :42-47); plan check rds:1171-1173 and Apply check rds:1492-1493 are the same logic. |
| S04 | CAD/PDF/IFC extraction (plot) | unchanged | render.py identical modulo line endings (plot script :79-82, 30-minute timeout :19). FLS drawings are plotted through the same `render_file` inside `plan_job` (rsv:119-142, unchanged hunk). |
| S05 | Sheet/floor detection; plot-model tie | unchanged (code), caller changed | geometry.py, pages.py identical (scale+offset only, FIT_VERSION 1 geometry.py:23). `_fit` is called after `plan_job` in `run` (rsv:193) and in `build` (rsv:595). |
| S06 | Room and geometry discovery (review windows) | changed | rsv +377/-71. Windows can be `incomplete` and are merged room by room (`rooms_to_ask` rsv:331-337, merge rsv:499-523); `outcome()` (rsv:400-435); `ReviewIncomplete`, `blocked`/`failed` keep the previous answers (rsv:181-190, 248-256); `keep_answered` (rsv:300); every look sends `effort` and `exact_model=True`, the disabled provider's placeholder is refused (rsv:464-470, 477-483, 494-499); `get_review_provider` (rsv:180); decisions kept with their proposal (rsv:693-706, 765-832); plan/FLS pass findings merged (rsv:340-361). Prompt text unchanged: `PROMPT_VERSION = "drawing-review-2026-10-01.3"` (review/ai.py:33), per-sheet version `PROMPT_VERSION+<rulings sha1[:10]>` (rsv:175-176). |
| S07 | Existing symbol discovery | unchanged | `_occurrences` (rds:97-108), `_symbols`, `_top_level` not in the diff. |
| S08 | Wall extraction and caching | unchanged | walls.py identical (raw-layer deny-list NOT_WALLS :25-26, VERSION 1 :27); `_walls` rds:178-192 unchanged. A second index now sits beside it (N03). |
| S09 | Interface schedule ingestion | changed (large) | interfaces/service.py 1,082 to 2,150 lines; FI-P1 evidence currency and published snapshot (`view_state`, `primary`, `view_reasons`: interfaces/service.py:797-843), scan.py +44/-4, new evidence/geometry/workflow/findings/render/cases_pdf (S1). For Redesign the contract that moved: a row's `anchor` is now the drawn equipment symbol's centre (`equipment_anchor`), `None` for a label-only item (interfaces/service.py:1440); in RD-M1 it was the label's own point. |
| S10 | Device/module identification | changed | `_interface_changes` takes the verified `built` view and stamps `"verified": True` (rds:525-577); modules are made only from a verified schedule (rds:503-510, 1199-1209, 646-652). Still resolves the trade drawing's `anchor` as a point on the FA drawing (rds:548-552, comment rds:381-385) and still stores an absolute library path (`.resolve().as_posix()` rds:435). |
| S11 | AI input construction | unchanged | `_prepare` and `_picture(doc, change, 1400)` (rds:1124) have no overlay on the model's picture; `_picture` gained an optional overlay used only by the GET image (S17). Symbol list still not stored. |
| S12 | AI placement proposal | changed | provider `get_prep_provider()` (rds:1119) instead of `get_provider()`; `model=prep_model, effort=prep_effort, exact_model=True` (rds:1133-1135) instead of `drawing_review_model`; pool `prep_agent_parallel` (default 4) instead of `drawing_review_parallel` (2) (prepare.py:156); driven by `PR.place` (N02); with prep AI off the call is skipped and the platform places every pending change at the review's point (prepare.py:144-154) where RD-M1 would have failed each change. Prompt and parser unchanged (ai.py identical): `drawing-redesign-2026-10-02.4`. |
| S13 | Deterministic placement conversion | unchanged | `_place`, `_place_module`, `read_answer` not in the diff. New callers: `PR.place`, `PR._set`. |
| S14 | Coordination | changed | `coordinate(..., columns)`: a candidate spot within `GAP_M` of a column is refused (rds:976-977). Still no report of an unresolved clash: the loop ends `fixed[...].append(c)` for any change it could not clear (rds:1108) - RD-M1-F012 stands. Wrapped by `PR.coordinate` (N06/N07). |
| S15 | Manual engineer changes | changed | `adjust` passes columns (rds:1311-1312) and re-measures coverage for detectors (rds:1317-1318 -> N08); `add_interfaces` refuses an unverified schedule (rds:649-653). Still no actor or time on a decision (RD-M1-F018 stands: signature has no user). |
| S16 | Plan persistence | changed | `plan()` is now four stages placement / coordination / orchestrator / gate (rds:1229-1246); keeps a change whose finding the review no longer has (rds:1188-1194) and the coverage detectors the engineer settled (rds:1212-1215); writes `row.run` (rds:1217-1249); sets `row.status = "planned"` whatever the gate says (rds:1250). Still rewrites the whole row after every answer, no concurrency control (prepare.py:193-194; PATCH routes do not check `row.status == "planning"`, routers/redesign.py:120-144) - RD-M1-F032 stands and its window is now longer (placement + coordination + orchestrator). |
| S17 | Preview rendering | changed | `image()` adds columns and the coverage circle as an overlay and reads the column pickle on a GET (`PR.columns(..., build=False)`, rds:1342-1364). |
| S18 | Approval/rejection state (view, `_drawn`) | changed | `_drawn` (rds:695-701): coverage-added detectors need approval; a proposed review change is dropped from the drawn set only if the orchestrator said `reject`; any other proposed review change is still drawn. `view` adds `run` and `agents_on` (rds:1564) and still calls `review.build` and commits (rds:1541-1545). |
| S19 | Apply job creation | unchanged | `_start` (routers/redesign.py:74-93) and `start_apply` (:103-107) not in the diff; no gate, plan-state or review-state check (N10). |
| S20 | CAD script generation | unchanged | cad.py identical; `to_cad` (rds:1400-1419) unchanged. `apply()` still calls `refresh()` first (rds:1495), which now also re-coordinates against columns (rds:1440-1443, 1473). Its input rule `_drawn` changed upstream (S18). |
| S21 | Block/library dependency loading | unchanged | cad.py identical; stored absolute library path (rds:435) - RD-M1-F001 stands. |
| S22 | AutoCAD execution | unchanged | cad.py identical (timeout, no cancellation). |
| S23 | Output verification | unchanged | cad.py identical (copy exists and mtime changed). |
| S24 | Output registration | unchanged | rds:1502-1521: minute-resolution name (:1502), copy into `<project folder>/03- Drawings/Redesign` (:1509-1519), absolute `output_path` (:1520) - F016/F031/F033 stand. |
| S25 | Error handling and retry | unchanged for Redesign | `_redesign` runner not in the runners diff; jobs.py diff is progress flushing and lane lists. (The review runner now maps `ReviewIncomplete` to `ReadError`, runners.py: `isinstance(exc, (RenderError, review.ReviewIncomplete))`.) |

### 2.2 New stages N01-N18 (S7 B2)

"Run by" says what executes the stage: the plan job (IFC worker), an explicit API request, a GET, the Apply job, or an explicit CLI. "Prompt / version" is the model task and version constant where the stage calls a model.

| # | New stage | file:line (HEAD) | Run by | Reads | Writes | Model prompt / version constant | Gate / note |
|---|---|---|---|---|---|---|---|
| N01 | Preparation switch, provider, run record | ai/provider.py:920-941 `prep_ai_on`,`get_prep_provider`; prepare.py:776-781 `started_run`; rds:1217-1218, 1564; models.py:697; migration e6a8c0b2d4f6 | plan job writes; GET /redesign/{did} reads | settings AI_ENABLED, PREP_AI_ENABLED, prep_model, prep_orchestrator_model, prep_effort, prep_agent_parallel 4, prep_max_concurrency 4, radii 6.3/6.3, prep_column_layers (config.py:425-436) | `project_redesign.run` JSON {started_at, ai, model, orchestrator_model, parallel, radius, stage, agents[], placement, coordination, review, gate} | none | `prep_ai_on()` is `ai_enabled or prep_ai_enabled` (provider.py:924): prep agents are on whenever AI_ENABLED is on, whatever PREP_AI_ENABLED says (config.py:421-424 says the opposite intent; S2 Table A row PREP.plan_run says "only when PREP_AI_ENABLED"). With AI_ENABLED on, `prep_max_concurrency` is not applied (provider.py:934-935). See C22. |
| N02 | Placement by agents, or by the platform alone | prepare.py:133-199 `place`; :117-130 `fallback_answer`; :109-114 `guess_symbol`; rds:1112-1142 `_ask` | plan job (thread pool) | pending changes, sheet geometry, symbol list, walls, review PDF crops (legend + 8 m crop at 1400 px), up to 15 numbered candidates | change.ai/confidence/note/insert/remove/status; `row.calls`; `row.changes` rewritten and committed after every answer (prepare.py:193-194); run.agents | `drawing-redesign-2026-10-02.4` (redesign/ai.py:12), task `fa_drawing_redesign`, model `prep_model`, effort, exact_model | With prep AI off no model is called and each change goes to the review's point with the nearest or name-matched symbol erased (C03). Result is `proposed` and `_drawn` (C02). |
| N03 | Column index | prepare.py:73-89 `columns`; coverage.py:118-175 `build_columns`,`load_columns`; VERSION 2 (coverage.py:31) | plan job builds (rds:1234); GET image (rds:1359), PATCH (rds:1312), POST interfaces (rds:667), Apply refresh (rds:1442, 1473) only load | DXF modelspace, recursive decompose (ezdxf); layers by regex; boundary lines by BOUND_LAYERS (coverage.py:48), trusted only if >= 200 m (coverage.py:50, 156) | `uploads/EP-n/redesign/columns-<did>-<sha16>-v2.pkl` (coverage.py:159-160), process dict `_COLUMNS` (prepare.py:64, never invalidated) | none | A read failure is logged and the plan goes on with no columns (prepare.py:84-86); the gate does not say so (C06). Layer read is the raw layer (coverage.py:136) (C10). |
| N04 | Room fill (rooms from boundary lines) | coverage.py:267-324 `room_at`,`_fill`; :235-260 `double_lines` | plan job; API process on every detector edit (via N08) | `columns.bounds` (named boundary layers) else double lines of the wall index (coverage.py:273-276) | none (in-memory masks; 0.2 m grid, 30 m reach, doorway closing 0.5/0.75/1.0 m, 1,500 m2 cap, 2 m2 floor) | none | A fill that leaks is an `open` room: coverage not measured. |
| N05 | Coverage measurement, best spots, room grouping | prepare.py:235-304 `rooms`,`propose`; coverage.py:330-414 `uncovered`,`measure`,`best_spots` | plan job | new detector changes (system detection or source coverage; add/replace; pending/proposed/approved), existing detector occurrences by name regex (prepare.py:59, 263-265), erased handles (prepare.py:498) | in-memory plan {moves, extra, before, after, issues} | none | Tolerance: covered when <= 1% or <= 0.5 m2 uncovered (coverage.py:41, 352); straight-line radius 6.3 m. C11-C14. |
| N06 | Coordination agent, one room at a time | prepare.py:383-414 `_ask_coordination`; :417-463 `_decide`; agents.py:25-68, 113-155 | plan job (thread pool) for rooms where the platform found an issue | crop of the review plot around the room with overlay (circles, columns, uncovered tint, N/S labels) + text | change.insert/seen via `_set`, change.coordination {by, moved_m, reason, refused}, run.agents, `row.calls` | `drawing-prep-coordination-2026-10-06.1` (agents.py:26), task `fa_prep_coordination`, model `prep_model`, exact_model, `accept=coordination_problem` | An agent point is checked against columns and room containment only (prepare.py:439-445) and the room's total coverage against the platform's (:455-462). |
| N07 | Platform coordination with columns; coverage-added detectors | prepare.py:491-598 `coordinate`; :466-488 `_extra_change`; :205-220 `_set`; rds:925-1109 (column test :976-977) | plan job; also API (PATCH rds:1311, POST interfaces rds:667) and Apply job (refresh rds:1440-1443, 1473) | all changes, walls, symbols, columns | new changes `cov:<sha1 of sheet index, x, y>[:12]` (source coverage, status proposed), insert positions, change.coordination/coverage | none | Coverage-added detectors are drawn only once approved (rds:699). Ids are position-derived: a changed spot is a new id. |
| N08 | Coverage re-measure after an engineer edit | prepare.py:601-623 `annotate_room`,`measure_again`; rds:1317-1318, 1324-1339 `_measure_again` | explicit PATCH in the API process | walls pickle, columns pickle, `resolved_drawing(..., with_occurrences=True)`, review sheets | change.coverage on the group's members | none | Does not touch `run.coordination`, `run.gate` (C07). Heavy numpy fill on the request path. |
| N09 | Orchestrator floor review | prepare.py:629-733 `review`,`_review_input`,`_ask_review`; agents.py:70-99, 158-185 | plan job, one call a floor | JSON of the floor's non-interface, non-skipped changes only (prepare.py:629-647, 679-680) - no image | change.check {verdict ok/check/reject, reason}; run.review {state, floors[]}; `row.calls` | `drawing-prep-orchestrator-2026-10-06.1` (agents.py:28), task `fa_prep_orchestrator`, model `prep_orchestrator_model`, exact_model, `accept=review_problem` | A `reject` removes a proposed review change from `_drawn` (rds:700); `check` and a missing verdict change nothing. C04, C05. |
| N10 | Preparation gate | prepare.py:739-773 `gate`; rds:1246, 1253 | plan job, once at the end | changes, coordination stats, orchestrator state, columns | `run.gate` {state ready/needs_engineer, reasons[]} | none | **Not enforced by Apply** (quotes below). Shown by AgentRunPanel.tsx:55-95 only. |
| N11 | Draftsman markup PDF | redesign/markup.py:27-80 `build`; rds:1367-1386 `draftsman_pdf`; routers/redesign.py:190-198; review/markup.py `footer` parameter | GET (renders per request) | `row.changes` filtered by `_drawn`, review sheets and plot PDF | none (a `state()` row may be flushed: S5) | none | Includes proposed, unapproved review changes (C02). Not covered by any test. |
| N12 | Interface verification gate and anchor contract | rds:503-522 `interfaces_verified`,`keep_interfaces`,`restore_kept`; rds:1199-1209 (plan), 646-652 (add_interfaces); interfaces/service.py:797-843, 1440 | plan job; explicit POST /redesign/{did}/interfaces | `I.build` (evidence listing, published snapshot: S1) | only the plan (generated or kept interface changes) | FI-P1 workflow has its own prompts (S1), none in this path | Verified at plan/add time; not re-checked at Apply (C08). Trade-drawing frame still assumed equal to the FA frame (C-bis F007). |
| N13 | Review outcome and resumable looks | rsv:145-284 `run`; 287-328 `plan_looks`; 331-337; 364-435 `outcome`; routers/drawing_review.py:68-92 | explicit POST -> job `fa_drawing_review`; `outcome` is a pure read in GET | plot PDF, sheets, rulings | ProjectDrawingReview.sheets/status/error/model/calls | `drawing-review-2026-10-01.3` + rulings hash (rsv:175-176), tasks fa_drawing_review_{window,sheet,fls}, model `drawing_review_model` | `row.status` becomes `done` even with failed/incomplete windows (rsv:259-263) (C09). |
| N14 | Review decisions kept to their proposal | rsv:693-706, 765-832; routers/drawing_review.py:104-156, 258-287 | explicit POST | findings (built) | `decisions` JSON {status, note, instruction, by, at, basis, via, history[]} | none | A decision whose proposal changed returns to `open` with `previous_decision` shown (rsv:693-706); Redesign is not told (C08). |
| N15 | Pass-finding merge | rsv:340-361 `_merge_passes` | GET build (derived) | findings | none | none | Merges a plan/FLS pass finding into the room finding of the same page/system/action (`also_seen`). |
| N16 | Rulings (company-wide) | review/rulings.py:1-100; rsv:175-176, 688, 719-723, 750-753; routers/drawing_review.py:149-151, 280-282, 290-304 | written by explicit POST decisions / bulk accept; read by every review job and every GET build; deleted by explicit DELETE | `review_rulings` rows of all projects | `review_rulings` | text appended to every review system prompt; version `sha1(text)[:10]` (rulings.py:90) | C15-C18. File identical to RD-M1 (never audited there: RD-M1 s7 "review stages mapped only as inputs"). |
| N17 | Scoped review run | review/scoped.py:1-445; scripts/scoped_drawing_review.py | explicit CLI in its own process; job row written already `running` (scoped.py:380-392) | DB, plot PDF (never plots: preflight scoped.py:98-100) | BackgroundJob, ProjectDrawingReview, a JSON report; global settings changed then restored (scoped.py:276-311) | review prompts, `fresh=True` (scoped.py:289-290), `Guard` enforces floor, call and turn limits (scoped.py:176-231) | Refuses if AI_ENABLED is on (scoped.py:84-85). C19. |
| N18 | Review/prep model route | ai/provider.py:951-966 `get_review_provider`; config.py:405-418; compliance/assist.py:248-340 (`exact_model`, `accept`, `fresh`, `NULL_MODEL`) | every review look and every prep look | settings | result cache keyed incl. effort, exact_model (assist.py:281-286) | all of the above | No `project_policy` check on the path (C15). |

## 3. Is the preparation gate enforced by Apply?

**No, by code reading (S7 B3).** The gate is computed once, at the end of the plan job, and stored:

```
rds:1246   run["gate"] = PR.gate(changes, run["coordination"], run["review"], cols)
rds:1250   row.status, row.finished_at = "planned", utc_now()
```

S7: "`grep -n gate` over backend/app/redesign, routers/redesign.py, ifc/services/runners.py and routers/drawing_review.py finds it only at prepare.py (definition, docstring), rds:1245-1253 (the line above and the plan's return value). Apply never reads `row.run`:"

```
rds:1484-1499 (apply)
    drawing = db.get(ProjectIfcDrawing, drawing_id)
    row = state(db, project, drawing_id)
    row.output_status, row.output_error = "making", None
    ...
    refresh(db, project, drawing, row)
    todo = [c for c in row.changes or [] if _drawn(c)]
    if not todo:
        raise RedesignError("No change is placed to make: plan the redesign, or approve the changes first.")
routers/redesign.py:103-107
    def start_apply(project_id, drawing_id, current_user = Depends(require_role(*CREATOR_ROLES)), db = Depends(get_db)):
        project = _get_project_or_404(db, project_id)
        return _start(db, project, _drawing(db, project, drawing_id), service.KIND_APPLY, current_user, "drawing")
rds:699-701 (what is drawn)
    proposed = (c["status"] == "proposed" and c.get("source") not in (INTERFACE, PR.COVERAGE)
                and (c.get("check") or {}).get("verdict") != "reject")
    return (c["status"] == "approved" or proposed) and bool(c.get("remove") or c.get("insert"))
```

S7 on the page: "The page does not enforce it either: the Make button is `disabled={disabled || ready === 0}` where `ready = all.filter((c) => c.drawn).length` (RedesignPanel.tsx:157, 403-404), the Devices step badge is a check mark whenever `redesign_status === "planned"` (ProjectDrawingPrepPage.tsx:70), and `run.gate` is only displayed (AgentRunPanel.tsx:55-95). No test applies a `needs_engineer` plan (no test reaches `apply()` at all)."

This is candidate finding RD-M1R-C01 (High) and, through `_drawn`, RD-M1R-C02 (Critical). The server-side `start_apply`, `_start` and `apply()` are unchanged in stage terms since RD-M1 (S19 unchanged, S7 B1). "Not enforced" is a reading of source; no Apply was started.

## 4. The 22 candidate findings (S7 Table C)

Scheme: RD-M1's categories A Source and extraction; B Device understanding; C Placement; D Coverage and engineering rules; E Coordination; F AI behaviour; G Workflow; H CAD Apply, plus **I. Data governance / scope** (new in S7: what data may reach a model or another project). Every row is `CONFIRMED (code)` and `UNREVIEWED`. Severity is S7's proposal on RD-M1's scale. "Owner" uses the roadmap's milestone names (M3 Ownership, Access and Memory Policy; M5 Safe Apply; M7 Central Processing; M8 Deterministic Geometry; M10 DB-driven tabs; M12 Multi-Stage AI and Visual Review). Where S7 gives a combined category such as "A/D" or "C/D" the CSV takes the first letter as primary and the second as secondary. No instance-level finding (a particular detector, room or sheet of GC-01) is asserted.

Counts: Critical 1 (C02), High 8 (C01, C03, C04, C08, C10, C15, C16, C17), Medium 10 (C05, C06, C07, C09, C11, C12, C13, C18, C19, C20), Low 3 (C14, C21, C22). Total 22. The CSV agrees with these counts and with S7's severity and owner for every row.

| ID | Severity | Category | Defect class | Stage | file:line (under backend/app/) | Deterministic | Existing test (S7) | Owner milestone |
|---|---|---|---|---|---|---|---|---|
| RD-M1R-C01 | High | G | Preparation gate stored, not enforced at Apply (server or page) | S19/S20, N10 | redesign/service.py:1246, 1484-1499; routers/redesign.py:104-107 | Yes | gate arithmetic only (test_drawing_prep.py:161); nothing reaches Apply | M5 |
| RD-M1R-C02 | Critical | G | Proposed, unapproved changes are drawn; with prep AI off the platform alone creates them (extends RD-M1-F002) | S18, N02, N09, N11 | redesign/service.py:699-701, 865-866; redesign/prepare.py:144-153 | Yes | PINNED as intended (test_redesign.py:213; test_drawing_prep.py:142) | M5 |
| RD-M1R-C03 | High | F | Agents-off fallback erases the nearest symbol whatever its name | N02 | redesign/prepare.py:121-125 | Yes | named case only (test_drawing_prep.py:149) | M5 / M8 |
| RD-M1R-C04 | High | F | Floor review is structured text, no rendered image: "ok" is not visual evidence | N09 | redesign/prepare.py:656-660; redesign/agents.py:74 | Yes | none asserts an image part (test_drawing_prep.py:215 reads text parts) | M12 |
| RD-M1R-C05 | Medium | F | An orchestrator verdict is not required per change; omission, `needs_engineer` and open questions do not reach the gate | N09, N10 | redesign/agents.py:158-171; redesign/prepare.py:713-715, 761-765 | Yes | none (fake answers every id) | M12 |
| RD-M1R-C06 | Medium | G | Gate omits conditions the run itself records (no columns index, big coordination moves, plot residual > 1 m, erase-by-hand) | N10 | redesign/prepare.py:84-86, 293-301, 749 | Yes | none | M5 / M8 |
| RD-M1R-C07 | Medium | G | Gate, run summary and orchestrator verdicts are snapshots; engineer edits and Apply's refresh do not recompute or invalidate them | N08, N10, S15, S20 | redesign/service.py:1265-1321, 1495, 1564 | Yes | none | M5 |
| RD-M1R-C08 | High | G | Stale plan: a reversed or changed review decision, or a no-longer-verified interface schedule, is not seen by Apply; a re-plan drops approvals asymmetrically | S16, S18, S20, N12, N14 | redesign/service.py:1179-1199, 1496; review/service.py:693-706 | Yes | none for reversal; keep-when-gone pinned (test_drawing_prep.py:416) | M5 / M7 |
| RD-M1R-C09 | Medium | G | A partly reviewed drawing (`status` done, `outcome` partial) is accepted by Redesign, server and page | S02, S16, N13 | review/service.py:259-263; redesign/service.py:87-88 | Yes | review side only (test_drawing_review_outcome.py:292) | M5 / M12 |
| RD-M1R-C10 | High | A/D | Room fill and coverage rest on the raw-layer wall/boundary index RD-M1 found untrustworthy | S08, N03-N05 | redesign/coverage.py:48, 136-137 | Yes | synthetic walls only | M8 |
| RD-M1R-C11 | Medium | A | Distances taken as metres in room fill, coverage, radius and library scale; real drawing units are read only at Apply | N03-N05, S10 | redesign/coverage.py:19, 330-342 | Yes | none (tests use 0.1 m per pt) | M8 |
| RD-M1R-C12 | Medium | D | Coverage is measured only in rooms that receive an added/replaced detector; REMOVE never triggers it; the page says "every room covered" | N05, N10 | redesign/prepare.py:96-99, 235-253 | Yes | none | M8 |
| RD-M1R-C13 | Medium | D | Existing detectors are counted by name regex (SMOKE, HEAT, SD, OS, HD...) and heat and smoke share one radius | N05 | redesign/prepare.py:59, 264 | Yes | none | M8 |
| RD-M1R-C14 | Low | D | The erased-handle set counts skipped, failed and unapproved removals as removed | N05, N08 | redesign/prepare.py:498, 620 | Yes | none | M8 |
| RD-M1R-C15 | High | I | `ai_policy` ("blocked") is consulted by no review, preparation, redesign or scoped-review AI path | N02, N06, N09, N13, N17 | review/service.py:438-527; redesign/prepare.py:383-414, 650-666 (absence of any project_policy reference) | Yes | none | M3 / M12 |
| RD-M1R-C16 | High | I | Review rulings are company-wide: other projects' text enters the prompt, auto-dismisses findings, is returned in the payload, can be deleted by anyone, and vanishes with a project | N16 | review/rulings.py:59-90; review/service.py:688, 719-723 | Yes | single-project test only (test_drawing_review.py:192) | M3 / M12 |
| RD-M1R-C17 | High | C/D | A "not needed" ruling is matched on room kind + system + action, not on the device, and so suppresses a different required device | N16, S06 | review/rulings.py:77, 96-99; review/service.py:719-723 | Yes | same-device case only | M12 |
| RD-M1R-C18 | Medium | I | Bulk accept writes a company-wide CONFIRMED ruling for every accepted finding, unreviewed | N16 | routers/drawing_review.py:278-282 | Yes | not asserted | M3 / M12 |
| RD-M1R-C19 | Medium | G | A continued or scoped review keeps old answers and relabels them with the current prompt+rulings version | N13, N17 | review/service.py:300, 311 | Yes | keep-and-ask-rest pinned (test_scoped_drawing_review.py:479), label not | M12 / M7 |
| RD-M1R-C20 | Medium | G | GET /redesign/{did} (polled by the page) runs the review build: geometry fit, row creation, commit (extends RD-M1-F019) | S18, S05 | redesign/service.py:1541-1545; review/service.py:593-596 | Yes | none | M10 |
| RD-M1R-C21 | Low | G | A preparation run cannot be reproduced from what it stores (orchestrator payload, coordination picture, answers) | N06, N09 | redesign/prepare.py:189-191, 723-725 | Yes | none | M12 / M7 |
| RD-M1R-C22 | Low | G | Prep agents cannot be switched off while AI_ENABLED is on; the gate names the wrong switch | N01, N10 | ai/provider.py:920-924; core/config.py:421-424 | Yes | none | M12 |

Owner milestones in the CSV are S7's, written with "(proposed)" as RD-M1 did. S7 names M3 for C15, C16 and C18 in addition to M5, M7, M8, M10 and M12.

### 4.1 Code identity of each finding

Each finding is traceable to the files below at the hashes S7 recorded (first 12 hex of sha256, S7 Table A). Files S7 did not list in Table A (adjacent files, `ai/provider.py`, `core/config.py`, `compliance/assist.py`, `services/project_deletion.py`, `ai/project_policy.py`) have no hash in S7; a reviewer taking the hash of those files at the review time should record it then.

| Finding | Files and hash now (first 12 hex) |
|---|---|
| RD-M1R-C01 | redesign/service.py `45eed814f832`; redesign/prepare.py `31bcab786877`; routers/redesign.py `06f6793e7c64`; fe:components/prep/RedesignPanel.tsx `9bf5c2a874aa`; fe:pages/ProjectDrawingPrepPage.tsx `b80891673b52`; fe:components/prep/AgentRunPanel.tsx `1921006f0571` |
| RD-M1R-C02 | redesign/service.py `45eed814f832`; redesign/prepare.py `31bcab786877`; redesign/markup.py `087997d44886`; fe:components/prep/RedesignPanel.tsx `9bf5c2a874aa` |
| RD-M1R-C03 | redesign/prepare.py `31bcab786877`; redesign/service.py `45eed814f832` |
| RD-M1R-C04 | redesign/prepare.py `31bcab786877`; redesign/agents.py `e67944545f76` |
| RD-M1R-C05 | redesign/agents.py `e67944545f76`; redesign/prepare.py `31bcab786877` |
| RD-M1R-C06 | redesign/prepare.py `31bcab786877`; redesign/service.py `45eed814f832` |
| RD-M1R-C07 | redesign/service.py `45eed814f832`; redesign/prepare.py `31bcab786877`; fe:components/prep/AgentRunPanel.tsx `1921006f0571` |
| RD-M1R-C08 | redesign/service.py `45eed814f832`; review/service.py `d5bc9597216f`; routers/drawing_review.py `f5a21843ce58` |
| RD-M1R-C09 | review/service.py `d5bc9597216f`; redesign/service.py `45eed814f832`; fe:components/prep/RedesignPanel.tsx `9bf5c2a874aa`; fe:pages/ProjectDrawingPrepPage.tsx `b80891673b52` |
| RD-M1R-C10 | redesign/coverage.py `8e7d122ddaf8`; redesign/walls.py `6433e5703d5c` |
| RD-M1R-C11 | redesign/coverage.py `8e7d122ddaf8`; redesign/prepare.py `31bcab786877`; redesign/service.py `45eed814f832` |
| RD-M1R-C12 | redesign/prepare.py `31bcab786877`; fe:pages/ProjectDrawingPrepPage.tsx `b80891673b52` |
| RD-M1R-C13 | redesign/prepare.py `31bcab786877`; core/config.py (not in Table A) |
| RD-M1R-C14 | redesign/prepare.py `31bcab786877` |
| RD-M1R-C15 | ai/project_policy.py (not in Table A); review/service.py `d5bc9597216f`; redesign/prepare.py `31bcab786877`; redesign/service.py `45eed814f832`; review/scoped.py `227001d23eda`; compliance/assist.py (not in Table A) |
| RD-M1R-C16 | review/rulings.py `7fc8ef3a33c2`; review/service.py `d5bc9597216f`; routers/drawing_review.py `f5a21843ce58`; services/project_deletion.py (not in Table A) |
| RD-M1R-C17 | review/rulings.py `7fc8ef3a33c2`; review/service.py `d5bc9597216f`; review/ai.py `7b17f4fcea9b` |
| RD-M1R-C18 | routers/drawing_review.py `f5a21843ce58`; review/rulings.py `7fc8ef3a33c2` |
| RD-M1R-C19 | review/service.py `d5bc9597216f`; review/scoped.py `227001d23eda` |
| RD-M1R-C20 | redesign/service.py `45eed814f832`; review/service.py `d5bc9597216f` |
| RD-M1R-C21 | redesign/prepare.py `31bcab786877` |
| RD-M1R-C22 | ai/provider.py (not in Table A); core/config.py (not in Table A); redesign/prepare.py `31bcab786877` |

### 4.2 The Critical and High findings, as S7 states them

Text below is S7's own C-detail paragraph for each finding, copied; "B3" in S7 refers to section 3 of this document. Order: the Critical finding, then the High findings by ID.

**RD-M1R-C02 - Unapproved changes drawn; the platform alone can create them** (G, Critical, extends RD-M1-F002). Stage S18, N02. Code: rds:699-701 (quote in section 3 of this document); prepare.py:144-153 `if not prep_ai_on(): stats["by"] = "platform"; for c in todo: answer = fallback_answer(c, symbols) ... R._place(c, sheets[c["page"]], symbols, answer, walls)`; `_place` ends `if change["status"] in ("pending", "failed"): change["status"] = "proposed"` (rds:865-866). In RD-M1 a plan with no usable model left each change `failed` (the call returned no data); now it leaves `proposed`, which `_drawn` draws. The orchestrator, which is the only control, is off in that mode (prepare.py:685-687 `state "off"`) and in any case only `reject` stops a proposed change (rds:700). The draftsman PDF (N11) lists them as changes "to be drawn", and the page's count card still calls them "Placed, to approve" (RedesignPanel.tsx:246; S6 Table C). Cause: CONFIRMED (code). Deterministic: yes. Tests: the behaviour is asserted as intended: `assert R._drawn({**placed, "status": "proposed"})` (test_redesign.py:213) and `assert R._drawn({**base, "status": "proposed"})` (test_drawing_prep.py:142), `assert R._drawn({**base, "status": "approved", "check": {"verdict": "reject", ...}})` (:146). Fixing it requires changing those assertions (RD-M2 did, in a candidate not integrated here). Owner: M5.

**RD-M1R-C01 - Gate stored, not enforced at Apply** (G, High). Stage S19/S20, N10. Code: rds:1246 `run["gate"] = PR.gate(...)`; rds:1496-1498 `todo = [c for c in row.changes or [] if _drawn(c)]` / `raise RedesignError("No change is placed to make: plan the redesign, or approve the changes first.")`; routers/redesign.py:104-107 `start_apply` creates the job with no state check; RedesignPanel.tsx:403 `disabled={disabled || ready === 0}`. Full quotes in section 3 of this document (S7 B3). Cause: CONFIRMED (code). Deterministic: yes. Tests: test_drawing_prep.py:161 (`test_the_gate_is_the_platforms_count`) and :328 (asserts `run["gate"]["state"] == "needs_engineer"`); no test posts Apply. Owner: M5 ("enforce gates at the server boundary").

**RD-M1R-C03 - Fallback REMOVE/REPLACE erases the nearest symbol of any kind** (F, High). Stage N02. Code prepare.py:121-125:

**RD-M1R-C04 - Floor review is text, not a picture** (F, High). Stage N09. Code prepare.py:656-660: `result = assist.call_task(session, AG.REVIEW_TASK, AG.REVIEW_SYSTEM, [TextPart("the floor's changes (data)", json.dumps(payload, default=str))], AG.REVIEW_SCHEMA, ...)`; the prompt says "You receive one floor's changes as JSON data" (agents.py:74). The payload is `_review_input` (prepare.py:629-647): ids, device names, confidences, `metres_from_review_point`, `on_wall`, `column_clear`, the platform's own `coordination` and `coverage`. No ImagePart, so `ok` cannot attest what the plan shows (a wall behind the device, a door swing, a symbol on a note); it can only restate the platform's numbers. The roadmap says the same (s3 Drawings, M12: "Structured-text review alone cannot prove visual placement"). Compare N06, which does see an image. Cause: CONFIRMED (code). Tests: FakeOpus builds its answer from `texts` only (test_drawing_prep.py:191-212); no assertion on parts. Owner: M12.

**RD-M1R-C08 - Stale plan after a decision reversal (and a schedule change)** (G, High). Stage S16, S18, S20, N12, N14. Apply draws whatever `row.changes` holds (rds:1496); neither `decide` nor `decide_many` touches the redesign row (no `redesign` reference in backend/app/review or routers/drawing_review.py); the view only reports `undecided` (rds:1544, 1558). So an accepted finding the engineer later dismisses or reopens, or whose proposal changed so its decision returned to `open` (rsv:693-706), is still drawn until the plan is run again. The re-plan is asymmetric: `accepted = [f for f in view["findings"] if f["decision"] == "accepted" ...]` (rds:1179) builds the list, and only changes whose finding is absent from the review are carried over (rds:1192-1194), so an engineer-approved change whose finding is present but no longer accepted is dropped, approval included, while one whose finding vanished is kept (that keep is pinned: test_drawing_prep.py:416). Interface modules: `interfaces_verified` is asked at plan and add time only (rds:1199, 649); an approved module stays drawn after the schedule stops being verified (S2 Table E row 10). Cause: CONFIRMED (code). Tests: none for reversal. Owner: M5 (stale approvals), M7.

**RD-M1R-C10 - Coverage on an untrusted index** (A/D, High). Stage S08, N03-N05. coverage.py:136-137 reads `entity.dxf.get("layer")` (raw) and tests BOUND_LAYERS (`WALL|DOOR|GLASS|GLAZ|SILL|WINDOW|WIN|CURTAIN|PARTITION|COLUMN|COLS?|S-COL`, :48); the fallback is `double_lines(walls.near(...))` over walls.py's raw-layer deny-list (identical to RD-M1). RD-M1 found raw layer `0` with effective layer `29-PARKING` admitted (F006), 4,351 invisible-flag segments (F005) and no containment model (F022); none of visibility, layer on/frozen/no-plot, viewport freeze or effective layer is read (roadmap s3: "New room coverage code cannot compensate for an untrusted wall index"). A room is only as real as the lines that close it, and the gate, the added detectors and the best spots all come from it. Not re-run here; instance effects on GC-01 are not asserted. Tests: synthetic `Walls` only (test_drawing_prep.py:21-34). Owner: M8.

**RD-M1R-C15 - ai_policy not consulted** (I, High). `project_policy.allowed/require` (app/ai/project_policy.py) is used by sheet_reader, verification, submittal_reader, extraction, sample_request and compliance; `grep -rn "ai_policy\|project_policy"` over backend/app/review, backend/app/redesign, routers/redesign.py, routers/drawing_review.py and ifc/services/runners.py returns nothing. Review looks (rsv:438-527) send plan crops and room names; placement, coordination and orchestrator send plan crops and JSON about the project (prepare.py:383-414, 650-666; rds:1112-1142); the scoped run does too. A project set to `blocked` ("its documents are not sent to an AI provider") still has them sent when a switch is on (S2 s7.2 #4; N18). Tests: no `ai_policy` in the five files. Owner: M3 (policy), M12 (call site).

**RD-M1R-C16 - Rulings are company-wide** (I, High). `listed(db)` has no project filter (rulings.py:59-60); `prompt(db)` puts up to 80 of them, with room names, notes and instructions, into every project's review prompt (rulings.py:71-90; rsv:175-176) and a new ruling changes the prompt version so every project's looks are asked again (rsv:176-177, 296-300); `build` uses `R.not_needed(db)` to set `decision = "dismissed", by_ruling = True` on another project's findings (rsv:688, 719-723), which then never reach Redesign (rds:1179); the page payload returns every ruling's room, instruction, note and `project_id` (rsv:750-753); `DELETE /drawing-review/rulings/{id}` checks neither project nor owner (drawing_review.py:290-304); project deletion removes the project's rulings (project_deletion.py:97), silently reopening other projects' by-ruling dismissals. (S2 s7.2 #5-#6 note the exposure; the consequence for what Redesign draws is added here.) RD-M1's DB snapshot already held 108 `review_rulings` rows across its 10 projects (E12 table_counts), of which at most 80 enter a prompt (rulings.py:25). Tests: one project (test_drawing_review.py:192-238). Owner: M3 (policy), M12.

**RD-M1R-C17 - Ruling key ignores the device** (C/D, High). The model sees rulings keyed `(room_key or room_type, system, action, device)` (rulings.py:77) but the automatic dismissal uses `(room_key, system, action)` only (rulings.py:96-99; rsv:719-723, for `kind in ("room", "spacing")`). The six systems are coarse (review/ai.py SYSTEMS): `speaker` covers ceiling speakers, wall speakers and sounder-flashers, and the company rules require a sounder-flasher in pump rooms (review/ai.py RULES). So "NOT NEEDED: ADD ceiling speaker in PUMP ROOM" settles "ADD sounder-flasher in PUMP ROOM" as dismissed by ruling on every floor and in every project; the only trace is the note "By ruling (<room>)". Tests: test_drawing_review.py:192 uses the same device on both floors. Owner: M12.

The 13 Medium and Low findings (C05, C06, C07, C09, C11, C12, C13, C14, C18, C19, C20, C21, C22) are in the CSV with the same evidence fields and in S7 C-detail; they are not repeated here.

## 5. Cross-check of RD-M1's findings in the changed code (S7 C-bis)

S7 re-checked RD-M1's 35 findings against the code at HEAD as an independent cross-check. "Open" there means still present by file identity (the code RD-M1 cited is in a file whose hash is unchanged) or by a line read at HEAD; nothing was run. **The classification of RD-M1's 35 findings (fixed, still open, superseded, not reproduced) is made in `M2R-FINDINGS-DELTA`, built on the S6 survey (`evidence/surveys/S6-findings-delta.md`), which is the authority; this section does not classify and defers to it wherever the two differ.** S7 reports S6's totals as FIXED 0, STILL OPEN 32, SUPERSEDED 1, NOT REPRODUCED 2 over all 35, and says none is fixed and that RD-M2's closures are not in this tree.

| RD-M1 finding | Status at HEAD (S7's reading) | Evidence (S7) |
|---|---|---|
| F001 absolute library path | OPEN | rds:435 `.resolve().as_posix()`; cad.py identical |
| F002 proposed review changes drawn | OPEN, altered | rds:699-701: now excludes an orchestrator `reject` and coverage detectors; see C02 |
| F003 low-confidence REMOVE accepted | OPEN | ai.py `read_answer` identical; new path C03 |
| F004 invalid script on error; F023 output not verified; F024 leftovers; F034 no cancel | OPEN | cad.py identical (hash 031e760a7f7c) |
| F005 wall index layer interpretation; F021 no rotation; F022 no containment | OPEN | walls.py, geometry.py identical; C10 |
| F006, F008, F009, F010, F011 coordination/placement classes | OPEN | cause class unchanged: coordination still ignores doors, windows, notes, equipment (rds:925-1109); columns now handled (rds:976-977) |
| F007 trade-drawing frame assumed equal to the FA frame | OPEN, anchor contract changed | rds:381-385, 548-552 take `anchor` as an FA-drawing point; interfaces/geometry.py `aligned` (geometry.py:379) compares trade drawings with each other only; row `anchor` is now the equipment symbol's centre (interfaces/service.py:1440) |
| F012 unresolved clash silent | OPEN | rds:1108 |
| F013, F014, F029 AI behaviour | OPEN | redesign/ai.py identical |
| F028 inconsistent repeated answer | NOT REPRODUCED (S6) | no code defect to cite; needs the stored cache (E08) or fresh model calls |
| F016 absolute output path; F031 archive copy; F033 minute-resolution name | OPEN | rds:1520; rds:1509-1519; rds:1502 |
| F017 duplicate execution; F030 plan changed at Apply | OPEN | rds:1495 `refresh()` runs first; no idempotency guard in `_start` beyond the active-job key |
| F018 no actor on decisions | OPEN | `adjust` has no user argument (rds:1265-1267) |
| F019 read-side effects | OPEN, extended | C20 |
| F026 incomplete placement of required modules | NOT REPRODUCED (S6) | the producing code is unchanged (rds:553-566) but the anchor it consumes changed (interfaces/service.py:1440), so the RD-M1 counts do not carry over |
| F027 rules not re-checked | SUPERSEDED for detector coverage only (S6) | N05/N07/N08/N10 now measure detector coverage at 6.3 m; no other rule (device by room kind, spacing, FLS) is re-checked after placement |
| F032 concurrent overwrite | OPEN, window longer | prepare.py:193-194; routers/redesign.py:120-144 |
| F035 confirm flag not gating | OPEN | rds:1552-1553 view only |
| F015, F020, F025 | not re-read | symbol-name mapping, AI-call provenance, floor naming: files not individually re-read |

S7's own tally: 29 still open (F009 and F010 by cause class), 1 superseded in part (F027), 2 not reproduced (F026, F028), 3 not re-read (F015, F020, F025), total 35. S6 classifies the three not re-read as STILL OPEN. S7 notes that S6's observations N1-N3 independently confirm C01, C02 and C03.

## 6. Corrections S7 made to the M1 refresh survey S2

S7 reused `docs/milestones/M1/refresh-2026-10-06/evidence/surveys/S2-drawings-review-redesign.md` (cited "S2 Table X row n"). These items are recorded here for the M1 package's errata later; S2 is not edited by this milestone. S7 states them under "Corrections and additions to S2 found while reusing it":

1. **Correction (file name).** S2 Table A rows `PREP.change` and `PREP.run` cite `review/prepare.py`; the file is `backend/app/redesign/prepare.py`.
2. **Correction (switch).** S2 Table A row `PREP.plan_run` says the agents run "only when PREP_AI_ENABLED"; `prep_ai_on()` is `ai_enabled or prep_ai_enabled` (`ai/provider.py:920-924`), so they run whenever AI_ENABLED is on (see C22).
3. **Spot check, no correction.** S2's `rds` line numbers were checked at HEAD and are correct: `_drawn` 695-701, `plan` 1145, `apply` 1479, `view` 1535, `interfaces_verified` 503, `_review` 80.
4. **Confirmed and extended.** S2 s7.2 #7 and Table E row 10 (Apply draws unapproved changes; the plan is not re-checked against the review) are confirmed. S7 adds the asymmetric re-plan (`rds:1179-1194`, C08), the agents-off creation path (C02, C03), and that the gate is not surfaced to the Apply button (C01).
5. **Confirmed and extended.** S2 s7.2 #5-#6 (rulings are company-wide) are confirmed. S7 adds that ruling matching ignores the device (C17), that bulk accept records rulings (C18), and that RD-M1's snapshot already held 108 rulings.

## 7. Limitations

- **No visual and no instance-level finding is possible from this survey.** No drawing, plot, crop or render was opened. No finding names a detector, room, sheet or coordinate of GC-01; the sheet, floor, room, coordinate and crop cells of the CSV read "n/a".
- **Nothing was run.** Every `CONFIRMED (code)` is a reading of source. The test suites pass (116 passed, `evidence/TEST-RESULTS.md`), but they pin current behaviour, including the behaviour C02 and C08 describe as defects, and use synthetic data and a stubbed model (see `M2R-TEST-COVERAGE-MAP.md`).
- **Every candidate is unreviewed.** `reviewer_status` is `UNREVIEWED` on all 22 rows. Severity is S7's proposal, not a decision. The `expected_behavior` and `reproduction_steps` cells are the scribe's statement of the rule each finding implies and of a bounded static or synthetic case; none was executed, and the CSV `confidence` cells are "Not rated" because S7 gives severity and cause status only.
- **The Golden Case does not cover this surface.** GC-01 is not reproducible from this repository as a whole (no DWG, DXF, database or plot; S7 Table E). The module library and the RD-M1 evidence JSON and renders verify by hash, but a baseline for N01-N11 needs a fresh plan on the GC-01 drawing. S7 suggests the agents-off path (N02 fallback, N03-N05, N07, N10) as the first deterministic re-run, calls no model, and does not test whether it is stable run to run.
- **Six manifest files cannot be diffed exactly** (`core/config.py`, `interfaces/{export,pdf,service,visual}.py`, `tests/test_fa_interfaces.py`); `interfaces/service.py` differs from b5c2222 by 2,660 B from the manifest copy (S7 s7 unknown 2).
- **Other unknowns S7 lists (s7).** Real switch values (AI_ENABLED, PREP_AI_ENABLED, DRAWING_REVIEW_AI_ENABLED, per-project `ai_policy`) on any deployment were not read; GC-01's drawing units and whether `coverage.py:136`'s raw layer matches the effective layer for its boundary layers are unknown; the engineering constants (6.3 m radius, 1% / 0.5 m2 tolerance, 0.5 m wall clearance, 0.3 m column gap, 15 m / 1,500 m2 limits) are set "by the engineers, 6 October 2026" with no standard cited and were not assessed against NFPA 72, the UAE Fire Code or a project specification; the coordination and orchestrator prompts were read, not evaluated, and no answer from either exists here; `ProjectDrawingReviewPage.tsx`, `RedesignPanel.tsx` and `AgentRunPanel.tsx` were read only at the cited lines; whether a PATCH during a running plan job is lost (C07, RD-M1-F032) is code reasoning only; `interfaces/*` beyond the Redesign-facing contract belongs to S1; the RD-M2 candidate exists only as documents; wall and column indexes are loaded with `pickle.load` from uploads (`walls.py:195`, `coverage.py:170`) and who can write there is unknown.
- **The tree was moving.** Other sessions changed `docs/` in the same working tree while S7 ran, and S7 read the roadmap as it stood then. HEAD moved from 4bab8d2 to f828ca1 during S7, and the test run's HEAD moved to c1f962a after the runs; `backend/` and `frontend/` were unchanged in the interval S7 checked, and this HEAD (457c815) is stated by the caller to be code-identical to 771001e.
