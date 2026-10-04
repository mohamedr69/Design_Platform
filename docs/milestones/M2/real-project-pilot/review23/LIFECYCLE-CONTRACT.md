# Runner lifecycle contract — `runner-lifecycle-2026-10-01.v1`

Applies to the document-arm runner `harness-v4.1/arm_ev.py` (runner `arm-ev-2026-10-01.v4.1`; scoring contract `harness-contract-2026-09-30.v4` unchanged). Defined before the edit; the tests in `harness-v4.1/test_lifecycle_v4_1.py` and the evidence in `lifecycle-evidence/` exercise every clause through the actual runner with a scripted provider.

## States of a run (one sandbox = one tag = one arm = one declaration = one allowance key)

| State | Meaning | Ordinary `--resume` |
|---|---|---|
| `completed` | every project processed or skipped as done | permitted; nothing to do (zero sends unless `--reread`, a dry-only device) |
| `deferred` | one or more projects persisted as deferred by the whole-project reservation rule (zero requests sent for them) | **permitted**: deferred projects are taken in declared order when the rolling capacity covers their worst case; durable allowances and the binding continue |
| interrupted (no final record; an allowance attempt left `open`) | the process died around a request | **permitted**: the open attempt is marked `interrupted`, completed documents (bound by the scoring contract) are skipped, only the remaining durable allowance of the interrupted document can be used |
| `stopped` — **terminal** | a critical acceptance by the arm's AI on a resolved label (the tripwire), or three consecutive provider failures | **refused**: the preserved stopped result is returned with **zero provider requests** (exit code 4, a refusal record with `requests_sent: 0`); the initial stop reason and its triggering evidence are kept; the projects / not-attempted / deferred lists are preserved; the status stays `stopped` |

A single failed or interrupted request is not terminal. Plain `--resume` is never approval to clear a stop, retry a rejected arm or reset the failure breaker; there is no override flag, approval flow, new budget scope or amendment mechanism in this harness — reopening a stopped arm requires a separate explicit decision and a new binding.

## Persistence

- A terminal stop is written **the moment it is decided** to `out/TERMINAL-STOP.json` (atomic write + fsync, `os.replace`), **before** any manifest update, and is never overwritten: the file holds the first stop's kind, reason, evidence (the tripwire's critical acceptances, or the last three failed requests), time, pid, tag, arm, declaration hash and allowance key.
- The manifest (`out/RUN.json`) carries the same stop under `terminal_stop`; the final status is `stopped` whenever the runner state or the stop file says so — a stopped run is never relabelled `completed` because no project remains.
- Every project after a terminal stop is recorded as `not_attempted` with the stop reason.

## Resume validation order (before the startup manifest write and before any call can leave)

1. `out/TERMINAL-STOP.json` present → terminal.
2. Else the manifest's `terminal_stop` → terminal (the file was lost).
3. Else a v4 manifest whose `runner_state.stopped` starts with a terminal reason → the stop is persisted from the manifest (`reconstructed: true`) → terminal.
4. Else **offline reconstruction from the saved evidence**: the same tripwire (eligible evidence only, the scoring contract's binding) is run over every project whose planned documents this arm has already read; a critical acceptance on a resolved label persists a reconstructed stop → terminal. No request is made in this step.
5. Otherwise the resume proceeds under the existing rules (deferral, interruption, completed-document skips, cache accounting, 12 / document allowance, arm scope, rolling project limit).

If a saved stop belongs to another binding (declaration hash or arm), the runner asserts and stops before dispatch.

## Dry-only devices used by the evidence (never active without `PILOT_DRY=1`)

`PILOT_DRY_KILL_AT_STOP=before_file | after_file` (exit 98 around the persistence boundary), `PILOT_DRY_FAIL_FROM=n [PILOT_DRY_FAIL_COUNT=k]` (scripted provider failures), the disagreeing synthetic labels (`X-DRY-1 → X-DRY-9`, the reviewer's device) that make the real tripwire fire on the scripted answers.
