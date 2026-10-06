# Test Results (RD-M1 refresh, unified milestone M2)

Date: 2026-10-06
HEAD at the start and during all test runs: `4bab8d267d843ef0ef21f2db99638f8c76ad891f`. When re-checked after the runs, HEAD had moved to `c1f962ac705853f94ef4e5661cf46d180a6d996b` (see the git status section); the tests ran against the tree as it was under 4bab8d2 plus the two modified docs files listed below, and this runner did not re-run anything on the new HEAD.
Run by: ep-test-runner. No application, test or documentation file was edited. Nothing was retried; every run below is the first and only run of its command.

## git status --short

Before the runs:

```
 M docs/milestones/M1/refresh-2026-10-06/M1R-DATA-OWNERSHIP-DELTA.csv
 M docs/milestones/M1/refresh-2026-10-06/M1R-DATA-OWNERSHIP-DELTA.md
```

After the runs (taken before this file was written, then re-checked after writing it; same result):

```
?? docs/milestones/redesign/RD-M1-refresh-2026-10-06/
```

The only new entry is this evidence folder. The two ` M` files under `docs/milestones/M1/refresh-2026-10-06/` were listed before the runs and were no longer listed afterwards, and HEAD moved from `4bab8d2` to `c1f962a` in the same window. This runner did not touch those files (it only wrote under `evidence/tests/` and the scratchpad) and no pytest test writes to `docs/`; another actor in the same tree most likely committed them. This runner cannot confirm that (git commands beyond `rev-parse` and `status` are not permitted) and did not check whether `c1f962a` changed any file under `backend/`. If it did, the counts here describe the tree under `4bab8d2`, not `c1f962a`. Flagged for the reviewer.

## Environment

| Item | Value |
|---|---|
| OS | Linux 6.18.44-fc-v70 x86_64, Ubuntu 24.04.5 LTS (container) |
| Python | CPython 3.13.16 |
| pytest | 8.3.4 (`pip show`) |
| ezdxf | 1.4.4 |
| pymupdf | 1.28.2 |
| SQLAlchemy | 2.0.36 |
| fastapi | 0.115.6 |
| Tesseract | not installed (`shutil.which('tesseract')` is None) |
| AutoCAD | not present |
| Archive / database | none live; fixtures create temporary SQLite databases (`conftest.py`) |
| Env for the runs | `PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT=` (empty), `-p no:cacheprovider` |
| Working directory | `/home/user/Design_Platform/backend` (the tree itself, not a copy) |

`import fastapi` succeeded; no `pip install` was needed. The package versions equal those RD-M1 recorded for its Windows interpreter (Python 3.12.10 there); only the OS and Python minor version differ.

## Commands (exact)

Combined run:

```
cd /home/user/Design_Platform/backend
PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= python3 -m pytest tests/test_redesign.py tests/test_drawing_prep.py tests/test_drawing_review.py tests/test_scoped_drawing_review.py tests/test_drawing_review_outcome.py tests/test_fa_interfaces.py tests/test_ifc_worker_and_ai.py -q -p no:cacheprovider --basetemp=/tmp/claude-0/-home-user-Design-Platform/32737463-7564-5f1d-b606-2274610299d6/scratchpad/m2r/tests/pytest-temp --junitxml=<evidence>/redesign-suites.xml 2>&1 | tee <evidence>/redesign-suites.log
```

Per file (one run per file, output to `<evidence>/<testfile>.txt`), for each of the seven files:

```
PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= python3 -m pytest tests/<testfile>.py -rA -p no:cacheprovider --basetemp=<scratch>/pytest-temp-<testfile> > <evidence>/<testfile>.txt 2>&1
```

`<evidence>` = `docs/milestones/redesign/RD-M1-refresh-2026-10-06/evidence/tests/`; `<scratch>` = `/tmp/claude-0/-home-user-Design-Platform/32737463-7564-5f1d-b606-2274610299d6/scratchpad/m2r/tests/`.

## Combined result

```
116 passed, 68 warnings in 156.14s (0:02:36)
```

The JUnit file agrees: 116 tests, 0 failures, 0 errors, 0 skipped.

## Per-file results and comparison with RD-M1

"Then" = RD-M1 `TEST-RESULTS.md` (78 tests over four files). "Now" = this run (separate `-rA` run per file; the per-file counts add up to the combined 116). All of RD-M1's skipped and error counts were 0, and are 0 now.

| File | Passed | Failed | Errors | Skipped | Warnings | Duration | Then (passed) | Now | Delta |
|---|---|---|---|---|---|---|---|---|---|
| tests/test_redesign.py | 16 | 0 | 0 | 0 | 1 | 0.10 s | 16 | 16 | 0 |
| tests/test_drawing_prep.py | 14 | 0 | 0 | 0 | 5 | 58.71 s | not run | 14 | +14 (new suite) |
| tests/test_drawing_review.py | 11 | 0 | 0 | 0 | 6 | 8.60 s | 11 | 11 | 0 |
| tests/test_scoped_drawing_review.py | 13 | 0 | 0 | 0 | 10 | 20.39 s | not run | 13 | +13 (new suite) |
| tests/test_drawing_review_outcome.py | 8 | 0 | 0 | 0 | 9 | 14.45 s | not run | 8 | +8 (new suite) |
| tests/test_fa_interfaces.py | 13 | 0 | 0 | 0 | 5 | 8.41 s | 10 | 13 | +3 |
| tests/test_ifc_worker_and_ai.py | 41 | 0 | 0 | 0 | 38 | 54.19 s | 41 | 41 | 0 |
| **Total** | **116** | **0** | **0** | **0** | 74 (per-file runs; 68 in the combined run, where pytest groups the same warnings) | 164.85 s (sum of per-file) | **78** | **116** | **+38** |

RD-M1 suites only (four files): then 78, now 81 (16 + 11 + 13 + 41), delta +3, all in `test_fa_interfaces.py`. The three added suites contribute the remaining 35 (14 + 13 + 8), so 81 + 35 = 116.

### Tests added or removed, by name

- `test_redesign.py`: the 16 test ids in this run's `-rA` listing are identical to the 16 ids in RD-M1's `evidence/tests/test_redesign.txt` (compared by sorted id). None added, none removed.
- `test_drawing_review.py` (11 then, 11 now) and `test_ifc_worker_and_ai.py` (41 then, 41 now): RD-M1 recorded these in `-q` mode, so its evidence files hold counts but no test names. Equal counts are consistent with no change, but names cannot be compared; "no test added or removed" is not established for these two beyond the count.
- `test_fa_interfaces.py` (10 then, 13 now): +3 tests. RD-M1's evidence has no test names for this file, so which three are new cannot be identified from the listings. The current file defines 13 tests; the last five in file order, all about dampers, look like later additions but that is an inference, not evidence: `test_a_damper_label_is_scheduled_as_the_drawing_shows_it_once_looked_at`, `test_damper_without_visual_result_is_held_and_text_is_not_equipment_location`, `test_visual_damper_keeps_label_and_physical_equipment_anchors_separate`, `test_a_damper_whose_symbol_is_unclear_or_shared_or_missed_by_the_model_is_held` (plus `test_a_fire_pump_room_drawn_but_not_named_gets_the_schematics_pumps_where_it_is`). Full names with outcomes are in `test_fa_interfaces.txt`.
- New suites (not run by RD-M1), all test names with PASSED are in their `-rA` files: `test_drawing_prep.py` (14), `test_scoped_drawing_review.py` (13), `test_drawing_review_outcome.py` (8).
- Warning counts: RD-M1 reported 50 warnings over its four files; the same four files give 1 + 6 + 5 + 38 = 50 now. All warnings are the starlette `anyio.abc.BlockingPortal` deprecation and `datetime.utcnow()` in `alembic/versions/e1f2a3b4c5d7_ifc_worker_and_ai_review.py:91`; none relates to a test result.

## Failures

None. 0 failed, 0 errors, 0 skipped in the combined run and in each of the seven per-file runs. There is therefore no test id or assertion tail to quote.

## Environment gaps

No test needed Tesseract or AutoCAD and reported being unable to run: none was skipped, xfailed or errored. The absence of Tesseract and AutoCAD means that any code path that calls them is not exercised by these suites (see limits); that is a property of the suites plus this container, not a recorded failure.

## Evidence files (under `docs/milestones/redesign/RD-M1-refresh-2026-10-06/evidence/tests/`)

`redesign-suites.log`, `redesign-suites.xml`, and one `-rA` file per test file: `test_redesign.txt`, `test_drawing_prep.txt`, `test_drawing_review.txt`, `test_scoped_drawing_review.txt`, `test_drawing_review_outcome.txt`, `test_fa_interfaces.txt`, `test_ifc_worker_and_ai.txt`. The log and per-file text files hold absolute container paths (`/home/user/...`); RD-M1 redacted Windows user-profile paths, this run did not need to.

## Limits: what this run does not establish

- It does not establish AutoCAD behavior: no AutoCAD was present, so no generated script was run, no drawing was opened, erased from or inserted into, and no output drawing was verified.
- It does not establish model behavior: `AI_ENABLED=false` and the fixtures replace the model with stubs, so no real model call was made and nothing here shows how a real model answers, how often, or how well.
- It does not establish anything about the GC-01 drawing or any real drawing; fixtures are synthetic, temporary SQLite databases with synthetic DXF/PDF data, and no live archive or database was read. Tesseract being absent means OCR paths against real scans were not exercised either.
- It is not acceptance: passing tests show that the code does what the tests assert, not that the behavior is right on real drawings or accepted by the owner. RD-M1's list of untested gaps (F001 to F035) was not re-assessed by this run; the added tests were not mapped to those findings.
- Test names for three of RD-M1's four files could not be compared because RD-M1 recorded them in `-q` mode; counts were compared there.
- The tree is run in place (not an isolated copy as in RD-M1): `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` were set, and `git status` after the runs shows no new file other than this evidence folder. The full backend suite was not run; only the seven requested files.
