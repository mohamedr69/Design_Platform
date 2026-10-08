# DECLARATION-DIFF-V4-V5: v4 (`e0a93c46...fbeb9`, frozen, never authorized, never run) -> v5 (this package)

- v5 sha256: `db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`.
- Method (the R42 leaf-diff form): both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the R43-44 re-point `review43/scripts/harness-r32`->`review45/scripts/harness-r32`), rebound (the sha256 of a re-pointed review45 harness file, equal to the hash BINDING-MANIFEST-R45-HARNESS binds), changed, added or removed.
- Top-level keys: {'unchanged': 66, 'repointed / rebound only': 4, 'changed': 25, 'added': 1, 'removed': 0}.
- Leaves: {'unchanged': 1281, 'repointed': 41, 'rebound': 2, 'changed': 69, 'added': 92, 'removed': 12}.
- **Protected values (every number and rule that must not change): ALL UNCHANGED (or re-pointed / rebound only)** (75 keys and leaves checked).
- Trees in text: frozen-r13 7ec3d2cf / cand-r30n 436daef2 in trees, lanes and evaluator, equal to v4.
- New identifiers: stamp r32-v5, folder, scope, AI_LEDGER_SCOPE, pinned authorization and RUN paths, binding 9af8e07a..., isolation harness review45.
- v4 identifiers left in v5: 18, 18 inside record keys, 0 outside.
- Result: OK.

## Top-level keys

| Key | State | Reason |
|---|---|---|
| `application_ai_limits` | unchanged | unchanged |
| `application_env` | unchanged | unchanged |
| `application_env_detail` | unchanged | unchanged |
| `authorities` | unchanged | the authority register re-hashed at its current (append-only) state |
| `authorization` | changed | pinned authorization path, RUN file and scope of v5 in the budget-authorization names; invocation from review45 with its manifest (run, working_directory, harness_copy); runbook pointer RUNBOOK-R32-V5.md |
| `authorization_status` | unchanged | unchanged |
| `binding_manifest_sha256` | changed | harness rebind: BINDING-MANIFEST-R45-HARNESS (review45, 9af8e07a...9ffb) instead of BINDING-MANIFEST-R43-HARNESS |
| `bound_files_rehashed` | changed | the v5 re-hash record (v4 nodes; rebound review45 harness nodes) |
| `budget` | unchanged | unchanged |
| `budget_approved` | unchanged | unchanged |
| `budget_detail` | unchanged | unchanged |
| `cohort` | unchanged | unchanged |
| `concentration_on_proposal` | unchanged | unchanged |
| `contract` | unchanged | unchanged |
| `controls` | unchanged | unchanged |
| `cost` | unchanged | unchanged |
| `cross_page_identity` | unchanged | unchanged |
| `decision_coverage_gate` | unchanged | unchanged |
| `decision_coverage_gate_detail` | unchanged | unchanged |
| `declared_at_utc` | changed | the time of this freeze |
| `disclosures` | changed | corrected first read (R45-06, R45-07, the R34-18 three-document exception, read count 5), dry exercise / isolation / ledger / test-exception disclosures restated for review45 and v5, seven added (harness rebind, drill, criterion and result, AI-on limit R45-08, drill limits, pre-run exposure, A-13 item 3 lapsed) |
| `disk_precondition` | unchanged | unchanged |
| `disk_precondition_detail` | unchanged | unchanged |
| `dispatch_order` | unchanged | unchanged |
| `elapsed_bounds` | unchanged | unchanged |
| `emission_rules` | unchanged | unchanged |
| `estimated_usage` | unchanged | unchanged |
| `evaluator` | unchanged | unchanged |
| `executed` | unchanged | unchanged |
| `forbidden_after_authorization` | changed | the harness prohibition re-pointed to review45; two items added (the superseded v4; a dry drill flag in a live invocation) |
| `gates` | unchanged | unchanged |
| `global_provider` | unchanged | unchanged |
| `harness` | changed | harness rebind: review45 (binding and package manifest, package check, accepted_by Verification 45, modules re-pointed and rebound incl. the new drill_r45, drill contracts, review43 added to the lineage) |
| `interpretations` | unchanged | unchanged |
| `interpreter` | unchanged | unchanged |
| `interpreter_detail` | unchanged | unchanged |
| `invocation_order` | unchanged | unchanged |
| `isolation` | repointed / rebound only | harness rebind: the review45 harness folder |
| `isolation_detail` | unchanged | unchanged |
| `lane_switches` | unchanged | unchanged |
| `lane_task_kinds` | unchanged | unchanged |
| `lane_task_kinds_detail` | unchanged | unchanged |
| `lanes` | unchanged | unchanged |
| `ledger` | changed | the v5 scope name; path and limits unchanged |
| `ledger_baseline` | changed | re-read at this freeze (484 / 18 / 0 unchanged; v5 scope absent added; the rule restated for the v5 copies) |
| `ledger_detail` | changed | the creation sentence names task R43-44 and 'no v4 or v5 scope' |
| `model_identity` | unchanged | unchanged |
| `model_identity_detail` | unchanged | unchanged |
| `name` | changed | names declaration v5 (R43 trees, review45 harness) |
| `owner_conditional_decision` | changed | A-13 item 3 carried as HISTORY (verbatim unchanged): carried_as and status_at_v5_freeze (lapsed; a fresh D1/D2 required) added |
| `owner_decision_required` | added | ADDED: exactly the six check-8 steps of Verification 45 section 5, with their status at this freeze and the restated (b) |
| `plan_sources` | unchanged | unchanged |
| `policy` | unchanged | unchanged |
| `portability` | unchanged | unchanged |
| `preconditions` | changed | no_v4_run_folder replaced by no_v5_run_folder; v4 artefacts untouched added; ledger and conditional-decision pointers restated; pip freeze unchanged |
| `primary_outcomes` | unchanged | unchanged |
| `probe_population` | unchanged | unchanged |
| `project_request_bounds` | unchanged | unchanged |
| `project_request_bounds_detail` | unchanged | unchanged |
| `project_window` | unchanged | unchanged |
| `project_window_detail` | unchanged | unchanged |
| `provider` | changed | owner-confirmable: the v5 scope |
| `provider_env` | changed | AI_LEDGER_SCOPE = the v5 scope; every other value unchanged |
| `r_and_p` | unchanged | unchanged |
| `reference_set` | unchanged | unchanged |
| `reference_set_statement` | unchanged | unchanged |
| `request_path_coverage` | changed | harness rebind: the dynamic proof re-pointed to review45's tests/full junit; the drill files covered (drill_r45) |
| `resume_authorization` | repointed / rebound only | the guard module re-pointed to review45 (same bytes) |
| `resume_detail` | unchanged | unchanged |
| `resume_policy` | unchanged | unchanged |
| `retry_rule` | unchanged | unchanged |
| `reviews` | changed | Verifications 44 and 45 (verification, findings, package check) added |
| `revision_comparison_rule` | repointed / rebound only | only the review45 harness re-point (and the harness manifest's hashes) |
| `run` | changed | new stamp r32-v5 and run folder C:/t/r2x/r42-sandbox/r32-v5 (allowance, capture store, run state under it); the dry-base sentence (r45q) |
| `run_set` | repointed / rebound only | only the review45 harness re-point (and the harness manifest's hashes) |
| `run_set_sha256` | unchanged | unchanged |
| `schema` | changed | the v5 schema id |
| `scope_limitations` | unchanged | unchanged |
| `standing_status` | unchanged | unchanged |
| `standing_status_at_v4_freeze` | unchanged | unchanged |
| `status` | changed | Verification 46, the owner's option-1 choice with the restated (b) and a fresh D1/D2 pending |
| `stop_rules` | unchanged | unchanged |
| `supersedes` | changed | supersedes v4 e0a93c46...fbeb9 (frozen, never authorized, never run; its manifest named; the review43 binding superseded by the review45 manifest 9af8e07a...) plus the chain (v4, v3, v3 RUN, v2); v4's own supersedes record kept as lineage |
| `switch_names` | unchanged | unchanged |
| `task` | changed | R43-44 (A-13 item 2; Verification 44 option 1; Verification 45 section 5 item 2), ep-implementer |
| `test_exceptions` | changed | the R43V-05 exception carried; carried_to_v5 (Verification 45 R45-10) added |
| `thresholds_verbatim` | unchanged | unchanged |
| `token_thresholds` | unchanged | unchanged |
| `trees` | unchanged | unchanged |
| `trees_r43` | changed | pointer: the corrected V4-05 list is in PILOT/declaration-r32-v4 (not in this package); commits unchanged |
| `unread_page_rule` | unchanged | unchanged |
| `v4_preparation_items` | changed | pointer: the corrected list is in PILOT/declaration-r32-v4 (not in this package) |
| `verification40_items` | unchanged | unchanged |
| `verification41_items` | unchanged | unchanged |
| `verification43_items` | unchanged | unchanged |
| `what_this_run_can_show` | unchanged | unchanged |

## Protected keys and leaves (all must be unchanged, re-pointed or rebound)

- `budget`: ok
- `budget_detail`: ok
- `project_window`: ok
- `project_window_detail`: ok
- `lane_switches`: ok
- `lane_task_kinds`: ok
- `lane_task_kinds_detail`: ok
- `application_env`: ok
- `application_env_detail`: ok
- `application_ai_limits`: ok
- `decision_coverage_gate`: ok
- `decision_coverage_gate_detail`: ok
- `gates`: ok
- `resume_policy`: ok
- `stop_rules`: ok
- `estimated_usage`: ok
- `token_thresholds`: ok
- `elapsed_bounds`: ok
- `cost`: ok
- `controls`: ok
- `cross_page_identity`: ok
- `concentration_on_proposal`: ok
- `primary_outcomes`: ok
- `thresholds_verbatim`: ok
- `scope_limitations`: ok
- `probe_population`: ok
- `r_and_p`: ok
- `retry_rule`: ok
- `unread_page_rule`: ok
- `reference_set`: ok
- `cohort`: ok
- `evaluator`: ok
- `emission_rules`: ok
- `interpretations`: ok
- `switch_names`: ok
- `lanes`: ok
- `what_this_run_can_show`: ok
- `reference_set_statement`: ok
- `trees`: ok
- `run_set_sha256`: ok
- `policy`: ok
- `plan_sources`: ok
- `executed`: ok
- `budget_approved`: ok
- `authorization_status`: ok
- `standing_status`: ok
- `model_identity.models.small`: ok
- `model_identity.models.standard`: ok
- `model_identity.provider`: ok
- `ledger.limits`: ok
- `ledger.path`: ok
- `ledger.wrap_provider`: ok
- `provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY`: ok
- `provider_env.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY`: ok
- `provider_env.AI_MAX_CALLS_PER_DOCUMENT`: ok
- `provider_env.AI_MAX_ELAPSED_S_PER_JOB`: ok
- `provider_env.AI_LEDGER_LIMITS`: ok
- `provider_env.AI_MODEL_SMALL`: ok
- `provider_env.AI_MODEL_STANDARD`: ok
- `provider_env.AI_PROVIDER`: ok
- `provider_env.AI_EFFORT`: ok
- `provider_env.AI_TIMEOUT_S`: ok
- `provider_env.AI_CLI_TIMEOUT_S`: ok
- `provider_env.AI_LEDGER_PATH`: ok
- `model_identity.cli.version`: ok
- `run_set.truth`: ok
- `run_set.labels_eval_input`: ok
- `project_request_bounds_detail.EP-27331`: ok
- `project_request_bounds_detail.all_projects_structural`: ok
- `project_request_bounds_detail.all_projects_planning`: ok
- `project_request_bounds_detail.required_application_minimum`: ok
- `resume_detail.invocations_expected`: ok
- `resume_detail.rule`: ok
- `resume_detail.resume_invocations.EP-27331_full`: ok
- `resume_detail.resume_invocations.last_invocation_starts_after_s`: ok

## Changed, added and removed leaves

### changed (69)

- `authorization.invocation.harness_copy`
- `authorization.invocation.run`
- `authorization.path`
- `authorization.runbook`
- `authorization.two_hash_procedure.budget_authorization_names`
- `authorization.two_hash_procedure.run_file`
- `binding_manifest_sha256`
- `bound_files_rehashed.harness_nodes_rebound`
- `bound_files_rehashed.rule`
- `declared_at_utc`
- `disclosures`
- `forbidden_after_authorization`
- `harness.accepted_by`
- `harness.binding_manifest.entries`
- `harness.binding_manifest.path`
- `harness.binding_manifest.sha256`
- `harness.binding_manifest.supersedes`
- `harness.bound_code_used_as_is`
- `harness.package`
- `harness.package_check.path`
- `harness.package_check.sha256`
- `harness.package_manifest.path`
- `harness.package_manifest.sha256`
- `ledger.scope`
- `ledger_baseline.rule`
- `ledger_detail.creation`
- `name`
- `preconditions.ledger_baseline`
- `preconditions.owner_conditional_decision`
- `provider.owner_confirmable.ledger.scope`
- `provider_env.AI_LEDGER_SCOPE`
- `request_path_coverage.dynamic.junit.path`
- `request_path_coverage.dynamic.junit.sha256`
- `request_path_coverage.dynamic.result.tail`
- `run.allowance`
- `run.base_justification`
- `run.capture_store`
- `run.folder`
- `run.run_state`
- `run.stamp`
- `schema`
- `status`
- `supersedes.binding_manifests.rule`
- `supersedes.binding_manifests.superseded_by.path`
- `supersedes.binding_manifests.superseded_by.sha256`
- `supersedes.declaration.path`
- `supersedes.declaration.sha256`
- `supersedes.differences`
- `supersedes.lineage.declaration.path`
- `supersedes.lineage.declaration.sha256`
- `supersedes.lineage.differences`
- `supersedes.lineage.lineage.declaration.path`
- `supersedes.lineage.lineage.declaration.sha256`
- `supersedes.lineage.lineage.differences`
- `supersedes.lineage.lineage.manifest.path`
- `supersedes.lineage.lineage.manifest.sha256`
- `supersedes.lineage.lineage.status`
- `supersedes.lineage.lineage.structure`
- `supersedes.lineage.manifest.path`
- `supersedes.lineage.manifest.sha256`
- `supersedes.lineage.status`
- `supersedes.lineage.structure`
- `supersedes.manifest.path`
- `supersedes.manifest.sha256`
- `supersedes.status`
- `supersedes.structure`
- `task`
- `trees_r43.corrected_v4_05`
- `v4_preparation_items.corrected_copy`

### added (92)

- `bound_files_rehashed.v4_nodes_equal`
- `harness.contracts.disclosure_amendment_draft_r45.path`
- `harness.contracts.disclosure_amendment_draft_r45.sha256`
- `harness.contracts.drill_criterion_r45.path`
- `harness.contracts.drill_criterion_r45.sha256`
- `harness.contracts.drill_diff_r45.path`
- `harness.contracts.drill_diff_r45.sha256`
- `harness.lineage.review43.accepted_by`
- `harness.lineage.review43.binding.path`
- `harness.lineage.review43.binding.sha256`
- `harness.lineage.review43.repoint_diff.path`
- `harness.lineage.review43.repoint_diff.sha256`
- `harness.modules.drill_r45.path`
- `harness.modules.drill_r45.sha256`
- `ledger_baseline.v5_scope_present`
- `owner_conditional_decision.carried_as`
- `owner_conditional_decision.status_at_v5_freeze`
- `owner_decision_required.restated_condition_b`
- `owner_decision_required.rule`
- `owner_decision_required.source.path`
- `owner_decision_required.source.section`
- `owner_decision_required.source.sha256`
- `owner_decision_required.status_at_v5_freeze.1`
- `owner_decision_required.status_at_v5_freeze.2`
- `owner_decision_required.status_at_v5_freeze.3`
- `owner_decision_required.status_at_v5_freeze.4`
- `owner_decision_required.status_at_v5_freeze.5`
- `owner_decision_required.status_at_v5_freeze.6`
- `owner_decision_required.steps`
- `owner_decision_required.steps_note`
- `preconditions.no_v5_run_folder`
- `preconditions.v4_artifacts_untouched`
- `request_path_coverage.drill_r45.evidence.path`
- `request_path_coverage.drill_r45.evidence.sha256`
- `request_path_coverage.drill_r45.files.drill_r45.path`
- `request_path_coverage.drill_r45.files.drill_r45.sha256`
- `request_path_coverage.drill_r45.files.lane_r32.path`
- `request_path_coverage.drill_r45.files.lane_r32.sha256`
- `request_path_coverage.drill_r45.files.runner_r32.path`
- `request_path_coverage.drill_r45.files.runner_r32.sha256`
- `request_path_coverage.drill_r45.global_provider_in_the_drill`
- `request_path_coverage.drill_r45.junit.path`
- `request_path_coverage.drill_r45.junit.sha256`
- `request_path_coverage.drill_r45.live_mode`
- `request_path_coverage.drill_r45.requests`
- `request_path_coverage.drill_r45.result.errors`
- `request_path_coverage.drill_r45.result.failures`
- `request_path_coverage.drill_r45.result.returncode`
- `request_path_coverage.drill_r45.result.skipped`
- `request_path_coverage.drill_r45.result.tail`
- `request_path_coverage.drill_r45.result.tests`
- `request_path_coverage.drill_r45.what`
- `reviews.verification44.path`
- `reviews.verification44.sha256`
- `reviews.verification44_findings.path`
- `reviews.verification44_findings.sha256`
- `reviews.verification44_package_check.path`
- `reviews.verification44_package_check.sha256`
- `reviews.verification45.path`
- `reviews.verification45.sha256`
- `reviews.verification45_findings.path`
- `reviews.verification45_findings.sha256`
- `reviews.verification45_package_check.path`
- `reviews.verification45_package_check.sha256`
- `supersedes.binding_manifests.v4_binding_review43.path`
- `supersedes.binding_manifests.v4_binding_review43.sha256`
- `supersedes.chain.rule`
- `supersedes.chain.v2`
- `supersedes.chain.v3`
- `supersedes.chain.v3_run_declaration`
- `supersedes.chain.v4`
- `supersedes.lineage.authorization_file.committed_as`
- `supersedes.lineage.authorization_file.never_removed`
- `supersedes.lineage.authorization_file.path`
- `supersedes.lineage.authorization_file.sha256`
- `supersedes.lineage.binding_manifests.rule`
- `supersedes.lineage.binding_manifests.superseded_by.path`
- `supersedes.lineage.binding_manifests.superseded_by.sha256`
- `supersedes.lineage.binding_manifests.task37_r43.path`
- `supersedes.lineage.binding_manifests.task37_r43.sha256`
- `supersedes.lineage.binding_manifests.v3_binding_review42.path`
- `supersedes.lineage.binding_manifests.v3_binding_review42.sha256`
- `supersedes.lineage.lineage.lineage.declaration.path`
- `supersedes.lineage.lineage.lineage.declaration.sha256`
- `supersedes.lineage.lineage.lineage.differences`
- `supersedes.lineage.lineage.lineage.manifest.path`
- `supersedes.lineage.lineage.lineage.manifest.sha256`
- `supersedes.lineage.lineage.lineage.status`
- `supersedes.lineage.lineage.lineage.structure`
- `supersedes.lineage.run_declaration.path`
- `supersedes.lineage.run_declaration.sha256`
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.carried_to_v5`

### removed (12)

- `bound_files_rehashed.v3_nodes_equal`
- `preconditions.no_v4_run_folder`
- `supersedes.authorization_file.committed_as`
- `supersedes.authorization_file.never_removed`
- `supersedes.authorization_file.path`
- `supersedes.authorization_file.sha256`
- `supersedes.binding_manifests.task37_r43.path`
- `supersedes.binding_manifests.task37_r43.sha256`
- `supersedes.binding_manifests.v3_binding_review42.path`
- `supersedes.binding_manifests.v3_binding_review42.sha256`
- `supersedes.run_declaration.path`
- `supersedes.run_declaration.sha256`

### repointed (41) and rebound (2)

- `harness.modules.lane_r32.sha256` (rebound)
- `harness.modules.runner_r32.sha256` (rebound)
- `authorization.invocation.working_directory`
- `harness.concentration_rule.code.path`
- `harness.modules.allowance_r32.path`
- `harness.modules.capture_store.path`
- `harness.modules.concentration_r32.path`
- `harness.modules.converter_r32.path`
- `harness.modules.coverage_v4.path`
- `harness.modules.dispatch_guard_r32.path`
- `harness.modules.drawings_ai_probe_r39.path`
- `harness.modules.inputs_r32.path`
- `harness.modules.labels_adapter_r32.path`
- `harness.modules.lane_judge_r32.path`
- `harness.modules.lane_r32.path`
- `harness.modules.literal_compare_r32.path`
- `harness.modules.model_identity_r38.path`
- `harness.modules.page_relations_r38.path`
- `harness.modules.preflight_r32.path`
- `harness.modules.project_bounds_r32.path`
- `harness.modules.r32_test_helpers.path`
- `harness.modules.r34_scenarios.path`
- `harness.modules.request_paths_r39.path`
- `harness.modules.request_paths_r42.path`
- `harness.modules.resume_invocations_r39.path`
- `harness.modules.run_control_r38.path`
- `harness.modules.run_set_selector_r32.path`
- `harness.modules.run_state_r38.path`
- `harness.modules.runner_r32.path`
- `harness.modules.sandbox_child_r32.path`
- `harness.modules.sandbox_ingest_r32.path`
- `harness.modules.score_bcr_r32.path`
- `harness.modules.score_lane_r32.path`
- `harness.modules.state_check.path`
- `harness.modules.stop_rules.path`
- `harness.modules.synthetic_r32.path`
- `harness.modules.tripwire_r32.path`
- `harness.modules.unread_pages_probe_r39.path`
- `harness.modules.visibility_r38.path`
- `isolation.allowed_under_forbidden.harness`
- `resume_authorization.implementation.guard.path`
- `revision_comparison_rule.implementation.path`
- `run_set.selector.path`

## v4 identifiers left in v5 (JSON path: identifiers; all inside record keys)

- `forbidden_after_authorization[20]`: r32-v4
- `harness.binding_manifest.supersedes`: f35355aa
- `harness.lineage.review43.binding.sha256`: f35355aa
- `preconditions.v4_artifacts_untouched`: declaration-r32-v4, r32-v4
- `run.base_justification[0]`: r32-v4, r43p
- `supersedes.binding_manifests.rule`: f35355aa
- `supersedes.binding_manifests.v4_binding_review43.sha256`: f35355aa
- `supersedes.declaration.path`: R32-V4, declaration-r32-v4
- `supersedes.lineage.binding_manifests.rule`: f35355aa
- `supersedes.lineage.binding_manifests.superseded_by.sha256`: f35355aa
- `supersedes.manifest.path`: R32-V4, declaration-r32-v4
- `supersedes.status`: m2-fresh-validation-r32-v4, r32-v4
- `trees_r43.corrected_v4_05`: R32-V4, declaration-r32-v4
- `v4_preparation_items.corrected_copy`: R32-V4, declaration-r32-v4
- `v4_preparation_items.source.path`: R32-V4
- `verification43_items.1_isolation_harness`: review43/scripts/harness-r32
- `verification43_items.2_binding_and_trees`: R32-V4, f35355aa
- `verification43_items.3_new_stamp_folder_scope_paths`: R32-V4, declaration-r32-v4, m2-fresh-validation-r32-v4, r32-v4
