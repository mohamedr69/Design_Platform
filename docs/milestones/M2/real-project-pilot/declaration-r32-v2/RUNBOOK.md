# Runbook: fresh validation R32, corrected declaration v2 (ORCH-09)

**Status: the declaration is frozen and NOT authorized.** Nothing in this runbook may be done before Verification 41 and the owner's own budget authorization. This task ran none of the owner steps: no probe, no token, no RUN file, no authorization file, no scope, no invocation.

| | |
|---|---|
| Frozen declaration | `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\FRESH-VALIDATION-DECLARATION-R32-V2.json` |
| Frozen hash | **`f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af`** (`DECLARATION.sha256`). It identifies what was reviewed. It is **never** given to the runner. |
| RUN declaration (made by the owner, section 2) | `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json` |
| Authorization file (written by the owner, pinned) | `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\OWNER-DISPATCH-AUTHORIZATION.json` |
| Bound harness | `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\review39\scripts\harness-r32` (`BINDING-MANIFEST-R39.json` `a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b`) |
| Python | `C:\Users\moham\Desktop\dev\dev\ep-platform\backend\venv\Scripts\python.exe`, always with `-B`, never with `-O` |
| Run folder (created by the first invocation) | `C:\t\r2x\r40-sandbox\r32-v2`. Never moved, never deleted. |
| Ledger and scope | `C:\t\r2x\ledger\r2x-ledger.sqlite`, scope **`m2-fresh-validation-r32-v2-2026-10-04`**, limits `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` |
| Owner records folder (owner creates it) | `C:\t\r2x\r40-sandbox\r32-v2-owner-records` (outside the run folder and the package) |

**Conventions.**
- Every command is for **cmd.exe**, not Windows PowerShell 5.1: PowerShell 5.1 drops an empty `""` argument when it calls a native program, and the probe needs one.
- **O** = the owner. **V** = the orchestrator or an independent verifier (read-only steps).
- The reference set is independently AI-reviewed (Claude agents), not human-signed.
- **The decision coverage gate is C ≥ B only. This is a change from plan v2** (whose gate was C ≥ B and C ≥ R), ruled by the owner (A-10). It is not an unchanged gate. C ≥ R is a mandatory diagnostic.

Open one cmd.exe window and set these once (they hold no secret):

```cmd
set PKG=C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2
set HARNESS=C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\review39\scripts\harness-r32
set PY=C:\Users\moham\Desktop\dev\dev\ep-platform\backend\venv\Scripts\python.exe
set PYTHONDONTWRITEBYTECODE=1
set GIT_OPTIONAL_LOCKS=0
```

## 1. (a) The owner's model-identity probe (before anything else; A-10 item 2; Verification 40 section 6, amended per R40-16)

**What it is.** The owner's own check, outside the experiment and outside the harness, that the installed CLI accepts the pinned full ids and what the server says it ran. **This task did not run it.** It is not authorized by this runbook or by the declaration. It uses the owner's subscription.

**What it costs.** At least one request per pinned id. **The number of requests cannot be verified offline.** The flags below reduce the CLI's own background requests, but nothing shows they remove them. `num_turns` and every `modelUsage` entry show what the CLI reports.

### 1.1 The CLI file and version (no request)

```cmd
where claude
certutil -hashfile "C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe" SHA256
claude --version
```

Expected:
- `where claude` lists exactly `C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe` (the declaration's `AI_CLAUDE_CLI` is `claude`, resolved on PATH).
- The sha256 is `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03` (218,746,016 bytes; BINDING-MANIFEST-R39 records it).
- `claude --version` prints exactly **`2.1.263 (Claude Code)`**. The declaration pins this line. Any other line: **stop**. A CLI change before dispatch requires a new declaration hash.

### 1.2 The probe, once per pinned id (cmd.exe, an empty folder each)

```cmd
cd /d %TEMP%
mkdir ep-model-probe-sonnet
cd ep-model-probe-sonnet
set ANTHROPIC_API_KEY=
set ANTHROPIC_AUTH_TOKEN=
set CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
echo Reply with the single word OK.| "C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe" -p --output-format stream-json --verbose --model claude-sonnet-5 --max-turns 1 --no-session-persistence --disable-slash-commands --strict-mcp-config --tools "" > probe-claude-sonnet-5.jsonl
```

```cmd
cd /d %TEMP%
mkdir ep-model-probe-opus
cd ep-model-probe-opus
set ANTHROPIC_API_KEY=
set ANTHROPIC_AUTH_TOKEN=
set CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
echo Reply with the single word OK.| "C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe" -p --output-format stream-json --verbose --model claude-opus-5 --max-turns 1 --no-session-persistence --disable-slash-commands --strict-mcp-config --tools "" > probe-claude-opus-5.jsonl
```

`claude-sonnet-5` is the tier every B, C and R read uses. `claude-opus-5` is used only by EV2 escalations, which are off under the declared EV1 switches. The declaration pins both, so both are probed.

### 1.3 What to read in each `.jsonl` (one JSON object per line), and the pass / fail reading

| Line | Field | Pass | Fail |
|---|---|---|---|
| `{"type":"system","subtype":"init",…}` | `claude_code_version` | `"2.1.263"` | anything else |
| same | `model` | the probed id (`claude-sonnet-5` / `claude-opus-5`) | anything else |
| every `{"type":"assistant",…}` | `message.model` | the probed id | any other value. **`"<synthetic>"` marks a message the CLI made itself** (for example an API error), not a server statement: fail |
| the final `{"type":"result",…}` | `subtype`, `is_error`, `num_turns` | `"success"`, `false`, `1` | otherwise |
| same | `modelUsage` | exactly one key without `haiku`, equal to the probed id, with `canonicalModel` equal to it and `provider` `"firstParty"` | a different non-haiku key, or none |
| same | other `modelUsage` keys (for example a `claude-haiku-4-5` helper) | **record them**: each is at least one more request | — |

**Interpretation (A-10; R40-16, R40-17):**
- An alias, or an echoed configured id, is **never** proof of the underlying model.
- `modelUsage` keys and `canonicalModel` are the CLI's own record of the **requested** id.
- `message.model` is **the server's statement** of the model that produced the response. It is the strongest identity the CLI exposes. It is consistent evidence, **not proof** of the underlying model.
- **The request count cannot be verified offline.**
- **Pass:** both probes pass every row. The pins then agree with the server's own report. The served-model identity stays **UNRESOLVED** in the strict sense (a self-report).
- **Fail:** do not dispatch. Report the lines to the orchestrator. A different reported id needs a new declaration (new pins, new hash) and its own verification.
- **If the owner does not run the probe:** the owner may instead accept UNRESOLVED identity with the fail-closed runtime check (declaration `model_identity_detail`). That check compares every response's reported model with the pins: a mismatch makes the run INVALID. Its two limits: it compares the **requested** id that the CLI reports, and an echoed id (a response with no non-haiku key, a timeout) passes.

## 2. (b) The two-hash procedure (R38-07)

### 2.1 O: choose the token and compute its digest

The token is generated by the owner, high-entropy, held only by the owner (for example in a password manager), **never stored in any file**, and presented only in the environment variable `R34_OWNER_DISPATCH_TOKEN`. Use hex only, so that cmd.exe needs no quoting:

```cmd
"%PY%" -B -c "import secrets; print(secrets.token_hex(32))"
set R34_OWNER_DISPATCH_TOKEN=<the 64-hex token you just generated>
"%PY%" -B -c "import hashlib, os; print(hashlib.sha256(os.environ['R34_OWNER_DISPATCH_TOKEN'].encode('utf-8')).hexdigest())"
```

The **digest** is the sha256 of the token's UTF-8 bytes with no trailing newline, as **64 lower-case hex characters**. The digest becomes readable in the repository (inside the RUN file); the token never does.

### 2.2 O: check the frozen file, then write the RUN file

```cmd
certutil -hashfile "%PKG%\FRESH-VALIDATION-DECLARATION-R32-V2.json" SHA256
type "%PKG%\DECLARATION.sha256"
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r40.py fill_owner_digest --digest <digest>
```

- Both hashes must read `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af`.
- `fill_owner_digest` writes `FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json` beside the frozen file (it refuses if it exists). It is the frozen file with **only** `authorization.owner_token_sha256` changed from the placeholder to the digest. It prints `run_sha256`: the **RUN hash**. The owner computes it here.

### 2.3 V: independent verification of the RUN hash (read-only)

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r40.py verify_run_file --digest <digest> --run-sha <RUN hash>
certutil -hashfile "%PKG%\FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json" SHA256
```

`"verified": true` means: the frozen file still hashes to `DECLARATION.sha256`, the RUN file's bytes equal the frozen bytes with the single replacement, and its sha256 equals the RUN hash (and differs from the frozen hash). V reports the result to the owner **before** the budget authorization is written.

### 2.4 O: the budget authorization (the owner's message)

It names exactly:
1. the frozen hash `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af`;
2. the digest;
3. the RUN hash (computed in 2.2, independently verified in 2.3);
4. the absolute RUN-file path `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json`;
5. the absolute authorization path `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\OWNER-DISPATCH-AUTHORIZATION.json`;
6. the scope `m2-fresh-validation-r32-v2-2026-10-04` with exactly the limits `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` in `C:\t\r2x\ledger\r2x-ledger.sqlite`;
7. the first invocation: the `run` command of section 5.1.

The budget authorization covers the ceiling of 556 requests across all invocations. Each invocation still needs its own authorization file (2.5).

### 2.5 O: the authorization file (one per invocation)

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r40.py write_authorization --run-sha <RUN hash>
```

It refuses unless the RUN file verifies, and it writes `OWNER-DISPATCH-AUTHORIZATION.json` at the pinned path with exactly: `declaration_sha256` = **the RUN hash (never the frozen hash)**, `owner_token_sha256` = the digest, `authorized_by` = `"owner"`, `nonce` = a fresh random value (16–128 characters `[A-Za-z0-9_-]`). The owner may write the same four fields by hand instead. A file naming the frozen hash is refused by the guard, the runner and the scope command.

## 3. (c) The scope creation (R38-11; `SCOPE-CREATION-COMMAND.md`)

Immediately before the first invocation (the scope's `elapsed_s` counts from its creation), with the token still set:

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B create_scope_r40.py preview
"%PY%" -B create_scope_r40.py create --frozen-sha f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af --run-sha <RUN hash>
"%PY%" -B create_scope_r40.py status
```

- `preview` creates nothing and lists every precondition.
- `create` refuses, creating nothing, unless: the authorization file exists; the frozen hash given equals the file and `DECLARATION.sha256`; the RUN file hashes to the RUN hash and equals the single replacement; the authorization names the RUN hash, the digest, the owner and a nonce, and the token matches; the run folder does not exist; the bound harness verifies and the RUN declaration passes contract 4; the application's `ledger.py` is the bound one; and no scope of that name exists. It then creates the scope with the application's own `Ledger(path, scope, Limits(**limits))` and verifies it.
- **Verification** (`status`, read-only): `exists` true, `limits_equal_declared` true, `breaker` null, `scope_entries` 0, and `ledger_totals` = 483 entries (unchanged), **18** scopes (one more), 0 amendments. `create` itself prints the same check and `"created": true`.
- The scope is created **once**. Never for a resume, never under another name, never with other limits.

## 4. (d) The preflight: what the runner checks and records

The owner does not run a separate preflight: the runner runs it at every invocation, and every live lane runs it again. **Nothing is created before every check below has passed** (except where stated).

1. `verify_binding`: `BINDING-MANIFEST-R39.json` hashes to `a6f703b4…567b` and all 239 bound files re-hash equal.
2. `load_declaration` / `validate_declaration` (contract 4): the RUN file hashes to the given RUN hash; binding and run set equal; every key present: `run` (the folder `C:/t/r2x/r40-sandbox/r32-v2`), the pinned authorization path, a 64-hex digest, the parent budget 556 and lane allowances 240/240/40/36, the window 60 per 86,400 s, the lane switches, `lane_task_kinds`, `application_env` exactly `{"DRAWINGS_AI_REVIEW_ENABLED": "false"}`, `resume_policy` `full`, `decision_coverage_gate` `C_GE_B_ONLY`, the model-identity pins (full ids; provider `claude-code`; CLI `claude` / `2.1.263 (Claude Code)`), the provider environment with **compatible limits** (`project_bounds_r32.check_compatible`: the per-project limits ≥ 84; per-document 12 and 120 s), the ledger (path, scope, limits equal to the parent, `wrap_provider` true).
3. The candidate (`a8aacedd…`) and baseline (`3d5607d9…`) HEADs, both clean.
4. The truth built from the reference set and the population gate (identity 57, revision 38, decision 38); the run set (24 documents).
5. **Bounds recomputation:** `PROJECT-REQUEST-BOUNDS.json` recomputed from the run set, the truth and the bound code with the declared switches must equal the bound file (`99be01fb…1721`).
6. The ledger scope exists with exactly the declared limits and a closed breaker.
7. The guard preview: the pinned authorization file, its fields, the token digest, an unconsumed nonce.
8. Then: the run folder (first invocation only), the `WRITER.lock`, **`claude --version` recorded** (`CLI-VERSIONS.jsonl`; `inv-<n>\PROVIDER-IDENTITY.json` with the provider identity and the declared models) and compared with the pin and with the run's first invocation; then the nonce is **consumed** (`authorization\consumed-<…>.json`).
9. Every lane, before anything is built: the same live preflight; its `AI_EVIDENCE_*` switches exactly; every provider value in its environment **and** in the application's settings; **the `application_env` check** (the variable, the setting `drawings_ai_review_enabled` False, and `drawing_ai_review.enabled()` off); the guard's `verify` of this invocation's consumption record. Every response then passes the identity check.

This task ran all of it dry or offline (`PREFLIGHT-REPORT.md`): the lanes' environment checks pass for every declared value in both trees, which excludes the R39-18 failure class for these values.

## 5. (e) The invocations

### 5.1 Invocation 1: `run`

After sections 1 to 3, with the token set and the authorization file written:

```cmd
mkdir C:\t\r2x\r40-sandbox\r32-v2-owner-records
cd /d "%HARNESS%"
"%PY%" -B runner_r32.py run --mode live --declaration C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json --declaration-sha <RUN hash> --run-set C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json --binding C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/BINDING-MANIFEST-R39.json --binding-sha a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b
```

**Dispatch order inside the invocation:** B (24 documents registered, then processed; tripwire after each) → C only when no B document is DEFERRED (from copies of B's final database, after the state check) → R and P only when no C document is DEFERRED (R served from C's capture; P samples C's answered dispatches, frozen at P's first run) → offline scoring.

**Expected requests** (estimates, not limits):

| Lane | Planning | Structural maximum | Allowance |
|---|---|---|---|
| B | 6 | 48 | 240 |
| C | 112 | 240 (255 before the cap) | 240 |
| R | 10 | 40 (222 before the cap) | 40 |
| P | 17 | 36 | 36 |
| **Total** | **145** | **364** | **556** |

Retries of failed requests (5.2) are charges on top of these, bounded by the allowances, the parent 556 and the window.

**After the invocation (always):**

```cmd
move "%PKG%\OWNER-DISPATCH-AUTHORIZATION.json" C:\t\r2x\r40-sandbox\r32-v2-owner-records\AUTHORIZATION-inv-1.json
set R34_OWNER_DISPATCH_TOKEN=
type C:\t\r2x\r40-sandbox\r32-v2\RUN-STATE.json
```

Read the last entry of `invocations`: `status`, `run_state`, `comparison_state`, `resume_not_before_utc`, `deferred`. The full report is `C:\t\r2x\r40-sandbox\r32-v2\inv-1\out\RUN-REPORT.json`.

### 5.2 The deferral / resume loop (EP-27331; `resume_policy` `full`)

EP-27331 needs 63 requests at the planning estimate and 160 at the structural maximum; the window allows 60 per rolling 24 h over all lanes. A request the window would exceed is **deferred, not charged and not permanent**. Under `full`, a resume is allowed only at `resume_not_before_utc` (the latest structural `retry_at_full` of the deferred documents: the window then has room for everything the project can still ask, or is empty).

| EP-27331 demand | Invocations under `full` | The last invocation starts about |
|---|---|---|
| Planning estimate 63 | **2** | 24.3 h after the first |
| Structural maximum 160 | **3** | 48.5 h after the first |

Every other project needs at most 1 window at planning and 3 at its structural maximum, in the same invocations. **One owner authorization per invocation.** Retries of failed requests can add charges and invocations.

Loop, while the last `run_state` is `DEFERRED`:
1. Wait until `resume_not_before_utc`. **An earlier resume is refused and creates nothing; no authorization is consumed** (the resume gate runs before the guard).
2. Reconcile (V or O, read-only):
   ```cmd
   cd /d "%HARNESS%"
   "%PY%" -B allowance_r32.py audit C:\t\r2x\r40-sandbox\r32-v2\allowance.sqlite C:\t\r2x\r40-sandbox\r32-v2-owner-records\AUDIT-before-inv-<n>.json C:/t/r2x/ledger/r2x-ledger.sqlite m2-fresh-validation-r32-v2-2026-10-04
   cd /d "%PKG%\scripts"
   "%PY%" -B create_scope_r40.py status
   ```
   `reconciliation.consistent` must be true (ledger dispatch entries ≤ charges ≤ 556; every charge names its ledger entry or why not), the scope's breaker null and its limits equal. Any difference stops the run until it is explained.
3. A new authorization (2.5, a fresh nonce), the token set again.
4. The resume:
   ```cmd
   cd /d "%HARNESS%"
   "%PY%" -B runner_r32.py resume --mode live --declaration C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json --declaration-sha <RUN hash> --run-set C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json --binding C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/BINDING-MANIFEST-R39.json --binding-sha a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b
   ```
5. Withdraw the authorization (move it to `AUTHORIZATION-inv-<n>.json` in the owner records), clear the token, read `RUN-STATE.json`.

**What a resume does** (LIVE-RUN-CONTRACT v4 §4, §5, §13, carried verbatim in the declaration): every request with a bound **answer** is served, never re-sent; a reserved request without an outcome is served `interrupted_charged`, never re-sent; **a request whose dispatches all failed is dispatched again as a retry with its ordinal, charged** — a change from plan v2 §4 ("A resume never re-sends a bound fingerprint"; declaration `retry_rule`). No allowance, charge, refusal or terminal stop is ever reset. After the elapsed bound a deferred run is CLOSED.

### 5.3 Stop rules and terminal states

| Event | Lane | Effect |
|---|---|---|
| Critical acceptance on resolved truth | B | terminal; **INVALID**; C never starts or stops |
| Critical acceptance on resolved truth | C | C terminal; **RESULT** (NOT ELIGIBLE) |
| Critical acceptance on resolved truth | R or P | a reference finding; no stop |
| Critical acceptance on unresolved truth | any | reported only |
| Three consecutive provider failures | B / C / R or P | INVALID / INCOMPLETE / that lane only |
| Lane allowance, parent (requests, tokens, elapsed), ledger, breaker, guard refusal | any | a durable budget stop of that lane, never raised or reset; INCOMPLETE if B or C |
| Project-window refusal | any | the document is **DEFERRED** (not charged, not permanent) |
| Model-identity mismatch | any | `IDENTITY-INVALID.json`; **INVALID**; never resumed |
| Undeclared task kind or a request without the document's context | any | `CONTRACT-BREACH.json`; **INVALID**; never resumed |
| Pages left unread by the application's own per-document limits (reader cap 8, JobBudget 12 / 120 s, reader exception) | C, R (B: form read) | the document stays **COMPLETE**, every unread page listed and counted unread ('no_trigger' pages are not listed) |

| Terminal or run state | Meaning | What the owner does |
|---|---|---|
| **DEFERRED** | the invocation ended with deferred documents | wait for `resume_not_before_utc`, then 5.2 |
| **INCOMPLETE** | a B or C document was refused by a limit or is still deferred, a B/C budget stop, three C provider failures, or a deferral that cannot finish within the elapsed bound | a resume is allowed (it never undoes a budget stop); the comparison stays INCOMPLETE if the stop is durable; report it |
| **INVALID** | B safety stop, three B provider failures, identity mismatch, contract breach | stop; never resumed; report |
| **CLOSED** | a deferred run whose elapsed bound passed (closed INCOMPLETE by the runner) | stop; report |
| **RESULT** | C failed the safety gate | stop; report NOT ELIGIBLE |
| **FINISHED** | every lane complete and scored | section 7 |

## 6. Failure handling

- **A consumed authorization with no request sent (R39-18 risk).** The bound `validate_declaration` still accepts `"12.0"` / `"120.0"` for two limit keys; such a value would pass the preflight, consume the authorization, then fail closed in every lane with no request sent: a wasted invocation and a run folder. **This declaration writes integer strings** (`"96"`, `"600"`, `"12"`, `"120"`) and this task proved offline that every declared value parses in every lane (PREFLIGHT-REPORT §3, §6). If an invocation nevertheless ends `interrupted` or `refused` after the nonce was consumed: do not reuse the nonce; read `inv-<n>\out\RUN-REPORT.json` and the `lane-*.log` files; a resume (with a NEW authorization) is allowed after an interrupted or refused invocation; if the cause is a declared value, stop: a new declaration is needed.
- **The CLI-version dead-end.** The runner records `claude --version` **after** creating the run folder and **before** consuming the authorization. If that check refuses **invocation 1**, the run folder exists without an allowance: `run` is refused (the folder exists) and `resume` is refused (no allowance). The run cannot continue; a new declaration with a new stamp is needed; never delete the folder. Shown dry in PREFLIGHT-REPORT §7. **Prevention:** section 1.1 immediately before invocation 1. At a later invocation the same refusal leaves the run resumable once the CLI is back to `2.1.263 (Claude Code)`; no authorization is consumed.
- **A crashed runner.** Remove `C:\t\r2x\r40-sandbox\r32-v2\WRITER.lock` only when no runner process is alive; then resume with a new authorization.
- **A token or authorization mistake.** Every refusal of the guard happens before anything is sent; correct the file and retry with a fresh nonce.

## 7. (f) Scoring, the audit view, reconciliation and the final report

- **Scoring** runs offline at the end of every invocation: `score_lane_r32` per lane, then `score_bcr_r32.evaluate` with the candidate-level outcome. Outputs in `C:\t\r2x\r40-sandbox\r32-v2\inv-<n>\out\`: `SCORE-BCR-R32.json`, `lane-B.r32.json`, `lane-C.r32.json`, `lane-R.r32.json`, `RUN-REPORT.json`, `ALLOWANCE-AUDIT.json`. The last invocation's files are the result.
- **The audit view:** `ALLOWANCE-AUDIT.json` of each invocation (charges with outcome and ledger entry, refusals, retries, durable stops, reconciliation), plus the owner's own audit of 5.2 step 2.
- **The ledger live check:** `RUN-REPORT.json` `ledger_live_check.ok` true (growth only inside the declared scope, at most 556 dispatch entries, no new scope, no amendment).
- **The final report** carries, from `REPORT-TEMPLATE.md` and the declaration:
  1. the frozen hash, the RUN hash, the digest, the invocations (with their authorization hashes), the CLI version of each invocation;
  2. the candidate outcome and the comparison state; the per-field outcomes as diagnostics;
  3. **the decision coverage gate C ≥ B only, stated as a change from plan v2**, and **the mandatory C ≥ R diagnostic**: its state (COMPLETE or INCOMPLETE with why), the counts of C and R, and every document and page with missing coverage, each lane's class and the reason;
  4. the unread pages per lane (kind, reason, partial);
  5. every limit event, deferral, retry and refusal per document and page; `limit_incomplete` and `matched_exclusions`;
  6. requests and tokens per lane, actual, against the estimates; the returned model ids per lane from the identity logs;
  7. R and P as diagnostics with no credit (INCOMPLETE when truncated);
  8. the scope limitations (the unsupported-control shortfall) and what is not claimed;
  9. the statement "reference set independently AI-reviewed (Claude agents), not human-signed";
  10. the statuses: no default selected; M2 stays **CHANGES STILL REQUIRED** until an independent review and a separate owner decision; M3 not started.

## 8. (g) Forbidden

- Using the frozen declaration file or the frozen hash with the runner, the guard or the scope command.
- Any step before Verification 41 and the owner's budget authorization.
- Creating the scope more than once, under another name, with other limits, or before the authorization file names the RUN hash.
- Starting `lane_r32.py` directly or with a hand-made configuration; `python -O`; relative paths for `--declaration`, `--binding`, `--run-set`.
- Moving or deleting the run folder; reusing a nonce; writing the token into any file.
- Running the probe through the harness or inside the experiment's ledger scope.
- Raising, resetting or re-creating a lane allowance, the parent budget or the ledger limits; amending the scope.
- Selecting a default variant; M2 acceptance by this run; starting M3; production use or production database writes; any OneDrive change; opening a sealed project; any project outside the six; any use outside the declaration; human sign-off claims for the AI-reviewed labels.

## 9. Every dispatching or scope-creating command refuses without the authorization file (with the tests)

| Command | Refusal without `OWNER-DISPATCH-AUTHORIZATION.json` | Test (passed) |
|---|---|---|
| `runner_r32.py run --mode live` | "no owner dispatch authorization", before any folder | review39 `test_runner_r32.py::test_live_mode_with_a_complete_declaration_and_no_authorization_refuses_before_any_folder_exists`; this package's PREFLIGHT §9 |
| `runner_r32.py resume --mode live` | the same guard preview (a new authorization per invocation); "nothing to resume" when no run exists | same test; `test_resumable_rules` |
| a live lane started directly | "no owner dispatch authorization [lane C guard]" | review39 `test_runner_r32.py::test_a_direct_live_lane_invocation_is_refused_by_the_guard_without_authorization` |
| every request (`GuardedProvider`) | `dispatch_refused`; the real provider is never built | review39 `test_dispatch_guard_r32.py::test_no_authorization_file_exists_and_the_guard_refuses_without_one`, `::test_the_guarded_provider_never_builds_the_real_provider_when_refused`; this package's PREFLIGHT §10 |
| `create_scope_r40.py create` | "no owner dispatch authorization", nothing created | this package's `test_r40.py::test_scope_create_refuses_without_the_authorization_file` |

The other commands need no authorization because they cannot dispatch or touch the ledger: the probe (the owner's own CLI use, outside the experiment), `fill_owner_digest` and `write_authorization` (they write the owner's own files), `verify_run_file`, `create_scope_r40.py preview` / `status` and `allowance_r32.py audit` (read-only).
