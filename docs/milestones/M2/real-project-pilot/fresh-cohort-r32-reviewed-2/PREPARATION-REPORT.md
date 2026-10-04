# Cohort preparation after Independent Preparation Review 33: r32-labels-reviewed-2

**Task:** ORCH-04.1, agent label R32APPLY2-IMPL, under EP Platform Master Plan authority A-03 (owner decision 2026-10-03, Claude-only workflow). Task definition: `master-roadmap/orchestrator/NEXT-BOUNDED-TASK.md` (ORCH-04).
**Model:** Claude Opus 5.5 (`claude-opus-5-5`), effort High, by my own system context.
**Date:** 2026-10-03 (UTC).
**Role:** a fresh, isolated implementation agent, and the only write-capable agent running. I am not the drafter, a label reviewer, a Review 33 agent or the ORCH-02 implementer. Nothing here approves or self-approves anything.

This task applied the Review 33 rulings mechanically. No image was read and no ruling was re-made. There was no model or provider request, no prediction, no ledger scope, no OneDrive access and no sealed project.

## End state

| Item | Value |
|---|---|
| New labels | `labels/R32-LABELS-REVIEWED-2.json`, version `r32-labels-reviewed-2`, sha256 `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6` |
| Derived from | `r32-labels-reviewed-1`, sha256 `00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779` (verbatim copy in `labels/`, unchanged) |
| Draft | `r32-labels-draft-1`, sha256 `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334` (verbatim copy in `labels/`, unchanged) |
| Rulings applied | Review 33 `INDEPENDENT-REVIEW.md` `8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804`; `ESCALATION-RULINGS.final.json` `e2fe503d96a3bc08c99ce52862d2017a567f6e2a6677744f43750c5ebc7611a0`; `DISPOSITIONS.json` `ceb8fdcc6cc3e54219ab22686fc663a66c93ca5ed44316255ddf24745018315b` (whole folder copied verbatim to `review-33/`) |
| Review 33 verdict | **PREPARATION ACCEPTED WITH CONDITIONS** (conditions C-1 to C-9) |
| Conditions addressed here | C-1 (rulings applied as a new immutable version, recount) and C-2 (amendments and interpretations recorded) |
| Field populations | `FIELD-POPULATION.json` (sha256 `799a4b8f97c4560a2906da84f94515711cf9841b3bb3a9529ad6f5cde338539e`): identity **57**, revision **38**, decision **38**; `excluded_unresolved` **{}** |
| Gate action | **READY FOR INDEPENDENT PREPARATION REVIEW** (pool gate: each field at least 12; 0 extensions) |
| Package check | `evidence/PACKAGE-CHECK.json`, written by `scripts/verify_r32c_package.py` |
| Manifest | `evidence/EVIDENCE-MANIFEST.json`, written last; it binds the package check. Its sha256 is in the M2-REVIEW-RESPONSE.md entry. |

## What changed from reviewed-1 (Review 33 section 4.4)

The function is `build_reviewed2` in `scripts/apply_review33_r32.py`. It is pure. It takes the row values from `ESCALATION-RULINGS.final.json`, checks the reviewed-1 values Review 33 states before changing anything, and then diffs reviewed-1 against reviewed-2. It raises if any key outside the enumerated set differs, or if its change log and the diff disagree. `verify_r32c_package.py` repeats the diff with its own independent restatement of section 4.4.

| # | Row | Change |
|---|---|---|
| 1 | `F069/p1/identity` | `state` present → **ambiguous**; `literal` EP-15744 → **null**; `candidates` added [EP-15744, printed_label "Refrence", role not established on the page]; `review_status` unresolved → **ruled (Review 33, D-004)**; open question closed with a reference. `association` resolved and `excluded_from_scoring` true are unchanged. |
| 2 | `F069/p3/identity` | The same as row 1. |
| 3 | `F069` document identity | `resolved_for_scoring` unresolved → **no**; `carries_fact` stays **no**; the D-004 open question is closed (ruled). |
| 4 | `F019/p1/revision` | `review_status` unresolved → **ruled (Review 33, D-005)**; open question closed. `state` ambiguous, `candidates` 00 ("Rev. no." cell) and 01 (latest revision-table entry), `association` resolved, `region` [0.04, 0.86, 0.43, 0.99] and `excluded_from_scoring` true are unchanged (checked equal to the ruling). |
| 5 | `F019` document revision | `resolved_for_scoring` unresolved → **no**; `carries_fact` unresolved → **no**; the D-005 question's ruling becomes "ruled (Review 33, D-005)" and its open question is closed; the D-005 entry of the `unresolved` list is marked ruled. |
| 6 | `escalations[]` | All six entries (three D-004, three D-005) gain `status` "ruled (Review 33, D-00x)" and `ruled_by` with the Review 33 and `ESCALATION-RULINGS.final.json` hashes and the resulting value. No escalation is open. |
| 7 | count-once aliases | Annotated in `count_once_alias_annotations`: F031→F001 and F059→F046 as the Review 33 (c)(ii) ruling (an amendment to convention section 1), with the F031 p3/p4 caveat on F031; F052→F038 and F070→F067 as frozen section 1. The `count_once_aliases` mapping itself is unchanged. |
| 8 | amendment and interpretation list | `convention_amendments_and_interpretations`: the C-2 text verbatim, then (c)(ii), (d1), (e)/D-001 (amendments) and (g)(1), (g2)/D-002, (h)/D-003, (d2), (f) and the D-005 page reading of sections 2 and 4 (interpretations). Each item quotes the Review 33 text verbatim and the matching `ESCALATION-RULINGS.final.json` carried-over text, and names the label-review convention topic. |
| 9 | metadata | `version`, `status` ("AI-reviewed: owner-delegated independent Claude AI review (ORCH-01A) with the Independent Preparation Review 33 rulings applied; NOT human-signed; NOT a human review"), `derived_from`, `applied` (hashes, verdict, `conditions_applied` ["C-1","C-2"]), `change_log` (51 entries, each with provenance "Review 33 <ruling id>" and the Review 33 hash), `generated_at_utc`, `generator`. The replaced reviewed-1 metadata is kept verbatim under `lineage.reviewed_1`. |

Every other document, page and field is identical to reviewed-1 at field level. Only F019 and F069 differ among the 72 documents.

**Page-field review status after application:**
- identity: 128 accepted, 14 corrected, 2 ruled (Review 33, D-004);
- revision: 123 accepted, 20 corrected, 1 ruled (Review 33, D-005);
- decision: 131 accepted, 13 corrected.

Nothing is `unresolved` anywhere, and no `open_question` key remains.

**How open items were closed (representation, not a ruling):**
- Each closed `open_question` is removed from its row and kept, word for word, under `review33_ruling.open_question_closed`, together with the closing reference (review name, ruling id, both hashes).
- The F019 `unresolved` list keeps the draft's strings verbatim. Its D-005 entry is marked ruled in `unresolved_review33_marks`, and it points to the ruled question.
- Each changed row and document carries a `review33_ruling` block: ruling id, outcome, ruling text, superseded values, the owner alternative (not applied) and the hashes.

## Counts (`FIELD-POPULATION.json`)

- **Status:** COUNTED. **Stage:** "initial pool after independent review and Review 33 rulings". **Extensions used:** 0.
- **Rule:** the reviewed-1 count-once rule, unchanged. Per field, count the distinct documents, after count-once, whose document review has `resolved_for_scoring` = yes and `carries_fact` = yes. Unresolved documents would be excluded and listed.
- **Aliases:** F031→F001 and F059→F046 (Review 33 (c)(ii)); F052→F038 and F070→F067 (frozen section 1).
- **Identity 57. Revision 38. Decision 38.**
- **Excluded as unresolved:** none (`{}`). **Upper bound if resolved:** 57 / 38 / 38, equal to the counts.
- **Documents:** 72 staged files, 70 with their own rulings, 68 distinct after count-once.
- **Decision-carrying documents by project (information only):** EP-27331 12, EP-3563 11, EP-29255 10, EP-26687 3, EP-22349 2, EP-15744 0.
- **Consistency check: OK.** All 138 `carries_fact` yes document fields have at least one in-scope labelled page with the field present, association resolved and not excluded. None of the 72 `carries_fact` no document fields has such a page. In-scope pages come from `fresh-cohort-r32/RENDERS.json` (`175a3a10…e8be`, the rendered pages), and they equal the EVIDENCE-INDEX renders. No labelled page lies outside scope. The only in-scope pages without labels are those of the byte-identical aliases F052 (pages 1 to 4) and F070 (page 1), which have no pages of their own.
- **Cross-check:** the frozen reviewed-1 count function (`fresh-cohort-r32-reviewed/scripts/count_population_r32.py`, read only) gives the same 57/38/38 on reviewed-2, with every excluded list empty.

## Statuses, stated separately

1. **Source permission and verification:** unchanged. A-02 (owner, 2026-10-02) covers discovery, download, staging, rendering, label drafting and preparation for the six projects. It does not cover provider or model use. Verification was 10 of 10 with no replacement (r32 packet). This task did not touch OneDrive, sources or projects. The projects' AI policies are **not yet checked** (C-9).
2. **Label drafting:** frozen. `r32-labels-draft-1` (`ebd1e24d…a334`) is AI-drafted (Claude Opus 5.5) and not human-signed. It is copied verbatim and was not edited.
3. **Independent label review:** the owner-delegated independent Claude AI review (ORCH-01A, applied as `r32-labels-reviewed-1`, `00e53e82…9779`) is unchanged. Review 33 ruled D-004 (AMBIGUOUS), D-005 (AMBIGUOUS) and (c)(ii) (ADOPTED), and those rulings are now applied as `r32-labels-reviewed-2` (`89c60e9d…b9a6`). The labels are **AI-drafted and AI-reviewed. They are NOT human-signed, NOT a human review**, and they come from the same model family as the system under test (R33-02). The AI-ACCURACY-POLICY §8 conflict is **open for the owner** (C-3).
4. **Field populations:** identity **57**, revision **38**, decision **38**, with **nothing unresolved** and 0 extensions.
5. **Preparation gate:**
   - The pool gate (each field at least 12) is met.
   - The Review 33 verdict is **PREPARATION ACCEPTED WITH CONDITIONS**.
   - **C-1 and C-2** are met by this package as applied by the implementer. That is subject to the independent re-derivation and recount by a fresh read-only agent and the orchestrator's verification. It is not self-approved.
   - **C-3, C-4 and C-9** are owner-only and pending: the §8 route, the concentration-rule stratum leg, and the project AI policies.
   - **C-5 to C-8** are pending correction tasks: C-5 the harness adapter, C-6 the offline test of evaluator .10, C-7 the new declaration, C-8 the minor-finding disclosures. None was started here.
   - Gate action: **READY FOR INDEPENDENT PREPARATION REVIEW**.
6. **Live-run authorization and budget:** none, and nothing was requested. There is no provider use, budget, ledger scope or use of the 556 ceiling. The AI ledger `C:/t/r2x/ledger/r2x-ledger.sqlite` was opened read-only (`mode=ro`, `uri=True`) only. It still shows 483 entries and 17 scopes, and nothing was written to it.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** **not started.**

**Also stated separately:**
- **Correction readiness:** no harness, adapter, converter, selector or evaluator work was done (C-5, C-6 pending).
- **Accuracy:** not measured. There was no model call and no prediction.
- **Label truth:** as in status 3.
- **Permissions and budget:** as in status 6.

## Package contents

| Path | What it is |
|---|---|
| `labels/R32-LABELS-REVIEWED-2.json` | New labels (this task) |
| `labels/R32-LABELS-REVIEWED-1.json`, `labels/R32-LABELS-DRAFT-1.json` | Verbatim copies, hashes unchanged |
| `review-33/` | Verbatim copy of the whole Review 33 folder (19 files, including `dimensions/`), with `COPY-MANIFEST.json` (source and copy sha256) |
| `packet-inputs/` | Verbatim copy of `fresh-cohort-r32-reviewed/packet-inputs/` (6 files, including its own original COPY-MANIFEST.json) |
| `evidence/COPY-MANIFEST.json` | Source and copy sha256 for `labels/` and `packet-inputs/` |
| `FIELD-POPULATION.json` | Counted field populations |
| `scripts/` | check_inputs_r32c.py, copy_inputs_r32c.py, apply_review33_r32.py, count_population_r32c.py, verify_r32c_package.py and the two test files (identical to the work folder `C:/t/iso/work/r2x/r32c/`) |
| `tests/` | junit XML: 21 + 7 tests, all passed (pytest 8.3.4, Python 3.12.10) |
| `evidence/INPUT-HASH-CHECK.json` | Step-0 check: 7 of 7 frozen files and 45 of 45 source-manifest files match; the full hashes of `ESCALATION-RULINGS.final.json` and `DISPOSITIONS.json` are recorded and equal the values named in INDEPENDENT-REVIEW.md |
| `evidence/PACKAGE-CHECK.json`, `evidence/EVIDENCE-MANIFEST.json` | Package check, then the manifest, written last |
| `COMMANDS-AND-AUDIT-LOG.md` | Every command, in UTC |

## Observations (facts, no action taken)

- **F069 p1 candidate role wording.** Section 4.4 item 1 gives the candidate role as "not established on the page". `ESCALATION-RULINGS.final.json`, which Review 33 says governs the reviewed-2 application, gives it for p1 as "not established on the page (issuer's project/job number on F062/F068)", and for p3 as "not established on the page". The JSON values were applied verbatim. Section 4.1 states that F062/F068 are context only, not the basis of the ruling.
- **F019 p1 revision note.** The ruling row in `ESCALATION-RULINGS.final.json` carries a `note` worded differently from reviewed-1's. Its `row_change` says "status fields only", and section 4.4 item 4 lists no note change, so the reviewed-1 note was kept. The ruling's wording is recorded in `review33_ruling.ruling_row_note`.
- **F069 p1/p3 keys not enumerated as changing.** `printed_label` "Refrence", `semantic_role` "own quotation reference (equals the project EP number)", `region`, `value_note`, `evidence` and `review_provenance` are kept from reviewed-1. The `semantic_role` text predates the ruling. A consumer should read `state` and `candidates`.
- **Label-review ids.** The D-001 to D-005 inside "(e)/D-001", "(g2)/D-002", "(h)/D-003" and "D-005" are the label review's dispositions (`M2-label-review-r32-draft-1/DISPOSITIONS.json`, `e8828bec…`), not the ids in Review 33's own DISPOSITIONS.json.
- **Task-text hashes.** The task text gives `ESCALATION-RULINGS.final.json` and `DISPOSITIONS.json` by 16-hex prefix only. Both prefixes match, and the full values recorded above equal those named in INDEPENDENT-REVIEW.md.
- **Ledger `-shm` file.** The read-only opens of the AI ledger (`mode=ro`) updated the mtime of `r2x-ledger.sqlite-shm` (to 10:03:30Z at the dry-run check; it had been 08:00:47Z, from Review 33's verifier). The `.sqlite` file (mtime 2026-10-01) and `-wal` (0 bytes) are unchanged, and the counts are unchanged. The ledger folder is not one of the frozen trees checked for the 09:50:00Z cutoff.
- **by_project_decision.** It now lists EP-15744 explicitly with 0. In reviewed-1 the project was omitted.
