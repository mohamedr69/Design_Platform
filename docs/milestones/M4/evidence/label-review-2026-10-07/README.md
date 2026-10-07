# R32 label review — summary, 7 October 2026

## 1. Header

- **Reviewed:** label set `r32-labels-reviewed-2` (`docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json`), sha256 `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6`. Every one of the six reports recomputed this hash and reports MATCH.
- **Scope:** 72 pool files staged (12 per project across the 6 frozen R32 projects). Applying the cohort's count-once rule (frozen section 1 byte-identical aliases F052→F038 and F070→F067; Review 33 interpretation (c)(ii) content-duplicate aliases F031→F001 and F059→F046 — the same four aliases recorded in `docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed-2/FIELD-POPULATION.json` `count_once_aliases`), the six reports count **68 distinct documents**, not 72: EP-3563 11, EP-29255 12, EP-27331 12, EP-22349 11, EP-26687 11, EP-15744 11 (11+12+12+11+11+11 = 68). This equals `FIELD-POPULATION.json`'s `distinct_documents.distinct_after_count_once` value of 68, which is the frozen cohort's own counting unit for "documents." (Note: the orchestrator's brief said "24 counted documents"; that is the declaration v3 scored cohort (24 documents: 16 decision-bearing, 4 revision top-ups, 4 negative controls, per the M2 closure decision), not the labelled pool. The pool reviewed here is the whole label set, 68 distinct documents after count-once; the scribe used 68 and the orchestrator confirms it.)
- **By whom:** six independent instances of the ep-label-reviewer role, each run as a general-purpose agent with the role's definition inlined, each a Claude Opus agent, each assigned exactly one project, read-only (none wrote outside its own scratchpad; none wrote to a label or repository file). Filed verbatim by the orchestrator; see `docs/SESSION-LOG-2026-10-07-windows.md` row 1a.
- **When:** 7 October 2026 (all six reports).
- **On what:** the staged PDFs and hash-bound renders/crops under `C:\t\r2x\r32-stage`. Every report recomputed source hashes against `SOURCE-MANIFEST.json` (staged PDF) and `EVIDENCE-INDEX.json` (renders, text layers, crops); **every hash matched in every project** — all six reports state this explicitly, with no NOT CHECKED or mismatched document anywhere in the cohort.
- **Method:** each reviewer read the page (render and/or bound crop) before opening the label's values for that page, and did not use file or folder names as evidence. The judging rule was the frozen `packet-inputs/LABEL-CONVENTIONS-R32.md`, read in full by each reviewer. Where a reviewer's agreement or disagreement turned on an amendment or interpretation recorded in the label file rather than on the frozen text alone, each report says so explicitly (for example EP-3563's "AGREE (C1)" caveat, EP-27331's "AGREE*" marker for interpretation (g)(1), EP-29255's and EP-22349's citations of amendment/interpretation letters in the Reason column).

## 2. Per-project table

Unit varies by report, as stated. "Documents" gives staged pool files → counted documents after the project's own count-once rule.

| Project | Documents (staged → counted) | Field | Unit | Reviewed | Agree | Disagree | Cannot determine | NOT ESTABLISHED statement (as given) |
|---|---|---|---|---|---|---|---|---|
| EP-3563 | 12 → 11 | identity | page rows (F031 p1–2 aliased into F001, not counted) | 20 | 20 | 0 | 0 | "all three fields are **NOT ESTABLISHED** for this project" — count-once units number 11, below 12 |
| EP-3563 | 12 → 11 | revision | page rows | 20 | 19 | 1 (F019 p1) | 0 | same |
| EP-3563 | 12 → 11 | decision | page rows | 20 | 20 | 0 | 0 | same |
| EP-29255 | 12 → 12 | identity | page rows | 18 | 18 | 0 | 0 | "established at page level (≥12); 14 resolved-present cases" |
| EP-29255 | 12 → 12 | revision | page rows | 18 | 16 | 2 (F024, F029) | 0 | "18 ≥12 page cases, but only 5 resolved-present values, so **NOT ESTABLISHED** for present-value accuracy in this project" |
| EP-29255 | 12 → 12 | decision | page rows | 18 | 18 | 0 | 0 | "established at page level (≥12); 15 resolved-present cases" |
| EP-27331 | 12 → 12 | identity | page rows | 47 | 46 (12 AGREE*) | 0 | 1 (F028 p4) | "12 or more cases: established by count" |
| EP-27331 | 12 → 12 | revision | page rows | 47 | 47 (12 AGREE*) | 0 | 0 | "12 or more cases: established by count" |
| EP-27331 | 12 → 12 | decision | page rows | 47 | 44 | 0 | 3 (F030 p1, p3, p4) | "12 or more cases: established by count" (document level: 11 agree + 1 cannot-determine of 12 reviewed) |
| EP-22349 | 12 → 11 | identity | page-field cases | 17 | 17 | 0 | 0 | "Page-field level: all three fields reach 12 or more matched cases, so they are established for this project" — but "Document level ... there are only 11 counted documents ... Every field is therefore **NOT ESTABLISHED** for this project at document level" |
| EP-22349 | 12 → 11 | revision | page-field cases | 17 | 17 | 0 | 0 | same page-level/document-level split; present-value cases only 3, also NOT ESTABLISHED by present value |
| EP-22349 | 12 → 11 | decision | page-field cases | 17 | 17 | 0 | 0 | same split; present-value cases only 7 |
| EP-26687 | 12 → 11 | identity | page cases (count-once: F059 under F046) | 13 | 13 | 0 | 0 | "Page cases ≥ 12; but only 11 counted documents, so **NOT ESTABLISHED** on the document unit" |
| EP-26687 | 12 → 11 | revision | page cases | 13 | 13 | 0 | 0 | "**NOT ESTABLISHED** (9 present values; 11 documents)" |
| EP-26687 | 12 → 11 | decision | page cases | 13 | 13 | 0 | 0 | "**NOT ESTABLISHED** (5 present values; 11 documents)" |
| EP-15744 | 12 → 11 | identity | page items (count-once: F070 under F067) | 26 | 26 | 0 | 0 | "**NOT ESTABLISHED**" — counted per document after count-once, only 11 reviewed cases, under 12 |
| EP-15744 | 12 → 11 | revision | page items | 26 | 26 | 0 | 0 | same |
| EP-15744 | 12 → 11 | decision | page items | 26 | 26 | 0 | 0 | same |

Note on EP-26687's raw figure: before applying its own count-once rule, the report's per-item table lists 42 page-field rows (14 labelled pages × 3 fields), all AGREE, 0 DISAGREE, 0 CANNOT DETERMINE ("Result: all 42 page-field rows agree with the pages"). The 13-per-field figure above is after folding F059 under F046, which is the unit the report's own totals table and NOT ESTABLISHED statement use.

**Critical false accepts, by project (all six say none in the strict sense):**
- EP-3563: none found.
- EP-29255: none found; project-membership flags raised for F002, F023, F027 (see section 4).
- EP-27331: none found.
- EP-22349: none found; project-membership flag raised for F035 (see section 4).
- EP-26687: none found.
- EP-15744: none found; project-membership flags raised for F043, F071, F069 (see section 4).

## 3. Cohort totals (sum of the six reports' page-field rows, per field)

Using each report's own per-field totals (EP-26687 and EP-15744's counted-once figures, as in section 2):

| Field | Reviewed | Agree | Disagree | Cannot determine |
|---|---|---|---|---|
| Identity | 20+18+47+17+13+26 = **141** | 20+18+46+17+13+26 = **140** | 0 | 1 |
| Revision | 20+18+47+17+13+26 = **141** | 19+16+47+17+13+26 = **138** | 3 | 0 |
| Decision | 20+18+47+17+13+26 = **141** | 20+18+44+17+13+26 = **138** | 0 | 3 |

(Each field's reviewed count sums to 141 because every labelled page contributes one row per field across the cohort; agree + disagree + cannot determine reconciles to 141 for each field.)

**Every DISAGREE row:**

| Project | Document | Page | Field | Reason (one line) |
|---|---|---|---|---|
| EP-3563 | F019 | 1 | revision | Label reads ambiguous/excluded under amendment D-005; reviewer found "00" present in the Rev. no. cell, which frozen section 4 treats as the primary source over the conflicting register-table row "01" — a conservative disagreement, not a false accept. |
| EP-29255 | F024 | 1 | revision | Label asserts a resolved absence under interpretation (g2); the page's only revision string is the "-R02" suffix of the REF NO, which frozen section 4 (embedded-only case) scores as present/suffix/uncertain, not absent. |
| EP-29255 | F029 | 1 | revision | Same reasoning as F024: frozen section 4 gives present/suffix/uncertain against the label's resolved absence under (g2). |

**Every CANNOT DETERMINE row:**

| Project | Document | Page | Field | Reason (one line) |
|---|---|---|---|---|
| EP-27331 | F028 | 4 | identity | Value is correct, but frozen section 3 does not settle whether a reply sheet's "Reference" is its own number or a referenced document; resolved only by interpretation (g2). |
| EP-27331 | F030 | 1 | decision | State, literal and association agree, but the "Code B+Resubmit" class is not settled by frozen section 5 (both "code B" and "resubmit" are printed); the label relies on amendment (d1). |
| EP-27331 | F030 | 3 | decision | Same class question as F030 p1 (amendment (d1)), applied to the register's "B+R" letters. |
| EP-27331 | F030 | 4 | decision | Same class question as F030 p1 (amendment (d1)), applied to the title-block "B+R Approved with comments" cell. |

## 4. Critical false accepts

All six reports state none found in the strict sense (no wrong value labelled as a resolved present value). Several reviewers raised project-membership flags instead, explicitly as matters for human ruling, not as false accepts:

- **EP-29255** (verbatim): "Project-membership flag for human ruling. These documents are labelled `ep: 29255` and `resolved_for_scoring: yes`, but their pages print other projects: F002 p1: 'PROPOSED B+G+5+R RESIDENTIAL BUILDING … Plot No. JVC10QMRP200' (Modular Design / TAK). F002 p2 and p4: 'Project : Riva Residence, Plot No. O-4B at Dubai Maritime City'. F023: 'RESIDENTIAL BLOCKS (CITYWALK)', dated 2014. F027: 'Project : Creek View-02, Residential + Commercial Building … Dubai Health Care City'. ... The label states this openly. ... These would become critical false accepts if any gate metric treats `ep` as project-binding truth, for example a 'document belongs to this project' check. A human must rule on whether these 4 files stay in the EP-29255 scoring population."
- **EP-22349** (verbatim): "F035 project content (risk, not an error): the file is staged under EP-22349 but holds earlier approvals on four other projects. These are EMAAR/Mirage, Emarat/Al Burj, Expo/MUSE Angola Pavilion and DHA/Hosmac. Its four resolved identities, three resolved revisions and three resolved decisions are not EP-22349 facts. If a gate counts them toward EP-22349 at document level, it would be counting another project's documents as this project's. A human must decide whether F035 belongs in this project's field populations."
- **EP-15744** (verbatim): "F043: pages 1–4 are a generic Military Works Command 2014 letter (ش إ م / عام/٢٠١٤ / ١٣٢٤) and the 'CMW General Specifications Annexure B' vendor list. Nothing on these pages shows EP-15744 or 17045. The label's `ep` cannot be confirmed from the pages, yet F043 counts in this project's identity and revision populations. F071: the header says 'CME-17045 @ ALI MINHAD', but every EASE image on pages 2–4 is stamped 'Project: Malleha Camp' / '(c) EASE 4.4 / Malleha Camp'. The calculation images may be reused from another project's model. All labelled values are absent, so there is no false accept. F069: page 1 reads 'Command Of Military Works 17045 at Al minhad', but page 3 reads 'CMW 17045 at Al Awir'. The location differs within one file."

## 5. Convention questions the reviewers raised that need a human ruling

- **Amendment (d1), "approved as noted / resubmit" class:** EP-3563's caveat C1 (the "Approved as noted / Resubmit" option carries both an approval and a resubmit marker; the class `approved as noted` follows the label file's amendment (d1), not the frozen text alone — applies to 5 rows); EP-27331's "B+Resubmit"/"B+R" class question on F030 p1, p3 and p4.
- **Interpretation (g)(1), register "-Rev.NN" tails:** EP-27331 — 24 register rows (12 identity, 12 revision) drop or resolve the printed "-Rev.NN" tail against the frozen literal/association rule; flagged for accept-or-reject against the frozen conventions.
- **Interpretation (g2), reply-sheet reference as identity/revision:** EP-27331 F028 p4 identity (CANNOT DETERMINE, whether a reply sheet's "Reference" is its own number or a referenced document); EP-29255 F024 and F029 revision (the label's resolved-absence reading under (g2) versus frozen section 4's present/suffix/uncertain reading — the two DISAGREE rows in section 3).
- **D-005, F019 revision:** EP-3563 — whether the page's Rev. no. cell ("00") or the register's conflicting "01" row governs, and whether the label's ambiguous/excluded reading (resting on amendment D-005) is correct.
- **Count-once of content duplicates:** EP-3563 F031/F001 (content duplicate, not byte-identical — hygiene item H2; human sign-off item 3 asks whether F031 counts once with F001); EP-26687 F059/F046 (human sign-off asks for the owner's acceptance of the F059→F046 count-once amendment).
- **Interpretation (f), register status letters:** EP-27331 — the register status letters (B, C, etc.) depend on interpretation (f), listed among the interpretations to accept or reject.
- **F038 approved vs. approved-as-noted:** EP-22349 — whether F038's Civil Defence initial drawings approval is class "approved" or "approved as noted," given the generic listed conditions and the "APPROVED WITH COMMENTS" mark of AJ Training & Consultancy, including whether AJ acts for the authority (the page does not establish this).
- **F035 p3, ambiguous vs. class other:** EP-22349 — whether F035 p3's partly-approving handwritten decision ("Samples not new & delapidated ... Samples for AX-T605L & AX-T632L are approved") should be "ambiguous" (the label's state, chosen as conservative) or "present, class other" under convention section 5.
- **F024/F029 revision, absent vs. suffix-uncertain:** EP-29255 — the ruling between frozen section 4 and amendment/interpretation (g2) for these two revisions (same rows as the DISAGREE list in section 3).

## 6. Hygiene findings, grouped

**Stale open items**
- EP-26687: F039 and F040 still list "p1 revision only as the '-R0' suffix ... (association uncertain)" under `unresolved`, although the reviewed rows now read absent; F059 still says "reviewer to rule whether F046 and F059 count once" and F046 says "near-duplicate of F059," although count-once was adopted. Bookkeeping only; the rows themselves are correct.

**`other_identities` gaps**
- EP-3563 (H5, optional): referenced drawing numbers not recorded in other_identities — F010 "FAM-PIV-MAH-SPD-FAS-2633-002 A & B" and "…-002 D," and the IFC refs "FA/102" / "FA/107."
- EP-22349 (item 2): F048 and F049 both print "OLD APPLICATION NUMBER 2020 - 4 - 1072822," which the label omits from other_identities while F042, F044, F047, F051, F053 and F054 record it; F047 also gives it a different role wording. Does not affect the identity field.
- EP-27331: consultant red notes cite other drawings not recorded (F009 p4 "B01-ASC-SD-ELE-0033 - R0," F021 p4 "B01-ASC-SD-ELE-0014 - R0," F030 p4 "B01-ASC-SD-ELE-0020-Rev.00"); F021 p4's PART headings; the "2022012-B01-..." drawing-reference rows listed only on F008 p4; Z02.B01 listed only on F008 p1, J269 only on F008 p2.
- EP-26687 (item 2): other_identities is empty for the whole project, although the field appears 113 times elsewhere in the label file; JOB.NO. 19-23, PLOT NO 3620619, and the SDAR drawing numbers FA-6001/EM-104 are mentioned only in review notes, not structured. Does not affect scoring.

**Literal boundary inconsistencies**
- EP-29255 (H1): on F002 p1 the identity literal excludes the red "B R1," yet the revision is labelled "suffix of the printed document number" — the identity literal rule is not applied the same way as on the NBC-JGH forms (non-scoring, since revision there is uncertain).
- EP-15744: F043's revision literal is recorded as "Rev. 0" (with the printed prefix kept), while other labels (e.g. F067 "00") record the value only — scorers must normalise.
- EP-15744: F043 mixes two documents at file level — identity comes from the page 1 cover letter, revision from the pages 2–4 annex (D-003); a scorer pairing identity with revision per file would pair values from two different documents.

**Note-only errors**
- EP-3563 (H1): F012 p1 revision `value_note` says "00 05-05-16 ISSUED FOR APPROVAL," but the page prints "00 05-03-16 ISSUED FOR APPROVAL." Note-only; the scored value "01" is unaffected.
- EP-22349 (item 4): F038 p3's decision notes do not mention the blue handwritten review comments on the drawing, which bear on the approved/approved-as-noted question in section 5 above.
- EP-15744: F067's stamp date digit is uncertain ("10" or "18"), but the label states "10 MAY 2017" as fact.

**Hyphen/space normalisation**
- EP-26687 (item 3): the text layer of F039 p1, F040 p1 and F072 uses U+2010 hyphens, while the label literals use ASCII "-"; rendering can't distinguish them, so the scorer should normalise.
- EP-15744: F067's drawing number may have a space after "C001-" that is ambiguous in the raster; flagged for normalisation.
- EP-3563 and EP-29255: several identities are printed with or without a space before a trailing revision letter (e.g. EP-3563 F012 "...007 A", F033 "...004 A"; EP-29255 F002 p1 "...EL-013" followed by a separately-coloured "B R1") — the reports keep the literal as printed in each case.

**Other mechanical hygiene (no value errors)**
- EP-22349 (item 3): two evidence references on F038 cite bare render file names rather than the hash-bound crop path — both still refer to correct locations.
- EP-29255 (H3): evidence references mix bare crop names and full paths — cosmetic.
- EP-22349 (item 5): F048 and F054 both print sheet number "FA-05" for different drawings; the label flags this, and scoring must key on the document, not the literal.
- EP-26687 (item 4): nothing on F066 itself ties it to EP-26687 (only EST/Carrier/EATON logos and an Al Arabia footer); its membership rests on staging metadata, not page evidence. All three fields are absent, so this does not affect scoring.
- EP-27331: source-side inconsistencies that are not label errors — F037 p2's register description says "37th to 48th Floor (Tier 2)" against the cover/listed drawing's 49th–53rd (Tier 3); F028 p4 prints "Plot Z01-B01" where every other page has Z02-B01 (still the same J269 project); the F025 p2 register numbers lack the leading "B" (already noted by the label).
- No report found a missing page reference, a duplicated item (beyond the declared count-once aliases), a label pointing at the wrong document, or a scan too poor to read.

## 7. What this review establishes and does not

This is a **third, independent AI review** of the same label set `r32-labels-reviewed-2` — distinct from the drafting pass and from the independent review/consolidation passes already recorded against this file (`AI-ACCURACY-POLICY-AMENDMENT-R32-01.md` section "Record of how the controls are met"). All six reviewer agents were independent of the drafting and reviewing agents of the label set and of each other, read-only, one project each.

Under `AI-ACCURACY-POLICY-AMENDMENT-R32-01` (`docs/milestones/M4/evidence/policy-2026-10-07/AI-ACCURACY-POLICY-AMENDMENT-R32-01.md`), this label set — and this review of it — may be cited only as: **"reference set independently AI-reviewed (Claude agents), not human-signed."** It must not be described as human-signed labels, human Golden Truth, or independently human-verified evidence.

It does **not** satisfy:
- `M2-ACCEPTANCE-MATRIX.md` gate **G9** ("Manually verified Golden cases from originals ... labels independently checked, not solely by another model"): G9's existing evidence already records "No human-signed set exists; amendment R32-01 admits the AI-reviewed `r32-labels-reviewed-2` for the R32 cohort only," and its remaining gap — "Outside R32 every label set is AI-authored or AI-reviewed" — is unchanged by this review, which is itself AI-only;
- the roadmap's **M4 closure item 4** ("Label review outside the run-specific amendment"), which this repository's own readiness survey (`docs/milestones/M4/README.md`) records as "not accepted" because the labels are "AI-reviewed only." A third AI review does not change that status.

**What a human reviewer must still confirm** (the union of the six reports' section-6 / sign-off lists, deduplicated):

- EP-3563: whether F019 p1 revision is "00" (from the cell) or ambiguous; whether the decision class for "Approved as noted / Resubmit" is `approved as noted` (amendment d1) or `revise and resubmit`; whether F031 counts once with F001 (a content duplicate, not a byte duplicate); the F010 decision mark, a stroke continuing from the reviewer's initials.
- EP-29255: whether F002, F023 and F027 (other projects' documents) belong in EP-29255's scoring population; the ruling between frozen section 4 and interpretation (g2) for the F024 and F029 revisions; the F002 p1 literal boundary, plus the low-resolution F023 reading ("273 / MT / MEP 2 1 7," tick at B).
- EP-27331: the ruling on the F030 B+Resubmit class and the F028 p4 reply-sheet identity; whether to accept or reject interpretations (g)(1), (g2), (d1) and (f) against the frozen conventions; whether the pink B highlights on F009, F020 and F021 p4 are consultant decision marks.
- EP-22349: whether F035, a compilation of other projects' approvals, may count toward EP-22349 field populations; whether F038's Civil Defence initial approval is class "approved" or "approved as noted," including whether AJ Training & Consultancy acts for the authority; whether F035 p3's partly-approving decision should be "ambiguous" or "present, class other."
- EP-26687: the five consultant decision marks (F039 p1/p2, F040 p1/p2, F072 p1); that the "-R0" description suffixes on F039 p1 and F040 p1 are correctly left out as the page's revision; the owner's acceptance of the F059→F046 count-once amendment and of F066 belonging to the project.
- EP-15744: the Arabic literal on F043 p1; the ruling that F061's DCD issuer "يعتمد" block is not a decision; F067's stamp meaning, date and actor; the ruling (D-004) between "ambiguous" and "absent" for F069; whether F043 and F071 truly belong to EP-15744.
