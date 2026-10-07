# M10 addendum: GET handlers that now do folder listing or reconcile on an ordinary read (7 October 2026)

Unified milestone: M10 (Database-Driven Tab Migration). Task: ORCH-037 (ep-scribe). Worktree `G:/dev (2)/dev/ep-platform-merged/roadmap-u2`, branch `roadmap/u2`, HEAD at start `573780a561fac560b5e5b5344c227f348eb65fb2`.

## Status

**Implemented / partial, not accepted.** The M10 exit is not met for these routes (survey section 6, M10 row: "Zero read-time folder scan and zero business write: not met"). The code is uncommitted in the live clone `G:/dev (2)/dev/ep-platform-merged/ep-platform` (branch `claude/upbeat-lovelace-sa9j3w`, HEAD 7a1bf6f) at 2026-10-07. Source: `MR/orchestrator/surveys/U2-DELTA-DRAWINGS-PROCESSING-2026-10-07.md` (the survey), snapshot 22:13:40 local. The survey records sha256 only for `document_classification_ai.py`, `drawings_chat.py`, `folder_import.py` (a29346b60235) and `sheet_numbers.py`; for `routers/drawings.py`, `routers/ifc_boq.py`, `shop_drawings.py`, `project_state.py` it records none. Nothing was run by the scribe.

The roadmap M10 exit: "ordinary tab reads perform no source parsing/OCR/model calls/folder scans or business writes", and the M3-accepted list of eight groups of state-changing GET handlers moves to processors or explicit commands, M7 owning the processors. The survey states that list is unchanged by this change set, which **adds one new scanning GET and extends reconcile-on-read to two more routes and to Home's richer path**.

## 1. Handlers (6 rows), in the section 9 consumer-acceptance columns

Section 9 of the roadmap requires each row to hold: input owner, source/artifact IDs, API contract, freshness, override behavior, legacy/new comparison, no-read-work check and rollback switch. Section 9 Drawings row: "Stored scope/revision/approval and review projections; remove GET reconciliation; reuse extraction, geometry and evidence". What the survey records is filled in; everything else says "not recorded; to be defined".

| # | GET handler | What it does on the read (survey section 3) | Class | Input owner | Source / artifact IDs | Freshness | Override behavior |
|---|---|---|---|---|---|---|---|
| G1 | `GET /drawings/summary` (`drawings.py:125-133`) | `_catch_up` (:130), then `shop_drawings.summary`, which now calls `log_by_ifc` for each system (`shop_drawings.py:1041+`). `reconcile(ai=False)` writes shop drawing, floor and issue rows and commits when `needs_reconcile` | reconcile + read-model | owner decision pending (M7) | Stored IFC sheets in `ProjectIfcDrawing.meta`; no artifact id | `needs_reconcile` compares sync and reconcile timestamps (`shop_drawings.py:718-723`) | not recorded; to be defined |
| G2 | `GET /drawings/log?view=` (`drawings.py:136-142`; `_log` :96-122) | `_catch_up` (:97), builds the log, then `folder_import.files` (:116): a directory scan on every call, including `view=floor` (a OneDrive-synced folder, per the survey) | reconcile + folder-scan | owner decision pending (M7) | As G1; folder listing has no stored form | As G1; listing is live | not recorded; to be defined |
| G3 | `GET /drawings/log/export.xlsx` (`drawings.py:153-211`) | Same `_log` call (:161) | reconcile + folder-scan | owner decision pending (M7) | As G2 | As G2 | not recorded; to be defined |
| G4 | `GET /ifc-drawings/folder` (`ifc_boq.py:578-586`) | `folder_import.files`: `os.path.isdir`, `os.scandir` of the IFC folder, `entry.stat()` per file (`folder_import.py:92-137`); DB reads of live drawings and active `ifc_read` jobs. No hashing, no file opening, no write | folder-scan (listing only; the docstring "Nothing is read here" is true for content) | owner decision pending (M7) | Directory entries; no artifact id | Live | n/a |
| G5 | `GET /drawings/assistant` (`drawings.py:660-668`) | `drawings_chat.available` calls `get_chat_provider()`, which may construct the provider object (`provider.py:998-1001`); no model call, no write | read-model-only (provider construction side effect) | owner decision pending (M7) | none | n/a | n/a |
| G6 | Project Home `/state` through `project_state._shop_drawings_by_system` (`project_state.py:205-224`), an existing path whose meaning changed | Reconcile if behind, then `shop_drawings.summary`, now per IFC sheet | reconcile (existing) and a semantic change: Home's `total`/`approved` now count IFC sheets while its docstring still says floors (:207-209) | owner decision pending (M7) | as G1 | as G1 | not recorded; to be defined |

Related, not a GET: the assistant POST (`/drawings/assistant`, `drawings.py:671`) walks the project folder: `drawings_chat._required` (:215-230) -> `drawing_requirements.status` -> `required_drawings.status` (`os.isdir`, `os.walk`, `required_drawings.py:109-115`, :91). The docstrings "no file is opened for it" (`drawings_chat.py:10`) and "never from the folder" (:236) are only partly true (survey section 3, observations). Not a read-side GET, but a folder walk per message.

Observed as already read-model-only (survey): `log_by_ifc` itself (stored sheets from `meta` via `building_floors.ifc_sheets`, `building_floors.py:84-91`, aliases and records; docstring "nothing is written" holds, `shop_drawings.py:913-928`) and `folder_import.drawings_for` (DB only, :66-78). The sheet-number backfill is a CLI, not a GET (`sheet_numbers.py:1-13`).

## 2. The contract these routes will have to meet

From the roadmap M10 exit and section 9, applied to the six handlers. Nothing below is a claim that any item is met today.

1. **No read-time folder scan.** G2, G3 and G4 must serve a stored projection of the IFC folder listing, not `os.scandir` on the request. Survey's smallest action: "replace the listing with a stored projection once M7 exists". The producer of the listing becomes a processor or an explicit command (for example, an explicit refresh action), with M7 owning the processor.
2. **No business write on a read.** G1, G2, G3 and G6 must not call `_catch_up` or `reconcile`. Reconciliation moves to a processor or explicit command; the read returns stored state with pending, stale, missing, partial and conflict states shown honestly (M10 exit).
3. **No model call, no parsing** on any of the six; G5's provider construction must not be a side effect of a status read (class read-model-only today).
4. **Consumer acceptance record per row (section 9):** input owner (decision pending, M7), source/artifact IDs (from the M7 registry, once it exists), API contract (the six routes' current shapes are the legacy side), freshness (honest per capability), override behavior (not recorded for the per-sheet log; the survey states the sheet-number override semantics are not recorded), legacy/new comparison, no-read-work check, rollback switch.
5. **Home (G6) migrates after its inputs** (M10 exit), and its sheet-versus-floor semantic change must be settled first: Home's total and approved count IFC sheets while its docstring says floors, and Home and Drawings aggregates must not be reused for workload (RC-37, roadmap M28 row).
6. **Per-IFC-sheet log (`log_by_ifc`)** is the survey's "good stored-read candidate": it needs no parsing on read because it uses stored sheets. The stored sheet number has no version for its reading logic (`needs_numbers` means "no sheet has a `number` key", `sheet_numbers.py:32-35`), so a freshness rule must be defined before it can be a registry artifact.

## 3. Smallest action named by the survey (section 6, M10 row)

Add three rows to the M10 consumer record: `GET /drawings/log` and `summary` (reconcile), `GET /ifc-drawings/folder` (scan), Home `/state` (semantic change); replace the listing with a stored projection once M7 exists.

## 4. What this addendum does not prove

That the IFC view needs no parsing on read is supported (stored sheets); zero read-time folder scan and zero business write are **not met**. No test or run supports either statement beyond the survey's code reading.
