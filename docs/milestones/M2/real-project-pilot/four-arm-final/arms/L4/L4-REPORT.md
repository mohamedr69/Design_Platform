# Arm L4 report (declaration 6c0189b3…, tag final-L4: title-block (ROI) discovery, targeted reads on)

Machine reports: `REPORT-L4-FULL.json`, `REPORT-L4-EXTRA.json`, `REPORT-L4-1.json`, `TARGETED-L4.json`. Frozen evidence: `evidence-L4/` (manifest `0ca31663…`).
Scored by the frozen final scorer (v4, evaluator .9, AI disabled) over A, L1, L2, L3 and L4 (`final-score/`). Labels r26.2 unchanged.

## Accounting

1. **Final state:** completed, 17:51:11–18:17:52 UTC. Breaker never opened; no terminal stop; nothing deferred.
2. **Requests:** 66 dispatched (all settled) of 180. Refused before dispatch: 0 by the ledger, rolling counter or durable allowance; 8 reader calls by the application's per-document elapsed-time budget (D09 p1 identity, revision and decision; D16 p1 identity; D19 p4 region discovery; D22 p2 revision and decision; D26 p3 identity). Cache hits 0. Usable allowance left: 114 (nothing pending).
3. **Tokens (ledger):**

| | Requests | Input | Output |
|---|---|---|---|
| Provider-reported actual | 64 | 634,893 (cached 387,305) | 100,950 |
| Estimated charge, 2 timeouts with unknown usage | 2 | 23,669 | 1,600 |
| Ledger total accounted | 66 | 658,562 | 102,550 |

4. **Largest request:** ledger id 418, page discovery, 28,176 input / 1,853 output. Largest output: id 452, region discovery, 11,726. No threshold breach.
5. **Breaker, failures, terminal state:** provider timeouts on region discovery at 17:58:20 (id 434) and 18:04:35 (id 451), not consecutive. No breaker, no terminal stop.
6. **Documents:** fully processed 21; partially processed 5 (D09, D16, D19, D22, D26, each cut by the per-document time budget); budget-stopped 0; deferred 0; unsupported 1 (D27); not attempted 0.

## Coverage (27 documents, 42 in-scope pages; 54 beyond-scope pages and D27 retained)

| Field | Documents usable on all in-scope pages | Field read completed (pages) | Verified absence (no fact in truth) | Wrong absence (fact in truth) | Accepted facts: correct / wrong | Held: correct / wrong / on no-record page |
|---|---|---|---|---|---|---|
| Identity | 13 | 19 | 1 | 0 | 11 / 1 | 3 / 6 / 1 |
| Revision | 13 | 12 | 2 | 3 (D21, D24, D25) | 6 / 0 | 5 / 0 / 1 |
| Decision | 5 | 3 | 8 | 0 | 1 / 0 | 1 / 0 / 0 |

A completed read is not a recovery: correct facts recovered are the "accepted correct" column and the evaluator's clean recovery in `ACCURACY-AND-COVERAGE.json`. Decision pages located but unread (located_incomplete): 10, not coverage.

## Targeted calls (8 dispatched, 0 refused, 0 cache hits)

| Doc / page / field | Reason | Route and source region (pt) | First reading → targeted reading | Effect | Frozen outcome |
|---|---|---|---|---|---|
| D15 p1 revision (uncertain) | title block without identity; unexplained empty document | located strip, text; [2107, 1029, 2122, 1033] | (none) → 01 | changed: supplied a value | held correct |
| D12 p1 identity (uncertain) | identity without revision | located labels, text; [1446, 1500, 2274, 1512] | BH2031_DIB_AMB_ID → BH2031_DIB_AMB_ID_MAIN (matches truth) | changed | held wrong (the conflict kept the first value) |
| D23 p1 identity | identity without revision | full page; no region | discovery value confirmed | completed the field | held correct |
| D23 p1 revision | identity without revision | full page; no region | discovery value confirmed | completed the field | no scored emission |
| D04 p1 identity | form without identity; decision block unread | full page; [121, 146, 195, 160] | FA-101-106 → 17 (matches truth) | changed | held wrong (the conflict kept the first value) |
| D21 p1 identity (uncertain) | form without identity | full page; [155, 111, 196, 129] | 3561 → 3561 | redundant | validated correct |
| D03 p1 identity (uncertain) | unexplained empty document | full page; [243, 55, 305, 64] | (none) → "2.4 Accessories" | changed: supplied a value | **validated wrong: critical acceptance on an uncertain label** |
| D06 p1 identity | audit of a confident output | located labels, text; [3043, 2288, 3126, 2296] | ARC-41034 → DCH-M-BSB-DWG-ZZ-ARC-41034 (matches truth) | changed | held wrong (the conflict kept the first value) |

The call record does not store the image crop; the region is the field's final source region in page points and the route is the discovery route.

## Individual documents (frozen scores)

- **D04 p1** (resolved): decision ANN read and held correct (in every arm); identity held wrong "FA-101-106" (truth "17"; the targeted read found "17" but the conflict held the first value); revision "00" validated correct.
- **D16 p1** (resolved, decision outside the title block): decision located but not read (located_incomplete); identity held correct; revision missed.
- **D17 p1** (resolved): decision not attempted; identity and revision missed.
- **D18 p1** (resolved): decision located but not read; identity and revision missed.
- **D19** (resolved): p1 decision (C. Revise & Resubmit, normalized rejected) not selected by the reader's policy in any arm; p2 identity held wrong (truncated number); pages 2–4 decisions UR.
- **D22** (resolved): p1 decision ANN validated correct and identity "0284" validated correct; p2 identity held wrong ("MEC/SD/PR56/0284 Rev. 00"); p2 revision and decision refused by the time budget.
- **D26** (uncertain): p2 revision "00" is a **conflict** (discovery "Rev. 00 – Sep. 2018" versus first read "00", source region [422, 755, 612, 776], the running footer); the frozen evaluator associated it across pages to the page-1 record and scored it held correct; p2 identity "28 20 00" validated correct by the same cross-page association. The frozen D26 truth is unchanged; see `POST-RUN-ADJUDICATION.md`.

## No change

Business rows and document roles equal the A base (all arms); the staged files and every planned source hash are unchanged; the runner wrote only `C:/t/r2x/runs/final-L4/db`; no production database, live service, `.env` or source folder was written.

## Scope

`m2-four-arm-final-2026-10-01-L4`: declared limits, created 17:51:15 UTC, expires 2026-10-05 17:51:15 UTC, breaker clear, terminal state none, 66 entries settled, 0 in flight. No resume is needed or permitted.
