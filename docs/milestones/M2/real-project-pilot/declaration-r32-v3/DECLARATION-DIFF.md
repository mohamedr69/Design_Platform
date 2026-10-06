# DECLARATION-DIFF: v2 (`f38fb281…25af`, frozen, superseded, never run) → v3 (this package)

- v3 sha256: `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`.
- Method: both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the absent Desktop installation's prefix `C:/Users/moham/Desktop/dev/dev/ep-platform` replaced by `G:/dev (2)/dev/ep-platform-merged/ep-platform`), changed, added or removed.
- Top-level keys: {'unchanged': 36, 'repointed only': 10, 'changed': 29, 'added': 12, 'removed': 0}.
- Leaves: {'unchanged': 835, 'repointed': 68, 'changed': 113, 'added': 266, 'removed': 34}.
- **Protected values (every number and rule that must not change): ALL UNCHANGED (or re-pointed only)** (75 keys and leaves checked: application_ai_limits, application_env, application_env_detail, authorization_status, budget, budget_approved, budget_detail, cohort, concentration_on_proposal, controls, cost, cross_page_identity, decision_coverage_gate, decision_coverage_gate_detail, elapsed_bounds, emission_rules, estimated_usage, evaluator, executed, gates, interpretations, lane_switches, lane_task_kinds, lane_task_kinds_detail, lanes, ledger.limits, ledger.path, ledger.wrap_provider, model_identity.cli.version, model_identity.models.small, model_identity.models.standard, model_identity.provider, plan_sources, policy, primary_outcomes, probe_population, project_request_bounds_detail.EP-27331, project_request_bounds_detail.all_projects_planning, project_request_bounds_detail.all_projects_structural, project_request_bounds_detail.required_application_minimum, project_window, project_window_detail, provider_env.AI_CLI_TIMEOUT_S, provider_env.AI_EFFORT, provider_env.AI_LEDGER_LIMITS, provider_env.AI_LEDGER_PATH, provider_env.AI_MAX_CALLS_PER_DOCUMENT, provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY, provider_env.AI_MAX_ELAPSED_S_PER_JOB, provider_env.AI_MODEL_SMALL, provider_env.AI_MODEL_STANDARD, provider_env.AI_PROVIDER, provider_env.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY, provider_env.AI_TIMEOUT_S, r_and_p, reference_set, reference_set_statement, resume_detail.invocations_expected, resume_detail.resume_invocations.EP-27331_full, resume_detail.resume_invocations.last_invocation_starts_after_s, resume_detail.rule, resume_policy, retry_rule, run_set.labels_eval_input, run_set.truth, run_set_sha256, scope_limitations, standing_status, stop_rules, switch_names, thresholds_verbatim, token_thresholds, trees, unread_page_rule, what_this_run_can_show).

## Top-level keys

| Key | State | Reason |
|---|---|---|
| `application_ai_limits` | unchanged | unchanged |
| `application_env` | unchanged | unchanged |
| `application_env_detail` | unchanged | unchanged |
| `authorities` | changed | A-11 applied and summarised; the authority register re-hashed at its current (append-only) state |
| `authorization` | changed | pinned path beside v3; the RUN file v3; the scope v3; invocation from review42 with the bound interpreter; contract v5 section 3 cited; the multi-invocation file fields (A-11 section 4) |
| `authorization_status` | unchanged | unchanged |
| `binding_manifest_sha256` | changed | BINDING-MANIFEST-R42 (review42) instead of R39 |
| `bound_files_rehashed` | added | ADDED: the build-time re-hash record |
| `budget` | unchanged | unchanged |
| `budget_approved` | unchanged | unchanged |
| `budget_detail` | unchanged | unchanged |
| `cohort` | repointed only | only the Desktop paths re-pointed |
| `concentration_on_proposal` | repointed only | only the Desktop paths re-pointed |
| `contract` | changed | contract 5 (review42 preflight_r32.CONTRACT 'r42-live-contract-5') |
| `controls` | unchanged | unchanged |
| `cost` | unchanged | unchanged |
| `cross_page_identity` | repointed only | only the Desktop paths re-pointed |
| `decision_coverage_gate` | unchanged | unchanged |
| `decision_coverage_gate_detail` | repointed only | only the Desktop paths re-pointed |
| `declared_at_utc` | changed | the time of this freeze |
| `disclosures` | changed | R40-04, R40-08 (R41-12 correction), the CLI dead-end (R41-09 closed), path length, the dry exercise (R41-13) restated; nine ORCH-10 disclosures added |
| `disk_precondition` | added | ADDED (contract 5): 2 GiB on C:, only upward (R41-10, C1) |
| `disk_precondition_detail` | added | ADDED |
| `dispatch_order` | changed | the reordered invocation (contract v5 section 14) |
| `elapsed_bounds` | unchanged | unchanged |
| `emission_rules` | unchanged | unchanged |
| `estimated_usage` | unchanged | unchanged |
| `evaluator` | repointed only | only the Desktop paths re-pointed |
| `executed` | unchanged | unchanged |
| `forbidden_after_authorization` | changed | four items added (v2, the merged installation's CLI / .env / data / code, run-folder records, the floor and the bound) |
| `gates` | unchanged | unchanged |
| `global_provider` | added | ADDED (contract 5; R40-04 option 2) |
| `harness` | changed | review42 (manifest, binding, modules, contracts v5); review39 added to the lineage; the work records referenced in the v2 package |
| `interpretations` | unchanged | unchanged |
| `interpreter` | added | ADDED (contract 5): the bound interpreter |
| `interpreter_detail` | added | ADDED: requirements and import check of both trees |
| `invocation_order` | added | ADDED (R41-09, R41-10, R41-11): the reordered invocation, re-entry and the dead-end cases |
| `isolation` | added | ADDED (contract 5): the merged installation is forbidden except the venv and the review42 harness |
| `isolation_detail` | added | ADDED |
| `lane_switches` | unchanged | unchanged |
| `lane_task_kinds` | unchanged | unchanged |
| `lane_task_kinds_detail` | unchanged | unchanged |
| `lanes` | unchanged | unchanged |
| `ledger` | changed | the v3 scope name; path and limits unchanged |
| `ledger_detail` | changed | create_scope_r42.py; the C1 disk check |
| `model_identity` | changed | the CLI pinned by ABSOLUTE PATH and file sha256 (contract 5); models, provider and version line unchanged |
| `model_identity_detail` | changed | the CLI rule (file hash before anything, version before the folder); the bundled 2.1.289 named as not used |
| `name` | changed | names declaration v3 (merged installation) |
| `plan_sources` | repointed only | only the Desktop paths re-pointed |
| `policy` | unchanged | unchanged |
| `portability` | added | ADDED: the re-pointing and the path lengths |
| `primary_outcomes` | unchanged | unchanged |
| `probe_population` | unchanged | unchanged |
| `project_request_bounds` | changed | review42 PROJECT-REQUEST-BOUNDS.json (recomputed; equal to review39's in every verified key, the run-set path re-pointed) |
| `project_request_bounds_detail` | changed | adds the equality record with review39 |
| `project_window` | unchanged | unchanged |
| `project_window_detail` | unchanged | unchanged |
| `provider` | changed | owner-confirmable: the v3 scope, the CLI pin, the disk floor, the resume authorization; AI_CLAUDE_CLI declared absolute |
| `provider_env` | changed | AI_CLAUDE_CLI = the absolute CLI path; AI_LEDGER_SCOPE = the v3 scope; every other value unchanged |
| `r_and_p` | unchanged | unchanged |
| `reference_set` | repointed only | only the Desktop paths re-pointed |
| `reference_set_statement` | unchanged | unchanged |
| `request_path_coverage` | changed | R40-04 closed by option 2: the refusing global provider; static and dynamic proof; v2's proof-based text kept as superseded |
| `resume_authorization` | added | ADDED (contract 5; A-11 section 4): the separable multi-invocation proposal, max 3 |
| `resume_detail` | changed | review42 RESUME-INVOCATIONS-R42.json (byte-identical to R39's) |
| `resume_policy` | unchanged | unchanged |
| `retry_rule` | repointed only | only the Desktop paths re-pointed |
| `reviews` | changed | Verification 41 (and its findings and package check) and RUNBOOK-ADDENDUM-R41 added |
| `revision_comparison_rule` | changed | implementation re-bound to the review42 copy (same hash) |
| `run` | changed | stamp r32-v3, base C:/t/r2x/r42-sandbox, folder C:/t/r2x/r42-sandbox/r32-v3 (same lengths as v2); the re-entry rule |
| `run_set` | changed | selector re-bound to the review42 copy (same hash) |
| `run_set_sha256` | unchanged | unchanged |
| `schema` | changed | the v3 schema id |
| `scope_limitations` | unchanged | unchanged |
| `standing_status` | unchanged | unchanged |
| `status` | changed | Verification 42 and the owner's decision card pending |
| `stop_rules` | repointed only | only the Desktop paths re-pointed |
| `supersedes` | changed | supersedes v2 f38fb281...25af (A-11; never to be run); v2's own supersedes record kept as lineage |
| `switch_names` | unchanged | unchanged |
| `task` | changed | ORCH-10 / R42PORT-IMPL |
| `thresholds_verbatim` | repointed only | only the Desktop paths re-pointed |
| `token_thresholds` | unchanged | unchanged |
| `trees` | unchanged | unchanged |
| `unread_page_rule` | unchanged | unchanged |
| `verification40_items` | changed | R40-04 now closed by option 2 |
| `verification41_items` | added | ADDED: R41-09 to R41-15, R41-18, C1; the four r40 records bound by hash |
| `what_this_run_can_show` | unchanged | unchanged |

## Changed, added and removed leaves

### changed (113)

- `authorities.applied`
- `authorities.register.sha256`
- `authorization.invocation.harness_copy`
- `authorization.invocation.resume`
- `authorization.invocation.run`
- `authorization.invocation.working_directory`
- `authorization.one_invocation_per_authorization`
- `authorization.path`
- `authorization.placeholder_rule`
- `authorization.runbook`
- `authorization.two_hash_procedure.budget_authorization_names`
- `authorization.two_hash_procedure.independent_verification`
- `authorization.two_hash_procedure.run_file`
- `binding_manifest_sha256`
- `contract`
- `declared_at_utc`
- `disclosures`
- `dispatch_order`
- `forbidden_after_authorization`
- `harness.accepted_by`
- `harness.binding_manifest.entries`
- `harness.binding_manifest.path`
- `harness.binding_manifest.sha256`
- `harness.binding_manifest.supersedes`
- `harness.bound_code_used_as_is`
- `harness.concentration_rule.code.path`
- `harness.modules.allowance_r32.path`
- `harness.modules.capture_store.path`
- `harness.modules.concentration_r32.path`
- `harness.modules.converter_r32.path`
- `harness.modules.coverage_v4.path`
- `harness.modules.dispatch_guard_r32.path`
- `harness.modules.dispatch_guard_r32.sha256`
- `harness.modules.drawings_ai_probe_r39.path`
- `harness.modules.inputs_r32.path`
- `harness.modules.inputs_r32.sha256`
- `harness.modules.labels_adapter_r32.path`
- `harness.modules.lane_judge_r32.path`
- `harness.modules.lane_r32.path`
- `harness.modules.lane_r32.sha256`
- `harness.modules.literal_compare_r32.path`
- `harness.modules.model_identity_r38.path`
- `harness.modules.model_identity_r38.sha256`
- `harness.modules.page_relations_r38.path`
- `harness.modules.preflight_r32.path`
- `harness.modules.preflight_r32.sha256`
- `harness.modules.project_bounds_r32.path`
- `harness.modules.r32_test_helpers.path`
- `harness.modules.r32_test_helpers.sha256`
- `harness.modules.r34_scenarios.path`
- `harness.modules.request_paths_r39.path`
- `harness.modules.resume_invocations_r39.path`
- `harness.modules.run_control_r38.path`
- `harness.modules.run_control_r38.sha256`
- `harness.modules.run_set_selector_r32.path`
- `harness.modules.run_state_r38.path`
- `harness.modules.run_state_r38.sha256`
- `harness.modules.runner_r32.path`
- `harness.modules.runner_r32.sha256`
- `harness.modules.sandbox_child_r32.path`
- `harness.modules.sandbox_ingest_r32.path`
- `harness.modules.sandbox_ingest_r32.sha256`
- `harness.modules.score_bcr_r32.path`
- `harness.modules.score_lane_r32.path`
- `harness.modules.state_check.path`
- `harness.modules.stop_rules.path`
- `harness.modules.synthetic_r32.path`
- `harness.modules.tripwire_r32.path`
- `harness.modules.unread_pages_probe_r39.path`
- `harness.modules.visibility_r38.path`
- `harness.package`
- `harness.package_check.path`
- `harness.package_check.sha256`
- `harness.package_manifest.path`
- `harness.package_manifest.sha256`
- `ledger.scope`
- `ledger_detail.creation`
- `model_identity.cli.path`
- `model_identity_detail.cli.path_setting`
- `model_identity_detail.cli.rule`
- `name`
- `project_request_bounds.path`
- `project_request_bounds.sha256`
- `provider.owner_confirmable.cli_version`
- `provider.owner_confirmable.ledger.scope`
- `provider.proposed_vs_tree_defaults.AI_CLAUDE_CLI.declared`
- `provider_env.AI_CLAUDE_CLI`
- `provider_env.AI_LEDGER_SCOPE`
- `request_path_coverage.finding`
- `request_path_coverage.lane_B`
- `request_path_coverage.residual_risk`
- `resume_detail.resume_invocations.path`
- `revision_comparison_rule.implementation.path`
- `run.allowance`
- `run.base_justification`
- `run.capture_store`
- `run.folder`
- `run.rule`
- `run.run_state`
- `run.sandbox_base`
- `run.stamp`
- `run_set.selector.path`
- `schema`
- `status`
- `supersedes.declaration.path`
- `supersedes.declaration.sha256`
- `supersedes.differences`
- `supersedes.manifest.path`
- `supersedes.manifest.sha256`
- `supersedes.status`
- `supersedes.structure`
- `task`
- `verification40_items.R40-04`

### added (266)

- `authorities.summary.A-11`
- `authorization.authorization_rule_v5.lines`
- `authorization.authorization_rule_v5.sha256`
- `authorization.authorization_rule_v5.source`
- `authorization.authorization_rule_v5.text`
- `authorization.file_fields_multi.authorized_by`
- `authorization.file_fields_multi.declaration_sha256`
- `authorization.file_fields_multi.invocations_authorized`
- `authorization.file_fields_multi.no_other_key`
- `authorization.file_fields_multi.nonces`
- `authorization.file_fields_multi.owner_token_sha256`
- `authorization.invocation.reentry`
- `bound_files_rehashed.rule`
- `bound_files_rehashed.v2_nodes_equal`
- `disk_precondition.min_free_bytes`
- `disk_precondition.path`
- `disk_precondition_detail.bound`
- `disk_precondition_detail.condition`
- `disk_precondition_detail.enforced_by`
- `disk_precondition_detail.why`
- `global_provider.B`
- `global_provider.C`
- `global_provider.P`
- `global_provider.R`
- `harness.contracts.change_record_r42.path`
- `harness.contracts.change_record_r42.sha256`
- `harness.contracts.live_run_contract_v5.path`
- `harness.contracts.live_run_contract_v5.sha256`
- `harness.contracts.request_paths_r42.path`
- `harness.contracts.request_paths_r42.sha256`
- `harness.contracts.request_paths_static_r42.path`
- `harness.contracts.request_paths_static_r42.sha256`
- `harness.lineage.review39.accepted_by`
- `harness.lineage.review39.binding.path`
- `harness.lineage.review39.binding.sha256`
- `harness.lineage.review39.change_record.path`
- `harness.lineage.review39.change_record.sha256`
- `harness.lineage.review39.contract_v4.path`
- `harness.lineage.review39.contract_v4.sha256`
- `harness.lineage.review39.manifest.path`
- `harness.lineage.review39.manifest.sha256`
- `harness.modules.request_paths_r42.path`
- `harness.modules.request_paths_r42.sha256`
- `harness.review39_work_records.AUDIT-LOG.md.path`
- `harness.review39_work_records.PROGRESS.md.path`
- `interpreter.path`
- `interpreter.sha256`
- `interpreter.version`
- `interpreter_detail.app_resolves_to_tree.baseline`
- `interpreter_detail.app_resolves_to_tree.candidate`
- `interpreter_detail.base_interpreter.path`
- `interpreter_detail.base_interpreter.sha256`
- `interpreter_detail.evidence.path`
- `interpreter_detail.evidence.sha256`
- `interpreter_detail.freeze_record_differences.pip.installed`
- `interpreter_detail.freeze_record_differences.pip.record`
- `interpreter_detail.needed_modules_import.baseline`
- `interpreter_detail.needed_modules_import.candidate`
- `interpreter_detail.other_app_modules_failed.baseline`
- `interpreter_detail.other_app_modules_failed.candidate`
- `interpreter_detail.requirements_differences.baseline`
- `interpreter_detail.requirements_differences.candidate`
- `interpreter_detail.sys_version`
- `invocation_order.authorization_consumed`
- `invocation_order.contract.lines`
- `invocation_order.contract.sha256`
- `invocation_order.contract.source`
- `invocation_order.contract.text`
- `invocation_order.deadend_cases_closed.A_version_mismatch.final`
- `invocation_order.deadend_cases_closed.A_version_mismatch.first`
- `invocation_order.deadend_cases_closed.A_version_mismatch.ok`
- `invocation_order.deadend_cases_closed.A_version_mismatch.recovered_by`
- `invocation_order.deadend_cases_closed.B_disk_full_at_identity_record.final`
- `invocation_order.deadend_cases_closed.B_disk_full_at_identity_record.first`
- `invocation_order.deadend_cases_closed.B_disk_full_at_identity_record.ok`
- `invocation_order.deadend_cases_closed.B_disk_full_at_identity_record.recovered_by`
- `invocation_order.deadend_cases_closed.C_interrupted_at_allowance_creation.final`
- `invocation_order.deadend_cases_closed.C_interrupted_at_allowance_creation.first`
- `invocation_order.deadend_cases_closed.C_interrupted_at_allowance_creation.ok`
- `invocation_order.deadend_cases_closed.C_interrupted_at_allowance_creation.recovered_by`
- `invocation_order.deadend_cases_closed.D_failure_after_the_allowance.final`
- `invocation_order.deadend_cases_closed.D_failure_after_the_allowance.first`
- `invocation_order.deadend_cases_closed.D_failure_after_the_allowance.ok`
- `invocation_order.deadend_cases_closed.D_failure_after_the_allowance.recovered_by`
- `invocation_order.deadend_cases_closed.E_lane_B_crash_after_a_response.final`
- `invocation_order.deadend_cases_closed.E_lane_B_crash_after_a_response.first`
- `invocation_order.deadend_cases_closed.E_lane_B_crash_after_a_response.ok`
- `invocation_order.deadend_cases_closed.E_lane_B_crash_after_a_response.recovered_by`
- `invocation_order.deadend_cases_closed.E_lane_C_crash_after_a_response.final`
- `invocation_order.deadend_cases_closed.E_lane_C_crash_after_a_response.first`
- `invocation_order.deadend_cases_closed.E_lane_C_crash_after_a_response.ok`
- `invocation_order.deadend_cases_closed.E_lane_C_crash_after_a_response.recovered_by`
- `invocation_order.deadend_cases_closed.E_lane_R_crash_after_a_response.final`
- `invocation_order.deadend_cases_closed.E_lane_R_crash_after_a_response.first`
- `invocation_order.deadend_cases_closed.E_lane_R_crash_after_a_response.ok`
- `invocation_order.deadend_cases_closed.E_lane_R_crash_after_a_response.recovered_by`
- `invocation_order.deadend_cases_closed.T_version_timeout.final`
- `invocation_order.deadend_cases_closed.T_version_timeout.first`
- `invocation_order.deadend_cases_closed.T_version_timeout.ok`
- `invocation_order.deadend_cases_closed.T_version_timeout.recovered_by`
- `invocation_order.deadend_cases_closed.live_shaped.B_identity_record_disk_full.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.B_identity_record_disk_full.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.B_identity_record_disk_full.result`
- `invocation_order.deadend_cases_closed.live_shaped.C_interrupted_at_allowance.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.C_interrupted_at_allowance.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.C_interrupted_at_allowance.result`
- `invocation_order.deadend_cases_closed.live_shaped.D_consumption_fails_after_the_allowance.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.D_consumption_fails_after_the_allowance.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.D_consumption_fails_after_the_allowance.result`
- `invocation_order.deadend_cases_closed.live_shaped.D_resume_with_the_same_unconsumed_authorization.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.D_resume_with_the_same_unconsumed_authorization.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.D_resume_with_the_same_unconsumed_authorization.result`
- `invocation_order.deadend_cases_closed.live_shaped.D_run_again_refused.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.D_run_again_refused.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.D_run_again_refused.result`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_cli_updated.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_cli_updated.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_cli_updated.result`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_disk_below_floor.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_disk_below_floor.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_disk_below_floor.result`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_fresh_nonce.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_fresh_nonce.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_fresh_nonce.result`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_with_the_consumed_nonce.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_with_the_consumed_nonce.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.E_resume_with_the_consumed_nonce.result`
- `invocation_order.deadend_cases_closed.live_shaped.re_entry_with_the_same_authorization.allowance`
- `invocation_order.deadend_cases_closed.live_shaped.re_entry_with_the_same_authorization.nonces_consumed`
- `invocation_order.deadend_cases_closed.live_shaped.re_entry_with_the_same_authorization.result`
- `invocation_order.deadend_cases_closed.ok`
- `invocation_order.findings`
- `isolation.allowed_under_forbidden.harness`
- `isolation.allowed_under_forbidden.interpreter`
- `isolation.env_file_never_read`
- `isolation.forbidden_root`
- `isolation_detail.inherited_os_environment`
- `isolation_detail.lane_env_checks`
- `isolation_detail.merged_env_file.path`
- `isolation_detail.merged_env_file.read`
- `isolation_detail.rule`
- `model_identity.cli.sha256`
- `model_identity_detail.cli.bundled_cli_not_used.path`
- `model_identity_detail.cli.bundled_cli_not_used.statement`
- `portability.contract.lines`
- `portability.contract.sha256`
- `portability.contract.source`
- `portability.contract.text`
- `portability.path_lengths.evidence.path`
- `portability.path_lengths.evidence.sha256`
- `portability.path_lengths.summary.bound_max`
- `portability.path_lengths.summary.live_run_folder_files_max`
- `portability.path_lengths.summary.live_staged_max`
- `portability.path_lengths.summary.live_staged_max_inv_1_to_9`
- `portability.path_lengths.summary.long_paths_enabled`
- `portability.path_lengths.summary.owner_records_max`
- `portability.path_lengths.summary.package_max.declaration-r32-v2`
- `portability.path_lengths.summary.package_max.declaration-r32-v3`
- `portability.path_lengths.summary.package_max.review39`
- `portability.path_lengths.summary.package_max.review42`
- `portability.path_lengths.summary.paths_at_or_over_260_outside_staged_pdfs`
- `portability.path_lengths.summary.statement`
- `portability.repointed`
- `portability.why`
- `project_request_bounds_detail.equality_with_review39.differs_only_in`
- `project_request_bounds_detail.equality_with_review39.every_verify_bounds_key_equal`
- `project_request_bounds_detail.equality_with_review39.review39.path`
- `project_request_bounds_detail.equality_with_review39.review39.sha256`
- `provider.owner_confirmable.disk_precondition`
- `provider.owner_confirmable.resume_authorization`
- `request_path_coverage.closed_by`
- `request_path_coverage.contract.lines`
- `request_path_coverage.contract.sha256`
- `request_path_coverage.contract.source`
- `request_path_coverage.contract.text`
- `request_path_coverage.dynamic.demo.B.breach`
- `request_path_coverage.dynamic.demo.B.drill_answer`
- `request_path_coverage.dynamic.demo.B.global_provider`
- `request_path_coverage.dynamic.demo.B.run_state`
- `request_path_coverage.dynamic.demo.C.breach`
- `request_path_coverage.dynamic.demo.C.drill_answer`
- `request_path_coverage.dynamic.demo.C.global_provider`
- `request_path_coverage.dynamic.demo.C.run_state`
- `request_path_coverage.dynamic.demo.P.breach`
- `request_path_coverage.dynamic.demo.P.drill_answer`
- `request_path_coverage.dynamic.demo.P.global_provider`
- `request_path_coverage.dynamic.demo.P.run_state`
- `request_path_coverage.dynamic.demo.R.breach`
- `request_path_coverage.dynamic.demo.R.drill_answer`
- `request_path_coverage.dynamic.demo.R.global_provider`
- `request_path_coverage.dynamic.demo.R.run_state`
- `request_path_coverage.dynamic.junit.path`
- `request_path_coverage.dynamic.junit.sha256`
- `request_path_coverage.dynamic.result.errors`
- `request_path_coverage.dynamic.result.failures`
- `request_path_coverage.dynamic.result.returncode`
- `request_path_coverage.dynamic.result.skipped`
- `request_path_coverage.dynamic.result.tail`
- `request_path_coverage.dynamic.result.tests`
- `request_path_coverage.static.doc.path`
- `request_path_coverage.static.doc.sha256`
- `request_path_coverage.static.reached_sites_equal_to_review39.B`
- `request_path_coverage.static.reached_sites_equal_to_review39.C`
- `request_path_coverage.static.reached_sites_equal_to_review39.R`
- `request_path_coverage.static.static.path`
- `request_path_coverage.static.static.sha256`
- `request_path_coverage.static.summary.application_set_provider_sites_reached`
- `request_path_coverage.static.summary.every_lane_installs_before_its_application_entry`
- `request_path_coverage.static.summary.every_site_guarded`
- `request_path_coverage.static.summary.get_provider_sites`
- `request_path_coverage.static.summary.statement`
- `request_path_coverage.superseded_v2_coverage.corrected_claim`
- `request_path_coverage.superseded_v2_coverage.coverage_for_C_R_P`
- `request_path_coverage.superseded_v2_coverage.owner_options`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.PATHS-MINE-R40.json.path`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.PATHS-MINE-R40.json.sha256`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.PATHS-WHY-R40.json.path`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.PATHS-WHY-R40.json.sha256`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.UNREAD-R40.json.path`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.UNREAD-R40.json.sha256`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.paths_mine_r40.py.path`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.paths_mine_r40.py.sha256`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.paths_why_r40.py.path`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.paths_why_r40.py.sha256`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.unread_r40.py.path`
- `request_path_coverage.superseded_v2_coverage.proof_bound_in_v2.unread_r40.py.sha256`
- `request_path_coverage.superseded_v2_coverage.residual_risk`
- `resume_authorization.expected_use`
- `resume_authorization.implementation.guard.path`
- `resume_authorization.implementation.guard.sha256`
- `resume_authorization.implementation.tests`
- `resume_authorization.max_invocations_per_file`
- `resume_authorization.rules`
- `resume_authorization.status`
- `resume_detail.resume_invocations.equality_with_review39`
- `reviews.runbook_addendum_r41.path`
- `reviews.runbook_addendum_r41.sha256`
- `reviews.verification41.path`
- `reviews.verification41.sha256`
- `reviews.verification41_findings.path`
- `reviews.verification41_findings.sha256`
- `reviews.verification41_package_check.path`
- `reviews.verification41_package_check.sha256`
- `supersedes.lineage.declaration.path`
- `supersedes.lineage.declaration.sha256`
- `supersedes.lineage.differences`
- `supersedes.lineage.manifest.path`
- `supersedes.lineage.manifest.sha256`
- `supersedes.lineage.status`
- `supersedes.lineage.structure`
- `verification41_items.R41-09`
- `verification41_items.R41-10`
- `verification41_items.R41-11`
- `verification41_items.R41-12`
- `verification41_items.R41-13`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/AUDIT-LOG.md.path`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/AUDIT-LOG.md.sha256`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/FROZEN-INPUTS-FINAL.json.path`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/FROZEN-INPUTS-FINAL.json.sha256`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/PROGRESS.md.path`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/PROGRESS.md.sha256`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/RESPONSE-APPEND-RECORD.json.path`
- `verification41_items.R41-14.bound_by_hash.C:/t/iso/work/r2x/r40/RESPONSE-APPEND-RECORD.json.sha256`
- `verification41_items.R41-15`
- `verification41_items.R41-18`
- `verification41_items.condition_C1`

### removed (34)

- `harness.review39_work_records.AUDIT-LOG.md.package_path`
- `harness.review39_work_records.PROGRESS.md.package_path`
- `harness.review39_work_records.why`
- `request_path_coverage.corrected_claim`
- `request_path_coverage.coverage_for_C_R_P`
- `request_path_coverage.owner_options`
- `request_path_coverage.proof_bound.PATHS-MINE-R40.json.original`
- `request_path_coverage.proof_bound.PATHS-MINE-R40.json.package_path`
- `request_path_coverage.proof_bound.PATHS-MINE-R40.json.sha256`
- `request_path_coverage.proof_bound.PATHS-MINE-R40.json.verification40_recorded`
- `request_path_coverage.proof_bound.PATHS-WHY-R40.json.original`
- `request_path_coverage.proof_bound.PATHS-WHY-R40.json.package_path`
- `request_path_coverage.proof_bound.PATHS-WHY-R40.json.sha256`
- `request_path_coverage.proof_bound.PATHS-WHY-R40.json.verification40_recorded`
- `request_path_coverage.proof_bound.UNREAD-R40.json.original`
- `request_path_coverage.proof_bound.UNREAD-R40.json.package_path`
- `request_path_coverage.proof_bound.UNREAD-R40.json.sha256`
- `request_path_coverage.proof_bound.UNREAD-R40.json.verification40_recorded`
- `request_path_coverage.proof_bound.paths_mine_r40.py.original`
- `request_path_coverage.proof_bound.paths_mine_r40.py.package_path`
- `request_path_coverage.proof_bound.paths_mine_r40.py.sha256`
- `request_path_coverage.proof_bound.paths_mine_r40.py.verification40_recorded`
- `request_path_coverage.proof_bound.paths_why_r40.py.original`
- `request_path_coverage.proof_bound.paths_why_r40.py.package_path`
- `request_path_coverage.proof_bound.paths_why_r40.py.sha256`
- `request_path_coverage.proof_bound.paths_why_r40.py.verification40_recorded`
- `request_path_coverage.proof_bound.request_paths_static.path`
- `request_path_coverage.proof_bound.request_paths_static.sha256`
- `request_path_coverage.proof_bound.unread_r40.py.original`
- `request_path_coverage.proof_bound.unread_r40.py.package_path`
- `request_path_coverage.proof_bound.unread_r40.py.sha256`
- `request_path_coverage.proof_bound.unread_r40.py.verification40_recorded`
- `request_path_coverage.proof_bound.verification40_package_check.path`
- `request_path_coverage.proof_bound.verification40_package_check.sha256`

