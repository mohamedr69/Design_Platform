# Arm L3 report (declaration 6c0189b3…, tag final-L3: whole-page discovery, targeted reads on)

Machine reports: `REPORT-L3-FULL.json`, `REPORT-L3-EXTRA.json`, `REPORT-L3-1.json`. Evidence: `evidence-L3/` (manifest in the run log).
Scoring is INTERIM: the frozen scorer v4 / evaluator .9, AI disabled, over A + L1 + L2 + L3 (`interim-score-L3/`). Final scoring and any label adjudication wait for L4. Labels r26.2 were not changed; D26 truth is untouched.

1. **Final state:** completed, 17:17:23–17:48 UTC. Breaker never opened; no terminal stop; nothing deferred.
2. **Requests:** 66 dispatched (all settled). Refused before dispatch: 0 by the ledger, rolling counter or durable allowance; 12 reader calls by the application's per-document elapsed-time budget (1 of them a targeted read). Cache hits 0. Usable allowance left: 114 of 180 (nothing pending).
3. **Tokens (ledger):**

| | Requests | Input | Output |
|---|---|---|---|
| Provider-reported actual | 63 | 711,471 (cached 438,103) | 104,982 |
| Estimated charge, 3 timeouts with unknown usage | 3 | 136,632 | 32,610 |
| Ledger total accounted | 66 | 848,103 | 137,592 |

4. **Largest request:** ledger id 393, page discovery, 41,265 input / 3,790 output. Largest output: id 364, 9,836. No threshold breach, no breaker event. Provider timeouts (page discovery): 17:23:29 (id 365), 17:32:26 (id 384), 17:38:30 (id 400); never consecutive (0 at the end).
5. **Documents:** fully processed 18; partially processed 8 (D01, D08, D15, D17, D18, D19, D22, D26: one to three calls refused by the per-document time budget); budget-stopped 0; deferred 0; unsupported 1 (D27, Word control); not attempted 0.
6. **Coverage** (27 documents, 42 in-scope pages, 54 beyond-scope pages and the Word control retained):

| Field | Documents usable on all in-scope pages L1 / L2 / L3 | In-scope pages completed read L1 / L2 / L3 | Usable pages (read or verified absence) L1 / L2 / L3 |
|---|---|---|---|
| Identity | 6 / 12 / 13 | 8 / 15 / 16 | 9 / 16 / 18 |
| Revision | 5 / 11 / 11 | 5 / 12 / 10 | 8 / 16 / 15 |
| Decision | 7 / 7 / 16 | 1 / 6 / 5 | 11 / 15 / 22 |

   Documents required-complete: L1 4, L2 4, L3 11. L3's decision usability is mostly "absent by discovery" (17 pages), which includes a false absence on D18 (a decision is printed). Matched L1/L3 population: see item 11.
7. **Targeted reads (the X effect):**
   - Attempted: 11 targeted calls; 10 dispatched, 1 refused before dispatch by the time budget (D15 p1), 0 cache hits.
   - Fields completed by a targeted read that the primary had not completed: 4 (D07 identity, D12 revision, D23 identity, D23 revision).
   - Correct values recovered on those: 1 validated correct (D07 identity "ELEC-B11-PAVA-101"); 1 held correct (D23 identity); D12 and D23 revision produced no scored own-revision emission.
   - Wrong values accepted: 0.
   - Held correct / held wrong on fields with a targeted read: held correct 4 (D09, D21, D23, D24 identity), held wrong 3 (D04, D06, D12 identity; D06 and D12 hold the same wrong values in L2, which has no targeted reads).
   - Targeted calls that changed nothing: 6 (re-reads of identities the primary had already completed: D04, D06, D09, D12, D21, D24).
   - 17 further fields recorded no targeted read because the primary failed or was refused, or the per-document budget was spent.
8. **Critical acceptances:** none in L3 (scorer and tripwire). For the record, L2's one critical acceptance (D26 p2 revision) is on a document on the predeclared uncertainty list (confidence medium); L1 had none.
9. **D26 page 2 revision:** L3 emitted "00" as an own revision **candidate**, not validated: the read did not complete (incomplete: no region), there was no region and no source text ("discovery only: no blind reading of the region"); the targeted read was not attempted (per-document budget). Evidence role: own revision, from discovery only. Frozen-label outcome: **held on a no-record page** (not a critical acceptance). For comparison: L1 held "Rev. 00 – Sep. 2018" (held on no-record page); L2 validated "00" from the text of the running footer region (critical). No relabelling or post-result adjudication was done.
10. **Decision pages** (all resolved labels):

| Page | Label | L1 | L2 | L3 |
|---|---|---|---|---|
| D04 p1 | approved as noted | read, held correct (ANN) | read, held correct | read, held correct |
| D16 p1 | approved as noted | absent by discovery (false) | not attempted | not attempted |
| D17 p1 | approved as noted | failed | not attempted | time budget refused |
| D18 p1 | approved as noted | not attempted | located, unread | absent by discovery (false) |
| D19 p1 | rejected (C. Revise & Resubmit) | not selected by policy | not selected | not selected |
| D19 p2 | UR | no region | read, no emission | no region |
| D19 p3–p4 | UR | budget | not attempted / budget | not attempted |
| D22 p1 | approved as noted | not attempted | read, **validated correct** | read, **validated correct** |
| D22 p2 | approved as noted | budget | read, no scored emission | not attempted |
| D22 p3 | n/a | budget | not attempted | not attempted |
| D22 p4 | UR | budget | budget | budget |

   Decision recovery on D16–D18 (the crop-eligible pages) is zero in every arm so far.
11. **L1 versus L3:**
   - Whole sample: see item 6 (every unattempted document and page retained).
   - Matched fields read in both arms: identity 3 documents (D04 missed in both; D12 recovered in both; D24 held in both), revision 1 (D04 recovered in both), decision 1 (D04 held in both). No difference on any matched field.
   - Gain attributable to targeted reads: at most 4 field completions and 1 correct validated value (D07 identity); no wrong value accepted; most of L3's coverage advantage over L1 comes from L1's breaker stop (11 in-scope pages never attempted in L1), not from targeted reads.
   - Required matched sample: **not reached** (14 documents with some read in both, but at most 3 per field read in both; the plan needs 12). The pair is INCONCLUSIVE.
   - Limitations: L1's breaker; run-to-run model variation (every dispatched response in every arm was claude-sonnet-5, the "sonnet" alias rows are timeouts with no model reported; no "opus" escalation was used), visible in the same model giving D04 identity "FA-101-106" in L2 and "FA-101-10" in L3, and D26 p2 validated in L2 but held in L3.
12. **No change:** business rows and document roles equal the A base; staged files and their manifest unchanged; every row's source hash equals the planned hash; the runner wrote only `C:/t/r2x/runs/final-L3/db`; no production database, live service, `.env` or source folder was written.
13. **Scope:** `m2-four-arm-final-2026-10-01-L3`, limits equal the declared ones, created 17:17:23 UTC, expires 2026-10-05 17:17:23 UTC, breaker clear, terminal state none, 66 entries settled, 0 in flight. No resume is needed or permitted (nothing pending).
