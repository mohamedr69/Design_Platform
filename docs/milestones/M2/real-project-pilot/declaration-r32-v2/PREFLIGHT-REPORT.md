# Preflight report: the corrected declaration against the bound review39 harness (ORCH-09, no dispatch)

| | |
|---|---|
| **Declaration** | `FRESH-VALIDATION-DECLARATION-R32-V2.json` `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` (equal to `DECLARATION.sha256`) |
| **Harness** | `PILOT/review39/scripts/harness-r32`, run and imported unchanged (each import preceded by a check of its 56 files against `BINDING-MANIFEST-R39` `harness_r39_package`); bytecode writing off; no `__pycache__` created |
| **Evidence** | `dry-run/PREFLIGHT-RESULTS.json` (`4b0510644941600897c9b7cfe797a83d0982ac7f940296e3253e7a41b7b4feed`, 11:55:54–11:57:06Z)<br>`dry-run/DRY-EXERCISE.json` (`9184955cf1c195bb815321a381b93b92da4bdd2350bfd88ed7537206f2d9ad1d`, phases 12:43:36–12:47:34Z) with `dry-run/exercise/`, `dry-run/deferral-loop-*/`, `dry-run/CLI-VERSION-DEADEND.json`<br>`dry-run/lane-env/`, `scope/`, `evidence/PATHLEN-PROBE.json` |
| **Model requests** | **0** in every step |
| **AI ledger** (`mode=ro`, `uri=True`) | **483 entries / 17 scopes / 0 amendments** before and after every step; scope-name hash `a037785a…663e` unchanged; **no scope created** |
| **Authorization** | **None.** No `OWNER-DISPATCH-AUTHORIZATION.json`, no RUN file, no token file anywhere searched (PILOT, MR, `C:/t`, the scratchpad); `R34_OWNER_DISPATCH_TOKEN` never set |
| **Gate** | The decision coverage gate is C ≥ B only, **a change from plan v2** (A-10); C ≥ R is a mandatory diagnostic |
| **Reference set** | independently AI-reviewed (Claude agents), not human-signed |

## 1. The frozen file as written is refused

`preflight_r32.validate_declaration(declaration as written)`: **REFUSED** — "refused: the declaration binds no owner token digest" (the placeholder `TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION`, exactly once). The guard's `validate` refuses it for the same reason (`test_r40.py::test_frozen_declaration_refused_as_written_by_preflight_and_guard`).

## 2. An in-memory dummy digest passes contract 4 (never written)

The owner's procedure (`fill_owner_digest`) applied **in memory** with a dummy digest (63 zeros and a one; no token's digest) gives a copy differing only in that value. `validate_declaration` on it: **PASSED** — contract `r39-live-contract-4`, run folder `C:/t/r2x/r40-sandbox/r32-v2`, lane allowances 240 / 240 / 40 / 36, parent 556 / 16,300,000 / 3,260,000 / 604,800, window 60 / 86,400, the four lanes' switches, task kinds, `application_env`, `resume_policy` `full`, gate `C_GE_B_ONLY`, the pinned identities, the bounds reference, the ledger. The copy's sha256 (`1bf8d90a…daaa`) belongs to that in-memory copy only: no file with that hash exists, and the dummy digest is in no package file (checked).

## 3. Negative probes (48, all as expected) and the integer strings

Each probe mutates the in-memory copy and calls `validate_declaration` (contract 4). **48 of 48 gave the expected result.**

| Probe | Result |
|---|---|
| Lane allowance B 241; allowances without P | REFUSED ("not the plan's") |
| Parent total 600 (parent / lane inconsistency); parent missing `elapsed_s` | REFUSED |
| Parent elapsed 600,000 with the ledger equal | REFUSED ("bounds computed for another elapsed bound") |
| Ledger `output_tokens` or `requests` differing from the parent | REFUSED ("the backstop of the parent budget") |
| Window limit 61; window 3,600 s | REFUSED |
| Window limit 30 | REFUSED ("bounds computed for another project window") |
| `AI_MAX_CALLS_PER_PROJECT_PER_DAY` 83 or 60; `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` 83 (below the minimum 84) | REFUSED ("incompatible limits") |
| `AI_MAX_CALLS_PER_PROJECT_PER_DAY` `"96.0"` (float string) | REFUSED (integer parse) |
| `AI_MAX_CALLS_PER_PROJECT_PER_DAY` `"84"` (the minimum) | ACCEPTED |
| `AI_MAX_CALLS_PER_DOCUMENT` `"12.0"`, `AI_MAX_ELAPSED_S_PER_JOB` `"120.0"` (float strings) | **ACCEPTED by the harness** (R39-18 / R40-08, not implemented in review39); **refused by this package's integer-string check** (`build_declaration_r40.integer_string_problems`) |
| `AI_MAX_CALLS_PER_DOCUMENT` 11 or 13; `AI_MAX_ELAPSED_S_PER_JOB` 119 (per-document limits) | REFUSED |
| Aliases `sonnet` / `opus` pinned; `AI_MODEL_SMALL` `sonnet` against the pin; provider `claude`; CLI path differing | REFUSED |
| CLI version `"2.1.263"` (not the exact line) | ACCEPTED by the contract (any non-empty line); the runner compares it with `claude --version` at every invocation, which is why the declaration pins the exact line `2.1.263 (Claude Code)` |
| Scope mismatch (either side) | REFUSED |
| Run folder elsewhere; sandbox base not `C:/t/r2x/r<NN>-sandbox`; stamp `a` | REFUSED |
| Authorization path elsewhere | REFUSED |
| Digest upper-case, 63 characters, the placeholder | REFUSED ("binds no owner token digest") |
| `wrap_provider` false | REFUSED |
| `application_env` missing, `true`, or with an extra key | REFUSED |
| Gate `C_GE_B_AND_C_GE_R` (plan v2, R in eligibility); an unknown gate id | REFUSED |
| `resume_policy` `soonest` | REFUSED |
| `resume_policy` `earliest` | ACCEPTED (allowed by contract 4; this declaration binds `full`) |
| `lane_task_kinds` widened (B + `drawings_reply_match`); lane P with switches; an `AI_EVIDENCE_*` key in `provider_env`; contract 3; a dry-exercise flag | REFUSED |

**The declaration's own values:** every count and time limit is an integer string (`"96"`, `"600"`, `"12"`, `"120"`, `"1800"`, `"60"`, `"300"`, prices `"0"`); the only non-integer numeric value is `AI_MAX_COST_PER_JOB` `"0.5"` (a currency amount; inert while prices are 0). `project_bounds_r32.check_compatible` returns no problem.

## 4. The binding

`preflight_r32.verify_binding(BINDING-MANIFEST-R39.json, a6f703b4…567b)`: **PASSED, 239 of 239 bound files re-hashed equal** (the package and work-folder harness copies, the application sources, review38 and review36, the run set, the truth, the reference-set packages, the evaluator package, Reviews 34–39).

## 5. The bounds recomputation

`verify_bounds` with the declared switches, window and elapsed bound: **PASSED** — `PROJECT-REQUEST-BOUNDS.json` (`99be01fb…1721`) equals its recomputation from the run set (24 documents), the truth (`4e237a4e…e064`, rebuilt from the reference set) and the bound code; required minimum 84; population gate DISPATCH_ELIGIBLE.

## 6. The four lanes' live environment checks, offline (the R39-18 class)

`lane_env_check_r40.py` ran, in each lane's own tree, exactly the checks a live lane makes before anything is built, with the environment the bound runner builds in live mode (`runner_r32.lane_env('live', …)` from the declaration): `verify_lane_environment` (mode live: every switch, every provider value in the environment **and** in the application's settings), `verify_application_env` (the variable and `drawings_ai_review_enabled` False), and `drawing_ai_review.enabled()` off.

| Lane | Tree | Result |
|---|---|---|
| B | `C:/t/iso/frozen-r12/backend` | PASSED (3 of 3) |
| C | `C:/t/iso/cand-r29/backend` | PASSED (3 of 3) |
| R | `C:/t/iso/cand-r29/backend` | PASSED (3 of 3) |
| P | `C:/t/iso/cand-r29/backend` | PASSED (3 of 3) |

Every declared value parses into the application's settings (`dry-run/lane-env/LANE-ENV-*.json` lists the parsed values: `ai_max_calls_per_project_per_day` 96, `ai_max_elapsed_s_per_job` 120.0, `ai_model_small` `claude-sonnet-5`, …). No provider was built, no database opened, no CLI run; only each lane's `tmp` folder was created under `C:/t/r2x/r40-sandbox/r40d-env-<lane>`. So no declared value can pass the preflight, consume an owner authorization and then fail in a lane (the R39-18 risk), as long as the trees and the settings code stay as bound.

## 7. The CLI-version dead-end (dry drill; `dry-run/CLI-VERSION-DEADEND.json`)

The runner records `claude --version` **after** creating the run folder and **before** consuming the authorization. Dry mode runs no CLI, so the live check's refusal was injected **in-process** (only `model_identity_r38.record_invocation` replaced by a function raising the same `IdentityRefused`; no bound file changed), then the runner was called again without the injection:

| Step | Result |
|---|---|
| `run` with the injected version refusal at invocation 1 | refused: "CLI version '9.9.9 (Claude Code)' differs from the declared '2.1.263 (Claude Code)'"; the run folder exists with `RUN-STATE.json`, **no `allowance.sqlite`, no `capture.sqlite`** |
| `run` again | refused: "a second fresh invocation of this run is refused (… exists); use 'resume'" |
| `resume` | refused: "the run's allowance.sqlite is missing; a resume never re-creates it" |

**Reading:** with the declared stamp, such a refusal at invocation 1 would leave the run unable to continue; a new declaration would be needed. The authorization is not consumed. **Mitigation:** RUNBOOK section 1.1 (`claude --version` must print `2.1.263 (Claude Code)` immediately before invocation 1). It is listed among the owner's acknowledgements (DECLARATION-SUMMARY section 14).

## 8. The dry exercise with the declaration's switches (`dry-run/DRY-EXERCISE.json`, tag `52050f`)

**Before:** the declaration's lane switches, lane allowances, parent, window, `application_env`, task kinds, gate and resume policy equal the runner's dry values (all 8 checks true), so the dry runs ran the declared arms. The bound harness ran unchanged from `PILOT/review39/scripts/harness-r32` with `--sandbox-base C:/t/r2x/r40-sandbox` (a declared parameter: no twin was needed). Reader `none`: no application reader touched a cohort document; every request ended at the refusing stub (`dry_refused`); no provider was built; no ledger path.

**8.1 The main exercise: all 24 run-set documents, as six per-project dry runs** (`main_kind`; drive C stayed below the 250 MB a single 112 MB run needs, section 14):

| Project | Documents | Lanes B / C / R / P (stub calls) | Status | Comparison | Ledger |
|---|---|---|---|---|---|
| EP-3563 | 3 | 3 / 3 / 1 / 0 | finished | PENDING (NOT ELIGIBLE) | unchanged |
| EP-15744 | 1 | 1 / 1 / 1 / 0 | finished | PENDING (NOT ELIGIBLE) | unchanged |
| EP-22349 | 5 | 5 / 5 / 1 / 0 | finished | PENDING (NOT ELIGIBLE) | unchanged |
| EP-26687 | 7 | 7 / 7 / 1 / 0 | finished | PENDING (NOT ELIGIBLE) | unchanged |
| EP-27331 | 6 | 6 / 6 / 1 / 0 | finished | PENDING (NOT ELIGIBLE) | unchanged |
| EP-29255 | 2 | 2 / 2 / 1 / 0 | finished | PENDING (NOT ELIGIBLE) | unchanged |

- Each run: ingestion of its documents (registration only, the ingestion and C-from-B state checks ok), B, the C-from-B state check, C, R (served C's capture by content key, plus one reference-only probe), P (0: in dry mode C has no answered dispatch to sample), offline scoring. The truth written by every run equals the bound truth `4e237a4e…`.
- **Model requests 0**; the scorer's outcome (every lane has 0 facts because no reader ran) **exercises the scorer and is not a result**.

**8.2 The EP-27331 deferral / resume loop under `resume_policy` `full`** (EP-27331's 6 documents; dry drill windows, small so the loop completes in minutes):

| Drill window | Invocations | Early resumes refused | Resumes between the earliest and the full time refused | Refused resumes created nothing | Final state |
|---|---|---|---|---|---|
| 10 per 20 s (the shape of the planning case) | **2** | 1 | 1 | yes | FINISHED |
| 6 per 20 s (the shape of the structural case) | **3** | 2 | 0 | yes | FINISHED |

- Invocation 1 of the first loop: B 6 and C 4 charged, then C's documents 5 and 6 DEFERRED; R and P "not started: 2 C document(s) DEFERRED"; `resume_not_before` = the `full` time (the window empty), 2 s after the earliest retry; a resume before it was refused ("the resume policy 'full' allows a resume at …"), also one between the earliest and the full time; the resume at the full time served the 10 answered requests and charged the rest: FINISHED.
- The second loop needed 3 invocations (B 6, then C 6, then R's reference-only request), each resume at its `full` time.
- Every DEFERRED record carried `retry_at_earliest` and `retry_at_full` {planning, structural}; the live numbers (EP-27331: 2 invocations at planning, 3 at the structural maximum) are `RESUME-INVOCATIONS-R39.json`'s model, reproduced by Verification 40.

**Invariants of the exercise:** AI ledger 483 / 17 / 0 at every snapshot; 0 model requests; the live run folder `C:/t/r2x/r40-sandbox/r32-v2` never created. Because drive C was nearly full, the staged PDF copies of every finished dry invocation were removed after it (8 folders, 182,858,695 bytes in the recorded process; copies of the frozen staging; the run records, databases and outputs kept).

## 9. The live runner refuses before creating any folder (the frozen hash was never used with it)

| Attempt | Result |
|---|---|
| `python -B runner_r32.py run --mode live --declaration <the RUN path> --declaration-sha <the in-memory copy's hash> …` as a subprocess from the bound harness, **no RUN file, no token** | **REFUSED** (exit 1): "live mode needs the declaration and its exact sha256"; no folder |
| The same `run` in-process, the loader serving the in-memory RUN copy (nothing written) | **REFUSED** after the binding (239), contract 4, the HEADs, the truth and population gate, the run set and the **bounds recomputation**: "the declared ledger scope 'm2-fresh-validation-r32-v2-2026-10-04' does not exist (it is created only under the owner's authorization, never by this harness)"; no folder |
| The same, with the scope check and the guard's declaration loader also patched in-process (pretending the scope exists) | **REFUSED** by the guard preview: "no owner dispatch authorization (…\declaration-r32-v2\OWNER-DISPATCH-AUTHORIZATION.json does not exist)" — before the run folder, the WRITER lock, the CLI check and any consumption |

The run folder never existed (before, during, after). Review39's own tests prove the same refusal with a complete temporary declaration (`test_runner_r32.py::test_live_mode_with_a_complete_declaration_and_no_authorization_refuses_before_any_folder_exists`; passed in review39's junit, checked by `test_r40.py`).

## 10. The guard refuses

| Call | Result |
|---|---|
| `dispatch_guard_r32.check(<RUN path>, <in-memory hash>, action="preview")` (loader serving the in-memory copy) | refused: no owner dispatch authorization |
| `check(…, action="consume")` | converted to preview, writes nothing: refused, the same |
| `check(<RUN path>, …)` with the real loader | refused: the declaration is missing or does not hash |
| `check(None, None)` | refused: no verified declaration |
| `validate(<copy>, …, auth=None, token=None)` | refused: the authorization is not a JSON object |
| `GuardedProvider(…).complete(request)` | `dispatch_refused`; the inner provider **never built** (0 dispatched, 1 refused) |

## 11. The scope command

- `create_scope_r40.py preview`: exit 0, **ledger unchanged** (483 / 17 / 0 before and after), scope absent; output `scope/SCOPE-PREVIEW-OUTPUT.json` (shown in `SCOPE-CREATION-COMMAND.md`).
- `create_scope_r40.py create --frozen-sha f38fb281… --run-sha <in-memory hash>`: exit 3, "refused: no owner dispatch authorization (… does not exist)"; ledger unchanged; `scope/SCOPE-CREATE-REFUSED-OUTPUT.json`.
- Tests: preview creates nothing; the real mode refuses without the authorization file; a wrong declaration hash is refused; the positive path on a throwaway SQLite file only (`SCOPE-CREATION-COMMAND.md` section 4).

## 12. Invariants (before and after every preflight step; `PREFLIGHT-RESULTS.json` `invariants`)

AI ledger 483 / 17 / 0 unchanged; run folder never created; the review39 harness folder byte-identical, no `__pycache__`; the package unchanged by the preflight outside its own outputs; no authorization, RUN or token file; no token in the environment; the dummy digest in no file; 0 model requests.

## 13. What this preflight does not show

- **The live path end to end.** No authorization, token, scope or provider may exist.
- **The application's processing of the real cohort PDFs.** That happens for the first time in live B (R34-18).
- **The served model's identity.** UNRESOLVED; the owner's probe (RUNBOOK section 1) was not run.
- **A single 24-document dry run** in this package's evidence (six per-project runs instead; section 14). Verification 40 and the superseded package ran single multi-document dry runs of the same code paths.

## 14. Disclosures

- **Drive C ran out of space during this task.** Other processes were writing on C: (ep-platform test temp folders `ep-test-*`, `boq-test-*`, `pytest-of-moham` in `%TEMP%`, written between 11:57Z and 12:18Z; Codex processes were running). At 11:57–11:59Z the drive reached **0 bytes free** and the first dry-exercise attempt failed (the main run `interrupted` during ingestion; the loops stopped after one invocation; only the CLI drill completed). Nothing of that attempt reached the package: its outputs are kept in `C:/t/iso/work/r2x/r40/failed-dry-attempt-1/`. I removed only my own failed dry sandbox (85 MB) to let the tools write. The exercise was then hardened (a free-space guard before every runner call, outputs staged in the work folder and copied to the package only when everything succeeded, staged PDF copies trimmed) and run in phases; my own guard stopped two phases early (118 MB < 120 MB; 79 MB < 80 MB), both recorded in the work-folder audit log; the final phases succeeded. Free space stayed between 60 and 180 MB afterwards.
- **Windows path length:** `LongPathsEnabled` is 0 on this machine; ordinary file APIs fail at 260 characters or more (`evidence/PATHLEN-PROBE.json`, made with the backend's Python: 259 opens, 260 fails). The declared base and stamp keep the longest application path (F032) at 255 characters; the application also opens PDFs through its own extended-length helper.
- **No `claude` invocation of any kind** and no `--version` call: the CLI line `2.1.263 (Claude Code)` is taken from the earlier records (declaration-r32's audit log, the four-arm and review06 declarations) and the file's embedded version 2.1.263; the file was only hashed (`0b35df94…5b03`). The owner confirms the line (RUNBOOK section 1.1).
- The dry runs' sandboxes remain under `C:/t/r2x/r40-sandbox/r40d-*` (dry, 0 model requests), including those of the stopped attempts (tags `6dac0a`, `7bd0d8`).
