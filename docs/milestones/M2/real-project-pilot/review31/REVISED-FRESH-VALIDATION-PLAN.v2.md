# Revised fresh-validation plan v2

This supersedes `review30/REVISED-FRESH-VALIDATION-PLAN.md`. **It is a plan and a draft declaration only** ([DRAFT-DECLARATION.v2.json](DRAFT-DECLARATION.v2.json)).

**Running it needs, in order:**
1. independent review of this preparation package;
2. a new owner permission naming the EP numbers of the cohort ([COHORT-PROPOSAL.md](COHORT-PROPOSAL.md));
3. labels that pass the population gate;
4. a budget authorization naming the frozen declaration hash.

## 1. Arms and lanes

| Lane | Code and switches | Role |
|---|---|---|
| **B** | `3d5607d`, evidence reader off | the accepted baseline. It runs first. |
| **C** | `a8aaced`, L3 switch set plus IG, CA, DR and PA | the combined candidate. It starts from a verified copy of B's database. |
| **R** | `a8aaced`, L3 switch set | the reference. It is served C's capture by content key, and a request C never made is sent once as reference-only. |
| **P** | n/a | the variation probe: a seeded 15% of C's answered dispatches, re-sent once. It is reported only. |

The lane contract is implemented and tested in `harness/capture_store.py`, `harness/state_check.py` and `harness/stop_rules.py` ([STOP-AND-SAFETY-RULES.md](STOP-AND-SAFETY-RULES.md)).

## 2. Selection, fixed before any label

1. **Cohort:** Option B, as proposed and once permitted. Sealed projects are excluded.
2. **Pool and extensions:**
   - the pool of 72 documents;
   - up to two predeclared extensions of 36 review-signal paths each;
   - the **population gate**: at least 12 resolved, independently reviewed documents for **each** of identity, revision and decision, or PREPARATION BLOCKED.

   Details are in [FIELD-POPULATION-FEASIBILITY.v2.md](FIELD-POPULATION-FEASIBILITY.v2.md).
3. **Run set**, seeded with `m2-r30-runset-2026-10-02`:
   - all resolved decision-bearing documents, up to 16 (at least 12 by the gate);
   - resolved identity and revision documents without a decision, up to 8, until each field reaches 16;
   - 4 negative controls;
   - 2 unsupported controls;
   - at most 30 documents.

   Only truth presence in the frozen labels is used.
4. **Freeze:** the selection, labels, run-set manifest and replacement log are hashed **after replacements and before B runs**.

## 3. Labels

- **Conventions:** written and frozen before labelling, as in Review 30.
- **Review:** independent of the drafter. The owner delegated it to the Codex reviewer, and it is **recorded as owner-delegated independent AI review, never as human sign-off**.
- **Counting rule:** only documents that are resolved **and** independently reviewed count toward the gate and the primary population.
- **After prediction:** no label changes after any prediction is seen. Disputes go to an immutable note that cannot change a score.

## 4. Execution order

1. **Preflight:** the bindings are checked against `BINDING-MANIFEST.json` and the declaration hash. Any difference refuses the run.
2. **B:** runs, with the tripwire checked after every document. On completion, B's database file hash is recorded.
3. **C-from-B check:** C's sandbox is a copy of B. `state_check.check_c_start` must pass: the recorded hash, equal logical content, no C-policy or unattributed evidence, and no evidence-task cache row.
4. **C:** runs through lane C of the capture store, with the tripwire after every document.
5. **R:** runs through lane R, served C's capture. Its own requests are reference-only.
6. **P:** the probe runs over C's answered dispatches.
7. **Scoring:** offline (`score_lane.py`, evaluator .10, coverage v4.3), then `score_bcr.evaluate`.

A **resume** never re-sends a bound fingerprint. A reserved request without an answer is charged and served as `interrupted_charged`, as the dry run's resume drill shows.

## 5. Comparison and adoption contract

**Thresholds, quoted verbatim** with source hashes in the declaration:
- **AI-ACCURACY-POLICY §1:** "Target zero observed errors among adjudicated automatically accepted critical facts, with at least 90% correct automatic recovery on clear applicable facts in the expanded M2 evaluation. Preserve the existing 98% minimum accepted-precision gate for other evaluated fields."
- **M2-ACCEPTANCE-REPORT:** ">= 98 % precision, accepted critical fields"; ">= 90 % recovery of readable critical fields"; "zero unresolved critical false acceptance".
- **MASTER-ROADMAP M2:** "Completion additionally requires measured benefit from the selected AI profile, no unresolved critical false acceptance, correct automatic recovery and explicit cost/latency/review burden."
- **review21 ANALYSIS-PLAN §5, decision coverage**, applied as C ≥ B **and C ≥ R**. Wrong absences and `located_incomplete` never count.
- **review21 ANALYSIS-PLAN §5, request gate:** "≥ 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero".

**Rules** (`harness/score_bcr.py`, 13 tests):
1. **Unit and population:** the document is the unit. Resolved, independently reviewed labels are primary, and unresolved ones are reported separately. Each field needs at least 12 matched documents.
2. **Estimates:** y = 1 for clean, correctly associated recovery. The paired difference uses a document-cluster bootstrap, stratified by project, with 2,000 resamples and seed `m2-r30-bootstrap-2026-10-02`.
3. **Request gate at equal caps (R31-03):** B and C have **the same maximum allowance** (§7).
   - Extra requests are C's total, including what it inherits from B, minus B's total. That difference is the policy cost.
   - The gate passes when net correct facts × 8 ≥ extra requests, with no new false acceptance and a bootstrap interval for the net gain per document that excludes zero.
   - **No unequal-cap version exists.** The scorer refuses one as not applicable.
4. **Safety and accuracy thresholds:**
   - zero critical acceptances on resolved truth in C;
   - accepted precision ≥ 0.98 for each field;
   - clean recovery ≥ 0.90 for each field.
5. **Concentration:** C is not eligible if more than half of its net gain in a field comes from one project or one stratum.
6. **Outcome:** one of ELIGIBLE FOR A SEPARATE SELECTION DECISION, NOT ELIGIBLE, INCOMPLETE, INVALID or PREPARATION BLOCKED. **No default is ever selected by the run.**

## 6. Primary outcomes, predeclared

As in Review 30:
- association errors, C against B and C against R;
- revision lost or gained under PA, C against R on identical responses;
- decision outcomes under DR: completed reads, verified absences, wrong absences, accepted decisions and held conflicts;
- critical acceptances on resolved and on unresolved truth, for each lane;
- new requests and tokens.

## 7. Limits and stop rules

**Caps:**
- B 240 and C 240 (equal);
- R reference-only 40;
- probe 36;
- **at most 556**, with expected use about 171.

The equal allowance for B and C covers the request cap, the scope token thresholds (7,000,000 / 1,400,000 estimated) and the elapsed bound (72 h). Cost is unknown. The stop rules are in [STOP-AND-SAFETY-RULES.md](STOP-AND-SAFETY-RULES.md), and the budget proposal is in [BUDGET-DECISION-CARD.v2.md](BUDGET-DECISION-CARD.v2.md).

## 8. What the run can and cannot show

- **Every gate met on the permitted Option B cohort:** this is evidence toward closing M2, still subject to independent review and a separate owner selection decision.
- **Never shown:** a default, production use, M2 acceptance by itself, or M3.
