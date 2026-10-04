# M2 Preparation Review 33, dimension D3: label truth, conventions and the escalations (image-based)

**Agent:** R33-D3, task ORCH-03.1/D3. Claude Opus 5.5 (claude-opus-5-5), effort high. This is a fresh, isolated agent, independent of the drafter, the R32REV-* reviewers and the R32APPLY-* implementer.

**Status:** This is an owner-delegated independent Claude AI review, not human sign-off. It authorises nothing. M2 stays CHANGES STILL REQUIRED, and M3 has not started.

**Method:** I read the bound staged images myself (renders `C:/t/r2x/r32-stage/renders/F###-pN.png` and crops `C:/t/r2x/r32-stage/crops/*.png`). Working zooms, pixel diffs and contact sheets in my scratchpad (`r33-d3/`) are derived views, not evidence. No model or provider request was made. File names were never used as evidence.

## 1. Commands run

- `sha256sum` on all frozen inputs and on the staged PDFs (D3-01).
- Python, read-only: flatten R32-LABELS-REVIEWED-1.json into 432 page-field rows (`rows.json`) and draw the deterministic sample (`sample.py`). The sample is every 10th accept row per field, ordered by (pool_id, page), taking indices 9, 19, 29 and so on.
- Pillow, with the venv python and PYTHONDONTWRITEBYTECODE=1, no package scripts: pixel diffs F001/F031 and F046/F059 (`cmp.py`, `cmp2.py`), zooms and rotations (`zoom.py`), contact sheets (`stack.py`, `grid.py`, `g4.py`, `dec.py`, `dec2.py`).
- grep of `apply_rulings_r32.py`, `PREPARATION-REPORT.md` and `review31/scripts/harness/*.py`.

Nothing outside my scratchpad and these three output files was written.

## 2. Findings

### D3-01 (info, CONFIRMED)

**Claim:** The label inputs this dimension relies on match their frozen hashes.

**Evidence:** sha256sum: R32-LABELS-DRAFT-1.json ebd1e24d...a334; LABEL-CONVENTIONS-R32.md 5c09d4d2...e570; FROZEN-SELECTION.json bf71779a...5d21; CROPS.jsonl b1760b64...cd1ff; EVIDENCE-INDEX.json 0d0db4f8...08b8; fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json 15c4114d...d0ed; REVIEWER-RESPONSE.final.json 920a21d6...4c5b; REVIEWER-RESPONSE.json 70f94632...ff8; CRITIQUE.json ad6798dc...7eef; DISPOSITIONS.json e8828bec...0a7; R32-LABELS-REVIEWED-1.json 00e53e82...9379; fresh-cohort-r32-reviewed/evidence/EVIDENCE-MANIFEST.json 64c03667...31c6. Staged byte duplicates re-hashed: F038 = F052 = 6f2e35f3...0d53, F067 = F070 = 7b7e3a7a...1d55. FIELD-POPULATION.json (no frozen hash given) is 5b9cf095...4505.

**Required action:** None.

### D3-02 (info, CONFIRMED)

**Claim:** Stratified image verification of r32-labels-reviewed-1 refutes no row.

**Evidence:** 98 items checked against the staged renders and crops: all 47 rows ruled 'correct', the 3 unresolved rows, all 9 rows with resubmission_required, 38 accept rows (every 10th accept row per field ordered by (pool_id, page): identity 12, revision 12, decision 13, plus 1 supplement F035 p1 decision because the every-10th rule gave no decision row from project 22349; together they cover all six projects 3563, 22349, 27331, 15744, 26687 and 29255), and the 2 added other_identities (F047 p1 '2020 - 4 - 1072822' under 'OLD APPLICATION NUMBER'; F028 p4 '00' under 'REV'). 95 CONFIRMED, 0 REFUTED, 3 escalated rows ruled separately (D3-03). Per-row results are in D3-report.md. Two sub-points cannot be confirmed: the F067 p1 actor (the Arabic arc of the stamp is not legible to me) and the case of the second 'Samples' in the F035 p3 literal. Both rows are ambiguous and not scored.

**Required action:** None for the sampled rows. Disclose that the verification is a sample (98 of 432 page-field rows plus added entries), not a full re-read.

### D3-03 (major, CONFIRMED)

**Claim:** Escalations D-004 (F069 identity) and D-005 (F019 revision) are still open in the reviewed package. This dimension rules D-004 = ambiguous and D-005 = present '00' under the frozen text.

**Evidence:** D-004: renders F069-p1 (Design Sheet 5-Aug-18, 'Refrence : EP-15744', Quotation for Fire Alarm System) and F069-p3 (4-Aug-18, same 'Refrence : EP-15744', Quotation for Emergency Lighting System); F062-p1 'Project ID : EP-15744', Document No. EP-15744/SM/FAS/201; F068-p1 'Oracle Job No. / OM No.' EP-15744. All are documents of the same issuer, Al Arabia. Frozen section 2 ties 'ambiguous' to what the page establishes, and using other documents to set the role is the (h2) addition, which is not an owner amendment. Result: ambiguous, F069 identity no/no. The gate is unchanged: identity stays 57. D-005: crop F019-p1-0.03_0.84_0.2_1-r90 shows 'Rev. no.' 00 and DATE 09-05-16; the render's revision table shows 00 05-03-16 ISSUED FOR APPROVAL and 01 09-05-16 AS PER CONSULTANT COMMENTS. Frozen section 4 makes the cell the primary source and uses the table only when it is the only source, so the frozen text decides the candidate: present '00', resolved, F019 revision yes/yes, and the revision population goes 38 -> 39. Under the topic (i) amendment it would be ambiguous and stay 38. Details are in D3-escalation-rulings.json.

**Required action:** Before the declaration, the owner or the preparation review must close D-004 and D-005: adopt these rulings or adopt (h2)/(i) as explicit amendments. Then write the ruled states into the label version and recount (identity 57; revision 39 under these rulings, 38 if (i) is adopted; decision 38).

### D3-04 (major, CONFIRMED)

**Claim:** Final convention (c)(ii) counts content duplicates (render-identical pages) once. This amends frozen section 1, which counts only byte-identical files once. It changes all three populations, and it is not recorded or escalated as an amendment, unlike (h2) and (i).

**Evidence:** Frozen section 1: only 'byte-identical staged files (F038 = F052, F067 = F070)' count once. (c)(ii) adds F031->F001 and F059->F046, and FIELD-POPULATION applies both ('content duplicates F031->F001, F059->F046 by final convention (c)'). Without the aliases the gate counts would be identity 59, revision 40 and decision 39, against 57/38/38. Image checks: F001-p1/p2 vs F031-p1/p2 differ by 0 pixels. F046-p1 vs F059-p1 differ by more than 64 grey levels in only 1,183 pixels, all inside x 0.842-0.883, y 0.856-0.912 (the Al Arabia round seal, present on F046 only); the title blocks are identical. Caveat: F031 has pages p3-p4 (a Dewan Comments Resolution Sheet with 'MAT - 116', 'Rev.: 02') that F001 lacks, so '(in-scope pages that carry the field facts are render-identical)' is not literally true for F031 p3. Its values equal F001's, so no new fact is added.

**Required action:** List (c)(ii) in the declaration as an amendment to frozen section 1, with the F031 p3 caveat, for owner or preparation-review acceptance. Otherwise revert to byte-identical-only counting (59/40/39). Both pass the gate of 12.

### D3-05 (minor, CONFIRMED)

**Claim:** Final convention (d1) classes 'Approved as noted / Resubmit', 'Code B+Resubmit' and 'B+R' as 'approved as noted' and adds resubmission_required. This departs from frozen section 5, which lists 'resubmit' as a marker of 'revise and resubmit'. It is not recorded as an amendment, and the scorer tolerance it relies on is not defined.

**Evidence:** All 9 affected rows checked on the image: F001 p2 and F031 p2 (red tick on 'Approved as noted / Resubmit'); F017 p1, F022 p1, F026 p1 and F033 p1 (Dewan REVIEW NOTE mark on 'APPROVED AS NOTED / RESUBMIT'); F030 p1 ('Code B' filled with '+Resubmit' added), F030 p3 (register 'B+R') and F030 p4 (Mirage 'B+R', B 'Approved with comments' green). The marks are where the labels say. The class reading is defensible because separate revise and reject options exist and are unmarked, but it is an interpretation of the frozen text.

**Required action:** Record (d1) and the resubmission_required field as an amendment or interpretation in the declaration. Define the scorer tolerance concretely: which predicted classes score correct on these 9 rows, which belong to 6 counted documents.

### D3-06 (minor, CONFIRMED)

**Claim:** Final convention (e) as amended by D-001 overrides frozen section 5's 'not approved' marker for the EMAAR/Mirage code C. The ruling text says so, but it was disposed as 'adopted' rather than escalated as a convention amendment, which is inconsistent with how D-004 and D-005 were treated.

**Evidence:** Crop F025-p1-0.1_0.69_0.93_0.715: Code C box filled red and ringed. The Mirage legend reads 'C Not Approved (Re-submit with in 14 days)' with D 'Incomplete, Resubmit' (crops F037-p3-0.86_0.19_0.99_0.27 and F034-p4-0.84_0.19_0.98_0.275 show the same printed legend). Frozen section 5 maps 'code C, resubmit' to revise and resubmit and 'code D, not approved' to rejected, so the frozen markers conflict for this legend. The (e) reading (revise and resubmit) is the defensible resolution. Affected: the F025 p1/p3/p4 class and the p2 register letter. No population changes.

**Required action:** Add (e)/D-001 to the declaration's list of convention amendments.

### D3-07 (minor, CONFIRMED)

**Claim:** Several final rulings add interpretive rules to the frozen text without labelling them as amendments: (g)(1), (g2), (h)/D-003, (d2) and (f). Only D-003 changes a population.

**Evidence:** (g)(1) stores the identity of 12 register pages without the labelled tail (e.g. crop F034-p3: 'Submittal Ref: B01-ASC-SD-ELE-0104-Rev.00', identity 'B01-ASC-SD-ELE-0104') and lets a scorer accept either form, whereas frozen section 3 keeps the literal 'as printed'. (g2) excludes a labelled 'REV 00' on a reply sheet from the page revision (render F028-p4, 'Reference : . B01-ASC-SD-ELE-0048 REV 00' inside a Rev.01 package); this departs from section 4's labelled-REV-field source but follows its 'own current revision' wording. (h)/D-003 makes the F043 p2-p4 running-header 'Rev. 0' resolved (crop F043-p2-0_0_0.2_1-r270, confirmed) and moves F043 revision no/no -> yes/yes, so the revision population goes 37 -> 38; this applies frozen section 7. (d2) and (f) add classes of non-decisions and register-letter handling consistent with section 5. Image checks for every sampled row under these rulings: CONFIRMED.

**Required action:** List these rulings in the declaration as interpretations of the frozen conventions, and state that D-003 changes the revision population by +1.

### D3-08 (minor, CONFIRMED)

**Claim:** The reviewed label file stores the unresolved F069 p1/p3 identity rows as state 'present', literal 'EP-15744'. The final response and D-004 record state 'ambiguous', and neither escalation option supports 'present'.

**Evidence:** R32-LABELS-REVIEWED-1.json documents.F069.pages.1/3.identity: state 'present', literal 'EP-15744', review_status 'unresolved', excluded_from_scoring true. REVIEWER-RESPONSE.final.json page_field_rulings F069 p1/p3 identity: ruling 'unresolved', state 'ambiguous'. apply_rulings_r32.py line 143: 'unresolved: keep the draft values'. For F019 the draft value was already ambiguous, so only F069 is affected. FIELD-POPULATION excludes F069 correctly.

**Required action:** When D-004 is closed, write the ruled state (ambiguous per D3-03). Until then, any consumer must honour excluded_from_scoring, and the declaration should say so.

### D3-09 (major, UNVERIFIABLE)

**Claim:** The carried-over items depend on scorer rules that no scorer bound to the r32 labels implements, as far as the packages I may read show: count-once aliases, page-keyed scoring of compilations (F002, F035, F043, F069), whitespace-insensitive literal comparison (F023, F067, 'FA- 6001', 'EM- 104', LACASA '- R0n'), either-form identity for labelled '-Rev.0n' tails, and resubmission tolerance.

**Evidence:** review31/scripts/harness/score_lane.py scores lanes through the application evaluator against the frozen r26.2 labels. Its literal comparison is in the candidate source tree, which this dimension may not open. fresh-cohort-r32-reviewed contains count_population_r32.py and apply_rulings_r32.py but no scorer. grep for whitespace/normalisation in review31/scripts/harness returned only labelling text. The rules exist only as prose in the convention rulings.

**Required action:** Before the declaration, bind a scorer for the r32 labels that implements these rules, with tests on the named rows (F023, F067, F040/F046/F059, F005-F007/F011, F002/F035/F043, the 9 resubmission rows and the register tails).

### D3-10 (info, CONFIRMED)

**Claim:** Counting the LACASA/Scale '- R0n' suffixes as revisions would be a convention change that needs an owner decision.

**Evidence:** Crops F005-p1-0.1_0.215_0.92_0.33, F006-p1-0.4_0.22_0.8_0.245, F007-p1-0.45_0.2_0.85_0.215 and F011-p1-0.45_0.205_0.85_0.22: the only revision source is the unlabelled suffix of the Reference. Frozen section 4 'embedded only' makes it present with association uncertain, and frozen section 7 counts only resolved values. Counting the suffixes would contradict both and could add up to 8 revision documents (F002, F003, F004, F005, F006, F007, F011, F015).

**Required action:** None unless the owner wants the suffixes counted; that would need an explicit amendment to sections 4 and 7.

### D3-11 (info, CONFIRMED)

**Claim:** Decision truth: every decision row ruled present or ambiguous names the reviewing party (consultant, authority, or the PMC/client on ambiguous rows), never the contractor. The 12 rows with actor_state 'inferred' are defensible, and none of them carries a counted fact on its own.

**Evidence:** All 81 decision rows with state present or ambiguous were viewed on their regions. The actors seen are: Dewan REVIEW NOTE stamps; LACASA forms and stamps; Mirage code boxes and review blocks (Bipin Mathew, Syed shaber, M.H Sr. Resident Engineer); AREX stamp and signatures (Arun Menon, Sam Gopinathan); Khatib & Alami 'FOR ENGINEER'S USE ONLY'; Modular Design; Al Burj Resident Engineer; Hosmac 'For Consultants'; Trevor Maltman 'For Engineer'; Dubai Civil Defence approved-plans stamps (F014, F016); the Ajman Civil Defence letter and 'Initial Drawings Approval' stamps (F038); the du 'No Objection' Building NOC (F027). Contractor circulation stamps (F020 p2, F028 p2, F032 p2), reply sheets (F024, F028 p4) and contractor code restatements are labelled absent. Inferred rows: 10 register Status letters (F008, F013, F020, F025, F028, F030, F032, F034, F036 p3 and F037 p2; uncertain association, never counted under (f)); F009 p4 (Mirage printed block with B highlighted but date and reviewer blank; the document decision is carried by p1 'Code B' with a named reviewer); F067 p1 (ambiguous; the stamp's Arabic arc is not legible to me, so the 'client' actor is UNVERIFIABLE, but the row is not scored).

**Required action:** None.

### D3-12 (info, CONFIRMED)

**Claim:** Label truth status of r32-labels-reviewed-1: AI-drafted, then AI-reviewed by independent Claude agents, and not human-signed. This dimension refuted 0 rows.

**Evidence:** The reviewed file's status field reads 'AI-reviewed: owner-delegated independent Claude AI review (R32REV-B1..B7, CONSOLIDATE, CRITIC, DISPOSE; Claude Opus 5.5 High); NOT human-signed; NOT a human review'. Frozen section 8 says the drafts are AI-authored. This D3 check is a further independent Claude review of a 98-item sample: 0 refuted, 3 escalated rows ruled, 2 sub-points unverifiable. Two open escalations and the unrecorded amendments (D3-04 to D3-07) remain.

**Required action:** In the declaration, state the labels as AI-drafted and AI-reviewed, not human-signed, and do not present them as human ground truth.

## 3. Check 1: final convention rulings against the frozen LABEL-CONVENTIONS-R32.md

There are 16 rulings: (a), (b), (c), (d1), (d2), (e), (f), (g), (g2), (h), (h2), (i), (i2), (j), (k) and (m). Five of them carry a disposition: (e) D-001, (g2) D-002, (h) D-003, (h2) D-004 and (i) D-005.

| Ruling | Relation to the frozen text | Recorded as amendment? | Population effect |
|---|---|---|---|
| (a) association_note | Tightens section 2 ('with a note') | Not needed | None |
| (b) evidence binding | Consistent with section 6 | Not needed | None |
| (c)(i) byte duplicates | Equals section 1 | n/a | Already frozen |
| (c)(ii) content duplicates F031->F001, F059->F046 | **Amends section 1**, which is byte-identical only | **No** | Identity -2, revision -2, decision -1 (57/38/38 against 59/40/39) |
| (d1) mixed options = approved as noted, plus resubmission_required | **Departs from section 5's literal 'resubmit' marker** and adds a schema field and a scorer tolerance | **No** | Class only, on 9 rows |
| (d2) authority approvals and non-decisions | Adds detail to section 5; consistent | No (interpretation) | None found |
| (e) legend governs the code class; D-001 | **Explicitly overrides section 5's 'not approved' marker** for Mirage/EMAAR C | Stated in the text, disposed 'adopted', **not escalated** | Class of F025 rows |
| (f) register status letters | Applies section 2 association; never counts | Not needed | None |
| (g)(1) labelled '-Rev.0n' tail | Identity stored **without** the tail, against section 3 'literal as printed'; scorer accepts either form | **No** | None (register pages only) |
| (g)(2) unlabelled suffix | Equals section 4 'embedded only' | n/a | None |
| (g)(3) revision of another document | Applies section 4 'page's own' | Not needed | F039 and F040 p1 re-ruled absent (no count effect) |
| (g2) reply sheets; D-002 | Interprets section 4 (a labelled REV on a reply sheet is not the page revision) and adds an identity rule | **No** (D-002 adopted) | Revision resolved_for_scoring only (F024, F029 yes/no) |
| (h) compilations; D-003 | Page-keyed truth applies sections 1 and 7; D-003 resolves the F043 header 'Rev. 0' | Disposition, not an amendment | **Revision +1** (F043) |
| (h2) Reference = job number | **Adds to section 3** | **Yes, escalated (D-004)** | Identity resolved_for_scoring only |
| (i) ambiguous/illegible; cell-vs-table conflict | Conflict sentence **amends section 4** | **Yes, escalated (D-005)** | Revision ±1 (F019) |
| (i2) literal form, whitespace-insensitive scorer | Labels comply with section 3; the comparison is a scorer rule | Not a convention change | None |
| (j) regions, (k) rotated crops, (m) stamp location | Procedural, consistent with section 6 | Not needed | None |

## 4. Check 2: stratified verification against the page images (98 items)

The sample:

- all 47 'correct' rows;
- the 3 unresolved rows;
- all 9 resubmission_required rows (one of them is also a 'correct' row);
- 37 every-10th accept rows (identity 12, revision 12, decision 13), plus 1 supplement (F035 p1 decision), because the every-10th rule gave no decision row from project 22349;
- the 2 added other_identities.

The accept rows cover all six projects in every field except decision for project 22349, which the supplement fills. Result: **0 REFUTED**, 95 CONFIRMED, and 3 rows ruled under D-004/D-005.

| Pool | Proj | Page | Field | Selected as | Reviewed state | Literal / class | Verdict | What the image shows |
|---|---|---|---|---|---|---|---|---|
| F001 | 3563 | 2 | decision | resub:yes | present | Approved as noted / Resubmit / approved as noted | CONFIRMED | Red tick on 'Approved as noted / Resubmit'; separate 'Revise / Resubmit' and 'Rejected / Resubmit' options unticked (render F001-p2, crop F001-p2-0.05_0.72_0.6_0.76). |
| F005 | 29255 | 1 | identity | correct | present | NBC-JGH-SCALE-SDS-MEP-ELE-CCTV-2025-0004- R00 | CONFIRMED | 'Reference: NBC-JGH-SCALE-SDS-MEP-ELE-CCTV-2025-0004- R00' printed with a space before R00 (crop F005-p1-0.1_0.215_0.92_0.33). |
| F005 | 29255 | 1 | revision | correct | present | R00 | CONFIRMED | Only source is the unlabelled '- R00' suffix of the Reference; attachment-table '00' belongs to enclosed drawing EC-103 (same crop). Present/uncertain per frozen section 4 embedded-only. |
| F006 | 29255 | 1 | decision | accept-10th | present | APPROVED AS NOTED / approved as noted | CONFIRMED | Pen stroke through the 'APPROVED AS NOTED' box in the ACTION (As Marked) row, Reviewed By signature (crop F006-p1-0.18_0.6_0.82_0.66). |
| F006 | 29255 | 1 | identity | correct | present | NBC-JGH-SCALE-MAS-MEP-ELE-LC-2025-007- R02 | CONFIRMED | 'Reference: NBC-JGH-SCALE-MAS-MEP-ELE-LC-2025-007- R02' (crop F006-p1-0.4_0.22_0.8_0.245). |
| F006 | 29255 | 1 | revision | correct | present | R02 | CONFIRMED | R02 only as suffix of the Reference; present/uncertain. |
| F006 | 29255 | 2 | revision | correct | present | R02 | CONFIRMED | 'Submittal Ref No. : NBC-JGH-SCALE-MAS-MEP-ELE-2025-007-R02' (no '-LC-', no space); R02 only as suffix; present/uncertain (crop F006-p2-0.2_0.22_0.7_0.31). |
| F007 | 29255 | 1 | identity | accept-10th | present | NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0009- R00 | CONFIRMED | 'Reference: NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0009- R00' (crop F007-p1-0.45_0.2_0.85_0.215). |
| F007 | 29255 | 2 | revision | accept-10th | present | 00 | CONFIRMED | Title block 'REVISION: 00' beside DRAWING NO EA-201 (crop F007-p2-0.81_0.92_0.99_0.98). |
| F009 | 27331 | 3 | decision | accept-10th | absent |  | CONFIRMED | Drawing register, Status column empty for all four rows (render F009-p3). |
| F010 | 3563 | 1 | identity | accept-10th | present | FAM-PIV-MAH-SPD-FAS-2633-002C | CONFIRMED | 'DWG. NO: FAM-PIV-MAH-SPD-FAS-2633-002C', Rev. no. 02 (crop F010-p1-0.86_0.9_0.98_0.97). |
| F011 | 29255 | 1 | revision | accept-10th | present | R00 | CONFIRMED | 'Reference: NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0010- R00'; suffix only, uncertain. |
| F014 | 3563 | 1 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Round Dubai Civil Defence approved-plans stamp, red Arabic 'approved plans' text, 253708-37-1, 15/01/17, plot 6742010; yellow 'APPROVED' box separate (crop F014-p1-0.84_0.02_1_0.35). |
| F014 | 3563 | 2 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Same Civil Defence stamp text on this sheet (crop F014-p2-0.84_0.02_1_0.35). |
| F014 | 3563 | 3 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Same Civil Defence stamp text (crop F014-p3-0.84_0.02_1_0.35). |
| F014 | 3563 | 3 | identity | accept-10th | present | 103B | CONFIRMED | Split cells: DISCIPLINE 'FP', DRAWING NO. '103B', REVISION 01; drawing-number cell = identity (crop F014-p3-0.9_0.9_0.99_0.98). |
| F014 | 3563 | 4 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Same Civil Defence stamp text (crop F014-p4-0.84_0.02_1_0.35). |
| F014 | 3563 | 4 | revision | accept-10th | present | 01 | CONFIRMED | REVISION cell '01' beside DRAWING NO. 103C (crop F014-p4-0.9_0.9_0.99_0.98). |
| F015 | 29255 | 1 | decision | accept-10th | present | APPROVED AS NOTED / approved as noted | CONFIRMED | Blue ellipse around 'APPROVED AS NOTED' in the ACTION (As Marked) row (crop F015-p1-0.1_0.78_0.8_0.83). |
| F016 | 3563 | 1 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Civil Defence approved-plans stamp, same text (crop F016-p1-0.84_0.02_1_0.35). |
| F016 | 3563 | 2 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Same stamp (crop F016-p2-0.84_0.02_1_0.35). |
| F016 | 3563 | 3 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Same stamp (crop F016-p3-0.84_0.02_1_0.35). |
| F016 | 3563 | 4 | decision | correct | present | مخططات معتمدة / approved | CONFIRMED | Same stamp (crop F016-p4-0.84_0.02_1_0.35). |
| F017 | 3563 | 1 | decision | resub:yes | present | APPROVED AS NOTED / RESUBMIT / approved as noted | CONFIRMED | Dewan REVIEW NOTE stamp, red arrow into 'APPROVED AS NOTED / RESUBMIT' (crop F017-p1-0.88_0.58_0.95_0.7). |
| F019 | 3563 | 1 | revision | unresolved | ambiguous |  | RULED (see escalation rulings D-004 / D-005) | See D-005 ruling: cell 'Rev. no.' 00; table rows 00 05-03-16 ISSUED FOR APPROVAL and 01 09-05-16 AS PER CONSULTANT COMMENTS; title-block DATE 09-05-16. |
| F020 | 27331 | 1 | identity | correct | present | B01-ASC-SD-ELE-0047 | CONFIRMED | 'Submittal Ref.No. B01-ASC-SD-ELE-0047' (crop F020-p1-0.16_0.15_0.92_0.168). |
| F020 | 27331 | 1 | revision | correct | present | 0 | CONFIRMED | 'Rev. No.' cell '0' (same crop). |
| F020 | 27331 | 2 | identity | accept-10th | absent |  | CONFIRMED | Contractor J269 CIRCULATION stamp with handwritten 'SD-ELE-47 (B)'; no printed own number (render F020-p2). |
| F020 | 27331 | 4 | revision | accept-10th | present | 00 | CONFIRMED | 'REVISION 00' beside DRAWING NO. B01-02-ASC_EGTS-P05-SD-FA-0008 (crop F020-p4-0.86_0.955_0.995_0.985). |
| F021 | 27331 | 1 | identity | correct | present | B01-ASC-SD-ELE-0037 | CONFIRMED | 'Submittal Ref.No. B01-ASC-SD-ELE-0037' (crop F021-p1-0.16_0.152_0.92_0.17). |
| F021 | 27331 | 1 | revision | correct | present | 00 | CONFIRMED | 'Rev. No.' cell '00'. |
| F021 | 27331 | 3 | decision | accept-10th | absent |  | CONFIRMED | Register Status column empty for rows 1-5 (crop F021-p3-0.03_0.15_0.8_0.5). |
| F022 | 3563 | 1 | decision | resub:yes | present | APPROVED AS NOTED / RESUBMIT / approved as noted | CONFIRMED | Dewan REVIEW NOTE stamp, red pen stroke into 'APPROVED AS NOTED / RESUBMIT' (crop F022-p1-0.23_0.9_0.33_1-r90). |
| F022 | 3563 | 1 | revision | correct | present | 00 | CONFIRMED | 'Rev. no.' 00 beside DWG. NO FAM-PIV-MAH-SPD-CBS-2633-004C (render F022-p1, rotated). |
| F023 | 29255 | 1 | identity | correct | present | 273 / MT / MEP 2 1 7 | CONFIRMED | 'MAS Ref. No. 273 / MT / MEP 2 1 7' with wide letter-spacing (crop F023-p1-0.2_0.25_0.8_0.3). |
| F023 | 29255 | 1 | revision | correct | present | 00 | CONFIRMED | 'Revision No.' red '00' (same crop). |
| F024 | 29255 | 1 | identity | correct | present | NBC-JGH-SCALE-MAS-MEP-ELE-LC-2025-007-R02 | CONFIRMED | 'CONSULTANT COMMENTS / REF NO: NBC-JGH-SCALE-MAS-MEP-ELE-LC-2025-007-R02' on a contractor (Al Arabia seal) reply table; answered submittal's number, association uncertain (render F024-p1). |
| F024 | 29255 | 1 | revision | correct | absent |  | CONFIRMED | Only the R02 suffix of the answered submittal's reference; absent per (g2). |
| F025 | 27331 | 1 | decision | correct | present | Code C / revise and resubmit | CONFIRMED | Code C box filled red and ringed blue; legend C 'Not Approved (Re-submit within 14 days)'; Electrical Bipin Mathew (crop F025-p1-0.1_0.69_0.93_0.715). |
| F025 | 27331 | 4 | identity | accept-10th | present | B01-02-ASC_EGTS-T01_SCH-SD-EML-0030.02 | CONFIRMED | 'DRAWING NO. B01-02-ASC_EGTS-T01_SCH-SD-EML-0030.02', REVISION 00 (crop F025-p4-0_0.85_0.1_1-r90). |
| F026 | 3563 | 1 | decision | correct; resub:yes | present | APPROVED AS NOTED / RESUBMIT / approved as noted | CONFIRMED | Dewan REVIEW NOTE stamp beside the title block, red stroke into 'APPROVED AS NOTED / RESUBMIT', 31.7.16 (crop F026-p1-0.8_0.03_0.94_0.1-r270). |
| F026 | 3563 | 1 | revision | correct | present | 00 | CONFIRMED | 'Rev. no.' 00 (crop F026-p1-0.8_0.03_0.94_0.1-r270). |
| F028 | 27331 | 2 | decision | accept-10th | absent |  | CONFIRMED | Contractor circulation stamp only (handwritten 'SD-ele-48'), no decision area (render F028-p2). |
| F028 | 27331 | 2 | revision | accept-10th | absent |  | CONFIRMED | No revision source on the circulation page. |
| F028 | 27331 | 4 | revision | correct | absent |  | CONFIRMED | 'Reference : . B01-ASC-SD-ELE-0048 REV 00' on the Al Arabia 'Reply to Consultant Comments' sheet, Subject 'Consultant Comments on 6TH FLOOR...'; package is Rev.01 (register p3 'B01-ASC-SD-ELE-0048-Rev.01'); absent per (g2), 00 kept as other identity (render F028-p4). |
| F029 | 29255 | 1 | identity | correct | present | NBC-JGH-SCALE-MAS-MEP-ELE-2025-018-R00 | CONFIRMED | 'Reference : NBC-JGH-SCALE-MAS-MEP-ELE-2025-018-R00', Subject 'Reply to comments for SCS Rev.00' (crop F029-p1-0.08_0.08_0.6_0.13). |
| F029 | 29255 | 1 | revision | correct | absent |  | CONFIRMED | R00 names the commented submission; absent per (g2). |
| F030 | 27331 | 1 | decision | resub:yes | present | Code B+Resubmit / approved as noted | CONFIRMED | Code B box filled red, '+Resubmit' added after 'Code B', ringed red (crop F030-p1-0.11_0.7_0.93_0.725). |
| F030 | 27331 | 3 | decision | resub:yes | present | B+R / approved as noted | CONFIRMED | Register Status 'B+R' on all four rows (crop F030-p3-0.03_0.15_0.8_0.5). |
| F030 | 27331 | 4 | decision | resub:yes | present | B+R Approved with comments / approved as noted | CONFIRMED | Mirage block heading 'B+R' with red '+R', B 'Approved with comments' cell green; 21.05.2025, Bipin Mathew (crop F030-p4-0.84_0.19_0.975_0.27). |
| F030 | 27331 | 4 | identity | accept-10th | present | B01-02-ASC_EGTS-P05-SD-FA-0010 | CONFIRMED | 'DRAWING NO. B01-02-ASC_EGTS-P05-SD-FA-0010', REVISION 00 (crop F030-p4-0.84_0.935_0.98_0.97). |
| F031 | 3563 | 2 | decision | resub:yes | present | Approved as noted / Resubmit / approved as noted | CONFIRMED | Pixel-identical to F001 p2 (0 differing pixels); tick on 'Approved as noted / Resubmit' (crop F031-p2-0.05_0.72_0.6_0.76). |
| F031 | 3563 | 3 | decision | accept-10th | absent |  | CONFIRMED | Dewan 'Comments Resolution Sheet' (Submittal No.: MAT - 116, Rev.: 02): contractor responses and consultant handwritten remarks, no decision option or mark (render F031-p3). |
| F032 | 27331 | 1 | identity | correct | present | B01-ASC-SD-ELE-0075 | CONFIRMED | 'Submittal Ref.No. B01-ASC-SD-ELE-0075' (crop F032-p1-0.16_0.155_0.92_0.172). |
| F032 | 27331 | 1 | revision | correct | present | 00 | CONFIRMED | 'Rev. No.' 00. |
| F032 | 27331 | 2 | revision | accept-10th | absent |  | CONFIRMED | Contractor circulation stamp 'SD-ELE-75' only; no revision (render F032-p2). |
| F033 | 3563 | 1 | decision | resub:yes | present | APPROVED AS NOTED / RESUBMIT / approved as noted | CONFIRMED | Dewan REVIEW NOTE stamp, red stroke into 'APPROVED AS NOTED / RESUBMIT', 17.8.16 (render F033-p1 region). |
| F034 | 27331 | 1 | identity | correct | present | B01-ASC-SD-ELE-0104 | CONFIRMED | 'Submittal Ref.No. B01-ASC-SD-ELE-0104' (crop F034-p1-0.16_0.158_0.92_0.175). |
| F034 | 27331 | 1 | revision | correct | present | 00 | CONFIRMED | 'Rev. No.' 00. |
| F034 | 27331 | 3 | identity | accept-10th | present | B01-ASC-SD-ELE-0104 | CONFIRMED | 'Submittal Ref: B01-ASC-SD-ELE-0104-Rev.00' on the register; identity without the labelled tail per (g)(1) (crop F034-p3-0.03_0.15_0.8_0.4). |
| F034 | 27331 | 4 | decision | accept-10th | present | B Approved with comments / approved as noted | CONFIRMED | Mirage block, B 'Approved with comments' green, 11.06.2025, Bipin Mathew (crop F034-p4-0.84_0.19_0.98_0.275). |
| F035 | 22349 | 2 | revision | correct | ambiguous | 2 | CONFIRMED | 'Rev. No.' cell holds a handwritten 'X' and a circled '2'; readable, role not established: ambiguous (crop F035-p2-0.65_0.13_0.98_0.21). |
| F035 | 22349 | 3 | decision | correct | ambiguous | Samples not new & delapidated. Replace samples (of good condition) for | CONFIRMED | Handwritten mixed outcome: two samples to replace, two approved; no status box. State ambiguous confirmed. The case of the second 'Samples' is not certain on the image (the reviewer wrote lower case); immaterial because ambiguous rows are not scored (crop F035-p3-0.15_0.52_0.95_0.75). |
| F036 | 27331 | 1 | revision | accept-10th | present | 00 | CONFIRMED | 'Rev. No.' 00 beside 'Submittal Ref.No. B01-ASC-SD-ELE-0109' (crop F036-p1-0.15_0.162_0.92_0.18). |
| F037 | 27331 | 1 | identity | accept-10th | present | B01-ASC-SD-ELE-0084 | CONFIRMED | 'Submittal Ref.No. B01-ASC-SD-ELE-0084', Rev. No. 0 (crop F037-p1-0.16_0.15_0.92_0.168). |
| F037 | 27331 | 3 | decision | accept-10th | present | B Approved with comments / approved as noted | CONFIRMED | Mirage block, B 'Approved with comments' green and red-framed, 09.06.2025, Bipin Mathew (crop F037-p3-0.86_0.19_0.99_0.27). |
| F038 | 22349 | 4 | revision | accept-10th | absent |  | CONFIRMED | Sheet FF-02 title block has no revision cell; the Civil Defence 'Initial Drawings Approval' stamp carries no revision (render F038-p4). |
| F039 | 26687 | 1 | revision | correct | absent |  | CONFIRMED | 'Ref. No.SDAR-MEP-FA-6001' has no suffix; '-R0' ends the description line 'FA-6001 SCHEMATIC DIAGRAM FIRE ALARM LAYOUT-R0' of the enclosed drawing; absent per (g)(3) (render F039-p1). |
| F039 | 26687 | 2 | decision | correct | present | B Approved As Noted / approved as noted | CONFIRMED | AREX SHOP DRAWING REVIEW STATUS stamp, B 'Approved As Noted' ticked, Date 18-09-2023; review-table codes B (crop F039-p2-0.61_0.78_1_0.97). |
| F040 | 26687 | 1 | revision | correct | absent |  | CONFIRMED | 'Ref. No.SDAR-MEP-EM-104' has no suffix; '-R0' ends the description of enclosed EM-104; absent (render F040-p1). |
| F040 | 26687 | 2 | identity | accept-10th | present | EM- 104 | CONFIRMED | 'DWG-NO:EM- 104' with a space, REV - 0 (crop F040-p2-0.88_0.9_1_0.97). |
| F043 | 15744 | 1 | decision | accept-10th | absent |  | CONFIRMED | Arabic cover letter forwarding approved material lists; no review decision area (render F043-p1). |
| F043 | 15744 | 1 | identity | correct | present | ش إ م / عام/٢٠١٤ / ١٣٢٤ | CONFIRMED | Letter number after the Arabic 'number' label, as recorded (crop F043-p1-0.45_0.15_0.95_0.3). |
| F043 | 15744 | 2 | identity | correct | ambiguous |  | CONFIRMED | Running header 'Command of Military Works - CMWGENERAL SPECIFICATIONSANNEXU RE B - Rev. 0 -DATE:5-3-2014'; no labelled document number; ambiguous (crop F043-p2-0_0_0.2_1-r270). |
| F043 | 15744 | 2 | revision | correct | present | Rev. 0 | CONFIRMED | Header 'Rev. 0' labelled, belonging to the page's own annex (same crop). |
| F043 | 15744 | 3 | identity | correct | ambiguous |  | CONFIRMED | Same running header as p2 (crop F043-p3-0_0_0.2_1-r270). |
| F043 | 15744 | 3 | revision | correct | present | Rev. 0 | CONFIRMED | Header 'Rev. 0' (same crop). |
| F043 | 15744 | 4 | identity | correct | ambiguous |  | CONFIRMED | Same running header (crop F043-p4-0_0_0.2_1-r270). |
| F043 | 15744 | 4 | revision | correct | present | Rev. 0 | CONFIRMED | Header 'Rev. 0' (same crop). |
| F048 | 22349 | 1 | revision | accept-10th | absent |  | CONFIRMED | Title block (FA-05, plot 0815, job 000, date 15/03/2022) has no revision cell (render F048-p1). |
| F050 | 26687 | 1 | decision | accept-10th | absent |  | CONFIRMED | AREX/ENCO drawing EM-100, no review stamp or status area (render F050-p1). |
| F051 | 22349 | 1 | identity | accept-10th | present | EM-15 | CONFIRMED | 'SHEET NO. EM-15' is the only drawing number in the title block (crop F051-p1-0.87_0.84_1_0.98). |
| F059 | 26687 | 1 | revision | accept-10th | present | 0 | CONFIRMED | 'REV - 0' beside DWG-NO:FA- 6001 (crop F059-p1-0.88_0.9_1_0.96). |
| F061 | 15744 | 1 | decision | accept-10th | absent |  | CONFIRMED | Dubai Civil Defence agent licence K18 with the issuer's own authentication stamp and signature; not a review decision per (d2) (render F061-p1). |
| F061 | 15744 | 2 | identity | accept-10th | present | K18 | CONFIRMED | Licence number K18 in the licence-number box (render F061-p2). |
| F061 | 15744 | 4 | identity | correct | present | K18 | CONFIRMED | Licence number K18 (render F061-p4). |
| F064 | 15744 | 3 | revision | accept-10th | absent |  | CONFIRMED | TOA manual page 5-56, no revision source (render F064-p3). |
| F065 | 15744 | 1 | decision | accept-10th | absent |  | CONFIRMED | TOA/Al Arabia Schedule of Equipment, no stamp or status area (render F065-p1). |
| F067 | 15744 | 1 | decision | correct | ambiguous | (round stamp dated 10 MAY 2017 with a signature in the AUTHORITIES APP | CONFIRMED | AUTHORITIES APPROVAL box: round stamp '10 MAY 2017' plus a signature, no decision wording; ambiguous confirmed. The Arabic arc is not legible to me at render resolution, so the actor 'Command of Military Works' is UNVERIFIABLE; the state is CONFIRMED (render F067-p1, crop F067-p1-0.82_0.74_0.99_0.95). |
| F067 | 15744 | 1 | identity | accept-10th | present | CMW-17045-C001-01-E-0001 | CONFIRMED | 'DRAWING NO. CMW-17045-C001-01-E-0001' (crop F067-p1-0.82_0.74_0.99_0.95). |
| F067 | 15744 | 1 | revision | correct | present | 00 | CONFIRMED | 'REVISION No. 00' (same crop). |
| F069 | 15744 | 1 | identity | unresolved | present | EP-15744 | RULED (see escalation rulings D-004 / D-005) | See D-004 ruling: 'Refrence : EP-15744', Design Sheet 5-Aug-18, Quotation for Fire Alarm System (render F069-p1). |
| F069 | 15744 | 3 | identity | unresolved | present | EP-15744 | RULED (see escalation rulings D-004 / D-005) | See D-004 ruling: 'Refrence : EP-15744', Design Sheet 4-Aug-18, Quotation for Emergency Lighting System (render F069-p3). |
| F071 | 15744 | 2 | revision | accept-10th | absent |  | CONFIRMED | SPL/STI calculation image page; header 'CME-17045 @ ALI MINHAD) - SPL/STI CALCULATION'; no revision (render F071-p2). |
| F071 | 15744 | 4 | decision | accept-10th | absent |  | CONFIRMED | Calculation conclusion only; no review area (render F071-p4). |
| F035 | 22349 | 1 | decision | accept-supplement: first 22349 decision accept row by (pool_ | present | B / approved as noted | CONFIRMED | ENGINEER'S COMMENTS boxes A/B/C/R, B ticked, 'REFER THE ...' comment (render F035-p1). |
| F047 | 22349 | 1 | other_identities (added) | added other identity |  | 2020 - 4 - 1072822 | CONFIRMED | Title block 'OLD APPLICATION NUMBER 2020 - 4 - 1072822', printed with spaces; equals the F038 p1 letter number 2020-4-1072822 (render F047-p1, crop F038-p1-0.05_0.19_0.95_0.47). |
| F028 | 27331 | 4 | other_identities (added) | added other identity |  | 00 | CONFIRMED | 'REV 00' after 'Reference : . B01-ASC-SD-ELE-0048' on the reply sheet (render F028-p4). |

## 5. Check 3: escalation rulings

Full details are in `D3-escalation-rulings.json`.

### D-004: F069 p1/p3 identity

**Ruling: AMBIGUOUS.**

What the pages show:

- F069 p1 and p3 are two Al Arabia 'Design Sheet' quotations (5-Aug-18 fire alarm; 4-Aug-18 emergency lighting). Both print 'Refrence : EP-15744', and nothing else could be an own number.
- F062 p1, an Al Arabia transmittal, prints 'Project ID : EP-15744' and Document No. EP-15744/SM/FAS/201.
- F068 p1, an Al Arabia T&C request form, prints 'Oracle Job No. / OM No.' EP-15744.

Why ambiguous:

- That evidence, and the repeat of the value on two quotations, rules out 'present'.
- Frozen section 2 defines 'ambiguous' by what the page establishes. Using other documents to fix the role is the (h2) addition to section 3, which is not an owner amendment.

Result:

- Rows: ambiguous, with candidate EP-15744 under 'Refrence'.
- Document: F069 identity resolved_for_scoring no, carries_fact no.
- Gate count unchanged: identity 57.
- If the owner adopts (h2), the state becomes absent, and F069 identity becomes resolved_for_scoring yes, still carries_fact no.
- Package defect: the reviewed file still stores state 'present' on these rows (D3-08).

### D-005: F019 p1 revision

**Ruling: PRESENT '00' under frozen section 4.**

What the page shows:

- The cell 'Rev. no.' reads 00.
- The table rows read 00 05-03-16 ISSUED FOR APPROVAL and 01 09-05-16 AS PER CONSULTANT COMMENTS.
- The title-block DATE is 09-05-16.

Why present '00':

- Section 4 names the revision cell the primary source and uses the table only when it is the only source. The frozen text therefore decides which candidate is the field, so section 2's 'ambiguous' does not apply.
- The (i) conflict sentence is an amendment.

Result:

- Row: present '00', label 'Rev. no.', association resolved, with the table row 01 recorded in a note.
- Document: F019 revision yes/yes.
- Revision population 38 -> 39.
- Disclosure: the matching dates suggest the cell may be stale. If the owner adopts (i), the row is ambiguous and the revision population stays 38.

## 6. Check 4: carried-over items

- **F031 -> F001:**
  - p1-p2 renders are pixel-identical (0 px).
  - F031 has an extra Comments Resolution Sheet (p3: MAT - 116, Rev.: 02) with the same values as F001.
  - Count once is defensible, but (c)(ii)'s literal condition is not met for p3, and (c)(ii) is an unrecorded amendment (D3-04).
- **F059 -> F046:**
  - The only difference is the Al Arabia round seal: 1,183 px above 64 grey levels, in x 0.842-0.883, y 0.856-0.912. The title blocks are identical.
  - CONFIRMED.
- **Page-keyed scoring of F002, F035 and F043:**
  - Required, because the pages are different documents.
  - It is consistent with section 7, but no scorer for the r32 labels is bound (D3-09).
- **Whitespace-insensitive comparison** (F023, F067, LACASA '- R0n', 'FA- 6001', 'EM- 104'):
  - The labels keep the printed form, as section 3 requires.
  - The comparison is a scorer rule, not a convention change, and it must be bound.
- **LACASA/Scale '- R0n':**
  - Counting the suffixes would contradict sections 4 and 7, so it is a convention change and needs an owner decision (D3-10).
- **resubmission_required:**
  - All 9 marks were confirmed on the image.
  - (d1) departs from the literal frozen section 5 and is unrecorded; the scorer tolerance is undefined (D3-05).

## 7. Check 5: decision truth

I viewed the regions of all 81 decision rows ruled present or ambiguous.

- Every actor is a consultant, an authority, or (on ambiguous rows only) the PMC or client. None is the contractor.
- Contractor circulation stamps, reply sheets and code restatements are labelled absent.
- 12 rows have actor_state 'inferred':
  - 10 register Status letters, which never count under (f);
  - F009 p4: a Mirage printed review block with B highlighted, date and reviewer blank. Defensible; the document decision rests on p1, where the reviewer is named;
  - F067 p1: ambiguous, and the actor is unverifiable to me. It is not scored.
- The Civil Defence approvals carry only generic printed conditions: the F038 letter and 'Initial Drawings Approval' stamps, and the F014/F016 approved-plans stamps. Classing them 'approved' follows (d2).

## 8. Check 6: label truth status

r32-labels-reviewed-1 is:

- **AI-drafted** (Claude);
- **AI-reviewed by independent Claude agents** (R32REV-B1..B7, CONSOLIDATE, CRITIC, DISPOSE), and now sample-checked by this D3 agent;
- **not human-signed**.

Rows refuted by this dimension: **0** of 95 sampled page-field rows; the 2 added other_identities were also confirmed. Open items:

- D-004 and D-005;
- the unrecorded amendments (D3-04 to D3-07);
- the unbound scorer rules (D3-09).

## 9. Counts

| Field | Reviewed gate count | With D3 rulings | Without the (c)(ii) aliases |
|---|---|---|---|
| identity | 57 | 57 | 59 |
| revision | 38 | 39 (38 if topic i is adopted) | 40 (41 with the D-005 ruling) |
| decision | 38 | 38 | 39 |

Every alternative stays at or above the gate minimum of 12.
