"""ORCH-10 (R42PORT-IMPL): write the owner-facing documents of PILOT/declaration-r32-v3/ ONCE each -- RUNBOOK.md,
SCOPE-CREATION-COMMAND.md, DECLARATION-SUMMARY.md, BUDGET-DECISION-CARD.v5.md, PREFLIGHT-REPORT.md and COMMANDS.md -- with
every hash and number read from the frozen declaration and the evidence files (nothing typed by hand that a file holds).
Usage: make_v3_docs_r42.py"""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

P = C.PACKAGE
W = lambda p: str(p).replace("/", "\\")  # noqa: E731


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def main() -> int:
    decl = load(P / C.DECLARATION_NAME)
    fsha = C.sha256_file(P / C.DECLARATION_NAME)
    bsha = C.sha256_file(C.BINDING42)
    r42man = C.sha256_file(C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json")
    pre = load(P / "dry-run/PREFLIGHT-RESULTS.json")
    dry = load(P / "dry-run/DRY-EXERCISE.json")
    diff = load(P / "DECLARATION-DIFF.json")
    t42 = load(C.REVIEW42 / "tests/SUMMARY.json")
    demos = load(C.REVIEW42 / "evidence/demos/DEMOS-R42.json")
    path = load(P / "evidence/PATHLEN-PROBE.json")["summary"]
    interp = load(P / "evidence/INTERPRETER-CHECK.json")
    limits = json.dumps(decl["ledger"]["limits"], sort_keys=True)
    run_path, auth_path = P / C.RUN_NAME, P / C.AUTH_NAME
    harness = C.HARNESS42
    rs = C.RUN_SET
    cli = decl["model_identity"]["cli"]
    probes = pre["checks"]["3_negative_probes"]
    loops = {k: v["invocations"] for k, v in dry["deferral_loops"].items()}
    xp = dry["cross_project_drill"]["loop"]
    run_cmd = (f'"%PY%" -B runner_r32.py run --mode live --declaration "{run_path.as_posix()}" --declaration-sha <RUN hash> '
               f'--run-set "{rs.as_posix()}" --binding "{C.BINDING42.as_posix()}" --binding-sha {bsha}')
    files = {}
    files["RUNBOOK.md"] = f"""# Runbook: fresh validation R32, corrected declaration v3 (ORCH-10, merged installation)

**Status: the declaration is frozen and NOT authorized.** Nothing in this runbook may be done before Verification 42 and the owner's own decisions and budget authorization. This task ran none of the owner steps: no probe, no token, no RUN file, no authorization file, no scope, no invocation, no `claude` process of any kind.

| | |
|---|---|
| Frozen declaration | `{W(P / C.DECLARATION_NAME)}` |
| Frozen hash | **`{fsha}`** (`DECLARATION.sha256`). It identifies what was reviewed. It is **never** given to the runner. |
| Superseded (never to be run) | v2 `{C.V2_SHA}` (its bindings name the absent Desktop installation) |
| RUN declaration (made by the owner, section 2) | `{W(run_path)}` |
| Authorization file (written by the owner, pinned) | `{W(auth_path)}` |
| Bound harness | `{W(harness)}` (`BINDING-MANIFEST-R42.json` `{bsha}`; review42 manifest `{r42man}`) |
| Python (bound) | `{W(C.PY)}` (Python {decl['interpreter']['version']}, sha256 `{decl['interpreter']['sha256']}`), always with `-B`, never with `-O` |
| CLI (pinned) | `{W(cli['path'])}`, sha256 `{cli['sha256']}`, line **`{cli['version']}`**. The merged installation's bundled 2.1.289 is never used. |
| Run folder (created by the first invocation) | `{W(C.RUN_FOLDER)}`. Never moved, never deleted. |
| Ledger and scope | `{W(C.AI_LEDGER)}`, scope **`{C.SCOPE}`**, limits `{limits}` |
| Disk floor | drive C at least **2 GiB** (2,147,483,648 bytes) free, checked by the runner and the scope command (condition C1) |
| Owner records folder (owner creates it) | `C:\\t\\r2x\\r42-sandbox\\r32-v3-owner-records` (outside the run folder and the package) |

**Conventions.**
- Every command is for **cmd.exe**, not Windows PowerShell 5.1 (PowerShell 5.1 drops an empty `""` argument, and the probe needs one). Every path is quoted: the package path contains a space and parentheses.
- **O** = the owner. **V** = the orchestrator or an independent verifier (read-only steps).
- The reference set is independently AI-reviewed (Claude agents), not human-signed.
- **The decision coverage gate is C ≥ B only. This is a change from plan v2** (whose gate was C ≥ B and C ≥ R), ruled by the owner (A-10). C ≥ R is a mandatory diagnostic.

Open one cmd.exe window and set these once (they hold no secret):

```cmd
set PKG={W(P)}
set HARNESS={W(harness)}
set PY={W(C.PY)}
set CLI={W(cli['path'])}
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

Expected: the sha256 is `{cli['sha256']}`; the version line is exactly **`{cli['version']}`**, printed within a few seconds; the free space is at least **2147483648**, and no other heavy writer is running (ep-platform test runs, Codex processes, other sessions writing to temp). Any other result: **stop**. The runner checks the same three things itself, before anything is created (section 4), but the owner's own check comes first.

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
certutil -hashfile "%PKG%\\{C.DECLARATION_NAME}" SHA256
type "%PKG%\\DECLARATION.sha256"
cd /d "%PKG%\\scripts"
"%PY%" -B build_declaration_r42.py fill_owner_digest --digest <digest>
```

Both hashes read `{fsha}`. `fill_owner_digest` writes `{C.RUN_NAME}` (only the digest replaced) and prints the **RUN hash**.

### 2.3 V: independent verification of the RUN hash (read-only)

```cmd
cd /d "%PKG%\\scripts"
"%PY%" -B build_declaration_r42.py verify_run_file --digest <digest> --run-sha <RUN hash>
```

`"verified": true` is required before the budget authorization.

### 2.4 O: the budget authorization (the owner's message)

It names exactly: the frozen hash `{fsha}`; the digest; the RUN hash; the absolute RUN-file path `{W(run_path)}`; the absolute authorization path `{W(auth_path)}`; the scope `{C.SCOPE}` with exactly the limits `{limits}` in `{W(C.AI_LEDGER)}`; the first invocation (section 5.1); and, if the owner chooses it, the multi-invocation authorization of section 2.5 (b).

### 2.5 O: the authorization file

(a) **Per invocation (the default, as in v2):**

```cmd
cd /d "%PKG%\\scripts"
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
cd /d "%PKG%\\scripts"
"%PY%" -B create_scope_r42.py preview
"%PY%" -B create_scope_r42.py create --frozen-sha {fsha} --run-sha <RUN hash>
"%PY%" -B create_scope_r42.py status
```

`create` refuses, creating nothing, unless every precondition holds -- now including the bound interpreter, the CLI file's sha256 and the disk floor (condition C1). `status`: `exists` true, `limits_equal_declared` true, `breaker` null, `scope_entries` 0, `ledger_totals` 483 / **18** / 0.

## 4. (d) What the runner checks, and in which order (contract v5 section 14)

1. **Before anything is created, re-opened or consumed:** the binding (`BINDING-MANIFEST-R42.json` `{bsha}`, every bound file); contract 5 (`validate_declaration`); the bound interpreter; **the CLI file's sha256**; **the free disk ≥ 2 GiB**; the HEADs; the truth and the population gate; the run set; the bounds recomputation; the ledger scope; the resume rules (a resume) or the re-entry proof (a `run` on an existing folder); the guard preview; then **`"%CLI%" --version`** compared with `{cli['version']}` and with the run's first line.
2. The run folder (invocation 1), `RUN-STATE.json`, `WRITER.lock`, the version and identity record.
3. The capture store bound to the run key; the allowance created atomically.
4. **Only then** the authorization nonce is consumed.
5. The lanes (each re-runs the live preflight, its switches, provider values, `application_env`, **isolation from the merged installation**, the interpreter, the guard's `verify`); the audit; the scoring. In lanes C, R and P the application's global provider is a refusing provider (R40-04).

## 5. (e) The invocations

### 5.1 Invocation 1: `run`

```cmd
mkdir C:\\t\\r2x\\r42-sandbox\\r32-v3-owner-records
cd /d "%HARNESS%"
{run_cmd}
```

**Expected requests** (estimates, not limits): B 6 / 48, C 112 / 240, R 10 / 40, P 17 / 36 (planning / structural maximum); total 145 / 364 against the parent 556 (unchanged from v2).

**After the invocation (always):** move the authorization file to the owner records (per-invocation form) or leave it in place until its nonces are consumed (multi-invocation form); clear the token (`set R34_OWNER_DISPATCH_TOKEN=`); read `C:\\t\\r2x\\r42-sandbox\\r32-v3\\RUN-STATE.json` (last entry of `invocations`).

### 5.2 Re-entry after a failure before the allowance existed (new in v3)

If invocation 1 ended `interrupted` or `refused` and `C:\\t\\r2x\\r42-sandbox\\r32-v3\\allowance.sqlite` does **not** exist, repeat **the same `run` command** (with the same, unconsumed authorization). The runner proves from the folder's records that no allowance was created, no nonce consumed and no request charged (`REENTRY-<n>.json`) and continues. Never delete or edit the folder. If the allowance exists, use `resume` (5.3).

### 5.3 The deferral / resume loop (EP-27331; `resume_policy` `full`; unchanged from v2)

EP-27331 needs 2 invocations at the planning estimate (the last starts about 24.3 h after the first) and 3 at the structural maximum (about 48.5 h). While the last `run_state` is `DEFERRED`:
1. Wait until `resume_not_before_utc` (an earlier resume is refused, creates nothing, consumes nothing).
2. Repeat section 1.1 (CLI hash, version line, disk ≥ 2 GiB) -- the runner re-checks them before consuming the resume's nonce.
3. Reconcile (read-only): `cd /d "%HARNESS%"` then `"%PY%" -B allowance_r32.py audit C:\\t\\r2x\\r42-sandbox\\r32-v3\\allowance.sqlite C:\\t\\r2x\\r42-sandbox\\r32-v3-owner-records\\AUDIT-before-inv-<n>.json C:/t/r2x/ledger/r2x-ledger.sqlite {C.SCOPE}` and `create_scope_r42.py status`; `reconciliation.consistent` must be true.
4. A new authorization file (2.5 a), or the next nonce of the multi-invocation file (2.5 b); the token set again.
5. The same command as 5.1 with `resume` instead of `run`.

A resume serves every bound answer, serves an interrupted dispatch `interrupted_charged`, and dispatches a failed request again as a charged retry -- **a change from plan v2 §4** (declaration `retry_rule`). No allowance, charge, refusal or terminal stop is ever reset.

### 5.4 Stop rules and terminal states

Unchanged from v2 (declaration `stop_rules`): INVALID (B safety stop, three B failures, identity mismatch, contract breach -- now including a request that reaches the global provider in C, R or P), RESULT (C safety stop), INCOMPLETE, DEFERRED, CLOSED, FINISHED.

## 6. Failure handling

- **Before the allowance exists** (a CLI hash or version refusal, a timeout of `--version`, the disk below the floor, a full disk while recording, an interruption at the allowance creation): nothing was consumed. Fix the cause (section 1.1) and repeat the same `run` command (5.2).
- **After the allowance exists but before the nonce was consumed:** `resume` with the same authorization.
- **After the nonce was consumed:** `resume` with a new authorization (or the next nonce).
- **A crashed runner:** remove `C:\\t\\r2x\\r42-sandbox\\r32-v3\\WRITER.lock` only when no runner process is alive.
- **A '12.0'-style value** cannot reach the runner: the RUN file must equal the frozen bytes with only the digest replaced (R41-12 corrected: no runbook step checks integer strings; this equality is the protection).

## 7. (f) Scoring, audit, reconciliation, the final report

Unchanged from v2's RUNBOOK section 7, with the v3 run folder (`C:\\t\\r2x\\r42-sandbox\\r32-v3\\inv-<n>\\out\\`) and the decision coverage gate stated as **C ≥ B only, a change from plan v2**, with the mandatory C ≥ R diagnostic.

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
"""
    files["SCOPE-CREATION-COMMAND.md"] = f"""# Scope-creation command: `create_scope_r42.py` (declaration v3)

- **Script:** `PILOT/declaration-r32-v3/scripts/create_scope_r42.py`. Reviewed with the declaration. **Not executed by this task** (only `preview` and the refusals; a positive creation only on a throwaway SQLite file in a test).
- **Creates:** once, the scope **`{C.SCOPE}`** in `{C.AI_LEDGER.as_posix()}` with exactly `{limits}` (= the parent budget plus the per-request estimates), a closed breaker and no entries, through the candidate application's own `app.ai.ledger.Ledger` (`ledger.py` `d9f92297…`).
- **When:** by the owner, after the budget authorization, immediately before invocation 1, with the token in `R34_OWNER_DISPATCH_TOKEN`.

```cmd
cd /d "{W(P / 'scripts')}"
"{W(C.PY)}" -B create_scope_r42.py preview
"{W(C.PY)}" -B create_scope_r42.py create --frozen-sha {fsha} --run-sha <RUN hash>
"{W(C.PY)}" -B create_scope_r42.py status
```

**`create` refuses, creating nothing, unless, in order:** (1) the authorization file exists at `{W(auth_path)}`; (2) `--frozen-sha` equals the file and `DECLARATION.sha256`; (3) the RUN file hashes to `--run-sha` (never a frozen hash, neither v3's nor v2's) and equals the frozen bytes with only the digest replaced; (4) the authorization (either form) names the RUN hash, the digest, the owner and its nonce(s), and the token matches (nothing is consumed); (5) the run folder `{C.RUN_FOLDER.as_posix()}` does not exist; (6) `BINDING-MANIFEST-R42` verifies and the RUN declaration passes contract 5; (7) **ORCH-10:** the bound interpreter runs the command, the pinned CLI file hashes to `{cli['sha256']}` (read as bytes), and drive C has at least 2 GiB free (condition C1); (8) `ledger.py` is the bound one; (9) no scope of that name exists.

**Dry evidence:** `scope/SCOPE-PREVIEW-OUTPUT.json` (nothing created; ledger unchanged) and `scope/SCOPE-CREATE-REFUSED-OUTPUT.json` (refused: no authorization file). Tests: `tests/test_r42.xml` (every refusal above, including the disk floor, and one positive creation on a throwaway file).
"""
    files["DECLARATION-SUMMARY.md"] = f"""# Declaration summary: fresh validation R32, corrected declaration v3 (ORCH-10; frozen, NOT authorized)

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v3/{C.DECLARATION_NAME}`, sha256 **`{fsha}`**, contract `{decl['contract']}` |
| **Supersedes** | v2 `{C.V2_SHA}` (A-11: not runnable as declared -- its bindings name the absent Desktop installation and venv; never authorized, never run, never to be run) |
| **Bound harness** | `PILOT/review42/` (`BINDING-MANIFEST-R42` `{bsha}`; manifest `{r42man}`); pending Verification 42 |
| **Status** | `executed: false`, `budget_approved: false`, authorization "none; owner decision pending" |
| **Reference set** | `r32-labels-reviewed-2` (`89c60e9d…b9a6`): reference set independently AI-reviewed (Claude agents), not human-signed |
| **Standing** | M2 CHANGES STILL REQUIRED. M3 not started. |

## 1. What did not change (DECLARATION-DIFF: protected values all unchanged: {diff['protected_all_ok']})

Every number and rule of v2: the arms and switches, the task kinds, the run set (`9058f3d6…7ce8`, 24 documents), the truth (`4e237a4e…e064`), the reference set, the parent budget 556 / 16,300,000 / 3,260,000 / 604,800 s, the lane allowances B 240 / C 240 / R 40 / P 36, the project window 60 per 86,400 s, the thresholds, the application limits "96" / "600" / "12" / "120", **the decision coverage gate C ≥ B only -- a change from plan v2 (A-10)** with C ≥ R a mandatory diagnostic, `resume_policy` `full`, the stop rules, the concentration results, the model pins `claude-sonnet-5` / `claude-opus-5` / `claude-code` and the CLI line `2.1.263 (Claude Code)`.

## 2. What changed (ORCH-10; each item answers a finding or an owner decision)

| Item | v3 | Answers |
|---|---|---|
| Portability | every binding re-pointed to the merged installation; every bound file re-hashes equal | A-11 |
| Interpreter | bound: `{C.PY}` (path, sha256, version) | 2.1.1 |
| CLI | pinned by absolute path, file sha256 `{cli['sha256'][:12]}…` and the exact line; the bundled 2.1.289 never used | 2.1.4 |
| Isolation | no lane value, setting, import path or module under the merged installation except the venv and the harness; the merged `.env` never read | 2.1.5 |
| Global provider | a fail-closed refusing provider in C, R and P; B unchanged | R40-04 (option 2) |
| Invocation order | every check (CLI file, version, disk) before the run folder; the nonce consumed only after the allowance and the capture store exist; re-entry of a folder without an allowance; resume re-checks | R41-09, R41-11 |
| Disk precondition | 2 GiB on C, enforced by the runner and the scope command, only upward | R41-10 (C1) |
| Authorization | the multi-invocation form as a **proposal** (max 3 per file); the per-invocation form unchanged | A-11 §4 |
| Stamp / folder / scope | `r32-v3` / `{C.RUN_FOLDER.as_posix()}` / `{C.SCOPE}` | new declaration |
| Statements | R41-12 (no runbook integer-string check; the RUN-file equality is the protection) and R41-13 (the dry exercise named exactly) corrected | R41-12, R41-13 |

## 3. Evidence

- Preflight: {probes['count']} negative probes ({probes['carried_from_v2']} carried, {probes['new_for_contract_5']} new), all as expected: {probes['all_as_expected']}; binding, bounds, lane environments (with isolation), interpreter, CLI file and disk pass; the runner and the guard refuse with no folder and no `--version` (`PREFLIGHT-REPORT.md`).
- Dry exercise: the single 24-document run {dry['single']['report']['run_state']}; six per-project runs; EP-27331 loops {list(loops.values())} invocations; the cross-project drill {xp['invocations']} invocations; the CLI-version case no longer a dead-end; 0 model requests; AI ledger 483 / 17 / 0 throughout.
- review42: {t42['total']['tests']} tests, {t42['total']['failures']} failures; {sum(1 for v in demos['demos'].values() if v['ok'])}/{len(demos['demos'])} scripted-provider demonstrations passed.

## 4. Owner decisions (unchanged in substance; none taken by this task)

1. **Served-model identity:** UNRESOLVED offline. Run the probe (RUNBOOK 1.2) or accept UNRESOLVED identity with the fail-closed runtime check and its two limits.
2. **R40-04:** closed in code by option 2 (A-11); the owner may note the stated residual risk (`REQUEST-PATHS.md` §5).
3. **Condition C1:** now enforced in code; the owner still stops other heavy writers before every invocation.
4. **One approval for all planned resumptions:** use it (one file, 3 nonces) or keep one file per invocation.
5. **Acknowledgements:** R40-15 (application-internal page limits leave a document COMPLETE with unread pages), R40-13 (the failed-read retry is a change from plan v2 §4), the output-token bound location, keeping the CLI at 2.1.263.
6. **Owner-confirmable values** (a change means a new hash): the per-project limit "96", the scope name, the run folder, `AI_EFFORT` low, `resume_policy` `full`, the disk floor, the bound 3.
7. **The budget authorization itself:** 556 requests, 16.3 M input / 3.26 M output tokens, 7 days, the scope with exact limits, the first invocation; it names the frozen hash `{fsha}`, the digest, the independently verified RUN hash and the absolute paths. Cost: unknown (subscription), never zero.

## 5. Statuses, stated separately

- **Correction readiness:** delivered for Verification 42; not self-approved.
- **Accuracy:** none; no prediction exists.
- **Label truth:** reference set independently AI-reviewed (Claude agents), not human-signed.
- **Permissions and budget:** eligibility only (A-06); nothing authorized.
- **M2:** CHANGES STILL REQUIRED. **M3:** not started.
"""
    files["BUDGET-DECISION-CARD.v5.md"] = f"""# Budget decision card v5: fresh validation R32, corrected declaration v3 (proposal, NOT authorized)

This supersedes `declaration-r32-v2/BUDGET-DECISION-CARD.v4.md` (its declaration `{C.V2_SHA[:12]}…` cannot be run as declared and is superseded by A-11). **Nothing is authorized.** The numbers are v2's, unchanged.

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v3/{C.DECLARATION_NAME}`, frozen sha256 `{fsha}` |
| **Bound harness** | review42 (`BINDING-MANIFEST-R42` `{bsha}`), pending Verification 42 |
| **Decision coverage gate** | **C ≥ B only: a change from plan v2** (A-10); C ≥ R a mandatory diagnostic |

## 1. The ceiling (unchanged)

| Item | Value |
|---|---|
| Requests | **556** (B 240, C 240, R 40, P 36; no borrowing; never raised, reset or refunded) |
| Tokens | 16,300,000 input / 3,260,000 output (per request estimates 90,000 / 20,000) |
| Elapsed | 604,800 s (7 days) from the scope's creation and from the first invocation; the earlier stops first |
| Project window | 60 per project per rolling 24 h over all lanes (a refusal defers, never charges) |

## 2. Estimated usage (unchanged; estimates, not limits)

Planning 145 (B 6, C 112, R 10, P 17); structural maximum 364 (B 48, C 240, R 40, P 36). EP-27331: 63.0 / 160 requests, 2 or 3 invocations. At the structural maximum with every request at p95 size, the 3.26 M output bound would refuse first (in lane P).

## 3. Invocations and approvals

| Case | Invocations | Per-invocation form | One approval for all planned resumptions (proposal, A-11 §4) |
|---|---|---|---|
| Planning estimate | 2 | 2 authorization files | 1 file with 3 nonces (one left unused) |
| Structural maximum | 3 | 3 files | 1 file with 3 nonces |
| Retries | can add invocations | one file each | a new file after the third |

Either way each invocation consumes exactly one nonce, only after the run's allowance exists (a failure before consumes nothing), and a resume before the `full` time is refused and consumes nothing. The owner's token is presented at every invocation in both forms.

## 4. Preconditions now enforced in code (v3)

The CLI file's sha256 and its `--version` line, the bound interpreter and **at least 2 GiB free on drive C** are checked before invocation 1, before every resume and before the scope creation.

## 5. Cost

**Unknown, never zero** (`claude-code` on the owner's subscription; no price configured).

## 6. What signing authorizes / does not authorize

Signing authorizes only: the RUN declaration derived from `{fsha}` with the owner's digest; the creation, once, of `{C.SCOPE}` with exactly `{limits}`; invocation 1 and each resume with its own nonce (per-invocation files, or one multi-invocation file of at most 3 nonces if the owner chooses); requests by B, C, R, P on the six cohort projects' frozen staged copies within the ceiling. It does **not** authorize raising, resetting or re-creating any allowance or limit, a second scope, the frozen file with the runner, a default variant, M2 acceptance, M3, production use, any OneDrive change, a sealed project, any other project, or human sign-off claims for the AI-reviewed labels.
"""
    pc = pre["checks"]
    files["PREFLIGHT-REPORT.md"] = f"""# Preflight report: declaration v3 (ORCH-10; dry, offline; no request, no `claude` process)

- **Declaration:** `{fsha}`; **binding:** `{bsha}`; **harness:** `{harness.as_posix()}`.
- **Results file:** `dry-run/PREFLIGHT-RESULTS.json` (`{C.sha256_file(P / 'dry-run/PREFLIGHT-RESULTS.json')}`), ok **{pre['ok']}**.

## 1. Contract 5

- As written: **{pc['1_validate_declaration_as_written']['result']}** ({pc['1_validate_declaration_as_written']['reason']}).
- In memory with a dummy digest (never written): **{pc['2_validate_declaration_in_memory_dummy_digest']['result']}**.
- Negative probes: **{sum(r['as_expected'] for r in probes['rows'])}/{probes['count']} as expected** ({probes['carried_from_v2']} carried from v2 and adjusted to contract 5, {probes['new_for_contract_5']} new for the CLI pin, the interpreter, the disk floor, the isolation, the resume authorization and the global provider). As in v2 the contract still accepts '12.0' / '120.0' (R39-18; the RUN-file equality keeps them out); it accepts an interpreter sha256 of another file and the bundled CLI path, which the runtime checks (`verify_interpreter`, `verify_cli`) refuse.

## 2. Binding, bounds, lanes, interpreter, CLI file, disk

- `verify_binding`: **{pc['4_verify_binding']['result']}**, {pc['4_verify_binding']['files_verified']} files (extended-length opens).
- Bounds recomputed and equal: **{pc['5_verify_bounds']['result']}**; population gate {pc['5_verify_bounds']['population_gate']}; {pc['5_verify_bounds']['run_set_documents']} documents.
- Lane environments offline (live environment): {', '.join(f"{k} {v['ok']}" for k, v in pc['6_lane_environment_checks_offline']['lanes'].items())} -- switches, provider values, `application_env`, drawings-AI review off, **isolation**, **interpreter** (`dry-run/lane-env/`).
- Interpreter {pc['7_interpreter_cli_file_disk']['interpreter']['verified']}; CLI file `{pc['7_interpreter_cli_file_disk']['cli_file']['cli_sha256'][:12]}…` ({pc['7_interpreter_cli_file_disk']['cli_file']['cli_bytes']} bytes, read only, never executed); free disk {pc['7_interpreter_cli_file_disk']['free_disk']['free_bytes']} bytes ≥ {pc['7_interpreter_cli_file_disk']['free_disk']['min_free_bytes']}.
- Interpreter against the trees (`evidence/INTERPRETER-CHECK.json`): requirement differences {dict((k, len(v['requirement_differences'])) for k, v in interp['trees'].items())}; lane modules import {dict((k, v['needed_modules_import']) for k, v in interp['trees'].items())}; other app modules failing {dict((k, len(v['other_modules_failed'])) for k, v in interp['trees'].items())}; differences from the recorded merged-venv freeze: {json.dumps(interp['interpreter']['freeze_record']['differences'])}.

## 3. Refusals before any folder

- The runner as the owner would type it, without a RUN file or token: **{pc['8_runner_live_subprocess_without_run_file_or_token']['result']}**.
- In process with the in-memory RUN copy: **{pc['9_runner_live_in_process_in_memory_run_copy']['result']}** at the ledger scope.
- With the scope pretended: **{pc['10_runner_live_in_process_scope_pretended']['result']}** by the guard ("no owner dispatch authorization"), before the run folder and **before `--version`** (version runner calls: {pc['10_runner_live_in_process_scope_pretended']['version_runner_called']}).
- The guard alone: **{pc['11_dispatch_guard']['result']}**; the scope command: **{pc['12_scope_command']['result']}** (preview created nothing; create refused).
- Invariants: {json.dumps(pre['invariants'])}.

## 4. Path lengths (`evidence/PATHLEN-PROBE.json`)

LongPathsEnabled {path['long_paths_enabled']}; bound paths max {path['bound_max']}; package paths max {path['package_max']}; live staged PDFs max {path['live_staged_max']} ({path['live_staged_max_inv_1_to_9']} for inv-1..9); run-folder records max {path['live_run_folder_files_max']}; owner records max {path['owner_records_max']}. {path['statement']}.

## 5. The dry exercise (`dry-run/DRY-EXERCISE.json`, ok {dry['ok']})

- **Single run** over all 24 documents: {dry['single']['report']['run_state']} (R41-13: the run v2 could not make).
- **Six per-project runs:** {', '.join(f"{k} {v['report']['run_state']}" for k, v in dry['split']['runs'].items())}.
- **EP-27331 deferral loops under `full`:** {loops} invocations; every early resume refused and nothing created.
- **Cross-project drill** (24 documents, window 10 per 20 s): {xp['invocations']} invocations, {xp['early_resumes_refused']} early resume(s) refused, final {xp['final_run_state']}.
- **The CLI-version case:** a version refusal at invocation 1 created nothing and the same `run` then finished ({dry['cli_version_case']['ok']}).
- Model requests {dry['model_requests_total']}; AI ledger 483 / 17 / 0 throughout ({dry['ai_ledger_unchanged_483_17_0']}); the live run folder absent ({dry['live_run_folder_absent']}).
"""
    files["COMMANDS.md"] = f"""# Commands (declaration-r32-v3, ORCH-10): reproducible from a clean cmd.exe shell

```bat
set PY="{W(C.PY)}"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set GIT_OPTIONAL_LOCKS=0
set PYTHONPATH=C:\\t\\iso\\work\\r2x\\r42\\guard
set PKG={W(P)}
cd /d "%PKG%\\scripts"
```

`PYTHONPATH` loads the R42 audit guard (a byte copy is in `scripts\\guard\\sitecustomize.py`) in every process and child. Never `-O`; `R34_OWNER_DISPATCH_TOKEN` is never set by these commands. The review42 package must be complete first (`PILOT\\review42\\COMMANDS.md`).

**What these commands never do:** a provider or model request; a `claude` invocation of any kind; a ledger scope, token, authorization file or RUN file; a write outside `C:\\t\\iso\\work\\r2x\\r42`, `C:\\t\\r2x\\r42-sandbox` and the two new packages (the response ledger's one append excepted).

```bat
rem 0. evidence: the interpreter against the trees, the path lengths
%PY% -B interpreter_check_r42.py "%PKG%\\evidence\\INTERPRETER-CHECK.json"
%PY% -B pathlen_probe_r42.py "%PKG%\\evidence\\PATHLEN-PROBE.json" <a finished dry run folder>

rem 1. the declaration (show: print only; write: once), then the diff
%PY% -B build_declaration_r42.py show
%PY% -B build_declaration_r42.py write
%PY% -B diff_declaration_r42.py

rem 2. the dry preflight
%PY% -B preflight_r42.py

rem 3. the dry exercise, in phases (finish copies into dry-run\\ only when every phase succeeded)
%PY% -B dry_exercise_r42.py new-tag
%PY% -B dry_exercise_r42.py single <tag>
%PY% -B dry_exercise_r42.py split <tag>
%PY% -B dry_exercise_r42.py loops <tag>
%PY% -B dry_exercise_r42.py xproject <tag>
%PY% -B dry_exercise_r42.py cli <tag>
%PY% -B dry_exercise_r42.py finish <tag>

rem 4. the package tests (junit)
%PY% -B run_tests_r42pkg.py C:\\t\\r2x\\r42-sandbox\\pytest-<new>

rem 5. the documents, the after-snapshot, the package check, the manifest (LAST), the one response append
%PY% -B make_v3_docs_r42.py
%PY% -B snapshot_r42.py "%PKG%\\evidence\\SNAPSHOT-AFTER.json"
%PY% -B package_r42.py check v3
%PY% -B package_r42.py manifest v3
%PY% -B append_response_r42.py
```

Read-only helpers: `create_scope_r42.py preview | status`; `build_declaration_r42.py verify_run_file --digest <hex> --run-sha <hex>`.
Owner-only (never run by this task): `build_declaration_r42.py fill_owner_digest | write_authorization`, `create_scope_r42.py create`, `runner_r32.py run|resume --mode live` (RUNBOOK.md).
"""
    for name, text in files.items():
        if (P / name).exists():
            raise SystemExit(f"refused: {name} exists (written once)")
    for name, text in files.items():
        C.write_once(P / name, text)
        print("written", name, C.sha256_file(P / name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
