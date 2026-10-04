# M2 Review 12: legacy anchor reconstruction

These statements are made separately. None of them implies another.

| Question | Status |
|---|---|
| **Correction readiness** | **READY FOR INDEPENDENT CORRECTION REVIEW** (a submission status only). R12-01A and R12-01B are implemented in the isolated candidate `3d5607d`, frozen, probed, focused-tested and re-scored. The planned full suite completed (exit code 1; only the 2 pre-existing failures), and the package checks passed. |
| **Accuracy** | **Unresolved.** B-1 (recovery below 90%), B-2 (identity precision below 98%), B-5 (no supported variant choice) and B-6 (the H-06 BOQ misreads) remain. These synthetic checks justify no new accuracy figure, and every stored run re-scores identically. |
| **Human truth** | **Unconfirmed (B-3).** No reviewer is appointed and there is no sign-off. Packet v2 is unchanged, with blank reviewer fields; zero reviewer names is not a sign-off. AI-generated labels remain proposals. |
| **Bounded evaluation permission** | **Granted by the owner for the existing frozen 34-project Round 2 sample**, through the existing provider and within the existing budgets and experiment gates. See `master-roadmap/OWNER-AI-PERMISSION-ROUND2.md`. |

**The permission, in detail.**
- **What it corrects.** It corrects the Review 11 statement "29076, 30088 and 30784 only / no owner answer", which is stale for bounded evaluation. That earlier statement stays in its package as history.
- **The frozen manifest.** The exact projects must be resolved against the frozen selection before any later authorized evaluation:
  - `review06/ROUND2-PLAN.md`, SHA-256 `83ebd973…`;
  - `review06/evidence/round2/ROUND2-SELECTION.json`, SHA-256 `5437e164…`.
- **What it does not do:**
  - it does **not** unseal the ten sealed holdouts, which stay sealed;
  - it does not change live project policies;
  - it does not authorize a run in this correction. No model was called, and no project was re-asked.

**M2 remains CHANGES STILL REQUIRED.** No M3 work and no production promotion is authorized by this task.

## What was corrected

**R12-01A: exact entries, not reselection by value.**
- Reconstruction of a pre-`.6` anchor now carries the **exact** historical entry in effect at the fact's attempt, with its value, target and order evidence, selected by reliable order.
- An unrelated drawing's repeated revision literal can no longer remove a decision's revision constraint.
- An incompatible or unavailable revision context is never treated as a known absence.

**R12-01B: reliable order for every context entry.**
- A context entry with missing or ambiguous order is never attempt 0 and never picked by list position. The association is then held with its reason.
- The explicit flat `legacy` format and reliable numbered history keep their compatibility.

**Anchors `a977364` already saved** (shown only in synthetic data built with the pinned `.6` reader; not claimed to exist in production):
- they are re-derived from recorded history, with the original kept as `replaced_anchor`, or held until a genuine re-read;
- read-time anchors are never rewritten.

## Package

| Document | Contents |
|---|---|
| [COMPATIBILITY.md](COMPATIBILITY.md) | The contract, with the expectations frozen before the code changed (original in `evidence/`) and the actual results on `a977364` and `3d5607d` |
| [DISPOSITIONS.md](DISPOSITIONS.md) | R12-01A and R12-01B, the handling of anchors `.6` saved, the `_brief` defect caught before the freeze, and the accepted work carried forward |
| [RESCORE.md](RESCORE.md) | The 33 stored runs, identical to Review 11, and what that does and does not show |
| [REGRESSION.md](REGRESSION.md) | What was reproduced, what is new and what is submitted: the module on both candidates, the probes, the focused modules, the planned full suite (with its captured exit code), and the Review 11 run kept as history |
| [PROVENANCE-AND-FREEZE.md](PROVENANCE-AND-FREEZE.md) | Commit, freeze, source hashes and diff, commands and environment, trees |
| `evidence/` | `EVIDENCE-MANIFEST.json`, the frozen expectations, tests, the before and after runs, probes, the re-score, freeze and diff, patch scripts, suite and focused JUnit |

## Tests

All new, on the frozen candidate `3d5607d`; all synthetic or scripted:
- **Planned full suite (run once, exit code captured):** exit **1**; 1,694 tests, **1,657 passed, 2 failed, 35 skipped, 0 errors**, no collection errors.
  - **The 2 failures are pre-existing:** the same test identity and message as the Review 10 and Review 11 runs.
  - **The Review 11 timeout test** (`test_two_worker_processes_cannot_both_claim`) passed, in 4.8 s. The Review 11 run's failure stays in history, cause unconfirmed.
- **The reviewer's 188-test set:** 188 passed, exit 0.
- **Review 12 module:** 11 passed, exit 0. On `a977364` it fails 6 of 11, all on behaviour (exit 1).
- **Compatibility and persistence modules:** 127 passed, 7 skipped, exit 0.
- **Probes:**
  - on `a977364`, all four reproduce the reviewer's results exactly;
  - on `3d5607d`, both R12 cases are held and the different-literal control gives the same outcome;
  - the retention, association and R9 probes are unchanged.
- **Re-score:** all 33 stored runs are identical to Review 11 (single-attempt data; this does not validate repeated-processing safety).

## Limitations

- **Overlapping writers.** Attempt numbering is guaranteed only under the existing one-job-at-a-time contract. Overlapping writers are neither prevented nor tested.
- **Already-saved `.6` anchors.** Their repair relies on the recorded history that remains. Where that history is gone, the association stays held until a genuine re-read.
- **The Review 11 full-suite timeout** remains a failure of that submitted run. Its cause is unconfirmed, and it was not reproduced in focused checks.
