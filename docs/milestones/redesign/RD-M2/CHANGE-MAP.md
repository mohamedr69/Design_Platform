# RD-M2 Change Map

Line numbers are in the delivered **candidate v2.1** copy (`cand/`), which is what `evidence/rdm2-candidate.patch` produces (sha256 in `PACKAGE-MANIFEST.json`). Lineage: v1 (AutoCAD session 1) → v2 (`verify.py` whole-line markers; AutoCAD session 2, passed) → v2.1 (one test assertion made exact; **application code byte-identical to v2**, see `evidence/candidate-files.json → application_code_differs_from_v2 = []`). Paths are relative to `ep-platform/`.

## Application files changed (6) and added (1)

| File | Change (+/− lines) | What changed |
|---|---|---|
| `backend/app/redesign/service.py` | +290 / −47 | `ApplyError`, `ApplyRefused` and `ApplyStale` added. The drawn-set gate `_drawn()` (713) is now approved-only, and `requires_confirmation()` (704) is added. `module_library()` (423) and `to_cad()` (1336) resolve module files from the current library and carry erase-verification data. `adjust()` (1245) gains `confirmed`. New Apply pipeline (1430–1702): `content_fingerprint`, `_snapshot`, `apply_request`, `_refusal`, `output_file_for`, `_unique_output`, `_publish` (exclusive create), `_readback`, and `apply()` rewritten. `view()` gains `requires_confirmation`, `confirmed`, `counts.drawn` and `output.available`. |
| `backend/app/redesign/cad.py` | +168 / −53 | Fail-closed AutoLISP: `ep_new_insert`, `ep_erase`, `ep_make`, `ep_fail`, guarded steps, count check before `QSAVE`, nonce-bound run-time markers. `apply()` is replaced by `run()`: a run folder of its own, a copy check, `Popen` polling with `check()`, kill on cancel/timeout, full log kept, no promotion. |
| `backend/app/redesign/verify.py` | new, 128 lines | Log parsing bound to the nonce, whole lines only (v2, after the AutoCAD validation); the expectation; DXF read-back reconciliation by handle; `verify()`. |
| `backend/app/routers/redesign.py` | +17 / −8 | `ChangeIn.confirmed`. The Apply POST records `apply_request` (source hash, fingerprint, drawn count) in the job params and refuses with 422 when nothing is approved. `output.dwg` goes through `output_file_for` (relative path, legacy rebase, traversal refusal). |
| `backend/app/ifc/services/runners.py` | +4 / −1 | The Apply runner passes `request=job.params`, `job_id` and `job_created_at` to `apply()`. |
| `frontend/src/pages/ProjectRedesignPage.tsx` | +51 / −20 | "Placed, to approve" becomes "Proposed, not drawn until approved"; "not drawn until approved" shows on every proposed change (not only modules); a "Confirm this spot" button; output states made, stale, cancelled, interrupted and making; no "filed in" wording; header text. |

## Tests changed (1) and added (1)

| File | Change | Why |
|---|---|---|
| `backend/tests/test_redesign.py` | +15 / −6, in 3 tests | Each assertion encoded behaviour the owner reversed. Every one was replaced by a **stricter** assertion: proposed review changes are not drawn; the script uses `ep_erase` and never `(entdel (entlast))` or a bare `QSAVE`; the library path is the current one and the stored path is absent from the script. No assertion was removed without a stronger replacement. |
| `backend/tests/test_redesign_apply.py` | new, 35 tests | The 20 required behaviours, the same-converter source read-back, and two regression tests built from the real AutoCAD validation logs (see `REGRESSION.md` for the mapping). |

## Files confirmed unchanged

`backend/app/redesign/{walls.py, ai.py, __init__.py, library/*}`, `backend/app/review/*`, `backend/app/interfaces/*`, `backend/app/services/jobs.py`, `backend/app/models.py`, `backend/alembic/*`. There is **no schema migration**: idempotency data lives in the job's existing `params` and `result` JSON, and the new output states fit `output_status VARCHAR(16)`.

## Behaviour removed

- The project-archive copy (`<source folder>/03- Drawings/Redesign/…`), per owner decision 2.
- `refresh()` is no longer called by Apply. Apply refuses changes placed by an earlier version ("place them again") instead of re-placing them unseen. `refresh()` itself is unchanged.
- The shared `work-<row id>` folder. Each Apply has `runs/<apply id>/`.
