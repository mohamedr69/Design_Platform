# Compatibility and persistence -- real documents, sandbox and clone

Every outcome below was read back from the sandbox database after reopening it (a separate read-only
connection), not from in-process objects. Runner scripts and raw outputs are under `outputs/`.

## 1. Discovery against the supported-file contract

The sync registers `.pdf` files anywhere and `.doc/.docx` files inside a transmittal folder; every other
extension is unsupported and counted, not registered. Per project the sandbox registered exactly the staged
sample (`files` = staged count; `RUN-*.json`): 40, 40, 55, 2, 52, 60, 32, 40, 58, 6 for EP-30784, 30088,
29076, 27474, 25091, 26369, 19977, 13777, 26082, 14119 (the 52/58 include the BOQ sheets staged into those
trees). The inventory's unsupported extensions per folder (`.dwg`, `.bak`, `.zip`, `.xlsx`, images, ...) are in
`PROJECT-INVENTORY.json`; none was registered.

## 2. Persistence scenarios on real sampled copies (both profiles, `outputs/SCENARIOS2-<profile>.json`)

Documents: a two-page shop-drawing cover (EP-30784, text), a one-page scanned drawing (EP-29076), an
eleven-page sample-tag submittal with records on pages 1 and 6 (EP-26082, the "package"), a 204-page scanned
datasheet pack (EP-29076, the "scan package"). The same 24 steps ran under both profiles with identical
outcomes except the stored profile stamp.

| step | what changed | observed, reopened from the database |
|---|---|---|
| 1 first read | 4 new files | 4 processed; package complete with records p1 (UR) and p6 (UR); scan package `bounded`, `stop_reason=page_scan_limit`, 12 visited / 192 skipped |
| 2 unchanged rerun (touched) | mtimes only | sync `changed 4`, processing `unchanged_after_hash 4`: readings reused, nothing re-read |
| 3 duplicate copy | same bytes under `Archive/` | its own row; `duplicates_reused 1`; records copied |
| 4 corrupt replacement | file replaced by a non-PDF | `failed 1`; row `failed`, error `FileDataError`, last good reading kept, `attempt=failed`, `stale=true` |
| 5 retry, nothing changed | -- | the failed row is planned again (`planned 1`) and fails again; still kept |
| 5b retry after a touch | mtime | the same |
| 6 restored | good bytes back | read; `duplicates_reused 1` (the twin's reading), attempt cleared, `stale` cleared |
| 7 file removed | deleted | `removed 1`; row state `removed`, reading kept |
| 8 file back | same bytes | `unchanged_after_hash 1`: the removed row returns `fresh` without a re-read |
| 9 scan re-read with OCR failing | bytes changed, OCR raising | `partial 1`; row `fresh` with `attempt=partial`, `stale=true`, previous reading kept |
| 10a partial, nothing changed | -- | the partial row is planned again and read successfully (`processed 1`), attempt cleared |
| 10b OCR back after a touch | mtime | `unchanged_after_hash 1` |
| 11 wide read of the package | bytes changed, limits 400 | complete, 11 visited |
| 12 narrow read (limits 3) of changed bytes | bytes changed | `bounded`, `stop_reason=reply_search_limit`, 3 visited / 8 skipped; the p6 record carried with `carried_unvisited`, `carried_unverified`, `retained.parser_version=parse-2026-09-28.4`; `extracted.retained` = {records 1, mixed false}; counted `partial 1` by the processing job |
| 13 narrow read again, same bytes | mtime | `unchanged_after_hash 1`: the bounded reading stands |
| 13b narrow read of changed bytes again | bytes changed | the carried record keeps its original provenance and flags (no restamp) |
| 14 wide read again | bytes changed, limits 400 | complete; nothing carried |
| 15 narrow read after a parser change | stored parser rewritten to `parse-older`, bytes changed, limits 3 | p6 record carried with `carried_other_parser` + `carried_unverified` + `carried_unvisited`, `retained.parser_version=parse-older`; `extracted.retained.mixed=true`, `other_parser=1`; status UR (decision withheld) |
| 16 wide read by the current parser | bytes changed, limits 400 | cleared: complete, both records current, no `retained` |
| 17 wide read under the other profile | profile swapped | reading stamped with the other profile |
| 18 narrow read under this profile | limits 3 | p6 record carried with `carried_other_profile`; `mixed=true`, `other_profile=1`; UR |
| 18b scanned package under an OCR budget of 2 | `OCR_PAGE_LIMIT` 2 | `bounded` (page scan limit stops the pack before the OCR budget binds on this file) |
| 19 cancelled after the first file | `JobContext.check` raises `Cancelled` | processing job `cancelled`; the first file written; the other three left `pending` |
| 20 resumed | next sync | `already_pending 4`, all four read; nothing written back as fresh in between |

Findings:

- A failed or partial row is planned again on the next sync even when its file has not changed (steps 5,
  10a). The processing job's telemetry counts a bounded reading with carried records as `partial` (steps 12,
  13b) although the row's own attempt outcome is not partial: a counting label, not a persistence defect
  (`DEFECTS.md` P-obs-2).
- Step 12 expected records on the skipped pages to be carried from "the earlier reading of other bytes" and
  that is what happened (`carried_unverified`); the M2 review 03 provenance rules hold on a real submittal.
- No scenario changed a business table other than `project_documents`, `document_dependencies` and the
  drawings tables the sync's own reconciliation owns.

## 3. Regression controls on a WAL-consistent clone of the live database (`outputs/clone_default/`)

Projects 1 (EP-30784, 359 registered documents) and 4 (EP-30088, 525). All 884 live readings are legacy
readings (`{records, notes}`, no parser version, state `fresh`).

| stage | what ran | result |
|---|---|---|
| snapshot before | `scripts/business_snapshot.py` for both projects | `snapshot_before_p*.json` |
| sync 1 | `POST /projects/{id}/jobs/sync-documents` inline (the worker's path, reconciliation included) | 359 / 525 unchanged, 0 changed, no processing job; only `documents_synced_at`, `drawings_reconciled_at`, a `project_changes` row, and idempotent rewrites of `drawing_issues` / `project_building_floors` / `project_shop_drawings` (same row counts, refreshed timestamps) |
| repair | `scripts/repair_extraction.py --project N --ids <the 80 sampled rows> --select parser-outdated --apply` | project 1: 38 selected, 36 repaired, 2 skipped (transmittals: another reader); project 4: 39 selected, 38 repaired, 1 skipped. Every repaired row: current parser, notes, evidence kinds; `document_dependencies` re-registered (+10 rows for project 4) |
| mirror changes by the repair | reference / revision / status columns | project 1: none; project 4: 10 references and 9 statuses changed, e.g. `ICC-DLRC-SPM-SD-MEP` -> `ICC-DLRC-SPM-SD-MEP-0078` (the legacy reading cut the serial), `7-Mar-2026` -> `ICC-DLRC-SPM-SD-MEP-FA-0128` (a date as reference), `UR` -> `rejected` / `ANN` where the York form's framed box is now read. Each is in `repair_p4.json` with old and new |
| sync 2 | the ordinary sync again | project 4 reconciliation from the repaired readings: 8 new `project_shop_drawings` rows, 7 `project_building_floors` rows, 2 `drawing_issues`, 17 `shop_drawing_events`; project 1: no domain delta |
| engineer marks | `project_boq_items` rows with an engineer origin (6 in project 1, 1 in project 4) | unchanged in every column |

Observed reconciliation defect (not fixed): two of the seven floors project 4 gained are `HC FIRE ALARM`
("Hc Floor Fire Alarm Layout", elevation 99999) and `FIRST FIRE ALARM`, derived from the drawing titles
`HC FLOOR FIRE ALARM LAYOUT` and `FIRST FLOOR FIRE ALARM LAYOUT`: the floor-name rule keeps the words after
"FLOOR" (`DEFECTS.md` P-05). G-01 (M1) remains an M4 gap: the reconciliation writes floors from readings
without an engineer gate.

## 4. BOQ / design-sheet path with the model disabled (`outputs/BOQ-RUN-default.json`)

For each of nine projects a sandbox project was created with its frozen sheets attached (`design_sheets`
under the staged tree) and `POST /projects/{id}/boq/ensure` called twice, then `POST .../jobs/boq-reread`.
Result, identical for all nine: `extracted=true`, 0 items, one warning per sheet
`"<sheet>: Not read: AI assistance is disabled (AI_ENABLED=false)"`, `boq_extracted_at` stamped once (the
second call returned the stored, empty BOQ), the reread job succeeded with `failed_sheets` listing every sheet
and 0 lines. No line was fabricated, no OCR-only reading was substituted for the model's. The 778 labelled rows
are therefore truth without a scored reading in this pilot: the design-sheet reader is a model-requiring
branch and is reported as **not exercised**.

## 5. R4-01 on the frozen code (`outputs/probe_r4/`)

The eight reviewer probes rerun on candidate A: the retained-parser probe now yields `parser_current=false`,
mirror UR, reuse hash absent, flags `carried_unvisited` + `carried_other_parser`; the seven earlier probes keep
their contracts. Persisted tests: `test_extraction_m2_review03.py` (18 passed), including
`test_a_record_read_by_an_older_parser_is_held_by_a_bounded_reading_until_its_page_is_read_again` and
`test_parser_compatibility_is_explicit_and_narrow`.

## 6. Profile separation

Default and promoted profiles ran into separate databases; 385 / 387 rows (the promoted run also registered
the two EP-30088 sheets staged meanwhile). Records differ between profiles on 8 documents (the promoted
profile turns held observations into records: three scanned transmittals `TR/...`, one extra page-2 record on
three York covers, a `rejected` / `ANN` read from a framed box on two). Every row carries its profile stamp;
no cross-profile reuse was observed (the promoted run, with a warm content-keyed OCR cache, still re-read every
document: `unchanged_after_hash 0`).
