# Commands (declaration-r32-v3, ORCH-10): reproducible from a clean cmd.exe shell

```bat
set PY="G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set GIT_OPTIONAL_LOCKS=0
set PYTHONPATH=C:\t\iso\work\r2x\r42\guard
set PKG=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3
cd /d "%PKG%\scripts"
```

`PYTHONPATH` loads the R42 audit guard (a byte copy is in `scripts\guard\sitecustomize.py`) in every process and child. Never `-O`; `R34_OWNER_DISPATCH_TOKEN` is never set by these commands. The review42 package must be complete first (`PILOT\review42\COMMANDS.md`).

**What these commands never do:** a provider or model request; a `claude` invocation of any kind; a ledger scope, token, authorization file or RUN file; a write outside `C:\t\iso\work\r2x\r42`, `C:\t\r2x\r42-sandbox` and the two new packages (the response ledger's one append excepted).

```bat
rem 0. evidence: the interpreter against the trees, the path lengths
%PY% -B interpreter_check_r42.py "%PKG%\evidence\INTERPRETER-CHECK.json"
%PY% -B pathlen_probe_r42.py "%PKG%\evidence\PATHLEN-PROBE.json" <a finished dry run folder>

rem 1. the declaration (show: print only; write: once), then the diff
%PY% -B build_declaration_r42.py show
%PY% -B build_declaration_r42.py write
%PY% -B diff_declaration_r42.py

rem 2. the dry preflight
%PY% -B preflight_r42.py

rem 3. the dry exercise, in phases (finish copies into dry-run\ only when every phase succeeded)
%PY% -B dry_exercise_r42.py new-tag
%PY% -B dry_exercise_r42.py single <tag>
%PY% -B dry_exercise_r42.py split <tag>
%PY% -B dry_exercise_r42.py loops <tag>
%PY% -B dry_exercise_r42.py xproject <tag>
%PY% -B dry_exercise_r42.py cli <tag>
%PY% -B dry_exercise_r42.py finish <tag>

rem 4. the package tests (junit)
%PY% -B run_tests_r42pkg.py C:\t\r2x\r42-sandbox\pytest-<new>

rem 5. the documents, the after-snapshot, the package check, the manifest (LAST), the one response append
%PY% -B make_v3_docs_r42.py
%PY% -B snapshot_r42.py "%PKG%\evidence\SNAPSHOT-AFTER.json"
%PY% -B package_r42.py check v3
%PY% -B package_r42.py manifest v3
%PY% -B append_response_r42.py
```

Read-only helpers: `create_scope_r42.py preview | status`; `build_declaration_r42.py verify_run_file --digest <hex> --run-sha <hex>`.
Owner-only (never run by this task): `build_declaration_r42.py fill_owner_digest | write_authorization`, `create_scope_r42.py create`, `runner_r32.py run|resume --mode live` (RUNBOOK.md).
