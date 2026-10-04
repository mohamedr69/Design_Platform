# Round 2 small batch: per-profile metrics (deliverable 5)

> **Truth status: PROVISIONAL.** Every label behind these figures is an AI-drafted proposal. It was written from the source before any prediction existed, and **no person has reviewed it.** These figures are diagnostics. They are **not** accuracy evidence and do not support selecting a variant. No winning variant is named.

**Scope.** 12 exploration documents across 10 projects, plus the exposed EP-8430 BOQ sheet.

**Evaluator.** `m2-pilot-eval-2026-09-29.9` (unchanged) and the BOQ join of `r2x_boq.py`. Each run is scored under its **declared** context, as the accepted Review 12 re-score did it:
- `det` and profile A: no AI stage;
- B: EV1 / default;
- C: EV2 / default.

**Controls.** The same rows scored under a context they were not run in show **no** AI evidence:
- B scored as EV2: states unavailable / none, 0 asserted;
- C scored as EV1: states unavailable / none, 0 asserted;
- B with no context: `no_context`, 0 asserted.

Files: `evidence/eval/SMALL-METRICS.json`, `eval-{det,A,B,C}.json` and `DISAGREEMENTS*.json`.

**Truth coverage.** The labels hold 8 identity components, 5 readable revisions (plus 3 known-absent), **0 decisions** (8 known negatives), and 16 no-record pages. Pages beyond the 4-page reading scope are unvalidated and never scored.

## 1. Documents: per field, per profile (evidence layer)

**Recovered** means a correct value was *automatically accepted* (clean or mixed). **Held** is a correct value kept as evidence only. **Held ≠ recovered.**

| Profile | Identity recovered | Identity held (correct) | Identity missed | Revision recovered | Revision held | Revision missed | Revision known-absent correct (tn) | Decision (tn) | **Critical false accepts** |
|---|---|---|---|---|---|---|---|---|---|
| det (no model) | 4/8 | 0 | 4 | 1/5 | 0 | 4 | 3/3 | 8/8 | **0** |
| A (application AI path) | 4/8 | 0 | 4 | 1/5 | 0 | 4 | 3/3 | 8/8 | **0** |
| B (EV1) | 4/8 | **3** | 1 | 1/5 | **2** | 2 | 3/3 | 8/8 | **3** |
| C (EV2) | 4/8 | **3** | 1 | 1/5 | 1 | 3 | 3/3 | 8/8 | **2** |

**Accepted precision** is computed over distinct asserted facts, false positives on no-record pages included:

| | det / A | B | C |
|---|---|---|---|
| Identity | 4/4 | 4/5 | 4/5 |
| Revision | 1/1 | 1/3 | 1/2 |

**Measured against the goals** (reported, not claimed on provisional truth):

| Goal | Result |
|---|---|
| 0 critical false accepts | Met by det and A. **Not met by B (3) or C (2).** |
| ≥ 90 % correct automatic recovery | **Not met by any profile:** identity 50 %, revision 20 %. B and C add held-correct evidence, but hold it rather than accept it. |
| 98 % for other fields | Not measurable on this batch. |

### The critical false accepts (every one is in the worklist, with a crop)

| Profile | Document, page | Field | Accepted | Reading |
|---|---|---|---|---|
| B | EP-17428 FA MS `1-7.pdf`, p4 | identity | `Rev.0` | **A revision literal accepted as an identity.** It is wrong however the open label questions are settled. |
| B | EP-17428, p3 | revision | `0` | Depends on the open CONFIRM item: is each divider page a component (blank number, `Rev.0`)? |
| C | EP-17428, p2 | revision | `Rev.0` | The same open item. |
| B | DCH-M-MHT-CAL-IFC-ELE-0001-00, p2 | revision | `00` | The right value for the document, but the proposed label puts the component on page 1 only. Page 2 is its Document History. A label-convention question. |
| C | Previous Project List, p1 | identity | `P06/TRANS/R1` | The proposed label reads this footer as a letterhead / form code. If a person confirms that, it is a **genuine critical error.** |

**Observed, not scored as critical.** On DJ-295, B held a **wrong** identity (`DJ-286-DAJMSTBD-ASS-0117`). It was held, never accepted, and C missed the identity. The printed AMANA number is not recovered by any profile.

### By document (identity / revision; `tn` = known negative)

| Document (stratum) | det = A | B | C |
|---|---|---|---|
| DRF EP-22510 (scan) | missed / tn | **held** / tn | held / tn |
| EP-23091 EML Design (design sheet, scan) | missed / missed | held / missed | held / missed |
| DJ-295 approval drawing | missed / missed | missed / **held** | missed / missed |
| LUX calculation EP-26208 (calc) | recovered / tn | recovered / tn | recovered / tn |
| FAS-09 (shop drawing) | missed / missed | held / held | held / held |
| DCH crisis sheet EP-30549 (reply stratum) | recovered / recovered | recovered / recovered | recovered / recovered |
| EML Sam B transmittal (Word) | recovered / tn | recovered / tn | recovered / tn |
| DCH calculation EP-30549 | recovered / missed | recovered / missed | recovered / missed |

The five documents with no component are all no-record pages: TOC, MS dividers, estimation, reference list and part of the calculation. There, any accepted identity or revision is a false positive; see the table of critical accepts above.

## 2. What profile A did

**Profile A made 0 model requests.** The application's existing AI path reads only submittal-role forms, and no small-batch document was classified as one. On this batch, A's rows equal the deterministic track's.

## 3. H-06 BOQ (EP-8430, exposed), blind row verification

**The baseline** is A, AI off: 20 accepted rows, 3 critical wrong accepted quantities (H-06), and 18 held rows.

| Profile | Requests | Wrong accepted rows **caught** (conflict) | Wrong accepted **validated** | Correct accepted confirmed | Held rows: blind reading right | Held rows unread (budget) | Extra |
|---|---|---|---|---|---|---|---|
| B (EV1: held + 20 % audit) | 25 | **2 of the audited** (Numeric Keypad `4`→`1`; one row read `94`) | 0 | 5 | 17 | 0 | 1 (a "Total Price" line) |
| C (EV2: every row) | 35, stopped by the cross-track 60/day limit | **4**: all three H-06 rows (`4` → blind `1`) and the `94` row | **0** | 16 | 14 | **3** (budget stop, not a negative) | 1 |

**Reading this.**
- **EV1** caught the H-06 rows only where the 20 % audit happened to select them. One H-06 row stays accepted and unverified.
- **EV2** caught all three and validated no wrong row. It reached the project's daily limit with three held rows left unread.
- **In both profiles the catch raises a conflict. It does not correct the row.** The policy question in DEFECT-INVENTORY.md §3 stays open.
- **Truth** is the Review 05 AI-drafted label. The crops confirm the printed `1`, but that is pending a person's confirmation.

## 4. Usage, latency, cost

All requests are real-model requests, recorded as actual provider-reported usage.

| Track | Requests | Tasks | Models (actual) | Escalations | Input tokens (actual) | of which cached | Output tokens (actual) | Latency median / p90 / max (ms) | Budget stops | Wall time |
|---|---|---|---|---|---|---|---|---|---|---|
| det | 0 | – | – | – | – | – | – | – | 0 | – |
| A | 0 | – | – | – | – | – | – | – | 0 | – |
| B | 24 | discover 13, revision 6, identity 4, decision 1 | sonnet-5 ×24 | 0 | 274,806 | 159,747 | 53,755 | 13,131 / 62,933 / 213,742 | 1 (EP-23323: 120 s per-document limit) | 668 s |
| C | 29 | discover 14, revision 7, identity 7, decision 1 | sonnet-5 ×24, opus-5 ×5 | 5 | 321,420 | 197,272 | 60,245 | 12,015 / 43,839 / 177,246 | 3 (the per-document time limit) | 754 s |
| BOQ-B | 25 | BOQ row | sonnet-5 | 0 | 137,696 | – | 9,811 | median 6,833, max 9,957 | 0 | 182 s |
| BOQ-C | 35 | BOQ row | sonnet-5 | 0 | 192,767 | – | 13,914 | median 7,027, max 13,035 | 1 cross-track refusal | 261 s |

**The ledger.** Scope `r2x-small-2026-09-29`, limit 150 requests:
- **113 settled**, 0 refused by the ledger, 0 with unknown usage, breaker never opened.
- Actual input 926,689 (of which 601,065 cached), actual output 137,725, 481 provider-reported turns.
- The ledger's preflight **estimates** were 2,117,450 input and 362,598 output. The estimates are not caps: the CLI adapter has no provider-enforced token limit.

**Accounting reconciles.** The 113 ledger requests equal the fresh `ai_usage` rows over all tracks (0 + 24 + 29 + 25 + 35). No request failed. No retry was needed.

**Cost: unknown.** No trustworthy price is configured, and the CLI's notional `total_cost_usd` is not used.

**The per-project daily limit across tracks** is in `evidence/run/PROJECT-DAY-COUNTER.json`. EP-8430 reached 60 and was refused once. Every other project stayed below it.
