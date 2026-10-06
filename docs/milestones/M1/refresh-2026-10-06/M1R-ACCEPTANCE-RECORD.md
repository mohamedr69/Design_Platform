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
| Refreshed field / producer / persistence / consumer / freshness / override matrix | 173 new rows in the accepted CSV's 22 columns; 108 drift entries on accepted rows (100 real drift, 8 line-number only) | 3 models still in no matrix (KnowledgeMapping, KnowledgeResponseSource, KnowledgeIssue); S5 contributed no ownership rows | Add the 3 knowledge rows in the next refresh pass (surveyor, 1 hour); otherwise none | [M1R-DATA-OWNERSHIP-DELTA.csv](M1R-DATA-OWNERSHIP-DELTA.csv), [M1R-DATA-OWNERSHIP-DELTA.md](M1R-DATA-OWNERSHIP-DELTA.md) §3–§6 |
| Shared artifact capability map | 38 stages mapped against the section 5 contract; 39 version constants and fingerprints, 14 places with no version; 9 content-keyed shared artifacts with hazards; gap checklist | Map is static; whether stale markers behave as read requires runtime | None for M1; the gaps are M7's scope | [M1R-ARTIFACT-CAPABILITY-MAP.md](M1R-ARTIFACT-CAPABILITY-MAP.md) |
| Protected behavior list | 73 distinct override writers; 54 rows with a recorded weakness, tagged M7 34 / M3 16 / M10 3 / M5 1 | Weakness flags and milestone tags are the scribe's reading of surveyor gap cells, not surveyor findings | Verifier to spot-check the tagging; owners act in M3/M5/M7/M10 | [M1R-PROTECTED-BEHAVIORS.md](M1R-PROTECTED-BEHAVIORS.md) |
| Identify all GET-side work | 149 GET handlers classified (144 `@router.get` plus 2 admin-router, 2 divisions factory, 1 `/health`); 67 perform read-time work; no GET calls a model or enqueues a job; the accepted M1's 14 producers re-checked (13 present, 1 changed, 0 removed); 15 new producers; 28 duplicate-producer groups | 17 handler rows where the area surveys and the all-router audit classify differently (kept side by side); PURE_READ confirmed to handler + first-level callees + token scan, not every transitive method | M10 migration takes the table as its worklist; disagreements settled when each handler is migrated | [M1R-READ-SIDE-EFFECTS.md](M1R-READ-SIDE-EFFECTS.md) |
| Identify manual-override writers | As above (73) | As above | — | [M1R-PROTECTED-BEHAVIORS.md](M1R-PROTECTED-BEHAVIORS.md) §2 |
| Traceable changes from the accepted M1 snapshot | Delta is additive; drift listed per accepted row; coverage table of all 78 models against both matrices | Accepted CSV's own cells are not corrected in place (by design) | — | [M1R-DATA-OWNERSHIP-DELTA.md](M1R-DATA-OWNERSHIP-DELTA.md) §3, §5 |
| Compliance and workload facts added (roadmap U3 §3) | 28 NOT_IMPLEMENTED rows grouped by target milestone (M7, M26, M28); Task One's eight baseline items checked (6 confirmed, items 5 and 7 corrected); every Task Two input confirmed absent with the searches run | — | M3 decisions, M7/M26/M28 delivery | [M1R-DATA-OWNERSHIP-DELTA.md](M1R-DATA-OWNERSHIP-DELTA.md) §6; [M1R-ROADMAP-CORRECTIONS.md](M1R-ROADMAP-CORRECTIONS.md) table 2 |

## 2. Exit gate assessment (orchestrator's reading; the verifier's verdict is in section 6)

The gate asks for one authoritative owner per critical fact and no unresolved ownership conflict. The refresh **identifies** the owners and **records 25 ownership conflicts without resolving them** ([delta §7](M1R-DATA-OWNERSHIP-DELTA.md)). Resolving them is an owner decision the roadmap places at M3 (section 6, "Workload facts have owners", "One consultant decision vocabulary", "Historical answers and global knowledge"). The accepted M1 took the same position in `M1-TARGET-OWNERSHIP-DECISIONS.md` (15 decisions, 14 settled). The orchestrator therefore reads the M1 refresh gate as: the current-state map is complete and traceable, and the conflict list is the input M3 needs. Whether that satisfies "no unresolved conflict" is for the verifier and the owner to state; this record does not claim it.

## 3. Snapshot and versions

| Item | Value |
|---|---|
| Surveyed commit | 771001e (branch tip when the surveys ran; later commits on the branch add only this folder) |
| Source hashes | [evidence/M1R-SOURCE-HASHES.json](evidence/M1R-SOURCE-HASHES.json): sha256 of the 130 repository files the surveys cite; 0 cited files missing |
| Raw surveys | [evidence/surveys/](evidence/surveys/) S1–S5, unedited surveyor output |
| Version constants seen | `parse-2026-10-05.5` (document_control.py), `titleblock-2` (title_block.py), `classify-2026-09-27.2` and others as listed in the capability map §3 |
| Database | none opened; every "local rows" claim in the surveys is UNKNOWN |

## 4. Tests

None run for this milestone; it changes no code. The focused regression rerun of 6 October 2026 on this tree (106 passed, 3 skipped, 1 failed for lack of Tesseract) is recorded in roadmap section 11 and is not evidence for M1.

## 5. How the work was done

Five read-only surveyors (Sonnet) worked in parallel on disjoint areas and wrote only to the session scratchpad; their outputs were copied unedited into `evidence/surveys/`. Three scribes (Sonnet) assembled the records from the surveys without re-reading code. The orchestrator (this session) wrote this record and the source-hash file. The project's agent roster (`.claude/agents/`) was not loaded in this session, so the roles were emulated with the built-in general-purpose agent and the write guard hook did not run; the working tree was checked clean after every agent.

Counting units: "row" in the CSV is one engineering fact or stored artifact; "handler" is one GET definition; "producer" is one code path that does read-time work (consumer paths listed inside); "override writer" is one endpoint or service that writes an engineer-chosen value.

Known inconsistencies between surveys, kept side by side rather than reconciled: floor-identity rule sets (S1 five, S5 seven); drawing-status derivations (S2 three, S5 four); whether `ai_policy` is enforced at every AI entry (S3) or absent from the drawing AI paths (S2); 17 handler classifications. S4 §7.1 has 23 checked statements, not the 22 its summary says. The "144 handlers" figure originated in the orchestrator's grep count given in the briefs, not in the roadmap.

## 6. Independent review disposition

**Verdict:** pending — ep-verifier (Opus, read-only) reviews this package against the gate; its verdict and findings are appended below when received.

## 7. Owner decisions still required (not taken here)

- The 25 ownership conflicts in [delta §7](M1R-DATA-OWNERSHIP-DELTA.md): M3.
- Whether "approved as noted" is final approval (today folded into approved on Home and the Drawings summary): M3.
- The 65 roadmap corrections in [M1R-ROADMAP-CORRECTIONS.md](M1R-ROADMAP-CORRECTIONS.md): the orchestrator proposes carrying them into roadmap Revision U4; 12 are marked false, 20 incomplete, 11 imprecise, 22 confirmed with nuance.

## 8. Integration status, retention, rollback, limitations

- Integration: records only; nothing to roll back in code. Reverting the commits that added this folder restores the previous state.
- Retention: the accepted M1 package and all prior evidence folders are untouched.
- Limitations: static reading; no runtime; no database; the three scribes did not re-verify code; only S5 span-checked its citations against the AST; 57 unknowns are listed in [M1R-UNKNOWNS.md](M1R-UNKNOWNS.md). These records establish the current-state map; they do not establish any behavior as correct or any later milestone as started.
