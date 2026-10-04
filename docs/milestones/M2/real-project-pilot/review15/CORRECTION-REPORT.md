# Closing Independent M2 Review 15: interrupted budgets, sparse row matching and overlay authority

**Task.** "TASK: Close Independent M2 Review 15" (`reviews/M2-review-15/`), done offline and in isolation.

**What was not done.**
- No model request.
- No change to live code, services, settings or data.
- No sealed-project access.
- No commit or push to the owner's repository.
- **No change to the accepted application `3d5607d99fcebf08ac45f5df937ad615ecc16fb3`.** Its tree is clean, and 9 of its source-file hashes are recorded in `evidence/r15/FREEZE-R15.json`.

**This folder is a new package.** `review05`–`review14`, the labels, packet v2 and the reviewer's files are unchanged.

**What stays accepted from Review 14:**
- the typed value comparisons;
- the label amendment `r14.1` and its source binding;
- the repaired links;
- the shortfall proposal;
- the historical deviation marker.

## States, reported separately

| State | Status |
|---|---|
| **Correction readiness** | R15-01 to R15-03 are corrected in harness `r15.1`, frozen in `FREEZE-R15.json`. Focused tests on the frozen version: **51 passed, exit code 0** (JUnit captured). The reviewer's probes were run unchanged against both the submitted and the corrected code. **Submitted for independent correction review.** |
| **Extraction accuracy** | Unresolved (B-1, B-2, B-5, B-6). The scripted tests measure the harness only. No accuracy or generalization claim follows. |
| **Review provenance and remaining ambiguity** | The AI source review (owner-delegated, not human, not blind) is unchanged. Its holds remain: F09, F10, F06 revision, `+SL23I` / `+SL231`, the `P06/TRANS/R1` role, the divider `Rev.0` target and the page-2 association proposal. The reviewer's F11/C0226 correction is acknowledged ([REVIEWER-CORRECTION-ACK.md](REVIEWER-CORRECTION-ACK.md)). |
| **Evaluation permission and budgets** | No budget was used. The stored BOQ runs remain marked as obtained with the per-document budget deviation (`evidence/historical/`). No run is scheduled. |
| **Sealed-validation readiness** | Not ready. The sealed cohort is unopened. |

**No variant winner, no M2 acceptance and no M3.** After this gate, the next task is the owner's targeted AI accuracy experiment. It was not launched here.

## R15-01: an interrupted allowance no longer resets

**The cause.** In r14.1, the consumed count was saved only after a whole chunk returned. A process that stopped inside a chunk had sent requests that were never recorded.

**The fix** (`boq_harness.py` r15.1, `DurableBudget` and `DocAllowance`):
- **Reserve = persist.** `DurableBudget.reserve` first takes the application `JobBudget`'s own reservation, with all of its limits. It then **commits** the increment of the durable count (SQLite, `BEGIN IMMEDIATE`, refused at the cap). Only then does it return, and only after it returns can the evidence reader send a request.
- **Uncertain reservations are spent, never re-granted.** This covers a death between the commit and the send, a provider failure, and a refusal after the commit.
- **One writer per (scope, profile, document).** An exclusive OS file lock is held for the whole sheet. A second writer gets `AllowanceBusy`. The OS releases the lock when its holder dies.
- **Attempts are labelled.** An attempt still `open` when the next writer takes the lock is marked `interrupted`, with the count it had reached. Durable evidence is kept.
- **Nothing is re-opened.** The elapsed basis stays the first start, and escalations are durable. No exhausted state is cleared, and no new scope is opened.
- **Resuming is allowed and safe for the allowance:** it continues from the durable count. It does **not** recover the interrupted chunk's uncommitted evidence.

| Probe or test | Submitted r14.1 | Corrected r15.1 |
|---|---|---|
| Reviewer's probe: child killed after 5 requests inside the first chunk, then resume | 0 persisted, 12 more, **17 in total** | **5 persisted, 7 more, 12 in total** |
| Clean completion, then resume | 12, then 0 | 12, then 0 |
| Killed at the cap, then resume | – | 0 more |
| Failure after sending | – | counted; resume sends 0 |
| 25 rows | – | 12 read, 13 budget-refused, earlier evidence intact |
| A second live writer | – | refused; proceeds after the holder ends; a killed holder does not block |
| A key that started 125 s ago | – | 0 sent (`elapsed_time`) |
| Escalations | – | 1, 1, then refused across processes |

The application-path tests (the real `verify_boq_rows`, `EvidenceRun` and `JobBudget`, with a scripted provider) pass on r15.1: the corrected loop sends 12, and the submitted loop still reproduces 25 / 38.

## R15-02: a scored value no longer chooses its truth row

**The fix** (`boq_contract.py` r15.1). The value comparisons are unchanged from r14.1, and a test checks that. Alignment **never uses a scored value**, neither the part number nor the quantity:
1. **Verified geometry first.** A truth row with a verified row position is paired with the single emitted row near it. If no emitted row is near it, it is **missed**, and it is never offered to another row.
2. **Everything else** is aligned one-to-one and in order, on the description only.
3. **Ties are held.** An emitted row that could equally take another truth row is **held**, with every candidate listed. It is never resolved by a value.

| Case | Submitted | Corrected |
|---|---|---|
| Reviewer's probe: only the first PRS-CSNKP emitted, misread `2` | `(first, 37, matched)`, a wrong join | `held: [6, 37]` |
| The same row with quantity `?`, `1`, `0`, `37`, `None`, or another part number | changes the result | **identical result** |
| Only the second occurrence emitted | – | held `[6, 37]` |
| Verified geometry (rows 6 and 37 positioned) | – | `(first, 6, matched_geometry)`, row 37 missed; the quantity error is now scored as wrong |
| An extra emitted duplicate | – | visible (unmatched or held) |
| Shuffled input order, same geometry | – | same join (10 shuffles) |
| Printed neighbours present | – | the order anchors the sparse duplicate to row 6; row 37 missed |
| Complete two-row and same-prefix controls | matched | matched |

**Saved-output replay** (both label versions; with and without the four verified H-06 row positions): **0 rows differ from the Review 14 replay** in truth, join, outcome or `blind_right`. B has 25 rows and C 38. The join gives 37 pairs, 0 held; with geometry, 4 pairs are made by position (2 of them for B's rows). **The synthetic failures did not occur in these saved runs.**

## R15-03: the overlay has no authority over scoring

**The fix** (`overlay.py` r15.1). The overlay is now an **annotation layer**. Critical errors, acceptance and recovery are exactly the context-bound evaluator's: `critical_after_overlay` always equals the evaluator's count.

**What each annotation reads:**
- **Context:** the run's declared context, from the evaluator result's `ai_context` (profile and variant) or passed explicitly.
- **Envelope:** only that context's envelope (`<profile>|<variant>`), and only if the envelope's content hash equals the row's hash. **No other envelope is ever scanned.** A missing or mismatched envelope gives `context_unknown` or `context_mismatch`.
- **Fact:** only on the fact's page, component (from the evaluator's group), field and **exact** value.
- **Literal support:** one declared prefix normalization for revisions: a leading `Rev` / `Rev.` / `Revision` is removed (`Rev.0` → `0`). **Internal punctuation is kept:** `1.0` ≠ `10`.
- **States:** explicit enums, never free text:
  - `role_state` ∈ {`revision`, `identity`, `footer_control_candidate_held`, `unknown`};
  - `association_state` ∈ {`no_target`, `proposal_only`, `held`, `approved`, `unknown`};
  - `recorded_state` is the reader's own stored state.

  Label version **`r15.1`** adds these enums to the 7 supported observations, keyed by the amendment unit that created each one. `r14.1` is unchanged.

| Probe or test | Submitted | Corrected |
|---|---|---|
| Accepted target equals an **unapproved** proposal | critical removed | **stays critical**; annotated "UNAPPROVED proposal (acceptance still an error)" |
| Even an `approved` association | – | stays critical: the evaluator decides |
| Foreign envelope first versus active first | 0 versus 1 criticals | **identical**; the target comes from the active context only |
| Only a foreign context present | – | `context_unknown` |
| Stale content hash | – | `context_mismatch` |
| No declared context | first envelope guessed | `context_unknown`; an explicit context is used as given |
| `1.0` versus `10` | supported, and critical removed | **not supported**, critical kept |
| Free text "…(HELD)" without an enum | treated as authority | `unknown`; no role conclusion |
| No-target control | critical | critical |

**This replaces the r14 test** that endorsed removing a critical error when the target equalled a proposal.

**Stored single-context results** are kept apart from the adversarial cases. Small batch B has 3 criticals and C has 2, both under the original and the amended labels. Every critical fact is found in its own context (`default|EV1`, `default|EV2`), and every recorded target is null. **The criticals are unchanged from the evaluator's and from Review 14.**

## Concise source diff (line endings ignored)

Files: `evidence/r15/diff/`. **`boq_contract.py` and `boq_harness.py` in r15 have CRLF line endings**, because the patch steps rewrote them; the diffs ignore that.

| Module | Lines added / removed | What changed |
|---|---|---|
| `boq_harness.py` | +161 / −41 | `AllowanceBusy`, OS lock, durable `consume`, labelled attempts, `DurableBudget`; `verify_sheet` holds the lock, opens and closes attempts, and wraps the budget; the r13 loop is kept only for demonstration |
| `boq_contract.py` | +66 / −27 | `_pair_score` uses the description only; `join_rows` does verified geometry first, then holds with all candidates; value comparisons unchanged |
| `overlay.py` | +102 / −38 | rewritten as annotation-only, bound to the exact context, with explicit states and a prefix-only revision normalization |

## Evidence (`evidence/`; every file hashed in `EVIDENCE-MANIFEST.json`, checker run after the final edit)

| Folder | Contents |
|---|---|
| `r15/` | The corrected modules, tests, `FREEZE-R15.json` (with the application source hashes), `dev/` (the one-off patch helpers, not part of the harness), `diff/`, `regression/` (JUnit, log, exit code 0), the replays with and without geometry, and `R15-SAVED-OUTPUT-CHECK.json` |
| `r15/probes/` | The reviewer's probe copied byte-identically, plus a copy parametrized only in its code and output folders; outputs and exit codes for **submitted** (pre-edit and recorded) and **corrected** |
| `labels/r15/` | `SMALL-BATCH-LABELS.amended-r15.1.json`, with the explicit states |
| `historical/` | The Review 14 deviation marker and the stored BOQ runs, re-copied byte-identically |
| `reviewer/` | Hashes of the Review 15 files used |
