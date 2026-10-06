# Commands (review42, ORCH-10): reproducible from a clean cmd.exe shell

**Environment (cmd.exe; every path quoted):**

```bat
set PY="G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set GIT_OPTIONAL_LOCKS=0
set PYTHONPATH=C:\t\iso\work\r2x\r42\guard
set R42=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\review42
set B=%R42%\scripts\build
```

- `PYTHONPATH` loads the R42 audit guard (`scripts/build/guard/sitecustomize.py`, a byte copy of `C:\t\iso\work\r2x\r42\guard\sitecustomize.py`) in every Python process and every child: any `claude` process, any network use, any write or read-write SQLite outside `C:\t\iso\work\r2x\r42`, `C:\t\r2x\r42-sandbox`, the two new packages and the session scratchpad is refused and logged. Never `-O`. `R34_OWNER_DISPATCH_TOKEN` is never set.
- The build scripts are in `scripts/build/` (byte copies of `C:\t\iso\work\r2x\r42\scripts\`); their outputs are written once (each refuses an existing output).

**What these commands never do:** a provider or model request; a `claude` invocation of any kind (the CLI file is read as bytes only); a ledger scope, token, authorization file or RUN file; a write to a frozen package, the staging, the candidate, the baseline, application code, the merged installation's code / data / `.env`, or a database (the AI ledger is opened `mode=ro` only).

## Reproduce (in this order)

```bat
rem 0. the standing facts and the before-snapshot (read-only)
%PY% -B "%B%\facts_r42.py" C:\t\iso\work\r2x\r42\out\FACTS-START.json
%PY% -B "%B%\snapshot_r42.py" C:\t\iso\work\r2x\r42\out\SNAPSHOT-BEFORE.json

rem 1. the harness: a byte copy of the corrected work copy (C:\t\iso\work\r2x\r42\harness-r32)
rem    (the corrections themselves: CHANGE-RECORD-R42.md; scripts\build\patch_runner_main_r42.py is the runner patch)

rem 2. the outputs, with the PACKAGE harness
%PY% -B "%B%\make_outputs_r42.py" "%R42%\evidence\OUTPUTS-R42.json"
%PY% -B "%B%\make_contract_v5_r42.py" "%R42%\LIVE-RUN-CONTRACT.md"

rem 3. the binding manifest (written once; --check-only re-hashes without writing)
%PY% -B "%B%\make_binding_r42.py" --check-only
%PY% -B "%B%\make_binding_r42.py"

rem 4. the whole test suite from the package harness (junit into tests\; about 17 minutes)
%PY% -B "%B%\run_tests_r42.py" "%R42%\tests" C:\t\r2x\r42-sandbox\pytest-<new> "%R42%\scripts\harness-r32"

rem 5. the scripted-provider demonstrations (evidence\demos\; about 11 minutes)
%PY% -B "%R42%\evidence\demos\demos_r42.py" "%R42%\scripts\harness-r32" "%R42%\evidence\demos\out-<new>"

rem 6. the change record, the after-snapshot, the package check and the manifest (LAST)
%PY% -B "%B%\make_review42_docs.py"
%PY% -B "%B%\snapshot_r42.py" "%R42%\evidence\SNAPSHOT-AFTER.json"
%PY% -B "%B%\package_r42.py" check review42
%PY% -B "%B%\package_r42.py" manifest review42
```

## Read-only checks anyone can run

```bat
rem every bound file against BINDING-MANIFEST-R42 (the runner does this before anything)
cd /d "%R42%\scripts\harness-r32"
%PY% -B -c "import preflight_r32 as PF, hashlib; p=r'%R42%\BINDING-MANIFEST-R42.json'; print(PF.verify_binding(p, hashlib.sha256(open(p,'rb').read()).hexdigest()))"
rem the static request paths and the global-provider resolution
%PY% -B request_paths_r42.py C:\t\r2x\r42-sandbox\REQUEST-PATHS-STATIC-check.json
```

The runner itself (`runner_r32.py run|resume --mode live …`) is owner-only and is described in `PILOT/declaration-r32-v3/RUNBOOK.md`.
