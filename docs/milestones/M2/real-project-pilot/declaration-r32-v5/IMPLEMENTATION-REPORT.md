# Task R43-44 implementation report: declaration v5 = v4 rebound to the review45 harness (frozen, NOT authorized)

Agent: ep-implementer, Claude Opus 5.5 (self-reported), effort high; 2026-10-08 04:14 to about 05:00 +04 (system clock). Authority A-13 item 2 (offline declaration preparation); Verification 44 option 1; Verification 45 section 5 item 2. Log rows from R43-74 in `docs/R43-SESSION-LOG.md`. Package untracked (no commit). Written BEFORE `BINDING-MANIFEST-R32-V5.json` and bound by it (the v4 ordering gap is fixed); the manifest hash and its self-checks are therefore not in this file (see `SELF-CHECK-1.json` / `-2.json` and the R43 log).

**This package binds code and inputs; it authorizes nothing: no run, budget, scope, token, nonce, RUN file, authorization file or dispatch. Declaration v4 remains frozen, untouched and NOT authorized. M4 (historical M2): CHANGES STILL REQUIRED. M3: accepted.**

## Hashes

| file | sha256 |
|---|---|
| `FRESH-VALIDATION-DECLARATION-R32-V5.json` (contract `r42-live-contract-5`, 221,229 B, declared 2026-10-08T00:31:25Z) | `db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df` |
| `DECLARATION-DIFF-V4-V5.json` / `.md` | `b64e931a…8465` / `9e5ff0b6…13b6` |
| `V5-BUILD-DIFF.md` | `1afbb532…b12d` |
| `RUNBOOK-R32-V5.md` / `SCOPE-CREATION-COMMAND.md` / `SUMMARY-R32-V5.md` / `BUDGET-CARD-V6.md` | `3fd7c986…2c84` / `da6fe1e7…69ea` / `a01f6b0f…6651` / `00c5e3f6…7a10` |
| `dry-run/PREFLIGHT-RESULTS.json` (steps 1–7) | `7f006f43…da03` |
| `dry-run/DRY-EXERCISE.json` (single run) | `745ee2a6…e6f0` |
| `rehearsal/demos/DEMOS-R42.json` | `3f178b85…dee6` |
| `evidence/drill-v5/out/DRILL-REPORT.json` | `b590acfc…e964` |
| bound harness manifest | `9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb` (629 entries) |
| supersedes v4 | `e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9`; v4 manifest `4c7285ee…20ab` |

## What v5 changes against v4 (DECLARATION-DIFF-V4-V5: ok)

Top-level keys: 66 unchanged, 4 re-pointed/rebound only, 25 changed, 1 added (`owner_decision_required`), 0 removed. Leaves: 1,281 unchanged, 41 re-pointed (`review43/scripts/harness-r32` → `review45/scripts/harness-r32`), 2 rebound (`lane_r32`, `runner_r32`), 69 changed, 92 added, 12 removed (v4's own supersedes record moved under `supersedes.lineage`; `preconditions.no_v4_run_folder` → `no_v5_run_folder`). **Every protected value unchanged** (arms, switches, task kinds, run set, truth, reference set, trees, parent 556, allowances, window, thresholds, limits, gate, resume policy, stop rules, concentration, pins); 0 v4 identifiers outside the record keys; trees and new identifiers checked.

The changes are exactly the card's list: the harness rebind (`isolation`, `binding_manifest_sha256`, `harness.*` incl. 36 module hashes with the new `drill_r45`, `authorization.invocation` run / working directory / harness copy, `request_path_coverage` re-pointed to review45's junit plus a `drill_r45` entry); stamp `r32-v5`, folder `C:/t/r2x/r42-sandbox/r32-v5`, scope and `AI_LEDGER_SCOPE` `m2-fresh-validation-r32-v5-2026-10-08`, pinned authorization and RUN paths in this package (none created); `supersedes` v4 plus the chain; the disclosures; the carried R43V-05 test exception (`carried_to_v5`, R45-10); A-13 item 3 carried verbatim as history (`carried_as`, `status_at_v5_freeze`: lapsed, a fresh D1/D2 required); `owner_decision_required` with exactly the six check-8 steps of Verification 45. Record pointers also updated: reviews (Verifications 44, 45), ledger baseline re-read, two pointers to the corrected V4 preparation list now naming `PILOT/declaration-r32-v4`, the harness prohibition and two added forbidden items.

## Disclosure corrections

- **R45-06 / R45-07 / R34-18:** the first-read disclosure now states (1) F009, F020 and F030 were processed offline **5** times before this freeze (R43-42: evidence run and test module; Verification 45: reproduction and test module; R43-44: one reproduction on v5's bindings), the exposed agents named; and (2) v3's live B (frozen-r12) read 15 of 24 documents (14 of the other 21) with one model form reading (F035), so only F037, F033, F006, F015, F032, F016 and F018 were never read.
- Added: the harness rebind, the drill (mode, path, refusals), its criterion `8b183053…d918` and result (PASS, 0 criticals, 0 requests, reproduced), the **AI-on limit R45-08** (F009/F020 form reading not rehearsed), the drill limits (3 of 24, one project, AI off, not a result), the pre-run exposure (R44-12 extended), and A-13 item 3 lapsed. The dry-exercise, isolation, ledger-baseline and test-exception disclosures were restated for review45 and v5.

## Rehearsal (0 model requests; byte copies; v5 guard; 0 guard refusals outside the probes)

- `validate_declaration`: in-memory dummy-digest copy PASSED; the file as written REFUSED (in the build and in preflight steps 1–2).
- Preflight steps 1–7 (`--upto 7`): **73/73** probes; verify_binding 629 files; bounds; lanes B/C/R/P; interpreter, CLI file, disk. Steps 8–12 not run. Attempt 1 failed only at step 6 because the launcher set `R43_GUARD_ROOTS` (a path under the merged installation) and every lane's isolation check refused it; kept in `evidence/preflight-attempt-1/` (`3f369368…f8e5`); the variable was dropped.
- Dry exercise: the single 24-document run FINISHED; B's tripwire inputs/outputs and rows byte-equal to v4's.
- Demonstrations: 8/8.
- Drill on v5's bindings (`--binding BINDING-MANIFEST-R45-HARNESS` `9af8e07a…`): PASS; F009 19, F020 21, F030 18 facts; 0 criticals; 0 requests; facts, rows and tripwire payloads equal to the review45 evidence run after normalising times and paths.
- Guard probes 22/22.

## Protected state

AI ledger (mode=ro) 484 / 18 / 0 before and after, no v4 or v5 scope; pip freeze `bd424a5c…bf7f` before and after; r32-v3 54 files by stat only, unchanged; the owner records one whole-folder hash (11 files), unchanged and not otherwise opened (the two permitted notes were not read); review42/43/45, declarations v1–v4, the R43 review package and the five trees unchanged; r32-v4 and r32-v5 absent. No `pip install`, no git write, no `claude`, no network.

## Not done / deviations

- Preflight steps 8–12, the split / loop / cross-project / CLI dry phases and the 549-test suite were not run (card).
- `create_scope_r42.py` was not run, not even `preview`.
- The dry single phase's append to `r45q/out/TRIMMED.jsonl` failed (folder missing) after the trim; recorded in `evidence/DRY-TRIMMED-NOTE.json`.
- `SUMMARY-R32-V5.md`, `BUDGET-CARD-V6.md` and this report were written into `r45q/o` and copied byte-for-byte into the package (the writing tool refused report-like file names in the package).
- Work folder `C:/t/r2x/r42-sandbox/r45q` (about 322 MB before the manifest); C: free about 3.4 GB.
