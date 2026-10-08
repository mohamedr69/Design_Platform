# M6 merge and conditions (ORCH-049)

Role: ep-implementer (Claude Opus 5.5, high effort), fresh and isolated. Authority: A-12, A-13 item 5, A-15 item 1.
Inputs: the ORCH-049 card; `MR/reviews/U2-M6-verify/INDEPENDENT-VERIFICATION.md` and `FINDINGS.json` (ORCH-048:
PASS WITH CONDITIONS, C1-C3, U2M6V-01..16). Date: 8 October 2026.

## Preconditions

- `roadmap/u2` HEAD was `b3c4949` (a session-log commit on top of `895167b`). It contains the ORCH-047 merge `55c4891`.
  The backend tree from `55c4891` to `b3c4949` is unchanged: only `docs/milestones/M5` and a session log changed.
- `task/m6-merge` was branched from `b3c4949` in the worktree `G:/dev (2)/dev/ep-platform-merged/wt-m6b`. Nothing was
  written to `ep-platform/`, `roadmap-u2/` or any other worktree.
- The baseline is the ORCH-047 merged-tree full run (`C:/t/tmp/owner-work/merged-full.xml`, tree `c865993a`). It is
  copied here as `evidence/merge-and-conditions/baseline-orch047-merged-full.xml`.

## Commits (on `task/m6-merge`; no merge into `roadmap/u2`, no push)

| Commit | What |
|---|---|
| `f95e66e` | merge of `task/m6-attribution` (`564c4fa`), conflict resolved (Part A) |
| `980f9a3` | Part B: C2, C3, U2M6V-03/-04/-07, docs |
| evidence commit | this report and `evidence/merge-and-conditions/` |

## Part A: the merge and condition C1

The only conflict was in `backend/app/services/document_classification.py`, in two places.

- **`record()`**
  - Both parameter sets are kept: `extra` from the owner, and `confirmed_by_id`, `attribution` and `stage_record`
    from M6. The new keyword is `skip_unchanged_history` (Part B).
  - `data = {**assessment.to_dict(), **(extra or {})}` is built before M6's no-op comparison and the insert, so the
    owner's F-02 one-INSERT guarantee holds.
- **`review_reasons()`**: both reasons are kept, the owner's `AI_REVIEW_REASON` first and then M6's
  attribution-conflict reason.
- **AI pass** (`document_classification_ai.keep()`)
  - It now passes `stage_record = {model, prompt_version, page_chars, producing_job_id}`. `run()` takes `job_id`
    from `ctx`.
  - A reused answer carries its original model, prompt version and page size, which follows the F-03 rule.
  - A conflict the pass raises therefore records `version = prompt_version`, not the rules version.
- **Alembic**: there is one head, `c6d8e0f2a4b6`, whose down-revision is `e6a8c0b2d4f6`. No merge migration was needed.
- **Targeted run at the merge commit**: 207 passed. The run covered classification v2, pilot and evidence; routing;
  m6_attribution (26); classification_ai; drawings_chat and drawings_module; processing_v2; migrations;
  worker_runtime; document_sync; file_sync_v2_processing; projects; and repair_tool.

## Part B: conditions and findings

Before means the merge commit `f95e66e` with the new test file added. After means `980f9a3`. Logs and XML are in
`conditions-before.*` and `conditions-after.*`.

| Item | Change | Test(s) in `test_m6_merge_conditions.py` | Before | After |
|---|---|---|---|---|
| C1 | stage-record hand-through (Part A) | `test_the_ai_pass_fills_the_stage_record_and_its_conflicts_carry_the_prompt_version` | pass (Part A already in) | pass |
| C2 / V-01 | test only (the code was already correct) | `test_an_ifc_drawing_type_outside_the_given_folders_never_claims_our_scope` (6 parametrised cases), `test_a_models_ifc_answer_outside_the_given_folders_is_stored_as_not_ours` | pass; under mutation N1c, **7 fail** (`mutation-n1c.json`, file restored byte-equal) | pass |
| C3 / V-02 | the harness reads a model answer through the live pass's own `_assessment` (`review_only_assessment`), so it is never supported; the stored arm caps a stored `ai` row marked supported to `hint` and counts it; `by_source` is added to every report; `HARNESS_VERSION` .2 | `test_the_harness_ai_arm_is_review_only_and_reports_each_source`, `test_the_harness_and_the_live_pass_read_a_model_answer_the_same_way` (15), `test_the_harness_stored_arm_caps_a_stored_ai_answer_and_reports_each_source` | 17 fail | pass |
| V-03 | `_same_side()`: an attribution claim on the engineer's side is no conflict; only an opposite-side claim is | `test_a_weaker_claim_on_the_same_side_is_no_conflict_and_an_opposite_side_claim_is` | fail (1 extra conflict) | pass |
| V-04 | `record(skip_unchanged_history=True)` in the backfill | `test_after_a_rules_bump_a_confirmed_row_is_re_marked_once_not_on_every_backfill` | fail (rows 4, 5, 6) | pass (4, 4, 4; assessed 3, 0, 0) |
| V-07 | `attribution_stale()` compares the stored `input_fingerprint` with the current one; it is shown in the read model and metrics; the no-op comparison includes it; the backfill re-attributes a stale rules row once and never replaces a current model answer to do so | `test_a_changed_input_fingerprint_marks_the_attribution_stale_and_the_backfill_re_attributes_once`, `test_the_backfill_never_replaces_the_models_answer_to_re_attribute_it` (added after the before run) | fail (`KeyError attribution_stale`) | pass |

**Two M6 assertions changed** with the behaviour the card orders:

- In `test_a_later_confirmation_...`, the recorded conflict fields go from `{"attribution", "system_code"}` to
  `{"system_code"}` (V-03).
- In the AI-arm harness test, `false_supported_rate` goes from 1/2 to 0/0 (C3).

**Docs**

- `DOCUMENT_CLASSIFICATION_V2.md` gains section E: the attribution field, the confirmation endpoint, conflicts, the
  stage record, and what is not done. The B11 note now points to E2.
- `DOCUMENT_CLASSIFICATION_AI.md` gains one line on the stage-record slots.

**Synthetic harness runs** through the command line (`harness-synthetic-*.json`, `scripts/harness_synthetic.py`):

- The stored arm reproduces the ORCH-043 values (type 2/4, false-supported 1/3).
- The stored arm with one stored `ai` row gives `ai_supported_capped` 1 and false-supported 0/2.
- The AI arm gives false-supported 0/0 and stages `{hint, unknown}` only.

## Preserved

- These are byte-identical to `564c4fa`: `RULES_VERSION`, `Stage`, `freshness`, `context_fingerprint`, `hint`,
  `assess`, `assess_row`, `hint_rows`, `current`, `intake_of`, `is_current`, `confirm` and `input_fingerprint`.
- `document_routing.py` and `document_control.py` are unchanged. `document_processing.py` equals `roadmap/u2`.
- The role gate (admin 403), the same-transaction audit event and the rule that nothing supersedes a confirmed row
  are covered by the unchanged M6 tests, which pass.
- The owner's review-only rule, the daily cap and the F-02/F-03 tests pass.
- No M5 or M8 file was touched. The only file outside M6 and classification that changed is
  `document_sync.py`: two lines, so the project facts are computed once per listing.

## Full suite (once, on `980f9a3`)

The full run gave 1,981 tests: 1,945 passed, 1 failed, 35 skipped (34 min). The ORCH-047 baseline was 1,926 tests:
1,890 passed, 1 failed, 35 skipped.

Comparison by name and message (`full-suite-comparison.json`):

- No new failures and no missing tests.
- The one failure is the same as the baseline's, with the same message: `test_proposed_materials::...part_catalogue...`.
- 55 tests were added: 26 from M6 and 29 from ORCH-049.
- Against the M6 branch's own run, no test is missing and there is no new failure.

The final targeted run (the Part A set plus the new file) gave 236 passed.

## Open items

- The inspector UI shows none of the M6 fields: there is no `engineer` basis in `ClassificationBasis`, and the
  attribution, conflict, stage-record and `attribution_stale` fields are untyped. No frontend change was made in this
  task.
- Membership enforcement on the confirmation endpoint (B-19, B-18 confirmer; M7).
- A real database-clone harness run with GOLDEN-LABELS under A-15 item 1. This needs separate authorisation and a copy
  only. Stored `ai` rows from 7 October that were stored as supported are now capped and counted.
- Engineer attribution labels and the owner's countersignature of the kind map. The rule that a weaker same-side claim
  is no conflict is the card's decision for U2M6V-03. It also treats RELATED_EXTERNAL against REFERENCE_ONLY as
  agreement; the owner may revisit this.
- Rows written before the migration read `attribution_stale` until a backfill re-attributes them. A current answer
  from the model's pass is re-attributed only when the pass writes again.
- The SQLite savepoint caveat (U2M6V-05) and the per-call `project_facts` cost in `record()` (U2M6V-13) are unchanged.

## Evidence

The evidence is in `docs/milestones/M6/evidence/merge-and-conditions/`:

- targeted runs (at the merge and final);
- the before and after runs of the conditions tests;
- the full suite, its comparison and the baseline;
- the N1c mutation;
- the harness reports and log;
- `runs.txt` (UTC times; the after runs list `f95e66e` because Part B was still uncommitted then);
- the scripts;
- `MANIFEST.json`.

Interpreter: `ep-platform/backend/venv/Scripts/python.exe -B`, `-p no:cacheprovider --basetemp=C:/t/tmp/m6b/bt`.
No provider, model, network, live platform, database or `pip install` was used.
