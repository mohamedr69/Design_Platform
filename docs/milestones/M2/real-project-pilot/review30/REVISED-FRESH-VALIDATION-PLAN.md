# Revised fresh-validation plan (supersedes `review29/FRESH-VALIDATION-PLAN.md`)

**This is a plan and a draft declaration ([DRAFT-DECLARATION.json](DRAFT-DECLARATION.json)) only.**
- Nothing has been selected beyond metadata, staged, opened, rendered, labelled, requested or scheduled.
- Running it needs three things: an owner decision on the cohort ([COHORT-OPTIONS.md](COHORT-OPTIONS.md)), for Option B a new owner permission, and a budget authorization naming the frozen declaration hash.
- That frozen declaration hash will exist only after a reviewed preparation package.

## 1. Arms and code

| Arm | Code | Switches | Role |
|---|---|---|---|
| **B**, accepted baseline | `3d5607d` | evidence reader off: the accepted application path, AI on | baseline policy |
| **C**, combined candidate | `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` | G, Rsup, required-first, deadline, X, IG, CA, DR, PA (ROI off) | candidate policy |
| **R**, reference | `a8aaced` | the same switch set **without** IG, CA, DR and PA (the frozen L3 identity) | internal contrast for each switch's effect. It is not an arm of its own: it is evaluated on C's captured responses (§4). |

## 2. Selection contract (R30-02), fixed before any label exists

1. **Pool draw:** a metadata-only, seeded draw of a 72-document labelling pool from the chosen cohort: 40 paths with a review or approval signal, 20 with a drawing signal and 12 others, at most 12 per project. Seed `m2-r30-pool-2026-10-02`.
2. **Labelling:** independent labelling of every in-scope page of the pool (§3), frozen by hash.
3. **Count:** count the resolved documents carrying each fact.
4. **Extension:** if any field has fewer than 16, use **one** predeclared extension, a seeded draw of 36 more review-signal paths, and label it the same way. No second extension is allowed.
5. **Run-set selection, seeded (`m2-r30-runset-2026-10-02`):**
   - all resolved decision-bearing documents, up to 16;
   - resolved identity and revision documents without a decision, up to 8, until each of identity and revision reaches at least 16;
   - 4 resolved negative or no-record controls;
   - 2 unsupported-input controls;
   - at most 30 documents in all.

   **Only truth presence**, meaning whether the frozen label has the field, is used to meet these strata. No model output, candidate output, replay or earlier prediction is used. Ties fall to the seeded order.
6. **Decision scope:** if resolved decision-bearing documents stay below 12 after the extension, **decision accuracy is out of scope**, and the run **cannot close the M2 decision gate**. Identity and revision proceed.
7. **Freeze:** the final selection, labels, run-set manifest and replacement log are frozen and hashed **after replacements and before either arm runs**.

Negative and no-record pages, unsupported items, pages beyond the reader scope and unresolved labels all stay in their declared denominators. Feasibility: [FIELD-POPULATION-FEASIBILITY.md](FIELD-POPULATION-FEASIBILITY.md).

## 3. Labels

- **Drafting and review:** labels are drafted, then **independently** reviewed against the source pages by a reviewer other than the drafter. An owner-delegated independent AI review is allowed only if stated as such, and human review remains pending until a reviewer is appointed.
- **Conventions:** written and frozen before labelling. They cover continuation-page running headers, product codes, two numbering systems on one sheet, stamps outside the title block, code-and-legend decisions and receipt stamps.
- **After prediction:** no label changes after any prediction is seen. Disputes go to a separate, immutable adjudication note that **cannot change any score**.

## 4. Stochastic control (R30-04 item 8): one capture per fingerprint, replayed

The four-arm experiment showed that the same model gives different first readings across runs. Independent single reads in two arms therefore cannot isolate a policy effect, and this plan does not describe them that way.

**Chosen design: execute each identical prompt and image fingerprint once, and replay the captured response wherever it recurs.**
1. **B runs first.** Its application-path AI requests are captured.
2. **C starts from B's database copy,** so B's results are inherited and never re-requested. Everything B and C share is identical by construction.
3. **C's evidence requests run live once each.** Every response is captured with its fingerprint (task, tier, prompt text and image hashes), using the Review 29 replay format.
4. **R is computed offline** by replaying C's capture under the reference switch set. A request R would make that C did not, such as a targeted read C's identity guard suppressed or a discovery-only decision read, is executed live **once** as a **reference-only** request. It is recorded separately, never served to C, and counted against its own cap.

   The C-against-R contrast, meaning the effect of IG, CA, DR and PA, is then measured on **identical responses** wherever both arms asked the same thing.
5. **Variation probe:** a seeded 15% sample of C's dispatched fingerprints (seed `m2-r30-variation-2026-10-02`) is executed once more, bypassing the cache. It estimates first-read variation per task, as the rate of disagreeing literals. It is reported only and never changes a score.

**Why this design and not counterbalanced repeats.** Capture and replay removes first-read variation from every comparison that shares a request. That gives the exact policy contrast the safety outcomes need, at a small fraction of the cost of repeating every read. The probe still measures the variation the design cannot remove: the B-against-C contrast rests on one realization of C's reads, because B has no evidence reads.

## 5. Comparison and adoption contract (R30-04)

**Governing thresholds, quoted verbatim:**
- **AI-ACCURACY-POLICY.md §1** (sha256 `7efa891b…`): "Target zero observed errors among adjudicated automatically accepted critical facts, with at least 90% correct automatic recovery on clear applicable facts in the expanded M2 evaluation. Preserve the existing 98% minimum accepted-precision gate for other evaluated fields."
- **M2-ACCEPTANCE-REPORT.md, Correction 5 targets table:** ">= 98 % precision, accepted critical fields"; ">= 90 % recovery of readable critical fields"; "zero unresolved critical false acceptance".
- **MASTER-ROADMAP.md M2** (sha256 `f6dba0b2…`): "Completion additionally requires measured benefit from the selected AI profile, no unresolved critical false acceptance, correct automatic recovery and explicit cost/latency/review burden."
- **review21/ANALYSIS-PLAN.md §5, decision coverage:** "an ROI arm's consultant-decision coverage (completed read or verified absence, **including decisions outside the title block**) must be ≥ the matching WP arm's. Unknown (`located_incomplete`) is not coverage." It applies here as **C's against B's**. Wrong absences are never counted as coverage.
- **review21/ANALYSIS-PLAN.md §5, X gate**, the request-normalized benefit gate: "≥ 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero". It applies here as C against B **with B's and C's natural caps**, and the extra requests are C's minus B's.

**Rules:**
1. **Minimum population:** at least 12 matched resolved documents per claimed field (§2).
2. **Estimates:** paired document-level estimates, scored 0 or 1 per document and field for clean, correctly associated recovery. Resolved labels form the primary population, and unresolved ones are reported separately. Uncertainty comes from a document-cluster bootstrap with 2,000 resamples, stratified by project, seed `m2-r30-bootstrap-2026-10-02`, 95% percentile interval.
3. **Request-normalized benefit:** incremental correctly associated recovery per additional application-visible request, (net correct facts of C minus B) divided by (requests of C minus B), with its own bootstrap interval. The request difference is **part of the policy**, and nothing is reported as equal-budget accuracy.
4. **Accounting:** application-visible requests, provider-reported actual input and output tokens, cached input, estimated charges for timeouts with unknown usage, refusals before dispatch, timeouts and breaker events, per arm and for reference-only and probe requests.
5. **Concentration rule:** no default when more than half of C's net gain in any field comes from one project or one layout stratum, or when a field's matched population is below 12.
6. **Primary outcomes:** listed in §6.
7. **Selection:** **no default is selected by the run.** Meeting every gate makes a candidate eligible for a separate selection decision, and nothing more.

## 6. Primary outcomes, predeclared (R30-05)

| Outcome | Comparison |
|---|---|
| False or cross-page association count (evaluator .10, per fact) | C against B, and C against R |
| Clean revision recovery lost or gained under PA, by document | C against R on identical responses |
| Consultant decision under DR: completed reads, verified absences, **wrong absences**, accepted decisions (correct or wrong), held conflicts | C against B, and C against R |
| Critical acceptances on **resolved** and on **unresolved** truth | each arm |
| New requests and tokens, actual and estimated, used by DR and by the combined candidate | C against R, and C against B |

Secondary outcomes: identity and revision recovery and precision, held correct and wrong, request-normalized benefit, and the variation-probe disagreement rates.

## 7. Stop rules

| Event | Effect |
|---|---|
| Critical acceptance on a resolved label in C | terminal stop for C, preserved and never resumed |
| Three consecutive provider failures | terminal stop |
| Breaker, ledger, allowance or counter refusal | budget stop, never raised or reset |
| Rolling-day deferral | manual resume with the same tag, no automation |
| Binding difference or second writer | refused before dispatch |

## 8. What the run can and cannot show

- **Option B, all gates met:** evidence toward closing M2, still subject to independent review and the owner's selection decision.
- **Option A:** within-project regression safety and recovery only.
- **Neither:** improved general accuracy beyond the cohort, a default, M2 acceptance or M3.
