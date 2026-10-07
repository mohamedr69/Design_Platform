# Second independent verification (ep-verifier, read-only), 6 October 2026, on f4d8ca0 (code at 771001e)

**Verdict: CHANGES REQUIRED → ACCEPT WITH NOTES once R1–R3 are applied** (the verifier's words: "With R1–R3 applied the package qualifies for ACCEPT WITH NOTES. None of the three affects a classification, a hash, a count or a test result."). The orchestrator applied R1–R3 and the alignment notes in the commit that records the verdict; the diff is `R-fixes.diff` in this folder.

## Items checked

| Item | Checked how | Result |
|---|---|---|
| Scope | `git diff 285857c f4d8ca0 --stat`: 12 files, all under the refresh folder; `git diff 771001e f4d8ca0 --stat -- backend frontend` empty; tree clean | PASS |
| C1 hash index | file_count 93, 93 entries; exactly the ten listed files added, none of the 83 old entries changed; sha256 and size recomputed from `git show 771001e:<path>` for the ten, 10 random others (seed 20261006), then all 93 | PASS, 93/93; note no longer says "every"; test_output_hashes 9/9 match the committed blobs |
| C1 completeness | Every `backend/…` and `frontend/…` path in every cell of both CSVs extracted and resolved against the 771001e tree | PASS. Only unhashed full path is the removed `ProjectRedesignPage.tsx` in F002's historical cell (listed as absent); other unhashed names are RD-M1 `evidence/scripts/*.py` (covered by the RD-M1 manifest) and the absent RD-M2 `verify.py` |
| C2 log | `git ls-files` lists the log; `git check-ignore -v --no-index` gives `.gitignore:17:*.log`; added in f4d8ca0, ends "116 passed, 68 warnings in 156.14s" | PASS; §2 says force-added |
| C3 | Acceptance §2 heading | PASS ("section 5") |
| N1 F027 | CSV refresh_note and acceptance §1; confirmed test_drawing_prep.py:356 is a PATCH approve on a coverage detector reaching `adjust()` then `_measure_again` (service.py:1317-1318) with no assertion on the re-measure | PASS on substance; mislabelled "second verification" (R1) |
| N2 F028 | CSV refresh_note; ai.py:12 PROMPT_VERSION and config.py:426-428 confirmed | PASS on substance; mislabelled (R1) |
| N3 offsets | `git show 771001e` of service.py and walls.py | CSV F002 1551 right; CSV F008 current_location 952 right; walls.py:25-26 NOT_WALLS, :27 VERSION as C10 and S08 now say; delta .md F002 still `S:1550` and F008 current_quote still 947-950 (R2) |
| N4 | Acceptance §1 | PASS (54-file delta 9/20/1/14/7 and full-manifest delta 14/8/15/1) |
| N5 | CSV owner_milestone | PASS (F017 "M5; M11 secondary", F032 "M5 + M7 + M10; M11 secondary"); primary owners unchanged |
| N6 | Acceptance record | PASS (scope note at the end of §2) |
| CSV structure | python csv | PASS: delta 35×30, header and all 840 data cells of columns 1–24 equal RD-M1's CSV, same id order; new surface 22×24 |
| §5 | Acceptance record | PASS (first verdict stated, "pending second verification"); two small inaccuracies noted below |

## Counts measured
STILL OPEN 32, SUPERSEDED 1, NOT REPRODUCED 2, FIXED 0; finding severity 2/9/18/6; candidate severity 1/8/10/3; 93 source files plus 9 test outputs hashed; all 63 files under backend/app/{redesign,review,interfaces,ifc} at 771001e hashed.

## Completeness result
In the CSVs, no cited in-tree file is unhashed. In the .md records and surveys, two in-tree files are cited but not hashed, neither locating a finding: `services/shop_drawings.py` (a negative grep hit) and the Alembic migration in the warnings line, which the coverage map and TEST-RESULTS misnamed (`e1f2a3b4c5d7_ifc_worker_and_ai_review.py`; the file is `e1f2a3b4c5d7_ifc_worker_identity_and_ai_review.py`).

## Remaining defects (fixed by the orchestrator in the recording commit)
- R1. F027 and F028 refresh_note credit N1/N2 to the "second verification"; should read "first verification".
- R2. Delta .md F002 `S:1550` → `S:1551`; CSV F008 current_quote `service.py:947-950` → `service.py:952`.
- R3. Hash-file note claimed the second verification's re-check ahead of time; reworded to cite acceptance record §5.

## Notes (no change required for acceptance; applied where the orchestrator could)
- Delta .md lagged the CSV: F028 basis "No code defect to cite" (also in new-surface .md), F027 row without the N1 caveat, F017/F032 without M11 secondary. Aligned.
- Acceptance §5 said "seven cited files" (ten were added: seven from cells, three from S7 prose) and "N1–N7 applied" (N7 needed nothing). Corrected.
- Scribe count differed between §4 ("two") and §7 ("three"). Corrected to two.
- C10 cites walls.py:23-27 in two cells; the range includes 25-26 plus the comment; acceptable.
- S6 and S7 keep the old offsets as raw survey evidence; correct.
- TEST-RESULTS.md keeps the misnamed migration; it is the runner's record.

## Limitations
Tests not re-run in this pass (relied on the first pass's re-run; log and XML checked by hash and summary line); classifications re-sampled only for F002, F008, F017, F027, F028, F032 and C10; completeness checked by regex over CSV cells and .md prose (a citation without a .py/.ts(x) extension would be missed); read-only git commands only; working notes `hashcheck.py`, `complete.py`, `notes.md` in this folder; tree clean at the end.
