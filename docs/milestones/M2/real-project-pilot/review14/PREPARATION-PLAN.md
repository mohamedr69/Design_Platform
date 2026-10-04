# R14-04 and R14-05: the worklist, the shortfall, and preparation before any further prediction

## 1. The worklist (R14-04)

**New file:** [`worklist/HUMAN-REVIEW-WORKLIST.r14.md`](worklist/HUMAN-REVIEW-WORKLIST.r14.md), with its `.json`.
- It has 43 items and **137 links, all checked, 0 broken**. The Markdown's own 137 links were checked too.
- Page images of findings point to the Review 07 packet at `../../review07/human-review-packet/pages/`.
- Crops point to the unchanged Review 13 copies.
- The four sample units have direct page links (their renders, copied into `worklist/pages/`).

**Why the Review 13 links broke.** They were written as `../review08/human-review-packet-v2/` joined with the packet's own `../../review07/…`. From `review13/worklist/` that resolves outside the milestone folder, which is why all 23 were broken. Review 13's file is preserved as submitted.

**The AI review in the worklist.** Each item carries the AI review in a separate `ai_review` block: status, observations, disposition, the effect in `r14.1`, binding, and provenance (AI, not human, not blind). The human answer fields are empty.

**The sample rule (disclosure kept).** The Review 13 20 % sample rule was written after the A/B runs began. It is prediction-independent by construction, but it was **not** frozen before predictions and is not a blind audit.

**For the next batch, the following are frozen before any prediction:**
- the population and the unit;
- the seed, the exclusions and the selected ids;
- the label version and the source hashes.

## 2. The shortfall (R14-05): a correct explanation and a proposal, not a changed selection

**The correct explanation.** The 35-document gap is a shortage against the **fixed quotas of the five small projects taken in full**:
- 27421 shop_drawing 14;
- 19144 approval_sample 8 and reply 2;
- 23091 scan 5 and submittal 1;
- 28745 submittal 3;
- 22510 submittal 1;
- 27421 submittal 1.

Their replacement pools ran out because of duplicates. That does **not** show the selected exploration cohort was exhausted. The five larger projects were sampled at 40–44 against a 90 cap, and they have **4,669 unused ranked candidates** in their frozen replacement orders.

**The proposal** (`evidence/r14/SHORTFALL-REALLOCATION-PROPOSAL.json`). It was not executed; `EXPLORATION-SELECTION.json` and `EXPLORATION-MANIFEST.json` are unchanged (their hashes are asserted), and no sealed project is involved.

The rule was fixed before any candidate was read:
- each short slot keeps its stratum;
- slots go to the larger projects (16830, 17428, 23323, 26208, 30549) in rotation;
- each takes the next unused candidate of that stratum in the **frozen rank order**;
- the 90 per-project and 45 % per-stratum caps are respected.

**Verification.** Every candidate was **read and SHA-256 hashed** through the approved read-only workflow (35 OneDrive placeholders hydrated). Each had to be distinct from:
- the 415 staged documents;
- the recorded duplicates;
- the exposed cohorts;
- earlier proposals.

**Result: 35 verified distinct, eligible candidates, one for each slot, all in their slot's stratum, 0 unfillable.**
- One candidate was rejected as duplicate content (`EP-16830/…/previous approval.pdf`).
- Per receiver: 17428 +14, 23323 +13, 26208 +5, 30549 +2, 16830 +1.
- If adopted, the cohort would have **450** distinct documents, and project sizes would be 16830 41, 17428 54, 23323 53, 26208 45 and 30549 46.

**This needs the owner's or reviewer's decision to adopt.** Until then, the frozen 415 stand and the work continues on them. The sealed cohort is never used to fill a gap.

## 3. Labelling before prediction (the plan for the remaining 403 documents)

| Step | Rule |
|---|---|
| Unit | Page labels in the v2-compatible format (`labels/LABEL-FORMAT.md`). Identities keep their role (own / listed / referenced / request / project / template / footer); states are clear / absent / unreadable / ambiguous. The `r14.1` addition, `supported_observations`, is used for printed facts with no supported target. |
| Batches | Per project, in `EXPLORATION-SELECTION` rank order. The label file of each batch is hashed and frozen **before** that batch's declaration and before any prediction exists for its documents. |
| Unresolved | Every unresolved label goes into that batch's worklist and stays unresolved until it is reviewed. A held item is never counted as a known negative. |
| Review | The mandatory items and a seeded 20 % sample are frozen in the batch declaration (population, unit, seed, exclusions, selected ids) before predictions. The review is currently by the owner-delegated AI reviewer; human signature fields stay empty unless a person signs. |
| BOQ | See §4. Rows are literal (part, quantity column, description; a "( n )" count in the description is recorded separately). The matrix layout needs its own row definition (floor × item cell) before it can be labelled. |
| Presentation | These documents are **not** presented as reviewed or labelled until their batch file exists. |

## 4. The 39 BOQ-name candidates, identified

`evidence/r14/BOQ-CANDIDATE-TRIAGE.json` is an AI visual triage of all 56 pages, done before any label or prediction. It is provisional.

| Class | Documents | Notes |
|---|---|---|
| Row-per-item BOQ tables | **29** | Design sheets, supplier quotations and material / equipment schedules, including rotated sheets. |
| Floor × item quantity matrix | **7** | The EP-17428 "schedule of materials" sheets. They need their own label unit before they can be scored. |
| Not a BOQ | **3** | A warranty letter, road geometric-design drawings (3 pages) and a shop drawing. |

**Pages inside BOQ documents that are not table pages (3).** They are accounted for explicitly: a blank letterhead page (#4 p2) and two terms-and-conditions pages (#8 p3, #22 p2). #3 p2 also carries terms under its table.

**Needs a person.** In the #26 and #27 schedules, page 2 heads its quantity column "MOUNTING".

The exploration BOQ set is therefore **29 row tables + 7 matrices**, against the master target of 40 BOQ sheets (the exposed sets supply the rest).

## 5. The corrected protocol and per-project workload (no run is scheduled)

`evidence/r14/WORKLOAD-ESTIMATE.json` gives two figures per project, under the corrected contract:
- the per-document budget is one per profile (12 calls and 120 s; the evidence reader caps a document at 8);
- 60 per project per rolling 24 h across all tracks;
- a new declared ledger scope, with nothing reset.

**Remaining work after the small batch:** 388 PDFs and 36 BOQ sheets.

| Project | PDFs | BOQ sheets | Requests at the observed rate | Requests at the cap bound | Minimum rolling days (observed / cap-bound) |
|---|---|---|---|---|---|
| 16830 | 36 | 6 | 231 | 720 | 4 / 12 |
| 17428 | 37 | 10 | 283 | 832 | 5 / 14 |
| 19144 | 42 | 0 | 185 | 672 | 4 / 12 |
| 22510 | 33 | 3 | 182 | 600 | 4 / 10 |
| 23091 | 51 | 2 | 249 | 864 | 5 / 15 |
| 23323 | 38 | 6 | 240 | 752 | 4 / 13 |
| 26208 | 37 | 4 | 211 | 688 | 4 / 12 |
| 27421 | 40 | 2 | 201 | 688 | 4 / 12 |
| 28745 | 32 | 2 | 165 | 560 | 3 / 10 |
| 30549 | 42 | 1 | 197 | 696 | 4 / 12 |

**How these figures are built.**
- The observed rate is the small batch's: B 2.0 and C 2.4 requests per document. BOQ sheets are assumed at half the 12-call cap per profile, because the stored BOQ runs exceeded 12 and their true rate under the contract is unknown.
- The day limit binds **per project**. The table is therefore a per-project minimum, not a sum over projects and not a calendar date.
- The ledger scope's request cap and provider latency bind in addition.

**Current allowance.**
- The rolling-24-hour counter shows EP-8430 at 60 (its day is full until the stored requests age out) and the exploration projects at 2–14.
- The small scope `r2x-small-2026-09-29` has 37 of 150 requests left. **It is not reused:** the next batch declares its own scope.

**No continuation is scheduled or launched by this task.** The next real run needs:
- this package reviewed;
- the batch's labels frozen;
- a new declaration.
