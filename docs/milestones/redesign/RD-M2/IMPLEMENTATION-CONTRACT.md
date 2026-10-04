# RD-M2 Implementation Contract

Written for the RD-M2 implementation agent and the independent RD-M2 reviewer.

## Where the candidate is

The owner's G-drive API (`127.0.0.1:8001`) runs `uvicorn --reload --reload-dir app` from `ep-platform\backend`. Any edit to `backend/app` in the live tree would **hot-reload a running service**, which the RD-M2 stop conditions forbid. The candidate was therefore built and tested only in an isolated copy:

| Copy | Purpose | Identity |
|---|---|---|
| `base` | Unchanged copy of the live `backend/{app,tests,alembic,*.ini,requirements.txt}` and `ProjectRedesignPage.tsx` | 380/380 files equal to the RD-M2 T0 baseline hashes |
| `cand` | The RD-M2 candidate | the same copy plus the changes in `CHANGE-MAP.md`; frozen hashes in `evidence/candidate-files.json` (v2.1; v1 and v2 manifests in `evidence/candidate-files-v1.json`, `-v2.json`) |
| `iso`, `iso2/main`, `iso2/erase` | AutoCAD validation sessions 1 (v1) and 2 (v2) | the frozen candidate placed under `code (2)/backend`, plus fresh copies of the RD-M1 snapshot DB and the GC-01 DWG/DXF |

The deliverable is `evidence/rdm2-candidate.patch` (a unified diff from `base` to `cand`). **It has not been applied to the live tree.** Applying it is the owner's step and is described in `NEXT-MILESTONE-HANDOFF.md` (stop or accept the reload of the :8001 API and restart the IFC worker, which has no hot reload).

Git: `ep-platform` HEAD `13eb73ce85e5ac55c14303efe9d8511090ace723`, branch `main`. The Redesign code is untracked, so the candidate's identity is its file hashes (`evidence/candidate-files.json`), not a commit.

## Owner decisions implemented

| # | Decision | Where |
|---|---|---|
| 1 | Draw only `approved`; never `proposed`, `skipped` or any other status; no implicit approval through the review | `_drawn()` and `requires_confirmation()`, `APPROVED-DRAWN-SET.md` |
| 2 | No archive publication; a unique, versioned platform output | `apply()` no longer writes `<project folder>/03- Drawings/Redesign`; `_unique_output()` and `_publish()`, `OUTPUT-VERIFICATION.md` |
| 3 | One isolated AutoCAD validation run | `AUTOCAD-VALIDATION.md` |
| 4 | Stored office-PC paths kept as history; CT1/CT2/CR resolved from the running code's library by interface code | `module_library()` and `to_cad()`, `PORTABLE-LIBRARY-RESOLUTION.md` |
| 5 | Refuse to publish when the change set or approvals changed after the Apply snapshot | `content_fingerprint()`, `_snapshot()`, `_refusal()`, `CONCURRENCY-GUARD.md` |

## In scope (findings)

F001, F002, F003 (exposure only), F004, F016, F017, F023, F033, F034, F035, the Apply part of F032, and as a consequence part of F030 (Apply no longer re-places or re-coordinates; see `CONCURRENCY-GUARD.md`).

## Not changed (out of scope, unchanged in the candidate)

Wall index and layer filtering (`walls.py`), room/building containment, candidate generation (`_prepare`), interface anchoring (`_interface_changes`), coordination (`coordinate`), coverage rules, obstacles, AI prompts, schema, confidence and model (`ai.py`), Plan (`plan()`), GET-side writes (`view()` still calls `state()`/`review.build()`), general Plan/PATCH concurrency, deployment, and archive publication. `git diff` evidence: `walls.py`, `ai.py`, `app/review/*`, `app/interfaces/*` and `services/jobs.py` are byte-identical in `cand` (`evidence/candidate-files.json`).

## Safety rules followed

No write to the live DB, the live uploads, the source DWG or the archive. No call to a live endpoint. No service started, stopped or reconfigured. No commit or push. The RD-M1 package was not modified: its 78-file manifest was verified at the start and at the end (`DATA-SAFETY-REPORT.md`).
