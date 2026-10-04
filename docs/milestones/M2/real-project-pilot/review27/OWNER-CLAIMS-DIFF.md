# Owner-facing claims: old (review26) → new (review27)

| Where (review26) | Old claim | New statement (review27) | Why |
|---|---|---|---|
| BUDGET-PROPOSAL §2 | "Tokens, enforced per scope: 4,000,000 input … 600,000 output, and at most 70,000 input / 20,000 output per request" | Token **thresholds on estimates** before dispatch; actual usage recorded after; an overshoot opens a breaker that stops **further** requests. The CLI cannot enforce actual token limits | R27-01; ledger contract; the Review 27 probe (81,625 actual vs a 70,000 threshold) |
| BUDGET-PROPOSAL §2 | "Across the five scopes that is at most 20 M input and 3 M output" | Removed. There is **no hard actual-token bound** for this provider | R27-01 |
| BUDGET-PROPOSAL §2 | "the per-scope token cap … would stop an arm before its request cap. That ends in a budget stop, never an overspend" | The breaker ends an arm **after** the overshooting request. Actual usage can exceed a threshold; no "never an overspend" claim is made | R27-01 |
| BUDGET-PROPOSAL §3 table | "Scope token caps … the ledger, before dispatch" | Thresholds on estimates before dispatch, plus a post-response breaker on actual overshoot | R27-01 |
| BUDGET-PROPOSAL §2, decision text | "at most 688 requests" | "at most 688 **application-visible** requests; one CLI request may contain several provider-internal turns" | R27-01 |
| BUDGET-PROPOSAL §4 | 96 h elapsed (stated as the revision) | Unchanged value, now explicitly **proposed, unapproved and not a completion guarantee** | R27-01 item 4 |
| Decision text | declaration `aec4d4df…`, labels r26, "4 M input / 600 k output tokens each" | declaration **`6c0189b3…`**, labels **r26.2**, token thresholds on estimates with the CLI limitation stated in the decision itself | R27-01, R27-02 |
| LABELS-SUMMARY | "not independently reviewed"; step 4 open | Independent owner-delegated **AI** source review supplied (Review 27); not human, not blind; rulings applied in r26.2 | R27-02 |
| LABELS-SUMMARY | D17 actor inferred listed under "Conventions (no truth uncertainty)" | D17 actor is an explicit **field-level uncertainty** (inferred, not established); the readable decision value is unchanged | R27-02 |
| LABELS-SUMMARY | D19 "rejected (C. Revise & Resubmit)" | The source literal **C. Revise & Resubmit** (D blank) is recorded; "rejected" is only the evaluator's coarse normalization; enclosed sheets stay UR | R27-02 |
| LABELS-SUMMARY | D05 "UR" only | Plus the printed stage **ASBUILT** as descriptive metadata (no routing change) | R27-02 |
| LABELS-SUMMARY | off-title-block: "6 confirmed … meets the minimum by count", strict-reading shortfall of 3 | The reviewer's pre-run interpretation: **5 source-attributed decision documents** among the 24 primary meet the minimum of 4 (D17 excluded from the attribution count); the screen's 1/4 result is kept; no top-up | R27-02 |
| BUDGET-PROPOSAL / READINESS | the ROI population not stated | **Only D16–D18** are crop-eligible decision sheets (one project, 2 explicit stamps); D04, D19 and D22 use whole-page discovery; a small diagnostic | R27-02 |
| READINESS-REPORT | "Labels ready and frozen, specifically incomplete … independent review open" | Labels `r26.2` frozen with the independent AI source review applied; the Word control D27 is not visually verified | R27-02 |
