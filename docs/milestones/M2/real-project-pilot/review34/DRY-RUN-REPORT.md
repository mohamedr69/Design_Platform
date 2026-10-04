# Dry run (review34, ORCH-05C)

| | |
|---|---|
| **Command** | `dry_run_r34.py r34dry-20261003b <package>/BINDING-MANIFEST-R34.json 3d0f8bfe37d55a4c0490e054c0d710f4bb1d2ac839dffd08daaafca19063ea27` (`COMMANDS.md`) |
| **When** | 2026-10-03T12:49:43Z to 12:50:24Z |
| **Report** | `dry-run/DRY-RUN-REPORT.json` (sha256 `4ef5297fc9201326d214f716036c42b5f1e8bbfd7332ecd8e0d61730595dc46a`) |
| **Provider or model requests** | **0**. No provider exists in dry mode: every request ended at `DryRefusingProvider` (`dry_refused`) |
| **AI ledger** (`mode=ro`) | **483 entries / 17 scopes / 0 amendments before and after**; scope-name hash `a037785a…663e` unchanged; **no scope created** |
| **Prediction** | none: reader `none` on every cohort document; no application reader touched a cohort document |
| **Authorization** | none: no `OWNER-DISPATCH-AUTHORIZATION.json` (or any file named like a dispatch authorization, or any JSON object with an authorization's keys) under the pilot folder, the work folders, the r34 sandbox or the scratchpad |
| **Reference set** | independently AI-reviewed (Claude agents), not human-signed |

An earlier attempt (`r34dry-20261003a`) is recorded in `CORRECTION-REPORT.md` §7: its drill passed and the ledger stayed 483/17, but its authorization-file search also matched two pre-existing earlier-package files; the search was made precise and the run repeated.

## 1. Inputs re-derived (carried unchanged)

- `PACKET OK` from `preflight_inputs.py` (every task hash, review33 112/112, review33 binding 68/68, review31 58/58, reviewed-2 43/43, packet 110/110, HEADs clean, ledger 483/17/0, response ledger `500d55f5…90ac`).
- The adapter re-derives `TRUTH-R32.json` `4e237a4e…e064`; the selector re-derives `RUN-SET-PROPOSAL.json` `9058f3d6…7ce8` (24 documents: 16 decision-bearing, 4 top-ups, 4 negative controls; unsupported controls short by 2; projection identity 23, revision 16, decision 16); the converter re-derives `LABELS-R32-EVAL-INPUT.json` `4b2c73d5…5cc`. Populations 57/38/38.

## 2. Ingestion of all 72 staged files (`dry-run/INGEST-72.json`)

The unchanged `sandbox_ingest_r32` (base set to `C:/t/r2x/r34-sandbox/`) registered all 72 files of the six projects in `C:/t/r2x/r34-sandbox/r34dry-20261003b-all72/` through the baseline tree, **without processing**: 72 rows `pending`; `ai_usage`, `document_readings`, `background_jobs`, `result_cache`, `extraction_runs`, `project_submittals` all 0; the C-from-B state check passes.

## 3. The two-invocation drill (RC-4; `dry-run/runner/`)

One run folder for the dry run key `ee5b192a…203b`: `C:/t/r2x/r34-sandbox/r34dry-20261003b/` (allowance, capture store, `RUN-STATE.json`).

| Step | Command | Result |
|---|---|---|
| 1 | `run` with `--dry-fault C:5` | B completed (24 probes); lane C **died right after its 5th dispatch was sent**: C rows 4 `failed` (dry_refused) + **1 `reserved`** (seq 29); charges B 24, C 5. Invocation 1 `interrupted` (`runner/inv-1/`) |
| 2 | `run` again (same stamp) | **Refused**: "a second fresh invocation of this run is refused … use 'resume'" |
| 3 | `resume` (same stamp) | **Completed** (`runner/inv-2/`): B **0** new dispatches (24 served `same_bound_fingerprint`); C **19** new dispatches = only the requests never made (5 served, of which the reserved one **once as `interrupted_charged`**); R served C's 24 by content key and sent 1 reference-only; P 0. Seq 29 is still `reserved` (never re-sent). Duplicate bound keys: 0. Caps fixed **240/240/40/36** (no fresh caps); charges B 24, C 24, R 1, P 0 = 49 = the 49 capture rows (every charge a first dispatch) |
| 4 | `resume` again | **Refused**: "the run is complete; there is nothing to resume" |
| 5 | `run` again | **Refused**: a second fresh invocation |

`runner/DRILL.json` holds the 15 checks (all true); `runner/RUN-STATE.json` shows invocation 1 `fresh` / `interrupted` and invocation 2 `resume` / `finished` (comparison PENDING, candidate outcome NOT ELIGIBLE because every lane has 0 facts in a dry run). In invocation 2: C-from-B and R-from-B state checks pass; every lane `reader: none`, no live provider attempt blocked (none was attempted), 0 model requests; lane switches labelled "dry defaults (the DRAFT-DECLARATION.v2 arms); used in dry mode only, never in live mode" and verified by each lane.

## 4. The guard (`dry-run/GUARD-CHECK.json`, RC-3)

- The pinned path for a declaration at the review34 package root (`review34/OWNER-DISPATCH-AUTHORIZATION.json`) does not exist.
- `check(None, None)`: refused ("no verified declaration"); `check(<review34>/DECLARATION.json, 000…)`: refused (the declaration is missing / does not hash).
- `runner_r32.py run --mode live … --auth-path …`: exit 2, "unrecognized arguments: --auth-path".
- `GuardedProvider` without an authorization: `dispatch_refused`, the real provider never built.
- Files whose name contains AUTHORIZATION under the pilot folder are listed as pre-existing (all written before this task, none an owner dispatch authorization).

## 5. Scorer and concentration rule v2 on Review 34's scenarios (`dry-run/SCORER-SCENARIOS.json`)

Synthetic lanes made from the truth itself (no reader, no model, no prediction); these exercise the scorer and are **not results**.

| Scenario | Candidate outcome (RC-2) | Field outcomes (identity / revision / decision) |
|---|---|---|
| S1 one wrong revision acceptance (F037) | NOT ELIGIBLE | NE / NE / NE; revision failures **1** (RC-6) |
| S2 identity +8, wrong decision on F072 | NOT ELIGIBLE | NE / NE / NE |
| S3a decision +2 in EP-22349 | NOT ELIGIBLE | NE / NE / NE; decision concentration NOT ELIGIBLE |
| **S3b decision +3 on F037, F009, F032 (EP-27331)** | **NOT ELIGIBLE** | E / E / **NE** (concentration: project, contractor, layout 1.0) |
| S3c decision +4 in EP-27331 | NOT ELIGIBLE | E / E / NE |
| S3c-spread decision +4 over four projects | **ELIGIBLE FOR A SEPARATE SELECTION DECISION** | E / E / E |
| S3d every field +, two EP-22349 documents | NOT ELIGIBLE | NE / NE / NE |
| S4a C skips five decision documents | NOT ELIGIBLE | NE / NE / NE (decision matched 11) |
| S4b as S4a, INCOMPLETE | INCOMPLETE | INCOMPLETE ×3 |
| **S5 identity +8, decision recovery 0.7576** | **NOT ELIGIBLE** | E / E / NE |
| S6 revision +6, −2 in EP-26687 | NOT ELIGIBLE | NE / NE / NE |
| S7 decision accepted on negative control F060 | NOT ELIGIBLE | NE / NE / NE |
| S8 decision +2 in one project, identity −1 | NOT ELIGIBLE | NE / NE / NE |

E = ELIGIBLE FOR A SEPARATE SELECTION DECISION (diagnostic), NE = NOT ELIGIBLE. **EP-27331 decision gain sweep:** sizes 1 to 6 are NOT ELIGIBLE (concentration and candidate); the request gate passes from size 3.

## 6. What the dry run does not show

The live path end to end (no authorization, no provider, no scope may exist) and the application's processing of the real cohort PDFs, which happens for the first time in live B (R34-18).
