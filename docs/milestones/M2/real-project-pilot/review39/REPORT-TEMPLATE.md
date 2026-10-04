# Report template (review39; A-09 point 5; owner ruling A-10)

Every comparison report of the r39 harness carries the following text, rendered by `score_bcr_r32.report_template()` from the module constants `SCOPE_LIMITATIONS`, `NOT_CLAIMED`, `DECISION_COVERAGE_GATE_DEFINITIONS` and `C_GE_R_DIAGNOSTIC_RULE` (every `SCORE-BCR-R32.json` also carries `scope_limitations`, `not_claimed`, `decision_coverage_gate`, the mandatory `decision_coverage_C_ge_R` and `unread_pages`; no argument of `evaluate` removes them). With a result, the C >= R section lists the state, both lanes' counts and every document page with missing coverage and its reasons; this blank rendering lists the fields every report states.

## Scope limitations (declared; never removed)
- unsupported-control-shortfall: required 2, found 0. the run set holds 0 of the 2 unsupported-format controls plan v2 section 2.3 requires: no canonical pool document has an in-scope page labelled 'unsupported' or 'illegible' in r32-labels-reviewed-2; the shortfall is accepted ONLY as a declared scope limitation; no control is replaced once a prediction exists for the run (run_set_selector_r32.replace_controls); this limitation is never removed from a report
## Not claimed by this run
- unsupported-format safety (no unsupported or illegible control was read)
- generalization beyond the six cohort projects, their contractors and their layouts
## Decision coverage gate (CHANGED from plan v2; owner ruling A-10)
- Eligibility: C_GE_B_ONLY -- C >= B only. CHANGED from plan v2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md), whose gate was C >= B AND C >= R: the C >= R leg is removed from eligibility and kept as a mandatory diagnostic (owner ruling A-10). This is not an unchanged gate. Every other safety, accuracy and completeness gate is unchanged.
## C >= R decision coverage (MANDATORY diagnostic; never an eligibility input; no credit)
- Every report states: the state (COMPLETE, or INCOMPLETE when R did not complete its declared population, with why), the counts of C and R (coverage, completed reads, verified and wrong absences, other classes, scorable pages), whether C >= R holds (only when COMPLETE), and for every document with missing coverage in C or R: the page, each lane's coverage class, whether it is covered, and the reason.
## Pages not read under the application's own per-document limits
- A document whose pages the application did not read under its own per-document limits (the reader's call cap, the per-document JobBudget, a reader exception) stays COMPLETE; every such page is listed (result['unread_pages'] per lane) and counted as unread in every denominator. Harness and resource refusals make a document INCOMPLETE.
## Reference set
- reference set independently AI-reviewed (Claude agents), not human-signed
