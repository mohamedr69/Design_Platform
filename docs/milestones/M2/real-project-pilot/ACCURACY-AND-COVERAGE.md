# Accuracy, coverage and workload -- real-project pilot (2026-09-28)

Scored with `outputs/scripts/score.py` against `GOLDEN-LABELS.json`; per-document expected/actual rows in
`outputs/candidate{A,B}/per-document-<profile>.json`, the summaries in `outputs/candidate{A,B}/ACCURACY.json`.
Two candidates, same frozen sample, same labels: **A** is the frozen candidate (parser `parse-2026-09-28.4`),
scored on every cohort including the holdout before any fix; **B** is A plus the four bounded fixes P-01..P-04
(`DEFECTS.md`), rerun on both profiles. Accuracy, coverage and workload are reported separately; a sampled run
is never a validation of a whole project.

## 1. How a field is scored

- **Document outcome** (exclusive): `complete`, `bounded` (a page or OCR budget left pages unvisited, recorded
  in the ledger), `partial` (a page or OCR failed), `failed`, `unavailable`, `unsupported` (not registered),
  `not-run`. The Word transmittals read through the transmittal reader are counted `complete`.
- **Field validation state**, per critical field (reference, revision, decision) and system:
  `correct` (the reader's accepted value equals the label after the documented normalisation: whitespace and
  case for references, `R<n>` for revisions, a trailing `-R<n>` suffix on a labelled reference counts as the
  revision the reader files it under), `near` (same alphanumerics, different punctuation or a cut suffix:
  counted as wrong), `wrong`, `abstained` (no record, or the decision left `UR` / held as a candidate: nothing
  auto-accepted), `unscorable` (the label is `absent`, `n/a`, `unknown`, `illegible` or unlabelled).
- **Precision of accepted** = correct / (correct + wrong + near) among auto-accepted values. **Automatic
  recovery** = correct / (accepted + abstained). **Review rate** = abstained / (accepted + abstained).
- **Scope**: the M2 reader registers submissions, their covers and replies, contractor shop-drawing sheets and
  transmittals. Consultant IFC / tender sheets, specifications, letters, catalogues, calculations, authority
  documents and commercial papers carry a reference on the page too, and are labelled, but a record on them is
  not what the reader is for; the tables give both the whole sample and the in-scope subset (137 documents).
- A decision label of `n/a` (no consultant decision applies) is scored correct when the reader accepts nothing
  or leaves `UR`; an accepted `approved` / `ANN` / `rejected` on such a document would be a false acceptance.

## 2. Headline (default profile; the promoted profile is within a few documents of it, tables below)

| | candidate A, all 380 | candidate A, in scope (137) | candidate B, all 380 | candidate B, in scope (137) | target |
|---|---|---|---|---|---|
| decision: precision of accepted | 100 % (81/81) | 100 % (73/73) | 100 % (80/80) | 100 % (72/72) | >= 98 % |
| decision: automatic recovery | 66.4 % | 66.4 % | 65.6 % | 65.5 % | >= 90 % |
| reference: precision of accepted | 69.5 % (57/82) | 70.5 % (55/78) | 74.2 % (69/93) | 78.8 % (67/85) | >= 98 % |
| reference: automatic recovery | 19.0 % | 44.4 % | 23.0 % | 54.0 % | >= 90 % |
| revision: precision of accepted | 66.2 % (51/77) | 65.8 % (48/73) | 65.1 % (56/86) | 64.6 % (51/79) | >= 98 % |
| revision: automatic recovery | 19.3 % | 42.5 % | 21.2 % | 45.1 % | >= 90 % |
| false consultant approvals | 0 | 0 | 0 | 0 | 0 |
| wrong reference / revision accepted (critical) | 25 / 26 | | 24 / 30 | | 0 |

By cohort, in scope, candidate B default: regression (54 documents) reference 30/32 accepted correct, revision
29/29, decision 41/41; exploration (62) reference 24/39, revision 15/37, decision 20/20; holdout (21)
reference 13/14, revision 7/13, decision 11/11. The regression controls hold; the new layouts do not.

The accepted decisions are 11 `rejected` and 8 `ANN` (candidate B default), every one agreeing with the
label; the 42 abstentions are 24 `UR` where a mark exists (the LACASA handwritten circles, the Emaar ticked
boxes, the Dutco X marks: decision marks the reader does not yet read), 16 documents with no record, and 2
York covers where the correct decision is held as a candidate under the default profile (the promoted profile
accepts both, correctly).

## 3. What failed and why (candidate B; every case with its render in the tables below and in `DEFECTS.md`)

- **Revision from the wrong row** (P-06): 30 wrong revisions, all on drawing sheets whose revision table lists
  several rows or whose number carries a sheet-index suffix; BK Gulf (EP-25091), CSCEC / CKR (EP-26082), JAM
  (EP-26369). The reader takes the first row (or the `-01` sheet index) for the current revision.
- **Neighbour number from a reference table** (P-07): 12 wrong references on sheets that print a
  reference-drawings or shop-drawings table.
- **Reply sheets and transmittals** (P-08, P-09): 3 references taken from a quoted drawing or an item.
- **OCR** (P-10, P-11): 2 references with a dropped digit or character.
- **A quotation quoting a submittal number** (new with P-04): `EP-19977-Var1-Voltas.pdf` now accepts the
  `-MAT-` number its terms quote; the label is the quotation's own `EP-19977-Var. 01`. Listed, not hidden.
- One label of medium confidence disagrees with the reader on one character (`...-MAT-ELV-0023` against
  `...-MAT-ELE-0023`, EP-19977 CBS MS R1); the small print leaves it open, scored as wrong.

## 4. Coverage and page accounting (both candidates, both profiles: identical ledgers)

| | value |
|---|---|
| documents registered | 385 (default) / 387 (promoted: two EP-30088 sheets staged in between); the 380 sampled plus the BOQ sheets staged into the same trees |
| outcomes | complete 343, bounded 36, failed 1 (the 0-byte original), partial 0, unavailable 0 |
| pages | 6,379 in the ledgers; 1,170 visited, 5,209 skipped by budget (33 documents stopped by the 12-page scan limit, 3 by the reply-search limit), 0 failed |
| OCR | 215 to 224 pages attempted, 0 failed, 0 left out by the OCR budget |
| records on skipped pages | none carried in the sandbox runs (first reads); exercised on real copies in the scenarios (`COMPATIBILITY-AND-PERSISTENCE.md`) |
| BOQ rows | 778 labelled on 15 sheets, 0 read (model-only path, not exercised) |

## 5. Workload (same machine, `SYNC_FILE_WORKERS=0`, inline jobs; `outputs/candidate*/RUN-*.json` telemetry)

| run | wall time for the ten projects | slowest documents |
|---|---|---|
| candidate A default (cold OCR cache) | 899 s (EP-25091 169 s, EP-26369 158 s, EP-26082 152 s, EP-29076 132 s, EP-30784 102 s) | `AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` 68 s, `RDJ183 FA Stamped.pdf` 66 s, `R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf` 54 s (large A0 sheets, region OCR) |
| candidate A promoted (warm, content-keyed OCR cache) | 174 s | `AKA-DCC-ID-02-SD-TL-0504.pdf` 25 s (a render, not OCR) |
| candidate B default and promoted (warm) | about 3 to 4 minutes each | as above |

OCR documents per project (default): 17, 15, 21, 2, 9, 15, 21, 10, 12, 6. Retries: the sandbox runs needed
none; the scenarios drove failed and partial retries deliberately. Interruptions: one, deliberate (scenario 19).
The live setting of three sync workers was not used in the sandbox, so these times are single-worker times.

## 6. Tables

The tables that follow are generated (`outputs/scripts/render_tables.py`) from `ACCURACY.json` of each
candidate. Render links: `crops/sheet-NNN.jpg` holds four documents per sheet (tile index in brackets),
`crops/tb-NNN.jpg` the title-block strips of drawing-sized sheets, `crops/boq/` the BOQ pages.

### Candidate A (parse-2026-09-28.4, frozen before any fix)


**Profile `default`** -- document outcomes (exclusive): bounded 36, complete 343, failed 1

| field | auto-accepted | correct | wrong | near (punctuation / suffix) | abstained (UR / held / no record) | unscorable (label absent, n/a, unknown, illegible) | precision of accepted | automatic recovery | review rate |
|---|---|---|---|---|---|---|---|---|---|
| reference | 82 | 57 | 25 | 1 | 218 | 69 | 69.5 % | 19.0 % | 72.7 % |
| revision | 77 | 51 | 26 | 0 | 187 | 105 | 66.2 % | 19.3 % | 70.8 % |
| decision | 81 | 81 | 0 | 0 | 41 | 247 | 100.0 % | 66.4 % | 33.6 % |
| system | 77 | 65 | 12 | 0 | 292 | 0 | 84.4 % | 17.6 % | 79.1 % |

Pages: total 6379, visited 1170, skipped by budget 5209, failed 0; OCR attempted on 215 pages, failed 0, left out by the OCR budget 0; stop reasons null 344, page_scan_limit 34, reply_search_limit 2.


By cohort:

| cohort | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| exploration | 192 | bounded 15, complete 176, failed 1 | 18 / 40 (106) | 17 / 38 (96) | 25 / 25 (26) | 30 / 40 |
| holdout | 108 | bounded 9, complete 99 | 9 / 10 (73) | 5 / 10 (63) | 14 / 14 (11) | 9 / 10 |
| regression | 80 | bounded 12, complete 68 | 30 / 32 (39) | 29 / 29 (28) | 42 / 42 (4) | 26 / 27 |

By project:

| project | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| 13777 | 40 | bounded 5, complete 35 | 0 / 0 (21) | 0 / 0 (14) | 4 / 4 (8) | 0 / 0 |
| 14119 | 6 | complete 6 | 0 / 0 (5) | 0 / 0 (4) | 0 / 0 (0) | 0 / 0 |
| 19977 | 32 | bounded 1, complete 31 | 0 / 2 (17) | 2 / 2 (10) | 1 / 1 (6) | 2 / 2 |
| 25091 | 50 | bounded 3, complete 47 | 6 / 13 (29) | 1 / 13 (27) | 12 / 12 (9) | 5 / 13 |
| 26082 | 55 | bounded 7, complete 47, failed 1 | 5 / 9 (33) | 3 / 9 (32) | 3 / 3 (3) | 8 / 9 |
| 26369 | 60 | bounded 4, complete 56 | 9 / 10 (45) | 5 / 10 (43) | 10 / 10 (3) | 9 / 10 |
| 27474 | 2 | complete 2 | 0 / 0 (2) | 0 / 0 (2) | 0 / 0 (0) | 0 / 0 |
| 29076 | 55 | bounded 4, complete 51 | 7 / 16 (27) | 11 / 14 (27) | 9 / 9 (8) | 15 / 16 |
| 30088 | 40 | bounded 7, complete 33 | 11 / 11 (23) | 11 / 11 (15) | 19 / 19 (4) | 10 / 10 |
| 30784 | 40 | bounded 5, complete 35 | 19 / 21 (16) | 18 / 18 (13) | 23 / 23 (0) | 16 / 17 |

By stratum (path rule):

| stratum (path rule) | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| approval_sample | 18 | bounded 2, complete 16 | 4 / 6 (12) | 4 / 5 (8) | 3 / 3 (7) | 6 / 6 |
| calc | 9 | bounded 1, complete 8 | 1 / 1 (2) | 0 / 1 (1) | 2 / 2 (0) | 0 / 1 |
| design_sheet | 17 | bounded 1, complete 16 | 0 / 1 (12) | 0 / 1 (8) | 0 / 0 (1) | 1 / 1 |
| drawing_ifc_input | 90 | bounded 7, complete 83 | 1 / 3 (83) | 2 / 3 (82) | 4 / 4 (0) | 2 / 3 |
| other | 50 | bounded 8, complete 42 | 0 / 0 (24) | 0 / 0 (19) | 2 / 2 (2) | 0 / 0 |
| reply | 34 | bounded 2, complete 31, failed 1 | 12 / 16 (12) | 12 / 13 (6) | 9 / 9 (10) | 10 / 10 |
| scan | 31 | bounded 2, complete 29 | 0 / 4 (23) | 3 / 3 (15) | 1 / 1 (8) | 2 / 4 |
| shop_drawing | 81 | bounded 1, complete 80 | 38 / 50 (28) | 29 / 50 (29) | 56 / 56 (12) | 44 / 51 |
| spec_compliance | 18 | bounded 5, complete 13 | 0 / 0 (13) | 0 / 0 (14) | 0 / 0 (0) | 0 / 0 |
| submittal | 22 | bounded 7, complete 15 | 1 / 1 (9) | 1 / 1 (5) | 4 / 4 (1) | 0 / 1 |
| transmittal_word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

By format:

| format | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| scan | 67 | bounded 5, complete 62 | 3 / 13 (38) | 7 / 11 (22) | 4 / 4 (13) | 13 / 14 |
| text | 303 | bounded 31, complete 271, failed 1 | 54 / 69 (180) | 44 / 66 (165) | 77 / 77 (28) | 52 / 63 |
| word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

Critical failures, profile `default`: 51 -- wrong reference 24, wrong revision 26, reference differs in punctuation/suffix 1

| kind | document | expected (label) | actual (reader) | render |
|---|---|---|---|---|
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-3\Reply to MS Consultant Comments 31 (3).pdf` | `BBY006-GME-SDW-EL-LI-POD-P03-010031` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-007.jpg#tile-27 |
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-1\Reply to MS Consultant Comments 31 (1).pdf` | `BBY006-GME-SDW-EL-LI-POD-P01-010029` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-008.jpg#tile-28 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-003-R3` | `25H-AAEM-SD-ELEC-FA-B1-003` | crops/sheet-022.jpg#tile-84 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `R3` | `R0` | crops/sheet-022.jpg#tile-84 |
| wrong reference | `EP-29076/06- Drawings\01- FA\Fire Alarm\50 53rd Floor Fire Alarm Layout\1. R0\1. Submission\25H-S202-NCC-SD-MEP-ELE-FA-050-00.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-050-00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-050-00` | crops/sheet-022.jpg#tile-85 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-NCC-SD-MEP-ELE-FA-024-R00 - Code C.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-024-R0` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-024-RO` | crops/sheet-023.jpg#tile-89 |
| wrong reference | `EP-29076/06- Drawings\01- FA\Fire Alarm\31. 24th Floor Fire Alarm Layout\25H-S202-NCC-SD-MEP-ELE-FA-031-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-031-R00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-031` | crops/sheet-023.jpg#tile-91 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\30. 23rd Floor Emergency Lighting Layout\1. R0\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-030-R0` | `25H-S202-NCC-SD-MEP-ELE-EM-30-RO` | crops/sheet-028.jpg#tile-111 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-23-02` | `25H-AAEM-SD-ELEC-EM` | crops/sheet-029.jpg#tile-112 |
| wrong revision | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `02` | `R0` | crops/sheet-029.jpg#tile-112 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-047-00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-047-00` | crops/sheet-030.jpg#tile-118 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | `00` | `R2` | crops/sheet-030.jpg#tile-118 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-057-R00 - Code B\25H-S202-NCC-SD-MEP-ELE-FA-057-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-057-00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-057-00` | crops/sheet-030.jpg#tile-119 |
| wrong reference | `EP-29076/01- EP-29076 - Scan\EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf` | `TR/0127/26` | `25H-S202-NCC-MAS-MEP` | crops/sheet-032.jpg#tile-124 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `AKA-BKG-ELE-B1-SD-PAVA-00010` | `AKA-BKG-ELE-B1-SD-PAVA-00008` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `02` | `R0` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| reference differs in punctuation/suffix | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `AKA-DCC-ELE-FA-SD-000285-R2` | `AKA-DCC-ELE-FA-SD-000285` | crops/sheet-039.jpg#tile-155 |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `2` | `R0` | crops/sheet-039.jpg#tile-155 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `AKA-BKG-ELE-UR-SD-CBS-00054` | `AKA-BKG-ELE-CBS-SD-FA-00052` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00107.pdf` | `02` | `R0` | crops/sheet-040.jpg#tile-157, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R1 B\AKA-BKG-ELE-FA-SD-SCH-00102.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-158, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00055` | `AKA-BKG-ELE-LR-SD-PAVA-00053` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\1F MZ\AKA-BKG-ELE-1M-SD-PAVA-00026.pdf` | `AKA-BKG-ELE-1M-SD-PAVA-00026` | `AKA-BKG-ELE-1M-SD-PAVA-00027` | crops/sheet-041.jpg#tile-160, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00105.pdf` | `02` | `R0` | crops/sheet-041.jpg#tile-162, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\1M\R1 B\AKA-BKG-ELE-1M-SD-CBS-00028.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-163, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `01` | `R0` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\FAS\SCH\AKA-BKG-ELE-FA-SD-SCH-00100.pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-165, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 Calc\SPL\Atrium\AKA-BKG-ELE-GM-SD-PAVA-00016 (5).pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-166, crops/tb-024.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\General Drawings\ELECTRICAL\05. ICT\PDF\SA-H2-BEST-ICT-00100a.pdf` | `SA-H2-BEST-ICT-00100a` | `SA-H2-BEST-FA-00104` | crops/sheet-051.jpg#tile-200, crops/tb-030.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\R2\JAM-SD-FA-006-01.pdf` | `01` | `R2` | crops/sheet-055.jpg#tile-218, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -3\JAM-SD-FA-002.pdf` | `07` | `R10` | crops/sheet-055.jpg#tile-219, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-001 (LOW).pdf` | `05` | `R1` | crops/sheet-056.jpg#tile-222, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\JAM-SD-FA-001 (HIGH).pdf` | `04` | `R0` | crops/sheet-056.jpg#tile-223, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-004.pdf` | `06` | `R0` | crops/sheet-057.jpg#tile-224, crops/tb-033.jpg |
| wrong reference | `EP-19977/EP-19977 Scan Doc\EP-19977 FA MS R1 App.pdf` | `EBF-DCP-6374-VL-MAT-ELV-0003` | `Reference` | crops/sheet-062.jpg#tile-244 |
| wrong reference | `EP-19977/EP-19977 Scan Doc\EP-19977 FA MS R0 R&R.pdf` | `EBF-DCP-6374-VL-MAT-ELV-0003` | `Reference` | crops/sheet-063.jpg#tile-251 |
| wrong reference | `EP-26082/EP-26082 INPUTS\IFC DOC\OneDrive_2024-08-17\Dwgs\IBA IFC DWGS\FA & EM (CENT ENT)\PDF\R1029-16-IBA-DWG-L01-FAS-1231-PDF [0].pdf` | `R1029-16-IBA-DWG-L01-FAS-1231` | `R1029-16-IBA-DWG-L01-FAS-1233` | crops/sheet-081.jpg#tile-321, crops/tb-038.jpg |
| wrong revision | `EP-26082/EP-26082 INPUTS\TENDER DWGS\MGM\04-21_MGM HOTEL\09 OF 96_MEP - MGM 2 ELECTRICAL ELV\R1029-08-CKR-DWG-L09-EML-1209-PDF [B].pdf` | `B` | `R0` | crops/sheet-083.jpg#tile-329, crops/tb-040.jpg |
| wrong reference | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201` | `R1029-CSCEC-MEP-SD-MGM1-L02-FAS-1202` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `02` | `R1` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/SD\FAVE\MGM1\AB\L8\R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf` | `AB` | `R1` | crops/sheet-086.jpg#tile-343, crops/tb-043.jpg |
| wrong revision | `EP-26082/SD\APP SD\FAVE\M1\R1029-CSCEC-MEP-SD-MGM1-B01-FAS-1199 rev.02.pdf` | `02` | `R1` | crops/sheet-087.jpg#tile-345, crops/tb-044.jpg |
| wrong reference | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01` | `R1029-CSCEC-MEP-SD-MGM1-L01-EML-1201` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `00` | `R1` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\MGM1\Rev.02\L8\R1029-CSCEC-MEP-SD-MGM1-L8-EML-1208-01.pdf` | `02` | `R0` | crops/sheet-087.jpg#tile-347, crops/tb-044.jpg |
| wrong reference | `EP-26082/EP-26082 SCAN DOC\R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf` | `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020` | `1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-Rev` | crops/sheet-091.jpg#tile-362 |

**Profile `promoted`** -- document outcomes (exclusive): bounded 36, complete 343, failed 1

| field | auto-accepted | correct | wrong | near (punctuation / suffix) | abstained (UR / held / no record) | unscorable (label absent, n/a, unknown, illegible) | precision of accepted | automatic recovery | review rate |
|---|---|---|---|---|---|---|---|---|---|
| reference | 86 | 61 | 25 | 1 | 214 | 69 | 70.9 % | 20.3 % | 71.3 % |
| revision | 78 | 52 | 26 | 0 | 186 | 105 | 66.7 % | 19.7 % | 70.5 % |
| decision | 84 | 84 | 0 | 0 | 38 | 247 | 100.0 % | 68.8 % | 31.1 % |
| system | 81 | 67 | 14 | 0 | 288 | 0 | 82.7 % | 18.2 % | 78.0 % |

Pages: total 6379, visited 1170, skipped by budget 5209, failed 0; OCR attempted on 216 pages, failed 0, left out by the OCR budget 0; stop reasons null 344, page_scan_limit 34, reply_search_limit 2.


By cohort:

| cohort | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| exploration | 192 | bounded 15, complete 176, failed 1 | 19 / 41 (105) | 17 / 38 (96) | 25 / 25 (26) | 30 / 41 |
| holdout | 108 | bounded 9, complete 99 | 9 / 10 (73) | 5 / 10 (63) | 14 / 14 (11) | 9 / 10 |
| regression | 80 | bounded 12, complete 68 | 33 / 35 (36) | 30 / 30 (27) | 45 / 45 (1) | 28 / 30 |

By project:

| project | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| 13777 | 40 | bounded 5, complete 35 | 0 / 0 (21) | 0 / 0 (14) | 4 / 4 (8) | 0 / 0 |
| 14119 | 6 | complete 6 | 0 / 0 (5) | 0 / 0 (4) | 0 / 0 (0) | 0 / 0 |
| 19977 | 32 | bounded 1, complete 31 | 1 / 3 (16) | 2 / 2 (10) | 1 / 1 (6) | 2 / 3 |
| 25091 | 50 | bounded 3, complete 47 | 6 / 13 (29) | 1 / 13 (27) | 12 / 12 (9) | 5 / 13 |
| 26082 | 55 | bounded 7, complete 47, failed 1 | 5 / 9 (33) | 3 / 9 (32) | 3 / 3 (3) | 8 / 9 |
| 26369 | 60 | bounded 4, complete 56 | 9 / 10 (45) | 5 / 10 (43) | 10 / 10 (3) | 9 / 10 |
| 27474 | 2 | complete 2 | 0 / 0 (2) | 0 / 0 (2) | 0 / 0 (0) | 0 / 0 |
| 29076 | 55 | bounded 4, complete 51 | 7 / 16 (27) | 11 / 14 (27) | 9 / 9 (8) | 15 / 16 |
| 30088 | 40 | bounded 7, complete 33 | 13 / 13 (21) | 12 / 12 (14) | 22 / 22 (1) | 11 / 12 |
| 30784 | 40 | bounded 5, complete 35 | 20 / 22 (15) | 18 / 18 (13) | 23 / 23 (0) | 17 / 18 |

By stratum (path rule):

| stratum (path rule) | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| approval_sample | 18 | bounded 2, complete 16 | 4 / 6 (12) | 4 / 5 (8) | 3 / 3 (7) | 6 / 6 |
| calc | 9 | bounded 1, complete 8 | 1 / 1 (2) | 0 / 1 (1) | 2 / 2 (0) | 0 / 1 |
| design_sheet | 17 | bounded 1, complete 16 | 0 / 1 (12) | 0 / 1 (8) | 0 / 0 (1) | 1 / 1 |
| drawing_ifc_input | 90 | bounded 7, complete 83 | 1 / 3 (83) | 2 / 3 (82) | 4 / 4 (0) | 2 / 3 |
| other | 50 | bounded 8, complete 42 | 0 / 0 (24) | 0 / 0 (19) | 2 / 2 (2) | 0 / 0 |
| reply | 34 | bounded 2, complete 31, failed 1 | 13 / 17 (11) | 13 / 14 (5) | 12 / 12 (7) | 11 / 11 |
| scan | 31 | bounded 2, complete 29 | 3 / 7 (20) | 3 / 3 (15) | 1 / 1 (8) | 3 / 7 |
| shop_drawing | 81 | bounded 1, complete 80 | 38 / 50 (28) | 29 / 50 (29) | 56 / 56 (12) | 44 / 51 |
| spec_compliance | 18 | bounded 5, complete 13 | 0 / 0 (13) | 0 / 0 (14) | 0 / 0 (0) | 0 / 0 |
| submittal | 22 | bounded 7, complete 15 | 1 / 1 (9) | 1 / 1 (5) | 4 / 4 (1) | 0 / 1 |
| transmittal_word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

By format:

| format | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| scan | 67 | bounded 5, complete 62 | 6 / 16 (35) | 7 / 11 (22) | 4 / 4 (13) | 14 / 17 |
| text | 303 | bounded 31, complete 271, failed 1 | 55 / 70 (179) | 45 / 67 (164) | 80 / 80 (25) | 53 / 64 |
| word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

Critical failures, profile `promoted`: 52 -- wrong reference 24, printed EP differs from the folder's EP (association to check) 1, wrong revision 26, reference differs in punctuation/suffix 1

| kind | document | expected (label) | actual (reader) | render |
|---|---|---|---|---|
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-3\Reply to MS Consultant Comments 31 (3).pdf` | `BBY006-GME-SDW-EL-LI-POD-P03-010031` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-007.jpg#tile-27 |
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-1\Reply to MS Consultant Comments 31 (1).pdf` | `BBY006-GME-SDW-EL-LI-POD-P01-010029` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-008.jpg#tile-28 |
| printed EP differs from the folder's EP (association to check) | `EP-30088/09. Scan Document\EP-30088 CBS Sam B ack 13.08.26.pdf` | `EP-30058` | `TR/204/26` | crops/sheet-019.jpg#tile-75 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-003-R3` | `25H-AAEM-SD-ELEC-FA-B1-003` | crops/sheet-022.jpg#tile-84 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `R3` | `R0` | crops/sheet-022.jpg#tile-84 |
| wrong reference | `EP-29076/06- Drawings\01- FA\Fire Alarm\50 53rd Floor Fire Alarm Layout\1. R0\1. Submission\25H-S202-NCC-SD-MEP-ELE-FA-050-00.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-050-00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-050-00` | crops/sheet-022.jpg#tile-85 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-NCC-SD-MEP-ELE-FA-024-R00 - Code C.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-024-R0` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-024-RO` | crops/sheet-023.jpg#tile-89 |
| wrong reference | `EP-29076/06- Drawings\01- FA\Fire Alarm\31. 24th Floor Fire Alarm Layout\25H-S202-NCC-SD-MEP-ELE-FA-031-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-031-R00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-031` | crops/sheet-023.jpg#tile-91 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\30. 23rd Floor Emergency Lighting Layout\1. R0\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-030-R0` | `25H-S202-NCC-SD-MEP-ELE-EM-30-RO` | crops/sheet-028.jpg#tile-111 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-23-02` | `25H-AAEM-SD-ELEC-EM` | crops/sheet-029.jpg#tile-112 |
| wrong revision | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `02` | `R0` | crops/sheet-029.jpg#tile-112 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-047-00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-047-00` | crops/sheet-030.jpg#tile-118 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | `00` | `R2` | crops/sheet-030.jpg#tile-118 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-057-R00 - Code B\25H-S202-NCC-SD-MEP-ELE-FA-057-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-057-00` | `Reference25H-S202-NCC-SD-MEP-ELE-FA-057-00` | crops/sheet-030.jpg#tile-119 |
| wrong reference | `EP-29076/01- EP-29076 - Scan\EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf` | `TR/0127/26` | `25H-S202-NCC-MAS-MEP` | crops/sheet-032.jpg#tile-124 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `AKA-BKG-ELE-B1-SD-PAVA-00010` | `AKA-BKG-ELE-B1-SD-PAVA-00008` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `02` | `R0` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| reference differs in punctuation/suffix | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `AKA-DCC-ELE-FA-SD-000285-R2` | `AKA-DCC-ELE-FA-SD-000285` | crops/sheet-039.jpg#tile-155 |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `2` | `R0` | crops/sheet-039.jpg#tile-155 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `AKA-BKG-ELE-UR-SD-CBS-00054` | `AKA-BKG-ELE-CBS-SD-FA-00052` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00107.pdf` | `02` | `R0` | crops/sheet-040.jpg#tile-157, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R1 B\AKA-BKG-ELE-FA-SD-SCH-00102.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-158, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00055` | `AKA-BKG-ELE-LR-SD-PAVA-00053` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\1F MZ\AKA-BKG-ELE-1M-SD-PAVA-00026.pdf` | `AKA-BKG-ELE-1M-SD-PAVA-00026` | `AKA-BKG-ELE-1M-SD-PAVA-00027` | crops/sheet-041.jpg#tile-160, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00105.pdf` | `02` | `R0` | crops/sheet-041.jpg#tile-162, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\1M\R1 B\AKA-BKG-ELE-1M-SD-CBS-00028.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-163, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `01` | `R0` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\FAS\SCH\AKA-BKG-ELE-FA-SD-SCH-00100.pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-165, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 Calc\SPL\Atrium\AKA-BKG-ELE-GM-SD-PAVA-00016 (5).pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-166, crops/tb-024.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\General Drawings\ELECTRICAL\05. ICT\PDF\SA-H2-BEST-ICT-00100a.pdf` | `SA-H2-BEST-ICT-00100a` | `SA-H2-BEST-FA-00104` | crops/sheet-051.jpg#tile-200, crops/tb-030.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\R2\JAM-SD-FA-006-01.pdf` | `01` | `R2` | crops/sheet-055.jpg#tile-218, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -3\JAM-SD-FA-002.pdf` | `07` | `R10` | crops/sheet-055.jpg#tile-219, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-001 (LOW).pdf` | `05` | `R1` | crops/sheet-056.jpg#tile-222, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\JAM-SD-FA-001 (HIGH).pdf` | `04` | `R0` | crops/sheet-056.jpg#tile-223, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-004.pdf` | `06` | `R0` | crops/sheet-057.jpg#tile-224, crops/tb-033.jpg |
| wrong reference | `EP-19977/EP-19977 Scan Doc\EP-19977 FA MS R1 App.pdf` | `EBF-DCP-6374-VL-MAT-ELV-0003` | `Reference` | crops/sheet-062.jpg#tile-244 |
| wrong reference | `EP-19977/EP-19977 Scan Doc\EP-19977 FA MS R0 R&R.pdf` | `EBF-DCP-6374-VL-MAT-ELV-0003` | `Reference` | crops/sheet-063.jpg#tile-251 |
| wrong reference | `EP-26082/EP-26082 INPUTS\IFC DOC\OneDrive_2024-08-17\Dwgs\IBA IFC DWGS\FA & EM (CENT ENT)\PDF\R1029-16-IBA-DWG-L01-FAS-1231-PDF [0].pdf` | `R1029-16-IBA-DWG-L01-FAS-1231` | `R1029-16-IBA-DWG-L01-FAS-1233` | crops/sheet-081.jpg#tile-321, crops/tb-038.jpg |
| wrong revision | `EP-26082/EP-26082 INPUTS\TENDER DWGS\MGM\04-21_MGM HOTEL\09 OF 96_MEP - MGM 2 ELECTRICAL ELV\R1029-08-CKR-DWG-L09-EML-1209-PDF [B].pdf` | `B` | `R0` | crops/sheet-083.jpg#tile-329, crops/tb-040.jpg |
| wrong reference | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201` | `R1029-CSCEC-MEP-SD-MGM1-L02-FAS-1202` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `02` | `R1` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/SD\FAVE\MGM1\AB\L8\R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf` | `AB` | `R1` | crops/sheet-086.jpg#tile-343, crops/tb-043.jpg |
| wrong revision | `EP-26082/SD\APP SD\FAVE\M1\R1029-CSCEC-MEP-SD-MGM1-B01-FAS-1199 rev.02.pdf` | `02` | `R1` | crops/sheet-087.jpg#tile-345, crops/tb-044.jpg |
| wrong reference | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01` | `R1029-CSCEC-MEP-SD-MGM1-L01-EML-1201` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `00` | `R1` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\MGM1\Rev.02\L8\R1029-CSCEC-MEP-SD-MGM1-L8-EML-1208-01.pdf` | `02` | `R0` | crops/sheet-087.jpg#tile-347, crops/tb-044.jpg |
| wrong reference | `EP-26082/EP-26082 SCAN DOC\R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf` | `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020` | `1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-Rev` | crops/sheet-091.jpg#tile-362 |

### Candidate B (parse-2026-09-28.5, after P-01..P-04)


**Profile `default`** -- document outcomes (exclusive): bounded 36, complete 343, failed 1

| field | auto-accepted | correct | wrong | near (punctuation / suffix) | abstained (UR / held / no record) | unscorable (label absent, n/a, unknown, illegible) | precision of accepted | automatic recovery | review rate |
|---|---|---|---|---|---|---|---|---|---|
| reference | 93 | 69 | 24 | 1 | 207 | 69 | 74.2 % | 23.0 % | 69.0 % |
| revision | 86 | 56 | 30 | 0 | 178 | 105 | 65.1 % | 21.2 % | 67.4 % |
| decision | 80 | 80 | 0 | 0 | 42 | 247 | 100.0 % | 65.6 % | 34.4 % |
| system | 86 | 72 | 14 | 0 | 283 | 0 | 83.7 % | 19.5 % | 76.7 % |

Pages: total 6379, visited 1170, skipped by budget 5209, failed 0; OCR attempted on 224 pages, failed 0, left out by the OCR budget 0; stop reasons null 344, page_scan_limit 33, reply_search_limit 3.


By cohort:

| cohort | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| exploration | 192 | bounded 15, complete 176, failed 1 | 26 / 43 (103) | 17 / 41 (93) | 24 / 24 (27) | 31 / 43 |
| holdout | 108 | bounded 9, complete 99 | 13 / 18 (65) | 10 / 16 (57) | 14 / 14 (11) | 15 / 16 |
| regression | 80 | bounded 12, complete 68 | 30 / 32 (39) | 29 / 29 (28) | 42 / 42 (4) | 26 / 27 |

By project:

| project | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| 13777 | 40 | bounded 5, complete 35 | 1 / 2 (19) | 1 / 1 (13) | 4 / 4 (8) | 1 / 1 |
| 14119 | 6 | complete 6 | 0 / 0 (5) | 0 / 0 (4) | 0 / 0 (0) | 0 / 0 |
| 19977 | 32 | bounded 1, complete 31 | 3 / 5 (14) | 2 / 5 (7) | 0 / 0 (7) | 3 / 5 |
| 25091 | 50 | bounded 3, complete 47 | 6 / 13 (29) | 1 / 13 (27) | 12 / 12 (9) | 5 / 13 |
| 26082 | 55 | bounded 7, complete 47, failed 1 | 5 / 9 (33) | 3 / 9 (32) | 3 / 3 (3) | 8 / 9 |
| 26369 | 60 | bounded 4, complete 56 | 12 / 16 (39) | 9 / 15 (38) | 10 / 10 (3) | 14 / 15 |
| 27474 | 2 | complete 2 | 0 / 0 (2) | 0 / 0 (2) | 0 / 0 (0) | 0 / 0 |
| 29076 | 55 | bounded 4, complete 51 | 12 / 16 (27) | 11 / 14 (27) | 9 / 9 (8) | 15 / 16 |
| 30088 | 40 | bounded 7, complete 33 | 11 / 11 (23) | 11 / 11 (15) | 19 / 19 (4) | 10 / 10 |
| 30784 | 40 | bounded 5, complete 35 | 19 / 21 (16) | 18 / 18 (13) | 23 / 23 (0) | 16 / 17 |

By stratum (path rule):

| stratum (path rule) | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| approval_sample | 18 | bounded 2, complete 16 | 7 / 7 (11) | 5 / 6 (7) | 3 / 3 (7) | 6 / 6 |
| calc | 9 | bounded 1, complete 8 | 1 / 1 (2) | 0 / 1 (1) | 2 / 2 (0) | 0 / 1 |
| design_sheet | 17 | bounded 1, complete 16 | 0 / 1 (12) | 0 / 1 (8) | 0 / 0 (1) | 1 / 1 |
| drawing_ifc_input | 90 | bounded 7, complete 83 | 1 / 5 (81) | 4 / 5 (80) | 4 / 4 (0) | 4 / 5 |
| other | 50 | bounded 8, complete 42 | 0 / 1 (23) | 0 / 1 (18) | 2 / 2 (2) | 1 / 1 |
| reply | 34 | bounded 2, complete 31, failed 1 | 14 / 19 (9) | 13 / 14 (5) | 9 / 9 (10) | 12 / 12 |
| scan | 31 | bounded 2, complete 29 | 3 / 6 (21) | 3 / 5 (13) | 0 / 0 (9) | 2 / 6 |
| shop_drawing | 81 | bounded 1, complete 80 | 41 / 50 (28) | 29 / 50 (29) | 56 / 56 (12) | 44 / 51 |
| spec_compliance | 18 | bounded 5, complete 13 | 0 / 0 (13) | 0 / 0 (14) | 0 / 0 (0) | 0 / 0 |
| submittal | 22 | bounded 7, complete 15 | 2 / 3 (7) | 2 / 3 (3) | 4 / 4 (1) | 2 / 3 |
| transmittal_word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

By format:

| format | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| scan | 67 | bounded 5, complete 62 | 9 / 17 (34) | 8 / 14 (19) | 4 / 4 (13) | 15 / 18 |
| text | 303 | bounded 31, complete 271, failed 1 | 60 / 76 (173) | 48 / 72 (159) | 76 / 76 (29) | 57 / 68 |
| word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

Critical failures, profile `default`: 54 -- wrong reference 23, wrong revision 30, reference differs in punctuation/suffix 1

| kind | document | expected (label) | actual (reader) | render |
|---|---|---|---|---|
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-3\Reply to MS Consultant Comments 31 (3).pdf` | `BBY006-GME-SDW-EL-LI-POD-P03-010031` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-007.jpg#tile-27 |
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-1\Reply to MS Consultant Comments 31 (1).pdf` | `BBY006-GME-SDW-EL-LI-POD-P01-010029` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-008.jpg#tile-28 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-003-R3` | `25H-AAEM-SD-ELEC-FA-B1-003` | crops/sheet-022.jpg#tile-84 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `R3` | `R0` | crops/sheet-022.jpg#tile-84 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\30. 23rd Floor Emergency Lighting Layout\1. R0\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-030-R0` | `25H-S202-NCC-SD-MEP-ELE-EM-30` | crops/sheet-028.jpg#tile-111 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-23-02` | `25H-AAEM-SD-ELEC-EM` | crops/sheet-029.jpg#tile-112 |
| wrong revision | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `02` | `R0` | crops/sheet-029.jpg#tile-112 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | `00` | `R2` | crops/sheet-030.jpg#tile-118 |
| wrong reference | `EP-29076/01- EP-29076 - Scan\EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf` | `TR/0127/26` | `25H-S202-NCC-MAS-MEP` | crops/sheet-032.jpg#tile-124 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `AKA-BKG-ELE-B1-SD-PAVA-00010` | `AKA-BKG-ELE-B1-SD-PAVA-00008` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `02` | `R0` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| reference differs in punctuation/suffix | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `AKA-DCC-ELE-FA-SD-000285-R2` | `AKA-DCC-ELE-FA-SD-000285` | crops/sheet-039.jpg#tile-155 |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `2` | `R0` | crops/sheet-039.jpg#tile-155 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `AKA-BKG-ELE-UR-SD-CBS-00054` | `AKA-BKG-ELE-CBS-SD-FA-00052` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00107.pdf` | `02` | `R0` | crops/sheet-040.jpg#tile-157, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R1 B\AKA-BKG-ELE-FA-SD-SCH-00102.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-158, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00055` | `AKA-BKG-ELE-LR-SD-PAVA-00053` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\1F MZ\AKA-BKG-ELE-1M-SD-PAVA-00026.pdf` | `AKA-BKG-ELE-1M-SD-PAVA-00026` | `AKA-BKG-ELE-1M-SD-PAVA-00027` | crops/sheet-041.jpg#tile-160, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00105.pdf` | `02` | `R0` | crops/sheet-041.jpg#tile-162, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\1M\R1 B\AKA-BKG-ELE-1M-SD-CBS-00028.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-163, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `01` | `R0` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\FAS\SCH\AKA-BKG-ELE-FA-SD-SCH-00100.pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-165, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 Calc\SPL\Atrium\AKA-BKG-ELE-GM-SD-PAVA-00016 (5).pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-166, crops/tb-024.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\Proper Drawings\FIRE ALARM & EMERGENCY LIGHTING\PDF\SA-H2-BEST-FA-00201.pdf` | `SA-H2-BEST-FA-00201` | `SA-H2-BEST-VE-00G01` | crops/sheet-046.jpg#tile-182, crops/tb-025.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\General Drawings\ELECTRICAL\05. ICT\PDF\SA-H2-BEST-ICT-00100a.pdf` | `SA-H2-BEST-ICT-00100a` | `SA-H2-BEST-FA-00104` | crops/sheet-051.jpg#tile-200, crops/tb-030.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\Proper Drawings\FIRE ALARM & EMERGENCY LIGHTING\PDF\SA-H2-BEST-FA-00102c.pdf` | `SA-H2-BEST-FA-00102c` | `SA-H2-BEST-VE-00G01` | crops/sheet-051.jpg#tile-203, crops/tb-030.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\R2\JAM-SD-FA-006-01.pdf` | `01` | `R2` | crops/sheet-055.jpg#tile-218, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -3\JAM-SD-FA-002.pdf` | `07` | `R10` | crops/sheet-055.jpg#tile-219, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-001 (LOW).pdf` | `05` | `R1` | crops/sheet-056.jpg#tile-222, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\JAM-SD-FA-001 (HIGH).pdf` | `04` | `R0` | crops/sheet-056.jpg#tile-223, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-004.pdf` | `06` | `R0` | crops/sheet-057.jpg#tile-224, crops/tb-033.jpg |
| wrong reference | `EP-26369/MS FAS\R1\MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf` | `EP-26369/SS/FA/101` | `RDJ183-RAQ-Naffco-MAT-008` | crops/sheet-057.jpg#tile-227 |
| wrong revision | `EP-26369/MS FAS\R1\MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf` | `01` | `R0` | crops/sheet-057.jpg#tile-227 |
| wrong reference | `EP-19977/EP-19977 Scan Doc\EP-19977 CBS MS R1 R&R.pdf` | `EBF-DCP-6374-VL-MAT-ELV-0023` | `EBF-DCP-6374-VL-MAT-ELE-0023` | crops/sheet-061.jpg#tile-243 |
| wrong revision | `EP-19977/EP-19977 Scan Doc\EP-19977 CBS MS R1 R&R.pdf` | `01` | `R0` | crops/sheet-061.jpg#tile-243 |
| wrong revision | `EP-19977/EP-19977 Scan Doc\EP-19977 FA MS R1 App.pdf` | `01` | `R0` | crops/sheet-062.jpg#tile-244 |
| wrong reference | `EP-19977/EP-19977 Commercial\EP-19977-Var1-Voltas.pdf` | `EP-19977-Var. 01` | `EBF-DCP-6374-VL-MAT-ELV-0003` | crops/sheet-066.jpg#tile-261 |
| wrong revision | `EP-19977/EP-19977 Commercial\EP-19977-Var1-Voltas.pdf` | `Var. 01` | `R0` | crops/sheet-066.jpg#tile-261 |
| wrong reference | `EP-13777/Approval Documents\AAR-001 Commented Material Submittal- Fire Alarm System & Voice Evacuation System (1).pdf` | `IM/A2A3/RR/sm/AAR/001` | `A23-EFE-MAT-E-0033` | crops/sheet-075.jpg#tile-298 |
| wrong reference | `EP-26082/EP-26082 INPUTS\IFC DOC\OneDrive_2024-08-17\Dwgs\IBA IFC DWGS\FA & EM (CENT ENT)\PDF\R1029-16-IBA-DWG-L01-FAS-1231-PDF [0].pdf` | `R1029-16-IBA-DWG-L01-FAS-1231` | `R1029-16-IBA-DWG-L01-FAS-1233` | crops/sheet-081.jpg#tile-321, crops/tb-038.jpg |
| wrong revision | `EP-26082/EP-26082 INPUTS\TENDER DWGS\MGM\04-21_MGM HOTEL\09 OF 96_MEP - MGM 2 ELECTRICAL ELV\R1029-08-CKR-DWG-L09-EML-1209-PDF [B].pdf` | `B` | `R0` | crops/sheet-083.jpg#tile-329, crops/tb-040.jpg |
| wrong reference | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201` | `R1029-CSCEC-MEP-SD-MGM1-L02-FAS-1202` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `02` | `R1` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/SD\FAVE\MGM1\AB\L8\R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf` | `AB` | `R1` | crops/sheet-086.jpg#tile-343, crops/tb-043.jpg |
| wrong revision | `EP-26082/SD\APP SD\FAVE\M1\R1029-CSCEC-MEP-SD-MGM1-B01-FAS-1199 rev.02.pdf` | `02` | `R1` | crops/sheet-087.jpg#tile-345, crops/tb-044.jpg |
| wrong reference | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01` | `R1029-CSCEC-MEP-SD-MGM1-L01-EML-1201` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `00` | `R1` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\MGM1\Rev.02\L8\R1029-CSCEC-MEP-SD-MGM1-L8-EML-1208-01.pdf` | `02` | `R0` | crops/sheet-087.jpg#tile-347, crops/tb-044.jpg |
| wrong reference | `EP-26082/EP-26082 SCAN DOC\R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf` | `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020` | `1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-Rev` | crops/sheet-091.jpg#tile-362 |

**Profile `promoted`** -- document outcomes (exclusive): bounded 36, complete 343, failed 1

| field | auto-accepted | correct | wrong | near (punctuation / suffix) | abstained (UR / held / no record) | unscorable (label absent, n/a, unknown, illegible) | precision of accepted | automatic recovery | review rate |
|---|---|---|---|---|---|---|---|---|---|
| reference | 97 | 73 | 24 | 1 | 203 | 69 | 75.3 % | 24.3 % | 67.7 % |
| revision | 87 | 57 | 30 | 0 | 177 | 105 | 65.5 % | 21.6 % | 67.0 % |
| decision | 83 | 83 | 0 | 0 | 39 | 247 | 100.0 % | 68.0 % | 32.0 % |
| system | 90 | 74 | 16 | 0 | 279 | 0 | 82.2 % | 20.1 % | 75.6 % |

Pages: total 6379, visited 1170, skipped by budget 5209, failed 0; OCR attempted on 225 pages, failed 0, left out by the OCR budget 0; stop reasons null 344, page_scan_limit 33, reply_search_limit 3.


By cohort:

| cohort | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| exploration | 192 | bounded 15, complete 176, failed 1 | 27 / 44 (102) | 17 / 41 (93) | 24 / 24 (27) | 31 / 44 |
| holdout | 108 | bounded 9, complete 99 | 13 / 18 (65) | 10 / 16 (57) | 14 / 14 (11) | 15 / 16 |
| regression | 80 | bounded 12, complete 68 | 33 / 35 (36) | 30 / 30 (27) | 45 / 45 (1) | 28 / 30 |

By project:

| project | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| 13777 | 40 | bounded 5, complete 35 | 1 / 2 (19) | 1 / 1 (13) | 4 / 4 (8) | 1 / 1 |
| 14119 | 6 | complete 6 | 0 / 0 (5) | 0 / 0 (4) | 0 / 0 (0) | 0 / 0 |
| 19977 | 32 | bounded 1, complete 31 | 4 / 6 (13) | 2 / 5 (7) | 0 / 0 (7) | 3 / 6 |
| 25091 | 50 | bounded 3, complete 47 | 6 / 13 (29) | 1 / 13 (27) | 12 / 12 (9) | 5 / 13 |
| 26082 | 55 | bounded 7, complete 47, failed 1 | 5 / 9 (33) | 3 / 9 (32) | 3 / 3 (3) | 8 / 9 |
| 26369 | 60 | bounded 4, complete 56 | 12 / 16 (39) | 9 / 15 (38) | 10 / 10 (3) | 14 / 15 |
| 27474 | 2 | complete 2 | 0 / 0 (2) | 0 / 0 (2) | 0 / 0 (0) | 0 / 0 |
| 29076 | 55 | bounded 4, complete 51 | 12 / 16 (27) | 11 / 14 (27) | 9 / 9 (8) | 15 / 16 |
| 30088 | 40 | bounded 7, complete 33 | 13 / 13 (21) | 12 / 12 (14) | 22 / 22 (1) | 11 / 12 |
| 30784 | 40 | bounded 5, complete 35 | 20 / 22 (15) | 18 / 18 (13) | 23 / 23 (0) | 17 / 18 |

By stratum (path rule):

| stratum (path rule) | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| approval_sample | 18 | bounded 2, complete 16 | 7 / 7 (11) | 5 / 6 (7) | 3 / 3 (7) | 6 / 6 |
| calc | 9 | bounded 1, complete 8 | 1 / 1 (2) | 0 / 1 (1) | 2 / 2 (0) | 0 / 1 |
| design_sheet | 17 | bounded 1, complete 16 | 0 / 1 (12) | 0 / 1 (8) | 0 / 0 (1) | 1 / 1 |
| drawing_ifc_input | 90 | bounded 7, complete 83 | 1 / 5 (81) | 4 / 5 (80) | 4 / 4 (0) | 4 / 5 |
| other | 50 | bounded 8, complete 42 | 0 / 1 (23) | 0 / 1 (18) | 2 / 2 (2) | 1 / 1 |
| reply | 34 | bounded 2, complete 31, failed 1 | 15 / 20 (8) | 14 / 15 (4) | 12 / 12 (7) | 13 / 13 |
| scan | 31 | bounded 2, complete 29 | 6 / 9 (18) | 3 / 5 (13) | 0 / 0 (9) | 3 / 9 |
| shop_drawing | 81 | bounded 1, complete 80 | 41 / 50 (28) | 29 / 50 (29) | 56 / 56 (12) | 44 / 51 |
| spec_compliance | 18 | bounded 5, complete 13 | 0 / 0 (13) | 0 / 0 (14) | 0 / 0 (0) | 0 / 0 |
| submittal | 22 | bounded 7, complete 15 | 2 / 3 (7) | 2 / 3 (3) | 4 / 4 (1) | 2 / 3 |
| transmittal_word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

By format:

| format | documents | outcomes | reference correct / accepted (abstained) | revision correct / accepted (abstained) | decision correct / accepted (abstained) | system correct / accepted |
|---|---|---|---|---|---|---|
| scan | 67 | bounded 5, complete 62 | 12 / 20 (31) | 8 / 14 (19) | 4 / 4 (13) | 16 / 21 |
| text | 303 | bounded 31, complete 271, failed 1 | 61 / 77 (172) | 49 / 73 (158) | 79 / 79 (26) | 58 / 69 |
| word | 10 | complete 10 | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 (0) | 0 / 0 |

Critical failures, profile `promoted`: 55 -- wrong reference 23, printed EP differs from the folder's EP (association to check) 1, wrong revision 30, reference differs in punctuation/suffix 1

| kind | document | expected (label) | actual (reader) | render |
|---|---|---|---|---|
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-3\Reply to MS Consultant Comments 31 (3).pdf` | `BBY006-GME-SDW-EL-LI-POD-P03-010031` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-007.jpg#tile-27 |
| wrong reference | `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\POD-1\Reply to MS Consultant Comments 31 (1).pdf` | `BBY006-GME-SDW-EL-LI-POD-P01-010029` | `BBY006-GME-SDW-EL-LI-ZZZ-ZZZ-010034` | crops/sheet-008.jpg#tile-28 |
| printed EP differs from the folder's EP (association to check) | `EP-30088/09. Scan Document\EP-30088 CBS Sam B ack 13.08.26.pdf` | `EP-30058` | `TR/204/26` | crops/sheet-019.jpg#tile-75 |
| wrong reference | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-FA-003-R3` | `25H-AAEM-SD-ELEC-FA-B1-003` | crops/sheet-022.jpg#tile-84 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\Fire Alarm\25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf` | `R3` | `R0` | crops/sheet-022.jpg#tile-84 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\30. 23rd Floor Emergency Lighting Layout\1. R0\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-030-R00 - Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-030-R0` | `25H-S202-NCC-SD-MEP-ELE-EM-30` | crops/sheet-028.jpg#tile-111 |
| wrong reference | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `25H-S202-NCC-SD-MEP-ELE-EM-23-02` | `25H-AAEM-SD-ELEC-EM` | crops/sheet-029.jpg#tile-112 |
| wrong revision | `EP-29076/06- Drawings\02- CBS\03- SD\SLD\REF\OneDrive_1_9-18-2026 (1)\23. 15th Floor Emergency Lighting Layout\3. R2\2. Commented\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B\25H-S202-NCC-SD-MEP-ELE-EM-23-02_Code B.pdf` | `02` | `R0` | crops/sheet-029.jpg#tile-112 |
| wrong revision | `EP-29076/06- Drawings\01- FA\03- SD\00- APPROVED\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B\25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | `00` | `R2` | crops/sheet-030.jpg#tile-118 |
| wrong reference | `EP-29076/01- EP-29076 - Scan\EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf` | `TR/0127/26` | `25H-S202-NCC-MAS-MEP` | crops/sheet-032.jpg#tile-124 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `AKA-BKG-ELE-B1-SD-PAVA-00010` | `AKA-BKG-ELE-B1-SD-PAVA-00008` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\B1\R2 B\AKA-BKG-ELE-B1-SD-PAVA-00010.pdf` | `02` | `R0` | crops/sheet-039.jpg#tile-154, crops/tb-021.jpg |
| reference differs in punctuation/suffix | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `AKA-DCC-ELE-FA-SD-000285-R2` | `AKA-DCC-ELE-FA-SD-000285` | crops/sheet-039.jpg#tile-155 |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-DCC-ELE-FA-SD-000285-R2-AKA-Shop drawing for Fire Alarm System Schematic Diagram.pdf` | `2` | `R0` | crops/sheet-039.jpg#tile-155 |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `AKA-BKG-ELE-UR-SD-CBS-00054` | `AKA-BKG-ELE-CBS-SD-FA-00052` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\UR\R1 B\AKA-BKG-ELE-UR-SD-CBS-00054.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-156, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00107.pdf` | `02` | `R0` | crops/sheet-040.jpg#tile-157, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R1 B\AKA-BKG-ELE-FA-SD-SCH-00102.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-158, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00055` | `AKA-BKG-ELE-LR-SD-PAVA-00053` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\PAVA\UR\R1 B\AKA-BKG-ELE-UR-SD-PAVA-00055.pdf` | `01` | `R0` | crops/sheet-040.jpg#tile-159, crops/tb-022.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\1F MZ\AKA-BKG-ELE-1M-SD-PAVA-00026.pdf` | `AKA-BKG-ELE-1M-SD-PAVA-00026` | `AKA-BKG-ELE-1M-SD-PAVA-00027` | crops/sheet-041.jpg#tile-160, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-161, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\FA\SCH\R2 C\AKA-BKG-ELE-FA-SD-SCH-00105.pdf` | `02` | `R0` | crops/sheet-041.jpg#tile-162, crops/tb-023.jpg |
| wrong revision | `EP-25091/EP-25091 SD\Final SD  received on 04-02-26 from BK Gulf\ELETRICAL\CBS\1M\R1 B\AKA-BKG-ELE-1M-SD-CBS-00028.pdf` | `01` | `R0` | crops/sheet-041.jpg#tile-163, crops/tb-023.jpg |
| wrong reference | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `AKA-BKG-ELE-UR-SD-PAVA-00051` | `AKA-BKG-ELE-LR-SD-PAVA-00052` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\PAVA\PAVA-UR\AKA-BKG-ELE-UR-SD-PAVA-00051-clouded.pdf` | `01` | `R0` | crops/sheet-042.jpg#tile-164, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 SD\FAS\SCH\AKA-BKG-ELE-FA-SD-SCH-00100.pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-165, crops/tb-024.jpg |
| wrong revision | `EP-25091/EP-25091 Calc\SPL\Atrium\AKA-BKG-ELE-GM-SD-PAVA-00016 (5).pdf` | `02` | `R0` | crops/sheet-042.jpg#tile-166, crops/tb-024.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\Proper Drawings\FIRE ALARM & EMERGENCY LIGHTING\PDF\SA-H2-BEST-FA-00201.pdf` | `SA-H2-BEST-FA-00201` | `SA-H2-BEST-VE-00G01` | crops/sheet-046.jpg#tile-182, crops/tb-025.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\General Drawings\ELECTRICAL\05. ICT\PDF\SA-H2-BEST-ICT-00100a.pdf` | `SA-H2-BEST-ICT-00100a` | `SA-H2-BEST-FA-00104` | crops/sheet-051.jpg#tile-200, crops/tb-030.jpg |
| wrong reference | `EP-26369/Inputs\AMANA - wetransfer_l-s-zip_2024-08-02_1335\L&S\L&S\Drawing\Proper Drawings\FIRE ALARM & EMERGENCY LIGHTING\PDF\SA-H2-BEST-FA-00102c.pdf` | `SA-H2-BEST-FA-00102c` | `SA-H2-BEST-VE-00G01` | crops/sheet-051.jpg#tile-203, crops/tb-030.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\R2\JAM-SD-FA-006-01.pdf` | `01` | `R2` | crops/sheet-055.jpg#tile-218, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -3\JAM-SD-FA-002.pdf` | `07` | `R10` | crops/sheet-055.jpg#tile-219, crops/tb-032.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-001 (LOW).pdf` | `05` | `R1` | crops/sheet-056.jpg#tile-222, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\JAM-SD-FA-001 (HIGH).pdf` | `04` | `R0` | crops/sheet-056.jpg#tile-223, crops/tb-033.jpg |
| wrong revision | `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\UPDATE DWGS\MRO UPDATE -4\JAM-SD-FA-004.pdf` | `06` | `R0` | crops/sheet-057.jpg#tile-224, crops/tb-033.jpg |
| wrong reference | `EP-26369/MS FAS\R1\MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf` | `EP-26369/SS/FA/101` | `RDJ183-RAQ-Naffco-MAT-008` | crops/sheet-057.jpg#tile-227 |
| wrong revision | `EP-26369/MS FAS\R1\MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf` | `01` | `R0` | crops/sheet-057.jpg#tile-227 |
| wrong reference | `EP-19977/EP-19977 Scan Doc\EP-19977 CBS MS R1 R&R.pdf` | `EBF-DCP-6374-VL-MAT-ELV-0023` | `EBF-DCP-6374-VL-MAT-ELE-0023` | crops/sheet-061.jpg#tile-243 |
| wrong revision | `EP-19977/EP-19977 Scan Doc\EP-19977 CBS MS R1 R&R.pdf` | `01` | `R0` | crops/sheet-061.jpg#tile-243 |
| wrong revision | `EP-19977/EP-19977 Scan Doc\EP-19977 FA MS R1 App.pdf` | `01` | `R0` | crops/sheet-062.jpg#tile-244 |
| wrong reference | `EP-19977/EP-19977 Commercial\EP-19977-Var1-Voltas.pdf` | `EP-19977-Var. 01` | `EBF-DCP-6374-VL-MAT-ELV-0003` | crops/sheet-066.jpg#tile-261 |
| wrong revision | `EP-19977/EP-19977 Commercial\EP-19977-Var1-Voltas.pdf` | `Var. 01` | `R0` | crops/sheet-066.jpg#tile-261 |
| wrong reference | `EP-13777/Approval Documents\AAR-001 Commented Material Submittal- Fire Alarm System & Voice Evacuation System (1).pdf` | `IM/A2A3/RR/sm/AAR/001` | `A23-EFE-MAT-E-0033` | crops/sheet-075.jpg#tile-298 |
| wrong reference | `EP-26082/EP-26082 INPUTS\IFC DOC\OneDrive_2024-08-17\Dwgs\IBA IFC DWGS\FA & EM (CENT ENT)\PDF\R1029-16-IBA-DWG-L01-FAS-1231-PDF [0].pdf` | `R1029-16-IBA-DWG-L01-FAS-1231` | `R1029-16-IBA-DWG-L01-FAS-1233` | crops/sheet-081.jpg#tile-321, crops/tb-038.jpg |
| wrong revision | `EP-26082/EP-26082 INPUTS\TENDER DWGS\MGM\04-21_MGM HOTEL\09 OF 96_MEP - MGM 2 ELECTRICAL ELV\R1029-08-CKR-DWG-L09-EML-1209-PDF [B].pdf` | `B` | `R0` | crops/sheet-083.jpg#tile-329, crops/tb-040.jpg |
| wrong reference | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201` | `R1029-CSCEC-MEP-SD-MGM1-L02-FAS-1202` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/BOQ\SD\FAVE\M1\APP\R1029-CSCEC-MEP-SD-MGM1-L01-FAS-1201.pdf` | `02` | `R1` | crops/sheet-085.jpg#tile-339, crops/tb-042.jpg |
| wrong revision | `EP-26082/SD\FAVE\MGM1\AB\L8\R1029-CSCEC-MEP-SD-MGM1-L08-FAS-1208.pdf` | `AB` | `R1` | crops/sheet-086.jpg#tile-343, crops/tb-043.jpg |
| wrong revision | `EP-26082/SD\APP SD\FAVE\M1\R1029-CSCEC-MEP-SD-MGM1-B01-FAS-1199 rev.02.pdf` | `02` | `R1` | crops/sheet-087.jpg#tile-345, crops/tb-044.jpg |
| wrong reference | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01` | `R1029-CSCEC-MEP-SD-MGM1-L01-EML-1201` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\P & B\Rev.00\GF\R1029-CSCEC-MEP-SD-P&B-GFL-EML-1220-01.pdf` | `00` | `R1` | crops/sheet-087.jpg#tile-346, crops/tb-044.jpg |
| wrong revision | `EP-26082/SD\CBS\MGM1\Rev.02\L8\R1029-CSCEC-MEP-SD-MGM1-L8-EML-1208-01.pdf` | `02` | `R0` | crops/sheet-087.jpg#tile-347, crops/tb-044.jpg |
| wrong reference | `EP-26082/EP-26082 SCAN DOC\R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf` | `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020` | `1029-CSM-CO-ELV-EL-MAR-PJW-ZZZ-Rev` | crops/sheet-091.jpg#tile-362 |

### Random correct controls (candidate B, default profile; seed 20260928)

| document | cohort | reference | revision | decision | render |
|---|---|---|---|---|---|
| `EP-30088/10. SD\recieved\Fire alarm layout\Received\R01\ICC-DLRC-SPM-SD-MEP-FA-0042-01-HC FLOOR FIRE ALARM LAYOUT_ICC-DLRC-SPM-SD-MEP-FA-0042-01.pdf` | regression | `ICC-DLRC-SPM-SD-MEP-FA-0042` | `R1` | `ANN` | crops/sheet-011.jpg#tile-43 |
| `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R00\10. L02-1st Mechanical Floor\BBY006-GME-SDW-EL-LI-ZZZ-L02-010033.pdf` | regression | `BBY006-GME-SDW-EL-LI-ZZZ-L02-010033` | `R0` | `UR` | crops/sheet-001.jpg#tile-3, crops/tb-001.jpg |
| `EP-30784/04- Drawings\08-Shop Drawing\2.EML\approved\BBY006-GME-SDW-EL-LI-ZZZ-L57-010041 Shop Drawing L57-4th Mechanical Floor Plan Emergency Lighting Layout.pdf` | regression | `BBY006-GME-SDW-EL-LI-ZZZ-L57-010041` | `R0` | `ANN` | crops/sheet-005.jpg#tile-18 |
| `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R01\L58\BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf` | regression | `BBY006-GME-SDW-EL-LI-ZZZ-L58-010042` | `R1` | `UR` | crops/sheet-003.jpg#tile-8, crops/tb-002.jpg |
| `EP-29076/06- Drawings\01- FA\03- SD\25H-AAEM-SD-ELEC-FA-152 -L 64\R1\25H-AAEM-SD-ELEC-FA-64F-53A-R00.pdf` | exploration | `25H-AAEM-SD-ELEC-FA-64F-053A` | `R1` | `UR` | crops/sheet-021.jpg#tile-81, crops/tb-009.jpg |
| `EP-30784/08- approval\MS\FA\BBY006-GME-MAS-EL-FA-0001 Material Submittal for Fire Alarm, Fire Telephone & Voice Evacuation System.pdf` | regression | `BBY006-GME-MAS-EL-FA-0001` | `R0` | `ANN` | crops/sheet-006.jpg#tile-21 |
| `EP-30784/04- Drawings\08-Shop Drawing\2.EML\R00\21. L58(TYP 3A) Floor Plan\BBY006-GME-SDW-EL-LI-ZZZ-L58-010042.pdf` | regression | `BBY006-GME-SDW-EL-LI-ZZZ-L58-010042` | `R0` | `UR` | crops/sheet-005.jpg#tile-16, crops/tb-003.jpg |
| `EP-30088/10. SD\recieved\Fire alarm layout\Received\R01\ICC-DLRC-SPM-SD-MEP-FA-0128-00-COMMENTED-C.pdf` | regression | `ICC-DLRC-SPM-SD-MEP-FA-0128` | `R0` | `rejected` | crops/sheet-014.jpg#tile-52 |
| `EP-26369/SHOP DRAWINGS\MRO SHOP DWGS\JAM-SD-FA-001.pdf` | holdout | `JAM-SD-FA-001` | `R0` | `UR` | crops/sheet-056.jpg#tile-220, crops/tb-032.jpg |
| `EP-30088/04. Drawings\SD\recieved\TransferNow-20260908BGEp3fee\Emergency Lighting Layout\Received\ICC-DLRC-SPM-SD-MEP-0080-00-COMMENTED-C.pdf` | regression | `ICC-DLRC-SPM-SD-MEP-0080` | `R0` | `rejected` | crops/sheet-015.jpg#tile-57 |
| `EP-30784/04- Drawings\08-Shop Drawing\1.FAVE\R1\rejected\BBY006-GME-SDW-FP-FA-BSM-B02-010027 Shop Drawing for Basement-2 Floor Plan - Fire Alarm Layout.pdf` | regression | `BBY006-GME-SDW-FP-FA-BSM-B02-010027` | `R0` | `rejected` | crops/sheet-004.jpg#tile-15 |
| `EP-30088/04. Drawings\SD\recieved\TransferNow-20260908BGEp3fee\Fire alarm layout\Received\R01\ICC-DLRC-SPM-SD-MEP-FA-0042-01-HC FLOOR FIRE ALARM LAYOUT_ICC-DLRC-SPM-SD-MEP-FA-0042-01.pdf` | regression | `ICC-DLRC-SPM-SD-MEP-FA-0042` | `R1` | `ANN` | crops/sheet-011.jpg#tile-43 |