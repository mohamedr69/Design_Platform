# Reference labels — completeness, evidence and uncertainty (`r26-labels-2026-10-01.1`)

**Provenance.** The labels were AI-drafted by the Claude Opus 5.5 coding assistant from local renders and text layers of the hash-checked staged copies. They were then given a second pass by the same assistant. **They are not human-signed, not blind, and not independently reviewed.** No model or provider request was made, no prediction exists for these documents, and no value was taken from a file name. The labels are versioned beside the untouched R21 skeletons ([labels-r26/LABEL-MANIFEST.r26.json](labels-r26/LABEL-MANIFEST.r26.json) records their hashes), and they are frozen before any prediction.

## Completeness

| | Count |
|---|---:|
| Planned documents labelled (register layer) | **27 / 27** |
| In-scope pages labelled (page layer) | **42 / 42**: 30 component records + 12 no-record pages (contents, datasheets, continuation pages) |
| Pages beyond the reader's scope (long-PDF controls) | 54, declared unsupported, not labelled |
| Unsupported-input control (legacy `.doc`) | labelled at register level from text runs of the binary (not rendered) |
| Documents left blank or unresolved | **0**; truth-relevant uncertainty is labelled with confidence *medium* (10 documents) |
| Confidence | 17 high · 10 medium |

**Field coverage (page records).** Identity, printed revision, consultant decision, decision actor and decision location are kept separate on every record. Each record lists all printed identities with a role, and only one is marked `own_for_evaluation`. Decisions break down as:

| Decision | Records |
|---|---:|
| approved as noted | 6 |
| rejected (C. Revise & Resubmit) | 1 |
| UR (issued for approval, no decision) | 11 |
| n/a (no decision expected) | 12 |

Five records have no printed revision.

**Evidence.** Every page carries its source sha256, render sha256 and approximate regions for identity, revision and decision, plus the hashes of the zoom crops used ([labels-r26/R26-LABEL-EVIDENCE.json](labels-r26/R26-LABEL-EVIDENCE.json); crops in [label-evidence/](label-evidence/)). Every literal on a page that has a text layer was found in that text layer. Image-only pages were read on zoom crops. The labels parse through the frozen evaluator (`m2-pilot-eval-2026-09-29.9`): 31 expected components, all references readable, 7 readable consultant decisions and 24 no-decision labels.

## Off-title-block decision minimum

Every consultant decision in the sample lies **outside a drawing title block**:
- D04: tick on a material-submittal form;
- D16 and D18: ATK CODE B stamp plus handwritten status in the drawing field;
- D17: handwritten status only;
- D19: tick on a K&A submittal form;
- D22: tick on a submittal form, plus the review-status sheet.

That makes **6 confirmed** among the 24 primary documents, which meets the minimum of 4 by count. The R21 text screen was weak: only D04 of its 4 screened candidates is a real decision. D01, D02 and D03 matched note, authenticity or marketing text. Under a strict reading of the R21 rule, which counts only screened candidates, there is a shortfall of 3. The predeclared top-up was **not** performed, because this task freezes the 27-document sample; the strict-reading shortfall is disclosed here for the reviewer. Three of the six decisions (D16–D18) come from one project and one consultant; the analysis keeps them clustered. With no decision inside a title block, the ROI arms' decision coverage is measured entirely on off-title-block decisions.

## Uncertainty and conventions

- **Genuine (medium confidence, excluded from the critical-stop tripwire by the runner's predeclared rule):**
  - D03: datasheet product codes are not treated as document identity;
  - D08, D11: identity printed only as a sheet number beside a project number;
  - D12: set cover sheet, so the file-name sheet number is not used;
  - D15: revision taken from the latest table row;
  - D21: handwritten internal form number;
  - D24: the quotation reference equals the project number;
  - D25, D26: certificate and specification-section numbers taken as identities;
  - D27: `.doc` labelled without rendering.
- **Conventions (no truth uncertainty):**
  - D09: the drawing number's trailing `-01` is kept;
  - D19 pages 2–4 and D22 page 4: enclosed sheets carry no decision of their own, so they are labelled UR at page level and the package decision stays on the forms;
  - D22 page 1: the printed serial `0284`;
  - D17: decision actor inferred.

All are listed in [labels-r26/R26-UNCERTAINTY-AND-EXPOSURE.json](labels-r26/R26-UNCERTAINTY-AND-EXPOSURE.json).

**Disagreements:** none. The second pass covered every decision label, every rotated or scanned item and a seeded 25 % subset (D12, D08, D25, D19, D01, D20, D11), and changed no label ([labels-r26/R26-REVIEW-PASS.json](labels-r26/R26-REVIEW-PASS.json)).

**Exposure.** No document has a prior prediction; all were excluded by hash from every earlier predicted or held-out set. Round 2 first-page renders existed earlier. The r26 renders and crops were made for labelling only.

## What is specifically incomplete

1. **Independent review.** Step 4 of the R21 label manifest asks for an *independent* owner-delegated AI source review. The second pass here was by the same assistant, because no other model may be used in this task. The independent review of this package can supply that independence. Any label it changes becomes `r26.2`, frozen before any prediction.
2. **Strict off-title-block reading.** The shortfall of 3 (above) is disclosed, not topped up.
