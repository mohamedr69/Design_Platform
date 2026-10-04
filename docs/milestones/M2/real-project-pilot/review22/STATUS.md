# Status after the Review 22 correction task (2026-09-30)

Stated separately, as the task requires. Nothing here is self-approval; the package is submitted for independent review.

## 1. Harness correction readiness — corrected offline, awaiting independent review

- **R22-01 (source binding gates accuracy):** one eligibility contract (`harness-v4/coverage_v4.py::eligible_rows`, contract `harness-contract-2026-09-30.v4`) is applied *before* the accuracy call, the coverage, the matched subsets, the comparisons and the runner's tripwire. Mismatched or missing source hashes and evidence of another arm's context earn no credit; every planned document stays in the denominator; rejected evidence is reported; a run whose present documents are all ineligible is reported `valid_accuracy_claim = false`. The reviewer's regressions (2 failed on the submitted harness) pass on v4 (5 passed), reproduced from byte copies of the reviewer's files.
- **R22-02 (page bounds):** an emitted page is checked against the declared file's page count *and* the reader's scope, with distinct diagnostics (`page_not_in_document`, `page_beyond_reader_scope`, `invalid_page_identifier`), carried through the real scorer's output.
- **R22-03 (durable resume and rolling-day scheduling):** the reviewed r16.1 durable document allowance is integrated into the actual document-arm runner (`harness-v4/arm_ev.py`, charge before dispatch, one writer per sandbox and per document, `--resume` over the same sandbox, a new tag never recreates an allowance); the static per-arm share is withdrawn; the runner applies the declared whole-project reservation rule (`whole-project-reservation-2026-09-30.v4`) and persists deferrals with zero requests sent. Eight scenarios were exercised through the actual runner with a scripted provider and a fake clock ([runner-evidence/](runner-evidence/)).
- The corrected harness is frozen ([bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json)); the workload and draft declaration are regenerated from the implemented scheduler ([workload/](workload/), [declaration/](declaration/)).
- **No application code changed.** The frozen R21 candidate `719e8de` (scratch clone) is untouched; the accepted baseline stays `3d5607d`.

## 2. H-06 — COMPLETE, unchanged

Completed under the original frozen declaration `7b2513b2…` and accepted by Review 22. The saved outputs were replayed offline through the unchanged continuation scorer in this task: six JSON files byte-identical ([h06-replay/](h06-replay/)). No rerun was made or is proposed. The original experiment ledger is unchanged (128/150 settled; no new entry).

## 3. Budget and live execution — none

No provider or model request was made in this task (every run used the scripted dry provider under `PILOT_DRY=1`; the live ledger, the live rolling-day counter and the original documents were not touched). No live schedule exists; no cap was raised; no budget was reset; no new live scope was opened. **The 688-request proposal is NOT approved**; the corrected workload still shows it only as the proposed authorized maximum *if* approved, beside the expected 509 and the uncapped structural maximum of 1,256.

## 4. Extraction accuracy and labels — unresolved

Live extraction accuracy of the four arms is unknown (nothing ran). The R21 labels remain skeletons with a frozen manifest: AI-drafted / AI-reviewed provenance, unresolved items listed explicitly, no human sign-off claimed, no model call made to finish them. The frozen R21 sample and the sealed projects are untouched.

## 5. No chosen default — M2 CHANGES STILL REQUIRED

ROI (title-block-first) discovery and the targeted read remain experimental; no variant is adopted; ROI's disclosed decision-coverage loss stands. The R19 corrections stay accepted. M2 remains **CHANGES STILL REQUIRED**.

Requested now: independent review of this package. The owner is not asked to repeat the existing Round 2 permission; the budget decision on the experiment is for after that review.
