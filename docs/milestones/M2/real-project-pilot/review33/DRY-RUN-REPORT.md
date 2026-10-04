# Dry run of the r32 harness (ORCH-05.1): no model request, no prediction

| | |
|---|---|
| **Command** | `python dry_run_r33.py r33dry-20261003b <package>/BINDING-MANIFEST-R33.json d1a8a40100fc05a937ccf40f6fb02a5788bfbea8a74adafcfc68b0f01a53936e`, run in the work folder `C:/t/iso/work/r2x/r33` |
| **Window** | 2026-10-03 11:22:08Z to 11:22:33Z |
| **Report** | `dry-run/DRY-RUN-REPORT.json` (sha256 `0e884550…789d`) |
| **Reference set** | Independently AI-reviewed (Claude agents), not human-signed |

## Safety facts

| Check | Result |
|---|---|
| **AI ledger** (`file:…r2x-ledger.sqlite?mode=ro`, `uri=True`), before | 483 entries, 17 scopes, 0 limit amendments. The scope-name digest is `a037785a…663e` |
| AI ledger, after | **483 / 17 / 0**, with the same scope-name digest. **No ledger scope was created** |
| Provider or model calls | **0**. No provider was built in any lane. Every live provider class of each application tree was replaced by one that raises, and `live_provider_attempts_blocked` is empty in every lane. Lanes ran with a PATH that holds no CLI and with an empty `AI_LEDGER_PATH` |
| Requests that reached the dry stub | B 24, C 24, R 1 and P 0. Each is a synthetic `r33_dry_probe` that carries no document content. The stub answered `dry_refused` without calling anything. These are the capture-store and allowance exercises, **not model requests** |
| Predictions | **None.** No application reader ran on any cohort document (`reader: "none"`). `rows-B.json` holds only the 24 bare PENDING registrations, with `extracted` null. Dry mode refuses `reader: "application"` on a cohort document (`test_dry_mode_refuses_to_run_a_reader_on_a_cohort_document`) |
| Dispatch guard | It refused: `OWNER-DISPATCH-AUTHORIZATION.json` does not exist (`dry-run/GUARD-CHECK.json`). This task did not create the file |
| Writes | Only the work folder, this package, the agent scratchpad and `C:/t/r2x/r33-sandbox/`. `backend/ep_platform.db` was never opened. No live service, OneDrive file or sealed project was touched, and the staging area was read-only |

## What ran

1. **Preflight of the inputs** (`preflight_inputs.py`): PACKET OK.
   - Every frozen hash was equal.
   - The manifests re-verified entry by entry: review31 58/58, reviewed-2 43/43, packet 110/110.
   - cand-r29 `a8aacedd` and frozen-r12 `3d5607d9` were clean.
2. **Adapter.** `TRUTH-R32.json` (`4e237a4e…e064`) was rebuilt and is byte-identical, so it is deterministic.
   - Populations are 57/38/38, the same as `FIELD-POPULATION.json`.
   - NOT_SCORABLE covers 32 rows on 32 pages in 25 documents.
3. **Run-set selector.** `RUN-SET-PROPOSAL.json` (`9058f3d6…7ce8`) was rebuilt and is identical.
   - It holds 24 documents: 16 decision-bearing, 4 revision top-ups and 4 negative controls.
   - **The unsupported controls are short by 2.**
   - Projection: identity 23, revision 16, decision 16.
4. **Ingestion of all 72 staged files** (`dry-run/INGEST-72.json`).
   - The sandbox is `C:/t/r2x/r33-sandbox/r33dry-20261003b-all72`.
   - 6 projects × 12 documents were registered PENDING by the baseline tree's own `document_sync.listing`. Nothing was opened, hashed or read.
   - There are 0 rows each in `ai_usage`, `document_readings`, `background_jobs`, `result_cache`, `extraction_runs` and `project_submittals`.
   - Each staged sha256 equals SOURCE-MANIFEST before and after the copy.
   - The B file is `5a14adb1…`. `state_check.check_c_start` on a C copy is **ok**: equal logical content, no C-policy evidence, no evidence cache row.
5. **Runner, dry mode** (`dry-run/runner/`), over the proposal.
   - **Binding.** The binding manifest `d1a8a401…` was verified, with 68 files re-hashed.
   - **Population gate:** DISPATCH_ELIGIBLE.
   - **B:** the run set (24) was ingested into `C:/t/r2x/r33-sandbox/r33dry-20261003b/B`. The B file is `3dc82db2…`, unchanged after lane B because no reader ran. Lane B loaded the baseline tree under the confinement asserts and sent 24 probes through the chain (stop guard → capture store → durable allowance → dry stub). The tripwire subprocess ran on an empty fact list.
   - **C-from-B and R-from-B:** `state_check` was ok for both, against the recorded B hash.
   - **C:** the candidate tree was loaded with the C switches (policy `…+identity-role-guard…+decision-region…+page-association…`) and sent 24 probes in lane C.
   - **R:** the candidate was loaded with the reference switches. **All 24 of C's probes were served to R from C's capture by content key**, and 1 reference-only probe was sent in lane R.
   - **P:** C had 0 answered dispatches (all were refused), so the sample was 0.
   - **Capture store:** 49 rows, 0 duplicate bound keys, 0 R rows served to C, 0 P rows served to B or C.
6. **Resume drill.** C ran again, against a copy of the capture and of the allowance, with C's first request reset to RESERVED.
   - **0** requests reached the stub.
   - The reserved request was served once as `interrupted_charged` and never re-sent.
   - There were 24 same-fingerprint serves and 49 rows before and after.
   - The allowance charges were 49 before and 49 after: nothing refunded, nothing added.
   - **Passes.**
7. **Scoring of the dry lanes.** `score_lane_r32` + `score_bcr_r32` produced `runner/SCORE-BCR-R32.json`, marked `exercise_only`.
   - With 0 facts in every lane, every field is NOT ELIGIBLE (matched 0 < 12, clean recovery 0.0), and concentration is UNDETERMINED.
   - **This is not a result.**
8. **Scorer and concentration on synthetic results** (`dry-run/SCORER-SCENARIOS.json`). The lanes were built from the frozen truth itself: correct values were copied from it and wrong values were invented. No reader was involved. The scenarios use the real run set (matched identity 23, revision 16, decision 16).

| Scenario | Outcome by field (identity / revision / decision) | Concentration | Note |
|---|---|---|---|
| S1 uniform gain | ELIGIBLE / ELIGIBLE / ELIGIBLE | ELIGIBLE ×3 | request gate passes: 55 facts for 100 extra requests. The largest project share is 0.375 (EP-27331), and so is the largest layout share |
| S2 gain only in EP-27331 (+2) | NOT ELIGIBLE ×3 | NOT ELIGIBLE ×3 | more than half from one project, contractor and layout key (6 of 7 and 6 of 6); recovery is below 0.90 as well |
| S3 one wrong revision in C (F009 p1) | NOT ELIGIBLE ×3 | ELIGIBLE ×3 | the critical is attributed to `revision / F009 / p1`. It is a candidate-level safety failure, a new false acceptance fails the request gate, and revision precision is 0.971 |
| S4 decision accepted on negative control F042 | NOT ELIGIBLE ×3 | decision NOT ELIGIBLE | the negative-control leg, plus the critical at `decision / F042 / p1` |
| S5 accepted values on all 12 NOT_SCORABLE run-set rows | NOT ELIGIBLE ×3 | ELIGIBLE ×3 | 0 resolved criticals and 12 unresolved, which are reported. The new unresolved false acceptances fail the request gate, keeping parity with Review 31 |
| S6 decision gain on 3 documents | ELIGIBLE / ELIGIBLE / NOT ELIGIBLE | decision UNDETERMINED | decision recovery is 0.15. A net gain of 3 is below the minimum of 4, so it is reported and does not block |

## What the dry run does not show

- No accuracy figure for B, C or R.
- No request, token, latency or cost estimate for the r32 run.
- No live behaviour of the provider path. That path is unreachable until the owner's authorization exists.
- The application readers' path in dry mode was exercised only on **synthetic** documents, in `test_runner_r32.py`:
  - B processed two generated PDFs of an invented project EP-990001;
  - the per-document tripwire ran after every document and at the end;
  - a deliberately wrong synthetic truth made B terminal, the comparison INVALID, and C never started;
  - C-from-B, R served from C, and the resume drill all ran.

The superseded first attempt, `r33dry-20261003a`, wrote its runner JSON with CRLF line endings. Its package outputs were removed, its sandboxes are kept and unused, and the audit log records it.
