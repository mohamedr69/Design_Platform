# Review note: consolidated label review of `r32-labels-draft-1`

**Task:** ORCH-01A.2, agent R32REV-CONSOLIDATE, Claude Opus 5.5 (`claude-opus-5-5`), effort High.

**Completed:** 2026-10-03T05:22:17Z.

**Response:** [REVIEWER-RESPONSE.json](REVIEWER-RESPONSE.json), sha256 `70f94632884af028f31d66f76557807801cf00fcca37251a2ade25c9de3a3ff8`, also recorded in [RESPONSE.sha256](RESPONSE.sha256).

This is an owner-delegated independent Claude AI review under owner decision A-03. It is **not** human sign-off.

## 1. Packet integrity: OK

| Check | Result |
|---|---|
| `evidence/EVIDENCE-MANIFEST.json` sha256 | `15c4114d…82d0ed`, matches the expected value |
| Files listed in the manifest | 110 re-hashed, 0 mismatched |
| Draft `labels/R32-LABELS-DRAFT-1.json` | `ebd1e24d…a334`, matches |
| Conventions `LABEL-CONVENTIONS-R32.md` | `5c09d4d2…e570`, matches |
| Renders in EVIDENCE-INDEX | 149 re-hashed, 0 bad |
| Crops in EVIDENCE-INDEX | 189 re-hashed, 0 bad |
| Batch inputs | all seven name the same draft sha256, report status DONE and report their own integrity check OK |

`evidence/PACKAGE-CHECK.json` is not listed in the manifest. It is the packaging report written beside the manifest, and it reports its own `unlisted: []`. It is not a mismatch.

## 2. Review completeness: complete, 0 unresolved

**Coverage:**
- The seven batches cover 70 pool ids with no overlap.
- Every one of the 432 page-field rows and 210 document-field rows is ruled exactly once.
- No row was missing, duplicated, or left unresolved for capacity.
- The batches answered 54 of the 56 questions. The two byte-identical copies, F052 and F070, are in no batch pool list, so the consolidator ruled those two questions after hashing the staged PDFs.

**Page-field rulings after harmonisation:**

| Field | accept | correct | reject | unresolved |
|---|---|---|---|---|
| identity | 128 | 16 | 0 | 0 |
| revision | 127 | 17 | 0 | 0 |
| decision | 131 | 13 | 0 | 0 |

**Document-field "yes" counts.** These are reviewer counts over the 210 rows. **They are not yet the gate count.**

| Field | resolved_for_scoring yes | carries_fact yes | both yes | both yes, without F031 / F059 (count-once) |
|---|---|---|---|---|
| identity | 67 | 59 | 59 | 57 |
| revision | 63 | 39 | 39 | 37 |
| decision | 69 | 39 | 39 | 38 |

When the preparation step makes the gate count, it must apply count-once:
- F031 counts with F001.
- F059 counts with F046.
- F052 = F038 and F070 = F067 have no rows of their own.

**Provenance:**

| Source | Rows |
|---|---|
| Batch rulings, page-field, document-field and questions together | B1 114, B2 99, B3 94, B4 95, B5 88, B6 75, B7 115 |
| Harmonised | 12 rows: 4 page-field and 8 document-field |
| Harmonised questions | 4 |
| Questions ruled by the consolidator | 2 |

Each harmonised entry keeps the batch ruling in `superseded_batch_ruling`.

**Evidence binding:**
- 22 batch rows cited scratch-folder zooms or overlays.
- Those entries were moved to `reviewer_working_images`, and the rulings are unchanged.
- Every `evidence_checked` path is now under `C:/t/r2x/r32-stage` and bound by EVIDENCE-INDEX.json.

## 3. Convention rulings issued: 16, for the pool and for extensions

| Topic | Ruling | Rows re-ruled |
|---|---|---|
| (a) | An uncertain association always carries a note. | none |
| (b) | Evidence strings resolve to bound images; working images are not evidence. | none, 22 rows normalised |
| (c) | Duplicates: byte-identical files, or render-identical files without an added field fact, count once on the lower id. | F031 and F059 document rows tagged `gate_count_once_with` |
| (d1) | Mixed options such as "Approved as noted / Resubmit" and "B+R" are classed `approved as noted`. | none |
| (d2) | Authority approvals, and marks that are not decisions. | none |
| (e) | A code letter's class follows the meaning of its printed legend. Example: EMAAR C/D is `revise and resubmit`; a plain "Not Approved" is `rejected`. | none |
| (f) | Register status letters are present, actor inferred, association uncertain, and never carry the document decision. | none |
| (g) | Labelled tail, unlabelled own-number suffix, and revision values of another document. Reconciles the B6 versus B2/B7 conflict. | F039 p1 and F040 p1 revision changed to absent |
| (g2) | Reply-to-comments sheets. Reconciles the B2 versus B4 conflict. | F024 p1 and F029 p1 revision changed to absent; F024 and F029 document revision changed to yes/no |
| (h) | Compilation files: page-level truth; a file carries a field when at least one page is present and resolved. B7's stricter rule is not adopted. | none |
| (h2) | A project or job number under a "Reference" label makes the identity ambiguous. | none |
| (i) | Ambiguous versus illegible. | none |
| (i2) | Literal form; the scorer compares whitespace-insensitively and keys on pool id. | none |
| (j) | Region tolerance 0.01; a region-only correction changes no ruling. | none |
| (k) | Rotated crops: the upright crop only. | none |
| (m) | Stamp location beyond the title-block frame. | none |

For the (g) and (g2) changes, the consolidator viewed the images itself:
- the F039-p1 and F040-p1 renders;
- the F028-p4 render;
- the F024-p1 and F029-p1 crops;
- the F046/F059 seal region, by pixel comparison and a view.

## 4. Items escalated for an owner or preparation-review decision

No row is unresolved. These items need a decision outside this review:

1. **Count-once rule.** The gate must apply count-once:
   - F031 with F001;
   - F059 with F046;
   - F052 with F038;
   - F070 with F067.

   The document-field rulings for F031 and F059 stay yes/yes as facts.
2. **Page-level scoring of compilation files.** The scorer must key on (pool id, page) for F002 and F035, and for F043 (a letter plus an annex). The preparation review should confirm that it does before those files count.
3. **Literal comparison.** The scorer should compare literals whitespace-insensitively. This affects the LACASA "- R0n" references, F023 "MEP 2 1 7" and the F067 "C001- 01" gap.
4. **LACASA/Scale "- R0n" suffixes.** The systematic suffixes stay uncertain, so F003, F004, F005, F006 and F015 revision is no/no. Counting them would need an explicit owner convention change.
5. **Recommended schema addition.** The reviewed version should add `resubmission_required = yes` for the mixed-option rows. Those rows are F001 p2, F031 p2, F017, F022, F026, F033 and F030 p1/p3/p4.

## 5. Independence

**Agents:**
- Seven fresh batch agents, R32REV-B1 to B7, each Claude Opus 5.5 at effort High. Each batch's `reviewer.model_self_report` is copied into `agents`.
- One fresh consolidator, R32REV-CONSOLIDATE, also Claude Opus 5.5 at effort High.
- Orchestrator: Claude Fable 5.1.

None of them is the drafting agent.

**What the consolidator did not do:**
- It consulted no predictions.
- It made no provider or model request.
- It used no network.
- It ran no packet script.
- It ran no state-changing git command.

**What the consolidator opened:**
- the packet `fresh-cohort-r32`;
- the seven batch files and their notes;
- the staging area `C:/t/r2x/r32-stage`: renders, crops, and hashes of the staged PDFs;
- its own scratch folder.

It opened nothing else.

## 6. Label truth after this review

AI-reviewed (owner-delegated Claude review), not human-signed. The drafter applies these rulings in a new version, `r32-labels-reviewed-1`. The draft itself stays unchanged.

## 7. Permissions and budget

Unchanged. Nothing was requested.

## 8. Milestone status

M2 is **CHANGES STILL REQUIRED**. M3 has not started. This review changes neither.
