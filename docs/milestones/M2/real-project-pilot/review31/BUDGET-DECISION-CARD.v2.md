# Budget decision card v2: fresh validation (proposal, **not requested**)

This supersedes `review30/BUDGET-DECISION-CARD.md`. There is no budget scope, schedule, authorization or dispatch. The card shows what a later authorization would have to name. [DRAFT-DECLARATION.v2.json](DRAFT-DECLARATION.v2.json) is a draft, not that declaration.

| Item | Proposal |
|---|---|
| Documents in the run | at most 30, after the population gate passes (≥ 12 resolved, independently reviewed documents for each of identity, revision and decision) |
| Request ceilings at reservation | **B 240 · C 240 (equal, 8 per document) · R reference-only 40 · probe 36 · total at most 556** |
| Why B equals C | the request-normalized gate is defined **at equal caps** (R31-03). B and C get the same maximum allowance, and the requests C uses beyond B are measured as policy cost. |
| Expected requests (unchanged) | B about 6 · C about 135 · R about 10 · probe about 20, about 171 in all |
| Per-request token thresholds | 90,000 input and 20,000 output, **estimated** before dispatch. These are **not hard limits**: one CLI request can exceed them, and an actual overshoot opens the breaker for later requests. |
| Scope token thresholds, estimated input / output | **B 7,000,000 / 1,400,000 · C 7,000,000 / 1,400,000 (equal)** · R 1,200,000 / 240,000 · probe 1,100,000 / 220,000 |
| Elapsed bound | **B 72 h · C 72 h (equal)** · R and probe 24 h after C ends |
| Rolling requests per project per day | 60, all tracks counted |
| Cost | **unknown**, and never treated as zero |
| Stop rules | [STOP-AND-SAFETY-RULES.md](STOP-AND-SAFETY-RULES.md): a resolved-truth critical in B makes the comparison INVALID; in C it is a terminal stop and a failed safety gate; in R or P it is a finding only. Three consecutive failures in a lane stop that lane. Breaker or refusal: budget stop, never raised. |

## Decisions the owner must make first, in order

1. **Preparation package:** wait for this package's independent review.
2. **Cohort permission:** a new written permission naming EP 3563, 22349, 27331, 15744, 26687 and 29255, with alternates 22317, 29628, 25909 and 28908 entering in seeded order only. It covers download, staging, labelling and provider use. **It has not been requested.**
3. **Labels:** drafting, then the owner-delegated independent AI review by the Codex reviewer, recorded as such and never as human sign-off. Up to two predeclared extensions follow. If the population gate still fails, the outcome is **PREPARATION BLOCKED** and no budget is needed.
4. **Budget:** only after the gate passes. Authorize the frozen declaration by its hash, with these or corrected caps.
