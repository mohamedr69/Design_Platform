# R32 label review — EP-27331 (raw reviewer report, filed verbatim by the orchestrator)

Filed 7 October 2026. Role: ep-label-reviewer, run as a general-purpose Claude Opus agent with the role's definition inlined (see docs/SESSION-LOG-2026-10-07-windows.md row 1a). Read-only; the agent wrote nothing outside the scratchpad. Label set `r32-labels-reviewed-2` (sha256 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6); staged pages under C:\t\r2x\r32-stage. This is an AI review, not a human sign-off (AI-ACCURACY-POLICY amendment R32-01); it does not close acceptance-matrix gate G9.

---

## Label review: EP-27331 (EMAAR / Mirage, Sea Point Plot B01, J 269)

**1. Header**
- **Cohort:** frozen R32 fresh M2 validation cohort (unified M4).
- **Project:** EP-27331, 12 documents, 47 labelled pages.
- **Label file:** `r32-labels-reviewed-2`, at G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json. The sha256 is 89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6, which matches.
- **Conventions:** packet-inputs/LABEL-CONVENTIONS-R32.md (frozen), read in full. I also read the label file's own `convention_rulings` and `convention_amendments_and_interpretations`.
- **Source hashes (sha256 recomputed for every file):**

| F-id | Staged PDF vs SOURCE-MANIFEST | Renders vs EVIDENCE-INDEX | Crops vs EVIDENCE-INDEX |
|---|---|---|---|
| F008 | MATCH | p1–p4 MATCH | 5 MATCH |
| F009 | MATCH | p1–p4 MATCH | 4 MATCH |
| F013 | MATCH | p1–p4 MATCH | 5 MATCH |
| F020 | MATCH | p1–p4 MATCH | 5 MATCH |
| F021 | MATCH | p1–p4 MATCH | 7 MATCH |
| F025 | MATCH | p1–p4 MATCH | 11 MATCH |
| F028 | MATCH | p1–p4 MATCH | 3 MATCH |
| F030 | MATCH | p1–p4 MATCH | 5 MATCH |
| F032 | MATCH | p1–p4 MATCH | 5 MATCH |
| F034 | MATCH | p1–p4 MATCH | 5 MATCH |
| F036 | MATCH | p1–p4 MATCH | 5 MATCH |
| F037 | MATCH | p1–p3 MATCH | 5 MATCH |

  - The `staged_sha256` stored in the label for each document also equals the manifest value.
  - Page counts (pymupdf) match the label's `kind` text: 56, 7, 4, 7, 30, 8, 61, 7, 15, 15, 82 and 3 pages.
  - No document is NOT CHECKED.
- **Reviewer:** ep-label-reviewer role (Claude Opus agent), independent of the drafting and reviewing agents of the label set.
- **Date:** 7 October 2026.
- **Method:** for every page I read the render and the bound crops myself before opening the label values. The rotated F025 pages were read from the upright r90 crops. I made two scratch zooms (one from the source PDF, one from the render) under the scratchpad only. Nothing was written anywhere else, and no model call was made.

**2. Per-item table**

Notation:
- `P` = present, `A` = absent, `res` = resolved, `unc` = uncertain, `inf` = actor inferred, `TB` = in title block.
- Unless marked otherwise, every row has `excluded_from_scoring` = false, and the labelled state, literal, semantic role and association equal my observation.
- `AGREE*` means the value agrees but the row depends on a label-set interpretation that is not in the frozen conventions (see section 5).

Page types, the same in every document:
- **Cover page (p1):** the Document Submittal form, with the code A–E row and its legend "B-Approved with comments, C-Not Approved (Re-submit within 14 days)".
- **Circulation page (p2):** the Al Sahel "J269 CIRCULATION" stamp plus a handwritten file note. F025 and F037 have no circulation page.
- **Register page:** the DRAWING REGISTER, headed "Submittal Ref: <no>-Rev.<rev>".
- **Drawing sheet:** an A1 sheet carrying the Mirage A–E review block and the DRAWING NO. / REVISION cells.

| Doc | Pg | Field | Labelled | Observed | Verdict | Reason |
|---|---|---|---|---|---|---|
| F008 | 1 | identity | P "B01-ASC-SD-ELE-0102" (Submittal Ref.No.) res | same | AGREE | own submittal ref on the cover |
| F008 | 1 | revision | P "00" (Rev. No.) res | "00" | AGREE | Rev. No. cell |
| F008 | 1 | decision | P "Code B", approved as noted, res, outside TB | Code B box green, ticked and circled; Bipin Mathew 11.06.2025 | AGREE | legend on the same page |
| F008 | 2 | identity | A | A (handwritten "SD-ELE-102_B" only) | AGREE | no printed own number |
| F008 | 2 | revision | A | A | AGREE | none printed |
| F008 | 2 | decision | A no_decision_area | A no_decision_area | AGREE | contractor circulation stamp |
| F008 | 3 | identity | P "B01-ASC-SD-ELE-0102" | printed "B01-ASC-SD-ELE-0102-Rev.00" | AGREE* | (g)(1): label drops the labelled tail; printed form is kept in value_note |
| F008 | 3 | revision | P "00" labelled tail, res | "-Rev.00" tail | AGREE* | (g)(1) association resolved |
| F008 | 3 | decision | P "B", approved as noted, unc, inf | Status "B" on all 6 rows, unsigned, serif face | AGREE | per-item letters; association uncertain is right |
| F008 | 4 | identity | P "B01-02-ASC_EGTS-T01_L35-SD-EML-0013" (DRAWING NO.) | same | AGREE | title block |
| F008 | 4 | revision | P "00" (REVISION) | "00" | AGREE | revision cell |
| F008 | 4 | decision | P "B Approved with comments", TB, res | B cell green; 11.06.2025, Bipin Mathew | AGREE | Mirage review block |
| F009 | 1 | identity | P "B01-ASC-SD-ELE-0034" | same | AGREE | cover |
| F009 | 1 | revision | P "0" | "0" | AGREE | literal kept as printed ("0", not "00") |
| F009 | 1 | decision | P "Code B", approved as noted, res | red tick on Code B; Syed shaber 07/05/25 | AGREE | |
| F009 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page ("SD-ELE-34-(B)") |
| F009 | 3 | identity | P "B01-ASC-SD-ELE-0034" | printed "...0034-Rev.00" | AGREE* | (g)(1) |
| F009 | 3 | revision | P "00" res | "-Rev.00" | AGREE* | (g)(1) |
| F009 | 3 | decision | A blank_decision_area | Status column empty | AGREE | |
| F009 | 4 | identity | P "B01-02-ASC_EGTS-P05-SD-FA-0006" | same | AGREE | |
| F009 | 4 | revision | P "00" | "00" | AGREE | |
| F009 | 4 | decision | P "B Approved with comments", TB, res, inf | B cell pale pink; Date Reviewed and Reviewed By blank | AGREE | presence rests on the highlight alone (see section 5) |
| F013 | 1 | identity | P "B01-ASC-SD-ELE-0060" | same | AGREE | |
| F013 | 1 | revision | P "0" | "0" | AGREE | |
| F013 | 1 | decision | P "Code B", approved as noted, res | Code B red-filled and clouded; Bipin Mathew 02/06/2025 | AGREE | |
| F013 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page |
| F013 | 3 | identity | P "B01-ASC-SD-ELE-0060" | "...0060-Rev.00" | AGREE* | (g)(1) |
| F013 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F013 | 3 | decision | P "B" unc inf | Status "B" on 1 row | AGREE | |
| F013 | 4 | identity | P "B01-02-ASC_EGTS-T01_L25_34-SD-FA-0012" | same | AGREE | |
| F013 | 4 | revision | P "00" | "00" | AGREE | |
| F013 | 4 | decision | P "B Approved with comments" TB res | B green; 02.06.2025, Bipin Mathew | AGREE | |
| F020 | 1 | identity | P "B01-ASC-SD-ELE-0047" | same | AGREE | |
| F020 | 1 | revision | P "0" | "0" | AGREE | |
| F020 | 1 | decision | P "Code B" res | red tick on B, circled; Syed shaber 16/05/25 | AGREE | |
| F020 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page |
| F020 | 3 | identity | P "B01-ASC-SD-ELE-0047" | "...0047-Rev.00" | AGREE* | (g)(1) |
| F020 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F020 | 3 | decision | P "B" unc inf (rows 1–3 of 4) | "B" on rows 1–3, row 4 blank | AGREE | the note records the partial coverage |
| F020 | 4 | identity | P "B01-02-ASC_EGTS-P05-SD-FA-0008" | same | AGREE | |
| F020 | 4 | revision | P "00" | "00" | AGREE | |
| F020 | 4 | decision | P "B Approved with comments" TB res | B pale pink, red signature in Reviewed By, no date | AGREE | |
| F021 | 1 | identity | P "B01-ASC-SD-ELE-0037" | same | AGREE | |
| F021 | 1 | revision | P "00" | "00" | AGREE | |
| F021 | 1 | decision | P "Code B" res | red tick on B; Syed shaber 12/05/25 (grid lines only, not struck through) | AGREE | |
| F021 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page |
| F021 | 3 | identity | P "B01-ASC-SD-ELE-0037" | "...0037-Rev.00" | AGREE* | (g)(1) |
| F021 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F021 | 3 | decision | A blank_decision_area | Status column empty | AGREE | |
| F021 | 4 | identity | P "B01-02-ASC_EGTS-P03_P04-SD-EML-0005" | same in DRAWING NO. | AGREE | PART headings "...SD-FA-0005-01/-02/-03" are not the identity |
| F021 | 4 | revision | P "00" | "00" | AGREE | |
| F021 | 4 | decision | P "B Approved with comments" TB res | B pale pink, red signature, no date | AGREE | |
| F025 | 1 | identity | P "B01-ASC-SD-ELE-0184" | same | AGREE | |
| F025 | 1 | revision | P "00" | "00" | AGREE | |
| F025 | 1 | decision | P "Code C", revise and resubmit, res | Code C red-filled, circled; Bipin Mathew 24.09.2025 | AGREE | frozen section 5 names "code C" as revise and resubmit |
| F025 | 2 | identity | P "B01-ASC-SD-ELE-0184" | "...0184-Rev.00" (register) | AGREE* | (g)(1) |
| F025 | 2 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F025 | 2 | decision | P "C" unc inf | blue "C" on 6 rows | AGREE | |
| F025 | 3 | identity | P "B01-02-ASC_EGTS-T01_SCH-SD-EML-0030.01" | same (upright r90 crop) | AGREE | |
| F025 | 3 | revision | P "00" | "00" | AGREE | |
| F025 | 3 | decision | P "C Not Approved (Re-submit with in 14 days)" TB res | C green; 24.09.2025, Bipin Mathew | AGREE | |
| F025 | 4 | identity | P "...SCH-SD-EML-0030.02" | same | AGREE | |
| F025 | 4 | revision | P "00" | "00" | AGREE | |
| F025 | 4 | decision | P "C Not Approved (Re-submit with in 14 days)" TB res | same | AGREE | |
| F028 | 1 | identity | P "B01-ASC-SD-ELE-0048" | same | AGREE | |
| F028 | 1 | revision | P "1" | "1" | AGREE | |
| F028 | 1 | decision | P "Code B" res | B green-filled, circled; Bipin Mathew 30.09.2025 | AGREE | |
| F028 | 2 | identity / revision / decision | A / A / A no_decision_area | same ("SD-ele-48") | AGREE ×3 | circulation page |
| F028 | 3 | identity | P "B01-ASC-SD-ELE-0048" | "...0048-Rev.01" | AGREE* | (g)(1) |
| F028 | 3 | revision | P "01" | "-Rev.01" | AGREE* | (g)(1) |
| F028 | 3 | decision | P "B" unc inf | blue "B" on 5 rows | AGREE | |
| F028 | 4 | identity | P "B01-ASC-SD-ELE-0048" (Reference :) res | Al Arabia "Reply to Consultant Comments": "Reference : . B01-ASC-SD-ELE-0048 REV 00" | CANNOT DETERMINE | value correct, but frozen section 3 does not settle whether a reply sheet's "Reference" is its own number or a referenced document; resolved only by interpretation (g2) |
| F028 | 4 | revision | A ("REV 00" kept as referenced revision) | no own revision; "REV 00" names the commented submission | AGREE | |
| F028 | 4 | decision | A no_decision_area | contractor's reply sheet with "Comply" entries, no consultant mark | AGREE | |
| F030 | 1 | identity | P "B01-ASC-SD-ELE-0052" | same | AGREE | |
| F030 | 1 | revision | P "0" | "0" | AGREE | |
| F030 | 1 | decision | P "Code B+Resubmit", approved as noted, res, resubmission_required yes | "Code B+Resubmit", red box, circled; Bipin Mathew 21/05/2025 | CANNOT DETERMINE | state, literal and association agree; the class is not settled by frozen section 5 (both "code B" and "resubmit" are printed) — label relies on amendment (d1) |
| F030 | 2 | identity / revision / decision | A / A / A no_decision_area | same ("SD.ELE-0052_B+R" and a contractor note "resubmit the 'C' status comments") | AGREE ×3 | contractor notes are not decisions |
| F030 | 3 | identity | P "B01-ASC-SD-ELE-0052" | "...0052-Rev.00" | AGREE* | (g)(1) |
| F030 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F030 | 3 | decision | P "B+R" unc inf, approved as noted | "B+R" on 4 rows | CANNOT DETERMINE | same class question, (d1) |
| F030 | 4 | identity | P "B01-02-ASC_EGTS-P05-SD-FA-0010" | same | AGREE | |
| F030 | 4 | revision | P "00" | "00" | AGREE | |
| F030 | 4 | decision | P "B+R Approved with comments" TB res, approved as noted | B cell green with red "+R"; 21.05.2025, Bipin Mathew | CANNOT DETERMINE | class question, (d1) |
| F032 | 1 | identity | P "B01-ASC-SD-ELE-0075" | same | AGREE | |
| F032 | 1 | revision | P "00" | "00" | AGREE | |
| F032 | 1 | decision | P "Code B" res | B green, circled; Bipin Mathew 03.06.2025 | AGREE | |
| F032 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page |
| F032 | 3 | identity | P "B01-ASC-SD-ELE-0075" | "...0075-Rev.00" | AGREE* | (g)(1) |
| F032 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F032 | 3 | decision | P "B" unc inf | "B" on 2 rows | AGREE | |
| F032 | 4 | identity | P "B01-02-ASC_EGTS-T01_L25_34-SD-EML-0012" | same | AGREE | |
| F032 | 4 | revision | P "00" | "00" | AGREE | |
| F032 | 4 | decision | P "B Approved with comments" TB res | B green; 03.06.2025, Bipin Mathew | AGREE | |
| F034 | 1 | identity | P "B01-ASC-SD-ELE-0104" | same | AGREE | |
| F034 | 1 | revision | P "00" | "00" | AGREE | |
| F034 | 1 | decision | P "Code B" res | B green, ticked, circled; Bipin Mathew 17.06.2025 | AGREE | |
| F034 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page |
| F034 | 3 | identity | P "B01-ASC-SD-ELE-0104" | "...0104-Rev.00" | AGREE* | (g)(1) |
| F034 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F034 | 3 | decision | P "B" unc inf | "B" on 2 rows | AGREE | |
| F034 | 4 | identity | P "B01-02-ASC_EGTS-T01_L57-SD-EML-0018" | same | AGREE | |
| F034 | 4 | revision | P "00" | "00" | AGREE | |
| F034 | 4 | decision | P "B Approved with comments" TB res | B green; 11.06.2025, Bipin Mathew | AGREE | |
| F036 | 1 | identity | P "B01-ASC-SD-ELE-0109" | same | AGREE | |
| F036 | 1 | revision | P "00" | "00" | AGREE | |
| F036 | 1 | decision | P "Code B" res | B green, ticked, circled; Bipin Mathew 17.06.2025 | AGREE | |
| F036 | 2 | identity / revision / decision | A / A / A no_decision_area | same | AGREE ×3 | circulation page |
| F036 | 3 | identity | P "B01-ASC-SD-ELE-0109" | "...0109-Rev.00" | AGREE* | (g)(1) |
| F036 | 3 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F036 | 3 | decision | P "B" unc inf | "B" on 10 rows | AGREE | |
| F036 | 4 | identity | P "B01-02-ASC_EGTS-T02_L10_18-SD-EML-0021" | same | AGREE | |
| F036 | 4 | revision | P "00" | "00" | AGREE | |
| F036 | 4 | decision | P "B Approved with comments" TB res | B green; 17.06.2025, Bipin Mathew | AGREE | |
| F037 | 1 | identity | P "B01-ASC-SD-ELE-0084" | same | AGREE | |
| F037 | 1 | revision | P "0" | "0" | AGREE | |
| F037 | 1 | decision | P "Code B" res | B red, clouded; Bipin Mathew 09/06/2025 | AGREE | |
| F037 | 2 | identity | P "B01-ASC-SD-ELE-0084" | "...0084-Rev.00" (register) | AGREE* | (g)(1) |
| F037 | 2 | revision | P "00" | "-Rev.00" | AGREE* | (g)(1) |
| F037 | 2 | decision | P "B" unc inf | "B" on 1 row | AGREE | |
| F037 | 3 | identity | P "B01-02-ASC_EGTS-T01_L49_53-SD-FA-0016" | same | AGREE | |
| F037 | 3 | revision | P "00" | "00" | AGREE | |
| F037 | 3 | decision | P "B Approved with comments" TB res | B green; 09.06.2025, Bipin Mathew | AGREE | |

`other_identities`: I found no case where the label puts my identity value into `other_identities`. The plot number 3927069 / Z02.B01, the listed enclosures, the referenced drawings and the handwritten contractor notes are correctly placed there.

**3. Totals for this project** (page-level rows; there are no count-once aliases in EP-27331)

| Field | Reviewed | Agree | Disagree | Cannot determine | Status |
|---|---|---|---|---|---|
| identity | 47 | 46 (12 of them AGREE*) | 0 | 1 (F028 p4) | 12 or more cases: established by count |
| revision | 47 | 47 (12 of them AGREE*) | 0 | 0 | 12 or more cases: established by count |
| decision | 47 | 44 | 0 | 3 (F030 p1, p3, p4) | 12 or more cases: established by count |

- **Present and resolved rows agreed:**
  - Identity: 36. Only 24 if the 12 register rows dependent on (g)(1) are set aside.
  - Revision: 36. Only 24 on the same basis.
  - Decision: 22. This excludes the 10 register letters, which are uncertain by design, and the 2 F030 class questions.
- **Document level (12 documents):**
  - Identity and revision: 12 of 12 agree.
  - Decision: 11 agree plus 1 cannot determine (F030 class). That is 12 reviewed, but only 11 agreed.

**4. Critical false accepts**
None found.
- Every resolved present value matches the page.
- All 12 documents are Sea Point (J 269), EMAAR Beachfront Plot B01 submittals, so none belongs to another project.

**5. Hygiene and convention findings**
- **No mechanical problems:**
  - No missing page references or regions.
  - Every `evidence_checked` path is bound in EVIDENCE-INDEX.
  - No duplicated items, no labels pointing at the wrong document, and no scans too poor to read.
- **Convention dependence** (the value is right, but the frozen text would rule differently or does not decide):
  - **Interpretation (g)(1), 24 rows:** the 12 register identity rows drop the printed "-Rev.NN" tail, and the 12 register revision rows mark that tail as association resolved. Frozen sections 3 and 4 (literal "as printed"; an embedded revision is a suffix with association uncertain) would differ on both counts.
  - **Interpretation (g2):** F028 p4 identity.
  - **Amendment (d1):** the "B+Resubmit" / "B+R" class on F030 p1, p3 and p4.
  - **Interpretation (f):** the register status letters.
  - F025 Code C → revise and resubmit agrees with the frozen text, which names "code C".
- **Weak decision evidence:** on F009 p4 the B cell is highlighted pale pink with Date Reviewed and Reviewed By blank. F020 p4 and F021 p4 are similar, with an unnamed signature only.
- **Incomplete `other_identities` (not scored):**
  - The consultant's red notes cite other drawings: F009 p4 "B01-ASC-SD-ELE-0033 - R0", F021 p4 "B01-ASC-SD-ELE-0014 - R0", F030 p4 "B01-ASC-SD-ELE-0020-Rev.00".
  - F021 p4 has the PART headings "B01-02-ASC_EGTS-P03_P04-SD-FA-0005-01/-02/-03".
  - The "2022012-B01-..." drawing-reference rows are listed only on F008 p4.
  - Z02.B01 is listed only on F008 p1, and J269 only on F008 p2.
- **Source-side inconsistencies (not label errors):**
  - The F037 p2 register description says "37th to 48th Floor (Tier 2)", but the cover and the listed drawing are 49th–53rd (Tier 3).
  - F028 p4 prints "Plot Z01-B01" where every other page has Z02-B01. It is still the same J 269 project.
  - The F025 p2 register numbers lack the leading "B"; the label already notes this.

**6. Sign-off status**
This is an AI review, not a human sign-off. A human reviewer must still:
- rule on the F030 B+Resubmit class and the F028 p4 reply-sheet identity;
- accept or reject interpretations (g)(1), (g2), (d1) and (f) against the frozen conventions;
- confirm that the pink B highlights on F009, F020 and F021 p4 are consultant decision marks.
