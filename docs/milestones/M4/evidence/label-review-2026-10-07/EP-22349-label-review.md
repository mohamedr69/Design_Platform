# R32 label review — EP-22349 (raw reviewer report, filed verbatim by the orchestrator)

Filed 7 October 2026. Role: ep-label-reviewer, run as a general-purpose Claude Opus agent with the role's definition inlined (see docs/SESSION-LOG-2026-10-07-windows.md row 1a). Read-only; the agent wrote nothing outside the scratchpad. Label set `r32-labels-reviewed-2` (sha256 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6); staged pages under C:\t\r2x\r32-stage. This is an AI review, not a human sign-off (AI-ACCURACY-POLICY amendment R32-01); it does not close acceptance-matrix gate G9.

---

## 1. Header

- **Cohort:** frozen R32 fresh M2 validation cohort (unified M4)
- **Project:** EP-22349
- **Label file:** `G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json`, version r32-labels-reviewed-2. Its sha256 is `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6`, which matches.
- **Conventions:** read in full from `packet-inputs/LABEL-CONVENTIONS-R32.md`.
- **Source hashes:** every staged PDF matched `staged_sha256` in SOURCE-MANIFEST.json. Every render matched EVIDENCE-INDEX.json, and so did its text layer and its binding to the staged hash. Every crop listed for these documents also matched.
  - F035: PDF matched; renders p1–p4 matched; 8 crops matched.
  - F038: PDF matched; renders p1–p4 matched; 7 crops matched.
  - F042, F044, F047, F048, F049, F051, F053, F054: each PDF matched; each p1 render matched; each crop matched.
  - F045: PDF matched; p1 render matched; it has no crops.
  - F052: PDF matched; renders p1–p4 matched.
- **F052 alias:** confirmed byte-identical to F038. Both files have sha256 `6f2e35f38fe457048e3804eb7b93f3e606f5ba06cb1a31bc0304999e96f30d53`, and `cmp` reports them identical. F052 was counted once, under F038, and not re-labelled.
- **No mismatch anywhere:** no document is NOT CHECKED.
- **Extra crops:** a few stamp regions were cropped with pymupdf from the hash-checked staged PDFs, written under the scratchpad only.
- **Reviewer:** ep-label-reviewer role (Claude Opus agent), independent of the drafting and reviewing agents of the label set.
- **Date:** 7 October 2026.
- **Method:** I read each page's three fields from the render or crop before opening that document's label.

## 2. Per-item table

| Doc | Pg | Field | Labelled (state / literal) | Observed (state / literal) | Verdict | Reason |
|---|---|---|---|---|---|---|
| F035 | 1 | identity | present / `GGC/140/MAS/MEP-ELE-026` ("Submittal Ref:") | present / `GGC/140/MAS/MEP-ELE-026` | AGREE | Printed in the Submittal Ref cell. Association resolved. Page is an EMAAR/Mirage submittal (AR III, Wadi Al Safa 5). |
| F035 | 1 | revision | present / `03` ("REV.") | present / "REV. 03" → `03` | AGREE | Value in the same cell as the label. |
| F035 | 1 | decision | present / `B` / approved as noted / Engineer (Mirage) / outside_title_block | present / B tick / approved as noted | AGREE | The tick starts in the B box under ENGINEER'S COMMENTS. Page legend: "B: No Objection subject to comments". |
| F035 | 2 | identity | present / `CRWN-ELEC-MAT-024` ("Ref. No.") | present / same | AGREE | Emarat/Al Burj MAR (Al Rashidiyah filling station). |
| F035 | 2 | revision | ambiguous / `2` | handwritten "X" then a circled "2" in a blank Rev. No. cell; its role as revision is uncertain | AGREE | The "2" is legible but its role is not established, so ambiguous is correct. Not scorable. |
| F035 | 2 | decision | present / `B- Approved As Noted` / approved as noted / Al Burj RE | present / B box ticked | AGREE | Tick in B box. The client's B is highlighted but not ticked, and the label notes this. |
| F035 | 3 | identity | present / `ANG-EXPO-MUSE-NSD-ARCO-MEP-ST-024` ("REF NO.") | present / same | AGREE | Angola Pavilion Expo 2020 submittal sheet. |
| F035 | 3 | revision | present / `00` ("REVISION") | present / `00` | AGREE | |
| F035 | 3 | decision | ambiguous / "Samples not new & delapidated. Replace samples … AX-T741 & AX-T708. Samples for AX-T605L & AX-T632L are approved." | handwritten MUSE comment: two samples to be replaced, two approved; no status box | AGREE | No single class applies. "Present, class other" would also be defensible under convention §5. The ambiguous state is the conservative choice and leaves the field unscored. The literal follows the handwriting. |
| F035 | 4 | identity | present / `MLT-J2734-MAF-EL-025` ("Submittal No.") | present / same (faint) | AGREE | DHA MAF (DIC Emergency & Trauma Center). |
| F035 | 4 | revision | present / `01` ("Rev.") | present / `01` | AGREE | |
| F035 | 4 | decision | present / `No Objection with Comments` / approved as noted / consultant (Hosmac) | present / red tick and underline at "No Objection with Comments" | AGREE | The DHA block ticks "2. work may proceed subject to incorporation of comments", and the label notes this. |
| F038 | 1 | identity | present / `2020-4-1072822` (الرقم) | present / same | AGREE | Ajman Civil Defence letter number. other_identities (plot 0815, receipt 200020347656) are correct. |
| F038 | 1 | revision | absent | absent | AGREE | Only the issue and expiry dates are printed. |
| F038 | 1 | decision | present / "…قد تم اعتماد المخططات من قبلنا و لا مانع لدينا من تنفيذ هذه الأعمال شريطة التقيد بالتالي" / approved / Ajman CD | present / approval subject to listed conditions | AGREE | The conditions are generic. "approved" is defensible; "approved as noted" is the alternative (see item 6). |
| F038 | 2 | identity | present / `F.F-00` (SHEET NO.) | present / `F.F-00` | AGREE | No separate drawing-number cell. 2020-4-1072822, 0815 and 000 are correctly in other_identities. |
| F038 | 2 | revision | absent | absent | AGREE | No REV cell or table. |
| F038 | 2 | decision | present / "إعتماد مخططات أولية / Initial Drawings Approval" / approved / Ajman CD | present / CD stamp | AGREE | The authority stamp is unambiguous. The page also carries a handwritten "APPROVED WITH COMMENTS", dated 11 Mar 2020, beside the "AJ TRAINING & CONSULTANCY" stamp. The page does not say what role AJ has. The label treats it as a third party (see item 6). |
| F038 | 3 | identity | present / `F.F-01` | present / `F.F-01` | AGREE | |
| F038 | 3 | revision | absent | absent | AGREE | |
| F038 | 3 | decision | present / Initial Drawings Approval / approved / Ajman CD | present / CD stamp | AGREE | The AJ stamp and signature are present without the "approved with comments" text, which is correct. Blue handwritten review comments are on the drawing; the label's notes do not mention them. |
| F038 | 4 | identity | present / `F.F-02` | present / `F.F-02` | AGREE | |
| F038 | 4 | revision | absent | absent | AGREE | |
| F038 | 4 | decision | present / Initial Drawings Approval / approved / Ajman CD | present / CD stamp | AGREE | |
| F042 | 1 | identity | present / `FA-03` (SHEET NO.) | present / `FA-03` | AGREE | "OLD APPLICATION NUMBER 2020 - 4 - 1072822" is correctly in other_identities. |
| F042 | 1 | revision | absent | absent | AGREE | |
| F042 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | The only stamp is Al Arabia For Safety & Security, the contractor/supplier, so it is not a decision. "AS BUILT" is a drawing status. |
| F044 | 1 | identity | present / `EM-07` | present / `EM-07` | AGREE | |
| F044 | 1 | revision | absent | absent | AGREE | |
| F044 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | Al Arabia contractor stamp only. |
| F045 | 1 | identity | absent | absent | AGREE | Product schematic with no title block. The AX-T codes are catalogue codes. |
| F045 | 1 | revision | absent | absent | AGREE | |
| F045 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | |
| F047 | 1 | identity | present / `EM-02` | present / `EM-02` | AGREE | |
| F047 | 1 | revision | absent | absent | AGREE | |
| F047 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | No stamp. |
| F048 | 1 | identity | present / `FA-05` | present / `FA-05` | AGREE | other_identities omit the printed old application number (item 5). |
| F048 | 1 | revision | absent | absent | AGREE | |
| F048 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | |
| F049 | 1 | identity | present / `EM-05` | present / `EM-05` | AGREE | other_identities omit the printed old application number (item 5). |
| F049 | 1 | revision | absent | absent | AGREE | |
| F049 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | |
| F051 | 1 | identity | present / `EM-15` | present / `EM-15` | AGREE | |
| F051 | 1 | revision | absent | absent | AGREE | |
| F051 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | Al Arabia contractor stamp only. |
| F053 | 1 | identity | present / `FA-17` | present / `FA-17` | AGREE | |
| F053 | 1 | revision | absent | absent | AGREE | |
| F053 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | Al Arabia contractor stamp only. |
| F054 | 1 | identity | present / `FA-05` | present / `FA-05` | AGREE | Same printed sheet number as F048, but a different drawing: fourth parking plan, 18/05/2023, versus F048's typical floor plan, 15/03/2022. The label flags this. |
| F054 | 1 | revision | absent | absent | AGREE | |
| F054 | 1 | decision | absent / no_decision_area | absent / no_decision_area | AGREE | Al Arabia contractor stamp only. |
| F052 | — | (alias) | duplicate_of F038; no pages of its own | byte-identical to F038 (sha256 and cmp) | AGREE | Counted once, under F038. |

**Fields in every row:** semantic role, association (all present values resolved), excluded_from_scoring (all false) and location (all outside_title_block for decisions) were also checked, and all agree.

## 3. Totals for EP-22349 (page-field cases; F052 counted once under F038)

| Field | Reviewed | Agree | Disagree | Cannot determine |
|---|---|---|---|---|
| identity | 17 | 17 | 0 | 0 |
| revision | 17 | 17 | 0 | 0 |
| decision | 17 | 17 | 0 | 0 |

- **Page-field level:** all three fields reach 12 or more matched cases, so they are established for this project.
- **Present-and-resolved values only:**
  - identity: 16 cases, established.
  - revision: 3 cases (F035 p1, p3 and p4), **NOT ESTABLISHED**.
  - decision: 7 cases (F035 p1, p2 and p4, plus F038 p1–p4), **NOT ESTABLISHED**.
- **Document level** (counting rule in convention §7): there are only 11 counted documents (F035, F038+F052, F042, F044, F045, F047, F048, F049, F051, F053, F054). Every field is therefore **NOT ESTABLISHED** for this project at document level.
- **If the F035 pages are excluded** (they belong to other projects): 13 cases per field remain. The present-value counts fall to identity 12, revision 0 and decision 4.

## 4. Critical false accepts

None found. No wrong value is labelled as a resolved present value. No document from another project is labelled as an EP-22349 document. The label states plainly in `kind` and `page_role` that F035 pages 1–4 are other projects' submittals, and it restricts scoring to the page level.

## 5. Hygiene findings

1. **F035 project content (risk, not an error):** the file is staged under EP-22349 but holds earlier approvals on four other projects. These are EMAAR/Mirage, Emarat/Al Burj, Expo/MUSE Angola Pavilion and DHA/Hosmac. Its four resolved identities, three resolved revisions and three resolved decisions are not EP-22349 facts. If a gate counts them toward EP-22349 at document level, it would be counting another project's documents as this project's. A human must decide whether F035 belongs in this project's field populations.
2. **F048 and F049 other_identities:** both pages print "OLD APPLICATION NUMBER 2020 - 4 - 1072822", which the render and text layer both show. The label leaves it out of other_identities, while F042, F044, F047, F051, F053 and F054 record it. F047 also gives it a different role wording from the others. This does not affect the identity field.
3. **F038 evidence references:**
   - p3 identity cites "render F038-p3.png", although the hash-bound crop `F038-p3-0.88_0.7_1_0.98.png` exists.
   - p1 decision cites "render F038-p1.png" as a bare name, not a path.
   - Both refer to correct locations.
4. **F038 p3 note gap:** the decision notes do not mention the blue handwritten review comments on the drawing ("sprinkler system shall comply with UAE life safety code and NFPA 13", "fire lift…", "FM200", "clean agent system should be provided"). These bear on the approved / approved-as-noted question in item 6.
5. **Same sheet number on two drawings:** F048 and F054 both print FA-05 for different drawings. The label flags this correctly, and scoring must key on the document, not the literal.
6. **Other checks:** no missing page references, no duplicated items (apart from the declared F052 alias), and no label pointing at the wrong document. All scans were legible. F035 p4 is faint but readable.

## 6. Human sign-off still needed

This is an AI review, not a human sign-off. A human reviewer must still confirm three things:
- Whether F035, a compilation of other projects' approvals, may count toward EP-22349 field populations.
- Whether F038's Civil Defence initial approval is class "approved" or "approved as noted", given the conditions and the "APPROVED WITH COMMENTS" mark of AJ Training & Consultancy. This includes whether AJ acts for the authority, which the page does not establish.
- Whether F035 p3's partly approving decision should be "ambiguous" or "present, class other".
