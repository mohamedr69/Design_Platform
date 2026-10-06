# Budget decision card v5: fresh validation R32, corrected declaration v3 (proposal, NOT authorized)

This supersedes `declaration-r32-v2/BUDGET-DECISION-CARD.v4.md` (its declaration `f38fb281f30b…` cannot be run as declared and is superseded by A-11). **Nothing is authorized.** The numbers are v2's, unchanged.

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v3/FRESH-VALIDATION-DECLARATION-R32-V3.json`, frozen sha256 `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40` |
| **Bound harness** | review42 (`BINDING-MANIFEST-R42` `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`), pending Verification 42 |
| **Decision coverage gate** | **C ≥ B only: a change from plan v2** (A-10); C ≥ R a mandatory diagnostic |

## 1. The ceiling (unchanged)

| Item | Value |
|---|---|
| Requests | **556** (B 240, C 240, R 40, P 36; no borrowing; never raised, reset or refunded) |
| Tokens | 16,300,000 input / 3,260,000 output (per request estimates 90,000 / 20,000) |
| Elapsed | 604,800 s (7 days) from the scope's creation and from the first invocation; the earlier stops first |
| Project window | 60 per project per rolling 24 h over all lanes (a refusal defers, never charges) |

## 2. Estimated usage (unchanged; estimates, not limits)

Planning 145 (B 6, C 112, R 10, P 17); structural maximum 364 (B 48, C 240, R 40, P 36). EP-27331: 63.0 / 160 requests, 2 or 3 invocations. At the structural maximum with every request at p95 size, the 3.26 M output bound would refuse first (in lane P).

## 3. Invocations and approvals

| Case | Invocations | Per-invocation form | One approval for all planned resumptions (proposal, A-11 §4) |
|---|---|---|---|
| Planning estimate | 2 | 2 authorization files | 1 file with 3 nonces (one left unused) |
| Structural maximum | 3 | 3 files | 1 file with 3 nonces |
| Retries | can add invocations | one file each | a new file after the third |

Either way each invocation consumes exactly one nonce, only after the run's allowance exists (a failure before consumes nothing), and a resume before the `full` time is refused and consumes nothing. The owner's token is presented at every invocation in both forms.

## 4. Preconditions now enforced in code (v3)

The CLI file's sha256 and its `--version` line, the bound interpreter and **at least 2 GiB free on drive C** are checked before invocation 1, before every resume and before the scope creation.

## 5. Cost

**Unknown, never zero** (`claude-code` on the owner's subscription; no price configured).

## 6. What signing authorizes / does not authorize

Signing authorizes only: the RUN declaration derived from `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40` with the owner's digest; the creation, once, of `m2-fresh-validation-r32-v3-2026-10-06` with exactly `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}`; invocation 1 and each resume with its own nonce (per-invocation files, or one multi-invocation file of at most 3 nonces if the owner chooses); requests by B, C, R, P on the six cohort projects' frozen staged copies within the ceiling. It does **not** authorize raising, resetting or re-creating any allowance or limit, a second scope, the frozen file with the runner, a default variant, M2 acceptance, M3, production use, any OneDrive change, a sealed project, any other project, or human sign-off claims for the AI-reviewed labels.
