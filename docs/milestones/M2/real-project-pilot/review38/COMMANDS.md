# Commands (review38, ORCH-08)

Python: `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe` with `PYTHONDONTWRITEBYTECODE=1` and `PYTEST_ADDOPTS="-p no:cacheprovider"`; never `-O`. `GIT_OPTIONAL_LOCKS=0` for every git read. Paths: `PILOT` = `C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot`, `WORK` = `C:/t/iso/work/r2x/r38`. None of these commands makes a model or provider request; none creates a ledger scope, token, authorization file or run file. The live commands of the runner are documented in `LIVE-RUN-CONTRACT.md` and need a declaration (ORCH-09) and the owner's authorization; they are not run here.

## Reproduce

```text
# 0. read-only snapshot of the frozen trees (also run at the end as SNAPSHOT-AFTER)
python -B WORK/scripts/snapshot_r38.py WORK/evidence/SNAPSHOT-BEFORE.json

# 1. the whole test suite from the harness itself (no twin: the sandbox base defaults to C:/t/r2x/r38-sandbox)
python -B WORK/scripts/run_tests_r38.py <new junit dir> <new basetemp dir> [<harness dir, default WORK/harness-r32>]

# 2. the per-project request bounds of the frozen run set (window 60 per 86,400 s, elapsed bound 604,800 s)
cd WORK/harness-r32
python -B project_bounds_r32.py PILOT/review34/RUN-SET-PROPOSAL.json <out>/PROJECT-REQUEST-BOUNDS.json 60 86400 604800

# 3. the cross-page what-if (copies of the evaluator-offline-r32 parity scripts; one process per side)
python -B WORK/scripts/make_parity_copy_r38.py <record json>
cd WORK/parity/r36-side && python -B ../../scripts/cross_page_whatif_r38.py pass r36 WORK/parity/r36-side/run/PASS-R36.json
cd WORK/parity/r38-side && python -B ../../scripts/cross_page_whatif_r38.py pass r38 WORK/parity/r38-side/run/PASS-R38.json
cd WORK/parity/r38-side && python -B ../../scripts/cross_page_whatif_r38.py pass r38 WORK/parity/r38-side/run/PASS-R38-NOSOURCE.json nosource
python -B WORK/scripts/cross_page_whatif_r38.py compare <PASS-R36> <PASS-R38> <PASS-R38-NOSOURCE> <out>/CROSS-PAGE-WHATIF.json

# 4. the visibility dry exercise (refusing stub; real labels read by the adapter only; SYNTHETIC EP-990001 for the application path)
python -B WORK/scripts/visibility_exercise_r38.py <new work dir> <out>/VISIBILITY-RESULT.json <out>/VISIBILITY-REPORT.md

# 5. the diff, the binding manifest, the package, its check, the manifest (last)
python -B WORK/scripts/make_diffs_r38.py WORK/evidence/HARNESS-DIFF-R36-R38.patch WORK/evidence/HARNESS-FILES-R36-R38.json
python -B WORK/scripts/assemble_review38.py
python -B WORK/scripts/make_binding_r38.py PILOT/review38/BINDING-MANIFEST-R38.json
python -B WORK/scripts/verify_review38_package.py PILOT/review38/evidence/PACKAGE-CHECK.json
python -B WORK/scripts/write_manifest_r38.py

# 6. the audit view of any run's allowance (read-only on both databases)
python -B WORK/harness-r32/allowance_r32.py audit <run folder>/allowance.sqlite <out json> [<ledger path> <scope>]
```

## Dry runs of the runner (examples; dry mode only)

```text
cd WORK/harness-r32
python -B runner_r32.py run    --mode dry --stamp <S> --run-set <RS> --binding <BM> --binding-sha <SHA> [--dry-inject <INJECT.json>] [--dry-synthetic <SPEC.json>]
python -B runner_r32.py resume --mode dry --stamp <S> --run-set <RS> --binding <BM> --binding-sha <SHA> [the same --dry-inject / --dry-synthetic]
```
