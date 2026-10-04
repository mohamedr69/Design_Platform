# Declaration summary for the owner (A-08 items): fresh validation R32

**Status: frozen, NOT authorized. No dispatch has happened.**
- **What does not exist:** a ledger scope, a token, an authorization file, a budget, a model request.
- **Where things stand:** M2 is CHANGES STILL REQUIRED, and M3 has not started.
- **The reference set:** every metric of this run is stated against a reference set independently AI-reviewed (Claude agents), not human-signed.

## 1. Declaration hash

| | |
|---|---|
| File | `docs/milestones/M2/real-project-pilot/declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json` |
| **sha256** | **`38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0`** (also in `DECLARATION.sha256`) |
| Binds | Harness `review36` (`BINDING-MANIFEST-R36` `5a1a6aad…e568`, 155 files)<br>Run set `9058f3d6…7ce8`<br>Reference set `r32-labels-reviewed-2` `89c60e9d…b9a6`<br>Policy `7efa891b…4f47` and amendment R32-01 `815d43fd…5de6`<br>Evaluator .10 `268d8623…4b4f` (emission role only)<br>Candidate `a8aaced…` and baseline `3d5607d…` (both clean)<br>Reviews 33 to 37<br>Authorities A-01 to A-08 |

## 2. Arm definitions

| Lane | Code | Switches | Role |
|---|---|---|---|
| **B** | baseline `3d5607d` | `AI_EVIDENCE_VARIANT=off` (evidence reader off; stated explicitly) | The accepted path. Runs first, with the tripwire after every document. |
| **C** | candidate `a8aaced` | The L3 set (`VARIANT=EV1`, `GUARD=1`, `SUPPORT=v2`, `SCHEDULING=required_first`, `DEADLINE=1`, `TARGETED=1`) plus IG `IDGUARD=1`, CA `ADJUDICATE=1`, DR `DECISION_REGION=1` and PA `ASSOC=1` | The combined candidate. Starts from a verified copy of B's database. |
| **R** | candidate `a8aaced` | The L3 set | The reference. Served C's capture. Requests C never made are sent once as reference-only. Offline contrast only, never a live stop. |
| **P** | candidate | `{}` | The variation probe: a seeded 15 % of C's answered dispatches, re-sent once. Reported only. |

## 3. Run-set counts

- **24 documents:**
  - 16 decision-bearing;
  - 4 revision top-ups (F060, F043, F057, F046);
  - 4 negative controls (F051, F042, F047, F066).
- **Per-field matched projection.** The minimum is 12.

  | Field | Documents | Margin |
  |---|---|---|
  | Identity | 23 | 11 |
  | Revision | 16 | **4** |
  | Decision | 16 | **4** |

- **Decision controls:** 16 positive and 8 negative (the 4 controls plus the 4 top-ups).
- **Unsupported controls: shortfall 2 of 2.** This is a plan v2 §2.3 deviation. No substitute was drawn, so unsupported-input behaviour is not validated.

## 4. Request caps

**B 240 = C 240, R 40, P 36, total 556.**
- The allowance enforces these per lane. It is never raised or reset.
- The ledger scope's request limit of 556 is the backstop.

## 5. Token thresholds

These are estimates and breakers, **never hard limits**.
- **Per request:** 90,000 input and 20,000 output.
- **Per lane:** B 7.0 M / 1.4 M, C 7.0 M / 1.4 M, R 1.2 M / 0.24 M, P 1.1 M / 0.22 M.
- **Enforced only as the one scope's totals:** 16.3 M / 3.26 M. Lane equality between B and C is not enforced (R35-10).

## 6. Estimated usage

**Requests:**

| | B | C | R | P | Total | Cap |
|---|---|---|---|---|---|---|
| Planning | 6 | 112 | 10 | 17 | **145** | 556 |
| Conservative | 16 | 192 | 40 | 29 | **277** | 556 |

**Tokens (planning):** about 1.71 M input and 0.26 M output. Conservative: 12.3 M / 2.9 M.

**Per project**, B + C planning / maximum, and all lanes at planning:

| Project | B + C planning / max | All lanes planning |
|---|---|---|
| **EP-27331** | **52 / 54** | **63** |
| EP-26687 | 21 / 59 | 25 |
| EP-22349 | 24 / 42 | 29 |
| EP-3563 | 15 / 27 | 18 |
| EP-29255 | 8 / 18 | 9 |
| EP-15744 | 8 / 8 | 10 |

**Project-day limit: 60.**
- **For B and C:** the INCOMPLETE risk for EP-27331 is not expected at the estimates.
- **For P (and conservatively R):** EP-27331 can be refused, because all lanes at planning reach 63.
- **Refusals are permanent** for the run (R35-09).

Details are in `BUDGET-DECISION-CARD.v3.md`.

## 7. Cost status

**Unknown, and never zero.** The provider is `claude-code` on the owner's subscription, and no price is configured.

**Owner-confirmable fields** (cost depends on them):
- `AI_MODEL_SMALL` = `sonnet`, recorded by the ledger as claude-sonnet-5;
- `AI_MODEL_STANDARD` = `opus`, recorded as claude-opus-5;
- `AI_EFFORT` = `low`, which the CLI adapter does not send;
- the project-day limit, 60;
- the scope name `m2-fresh-validation-r32-2026-10-03`.

Changing any of these is a new declaration with a new hash.

## 8. Stop rules

They are carried verbatim in the declaration.

| Event | Effect |
|---|---|
| Resolved-truth critical in **B** | **INVALID**; C never starts |
| Resolved-truth critical in **C** | C terminal; **RESULT**, NOT ELIGIBLE |
| Resolved-truth critical in **R or P** | A finding only |
| Unresolved-truth critical | Reported only |
| Three consecutive provider failures | B: INVALID; C: INCOMPLETE; R or P: that lane only |
| Breaker, ledger, allowance or day-limit refusal | A budget stop of that lane, never raised; in B or C, INCOMPLETE |
| Resume | Never undoes a budget or provider-failure stop. Refused after RESULT, after INVALID and after a complete run. |

The application's internal AI limits act as silent stops: 120 s per document job, calls per document, and its own 60 per project per day.

## 9. Concentration results on the proposal

The rule is v2 (`concentration-r32-2026-10-03.2`), applied to the run-set structure in `CONCENTRATION-ON-PROPOSAL.md`.
- **ELIGIBLE is reachable in every field.** The smallest ELIGIBLE net gain is 2.
- **Never ELIGIBLE:**
  - a net gain of 1;
  - a net gain of 2 inside one project or one layout;
  - **any gain confined to EP-27331 / the EMAAR template.** That is 6 of the 16 decision and 6 of the 16 revision documents. Up to the full 6, it needs at least 6 more spread gains elsewhere.
- **Any C false acceptance on the 8 negative decision controls** makes the field NOT ELIGIBLE.
- **Cross-check:** the frozen code agreed with the oracle on 1,084 gain sets, with 0 mismatches.

## 10. Dispatch order

1. Preflight, including the scope's existence and limits, and a guard preview.
2. **B**: 24 documents registered, then processed.
3. **The C-from-B state check**, for C and R.
4. **C**
5. **R**: from C's capture.
6. **P**: the probe.
7. **Offline scoring**, with one candidate-level outcome.

**No default is ever selected.**

## 11. What the owner must do to authorize

All of the following come after ORCH-07V, the independent verification of this declaration.

1. **Decide the owner-confirmable fields** (section 7) and the day-limit risk (section 6).
   - To change any of them, or to order a harness change or per-lane scopes, ask for a new declaration. This one would then not be used.
2. **Choose a token.** It is a secret only the owner holds. Compute its sha256, the **digest**.
3. **Write the budget authorization.** It must name:
   - this declaration hash `38e08df9…76b0`;
   - the digest;
   - the scope `m2-fresh-validation-r32-2026-10-03` with limits `{"requests": 556, "per_request_input": 90000, "per_request_output": 20000, "input_tokens": 16300000, "output_tokens": 3260000, "elapsed_s": 604800}`;
   - the first invocation.
4. **Write the digest** into the declaration.
   - The runnable declaration is this file with **only** `authorization.owner_token_sha256` changed from the placeholder to the digest (`build_declaration_r37.fill_owner_digest`).
   - Save it in the same folder. Its sha256 is the **run hash**.
5. **Create the ledger scope**, new and empty, with exactly those limits and a closed breaker.
   - Do this immediately before the first invocation: elapsed time counts from creation.
   - The harness never creates it.
6. **Write `OWNER-DISPATCH-AUTHORIZATION.json` at the pinned path** `docs/milestones/M2/real-project-pilot/declaration-r32/OWNER-DISPATCH-AUTHORIZATION.json`, with:
   - `declaration_sha256` = the run hash;
   - `owner_token_sha256` = the digest;
   - `authorized_by` = `"owner"`;
   - `nonce` = a fresh 16–128 character `[A-Za-z0-9_-]` value.
7. **Present the token at the invocation** in `R34_OWNER_DISPATCH_TOKEN`:
   - run `runner_r32.py run --mode live` from `C:/t/iso/work/r2x/r36/harness-r32`;
   - use absolute paths;
   - set `PYTHONDONTWRITEBYTECODE=1` and `GIT_OPTIONAL_LOCKS=0`;
   - do not use `python -O`.

   The full command is in the declaration under `authorization.invocation`.
8. **Withdraw or replace the authorization file** after every invocation.
   - Each `resume` needs a new file with a fresh nonce.
   - Before each invocation, reconcile the scope's entries with the allowance charges.
   - Never move or delete the run folder `C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03`.

**Still forbidden after signing:**
- a default variant;
- M2 acceptance by this run;
- M3;
- production use;
- OneDrive changes;
- sealed projects;
- any project outside the six;
- human sign-off claims for the AI-reviewed labels.
