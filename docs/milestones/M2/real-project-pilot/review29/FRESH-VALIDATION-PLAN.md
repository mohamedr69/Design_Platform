# Fresh validation plan: accepted baseline against the combined candidate

**This is a plan only. Nothing in it has run.**
- No document has been selected, staged or read for it.
- No label has been drafted.
- No model request, scope, schedule or dispatch exists.

Running it needs a separate owner authorization, which must name a frozen declaration hash, and a separately reviewed preparation package.

## 1. Question and design

**Question.** On documents never seen by any earlier M2 stage, does the combined candidate improve correctly associated recovery of identity, revision and consultant decision over the accepted baseline? It must also not add a critical acceptance or regress decision coverage.

**Two arms only. No single-switch or ROI arms.**

| Arm | Code | Configuration |
|---|---|---|
| B (accepted baseline) | `3d5607d` | The accepted application path: AI on, evidence reader off. This is the frozen four-arm A base. |
| C (combined candidate) | the Review 29 candidate commit | L3 switch set (G, Rsup, required-first, deadline, X) plus IG, CA, DR and PA. ROI is off. |

C reads the same staged copies as B, starting from B's database copy, as L1 to L4 did from A.

## 2. Documents

**Pool.** The pool is the 10 exploration projects of the frozen Round 2 selection (`review06/evidence/round2/ROUND2-SELECTION.json`), which the owner's Round 2 permission covers. The following stay out:
- the 10 sealed validation projects, which remain sealed;
- the 14 exposed regression projects.

**Unseen means all of the following.** A document's path and SHA-256 must appear in none of these:
- the exploration selection (`review13/evidence/manifest/EXPLORATION-SELECTION.json`, all 450 primary documents);
- any staged set, including the Round 2 small batch, the AI pilot, its continuation, H-06, R21 and the four-arm stage;
- any label file, including r14.1, r16.1, r21, r26.1 and r26.2;
- any run sandbox under `C:/t/r2x/runs`.

Exclusion is by both path and content hash, and a duplicate of an exposed file by hash is excluded.

**Size.** 20 documents, which is smaller than the four-arm experiment's 27. They are chosen by a seeded, stratified rule from names and file metadata only, before any content is read:

| Stratum | Documents |
|---|---|
| Drawing sheets, at least 2 of them scans | 6 |
| Submittal or review forms with a decision block in their name or folder | 5 |
| Multi-page specifications or datasheets | 4 |
| Transmittals and covering letters | 3 |
| Approval-folder documents | 2 |

At most 3 per project. When a draw is unreadable or encrypted, the next seeded replacement is taken, and every replacement is recorded.

**Frozen before labelling.** The selection script, seed, pool manifest and selection output are hashed into the preparation package before any page is rendered.

**Known limitation.** The documents are unseen, but their projects are not. The exploration stage exposed these projects' template families, so a gain on familiar templates cannot be told apart from a general gain. New projects would need a new owner permission and are not proposed here.

## 3. Labels

- **Frozen before prediction.** Every planned page up to the reader cap of 4 is labelled, together with no-record pages and the uncertainty list. The labels are frozen by hash before either arm runs.
- **Independent review.** A reviewer other than the drafter reviews every label, independently and against the source pages. An owner-delegated independent AI reviewer, as in Review 27, is acceptable but must be stated as such. Human review remains pending until a reviewer is appointed.
- **Conventions.** These are written and frozen before labelling. They cover continuation-page running headers, product codes, two numbering systems on one sheet, and stamps outside the title block.
- **No relabelling after prediction.** Post-run disputes go to a separate adjudication note that cannot change the score.

## 4. Scoring

- **Evaluators.** Evaluator .10 (`m2_eval6`, per-fact association) is primary, and .9 is reported beside it for continuity.
- **Eligibility and coverage.** Both follow the frozen v4 contract.
- **Denominators.** All 20 documents and all in-scope pages stay in every denominator. That includes unsupported, incomplete, budget-stopped, failed and unattempted items, and pages beyond the reader scope are counted.
- **Measures kept apart.** These are reported separately:
  - field read completed;
  - verified absence;
  - wrong absence;
  - accepted fact, correct or wrong;
  - held candidate, correct, wrong or on a page with no record;
  - correctly associated recovery.
- **Paired comparison of B against C.** The unit is the document. Resolved labels form the primary population, and unresolved ones are reported separately. Uncertainty comes from a document-cluster bootstrap with 2,000 resamples, stratified by project, seed fixed.
- **Minimum sample.** A field with fewer than 12 resolved documents carrying the fact, attempted by both arms, is INCONCLUSIVE.

## 5. Limits

The token limits are estimates, not hard bounds.

| | Arm B | Arm C |
|---|---|---|
| Application-visible requests, hard ceiling at reservation | 8 | 120 |
| Per-request estimated input / output tokens (pre-dispatch thresholds; an actual overshoot opens the breaker for later requests) | 90,000 / 20,000 | 90,000 / 20,000 |
| Scope estimated input / output tokens | 400,000 / 60,000 | 3,000,000 / 500,000 |
| Elapsed time from first use (a proposal, not a completion guarantee) | 4 h | 48 h |
| Rolling requests per project per day, all tracks counted | 60 (unchanged) | 60 (unchanged) |

- **Total ceiling:** 128 application-visible requests. That is less than the 234 the four-arm experiment used and less than its 688 cap.
- **Cost:** unknown.
- **Why 90,000 per request:** one L1 discovery request used 70,264 actual input tokens. The higher threshold avoids a trivial breaker stop on one large sheet, and it is declared before the run.

## 6. Stop conditions

| Event | Effect |
|---|---|
| Critical acceptance on a resolved label | Terminal stop, preserved. It is never resumed. |
| Three consecutive completed provider failures | Terminal stop, preserved. |
| Breaker, ledger, allowance or counter refusal | Budget stop. It is never raised or reset. |
| Rolling-day deferral | Wait for the window, then resume manually with the same tag. |
| Any binding difference or second writer | Refused before dispatch. |
| Critical acceptance on an uncertain label | Reported, not a stop, as in the four-arm rule. |

## 7. Adoption gates

All of the following apply. No default is selected by the run itself.

1. No critical accepted value on resolved truth.
2. Consultant-decision coverage does not regress against B. The coverage counted is completed reads plus verified absences where the truth has no decision, so wrong absences do not count.
3. Incomplete and unsupported items stay in every denominator.
4. No default rests on coverage or request count alone.
5. No default when the gain is clustered in one project or the matched population is below the minimum.

## 8. What the preparation package must contain before any authorization

- The selection script, seed, pool manifest, exclusion evidence and frozen selection.
- The frozen labels and their independent review, the conventions file and the uncertainty list.
- A declaration binding these files, both code commits, both configurations, the evaluators, the limits, the stop rules and the runbook.
- A dry run with a scripted provider over the staged copies.
- A budget decision card.
