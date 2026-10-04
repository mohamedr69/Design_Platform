# Status after Independent Review 20, and H-06 (2026-09-30)

## Status, stated separately

1. **R19 corrections: ACCEPTED** by Review 20 (R19-01 and R19-02, on scratch candidate `69ee759`, within the reviewed scope). They are not reopened here.
2. **E (located title-block discovery) remains EXPERIMENTAL and is NOT approved as the default reader.** It leaves consultant decisions outside the title block unread (reported as unknown, never absent), so it fails the decision-coverage gate as designed.
3. **H-06: PENDING.** The live refusal is saved; no dispatch, no ledger entry, no allowance opened. Details below.
4. **Accuracy is unresolved, and so is label uncertainty.** Labels are AI-drafted or AI-reviewed and provisional; no human signature is implied. The seven-document continuation (identity S 2 → T2 5, revision 3 → 5) remains provisional. Its gain is mostly rotation-correct support, and it shows no incremental benefit of targeted calls.
5. **M2 is NOT accepted.** It remains CHANGES STILL REQUIRED. There is no variant adoption, production integration or M3.

## H-06 (the already-declared control)

**Binding, unchanged:**
- declaration `7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3`;
- runner `cont_boq.py`, the accepted `3d5607d` BOQ reader, the queue, the r16.1 matcher and replay;
- the H-06 sheet, extraction and labels.

The newer document-reader candidates are not bound into the control.

**Live check at 2026-09-30 17:11:10 UTC** ([h06/](h06/)):

| Item | Value |
|---|---|
| Durable ledger, original experiment | 104 / 150 settled; 0 open reservations; 46 left, of which 24 reserved for H-06 |
| H-06 ledger scopes | no entries |
| Exclusive H-06 allowance store | never opened (both arms have their full 12) |
| EP-8430 rolling day | **60 / 60 used**: neither arm fits |
| Frozen runner | invoked, **refused before any request**: "EP-8430 rolling-24-hour allowance cannot fit this arm now (60/60 used)" |

**Eligibility by the live counter at that check:** one 12-request arm from **2026-09-30 18:53:56 UTC**; both arms from **18:55:20 UTC**. The same result was recorded at 14:49:52 and 15:26:47 UTC.

This is a reading of the counter, not an authorization. The next run must repeat the preflight ([H06-RUNBOOK.md](H06-RUNBOOK.md)). No automation was scheduled and nothing waited for the window.

**What completion will and will not show:**
- **The queue:** the frozen BOQ-T queue puts held rows first and cannot reach H-06's three wrong accepted rows within 12 requests. That will be reported as observed, with reached / unreached rows and no inferred detection.
- **Scope:** completion closes the experimental control only, not M2 accuracy or general safety.

## Prospective experiment

See [EXPERIMENT-DRAFT.md](EXPERIMENT-DRAFT.md). It is DRAFT / NOT EXECUTED. It isolates:
- G, rotation clipping and OCR fallback, offline on identical captured responses;
- ROI and X, as live 2×2 contrasts with G, the support policy and the deadline policy held common;
- D, as an optional separate arm.

It adds a decision-coverage adoption gate, page / field-aware fail-closed coverage, equal-budget comparisons with known and estimated token accounting, and a workload table:
- **Core design:** about 234 expected requests, cap 280, about 3.0M input tokens.
- **Price:** unknown, so no dollar figure.

A budget decision is requested only after that draft is reviewed.
