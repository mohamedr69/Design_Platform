# Second independent verification: ep-verifier (Opus, read-only), 6 October 2026, on c1f962a (code at 771001e)

**Verdict: ACCEPT WITH NOTES.**

All of C1 to C6 are applied correctly, and so is C7 in the rows it named. The only remaining problems are three stale cache line numbers outside the CSV row that C7 named, and one duplicated sentence. Neither blocks acceptance. The notes are the ones the first verifier set: the package is static reading only, and the S1–S4 citations were not mechanically span-checked.

## Scope
- `git diff 4bab8d2 c1f962a --stat` changes 8 files, all under `docs/milestones/M1/refresh-2026-10-06/`: the 7 records plus `evidence/M1R-SOURCE-HASHES.json`.
- Empty diff between 4bab8d2 and c1f962a: `backend/`, `frontend/`, the accepted `M1-DATA-OWNERSHIP.csv`, `M1-TARGET-OWNERSHIP-DECISIONS.md`, `evidence/surveys/`, `evidence/verification-01/`, `docs/UNIFIED_MASTER_ROADMAP.md`. `backend/` and `frontend/` also have an empty diff between 771001e and c1f962a.

## C1–C7

| Change | Checked how | Result |
|---|---|---|
| C1: classify the 25 conflicts in delta §7 | Read the whole §7 table; counted the "Accepted decision" and "Kind" columns; checked every M3-OWNER-DECISION row against roadmap §6 and the M3 list; checked 7 SETTLED-GAP rows (#1, 3, 6, 11, 13, 20, 21) against D-xx wording and the accepted CSV targets. | Pass. 25/25 classified: 17 SETTLED-GAP (1-8, 11-15, 20, 21, 23, 24), 4 M3-OWNER-DECISION (9, 10, 17, 25), 4 NEW-PROPOSED (16, 18, 19, 22). #9, #10, #25 match the M3 list verbatim; #17 and S-1 match "global promotion". Every SETTLED-GAP row checked cites a decision that names that owner. |
| C2: fill the target owner in 79 rows | Parsed the CSV; diffed against the 4bab8d2 CSV; classified each of the 79 rows; sampled 14 inherited rows against D-01..D-15 and the accepted CSV. | Pass. 173 × 22, header identical. 0 "UNKNOWN" in target cells. Kinds 56 / 13 / 10. No inheritance contradicts a decision's wording (note 3). |
| C3: `version` is written | Grepped the package outside the surveys for "never written", "no writer", "dead column", every mention of `version` and "concurrency"; read CMP.statement_version, CMP.approved_version, RC-27, capability map C-25, N-10, §6.1, errata §9. | Pass. No remaining claim that `version` has no writer except the quoted survey claim in the errata. Every corrected statement cites `services/concurrency.py:63-71` and calls it an optimistic-concurrency counter. CMP.statement_version is CURRENT. RC-27 corrected. Errata lists the S4 error and the read-side increment. |
| C4: source hashes | Loaded the JSON; recomputed sha256 and byte length of all 251 entries from `git show 771001e:<path>` (25 also by `sha256sum`); compared with HEAD; grepped for the two wrong paths; checked every path cited in the records exists at 771001e. | Pass. `file_count` 251; `unresolved_citations` []; 251/251 match. Only `docs/UNIFIED_MASTER_ROADMAP.md` differs at HEAD and is flagged. The 5 previously unhashed files are present. `review/prepare.py` and `ifc/ai_symbol_review.py` appear only in errata §9 and the delta §8 change log. Acceptance record §3 states 251. |
| C5: AI policy settled from code | Read acceptance record §5, protected behaviors summary, S3-D11, §4.2, delta §7 #25; checked the cited lines; grepped `project_policy` / `ai_policy`. | Pass. All four places state the code finding (`drawing_ai_review.py:118-127`; `compliance/service.py:192`, `566`; `routers/compliance.py:641`). "Kept side by side" survives only for the floor-identity, drawing-status and 17-handler inconsistencies, which is correct. |
| C6: drift wording and writer coverage | Recounted the §5 kind column with Python; read acceptance record §1. | Pass. 55 semantic + 35 line-number + 9 claim false + 1 both = 100 with drift; 36 involve line numbers; 6 no drift; 2 not re-verified; 108 total. §1 matches and names the areas not re-surveyed for override writers. |
| C7: minor references | Read CACHE.result_cache, PREP.change, PREP.run, WL.sd_required_scope, RC-13, RC-30, RC-58. | Pass on the named items. The same cache error survived in two other records (D1, fixed by the orchestrator in the commit recording this verdict). |
| Acceptance record §2 and §6 | Read both; diffed against 4bab8d2. | Pass. §2 states the ownership rule with measured counts (17/4/4; 56/13/10). "Took the same position" is gone. §6 read "pending second verification". |

## Counts measured

| Measure | Value |
|---|---|
| CSV rows × columns | 173 × 22 |
| Duplicate ids / ids also in the accepted CSV | 0 / 0 |
| Target cells containing "UNKNOWN" | 0 |
| Cells changed since 4bab8d2 | 81 `target_producer`, 81 `target_source_of_truth`, 25 other |
| Previously open rows by kind | inherited 56, PROPOSED 13, M3-OWNER-DECISION 10 |
| Inherited rows by group | SD 12, DOC 20, LOG 2, DRV 7, PREP 7, DFT 4, ARC 3, PST 1 |
| Statuses | CURRENT 123, READ_SIDE_EFFECT 17, DUPLICATE_DERIVATION 1, LEGACY 5, NOT_IMPLEMENTED 27 |
| §7 conflicts | 25: 17 SETTLED-GAP, 4 M3-OWNER-DECISION, 4 NEW-PROPOSED |
| Drift entries | 108 |
| Hash entries | 251 of 251 match |

## Spot-check of claims added by the corrections (code at 771001e)

| # | Claim | Result |
|---|---|---|
| 1 | `services/concurrency.py:63-71`: `before_update` listener on ProjectDesign and ComplianceStatement runs `version = (version or 0) + 1` when `is_modified` | CONFIRMED |
| 2 | Imported at `routers/design.py:41`, `boq_review.py:30`, `projects.py:61` | CONFIRMED |
| 3 | `models.py:1604` default 0; `routers/compliance.py:549` puts `current_version` in the 409; `schemas_design.py:957` exposes `version` | CONFIRMED |
| 4 | GET `/compliance/statements/{id}` (521-530) → `_statement_out` (424-427) → `service.recheck@1052`, which reassigns rows and commits | CONFIRMED |
| 5 | `drawing_ai_review.enabled` (118-127) checks only three switches; no `project_policy`/`ai_policy` reference in `review/`, `redesign/`, `ifc/`, `drawing_ai_review.py`, `shop_drawings.py` | CONFIRMED |
| 6 | `project_policy.allowed` gates `compliance/service.py:192`, `566`, `routers/compliance.py:641` | CONFIRMED |
| 7 | Threshold 0.97 at `core/config.py:235`; applied at `ifc/services/ai_symbol_review.py:328-350`; `resolve.py:132-133` asks "confirm" only for library/family matches on plans | CONFIRMED |
| 8 | `ai/cache.py`: TTL test at 78, `put` at 86-93 | CONFIRMED |
| 9 | `redesign/prepare.py::place@133`; `review/prepare.py` and `ifc/ai_symbol_review.py` do not exist | CONFIRMED |
| 10 | `compliance/learning.py:139-152` keyed by `system_code` only; `knowledge/review.py:178-201` validates vocabulary and ids | CONFIRMED |
| 11 | Owner cells: SD.requirement_state → D-08(a); DOC.drawing_scope_by_folder → D-04 scope attribute; SD.floor_alias_auto → D-04 | CONFIRMED |

## Remaining defects (non-blocking)

- D1. Stale `ai/cache.py` line numbers in capability map rows V-19 and K-03 and in RC-20 (77 → 78; 84-91 → 86-93). Fixed by the orchestrator in the commit that records this verdict; errata §9 updated.
- D2. Duplicated "History: 79 rows…" sentence in acceptance record §1 row 1. Fixed in the same commit.

## Notes
1. Static reading only. No code, test or database was run.
2. S1–S4 citations were not mechanically span-checked; only the citations above and the first verifier's sample were opened.
3. Some inheritances follow the orchestrator's rule but go beyond the decision's literal wording: DRV.*, PREP.*, DFT.* under D-04 (which names the register tables); ARC.* under D-01 (project information and lifecycle). None contradicts a decision; M3 should confirm them when it ratifies the PROPOSED owners.
4. "File Sync registry / M7 shared processing registry" on DOC.* rows joins two names, following the accepted CSV's own convention; M7 should keep it to one registry.
5. Acceptance record §7 counts 13 PROPOSED target owners; the 5 USR.* rows also carry PROPOSED owners under M3-OWNER-DECISION, so M3 ratifies 18 PROPOSED owner cells in total.
6. The hash file flags `docs/UNIFIED_MASTER_ROADMAP.md` as differing at HEAD (commit 6de416b, Revision U4); a document, not code.

## Limitations
Read-only; inherited-row plausibility judged against decision text and the accepted CSV, not owner intent; the M3 reserved list taken from roadmap §6 and M3 as at U4; hash recomputation proves the hashed bytes match 771001e, not that the list holds every cited file (completeness checked by path-resolving the records); code claims checked only for the 11 items above, the rest rely on the first pass's 34-citation sample.

Working notes: `notes.md`, `sample25.txt`, `filled.txt`, `ni_csv.txt`, `ni_md.txt` in this folder.
