# Batch B4 note: independent label review of r32-labels-draft-1

- **Task:** ORCH-01A.1 / B4 (agent label R32REV-B4)
- **Project:** EP-27331
- **Documents:** F028, F030, F032, F034, F036, F037
- **Status:** DONE
- **Response file:** `REVIEWER-RESPONSE.batch-B4.json`

## Integrity

- **Evidence manifest:** all 110 files listed in `evidence/EVIDENCE-MANIFEST.json` match their sha256 values. The manifest itself is `15c4114d…d0ed`.
- **Frozen files:** the draft (`ebd1e24d…a334`), the conventions, FROZEN-SELECTION, SOURCE-MANIFEST, CROPS.jsonl and EVIDENCE-INDEX all match their expected hashes.
- **Reviewer columns:** blank in both worklists (432 and 210 rows).

## Counts

| Item | Expected | Ruled |
|---|---|---|
| Page-field rows | 69 | 69 |
| Document-field rows | 18 | 18 |
| Questions | 8 | 8 |

### Page-field rulings

| Field | Accept | Correct | Reject | Unresolved |
|---|---|---|---|---|
| Identity | 21 | 2 | 0 | 0 |
| Revision | 20 | 3 | 0 | 0 |
| Decision | 23 | 0 | 0 | 0 |

The five corrections:

- **F028 p4 revision: present/uncertain changed to absent.** The "REV 00" on the Al Arabia "Reply to Consultant Comments" sheet cites the earlier submission that was commented on. The package this sheet belongs to is Rev 1.
- **F032 p1 and F034 p1, identity and revision: regions only.** The helper's constant regions for the cover reference row sit below the printed text. The values are correct.

### Document-field rulings (resolved_for_scoring / carries_fact)

| Field | yes / yes | Any no |
|---|---|---|
| Identity | 6 | 0 |
| Revision | 6 | 0 |
| Decision | 6 | 0 |

Each document carries a consultant decision with resolved association on its cover form (Code B, or Code B+Resubmit for F030). Five of them (all except F028) also carry it on the enclosed sheet's Mirage review block.

## Questions

All 8 questions are answered.

- **Register status letters:** the 6 questions on these are accepted as drafted. The decision is present, the actor is an inferred consultant, and the association is uncertain.
- **F030 B+R class:** accepted as `approved as noted`.
- **F028 p4 revision:** corrected to absent.

## Convention topics proposed

- **(b)** Evidence strings written as "render F028-p4.png" resolve to the render file.
- **(d)** B+R and "Code B+Resubmit" map to `approved as noted`, with the literal kept and a resubmission flag suggested.
- **(e)** Classify by the meaning in the page's printed legend. On this EMAAR/Mirage legend, C and D both invite resubmission, so both map to `revise and resubmit`. No C or D decision occurs in this batch.
- **(f)** Register status letters: present, inferred actor, uncertain association. They never carry the decision for the document on their own.
- **(g)** A tail with the word "Rev" ("-Rev.01") counts as a labelled revision with resolved association. A bare "-R00" stays uncertain.
- **(new)** A revision cited on a reply-to-comments sheet is a referenced revision, not the page's own revision.
- **(j)** The helper template's cover-row regions miss the value on F032 p1 and F034 p1.
- **(a)/(k)** Neither topic arises in this batch.

## Could not open

Nothing. Every in-scope render and every cited crop opened and was readable. No crop in this batch is rotated.

## Independence

- **Reviewer:** a fresh workflow subagent, Claude Opus 5.5 (claude-opus-5-5), with no access to the drafting session.
- **No predictions:** no predictions, application outputs or earlier experiment outputs were consulted.
- **No model calls:** no provider or model request was made, and no packet script was run.
- **Files opened:** only the packet under `fresh-cohort-r32` (read-only) and images under `C:/t/r2x/r32-stage` (renders and crops). Text layers were not used.
- **Files written:** only this batch's two output files and the scratchpad subfolder `r32rev-B4`.
- **Nature of the review:** this is an owner-delegated independent Claude AI review, not human sign-off.
- **Earlier run:** an interrupted earlier run had written only the integrity script, so this review started from scratch.
