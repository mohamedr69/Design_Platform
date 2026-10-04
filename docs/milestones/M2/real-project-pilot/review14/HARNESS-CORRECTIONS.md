# R14-01 and R14-02: the budget and scorer corrections to the exploration harness

**Scope.** Only the Round 2 experiment harness changed. **The accepted application (`3d5607d`) is unchanged.** No model request was made, and no new real run was performed.

The corrected files are frozen in `evidence/r14/FREEZE-R14.json` (17 files):
- `boq_contract.py`: `r2x-boq-contract-2026-09-30.1`
- `boq_harness.py`: `r2x-boq-harness-2026-09-30.1`
- `overlay.py`: `r2x-overlay-2026-09-30.1`

## R14-01: the per-document budget was reset for every chunk

### The defect, reproduced

The submitted runner is `review13/evidence/scripts/run/r2x_boq.py`, lines 118–133, preserved unchanged. For each chunk of 11 rows it did two things:

1. `run.budget = open_budget(db, None)`: a new `JobBudget` whose call counter and elapsed clock start at zero.
2. `run.exhausted = None`: every per-document stop that was not run-level was cleared.

So the declared **12 calls per document** and **120 s per document** applied per chunk, not per document.

`boq_harness.verify_sheet_submitted` keeps that loop verbatim in behaviour. Driven by a scripted provider through the frozen application's own `verify_boq_rows`, `JobBudget` and `EvidenceRun`, on the exposed EP-8430 sheet (hash-checked, offline), it gives (`evidence/r14/REPRO-R14.json`):

| Profile | Rows selected | Submitted loop: requests | Corrected loop: requests | Corrected: rows refused as budget stops |
|---|---|---|---|---|
| EV1 | 25 | **25** | **12** (`calls_per_document`) | 13 |
| EV2 | 38 | **38** | **12** (`calls_per_document`) | 26 |

**Reconciling the real runs.** The stored runs made **25 (B) and 35 (C) requests on the one EP-8430 PDF**, against the declared 12: 13 and 23 over. The scripted reproduction gives the same 25 for EV1. EV2's real run stopped at 35 because it reached the cross-track day limit.

**What was not exceeded.**
- The 60-per-project-per-day cap: EP-8430 reached exactly 60 (25 + 35) and was then refused.
- The 150-request experiment cap: 113 were used.

### The correction

`boq_harness.verify_sheet` works as follows:
- The document's budget is **opened once** and shared by every chunk. Its call count, escalation count and elapsed basis carry across chunks.
- A per-document stop is **never cleared**. Later rows are recorded as budget-refused reads (`unverified`, "no reading"), and earlier evidence is kept.
- The consumed allowance is **persisted** per (declaration scope, profile, document SHA-256). A resume, a new process or a new chunk list therefore gets **no fresh allowance**, and the elapsed basis resumes from the first start.

**Which caps are per document and profile, and which are shared.**
- **Per document and profile:** 12 calls, 120 s and 2 escalations. That is one `JobBudget` per (scope, profile, document).
- **Shared across profiles, tracks and processes:**
  - the 60-per-project day limit (`xtrack.py`);
  - the ledger scope's request and elapsed caps.

**The corrected runner** is `evidence/r14/r2x_boq2.py`. It uses `verify_sheet` and writes its results unscored; scoring is done by the typed contract. It has **not** been run against a real provider in this task. The evidence-stage runner (`r2x_ev.py`) was checked: `evidence_stage` opens one budget per document itself, and the runner never reopens or clears it. It needs no change.

**Tests.** All run against the frozen application code with a scripted provider (`evidence/r14/tests/test_r14_harness.py`):
- the submitted loop exceeds 12;
- the corrected loop sends exactly 12, across the boundary between the 11-row first chunk and the second chunk;
- the earlier 12 answers stay intact, and each later row is logged `budget: calls_per_document`;
- transport failures count against the 12;
- a resume or a new process gets 0 fresh requests, while another profile gets its own 12;
- an elapsed basis older than 120 s stops the document before any request.

## R14-02: lossy comparison and a first-candidate truth join

### The defects, reproduced on the submitted expressions

`boq_contract.old_values_equal` is `evidence_reader.norm(a) == norm(b)` as the runner used it. `old_join` is the runner's join, verbatim.

| Left | Right | Submitted | Contract (required) |
|---|---|---|---|
| part `PT-1S` | part `PT-1S+` | **equal** | different |
| quantity `1.0` | quantity `10` | **equal** | different |
| quantity `-1` | quantity `1` | **equal** | different |
| numeric `0` | absent | **equal** | different |
| `PRS-CSNKP` / `2` (identical-value control) | same | equal | equal |
| `1` | `1.0` | different | **equal** (the declared numeric contract) |

**The join.**
- **Repeated parts:** two `PRS-CSNKP` rows emitted as `2`, with truths `1` and `2`. The submitted join gives the second row the first row's truth `1`.
- **Descriptions with the same prefix:** "Power Amplifier 8 X 60 W" and "Power Amplifier 4 X 125 W" share their first 12 normalized characters. The submitted join takes the first candidate.

Both are shown in the tests on the old code, then fixed.

### The correction: `boq_contract.py`

- **Parts** are compared as the literal in upper case, with whitespace removed and **every other character kept** (`+ - / .`). Two blank cells are equal.
- **Quantities** are typed:
  - `absent` ≠ `0`;
  - `unreadable` is a state and never agrees with anything;
  - `number` is compared as a Decimal, with sign and decimals: `1 == 1.0`, `1.0 ≠ 10`, `-1 ≠ 1`;
  - a count unit (`no.`, `pcs`, …) is the same as no unit, while other units must match;
  - `text` matches only the same literal, and text never equals a number.
- **The truth join** works per (document hash, page):
  - truth rows are taken in print order and emitted rows in geometry order (the row's `y`, or the centre of its held region);
  - the alignment is **one-to-one and order-preserving**;
  - a pair needs an equal part or a similar description;
  - a pair is **held as ambiguous** when an equally good alignment exists without it.

  The EP-8430 label order was checked against the emitted geometry: all 38 rows appear in the same order, and the H-06 rows sit at the recorded y positions.

## Replay of every stored BOQ output (no new calls)

Output: `evidence/r14/REPLAY-BOQ.json`. Both stored runs were replayed against the original labels (Review 05) and the amended `r14.1` labels, separately named. Per-row before/after is given for every row, unchanged rows included.

| Stored run | Truth | Before | After | Rows changed (outcome / truth / blind) |
|---|---|---|---|---|
| boq-B | original | caught 2, confirmed 5, held-blind-right 17, extra 1 | **identical** | 0 / 0 / 0 |
| boq-C | original | confirmed 16, caught 4, held-blind-right 14, extra 1, held-unread 3 | **identical** | 0 / 0 / 0 |
| boq-B | amended r14.1 | same | identical | 0 / 0 / 0 |
| boq-C | amended r14.1 | same | identical | 0 / 0 / 0 |

- **The join:** 37 one-to-one pairs, **0 ambiguous**. The one unmatched emitted row is the "Total Price For" line, an extra.
- **The frozen BOQ evaluator's own pairing** (`.3`, unchanged) assigns the same truth as the contract join to every row.
- **The scorer defects did not change any stored outcome in this run.** The reviewer did not claim they had.

### Every stored BOQ result is marked as obtained under the per-document budget deviation

Each replay record states the deviation: 25 and 35 requests against 12. **The EV1 / EV2 BOQ comparison is exploratory evidence obtained under a different effective budget.**

**A truncation view.** This is a counterfactual on the stored request order, not a run: the rows within the first 12 requests are those the declared limit would have allowed.

| Profile | Within the first 12 requests |
|---|---|
| EV1 | caught 2 (H06-1 `4`→`1`, and the `94` row with the part missing), confirmed 5, held-blind-right 5; 13 rows would have been budget-refused |
| EV2 | caught 3 (H06-1, the `94` row, H06-2 CD Changer), confirmed 9; **H06-3 (Printer) was request 20** and would have been budget-refused; 26 rows would have been refused |

**Under the declared contract, neither profile would have reached all three H-06 rows on this 38-row sheet.** The application's 12-calls-per-document limit makes complete row verification impossible for such a sheet. That is a finding for the policy decision (B-6), not something to be solved by resetting budgets.
