# DRAFT / NOT EXECUTED: isolated accuracy experiment (prospective declaration)

**Status: DRAFT. NOT EXECUTED. NOT AUTHORIZED TO RUN.**

- No model request, application change, sealed content or residual allowance is used by this document.
- Running it needs:
  - the prerequisite implementation (section 9), reviewed;
  - a frozen, hashed final declaration;
  - **a separate owner budget decision** (section 10).
- The residual of the original 150-request experiment is **not** assumed to fund it.

Structured form: [EXPERIMENT-DRAFT.json](EXPERIMENT-DRAFT.json). Supporting offline evidence (exposed data, no model calls):
- [isolation/OFFLINE-ISOLATION-REPLAY.json](isolation/OFFLINE-ISOLATION-REPLAY.json)
- [feasibility/SAMPLE-FEASIBILITY.json](feasibility/SAMPLE-FEASIBILITY.json)
- [coverage-v3/](coverage-v3/)
- [workload/OBSERVED-WORKLOAD.json](workload/OBSERVED-WORKLOAD.json)

## 1. Question and the named changes

What does each change contribute to **correctly associated** recovery of own identity, revision and consultant decision, and at what coverage and request cost, on documents never predicted before?

| Symbol | Change | Kind | How it is isolated |
|---|---|---|---|
| G | bare-revision-token guard | deterministic validator | offline, on identical captured responses (P0→P1) |
| Rrot | rotation-correct clipping of the text layer | deterministic support | offline, on identical responses (P1→P2) |
| Rocr | local OCR fallback when a region has no text | deterministic support | offline, on identical responses (P2→P3) |
| D | deadline policy: request timeout = min(provider timeout, remaining job time); no request started with < 20 s left | request policy | optional live arm L1−D against L1 (section 3) |
| ROI | located title-block discovery for drawing sheets | discovery (model input) | live: L1 against L2, with G / Rrot / Rocr / D held common |
| X | optional targeted context reads (required-first) | extra requests | live: L1 against L3 and L2 against L4, everything else common |

The earlier nested proposal changed G together with R, bundled Rrot with Rocr, and bundled ROI with D. None of those contrasts is used here.

## 2. Evidence already available (offline, exposed data: diagnostic only)

The replay applies the same stored S model responses (25 own-identity / revision observations with a region) under nested policies. Validation and OCR input are held fixed.

| Step | Pilot S (13) | Continuation S (12) | Wrong validations |
|---|---|---|---|
| P0→P1 (G only) | no change | no change | 0 |
| P1→P2 (Rrot only) | +3 correct (all rotated pages) | +4 correct (all rotated pages) | 0 |
| P2→P3 (Rocr only) | +1 correct (a scanned letter) | 0 | 0 |

This is **exposed-data diagnostic evidence** (the documents are exposed, and the labels are AI-drafted or AI-reviewed). It motivates the design; it is not a result of this experiment.

## 3. Arm matrix (frozen before fresh predictions)

**Held common in every live arm L1–L4:** G on; support policy P3 (Rrot + Rocr); deadline policy D; provider, model aliases, prompts, schemas and policy identities (section 6); EV1 triggers; per-document caps.

| Arm | Discovery | X (targeted reads) | Purpose |
|---|---|---|---|
| **L1** WP | whole page (accepted discovery) | off | reference for the model-dependent contrasts |
| **L2** ROI | located title block | off | L1→L2 = ROI alone |
| **L3** WP+X | whole page | on | L1→L3 = X on whole-page discovery |
| **L4** ROI+X | located title block | on | L2→L4 = X on ROI; 2×2 interaction with L1–L3 |
| *(optional)* L1−D | whole page | off, **D off** | L1−D→L1 = deadline policy alone |

**Offline, on each live arm's own captured responses, with no request:** P0, P1, P2 and P3 re-validation. These isolate G, Rrot and Rocr **on fresh data**, from identical responses.

**Not an arm:** the accepted production reader exactly as deployed. Its behaviour equals L1's captured responses under P0 with D off. The only live difference is D, which is what the optional L1−D arm measures. Any contrast between the accepted reader and L1 is labelled the **combined** G+Rrot+Rocr+D policy, never "rotation".

## 4. Sample rule and labelling workflow

**Eligible pool:** the 415-document non-sealed exploration manifest (sha `ee9df7b5…`), minus every document ever predicted or held out, matched by sha256. That excludes the small batch, the pilot, the continuation, both BOQ sheets and the review05 holdout sets (28 excluded, 387 remaining).

**Available within the reader's 4-page scope:** 283 PDFs across 10 projects.

| Stratum | Available |
|---|---|
| drawing sheet, rotated, text layer | 64 |
| drawing sheet, rotation 0, text layer | 33 |
| drawing sheet, scan | 11 (8 rotation 0 + 3 rotated) |
| A3 / A4, text layer | 94 |
| A3 / A4, scan | 81 |

Beyond the reader's scope: 89 PDFs with more than 4 pages, and 15 Word files.

**Proposed sample: 24 documents**, order = sha256(seed ‖ doc_key), with a new seed declared at freeze.

| Stratum | Documents |
|---|---|
| Rotated text-layer drawing sheets | 8 |
| Rotation-0 text-layer drawing sheets | 4 |
| Drawing-sheet scans | 3 |
| A3 / A4 text layer | 5 |
| A3 / A4 scans | 4 |

- **Per project:** at most 3 documents from any one project.
- **Coverage controls:** 2 PDFs with 5+ pages and 1 Word file. Their pages beyond scope and the Word file are reported `unsupported`, never truncated or dropped.
- **Planned denominator:** 27 documents.

**Labels, frozen with hashes before any prediction:**
- Drafted by an AI labeller from source renders and the text layer.
- Each fact bound to a page and region, with its role (own / referenced / template) and association (target, revision).
- **Consultant decision:** present or absent, marked option, actor, legend, and **location relative to the title block** (inside / outside / none). The decision gate depends on this field.
- **Independent AI source review** (owner-delegated, not human) of every decision label, every rotated or scanned item, and a seeded 25% random subset, before scoring.
- Ambiguous evidence stays **unresolved** and is reported separately.
- No prediction becomes truth. **No human signature is implied or filled.**

## 5. Coverage and accuracy reporting

- **Coverage:** page- and field-aware (prototype `coverage_v3_draft.py`, 7 passing unit tests; tried on the stored pilot outputs).
  - **Every declared page** of every planned document is in the denominator. Missing pages **fail closed**. Pages beyond the reader scope and unsupported inputs are marked, not dropped.
  - Unattempted files, timeouts, budget stops and policy-unselected pages are all counted.
  - Discovery absence is distinct from a completed read.
  - Transport state is reported separately.
  - On the stored pilot, a first-page view would have hidden that SOV's page 2 was never read.
- **Accuracy, per field, arm, project and layout stratum:**
  - accepted-precision numerator and denominator;
  - critical false accepts, split by label status;
  - correctly associated recovery;
  - held evidence;
  - extra predictions and negatives.
- **Uncertainty:**
  - Wilson 95% intervals for every rate.
  - With zero observed false accepts, report the rule-of-three upper bound (3/n), never "zero risk".
  - Per-project and per-layout tables alongside pooled results.

## 6. Freeze list (the final declaration must bind all of these)

- **Code:** the accepted `3d5607d`; the candidate commit with the flags per arm (section 9); the reader, policy, prompt and schema identities of each arm.
- **Provider:** the existing claude-code provider, aliases small = sonnet, standard = opus; actual models recorded per response; no provider or model change.
- **Cache:** result cache on; each arm starts from a copy of one common A-base sandbox; arm identities differ, so there is no cross-arm reuse; no earlier evidence is loaded.
- **Inputs and scoring:** the sample manifest and stage hashes, the labels and review hashes, evaluator .9 (unchanged), the coverage v3 scorer (after review), and the runners.
- **Limits:** 12 requests per document per profile, 2 escalations, the 120 s job budget, 60 per project per rolling day across all tracks, and the per-request token breaker (70,000 total input including cached). The breaker is enforced after completion and is not provider-enforced.

## 7. Gates (declared in advance; success cannot be redefined afterwards)

| Gate | Requirement |
|---|---|
| **Safety** | No critical false acceptance on a resolved label (a stop rule). Report the rule-of-three bound. |
| **Decision coverage (adoption gate for ROI)** | ROI arms' consultant-decision coverage (completed read or verified absence) must be **≥ that of the matching WP arm**, counting decisions **outside the title block**. Unknown (located-incomplete) is not coverage. ROI is not adopted on number or revision gains alone. With the current title-block-only design this gate is expected to **fail**; a separate decision-region strategy (section 8) would be needed first. |
| **X adoption** | Incremental correctly associated recovery ≥ 1 fact per 8 extra requests, at equal document caps, with no new false accept. If the confidence interval includes zero, the result is "no evidence of benefit", not adoption. |
| **Deterministic support (Rrot, Rocr)** | Measured offline on fresh captured responses. Adoption also needs zero new wrong validations, and a code review of the OCR time bound. |
| **Coverage honesty** | Every planned page and file is reported; timed-out requests are charged at their estimate. |

## 8. Proposed decision-region strategy (NOT implemented, NOT run)

The goal is to recover consultant decisions outside the title block without whole-page discovery for every sheet.

1. **Candidate detection, deterministic and without model calls:**
   - decision cues in the text layer or OCR anywhere on the page (APPROVED, NO OBJECTION, REVISE AND RESUBMIT, CODE A/B/C, REJECTED, stamp words);
   - raster-stamp detection by image analysis: saturated-ink blobs or rectangular stamp contours;
   - each candidate gives a second located crop.
2. **Reading:** one `read_decision` request per candidate crop, capped at 2 per page. The legend / actor / target rules are unchanged.
3. **No candidate:** the decision stays **unknown** (`incomplete:located_region_only`), never absent. An optional low-resolution decision-only whole-page pass would be a separate, costed arm.
4. **Cost:** about +0.3 to +1 request per drawing page. This needs measuring: it is the share of pages with candidates.
5. **Validation needs before any live use:**
   - a labelled set of stamp and decision positions;
   - offline candidate recall and false-candidate rate, per layout;
   - OCR time bounds;
   - persisted-stage tests on real crops, including raster stamps.

## 9. Prerequisite implementation (NOT done here; needs its own review before freeze)

- Decouple D from E: a separate flag for the deadline policy, so ROI and D can vary independently.
- Separate flags for Rrot and Rocr, or keep them common (as specified above) and isolate them only offline.
- Move coverage v3 into the scorer, fail-closed, with the unit tests.
- Optional: the decision-region strategy (section 8), only with its validation evidence.

## 10. Workload and budget (tokens and requests only: price unknown, no dollar amount)

**Observed rates** (durable ledger, all original-experiment scopes):
- Requests per planned document for arms not stopped by a cap: S 2.14, G 2.17, T2 2.29.
- Pilot T is a breaker-truncated lower bound.

| Task | Input tokens incl. cached: mean / p90 / max | Output mean | Latency p50 / p90 | Unknown usage |
|---|---|---|---|---|
| discover_page (whole page) | 26.5k / 55.1k / 81.6k | 4.6k | 39 s / 168 s | 2 of 34 (charged at estimate) |
| discover_region (ROI) | 13.9k / 26.0k / 26.0k | 3.5k | 36 s / 57 s | 1 of 6 |
| read_identity / read_revision | 7.8k / 6.1k | 0.2–0.4k | 6–7 s | 0 |
| read_field_context (X) | 6.7k | 0.3k | 7 s | 0 |
| read_decision | 6.2k | 0.4k | 8 s | 0 |

**Proposed workload** for 24 fresh documents (plus 3 coverage controls whose unsupported parts cost 0 requests):

| Arm | Expected requests | Declared cap | Expected input tokens incl. cached |
|---|---|---|---|
| L1 WP | ~55 | 65 | ~0.85M |
| L2 ROI | ~52 | 65 | ~0.55M |
| L3 WP+X | ~65 | 75 | ~0.95M |
| L4 ROI+X | ~62 | 75 | ~0.65M |
| *(optional)* L1−D | ~55 | 65 | ~0.85M |
| **Total, core L1–L4** | **~234** | **280** | **~3.0M** input, ~0.3M output |
| **Total, with L1−D** | ~289 | 345 | ~3.85M input |

- **Hard ceiling (never raised):** 12 per document per arm, so 27 × 12 × 4 = 1296 for the core arms. The declared caps are the binding limits.
- **Project rolling day:** at most 3 documents per project × 4 arms × about 3 requests ≈ 36 per project, under the 60 limit, so a single-day run is feasible. A multi-day schedule is declared if needed.
- **Wall clock:** about 25–60 minutes per arm, dominated by discovery latency.
- **Offline replays** (G / Rrot / Rocr on fresh responses): 0 requests.

**Budget decision requested of the owner, only after this draft is reviewed:**
- a new allowance of **280 requests** for the core design (or 345 with L1−D), under a new declared scope with the limits above; or
- a smaller N with proportionally smaller caps.

The residual of the original experiment is not used for this.
