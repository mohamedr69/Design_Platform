# Fresh M2 validation cohort: preparation report (interim)

**Stage:** the initial pool is drafted and frozen and **handed to the independent label reviewer**.

This is not an end state. The task's end states are READY FOR INDEPENDENT PREPARATION REVIEW and PREPARATION BLOCKED, and both are decided only after the independent label rulings come back (task step 10).

**Scope:** owner authorization of 2026-10-02 ([AUTHORIZATION-2026-10-02.md](AUTHORIZATION-2026-10-02.md), recorded verbatim). The process follows Review 32 (`REVIEW 31 ACCEPTED FOR COHORT PREPARATION ONLY`).

**What did not happen:**
- no provider or model request;
- no prediction of any kind: no baseline, candidate, reference, probe or application AI path;
- no ledger scope (483 entries and 17 scopes unchanged), and no use of the 556-request ceiling;
- no change to application code, the candidate, evaluators, existing labels, earlier packages or any database;
- no human review is claimed.

## 1. Frozen hashes before touching the cohort (task step 1)

[PRE-AUTHORIZATION-HASH-CHECK.json](PRE-AUTHORIZATION-HASH-CHECK.json) shows all of the following matched:
- **Review 31 package:** manifest `d5fe1649…` and all 58 files, its checker, the binding manifest `2dfef08e…` and draft declaration v2 `19720ad9…`;
- **Frozen code:** candidate `a8aaced` and baseline `3d5607d`, both clean;
- **Earlier packages:** review30, review29 and four-arm-final;
- **Ledger:** 483 entries and 17 scopes.

The Review 32 files were hashed as well.

## 2. Projects and contractors (task steps 2 and 3)

[PROJECT-AND-CONTRACTOR-VERIFICATION.csv](PROJECT-AND-CONTRACTOR-VERIFICATION.csv) and [PROJECT-VERIFICATION.json](PROJECT-VERIFICATION.json) record the checks. They used the tested Review 31 rules, unchanged, on metadata only.

- **Result:** **all 6 primaries and all 4 alternates pass**, so the cohort is EP-3563, EP-22349, EP-27331, EP-15744, EP-26687 and EP-29255, with no replacement.
- **What passing means:**
  - one folder per EP, and the folder name carries the EP number;
  - hierarchy class `project`;
  - the contractor equals the Review 31 record, and its cluster aliases no used contractor;
  - absent from every used source, including all 930 M1/M2 databases readable today;
  - not in the Round 2 selection, so not sealed. The 10 sealed EPs are listed in the JSON.
- **Proposal mentions:** the only hits for the cohort EPs are the Review 32 reviewer notes that propose this cohort. They are listed per file and not counted as use. That is why the used-EP count reads 209, which is 199 plus these 10.

## 3. Seeded pool, metadata only (task step 4)

[FROZEN-SELECTION.json](FROZEN-SELECTION.json) has sha256 `bf71779a…`. The draw rules are embedded in it and were fixed before the draw. The seed is `m2-r30-pool-2026-10-02`.

- **Universe:** 3,046 PDFs across the six folders. Excluded: 457 name-and-size duplicate copies, 2 paths naming another EP and 2 empty files, which leaves 2,585 eligible.
  - The `\\?\` long-path prefix was used, so no path longer than 260 characters was skipped. Review 31's metadata walk had silently skipped such paths and counted 2,455 PDFs for these projects.
- **Pool:** 72 documents. By stratum: 40 review-signal, 20 drawing-signal and 12 other. Each project contributes exactly 12.
- **Extensions:** the full seeded order for the extensions (302 review-signal paths) is frozen in the same file.

## 4. Staging (task step 5)

[SOURCE-MANIFEST.json](SOURCE-MANIFEST.json) has sha256 `951e8697…`.
- **Copies:** all 72 files were copied to `C:/t/r2x/r32-stage/files/` and hashed while read: 249.5 MB downloaded from OneDrive placeholders.
- **Originals:** never edited, renamed, moved or written beside. Each original's size and modified time are unchanged, and size matches the selection for all 72.
- **Byte-identical pairs:** F038 = F052 and F067 = F070. They are labelled once and count once (convention 1).

## 5. Renders and crops (task step 6)

| Recipe | Output |
|---|---|
| RENDER-R32-1, staged bytes only | 149 in-scope pages (pages 1–4) of 72 documents, plus text layers. No document is unsupported. |
| CROP-R32-1 | 189 crops |

Each image is bound to the staged sha256, page, region and recipe ([EVIDENCE-INDEX.json](EVIDENCE-INDEX.json)). The images stay in the isolated staging area, about 143 MB.

## 6. Draft labels (task steps 7 to 9)

- **Conventions:** [LABEL-CONVENTIONS-R32.md](LABEL-CONVENTIONS-R32.md), sha256 `5c09d4d2…`, frozen before the first label.
- **Draft:** [labels/R32-LABELS-DRAFT-1.json](labels/R32-LABELS-DRAFT-1.json), sha256 `ebd1e24d…`, **AI-authored and not human-signed**. It was drafted from source pages only.
  - **Never used:** predictions, application outputs, registers, extracted records, earlier labels, or file names as evidence.
  - **States recorded:** `present`, `absent`, `illegible`, `ambiguous` and `unsupported`, with association kept separate.
- **Mechanical validation** (`validate_drafts_r32.py`) found 0 problems:
  - every in-scope page is labelled;
  - every value has a region and bound evidence;
  - every crop's hash and binding were re-checked.

| Field (144 labelled pages) | present, association resolved | present, association uncertain | absent | ambiguous / illegible |
|---|---|---|---|---|
| identity | 111 | 0 | 30 | 3 / 0 |
| revision | 73 | 17 | 52 | 1 / 1 |
| decision | 69 | 10 | 63 | 2 / 0 |

- **Decision classes in the draft:** 59 approved as noted, 13 approved, 7 revise and resubmit.
- **Projection, not a gate count** ([labels/DRAFT-PROJECTION.json](labels/DRAFT-PROJECTION.json)): documents whose draft has a field present with association resolved number identity 62, revision 39 and decision 39, out of 70 distinct documents. Draft confidence is 29 high and 41 medium.
- **Concentration:** decision-bearing documents come mostly from EP-3563, EP-27331 and EP-29255. This bears on the later concentration rule and is not a gate input here.

## 7. Independent review handoff (task step 10)

[REVIEWER-PACKET.md](REVIEWER-PACKET.md) contains:
- 432 page-field rows and 210 document-field rows, with every reviewer column blank;
- 56 open questions;
- a response template.

The drafter **stops here**.

## 8. Field population (task step 12)

[FIELD-POPULATION.json](FIELD-POPULATION.json): **not counted**. Only independently reviewed rulings count. Extensions used: 0.

## Statuses, stated separately

1. **Source and project permission and verification:** owner authorization recorded verbatim. All 6 primaries are verified fresh from metadata, with no replacement. Sealed projects are excluded.
2. **Label drafting:** done for the initial pool (72 documents, 70 distinct, 144 pages). The draft `r32-labels-draft-1` is frozen, AI-authored and not human-signed.
3. **Independent label review:** **PENDING**, handed to the owner-delegated Codex reviewer. It is an AI review, not human sign-off.
4. **Field population counts:** not counted (gate counts need reviewed rulings). The draft projection is identity 62, revision 39, decision 39, and it is not a gate count.
5. **Preparation gate result:** not yet decided. Neither READY FOR INDEPENDENT PREPARATION REVIEW nor PREPARATION BLOCKED has been reached.
6. **Live-run authorization and budget:** none. No model request, ledger scope or budget, and the 556 ceiling is unused.
7. **M2:** CHANGES STILL REQUIRED. No default is selected, and M3 has not started.
