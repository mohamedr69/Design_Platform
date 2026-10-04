# Live-run contract of the r38 runner, version 3 (ORCH-08; A-09 points 1 to 7)

This is what `runner_r32.py`, `lane_r32.py`, `preflight_r32.py`, `allowance_r32.py`, `run_control_r38.py`, `run_state_r38.py`, `model_identity_r38.py`, `project_bounds_r32.py` and the unchanged `dispatch_guard_r32.py` (review38, bound in `BINDING-MANIFEST-R38.json`) require and do before and during a live run. **It authorizes nothing.** No declaration, authorization, token, run file, ledger scope or budget exists; this task created none. Version 2 (`review34/LIVE-RUN-CONTRACT.md`) stays frozen; this version replaces it for the r38 harness. M2 is CHANGES STILL REQUIRED; M3 has not started. Reference set: reference set independently AI-reviewed (Claude agents), not human-signed.

## 1. Entry points

```text
runner_r32.py run    --mode live --declaration <DECL> --declaration-sha <SHA> --run-set <RUN-SET> --binding <BINDING> --binding-sha <SHA>
runner_r32.py resume --mode live --declaration <DECL> --declaration-sha <SHA> --run-set <RUN-SET> --binding <BINDING> --binding-sha <SHA>
```

- No `--auth-path` (argparse rejects it), no `--stamp` other than the declaration's, no `--sandbox-base` in live mode.
- Dry drills only (each refused in live mode, by the runner and again by every lane): `--dry-fault L:N`, `--dry-inject FILE` (timeouts, an identity mismatch, interruptions, unsaved responses, ledger usage; small caps / window / parent; a FAKE ledger; lowered application limits), `--dry-synthetic SPEC` (SYNTHETIC EP-990001 documents only), `--sandbox-base`.

## 2. The declaration contract 3 (`preflight_r32.validate_declaration`, then `verify_bounds` in the live preflight)

Every key is required; a missing or different value refuses the run before any folder exists.

| Key | Required value | A-09 / finding |
|---|---|---|
| `contract` | `"r38-live-contract-3"` | — |
| `binding_manifest_sha256`, `run_set_sha256` | the binding manifest and run-set file of this run (both re-hashed) | R33-06 |
| `run.stamp`, `run.sandbox_base`, `run.folder` | stamp of 3–64 `[A-Za-z0-9._-]`; the **declared** sandbox base `C:/t/r2x/r<NN>-sandbox`; `run.folder` = base/stamp (one run folder per declaration) | task note (no twin) |
| `authorization.path`, `.owner_token_sha256` | the pinned path beside the declaration; the token digest (64 hex) | R34-03 (carried) |
| `budget.parent` | exactly `{total, input_tokens, output_tokens, elapsed_s}`, positive integers; `total` = 556 | point 3; R35-10, R38-13 |
| `budget.lane_allowances` | exactly `{"B": 240, "C": 240, "R": 40, "P": 36}`; their sum = `parent.total` | point 3 |
| `project_window` | `{limit 1..60, window_s 86400}`: the harness per-project **rolling** window, counted over the charges of every lane | point 1; R35-09, R38-08 |
| `project_request_bounds` | `{path, sha256}` of `PROJECT-REQUEST-BOUNDS.json`; its window and elapsed bound must be the declared ones; the live preflight recomputes it from the run set, the truth and the bound code and refuses any difference | point 1; R38-08 |
| `lane_switches` | the lanes B, C, R, P; `AI_EVIDENCE_*` strings; B, C, R state `AI_EVIDENCE_VARIANT`; P is `{}` | R34-05 (carried) |
| `provider_env` | the ten keys of contract 2 **plus** `AI_MAX_CALLS_PER_PROJECT_PER_DAY`, `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY`, `AI_MAX_CALLS_PER_DOCUMENT`, `AI_MAX_ELAPSED_S_PER_JOB`; **compatible limits** (section 9) | point 1 |
| `model_identity` | `{provider "claude-code", models {small, standard} = full ids (no alias), cli {path = AI_CLAUDE_CLI, version = exact line or null}}`; equal to `AI_MODEL_SMALL` / `AI_MODEL_STANDARD` | point 2; R38-10 |
| `ledger` | `{path, scope, limits, wrap_provider: true}`; `limits.requests` = parent total; `limits.input_tokens` / `output_tokens` / `elapsed_s` = the parent's | point 3 |

A declaration with `dry_exercise` set is never a live declaration (the guard refuses it too).

## 3. The authorization (`dispatch_guard_r32`, unchanged)

Exactly as contract 2, section 3: the pinned `OWNER-DISPATCH-AUTHORIZATION.json` with `declaration_sha256`, `owner_token_sha256`, `authorized_by "owner"`, a one-run `nonce`; the token presented in `R34_OWNER_DISPATCH_TOKEN`, compared by digest; one consumed nonce per invocation (`O_EXCL` record); every lane and every request verifies its own invocation's record. A resume is a new invocation with a new authorization.

## 4. One run folder, one parent budget, one capture store (`allowance_r32`, `capture_store`)

```text
<run.sandbox_base>/<stamp>/
  RUN-STATE.json            run key, stamp, base, binding / run-set hashes, caps, parent, window, every invocation (status, run state,
                            comparison, earliest retry, deferred documents, CLI version); a 'close' record when a deferral expired
  allowance.sqlite          the ONE parent budget: r38_binding (run key, caps, parent, window, bound_at), caps, charges, refusals, stops
  capture.sqlite            the ONE capture store (capture_store unchanged; table 'releases' added by run_control_r38 when needed)
  CLI-VERSIONS.jsonl        one line per invocation (cli path, version, provider, declared models)
  IDENTITY-INVALID.json     only when a returned identity differed (the offending request); never removed
  authorization/consumed-*  live only
  WRITER.lock               one writer at a time
  inv-<n>/                  PROVIDER-IDENTITY.json, IDENTITY-LOG-<lane>.jsonl, sandboxes B C R P and score, out/ (RUN-REPORT.json,
                            ALLOWANCE-AUDIT.json, LANE-<lane>.json, lane-<lane>.r32.json, SCORE-BCR-R32.json, ...)
```

- **Parent budget (immutable).** Total 556, the token bounds and the elapsed bound (counted from the allowance's binding time, i.e. the run's first invocation) are bound in the file with the lane allowances and the window; another value refuses to open it. A resume re-opens the same file: no allowance, charge, refusal or stop is reset.
- **Lane allowances, no borrowing.** A charge is refused when the lane's **own** allowance is used, whatever the other lanes have left; and when the parent total, a parent token bound or the elapsed bound is reached.
- **Charges are never refunded.** A request is charged before it can leave. Its outcome is settled afterwards (`ok`, `timeout`, `invalid_response`, `budget` = a ledger refusal, `dispatch_refused`, `identity_mismatch`, `dry_refused`, ...); a request whose answer was never saved (interrupted, or dispatched but unsaved) stays `dispatched` and charged.
- **Durable stops.** A lane that becomes terminal or budget-stopped records a stop (`stops` table; the first one wins; never deleted). Its later new requests are refused at the gate (`terminal_stop`); served replays are still served, so a resume reproduces the lane's state up to the stop.
- **Capture store (unchanged contract).** A bound fingerprint is served, never re-sent; R is served C's capture by content key; a reserved row without an answer is served `interrupted_charged`. **New:** a refusal never creates a row (the gate refuses before the reservation), so the store holds only dispatched requests; a window refusal after a reservation (a race) releases the reserved row, recorded in `releases`.

## 5. The project rolling window, deferral and resume (A-09 point 1)

- The window counts the charges of **every lane** for a project within the last `window_s` seconds (rolling, not a UTC day). A request that would exceed `limit` is **not charged and not permanent**: the gate raises `DeferDocument` (a `BaseException`, so no application handler can swallow it as a failed call), records the refusal with the **earliest retry time** (when the oldest charge that keeps the window full leaves it), and the lane rolls the document's database work back and marks it `DEFERRED`. The lane continues with the next document.
- A retry time after the elapsed bound is permanent instead (`deferral_beyond_bound`): the document is `INCOMPLETE`, visibly.
- **Lane gating.** C starts only when no B document is `DEFERRED`; R and P only when no C document is `DEFERRED` (R is served C's capture, P samples C's answered rows: both need C's complete capture). A lane that does not start lists every one of its documents as `DEFERRED` (kind `waiting`, with the blocker's retry time) or `INCOMPLETE` (kind `not_started`, with why) -- never absent.
- **Run state** of an invocation: `DEFERRED` (resumable at the earliest retry), `FINISHED`, `RESULT`, `INVALID`.
- **Resume rules** (`runner_r32.resumable`): refused while the earliest retry time has not come (nothing is created); refused after a terminal comparison (`RESULT`, `INVALID`, an identity mismatch) and after a complete run; after the elapsed bound a deferred run is **CLOSED**: a `close` record in `RUN-STATE.json` with comparison `INCOMPLETE: the deferral could not complete within the elapsed bound` and the deferred documents listed; nothing is dispatched. A resume re-runs every lane on new sandboxes; every bound fingerprint is served; only requests never made before are dispatched (a deferred request was never made).

## 6. Visibility: every refusal is recorded per document and page (A-09 points 1 and 7)

- **Where.** Each lane records every event with lane, kind, document, page, task, detail, retry time and class (`LANE-<lane>.json` `limit_events`), and a status for **every** run-set document (`COMPLETE` / `INCOMPLETE` / `DEFERRED`, reason, kinds, pages). The runner copies the statuses into `RUN-REPORT.json` (`documents`) and `RUN-STATE.json` (`deferred`). The scorer carries them into every normalised lane (`lane-<lane>.r32.json`) and `SCORE-BCR-R32.json`. The allowance's refusals, charges and stops are in `ALLOWANCE-AUDIT.json`.
- **Kinds.** `lane_allowance`, `parent_ceiling`, `parent_input_tokens`, `parent_output_tokens`, `parent_elapsed`, `project_window`, `deferral_beyond_bound`, `unattributed`, `terminal_stop`, `breaker`, `ledger`, `guard`, `identity_mismatch`, `identity_invalid`, `lane_stopped`, `not_started`, `waiting`, `application_project_limit` (class **limit**); `provider_timeout`, `provider_failure`, `interrupted_charged`, `prerequisite_failed` (class **failure**); `application_document_limit` (class **arm_policy**: the application's per-document job limits, part of the arm's own policy). Unknown kinds count as limits.
- **The application's own budget stops are observed**, not only the harness's: the lane wraps the evidence reader's `EvidenceRun.call` (C, R) and the baseline's submittal `_Run.call` (B) and records every new exhaustion (`calls_per_project_per_day` -> `application_project_limit`; the other job limits -> `application_document_limit`) per document and page, and in the audit's refusals.
- **Comparison.** A B or C document with a **limit**-class event, or `DEFERRED`, makes the comparison `INCOMPLETE` (`comparison_detail` counts them); it stays in every coverage and recovery denominator and is excluded from the matched sets (paired difference, request gate, concentration) with each exclusion listed. Failure- and arm-policy-class documents are `INCOMPLETE` and visible but follow the stop rules (three consecutive failures make a lane terminal) as in contract 2.
- **Silent skipping is a test failure** (`test_visibility_r38.py`, `test_runner_r32.py`): every run-set document has a status in every lane of every invocation report and in every normalised lane.

## 7. Model identity (A-09 point 2; `model_identity_r38`)

- **Pinned:** `AI_MODEL_SMALL = "claude-sonnet-5"`, `AI_MODEL_STANDARD = "claude-opus-5"` -- the full ids the claude-code adapter accepts (`--model <id>`) and records (the first non-haiku `modelUsage` key); the AI ledger's 483 entries show exactly these strings for the aliases `sonnet` / `opus`. Aliases are refused.
- **Before any lane:** the runner runs `<AI_CLAUDE_CLI> --version` (not a model request) and writes `inv-<n>/PROVIDER-IDENTITY.json` and a `CLI-VERSIONS.jsonl` line; a version different from the declared one, or from the run's first invocation, refuses the invocation before any dispatch. The built provider's adapter name must be the declared provider.
- **Every response:** the identity guard (above the dispatch guard, below the allowance) compares the returned model with the declared full id of the request's tier (or the request's explicit model) and the provider with the declared adapter, and logs the check (`IDENTITY-LOG-<lane>.jsonl`: ok / mismatch / not dispatched; `echo_no_reply` for a timeout or transport failure, where the adapter echoes the configured id). A difference writes `IDENTITY-INVALID.json` once (the offending request: lane, invocation, task, tier, document, page, expected and returned identity), the response becomes the failure `identity_mismatch` (its answer is never used; the request stays charged), every lane becomes terminal, the comparison is `INVALID`, the next request is refused (`identity_invalid`, at the gate, nothing reserved) and the run is never resumed.

## 8. The ledger: the single scope is the backstop (A-09 point 3)

- Live lanes wrap the real provider in the application's `LedgerProvider` on the declared scope (created only under the owner's authorization, never by this harness; verified read-only: exact limits, closed breaker).
- **Reconciliation.** Every charge precedes at most one ledger reservation (the ledger sits inside the dispatch guard, below the allowance and the identity guard). Hence ledger dispatch entries <= charges <= parent total = the scope's `requests` limit; the scope's token and elapsed limits equal the parent's. Each charge names its ledger entry id (the reservation, or the refusal entry the ledger recorded); a charge without an entry was refused before the ledger (guard, identity) or never settled; a ledger entry without a charge record was reserved by a process that died before the charge was settled. `ALLOWANCE-AUDIT.json` `reconciliation` reports these counts and problems; `allowance_r32.py audit <allowance.sqlite> <out> [<ledger> <scope>]` produces it read-only at any time.
- **What the scope does not split.** The ledger has one scope for all lanes; the per-lane split is the allowance's (charges by lane). A ledger refusal (`requests`, tokens, elapsed) or an open breaker refuses every lane; it is recorded (`ledger` / `breaker`), the lane stops (durable), the comparison is `INCOMPLETE` when B or C is affected. One per-request overshoot opens the shared breaker (R38-13, disclosed).
- **After every invocation** the runner checks read-only that the ledger grew only inside the declared scope, by at most the parent total.

## 9. Compatible limits (A-09 point 1; `project_bounds_r32`, `PROJECT-REQUEST-BOUNDS.json`)

- **The harness project window governs.** The application's own per-project limits count `AiUsage` rows in **one lane database per invocation** (fresh sandboxes per invocation; C and R are copies of B's database and so hold B's rows; served answers write rows too): B database 2 x documents, C database B + C maximum, R database B + R maximum, P none.
- The declaration must bind `AI_MAX_CALLS_PER_PROJECT_PER_DAY` and `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` >= the largest such count (**84** for the frozen run set: EP-27331, 12 + 72), so the application's per-project counter can never refuse; and `AI_MAX_CALLS_PER_DOCUMENT` 12 / `AI_MAX_ELAPSED_S_PER_JOB` 120 (the per-document job limits the bounds assume). Anything else is refused (`incompatible limits`). If an application limit nevertheless fires it is recorded (section 6) and the comparison is `INCOMPLETE`.
- The bounds: per project and lane, the planning model of the frozen ORCH-07 declaration and the structural maximum from the hard application bounds (12 calls per document within the 120 s job; at most 4 pages; C 9 and R 6 requests per page under the declared switches; the reader's 8 is checked only between pages; B one form read per document; P at most its cap and C's maximum), the windows each project needs and whether they fit the elapsed bound.

## 10. Lane verification (RC-5, carried) and the sandbox base

Every live lane re-runs the live preflight (now with the bounds recomputed and the model identity), verifies its `AI_EVIDENCE_*` environment equals its declared switches and every declared provider value is in its environment and in the application's settings (the four new limit keys included), and passes the guard before anything is built; a configuration with `auth_path`, a dry fault, injections, a fake ledger or lowered application limits is refused. The sandbox base is the declaration's `run.sandbox_base` (live) or `--sandbox-base` / `R38_SANDBOX_BASE` / the default `C:/t/r2x/r38-sandbox` (dry and tests): no code constant, so no test twin is needed. The ingestion child accepts a root under any `C:/t/r2x/r<NN>-sandbox/`.

## 11. Dry mode

No provider exists (the refusing `DryStub`); no ledger path (a FAKE ledger only with `dry_ledger`, inside the dry run folder, never the AI ledger); a PATH without any CLI; no CLI run (the version recorded is `dry mode: no CLI is run`); 0 model requests; the AI ledger must read the same before and after. Injections apply to the invocations they name (default the first; `--dry-fault` to the invocation it is given to).
