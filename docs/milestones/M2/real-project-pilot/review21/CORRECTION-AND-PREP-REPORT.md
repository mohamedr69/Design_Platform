# Four-arm accuracy experiment: offline preparation, and H-06 (2026-09-30)

**Scope of this package:** offline preparation only. The frozen R21 candidate makes the four declared arms executable; the harness, dry runs, sample, workload and draft declaration are reviewable. **No model request was made for the experiment; no new model budget is approved or requested until this package has been reviewed.** M2 remains CHANGES STILL REQUIRED (see [STATUS.md](STATUS.md)).

## 1. Prerequisite switches (frozen candidate)

Frozen R21 candidate: commit in [candidate/FROZEN-COMMIT.txt](candidate/FROZEN-COMMIT.txt) (`58ff6fc…`), branch `ai-pilot-r21-2026-09-30` in the scratch clone, parent `69ee759`. Only `backend/app/ai/evidence_reader.py` changed in the application, plus tests. Details: [CHANGE-MAP.md](CHANGE-MAP.md); diff: [candidate/](candidate/).

- **One switch per behaviour:** G, support v2 (Rsup), required-first scheduling (Sched), deadline (D), ROI, X. The reviewed Review 18/19 finding was addressed directly: support v2 was reachable only through the targeted branch, and the deadline was fused with ROI; both are now independent switches used by every read path.
- **Flags-off behaviour preserved:** identities equal the accepted `3d5607d`'s; the legacy G / T / T+E identity strings are unchanged byte-for-byte (asserted by the identity-matrix test and the declaration writer). No default activation.
- **Distinct evidence identity per arm:** L1–L4 have pairwise distinct reader / policy strings; the result cache never crosses arms (dry chain: cache keys pairwise disjoint).
- **Unchanged:** role checks, retained evidence, association and incomplete-read rules, request caps, thresholds, merge / selection; no decision-region detector or new fallback.

**Arm execution matrix** (each demonstrated with a keyed scripted provider through the persisted processing path on a 270°-rotated A2 sheet; L2 / L4 on the real located crop):

| Arm | Discovery | Image sent | Required order | X fires | Rsup in force | Deadline stamp |
|---|---|---|---|---|---|---|
| L1 | `discover_page` | whole page | discover → identity → revision | no | yes (revision validated on the rotated page) | every request |
| L2 | `discover_region` | the located crop | same | no | yes | every request |
| L3 | `discover_page` | whole page | same, then `read_field_context` | yes | yes | every request |
| L4 | `discover_region` | the located crop | same, then `read_field_context` | yes | yes | every request |

Also verified in `tests/test_ai_pilot_r21.py`: a same-arm restart in the same sandbox reuses its own answers (0 requests) while another arm gets 0 cache hits; the per-document cap refuses the third request before dispatch and records `budget` / `not_attempted:budget`; the deadline floor refuses a request with 12 s left.

## 2. Regression checks on the frozen candidate

| Run | Tests | Failures | Errors | Skipped | Exit |
|---|---|---|---|---|---|
| 17 focused modules, flags off | 267 | 0 | 0 | 0 | exit 0 |
| flags T (G + targeted) | 267 | 0 | 0 | 0 | exit 0 |
| T+E raw (legacy E, no adapter) | 267 | 19 | 0 | 0 | exit 1 |
| T+E with the actual-crop adapter | 267 | 22 | 0 | 0 | exit 1 |
| arm L1 switches | 267 | 0 | 0 | 0 | exit 0 |
| arm L2 switches, actual-crop adapter | 267 | 22 | 0 | 0 | exit 1 |
| arm L3 switches | 267 | 0 | 0 | 0 | exit 0 |
| arm L4 switches, actual-crop adapter | 267 | 22 | 0 | 0 | exit 1 |
| r16.1 BOQ harness | 66 | 0 | 0 | 0 | exit 0 |
| coverage v3 + harness integration | 13 | 0 | 0 | 0 | 0 |
| full backend suite, flags off (final frozen candidate) | 1769 | 2 | 0 | 35 | exit 1 |

JUnit, logs and exit codes: [tests/](tests/).

Interpretation:
- **Flags off and T:** all pass (the T set includes the three repaired legacy scenarios, the 30-test R18 module, the 13-test R19 module and the 8 new arm tests).
- **T+E raw / actual crop:** the same disclosed failures as on `69ee759` (19 raw; 22 with the actual-crop adapter). They are the crop-contract fixture cases (decisions printed outside the real crop) and the two `partial` page outcomes explained in review19; the legacy assertions were not weakened. Their counts are asserted unchanged in the package checker.
- **L2 / L4 with the actual-crop adapter:** the same crop-contract failures as T+E (ROI is the same located discovery), with the 8 new arm tests passing. E's coverage loss is reported, not hidden.
- **Full suite, flags off:** run once on the final frozen candidate; the 2 known baseline failures (same tests and messages as on `3d5607d`, `c216206` and `69ee759`) remain, with exit code 1 recorded.

## 3. Harness (offline)

- **Coverage v3** ([scripts/coverage_v3.py](scripts/coverage_v3.py)): every declared page and document; `select_attempt` binds the arm's attempt to the declared source hash, profile, variant and policy (enforced by the caller `score_arms_v3.py` and tested); unsupported inputs and pages beyond the reader scope stay in the counts (`complete_in_scope` is reported apart from `complete`); unknown / unattempted / budget-stopped pages earn nothing; emitted facts outside the declared scope are counted.
- **Tests:** the seven draft coverage tests re-pointed at v3 (one expectation changed and marked: a long file whose in-scope pages are all usable is `complete_in_scope`, no longer `incomplete`) plus 6 integration cases: binding mismatches (source / context / policy), mixed supported / unsupported and missing pages, unattempted documents, transport success with unusable fields, budget / timeout / discovery failure, extra facts outside scope, field-specific matched subsets with IDs. Result: 13 passed ([tests/HARNESS-V3.xml](tests/HARNESS-V3.xml)).
- **Dry run of the actual runners** (scripted provider, synthetic stage of 5 files including a 6-page PDF, a raster-stamp sheet and a Word file; [dry/](dry/)): A base → shares → L1 → L2 → L3 → L4 → restarts → scorer, all exit 0. Verified ([dry/DRY-CHAIN-CHECK.json](dry/DRY-CHAIN-CHECK.json)): every arm starts from the same A base; cache keys pairwise disjoint; every request carries a deadline-bounded timeout; required reads precede optional ones per document; business hashes equal A's; the scorer reports the Word file as unsupported, pages 5–6 as beyond scope and 0 extra facts.
- **Two honest findings from the dry run:**
  1. **Restart accounting:** a restart under a new tag starts from a copy of the A base and re-requests everything; the ledger scope cap is the only durable aggregate limit, while the per-document 12 is per job. Before any live run, either the r16.1 durable per-(scope, arm, document) allowance is integrated into the document arms, or the declaration states that a restart forfeits the interrupted arm's remaining allowance. **This is a prerequisite not done here.**
  2. The synthetic long file's pages carry deterministic title-block numbers, so EV1 selected few of them; the cap refusal is demonstrated at reader level and in the earlier real runs, not in the dry chain.

## 4. Sample, labels manifest and workload (frozen; no prediction)

- **Selection rule frozen before labelling** ([declaration/R21-SAMPLE.json](declaration/R21-SAMPLE.json)): from the 415-document non-sealed manifest, every previously predicted or held-out content hash excluded (28), duplicates collapsed (0), staged copies hash-checked, **every page** classified. 27 planned: 24 primary (8 rotated text drawing sheets, 4 rotation-0 text drawing sheets, 3 drawing-sheet scans, 5 A3/A4 text, 4 A3/A4 scans; ≤ 3 per project, 10 projects) + 2 long-PDF controls (10 and 52 pages) + 1 Word control. **Off-title-block decision stratum:** a deterministic text/OCR screen found 15 candidates; the minimum of **4** was filled first (4 selected); shortfall handling after labelling is predeclared (top-up from the screened pool in seed order, before any prediction).
- **Stage:** [declaration/R21-STAGE.json](declaration/R21-STAGE.json): 27 files, 26 PDFs, 96 pages, **42 in the reader's scope**, 54 beyond (the long controls).
- **Labels:** NOT drafted here. [labels-r21/LABEL-MANIFEST.json](labels-r21/LABEL-MANIFEST.json) freezes the workflow (AI-drafted, page / region bound, decision **location** required, independent AI review, provenance kept, no human signature, frozen before any prediction) and skeleton files list every document and in-scope page to label. Exposure records: [labels-r21/EXPOSURE.json](labels-r21/EXPOSURE.json).
- **Workload** ([workload/R21-WORKLOAD.json](workload/R21-WORKLOAD.json)), built from every in-scope page and the observed ledger rates (price unknown, no dollar amount), conservatively assuming every in-scope page is triggered:

| Arm | Expected requests | Cap (proposed) | Upper bound | Expected input tokens (incl. cached) | Upper-bound input tokens |
|---|---|---|---|---|---|
| A base | 4 | 8 | 8 | ~0.08M | – |
| L1 | 118 | 160 | 312 | 1.64M | 5.21M |
| L2 | 118 | 160 | 312 | 1.40M | 4.66M |
| L3 | 135 | 180 | 312 | 1.81M | 5.21M |
| L4 | 135 | 180 | 312 | 1.57M | 4.66M |
| **Core** | **509** | **688** | **1,256** | **~6.5M** | ~19.8M |

  The review20 figure (~234 expected, cap 280) was a **first-page** estimate; the page-level table replaces it. Retries: none by the CLI adapter; a timeout is one request charged at its 45,544-token estimate. Escalations: none under EV1 (cap 2 declared).
- **Rolling-day schedule:** worst case per project per arm is 36 requests (3 PDFs × 12), so at most one arm per project per rolling day in the worst case (3 days); expected 2 days. Frozen order A, L1, L2, L3, L4; an arm processes a project only when the project's remaining day allowance covers that arm's worst case for it, otherwise the project is deferred for that arm (never partial, never a raised cap). Incomplete pairs enter the all-planned comparison as not attempted / budget for that arm; each pair reports all-planned, attempted-by-both and field-specific read-in-both sets with IDs; a pair with fewer than 12 attempted-by-both documents is INCONCLUSIVE.
- **Draft declaration:** [declaration/R21-DECLARATION.draft.json](declaration/R21-DECLARATION.draft.json), marked `DRAFT / NOT EXECUTED / NO NEW MODEL BUDGET APPROVED`, bound to the frozen candidate, sample, stage, labels manifest and workload. The analysis plan (paired 2×2, document-clustered bootstrap, gains by label status, gates) is in [ANALYSIS-PLAN.md](ANALYSIS-PLAN.md).

## 5. H-06 (the already-authorized control; separate binding)

**COMPLETED under the original frozen declaration `7b2513b2…`** (runner `cont_boq.py`, accepted `3d5607d` BOQ reader, the frozen queue, r16.1 matcher; the R21 reader is not bound into it). Preflight, runner logs, declared orders, model inputs / outputs and ledger rows: [h06/](h06/).

Ledger after the run: 128 / 150 settled over the original experiment; H-06 scopes: [('ai-pilot-r18-2026-09-30-H06-S', 'settled', 12), ('ai-pilot-r18-2026-09-30-H06-T', 'settled', 12)].

Targets, identified in the evaluation only (never in a prompt, queue or selection): L1 (wrong_accepted_target: emitted 4, printed 1), L9 (wrong_accepted_target: emitted 4, printed 1), L17 (control: emitted 2, printed 2), L19 (wrong_accepted_target: emitted 4, printed 1).

| Arm | Requests | Reached rows | Wrong targets detected | Control | Outcomes | Not reached | Full sheet |
|---|---|---|---|---|---|---|---|
| BOQ-S | 12 (cap 12) | 12 of 38 | 1 / 3 | confirmed_correct | {'caught_wrong_accepted': 2, 'confirmed_correct': 5, 'held_blind_right': 5, 'held_unread': 12, 'extra_row': 1} | 26 | False |
| BOQ-S at equal requests (12) | | | 1 / 3 | | {'caught_wrong_accepted': 2, 'confirmed_correct': 5, 'held_blind_right': 5} | | |
| BOQ-T | 12 (cap 12) | 12 of 38 | 0 / 3 | not_reached | {'held_blind_right': 12} | 26 | False |
| BOQ-T at equal requests (12) | | | 0 / 3 | | {'held_blind_right': 12} | | |

Per target row (reached = read by the arm; a target never reached is NOT a detected error):

- L1 (wrong_accepted_target): BOQ-S: caught_wrong_accepted; BOQ-T: not_reached
- L9 (wrong_accepted_target): BOQ-S: not_reached; BOQ-T: not_reached
- L17 (control): BOQ-S: confirmed_correct; BOQ-T: not_reached
- L19 (wrong_accepted_target): BOQ-S: not_reached; BOQ-T: not_reached

H-06 completion closes the experimental control only; it is not M2 accuracy or general safety evidence.

## 6. What is requested now

- Independent review of the frozen candidate, the harness, the sample rule and the workload table.
- After that review, the owner's decision on the **core budget: 688 requests cap (about 509 expected), about 6.5M input tokens expected, price unknown**, under a new scope family — with the two open prerequisites (durable per-document allowance; labels drafted and AI-reviewed) completed before any request.
