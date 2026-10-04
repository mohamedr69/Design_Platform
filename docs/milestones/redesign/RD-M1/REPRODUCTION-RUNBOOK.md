# Reproduction Runbook (RD-M1 baseline, offline)

Reproduces the RD-M1 baseline **without touching live data, without a model call and without AutoCAD**. All scripts are in `evidence/scripts/` (user-profile paths redacted). **Copy them to `ISO/scripts/`**: `render_case.py`, `wall_layers.py`, `effective_layer.py`, `analyse_changes.py`, `ai_variation.py`, `dump_case.py` and `reproduce_apply_input.py` resolve `ISO/src`, `ISO/work`, `ISO/code` and `ISO/hash` relative to their own folder (`HERE/..`), so they do not run from `evidence/scripts/`. `invisible_flag.py` holds an absolute DXF path. **Do not run** `build_evidence.py`, `findings.py`, `package_check.py`, `patch_findings_review1.py`, `patch_docs_review1.py` or `patch_review2.py` against the package: they are the producer's package-writing tools, kept as provenance. Edit the absolute constants at the top of `q.py`, `snapshot_db.py`, `hash_tree.py` and `invisible_flag.py`.

## 0. Ground rules

- `ISO` = a folder **outside** the repository and outside anything the platform reads (`DATA_ROOT`, `UPLOADS_ROOT`, `backend/`). RD-M1 used the session scratch folder on C:.
- Never start the API or a worker against `ISO`. Never open a copied DWG in AutoCAD with save enabled.
- Python: the same CPython 3.12.10 venv the G-drive services use (or any 3.12 with ezdxf 1.4.4, PyMuPDF 1.28.2, Pillow 12.3.0). Always set `PYTHONDONTWRITEBYTECODE=1`.

## 1. Fixed inputs

| Input | Identity | How obtained in RD-M1 |
|---|---|---|
| Code | the working-tree files hashed in `BASELINE-MANIFEST.json` (`code_files`); git HEAD `13eb73ce85e5ac55c14303efe9d8511090ace723` + untracked Redesign files | copied to `ISO/code/backend` with `tar --exclude=__pycache__`; verified 379/379 hashes |
| DB snapshot | `ep_platform.audit-snapshot.db`, sha256 `b50dfe2b14ae381158cb47778651f8ce9bcf3dbed985e7b3af81a0821a8df8f0`, 332,709,888 B, alembic `c5e7a9b1d3f5`, integrity `ok` | `snapshot_db.py` (SQLite backup API from a `mode=ro` source) at 2026-10-03T15:48:50Z–15:49:01Z |
| Source DWG | GC01 `ifc/60de2a377daa.dwg` sha256 `66043c11…ec21` | read-only copy not needed (hash only) |
| Source DXF | GC01 `ifc/60de2a377daa.dxf` → `ISO/src/EP-30880/source.dxf` | `cp -p`; hash = E16 |
| Review plot | GC01 `review/66043c11fab9eaf5a1768ba2.pdf` → `ISO/src/EP-30880/review-plot.pdf` | `cp -p`; hash = E16 |
| Wall index | GC01 `redesign/walls-1-66043c11fab9eaf5-v1.pkl` → `ISO/src/EP-30880/walls.pkl` | `cp -p`; hash = E16 (a pickle: load only this platform-made file) |
| Failed Apply script | GC01 `redesign/work-1/redesign.scr` → `ISO/src/EP-30880/redesign-work-1/redesign.scr` | `cp -p`; sha256 `e2daf55bfe7edf4f9d0f93d0c646135b5eb4c9119bfd7b3af37e854ef9d019a0` |
| Configuration | none of `.env` is needed; secrets never copied. Scripts set `DATABASE_URL=sqlite:///:memory:`, `AI_ENABLED=false`, temp roots | – |
| AI | **disabled**; stored answers replayed from `project_redesign.changes[*].ai` and `result_cache` (task `fa_drawing_redesign`, prompt `drawing-redesign-2026-10-02.4`, model `claude-opus-5-5`) | – |

If you take a new snapshot, the live DB will have moved on: compare `E12` table counts and expect differences only from activity after 2026-10-03T15:49Z.

## 2. Steps and expected outputs

| # | Command (from `ISO`) | Expected output |
|---|---|---|
| 1 | `python scripts/snapshot_db.py ISO/db/ep_platform.audit-snapshot.db` (only if re-snapshotting) | `integrity_check: ok`; `journal_mode: wal`; `snapshot_total_changes_during_checks: 0` |
| 2 | `python scripts/dump_case.py` | `work/case/*.json` (7 files) |
| 3 | `python scripts/analyse_changes.py` | `drawn_total 11`; status_by_source `interface|proposed 146, interface|failed 47, review|skipped 27, interface|approved 7, review|approved 4`; 6 library paths not on G: (5 approved); 0 overlapping symbol pairs |
| 4 | `python scripts/ai_variation.py` | 33 cache rows, 31 changes, 2 with two differing answers |
| 5 | `python scripts/render_case.py work/renders work/render-spec.json` (spec = `evidence/E17-render-index.json` ids/boxes) | 13 PNG pairs; SHA-256 equal to `E17` (re-render verified identical in RD-M1) |
| 6 | `python scripts/wall_layers.py '<probes>'`, `python scripts/effective_layer.py '<probes>'` (probe JSON in `COMMANDS.md`), `python scripts/invisible_flag.py` | `segments_kept_total 92093`; probe `invisible-rect-left-edge` → layer `0` / effective `…$0$29-PARKING` via `*U442`; 4,351 invisible-flag segments. (`effective_layer.py` reports layer visibility only, not the entity invisible flag.) |
| 7 | `"<venv>\python.exe" scripts/reproduce_apply_input.py` (uses `ISO/code/backend`, in-memory DB) | `coordinate_seen_differences: []`; `drawn_changes: 11`; `byte_identical: true`; regenerated sha256 `e2daf55b…19a0` |
| 8 | `cd ISO/code/backend && python -m pytest -p no:cacheprovider tests/test_redesign.py tests/test_drawing_review.py tests/test_fa_interfaces.py tests/test_ifc_worker_and_ai.py` | 78 passed |
| 9 | `python scripts/hash_tree.py ISO/hash/AFTER.json` then compare with the T0 baseline | only the RD-M1 package and the owner's live logs/DB/WAL differ (see `DATA-SAFETY-REPORT.md`) |

## 3. Known nondeterminism

| Part | Deterministic? | Note |
|---|---|---|
| Geometry fit, wall index, symbols, placement conversion, coordination, script text | Yes | step 7 proves coordination and script generation from the stored plan |
| Fresh model answers | **No** | F028: 2 of 31 changes already have two differing cached answers; a fresh Plan may differ. RD-M1 made no model calls |
| AutoCAD execution | Not exercised | result depends on AutoCAD 2027 + support paths; job 121's failure is reproduced only as input + preserved log |
| PNG renders | Yes for the same PyMuPDF/Pillow versions | |

## 4. Reproducing the Apply failure itself (not done in RD-M1)

Requires AutoCAD's Core Console on an **isolated copy** with cwd inside `ISO`. RD-M1 did not do this because `accoreconsole` writes outside the working folder (user-profile temp files, `ErrorReports`, registry) — see `DATA-SAFETY-REPORT.md`. The expected outcome, from the preserved evidence, is the job-121 log tail: `"CT2.dwg": Can't find file in search path … *Invalid* ; error: Function cancelled`, and the copy not saved.

## 5. Cleanup

Delete `ISO`. Nothing else is created: the scripts write only below `ISO`, plus Python/pytest temp folders (`ep-test-*`, `rdm1-*`) under the user's temp directory.
