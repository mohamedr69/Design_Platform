# CHANGE-RECORD-R42: the r32 harness corrected for portability and safety in the merged installation (ORCH-10)

- **Task:** ORCH-10 (orchestrator ledger ORCH-027; task file sha256 `4ee96b8a…9b89`), agent R42PORT-IMPL, Claude Opus 5.5 (`claude-opus-5-5`, self-reported), effort High. Authorities A-03, A-06, A-09, A-10, A-11.
- **Not self-approved.** Delivered for Independent Verification 42 (ORCH-10V).
- **Binding:** `BINDING-MANIFEST-R42.json` sha256 **`00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`** (319 path-keyed bindings in 19 groups). Every one of the 239 bindings carried from R39 re-hashes EQUAL at its merged path (0 differ, 0 missing). The runnable harness is bound from `PILOT/review42/scripts/harness-r32/` only (`harness_r42_package`, 61 files).
- **Standing status:** M2 CHANGES STILL REQUIRED; M3 not started. Reference set independently AI-reviewed (Claude agents), not human-signed.

## 1. Every changed or new harness file

39 files are byte-identical to review39 (listed in the binding manifest `unchanged_from_review39`).

| File | Status | R39 sha256 | R42 sha256 | Lines | Finding / task item |
|---|---|---|---|---|---|
| `dispatch_guard_r32.py` | changed | `9cd6068f50c5…` | `877dee5d1c1e…` | +120 / -6 | 2.4 one approval for all planned resumptions: the multi-invocation form (strict keys, in-order nonces, bound, reuse / out-of-order refusals); the per-invocation form unchanged |
| `inputs_r32.py` | changed | `41309ae85a09…` | `1bec5d3165a9…` | +14 / -3 | 2.1.1 portability (PILOT -> the merged installation); 2.1.3 path lengths (sha256_file through the extended-length prefix) |
| `lane_r32.py` | changed | `493c0a9f248a…` | `b6014a015a7b…` | +55 / -2 | 2.2 R40-04: the refusing global provider installed in C, R, P before any application code, checked at the end, the dry drill global_provider_request; 2.1.5 isolation checked at the lane's start and end |
| `model_identity_r38.py` | changed | `433d0e5afff5…` | `0a463df6eee2…` | +58 / -10 | 2.1.4 the CLI pinned by absolute path + sha256 + exact version line (validate_pins), verify_cli_file (bytes only), check_version (pure, before anything; R41-09 A/T, R41-11) |
| `preflight_r32.py` | changed | `0e59dbff5e87…` | `8e652565b46e…` | +189 / -11 | contract 5: 2.1.1 interpreter, 2.1.4 the CLI file check, 2.3 the disk floor (R41-10), 2.1.5 isolation, 2.2 global_provider, 2.4 resume_authorization; 2.1.3 verify_binding through the extended-length prefix; the dry / test sandbox base r42 |
| `r32_test_helpers.py` | changed | `64c9ffcd3415…` | `2c2729e35701…` | +33 / -8 | tests: contract-5 temporary declarations (fake CLI file hashed, never executed); merged paths; base r42 |
| `request_paths_r42.py` | new | `—…` | `135a2baee9c4…` | +143 / -0 | 2.2 (a): the static analysis re-run plus the global-provider resolution of every get_provider() site |
| `run_control_r38.py` | changed | `d30de813c109…` | `5dd0ca3a770f…` | +66 / -1 | 2.2 R40-04: RefusingGlobalProvider (fail-closed, recorded, INVALID) |
| `run_state_r38.py` | changed | `5e789b05a23b…` | `a12695bf987c…` | +7 / -3 | 2.2 R40-04: the breach kind global_provider_request (class limit) |
| `runner_r32.py` | changed | `b290dd1c8ddd…` | `53a202567474…` | +190 / -52 | 2.3 R41-09 / R41-10 / R41-11: every check (CLI file, disk, version line) before the folder; capture store then atomic allowance before the nonce is consumed; reentry_proof; resume re-checks; the dry drill kind global_provider_request |
| `sandbox_ingest_r32.py` | changed | `8fb5c891a41b…` | `73027343a104…` | +9 / -3 | 2.1.1 the bound interpreter (PY -> the merged venv); 2.1.5 isolation (PWD / OLDPWD dropped from sandbox_env) |
| `test_dispatch_guard_r32.py` | changed | `8797e662f0de…` | `59b1e0c19a7e…` | +1 / -1 | tests: merged path constant |
| `test_global_provider_r42.py` | new | `—…` | `1e50dff2524a…` | +160 / -0 | 2.2 (a), (b), (c): static and dynamic proof in C, R, P; lane B unchanged |
| `test_literal_compare_r32.py` | changed | `b7850ef748eb…` | `ca7ed221a2d3…` | +1 / -1 | tests: merged path constant |
| `test_model_identity_r38.py` | changed | `03b244d05ff1…` | `987ffa8ec9e2…` | +46 / -7 | tests: the CLI pin, check_version, verify_cli_file |
| `test_portability_r42.py` | new | `—…` | `965955eaa2e0…` | +214 / -0 | 2.1: merged bindings, interpreter, long paths, CLI pin, disk floor, isolation, contract-5 keys |
| `test_preflight_r32.py` | changed | `096535e0c6d7…` | `1f1523f75131…` | +7 / -7 | tests: merged paths, base r42, contract name |
| `test_project_bounds_r32.py` | changed | `8a47c286c2de…` | `b1bd251c269e…` | +1 / -1 | tests: merged path constant |
| `test_resume_authorization_r42.py` | new | `—…` | `0f9fea2cd20e…` | +213 / -0 | 2.4: both forms and every refusal |
| `test_runner_order_r42.py` | new | `—…` | `45690911015d…` | +382 / -0 | 2.3: Verification 41's dead-end cases T, A, B, C, D, E (dry and live-shaped), the refusals that stay, resume re-checks, the multi-nonce run |
| `test_runner_r32.py` | changed | `6897891a35cd…` | `18beb790b5a8…` | +13 / -3 | tests: base r42; direct execute() calls prepare the allowance and the capture store as main now does |
| `test_sandbox_ingest_r32.py` | changed | `0da051961c54…` | `ec0093fd98d8…` | +1 / -1 | tests: base r42 in the docstring |

## 2. What changed and why

### 2.1 Portability (A-11; the Desktop installation and venv are absent)
- Every binding re-pointed to `G:/dev (2)/dev/ep-platform-merged/ep-platform/…`; every carried file re-hashes equal (no byte difference found).
- The interpreter is bound: `…/ep-platform/backend/venv/Scripts/python.exe` (Python 3.12.10). Contract 5 binds its path, sha256 and version; the runner and every live lane refuse another `sys.executable`. Its packages equal both frozen trees' `requirements.txt` pins and every application module of both trees imports under it (`PILOT/declaration-r32-v3/evidence/INTERPRETER-CHECK.json`).
- Path lengths: `sha256_file` and `verify_binding` open files through the extended-length prefix (`LongPathsEnabled` = 0); the probe is in `PILOT/declaration-r32-v3/evidence/PATHLEN-PROBE.json`.
- The CLI is pinned by absolute path (`AI_CLAUDE_CLI` = the WinGet file), its sha256 (`0b35df94…5b03`, read as bytes before any lane and before every resume) and the exact line `2.1.263 (Claude Code)`. The merged installation's bundled 2.1.289 is never used.
- Isolation: every lane, live and dry, at its start and its end, refuses an environment value, setting, import path or loaded module under the merged installation except the bound venv and this harness folder, and an application env file equal to the merged `.env`; `sandbox_env` drops `PWD` / `OLDPWD`.

### 2.2 R40-04 closed by option 2 (A-11: "a fail-closed boundary")
- Lanes C, R and P install `RefusingGlobalProvider` as the application's global provider before any application code; any `get_provider().complete(...)` is refused (`dispatch_refused`), recorded as the contract breach `global_provider_request` and makes the run INVALID. Lane B is unchanged (the chain).
- Static: `REQUEST-PATHS-STATIC.json` resolves all 88 site-lane pairs; every lane installs its global provider before its first application entry; the reached sites equal review39's ({'B': True, 'C': True, 'R': True}). Dynamic: `test_global_provider_r42.py` and `evidence/demos/DEMO-global_provider.json`. See `REQUEST-PATHS.md`.

### 2.3 R41-09 (the dead-end class), R41-10 (C1 disk) and R41-11 (CLI updates)
- The runner now checks the CLI file, the free disk (≥ 2 GiB on the sandbox drive; configurable only upward), every preflight item and the guard preview, and then compares `--version`, all BEFORE the run folder is created or re-opened.
- The capture store is bound and the allowance created atomically (built aside, renamed into place) BEFORE the authorization nonce is consumed.
- `run` re-enters a folder that, by its own records, holds no allowance, no consumed nonce and no charged request (`REENTRY-<n>.json`); with an allowance present `run` is refused and `resume` continues; a resume re-checks the CLI file, the version line and the disk before consuming its nonce.
- Every case of Verification 41's `deadends_r41` (T, A, B, C, D, E) is reproduced in dry and live-shaped form: none consumes an authorization, none strands the run (`test_runner_order_r42.py`, `evidence/demos/DEMO-interruption_and_deadends.json`). The refusals that must stay still refuse.

### 2.4 One approval for all planned resumptions (A-11 §4; separable, default off)
- `dispatch_guard_r32` accepts, besides the unchanged per-invocation file, a file with `invocations_authorized` N (1..3, bound by the declaration) and N nonces consumed one per invocation in order; any other key, a reused or out-of-order nonce, N above the bound, a declaration without the bound, or a frozen hash is refused; invocation N+1 needs a new file (`test_resume_authorization_r42.py`).

## 3. Tests (junit in `tests/`, run from the package harness under the R42 audit guard)

**549 tests, 0 failures, 0 errors, 0 skipped; guard refusals 0** (tree `G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review42/scripts/harness-r32`).

| Module | Tests | Result |
|---|---|---|
| `test_allowance_r32` | 19 | 19 passed in 1.98s |
| `test_capture_store` | 21 | 21 passed in 2.37s |
| `test_concentration_r32` | 28 | 28 passed in 6.92s |
| `test_converter_r32` | 7 | 7 passed in 0.21s |
| `test_dispatch_guard_r32` | 15 | 15 passed in 0.63s |
| `test_global_provider_r42` | 7 | 7 passed in 66.35s (0:01:06) |
| `test_labels_adapter_r32` | 13 | 13 passed in 0.33s |
| `test_lane_judge_r32` | 23 | 23 passed in 0.43s |
| `test_literal_compare_r32` | 48 | 48 passed in 1.21s |
| `test_model_identity_r38` | 10 | 10 passed in 0.25s |
| `test_portability_r42` | 28 | 28 passed in 1.81s |
| `test_preflight_r32` | 82 | 82 passed in 5.72s |
| `test_project_bounds_r32` | 9 | 9 passed in 0.70s |
| `test_request_paths_r39` | 11 | 11 passed in 26.04s |
| `test_resume_authorization_r42` | 31 | 31 passed in 1.28s |
| `test_run_control_r38` | 22 | 22 passed in 4.78s |
| `test_run_set_selector_r32` | 9 | 9 passed in 1.10s |
| `test_runner_order_r42` | 15 | 15 passed in 125.28s (0:02:05) |
| `test_runner_r32` | 50 | 50 passed in 129.61s (0:02:09) |
| `test_sandbox_ingest_r32` | 5 | 5 passed in 13.18s |
| `test_score_bcr_r32` | 43 | 43 passed in 9.14s |
| `test_state_check` | 5 | 5 passed in 0.30s |
| `test_stop_rules` | 8 | 8 passed in 0.12s |
| `test_tripwire_r32` | 5 | 5 passed in 0.33s |
| `test_unread_pages_r39` | 17 | 17 passed in 2.91s |
| `test_visibility_r38` | 18 | 18 passed in 508.01s (0:08:28) |

## 4. Scripted-provider demonstrations (`evidence/demos/`, dry or live-shaped, 0 CLI invocations, 0 model requests)

| Demonstration | Result | Also proven by |
|---|---|---|
| completion | PASSED (15.6 s) | test_runner_r32.py (the dry pipeline on the real reference set); test_runner_order_r42.py::test_dry_A_and_T_... |
| durable_charging | PASSED (80.7 s) | test_visibility_r38.py::test_provider_timeouts_are_visible_per_page_and_the_terminal_stop_survives_the_resume; test_visibility_r38.py::test_an_interrupted_or_unsaved_dispatch_stays_charged_and_is_visible_on_the_resume; test_allowance_r32.py::test_charges_are_never_refunded_whatever_the_outcome |
| global_provider | PASSED (56.9 s) | test_global_provider_r42.py (7 tests) |
| interruption_and_deadends | PASSED (164.5 s) | test_runner_order_r42.py (15 tests); test_runner_r32.py::test_* two-invocation drills |
| page_accounting | PASSED (45.2 s) | test_visibility_r38.py::test_pages_left_unread_by_the_application_are_listed_and_the_document_stays_complete; test_visibility_r38.py::test_the_application_path_on_synthetic_documents_records_pages; test_unread_pages_r39.py (17 tests) |
| refusal_before_dispatch | PASSED (1.2 s) | test_dispatch_guard_r32.py; test_resume_authorization_r42.py::test_a_file_naming_the_frozen_hash_is_refused_in_both_forms; test_runner_r32.py::test_live_mode_* (refusals before any folder) |
| terminal_stop | PASSED (60.0 s) | test_visibility_r38.py::test_lane_allowance_refusal_is_visible_everywhere_and_the_resume_keeps_the_stop; test_allowance_r32.py::test_refusals_and_terminal_stops_are_durable_and_a_resume_never_resets_them |
| window_deferral | PASSED (81.7 s) | test_visibility_r38.py::test_the_full_resume_policy_records_both_times_and_refuses_an_early_resume; test_visibility_r38.py::test_project_window_deferral_resumes_after_the_window_frees_and_never_resends; declaration-r32-v3 dry-run deferral loops (EP-27331, 2 and 3 invocations) |

AI ledger before and after: 483 / 17 / 0 (unchanged: True); authorization files written: 0.

## 5. Outputs re-run

- `PROJECT-REQUEST-BOUNDS.json` `ad059bfa314b…`: every key `verify_bounds` compares equals review39's `99be01fb…1721`; the file differs only in `run_set.path` (Desktop → merged).
- `RESUME-INVOCATIONS-R42.json` `9791fa897587…`: byte-identical to review39's.
- `REQUEST-PATHS-STATIC.json` `8b6488cfeb3a…`.
- `LIVE-RUN-CONTRACT.md` version 5 (`4353069805d6…`): version 4 with listed substitutions and sections 14–16; sections 4, 5, 6, 8, 9, 11, 12, 13 carried byte for byte (`evidence/CONTRACT-V5-RECORD.json`).

## 6. What was not changed
- Every number of the experiment (arms, run set, caps, parent, allowances, window, thresholds, gate, stop rules, pins); the scorer, the judge, the evaluator, the allowance, the capture store, the concentration rule (byte-identical files).
- No earlier package, label, frozen tree, application code, MR file, the AI ledger (read `mode=ro` only), the staging or the merged installation's code, data or `.env` was written. No `claude` process was started (the binary was read as bytes only); no provider or model request; no scope, token, RUN or authorization file.

## 7. Known limits
- The disk floor is checked at the start of each invocation; it cannot stop another process from filling the drive during an invocation.
- Isolation compares paths textually (forward/backslash and case normalised); an 8.3 short name of the merged folder would not be recognised.
- An application path that builds its own provider object (not through `get_provider()`) would bypass the chain; none is reached statically (REQUEST-PATHS.md §5).
- The live path (the real CLI, the real ledger scope, a real authorization) cannot be exercised offline; it is shown live-SHAPED (in process, fake ledger, fake CLI file, in-memory authorization, lanes stubbed).
