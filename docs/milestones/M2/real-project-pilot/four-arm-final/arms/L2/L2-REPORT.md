# Arm L2 report (declaration 6c0189b3…, tag final-L2)

Evidence: `evidence-L2/` (manifest sha256 `0c8f2310b390aaad7eff28db8b21ed7f223e18f21b750f25d16155857ced6b6d`); machine report `REPORT-L2-FULL.json`.
L1 counterpart: `evidence-L1/` (manifest `e2f17c01a3c5ad2cc16183d74acefbf44e0adc01cbb363e9e421aed5288b9d47`).
Scoring is INTERIM: the frozen scorer v4 with evaluator .9, AI disabled, over A + L1 + L2 (`interim-score-L2/`). The final scoring runs after all arms.

1. **Status:** completed. The breaker was never opened, there was no terminal stop and nothing was deferred. Run 16:09:46–16:32 UTC.
2. **Requests:** 64 sent (all settled) of 160. None was refused before dispatch by the ledger, the rolling counter or the durable allowance. 4 reader calls were refused before dispatch by the application's per-document elapsed-time budget (D26 p4 identity and revision, D19 p3 region discovery, D22 p3 page discovery); they consumed no tokens. 96 requests remain usable, but L2 has no pending work.
3. **Tokens (ledger):**

| | Requests | Input | Output |
|---|---|---|---|
| Provider-reported actual | 62 | 648,129 (of which cached 409,162) | 85,097 |
| Estimated charge, unknown usage (2 timeouts) | 2 | 22,786 | 1,600 |
| Ledger total accounted | 64 | 670,915 | 86,697 |
| Pre-dispatch estimates, all requests | 64 | 1,197,581 | 216,764 |

   The ledger's actual input equals the application's recorded input including cached input (648,129 both).
4. **Largest request:** ledger id 314, region discovery, 50,287 input / 6,923 output (34,080 cached, 6 turns, 66.8 s). Below both per-request thresholds (70,000 / 20,000). No request crossed any threshold.
5. **Events in order:** 16:13:27 provider timeout (id 302, region discovery); 16:15:26 provider timeout (id 303, region discovery). No breaker, no terminal stop. Consecutive failures at the end: 0.
6. **Grouping:** fully processed 23 documents; partially processed 3 (D19, D22, D26: one or two calls refused by the per-document time budget); budget-stopped 0; deferred 0; not attempted 1 (D27, the Word control, unsupported input). Every project was processed.
7. **Coverage (in-scope pages: 42; pages beyond the reader scope retained: 54; Word control retained):**

| Field | Documents usable on all in-scope pages (of 27) L1 → L2 | In-scope pages completed read L1 → L2 | Usable (read or verified absence) L1 → L2 |
|---|---|---|---|
| Identity | 6 → 12 | 8 → 15 | 9 → 16 |
| Revision | 5 → 11 | 5 → 12 | 8 → 16 |
| Decision | 7 → 7 | 1 → 6 | 11 → 15 |

   L1 is confounded by its breaker stop: 9 L1 documents were budget-stopped and 11 in-scope pages were never attempted. Decision pages located but unread (located_incomplete) in L2: 9; not coverage.
8. **Critical and held:** the scorer lists **one critical acceptance**: D26 (EP-16830 CCTV specification, a control with confidence medium on the declared uncertainty list) page 2, revision "00" validated on a no-record page. The declared stop rule covers resolved labels only, so the runner's tripwire did not stop the arm; it is reported, not hidden. Held: 12 held correct, 4 held wrong (identities of D04, D06, D12, D19 p2), 7 held on no-record pages (D03, D21, D26). Observed deterministic error (not AI): D15 revision "00" vs R1 (the same in L1).
9. **Matched L1/L2 (fields completed-read in both on all in-scope pages):** identity 3 documents (D04 missed in both; D12 recovered in both; D24 held in L1 → recovered in L2), revision 1 (D04 recovered in both), decision 1 (D04 held in both). 22 documents were attempted by both arms, but so few were read in both that the pair is **INCONCLUSIVE** by the predeclared rule (fewer than 12). Whole-sample coverage is in item 7.
10. **No change:** business rows and document roles equal the A base (scorer check true); the 27 staged files and their manifest re-hash equal; every row's source hash equals the planned hash. The runner wrote only its sandbox `C:/t/r2x/runs/final-L2/db`; no production database, live service, `.env` or source folder was written.
11. **ROI decision-coverage gate:** **not cleanly evaluable.** Of the 7 decision pages only 2 were attempted by both arms (D04 read in both; D19 not selected in both); L1's breaker removed D22. By the rule L2 3 ≥ L1 2, but that is driven by D22, which L1 never reached. On the crop-eligible pages: **D16** L1 discovery said absent (a false absence; a decision is printed), L2 not attempted; **D17** L1 failed, L2 not attempted; **D18** L1 not attempted, L2 located but unread. Neither arm read a decision on D16–D18.
12. **Scope:** `m2-four-arm-final-2026-10-01-L2`, limits equal the declared ones, created 16:09:46 UTC, expires 2026-10-05 16:09:46 UTC, breaker clear, 64 entries settled, 0 in flight. No resume is needed or permitted: nothing is pending.
