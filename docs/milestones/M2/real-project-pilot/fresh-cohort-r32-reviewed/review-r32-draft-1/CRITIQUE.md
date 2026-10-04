# Critique of the consolidated label review (r32-labels-draft-1)

**Task:** ORCH-01A.4, agent R32REV-CRITIC, Claude Opus 5.5 (`claude-opus-5-5`), effort High.

**Reviewed:** [REVIEWER-RESPONSE.json](REVIEWER-RESPONSE.json), sha256 `70f94632884af028f31d66f76557807801cf00fcca37251a2ade25c9de3a3ff8`.

This is an owner-delegated independent Claude AI critique under owner decision A-03. It is **not** human sign-off. M2 is still **CHANGES STILL REQUIRED**, and M3 has not started.

## What I examined

| Scope | Count |
|---|---|
| Non-accept page-field rulings | 46 (all) |
| Document-field rows with a 'no' | 73 (all) |
| Convention rulings | 16 (each checked on at least two affected pages) |
| Accept sample: every 4th accept row by (pool_id, page, field), plus the accept rows with uncertain association | 97 + 19 = 109 distinct |
| Renders and crops opened (approximate) | 170 |

I opened only staged renders and crops, and my own magnifications of them. I opened no forbidden path, ran no packet script and made no model or network request.

## Disagreements

There are 8 disagreements. 6 of them are material.

### C-001: topic=(e) class of a code letter: tie-breaker clause vs the EMAAR/Mirage legend, pool_id=F025, field=decision

**Material:** yes. Changes a convention rule (e); as worded the rule can change the class of the F025 p1, p3 and p4 decisions.

**Reviewer ruling:** Topic (e): 'Not Approved (Re-submit within 14 days)' = revise and resubmit, but also 'where one legend prints both a revise option and a separate rejection option, the rejection option is rejected even if it adds Resubmit'. Stated consequence: EMAAR/Mirage C and D = revise and resubmit, so F025 p1/p3/p4 Code C = revise and resubmit.

**Critic view:** The Mirage legend prints C 'Not Approved (Re-submit with in 14 days)' and D 'Incomplete, Resubmit'. Read literally, D is the revise option and C is a separate option that opens with 'Not Approved'. The tie-breaker would then make C 'rejected', which contradicts the ruling's own stated consequence and the F025 rows. The frozen conventions section 5 also lists 'not approved' under rejected. The F025 class revise and resubmit is defensible, because the C option carries its own resubmission instruction. The tie-breaker still has to be reworded, for example: 'an option counts as a rejection option only when it carries no resubmission instruction of its own'. The reviewed version should also say explicitly that Mirage C overrides the 'not approved' marker in section 5. As worded, a preparation step that applies (e) mechanically can flip three F025 page decisions and the F025 document class.

**Evidence:** C:/t/r2x/r32-stage/crops/F025-p1-0.1_0.69_0.93_0.715.png (Code C box filled red and ringed blue; legend on C:/t/r2x/r32-stage/renders/F025-p1.png); C:/t/r2x/r32-stage/crops/F025-p3-0.69_0.85_0.81_1-r90.png and C:/t/r2x/r32-stage/crops/F025-p4-0.69_0.85_0.81_1-r90.png (C 'Not Approved (Re-submit with in 14 days)' highlighted green, D 'Incomplete, Resubmit', Bipin Mathew 24.09.2025)

### C-002: pool_id=F006, page=2, field=revision

**Material:** yes. Changes the page state for F006 p2 revision (present/uncertain -> absent) and the wording of convention g2 (identity association condition).

**Reviewer ruling:** correct: present 'R02', suffix of the printed document number, association uncertain (note added). Topic (g2) lists F006 p2 identity as resolved because the reference 'equals the own number of a submittal in the same staged file'.

**Critic view:** F006 p2 is the LACASA consultant comment sheet. It prints 'Submittal Ref No. : NBC-JGH-SCALE-MAS-MEP-ELE-2025-007-R02', with no '-LC-' and no space before R02. The p1 form Reference is 'NBC-JGH-SCALE-MAS-MEP-ELE-LC-2025-007- R02'. The two literals are not equal, so g2's own identity condition ('equals') is not met, yet p2 identity is kept resolved. g2's revision clause makes a revision printed with that reference the page revision only when it is labelled and equals the current revision; otherwise the page revision is absent and the value is kept as referenced_revision. R02 here is unlabelled, so under g2 the p2 revision should be absent (referenced_revision R02), not present/uncertain. There are two fixes. (a) Re-rule F006 p2 revision to absent, and reword the g2 identity condition to 'names the same submittal (same serial and revision; a project-code infix difference is allowed)'. (b) Or take the consultant's own comment sheet out of g2. As issued, the row and the convention contradict each other. The document-level F006 revision stays no/no either way, because p1 has a suffix only.

**Evidence:** C:/t/r2x/r32-stage/renders/F006-p2.png ('Submittal Ref No. : NBC-JGH-SCALE-MAS-MEP-ELE-2025-007-R02', underlined 'Approved as Noted', signed Mohamad El Haj); C:/t/r2x/r32-stage/crops/F006-p1-0.4_0.22_0.8_0.245.png ('Reference: NBC-JGH-SCALE-MAS-MEP-ELE-LC-2025-007- R02'); C:/t/r2x/r32-stage/crops/F006-p2-0.2_0.22_0.7_0.31.png

### C-003: pool_id=F043, field=revision

**Material:** yes. Changes association (uncertain -> resolved) on F043 p2-p4 revision and the F043 document revision resolved_for_scoring/carries_fact (no/no -> yes/yes); otherwise it requires a change to convention (h).

**Reviewer ruling:** F043 p2-p4 revision accept: present 'Rev. 0', association uncertain ('belongs to the enclosed annex, not to the cover letter that is the file's lead document'). F043 document revision: resolved_for_scoring no, carries_fact no ('depends on which component is the document').

**Critic view:** This contradicts topic (h), which the same response adopts. Under (h) a compilation's truth is page-level, and 'each in-scope page's field belongs to that page's own document'. The running header on pages 2-4 is the header of the page's own document and labels the value: 'Command of Military Works - CMW GENERAL SPECIFICATIONS ANNEXU RE B - Rev. 0 - DATE:5-3-2014'. Under (h) this is a labelled revision of the page's own document (the annex), with association resolved. The p1 letter simply has no revision. An ambiguous page identity does not make a labelled revision on the same page uncertain, and (h) gives no such rule. Critic ruling: p2-p4 revision present 'Rev. 0', association resolved; F043 revision resolved_for_scoring yes, carries_fact yes (page-level). If the consolidator wants a 'lead document' rule instead, it must be added to (h) and applied to F002, F035 and F069 as well.

**Evidence:** C:/t/r2x/r32-stage/crops/F043-p2-0_0_0.2_1-r270.png, C:/t/r2x/r32-stage/crops/F043-p3-0_0_0.2_1-r270.png, C:/t/r2x/r32-stage/crops/F043-p4-0_0_0.2_1-r270.png (running header with 'Rev. 0'); C:/t/r2x/r32-stage/renders/F043-p1.png (letter, no revision)

### C-004: topic=(h2) project or job number under a 'Reference' label, pool_id=F069, field=identity

**Material:** yes. Changes convention h2 and, depending on the fix, the F069 p1/p3 identity state (ambiguous vs absent) and F069 identity resolved_for_scoring.

**Reviewer ruling:** Topic (h2): a value under 'Reference' that is a project or job number makes the identity ambiguous. 'It counts as a project or job number when staged pages of the same project print it as such or distinct documents share it verbatim.' F069 p1/p3 corrected from present to ambiguous; F069 identity resolved_for_scoring no.

**Critic view:** There are two defects. (1) The second test, 'distinct documents share it verbatim', is over-broad. F038 p1's own letter number '2020-4-1072822' (label 'الرقم') is shared verbatim: it is the transaction number on the F038 p2-p4 Civil Defence stamps, and the 'OLD APPLICATION NUMBER 2020 - 4 - 1072822' on F047, F048 and F049. Yet it is correctly the letter's identity. The test should be limited to values that some staged page prints with a project or job role. That narrower test already covers F069: F062 prints 'Project ID : EP-15744' and F068 prints 'Oracle Job No. / OM No.' EP-15744. (2) The rule contradicts itself. Once its own test establishes the role as a project or job number, conventions section 3 makes the value an other identity, and the identity is absent (no own number printed), not ambiguous ('role cannot be established'). Either rule absent when the cross-document test is met (F069 identity resolved_for_scoring yes, carries_fact no), or keep ambiguous and drop the cross-document test. The F069 state and its resolved_for_scoring depend on which.

**Evidence:** C:/t/r2x/r32-stage/renders/F069-p1.png and C:/t/r2x/r32-stage/renders/F069-p3.png ('Refrence : EP-15744' on both quotations); C:/t/r2x/r32-stage/renders/F062-p1.png ('Project ID : EP-15744'); C:/t/r2x/r32-stage/renders/F068-p1.png ('Oracle Job No. / OM No.' EP-15744); C:/t/r2x/r32-stage/crops/F038-p1-0.05_0.19_0.95_0.47.png ('الرقم: 2020-4-1072822'); C:/t/r2x/r32-stage/crops/F038-p2-0.62_0.72_0.88_0.97.png (stamp transaction 2020-4-1072822); C:/t/r2x/r32-stage/renders/F047-p1.png ('OLD APPLICATION NUMBER 2020 - 4 - 1072822')

### C-005: pool_id=F019, page=1, field=revision

**Material:** yes. Changes state (ambiguous vs present '00') and F019 revision resolved_for_scoring; amends frozen convention section 4.

**Reviewer ruling:** accept: ambiguous (cell 00 vs latest table entry 01). Topic (i) adds 'A labelled revision cell that disagrees with the latest revision-table entry on the same page is ambiguous ... not resolved for scoring', recorded as 'Batches agree; no row changed'.

**Critic view:** The page does show the conflict. The 'Rev. no.' cell reads 00; the table rows read '01 09-05-16 AS PER CONSULTANT COMMENTS' and '00 05-03-16 ISSUED FOR APPROVAL'; the title-block DATE is 09-05-16. But the frozen conventions section 4 already orders the sources: the revision cell is the primary source, and the table is used 'when only a revision-history table is printed'. Under the frozen text, F019 p1 revision is present '00', resolved, with a note on the stale-looking cell. Topic (i) therefore amends section 4 with a new conflict precedence, and it removes one document from the revision population. That is an owner-level convention change, not a harmonisation, and REVIEW-NOTE section 4 does not escalate it. Critic view: either label present '00' under the frozen hierarchy, or escalate (i) explicitly as an amendment to section 4 before the gate count uses it.

**Evidence:** C:/t/r2x/r32-stage/crops/F019-p1-0.03_0.84_0.2_1-r90.png (DATE 09-05-16, Rev. no. 00, DWG. NO FAM-PIV-MAH-SPD-FA-2633-007); C:/t/r2x/r32-stage/renders/F019-p1.png revision table (01 09-05-16 / 00 05-03-16); C:/t/r2x/r32-stage/crops/F019-p1-0.38_0.86_0.44_0.99-r90.png

### C-006: pool_id=F067, page=1, field=identity

**Material:** yes. Changes the literal, for consistency with F039, F040 and F046 practice; no scoring effect if the scorer compares whitespace-insensitively.

**Reviewer ruling:** accept: literal 'CMW-17045-C001-01-E-0001'. The gap after 'C001-' 'is not established as a typed space'; the scorer should treat the spaced form as equal.

**Critic view:** On the bound crop the gap after 'C001-' is clearly wider than the gap after every other hyphen in the same number. My column scan of the DRAWING NO. line gives about 9 px there against 3-5 px elsewhere, and a magnified view shows it as a space. The pool keeps comparable visible gaps as printed ('FA- 6001', 'EM- 104', 'NBC-...-0002- R00'). Conventions section 3 keeps internal spaces as printed, and (i2) says the label keeps the printed form. Critic literal: 'CMW-17045-C001- 01-E-0001'. With whitespace-insensitive scoring the effect on the gate is nil, but the literal itself differs, and the pool should be consistent. Confidence is moderate, because the page has no text layer.

**Evidence:** C:/t/r2x/r32-stage/crops/F067-p1-0.82_0.74_0.99_0.95.png (DRAWING NO. cell); C:/t/r2x/r32-stage/renders/F067-p1.png; C:/t/r2x/r32-stage/renders/F067-p1.txt is empty (scan)

### C-007: topic=(d1) vs (e) wording overlap for 'Approved as noted / Resubmit'

**Material:** no. Precedence clarification only; no state, literal, class or count changes.

**Reviewer ruling:** (d1): mixed options lead with the approval and are class approved as noted. (e): 'wording that sends the document back for resubmission ... = revise and resubmit'.

**Critic view:** Read alone, the (e) wording rule also matches 'Approved as noted / Resubmit', 'APPROVED AS NOTED / RESUBMIT', 'Code B+Resubmit' and 'B+R', all of which send the document back for resubmission. The intended outcome, with (d1) governing, is right on the images. The Dewan stamp and the F001 form print separate REVISE & RE-SUBMIT and REJECTED options, and the Mirage reviewer picked B and added '+Resubmit'/'+R' while C was available. (e) should state that (d1) takes precedence for options that open with an approval. No row changes.

**Evidence:** C:/t/r2x/r32-stage/crops/F017-p1-0.88_0.58_0.95_0.7.png, C:/t/r2x/r32-stage/crops/F033-p1-0.93_0.58_0.99_0.68.png, C:/t/r2x/r32-stage/crops/F022-p1-0.23_0.9_0.33_1-r90.png, C:/t/r2x/r32-stage/crops/F026-p1-0.8_0.03_0.94_0.1-r270.png (ticks into APPROVED AS NOTED / RESUBMIT); C:/t/r2x/r32-stage/crops/F030-p1-0.11_0.7_0.93_0.725.png ('Code B +Resubmit'); C:/t/r2x/r32-stage/crops/F030-p4-0.84_0.19_0.975_0.27.png ('B+R')

### C-008: topic=(f) register status letters with partial coverage, pool_id=F020, page=3, field=decision

**Material:** no. Wording gap; no row change.

**Reviewer ruling:** accept: present 'B', association uncertain. (f) covers only 'differing letters across rows' (ambiguous) and an 'empty Status column' (absent).

**Critic view:** On F020 p3, rows 1-3 carry 'B' and row 4 (FA-0008.03) is blank. (f) does not say how to rule a partly filled Status column. Present/uncertain with a note is reasonable, and it changes nothing at document level because register rows never carry the fact. (f) should still name the case so that extensions are ruled alike.

**Evidence:** C:/t/r2x/r32-stage/crops/F020-p3-0.03_0.15_0.8_0.5.png

## Missed items

- **M-001: The F038 p1 identity value is shared verbatim across documents.** '2020-4-1072822' is the F038 p1 letter number ('الرقم'). It also appears as the transaction number on the F038 p2-p4 stamps and as 'OLD APPLICATION NUMBER 2020 - 4 - 1072822' in the F042, F047, F048 and F049 title blocks. The batch noted its omission from other_identities only for F047-F049. This is not a field error, but it collides with the h2 test (C-004), and it should be recorded as an other identity on those pages. Evidence: C:/t/r2x/r32-stage/crops/F038-p1-0.05_0.19_0.95_0.47.png; C:/t/r2x/r32-stage/renders/F047-p1.png; C:/t/r2x/r32-stage/renders/F042-p1.png
- **M-002: The escalation list omits the convention amendments that change populations.** REVIEW-NOTE section 4 escalates count-once, page-level scoring, whitespace comparison, the LACASA suffixes and resubmission_required. It does not escalate topic (i) or topic (h2), both recorded as 'batches agree; no row changed'. Topic (i) is a new precedence over frozen section 4 and removes F019 from the revision population. Topic (h2) is a new identity rule and removes F069 from the identity population. Evidence: REVIEWER-RESPONSE.json convention_rulings (i) and (h2); see C-004 and C-005

## Rulings confirmed on the images (selection)

- **Decision marks:**
  - Dewan REVIEW NOTE ticks: F010, F012, F017, F018, F019, F022, F026, F033.
  - Mirage cover codes B/C: F008, F013, F020, F021, F025, F028, F030, F032, F034, F036, F037.
  - Mirage sheet review blocks: F008, F009, F013, F020, F021, F025 p3/p4, F030, F032, F036, F037.
  - LACASA ACTION marks: F003, F004, F005, F006, F007, F011, F015.
  - SAIFCO '(B) Proceed as Noted': F002 p2 and p4. The F002 p1 B tick is separate from the PM signature.
  - AREX: F039, F040, F072.
- **Authority stamps and non-decisions:**
  - Authority approvals: the F014/F016 Civil Defence stamp (literal is the stamp text only), F038, and the F027 du stamp.
  - Not decisions: the F061 licence authentication and the AS BUILT boxes.
- **Register letters (f):** F008, F013, F020, F025, F028, F030, F032, F034, F036, F037.
- **Revisions and reply sheets:**
  - F039/F040 p1 revision re-ruled to absent: '-R0' ends the enclosed drawing's description.
  - Reply sheets: F024, F028 p4, F029.
- **Duplicates:**
  - F001/F031: the renders show 0 differing pixels.
  - F046/F059: they differ only by the contractor's round seal.
  - F038=F052 and F067=F070: identical sha256.
- **Ambiguous fields:** F035 p2 revision (an X and a circled 2), F035 p3 decision (mixed sample outcome), F067 decision (dated stamp with no decision wording), and F043 p2-p4 identity.

## Summary

I examined 46 non-accept rulings, 73 document-field rows with a 'no', all 16 convention rulings and an accept sample of 109 rows against the staged images. Most rulings hold. There are 8 disagreements, 6 of them material, and 2 missed items.

**Material disagreements:**

- **C-001:** the topic (e) tie-breaker contradicts its own Mirage C consequence and frozen section 5.
- **C-002:** F006 p2 does not meet g2's 'equals' identity condition, and under g2's revision clause its unlabelled R02 should be absent.
- **C-003:** under (h), the F043 annex 'Rev. 0' is a labelled revision of the page's own document, so it should be resolved and the F043 revision carried.
- **C-004:** the h2 cross-document test is over-broad (it catches the F038 letter number) and contradicts itself (an established job number should give absent, not ambiguous).
- **C-005:** topic (i) silently amends the frozen section 4 cell-first rule for F019.
- **C-006:** the F067 literal drops a visible space.

**Non-material disagreements:** wording gaps in (d1)/(e) and in (f).

Nothing here changes M2 status. This is an AI critique, not sign-off.
