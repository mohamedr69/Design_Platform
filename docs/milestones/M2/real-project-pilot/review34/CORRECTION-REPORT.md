# Correction report: review34 (ORCH-05C). Concentration rule v2, candidate-level outcome, pinned one-run dispatch guard, per-declaration allowance and resume

| | |
|---|---|
| **Task** | ORCH-05C (NEXT-BOUNDED-TASK, ledger ORCH-010), agent label R34HARNESS-IMPL |
| **Agent** | Claude Opus 5.5 (`claude-opus-5-5`), effort High, self-reported from its system context. A fresh, isolated agent and the only write-capable agent running. Not the ORCH-05 implementer and not the Review 34 reviewer |
| **Authorities** | A-03, A-05 (concentration rule) and A-08 (authorized sequence); A-06 eligibility limits unchanged |
| **Date** | 2026-10-03 |
| **Answers** | Independent Review 34 (`INDEPENDENT-REVIEW.md` `75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47`, `FINDINGS.json` `af99a772cafac9ef24be67902e6769fb92f544be76df3ed2f25969c1642f9fd8`): required corrections **RC-1 to RC-6** (findings R34-01, R34-02, R34-03, R34-04, R34-05, R34-08) |
| **Base** | review33 (manifest `c5001c95…5919`, 112 files; binding `d1a8a401…936e`, 68 files), re-verified before acting |
| **Binding** | `BINDING-MANIFEST-R34.json`, sha256 `3d0f8bfe37d55a4c0490e054c0d710f4bb1d2ac839dffd08daaafca19063ea27`, 118 files |
| **Approval** | Nothing here is self-approved. The package goes to Independent Review 35 (ORCH-05R2) |
| **Reference set** | `r32-labels-reviewed-2` (`89c60e9d…b9a6`): independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01) |

## 1. Index

| File | What it is |
|---|---|
| `CORRECTION-REPORT.md` | This file: index, the finding each change answers, the item-13 rulings carried, the declaration list carried forward, statuses |
| `CONCENTRATION-RULE-R32.md` | Version 2 of the rule (`concentration-r32-2026-10-03.2`): the rule, the stratified-bootstrap justification, Review 34's scenarios, the change record from version 1 |
| `SCORER-CHANGES.md` | Differences from review31 (19 rows) and from review33 |
| `LIVE-RUN-CONTRACT.md` | What a live run requires: the declaration contract, the pinned one-run authorization, the run folder and resume, the ledger behaviour, the lane verification |
| `DRY-RUN-REPORT.md`, `dry-run/` | The dry run: ingestion of 72, the two-invocation drill, the guard check, the scorer scenarios, the ledger before and after |
| `BINDING-MANIFEST-R34.json` | The binding: frozen inputs, Review 34, the review33 manifest and binding, review31's harness, the review33 harness base, the review34 harness and tests, the carried files and the run set; the unchanged / changed / new module tables |
| `RUN-SET-PROPOSAL.json`, `LABELS-R32-EVAL-INPUT.json`, `CONVERTER-RECONCILIATION.json`, `ADAPTER-CONTRACT.md`, `RUN-SET-RULE.md`, `dry-run/TRUTH-R32.json` | **Carried unchanged** from review33 (byte-identical; hashes in §4) |
| `scripts/harness-r32/` | The harness (40 files), byte-identical to the bound work copy `C:/t/iso/work/r2x/r34/harness-r32/` |
| `scripts/*.py` | Preflight, binding, dry run, tests, package check, manifest and response append |
| `tests/*.xml` | junit, one file per module: 16 files, 245 tests, 0 failures, 0 errors |
| `COMMANDS.md`, `COMMANDS-AND-AUDIT-LOG.md` | How to re-run everything; every command in UTC |
| `evidence/PACKAGE-CHECK.json`, `evidence/EVIDENCE-MANIFEST.json` | The package checker's result; the manifest, written last |

## 2. The corrections and the finding each answers

| RC | Finding | Change | Tests (junit file: tests) |
|---|---|---|---|
| **RC-1** | **R34-01** (blocker) | `concentration_r32.py` version 2 (`concentration-r32-2026-10-03.2`, `CONCENTRATION-RULE-R32.md` v2): a **positive net gain is NEVER ELIGIBLE while more than half of it comes from one project, one contractor or one layout key, at any size**; the net-gain-of-4 floor is removed from those three legs; the negative-control leg (threshold 0) and the failure-concentration leg are kept; UNDETERMINED only when the net gain is 0 or negative and decided after every NOT ELIGIBLE leg; the refuted §4 justification is replaced by one based on the scorer's project-stratified bootstrap; change record from version 1 | `test_concentration_r32`: `test_version_two_has_no_net_gain_floor`, `test_a_gain_inside_one_project_is_never_eligible_at_any_size[1-4]`, `test_a_net_gain_of_one_is_always_concentrated`, `test_a_small_gain_spread_over_projects_and_layouts_is_eligible`, `test_exactly_half_is_not_concentrated`, `test_layout_leg_…`, `test_contractor_leg_…`, `test_undetermined_only_when_there_is_no_gain`, `test_undetermined_never_turns_not_eligible_into_eligible`, `test_monotonic_adding_a_gain_to_the_dominant_group_never_makes_it_eligible`, `test_monotonic_on_the_real_run_set_ep27331_decision_gain_of_every_size`, **`test_s3a_…`, `test_s3b_decision_gain_of_three_on_f037_f009_f032_of_ep27331_is_not_eligible`, `test_s3c_…`**; `test_score_bcr_r32`: `test_the_project_stratified_bootstrap_excludes_zero_for_a_gain_concentrated_in_one_project[3]`, `test_version_one_floor_rested_on_an_unstratified_bootstrap_that_the_scorer_does_not_use`, `test_s3b_and_s3c_concentrated_decision_gains_make_the_candidate_not_eligible`. **All pass** |
| **RC-2** | **R34-02** (major) | `score_bcr_r32.py`: one candidate-level outcome `result["outcome"]` (and `result["candidate"]`): ELIGIBLE FOR A SEPARATE SELECTION DECISION only when all three fields are ELIGIBLE; otherwise the precedence INVALID > NOT ELIGIBLE > INCOMPLETE over the field outcomes (a PREPARATION BLOCKED / NOT DISPATCHABLE comparison state is the outcome); fields reported individually as diagnostics; no default ever selected | `test_score_bcr_r32`: `test_field_outcomes_are_diagnostics_and_the_candidate_outcome_is_conjunctive`, `test_candidate_precedence_invalid_over_not_eligible_over_incomplete[6]`, **`test_s5_decision_recovery_0_7576_makes_the_candidate_not_eligible`**, `test_s4b_incomplete_and_spread_gain_reach_their_candidate_outcomes`, `test_stop_states_override_every_field`, `test_population_gate_extends_then_blocks_…`, `test_all_good_and_spread_gain_is_eligible_for_every_field_and_the_candidate_…`. **All pass** |
| **RC-3** | **R34-03** (major) | `dispatch_guard_r32.py`, `runner_r32.py`, `lane_r32.py`, new `preflight_r32.py`: in live mode the authorization path is **pinned** to `<declaration folder>/OWNER-DISPATCH-AUTHORIZATION.json` (no `--auth-path`, a configured `auth_path` is refused, the declaration must bind the pinned path); the authorization must carry the declaration hash, the owner token **digest** the declaration binds (the token is presented at run time in `R34_OWNER_DISPATCH_TOKEN` and never stored), `authorized_by: "owner"` and a **one-run nonce** that the runner consumes on first use into an `O_EXCL` run-bound record holding the authorization's own hash (reuse refused; each invocation needs its own nonce); a **direct** `lane_r32.py` live invocation runs the same preflight and the same guard | `test_dispatch_guard_r32` (15): `test_wrong_path_bound_by_the_declaration_is_refused`, `test_the_authorization_path_is_pinned_and_cannot_be_given`, `test_missing_declaration_hash_is_refused`, `test_a_different_declaration_hash_is_refused`, `test_wrong_digest_is_refused`, `test_a_missing_or_wrong_owner_token_is_refused`, `test_not_the_owner_or_no_nonce_is_refused[3]`, `test_consumed_nonce_is_refused_and_lanes_need_their_own_invocation`, `test_the_guarded_provider_…[2]`, `test_a_dry_exercise_declaration_never_authorizes`; `test_runner_r32`: `test_there_is_no_auth_path_argument[dry, live]`, `test_live_mode_with_a_complete_declaration_and_no_authorization_refuses_before_any_folder_exists`, **`test_a_direct_live_lane_invocation_is_refused_by_the_guard_without_authorization`**, `test_a_direct_live_lane_with_a_configuration_or_environment_unlike_the_declaration_is_refused[7]`, `test_no_authorization_file_was_written_by_the_tests`. **All pass. No authorization file was created** (in-memory objects and a monkeypatched loader only) |
| **RC-4** | **R34-04** (major) | `allowance_r32.py`, `runner_r32.py`, `preflight_r32.py`: **one** durable allowance (lane caps 240/240/40/36 and the project-day counter, 60 per project per UTC day across all lanes) and **one** capture store per declaration, both bound to the declaration hash (`r34_binding` tables; caps and day limit stored in the file), in **one** declared run folder `C:/t/r2x/r34-sandbox/<stamp>`; `runner_r32 run` (first invocation only; a second fresh invocation is refused) and `runner_r32 resume` (same stamp: re-opens the same allowance and capture store, never re-sends a bound fingerprint, serves a reserved request as `interrupted_charged`, never grants fresh caps); the "AI ledger unchanged" check is **dry-only**; live ledger behaviour defined: `LedgerProvider` writes to the declared scope and limits, the runner and every lane verify the scope exists with exactly the declared limits before dispatch and refuse otherwise, and after the run the ledger may have grown only inside that scope and within the caps; **no scope is created by this task** | `test_allowance_r32`: `test_an_allowance_is_bound_to_one_run_key_and_refuses_another`, `test_the_day_limit_is_bound_in_the_file_and_never_changed`, `test_a_second_invocation_reopens_the_same_counts_and_never_gets_fresh_caps`, `test_a_lane_never_creates_the_allowance`, `test_live_refuses_an_unattributed_request`, `test_the_capture_store_file_is_bound_to_the_same_run_key`; `test_preflight_r32`: `test_the_declared_scope_must_exist_with_exactly_the_declared_limits`, `test_live_ledger_growth_only_inside_the_declared_scope_and_within_the_caps`; `test_runner_r32`: **`test_the_two_invocation_drill`**, `test_resumable_rules`, `test_a_resume_of_another_run_or_with_another_binding_is_refused`, `test_a_second_writer_is_refused`, `test_live_mode_refuses_a_missing_or_different_ledger_scope`. **All pass**; the dry run repeats the drill on the full run set (§ `DRY-RUN-REPORT.md`) |
| **RC-5** | **R34-05** (minor) | `lane_r32.py`, `preflight_r32.py`, `runner_r32.py`: live lanes verify their `AI_EVIDENCE_*` switches (B/C/R, and P = none) and the provider environment (`AI_PROVIDER`, model aliases, effort, timeouts, CLI path, ledger path / scope / limits and the `LedgerProvider` wrapping) against the declaration's bound values, in the environment **and** in the application's settings; a missing or different value refuses the run; the runner no longer falls back to default switches in live mode; dry mode uses `DRY_LANE_SWITCHES`, labelled as dry defaults | `test_preflight_r32`: `test_every_top_level_key_is_required[7]`, `test_a_missing_or_different_value_refuses_live_mode[20]`, `test_ledger_limits_above_the_caps_are_refused`, `test_a_complete_declaration_passes_…`, `test_the_lane_environment_equal_to_the_declaration_passes`, `test_a_missing_or_different_lane_value_refuses[9]`, `test_no_silent_default_switches_or_provider_environment`, `test_a_dry_exercise_is_never_a_live_declaration`; `test_runner_r32`: `test_live_mode_without_explicit_switches_or_provider_environment_refuses[3]`, `test_lane_env_has_no_silent_default`, the direct-lane environment refusals. **All pass** |
| **RC-6** | **R34-08** (minor) | `concentration_r32.py`: failures counted **once per (document, field)**; a wrong acceptance that also loses the fact is one failure; wrong acceptances on several pages of a document are one failure. (`lane_judge_r32.py` is unchanged: its per-row `critical` list reports distinct wrong values and is not a failure count) | `test_concentration_r32`: `test_a_wrong_acceptance_that_loses_the_fact_is_one_failure`, `test_wrong_acceptances_on_several_pages_of_one_document_are_one_failure`, `test_s1_one_wrong_revision_acceptance_is_one_failure_on_the_real_run_set`; `test_score_bcr_r32`: `test_s1_one_wrong_acceptance_is_exactly_one_failure_and_fails_the_candidate`. **All pass** |

**Other changes, each only what the corrections or the task's write rule need:**
- `sandbox_child_r32.py` and `test_sandbox_ingest_r32.py`: the sandbox base `C:/t/r2x/r33-sandbox/` → `C:/t/r2x/r34-sandbox/` (path only; this task may write sandboxes only under `C:/t/r2x/r34-sandbox/`). `sandbox_ingest_r32.py` is carried **unchanged by hash**; `runner_r32` sets its module constant `SANDBOX_BASE` to the r34 base at import (the constant is read when `ingest()` runs).
- `r32_test_helpers.py`: temporary live declarations and fake ledgers for the refusal tests (pytest `tmp_path` only; never an authorization, never the real ledger).
- New `r34_scenarios.py`: Review 34's scenario structures over the real truth and run set with lanes made from the truth (no reader, no prediction).

## 3. Item-13 rulings of Review 34, carried

The rulings (Review 34 §5) are carried unchanged; nothing in this package reverses them. The two ESCALATE items are listed for the declaration (§5 below).

| Interpretation | Ruling |
|---|---|
| The unlabelled `- R0n` suffix base form is accepted as identity on 8 rows (F003, F004, F005, F006 p1 and p2, F007, F011, F015) | **ACCEPT.** It carries the frozen evaluator .10 `suffix` equivalence and the application's `split_suffix`, and wrong suffixes or bases still fail (tested). Without it, the accepted baseline B would very likely go INVALID on F006 and F015 in the run set. The declaration lists it as an interpretation, and ORCH-06 tests .10 parity. |
| A C critical acceptance in any field makes every field NOT ELIGIBLE | **ACCEPT.** This is the plan's §5.4 safety gate on the candidate, and the stop rule ends C anyway. The same reasoning **requires** RC-2 (a conjunctive candidate outcome). |
| Cross-page identity follows evaluator .10 except on compilations | **ACCEPT** for cover and enclosure packages. **ESCALATE to the declaration** for drawing sets with per-page drawing numbers (F016 and F038 in the run set, F014 outside it): keep .10 parity and disclose it, or treat them as page-keyed (R34-06). |
| B counts as attempted only when its row exists | **ACCEPT.** Ingestion registers every run-set document, so this equals review31's "B always attempted". C skips documents whose B row is not fresh, so a B failure cannot inflate C's gain. Disclose. |
| The layout key is hand-written | **ACCEPT as frozen**: deterministic, documented, label text only, reproduced by me, and frozen before any prediction. Disclose two things:<br>• rules 6–11 were authored after reading label text;<br>• 18 documents are singletons that can never concentrate. |
| Contractor equals project | **ACCEPT** as a factual mapping of `PROJECT-VERIFICATION.json`. **ESCALATE the disclosure** (R34-07): A-05's contractor dimension adds nothing beyond the project leg in this cohort. |
| F069 p2 and p4 identity are NOT_SCORABLE (32 against 30) | **ACCEPT** (R34-11); list it in the declaration. |

## 4. Carried unchanged from review33 (by hash)

| File | sha256 | Equal to review33 |
|---|---|---|
| `labels_adapter_r32.py` | `ff9d2e6b9311bd9ceaaab76f1d3237c1129f8d6c1a70d56d831e11d0e02501ab` | yes |
| `literal_compare_r32.py` | `ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6` | yes |
| `converter_r32.py` | `4095a4967a7e7caa992feec4901e06c1836d263f62ab1ba884db8355c30f9704` | yes |
| `run_set_selector_r32.py` | `5c923ec85f90173b13836b04d81d6e96a6f498e4ce52a6a9a4f7e16851acba53` | yes |
| `sandbox_ingest_r32.py` | `3e0e906df9aa1d387bc8a018142e122c1c9545f54f6d2aa311718c75e45e92a6` | yes |
| `capture_store.py` (review31 copy) | `84c05fc438b83bef1673811be26b91a81fc8f0e52bd9e1cd94e82a22a30e27c3` | yes (and equal to review31) |
| `state_check.py` (review31 copy) | `a9985b100215363ba82c6070ce931b99b64110ce0b92566804dc2b6c482186c3` | yes (and equal to review31) |
| `stop_rules.py` (review31 copy) | `4632ffeaea83d7849328f5f7ac5a3a857de121fd389e4a066627e1bdb77f4996` | yes (and equal to review31) |
| `dry-run/TRUTH-R32.json` | `4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064` | yes (and re-derived by the adapter) |
| `RUN-SET-PROPOSAL.json` | `9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8` | yes (and re-derived by the selector) |
| `LABELS-R32-EVAL-INPUT.json` | `4b2c73d59ab852fa45eb46ff58f0ee13242c2ccac4db0221f4b1b607edede5cc` | yes (and re-derived by the converter) |
| `CONVERTER-RECONCILIATION.json` | `e350d2fe78d6062cf59328d1caedfca8f8a72210d2d043c5c37068033b2624f3` | yes |
| `ADAPTER-CONTRACT.md`, `RUN-SET-RULE.md` | `871c103d…148a`, `9ee2ccec…dad0` | yes |

Also unchanged (bound under `unchanged_modules`): `lane_judge_r32.py`, `inputs_r32.py`, `coverage_v4.py`, `score_lane_r32.py`, `synthetic_r32.py`, `tripwire_r32.py` and the tests of every unchanged module. The table of changed modules (review33 hash → review34 hash, with the finding answered) is in `BINDING-MANIFEST-R34.json` under `changed_modules` and in `SCORER-CHANGES.md` Part B.

## 5. What the ORCH-07 declaration must bind and decide

### 5.1 Carried forward verbatim from Review 34 §9 (heading level adjusted)

#### 9. What the ORCH-07 declaration must bind and decide

1. **Harness.** The corrected binding manifest after RC-1 to RC-6. Its own hash replaces `d1a8a401…`.
2. **Run set.**
   - `RUN-SET-PROPOSAL.json` (`9058f3d6…7ce8`, 24 documents), the selector code hash and seed `m2-r30-runset-2026-10-02`.
   - The executable control definitions.
   - **The unsupported-control shortfall of 2**, as a plan v2 §2.3 deviation: no substitute, and unsupported-input behaviour not validated. Any substitute is an owner decision, from the pool only.
   - The 8 negative decision documents: 4 controls and 4 top-ups.
3. **The concentration rule** (post-RC-1), its version and hash. Decision type and stratum are report-only. The contractor leg is degenerate (R34-07).
4. **The candidate-level outcome** (RC-2) as the comparison outcome. Per-field outcomes are diagnostics.
5. **The allowance and capture-store location.**
   - One bound path per declaration.
   - Same-stamp resume.
   - No fresh second invocation.
   - The project-day limit (60 per UTC day, all lanes) and a per-project request plan.
   - The caps: B 240 = C 240, R 40, P 36, at most 556.
6. **The ledger.**
   - Whether a live scope is created: name, `AI_LEDGER_PATH`, `AI_LEDGER_SCOPE` and limits no larger than the caps.
   - The runner's live-mode ledger check.
   - The owner's budget authorization naming the declaration hash.
7. **Lane switches.** The B, C and R switch sets, stated explicitly. The runner must not fall back to its defaults.
8. **The provider environment.**
   - `AI_PROVIDER`, the model aliases (standard and small), effort, timeouts and output limits, and the CLI path.
   - Whether `LedgerProvider` wraps the provider.
   - All bound by hash.
9. **The authorization.** The pinned path, the token digest and one-run use (RC-3).
10. **The interpretation list**, in addition to Review 33's C-2 list:
    - the suffix base form (8 rows);
    - the (d1) tolerance, including the application's `rejected`;
    - application `rejected` = revise-and-resubmit;
    - the cross-page identity decision for drawing sets (R34-06);
    - F069 p2/p4 (R34-11);
    - candidate-level gates;
    - B attempted when registered;
    - the layout-key provenance.
11. **Disclosures:**
    - the matched margin (section 7);
    - that the application processes the real cohort PDFs for the first time in live B (R34-18);
    - the reference-set statement on every metric;
    - policy `7efa891b…` and amendment `815d43fd…`.

### 5.2 Additions implied by RC-3 and RC-4 (this package)

12. **The pinned authorization path:** `<the declaration's own folder>/OWNER-DISPATCH-AUTHORIZATION.json`, bound as `authorization.path`; the runner has no `--auth-path` and refuses a configured one.
13. **The owner token digest:** `authorization.owner_token_sha256` (sha256 of a token the owner keeps); the authorization repeats it; the token is presented only at live start in `R34_OWNER_DISPATCH_TOKEN` and is never stored in any file.
14. **The one-run nonce:** the owner's authorization carries a nonce that the runner consumes into `<run folder>/authorization/`; every invocation (the first `run` and each `resume`) needs its own authorization with a fresh nonce for the same declaration.
15. **One run folder per declaration:** `run.stamp` and `run.folder` = `C:/t/r2x/r34-sandbox/<stamp>`, holding the one allowance (caps and the project-day limit bound in the file), the one capture store and `RUN-STATE.json`; `run` once, then only `resume`.
16. **The ledger scope name and limits:** `ledger.path`, `ledger.scope`, `ledger.limits` (with `requests` at most 556) and `wrap_provider: true`, equal to `AI_LEDGER_PATH`, `AI_LEDGER_SCOPE` and `AI_LEDGER_LIMITS`; the scope must exist with exactly these limits before dispatch (it is created only under the owner's budget authorization, never by the harness).
17. **Explicit lane switches and provider environment** in the exact form of `LIVE-RUN-CONTRACT.md` §2 (lanes B, C, R, P with P empty; the ten required provider keys).
18. **Disclosures added by this package:** a net gain of 1 in a field is always NOT ELIGIBLE under rule v2, and a net gain of 2 only passes when the two documents differ in project and layout (`CONCENTRATION-RULE-R32.md` §4); a budget stop (lane cap or day limit) is not undone by a resume (`LIVE-RUN-CONTRACT.md` §4).

## 6. Explicitly out of scope

- Evaluator .10 changes and its offline zero-call test (ORCH-06, C-6) and its verification (ORCH-06V).
- The declaration (ORCH-07, C-7), the budget decision and any owner authorization. `OWNER-DISPATCH-AUTHORIZATION.json` was **not** created anywhere, and no ledger scope was created.
- Any dispatch, prediction, label change, change to review31, review33, the cohort packages, the review folders, staging, the candidate or baseline trees, the application or production data.

## 7. Problems and limits found while doing this task (facts, not approvals)

- **Dry-run attempt 1** (stamp `r34dry-20261003a`) passed its drill and kept the ledger at 483/17, but its final assertion failed because the authorization-file search glob `*AUTHORIZATION*.json` also matched two **pre-existing** files of earlier packages (`fresh-cohort-r32/PRE-AUTHORIZATION-HASH-CHECK.json`, `review07/evidence/matched/SANDBOX-AUTHORIZATION.json`, both written before this task and neither an owner dispatch authorization). The search was made precise (file names containing `DISPATCH-AUTHORIZATION`, plus any JSON object with the keys of an authorization); attempt 1's outputs were moved to the agent scratchpad and the dry run was repeated as `r34dry-20261003b`. Its run folders remain under `C:/t/r2x/r34-sandbox/`.
- **Windows path length:** the consumption record is named by the first 32 hex characters of sha256(nonce) (the full digest is inside) so that test paths stay under 260 characters.
- **Not exercised:** the live path end to end (no authorization, no provider, no scope may exist); it is exercised up to the guard's refusal, with a direct lane invocation, on temporary declarations and fake ledgers.

## 8. Statuses, stated separately

1. **Source permission and verification.** A-02 (access, staging, drafting and preparation) and A-06 (project and provider **eligibility** for EP-3563, 22349, 27331, 15744, 26687 and 29255) are unchanged; neither authorizes dispatch. Verification stands at 10 of 10, with no replacement; the 72 staged files re-hash to SOURCE-MANIFEST (ingestion of 72 in the dry run).
2. **Label drafting.** `r32-labels-draft-1` is frozen and unchanged. It is AI-drafted (Claude Opus 5.5) and not human-signed.
3. **Reference set.** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is the reference set under amendment R32-01 (`815d43fd…5de6`; policy `7efa891b…4f47` unchanged): **independently AI-reviewed (Claude agents), not human-signed**, not human Golden Truth.
4. **Field populations.** Identity 57, revision 38, decision 38 (reproduced by the unchanged adapter); 0 extensions.
5. **Review 33 / Review 34 conditions.** Review 33: C-4 (the concentration rule) and C-5 (the harness) are **answered again by this package, pending Review 35**; C-6 is ORCH-06, C-7 is ORCH-07, C-8 is carried into the declaration. Review 34: RC-1 to RC-6 are **implemented and tested here, pending Review 35**; nothing is self-approved.
6. **Live-run authorization and budget.** **None.** No `OWNER-DISPATCH-AUTHORIZATION.json` exists (searched under the pilot folder, the work folders, the r34 sandbox and the scratchpad). No budget, no ledger scope, no dispatch. The AI ledger was opened read-only only and reads 483 entries, 17 scopes and 0 amendments, before and after.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.
