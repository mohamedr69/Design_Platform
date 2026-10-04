# Round 2 small batch: the frozen experiment declaration, raw outputs, and the usage / failure ledger (deliverable 4)

## 1. The declaration (frozen before the first model request)

**Files.**
- The declaration: `evidence/run/EXPERIMENT-DECLARATION-SMALL.json`, sha256 **`c146e5752003a890256a0c612ceaa6f164766cb7e8683bf120fdd875e0f9c988`**. It was written by `declare_small.py`, which makes no model request; the provider was checked only with `claude --version`, which reported 2.1.263.
- Addendum 1: `…addendum-1.json`, sha256 `eb3ec504b5a388500167a1c53234df1b0ce498efef3f824c8666902627aa5604`. It records deviations only; **no limit, source or frozen label was changed.**

**What the declaration records.**

| | |
|---|---|
| Candidate | `3d5607d` (clean), FREEZE-R12 hash, eleven source-file hashes; the reader, policy, schema, prompt, audit, ledger, parser, extractor, evaluator and BOQ evaluator identities |
| Permission | OWNER-AI-PERMISSION-ROUND2.md, by hash, **reused, not asked again**. Resolved against ROUND2-SELECTION.json (by hash): 10 exploration projects plus exposed EP-8430. The 10 sealed projects are listed as excluded. Sandbox projects use the application default `ai_policy` `allowed`; live policies are not read or changed. |
| Sources | The exploration manifest, the small batch, the stage manifest, and every file's sha256 |
| Proposed truth | Page labels `d21a83fd…`, derived register labels `fb65f3c2…`, and HOLDOUT-BOQ-LABELS by hash. Status: AI proposals, provisional. |
| Provider | `claude-code` (the Claude Code CLI, the existing evaluation provider); aliases small = `sonnet`, standard = `opus`. The actual model is recorded per response. |
| **Application limits** | **The frozen candidate's defaults, not overridden:** 12 calls per document, **60 per project per day**, 120 s elapsed per job / evidence document, 2 escalations, concurrency 2, CLI timeout 300 s. The per-task input / output figures gate the application's reservation *estimate* only. The cost cap is inert while unpriced. **Review 07 raised the day and time limits to 300; this round did not.** |
| The day limit across tracks | `xtrack.py`, a file-backed counter shared by every runner: a request is refused once a project's rolling-24-hour total over **all** tracks reaches 60. Each sandbox still enforces its own limit too. |
| **Ledger** | `ai-ledger-2026-09-29.2`, file `C:/t/r2x/ledger/r2x-ledger.sqlite`, scope `r2x-small-2026-09-29`: requests **150** (hard), elapsed 14,400 s (hard, for new requests), per-request 70,000 / 20,000, aggregate 4,000,000 / 600,000. The token figures are **estimate plus breaker, not provider-enforced**. Shared by every track. |
| The exhausted Review 07 scope | `r7-matched` (120 settled plus 1 refused) is **not reset, amended or reused**. Its file (`C:/t/r7/ledger/matched.sqlite`) is Review 07 evidence and is not opened for writing: ledger `.2` would add a column to it. That is why Round 2 has its own ledger file. |
| Pricing | Unknown. Cost is reported as unknown, never zero. A spend cap cannot be established without valid pricing or an account control, so the request and time caps are the binding controls. |
| Cache mode | The application result cache is on, with its keys: reader, prompt, schema, policy, variant, tier and model. B and C start from a copy of A's database, which holds no evidence-cache entry. Cache hits are recorded as cache hits. |
| A / B / C | **A** = `AI_EVIDENCE_VARIANT=off` with AI enabled: the application's existing AI path. **B** = EV1: the five targeted triggers plus the seeded 20 % audit (seed by sha256 and page); for BOQ, held rows plus a 20 % audit of accepted rows. **C** = EV2: every confident page, plus standard-tier escalation (≤ 2 per document); for BOQ, every row. **det** = AI disabled (a reference only). |
| Verifier inputs | **Blind:** the page or row crop only, never the first reader's values (the evidence-reader contract) |
| Run order | det → A → B → C → BOQ-B → BOQ-C, one at a time |
| Stop conditions | A ledger refusal; an application limit; the cross-track day limit; three consecutive provider failures; a changed hash, a sealed or undeclared project, or an existing sandbox (the runner refuses to start) |
| Partial results | Kept. A budget stop is recorded as budget, never as absent or negative. |
| Continuation | Only under a new declaration or addendum, with its own scope; nothing is reset |
| Gate before the remaining batch | Every document persisted in every track; no business-row change; the ledger reconciles with usage; no provider failure; scored with its truth status stated |

## 2. What ran (every attempt, including the failed one)

| Tag | Track | Result |
|---|---|---|
| `r2x-small-det` | det | 12/12 documents, 0 requests (`run-small-det.log`). Its first start failed on a runner key error before writing a sandbox (addendum 1). |
| `r2x-small-A.failed-1` | A, attempt 1 | **Failed before any request:** the cross-track counter's folder was missing. The sandbox and log are preserved (addendum 1). |
| `r2x-small-A` | A | 12/12 documents, **0 requests** (the application AI path reads only submittal forms) |
| `r2x-small-B` | B (EV1) | 24 requests, all `ok`; 1 budget stop (the per-document time limit); 669 s |
| `r2x-small-C` | C (EV2) | 29 requests, all `ok`; 5 escalations to opus; 3 budget stops; 754 s |
| `r2x-small-boq-B` | BOQ EV1 | 25 requests, all `ok`; 182 s |
| `r2x-small-boq-C` | BOQ EV2 | 35 requests, all `ok`; **stopped by the cross-track day limit** (EP-8430 at 60); 3 held rows unread; 261 s |

**Raw outputs** for each tag are in `evidence/run/runs/<tag>/`: `RUN.json`, `rows.json`, `usage.json`, and `BOQ.json` for the BOQ tracks. Logs are in `evidence/run/logs/`.

## 3. The usage and failure ledger

**Files.**
- `evidence/run/LEDGER-r2x-small.json`: the scope, and every entry with its estimate, actual usage, turns, latency and outcome, read only.
- `evidence/run/PROJECT-DAY-COUNTER.json`: every request of every track per project.

**Summary.**

| | |
|---|---|
| Requests | 113 settled, 0 refused, 0 unknown usage, 0 failures, breaker closed |
| Models (actual) | `claude-sonnet-5` ×108, `claude-opus-5` ×5 |
| Tokens (actual) | input 926,689 (cached 601,065), output 137,725, 481 turns |
| Tokens (estimated) | input 2,117,450, output 362,598 |
| Budget stops | 4 per-document time stops (B 1, C 3) and 1 cross-track day-limit stop (BOQ-C) |
| Cost | Unknown |
| **Reconciliation** | Ledger 113 = fresh `ai_usage` 113 across tracks ✔ |

**The small-batch gate:**
- persistence: 12/12 documents in every track ✔;
- no business-row change: `project_submittals` and `project_shop_drawings` are 0 in every sandbox, and B and C changed only shadow evidence ✔;
- accounting ✔;
- no provider failure ✔;
- scored with truth status ✔.

**The gate passes as a process gate. It does not make the results accuracy evidence.**
