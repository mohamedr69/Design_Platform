# Commands (review36, ORCH-06C)

## Environment

- **Python:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe` (3.12.10).
- **Variables:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`, `PYTEST_ADDOPTS="-p no:cacheprovider"`.
- **Work folder:** `C:/t/iso/work/r2x/r36/`. The bound harness copy is `C:/t/iso/work/r2x/r36/harness-r32/` (`BINDING-MANIFEST-R36.json`). `scripts/harness-r32/` in this package holds byte-identical copies; `scripts/` holds the task scripts (byte-identical to the work folder); `scripts/parity-r36/` holds the patched copy of the two ORCH-06 parity scripts. The package check verifies all three.
- **No model request:** none of these commands sends one. No authorization file is ever written; no ledger scope is created.
- **Writes:** only to the work folder, this package, the agent scratchpad (`…/scratchpad/r36harness/`), `C:/t/r2x/r36-sandbox/` (test sandboxes of the twin run) and the single response-ledger append.
- **Never reused:** a junit, basetemp, twin, copy or output folder is never reused; each script refuses an existing target.

## Steps

| Step | Working directory | Command | Output |
|---|---|---|---|
| Task-start snapshot (frozen trees, AI ledger read-only, response hash, candidate / baseline git) | work folder | `python snapshot_r36.py <work>/evidence-work/SNAPSHOT-BEFORE.json before` | the snapshot JSON |
| Copy the review34 harness (every source checked against the review34 manifest) | work folder | `python copy_harness_r36.py <work>/evidence-work/COPY-RECORD.json` | `harness-r32/` (40 files) |
| Apply the one change | work folder | `python apply_h1_fix_r36.py apply C:/t/iso/work/r2x/r36/harness-r32` | `literal_compare_r32.py` `ec2221c8…` -> `c23ba577…`; `test_literal_compare_r32.py` `1d91cb54…` -> `66e0ddcf…` |
| Re-derive the change from review34 (a check, any new folder) | work folder | `python apply_h1_fix_r36.py derive <new folder>` | the same two hashes |
| Test-run twin (only `C:/t/r2x/r34-sandbox` -> `C:/t/r2x/r36-sandbox`) | work folder | `python make_suite_twin_r36.py <work>/evidence-work/TWIN-RECORD.json` | `harness-r32-suite-twin/` |
| Whole suite (16 modules) from the twin, write guard on (about 3 min) | work folder | `python run_tests_r36.py twin <new junit dir> <new basetemp dir>` | one XML per module + `guard/*.json` |
| The 14 sandbox-free modules from the bound copy, write guard on (about 2 min) | work folder | `python run_tests_r36.py bound <new junit dir> <new basetemp dir>` | one XML per module + `guard/*.json` |
| Parity-script copy (work folder r35 -> r36/parity, harness folder -> the r36 copy, literal_compare hash -> r36) | work folder | `python make_parity_copy_r36.py <work>/evidence-work/PARITY-COPY-RECORD.json` | `parity/scripts/` |
| ORCH-06 parity run with the fixed harness (about 17 min; evaluator side re-run read-only, guards on) | `C:/t/iso/work/r2x/r36/parity` | `python scripts/run_evaluator_offline_r32.py --fixtures <PILOT>/evaluator-offline-r32/SYNTHETIC-PREDICTIONS.json --out C:/t/iso/work/r2x/r36/parity/run/RUN-R36-FULL.json --scope full` | the run JSON (exit 1 is expected: the 106 H1 cases no longer equal the fixtures' review34 expectation) |
| Row-level judgements, review34 harness and r36 harness | work folder | `python judge_all_rows_r36.py old <work>/whatif/ROWS-OLD.json` and `python judge_all_rows_r36.py new <work>/whatif/ROWS-NEW.json` | 42,804 rows per state |
| H1 what-if result | work folder | `python h1_whatif_r36.py <package>/H1-WHATIF-RESULT.json` | the result (refuses an existing file) |
| Binding manifest (written once) | work folder | `python make_binding_r36.py` | `BINDING-MANIFEST-R36.json`; prints its sha256 and entry count |
| Package check | work folder | `python verify_review36_package.py [--skip-tests]` | `evidence/PACKAGE-CHECK.json` |
| Evidence manifest (last, written once) | work folder | `python package_r36.py` | `evidence/EVIDENCE-MANIFEST.json` |
| Response-ledger append (once) | work folder | `python append_response_r36.py` | one entry at the end of `docs/milestones/M2/M2-REVIEW-RESPONSE.md` (refuses unless the file still hashes to `44b5ae38…1bc25`) |
| One module, quickly | `harness-r32/` | `python -m pytest -q test_literal_compare_r32.py --basetemp=<scratch dir>` | stdout |

**Rules:**

- **Ledger.** The AI ledger is only ever opened as `file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro` with `uri=True`.
- **Production database.** `backend/ep_platform.db` is never opened.
- **Bytecode.** Every import of review34, the candidate or the baseline runs with bytecode writing off.
- **Write guard.** Every pytest process of `run_tests_r36.py` loads `pytest-plugins/r36_write_guard.py`, an audit hook that refuses any write outside the basetemp, the junit folder and (twin) `C:/t/r2x/r36-sandbox/`, and refuses network connections. TEMP / TMP point into the basetemp.
- **Why a twin.** The review34 suite hard-codes `C:/t/r2x/r34-sandbox` (sandbox base, child assertion, helpers, test assertions), and `test_runner_r32` / `test_sandbox_ingest_r32` create sandboxes there. This task may write sandboxes only under `C:/t/r2x/r36-sandbox/` and may change no module except `literal_compare_r32.norm_revision`. The twin is not bound and not packaged as harness code.
