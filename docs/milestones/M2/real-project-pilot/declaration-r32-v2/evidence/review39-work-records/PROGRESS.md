# ORCH-08C R39HARNESS-IMPL progress

Task: turn review38/ into review39/ (R39-04, R39-06, R39-08, R39-16, R39-15 disclosure, R39-09 evidence, R39-02/R39-17 records).
Agent: Claude Opus 5.5 (self-reported), label R39HARNESS-IMPL. Started 2026-10-04.

## Steps
- [ ] 0. Frozen input recompute (PACKET MISMATCH check), ledger 483/17 before
- [ ] 1. Read Verification 39, review38 package, r38 work folder
- [ ] 2. Copy review38 harness to r39 work folder (harness-r32)
- [ ] 3. Change 1 REQUEST-PATHS + application_env + gate task kind/context + 1(d) proof + bounds
- [ ] 4. Change 2 unread pages
- [ ] 5. Change 3 retry policy
- [ ] 6. Change 4 capture store failed reads
- [ ] 7. Change 5 gate constant
- [ ] 8. Change 6 MODEL-ID-EVIDENCE
- [ ] 9. Tests + junit
- [ ] 10. Visibility re-run
- [ ] 11. Package review39/ docs, binding, check, manifest last
- [ ] 12. Response-ledger append; ledger 483/17 after

## Log
- 09:00Z start; frozen inputs all equal (AUDIT-LOG); harness copied (r39/harness-r38-base frozen ref, r39/harness-r32 dev).
- 09:40Z reading done (V39, review38 docs, harness). Static request-path analysis script scripts/request_paths_r39.py -> out/REQUEST-PATHS-STATIC.json:
  B reaches submittal form read (assist._call), drawings AI (_ask), baseline evidence stage (VARIANT off); C/R reach EvidenceRun.call only.
- Design decisions (to state in CHANGE-RECORD):
  * application_env = {DRAWINGS_AI_REVIEW_ENABLED: "false"} only (config.py b4fbc07f in both trees, setting drawings_ai_review_enabled).
  * lane_task_kinds derived from switches (B read_submittal_form; C 6 kinds; R 5; P = C's) bound in contract 4.
  * gate: undeclared task / missing or stale context -> CONTRACT-BREACH.json, run INVALID, never a failure-streak count.
  * unread pages: arm_policy kinds (reader cap, JobBudget, reader exception) -> COMPLETE + unread_pages.
  * retries: failed fingerprint (not dry_refused) never served; retry row (retry key) + retries table in capture.sqlite (capture_store.py unchanged);
    R mirrors C's current state by content key (contract 3 exception kept); interrupted (reserved) still served interrupted_charged.
  * retry_at_full from bounds totals (planning, structural); resume_policy full (structural basis) default / earliest.
  * gate constant DECISION_COVERAGE_GATE + definitions; declaration key decision_coverage_gate.
- 09:45Z dev suite run 2: 464 tests / 22 modules, 0 failures (before the A-10 gate edits).
- 09:52Z coordinator relayed owner decision A-10 (verified in AUTHORITY-REGISTER.md): gate C>=B only bound + mandatory C>=R diagnostic (change from plan v2, refuse R in eligibility); MODEL-ID-EVIDENCE with the owner's probe command/evidence/interpretation (probe not run); explain the failed static request-path step (audit corrected 09:58Z).
- 10:05Z A-10 gate implemented (score_bcr refuse_r_in_eligibility, c_ge_r_diagnostic, report template; preflight refuses plan-v2 gate); tests updated (score 43, preflight 82 pass).
- 10:10Z docs drafted: REQUEST-PATHS.md (incl. the failure explanation), MODEL-ID-EVIDENCE.md (probe 4.1 json / 4.2 stream-json; identity UNRESOLVED; runtime fail-closed with stated limits).
- NEXT: freeze harness, final junit run, visibility exercise, outputs (bounds, resume invocations, probes), docs (CHANGE-RECORD-R39, SCORER-CHANGES v4, LIVE-RUN-CONTRACT v4, REPORT-TEMPLATE, COMMANDS*), diffs, binding, assemble, check, manifest, response append.
- DONE (10:5xZ): frozen harness (56 files), final suite 466/22 modules 0 failures; visibility 17 scenarios ok; package review39 assembled (148 files incl. manifest); BINDING-MANIFEST-R39 a6f703b4...; PACKAGE-CHECK all_ok fad730b9...; EVIDENCE-MANIFEST 2430fa2b...; response ledger 49b4ca01 -> caf949b2...; ledger 483/17.
