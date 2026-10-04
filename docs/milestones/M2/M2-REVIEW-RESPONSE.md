# M2 - Response to Independent Review 01 (R1-R6)

Correction of 2026-09-28 (local). Source: commit `ed7d221df24dbdeac3ababed5de3e128fed0c588` (the reviewed checkout, clean at review) plus the uncommitted correction diff `evidence/r3__m2_review01_changes.diff` (application: `document_control.py`, `document_sync.py`, `document_processing.py`, `design_sheet_extractor.py`, `core/config.py`, `scripts/repair_extraction.py`; tests: new `tests/test_extraction_m2_review.py`, `tests/test_design_sheet_extractor.py` (+1), `tests/test_extraction_m2.py` (2 assertions), `tests/test_document_control.py` (1 patch target)). Versions: `PARSER_VERSION parse-2026-09-28.3`, `BOX_VERSION box-4`; no migration, no business policy, no routing, no calculation changed. Nothing was run against the live database, cache, workers or a model; the backend was not stopped or started; original files were opened read-only. The independent review artifacts are untouched (the probe copy under `C:\t\m2r\probe` is byte-identical: sha256 `0569bd8d...`). All isolated runs used the short scratch path `C:\t\m2r` for pytest and the session scratchpad for evidence, in-memory or clone databases, scratch cache/library/uploads, `AI_ENABLED=false`, settings set before any import.

| Finding | Root cause | Change | Tests / evidence | Remaining limitation | Disposition |
|---|---|---|---|---|---|
| **R1** [P1] A failed re-read erased the last successful reading | `document_sync.process` wrote whatever `extract` returned; an open failure or an OCR exception came back as an empty reading with a note, and the processing loop marked it fresh with the new parser version and time | Readings now carry a coverage ledger with an outcome (complete / bounded / partial / unavailable / failed). Only a complete or bounded reading replaces the stored one. Any other outcome keeps the previous records, `parser_version`, `read_sha256` and `read_at` untouched and records the attempt beside them (`extracted.attempt`: at, outcome, attempted sha256, error, notes, coverage, observations, partial records if any); a changed file marks the kept reading `stale`; top-level mirrors stay consistent with the kept records. A first-time unreadable file is a visible row with an honest attempt and no records. `document_processing.run` sets `failed` (+ error) for failed/unavailable and `fresh` for partial; `pending_rows`/`pending_count` select rows carrying an attempt, so retry picks the incomplete work and a successful retry clears it (idempotent). The repair tool previews/skips partial re-reads and writes the same provenance | `tests/test_extraction_m2_review.py` R1 block (5 tests: corrupt replacement -> second failure -> good retry, OCR failure on a changed scan, failure on page 2 after page 1, new unreadable file, repair-tool preview); cancellation/resume/worker-restart: existing `test_document_processing_v2`, `test_file_sync_v2_processing`, `test_document_sync` (all pass). Reviewer probes re-run on the final code: `unopenable_replaces_previous` and `ocr_failure_replaces_previous` keep the record (`evidence/r3__probe__probe_results.json`) | The attempt lives inside the `extracted` JSON (no schema change); a partial multi-page result is retained as the attempt's records, not merged; resume is per document (a partial reading is re-read whole), not per page | **Fixed** (D-EXT-7) |
| **R2** [P1] Annotation comments and conflicting marks became approval | The annotation path validated with `_options_named` only; `boxed_decision` short-circuited annotation-then-frame, so the first method hid the other | One collector (`decision_marks`) for filled boxes, PDF annotations, drawn frames and highlights; one strict validator (`_label_is_one_option`) for all of them (one option and nothing but its letter/dash/"UR"/"Re"/"Review"; comments, contractor text, receipt labels and partial words are not marks); resolution after collection (`resolve_marks`): agreeing marks resolve, different explicit options are a **conflict** kept as `decision_candidates` (status, label, method) with flag `decision_conflict` and status UR. The record persists candidates and flags; a conflict is stored unresolved, never as approval. Method, label and page stay distinguishable; actor/context: the filled-box/annotation/frame methods are the consultant's marks on the recommendation row; a comment box is never one | R2 block (4 tests: annotation round a comment; contractor/receipt/partial labels under every method; annotation+drawn and filled+annotation conflicts with an agreeing positive control; persistence through normal processing). Probes `annotated_comment_becomes_decision` -> `None`, `conflicting_frame_methods` -> `None`. Existing frame/box/stamp positives unchanged (`test_extraction_m2`, `test_document_control`) | Validation is lexical (the `_OPTIONS` vocabulary); a form with unknown option wording gives no mark rather than a wrong one | **Fixed** (D-EXT-8) |
| **R3** [P2] Pages not accounted for; a leading separator hid the cover | `read_open_pdf` returned after a first page with no record and no pending form, without a note | Bounded page discovery: the first 12 pages are visited regardless of page 1; reply-search and OCR budgets unchanged (12 / 12); the ledger lists `pages_total`, `pages_visited`, `pages_skipped` (each with its reason), `pages_failed` (per-page reader exception -> partial reading), `ocr_failed_pages`, `stop_reason`, `promoted`. Components that must not be legacy register rows are additive `observations` on the reading (`drawing_sheet`, `cover_untracked`, `transmittal`, `decision_unpromoted`, `consultant_comments`); `records` consumers see nothing new | R3 block (6 tests: leading separator, standalone untracked sheet, mixed drawing/reply/datasheet/certificate file with a full page ledger, later consultant section, page-scope limit with skipped pages listed, untracked cover default vs promoted). Probe `leading_page_hides_cover` now visits page 2 and returns the cover. Population (124 documents, `evidence/r3__population_comparison.json`): 351 pages visited, 35 pages skipped on 8 documents (all with reasons), 0 failed pages, outcomes: 116 complete + 8 bounded; observations on 100 documents | Interrupted/resumed traversal is at document granularity (D-EXT-7): there is no per-page cursor; a page past the scan limit is skipped with a reason, not queued | **Fixed** (D-EXT-9); resume granularity stated |
| **R4** [P2] Golden and BOQ evidence gap | 17 visual / 103 regex labels; 687 unresolved; no current-reader BOQ run | (1) **Source review**: every text-PDF case (111) checked on header and recommendation-row crops of the original (19 contact sheets, hashed; `crops/visual_check.json`): 111 of 111 agree with the visually expected status; labels now carry `visual_crop_check_2026_09_28`. The 3 scans were visually checked before (687, 729, 730). (2) **687**: bounded OCR of the reference cell alone recovers `R1029-CSM-CO-ELE-FA-MAR-PJW-ZZZ-ZZZ-1004` (x2 upscale, hyphen kept, nothing guessed); the parser's whole-page read stays truncated and is now flagged `reference_incomplete`; checkbox mark analysis: B darkest (0.31) but not separable from the shaded D box under the rule, recorded **unresolved**, status UR; both visible in the manifest on both paths. (3) Fields verified per case: reference, revision, printed revision / revision source, date, status, listed sheets, system / raw system, category, authorship (printed project code on 687/729/730), components; `printed_revision` is recorded only when printed (an inferred R0 has `revision_source = default`). (4) **BOQ on the originals**: deterministic OCR path, no model, page and row accounting (`evidence/r3__boq_run.json`): FAS 74 golden rows -> 73 lines (69 matched by part, 4 read with a misspelt part, 1 unread in an unruled band, 1 title row dropped with an issue), quantity 68/69; EML 12 -> 12 (11 by part, 1 I/1 misspelling), all quantities right when paired by position. The unread band was silent: fixed as a skipped region + note (D-BOQ-1). (5) No-model verification still `state failed`; not marked successful. Timing on identical work, both cold: 263.8 s (.2) -> 243.7 s (.3) over 124 documents; no latency regression, no improvement claimed | Manifest regenerated after final code and labels (`M2-GOLDEN-MANIFEST.json`, verdicts for `.2`, `.3 default`, `.3 promoted`); `evidence/r3__region687__region_687.json`; `evidence/r3__boq_run.json/.log`; `test_design_sheet_extractor::test_an_inked_band_between_two_tables_is_a_skipped_region_not_a_silent_gap`; visual sheets in the scratchpad hashed in `evidence/M2-EVIDENCE-MANIFEST.json` | 6 Word transmittals keep a "label pending" provenance (no independent check of .docx content was done). The current-reader BOQ defects D-BOQ-open-1..5 (unread band row, TP606 `49`, four misspelt parts, `Field Devices` group not carried into the next table, one I/1) are demonstrated and **open**; the group carry-over is a bounded candidate not made because the group is part of stored line identity. The **model verification path was not exercised** (no model call allowed): its accuracy is missing evidence, not a claim. No engineer sign-off is claimed anywhere; the BOQ fixture is author-transcribed | **Fixed** for Golden review, 687 representation, BOQ accounting and the silent band; **BLOCKED BY MISSING EVIDENCE** for real-model BOQ verification; BOQ reader misreads **open** (reported, not fixed) |
| **R5** [P1] Ordinary-processing compatibility not established | The extract-only CLI proved its own writes only; the corrected reader's first clone repair (run 1) itself failed on 35 rows because an observation carried a raw dataclass dict (a datetime) into the row's JSON column - the ordinary writer would have failed the same rows (D-EXT-10, fixed, persistence test added, run 2 on those rows); `document_processing.run` feeds `submittal_reader.check`, `reconcile_actions` and `shop_drawings.reconcile` from the changed reader with no gate | Enforceable boundary: `Settings.extraction_promote_observations` (env `EXTRACTION_PROMOTE_OBSERVATIONS`), default **false**. Off: decisions read by the M2 methods (drawn frame, highlight) are candidates with flag `decision_method_unpromoted`, untracked-discipline covers and scanned-transmittal samples are observations, a mark on a folder-revision sheet that prints another revision is held (`decision_revision_unvalidated`) on both paths; filled-box and stamp-annotation decisions, which the previously accepted reader already read, stay records. On: the M2 behaviour, minus the folder-revision hold. Normal route traced and exercised through `document_processing.run` in isolated fixtures: manual submittal status + corrected BOQ line survive a re-read with a drawn frame (the map is not redrawn when no form changed); engineer-confirmed drawing revision survives a contrary reading; folder R1 vs printed 00 held; mangled identity kept apart (second cover, G-M2-6 unchanged). **G-01 still exists**: `sync_register` still overwrites an engineer status when `submittal_reader.check` runs; the correction does not touch it. What changes is the input: on the default path no new decision method reaches it | R5 block (5 tests) + R3/R2 gate tests; population on both paths: default vs M2 submission 84 identical / 24 status held / 16 records held as observations (11 fire-fighting covers, 3 OCR-mangled second covers, 2 scanned transmittals); promoted vs default 86 identical / 22 statuses restored / 16 records restored, the 2 folder-revision holds (120, 122 page 2) remaining on both paths (`evidence/r3__population_comparison.json`). Clone extract-only repair with the corrected reader, default path, form-reading records included: project 4: run 1 522 selected / 484 repaired / 32 failed on the observation JSON defect D-EXT-10, run 2 on those 32: 32 repaired / 0 failed, tables changed ['document_dependencies', 'project_documents'], roles changed 0, form-reading records 9 -> 5 (4 documents changed); project 1: run 1 356 selected / 349 repaired / 3 failed on the observation JSON defect D-EXT-10, run 2 on those 3: 3 repaired / 0 failed, tables changed ['document_dependencies', 'project_documents'], roles changed 0, form-reading records 2 -> 2 (0 changed); vs the M2 submission's repair: project 4 {'identical': 447, 'changed:status': 39, 'records_removed': 32, 'records_added': 4}, project 1 {'records_removed': 3, 'identical': 329, 'records_added': 1, 'changed:status': 23} (`evidence/r3__repair_r3_comparison.json`, `repair_r3__records_before/after.json`) | Equivalence with the accepted reader is not claimed: the default path still reads filled boxes and stamp annotations as before and adds ledger/attempt/observation data inside `extracted`; the promoted path is for isolated evaluation until the owner promotes it. G-01 remains a known defect for M4 | **Fixed** (D-GATE-1, D-REV-2); G-01 open and documented |
| **R6** [P2] Operational audit and recovery | The acceptance report said "no restart" while the handoff admitted a stop/start for the snapshot | Timeline corrected (section 2 below) with reported vs observed facts. Independently observed now (read-only): no listener on port 8000 (`netstat`), no `-wal`/`-shm` beside the live database, and the live `backend/ep_platform.db` is **byte-identical** to the committed snapshot (sha256 `8db43511...` both; 890 documents, no `parser_version` on any reading, last processing 2026-09-27 14:58:09, alembic head `a5b6c7d8e9f0`): whatever the launcher did after the commit, it wrote nothing to the database. Recovery is a separate checklist (`M2-RECOVERY-CHECKLIST.md`), not executed. Population IDs corrected: 24, 122, 313, 316 outside the manifest (22 inside). Hashes refreshed and the current commit recorded (`evidence/M2-EVIDENCE-MANIFEST.json`) | `evidence/r3__live_db_readonly_check.json`; `M2-RECOVERY-CHECKLIST.md`; `M2-BASELINE.md` note; evidence manifest | Whether the API process started and died (its startup would have run migrations/seeds/`fail_interrupted` first) cannot be told from the database alone; only "no database write" is established | **Corrected**; recovery left to the owner |

## 1. Test commands and results

From `backend/`, `TEMP=TMP=C:/t/m2r`, `--basetemp=C:/t/m2r/...` (short path; the reviewer's four path-length setup failures do not occur):

```
venv/Scripts/python -m pytest tests/test_ai_sheet_reader.py tests/test_battery_api.py tests/test_boq_corrections_v2.py tests/test_boq_extraction_v2.py tests/test_boq_geometry_v2.py tests/test_boq_selective_v2.py tests/test_boq_verification_v2.py tests/test_classification_evidence.py tests/test_document_classification_pilot.py tests/test_document_classification_v2.py tests/test_document_control.py tests/test_document_processing_v2.py tests/test_document_routing.py tests/test_document_sync.py tests/test_drawings_module.py tests/test_extraction_m2.py tests/test_extraction_repair.py tests/test_file_sync_v2.py tests/test_file_sync_v2_processing.py tests/test_project_state.py tests/test_repair_tool.py tests/test_submittal.py tests/test_submittal_ai.py tests/test_extraction_m2_review.py tests/test_design_sheet_extractor.py -q -p no:cacheprovider --basetemp=C:/t/m2r/ptfull --junitxml=final_r3.xml
```

Result: **317 tests, 309 passed, 7 skipped, 1 failed, 0 errors** in 308.4 s (`evidence/r3__final_r3.xml`, `.log`). The one failure, `tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows` (a BOQ read run as a background job thread; `FOREIGN KEY constraint failed` on `project_boq_items.extraction_run_id` inside the job, or `UnmappedInstanceError: NoneType` in the full run), is **not attributable to the correction**: it fails identically on a clean worktree of the reviewed commit `ed7d221` with the same interpreter (3 of 3 runs alone; `evidence/r3__flaky_1.log` is the same failure on this tree), passed in the first full run of this correction (`r3__final_r3_run1.xml`) and in the M2 submission's run, and passes when its module runs together with `tests/test_boq_extraction_v2.py` (20 passed, same code, same hour). It is order/timing dependent in untouched BOQ job code (`app/routers/projects.py::_extract_boq`, `app/services/jobs.py`), not diagnosed here, and listed as a limitation for the re-review. A first full run on the code before the observation-JSON fix (D-EXT-10) is kept as `evidence/r3__final_r3_run1.xml` (316 tests, all passing, 392.6 s); it did not contain the persistence test that catches the defect. The 7 skips are the live-archive BOQ sheet tests (`EP_PLATFORM_LIVE_ARCHIVE_ROOT` unset). The 270 tests of the submission are included; `tests/test_extraction_m2_review.py` adds 21; `tests/test_design_sheet_extractor.py` adds 1 and contributes its other 25.

Reviewer probes (`probe_m2.py`, unmodified) on the final code: `unopenable_replaces_previous` -> record kept; `ocr_failure_replaces_previous` -> record kept; `leading_page_hides_cover` -> page 2 visited, cover read; `annotated_comment_becomes_decision` -> `None`; `conflicting_frame_methods` -> combined `None` (annotated alone A, drawn alone C).

## 2. Operations timeline (corrected)

| When (local, 2026-09-28) | Reported (by the author) | Independently observed |
|---|---|---|
| 2026-09-27 evening -> 00:20 | M2 work; every run on clones/scratch; the backend that had been running since earlier in the day was left alone. The acceptance report's "no restart" described this period | - |
| ~00:20 | `stop-backend.bat` run to take a consistent database snapshot for the commit (WAL checkpointed); the acceptance report was not updated to say so | commit `ed7d221` at 00:27:10 contains `backend/ep_platform.db` (95,461,376 bytes) |
| after 00:27 | `start-backend.bat` launched detached (PowerShell `Start-Process`); its four windows were not watched; `/health` never confirmed. The launcher stops this checkout's processes and starts the API (migrations, seeds, `fail_interrupted`) and three workers (`recover_stale`, then queued work) | the review found no port-8000 listener and `GET /health` refused (WinError 10061); this correction found the same (no listener) and the live database byte-identical to the committed snapshot, no `-wal`/`-shm` files |
| during this correction | no stop/start, no launcher, no worker, no live migration, no live processing, no live repair | `evidence/r3__live_db_readonly_check.json` (read-only `mode=ro` connections) |

Conclusion: no live data was changed by the launcher after the commit (database identical); whether the API process ran its startup and exited is unknown; nothing about live processing under `parse-2026-09-28.2` happened (no reading carries a parser version). The M2 acceptance report's operations statements are corrected in place (section "Correction 2026-09-28").

## 3. Evidence package (all under `docs/milestones/M2/evidence/`, prefixed `r3__`; hashes in `M2-EVIDENCE-MANIFEST.json`)

- Tests: `r3__final_r3.xml`, `r3__final_r3.log`; probes: `r3__probe__probe_results.json`, `r3__probe__probe_m2.py` (copy).
- Golden: `M2-GOLDEN-MANIFEST.json` (regenerated), `r3__crops__visual_check.json`, `r3__crops__index.json`, `r3__crops.py`, contact sheets `crops/sheet-01..19.png` and crops (scratch, hashed); `r3__region687__region_687.json`, `r3__region_687.py`, crops (scratch, hashed).
- BOQ: `r3__boq_run.json`, `r3__boq_run.log`, `r3__boq_run.py`.
- Population runs: `r3__parser_population_r3_default.json/.log`, `r3__parser_population_r3_promoted.json/.log`, `r3__run_parser_r3.py`, `r3__population_comparison.json`, `r3__compare_population.py`.
- Clone repair (default path): `r3__r5_repair.py/.log`, `r3__repair_r3__repair_p4/p1.json/.log`, snapshots and record dumps before/after (form-reading records included), `r3__repair_r3_comparison.json`, `r3__compare_repair_r3.py`.
- Source identity: `r3__m2_review01_changes.diff`, `r3__before_manifest.json` (hashes of the tree at the start of the correction: HEAD `ed7d221`, clean), `r3__live_db_readonly_check.json`, `r3__build_manifest_r3.py`, `r3__assemble_evidence_r3.py`.

## 4. Verdict

**READY FOR INDEPENDENT M2 RE-REVIEW**, with these portions stated as they are: (a) the real-model BOQ verification path is **BLOCKED BY MISSING EVIDENCE** in this correction (no model call was permitted; the deterministic path is measured, the verification path is not); (b) the current-reader BOQ misreads D-BOQ-open-1..5 are demonstrated and reported open, not fixed; (c) G-01 is unchanged and documented; (d) the six Word transmittals keep a pending label; (e) no engineer sign-off is claimed; (f) one pre-existing order/timing-dependent BOQ job test fails in the second full run and on the clean reviewed commit alike (section 1). No self-acceptance, no live repair, no restart, no M3 work.


---

# Response to Independent Review 02 (A-D)

Correction of 2026-09-28 (local, afternoon). Source: commit `ed7d221df24dbdeac3ababed5de3e128fed0c588` plus the Review 01 correction and, on top of it, the Review 02 correction (uncommitted; `evidence/r4__m2_review02_changes.diff` is the whole uncommitted diff, `evidence/r4__before_manifest_r2.json` the hashes of the dirty tree before this correction). Versions: `PARSER_VERSION parse-2026-09-28.4`, `BOX_VERSION box-4`, `design_sheet_extractor.PARSER_VERSION 2026-09-28.1`. No migration; no business, revision or calculation policy changed; no live data, backend, worker or model touched. The review files are untouched (the probe copy under `C:\t\m2r2\probe` is byte-identical: sha256 `08b948d4fa55b8ba...`). `backend/library/symbols/symbol_library.json` was found already modified at the start of this correction (its `exported_at` rewritten at 09:10:24 local by an app start outside this session, after the Review 01 package); it is not part of either correction and was left as found.

| Finding | Root cause | Change | Tests / evidence | Remaining limitation | Disposition |
|---|---|---|---|---|---|
| **A** [P1] Legacy readings discarded; bounded runs replaced complete ones | `document_sync.process` kept a previous reading only when it carried `parser_version` (the 367 live payloads carry none); `COMPLETE_OUTCOMES` let a bounded run (page budget reached) replace a reading whose records sat on the pages it never visited | `reading_to_keep`: any previous reading with records, or a modern one (parser version / hash) even without, is kept in front of a failed, unavailable or partial attempt -- records, form evidence (`extracted.form`), mirrors and provenance exactly as they were; `staleness` is True/False when the reading records its hash and **None** (`source_identity: unknown`) for a legacy one: nothing is invented. `carry_unvisited`: a bounded reading carries the kept reading's records from the pages it skipped (and records of unknown page), flagged `carried_unvisited`, plus `carried_unverified` when the file's bytes are not the ones the kept reading was read from (or unknown), with a note and `coverage.carried_from_previous`; the mirrors follow. The same carry in the repair tool's preview/apply. A successful retry replaces the reading and keeps the form evidence | `tests/test_extraction_m2_review02.py`: `test_a_legacy_reading_without_parser_version_survives_failures_and_a_successful_retry` (legacy payload + form -> open failure -> OCR failure -> second failure -> good file; persisted through normal processing, retry accounting checked), `test_a_bounded_re_read_carries_the_records_of_the_pages_it_did_not_visit` (complete 13-page reading, then the repair path on the same bytes, then ordinary processing on changed bytes, then a wider reader), `test_reading_to_keep_and_staleness_tell_legacy_from_modern_from_nothing`, `test_carry_unvisited_keeps_records_of_unknown_page_and_flags_by_source_identity`; the reviewer's probes `legacy_last_success_without_parser_version` (records kept) and `bounded_replaces_more_complete_success` (record carried with both flags) - `evidence/r4__probe__independent_probes_after.json` | A carried record is what the previous content held, marked so; the reader does not read the skipped pages (the budget stands). A legacy reading's staleness stays unknown until a complete re-read | **Fixed** (D-EXT-11, D-EXT-12) |
| **B** [P1] Text and OCR bypassed conflict resolution | Marks were collected only when every text record was UR; the OCR decision replaced the status after the marks had been settled | `settle_decision`: the page's text status (method `text`), every mark (`filled_box`, `annotation`, `drawn_frame`) and the OCR decision (method `ocr`) are candidates settled once per record; different answers are a conflict (UR, every candidate, `decision_conflict`), agreement settles the status when a promoted method is among them, held methods alone are candidates. The stamp-over-tick precedence the reader applied implicitly (comment on the SAR sample) is **withdrawn** until an explicit policy is authorised: that case is now a conflict the record shows; no new approval policy is introduced | `test_a_status_in_the_text_and_a_frame_on_another_option_are_a_conflict` (both gate settings), `test_marks_that_conflict_are_not_settled_by_what_ocr_reads_afterwards` (annotation A + frame C then OCR A; and the reverse; both gate settings), `test_agreeing_text_marks_and_ocr_settle_one_status_with_every_method_recorded`, `test_an_unpromoted_frame_does_not_return_as_a_status_through_ocr_of_the_options_list`, `test_an_ocr_failure_leaves_the_text_and_mark_evidence_to_settle_the_page`, `test_a_frame_round_a_comment_naming_an_option_is_noise_beside_the_text_status`, `test_a_conflict_reaches_the_row_and_its_register_row_as_under_review` (persisted: row status, stored record, `log_records`); `test_document_control::test_a_consultants_stamp_that_disagrees_with_the_ticked_box_is_a_conflict` (was `..._overrides_the_ticked_box`); probes `ocr_overrides_collected_conflict` -> UR with three candidates, `text_decision_bypasses_mark_collection` -> UR conflict | A consumer that wants the stamp to outrank the tick needs an authorised precedence policy (owner); until then such pages read UR with the evidence attached | **Fixed** (D-EXT-13) |
| **C** [P1] The promotion gate was absent from reuse | `parser_current` checked the parser version only; `_previous_sha`, the known-content map and `read_task`'s unchanged shortcut reused a promoted reading with the gate off | A reading's identity is (content hash, `PARSER_VERSION`, **profile**): `extracted.profile` (`default` / `promoted`, from the reading's own `coverage.promoted`) is written by processing and the repair tool; `parser_current` requires the current parser *and* the current profile (`document_control.extraction_profile()`), so `_previous_sha`, the known-content map, `read_task`'s unchanged return and the duplicate copy all recompute on a mismatch; a reading without a recorded profile is not current; the repair selection `parser-outdated` includes profile mismatch | `test_a_reading_carries_its_profile_and_freshness_checks_it` (off -> on: unchanged bytes re-read, on -> on: reused and idempotent, on -> off: re-read, missing profile: not current; `read_task` refuses the unchanged shortcut), `test_a_duplicate_copy_is_not_given_the_other_profiles_reading`, `test_the_repair_tool_selects_readings_of_another_profile_and_is_idempotent_within_one`; probe `promoted_reading_reused_with_gate_off` -> `parser_current false, previous_sha_reused false, task_unchanged false` | A profile change is applied when a row is next processed (a content change) or by the repair tool; rows untouched on disk keep their reading with its profile recorded, never reused as the other's. Engineer-confirmed domain values are not touched by a profile switch (`test_an_engineer_confirmed_revision_survives...` unchanged). G-01 stays as documented | **Fixed** (D-GATE-2) |
| **D** [P2] BOQ correctness, harness race, accounting | Current-reader defects D-BOQ-open-1..5; one BOQ job test failing by order; page categories not exclusive; a 124-row table totalling 120 | **D1** the inked band between two tables is read as rows under the heading in force (`_read_page` -> `_read_table` on the band); a band that yields no row is a `skipped` region **and** an `UNPROCESSED_PAGE_OR_REGION` issue, so the sheet is not accepted as complete over it. **D2** a strip quantity at 60-90 % is checked on its own cell for a cut digit only (`_check_cut_digit`): a pass reading the strip's digits plus one sends the row to review; the low-confidence path keeps its full confirmation with the same rule (`_cut_digit`). **D3** a part number read below 90 % is checked by two independent passes on its cell (`_confirm_catalog`): both agreeing on another whole reading, or a same-length near miss (edit distance <= 2), make the row a review row (`_uncertain_part_issue`, `PART_NUMBER_CONFLICT`, every reading kept); fragments and clipped readings are not evidence; nothing is substituted. **D4** the group heading in force carries across a split table and across pages, reset by a new section banner (`_read_table` / `_read_ruled_rows` return it). **D5** the Golden matcher pairs repeated parts by page and occurrence order (`scripts/boq_metrics.match_rows`). **D6** the six Word transmittals read from their own .doc binary text. **D7** the BOQ job test: traced (`evidence/r4__job_trace.log`: every session on one DBAPI connection, `conn=...` identical for `MainThread`, `AnyIO worker thread` and `job-1-boq_read`; a request session's close issues ROLLBACK on the job thread's in-flight transaction); the defect is the test harness's in-memory database (StaticPool: one shared connection) with a real job thread, not the application (the platform runs a file database, one connection per thread). Fix: the test database is a SQLite file in a temporary folder (`tests/conftest.py`; `EP_TEST_DATABASE=memory` keeps the old harness to reproduce the defect); regression `tests/test_job_thread_sessions.py` (a job flushes a row, waits, commits while the test polls it through the API): fails on the memory harness (the flushed row is gone), passes on the file. **D8** the page ledger has two exclusive dimensions: pages visited / skipped / failed sum to the page count and never overlap (a failed page leaves `visited`), OCR is `coverage.ocr` (attempted, failed, skipped by budget) and `ocr_failed_pages`; the document accounting is over the whole 124-document population with exclusive outcomes | BOQ on the originals (`evidence/r4__boq_run_r2.json`, `.log`; before: `r3__boq_run.json`): see the table below. `test_design_sheet_extractor.py`: `test_an_inked_band_between_two_tables_is_a_skipped_region_not_a_silent_gap` (band read / band unread with the heading carried), `test_a_longer_independent_reading_sends_a_cut_digit_to_review`, `test_a_part_number_the_independent_passes_do_not_confirm_is_a_row_for_review`, `test_the_catalog_check_reads_the_cell_twice_and_keeps_what_each_pass_read`; Word labels `evidence/r4__word_transmittals_independent.json` (6 of 6 read: TR number, date, subject); job test: `evidence/r4__job_trace.log`, `evidence/r4__job_test_runs.json` (alone x3, in its module, mixed order, full suite); accounting: `M2-GOLDEN-MANIFEST.json` `outcome_accounting_documents_parse_4`, `page_accounting_parse_4` | Open reader defects, listed as code defects: the EML two-line cell `+SL23I` is accepted as `+SL231` (the cell passes read fragments of a two-line cell, so nothing flags it); `6538-G5` is grouped under `Booster Power Supply` where the transcriber left it ungrouped (a rule of the sheet's layout, not settled); the band row's part is read as printed and cut (`SIGA-OSHD-FC`), which the Golden fixture names whole. The real-model verification path is still not exercised (no model call permitted): missing evidence, separate from the code | **Fixed** D1-D8 with three reader defects **open** (below); real-model path **BLOCKED BY MISSING EVIDENCE** |

## Deterministic BOQ reader on the originals, before and after

| Sheet | Review 01 reader (`2026-09-15.2`) | Review 02 reader (`2026-09-28.1`) |
|---|---|---|
| FAS (74 golden rows, 2 pages) | 73 lines accepted, 0.932 recall, part 1.000 / quantity 0.9855 / group 0.638 on matched rows; 1 row unread and silent (band), TP606 accepted as 49, 4 misspelt parts accepted, 26 rows without group | 69 lines accepted, 0.919 recall, part 1.000 / quantity 1.000 / group 0.985 on matched rows; the band row read (`SIGA-OSHD-FC`, 525, as printed and cut); 6 rows for review: KEOLAUON LOT LI (quantity), 4-CABI6D (PART_NUMBER_CONFLICT), SIGA-AAS0 (PART_NUMBER_CONFLICT), WSTIA-T (PART_NUMBER_CONFLICT), G1IARN (PART_NUMBER_CONFLICT), TP606 (quantity); outcome NEEDS_INTERPRETATION (not accepted whole) |
| EML (12 golden rows, 1 page) | 12 lines, quantities judged crosswise on the repeated SL210DI | 12 lines accepted, 0.917 recall, quantity 1.000 with the matcher pairing SL210DI by occurrence; open: `+SL231` for `+SL23I` |

Nothing in the reader knows a Golden value; the fixture is read only by `scripts/boq_metrics.py`. No model was called.

## Population, page ledger and clone (Review 02 reader, isolated)

- Population read (124 documents, cold caches): default vs Review 01 default {'identical': 124}; promoted vs default {'identical': 86, 'changed:status': 22, 'records_added': 16}. Document outcomes over 124, exclusive: default {'succeeded_with_records': 110, 'succeeded_observations_only': 13, 'succeeded_no_records': 1, 'total': 124}, promoted {'succeeded_with_records': 123, 'succeeded_no_records': 1, 'total': 124} (no-record documents: [620]). Pages (default): {'visited': 351, 'skipped': 23, 'failed': 0, 'total': 374, 'ocr': {'attempted': 269, 'failed': 0, 'skipped_budget': 12}, 'document_outcomes': {'complete': 116, 'bounded': 8}} -- visited + skipped + failed = total on every document (`document_outcomes` shows no `NON_EXCLUSIVE` / `PAGES_DO_NOT_SUM`). Timing on identical work: 243.7 s (.3) -> 267.5 s (.4); the .4 run overlapped with test runs for part of its time -- not a latency claim.
- Golden verdicts (parse .4): reference, default {'match': 99, 'held: observation carries the reference (promotion off)': 13, 'incomplete: flagged reference_incomplete, evidence in region687': 1}, promoted {'match': 112, 'incomplete: flagged reference_incomplete, evidence in region687': 1}; status, default {'match': 83, 'held: candidate agrees, method unpromoted': 22, 'held: decision observation only (cover held as observation)': 11, 'unresolved: scanned tick, mark analysis inconclusive (region687)': 1, 'held: transmittal observation carries the status (promotion off)': 2}, promoted {'match': 118, 'unresolved: scanned tick, mark analysis inconclusive (region687)': 1}. The six Word transmittals now carry independent labels (systems {'match': 6}).
- Clone extract-only repair (default profile, fresh copy of the read-only clone, form-reading records included): `evidence/r4__repair_r4_comparison.json`.

| Project | Repair manifest | Tables changed | Documents with changed records (all sources) | Roles changed | After | Stored records vs the M2 submission's repair (`repair2`, parse .2) |
|---|---|---|---|---|---|---|
| EP-30088 (project 4) | 522 selected, 516 repaired, 6 skipped, 0 failed, 625.7 s | `document_dependencies` (174 of 306 rows), `project_documents` (516 of 525 rows); project fields changed: False | 165 of 525; form-reading records 9 -> 5 (4 documents); mirrors changed 160 | 0 | states {'fresh': 525}; attempts 0; stale 0; profiles {'default': 516, 'none': 9}; observation kinds {'decision_unpromoted': 66, 'consultant_comments': 209, 'cover_untracked': 36, 'drawing_sheet': 47, 'decision_conflict': 1, 'transmittal': 2}; flags {'decision_method_unpromoted': 44, 'reference_incomplete': 1} | {'identical': 447, 'changed:status': 39, 'records_removed': 32, 'records_added': 4} |
| EP-30784 (project 1) | 356 selected, 352 repaired, 4 skipped, 0 failed, 666.5 s | `document_dependencies` (222 of 384 rows), `project_documents` (352 of 359 rows); project fields changed: False | 24 of 359; form-reading records 2 -> 2 (0 documents); mirrors changed 3 | 0 | states {'fresh': 359}; attempts 0; stale 0; profiles {'default': 352, 'none': 7}; observation kinds {'transmittal': 3, 'consultant_comments': 4, 'drawing_sheet': 50, 'decision_conflict': 3}; flags {'decision_revision_unvalidated': 23, 'decision_conflict': 3} | {'records_removed': 3, 'identical': 326, 'records_added': 1, 'changed:status': 26} |

## Tests

`**337 tests, 330 passed, 7 skipped, 0 failed, 0 errors** in 402.6 s` (`evidence/r4__final_r4.xml`, `.log`; the file-backed test harness). No failures. The BOQ job test runs: {"alone_1": {"args": ["tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows"], "env": {}, "rc": 0, "summary": "1 passed, 2 warnings in 2.65s"}, "alone_2": {"args": ["tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows"], "env": {}, "rc": 0, "summary": "1 passed, 2 warnings in 2.65s"}, "alone_3": {"args": ["tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows"], "env": {}, "rc": 0, "summary": "1 passed, 2 warnings in 3.05s"}, "in_module": {"args": ["tests/test_ai_sheet_reader.py"], "env": {}, "rc": 0, "summary": "7 passed, 7 warnings in 14.11s"}, "mixed_order_a": {"args": ["tests/test_boq_extraction_v2.py", "tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows", "tests/test_document_sync.py", "tests/test_submittal.py"], "env": {}, "rc": 0, "summary": "53 passed, 37 warnings in 84.82s (0:01:24)"}, "mixed_order_b": {"args": ["tests/test_submittal.py", "tests/test_document_sync.py", "tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows", "tests/test_boq_extraction_v2.py"], "env": {}, "rc": 0, "summary": "53 passed, 37 warnings in 86.39s (0:01:26)"}, "memory_harness_alone": {"args": ["tests/test_ai_sheet_reader.py::test_the_first_read_runs_as_a_job_the_page_follows"], "env": {"EP_TEST_DATABASE": "memory"}, "rc": 0, "summary": "1 passed, 2 warnings in 2.53s"}, "memory_harness_regression": {"args": ["tests/test_job_thread_sessions.py"], "env": {"EP_TEST_DATABASE": "memory"}, "rc": 1, "summary": "1 failed, 2 warnings in 3.26s"}, "file_harness_regression_x3": {"args": ["tests/test_job_thread_sessions.py", "tests/test_job_thread_sessions.py", "tests/test_job_thread_sessions.py"], "env": {}, "rc": 0, "summary": "3 passed, 4 warnings in 7.57s"}}. Skips are the live-archive BOQ sheet tests (`EP_PLATFORM_LIVE_ARCHIVE_ROOT` unset).

## Verdict (Review 02)

**READY FOR INDEPENDENT M2 RE-REVIEW.**

Code defects remaining (reader, deterministic path): (1) EML `SL2MNM65D3C-M +SL23I` read `+SL231` and accepted (two-line cell; the cell check reads fragments); (2) `6538-G5` grouped under the heading above it where the fixture leaves it ungrouped; (3) the band row's part number is read as printed and cut (`SIGA-OSHD-FC`) -- the sheet cuts it, the fixture completes it. Missing evidence: the real-model BOQ verification path (no model call permitted); engineer sign-off on Golden labels (none claimed). G-01 stays documented, untouched.


## Operations observed at the end of the Review 02 correction (read-only, 2026-09-28T10:41:33 local)

Not done by this correction, and not asked for: **the backend is running from this checkout** -- an API (`uvicorn app.main:app --reload --port 8000`, listener on 127.0.0.1:8000) and the sync, document and IFC workers, with the launcher's command lines (`evidence/r4__live_check_r4.json`). Their start is outside this session: `backend/library/symbols/symbol_library.json` was exported at 2026-09-28T10:09:44 and again earlier at 09:10:24 (an app start writes it), and `backend/ep_platform.db` (main file) was last written at 2026-09-28T10:22:24 with an active write-ahead log of 4120032 bytes. The live database file therefore no longer matches the committed snapshot (`git status` shows `M backend/ep_platform.db`; sha256 `6a220e62768d3392...` now). What the database holds, read-only: 890 documents, parser versions {'none': 890}, last processing 2026-09-27 14:58:09.579508, newest jobs [(27, 'ai_verify', 'succeeded', '2026-09-27 14:54:15.609921'), (26, 'boq_read', 'succeeded', '2026-09-27 14:54:15.374982'), (25, 'process_documents', 'succeeded', '2026-09-27 14:46:13.596564')], last login [('admin@ep-platform.com', '2026-09-27 19:38:09.317741')] -- **no document processing, job or login has happened since 2026-09-27**; the writes so far are the startup's own (migrations at the same head `a5b6c7d8e9f0`, seeds, worker heartbeats). Implication: the workers run the code they started with and the API reloads on every edit, so both are running **uncommitted, in-progress correction code** (parser `parse-2026-09-28.4`, profile `default`) against the live database. Nothing has been processed, but the next sync or processing job would apply this code live. This correction did not start, stop, or use these processes, and does not do so now; whether to stop them (`stop-backend.bat`) until the re-review is the owner's call (`M2-RECOVERY-CHECKLIST.md`).


---

# Response to Independent Review 03 (R3-01..R3-03)

Correction of 2026-09-28 (local, late morning). Source: commit `ed7d221df24dbdeac3ababed5de3e128fed0c588` plus the Review 01, 02 and 03 corrections, uncommitted (`evidence/r5__m2_review03_changes.diff` is the whole uncommitted backend diff; `evidence/r5__before_manifest_r3.json` the hashes of the dirty tree before this correction). Versions unchanged since Review 02 (`parse-2026-09-28.4`, box-4, sheet reader `2026-09-28.1`): the reader's records did not change, the writer's handling of them did. No live data, backend, worker or model touched; the running backend found at the end of Review 02 was neither used nor stopped. The review files are untouched (probe copies under `C:\t\m2r3\probe` byte-identical).

| Finding | Root cause | Change | Tests / evidence | Remaining limitation | Disposition |
|---|---|---|---|---|---|
| **R3-01** [P1] Repeated bounded reads erased inherited uncertainty | `carry_unvisited` computed the flags from the *previous envelope's* hash and re-created them; the new envelope's hash, parser and profile were written over the carried records; the same helper served the repair tool | Every carried record keeps its own provenance in `retained` (`source_sha256`, `parser_version`, `profile`, `read_at`: the envelope's at first carry, None where that reading recorded none; never restamped afterwards -- `document_sync.retained_provenance`). Its flags follow that provenance against the current content and profile, not the envelope: `carried_unverified` while its source bytes are not the file's now (or unknown), `carried_other_profile` while its profile is not the current one (or unknown). Its decision is projected as the record's status only when both bytes and profile match; otherwise the status is UR and the decision is kept as a candidate (method `retained`), restored when a later carry finds bytes and profile matching again. The envelope carries `retained` (count, pages, unverified, other-profile, sources) beside `coverage.carried_from_previous`; the note says how many are unverified / held. The same helper, with the profile, in `repair_extraction.preview`/`apply_row`; `retained` summarised on apply | `tests/test_extraction_m2_review03.py`: `test_repeated_bounded_reads_keep_the_carried_records_provenance_and_uncertainty` (complete -> changed bytes bounded -> the repair tool twice on the same new bytes -> reload in another session -> bytes changed again -> wider reader: original hash/time kept, both flags kept, then the record read afresh), `test_a_legacy_record_carried_into_a_bounded_reading_has_unknown_provenance_and_no_projected_decision`, `test_carry_unvisited_follows_the_records_own_provenance_not_the_envelope`; the reviewer's probe `repeat_bounded`: first `['carried_unvisited', 'carried_unverified']`, second `['carried_unvisited', 'carried_unverified']`, retained source `old-bytes` (`evidence/r5__probe__boundary_probes_after.json`) | A carried record's identity (reference, revision, page) is still projected, flagged; only its decision is withheld. Page numbers are taken as the record's page; a file whose pages moved keeps the record flagged unverified until the page is read | **Fixed** (D-EXT-14) |
| **R3-02** [P1] Bounded carry bypassed the profile boundary | `carry_unvisited` did not know the profile; the default envelope certified a promoted record | Above: `carried_other_profile` and the withheld decision (mirror UR) for a record of another or unknown profile; `document_processing.parser_current` is False for a reading whose `retained.other_profile` > 0 (a mixed reading is never a current reading, so `_previous_sha` and `read_task`'s unchanged shortcut recompute; `pending_rows` does not select it on its own, so no retry loop); the known-content map never copies a reading with retained records to a duplicate file; the repair tool's `parser-outdated` selection names a mixed reading | `test_a_promoted_record_on_an_unvisited_page_is_held_by_a_default_bounded_reading` (promoted complete -> default bounded on the same bytes: status UR, candidate `retained`, mirror UR, `parser_current` False, `log_records` UR, duplicate not copied, reload; the repair tool selects and re-applies the same projection; gate on again: the decision restored and `parser_current` True; profile stripped: held), `test_a_default_record_is_held_by_a_promoted_bounded_reading_too`; probe `promoted_carried_as_default`: status `UR`, flags `['carried_unvisited', 'carried_other_profile']`, mirror `UR`, `parser_current` False, reuse `None`; the five inherited probes unchanged (`r5__probe__independent_probes_after.json`) | Engineer-confirmed domain values are untouched (the fixture of Review 01 still passes). Historical evidence is kept, never cleared | **Fixed** (D-GATE-3) |
| **R3-03** [P2] The EML part-number misread passed as VALID | `_confirm_catalog` read a two-line cell one line at a time (fragments) and treated fragments as no contrary evidence | A cell taller than a line and a half is read as a block (`--psm 6`, lines joined); readings are compared as part keys (the part's own characters, upper case); a part is **confirmed** only when a pass read the strip's whole value; otherwise the row is a review row: either a pass read another whole part (both passes agreeing, or a same-length near miss by one or two substituted glyphs -- I/1, O/0, Z/2) or no pass read the whole part at all ("no independent pass read the whole part number"). Nothing is substituted; the row keeps its literal value, quantity, cell box (`catalog_cell`), every reading and the reason (`catalog_check`). The matcher accepts a fixture row's `printed_part_number` | `test_design_sheet_extractor.py`: `test_a_multiline_catalog_cell_is_read_as_a_block_and_a_near_miss_holds_it`, `test_fragments_do_not_confirm_a_part_and_a_whole_matching_reading_does` (fragments only, nothing read, conflicting whole readings, a clear matching whole reading beside a clipped fragment, a cut identity read literally), `test_an_unruled_sheet_keeps_wrapped_rows_together` (now judged over lines plus held rows); originals: see the table below (`evidence/r5__boq_run_r3.json`) | A part read below 90 % whose cell the passes cannot read whole is held even when the strip was right (EML SL210DI at 7 %): a review row, not a loss. Real-model verification: still missing evidence | **Fixed** (D-BOQ-6) |

## Deterministic BOQ reader on the originals (Review 02 -> Review 03)

| Sheet | Review 02 reader | Review 03 reader |
|---|---|---|
| FAS (74 golden rows) | 69 lines accepted, part 1.000; 6 review rows | 69 lines accepted, 69 matched, part 1.000 / quantity 1.000 / group 0.986; review rows: 4-CABI6D (an independent pass read another part number (a near miss of the strip's)), SIGA-AAS0 (an independent pass read another part number (a near miss of the strip's)), WSTIA-T (an independent pass read another part number), G1IARN (an independent pass read another part number), TP606 (quantity); outcome NEEDS_INTERPRETATION |
| EML (12 golden rows) | 12 lines accepted incl. `+SL231` for `+SL23I`, 0 review rows, outcome VALID | 10 lines accepted, 10 matched, part/quantity 1.00/1.00; review rows: SL210DI (no independent pass read the whole part number), SL2MNM65D3C-M +SL231 (an independent pass read another part number (a near miss of the strip's)); outcome **NEEDS_INTERPRETATION** -- the sheet is not VALID while that identity is unresolved |

Adjudication of the two disputed labels against the source (crops in the scratchpad, hashed in the evidence manifest; recorded in `M2-GOLDEN-MANIFEST.json` `boq_case.current_reader_run_2026_09_28_review03.adjudications` and in the fixture's notes):
- **SIGA-OSHD-FC**: the sheet prints `SIGA-OSHD-FC` with the next glyph cut by the column rule. The reader's literal value is correct extraction; the identity is incomplete on the source. The fixture's `SIGA-OSHD-FCN` is the transcriber's completion, unsupported by the source: the fixture row now carries `printed_part_number: SIGA-OSHD-FC` and the metrics accept the printed form; nothing is completed by the reader. A reliable geometric clip detector was tried (ink in the columns before the rule) and rejected: uncut rows score higher than the cut one on this scan.
- **6538-G5**: printed as a stand-alone item (its own quantity 4) below the Remote power supply kit's components, under no heading of its own. The reader assigns the heading in force (`Booster Power Supply`); the transcriber left it ungrouped. The sheet prints no rule that settles it (no blank-row or indentation convention is established elsewhere on the sheet): a group-layout judgement for the owner, not an extractor error; left as a disagreement in the metrics.

## Compatibility note: the SAR sample (stamp over tick)

Before Review 02 the reader let an OCR-read stamp override a ticked box implicitly (`test_a_consultants_stamp_overrides_the_ticked_box`; EP-30784 `BBY006-GME-SAR-EL-LI-0001`). Since Review 02 the two are candidates settled together; where they disagree the record is UR with `decision_conflict`. Read on the originals by the current reader (`evidence/r5__sar_sample_reads.json`, parser parse-2026-09-28.4): 351 (default): status UR, flags ['decision_conflict'], candidates [('ANN', 'text'), ('rejected', 'ocr')]; 352 (default): status UR, flags ['decision_conflict'], candidates [('ANN', 'text'), ('rejected', 'ocr')]; 353 (default): status ANN, flags [], candidates [('ANN', 'text'), ('ANN', 'ocr')] (the promoted profile reads the same). The stored live readings (old parser) hold `rejected` (R0) and `ANN` (R1). Consumers affected by the raw change: the samples register built from `records` (`document_sync.log_records`/`combine`) shows UR instead of rejected for the R0 sample once it is re-read; the submittal map (`submittal_reader.check`) reads forms, not these records; shop drawings reconciliation reads drawings, not samples. No domain-resolution policy exists that ranks a consultant's stamp over a ticked box, and none is invented here: the raw extraction reports the conflict; the specific owner decision needed is "on a form where a ticked option and a pasted stamp disagree, which stands" -- until it is taken, such records stay UR with both candidates.

## Clone repair (fresh copy of the read-only clone, default profile, Review 03 writer)

| Project | Repair manifest | Tables changed | Documents with changed records (all sources) | Roles changed | After | Stored records vs the M2 submission's repair |
|---|---|---|---|---|---|---|
| EP-30088 (project 4) | 522 selected, 516 repaired, 6 skipped, 0 failed | `document_dependencies` (174 of 306 rows), `project_documents` (516 of 525 rows); project fields changed: False | 165 of 525; form-reading records 9 -> 5; mirrors changed 160 | 0 | profiles {'default': 516, 'none': 9}; retained {'documents': 0, 'other_profile': 0, 'unverified': 0}; invalid JSON 0 | {'identical': 447, 'changed:status': 39, 'records_removed': 32, 'records_added': 4} |
| EP-30784 (project 1) | 356 selected, 352 repaired, 4 skipped, 0 failed | `document_dependencies` (222 of 384 rows), `project_documents` (352 of 359 rows); project fields changed: False | 24 of 359; form-reading records 2 -> 2; mirrors changed 3 | 0 | profiles {'default': 352, 'none': 7}; retained {'documents': 0, 'other_profile': 0, 'unverified': 0}; invalid JSON 0 | {'records_removed': 3, 'identical': 326, 'records_added': 1, 'changed:status': 26} |

`retained` counts how many documents carry records of an earlier reading of their own file (legacy readings on skipped pages: unknown provenance, decisions held), `other_profile` how many of those are mixed readings (never current: read again on the next content change or repair).

## Tests

**344 tests, 337 passed, 7 skipped, 0 failed, 0 errors** in 422.2 s (`evidence/r5__final_r5.xml`, `.log`; file-backed harness). No failures. Skips: the live-archive BOQ sheet tests. The seven reviewer probes (five inherited, two new) meet their contracts on the final code.

## Verdict (Review 03)

**READY FOR INDEPENDENT M2 RE-REVIEW.**

Code defects remaining: none reproduced by the reviewer's probes or known on the originals beyond the held rows (which are the contract). Owner decisions: (1) stamp versus ticked box on a form (the SAR case); (2) the group of a stand-alone item printed under a heading in force without a heading of its own (6538-G5). Missing evidence: real-model BOQ verification (no model call permitted); engineer countersignature of Golden labels (none claimed); G-01 stays the documented M4 gap.


---

# Response to Independent M2 Review 04 (2026-09-28)

Source identity: reviewed commit `ed7d221` plus the Review 01-03 corrections were committed by the owner as
`2221b4327c7dd140994cc2c98e89229431b34899`; this response's code is that commit plus the uncommitted R4-01
closure and the pilot fixes below (hashes in `real-project-pilot/RUN-MANIFEST.json`, evidence prefixed `r6__`
in `evidence/M2-EVIDENCE-MANIFEST.json`). Earlier evidence (`r3__`, `r4__`, `r5__`) is kept unchanged.

## R4-01 -- disposition: fixed (candidate for re-review)

| requirement (Review 04) | what was done | where |
|---|---|---|
| retained parser compatibility part of authoritative projection and freshness / reuse | `document_sync.carry_unvisited` compares the carried record's `retained.parser_version` with an explicit, narrow compatibility contract (`parser_compatible`: only the current `PARSER_VERSION`); a record from another or an unknown parser is flagged `carried_other_parser` (plus `carried_unverified` when its bytes differ), its decision is withheld as a candidate `[status, "retained from a <profile> reading by <parser> of these|other bytes", "retained"]`, status `UR`; `retained_summary` adds `mixed` and `other_parser` | `document_sync.py` (`CARRIED_OTHER_PARSER`, `parser_compatible`, `carry_unvisited`, `retained_summary`) |
| explicit mixed / outdated state; never masquerading as current; not copied by a current-result shortcut | `document_processing.parser_current` is False when `extracted.retained.other_parser` (or `other_profile`) is set; `_previous_sha` then returns None (no unchanged-hash reuse); the known-content map excludes rows with `retained`, so a duplicate never receives a mixed reading | `document_processing.py` |
| repair selection recognises it | `select_rows("parser-outdated")` names "carries records read by another or an unknown parser"; `apply_row` recomputes `retained` | `scripts/repair_extraction.py` |
| no infinite automatic retry for intentional page limits | unchanged: a bounded reading of unchanged bytes is not re-planned by the sync; the mixed state clears on the next content change, a wider read, or the repair tool (scenario 15 -> 16 on a real document) | `real-project-pilot/COMPATIBILITY-AND-PERSISTENCE.md` section 2 |
| explicit version-compatibility contract; not "every older / missing version compatible" | `parser_compatible(version)` is true only for the current version; `None` (legacy, unknown) is incompatible; `test_parser_compatibility_is_explicit_and_narrow` | `document_sync.py`, `tests/test_extraction_m2_review03.py` |
| persisted normal-processing and repair tests | `test_a_record_read_by_an_older_parser_is_held_by_a_bounded_reading_until_its_page_is_read_again`: same bytes / same profile / older parser with a formerly Approved decision on the skipped page -> held, not current, not reused; missing parser identity -> held; repeated bounded runs + reload keep the uncertainty; duplicate reuse and unchanged-hash checks on the mixed reading; a wider current-parser read restores current / idempotent behaviour; existing source-change and profile-change cases updated for the new flag and still pass | `tests/test_extraction_m2_review03.py` (18 tests), `test_extraction_m2_review02.py` |
| historical evidence and engineer overrides preserved | the carried record keeps its records, candidates, `retained` provenance; nothing deleted; the pilot's clone workflow shows engineer-origin BOQ rows unchanged | probes; `real-project-pilot/outputs/clone_default/` |
| consumer-compatible shapes | `ControlledDocument` gained no field; `flags`, `decision_candidates`, `retained` (existing) carry the state; `extracted.retained` gained `mixed` and `other_parser` keys | -- |
| reviewer probes | all eight rerun on the frozen code: the retained-parser probe yields `parser_current=false`, mirror `UR`, reuse hash `None`, flags `carried_unvisited` + `carried_other_parser`; the seven earlier probes keep their contracts | `real-project-pilot/outputs/probe_r4/`, `evidence/r6__probe__*` |

Found while closing R4-01, fixed: `document_processing` raised `KeyError: 'unchanged'` on a duplicate-content
result (`result["unchanged"]` where the copy path never sets the key); now `result.get("unchanged")`
(`M2-DEFECTS-AND-FIXES.md`, D-PROC-1).

## Real-project pilot (owner-authorised, executed after the R4-01 closure)

Deliverables under `docs/milestones/M2/real-project-pilot/` (`PILOT-PLAN.md`, `PROJECT-INVENTORY.json`,
`FROZEN-SAMPLE.json`, `FROZEN-BOQ-SET.json`, `GOLDEN-LABELS.json`, `RUN-MANIFEST.json`,
`ACCURACY-AND-COVERAGE.md`, `COMPATIBILITY-AND-PERSISTENCE.md`, `DEFECTS.md`, `ACCEPTANCE.md`, `outputs/`,
`crops/`). Verdict there: **CHANGES REQUIRED** -- decision precision 100 % with no false approval, but
reference / revision precision about 65-79 % on the eight new projects' drawing-sheet layouts (revision table
rows, reference-drawing tables), far from the 98 % target; four bounded reader defects fixed with regression
tests (P-01..P-04, parser `parse-2026-09-28.5`); the larger classes left for M3 with evidence. The BOQ reader
is a model-only path and was not exercised (778 rows labelled, none scored).

## Tests

Submitted module set (the reviewer's 28 modules, now with the two R4 tests): **346 tests, 339 passed, 7 skipped, 0 failed, 0 errors** in 299.8 s (`evidence/r6__suite_submitted_r6.xml`, `.log`; file-backed harness, candidate B). `tests/test_extraction_pilot.py`: 5 passed. Full backend suite (`tests/`, 1,442 tests): 1,404 passed, 35 skipped, 3 failed (`evidence/r6__suite_full_r6.xml`): `test_ep_archive_models::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` (FOREIGN KEY constraint on `DROP TABLE users`), `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it`, `test_submittal_one_per_system::test_the_page_counts_submittals_by_their_latest_revision` -- all three fail identically with the candidate A reader (HEAD's `document_control.py` swapped in), are outside the submitted set, and are pre-existing; not investigated in this correction.

## Verdict (Review 04)

R4-01: **READY FOR INDEPENDENT RE-REVIEW** of the closure. M2 acceptance: **CHANGES REQUIRED** by the real-project
pilot (`real-project-pilot/ACCEPTANCE.md`); not self-approved. Owner decisions and missing evidence:
unchanged from Review 03 (SAR stamp versus tick; 6538-G5 layout; real-model BOQ verification; countersigned
labels; G-01 in M4), plus the pilot's P-obs-3 / P-obs-4 policies and a model-enabled BOQ run over the 15
labelled sheets. M3 not begun; no live backfill.

# Response to Independent M2 Review 05 (2026-09-28)

Report with every figure, table and link: `real-project-pilot/review05/REVIEW-05-REPORT.md`. Candidate C = parser
`parse-2026-09-28.6`, title-block reader `titleblock-1` (`app/services/title_block.py`), design-sheet extractor
`2026-09-28.2`; frozen in `real-project-pilot/review05/CANDIDATE-C-FREEZE.json`. Nothing committed; no live data,
production endpoint, service, model enablement or M3/M4 change; the live database and `symbol_library.json` are not in
the diff (`evidence/r7__live_check.json`). M2 not self-approved; M3 not begun.

| finding | what was wrong | what changed | evidence | disposition |
|---|---|---|---|---|
| **R5-01** [P1] raw extraction on real layouts | own number / revision taken from reference tables, callouts, revision-history rows and dates (P-06/P-07), reply and transmittal identity (P-08/P-09), wrapped joins (P-10), P-11, raw floor (P-05) | title block read by position (own number cell, REV cell on its row; tables, history, callouts, split runs, second numbering schemes excluded; a self-contradicting sheet flagged `revision_conflict`; letters kept as printed, never mapped); reference roles (cross-reference, citation, subject line, form template); reply header; transmittal items never the identity and an unread TR kept unread; no join onto field labels, split start held; form editions / table headers not revisions; a lost cover line re-read once in its header band; MTG tag code; raw floor as printed; P-11 reclassified as a label error (the cover prints EM-30) | `tests/test_m2_review05.py` (22, source-derived, incl. the two checked originals by sha256); corpus: critical 30 → 0 (B → C, per profile) | **Corrected** on the exposed corpus; **not demonstrated on unseen layouts** (holdout H-01..H-05) |
| **R5-02** [P1] scorer let negatives, conflicts and extra records pass | n/a / absent truths unscorable; unknown lumped with absence; one record per document; held evidence as approval; system by substring | evaluator `scripts/m2_pilot_eval.py` (.3): negatives can fail, unknown unscorable, separate denominators, record-set matching per page, every record scored, unvalidated pages reported, conflict needs evidence, held ≠ accepted, equivalence table, raw vs register vs projection | `tests/test_m2_pilot_eval.py` (10 adversarial); A/B re-scored (report section 2) | **Corrected** |
| **R5-03** [P1] truth and reporting | labels from file names, missing pages, units mixed, "30/32 meets 98 %" | truth v2 versioned with evidence (7 document fields, 3 BOQ rows; v1 kept); 25 documents page-labelled (78 records, 54 no-record, 24 unvalidated pages); common corpus verified (387 rows, 0 hash differences in six runs); units table; the 98 % claim corrected (93.8 %); 708 equipment rows counted apart from 65 headings | `review05/labels/`, `common_corpus.json`, `../real-project-pilot/ACCEPTANCE.md` | **Corrected** |
| **R5-04** [P1] BOQ | model-disabled BOQ unscored; KCW019ML-IP65 accepted as KCWO019ML-IP65 on correlated OCR; ensure / re-read completion contract | deterministic track scored (`scripts/m2_boq_eval.py`): critical 55 → 5; correlated agreement held; item-number / crossed columns held; ensure not stamped without an attempt, all-failed re-read fails, unread sheets' lines never offered as removals; three reports kept apart; real model not exercised | `tests/test_m2_review05_boq.py` (11), `review05/boq/`, integration run on the 15 sheets | **Partly corrected**: 5 confident misreads open; holdout BOQ 4 critical; real-model **BLOCKED BY MISSING EVIDENCE** |
| **D** revalidation | exposed holdout; no fresh evaluation | frozen C; 4 unseen projects (seeded, 4 contractors, no pilot hash), plan and labels hashed before the run, both profiles in a separate sandbox | `review05/holdout/` | **Failed**: 0 records emitted, 0 critical; recovery 0/9 references (H-01..H-06) |

Full-suite failures (D5): the page-counts test is fixed (it read uncommitted rows through the API's connection; it
passed only on the old shared-connection harness); the migration downgrade (`c0e4a9b6d321` rebuilds `users` under
enforced foreign keys) and the part-catalogue test (stale since c49f406 moved the catalogue to `PartDatasheetLink`) fail
since before M1, are outside M2 and are documented with root cause and impact (report section 5), not changed.

## Tests (Review 05)

- Reviewer module set (28 modules, the command in the review package): **339 passed, 7 skipped, 0 failed**
  (`evidence/r7__suite_submitted.xml`).
- `tests/test_extraction_pilot.py` + new regressions (`test_m2_review05.py`, `test_m2_review05_boq.py`,
  `test_m2_pilot_eval.py`, `test_submittal_one_per_system.py`): **55 passed** (`evidence/r7__suite_new.xml`).
- Full backend suite: **1,485 tests: 1,448 passed, 35 skipped, 2 failed** in 1,631 s -- the two pre-M1 failures diagnosed above (`test_ep_archive_models::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index`, `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it`); the page-counts test now passes (`evidence/r7__suite_full.xml`).

## Verdict (Review 05)

**CHANGES STILL REQUIRED.** Open, all M2: H-01..H-06 from the unseen holdout, B-04 (confident BOQ misreads), unread
decision marks, recovery below 90 % on every critical field, and the real-model BOQ track (missing evidence). The
holdout is exposed now; a further candidate needs a fresh one. Owner decisions pending as before (label countersignature,
P-obs-3 / P-obs-4 policies, SAR stamp versus tick, whether to stop the live backend running from this checkout).

# Response to Independent M2 Review 06 (2026-09-29)

The full package is `real-project-pilot/review06/` (index: `REVIEW-06-REPORT.md`).

**Where the candidate lives.**
- The candidate is an isolated copy (`C:/t/iso/ep-platform/backend`).
- Its baseline commit `c692f1e` = Candidate C, carried explicitly.
- The owner's tree, the live services, the live `.env`, the live database and the symbol library are untouched.
- The owner's tree was not stashed, reset, committed or pushed.

## Dispositions

| Finding | Disposition | How |
|---|---|---|
| R6-01 to R6-04 | Closed | Evaluator `.4` (`scripts/m2_eval4.py`, 14 adversarial tests, each failing on `.3`). The reviewer's six probes now give the expected outcomes. Every stored output was re-scored; Candidate C goes 0 → 2 critical per profile. |
| R6-05 | Open, blocker | — |
| H-01 | Partly closed | OCR title block; 03-D has no revision. |
| H-02, H-04, H-05 | Closed as raw evidence | — |
| H-03 | Open for decisions | Not readable deterministically; the model could not be used, as no AI policy is recorded for the project. |
| H-06 | Partly closed | The "2 read as 9" row is held; the three "1 read as 4" rows remain. |

## Candidate

**Deterministic.** `parse-2026-09-29.8`, `titleblock-3`, sheet extractor `2026-09-29.1`. Results against Candidate C (all exposed data):

| Set | Result |
|---|---|
| Pilot | Critical unchanged at 2. Raw identity 223 → 244, raw revision 185 → 195, register revision 104/108 → 107/111. |
| Holdout | Register reference 0 → 3/5; raw identity 3 → 14/20; raw revision 0 → 7/13; 0 critical. |
| BOQ | Deterministic critical: pilot 5 → 4, holdout 4 → 3. |

**AI evidence stage.** `app/ai/evidence_reader.py`, off by default:
- triggers on missing evidence as well as flags, plus a frozen 20% audit;
- page discovery, then blind crop reads with no proposed value;
- a versioned validation policy decides acceptance;
- it writes only `extracted["ai_evidence"]`.

Tests: 21 mocked contract tests.

## Real model (declared budgets; 690 of the declared 700 requests)

Only three projects had a recorded AI policy. Cost is unknown.

- **AI-EV0 (AS-IS)** introduced one critical false acceptance: a transmittal acknowledgment was keyed under an item it lists.
- **AI-EV1 and AI-EV2** changed no record and introduced no error. Their gains were small. EV2 cost more and did not recover more than EV1.
- **The application's model BOQ path** clearly out-recovers the deterministic reader. Its remaining critical error is one lost "+".
- **The blind BOQ verifier `.2`** read parts 50/50, catching PT-1S+. Its quantity check is limited by the component-count layout.
- Two verifier `.1` defects and three runner bugs were found and fixed. All attempts are kept.

## Tests (Review 06)

| Suite | Result |
|---|---|
| Reviewer set | 339 passed, 7 skipped, 0 failed |
| New and changed modules | 84 passed; evidence reader now 21; review06 title-block and BOQ tests 11 |
| Full suite | See `review06/REGRESSION.md`. Two pre-existing failures, plus one isolation artefact (the sandbox `.env` pins `DATABASE_URL`). |

One Review 02 BOQ assertion was changed deliberately, as a contract change for the reviewer to confirm.

## Verdict (Review 06)

**CHANGES STILL REQUIRED.** The blockers are listed in `REVIEW-06-REPORT.md`:
- B-1: recovery below 90%.
- B-2: remaining critical false accepts. These include D-R6-A (flagged references used as register keys) and the AS-IS submittal reader's association error.
- B-3: real-model evidence limited by unrecorded project AI policies.
- B-4: Round 2 needs independent human labels and a second review. The selection is frozen; nothing new has been read.
- B-5: cost unknown, and the token cap is not enforced on actual usage.
- B-6: the BOQ contract change needs confirmation.

M2 is not accepted and M3 is not started.

# Response to Independent M2 Review 07 (2026-09-29)

The full package is `real-project-pilot/review07/` (index: `REVIEW-07-REPORT.md`).

**Boundaries.**
- The work was done in the isolated scratch repository (`C:/t/iso/ep-platform`).
- The frozen candidate is commit `c9a1a14`; the evaluator amendment is `1455f8b`. The recovered Review 06 final state is `043dee9`, hash-verified.
- The owner's tree, the live services, `.env`, the database (read only twice), the symbol library, the OneDrive originals and the sealed Round 2 cohort are untouched.

## Dispositions

| Finding | Disposition | How |
|---|---|---|
| R7-01 | Closed | Evaluator `.6`: every emitted fact scored; the reviewer's probes fail `.4` and pass `.6`; all stored outputs re-scored; changed findings adjudicated against the source. The Review 06 "zero introduced AI errors" is **withdrawn**: 2 are reported, both disputed truth pending human review. |
| R7-02 | Closed | Policy `.2`: region-bound literal support, near match only a candidate, decision corroboration / legend / actor / target, escalation over all readings, own and referenced identities apart, numeric semantics. Each probe is validated by the pinned `.1` reader and refused by `.2`. |
| R7-03 | Closed | Last-good evidence per page beside additive attempts; stale envelopes are not current; the profile is bound end to end. |
| R7-04 | Closed within stated limits | A shared persistent ledger (hard request caps; estimate plus breaker for CLI tokens), tested with scripted providers and held exactly at 120/120 on the matched run. |
| R7-05 | Provenance corrected and frozen | Hermetic full suite on the frozen code: 1,563 passed, 35 skipped, 2 pre-existing failures. A small matched run was made; no variant is adopted. |
| E | Closed | Uncertain references are pending evidence (register critical 2 → 0 in both profiles; dry run: no business-row change); a transmittal's listed submittal is no longer its identity on all three business paths; description counts are located facts. |
| G | Prepared | The human-review packet (339 component items, 194 BOQ items), not reviewed. |

## Verdict (Review 07)

**CHANGES STILL REQUIRED.** The blockers:
- B-1: recovery below 90%.
- B-2: identity precision below 98%.
- B-3: truth unresolved, pending the owner's reviewer.
- B-4: project-model eligibility, an owner decision.
- B-5: no supported variant choice.
- B-6: H-06 BOQ misreads.

M2 is not accepted and M3 is not started.

# Response to Independent M2 Review 08 (2026-09-29)

The package is [real-project-pilot/review08/](real-project-pilot/review08/REVIEW-08-REPORT.md). The candidate is `e02a8c1` in the isolated scratch repository (parent `1455f8b`), frozen at `C:/t/iso/frozen-r8` with no `.env`.
- No model was called; every AI answer in the tests is scripted.
- The owner's code, services, settings, data, originals and sealed projects were not touched.
- The Review 07 freeze and the evaluator amendment are kept as history.

## Dispositions

| Finding | Disposition |
|---|---|
| **R8-01, field-level lifecycle** | **Fixed.** Every required read records its own outcome: completed, absent by discovery, incomplete, failed, budget or not attempted. The merge works field by field, and only a completed read replaces a field. A completed, source-supported negative supersedes; failures, budget refusals, absence by discovery and unreadable results never do. Last-good evidence keeps its provenance, and failed attempts are appended. Tested through `evidence_stage` on persisted rows, reloaded after every step. |
| **R8-02, context-bound selection** | **Fixed.** `evidence_for(sha256, profile, variant, policies)` answers current, pending, unavailable or stale, and never substitutes another context's evidence. History is available only through `last_known`. An unknown legacy profile needs the caller's declaration. Evaluator `.7` scores AI evidence only for the declared context and reproduces every stored `.6` result. |
| **R8-03, authoritative ledger scope** | **Fixed.** Persisted limits are authoritative: different limits, looser or stricter, are refused (`LedgerConfigMismatch`). Reserve and settle read the limits from the database. A change needs an authorised, versioned, audited amendment. A first-open locking race was found and fixed. The Review 07 matched run is not claimed to have overspent. |
| **R8-04, BOQ heading** | **Fixed.** A heading is `not_an_item` only without any item data. With item data it is a held conflict (`disputed`); if illegible it is `unverified`. No BOQ line is removed. |
| **Human-review handoff** | **Prepared, not reviewed.** Packet v2 keeps the same scope, records one row per identity with its printed label and role, and narrows "ambiguous". The findings index covers the 13 findings: 8 to decide, 5 to confirm. No reviewer name is filled in. |

## Tests (Review 08)

All new, on `e02a8c1`:
- **Review 08 module:** 27/27 pass. The same module fails 24/27 on `1455f8b`, each on a behavioural assertion.
- **The reviewer's six-module set:** 88 passed.
- **BOQ, extraction and AI compatibility modules:** 157 passed, 7 skipped.
- **Hermetic full suite:** 1,628 tests, 1,591 passed, 35 skipped, 2 failed. Both failures are pre-existing and the same as in Review 07.

## Verdict (Review 08)

**READY FOR INDEPENDENT CORRECTION REVIEW.**

M2 remains **CHANGES STILL REQUIRED**:
- B-1: recovery below 90%.
- B-2: identity precision below 98%.
- B-3: human truth pending; the reviewer appointment rests with the owner.
- B-4: project-model eligibility, an owner decision.
- B-5: no supported variant choice.
- B-6: the H-06 BOQ misreads.

Correction acceptance does not imply M2 acceptance. No M3 or production promotion is authorized.

# Response to Independent M2 Review 09 (2026-09-29)

The package is [real-project-pilot/review09/](real-project-pilot/review09/REVIEW-09-REPORT.md). The candidate is `689d95e` in the isolated scratch repository (parent chain `ec4f0fc` → `e02a8c1`), frozen at `C:/t/iso/frozen-r9` with no `.env`.
- No model was called, and no source document was opened.
- The owner's application, services, database, settings, symbol library, originals and sealed cohort were not touched.
- Review 08 is kept as history.

## Dispositions

| Finding | Disposition |
|---|---|
| **R9-01, usable reads** | **Fixed.** The request outcome and field usability are recorded separately. An illegible or empty blind answer is `unusable:*` and supersedes nothing; discovery-only candidates and negatives are kept with the attempt (`unapplied`). A completed, legible negative still supersedes, and a completed conflict stays explicit. Tested through the persisted stage. |
| **R9-02, association** | **Fixed.** Decisions record `target` and `target_revision`; revisions record `target`. Selection labels each dependent fact `current`, `held:target_changed`, `held:revision_changed`, `by_target` or `not_recorded`. Evaluator `.8` judges held and by-target facts only under their own target and keeps them visible. Same-identity retries are unchanged, and legacy facts get no invented target. The re-score of every stored run is identical to `.7`: the stored runs never exercised the defect. |
| **R9-03, source identity** | **Fixed.** Source identity is decided per field (`current`, `stale`, `unknown_source`, `source_required`, plus `withheld`). An unknown profile implies nothing about bytes, and retained fields are never relabelled. Historical compatibility is a separate, manifest-backed mode, and no stored run needed it. |
| **R9-04, heading item presence** | **Fixed.** The normal verifier passes the reader's description. A part, a present quantity (`0` and `"0"` included) or a `( n )` count on either side against a heading answer is a held conflict. An illegible answer stays unverified. Lines and literals are kept. |
| **R8-03 ledger (accepted)** | Wording corrected: an already-open handle reads the saved, amended policy, and a newly opened handle supplying the old limits is refused. The behaviour is unchanged, and no claim is made that the 120-request run overspent. |

## Tests (Review 09)

All new, on `689d95e`:
- **Review 09 module:** 34/34. On `e02a8c1` it fails 22/34: 20 on behaviour, 1 on dropped metadata, 1 on the ledger wording.
- **The reviewer's seven-module set:** 115 passed.
- **Compatibility modules:** 157 passed, 7 skipped.
- **Hermetic full suite:** 1,662 tests, 1,625 passed, 35 skipped, 2 failed. Both failures are the same pre-existing ones as in Review 08.
- **The reviewer's probes:** they reproduce exactly on `e02a8c1`, and every defect case flips on the candidate.

## Verdict (Review 09)

- **Correction readiness:** READY FOR INDEPENDENT CORRECTION REVIEW.
- **Accuracy:** unresolved (B-1 recovery below 90%, B-2 identity precision below 98%, B-5 no supported variant choice, B-6 H-06 BOQ misreads). No figure changes.
- **Human truth:** pending. Packet v2 is prepared, no reviewer is named, and the appointment rests with the owner (B-3).
- **Project permission:** pending as recorded (29076, 30088, 30784 only; B-4). No owner answer has been received.

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2, starts M3 or authorizes production promotion.

# Response to Independent M2 Review 10 (2026-09-29)

The package is [real-project-pilot/review10/](real-project-pilot/review10/REVIEW-10-REPORT.md). The candidate is `a34d3f8` in the isolated scratch repository (parent `689d95e`), frozen at `C:/t/iso/frozen-r10` with no `.env`.
- **Scope:** only association logic changed: reader `.5` (selection) and evaluator `.9`. R9-01, R9-03, R9-04 and the ledger wording, all accepted, are unchanged.
- **Boundaries:** no model call, no corpus expansion, no migration, backfill or AI adjudication. No owner code, services, data, settings, libraries, originals or sealed projects were touched.

## Dispositions

| Finding | Disposition |
|---|---|
| **R10-01A: a targetless legacy fact inherited a later identity** | **Fixed.** A targetless fact's context is the identity in effect at its own attempt, taken from recorded provenance and history. When the context changed or was unknown, the fact is held and unassociated: never reassigned, never given an invented target, still visible. An unchanged context (single attempt or same-literal retry) keeps the supported original grouping. |
| **R10-01B: a missing identity bypassed a known revision constraint** | **Fixed.** All known constraints are checked before any `current` or `by_target` association. Revisions are compared only when they are compatible with the same target, and a candidate or conflicting identity never establishes `current`. |

## Tests (Review 10)

New, on `a34d3f8`:
- **Review 10 module:** 12/12. On `689d95e` it fails 7/12, all on behaviour; 5 controls pass.
- **The reviewer's eight-module set:** 149 passed.
- **Affected modules:** 116 passed, 7 skipped.
- **Hermetic full suite:** 1,674 tests, 1,637 passed, 35 skipped, 2 failed, both pre-existing.
- **Probes:** the reviewer's probes reproduce exactly on `689d95e`, and both R10-01 cases are held on `a34d3f8`.

**Re-score under evaluator `.9`:** totals are identical in all 33 stored runs. 5 matched-run documents change only their association route (a candidate identity anchor), and every outcome is unchanged. Prior scores are kept as history.

## Verdict (Review 10)

- **Correction readiness:** READY FOR INDEPENDENT CORRECTION REVIEW.
- **Accuracy:** unresolved (B-1, B-2, B-5, B-6); no figure changes.
- **Human truth:** pending. Packet v2 is unchanged, no reviewer is named, and the appointment rests with the owner (B-3).
- **Project permission:** pending as recorded (29076, 30088, 30784; B-4).

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2 or starts M3.

# Response to Independent M2 Review 11 (2026-09-29)

The package is [real-project-pilot/review11/](real-project-pilot/review11/REVIEW-11-REPORT.md). The candidate is `a977364` in the isolated scratch repository (parent `a34d3f8`), frozen at `C:/t/iso/frozen-r11` with no `.env`.
- **Scope:** reader `.6` only: evidence provenance, ordering and association. Evaluator `.9`, the policy, the ledger and business logic are unchanged.
- **Boundaries:** no model call, no migration or backfill of live rows, no AI adjudication. No owner code, services, data, settings, libraries, originals or sealed projects were touched.

## Dispositions

| Finding | Disposition |
|---|---|
| **R11-01A: a held decision accepted after its old revision left history** | **Fixed.** Each retained dependent fact keeps its own durable association context (`anchor`), stamped before anything is pruned. The reviewer's pruning sequence stays `held:revision_changed` on every read; only a genuine re-read of the decision resolves it. |
| **R11-01B: repeated attempt numbers made newer evidence look contemporaneous** | **Fixed.** Attempts are ordered by a persistent per-row sequence (`attempt_seq`), which the stage uses to number attempts. It is unique and increasing for writes serialized by the existing job contract (one documents job at a time, one row at a time); overlapping writers are not guaranteed and not tested. The collision sequence stays `held:context_changed`. Rows already stored with repeated or missing numbers are held, and no chronology is invented for them. |

## Tests (Review 11)

New, on `a977364`; all synthetic or scripted:
- **Review 11 module:** 9/9. On `a34d3f8` it fails 5/9, all on behaviour.
- **The reviewer's nine-module set:** 161 passed.
- **Persistence and compatibility modules:** 127 passed, 7 skipped.
- **Hermetic full suite, run once:** 1,683 tests, 1,645 passed, 3 failed, 35 skipped, 0 errors.
  - Two failures are pre-existing, with the same identity and message as the Review 10 run.
  - The third, new in this run: `test_sync_worker.py::test_two_worker_processes_cannot_both_claim`, `TimeoutExpired`, in a run 2.3× slower than usual. The changed code is not on its path, and it passes 3/3 in isolation on both candidates. It is dispositioned as environmental and stays recorded; no second full run was made.
- **Re-score:** all 33 stored runs are identical to Review 10.

## Verdict (Review 11)

- **Correction readiness:** READY FOR INDEPENDENT CORRECTION REVIEW, with the limitation above.
- **Accuracy:** unresolved (B-1, B-2, B-5, B-6).
- **Human truth:** pending (B-3). Packet v2 is unchanged, and no reviewer is named.
- **Project permission:** unchanged (B-4): 29076, 30088 and 30784 only.

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2 or starts M3.

# Response to Independent M2 Review 12 (2026-09-29)

The package is [real-project-pilot/review12/](real-project-pilot/review12/REVIEW-12-REPORT.md). The candidate is `3d5607d` in the isolated scratch repository (parent `a977364`), frozen at `C:/t/iso/frozen-r12` with no `.env`.
- **Scope:** reader `.7` changes legacy anchor reconstruction only. Evaluator `.9`, the policy, the ledger and business logic are unchanged.
- **Boundaries:** no model call and no backfill. No owner code, services, live data, `.env`, library, originals or sealed projects were touched.

## Dispositions

| Finding | Disposition |
|---|---|
| **R12-01A: a repeated revision literal selected another historical entry** | **Fixed.** Reconstruction carries the exact historical entry, selected by reliable order and never by printed value. Found, established absence, incompatible and unavailable are kept distinct. The reviewer's case holds ANN (`held:revision_changed`), and the different-literal control now gives the identical outcome. |
| **R12-01B: a context entry without order became attempt zero** | **Fixed.** Every context entry needs a reliable order (`seq`, a unique numbered attempt, or the explicit flat `legacy` format). Missing or ambiguous order holds the association with its reason. |
| **Anchors `a977364` saved (synthetic data only)** | Re-derived from recorded history, with the original kept as `replaced_anchor`, or held until a genuine re-read. Read-time anchors are never rewritten. |

## Tests (Review 12)

New, on `3d5607d`; all synthetic or scripted:
- **Planned full suite, run once:** pytest exit code **1** (captured); 1,694 tests, 1,657 passed, 2 failed, 35 skipped, 0 errors.
  - Both failures are pre-existing, with the same identity and message as Reviews 10 and 11.
  - The Review 11 sync-worker timeout test passed (4.8 s). That run's failure stays in history: not reproduced in focused checks, cause unconfirmed.
- **The reviewer's 188-test set:** 188 passed.
- **Review 12 module:** 11/11. On `a977364` it fails 6/11, all on behaviour.
- **Compatibility modules:** 127 passed, 7 skipped.
- **Re-score:** all 33 stored runs are identical to Review 11.

## Verdict (Review 12)

- **Correction readiness:** READY FOR INDEPENDENT CORRECTION REVIEW (a submission status only).
- **Accuracy:** unresolved (B-1, B-2, B-5, B-6).
- **Human truth:** unconfirmed (B-3). No reviewer is named.
- **Bounded evaluation permission:** granted by the owner for the frozen 34-project Round 2 sample (`OWNER-AI-PERMISSION-ROUND2.md`). This supersedes the earlier "three projects only" statement for that scope. The ten sealed holdouts stay sealed, and no run happened in this correction.

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2, starts M3 or authorizes production.

# Response to Independent M2 Review 13: Round 2 exploration and human-truth preparation (2026-09-29)

Package: `real-project-pilot/review13/` (index: `ROUND2-EXPLORATION-REPORT.md`). Review 13 accepted the Review 12 correction on `3d5607d`. This round builds on that candidate and **does not change it.**

## What was done

- **Exploration selection and staging** (exploration projects only):
  - **415 distinct documents against 450.** The 35-document shortfall is reported, not filled.
  - 42 duplicates were recorded; 0 were unreadable.
  - A long-path counting defect in the frozen selection's file counts is documented. Membership is unaffected.
  - **No sealed content was opened.**
- **Proposal labels:**
  - The 12-document small batch was labelled before any prediction.
  - These labels are **AI proposals**, not human truth.
  - The remaining 403 documents and the BOQ candidates are not labelled yet.
- **Human-review worklist:**
  - Packet v2 is linked unchanged.
  - Crops were made for all 13 source findings (8 DECIDE, 5 CONFIRM), H-06, the unresolved labels and every critical accept, plus a seeded 20 % independent sample.
  - **No reviewer is named, and no answer is filled in.**
- **Real-model A/B/C on the small batch and H-06:**
  - The declaration was frozen first. The application limits were unchanged, and the per-project daily limit was applied across tracks.
  - A Round 2 ledger scope was used; the exhausted `r7-matched` scope was untouched.
  - **113 requests**, reconciled with the application's usage table. **Cost unknown.**
- **Regression:** no candidate change. The reviewer's 188-test set plus Review 12's module: **199 passed, exit code 0.**

## Results (provisional truth only; not accuracy evidence)

| Profile | Result |
|---|---|
| A | 0 requests: the application AI path reads only submittal forms |
| B and C | Each **held** 3 correct identities the deterministic track missed, but accepted none of them, so recovery stays 4/8 (identity) and 1/5 (revision). **Critical accepts: B 3, C 2.** B's `Rev.0` accepted as an identity is genuine; C's letterhead code accepted as an identity is genuine if the proposed label is confirmed. |
| H-06 | **EV2 caught all three wrong accepted quantities** and validated no wrong row. EV1 caught only what its audit sampled. |

**No variant is selected.**

## Verdict

- **Exploration preparation:** delivered for independent review.
- **Accuracy:** unresolved (B-1, B-2, B-5, B-6).
- **Human truth:** unconfirmed; a reviewer appointment is pending.
- **Sealed validation:** not ready.

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2, starts M3 or authorizes production.

# Response to Independent M2 Review 14: the Round 2 evaluation corrections (2026-09-30)

Package: `real-project-pilot/review14/` (index: `CORRECTION-REPORT.md`). This is a bounded correction task. There were no model requests. The accepted application `3d5607d` is unchanged.

## Dispositions

| Finding | Disposition |
|---|---|
| **R14-01: per-document budget reset per chunk** | **Fixed in the harness.** There is now one budget per (scope, profile, document) across chunks, retries and resumes. The consumed allowance is persisted and no stop is cleared. Reproduced offline: the submitted loop sends 25 (EV1) and 38 (EV2) requests; the corrected loop sends 12. The stored runs (25 and 35 against 12) are preserved and marked as obtained under the deviation. The 60/day and 150 caps were not exceeded. |
| **R14-02: lossy comparison and a first-candidate join** | **Fixed.** A typed part / quantity contract, and a one-to-one, order-preserving join with ambiguity held. The four defect pairs, the repeated-part case and the same-prefix case are shown on the old code. The replay of all stored BOQ outputs against both label versions changes **0 rows**. Under the declared 12 requests, EV2 would have reached only 2 of the 3 H-06 rows. |
| **R14-03: the source-image review** | **Label version `r14.1`** (originals preserved). All 43 units are **bound**: 48 of 53 image uses regenerate byte-identically from the hash-verified source, and 5 packet pages match by appearance. One transcription was checked against the text layer and not applied. Re-scored with the original and the amended labels: matched EV1/EV2 criticals go from 2 and 1 to 0 (F09 becomes a register-off source literal, with its association held). The small-batch criticals are **retyped, not removed** (their recorded targets are null). |
| **R14-04: worklist links and sample provenance** | **Fixed.** 43 items and 137 links, all checked. The AI review sits in separate blocks and the human fields are empty. The sample disclosure is kept, and the next batch freezes its sample before predictions. |
| **R14-05: the shortfall** | **Explanation corrected.** Proposal only: 35 verified distinct, eligible within-cohort candidates, which would give 450. The frozen selection is unchanged. BOQ triage: 29 row tables, 7 matrices, 3 not BOQ. A labelling plan and a per-project workload are included; no run is scheduled. |

## Tests

- **Offline tests on the frozen harness:** 22 passed, exit code 0. These cover budget continuity, the typed comparison, the join and the overlay, with a scripted provider only.
- **Package check after the final edit:** ok.
- The full application suite was not re-run: no application code changed.

## Verdict

- **Correction readiness:** submitted for independent review.
- **Accuracy:** unresolved (B-1, B-2, B-5, B-6); no variant is selected.
- **Review provenance:** an owner-delegated AI review of 43 units. It is not a human signature and not blind; holds remain.
- **Budgets:** the stored BOQ runs are marked; no continuation is scheduled.
- **Sealed validation:** not ready.

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2, starts M3 or authorizes production.

# Response to Independent M2 Review 15: interrupted budgets, sparse row matching and overlay authority (2026-09-30)

Package: `real-project-pilot/review15/` (index: `CORRECTION-REPORT.md`). This is an offline correction: no model requests, and no change to the accepted application `3d5607d` (its source hashes are recorded).

| Finding | Disposition |
|---|---|
| **R15-01: an interrupted allowance reset** | **Fixed** (harness r15.1). The durable count is committed at reservation, before a request can leave the process; uncertain reservations are spent. One writer per key (an OS lock). Attempts are labelled (`interrupted`). The first-start elapsed basis and escalations are durable. The reviewer's probe goes from 17 to **12** requests (5 persisted before the kill, 7 on resume). Tests cover a real child killed inside a chunk, resume, failure after sending, the cap, a second writer, a killed lock holder, elapsed time and escalations. |
| **R15-02: a wrong quantity selected its truth row** | **Fixed** (contract r15.1). Alignment never uses a scored value: verified geometry first, then order and description; ties are held with all candidates. The reviewer's case is now `held [6, 37]`, identical for any emitted quantity or part; with verified geometry it is row 6 and row 37 is missed. The missing-first/second, extra, shuffled, neighbour, complete-row and same-prefix cases are all tested. **Saved-output replay: 0 row deltas** under both label versions, with and without geometry. |
| **R15-03: the overlay could clear an acceptance error** | **Fixed** (overlay r15.1). It annotates only, and the evaluator's criticals are kept exactly. It is bound to the exact run context and content hash, with no fallback to other envelopes. A revision is normalized by prefix only (`1.0` ≠ `10`). States are explicit enums (label version r15.1 adds them; r14.1 is unchanged). The proposal, envelope-order and punctuation probes now keep their criticals. The stored small batch stays B 3 / C 2, with every fact found in its own context. The r14 test that endorsed removing a critical error is replaced. |
| **F11/C0226** | The reviewer's correction is acknowledged additively: `R1029-07-W&A-DWG-TYP-GRO-INT-9011-01` is retained, and the prior files are unedited. |

**Tests.** Focused tests on the frozen r15.1: **51 passed, exit code 0** (JUnit captured). They include the defect reproductions on the submitted r14.1 code. The reviewer's probes were run unchanged against both versions. Package check: ok.

**Verdict.**
- **Correction readiness:** submitted for independent correction review.
- **Accuracy:** unresolved (B-1, B-2, B-5, B-6); no variant is selected.
- **Sealed validation:** not ready.
- **Next task:** the owner's targeted AI accuracy experiment, after this gate; it was not launched here.

M2 remains **CHANGES STILL REQUIRED**. Nothing here approves M2, starts M3 or authorizes production.

# Response to Independent M2 Review 16: BOQ row boundaries and held outcomes (2026-09-30)

Package: `real-project-pilot/review16/` (index: `CORRECTION-REPORT.md`). This is an offline correction of the evaluation harness only. There were no model requests. The accepted application `3d5607d` is unchanged (source hashes recorded; tree clean). The R15-01 allowance and R15-03 overlay modules are byte-identical to r15.1.

| Finding | Disposition |
|---|---|
| **R16-01: fallback alignment crossed a verified source row** | **Fixed** (contract r16.1). Every verified truth row bounds the page's fallback matches, whether or not it was emitted. Unpositioned rows are placed in the interval between the verified rows that enclose them, and matching uses order and description inside one interval only. Contradictory verified positions hold the whole page. Part number and quantity never choose a truth row. The reviewer's test gives 2 failures + 3 controls on r15.1 and **5/5 on r16.1**. The global no-crossing property is asserted on the reviewer's cases, a mixed page, shuffled inputs and 300 seeded random pages. |
| **R16-02: geometry holds were reported as extra rows** | **Fixed** (the `replay_core` reporting path, used by the replay script). Held rows keep their candidates and reason in the row outcome and the summary, with no match or value credit. `extra_row` is used only for rows the join lists as unmatched. Emitted and truth accounting is complete. The integration test through `replay_sheet` holds the y=95/105 rows against verified row 6 (candidates `[6]`), with genuine extra, missed and geometry-matched rows as controls. On r15.1 the same inputs gave `extra_row`. |

**Validation on the frozen r16.1.**
- **Focused tests:** 66 run (51 existing + 15 new); 66 passed, 0 failed, 0 errors, 0 skipped. Pytest exit code 0 (JUnit captured).
- **Recorded invocation error:** the first run of the reviewer's test used a copy whose filename pytest could not import (exit 2, no tests ran). It is kept separately.
- **Review 15 probes:** allowance 5 + 7 = 12; the duplicate is still held; all 5 overlay cases keep their error.
- **Saved BOQ replay:** 0 row deltas against both the r14 and r15 replays in all 8 runs.
- **Stored overlay:** B 3 / C 2.
- **Package check after the final edit:** ok.

**Status:** READY FOR INDEPENDENT CORRECTION REVIEW (not self-approved).
- Extraction accuracy is unresolved (B-1, B-2, B-5, B-6).
- The AI-review holds remain, and the evaluation permission is unchanged.
- Sealed validation is not ready.
- The targeted AI accuracy experiment follows independent review; it was not started.

M2 remains **CHANGES STILL REQUIRED**.

# Response to the Review 17 task: targeted AI accuracy pilot (2026-09-30)

Package: `real-project-pilot/ai-accuracy-pilot/` (index: `AI-PILOT-REPORT.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `c651be06e3ad3589b4ad20c8e255ae55b6645ff44a5788513d3d18071977e12a`. `evidence/PACKAGE-CHECK.json` reports ok.

This is a diagnostic pilot on AI-drafted **provisional** labels. It ran in isolated sandboxes, and the declaration (`6218bb8f…`) was frozen before any request. The owner's Round 2 permission was reused, not requested again. No live code, service, setting, database or document was changed, and no business row changed: the business hashes of S, G and T equal A's. Sealed projects stay unopened.

- **Candidate** `e5a0a94` (scratch branch, parent `3d5607d`). It changes only `app/ai/evidence_reader.py`, flag-gated:
  - **G:** a bare revision token is never validated as an identity.
  - **T:** G, plus region support from the rotation-correct text layer or local OCR, plus one independent context read of an own identity or revision that was not validated. The acceptance rule is unchanged.
- **Tests:**
  - Candidate full suite, flags off: 1681 passed, 2 failed. Both failures reproduce on `3d5607d`.
  - Focused modules: flags off 216/216, G 216/216, T 213/216. The 3 T failures are recorded scripted-sequence effects, none a new acceptance.
  - BOQ queue: 8/8.
- **Sample:** 12 documents from 5 exploration projects, plus BOQ sheet EP-22510.
- **Requests:** 72 settled of the 150 cap. Per arm: A 2, S 18, G 26, T 9, BOQ-S 5, BOQ-T 12. Cost is unknown.
- **Results:**
  - 0 critical acceptances in any arm.
  - The guard never fired, so S→G is run-to-run variance only.
  - T's scope was closed by its declared token breaker: one FA-105 discovery took 81,625 input tokens over 8 CLI turns. Nothing was raised or reset, and 7 documents were not attempted by T.
  - On the 4 documents all arms processed, G→T recovered one held revision (targeted read) and one identity with an uncertain label (region support). It also AI-confirmed the scan identity `P10781` by local OCR.
  - BOQ-T spent its 12 requests on uncertain rows first and flagged the panel line. At equal request count it matched BOQ-S. The sheet had no wrong accepted row, so detection benefit is untested.
- **Blockers found:** full-page discovery latency against the 120 s job budget, and CLI turn variance against the per-request token breaker.
- **EP-8430 H-06 BOQ control:** not run. Its day allowance is full until about 2026-09-30 19:00 UTC.

**Recommendation:** INCONCLUSIVE. The signal is promising and there is no safety regression, but the evidence is insufficient. The independent review requests are listed in the report (section 7).

**Status:** READY FOR INDEPENDENT REVIEW (not self-approved). There is no variant adoption, production rollout, M3 or sealed validation.

M2 remains **CHANGES STILL REQUIRED**.

# Response to Independent M2 Review 18: targeted AI pilot correction and efficiency-first continuation (2026-09-30)

Package: `real-project-pilot/ai-pilot-r18-correction/` (index: `CORRECTION-AND-CONTINUATION-REPORT.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `fa7a88da3624b0028bd44fd728f7ea6d6ee75b5501fb12a0bb40d0f33a74dae0`. `evidence/PACKAGE-CHECK.json` reports ok. `ai-accuracy-pilot` and the earlier packages are unchanged.

**Correction**, done offline in isolation. The successor is `c216206` (scratch branch, parent `e5a0a94`), and only `app/ai/evidence_reader.py` changes, flag-gated.

| Finding | Disposition |
|---|---|
| **R18-01** | Fixed. A genuine targeted recovery completes the field only with a legible, own-role value. Primary and targeted outcomes are kept apart. The field is persisted, reloaded and selected, with the revision target intact. Empty, illegible, timeout, refusal and wrong-role reads never complete and keep the last-good value. A disagreement completes as a conflict and an unsupported read as a candidate; neither validates. |
| **R18-02** | Fixed. No targeted read follows a failed, refused or budget-refused primary or escalation request, and exhaustion is kept. |
| **R18-03** | Fixed. Keyed scripted providers replace the positional queue. The R7, R8 and R10 scenarios pass with flags off, G and T, and their later stages now run. There is a stated, tested required-first scheduling contract. |

The reviewer's probes reproduce exactly on `e5a0a94` and behave as required on the successor.

**Tests on the successor:**
- Focused modules: flags off / G / T 246/246/246.
- T+E: 246 with a whole-sheet frame shim; 19 frame-dependent script failures without it, explained in the report.
- r16.1 harness: 66 passed. BOQ queue: 8 passed.
- Full suite, flags off: 1711 passed, 2 failed (the known baseline failures, which reproduce on `3d5607d`).

**Efficiency change E** (a separate flag):
- located discovery for drawing sheets from the application's own title-block labels and strip;
- located absence recorded as incomplete;
- request and OCR timeouts bounded by the job's remaining time.

Offline: the located area contains the labelled identity on 8 of 9 drawing sheets; the ninth, a scan, cannot be verified offline.

**Guard:** an offline replay of the confirmed `Rev.0` acceptance reproduces the acceptance with the guard off and holds it with the guard on. 11 short-identifier controls pass.

**Labels:** v2 adds only the Review 18 AI source review, with provenance; v1 is kept. Rescoring the stored results under v2 changes no score; only the Reply to Comments label becomes resolved.

**Continuation**, frozen before any request (declaration `7b2513b2…`):
- **Budget:** the residual of the original 150 was reconciled at 78, with H-06's 24 reserved first. Requests used: A 1, S 15, T2 16, so 32 used and 46 left (24 reserved).
- **Sample:** 4 exposed large-sheet controls plus 3 new sheets labelled before prediction.
- **Results:** 0 critical acceptances and no business-row change. Across all 7 planned documents, identities recovered S 2 → T2 5 and revisions S 3 → T2 5 (precision 5/5). On the matched 4, T2 recovered 4/4 identities and 4/4 revisions.
- **Attribution:** an offline replay of S's own captured readings shows most gains come from rotation-correct region support (deterministic), not new model reads. Located discovery supplied regions for one sheet. The targeted read made one request with no score change.
- **Costs:** two deadline-bound discovery timeouts, and a wrong-edge strip on a scan (an honest incomplete).
- **Tokens:** located discovery used about 14k input tokens against about 31k for the full page. Latency is mixed and model-variable.

**H-06: PENDING, not waived.** The runner refused before any request at 13:47 UTC because EP-8430 was at 60/60. It can take one arm (12 requests) from 18:53:57 UTC and both arms (24) from 18:55:21 UTC on 2026-09-30. A dry run shows the frozen BOQ-T queue (held rows first) cannot reach H-06's accepted wrong rows within 12 requests. The queue was not re-tuned.

**Status:** submitted for independent review (not self-approved). The experiment is not complete while H-06 is pending. There is no variant adoption, production rollout, M3 or sealed validation.

M2 remains **CHANGES STILL REQUIRED**.

# Response to Independent M2 Review 19: E absence semantics, coverage reporting, actual-crop validation, H-06 (2026-09-30)

Package: `real-project-pilot/review19/` (index: `CORRECTION-REPORT.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `4b2347b3790c2f3eedbaa62fc0c9d0760f730f3b88eb0a8409d6bb98c69ffb1e`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages and the reviewer's files are unchanged.

The successor `69ee759` (scratch clone; parent `c216206`) changes only `evidence_reader.py`, behind E. It was frozen and hashed before validation. No model request was made in this task.

**Reproduction:** the reviewer's contracts on `c216206` gave 2 failed, 6 passed. The probe JSON is identical to the reviewer's. On the frozen successor with the v2 replay, all 8 pass.

| Finding | Disposition |
|---|---|
| **R19-01** | Fixed. A located crop never establishes absence outside what it inspected: text-layer silence no longer means `absent_by_discovery`, and uninspected decisions are `incomplete:located_region_only`. E becomes `.2`. Persisted-stage tests on the real crop cover a raster stamp outside the crop, plus these controls: an ordinary whole-page document, a wholly scanned sheet, decision words outside the crop, a genuine decision read, and a failed re-read or later crop that keeps the good decision. |
| **R19-02** | Fixed as coverage result version 2; stored attempts are unaltered. Required fields are explicit; transport state is separate from field coverage; discovery absence is kept distinct from a completed read. |

The R19-02 replay, over all 7 planned documents:
- All-planned recovery is unchanged (S identity 2 / revision 3; T2 5 / 5).
- The v1 four-document group is renamed `no_transport_stop_subgroup`.
- Documents with all required fields usable in both arms: 1 (819-TL-101); under R19-01, 0.
- Identity and revision read in both arms: 3 each (T2 3/3, S 1/3 and 2/3). Decision read in both arms: 0.

**Actual E path** (16 modules, 259 tests on the frozen successor):

| Run | Result |
|---|---|
| flags off / T | 259 / 259 passed |
| T+E, actual crop (coordinate adapter, real locator) | 22 failed, each classified from the adapter's own log |
| T+E, whole-page shim (compatibility only) | 12 failed, all in the new actual-crop module, by design |
| T+E, raw | the same 19 as disclosed |

The 22 actual-crop failures: in 20, the fixture's decision (and in one also its revision) is printed outside the real crop, so it is never read. In the other 2, the page is `partial` because its decision is unknown; all other assertions passed. The legacy tests were not edited. This shows an E coverage cost: decisions outside the title block are not read on drawing sheets.

**Full suite on the final frozen candidate** (flags off): 1724 passed, 2 failed (the same known baseline tests and messages), 35 skipped.

The four conclusions, stated separately:

1. **Correction acceptance is requested.**
2. **Extraction accuracy is unresolved.** The gain is mostly rotation-correct support; targeted calls show no incremental gain; no variant is chosen.
3. **Evidence and label uncertainty is unchanged.** Labels are AI-drafted or AI-reviewed; no human sign-off is implied.
4. **H-06 is PENDING.** The frozen declaration, runner and binding are unchanged. The live preflight at 15:26:47 UTC showed:
   - ledger 104/150 settled, 0 open reservations, H-06 scopes and allowance unused;
   - EP-8430 at 60/60.

   The runner refused before any dispatch, and the refusal is saved. By the live counter at that check, one arm fits from 18:53:56 UTC and both from 18:55:20 UTC on 2026-09-30. That window must be re-verified at dispatch.

A prospective experiment isolating the rotation fix, ROI discovery and targeted calls is proposed, not executed.

**Status:** submitted for independent review (not self-approved); the experiment is not complete while H-06 is pending. M2 remains **CHANGES STILL REQUIRED**.

# Response to Independent M2 Review 20: H-06 status and a draft isolated experiment (2026-09-30)

Package: `real-project-pilot/review20/` (index: `STATUS-AND-H06.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `2aa5a725620e8127b0cb059ed145b680bcf979673167d28daa07cde831123a2d`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages and response entries are unchanged.

No model request was made; the ledger is unchanged at 104/150 settled.

**Status, stated separately:**

1. The R19 corrections are ACCEPTED by Review 20; they are not reopened.
2. E (title-block-first discovery) remains experimental and is NOT approved as the default; it leaves off-title-block consultant decisions unread.
3. **H-06 is PENDING.**
4. Accuracy and label uncertainty are unresolved; the labels are AI-drafted or AI-reviewed, and no human signature is implied.
5. M2 is not accepted.

**H-06:** the frozen binding is unchanged (declaration `7b2513b2…`, `cont_boq.py`, the accepted `3d5607d` BOQ reader, the queue and the r16.1 matcher).
- **Live preflight at 2026-09-30 17:11:10 UTC:** ledger 104/150 settled with 0 open reservations; no H-06 ledger entry; the H-06 allowance never opened; EP-8430 at **60/60**.
- **Runner:** it refused before any request. The refusal and preflight are saved.
- **Eligibility by the live counter at that check:** one arm from 18:53:56 UTC, both from 18:55:20 UTC. This is not an authorization.
- **No wait:** no automation was scheduled and there was no multi-hour wait.
- **Runbook:** `H06-RUNBOOK.md` gives the exact preflight / arm / score steps under the same binding.

**Prospective experiment: DRAFT / NOT EXECUTED** (`EXPERIMENT-DRAFT.md` and `.json`).

- **G, rotation clipping and OCR fallback** are isolated offline, on identical captured responses (P0→P1→P2→P3).
  - Exposed-data diagnostic result: G changes nothing; rotation clipping alone gives +3 and +4 correct validations; the OCR fallback gives +1; no wrong validation at any step.
- **ROI and X** are live 2×2 contrasts. G, the support policy and a deadline policy D (to be decoupled from E first) are held common; D itself is an optional separate arm.
- **Coverage:** page- and field-aware and fail-closed (a prototype with 7 passing tests; on the stored pilot it shows a multi-page page-2 gap).
- **Gates:** a decision-coverage adoption gate that counts off-title-block decisions; the decision-region strategy is proposed, not implemented.
- **Sample feasibility:** 283 unexposed in-scope PDFs across 10 non-sealed projects, with strata counts; 89 files are beyond the page scope and 15 are Word files, marked unsupported.
- **Workload** from the ledger: core design about 234 expected requests, cap 280, about 3.0M input tokens including cached. The price is unknown, so there is no dollar figure.
- **Funding:** a budget decision is requested only after review. The original residual is not assumed.

**Status:** submitted for independent review (not self-approved); the experiment is not complete while H-06 is pending. M2 remains **CHANGES STILL REQUIRED**.

# Response to the Review 20 task: H-06 completed; four-arm experiment prepared offline (2026-09-30)

Package: `real-project-pilot/review21/` (index: `CORRECTION-AND-PREP-REPORT.md`, status: `STATUS.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `5d5a1d26ca23de5d51233b5acdd8a932db69cd41c9205a18911a70960586a326`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages, labels and response entries are unchanged.

**H-06: COMPLETED under the original frozen declaration `7b2513b2…`** (unchanged runner, accepted `3d5607d` BOQ reader, frozen queue, r16.1 matcher; the new document reader is not bound into it). Live preflights immediately before each arm: ledger 104/150 settled, 0 open reservations, H-06 scopes and allowance unused; EP-8430 rolling day 45/60 at 18:54 UTC (12 fit), then 41/60 at 18:56 UTC. Both arms ran with 12 requests each (24 total; ledger now 128/150; no unknown usage; no reset, replacement scope, chunk allowance or reopened breaker).

| Arm | Requests | Rows reached | Wrong accepted rows detected | Control row | Full sheet |
|---|---|---|---|---|---|
| BOQ-S (EV1 selection) | 12 / 12 | 12 of 38 | **1 of 3** (L1 caught; L9, L19 not reached) | confirmed correct | no |
| BOQ-T (frozen risk queue, held rows first) | 12 / 12 | 12 of 38 | **0 of 3** (none reached) | not reached | no |

At equal requests (12) the counts are the same. A target never reached is not a detected error; the T result diagnoses the frozen queue under its real cap. H-06 completion closes the experimental control only.

**Four-arm experiment: PREPARED OFFLINE ONLY** (no model request; no new budget approved or requested until reviewed).

- Frozen R21 candidate `719e8de` (scratch; parent `69ee759`; only `evidence_reader.py` in the application): one switch per behaviour (guard, support v2, required-first scheduling, deadline, ROI, targeted). Support and scheduling no longer depend on the targeted branch; the deadline no longer depends on ROI. Flags-off identity equals the accepted one; the legacy G / T / T+E identity strings are unchanged; the four arms have distinct cache identities.
- Regression on the frozen candidate: flags off / T / L1 / L3 267 passed each; T+E raw 19 and actual-crop 22 failures, identical by test ID to the disclosed review19 sets (E's coverage loss, not hidden); L2 / L4 actual-crop the same 22; r16.1 harness 66 passed; harness integration 13 passed; full suite 1732 passed, 2 known baseline failures (same tests and messages).
- Harness: coverage v3 (every declared page, caller-enforced binding to source hash / profile / variant / policy, fail-closed missing pages, unsupported inputs and beyond-scope pages counted, extra facts outside scope counted); the actual arm runner and scorer dry-run end to end with a scripted provider (common A base, arm caches disjoint, deadline on every request, required reads before optional). Two honest findings: a restart under a new tag re-requests everything (a durable per-document allowance is a prerequisite before live runs); the synthetic stage did not exercise the cap.
- Sample frozen before labelling: 27 planned (24 primary across 5 strata and 10 projects, ≤ 3 per project; 2 long-PDF controls; 1 Word control); every page classified; 42 in-scope pages; a predeclared minimum of 4 screened off-title-block decision documents, with shortfall handling; labels and AI review to be drafted after the budget decision and frozen before any prediction.
- Workload from every in-scope page (price unknown): expected 509 core requests, proposed caps 688 (L1 160, L2 160, L3 180, L4 180, A 8), absolute ceiling 1,256; ~6.5M input tokens expected; worst-case rolling-day schedule 3 days (one arm per project per day), expected 2; frozen order and incomplete-pair rules declared. The review20 figure (~234 / 280) was first-page only.
- Draft declaration marked `DRAFT / NOT EXECUTED / NO NEW MODEL BUDGET APPROVED`; analysis plan: paired 2×2 with document-clustered bootstrap, gains by label status, P0–P3 described as conditional re-validation on fixed responses (cached OCR omitted in the submitted diagnostic), decision-coverage adoption gate retained.

**Status:** R19 corrections accepted; E experimental, not a default; H-06 complete; accuracy and label uncertainty unresolved; M2 **CHANGES STILL REQUIRED**. Requested now: independent review of this package, then the owner's decision on the 688-request core cap.

# Response to Independent Review 22: offline four-arm harness readiness (2026-10-01)

Package: `real-project-pilot/review22/` (index: `CORRECTION-REPORT.md`, status: `STATUS.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `79ef8fb5c97a87570a9314829e2469ddfc2ad005bef2938dd575d5da9e3b631f`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages, labels, reviewer files and response entries are unchanged.

No provider or model request was made (every run used the scripted dry provider in isolated dry roots); the live ledger is unchanged at 128/150 settled with no r21 / r22 live scope; no live schedule, cap increase, budget reset, new live scope or H-06 rerun. **The 688-request proposal is not approved.** No application code changed: frozen candidate `719e8de` (the R21 report's prose `58ff6fc…` was a stale short ID), accepted baseline `3d5607d`.

**Reproduced first:** the reviewer's probes and five regressions on the submitted R21 harness give the reviewer's result (2 failed, 3 passed; identical `INDEPENDENT-PROBES.json`); the static-share guard probe and the restart path were reproduced; the reviewer folder was never written to.

**R22-01 — corrected.** One eligibility contract (`coverage_v4.eligible_rows`, contract `harness-contract-2026-09-30.v4`) is applied before the accuracy call, the coverage, the matched subsets, the pair comparisons and the runner's tripwire. A mismatched or missing source hash and evidence of another arm's context earn no credit; every planned document stays in the denominator; rejected evidence is reported; a run with no eligible document is reported `valid_accuracy_claim = false`. The reviewer's regressions pass on v4 (5 passed); replaying the R21 dry outputs shows v4 = v3 with correct sources and 0 credit (v3: 9 identity recoveries per arm) under mismatched sources. Evaluator and retained-evidence / association contracts untouched.

**R22-02 — corrected.** Emitted pages are checked against the declared file's page count and the reader scope with distinct diagnostics (`page_not_in_document`, `page_beyond_reader_scope`, `invalid_page_identifier`), carried through the real scorer.

**R22-03 — implemented in the actual runner and exercised.** The reviewed r16.1 durable document allowance (scope / arm-profile-policy / document, charged before dispatch, lost results stay charged, cache hits charge nothing, ledger scope pre-checked) is integrated into `arm_ev.py`; one writer per sandbox and per document; `--resume` over the same sandbox (completed documents skipped only when the scoring contract binds them; interrupted work visible and limited to the remaining allowance); a new tag never recreates an allowance (refused before dispatch). The static per-arm share is withdrawn; the runner applies the declared whole-project reservation rule (versioned `whole-project-reservation-2026-09-30.v4`): a project whose rolling 24 h capacity does not cover the batch's worst case is persisted as deferred with zero requests, and a later resume takes it in declared order. Eight scenarios ran through the actual runner with a scripted provider and a fake clock (8 regressions passed): a document killed mid-reading and resumed attempted more than 12 reads and was capped at 12 across the restart; a new tag was refused; a second writer was refused and the document lock was busy; a reread produced only cache hits with unchanged charges; an exhausted arm scope was a budget stop with charged == sent == counter; a project with insufficient capacity sent zero requests and completed on the next simulated window without resetting totals; refusals before dispatch.

**Workload / declaration v2:** the schedule is generated by simulating the implemented rule (worst-case demand: last batch starts at 72 h, batches at 0 / 24 / 48 / 72 h; expected demand: 24 h; ~0.6 h run time per arm to add; assumptions stated; the S7 fake-clock runner evidence reproduced by the simulator). Three request figures are kept apart: expected 509; proposed authorized maximum 688 *if approved* (not approved); uncapped structural maximum 1,256. The p90-based token figure is a statistical planning estimate; price unknown; no cost or completion guarantee. The draft declaration is `DRAFT / NOT EXECUTED / NO NEW MODEL BUDGET APPROVED`, bound to `719e8de`, the frozen sample / stage, the R21 labels manifest, workload v2 and harness contract v4. Labels remain the prerequisite (AI-drafted / AI-reviewed provenance, unresolved items explicit, no human sign-off, no model call to finish them).

**Frozen and tested:** harness v4 frozen (`bindings/FROZEN-HARNESS.json`); harness v4 19 passed, runner 8 passed, unchanged v3 harness 13 passed, r16.1 controls 66 passed; H-06 replay through the unchanged scorer byte-identical (six files); application suites not rerun (no application change; the R21 results, including the disclosed ROI-configuration failures and the 2 baseline failures, stand).

**Status, stated separately:** (1) correction readiness — corrected offline, frozen, submitted for independent review; (2) H-06 complete and unchanged; (3) no new budget granted and no live run; (4) extraction accuracy and labels unresolved; (5) no chosen default (ROI / targeted remain experimental; R19 corrections stay accepted); M2 **CHANGES STILL REQUIRED**. Not self-approved. The next live experiment can be proposed only after these corrections are reviewed and the owner authorizes a concrete budget.

# Response to Independent Review 23: terminal experiment stops survive resume (2026-10-01)

Package: `real-project-pilot/review23/` (index: `CORRECTION-REPORT.md`, contract: `LIFECYCLE-CONTRACT.md`, status: `STATUS.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `04ccd8860976a0951bad71b430da6b0431634bbd0fbe08a62f47d265ccfd90e5`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages, labels, reviewer files and response entries are unchanged.

No provider or model request was made (scripted dry provider, isolated roots); the live ledger is unchanged at 128/150 settled with no r21 / r22 / r23 live scope; no live schedule, cap increase, budget reset, new live scope or H-06 rerun; **the 688-request proposal is not approved**; no override or reopening mechanism was created. No application code changed (`719e8de` / `3d5607d` clean). R22-01 and R22-02 are accepted and untouched; the scorer, scheduler and durable-allowance module are byte-identical to review22's frozen v4.

**Reproduced first:** the reviewer's `resume_stop_probe.py` (byte copy, adapted only in its output / workspace / runner path) on the submitted v4 runner: stop after EP-16830 with one critical tripwire result and 12 scripted requests; plain `--resume` dispatched 8 requests to EP-17428; regressions 1 failed / 2 controls passed.

**R23-01 — corrected (harness v4.1, runner `arm-ev-2026-10-01.v4.1`, lifecycle contract `runner-lifecycle-2026-10-01.v1`).** A terminal stop (critical acceptance on a resolved label; three consecutive provider failures) is persisted atomically the moment it is decided, before any manifest update, with its reason and triggering evidence, and is never overwritten. `--resume` loads and validates the persisted state — the stop file, the manifest's stop, a v4 record's terminal reason, or an offline reconstruction by the same tripwire over the projects already read — before the startup write and before any call can leave, and returns the preserved stopped result with zero requests (exit 4, refusal recorded, lists preserved, status `stopped`; never relabelled `completed`). Deferral, interruption recovery, completed-document skips, cache accounting, the 12 / document allowance, arm scope and rolling project limit are unchanged. Plain `--resume` is not approval to clear a stop; reopening requires a separate explicit decision and binding.

**Validated through the actual runner with the scripted provider** (5 lifecycle regressions passed): critical stop with pending work then plain resume — zero sends, original stop and evidence preserved; repeated resume — still zero, unchanged; terminal stop after the last project — stays `stopped`; three consecutive provider failures — terminal, resume cannot clear it, while a single failed request is not terminal; interruption before the stop file — recovery reconstructs the stop offline from saved evidence and refuses before dispatch; interruption after the stop file — recovery refuses on the file. Positive controls: the eight R22 runner scenarios rerun green with the v4.1 runner (daily deferral resumes when eligible; kill / resume uses only the remaining allowance). The reviewer's own probe on v4.1: resume sends zero requests with the stop preserved — 3 passed. Scoring tests 19 passed (unchanged scorer).

**Status, stated separately:** (1) correction ready for independent review; (2) H-06 complete and unchanged; (3) no new model budget, no live run; (4) labels and extraction accuracy unresolved; (5) no selected default; M2 **CHANGES STILL REQUIRED**. Not self-approved; the four-arm model experiment was not started. After this correction is accepted, the next gate is the concrete experiment / label preparation and the owner's budget decision.

# Response to Independent Review 24: provider-failure stop recovery (2026-10-01)

Package: `real-project-pilot/review24/` (index: `CORRECTION-REPORT.md`, contract: `LIFECYCLE-CONTRACT.md` v2, status: `STATUS.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `135fa6f70144d0f816de614bbf0904fb03439717f3ed052018683b9aa9f32059`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages, labels, reviewer files and response entries are unchanged.

No provider or model request was made (scripted dry provider, isolated roots); the live ledger is unchanged at 128/150 settled with no r21–r24 live scope; no live schedule, budget reset or increase, new live scope, H-06 rerun, sealed-project access or label edit; **the 688-request proposal is not approved**; no override or reopening mechanism. No application code changed (`719e8de` / `3d5607d` clean). The scorer is byte-identical to review22's v4 (R22-01 / R22-02 kept); the R23 critical-stop paths are unchanged.

**Reproduced first** (reviewer's probe, helper and regressions staged byte-identical beside the unchanged v4.1 runner): with three scripted failures and the before-file kill, the initial run exited 98 with three recorded `transport` outcomes and no stop on disk; plain `--resume` exited 0, sent 16 new scripted requests and completed. The after-file control refused. Regressions 1 failed / 2 passed.

**R24-01 — corrected (harness v4.2, runner `arm-ev-2026-10-01.v4.2`, lifecycle contract v2).** A small fsync'd provider-outcome journal bound to the run (header before any dispatch; `attempt` before each call that may leave; `result` after it returns and before the failure-streak decision) makes every decided provider stop durable before the stop file. On `--resume`, before the startup write and any dispatch, a validated trailing streak of three completed failures reconstructs the provider stop with its original reason and the journalled failures as evidence and refuses with zero requests (exit 4). A torn, foreign, inconsistent or missing journal (when work was recorded) refuses with zero requests (exit 5), writes no stop and leaves the run record untouched. Otherwise the durable streak is carried across the restart, so plain resume cannot reset the provider breaker. A success resets the streak; cache hits, budget refusals and unresolved in-flight requests do not count. The harness was frozen before the final validation.

**Validated through the actual runner, critical and provider paths reported separately.** Critical stops: the existing lifecycle scenarios all pass with v4.2 (ordinary resume, repeated resume, stop after the last project, before-file and after-file interruptions). Provider stops (7 boundary regressions): ordinary, before-file (reconstructed, 0 new sends), after-file and repeated resume (stop file, charges, journal and io unchanged) are all terminal. Two failures plus an unresolved request, or a success between failures, do not reconstruct a stop. The breaker survives a restart. Four kinds of unusable evidence refuse without dispatch or fabrication. Controls: the eight runner scenarios pass (kill / resume allowance, cache hits, daily deferral), and their journals show budget refusals and cache hits recorded but not counted. Journal unit tests 23, lifecycle 5, runner 8, boundary 7 and scorer 19 all passed. The reviewer's probe on v4.2 passed 3/3: before-file resume exit 4 with 0 new requests.

**Status, stated separately:** (1) submission ready for independent review; not milestone acceptance; (2) H-06 complete and unchanged; (3) no new model budget, no live run; (4) labels, extraction accuracy and the default choice unresolved; (5) M2 **CHANGES STILL REQUIRED**. Not self-approved; the four-arm experiment was not started.

# Response to Independent Review 25: reject contradictory neutral journal results (2026-10-01)

Package: `real-project-pilot/review25/`. The index is `CORRECTION-REPORT.md`; the contract is `JOURNAL-KIND-OUTCOME-CONTRACT.md`; the status is `STATUS.md`. Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `769320d741e5683a1b5466eac0b1e8da88cb86f9e65f6f6f40b78fa9984cf242`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages, labels, reviewer files and response entries are unchanged by this task.

**R24-01 remains corrected.** The original before- and after-stop-file probe was rerun on the frozen successor. Both cases resume with exit 4, zero new requests and `stopped`, and 3 regressions passed. The runner `arm_ev.py` is byte-identical to v4.2.

**R25-01: reproduced, then corrected.** The reviewer's probe, helper and regressions were staged byte-identical beside the unchanged v4.2 runner. Three mutations each loaded as ok with streak 2, resumed with exit 0, sent 16 new scripted requests and completed. The regressions gave 3 failed and 3 controls passed (pytest exit 1). Harness v4.3 (validator `provider-outcomes.v1/validator-2`) now enforces the allowed kind/outcome combinations for all five result kinds:
- `ok` and `failure`: unchanged;
- `cache_hit`: outcome `"ok"`;
- `budget`: outcome starting with `budget`;
- `none`: no outcome.

A contradiction makes the journal indeterminate. Resume then exits 5 before dispatch with zero requests and writes no stop. The run record, allowance charges, journal and io stay byte-identical, and the refusal is recorded with its reason. The journal format is unchanged, and all 25 existing v4.2 journals load identically under both validator revisions. Valid neutral results stay neutral, success still resets the streak, unresolved attempts stay neutral, and restarts still do not reset the breaker. Saved project lists on reconstructed stops are untouched. The harness was frozen before the final validation.

**Fresh tests on the frozen successor** (actual runner, scripted provider):
- the reviewer's three mutations: indeterminate, exit 5, 0 new requests, saved state unchanged;
- the unmutated control: streak 3, stop reconstructed, exit 4;
- reviewer's probe: 6 passed;
- submitted 62-test set, one run: 62 passed, 0 failed, 0 errors, 0 skipped, pytest exit 0;
- R25 regressions: 32 passed, pytest exit 0.

**No new accuracy evidence:** these are synthetic harness tests. **Budget:** no model call, no new model budget, no live run and no new live scope. The ledger stays at 128/150 settled, H-06 is complete and unchanged, and the 688-request proposal remains unapproved. Labels, extraction accuracy and the default variant remain unresolved. M2 **CHANGES STILL REQUIRED**. This submission is ready for independent review and is not self-approved.

# Four-arm accuracy experiment: readiness for the owner's budget decision (2026-10-01)

Package: `real-project-pilot/review26/` (index: `READINESS-REPORT.md`; proposal: `BUDGET-PROPOSAL.md`; labels: `LABELS-SUMMARY.md`; runbook: `RUNBOOK.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `a6bf987d00d446479b09f1314cc70cae1be8a9f4687ba131866928a675fac2f9`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages, the R21 label skeletons, reviewer files and response entries are unchanged; this entry is appended to the current prefix (`182e6556…`).

This follows Independent Review 26, which accepted R25-01 on harness v4.3. **No model or provider request, schedule or dispatch was made**, and no application, service, live-data or original-document change was made. The ten sealed projects stay sealed.

- **Declaration.** The final declaration (`aec4d4df…`) keeps the reviewed four-arm design: candidate `719e8de`, baseline `3d5607d`, the frozen 27-document sample with its controls, evaluator .9. It binds by sha256 the reviewed v4.3 runner, journal, scorer, allowance and the A runner's imports, plus the frozen labels, under a new ledger scope family. The original run's remaining 22 requests are not used.
- **Labels.** The R21 label files were skeletons. All 27 documents and 42 in-scope pages are now labelled from local renders and text layers, with page, region and hash evidence, and frozen before any prediction (`r26-labels-2026-10-01.1`).
  - They are AI-drafted with a same-assistant second pass: not human, not blind, not independently reviewed (the manifest's independent-review step remains open).
  - Uncertainty is kept as *medium* confidence on 10 documents.
  - All 6 consultant decisions in the sample lie outside a title block, which meets the off-title-block minimum by count. A strict reading of the screened-candidate rule leaves a shortfall of 3, which is disclosed; there was no top-up, because the sample is frozen.
- **Proposal.** Expected ≈ 509 requests; **enforced maximum 688** (A 8, L1 160, L2 160, L3 180, L4 180); structural maximum 1,256, which is never an allowance. The existing per-document limit (12) and rolling per-project limit (60 / 24 h) stay in force. The 6 ledger-enforcement cases were demonstrated on the actual ledger class.
- **One assumption corrected.** The 4-hour scope elapsed limit could not hold the declared rolling-day deferral schedule. The revised proposal sets 96 h for the document-arm scopes; the request and token caps are unchanged. Cost is unknown.
- **Preflight.** A scripted-provider preflight of the exact binding over the real stage ran with every step exit 0. Deferral fired as designed. On a contents page, a fabricated scripted decision was validated, and the tripwire stopped L1 and L2 terminally. This is a completion risk to disclose, not an accuracy measurement.

**Status, stated separately:** (1) the harness correction is accepted; (2) labels are ready and frozen, but specifically incomplete on independent review and the strict off-title-block reading; (3) funding is pending; (4) there has been no live run; (5) accuracy is not yet established; (6) no default is chosen; (7) M2 is not accepted: **CHANGES STILL REQUIRED**. H-06 is complete and unchanged.

**Owner decision requested:** approve or decline a new budget of at most 688 requests under scopes `m2-four-arm-final-2026-10-01-{A,L1,L2,L3,L4}` (caps 8 / 160 / 160 / 180 / 180; 4 M input / 600 k output tokens each; 96 h elapsed per document arm, 4 h for A) on the `claude-code` provider at an unknown dollar cost, running exactly declaration `aec4d4df…`. Nothing will be scheduled or dispatched while this decision is pending.

# Response to Independent M2 Review 27: funding clarity and independent label binding (2026-10-01)

Package: `real-project-pilot/review27/` (index: `CORRECTION-REPORT.md`; decision: `DECISION-CARD.md`). Manifest `evidence/EVIDENCE-MANIFEST.json`, sha256 `ae067a90b94598fcfd7e6f49e2128007ef6312ca5699157c5270f5ec4d3945e9`. `evidence/PACKAGE-CHECK.json` reports ok. Earlier packages (including review26 and declaration v1 `aec4d4df…`), the r26.1 labels, the R21 skeletons, the reviewer files and the earlier response entries are unchanged. This entry is appended to the file as found (prefix `e621fa7e…`).

There was no model or provider request, scope creation, schedule, dispatch or H-06 rerun. No application, harness, ledger, scorer or stop-policy file changed. **The 688-request proposal remains unapproved.**

**R27-01, corrected.** The budget proposal, decision card, runbook and declaration now state the following:
- **Requests:** at most 688 *application-visible* requests (A 8 / L1 160 / L2 160 / L3 180 / L4 180). One CLI request may contain several provider-internal turns.
- **Tokens:** the token thresholds act on *estimates* before dispatch. Actual usage is recorded afterwards, and an overshoot opens a breaker that stops later requests. The `claude-code` CLI cannot enforce actual token limits, so there is no hard actual-token bound.
- **Cost:** unknown.
- **Elapsed time:** the 96 h document-arm lifetime (4 h for A) is an unapproved proposal, not a completion guarantee.

The "at most 20 M / 3 M", hard per-request and "never an overspend" claims are removed. The frozen ledger contract and the independent probe are cited, and an old/new diff of the owner-facing claims is included.

**R27-02, applied as labels `r26-labels-2026-10-01.2`** (manifest `ed3c88e4…`), beside r26.1 and bound by hash to the independent record:
- **Provenance:** the independent owner-delegated AI source review is credited. It is not human and not blind.
- **D17:** the decision value is kept, and the actor is recorded as inferred field-level uncertainty. The schema limitation is disclosed: the runner's uncertainty list is document-level and doubles as the stop exclusion, so the stop policy is unchanged and the actor is not scored.
- **D19:** the literal C. Revise & Resubmit is recorded beside the coarse `rejected`; the enclosed sheets stay UR.
- **D05:** the printed ASBUILT stage is kept as metadata.
- **D27:** marked not visually verified, with no extraction credit.
- **Off-title-block minimum:** recorded under the reviewer's pre-run interpretation. Five source-attributed decision documents among the 24 primary meet the minimum of 4, the screen's 1/4 result is kept, and there is no top-up.
- **ROI population:** recomputed with the frozen predicate. Only D16–D18 are crop-eligible (one project, 2 explicit stamps), while D04, D19 and D22 use whole-page discovery. This makes the ROI comparison a small diagnostic.

**Final binding.** Declaration v2 sha256 **`6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1`** supersedes v1, and an approval of v1 does not carry over. Its scopes, limits and caps are identical to v1. Re-scoring the review26 preflight runs under v2 gives identical recovery, coverage and eligibility.

**Status, stated separately:**
1. Correction ready for review (not self-approved).
2. The owner's funding decision is pending (`DECISION-CARD.md`).
3. The experiment has not run.
4. Extraction accuracy is unresolved.
5. No default is selected.
6. M2 remains **CHANGES STILL REQUIRED**.

# Four-arm accuracy experiment executed under declaration 6c0189b3 (2026-10-01)

After Review 28 accepted the Review 27 correction, the owner authorized execution of declaration `6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1` in writing. The authorization is recorded verbatim, sha256 `2e700c3e…`.

Package: `real-project-pilot/four-arm-final/`, indexed by `FINAL-EXPERIMENT-REPORT.md`. Its manifest is `evidence/EVIDENCE-MANIFEST.json`, sha256 `cf1b95f1e88889c82fa6897507773185d4abbfbeaa1228c0b8ed1a4f981d419b`. `evidence/PACKAGE-CHECK.json` reports ok. The check re-runs the frozen scorer and the analysis offline and requires identical results.

Earlier packages, the labels r26.1 and r26.2, the reviewer files and the earlier response entries are unchanged. This entry is appended to the file as found (prefix `2126426c…`).

**What ran.** A, L1, L2, L3 and L4 ran in the frozen order. Before every start, the bindings, ledger, rolling capacity and writers were re-checked.
- **Requests:** 234 of the 688 application-visible requests were dispatched: A 4, L1 34, L2 64, L3 66 and L4 66.
- **Tokens:** Provider-reported actual usage was 2,472,165 input tokens, of which 1,533,942 were cached, and 353,256 output tokens. Ten timeouts were charged at their estimates, adding 292,346 input and 63,901 output tokens. The ledger total is 2,764,511 input and 417,157 output tokens.
- **Cost:** unknown.
- **L1:** Its breaker opened when one request used 70,264 actual input tokens. This was a budget stop, and L1 was not resumed or reset.
- **Other arms:** No other breaker opened. There was no terminal stop and no deferral.
- **Unchanged:** No limit, model, label, sample or stop rule changed. No business row, document role, source file or production state changed.

**Results.**
- **Comparisons:** Every predeclared comparison is **INCONCLUSIVE**. Too few matched facts exist for decisions, and the identity and revision intervals include zero.
- **Critical acceptances:** None landed on a resolved label. Two landed on labels on the uncertainty list: L2 on D26 page-2 revision, and L4 on D03 page-1 identity. A targeted read introduced the D03 one.
- **Targeted reads:** The X gate fails in both pairs. The targeted reads found the true value of D04, D06 and D12, but the reader's conflict rule held the earlier wrong value each time.
- **Decisions outside the title block:** No arm read a decision on D16, D17 or D18. The ROI decision gate is confounded for L1 → L2 and fails by rule for L3 → L4.
- **Adjudication:** Post-run notes are separate and do not change any score. They cover the D26 running footer, D03, the conflict rule and wrong absences.

**Status, stated separately:**
1. The experiment has been executed. It is submitted for independent review and not self-approved.
2. Extraction accuracy has been measured, but the comparisons are inconclusive.
3. No default is selected or deployed.
4. There was no production change, and M3 has not started.
5. M2 remains **CHANGES STILL REQUIRED**.

# Response to M2 Review 29: a bounded offline accuracy candidate (2026-10-02)

Package: `real-project-pilot/review29/`, indexed by `CORRECTION-REPORT.md`. Its manifest is `evidence/EVIDENCE-MANIFEST.json`, sha256 `ca3f33ad4fadec2072d52b6f90e618c90bfabc16b12bae054c21a8739210d87b`. `evidence/PACKAGE-CHECK.json` reports ok.

`four-arm-final/` is preserved byte for byte, and so are labels r26.1 and r26.2, evaluator .9, baseline `3d5607d`, candidate `719e8de`, harness v4.3, the ledger, the reviewer files and the earlier entries. This entry is appended to the file as found (prefix `55bb40ab…`).

There was no model or provider request, live run, production change, migration or label change.

**Candidate.** `C:/t/iso/cand-r29`, commit `a8aaced`, parent `719e8de`. It adds four independent switches, each with its own identity. With all four off, it equals `719e8de`.
- **Identity role guard (IG):** headings, clause titles, generic labels, revision tokens, running headers and footers, and reference-role values are held, with their region.
- **Conflict adjudication (CA):** a written evidence-ordering contract. Two agreeing model readings, an own-role label and source binding are required, and every competitor must be disqualified. Recency is never used.
- **Decision-region path (DR):** a bounded path. An unread or uninspected region is unknown, never absent.
- **Page association invariant (PA):** dependent facts bind only to an identity established on their own page. Evaluator `.10` (`m2_eval6`) associates per fact, and `.9` is unchanged.

Contracts were frozen before the code. Two revisions were frozen before their fixes and are reported:
- **C2 revision 1:** split-text truncations had been validated in the replay.
- **C1 revision 2:** guarding a conflict suppressed the targeted read.

**Offline results.**
- **Defects:** all four were reproduced from the stored outputs before implementation.
- **Tests:**
  - **Review 29 tests:** 92 pass.
  - **Focused suites:** 652 passed and 0 failed.
  - **Full suite:** 2 failures, identical by name and message to the accepted baseline's clean re-run. A stalled overnight baseline run is disclosed, not used.
- **Replay** (24 runs, 0 model requests):
  - flags-off fidelity: L1 and L2 at 27 of 27, L3 and L4 at 25 of 27, the difference being original-run OCR timing;
  - **0 newly validated wrong facts**;
  - critical acceptances under the combined configuration: L1 1 → 0, L2 1 → 0, L4 1 → 0;
  - wrong decision absences: 2 → 0;
  - newly validated correct facts: D04 and D09 only;
  - PA costs 1 to 2 correct revisions in L1 and L2.
- **Diagnostic only:** this is an exposed corpus, and no general accuracy is claimed.

**Fresh validation.** Planned but not run: 20 unseen, non-sealed documents, the accepted baseline against the combined candidate, at most 128 requests. It needs the owner's authorization.

**Status, stated separately:**
1. Correction: READY FOR INDEPENDENT CORRECTION REVIEW (not self-approved).
2. Historical experiment: preserved.
3. Accuracy: unresolved.
4. Labels: unchanged.
5. Default: none selected.
6. M2: **CHANGES STILL REQUIRED**. M3 has not started.

# Response to Independent M2 Review 30: Review 29 package corrections and fresh-validation design (2026-10-02)

Package: `real-project-pilot/review30/`, indexed by `CORRECTION-REPORT.md`. Its manifest is `evidence/EVIDENCE-MANIFEST.json`, sha256 `453a9d61207c445be864ec96e9b9516517e14ea19813adb5fd46834daf10636c`, written last. `evidence/PACKAGE-CHECK.json` reports ok.

`review29/`, `four-arm-final/`, the candidate code, the tests, the evaluators, labels r26.1 and r26.2, the ledger (483 entries) and the earlier entries are unchanged. This entry is appended to the file as found (prefix `80f85bb7…`).

There was no model call, new document content, staging, budget scope, authorization or validation run. No API key was requested.

- **R30-01:**
  - **Final candidate:** `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` throughout. `a4ce6a3` is kept only as the explicitly historical first commit.
  - **Overlay:** Review 29 `CHANGE-MAP.md` and `COMMANDS.md` are superseded by a versioned overlay. Its counts match the JUnit evidence: 40, 20, 14, 6 and 12, for 92 in total.
  - **Checker:** it now fails on a stale commit, on a historical commit presented as final, and on a stale count. Ten checker tests prove it, and they also show that the original Review 29 change map fails.
- **R30-02:** at least 12 matched resolved documents per claimed field, with a target of 16. The selection is two-stage, seeded and predeclared, with replacement by frozen-label truth presence only, at most one extension, and a freeze before prediction. Identity and revision are feasible. Decision is not guaranteed, with a worst case of 11. Below 12, decision is out of scope and the M2 decision gate stays open.
- **R30-03:**
  - **Option A**, within-project: templates are exposed, so it shows regression safety only.
  - **Option B**, fresh projects, metadata only: six projects from six contractors untouched by M2 (22936, 19905, 20561, 16385, 29255, 24752), with four alternates. Sealed projects are excluded, and it needs a **new owner permission**.
  - **Recommended:** Option B for M2 closure.
- **R30-04 and R30-05:** `REVISED-FRESH-VALIDATION-PLAN.md` and `DRAFT-DECLARATION.json` bind the following:
  - the verbatim M2 thresholds, with source hashes;
  - the matched minimum of 12;
  - paired estimates and a cluster bootstrap with fixed seeds;
  - the request-normalized benefit gate, with natural caps;
  - full token and refusal accounting;
  - the concentration rule;
  - primary outcomes for association, PA revision loss and DR decisions and cost;
  - one capture per fingerprint, with replay and a reported variation probe;
  - adjudication only in an immutable note.

  The budget card proposes at most 332 requests, with cost unknown, and **requests nothing**.

**Status, stated separately:**
1. Offline candidate: accepted (Review 30).
2. Package correction: READY FOR INDEPENDENT PREPARATION REVIEW (not self-approved).
3. Cohort: Option A covered; Option B not permitted. Sealed projects stay sealed.
4. Labels: none for the fresh run.
5. Budget: none requested.
6. Live run: not started.
7. Accuracy unresolved, no default selected, M2 **CHANGES STILL REQUIRED**, M3 not started.

# Response to Independent M2 Review 31: selector, experiment contracts and dry run (2026-10-02)

Package: `real-project-pilot/review31/`, indexed by `CORRECTION-REPORT.md`. Its manifest is `evidence/EVIDENCE-MANIFEST.json`, sha256 `d5fe164918741014ded7425cda7679bd310a97b07511dd85bb65ec642077c460`, written last. `evidence/PACKAGE-CHECK.json` reports ok: 58 files, 51 tests re-run from the packaged copies, and every binding re-verified.

The candidate `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` is frozen and clean. `review30/`, `review29/`, `four-arm-final/`, labels r26.2, the evaluators, the ledger (483 entries, 17 scopes) and the earlier entries are unchanged. This entry is appended to the file as found (prefix `bdbe511c…`).

There was no model call, provider contact, ledger scope, placeholder download, new document opened or rendered, label drafted, budget request or authorization. The GPT bridge stays disabled.

- **R31-01:** the selector is rebuilt on tested rules (4 tests).
  - **Topology:** explicit classification, with 175 ambiguous hierarchies failing closed.
  - **Contractors:** canonicalized names and alias clusters, failing closed.
  - **Used sets:** structured sources only, including all 959 M1/M2 databases, giving 199 used EPs.
  - **Proposal:** Option B, with evidence rows: picks 3563, 22349, 27331, 15744, 26687 and 29255, and alternates 22317, 29628, 25909 and 28908. It is metadata only and **not permitted**.
  - **Review 30 picks:** reconciled. 19905 is excluded as an alias of a used contractor, three alternates as ambiguous hierarchies, and 29255 is selected again.
- **R31-02:** dispatch only when identity, revision **and** decision each have at least 12 resolved, independently reviewed documents. Otherwise extension-1, then extension-2, then **PREPARATION BLOCKED**. There is no partial closure run. With both extensions, the worst-case decision count is 17, and P(below 12) = 0.001 at the low rate.
- **R31-03:** one rule. B and C have **equal maximum allowances**: 240 requests each, equal token thresholds and elapsed time. The gate is applied as quoted, "at equal caps", and the request difference, including requests inherited from B, is the policy cost. An unequal-cap gate is refused as not applicable. The ceiling rises from 332 to 556; expected use is unchanged at about 171.
- **R31-04:**
  - **Stop rules** (8 tests): a resolved critical in B makes the comparison INVALID and blocks C. In C it is a terminal stop and a failed safety gate. In R or P it is a finding only, never a live stop.
  - **Shared-response store** (21 tests): one dispatch per bound fingerprint; no B/C sharing across any context difference; R is served C's capture, including failures, and never re-sends; reference and probe requests never alter B or C; an interrupted dispatch is charged and never re-sent; provenance is kept.
  - **C-from-B state check** (5 tests).
- **R31-05:**
  - **Scorer:** `score_bcr` (13 tests).
  - **Dry run** over the staged four-arm sample, with **0 model requests** and the ledger unchanged. The population gate returns PREPARATION BLOCKED (decision 6 < 12), so a live run would stop there. Every later stage still ran as an exercise. The rows of C and R are identical to the Review 29 replays, and the resume drill re-sent nothing.
  - **Bindings:** the immutable binding manifest `2dfef08e…5fba` is bound by draft declaration v2 `19720ad9…8b5d`.
- **Owner decisions recorded:** label review is delegated to the Codex reviewer and recorded as independent AI review, never human sign-off. The GPT bridge stays disabled.

**Status, stated separately:**
1. Offline candidate: accepted (`a8aaced`, frozen).
2. Preparation package: READY FOR INDEPENDENT PREPARATION REVIEW (not self-approved).
3. Cohort: Option B proposed, metadata only. A new owner permission naming the EP numbers is required and has not been requested. Sealed projects stay sealed.
4. Labels: none for the fresh run. Review will be the owner-delegated independent AI review, not human sign-off.
5. Budget: none requested. 556 is a proposal ceiling.
6. Live run: not started.
7. Accuracy unresolved, no default selected, M2 **CHANGES STILL REQUIRED**, M3 not started.

# Cohort preparation after Independent M2 Review 32: initial pool drafted, handed to independent label review (2026-10-03)

Package: `real-project-pilot/fresh-cohort-r32/`, indexed by `PREPARATION-REPORT.md` and `REVIEWER-PACKET.md`. Its manifest is `evidence/EVIDENCE-MANIFEST.json`, sha256 `15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed`, written last. `evidence/PACKAGE-CHECK.json` reports ok. The check covers 110 files; 72 staged files, 149 renders and 189 crops, all re-hashed; the OneDrive originals; the draft bindings; blank reviewer columns; and the unchanged ledger, trees and Review 31 package.

**Authorization:** the owner's authorization is recorded verbatim (`AUTHORIZATION-2026-10-02.md`). It covers discovery, OneDrive download, staging, rendering and label preparation for the named projects only.

**Not done:** no provider or model request, prediction, ledger scope, budget or use of the 556 ceiling. No application, candidate, evaluator, label, earlier package or database was changed. No human review is claimed. This entry is appended to the file as found (prefix `afddd562…`).

- **Step 1:** every frozen hash of Review 31 and the earlier packages matched before the cohort was touched.
- **Steps 2 and 3:** all 6 primaries (EP-3563, 22349, 27331, 15744, 26687, 29255) and all 4 alternates passed the metadata verification with the tested Review 31 rules. No replacement was needed, and sealed projects are excluded.
- **Step 4:** the seeded pool of 72 documents (40 review-signal, 20 drawing-signal, 12 other, 12 per project) is frozen as `FROZEN-SELECTION.json` `bf71779a…`. The extension order is frozen in the same file. Long paths are handled; Review 31's walk had skipped them.
- **Steps 5 and 6:** 72 files staged with source hashes and the originals unchanged (`SOURCE-MANIFEST.json` `951e8697…`). There are 149 in-scope page renders and 189 crops, each bound to the staged hash, page, region and recipe. Two byte-identical pairs count once.
- **Steps 7 to 9:**
  - **Conventions:** frozen before labelling (`5c09d4d2…`).
  - **Draft:** `r32-labels-draft-1` (`ebd1e24d…`) is AI-authored and not human-signed. It was drafted from source pages only, with explicit states and association kept separate.
  - **Validation:** mechanical validation found 0 problems.
  - **Projection, not a gate count:** identity 62, revision 39, decision 39 documents present with association resolved, out of 70 distinct.
- **Step 10:** the reviewer packet (432 page-field and 210 document-field rows, 56 questions, response template) is handed to the owner-delegated Codex reviewer. The drafter has stopped.

**Status, stated separately:**
1. Source and project permission and verification: authorized and verified.
2. Label drafting: initial pool done and frozen.
3. Independent label review: PENDING (owner-delegated AI review, not human sign-off).
4. Field population: not counted.
5. Preparation gate: not yet decided.
6. Live run and budget: none.
7. M2: CHANGES STILL REQUIRED. No default selected, and M3 not started.

# Cohort preparation after independent label review (Claude, ORCH-01A/ORCH-02): r32-labels-reviewed-1 and counted populations (2026-10-03)

**Task:** ORCH-02.1, agent R32APPLY-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High. Authority: A-03.

**Package:** `real-project-pilot/fresh-cohort-r32-reviewed/`, indexed by `PREPARATION-REPORT.md`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `64c0366737a5567284c6b862e5addbb0091f7bf98066745f081407a8b3fe31c6`, written last; 45 files.
- **Package check:** `evidence/PACKAGE-CHECK.json` reports ok, 18 of 18 checks.

**Reviewed labels:** `labels/R32-LABELS-REVIEWED-1.json`, version `r32-labels-reviewed-1`, sha256 `00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779`.
- **Derived from:** `r32-labels-draft-1` (`ebd1e24d…a334`).
- **Rulings applied:** the frozen `REVIEWER-RESPONSE.final.json` (`920a21d6…4c5b`), with DISPOSITIONS (`e8828bec…30a7`), CRITIQUE (`ad6798dc…7eef`) and the consolidated response (`70f94632…3ff8`).
- **Method:** applied mechanically, with no re-ruling and no image reading. All 432 page-field, 210 document-field and 56 question rulings were consumed exactly once.
- **Page-field outcome:**
  - identity: 128 accepted, 14 corrected, 2 unresolved;
  - revision: 123 accepted, 20 corrected, 1 unresolved;
  - decision: 131 accepted, 13 corrected.

**This is an owner-delegated independent Claude AI review. It is NOT human sign-off.**

**Counts** (`FIELD-POPULATION.json`, stage "initial pool after independent review", 0 extensions):
- **Rule:** per field, the distinct documents, after count-once, whose review has `resolved_for_scoring` = yes and `carries_fact` = yes.
- **Count-once aliases:** F052→F038 and F070→F067 (byte-identical); F031→F001 and F059→F046 (final convention (c)).
- **Identity: 57. Revision: 38. Decision: 38.**
- **Excluded as unresolved:** identity [F069] (D-004), revision [F019] (D-005), decision [].
- **Upper bound if resolved:** 57 / 39 / 38.
- **Documents:** 72 staged files, 70 with their own rulings, 68 distinct after count-once.
- **Consistency check:** OK.

**Gate action:** **READY FOR INDEPENDENT PREPARATION REVIEW**. This is a mechanical count, not an approval. No extension was drawn.

**Status, stated separately:**
1. Source and project permission and verification: unchanged (authorized and verified in the r32 packet).
2. Label drafting: frozen. `r32-labels-draft-1` is unchanged.
3. Independent label review: done as an owner-delegated independent Claude AI review, not human sign-off. Agents R32REV-B1 to B7, CONSOLIDATE, CRITIC and DISPOSE ran Claude Opus 5.5 at effort High; the orchestrator was Claude Fable 5.1. Of 6 material disagreements, 1 was upheld, 3 adopted and 2 escalated: D-004 (F069 identity) and D-005 (F019 revision).
4. Field population counts: identity 57, revision 38, decision 38, under the count-once rule. Excluded: F069 (identity) and F019 (revision).
5. Preparation gate: READY FOR INDEPENDENT PREPARATION REVIEW.
6. Live-run authorization and budget: none, and nothing was requested. The AI ledger was opened read-only only and still shows 483 entries and 17 scopes.
7. M2: **CHANGES STILL REQUIRED**. M3 not started.

# Cohort preparation after Independent Preparation Review 33: r32-labels-reviewed-2 (2026-10-03)

**Task:** ORCH-04.1, agent R32APPLY2-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High. Authority: A-03.
- This task applied Review 33 conditions C-1 and C-2 mechanically.
- No image was read and no ruling was re-made.
- There was no model or provider request, no prediction, no ledger scope, no OneDrive access and no sealed project.

**Package:** `real-project-pilot/fresh-cohort-r32-reviewed-2/`, indexed by `PREPARATION-REPORT.md`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `1f27a544fa9fb839f5ae9bed721f1e00e7d5cbe1f63f56dd5bbf6fa8086bdb76`. It was written last and lists 43 files; the manifest itself and the package check are the other two.
- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `1b807c404d426a65b3e316087fa85a431088ab19af4fa8dc8c115776da3756e2`, bound by the manifest. It reports ok, 24 of 24 checks.

**Labels:** `labels/R32-LABELS-REVIEWED-2.json`, version `r32-labels-reviewed-2`, sha256 `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6`.
- **Derived from:** `r32-labels-reviewed-1` (`00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779`). Both reviewed-1 and the draft `r32-labels-draft-1` (`ebd1e24d…a334`) are unchanged and copied verbatim.
- **Rulings applied:** Independent Preparation Review 33, verdict **PREPARATION ACCEPTED WITH CONDITIONS**:
  - `INDEPENDENT-REVIEW.md` `8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804`;
  - `ESCALATION-RULINGS.final.json` `e2fe503d96a3bc08c99ce52862d2017a567f6e2a6677744f43750c5ebc7611a0`;
  - `DISPOSITIONS.json` `ceb8fdcc6cc3e54219ab22686fc663a66c93ca5ed44316255ddf24745018315b`.
  The whole Review 33 folder is copied verbatim to `review-33/`.
- **Rows changed** (section 4.4):
  - F069 p1 and p3 identity: present → ambiguous, literal null, candidate EP-15744 under "Refrence" with its role not established on the page, ruled (Review 33, D-004).
  - F069 identity: `resolved_for_scoring` no, `carries_fact` no.
  - F019 p1 revision: stays ambiguous with candidates 00 and 01, excluded, ruled (Review 33, D-005).
  - F019 revision: no / no. The D-005 question and its `unresolved` entry are marked ruled.
  - All six escalations are marked ruled, with both hashes.
- **Also recorded:**
  - Alias annotations: F031→F001 and F059→F046 as the Review 33 (c)(ii) amendment to section 1, with the F031 p3/p4 caveat; F052→F038 and F070→F067 as frozen section 1.
  - The C-2 amendment and interpretation list: (c)(ii), (d1), (e)/D-001, (g)(1), (g2)/D-002, (h)/D-003, (d2), (f) and the D-005 page reading.
  - A 51-entry change log, each entry with provenance "Review 33 <ruling id>".
- **Nothing else changed.** Every other document, page and field is identical to reviewed-1 at field level. The apply function and an independent restatement in the package check both assert this.

**The labels are AI-drafted and AI-reviewed (owner-delegated independent Claude AI review, with the Review 33 rulings applied). They are NOT human-signed and NOT a human review.**

**Counts** (`FIELD-POPULATION.json`, sha256 `799a4b8f97c4560a2906da84f94515711cf9841b3bb3a9529ad6f5cde338539e`; stage "initial pool after independent review and Review 33 rulings"; 0 extensions):
- **Identity: 57. Revision: 38. Decision: 38.**
- **Excluded as unresolved:** none (`{}`).
- **Upper bound:** 57 / 38 / 38.
- **Consistency check:** OK. 138 yes and 72 no document fields agree with the in-scope pages.

**Gate action:** **READY FOR INDEPENDENT PREPARATION REVIEW**. This is a mechanical count, not an approval.

**Tests:** 21 and 7 pytest tests passed (junit in `tests/`).

**Status, stated separately:**
1. **Source permission and verification:** unchanged. A-02 covers access, staging, drafting and preparation only, not provider use. The projects' AI policies are not yet checked (C-9).
2. **Label drafting:** frozen. `r32-labels-draft-1` is unchanged, AI-drafted and not human-signed.
3. **Independent label review:** owner-delegated independent Claude AI review (reviewed-1), with Review 33's D-004, D-005 and (c)(ii) rulings now applied as reviewed-2. It is not human sign-off, and it comes from the same model family as the system under test. The §8 conflict is open for the owner (C-3).
4. **Field populations:** identity 57, revision 38, decision 38, with nothing unresolved.
5. **Preparation gate:**
   - The pool gate is met. The Review 33 verdict is PREPARATION ACCEPTED WITH CONDITIONS.
   - C-1 and C-2 are met by this package as applied. This is subject to the independent re-derivation and the orchestrator's verification, and it is not self-approved.
   - C-3, C-4 and C-9 are owner-only and pending.
   - C-5 to C-8 are pending correction tasks.
6. **Live-run authorization and budget:** none, and nothing was requested. The AI ledger was opened read-only only and still shows 483 entries and 17 scopes.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Correction package review33: r32 harness adapter, per-field scorer, C-4 concentration rule, run-set selector, guarded runner (2026-10-03)

**Task:** ORCH-05.1, agent R33HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High. Authorities: A-03, A-05 and A-08. It answers Review 33 conditions **C-4** (concentration rule, owner decision A-05) and **C-5** (harness adapter). It is a correction package, pending its independent review (ORCH-05R). It is not self-approved.

**Package:** `docs/milestones/M2/real-project-pilot/review33/`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `c5001c95420ac76150f320f04b1edfc5785264d00662d97e8f92ec83c6c95919`. It was written last and lists 112 files.
- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `57453a7aa06d5a347f7221370bcdf03b8f7a45a4a99d6867ffe6e2f35a6f1afd`, ok. The check re-hashed every input and manifest, re-ran 144 tests (0 failures), counted the AI ledger read-only at 483/17, found no frozen file modified after 2026-10-03T10:30:00Z, found no `OWNER-DISPATCH-AUTHORIZATION.json`, and confirmed that the guard refuses.
- **Binding manifest:** `BINDING-MANIFEST-R33.json`, sha256 `d1a8a40100fc05a937ccf40f6fb02a5788bfbea8a74adafcfc68b0f01a53936e`. It binds 68 files: the frozen inputs, the policy `7efa891b…4f47` and its amendment `815d43fd…5de6`, the reviewed-2, packet and review31 manifests, review31's harness as `harness-base`, every `harness-r32` source and test, and the run-set proposal. It also records candidate `a8aacedd` and baseline `3d5607d9`, both clean.

**What was built** (`scripts/harness-r32/`; junit in `tests/`):
- `labels_adapter_r32` (13 tests): per (pool id, page, field) truth, with per-field `resolved_for_scoring` and a NOT_SCORABLE sentinel distinct from None and ABSENT. 32 rows on 32 pages in 25 documents are not scorable. Aliases are canonical. Compilations are keyed by page. It adds project, contractor, stratum, a deterministic layout key and decision type. It reproduces FIELD-POPULATION 57/38/38 with the same ids. Truth `4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064`.
- `literal_compare_r32` (13 tests): whitespace-insensitive; folds dash variants; accepts either-form labelled tails ((g)(1)); compares decisions by class with the application vocabulary and the (d1) tolerance; byte-compares Arabic literals.
- `lane_judge_r32` (7), `score_bcr_r32` (16): the Review 31 rules per field (equal caps 240/240, request gate, 0.98 precision, 0.90 recovery, outcomes, no default), with NOT_SCORABLE excluded and a per-field critical tripwire. Review 31's `score_bcr.py` is untouched, and `SCORER-CHANGES.md` lists 17 differences.
- `concentration_r32` (12 tests) and `CONCENTRATION-RULE-R32.md`, the C-4 replacement:
  - **NOT ELIGIBLE** when: net gain ≥ 4 and more than half of it comes from one project, contractor or layout key; or failures ≥ 2 with more than half in one such group whose own net gain is negative; or decision has any false acceptance on a negative decision control.
  - **UNDETERMINED** (not blocking) below a net gain of 4.
  - Decision type and stratum are reported only.
- `run_set_selector_r32` (8 tests) and `RUN-SET-PROPOSAL.json` (`9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8`): a proposal, frozen only by ORCH-07.
  - It holds 24 documents: 16 decision-bearing, 4 revision top-ups and 4 negative controls.
  - **The unsupported controls are short by 2**: no pool page is labelled unsupported or illegible, and nothing was invented.
  - Projection: identity 23, revision 16, decision 16 (margin 4 for revision and decision).
- `converter_r32` (7 tests) and `LABELS-R32-EVAL-INPUT.json`, in evaluator .10 format. Reconciliation: 432 truth rows = 417 mapped + 15 explicit exclusions (the aliases F031 and F059), each exactly once. The frozen evaluator's truth functions read every converted row as its r32 kind.
- `sandbox_ingest_r32` (5 tests): the 72 staged files were registered PENDING in an isolated sandbox under `C:/t/r2x/r33-sandbox/`, by the baseline tree, without processing. `state_check` is ok.
- `runner_r32` and `lane_r32` (8 tests), `dispatch_guard_r32` (11), `allowance_r32` (5), `tripwire_r32` (5), plus the unchanged copies of `capture_store` (21), `stop_rules` (8) and `state_check` (5).
  - The provider path is reachable only through `dispatch_guard_r32.authorize()`. It refuses unless `OWNER-DISPATCH-AUTHORIZATION.json` exists and names the ORCH-07 declaration hash and an owner budget token. This task did not create that file.
  - Resume contract: a reserved request without an answer is charged and never re-sent.

**Dry run** (`DRY-RUN-REPORT.md`, `dry-run/`):
- **Provider or model calls:** 0. No provider was built.
- **AI ledger:** 483/17 before and 483/17 after. No ledger scope was created.
- **No prediction.** No application reader ran on any cohort document (reader `none`).
- **What ran:**
  - the binding was verified;
  - the guard refused;
  - the run set was ingested and the C/R-from-B state checks passed;
  - capture-store lanes B/C/R/P exchanged synthetic probes with a refusing stub, and R was served C's capture;
  - the resume drill passed with 0 re-sends.
- **The scorer and the concentration rule** were exercised on synthetic results built from the truth, not predictions. ELIGIBLE is reachable for all three fields under the new rule.

**Out of scope (not done here):** evaluator .10 changes and its offline test (ORCH-06), the declaration (ORCH-07), and any dispatch.

**Reference set:** independently AI-reviewed (Claude agents), not human-signed. It is used under AI-ACCURACY-POLICY-AMENDMENT-R32-01, and it is not human Golden Truth.

**Status, stated separately:**
1. **Source permission and verification:** unchanged. A-02 covers access, staging, drafting and preparation. A-06 grants project and provider **eligibility** for the six projects, but not dispatch. Verification stands at 10 of 10, with no replacement.
2. **Label drafting:** `r32-labels-draft-1` is frozen and unchanged. It is AI-drafted and not human-signed.
3. **Independent label review and reference-set status:** the owner-delegated independent Claude AI review, with the Review 33 rulings applied as `r32-labels-reviewed-2` (`89c60e9d…b9a6`). Under amendment R32-01 it is an AI-reviewed reference set: not human-signed, not human Golden Truth.
4. **Field populations:** identity 57, revision 38, decision 38 (reproduced by the adapter), with 0 extensions.
5. **Preparation gate and Review 33 conditions:**
   - The pool gate is met.
   - **C-4 and C-5 are answered by this package, pending the independent review (ORCH-05R).**
   - C-6 is ORCH-06, and C-7 is ORCH-07.
6. **Live-run authorization and budget:** none. No owner dispatch authorization exists. No budget, ledger scope or dispatch. The ledger is untouched at 483/17.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Correction package review34: concentration rule v2, candidate outcome, pinned one-run dispatch guard, per-declaration allowance and resume (2026-10-03)

**Task:** ORCH-05C, agent label R34HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities: A-03, A-05 and A-08. It answers Independent Review 34 (`75061210…bc8f47`, findings `af99a772…f9fd8`, verdict CHANGES REQUIRED): required corrections **RC-1 to RC-6** (R34-01, R34-02, R34-03, R34-04, R34-05, R34-08). It is a correction package pending Independent Review 35 (ORCH-05R2). It is not self-approved.

**Package:** `docs/milestones/M2/real-project-pilot/review34/`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86`. It was written last and lists 124 files.
- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `e96bad2379736b9e18de8ef82e534ef172ea65453f69bdf2a9ffd05e9e84967a`, ok. It re-hashed every input and manifest, re-ran 245 tests in 16 modules (0 failures), counted the AI ledger read-only at 483/17/0, found no frozen file modified after 2026-10-03T12:10:00Z, found no authorization file anywhere, and confirmed the guard's refusals.
- **Binding manifest:** `BINDING-MANIFEST-R34.json`, sha256 `3d0f8bfe37d55a4c0490e054c0d710f4bb1d2ac839dffd08daaafca19063ea27` (118 files). It supersedes review33's `d1a8a401…936e` and binds the frozen inputs, Review 34, the review33 manifest and binding, review31's harness, the review33 harness base, every review34 harness source and test, the carried files and the run set; it records the unchanged, changed and new module tables and candidate `a8aacedd` / baseline `3d5607d9`, both clean.

**Corrections** (`scripts/harness-r32/`; junit in `tests/`; details in `CORRECTION-REPORT.md` §2):
- **RC-1 (R34-01, blocker):** `concentration_r32` version 2, `concentration-r32-2026-10-03.2` (`CONCENTRATION-RULE-R32.md` v2 with a change record): a positive net gain is never ELIGIBLE while more than half of it comes from one project, contractor or layout key, at any size (no net-gain floor); the negative-control and failure legs are kept; UNDETERMINED only for a net gain of 0 or less and never overriding NOT ELIGIBLE; the justification now rests on the scorer's project-stratified bootstrap (which excludes zero for a gain concentrated in one project at net 2 and 3). Tests: Review 34's S3a, S3b (decision +3 on F037, F009, F032 of EP-27331: now NOT ELIGIBLE), S3c (stays NOT ELIGIBLE), a spread control (ELIGIBLE), and monotonicity (`test_concentration_r32` 28 tests).
- **RC-2 (R34-02):** `score_bcr_r32` gives one candidate-level outcome: ELIGIBLE FOR A SEPARATE SELECTION DECISION only when all three fields are ELIGIBLE, otherwise INVALID > NOT ELIGIBLE > INCOMPLETE over the field outcomes; fields stay as diagnostics; no default. S5 (decision recovery 0.7576) gives NOT ELIGIBLE (`test_score_bcr_r32` 28 tests).
- **RC-3 (R34-03):** the authorization path is pinned beside the declaration (no `--auth-path`, a configured `auth_path` is refused); the authorization must carry the declaration hash, the owner token digest the declaration binds (the token is presented at run time and never stored) and a one-run nonce consumed into a run-bound record holding the authorization's own hash; a direct live `lane_r32.py` runs the same preflight and guard. Tests prove: wrong path, missing declaration hash, wrong digest and consumed nonce refused; a direct lane refused without authorization (`test_dispatch_guard_r32` 15, `test_runner_r32` 28). **No authorization file was created.**
- **RC-4 (R34-04):** one allowance (caps 240/240/40/36 and the project-day counter, 60 per project per UTC day across all lanes) and one capture store per declaration, bound to its hash, in one run folder; `runner_r32 run` once, then `runner_r32 resume` (same stamp, never re-sends a bound fingerprint, serves a reserved request as `interrupted_charged`, never fresh caps); the ledger-unchanged assertion is dry-only; live, `LedgerProvider` writes to the declared scope and the runner and lanes verify that scope and its limits before dispatch (no scope created) (`test_allowance_r32` 11, `test_preflight_r32` 43).
- **RC-5 (R34-05):** live lanes verify their switches and provider environment (provider, model aliases, effort, timeouts, CLI path, ledger wrapping) against the declaration, in the environment and the application's settings; no silent defaults in live mode; dry defaults labelled.
- **RC-6 (R34-08):** a wrong acceptance is exactly one failure (failures once per document and field).
- **Carried unchanged by hash:** the adapter, literal comparison, converter, selector, sandbox ingestion and the review31 copies (capture store, state check, stop rules); `TRUTH-R32` `4e237a4e…e064`, `RUN-SET-PROPOSAL` `9058f3d6…7ce8`, `LABELS-R32-EVAL-INPUT` `4b2c73d5…5cc`, `CONVERTER-RECONCILIATION` `e350d2fe…24f3`.

**Dry run** (`DRY-RUN-REPORT.md`, `dry-run/`):
- **Provider or model calls:** 0. **AI ledger:** 483/17 before and 483/17 after; no scope created. No prediction (reader `none`).
- **Two-invocation drill:** a fresh run interrupted by a crash right after a send; a second fresh run refused; a same-stamp resume that re-sent nothing, served the reserved request once as `interrupted_charged`, kept the caps and completed; then resume and run refused (15 of 15 checks true).
- **Scorer scenarios** (synthetic lanes made from the truth, not results): S3b and S5 give the candidate NOT ELIGIBLE; the spread control gives ELIGIBLE; EP-27331 decision gains of 1 to 6 documents are all NOT ELIGIBLE.

**Out of scope (not done here):** evaluator .10 changes and its offline test (ORCH-06, ORCH-06V), the declaration and budget (ORCH-07), any owner authorization, ledger scope or dispatch.

**Reference set:** independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.

**Status, stated separately:**
1. **Source permission and verification:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider **eligibility** for the six projects, not dispatch. Verification stands at 10 of 10, with no replacement.
2. **Label drafting:** `r32-labels-draft-1` is frozen and unchanged; AI-drafted and not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) under amendment R32-01: independently AI-reviewed, not human-signed.
4. **Field populations:** identity 57, revision 38, decision 38; 0 extensions.
5. **Review 33 / Review 34 conditions:** C-4 and C-5 are answered again here and RC-1 to RC-6 are implemented and tested, all pending Review 35; C-6 is ORCH-06, C-7 is ORCH-07, C-8 is carried into the declaration.
6. **Live-run authorization and budget:** none. No `OWNER-DISPATCH-AUTHORIZATION.json` exists anywhere; no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Offline evaluator .10 parity test against the r32 reference set (ORCH-06, 2026-10-03)

**Task:** ORCH-06 (Review 33 condition C-6, finding D4-06; Review 35 section 6 items 1 and 10), agent label R35EVAL-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03 and A-08. The only write-capable agent. It is an implementation test package pending the independent read-only verification ORCH-06V. It is not self-approved.

**Package:** `docs/milestones/M2/real-project-pilot/evaluator-offline-r32/`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7`, written last, 25 files.
- **Package check:** `evidence/PACKAGE-CHECK.json` ok, 16 of 16 checks: every frozen input re-hashed equal; candidate `a8aacedd` clean and no candidate file modified after the task start; no frozen file modified after 2026-10-03T13:50:00Z (the running application's own `ep_platform.db` files reported apart); 16 tests, 0 failures, 0 errors; AI ledger 483/17 read-only; no provider code path executed; no authorization file created by this task.
- **Binding manifest:** `BINDING-MANIFEST-R35.json`, sha256 `1de0773a23a38b39ffad770cf23d9d61d7e7ca1187693bbc29dbaccbcbbd62cb`: candidate HEAD and status, evaluator .10 `m2_eval6.py` `268d86231260392dc5592a6937803b8fcd15a41e9590b442f3f0a70dc57b4b4f` and every candidate module it imported, the review34 inputs and harness modules, the reference set and conventions, Reviews 33-35, and the fixtures `SYNTHETIC-PREDICTIONS.json` `9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774`.

**What was tested:** 4805 SYNTHETIC fixtures built from `TRUTH-R32.json` and `LABELS-R32-EVAL-INPUT.json` only (every one of the 417 canonical truth rows covered; whitespace, dash, leading-zero, (g)(1) tail, suffix-base, Arabic, decision-vocabulary and (d1) variants; wrong-value controls; ABSENT and NOT_SCORABLE rows; page-keyed compilations F002 / F035 / F043; cross-page identity in drawing sets F014 / F016 / F038 and cover packages), each fed to evaluator .10 offline through two channels (register record, validated AI evidence) exactly as `score_lane.py` calls it (`EV.evaluate(register, page, rows, corrections, ai_context)`, `layers.evidence`): **9610 cases**, each compared with the frozen harness verdict (`lane_judge_r32` / `literal_compare_r32`) on the same pair.

**Results** (evaluator against the harness on the pair):
- All cases: parity 6301; (a) stricter-critical 2124; (a) stricter-recovery 549; (b) looser-accepts-wrong 86; (b) looser-hides-wrong 308; (c) NOT_SCORABLE excluded by both 242; side-row recovery credits 270.
- Values the application can emit (7676 cases): parity 5898; (a) critical 1448; (a) recovery 0; (b) accepts-wrong 86; (b) hides-wrong 32; (c) 212. By field: identity: a-critical 978, a-recovery 0, b-accepts-wrong 0, b-hides-wrong 32; revision: a-critical 456, a-recovery 0, b-accepts-wrong 86, b-hides-wrong 0; decision: a-critical 14, a-recovery 0, b-accepts-wrong 0, b-hides-wrong 0.
- Against the facts .10's own emission extracts (`harness_wired`): {"a_stricter_critical": 2124, "b_looser_accepts_wrong": 86, "b_looser_hides_wrong": 32, "c_not_scorable_excluded": 242, "parity": 7126}.
- By rule: H1 74 cases (74 reachable); R1 880 cases (880 reachable); R2 420 cases (420 reachable); R2b 48 cases (48 reachable); R3 72 cases (72 reachable); R3b 26 cases (26 reachable); R4 14 cases (14 reachable); R5 32 cases (32 reachable, 44 side rows); R6 0 cases (0 reachable, 226 side rows); R7 1501 cases (0 reachable).
- (c) NOT_SCORABLE: 242 of 242 cases on 32 rows excluded by .10; 0 read as absent; 0 scored.
- **Main divergences.** (a) critical: identity dash glyphs not folded (R1), revision 'Rev. 01' / 'REV 01' read by first token (R2), F043 truth 'Rev. 0' normalised to 'REV.' (R2b), (g)(1) tail form (R3), the application's `rejected` on (d1) rows (R4). (b): any 'Rev. <n>' accepted on F043 p2-p4 (R2b), another page's identity on a compilation page associated cross-page and never flagged (R5), cross-page copies credited to the other page (R6). Decision text other than approved / ANN / rejected (R7) is never emitted by the application.
- **Normaliser question:** a blind normaliser (N1) leaves (g)(1), (d1), compilation and cross-page divergences; a truth-aware one (N2, with compilation split) leaves only two harness departures from the conventions; neither made .10 accept a wrong-value control the harness rejects (N1 0, N2 0; without a normaliser 12). Analysis only; not recommended over binding the frozen judge.

**Recommendation for ORCH-07:** bind evaluator .10 **as is in its emission role only** (`record_groups`, `observation_groups`, `ai_groups` through `tripwire_r32.facts_from_row`, as the frozen review34 `score_lane_r32` already does), with every verdict, metric, tripwire and gate from `lane_judge_r32` + `literal_compare_r32`; do **not** bind .10's own judging. No candidate correction is needed for that binding. If ORCH-07 wants .10's judging to produce any verdict, a candidate correction (new commit, own independent review) is required before any live run, changing R1 (dash folding in `norm_ref` / `same_identity`), R2 / R2b (`norm_rev` whole-value parse), R3 ((g)(1) alternates), R4 ((d1) alternative decision), R5 (no cross-page association in compilations) and R6 (no cross-page recovery credit, or declare it); R7 optional. List the interpretations of Review 35 item 10 and disclose the harness departures H1-H5 (`EVALUATOR-TEST-REPORT.md` sections 7 and 10).

**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; the provider classes were stubbed to raise and none was constructed; no real prediction exists or was created; the AI ledger was opened read-only only and reads 483 entries / 17 scopes before and after; no ledger scope; no OneDrive; no sealed project; no authorization file created (the 35 files named `OWNER-DISPATCH-AUTHORIZATION.json` found in the session scratchpad are pytest temporaries of earlier harness tasks, all older than this task). The candidate `C:/t/iso/cand-r29` was never written (`git status --porcelain` empty before and after).

**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.

**Status, stated separately:**
1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.
2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents) and not human-signed.
4. **Field populations:** identity 57, revision 38, decision 38.
5. **Conditions:** C-6 answered by this package, **pending ORCH-06V**; C-7 is ORCH-07; C-8 is carried into the declaration.
6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Correction package review36: H1 whitespace fix in literal_compare_r32.norm_revision (2026-10-03)

**Task:** ORCH-06C, agent label R36HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03 and A-08. The only write-capable agent. It answers Independent Verification 36 (`f698c2ff…3a00`), finding **R36-08** (major, CONFIRMED: H1 is a harness defect), condition 1 for ORCH-07. It is a correction package pending the independent read-only check ORCH-06CV (Verification 37). It is not self-approved.

**Package:** `docs/milestones/M2/real-project-pilot/review36/`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0`, written last, 135 files.
- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `2d53bc24b05b3b0c55096031dff1fc2e74376b4b9afcc9e791c3d78b02c56331`, ok: frozen inputs re-hashed (PACKET OK); only one module differs from review34; the suite re-run passes; AI ledger 483/17/0 read-only; no frozen file modified after 2026-10-03T15:30:00Z and every frozen tree digest equal to the task-start snapshot; no authorization file.
- **Binding manifest:** `BINDING-MANIFEST-R36.json`, sha256 `5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568`: every harness file (work copy, package copy, review34 base), the review34 manifest and binding, the evaluator-offline-r32 manifest, binding, fixtures and matrix, Verification 36, and the review34 inputs / carried files / run set carried unchanged; it passes the runner's own `preflight_r32.verify_binding`.

**The change (exactly one function):** `literal_compare_r32.py` `norm_revision` only. After the unchanged Arabic branch, dash folding, upper-casing and the optional REVISION / REV / REV. / R / R. prefix (same alternatives, same order), every whitespace character is removed before the number pattern `0*(\d+)` is matched; the non-numeric fallback, leading-zero handling and the module docstring are unchanged; a function docstring was added. `0 1` and `REV 0 1` and `R 01` -> `R1`, `0 0` -> `R0`, `Rev. 0 2` -> `R2`.
- `literal_compare_r32.py`: review34 `ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6` -> r36 `c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09`.
- `test_literal_compare_r32.py`: review34 `1d91cb5443ac5258b3fc60268b80a2815517badb5ebf5c77a3d0bf6b62831e4e` -> r36 `66e0ddcf92ae4aaf350ca1143ad4f22f62ab777e12700c978652b276fdbb34c6` (35 tests appended; the review34 file is an exact byte prefix). The other 38 harness files are byte-identical to review34.

**Effect (H1-WHATIF-RESULT.json):**
- Row level: 42,804 row judgements per state (Verification 36's population); exactly **53** change on `accepted` and **53** on `validated`: the 53 `ws_inside_number` truth rows, each `wrong_only` + 1 critical -> `recovered_clean` (kind `normalised`), 0 side rows.
- Parity run re-executed (harness side with the fixed harness, evaluator side re-run read-only): 9,610 cases; exactly **106** change (the 53 rows x 2 channels; 23 rows in the run set), critical -> correct on both the pair and the wired facts; evaluator side identical; class changes: b_looser_accepts_wrong -> parity 74; parity -> a_stricter_critical 32.
- **Wrong-value controls:** 1,636 fixtures / 3,272 cases, **0 verdicts changed, 0 newly accepted**. (Before and after, the frozen harness accepts 13 decision controls by its H2 vocabulary, `Code D - Rejected`: 26 pair cases and 13 wired cases; the fix touches no decision comparison.)
- **NOT_SCORABLE:** 32 rows / 242 cases, all excluded by the harness before and after; 0 read as absent.
- Verification 36's what-if numbers are reproduced exactly (42,804 rows, 53 changed, 0 wrong controls newly accepted; 106 cases, 74 where .10 accepts and 32 where both were critical; 23 rows in the run set).

**Tests:** the whole review34 suite from the copy, 16 modules, **280 tests (245 review34 + 35 new), 0 failures, 0 errors**. Disclosure: the review34 suite hard-codes the sandbox base `C:/t/r2x/r34-sandbox`, so the whole-suite run uses a test-run twin of the bound copy that differs only by that string -> `C:/t/r2x/r36-sandbox` (15 occurrences in 8 files; verified byte for byte); the 14 sandbox-free modules also ran from the bound copy itself (247 tests, 0 failures). The new H1 tests fail on the review34 module (16 of 48) and pass on the r36 module.

**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; the parity run's guard constructed no provider and blocked no attempt; no prediction exists or was created (the values are the frozen SYNTHETIC fixtures); the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 amendments before and after; no ledger scope; no OneDrive; no sealed project; no authorization file created; review34, evaluator-offline-r32, the cohort packages, staging, the candidate and the baseline were not written (digests unchanged).

**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.

**Status, stated separately:**
1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.
2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents), not human-signed.
4. **Field populations:** identity 57, revision 38, decision 38.
5. **Conditions:** R36-08 answered by this package, **pending ORCH-06CV**; the other ORCH-07 conditions of Verification 36 (R36-07, R36-09, the disclosures) are carried into the declaration.
6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Fresh-validation declaration R32 and budget decision card v3 (ORCH-07, 2026-10-03): frozen, NOT authorized, NO dispatch

**Task:** ORCH-07 (orchestrator ledger ORCH-016), agent label R37DECL-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03, A-06 and A-08. The only write-capable agent. It produces the frozen declaration the owner can authorize by hash, the budget decision card v3 and a dry preflight. It authorizes nothing and does not self-approve; ORCH-07V (independent verification) is next.

**Package:** `docs/milestones/M2/real-project-pilot/declaration-r32/`.
- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `59361b9331cf3d28979129dfa1749b10f345e5ad24f26b9691012423fd1be2c8`, written last, 56 files.
- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `8afde9ab3018a399f2b758f27fff31f6baa6412beedffd422b0d6a0ee858dfb4`, ok: frozen inputs re-hashed (PACKET OK); the declaration hash equals `DECLARATION.sha256`; no authorization file; no token; AI ledger 483/17/0 read-only; no frozen file modified after 2026-10-03T16:55:00Z (and none after the task start); frozen trees equal before and after; candidate and baseline clean; tests 34 passed, 0 failures, 0 errors (re-run equal).
- **Declaration:** `FRESH-VALIDATION-DECLARATION-R32.json`, sha256 **`38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0`**, written once; `executed: false`, `budget_approved: false`, authorization "none; owner decision pending"; `authorization.owner_token_sha256` is the explicit placeholder `TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION`, which the preflight refuses until the owner names the token digest; the runnable declaration is this file with only that value replaced.

**A-08 items in brief:**
- **Arms:** B = baseline `3d5607d`, `AI_EVIDENCE_VARIANT=off`; C = candidate `a8aaced`, L3 set (EV1, GUARD, SUPPORT v2, SCHEDULING required_first, DEADLINE, TARGETED) + IG/CA/DR/PA (IDGUARD, ADJUDICATE, DECISION_REGION, ASSOC); R = candidate, L3 set, served C's capture, reference-only requests; P = `{}`, seeded 15 % probe of C's answered dispatches. Dispatch order: B, the C-from-B state check, C, R, P, offline scoring.
- **Run set:** `9058f3d6…7ce8`, 24 documents (16 decision-bearing, 4 revision top-ups, 4 negative controls); matched projection identity 23 / revision 16 / decision 16 (minimum 12); decision controls 16 positive / 8 negative; unsupported controls short by 2 (plan v2 section 2.3 deviation, no substitute).
- **Caps:** B 240 = C 240, R 40, P 36 (556). **Token thresholds:** 90,000 / 20,000 per request (estimates, breakers); lanes B 7.0M/1.4M = C, R 1.2M/0.24M, P 1.1M/0.22M, enforced only as one scope's totals 16.3M / 3.26M (R35-10). **Elapsed:** B 72 h, C 72 h, R and P 24 h; enforced only as the scope's 604,800 s from its creation.
- **Estimated usage:** planning B 6, C 112, R 10, P 17 = 145 requests (conservative 277); about 1.71M input / 0.26M output tokens; EP-27331 (6 documents, 23 pages) B + C 52 planning / 54 maximum, all lanes 63 planning against the project-day limit **60** (R and P may be refused for EP-27331; refusals are permanent for the run, R35-09).
- **Cost:** unknown, never zero (claude-code on the owner's subscription; no price configured). **Owner-confirmable:** `AI_MODEL_SMALL` `sonnet`, `AI_MODEL_STANDARD` `opus` (the four-arm aliases; the AI ledger recorded claude-sonnet-5 457 and claude-opus-5 5), `AI_EFFORT` `low` (not sent by the CLI adapter), project-day limit 60, scope `m2-fresh-validation-r32-2026-10-03`; tree defaults are claude-fable-5-1 / claude-fable-5-1 / low.
- **Stop rules:** verbatim from STOP-AND-SAFETY-RULES and the review34 resume rules (resolved-truth critical in B -> INVALID, in C -> RESULT, in R/P a finding; three provider failures; budget stops never raised; resume never undoes a budget or provider-failure stop and is refused after a terminal comparison).
- **Concentration on the proposal:** ELIGIBLE reachable in every field (smallest net gain 2); a net gain of 1, or any gain confined to one project or layout (EP-27331 / EMAAR: 6 of 16 decision documents), is never ELIGIBLE; frozen code equals the oracle on 1,084 gain sets (0 mismatches).

**Preflight (dry, `dry-run/`):** `validate_declaration` on the file as written REFUSED ("the declaration binds no owner token digest", by design); on an in-memory copy with a syntactically valid dummy digest (never written) PASSED; `verify_binding` on `BINDING-MANIFEST-R36` PASSED (155 files); `runner_r32 run --mode live` from the bound copy without authorization and without a token REFUSED before creating any folder; in-process with the dummy-digest copy it REFUSED at the ledger-scope check (no scope exists); the guard refused (no authorization file). Dry exercise from a test twin (sandbox base C:/t/r2x/r37-sandbox) with the declaration's switches and the refusing stub: every lane verified its switches equal the declaration, 0 model requests, reader 'none'.

**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; no prediction; no ledger scope; no token generated; no `OWNER-DISPATCH-AUTHORIZATION.json` or similar file created; the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 amendments before and after; no OneDrive; no sealed project. Disclosure: one local `claude --version` (no -p, no model request).

**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.

**Status, stated separately:**
1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.
2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents), not human-signed.
4. **Field populations:** identity 57, revision 38, decision 38.
5. **Conditions:** C-7 answered by this declaration, **pending ORCH-07V**; C-8 carried into the declaration's disclosures; R37-04 stated as the exact revision rule (exposure 0, residual risk named).
6. **Live-run authorization and budget:** none. Declaration `38e08df9…` is frozen and NOT authorized; no authorization file, no token, no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Correction package review38: A-09 harness correction (deferral and visible INCOMPLETE, compatible limits, pinned model identity, lane allowances, evidenced cross-page identity, R/P no credit) (2026-10-03)

- **Task:** ORCH-08 (orchestrator ledger ORCH-019), agent R38HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03, A-06, A-09. Work 2026-10-03 18:20Z to about 19:40Z (interrupted by the account usage limit) and 2026-10-04 from 07:39:51Z.
- **Package:** `PILOT/review38/`; `evidence/EVIDENCE-MANIFEST.json` sha256 **`07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9`** (128 files); `BINDING-MANIFEST-R38.json` `4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d`; `evidence/PACKAGE-CHECK.json` `f4671546e1551578e19268d563d114300ef376c9c54734986c1e6cfbb4f877fb` (all checks ok).
- **Nature:** a correction package, pending ORCH-08V (Verification 39). Not self-approved; it authorizes nothing. The corrected declaration is ORCH-09's.
- **Tests:** 392 tests in 20 modules, 0 failures, 0 errors, 0 write-guard refusals; junit in `tests/`; the whole suite runs from the harness itself (the sandbox base is declared / parameterised, default `C:/t/r2x/r38-sandbox`; no test twin).

**Changes (A-09 point; finding):**
1. **Request bounds and compatible limits** (point 1; R38-08): new `project_bounds_r32.py`, `PROJECT-REQUEST-BOUNDS.json` (`a90ecd1b3fec1fc82ad9668a5ad90ba317558760566653cbe178650df84cf82a`); EP-27331 planning 63.0 (B 6, C 46, R 4.1, P 6.9), structural maximum 154 (B 6, C 72, R 40, P 36); the harness rolling window (<= 60 per 86,400 s, all lanes) governs; `validate_declaration` refuses `AI_MAX_CALLS_PER_PROJECT_PER_DAY` / `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` below 84 (the largest row count of one lane database: EP-27331 12 + 72) and per-document limits other than 12 / 120 s; the live preflight recomputes the bounds file.
2. **Visible refusals and rolling-window deferral** (point 1; R35-09, R38-08): every refusal (lane allowance, parent ceiling / tokens / elapsed, window, breaker, ledger, guard, identity, terminal stop, the application's own limits) is recorded per document and page in the lane rows, the run report, the scorer and the audit view; a window refusal is never charged: the document is DEFERRED with its earliest retry, a resume dispatches it once the window frees (never a bound fingerprint again), a deferral that cannot finish within the elapsed bound ends INCOMPLETE (or the run is CLOSED); B/C limit-affected documents make the comparison INCOMPLETE and stay in every denominator; silent skipping fails the tests.
3. **Model identity** (point 2; R38-10): full ids pinned, `claude-sonnet-5` (small) / `claude-opus-5` (standard), aliases refused; `claude --version` and the provider identity recorded per invocation (held equal across the run); every response checked; a mismatch records the offending request in `IDENTITY-INVALID.json`, makes the run INVALID and refuses the next request and every resume.
4. **Parent budget and lane allowances** (point 3; R35-10, R38-13): one immutable parent (556; token and elapsed bounds) with lane allowances B 240 / C 240 / R 40 / P 36; no borrowing; failed, timed-out, interrupted and dispatched-but-unsaved requests stay charged; durable stops and refusals survive resume; `ALLOWANCE-AUDIT.json` / `allowance_r32.py audit` list every charge with lane, document, outcome and ledger entry, reconciled with the single ledger scope (its limits must equal the parent's).
5. **Cross-page identity** (point 4; R34-06, R36-09): rule CP-R38 (source, document identity, target and the labels' recorded page relationship R1 / R2 / R3; never the file alone; conflicting identity earns no credit). `CROSS-PAGE-WHATIF.json` (`491f9590e775fa5367569787cbc3394d8db1b82908f5f6111a2a7491da8c6fe6`): 356 target verdicts change on 89 fixtures (pair 178, wired 178), all to critical_false_acceptance; 40 fixtures keep an evidenced association ({'R1': 30, 'R2': 24, 'R3': 26}); the r36 copy reproduces the frozen matrix except exactly the 106 H1 cases.
6. **Unsupported-control shortfall** (point 5): a declared scope limitation in every scorer result (no argument removes it), `REPORT-TEMPLATE.md` states that unsupported-format safety and generalization are not claimed; the selector refuses any replacement once a prediction exists for the run.
7. **R and P** (point 6; R38-09): no accuracy or recovery credit anywhere; the decision coverage gate is C >= B only (the C >= R leg becomes a reported diagnostic: stated as a consequence); the candidate outcome reads only B and C; a truncated R or P is an INCOMPLETE diagnostic; tests prove a full, a truncated and no R give the identical candidate outcome.
8. **Visibility proof** (point 7): `VISIBILITY-REPORT.md` / `VISIBILITY-RESULT.json`, 12 dry scenarios with the refusing stub (records found in run state / lane rows / scorer / audit): application_path (3/3/10/3), application_project_limit (4/4/11/4), bound_passed_while_deferred (8/1/1/1), breaker (1/1/7/3), deferral_beyond_bound (3/3/9/6), identity_mismatch (1/1/8/2), interrupted (2/2/6/1), lane_allowance (2/2/14/5), ledger (2/2/8/3), project_window (16/4/8/12), provider_timeout (12/12/26/10), unsaved (2/2/6/1). Every injected event visible in every place: True; no bound fingerprint re-sent: True.
9. **Carried unchanged by hash:** the adapter, literal comparison (H1 fix), converter, sandbox ingestion, concentration rule v2, the review31 / v4 copies (capture store, coverage, state check, stop rules), the dispatch guard and their tests; the selector's selection code is byte-identical (only the replacement refusal appended). Records: CHANGE-RECORD.md, SCORER-CHANGES.md v3, LIVE-RUN-CONTRACT.md v3, BINDING-MANIFEST-R38.json, COMMANDS.md, COMMANDS-AND-AUDIT-LOG.md.

**Dry exercise:** 0 provider calls; AI ledger (mode=ro) before 483 / 17, after 483 / 17.

**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; no prediction (SYNTHETIC fixtures, refusing stubs and SYNTHETIC EP-990001 documents only); no ledger scope, token, authorization file, run file or declaration created; the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 amendments before and after; no OneDrive; no sealed project. Disclosure: one local `claude --version` (2026-10-03T18:38:42Z, `2.1.263 (Claude Code)`; no -p, no model request).

**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).

**Status, stated separately:**
1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.
2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents), not human-signed.
4. **Field populations:** identity 57, revision 38, decision 38.
5. **Conditions:** the A-09 harness points are answered by this package, **pending Verification 39 (ORCH-08V)**; the corrected declaration is **pending ORCH-09**.
6. **Live-run authorization and budget:** none. The declaration `38e08df9…` stays superseded and NOT authorized; no new declaration, authorization file, token, budget, ledger scope or dispatch exists.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.

# Correction package review39: harness correction after Verification 39 (drawings-AI path disabled and gated, unread pages, retry_at_full and resume policy, failed reads retried, decision coverage gate C >= B only per owner ruling A-10) (2026-10-04)

- **Task:** ORCH-08C (orchestrator ledger ORCH-021; owner decision A-10 relayed during the task), agent R39HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03, A-06, A-09, A-10. Work 2026-10-04 from 09:00Z.
- **Package:** `PILOT/review39/`; `evidence/EVIDENCE-MANIFEST.json` sha256 **`2430fa2bf6bcb5bf3775efe143575dcd9cdc55723ab994cfaec5f63fbdded990`** (147 files); `BINDING-MANIFEST-R39.json` `a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b` (binds review38 `07c2fb78…8ce9` / `4c2904cd…f314d` and review36 `5e950813…9de9d0` / `5a1a6aad…e568`); `evidence/PACKAGE-CHECK.json` `fad730b9403db6e8ea995a47a9a6b2727c0316db982f5a0b10d05279cfb05cf1` (all checks ok).
- **Nature:** a correction package, pending Verification 40. Not self-approved; it authorizes nothing. The corrected declaration is ORCH-09's.
- **Harness vs review38:** 29 files unchanged (byte-identical), 21 changed, 6 new, 0 removed (`evidence/HARNESS-FILES-R38-R39.json`, every file with its review38 and review39 hash; changed tests listed as changed).
- **Tests:** 466 tests in 22 modules, 0 failures, 0 errors, 0 write-guard refusals; junit in `tests/`.

**Changes (finding; A-09 point):**
1. **Undeclared request paths** (R39-04 major; A-09 points 1 and 3): `REQUEST-PATHS.md` enumerates every provider-call site each lane reaches (static over-approximation plus hand reading); the only reachable undeclared path is the baseline drawings-AI review (`document_processing.run` -> `shop_drawings.reconcile` -> `drawing_ai_review`, up to 10 per project per B invocation). Declaration contract 4 binds `application_env` = exactly `{"DRAWINGS_AI_REVIEW_ENABLED": "false"}` (refused otherwise); `sandbox_env` sets it; every lane (live and dry, every invocation and resume) verifies it in the environment, the application's settings and `drawing_ai_review.enabled()`. The gate refuses a task kind not declared for the lane (`lane_task_kinds`) or a request without the current document's context (the lane clears it after each document) as a contract breach: recorded, never charged, the run INVALID, never a failure-streak count. 1(d): drawings-AI outputs feed no measured field in either tree (code reading and the `feed` probe: the answer is applied to the shop-drawing records, every scored project_documents column unchanged).
2. **Unread pages** (R39-06; A-09 point 1): harness and resource refusals make a document INCOMPLETE; the reader's own cap, the JobBudget and a reader exception leave it COMPLETE with every unread page recorded per page (lane rows, run report, scorer, audit) and counted as unread in every denominator. Verification 39's scenarios A (4 + 4), B (7 + 5) and C (exception) are tests. The review38 claim "the reader's 8 is recorded per page" was wrong (corrected in CHANGE-RECORD-R39.md; review38's record stays frozen).
3. **Retry policy** (R39-08): every DEFERRED record carries `retry_at_earliest` and `retry_at_full` (planning / structural); the declaration's `resume_policy` (`full` default, `earliest` allowed) is enforced (an early resume is refused and creates nothing). EP-27331 invocations: planning demand full 2 / earliest 2-4; structural demand full 3 / earliest 3-101; every resume needs its own owner authorization.
4. **Failed reads and the capture store** (R39-16): the store serves bound answers only; a fingerprint whose dispatches all failed is dispatched again on the application's own retry path (charged, never refunded, recorded as a retry with its ordinal), identically for B and C; interrupted dispatches are still never re-sent; R is still served C's capture by content key; P's sample is frozen at its first run. Accuracy implication stated in LIVE-RUN-CONTRACT.md section 13. Consequence for the bounds: B is now 2 per document per invocation, so EP-27331 is planning 63.0 / structural 160 (not the expected 154: +6 for B's retry), 3 windows; with the drawings-AI path enabled it would be 170 (164 on review38's model, Verification 39's 164); required application minimum 84 unchanged.
5. **Decision coverage gate** (R39-15; owner ruling A-10): eligibility is C >= B only. **This is a change from plan v2** (whose gate was C >= B and C >= R), ruled by the owner on 2026-10-04 -- not an unchanged gate. C >= R is a MANDATORY diagnostic in every scorer result and report (counts, missing coverage per document, reasons; INCOMPLETE when R is truncated); the scorer and the declaration contract refuse any definition that binds R into eligibility. Every other safety, accuracy and completeness gate is unchanged.
6. **Model identity** (R39-09): `MODEL-ID-EVIDENCE.md` from a read-only byte search of the installed CLI (2.1.263, sha256 `0b35df94…5b03`; never executed): both pinned ids are in its catalog and a full id passes `--model` unchanged; `--output-format json` reports the REQUESTED model as the `modelUsage` key (no dated id); only `stream-json`'s `message.model` exposes the server's statement. Served-model identity: **UNRESOLVED** offline; the owner's probe command, expected evidence and interpretation are given (not run). The runtime check stays fail-closed for any verifiable mismatch (limits stated).
7. **Records** (R39-02, R39-17): the binding manifest of review38 is `4c2904cd…398bcf7fee…f314d` (bound by hash here). Correction of the review38 response entry: its carried modules were unchanged by hash, but **two of their tests had changed** (`test_literal_compare_r32.py`: one judge-level expectation for the 25 formerly forgiven controls; `test_sandbox_ingest_r32.py`: a path-only change); and its "R1 30, R2 24, R3 26" were **case counts** -- the 40 kept fixtures are **R1 15, R2 12, R3 13**. The static request-path step failed twice before succeeding (a shell heredoc parse error, then a missing output folder); explained in REQUEST-PATHS.md section 3 and the audit log.
8. **Visibility:** `VISIBILITY-REPORT.md` re-run over the r39 harness, 17 dry scenarios (12 of review38 plus undeclared task kind, missing context, unread pages, the full resume policy, the failed-read retry); every event visible in every place it can reach: True; contract breaches only where injected: True; model requests 0.

**Zero calls:** no provider or model request of any kind, no `claude` invocation in any form, no network; no prediction; no ledger scope, token, authorization file, run file or declaration created; the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 amendments before and after.

**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).

**Status, stated separately:**
1. **Correction readiness:** Verification 39's R39-04, R39-06, R39-08, R39-16, R39-15 (with A-10), R39-09, R39-02 and R39-17 are answered by this package, **pending Verification 40**; the corrected declaration is **pending ORCH-09** (needs Verification 40 and the owner's model-identity probe outcome or acceptance of UNRESOLVED identity).
2. **Accuracy:** none. No prediction exists; every figure is from SYNTHETIC fixtures, dry stubs or models.
3. **Label truth:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) independently AI-reviewed (Claude agents), not human-signed; populations identity 57, revision 38, decision 38.
4. **Permissions and budget:** eligibility only (A-06). No declaration, authorization file, token, budget, ledger scope or dispatch exists.
5. **M2:** **CHANGES STILL REQUIRED.**
6. **M3:** not started.

# Corrected fresh-validation declaration R32 v2, runbook and scope-creation command (ORCH-09, 2026-10-04): frozen, NOT authorized, NO dispatch

- **Task:** ORCH-09 (orchestrator ledger ORCH-024), agent R40DECL-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03, A-06, A-08, A-09, A-10. Work 2026-10-04 from 11:21Z.
- **Package:** `PILOT/declaration-r32-v2/`; `evidence/EVIDENCE-MANIFEST.json` sha256 **`6fa552ebd7561ed519e58a95c45ea6e2427cb0b13c94dc3739df4e868e0b6bfb`** (240 files); `evidence/PACKAGE-CHECK.json` `b2e8022b7b10f1762ff09ecdfde4d63f56bb5ad9a2bb4f1065939f3de7cef8a3` (all checks ok).
- **Declaration:** `FRESH-VALIDATION-DECLARATION-R32-V2.json` sha256 **`f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af`** (= `DECLARATION.sha256`), contract `r39-live-contract-4`, bound to review39 (`BINDING-MANIFEST-R39` `a6f703b4…567b`, manifest `2430fa2b…d990`). The owner-token digest is an explicit placeholder (exactly once); the preflight and the guard refuse the file as written; an in-memory copy with a dummy digest passes contract 4 (never written). It supersedes `38e08df9…76b0` (A-09: never authorized, never run).
- **Differences from the superseded declaration** (`DECLARATION-DIFF.md`): 31 top-level keys changed, 27 added, 4 removed (caps, caps_detail, project_day_limit, project_day_limit_detail: replaced by contract 4's budget and project_window), 17 unchanged.
- **Values:** parent budget 556 / 16,300,000 / 3,260,000 / 604,800 s; lane allowances B 240, C 240, R 40, P 36; project window 60 per 86,400 s (all lanes); `resume_policy` `full`; `application_env` `{"DRAWINGS_AI_REVIEW_ENABLED": "false"}`; task kinds per lane from the switches; models `claude-sonnet-5` / `claude-opus-5`, provider `claude-code`, CLI line `2.1.263 (Claude Code)`; compatible limits as integer strings `AI_MAX_CALLS_PER_PROJECT_PER_DAY` "96" (required 84, margin 12 = one document's JobBudget), `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` "600", `AI_MAX_CALLS_PER_DOCUMENT` "12", `AI_MAX_ELAPSED_S_PER_JOB` "120"; ledger scope `m2-fresh-validation-r32-v2-2026-10-04` (limits = the parent; does not exist); run folder `C:/t/r2x/r40-sandbox/r32-v2` (short: the longest application path is 255 characters).
- **The decision coverage gate is C >= B only: a change from plan v2** (owner ruling A-10; not an unchanged gate); C >= R a mandatory diagnostic.
- **Verification 40 items:** R40-04 (the claim corrected: the gate's belt and braces holds for lane B only; C/R/P rest on two static analyses and a dynamic run with get_provider() raising, 0 calls, bound by hash; residual risk stated; two owner options); R40-13 (the failed-read retry named a change from plan v2 section 4; review39 contract v4 sections 4, 5, 6, 13 carried verbatim, replacing review34's resume rules); R40-16 (the amended probe in RUNBOOK section 1; no 'exactly one request' claim); R40-08 (integer strings; the R39-18 risk and its handling); R40-10 (the no_trigger exclusion and two unguarded corners); R40-12 (P's population drawn at its first run, cap 36, seed unchanged); R40-15 (acknowledgement requested); R40-19 (review39 SNAPSHOT-BEFORE 09:55:49Z); R40-20 (review39's final AUDIT-LOG.md / PROGRESS.md copied and bound).
- **Preflight (dry):** as written REFUSED (placeholder); dummy digest PASSED; 48/48 negative probes as expected (the harness still accepts '12.0' / '120.0', R40-08, which the integer-string check refuses); binding 239/239; bounds recomputed equal; the four lanes' live environment checks pass offline; the live runner refused with no folder (no RUN file; no scope; no authorization); the guard refused and built no provider; the scope command's preview created nothing and its create mode refused without an authorization file.
- **Dry exercise:** the bound review39 harness unchanged (declared sandbox base, no twin), reader 'none', refusing stub: main run status finished; EP-27331 deferral loops under 'full' finished in {'planning-shape-window-10': 2, 'structural-shape-window-6': 3} invocations with every early resume refused and nothing created; the CLI-version dead-end shown (a version refusal at invocation 1 leaves a folder without an allowance: neither run nor resume can continue); model requests 0; AI ledger 483 / 17 / 0 before and after.
- **Tests:** 36 tests, 0 failures, 0 errors, 0 write-guard refusals (`tests/test_r40.xml`).
- **Environment note:** drive C: reached 0 bytes free during the first dry-exercise attempt (other processes were writing ep-platform test temp folders); that attempt is recorded in the work folder and was re-run; nothing of anyone else was touched.

**Zero calls:** no provider or model request of any kind, no `claude` invocation in any form, no network; no prediction; no ledger scope, token, authorization file or RUN file; the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 amendments before and after.

**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).

**Status, stated separately:**
1. **Correction readiness:** the corrected declaration, runbook and scope-creation command are delivered, **pending Verification 41**; not self-approved.
2. **Accuracy:** none. No prediction exists; every figure is an estimate, a bound or a dry-run exercise.
3. **Label truth:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) independently AI-reviewed (Claude agents), not human-signed; populations 57 / 38 / 38.
4. **Permissions and budget:** eligibility only (A-06). No authorization file, token, budget, ledger scope or dispatch exists. Open owner decisions: served-model identity UNRESOLVED (probe or accept); R40-04 (accept the proof or order a harness change); the budget authorization.
5. **M2:** **CHANGES STILL REQUIRED.**
6. **M3:** not started.
