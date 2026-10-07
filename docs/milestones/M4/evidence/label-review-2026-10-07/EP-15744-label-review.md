# R32 label review — EP-15744 (raw reviewer report, filed verbatim by the orchestrator)

Filed 7 October 2026. Role: ep-label-reviewer, run as a general-purpose Claude Opus agent with the role's definition inlined (see docs/SESSION-LOG-2026-10-07-windows.md row 1a). Read-only; the agent wrote nothing outside the scratchpad. Label set `r32-labels-reviewed-2` (sha256 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6); staged pages under C:\t\r2x\r32-stage. This is an AI review, not a human sign-off (AI-ACCURACY-POLICY amendment R32-01); it does not close acceptance-matrix gate G9.

---

## Label review: EP-15744, R32 fresh M2 validation cohort (unified M4)

**1. Header**
- **Cohort:** frozen R32 fresh M2 validation cohort (unified M4).
- **Project:** EP-15744.
- **Label file:** `G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json` (`r32-labels-reviewed-2`). Its sha256 is 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6, which matches the expected hash.
- **Conventions:** `packet-inputs/LABEL-CONVENTIONS-R32.md`, read in full.
- **Source hashes:** every staged PDF matched its SOURCE-MANIFEST `staged_sha256`, and every render and crop I used matched EVIDENCE-INDEX.
  - F043: PDF matched; renders p1–4 matched; 6 crops matched.
  - F055: PDF matched; render p1 matched.
  - F061: PDF matched; renders p1–4 matched.
  - F062, F063, F065, F068: PDF matched; render p1 matched.
  - F064, F069, F071: PDF matched; renders p1–4 matched.
  - F067: PDF matched; render p1 matched; 2 crops matched.
  - F070: PDF matched, and its sha256 7b7e3a7a679e55edfaa940b773e8fa711a71b2c1785a9e32c50c500627431d55 is identical to F067. Byte identity is confirmed. F070 is counted once, under F067, and was not re-labelled. Its render p1 also matched.
  - Extra crops I made from the hash-checked PDFs were written only under the scratchpad.
- **Reviewer:** ep-label-reviewer role (Claude Opus agent), independent of the drafting and reviewing agents of the label set.
- **Date:** 7 October 2026.
- **Method:** for every page I read the render (and crop) before opening the label values.

**2. Per-item table**

Abbreviations: Id = identity, Rev = revision, Dec = decision. "absent/nda" = absent with absent_kind no_decision_area. "res" = association resolved. "excl" = excluded_from_scoring.

| Doc | Pg | Field | Labelled | Observed | Verdict | Reason |
|---|---|---|---|---|---|---|
| F043 | 1 | Id | present "ش إ م / عام/٢٠١٤ / ١٣٢٤" (الرقم), res | present, same literal after "الرقـم :" | AGREE | Letter reference matches as printed, including unspaced "عام/٢٠١٤" and Arabic-Indic digits. The corrected region (y 0.185–0.207) is right. |
| F043 | 1 | Rev | absent | absent | AGREE | The cover letter has no revision source. |
| F043 | 1 | Dec | absent/nda | absent/nda | AGREE | Letter transmitting approved-material lists; no decision on a submitted document. |
| F043 | 2 | Id | ambiguous (candidates "ANNEXURE BROV.011OF12", "ANNEXU RE B") | ambiguous / no labelled own number | AGREE | Footer page locator and header annex designation; neither is marked as the document number. |
| F043 | 2 | Rev | present "Rev. 0", res | present: "RE B - Rev. 0 -DATE:5-3-2014" in the running header | AGREE | Value is right. The literal includes the "Rev." prefix (see hygiene). |
| F043 | 2 | Dec | absent/nda | absent/nda | AGREE | "APPROVED MATERIALS / VENDORS" is the list title, not a decision. |
| F043 | 3 | Id | ambiguous ("ANNEXURE BROV.012OF12" / "ANNEXU RE B") | ambiguous | AGREE | Same as p2. |
| F043 | 3 | Rev | present "Rev. 0", res | present "Rev. 0" | AGREE | Same header. |
| F043 | 3 | Dec | absent/nda | absent/nda | AGREE | List page. |
| F043 | 4 | Id | ambiguous ("ANNEXURE BROV.013OF12" / "ANNEXU RE B") | ambiguous | AGREE | Same as p2. |
| F043 | 4 | Rev | present "Rev. 0", res | present "Rev. 0" | AGREE | Same header. |
| F043 | 4 | Dec | absent/nda | absent/nda | AGREE | List page. |
| F055 | 1 | Id | absent | absent | AGREE | Legend/specification extract with no title block. |
| F055 | 1 | Rev | absent | absent | AGREE | No revision source. |
| F055 | 1 | Dec | absent/nda | absent/nda | AGREE | No status area. |
| F061 | 1 | Id | present "K18" (رقم الترخيص), res | present "K18" | AGREE | Licence number in the certificate header block. 217030 (رقم الرخصة), 14585 (رقم السجل) and "28 - 1" are correctly kept in other_identities. |
| F061 | 1 | Rev | absent | absent | AGREE | Only the licence year 2018 and the sheet counter. |
| F061 | 1 | Dec | absent/nda | absent/nda | AGREE | The DCD "يعتمد / عن مدير الإدارة العامة للدفاع المدني/دبي" block with stamp is the issuer's authentication of its own licence, not a review decision. This is a judgement; see section 6. |
| F061 | 2 | Id | present "K18", res | present "K18" | AGREE | Sheet "(28 – 3)". |
| F061 | 2 | Rev | absent | absent | AGREE | — |
| F061 | 2 | Dec | absent/nda | absent/nda | AGREE | Same issuer block. |
| F061 | 3 | Id | present "K18", res | present "K18" | AGREE | Sheet "(28 – 4)". |
| F061 | 3 | Rev | absent | absent | AGREE | — |
| F061 | 3 | Dec | absent/nda | absent/nda | AGREE | Same. |
| F061 | 4 | Id | present "K18", res | present "K18" | AGREE | Sheet "(28 – 9)". The corrected region is right. |
| F061 | 4 | Rev | absent | absent | AGREE | — |
| F061 | 4 | Dec | absent/nda | absent/nda | AGREE | Same. |
| F062 | 1 | Id | present "TR/3544/18" (AASS Ref.), res | present "TR/3544/18" | AGREE | Own transmittal reference. EP-15744/SM/FAS/201, Project ID EP-15744 and P06/TRANS/R1 are correctly in other_identities. |
| F062 | 1 | Rev | absent | absent | AGREE | "R0" in the subject belongs to the enclosed submittal; R1 is the form code. |
| F062 | 1 | Dec | absent/nda | absent/nda | AGREE | Receipt block (signature, 13-08-18) and a handwritten Arabic routing note only. |
| F063 | 1 | Id | present "TR/6143/19" (AASS Ref.), res | present "TR/6143/19" | AGREE | Own transmittal reference. |
| F063 | 1 | Rev | absent | absent | AGREE | — |
| F063 | 1 | Dec | absent/nda | absent/nda | AGREE | Receipt block only (04-11-2019). |
| F064 | 1–4 (one row per page per field, 12 items) | Id / Rev / Dec | absent / absent / absent/nda on every page | the same on every page | AGREE ×12 | TOA manual pages 5-54 to 5-57; page numbers only. |
| F065 | 1 | Id / Rev / Dec | absent / absent / absent/nda | the same | AGREE ×3 | Equipment schedule with model codes only. |
| F067 | 1 | Id | present "CMW-17045-C001-01-E-0001" (DRAWING NO.), res | present; the print shows a visible gap: "CMW-17045-C001- 01-E-0001" | AGREE | Value and role are right. The gap after "C001-" may or may not be a space character in the raster; the label flags it for normalisation. |
| F067 | 1 | Rev | present "00" (REVISION No.), res | present "00" | AGREE | Matches revision row "00 CONSTRUCTION DOCUMENT 05/17". |
| F067 | 1 | Dec | ambiguous; dated round stamp plus signature in the AUTHORITIES APPROVAL box; actor CMW (inferred); in_title_block | ambiguous | AGREE | No decision wording, code or legend; approval versus receipt cannot be established. The day digit of the stamp reads "1 0" or "1 8"; the label states "10 MAY 2017". |
| F068 | 1 | Id | absent; EP-15744 in other_identities as "Oracle Job No. / OM No." | absent | AGREE | The page itself labels EP-15744 as a job number. P06/PRC&CR/F and PRE.FAISAL/PRF/11 are form/file codes. |
| F068 | 1 | Rev | absent | absent | AGREE | — |
| F068 | 1 | Dec | absent/nda | absent/nda | AGREE | "Received @ 28.4.19" is a receipt, not a decision. |
| F069 | 1 | Id | ambiguous, literal null, candidate "EP-15744" (Refrence), excl true | ambiguous | AGREE | The only candidate is under the bare label "Refrence". The page does not say whether it is the quotation's own number or a job number. |
| F069 | 1 | Rev | absent | absent | AGREE | — |
| F069 | 1 | Dec | absent/nda | absent/nda | AGREE | Supplier quotation. |
| F069 | 2 | Id / Rev / Dec | absent / absent / absent/nda | the same | AGREE ×3 | Continuation page ("Page 2 of 2"). |
| F069 | 3 | Id | ambiguous, literal null, candidate "EP-15744", excl true | ambiguous | AGREE | Second Design Sheet (4-Aug-18); same bare "Refrence". |
| F069 | 3 | Rev | absent | absent | AGREE | — |
| F069 | 3 | Dec | absent/nda | absent/nda | AGREE | Quotation. |
| F069 | 4 | Id / Rev / Dec | absent / absent / absent/nda | the same | AGREE ×3 | Terms and signature page. |
| F071 | 1–4 (one row per page per field, 12 items) | Id / Rev / Dec | absent / absent / absent/nda on every page | the same on every page | AGREE ×12 | The running header "CME-17045 @ ALI MINHAD) – SPL/STI CALCULATION" is a project/title line, not a number. No revision and no status area. |
| F070 | — | — | duplicate_of F067, no pages | byte-identical to F067 (sha256 equal) | AGREE (alias) | Counted once under F067; not re-labelled. |

**3. Totals per field for EP-15744** (F070 counted once under F067)

| Field | Page items reviewed | Agree | Disagree | Cannot determine | Status |
|---|---|---|---|---|---|
| Identity | 26 | 26 | 0 | 0 | **NOT ESTABLISHED** |
| Revision | 26 | 26 | 0 | 0 | **NOT ESTABLISHED** |
| Decision | 26 | 26 | 0 | 0 | **NOT ESTABLISHED** |

- **Why all three are NOT ESTABLISHED:** counted per document after count-once, each field has only 11 reviewed cases, which is under 12.
- **Present-value cases are fewer still:**
  - Identity: present and resolved on 8 pages across 5 documents (F043, F061, F062, F063, F067).
  - Revision: present on 4 pages across 2 documents (F043, F067).
  - Decision: present on 0 pages. There are 25 absent/nda pages and 1 ambiguous page (F067).
- The decision absent states and absent_kind values were judged throughout; all agree.

**4. Critical false accepts**
None found. No wrong value is labelled as a resolved present value. I could not show that any document belongs to another project, but three need a human look at project membership:
- **F043:** pages 1–4 are a generic Military Works Command 2014 letter (ش إ م / عام/٢٠١٤ / ١٣٢٤) and the "CMW General Specifications Annexure B" vendor list. Nothing on these pages shows EP-15744 or 17045. The label's `ep` cannot be confirmed from the pages, yet F043 counts in this project's identity and revision populations.
- **F071:** the header says "CME-17045 @ ALI MINHAD", but every EASE image on pages 2–4 is stamped "Project: Malleha Camp" / "(c) EASE 4.4 / Malleha Camp". The calculation images may be reused from another project's model. All labelled values are absent, so there is no false accept.
- **F069:** page 1 reads "Command Of Military Works 17045 at Al minhad", but page 3 reads "CMW 17045 at Al Awir". The location differs within one file.

**5. Hygiene findings**
- **F043 revision literal:** recorded as "Rev. 0", which includes the printed prefix "Rev.". Other labels record the value only (for example F067 "00"). The literal convention is inconsistent, so scorers must normalise.
- **F043 mixes two documents at file level:** its identity comes from the page 1 cover letter, while its revision comes from the pages 2–4 annex (D-003). Any scorer that pairs identity with revision per file will pair values from two different documents.
- **F069 cross-document reasoning in the label text:** the state "ambiguous" is page-only and correct. But the p1 candidate role says "(issuer's project/job number on F062/F068)", the `semantic_role` says "own quotation reference (equals the project EP number)", and the review note asserts EP-15744 "is the contractor's EP project/job number". This cites other documents, which the conventions forbid. The semantic_role also contradicts the ambiguous state.
- **F069 holds two quotations** (pages 1–2 and 3–4) in one pool document. The label notes this.
- **F067 drawing number spacing:** possible space after "C001-" (see table).
- **F067 missing other identity:** the frame code "CMW-D005-DWG-Rev01-111127 / ISO 9001-2008" (bottom left) is not in other_identities. Its "Rev01" must not be read as the drawing's revision.
- **F067 stamp date:** the day digit is uncertain ("10" or "18"), but the label states 10 MAY 2017 as fact.
- **F061 sheet numbering:** the in-scope pages are licence sheets 1, 3, 4 and 9 of 28, not consecutive. This is informational only.
- **F055 text layer:** contains garbled glyphs (",3&(,/,1*7<3("). This does not affect any label.
- **No other problems:** no missing page references, no duplicate items beyond the F070 alias, no label pointing at the wrong document, and no unreadable scan. F043 pages 2–4 are scanned and rotated but legible.

**6. Not a human sign-off**
This is an AI review, not a human sign-off. A human reviewer must still confirm:
- the Arabic literal on F043 p1;
- the F061 ruling that a DCD issuer "يعتمد" block is not a decision;
- the F067 stamp's meaning, date and actor;
- the F069 ruling D-004 (ambiguous versus absent);
- that F043 and F071 truly belong to EP-15744.
