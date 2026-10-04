# Round 2 exploration: regression evidence and manifests (deliverable 6)

## 1. What changed in the candidate

**Nothing.** No application, parser, evaluator or test file was changed in this round.

- The candidate stays `3d5607d` (`C:/t/iso/frozen-r12`). `git status --porcelain` was empty when the experiment was declared, and again after the regression run.
- There is therefore **no new freeze and no candidate diff.** Regression tests for a change are not applicable.
- What was added in this round are **experiment scripts outside the candidate**:
  - selection, staging, rendering, labelling, runners, scorer and worklist tools;
  - under `C:/t/iso/work/r2x/`, copied to `evidence/scripts/`.
  - Their hashes are in `evidence/EVIDENCE-MANIFEST.json`, and the runner hashes are also in `evidence/run/RUNNERS-SHA256.txt`.

## 2. A focused run on the frozen candidate (new, this round)

**The run.**
- **Command:** `TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp python -B -m pytest <12 modules> -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/r2x-reg --junitxml=…`, run in `C:/t/iso/frozen-r12/backend` (no `.env`). pytest's own exit code was written by `echo $?` immediately afterwards.
- **Modules:** the reviewer's 188-test set (`test_m2_review11`, `test_m2_review10`, `test_m2_review09`, `test_m2_review08`, `test_m2_eval5`, `test_evidence_reader_r7`, `test_evidence_reader`, `test_ai_ledger`, `test_m2_review07_extraction`, `test_m2_review07_boq`, `test_sync_worker`) plus `test_m2_review12`.
- **Result:** **199 passed, 0 failed, 0 errors, 0 skipped; pytest exit code 0** (127.8 s).
- **Concurrency:** it ran **while profile B's real-model run was in progress** (a separate process and sandbox). `test_sync_worker` passed under that load. As in Review 12, this pass does not establish the cause of Review 11's timeout.
- **Evidence:** `evidence/regression/r2x__reviewer188_plus_r12_on_3d5607d.xml`, `reviewer188_plus_r12.log` and `pytest_exit_code.txt`.

**The full suite was not run again.** Its status on `3d5607d` is Review 12's run: 1,694 tests, 1,657 passed, 2 pre-existing failures, 35 skipped, exit code 1. See [BASELINE-AND-MANIFEST.md](BASELINE-AND-MANIFEST.md) §1.

## 3. Checks built into the experiment scripts (each run refuses to start otherwise)

| Check | Where |
|---|---|
| The selection, staging manifest, small batch, stage and label hashes equal the frozen values | every script (`assert sha256 == …`) |
| The declaration hash equals the frozen value | every runner and the scorer |
| The stage projects are within the declaration, and no project is sealed | `declare_small.py`, `r2x_ev0.py` |
| The application limits equal the frozen candidate's defaults (not overridden) | `r2x_ev0.py`, `r2x_ev.py`, `r2x_boq.py` |
| The reader, policy, schema, prompt and audit identities equal the declaration's | `r2x_ev.py`, `r2x_boq.py` |
| A sandbox is never re-run in place; a failed or stopped run is preserved and a new tag is used | every runner |
| Profile B / C starts only from this declaration's profile-A run | `r2x_ev.py` |
| The evaluator scores AI evidence only under the run's declared context; the wrong-variant and no-context controls score none | `score_small.py` (`SMALL-METRICS.json`, `controls`) |

## 4. Manifests

`evidence/EVIDENCE-MANIFEST.json` lists every file of this package with its sha256.

**Earlier packages are unchanged.** `review05`–`review12` and `human-review-packet-v2` are referenced by hash, never rewritten.
