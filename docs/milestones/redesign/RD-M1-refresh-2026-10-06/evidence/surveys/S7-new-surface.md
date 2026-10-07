# S7 - New-surface delta survey for Redesign / Drawings Preparation (M2 refresh, input to RD-M1 delta baseline)

Surveyor: ep-surveyor (read-only). Survey date: 2026-10-06 (survey run on this date; repository commit dates are 2026-10-04..06).
Repository: /home/user/Design_Platform, HEAD 4bab8d2 at the start (`git diff --stat 771001e HEAD -- backend frontend` is empty: code identical to 771001e). Other sessions committed docs-only changes during the survey (HEAD at the end: f828ca1; `git diff --stat 4bab8d2 HEAD -- backend frontend` is empty), so every code statement holds at 4bab8d2 and at f828ca1.
Method: static reading of source, `git` read-only plumbing, sha256 of files. No test was run, no server started, no database queried, no model or AutoCAD called, nothing inside the repository changed. Everything below is UNREVIEWED; every "CONFIRMED (code)" is a reading of source, not a run.

## 0. Scope, evidence method, commands

**Scope.** The file set named in the brief: backend/app/redesign/**, backend/app/review/**, backend/app/interfaces/**, routers/redesign.py, routers/drawing_review.py, the five test files, the frontend pages (ProjectDrawingPrepPage, ProjectRedesignPage, ProjectDrawingReviewPage, ProjectDrawingsPage) and components/prep/*. Compared with RD-M1 (`docs/milestones/redesign/RD-M1/`: CURRENT-PIPELINE.md, RD-M1-REPORT.md s1-s3, GOLDEN-CASE-SELECTION.md, BASELINE-MANIFEST.json, FAILURE-INVENTORY.md categories A-H). Reuses `docs/milestones/M1/refresh-2026-10-06/evidence/surveys/S2-drawings-review-redesign.md` (cited "S2 Table X row n"; tables there: A = new field rows, B = drift, C = GET handlers, D = override writers, E = reuse/freshness + version constants) and S1 (interfaces) / S5 (GET side work).

**Key evidence finding (changes how exact this survey can be).** The RD-M1 baseline blobs are recoverable from git: commit **b5c2222** (2026-10-04 13:41, "Baseline: snapshot of the live working tree ... before FI-P1") holds blobs whose sha256 equals the BASELINE-MANIFEST.json hash for 29 of the 35 non-DWG manifest code files (all of backend/app/redesign/*, backend/app/review/*, routers/redesign.py, ProjectRedesignPage.tsx, test_redesign.py, interfaces detect/matrix/scan/schedules/__init__, jobs.py, runners.py, assist.py; conftest.py and test_ifc_worker_and_ai.py match older commits af7de8f / eb057eb). Where this is so, "what changed since RD-M1" below is an exact `git diff b5c2222 HEAD`, not an inference. Six manifest files have no matching blob anywhere in history: core/config.py, interfaces/{export,pdf,service,visual}.py, tests/test_fa_interfaces.py (the G-drive tree at RD-M1 time differs from b5c2222 for them; their deltas are lower bounds).

**Line endings.** The manifest was taken on Windows (CRLF); this checkout is LF. Seven files differ from the manifest hash only by line endings (converting LF to CRLF reproduces the manifest hash exactly): redesign/library/modules.json, review/{ai,pages,render}.py, interfaces/{detect,matrix}.py, test_drawing_review.py. They are treated as unchanged. The same applies to 5 of the 78 files of the RD-M1 package itself (FAILURE-INVENTORY.csv, E04, E08, E12, E18): 73 hash exactly, 5 match after CRLF restoration, 0 missing, 0 differing in content.

**RD-M2 is not in this tree.** `docs/milestones/redesign/RD-M2/` and `RD-M2-review-correction-r1/` describe a candidate (approved-only drawn set, fail-closed script, portable library, verify.py, test_redesign_apply.py). None of it is present here: no `verify.py`, no `test_redesign_apply.py`, `cad.py` is byte-identical to RD-M1 (031e760a7f7c...), `_drawn` still draws proposed review changes. So every RD-M1 Apply finding is unfixed in the active tree by file identity (see C-bis).

**Commands used** (all read-only; `git --no-optional-locks` from the diff stage on; the first `git log`, `git show --stat` and `git status` calls ran without it and can at most refresh the index stat cache):
`git rev-parse --short HEAD`; `git status --short` (once, at the start; it may refresh the index stat cache, no content changes); `git log --all --format=... -- <path>`; `git show <rev>:<path>`; `git cat-file -s`; `git ls-tree -r --name-only`; `git diff [--stat|--numstat] b5c2222 HEAD -- <paths>`; `git diff --stat 771001e HEAD -- backend frontend`; `ls`, `wc -l`, `grep -n`, `sed -n`, `find -iname '*.dxf' -o -iname '*.dwg'`; `sha256sum`; python3 heredocs (stdlib `json`, `hashlib`, `ast`, `glob`, `subprocess`) that read files and `git show` blobs and write only to this scratchpad folder; Read of the listed documents.
Not run by this survey: pytest, UI, AutoCAD, any model. Tests were run by another session (ep-test-runner, `docs/milestones/redesign/RD-M1-refresh-2026-10-06/evidence/TEST-RESULTS.md`, HEAD 4bab8d2, Python 3.13, AI_ENABLED=false): 116 passed in seven files, of which 62 in the five files of Table D (16 + 14 + 11 + 13 + 8), the same 62 this survey counted with `ast`. A parallel survey, S6 (`.../RD-M1-refresh-2026-10-06/evidence/surveys/S6-findings-delta.md`, committed as f861703 while this survey was running), classifies RD-M1's 35 findings against the active tree; it is the authority for those 35 (C-bis below is an independent cross-check and defers to it where they differ). S6's observations N1-N3 independently confirm C01, C02 and C03.

**Abbreviations.** S01-S25 = RD-M1's 25 stages (CURRENT-PIPELINE.md). N01-N18 = new stages (Table B2). C01-C22 = candidate findings `RD-M1R-C01...` (Table C). `rds` = redesign/service.py, `PR` = redesign/prepare.py, `rsv` = review/service.py. Line numbers are HEAD.

## 1. Headline numbers

- Table A: 54 files listed (48 in the requested set + 6 adjacent). Requested set: 13 unchanged (hash equal), 7 unchanged but line endings, 9 CHANGED, 1 REMOVED (ProjectRedesignPage.tsx), 15 NEW (not in the manifest, absent at b5c2222), 3 not in the manifest but present at b5c2222 (drawing_review.py router, ProjectDrawingReviewPage.tsx, ProjectDrawingsPage.tsx).
- Table B: RD-M1's 25 stages: 14 unchanged, 11 changed, 0 removed. 18 new stages (N01-N18).
- Table C: 22 candidate findings: Critical 1, High 8, Medium 10, Low 3. Plus C-bis: RD-M1 findings re-checked.
- Table D: 62 test functions in the five files; 12 of the 43 stages (S01-S25 + N01-N18) have no test in them (9 RD-M1 + 3 new), 5 more are only partly pinned; no test of any kind exercises `apply()` or the Apply job.
- Table E: GC-01 as a whole is NOT reproducible from this repository (no DWG/DXF/DB/plot); the module library, the evidence JSON and the 26 render/crop PNGs are, and verify by hash.

## 2. Table A - file delta against RD-M1's BASELINE-MANIFEST.json

Columns: "In manifest" = listed in `code_files` of BASELINE-MANIFEST.json (RD-M1 T0 2026-10-03T19:46+0400). "Hash then / now" = first 12 hex of sha256 (manifest value / current file; manifest values are of CRLF files). "Size then / now" = bytes (the manifest records size, not lines). "Lines then / now" = line count: "then" is taken from git blob b5c2222 where that blob's hash equals the manifest hash ("baseline blob recoverable"), otherwise from the nearest b5c2222 blob and marked in the note; the RD-M1 documents confirm two of them (service.py 1,449 lines; ProjectRedesignPage.tsx 584 lines). The note gives `git diff --numstat b5c2222 HEAD` (+added/-removed lines).

| File | In manifest | Hash then | Hash now | Result | Bytes then / now | Lines then / now | Note |
|---|---|---|---|---|---|---|---|
| `backend/app/redesign/__init__.py` | yes | 2250f011d362 | 2250f011d362 | same | 187 / 187 | 3 / 3 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/agents.py` | no | - | e67944545f76 | NEW vs manifest | - / 9,933 | - / 185 | added after b5c2222 |
| `backend/app/redesign/ai.py` | yes | be5b8f28cefe | be5b8f28cefe | same | 4,487 / 4,487 | 81 / 81 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/cad.py` | yes | 031e760a7f7c | 031e760a7f7c | same | 9,986 / 9,986 | 176 / 176 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/coverage.py` | no | - | 8e7d122ddaf8 | NEW vs manifest | - / 18,625 | - / 414 | added after b5c2222 |
| `backend/app/redesign/library/CR.dwg` | yes | d0b4cd2244d4 | d0b4cd2244d4 | same | 40,613 / 40,613 | 254 / 254 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/library/CT1.dwg` | yes | f43361eab514 | f43361eab514 | same | 39,653 / 39,653 | 243 / 243 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/library/CT2.dwg` | yes | 7afd3a163ec4 | 7afd3a163ec4 | same | 39,365 / 39,365 | 247 / 247 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/library/modules.json` | yes | 3dddf8e7a817 | 27acf22d8491 | same content (line endings only) | 728 / 690 | 38 / 38 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/markup.py` | no | - | 087997d44886 | NEW vs manifest | - / 4,203 | - / 80 | added after b5c2222 |
| `backend/app/redesign/prepare.py` | no | - | 31bcab786877 | NEW vs manifest | - / 41,997 | - / 781 | added after b5c2222 |
| `backend/app/redesign/service.py` | yes | 69fa173ab549 | 45eed814f832 | CHANGED | 75,159 / 82,874 | 1,449 / 1,569 | b5c2222 to HEAD: +176/-56; baseline blob recoverable at b5c2222 |
| `backend/app/redesign/walls.py` | yes | 6433e5703d5c | 6433e5703d5c | same | 9,004 / 9,004 | 197 / 197 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/ai.py` | yes | 6e16c49d7c55 | 7b17f4fcea9b | same content (line endings only) | 15,134 / 14,881 | 253 / 253 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/fls.py` | yes | 8ea424b04ef3 | 8ea424b04ef3 | same | 3,232 / 3,232 | 78 / 78 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/geometry.py` | yes | df696208fc9c | df696208fc9c | same | 5,607 / 5,607 | 130 / 130 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/markup.py` | yes | 2ccb2d70a198 | aec489c57c8c | CHANGED | 7,221 / 7,260 | 157 / 158 | b5c2222 to HEAD: +3/-2; baseline blob recoverable at b5c2222 |
| `backend/app/review/pages.py` | yes | 5b9b9e7c7f51 | f980d6cf0f75 | same content (line endings only) | 7,800 / 7,629 | 171 / 171 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/render.py` | yes | dc676dfd9f85 | c64112d1d1a0 | same content (line endings only) | 4,052 / 3,956 | 96 / 96 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/rulings.py` | yes | 7fc8ef3a33c2 | 7fc8ef3a33c2 | same | 4,489 / 4,489 | 100 / 100 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/review/scoped.py` | no | - | 227001d23eda | NEW vs manifest | - / 24,130 | - / 445 | added after b5c2222 |
| `backend/app/review/service.py` | yes | 30ca4d327eb1 | d5bc9597216f | CHANGED | 40,832 / 57,995 | 753 / 1,059 | b5c2222 to HEAD: +377/-71; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/__init__.py` | yes | ebefb04dd375 | ebefb04dd375 | same | 226 / 226 | 3 / 3 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/cases_pdf.py` | no | - | 12ab9bd5ecd5 | NEW vs manifest | - / 11,897 | - / 236 | added after b5c2222 |
| `backend/app/interfaces/detect.py` | yes | 88a7a07df5dc | b200c828f2c0 | same content (line endings only) | 12,664 / 12,432 | 232 / 232 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/evidence.py` | no | - | 22ba47a88dab | NEW vs manifest | - / 14,985 | - / 332 | added after b5c2222 |
| `backend/app/interfaces/export.py` | yes | a8847d6171a3 | 2233ee34ebf4 | CHANGED | 12,832 / 15,159 | 236 / 277 | b5c2222 to HEAD: +57/-16 |
| `backend/app/interfaces/findings.py` | no | - | 755836d32597 | NEW vs manifest | - / 42,047 | - / 792 | added after b5c2222 |
| `backend/app/interfaces/geometry.py` | no | - | 53697c4fdb44 | NEW vs manifest | - / 17,435 | - / 388 | added after b5c2222 |
| `backend/app/interfaces/matrix.py` | yes | e6dcd92faa4b | eec34a66f27e | same content (line endings only) | 9,522 / 9,364 | 158 / 158 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/pdf.py` | yes | bb859583b408 | 8b05f99d4f73 | CHANGED | 13,223 / 13,534 | 274 / 285 | b5c2222 to HEAD: +20/-9 |
| `backend/app/interfaces/render.py` | no | - | 33618cca61f2 | NEW vs manifest | - / 16,895 | - / 391 | added after b5c2222 |
| `backend/app/interfaces/scan.py` | yes | c374dfda628b | c02b0bc0ac6c | CHANGED | 5,320 / 8,138 | 122 / 162 | b5c2222 to HEAD: +44/-4; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/schedules.py` | yes | acc9c1653de1 | acc9c1653de1 | same | 7,206 / 7,206 | 159 / 159 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/app/interfaces/service.py` | yes | 1047d210cdb9 | d07bc80d50f2 | CHANGED | 55,493 / 122,011 | 1,082 / 2,150 | b5c2222 to HEAD: +1319/-251 |
| `backend/app/interfaces/visual.py` | yes | eca4bda4eef1 | ba23a58fb769 | CHANGED | 16,727 / 18,412 | 360 / 373 | b5c2222 to HEAD: +200/-187 |
| `backend/app/interfaces/workflow.py` | no | - | 1728efd52215 | NEW vs manifest | - / 59,933 | - / 1,025 | added after b5c2222 |
| `backend/app/routers/redesign.py` | yes | a7dfa7a7fce9 | 06f6793e7c64 | CHANGED | 9,479 / 10,473 | 183 / 198 | b5c2222 to HEAD: +15/-0; baseline blob recoverable at b5c2222 |
| `backend/app/routers/drawing_review.py` | no | - | f5a21843ce58 | not in manifest (existed at b5c2222) | - / 15,855 | 300 / 304 | b5c2222 to HEAD: +15/-11 |
| `backend/tests/test_redesign.py` | yes | 60e0482c7a82 | 60e0482c7a82 | same | 20,756 / 20,756 | 316 / 316 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/tests/test_drawing_prep.py` | no | - | 75759a296377 | NEW vs manifest | - / 26,750 | - / 453 | added after b5c2222 |
| `backend/tests/test_drawing_review.py` | yes | 2eaaa6e899b1 | 616b70f2f9e4 | same content (line endings only) | 26,574 / 26,140 | 434 / 434 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |
| `backend/tests/test_scoped_drawing_review.py` | no | - | 53fe25e1c4da | NEW vs manifest | - / 30,350 | - / 556 | added after b5c2222 |
| `backend/tests/test_drawing_review_outcome.py` | no | - | f6dc6e5347f7 | NEW vs manifest | - / 17,440 | - / 314 | added after b5c2222 |
| `frontend/src/pages/ProjectDrawingPrepPage.tsx` | no | - | b80891673b52 | NEW vs manifest | - / 6,669 | - / 143 | added after b5c2222 |
| `frontend/src/pages/ProjectRedesignPage.tsx` | yes | d62938c60b74 | - | REMOVED | 24,742 / - | 584 / - | deleted after b5c2222; baseline blob recoverable at b5c2222 |
| `frontend/src/pages/ProjectDrawingReviewPage.tsx` | no | - | 375f38bfaba1 | not in manifest (existed at b5c2222) | - / 38,620 | 773 / 848 | b5c2222 to HEAD: +94/-19 |
| `frontend/src/pages/ProjectDrawingsPage.tsx` | no | - | 0f8301316e75 | not in manifest (existed at b5c2222) | - / 11,308 | 249 / 249 | unchanged since b5c2222 |
| `frontend/src/components/prep/AgentRunPanel.tsx` | no | - | 1921006f0571 | NEW vs manifest | - / 12,801 | - / 270 | added after b5c2222 |
| `frontend/src/components/prep/RedesignPanel.tsx` | no | - | 9bf5c2a874aa | NEW vs manifest | - / 28,705 | - / 632 | added after b5c2222 |
| `frontend/src/components/prep/types.ts` | no | - | 60d4cf3eb506 | NEW vs manifest | - / 4,333 | - / 170 | added after b5c2222 |
| `backend/scripts/scoped_drawing_review.py` | no | - | c6f44d8ca7c1 | NEW vs manifest | - / 4,919 | - / 85 | added after b5c2222 |
| `backend/alembic/versions/e6a8c0b2d4f6_drawing_prep_run.py` | no | - | a0247dedab2d | NEW vs manifest | - / 832 | - / 28 | added after b5c2222 |
| `backend/alembic/versions/c5e7a9b1d3f5_drawing_redesign.py` | yes | 9d7f175a831a | 9d7f175a831a | same | 2,099 / 2,099 | 48 / 48 | unchanged since b5c2222; baseline blob recoverable at b5c2222 |

Reading notes for Table A:
- "same content (line endings only)": the file's LF form hashes to the manifest value once converted to CRLF (verified). Treated as unchanged: review/ai.py (prompt `drawing-review-2026-10-01.3` unchanged), review/pages.py, review/render.py, interfaces/detect.py, interfaces/matrix.py, modules.json, test_drawing_review.py.
- Unchanged by hash and therefore by behaviour: redesign/{ai,cad,walls}.py, the three library DWGs, review/{fls,geometry,rulings}.py, interfaces/{__init__,schedules}.py, test_redesign.py. In particular `cad.py` (stages S20-S23), `walls.py` (S08), `ai.py` (prompt `drawing-redesign-2026-10-02.4`, S12/S13 parser) and `rulings.py` are exactly what RD-M1 froze.
- Changed redesign/service.py: b5c2222 to HEAD +176/-56 (1,449 to 1,569 lines). Changed review/service.py +377/-71 (753 to 1,059). Changed routers/redesign.py +15/-0. Changed review/markup.py +3/-2 (a `footer` parameter). The hunks are read in Table B.
- Changed interfaces/service.py 1,082 (b5c2222) to 2,150 lines (+1,319/-251; the RD-M1 manifest copy was 55,493 B, b5c2222 58,153 B, HEAD 122,011 B). New modules cases_pdf, evidence, findings, geometry, render, workflow (FI-P1). Only the Redesign-facing contract is read here (Table B, S09/S10/N12); the rest is S1's.
- Adjacent files changed since b5c2222 that the pipeline calls (not in the manifest set above, diffs read): `ai/provider.py` (+449: get_prep_provider, get_review_provider, prep_ai_on), `compliance/assist.py` (+50: exact_model, accept, fresh, NULL_MODEL), `core/config.py` (+160: prep_*, drawing_review_* switches), `ifc/services/runners.py` (+59: keep_answered, ReviewIncomplete mapping, interface run kinds; `_redesign` unchanged), `services/jobs.py` (+24: lanes, progress flush; `recover_stale` untouched), `ifc/dxf/convert.py` (+17: DWG_CONVERT_PARALLEL semaphore instead of a single lock), models.py (+162; ProjectRedesign.run at models.py:697, migration e6a8c0b2d4f6).
- Missing from the manifest and never compared by RD-M1: ProjectDrawingReviewPage.tsx (773 to 848 lines, +94/-19 since b5c2222), routers/drawing_review.py (+15/-11), ProjectDrawingsPage.tsx (unchanged since b5c2222).
- The frontend page RD-M1 audited (ProjectRedesignPage.tsx, 584 lines, hash d62938c60b74 = b5c2222 blob) no longer exists; its role is split into ProjectDrawingPrepPage.tsx (143), components/prep/RedesignPanel.tsx (632), AgentRunPanel.tsx (270), types.ts (170).

## 3. Table B - pipeline stage delta

### B1. RD-M1's 25 stages (CURRENT-PIPELINE.md) at HEAD

"Changed" is read from `git diff b5c2222 HEAD` (b5c2222's redesign/review blobs are hash-identical to the RD-M1 manifest). Stage names and numbers are RD-M1's.

| # | RD-M1 stage | Mark | What changed (or why unchanged), file:line at HEAD |
|---|---|---|---|
| S01 | Drawing registration | changed (minor) | ifc/dxf/convert.py: the one-at-a-time DWG conversion lock became a `DWG_CONVERT_PARALLEL` semaphore (+17/-2). Registration code itself is outside the diffed set; S1 rows IFC.* own it. |
| S02 | Drawing/source selection | changed | routers/redesign.py:59-60 adds `review_state = review_service.outcome(review)[0]` to the drawings list; page picks the first drawing with `review_state == "done"` (ProjectDrawingPrepPage.tsx:46-47). `_drawing` (routers/redesign.py:35-39) still has no `deleted_at` check, unlike drawing_review.py:36-40 (S2 s7.2 #9). |
| S03 | Source hashing | unchanged | review/render.py identical modulo line endings (`_sha` :42-47); plan check rds:1171-1173 and Apply check rds:1492-1493 are the same logic. |
| S04 | CAD/PDF/IFC extraction (plot) | unchanged | render.py identical modulo line endings (plot script :79-82, 30-minute timeout :19). FLS drawings are plotted through the same `render_file` inside `plan_job` (rsv:119-142, unchanged hunk). |
| S05 | Sheet/floor detection; plot-model tie | unchanged (code), caller changed | geometry.py, pages.py identical (scale+offset only, FIT_VERSION 1 geometry.py:23). `_fit` is called after `plan_job` in `run` (rsv:193) and in `build` (rsv:595). |
| S06 | Room and geometry discovery (review windows) | changed | rsv +377/-71. Windows can be `incomplete` and are merged room by room (`rooms_to_ask` rsv:331-337, merge rsv:499-523); `outcome()` (rsv:400-435); `ReviewIncomplete`, `blocked`/`failed` keep the previous answers (rsv:181-190, 248-256); `keep_answered` (rsv:300); every look sends `effort` and `exact_model=True`, the disabled provider's placeholder is refused (rsv:464-470, 477-483, 494-499); `get_review_provider` (rsv:180); decisions kept with their proposal (rsv:693-706, 765-832); plan/FLS pass findings merged (rsv:340-361). Prompt text unchanged: `PROMPT_VERSION = "drawing-review-2026-10-01.3"` (review/ai.py:33), per-sheet version `PROMPT_VERSION+<rulings sha1[:10]>` (rsv:175-176). |
| S07 | Existing symbol discovery | unchanged | `_occurrences` (rds:97-108), `_symbols`, `_top_level` not in the diff. |
| S08 | Wall extraction and caching | unchanged | walls.py identical (raw-layer deny-list NOT_WALLS :23-24, VERSION 1 :27); `_walls` rds:178-192 unchanged. A second index now sits beside it (N03). |
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

### B2. New stages introduced by the added code

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

### B3. Is the preparation gate enforced by Apply? - NO (code)

The gate is computed once, at the end of the plan job, and stored:

```
rds:1246   run["gate"] = PR.gate(changes, run["coordination"], run["review"], cols)
rds:1250   row.status, row.finished_at = "planned", utc_now()
```
`grep -n gate` over backend/app/redesign, routers/redesign.py, ifc/services/runners.py and routers/drawing_review.py finds it only at prepare.py (definition, docstring), rds:1245-1253 (the line above and the plan's return value). Apply never reads `row.run`:

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
The page does not enforce it either: the Make button is `disabled={disabled || ready === 0}` where `ready = all.filter((c) => c.drawn).length` (RedesignPanel.tsx:157, 403-404), the Devices step badge is a check mark whenever `redesign_status === "planned"` (ProjectDrawingPrepPage.tsx:70), and `run.gate` is only displayed (AgentRunPanel.tsx:55-95). No test applies a `needs_engineer` plan (no test reaches `apply()` at all).

## 4. Table C - new failure surface: UNREVIEWED candidate findings

Scheme: RD-M1's categories A Source and extraction; B Device understanding; C Placement; D Coverage and engineering rules; E Coordination; F AI behaviour; G Workflow; H CAD Apply; plus **I. Data governance / scope** (new: what data may reach a model or another project). All rows: cause status CONFIRMED (code) - read from source; nothing was run and nothing visual was possible. Severity is a proposal on RD-M1's scale (Critical / High / Medium / Low). "Owner" uses the roadmap's milestone names (M3 Ownership, Access & Memory Policy; M5 Safe Apply; M7 Central Processing; M8 Deterministic Geometry; M10 DB-driven tabs; M12 Multi-Stage AI & Visual Review). No instance-level finding (a particular detector, room or sheet of GC-01) is asserted.

### C-summary

| ID | Sev | Cat | Defect class (short) | Stage | Deterministic | Existing test | Owner |
|---|---|---|---|---|---|---|---|
| RD-M1R-C01 | High | G | Preparation gate stored, not enforced at Apply (server or page) | S19/S20, N10 | Yes | gate arithmetic only (test_drawing_prep.py:161); nothing reaches Apply | M5 |
| RD-M1R-C02 | Critical | G | Proposed, unapproved changes are drawn; with prep AI off the platform alone creates them (extends RD-M1-F002) | S18, N02, N09, N11 | Yes | PINNED as intended (test_redesign.py:213; test_drawing_prep.py:142) | M5 |
| RD-M1R-C03 | High | F | Agents-off fallback erases the nearest symbol whatever its name | N02 | Yes | named case only (test_drawing_prep.py:149) | M5 / M8 |
| RD-M1R-C04 | High | F | Floor review is structured text, no rendered image: "ok" is not visual evidence | N09 | Yes | none asserts an image part (test_drawing_prep.py:215 reads text parts) | M12 |
| RD-M1R-C05 | Medium | F | An orchestrator verdict is not required per change; omission, `needs_engineer` and open questions do not reach the gate | N09, N10 | Yes | none (fake answers every id) | M12 |
| RD-M1R-C06 | Medium | G | Gate omits conditions the run itself records (no columns index, big coordination moves, plot residual > 1 m, erase-by-hand) | N10 | Yes | none | M5 / M8 |
| RD-M1R-C07 | Medium | G | Gate, run summary and orchestrator verdicts are snapshots; engineer edits and Apply's refresh do not recompute or invalidate them | N08, N10, S15, S20 | Yes | none | M5 |
| RD-M1R-C08 | High | G | Stale plan: a reversed or changed review decision, or a no-longer-verified interface schedule, is not seen by Apply; a re-plan drops approvals asymmetrically | S16, S18, S20, N12, N14 | Yes | none for reversal; keep-when-gone pinned (test_drawing_prep.py:416) | M5 / M7 |
| RD-M1R-C09 | Medium | G | A partly reviewed drawing (`status` done, `outcome` partial) is accepted by Redesign, server and page | S02, S16, N13 | Yes | review side only (test_drawing_review_outcome.py:292) | M5 / M12 |
| RD-M1R-C10 | High | A/D | Room fill and coverage rest on the raw-layer wall/boundary index RD-M1 found untrustworthy | S08, N03-N05 | Yes | synthetic walls only | M8 |
| RD-M1R-C11 | Medium | A | Distances taken as metres in room fill, coverage, radius and library scale; real drawing units are read only at Apply | N03-N05, S10 | Yes | none (tests use 0.1 m per pt) | M8 |
| RD-M1R-C12 | Medium | D | Coverage is measured only in rooms that receive an added/replaced detector; REMOVE never triggers it; the page says "every room covered" | N05, N10 | Yes | none | M8 |
| RD-M1R-C13 | Medium | D | Existing detectors are counted by name regex (SMOKE, HEAT, SD, OS, HD...) and heat and smoke share one radius | N05 | Yes | none | M8 |
| RD-M1R-C14 | Low | D | The erased-handle set counts skipped, failed and unapproved removals as removed | N05, N08 | Yes | none | M8 |
| RD-M1R-C15 | High | I | `ai_policy` ("blocked") is consulted by no review, preparation, redesign or scoped-review AI path | N02, N06, N09, N13, N17 | Yes | none | M3 / M12 |
| RD-M1R-C16 | High | I | Review rulings are company-wide: other projects' text enters the prompt, auto-dismisses findings, is returned in the payload, can be deleted by anyone, and vanishes with a project | N16 | Yes | single-project test only (test_drawing_review.py:192) | M3 / M12 |
| RD-M1R-C17 | High | C/D | A "not needed" ruling is matched on room kind + system + action, not on the device, and so suppresses a different required device | N16, S06 | Yes | same-device case only | M12 |
| RD-M1R-C18 | Medium | I | Bulk accept writes a company-wide CONFIRMED ruling for every accepted finding, unreviewed | N16 | Yes | not asserted | M3 / M12 |
| RD-M1R-C19 | Medium | G | A continued or scoped review keeps old answers and relabels them with the current prompt+rulings version | N13, N17 | Yes | keep-and-ask-rest pinned (test_scoped_drawing_review.py:479), label not | M12 / M7 |
| RD-M1R-C20 | Medium | G | GET /redesign/{did} (polled by the page) runs the review build: geometry fit, row creation, commit (extends RD-M1-F019) | S18, S05 | Yes | none | M10 |
| RD-M1R-C21 | Low | G | A preparation run cannot be reproduced from what it stores (orchestrator payload, coordination picture, answers) | N06, N09 | Yes | none | M12 / M7 |
| RD-M1R-C22 | Low | G | Prep agents cannot be switched off while AI_ENABLED is on; the gate names the wrong switch | N01, N10 | Yes | none | M12 |

Counts: Critical 1 (C02), High 8 (C01, C03, C04, C08, C10, C15, C16, C17), Medium 10 (C05, C06, C07, C09, C11, C12, C13, C18, C19, C20), Low 3 (C14, C21, C22). Total 22.

### C-detail

**RD-M1R-C01 - Gate stored, not enforced at Apply** (G, High). Stage S19/S20, N10. Code: rds:1246 `run["gate"] = PR.gate(...)`; rds:1496-1498 `todo = [c for c in row.changes or [] if _drawn(c)]` / `raise RedesignError("No change is placed to make: plan the redesign, or approve the changes first.")`; routers/redesign.py:104-107 `start_apply` creates the job with no state check; RedesignPanel.tsx:403 `disabled={disabled || ready === 0}`. Full quotes in B3. Cause: CONFIRMED (code). Deterministic: yes. Tests: test_drawing_prep.py:161 (`test_the_gate_is_the_platforms_count`) and :328 (asserts `run["gate"]["state"] == "needs_engineer"`); no test posts Apply. Owner: M5 ("enforce gates at the server boundary").

**RD-M1R-C02 - Unapproved changes drawn; the platform alone can create them** (G, Critical, extends RD-M1-F002). Stage S18, N02. Code: rds:699-701 (quote in B3); prepare.py:144-153 `if not prep_ai_on(): stats["by"] = "platform"; for c in todo: answer = fallback_answer(c, symbols) ... R._place(c, sheets[c["page"]], symbols, answer, walls)`; `_place` ends `if change["status"] in ("pending", "failed"): change["status"] = "proposed"` (rds:865-866). In RD-M1 a plan with no usable model left each change `failed` (the call returned no data); now it leaves `proposed`, which `_drawn` draws. The orchestrator, which is the only control, is off in that mode (prepare.py:685-687 `state "off"`) and in any case only `reject` stops a proposed change (rds:700). The draftsman PDF (N11) lists them as changes "to be drawn", and the page's count card still calls them "Placed, to approve" (RedesignPanel.tsx:246; S6 Table C). Cause: CONFIRMED (code). Deterministic: yes. Tests: the behaviour is asserted as intended: `assert R._drawn({**placed, "status": "proposed"})` (test_redesign.py:213) and `assert R._drawn({**base, "status": "proposed"})` (test_drawing_prep.py:142), `assert R._drawn({**base, "status": "approved", "check": {"verdict": "reject", ...}})` (:146). Fixing it requires changing those assertions (RD-M2 did, in a candidate not integrated here). Owner: M5.

**RD-M1R-C03 - Fallback REMOVE/REPLACE erases the nearest symbol of any kind** (F, High). Stage N02. Code prepare.py:121-125:
`words = _words(change["device"])` / `named = [k for k in change["candidates"] if words & _words(k["name"])]` / `candidate = (named or change["candidates"])[0]["n"]`. When no candidate's name shares a word with the device, the first (nearest to the review's point) of up to 15 numbered symbols is chosen; the answer carries `"confidence": "low"` (:129) but `_place` never reads confidence (rds:794-866). The erase is real when the symbol is a top-level insert (`erasable`, rds:740), otherwise labelled "erase by hand". This is the RD-M1-F003 hazard (a REMOVE accepted on an unsupported pick) reachable with no model. Cause: CONFIRMED (code). Deterministic: yes. Tests: test_drawing_prep.py:149 covers the named case only (the heat-detector example resolves to candidate 2). Owner: M5 (approved-only) and M8.

**RD-M1R-C04 - Floor review is text, not a picture** (F, High). Stage N09. Code prepare.py:656-660: `result = assist.call_task(session, AG.REVIEW_TASK, AG.REVIEW_SYSTEM, [TextPart("the floor's changes (data)", json.dumps(payload, default=str))], AG.REVIEW_SCHEMA, ...)`; the prompt says "You receive one floor's changes as JSON data" (agents.py:74). The payload is `_review_input` (prepare.py:629-647): ids, device names, confidences, `metres_from_review_point`, `on_wall`, `column_clear`, the platform's own `coordination` and `coverage`. No ImagePart, so `ok` cannot attest what the plan shows (a wall behind the device, a door swing, a symbol on a note); it can only restate the platform's numbers. The roadmap says the same (s3 Drawings, M12: "Structured-text review alone cannot prove visual placement"). Compare N06, which does see an image. Cause: CONFIRMED (code). Tests: FakeOpus builds its answer from `texts` only (test_drawing_prep.py:191-212); no assertion on parts. Owner: M12.

**RD-M1R-C05 - Per-change verdict not required** (F, Medium). Stage N09/N10. Code: `review_problem` (agents.py:158-171) checks keys and types, not that every id was judged; `read_review` keeps only the verdicts it was given (agents.py:177-181); prepare.py:713-715 `for c in by_page[page]: if c["id"] in answer["verdicts"]: c["check"] = ...`; the gate counts only `reject` and `check` (prepare.py:761-765) so a change with no verdict counts as fine; `recommendation` and `open_questions` are stored in run.review (prepare.py:716-717) but `gate()` reads neither. Floor state is `done` as soon as the call returned (prepare.py:732). Tests: none omits an id. Owner: M12.

**RD-M1R-C06 - Gate omits conditions the run records** (G, Medium). Stage N10. (a) Columns index missing: `columns()` swallows the failure (prepare.py:84-86, a log line), `gate()` computes `on_column` only `if cols is not None` (prepare.py:749), and `coordination["columns"]` is `None` (prepare.py:501) with no reason - a drawing whose columns could not be read is "ready". (b) A detector moved by the platform far from where the review put it: > 1 m is only a note to the agent (prepare.py:293-301), not a gate reason. (c) Plot-fit residual > 1 m: `confirm` is computed for the page (rds:1552-1553) but is not a gate reason and does not affect `_drawn` (RD-M1-F035 stands). (d) A REMOVE whose symbol is not directly erasable ("erase by hand", rds:1408-1409) is not a reason. (e) Interface modules are excluded from the gate (prepare.py:744) and from the orchestrator (prepare.py:679). Tests: test_drawing_prep.py:161 asserts only the reasons that exist. Owner: M5 (server gate), M8.

**RD-M1R-C07 - Snapshots: gate, run summary, verdicts** (G, Medium). Stage N08, N10, S15, S20. `adjust` (rds:1265-1321) changes `status`, `insert`, `coverage`, but never `row.run` and never removes `change["check"]`; `view` returns `row.run` as stored (rds:1564) and the page shows `run.gate` (AgentRunPanel.tsx:55); `_drawn` reads `check.verdict` made on the placement before the engineer moved it (rds:700). `apply()` calls `refresh()` first (rds:1495), which can re-coordinate positions after the verdict was given (rds:1440-1443, 1473). So "Ready for the draftsman" can describe a plan that no longer exists. Tests: none. Owner: M5.

**RD-M1R-C08 - Stale plan after a decision reversal (and a schedule change)** (G, High). Stage S16, S18, S20, N12, N14. Apply draws whatever `row.changes` holds (rds:1496); neither `decide` nor `decide_many` touches the redesign row (no `redesign` reference in backend/app/review or routers/drawing_review.py); the view only reports `undecided` (rds:1544, 1558). So an accepted finding the engineer later dismisses or reopens, or whose proposal changed so its decision returned to `open` (rsv:693-706), is still drawn until the plan is run again. The re-plan is asymmetric: `accepted = [f for f in view["findings"] if f["decision"] == "accepted" ...]` (rds:1179) builds the list, and only changes whose finding is absent from the review are carried over (rds:1192-1194), so an engineer-approved change whose finding is present but no longer accepted is dropped, approval included, while one whose finding vanished is kept (that keep is pinned: test_drawing_prep.py:416). Interface modules: `interfaces_verified` is asked at plan and add time only (rds:1199, 649); an approved module stays drawn after the schedule stops being verified (S2 Table E row 10). Cause: CONFIRMED (code). Tests: none for reversal. Owner: M5 (stale approvals), M7.

**RD-M1R-C09 - Partial review treated as done** (G, Medium). Stage S02, S16, N13. rsv:259-263 sets `row.status = "done"` when some windows failed or are incomplete and only words the error text; `outcome()` calls that `partial` (rsv:431-434); `_review()` accepts any `done` (rds:87-88); the page's Place buttons use `drawing.review_status === "done"` (RedesignPanel.tsx:150, 178, 217) while the step badge uses `review_state` (ProjectDrawingPrepPage.tsx:60-68), so the page can show "part" on Review and still prepare devices. Rooms never reviewed yield no findings, hence no changes and no coverage. Tests: partial is pinned on the review side only (test_drawing_review_outcome.py:292). Owner: M5 / M12.

**RD-M1R-C10 - Coverage on an untrusted index** (A/D, High). Stage S08, N03-N05. coverage.py:136-137 reads `entity.dxf.get("layer")` (raw) and tests BOUND_LAYERS (`WALL|DOOR|GLASS|GLAZ|SILL|WINDOW|WIN|CURTAIN|PARTITION|COLUMN|COLS?|S-COL`, :48); the fallback is `double_lines(walls.near(...))` over walls.py's raw-layer deny-list (identical to RD-M1). RD-M1 found raw layer `0` with effective layer `29-PARKING` admitted (F006), 4,351 invisible-flag segments (F005) and no containment model (F022); none of visibility, layer on/frozen/no-plot, viewport freeze or effective layer is read (roadmap s3: "New room coverage code cannot compensate for an untrusted wall index"). A room is only as real as the lines that close it, and the gate, the added detectors and the best spots all come from it. Not re-run here; instance effects on GC-01 are not asserted. Tests: synthetic `Walls` only (test_drawing_prep.py:21-34). Owner: M8.

**RD-M1R-C11 - Units assumed metres** (A, Medium, latent). coverage.py:19 "Distances are in the drawing's units, taken as metres (as the walls)"; the radius `prep_smoke_radius_m = 6.3` is compared with model coordinates (coverage.py:330-342, prepare.py:68-70); `RADIUS_M = 8.0` (rds:59), library scale `_paper_scale` (rds:407-411) use the same assumption. `_units()` (rds:1392-1397) exists and is used only for the Apply marker size (rds:1494). On a drawing in mm a 6.3 radius would be 6.3 mm: every room "uncovered" and `best_spots` would add up to 12 per room (coverage.py:368, `most=12`). Whether GC-01 is in metres is not verified here. Tests: none with a non-metre drawing. Owner: M8.

**RD-M1R-C12 - Coverage scope** (D, Medium). Rooms are made only from changes that are detectors being added or replaced (`is_detector`, prepare.py:96-99; `rooms`, :235-253). Rooms with no new detector, and any room where the engineer's change is a REMOVE of a detector, are never measured, yet the page says "no device on a column or another device, every room covered at 6.3 m" (ProjectDrawingPrepPage.tsx:81-83) and the panel says "Ready for the draftsman". Tests: only rooms that receive a detector. Owner: M8.

**RD-M1R-C13 - Existing detectors by name** (D, Medium). prepare.py:59 `DETECTOR = re.compile(r"DETECTOR|SMOKE|HEAT|MULTI[-\s]?SENSOR|\bOS\b|\bHD\b|\bSD\b", re.I)` is applied to the symbol's device-type name or block label (prepare.py:264, 609): anything whose name contains SMOKE or HEAT (a smoke damper module, a smoke-control panel) counts as a detector that covers the room, which under-adds detectors. One radius for both heat and smoke (`prep_heat_radius_m = prep_smoke_radius_m = 6.3`, config.py:433-434; `radius()` prepare.py:68-70). Tests: none with a non-detector name. Owner: M8.

**RD-M1R-C14 - Erase set ignores status** (D, Low). prepare.py:498 and :620 `erased = {(c.get("remove") or {}).get("handle") for c in changes if c.get("remove")}` - every change with a `remove`, whatever its status. A detector whose REMOVE the engineer skipped (so it stays on the drawing) is treated as gone, so coverage is under-stated and detectors are over-added (conservative direction). Tests: none. Owner: M8.

**RD-M1R-C15 - ai_policy not consulted** (I, High). `project_policy.allowed/require` (app/ai/project_policy.py) is used by sheet_reader, verification, submittal_reader, extraction, sample_request and compliance; `grep -rn "ai_policy\|project_policy"` over backend/app/review, backend/app/redesign, routers/redesign.py, routers/drawing_review.py and ifc/services/runners.py returns nothing. Review looks (rsv:438-527) send plan crops and room names; placement, coordination and orchestrator send plan crops and JSON about the project (prepare.py:383-414, 650-666; rds:1112-1142); the scoped run does too. A project set to `blocked` ("its documents are not sent to an AI provider") still has them sent when a switch is on (S2 s7.2 #4; N18). Tests: no `ai_policy` in the five files. Owner: M3 (policy), M12 (call site).

**RD-M1R-C16 - Rulings are company-wide** (I, High). `listed(db)` has no project filter (rulings.py:59-60); `prompt(db)` puts up to 80 of them, with room names, notes and instructions, into every project's review prompt (rulings.py:71-90; rsv:175-176) and a new ruling changes the prompt version so every project's looks are asked again (rsv:176-177, 296-300); `build` uses `R.not_needed(db)` to set `decision = "dismissed", by_ruling = True` on another project's findings (rsv:688, 719-723), which then never reach Redesign (rds:1179); the page payload returns every ruling's room, instruction, note and `project_id` (rsv:750-753); `DELETE /drawing-review/rulings/{id}` checks neither project nor owner (drawing_review.py:290-304); project deletion removes the project's rulings (project_deletion.py:97), silently reopening other projects' by-ruling dismissals. (S2 s7.2 #5-#6 note the exposure; the consequence for what Redesign draws is added here.) RD-M1's DB snapshot already held 108 `review_rulings` rows across its 10 projects (E12 table_counts), of which at most 80 enter a prompt (rulings.py:25). Tests: one project (test_drawing_review.py:192-238). Owner: M3 (policy), M12.

**RD-M1R-C17 - Ruling key ignores the device** (C/D, High). The model sees rulings keyed `(room_key or room_type, system, action, device)` (rulings.py:77) but the automatic dismissal uses `(room_key, system, action)` only (rulings.py:96-99; rsv:719-723, for `kind in ("room", "spacing")`). The six systems are coarse (review/ai.py SYSTEMS): `speaker` covers ceiling speakers, wall speakers and sounder-flashers, and the company rules require a sounder-flasher in pump rooms (review/ai.py RULES). So "NOT NEEDED: ADD ceiling speaker in PUMP ROOM" settles "ADD sounder-flasher in PUMP ROOM" as dismissed by ruling on every floor and in every project; the only trace is the note "By ruling (<room>)". Tests: test_drawing_review.py:192 uses the same device on both floors. Owner: M12.

**RD-M1R-C18 - Bulk accept writes CONFIRMED rulings** (I, Medium). drawing_review.py:278-282: `elif f["decision"] != "accepted": service.record_decision(...); R.record(db, project.id, drawing.id, f, "accepted", user_id=current_user.id)` for every finding in the batch. The ruling text given to every later review says "They show what this company wants: follow them over your own reading ... propose what they CONFIRMED wherever the same situation occurs" (rulings.py:86-89). A one-click "accept the ones on show" is therefore recorded as the engineers' standing instruction. The code is byte-identical to RD-M1 but RD-M1 did not audit the review. Tests: `_reviewed_drawing` uses the bulk endpoint (test_drawing_prep.py:303) without asserting rulings. Owner: M3 / M12.

**RD-M1R-C19 - Kept answers relabelled** (G, Medium). rsv:300 `if old and (keep_answered or old.get("prompt_version") == version):` keeps the windows and passes a model answered; rsv:311 `sh["prompt_version"] = version` then stamps every planned sheet with the current prompt+rulings version. The scoped run always sets `keep_answered` (scoped.py:384-385, preflight :124-125). A sheet's stored answers can have been produced under older rulings or prompt text while the row says current; `outcome()` and `build` cannot tell. Tests: test_scoped_drawing_review.py:479 pins keep-and-ask-the-rest, not the label. Owner: M12, M7.

**RD-M1R-C20 - GET runs the review build** (G, Medium; extends RD-M1-F019). `view` calls `review.build(...)` and `db.commit()` (rds:1541-1545); `build` calls `_fit` (DXF parse, writes `row.sheets`) and commits (rsv:593-596, 537-554); `state()` creates rows (rds:70-77, rsv:49-57). The Prep page polls GET /redesign/{did}. Same chain in drawing-review GET/export/markup and draftsman (S2 Table C rows 17, 19, 20, 22, 26; S5). Tests: none asserts a GET leaves the stored rows unchanged. Owner: M10 (roadmap: "ordinary tab reads perform no ... business writes").

**RD-M1R-C21 - Run not reproducible** (G, Low). `record()` keeps stage, label, floor, room, state, seconds and the first 160 characters of the outcome (prepare.py:189-191, 534-538, 723-725). The orchestrator's payload (prepare.py:690), the coordination picture and text (prepare.py:329-380, 398-403) and the model's answers are not stored on the row; answers exist only in the result cache (key `{sha}:coord:{room}`, `{sha}:review:{page}`, with a TTL). RD-M1-F014 ("symbol list not stored") stands and the new agents add the same gap. Owner: M12, M7.

**RD-M1R-C22 - No independent off-switch for the agents** (G, Low). `prep_ai_on()` is `settings.ai_enabled or settings.prep_ai_enabled` (provider.py:920-924); config.py:421-424 describes PREP_AI_ENABLED as a switch "like the FA Interfaces workflow, AI_ENABLED staying off for the rest". With AI_ENABLED on (RD-M1's G copy had it on), the agents run, `prep_max_concurrency` is ignored (provider.py:934-935), and the gate's reason reads "not reviewed by the orchestrator (PREP_AI_ENABLED is off)" (prepare.py:767) while the condition is "neither switch is on". Tests: none with AI_ENABLED on and PREP off. Owner: M12.

### C-bis. RD-M1's 35 findings re-checked in the changed code

"Open" = still present by file identity (the code RD-M1 cited is in a file whose hash is unchanged) or by a line read at HEAD. Nothing here was run.

| RD-M1 finding | Status at HEAD | Evidence |
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

Tally of this cross-check: 29 still open (F009 and F010 by cause class), 1 superseded in part (F027), 2 not reproduced (F026, F028), 3 not re-read here (F015, F020, F025). S6 classifies the three as STILL OPEN and so reaches FIXED 0 / STILL OPEN 32 / SUPERSEDED 1 / NOT REPRODUCED 2 over all 35; none is fixed. RD-M2's closures are not in this tree.

## 5. Table D - test coverage map

Scope: every `test_*` function in test_redesign.py (16), test_drawing_prep.py (14), test_drawing_review.py (11), test_scoped_drawing_review.py (13), test_drawing_review_outcome.py (8) = **62** (checked with `ast`: every function is in the table, none missing). "Pins" means the test exercises that stage's own logic; a stage reached only through a monkeypatched stub is not counted (noted). The five files were not run here (see s0).

### D1. Per test

| File:line | Test | Stage(s) pinned | Note |
|---|---|---|---|
| test_redesign.py:30 | `test_a_change_is_prepared_with_the_devices_near_it_numbered` | S07, S11 |  |
| test_redesign.py:37 | `test_an_add_is_placed_where_the_model_points_with_the_drawings_own_symbol` | S13 |  |
| test_redesign.py:48 | `test_a_replace_takes_the_old_symbols_place_and_a_remove_needs_a_symbol` | S13 |  |
| test_redesign.py:62 | `test_the_answer_is_kept_only_where_it_is_well_formed` | S12, S13 |  |
| test_redesign.py:68 | `test_the_autocad_script_erases_inserts_at_the_true_scale_and_marks_each_change` | S20 |  |
| test_redesign.py:86 | `test_a_block_drawn_away_from_its_base_point_is_inserted_so_it_is_seen_on_the_spot` | S07, S13, S20 |  |
| test_redesign.py:100 | `test_a_sounder_flasher_is_the_strobe_symbol_and_a_sounder_the_wall_sounder` | S13 |  |
| test_redesign.py:119 | `test_a_block_faces_the_side_its_sound_waves_are_on` | S07, S13 |  |
| test_redesign.py:128 | `test_a_wall_device_is_fixed_with_its_back_on_the_wall_face` | S08, S13 |  |
| test_redesign.py:145 | `test_two_devices_at_one_wall_share_it_side_by_side_without_passing_its_corner` | S14 |  |
| test_redesign.py:173 | `test_an_ip_rated_emergency_light_is_the_drawings_e_made_weatherproof_as_a_new_block` | S13, S20 |  |
| test_redesign.py:199 | `test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved` | S10, S15, S18 | also PINS: a proposed review change is drawn (line 213) |
| test_redesign.py:224 | `test_a_library_block_is_brought_in_from_its_file_only_by_the_first_insert_and_noted` | S20, S21 |  |
| test_redesign.py:239 | `test_a_typical_plans_floors_get_one_module_each_item_stacked_and_the_unplaceable_listed` | S10 | S09 stubbed (I.build monkeypatched) |
| test_redesign.py:273 | `test_a_module_goes_on_the_nearest_real_wall_turned_to_it_past_an_equipment_outline` | S08, S10, S14 |  |
| test_redesign.py:295 | `test_coordination_is_always_done_the_engineers_moves_and_the_modules_notes_included` | S14, S15 |  |
| test_drawing_prep.py:37 | `test_a_room_is_filled_inside_its_walls_its_door_closed_and_a_pump_sets_outline_not_a_wall` | N04 |  |
| test_drawing_prep.py:46 | `test_coverage_is_measured_at_the_radius_and_the_best_spots_cover_the_room` | N05 |  |
| test_drawing_prep.py:60 | `test_a_detector_spot_keeps_off_the_columns` | N03, N05 |  |
| test_drawing_prep.py:68 | `test_the_coordination_moves_a_ceiling_device_off_a_column_and_a_wall_device_along_its_wall` | S14, N07 |  |
| test_drawing_prep.py:86 | `test_the_platform_proposes_the_best_spots_and_the_detectors_the_room_still_needs` | N05, N07 |  |
| test_drawing_prep.py:101 | `test_the_coordination_agents_layout_is_refused_when_it_covers_less_than_the_platforms` | N06 |  |
| test_drawing_prep.py:121 | `test_the_agents_answers_are_kept_to_what_they_were_shown_and_their_words_checked` | N06, N09 |  |
| test_drawing_prep.py:140 | `test_a_detector_added_for_coverage_or_rejected_by_the_orchestrator_is_drawn_only_once_approved` | S18, N07, N09 | PINS: a proposed review change is drawn, a rejected one is not (lines 142-146) |
| test_drawing_prep.py:149 | `test_with_the_agents_off_a_change_goes_to_the_reviews_point_with_the_drawings_symbol_named_like_it` | N02 |  |
| test_drawing_prep.py:161 | `test_the_gate_is_the_platforms_count` | N10 |  |
| test_drawing_prep.py:215 | `test_the_coordination_agent_and_the_orchestrator_run_side_by_side_through_the_call_path` | N01, N06, N07, N09, N10 |  |
| test_drawing_prep.py:328 | `test_the_devices_job_with_the_agents_off_places_coordinates_and_covers_without_a_model` | S15, S16, S18, S19, N01, N02, N03, N05, N07, N10 | plan job only; engineer approve/skip via PATCH; no Apply |
| test_drawing_prep.py:389 | `test_the_devices_job_with_the_agents_on_runs_them_on_the_preparation_route` | S12, N01, N02, N06, N09 |  |
| test_drawing_prep.py:416 | `test_a_devices_job_after_the_review_lost_its_answers_keeps_every_change_and_the_engineers_word` | S15, S16, N13 |  |
| test_drawing_review.py:35 | `test_rooms_are_read_off_the_plotted_plan` | S05, S06 |  |
| test_drawing_review.py:43 | `test_the_models_answer_is_kept_only_where_it_is_well_formed` | S06 |  |
| test_drawing_review.py:62 | `test_a_drawing_is_reviewed_and_each_finding_is_the_engineers_to_settle` | S06, N13, N14, N16 | plot stubbed; also the review XLSX, markup PDF, bulk accept |
| test_drawing_review.py:174 | `test_stair_detection_is_wanted_about_every_five_floors_not_on_each` | S06 |  |
| test_drawing_review.py:192 | `test_the_engineers_rulings_settle_the_same_change_elsewhere_and_go_to_the_model` | N16 |  |
| test_drawing_review.py:240 | `test_the_ifc_signs_are_checked_against_the_fls_drawing_of_the_same_floor` | S06 | plot/FLS render stubbed |
| test_drawing_review.py:296 | `test_the_plot_is_tied_to_the_drawing_by_the_texts_both_carry` | S05 |  |
| test_drawing_review.py:317 | `test_a_driveway_sounder_flasher_is_asked_for_only_past_12_m` | S05, S06 |  |
| test_drawing_review.py:339 | `test_a_decision_goes_to_the_same_comment_on_the_other_floors_and_is_undone_with_it` | N14, N16 |  |
| test_drawing_review.py:389 | `test_staircase_speakers_go_on_alternate_floors` | S06 |  |
| test_drawing_review.py:409 | `test_an_emergency_light_in_a_garbage_room_is_to_be_deleted` | S06 |  |
| test_scoped_drawing_review.py:107 | `test_the_scoped_run_asks_about_the_named_floor_alone_and_puts_every_setting_back` | N17 |  |
| test_scoped_drawing_review.py:151 | `test_a_scoped_run_whose_calls_all_fail_keeps_the_answers_and_decisions_and_puts_everything_back` | N13, N17 |  |
| test_scoped_drawing_review.py:182 | `test_a_run_that_breaks_off_fails_its_job_and_still_puts_everything_back` | N17 | review job (runners.run_drawing_review), not the redesign runner |
| test_scoped_drawing_review.py:205 | `test_the_scoped_run_refuses_before_asking_anything` | N17 |  |
| test_scoped_drawing_review.py:245 | `test_the_guard_counts_every_call_refuses_one_past_the_limit_and_stops_on_more_than_it_should` | N17 |  |
| test_scoped_drawing_review.py:329 | `test_an_acceptance_stays_only_while_the_proposal_is_the_same` | N14 |  |
| test_scoped_drawing_review.py:374 | `test_a_decision_made_before_proposals_were_kept_stands_only_until_a_review_runs` | N14 |  |
| test_scoped_drawing_review.py:408 | `test_a_window_the_model_answered_for_some_rooms_is_not_done_and_is_asked_again` | N13 |  |
| test_scoped_drawing_review.py:427 | `test_the_cli_is_given_the_turn_limit_and_its_turns_are_counted` | N18 |  |
| test_scoped_drawing_review.py:455 | `test_looks_go_one_at_a_time_so_a_stop_keeps_the_next_from_being_sent` | N17 |  |
| test_scoped_drawing_review.py:479 | `test_the_continuation_asks_only_what_is_left_and_keeps_what_was_answered` | N13, N17 |  |
| test_scoped_drawing_review.py:526 | `test_a_plan_pass_finding_the_room_review_has_is_merged_not_shown_twice` | N15 |  |
| test_scoped_drawing_review.py:543 | `test_the_clis_own_account_of_a_call_is_kept` | N18 |  |
| test_drawing_review_outcome.py:82 | `test_the_models_finding_reaches_the_review_page_through_the_worker_the_database_and_the_api` | S02, S06, N13 | worker, DB and API; fake model |
| test_drawing_review_outcome.py:131 | `test_a_plot_with_no_model_to_call_is_blocked_and_keeps_the_answers_and_decisions_before_it` | N13, N18 |  |
| test_drawing_review_outcome.py:158 | `test_a_plot_whose_every_look_fails_is_failed_and_keeps_what_was_there` | N13 |  |
| test_drawing_review_outcome.py:177 | `test_a_completed_review_with_no_findings_says_so_with_the_rooms_it_read` | N13 |  |
| test_drawing_review_outcome.py:187 | `test_the_disabled_providers_placeholder_saved_as_done_is_not_a_review_and_is_asked_again` | N13, N18 |  |
| test_drawing_review_outcome.py:223 | `test_an_exact_model_task_gets_no_answer_from_the_disabled_provider_and_none_is_stored` | N18 |  |
| test_drawing_review_outcome.py:256 | `test_the_drawing_reviews_own_switch_calls_the_model_for_the_review_alone` | N01, N18 |  |
| test_drawing_review_outcome.py:292 | `test_a_blocked_attempt_on_a_partly_reviewed_drawing_leaves_it_partial` | N13, S02 |  |


### D2. Per stage (RD-M1 S01-S25 and new N01-N18)

| Stage | Name | Tests in the five files | Partial / note |
|---|---|---|---|
| S01 | Drawing registration | 0 |  |
| S02 | Drawing/source selection | 2 |  |
| S03 | Source hashing | 0 |  |
| S04 | CAD/PDF/IFC extraction (plot) | 0 |  |
| S05 | Sheet/floor detection; plot-model tie | 3 |  |
| S06 | Room/geometry discovery (review) | 9 |  |
| S07 | Existing symbol discovery | 3 |  |
| S08 | Wall extraction and caching | 2 | query side only (Walls); build()/caching untested |
| S09 | Interface schedule ingestion | 0 | (none in the five files; test_fa_interfaces.py and test_fa_evidence.py cover the schedule itself) |
| S10 | Device/module identification | 3 |  |
| S11 | AI input construction | 1 |  |
| S12 | AI placement proposal | 2 |  |
| S13 | Deterministic placement conversion | 8 |  |
| S14 | Coordination | 4 |  |
| S15 | Manual engineer changes | 4 | approve/skip through PATCH only; adjust with candidate/symbol/point/rotation untested |
| S16 | Plan persistence | 2 |  |
| S17 | Preview rendering | 0 |  |
| S18 | Approval/rejection state | 3 |  |
| S19 | Apply job creation | 1 | plan job only; the Apply job is never started |
| S20 | CAD script generation | 4 |  |
| S21 | Block/library dependency | 1 | script text only; a missing or unreachable library path is untested |
| S22 | AutoCAD execution | 0 |  |
| S23 | Output verification | 0 |  |
| S24 | Output registration | 0 |  |
| S25 | Error handling and retry | 0 |  |
| N01 | Prep switch, provider, run record | 4 |  |
| N02 | Placement agents / platform fallback | 3 |  |
| N03 | Column index | 2 | Columns.hit/near only; build_columns/load_columns untested |
| N04 | Room fill | 1 |  |
| N05 | Coverage measure, best spots, grouping | 4 |  |
| N06 | Coordination agent | 4 |  |
| N07 | Platform coordination + coverage detectors | 5 |  |
| N08 | Coverage re-measure after edit | 0 |  |
| N09 | Orchestrator floor review | 4 |  |
| N10 | Preparation gate | 3 |  |
| N11 | Draftsman markup PDF | 0 |  |
| N12 | Interface verification gate | 0 |  |
| N13 | Review outcome, resumable looks | 11 |  |
| N14 | Decisions kept to proposal | 4 |  |
| N15 | Pass-finding merge | 1 |  |
| N16 | Rulings | 3 |  |
| N17 | Scoped review run | 7 |  |
| N18 | Review/prep model route | 6 |  |


**Count of stages with no test in the five files: 12 of 43** - RD-M1 stages S01, S03, S04, S09, S17, S22, S23, S24, S25 (9) and new stages N08, N11, N12 (3). Only partly pinned: S08, S15, S19 (plan half only), S21, N03 (5).

Other tests outside the five files that reach these stages (found by grep, not re-read in full): test_fa_evidence.py:672-720 (N12: `keep_interfaces`/`restore_kept` byte for byte, `add_interfaces` refuses an unverified schedule); test_fa_interfaces.py and test_fa_evidence.py (S09); test_worker_runtime.py:83-98 (an IFC worker whose provider module predates `get_prep_provider` fails at start); test_ifc_worker_and_ai.py (job runner generically; `grep redesign` finds nothing there, so RD-M1's tests-column entry for S19/S25 does not cover the Redesign runner). Nothing in backend/tests calls `redesign.service.apply`, `cad.apply`, `POST .../apply/jobs`, `redesign.markup.build`, `PR.measure_again` or `R.adjust` with a point/symbol/rotation (grep). Synthetic geometry only: no test uses a DXF/DWG file (`source.write_bytes(b"0\nEOF\n")` stub in test_drawing_prep.py `_devices_job`; blank 2000x2000 pt PDF; hand-built `Walls`/`Columns`).

**Tests that pin behaviour this survey proposes to change:** test_redesign.py:213 and test_drawing_prep.py:142-146 (proposed review changes are drawn; C02), test_drawing_prep.py:416 (changes whose finding vanished are kept; C08). Changing C02 means changing those assertions on purpose.

## 6. Table E - Golden Case status (GC-01)

GC-01 = project 5 / EP-30880 / IFC drawing 1 / redesign row 1 (RD-M1 GOLDEN-CASE-SELECTION.md, BASELINE-MANIFEST.json `golden_case`, evidence E16). "GC01:" is the case's upload folder on the RD-M1 machine.

### E1. What is in this repository and verifies

| Item | RD-M1 identity | In this repo | How checked now | Evidence file holding the hash |
|---|---|---|---|---|
| Module library CR.dwg | sha256 d0b4cd2244d45ae5913a8e01b3eb1ff623333bdc5f03598a8d2f77f9536e888a, 40,613 B | yes, backend/app/redesign/library/CR.dwg | `sha256sum` equal | E16, BASELINE-MANIFEST.json `redesign_library` |
| Module library CT1.dwg | f43361eab514f2c718e9e1d5dca9d87fe4d58761411fcf6967c549f5f795e3b8, 39,653 B | yes | equal | same |
| Module library CT2.dwg | 7afd3a163ec433253eabab7864c27e258726f1c60d34348e2f12a9a84a664686, 39,365 B | yes | equal | same (and `golden_case.files.lib_CT2`) |
| modules.json | manifest 3dddf8e7a81794877aa28b515222580840ea5646a3a6f67b1b9acee07cec5c05 (728 B, CRLF) | yes, now 27acf22d8491d56b5a59703b74e9135c13eddab678404c3ff459e8873e2fdcc8 (690 B, LF) | LF to CRLF conversion reproduces the manifest hash | E16, manifest |
| RD-M1 code | `code_files` hashes | 29 of 35 non-DWG files recoverable from git b5c2222 (conftest.py af7de8f, test_ifc_worker_and_ai.py eb057eb); 6 not recoverable (config.py, interfaces/{export,pdf,service,visual}.py, test_fa_interfaces.py) | blob hash equals manifest hash | BASELINE-MANIFEST.json |
| RD-M1 package | PACKAGE-MANIFEST.json, 78 files | yes | 73 exact, 5 equal after CRLF restoration (FAILURE-INVENTORY.csv, E04, E08, E12, E18), 0 missing | PACKAGE-MANIFEST.json |
| Evidence JSON E01-E18 and 17 scripts | per package manifest | yes (docs/milestones/redesign/RD-M1/evidence/) | as above | PACKAGE-MANIFEST.json |
| Renders and crops | 13 pairs: 8 PNG in renders/, 18 in crops/ | yes | 26 of 26 equal the sha256 in E17 | E17-render-index.json |
| Stored plan as data | 31 review changes, 200 interface changes, redesign row, jobs, usage | yes as extracts (E03, E06 98 KB, E07 80 KB, E02, E09, E14) | files present; content not re-derived | PACKAGE-MANIFEST.json |
| Apply failure evidence | script lines with PC-A library path, AutoCAD log tail | yes, redacted (E01, E05, E13) | read | E01, E05, E13 |

### E2. What is NOT in this repository

| Item | Identity (full hash where RD-M1 recorded it) | Holder of the hash |
|---|---|---|
| Source DWG `GC01:ifc/60de2a377daa.dwg` | 66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21, 4,380,643 B (= review and redesign `source_sha256`) | E16; manifest `golden_case.files.source_dwg` |
| Source DXF `GC01:ifc/60de2a377daa.dxf` | dbe7900f21033b2a9c5d3379c93cbf56250735143f8a424559b09a9d4ee5c14f, 28,233,874 B | E16; manifest |
| Six trade DXFs `GC01:interfaces/*.dxf` | 686438ed...0a8b (43,212,344 B), a8710daa...e5da (29,851,807), c9691cab...248c (24,670,328), 314728442...c2df (40,470,768), 044c709a...62f9 (23,200,065), ab3edfe5...01fd (31,609,477): full values in E16 | E16 |
| Review plot `GC01:review/66043c11fab9eaf5a1768ba2.pdf` (20 pages) | 2dd28b0480adcd2beb47dab31558ee5dc88fec72334c0add48a1fd1a5a9f2dae, 13,598,514 B | E16; manifest `review_pdf` |
| Wall index `GC01:redesign/walls-1-66043c11fab9eaf5-v1.pkl` | 9e5a94c17fa2573faaed31c4c909673ac8ce49cbb420fcb6b1c82647d8ec6197, 4,220,035 B | E16; manifest `wall_index` |
| Original failing Apply script `redesign/work-1/redesign.scr` | e2daf55bfe7edf4f9d0f93d0c646135b5eb4c9119bfd7b3af37e854ef9d019a0, 11,283 B; only the redacted E01 is here (hash differs by design) | E16, E18 (regenerated byte-identically from the DB snapshot in RD-M1) |
| DB snapshot `ep_platform.audit-snapshot.db` | b50dfe2b14ae381158cb47778651f8ce9bcf3dbed985e7b3af81a0821a8df8f0, 332,709,888 B (alembic c5e7a9b1d3f5; 108 review_rulings, 1,139 result_cache rows) | E12, manifest `database` |
| 17 earlier applied DWGs | e.g. `... Redesign 2026-10-02 1625.dwg` 4a512056e70b64e62198bf33e04f329cfc87fbd221f810ec6b9fd346eaac8664 | E16 |
| AutoCAD logs, `ErrorReports` | cer.log cef383c2...9b37 | E16 |

Fixtures and synthetic input: backend/tests/fixtures holds four JSON files (boq_ep30784.json, boq_ep30784_golden_v1.json, ve_ep24601_tower_a.json, ve_ep29495.json): BOQ and variation data, nothing for Redesign. `find` for *.dxf and *.dwg returns only the three library blocks. The five test files build their geometry in code (a hand-made `Walls`/`Columns` grid, a 2000 x 2000 pt blank PDF, a 1 pt = 0.1 m geometry, a 20 x 10 m "store"), and `_devices_job` writes a stub DXF (`b"0\nEOF\n"`). So no test exercises a real DXF, a real plot, a real wall index, or the module library DWGs.

### E3. What that means for GC-01's sub-cases

| Sub-case | Reproducible from this repository alone? |
|---|---|
| GC-01a modules CT1/CT2/CR, failed Apply (F001) | Evidence only: library hashes, E01/E05 script text and paths, E02/E13 logs. The byte-identical regeneration (E18) needs the DB snapshot. Not executed here. |
| GC-01b-i (wall devices on non-wall geometry, wrong room, doors, typical plans, orientation) | Images only (crops/, renders/ verified by hash) plus change JSON in E06/E07. Any code re-run needs the DXF, plot, DB. |
| GC-01j previous Apply success | Hashes only (E16); DWGs not present, not renderable without AutoCAD/ODA. |
| GC-01k AI repeated answers | E08 (stored data, 2 of 31 changes). |

**New-surface baseline: no Golden evidence exists.** GC-01 predates Drawings Preparation: the RD-M1 snapshot has alembic `c5e7a9b1d3f5`, so no `project_redesign.run` column (migration e6a8c0b2d4f6 came later), no columns index (VERSION 2 pickle), no coverage figure, no orchestrator verdict and no gate for it. A delta baseline for N01-N11 needs a fresh plan on the GC-01 drawing, which needs the DXF, plot, wall index and DB. The agents-off path (N02 fallback + N03-N05 + N07 + N10) calls no model and is the natural first deterministic re-run; whether it is stable run to run is not tested here.

## 7. Unknowns

1. **Nothing was run by this survey.** Every "CONFIRMED (code)" is a reading of source. The test suites pass (116, ep-test-runner, 4bab8d2) but they pin current behaviour, including the behaviour C02 and C08 call defects; no UI, AutoCAD, DB or model was exercised by anyone.
2. **Exact RD-M1 text of six files** (core/config.py; interfaces/export, pdf, service, visual; test_fa_interfaces.py): no git blob matches the manifest hash, so their deltas are measured against b5c2222 (taken 2026-10-04 13:41, after the RD-M1 audit of 2026-10-03). Interfaces/service.py differs from b5c2222 by 2,660 B from the manifest copy; that part of the history is not diffable.
3. **Real switch values** (AI_ENABLED, PREP_AI_ENABLED, DRAWING_REVIEW_AI_ENABLED, ai_policy per project) on any deployment: `.env` not read. RD-M1 recorded AI_ENABLED=true and project 5 ai_policy=allowed on the G copy; under that, prep agents run (C22) and C15 was not exposed.
4. **GC-01 drawing units** (C11), and whether the raw-layer reading in coverage.py:136 matches the effective layer for GC-01's boundary layers (RD-M1 E10/E11 show raw `0` vs effective `29-PARKING` for walls; boundary layers were not examined).
5. **Engineering rules in code**: radius 6.3 m (smoke and heat), 1% / 0.5 m2 tolerance, 0.5 m wall clearance, 0.3 m column gap, 15 m / 1,500 m2 limits are set "by the engineers, 6 October 2026" (config.py:431-436, coverage.py) with no standard cited in code; not assessed against NFPA 72, the UAE Fire Code or any project specification.
6. **Model behaviour**: prompts of the coordination and orchestrator agents were read, not evaluated; no answer from either exists in this repository.
7. **ProjectDrawingReviewPage.tsx** (848 lines, +94/-19 since b5c2222) and RedesignPanel/AgentRunPanel were read only at the lines cited; the pages were not run.
8. **Concurrency**: whether a PATCH during a running plan job is lost (C07/F032; S2 s7.1 #4) is code reasoning only.
9. **interfaces/*** beyond the Redesign-facing contract (workflow, findings, evidence, geometry, render, cases_pdf) belongs to S1; the new interface `anchor` contract (equipment symbol centre or None) was read, its accuracy was not.
10. **RD-M2 candidate** (G drive) exists in this repository only as documents (docs/milestones/redesign/RD-M2*); its code is not in the tree, so what its integration would change in the new prep code (gate, `confirm`, drawn set) is unassessed.
11. **Pickle trust**: wall and column indexes are `pickle.load`ed from uploads (walls.py:195, coverage.py:170); who can write there is S2 s7.1 #8, still unknown.
12. **Roadmap working copy**: other sessions were changing docs/ in the same working tree while this survey ran (docs/UNIFIED_MASTER_ROADMAP.md and three M1-refresh files show as modified, `evidence/verification-02/` as untracked; `git status -- backend frontend` is clean). The roadmap's s3/M2/M5/M8/M10/M12 text was read as it stood during the survey.

### Corrections and additions to S2 found while reusing it

- S2 Table A rows PREP.change / PREP.run cite `review/prepare.py`: the file is `backend/app/redesign/prepare.py`.
- S2 Table A row PREP.plan_run says the agents run "only when PREP_AI_ENABLED": `prep_ai_on()` is `ai_enabled or prep_ai_enabled` (ai/provider.py:920-924) (C22).
- S2's `rds.py` line numbers spot-checked at HEAD and correct: `_drawn` 695-701, `plan` 1145, `apply` 1479, `view` 1535, `interfaces_verified` 503, `_review` 80.
- S2 s7.2 #7 and Table E row 10 (Apply draws unapproved changes; plan not re-checked against the review) are confirmed; this survey adds the asymmetric re-plan (rds:1179-1194, C08), the agents-off creation path (C02/C03) and that the gate is not even surfaced to the Apply button (C01).
- S2 s7.2 #5-#6 (rulings company-wide) are confirmed; added: ruling matching ignores the device (C17), bulk accept records rulings (C18), RD-M1's snapshot already held 108 rulings.

