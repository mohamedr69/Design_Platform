# M2 refresh — Golden Case GC-01 status

| Item | Value |
|---|---|
| Date | 6 October 2026 |
| Repository HEAD | `457c8159c7c587a36e40f0ba2af711a55cc3f00a` (457c815); code under `backend/` and `frontend/` identical to 771001e (orchestrator statement) |
| Sources | `evidence/surveys/S7-new-surface.md` section 6 (Table E, "S7") and section 7; `evidence/surveys/S6-findings-delta.md` section 6 ("S6"); `evidence/TEST-RESULTS.md`; RD-M1 `GOLDEN-CASE-SELECTION.md`, `REPRODUCTION-RUNBOOK.md`, `BASELINE-MANIFEST.json`, `PACKAGE-MANIFEST.json`, `evidence/E16-source-binding.json` |
| Companion files | `M2R-FINDINGS-DELTA.md`, `M2R-FINDINGS-DELTA.csv` |

**Snapshot statement.** This is a static reading of the branch. Tests were run by ep-test-runner as recorded in `evidence/TEST-RESULTS.md`. No model, AutoCAD, database or Golden drawing was used by anyone in this refresh. The hash checks in sections 2 and 3 were made by the surveyor (S7) with `sha256sum`; the scribe did not repeat them.

## 1. Scope and result

GC-01 is project 5 (EP-30880), IFC drawing 1 (`FIRE ALARM LAYOUT.dwg`, R0), redesign row 1, the only Redesign record in the RD-M1 audit snapshot. RD-M1 registered 11 sub-cases GC-01a to GC-01k, all slices of that one drawing (RD-M1 `GOLDEN-CASE-SELECTION.md`).

S7 headline: "GC-01 as a whole is NOT reproducible from this repository (no DWG/DXF/DB/plot); the module library, the evidence JSON and the 26 render/crop PNGs are, and verify by hash."

In short:

- What is here and verifies by hash: the three module library DWGs and `modules.json` (the last after line-ending restoration), the 78-file RD-M1 package (73 exact, 5 after line-ending restoration), and 26 of 26 renders and crops.
- What is not here: the source DWG and DXF, the six trade DXFs, the review plot, the wall index, the original Apply script, the database snapshot, the 17 earlier applied DWGs and the AutoCAD log. Each is pinned by hash in an RD-M1 evidence file (section 3), so a copy on the owner's machine can be checked against it.
- No GC-01 sub-case can be re-run end to end from this repository. The re-runnable cases here are the test suites (section 7), which use synthetic input.
- GC-01 has no baseline for the new surface (Drawings Preparation). It predates it (section 4).

## 2. What is in this repository and verifies by hash (S7 Table E, E1)

| Item | RD-M1 identity | Where it is | How it was checked now | Hash source |
|---|---|---|---|---|
| Module library `CR.dwg` | sha256 `d0b4cd2244d45ae5913a8e01b3eb1ff623333bdc5f03598a8d2f77f9536e888a`, 40,613 B | `backend/app/redesign/library/CR.dwg` | `sha256sum` equal | `evidence/E16-source-binding.json`; `BASELINE-MANIFEST.json` `redesign_library` |
| Module library `CT1.dwg` | `f43361eab514f2c718e9e1d5dca9d87fe4d58761411fcf6967c549f5f795e3b8`, 39,653 B | same folder | equal | same |
| Module library `CT2.dwg` | `7afd3a163ec433253eabab7864c27e258726f1c60d34348e2f12a9a84a664686`, 39,365 B | same folder | equal | same, and `golden_case.files.lib_CT2` |
| `modules.json` | manifest `3dddf8e7a81794877aa28b515222580840ea5646a3a6f67b1b9acee07cec5c05` (728 B, CRLF); now `27acf22d8491d56b5a59703b74e9135c13eddab678404c3ff459e8873e2fdcc8` (690 B, LF) | same folder | LF to CRLF conversion reproduces the manifest hash | E16; manifest |
| RD-M1 package | 78 files | `docs/milestones/redesign/RD-M1/` | 73 exact, 5 equal after CRLF restoration, 0 missing, 0 differing in content | `PACKAGE-MANIFEST.json` |
| Evidence JSON E01 to E18 and 17 scripts | per the package manifest | `docs/milestones/redesign/RD-M1/evidence/` | as above | `PACKAGE-MANIFEST.json` |
| Renders and crops | 13 pairs: 8 PNG in `renders/`, 18 in `crops/` | `docs/milestones/redesign/RD-M1/renders/`, `crops/` | 26 of 26 equal the sha256 in E17 | `evidence/E17-render-index.json` |
| Stored plan as data | 31 review changes, 200 interface changes, the redesign row, jobs, usage | `E03`, `E06` (98 KB), `E07` (80 KB), `E02`, `E09`, `E14` | files present; content not re-derived | `PACKAGE-MANIFEST.json` |
| Apply failure evidence | script lines with the PC-A library path; AutoCAD log tail | `E01` (redacted), `E05`, `E13` (redacted) | read | `PACKAGE-MANIFEST.json`; the redacted `E01` does not hash like the original script, by design |
| RD-M1 code | `BASELINE-MANIFEST.json` `code_files` | the current tree and git commit b5c2222 | 29 of 35 non-DWG code files are recoverable from b5c2222 with a blob hash equal to the manifest hash (`conftest.py` from af7de8f, `test_ifc_worker_and_ai.py` from eb057eb); 6 are not recoverable (`core/config.py`, `interfaces/export.py`, `pdf.py`, `service.py`, `visual.py`, `tests/test_fa_interfaces.py`) | `BASELINE-MANIFEST.json` |

Fixtures: `backend/tests/fixtures` holds four JSON files (BOQ and variation data) and nothing for Redesign. A search for `*.dxf` and `*.dwg` in the repository returns only the three library blocks (S7 Table E, E2).

## 3. What is not in this repository, and the RD-M1 file that pins it (S7 Table E, E2)

| Item | Identity recorded by RD-M1 | RD-M1 evidence file holding the hash |
|---|---|---|
| Source DWG `GC01:ifc/60de2a377daa.dwg` | sha256 `66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21`, 4,380,643 B (equals the review and redesign `source_sha256`) | `E16-source-binding.json`; `BASELINE-MANIFEST.json` `golden_case.files.source_dwg` |
| Source DXF `GC01:ifc/60de2a377daa.dxf` | `dbe7900f21033b2a9c5d3379c93cbf56250735143f8a424559b09a9d4ee5c14f`, 28,233,874 B | `E16` |
| Trade DXF `GC01:interfaces/496fe63ac0554a1ff64ce0f4.dxf` | `686438ed5c3600691018cdad64ef4dd1cdff2810d65b8fcafded9c1f029e0a8b`, 43,212,344 B | `E16` |
| Trade DXF `.../8eea8dd66621d1ecfd0f49e0.dxf` | `a8710daa27609632a1d8b4ad10bca599551f4721447cc399bd0660922183e5da`, 29,851,807 B | `E16` |
| Trade DXF `.../a3eda9255e7a52fcc37084c6.dxf` | `c9691cab04f80ea7cc04f7e98c86329d2fb9d4348ce0784b7600cb099605248c`, 24,670,328 B | `E16` |
| Trade DXF `.../a7fb4efa61a6ddb3f6b991ac.dxf` | `314728442f580f31bd2182a28b82226965b424f55bb59a588ad5cfb1b370c2df`, 40,470,768 B | `E16` |
| Trade DXF `.../eda8dd8d07475ef00c8e299c.dxf` | `044c709a1a8f3b91a660d49f3899f7b7a66ef50e1e04e00e43a4d6472b2562f9`, 23,200,065 B | `E16` |
| Trade DXF `.../fe304ccf33fac4f68bedbcbf.dxf` | `ab3edfe50ce970af400fbedffd95856ab35090ed66960882804ff9adb4b501fd`, 31,609,477 B | `E16` |
| Review plot `GC01:review/66043c11fab9eaf5a1768ba2.pdf` (20 pages) | `2dd28b0480adcd2beb47dab31558ee5dc88fec72334c0add48a1fd1a5a9f2dae`, 13,598,514 B | `E16`; manifest `review_pdf` |
| Plot working files `GC01:review/plot-66043c11fab9/` and `plot-8eea8dd66621/` (`drawing.dwg`, `plot.scr`) | recorded per file in `E16` (for example `plot.scr` of the first folder `2e050116f4ff22870fd55d80b703f1a11964859ad4663144f3725f7c6e91349c`, 100 B) | `E16` |
| Wall index `GC01:redesign/walls-1-66043c11fab9eaf5-v1.pkl` | `9e5a94c17fa2573faaed31c4c909673ac8ce49cbb420fcb6b1c82647d8ec6197`, 4,220,035 B | `E16`; manifest `wall_index` |
| Original failing Apply script `GC01:redesign/work-1/redesign.scr` | `e2daf55bfe7edf4f9d0f93d0c646135b5eb4c9119bfd7b3af37e854ef9d019a0`, 11,283 B. Only the redacted `E01` is in the repository (its hash differs by design); RD-M1 regenerated the original byte for byte from the DB snapshot | `E16`; `E18-reproduce-apply-input.json` |
| Database snapshot `ep_platform.audit-snapshot.db` | `b50dfe2b14ae381158cb47778651f8ce9bcf3dbed985e7b3af81a0821a8df8f0`, 332,709,888 B; alembic `c5e7a9b1d3f5`; 108 `review_rulings`, 1,139 `result_cache` rows | `E12-db-snapshot-info.json`; manifest `database` |
| 17 earlier applied DWGs `GC01:redesign/FIRE ALARM LAYOUT R0 - Redesign 2026-10-02 HHMM.dwg` | one hash each in `E16`; for example the 1625 file `4a512056e70b64e62198bf33e04f329cfc87fbd221f810ec6b9fd346eaac8664` | `E16` |
| AutoCAD log tail and `ErrorReports/…/cer.log` | `cef383c246a9015b3b32daff04d38854c83f9c4f06b9438484c90a4693ae9b37`, 9,870 B (the full AutoCAD log is not kept on failure; only the tail is in the repository) | `E16`; `E13`; job error in `E02` |

`GC01:` is the case's upload folder on the RD-M1 machine. The DB snapshot was kept outside the repository by RD-M1 (S6 section 6).

## 4. What this means for each GC-01 sub-case (S7 Table E, E3; S6 section 6; RD-M1 GOLDEN-CASE-SELECTION)

"Here" means what a reviewer can look at in the repository. "Re-run here" is no for every sub-case: each needs at least one input from section 3.

| Sub-case | Findings | Here | Needed to re-run | Re-run here? |
|---|---|---|---|---|
| GC-01a modules CT1, CT2, CR; failed Apply | F001 | Library hashes; `E01`, `E05` script text and paths; `E02`, `E13` logs | DB snapshot (changes, via `E05`, `E03`) to regenerate the Apply input with `E18` / `reproduce_apply_input.py`; AutoCAD for the "Function cancelled" outcome | No. The defect itself is decided statically (S6) |
| GC-01b wall devices on non-wall geometry | F005, F006 | Crops `GC01-R02*`; change JSON in `E06`, `E07` | `source.dxf` with `evidence/scripts/wall_layers.py`, `effective_layer.py`, `invisible_flag.py` (gives `E10`, `E11`) | No |
| GC-01c ceiling devices; symbol-text overlap | F009 (cause class F008) | Crops `GC01-R02*`; `E06` `insert.seen` for changes `3ddaa99cd7374341`, `45efbfb70918a4f0` | A new Plan on the GC-01 snapshot and a new render from `source.dxf` | No |
| GC-01d wrong target in another room (REMOVE) | F003 | `E06` change `d89599d510abfedf`; crops `GC01-R06*` | A model call through `PR._ask_review` | No; not static |
| GC-01e wrong room; dense symbols and notes (FA 108) | F029 | `E06` change `5d2de6f964bab9e3`; crops `GC01-R07*` | A model call | No |
| GC-01f external-discipline information; cross-discipline transformation (FA 101 B3-SEF-1, -3, -4) | F007 | Renders `GC01-R01*`, crops `R04*`, `R05*`; `E07` anchors | Re-run `interfaces.build` and `add_interfaces` on the snapshot with the six trade DXFs and `project_fa_interfaces`; compare with `E07` | No |
| GC-01g multi-sheet; typical plans; floor mapping | F026 (and F025) | Render `GC01-R12*`; `E04` `failed_errors` | The same interfaces re-run as GC-01f; `E04` `sheets_of_changes` after a new Plan | No |
| GC-01h dense modules, doors (FA 117 roof) | F011 | Renders `GC01-R10*`, crops `R11*` | A new Plan and render from `source.dxf` and the stored plan | No |
| GC-01i wall devices beside doors; orientation uncertainty | F013 | `E06` notes (changes `45efbfb70918a4f0`, `13059eaeb6b87480`, and others); `E04` symbol list | A new Plan, which needs model calls | No |
| GC-01j previous Apply success | F002 (whether earlier outputs held unapproved placements) | Hashes only, in `E16` | The 17 DWGs, opened with AutoCAD or an ODA converter (none was available to RD-M1) | No |
| GC-01k AI repeated answers | F028 | `E08` stored data (2 of 31 changes) | `E09`, `E08`, `evidence/scripts/ai_variation.py` on the snapshot, or fresh model calls | Evidence only; not re-derived here |

**No Golden evidence exists for the new surface.** GC-01 predates Drawings Preparation. The RD-M1 snapshot is at alembic `c5e7a9b1d3f5`, so it has no `project_redesign.run` column (migration `e6a8c0b2d4f6` came later), no columns index (VERSION 2 pickle), no coverage figure, no orchestrator verdict and no gate for it (S7 Table E, E3). A delta baseline for the new stages N01 to N11 needs a fresh Plan on the GC-01 drawing, which needs the DXF, the plot, the wall index and the DB. S7: "The agents-off path (N02 fallback + N03-N05 + N07 + N10) calls no model and is the natural first deterministic re-run; whether it is stable run to run is not tested here."

**RD-M1's gaps still stand.** The categories RD-M1 listed as missing (simple single-sheet drawing, rotated or transformed drawing, PDF or IFC source, modelled doors and windows, second project, inspectable Apply output) remain missing. The 116 tests do not fill them: they build geometry in code (a hand-made `Walls` and `Columns` grid, a blank PDF, a 20 x 10 m "store") and write a stub DXF (S7 Table E, E2). RD-M1's sufficiency verdict (sufficient for Apply safety, insufficient for geometry, coordination or AI-quality milestones) is unchanged.

## 5. Line endings: which RD-M1 files verify only after CRLF restoration

RD-M1 took its hashes on Windows, where files carry CRLF line endings. This checkout stores them with LF (S7 section 0). Converting LF to CRLF reproduces the RD-M1 hash exactly in each case below, so these files are treated as unchanged in content.

| Group | Files | Compared with |
|---|---|---|
| RD-M1 package (5 of 78 files) | `docs/milestones/redesign/RD-M1/FAILURE-INVENTORY.csv`; `evidence/E04-changes-analysis.json`; `evidence/E08-ai-variation.json`; `evidence/E12-db-snapshot-info.json`; `evidence/E18-reproduce-apply-input.json` | `PACKAGE-MANIFEST.json` (the other 73 files hash exactly) |
| RD-M1 code files (7) | `backend/app/redesign/library/modules.json`; `backend/app/review/ai.py`, `pages.py`, `render.py`; `backend/app/interfaces/detect.py`, `matrix.py`; `backend/tests/test_drawing_review.py` | `BASELINE-MANIFEST.json` `code_files` |

The scribe checked the first group with `grep -c` for a carriage return byte: 0 in each of the five files, which agrees with LF storage.

Two consequences for a reviewer:

- To check a hash from the package manifest against one of these files, convert LF to CRLF first (for example with `unix2dos` or `sed 's/$/\r/'`), then run `sha256sum`. A mismatch before conversion is expected and is not a finding.
- `M2R-FINDINGS-DELTA.csv` is not one of these files. Its first 24 columns are cell-equal to `FAILURE-INVENTORY.csv` (compared with Python `csv`: all 35 rows equal), but the file itself has LF endings and every cell quoted, so it will not match the RD-M1 CSV hash after any conversion. The RD-M1 CSV remains the frozen artifact.

## 6. Findings and the inputs that settle them (S6 section 6)

This table is S6 section 6 with the RD-M1 evidence names it gives. "E" numbers are files in `docs/milestones/redesign/RD-M1/evidence/`. Findings F008, F012, F019, F022, F027 and F034 have no row in S6 section 6: S6 decided them by reading code and names no stored input.

| Finding | What static reading cannot settle | Input that settles it |
|---|---|---|
| F001 | That the 6 stored changes still carry the PC-A path; what AutoCAD does on this host | DB snapshot `project_redesign.changes` via `E05-library-paths.json`, `E03`; regenerate the Apply script with `E18` / `reproduce_apply_input.py` (expected sha256 `e2daf55b…19a0`) and look for paths outside the running library; AutoCAD for the outcome (`E01` lines 51 to 54, `E05`, `E13`, `E16`) |
| F002 | Whether earlier Apply outputs held unapproved review placements | The 17 applied DWGs in `E02`, `E16`, opened with AutoCAD or an ODA converter; `E03` (0 review changes proposed in the snapshot) |
| F003 | Whether the new orchestrator would reject the lift-lobby REMOVE | A model call over change `d89599d510abfedf` (`E06`: ai.candidate 11, remove.handle 5DD10) through `PR._ask_review`; crops R06 A and B |
| F004 | Whether AutoCAD continues after a failed `-INSERT` | AutoCAD Core Console on an isolated copy with a missing library block (script as `E01` lines 53 to 56); owner decision C |
| F005, F006 | Layer composition of the current index; whether `29-PARKING` and the invisible flag still pass | GC-01 `source.dxf` with `wall_layers.py`, `effective_layer.py`, `invisible_flag.py` (`E10`, `E11`); `E07` for the two CT2 modules |
| F007, F026 | Whether the equipment-symbol anchor removes the out-of-building anchors and changes the 47 failed counts | Re-run `interfaces.build` and `add_interfaces` on the snapshot (trade DXFs, `project_fa_interfaces`); compare with `E07` anchors for CR B3-SEF-1, -3, -4 and `E04` `failed_errors`; render R01, R04, R05 |
| F009, F010, F011 | Instances (overlaps with text, notes, door swings) | Re-plan GC-01 and re-render crops R02, R06, R11 from `source.dxf` and the stored plan; `E06` `insert.seen` for changes `3ddaa99cd7374341`, `45efbfb70918a4f0` |
| F013, F014 | How many answers still state orientation uncertainty; whether the old symbol list contained Emergency Light | `E06` notes and `E04` symbol list; a new Plan needs model calls |
| F015 | Visual result of the bound-xref block insert | `E06` change `34d7690b0446388c` plus the applied DWG (AutoCAD) |
| F016, F017 | Current `output_path` value and job history on the owner's DB | `E03` (`output_path`), `E02` jobs 118 and 119, `E13` worker log "Job 119 was left running by a worker that stopped: requeued" |
| F018 | Nothing to settle (data and code agree); activity gaps | `E03` `change_keys_present`, `E14` |
| F020, F028 | Origin of the 7 `ai_usage` rows; the two repeated answers | `E09`, `E08`, `evidence/scripts/ai_variation.py` |
| F021 | Rotated or twisted sheets | No rotated case exists; needs a new Golden Case. Residuals on GC-01 are in `E15` (max 0.55 m) |
| F023, F024, F033 | Real output versus plan; leftovers; same-minute overwrite | AutoCAD on an isolated copy; `E16` file list; two Apply jobs in one minute |
| F025 | Current floor strings per sheet | `E04` `sheets_of_changes` after a new Plan |
| F029 | Whether the new orchestrator flags "Placed outside, beside door" | `E06` change `5d2de6f964bab9e3`; a model call |
| F030 | How many positions Apply's `refresh()` moves unseen | `E18` regeneration against the snapshot ("25 touches on GC-01" per F032), compared with the plan as last viewed |
| F031 | Whether the archive copy still happens on the owner's PC | The project archive folder `03- Drawings/Redesign` (not reachable from the audit PC) and `E02` `filed` |
| F032 | The race itself | Concurrent live requests (PATCH during Plan, Plan with Apply); only a timing test can show it |
| F035 | Whether any sheet exceeds 1 m residual | None on GC-01 (`E15`); needs a sheet with residual above `CONFIRM_ABOVE_M` |

Reading the table by what each finding still needs that is not in this repository:

- **Extracts that are already here.** Many inputs named above are RD-M1 extracts in `docs/milestones/redesign/RD-M1/evidence/` (E02 to E18). Reading them re-runs nothing; they hold what RD-M1 saw on 3 October 2026.
- **Files from section 3 (DXF, trade DXFs, plot, wall index, DB snapshot):** F001 (regeneration of the Apply script), F005, F006, F007, F026, F009, F010, F011 (re-plan and re-render), F013, F014, F025 (a new Plan), F020, F028 (`ai_variation.py` on the snapshot), F030.
- **The owner's live database or archive:** F016, F017 (current `output_path` and job history), F031 (the project archive folder).
- **A model call:** F003, F013, F014, F029, and F028 if fresh answers are wanted.
- **AutoCAD on an isolated copy:** F001 (the outcome), F004, F015, F023, F024, F033. F002 (earlier outputs) needs AutoCAD or an ODA converter.
- **A case or situation that does not exist yet:** F021 (rotated sheet), F035 (residual above 1 m), F032 (concurrent live requests).
- **No input needed:** F018 (S6: "Nothing to settle (data and code agree)"), and F008, F012, F019, F022, F027, F034, which have no row in S6 section 6.

## 7. The test suites as the bounded reproducible cases

These are the only cases that can be re-run from this repository alone. They use synthetic data and stubbed models. They show what the code does on that data; they are not acceptance and they do not map to the 35 findings (`evidence/TEST-RESULTS.md`, "Limits").

Run by ep-test-runner at 4bab8d2 (the run is the first and only run of each command): Linux 6.18.44 container, CPython 3.13.16, pytest 8.3.4, ezdxf 1.4.4, pymupdf 1.28.2, SQLAlchemy 2.0.36, fastapi 0.115.6; Tesseract and AutoCAD absent; `AI_ENABLED=false`, `DATA_ROOT=` empty. Combined result: "116 passed, 68 warnings in 156.14s". The JUnit file agrees: 116 tests, 0 failures, 0 errors, 0 skipped.

| File | Then (RD-M1, passed) | Now (passed) | Delta |
|---|---|---|---|
| `tests/test_redesign.py` | 16 | 16 | 0 |
| `tests/test_drawing_prep.py` | not run | 14 | +14 (new suite) |
| `tests/test_drawing_review.py` | 11 | 11 | 0 |
| `tests/test_scoped_drawing_review.py` | not run | 13 | +13 (new suite) |
| `tests/test_drawing_review_outcome.py` | not run | 8 | +8 (new suite) |
| `tests/test_fa_interfaces.py` | 10 | 13 | +3 |
| `tests/test_ifc_worker_and_ai.py` | 41 | 41 | 0 |
| **Total** | **78** (four files) | **116** (seven files) | **+38** |

- RD-M1 ran 78 tests in four files. The same four files now give 81 (16 + 11 + 13 + 41), a delta of +3, all in `test_fa_interfaces.py`. The three added suites give the other 35 (14 + 13 + 8).
- **Test ids identical for `test_redesign.py`:** the 16 ids in the current `-rA` listing equal the 16 ids in RD-M1's `evidence/tests/test_redesign.txt`, compared by sorted id. None added, none removed. The file's hash equals the RD-M2 base (`60e0482c…`, S6).
- For `test_drawing_review.py` (11 then, 11 now) and `test_ifc_worker_and_ai.py` (41 then, 41 now), RD-M1 recorded counts but no names, so "no test added or removed" is not established beyond the count. For `test_fa_interfaces.py`, which three tests are new cannot be identified from RD-M1's listings.
- Warnings: RD-M1 reported 50 over its four files; the same four files give 50 now (1 + 6 + 5 + 38). They are the starlette `anyio.abc.BlockingPortal` deprecation and `datetime.utcnow()` in an alembic migration.
- Not run: the full backend suite. `test_fa_evidence.py` and `test_sync_worker.py`, which S6 cites for F001, F017 and F032, were not among the seven files.
- What these suites do not establish: AutoCAD behavior (no script was run), model behavior (stubs), anything about GC-01 or any real drawing, OCR on real scans, and the Apply job (S7: no test of any kind exercises `apply()`).

To repeat the run, from `backend/`:

```
PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= python3 -m pytest tests/test_redesign.py tests/test_drawing_prep.py tests/test_drawing_review.py tests/test_scoped_drawing_review.py tests/test_drawing_review_outcome.py tests/test_fa_interfaces.py tests/test_ifc_worker_and_ai.py -q -p no:cacheprovider
```

Expected last line: `116 passed` (the 68 warnings and about 156 s were recorded on the container above; they may differ on another machine). A different Python minor version is the only environment difference RD-M1 recorded (3.12.10 there).

## 8. What a reviewer must do on the owner's machine to reproduce the rest

The procedure is RD-M1's `REPRODUCTION-RUNBOOK.md`. It reproduces the baseline "without touching live data, without a model call and without AutoCAD". The steps below cite its sections.

1. **Ground rules (runbook section 0).** Work in an `ISO` folder outside the repository and outside anything the platform reads (`DATA_ROOT`, `UPLOADS_ROOT`, `backend/`). Never start the API or a worker against `ISO`. Never open a copied DWG in AutoCAD with save enabled. Use CPython 3.12 with ezdxf 1.4.4, PyMuPDF 1.28.2 and Pillow 12.3.0, and set `PYTHONDONTWRITEBYTECODE=1`.
2. **Fixed inputs (runbook section 1).** Obtain each file listed in section 3 of this document and check its sha256 against the value in `E16` (database snapshot against `E12`). Copy the scripts from `evidence/scripts/` to `ISO/scripts/`; they resolve `ISO/src`, `ISO/work`, `ISO/code` and `ISO/hash` relative to their own folder. If a new database snapshot is taken instead, compare `E12` table counts and expect differences only from activity after 2026-10-03T15:49Z.
3. **Reproduce the RD-M1 baseline (runbook section 2, steps 1 to 9).** Expected outputs include `drawn_total 11`, 33 cache rows and 31 changes with 2 differing answers, 13 PNG pairs equal to `E17`, `segments_kept_total 92093`, `coordinate_seen_differences: []`, `byte_identical: true` and the regenerated Apply script sha256 `e2daf55b…19a0`. Runbook step 7 runs against `ISO/code/backend`, the RD-M1 code copy (379 of 379 hashes verified by RD-M1), so it reproduces the RD-M1 baseline, not the current tree.
4. **Run the current tree the same way.** This is the delta check. S6 section 6 asks for it for F001 (regenerate the Apply script and look for paths outside the running library) and F030. The scribe did not run it and does not state its result. The current `service.py` differs from the RD-M1 copy (1,569 lines now, 1,449 then, S6), so the regenerated script is not expected to equal `e2daf55b…19a0`; any difference needs to be explained, not assumed.
5. **Run the tests (runbook step 8, extended).** Runbook step 8 runs four files and expects 78 passed. The current set is seven files and 116 passed (section 7 above). Compare the 16 `test_redesign.py` ids with `evidence/tests/test_redesign.txt`.
6. **New-surface first re-run.** Make a fresh Plan on the GC-01 snapshot with the agents off (`prep_ai_enabled=False`, `ai_enabled=False`): S7 names this the natural first deterministic re-run, and it calls no model. Run it twice and compare, since stability run to run is untested. Then re-render the crops for F009, F010, F011 (R02, R06, R11) and the interface renders for F007 and F026 (R01, R04, R05).
7. **Model-dependent findings (F003, F013, F014, F028, F029).** Make model calls only with the owner's approval and `ai_policy`; RD-M1 made none. Record the answers beside the stored `E06` answers.
8. **AutoCAD (runbook section 4, not done in RD-M1).** On an isolated copy, with the working directory inside `ISO`, run the Core Console with the regenerated script. Expected outcome from the preserved evidence: `"CT2.dwg": Can't find file in search path … *Invalid* ; error: Function cancelled`, and the copy not saved. RD-M1 did not do this because `accoreconsole` writes outside the working folder (user-profile temp files, `ErrorReports`, registry; see RD-M1 `DATA-SAFETY-REPORT.md`). The same copy answers F004 (does AutoCAD continue after a failed `-INSERT`), F015, F023, F024 and F033. Inspecting the 17 earlier applied DWGs for F002 needs AutoCAD or an ODA converter.
9. **Cases that must be registered first.** At least one rotated sheet and one simple single-sheet drawing (RD-M1 `GOLDEN-CASE-SELECTION.md`, "Requested categories not available"), reviewed by the owner, before F021 or any geometry, coordination or AI-quality milestone can be tested.
10. **Cleanup (runbook section 5).** Delete `ISO`.

Known nondeterminism (runbook section 3): fresh model answers are not deterministic (F028: 2 of 31 changes already have two differing cached answers); AutoCAD execution depends on AutoCAD 2027 and its support paths; geometry fit, wall index, symbols, placement conversion, coordination and script text are deterministic, and PNG renders are deterministic for the same PyMuPDF and Pillow versions.

## 9. Limitations

- Static reading only; the scribe re-verified no hash, code or test. Hash results in sections 2 and 3 are the surveyor's (S7).
- GC-01 evidence in the repository is data and images extracted by RD-M1 on 3 October 2026; nothing here shows the current code's behavior on GC-01.
- S7 notes that, at RD-M1 time, 6 manifest code files cannot be matched to any git blob, so deltas for them are measured against b5c2222, a later snapshot (S7 section 7, unknown 2).
- The HEAD at the time of the test run (4bab8d2) differs from the HEAD of this document (457c815); see `M2R-FINDINGS-DELTA.md`, section 9.
- S6 header says `test_drawing_prep.py` has 25 test functions; `evidence/TEST-RESULTS.md` and S7 say 14. This document uses 14.
