# R32 label review — EP-26687 (raw reviewer report, filed verbatim by the orchestrator)

Filed 7 October 2026. Role: ep-label-reviewer, run as a general-purpose Claude Opus agent with the role's definition inlined (the project roster was not loadable in this session; see docs/SESSION-LOG-2026-10-07-windows.md row 1a). Read-only; the agent wrote nothing. Label set `r32-labels-reviewed-2` (sha256 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6); staged pages under C:\t\r2x\r32-stage. This is an AI review, not a human sign-off (AI-ACCURACY-POLICY amendment R32-01); it does not close acceptance-matrix gate G9.

---

## Label review: EP-26687, cohort R32 (`r32-labels-reviewed-2`)

**Result:** all 42 page-field rows agree with the pages. There are no disagreements, no "cannot determine" rows and no critical false accepts. Every source hash matched.

### 1. Header
- **Cohort:** the frozen R32 fresh M2 validation cohort (unified M4).
- **Project:** EP-26687. The label set has exactly these 12 documents for this project: F039, F040, F041, F046, F050, F056, F057, F058, F059, F060, F066, F072.
- **Label file:** `docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json`
  - sha256 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6. **MATCHED.**
- **Conventions:** `packet-inputs/LABEL-CONVENTIONS-R32.md`, read in full. I also read the label file's recorded amendment (c)(ii), which is what makes F059 a count-once alias of F046.
- **Source hashes checked:** each staged PDF against SOURCE-MANIFEST.json, and each render, text layer and crop against EVIDENCE-INDEX.json. The `staged_sha256` in the label file also equals the manifest for all 12.

| Document | PDF | Renders | Text layers | Crops |
|---|---|---|---|---|
| F039 | match | p1, p2 match | match | 4 of 4 match |
| F040 | match | p1, p2 match | match | 4 of 4 match |
| F041 | match | p1 match | match | 1 of 1 match |
| F046 | match | p1 match | match | 1 of 1 match |
| F050 | match | p1 match | match | 1 of 1 match |
| F056 | match | p1 match | match | 2 of 2 match |
| F057 | match | p1 match | match | 1 of 1 match |
| F058 | match | p1 match | match | 1 of 1 match |
| F059 | match | p1 match | match | 1 of 1 match |
| F060 | match | p1 match | match | 1 of 1 match |
| F066 | match | p1 match | match | no crop listed (none needed) |
| F072 | match | p1 match | match | 2 of 2 match |

- **Reviewer:** ep-label-reviewer role (Claude Opus agent), independent of the drafting and reviewing agents of the label set.
- **Date:** 7 October 2026.
- **Method:**
  - I read each render and crop before opening the label values.
  - I used the text layer only to confirm that each labelled region contains the value. All 27 regions of present values do.
  - Nothing was written outside the scratchpad, and no process or model was touched.

### 2. Per-item table
Every row below is AGREE. Unless the reason says otherwise, the labelled and observed semantic role, association (resolved) and `excluded_from_scoring` (false) also agree.

| Doc | Pg | Field | Labelled | Observed | Verdict | Reason |
|---|---|---|---|---|---|---|
| F039 | 1 | identity | present, "SDAR-MEP-FA-6001" (Ref. No.), own approval-request reference | present, "Ref. No.SDAR-MEP-FA-6001" in the SDAR header | AGREE | Form's own reference. Plot No. and the drawing named in the description (FA-6001) are not the identity. |
| F039 | 1 | revision | absent; "R0" kept as `referenced_revision` | absent: no revision cell; "-R0" ends the enclosed drawing's description line | AGREE | "-R0" belongs to the enclosed drawing, not to this page's own number (conventions section 4). |
| F039 | 1 | decision | present, "B - Approved as noted", approved as noted, consultant AREX, outside title block | blue tick in "B - Approved as noted"; A, C, D empty; Arun Menon / Sam Gopinathan, 18-09-2023 | AGREE | Consultant decision on the form; the contractor's round stamp is not a decision. |
| F039 | 2 | identity | present, "FA- 6001" (DWG-NO:) | "DWG-NO:FA- 6001" with a space after the hyphen | AGREE | Literal kept as printed. JOB.NO. 19-23 and PLOT NO 3620619 are not the identity. |
| F039 | 2 | revision | present, "0" (REV -), title-block cell | "REV - 0"; table row "0. SUBMITTED FOR APPROVAL 07-09-2023" | AGREE | Cell and table agree. |
| F039 | 2 | decision | present, "B Approved As Noted", approved as noted, AREX stamp, outside title block | AREX review-status stamp ticked B "Approved As Noted", dated 18-09-2023; review table code B (×2) | AGREE | The corrected region [0.615, 0.864, 0.66, 0.882] contains the ticked row. |
| F040 | 1 | identity | present, "SDAR-MEP-EM-104" (Ref. No.) | "Ref. No.SDAR-MEP-EM-104" | AGREE | Form's own reference. |
| F040 | 1 | revision | absent; "R0" kept as `referenced_revision` | absent: no cell; "-R0" ends the description of EM-104 | AGREE | Same reasoning as F039 p1. |
| F040 | 1 | decision | present, "B - Approved as noted", AREX | B ticked; A, C, D empty; consultant signatures, 18-09-2023 | AGREE | Consultant decision. |
| F040 | 2 | identity | present, "EM- 104" (DWG-NO:) | "DWG-NO:EM- 104" | AGREE | As printed, with the space. |
| F040 | 2 | revision | present, "0" | "REV - 0"; table row 0 | AGREE | |
| F040 | 2 | decision | present, "B Approved As Noted", AREX stamp, outside title block | AREX stamp ticked B; review table code B; red comments | AGREE | Region [0.62, 0.80, 0.67, 0.83] contains the ticked row on this sheet. |
| F041 | 1 | identity | present, "EM- 104" | "DWG-NO:EM- 104" | AGREE | |
| F041 | 1 | revision | present, "0" | "REV - 0"; table row 0 | AGREE | |
| F041 | 1 | decision | absent, `no_decision_area` | no review stamp or status box; only a round company seal | AGREE | A seal is not a decision. |
| F046 | 1 | identity | present, "FA- 6001" | "DWG-NO:FA- 6001" | AGREE | |
| F046 | 1 | revision | present, "0" | "REV - 0" | AGREE | |
| F046 | 1 | decision | absent, `no_decision_area` | no status area; company seal only | AGREE | |
| F050 | 1 | identity | present, "EM-100" | "DWG-NO:EM-100" (no space) | AGREE | |
| F050 | 1 | revision | present, "0" | "REV - 0" | AGREE | |
| F050 | 1 | decision | absent, `no_decision_area` | no stamp, seal or status area | AGREE | |
| F056 | 1 | identity | present, "EF-103" | "DWG-NO:EF-103" | AGREE | The page prints EF, not EM, although the title is "ROOF FLOOR EMERGENCY LAYOUT". The label correctly keeps the printed value and does not take a value from the file name. |
| F056 | 1 | revision | present, "1" | "REV - 1"; table "1 REVISED AS PER COMMENTS 21-09-2023" | AGREE | |
| F056 | 1 | decision | absent, `no_decision_area` | no review stamp; company seal only | AGREE | "REVISED AS PER COMMENTS" is the contractor's revision note, not a decision. |
| F057 | 1 | identity | present, "FA-1002" | "DWG-NO:FA-1002" | AGREE | |
| F057 | 1 | revision | present, "0" | "REV - 0" | AGREE | |
| F057 | 1 | decision | absent, `no_decision_area` | no review stamp; seal only | AGREE | |
| F058 | 1 | identity | present, "EM-102" | "DWG-NO:EM-102" | AGREE | |
| F058 | 1 | revision | present, "0" | "REV - 0" | AGREE | |
| F058 | 1 | decision | absent, `no_decision_area` | no review stamp; seal only | AGREE | |
| F059 (alias of F046) | 1 | identity | present, "FA- 6001" | "DWG-NO:FA- 6001" | AGREE | Labelled on its own page; counted once with F046. |
| F059 | 1 | revision | present, "0" | "REV - 0" | AGREE | Counted once. |
| F059 | 1 | decision | absent, `no_decision_area` | no stamp or seal at all | AGREE | Counted once. Visually it differs from F046 only by the seal, as the alias annotation states. |
| F060 | 1 | identity | present, "EM-100" | "DWG-NO:EM-100" | AGREE | |
| F060 | 1 | revision | present, "1" | "REV - 1"; table row 1 dated 21-09-2023 | AGREE | |
| F060 | 1 | decision | absent, `no_decision_area` | no stamp, seal or status area | AGREE | |
| F066 | 1 | identity | absent | "CONTENT" index page; no document or reference number printed | AGREE | |
| F066 | 1 | revision | absent | no cell, table or suffix | AGREE | |
| F066 | 1 | decision | absent, `no_decision_area` | no stamp or status area | AGREE | |
| F072 | 1 | identity | present, "MAR-MEP-ELE-05" (Ref. No.), own MAR reference | "Ref. No. MAR-MEP-ELE-05" | AGREE | Plot No. 3620619 is not the identity. |
| F072 | 1 | revision | absent | no revision cell, table or suffix on the form | AGREE | |
| F072 | 1 | decision | present, "C - Revise & Resubmit", revise and resubmit, AREX, outside title block | blue tick in "C - Revise & Resubmit"; A, B, D empty; Arun Menon / Sam Gopinathan, 07-09-2023 | AGREE | Consultant decision; the contractor's stamp and signature in the delivery cell are not decisions. |

### 3. Totals for EP-26687
- **Rows:** 42 page-field rows reviewed (14 pages × 3 fields): 42 AGREE, 0 DISAGREE, 0 CANNOT DETERMINE.
- **Count-once rule:** F059 p1 is counted under F046. That leaves 13 page cases per field and 11 counted documents.

| Field | Page cases reviewed | Agree | Disagree | Cannot determine | Present-value cases | Documents carrying the field | Status |
|---|---|---|---|---|---|---|---|
| identity | 13 | 13 | 0 | 0 | 12 | 10 of 11 | Page cases ≥ 12; but only 11 counted documents, so **NOT ESTABLISHED** on the document unit |
| revision | 13 | 13 | 0 | 0 | 9 | 9 of 11 | **NOT ESTABLISHED** (9 present values; 11 documents) |
| decision | 13 | 13 | 0 | 0 | 5 | 3 of 11 (F039, F040, F072) | **NOT ESTABLISHED** (5 present values; 11 documents) |

The NOT ESTABLISHED marks follow the gate-count unit in conventions section 7, where a document "carries" a field. Taken alone, this project cannot establish any field; it only contributes cases to the cohort-wide totals.

### 4. Critical false accepts
None found.
- No present resolved value differs from what its page prints.
- Every page with content shows the same project (Plot No. 3620619, owner Wail Al Jamali, Umm Suqeim Second, AREX/ENCO). F066 is the one exception, covered in section 5; all its fields are absent, so it cannot cause a false accept.

### 5. Hygiene findings (no value errors)
1. **Stale open items after the review rulings:**
   - F039 and F040 still list "p1 revision only as the '-R0' suffix ... (association uncertain)" under `unresolved`, with confidence "medium", although the reviewed rows now say absent.
   - F059 still says "reviewer to rule whether F046 and F059 count once", and F046 says "near-duplicate of F059", although count-once was adopted.
   - These are bookkeeping only; the rows themselves are correct.
2. **`other_identities` is empty for this project.** No EP-26687 document has a structured `other_identities` entry, although the field appears 113 times elsewhere in the file. The numbers that belong there are mentioned only in review notes:
   - JOB.NO. 19-23 and PLOT NO 3620619 on every drawing;
   - Plot No. 3620619 on the SDAR and MAR forms;
   - the drawing numbers FA-6001 and EM-104 named in the SDAR descriptions.

   No label puts one of these as the identity, so this does not affect scoring.
3. **Hyphen characters:** the text layer of F039 p1, F040 p1 and F072 uses U+2010 hyphens, while the label literals use ASCII "-". The rendering can't tell them apart, and the visible-rendering rule is satisfied. The scorer should normalise hyphens.
4. **F066 project link:** nothing on the page itself ties F066 to EP-26687. Its only marks are the EST, Carrier and EATON logos and the footer "Al Arabia Safety & Security L.L.C". Its membership rests on staging metadata, not page evidence. All three fields are absent, so this does not affect scoring.
5. **Cross-document reasoning in a note:** the F056 decision note names its seal "as legible on the larger F039 p2 crop". The seal is partly legible on F056 itself, and the decision state (absent) does not depend on it.
6. **Nothing else found:** all page references are present, there are no duplicated items, no label points at the wrong document, and all scans are clean vector renders, fully legible.

### 6. Human sign-off
This is an AI review, not a human sign-off. A human reviewer must still confirm three things:
- the five consultant decision marks (F039 p1/p2, F040 p1/p2, F072 p1);
- that the -R0 description suffixes on F039 p1 and F040 p1 are correctly left out as the page's revision;
- the owner's acceptance of the F059→F046 count-once amendment and of F066 belonging to the project.
