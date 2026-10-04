# M2 real-project pilot -- acceptance candidate verdict

**Verdict: CHANGES REQUIRED.** Not self-approved; for the independent reviewer and the owner.

> **Correction of Review 05 (2026-09-28): CHANGES STILL REQUIRED.** Candidate C (parser `parse-2026-09-28.6`,
> `titleblock-1`, design-sheet extractor `2026-09-28.2`) removes every critical failure this pilot's corpus exposed
> (30 -> 0 per profile under the corrected evaluator `m2-pilot-eval-2026-09-28.3` and labels v2; BOQ 55 -> 5), but on
> four fresh, unseen projects it read no record at all (holdout defects H-01..H-06), recovery is below 90 % everywhere,
> the deterministic BOQ still accepts wrong quantities and confident misreads, and the real-model BOQ track is not
> exercised. The figures in sections 1-3 below are candidate A/B under the submitted scorer and stay as history; the
> corrected re-scores, the holdout and the reasons are in `review05/REVIEW-05-REPORT.md`. Section 5 is withdrawn as an
> M3 handoff: the extraction items in it are M2 work (see `DEFECTS.md`, Review 05).

Source identity: candidate A = commit `2221b4327c7dd140994cc2c98e89229431b34899` + the uncommitted R4-01
closure (parser `parse-2026-09-28.4`); candidate B = A + `document_control.py` fixes P-01..P-04 and
`tests/test_extraction_pilot.py` (parser `parse-2026-09-28.5`). Hashes of both in `RUN-MANIFEST.json`.
Live data and OneDrive originals unchanged; no live service touched.

## 1. Targets (fixed before scoring) and results (default profile, in-scope documents; all-sample figures in `ACCURACY-AND-COVERAGE.md`)

| target | candidate A (frozen; holdout scored once, before any fix) | candidate B (after P-01..P-04) | met |
|---|---|---|---|
| >= 98 % precision among auto-accepted critical fields | decision 100 % (73/73); reference 70.5 % (55/78); revision 65.8 % (48/73) | decision 100 % (72/72); reference 78.8 % (67/85); revision 64.6 % (51/79) | decision yes; reference and revision **no** |
| >= 90 % correct automatic recovery of clearly readable applicable critical fields | decision 66 %; reference 44 %; revision 42 % | decision 66 %; reference 54 %; revision 45 % | **no** |
| no unresolved critical false acceptance | 0 false consultant approvals; 25 wrong references and 26 wrong revisions accepted | 0 false approvals; 24 wrong references (incl. 1 near) and 30 wrong revisions accepted | approvals yes; references / revisions **no** |
| no evidence loss | legacy readings kept through failed, partial, removed, bounded and interrupted runs (scenarios); repaired rows keep old records in the repair manifest | same | yes |
| no cross-profile / cross-parser reuse | every row stamped; mixed readings never current; R4 probes pass; promoted run re-read everything | same | yes |
| no engineer-override regression | 7 engineer-origin BOQ rows on the clone unchanged in every column; no confirmed drawings existed to test | same | yes, within what the clone held |

~~The regression controls (EP-30784, EP-30088) meet the precision target for reference (30/32 and 33/35 ...)~~
**Corrected (Review 05):** they do **not** meet it for reference: 30/32 is 93.8 % and 33/35 is 94.3 %, below 98 %
(the misses were the reply-sheet class P-08 and one near miss). Revision (29/29) and decision (41/41) did. Under the
corrected evaluator the regression cohort's reference result for candidate B default is in
`review05/eval/candidateB-default-v3.json` (`by.cohort`).

## 2. Holdout exposure

The holdout (EP-27474, EP-26369, EP-13777, EP-14119; 108 documents) was scored once on candidate A before any
fix. Fixes P-01..P-04 were chosen from regression / exploration failures only (EP-29076, EP-19977); the class
P-04 also occurs on EP-13777, which was not used to choose it. Candidate B was then scored on the holdout with
unchanged labels. Both results are retained (`outputs/candidateA`, `outputs/candidateB`). Because the holdout's
failures have now been seen (P-06, P-07 on EP-26369), any further fix aimed at those classes needs a fresh
holdout for a new claim; these four folders are exposed for that purpose.

## 3. Owner table -- project by project (candidate B, default profile; renders under `crops/`)

| project (cohort) | documents (in scope) | outcomes | reference correct / accepted (abstained) | revision | decision | failures (kind: documents; render) |
|---|---|---|---|---|---|---|
| EP-30784 Granada Europe (regression) | 40 (29) | 35 complete, 5 bounded | 19 / 21 (16) | 18 / 18 (13) | 23 / 23 (0) | wrong reference 2: the two `Reply to MS Consultant Comments 31 (1)/(3).pdf` reply sheets (P-08; `crops/sheet-007.jpg`) |
| EP-30088 Samana (regression) | 40 (25) | 33 complete, 7 bounded | 11 / 11 (23) | 11 / 11 (15) | 19 / 19 (4) | none. Two York covers held as candidates under the default profile (`crops/sheet-014.jpg`, `sheet-015.jpg`) are accepted correctly by the promoted profile |
| EP-29076 Al Arabia EMW (exploration) | 55 (24) | 51 complete, 4 bounded | 12 / 16 (27) | 11 / 14 (27) | 9 / 9 (8) | wrong reference 4 (`...-FA-003-R03 - Code B` attachment number taken as the cover's; `...-EM-23-02` cut; a scanned transmittal item P-09; OCR `030`->`30` P-11), wrong revision 3 (`sheet-021`..`sheet-030.jpg`, `tb-009`..`tb-016.jpg`). Decisions: the handwritten circles on the LACASA forms are not read (8 abstentions, `sheet-022`, `sheet-023`, `sheet-030.jpg`) |
| EP-25091 BK Gulf (exploration) | 50 (19) | 47 complete, 3 bounded | 6 / 13 (29) | 1 / 13 (27) | 12 / 12 (9) | wrong revision 12 and wrong reference 6 on the BK Gulf sheets with revision and reference tables (P-06, P-07; `tb-021`..`tb-024.jpg`); one Dutco cover with an engineer's signature and no status box (`sheet-039.jpg`) |
| EP-19977 Voltas (exploration) | 32 (11) | 31 complete, 1 bounded | 3 / 5 (14) | 2 / 5 (7) | 0 / 0 (7) | wrong reference 2 (a quotation quoting the submittal number; one medium-confidence label), wrong revision 3 (Emaar forms print `Rev.No. 01` under a `00` label row); the Emaar ticked boxes (B / C) are not read: 7 abstentions (`sheet-061`..`sheet-064.jpg`) |
| EP-26082 China State (exploration) | 55 (8) | 47 complete, 7 bounded, 1 failed (0-byte original) | 5 / 9 (33) | 3 / 9 (32) | 3 / 3 (3) | wrong revision 6 and wrong reference 4 on CSCEC / CKR / Kling sheets (P-06, P-07; `tb-038`..`tb-044.jpg`) |
| EP-27474 Alemco (holdout) | 2 (0) | 2 complete | 0 / 0 (2) | 0 / 0 (2) | -- | none (a DRF and a Design Sheet; nothing to register) |
| EP-26369 NAFFCO (holdout) | 60 (14) | 56 complete, 4 bounded | 12 / 16 (39) | 9 / 15 (38) | 10 / 10 (3) | wrong revision 6 and wrong reference 4 on the JAM shop drawings and one SA-H2 IFC sheet (P-06, P-07; `tb-032`..`tb-034.jpg`); the RAQ Code C forms and the Vortex "APPROVED BY" stamp are correct / owner policy (`sheet-057.jpg`, `sheet-058.jpg`) |
| EP-13777 EMT (holdout) | 40 (7) | 35 complete, 5 bounded | 1 / 2 (19) | 1 / 1 (13) | 4 / 4 (8) | wrong reference 1 (a Khatib & Alami form after P-04); the Emaar / K&A document-submittal ticks are read on 4 forms and abstained on 8 (`sheet-074`..`sheet-077.jpg`) |
| EP-14119 Aikah (holdout) | 6 (0) | 6 complete | 0 / 0 (5) | 0 / 0 (4) | -- | none (commercial and internal forms) |

Random correct controls with renders: the last table of `ACCURACY-AND-COVERAGE.md`.

## 4. Sample limits and untested branches

- 380 documents (376 distinct) drawn from 24,358 eligible files in ten folders; 137 in the reader's scope. Not
  a validation of any project; the 1,028 archive folders are untouched by this claim.
- The design-sheet / BOQ reader was not exercised (model disabled): 15 sheets, 778 rows labelled, no reading
  scored. The BOQ path was driven with the model off and behaved honestly (no lines, warnings stored).
- Labels are Claude's transcriptions from renders; no engineer countersigned them. Four are low confidence
  (rotated scans), 24 medium; one 0-byte original is unreadable.
- Real OneDrive unavailability mid-read, `.docx` transmittals and the three-worker live setting were not driven.
- The persistence scenarios ran on four real documents; the clone workflow repaired the 80 sampled rows of the
  regression controls, not their 884 readings (no bulk download).

## 5. ~~Proposed M3 handoff (not started)~~ -- withdrawn (Review 05)

Review 05: raw extraction defects are M2 work and are not handed to M3. Items 1, 3 and the raw-floor part of 4 are
corrected in candidate C (`review05/REVIEW-05-REPORT.md` section 3); item 2 (unread decision marks) and the holdout
defects H-01..H-06 are open **M2** defects (`DEFECTS.md`); only floor creation, aliases and elevations (G-01) remain
M4, and the owner policies in item 5 stay with the owner. Item 6 (a model-enabled BOQ run) is M2 evidence still
missing. The original list is kept below as history.


1. Title-block rules for the drawing-sheet families the pilot met (P-06, P-07): the sheet's own number and
   current revision come from the title block's DRAWING NO / REV cells; reference-drawings and shop-drawings
   tables are excluded; sheet-index suffixes (`-01` after the serial) are not revisions.
2. Decision marks the reader does not yet read: handwritten circles on LACASA forms, the Emaar / K&A ticked
   boxes, Dutco X marks -- with the same candidate / conflict discipline as the stamps and frames.
3. Reply-sheet and transmittal identity (P-08, P-09, P-10).
4. Floor-name rule for titles like `HC FLOOR FIRE ALARM LAYOUT` (P-05) under the G-01 gate (M4).
5. Owner policies recorded in `DEFECTS.md` P-obs-3 / P-obs-4 (printed EP differing from the folder; a comment
   with a signature but no code; a specialist consultancy's approval stamp).
6. A model-enabled BOQ run over the 15 labelled sheets before any BOQ claim.
