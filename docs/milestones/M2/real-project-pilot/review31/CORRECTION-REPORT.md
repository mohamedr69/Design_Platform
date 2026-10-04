# Review 31 correction: selector, experiment contracts and an executable dry run

**Scope:** offline preparation only.
- The candidate stays frozen at **`a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d`** (`C:/t/iso/cand-r29`, clean).
- No candidate code, evaluator, label, frozen output or earlier package changed.
- There was no model call, provider contact or ledger scope; the ledger stays at 483 entries and 17 scopes.
- No OneDrive placeholder was downloaded, no new document was opened or rendered, and no label was drafted.
- No budget was requested, and no authorization document exists. The GPT bridge stays disabled and is not part of the workflow.

**What changed:**
- The corrected selector and a metadata-only cohort proposal.
- The experiment contracts as tested code: the capture store, the C-from-B state check, the stop rules and the B/C/R scorer.
- A dry run of the whole contract over the already-staged four-arm sample, with zero model requests.
- An immutable binding manifest.
- Version 2 of the plan, declaration and budget card.

| File | What it is |
|---|---|
| [COHORT-PROPOSAL.md](COHORT-PROPOSAL.md) | R31-01: the corrected selector, its evidence rows, and the proposed Option B cohort |
| [FIELD-POPULATION-FEASIBILITY.v2.md](FIELD-POPULATION-FEASIBILITY.v2.md) | R31-02: the ≥ 12-per-field gate, two predeclared extensions, then PREPARATION BLOCKED |
| [REVISED-FRESH-VALIDATION-PLAN.v2.md](REVISED-FRESH-VALIDATION-PLAN.v2.md) | the plan, superseding Review 30's |
| [STOP-AND-SAFETY-RULES.md](STOP-AND-SAFETY-RULES.md) | R31-04: stop rules for B, C, R and P, the shared-response contract and the C-from-B check |
| [DRY-RUN-REPORT.md](DRY-RUN-REPORT.md) | R31-05: the executed dry run |
| [DRAFT-DECLARATION.v2.json](DRAFT-DECLARATION.v2.json) | the draft binding, not for execution, which binds `BINDING-MANIFEST.json` by hash |
| [BINDING-MANIFEST.json](BINDING-MANIFEST.json) | R31-05: sha256 of every selector, harness, scorer, stop-logic, test and dry-run file, plus the code, coverage contract and threshold sources |
| [BUDGET-DECISION-CARD.v2.md](BUDGET-DECISION-CARD.v2.md) | R31-03: equal caps for B and C. It is a proposal only, and **nothing is requested** |
| [COMMANDS.md](COMMANDS.md) | how to re-run every test, the selector, the dry run and the checker |

## R31-01: selector

The Review 30 selector judged contractor freshness from free text and missed exposure. It is replaced by tested rules (`scripts/selector_core.py`, 4 tests) and structured used sets (`scripts/used_sets.py`).

- **Topology:** every root folder is classified explicitly as `project_at_root`, `container`, `contractor` or `no_projects`, and every EP folder as `project`, `project_with_nested_eps` or `nested_project`.
  - Results: contractor 264, no projects 61, container 7, project at root 2.
  - **175 ambiguous hierarchies fail closed**, and so does an EP found in more than one folder.
- **Contractors:**
  - **Canonicalization:** names are lower-cased, parentheses and generic words are dropped, and `&` becomes `and`.
  - **Alias rules**, failing closed: equal space-free forms, one token set inside the other, the same distinctive first word, or space-free similarity of at least 0.85.
  - **Result:** 242 clusters, 23 of them alias clusters, and 54 clusters already used.
- **Used sets:** these come from structured sources only:
  - the Round 2 selection;
  - the review05 holdout;
  - the pilot inventories and golden manifests;
  - **every M1/M2 project database**, 959 files read-only;
  - document paths in those databases;
  - milestone narratives and backend tests;
  - exploration primary and replacement paths, and the used-project inventories, failing closed on cross-project material.

  Together they give **199 used EPs** and 33 used contractor names.
- **Evidence:** every pick and alternate has an evidence row showing that the project is fresh (EP absent from every source, one folder, unambiguous) and that its contractor cluster is fresh (nearest used canonical name and its similarity, with the alias rules applied). See [COHORT-PROPOSAL.md](COHORT-PROPOSAL.md).
- **Reconciliation with Review 30:** each Review 30 pick and alternate is explained in `cohort/R30-PICKS-RECONCILED.json`.
  - 19905 (ARJ Engineering) is now excluded: its cluster aliases a used contractor.
  - 25883, 19199 and 28328 are excluded as ambiguous hierarchies.
  - 29255 is selected again.
  - The others stay eligible but were not drawn.

## R31-02: population before dispatch

`score_bcr.population_gate` is the rule:
- An M2-closure run dispatches **only** when identity, revision **and** decision each have at least **12 resolved, independently reviewed documents** carrying the fact.
- Otherwise the next predeclared extension is drawn: first `extension-1` (+36 review-signal paths), then `extension-2` (+36).
- If a field is still short after `extension-2`, the outcome is **PREPARATION BLOCKED**. There is no dispatch and no partial closure run, so the Review 30 "decision out of scope" path is withdrawn.
- **Feasibility with both extensions (144 documents):** expected decision count 36.8, worst case 17, P(below 12) = 0.001 at the low planning rate. The path capacity of the proposed cohort is sufficient under the per-project caps, and alternate 22317 enters in seeded order at extension 2.
- **Tests:** 2 tests cover the extend, extend, block sequence and unreviewed or unresolved labels.

## R31-03: one request-normalized rule

- **Equal caps:** B and C get **the same maximum allowance**: 240 requests each (8 per document × 30), the same scope token thresholds and the same elapsed bound.
- **The gate:** it is applied exactly as quoted: "≥ 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero".
  - The request count of C includes the requests it inherits from B. The difference is the policy cost and is measured, never equalized.
  - No unequal-cap gate exists: the scorer refuses one as not applicable, and a test proves it.
- **Consistency:** the declaration and the budget card state the same rule.
- **Ceiling:** the total rises from 332 to **556 requests, as a ceiling only**. Expected use is unchanged, at about 171.

## R31-04: stop rules and shared responses

**Stop rules** (`harness/stop_rules.py`, 8 tests):

| Event | Effect |
|---|---|
| Resolved-truth critical acceptance in **B** | the comparison is **INVALID** (baseline incomplete), and C does not start or stops |
| Resolved-truth critical acceptance in **C** | C stops terminally. The comparison is valid, with the result "failed the safety gate" |
| Resolved-truth critical acceptance in **R or P** | a reference finding only. It never stops a live arm and is never reported as a live safety stop |
| Unresolved-truth critical acceptance | reported, never a stop |
| Failure streaks | counted per lane |
| Budget stops | never raised |

**Shared-response harness** (`harness/capture_store.py`, 21 tests):
- one dispatch per bound fingerprint;
- B and C never share;
- any difference in document, page, crop, prompt, system, effort, model, output limit, tier, profile, variant or policy is a new fingerprint;
- R is served C's capture, including C's failures, and never re-sends it;
- R-only and probe requests never reach B or C;
- an interrupted dispatch is charged and never re-sent;
- every served answer keeps its provenance.

**C-from-B check** (`harness/state_check.py`, 5 tests):
- the recorded B file hash;
- equal logical content;
- no C-policy or unattributed evidence;
- no evidence-task cache row.

## R31-05: executable, packaged, bound

- **Dry run** ([DRY-RUN-REPORT.md](DRY-RUN-REPORT.md)): it ran the real candidate through the store, the stop guard, the state check, the probe, a resume drill and the scorer, with **0 model requests**, every live provider class blocked and the ledger unchanged.
  - **Population gate:** applied to the r26.2 labels, it returns **PREPARATION BLOCKED** (decision 6 < 12). A live run would stop there. Everything after it was executed only as an exercise.
  - **Transparency:** the rows of C and R are **identical** to the Review 29 replays of the same candidate.
- **Binding manifest:** written once (sha256 `2dfef08e94710cadff155cf460fb131184941cc511419ec16acf95ce08d55fba`). The draft declaration v2 (sha256 `19720ad96cd2b7f34d871c58627ad47436b3aba32a74ddcf7b50e25972818b5d`) binds it.
- **Package checker:** `scripts/verify_r31_package.py` re-runs all 51 tests from the packaged copies and re-verifies every binding.

## Owner decisions recorded

- **Label review:** the owner delegated independent label review to the Codex reviewer. It is recorded as **owner-delegated independent AI review, never human sign-off**.
- **GPT bridge:** it remains disabled and is not part of the workflow.

## Status

1. **Offline candidate:** accepted (`a8aaced`, frozen).
2. **Preparation package:** READY FOR INDEPENDENT PREPARATION REVIEW (not self-approved).
3. **Cohort:** Option B proposed, metadata only. A new owner permission naming the EP numbers is **required** and has not been requested. Sealed projects stay sealed.
4. **Labels:** none for the fresh run. Review is delegated to the Codex reviewer as independent AI review, not human sign-off.
5. **Budget:** none requested. The 556 figure is a proposal ceiling.
6. **Live run:** not started.
7. **Accuracy, default, M2 and M3:** accuracy unresolved; no default selected; M2 **CHANGES STILL REQUIRED**; M3 not started.
