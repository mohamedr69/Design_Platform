# Exact commands and exit codes (Review 23 correction)

Interpreter `ep-platform/backend/venv/Scripts/python` (3.12); `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`; cwd `C:/t/iso/work/r2x/review23/harness-v4.1` unless stated. Every runner invocation used `PILOT_DRY=1` (scripted provider; isolated roots under `C:/t/r2x/dry-runs/r23-*`); no provider request. Logs: [logs/](logs/), [harness-v4.1/logs/](harness-v4.1/logs/), [repro/](repro/).

| Step | Command | Exit | Result |
|---|---|---|---|
| Reproduce on the submitted v4 runner | `python repro/run_stop_probe.py C:/t/iso/work/r2x/review22/harness-v4 …/review23/repro/on-v4 C:/t/r2x/dry-runs/r23-repro-v4` (cwd `review23/repro`) | probe 0; pytest 1 | initial: stopped after EP-16830, 12 requests, 1 critical; resume: **8 requests** to EP-17428; regressions **1 failed, 2 passed** ([repro/on-v4/](repro/on-v4/)) |
| Apply the recorded edits to a copy of frozen v4 | `python patch_lifecycle.py`; `python patch_lifecycle_2.py` | 0 | [harness-v4.1/](harness-v4.1/) |
| Evidence chain | `bash run_r23_chain.sh` ([logs/R23-CHAIN.log](logs/R23-CHAIN.log)) | every step 0 | |
| ↳ lifecycle probes | `python lifecycle_probes.py` | 0 | [lifecycle-evidence/LIFECYCLE.json](lifecycle-evidence/LIFECYCLE.json) |
| ↳ lifecycle regressions | `python -m pytest -q test_lifecycle_v4_1.py -p no:cacheprovider --junitxml=logs/LIFECYCLE-V4.1.xml` | 0 | **5 passed** |
| ↳ eight runner scenarios (v4.1 runner) | `PILOT_DRY=1 PILOT_DRY_MODE=coherent python runner_probes.py` | 0 | [runner-evidence/RUNNER-INTEGRATION.json](runner-evidence/RUNNER-INTEGRATION.json) |
| ↳ runner regressions | `python -m pytest -q test_runner_v4.py -p no:cacheprovider --junitxml=logs/RUNNER-V4.xml` | 0 | **8 passed** |
| ↳ scoring tests (unchanged scorer) | `python -m pytest -q test_harness_v4.py -p no:cacheprovider --junitxml=logs/HARNESS-V4.xml` | 0 | **19 passed** |
| ↳ reviewer's probe on v4.1 | `python repro/run_stop_probe.py …/review23/harness-v4.1 …/review23/repro/on-v4.1 C:/t/r2x/dry-runs/r23-repro-v4.1` | probe 0; pytest 0 | resume: **0 requests**, stop preserved; **3 passed** ([repro/on-v4.1/](repro/on-v4.1/)) |
| Freeze | `python bindings_r23.py` | 0 | [bindings/](bindings/) |
| Package / check | `python package_r23.py`; `python verify_r23_package.py` | 0 / 0 | `evidence/PACKAGE-CHECK.json` `ok: true` |
| Response | `python append_response.py 3a4d08abeaf75a3a3de7d83c43af79d2d707ffe1278e34ca568edf1cd769522f` | 0 | prefix byte-identical |

Not rerun: the application suites (no application file changed), the r16.1 controls and the H-06 replay (unchanged since review22; the allowance module hash is re-checked by the package checker).
