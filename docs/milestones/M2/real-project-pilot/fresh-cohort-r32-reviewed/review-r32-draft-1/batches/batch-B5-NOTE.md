# Batch B5: label review note (R32REV-B5, ORCH-01A.1/B5)

**Scope:** project EP-22349; draft `r32-labels-draft-1` (sha256 `ebd1e24d…a688a334`).
**Pool ids:** F035, F038, F042, F044, F045, F047, F048, F049, F051, F053, F054. F052 is a byte-identical copy of F038 and is ruled once, on F038.

**Output:** `REVIEWER-RESPONSE.batch-B5.json`, status DONE.

## Integrity

Every check passed:
- **Evidence manifest:** sha256 `15c4114d…` matches, and all 110 listed files match.
- **Frozen files:** the draft, the conventions, FROZEN-SELECTION, SOURCE-MANIFEST, CROPS.jsonl and EVIDENCE-INDEX all match their expected sha256.
- **Reviewer columns:** every reviewer column is blank in both worklists (432 and 210 rows).

## Expected and ruled counts

| Item | Expected | Ruled |
|---|---|---|
| Page-field rows | 51 | 51 |
| Document-field rows | 33 | 33 |
| Questions | 4 | 4 |

## Page-field rulings

| Field | accept | correct | reject | unresolved |
|---|---|---|---|---|
| identity | 17 | 0 | 0 | 0 |
| revision | 16 | 1 | 0 | 0 |
| decision | 16 | 1 | 0 | 0 |

**Corrections:**
- **F035 p2 revision:** changed from `illegible` to `ambiguous`, with literal `2`. The circled 2 is legible; only its role as the revision is uncertain.
- **F035 p3 decision:** `ambiguous` is kept. The literal is corrected to the handwritten spelling ("delapidated"), and the location `outside_title_block` is added.

## Document-field rulings

Every row is `resolved_for_scoring = yes`.

| Field | carries_fact yes | carries_fact no |
|---|---|---|
| identity | 10 (F035, F038, F042, F044, F047, F048, F049, F051, F053, F054) | 1 (F045) |
| revision | 1 (F035) | 10 |
| decision | 2 (F035, F038) | 9 |

## Questions

- **F035 compilation:** F035 is one document for the gate, with page-level truth and page-level scoring.
- **F035 p2 revision:** corrected to `ambiguous`.
- **F035 p3 decision:** `ambiguous` is kept, with the literal corrected.
- **F038 class:** `approved` is kept on all four pages. The conditions are standard, and the approval is initial-stage.

## Proposed convention topics

- **(b) Evidence strings:** "render F###-pN.png" resolves to the render (F038 p1 decision, F038 p3 identity).
- **(d) Authority approvals:** an authority's initial or conditional approval with generic conditions is `approved`. A third-party pre-check stamp is noted, not used as the field.
- **(e) Code letters:** a code letter is classed by the legend printed on the page. "D - Deferment" on the F035 p2 form is `other`, not `rejected`.
- **(h) Compilation files:** a compilation file is one unit with page-level scoring.
- **(i) Readable but uncertain values:** a readable value whose role is uncertain is `ambiguous`, not `illegible`. A mixed handwritten outcome stays `ambiguous`.
- **(j) Helper template regions:** all Infinity title-block regions were checked. F038 p3 is clipped slightly at the left edge, which is tolerated.
- **(k) Rotated crops:** none in B5.
- **(c) Same number on different drawings:** F048 and F054 both print SHEET NO. FA-05 on different drawings. They are two documents, and the scorer must key on the pool id.
- **(a) Uncertain association:** does not arise in B5.

## Other observations

- **Missing other identity:** the draft `other_identities` for F047, F048 and F049 omit the printed "OLD APPLICATION NUMBER 2020 - 4 - 1072822".
- **Render orientation:** drawing renders are landscape (1800x1272).
- **Earlier run:** the scratch folder r32rev-B5 held integrity and scope scripts from an interrupted earlier run, but no batch response file. This run re-ran those scripts and ruled every row from scratch.

**Could not open:** nothing. Every cited render and crop opened and was legible.

## Independence statement

- **Reviewer:** a fresh workflow subagent, Claude Opus 5.5 (claude-opus-5-5), at effort high.
- **No access to the drafting session:** this review had no access to the drafting session, predictions, ledgers or earlier experiment outputs.
- **No model requests:** no provider or model request was made. The reading of the page images is the review.
- **Files opened:** only these:
  - the fresh-cohort-r32 packet (read-only);
  - C:/t/r2x/r32-stage renders, text layers and crops;
  - this agent's own scratchpad subfolder r32rev-B5 (scripts and zoomed crops of renders);
  - this review folder.
- **No changes elsewhere:** no frozen artifact was modified, and no packet script was run.

This is an owner-delegated independent Claude AI review. It is NOT human sign-off.
