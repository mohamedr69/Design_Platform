# Commands (review34, ORCH-05C)

## Environment

- **Python:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe`.
- **Variables:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`, `PYTEST_ADDOPTS="-p no:cacheprovider"`.
- **Working copy:** the code runs from the work folder `C:/t/iso/work/r2x/r34/`, the copy bound by `BINDING-MANIFEST-R34.json`. `scripts/` in this package holds byte-identical copies (the package check verifies it).
- **No model request:** none of these commands sends one. No authorization file is ever written; no ledger scope is created.
- **Writes:** only to the work folder, this package, the agent scratchpad and `C:/t/r2x/r34-sandbox/`.
- **Never reused:** a run folder, sandbox or output folder is never reused; a dry run needs a new stamp.

| Step | Working directory | Command | Output |
|---|---|---|---|
| Preflight of the frozen inputs (PACKET OK / PACKET MISMATCH) | work folder | `python preflight_inputs.py` (after the response append: `--response-any`, which checks the pre-append prefix) | stdout |
| Binding manifest (written once per freeze) | work folder | `python make_binding_r34.py <package>/BINDING-MANIFEST-R34.json <package>/RUN-SET-PROPOSAL.json` | prints its sha256 and file count |
| Dry run (about 45 s) | work folder | `python dry_run_r34.py <new stamp> <package>/BINDING-MANIFEST-R34.json <binding sha256>` | `dry-run/` (refuses if `dry-run/runner` exists) |
| Runner, dry, first invocation | `harness-r32/` | `python runner_r32.py run --mode dry --stamp <new stamp> --run-set <package>/RUN-SET-PROPOSAL.json --binding <package>/BINDING-MANIFEST-R34.json --binding-sha <sha> [--out <new folder>] [--dry-fault C:5]` | `C:/t/r2x/r34-sandbox/<stamp>/` (run folder) and `RUN-REPORT.json` |
| Runner, dry, resume | `harness-r32/` | `python runner_r32.py resume --mode dry --stamp <same stamp> …` | invocation `inv-<n>` |
| Runner, live | `harness-r32/` | `python runner_r32.py run --mode live --declaration <ORCH-07 declaration> --declaration-sha <sha> --run-set … --binding … --binding-sha …` (then `resume`) | **Refused** unless the declaration satisfies `LIVE-RUN-CONTRACT.md` §2, its ledger scope exists with the declared limits, the owner's authorization is at the pinned path with a fresh nonce, and the owner's token is presented in `R34_OWNER_DISPATCH_TOKEN`. This task created none of these |
| All tests with junit (about 2.5 min; 16 modules, 245 tests) | work folder | `python run_tests_r34.py <junit dir> <pytest basetemp dir>` | one XML per module |
| One module | `harness-r32/` | `python -m pytest -q test_<module>.py --basetemp=<scratch dir>` | stdout |
| Capture-store tests (the unchanged review31 copy) | `C:/t/iso/cand-r29/backend` (read-only use) | `PYTHONPATH=C:/t/iso/work/r2x/r34/harness-r32 AI_ENABLED=false python -m pytest -q C:/t/iso/work/r2x/r34/harness-r32/test_capture_store.py --rootdir C:/t/iso/work/r2x/r34/harness-r32` | stdout |
| Package check | work folder | `python verify_review34_package.py [--skip-tests]` | `evidence/PACKAGE-CHECK.json` |
| Evidence manifest (last, written once) | work folder | `python package_r34.py` | `evidence/EVIDENCE-MANIFEST.json` |
| Response-ledger append (once) | work folder | `python append_response_r34.py` | one entry at the end of `docs/milestones/M2/M2-REVIEW-RESPONSE.md` (refuses unless the file still hashes to `500d55f5…90ac`) |

**Rules:**

- **Ledger.** The AI ledger is only ever opened as `file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro` with `uri=True`. Tests use fake ledgers under pytest's temporary folder.
- **Production database.** `backend/ep_platform.db` is never opened.
- **Bytecode.** The candidate and baseline trees are imported read-only with bytecode writing off; the package check verifies both stay clean at their HEADs.
- **Dry mode never reads a cohort document with an application reader.** The application readers' path is exercised only on synthetic documents (`synthetic_r32.py`, `test_runner_r32.py`).
- **Tests never write an authorization file.** Authorization contents are in-memory objects or a monkeypatched loader; `test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests` searches for one.
