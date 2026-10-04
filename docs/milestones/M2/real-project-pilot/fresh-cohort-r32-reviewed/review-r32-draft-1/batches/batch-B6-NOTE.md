# Batch B6 note: independent label review of r32-labels-draft-1

- **Task:** ORCH-01A.1 / B6, agent label R32REV-B6.
- **Project:** EP-26687.
- **Pool ids:** F039, F040, F041, F046, F050, F056, F057, F058, F059, F060, F066, F072.
- **Draft reviewed:** `r32-labels-draft-1`, sha256 `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334`.
- **Status:** DONE.
- **Full response:** `REVIEWER-RESPONSE.batch-B6.json`.

This is an owner-delegated independent Claude AI review. It is **not** human sign-off. M2 remains CHANGES STILL REQUIRED, and nothing here changes that.

## Integrity

- **Manifest:** `EVIDENCE-MANIFEST.json` matched (`15c4114d…82d0ed`), and all 110 files listed in it matched.
- **Named hashes:** the draft, the conventions, `FROZEN-SELECTION.json`, `SOURCE-MANIFEST.json`, `CROPS.jsonl` and `EVIDENCE-INDEX.json` all matched.
- **Reviewer columns:** every `reviewer_*` column in both worklist CSVs was blank.

## Coverage

| Item | Expected | Ruled |
|---|---|---|
| Page-field rows (14 pages) | 42 | 42 |
| Document-field rows | 36 | 36 |
| Questions | 4 | 4 |
| Images opened | | 39 (14 staged renders, 19 staged crops, 6 own check crops) |

## Page-field rulings

| Field | Accept | Correct | Reject | Unresolved |
|---|---|---|---|---|
| Identity | 14 | 0 | 0 | 0 |
| Revision | 14 | 0 | 0 | 0 |
| Decision | 13 | 1 | 0 | 0 |

The only correction is F039 p2 decision, and it changes the **region only**. The draft region [0.62,0.8,0.67,0.83] shows only the AREX logo on this sheet. The ticked "B Approved As Noted" row is at about [0.615,0.864,0.66,0.882]. The value, class (approved as noted), actor and association are unchanged.

## Document-field rulings

Every row was ruled `resolved_for_scoring = yes`.

| Field | carries_fact yes | carries_fact no |
|---|---|---|
| Identity | 11 | 1 (F066) |
| Revision | 10 | 2 (F066, F072) |
| Decision | 3 (F039, F040, F072) | 9 |

**Gate caution:** F046 and F059 are the same sheet. Their renders differ only in one region, a company seal that appears on F046 alone. Both are ruled carries_fact = yes for identity and revision, but the proposal is to count the pair **once**, on F046. Without that merge the identity and revision populations are over-counted by one.

## Questions

- **F039, F040:** the p1 "-R0" is a suffix of the enclosed drawing's description. Accepted as present with uncertain association. It does not block the document, because p2 "REV - 0" is resolved.
- **F046, F059:** count once (lower id F046). Both label sets are correct.

## Proposed convention rulings

- **(b) Evidence strings:** "render F###-pN.png" resolves to the bare render name. Affects F039 p1 and F040 p1 revision.
- **(c) Near-duplicates:** two documents that differ only by marks carrying no identity, revision or decision fact (such as a company seal) count once, on the lower id. A copy that adds a decision, or carries a different revision, stays separate.
  - Merged: F046 and F059.
  - Kept separate: F039 p2 against F046/F059; F040 p2 against F041; F050 against F060.
- **(d)/(e) Decision class:** the class follows the printed legend.
  - AREX forms: A = approved, B = approved as noted, C "Revise & Resubmit" = revise and resubmit, D "Not Approved" = rejected.
  - AREX stamp: "C Incorporate Comments & Resubmit" = revise and resubmit.
  - A helper's D-to-resubmit mapping must not override a printed "Not Approved". No D is ticked in this batch.
- **(g) Description suffix:** a "-R0" at the end of an enclosed drawing's description on an approval form is present with uncertain association. It counts only through the drawing page's resolved REV cell.
- **(j) Template regions:** helper template regions must be checked per page. F039 p2 is a mismatch; all other regions in the batch match.
- **Seals and revision notes:** company seals and contractor notes such as "REVISED AS PER COMMENTS" are not decisions, so the decision is absent with no_decision_area.

Topics (a), (f), (h), (i) and (k) do not arise in this batch. No crop is rotated.

## Could not open

Nothing. Every cited render and crop opened and was readable. F066 p1 has no crops, and none was needed.

## Independence statement

- **Agent:** a fresh, isolated Claude workflow subagent. It reports itself as Claude Opus 5.5 (claude-opus-5-5), effort high. It had no access to the drafting session.
- **No predictions or earlier outputs:** no predictions, application outputs, ledgers or earlier experiment outputs were consulted.
- **No requests:** no provider or model request and no network access were made.
- **Files read:** only the frozen packet under `docs/milestones/M2/real-project-pilot/fresh-cohort-r32`, the staged evidence under `C:/t/r2x/r32-stage` (renders and crops), and this task's own scratch subfolder. The packet scripts were not run.
- **Files written:** only this note and the batch response file. Check crops and diffs were made from the staged renders with PIL into scratch.
- **Leftover scratch file:** `scope.txt` (a worklist dump, no rulings) was already in the scratch subfolder from an earlier interrupted start. It was not used for any ruling.
