# Batch B1: independent label review of r32-labels-draft-1

| Item | Value |
|---|---|
| Task | ORCH-01A.1 / B1 (agent R32REV-B1) |
| Project | EP-3563 |
| Pool ids | F001, F010, F012, F014, F016, F017, F018, F019, F022, F026, F031, F033 |
| Draft | `r32-labels-draft-1`, sha256 `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334` |
| Response | `REVIEWER-RESPONSE.batch-B1.json` (status DONE) |
| Review kind | Owner-delegated independent Claude AI review. **Not human sign-off.** Nothing here changes the M2 status (CHANGES STILL REQUIRED) or starts M3. |

## Integrity

All checks passed:
- **Manifest:** `EVIDENCE-MANIFEST.json` hashes to `15c4114d…82d0ed`, and all 110 listed files match.
- **Named files:** the draft, conventions, frozen selection, source manifest, `CROPS.jsonl` and `EVIDENCE-INDEX.json` all match their expected hashes.
- **Reviewer columns:** every `reviewer_*` column in both worklists is blank.

## Counts

**Expected and ruled:**
- page-field rows: 66 of 66 (22 in-scope pages);
- document-field rows: 36 of 36;
- questions: 15 of 15.

**Page-field rulings:**

| Field | Accept | Correct | Reject | Unresolved |
|---|---|---|---|---|
| Identity | 22 | 0 | 0 | 0 |
| Revision | 20 | 2 | 0 | 0 |
| Decision | 13 | 9 | 0 | 0 |
| **Total** | **55** | **11** | **0** | **0** |

**What the 11 corrections change:**
- **Decision literals (8 rows):** F014 p1–4 and F016 p1–4. The literal becomes the Civil Defence stamp text "مخططات معتمدة" only. The draft joined it with a separate yellow APPROVED box whose author is not established. The region now covers the stamp. State, class (approved), actor and association are unchanged.
- **Revision regions (2 rows):** F022 p1 and F026 p1. The value 00 is correct, but the drafted region missed it in the rotated title block.
- **Decision location (1 row):** F026 p1 changes from `in_title_block` to `outside_title_block`. The stamp sits in the sheet margin beyond the frame.

No identity, revision or decision value or class was found wrong.

**Document-field rulings** (resolved_for_scoring / carries_fact):

| Field | yes / yes | no / no |
|---|---|---|
| Identity | 12 | 0 |
| Revision | 11 | 1 (F019, ambiguous: cell 00 against table 01) |
| Decision | 12 | 0 |

**Gate caution:** F001 and F031 should count once in each field. Pages 1–2 are pixel-identical, and the identity, revision and decision values are the same (proposed topic c). Counted that way, the distinct B1 contribution is:
- identity: 11
- revision: 10
- decision: 11

## Convention topics proposed

- **(d) "Approved as noted / Resubmit":** class `approved as noted`, with the literal kept verbatim. Applies to F001, F017, F022, F026, F031 and F033.
- **(d) Civil Defence approved-plans stamp:** class `approved`. The faint "FOR INFORMATION ONLY" box is the issuer's status option, not a decision. The literal is the stamp text only. Applies to F014 and F016.
- **(c) Content duplicates:** render-identical in-scope pages with the same values count once. Applies to F031 and F001.
- **(i) Revision conflict:** when the labelled revision cell and the latest table entry disagree, the state is `ambiguous` and the field is not scored. Applies to F019.
- **(b) "render F###-pN.png" evidence strings:** all three cases resolve to existing renders. Normalise them to the bare file name.
- **(j) Template-constant regions:** these failed three times in this batch (F022 and F026 revision regions, F026 location). The F014/F016 decision region also takes in the notes column. The F016 yellow APPROVED box moves between sheets.
- **(k) Rotated crops:** every cited rotated crop is the upright one.
- **New topic, stamp beyond the title-block frame:** `outside_title_block` (F012 as drafted, F026 corrected).

**Topics that do not arise in B1:** (a), (e), (f), (g) and (h). For (e) only, a rule is proposed without evidence from this batch: class follows the page's own printed legend; without a legend, D is `rejected` (convention 5).

**Region rule applied:** a drafted region is accepted when the value's centre lies inside it after widening by 0.01 page fraction.

## Could not open

Nothing failed to open. Every in-scope render and every crop cited by a draft row was opened.

Six uncited crops listed in `CROPS.jsonl` were not opened, because the cited ones were readable:
- F017-p1-0.81_0.86_0.92_0.92;
- F019-p1-0.03_0.84_0.2_1-r270;
- F019-p1-0.03_0.68_0.45_0.86-r270;
- F019-p1-0.08_0.86_0.12_0.99-r90;
- F019-p1-0.08_0.84_0.2_0.92-r90;
- F022-p1-0.03_0.84_0.33_1-r270.

## Independence statement

- **Agent:** a fresh, isolated workflow subagent (self-reported model Claude Opus 5.5, claude-opus-5-5) with no access to the drafting session.
- **No predictions:** no predictions, application outputs or earlier experiment outputs were consulted.
- **No outside requests:** no network, provider or model request was made.
- **Files opened, packet:** only `fresh-cohort-r32` was used. SOURCE-MANIFEST and RENDERS were read for page counts and staging records; the `relative_path` metadata was never used as evidence.
- **Files opened, staging:** `C:/t/r2x/r32-stage` (renders and crops only).
- **Files opened, scratch:** my scratch folder, which holds three enlargements made from the bound images (F010 box, F022 title block, F031 p3 revision cell).
- **Writes:** none outside the scratch folder and this batch folder; no packet script was run; no git command was used.
