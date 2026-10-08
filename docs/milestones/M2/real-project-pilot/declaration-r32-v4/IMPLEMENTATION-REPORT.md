# Task R43-40 implementation report: declaration v4 on the review43 harness and the R43 trees (frozen, NOT authorized)

Agent: ep-implementer, Claude Opus 5.5 (self-reported), effort high; 2026-10-08 00:03 to about 01:10 +04. Authority A-13 item 2. Log rows R43-53 to R43-56 in `docs/R43-SESSION-LOG.md`. Package untracked (no commit). **This package binds code and inputs; it authorizes nothing: no run, budget, scope, token, nonce, RUN file, authorization file or dispatch. M4 (historical M2): CHANGES STILL REQUIRED. M3: accepted.**

## Hashes

| file | sha256 |
|---|---|
| `FRESH-VALIDATION-DECLARATION-R32-V4.json` (contract `r42-live-contract-5`, 205,936 B) | `e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9` |
| `BINDING-MANIFEST-R32-V4.json` (25 fields, R42/R43 form; written last before this report) | `4c7285eeea712dde9350dc5e7b1f3068eafea6becad10636bb58ff69665720ab` |
| `SELF-CHECK-1.json` | 334 checks, 0 failures, 303 bound entries |
| bound harness manifest | `f35355aa8a8bca16803db3576fda8260a470915fee9c905b035f8d8bd9a374a7` (479 entries re-hash equal) |
| supersedes v3 | `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40` (executed, terminal); v3 manifest `a2df60dc...1a24` |
| R43 log prefix bound | lines 1-63 |

Other bound files and hashes: `DECLARATION-DIFF.json/.md`, `V4-BUILD-DIFF.md`, `dry-run/PREFLIGHT-RESULTS.json` (`34b02823...d475`), `dry-run/DRY-EXERCISE.json` (`8ccb6e44...fd9f`), `rehearsal/demos/DEMOS-R42.json`, `rehearsal/REAL-BASELINE-FACTS-FINDING.md`, `evidence/*`: see the manifest.

## What v4 changes against v3 (DECLARATION-DIFF)

Top-level keys: 58 unchanged, 7 repointed/rebound only, 22 changed, 8 added, 0 removed. Leaves: 1,155 unchanged, 57 repointed, 13 rebound, 56 changed, 124 added, 1 removed. **Protected values (arms, switches, task kinds, run set, truth, reference set, parent 556, lane allowances, window, thresholds, limits, gate, resume policy, stop rules, concentration, pins): all unchanged or re-pointed/rebound only.** Changed or added items: the harness manifest and isolation folder (`review43/scripts/harness-r32`); trees, lanes and evaluator re-pointed to frozen-r13 `7ec3d2cf` / cand-r30n `436daef2` (checked as text, R43V-13); the stamp `r32-v4`, the folder `C:/t/r2x/r42-sandbox/r32-v4`, the scope `m2-fresh-validation-r32-v4-2026-10-08`, and the pinned RUN and authorization paths in this package (none created); `ledger_baseline` 484/18/0; `test_exceptions`; `trees_r43`; `preconditions` (pip freeze R42-09); `owner_conditional_decision` (A-13 item 3 verbatim, a precondition, not an authorization); `verification43_items`; `v4_preparation_items`; ten disclosures. There are 0 old identifiers outside the record keys.

## Verification 43 readiness items (check 8)

1. The isolation harness is the review43 folder. 2. The binding is `f35355aa...`, the trees are R43, and V4-05 is corrected in `R32-V4-PREPARATION-LIST-CORRECTED.md`. 3. New stamp, folder, scope and paths. 4. The ledger pin is re-pinned to 484/18/0 in the v4 script copies (24 lines listed in V4-BUILD-DIFF section 3); the run-folder and authorization-file invariants are before/after comparisons. 5. The test exception is declared and evidenced (`evidence/AUTHORIZATION-FILE-TEST-EXCEPTION.json`: the only hit is the v3 file `f2546c91...425f`, commit 7a1bf6f). 6. **Stopped**: see the finding below. 7. The preflight driver imports only bound package scripts and the checked harness copy. 8. The guard `scripts/guard/sitecustomize.py` denies live run folders `r32-v<N>` and the owner records (it refuses reads of the owner records too), and passed 19/19 probes. 9. V4-01..V4-04 and R42-09 are carried.

## Rehearsal (0 requests)

- Preflight: 73/73 probes; steps 1-12 as expected; lanes B (frozen-r13) and C/R/P (cand-r30n) passed offline with the drawings AI off.
- Dry exercise: single 24-document run FINISHED, six per-project runs, deferral loops of 2 and 3 invocations, the cross-project drill, and the CLI case.
- Demonstrations 8/8 (the 7 of the card plus the global provider). Refusal before dispatch now also covers an authorization that names the executed v3 RUN hash.
- **Finding R43-40-F1:** F009, F020 and F030 got `exercise_no_facts`, with 0 facts.
  - The bound harness gives dry runs the application reader only for synthetic SYN* documents (`runner_r32.py:772`, `:865`) and asserts it (`lane_r32.py:84-86`). With reader `none`, lane B passes `extracted: None` to the tripwire (`:470-472`).
  - This is a design rule since review34 (R34-18).
  - I did not change the harness and ran no workaround. Condition (b) of A-13 item 3 is therefore not demonstrated.
  - Options for Verification 44 and the owner are listed in the finding.

## Protected state

- AI ledger: 484/18/0 before and after (mode=ro).
- Unchanged before and after:
  - pip freeze `bd424a5c...bf7f`;
  - the v3 run folder (54 files);
  - the owner records, hashed as a whole;
  - review42 and review43;
  - declarations v1 to v3;
  - the R43 review package;
  - the five trees.
- Nothing was created for v4: no v4 scope, run folder, RUN file or authorization file.
- Everything I created outside the package is under `C:/t/r2x/r42-sandbox/r43p/`.

## Not done

- No v4 RUNBOOK or budget card (not in the card; the declaration points to a later task).
- No full harness test run (it would create about 455 MB of sibling folders outside r43p; the test exception is evidenced by name search instead).
- The real-facts rehearsal (stopped, above).
