# Scope-creation command (Verification 38 R38-11; owner decision A-09 point 8)

**The command below is reviewed with the declaration and is NOT executed by this task.** Only its `preview` mode and its refusal without an authorization file were run. No ledger scope exists: the AI ledger reads 483 entries / 17 scopes / 0 amendments before and after.

| | |
|---|---|
| Script | `C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\scripts\create_scope_r40.py` |
| Ledger | `C:\t\r2x\ledger\r2x-ledger.sqlite` |
| Scope name | **`m2-fresh-validation-r32-v2-2026-10-04`** (no scope of that name exists) |
| Limits (equal to the parent budget, contract 4) | `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` |
| What creates it | the application's own code, `app.ai.ledger.Ledger(path, scope, Limits(**limits))` from `C:\t\iso\cand-r29\backend` (`ledger.py` `d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca`, equal in both trees): one immediate transaction inserts the new scope with exactly these limits, `created_at` now and a closed (null) breaker |
| Frozen declaration | `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` |
| **Decision coverage gate** | **C ≥ B only: a change from plan v2** (whose gate was C ≥ B and C ≥ R), ruled by the owner (A-10); not an unchanged gate. C ≥ R is a mandatory diagnostic and never decides eligibility. |

## 1. The exact command (owner only, cmd.exe)

Immediately before the first invocation (RUNBOOK section 3): the scope's `elapsed_s` counts from its creation, so any wait counts.

```cmd
set PY=C:\Users\moham\Desktop\dev\dev\ep-platform\backend\venv\Scripts\python.exe
set PYTHONDONTWRITEBYTECODE=1
set GIT_OPTIONAL_LOCKS=0
set R34_OWNER_DISPATCH_TOKEN=<the owner's token>
cd /d C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v2\scripts
"%PY%" -B create_scope_r40.py preview
"%PY%" -B create_scope_r40.py create --frozen-sha f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af --run-sha <RUN hash>
"%PY%" -B create_scope_r40.py status
```

## 2. Preconditions (checked in this order by `create`; any failure creates nothing, exit code 3)

1. **The authorization file exists** at the pinned path `…\declaration-r32-v2\OWNER-DISPATCH-AUTHORIZATION.json`.
2. **Declaration hash equality:** `--frozen-sha` equals the frozen file's sha256 and `DECLARATION.sha256`.
3. **The RUN file:** `FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json` exists, hashes to `--run-sha`, which is not the frozen hash, and equals the frozen bytes with only the placeholder replaced by the digest it binds (`build_declaration_r40.fill_owner_digest`).
4. **The authorization names the RUN hash** (never the frozen hash), the same digest, `authorized_by` `owner` and a nonce of 16–128 `[A-Za-z0-9_-]`; **the presented token's sha256 equals the digest** (`dispatch_guard_r32.validate`, pure). The nonce is **not** consumed here; the runner consumes it at the first invocation.
5. **The run folder `C:\t\r2x\r40-sandbox\r32-v2` does not exist.** The scope is created once, before the first invocation, never for a resume.
6. **The bound harness verifies** (`BINDING-MANIFEST-R39`, all 239 bound files) and **the RUN declaration passes contract 4** (`preflight_r32.validate_declaration`).
7. **The application's ledger module** is the bound one (`d9f92297…`).
8. **No scope of that name exists** in the ledger (opened `mode=ro`).

**After creating,** `create` verifies read-only, and prints `"created": true` only when all of these hold: the scope exists; its limits equal the declared ones; the breaker is null; it holds 0 entries; the ledger has exactly one more scope, the same entries and the same amendments; and `preflight_r32.verify_ledger_scope` accepts it. It writes no file and never prints the token.

**Verification afterwards** (`status`, read-only): `exists` true, `limits_equal_declared` true, `breaker` null, `scope_entries` 0, `ledger_totals` 483 / **18** / 0. The runner checks the same scope again at every invocation (`verify_ledger_scope`).

## 3. The preview output (run by this task; nothing was created)

`scope/SCOPE-PREVIEW-OUTPUT.json` (`eae4ff4f25f135236cda48556fc808e3a5357336db4a79515a8b10a5aceb6b54`), in full:

```json
{
 "create_command": "create_scope_r40.py create --frozen-sha <frozen hash> --run-sha <RUN hash>  (owner only; token in R34_OWNER_DISPATCH_TOKEN)",
 "frozen_declaration_sha256": "f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af",
 "ledger": "C:/t/r2x/ledger/r2x-ledger.sqlite",
 "ledger_after": {"entries": 483, "limit_amendments": 0, "scope_names_sha256": "a037785aba929442f67a179eff144e06c2777f72a42bc4741f6165f952db663e", "scopes": 17},
 "ledger_before": {"entries": 483, "limit_amendments": 0, "scope_names_sha256": "a037785aba929442f67a179eff144e06c2777f72a42bc4741f6165f952db663e", "scopes": 17},
 "ledger_unchanged": true,
 "limits": {"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556},
 "mode": "preview (read-only; nothing created)",
 "preconditions_now": {
  "1 authorization file at the pinned path": {"exists": false, "state": "NOT YET (the owner writes it after the budget authorization)"},
  "2 frozen declaration hash": {"equals_DECLARATION.sha256": true, "sha256": "f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af"},
  "3 RUN file": {"exists": false, "state": "NOT YET (the owner writes it with build_declaration_r40.py fill_owner_digest)"},
  "4 authorization names the RUN hash, the digest, the owner, a nonce; the token matches": {"state": "checked in create mode only"},
  "5 run folder absent": {"absent": true, "path": "C:/t/r2x/r40-sandbox/r32-v2"},
  "6 bound harness and contract 4": {"state": "checked in create mode (verify_binding a6f703b4...; validate_declaration on the RUN file)"},
  "7 application ledger module": {"equals_bound": true, "sha256": "d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca"},
  "8 no scope of that name": {"exists": false, "scope": "m2-fresh-validation-r32-v2-2026-10-04"}
 },
 "scope": "m2-fresh-validation-r32-v2-2026-10-04",
 "would_call": "sys.path.insert(0, 'C:/t/iso/cand-r29/backend'); from app.ai.ledger import Ledger, Limits; Ledger('C:/t/r2x/ledger/r2x-ledger.sqlite', 'm2-fresh-validation-r32-v2-2026-10-04', Limits(**{\"elapsed_s\": 604800, \"input_tokens\": 16300000, \"output_tokens\": 3260000, \"per_request_input\": 90000, \"per_request_output\": 20000, \"requests\": 556}))",
 "would_create": {"entries": "483 (unchanged)", "limit_amendments": "0 (unchanged)", "new_scope": {"breaker": null, "entries": 0, "limits": {"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}}, "scopes": "17 -> 18"}
}
```

(The paths of preconditions 1, 3 and 7 are abbreviated here; the file holds them in full.)

The `create` attempt without an authorization file (`scope/SCOPE-CREATE-REFUSED-OUTPUT.json`, `135f60f6a4c8ef48e70d65995eb84a42c6cdd27391a18a5152a488d9ebd86a62`): `{"created": false, "refused": "refused: no owner dispatch authorization (…/declaration-r32-v2/OWNER-DISPATCH-AUTHORIZATION.json does not exist)"}`, exit code 3, ledger unchanged.

## 4. Tests (`scripts/test_r40.py`, junit `tests/test_r40.xml`)

| Test | Proves |
|---|---|
| `test_scope_preview_creates_nothing` | the preview leaves the AI ledger at 483 / 17 / 0 and no scope of that name |
| `test_scope_status_is_read_only_and_reports_no_scope_yet` | the status mode is read-only |
| `test_scope_create_refuses_without_the_authorization_file` | the real mode refuses first, without the file; the ledger is unchanged |
| `test_scope_create_refuses_a_wrong_declaration_hash` | a wrong frozen hash, a RUN hash that is not the file's, the frozen hash given as the RUN hash, and an authorization naming the frozen hash are each refused |
| `test_scope_create_refuses_a_tampered_run_file_a_wrong_token_and_no_run_file` | a RUN file with any other edit, a wrong or missing token, and a missing RUN file are refused |
| `test_scope_create_refuses_when_the_run_folder_exists` | the scope is never created once the run exists |
| `test_scope_create_on_a_throwaway_ledger_creates_exactly_the_declared_scope` | on a throwaway SQLite file in pytest's temporary folder (never the AI ledger, asserted): exactly the declared limits, a null breaker, 0 entries, one more scope, `verify_ledger_scope` accepts it, and a second creation is refused |

The RUN copy, the digest and the authorization used by these tests exist in memory only, with a test token that is not the owner's. No RUN file and no authorization file was written anywhere.
