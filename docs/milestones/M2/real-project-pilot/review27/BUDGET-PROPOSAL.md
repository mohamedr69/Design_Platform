# Budget proposal v2 — four-arm accuracy experiment (for the owner's decision)

**Status:** proposal only, **not approved**. Nothing is scheduled or dispatched, and no model request has been made. This version replaces the review26 proposal. The declaration it describes is v2, which supersedes v1 (`aec4d4df…`). An approval that names v1 does not carry over. The changes are listed in [OWNER-CLAIMS-DIFF.md](OWNER-CLAIMS-DIFF.md).

## 1. What would run

| | |
|---|---|
| Declaration | [declaration/FINAL-DECLARATION.v2.json](declaration/FINAL-DECLARATION.v2.json), sha256 **`6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1`** |
| Application | A base on the accepted `3d5607d`; arms L1–L4 on candidate `719e8de` |
| Arms | **L1** whole-page discovery · **L2** title-block (ROI) discovery · **L3** whole-page + targeted reads · **L4** ROI + targeted reads |
| Harness | the reviewed v4.3 (Review 26), unchanged |
| Sample | the frozen 27 documents: 24 primary, 2 long-PDF controls and 1 Word control; 42 in-scope pages; 54 pages beyond scope and 1 unsupported input stay in the denominator |
| Reference labels | `r26-labels-2026-10-01.2`: AI-drafted, then given an independent owner-delegated **AI** source review (Review 27). Not human-signed and not blind. The Word control D27 was not visually verified |
| Provider | unchanged: the `claude-code` CLI adapter (EV1 uses the small tier) |
| Ledger | a new scope family `m2-four-arm-final-2026-10-01-*`; the original run's remaining 22 requests are not used |

## 2. What is limited, and how

**(a) Requests: a hard ceiling of 688 *application-visible* requests**

| Scope | Requests |
|---|---:|
| A | 8 |
| L1 | 160 |
| L2 | 160 |
| L3 | 180 |
| L4 | 180 |

Each request is counted when the ledger reserves it, before dispatch. An interrupted (in-flight) request stays counted, and a failed request counts. Cache hits and refusals do not count. **One application-visible CLI request can contain several provider-internal turns**; those turns are not separately capped.

Expected workload: about 509 requests, a conservative planning estimate (the preflight shows about 60 % of in-scope pages trigger a read, not 100 %). The structural maximum of 1,256 is not an allowance.

**(b) Tokens: thresholds on estimates, plus a breaker after the fact**

The thresholds per scope are 4,000,000 input (cached included) and 600,000 output, and per request 70,000 input and 20,000 output.
- **Before dispatch:** the ledger reserves an estimate and refuses a request whose estimate would pass a threshold.
- **After the response:** it records the provider-reported actual usage. If a request overshoots a per-request or aggregate threshold, the circuit breaker opens and no **further** request is sent in that scope.
- **What the CLI cannot do:** the `claude-code` CLI cannot enforce actual input or output limits. A single request can use more than any threshold before the breaker reacts. A timeout or unreported usage is charged at the estimate, which is not proof that it stayed below a threshold.

There is therefore **no hard upper bound on actual tokens** for this provider. This is the frozen ledger's documented contract (candidate `backend/app/ai/ledger.py`: module docstring, `reserve()`, `settle()`). Review 27's independent offline probe illustrates it: a request reserved at 100 tokens settled at 81,625 actual input tokens under a 70,000 per-request threshold. The excess was recorded, the breaker opened and the next request was refused. An aggregate probe (estimate 90, actual 110, threshold 100) behaved the same way.

Planning estimates (not bounds) for the four arms together: about 6.5 M input and 0.9 M output expected, and about 19.7 M input in a p90-based estimate. Under inputs like the p90 case, a scope's breaker would end an arm early.

**(c) Elapsed time: a proposal value, not a guarantee**

Each document-arm scope would get 96 h (345,600 s) and the A base 4 h, measured from each scope's first use. The 4-hour value of the earlier proposal could not hold the rolling-day deferral schedule (about 24 h expected, up to 72 h worst case). The 96 h value does not reset or extend any existing scope, because none exists. It does not guarantee completion: operator delays, a terminal stop or another limit can still end an arm.

**(d) Cost: unknown**

There is no authoritative price for the declared provider; the application's price fields are 0, meaning unknown. No dollar figure or cost bound is given.

## 3. Other limits that stay active

| Limit | Value | Enforced by |
|---|---|---|
| Per document | 12 requests, durable across restarts and tags; one reading stops at 8 (the frozen reader's constant) | the r16.1 durable allowance, charged before dispatch |
| Per project | 60 requests per rolling 24 h across all tracks (the A base included) | the cross-track counter plus the whole-project reservation: a project-arm batch starts only if the capacity covers 12 × its pending PDFs; otherwise it is deferred and sends zero requests |
| Immutability | a scope's limits are persisted at first use, and a different value raises `LedgerConfigMismatch`; the declaration hash, sandbox and allowance key are fixed; a new tag for an existing allowance is refused | ledger + runner |

## 4. What the experiment can and cannot show

- **A small, budget-constrained comparison** of the four arms on 27 documents. It cannot establish M2 acceptance or general accuracy.
- **Decisions.**
  - Six documents (seven page records) carry readable consultant or engineer decisions, all outside a drawing title block.
  - Five of those six have source-supported attribution. D17's actor is inferred.
- **ROI-specific decision coverage:**
  - **Crop-eligible pages:** only D16, D17 and D18 pass the frozen drawing-sheet predicate. All three come from one project (EP-19144), and only two (D16, D18) carry explicit approval stamps.
  - **Whole-page discovery:** the decision pages of D04, D19 and D22 are A4-size forms, so every arm reads them with whole-page discovery and the crop does not affect them.

  This is a **small diagnostic**, not proof of decision safety. The existing decision-coverage non-regression gate stays in force. A small cluster or zero matched usable decisions is not enough evidence to adopt a default.
- **Incomplete pages count.** Pages left incomplete by the reader's 8-request reading limit, unsupported pages and inputs, deferred, budget-stopped and terminally stopped work all stay in the denominator.

## 5. Preflight (scripted provider, no model request)

The exact binding was preflighted in a disposable sandbox on the real staged sample (review26). Every step exited 0, deferral fired as designed, and no document reached 12 requests. A scripted (fabricated) decision on the D20 contents page was validated, and the tripwire terminally stopped L1 and L2. That is a disclosed **completion risk**, not an accuracy result. Under declaration v2 the same runs re-score identically ([evidence/RESCORE-DELTA.json](evidence/RESCORE-DELTA.json)).

## 6. Stop conditions

| Kind | What happens |
|---|---|
| Terminal | A critical acceptance on a resolved label, or three consecutive completed provider failures, ends the arm. Plain `--resume` refuses (exit 4) |
| Budget stop | A request cap, token threshold on an estimate, open breaker after an actual overshoot, elapsed limit, per-document allowance or rolling counter. The run is never raised, reset or re-scoped |
| Refusal before dispatch | A changed declaration, source or label hash; a sealed project; an existing sandbox without `--resume`; a new tag for an existing allowance; a second writer; or indeterminate provider evidence (exit 5) |

The decision requested is in [DECISION-CARD.md](DECISION-CARD.md).
