# Closing Independent M2 Review 14: the Round 2 evaluation corrections (index)

**Task.** "TASK: Close Independent M2 Review 14" (`reviews/M2-review-14/M2-NEXT-CLAUDE-INSTRUCTIONS.md`), authorized by the owner for this bounded correction.

**Where the work ran.** In isolation (`C:/t/iso`, `C:/t/r2x`).

**What was not done.**
- No new model request.
- No change to live code, services, settings or data.
- No sealed-project access.
- No commit or push to the owner's repository.
- **The accepted application baseline `3d5607d` is unchanged** (clean tree, checked at the freeze).

**This folder is a new package.** `review05`–`review13` and packet v2 are unchanged.

## States, reported separately

| State | Status |
|---|---|
| **Correction readiness** | The harness, scorer and label corrections are complete and frozen (`evidence/r14/FREEZE-R14.json`). Offline tests on the frozen harness: **22 passed, exit code 0** (captured). **Submitted for independent review.** |
| **Extraction accuracy** | Unresolved (B-1, B-2, B-5, B-6). No variant is selected. No accuracy figure here is accepted evidence. |
| **Review provenance and remaining ambiguity** | 43 worklist units were reviewed by the owner-delegated **independent AI reviewer**. That is **not a human signature and not blind** to earlier predictions. **Held:** F09 (association), F10 (reference), F06 (revision), SB u5 (`+SL23I` / `+SL231`), the `P06/TRANS/R1` role, the divider `Rev.0` target and the calculation page-2 association proposal. Nothing else among the 415 documents is reviewed. |
| **Evaluation permission and budgets** | The 34-project evaluation permission stays recorded. No budget was used in this task. The stored BOQ runs are **marked** as obtained with the per-document budget deviation. No continuation is scheduled; the next run needs a new declaration. |
| **Sealed-validation readiness** | **Not ready.** The sealed cohort is unopened and must stay so until a frozen candidate, a predeclared comparison and pre-prediction labels exist. |

**No variant winner, no 100 % accuracy claim, no M2 acceptance and no M3.**

## Dispositions

| Finding | Disposition | Where |
|---|---|---|
| **R14-01: the BOQ runner reset the per-document budget per chunk** | **Fixed in the harness.** `boq_harness.verify_sheet` keeps one budget per (scope, profile, document) across chunks, retries and resumes. The consumed allowance is persisted, and no stop is cleared. **Reproduced** with a scripted provider: the submitted loop sends 25 (EV1) and 38 (EV2) requests against 12, and the corrected loop sends exactly 12. **Reconciled** with the stored real runs (25 and 35 against 12). The 60 per project per day and the 150 per experiment caps were **not** exceeded. The stored runs are preserved and marked; the corrected runner `r2x_boq2.py` has not been run. | [HARNESS-CORRECTIONS.md](HARNESS-CORRECTIONS.md) §R14-01 |
| **R14-02: lossy comparison and a first-candidate truth join** | **Fixed.** Typed contract `r2x-boq-contract-2026-09-30.1`: parts keep their punctuation; quantities are typed (sign, decimal, unit; zero ≠ absent; unreadable is a state); the join is one-to-one and order-preserving on geometry, with ambiguity held. **All four defect pairs** are reproduced on the submitted expression, alongside the identical-value control, the repeated-part case and the same-prefix case. **Replay** of every stored BOQ output against both label versions: **0 rows changed**. 0 ambiguous joins; the frozen evaluator's pairing agrees on every row. A truncation view shows what the declared 12-request limit would have covered. | [HARNESS-CORRECTIONS.md](HARNESS-CORRECTIONS.md) §R14-02 |
| **R14-03: wrong labels, and literal / role / association conflated** | **Materialized as label version `r14.1`** (originals preserved byte for byte). All 43 units carry the original, the observations, the disposition, the source hash, the page, the image hash and binding, the role and association, AI provenance and uncertainty. **Binding: all 43 units.** 48 of 53 image uses regenerate byte-identically from the hash-verified source; 5 packet pages match at 0.97–0.995 against controls of at most 0.36. One reviewer literal was checked against the text layer and **not applied** (F11/C0226 hyphen). **Re-scored** with the original and the amended labels, separately named. The overlay **retypes** the small-batch criticals and **removes none** (their recorded targets are null). | [LABEL-AMENDMENT-R14.1.md](LABEL-AMENDMENT-R14.1.md) |
| **R14-04: broken worklist links; sample provenance** | **Fixed.** A new worklist: 43 items, 137 links, 0 broken (checked). Sample units get page links. The AI review is attached in separate blocks, and the human fields stay empty. **The sample disclosure is kept.** The next batch freezes its sample before predictions. | [PREPARATION-PLAN.md](PREPARATION-PLAN.md) §1; [worklist/](worklist/HUMAN-REVIEW-WORKLIST.r14.md) |
| **R14-05: the shortfall explanation** | **Corrected.** The gap is a shortage against fixed quotas, not an exhausted cohort. **Proposal (not executed):** a deterministic within-cohort reallocation with **35 verified distinct, eligible candidates**, one per slot and in stratum, which would give 450. The frozen selection is unchanged. Preparation of the 415 continues: the labelling plan, the BOQ triage (29 row tables, 7 matrices, 3 not BOQ) and the per-project workload. | [PREPARATION-PLAN.md](PREPARATION-PLAN.md) §2–5 |

**The next extraction change** (designed, not implemented): refuse `Rev.0`-type tokens as identities, with positive controls. See [EXTRACTION-NEXT-CHANGE.md](EXTRACTION-NEXT-CHANGE.md).

## Evidence

All under `evidence/`; every file is hashed in `EVIDENCE-MANIFEST.json`, and `verify_package_r14.py` was run after the final edit.

| Folder | Contents |
|---|---|
| `r14/` | The corrected harness, evaluator overlay, scripts, tests, `FREEZE-R14.json`, `REPRO-R14.json`, `REPLAY-BOQ.json`, the binding files, `LITERAL-CHECK.json`, the shortfall proposal, the BOQ triage, the workload estimate, `rescore/`, and `regression/` (JUnit, log, exit code) |
| `labels/r14/` | The amended label copies and `AI-REVIEW-AMENDMENT-r14.1.json` |
| `historical/` | The stored Review 13 BOQ runs, copied read-only with a deviation marker |
| `reviewer/` | Hashes of the reviewer's files used |
