# Journal kind / outcome contract — `provider-outcomes.v1/validator-2`

This revises the validator of the provider-outcome journal (`provider-outcomes.v1`, introduced in review24) so that the damaged-evidence refusal that [lifecycle contract v2](../review24/LIFECYCLE-CONTRACT.md) already promises ("a kind … disagrees with its outcome → indeterminate") holds for **all five** result kinds. The journal format, its writer, the runner (`arm_ev.py`, byte-identical to v4.2) and the lifecycle contract are unchanged.

## Allowed combinations

Derived from the writer (`Journal.result` stores the kind `classify(entry)` and the reader log entry's `outcome`) and the reader's log semantics (`EvidenceRun.call` in the frozen candidate).

| Kind | Allowed `outcome` | Where it comes from | Streak effect |
|---|---|---|---|
| `ok` | exactly `"ok"` | a fresh provider request that succeeded | resets to 0 |
| `failure` | not `None`, not `"ok"`, not starting `budget` (e.g. `transport`, `timeout`) | a fresh provider request that failed | +1 |
| `cache_hit` | exactly `"ok"` | the reader logs every result-cache hit with `outcome: "ok"` | none |
| `budget` | a string starting with `budget` | the reader logs every budget / ledger / allowance refusal as `budget: …` | none |
| `none` | `None` | a call that produced no log entry (the writer then stores no outcome) | none |
| (attempt with no result) | — | a request in flight when the process ended | none |

Only the three neutral rows are new checks. The `ok` / `failure` rules are unchanged. So is the streak arithmetic: a success resets, a completed failure counts, and neutral results and unresolved attempts change nothing, across restarts.

## A contradiction is refused, never repaired

A record whose kind and outcome disagree (for example a `transport` outcome recorded as `budget`, `cache_hit` or `none`) makes the whole journal **indeterminate**, and the runner's existing path applies:

- exit 5 before any dispatch, with zero requests;
- no terminal stop written;
- the run record, allowance charges, journal and `io.jsonl` left untouched;
- the refusal recorded in `REFUSALS.jsonl` with its reason (`record N: kind and outcome disagree (kind '…', outcome '…')`) and `requests_sent: 0`.

The record is not coerced to the kind its outcome implies, because that would construct a stop, or clear one, from evidence the journal itself contradicts.

## Legacy compatibility

No format change was needed, so no version bump of `provider-outcomes.v1`. Every journal the v4.2 writer produced satisfies the table by construction, because the writer derives the kind from the same entry whose outcome it stores. This was confirmed on all 25 existing v4.2 journals: each loads identically (state, streak and reason) under validator-1 and validator-2; see [neutral-evidence/LEGACY-RECHECK.json](neutral-evidence/LEGACY-RECHECK.json).

Scope: this is an internal-consistency check on saved evidence, not authentication against deliberate rewriting. A rewrite that stays internally consistent is outside it, as the reviewer noted.
