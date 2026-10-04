# Commands (ORCH-06, package `evaluator-offline-r32`)

Every command runs from the work folder `C:/t/iso/work/r2x/r35` (never from the candidate tree), with the backend venv
Python and no bytecode, no pytest cache and no provider variables. Every path is absolute. No command makes a provider or
model request; the evaluator runs offline on SYNTHETIC fixtures only.

```bash
cd C:/t/iso/work/r2x/r35
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 PYTEST_ADDOPTS="-p no:cacheprovider" GIT_OPTIONAL_LOCKS=0
PY=C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe
PKG=C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/evaluator-offline-r32
W=C:/t/iso/work/r2x/r35
```

| # | Step | Command | Writes |
|---|---|---|---|
| 0 | Frozen-tree snapshot before | `$PY $PKG/scripts/tree_snapshot.py $W/SNAPSHOT-BEFORE.json before` | work folder |
| 1 | Fixtures (SYNTHETIC) | `$PY $PKG/scripts/fixtures_r32.py $PKG/SYNTHETIC-PREDICTIONS.json` | the fixture file |
| 2 | Evaluator .10 offline, whole register per call (as `score_lane.py`) | `$PY $PKG/scripts/run_evaluator_offline_r32.py --fixtures $PKG/SYNTHETIC-PREDICTIONS.json --out $W/run/RUN-EVAL-R35.json --scope full` | work folder |
| 3 | Same, fixture document only (scope check) | `$PY $PKG/scripts/run_evaluator_offline_r32.py --fixtures $PKG/SYNTHETIC-PREDICTIONS.json --out $W/run/RUN-EVAL-R35.docscope.json --scope document` | work folder |
| 4 | Normaliser analysis N1 / N2 (not bound code) | `$PY $PKG/scripts/normaliser_experiment_r35.py --fixtures $PKG/SYNTHETIC-PREDICTIONS.json --out $W/run/NORMALISER-N1.json --normaliser N1` (and `N2`) | work folder |
| 5 | Matrix, report, run summary | `$PY $PKG/scripts/make_report_r35.py $W/run/RUN-EVAL-R35.json $W/run/RUN-EVAL-R35.docscope.json $W/run/NORMALISER-N1.json $W/run/NORMALISER-N2.json` | `PARITY-MATRIX.json`, `EVALUATOR-TEST-REPORT.md`, `evidence/RUN-SUMMARY.json`, `evidence/NORMALISER-EXPERIMENT.json` |
| 6 | Tests (junit) | `$PY $PKG/scripts/run_tests_r35.py` | `tests/*.xml`; pytest temp under `$W/pytest-tmp` |
| 7 | Binding manifest | `$PY $PKG/scripts/make_binding_r35.py $W/run/RUN-EVAL-R35.json` | `BINDING-MANIFEST-R35.json` |
| 8 | Package check | `$PY $PKG/scripts/verify_package_r35.py` | `evidence/PACKAGE-CHECK.json` |
| 9 | Evidence manifest (last) | `$PY $PKG/scripts/package_r35.py` | `evidence/EVIDENCE-MANIFEST.json` |
| 10 | One response-ledger entry | `$PY $PKG/scripts/append_response_r35.py` | appends to `docs/milestones/M2/M2-REVIEW-RESPONSE.md` (refuses unless the file is `cc1edc4d…3084`) |
| 11 | Frozen-tree snapshot after | `$PY $PKG/scripts/tree_snapshot.py $W/SNAPSHOT-AFTER.json after` | work folder |

**Read-only checks used around the steps** (no write anywhere):

```bash
git -C C:/t/iso/cand-r29 rev-parse HEAD                     # a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d
GIT_OPTIONAL_LOCKS=0 git -C C:/t/iso/cand-r29 status --porcelain   # empty
sha256sum <every frozen input>                              # see BINDING-MANIFEST-R35.json
$PY -c "import sqlite3; c=sqlite3.connect('file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro', uri=True); print(c.execute('select count(*) from entries').fetchone(), c.execute('select count(*) from scopes').fetchone())"
```

**How the evaluator is reached.** `run_evaluator_offline_r32.py` imports `scripts.m2_eval6` from
`C:/t/iso/cand-r29/backend` in place (read-only, `sys.dont_write_bytecode`), after re-hashing it and every module it
imports, and calls `EV.evaluate(register, page, rows, page['page1_corrections'], ai_context)` exactly as
`review31/scripts/harness/score_lane.py` does, on `review34/LABELS-R32-EVAL-INPUT.json`. Before any evaluation it removes
`AI_*` / provider variables, sets `AI_ENABLED=false`, blocks sockets, DNS, subprocesses and `os.system`, replaces the
candidate's provider classes and `get_provider` / `set_provider` with raising stubs, and installs an audit hook that refuses
any write outside the work folder. Its output records every counter.
