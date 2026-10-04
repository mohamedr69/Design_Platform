# FI-P1 — PERFORMANCE AND BUDGET: scheduler, budgets, cancellation, measurement, provider limitations

Labels: C = confirmed (code/data read), A = assumption, EXAMPLE = illustrative value. Paths relative to `backend/app/`.

## 1. Concurrency today (C, research C §3)

| Layer | Mechanism | Limit |
|---|---|---|
| Job lane `ifc` | `jobs.claim` single-statement CAS counting `status == "running"`, FIFO by id (services/jobs.py:296-320) | `ifc_worker_concurrency=2` across all workers (config.py:183) |
| IFC worker | 1 process, 2 slot threads | 2 |
| Per job | `ThreadPoolExecutor(drawing_review_parallel=2)` in visual (visual.py:310) and review (review/service.py:209) | 2 |
| Model | `BoundedSemaphore(ai_max_concurrency=2)` **per process**, every caller (provider.py:488) | API + sync worker + ifc worker ≈ 6 CLI processes possible |
| Rendering | serial on the job thread inside the submit comprehension (visual.py:314-315) | none; uncancellable |
| RAM | `Plan` ≈ 2 GB for a 31 MB DXF (incident, C); 16 GB PCs assumed (config.py:123-127) | ≤2 loaded drawings sensible |
| GIL | ezdxf parse/decompose and `draw_entities` are pure Python; both slots + beat threads share one interpreter | heartbeat starvation possible (A) |

Nested limits today **multiply**: per-job pool × per-process semaphore × processes. The design below replaces them
with one global `model` limit and in-process pools for everything else.

## 2. Scheduler design (SPEC §6)

**Where it runs.** One parent job `fa_interfaces_run` (lane `ifc`, one of the 2 lane slots) with dedup key
`fa_interfaces:{project_id}` **shared with the old `fa_interfaces_scan`** (router dedup today
`fa_interfaces_scan:{project_id}`, routers/fa_interfaces.py:36, :62, C) so the two kinds can never run together for one
project. Its job thread is the orchestrator loop; it never parses, renders or calls a model itself. Drawing agents are
in-process state machines. No per-drawing child jobs (they would compete with Drawings Review/IFC reads for the 2
lane slots and need a merge step, A §4).

**In-memory pools (orchestrator process only; no DB rows).** Because render, geometry and writing all happen in the
orchestrator's own process and its children, these are plain `threading` semaphores/locks:

| Pool | Weight | Setting | Default (EXAMPLE) |
|---|---|---|---|
| `render` | 1 per window/overview render | `RENDER_SLOTS` | 2 |
| `geometry` | estimated GB per loaded drawing (DXF MB × 0.07, EXAMPLE from 31 MB → 2 GB) | `GEOMETRY_GB_LIMIT` | 4 |
| `writer:<source_id>` | 1 | fixed | 1 |
| `convert` | 1 per machine | fixed | mirrors `convert._lock` (C) |

**One cross-process DB lease pool: `model`.** The only limit that must span processes (API, sync worker, IFC worker
each build their own provider, provider.py:584-603, C). Implemented in `app/ai/gate.py::ModelGate` and taken
**inside the provider wrapper used by every caller** (`assist._call` → `provider.complete`), so Drawings Review, IFC
symbol review and the API share it and nothing multiplies. `ai_max_concurrency` stays **unchanged** as the inner
per-process cap; for the 2/4/6 experiment only the IFC worker process is started with `AI_MAX_CONCURRENCY` equal to
`AI_MODEL_SLOTS` (process environment, not `.env`), and the global pool guarantees the sum across processes never
exceeds `AI_MODEL_SLOTS`.

```
ai_model_leases(id, holder, pid, job_id, agent_id, acquired_at, expires_at)
acquire: BEGIN IMMEDIATE; DELETE expired; if count(*) < AI_MODEL_SLOTS: INSERT …; COMMIT
         on SQLITE_BUSY: retry with jittered backoff (busy_timeout 15 s is set, database.py, C); waiters poll every
         250–500 ms (EXAMPLE) and are woken early by an in-process release event
release: DELETE by id (also on exception); renew expires_at every ≤ TTL/3; TTL = request timeout + 60 s
```
SQLite write contention is bounded: one short write per acquire/release, no per-task lease commits for render or
geometry. Fairness among agents (round-robin by `served_count`, large 19-layout DWG cannot monopolise) is applied by
the orchestrator **before** a model lease is requested, so the DB pool only enforces the count.

**Process per drawing.** `agents/render.py::DrawingProcess` = `multiprocessing.get_context("spawn").Process` with a
request queue and a response queue (precedent for spawn + child limits: `document_sync.py:369-402`, C §3). It loads the
DXF once, builds the `Plan`, renders the per-layout overview and **all windows into the evidence store**
(`uploads/EP-n/interfaces/evidence/<sha24>/<layout>/<window_id>.png`), streams `{window_id, path, sha256, ms}`
back, then exits — at which point the `geometry` weight is released. Model steps read the cached PNGs, so the ~2 GB
geometry hold lasts only through rendering and the `model` slots can fill from several agents (a lifetime geometry
hold with limit 4 would have capped active drawings at ~2 and distorted the 2/4/6 measurement). Parent control:
`response_queue.get(timeout=RENDER_TIMEOUT_S)` per window (EXAMPLE 120 s) and `PLAN_BUILD_TIMEOUT_S` (EXAMPLE 300 s);
on timeout `process.terminate()`, the window is marked `unread:render_timeout`, and the child is restarted once
(EXAMPLE) with that window excluded. Hatch policy in the child: `Configuration(hatch_policy=HatchPolicy.SHOW_OUTLINE,
hatching_timeout=5.0)` (ezdxf 1.4.4 `addons/drawing/config.py:59-73, 261, 268`, C) plus a pre-filter dropping HATCH
entities whose bbox exceeds 4× the window (EXAMPLE) — the ASE-TILE case is ~150×60 m against 10 m windows (C).

**Model calls.** `subprocess.Popen` with a 1 s poll loop on a cancel token; on cancel/timeout the process tree is
killed. **Orphan protection on Windows** (`taskkill /T` only works while the parent lives): the orchestrator creates a
Windows Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and assigns every render child and `claude.exe` to it,
so worker death kills them (pywin32/ctypes, A: available on the worker PCs); a **startup reaper** scans `ai_usage`
rows left `status=dispatched`, checks `pid` against the live process's creation time (`process_started_at`), kills
matches and finalises the rows `cancelled, usage_unknown`.

**Duplicate-read prevention.** Task keys `(source_sha256, layout, window_id, prompt_version, model_id, effort)` are
unique in `fa_interface_page_results`; a task already `done` is reused; `cache.InFlight` (per process, ai/cache.py:102,
C) is kept for intra-process dedup of identical cache keys.

## 3. Budgets (SPEC §10) — what is enforceable and what is not

| Quantity | Nature | Where enforced | Honest label |
|---|---|---|---|
| Requests per agent / per run / per project-day | **hard cap**, known before dispatch | `ai_usage` row inserted `dispatched` **before** Popen (`JobBudget.reserve` pattern, ai/budget.py:80-103, C) | enforceable |
| Elapsed per agent / per run | hard cap on new dispatches, measured **from first dispatch** (queue wait excluded and reported separately); in-flight calls run to their own timeout | orchestrator | enforceable for dispatch only |
| Input tokens | estimate (flat 1,200/image, provider.py:111-121, C) | reservation only | **estimate** |
| Output tokens per call | `max_tokens` on the API provider; the CLI provider passes **no output limit** (provider.py:538-541, C) | API only | enforceable on API; informational on CLI |
| Actual tokens / cost | reported after the call; CLI `total_cost_usd` not read today (C) | `ai_usage` finalisation | actual when present; `usage_unknown` when killed |
| Provider-internal turns (CLI `Read` of images ≥2 turns; internal Haiku) | not controllable | recorded from `modelUsage` when present | informational |
| Post-response breakers (consecutive failures, rate_limit streak, `model_substituted`) | stop further dispatch | orchestrator | **breaker, not a cap** |

EXAMPLE allowances (owner decision #5), per agent:
`max_requests = 2 × layouts (regions off-viewport + legend, upper bound) + 2 × windows (associate + sweep) + reviews
(≤ 1 per model-proposed observation not settled by rule) + retries`, capped by `FA_AGENT_MAX_REQUESTS = 200`; a
19-layout DWG with 40 windows and 60 reviewable observations → ≤ 38 + 80 + 60 + retries. Per agent
`max_elapsed_s = 3600` from first dispatch; per run `max_requests = 800`; per call `timeout_s = 600` (today's
`drawing_review_timeout_s`, config.py:342, C); Fable adjudication ≤ 1 call per ConflictSet, ≤ 40 per run, only when
`FA_ADJUDICATION_ENABLED`. Retries: at most 1 (EXAMPLE) for `transport|rate_limit` only (provider `retryable`,
provider.py:89-92, C), each a separately reserved and charged attempt with backoff; none for
`auth|unsupported_model|model_substituted|invalid_response`. Never promise exactly-once; interrupted requests are
`usage_unknown` and count against the request cap.

## 4. Cancellation, stall detection and resume

Honoured today only at the file loop, after `readfile`, every 5,000 texts, every 20,000 entities and per completed
future (C, A §2). New rule: every task boundary checks the cancel token; on Stop the orchestrator sets
`progress.stage = "cancelling"` (job status stays `running` with `cancel_requested=1` — no new job status, so
`ACTIVE/FINISHED`, lane counting, `recover_stale` and `useJob` are untouched, jobs.py:64-66, :306, C), releases
leases, terminates render children and kills CLI processes, waits (bounded, EXAMPLE 30 s), then raises `Cancelled`
so the job ends `cancelled`. **Stall watchdog**: an agent is `failed:stalled` only when it **holds a lease** (model,
render or geometry) for `FA_STALL_TIMEOUT_S` (EXAMPLE 900 s) without a committed checkpoint — time spent waiting in a
queue is never a stall. This is separate from the process heartbeat (jobs.py:441-454, C) that today masks hung jobs.
Resume: a new attempt reads `PageOutcome` checkpoints and done task keys; nothing completed is redone; nothing partial
is trusted.

## 5. Measurement plan (SPEC §6, §12)

Protocol: the same frozen manifest (EP-30880 SM/HVAC/FF/ARCH set, or a held-out project); result cache and page
results **cleared before every run** (converted DXFs kept and declared); IFC worker alone on the PC; declared
resources (PC, RAM, CLI version, model id, effort). **Two runs per setting** (EXAMPLE) to see variance, three
settings → 6 runs; request cost ≈ 6 × (per-run requests, ≤ 800 EXAMPLE) ≈ ≤ 4,800 requests — stated up front for owner
approval before the experiment. Nothing is derived by dividing a sequential time by the agent count.

| Metric | Source |
|---|---|
| Total elapsed (run) from first dispatch; queue wait total | `fa_interface_runs`, `fa_interface_agent_runs.queue_wait_s` |
| Time to first usable reviewed result (first agent `complete` + validated) | agent table |
| Plan build and render time per window | `fa_interface_page_results.timings` |
| Model lease wait, model latency p50/p95 per step | `ai_model_leases` timestamps, `ai_usage.latency_ms` |
| Peak RAM (worker + children + CLI) | sampled by the orchestrator (psutil, A: available) |
| Timeouts, throttles (`rate_limit`), killed calls, usage_unknown, substituted calls | `ai_usage` |
| Requests and tokens per agent/run; estimated vs actual | `ai_usage` |
| Accuracy per concurrency setting (VALIDATION.md metrics) | evaluation harness |

Report per setting: `{model_slots, agents, elapsed_s, queue_wait_s, first_result_s, render_s_total, lease_wait_s,
p50/p95, peak_ram_gb, timeouts, throttles, requests, tokens_in/out, usage_unknown, substituted, accepted_precision,
physical_recall}`. 6 is not promised fastest: subscription limits (A) and RAM may make 4 or 2 better.

## 6. Provider limitations (category B) and the readiness probe

Verified today (C, BRIEF 4–6, research C §1–2, own spot-check): configured `ClaudeCodeProvider` has `_cli=None` →
every call `auth`, latency 0, mislabelled ("CLI not found" reported as auth); PATH CLI 2.1.263 rejects
`claude-opus-5-5` (needs ≥2.1.280), alias `opus` → claude-opus-5, `claude-fable-5-1` works; `--effort` exists in the
CLI but is never passed; no output-token limit is passed; `used` model is the first non-haiku `modelUsage` key
(provider.py:568). `ClaudeProvider` honours model + effort but callers pass no effort → `AI_EFFORT=low`; it sends Fable
with `betas=[server-side-fallback]`, `fallbacks="default"` (:251-253) and reports `model=model` (the requested id) on
every return (:263-299) — a fallback to Opus would be logged as Fable, a **silent substitution**; its readiness is
untested here (no credential inspected, A).

Readiness probe (Stage 0.2, provider-independent `ProviderCapabilities`):
```
ProviderCapabilities { provider: string, ready: bool, cli_path: string|null, cli_version: string|null,
  models: {model_id: enum[supported, unsupported, unknown]}, effort_passthrough: bool, output_cap: bool,
  fallbacks_disableable: bool, reports_used_model: bool, reasons: [string] }
```
`ClaudeCodeProvider`: resolve path, run `claude --version` once at build, compare against a per-model minimum
version table (`claude-opus-5-5: 2.1.280`, verified from today's error text), pass `--effort`, report
`output_cap=false`; `ready=false` with the reason when the configured drawing model is unsupported.
`ClaudeProvider`: credential present; `no_fallbacks` requests omit the fallback beta; `AiResponse.model` read from
`message.model`. Both: the wrapper compares the used model with the requested id and returns
`error="model_substituted"` for FA steps (finding held). Callers (`visual.check`, the orchestrator) gate on
`assist.available()` (compliance/assist.py:228-230, C) **before** loading any geometry; agents end
`unsupported:model_unavailable`. Operational: pinned CLI binary per worker machine, signed in as the worker's Windows
user; restart API and both workers after `.env`/CLI changes (`get_settings` lru_cache, config.py:428, C).

## 7. New settings (proposed names; defaults EXAMPLE)

`AI_MODEL_SLOTS=2` (global cross-process `model` pool; `AI_MAX_CONCURRENCY` unchanged), `RENDER_SLOTS=2`,
`GEOMETRY_GB_LIMIT=4`, `RENDER_TIMEOUT_S=120`, `PLAN_BUILD_TIMEOUT_S=300`, `FA_AGENT_MODEL=claude-opus-5-5`,
`FA_AGENT_EFFORT=high`, `FA_REVIEWER_MODEL=claude-opus-5-5`, `FA_ADJUDICATION_MODEL=claude-fable-5-1`,
`FA_ADJUDICATION_EFFORT=high`, `FA_ADJUDICATION_ENABLED=false` (with this default Fable makes no in-app call),
`FA_AGENT_MAX_REQUESTS=200`, `FA_AGENT_MAX_ELAPSED_S=3600`, `FA_RUN_MAX_REQUESTS=800`, `FA_STALL_TIMEOUT_S=900`,
`OBSIDIAN_VAULT_ROOT=` (unset). Existing `drawing_review_*` remain for Drawings Review; it adopts the `model` gate
automatically through the provider wrapper.
