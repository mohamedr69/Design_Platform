# ORCH-10 implementation report (R42PORT-IMPL): review42 and declaration-r32-v3

## Hashes
- Declaration v3 `FRESH-VALIDATION-DECLARATION-R32-V3.json`: **`9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`** (contract `r42-live-contract-5`; placeholder once; refused as written).
- `BINDING-MANIFEST-R42.json`: **`00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`** (319 bindings; all 239 carried from R39 re-hash equal, 0 differ, 0 missing).
- review42 `evidence/EVIDENCE-MANIFEST.json`: **`ab2bc40d6ab5a45b0f7dca710f188b1e9f2a9cb4da80118177c7b1df9658e782`**.
- declaration-r32-v3 `evidence/EVIDENCE-MANIFEST.json`: written after this report (see the response-ledger entry and the hand-back).
- Supersedes v2 `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` (never to be run). PROJECT-REQUEST-BOUNDS (review42) equals R39's in every verified key (only `run_set.path` re-pointed); RESUME-INVOCATIONS byte-identical.

## What changed and why (per finding)
- **Portability (A-11, 2.1):** every Desktop binding re-pointed to the merged installation and re-hashed (no byte difference); the merged venv interpreter bound (path, sha256, version; both trees' requirements and imports satisfied); extended-length hashing; the CLI pinned by absolute path + sha256 `0b35df94…5b03` + `2.1.263 (Claude Code)`, checked before any lane and every resume (read as bytes); isolation from the merged installation checked at every lane's start and end; the bundled 2.1.289 and the merged `.env` never used. Path lengths: bound max 151, live staged PDFs max 256, nothing else ≥ 260.
- **R40-04 (option 2):** a fail-closed `RefusingGlobalProvider` is the application's global provider in C, R and P (installed before any application code; any `get_provider().complete()` refused, recorded as breach `global_provider_request`, run INVALID); B unchanged. Static: all 88 site-lane pairs resolved; dynamic: C, R, P refused, B unchanged.
- **R41-09 / R41-10 / R41-11:** every check (CLI file, version line, free disk ≥ 2 GiB, binding, HEADs, truth, run set, bounds, scope, guard preview) before the run folder; capture store then atomic allowance before the nonce is consumed; `run` re-enters a folder with no allowance, no consumed nonce, no charge (REENTRY record); resume re-checks CLI and disk before its nonce. Cases T, A, B, C, D, E: none consumes an authorization, none strands the run; refusals that must stay still refuse.
- **A-11 §4:** multi-invocation authorization (max 3, in-order nonces, strict keys) as a separable proposal; per-invocation form unchanged.
- **R41-12 / R41-13 / R41-14:** statements corrected in the declaration and response entry; the four r40 work records bound by hash.
- Harness files changed: 17 (dispatch_guard_r32.py, inputs_r32.py, lane_r32.py, model_identity_r38.py, preflight_r32.py, r32_test_helpers.py, run_control_r38.py, run_state_r38.py, runner_r32.py, sandbox_ingest_r32.py, test_dispatch_guard_r32.py, test_literal_compare_r32.py, test_model_identity_r38.py, test_preflight_r32.py, test_project_bounds_r32.py, test_runner_r32.py, test_sandbox_ingest_r32.py); new: 5 (request_paths_r42.py, test_global_provider_r42.py, test_portability_r42.py, test_resume_authorization_r42.py, test_runner_order_r42.py).

## Tests
- review42: **549 tests, 0 failures, 0 errors, 0 skipped**, 0 audit-guard refusals (26 modules, package harness).
- declaration-r32-v3: **36 tests, 0 failures, 0 errors**, 0 guard refusals.
- Preflight: 73/73 probes as expected (48 from v2 + 25 new); all checks ok: True. Diff: protected values unchanged True.

## Demonstrations (dry / live-shaped; 0 CLI invocations; ledger 483/17/0 unchanged)
- completion: passed
- durable_charging: passed
- global_provider: passed
- interruption_and_deadends: passed
- page_accounting: passed
- refusal_before_dispatch: passed
- terminal_stop: passed
- window_deferral: passed
- Dry exercise: single 24-document run FINISHED; six per-project runs finished; EP-27331 loops [2, 3] invocations; cross-project drill 2 invocations; CLI-version case not a dead-end; 0 model requests.

## Residual risks
- The disk floor is checked at each invocation's start only; another writer can still fill the drive during an invocation.
- Isolation compares paths textually (an 8.3 short name of the merged folder would pass).
- An application path building its own provider object would bypass the chain (none reached statically).
- The live path (real CLI, real scope, real authorization) is shown only live-SHAPED offline; served-model identity stays UNRESOLVED.
- With the multi-invocation form, a leaked token plus that file allow up to 3 invocations without a further owner action (never beyond the 556-request parent).

## Not authorized
No scope, token, authorization file, RUN file, request, dispatch of B/C/R/P, default, M2 acceptance or M3. No `claude` process was started; no provider or model request was made.

## Statuses
- Correction readiness: delivered for Independent Verification 42; not self-approved.
- Accuracy: none; no prediction exists.
- Label truth: reference set independently AI-reviewed (Claude agents), not human-signed.
- Permissions/budget: eligibility only; nothing authorized.
- M2: CHANGES STILL REQUIRED. M3: not started.

READY FOR INDEPENDENT VERIFICATION 42
