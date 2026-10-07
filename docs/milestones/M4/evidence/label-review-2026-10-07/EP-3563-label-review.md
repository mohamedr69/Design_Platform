# R32 label review — EP-3563 (raw reviewer report, filed verbatim by the orchestrator)

Filed 7 October 2026. Role: ep-label-reviewer, run as a general-purpose Claude Opus agent with the role's definition inlined (see docs/SESSION-LOG-2026-10-07-windows.md row 1a). Read-only; the agent wrote nothing outside the scratchpad. Label set `r32-labels-reviewed-2` (sha256 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6); staged pages under C:\t\r2x\r32-stage. This is an AI review, not a human sign-off (AI-ACCURACY-POLICY amendment R32-01); it does not close acceptance-matrix gate G9.

---

## Label review report: EP-3563, cohort R32 (fresh M2 validation cohort, unified M4)

**1. Header**
- **Cohort:** frozen R32 fresh M2 validation cohort (unified M4). Project: **EP-3563** ("THE FIRST AVENUE MALL & HOTEL", Plot 6742010, consultant job D14-22, as printed on every page).
- **Label file:** `r32-labels-reviewed-2`, G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json. sha256 checked: 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6. **MATCH.**
- **Conventions:** packet-inputs/LABEL-CONVENTIONS-R32.md, read in full. Fields are judged on the frozen text. Where the label relies on a later amendment recorded in the label file, this report says so.
- **Source hashes:** every staged PDF was checked against SOURCE-MANIFEST.json `staged_sha256`, and every render, text layer and crop used was checked against EVIDENCE-INDEX.json. The label's `staged_sha256` also equals the manifest for all 12 documents.

| F-id | PDF | Renders (pages) | Crops |
|---|---|---|---|
| F001 | OK | OK (p1, p2) | OK (2) |
| F010 | OK | OK (p1) | OK (2) |
| F012 | OK | OK (p1) | OK (2) |
| F014 | OK | OK (p1–p4) | OK (8) |
| F016 | OK | OK (p1–p4) | OK (8) |
| F017 | OK | OK (p1) | OK (3) |
| F018 | OK | OK (p1) | OK (2) |
| F019 | OK | OK (p1) | OK (7) |
| F022 | OK | OK (p1) | OK (3) |
| F026 | OK | OK (p1) | OK (2) |
| F031 | OK | OK (p1–p4) | OK (3) |
| F033 | OK | OK (p1) | OK (2) |

- **Extra crops:** I made a few higher-resolution crops myself with pymupdf from the hash-checked PDFs, written only to the scratchpad (F010 stamp, F012 and F019 revision tables, F031 p3 header).
- **Reviewer:** ep-label-reviewer role (Claude Opus agent), independent of the drafting and reviewing agents of the label set.
- **Date:** 7 October 2026.
- **Method:** I read every page before looking at the label's values. I did not use file or folder names as evidence.

**2. Per-item table**
Format: labelled → observed. "pres" = present, "abs" = absent, "NDA" = no_decision_area. The scored decision rows are all `excluded_from_scoring: false`. Only F019 p1 revision is labelled excluded.

| Doc | Pg | Field | Labelled | Observed | Verdict | Reason |
|---|---|---|---|---|---|---|
| F001 | 1 | identity | pres "MAT – 116" (Submittal No.), resolved | pres "MAT – 116" (en dash, spaces) | AGREE | Labelled as the document's own number. FAM-PIV-BLD-MAT-ELE-116-02 is the transmittal-table reference and correctly sits in other_identities. |
| F001 | 1 | revision | pres "02" (Revision:) | pres "02" | AGREE | Header cell "Revision: 02". The footer "Rev.0" is the form template's revision. |
| F001 | 1 | decision | abs, NDA | abs, NDA | AGREE | Only the contractor's submission ticks and received/distribution stamps. |
| F001 | 2 | identity | abs | abs | AGREE | No own number. Footer form "DAE/F016A" only. |
| F001 | 2 | revision | abs | abs | AGREE | Footer "Material Submittal No. Rev.0" is the template. |
| F001 | 2 | decision | pres "Approved as noted / Resubmit", class approved as noted, consultant, resolved, outside_title_block | pres, red tick on "Approved as noted / Resubmit" | AGREE (class caveat C1) | Engineer's block, initialled 22.3.16. The "Approved" tick in Transmittal B is the contractor's, correctly not used. |
| F010 | 1 | identity | pres "FAM-PIV-MAH-SPD-FAS-2633-002C" (DWG. NO:) | same | AGREE | Title block. |
| F010 | 1 | revision | pres "02" (Rev. no.) | "02" | AGREE | Revision table 00/01/02 agrees. |
| F010 | 1 | decision | pres "APPROVED AS NOTED", approved as noted, in_title_block | pres "APPROVED AS NOTED" | AGREE | At 600 dpi, a red tick vertex sits at the APPROVED AS NOTED box, with the stroke running on from "25:4:16 N.H". No other box is marked. |
| F012 | 1 | identity | pres "FAM-PIV-MAH-SPD-FA-2633-007 A" | same, space before A | AGREE | |
| F012 | 1 | revision | pres "01" | "01" | AGREE | See hygiene item H1 for an error in the value_note. |
| F012 | 1 | decision | pres "APPROVED AS NOTED", outside_title_block | same | AGREE | Clear red tick. The stamp is in the sheet margin beyond the frame. |
| F014 | 1–4 | identity | pres "103" / "103A" / "103B" / "103C" (DRAWING NO.; DISCIPLINE "FP" split, noted) | same | AGREE ×4 | Split-cell rule, section 3. |
| F014 | 1–4 | revision | pres "01" (REVISION) | "01" | AGREE ×4 | |
| F014 | 1–4 | decision | pres "مخططات معتمدة", approved, Civil Defence, resolved, outside_title_block | pres, Civil Defence approved-plans stamp (253708-37-1, 15/01/17) on each page | AGREE ×4 | Authority decision. The yellow "APPROVED" and "FOR INFORMATION ONLY" boxes are the issuer's sheet status. Location is borderline (H4). |
| F016 | 1–4 | identity | pres "102" / "102A" / "102B" / "102C" (DISCIPLINE "FA" split) | same | AGREE ×4 | |
| F016 | 1–4 | revision | pres "01" | "01" | AGREE ×4 | |
| F016 | 1–4 | decision | pres "مخططات معتمدة", approved, Civil Defence | same stamp on each page | AGREE ×4 | As F014 (H4). |
| F017 | 1 | identity | pres "FAM-PIV-MAH-SPD-CBS-2633-007A" | same | AGREE | |
| F017 | 1 | revision | pres "00" | "00" | AGREE | Table row 00 28-05-16 agrees. |
| F017 | 1 | decision | pres "APPROVED AS NOTED / RESUBMIT", approved as noted, in_title_block | tick on "APPROVED AS NOTED / RESUBMIT" | AGREE (C1) | The stamp straddles the strip border but is mostly inside. |
| F018 | 1 | identity | pres "FAM-PIV-MAH-SPD-CBS-2633-002F" | same | AGREE | |
| F018 | 1 | revision | pres "01" | "01" | AGREE | Table 00 05-03-16 and 01 09-04-16 agree. |
| F018 | 1 | decision | pres "APPROVED AS NOTED", in_title_block | tick on APPROVED AS NOTED | AGREE | |
| F019 | 1 | identity | pres "FAM-PIV-MAH-SPD-FA-2633-007" | same | AGREE | Rotated sheet; upright crop used. |
| F019 | 1 | revision | **ambiguous, excluded_from_scoring** (D-005) | **pres "00"** (Rev. no. cell), conflicting with table | **DISAGREE** (conservative, not a false accept) | The page prints "Rev. no. 00" while the table's top row reads "01 09-05-16 AS PER CONSULTANT COMMENTS", the same date as the title block "09-05-16". Frozen section 4 makes the cell the primary source, so the frozen text gives present "00". The label's ambiguous/excluded reading rests on amendment D-005 to section 4. |
| F019 | 1 | decision | pres "APPROVED AS NOTED", in_title_block | faint stamp; red arrow ends at the APPROVED AS NOTED box | AGREE | Faint but legible. |
| F022 | 1 | identity | pres "FAM-PIV-MAH-SPD-CBS-2633-004C" | same | AGREE | |
| F022 | 1 | revision | pres "00" | "00" | AGREE | |
| F022 | 1 | decision | pres "APPROVED AS NOTED / RESUBMIT", in_title_block | tick at that box (7.8.16) | AGREE (C1) | |
| F026 | 1 | identity | pres "FAM-PIV-MAH-SPD-CBS-2633-006" | same | AGREE | |
| F026 | 1 | revision | pres "00" | "00" | AGREE | |
| F026 | 1 | decision | pres "APPROVED AS NOTED / RESUBMIT", outside_title_block | tick at that box (31.7.16); stamp in the margin | AGREE (C1) | |
| F031 | 3 | identity | pres "MAT – 116" (Submittal No.:), resolved | same | AGREE | Comments Resolution Sheet. "Document No. SS-PQP-124-F30" (issue 28/8/2015, Rev 0) is a form-control number and correctly sits in other_identities. |
| F031 | 3 | revision | pres "02" (Rev. :) | "Rev. : 02" | AGREE | The form block's "Rev: 0" is the template's. |
| F031 | 3 | decision | abs, NDA | abs, NDA | AGREE | The consultant's red notes ("Provide us with even expired certificate…") are comments, not a decision. |
| F031 | 4 | identity / revision / decision | abs / abs / abs NDA | same | AGREE ×3 | Page 2 of 3 of the sheet; no header. |
| F031 | 1–2 | all 6 rows | identical to F001 p1–p2 | identical | AGREE ×6 (not counted) | Count-once alias of F001. The renders are pixel-identical (I verified this). |
| F033 | 1 | identity | pres "FAM-PIV-MAH-SPD-FA-2633-004 A" | same, with space | AGREE | |
| F033 | 1 | revision | pres "01" | "01" | AGREE | Table 00 05-03-16 and 01 07-05-16 agree. |
| F033 | 1 | decision | pres "APPROVED AS NOTED / RESUBMIT", in_title_block | tick at that box (17.8.16) | AGREE (C1) | |

- **Caveat C1 (decision class):** the option "Approved as noted / Resubmit" carries both an approval and a resubmit marker. Frozen section 5 lists "resubmit" under revise and resubmit, so the class `approved as noted` follows the label file's amendment (d1), not the frozen text alone. State, literal and association agree on all these rows.
- **other_identities:** I found no case where the label put the number I consider the identity into other_identities.

**3. Totals for EP-3563**
Counting unit: page rows, with F031 pages 1–2 counted once under F001. That gives 20 counted rows per field.

| Field | Reviewed | Agree | Disagree | Cannot determine | Present labelled |
|---|---|---|---|---|---|
| Identity | 20 | 20 | 0 | 0 | 18 |
| Revision | 20 | 19 | 1 (F019 p1) | 0 | 17 |
| Decision | 20 | 20 | 0 | 0 | 17 (of which 5 depend on C1 for class) |

- **Status:** all three fields are **NOT ESTABLISHED** for this project.
  - The conventions' unit is the staged document, and the count-once units here number 11 (F001+F031, F010, F012, F014, F016, F017, F018, F019, F022, F026, F033), which is below 12.
  - Documents carrying each field after review: identity 11, revision 10 (F019 not carried), decision 11.
  - The 20 page rows meet 12, but they are not independent: the four F014 sheets and the four F016 sheets each share one authority stamp.

**4. Critical false accepts**
None found. No wrong value is labelled as a resolved present value. Every page shows The First Avenue Mall & Hotel / Plot 6742010 / D14-22, so I found no document of another project.

**5. Hygiene findings**
- **H1:** F012 p1 revision value_note says "00 05-05-16 ISSUED FOR APPROVAL". The page prints "00 05-03-16 ISSUED FOR APPROVAL". This is a note-only error; the scored value "01" is unaffected.
- **H2:** F031 is not byte-identical to F001 (staged sha256 4f1ffdfc… vs d701f99d…). Count-once rests on amendment (c)(ii), not frozen section 1, which covers byte-identical files only. Pages 1–2 are pixel-identical. Pages 3–4 are extra pages with the same MAT – 116 / 02 values. Page 5 is out of scope.
- **H3:** F019 p1 has an internal page conflict (cell "00" against table row "01" with the title-block date) and needs a human ruling (see section 2).
- **H4:** On F014 and F016 p1–4, the Civil Defence stamp covers the top of the right-hand title strip and the adjacent drawing area, roughly half in each. `outside_title_block` is borderline under ruling (m) but not unreasonable.
- **H5:** Optional. Referenced drawing numbers are not recorded in other_identities: F010 "FAM-PIV-MAH-SPD-FAS-2633-002 A & B" and "…-002 D", and the IFC refs "FA/102" / "FA/107".
- **Other hygiene:** no missing page references, regions or evidence; no duplicated items; no label points at the wrong document. All scans are readable. F010, F012 and F019 stamps are faint or low-resolution but legible.

**6. Human sign-off**
This is an AI review, not a human sign-off. A human reviewer must still confirm three things:
- F019 p1 revision: "00" from the cell, or ambiguous.
- Whether the decision class for "Approved as noted / Resubmit" is `approved as noted` (amendment d1) or `revise and resubmit`.
- Whether F031 counts once with F001. It is a content duplicate, not a byte duplicate.

They must also sign off the F010 decision mark, which is a stroke continuing from the reviewer's initials.
