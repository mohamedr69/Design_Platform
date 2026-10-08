# Human reviewer packet: R32 Golden labels (gate G9)

Role: ep-scribe. Authority: owner decision of 2026-10-08, authority A-14 item 6 (the human reviewer defined by the roadmap workflow is included). Repo: `roadmap-u2`, branch `roadmap/u2`, head at authoring `37350bc848f9e5ec97dcae0695f52719cc99b6b6`.

**Status: prepared, not performed. No human review of any R32 label has taken place, and nothing in this packet, the form or the index records one.** Until a named human signs the form, every R32 metric keeps the statement required by Amendment R32-01: "reference set independently AI-reviewed (Claude agents), not human-signed".

Companions in this folder: `HUMAN-REVIEW-SIGNOFF-FORM-R32.md` (the blank form; 24 documents, 56 pages, 168 page-field rows) and `HUMAN-REVIEW-INDEX.json` (paths and sha256 of every page image, staged original and label file). Paths below use `PKG` = `G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot` and `MR` = `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap`.

## 1. Purpose

M4 gate G9 (M2 acceptance matrix row G9; roadmap section 8, M4 required closure work point 4) asks for "manually verified Golden cases from originals; labels independently checked, not solely by another model" (policy section 8: "Gold labels must be independently checked against originals, not generated or approved solely by another model."). Today there is no human-signed set. Every R32 label is AI-drafted (Claude Opus 5.5) and AI-reviewed (agents R32REV-B1..B7, consolidation, critic, disposition, and the Independent Preparation Review 33), and Amendment R32-01 admits `r32-labels-reviewed-2` (sha256 `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6`) for the R32 cohort only, expressly "not human-signed". `OWNER-AI-PERMISSION-ROUND2.md` records: "Reviewer appointment and human sign-off remain pending".

This packet closes G9 **for the R32 cohort first**: a human checks the labels that will be scored in the R32 run set against the original pages. It is the "route (a)" of Review 33 (a human check of every page-field row actually scored in the frozen run set, at most 30 documents and 120 pages; the run set is 24 documents and 56 labelled pages, inside both bounds), which Review 33 calls "the only route that satisfies section 8 as written". The closure cohorts (expanded sealed pilot, BOQ, any later cohort) need their own packet later, built the same way; this one does not cover them and the amendment's scope rule is unchanged.

Review 33 timed route (a) "after the selector freezes and before B runs". The selector froze the 24-document run set (declaration v5, `run_set_sha256` `9058f3d6...7ce8`); v5 is frozen and not authorized and no run exists, so the check can still be done in that window. If the owner wants the route (a) timing, the check must be signed before any dispatch.

## 2. Who may sign

- An engineer of the owner's choosing, or the owner himself. The owner decides and states the name; this packet does not appoint anyone.
- The signer must be a person, must not have drafted or AI-reviewed these labels, and must read the pages himself (no AI model produces or pre-fills the readings).
- The AI reviewers (Claude Opus 5.5 agents R32REV-B1 to B7, R32REV-CONSOLIDATE, R32REV-CRITIC, R32REV-DISPOSE, R33-FINAL, and the drafter) are named as **prior reviewers**, never as signers. Their rulings stay as recorded.
- If the owner signs: the owner has already seen the v3 observation for F009 page 3 and ruled on it on 2026-10-07 (`C:/t/r2x/r42-sandbox/r32-v3-owner-records/F009-HUMAN-RULING-2026-10-07.md`). That is one human ruling on one field (identity of F009 page 3, "confirmed correct"); it is not a signed set, and it does not replace this check. The owner must list that exposure in the form's exposure declaration, and F009 is then not a blind row for him. An engineer who has not seen it avoids the issue; that is why an engineer is the cleaner choice. The owner decides.

## 3. What the human checks

Frozen rules: `PKG/fresh-cohort-r32-reviewed-2/packet-inputs/LABEL-CONVENTIONS-R32.md` (sha256 `5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570`) plus the recorded interpretations, summarised in 3.5. The reviewer applies them as written and does not improve them.

### 3.1 Material

For each of the 24 run-set documents (listed in the form; from `declaration-r32-v5` `run_set.pool_ids`): the page images named in the index (rendered PNG of each labelled page) and, when a render is unclear, rotated or cropped, the staged original PDF named in the index. The renders are bound to the staged PDF by sha256 (`EVIDENCE-INDEX.json`), and each staged PDF equals the source file on the shared drive (`SOURCE-MANIFEST.json`: source sha256 equals staged sha256), so the staged PDF is the original. The reviewer looks at the image; the `.txt` text layer is never evidence.

### 3.2 Per labelled page, three fields (as the reader scope of R32)

| Field | The reviewer decides |
|---|---|
| identity | the page's own document number as printed, with its printed label; project, plot, job, form, template and referenced numbers are not the identity; punctuation, hyphens, slashes and leading zeros kept; state present / absent / illegible / ambiguous / unsupported |
| revision | the page's own current revision as printed (cell, title-block REV, latest revision-table entry, or a labelled tail); an unlabelled suffix of the document number is recorded with association uncertain and is not counted |
| decision | the decision of the **reviewing party** (consultant or authority) on that page's document, as a stamp, ticked option, code letter with its legend, or handwritten text; contractor stamps, "received" stamps and blank workflow boxes are not decisions; class is approved / approved as noted / revise and resubmit / rejected / other, with the actor; a blank or missing area is `absent` (blank_decision_area or no_decision_area) |

Per document the reviewer also answers: is this the right file and are the labelled pages the pages the labels describe (form Section A).

### 3.3 Counts

24 documents (EP-26687: 7, EP-27331: 6, EP-22349: 5, EP-3563: 3, EP-29255: 2, EP-15744: 1), 246 PDF pages, **56 labelled pages** (pages 1 to 4 per document, the R32 reader scope; later pages are counted but not labelled), **168 page-field rows** (56 identity, 56 revision, 56 decision). Recorded states in `r32-labels-reviewed-2` for those rows: identity present 47, absent 6, ambiguous 3; revision present 38, absent 17, ambiguous 1; decision present 37, absent 18, ambiguous 1. The reviewer must check absent and ambiguous rows as carefully as present ones: an absent label hides an error as easily as a wrong literal. If the reviewer sees a decision or revision on an unlabelled page (page 5 onward), he writes it in the document's Note; it is not a row.

### 3.4 Dates and document sections (gate G3)

R32 scores identity, revision and decision only; no label for dates or document sections exists in any frozen set, so there is nothing to agree or disagree with. This packet therefore **does not include them**. If the owner keeps G3 (owner decision 4 of the M2 acceptance matrix: a separate validation scope, or descoping), a human check of dates and sections needs labels first: human-authored or AI-drafted then human-checked, under their own frozen conventions and a new packet. If the owner descopes G3, nothing is added. Either way this packet makes no claim on G3.

### 3.5 Recorded interpretations the reviewer applies (this cohort; Review 33 rulings, owner may reverse)

Count-once duplicates (F031 to F001, F052 to F038, F059 to F046, F070 to F067; none of the aliases is in the run set); (d1) "Approved as noted / Resubmit", "Code B+Resubmit", "B+R" are class approved as noted with the literal kept; (e) a code letter's class follows its printed legend, not the letter; (g)(1) a labelled `Rev.` tail is a revision, the identity is the number without it, and an unlabelled suffix is association uncertain; (h) compilation files are keyed by (document, page) and a labelled running-header value belongs to that page's document; (d2) an authority approval stamp without comments is approved, marks that are not review decisions assert none; (f) EMAAR register status letters are recorded present, actor inferred, association uncertain, and never carry the document decision. The full text is in `reviewed-2` `convention_amendments_and_interpretations`. A reviewer who thinks a convention is wrong does not apply a private rule: he marks Disagree with the literal he reads and says in Note which convention is in question; the owner rules on conventions.

## 4. Sampling rule

**What the policy says.** `AI-ACCURACY-POLICY.md` section 8 gives no sampling rule and no sample size. Its words are: "Gold labels must be independently checked against originals, not generated or approved solely by another model." Amendment R32-01 adds no sampling rule either; it only forbids calling the AI-reviewed set human-signed. The only quantitative statement found is Review 33's route (a): every page-field row that will actually be scored in the run set, at most 30 documents and 120 pages. That is a review route, not policy text.

**Required (follows Review 33 route (a)): a full check of the 24 run-set documents**, all 56 labelled pages, all 168 page-field rows. No sampling inside the run set.

**Proposal (not decided; the owner approves or changes it): a stratified sample of the remaining reviewed cohort.** The cohort has 72 staged files, 68 distinct documents after count-once, so 44 distinct documents outside the run set (83 labelled pages). The policy's wording, read strictly, covers all gold labels; the run set only covers what v5 scores. A sample extends the human assurance to the rest of the reference set and tests how well the AI review held. Proposed rule:

1. Strata are the six projects.
2. Per project, draw n = max(2, ceil(25 % of the remaining distinct documents)).
3. F019 (revision ambiguous, excluded from scoring) and F069 (compilation; unresolved identity) are always included, because they are the rows where the AI reviewers escalated; they count toward their project's n.
4. The rest is drawn by ascending sha256 of the string `m2-r30-runset-2026-10-02|<id>` (the frozen run-set seed), not chosen by hand.
5. Result: 14 documents and 27 labelled pages: F003, F007, F017, F019, F029, F034, F036, F049, F053, F056, F058, F062, F069, F071 (paths and hashes in the index under `proposal_sample_documents`; they are not on the sign-off form).
6. Escalation: any disagreement in the sample on a field triggers a full check of that project's remaining documents for that field. Any disagreement in the run set is handled by section 6.

Until the owner approves the proposal, only the 24 documents are required for the R32 G9 claim, and the claim is worded for the run set only.

## 5. Blindness rule

- The reviewer is shown the original page images, the frozen conventions, the document list and the blank form. Nothing else.
- Not shown, not discussed: any application prediction, harness output, extracted record, register entry, R32 v3 result (including the F009 page 3 observation and ruling), any v5 material, any earlier label set other than as Appendix L after the reader's own reading, and the AI reviewers' notes and rulings.
- The labels appear only in Appendix L of the form, to be opened after the reader has written his own reading for the page in Section B. The index carries no label content.
- File names and folder names are never evidence (`SOURCE-MANIFEST` relative paths are in the index only so a reviewer can verify the file; he must not read meaning into them).
- No model, provider, OCR or application is used to read pages. The reviewer's own reading is the evidence.
- Any exposure to a prediction or result is declared on the form (Section D). An undeclared exposure voids the affected rows.

## 6. Recording disagreements

- The frozen sets (`r32-labels-draft-1`, `reviewed-1`, `reviewed-2`, the declaration, the run set, the evaluation input) are never edited. A disagreement does not change a label, a population count or the declaration.
- The reviewer returns the completed form as a **new file** named `HUMAN-RESPONSE-R32-<signer-initials>-<YYYYMMDD>.md` (or the filled `.md` form plus a `.json` with one object per Disagree row: row id, reviewer reading in printed form, state, class and actor for a decision, region, note), stored in this folder or one the owner names. Its sha256 is written in the form's signature block and recorded by the scribe afterwards.
- Every Disagree row stays a **disputed row** with both readings kept: the label as recorded and the human reading.
- What a dispute changes (relabel, mark not scorable, rerun the check, change a convention) is an owner decision, and under the amendment and the frozen declaration it needs a new, hashed record (a new label version and, if v5 has not run, a new declaration; if v5 has run, an addendum). This packet applies none of those consequences.
- If an AI reviewer's label and the human differ, the human reading is recorded as the human reading; it does not become "the truth" until the owner rules, except that the owner has already ruled F009 page 3 identity (label stands).
- A "Not checked" mark is allowed with a reason; the sign-off then covers only the checked rows, and the claim is worded that way.

## 7. Sign-off statement

The signer copies the statement in Section D of the form unchanged:

> I examined the original page images of the documents and pages listed in this form against the field values recorded in label set `r32-labels-reviewed-2`, using the frozen label conventions `LABEL-CONVENTIONS-R32.md` and the recorded interpretations, without access to application predictions, harness outputs or R32 v3 / v5 results (except as declared above). The Agree / Disagree marks and notes in this form are my own reading. This signature covers only the rows marked as checked in this form. It is not an acceptance of M2 or M4, not an authorization of any run, budget or dispatch, and does not extend to any other cohort.

What a completed sign-off permits, and nothing more: the scribe may record "R32 run-set labels: human-checked by <name>, <role>, <date>: N rows agree, M rows disagree (listed)" and, if M is zero, may state that the run-set reference rows are human-verified. It does not by itself close G9 for the closure cohorts, does not change Amendment R32-01 for other cohorts, and does not accept M2 or M4. The wording "human Golden Truth" is not used for rows with a disagreement. Until the form is signed, nothing in the repository says a human reviewed anything.

## 8. Time estimate (planning figure, not a measured one)

- Setup (open the index, verify hashes, read the conventions): 0.5 h.
- Run set: 56 pages at about 5 to 7 minutes per page for three fields including the written reading and the comparison with Appendix L, plus extra time for the 5 ambiguous rows and rotated or photographed sheets (F006 is a photographed form): about 5.5 to 7 h.
- Sign-off and totals: 0.25 h.
- Total for the required check: about 6 to 8 hours, best split in two sittings with the form saved after each document.
- Proposed sample: 27 pages, about 2.5 to 3 h more.
- Disagreement write-up: not estimated.

## 9. Open points for the owner

1. Name the signer (an engineer or the owner) and, if the owner, accept the F009 exposure declaration.
2. Approve or change the sampling proposal in section 4.
3. Decide G3 (separate scope or descoping), since dates and sections have no labels.
4. Decide the timing: before any v5 dispatch (route (a) as Review 33 states it) or after.
5. Decide what a disagreement triggers (section 6), preferably before the check so the consequence is not chosen after seeing the result.
6. The closure cohorts need their own packet and their own human check; this one does not provide it.
