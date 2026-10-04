# Budget proposal — four-arm accuracy experiment (for the owner's decision)

**Status:** proposal only. Nothing is scheduled, nothing has been dispatched, and no model request has been made. Approval of this proposal is the owner's decision; the existing Round 2 permission covers the project population, not this budget.

## 1. What would run

| | |
|---|---|
| Declaration | [declaration/FINAL-DECLARATION.json](declaration/FINAL-DECLARATION.json), sha256 `aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998` |
| Application | A base on the accepted `3d5607d` (evidence reader off); arms L1–L4 on candidate `719e8de` |
| Arms | **L1** whole-page discovery · **L2** title-block (ROI) discovery · **L3** whole-page discovery + targeted reads · **L4** ROI discovery + targeted reads (guard, support v2, required-first scheduling and deadline common to all four) |
| Harness | reviewed v4.3 (accepted by Review 26): runner `arm-ev-2026-10-01.v4.2`, lifecycle contract v2, journal validator-2, scorer v4, r16.1 durable allowance |
| Sample | frozen R21 sample: **27 documents in 10 non-sealed projects** = 24 primary + 2 long-PDF controls (10 and 52 pages) + 1 legacy Word control; 26 PDFs, 96 pages, **42 pages within the reader's 4-page scope**, 54 beyond scope (counted as unsupported) |
| Reference labels | `r26-labels-2026-10-01.1`, frozen before any prediction (see [LABELS-SUMMARY.md](LABELS-SUMMARY.md)) |
| Provider / model | unchanged from the declaration: the existing `claude-code` CLI adapter (aliases `sonnet` / `opus`; EV1 uses the small tier) |
| Ledger | a **new** scope family `m2-four-arm-final-2026-10-01-*` in the existing ledger file; **the original run's remaining 22 requests are not used** |

## 2. The numbers

| Figure | Requests | Meaning |
|---|---:|---|
| Expected workload | **≈ 509** | planning estimate (R22 workload v2): A ≈ 4, L1 ≈ 118, L2 ≈ 118, L3 ≈ 135, L4 ≈ 135. It assumes every in-scope page triggers a read; the preflight shows that only about 60 % do (§5), so this figure is conservative |
| **Proposed enforced maximum** | **688** | the sum of the five scope caps: **A 8 · L1 160 · L2 160 · L3 180 · L4 180** — the most this experiment can send |
| Structural maximum | 1,256 | 12 requests × 26 PDFs × 4 arms + A's 8. It only describes the design's ceiling; **it is never a spending allowance** |

Tokens, enforced per scope: **4,000,000 input** (cached included) and **600,000 output**, and at most 70,000 input / 20,000 output per request. Across the five scopes that is at most 20 M input and 3 M output. Planning estimates for the four arms together: about 6.5 M input and 0.9 M output expected; about 19.7 M input in a p90-based estimate, which is a statistical estimate, not a bound. Under p90-like inputs the per-scope token cap (4 M) would stop an arm before its request cap. That ends in a budget stop, never an overspend.

**Cost: unknown.** The declared provider is the `claude-code` CLI and the declaration has no authoritative price for it (the application's price fields are 0, meaning unknown), so no dollar figure is given.

## 3. Limits that stay active together

| Limit | Value | Enforced by |
|---|---|---|
| Arm / A scope request cap | 688 in total (table above) | the ledger reserves each request **before dispatch**. An interrupted (in-flight) request stays counted. A failed request counts. Cache hits and refusals do not count |
| Scope token caps | 4 M input / 600 k output per scope; 70 k / 20 k per request | the ledger, before dispatch |
| Per document | **12 requests**, durable across restarts and tags; a single reading stops at **8** (the frozen reader's constant) | the r16.1 durable allowance, charged before dispatch |
| Per project | **60 requests per rolling 24 h across all tracks** (the A base included) | the cross-track counter plus the whole-project reservation: a project-arm batch starts only when the remaining capacity covers 12 × its pending PDFs; otherwise it is deferred and sends zero requests |
| Scope elapsed time | A 4 h; **each document arm 96 h** (revised, §4) | the ledger, measured from the scope's first use |
| Immutability | a scope's limits are persisted at first use; any different value raises `LedgerConfigMismatch`. A run's declaration hash, sandbox and allowance key are fixed. A new tag for an existing allowance is refused | ledger + runner |

All of these were demonstrated offline: on the actual ledger class with a throw-away file ([enforcement/ENFORCEMENT.json](enforcement/ENFORCEMENT.json), 6 cases), and on the actual runner in Reviews 22–25.

## 4. Revision of the earlier proposal: the elapsed-time limit

The R21/R22 proposal gave every scope `elapsed_s = 14,400` (4 hours). The ledger counts this from the scope's creation (case E5). The declared schedule, however, defers whole projects to later rolling days. The simulation puts the last batch at about 24 h (expected) and up to 72 h (worst case), and the preflight deferred projects in L3 and L4 exactly as designed. With 4 hours, any deferred project would be refused when the arm resumed and would end as a budget stop, never read.

**Revised:** document-arm scopes `elapsed_s = 345,600` (96 h); A base unchanged at 4 h. The request caps (688), token caps, per-document and rolling-project limits are **unchanged**. This is a parameter of scopes that do not exist yet, not an increase to an existing cap. The alternative (keep 4 h) would make deferred projects unreadable.

## 5. Preflight of the exact binding (scripted provider, no model request)

The final declaration's dry variant was run end to end in a new disposable sandbox over the real staged sample ([preflight/](preflight/)). All steps exited 0: A, L1–L4 and the v4 scorer with the frozen labels (27 planned, 0 out-of-scope facts, every claim valid).

- **Trigger rate:** of the in-scope pages the arms reached, about 60 % triggered a read (L3: 24 triggered, 15 not), against the 100 % the 509 estimate assumes.
- **Per-document demand:** with scripted maximal answers (four reads on every triggered page) no document reached the durable 12. A single reading stops at 8, so 4-page documents end with some pages budget-stopped. These pages stay in the planned denominator and are counted, not hidden.
- **Arm demand with maximal answers:** L3 sent 99 requests on 23 documents and L4 87 on 20 (one deferred project each), with L1 and L2 at 36 when stopped. That is well inside the 160 / 180 caps.
- **Deferral works on the real sample:** L3 deferred EP-23091 (needed 36, capacity 35), and L4 deferred EP-17428 and EP-23091, with zero requests sent for them.
- **A terminal stop happened:** the scripted provider fabricates a decision on every page. On the contents page D20 (no decision), L1 and L2 *validated* the fabricated "approved as noted"; the tripwire stopped both arms after 2 of 10 projects, and the stop is persisted and not resumable. This measures nothing about the real model, but it shows a **completion risk**: if the real model triggers such an acceptance even once on a resolved label, that arm ends early, its remaining documents enter the comparison as not attempted, and reopening needs a separate decision.

## 6. Schedule (assumptions)

- **Order:** arms are frozen as A → L1 → L2 → L3 → L4; projects run by EP number and documents in stage order.
- **Run time:** at the observed p50 latencies one arm takes about 0.6 h of sequential requests.
- **Rolling window:** the rolling 60-per-project limit makes the third and later arm on a 3-PDF project wait for the window.
- **Elapsed time:** simulated, the last batch starts at about 24 h (expected demand) or up to 72 h (worst case).
- **No automation:** each resume is started by the operator after re-checking the live counters (see [RUNBOOK.md](RUNBOOK.md)). There is no completion guarantee.

## 7. Stop conditions

| Kind | What happens |
|---|---|
| Terminal | A critical acceptance on a resolved label, or three consecutive completed provider failures, ends the arm. Plain `--resume` refuses (exit 4) |
| Budget stop | A scope cap, token cap, elapsed limit, per-document allowance or rolling counter is reached. The run is never raised, reset or re-scoped |
| Refusal before dispatch | A changed declaration, source or label hash; a sealed project; an existing sandbox without `--resume`; a new tag for an existing allowance; a second writer; or indeterminate provider evidence (exit 5) |

## 8. The decision requested

> **Approve or decline:** a new model budget of at most **688 requests** — A 8, L1 160, L2 160, L3 180, L4 180, under ledger scopes `m2-four-arm-final-2026-10-01-{A,L1,L2,L3,L4}` with 4 M input / 600 k output tokens each and an elapsed limit of 96 h per document arm (A 4 h) — on the `claude-code` provider at an unknown dollar cost. The run would use exactly the declaration `aec4d4df…`, the frozen R26 labels and the reviewed v4.3 harness, under the existing per-document (12) and per-project rolling (60 / 24 h) limits and the stop rules above.
