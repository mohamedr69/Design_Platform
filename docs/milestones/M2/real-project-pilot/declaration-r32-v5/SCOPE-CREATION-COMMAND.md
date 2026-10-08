# Scope-creation command: `create_scope_r42.py` (declaration v5; R44-07)

- **Who runs it: the owner alone.** No agent, orchestrator or verifier runs `create`. This document authorizes nothing and delegates nothing.
- **Script:** `PILOT/declaration-r32-v5/scripts/create_scope_r42.py` (the v4 script with only: the review45 harness manifest and group, the v5 pinned path in its text, and the v4 hash added to the refused hashes; `V5-BUILD-DIFF.md`). **Not executed by task R43-44** — not even `preview` (the card ran preflight steps 1–7 only; the scope command is step 12).
- **Declaration:** `PILOT/declaration-r32-v5/FRESH-VALIDATION-DECLARATION-R32-V5.json`, frozen sha256 **`db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`**.
- **Creates:** once, the scope **`m2-fresh-validation-r32-v5-2026-10-08`** in `C:/t/r2x/ledger/r2x-ledger.sqlite` with exactly `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` (the parent budget plus the per-request estimates, unchanged from v3 and v4), a closed breaker and no entries, through the candidate application's own `app.ai.ledger.Ledger` (`C:/t/iso/cand-r30n/backend/app/ai/ledger.py`, sha256 `d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca`).
- **When:** after Verification 46, the owner's option-1 register entry and the D1/D2 naming the v5 hash; after the RUN file (RUNBOOK-R32-V5 section 2.2), its independent check (2.3) and the authorization file (2.5); immediately before invocation 1 (the scope's 7-day `elapsed_s` counts from its creation); with the token in `R34_OWNER_DISPATCH_TOKEN`, the pip freeze equal to `bd424a5c4692ab4c1f634705e59ded3784549a6f6c9072ffea9860fbf611bf7f`, and `R43_HARNESS_RUN` unset.

## The exact commands (cmd.exe)

```cmd
cd /d "G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\scripts"
"G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe" -B create_scope_r42.py preview
"G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe" -B create_scope_r42.py create --frozen-sha db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df --run-sha <RUN hash>
"G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe" -B create_scope_r42.py status
```

`<RUN hash>` is the sha256 printed by `fill_owner_digest` and verified independently (`verify_run_file`), **never** the frozen hash.

**`preview`** is read-only (the AI ledger opened `mode=ro`): it prints the ledger, the scope name, the exact limits, the application call it would make and every precondition's current state. Expected now: ledger 484 / 18 / 0, no scope of that name, authorization file and RUN file "NOT YET".

**`create` refuses, creating nothing, unless, in order:**
1. the authorization file exists at the pinned path `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v5\OWNER-DISPATCH-AUTHORIZATION.json`;
2. `--frozen-sha` equals the frozen file's sha256 and `DECLARATION.sha256` (`db72025b…85df`);
3. the RUN file `FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json` hashes to `--run-sha`, which is not a frozen hash (v5, v4 `e0a93c46…`, v3 `9a55fa7b…`, v2 `f38fb281…`) nor the executed v3 RUN hash `c31cccd4…`, and equals the frozen bytes with only the digest filled in;
4. the authorization (either form) names the RUN hash, the same digest, `authorized_by` owner and its nonce(s), and the presented token's sha256 equals the digest (nothing is consumed here);
5. the run folder `C:/t/r2x/r42-sandbox/r32-v5` does not exist;
6. `BINDING-MANIFEST-R45-HARNESS.json` verifies against the declaration's `binding_manifest_sha256` `9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb` (every one of its 629 bound files), and the RUN declaration passes contract 5;
7. the bound interpreter runs the command, the pinned CLI file hashes to `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03` (read as bytes, never executed), and drive C holds at least 2 GiB;
8. `ledger.py` is the bound one (`d9f92297…`);
9. no scope of that name exists.

It then creates the scope and verifies it read-only: one more scope, the same entries and amendments, limits equal, breaker null, 0 entries, and `preflight_r32.verify_ledger_scope` passes.

**`status`** (read-only; after the creation and before every resume): expected after the creation `exists` true, `limits_equal_declared` true, `breaker` null, `scope_entries` 0, `ledger_totals` 484 / **19** / 0.

**Never:** a second scope, a scope for v4 (`m2-fresh-validation-r32-v4-2026-10-08`), reuse of the v3 scope, a `create` by anyone but the owner, or a `create` before the D1/D2 naming the v5 hash.
