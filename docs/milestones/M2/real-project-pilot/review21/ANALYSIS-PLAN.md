# Analysis plan for the four-arm experiment (part of the DRAFT; nothing here has run)

## 1. Design and contrasts

Paired 2×2 on the same 27 planned documents (26 PDFs, 1 Word control): discovery ∈ {whole page (WP), title block (ROI)} × optional targeted reads X ∈ {off, on}. Held common in all four arms: the guard G, support v2 (rotation-correct clip + bounded local OCR), the required-first scheduling, the deadline policy D, the provider, prompts, schemas and caps.

| Contrast | Arms | Isolates |
|---|---|---|
| ROI alone | L1 → L2 | discovery input, with D and support common |
| X on whole page | L1 → L3 | extra targeted requests |
| X on ROI | L2 → L4 | extra targeted requests under ROI |
| ROI under X | L3 → L4 | interaction |

The optional deadline-off arm (L1−D) is **excluded from the core**: its question (D alone) does not justify about 55 more requests here. Any contrast between the accepted production reader and L1 is the **combined** G + support v2 + D policy, and is never called "rotation".

## 2. What the offline P0–P3 replay is, and is not

P0 (guard off, accepted region text) → P1 (+G) → P2 (+rotation-correct clip) → P3 (+local OCR fallback) re-validates each arm's **own captured responses** under nested support policies.

It is **conditional field-value validation on fixed captured responses**. It is not a replay of the deployed application: it cannot reproduce requests that were never issued, altered discovery images, scheduling or deadline outcomes, and it does not measure correctly associated business recovery (that is the evaluator's job on the live arms). In the submitted diagnostic (review20), the processing sandbox's cached OCR lines were **deliberately omitted** from every policy alike (a normalisation: the replay validates from the text layer and, in P3, fresh local OCR only). The live arms use the cached OCR lines as the application does.

## 3. Reporting gains by label status and by kind

Every gain table separates:
- **resolved** labels (confidence high, no uncertainty entry) from **unresolved** ones;
- **literal validation** (the value validated in the evidence layer) from **correctly associated recovery** (the evaluator's `recovered_clean` with the right target / revision association);
- **AI-layer confirmation** of a fact the deterministic path already accepted from a new accepted fact.

Example of the required separation, from the submitted continuation: the rotation gain was **four literal validations**, one of them the **unresolved** EML-09 identity; that is not four resolved truths and not four associated recoveries.

## 4. Paired comparison with clustering

For each contrast and field:

- **Unit:** the planned document (multi-page documents contribute their in-scope pages; the document is the pairing unit).
- **Statistic:** the paired difference in correctly associated recovery, d = mean over documents of (arm B − arm A) with each document scored 0/1 per field (unresolved-label documents excluded from the primary estimate and reported separately).
- **Uncertainty:** a cluster (document-level) paired bootstrap, 2,000 resamples, stratified by project so that the 10 projects are represented; 95% percentile interval. A single pooled Wilson interval **does not** describe a paired treatment difference and is not used for that.
- **Incremental requests:** reported with the difference as "recovered facts per extra request", with its own bootstrap interval.
- **Sample-size limit:** with 26 PDFs a contrast can detect only large effects; a pair with fewer than 12 documents attempted by both arms is **INCONCLUSIVE** by rule. Per-project and per-layout tables are descriptive only.
- **Multiple comparisons:** four contrasts × three fields; interpretation is pre-ordered (ROI alone on decision coverage first, then X on identity / revision); no result is promoted on the strength of an unplanned comparison.
- **Stop rules:** a critical acceptance on a resolved label stops the arm; three provider failures; any breaker / cap refusal (a budget stop, never raised).
- **No universal claim:** zero observed false accepts is reported with the rule-of-three bound (3/n) and is not a zero-risk claim; nothing generalises beyond the cohort.

## 5. Coverage and adoption gates (predeclared)

- **Coverage:** page / field-aware v3, every declared page, fail-closed on missing pages, unsupported inputs and beyond-scope pages counted, transport separate, extra facts outside scope counted.
- **Decision-coverage gate for ROI:** an ROI arm's consultant-decision coverage (completed read or verified absence, **including decisions outside the title block**) must be ≥ the matching WP arm's. Unknown (`located_incomplete`) is not coverage. The current title-block-only reading is expected to fail this gate; it is not a default-reader candidate on identity gains alone.
- **X gate:** ≥ 1 correctly associated fact per 8 extra requests at equal caps, no new false accept, interval excluding zero; otherwise "no evidence of benefit".
- **Deterministic support (G, clip, OCR):** offline on fresh responses; zero new wrong validations.
