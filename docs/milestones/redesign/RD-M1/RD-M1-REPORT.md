# RD-M1 — Freeze, Baseline & Failure Inventory (Redesign)

Audit date 2026-10-03 (UTC+4), PC-B (the laptop running the G-drive copy). Audit and evidence only: no application code, prompt, test, configuration, database record or drawing was changed, and no Redesign endpoint was called. All findings are **unreviewed**; AI-authored visual findings are proposals, not engineering approval. Nothing here says the Redesign feature is accurate or production-ready.

## 1. Conclusions

| # | Question | Answer |
|---|---|---|
| 1 | Baseline reproducibility | **Partly proven.** From the WAL-consistent DB snapshot and an isolated byte-identical code copy, the Apply input is regenerated **byte-identically** (sha256 `e2daf55b…19a0`, `evidence/E18`), and coordination re-run on the stored plan changes no position. All 78 tests pass, and renders are deterministic. Not reproduced: fresh AI answers (no model calls, by rule), and the AutoCAD run itself (not executed — it writes outside the isolated folder). |
| 2 | Data safety | **Verified** for code, source drawings, uploads and the live DB, within the limits stated in `DATA-SAFETY-REPORT.md`. The only new files in the working tree are inside this package. |
| 3 | Pipeline completeness | **Mapped.** 25 stages are in `CURRENT-PIPELINE.md`, with its stated gaps (review internals; AutoCAD continuation after a LISP error). |
| 4 | Golden Cases | **Sufficient for the proposed RD-M2 (Apply safety)**, **insufficient** for geometry, coordination or AI milestones: only one Redesign case exists (GC-01, 11 sub-cases). |
| 5 | Critical failures | **2.** F002: review changes still in `proposed` (AI-placed, never approved) are drawn at Apply, while the page calls them "Placed, to approve". F003: a low-confidence REMOVE whose own note says the target is in the lift lobby was accepted, and handle 5DD10 (~6.6 m away, another room) was marked for erasure; the engineer skipped it. |
| 6 | Apply blocker | **Confirmed.** 5 approved CT1/CT2 modules (all engineer-moved/edited) carry a library path persisted on PC-A (`<PC-A user profile>/OneDrive - <org>/Desktop/dev/ep-platform/…/library/CT2.dwg`), which does not exist on PC-B. AutoCAD therefore searched for `CT2.dwg` and cancelled; the copy was not saved. `CT2.dwg` itself is present in the running copy's library. Evidence: original script line 51 (= E01 line 53), E05, E13, E16, E18; cause in code at service.py:435, :600-614, :1134, :1312-1314 and cad.py:114-117. |
| 7 | Coordination limitations | **Confirmed by code:** coordination ignores existing text and notes, door swings, windows, equipment, ceilings and other disciplines; existing devices count only if they are among some change's 15 nearest candidates, each as a 0.25 m square; unresolved clashes are not flagged; there is no room or building containment; the wall index admits non-wall geometry (≈10% of segments are on a wall layer, counted by *raw* layer). **Confirmed by data and code:** two approved modules sit on parking-block geometry admitted through raw layer `0` (effective `29-PARKING`, which the wall filter would exclude by name) (F006). That this line does not plot is a *visual* observation, explained by the DXF invisible flag for the ZCV segment only; for the ELECTRIC PUMP segment it is unexplained. The wall index also takes 4,351 invisible-flag segments (F005). **Suspected:** trade-drawing anchors outside the building (F007) come from a coordinate mismatch; typical-plan mismatches (F026). |
| 8 | AI variation | **Measured, limited** (stored data only): 2 of 31 changes have two cached answers that differ (one moved ≈0.6 m; one symbol "Sounder Strobe WP" → "Wall mounted sounder"). The inputs also differed, so pure model nondeterminism is not separable. 15/31 answers state orientation uncertainty. No fresh calls were made. |
| 9 | RD-M1 verdict | **READY FOR INDEPENDENT RD-M1 REVIEW** (self-approval excluded; see §8) |
| 10 | RD-M2 authorisation | **Not granted by this task.** A bounded proposal is in `NEXT-MILESTONE-HANDOFF.md`. |

Finding counts: **Critical 2 · High 9 · Medium 18 · Low 6** (35; `FAILURE-INVENTORY.md`; F032–F035 were added after the first independent review).

## 2. Environment identity

| Item | Value |
|---|---|
| Repository audited | `G:\dev (2)\dev\ep-platform` (a nested repo; the outer `G:\dev (2)\dev` repo records it as a gitlink `d3bea8b` with no `.gitmodules` mapping) |
| ep-platform git | HEAD `13eb73ce85e5ac55c14303efe9d8511090ace723`, branch `main`; 50 modified + 58 untracked entries (`git status -uall`) at T0 (`BASELINE-MANIFEST.json`). **All Redesign code is untracked.** |
| Outer repo git | HEAD `e2d8cfdb8376599562f6ec91f519c2efb7d43f54`, branch `master`; status as in the session's start snapshot (logs modified, a sibling clone folder untracked) |
| Python (G services) | Started as `venv\Scripts\python` in `G:\…\backend`, but the running process image is the **Desktop** venv launcher → CPython 3.12.10. The G copy's `backend/venv/pyvenv.cfg` points to a Python 3.13 on PC-A that does not exist here. |
| Frontend | Node v24.14.0; Vite ^8.2.2, React ^19.2.8, TypeScript ~6.0.2 (`package.json`) |
| AutoCAD | AutoCAD 2027 (Core Console; build 26.0.118.0.0 per the CER log); DWG TrueView 2026 installed; no ODA File Converter |
| Database | SQLite in WAL mode, `G:\dev (2)\dev\ep-platform\backend\ep_platform.db` (DATABASE_URL relative, DATA_ROOT unset); alembic `c5e7a9b1d3f5` (drawing_redesign); 77 tables |
| Redesign flags | No Redesign-specific flag. `AI_ENABLED=true`, `AI_PROVIDER=claude-code`, `AI_CLAUDE_CLI` set (path only), `drawing_review_model=claude-opus-5-5`, `drawing_review_parallel=2`, timeout 600 s, max calls 300, max cost 50; project 5 `ai_policy=allowed`. Secrets were not read into the package. |
| Running services (not touched) | **G copy:** API uvicorn `127.0.0.1:8001` (pids 3644/28112), sync worker (7892), IFC worker (37964, 2 slots), Vite on :5174 (38548) and :5175 (22960, a second `start.bat` launch). **Desktop copy:** API `127.0.0.1:8000` (22592), sync/document/IFC workers, Vite :5173. A separate Codex-driven evaluator process was also running on PC-B (not related). |
| Services writing to the DB | Yes: the sync worker polls every 1.5 s and the WAL was rewritten during the audit (mtime changed, size constant); the owner's browser polled the Redesign page (`backend-g-api.stdout.log`). |
| Host aliases | PC-A = the office PC where the 2026-10-02 plan/apply ran; PC-B = this laptop |

## 3. Verification of the stated facts

| # | Hypothesis | Verdict | Correction / evidence |
|---|---|---|---|
| 1 | Frontend, API, planning, coordination, CAD, wall extraction, AI and worker components | **True** | There is no Redesign-specific worker: Plan and Apply run as `fa_redesign_plan` / `fa_redesign_apply` jobs in the **IFC worker** (`runners.py:266-293`). Adjust, approve, interfaces and preview run in the API process. |
| 2 | The current case is the recent activity on the G-drive copy | **True** | project 5 (EP-30880), drawing 1, redesign row 1; jobs 119–121 ran on PC-B on 2026-10-03 (E02, E14). |
| 3 | Apply failed because AutoCAD could not locate an interface-module DWG such as CT2 | **True, needs correcting** | The DWG exists in the running copy's library. AutoCAD was given a path to it that exists only on PC-A, persisted in 6 engineer-edited changes (F001). Both job 119 (auto-requeued) and job 121 failed this way. |
| 4 | Library files CT1, CT2, CR | **True** | `backend/app/redesign/library/{CR,CT1,CT2}.dwg` + `modules.json` (sample 1:100 mm, note height 175). |
| 5 | Coordination uses walls, footprints, bounding boxes, clearances and movement along/between walls | **True** | Plus a free 8-direction step search for non-wall items and modules. GAP 0.15 m; existing devices are 0.25 m squares; modules use their own rectangle; notes are estimated as `len × h × 0.85` (S:824-1060). |
| 6 | Doors, windows, accessibility, ceilings, coverage and external clashes may be unmodelled | **Confirmed (code)** | None of these is an input to coordination. Doors and windows are only excluded from the wall index by layer name (F008, F011, F022, F027). |
| 7 | A new Plan job may exist or may have run | **True — it ran** | Job 120 `fa_redesign_plan`, created by user 1 at 2026-10-03 15:26:46 UTC, succeeded 15:27:24 (231 changes, 146 placed, 0 model calls since every review change was already settled). Job 121 Apply followed and failed. Observed only. |

## 4. What the current baseline is

- 231 stored changes: 31 from the review (4 approved, 27 skipped) and 200 interface modules (7 approved, 146 proposed, 47 failed). Apply would draw **11** (4 review + 7 modules), all on FA 101 (3rd basement pump room).
- The engineer skipped 27 of the 31 AI-placed review changes (87%). The reasons are not recorded (F018).
- On 2026-10-02 there were 44 `fa_drawing_redesign` model calls (33 fresh, 11 cache hits). 37 of them (27 fresh, 10 cached) fall inside Plan job 102's run window on PC-A; the other 7 do not (F020). 16 Apply jobs succeeded on PC-A (103–118), and job 119 made `…1654.dwg` on PC-A before being re-run on PC-B (F017).
- Applied DWGs exist (17) but were **not inspected**: there is no ODA converter, and AutoCAD was not run. Whether earlier outputs contained unapproved review placements (F002) is therefore unknown.

## 5. Findings by stage (summary — details in the inventory)

| Stage | Findings |
|---|---|
| 5–8 geometry / wall index | F005 (High), F021, F022 (High), F015 |
| 9–10 interface schedule | F007 (High), F026, F025 |
| 12–13 AI → conversion | F003 (**Critical**), F013, F014, F028, F029, F020 |
| 14 coordination | F008 (High), F009, F010, F011, F012, F006 (High) |
| 15–19 workflow | F002 (**Critical**), F032 (High), F018, F019, F030, F017, F016, F034, F035 |
| 20–24 Apply | F001 (High, blocker), F004 (High), F023 (High), F033, F024, F031 |
| rules | F027 |

## 6. Visual review

Claude reviewed 13 pairs of renders of **copies** (`renders/`, `crops/`). Each pair has the same page box and DPI; A is the source plot, and B is the stored plan reconstructed offline. These are not applied output. Visual findings F006, F007, F009, F010, F011 and F029 are marked *proposed (visual)* in their cause status. Where geometry or code corroborates them, that is stated. No image was checked by an engineer.

## 7. Limits of this audit

- One drawing, one project (no other Redesign data exists).
- Applied DWGs are not rendered, and the AutoCAD behaviour after a script error is not observed.
- The review stage (which produces the accepted findings) was mapped only as an input.
- AI variation was measured only from stored data (2 repeated pairs).
- The Desktop deployment's DB and the project archive were not opened.

## 8. Independent review

RD-M1 requires a fresh read-only reviewer. Round 1 (a separate agent that did not produce the audit) returned **CHANGES REQUIRED**: 7 required documentation changes and 6 non-blocking notes. The core bindings, data safety, the Apply-input regeneration and F001/F002/F003/F017 were independently confirmed. Its report is reproduced verbatim in `INDEPENDENT-REVIEW.md`, followed by the producer's change log. **Round 2** (same reviewer) returned **ACCEPT WITH NOTES**: all 7 required changes PASS, F032–F035 verified against code, no new errors, and git status and non-mutation re-verified. Its 4 non-blocking notes were applied (see `INDEPENDENT-REVIEW.md`). The producer does not approve this package.
