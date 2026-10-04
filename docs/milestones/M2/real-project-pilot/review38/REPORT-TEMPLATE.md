# Report template (review38; A-09 point 5)

Every comparison report of the r38 harness carries the following text, rendered by `score_bcr_r32.report_template()` from the module constants `SCOPE_LIMITATIONS` and `NOT_CLAIMED` (every `SCORE-BCR-R32.json` also carries both fields; no argument of `evaluate` removes them).

## Scope limitations (declared; never removed)
- unsupported-control-shortfall: required 2, found 0. the run set holds 0 of the 2 unsupported-format controls plan v2 section 2.3 requires: no canonical pool document has an in-scope page labelled 'unsupported' or 'illegible' in r32-labels-reviewed-2; the shortfall is accepted ONLY as a declared scope limitation; no control is replaced once a prediction exists for the run (run_set_selector_r32.replace_controls); this limitation is never removed from a report
## Not claimed by this run
- unsupported-format safety (no unsupported or illegible control was read)
- generalization beyond the six cohort projects, their contractors and their layouts
## Reference set
- reference set independently AI-reviewed (Claude agents), not human-signed
