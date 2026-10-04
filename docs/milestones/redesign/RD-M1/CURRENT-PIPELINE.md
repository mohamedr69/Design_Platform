# Current Redesign Pipeline (as of ep-platform HEAD 13eb73c + untracked working tree, audited 2026-10-03)

Scope: the code that the G-drive copy's API (:8001) and IFC worker run. The Redesign code is **untracked** in git (`backend/app/redesign/`, `backend/app/routers/redesign.py`, `backend/tests/test_redesign.py`, migration `c5e7a9b1d3f5_drawing_redesign.py`), so it is identified by SHA-256 in `BASELINE-MANIFEST.json`, not by commit.

Paths below are relative to `ep-platform/`. "S" = `backend/app/redesign/service.py`.

## Components

| Component | Where | Runs in |
|---|---|---|
| Page | `frontend/src/pages/ProjectRedesignPage.tsx` (584 lines) | Vite dev server (:5174/:5175 for the G copy) |
| API | `backend/app/routers/redesign.py` (9 endpoints) | uvicorn :8001 |
| Plan / adjust / coordinate / Apply orchestration | S (1,449 lines) | IFC worker (plan, apply jobs); API process (adjust, set_status, add_interfaces, view, image) |
| Model prompt + answer parser | `backend/app/redesign/ai.py` (prompt `drawing-redesign-2026-10-02.4`) | IFC worker |
| AutoCAD script | `backend/app/redesign/cad.py` | IFC worker → `accoreconsole.exe` (AutoCAD 2027) |
| Wall index | `backend/app/redesign/walls.py` | IFC worker / API |
| Module library | `backend/app/redesign/library/{CR,CT1,CT2}.dwg`, `modules.json` | read by S and AutoCAD |
| Upstream: Drawings Review | `backend/app/review/*` | IFC worker |
| Upstream: FA Interface Schedule | `backend/app/interfaces/*` | IFC worker / API |
| Upstream: IFC reading | `backend/app/ifc/*` (`resolve.resolved_drawing`, `storage`, `dxf/convert`) | IFC worker |
| Jobs | `backend/app/services/jobs.py`, `backend/app/ifc/services/runners.py:266-293` | IFC worker (`python -m app.workers.ifc_worker`) |

There is **no** Redesign-specific feature flag. Model use is governed by `AI_ENABLED` (true in the G copy's `.env`), `AI_PROVIDER=claude-code`, `drawing_review_model` (default `claude-opus-5-5`), `drawing_review_parallel` (2), `drawing_review_timeout_s` (600), the review's budget (`review._budget`), and the project's `ai_policy` (`allowed` for project 5).

## Stage map

Legend — D: deterministic; DB-R / DB-W: database reads / writes.

| # | Stage | Code | Input → Output | DB-R / DB-W | External / AI / cache | Side effects | Failure handling | Provenance kept | D? | Tests |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Drawing registration | `app/ifc` upload → `project_ifc_drawings` | DWG upload → DXF (`EP-<n>/ifc/<id>.dxf`) + DWG beside it; `units`, `groups` | W `project_ifc_drawings` | accoreconsole DWG→DXF | files under uploads | job failure | `source_sha256` column is **NULL** for drawing 1 | Yes | test_ifc_* |
| 2 | Drawing/source selection | `routers/redesign.py:41-58` (`revisions.in_force`) | project → in-force FA IFC drawings | R drawings, reviews, redesign | – | none | 404 | – | Yes | none |
| 3 | Source hashing | `review/render.py:26-48` `source_file`, `_sha`; S:1121-1123, 1373-1374 | DWG beside DXF, else archive copy, else DXF → sha256 | R review row | – | reads file | RedesignError "drawing has changed" | `source_sha256` on review + redesign rows | Yes | test_drawing_review |
| 4 | CAD/PDF/IFC extraction | `review/render.py:59-96` (plot), `ifc/dxf/convert.py` | DWG → PDF of all layouts (`review/<sha24>.pdf`) | W review `pdf_path` | accoreconsole `-EXPORT` | `review/plot-<sha12>/` work dir (left on failure) | RenderError | PDF named by source hash | Yes (AutoCAD) | test_drawing_review |
| 5 | Sheet and floor detection; plot↔model tie | `review/pages.py`; `review/geometry.py:35-104` `fit`, `fit_sheets` | PDF text vs DXF text → per sheet `{a,bx,by,residual,pairs}` (**scale+offset only, no rotation**) | W review `sheets[*].geometry` (also from GET view via `_fit`) | – | – | sheet geometry `{error}` → change "failed" | residual stored per change | Yes | test_drawing_review |
| 6 | Room and geometry discovery | review windows (`sheets[*].windows[*].rooms`) | AI review → room names/points | review row | Claude (review tasks) | – | – | room name string only; **no room polygon reaches Redesign**; sheet `plan` box = whole frame | No (AI) | test_drawing_review |
| 7 | Existing symbol discovery | `ifc/resolve.resolved_drawing`; S:97-119 `_occurrences`, S:275-312 `_symbols`, S:315-359 `_top_level` | DXF symbols → occurrences (handle, block, cx/cy, rotation, scale, layer, type); block extents & facing heuristics | R `project_ifc_drawings.groups` | ezdxf | – | blocks that cannot be measured skipped | handles stored in candidates | Yes | test_redesign (synthetic) |
| 8 | Wall extraction and caching | `walls.py:151-197`; S:178-192 `_walls` | DXF modelspace recursively decomposed; LINE/POLYLINE not matching `NOT_WALLS` on **raw** layer; entity invisible flag, layer state and viewport freeze ignored; 2 m grid | none | ezdxf | writes `uploads/EP-<n>/redesign/walls-<did>-<sha16>-v1.pkl`; process-level cache `_WALLS` | unreadable pickle → rebuilt | keyed by source sha + version | Yes | synthetic `Walls` only |
| 9 | Interface schedule ingestion | `interfaces/service.py:423-490` `build`, `_read_source`, `_item` (anchor = trade drawing's own model x,y, `:621`) | trade DXFs (`EP-<n>/interfaces/*.dxf`) + schedules → rows with `modules`, `anchor`, `floor_key` | R/W `project_fa_interfaces` | ezdxf; (scan job `fa_interfaces_scan`) | cache under interfaces | rows without anchor → "draw by hand" | row id, source drawing | Yes | test_fa_interfaces |
| 10 | Device / module identification | S:394-441 `_module_symbols`, S:503-597 `_interface_changes`, S:209-273 PREFERRED / weather / ELS rules | rows + library → module changes `if:<sha1>:<CODE><n>` with absolute `library` path | – | – | – | per-row "failed" with reason | `interface.row`, anchor | Yes | test_redesign |
| 11 | AI input construction | S:677-746 `_prepare`, `_picture`; S:1063-1083 `_ask` | change → crop PNG (RADIUS 8 m), legend crop, text: action/device/floor/room/instruction, numbered candidates (≤15), symbol list | R review PDF | pymupdf | – | sheet without geometry → change failed | prompt version; **symbol list not stored** | Yes | test_redesign |
| 12 | AI placement proposal | S:1084-1089 → `compliance/assist.call_task`; `ai.py` SYSTEM/SCHEMA | one call per pending change, thread pool `drawing_review_parallel` | W `ai_usage` (run_id NULL), `result_cache` | Claude via Claude Code CLI; cache key = (doc sha:change id, evidence fingerprint, task, prompt) | – | error → change "failed" | cached answer + model; `row.calls` | **No** | none (provider not exercised) |
| 13 | Deterministic placement conversion | `ai.py:58-81` `read_answer`; S:749-821 `_place`; S:455-500 `_nearest_wall`, `_place_module` | answer → remove (handle) / insert (block, layer, scale, rotation, model point, seen point, offset, radius, facing, library) | – | – | – | no candidate → failed | `ai` answer stored on change | Yes | test_redesign |
| 14 | Coordination | S:824-1060 `coordinate` | placed changes + candidate devices (0.25 m squares) + walls → moved seen/model points | – | – | – | **unresolved clash silently kept** | `coordinated` flag | Yes | test_redesign (2 tests) |
| 15 | Manual engineer changes | S:650-664 `set_status`; S:1196-1249 `adjust`; S:617-647 `add_interfaces`; router PATCH/POST | status / candidate / symbol / point / rotation → re-place + re-coordinate | R/W `project_redesign` | – | – | 422 on RedesignError | `moved`, `edited` flags only; **no who/when** | Yes | partial |
| 16 | Plan persistence | S:1095-1190 `plan` | all of the above → `project_redesign.changes` (JSON), `symbols`, `calls`, status | W `project_redesign` (after each answer) | – | – | exception → status failed, error | keeps approved/skipped/moved/edited verbatim (S:1134); rewrites the whole row after every answer, no concurrency control (F032) | Mixed | none for plan() end-to-end |
| 17 | Preview rendering | S:1252-1268 `image`; router `:158-169` | change → PNG crop with markers | R review row (own session) | pymupdf | `state()` may insert a row | 404 | – | Yes | none |
| 18 | Approval / rejection state | S:667-671 `_drawn`; S:1416-1449 `view`; UI `:213-215, 292` | status → drawn flag | **GET view writes**: `state()`, `review.build()` (+`_fit`), commit | – | – | – | – | Yes | test_redesign (module rule) |
| 19 | Apply job creation | router `:70-104` `_start`, `start_apply`, `jobs.enqueue` (dedup key `fa_redesign_apply:<p>:<d>`) | POST → queued job | W `background_jobs`, `activity_events` | – | – | existing active job returned | job params `{drawing_id, user_id}` | Yes | test_ifc_worker_and_ai |
| 20 | CAD script generation | S:1282-1301 `to_cad`; `cad.py:52-140` `script_lines` | drawn changes → AutoLISP `.scr` (insert at 1 to learn unit factor, `entdel (entlast)`, insert at scale/factor; markers; notes; QSAVE) | S:1376 `refresh()` **re-places and commits** first | – | – | – | script written to `work-<row id>/redesign.scr` | Yes | test_redesign (script text) |
| 21 | Block/library dependency loading | `cad.py:114-117` | `"CT2=<absolute library path>"` when the block is absent | – | AutoCAD support search path | – | none | absolute path from plan time (F001) | Yes | test_redesign (no missing-path case) |
| 22 | AutoCAD execution | `cad.py:143-163` | copy of source DWG in `work-<id>/` + script → accoreconsole `/i /s /l en-US`, timeout 1200 s | – | accoreconsole | AutoCAD writes `ErrorReports/` in cwd, temp files in user profile | timeout → CadError | log discarded on success | Yes (given same AutoCAD) | none |
| 23 | Output verification | `cad.py:165-168` | copy exists and mtime changed | – | – | – | CadError with log tail | – | Yes | none |
| 24 | Output registration | S:1383-1404; `cad.py:169-175` | copy → `uploads/EP-<n>/redesign/<stem> <rev> - Redesign <stamp>.dwg`, and a copy into `<project source folder>/03- Drawings/Redesign/` | W `project_redesign.output_*` (absolute `output_path`) | – | writes into the synced project archive | archive write failure logged only | output path, change count, time | Yes | none |
| 25 | Error handling and retry | `runners.py:266-288`; `jobs.py:351-396` `recover_stale` (MAX_ATTEMPTS 2) | exceptions → `ReadError` → job failed; stale running job → requeued | W jobs, redesign row (`output_status=failed`, `output_error`) | – | – | requeue on worker start by heartbeat age | `attempts` | Yes | test_ifc_worker_and_ai |

## Data shapes (stored)

- `project_redesign.changes[]` keys: `action, ai, at, box, candidates, confidence, coordinated, device, edited, error, floor, id, insert, instruction, interface, moved, note, on_wall, page, placeholder, remove, residual, room, sheet, source, status, system, system_name` (E03).
- `insert`: `symbol, name, code, block, layer, scale, rotation, page, model, seen, placed, offset, radius, make, library, facing`.
- `interface`: `anchor, code, depth, equipment, for, half, note_height, row, tag`.
- Statuses: `pending, proposed, approved, skipped, failed`. Drawn at Apply: approved, **or proposed when not an interface module** (S:667-671).

## Gaps in this map

- The review stages (4–6) were mapped only as far as the Redesign consumes them; the review's own AI prompts were not audited.
- AutoCAD's runtime behaviour after a LISP error inside a script (does it continue to `QSAVE`?) was not observed (no AutoCAD run in RD-M1).
- The frontend was read for API calls and wording only; no UI was run.
