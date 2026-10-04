# Runbook — authorized execution and scoring (for use only after an explicit owner authorization)

Nothing in this runbook may run before the owner approves [BUDGET-PROPOSAL.md](BUDGET-PROPOSAL.md) in writing and that approval names the declaration hash. This package does not schedule or dispatch anything.

Paths and constants:

| | |
|---|---|
| Interpreter | `ep-platform/backend/venv/Scripts/python` |
| Environment | `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`; **`PILOT_DRY` must be unset** |
| Harness | `C:/t/iso/work/r2x/review25/harness-v4.3` (byte-identical to the reviewed review25 package; hashes in the declaration) |
| Declaration | `C:/t/iso/work/r2x/r26/FINAL-DECLARATION.json`, sha256 `aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998` |
| Live ledger | `C:/t/r2x/ledger/r2x-ledger.sqlite` |
| Rolling counter | `C:/t/r2x/ledger/project-day.sqlite` |
| Durable allowance | `C:/t/r2x/ledger/doc-allowance.sqlite` |

## 0. Record the authorization

Save the owner's approval as `AUTHORIZATION-<date>.md` beside the declaration. Record its sha256 in the run log. It must quote:
- the declaration hash;
- the five scope names and caps (688 in total);
- the token and elapsed limits.

Any difference, such as another cap, scope or model, needs a **new** declaration and a new approval, never an edit.

## 1. Offline preflight (no request)

1. **Declaration:** `sha256sum FINAL-DECLARATION.json` must equal `aec4d4df…`.
2. **Harness:** every file listed under `code.harness.files` and `code.a_runner_imports`, the evaluator and the r16.1 allowance module must equal its declared hash.
3. **Trees:** `C:/t/iso/cand-ai4` must be at `719e8de…` and clean, and `C:/t/iso/frozen-r12` at `3d5607d…` and clean.
4. **Labels:** the label files and `LABEL-MANIFEST.r26.json` must equal their declared hashes. The runner re-checks the label files itself.
5. **Stage:** `R21-STAGE.json` and all 27 staged files must equal their hashes. The A runner re-checks them.
6. **Ledger:** read-only, no scope named `m2-four-arm-final-2026-10-01-*` may exist before the first start. On later starts, each scope's stored limits must equal the declared ones; the ledger refuses otherwise.
7. **Writers:** no other runner may be running against these sandboxes.

## 2. Immediately before every dispatch (each start and each resume)

- **Rolling counter:** read it for the projects of the batch (`xtrack2.capacity(ep, 60)` against `C:/t/r2x/ledger/project-day.sqlite`) and save the snapshot in the run log. The runner applies the same check itself and defers a project that does not fit.
- **Ledger totals:** read the scope's totals (requests, tokens, in flight, elapsed, breaker) and save them. Do not start if the breaker is set, `in_flight` is non-zero from an unknown process, or the elapsed limit is close to expiry.

## 3. Execution, in the frozen order

- **A base (once):**
  `python arm_a.py <A_TAG> --declaration FINAL-DECLARATION.json --declaration-sha aec4d4df…`
- **Each arm, in the order L1, L2, L3, L4:**
  `python arm_ev.py <A_TAG> <ARM_TAG> <ARM> --declaration FINAL-DECLARATION.json --declaration-sha aec4d4df…`

Read every result:

| Result | Meaning | Action |
|---|---|---|
| exit 0, status `completed` | all planned projects done | next arm |
| exit 0, status `deferred` | whole projects were deferred with zero requests (rolling capacity) | Wait for the window, with no automation. Redo step 2, then `… --resume` with the **same** tag. Repeat until no project is deferred or the scope ends |
| exit 0, status `stopped` | a terminal stop (critical acceptance or three provider failures) | **Do not resume.** Record it. The arm ends; its remaining documents are not attempted |
| exit 4 | a resume found the preserved terminal stop | do not retry; record it |
| exit 5 | indeterminate provider evidence | stop; do not dispatch; escalate for a separate decision |
| any refusal before dispatch (changed hash, second writer, new tag, missing sandbox) | binding or concurrency problem | stop and investigate; never work around it |
| process killed or interrupted | an in-flight request stays charged | `--resume` with the same tag continues with the remaining durable allowance only |

**Never:**
- open a new tag for an arm that has started;
- create a new scope;
- amend a scope's limits;
- reset a ledger, counter or allowance;
- run the arms in parallel against the same project window;
- resume a terminal stop.

## 4. Scoring (offline, after the runs)

`python score_arms_v4.py --declaration FINAL-DECLARATION.json --declaration-sha aec4d4df… --runs C:/t/r2x/runs --tags A=<A_TAG>,L1=…,L2=…,L3=…,L4=… --out <OUT>`

This produces `ARMS-METRICS.v4.json`:
- eligibility before accuracy;
- coverage over all 27 planned documents and every declared page;
- extra facts outside scope, by page position;
- the four pair comparisons.

The analysis follows the Review 21 plan: a paired 2×2 with a document-clustered bootstrap, gains reported by label status, and the off-title-block decision-coverage adoption gate. Documents not attempted, deferred past the run, budget-stopped or terminally stopped stay in the denominator.

## 5. After the run

1. Export the live ledger rows of the five scopes.
2. Package runs, journals, stop files, counter snapshots and metrics.
3. Submit for independent review.

No default variant is adopted, and M2 is not accepted by running this.
