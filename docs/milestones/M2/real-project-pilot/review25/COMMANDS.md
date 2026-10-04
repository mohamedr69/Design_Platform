# Exact commands and exit codes (Review 25 correction)

Interpreter `ep-platform/backend/venv/Scripts/python` (3.12); `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`; cwd `C:/t/iso/work/r2x/review25/harness-v4.3` unless stated. Every runner invocation used `PILOT_DRY=1` with the scripted provider in isolated roots under `C:/t/r2x/dry-runs/r25-*`; no provider request. Chain log: [logs/R25-CHAIN.log](logs/R25-CHAIN.log).

| Step | Command | Exit | Result |
|---|---|---|---|
| Reproduce on unchanged v4.2 | `python repro/run_neutral_probe.py C:/t/iso/work/r2x/review24/harness-v4.2 …/review25/repro/on-v4.2 C:/t/r2x/dry-runs/r25-repro-v4.2` (cwd `review25/repro`) | probe 0; pytest **1** | 3 mutations: ok/streak 2, resume exit 0, 16 new, completed; **3 failed, 3 passed** |
| Apply the recorded edit to a copy of frozen v4.2 | `python patch_kind_outcome.py` | 0 | |
| Freeze (before the final validation) | `python bindings_r25.py` | 0 | [bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json) |
| Final chain | `bash run_r25_chain.sh` | every step 0 | |
| ↳ evidence for the 62-test set | `python lifecycle_probes.py`; `PILOT_DRY=1 PILOT_DRY_MODE=coherent python runner_probes.py`; `python provider_boundary_probes.py` | 0 / 0 / 0 | |
| ↳ submitted 62-test set (one run) | `python -m pytest -q test_provider_journal.py test_harness_v4.py test_runner_v4.py test_lifecycle_v4_1.py test_boundary_v4_2.py -p no:cacheprovider --junitxml=logs/SUBMITTED-62.xml` | **0** ([logs/SUBMITTED-62.exit](logs/SUBMITTED-62.exit)) | **62 passed** |
| ↳ R25 mutation probes | `python neutral_mutation_probes.py` | 0 | [neutral-evidence/NEUTRAL.json](neutral-evidence/NEUTRAL.json) |
| ↳ legacy recheck | `python legacy_journal_recheck.py` | 0 | 25 journals, all equal |
| ↳ R25 regressions | `python -m pytest -q test_neutral_v4_3.py -p no:cacheprovider --junitxml=logs/NEUTRAL-V4.3.xml` | **0** ([logs/NEUTRAL-TESTS.exit](logs/NEUTRAL-TESTS.exit)) | **32 passed** |
| ↳ reviewer's probe on v4.3 | `python repro/run_neutral_probe.py …/review25/harness-v4.3 …/review25/repro/on-v4.3 C:/t/r2x/dry-runs/r25-repro-v4.3` | probe 0; pytest **0** | 3 mutations: indeterminate, exit 5, 0 new; **6 passed** |
| ↳ original R24 probe on v4.3 | `python C:/t/iso/work/r2x/review24/repro/run_provider_probe.py …/review25/harness-v4.3 …/review25/repro/r24-provider-probe-on-v4.3 C:/t/r2x/dry-runs/r25-r24probe-v4.3` | probe 0; pytest **0** | before-file and after-file: 98 → 4, 0 new, stopped; **3 passed** |
| Package / check | `python package_r25.py`; `python verify_r25_package.py` | 0 / 0 | `evidence/PACKAGE-CHECK.json` `ok: true` |
| Response | `python append_response.py 8ed53fb35400dd3de6a5da22ad93e1425160e92e61b586505f454f21de9f8dba` | 0 | prefix byte-identical |

Not run: application suites (no application file changed); H-06; any model call.

The response file's hash at the start of this task (`8ed53fb3…`) differs from the hash my Review 24 append left (`fa4423e2…`). The Review 23 and 24 entries are intact, and content before them changed. That change was made outside this task, and it is left as found. This task's append is prefix-checked against the start-of-task hash.
