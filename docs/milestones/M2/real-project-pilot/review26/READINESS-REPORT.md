# Four-arm accuracy experiment — readiness for the owner's budget decision (2026-10-01)

This package follows Independent Review 26, which accepted R25-01 on harness v4.3 and found no new defect. It prepares the measurement run offline: the final declaration, frozen reference labels, the exact budget proposal and the runbook. **No model or provider request, schedule or dispatch was made.** Application code, live services and data, original documents, sealed projects, earlier packages and the R21 label skeletons are unchanged.

| Document | Content |
|---|---|
| [BUDGET-PROPOSAL.md](BUDGET-PROPOSAL.md) | the owner-facing proposal, the reconciliation of the earlier figures, enforcement, the preflight and the decision requested |
| [LABELS-SUMMARY.md](LABELS-SUMMARY.md) | label completeness, evidence, uncertainty, the off-title-block outcome and what is specifically incomplete |
| [RUNBOOK.md](RUNBOOK.md) | authorized execution and scoring: live re-checks before dispatch, deferrals, terminal stops |
| [declaration/FINAL-DECLARATION.json](declaration/FINAL-DECLARATION.json) | the frozen binding, sha256 `aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998` |
| [labels-r26/](labels-r26/) | the frozen labels and manifest |
| [bindings/SOURCE-BINDINGS.json](bindings/SOURCE-BINDINGS.json) | trees, harness, label, stage and evaluator hashes; reviewer files; earlier packages; ledger state |
| [preflight/](preflight/) · [enforcement/](enforcement/) | the scripted preflight of the exact binding; the ledger enforcement cases |
| [COMMANDS.md](COMMANDS.md) | exact commands and exit codes |

## What was done

1. **Reused the reviewed design.** The four arms (L1–L4), candidate `719e8de`, baseline `3d5607d`, the frozen 27-document sample with its long-PDF and Word controls (96 pages, 42 in scope), the evaluator .9, source / profile / variant / arm-policy binding and the off-title-block decision-coverage gate are unchanged. The declaration now binds the reviewed v4.3 runner, journal, scorer and allowance files and the two modules the A runner imports, all by sha256. It verified every one of them against the review25 package before writing.
2. **Completed and froze the reference labels.** The R21 files were skeletons ("PENDING"); nothing reusable existed. All 27 documents and 42 in-scope pages are now labelled with page, region and hash evidence. Identity, revision, decision, actor and decision location are kept distinct. Uncertainty is kept as confidence *medium* (10 documents), and nothing is taken from file names or predictions. The labels are versioned beside the skeletons and frozen (`r26-labels-2026-10-01.1`, manifest `b29d93d1…`).
3. **Produced the exact proposal.** It reconciles 509 expected / 688 enforced maximum / 1,256 structural, and shows how the limits are enforced. **One planning assumption no longer fit:** the 4-hour scope elapsed limit cannot hold the declared rolling-day deferral schedule. The revised proposal keeps every request and token cap and sets 96 h for the document-arm scopes. Cost remains unknown.
4. **Checked the binding offline.** The labels parse through the frozen evaluator, and the 6 ledger-enforcement cases hold. A scripted-provider preflight of the exact binding ran in a new disposable sandbox over the real staged sample: A, L1–L4 and the scorer all exited 0, and deferral and the terminal stop both fired as designed. The accepted Review 26 tests (100 fresh) are reused; no full suite was needed for label and documentation work.

## Status, stated separately

| Item | Status |
|---|---|
| Harness correction | **Accepted** (Review 26: R25-01 corrected; R24-01 and earlier corrections closed). No new engineering cycle was started |
| Reference labels | **Ready and frozen** for all 27 documents and 42 in-scope pages, **specifically incomplete** in two respects: (1) the second pass was by the same assistant, so the manifest's *independent* review step is still open (the independent review of this package can supply it; any change becomes `r26.2` before any prediction); (2) a strict reading of the off-title-block rule leaves a shortfall of 3 (1 of 4 screened candidates confirmed), although 6 confirmed decisions meet the minimum by count; no top-up, because the sample is frozen |
| Funding | **Pending** the owner's decision below |
| Live run | **None.** No model request, schedule or dispatch; the live ledger is unchanged at 128/150 settled with no new scope |
| Accuracy | **Not yet established** (the preflight used scripted answers) |
| Default variant | **None chosen** |
| M2 | **Not accepted: CHANGES STILL REQUIRED** |
| H-06 | complete and unchanged |

**Disclosed, not attributed:** the older discrepancy in `M2-REVIEW-RESPONSE.md` stays as Review 26 described it. Its current prefix (sha256 `182e6556…`, ending in the Review 25 append) is preserved by this task's append.

## The owner's decision

> **Approve or decline:** a new model budget of at most **688 requests** — A 8, L1 160, L2 160, L3 180, L4 180, under ledger scopes `m2-four-arm-final-2026-10-01-{A,L1,L2,L3,L4}` with 4 M input / 600 k output tokens each and an elapsed limit of 96 h per document arm (A 4 h) — on the `claude-code` provider at an unknown dollar cost. The run would use exactly the declaration `aec4d4df…`, the frozen R26 labels and the reviewed v4.3 harness, under the existing per-document (12) and per-project rolling (60 / 24 h) limits and the stop rules in the proposal.

Nothing will be scheduled or dispatched while this decision is pending.
