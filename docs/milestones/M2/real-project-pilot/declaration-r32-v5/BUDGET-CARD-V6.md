# Budget decision card v6: fresh validation R32, declaration v5 (proposal, NOT authorized; R44-07)

This supersedes `declaration-r32-v3/BUDGET-DECISION-CARD.v5.md` (v3's card; v3 is executed and terminal). Declaration v4 had no card (R44-07) and is superseded, never authorized, never run. **Nothing is authorized by this card.** The numbers are v3's and v4's, unchanged.

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v5/FRESH-VALIDATION-DECLARATION-R32-V5.json`, frozen sha256 **`db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`** |
| **Bound harness** | review45 (`BINDING-MANIFEST-R45-HARNESS` `9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb`; Verification 45 VERIFIED WITH CONDITIONS); Verification 46 of v5 pending |
| **Scope** | `m2-fresh-validation-r32-v5-2026-10-08` in `C:/t/r2x/ledger/r2x-ledger.sqlite` (created only by the owner, `SCOPE-CREATION-COMMAND.md`) |
| **Decision coverage gate** | **C ≥ B only: a change from plan v2** (A-10); C ≥ R a mandatory diagnostic |
| **Served-model identity** | **UNRESOLVED** offline (`model_identity_detail`): the owner runs the probe (RUNBOOK-R32-V5 §1.3) or accepts UNRESOLVED identity with the fail-closed runtime check and its two limits (it compares what the CLI reports, in json mode the REQUESTED id; an echoed id passes) |

## 1. The ceiling (unchanged: 556)

| Item | Value |
|---|---|
| Requests | **556** (B 240, C 240, R 40, P 36; no borrowing; never raised, reset or refunded) |
| Tokens | 16,300,000 input / 3,260,000 output (parent and scope) |
| Per-request token thresholds | 90,000 input / 20,000 output: reservation thresholds on estimates before dispatch, not hard limits; an actual overshoot opens the scope's breaker for every later request (R38-13; the largest actual usage in the ledger is input 81,625 / output 19,568) |
| Per-lane token estimates | B 7.0 M / 1.4 M, C 7.0 M / 1.4 M, R 1.2 M / 0.24 M, P 1.1 M / 0.22 M (estimates; per-lane equality not enforced, R35-10) |
| Elapsed | 604,800 s (7 days) from the scope's creation and from the first invocation; the earlier stops first |
| Project window | 60 per project per rolling 24 h over all lanes (a refusal defers, never charges) |

## 2. Estimated usage (unchanged; estimates, not limits)

Planning 145 (B 6, C 112, R 10, P 17); structural maximum 364 (B 48, C 240, R 40, P 36). At the structural maximum with every request at the calibrated p95 the output total (3,621,208) would exceed the 3,260,000 bound: the ledger would refuse first. EP-27331 needs 2 invocations at planning (the last about 24.3 h after the first) and 3 at the structural maximum (about 48.5 h).

**Risk of an early terminal stop (disclosed, not priced):** for F009 and F020 the live application's model form reading (AI on) is not rehearsed (Verification 45 R45-08); a wrongly read page-1 reference, revision or code would be a resolved critical in B and end the run INVALID, as in v3 (1 request spent). The deterministic reading of F009, F020 and F030 passed the drill (0 criticals, 0 requests).

## 3. Invocations and approvals

| Case | Invocations | Per-invocation form | One approval for all planned resumptions (proposal) |
|---|---|---|---|
| Planning estimate | 2 | 2 authorization files | 1 file with 3 nonces (one left unused) |
| Structural maximum | 3 | 3 files | 1 file with 3 nonces |
| Retries | can add invocations | one file each | a new file after the third |

Each invocation consumes exactly one nonce, only after the run's allowance exists; a resume before the `full` time is refused and consumes nothing. The owner's token is presented at every invocation in both forms.

## 4. Preconditions (each checked by the owner before invocation 1 and every resume)

- The pip freeze of the bound interpreter hashes to `bd424a5c4692ab4c1f634705e59ded3784549a6f6c9072ffea9860fbf611bf7f` (R42-09; RUNBOOK-R32-V5 §1.1).
- The CLI file's sha256 `0b35df94…5b03` and its line `2.1.263 (Claude Code)`; the bound interpreter; at least 2 GiB free on drive C (also enforced in code by the runner and the scope command).
- Verification 46, the owner's option-1 register entry with the restated (b), and the fresh D1/D2 naming the v5 hash (`owner_decision_required`).

## 5. Cost

**Unknown, never zero** (`claude-code` on the owner's subscription; no price configured).

## 6. What signing authorizes / does not authorize

Signing (the owner's D2 message naming this card) would authorize only: the RUN declaration derived from `db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df` with the owner's digest; the creation, once and by the owner, of `m2-fresh-validation-r32-v5-2026-10-08` with exactly `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}`; invocation 1 and each resume with its own nonce (per-invocation files, or one multi-invocation file of at most 3 nonces if the owner chooses); requests by B, C, R, P on the six cohort projects' frozen staged copies within the ceiling. It does **not** authorize raising, resetting or re-creating any allowance or limit, a second scope, a v4 scope or run, the frozen file with the runner, the drill flag in a live run, a default variant, M4 acceptance, production use, any OneDrive change, a sealed project, any other project, or human sign-off claims for the AI-reviewed labels.
