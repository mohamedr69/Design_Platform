# Preflight report: the frozen declaration against the bound harness (ORCH-07, no dispatch)

| | |
|---|---|
| **Declaration** | `FRESH-VALIDATION-DECLARATION-R32.json` `38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0` (equal to `DECLARATION.sha256`) |
| **Harness** | The bound copy `C:/t/iso/work/r2x/r36/harness-r32` (`BINDING-MANIFEST-R36.json` `5a1a6aad…e568`, entries `harness_r36`). Each imported module was checked against the binding before import. Bytecode writing was off. |
| **Evidence** | `dry-run/PREFLIGHT-RESULTS.json` (`bf49117d96833b3c589b61dd2c5e36334a412e9e1c68a3ea7d3a6a7317ccf949`, 17:15:26–17:15:30Z)<br>`dry-run/DRY-EXERCISE.json` (`1e3c52ae5af6e3739aa266808c56628d59d7b936ce9b462c4dcc6695c4af33b7`)<br>`dry-run/TWIN-RECORD.json` (`1c7634795b25fd157753f7015cd41f58c9e3ff1b9ab17f0ef5200205cbe2c58c`)<br>`dry-run/exercise/` |
| **Model requests** | **0** |
| **AI ledger** (`mode=ro`, `uri=True`) | **483 entries / 17 scopes / 0 amendments** before and after every step. Scope-name hash `a037785a…663e` unchanged. **No scope created.** |
| **Authorization** | **None.** No `OWNER-DISPATCH-AUTHORIZATION.json` exists at the pinned path, and no file whose name contains `dispatch-authorization` exists under the pilot folder, the roadmap folder, `C:/t/r2x`, the work folder or the scratchpad. **No token was generated, and `R34_OWNER_DISPATCH_TOKEN` was never set.** |

## 1. The placeholder digest: the declaration as written is refused, by design

`authorization.owner_token_sha256` holds the explicit placeholder `TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION`. It is not a digest.
- **The preflight refuses it.** `preflight_r32.validate_declaration` and the live runner (`load_declaration`) both refuse with **"refused: the declaration binds no owner token digest"**.
- **The guard refuses it** for the same reason.
- **They keep refusing until the owner fills it in.**

**How the owner fills it in:**
1. The owner chooses a token and names its sha256 in the budget authorization.
2. The runnable declaration is this file with exactly that one value replaced (`build_declaration_r37.fill_owner_digest`; tested in memory). Its own sha256 is what the runner, every lane, the guard and the authorization file use.

**The checks that run before the digest check all passed on the file as written:**
- the file hashes to its sha256;
- `binding_manifest_sha256` and `run_set_sha256` equal the files given;
- every required key is present;
- `run.folder` = `C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03`;
- `authorization.path` = the pinned path `PILOT/declaration-r32/OWNER-DISPATCH-AUTHORIZATION.json`.

| Check | Result |
|---|---|
| `validate_declaration(declaration as written)` | **REFUSED**: "refused: the declaration binds no owner token digest" (expected) |
| `load_declaration(path, 38e08df9…, binding 5a1a6aad…, run set 9058f3d6…)` | **REFUSED**: the same reason (expected) |
| `validate_declaration(in-memory copy with a syntactically valid dummy digest)` | **PASSED**. Stamp, run folder, caps 240/240/40/36, day limit 60, lane switches B/C/R/P, provider environment (10 required keys + 17 application limits), ledger (path, scope, limits, `wrap_provider` true), pinned authorization path. The dummy digest was held in memory only. It is no token's digest, and it was never written to disk (checked: no package file contains it). |

## 2. The binding

`preflight_r32.verify_binding(BINDING-MANIFEST-R36.json, 5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568)`: **PASSED, 155 of 155 bound files re-hashed equal.** These include the 40 work-folder copies under `C:/t/iso/work/r2x/r36/harness-r32/`, which therefore still hash as bound (Verification 37 R37-09).

## 3. The live runner without authorization and without a token

| Attempt | Result |
|---|---|
| `python -B runner_r32.py run --mode live --declaration <declaration> --declaration-sha 38e08df9… --run-set …/review34/RUN-SET-PROPOSAL.json --binding …/review36/BINDING-MANIFEST-R36.json --binding-sha 5a1a6aad…`, from the bound copy, as a subprocess, with no `R34_OWNER_DISPATCH_TOKEN` and no authorization file | **REFUSED, exit 1**: `preflight_r32.Refused: refused: the declaration binds no owner token digest`.<br>The refusal came at the declaration contract, **before any folder was created**: `C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03` does not exist, before or after, and the `r34-sandbox` listing is unchanged. |
| The same `run` in-process, with the in-memory dummy-digest copy (patched loader; nothing written) | **REFUSED**: "the declared ledger scope 'm2-fresh-validation-r32-2026-10-03' does not exist (it is created only under the owner's authorization, never by this harness)".<br>This refusal came after the binding, the declaration contract, the candidate and baseline HEADs (clean), the truth and population gate (57/38/38) and the run set (24) had all passed, and **before** the guard preview and before any folder was created. |
| `dispatch_guard_r32.check(declaration, 38e08df9…, action="preview")` | **REFUSED**: "no owner dispatch authorization (…/declaration-r32/OWNER-DISPATCH-AUTHORIZATION.json does not exist)" |
| `check(…, action="consume")` | Converted to preview, which writes nothing: **REFUSED**, same reason |
| `check(None, None)` | **REFUSED**: "no verified declaration" |
| `GuardedProvider(...).complete(request)` with no authorization | `dispatch_refused`. The inner provider was **never built** (0 dispatched, 1 refused). |

**Invariants**, recorded before and after every step:
- AI ledger unchanged at 483/17/0;
- the run folder never created;
- `r34-sandbox` unchanged;
- the bound harness folder byte-identical, with no `__pycache__`;
- the package unchanged by the preflight;
- no authorization file;
- no token;
- the dummy digest never written;
- 0 model requests.

## 4. The dry-mode exercise with the declaration's switches and the refusing stub

**The test twin.** The task allows sandboxes only under `C:/t/r2x/r37-sandbox/`, while the bound code's base is `C:/t/r2x/r34-sandbox`.
- The exercise therefore ran from a **test twin**, `C:/t/iso/work/r2x/r37/harness-r32-dry-twin/`. It is the package copy of the bound harness (each file checked against `harness_r36_package`), with **only** the literal `C:/t/r2x/r34-sandbox` replaced by `C:/t/r2x/r37-sandbox`.
- That made 15 substitutions in 8 files. The 40 file hashes are in `TWIN-RECORD.json`.
- The twin is **not bound** and is never a live harness. A relocated copy would be a new binding (Verification 37 item 1).

**How it ran:**
- `runner_r32.main(["run", "--mode", "dry", "--stamp", "orch07-dry-20261003a", …])` ran in-process from the twin, 17:16:18–17:16:35Z.
- `runner_r32.DRY_LANE_SWITCHES` was set to the declaration's `lane_switches`. These were checked equal to the runner's own dry defaults (the DRAFT-DECLARATION.v2 arms) before the run.
- The declaration's caps (240/240/40/36) and day limit (60) equal the dry values (checked).
- Run folder: `C:/t/r2x/r37-sandbox/orch07-dry-20261003a`.

| Item | Result |
|---|---|
| Ingestion | 24 run-set documents of 6 projects registered without processing (24 `pending`). `ai_usage`, `document_readings`, `background_jobs`, `result_cache`, `extraction_runs` and `project_submittals` are all 0. |
| C-from-B and R-from-B state checks | **Pass** |
| Lane switches | Each lane verified that its `AI_EVIDENCE_*` environment equals the declaration's switches exactly: B `{AI_EVIDENCE_VARIANT: off}`, C 10 switches, R 6 switches, P `{}`. The result is true for B, C, R and P. |
| Provider | **None built.** Every request ended at `DryRefusingProvider` (`dry_refused`). The live provider classes were patched to raise, and no attempt reached them. The lane PATH held no CLI, and there was no ledger path. |
| Requests through the chain (stub calls) | B 24, C 24, R 1 reference-only (+24 served from C's capture by content key), P 0 (C had no answered dispatch). **Model requests: 0.** |
| Allowance (dry run key, not the declaration's) | Caps fixed at 240/240/40/36, day limit 60. Charges: B 24, C 24, R 1, P 0. |
| Capture store | 49 rows. 0 duplicate bound keys, 0 reserved without an answer. R served 24 from C's capture. 0 rows served from P to B or C. |
| AI ledger | 483/17/0 before and after (the runner's own dry check and this task's check). **No scope.** |
| Scorer | Candidate outcome NOT ELIGIBLE, comparison PENDING. Every lane has 0 facts because no reader ran (reader `none`): **an exercise of the scorer, not a result.** |
| Truth | The run's `TRUTH-R32.json` equals the bound truth `4e237a4e…` |

## 5. What this preflight does not show

- **The live path end to end.** No authorization, token, scope or provider may exist.
- **The application's processing of the real cohort PDFs.** That happens for the first time in live B (R34-18).
- **Live attribution of R and P requests** for the project-day counter (R35-20).
- **The owner's fill of the digest.** It was tested only as a pure function in memory.

## 6. Disclosures

- **One `claude --version` call.** While locating the Claude Code CLI to compare the provider environment, this agent ran `claude --version` once. It is a local version print, with no `-p` and no model request. The four-arm declaration already records CLI 2.1.263.
- **The twin's ingestion** copied the 24 staged run-set PDFs into the dry sandbox `C:/t/r2x/r37-sandbox/orch07-dry-20261003a/`. This was registration only, and no reader ran.
- **Read-only opens of the AI ledger** may touch the WAL `-shm` file's modification time. The database is unchanged.
