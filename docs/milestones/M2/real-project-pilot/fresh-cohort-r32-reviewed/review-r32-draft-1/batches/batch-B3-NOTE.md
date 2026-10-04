# Batch B3 note: independent label review of r32-labels-draft-1

- **Task:** ORCH-01A.1 / B3 (agent label R32REV-B3)
- **Project:** EP-27331
- **Documents:** F008, F009, F013, F020, F021, F025
- **Draft under review:** `r32-labels-draft-1` (sha256 `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334`)
- **Response file:** `REVIEWER-RESPONSE.batch-B3.json`, status **DONE**

This is an owner-delegated independent Claude AI review. It is **not** human sign-off. It changes nothing about the M2 or M3 status.

## Integrity

All checks passed:
- The evidence manifest hashes to `15c4114d…d0ed`, and all 110 listed files match their recorded hashes.
- The draft, conventions, FROZEN-SELECTION, SOURCE-MANIFEST, CROPS.jsonl and EVIDENCE-INDEX each match their expected sha256.
- Every `reviewer_*` column in both worklists is blank (432 and 210 rows).

## Counts

- **Expected:** 72 page-field rows, 18 document-field rows and 4 questions.
- **Ruled:** 72, 18 and 4.

### Page-field rulings

| Field | accept | correct | reject | unresolved |
|---|---|---|---|---|
| identity | 22 | 2 | 0 | 0 |
| revision | 22 | 2 | 0 | 0 |
| decision | 23 | 1 | 0 | 0 |
| **Total** | 67 | 5 | 0 | 0 |

The five corrections:
- **F020 p1 and F021 p1, identity and revision:** only the region changes. The value is correct, but the cover form on these two scans sits higher than the template region, so the drafted region lies below the printed text.
- **F025 p1 decision:** the actor detail changes from "15" to "14 engineer comment lines", and the region now covers the whole red Code C box. State, literal and class (`revise and resubmit`) are unchanged.

### Document-field rulings

| Field | resolved_for_scoring yes / no | carries_fact yes / no |
|---|---|---|
| identity | 6 / 0 | 6 / 0 |
| revision | 6 / 0 | 6 / 0 |
| decision | 6 / 0 | 6 / 0 |

Every document carries its decision on the cover form and on at least one sheet title block, each with a consultant reviewer, so the association is resolved:
- **F008, F009, F013, F020, F021:** Code B, `approved as noted`.
- **F025:** Code C, `revise and resubmit`.

### Questions

All four questions concern the register status letters on F008 p3, F013 p3, F020 p3 and F025 p2. Each is ruled "keep as drafted":
- state `present`, actor `inferred`, association `uncertain`;
- the letters are excluded from `carries_fact`;
- the document decision is resolved by the cover and the sheets.

## Convention topics proposed

- **(f) Register status letters:** these are per-item codes, not a page decision. They are recorded as `present` with association `uncertain` and actor `inferred`. They never count for `carries_fact`. An empty Status column is `blank_decision_area`.
- **(g) Labelled "-Rev.00" tail:** a revision appended with its own "Rev." label is treated as a labelled revision with association `resolved`. The suffix rule, with association `uncertain`, stays for unlabelled `-R00` style tails.
- **(j) Template regions:** a template region is accepted only if the value lies inside it on that page. Otherwise the ruling is "correct" with a region-only change, which has no effect on the gate.
- **(k) Rotated crops:** the draft correctly cites the readable `-r90` crops on F025 p3 and p4. The `-r270` crops of the same regions are upside down.
- **(b) Evidence strings:** the "render F###-pN.png" strings on F008 p3 and F009 p3 resolve to existing renders.
- **(e) Code D:** classify each code by the legend printed in the same package. On these EMAAR/Mirage forms, D reads "Incomplete, Resubmit", so it maps to `revise and resubmit`. No D decision occurs in B3.
- **(d) "B+R" in comment text:** "(B+R)" appears inside an F025 p1 comment about other submittals. It is not a decision.
- **(a) Missing association notes:** none in B3. Every uncertain row has a note.

Topics (c), (h) and (i) do not arise in this batch.

## Other observations

- **F021 p4 `other_identities`:** the draft omits the PART-1/2/3 headings (`B01-02-ASC_EGTS-P03_P04-SD-FA-0005-01/-02/-03`) and a note that cites DWG `B01-ASC-SD-ELE-0014 - R0`. Neither is the page's own number, so the identity ruling stands.
- **Files not opened:** none. Every cited render and crop opened and was readable.

## Independence statement

- **Reviewer:** a fresh workflow subagent, Claude Opus 5.5 (`claude-opus-5-5`), with no access to the drafting session.
- **Predictions:** no predictions, application outputs or earlier experiment outputs were consulted.
- **Requests and scripts:** no provider or model request was made, and no packet script was run.
- **Files opened:** only under the packet folder `fresh-cohort-r32`, `C:/t/r2x/r32-stage`, and the reviewer's own scratch folder. The scratch folder holds two zoom images made from staged renders, used for reading only.
- **Prior run:** an earlier interrupted run had left only scratch helper files and no batch response. This run re-checked integrity and ruled every row from the images.
