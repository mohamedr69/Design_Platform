# M1 refresh — acceptance record

Milestone: **M1 — Data Requirements, Ownership & Current-State Map** (refresh for the current code).
Date: 6 October 2026. Snapshot surveyed: branch `claude/upbeat-lovelace-sa9j3w` at commit **771001e** (`771001e6b70939704a478d09a6740e76778cfecd`). Documentation and read-only inspection only: no application code, test, migration, configuration or frozen evidence file was changed; no database was opened; no code was run. The accepted M1 package under `docs/milestones/M1/` (closure revision 2026-09-27, HEAD 13eb73ce of the earlier repository) is unchanged and remains the accepted historical snapshot.

Task statement, as the roadmap's section 14 requires:

| Element | Value |
|---|---|
| Milestone | M1 refresh |
| Bounded scope | Extend the accepted 155-field ownership matrix to every producer added since its snapshot; add the compliance and workload facts of roadmap section 3 as explicit gap rows; refresh the read-side-effect inventory across every GET handler; list the manual override writers and the protections on them; map today's processing artifacts against the section 5 registry contract; record where roadmap U3 and the accepted package disagree with the code. |
| Snapshot changed | None in code. Records added under `docs/milestones/M1/refresh-2026-10-06/`. |
| Completion gate | Roadmap M1 exit: every critical fact/artifact has exactly one authoritative owner, producer and consumer contract; no unresolved conflict over whether the tab, processor or memory service owns it; GET-side work and manual-override writers identified; traceable from the accepted snapshot. |
| Evidence destination | This folder. |

## 1. Requirement → current implementation → remaining gap → action → evidence

| Requirement (roadmap M1) | Delivered | Remaining gap | Action / owner | Evidence |
|---|---|---|---|---|
| Refreshed field / producer / persistence / consumer / freshness / override matrix | 173 new rows in the accepted CSV's 22 columns, each naming one target owner (delta §2); drift on accepted rows: 108 entries: 100 carry drift (36 of them line-number drift, 35 line-number only and 1 also semantic), 6 no drift, 2 not re-verified | 3 models still in no matrix (KnowledgeMapping, KnowledgeResponseSource, KnowledgeIssue); S5 contributed no ownership rows. History: 79 rows had no target owner at the first verification; filled per the ownership rule in delta §2 | Add the 3 knowledge rows in the next refresh pass (surveyor, 1 hour); otherwise none. | [M1R-DATA-OWNERSHIP-DELTA.csv](M1R-DATA-OWNERSHIP-DELTA.csv), [M1R-DATA-OWNERSHIP-DELTA.md](M1R-DATA-OWNERSHIP-DELTA.md) §3–§6 |
| Shared artifact capability map | 38 stages mapped against the section 5 contract; 39 version constants and fingerprints, 14 places with no version; 9 content-keyed shared artifacts with hazards; gap checklist | Map is static; whether stale markers behave as read requires runtime | None for M1; the gaps are M7's scope | [M1R-ARTIFACT-CAPABILITY-MAP.md](M1R-ARTIFACT-CAPABILITY-MAP.md) |
| Protected behavior list | 73 distinct override writers; 54 rows with a recorded weakness, tagged M7 34 / M3 16 / M10 3 / M5 1 | Weakness flags and milestone tags are the scribe's reading of surveyor gap cells, not surveyor findings | Verifier to spot-check the tagging; owners act in M3/M5/M7/M10 | [M1R-PROTECTED-BEHAVIORS.md](M1R-PROTECTED-BEHAVIORS.md) |
| Identify all GET-side work | 149 GET handlers classified (144 `@router.get` plus 2 admin-router, 2 divisions factory, 1 `/health`); 67 perform read-time work; no GET calls a model or enqueues a job; the accepted M1's 14 producers re-checked (13 present, 1 changed, 0 removed); 15 new producers; 28 duplicate-producer groups | 17 handler rows where the area surveys and the all-router audit classify differently (kept side by side); PURE_READ confirmed to handler + first-level callees + token scan, not every transitive method | M10 migration takes the table as its worklist; disagreements settled when each handler is migrated | [M1R-READ-SIDE-EFFECTS.md](M1R-READ-SIDE-EFFECTS.md) |
| Identify manual-override writers | 73 writers in the five surveyed areas; BOQ, BOQ corrections, project details, design rules and part currents are covered only by the accepted M1 and were not re-surveyed for new writers | As above | — | [M1R-PROTECTED-BEHAVIORS.md](M1R-PROTECTED-BEHAVIORS.md) §2 |
| Traceable changes from the accepted M1 snapshot | Delta is additive; drift listed per accepted row; coverage table of all 78 models against both matrices | Accepted CSV's own cells are not corrected in place (by design) | — | [M1R-DATA-OWNERSHIP-DELTA.md](M1R-DATA-OWNERSHIP-DELTA.md) §3, §5 |
| Compliance and workload facts added (roadmap U3 §3) | 27 NOT_IMPLEMENTED rows grouped by target milestone (M7, M26, M28; 28 before CMP.statement_version was corrected to CURRENT); Task One's eight baseline items checked (6 confirmed, items 5 and 7 corrected); every Task Two input confirmed absent with the searches run | — | M3 decisions, M7/M26/M28 delivery | [M1R-DATA-OWNERSHIP-DELTA.md](M1R-DATA-OWNERSHIP-DELTA.md) §6; [M1R-ROADMAP-CORRECTIONS.md](M1R-ROADMAP-CORRECTIONS.md) table 2 |

## 2. Exit gate assessment (orchestrator's reading; the verifier's verdict is in section 6)

Every critical fact and artifact in the refreshed matrix names one target owner: the accepted decision D-xx where one exists, otherwise a PROPOSED owner for M3 to ratify. Of the 25 items in [delta §7](M1R-DATA-OWNERSHIP-DELTA.md), 17 are current-code multi-writer or protection gaps under an owner already settled by D-xx and are carried to M4, M5, M7, M10 and M26; 4 are owner decisions that roadmap section 6 and M3 reserve to the owner ("approved as noted" finality, item 9; historical answers and the global namespace, items 10 and 17; the project AI/provider policy, item 25); M1 does not settle these and records them as explicit M3 owner decisions; 4 are new facts with a PROPOSED owner. The M1 exit is met for ownership in this sense; it is not a claim that today's code has one writer per fact.

The other two decisions the roadmap reserves (who may record and override contract value, capacity, ownership shares, stream applicability and strength; retention of an archived or cancelled project) concern absent facts, not conflicts: they are named in the target cells of the WL.* and PRJL.* rows. In the CSV, 56 of the 79 target cells filled after the first verification inherit an accepted decision, 13 name a PROPOSED owner and 10 are bounded by an M3 owner decision (delta §2).

## 3. Snapshot and versions

| Item | Value |
|---|---|
| Surveyed commit | 771001e (branch tip when the surveys ran; later commits on the branch add only this folder) |
| Source hashes | sha256 of every repository file cited by full path or by resolved abbreviation in the records and surveys (251 files, see [evidence/M1R-SOURCE-HASHES.json](evidence/M1R-SOURCE-HASHES.json), regenerated after verification); backend/ and frontend/ are unchanged between 771001e and HEAD |
| Raw surveys | [evidence/surveys/](evidence/surveys/) S1–S5, unedited surveyor output |
| Version constants seen | `parse-2026-10-05.5` (document_control.py), `titleblock-2` (title_block.py), `classify-2026-09-27.2` and others as listed in the capability map §3 |
| Database | none opened; every "local rows" claim in the surveys is UNKNOWN |

## 4. Tests

None run for this milestone; it changes no code. The focused regression rerun of 6 October 2026 on this tree (106 passed, 3 skipped, 1 failed for lack of Tesseract) is recorded in roadmap section 11 and is not evidence for M1.

## 5. How the work was done

Five read-only surveyors (Sonnet) worked in parallel on disjoint areas and wrote only to the session scratchpad; their outputs were copied unedited into `evidence/surveys/`. Three scribes (Sonnet) assembled the records from the surveys without re-reading code. After the first verification a revising scribe applied changes C1 to C7 to the seven records; it read only the code lines it cites for those changes and did not edit the surveys. The orchestrator (this session) wrote this record and the source-hash file. The project's agent roster (`.claude/agents/`) was not loaded in this session, so the roles were emulated with the built-in general-purpose agent and the write guard hook did not run; the working tree was checked clean after every agent.

Counting units: "row" in the CSV is one engineering fact or stored artifact; "handler" is one GET definition; "producer" is one code path that does read-time work (consumer paths listed inside); "override writer" is one endpoint or service that writes an engineer-chosen value.

Known inconsistencies between surveys, kept side by side rather than reconciled: floor-identity rule sets (S1 five, S5 seven); drawing-status derivations (S2 three, S5 four); 17 handler classifications. Whether `ai_policy` is enforced at every AI entry (S3) or absent from the drawing AI paths (S2) was settled after verification from the code: `project_policy.allowed` is not consulted on the drawing AI paths (services/drawing_ai_review.py:118-127 checks only drawings_ai_review_enabled, ai_enabled and the provider; no reference in review/, redesign/ or ifc/services/ai_symbol_review.py); compliance assist calls are gated by compliance/service.py:192 and 566 and routers/compliance.py:641. The policy's scope is an M3 owner decision; its enforcement is a gap for M7/M12 (delta §7 #25). S4 §7.1 has 23 checked statements, not the 22 its summary says. The "144 handlers" figure originated in the orchestrator's grep count given in the briefs, not in the roadmap.

## 6. Independent review disposition

**Verdict: ACCEPT WITH NOTES** (second independent verification, 6 October 2026, on commit c1f962a; notes: static reading only, S1–S4 citations not mechanically span-checked).

Two passes by the ep-verifier role (Opus, read-only), neither of which wrote the package:

1. First pass on commits e6259de..36144e2: **CHANGES REQUIRED** with seven documentation corrections C1–C7 (79 rows without a target owner; 25 conflicts not classified against the accepted decisions D-01..D-15; one false code claim about `ComplianceStatement.version`; source hashes covering only full-path citations; the AI-policy point left unsettled; drift and override-writer wording; minor references). Record: [evidence/verification-01/](evidence/verification-01/README.md). All seven were applied in commit c1f962a; the ownership rule used for C2 is in the delta §2.
2. Second pass on c1f962a: **ACCEPT WITH NOTES**. C1–C7 verified pass; 251 of 251 source hashes recomputed; 11 added code claims confirmed at 771001e; two non-blocking defects (D1 stale cache line numbers in the capability map and RC-20, D2 a duplicated sentence) fixed in the commit that records this verdict. Full report: [evidence/verification-02/REPORT.md](evidence/verification-02/REPORT.md).

What the verdict does and does not say: the current-state map is complete for the surveyed areas and traceable to the accepted snapshot; every critical fact names one target owner, 18 PROPOSED owner cells and 4 owner decisions await M3 ratification; nothing about today's code behavior is declared correct, and no later milestone is started by this acceptance.
## 7. Owner decisions still required (not taken here)

- From the 25 items in [delta §7](M1R-DATA-OWNERSHIP-DELTA.md): the 4 M3-OWNER-DECISION items (9, 10, 17, 25) and the ReviewRuling scope (S-1); M3 also ratifies the 4 PROPOSED owners (16, 18, 19, 22) and the 13 PROPOSED target owners in the CSV. The 17 SETTLED-GAP items go to the milestone named in each row, not to M3.
- Project access (USR.* rows) and the retention of an archived, cancelled or deleted project (PRJL.* rows): M3.
- Whether "approved as noted" is final approval (today folded into approved on Home and the Drawings summary): M3.
- The 65 roadmap corrections in [M1R-ROADMAP-CORRECTIONS.md](M1R-ROADMAP-CORRECTIONS.md): the orchestrator proposes carrying them into roadmap Revision U4; 12 are marked false, 20 incomplete, 11 imprecise, 22 confirmed with nuance.

## 8. Integration status, retention, rollback, limitations

- Integration: records only; nothing to roll back in code. Reverting the commits that added this folder restores the previous state.
- Retention: the accepted M1 package and all prior evidence folders are untouched.
- Limitations: static reading; no runtime; no database; the first three scribes did not re-verify code, and the revision after verification read only the lines it cites; only S5 span-checked its citations against the AST; 57 unknowns are listed in [M1R-UNKNOWNS.md](M1R-UNKNOWNS.md). These records establish the current-state map; they do not establish any behavior as correct or any later milestone as started.

## 9. Errata to raw surveys

The surveys in `evidence/surveys/` are raw evidence and were not edited. The records carry these corrections, found by the first verification or while applying its changes.

| Survey or record | What it says | What the code shows (file:line at 771001e) | Corrected in |
|---|---|---|---|
| S4 Table A CMP.statement_version; Table B entry 10; section 7.1 row 8 | `ComplianceStatement.version` has no writer (default 0, one read) | It is written. `backend/app/services/concurrency.py::_bump_version` (lines 63-71), a SQLAlchemy before_update listener on ComplianceStatement and ProjectDesign, increments it on every modifying flush, including a background AI fill and the GET recheck; the module is imported by routers/design.py:41, routers/boq_review.py:30 and routers/projects.py:61. It is an optimistic-concurrency counter, not an approved-version number; no immutable approved version exists and approved rows are not kept. The survey's search (`statement\.version\|\.version *\+=`) does not match the listener's `target.version` assignment | CSV CMP.statement_version (now CURRENT) and CMP.approved_version; delta §4.19, §5 S4-B10, §6 totals (CURRENT 123, NOT_IMPLEMENTED 27); RC-27; capability map C-25, N-10, §6.1 |
| (follows from the row above) | — | GET /compliance/statements/{id} (routers/compliance.py:521-530) runs `service.recheck` (compliance/service.py:1052) through `_statement_out` (routers/compliance.py:424-427); a row change it commits passes the listener, so the read increments `version`: a read-side write on a concurrency token | Here and CSV CMP.statement_version (freshness_dependencies) |
| S2 Table A PREP.change, PREP.run | `review/prepare.py` | The file is `backend/app/redesign/prepare.py` (`place` at line 133); `backend/app/review/prepare.py` does not exist | CSV PREP.change, PREP.run; delta §4.9 |
| S3 Table A CACHE.result_cache | TTL measured at AC:77; put at AC:84-91 and AC:88-91 | The TTL test is ai/cache.py:78; `put` is lines 86-93 | CSV CACHE.result_cache; capability map V-19, K-03; RC-20 (second verification D1) |
| S3 Table D #11 | The project AI policy is enforced at every AI entry | Not on the drawing AI paths (services/drawing_ai_review.py:118-127; no reference in review/, redesign/ or ifc/services/ai_symbol_review.py); compliance assist calls are gated at compliance/service.py:192, 566 and routers/compliance.py:641 | Protected behaviors S3-D11, summary and §4.2; delta §7 #25; section 5 above |
| S1 key finding 2 and Table B (as carried into RC-13, RC-58) | AI answers at 0.97 or more count as verified exact matches with no engineer step (ifc/resolve.py:132-133) | The 0.97 threshold (core/config.py:235) is applied at ifc/services/ai_symbol_review.py:328-350, which writes an accepted answer to the company library as source ai; resolve.py:132-133 asks "confirm" only for a verified symbol on the plans matched by resemblance (library or family) | RC-13, RC-58 |
| First-pass records (not surveys) | delta §7 #17 `ifc/ai_symbol_review.py:339-344`; delta §7 #10 `knowledge/learning.py:139-152`; RC-24 `compliance/review.py:178-201` | `backend/app/ifc/services/ai_symbol_review.py`, `backend/app/compliance/learning.py` and `backend/app/knowledge/review.py`; the paths written do not exist | delta §7 #10 and #17; RC-24 |
| First-pass acceptance record | Drift "100 real drift, 8 line-number only" | 108 entries: 100 carry drift (36 with line-number drift, 35 of them line-number only), 6 no drift, 2 not re-verified | Section 1 |
