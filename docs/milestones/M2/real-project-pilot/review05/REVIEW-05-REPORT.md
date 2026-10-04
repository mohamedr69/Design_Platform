# M2 Review 05 — real-project extraction and evaluation (correction report)

Date: 2026-09-28 (local). Scope: the four findings of Independent M2 Review 05 (R5-01 … R5-04) and the revalidation (D).
Nothing here approves M2 or starts M3. No live data, production endpoint, service, model or M3/M4 code was touched; the
live database and `backend/library/symbols/symbol_library.json` are not part of this correction (section 8).

Verdict of this correction: **CHANGES STILL REQUIRED** (section 7).

Candidate names used below: **A** = parser `parse-2026-09-28.4` (pilot, before its fixes), **B** = `parse-2026-09-28.5`
(pilot, submitted to Review 05), **C** = `parse-2026-09-28.6` + `titleblock-1` + design-sheet extractor `2026-09-28.2`
(this correction; frozen in `CANDIDATE-C-FREEZE.json`). **C0** and **C1** are intermediate runs of C made while it was
being corrected; they are kept, not replaced (`outputs/candidateC-intermediate/`).

## 1. Units and corpus (reconciliation)

| unit | count | where |
|---|---|---|
| frozen pilot documents (sha256-frozen, staged read-only copies) | 380 (370 PDF, 10 Word `.doc`, 0 `.docx`) | `../FROZEN-SAMPLE.json` |
| frozen BOQ Design Sheets | 15 (8 of them also in the 380) | `../FROZEN-BOQ-SET.json` |
| files staged and read by every run | 387 = 380 + 7 BOQ-only sheets | `common_corpus.json` |
| candidate A default | 385 (the two BOQ-only sheets EP-26369 `MS FAS\BOQ.pdf` and `EP-26369 Design.pdf` were staged after that run; they carry no document labels, so no score changes) | idem |
| rows whose stored `read_sha256` / `sha256` differ from the frozen hash | 0 in all six runs (A, B, C × default, promoted) | idem |
| page-labelled documents (truth v2) | 25 documents, 78 page records, 54 no-record pages, 24 unvalidated pages | `labels/GOLDEN-LABELS-v2-PAGES.json` |
| other documents | truth v1 (page 1) | `../GOLDEN-LABELS.json` (unchanged, kept) |
| BOQ rows labelled | 778 = 439 line + 269 component (**708 equipment rows**) + 65 heading + 5 component-or-heading (unscorable) | `../GOLDEN-LABELS.json` `boq_design_sheets` |

A *record* is one register record a page yields; scores are per record field. A document is not a record and a page is
not a document: every table below says which unit it counts.

## 2. R5-02 / R5-03 — the evaluator (A)

The submitted scorer (`../outputs/scripts/score.py`, pilot) and its outputs are kept as history. The corrected
evaluator is `backend/scripts/m2_pilot_eval.py` (`m2-pilot-eval-2026-09-28.3`; .2 was the first correction, .3 adds that
a reference the reader itself marks `reference_incomplete` / `reference_uncertain` is *held*, and that a sheet labelled as
contradicting itself is scored on whether the reader said so). Adversarial tests: `backend/tests/test_m2_pilot_eval.py`
(10), all of the cases the review named:

- a known absence is a negative control that can fail (n/a + an approval = false positive; absent reference + an
  invented one = false positive);
- unknown / illegible / ambiguous / unlabelled truth is **unscorable**, never counted with absences;
- separate denominators: precision of what was *accepted*, recovery of what was *readable*, specificity of *negatives*,
  abstention, held evidence;
- a conflict counts only with its evidence (flag or candidates), not a default UR;
- held evidence is recovery of evidence, never an accepted approval;
- record-set matching by page and identity (matched / substituted / missing / extra / duplicate); every emitted record
  is scored, a later correct record does not hide an earlier wrong one; a default-sourced revision is a projection, not
  a raw misread;
- pages without truth are **unvalidated** and reported (C: 4 records);
- Word transmittals are scored;
- system equivalence is a table (`SYSTEM_EQUIVALENCE`), not a substring (`non-FAS` is not FAS); production rules are not
  altered;
- revisions compare as printed (numbers by value, letters as written; a reference's `-R3` suffix counts).

Raw extraction, register eligibility and business projection are kept apart: `register: false` truth (untracked
discipline, evidence-only component) is scored as *unregistered* with a raw-evidence check, a default revision as a
projection, and the default-profile withholding of a correct candidate as held, not a misread.

**Golden truth corrections are versioned** (`labels/GOLDEN-LABELS-v2-PAGES.json`, `page1_corrections`, each with the
old value, the new one and its evidence; v1 unchanged):

| document | field | v1 | v2 | evidence |
|---|---|---|---|---|
| EP-19977 CBS MS R1 R&R | reference | …MAT-ELV-0023 | …MAT-ELE-0023 | pages 1-2 print ELE |
| A23-EFE-MAT-E-00033 | decision | unknown | ANN | page 2 (B) ticked |
| AAR-001 Commented MS | decision | unknown | ANN (package, page 3) | page 3 |
| AKA-DCC-…-000285-R2 | decision | UR | ambiguous | red-outlined box |
| BBY006 …L58-010042 (R01) | revision | 01 | 00 (REV. NO. cell); history's latest row 01 | `crops/l58_r01.png`; the sheet contradicts itself |
| idem | revision_conflict / date | — / 21.08.2026 | true / 06.08.2026 | idem |
| 25H-…-EM-030-R00 | reference | …EM-030-R0 | …EM-30-R0 | `crops/em030.png`: the cover prints 30; v1 copied the file name |
| 25H-…-EM-23-02 | reference, revision | …EM-23-02, 02 | …EM-23-R2, R2 | `crops/ncc_refs.png` |

BOQ label corrections (`labels/BOQ-LABEL-CORRECTIONS-v2.json`): the "Graphic Command Centre" row on EP-26082 FAS,
EP-29076 FAS and EP-30088 FAS prints a quantity (6 / 1 / 1) with its components under it — a package line, not a
heading (`crops/gcc.png`).

**The "30/32 or 33/35 meets 98 %" assertion was wrong**: 30/32 is 93.8 % and 33/35 is 94.3 %, below the 98 % target.
Corrected in `../ACCEPTANCE.md`. Targets and critical gates are unchanged (>= 98 % precision among accepted critical
fields; >= 90 % recovery of readable critical fields; zero unresolved critical false acceptance).

### Re-scored stored candidates (frozen pilot corpus, labels v2, evaluator .3)

| run | critical | reference: correct/accepted; recovered/readable; negatives kept | printed revision | decision | records matched / substituted / missing / extra |
|---|---|---|---|---|---|
| A default | 31 | 94/117; 94/156; 67/67 | 57/65; 57/142; 13/13 | 25/25; 25/70; 144/144 | 94 / 25 / 37 / 0 |
| A promoted | 31 | 101/124; 101/158; 67/67 | 61/69; 61/141; 16/16 | 28/28; 28/72; 144/144 | 101 / 25 / 32 / 0 |
| B default | 30 | 114/134; 114/160; 67/69 | 68/78; 68/144; 14/14 | 25/25; 25/71; 149/149 | 114 / 21 / 25 / 2 |
| B promoted | 30 | 121/141; 121/162; 67/69 | 72/82; 72/143; 17/17 | 28/28; 28/73; 149/149 | 121 / 21 / 20 / 2 |
| C0 default (intermediate) | 9 | 125/130; 125/162; 67/69 | 97/101; 97/147; 13/13 | 26/26; 26/71; 151/151 | 125 / 5 / 32 / 2 |
| C1 default (intermediate) | 1 | 135/136; 135/164; 67/67 | 103/103; 103/149; 13/13 | 26/26; 26/71; 151/151 | 135 / 3 / 26 / 0 |
| **C default** | **0** | 137/137; 137/164; 67/67 | 104/104; 104/149; 13/13 | 26/26; 26/71; 151/151 | 137 / 2 / 25 / 0 |
| **C promoted** | **0** | 144/144; 144/166; 67/67 | 108/108; 108/148; 16/16 | 29/29; 29/73; 151/151 | 144 / 2 / 20 / 0 |

These are **exposure numbers, not unseen results**: C was corrected on this corpus (all three pilot cohorts, including
the pilot's own "holdout" cohort, were looked at while fixing). Precision is at target on it; **recovery is not**:
reference 83.5 % / 86.7 %, printed revision 69.8 % / 73.0 %, decision 36.6 % / 39.7 % (default / promoted), all below
90 %. Grouped by project, format, cohort and label confidence: `eval/*.json` (`by`), tables for C default below.

| format (C default) | docs | reference | printed revision | decision |
|---|---|---|---|---|
| scan | 67 | 23/23 accepted, 23/32 readable | 7/7, 7/31 | 0/0, 0/14 |
| text | 303 | 105/105, 105/122 (2 held) | 97/97, 97/117 | 26/26, 26/57 (2 held) |
| word (.doc) | 10 | 9/9, 9/10 | 0/0, 0/1 | 0/0, 0/0 |

| cohort (C default) | docs | reference | printed revision | decision |
|---|---|---|---|---|
| regression | 80 | 46/46, 46/52 | 40/40, 40/46 | 25/25, 25/33 (2 held) |
| exploration | 192 | 61/61, 61/75 (1 held) | 38/38, 38/68 | 1/1, 1/30 |
| pilot "holdout" (exposed) | 108 | 30/30, 30/37 (1 held) | 26/26, 26/35 | 0/0, 0/8 |

| label confidence (C default) | docs | reference | printed revision | decision |
|---|---|---|---|---|
| high | 351 | 131/131, 131/154 | 98/98, 98/140 | 26/26, 26/69 |
| medium | 24 | 4/4, 4/7 | 4/4, 4/7 | 0/0, 0/2 |
| low | 4 | 2/2, 2/3 | 2/2, 2/2 | — |

Word: the pilot corpus has 10 `.doc` transmittals and **no `.docx`**; the holdout adds two `.docx` transmittals (section 6).

## 3. R5-01 — raw extraction (B)

Source-backed cases first (`backend/tests/test_m2_review05.py`, 22 tests; the two independently checked originals are
also read directly when their staged copies are present, with their sha256 checked).

| case | before | now | how |
|---|---|---|---|
| AKA-BKG-ELE-B1-SD-PAVA-00010 (fa9fede5…) | reference …-00008 (the match-line callout "REFER TO DWG No."), revision R0 | …-00010, printed REV 02 → R2 (printed) | title block read by position (`app/services/title_block.py`): the own number is the one-value cell under "Drawing No." nearest the sheet's title-block corner, the REV cell on its row; the reference-drawings table (under its heading, or a column of several values) and the revision history are separate facts (stored as a `title_block` observation) |
| JAM-SD-FA-002 (a6624709…) | R10 from the date 10.09.2024 under the "Rev." label | printed 07 → R7 | REV cell by position; text reader: a number followed by `.dd` is a date, not a revision |
| BK Gulf 00051/00054/00055/00026, SA-H2 00201/00102c/ICT-00100a, Kling/IBA 1231, CSCEC 1201/1208/1199/1220-01, JAM-001 | neighbour / table numbers, first table row revisions | own number and REV cell (17 of 17 source sheets) | idem; rotated sheets read in display coordinates |
| two numbering schemes (IBA CLIENT vs MUNICIPALITY DRAWING No.) | municipality number | the controlled-grammar number; neither → no number | `controlled=` rule, no first/last/highest heuristic |
| a callout "DWG No. X" on the plan (SA-H2 ICT) | FA-00104 | not a cell (label and number in one run) | inline cells count only where the sheet has no true cell |
| numbers split into runs ("R1029- -BSB-DWG- ARC-") | — | refused (incomplete) | `_incomplete` |
| alpha / mixed revisions ("AB") | R1 from a table | printed "AB", flag `printed_revision_unmapped`, no R-number made of it | — |
| BBY006 L58 R01: REV. NO. 00 vs history row 01 | 00 accepted as the revision | printed 00, flag `revision_conflict`, projection from the folder (R1) | history's latest dated row compared with the REV cell |
| P-08 reply (EP-30784 "Reply to MS Consultant Comments 31") | quoted …-010034 | header "Ref No : …-010029" | labelled candidate first; "Refer to …" is a cross-reference; a reply with only quoted numbers names nothing |
| P-09 scanned transmittal (EP-29076, TR read "18/0127/26"; re-reads gave 7R, 1R, TR) | an item's number, cut | no record from items; transmittal kept as an observation with `reference_unread` and the literal raw token | re-reads disagree on the prefix, so none is taken |
| P-10 (MTG-1020 page 1: "R 1029-…-ZZZ-\nRev.01") | "1029-…-MAR-…-ZZZ-Rev" | the wrapped segment never joins a field label; a split start is `reference_uncertain` (held) | — |
| P-10 page 6 (MTG tag form) | footer form number R1029-CSCEC-FM-MAR-001, then the related MAR number | MTG-1020 (MTG = CSCEC material sample tag, category samples) | footer template numbers (`_R01` / "Version Date") and subject-line / "(Ref: …)" citations are never identity |
| P-11 (EM-030) | "OCR digit loss" | **label error**: the cover prints EM-30 (crop); v2 correction; the reader reads as printed and never from the file name | — |
| NCC scanned covers FA-003, EM-23 (OCR lost the "Reference:" line) | the attachment table's number | a listed attachment is not the cover; one bounded re-read of the header band (same scale, cached) recovers the line | `ocr_retry` observation records it |
| form editions (Emaar "Form No.: F-013 / Rev.0", LACASA "(Rev.02)") and table headers ("DRAWING No. / DOCUMENTS No. Rev") | R0 / R2 / R1 accepted | not a revision | `page_revision()` |
| covering sheets (EFECO fax), comment sheets (A23 p3), quotations (Voltas) | records of the quoted submittal | none | fax heading, subject line, parenthetical citation |
| P-05 raw floor | "FIRST FLOOR FIRE ALARM LAYOUT" kept whole (→ "FIRST FIRE ALARM" downstream) | "FIRST FLOOR"; "HC FLOOR" kept raw; a floor-only line still whole | no expansion, alias or elevation (M4) |

The four pilot fixes (P-01…P-04) stay in force (`test_extraction_pilot.py`, 5 tests) and the eight review-04 probes are
unchanged. Unrecognised consultant marks: the pilot's mark reader is unchanged; the holdout adds a real negative control
(a tick printed on the National Guard form template in the A box on both a C and a B decision) — not exercised because
the MTS form is outside the reference grammar (section 6).

Parser identity: `PARSER_VERSION parse-2026-09-28.6` (a stored reading of .5 is re-read by processing, as before);
`title_block.TITLE_BLOCK_VERSION titleblock-1`; the band re-read is page-cache variant `band-1`. Persistence: normal
processing and the repair tool both store the title-block reading, flags and observation
(`test_the_title_block_reading_is_stored_by_processing_and_by_the_repair_tool`).

Corpus effect of the title-block reader alone (216 drawing-sized pages of the frozen corpus): 109 own numbers and 126
REV cells agreed with the labels before the last two rules; the 6 wrong cells (split runs, municipality numbers) are what
those rules removed (`scripts/tb_corpus.py`).

## 4. R5-04 — BOQ (C): three separate reports

### 4a. Deterministic OCR accuracy (`app.services.design_sheet_extractor.extract_design_sheet`, AI_ENABLED=false, 15 frozen sheets)

`backend/scripts/m2_boq_eval.py` (`m2-boq-eval-2026-09-28.2`): rows aligned in page order, equipment rows scored,
headings apart, review rows *held*. Before = extractor `2026-09-28.1`, after = `2026-09-28.2`, both on labels v2.

| | accepted rows | held rows | part no. correct / accepted | quantity | description | critical |
|---|---|---|---|---|---|---|
| before | 403 | 44 | 374/386 (96.9 %) | 373/403 (92.6 %) | 384/403 | **55** |
| after | 311 | 136 | 288/292 (98.6 %) | 310/311 (99.7 %) | 293/311 (94.2 %) | **5** |

Recovery of equipment rows fell (part number 55.5 % → 42.7 % of readable): rows the reader cannot stand behind are now
review rows with their readings, quantity and crop, not lines. Per sheet: `boq/after2.json`.

Changes: (1) **correlated OCR is not corroboration** — a strip read under 90 % that both passes on the same pixels repeat
is held (`catalog_check.agreement = "correlated"`); on this corpus 8 of 64 such "confirmed" reads were wrong
(KCW019ML-IP65 read KCWO019ML-IP65 at 51 % by the strip and both passes, EP-19977; G1ARN→GIARN; CTR160→CTRI60;
SIGA-OSHD-FCN→…FC). Nothing is substituted (no O/0, I/1 rule), the literal reading stays. (2) a quantity column that
counts 1, 2, 3 … down ≥ 5 rows is the item-number column, and every row of that column layout is held (EP-26369 MS FAS
BOQ: 29 wrong quantities before); (3) a table whose descriptions are mostly numbers has crossed columns and is held
(EP-26082 aspiration: 10). Tests: `backend/tests/test_m2_review05_boq.py` (clear confident cells unchanged; noisy
repeated wrong reads held; split multiline identity held; duplicate parts with different quantities stay two lines; real
repeating quantities untouched; nothing dropped). Two review-03 tests that encoded the old rule were updated with the
reason (`test_design_sheet_extractor.py`).

**Still open (critical, 5)**: confident strip misreads at 91 % that no check is asked about — SIGA-AA50→SIGA-AASO
(EP-14119), PT-1S+→PT-1S (EP-26082, EP-30088), 4-FWAL4→4-FWALA (EP-30088), and SIGA-IB 75→15 (EP-30088). The
deterministic path has no independent evidence for these; they are not fixed.

### 4b. The application's model-disabled integration behaviour

The production BOQ read is the model's (`app.ai.sheet_reader`); with AI_ENABLED=false no reader stands in. Before: the
first `/boq/ensure` answered `extracted=true` with no line, stamped `boq_extracted_at`, and every later open returned that
empty BOQ even after the model was enabled; the re-read job *succeeded* with every sheet in `failed_sheets`; and a sheet
that could not be read had its existing BOQ lines offered as **removals** ("the sheet no longer yields this line") —
an engineer accepting them would have deleted lines no one had re-read (a snapshot is taken first, so they were
restorable, but the candidate misstated why).

Fixed within the existing contract (`app/routers/projects.py`, `app/services/boq_candidates.py`, `app/ai/sheet_reader.py`,
`DesignSheetExtraction.attempted`): a read that attempted no sheet (model off/unavailable, file missing) is **not
stamped** — the reasons are returned, each sheet is recorded as not read once (not on every open), and the next open
tries again; a sheet read and found unreadable is still stamped, as documented. A re-read leaves the lines of sheets it
could not read out of the comparison (`summary.not_reread`) — never offered as removals; a re-read that read no sheet
fails (HTTP 409 / job failed) and leaves the BOQ as it was. Reproduced on disposable data
(`test_m2_review05_boq.py`: first read not stamped and read on the next open once a reader can; a previously good BOQ
kept through an all-failed re-read, the job failed; one sheet failing, its lines not removed) and on the 15 frozen
sheets through the API (`boq/integration-candidateC-BOQ-RUN-default.json`: every ensure `extracted=false` with the
reasons, every re-read job failed with "No Design Sheet could be read … the BOQ is unchanged").

### 4c. Real-model accuracy

**Not exercised.** No model call was permitted; nothing here measures it. BLOCKED BY MISSING EVIDENCE for that track.

## 5. Full-suite failures (D5)

| test | baseline | root cause | compatibility impact | disposition |
|---|---|---|---|---|
| `test_submittal_one_per_system.py::test_the_page_counts_submittals_by_their_latest_revision` | passed at 13eb73c / ed7d221; fails since 2221b43 | the test read, through the API's own connection, rows `sync_register` had flushed but not committed (`check()` commits after it); it passed only on the old in-memory harness's single shared connection | none in production (the route commits) | **fixed in the test** (commits as `check` does) |
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` | fails at 13eb73c (pre-M1), ed7d221, 2221b43 and now | migration `c0e4a9b6d321`'s SQLite downgrade rebuilds `users` with `batch_alter_table`, which drops the table while `PRAGMA foreign_keys=ON` (set by `app/database.py` since df61447) — other tables reference `users`, so `DROP TABLE users` fails | downgrades only; the upgrade path is unaffected | existing limitation outside M2 (migration reversibility); fix belongs with that migration (foreign keys off around the batch rebuild); not changed here (no migration in this correction) |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` | fails at 13eb73c and after | commit c49f406 (2026-09-23) made `part_catalog.catalog()` read datasheet part numbers from `PartDatasheetLink` rows instead of walking the library files; the test still sets up only the files | the Proposed Materials completion shows datasheet parts only once the library is indexed — intended by that commit | stale test outside M2; documented, not changed |

## 6. Revalidation on unseen projects (D)

Frozen first (`CANDIDATE-C-FREEZE.json`: source hashes, versions, settings). Declared before any holdout document was
opened (`holdout/HOLDOUT-PLAN.json`): selection, strata, quotas, metrics, unchanged targets, no tuning.

- **Projects** (`holdout/SELECTION.json`): all 1,026 EP folders under the archive root shuffled with seed 20260929; the
  first four eligible, one per contractor, none a pilot project or pilot contractor: EP-28605 (Iwin), EP-19138 (Al Futtaim
  Group), EP-28569 (Aswar Engineering), EP-8430 (Al Ghurair MEP). Metadata only until staged.
- **Documents** (`holdout/HOLDOUT-SAMPLE.json`): 28 documents + 4 Design Sheets by stratum rules on names; no file
  shares a hash with the frozen pilot. The first staging had an encoding bug in one rule (the "Ack" rule could not
  match); it was re-staged before any content was read, and the first result is kept
  (`HOLDOUT-SAMPLE-run1-regex-bug.json`). One file over the declared 60 MB cap was skipped by name (a 138 MB MTS
  approval). Template overlap: the company's own forms (document transmittal, MS cover) are the same template as the
  pilot's; the drawing, submittal-form and BOQ layouts are new families (Nakheel/Dar title block with "Drg. no.",
  National Guard MTS form, ICT budget sheet "#A | Model No | … | Qty").
- **Labels before predictions**: every page up to the reader's budget labelled from renders (`holdout/pages/`, 64 pages)
  and the Word files' text; the four sheets row by row (155 rows); all label files hashed before the first run
  (`holdout/LABELS-FROZEN-BEFORE-RUN.json`, verified unchanged afterwards).
- **Runs**: both profiles on the identical staged set, separate sandbox (`C:/t/holdout`, its own databases and page cache).

Result (evaluator .3 unchanged; `holdout/eval-default.json`, `eval-promoted.json`):

| | default | promoted |
|---|---|---|
| records emitted | 0 | 0 |
| critical | 0 | 0 |
| reference: accepted / readable recovered | 0 / 0 of 9 | 0 / 0 of 9 |
| decision negatives kept | 9 / 9 | 9 / 9 |
| register-false evidence recovered (evaluator's check) | 0 of 11 | 0 of 11 |
| labelled no-record pages with no record (supplementary count) | 48 of 48 | 48 of 48 |

**The holdout fails the recovery target outright**: nothing was read into a record. No wrong value was accepted, but
that says little when nothing was accepted. What was missed (none of it tuned afterwards):

- **H-01** Nakheel/Dar shop drawings AGC-DF-MEP-SD-PAS-02-A/-02-D/-03-D (PAVA, REV 00, clearly printed): the title block
  labels its number cell "Drg. no." and its title "DWG. TITLE", which neither the title-block labels nor the text
  reader's drawing gate recognise → no record, no observation.
- **H-02** the company's own MS cover sheets (`EP-28605 /MA/FA/201`, Rev 00): "/MA/" numbering is outside the reference
  grammar.
- **H-03** the client's National Guard MATERIAL SUBMITTAL forms (MTS-E-0018 Rev 01 "B", Rev 00 "C") and a Dar review
  form (Code 3): outside the grammar; their decisions are not read. The template tick in the A box was therefore never
  put to the test.
- **H-04** as-built ELV sheets: the own number *was* read by the title block (3 of 3, stored as an observation) but not
  their REV cell ("REV" under "ORIGINAL SIZE" in a stacked cell), and the evaluator's raw-evidence check does not look at
  the title-block observation's `number` field (a frozen-evaluator limitation, reported, not changed).
- **H-05** transmittals of *material* submittals (2 scanned, 4 Word incl. both `.docx`): the transmittal reader keeps a
  transmittal's *sample* submissions only; a correctly OCR'd TR/0897/17 was discarded, and the Word ones yield nothing.
  One scanned transmittal whose OCR lost the TR line was correctly kept as `reference_unread`.
- **H-06** holdout BOQ (deterministic, `holdout/boq-holdout.json`): 22 rows accepted, part numbers 13/13, quantities
  18/22 — **4 critical** (EP-8430: a printed "1" read as "4" on three rows, PRS-CSNKP among them, and a "2" read as "9"); every row of the ICT layout
  (EP-28569, "#A" item column) held rather than accepted; recovery 12-18 %.

## 6b. Tests

Reviewer module set (28 modules): 339 passed, 7 skipped, 0 failed. `test_extraction_pilot.py` + the new regressions:
55 passed. Full suite: 1,485 tests, 1,448 passed, 35 skipped, 2 failed (the two pre-M1 failures in section 5).
JUnit files: `../../evidence/r7__suite_submitted.xml`, `r7__suite_new.xml`, `r7__suite_full.xml`.

## 7. Verdict

**CHANGES STILL REQUIRED.** Candidate C removes every critical failure the pilot corpus exposed (30 → 0 per profile under evaluator .3; 35 under .2) and
the BOQ reader's (55 → 5), with a corrected, tested evaluator and versioned truth; but on unseen projects it read
nothing (H-01…H-05), the deterministic BOQ still accepts wrong quantities and confident misreads (4b/H-06 and the 5
open), recovery is below 90 % everywhere, and the real-model track is not exercised. Per the review, the holdout is not
tuned on and remains a failed holdout; a further candidate needs a fresh one.

## 8. What was not touched

The live backend is running from this checkout (API with `--reload` and three workers, started 2026-09-28 09:10 outside
this session; `evidence/r7__live_check.json`). This correction did not start, stop or call it. Read-only: the live
database has had no job or document processing since 2026-09-27 14:58 (890 documents, no `parser_version`), one admin
login at 2026-09-28 15:09; its main file and write-ahead log and `symbol_library.json` keep being rewritten by the API's
start-up on every reload after a source edit (times in the evidence file) — both are operational files and are not part of this correction's diff. Because the API
reloads uncommitted code, the next sync through it would run candidate C; stopping it is the owner's call
(`../../M2-RECOVERY-CHECKLIST.md`).
