# Defects found by the real-project pilot

Numbering: P-nn are pilot findings. "Fixed" means fixed in candidate B with a bounded regression test in
`backend/tests/test_extraction_pilot.py` whose snippets quote the pilot document that showed the defect; the
fix is a candidate for the independent reviewer, not an accepted change. Everything else was listed as open for
the M3 handoff -- **withdrawn by Review 05: raw extraction defects are M2 work** (see the Review 05 section at the end). Cohort names which cohort demonstrated it; a holdout project is named only where the same
class also appeared in the regression or exploration cohorts (the holdout did not drive any fix).

## Fixed in candidate B (parser `parse-2026-09-28.5`)

| id | demonstrated by | what happened | root cause | fix | test |
|---|---|---|---|---|---|
| P-01 | EP-29076 (exploration), 4 scanned LACASA submittal forms, e.g. `.../25H-S202-NCC-SD-MEP-ELE-FA-050-00.pdf` | reference accepted as `Reference25H-S202-NCC-SD-MEP-ELE-FA-050-00` | OCR runs the field label into the number; the reference grammar's leading `[A-Z0-9]+` token took the label | `reference_candidates` strips a leading `Reference` / `Ref.` / `No.` label glued to a token that holds a digit (`_GLUED_LABEL`); the candidate's offset moves to the number so label searches behind it still work | `test_p01_...` |
| P-02 | EP-19977 (exploration), Emaar approval-form register prints `EP-19977 FA MS R1 App.pdf`, `EP-19977 FA MS R0 R&R.pdf` | reference accepted as the bare word `Reference` | an empty `Drawing No:` field followed by the `Reference No:` label: `DRAW_REF` captured the next label as the number | `drawing_number()` returns the first drawing-number field whose value holds a digit and is not a field label | `test_p02_...` |
| P-03 | EP-29076 (exploration), scanned forms `...-FA-024-R00 - Code C.pdf`, `...-EM-030-R00 - Code B.pdf` | reference `...-FA-024-RO` (suffix kept), revision R0 by default rather than from the suffix | OCR reads the zero of `-R00` as the letter O; the `-R\d+` suffix rule then does not see a revision | a trailing `-R` suffix made only of O/0 and digits is normalised (O -> 0) before the suffix is read (`_OCR_REVISION_SUFFIX`); real trailing segments are untouched | `test_p03_...` |
| P-04 | EP-19977 (exploration): `EBF-DCP-6374-VL-MAT-ELV-0003`; the same numbering in EP-13777 (holdout: `A23-EFE-MAT-E-00033`) | no reference candidate on the Emaar / Voltas forms, hence P-02 | `-MAT-` (material submittal) is not one of the reference codes; the code may also follow a wrapped hyphen (`...-VL-` / `MAT-ELV-0003`) | `MAT` added to `_CODES` as a submittal code; `REF` allows a line break after the hyphen in front of the code | `test_p04_...`, `test_p02_...` |

Candidate B's effect on the scores is in `ACCURACY-AND-COVERAGE.md` (candidate A vs B, same labels).

## Open (not fixed in this pilot)

| id | demonstrated by | what happens | evidence | disposition |
|---|---|---|---|---|
| P-05 reconciliation floors | EP-30088 (regression clone, `outputs/clone_default/`) | drawing titles `HC FLOOR FIRE ALARM LAYOUT`, `FIRST FLOOR FIRE ALARM LAYOUT` produce floors `HC FIRE ALARM` / `FIRST FIRE ALARM` (elevation 99999) in `project_building_floors` and the drawings are filed under them | `records_after.json`, `snapshot_after_p4.json`, floor rows 79-80 | ~~M3~~ Review 05: the raw floor is M2 and is corrected in candidate C (`FIRST FLOOR`, `HC FLOOR` kept raw); floor creation, aliases and elevation stay M4 (G-01) |
| P-06 revision from the wrong row | EP-25091 (exploration: 12 of 13 BK Gulf sheets), EP-26082 (exploration: CSCEC / CKR sheets), the same class on EP-26369 JAM sheets (holdout) | revision accepted as the first row of the revision table (`R0`, or `R1` from the "01" sheet-index suffix) while the title block's REV cell prints 01/02/07; on JAM-SD-FA-002 `R10` from "10.09.24" | `per-document-*.json`, `wrong revision` rows; renders linked in `ACCURACY-AND-COVERAGE.md` | open: a title-block rule (the REV cell, or the last row of the revision table) per layout family; the largest single cause of wrong critical accepts |
| P-07 neighbour number from a reference table | EP-25091 (BK Gulf: `...-PAVA-00010` read as `...-00008`, `UR-` read as `LR-`), EP-26082 (Kling / CSCEC: `L01-FAS-1231` -> `1233`, `L01-FAS-1201` -> `L02-FAS-1202`, `P&B-GFL-EML-1220-01` -> `MGM1-L01-EML-1201`), EP-26369 SA-H2 sheets (holdout) | the drawing's own number is read from the reference-drawings / shop-drawings table printed on the sheet rather than from its title block | same files | open: the sheet's own number is the one in the title block's DRAWING NO cell; the reference tables must be excluded or ranked below it |
| P-08 reply sheet reference | EP-30784 (regression): `Reply to MS Consultant Comments 31 (1)/(3).pdf` | the reply's reference is taken from a drawing quoted in the comments (`...-ZZZ-ZZZ-010034`) rather than the submission it answers (`...-POD-P01-010029` / `P03-010031`) | `per-document-*.json` | open: reply sheets carry the answered reference in their header row; the comment body quotes others |
| P-09 transmittal item number as the transmittal's reference | EP-29076: `EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf` (a scanned transmittal) | promoted/default read `25H-S202-NCC-MAS-MEP` (an item's number, cut) instead of `TR/0127/26` | same | open: the transmittal reader's TR/ number should win on a scanned transmittal too (the Word path reads it) |
| P-10 sample-tag / submittal cover cut | EP-26082: `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf` | reference `1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-Rev` (leading R dropped, `ZZZ-` continued onto `Rev`) | same | open: the wrapped-segment rule joins `-` + `Rev`; the OCR dropped the leading character |
| P-11 OCR digit loss | EP-29076 `...-EM-030-R00`: read `EM-30` | a zero dropped by OCR inside the serial | same | open (OCR quality; the cue-band render shows `030`) |
| P-obs-1 duplicate-content KeyError | found while closing R4-01 (unit test) | `document_processing` raised `KeyError: 'unchanged'` on a duplicate-content result | fixed in candidate A (`result.get("unchanged")`), covered by the R4 test | fixed before the freeze; recorded here for completeness |
| P-obs-2 telemetry label | scenarios 12 / 13b | a bounded reading with carried records is counted `partial` by the processing job's telemetry while the row's attempt is not partial | `SCENARIOS2-*.json` | open, cosmetic: the count should say `bounded` |
| P-obs-3 printed EP differs from the folder | EP-30088 (`EP-30058` on the Al Arabia quotation, warranty and transmittals), EP-30784 (`EP-30627` on a cable submittal), EP-29076 (`EP-29676` typo), EP-13777 (`DIFC ICD` VESDA schedule), EP-30784 (`BUGATTI RESIDENCE` specs), EP-30088 (`SAMANA IVY GARDENS 2` PQ) | documents print another job's number or name | `GOLDEN-LABELS.json` `printed_project`; `printed EP differs` rows in the critical list | not a reader defect: filing follows the folder; flagged for the M3 register as a cross-project context warning |
| P-obs-4 decisions without a code | EP-25091 Dutco form `...-000285-R2` (engineer signed with a comment, no status box), EP-29076 sheets with review mark-ups and an unmarked A-D box, EP-26369 `RDJ183 FA Stamped.pdf` (a fire-safety consultancy "APPROVED BY" box, no A-D code) | the reader keeps UR, which the labels agree with; whether a comment-with-signature or a specialist consultancy's approval is a decision is an owner policy | labels (`decision_candidates`) | owner decision, not a reader defect |

## Not exercised

- The design-sheet / BOQ reader (model-only path): 15 sheets, 778 labelled rows, no scored reading.
- Real OneDrive unavailability during a read (a file made online-only mid-run): only the removed-file and
  corrupt-file paths were driven; the reader's `unavailable` outcome was not reproduced on a real placeholder.
- `.docx` transmittals (the sample held `.doc` only).

## Review 05 (candidate C: parser `parse-2026-09-28.6`, `titleblock-1`, extractor `2026-09-28.2`) -- all M2

Evidence and figures: `review05/REVIEW-05-REPORT.md`. "Corrected" = fixed in candidate C with a regression test;
not an accepted change.

| id | class | status in candidate C | test / evidence |
|---|---|---|---|
| P-05 | raw floor from titles | corrected (raw floor as printed; no expansion) | `test_m2_review05.py::test_the_raw_floor_is_the_floor_the_title_prints_and_nothing_is_expanded` |
| P-06 | revision from the wrong row | corrected: the title block's REV cell by position; a sheet whose REV cell and history disagree is flagged `revision_conflict` | `test_jam_sd_fa_002…`, `test_a_sheet_whose_rev_cell…`, `test_letters_are_a_revision_as_printed…` |
| P-07 | neighbour / table number | corrected: own number cell; reference tables, callouts, split runs and a second numbering scheme excluded | `test_pava_00010…`, `test_a_table_column_is_not_a_cell…`, `test_two_numbering_schemes…`, `test_a_callout_to_another_sheet…`, originals test |
| P-08 | reply sheet quotes another drawing | corrected: the header's own label wins; "Refer to" is a cross-reference | `test_a_reply_is_the_reply_to_the_submission_its_header_names…` |
| P-09 | scanned transmittal item as its number | corrected: no record from items; an unread TR number stays unread (`reference_unread`, literal raw token) | `test_a_scanned_transmittal_is_not_its_first_items_number…` |
| P-10 | wrapped join onto "Rev", split start | corrected: no join onto field labels; split start `reference_uncertain` (held); MTG sample-tag code | `test_a_wrapped_number_is_not_joined…`, `test_a_material_sample_tag…` |
| P-11 | "OCR digit loss" EM-030 | reclassified: a v1 label error (the cover prints EM-30); the reader reads as printed | `test_a_printed_number_is_read_as_printed…`; `review05/crops/em030.png` |
| P-12 | footer form number / subject line / citation / fax cover as a record | corrected | `test_a_subject_line_a_citation_and_a_form_template_number…`, `test_a_fax_cover…` |
| P-13 | form edition / table header read as the revision | corrected (`page_revision`) | `test_a_forms_own_edition_and_a_tables_header…` |
| P-14 | scanned cover whose reference line OCR lost | corrected: listed attachments are not the cover; one bounded header-band re-read | `test_a_listed_attachment_is_not_the_cover…` |
| B-01 | BOQ: correlated OCR counted as confirmation (KCW019ML-IP65) | corrected: held with the literal readings, quantity and crop | `test_m2_review05_boq.py` |
| B-02 | BOQ: item-number column read as quantities; crossed columns | corrected: held for review, nothing dropped | idem |
| B-03 | BOQ read with the model off stamped as extracted; all-failed re-read "succeeded"; unread sheets' lines offered as removals | corrected within the existing contract | idem (contract tests), `review05/boq/integration-candidateC-BOQ-RUN-default.json` |
| B-04 | BOQ: confident strip misreads (SIGA-AASO, PT-1S, 4-FWALA, SIGA-IB 75->15) | **open** (5 critical on the pilot sheets) | `review05/boq/after2.json` |
| H-01 | Nakheel/Dar title block ("Drg. no.", "DWG. TITLE") not read | **open** (holdout) | `review05/holdout/` |
| H-02 | company MS cover numbers (`/MA/`) outside the grammar | **open** (holdout) | idem |
| H-03 | client MTS submittal forms and review forms (decisions B / C / Code 3) not read | **open** (holdout) | idem |
| H-04 | as-built ELV REV cell (stacked cell) not read | **open** (holdout) | idem |
| H-05 | transmittals of material submittals leave no trace (a correct TR number discarded) | **open** (holdout) | idem |
| H-06 | holdout BOQ: wrong quantities accepted (4 critical) | **open** (holdout) | `review05/holdout/boq-holdout.json` |
| P-obs-5 | P-04 `.docx` gap | the pilot held `.doc` only; the holdout's two `.docx` transmittals are material transmittals (H-05) | — |
