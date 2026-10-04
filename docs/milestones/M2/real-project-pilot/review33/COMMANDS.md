# Commands (review33, ORCH-05.1)

## Environment

- **Python:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe`.
- **Variables:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8` and `PYTEST_ADDOPTS="-p no:cacheprovider"`.
- **Working copy:** the code runs from the work folder `C:/t/iso/work/r2x/r33/`. That is the copy bound by `BINDING-MANIFEST-R33.json`. `scripts/` in this package holds byte-identical copies, and the package check verifies that they are identical.
- **No model request:** none of these commands sends one.
- **Writes:** only to the work folder, this package, the agent scratchpad and `C:/t/r2x/r33-sandbox/`.
- **Never reused:** a sandbox or run folder is never reused. Pick a new stamp each time.

| Step | Working directory | Command | Output |
|---|---|---|---|
| Preflight of the frozen inputs (PACKET OK / PACKET MISMATCH) | work folder | `python preflight_inputs.py` | stdout |
| Derived files (adapter, converter, selector) | work folder | `python prepare_r33.py` | `dry-run/TRUTH-R32.json`, `LABELS-R32-EVAL-INPUT.json`, `CONVERTER-RECONCILIATION.json`, `RUN-SET-PROPOSAL.json` |
| Binding manifest (written once per freeze) | work folder | `python make_binding_r33.py <package>/BINDING-MANIFEST-R33.json <package>/RUN-SET-PROPOSAL.json` | `BINDING-MANIFEST-R33.json` (prints its sha256) |
| Dry run (about 30 s) | work folder | `python dry_run_r33.py <new stamp> <package>/BINDING-MANIFEST-R33.json <binding sha256>` | `dry-run/` (refuses if `dry-run/runner` exists) |
| Runner alone, dry | `harness-r32/` | `python runner_r32.py --mode dry --stamp <new stamp> --run-set <package>/RUN-SET-PROPOSAL.json --binding <package>/BINDING-MANIFEST-R33.json --binding-sha <sha> --resume-drill --out <new folder>` | `RUN-REPORT.json` and lane files |
| Runner, live | `harness-r32/` | `… --mode live --declaration <ORCH-07 declaration> --declaration-sha <sha>` | **Refused** until `OWNER-DISPATCH-AUTHORIZATION.json` exists and names that declaration hash and an owner budget token. This task never creates it |
| All tests with junit (about 75 s; 15 modules, 144 tests) | work folder | `python run_tests_r33.py <junit dir> <pytest basetemp dir>` | one XML per module |
| One module | `harness-r32/` | `python -m pytest -q test_<module>.py --basetemp=<scratch dir>` | stdout |
| Capture-store tests (the unchanged review31 copy) | `C:/t/iso/cand-r29/backend` (read-only use) | `PYTHONPATH=C:/t/iso/work/r2x/r33/harness-r32 AI_ENABLED=false python -m pytest -q C:/t/iso/work/r2x/r33/harness-r32/test_capture_store.py --rootdir C:/t/iso/work/r2x/r33/harness-r32` | stdout |
| Package check | work folder | `python verify_review33_package.py [--skip-tests]` | `evidence/PACKAGE-CHECK.json` |
| Evidence manifest (last, written once) | work folder | `python package_r33.py` | `evidence/EVIDENCE-MANIFEST.json` |
| Response-ledger append (once) | work folder | `python append_response_r33.py` | one entry at the end of `docs/milestones/M2/M2-REVIEW-RESPONSE.md` (it refuses unless the file still hashes to `da5cc798…f7f7`) |

**Rules:**

- **Ledger.** The AI ledger is only ever opened as `file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro` with `uri=True`.
- **Production database.** `backend/ep_platform.db` is never opened.
- **Bytecode.** The candidate and baseline trees are imported read-only, with bytecode writing off. The package check verifies that both stay clean at their HEADs.
- **Dry mode never reads a cohort document with an application reader.** A lane started with `reader: "application"` in dry mode on a cohort pool id stops at its first assert. The application readers' path is exercised only on synthetic documents (`synthetic_r32.py`, `test_runner_r32.py`).
