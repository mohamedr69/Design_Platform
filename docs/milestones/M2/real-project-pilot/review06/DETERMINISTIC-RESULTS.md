# M2 Review 06: deterministic (model-disabled) results

## How these runs were made

- **Code:** the candidate's own application path in disposable sandboxes under `C:/t/r6/<tag>`:
  - database, cache, library and uploads are sandboxed;
  - `AI_ENABLED=false`;
  - `SYNC_FILE_WORKERS=0`.
- **Path:** projects are created through the API (TestClient, no server). The `sync-documents` job runs inline, followed by processing, then the stored readings are dumped from the reopened database.
- **Runner:** `scripts/run_r6.py`.
- **Inputs:** the Review 05 staged copies (`C:/t/pilot/stage`, `C:/t/holdout/stage`), read-only.
- **Scoring:** frozen evaluator .4 with labels v1, the v2 page labels and the holdout labels.
- **Denominators:** readable truth. Accepted precision = tp / accepted. **All sets are exposed.**

Cells show tp / accepted / readable.

## Pilot (10 projects, 387 documents)

| Profile | Run | Critical | Register reference | Register revision | Register decision | Raw identity | Raw revision | Raw decision |
|---|---|---|---|---|---|---|---|---|
| default | Candidate C (parse .6) | 2 | 137/139/164 | 104/104/142 | 26/26/71 | 223/223/363 | 185/185/310 | 29/29/80 |
| default | parse .7, superseded | **5** | 137/142/167 | 109/109/145 | 26/26/71 | 248/248/363 | 195/195/310 | 29/29/80 |
| default | **candidate parse .8** | **2** | 137/139/164 | **107**/107/142 | 26/26/71 | **244**/244/363 | **195**/195/310 | 29/29/80 |
| promoted | Candidate C (parse .6) | 2 | 144/146/166 | 108/108/144 | 29/29/73 | 223/223/363 | 185/185/310 | 29/29/80 |
| promoted | **candidate parse .8** | **2** | 144/146/166 | **111**/111/144 | 29/29/73 | **244**/244/363 | **195**/195/310 | 29/29/80 |

Rates for candidate parse .8:

| Profile | Reference recovery | Revision recovery | Decision recovery | Reference precision | Revision and decision precision |
|---|---|---|---|---|---|
| default | 83.5% | 75.4% | 36.6% | 98.6% | 100% |
| promoted | 86.7% | 77.1% | 39.7% | 98.6% | 100% |

Raw layer, candidate parse .8:

| Field | Candidate C | Candidate | Change | Wrong raw values |
|---|---|---|---|---|
| identity | 61.4% | 67.2% | +21 | none |
| revision | 59.7% | 62.9% | +10 | none |
| decision | 36.3% | 36.3% | unchanged | none |

Execution: 343 complete, 36 bounded, 1 failed (EP-26082, the same file as in Review 05).

The 2 remaining critical errors are the flagged references carried from Candidate C (D-R6-A in DISPOSITIONS).

## Holdout (4 projects, 32 files; exposed)

| Profile | Run | Critical | Register reference | Register revision | Raw identity | Raw revision | Raw decision |
|---|---|---|---|---|---|---|---|
| both | Review 05 (parse .6) | 0 | 0/0/5 | 0/0/5 | 3/3/20 | 0/0/13 | 0/0/4 |
| both | **candidate parse .8** | **0** | **3**/3/5 | **2**/2/5 | **14**/14/20 | **7**/7/13 | 0/0/4 |

The per-file readings are listed in DISPOSITIONS (H-01 to H-05) and in `runs/det-holdout/rows-*.json`.

## Against the targets

Targets: at least 90% correct automatic recovery on clear applicable facts, and zero critical false accepts.

- **Not met.** Recovery is still under 90% on every field.
- Pilot critical is 2 per profile (D-R6-A).
- Decisions are the weakest field at 37–40%.
- The deterministic reader alone does not reach the objective.
