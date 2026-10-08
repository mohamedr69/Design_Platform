# DECLARATION-DIFF: v3 (`9a55fa7b...1b40`, executed 2026-10-07, terminal) -> v4 (this package)

- v4 sha256: `e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9`.
- Method: both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the R43 re-point: `frozen-r12`->`frozen-r13`, `cand-r29`->`cand-r30n`, `3d5607d...`->`7ec3d2cf...`, `a8aaced...`->`436daef2...`, `review42/scripts/harness-r32`->`review43/scripts/harness-r32`), rebound (the sha256 of a re-pointed review43 harness file, equal to the hash BINDING-MANIFEST-R43-HARNESS binds), changed, added or removed.
- Top-level keys: {'unchanged': 58, 'repointed / rebound only': 7, 'changed': 22, 'added': 8, 'removed': 0}.
- Leaves: {'unchanged': 1155, 'repointed': 57, 'rebound': 13, 'changed': 56, 'added': 124, 'removed': 1}.
- **Protected values (every number and rule that must not change): ALL UNCHANGED (or re-pointed / rebound only)** (75 keys and leaves checked).
- Trees in text (R43V-13): frozen-r13 7ec3d2cf / cand-r30n 436daef2 in trees, lanes and evaluator.
- Old identifiers left in v4: 15, 15 inside record keys, 0 outside.

## Top-level keys

| Key | State | Reason |
|---|---|---|
| `application_ai_limits` | unchanged | unchanged |
| `application_env` | unchanged | unchanged |
| `application_env_detail` | unchanged | unchanged |
| `authorities` | changed | A-13 applied and summarised; the authority register re-hashed at its current (append-only) state |
| `authorization` | changed | pinned path, RUN file and scope of v4; invocation from review43 with its manifest (harness_copy, working_directory); runbook pointer (section 0 items 2, 3) |
| `authorization_status` | unchanged | unchanged |
| `binding_manifest_sha256` | changed | BINDING-MANIFEST-R43-HARNESS (review43, f35355aa...374a7) instead of BINDING-MANIFEST-R42 (section 0 item 2) |
| `bound_files_rehashed` | changed | the v4 re-hash record (v3 nodes; rebound harness nodes) |
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
| `disclosures` | changed | the dry-exercise and isolation disclosures restated for review43; ten R43-40 disclosures added (v3 result, V4-01..V4-04, R43V-04/05/09/10, pip freeze) |
| `disk_precondition` | unchanged | unchanged |
| `disk_precondition_detail` | unchanged | unchanged |
| `dispatch_order` | unchanged | unchanged |
| `elapsed_bounds` | unchanged | unchanged |
| `emission_rules` | unchanged | unchanged |
| `estimated_usage` | unchanged | unchanged |
| `evaluator` | repointed / rebound only | only the R43 re-point (and the harness manifest's hashes) |
| `executed` | unchanged | unchanged |
| `forbidden_after_authorization` | changed | two items added (the executed v3 artifacts; any harness but review43) |
| `gates` | unchanged | unchanged |
| `global_provider` | unchanged | unchanged |
| `harness` | changed | review43 (binding manifest, modules re-pointed and rebound, accepted by Verification 43); review42 added to the lineage; the re-point diff added to the contracts |
| `interpretations` | unchanged | unchanged |
| `interpreter` | unchanged | unchanged |
| `interpreter_detail` | changed | a sentence on the R43 trees added (requirements equal) |
| `invocation_order` | unchanged | unchanged |
| `isolation` | repointed / rebound only | the review43 harness folder (section 0 item 1) |
| `isolation_detail` | changed | the lane checks of this package |
| `lane_switches` | unchanged | unchanged |
| `lane_task_kinds` | unchanged | unchanged |
| `lane_task_kinds_detail` | unchanged | unchanged |
| `lanes` | repointed / rebound only | only the R43 re-point (and the harness manifest's hashes) |
| `ledger` | changed | the v4 scope name; path and limits unchanged |
| `ledger_baseline` | added | ADDED (section 0 item 4, R43V-04): 484 / 18 / 0 at freeze |
| `ledger_detail` | changed | the creation sentence names 484 / 18 / 0 (R43V-04) |
| `model_identity` | unchanged | unchanged |
| `model_identity_detail` | unchanged | unchanged |
| `name` | changed | names declaration v4 (R43 trees, review43 harness) |
| `owner_conditional_decision` | added | ADDED (section 2 item 6): A-13 item 3 verbatim, a precondition, not an authorization |
| `plan_sources` | unchanged | unchanged |
| `policy` | unchanged | unchanged |
| `portability` | unchanged | unchanged |
| `preconditions` | added | ADDED (section 0 item 9): pip freeze (R42-09), ledger, conditional decision |
| `primary_outcomes` | unchanged | unchanged |
| `probe_population` | unchanged | unchanged |
| `project_request_bounds` | unchanged | unchanged |
| `project_request_bounds_detail` | unchanged | unchanged |
| `project_window` | unchanged | unchanged |
| `project_window_detail` | unchanged | unchanged |
| `provider` | changed | owner-confirmable: the v4 scope |
| `provider_env` | changed | AI_LEDGER_SCOPE = the v4 scope; every other value unchanged |
| `r_and_p` | unchanged | unchanged |
| `reference_set` | unchanged | unchanged |
| `reference_set_statement` | unchanged | unchanged |
| `request_path_coverage` | changed | the dynamic proof re-pointed to review43's test_global_provider_r42 junit and result |
| `resume_authorization` | repointed / rebound only | the guard module re-pointed to review43 (rebound) |
| `resume_detail` | unchanged | unchanged |
| `resume_policy` | unchanged | unchanged |
| `retry_rule` | unchanged | unchanged |
| `reviews` | changed | Verification 42 and 43 (with findings and package check), RUNBOOK-ADDENDUM-R42 and the review-43 report added |
| `revision_comparison_rule` | repointed / rebound only | only the R43 re-point (and the harness manifest's hashes) |
| `run` | changed | stamp r32-v4, folder C:/t/r2x/r42-sandbox/r32-v4 (same lengths as v3); the dry-base sentence (section 0 item 3) |
| `run_set` | repointed / rebound only | only the R43 re-point (and the harness manifest's hashes) |
| `run_set_sha256` | unchanged | unchanged |
| `schema` | changed | the v4 schema id |
| `scope_limitations` | unchanged | unchanged |
| `standing_status` | unchanged | unchanged |
| `standing_status_at_v4_freeze` | added | ADDED: M4 CHANGES STILL REQUIRED, M3 accepted (standing_status carried unchanged as v3's record) |
| `status` | changed | Verification 44 and the owner's conditional decision pending |
| `stop_rules` | unchanged | unchanged |
| `supersedes` | changed | supersedes the executed v3 9a55fa7b...1b40 (its RUN file, authorization file and manifest named; the v3 binding R42 and the task-37 manifest named, superseded by the harness manifest f35355aa...); v3's own supersedes record kept as lineage |
| `switch_names` | unchanged | unchanged |
| `task` | changed | R43-40 (A-13 item 2), ep-implementer |
| `test_exceptions` | added | ADDED (section 0 item 5, R43V-05): the authorization-file test |
| `thresholds_verbatim` | unchanged | unchanged |
| `token_thresholds` | unchanged | unchanged |
| `trees` | repointed / rebound only | only the R43 re-point (and the harness manifest's hashes) |
| `trees_r43` | added | ADDED (section 0 item 2, V4-05 corrected): commits, parents, patch-id |
| `unread_page_rule` | unchanged | unchanged |
| `v4_preparation_items` | added | ADDED (section 0 item 9): V4-01..V4-05 |
| `verification40_items` | unchanged | unchanged |
| `verification41_items` | unchanged | unchanged |
| `verification43_items` | added | ADDED: the nine readiness items of Verification 43 check 8 |
| `what_this_run_can_show` | unchanged | unchanged |

## Changed, added and removed leaves

### changed (56)

- `authorities.applied`
- `authorities.register.sha256`
- `authorization.invocation.harness_copy`
- `authorization.invocation.run`
- `authorization.path`
- `authorization.runbook`
- `authorization.two_hash_procedure.budget_authorization_names`
- `authorization.two_hash_procedure.run_file`
- `binding_manifest_sha256`
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
- `isolation_detail.lane_env_checks`
- `ledger.scope`
- `ledger_detail.creation`
- `name`
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
- `supersedes.declaration.path`
- `supersedes.declaration.sha256`
- `supersedes.differences`
- `supersedes.lineage.declaration.path`
- `supersedes.lineage.declaration.sha256`
- `supersedes.lineage.differences`
- `supersedes.lineage.manifest.path`
- `supersedes.lineage.manifest.sha256`
- `supersedes.lineage.status`
- `supersedes.lineage.structure`
- `supersedes.manifest.path`
- `supersedes.manifest.sha256`
- `supersedes.status`
- `supersedes.structure`
- `task`

### added (124)

- `authorities.summary.A-13`
- `bound_files_rehashed.harness_nodes_rebound`
- `bound_files_rehashed.v3_nodes_equal`
- `harness.contracts.harness_repoint_diff_r43.path`
- `harness.contracts.harness_repoint_diff_r43.sha256`
- `harness.lineage.review42.accepted_by`
- `harness.lineage.review42.binding.path`
- `harness.lineage.review42.binding.sha256`
- `harness.lineage.review42.change_record.path`
- `harness.lineage.review42.change_record.sha256`
- `harness.lineage.review42.contract_v5.path`
- `harness.lineage.review42.contract_v5.sha256`
- `harness.lineage.review42.manifest.path`
- `harness.lineage.review42.manifest.sha256`
- `interpreter_detail.r43_trees`
- `ledger_baseline.at_freeze.entries`
- `ledger_baseline.at_freeze.limit_amendments`
- `ledger_baseline.at_freeze.scope_names_sha256`
- `ledger_baseline.at_freeze.scopes`
- `ledger_baseline.rule`
- `ledger_baseline.v3_scope_present`
- `ledger_baseline.v4_scope_present`
- `owner_conditional_decision.conditions_as_named.a`
- `owner_conditional_decision.conditions_as_named.b`
- `owner_conditional_decision.conditions_as_named.c`
- `owner_conditional_decision.kind`
- `owner_conditional_decision.source.entry`
- `owner_conditional_decision.source.item`
- `owner_conditional_decision.source.path`
- `owner_conditional_decision.source.sha256`
- `owner_conditional_decision.verbatim`
- `preconditions.ledger_baseline`
- `preconditions.no_v4_run_folder`
- `preconditions.owner_conditional_decision`
- `preconditions.pip_freeze.command`
- `preconditions.pip_freeze.distributions_record.path`
- `preconditions.pip_freeze.distributions_record.sha256`
- `preconditions.pip_freeze.rule`
- `preconditions.pip_freeze.sha256`
- `preconditions.pip_freeze.source.path`
- `preconditions.pip_freeze.source.section`
- `preconditions.pip_freeze.source.sha256`
- `preconditions.v3_artifacts_untouched`
- `reviews.review43_report.path`
- `reviews.review43_report.sha256`
- `reviews.runbook_addendum_r42.path`
- `reviews.runbook_addendum_r42.sha256`
- `reviews.verification42.path`
- `reviews.verification42.sha256`
- `reviews.verification42_findings.path`
- `reviews.verification42_findings.sha256`
- `reviews.verification43.path`
- `reviews.verification43.sha256`
- `reviews.verification43_findings.path`
- `reviews.verification43_findings.sha256`
- `reviews.verification43_package_check.path`
- `reviews.verification43_package_check.sha256`
- `standing_status_at_v4_freeze.M3`
- `standing_status_at_v4_freeze.M4 (historical M2)`
- `standing_status_at_v4_freeze.note`
- `supersedes.authorization_file.committed_as`
- `supersedes.authorization_file.never_removed`
- `supersedes.authorization_file.path`
- `supersedes.authorization_file.sha256`
- `supersedes.binding_manifests.rule`
- `supersedes.binding_manifests.superseded_by.path`
- `supersedes.binding_manifests.superseded_by.sha256`
- `supersedes.binding_manifests.task37_r43.path`
- `supersedes.binding_manifests.task37_r43.sha256`
- `supersedes.binding_manifests.v3_binding_review42.path`
- `supersedes.binding_manifests.v3_binding_review42.sha256`
- `supersedes.lineage.lineage.declaration.path`
- `supersedes.lineage.lineage.declaration.sha256`
- `supersedes.lineage.lineage.differences`
- `supersedes.lineage.lineage.manifest.path`
- `supersedes.lineage.lineage.manifest.sha256`
- `supersedes.lineage.lineage.status`
- `supersedes.lineage.lineage.structure`
- `supersedes.run_declaration.path`
- `supersedes.run_declaration.sha256`
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.cause.committed_as`
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.cause.path`
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.cause.sha256`
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.declared_exception`
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.finding`
- `trees_r43.baseline.branch`
- `trees_r43.baseline.commit`
- `trees_r43.baseline.parent`
- `trees_r43.baseline.tree`
- `trees_r43.candidate.branch`
- `trees_r43.candidate.checkout`
- `trees_r43.candidate.commit`
- `trees_r43.candidate.parent`
- `trees_r43.candidate.tree`
- `trees_r43.corrected_v4_05`
- `trees_r43.document_control_py.path`
- `trees_r43.document_control_py.sha256`
- `trees_r43.parser_version`
- `trees_r43.patch_id`
- `trees_r43.requirements_equal.all_equal`
- `trees_r43.requirements_equal.sha256.C:/t/iso/cand-r29`
- `trees_r43.requirements_equal.sha256.C:/t/iso/cand-r30n`
- `trees_r43.requirements_equal.sha256.C:/t/iso/frozen-r12`
- `trees_r43.requirements_equal.sha256.C:/t/iso/frozen-r13`
- `v4_preparation_items.V4-01`
- `v4_preparation_items.V4-01_entry.path`
- `v4_preparation_items.V4-01_entry.sha256`
- `v4_preparation_items.V4-02.path`
- `v4_preparation_items.V4-02.sha256`
- `v4_preparation_items.V4-03`
- `v4_preparation_items.V4-04`
- `v4_preparation_items.V4-05`
- `v4_preparation_items.corrected_copy`
- `v4_preparation_items.source.path`
- `v4_preparation_items.source.sha256`
- `verification43_items.1_isolation_harness`
- `verification43_items.2_binding_and_trees`
- `verification43_items.3_new_stamp_folder_scope_paths`
- `verification43_items.4_ledger_baseline`
- `verification43_items.5_authorization_file_test`
- `verification43_items.6_dry_rehearsal_real_facts`
- `verification43_items.7_reproducible_preflight`
- `verification43_items.8_guard`
- `verification43_items.9_carried`

### removed (1)

- `bound_files_rehashed.v2_nodes_equal`

### repointed (57) and rebound (13)

- `harness.modules.converter_r32.sha256` (rebound)
- `harness.modules.drawings_ai_probe_r39.sha256` (rebound)
- `harness.modules.inputs_r32.sha256` (rebound)
- `harness.modules.lane_r32.sha256` (rebound)
- `harness.modules.preflight_r32.sha256` (rebound)
- `harness.modules.project_bounds_r32.sha256` (rebound)
- `harness.modules.request_paths_r39.sha256` (rebound)
- `harness.modules.runner_r32.sha256` (rebound)
- `harness.modules.sandbox_child_r32.sha256` (rebound)
- `harness.modules.sandbox_ingest_r32.sha256` (rebound)
- `harness.modules.score_lane_r32.sha256` (rebound)
- `harness.modules.tripwire_r32.sha256` (rebound)
- `harness.modules.unread_pages_probe_r39.sha256` (rebound)
- `authorization.invocation.working_directory`
- `evaluator.file.path`
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
- `lanes.B.commit`
- `lanes.B.tree`
- `lanes.C.commit`
- `lanes.C.tree`
- `lanes.P.tree`
- `lanes.R.commit`
- `lanes.R.tree`
- `resume_authorization.implementation.guard.path`
- `revision_comparison_rule.implementation.path`
- `run_set.selector.path`
- `trees.baseline.config_py.path`
- `trees.baseline.head`
- `trees.baseline.tree`
- `trees.candidate.config_py.path`
- `trees.candidate.head`
- `trees.candidate.ledger_py.path`
- `trees.candidate.provider_py.path`
- `trees.candidate.tree`

## Old identifiers left in v4 (JSON path: identifiers)

- `disclosures[46]`: frozen-r12
- `interpreter_detail.evidence.path`: declaration-r32-v3
- `interpreter_detail.r43_trees`: cand-r29, frozen-r12
- `portability.path_lengths.evidence.path`: declaration-r32-v3
- `preconditions.pip_freeze.distributions_record.path`: declaration-r32-v3
- `run.base_justification[0]`: r32-v3
- `supersedes.authorization_file.path`: declaration-r32-v3
- `supersedes.declaration.path`: declaration-r32-v3
- `supersedes.manifest.path`: declaration-r32-v3
- `supersedes.run_declaration.path`: declaration-r32-v3
- `supersedes.status`: r32-v3
- `test_exceptions.test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests.cause.path`: declaration-r32-v3
- `trees_r43.baseline.parent`: 3d5607d
- `trees_r43.candidate.parent`: a8aaced
- `v4_preparation_items.V4-05`: 3d5607d, a8aaced
