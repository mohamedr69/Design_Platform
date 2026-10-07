# Independent review (ep-verifier, read-only), 6 October 2026 — M2 refresh, first pass

**Verdict: CHANGES REQUIRED.** Three small changes to records and data are needed (C1–C3). Nothing in the package treats a historical finding as fixed. The structural checks pass. Every sampled classification and candidate holds against the code. The bounded cases reproduce: the verifier re-ran the seven suites on a `git archive 771001e backend` copy in the scratchpad and got 116 passed in 158.90 s, with test ids identical to the committed `redesign-suites.xml`. What failed was the traceability index: the hash file's claim to cover every cited file (`unresolved_citations: []`) and the acceptance record's claim that the test log is "in evidence" were false. After C1–C3 the package would be ACCEPT WITH NOTES.

## Gate clause → evidence → result

| Gate clause | Evidence | Result |
|---|---|---|
| Trace current findings to source hashes | Each finding and candidate has a current file:line; files hashed at 771001e recompute; quotes match | Partly: all 83 hashed files recompute, sampled quotes match with 3 line offsets, but 7 cited files had no hash entry (C1) |
| Trace to input hashes | Inputs hashed or stated absent with the RD-M1 file pinning them | Met: Golden-status §3 names each missing GC-01 input with its RD-M1 hash file; source DWG hash in E16, DB snapshot in E12 and the baseline manifest, Apply script in E16; 26 of 26 renders and crops match E17; 3 library DWGs match |
| Trace to output hashes | Test outputs committed with counts | Partly: XML and seven -rA texts committed; `redesign-suites.log` listed but gitignored (C2) |
| Reproduce bounded cases | Exact command; tests present; re-run gives the same result | Met: 116 passed with the same 116 ids on an isolated 771001e copy |
| Historical findings not treated as fixed | Rule written; FIXED 0; SUPERSEDED rests on a test of deterministic code | Met: FIXED 0; F003's AI-only mitigation kept STILL OPEN; F002 open despite two tests pinning current behavior; F027 scoped (N1) |
| GC-01 honesty | States what can only be done on PC-B | Met: every sub-case marked "Re-run here? No" with the reason |

## Structural results
- M2R-FINDINGS-DELTA.csv: 1 header + 35 rows × 30 columns; all 864 cells of the first 24 columns equal RD-M1's CSV; 6 appended columns non-empty; classifications STILL OPEN 32 / SUPERSEDED 1 / NOT REPRODUCED 2 / FIXED 0; severity 2/9/18/6; primary owner M5 14, M8 14, M12 3, M7 2, M10 1, M18 1.
- M2R-NEW-SURFACE-INVENTORY.csv: 22 × 24, header identical to RD-M1's; severity 1/8/10/3.
- M2R-SOURCE-HASHES.json: all 83 entries recomputed and match on sha256 and size; all 9 redesign/*.py present.
- RD-M1 package: 78 entries, 73 exact, 5 equal after LF→CRLF (FAILURE-INVENTORY.csv, E04, E08, E12, E18), 0 mismatched, 0 absent.
- RD-M2 absent: verify.py and test_redesign_apply.py do not exist at 771001e; cad.py (031e760a…) and test_redesign.py (60e0482c…) equal the RD-M1 manifest; service.py differs; `git apply --check` of the candidate patch fails on service.py:34 and the removed ProjectRedesignPage.tsx.
- File delta over the whole 38-entry code/library manifest: 14 same, 8 CRLF-only, 15 changed, 1 removed; the record's 14/7/9/1/20 is correct for S7 Table A's 54 files (N4).
- Tests: XML tests=116, failures=0, errors=0, skipped=0; per class 41/16/14/13/13/11/8 equal to the -rA PASSED counts; "ERROR" lines in the texts are job log lines; test_redesign's 16 ids identical to RD-M1's; 78 → 81 for the same four files; no call to service.apply, cad.apply or /apply/jobs anywhere in backend/tests.
- Code identity: `git diff --stat 771001e <c> -- backend frontend` empty for 4bab8d2, c1f962a, f828ca1, 457c815 and 285857c.

## Classification sample (16): F002, F003, F001, F004, F005, F007, F008, F022, F023, F032, F019, F030, F035, F027, F026, F028 — all CONFIRMED; line offsets in F002 (1550→1551) and F008 (947-950→952); F027 confirmed for its stated scope and imprecise as a whole-finding class (N1); F028 locations confirmed, class basis imprecise (N2).

## Candidate sample (11): C02, C01, C03, C04, C15, C16, C17, C10, C12, C14, C22 — all CONFIRMED; C10 line offset (walls.py 23-24→25-26); existing-test-coverage cells correct (test_redesign.py:213 and test_drawing_prep.py:142-146 pin the current `proposed`-drawn behavior; the gate assertion is at :344 in the test starting :328).

## Cross-record consistency: classification, severity, owner, file-delta, stage, test counts and "no test reaches apply()" agree across all records. Inconsistencies: §2 pointed at section 6 (C3); file-delta scope (N4); three line offsets (N3).

## Frozen folders and scope: changes only under docs/milestones/M1/refresh-2026-10-06/ (M1 commits) and docs/roadmap-sources/ (roadmap U4 commit); nothing under backend/, frontend/, RD-M1, RD-M2, RD-M2-review-correction-r1, M2 or roadmap-evidence; the five M2 commits touch only this folder.

## Mapping decisions (§3): (a) F008–F012 → M8 with M12 for the rendered check is consistent with M8's "doors, ceilings, obstacles, containment, rotation, spacing, coverage and post-change clash checks" and M12's "render the proposed changes, obtain separate visual review"; recorded as a decision, the CSV keeps RD-M1's text; F009/F010 instances need a render (M12). (b) RD-M2→M5, RD-M3→M8, RD-M4→M12, RD-M5→M13 match the appendix; "AI-validation"→M12 and "RD-M6"→M7/M10/M18 are correctly labelled decisions. Consistent.

## Changes required: C1 add the missing hash entries and update the count; C2 commit the log or correct the wording; C3 section reference. Notes N1–N7 as listed in README.md.

## Limits: 16 of 35 findings and 11 of 22 candidates sampled; S6/S7 not re-read in full; engineering severity not judged; RD-M1-era historical statements not verified; `_measure_again` reachability in test_drawing_prep.py:328 not checked; re-run used this container (Python 3.13.16) on a `git archive` copy of 771001e; read-only git commands only (`git archive` output to the scratchpad; `git apply --check` check-only); tree clean after all checks.
