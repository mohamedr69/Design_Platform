# Runner lifecycle contract — `runner-lifecycle-2026-10-01.v2`

Supersedes `v1` (review23) for the document-arm runner `harness-v4.2/arm_ev.py` (runner `arm-ev-2026-10-01.v4.2`). Everything in v1 stands; v2 adds the durable provider-outcome journal so a **reached** provider-failure stop cannot be forgotten at the stop-persistence boundary. Scoring contract `harness-contract-2026-09-30.v4` and the whole-project scheduling rule are unchanged.

## Unchanged from v1

- States `completed`, `deferred`, interrupted (open allowance attempt) resume normally; `stopped` is terminal for plain `--resume` (exit 4, zero requests, first reason and evidence preserved, lists preserved, never relabelled `completed`).
- Terminal kinds: critical acceptance on a resolved label (tripwire); three consecutive completed provider failures.
- A terminal stop is written to `out/TERMINAL-STOP.json` atomically the moment it is decided and never overwritten. No override flag, approval flow, budget scope or amendment mechanism exists; reopening needs a separate explicit decision and binding.

## New in v2: the provider-outcome journal (`out/PROVIDER-OUTCOMES.jsonl`, `provider-outcomes.v1`)

**Why a new record.** The existing evidence is not sufficient on its own: the ledger records outcomes (and in-flight reservations) but is bound to the arm scope only, not to the sandbox, tag or document; `io.jsonl` is bound to the sandbox but has no in-flight marker, no binding fields and no fsync. The journal is the smallest record that is bound, ordered, durable and distinguishes unresolved requests. The ledger is used as independent corroboration in the evidence, not by recovery.

**Write order** (each line written whole, flushed and fsync'd before the runner continues):

1. `header` — at run creation, before any request can leave: the binding (declaration hash, arm, tag, A tag, allowance scope and profile, policy) and its digest.
2. `attempt` — before a call that may dispatch is handed to the reader (seq, pid, document sha256, task, page). Calls already refused by the runner's own pre-checks are not journalled (they cannot dispatch).
3. `result` — immediately after the call returns and **before** the failure-streak decision: `ok` / `failure` (with the provider outcome) / `cache_hit` / `budget` / `none`.

Consequence: whenever the runner has decided a provider-failure stop, its three failures are already durable in the journal; an `attempt` without its `result` is a request that was in flight when the process ended.

**Streak semantics.** Over the run's resolved results in journal order, across processes: `failure` +1; `ok` resets to 0; `cache_hit`, `budget`, `none` and unresolved attempts change nothing. **A process restart neither resets nor extends the streak** — this makes v1's "plain `--resume` is not a breaker reset" hold for the provider breaker too (v4.1 kept the count in memory, so a restart silently reset it). Three consecutive completed failures are terminal.

**Resume validation order** (before the startup manifest write and before any call can leave):

1. `TERMINAL-STOP.json` → terminal (v1).
2. The manifest's `terminal_stop` → terminal (v1).
3. A legacy manifest whose `runner_state.stopped` is a terminal reason → persisted as reconstructed → terminal (v1).
4. **The journal** (v2): validated (see below). A durable trailing streak ≥ 3 → the provider stop is persisted with its original reason `stop: three consecutive provider failures`, `reconstructed: true` and the three journalled failures (seq, pid, document, task, page, outcome) as evidence → terminal (exit 4, zero requests). Otherwise the streak and its failures are carried into the process and the journal continues its sequence.
5. The critical-acceptance offline reconstruction (v1).
6. Otherwise the ordinary resume rules.

**Fail closed.** The journal is *indeterminate* when a line is torn or unparsable; the header is missing, not first, or bound to another run; a record carries another binding digest; a result has no open attempt; a process has two open attempts or its records are not contiguous; a seq does not increase; a kind is unknown or disagrees with its outcome; or a document is outside the declared sources. A missing journal is indeterminate when the sandbox already recorded a request, a document start or an allowance charge. An indeterminate journal → **refusal with exit 5**: zero requests, no stop written (no failure history is fabricated), the run record left untouched, the refusal recorded in `REFUSALS.jsonl` with `requests_sent: 0`. Resolving that state needs a separate explicit decision.

## Dry-only devices used by the evidence

`PILOT_DRY_FAIL_FROM` / `PILOT_DRY_FAIL_COUNT` (v1), **`PILOT_DRY_FAIL_AT=i,j,…`** (v2: failures at exact dispatched-request indices, to put a success between failures), `PILOT_DRY_KILL_AFTER` (in flight), `PILOT_DRY_KILL_AT_STOP=before_file|after_file` (v1). All are honoured only under `PILOT_DRY=1`.
