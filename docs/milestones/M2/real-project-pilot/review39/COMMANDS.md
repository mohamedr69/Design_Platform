# Commands (review39, ORCH-08C)

**Environment.**
- Python: `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe`, with `PYTHONDONTWRITEBYTECODE=1` and `PYTEST_ADDOPTS="-p no:cacheprovider"`. Never use `-O`.
- Set `GIT_OPTIONAL_LOCKS=0` for every git read.
- Paths:
  - `PILOT` = `C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot`
  - `WORK` = `C:/t/iso/work/r2x/r39`
  - the sandbox base is `C:/t/r2x/r39-sandbox`.

**What these commands never do.**
- None of them makes a model or provider request.
- None of them runs `claude` in any form.
- None of them creates a ledger scope, token, authorization file or run file.

The runner's live commands are documented in `LIVE-RUN-CONTRACT.md`. They need a declaration (ORCH-09) and the owner's authorization, and they are not run here. The owner's model-identity probe is documented in `MODEL-ID-EVIDENCE.md` §4; the owner runs it, not this task.

## Reproduce

```text
# 0. read-only snapshot of the frozen trees (also run at the end as SNAPSHOT-AFTER)
python -B WORK/scripts/snapshot_r39.py WORK/evidence/SNAPSHOT-BEFORE.json

# 1. the static request paths (REQUEST-PATHS-STATIC.json; reads source files only)
cd WORK/harness-r32 && python -B request_paths_r39.py <out>/REQUEST-PATHS-STATIC.json

# 2. the whole test suite from the harness itself (22 modules incl. test_request_paths_r39, test_unread_pages_r39)
python -B WORK/scripts/run_tests_r39.py <new junit dir> <new basetemp dir> [<harness dir, default WORK/harness-r32>]

# 3. the per-project request bounds (window 60 per 86,400 s, elapsed bound 604,800 s) and the resume-policy model
cd WORK/harness-r32
python -B project_bounds_r32.py PILOT/review34/RUN-SET-PROPOSAL.json <out>/PROJECT-REQUEST-BOUNDS.json 60 86400 604800
python -B resume_invocations_r39.py <out>/PROJECT-REQUEST-BOUNDS.json <out>/RESUME-INVOCATIONS-R39.json

# 4. the dynamic probes (drawings-AI switch and 1(d) in both trees; Verification 39's unread-page scenarios A, B, C)
python -B WORK/scripts/probe_evidence_r39.py <out>/DRAWINGS-AI-PROBE-R39.json <out>/UNREAD-PAGES-PROBE-R39.json

# 5. the model-identity evidence (read-only byte search of the installed CLI file; the CLI is NOT executed)
python -B WORK/scripts/model_id_evidence_r39.py <out>/MODEL-ID-EVIDENCE.json

# 6. the visibility dry exercise (17 scenarios; refusing stub; SYNTHETIC EP-990001 for the application paths)
python -B WORK/scripts/visibility_exercise_r39.py <new work dir> <out>/VISIBILITY-RESULT.json <out>/VISIBILITY-REPORT.md

# 7. the diff, the package, the binding manifest, its check, the manifest (last), the response entry
python -B WORK/scripts/make_diffs_r39.py WORK/evidence/HARNESS-DIFF-R38-R39.patch WORK/evidence/HARNESS-FILES-R38-R39.json
python -B WORK/scripts/assemble_review39.py
python -B WORK/scripts/make_binding_r39.py PILOT/review39/BINDING-MANIFEST-R39.json
python -B WORK/scripts/verify_review39_package.py PILOT/review39/evidence/PACKAGE-CHECK.json
python -B WORK/scripts/write_manifest_r39.py
python -B WORK/scripts/append_response_r39.py

# 8. the audit view of any run's allowance (read-only on both databases)
python -B WORK/harness-r32/allowance_r32.py audit <run folder>/allowance.sqlite <out json> [<ledger path> <scope>]
```

## Dry runs of the runner (examples; dry mode only)

```text
cd WORK/harness-r32
python -B runner_r32.py run    --mode dry --stamp <S> --run-set <RS> --binding <BM> --binding-sha <SHA> [--dry-inject <INJECT.json>] [--dry-synthetic <SPEC.json>]
python -B runner_r32.py resume --mode dry --stamp <S> --run-set <RS> --binding <BM> --binding-sha <SHA> [the same --dry-inject / --dry-synthetic]
```

An `INJECT.json` may set `"resume_policy": "full" | "earliest"` (default `full`) and the drill injections listed in `LIVE-RUN-CONTRACT.md` §1. The patch scripts in `scripts/patch_*.py` are the one-off edits that produced the development copy of the harness from review38's. They are kept as a record; they are not part of reproducing it.
