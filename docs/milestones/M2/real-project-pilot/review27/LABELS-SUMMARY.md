# Reference labels r26.2 — provenance, rulings and populations

**Version:** `r26-labels-2026-10-01.2`, frozen before any prediction ([labels-r26.2/LABEL-MANIFEST.r26.2.json](labels-r26.2/LABEL-MANIFEST.r26.2.json)). It sits beside r26.1 (review26, unchanged) and the R21 skeletons (unchanged), and is bound to the same source hashes.

**Provenance:**
- AI-drafted by the Claude Opus 5.5 coding assistant, from local renders and text layers of the hash-checked staged copies;
- a same-assistant second pass;
- an **independent owner-delegated AI source review** by the Codex reviewer in Independent M2 Review 27, separate from the drafting assistant. It covered all 42 in-scope pages, every decision record, the rotated and scanned items and the seeded subset, and is bound by sha256 to `INDEPENDENT-LABEL-REVIEW.json` (`d85127c7…`).

**Not** human-signed, **not** blind to the draft, no predictions consulted, and 0 provider requests. The legacy Word control **D27 was not visually verified** by the drafter or the reviewer. It stays an unsupported input in the denominator and earns no extraction-accuracy credit.

## Rulings applied ([labels-r26.2/R26.2-CHANGES.json](labels-r26.2/R26.2-CHANGES.json))

| Doc | Change | Unchanged |
|---|---|---|
| D17 | `decision_actor` becomes "unresolved (inferred: ATK …)", with `actor_attribution.state = inferred_unresolved`. It moves from "conventions" to **field-level uncertainty** | the readable decision value *approved as noted* (Code B, resubmit), identity and revision |
| D19 | adds the source literal **C. Revise & Resubmit** (D. Rejected blank) and the normalization note | the scored value `rejected` (the evaluator's coarse convention, not a business status); the enclosed sheets (pages 2–4) stay **UR** |
| D05 | adds the printed stage **ASBUILT** as descriptive metadata | identity `ELEC-B9-FA-101`, revision `0`, decision `UR`; no routing change |
| D27 | adds a verification note (not visually verified; no extraction credit) | its register-level label and unsupported treatment |

All other literals, confidences and no-record pages are unchanged. So is the **document-level uncertainty list** (D03, D08, D11, D12, D15, D21, D24, D25, D26, D27), which the runner reads to exclude documents from the critical-acceptance stop.

### How the metrics treat D17

The frozen evaluator scores the literal decision value and does **not** score the actor. D17's decision is scored as *approved as noted*, and its actor uncertainty affects no metric.

The runner's predeclared uncertainty rule is **document-level only**: listing a document there removes it from the critical-acceptance stop. The schema cannot express "decision value certain, actor inferred". The actor uncertainty is therefore recorded in a separate `field_uncertainty` list and the stop policy is unchanged, as this task requires. This limitation is disclosed, not worked around.

## Off-title-block populations (three separate questions)

| Population | Result |
|---|---|
| The original screen-selected candidates D01–D04 | only **D04** has a real marked decision (the screen was a selection aid; its 1/4 result is kept) |
| Decision-bearing documents among the frozen 24 primary documents | **six documents** (D04, D16, D17, D18, D19, D22), **seven page records** (D22 has two). **Five** have source-supported consultant or engineer attribution; D17's actor is inferred |
| Decision pages eligible for title-block cropping (the frozen `is_drawing_sheet`: longest side > 1,300 pt) | **D16, D17, D18 only**, all from EP-19144, two (D16, D18) with explicit approval stamps. D04, D19 and D22 decision pages are A4/Letter forms read by whole-page discovery ([evidence/ROI-POPULATION.json](evidence/ROI-POPULATION.json): 19 of 42 in-scope pages are drawing-sized) |

**Pre-run interpretation (the reviewer's, recorded before any prediction):** the minimum of 4 confirmed decisions is counted over the frozen 24 primary documents. The 5 source-attributed decision documents meet it without relying on D17. No top-up is requested or performed.

This does **not** supply four independently attributed, crop-eligible decision documents or four distinct decision layouts. ROI-specific decision coverage is a small diagnostic on three clustered sheets, reported separately from the A4 forms. The existing decision-coverage non-regression gate stays in force; crop eligibility does not prove what a runtime crop will contain.

## Unchanged notes

- **Pages and denominators:** 42 in-scope pages, 30 records and 12 no-record pages; 54 pages beyond scope; every unsupported or incomplete page stays in the denominators.
- **Continuation pages:** labelled no-record. A repeated own identity there is handled by the evaluator's cross-page association rule (Review 27 found no evaluator defect).
