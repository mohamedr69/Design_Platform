# Test Results (RD-M1)

## Where the tests ran

- Against a **byte-identical copy** of `backend/app`, `backend/tests`, `backend/alembic`, `alembic.ini`, `pytest.ini`, `requirements.txt` placed in the isolated audit area (not the repository). 379 copied files were compared with the pre-audit hash baseline: 0 mismatches (the one extra copied file, the ignored leftover `backend/tests/test_ep_platform.db`, is not used by the suite: `conftest.py` sets `DATABASE_URL=sqlite:///:memory:`).
- Why a copy: pytest and Python would otherwise write `.pytest_cache/` and `__pycache__/` into the owner's tree. The run also used `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`.
- Interpreter: the same one the G-drive services run with — the Desktop copy's venv (`…\Desktop\dev\dev\ep-platform\backend\venv\Scripts\python.exe`, CPython 3.12.10; pytest 8.3.4, ezdxf 1.4.4, PyMuPDF 1.28.2, SQLAlchemy 2.0.36, FastAPI 0.115.6). The G copy's own `backend/venv` points at a Python 3.13 that does not exist on this PC.
- Hermeticity (from `tests/conftest.py`): in-memory DB, temporary uploads/library/cache folders under the user's temp directory, `AI_ENABLED=false`, archive auto-detect off. No `.env` was copied.
- "Clean baseline": the Redesign code and tests are untracked, so a clean checkout of HEAD `13eb73c` does not contain them. The baseline here is the exact working-tree content identified by hash in `BASELINE-MANIFEST.json`.

## Results

| Command (cwd = isolated copy of `backend/`) | Tests | Passed | Failed | Skipped | Errors | Warnings | Duration |
|---|---|---|---|---|---|---|---|
| `python -m pytest -p no:cacheprovider tests/test_redesign.py -v -rA --durations=5` | 16 | 16 | 0 | 0 | 0 | 1 | 0.27 s (10 s wall) |
| `python -m pytest -p no:cacheprovider tests/test_drawing_review.py -q -rfEs` | 11 | 11 | 0 | 0 | 0 | 6 | 9.99 s |
| `python -m pytest -p no:cacheprovider tests/test_fa_interfaces.py -q -rfEs` | 10 | 10 | 0 | 0 | 0 | 5 | 8.54 s |
| `python -m pytest -p no:cacheprovider tests/test_ifc_worker_and_ai.py -q -rfEs` | 41 | 41 | 0 | 0 | 0 | 38 | 65.88 s |
| **Total** | **78** | **78** | **0** | **0** | **0** | 50 | |

Full logs (user-profile paths redacted): `evidence/tests/*.txt`. No failure to report; no test was changed.

The full backend suite was **not** run: RD-M1 asked for the Redesign tests; the three neighbouring files were added because Redesign consumes the review, the interface schedule and the IFC job runner.

## What the passing tests do and do not cover

`test_redesign.py` (16 tests) exercises the deterministic helpers with synthetic data: `_prepare`, `_place`, `read_answer` format checks, `script_lines` text, drawn-centre offsets, preferred symbols, block facing, a synthetic `Walls` index, side-by-side coordination, the weatherproof light block, module scale and the "modules drawn only once approved" rule, typical-plan stacking, the module wall rule and coordination with engineer moves.

Not covered by any test (each linked to an inventory finding):

| Gap | Finding |
|---|---|
| A stored library path that no longer exists (or another machine's path) at Apply | F001 |
| Review changes in status `proposed` being drawn without approval | F002 |
| Low-confidence / self-contradicting REMOVE answers | F003 |
| Script behaviour after a failed `-INSERT` (`entlast`/`entdel`) | F004 |
| Wall index from real DXF layering (layer-0 block content, frozen layers, non-wall layers) | F005, F006 |
| Interface anchors that fall outside the building | F007 |
| Coordination against text, notes, doors, windows, equipment | F008–F011 |
| Output verification after AutoCAD | F023 |
| `plan()`, `apply()`, `refresh()` end-to-end; GET endpoints without writes | F019, F030 |
| Cross-host requeue of a job whose work already completed | F017 |
| Concurrent Plan/PATCH/Apply writes (lost updates) | F032 |
| Same-minute output name overwrite; Apply cancellation; confirm flag | F033, F034, F035 |
| Wall index ignoring the DXF invisible flag | F005 |

Passing tests therefore do **not** show that Redesign is correct on real drawings.
