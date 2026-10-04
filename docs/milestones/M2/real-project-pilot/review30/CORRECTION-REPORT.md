# Review 30 correction: Review 29 package corrections and fresh-validation design

**Scope:** documentation, package checker and validation preparation only.
- No candidate code, test, evaluator, frozen replay output, label or historical package changed.
- No model call was made, and no new source-document content was opened, rendered or staged.
- No budget scope, authorization, schedule, validation, production change or M3 work was created or started.
- No API key was requested, and the GPT bridge was not used.

The final candidate is **`a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d`** (`a8aaced`, in `C:/t/iso/cand-r29`), which the independent reviewer accepted against the bounded offline criteria.

## R30-01: package identity and counts

- **Stale statements found.**
  - `review29/CHANGE-MAP.md` named the first candidate commit `a4ce6a3` as the candidate.
  - It gave two test counts that disagree with the JUnit evidence `review29/tests/FOCUSED-final.xml`: identity guard 39 against 40, and adjudication 18 against 20.
  - `review29/COMMANDS.md` named `a4ce6a3` without marking it as historical.
- **Overlay.** The frozen Review 29 package is not edited. Version 2 of both documents is in [review29-overlay/](review29-overlay/CHANGE-MAP.md), and [review29-overlay/OVERLAY.md](review29-overlay/OVERLAY.md) lists exactly which Review 29 documents it supersedes.
- **Reconciled counts.** Identity guard 40, adjudication 20, decision region 14, association 6 and persistence 12, for 92 in total. The `evidence_reader.py` diff is +547 / −12.
- **Historical mentions.** `a4ce6a3` remains only where it is explicitly historical: the first candidate commit, its patch, its contract freeze and its earlier test run.
- **Checker.** `scripts/r30_checks.py` adds two checks:
  - `check_commit_statements` fails when a current-candidate statement names a non-final commit, or when a historical commit is presented as final, marker or not;
  - `check_test_counts` fails when a reported per-module count or suite total differs from the JUnit evidence, or names a module absent from it.
- **Checker tests.** `scripts/test_r30_checks.py` has 10 tests, all passing (`tests/CHECKER-TESTS.xml`). They prove three things:
  - the stale-commit, historical-as-final and stale-count cases fail;
  - the original Review 29 `CHANGE-MAP.md` and `COMMANDS.md` fail;
  - the overlay and the unchanged Review 29 documents pass.
- **Package checker.** `verify_r30_package.py` runs both checks over every owner-facing document of this package and the overlay, against this package's manifest candidate.

## R30-02: achievable field populations

[FIELD-POPULATION-FEASIBILITY.md](FIELD-POPULATION-FEASIBILITY.md) and §2 of the plan set the rules:
- at least 12 resolved, matched documents per claimed field, with a selection target of 16;
- a two-stage, seeded, predeclared selection, in which replacement uses frozen-label truth presence only;
- one extension at most;
- freezing after replacement and before prediction;
- all denominators retained.

Identity and revision are feasible. **Decision is not guaranteed:** the worst case is 11 even after the extension. If fewer than 12 resolved decision-bearing documents result, decision accuracy is out of scope and the run cannot close the M2 decision gate. This is declared now.

## R30-03: cohort options

[COHORT-OPTIONS.md](COHORT-OPTIONS.md) gives two options, built from metadata only. No permission is assumed for either.
- **Option A, within-project:** templates are exposed, so it shows regression safety only.
- **Option B, fresh projects:** six projects from six contractors untouched by M2, with four alternates. 207 referenced projects and their 59 contractors are excluded, sealed stay excluded, and a **new owner permission** is required.

**Recommended:** Option B for M2 closure.

## R30-04 and R30-05: comparison, adoption and outcomes

[REVISED-FRESH-VALIDATION-PLAN.md](REVISED-FRESH-VALIDATION-PLAN.md) and [DRAFT-DECLARATION.json](DRAFT-DECLARATION.json) bind the following:
- the M2 thresholds, quoted verbatim with source hashes;
- the minimum of 12 matched resolved documents per claimed field;
- paired document-level estimates, a project-stratified cluster bootstrap with 2,000 resamples and fixed seeds;
- the request-normalized benefit gate, with natural caps and the request difference treated as policy;
- full token, timeout, refusal and breaker accounting;
- the one-project-or-layout concentration rule;
- PA revision loss and DR decision recovery and cost as primary outcomes;
- stochastic control by executing each fingerprint once and replaying captures, with a reference contrast and a reported variation probe;
- adjudication only in an immutable note that cannot change scores.

[BUDGET-DECISION-CARD.md](BUDGET-DECISION-CARD.md) proposes caps (at most 332 requests, cost unknown) for a later decision. **No budget is requested.**

## Checks

`evidence/PACKAGE-CHECK.json` covers the following:
- the manifest;
- links;
- the commit and count checks over all owner-facing documents and the overlay;
- the checker tests;
- the candidate commit and its clean tree;
- `review29/` and `four-arm-final/` unchanged, by manifest and every file;
- labels r26.1 and r26.2, evaluators .9 and .10, and the baseline and `719e8de` trees unchanged;
- the ledger unchanged (483 entries);
- verbatim thresholds present in their sources;
- the draft declaration not executed;
- the fresh candidates metadata-only;
- no authorization document in the package.

## Status, stated separately

| Item | Status |
|---|---|
| Offline candidate acceptance | `a8aaced` accepted by the independent reviewer against the bounded offline criteria (Review 30) |
| Package correction readiness | READY FOR INDEPENDENT PREPARATION REVIEW, if `evidence/PACKAGE-CHECK.json` is ok |
| Cohort permission | Option A covered by the Round 2 permission. Option B **not permitted**: it needs a new owner permission naming the EP numbers. Sealed projects stay sealed. |
| Labels | none drafted for the fresh run; r26.1 and r26.2 unchanged |
| Budget | none requested or approved; the card is a proposal |
| Live run | not started; no scope, schedule or dispatch |
| Accuracy, default, M2, M3 | accuracy unresolved; no default selected; **M2 CHANGES STILL REQUIRED**; M3 not started |
