# Commands (declaration-r32-v2, ORCH-09)

**Environment.**
- Python: `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe` (3.12.10) with `-B`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`; `GIT_OPTIONAL_LOCKS=0` for every git read; never `-O`. `R34_OWNER_DISPATCH_TOKEN` was never set.
- `PKG` = `C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v2`; `WORK` = `C:/t/iso/work/r2x/r40`; the dry sandbox base `C:/t/r2x/r40-sandbox` (dry stamps begin `r40d`, never the live stamp `r32-v2`).
- The bound harness `PILOT/review39/scripts/harness-r32` is only imported or run, never changed (each import is preceded by a check of its 56 files against `BINDING-MANIFEST-R39`).
- **The decision coverage gate is C ≥ B only, a change from plan v2** (A-10); C ≥ R is a mandatory diagnostic.

**What these commands never do:** a provider or model request; a `claude` invocation of any kind; a ledger scope, token, authorization file or RUN file; a write to a frozen package, the staging, the candidate, the baseline, application code or a database (the AI ledger is opened `mode=ro` only).

## Reproduce (in this order)

```text
# 0. read-only snapshot of every frozen tree (SNAPSHOT-BEFORE at the start, SNAPSHOT-AFTER at the end) and the frozen-input recompute
python -B PKG/scripts/snapshot_r40.py WORK/SNAPSHOT-BEFORE.json
python -B PKG/scripts/check_frozen_inputs_r40.py WORK/FROZEN-INPUTS-START.json          # PACKET MATCH or PACKET MISMATCH (exit 3)

# 1. the Windows path-length probe (files only under C:/t/r2x/r40-sandbox/pathlen-probe)
python -B PKG/scripts/pathlen_probe_r40.py WORK/PATHLEN-PROBE.json

# 2. the declaration (show: print only; write: once), then the diff
cd PKG/scripts
python -B build_declaration_r40.py show
python -B build_declaration_r40.py write                 # FRESH-VALIDATION-DECLARATION-R32-V2.json + DECLARATION.sha256
python -B diff_declaration_r40.py                        # DECLARATION-DIFF.json + DECLARATION-DIFF.md

# 3. the dry preflight (contract 4, 48 probes, binding, bounds, lanes' environment, runner and guard refusals, the scope command)
python -B preflight_r40.py                               # dry-run/PREFLIGHT-RESULTS.json, dry-run/lane-env/, scope/

# 4. the dry exercise, in phases (refuses below its free-space guard; outputs staged in WORK/dry/out-<tag>/ until 'finish')
python -B dry_exercise_r40.py new-tag                    # prints a tag (this package: 52050f)
python -B dry_exercise_r40.py loops <tag>                # the EP-27331 deferral loops under 'full' + the CLI-version dead-end drill
python -B dry_exercise_r40.py main-split <tag>           # all 24 documents as six per-project dry runs (or 'main <tag>': one run, needs 250 MB free)
python -B dry_exercise_r40.py finish <tag>               # dry-run/DRY-EXERCISE.json and the copies, only if both phases succeeded

# 5. the tests (junit)
python -B run_tests_r40.py C:/t/r2x/r40-sandbox/pytest-<new>     # tests/test_r40.xml, tests/SUMMARY.json, tests/guard/

# 6. the end snapshot, the package check, the manifest (last), the response-ledger append
python -B snapshot_r40.py PKG/evidence/SNAPSHOT-AFTER.json
python -B package_r40.py check                           # evidence/PACKAGE-CHECK.json (runs check_frozen_inputs_r40 -> evidence/FROZEN-INPUTS-END.json)
python -B package_r40.py manifest                        # evidence/EVIDENCE-MANIFEST.json
python -B append_response_r40.py                         # one entry appended to docs/milestones/M2/M2-REVIEW-RESPONSE.md
```

## Read-only helpers

```text
python -B PKG/scripts/create_scope_r40.py preview        # what the scope command would create; creates nothing
python -B PKG/scripts/create_scope_r40.py status         # the declared scope's state
python -B PKG/scripts/build_declaration_r40.py verify_run_file --digest <hex> --run-sha <hex>   # V's re-verification of the owner's RUN file
```

## Owner-only commands (never run by this task)

`build_declaration_r40.py fill_owner_digest`, `build_declaration_r40.py write_authorization`, `create_scope_r40.py create`, `runner_r32.py run|resume --mode live`, and the model-identity probe: see `RUNBOOK.md`.
