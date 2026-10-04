# Budget decision card: fresh validation (proposal, **not requested yet**)

There is no budget scope, schedule, authorization or dispatch. The card shows what a later authorization would have to name. That authorization comes only after a reviewed preparation package freezes the declaration and gives its hash. [DRAFT-DECLARATION.json](DRAFT-DECLARATION.json) is a draft and is not that declaration.

| Item | Proposal |
|---|---|
| Documents in the run | at most 30, after field-stratified selection ([FIELD-POPULATION-FEASIBILITY.md](FIELD-POPULATION-FEASIBILITY.md)) |
| Application-visible requests, hard ceiling at reservation | **B 16 · C 240 (8 per document) · R reference-only 40 · variation probe 36 · total at most 332** |
| Expected requests | B about 6 · C about 135 (L3 averaged 2.4 per document; DR adds about 1.5 to 2) · R about 10 · probe about 20 |
| Per-request token thresholds | 90,000 estimated input and 20,000 estimated output. These are **estimates checked before dispatch, not hard limits.** One CLI request can exceed them, and an actual overshoot opens the breaker for later requests. |
| Scope token thresholds, estimated input / output | B 400,000 / 80,000 · C 7,000,000 / 1,400,000 · R 1,200,000 / 240,000 · probe 1,100,000 / 220,000 |
| Cost | **unknown** |
| Elapsed time, a proposal and not a completion guarantee | B 4 h · C 72 h · R and probe 24 h after C ends |
| Rolling requests per project per day | 60, all tracks counted (unchanged) |
| Stop rules | resolved-truth critical acceptance or three consecutive provider failures: terminal stop; breaker or refusal: budget stop, never raised |
| Request difference | part of the policy. Benefit is judged per additional request, and no equal-budget accuracy is implied. |

## Decisions the owner must make first, in order

1. **Cohort.**
   - **Option B, fresh projects** ([COHORT-OPTIONS.md](COHORT-OPTIONS.md)), is recommended for M2 closure. It needs a **new written permission naming the EP numbers**: download, staging, labelling and provider use.
   - **Option A, within-project**, runs under the existing Round 2 permission but cannot close M2.
2. **Label reviewer.** Who reviews the labels independently: a human, or an owner-delegated AI reviewer stated as such.
3. **Preparation package.** Only after it is reviewed: authorize the frozen declaration by its hash, with these or corrected caps.

**Decision accuracy may end up out of scope.** If the labelled pool yields fewer than 12 resolved decision-bearing documents, decision accuracy is out of scope, as declared before the run, and the M2 decision gate stays open.
