# ORCH-08 / R38HARNESS-IMPL progress (UTC)

- 2026-10-03T18:20Z start. Read NEXT-BOUNDED-TASK (ORCH-08), AUTHORITY-REGISTER (A-06, A-09), Verification 38 (R38-07..R38-16), findings R34-06, R35-06..R35-10, R36-07, R36-09, R37-04.
- 2026-10-03T18:25Z hashes recomputed, all equal: review36 manifest 5e950813 (135/135, 0 bad), BINDING-MANIFEST-R36 5a1a6aad, declaration-r32 manifest 59361b93 (56/56) and declaration 38e08df9, evaluator-offline-r32 manifest 86dd81d3 (25/25), SYNTHETIC-PREDICTIONS 9f3e0e56, RUN-SET-PROPOSAL 9058f3d6, TRUTH-R32 4e237a4e, reviewed-2 89c60e9d, response ledger 664fc295, candidate HEAD a8aacedd clean, AI ledger 483/17 (mode=ro).
- 2026-10-03T18:26Z work folder created; review36/scripts/harness-r32/* (40 files) copied to r38/harness-r36-base/ (frozen reference) and r38/harness-r32/ (development).
- 2026-10-03T18:38:42Z `claude --version` run once: `2.1.263 (Claude Code)`.
- 2026-10-03T18:40Z evidence/SNAPSHOT-BEFORE.json (read-only snapshot of the frozen trees).
- by 2026-10-03T19:10Z (development, not yet integrated):
  - change 5: page_relations_r38.py (rule CP-R38), lane_judge_r32.py, tripwire_r32.py; test_lane_judge_r32.py rewritten (21 pass); test_literal_compare_r32.py: one judge-level expectation updated for the 25 formerly forgiven controls (48 pass). What-if pending.
  - change 1: project_bounds_r32.py (EP-27331 planning 63.0, structural 154; required application per-project limit 84). Tests pending.
  - change 3: model_identity_r38.py (pins claude-sonnet-5 / claude-opus-5). Tests pending.
  - changes 2/4: allowance_r32.py rewritten (parent budget, lane allowances, rolling window, refusals, durable stops, audit, CLI); test_allowance_r32.py rewritten (16 pass); run_control_r38.py (gate, deferral, recorder, controller, dry stub, probe).
  - preflight_r32.py contract 3 (declared sandbox base); test_preflight_r32.py rewritten (70 pass); lane_r32.py, runner_r32.py, score_lane_r32.py, score_bcr_r32.py rewritten; run_set_selector_r32.py replacement refusal; sandbox_child_r32.py base parameterised; r32_test_helpers.py contract-3 declarations. Runner/lane integration not yet run.

- by 2026-10-03T19:31Z (integration): run_state_r38.py split out of run_control_r38.py (the runner never imports the application);
  runner/lane integration runs end to end (dry, reader none; synthetic application path); deferral + resume until finished verified
  in scratch runs (C:/t/r2x/r38-sandbox/try-*). Tests written and passing in development runs: test_project_bounds_r32 (9),
  test_model_identity_r38 (8), test_score_bcr_r32 (39), test_run_set_selector_r32 (9), test_runner_r32 (40), test_visibility_r38
  (12, after two fixes: injections apply to invocation 1 by default; the bound-passed scenario timing), test_run_control_r38 (10,
  from the candidate tree), carried modules (58).

## Changes (status)
1. project bounds + compatible limits: code + tests pass; PROJECT-REQUEST-BOUNDS.json to generate for the package
2. visible refusals + rolling-window deferral: code + tests pass (runner, visibility, run control)
3. model identity pin: code + tests pass
4. parent budget + lane allowances + audit: code + tests pass (allowance, visibility drills)
5. cross-page identity: code + tests pass; what-if (CROSS-PAGE-WHATIF.json) pending
6. unsupported-control shortfall: code + tests pass
7. R/P no credit: code + tests pass
8. visibility proof (dry exercise + VISIBILITY-REPORT.md): pending
9. carry/tests/records/manifests/response append: pending

## Interruption and resume
- ~2026-10-03T19:40Z interrupted by the account usage limit (coordinator).
- 2026-10-04T07:39:51Z resumed; every frozen input hash recomputed and equal (AUDIT-LOG.md); AI ledger 483/17/0; candidate and baseline clean.
- Remaining at resume: freeze the harness; PROJECT-REQUEST-BOUNDS.json; CROSS-PAGE-WHATIF.json; visibility exercise + VISIBILITY-REPORT.md; full junit test run; package review38 (docs, binding, check, manifest); response-ledger append.
- 2026-10-04T07:41Z harness frozen (FREEZE-1, 50 files); full suite 392 tests / 20 modules, 0 failures, 0 guard refusals (out/tests-1).
- 2026-10-04T07:44Z CROSS-PAGE-WHATIF.json done (356 changed target verdicts on 89 fixtures; 40 fixtures keep an evidenced association); PROJECT-REQUEST-BOUNDS.json done (a90ecd1b).
- 2026-10-04T07:50Z visibility exercise running; docs drafted in r38/docs (LIVE-RUN-CONTRACT v3, SCORER-CHANGES v3, CHANGE-RECORD); binding / assemble / verify / append scripts next.
- 2026-10-04T07:55Z scripts written: make_diffs_r38, make_binding_r38, assemble_review38, verify_review38_package, write_manifest_r38, append_response_r38, visibility_exercise_r38; docs: CHANGE-RECORD (sections 1-11), SCORER-CHANGES v3, LIVE-RUN-CONTRACT v3, COMMANDS. Visibility exercise running (8 of 12 scenarios ok so far).
- 2026-10-04T07:55:28Z visibility exercise done: 12 scenarios, every injected event visible in the four places, 0 model requests, AI ledger 483/17/0 unchanged, no re-send.
- 2026-10-04T07:56Z package assembled (PILOT/review38, 126 files); BINDING-MANIFEST-R38.json 4c2904cd...; PACKAGE-CHECK all 13 checks ok.

## Changes (final status, 2026-10-04T07:57Z)
1-9: done (code, tests 392/392 pass, outputs, docs, binding, check). Remaining: the evidence manifest (last) and the one response-ledger append.
