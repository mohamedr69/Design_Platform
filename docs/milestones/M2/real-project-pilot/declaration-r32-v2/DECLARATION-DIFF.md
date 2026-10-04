# Declaration diff: superseded `38e08df9…76b0` → corrected `f38fb281…25af`

- **Superseded:** `C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json` sha256 `38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0` (A-09: never authorized, never run, never to be run).
- **Corrected:** `C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.json` sha256 `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af`.
- **Method:** both files are flattened to leaf paths (objects recursed, lists compared whole). Every top-level key is listed with its status and the reason; every added, removed or changed leaf path is listed below it. The machine-readable version, with full values, is `DECLARATION-DIFF.json` (written by `scripts/diff_declaration_r40.py`).
- **Top-level keys:** 17 unchanged, 31 changed, 27 added, 4 removed.
- **Leaf paths:** 112 changed, 518 added, 124 removed.
- **Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed.

## 1. Top-level keys

| Key | Status | Why |
|---|---|---|
| `application_ai_limits` | changed | compatible limits with margins and justification; integer strings (R40-08); the 'silent stops' replaced by recorded unread pages |
| `application_env` | added | ADDED: contract 4 exactly {DRAWINGS_AI_REVIEW_ENABLED: false} (R39-04) |
| `application_env_detail` | added | ADDED: explanation |
| `authorities` | changed | A-09 and A-10 applied and summarised; register hash 346597d3... (A-09 and A-10 present) |
| `authorization` | changed | pinned path beside this declaration; two-hash procedure (R38-07) with the RUN file and who verifies the RUN hash; review39 contract section 3 carried verbatim; invocation from the review39 harness |
| `authorization_status` | unchanged | unchanged |
| `binding_manifest_sha256` | changed | bound harness review39 (BINDING-MANIFEST-R39 a6f703b4...) instead of review36 (5a1a6aad...) |
| `budget` | added | ADDED: contract 4 parent budget {total 556, input 16,300,000, output 3,260,000, elapsed 604,800 s} and lane allowances (A-09 point 3) |
| `budget_approved` | unchanged | unchanged |
| `budget_detail` | added | ADDED: A-09 point 3 rule, enforcement, no borrowing, charges never refunded |
| `caps` | removed | REMOVED: contract 4 names the lane allowances budget.lane_allowances (same values B 240 / C 240 / R 40 / P 36) |
| `caps_detail` | removed | REMOVED: replaced by budget_detail |
| `cohort` | unchanged | unchanged |
| `concentration_on_proposal` | added | ADDED: the superseded package's concentration results carried by hash (module and run set unchanged) |
| `contract` | added | ADDED: contract 4 (review39 preflight_r32.CONTRACT 'r39-live-contract-4'); the superseded file predates the key |
| `controls` | changed | the shortfall entry gains its A-09 point 6 statement |
| `cost` | unchanged | unchanged |
| `cross_page_identity` | added | ADDED: rule CP-R38 (A-09 point 5) |
| `decision_coverage_gate` | added | ADDED: contract 4 'C_GE_B_ONLY' (A-10): a change from plan v2 |
| `decision_coverage_gate_detail` | added | ADDED: the bound text, the change from plan v2, the plan v2 definition, the mandatory diagnostic, contract v4 section 12 verbatim |
| `declared_at_utc` | changed | the time of this freeze |
| `disclosures` | changed | stale items replaced (day limit, silent stops, H4, H5, the twin); new disclosures for R40-04/08/10/12/13, the CLI-version dead-end, identity UNRESOLVED, tokens at the structural maximum, path length, the dry exercise |
| `dispatch_order` | changed | owner steps before invocation 1; CLI version and nonce consumption; lane gating on deferral; frozen P sample; DEFERRED / resume |
| `elapsed_bounds` | changed | two clocks (allowance and scope); waiting times under 'full' |
| `emission_rules` | unchanged | unchanged |
| `estimated_usage` | changed | structural maxima and per-project figures from PROJECT-REQUEST-BOUNDS replace the superseded 'conservative' 8-per-document maxima (R38-08); tokens at the structural maximum |
| `evaluator` | changed | judging statement names the review39 lane_judge (rule CP-R38) |
| `executed` | unchanged | unchanged |
| `forbidden_after_authorization` | changed | four items added (the frozen hash never with the runner; the scope once; the probe outside the harness; no direct lane) |
| `gates` | changed | decision_coverage CHANGED to C >= B only (A-10; a change from plan v2); comparison_state (A-09 point 1) and other_gates added; every other gate verbatim |
| `harness` | changed | review39 (manifest 2430fa2b..., binding a6f703b4..., 239 bound files) replaces review36; modules and contracts re-bound; lineage; review39 SNAPSHOT-BEFORE 09:55:49Z (R40-19); work records bound (R40-20) |
| `interpretations` | changed | the .10-parity cross-page items and the H4 gap are superseded by rule CP-R38 (A-09 point 5) |
| `lane_switches` | unchanged | unchanged |
| `lane_task_kinds` | added | ADDED: contract 4 task kinds per lane = task_kinds_for(lane_switches) (R39-04) |
| `lane_task_kinds_detail` | added | ADDED: explanation |
| `lanes` | changed | task kinds per lane; B's drawings-AI review off; R no credit and never eligibility (A-09 point 7, A-10); P's population drawn at its first run (R40-12) |
| `ledger` | changed | new scope name m2-fresh-validation-r32-v2-2026-10-04; limits unchanged (equal to the parent, contract 4) |
| `ledger_detail` | changed | creation by create_scope_r40.py (R38-11); two elapsed clocks; reconciliation before every resume |
| `model_identity` | added | ADDED: contract 4 pinned full ids, provider, CLI path and version line '2.1.263 (Claude Code)' (A-09 point 2, A-10) |
| `model_identity_detail` | added | ADDED: served-model identity UNRESOLVED, the runtime check fail-closed with its two limits, the CLI file hash, the probe pointer |
| `name` | changed | names the corrected declaration v2 |
| `plan_sources` | unchanged | unchanged |
| `policy` | unchanged | unchanged |
| `primary_outcomes` | unchanged | unchanged |
| `probe_population` | added | ADDED: R40-12 |
| `project_day_limit` | removed | REMOVED: the UTC day limit 60 is replaced by the rolling project window (A-09 point 1) |
| `project_day_limit_detail` | removed | REMOVED: replaced by project_window_detail (deferral, not a permanent refusal) |
| `project_request_bounds` | added | ADDED: contract 4 binding of PROJECT-REQUEST-BOUNDS.json (99be01fb...) |
| `project_request_bounds_detail` | added | ADDED: EP-27331 planning 63.0 / structural 160 / 170 with the drawings path; required minimum 84 |
| `project_window` | added | ADDED: contract 4 harness rolling window {limit 60, window_s 86,400}, all lanes |
| `project_window_detail` | added | ADDED: deferral rule, lane gating, what it replaces |
| `provider` | changed | owner-confirmable fields restated for full ids, the CLI pin, the scope name and the per-project limit; owner_confirmable 'project_day_limit' removed |
| `provider_env` | changed | full model ids (A-09 point 2); new scope name; per-project limit 96 >= 84 (compatible limits); integer strings for every count and time limit (R40-08: '120', '1800', prices '0') |
| `r_and_p` | added | ADDED: A-09 point 7 (no credit; diagnostic INCOMPLETE) |
| `reference_set` | unchanged | unchanged |
| `reference_set_statement` | unchanged | unchanged |
| `request_path_coverage` | added | ADDED: R40-04 -- the corrected claim, the proof bound by hash, the residual risk, the owner's two options |
| `resume_detail` | added | ADDED: RESUME-INVOCATIONS-R39 (9791fa89...) bound; 2 / 3 invocations under 'full' |
| `resume_policy` | added | ADDED: contract 4 resume_policy 'full' (R39-08) |
| `retry_rule` | added | ADDED: R40-13 -- the failed-read retry named as a change from plan v2 section 4 |
| `reviews` | changed | Verifications 38, 39 and 40 added |
| `revision_comparison_rule` | changed | implementation re-bound to the review39 copy of literal_compare_r32.py (same hash c23ba577...) |
| `run` | changed | contract 4: declared sandbox_base; base C:/t/r2x/r40-sandbox and stamp r32-v2 (short paths, justified); the superseded folder was under r34-sandbox |
| `run_set` | changed | selector re-bound to the review39 copy (ec5025d2..., its selection code unchanged since review36; the replacement refusal appended in review38); frozen_by restated |
| `run_set_sha256` | unchanged | unchanged |
| `schema` | changed | new schema id for the corrected declaration |
| `scope_limitations` | added | ADDED: the shortfall as a declared scope limitation and what is not claimed (A-09 point 6) |
| `standing_status` | unchanged | unchanged |
| `status` | changed | adds 'no run file' and 'Verification 41' to the not-authorized status |
| `stop_rules` | changed | review39 contract v4 sections 4, 5, 6 and 13 verbatim REPLACE the review34 resume rules (R40-13); terminal states INCOMPLETE / DEFERRED / INVALID / CLOSED / RESULT / FINISHED; the stop-and-safety table unchanged |
| `supersedes` | added | ADDED: names the superseded declaration and its manifest (A-09) |
| `switch_names` | unchanged | unchanged |
| `task` | changed | ORCH-09 / R40DECL-IMPL |
| `thresholds_verbatim` | unchanged | unchanged (re-verified verbatim at build time) |
| `token_thresholds` | changed | enforcement restated (the allowance also enforces the parent token bounds); breaker margins (R38-13) |
| `trees` | changed | adds config.py of the baseline, the application ledger.py and provider.py hashes |
| `unread_page_rule` | added | ADDED: R39-06 rule, the no_trigger exclusion and two unguarded corners (R40-10), the R40-15 acknowledgement |
| `verification40_items` | added | ADDED: where each Verification 40 item is answered |
| `what_this_run_can_show` | unchanged | unchanged |

## 2. Every changed, added or removed leaf path

### `application_ai_limits` (changed)

- changed `application_ai_limits.bound.AI_MAX_CALLS_PER_PROJECT_PER_DAY`: "60" → "96"
- changed `application_ai_limits.bound.AI_MAX_ELAPSED_S_PER_JOB`: "120.0" → "120"
- changed `application_ai_limits.bound.AI_PRICE_CACHED_INPUT_PER_MILLION`: "0.0" → "0"
- changed `application_ai_limits.bound.AI_PRICE_INPUT_PER_MILLION`: "0.0" → "0"
- changed `application_ai_limits.bound.AI_PRICE_OUTPUT_PER_MILLION`: "0.0" → "0"
- changed `application_ai_limits.bound.AI_READ_MAX_ELAPSED_S`: "1800.0" → "1800"
- changed `application_ai_limits.statement`: "bound in provider_env at the candidate and baseline tree defaults (equal in both config.py files; no .env file exists in either tree; sandbox_env ... → "bound in provider_env; every other application limit stays at the candidate and baseline tree default (equal in both config.py files, b4fbc07f...;...
- added `application_ai_limits.compatible_limits.AI_MAX_CALLS_PER_DOCUMENT.basis`: "required equal to the bounds' assumption (tree default 12)"
- added `application_ai_limits.compatible_limits.AI_MAX_CALLS_PER_DOCUMENT.value`: "12"
- added `application_ai_limits.compatible_limits.AI_MAX_CALLS_PER_PROJECT_PER_DAY.justification`: "the required minimum 84 is the largest AiUsage row count any lane database can hold in one invocation (EP-27331: B's 12 rows + C's JobBudget 12 x ...
- added `application_ai_limits.compatible_limits.AI_MAX_CALLS_PER_PROJECT_PER_DAY.margin`: 12
- added `application_ai_limits.compatible_limits.AI_MAX_CALLS_PER_PROJECT_PER_DAY.value`: "96"
- added `application_ai_limits.compatible_limits.AI_MAX_ELAPSED_S_PER_JOB.basis`: "required equal to the bounds' assumption (tree default 120.0, written '120')"
- added `application_ai_limits.compatible_limits.AI_MAX_ELAPSED_S_PER_JOB.value`: "120"
- added `application_ai_limits.compatible_limits.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY.justification`: "the tree default and the superseded declaration's value, unchanged: it governs only B's form reads (sheet_reader uses max(read limit, project limi...
- added `application_ai_limits.compatible_limits.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY.margin`: 516
- added `application_ai_limits.compatible_limits.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY.value`: "600"
- added `application_ai_limits.compatible_limits.check`: "project_bounds_r32.check_compatible(provider_env, PROJECT-REQUEST-BOUNDS) returns [] (no problem)"
- added `application_ai_limits.compatible_limits.required_minimum.AI_MAX_CALLS_PER_PROJECT_PER_DAY`: 84
- added `application_ai_limits.compatible_limits.required_minimum.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY`: 84
- added `application_ai_limits.integer_strings`: "R40-08: every count and time limit is written as an integer string ('96', '600', '12', '120', '1800'; never '84.0'); the only non-integer numeric ...
- added `application_ai_limits.not_silent`: "replaces the superseded 'silent_stops': the application's per-document limits (the reader's cap 8, the JobBudget 12 / 120 s, a reader exception) a...
- removed `application_ai_limits.silent_stops`: ["the evidence reader opens one JobBudget per document: at most 12 calls (the reader's own MAX_CALLS_PER_DOCUMENT 8 binds first), 120 s elapsed per...

### `application_env` (added)

- added `application_env.DRAWINGS_AI_REVIEW_ENABLED`: "false"

### `application_env_detail` (added)

- added `application_env_detail`: "exactly the allowlist contract 4 requires: the baseline's drawings-AI review (document_processing.run -> shop_drawings.reconcile -> drawing_ai_rev...

### `authorities` (changed)

- changed `authorities.applied`: ["A-03", "A-06", "A-08"] → ["A-03", "A-06", "A-08", "A-09", "A-10"]
- changed `authorities.register.sha256`: "01df9af0eacc38db93cbe262077bb2952806ac80ca50dc68f242711d04e02a96" → "346597d3c482cf66b7daeaec17a1334715d6e000be68725679013184361ffcfd"
- added `authorities.summary.A-09`: "the frozen R32 declaration 38e08df9...76b0 is not authorized and is superseded; one bounded preparation correction and a NEW declaration hash: com...
- added `authorities.summary.A-10`: "decision coverage eligibility C >= B only, C >= R a mandatory diagnostic, explicitly a change from plan v2 (1); the owner runs the model-identity ...

### `authorization` (changed)

- changed `authorization.file_fields.declaration_sha256`: "the sha256 of the runnable (digest-filled) declaration file" → "the RUN hash (the sha256 of the digest-filled RUN declaration file), never the frozen hash"
- changed `authorization.file_fields.owner_token_sha256`: "the same digest the runnable declaration binds" → "the same digest the RUN declaration binds"
- changed `authorization.invocation.harness_copy`: "C:/t/iso/work/r2x/r36/harness-r32 is the copy BINDING-MANIFEST-R36 binds as harness_r36; PILOT/review36/scripts/harness-r32 is byte-identical (har... → "PILOT/review39/scripts/harness-r32 is the copy BINDING-MANIFEST-R39 binds as harness_r39_package; C:/t/iso/work/r2x/r39/harness-r32 is byte-identi...
- changed `authorization.invocation.resume`: "the same with 'resume' (a new authorization with a fresh nonce first)" → "the same with 'resume' instead of 'run' (a new authorization file with a fresh nonce first; not before RUN-STATE.json resume_not_before_utc)"
- changed `authorization.invocation.run`: "python runner_r32.py run --mode live --declaration <absolute path of the runnable declaration in PILOT/declaration-r32/> --declaration-sha <its sh... → "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe -B runner_r32.py run --mode live --declaration C:/Users/moham/Desktop/d...
- changed `authorization.invocation.working_directory`: "C:/t/iso/work/r2x/r36/harness-r32" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32"
- changed `authorization.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32/OWNER-DISPATCH-AUTHORIZATION.json" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v2/OWNER-DISPATCH-AUTHORIZATION.json"
- changed `authorization.placeholder_rule`: "owner_token_sha256 holds an explicit placeholder, not a digest: preflight_r32.validate_declaration and dispatch_guard_r32 refuse it ('the declarat... → "owner_token_sha256 holds an explicit placeholder, exactly once in this file, not a digest: preflight_r32.validate_declaration and dispatch_guard_r...
- changed `authorization.runbook`: ["R35-07 / R35-10: the owner creates the ledger scope NEW and EMPTY with exactly ledger.limits and a closed breaker, immediately before the first i... → "RUNBOOK.md in this package (exact, ordered, absolute paths); SCOPE-CREATION-COMMAND.md for the scope"
- changed `authorization.token_presentation`: "the owner presents the token in the environment variable R34_OWNER_DISPATCH_TOKEN at each invocation; it is compared by digest and never written t... → "the owner presents the token in the environment variable R34_OWNER_DISPATCH_TOKEN at each invocation and at the scope creation; it is compared by ...
- added `authorization.authorization_rule_v4_verbatim.lines`: "58-66"
- added `authorization.authorization_rule_v4_verbatim.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `authorization.authorization_rule_v4_verbatim.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `authorization.authorization_rule_v4_verbatim.text`: ["## 3. The authorization (`dispatch_guard_r32`, unchanged)", "", "As in contract 2, section 3:", "- the pinned `OWNER-DISPATCH-AUTHORIZATION.json`...
- added `authorization.invocation.environment.GIT_OPTIONAL_LOCKS`: "0"
- added `authorization.invocation.environment.PYTHONDONTWRITEBYTECODE`: "1"
- added `authorization.invocation.environment.R34_OWNER_DISPATCH_TOKEN`: "<the owner's token, never written>"
- added `authorization.invocation.python`: "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
- added `authorization.two_hash_procedure.authorization_file`: "names the RUN hash (declaration_sha256), never the frozen hash"
- added `authorization.two_hash_procedure.budget_authorization_names`: ["the frozen hash", "the digest", "the RUN hash", "the absolute RUN-file path C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-pr...
- added `authorization.two_hash_procedure.digest`: "sha256 of the token's UTF-8 bytes with no trailing newline, written as 64 lower-case hex characters"
- added `authorization.two_hash_procedure.frozen_hash`: "the sha256 of THIS file (DECLARATION.sha256); it identifies what the owner reviewed and is never given to the runner"
- added `authorization.two_hash_procedure.independent_verification`: "before any authorization file or scope exists, the orchestrator (or an independent verifier) re-computes it with build_declaration_r40.py verify_r...
- added `authorization.two_hash_procedure.run_file`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json"
- added `authorization.two_hash_procedure.run_hash`: "the sha256 of the RUN file, computed by the owner when the file is written (fill_owner_digest prints it)"
- added `authorization.two_hash_procedure.token`: "generated by the owner, high-entropy (for example 32 random bytes as 64 hex characters), held only by the owner, never stored in any file, present...

### `binding_manifest_sha256` (changed)

- changed `binding_manifest_sha256`: "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568" → "a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b"

### `budget` (added)

- added `budget.lane_allowances.B`: 240
- added `budget.lane_allowances.C`: 240
- added `budget.lane_allowances.P`: 36
- added `budget.lane_allowances.R`: 40
- added `budget.parent.elapsed_s`: 604800
- added `budget.parent.input_tokens`: 16300000
- added `budget.parent.output_tokens`: 3260000
- added `budget.parent.total`: 556

### `budget_detail` (added)

- added `budget_detail.enforcement`: "allowance_r32 charges before dispatch per lane (never refunded, never raised); the parent total 556, input tokens 16,300,000, output tokens 3,260,...
- added `budget_detail.equal_allowance_B_C`: "B 240 = C 240 (8 per document x 30 documents): the request gate is defined at equal caps (R31-03)"
- added `budget_detail.per_document_cap_basis`: "8 requests per document x 30 documents = 240; the run set holds 24 documents"
- added `budget_detail.replaces`: "the superseded keys caps / caps_detail (contract 4 names them budget.lane_allowances)"
- added `budget_detail.rule`: "A-09 point 3: one immutable parent experiment budget with separately auditable lane allowances; no lane borrows another's allowance; the declared ...
- added `budget_detail.total`: 556

### `caps` (removed)

- removed `caps.B`: 240
- removed `caps.C`: 240
- removed `caps.P`: 36
- removed `caps.R`: 40

### `caps_detail` (removed)

- removed `caps_detail.enforcement`: "allowance_r32 reserves before dispatch per lane (never refunded, never raised) and the ledger scope's 'requests' limit 556 is the cumulative backs...
- removed `caps_detail.equal_allowance_B_C`: "B 240 = C 240 (8 per document x 30 documents): the request gate is defined at equal caps (R31-03)"
- removed `caps_detail.per_document_cap_basis`: "8 requests per document x 30 documents = 240; the run set holds 24 documents (192 at 8 per document)"
- removed `caps_detail.total`: 556

### `concentration_on_proposal` (added)

- added `concentration_on_proposal.carried`: "concentration_r32.py is byte-identical in review36 and review39 (fc5052f8...) and the run set is unchanged, so the superseded package's results on...
- added `concentration_on_proposal.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32/concentration/CONCENTRATION-ON-PROPOSAL.json"
- added `concentration_on_proposal.sha256`: "5ebc2885edb306b611a35ac2c01d5a68033dbafed052706edb8699dc5ceda215"

### `contract` (added)

- added `contract`: "r39-live-contract-4"

### `controls` (changed)

- added `controls.unsupported_control_shortfall.declared_scope_limitation`: "A-09 point 6 (owner): accepted ONLY as a declared scope limitation; no control is replaced after predictions exist (run_set_selector_r32.replace_c...

### `cross_page_identity` (added)

- added `cross_page_identity.rule`: "CP-R38 (A-09 point 5; review38 SCORER-CHANGES v3 Part B rows 1-2; lane_judge_r32 + page_relations_r38, unchanged in review39)"
- added `cross_page_identity.supersedes`: "the superseded declaration's .10-parity cross-page rule (review35_item10, verification36_section6, H4, H5)"
- added `cross_page_identity.text`: "an asserted identity that differs from the page's own value (or is asserted on an ABSENT identity page) is a cross-page association -- neither cor...
- added `cross_page_identity.whatif.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review38/CROSS-PAGE-WHATIF.json"
- added `cross_page_identity.whatif.sha256`: "491f9590e775fa5367569787cbc3394d8db1b82908f5f6111a2a7491da8c6fe6"
- added `cross_page_identity.whatif.summary`: "356 target verdicts change on 89 fixtures, all to critical_false_acceptance; 40 fixtures keep an evidenced association (R1 15, R2 12, R3 13); the ...

### `decision_coverage_gate` (added)

- added `decision_coverage_gate`: "C_GE_B_ONLY"

### `decision_coverage_gate_detail` (added)

- added `decision_coverage_gate_detail.bound`: "C_GE_B_ONLY"
- added `decision_coverage_gate_detail.change_from_plan_v2`: "CHANGED from plan v2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md), whose gate was C >= B AND C >= R: the C >= R leg is removed from eligibility ...
- added `decision_coverage_gate_detail.contract_v4_section_12_verbatim.lines`: "211-221"
- added `decision_coverage_gate_detail.contract_v4_section_12_verbatim.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `decision_coverage_gate_detail.contract_v4_section_12_verbatim.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `decision_coverage_gate_detail.contract_v4_section_12_verbatim.text`: ["## 12. The decision coverage gate (R39-15; the owner's ruling A-10, 2026-10-04)", "", "- **Eligibility: C >= B only.** The constant is `score_bcr...
- added `decision_coverage_gate_detail.mandatory_diagnostic`: "mandatory diagnostic (owner ruling A-10): C >= R decision coverage, reported with both lanes' counts, the missing coverage per document and the re...
- added `decision_coverage_gate_detail.other_gates`: "every other safety, accuracy and completeness gate is preserved verbatim from the superseded declaration"
- added `decision_coverage_gate_detail.plan_v2_definition.id`: "C_GE_B_AND_C_GE_R"
- added `decision_coverage_gate_detail.plan_v2_definition.status`: "SUPERSEDED by the owner's ruling A-10: R never determines eligibility; refused if a declaration or a caller binds it"
- added `decision_coverage_gate_detail.plan_v2_definition.text`: "plan v2: decision coverage of C >= that of B AND >= that of R"
- added `decision_coverage_gate_detail.statement`: "A CHANGE FROM PLAN V2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md), whose gate was C >= B AND C >= R. It is NOT an unchanged gate. The owner rul...
- added `decision_coverage_gate_detail.text`: "decision coverage eligibility: decision coverage of C >= decision coverage of B on the resolved decision documents of the run set (completed read ...

### `declared_at_utc` (changed)

- changed `declared_at_utc`: "2026-10-03T17:14:03+00:00" → "2026-10-04T11:51:31+00:00"

### `disclosures` (changed)

- changed `disclosures`: ["matched margin: the projected matched populations are identity 23, revision 16, decision 16 against the minimum of 12 (margins 11 / 4 / 4); a doc... → ["matched margin: the projected matched populations are identity 23, revision 16, decision 16 against the minimum of 12 (margins 11 / 4 / 4); a doc...

### `dispatch_order` (changed)

- changed `dispatch_order`: ["preflight (binding manifest and every bound file, the declaration contract, run set, candidate and baseline HEADs clean, truth and population gat... → ["owner, before invocation 1: the model-identity probe (RUNBOOK section 1), `claude --version` == '2.1.263 (Claude Code)', the two-hash procedure a...

### `elapsed_bounds` (changed)

- changed `elapsed_bounds.enforced`: "only the scope's elapsed_s 604,800 s (168 h), which the application's ledger measures from the scope's CREATION (scopes.created_at), not from its ... → "two clocks, both bounds, the earlier one stops first: the allowance's parent elapsed_s 604,800 s counts from the run's allowance binding (the firs...

### `estimated_usage` (changed)

- changed `estimated_usage.statement`: "estimates, not limits and not measurements; the caps and the ledger limits are the bounds" → "estimates, not limits and not measurements; the lane allowances, the parent budget, the window and the ledger limits are the bounds"
- added `estimated_usage.lanes_note`: "carried from the superseded declaration (planning B 6, C 112, R 10, P 17 = 145; low C 108). Its 'conservative' C 192 (8 per document) is NOT a bou...
- added `estimated_usage.per_project.EP-15744.application_rows_maximum.B_database`: 2
- added `estimated_usage.per_project.EP-15744.application_rows_maximum.C_database`: 14
- added `estimated_usage.per_project.EP-15744.application_rows_maximum.P`: 0
- added `estimated_usage.per_project.EP-15744.application_rows_maximum.R_database`: 14
- added `estimated_usage.per_project.EP-15744.application_rows_maximum.max`: 14
- added `estimated_usage.per_project.EP-15744.drawings_ai_if_enabled_all_lanes`: 48
- added `estimated_usage.per_project.EP-15744.pages_read`: 4
- added `estimated_usage.per_project.EP-15744.planning.B`: 0
- added `estimated_usage.per_project.EP-15744.planning.C`: 8
- added `estimated_usage.per_project.EP-15744.planning.P`: 1.2
- added `estimated_usage.per_project.EP-15744.planning.R`: 0.7
- added `estimated_usage.per_project.EP-15744.planning.all_lanes`: 9.9
- added `estimated_usage.per_project.EP-15744.planning_exceeds_window`: false
- added `estimated_usage.per_project.EP-15744.structural_exceeds_window`: false
- added `estimated_usage.per_project.EP-15744.structural_maximum.B`: 2
- added `estimated_usage.per_project.EP-15744.structural_maximum.C`: 12
- added `estimated_usage.per_project.EP-15744.structural_maximum.P`: 12
- added `estimated_usage.per_project.EP-15744.structural_maximum.R`: 12
- added `estimated_usage.per_project.EP-15744.structural_maximum.all_lanes`: 38
- added `estimated_usage.per_project.EP-15744.windows_needed_structural`: 1
- added `estimated_usage.per_project.EP-22349.application_rows_maximum.B_database`: 10
- added `estimated_usage.per_project.EP-22349.application_rows_maximum.C_database`: 61
- added `estimated_usage.per_project.EP-22349.application_rows_maximum.P`: 0
- added `estimated_usage.per_project.EP-22349.application_rows_maximum.R_database`: 52
- added `estimated_usage.per_project.EP-22349.application_rows_maximum.max`: 61
- added `estimated_usage.per_project.EP-22349.drawings_ai_if_enabled_all_lanes`: 147
- added `estimated_usage.per_project.EP-22349.pages_read`: 11
- added `estimated_usage.per_project.EP-22349.planning.B`: 2
- added `estimated_usage.per_project.EP-22349.planning.C`: 22
- added `estimated_usage.per_project.EP-22349.planning.P`: 3.3
- added `estimated_usage.per_project.EP-22349.planning.R`: 2.0
- added `estimated_usage.per_project.EP-22349.planning.all_lanes`: 29.3
- added `estimated_usage.per_project.EP-22349.planning_exceeds_window`: false
- added `estimated_usage.per_project.EP-22349.structural_exceeds_window`: true
- added `estimated_usage.per_project.EP-22349.structural_maximum.B`: 10
- added `estimated_usage.per_project.EP-22349.structural_maximum.C`: 51
- added `estimated_usage.per_project.EP-22349.structural_maximum.P`: 36
- added `estimated_usage.per_project.EP-22349.structural_maximum.R`: 40
- added `estimated_usage.per_project.EP-22349.structural_maximum.all_lanes`: 137
- added `estimated_usage.per_project.EP-22349.windows_needed_structural`: 3
- added `estimated_usage.per_project.EP-26687.application_rows_maximum.B_database`: 14
- added `estimated_usage.per_project.EP-26687.application_rows_maximum.C_database`: 83
- added `estimated_usage.per_project.EP-26687.application_rows_maximum.P`: 0
- added `estimated_usage.per_project.EP-26687.application_rows_maximum.R_database`: 68
- added `estimated_usage.per_project.EP-26687.application_rows_maximum.max`: 83
- added `estimated_usage.per_project.EP-26687.drawings_ai_if_enabled_all_lanes`: 169
- added `estimated_usage.per_project.EP-26687.pages_read`: 9
- added `estimated_usage.per_project.EP-26687.planning.B`: 3
- added `estimated_usage.per_project.EP-26687.planning.C`: 18
- added `estimated_usage.per_project.EP-26687.planning.P`: 2.7
- added `estimated_usage.per_project.EP-26687.planning.R`: 1.6
- added `estimated_usage.per_project.EP-26687.planning.all_lanes`: 25.3
- added `estimated_usage.per_project.EP-26687.planning_exceeds_window`: false
- added `estimated_usage.per_project.EP-26687.structural_exceeds_window`: true
- added `estimated_usage.per_project.EP-26687.structural_maximum.B`: 14
- added `estimated_usage.per_project.EP-26687.structural_maximum.C`: 69
- added `estimated_usage.per_project.EP-26687.structural_maximum.P`: 36
- added `estimated_usage.per_project.EP-26687.structural_maximum.R`: 40
- added `estimated_usage.per_project.EP-26687.structural_maximum.all_lanes`: 159
- added `estimated_usage.per_project.EP-26687.windows_needed_structural`: 3
- added `estimated_usage.per_project.EP-27331.application_rows_maximum.B_database`: 12
- added `estimated_usage.per_project.EP-27331.application_rows_maximum.C_database`: 84
- added `estimated_usage.per_project.EP-27331.application_rows_maximum.P`: 0
- added `estimated_usage.per_project.EP-27331.application_rows_maximum.R_database`: 84
- added `estimated_usage.per_project.EP-27331.application_rows_maximum.max`: 84
- added `estimated_usage.per_project.EP-27331.drawings_ai_if_enabled_all_lanes`: 170
- added `estimated_usage.per_project.EP-27331.pages_read`: 23
- added `estimated_usage.per_project.EP-27331.planning.B`: 6
- added `estimated_usage.per_project.EP-27331.planning.C`: 46
- added `estimated_usage.per_project.EP-27331.planning.P`: 6.9
- added `estimated_usage.per_project.EP-27331.planning.R`: 4.1
- added `estimated_usage.per_project.EP-27331.planning.all_lanes`: 63.0
- added `estimated_usage.per_project.EP-27331.planning_exceeds_window`: true
- added `estimated_usage.per_project.EP-27331.structural_exceeds_window`: true
- added `estimated_usage.per_project.EP-27331.structural_maximum.B`: 12
- added `estimated_usage.per_project.EP-27331.structural_maximum.C`: 72
- added `estimated_usage.per_project.EP-27331.structural_maximum.P`: 36
- added `estimated_usage.per_project.EP-27331.structural_maximum.R`: 40
- added `estimated_usage.per_project.EP-27331.structural_maximum.all_lanes`: 160
- added `estimated_usage.per_project.EP-27331.windows_needed_structural`: 3
- added `estimated_usage.per_project.EP-29255.application_rows_maximum.B_database`: 4
- added `estimated_usage.per_project.EP-29255.application_rows_maximum.C_database`: 25
- added `estimated_usage.per_project.EP-29255.application_rows_maximum.P`: 0
- added `estimated_usage.per_project.EP-29255.application_rows_maximum.R_database`: 22
- added `estimated_usage.per_project.EP-29255.application_rows_maximum.max`: 25
- added `estimated_usage.per_project.EP-29255.drawings_ai_if_enabled_all_lanes`: 74
- added `estimated_usage.per_project.EP-29255.pages_read`: 3
- added `estimated_usage.per_project.EP-29255.planning.B`: 2
- added `estimated_usage.per_project.EP-29255.planning.C`: 6
- added `estimated_usage.per_project.EP-29255.planning.P`: 0.9
- added `estimated_usage.per_project.EP-29255.planning.R`: 0.5
- added `estimated_usage.per_project.EP-29255.planning.all_lanes`: 9.4
- added `estimated_usage.per_project.EP-29255.planning_exceeds_window`: false
- added `estimated_usage.per_project.EP-29255.structural_exceeds_window`: true
- added `estimated_usage.per_project.EP-29255.structural_maximum.B`: 4
- added `estimated_usage.per_project.EP-29255.structural_maximum.C`: 21
- added `estimated_usage.per_project.EP-29255.structural_maximum.P`: 21
- added `estimated_usage.per_project.EP-29255.structural_maximum.R`: 18
- added `estimated_usage.per_project.EP-29255.structural_maximum.all_lanes`: 64
- added `estimated_usage.per_project.EP-29255.windows_needed_structural`: 2
- added `estimated_usage.per_project.EP-3563.application_rows_maximum.B_database`: 6
- added `estimated_usage.per_project.EP-3563.application_rows_maximum.C_database`: 36
- added `estimated_usage.per_project.EP-3563.application_rows_maximum.P`: 0
- added `estimated_usage.per_project.EP-3563.application_rows_maximum.R_database`: 30
- added `estimated_usage.per_project.EP-3563.application_rows_maximum.max`: 36
- added `estimated_usage.per_project.EP-3563.drawings_ai_if_enabled_all_lanes`: 100
- added `estimated_usage.per_project.EP-3563.pages_read`: 6
- added `estimated_usage.per_project.EP-3563.planning.B`: 3
- added `estimated_usage.per_project.EP-3563.planning.C`: 12
- added `estimated_usage.per_project.EP-3563.planning.P`: 1.8
- added `estimated_usage.per_project.EP-3563.planning.R`: 1.1
- added `estimated_usage.per_project.EP-3563.planning.all_lanes`: 17.9
- added `estimated_usage.per_project.EP-3563.planning_exceeds_window`: false
- added `estimated_usage.per_project.EP-3563.structural_exceeds_window`: true
- added `estimated_usage.per_project.EP-3563.structural_maximum.B`: 6
- added `estimated_usage.per_project.EP-3563.structural_maximum.C`: 30
- added `estimated_usage.per_project.EP-3563.structural_maximum.P`: 30
- added `estimated_usage.per_project.EP-3563.structural_maximum.R`: 24
- added `estimated_usage.per_project.EP-3563.structural_maximum.all_lanes`: 90
- added `estimated_usage.per_project.EP-3563.windows_needed_structural`: 2
- added `estimated_usage.per_project_note`: "replaces the superseded per-project figures (whose 'C_max' 8 per document was not a bound): planning and structural maxima of PROJECT-REQUEST-BOUN...
- added `estimated_usage.structural_maximum.by_lane.B`: 48
- added `estimated_usage.structural_maximum.by_lane.C`: 240
- added `estimated_usage.structural_maximum.by_lane.P`: 36
- added `estimated_usage.structural_maximum.by_lane.R`: 40
- added `estimated_usage.structural_maximum.by_lane_before_caps.B`: 48
- added `estimated_usage.structural_maximum.by_lane_before_caps.C`: 255
- added `estimated_usage.structural_maximum.by_lane_before_caps.P`: 171
- added `estimated_usage.structural_maximum.by_lane_before_caps.R`: 222
- added `estimated_usage.structural_maximum.note`: "one dispatch per request per invocation; retries of failed requests across resumes are not included (bounded by the lane allowances, the parent 55...
- added `estimated_usage.structural_maximum.source`: "PROJECT-REQUEST-BOUNDS.json (project-bounds-r39-2026-10-04.1)"
- added `estimated_usage.structural_maximum.total`: 364
- added `estimated_usage.tokens_at_structural_maximum_p95.B.input`: 1202736
- added `estimated_usage.tokens_at_structural_maximum_p95.B.output`: 186288
- added `estimated_usage.tokens_at_structural_maximum_p95.C.input`: 10930560
- added `estimated_usage.tokens_at_structural_maximum_p95.C.output`: 2608800
- added `estimated_usage.tokens_at_structural_maximum_p95.P.input`: 1639584
- added `estimated_usage.tokens_at_structural_maximum_p95.P.output`: 391320
- added `estimated_usage.tokens_at_structural_maximum_p95.R.input`: 1821760
- added `estimated_usage.tokens_at_structural_maximum_p95.R.output`: 434800
- added `estimated_usage.tokens_at_structural_maximum_p95.basis`: "structural maximum x the ledger's calibrated p95 of the largest task (discover_page 45,544 / 10,870; B read_submittal_form 25,057 / 3,881): a deli...
- added `estimated_usage.tokens_at_structural_maximum_p95.consequence`: "at the structural maximum with every request sized at that p95 the output total would exceed the parent / scope output bound 3,260,000: the ledger...
- added `estimated_usage.tokens_at_structural_maximum_p95.total.input`: 15594640
- added `estimated_usage.tokens_at_structural_maximum_p95.total.output`: 3621208
- added `estimated_usage.tokens_at_structural_maximum_p95.versus_parent.input_tokens`: 16300000
- added `estimated_usage.tokens_at_structural_maximum_p95.versus_parent.output_tokens`: 3260000
- removed `estimated_usage.per_project.EP-15744.B_conservative`: 0
- removed `estimated_usage.per_project.EP-15744.B_plus_C_max`: 8
- removed `estimated_usage.per_project.EP-15744.B_plus_C_planning`: 8
- removed `estimated_usage.per_project.EP-15744.C_low`: 4.5
- removed `estimated_usage.per_project.EP-15744.C_max`: 8
- removed `estimated_usage.per_project.EP-15744.C_planning`: 8
- removed `estimated_usage.per_project.EP-15744.P_max`: 1.2
- removed `estimated_usage.per_project.EP-15744.P_planning`: 1.2
- removed `estimated_usage.per_project.EP-15744.R_max`: 8
- removed `estimated_usage.per_project.EP-15744.R_planning`: 0.7
- removed `estimated_usage.per_project.EP-15744.all_lanes_conservative`: 17.2
- removed `estimated_usage.per_project.EP-15744.all_lanes_planning`: 9.9
- removed `estimated_usage.per_project.EP-15744.decision_bearing`: 0
- removed `estimated_usage.per_project.EP-15744.in_scope_pages`: 4
- removed `estimated_usage.per_project.EP-15744.pages_read_by_c`: 4
- removed `estimated_usage.per_project.EP-22349.B_conservative`: 2
- removed `estimated_usage.per_project.EP-22349.B_plus_C_max`: 42
- removed `estimated_usage.per_project.EP-22349.B_plus_C_planning`: 24
- removed `estimated_usage.per_project.EP-22349.C_low`: 22.5
- removed `estimated_usage.per_project.EP-22349.C_max`: 40
- removed `estimated_usage.per_project.EP-22349.C_planning`: 22
- removed `estimated_usage.per_project.EP-22349.P_max`: 6.0
- removed `estimated_usage.per_project.EP-22349.P_planning`: 3.3
- removed `estimated_usage.per_project.EP-22349.R_max`: 40
- removed `estimated_usage.per_project.EP-22349.R_planning`: 2.0
- removed `estimated_usage.per_project.EP-22349.all_lanes_conservative`: 88.0
- removed `estimated_usage.per_project.EP-22349.all_lanes_planning`: 29.3
- removed `estimated_usage.per_project.EP-22349.decision_bearing`: 2
- removed `estimated_usage.per_project.EP-22349.in_scope_pages`: 11
- removed `estimated_usage.per_project.EP-22349.pages_read_by_c`: 11
- removed `estimated_usage.per_project.EP-26687.B_conservative`: 3
- removed `estimated_usage.per_project.EP-26687.B_plus_C_max`: 59
- removed `estimated_usage.per_project.EP-26687.B_plus_C_planning`: 21
- removed `estimated_usage.per_project.EP-26687.C_low`: 31.5
- removed `estimated_usage.per_project.EP-26687.C_max`: 56
- removed `estimated_usage.per_project.EP-26687.C_planning`: 18
- removed `estimated_usage.per_project.EP-26687.P_max`: 8.4
- removed `estimated_usage.per_project.EP-26687.P_planning`: 2.7
- removed `estimated_usage.per_project.EP-26687.R_max`: 40
- removed `estimated_usage.per_project.EP-26687.R_planning`: 1.6
- removed `estimated_usage.per_project.EP-26687.all_lanes_conservative`: 107.4
- removed `estimated_usage.per_project.EP-26687.all_lanes_planning`: 25.3
- removed `estimated_usage.per_project.EP-26687.decision_bearing`: 3
- removed `estimated_usage.per_project.EP-26687.in_scope_pages`: 9
- removed `estimated_usage.per_project.EP-26687.pages_read_by_c`: 9
- removed `estimated_usage.per_project.EP-27331.B_conservative`: 6
- removed `estimated_usage.per_project.EP-27331.B_plus_C_max`: 54
- removed `estimated_usage.per_project.EP-27331.B_plus_C_planning`: 52
- removed `estimated_usage.per_project.EP-27331.C_low`: 27.0
- removed `estimated_usage.per_project.EP-27331.C_max`: 48
- removed `estimated_usage.per_project.EP-27331.C_planning`: 46
- removed `estimated_usage.per_project.EP-27331.P_max`: 7.2
- removed `estimated_usage.per_project.EP-27331.P_planning`: 6.9
- removed `estimated_usage.per_project.EP-27331.R_max`: 40
- removed `estimated_usage.per_project.EP-27331.R_planning`: 4.1
- removed `estimated_usage.per_project.EP-27331.all_lanes_conservative`: 101.2
- removed `estimated_usage.per_project.EP-27331.all_lanes_planning`: 63.0
- removed `estimated_usage.per_project.EP-27331.decision_bearing`: 6
- removed `estimated_usage.per_project.EP-27331.in_scope_pages`: 23
- removed `estimated_usage.per_project.EP-27331.pages_read_by_c`: 23
- removed `estimated_usage.per_project.EP-29255.B_conservative`: 2
- removed `estimated_usage.per_project.EP-29255.B_plus_C_max`: 18
- removed `estimated_usage.per_project.EP-29255.B_plus_C_planning`: 8
- removed `estimated_usage.per_project.EP-29255.C_low`: 9.0
- removed `estimated_usage.per_project.EP-29255.C_max`: 16
- removed `estimated_usage.per_project.EP-29255.C_planning`: 6
- removed `estimated_usage.per_project.EP-29255.P_max`: 2.4
- removed `estimated_usage.per_project.EP-29255.P_planning`: 0.9
- removed `estimated_usage.per_project.EP-29255.R_max`: 16
- removed `estimated_usage.per_project.EP-29255.R_planning`: 0.5
- removed `estimated_usage.per_project.EP-29255.all_lanes_conservative`: 36.4
- removed `estimated_usage.per_project.EP-29255.all_lanes_planning`: 9.4
- removed `estimated_usage.per_project.EP-29255.decision_bearing`: 2
- removed `estimated_usage.per_project.EP-29255.in_scope_pages`: 3
- removed `estimated_usage.per_project.EP-29255.pages_read_by_c`: 3
- removed `estimated_usage.per_project.EP-3563.B_conservative`: 3
- removed `estimated_usage.per_project.EP-3563.B_plus_C_max`: 27
- removed `estimated_usage.per_project.EP-3563.B_plus_C_planning`: 15
- removed `estimated_usage.per_project.EP-3563.C_low`: 13.5
- removed `estimated_usage.per_project.EP-3563.C_max`: 24
- removed `estimated_usage.per_project.EP-3563.C_planning`: 12
- removed `estimated_usage.per_project.EP-3563.P_max`: 3.6
- removed `estimated_usage.per_project.EP-3563.P_planning`: 1.8
- removed `estimated_usage.per_project.EP-3563.R_max`: 24
- removed `estimated_usage.per_project.EP-3563.R_planning`: 1.1
- removed `estimated_usage.per_project.EP-3563.all_lanes_conservative`: 54.6
- removed `estimated_usage.per_project.EP-3563.all_lanes_planning`: 17.9
- removed `estimated_usage.per_project.EP-3563.decision_bearing`: 3
- removed `estimated_usage.per_project.EP-3563.in_scope_pages`: 6
- removed `estimated_usage.per_project.EP-3563.pages_read_by_c`: 6

### `evaluator` (changed)

- changed `evaluator.judging`: "every verdict, metric, tripwire, coverage figure, control and gate comes from lane_judge_r32 + literal_compare_r32; .10 judging is never bound; pl... → "every verdict, metric, tripwire, coverage figure, control and gate comes from lane_judge_r32 (with rule CP-R38) + literal_compare_r32 of the revie...

### `forbidden_after_authorization` (changed)

- changed `forbidden_after_authorization`: ["selecting a default variant", "M2 acceptance by this run", "starting M3", "production use or production database writes", "any OneDrive change", ... → ["selecting a default variant", "M2 acceptance by this run", "starting M3", "production use or production database writes", "any OneDrive change", ...

### `gates` (changed)

- changed `gates.decision_coverage`: "completed reads + verified absences of C >= those of B and >= those of R; wrong absences and located_incomplete never count; NOT_SCORABLE rows nev... → "C_GE_B_ONLY (owner ruling A-10): completed reads + verified absences of C >= those of B on the resolved decision documents of the run set; wrong a...
- added `gates.comparison_state`: "A-09 point 1: a B or C document refused by a limit (classes limit / failure) or DEFERRED makes the comparison INCOMPLETE; it stays in every denomi...
- added `gates.decision_coverage_superseded_text`: "completed reads + verified absences of C >= those of B and >= those of R; wrong absences and located_incomplete never count; NOT_SCORABLE rows nev...
- added `gates.other_gates`: "every other safety, accuracy and completeness gate is carried verbatim from the superseded declaration (per_field, safety, request_gate, concentra...

### `harness` (changed)

- changed `harness.accepted_by`: "Verification 37 (ORCH-06C VERIFIED); H1 closed" → "Verification 40 (ORCH-08C VERIFIED; 0 blockers, 0 majors, 3 minors routed to this declaration: R40-04, R40-13, R40-16)"
- changed `harness.binding_manifest.entries`: 155 → 239
- changed `harness.binding_manifest.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/BINDING-MANIFEST-R36.json" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/BINDING-MANIFEST-R39.json"
- changed `harness.binding_manifest.sha256`: "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568" → "a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b"
- changed `harness.binding_manifest.supersedes`: "review34/BINDING-MANIFEST-R34.json 3d0f8bfe... for the harness code; every other review34 binding entry is carried unchanged" → "review38/BINDING-MANIFEST-R38.json 4c2904cd... for the harness code; carried groups re-hashed and equal"
- changed `harness.bound_code_used_as_is`: "the bound code runs unchanged from C:/t/iso/work/r2x/r36/harness-r32 (its SANDBOX_BASE C:/t/r2x/r34-sandbox); a relocated copy would be a new bind... → "the bound code runs unchanged from PILOT/review39/scripts/harness-r32: the sandbox base is DECLARED (run.sandbox_base), not a code constant, so no...
- changed `harness.concentration_rule.code.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/concentration_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/concentration_r32.py"
- changed `harness.lineage.review33.accepted_by`: "Review 34 (with corrections RC-1 to RC-6, closed by review34)" → "Review 34"
- changed `harness.modules.allowance_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/allowance_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/allowance_r32.py"
- changed `harness.modules.allowance_r32.sha256`: "803a65bbff254c567fcd7e578948c017e0cb6e19cd38d151de3da3e0e3fb1af5" → "6231b238654150cb1c193db4d7ef4319254a1ad885906ec7b6249e4459d55e19"
- changed `harness.modules.capture_store.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/capture_store.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/capture_store.py"
- changed `harness.modules.concentration_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/concentration_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/concentration_r32.py"
- changed `harness.modules.converter_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/converter_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/converter_r32.py"
- changed `harness.modules.dispatch_guard_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/dispatch_guard_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/dispatch_guard_r32.py"
- changed `harness.modules.labels_adapter_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/labels_adapter_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/labels_adapter_r32.py"
- changed `harness.modules.lane_judge_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/lane_judge_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/lane_judge_r32.py"
- changed `harness.modules.lane_judge_r32.sha256`: "a0b6b7c83262ddb2d1337d5ed17296a5aa6fa26cc6ebbee18afcb3cf48f0ca45" → "a3b0b9426fd316a10c8f48a153695502990e38707061f2888add8a919019ae70"
- changed `harness.modules.lane_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/lane_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/lane_r32.py"
- changed `harness.modules.lane_r32.sha256`: "b46f5e0b41ce0e6f046054d1072696c62c1740ccc272fb3ef7890b74d4104ed2" → "493c0a9f248a9ceeba0ab2089a86ffed1c0bc142acdde9117012960a36088e6f"
- changed `harness.modules.preflight_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/preflight_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/preflight_r32.py"
- changed `harness.modules.preflight_r32.sha256`: "011c462cf02a1d90f8bbcaa5c468aa994550031016f2055699a62b636c02f511" → "0e59dbff5e87c1f5a9df2520bc82db7cf01b7086a314a9cefb56bcff47ea442f"
- changed `harness.modules.run_set_selector_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/run_set_selector_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/run_set_selector_r32.py"
- changed `harness.modules.run_set_selector_r32.sha256`: "5c923ec85f90173b13836b04d81d6e96a6f498e4ce52a6a9a4f7e16851acba53" → "ec5025d248a190a14d8c2e128cdc8181b0708ab834ca322f62337cf7f32fc2f4"
- changed `harness.modules.runner_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/runner_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/runner_r32.py"
- changed `harness.modules.runner_r32.sha256`: "22c71319087d412bd72666add99660936c9999d2eb075ceee716d715cb9b5672" → "b290dd1c8ddda1b8d16117789f2f7691e792830e5a99e6b3b5a0963780027108"
- changed `harness.modules.sandbox_child_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/sandbox_child_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/sandbox_child_r32.py"
- changed `harness.modules.sandbox_child_r32.sha256`: "39bf11bc6a81a364f483c5668e22ebdb618f8605cb666fd9e16ae3a83d323d68" → "70684eb0a2b1a208dcf1e4e217bf039ed37cf4593b7fc1a0d63e21920cc27bba"
- changed `harness.modules.sandbox_ingest_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/sandbox_ingest_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/sandbox_ingest_r32.py"
- changed `harness.modules.sandbox_ingest_r32.sha256`: "3e0e906df9aa1d387bc8a018142e122c1c9545f54f6d2aa311718c75e45e92a6" → "8fb5c891a41bba5f86c6426fb4784ec4dd0b029cc2733893b17a23712aa56ef5"
- changed `harness.modules.score_bcr_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/score_bcr_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/score_bcr_r32.py"
- changed `harness.modules.score_bcr_r32.sha256`: "3436fe7df06ef15c0d5c0fdaabf728b6216b34909d00ef4be0a3b7eb9217fb63" → "ccfc7200ca8906bc1383986cefc44b2ca134b7de5d5cfcda0268253da20f8524"
- changed `harness.modules.score_lane_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/score_lane_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/score_lane_r32.py"
- changed `harness.modules.score_lane_r32.sha256`: "c25f4d8994631b0fe5b52c1eb4d5bb0f7227f15a4b26c671e72e9c7e31c3c915" → "33a102d04bac562add88638008cd4561347225347115a3ad647b264a8a83832c"
- changed `harness.modules.state_check.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/state_check.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/state_check.py"
- changed `harness.modules.stop_rules.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/stop_rules.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/stop_rules.py"
- changed `harness.modules.tripwire_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/tripwire_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/tripwire_r32.py"
- changed `harness.modules.tripwire_r32.sha256`: "42dc6226700852f84762bdd7759bb7592de72778fe92aaad7f7993db291f14d0" → "2a67c268ac4ac641f59d6acca5867e1419670dd885a2340d4d64af60161ca389"
- changed `harness.package`: "PILOT/review36/" → "PILOT/review39/"
- changed `harness.package_manifest.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/evidence/EVIDENCE-MANIFEST.json" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/evidence/EVIDENCE-MANIFEST.json"
- changed `harness.package_manifest.sha256`: "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0" → "2430fa2bf6bcb5bf3775efe143575dcd9cdc55723ab994cfaec5f63fbdded990"
- added `harness.contracts.change_record_r39.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/CHANGE-RECORD-R39.md"
- added `harness.contracts.change_record_r39.sha256`: "7328d242acbd9f929cb10db20d2f2a2ddc00c251787cbb3b925f9c09a6f18418"
- added `harness.contracts.drawings_ai_probe.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/DRAWINGS-AI-PROBE-R39.json"
- added `harness.contracts.drawings_ai_probe.sha256`: "19dcd79b682d40e47ba52ee29754d54d042880503d01c9c4ebc72f70852ea4b8"
- added `harness.contracts.live_run_contract_v4.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `harness.contracts.live_run_contract_v4.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `harness.contracts.model_id_evidence.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/MODEL-ID-EVIDENCE.md"
- added `harness.contracts.model_id_evidence.sha256`: "37bec20e9bfdcedfd788a5831dae37adb7013b083587a529989e8a1659d1f0fb"
- added `harness.contracts.report_template.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/REPORT-TEMPLATE.md"
- added `harness.contracts.report_template.sha256`: "da91e329d203f239b9c2155614c0e1a812d82e7727649f0866506bb2089af14d"
- added `harness.contracts.request_paths.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/REQUEST-PATHS.md"
- added `harness.contracts.request_paths.sha256`: "0359ba769e38f87e96d9d1b88c75372e8811c8653072458d71d503b6e9faa619"
- added `harness.contracts.request_paths_static.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/REQUEST-PATHS-STATIC.json"
- added `harness.contracts.request_paths_static.sha256`: "c0e6a43951d1eadc9c6602c5e05c4d2ce532d680ec7c445c9e6cf2266d14ac5b"
- added `harness.contracts.scorer_changes_v4.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/SCORER-CHANGES.md"
- added `harness.contracts.scorer_changes_v4.sha256`: "732e33b8a5d4cf8e9c6b40605e24ac65263a2130e91195f3ac1d9c09ea3914dc"
- added `harness.contracts.unread_pages_probe.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/UNREAD-PAGES-PROBE-R39.json"
- added `harness.contracts.unread_pages_probe.sha256`: "6afebf122c9ce73b815905bdaf9cceaf908d8f2f9b60e9e04ff03705f4c9769a"
- added `harness.contracts.visibility_report.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/VISIBILITY-REPORT.md"
- added `harness.contracts.visibility_report.sha256`: "481e4966b33eac4358ccfd8cc53088abc95d5125bd23450532d6aac9f74a30f8"
- added `harness.contracts.visibility_result.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/VISIBILITY-RESULT.json"
- added `harness.contracts.visibility_result.sha256`: "1811e4561ae2cd157aeb9e7b599ac094b0141743f8113fea0a0944c88638192c"
- added `harness.lineage.review34.contract_v2.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/LIVE-RUN-CONTRACT.md"
- added `harness.lineage.review34.contract_v2.sha256`: "0658e2a82b7daf9fe0d9229b6c8926f2aaf04df0c9f9e2533cf484704004b9e7"
- added `harness.lineage.review36.accepted_by`: "Verification 37"
- added `harness.lineage.review36.binding.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/BINDING-MANIFEST-R36.json"
- added `harness.lineage.review36.binding.sha256`: "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568"
- added `harness.lineage.review36.h1_whatif.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/H1-WHATIF-RESULT.json"
- added `harness.lineage.review36.h1_whatif.sha256`: "19b14ab3b23eb0be818ddb6c131a88bff116abb13ce5b7eac932313f925343aa"
- added `harness.lineage.review36.manifest.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/evidence/EVIDENCE-MANIFEST.json"
- added `harness.lineage.review36.manifest.sha256`: "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0"
- added `harness.lineage.review38.accepted_by`: "Verification 39 (with conditions; closed by review39 and Verification 40)"
- added `harness.lineage.review38.binding.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review38/BINDING-MANIFEST-R38.json"
- added `harness.lineage.review38.binding.sha256`: "4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d"
- added `harness.lineage.review38.change_record.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review38/CHANGE-RECORD.md"
- added `harness.lineage.review38.change_record.sha256`: "76915f1d834a08ae288902dc34aaafc8253039b008560b5cd61868356d7ba6d8"
- added `harness.lineage.review38.contract_v3.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review38/LIVE-RUN-CONTRACT.md"
- added `harness.lineage.review38.contract_v3.sha256`: "96230dadc80b51ae8f20e8de4d0bcbde3bbeb97110a3a2e9b177b3debe050eb3"
- added `harness.lineage.review38.manifest.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review38/evidence/EVIDENCE-MANIFEST.json"
- added `harness.lineage.review38.manifest.sha256`: "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9"
- added `harness.lineage.review38.scorer_changes_v3.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review38/SCORER-CHANGES.md"
- added `harness.lineage.review38.scorer_changes_v3.sha256`: "276c79aafd124eb7f05cce6a44d0a4ded5d8d0bf3fe7f739c2d1b6e80ad852fd"
- added `harness.modules.coverage_v4.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/coverage_v4.py"
- added `harness.modules.coverage_v4.sha256`: "e260a60975cc1cb72a021fee10303dfadb7ae5594c1d3cb026d4a77d7b2fcfad"
- added `harness.modules.drawings_ai_probe_r39.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/drawings_ai_probe_r39.py"
- added `harness.modules.drawings_ai_probe_r39.sha256`: "510ac22b5498850dd7851ea674d35f821df96d2fd4b080e787e309aac5d8da93"
- added `harness.modules.inputs_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/inputs_r32.py"
- added `harness.modules.inputs_r32.sha256`: "41309ae85a091944f53e10797c424a711a80ef106c91974a5ca2401f42a014e3"
- added `harness.modules.literal_compare_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/literal_compare_r32.py"
- added `harness.modules.literal_compare_r32.sha256`: "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"
- added `harness.modules.model_identity_r38.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/model_identity_r38.py"
- added `harness.modules.model_identity_r38.sha256`: "433d0e5afff55af94f58291c96bce3b92905b31f6d5737c26b3eb7193d811a68"
- added `harness.modules.page_relations_r38.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/page_relations_r38.py"
- added `harness.modules.page_relations_r38.sha256`: "256e1e3dd307f392eefc20d80cb8b0c42c320082a92a5438bfa0a9d64d0aee94"
- added `harness.modules.project_bounds_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/project_bounds_r32.py"
- added `harness.modules.project_bounds_r32.sha256`: "6abbf5eb04a72e55feb3883cb50730006f2caf1224c2e0edc63a23ef978c859b"
- added `harness.modules.r32_test_helpers.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/r32_test_helpers.py"
- added `harness.modules.r32_test_helpers.sha256`: "64c9ffcd341570d83e4cff272c16882dee0a6991537423bffc76ccdcfd7edf09"
- added `harness.modules.r34_scenarios.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/r34_scenarios.py"
- added `harness.modules.r34_scenarios.sha256`: "c2d52c56bf7c4119f62f851a8c8ae628dfa42a270aaa226d58c68f73e2e26fa1"
- added `harness.modules.request_paths_r39.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/request_paths_r39.py"
- added `harness.modules.request_paths_r39.sha256`: "0ee519859cca6921b57f082cd8b58b91cd429521a47ecf0f7066fd7a1950aee0"
- added `harness.modules.resume_invocations_r39.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/resume_invocations_r39.py"
- added `harness.modules.resume_invocations_r39.sha256`: "b217b053f69213e7320469584e748d2b15679ed39d4345e0e95cfce6ebf36864"
- added `harness.modules.run_control_r38.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/run_control_r38.py"
- added `harness.modules.run_control_r38.sha256`: "d30de813c1092d46e3af940a4b0e3b03b9820c2b96c28b81ca71f40981bc42d1"
- added `harness.modules.run_state_r38.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/run_state_r38.py"
- added `harness.modules.run_state_r38.sha256`: "5e789b05a23beae15195590ae0497739f87a493ea06acae3e8a798d054e653f8"
- added `harness.modules.synthetic_r32.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/synthetic_r32.py"
- added `harness.modules.synthetic_r32.sha256`: "9248cbf72e5a0033c1753bd9867591adf41de6c4ccaff9947323d16d450be65c"
- added `harness.modules.unread_pages_probe_r39.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/unread_pages_probe_r39.py"
- added `harness.modules.unread_pages_probe_r39.sha256`: "f326c362a0920e9c7f58d237d2cc41b4b5fc0525c5cb64f979f3c9166bbaf2cd"
- added `harness.modules.visibility_r38.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/visibility_r38.py"
- added `harness.modules.visibility_r38.sha256`: "4dcfff3777acbe4eb5c8ca861f3ea4e4e221f7242e21c1e47c93807c005cb156"
- added `harness.package_check.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/evidence/PACKAGE-CHECK.json"
- added `harness.package_check.sha256`: "fad730b9403db6e8ea995a47a9a6b2727c0316db982f5a0b10d05279cfb05cf1"
- added `harness.review39_snapshot_before.note`: "R40-19: review39's SNAPSHOT-BEFORE was taken at 09:55:49Z (after the code changes of 09:21-09:53Z), not 'about 10:13Z' as CHANGE-RECORD-R39 sectio...
- added `harness.review39_snapshot_before.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/evidence/SNAPSHOT-BEFORE.json"
- added `harness.review39_snapshot_before.sha256`: "e50a6222191bbffc661f92b6f39de954ae71c48ca3d653909fd38b7c8fe1efa3"
- added `harness.review39_snapshot_before.taken_utc`: "2026-10-04T09:55:49+00:00"
- added `harness.review39_work_records.AUDIT-LOG.md.original`: "C:/t/iso/work/r2x/r39/AUDIT-LOG.md"
- added `harness.review39_work_records.AUDIT-LOG.md.package_path`: "evidence/review39-work-records/AUDIT-LOG.md"
- added `harness.review39_work_records.AUDIT-LOG.md.sha256`: "62cac01271e46bbeb1fcdfe77afab6bbbe7ca7b6b79f493d090578210c9592d4"
- added `harness.review39_work_records.PROGRESS.md.original`: "C:/t/iso/work/r2x/r39/PROGRESS.md"
- added `harness.review39_work_records.PROGRESS.md.package_path`: "evidence/review39-work-records/PROGRESS.md"
- added `harness.review39_work_records.PROGRESS.md.sha256`: "e0d6066792ac5e9f4755f83a278dce7b52d37a59cf313aa4e7ee2b61a39c3107"
- added `harness.review39_work_records.why`: "R40-20: the package's audit log stops one entry short (10:19:54Z); the final work-folder AUDIT-LOG.md and PROGRESS.md are copied into this package...
- removed `harness.changed_module.literal_compare_r32.py.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/literal_compare_r32.py"
- removed `harness.changed_module.literal_compare_r32.py.replaces`: "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6"
- removed `harness.changed_module.literal_compare_r32.py.sha256`: "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"
- removed `harness.changed_module.test_literal_compare_r32.py.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/test_literal_compare_r32.py"
- removed `harness.changed_module.test_literal_compare_r32.py.sha256`: "66e0ddcf92ae4aaf350ca1143ad4f22f62ab777e12700c978652b276fdbb34c6"
- removed `harness.contracts.live_run_contract.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/LIVE-RUN-CONTRACT.md"
- removed `harness.contracts.live_run_contract.sha256`: "0658e2a82b7daf9fe0d9229b6c8926f2aaf04df0c9f9e2533cf484704004b9e7"
- removed `harness.contracts.scorer_changes.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/SCORER-CHANGES.md"
- removed `harness.contracts.scorer_changes.sha256`: "c261b5eb6ca4561e638e6c3c218fefb30d115cb871ec19e19f2c50ca8bdb642d"
- removed `harness.h1_whatif.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/H1-WHATIF-RESULT.json"
- removed `harness.h1_whatif.sha256`: "19b14ab3b23eb0be818ddb6c131a88bff116abb13ce5b7eac932313f925343aa"

### `interpretations` (changed)

- changed `interpretations.review35_item10`: ["the unlabelled '- R0n' suffix base form is accepted (8 rows)", "the (d1) tolerance, including the application's 'rejected' (7 scorable rows)", "t... → ["the unlabelled '- R0n' suffix base form is accepted (8 rows)", "the (d1) tolerance, including the application's 'rejected' (7 scorable rows)", "t...
- changed `interpretations.verification36_section6`: ["whitespace-insensitive comparison (i2); for revisions it holds after the H1 correction, except whitespace inside the prefix word (R37-04; revisio... → ["whitespace-insensitive comparison (i2); for revisions it holds after the H1 correction, except whitespace inside the prefix word (R37-04; revisio...
- added `interpretations.cross_page_rule_scope.documents_formerly_in_scope`: ["F006", "F009", "F016", "F020", "F021", "F030", "F032", "F037", "F038", "F039", "F040"]
- added `interpretations.cross_page_rule_scope.superseded`: "the .10-parity scope (11 run-set documents) is replaced by rule CP-R38, which applies to every document"
- removed `interpretations.cross_page_rule_scope.documents`: ["F006", "F009", "F016", "F020", "F021", "F030", "F032", "F037", "F038", "F039", "F040"]

### `lane_task_kinds` (added)

- added `lane_task_kinds.B`: ["read_submittal_form"]
- added `lane_task_kinds.C`: ["discover_page", "locate_decision", "read_decision", "read_field_context", "read_identity", "read_revision"]
- added `lane_task_kinds.P`: ["discover_page", "locate_decision", "read_decision", "read_field_context", "read_identity", "read_revision"]
- added `lane_task_kinds.R`: ["discover_page", "read_decision", "read_field_context", "read_identity", "read_revision"]

### `lane_task_kinds_detail` (added)

- added `lane_task_kinds_detail`: "preflight_r32.task_kinds_for(lane_switches) (REQUEST-PATHS.md): B the baseline form read only; C the candidate evidence reader's kinds under C's s...

### `lanes` (changed)

- changed `lanes.P.meaning`: "the variation probe: a seeded 15 % of C's answered dispatches (seed m2-r30-variation-2026-10-02) re-sent once in lane P" → "the variation probe: a seeded 15 % (seed m2-r30-variation-2026-10-02) of C's answered dispatches AS DRAWN AT P's FIRST RUN, re-sent once in lane P...
- changed `lanes.P.role`: "reported only; never served to B or C; never a score" → "reported only; never served to B or C; never a score; no credit (A-09 point 7)"
- changed `lanes.R.role`: "offline contrast only; never a gate input except decision coverage C >= R; never a live stop (a resolved-truth critical in R is a reference finding)" → "offline contrast only; R earns NO accuracy or recovery credit (A-09 point 7); it never determines eligibility: the C >= R decision coverage contra...
- added `lanes.B.drawings_ai_review`: "switched off by application_env in every lane (REQUEST-PATHS.md; Verification 40 R40-03)"
- added `lanes.B.task_kinds`: ["read_submittal_form"]
- added `lanes.C.task_kinds`: ["discover_page", "locate_decision", "read_decision", "read_field_context", "read_identity", "read_revision"]
- added `lanes.P.task_kinds`: ["discover_page", "locate_decision", "read_decision", "read_field_context", "read_identity", "read_revision"]
- added `lanes.R.task_kinds`: ["discover_page", "read_decision", "read_field_context", "read_identity", "read_revision"]

### `ledger` (changed)

- changed `ledger.scope`: "m2-fresh-validation-r32-2026-10-03" → "m2-fresh-validation-r32-v2-2026-10-04"

### `ledger_detail` (changed)

- changed `ledger_detail.creation`: "created only by the owner's budget authorization naming the declaration hash; new and empty, exactly these limits, closed breaker; this task creat... → "created only by the owner, with create_scope_r40.py create (SCOPE-CREATION-COMMAND.md), after the budget authorization, with the authorization fil...
- changed `ledger_detail.limits_keys`: "every key is a field of the application's ledger Limits (requests, input_tokens, output_tokens, per_request_input, per_request_output, elapsed_s);... → "every key is a field of the application's ledger Limits (requests, input_tokens, output_tokens, per_request_input, per_request_output, elapsed_s);...
- changed `ledger_detail.live_check`: "after the run the ledger may have grown only inside the declared scope (no new scope, no limit amendment, every other scope unchanged) and by at m... → "after every invocation the ledger may have grown only inside the declared scope (no new scope, no limit amendment, every other scope unchanged) an...
- changed `ledger_detail.one_scope_for_all_lanes`: "one scope serves B, C, R and P; the owner may instead order per-lane scopes, which is a new declaration (R35-10)" → "one scope serves B, C, R and P (R35-10); per-lane token and elapsed thresholds are not enforced per lane"
- added `ledger_detail.elapsed`: "the scope's elapsed_s counts from the scope's CREATION; the allowance's elapsed bound counts from the first invocation; both are bounds, the earli...
- added `ledger_detail.reconciliation`: "before every resume: allowance_r32.py audit with the ledger and scope (charges <= 556; ledger dispatch entries <= charges; every charge names its ...
- removed `ledger_detail.r35_10_consequence`: "only the request caps are per lane (the allowance); the lane token and elapsed thresholds of plan v2 section 7 are not enforced per lane, so equal...

### `model_identity` (added)

- added `model_identity.cli.path`: "claude"
- added `model_identity.cli.version`: "2.1.263 (Claude Code)"
- added `model_identity.models.small`: "claude-sonnet-5"
- added `model_identity.models.standard`: "claude-opus-5"
- added `model_identity.provider`: "claude-code"

### `model_identity_detail` (added)

- added `model_identity_detail.cli.embedded_version`: "2.1.263"
- added `model_identity_detail.cli.file`: "C:/Users/moham/AppData/Local/Microsoft/WinGet/Packages/Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe/claude.exe"
- added `model_identity_detail.cli.file_bytes`: 218746016
- added `model_identity_detail.cli.file_sha256`: "0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03"
- added `model_identity_detail.cli.path_setting`: "claude (AI_CLAUDE_CLI; resolved on PATH to the WinGet package file below; the owner confirms with `where claude`)"
- added `model_identity_detail.cli.rule`: "the runner records `claude --version` before any lane of every invocation (CLI-VERSIONS.jsonl, PROVIDER-IDENTITY.json) and refuses an invocation w...
- added `model_identity_detail.cli.version_pinned`: "2.1.263 (Claude Code)"
- added `model_identity_detail.evidence.json.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/MODEL-ID-EVIDENCE.json"
- added `model_identity_detail.evidence.json.sha256`: "d466bb9966a76aa3962f93507c60c665a47b7b8e5d21a96c61d85b92c520371e"
- added `model_identity_detail.evidence.md.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/MODEL-ID-EVIDENCE.md"
- added `model_identity_detail.evidence.md.sha256`: "37bec20e9bfdcedfd788a5831dae37adb7013b083587a529989e8a1659d1f0fb"
- added `model_identity_detail.pins`: "full ids, no aliases (A-09 point 2): AI_MODEL_SMALL claude-sonnet-5 (every B, C and R read), AI_MODEL_STANDARD claude-opus-5 (EV2 escalations only...
- added `model_identity_detail.probe`: "the owner's probe is RUNBOOK section 1 (Verification 40 section 6, amended per R40-16): not run by this task; its request count cannot be verified...
- added `model_identity_detail.runtime_check`: "fail-closed under the declared INVALID rule: every response's reported model and provider are compared with the pins (IdentityGuard); a mismatch w...
- added `model_identity_detail.runtime_check_limits`: ["limit 1: it compares what the CLI reports, which in json mode is the REQUESTED id: it verifies the CLI's resolution of --model and the absence of...
- added `model_identity_detail.served_model_identity`: "UNRESOLVED"
- added `model_identity_detail.unresolved_statement`: "MODEL-ID-EVIDENCE (review39; reproduced by Verification 40 R40-17): claude-sonnet-5 and claude-opus-5 are catalog ids that the CLI passes unchange...

### `name` (changed)

- changed `name`: "M2 fresh validation R32: accepted baseline B vs Review 29 combined candidate C, with reference R and variation probe P" → "M2 fresh validation R32, corrected declaration v2: accepted baseline B vs Review 29 combined candidate C, with reference R and variation probe P"

### `probe_population` (added)

- added `probe_population.cap`: 36
- added `probe_population.definition`: "P's population is C's ANSWERED dispatches AS DRAWN AT P's FIRST RUN: the seeded 15 % sample (seed m2-r30-variation-2026-10-02) is drawn once, when...
- added `probe_population.diagnostic`: "P earns no credit; when P cannot complete its frozen sample its diagnostic is INCOMPLETE"
- added `probe_population.example`: "Verification 40 T7: P drew 3 of C's 20 answered dispatches at its first run; after C's retries C had 25, where an unfrozen draw would give 4 of 25...
- added `probe_population.rate`: 0.15
- added `probe_population.seed`: "m2-r30-variation-2026-10-02"
- added `probe_population.why`: "a necessary consequence of the failed-read retry rule (review39 change 4): without the freeze, a resume that re-runs C after P would redraw P's sa...

### `project_day_limit` (removed)

- removed `project_day_limit`: 60

### `project_day_limit_detail` (removed)

- removed `project_day_limit_detail.incomplete_risk`: ["a B or C request refused by the day limit is a budget stop of that lane and makes the comparison INCOMPLETE; for EP-27331 that needs B's EP-27331...
- removed `project_day_limit_detail.justification`: ["60 is the largest value the frozen preflight accepts and equals plan v2 section 7 and the application's own ai_max_calls_per_project_per_day", "a...
- removed `project_day_limit_detail.owner_alternative`: "accept this risk with the authorization, or order a harness change (a higher ceiling or a refusal retryable after the UTC day changes) with re-fre...
- removed `project_day_limit_detail.range_allowed_by_preflight`: "1..60"
- removed `project_day_limit_detail.value`: 60

### `project_request_bounds` (added)

- added `project_request_bounds.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/PROJECT-REQUEST-BOUNDS.json"
- added `project_request_bounds.sha256`: "99be01fbf25ed6e6219cc6b09b56aa9cd728ad9b30379e6b4b157aa394131721"

### `project_request_bounds_detail` (added)

- added `project_request_bounds_detail.EP-27331.drawings_ai_enabled_alternative`: 170
- added `project_request_bounds_detail.EP-27331.note`: "structural 160, not 154: B's reconcile repeat of a failed form read is dispatched again (review39 change 4), so B is bounded at 2 per document per...
- added `project_request_bounds_detail.EP-27331.planning`: 63.0
- added `project_request_bounds_detail.EP-27331.structural`: 160
- added `project_request_bounds_detail.EP-27331.structural_by_lane.B`: 12
- added `project_request_bounds_detail.EP-27331.structural_by_lane.C`: 72
- added `project_request_bounds_detail.EP-27331.structural_by_lane.P`: 36
- added `project_request_bounds_detail.EP-27331.structural_by_lane.R`: 40
- added `project_request_bounds_detail.EP-27331.windows_needed_structural`: 3
- added `project_request_bounds_detail.all_projects_planning.EP-15744`: 9.9
- added `project_request_bounds_detail.all_projects_planning.EP-22349`: 29.3
- added `project_request_bounds_detail.all_projects_planning.EP-26687`: 25.3
- added `project_request_bounds_detail.all_projects_planning.EP-27331`: 63.0
- added `project_request_bounds_detail.all_projects_planning.EP-29255`: 9.4
- added `project_request_bounds_detail.all_projects_planning.EP-3563`: 17.9
- added `project_request_bounds_detail.all_projects_structural.EP-15744`: 38
- added `project_request_bounds_detail.all_projects_structural.EP-22349`: 137
- added `project_request_bounds_detail.all_projects_structural.EP-26687`: 159
- added `project_request_bounds_detail.all_projects_structural.EP-27331`: 160
- added `project_request_bounds_detail.all_projects_structural.EP-29255`: 64
- added `project_request_bounds_detail.all_projects_structural.EP-3563`: 90
- added `project_request_bounds_detail.recomputed_by`: "the live preflight (verify_bounds) and every live lane; a difference refuses the run"
- added `project_request_bounds_detail.required_application_minimum.AI_MAX_CALLS_PER_PROJECT_PER_DAY`: 84
- added `project_request_bounds_detail.required_application_minimum.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY`: 84
- added `project_request_bounds_detail.retries_across_resumes`: "not in the totals: a resume dispatches again every fingerprint whose dispatches all failed (ORCH-08C, R39-16), each a new charge counted by the wi...
- added `project_request_bounds_detail.version`: "project-bounds-r39-2026-10-04.1"

### `project_window` (added)

- added `project_window.limit`: 60
- added `project_window.window_s`: 86400

### `project_window_detail` (added)

- added `project_window_detail.a_refusal_is_a_deferral`: "a request the window would exceed is never charged and never permanent: the document is DEFERRED with retry_at_earliest and retry_at_full {plannin...
- added `project_window_detail.replaces`: "the superseded project_day_limit 60 per UTC day and project_day_limit_detail: a day-limit refusal was permanent for the run (R35-09); the rolling ...
- added `project_window_detail.rule`: "the harness per-project ROLLING-window limit: at most 60 charges per project within any 86,400 s, counted over ALL lanes (the probe lane is attrib...
- added `project_window_detail.value_basis`: "60 is the largest value contract 4 accepts and equals plan v2 section 7; PROJECT-REQUEST-BOUNDS.json was computed for exactly this window"

### `provider` (changed)

- changed `provider.environment_keys`: "the ten required keys plus the application's own AI limits, all strings, all verified by every live lane (provider_env)" → "the ten required keys plus the application's own AI limits, all strings, integer strings for every count and time limit, all verified by every liv...
- changed `provider.owner_confirmable.AI_EFFORT`: "declared 'low' (the tree default; the four-arm declaration bound no effort, so its tree default 'low' applied); the claude-code adapter passes no ... → "declared 'low' (the tree default); the claude-code adapter sends no effort flag, so it does not change a request"
- changed `provider.owner_confirmable.AI_MODEL_SMALL`: "declared 'sonnet' (the four-arm alias; recorded as claude-sonnet-5); alternatives: the full id 'claude-sonnet-5' (pins the model if the alias move... → "declared 'claude-sonnet-5' (full id, A-09 point 2; the four-arm alias 'sonnet' was recorded as claude-sonnet-5)"
- changed `provider.owner_confirmable.AI_MODEL_STANDARD`: "declared 'opus' (recorded as claude-opus-5; used only for escalations, at most 2 per document); alternatives: 'claude-opus-5', or the tree default... → "declared 'claude-opus-5' (full id; EV2 escalations only, not reached under EV1)"
- changed `provider.owner_confirmable.ledger.scope`: "declared 'm2-fresh-validation-r32-2026-10-03' (a new name; no scope of that name exists)" → "declared 'm2-fresh-validation-r32-v2-2026-10-04' (a new name; no scope of that name exists)"
- changed `provider.proposed_vs_tree_defaults.AI_MODEL_SMALL.declared`: "sonnet" → "claude-sonnet-5"
- changed `provider.proposed_vs_tree_defaults.AI_MODEL_STANDARD.declared`: "opus" → "claude-opus-5"
- added `provider.owner_confirmable.AI_MAX_CALLS_PER_PROJECT_PER_DAY`: "declared '96' (application_ai_limits.compatible_limits)"
- added `provider.owner_confirmable.cli_version`: "pinned '2.1.263 (Claude Code)'"
- removed `provider.owner_confirmable.project_day_limit`: "declared 60 (project_day_limit_detail)"

### `provider_env` (changed)

- changed `provider_env.AI_LEDGER_SCOPE`: "m2-fresh-validation-r32-2026-10-03" → "m2-fresh-validation-r32-v2-2026-10-04"
- changed `provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY`: "60" → "96"
- changed `provider_env.AI_MAX_ELAPSED_S_PER_JOB`: "120.0" → "120"
- changed `provider_env.AI_MODEL_SMALL`: "sonnet" → "claude-sonnet-5"
- changed `provider_env.AI_MODEL_STANDARD`: "opus" → "claude-opus-5"
- changed `provider_env.AI_PRICE_CACHED_INPUT_PER_MILLION`: "0.0" → "0"
- changed `provider_env.AI_PRICE_INPUT_PER_MILLION`: "0.0" → "0"
- changed `provider_env.AI_PRICE_OUTPUT_PER_MILLION`: "0.0" → "0"
- changed `provider_env.AI_READ_MAX_ELAPSED_S`: "1800.0" → "1800"

### `r_and_p` (added)

- added `r_and_p.credit`: "none (A-09 point 7): R and P earn no accuracy or recovery credit anywhere and never select a default; the candidate outcome reads only B and C"
- added `r_and_p.diagnostic_incomplete`: "when truncation (a lane stop, a refusal, a deferral, a lane that never started) prevents R from completing its declared diagnostic population (the...

### `request_path_coverage` (added)

- added `request_path_coverage.corrected_claim`: "review39's REQUEST-PATHS.md section 4 and CHANGE-RECORD-R39 section 7 say the runtime gate refuses any undeclared request 'that a missed static ed...
- added `request_path_coverage.coverage_for_C_R_P`: "C, R and P rest on proof under the declared switches: no get_provider() call is reachable on their path -- two static analyses (review39 request_p...
- added `request_path_coverage.finding`: "Verification 40 R40-04 (minor)"
- added `request_path_coverage.lane_B`: "lane B's belt and braces holds: the chain is the global provider, so any request reaches the gate (undeclared kind or missing context: contract br...
- added `request_path_coverage.owner_options`: ["(1) accept the proof-based coverage for C, R and P with the residual risk as stated (no harness change; this declaration as frozen)", "(2) order ...
- added `request_path_coverage.proof_bound.PATHS-MINE-R40.json.original`: "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40/out/PATHS-MINE-R40.json"
- added `request_path_coverage.proof_bound.PATHS-MINE-R40.json.package_path`: "evidence/r40-04-proof/PATHS-MINE-R40.json"
- added `request_path_coverage.proof_bound.PATHS-MINE-R40.json.sha256`: "8f7f768e21b4ad3d8d6a042f9be03293c13810bc286b0ade05a530a78e1b1978"
- added `request_path_coverage.proof_bound.PATHS-MINE-R40.json.verification40_recorded`: "INDEPENDENT-PACKAGE-CHECK.json raw_outputs_sha256['out/PATHS-MINE-R40.json']"
- added `request_path_coverage.proof_bound.PATHS-WHY-R40.json.original`: "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40/out/PATHS-WHY-R40.json"
- added `request_path_coverage.proof_bound.PATHS-WHY-R40.json.package_path`: "evidence/r40-04-proof/PATHS-WHY-R40.json"
- added `request_path_coverage.proof_bound.PATHS-WHY-R40.json.sha256`: "63f65a294f52fed5d596694567847e9af1203bfa8fc2b99734f2f3f2a8021af2"
- added `request_path_coverage.proof_bound.PATHS-WHY-R40.json.verification40_recorded`: "INDEPENDENT-PACKAGE-CHECK.json raw_outputs_sha256['out/PATHS-WHY-R40.json']"
- added `request_path_coverage.proof_bound.UNREAD-R40.json.original`: "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40/out/UNREAD-R40.json"
- added `request_path_coverage.proof_bound.UNREAD-R40.json.package_path`: "evidence/r40-04-proof/UNREAD-R40.json"
- added `request_path_coverage.proof_bound.UNREAD-R40.json.sha256`: "1cd15c8e90611efecc2186c7ebb325aef96499ce76b9d421bb683344bd8f145b"
- added `request_path_coverage.proof_bound.UNREAD-R40.json.verification40_recorded`: "INDEPENDENT-PACKAGE-CHECK.json raw_outputs_sha256['out/UNREAD-R40.json']"
- added `request_path_coverage.proof_bound.paths_mine_r40.py.original`: "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40/scripts/paths_mine_r40...
- added `request_path_coverage.proof_bound.paths_mine_r40.py.package_path`: "evidence/r40-04-proof/paths_mine_r40.py"
- added `request_path_coverage.proof_bound.paths_mine_r40.py.sha256`: "fedca26bf00ac8e5a16043a6dbea1c2b92a3af9d501fabc1b909a39e43bf741e"
- added `request_path_coverage.proof_bound.paths_mine_r40.py.verification40_recorded`: "INDEPENDENT-PACKAGE-CHECK.json scripts_sha256['scripts/paths_mine_r40.py']"
- added `request_path_coverage.proof_bound.paths_why_r40.py.original`: "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40/scripts/paths_why_r40.py"
- added `request_path_coverage.proof_bound.paths_why_r40.py.package_path`: "evidence/r40-04-proof/paths_why_r40.py"
- added `request_path_coverage.proof_bound.paths_why_r40.py.sha256`: "cd4fa3217b52c95674a6c809ab985edc6a146e0864fba6c421bfdd0db5b89559"
- added `request_path_coverage.proof_bound.paths_why_r40.py.verification40_recorded`: "INDEPENDENT-PACKAGE-CHECK.json scripts_sha256['scripts/paths_why_r40.py']"
- added `request_path_coverage.proof_bound.request_paths_static.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/REQUEST-PATHS-STATIC.json"
- added `request_path_coverage.proof_bound.request_paths_static.sha256`: "c0e6a43951d1eadc9c6602c5e05c4d2ce532d680ec7c445c9e6cf2266d14ac5b"
- added `request_path_coverage.proof_bound.unread_r40.py.original`: "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40/scripts/unread_r40.py"
- added `request_path_coverage.proof_bound.unread_r40.py.package_path`: "evidence/r40-04-proof/unread_r40.py"
- added `request_path_coverage.proof_bound.unread_r40.py.sha256`: "baecb0376091b7bd866e2f6d2f6cec06ef31df92381fb84f0a4262d32a002da1"
- added `request_path_coverage.proof_bound.unread_r40.py.verification40_recorded`: "INDEPENDENT-PACKAGE-CHECK.json scripts_sha256['scripts/unread_r40.py']"
- added `request_path_coverage.proof_bound.verification40_package_check.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-40/INDEPENDENT-PACKAGE-CHECK...
- added `request_path_coverage.proof_bound.verification40_package_check.sha256`: "51222ad53fd3bf42a205ac0dc9c9e3f6bd5d65b0251fab1815b31c9216667c99"
- added `request_path_coverage.residual_risk`: "stated plainly: an application path that calls get_provider() in lane C, R or P, not found by either static analysis and not exercised by the dyna...

### `resume_detail` (added)

- added `resume_detail.invocations_expected`: "2 at the planning estimate (the last starts about 24.3 h after the first), 3 at the structural maximum (about 48.5 h); every other project needs a...
- added `resume_detail.resume_invocations.EP-27331_earliest_for_comparison.planning`: [2, 4]
- added `resume_detail.resume_invocations.EP-27331_earliest_for_comparison.structural`: [3, 101]
- added `resume_detail.resume_invocations.EP-27331_full.planning_demand_63`: 2
- added `resume_detail.resume_invocations.EP-27331_full.structural_demand_160`: 3
- added `resume_detail.resume_invocations.last_invocation_starts_after_s.planning`: 87580.0
- added `resume_detail.resume_invocations.last_invocation_starts_after_s.structural`: 174760.0
- added `resume_detail.resume_invocations.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/RESUME-INVOCATIONS-R39.json"
- added `resume_detail.resume_invocations.sha256`: "9791fa897587fd83e1a087e302487ce245470a41c32f9aa10b48c1211e7dcf6b"
- added `resume_detail.resume_invocations.statement`: "each invocation after the first is a resume with its own owner authorization (one nonce per invocation); a resume before the declared policy's tim...
- added `resume_detail.resume_invocations.version`: "resume-invocations-r39-2026-10-04.1"
- added `resume_detail.rule`: "'full' (the default contract 4 offers and this declaration binds): a DEFERRED run may be resumed only at the LATEST structural-basis retry_at_full...

### `resume_policy` (added)

- added `resume_policy`: "full"

### `retry_rule` (added)

- added `retry_rule.accuracy_implication`: "B and C can obtain an answer on a retry where the stored failure was served before; results can depend on the number of invocations; the rule is i...
- added `retry_rule.budget_stops_stay_durable`: "a ledger, breaker, guard, allowance or parent refusal stops the lane durably; a resume never undoes it and refuses its retries visibly (terminal_s...
- added `retry_rule.change_from_plan_v2`: true
- added `retry_rule.now_reads`: "a resume never re-sends a request with a bound ANSWER; a fingerprint whose dispatches all FAILED is dispatched again on the application's own retr...
- added `retry_rule.plan_v2_section_4_verbatim.line`: 58
- added `retry_rule.plan_v2_section_4_verbatim.sha256`: "83c120c939c28351a7a1a70e54e9b9ab2487724aa19cdb979f16f043f2c56bfb"
- added `retry_rule.plan_v2_section_4_verbatim.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review31/REVISED-FRESH-VALIDATION-PLAN.v2.md"
- added `retry_rule.plan_v2_section_4_verbatim.text`: "A **resume** never re-sends a bound fingerprint. A reserved request without an answer is charged and served as `interrupted_charged`, as the dry r...
- added `retry_rule.statement`: "this is a CHANGE FROM PLAN V2 section 4 ('A resume never re-sends a bound fingerprint') and from review34's verbatim resume rules carried by the s...
- added `retry_rule.within_one_invocation`: "B's reconcile check repeats a failed form read: the repeat is dispatched (retry 2), attributed to its own document"

### `reviews` (changed)

- added `reviews.verification38.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-38/INDEPENDENT-VERIFICATION.md"
- added `reviews.verification38.sha256`: "006d0203aaa98a9973de140ab73ac2e127df06f827c686b1f2629c1ae607f5c7"
- added `reviews.verification38_findings.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-38/FINDINGS.json"
- added `reviews.verification38_findings.sha256`: "d432e3f5d5e8391c4dbf1f6b91b432d07d06606bd4afb9971750ca126c91d38a"
- added `reviews.verification39.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-39/INDEPENDENT-VERIFICATION.md"
- added `reviews.verification39.sha256`: "5bb967f278fd331047df3b8026432bc01ac4b678d4cc48286e50dbc6fba46598"
- added `reviews.verification39_findings.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-39/FINDINGS.json"
- added `reviews.verification39_findings.sha256`: "5976db3818000242ec32ef16323516ca29270e74027f7b10cef22fe3e2b8028a"
- added `reviews.verification40.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-40/INDEPENDENT-VERIFICATION.md"
- added `reviews.verification40.sha256`: "620ea60a63e871625c940f27ff50b2999d2403111b088275702eb68abf736cb2"
- added `reviews.verification40_findings.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-40/FINDINGS.json"
- added `reviews.verification40_findings.sha256`: "f225540849a5097fa8c27e870b2001ca593b91735832e1424c0a19ce12d86e48"
- added `reviews.verification40_package_check.path`: "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-40/INDEPENDENT-PACKAGE-CHECK...
- added `reviews.verification40_package_check.sha256`: "51222ad53fd3bf42a205ac0dc9c9e3f6bd5d65b0251fab1815b31c9216667c99"

### `revision_comparison_rule` (changed)

- changed `revision_comparison_rule.implementation.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/literal_compare_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/literal_compare_r32.py"

### `run` (changed)

- changed `run.allowance`: "C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03/allowance.sqlite" → "C:/t/r2x/r40-sandbox/r32-v2/allowance.sqlite"
- changed `run.capture_store`: "C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03/capture.sqlite" → "C:/t/r2x/r40-sandbox/r32-v2/capture.sqlite"
- changed `run.folder`: "C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03" → "C:/t/r2x/r40-sandbox/r32-v2"
- changed `run.never_moved_or_deleted`: "the run folder holds the one-run anchors (consumed nonces, allowance charges); it is never moved or deleted (R35-07)" → "the run folder holds the one-run anchors (consumed nonces, allowance charges, durable stops); it is never moved or deleted (R35-07)"
- changed `run.rule`: "one run folder, one allowance (caps and day limit bound in the file) and one capture store per declaration, all bound to the declaration sha256 (t... → "one run folder, one allowance (parent budget, lane allowances and project window bound in the file) and one capture store per declaration, all bou...
- changed `run.run_state`: "C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03/RUN-STATE.json" → "C:/t/r2x/r40-sandbox/r32-v2/RUN-STATE.json"
- changed `run.stamp`: "r32-fresh-validation-2026-10-03" → "r32-v2"
- added `run.base_justification`: ["C:/t/r2x/r40-sandbox matches the bound preflight's declared-base rule C:/t/r2x/r<NN>-sandbox; it is this task's own sandbox base, used by no test...
- added `run.sandbox_base`: "C:/t/r2x/r40-sandbox"
- removed `run.base_of_the_bound_code`: "C:/t/r2x/r34-sandbox is the SANDBOX_BASE of the bound preflight_r32 / runner_r32 (Verification 37 item 1); the folder does not exist at declaratio...

### `run_set` (changed)

- changed `run_set.frozen_by`: "this declaration (RUN-SET-RULE.md: the proposal is frozen only by the ORCH-07 declaration)" → "the ORCH-07 declaration (superseded) and again by this declaration (RUN-SET-RULE.md)"
- changed `run_set.selector.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review36/scripts/harness-r32/run_set_selector_r32.py" → "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/scripts/harness-r32/run_set_selector_r32.py"
- changed `run_set.selector.sha256`: "5c923ec85f90173b13836b04d81d6e96a6f498e4ce52a6a9a4f7e16851acba53" → "ec5025d248a190a14d8c2e128cdc8181b0708ab834ca322f62337cf7f32fc2f4"

### `schema` (changed)

- changed `schema`: "orch07-fresh-validation-declaration-r32.1" → "orch09-fresh-validation-declaration-r32-v2.1"

### `scope_limitations` (added)

- added `scope_limitations.items`: [{"declared_by": "A-09 point 5 (owner)", "found": 0, "id": "unsupported-control-shortfall", "required": 2, "statement": "the run set holds 0 of the...
- added `scope_limitations.not_claimed`: ["unsupported-format safety (no unsupported or illegible control was read)", "generalization beyond the six cohort projects, their contractors and ...
- added `scope_limitations.statement`: "A-09 point 6: the unsupported-control shortfall is a declared scope limitation, never replaced after predictions exist, never removed from a report"

### `status` (changed)

- changed `status`: "FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file and no dispatch exist; the owner's budget decision is pending" → "FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file, no run file and no dispatch exist; Verification 41 and the o...

### `stop_rules` (changed)

- changed `stop_rules.implementation`: "stop_rules.StopController (unchanged copy, 4632ffea...) replays every lane's events; the tripwire is per field (pool id, page, field)" → "run_state_r38.ControllerR38 (subclassing the unchanged stop_rules.StopController, 4632ffea...) replays every lane's events; the tripwire is per fi...
- changed `stop_rules.summary`: ["budget stops and provider-failure stops are not undone by a resume", "resume is refused after a terminal comparison (RESULT, INVALID) and after a... → ["budget stops and provider-failure stops are not undone by a resume", "a window refusal is a deferral, never charged and never permanent", "resume...
- added `stop_rules.terminal_states.CLOSED`: "a DEFERRED run whose elapsed bound passed: closed INCOMPLETE by the runner (the deferred documents listed); terminal; never resumed"
- added `stop_rules.terminal_states.DEFERRED`: "the run state of an invocation that ended with deferred documents (the project window); not terminal; resume allowed at resume_not_before (policy ...
- added `stop_rules.terminal_states.FINISHED`: "every lane complete; scored; a complete run is never resumed"
- added `stop_rules.terminal_states.INCOMPLETE`: "a B or C document refused by a limit (classes limit / failure) or still DEFERRED, a budget stop of B or C, three consecutive provider failures in ...
- added `stop_rules.terminal_states.INVALID`: "a resolved-truth critical in B, three consecutive provider failures in B, a model-identity mismatch (IDENTITY-INVALID.json), or a contract breach ...
- added `stop_rules.terminal_states.RESULT`: "a resolved-truth critical in C: C terminal, NOT ELIGIBLE; terminal; never resumed"
- added `stop_rules.verbatim_review39_resume_rules.replaces`: "the superseded declaration's verbatim review34 resume rules (review34 LIVE-RUN-CONTRACT lines 67-73), per Verification 40 R40-13"
- added `stop_rules.verbatim_review39_resume_rules.section_13.lines`: "223-241"
- added `stop_rules.verbatim_review39_resume_rules.section_13.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `stop_rules.verbatim_review39_resume_rules.section_13.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `stop_rules.verbatim_review39_resume_rules.section_13.text`: ["## 13. Failed reads and the capture store: behaviour and its accuracy implication (R39-16)", "", "- **Within one invocation.**", "  - Lane B's AI...
- added `stop_rules.verbatim_review39_resume_rules.section_4.lines`: "68-91"
- added `stop_rules.verbatim_review39_resume_rules.section_4.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `stop_rules.verbatim_review39_resume_rules.section_4.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `stop_rules.verbatim_review39_resume_rules.section_4.text`: ["## 4. One run folder, one parent budget, one capture store", "", "The folder layout is the same as version 3, section 4. `capture.sqlite` gains t...
- added `stop_rules.verbatim_review39_resume_rules.section_5.lines`: "93-115"
- added `stop_rules.verbatim_review39_resume_rules.section_5.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `stop_rules.verbatim_review39_resume_rules.section_5.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `stop_rules.verbatim_review39_resume_rules.section_5.text`: ["## 5. The project rolling window, deferral and resume (A-09; R39-08)", "", "- **The window (unchanged).** It counts the charges of every lane for...
- added `stop_rules.verbatim_review39_resume_rules.section_6.lines`: "117-152"
- added `stop_rules.verbatim_review39_resume_rules.section_6.sha256`: "d563d41767d0bebf73b464145dc55226c9708725d48df3e580790968c2f2b2af"
- added `stop_rules.verbatim_review39_resume_rules.section_6.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39/LIVE-RUN-CONTRACT.md"
- added `stop_rules.verbatim_review39_resume_rules.section_6.text`: ["## 6. Visibility: every event is recorded per document and page", "", "- **Where (unchanged).**", "  - Lane rows: `LANE-<lane>.json` `limit_event...
- removed `stop_rules.verbatim_review34_resume_rules.lines`: "67-73"
- removed `stop_rules.verbatim_review34_resume_rules.sha256`: "0658e2a82b7daf9fe0d9229b6c8926f2aaf04df0c9f9e2533cf484704004b9e7"
- removed `stop_rules.verbatim_review34_resume_rules.source`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/LIVE-RUN-CONTRACT.md"
- removed `stop_rules.verbatim_review34_resume_rules.text`: ["- **run** refuses when the run folder exists (\"a second fresh invocation is refused; use resume\").", "- **resume** requires the same run key, s...

### `supersedes` (added)

- added `supersedes.declaration.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json"
- added `supersedes.declaration.sha256`: "38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0"
- added `supersedes.differences`: "DECLARATION-DIFF.md and DECLARATION-DIFF.json in this package list every difference"
- added `supersedes.manifest.path`: "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/declaration-r32/evidence/EVIDENCE-MANIFEST.json"
- added `supersedes.manifest.sha256`: "59361b9331cf3d28979129dfa1749b10f345e5ad24f26b9691012423fd1be2c8"
- added `supersedes.status`: "superseded by owner decision A-09 (2026-10-03): never authorized, never run, never to be run"
- added `supersedes.structure`: "the superseded declaration's structure and numbers are kept wherever A-09, A-10 and Verification 40 do not change them"

### `task` (changed)

- changed `task`: "ORCH-07 (orchestrator ledger ORCH-016), implementation agent R37DECL-IMPL, Claude Opus 5.5 (claude-opus-5-5), effort High" → "ORCH-09 (orchestrator ledger ORCH-024), implementation agent R40DECL-IMPL, Claude Opus 5.5 (claude-opus-5-5, self-reported), effort High"

### `token_thresholds` (changed)

- changed `token_thresholds.enforced`: "only the single scope's totals input_tokens 16,300,000 and output_tokens 3,260,000 (the sum of the lane thresholds) and the per-request thresholds... → "the parent budget's input 16,300,000 / output 3,260,000 tokens by the allowance on the provider-reported usage of every settled charge (parent_inp...
- added `token_thresholds.breaker_margins`: "Verification 38 R38-13: the largest actual per-request usage in the AI ledger is input 81,625 and 70,264 and output 19,568 against the declared 90...

### `trees` (changed)

- added `trees.baseline.config_py.path`: "C:/t/iso/frozen-r12/backend/app/core/config.py"
- added `trees.baseline.config_py.sha256`: "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155"
- added `trees.candidate.ledger_py.path`: "C:/t/iso/cand-r29/backend/app/ai/ledger.py"
- added `trees.candidate.ledger_py.sha256`: "d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca"
- added `trees.candidate.provider_py.path`: "C:/t/iso/cand-r29/backend/app/ai/provider.py"
- added `trees.candidate.provider_py.sha256`: "d465961efb07b7f9df2597b37a228735238af433d950bf7095925e8cc43eb5ba"

### `unread_page_rule` (added)

- added `unread_page_rule.acknowledgement_R40_15`: "documents with application-internal page limits are COMPLETE with unread pages (ORCH-021's interpretation of A-09 point 1, made by the orchestrato...
- added `unread_page_rule.no_trigger_exclusion`: "pages whose outcome is 'no_trigger' (the reader's own trigger rule: the page was never meant to be read) are NOT listed as unread pages; they stay...
- added `unread_page_rule.rule`: "A-09 point 1 as read by ORCH-021: harness and resource refusals (lane allowance, parent ceiling / tokens / elapsed, window, breaker, ledger, guard...
- added `unread_page_rule.unguarded_corners`: ["R40-10 (a): if evidence_stage stores no new attempt for a document (its own skip when row.sha256 is missing or row.extracted is not a dict, or a ...

### `verification40_items` (added)

- added `verification40_items.R40-04`: "request_path_coverage (claim corrected, proof bound, residual risk, owner options)"
- added `verification40_items.R40-08`: "application_ai_limits.integer_strings; the R39-18 risk in disclosures and RUNBOOK section 6"
- added `verification40_items.R40-10`: "unread_page_rule.no_trigger_exclusion and unread_page_rule.unguarded_corners"
- added `verification40_items.R40-12`: "probe_population"
- added `verification40_items.R40-13`: "retry_rule (a change from plan v2 section 4) and stop_rules.verbatim_review39_resume_rules (replacing review34's)"
- added `verification40_items.R40-15`: "unread_page_rule.acknowledgement_R40_15"
- added `verification40_items.R40-16`: "model_identity_detail.probe and RUNBOOK section 1 (amended probe; the request count cannot be verified offline)"
- added `verification40_items.R40-19`: "harness.review39_snapshot_before (09:55:49Z)"
- added `verification40_items.R40-20`: "harness.review39_work_records (copied and bound by hash)"
