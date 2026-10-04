# Budget decision card v4: fresh validation R32, corrected declaration v2 (proposal, NOT authorized)

This supersedes `declaration-r32/BUDGET-DECISION-CARD.v3.md` (its declaration `38e08df9…76b0` is superseded by A-09 and must never be authorized).
- **Nothing is authorized.** No budget, ledger scope, token, authorization file, RUN file, schedule or dispatch exists.
- **The card states what the owner would authorize by signing,** after Verification 41. It changes nothing in the frozen declaration.

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.json` |
| **Frozen sha256** | `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` |
| **Status** | `executed: false`, `budget_approved: false`, authorization "none; owner decision pending" |
| **Bound harness** | review39 (`BINDING-MANIFEST-R39` `a6f703b4…567b`), verified by Verification 40 |
| **Reference set** | independently AI-reviewed (Claude agents), not human-signed (amendment R32-01) |
| **Standing** | M2 CHANGES STILL REQUIRED. M3 not started. |
| **Decision coverage gate** | **C ≥ B only: a change from plan v2** (whose gate was C ≥ B and C ≥ R), ruled by the owner (A-10); not an unchanged gate. C ≥ R is a mandatory diagnostic and never decides eligibility. |

## 1. The ceiling: one immutable parent budget

| Item | Value | Enforced by |
|---|---|---|
| **Requests** | **556** | the run's allowance (`parent_ceiling`) and the ledger scope's `requests` |
| Input tokens | 16,300,000 | the allowance on reported usage (`parent_input_tokens`) and the scope's `input_tokens` |
| Output tokens | 3,260,000 | the allowance (`parent_output_tokens`) and the scope's `output_tokens` |
| Elapsed | 604,800 s (7 days) | the allowance (from the first invocation) and the scope (from its **creation**): the earlier one stops first |
| Per request | 90,000 input / 20,000 output | the ledger, on **estimates** before dispatch; an actual overshoot opens the breaker (not a hard limit; the CLI has none) |

## 2. Lane allowances (separately auditable; no borrowing; never raised, reset or refunded)

| Lane | Allowance | Why |
|---|---|---|
| **B** (baseline) | **240** | Equal to C: the request gate is defined at equal caps (8 per document × 30) |
| **C** (candidate) | **240** | Equal to B |
| **R** (reference-only) | **40** | |
| **P** (probe) | **36** | |
| **Total** | **556** | = the parent |

Failed, interrupted, timed-out and dispatched-but-unsaved requests stay charged. A retry of a failed request is a new charge.

**Project window:** at most 60 requests per project per rolling 24 h over all lanes. Above it, documents are **deferred** (not charged, not lost) and resumed later.

## 3. Estimated usage (estimates, not limits)

| Lane | Planning | Structural maximum | Allowance |
|---|---|---|---|
| B | 6 | 48 | 240 |
| C | 112 | 240 | 240 |
| R | 10 | 40 | 40 |
| P | 17 | 36 | 36 |
| **Total** | **145** | **364** | **556** |

- **Tokens:** planning about 1.71 M input / 0.26 M output. At the structural maximum with every request at the calibrated p95 of the largest task: 15.6 M / 3.62 M, where the 3.26 M output bound would refuse first (a visible stop).
- **Binding project EP-27331:** 63.0 requests at planning, 160 at the structural maximum (170 only if the drawings-AI path were on; it is off): 2 or 3 windows.
- **Retries** across resumes are extra charges, inside the same allowances.

## 4. Cost status

**Unknown, and never treated as zero.** The provider is `claude-code` on the owner's Claude subscription; no price is configured. Model: `claude-sonnet-5` for every read (`claude-opus-5` pinned for EV2 escalations, which the declared EV1 switches do not reach).

## 5. Owner authorizations expected

| Case | Invocations | Owner authorization files |
|---|---|---|
| Planning estimate | **2** (the second starts about 24.3 h after the first) | 2 |
| Structural maximum | **3** (the last starts about 48.5 h after the first) | 3 |
| Retries of failed requests | can add invocations | one per invocation |

Each invocation consumes exactly one authorization file with a fresh nonce. A resume before the `full` policy's time is refused, creates nothing and consumes nothing.

## 6. Stop rules (summary; the declaration carries them verbatim)

- Resolved-truth critical: B → **INVALID** (C never starts); C → **RESULT** (NOT ELIGIBLE); R or P → a finding only.
- Three consecutive provider failures: B → INVALID; C → INCOMPLETE; R or P → that lane only.
- Allowance, parent, ledger, breaker or guard refusal: a durable budget stop; INCOMPLETE in B or C; never undone by a resume.
- Window refusal: **DEFERRED**, resumed at `resume_not_before`; after the elapsed bound, **CLOSED** (INCOMPLETE).
- Model-identity mismatch or an undeclared request path: **INVALID**, never resumed.
- Pages unread under the application's own per-document limits: the document stays COMPLETE, the pages are listed and counted unread.

## 7. What signing authorizes

Only, and exactly:
1. the RUN declaration derived from the frozen hash `f38fb281…25af` with the owner's digest (the budget authorization names the frozen hash, the digest, the RUN hash and the absolute RUN-file and authorization paths);
2. the creation, once, of the scope `m2-fresh-validation-r32-v2-2026-10-04` in `C:\t\r2x\ledger\r2x-ledger.sqlite` with exactly `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}`, by `create_scope_r40.py create`;
3. the first invocation `runner_r32.py run --mode live` (RUNBOOK section 5.1), and each later `resume` only with its own new authorization file;
4. requests by B, C, R and P on the six cohort projects' frozen staged copies, within the ceiling above.

## 8. What signing does NOT authorize

- Raising, resetting or re-creating an allowance, the parent budget or the ledger limits; a second scope.
- Using the frozen file or hash with the runner.
- Selecting a default variant; M2 acceptance by this run; M3.
- Production use or production database writes; any OneDrive change; a sealed project; any project outside the six; any use outside the declaration.
- Human sign-off claims for the AI-reviewed labels.
- It does not settle the open decisions of `DECLARATION-SUMMARY.md` section 14 (served-model identity; R40-04); those are decided separately and before signing.

**What every gate met would mean:** evidence toward closing M2, still subject to independent review and a separate owner selection decision.
