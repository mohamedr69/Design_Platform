# Concentration rule v2 on the frozen run set (ORCH-07)

| | |
|---|---|
| **Rule** | `concentration-r32-2026-10-03.2`, code `concentration_r32.py` `fc5052f80ea6d2454feadb84ccc863877cdc9851921f7c4dd551c58da914dffe` (bound in `BINDING-MANIFEST-R36.json`; document `review34/CONCENTRATION-RULE-R32.md` `0affc814…80c2`) |
| **Run set** | `review34/RUN-SET-PROPOSAL.json` `9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8` (24 documents) |
| **Evidence** | `concentration/CONCENTRATION-ON-PROPOSAL.json` (`5ebc2885edb306b611a35ac2c01d5a68033dbafed052706edb8699dc5ceda215`), made by `scripts/concentration_on_proposal_r37.py` |
| **Nature** | Hypothetical gain sets over the run set's structure. Part 1 is exact combinatorics. Part 2 runs the frozen code on synthetic lanes built from the truth itself (`r34_scenarios.lane`, as Reviews 34 and 35 did). **No prediction, reader or model was used, and none of this is a result.** |
| **Reference set** | Reference set independently AI-reviewed (Claude agents), not human-signed |

## 1. The rule, as frozen

For each field, the rule looks at the **matched** documents: canonical, resolved for the field, carrying it, and attempted by both B and C. The per-document gain is g = y_C − y_B, and the net gain is the sum of g.

The field is **NOT ELIGIBLE** when any of these holds:
1. The net gain is positive and one project, one contractor or one layout key holds **more than half** of it. This applies at every size.
2. There are at least 2 failures (counted once per document), more than half of them sit in one group, and that group's own net gain is negative.
3. For decision only: C makes any false acceptance on a negative decision control.

Otherwise the field is **UNDETERMINED** when the net gain is 0 or below. This does not block on its own. It is **ELIGIBLE** when the net gain is positive.

In this cohort, contractor equals project: each project has one contractor, and `contractor_equals_project` is true. The contractor leg therefore always fires together with the project leg. Decision type and stratum are reported only.

## 2. The structure of the run set, by field

| Field | Matched projection | By project | Largest layout key |
|---|---|---|---|
| Identity | 23 | EP-26687 6, EP-27331 6, EP-22349 5, EP-3563 3, EP-29255 2, EP-15744 1 | `emaar-mirage-document-submittal` 6, then `enco-shop-drawing` 3 and `infinity-al-arabia-drawing-sheet` 3 (12 layout keys) |
| Revision | 16 | EP-27331 6, EP-26687 5, EP-3563 3, EP-15744 1, EP-22349 1 | `emaar-mirage-document-submittal` 6, then `enco-shop-drawing` 3 (7 layout keys) |
| Decision | 16 | EP-27331 6, EP-26687 3, EP-3563 3, EP-22349 2, EP-29255 2 | `emaar-mirage-document-submittal` 6 (the same 6 documents as EP-27331), then 2 each for `arex-enco-…` and `pivot-al-arabia-…` (9 layout keys) |

The decision controls in the run set are 16 positive documents and 8 negative ones: F042, F043, F046, F047, F051, F057, F060 and F066. The unsupported-control shortfall of 2 is a plan v2 §2.3 deviation, and no substitute was drawn.

## 3. Is ELIGIBLE reachable? (pure gains, Part 1, exact)

The table counts every set of documents on which C could gain while B misses, with no losses. For each size it shows how many of those sets the rule leaves ELIGIBLE, out of all sets of that size.

| Gain size | Identity | Revision | Decision |
|---|---|---|---|
| 1 | 0 / 23 | 0 / 16 | 0 / 16 |
| 2 | 209 / 253 | 92 / 120 | 97 / 120 |
| 3 | 949 / 1,771 | 230 / 560 | 282 / 560 |
| 4 | 7,940 / 8,855 | 1,477 / 1,820 | 1,579 / 1,820 |
| 5 | 25,876 / 33,649 | 2,628 / 4,368 | 3,156 / 4,368 |
| 6 | 95,878 / 100,947 | 6,986 / 8,008 | 7,272 / 8,008 |
| 8 | 481,066 / 490,314 | 11,940 / 12,870 | 12,105 / 12,870 |
| 12 and above | all | all | all |

- **ELIGIBLE is reachable in every field.** The smallest ELIGIBLE net gain is **2** in all three.
- The decision counts for sizes 1 to 6 equal Review 35's exhaustive check: 0, 97, 282, 1,579, 3,156 and 7,272.

## 4. Which gains make a field NOT ELIGIBLE

**Never ELIGIBLE, in any field and at any size:**
- A net gain of **1**. One document is 100 % of it.
- A net gain of **2** unless the two documents differ in project (which is also the contractor) **and** in layout key.
- Any gain confined to **one project**. The largest projects are:
  - identity: EP-26687 (6) and EP-27331 (6);
  - revision: EP-27331 (6);
  - decision: EP-27331 (6).
- Any gain confined to **one layout key**. The largest is the EMAAR template `emaar-mirage-document-submittal`: 6 of 16 decision documents, 6 of 16 revision documents and 6 of 23 identity documents.
- In general, any gain in which one project, contractor or layout key holds more than half.

**Decision field, frozen code on synthetic lanes:**

| Gain set | Outcome |
|---|---|
| All 6 EP-27331 (EMAAR) decision documents | **NOT ELIGIBLE**. Project, contractor and layout are each 1.0. |
| The 6 EMAAR documents plus 6 others (12) | ELIGIBLE. EMAAR holds exactly half, which is not more than half. |
| The 6 EMAAR documents plus 7 others (13) | ELIGIBLE |
| Every decision document (16) | ELIGIBLE |
| One document in each of the 5 decision projects | ELIGIBLE |
| The same spread gain (5) plus one C false acceptance on negative control F060 | **NOT ELIGIBLE** (negative-control leg) |

A full EMAAR gain therefore needs at least 6 further gaining decision documents outside EP-27331 before the field can be ELIGIBLE. Those 6 must also not be concentrated among themselves.

**Revision field, failure leg:**

| Case | Outcome |
|---|---|
| Gain on one document in each project except EP-26687 (F043, F035, F037, F033); no loss | ELIGIBLE |
| The same gain, plus losses on F039 and F040 in EP-26687 (net +2, 2 failures) | **NOT ELIGIBLE**. 2 of 2 failures sit in one project, contractor and layout whose net gain is −2. |

## 5. Cross-check of the frozen code against the oracle (Part 2)

The oracle is: "more than half of a positive net gain in one project, contractor or layout key gives NOT ELIGIBLE".

The cases checked for every field were:
- the empty set;
- every single document;
- every pair;
- every subset inside each project, at every size;
- 120 seeded random subsets of size 3 or more (seed `orch07-concentration-on-proposal-2026-10-03`).

| Field | Gain sets checked | Mismatches |
|---|---|---|
| Identity | 489 | 0 |
| Revision | 303 | 0 |
| Decision | 292 | 0 |

## 6. What this means for the owner

- A **real decision gain** that comes only from fixing the EMAAR template (EP-27331) can never make the candidate ELIGIBLE. That is the likeliest pattern, as Review 34 §6 noted. ELIGIBLE needs the gain spread over projects and templates.
- Losses elsewhere can make a spread gain concentrated.
- Within-group churn, such as +3 and −2 in one group, is flagged by neither leg (R35-15).
- The field gate needs at least 12 matched documents. The margins are only 4 for revision and 4 for decision (23 / 16 / 16 projected). A spread gain is therefore also exposed to the matched-population risk in the declaration's disclosures.
- Every figure here is structural. The run's actual outcome depends on what B and C read. The candidate-level outcome also needs every other gate:
  - precision 0.98;
  - recovery 0.90;
  - zero critical acceptances on resolved truth in C;
  - the request gate at equal caps;
  - decision coverage C ≥ B and C ≥ R.
