# Runbook: fresh validation R32, corrected declaration v3 (ORCH-10, merged installation)

**Status: the declaration is frozen and NOT authorized.** Nothing in this runbook may be done before Verification 42 and the owner's own decisions and budget authorization. This task ran none of the owner steps: no probe, no token, no RUN file, no authorization file, no scope, no invocation, no `claude` process of any kind.

| | |
|---|---|
| Frozen declaration | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\FRESH-VALIDATION-DECLARATION-R32-V3.json` |
| Frozen hash | **`9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`** (`DECLARATION.sha256`). It identifies what was reviewed. It is **never** given to the runner. |
| Superseded (never to be run) | v2 `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` (its bindings name the absent Desktop installation) |
| RUN declaration (made by the owner, section 2) | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json` |
| Authorization file (written by the owner, pinned) | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\OWNER-DISPATCH-AUTHORIZATION.json` |
| Bound harness | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\review42\scripts\harness-r32` (`BINDING-MANIFEST-R42.json` `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`; review42 manifest `ab2bc40d6ab5a45b0f7dca710f188b1e9f2a9cb4da80118177c7b1df9658e782`) |
| Python (bound) | `G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe` (Python 3.12.10, sha256 `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14`), always with `-B`, never with `-O` |
| CLI (pinned) | `C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe`, sha256 `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03`, line **`2.1.263 (Claude Code)`**. The merged installation's bundled 2.1.289 is never used. |
| Run folder (created by the first invocation) | `C:\t\r2x\r42-sandbox\r32-v3`. Never moved, never deleted. |
| Ledger and scope | `C:\t\r2x\ledger\r2x-ledger.sqlite`, scope **`m2-fresh-validation-r32-v3-2026-10-06`**, limits `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` |
| Disk floor | drive C at least **2 GiB** (2,147,483,648 bytes) free, checked by the runner and the scope command (condition C1) |
| Owner records folder (owner creates it) | `C:\t\r2x\r42-sandbox\r32-v3-owner-records` (outside the run folder and the package) |

**Conventions.**
- Every command is for **cmd.exe**, not Windows PowerShell 5.1 (PowerShell 5.1 drops an empty `""` argument, and the probe needs one). Every path is quoted: the package path contains a space and parentheses.
- **O** = the owner. **V** = the orchestrator or an independent verifier (read-only steps).
- The reference set is independently AI-reviewed (Claude agents), not human-signed.
- **The decision coverage gate is C ≥ B only. This is a change from plan v2** (whose gate was C ≥ B and C ≥ R), ruled by the owner (A-10). C ≥ R is a mandatory diagnostic.

Open one cmd.exe window and set these once (they hold no secret):

```cmd
set PKG=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3
set HARNESS=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\review42\scripts\harness-r32
set PY=G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe
set CLI=C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe
set PYTHONDONTWRITEBYTECODE=1
set GIT_OPTIONAL_LOCKS=0
set DISABLE_AUTOUPDATER=1
```

`DISABLE_AUTOUPDATER=1` keeps the CLI from updating itself in this window (R41-11); the owner also keeps the CLI at 2.1.263 for the whole run (no `winget upgrade`).

## 1. (a) The owner's checks before anything else

### 1.1 The CLI file, its version, the disk (no request)

```cmd
certutil -hashfile "%CLI%" SHA256
"%CLI%" --version
"%PY%" -B -c "import shutil; print(shutil.disk_usage('C:/').free)"
```

Expected: the sha256 is `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03`; the version line is exactly **`2.1.263 (Claude Code)`**, printed within a few seconds; the free space is at least **2147483648**, and no other heavy writer is running (ep-platform test runs, Codex processes, other sessions writing to temp). Any other result: **stop**. The runner checks the same three things itself, before anything is created (section 4), but the owner's own check comes first.

### 1.2 The model-identity probe (A-10 item 2; unchanged from v2, now with the absolute path)

Not run by this task; it uses the owner's subscription; its request count cannot be verified offline.

```cmd
cd /d %TEMP%
mkdir ep-model-probe-sonnet
cd ep-model-probe-sonnet
set ANTHROPIC_API_KEY=
set ANTHROPIC_AUTH_TOKEN=
set CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
echo Reply with the single word OK.| "%CLI%" -p --output-format stream-json --verbose --model claude-sonnet-5 --max-turns 1 --no-session-persistence --disable-slash-commands --strict-mcp-config --tools "" > probe-claude-sonnet-5.jsonl
```

Then the same in `ep-model-probe-opus` with `claude-opus-5` and `probe-claude-opus-5.jsonl`. Read the lines as in v2's RUNBOOK section 1.3 (unchanged): `system`/`init` `claude_code_version` "2.1.263" and `model` = the probed id; every `assistant` `message.model` = the probed id (`"<synthetic>"` fails); the `result` line `subtype` "success", `is_error` false, `num_turns` 1; `modelUsage` exactly one non-haiku key equal to the probed id, `canonicalModel` equal, `provider` "firstParty"; record any other key. `message.model` is the server's statement, consistent evidence and **not proof**. If the owner does not run the probe, he may accept UNRESOLVED identity with the fail-closed runtime check and its two limits (declaration `model_identity_detail`).

## 2. (b) The two-hash procedure (R38-07; unchanged method)

### 2.1 O: the token and its digest

```cmd
"%PY%" -B -c "import secrets; print(secrets.token_hex(32))"
set R34_OWNER_DISPATCH_TOKEN=<the 64-hex token you just generated>
"%PY%" -B -c "import hashlib, os; print(hashlib.sha256(os.environ['R34_OWNER_DISPATCH_TOKEN'].encode('utf-8')).hexdigest())"
```

### 2.2 O: check the frozen file, then write the RUN file

```cmd
certutil -hashfile "%PKG%\FRESH-VALIDATION-DECLARATION-R32-V3.json" SHA256
type "%PKG%\DECLARATION.sha256"
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r42.py fill_owner_digest --digest <digest>
```

Both hashes read `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`. `fill_owner_digest` writes `FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json` (only the digest replaced) and prints the **RUN hash**.

### 2.3 V: independent verification of the RUN hash (read-only)

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r42.py verify_run_file --digest <digest> --run-sha <RUN hash>
```

`"verified": true` is required before the budget authorization.

### 2.4 O: the budget authorization (the owner's message)

It names exactly: the frozen hash `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`; the digest; the RUN hash; the absolute RUN-file path `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json`; the absolute authorization path `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\OWNER-DISPATCH-AUTHORIZATION.json`; the scope `m2-fresh-validation-r32-v3-2026-10-06` with exactly the limits `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` in `C:\t\r2x\ledger\r2x-ledger.sqlite`; the first invocation (section 5.1); and, if the owner chooses it, the multi-invocation authorization of section 2.5 (b).

### 2.5 O: the authorization file

(a) **Per invocation (the default, as in v2):**

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r42.py write_authorization --run-sha <RUN hash>
```

(b) **One approval for all planned resumptions (A-11 section 4; a proposal the owner may use or not):**

```cmd
"%PY%" -B build_declaration_r42.py write_authorization --run-sha <RUN hash> --invocations 3
```

It writes exactly `authorized_by`, `declaration_sha256` (the RUN hash), `owner_token_sha256`, `invocations_authorized` 3 and three fresh nonces. Each invocation consumes exactly the next nonce; a consumed nonce is never reusable; the file can never raise, reset or re-create an allowance, the parent, the window or the scope; a fourth invocation needs a new file. With (b), a resume needs no new file until all three are consumed; the owner still sets the token at every invocation. A file naming the frozen hash is refused (guard, runner and scope command).

## 3. (c) The scope creation (`SCOPE-CREATION-COMMAND.md`)

Immediately before the first invocation (the scope's `elapsed_s` counts from its creation), with the token set and section 1.1 just repeated:

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B create_scope_r42.py preview
"%PY%" -B create_scope_r42.py create --frozen-sha 9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40 --run-sha <RUN hash>
"%PY%" -B create_scope_r42.py status
```

`create` refuses, creating nothing, unless every precondition holds -- now including the bound interpreter, the CLI file's sha256 and the disk floor (condition C1). `status`: `exists` true, `limits_equal_declared` true, `breaker` null, `scope_entries` 0, `ledger_totals` 483 / **18** / 0.

## 4. (d) What the runner checks, and in which order (contract v5 section 14)

1. **Before anything is created, re-opened or consumed:** the binding (`BINDING-MANIFEST-R42.json` `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`, every bound file); contract 5 (`validate_declaration`); the bound interpreter; **the CLI file's sha256**; **the free disk ≥ 2 GiB**; the HEADs; the truth and the population gate; the run set; the bounds recomputation; the ledger scope; the resume rules (a resume) or the re-entry proof (a `run` on an existing folder); the guard preview; then **`"%CLI%" --version`** compared with `2.1.263 (Claude Code)` and with the run's first line.
2. The run folder (invocation 1), `RUN-STATE.json`, `WRITER.lock`, the version and identity record.
3. The capture store bound to the run key; the allowance created atomically.
4. **Only then** the authorization nonce is consumed.
5. The lanes (each re-runs the live preflight, its switches, provider values, `application_env`, **isolation from the merged installation**, the interpreter, the guard's `verify`); the audit; the scoring. In lanes C, R and P the application's global provider is a refusing provider (R40-04).

## 5. (e) The invocations

### 5.1 Invocation 1: `run`

```cmd
mkdir C:\t\r2x\r42-sandbox\r32-v3-owner-records
cd /d "%HARNESS%"
"%PY%" -B runner_r32.py run --mode live --declaration "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v3/FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json" --declaration-sha <RUN hash> --run-set "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json" --binding "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review42/BINDING-MANIFEST-R42.json" --binding-sha 00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c
```

**Expected requests** (estimates, not limits): B 6 / 48, C 112 / 240, R 10 / 40, P 17 / 36 (planning / structural maximum); total 145 / 364 against the parent 556 (unchanged from v2).

**After the invocation (always):** move the authorization file to the owner records (per-invocation form) or leave it in place until its nonces are consumed (multi-invocation form); clear the token (`set R34_OWNER_DISPATCH_TOKEN=`); read `C:\t\r2x\r42-sandbox\r32-v3\RUN-STATE.json` (last entry of `invocations`).

### 5.2 Re-entry after a failure before the allowance existed (new in v3)

If invocation 1 ended `interrupted` or `refused` and `C:\t\r2x\r42-sandbox\r32-v3\allowance.sqlite` does **not** exist, repeat **the same `run` command** (with the same, unconsumed authorization). The runner proves from the folder's records that no allowance was created, no nonce consumed and no request charged (`REENTRY-<n>.json`) and continues. Never delete or edit the folder. If the allowance exists, use `resume` (5.3).

### 5.3 The deferral / resume loop (EP-27331; `resume_policy` `full`; unchanged from v2)

EP-27331 needs 2 invocations at the planning estimate (the last starts about 24.3 h after the first) and 3 at the structural maximum (about 48.5 h). While the last `run_state` is `DEFERRED`:
1. Wait until `resume_not_before_utc` (an earlier resume is refused, creates nothing, consumes nothing).
2. Repeat section 1.1 (CLI hash, version line, disk ≥ 2 GiB) -- the runner re-checks them before consuming the resume's nonce.
3. Reconcile (read-only): `cd /d "%HARNESS%"` then `"%PY%" -B allowance_r32.py audit C:\t\r2x\r42-sandbox\r32-v3\allowance.sqlite C:\t\r2x\r42-sandbox\r32-v3-owner-records\AUDIT-before-inv-<n>.json C:/t/r2x/ledger/r2x-ledger.sqlite m2-fresh-validation-r32-v3-2026-10-06` and `create_scope_r42.py status`; `reconciliation.consistent` must be true.
4. A new authorization file (2.5 a), or the next nonce of the multi-invocation file (2.5 b); the token set again.
5. The same command as 5.1 with `resume` instead of `run`.

A resume serves every bound answer, serves an interrupted dispatch `interrupted_charged`, and dispatches a failed request again as a charged retry -- **a change from plan v2 §4** (declaration `retry_rule`). No allowance, charge, refusal or terminal stop is ever reset.

### 5.4 Stop rules and terminal states

Unchanged from v2 (declaration `stop_rules`): INVALID (B safety stop, three B failures, identity mismatch, contract breach -- now including a request that reaches the global provider in C, R or P), RESULT (C safety stop), INCOMPLETE, DEFERRED, CLOSED, FINISHED.

## 6. Failure handling

- **Before the allowance exists** (a CLI hash or version refusal, a timeout of `--version`, the disk below the floor, a full disk while recording, an interruption at the allowance creation): nothing was consumed. Fix the cause (section 1.1) and repeat the same `run` command (5.2).
- **After the allowance exists but before the nonce was consumed:** `resume` with the same authorization.
- **After the nonce was consumed:** `resume` with a new authorization (or the next nonce).
- **A crashed runner:** remove `C:\t\r2x\r42-sandbox\r32-v3\WRITER.lock` only when no runner process is alive.
- **A '12.0'-style value** cannot reach the runner: the RUN file must equal the frozen bytes with only the digest replaced (R41-12 corrected: no runbook step checks integer strings; this equality is the protection).

## 7. (f) Scoring, audit, reconciliation, the final report

Unchanged from v2's RUNBOOK section 7, with the v3 run folder (`C:\t\r2x\r42-sandbox\r32-v3\inv-<n>\out\`) and the decision coverage gate stated as **C ≥ B only, a change from plan v2**, with the mandatory C ≥ R diagnostic.

## 8. (g) Forbidden

Everything v2 forbade, plus: the frozen v2 declaration; the merged installation's bundled CLI 2.1.289, its `.env`, data or code in any lane; editing a run folder's `REENTRY-<n>.json`, `RUN-STATE.json`, consumption records or allowance; lowering the disk floor or raising `resume_authorization.max_invocations_per_file`.

## 9. Every dispatching or scope-creating command refuses without the authorization file

| Command | Refusal | Test (review42 junit, passed) |
|---|---|---|
| `runner_r32.py run --mode live` | "no owner dispatch authorization", before any folder and before `--version` | `test_runner_r32.py`, `test_runner_order_r42.py`; PREFLIGHT §10 |
| `runner_r32.py resume --mode live` | the same guard preview; a consumed nonce refused | `test_runner_order_r42.py::test_live_E_...` |
| a live lane started directly | refused by the same guard | `test_runner_r32.py` |
| every request (`GuardedProvider`) | `dispatch_refused` | `test_dispatch_guard_r32.py` |
| an application `get_provider()` call in C, R, P | `dispatch_refused`, INVALID | `test_global_provider_r42.py` |
| `create_scope_r42.py create` | "no owner dispatch authorization", nothing created | this package's `test_r42.py` |
