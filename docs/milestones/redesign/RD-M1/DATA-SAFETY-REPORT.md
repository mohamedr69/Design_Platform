# Data Safety Report (RD-M1)

**Verdict: VERIFIED** for application code, source drawings, uploads and prior outputs, and the live database, within the limits in §7. Machine-checked results are in `PACKAGE-CHECK.json`.

## 1. Working tree

| Check | Result |
|---|---|
| Baseline T0 | 2026-10-03 19:46–19:48 (UTC+4): SHA-256, size and mtime of 740 git-visible files in `ep-platform`, 1,870 upload, library, `.env` and DB-metadata entries, and 25 git-visible files of the outer repo. The full baseline is kept outside the repo (its own sha256 is in `BASELINE-MANIFEST.json`). |
| T0 timing | T0 started ≈3 minutes after the audit began (≈19:43). The independent reviewer closed that gap: no file under `ep-platform` (venv and node_modules excluded) is newer than 19:40 except the live DB/WAL and the package; `.git/index` was touched at 19:43:30 (see below). |
| After T1 | Re-hashed after the package was written (final run recorded in `PACKAGE-CHECK.json` → `no_application_file_changes`) |
| Changed / removed | **0 / 0** of 740 pre-existing files |
| Added | Only files under `docs/milestones/redesign/RD-M1/`; **0** elsewhere |
| Outer repo | Only `worker-g.stderr.log` changed. That is the owner's running sync worker, which appends a line every minute. No other file changed. |
| Never run | `git add/commit/push/stash/reset/checkout/clean`, formatters, or any write to `.git` by command. The first `git status` ran without `GIT_OPTIONAL_LOCKS=0` and may have refreshed git's index stat cache (`.git/index`, outside the working tree); later git calls used `GIT_OPTIONAL_LOCKS=0`. |
| Caches | Tests ran on an isolated code copy with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`, so no `__pycache__` or `.pytest_cache` was written into the tree. |

## 2. Source drawings, uploads, prior outputs

- **1,867 of 1,867** upload and library files are byte-identical at T0 and T1. This covers the GC-01 source DWG/DXF, the review PDF, 6 trade DXFs, the wall index, the 17 earlier redesigned DWGs, `work-1/redesign.dwg` and `.scr`, the module library DWGs, and every other project's uploads. No file was added beside any original.
- Only **copies** in the isolated area were opened: the DXF (ezdxf, read), the review PDF (PyMuPDF, render), the wall-index pickle (loaded in an isolated process; it is a file this platform wrote itself), and the Apply script.
- `selected_source_hashes`: the GC-01 source DWG hash equals the review `source_sha256`, the Redesign `source_sha256`, and the hash of `work-1/redesign.dwg` (so AutoCAD never saved the job-121 copy).
- **AutoCAD was not run.** Its Core Console writes `ErrorReports/` into its working folder and temp/UPI files under the user profile (shown by the preserved `cer.log`), so it cannot be confined to the isolated folder. DWG TrueView was not opened.

## 3. Database

| Item | Value |
|---|---|
| Live DB | SQLite, WAL mode, in the G copy's `backend/` (relative `DATABASE_URL`, `DATA_ROOT` unset). Written by the owner's running services throughout. |
| Snapshot method | `sqlite3.Connection.backup(pages=-1)` from a source opened `mode=ro` with `PRAGMA query_only=ON`. This is one read transaction, so it gives one consistent point including WAL content. A read-only connection cannot checkpoint or truncate the WAL. |
| Snapshot time | 2026-10-03T15:48:50Z → 15:49:01Z |
| Snapshot identity | sha256 `b50dfe2b14ae381158cb47778651f8ce9bcf3dbed985e7b3af81a0821a8df8f0`, 332,709,888 B, `integrity_check = ok`, alembic `c5e7a9b1d3f5`, 77 tables (counts in `evidence/E12`) |
| Snapshot location | the session scratch folder on C:, outside the repo. No running service can use it: both deployments resolve `./ep_platform.db` relative to their own `backend/` folder. |
| Audit queries | snapshot opened `mode=ro` + `query_only`; every query asserts `total_changes == 0` |
| Live read-only probes | two probes (`mode=ro`, `query_only`, `total_changes 0`): Redesign row 1 `updated_at` is still `2026-10-03 15:28:00.097343` (before the audit began at ≈15:43Z). Max job id is 121, max activity id 972, max `ai_usage` id 729, and there are 33 `fa_drawing_redesign` cache rows — all equal to the snapshot. |
| Live DB file metadata | changed between T0 and T1 through the owner's services (WAL appends and checkpoints) — expected and not caused by the audit |
| Note | A WAL reader registers read marks in the `-shm` file. Every reader does this, including the platform's own pages. It does not change database content. |
| Private data | The DB copy, full case dumps and the full baseline are **not** packaged. The package holds derived records with host names, Windows user names and the project's name removed (`no_private_names_in_package`). |

## 4. Live jobs and services

- No Redesign endpoint was called. No job was created, retried, resumed or cancelled. Job 120 (Plan) and job 121 (Apply) had already finished before the audit began, and were only read.
- No service was started or stopped and no port was changed: :8000, :8001, :5173, :5174 and :5175 are as found.
- No platform model call was made. The visual review of rendered PNG copies was done by Claude in this audit session; it is recorded as AI-proposed findings.

## 5. Secrets

The `.env` files were read only through a redacting filter (keys, secrets, passwords and tokens replaced). They were never copied, and only non-secret settings appear in the package. The AI CLI path is mentioned only as "set".

## 6. Files created outside the repository

- The isolated area, ≈387 MB: DB snapshot, copied sources, code copy, renders, hashes and case dumps. It is kept for the independent reviewer; delete it after review.
- Python temp folders from the tests and the reproduction script (`ep-test-*`, `rdm1-*` under the user's temp directory; these are mixed with older `ep-test-*` folders from the owner's own runs).

## 7. Limits (what is not proven)

- The live DB cannot be compared by content hash, because it changes under the owner's services. Non-mutation rests on the read-only access method and on the unchanged Redesign row, job, activity, AI-usage and cache maxima.
- Whether AutoCAD can be confined to a folder was not tested; it was simply not run.
