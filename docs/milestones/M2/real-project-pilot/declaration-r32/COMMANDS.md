# Commands (declaration-r32, ORCH-07)

## Environment

- **Python:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe`, always with `-B`.
- **Variables:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`, `PYTEST_ADDOPTS="-p no:cacheprovider"`, `GIT_OPTIONAL_LOCKS=0`.
- **Work folder:** `C:/t/iso/work/r2x/r37/`. Every command runs there. `scripts/` in this package holds byte-identical copies, which the package check verifies.
- **Harness:**
  - The live and preflight steps use the bound copy `C:/t/iso/work/r2x/r36/harness-r32/` (`BINDING-MANIFEST-R36.json`, `harness_r36`).
  - The pure analyses import the byte-identical package copy `PILOT/review36/scripts/harness-r32/` (`harness_r36_package`).
  - Every imported module is hash-checked first.
- **No model request.** None of these commands sends one. No authorization file is written, no token is generated and no ledger scope is created.
- **Writes** go only to:
  - the work folder;
  - this package;
  - the scratchpad `…/scratchpad/r37decl/`;
  - `C:/t/r2x/r37-sandbox/` (the dry exercise);
  - the single response-ledger append.
- **Never reused:** every output is written once (`O_EXCL`). A script refuses an existing target.

## Steps

| # | Command | Output |
|---|---|---|
| 1 | `python -B snapshot_r37.py C:/t/iso/work/r2x/r37/evidence-work/SNAPSHOT-BEFORE.json before` | The task-start snapshot: 18 frozen trees (sha256, size, mtime per file), 6 single files, git state, AI ledger (read-only), response ledger hash, live-sandbox listing, authorization search. Copied byte for byte to `evidence/SNAPSHOT-BEFORE.json`. |
| 2 | `python -B estimates_r37.py` | Prints the request and token estimates. The declaration embeds them. |
| 3 | `python -B build_declaration_r37.py show` | Prints the declaration it would write. Writes nothing. |
| 4 | `python -B build_declaration_r37.py write` | `FRESH-VALIDATION-DECLARATION-R32.json` and `DECLARATION.sha256`, **written once**. The script refuses if either exists, on any hash difference (PACKET MISMATCH), if the ledger is not 483/17/0, if the scope name exists, or if the run folder exists. |
| 5 | `python -B preflight_r37.py <package>/dry-run/PREFLIGHT-RESULTS.json` | Runs `validate_declaration` as written and on an in-memory dummy-digest copy, `load_declaration`, `verify_binding`, and the live runner without authorization or token (subprocess from the bound copy, then in-process with the in-memory copy). Also runs the guard checks and the ledger, folder and authorization invariants. |
| 6 | `python -B dry_exercise_r37.py orch07-dry-20261003a` | The test twin `harness-r32-dry-twin/` (`dry-run/TWIN-RECORD.json`), then the dry run with the declaration's switches in `C:/t/r2x/r37-sandbox/orch07-dry-20261003a`. Writes `dry-run/DRY-EXERCISE.json` and `dry-run/exercise/`. |
| 7 | `python -B concentration_on_proposal_r37.py <package>/concentration/CONCENTRATION-ON-PROPOSAL.json` | Rule v2 on the run-set structure, exact combinatorics plus the frozen code on synthetic lanes. About 30 s. |
| 8 | `python -B run_tests_r37.py <new scratch basetemp>` | `tests/test_r37.xml` (junit) |
| 9 | `python -B package_r37.py copy-scripts` | `scripts/` |
| 10 | `python -B snapshot_r37.py <package>/evidence/SNAPSHOT-AFTER.json after` | The end-of-task snapshot |
| 11 | `python -B package_r37.py check` | `evidence/PACKAGE-CHECK.json`. It re-runs the tests into the scratchpad. |
| 12 | `python -B package_r37.py manifest` | `evidence/EVIDENCE-MANIFEST.json`, **written last** |
| 13 | `python -B append_response_r37.py` | One entry at the end of `docs/milestones/M2/M2-REVIEW-RESPONSE.md`. The script refuses unless the file still hashes to `b055b6a6…72e8`. |

## How the owner derives the runnable declaration (not run by this task)

Run this from `scripts/` (or the work folder). It writes bytes directly, so no line-end conversion happens:

```text
python -B -c "import pathlib, build_declaration_r37 as BD; d = pathlib.Path(r'<package>'); (d / 'FRESH-VALIDATION-DECLARATION-R32.RUN.json').write_bytes(BD.fill_owner_digest((d / 'FRESH-VALIDATION-DECLARATION-R32.json').read_bytes(), '<64-hex sha256 of the owner token>'))"
```

- The runnable file must sit in the same folder as the frozen declaration, because the pinned authorization path is the declaration's own folder.

- The function replaces only the placeholder value of `authorization.owner_token_sha256`.
- It refuses a digest that is not 64 lower-case hex characters.
- It asserts that nothing else changed.
- The new file's sha256 is the run hash named in `OWNER-DISPATCH-AUTHORIZATION.json`.
- **This task ran the function only in memory, with a dummy digest, inside the tests.**

## Rules

- **AI ledger:** opened only as `file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro` with `uri=True`.
- **Production database:** `backend/ep_platform.db` is never opened.
- **Bytecode and git:** the candidate and baseline trees are read with bytecode writing off and `GIT_OPTIONAL_LOCKS=0`. The package check verifies that both stay clean at their HEADs.
- **Dry mode never reads a cohort document with an application reader.** Reader `none`, the refusing stub, and no CLI on the lane PATH.
