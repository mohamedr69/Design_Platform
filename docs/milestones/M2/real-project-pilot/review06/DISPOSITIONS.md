# M2 Review 06: dispositions R6-01 to R6-05 and H-01 to H-06

**Terms.** "Closed" means corrected, with tests and evidence. "Partly" means improved, with the remaining gap named. "Open" means not resolved; it is a blocker when it gates M2.

**Where things live.**
- Source paths are in the isolated candidate, `C:/t/iso/ep-platform/backend`. Its exact diff and new files are in `evidence/candidate.diff` and `evidence/candidate_new_files/`.
- Evidence paths are relative to `evidence/`.

**Holdout status.** The Review 05 holdout (H-cases) has been used for correction since Review 05. Every holdout number here is an **exposed-corpus regression result, not a generalization claim**.

## Evaluator findings

| ID | Disposition | Source | Tests | Evidence |
|---|---|---|---|---|
| **R6-01** Duplicates hid wrong critical values | **Closed** | `scripts/m2_eval4.py`: `associate`, `pool`, `judge_fields`, `totals.redundant_copies` / `conflicting_emission_sets` | `test_m2_eval4.py` 1–3, all failing on .3 | `reviewer_probes_eval4.txt` (conflicting_duplicate: 2 critical). `eval4/*.json`: Candidate C 0 → 2 critical |
| **R6-02** Accepted decision on conflict truth evaded the gate | **Closed** | `decision_truth` conflict state; `accepted_on_conflict` is counted as accepted and critical; `conflict_resolved_silently` for revisions | tests 4–5 | probe accepted_approval_on_conflict: `decision: accepted_on_conflict` is critical |
| **R6-03** Denominators depended on output | **Closed** | `evaluate` builds expected records from truth for every labelled document; `execution_outcome`; `revision_truth` / `decision_truth` states; association by a single component | tests 7–11 | probes missing_execution_row, absent_revision_missing_record, known_decision_unknown_reference, absent_decision |
| **R6-04** Raw evidence accounting incomplete | **Closed** for the evaluator | `adapt_observation` for every observation shape; separate register, raw, projection and evidence layers | tests 12–14 | EVALUATOR.md: Candidate C raw identity 223/363, revision 185/310, decision 29/80 |
| **R6-05** Recovery, confident BOQ errors and the untested real model block M2 | **Open (blocker)**, partly addressed | see H-cases, BOQ-RESULTS, REAL-MODEL-RESULTS | — | recovery is still below 90% on every field; BOQ critical 5 → 4 (pilot) and 4 → 3 (holdout); the real model now runs on eligible projects but is not yet sufficient |

Evaluator .4 and BOQ evaluator .3 were frozen before any AI-variant run (`FREEZE-evaluators.json`).

## Holdout extraction cases

Parser `parse-2026-09-29.8`, `titleblock-3`, fields `fields-2026-09-29.1`, transmittal observe `transmittal-observe-2026-09-29.1`, sheet extractor `2026-09-29.1`.

| ID | Case | Disposition | What the candidate now reads | Source | Tests |
|---|---|---|---|---|---|
| **H-01** | AGC-DF-MEP-SD-PAS-02-A / 02-D / 03-D: `Drg. no.`, vector-drawn title block | **Partly closed** | 02-A and 02-D become records with REV `00` (the title-block strip is OCRed; the number is one clean token). 03-D becomes a record **without** a revision: OCR of its REV cell read nothing, and it is not guessed. | `title_block.py` (DRG label, `ocr_word_lines`, `read_page` OCR branch, `ocr_number`); `document_control._sheet_of` / `_title_block_ocr_lines`; page gate `own` | `test_m2_review06_titleblock.py` (8) |
| **H-02** | The company's MS cover sheets `EP-28605 /MA/FA/201`, Rev 00 | **Closed as raw evidence** | A `form_identity` observation on both CS.pdf files: identity `EP-28605 /MA/FA/201`, label, revision `00`, purpose "material submittal" read from the heading, and region. It is not made a register record: "/MA/" is not assumed to be one document type. | `labelled_fields.py`, `document_control.page_evidence` | `test_extraction_m2_review` (no stray observation), EVALUATOR test 12 |
| **H-03** | Client MTS forms (MTS-E-0018 R01 "B", R00 "C") and the Dar review form (Code 3): identities and decisions | **Open for decisions**; identities partly read | The Dar form gives `form_identity` `ICDS-DOC-01943`: the literal OCR text, whose leading "I" is probably noise; it is kept literal and unverified. The MTS package gives the reply page's reference `NG/LGC/C&M/07/2024/34-MTS-E-0018`; the form's own "MTS E 0018" is not read by OCR. **No decision is read deterministically.** These pages are exactly the AI evidence stage's `decision_block_unread` / `form_or_title_block_without_identity` triggers. The holdout projects have no recorded AI policy, so the real model was **not run on them** (REAL-MODEL-RESULTS). | as H-02; `evidence_reader.triggers` | `test_evidence_reader.py` (triggers) |
| **H-04** | As-built ELV sheets: own number read, REV missed (stacked cell) | **Closed** | CCTV-2001, CCTV-2002 and TL-2001 carry `title_block` observations with REV `00`. The stacked "REV / ORIGINAL SIZE" cell is handled, as is the nearest REV cell. They stay evidence only (no shop-drawing record), as the register rules exclude as-built sheets. | `title_block._cell_value` (sub-label rows), nearest-REV fallback | raw layer: holdout raw revision 0/13 → 7/13 |
| **H-05** | Transmittals of material submittals (2 scanned, 4 Word) | **Closed as raw evidence** | Every transmittal is an observation: its TR number, date, to/attn, subject, project id, listed items and receipt evidence. Results: TR/0897/17 (scanned and Word), TR/2001/17, TR/1785/24, TR/1733/24. The EP-28569 scanned Ack has its TR line unread (`reference_unread`) but its item is read. The sample-register behaviour is unchanged (`read_transmittal` records as before), and material transmittals are not filed as sample approvals. Gap: the EP-28605 scanned Ack gave no transmittal observation (its OCR has no transmittal heading). | `transmittals.observe`, `looks_like_transmittal_form`; `document_sync` Word branch | reviewer set (sample register) 339 passed |
| **H-06** | Holdout BOQ, EP-8430: printed 1 read as 4 (3 rows), printed 2 read as 9 | **Partly closed** | The "2 read as 9" row is now **held**: all three independent passes read 2 and the strip read "\| 9" at 74%. The three "1 read as 4" rows stay accepted: the strip read them at 91–95% with no second pass (above the recheck band), or with passes absent. Holdout critical 4 → 3. The remaining cases need an independent reader. EP-8430 has no recorded AI policy, so it was not sent to the model. | `design_sheet_extractor._check_cut_digit` + `HOLD_ON_PASS_DISAGREEMENT` | `test_m2_review06_boq.py` (3); `boqexp/holdoutB.json` |

## Defects found and fixed during this round

These are disclosed rather than hidden.

1. **The OCR title-block fallback created wrong register keys** (parser `.7`, pilot). On EP-29076, `XY) LAC-653-GEN-ZZZ-ELV-FA-211`, `Ox) LAC-653-PLN-L04-ELV-FA-111` and `XS) LAC-653-PLN-LO8-ELV-FA-115 C 1` became records: **3 new critical** under evaluator .4. The fix is `titleblock-3` / parse `.8`: an OCR number is a key only when it is one clean, unambiguous token, and otherwise it is kept as `number_literal` / `number_candidate` evidence. Pilot critical returned to 2 (the pre-existing pair). The `.7` runs are kept as `runs/det-*-parse7-superseded` evidence and are not overwritten.
2. **A snapshot of the EV0 sandbox database copied the file without its WAL.** The first EV1 start saw 6 of 8 usage rows. It was stopped before any evidence call. The runner now uses the SQLite backup API (WAL-consistent), and EV1 was restarted.
3. **A purpose-only `form_identity` observation** was emitted on a cover whose record moved to the consultant page (`test_extraction_m2_review`). `form_identity` now needs an identity.

## Open defects carried

These are not moved to M3.

- **D-R6-A.** Two flagged references are still used as register keys (Candidate C behaviour): `A23-EFECO-MAT-E` on A23 page 4, and `V-EL-MTG-PJW-ZZZ` / `R1029-…-MTG-PJW-ZZZ` on MTG-1020 page 1. Evaluator .4 counts them as critical. The fix needs a business decision: whether a reference flagged incomplete may key a register row. This is a blocker.
- **D-R6-B.** Decisions on client and consultant forms outside the grammar (H-03) are not read without the model.
- **D-R6-C.** BOQ: 4 pilot and 3 holdout confident misreads remain accepted deterministically (BOQ-RESULTS).
- **D-R6-D.** The per-task input-token cap is checked on the reservation estimate, not on the actual tokens. Discovery calls used 16–30k input tokens against a declared 6,000 (REAL-MODEL-RESULTS).
