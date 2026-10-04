# Batch B7 note: independent label review of r32-labels-draft-1 (project EP-15744)

**Task:** ORCH-01A.1/B7 (agent label R32REV-B7).

**Kind of review:** an owner-delegated independent Claude AI review. It is **not** a human sign-off.

**Status:** DONE. The review started at 2026-10-03T04:58:47Z and finished at 2026-10-03T05:11:01Z.

**Output:** `batches/REVIEWER-RESPONSE.batch-B7.json`

**Pool ids:** F043, F055, F061, F062, F063, F064, F065, F067, F068, F069, F071. The byte-identical F070 is counted once, through F067.

## Integrity check
- **Manifest:** the sha256 of `evidence/EVIDENCE-MANIFEST.json` is `15c4114d…82d0ed`, as expected.
- **Manifest files:** all 110 listed files match their hashes, and none is missing.
- **Named files:** the draft labels (`ebd1e24d…a688`), conventions, frozen selection, source manifest, CROPS.jsonl and EVIDENCE-INDEX all match their expected hashes.
- **Reviewer columns:** every reviewer column in both worklists is blank.

## What was ruled
- **Page-field rows:** 78 expected, 78 ruled.
- **Document-field rows:** 33 expected, 33 ruled.
- **Questions:** 4 expected, 4 answered.

## Page-field rulings per field

| Field | Accept | Correct | Reject | Unresolved |
|---|---|---|---|---|
| identity | 19 | 7 | 0 | 0 |
| revision | 25 | 1 | 0 | 0 |
| decision | 25 | 1 | 0 | 0 |

The corrections:
- **F043 p1, identity:** region only. The draft region boxes the Gregorian date line, not the reference `ش إ م / عام/٢٠١٤ / ١٣٢٤`. The literal itself is confirmed.
- **F043 p2–p4, identity:** the state stays ambiguous, with two changes:
  - the header candidate is recorded as printed, `ANNEXU RE B`, instead of the fragment `RE B`;
  - the region now covers the footer candidate `ANNEXURE BROV.01nOF12`, which the draft region left out.
- **F061 p4, identity:** region only. The draft region boxes the year `2018`, not `K18`.
- **F067 p1, revision:** region only. The value `00` lies outside the draft region.
- **F067 p1, decision:** the state stays ambiguous. The actor is refined to the client, Command of Military Works (inferred from the arc of the stamp), and the location is in the title block. The stamp is dated 10 MAY 2017 and carries no decision wording.
- **F069 p1 and p3, identity:** the state changes from present to **ambiguous**. `Refrence : EP-15744` is the contractor's project/job number:
  - the same project's pages print it as Project ID (F062, F063) and as Oracle Job No. (F068);
  - both quotations in the file share it.

## Document-field rulings per field

| Field | resolved_for_scoring yes | resolved_for_scoring no | carries_fact yes | carries_fact no |
|---|---|---|---|---|
| identity | 10 | 1 (F069) | 5 (F043, F061, F062, F063, F067) | 6 |
| revision | 10 | 1 (F043) | 1 (F067) | 10 |
| decision | 10 | 1 (F067) | 0 | 11 |

The rulings differ from the draft in one place. F069 identity was drafted as carries = yes; it is ruled resolved = no and carries = no.

## Convention topics proposed
The topics are (a)–(e), (g)–(k) and one new topic, (l). Topic (f), the EMAAR register status letters, does not arise in B7.

- **(a) Uncertain association without a note:** no case in B7.
- **(b) Evidence strings:** `render F043-pN.png` resolves to the staged render.
- **(c) Duplicates:** F067 = F070 counts once. A compilation file is not a duplicate.
- **(d) Authority stamps:**
  - an authority's issuer block ("يعتمد") on its own licence is issuance, not a decision (F061);
  - a dated stamp with no wording in an AUTHORITIES APPROVAL box is ambiguous (F067).
- **(e) Code D:** code D means rejected, as the frozen conventions say. A helper mapping does not override that.
- **(g) Form-code suffixes:** a suffix on a form code, such as `P06/TRANS/R1`, is never the document's revision (F062, F063).
- **(h) Compilation files:** a field is resolved only when every component has the same truth (F069).
- **(h2) Project or job number under a "Reference" label:** the identity is ambiguous (F069).
- **(i) Specific items:** F043 annex identity and the F067 stamp.
- **(i2) Line breaks:** a literal must be the whole value, never a fragment of one line.
- **(j) Helper-generated pages:** no B7 document was drafted with a layout helper.
- **(k) Rotated crops:** the drafts for F043 p2 and p4 cite the readable r270 crop, not the upside-down r90 crop.
- **(l) Regions:** a wrong region is a correction even when the value is right.

## Open points and access
- **Files:** every image and packet file could be opened.
- **Text layers:** the F043 p1, F062 p1 and F067 p1 scans have empty text layers. This did not affect any ruling.
- **F067 drawing number:** it shows a slightly wider gap after `C001-`. The gap is smaller than a full space, so the unspaced literal is accepted, but scorers should treat both forms as equal.

## Independence
- **Agent:** a fresh, isolated workflow subagent. It describes itself as Claude Opus 5.5 (`claude-opus-5-5`) and ran at high effort.
- **Inputs not used:** it had no access to the drafting session, predictions, earlier experiment outputs or ledger. No prediction was consulted, and no provider or model request was made.
- **Files opened:** only files under the frozen packet `fresh-cohort-r32`, and images under `C:/t/r2x/r32-stage` (renders, crops and their text-layer files).
- **Reviewer zooms and overlays:** these are PIL crops of the staged PNGs, made in `scratchpad/r32rev-B7`. No PDF was rendered again.
- **Other batch files:** the batches folder was listed, but no other batch file was opened.
- **Frozen artifacts:** nothing frozen was modified.
