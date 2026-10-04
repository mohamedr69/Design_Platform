# M2 Review 07: the shared AI budget ledger (R7-04)

Source files:
- `app/ai/ledger.py` (`ai-ledger-2026-09-29.1`, `estimator-2026-09-29.1`);
- its wiring in `app/ai/provider.py` (`get_provider`) and `app/ai/evidence_reader.py` (`EvidenceRun.call`).

It is **off unless `AI_LEDGER_PATH` is set**.

## What it enforces, and what it cannot

| Control | How | Hard, or estimate plus breaker |
|---|---|---|
| Requests per run scope | `reserve` before dispatch: an atomic `BEGIN IMMEDIATE` on a shared SQLite ledger, across threads and processes | **hard**: a refused request is never sent |
| Aggregate input / output tokens | The reservation (an estimate) is checked before dispatch. Actual usage is settled after. If the settled total passes the cap, the breaker opens and nothing further is dispatched. | estimate plus breaker: a completed request cannot be made smaller |
| Per-request input / output tokens | Refused before dispatch when the **estimate** exceeds the cap. A request whose **actual** usage exceeds it opens the breaker. | estimate plus breaker |
| Elapsed time per scope | Checked at reservation | hard, for new requests |
| Provider-side output limit | The Anthropic API adapter sends `max_tokens`, a hard limit by the provider. The **Claude Code CLI adapter has no output or input flag**: nothing the CLI does is limited by the provider. | API: hard. CLI: estimate plus breaker. |

**No guaranteed token or spend ceiling is claimed for the CLI adapter.** The ledger guarantees the number of requests, stops after the first breach, and records every breach.

## Preflight estimate (`estimate`)

The claude-code adapter reserves the larger of two figures:
- an **analytic estimate**: the text of system, prompt and schema at about 3.5 characters per token, plus the CLI wrapper's roughly 4,500 tokens, multiplied by 2 turns when an image is read through its tool, plus per-image tokens at Anthropic's rule (w×h/750 after scaling to 1,568 px and about 1.15 MP);
- the task's **calibrated p95**, taken from the 690 recorded requests of 2026-09-28/29. For example, discovery is 45,544 input and 10,870 output; a BOQ row read is 5,523 and 628.

The API adapter uses the analytic estimate without CLI overhead. The review 06 constant reservation of 4,000 input tokens is gone.

## Units, as recorded

| Unit | Meaning |
|---|---|
| `requests` | application-visible provider requests (one `complete()`). A refusal is recorded as `refused`, not as a request. |
| `input_tokens` | the provider's input total, including cache creation and cache reads |
| `cached_input_tokens` | the cache-read part of the input (it is inside `input_tokens`) |
| `output_tokens` | as reported, thinking included where the provider counts it |
| `turns` | the provider-reported number of internal turns (`num_turns` from the CLI), never inferred |
| cache hit | a result-cache hit in the application: no request, no tokens, recorded as `cache_hit` |
| unknown usage | a timeout, exception or transport failure with no usage report is **charged at its reservation** and flagged `usage_unknown` |

**Price:** none is assumed. Cost stays unknown until trustworthy prices are configured. The CLI's own `total_cost_usd` field is a notional figure for a subscription, and it is not used.

## Tests: `tests/test_ai_ledger.py`, 9 tests with scripted providers only

| Case | What is shown |
|---|---|
| Underestimated input | 64,816 input tokens against a per-request cap of 50,000: recorded, the breaker opens, and the next request is not dispatched |
| Excessive output | refused before dispatch when the estimate is over the cap; caught after the fact (18,024 against 2,000) when the estimate was small |
| Timeout with unknown usage | charged at the reservation, and marked |
| Provider error, exception and caller retry | each accounted: 3 requests, the exception charged at its estimate |
| Concurrency | 16 threads reserving against a cap of 5: exactly 5 succeed |
| Restart, and another OS process | a second Python process shares the same ledger file; after a restart, limits and totals come from the file and the cap holds |
| One cap across tracks and documents | a documents track and a BOQ track share one input cap |
| Estimator | images, turns and the calibrated p95; the API adapter has no CLI overhead |
| Evidence run | stops on a ledger refusal: page 2 is recorded as a budget stop, the refusal is logged, and a repeated question is a cache hit, not a request |

## Used in the matched run

The matched run of MATCHED-RUN.md ran every track through one ledger scope. The caps were:
- `requests` 120;
- per-request input 70,000 and output 20,000;
- aggregate input 3,000,000 and output 400,000;
- 3 hours.

The settled figures, and any breach, are reported there.
