# Budget decision card v3: fresh validation R32 (proposal, NOT authorized)

This supersedes `review31/BUDGET-DECISION-CARD.v2.md`.
- **Nothing is authorized.** No budget, ledger scope, token, authorization file, schedule or dispatch exists.
- **The card states what the owner would authorize by signing.** It is built from the frozen declaration below and changes none of it.

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json` |
| **Declaration sha256 (frozen)** | `38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0` |
| **Status** | `executed: false`, `budget_approved: false`, authorization "none; owner decision pending" |
| **Reference set** | Reference set independently AI-reviewed (Claude agents), not human-signed (amendment R32-01) |
| **Standing** | M2 CHANGES STILL REQUIRED. M3 not started. |

## 1. What the owner authorizes by signing

The budget authorization names exactly four things.

1. **The declaration.** This means the frozen declaration hash `38e08df9…76b0`, plus the digest the owner chooses (item 3).
   - The runnable declaration is the frozen file with **only** `authorization.owner_token_sha256` changed: the placeholder is replaced by that digest (`build_declaration_r37.fill_owner_digest`).
   - The runnable file's own sha256 is the hash that the runner, the lanes, the guard and the authorization file use.
2. **Creation of one new, empty ledger scope** with exactly these limits and a closed breaker:

   | Item | Value |
   |---|---|
   | Ledger | `C:/t/r2x/ledger/r2x-ledger.sqlite` |
   | Scope | `m2-fresh-validation-r32-2026-10-03` (no scope of that name exists; the ledger has 17 scopes and 483 entries) |
   | `requests` | 556 |
   | `per_request_input` / `per_request_output` | 90,000 / 20,000 |
   | `input_tokens` / `output_tokens` | 16,300,000 / 3,260,000 (the sum of the lane thresholds) |
   | `elapsed_s` | 604,800 (168 h = B 72 h + C 72 h + R and P 24 h) |

   - Create the scope immediately before the first invocation. The ledger measures `elapsed_s` from the scope's **creation**, so any wait before the first run, and between resumes, counts.
3. **The token digest.** This is the sha256 of a token the owner chooses and holds. The token is presented at each invocation in `R34_OWNER_DISPATCH_TOKEN` and never written down by the harness.
4. **The first invocation:** `runner_r32 run --mode live`.
   - **Every later invocation is a `resume`.** It needs a new `OWNER-DISPATCH-AUTHORIZATION.json` with a fresh nonce.

## 2. Request caps (per lane, enforced by the durable allowance; never raised, reset or refunded)

| Lane | Cap | Why |
|---|---|---|
| **B** (baseline) | **240** | Equal to C. The request gate is defined at equal caps (8 per document × 30). |
| **C** (candidate) | **240** | Equal to B |
| **R** (reference-only) | **40** | |
| **P** (probe) | **36** | |
| **Total** | **556** | Also the scope's `requests` limit, which is the cumulative backstop |

## 3. Token thresholds (estimates and breakers, never hard limits)

| | Input | Output | Enforced how |
|---|---|---|---|
| Per request | 90,000 | 20,000 | On the **estimate**, before dispatch. An actual overshoot opens the breaker for later requests. The CLI has no hard bound. |
| Lane B (estimated) | 7,000,000 | 1,400,000 | **Not per lane.** One scope serves all lanes (R35-10). |
| Lane C (estimated) | 7,000,000 | 1,400,000 | Not per lane |
| Lane R (estimated) | 1,200,000 | 240,000 | Not per lane |
| Lane P (estimated) | 1,100,000 | 220,000 | Not per lane |
| **Scope total** | **16,300,000** | **3,260,000** | Enforced by the ledger |

## 4. Estimated usage (from the run set: 24 documents, at most 8 requests per document)

**These are estimates, not limits and not measurements.**

**The request model:**
- **C:** 2 requests per page read (at most 4 pages and 8 calls per document).
- **B:** plan v2's 6. The conservative figure is one form read per decision-bearing document.
- **R:** plan v2's 10.
- **P:** 15 % of C.

**The token model:** the per-request averages that the AI ledger recorded for the four-arm-final scopes:
- evidence lanes: 11,816.4 input and 1,789.7 output (230 requests);
- B: 11,682.2 and 1,379.8 (4 requests).

The conservative token figure uses the ledger's calibrated p95 for its largest task: 45,544 / 10,870 (B: 25,057 / 3,881).

**Requests and tokens, by lane:**

| Lane | Requests: planning | Low | Conservative | Cap | Input tokens: planning | Output tokens: planning | Input / output: conservative |
|---|---|---|---|---|---|---|---|
| B | 6 | — | 16 | 240 | 70,093 | 8,279 | 400,912 / 62,096 |
| C | **112** | 108 | 192 | 240 | 1,323,437 | 200,446 | 8,744,448 / 2,087,040 |
| R | 10 | — | 40 | 40 | 118,164 | 17,897 | 1,821,760 / 434,800 |
| P | 17 | — | 29 | 36 | 200,879 | 30,425 | 1,320,776 / 315,230 |
| **Total** | **145** | | **277** | **556** | **1,712,573** | **257,047** | 12,287,896 / 2,899,166 |

Plan v2 expected about 171 requests for up to 30 documents (B 6, C 135, R 10, P 20). The planning total for the 24 r32 documents is 145.

**Per project.** The project-day limit counts every lane per UTC day. The lanes run in the order B, C, R, P.

| Project | Docs | Pages read by C | Decision-bearing | B (cons.) | C planning / max | R planning | P planning | B+C planning / max | All lanes planning |
|---|---|---|---|---|---|---|---|---|---|
| **EP-27331** | 6 | 23 | 6 | 6 | 46 / 48 | 4.1 | 6.9 | **52 / 54** | **63.0** |
| EP-26687 | 7 | 9 | 3 | 3 | 18 / 56 | 1.6 | 2.7 | 21 / 59 | 25.3 |
| EP-22349 | 5 | 11 | 2 | 2 | 22 / 40 | 2.0 | 3.3 | 24 / 42 | 29.3 |
| EP-3563 | 3 | 6 | 3 | 3 | 12 / 24 | 1.1 | 1.8 | 15 / 27 | 17.9 |
| EP-29255 | 2 | 3 | 2 | 2 | 6 / 16 | 0.5 | 0.9 | 8 / 18 | 9.4 |
| EP-15744 | 1 | 4 | 0 | 0 | 8 / 8 | 0.7 | 1.2 | 8 / 8 | 9.9 |

## 5. Project-day limit: 60 (owner-confirmable)

**Why 60:**
- It is the largest value the frozen preflight accepts.
- It equals plan v2 and the application's own limit.
- A lower value only adds refusals.

**The risks for EP-27331:**
- **Comparison INCOMPLETE.** B + C stays at or under 60 at both planning (52) and maximum (54). An INCOMPLETE through a B or C day-limit refusal needs B's EP-27331 requests to exceed 12 alongside C's maximum. The estimates do not expect that, but cannot exclude it.
- **R and P refused.** At the planning estimate the project reaches 60 during **P**: 63 for all lanes. P (report-only) and, in a conservative case, R can then be refused for EP-27331.
  - A refusal stops that lane for the rest of the invocation.
  - R's contrasts, including decision coverage C ≥ R, are then computed on a truncated R.
- **Refusals are permanent** for the run, even after the UTC day changes (R35-09).

**The alternative:** order a harness change before authorizing. That means a higher ceiling, or a refusal that can be retried after the UTC day changes, with re-freeze, independent re-review and a new declaration.

## 6. Elapsed bounds

- **Declared:** B 72 h, C 72 h, and R and P 24 h after C ends.
- **Enforced:** only the scope's 168 h, counted from the scope's creation. Per-lane elapsed bounds are not enforced (R35-10).
- **The application's own job limit:** 120 s per document job. This is a silent stop on a slow document.

## 7. Cost status

**Unknown, and never treated as zero.**
- The provider is `claude-code`, which bills the owner's signed-in Claude subscription.
- The application has no price configured (`AI_PRICE_*` 0.0), so its cost column reads 0, which is reported as unknown.
- The models and effort below determine the cost.

## 8. Owner-confirmable fields (cost and accuracy depend on them)

| Field | Declared | Basis | Alternatives (each is a new declaration and a new hash before authorization) |
|---|---|---|---|
| `AI_MODEL_SMALL` (most requests) | **`sonnet`** | The four-arm-final declaration's alias. The AI ledger recorded it as `claude-sonnet-5` (457 entries). | `claude-sonnet-5` pins the model if the alias moves. The tree default is `claude-fable-5-1`. |
| `AI_MODEL_STANDARD` (escalations, at most 2 per document) | **`opus`** | The four-arm alias, recorded as `claude-opus-5` (5 entries) | `claude-opus-5`, or `claude-fable-5-1` |
| `AI_EFFORT` | **`low`** | The tree default, which the four-arm run also used. The `claude-code` adapter sends no effort flag to the CLI, so it does not change a request here. | `medium` / `high` (effective only with an API provider) |
| `project_day_limit` | **60** | Section 5 | 1 to 59 (more refusals), or a harness change |
| Ledger scope name | **`m2-fresh-validation-r32-2026-10-03`** | A new, unused name | Any new name, or per-lane scopes (R35-10) |

**The other provider values:**
- `AI_PROVIDER claude-code`;
- `AI_TIMEOUT_S 60` (API only);
- `AI_CLI_TIMEOUT_S 300`;
- `AI_CLAUDE_CLI claude` (CLI 2.1.263 recorded at the four-arm run);
- the application's own AI limits, bound at the tree defaults (declaration `application_ai_limits`).

## 9. Stop rules

They are carried verbatim in the declaration (`stop_rules`).

**Critical acceptance on resolved truth:**
- in **B**, the comparison is **INVALID** and C never starts;
- in **C**, C is terminal and the result is **RESULT**: the candidate failed the safety gate (NOT ELIGIBLE);
- in **R or P**, it is a reference finding only.

**Other stops:**
- **Critical acceptance on unresolved truth:** reported, never a stop.
- **Three consecutive provider failures:** B gives INVALID; C gives INCOMPLETE; R or P stops only that lane.
- **A breaker, ledger, allowance or counter refusal:** a budget stop of that lane, never raised or reset. In B or C it makes the comparison INCOMPLETE.
- **A binding difference or a second writer:** refused before dispatch.

**Resume:**
- A resume never undoes a budget stop or a provider-failure stop.
- A resume is refused after a terminal comparison (RESULT, INVALID) and after a complete run.

## 10. Dispatch order

1. Preflight:
   - the binding and every bound file;
   - the declaration;
   - the HEADs;
   - the truth and the population gate;
   - the run set;
   - the scope exists with exactly the limits;
   - a guard preview.
2. **B**: registration of the 24 documents, then processing. The tripwire runs after each document.
3. **The C-from-B state check**, for C and R.
4. **C**: the tripwire runs after each document.
5. **R**: served from C's capture. Reference-only requests are sent once.
6. **P**: the probe over C's answered dispatches.
7. **Offline scoring** with the candidate-level outcome.

## 11. Still forbidden after signing

- Selecting a default variant.
- M2 acceptance by this run.
- Starting M3.
- Production use or production database writes.
- Any OneDrive change.
- Opening a sealed project.
- Any project outside the six.
- Any use outside the declaration.
- Raising, resetting or re-creating a cap, the allowance or the ledger limits.
- Claiming human sign-off for the AI-reviewed labels.

**What every gate met would mean:** evidence toward closing M2. It would still be subject to independent review and a separate owner selection decision.
