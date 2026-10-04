# Exact commands and exit codes (Review 24 correction)

Interpreter `ep-platform/backend/venv/Scripts/python` (3.12); `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`; cwd `C:/t/iso/work/r2x/review24/harness-v4.2` unless stated. Every runner invocation used `PILOT_DRY=1` (scripted provider; isolated roots under `C:/t/r2x/dry-runs/r24-*`); no provider request. Logs: [logs/](logs/) and [harness-v4.2/logs/](harness-v4.2/logs/) (JUnit).

| Step | Command | Exit | Result |
|---|---|---|---|
| Reproduce on the submitted v4.1 runner (unchanged) | `python repro/run_provider_probe.py C:/t/iso/work/r2x/review23/harness-v4.1 …/review24/repro/on-v4.1 C:/t/r2x/dry-runs/r24-repro-v4.1` (cwd `review24/repro`) | probe 0; pytest 1 | before_file: initial exit 98 (3 × `transport`, no stop file, no manifest stop), resume exit 0, **16 new requests**, `completed`; after_file control: resume exit 4, 0 new; regressions **1 failed, 2 passed** |
| Apply the recorded edits to a copy of frozen v4.1 | `python patch_provider_recovery.py`; `python patch_provider_recovery_2.py` | 0 / 0 | |
| Freeze (before the final validation) | `python bindings_r24.py` | 0 | [bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json) |
| Evidence chain | `bash run_r24_chain.sh` ([logs/R24-CHAIN.log](logs/R24-CHAIN.log)) | every step 0 | |
| ↳ journal unit tests | `python -m pytest -q test_provider_journal.py -p no:cacheprovider --junitxml=logs/PROVIDER-JOURNAL.xml` | 0 | **23 passed** |
| ↳ lifecycle probes (critical T1–T3, T5a/b; provider T4/T4b) | `python lifecycle_probes.py` | 0 | [lifecycle-evidence/](lifecycle-evidence/) |
| ↳ lifecycle regressions | `python -m pytest -q test_lifecycle_v4_1.py -p no:cacheprovider --junitxml=logs/LIFECYCLE-V4.1.xml` | 0 | **5 passed** |
| ↳ eight runner controls | `PILOT_DRY=1 PILOT_DRY_MODE=coherent python runner_probes.py` | 0 | [runner-evidence/](runner-evidence/) |
| ↳ runner regressions | `python -m pytest -q test_runner_v4.py -p no:cacheprovider --junitxml=logs/RUNNER-V4.xml` | 0 | **8 passed** |
| ↳ provider boundary matrix P1–P6 | `python provider_boundary_probes.py` | 0 | [boundary-evidence/BOUNDARY.json](boundary-evidence/BOUNDARY.json) |
| ↳ boundary regressions | `python -m pytest -q test_boundary_v4_2.py -p no:cacheprovider --junitxml=logs/BOUNDARY-V4.2.xml` | 0 | **7 passed** |
| ↳ scorer tests (unchanged scorer) | `python -m pytest -q test_harness_v4.py -p no:cacheprovider --junitxml=logs/HARNESS-V4.xml` | 0 | **19 passed** |
| ↳ reviewer's probe on v4.2 | `python repro/run_provider_probe.py …/review24/harness-v4.2 …/review24/repro/on-v4.2 C:/t/r2x/dry-runs/r24-repro-v4.2` | probe 0; pytest 0 | before_file resume exit 4, **0 new**, `stopped`; **3 passed** |
| Package / check | `python package_r24.py`; `python verify_r24_package.py` | 0 / 0 | `evidence/PACKAGE-CHECK.json` `ok: true` |
| Response | `python append_response.py 4e220d8171657c2816b350d4443b665b44a59d3747bc4e7d3d67d274fd073da0` | 0 | prefix byte-identical |

Not rerun: application suites (no application file changed), the r16.1 controls and the H-06 replay (unchanged; the allowance module hash is re-checked by the package checker). An earlier trial of the boundary probes and of the reviewer's probe on an intermediate v4.2 (before `patch_provider_recovery_2.py`) was discarded; the evidence here is from the frozen harness only.
