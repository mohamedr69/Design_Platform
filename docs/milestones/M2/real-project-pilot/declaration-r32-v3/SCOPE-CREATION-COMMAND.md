# Scope-creation command: `create_scope_r42.py` (declaration v3)

- **Script:** `PILOT/declaration-r32-v3/scripts/create_scope_r42.py`. Reviewed with the declaration. **Not executed by this task** (only `preview` and the refusals; a positive creation only on a throwaway SQLite file in a test).
- **Creates:** once, the scope **`m2-fresh-validation-r32-v3-2026-10-06`** in `C:/t/r2x/ledger/r2x-ledger.sqlite` with exactly `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` (= the parent budget plus the per-request estimates), a closed breaker and no entries, through the candidate application's own `app.ai.ledger.Ledger` (`ledger.py` `d9f92297…`).
- **When:** by the owner, after the budget authorization, immediately before invocation 1, with the token in `R34_OWNER_DISPATCH_TOKEN`.

```cmd
cd /d "G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\scripts"
"G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe" -B create_scope_r42.py preview
"G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe" -B create_scope_r42.py create --frozen-sha 9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40 --run-sha <RUN hash>
"G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe" -B create_scope_r42.py status
```

**`create` refuses, creating nothing, unless, in order:** (1) the authorization file exists at `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\OWNER-DISPATCH-AUTHORIZATION.json`; (2) `--frozen-sha` equals the file and `DECLARATION.sha256`; (3) the RUN file hashes to `--run-sha` (never a frozen hash, neither v3's nor v2's) and equals the frozen bytes with only the digest replaced; (4) the authorization (either form) names the RUN hash, the digest, the owner and its nonce(s), and the token matches (nothing is consumed); (5) the run folder `C:/t/r2x/r42-sandbox/r32-v3` does not exist; (6) `BINDING-MANIFEST-R42` verifies and the RUN declaration passes contract 5; (7) **ORCH-10:** the bound interpreter runs the command, the pinned CLI file hashes to `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03` (read as bytes), and drive C has at least 2 GiB free (condition C1); (8) `ledger.py` is the bound one; (9) no scope of that name exists.

**Dry evidence:** `scope/SCOPE-PREVIEW-OUTPUT.json` (nothing created; ledger unchanged) and `scope/SCOPE-CREATE-REFUSED-OUTPUT.json` (refused: no authorization file). Tests: `tests/test_r42.xml` (every refusal above, including the disk floor, and one positive creation on a throwaway file).
