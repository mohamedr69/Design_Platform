# Runbook: fresh validation R32, declaration v5 (review45 harness; R44-07)

**Status: the declaration is frozen and NOT authorized.** Nothing in this runbook may be done before (1) an independent verification of v5 (Verification 46), (2) the owner's choice of option 1 with the restated condition (b), recorded as a new register entry, and (3) a fresh owner D1/D2 naming the v5 hash (`owner_decision_required` in the declaration). Task R43-44 wrote this runbook and ran none of its steps: no probe, no token, no RUN file, no authorization file, no scope, no invocation, no `claude` process of any kind.

**This runbook delegates nothing.** Every step marked **O** is the owner's own act. The delegation in A-13 item 3 ("the owner's runbook steps are delegated to the session as they were for v3") was worded for a v4 run "tonight", lapsed, and does not carry over to v5. Any delegation needs a new owner decision.

| | |
|---|---|
| Frozen declaration | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\FRESH-VALIDATION-DECLARATION-R32-V5.json` |
| Frozen hash | **`db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`** (`DECLARATION.sha256`). It identifies what was reviewed. It is **never** given to the runner. |
| Superseded (never to be run) | v4 `e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9` (never authorized, never run); v3 `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40` (executed 2026-10-07, terminal); v2 `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` |
| RUN declaration (made by the owner, section 2) | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json` |
| Authorization file (written by the owner, pinned) | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\OWNER-DISPATCH-AUTHORIZATION.json` |
| Bound harness | `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\review45\scripts\harness-r32` (`BINDING-MANIFEST-R45-HARNESS.json` **`9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb`**; the review43 harness plus the dry-only baseline-facts drill; Verification 45 VERIFIED WITH CONDITIONS) |
| Python (bound) | `G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe` (Python 3.12.10, sha256 `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14`), always with `-B`, never with `-O` |
| pip freeze (bound, R42-09) | sha256 **`bd424a5c4692ab4c1f634705e59ded3784549a6f6c9072ffea9860fbf611bf7f`** (`preconditions.pip_freeze`) |
| CLI (pinned) | `C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe`, sha256 `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03`, line **`2.1.263 (Claude Code)`**. The merged installation's bundled 2.1.289 is never used. |
| Run folder (created by the first invocation) | `C:\t\r2x\r42-sandbox\r32-v5`. Never moved, never deleted. (`r32-v3` is the executed v3 folder; `r32-v4` was never created and must never be.) |
| Ledger and scope | `C:\t\r2x\ledger\r2x-ledger.sqlite`, scope **`m2-fresh-validation-r32-v5-2026-10-08`**, limits `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` |
| Ledger now | 484 entries / 18 scopes / 0 amendments (the v3 scope present; no v4 or v5 scope) |
| Disk floor | drive C at least **2 GiB** (2,147,483,648 bytes) free, checked by the runner and the scope command |
| Owner records folder (owner creates it) | `C:\t\r2x\r42-sandbox\r32-v5-owner-records` (outside the run folder and the package) |

**Conventions.**
- Every command is for **cmd.exe**, not Windows PowerShell 5.1. Every path is quoted: the package path contains a space and parentheses.
- **O** = the owner. **V** = an independent verifier (read-only steps).
- The reference set is independently AI-reviewed (Claude agents), not human-signed.
- The decision coverage gate is **C ≥ B only, a change from plan v2** (A-10); C ≥ R is a mandatory diagnostic.

Open one cmd.exe window and set these once (they hold no secret):

```cmd
set PKG=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5
set HARNESS=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\review45\scripts\harness-r32
set PY=G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe
set CLI=C:\Users\moham\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe
set PYTHONDONTWRITEBYTECODE=1
set GIT_OPTIONAL_LOCKS=0
set DISABLE_AUTOUPDATER=1
set PIP_DISABLE_PIP_VERSION_CHECK=1
set R43_HARNESS_RUN=
```

`DISABLE_AUTOUPDATER=1` keeps the CLI from updating itself in this window; the owner keeps the CLI at 2.1.263 for the whole run (no `winget upgrade`). `R43_HARNESS_RUN` must be empty: the package scripts then use the bound review45 folder itself.

## 0. Before anything: what must already exist

1. Verification 46 of this package (v4→v5 diff limited to the harness rebind and the disclosures), with no blocker.
2. The owner's register entry choosing option 1 and restating condition (b) as "the review45 drill passes on F009/F020/F030" — knowing its limit R45-08: the drill does **not** show that the model's form reading of F009 and F020 is safe (`disclosures`, AI-on limit).
3. The owner's fresh D1 (served-model identity, section 1.3) and D2 (the budget authorization, section 2.4), naming `db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`.

If any of the three is missing: **stop**.

## 1. (a) The owner's checks before anything else

### 1.1 The pip-freeze equality (R42-09; condition (c) of the lapsed A-13 item 3, carried as a precondition)

```cmd
"%PY%" -B -c "import subprocess, hashlib, sys; o = subprocess.run([sys.executable, '-B', '-m', 'pip', 'freeze'], capture_output=True).stdout; print(hashlib.sha256(o).hexdigest())"
```

Expected: exactly `bd424a5c4692ab4c1f634705e59ded3784549a6f6c9072ffea9860fbf611bf7f`. Any other value: **stop**; install, upgrade or remove nothing in that venv while the experiment is open (the merged installation's `setup.bat` must not run). Repeat before invocation 1 and before **every** resume.

### 1.2 The CLI file, its version, the disk (no request)

```cmd
certutil -hashfile "%CLI%" SHA256
"%CLI%" --version
"%PY%" -B -c "import shutil; print(shutil.disk_usage('C:/').free)"
```

Expected: the sha256 is `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03`; the version line is exactly **`2.1.263 (Claude Code)`**; the free space is at least **2147483648**, and no other heavy writer is running. Any other result: **stop**. The runner checks the same three things itself, before anything is created.

### 1.3 D1: the served-model identity (unchanged from v3)

The served-model identity is **UNRESOLVED** offline (`model_identity_detail`). The owner either runs the probe below (it uses the owner's subscription: one request per model; its count cannot be verified offline) or accepts UNRESOLVED identity with the fail-closed runtime check and its two stated limits.

```cmd
cd /d %TEMP%
mkdir ep-model-probe-sonnet
cd ep-model-probe-sonnet
set ANTHROPIC_API_KEY=
set ANTHROPIC_AUTH_TOKEN=
set CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
echo Reply with the single word OK.| "%CLI%" -p --output-format stream-json --verbose --model claude-sonnet-5 --max-turns 1 --no-session-persistence --disable-slash-commands --strict-mcp-config --tools "" > probe-claude-sonnet-5.jsonl
```

Then the same in `ep-model-probe-opus` with `claude-opus-5` and `probe-claude-opus-5.jsonl`. Read: `system`/`init` `claude_code_version` "2.1.263" and `model` = the probed id; every `assistant` `message.model` = the probed id (`"<synthetic>"` fails); the `result` line `subtype` "success", `is_error` false, `num_turns` 1; `modelUsage` exactly one non-haiku key equal to the probed id. `message.model` is the server's statement, consistent evidence and **not proof**.

## 2. (b) The two-hash procedure

### 2.1 O: the token and its digest

```cmd
"%PY%" -B -c "import secrets; print(secrets.token_hex(32))"
set R34_OWNER_DISPATCH_TOKEN=<the 64-hex token you just generated>
"%PY%" -B -c "import hashlib, os; print(hashlib.sha256(os.environ['R34_OWNER_DISPATCH_TOKEN'].encode('utf-8')).hexdigest())"
```

The token is never written to a file, a message or a log.

### 2.2 O: check the frozen file, then write the RUN file

```cmd
certutil -hashfile "%PKG%\FRESH-VALIDATION-DECLARATION-R32-V5.json" SHA256
type "%PKG%\DECLARATION.sha256"
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r42.py fill_owner_digest --digest <digest>
```

Both hashes read `db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`. `fill_owner_digest` writes `FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json` (only the digest placeholder replaced) and prints the **RUN hash**.

### 2.3 V: independent verification of the RUN hash (read-only)

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r42.py verify_run_file --digest <digest> --run-sha <RUN hash>
```

`"verified": true` is required before the budget authorization.

### 2.4 O: D2, the budget authorization (the owner's message)

It names exactly: the frozen hash `db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`; the digest; the RUN hash; the absolute RUN-file path `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json`; the absolute authorization path `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\OWNER-DISPATCH-AUTHORIZATION.json`; the scope `m2-fresh-validation-r32-v5-2026-10-08` with exactly the limits above in `C:\t\r2x\ledger\r2x-ledger.sqlite`; the first invocation (section 5.1); and, if the owner chooses it, the multi-invocation form of section 2.5 (b). The budget itself is `BUDGET-CARD-V6.md`.

### 2.5 O: the authorization file

(a) **Per invocation (the default):**

```cmd
cd /d "%PKG%\scripts"
"%PY%" -B build_declaration_r42.py write_authorization --run-sha <RUN hash>
```

(b) **One approval for all planned resumptions (a proposal the owner may use or not):**

```cmd
"%PY%" -B build_declaration_r42.py write_authorization --run-sha <RUN hash> --invocations 3
```

Each invocation consumes exactly one nonce, only after the run's allowance exists; a consumed nonce is never reusable; the file can never raise, reset or re-create an allowance, the parent, the window or the scope; a fourth invocation needs a new file. A file naming a frozen hash (v5's, v4's, v3's or v2's) or the executed v3 RUN hash is refused.

## 3. (c) The scope creation — by the owner alone (`SCOPE-CREATION-COMMAND.md`)

Immediately before the first invocation (the scope's `elapsed_s` counts from its creation), with the token set and sections 1.1 and 1.2 just repeated, **the owner** runs the three commands of `SCOPE-CREATION-COMMAND.md` (preview, create, status). No one else creates the scope. `status` afterwards: `exists` true, `limits_equal_declared` true, `breaker` null, `scope_entries` 0, `ledger_totals` 484 / **19** / 0.

## 4. (d) What the runner checks, and in which order (contract v5 section 14)

1. **Before anything is created, re-opened or consumed:** the binding (`BINDING-MANIFEST-R45-HARNESS.json` `9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb`, every one of its 629 bound files); contract 5 (`validate_declaration`, including the isolation key = the review45 harness folder); the bound interpreter; the CLI file's sha256; the free disk ≥ 2 GiB; the HEADs (frozen-r13 `7ec3d2cf`, cand-r30n `436daef2`); the truth and the population gate; the run set; the bounds; the ledger scope; the resume rules or the re-entry proof; the guard preview; then `"%CLI%" --version`.
2. The run folder (invocation 1), `RUN-STATE.json`, `WRITER.lock`, the version and identity record.
3. The capture store bound to the run key; the allowance created atomically.
4. **Only then** the authorization nonce is consumed.
5. The lanes; the audit; the scoring. In C, R and P the application's global provider is a refusing provider.

The runner refuses `--dry-baseline-facts` and every other dry drill flag in live mode.

## 5. (e) The invocations

### 5.1 Invocation 1: `run`

```cmd
mkdir C:\t\r2x\r42-sandbox\r32-v5-owner-records
cd /d "%HARNESS%"
"%PY%" -B runner_r32.py run --mode live --declaration "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v5/FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json" --declaration-sha <RUN hash> --run-set "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json" --binding "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review45/BINDING-MANIFEST-R45-HARNESS.json" --binding-sha 9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb
```

**Expected requests** (estimates, not limits): B 6 / 48, C 112 / 240, R 10 / 40, P 17 / 36 (planning / structural maximum); total 145 / 364 against the parent 556 (unchanged).

**What can still stop the run early (disclosed):** for F009 and F020 the application asks the model for a form reading after the deterministic pass; a wrongly read page-1 reference, revision or code is a resolved critical in B and ends the run INVALID (the v3 stop rule). The review45 drill rehearsed only the deterministic reading (R45-08).

**After the invocation (always):** move the authorization file to the owner records (per-invocation form) or leave it until its nonces are consumed (multi-invocation form); clear the token (`set R34_OWNER_DISPATCH_TOKEN=`); read `C:\t\r2x\r42-sandbox\r32-v5\RUN-STATE.json` (last entry of `invocations`).

### 5.2 Re-entry after a failure before the allowance existed

If invocation 1 ended `interrupted` or `refused` and `C:\t\r2x\r42-sandbox\r32-v5\allowance.sqlite` does **not** exist, repeat **the same `run` command** with the same, unconsumed authorization (re-entry proof `REENTRY-<n>.json`). Never delete or edit the folder. If the allowance exists, use `resume` (5.3).

### 5.3 The resume rules (EP-27331; `resume_policy` `full`)

EP-27331 needs 2 invocations at the planning estimate (the last starts about 24.3 h after the first) and 3 at the structural maximum (about 48.5 h). While the last `run_state` is `DEFERRED`:
1. Wait until `resume_not_before_utc` (an earlier resume is refused, creates nothing, consumes nothing).
2. Repeat **section 1.1 (pip freeze)** and **section 1.2** (CLI hash, version line, disk ≥ 2 GiB).
3. Reconcile (read-only): `cd /d "%HARNESS%"` then `"%PY%" -B allowance_r32.py audit C:\t\r2x\r42-sandbox\r32-v5\allowance.sqlite C:\t\r2x\r42-sandbox\r32-v5-owner-records\AUDIT-before-inv-<n>.json C:/t/r2x/ledger/r2x-ledger.sqlite m2-fresh-validation-r32-v5-2026-10-08`, and `cd /d "%PKG%\scripts"` then `"%PY%" -B create_scope_r42.py status`; `reconciliation.consistent` must be true.
4. A new authorization file (2.5 a), or the next nonce of the multi-invocation file (2.5 b); the token set again.
5. The same command as 5.1 with `resume` instead of `run`.

A resume serves every bound answer, serves an interrupted dispatch `interrupted_charged`, and dispatches a failed request again as a charged retry (a change from plan v2 §4). No allowance, charge, refusal or terminal stop is ever reset.

### 5.4 Stop rules and terminal states

Unchanged (declaration `stop_rules`): INVALID (B safety stop — a critical acceptance on resolved truth in B —, three B failures, identity mismatch, contract breach including a request that reaches the global provider in C, R or P), RESULT (C safety stop), INCOMPLETE, DEFERRED, CLOSED, FINISHED.

## 6. Failure handling

- **Before the allowance exists:** nothing was consumed. Fix the cause (sections 1.1, 1.2) and repeat the same `run` command (5.2).
- **After the allowance exists but before the nonce was consumed:** `resume` with the same authorization.
- **After the nonce was consumed:** `resume` with a new authorization (or the next nonce).
- **A crashed runner:** remove `C:\t\r2x\r42-sandbox\r32-v5\WRITER.lock` only when no runner process is alive.
- The RUN file must equal the frozen bytes with only the digest replaced; this equality is the protection against altered values.

## 7. (f) Scoring, audit, the final report

As in v3's runbook section 7, with the v5 run folder (`C:\t\r2x\r42-sandbox\r32-v5\inv-<n>\out\`) and the decision coverage gate **C ≥ B only** with the mandatory C ≥ R diagnostic.

## 8. (g) Forbidden

Everything v3 and v4 forbade, plus: running v4 (`e0a93c46…`), v3 (`9a55fa7b…`, executed) or v2; creating `r32-v4` or a v4 scope; reusing the v3 run folder, scope, owner records or nonces; running the review43 or review42 harness or any harness other than `PILOT/review45/scripts/harness-r32`; passing `--dry-baseline-facts` or any dry drill flag to a live invocation; the merged installation's bundled CLI 2.1.289, its `.env`, data or code in any lane; editing a run folder's `REENTRY-<n>.json`, `RUN-STATE.json`, consumption records or allowance; lowering the disk floor or raising `resume_authorization.max_invocations_per_file`; any step of this runbook by anyone but the owner (O) or a read-only verifier (V).

## 9. Every dispatching or scope-creating command refuses without the authorization file

| Command | Refusal | Evidence |
|---|---|---|
| `runner_r32.py run --mode live` | "no owner dispatch authorization", before any folder and before `--version` | review45 `tests/full` (`test_runner_r32`, `test_runner_order_r42`); v4 `dry-run/PREFLIGHT-RESULTS.json` steps 8–10 (runner code unchanged outside the drill branches) |
| `runner_r32.py resume --mode live` | the same guard preview; a consumed nonce refused | `test_runner_order_r42.py` |
| every request (`GuardedProvider`) | `dispatch_refused` | `test_dispatch_guard_r32.py` |
| an application `get_provider()` call in C, R, P | `dispatch_refused`, INVALID | `test_global_provider_r42.py`; this package's demonstration `global_provider` |
| `create_scope_r42.py create` | "no owner dispatch authorization", nothing created | v4's `scope/SCOPE-CREATE-REFUSED-OUTPUT.json` (the v5 copy differs only in the manifest, the pinned path text and one more refused hash; not run by task R43-44) |
