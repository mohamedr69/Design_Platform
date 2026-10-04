# Exact commands and exit codes (Review 22 correction)

Interpreter: `ep-platform/backend/venv/Scripts/python` (Python 3.12), `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`. Working dir `C:/t/iso/work/r2x/review22/harness-v4` unless stated. Every model-facing run used `PILOT_DRY=1` (scripted provider; isolated dry root under `C:/t/r2x/dry-runs/r22*`); no provider request was made. Logs and JUnit files are in [harness-v4/logs/](harness-v4/logs/), [tests/](tests/), [repro/](repro/) and [runner-evidence/](runner-evidence/).

## 1. Reproduce the reviewer's findings on the submitted harness (before any change)

| Command | Exit | Result |
|---|---|---|
| `python repro/run_reviewer_probes.py C:/t/iso/work/r2x/review22/harness-r21 C:/t/iso/work/r2x/review22/repro/on-r21` (cwd `review22/repro`) | probes 0, pytest 1 | `INDEPENDENT-PROBES.json` identical to the reviewer's; regressions **2 failed, 3 passed** ([repro/on-r21/REVIEW22-REGRESSIONS.xml](repro/on-r21/REVIEW22-REGRESSIONS.xml)) |
| static-share guard probe on the submitted `arm_ev.py` (`repro/guard/`) | 0 | 6 sent; 9 of 10; refusal "per-arm project share (15)"; fresh document 0 |

## 2. Corrected harness v4

| Command | Exit | Result |
|---|---|---|
| `python -m pytest -q test_harness_v4.py -p no:cacheprovider --junitxml=logs/HARNESS-V4.xml` | 0 | **19 passed** |
| `python repro/run_reviewer_probes_v4.py C:/t/iso/work/r2x/review22/harness-v4 C:/t/iso/work/r2x/review22/repro/on-v4` (cwd `review22/repro`) | probes 0, pytest 0 | reviewer's regressions **5 passed** on v4 ([repro/on-v4/REVIEW22-REGRESSIONS.xml](repro/on-v4/REVIEW22-REGRESSIONS.xml)) |
| `bash run_canonical_chain.sh` (stage → dry labels → dry declaration → A → L1..L4 → deferred arm resumed with `XTRACK_FAKE_NOW` = +24 h 1 s → v4 scorer → runner probes) | 0 for every step ([harness-v4/logs/CANONICAL-CHAIN.log](harness-v4/logs/CANONICAL-CHAIN.log)) | [dry/](dry/) |
| `python runner_probes.py` (PILOT_DRY=1, PILOT_DRY_MODE=coherent; rerun after `patch_probe_fixes_3.py`) | 0 | [runner-evidence/RUNNER-INTEGRATION.json](runner-evidence/RUNNER-INTEGRATION.json) |
| `python -m pytest -q test_runner_v4.py -p no:cacheprovider --junitxml=logs/RUNNER-V4.xml` | 0 | **8 passed** |
| `python workload_r22.py` | 0 | [workload/R22-WORKLOAD.json](workload/R22-WORKLOAD.json) |
| `python declare_r22.py` (draft) / `PILOT_DRY=1 python declare_r22.py` (dry) | 0 | [declaration/R22-DECLARATION.draft.json](declaration/R22-DECLARATION.draft.json), [dry/R22-DECLARATION.dry.json](dry/R22-DECLARATION.dry.json) |
| `python bindings_r22.py` | 0 | [bindings/](bindings/) |
| `AI_ENABLED=false python replay_deltas.py` | 0 | [replays/REPLAY-DELTAS.json](replays/REPLAY-DELTAS.json) |

## 3. Unchanged controls

| Command | Exit | Result |
|---|---|---|
| `python -m pytest -q test_harness_v3.py test_coverage_v3_draft_compat.py -p no:cacheprovider --junitxml=…/tests-out/HARNESS-V3-UNCHANGED.xml` (cwd `review21`, unchanged v3 files) | 0 | **13 passed** |
| `python -m pytest -q tests -p no:cacheprovider --junitxml=…/tests-out/R16-HARNESS.xml` (cwd `C:/t/iso/work/r2x/r16`) | 0 | **66 passed** (durable budget / BOQ controls) |
| `AI_ENABLED=false python score_cont.py --declaration CONT-DECLARATION.json --declaration-sha 7b2513b2… --runs C:/t/r2x/runs --tags A=cont-A,S=cont-S,T2=cont-T2,BOQ-S=cont-h06-S,BOQ-T=cont-h06-T --out …/h06-replay/score` (cwd `ai-pilot-r18`) | 0 | six JSON files byte-identical to `review21/h06/score` ([h06-replay/H06-REPLAY-DELTAS.json](h06-replay/H06-REPLAY-DELTAS.json)) |

Application test suites were not rerun: no application file changed (the frozen candidate's tree is clean and its reader hash is unchanged; the R21 results — flags off / T / L1 / L3 267 passed each, T+E and L2 / L4 actual-crop 19 / 22 disclosed failures, full suite 1,732 passed with the 2 known baseline failures — stand as recorded in review21).

## 4. Package

| Command | Exit |
|---|---|
| `python package_r22.py` | 0 |
| `python verify_r22_package.py` | 0 — `evidence/PACKAGE-CHECK.json` `ok: true` |
| `python append_response.py d0339bdabf5cbeb9eb9afd02448b6a9f9624ac14e8dc7fe718e5c1c7e698303c` | 0 — prefix byte-identical |
