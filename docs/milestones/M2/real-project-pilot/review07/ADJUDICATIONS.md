# M2 Review 07: source adjudication of changed critical findings

Every finding that changed or appeared under evaluator .5/.6 was inspected against the staged source before any error count was asserted.
The source was read through the text layer, the OCR text, or a rendered crop (`evidence/adjudication_crops/`).
The Golden labels are **not** changed here: a disputed label goes to the human-review packet.

Categories:

| Category | Meaning |
|---|---|
| `ai_correct_label_disputed` | the AI value is printed on the page; the label is likely incomplete |
| `two_own_identities` | the page prints two identities that are both its own; the label chose the other |
| `label_gap_unlabelled_own` | the page prints its own identity, but the page labels list no component there |
| `literal_ocr_error` | a real misread of the printed characters (a raw-observation error) |
| `referenced_as_own` | a number the page references was taken as its own identity (a raw-observation error) |

| # | Run | Document | Page | Field | Value read | Label | Category | Evidence | Resolution |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AI-EV1 | …dows   -Final Design Revision Arch  - Approved/REQ-2387569  - BP.pdf | 1 | identity | `B2312982` | REQ-2387569 | `two_own_identities` | rendered page: Dubai Development Authority BUILDING PERMIT, 'Permit Number B2312982' in the header table; footer 'REQ-2387569-2' (the request reference); the file is named after the request | disputed truth -> human review; not counted as an AI false acceptance until settled |
| 2 | AI-EV1, AI-EV2 | …FA/03- SD/Fire Alarm/25H-S202-NCC-SD-MEP-ELE-FA-003-R03 - Code B.pdf | 3 | decision | `ANN` | n/a (no decision on page 3) | `ai_correct_label_disputed` | rendered crop of the blind read region: blue consultant stamp 'CODE B APPROVED AS NOTED' ticked and signed on page 3 (sheet 02 of 02); the engineer's-comments block beside it is unmarked | label likely incomplete -> human review |
| 3 | det .8 | EP-30784/01- EP-30784 Scan/EP-30784 EML Design.pdf | 1 | identity | `TEP-30784` | EP-30784 | `literal_ocr_error` | OCR of the labelled 'Doc No.' line adds a leading T | raw observation error (observed, not accepted) |
| 4 | det .8 | EP-14119/EP-14119 Commercial/EP-14119 LPO.pdf | 1 | identity | `LPOD-1856000229` | LPO/1050000159 | `literal_ocr_error` | OCR of the LPO number: '/' read as 'D' and digits misread | raw observation error |
| 5 | det .8 | EP-19977/EP-19977 Commercial/EP-19977 CBS Quotation.pdf | 1 | identity | `D1902-FC-DWG-EM-B1200` | EP-19977-R1 | `referenced_as_own` | the quotation's 'Ref' line quotes the consultant drawing it prices | raw observation error |
| 6 | det .8 | EP-19977/EP-19977 Commercial/EP-19977 FA Quotation R4.pdf | 1 | identity | `D1902-FC-DWG-EF-B1200 & ...` | EP - 19977 - R4-B0 | `referenced_as_own` | as above | raw observation error |
| 7 | det .8 | …77/*/TAV-TN-009782 (1).pdf, TAV-TN-000731.pdf, TAV-TN-011156 (1).pdf | 1 | identity | `K&A-WTRAN-017671 / -000913 / -020525` | TAVC-TRANSMIT-009782 / -000731 / -011156 | `two_own_identities` | text layer prints both 'TAVC-TRANSMIT-009782' and 'K&A-WTRAN-017671' (the consultant's and the contractor's transmittal numbers) | disputed truth -> human review (3 cases) |
| 8 | det .8 | EP-26369/MS FAS/R1/MS FAS SOFTCOPY (TIM AEROSPACE) R1.pdf | 1 | identity+revision | `EP-26369/SS/FA/101, 01` | page 1 labelled no component (components on pages 4-5) | `label_gap_unlabelled_own` | text layer page 1: 'EP-26369/SS/FA/101', 'Revision' (the company's own cover) | label gap -> human review |
| 9 | det .8 | EP-30784/03- MS/03- FRC/03- TIANJIE/BBY006_1.PDF | 3 | identity+revision | `EP-30627/SS/EML/ 1293, 00` | page 3 labelled no component | `label_gap_unlabelled_own` | text layer page 3: 'EP-30627/SS/EML/ 1293', 'Revision' -- a cover of another project number filed in this package | label gap -> human review |
| 10 | det .8 | EP-29076/*/Minutes of Weekly MEP Meeting No. 020 - Final Issuance.pdf | 1 | identity | `10789-CSCEC-OUT-L0` | L0749 | `two_own_identities` | OCR: the minutes carry the contractor's outgoing letter number and the meeting letter number | disputed truth -> human review |
| 11 | det .8 (parser drawing_sheet observations, also in Candidate C) | EP-26082 BELLAGIO / MGM / landscape sheets (9 cases) | 1 | identity | `R1029-05-BSB-DWG-ALL-ARC-1282, A-DWG-TYP-GRO-INT-1102-01, ...` | the sheet's own number | `referenced_as_own` | untracked-discipline sheet observations carry a referenced drawing number from the sheet's reference table / a part number | raw observation error (pre-existing since Candidate C) |
| 12 | det .8 holdout | EP-8430/Approval and Comments/PAVA MS Comments.pdf | 1 | identity | `ICDS-DOC-01943` | D15015-0200S-FS-EL-MS-0022 | `two_own_identities` | the Dar review form prints its own document number (OCR 'ICDS-DOC-01943', leading I probably noise) and the MS it reviews; the label keys the component to the reviewed MS | role ambiguity (own vs target) -> human review; the literal's leading 'I' also unverified |
| 13 | det .8 holdout | …-8430/EP-8430 PAVA MS/Rev. 0/Test Certificates/BOSCH PAVA Letter.pdf | 1 | identity | `BSS/AE/ALARABIA/170315-047` | no component | `label_gap_unlabelled_own` | the Bosch letter's own reference; labelled as a no-record page | label gap -> human review |

## Outcome

1. **AI-introduced errors.** Of the 2 cases evaluator .6 reports for Review 06 AI-EV1 (1 for AI-EV2), **none is a confirmed AI false acceptance**:
   - the building permit prints both `B2312982` (Permit Number) and `REQ-2387569-2` (the request reference);
   - page 3 of `FA-003-R03 - Code B` carries a signed consultant "CODE B APPROVED AS NOTED" stamp.

   Both are disputed truth, pending human review. Policy .2 still validates the permit identity (it is printed in the read region) and holds the Code B decision as a candidate.
2. **Wrong raw observations** (21 on the pilot, 2 on the holdout; identity and revision counted separately):

   | Category | Count | Kind |
   |---|---|---|
   | `literal_ocr_error` | 2 | real raw-observation error |
   | `referenced_as_own` | 11 | real raw-observation error; includes the 9 pre-existing drawing-sheet observations |
   | `two_own_identities` | 5 | label dispute |
   | `label_gap_unlabelled_own` | 5 | label gap |

   The real errors are held raw evidence, never register keys.
3. **Register critical** under the final candidate is **0** in both profiles. The two pre-existing flagged-reference cases are now held as pending evidence (EXTRACTION-SAFETY).
