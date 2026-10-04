# Arm comparison: the frozen 2×2 (final, offline)

Source: [ARM-COMPARISON.json](ARM-COMPARISON.json), produced from [final-score/ARMS-METRICS.v4.json](final-score/ARMS-METRICS.v4.json) by `scripts/final_analysis.py`.

The method follows the Review 21 analysis plan:
- the document is the unit;
- resolved labels are the primary population, and unresolved labels are reported separately;
- the paired difference is in clean, correctly associated recovery, scored 0 or 1 per document and field;
- uncertainty comes from a document-cluster bootstrap with 2,000 resamples, stratified by project, seed 20261001;
- a pair is INCONCLUSIVE with fewer than 12 documents attempted by both arms, and with too few matched facts.

The scorer's technical `valid` flag only means that some eligible evidence exists. It is **not** evidence of statistical or product validity.

## 1. ROI effect without targeted reads: L1 → L2

| | Identity | Revision | Decision |
|---|---|---|---|
| Resolved documents with the fact, attempted by both | 7 | 7 | 2 |
| Matched: field read on every in-scope page in both | 3 | 1 | 1 |
| Paired difference (95% interval) | 0.00 (0.00, 0.00) | 0.00 (0.00, 0.00) | 0.00 (0.00, 0.00) |
| Unresolved differences, reported separately | D24 +1, D25 +1, D26 −1 | none | none |
| Verdict | **INCONCLUSIVE, too few matched facts** | **INCONCLUSIVE, too few matched facts** | **INCONCLUSIVE, too few matched facts** |

- **Attempted by both:** 14 documents, which reaches the 12-document minimum. The per-field resolved populations do not reach it.
- **Coverage imbalance:** L1 left 18 page-fields at budget and 33 not attempted, and attempted 16 documents. L2 left 8 and 12, and attempted 24.
- **Breaker and timeouts:** L1's breaker opened at request 287. L1 had 3 timeouts and L2 had 2. L1's stop removed D22 and three other projects from L1, so this pair is strongly biased against L1.
- **Run-to-run variation:** 6 of 31 common first readings differ. The discovery inputs differ between whole page and title block, so treatment and variation are mixed.
- **ROI decision gate:**
  - **By the predeclared rule:** L2 scores 3 against L1's 2, a pass. Every gain is on D22, which L1 never reached.
  - **Strict, completed reads only:** L2 scores 3 against L1's 1.
  - **Crop-eligible pages:** D16 has a wrong absence in L1 and is not attempted in L2. D17 failed in L1 and is not attempted in L2. D18 is not attempted in L1 and located but unread in L2.

**Conclusion: inconclusive.** The gate pass is confounded by L1's breaker.

## 2. Targeted-read effect on whole-page discovery: L1 → L3

| | Identity | Revision | Decision |
|---|---|---|---|
| Resolved documents with the fact, attempted by both | 7 | 7 | 2 |
| Matched read in both | 3 | 1 | 1 |
| Paired difference (95% interval) | 0.00 (0.00, 0.00) | 0.00 (0.00, 0.00) | 0.00 (0.00, 0.00) |
| Unresolved differences | D25 +1, D26 −1 | D26 −1 | none |
| Verdict | **INCONCLUSIVE, too few matched facts** | **INCONCLUSIVE, too few matched facts** | **INCONCLUSIVE, too few matched facts** |

- **Attempted by both:** 14 documents.
- **Coverage imbalance:** L1 left 18 page-fields at budget and 33 not attempted. L3 left 12 and 15.
- **Breaker and timeouts:** L1's breaker; 3 timeouts in each arm.
- **Run-to-run variation:** 6 of 36 common first readings differ, on the same input and the same first-read path, so this is model variation. Examples are D04 "FA-101-106" against "FA-101-10", D09 "DJ-298-…" against "DJ-296-…", and D26 footer forms.
- **X gate:** It **fails**. Resolved documents gained 0 net correct facts for 32 extra requests. Most extra requests are L1's breaker deficit, not targeted reads. There was no new false accept.
- **Targeted calls:** 10 were dispatched and 1 was refused by the time budget.
  - **Correct:** 1 completed a field with a correct validated value (D07 identity).
  - **Changed but held:** 3 changed the first reading to the value matching the truth, but the conflict kept the first, wrong value as held (D04, D06, D12 identity).
  - **Completed without a scored improvement:** 3 completed a field with the discovery value (D23 identity, held correct; D12 and D23 revision, no scored emission).
  - **Redundant:** 3 confirmed a value already read (D09, D21, D24).

**Conclusion: inconclusive. There is no evidence of benefit.**

## 3. Targeted-read effect under ROI: L2 → L4

| | Identity | Revision | Decision |
|---|---|---|---|
| Resolved documents with the fact, attempted by both | 13 | 13 | 4 |
| Matched read in both | 10 | 8 | 2 |
| Paired difference (95% interval) | 0.00 (0.00, 0.00) | 0.00 (0.00, 0.00) | 0.00 (0.00, 0.00) |
| Unresolved differences | D15 +1, D21 +1, D26 +1 | D26 −1 | none |
| Verdict | **INCONCLUSIVE, interval includes zero** | **INCONCLUSIVE, interval includes zero** | **INCONCLUSIVE, too few matched facts** |

- **Attempted by both:** 23 documents.
- **Coverage imbalance:** L2 left 8 page-fields at budget and 12 not attempted. L4 left 16 and 9. L4 completed fewer decision reads, 3 against L2's 6.
- **Breaker and timeouts:** No breaker; 2 timeouts in each arm.
- **Run-to-run variation:** 5 of 73 common first readings differ, on the same path, so this is model variation. An example is D09 discovery reading "DJ-295-P-EN-SEE-04-ASY-0020-01" in L2 and "DJ-295-O-EN-DEE-04-0001" in L4.
- **X gate:** It **fails**. There were 0 net correct facts for 2 extra requests, and a **new false accept**: D03 p1 identity "2.4 Accessories", on an uncertain label, introduced by a targeted read.
- **Targeted calls:** 8 were dispatched.
  - **Wrong:** 1 was wrong (D03).
  - **Changed but held:** 3 found the value matching the truth, but the conflict held the first, wrong value (D04, D06, D12).
  - **Supplied a value:** 1 supplied a value later held correct (D15 revision).
  - **Completed without a scored improvement:** 2 completed fields with the discovery value (D23 identity and revision).
  - **Redundant:** 1 was redundant, ending validated correct (D21).

**Conclusion: inconclusive. There is no evidence of benefit, and targeted reads introduced a false accept on an uncertain label.**

## 4. ROI effect with targeted reads: L3 → L4

| | Identity | Revision | Decision |
|---|---|---|---|
| Resolved documents with the fact, attempted by both | 13 | 13 | 4 |
| Matched read in both | 11 | 7 | 2 |
| Paired difference (95% interval) | 0.00 (0.00, 0.00) | −0.08 (−0.23, 0.00) | 0.00 (0.00, 0.00) |
| Documents that differ | none | D22 −1 (one project, EP-26208) | none |
| Unresolved differences | D15 +1, D21 +1, D24 +1, D26 +1 | D08 +1 | none |
| Verdict | **INCONCLUSIVE, interval includes zero** | **INCONCLUSIVE, interval includes zero** | **INCONCLUSIVE, too few matched facts** |

- **Attempted by both:** 23 documents.
- **Coverage imbalance:** L3 left 12 page-fields at budget and 15 not attempted. L4 left 16 and 9.
- **Breaker and timeouts:** No breaker; 3 timeouts in L3 and 2 in L4.
- **Run-to-run variation:** 10 of 64 common first readings differ. The discovery inputs differ, so treatment and variation are mixed. An example is D01 "B18" in L3 against "BSB" in L4.
- **ROI decision gate:**
  - **By the predeclared rule:** L4 scores 2 against L3's 3, so it **fails**. L3's count includes a wrong absence on D18.
  - **Strict, completed reads only:** 2 against 2, equal.
  - **D16 and D18:** L4 located both but read neither.
  - **D17:** budget-refused in L3 and not attempted in L4.

**Conclusion: inconclusive.** The predeclared ROI gate is not met. The single negative difference is one document in one project.

## Pre-ordered interpretation

The analysis plan orders the questions. ROI alone on decision coverage comes first, then targeted reads on identity and revision.

1. **ROI decision coverage:** Not established. The L1 → L2 gate pass is confounded by L1's breaker. The L3 → L4 gate fails by rule. No arm read a decision on D16 to D18. The plan expected the title-block-only reading to fail this gate.
2. **Targeted reads on identity and revision:** There is no evidence of benefit in either pair. The X gate fails twice, and one new false accept occurred on an uncertain label. The pattern with the most diagnostic value is the reader's conflict rule. Targeted reads found the true value 3 times in each targeted arm, and the conflict rule held the earlier wrong value every time.

No conclusion is promoted from an unplanned comparison, and no default follows from these results.
