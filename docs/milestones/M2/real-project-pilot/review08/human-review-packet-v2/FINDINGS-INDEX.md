# Findings index: the 13 Review 07 source findings

**Status: prepared by AI, not reviewed.** Each group links the packet rows and page images it concerns. The Review 07 table stays unchanged in `../../review07/ADJUDICATIONS.md`; the one correction is noted under F10.

**8 groups (10 items) need a decision**: a fact or an association that the source leaves open for this packet. The other 5 groups (13 items) need only a confirmation of the label literal. Until a person settles them, none of these is counted as an AI success or as a confirmed error.

| Group | Status | Category | Field | Read | Label | Items (page image) |
|---|---|---|---|---|---|---|
| F01 | **DECIDE** | two_own_identities | identity | `B2312982` | REQ-2387569 | [C0073](../../review07/human-review-packet/pages/bbe5a2877086829d-p1.jpg) |
| F02 | **DECIDE** | ai_correct_label_disputed | decision | `ANN` | n/a (no decision on page 3) | [C0083](../../review07/human-review-packet/pages/13041b58155be258-p3.jpg) |
| F03 | confirm | literal_ocr_error | identity | `TEP-30784` | EP-30784 | [C0049](../../review07/human-review-packet/pages/241c5652f6d3ccc8-p1.jpg) |
| F04 | confirm | literal_ocr_error | identity | `LPOD-1856000229` | LPO/1050000159 | [C0261](../../review07/human-review-packet/pages/46e16cad3602ed1a-p1.jpg) |
| F05 | confirm | referenced_as_own | identity | `D1902-FC-DWG-EM-B1200` | EP-19977-R1 | [C0191](../../review07/human-review-packet/pages/ea9d1519b8af2f08-p1.jpg) |
| F06 | confirm | referenced_as_own | identity | `D1902-FC-DWG-EF-B1200 & ...` | EP - 19977 - R4-B0 | [C0193](../../review07/human-review-packet/pages/3679b3cbd02b4194-p1.jpg) |
| F07 | **DECIDE** | two_own_identities | identity | `K&A-WTRAN-017671 / -000913 / -020525` | TAVC-TRANSMIT-009782 / -000731 / -011156 | [C0202](../../review07/human-review-packet/pages/78571a79da44dd93-p1.jpg), [C0211](../../review07/human-review-packet/pages/c2b54cc0ebedea1c-p1.jpg), [C0220](../../review07/human-review-packet/pages/91c4d1aec0214727-p1.jpg) |
| F08 | **DECIDE** | label_gap_unlabelled_own | identity+revision | `EP-26369/SS/FA/101, 01` | page 1 labelled no component (components on pages 4-5) | [C0159](../../review07/human-review-packet/pages/733b0febc0ba007e-p1.jpg) |
| F09 | **DECIDE** | label_gap_unlabelled_own | identity+revision | `EP-30627/SS/EML/ 1293, 00` | page 3 labelled no component | [C0034](../../review07/human-review-packet/pages/21d2d84830ad11c6-p3.jpg) |
| F10 | **DECIDE** | two_own_identities | identity | `10789-CSCEC-OUT-L0` | L0749 | [C0245](../../review07/human-review-packet/pages/b28708dbf3c90abf-p1.jpg) |
| F11 | confirm | referenced_as_own | identity | `R1029-05-BSB-DWG-ALL-ARC-1282, A-DWG-TYP-GRO-INT` | the sheet's own number | [C0221](../../review07/human-review-packet/pages/0650252ca9aae3b2-p1.jpg), [C0222](../../review07/human-review-packet/pages/d513641371a26448-p1.jpg), [C0224](../../review07/human-review-packet/pages/20ec1badbe8eaeb7-p1.jpg), [C0225](../../review07/human-review-packet/pages/b73c4df87904e83e-p1.jpg), [C0226](../../review07/human-review-packet/pages/3e4e89ffa0c633c4-p1.jpg), [C0227](../../review07/human-review-packet/pages/11b5d15c0fbb99ba-p1.jpg), [C0229](../../review07/human-review-packet/pages/4b2e4da6f52cddb2-p1.jpg), [C0230](../../review07/human-review-packet/pages/8156d02ce8d1141c-p1.jpg), [C0244](../../review07/human-review-packet/pages/8f171daed83c545e-p9.jpg) |
| F12 | **DECIDE** | two_own_identities | identity | `ICDS-DOC-01943` | D15015-0200S-FS-EL-MS-0022 | [C0282](../../review07/human-review-packet/pages/8106a2d77584615c-p1.jpg) |
| F13 | **DECIDE** | label_gap_unlabelled_own | identity | `BSS/AE/ALARABIA/170315-047` | no component | [C0283](../../review07/human-review-packet/pages/44665c3b5543786e-p1.jpg) |

## What each group asks

- **F01** (1 item, EP-30088, pilot). **Decide**: Which printed identity is this document's own for evaluation: the building permit number (B2312982) or the request reference (REQ-2387569)? Record both with their printed labels and roles. Review 07 resolution: disputed truth -> human review; not counted as an AI false acceptance until settled.
- **F02** (1 item, EP-29076, pilot). **Decide**: Does the ticked, signed CODE B stamp on page 3 (sheet 02 of 02) give this component's decision? If so the label is incomplete. Review 07 resolution: label likely incomplete -> human review.
- **F03** (1 item, EP-30784, pilot). Confirm: Confirm the printed Doc No. literal (label EP-30784). The OCR reading TEP-30784 was observed, never accepted. Review 07 resolution: raw observation error (observed, not accepted).
- **F04** (1 item, EP-14119, pilot). Confirm: Confirm the printed LPO number literal (label LPO/1050000159). The OCR reading was observed, never accepted. Review 07 resolution: raw observation error.
- **F05** (1 item, EP-19977, pilot). Confirm: Confirm the quotation's own reference (label EP-19977-R1); the Ref-line drawing is a referenced (priced) drawing. Review 07 resolution: raw observation error.
- **F06** (1 item, EP-19977, pilot). Confirm: Confirm the quotation's own reference (label EP - 19977 - R4-B0); the Ref-line drawings are referenced (priced) drawings. Review 07 resolution: raw observation error.
- **F07** (3 items, EP-13777, pilot). **Decide**: Each transmittal prints the consultant's mail number (TAVC-TRANSMIT-...) and the contractor's reference number (K&A-WTRAN-...). Record both; say which one the register evaluates, or that both are the same document's own numbers. Review 07 resolution: disputed truth -> human review (3 cases).
- **F08** (1 item, EP-26369, pilot). **Decide**: Page 1 is the company's own cover (EP-26369/SS/FA/101, Revision). Is it a component of this document? The label has none on page 1. Review 07 resolution: label gap -> human review.
- **F09** (1 item, EP-30784, pilot). **Decide**: Page 3 is a cover carrying another project's number (EP-30627/SS/EML/ 1293). Is it part of this document (association), and is it a component? Review 07 resolution: label gap -> human review.
- **F10** (1 item, EP-26082, pilot). **Decide**: The minutes print the contractor's outgoing letter number (10789-CSCEC-OUT-L0...) and the meeting letter number (L0749). Which is the minutes' own identity for evaluation? *Correction:* Review 07 recorded the project as EP-29076; the file is in EP-26082 (GOLDEN-LABELS.json, packet item C0245, the det .8 output). Review 07 resolution: disputed truth -> human review.
- **F11** (9 items, EP-26082, pilot). Confirm: Confirm each sheet's own number; the numbers read came from the sheet's reference table or a part number (pre-existing since Candidate C). Review 07 resolution: raw observation error (pre-existing since Candidate C).
- **F12** (1 item, EP-8430, holdout). **Decide**: The Dar review form prints its own document number (OCR ICDS-DOC-01943; the leading I is unverified) and the method statement it reviews (D15015-0200S-FS-EL-MS-0022). Which is the component's own identity, and what is the exact literal? Review 07 resolution: role ambiguity (own vs target) -> human review; the literal's leading 'I' also unverified.
- **F13** (1 item, EP-8430, holdout). **Decide**: The Bosch letter prints its own reference BSS/AE/ALARABIA/170315-047. Is the letter a component (it is labelled a no-record page)? Review 07 resolution: label gap -> human review.

Each item also carries its group ID in the `finding_group` column of `COMPONENT-ITEMS-v2.csv`; its printed identities are in `IDENTITIES-v2.csv`.
