# S5 - GET handler side-work audit (read-time producers and duplicate producers)

Surveyor: ep-surveyor (read-only). Repository: /home/user/Design_Platform, HEAD 771001e (2026-10-06). Static inspection only: no endpoint was called, no job run, no repository file edited. Baseline compared: docs/milestones/M1/M1-DUPLICATION-AND-READ-SIDE-EFFECTS.md (generated 2026-09-27, committed in e49c2bf).

## 0. Reading guide

- Every row cites file:line (paths relative to backend/app unless they start with frontend/). `routers/x.py:A-B` after a handler is the handler's own span; helper spans were checked against the AST.
- Where a fact could not be established the row or section 7 says UNKNOWN with the reason.
- Class vocabulary: the eight classes of the brief (PURE_READ, SERVES_BYTES, FOLDER_SCAN, PARSES, MODEL_CALL, RECONCILES, WRITES, JOB_ENQUEUE) plus one added class, **EXPORT_RENDER**: a document built on request from stored rows (xlsx/pdf download). EXPORT_RENDER alone is an explicit download and is not counted as read-time work; where an export also scans, parses, reconciles or writes, those classes are listed beside it and it is counted as work.
- PURE_READ includes handlers that derive a value in memory from stored rows and persist nothing (marked 'derived each request'), and handlers whose only non-DB touch is a single stat of one known path (marked 'single stat') or a model-availability probe (marked 'probe only': `get_provider()` / `provider.ready`, which never calls a model).
- WRITES counts a database commit, a created row or a created directory/file made by the GET itself. Audit rows (`activity.record`) written by an export or by opening a project are WRITES too and are marked audit.

## 1. Handler census

| Source | Count | Command / evidence |
|---|---|---|
| `@router.get` decorators in backend/app/routers/*.py | 144 | `grep -c "@router.get"` per file, summed (matches the brief) |
| `@admin_router.get` (extraction.py) | 2 | extraction.py:309 `/admin/usage`, :367 `/admin/metrics` (missed by the starting grep) |
| `@routes.get` inside the `project_router()` factory (divisions.py) | 2 defs, 4 routes | divisions.py:15, :32; instantiated twice at divisions.py:43-44 (`/fire-fighting/projects`, `/elv/projects`) |
| `@app.get('/health')` (main.py) | 1 | main.py:278 |
| **Handler definitions audited** | **149** | = 144 + 2 + 2 + 1 |
| Runtime GET routes | 151 | the factory defs register twice |

Routers with no `@router.get`: samples.py (one POST, samples.py:24), __init__.py. Other GET registration forms searched and not found: `api_route`, `add_api_route`, `app.mount`/StaticFiles (`grep -rn "api_route\|add_api_route\|@app\.get\|mount("`). No FastAPI import or route enumeration was run (importing the app would run its lifespan hooks).

Request-level side effects that apply to every GET (not counted per handler): main.py:129-157 `request_id` middleware writes one log line; main.py:161-194 `slide_session` may re-issue the session cookie (no database write); deps.py:12-41 `get_current_user` reads the user row.

## 2. Summary counts

Total GET handler definitions: **149**.

| Bucket | Handlers |
|---|---|
| PURE_READ only | 72 |
| SERVES_BYTES only | 3 |
| EXPORT_RENDER only (explicit download, no scan/parse/write) | 7 |
| **PURE_READ or SERVES_BYTES (compliant with the M10 rule)** | **75** |
| Pure exports (explicit action, allowed by the M1 counting unit) | 7 |
| **Performing read-time work (any of FOLDER_SCAN, PARSES, RECONCILES, WRITES; MODEL_CALL and JOB_ENQUEUE are zero)** | **67** |

Handlers per class (a handler can carry several):

| Class | Handlers |
|---|---|
| PURE_READ | 72 |
| SERVES_BYTES | 4 |
| EXPORT_RENDER | 26 |
| FOLDER_SCAN | 39 |
| PARSES | 39 |
| MODEL_CALL | 0 |
| RECONCILES | 22 |
| WRITES | 40 |
| JOB_ENQUEUE | 0 |

Of the 40 WRITES handlers: 5 write only an audit row (export routes: projects.py:646, projects.py:1157, submittal.py:1025, submittal.py:1054, submittal.py:1088); the others write business or derived state (drawings register, shop BOQ, battery results, project actions, compliance statements, floor schedule, review/redesign/FA/draftsman state rows, project-open event plus folders on disk, archive index root path).

MODEL_CALL = 0 and JOB_ENQUEUE = 0 from any GET. Evidence: every caller of a provider `.complete(` lives in ai/evaluation.py, compliance/assist.py, extraction/pipeline.py, ifc/services/ai_symbol_review.py, review/scoped.py, services/drawing_ai_review.py (`grep -rn "\.complete(" --include=*.py .`); the only static path from a GET into one is `shop_drawings.reconcile -> _ai_review -> drawing_ai_review`, which sits behind `if ai:` (services/shop_drawings.py:225-229) and every GET passes `ai=False` (routers/drawings.py:86, services/project_state.py:213). Every `jobs.enqueue`/`jobs.start`/`start_background_scan`/`start_import`/`Thread(` call under routers/ (18 hits, `grep -rn` then an AST lookup of the enclosing function and its decorator) sits in a `@router.post` handler or in a helper called only from POST handlers: verification.py:123 `_start` (callers ensure_verification :136 and start_verification, both POST), redesign.py:82 `_start` (start_plan/start_apply, POST), projects.py:856 `_start_boq_read` (ensure_project_boq, POST). The model-related GETs only probe availability (`get_provider()`, `provider.ready`: ai/provider.py:885-893, :666-668).

By router file (PURE / BYTES / EXPORT-only / WORK):

| Router | PURE | BYTES | EXPORT | WORK |
|---|---|---|---|---|
| amplifier.py | 4 | 0 | 2 | 0 |
| archive.py | 0 | 0 | 0 | 2 |
| auth.py | 3 | 0 | 1 | 0 |
| backups.py | 0 | 0 | 0 | 1 |
| boq_review.py | 4 | 0 | 0 | 2 |
| compliance.py | 3 | 1 | 0 | 5 |
| data_location.py | 1 | 0 | 0 | 0 |
| design.py | 1 | 0 | 0 | 4 |
| design_rules.py | 3 | 0 | 0 | 8 |
| divisions.py | 2 | 0 | 0 | 0 |
| documents.py | 5 | 0 | 0 | 0 |
| draftsman.py | 0 | 0 | 0 | 1 |
| drawing_review.py | 1 | 0 | 0 | 4 |
| drawings.py | 2 | 0 | 0 | 7 |
| estimation.py | 2 | 0 | 0 | 0 |
| extraction.py | 2 | 0 | 0 | 3 |
| fa_interfaces.py | 1 | 0 | 0 | 4 |
| floor_schedule.py | 3 | 0 | 1 | 1 |
| ifc_boq.py | 4 | 0 | 1 | 2 |
| jobs.py | 2 | 0 | 0 | 0 |
| knowledge.py | 4 | 0 | 0 | 0 |
| logs.py | 2 | 0 | 0 | 2 |
| main.py | 1 | 0 | 0 | 0 |
| materials.py | 2 | 0 | 0 | 3 |
| modules.py | 3 | 0 | 0 | 0 |
| project_state.py | 1 | 0 | 0 | 2 |
| projects.py | 6 | 1 | 0 | 3 |
| readiness.py | 1 | 0 | 0 | 1 |
| redesign.py | 1 | 1 | 0 | 3 |
| register.py | 1 | 0 | 0 | 1 |
| shop_boq.py | 1 | 0 | 1 | 1 |
| submittal.py | 2 | 0 | 0 | 7 |
| users.py | 3 | 0 | 1 | 0 |
| verification.py | 1 | 0 | 0 | 0 |

## 3. What the audit found (read this first)

1. **The M1 inventory is not stale in its 14 rows: all 14 producers are still present** (Table B). One changed in a way that makes it worse (BOQ ensure no longer stamps when nothing was attempted, so it retries on every editor open; projects.py:892-906). Three widened (battery persistence, drawings catch-up, datasheet refresh).
2. **Six GET producers are missing from M1's list.** Five arrived after M1's closure commit e49c2bf (`git diff --name-status e49c2bf HEAD -- backend/app/routers`: draftsman.py, drawing_review.py, fa_interfaces.py, redesign.py, shop_boq.py are added; amplifier.py, design.py, projects.py, submittal.py, main.py are modified): FA interfaces (create row + folder walk), Assign Draftsman (create row + commit + three nested chains), Drawing Review (create row + DXF/PDF fit + commit), Redesign (create row + commit + review build), BOQ as per Shop Drawings (create-on-first-read from the IFC drawings). The sixth, the parts typeahead GET /parts/search (an XLSX parse and a library probe per keystroke), existed at e49c2bf (`git show e49c2bf:backend/app/routers/materials.py` has it at :426) and M1 did not list it. Likewise present at e49c2bf and unlisted by M1: the AI-check mount POST (/ai-verification/ensure) and the /state -> drawings reconcile path (`git show e49c2bf:backend/app/services/project_state.py` line 211).
3. **Project Home is the worst single mount**: it fires GET /readiness, /logs, /materials and /state in parallel (frontend/src/pages/ProjectHomePage.tsx:46-62) and fires them again on every project-change event (:72-75) while lib/projectChanges.tsx:33,78 polls /changes every 5 s. Together those four reads reach: the battery calculation write (readiness, materials), the datasheet library refresh (materials), the drawings reconcile (state), the actions reconcile (state), and the folder-reply status overlay (logs). Several of these writes record `ProjectChange` rows (services/project_state.py:51-55, :337-349), which are what the polling page watches: a read that can emit the event that triggers another read.
4. **No GET calls a model and none starts a job.** The model-related risk is on mount-time POSTs (Table B items 1 and N7), not on GET.
5. **Docstrings that contradict the code** (a reader trusting them would misclassify): routers/drawings.py:22-23 ('No request walks the project folder or resolves an IFC drawing' - the catch-up reconcile reads the IFC register and writes), routers/materials.py:241-243 and :395 ('nothing is scanned' - `_attach_datasheets` triggers the library refresh and the battery write), routers/design_rules.py:61 (proposals 'save nothing' is true, but every request regex-scans every indexed page of every sheet).

Worst three read-time producers by cost or business impact: (1) drawings reconcile on GET, reached from 8 GET handlers (5 in drawings.py, 2 in logs.py, and Home's /state);(2) datasheet-library discovery and refresh, reached from 16 GET handlers by refresh (including every consumer of the battery calculation, design.py:415 -> :644-662) and 18 by per-call discovery, including Home's /materials, documented in the code as taking minutes on a synced drive (services/schedule_materials.py:106-108: 'walks the manufacturer libraries on a synced drive and takes minutes'); (3) compliance statement recheck, which withdraws an engineer's approval and rewrites rows on a plain GET (and on the approved-statement exports). Close fourth: the battery calculation write, reached from 7 GET handlers (design.py:299/703/729, materials.py:233/387, readiness.py:64, submittal.py:1290) including two of Home's four mount reads.

## 4. Table A - every GET handler

Columns: router:decorator-line, path, handler (def line, span), classes, evidence (deepest file:line that does the work), notes. PURE_READ/SERVES_BYTES rows are brief; work rows carry the full chain.

### Shared chains (named once, referenced in the rows)

- **[BAT]** routers/design.py:410-586 _battery_calculation: recalculates a panel whose input hash moved (:484-514), db.add :511, db.commit :525-526 (BatteryPanelResult); and :415 _selectable_batteries :644-662 -> library.batteries (services/datasheet_library.py:466-473) -> _refresh, so every battery calculation also runs the datasheet-library discovery/refresh (chain: services/datasheet_library.py:311-348, services/company_library.py:248-281)
- **[DS]** datasheet-library refresh on lookup: services/datasheet_library.py:311-348 (age test :315-317, rglob :324, stat :334, changed PDF -> _index_file :339 -> pymupdf.open :210, cache rewrite _save_cache :347); library discovery on every call: services/company_library.py:248-281 (iterdir :260, holds_documents :266 -> os.scandir :228)
- **[RECON]** routers/drawings.py:81-86 _catch_up -> services/shop_drawings.py:718-723 needs_reconcile -> :144-234 reconcile(ai=False) (writes drawings/revisions/candidates/issues/floors/events + project.drawings_reconciled_at, db.commit :233; the model branch is skipped by `if ai:` :225-229)
- **[ACT]** services/project_state.py:323-355 reconcile_actions (db.add :337, resolve/reopen :341-349, db.flush :354) + routers/project_state.py:57-67 _actions (db.commit :64)
- **[FA]** interfaces/service.py:797-843 build -> state() creates the row on first read (:181-187 db.add/flush) and interfaces/evidence.py:166-185 take (os.scandir :176) -> _walk :109-163 (os.walk :123, stat only); router commit
- **[DREQ]** services/drawing_requirements.py:80-87 status -> services/required_drawings.py:105-146 -> _files :88-102 (os.walk of each required folder, os.path.isdir :114)
- **[STMT]** compliance/service.py:1052-1113 recheck (rows/summary/approval rewritten, _audit rows, db.commit :1067 and :1111; current_spec_sha :1005-1031 reads the whole spec file, cached on mtime/size)
- **[SPECS]** routers/compliance.py:164-206 _specs: find_specs on cold/refresh/moved (:187 -> services/spec_finder.py:343-439, rglob :362, pymupdf.open :377/:409/:430, zip member :384-393), _verify_matches :201 (reads first pages), _store_specs :155-161 (db.commit)
- **[AUDIT]** services/activity.py:45-72 record (db.add :70, db.commit :72): an audit row is written by this GET
- **[PROBE]** ai/provider.py:885-893 get_provider / :666-668 ready (probe only: shutil.which at construction, no model call)

### amplifier.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/amplifier.py:150 | `/projects/{project_id}/design/power` | `get_power` @151 (151-161) | PURE_READ | routers/amplifier.py:123-147 _power -> services/power_calculation.calculate (in memory); DB reads _current :47-52, _source :101-107; services/schedule_materials.py:152-173 sounder_bases | derived each request, never stored (module docstring :13-17); not persisted |
| routers/amplifier.py:292 | `/design/device-currents` | `device_currents` @293 (293-302) | PURE_READ | routers/amplifier.py:293-300 current_database :72-74 -> _current :47-52 |  |
| routers/amplifier.py:305 | `/projects/{project_id}/design/power/export.pdf` | `export_power` @306 (306-326) | EXPORT_RENDER | routers/amplifier.py:306-326 -> services/power_export.py:45 pymupdf.open() (new document built from the in-memory result) | explicit download; no scan |
| routers/amplifier.py:336 | `/design/speakers` | `speakers` @337 (337-348) | PURE_READ | routers/amplifier.py:337-348 speaker_database :55-57 -> _current :47-52 |  |
| routers/amplifier.py:388 | `/projects/{project_id}/design/amplifier/export.pdf` | `export_amplifier` @389 (389-409) | EXPORT_RENDER | routers/amplifier.py:389-409 -> services/amplifier_export.py:53 pymupdf.open() | explicit download; no scan |
| routers/amplifier.py:496 | `/projects/{project_id}/design/amplifier` | `get_amplifier` @497 (497-507) | PURE_READ | routers/amplifier.py:359-385 _out -> services/amplifier_calculation.calculate (in memory); handler :497-507 | derived each request, not persisted |

### archive.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/archive.py:71 | `/archive/search` | `search_archive` @72 (72-90) | WRITES | services/ep_directory.py:471-533 search -> get_root :167-182: `elif record.root_path != str(root): record.root_path = ...; db.commit()` (:180-182) | write only when this PC sees the archive root at a different path; otherwise a LIKE query on the index (:492-496). create=False so no create-on-first-read |
| routers/archive.py:93 | `/archive/status` | `archive_status` @94 (94-98) | WRITES | services/ep_directory.py:536-563 status: root.is_dir() :542 (one stat of the archive root) and get_root :543 (conditional commit :180-182) | single stat of the archive root, not a walk |

### auth.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/auth.py:85 | `/auth/me` | `me` @86 (86-87) | PURE_READ | routers/auth.py:86-87; deps.py:12-41 get_current_user (DB read of user) | middleware main.py:161-194 slides the session cookie (no DB write) |
| routers/auth.py:93 | `/auth/me/account` | `my_account` @94 (94-95) | PURE_READ | routers/auth.py:94-95 -> routers/users.py:176-177 account_out -> services/activity.py:140 account (DB reads) |  |
| routers/auth.py:98 | `/auth/me/activity` | `my_activity` @99 (99-107) | PURE_READ | routers/auth.py:99-107 -> routers/users.py:180-186 -> services/activity.py:92 events |  |
| routers/auth.py:110 | `/auth/me/account/export.xlsx` | `export_my_account` @111 (111-112) | EXPORT_RENDER | routers/auth.py:111-112 -> routers/users.py:189-195 -> services/activity.py:294 account_workbook (openpyxl Workbook built in memory) | no audit row written |

### backups.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/backups.py:44 | `/admin/backups` | `list_backups` @45 (45-53) | FOLDER_SCAN | routers/backups.py:49-50 BACKUPS_ROOT.glob('*.db') + path.stat() | admin only; one directory |

### boq_review.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/boq_review.py:112 | `/projects/{project_id}/boq/candidates` | `list_candidates` @113 (113-120) | PURE_READ | routers/boq_review.py:113-120 BoqCandidate query limit 20 |  |
| routers/boq_review.py:123 | `/projects/{project_id}/boq/candidates/{candidate_id}` | `get_candidate` @124 (124-131) | PURE_READ | routers/boq_review.py:124-131 _full(candidate, boq_version) |  |
| routers/boq_review.py:134 | `/projects/{project_id}/boq/candidates/{candidate_id}/changes/{change_id}/evidence.png` | `candidate_change_evidence` @135 (135-148) | PARSES FOLDER_SCAN | routers/boq_review.py:135-148 -> _render :262-281: boq_provenance.pipeline_sha :269 -> extraction/pipeline.sha256_of (hashes the whole Design Sheet) then ai/evidence.py:77-92 render_region (pymupdf.open :82, get_pixmap of the whole page :83, crop) | evidence picture rendered on demand from the source PDF; browser cache 300 s (_render :262-281) |
| routers/boq_review.py:212 | `/projects/{project_id}/boq/snapshots` | `list_snapshots` @213 (213-220) | PURE_READ | routers/boq_review.py:213-220 |  |
| routers/boq_review.py:223 | `/projects/{project_id}/boq/snapshots/{snapshot_id}` | `get_snapshot` @224 (224-231) | PURE_READ | routers/boq_review.py:224-231 |  |
| routers/boq_review.py:282 | `/projects/{project_id}/boq/items/{item_id}/evidence.png` | `boq_item_evidence` @283 (283-292) | PARSES FOLDER_SCAN | routers/boq_review.py:283-292 -> _render :262-281 (sha256 of the Design Sheet :269 + render_region ai/evidence.py:77-92) | one whole-page raster per requested line image |

### compliance.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/compliance.py:259 | `/projects/{project_id}/compliance` | `get_compliance` @260 (260-284) | FOLDER_SCAN PARSES WRITES | [SPECS]; every GET also: _uploaded_specs :100-128 opens each uploaded PDF (pymupdf.open :115, reads_like_a_spec) and _stored_specs :135-152 stats each stored path; assist.available :230-232 (probe) | M1 row 7. Cold, ?refresh=true (a GET query flag) or a moved file triggers the search; the upload re-read is unconditional |
| routers/compliance.py:287 | `/projects/{project_id}/compliance/file` | `open_specification` @288 (288-311) | SERVES_BYTES | routers/compliance.py:288-311 -> services/spec_finder.py:442-458 open_spec (reads the PDF, or extracts a zip member :452) | serves bytes; may extract from a zip |
| routers/compliance.py:333 | `/projects/{project_id}/compliance/draft-mail` | `draft_mail` @334 (334-376) | PURE_READ | routers/compliance.py:334-376 builds mail text from project records |  |
| routers/compliance.py:506 | `/projects/{project_id}/compliance/statements` | `list_statements` @507 (507-518) | PURE_READ | routers/compliance.py:507-518 (limit 30); _summary :417-419 -> service.is_approved/approval_blockers/readiness_of (computed) | recheck is NOT run here (M1 confirmed) |
| routers/compliance.py:521 | `/projects/{project_id}/compliance/statements/{statement_id}` | `get_statement` @522 (522-529) | WRITES RECONCILES | routers/compliance.py:522-529 -> _statement_out :424-427 -> [STMT] | M1 row 5: rows flagged recheck and approval withdrawn on a GET when BOQ/scope/knowledge/spec file moved; legacy rows upgraded + committed |
| routers/compliance.py:802 | `/projects/{project_id}/compliance/statements/{statement_id}/export.pdf` | `export_statement_pdf` @803 (803-820) | EXPORT_RENDER WRITES RECONCILES PARSES | routers/compliance.py:803-820 -> _approved_statement :791-794 (service.recheck) + _statement_event :812 (activity.record: [AUDIT]) + compliance/pdf_writer.py:171 build_pdf (pymupdf.open :56) | export that rechecks, writes an audit row and rebuilds the PDF |
| routers/compliance.py:823 | `/projects/{project_id}/compliance/statements/{statement_id}/export` | `export_statement` @824 (824-841) | EXPORT_RENDER WRITES RECONCILES | routers/compliance.py:824-841 -> _approved_statement :791-794 + _statement_event :833 + compliance/writer.py build_workbook | export that rechecks and writes an audit row |
| routers/compliance.py:844 | `/projects/{project_id}/compliance/statement-files` | `statement_files` @845 (845-852) | FOLDER_SCAN | routers/compliance.py:845-852 -> compliance/service.py:1126-1135 statement_files -> compliance/references.py:52-59 candidates (os.walk of the project folder and the uploads folder, name filter only) | walk of the whole project folder on every call |
| routers/compliance.py:855 | `/projects/compliance/knowledge` | `knowledge_status` @856 (856-859) | PURE_READ | routers/compliance.py:856-859 -> knowledge/importer.py:632-675 status (counts); source_root :114-125 does one is_file() |  |

### data_location.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/data_location.py:50 | `/data-location` | `data_location` @51 (51-79) | PURE_READ | routers/data_location.py:51-79 (two COUNT queries; Path.resolve of config paths) |  |

### design.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/design.py:160 | `/projects/{project_id}/design/ve` | `get_voice_evacuation` @161 (161-166) | PURE_READ | routers/design.py:161-166 -> _out :124-135 -> services calculate(design) in memory | derived each request |
| routers/design.py:169 | `/projects/{project_id}/design/ve/workbooks` | `list_amplifier_workbooks` @170 (170-190) | FOLDER_SCAN | routers/design.py:170-190: os.walk(project folder) :177, name regex only, capped by MAX_WORKBOOK_CANDIDATES | creator roles; walk of the whole project folder on every call |
| routers/design.py:299 | `/projects/{project_id}/design/battery` | `get_battery_calculation` @300 (300-315) | WRITES RECONCILES FOLDER_SCAN PARSES | [BAT]; plus _unresolved_reason :284-296 -> library.find for every part without a current ([DS]) | M1 row 2 producer + row 8. Consumer path (1) |
| routers/design.py:703 | `/projects/{project_id}/design/battery/export.xlsx` | `export_battery_calculation` @704 (704-726) | EXPORT_RENDER WRITES RECONCILES FOLDER_SCAN PARSES | routers/design.py:704-726: _battery_calculation :713 ([BAT]) + activity.record :717 ([AUDIT]) + services/battery_export.py workbook | M1 consumer path (6); also an audit row |
| routers/design.py:729 | `/projects/{project_id}/design/battery/export.pdf` | `export_battery_calculation_pdf` @730 (730-762) | EXPORT_RENDER WRITES RECONCILES FOLDER_SCAN PARSES | routers/design.py:730-760: _battery_calculation :743 + activity.record :744 + services/battery_pdf.py:418-434 battery_calculation_pdf (pymupdf.open :434) | consumer path (6); also an audit row |

### design_rules.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/design_rules.py:54 | `/design-rules/datasheets/proposals` | `datasheet_proposals` @55 (55-78) | FOLDER_SCAN PARSES | routers/design_rules.py:55-78: for every library, library.listing() :367 (-> [DS]) and candidate_parts :392-420 (regex over every indexed page text of every sheet) per request | O(all sheets x all pages) computed on read; nothing saved (docstring :61) |
| routers/design_rules.py:153 | `/design-rules/part-currents` | `list_part_currents` @154 (154-158) | PURE_READ | routers/design_rules.py:154-158 active_rules :122-128 |  |
| routers/design_rules.py:184 | `/design-rules/equipment-currents` | `list_equipment_currents` @185 (185-194) | PURE_READ | routers/design_rules.py:185-194 -> services/equipment_currents.py:153 all_rows |  |
| routers/design_rules.py:264 | `/design-rules/datasheet-libraries` | `list_datasheet_libraries` @265 (265-291) | FOLDER_SCAN PARSES | routers/design_rules.py:265-290: get_libraries() + library.count() :355-357 ([DS]) |  |
| routers/design_rules.py:294 | `/design-rules/datasheet-systems` | `list_datasheet_systems` @295 (295-326) | FOLDER_SCAN PARSES | routers/design_rules.py:295-326: len(library.listing()) :359-390 for every library ([DS]) |  |
| routers/design_rules.py:350 | `/design-rules/datasheets/all` | `list_all_datasheets` @351 (351-386) | FOLDER_SCAN PARSES | routers/design_rules.py:351-386: library.listing() per library ([DS]) + datasheet_documents.stored (DB) |  |
| routers/design_rules.py:394 | `/design-rules/datasheets/index` | `datasheet_index` @395 (395-454) | FOLDER_SCAN PARSES | routers/design_rules.py:395-454: library.listing() ([DS]) |  |
| routers/design_rules.py:457 | `/design-rules/datasheets` | `find_datasheets` @458 (458-499) | FOLDER_SCAN PARSES | routers/design_rules.py:458-499: equipment_currents.datasheet_for, datasheet_links.lookup, else library.find :419-482 ([DS]) |  |
| routers/design_rules.py:502 | `/design-rules/datasheets/file` | `open_datasheet` @503 (503-513) | SERVES_BYTES FOLDER_SCAN | routers/design_rules.py:503-513 _libraries() :260-261 -> get_libraries (services/company_library.py:248-281 discovery: iterdir :260, holds_documents :266 -> os.scandir :228, every call), library.resolve (stat, services/datasheet_library.py:499-505) -> FileResponse | serves the stored PDF; the folder scan is the library discovery that precedes it |
| routers/design_rules.py:521 | `/design-rules/datasheets/thumbnail` | `datasheet_thumbnail` @522 (522-550) | PARSES FOLDER_SCAN | routers/design_rules.py:522-550 (library discovery per call: services/company_library.py:248-281): pymupdf.open :542, load_page(0), get_pixmap -> PNG per request | thumbnail rendered on the way out, not stored (docstring :526-531); browser cache 3600 s |
| routers/design_rules.py:553 | `/design-rules/battery-units` | `list_battery_units` @554 (554-558) | PURE_READ | routers/design_rules.py:554-558 |  |

### documents.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/documents.py:73 | `/projects/{project_id}/documents/status` | `document_status` @74 (74-92) | PURE_READ | routers/documents.py:74-92 -> services/document_sync.py:1354-1365 status; jobs.worker_running (services/jobs.py:484-493, DB heartbeat read); one folder.is_dir() :88 | single stat of the project folder; folder content not read (docstring :80) |
| routers/documents.py:244 | `/projects/{project_id}/documents/sync-summary` | `sync_summary` @245 (245-258) | PURE_READ | routers/documents.py:245-258 -> services/document_sync.py:1542-1575 sync_summary (index rows only) |  |
| routers/documents.py:261 | `/projects/{project_id}/documents/sync-files` | `sync_files` @262 (262-276) | PURE_READ | routers/documents.py:262-276 -> services/document_sync.py:1459-1482 sync_files (index rows only) |  |
| routers/documents.py:279 | `/projects/{project_id}/documents/classification` | `document_classification` @280 (280-300) | PURE_READ | routers/documents.py:280-300 -> services/document_classification.py:937-961 as_dict (stored assessment + freshness test; no file read) |  |
| routers/documents.py:321 | `/projects/{project_id}/documents/classification/metrics` | `document_classification_metrics` @322 (322-330) | PURE_READ | routers/documents.py:322-330 -> services/document_classification.py:1007-1060 metrics (counts) |  |

### draftsman.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/draftsman.py:41 | `/projects/{project_id}/draftsman` | `get_assignment` @42 (42-43) | WRITES FOLDER_SCAN PARSES RECONCILES | routers/draftsman.py:27-38 _view: service.state creates the row on first read (services/draftsman_assignment.py:73-79 db.add :77/flush :78) + db.commit :30; services/draftsman_assignment.py:205-233 items runs seven checks: [DREQ]; _interfaces :100-114 ([FA]); _review :130-149 -> review/service.py:593 build for every review row (:596 _fit may parse DXF+PDF and commit); _amplifier :152-166 and _power :169-184 recompute from routers/amplifier.py | NOT in M1. One GET = create row + commit + folder walks + the Interfaces and Review chains; exceptions are swallowed per item (draftsman_assignment.py:225-229) |

### drawing_review.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/drawing_review.py:43 | `/projects/{project_id}/drawing-review` | `overview` @44 (44-51) | PURE_READ | routers/drawing_review.py:44-51 -> review/service.py:1018-1026 pages_of (stored sheet list); revisions.in_force (DB) |  |
| routers/drawing_review.py:54 | `/projects/{project_id}/drawing-review/{drawing_id}` | `get_review` @55 (55-60) | WRITES PARSES | routers/drawing_review.py:55-60 (build :58, db.commit :59) -> review/service.py:593-597 build: state() create-on-first-read :49-57 (db.add/flush); _fit :537-554 -> review/geometry.py:80-96 fit_sheets (ezdxf.readfile + pymupdf.open of the plotted PDF) when a sheet lacks the current geometry version; db.commit :596 and routers/drawing_review.py:59 | NOT in M1. 'a review read before this existed gets it the first time it is shown' (review/service.py:538-540) |
| routers/drawing_review.py:159 | `/projects/{project_id}/drawing-review/{drawing_id}/image` | `image` @160 (160-177) | PARSES | routers/drawing_review.py:160-177 -> review/service.py:1029-1045 image (pymupdf.open :1034 + crop render); service.state :173 creates a row (flush, never committed -> rolled back at session close) | image rendered on demand; browser cache 3600 s |
| routers/drawing_review.py:180 | `/projects/{project_id}/drawing-review/{drawing_id}/export.xlsx` | `export` @181 (181-228) | EXPORT_RENDER WRITES PARSES | routers/drawing_review.py:181-228 -> service.build :189 (create row, _fit parse, commit as above) + openpyxl workbook | export that triggers the review build |
| routers/drawing_review.py:231 | `/projects/{project_id}/drawing-review/{drawing_id}/markup.pdf` | `markup` @232 (232-249) | EXPORT_RENDER WRITES PARSES | routers/drawing_review.py:232-249 -> service.build :241 (as above) + review/markup.py:79 build (pymupdf.open + reads the plotted PDF) | export that triggers the review build |

### drawings.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/drawings.py:111 | `/projects/{project_id}/drawings/summary` | `drawings_summary` @112 (112-119) | RECONCILES WRITES | [RECON] | M1 row 4 |
| routers/drawings.py:122 | `/projects/{project_id}/drawings/log` | `drawings_log` @123 (123-127) | RECONCILES WRITES | [RECON] via _log :89-90 | M1 row 4 |
| routers/drawings.py:138 | `/projects/{project_id}/drawings/log/export.xlsx` | `export_drawings_log` @139 (139-188) | RECONCILES WRITES EXPORT_RENDER | [RECON] via _log :89-90; then openpyxl workbook :139-175 | M1 row 4 |
| routers/drawings.py:194 | `/projects/{project_id}/drawings/issues` | `issues` @195 (195-203) | RECONCILES WRITES | [RECON] at :198 | M1 row 4 |
| routers/drawings.py:209 | `/projects/{project_id}/drawings/floors` | `building_floors_view` @210 (210-226) | RECONCILES WRITES | [RECON] at :215 | M1 row 4 |
| routers/drawings.py:313 | `/projects/{project_id}/drawings/activity` | `drawings_activity` @314 (314-320) | PURE_READ | routers/drawings.py:314-320 -> services/shop_drawings.py:1040 events | no catch-up here |
| routers/drawings.py:333 | `/projects/{project_id}/drawings/sd/{drawing_id}` | `drawing_detail` @334 (334-337) | PURE_READ | routers/drawings.py:334-337 -> services/shop_drawings.py:889-909 detail (stored row) | no catch-up (M1 confirmed) |
| routers/drawings.py:533 | `/projects/{project_id}/drawings/required` | `required` @534 (534-541) | FOLDER_SCAN | routers/drawings.py:534-541 _required :529-530 -> [DREQ]; + services/project_state.py:151-164 material_approval -> items :113-119 -> routers/submittal.py:445-495 register_items (DB + index rows) | folder presence decides 'received' (a state inferred from files) |
| routers/drawings.py:544 | `/projects/{project_id}/drawings/required/export.xlsx` | `export_required` @545 (545-586) | FOLDER_SCAN EXPORT_RENDER | routers/drawings.py:545-585 _required :529-530 -> [DREQ] + openpyxl workbook |  |

### estimation.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/estimation.py:29 | `/estimation/projects` | `list_projects` @30 (30-31) | PURE_READ | routers/estimation.py:30-31 |  |
| routers/estimation.py:48 | `/estimation/projects/{project_id}` | `open_project` @49 (49-53) | PURE_READ | routers/estimation.py:49-53 |  |

### extraction.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/extraction.py:164 | `/projects/{project_id}/extraction` | `get_extraction` @165 (165-188) | FOLDER_SCAN | routers/extraction.py:165-188: sheet_reader.readings_for (ai/sheet_reader.py:266-283) SHA-256-hashes every Design Sheet (:274) and the DRF (:280) in full via extraction/pipeline.py:60-70 sha256_of; _run_out :125-157 -> llm_task_for :138 -> extraction/issues.py:164-173 -> ai/evaluation.py:338-342 gate_open -> _reports :308-324 (glob + stat of eval/reports/*.json :313, once per issue per request; contents re-read only when the stamp changes); get_provider/ready is a probe: [PROBE] | NOT in M1. Whole-file hashing of the project's source documents and a report-folder glob per listed issue on every open of the extraction view; model availability probe only |
| routers/extraction.py:198 | `/projects/{project_id}/extraction/issues/{issue_id}/evidence.png` | `issue_evidence` @199 (199-214) | PARSES | routers/extraction.py:199-213 -> ai/evidence.py:77-92 render_region (pymupdf.open :82, whole-page get_pixmap :83) | issue evidence rendered on demand |
| routers/extraction.py:347 | `/projects/{project_id}/ai/budget` | `project_ai_budget` @348 (348-364) | PURE_READ | routers/extraction.py:348-362 -> ai/metrics.py:125-142 budget_status (COUNT queries); get_provider probe | model availability probe only |
| routers/extraction.py:309 | `/admin/ai/usage` | `ai_usage` @310 (310-344) | PURE_READ | routers/extraction.py:310-338 AiUsage query (admin) | missed by `grep @router.get` (admin_router) |
| routers/extraction.py:367 | `/admin/ai/metrics` | `ai_metrics` @368 (368-378) | FOLDER_SCAN PARSES | routers/extraction.py:368-377 -> ai/metrics.py:145-157 summary -> ai/evaluation.py:327-335 latest_reports -> _reports :308-324 (glob *.json :313/:318, read_text :320) | admin; reads evaluation report files; missed by `grep @router.get` |

### fa_interfaces.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/fa_interfaces.py:62 | `/projects/{project_id}/fa-interfaces` | `get_schedule` @63 (63-67) | WRITES FOLDER_SCAN | routers/fa_interfaces.py:63-67 (db.commit :66, comment 'the project's row, made on first read') -> [FA] | NOT in M1 |
| routers/fa_interfaces.py:137 | `/projects/{project_id}/fa-interfaces/runs/latest` | `latest_run` @138 (138-142) | PURE_READ | routers/fa_interfaces.py:138-142 -> interfaces/workflow.py:911 latest, :887 view |  |
| routers/fa_interfaces.py:427 | `/projects/{project_id}/fa-interfaces/export.xlsx` | `export` @428 (428-437) | WRITES FOLDER_SCAN EXPORT_RENDER | routers/fa_interfaces.py:428-436 service.build + db.commit :433 ([FA]) + interfaces/export.py:51 workbook |  |
| routers/fa_interfaces.py:440 | `/projects/{project_id}/fa-interfaces/review-cases.pdf` | `review_cases_pdf` @441 (441-465) | WRITES FOLDER_SCAN EXPORT_RENDER PARSES | routers/fa_interfaces.py:441-465 service.build + db.commit :452 + interfaces/cases_pdf.py:201 build (pymupdf.open; reads stored case pictures via findings.case_folder) |  |
| routers/fa_interfaces.py:468 | `/projects/{project_id}/fa-interfaces/export.pdf` | `export_pdf` @469 (469-481) | WRITES FOLDER_SCAN EXPORT_RENDER | routers/fa_interfaces.py:469-481 service.build + db.commit :476 + interfaces/pdf.py:69 build (pymupdf.open()) |  |

### floor_schedule.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/floor_schedule.py:140 | `/projects/{project_id}/floor-schedule` | `get_floor_schedule` @141 (141-156) | FOLDER_SCAN PARSES WRITES RECONCILES | routers/floor_schedule.py:141-156 -> sync_from_folder :77-84 -> _read_from_folder :87-137: project_folders.design_documents :191-213 (os.scandir of 03- Design), document_sync.sha256_of :140-148 hashes every candidate workbook on every GET (:108), floor_schedule.read :406 (openpyxl parse) when the hash differs OR a newer non-schedule workbook exists (:111-114 `continue`, re-parsed every GET), commit :130; settle_unambiguous :81-82 (services/schedule_materials.py:202-238) commit | M1 row 6. Manual material_choice lost when the workbook is re-read (M1) |
| routers/floor_schedule.py:254 | `/projects/{project_id}/floor-schedule/materials/by-line` | `schedule_material_options` @255 (255-280) | PURE_READ | routers/floor_schedule.py:255-280 device_materials (services/schedule_materials.py:100-145, DB only), rank_for_line | docstring says it avoids the datasheet walk |
| routers/floor_schedule.py:283 | `/projects/{project_id}/floor-schedule/materials` | `schedule_materials` @284 (284-299) | PURE_READ | routers/floor_schedule.py:284-299 device_materials |  |
| routers/floor_schedule.py:415 | `/projects/{project_id}/floor-schedule/export.pdf` | `export_schedule` @416 (416-435) | EXPORT_RENDER | routers/floor_schedule.py:416-435 -> services/schedule_export.py:61 pymupdf.open() |  |
| routers/floor_schedule.py:449 | `/projects/{project_id}/floor-schedule/check` | `check_against_boq` @450 (450-508) | PURE_READ | routers/floor_schedule.py:450-503 compares stored schedule to ProjectBoqItem rows in memory | derived each request |

### ifc_boq.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/ifc_boq.py:157 | `/ifc/capabilities` | `capabilities` @158 (158-168) | FOLDER_SCAN | routers/ifc_boq.py:158-168 -> ifc/dxf/convert.py:69-92 find_converter (glob of %ProgramFiles%/Autodesk/AutoCAD* :78-80, odafc.is_installed :86-88) each call; jobs.worker_running (DB); ai_symbol_review.enabled (probe) | probes the machine's install folders on every call |
| routers/ifc_boq.py:171 | `/ifc/device-types` | `list_device_types` @172 (172-180) | PURE_READ | routers/ifc_boq.py:172-180 (GROUP BY count) |  |
| routers/ifc_boq.py:297 | `/ifc/ai-metrics` | `ai_metrics` @298 (298-325) | PURE_READ | routers/ifc_boq.py:298-324 IfcSymbolReview query + ai/metrics.py:97 usage_metrics (admin) |  |
| routers/ifc_boq.py:381 | `/projects/{project_id}/ifc-drawings` | `list_drawings` @382 (382-401) | PURE_READ | routers/ifc_boq.py:382-401 -> ifc/resolve.py:186 resolved_drawing(with_occurrences=False) per drawing (resolves stored groups against the symbol library, in memory) | recomputed each request, not persisted |
| routers/ifc_boq.py:613 | `/projects/{project_id}/ifc-drawings/{drawing_id}` | `get_drawing` @614 (614-617) | PURE_READ | routers/ifc_boq.py:614-617 -> _resolved :368-378 -> ifc/resolve.py:186 resolved_drawing | recomputed each request, not persisted |
| routers/ifc_boq.py:798 | `/projects/{project_id}/ifc-drawings/{drawing_id}/export` | `export_drawing` @799 (799-817) | EXPORT_RENDER | routers/ifc_boq.py:799-817 -> resolved_drawing + ifc/export.py:14 workbook |  |
| routers/ifc_boq.py:820 | `/projects/{project_id}/ifc-comparison` | `comparison` @821 (821-847) | FOLDER_SCAN PARSES WRITES RECONCILES | routers/ifc_boq.py:821-847: sync_from_folder :829 (routers/floor_schedule.py:77-84 + :87-137, as floor_schedule.py:140) + resolved_drawing per drawing in force (:833) | M1 row 6 consumer path (2) |

### jobs.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/jobs.py:121 | `/projects/{project_id}/jobs` | `list_jobs` @122 (122-129) | PURE_READ | routers/jobs.py:122-129 (BackgroundJob query, limit 20) |  |
| routers/jobs.py:132 | `/jobs/{job_id}` | `get_job` @133 (133-138) | PURE_READ | routers/jobs.py:133-138 |  |

### knowledge.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/knowledge.py:26 | `/admin/knowledge` | `knowledge_status` @27 (27-31) | PURE_READ | routers/knowledge.py:27-31 -> knowledge/importer.py:632-675 |  |
| routers/knowledge.py:56 | `/admin/knowledge/eligibility` | `eligibility_summary` @57 (57-63) | PURE_READ | routers/knowledge.py:57-63 -> knowledge/eligibility.summary (aggregates) |  |
| routers/knowledge.py:66 | `/admin/knowledge/eligibility/review-queue` | `eligibility_review_queue` @67 (67-79) | PURE_READ | routers/knowledge.py:67-79 -> knowledge/eligibility.review_queue |  |
| routers/knowledge.py:98 | `/admin/knowledge/imports/{import_id}` | `import_report` @99 (99-107) | PURE_READ | routers/knowledge.py:99-107 -> importer.import_report |  |

### logs.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/logs.py:53 | `/projects/{project_id}/logs/systems` | `logs_systems` @54 (54-60) | PURE_READ | routers/logs.py:54-60 -> services/shop_drawings.py:953-965 register_systems |  |
| routers/logs.py:90 | `/projects/{project_id}/logs/drawings` | `drawings_register` @91 (91-126) | RECONCILES WRITES | routers/logs.py:91-125: _catch_up :99 ([RECON]) then shop_drawings.register :981 (reads) | M1 row 4 |
| routers/logs.py:129 | `/projects/{project_id}/logs/drawings/export.xlsx` | `export_drawings_register` @130 (130-202) | RECONCILES WRITES EXPORT_RENDER | routers/logs.py:130-194: _catch_up :139 ([RECON]) + openpyxl workbook | M1 row 4 |
| routers/logs.py:205 | `/projects/{project_id}/logs/drawings/{drawing_id}` | `drawing_record` @206 (206-211) | PURE_READ | routers/logs.py:206-211 -> services/shop_drawings.py:889 detail | no catch-up (M1 confirmed) |

### materials.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/materials.py:100 | `/suppliers` | `list_suppliers` @101 (101-112) | PURE_READ | routers/materials.py:101-112 -> services/suppliers.py:39-45 (get :39-41, all_rows :44-45) |  |
| routers/materials.py:183 | `/projects/{project_id}/frc-cables` | `get_frc_cables` @184 (184-194) | PURE_READ | routers/materials.py:184-194 -> services/frc_cables.py:61-62 get (no create-on-read), :108 lines |  |
| routers/materials.py:233 | `/projects/{project_id}/materials` | `list_proposed` @234 (234-278) | FOLDER_SCAN PARSES WRITES RECONCILES | routers/materials.py:234-278: _materials -> routers/submittal.py:148-172 _attach_datasheets -> library.find for every BOQ/added part ([DS]); battery_materials.selected_batteries :262 -> services/battery_materials.py:51-58 -> [BAT] | docstring :241-243 says 'nothing is scanned'; it is (M1 row 8 + row 2 consumer path 3). Mounted by Project Home (frontend ProjectHomePage.tsx:58) |
| routers/materials.py:387 | `/projects/{project_id}/materials/schedule.pdf` | `export_schedule` @388 (388-406) | EXPORT_RENDER FOLDER_SCAN PARSES WRITES RECONCILES | routers/materials.py:388-403 -> services/submittal_package.py:1494-1503 build_schedule -> schedule_blocks :1343 -> selected_batteries :1459 ([BAT]) | docstring says 'From the database; nothing scanned' |
| routers/materials.py:426 | `/parts/search` | `search_parts` @427 (427-435) | PARSES FOLDER_SCAN | routers/materials.py:427-434 -> services/part_catalog.py:125-137 search -> catalog :66-122: read_origin_rows services/submittal_package.py:1824-1839 (openpyxl.load_workbook of the company country-of-origin template, no cache :1838) + _submittal_library() -> services/company_library.py:284-302 (is_dir/holds_documents scandir) + ProjectBoqItem query across ALL projects :111-114 | NOT in M1. Typeahead (frontend ProjectProposedMaterialsPage.tsx:704): an XLSX parse and a library probe per keystroke |

### modules.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/modules.py:15 | `/modules/admin` | `admin_module` @16 (16-17) | PURE_READ | routers/modules.py:16-17 (echoes the token user) |  |
| routers/modules.py:20 | `/modules/design` | `design_module` @21 (21-22) | PURE_READ | routers/modules.py:21-22 |  |
| routers/modules.py:25 | `/modules/viewer` | `viewer_module` @26 (26-27) | PURE_READ | routers/modules.py:26-27 |  |

### project_state.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/project_state.py:75 | `/projects/{project_id}/state` | `project_state_view` @76 (76-88) | RECONCILES WRITES | [ACT]; routers/project_state.py:82-88 -> services/project_state.py:231-262 summary -> :206-228 _shop_drawings_by_system :212-213 -> shop_drawings.reconcile(ai=False) ([RECON]); document_sync.log_records :1578 (index rows) | M1 row 9; also a NEW consumer of M1 row 4 (project_state.py:212-213), mounted by Project Home (ProjectHomePage.tsx:62) |
| routers/project_state.py:91 | `/projects/{project_id}/actions` | `project_actions` @92 (92-94) | RECONCILES WRITES | [ACT] (resolved=true only changes the final query :69-72) | M1 row 9 |
| routers/project_state.py:97 | `/projects/{project_id}/changes` | `project_changes` @98 (98-106) | PURE_READ | routers/project_state.py:98-106 -> services/project_state.py:64-74 changes_since | polled every 5 s per open project (frontend lib/projectChanges.tsx:33,:78) |

### projects.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/projects.py:424 | `/projects` | `list_projects` @425 (425-467) | PURE_READ | routers/projects.py:425-466 (ActivityEvent subquery for scope=mine) |  |
| routers/projects.py:470 | `/projects/{project_id}` | `get_project` @471 (471-479) | WRITES FOLDER_SCAN | routers/projects.py:471-478: activity.record_open (services/activity.py:76-89 -> record :70-72 INSERT ActivityEvent + commit when none in OPEN_WINDOW); _ensure_project_folders :105-116 -> services/project_folders.py:148-172 ensure (stat of each wanted folder :167-168, os.makedirs :170, activity.record for created folders) | M1 row 10. Creates folders on disk on a GET |
| routers/projects.py:634 | `/projects/{project_id}/boq` | `get_project_boq` @635 (635-643) | PURE_READ | routers/projects.py:635-643 project.boq_items |  |
| routers/projects.py:646 | `/projects/{project_id}/boq/export.xlsx` | `export_project_boq` @647 (647-664) | EXPORT_RENDER WRITES | routers/projects.py:647-664: activity.record :655 ([AUDIT]) + services/boq_export.py workbook | audit row on GET |
| routers/projects.py:1065 | `/projects/{project_id}/boq/revisions` | `list_boq_revisions` @1066 (1066-1073) | PURE_READ | routers/projects.py:1066-1073 |  |
| routers/projects.py:1146 | `/projects/{project_id}/boq/revisions/{number}` | `get_boq_revision` @1147 (1147-1154) | PURE_READ | routers/projects.py:1147-1154 |  |
| routers/projects.py:1157 | `/projects/{project_id}/boq/revisions/{number}/export.xlsx` | `export_boq_revision` @1158 (1158-1178) | EXPORT_RENDER WRITES | routers/projects.py:1158-1178: activity.record :1166 + workbook | audit row on GET |
| routers/projects.py:1181 | `/projects/{project_id}/boq/compare` | `compare_boq_versions` @1182 (1182-1206) | PURE_READ | routers/projects.py:1182-1206 compare_boq in memory |  |
| routers/projects.py:1377 | `/projects/{project_id}/logs` | `project_logs` @1378 (1378-1431) | PURE_READ | routers/projects.py:1378-1431: project_state.material_log (services/project_state.py:393-419 -> register_items routers/submittal.py:445-495), document_sync.log_records services/document_sync.py:1578-1642 (index rows; overlays folder-reply status via submittal_replies.for_revision :1626-1635), combine -> document_control.py:2277; sample_board_checks :1446-1463 | M1 row 12. Pure read of stored rows but re-derives status/combines every request; no file opened |
| routers/projects.py:1466 | `/projects/{project_id}/logs/file` | `project_log_file` @1467 (1467-1493) | SERVES_BYTES | routers/projects.py:1467-1493 FileResponse(os.path.isfile :1491) | path-confined; serves the file |

### readiness.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/readiness.py:64 | `/projects/{project_id}/readiness` | `project_readiness` @65 (65-70) | WRITES RECONCILES FOLDER_SCAN PARSES | routers/readiness.py:65-70 -> services/readiness.py:285 evaluate -> _calculations :189-193 -> [BAT]; _compliance :221-248 inputs_of (BOQ/scope hash only) | M1 consumer path (2); Project Home mount (ProjectHomePage.tsx:46-54) |
| routers/readiness.py:73 | `/projects/{project_id}/documents/intake` | `list_intake` @74 (74-81) | PURE_READ | routers/readiness.py:74-80 ProjectDocument rows |  |

### redesign.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/redesign.py:42 | `/projects/{project_id}/redesign` | `drawings` @43 (43-63) | PURE_READ | routers/redesign.py:43-62 (DB rows only) |  |
| routers/redesign.py:66 | `/projects/{project_id}/redesign/{drawing_id}` | `get_redesign` @67 (67-71) | WRITES PARSES | routers/redesign.py:67-71 -> redesign/service.py:1535-1569 view: state() create-on-first-read :70-77 (db.add/flush), db.commit :1545, and review.build :1541-1544 (review/service.py:593; _fit may parse DXF/PDF + commit) | NOT in M1 |
| routers/redesign.py:162 | `/projects/{project_id}/redesign/{drawing_id}/changes/{change_id}/image` | `change_image` @163 (163-172) | PARSES | routers/redesign.py:163-172 -> redesign/service.py:1342-1364 image (pymupdf.open :1361 + redesign/prepare columns); service.state :167 creates a row (flush, not committed) | browser cache 600 s |
| routers/redesign.py:175 | `/projects/{project_id}/redesign/{drawing_id}/output.dwg` | `output` @176 (176-187) | SERVES_BYTES | routers/redesign.py:176-187 FileResponse(row.output_path :180-185) | serves the made DWG; state() flush not committed |
| routers/redesign.py:190 | `/projects/{project_id}/redesign/{drawing_id}/markup.pdf` | `draftsman_pdf` @191 (191-198) | EXPORT_RENDER PARSES | routers/redesign.py:191-198 -> redesign/service.py:1367-1386 draftsman_pdf -> redesign/markup.py:34 build (pymupdf.open + the plotted PDF) |  |

### register.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/register.py:104 | `/register/revision` | `register_revision` @105 (105-119) | PURE_READ | routers/register.py:105-119 -> services/project_register.py:352-364 revision (path.stat of the register workbook) | a stat, by design (docstring :109-113); polled by the page |
| routers/register.py:122 | `/register/projects` | `list_register_projects` @123 (123-201) | PARSES FOLDER_SCAN | routers/register.py:123-201 -> services/project_register.py:220-237 projects: stat :229, _read :170-172 openpyxl load_workbook only when mtime/size changed | cached in memory by (mtime,size) |

### shop_boq.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/shop_boq.py:59 | `/projects/{project_id}/shop-boq` | `get_shop_boq` @60 (60-77) | WRITES | routers/shop_boq.py:60-76: when no row exists, shop_boq.make (services/shop_boq.py:166-198: resolved_drawing per IFC drawing via drawings_in_force :41-55, build, db.add :189, settle_unambiguous :195, db.commit :196) + activity.record :75 | NOT in M1. 'The first time it is asked for it starts as the BOQ as per IFC' (docstring :64-65) |
| routers/shop_boq.py:163 | `/projects/{project_id}/shop-boq/materials/by-line` | `material_options` @164 (164-182) | PURE_READ | routers/shop_boq.py:164-182 device_materials, rank_for_line |  |
| routers/shop_boq.py:185 | `/projects/{project_id}/shop-boq/export.pdf` | `export_pdf` @186 (186-201) | EXPORT_RENDER | routers/shop_boq.py:186-200 -> services/schedule_export.py:61 |  |

### submittal.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/submittal.py:175 | `/projects/{project_id}/submittal/materials` | `list_materials` @176 (176-189) | FOLDER_SCAN PARSES | routers/submittal.py:176-189 -> _materials :112-145 -> _attach_datasheets :148-172 -> library.find per part ([DS]) | M1 row 13/8. This route is also the 'materials' leg of the register |
| routers/submittal.py:498 | `/projects/{project_id}/submittals` | `list_submittals` @499 (499-563) | FOLDER_SCAN PARSES | routers/submittal.py:499-563: _materials :505 ([DS]); register_items :445-495 (_filed_in_the_folder :362-442 re-derives submittals from index rows; folder-letter reply overlay :479-495 via submittal_replies.for_revision); _storage :291-315 (iterdir :301 + one-level iterdir per subfolder :308, stat :309) | M1 row 13 |
| routers/submittal.py:873 | `/projects/{project_id}/submittals/map` | `submittal_map` @874 (874-890) | PURE_READ | routers/submittal.py:874-890: submittal_reader.available (ai/submittal_reader.py:196-210 -> [PROBE], evaluation.switched_off), latest_map :580-587, _as_the_register_stands :824-868 (overlays register status on the stored AI map) | model availability probe only; comment :884-886 says the folder is never checked on open |
| routers/submittal.py:955 | `/projects/{project_id}/submittals/{reference}/{revision}/reply` | `get_submittal_reply` @956 (956-985) | PARSES | routers/submittal.py:956-985 -> _consultant_words :925-952 (only when no SubmittalReply is saved :970-971) -> services/submittal_replies.py:89-116 words_of (pymupdf.open :108, up to 4 pages of the filed reply scan) | M1 row 14 |
| routers/submittal.py:1025 | `/projects/{project_id}/submittals/{reference}/{revision}/reply.xlsx` | `export_submittal_reply` @1026 (1026-1051) | EXPORT_RENDER PARSES WRITES | routers/submittal.py:1026-1051: get_submittal_reply :1035 (as submittal.py:955) + reply_sheet.workbook + activity.record :1046 ([AUDIT]) | audit row on GET |
| routers/submittal.py:1054 | `/projects/{project_id}/submittals/{reference}/{revision}/reply.pdf` | `export_submittal_reply_pdf` @1055 (1055-1085) | EXPORT_RENDER PARSES WRITES | routers/submittal.py:1055-1085: get_submittal_reply :1069 + services/reply_sheet.py:194 pdf + activity.record :1080 | audit row on GET |
| routers/submittal.py:1088 | `/projects/{project_id}/submittals/export.xlsx` | `export_submittals` @1089 (1089-1109) | EXPORT_RENDER FOLDER_SCAN PARSES WRITES | routers/submittal.py:1089-1109: activity.record :1097 + _materials :1099 ([DS]) + submittal_export workbook | audit row on GET |
| routers/submittal.py:1114 | `/projects/{project_id}/submittals/folder` | `submittal_folder` @1115 (1115-1121) | PURE_READ | routers/submittal.py:1115-1121 os.path.isdir(project.source_folder_path) | single stat |
| routers/submittal.py:1290 | `/projects/{project_id}/submittal/package/plan` | `package_plan` @1291 (1291-1308) | FOLDER_SCAN PARSES WRITES RECONCILES | routers/submittal.py:1291-1304 -> _plan_for :1202-1229: get_libraries ([DS]), _specs_for :1141-1180 (stored specs else find_specs :1158 = rglob+PDF opens), _battery_panels :1183-1199 (call :1195) -> [BAT], services/submittal_package.py:521 plan_package (_battery_datasheets :478-496 -> selected_batteries; _pdfs_in library folder :611) | creator roles; consumer paths (4)/(5) of M1 battery row; second caller of spec discovery |

### users.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/users.py:19 | `/users` | `list_users` @20 (20-21) | PURE_READ | routers/users.py:20-21 |  |
| routers/users.py:205 | `/users/{user_id}/account` | `user_account` @206 (206-209) | PURE_READ | routers/users.py:206-209 |  |
| routers/users.py:212 | `/users/{user_id}/activity` | `user_activity` @213 (213-221) | PURE_READ | routers/users.py:213-221 |  |
| routers/users.py:224 | `/users/{user_id}/account/export.xlsx` | `export_user_account` @225 (225-226) | EXPORT_RENDER | routers/users.py:225-226 -> :189-195 account_export |  |

### verification.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/verification.py:126 | `/projects/{project_id}/ai-verification` | `get_verification` @127 (127-132) | PURE_READ | routers/verification.py:127-132 -> _state :75-83: verification.available (ai/verification.py:381-388) -> [PROBE] | model availability probe only. The sibling POST /ai-verification/ensure (verification.py:135-153) is the mount-time job starter, see Table B N7 |

### divisions.py (and divisions factory)

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| routers/divisions.py:15 | `/{fire-fighting\|elv}/projects` | `list_projects` @16 (16-17) | PURE_READ | routers/divisions.py:16-17 (registered twice: /fire-fighting/projects and /elv/projects, divisions.py:43-44) | factory decorator, missed by `grep @router.get` |
| routers/divisions.py:32 | `/{fire-fighting\|elv}/projects/{project_id}` | `open_project` @33 (33-37) | PURE_READ | routers/divisions.py:33-37 (registered twice) | factory decorator, missed by `grep @router.get` |

### main.py

| router:line | path | handler | classes | evidence | notes |
|---|---|---|---|---|---|
| main.py:278 | `/health` | `health` @279 (279-295) | PURE_READ | main.py:279-295 -> workers/runtime.py:67-83 _git_revision reads .git/HEAD (2 tiny file reads) | not under backend/app/routers; unauthenticated |

## 5. Table B - read-time producers: M1's 14 and everything not in M1

Status vocabulary: STILL PRESENT (same mechanism, anchors re-found), CHANGED (mechanism or reach differs), REMOVED (none found). M1's line anchors moved with later edits; the current anchors are given.

### B1. M1's 14 producers (M1 order)

| # | M1 producer | Status | Current evidence | What changed / notes |
|---|---|---|---|---|
| 1 | BOQ mount auto-POST /boq/ensure | CHANGED (worse) | frontend/src/pages/ProjectBoqPage.tsx:221-223 (canEdit -> POST); backend/app/routers/projects.py:761-812 ensure_project_boq (M1 @758), :815-825 _needs_ai_read (M1 @811), :828-857 _start_boq_read (jobs.start :855; M1 @824), :860-973 _extract_boq (M1 @856) | Still a POST fired by page mount, not a GET. New: projects.py:892-906 returns without stamping boq_extracted_at when no sheet was attempted (model off/unavailable, file missing), so every editor open re-enters _extract_boq and may write an ExtractionRun per distinct reason (commit :905). M1's 'boq_extracted_at is null' condition now holds indefinitely in that state. |
| 2 | Battery calculation persistence (one producer, six consumer paths) | STILL PRESENT; consumer set widened | Producer routers/design.py:410-586 _battery_calculation (write :511-526, M1 @410 unchanged). GET consumers: design.py:300-315 (call :308), :704-726 (:713) and :730 (:743) exports; services/readiness.py:189-218 (:193) via GET /readiness; services/battery_materials.py:51-80 (:58) via GET /projects/{id}/materials (materials.py:262); services/submittal_package.py:493 (_battery_datasheets in plan_package) and :1459 (schedule_blocks via build_schedule) via GET /materials/schedule.pdf (materials.py:387) and GET /submittal/package/plan; routers/submittal.py:1183-1199 (:1195) via package_plan (:1291) | M1 listed six consumer paths; the code now has nine call sites reached by seven GET handlers (design.py:299/703/729, materials.py:233/387, readiness.py:64, submittal.py:1290) plus POST build. Additional cost not in M1: design.py:415 `_selectable_batteries` -> `library.batteries()` (datasheet_library.py:466-473) triggers the datasheet-library discovery/refresh on every battery calculation (see row 8). |
| 3 | Battery mount auto-POST fill-currents | STILL PRESENT | frontend/src/pages/ProjectBatteryPage.tsx:113 (POST), :128-137 (once per visit when canEdit and a panel has missing_parts); backend/app/routers/design.py:319-407 fill_battery_currents | unchanged |
| 4 | Drawings / Logs GET catch-up reconciliation | STILL PRESENT; one new consumer | routers/drawings.py:81-86 _catch_up -> services/shop_drawings.py:718-723 needs_reconcile, :144-234 reconcile(ai=False). Entry points: drawings.py:112-119 (summary, call :116), _log :89-90 (log :123, export :139), :195 (issues, call :198), :210 (floors, call :215); logs.py:99, :139 (drawings_register, export). NOT drawing_detail (:334) and not logs.drawing_record (:206). NEW consumer: services/project_state.py:206-228 _shop_drawings_by_system (:212-213) reached by GET /state (routers/project_state.py:76-88) | M1 omitted the /state path although it existed at e49c2bf (`git show e49c2bf:backend/app/services/project_state.py` line 211). Project Home mounts /state (ProjectHomePage.tsx:62) and re-reads on every 'drawing'/'action'/'submittal'/'documents' change event (:72-75). |
| 5 | Compliance statement recheck on read | STILL PRESENT | routers/compliance.py:522-529 get_statement -> _statement_out :424-427 -> compliance/service.py:1052-1113 recheck (commits :1067, :1111; current_spec_sha :1005-1031); `_approved_statement` :791-799 (recheck call :794) used by GET exports :803 and :824; list_statements :507 does not recheck | unchanged. Exports additionally write an audit row (compliance.py:812, :833). |
| 6 | Floor Schedule discovery/parse/save (one producer, two consumers) | STILL PRESENT; cost detail added | routers/floor_schedule.py:77-84 sync_from_folder (settle commit :81-82), :87-137 _read_from_folder (commit :130); consumers GET /floor-schedule (:141-156) and GET /ifc-comparison (routers/ifc_boq.py:821-847, call :829) | Beyond M1: every GET hashes every candidate workbook in full (floor_schedule.py:108 -> services/document_sync.py:140-148) after listing 03- Design (services/project_folders.py:191-213), and a newer workbook that is not a floor-wise schedule is re-parsed on every GET (:111-114 `continue`). |
| 7 | Compliance specification discovery and PDF reads | STILL PRESENT; second caller | routers/compliance.py:164-206 _specs (find_specs :187, _verify_matches :201 -> :209-233, _store_specs :155-161 commit :161), :100-128 _uploaded_specs (opens every uploaded PDF each GET: pymupdf.open :115), :135-152 _stored_specs, GET :260-284; services/spec_finder.py:343-439 find_specs (rglob :362, PDF opens :377/:409/:430, zip :384-393) | Second caller not in M1: routers/submittal.py:1141-1180 _specs_for (find_specs :1158 when no stored search) via GET /submittal/package/plan. `?refresh=true` is a query flag on a GET (compliance.py:262). |
| 8 | Shared datasheet lookup refresh/index/cache writes | STILL PRESENT; reach widened | services/datasheet_library.py:311-348 _refresh (interval library_rescan_seconds=60, core/config.py:325 and datasheet_library.py:534; rglob :324, stat :334, _index_file :339 -> pymupdf.open :210, _save_cache :347 writes a .json.gz); :419-464 find; :466-473 batteries; per-call discovery services/company_library.py:248-281 (iterdir :260, holds_documents :266 -> scandir :228) via get_libraries :540-569 | Reached by 16 GET handlers through refresh (design.py:299/703/729; design_rules.py:54/264/294/350/394/457; materials.py:233/387; readiness.py:64; submittal.py:175/498/1088/1290) and by 18 through discovery (plus design_rules.py:502/521). The first lookup after a restart loads the worker's cache file (main.py:100-102 comment); the API process still rescans every 60 s. |
| 9 | Project state / actions GET reconciliation | STILL PRESENT | routers/project_state.py:57-72 _actions (commit :64), :75-88 state, :91-94 actions; services/project_state.py:323-355 reconcile_actions (add :337, flush :354) | unchanged. /actions?resolved=true runs the same reconcile first. |
| 10 | Project-open folder provisioning and open telemetry | STILL PRESENT | routers/projects.py:471-479 get_project -> activity.record_open (services/activity.py:76-89 -> record :45-73) and _ensure_project_folders :105-118 -> services/project_folders.py:148-172 ensure (os.makedirs :170) | unchanged (M1 @467/@101 moved +4). |
| 11 | Frontend summary/status derivation | STILL PRESENT | frontend/src/pages/ProjectHomePage.tsx:399 bucket, :408 summarise, used at :88-90 over the /logs rows | Home also loads backend-derived state (/state, :62), so two derivations of the same statuses feed one page. |
| 12 | Samples derivation on read | STILL PRESENT | routers/projects.py:1378-1431 project_logs, :1446-1463 sample_board_checks; services/document_sync.py:1578-1642 log_records; services/document_control.py:2277 combine | unchanged; no file is opened (index rows only). |
| 13 | Submittal materials/storage listing | STILL PRESENT | routers/submittal.py:291-315 _storage (iterdir :301, per-folder iterdir :308, stat :309), :148-172 _attach_datasheets, GET :176 and :499 | unchanged; both go through the datasheet refresh (row 8). |
| 14 | Reply editor reads the filed reply PDF | STILL PRESENT; wider trigger | routers/submittal.py:956-985 get_submittal_reply -> :925-952 _consultant_words (:970-971 only when no reply saved) -> services/submittal_replies.py:89-116 words_of (pymupdf.open :108) | GET reply.xlsx (:1035) and GET reply.pdf (:1069) call get_submittal_reply, so each export can open the filed scan; M1 treated exports as outside the count. |

### B2. Read-time producers not in M1's 14

`Era`: ADDED-AFTER = the router/file is absent from e49c2bf (M1's closure commit); IN-M1-SNAPSHOT = present at e49c2bf but unlisted by M1.

| # | Producer | Era | Classes | Chain and evidence |
|---|---|---|---|---|
| N1 | GET /projects/{id}/fa-interfaces and its three exports | ADDED-AFTER | WRITES, FOLDER_SCAN | routers/fa_interfaces.py:63-67 (commit :66 'the project's row, made on first read'); interfaces/service.py:181-187 state creates ProjectFaInterfaces; interfaces/service.py:797-843 build -> interfaces/evidence.py:166-185 take (os.scandir :176) -> :109-163 _walk (os.walk :123, stat only); exports commit at :433, :452, :476 |
| N2 | GET /projects/{id}/draftsman | ADDED-AFTER | WRITES, FOLDER_SCAN, PARSES, RECONCILES | routers/draftsman.py:27-38 _view (commit :30); services/draftsman_assignment.py:73-79 state creates the row; :205-233 items runs seven checks: drawing_requirements.status (os.walk, services/required_drawings.py:88-101), interfaces.service.build (N1), review.service.build per review row (:142; review/service.py:593-597 _fit may parse DXF+PDF and commit), amplifier _out/_power recomputation (:152-184) |
| N3 | GET /projects/{id}/drawing-review/{id} and exports | ADDED-AFTER | WRITES, PARSES | routers/drawing_review.py:55-60 (commit :59); review/service.py:49-57 state creates ProjectDrawingReview; :537-554 _fit -> review/geometry.py:79-105 fit_sheets (ezdxf.readfile + pymupdf.open of the plotted PDF) when a sheet lacks the current geometry version; commit :596. export/markup call build again (:189, :241) |
| N4 | GET /projects/{id}/redesign/{id} | ADDED-AFTER | WRITES, PARSES | routers/redesign.py:67-71; redesign/service.py:1535-1569 view: state creates ProjectRedesign (:70-77), commit :1545, review.build :1544 (as N3) |
| N5 | GET /projects/{id}/shop-boq (create on first read) | ADDED-AFTER | WRITES | routers/shop_boq.py:60-76; services/shop_boq.py:166-198 make (resolved_drawing per IFC drawing via drawings_in_force :41-55, db.add :189, settle_unambiguous :195, commit :196) and activity.record :75. A read that builds the project's shop BOQ from the IFC drawings the first time anyone opens the tab |
| N6 | GET /parts/search (typeahead) | IN-M1-SNAPSHOT | PARSES, FOLDER_SCAN | routers/materials.py:427-434 -> services/part_catalog.py:125-137 search -> :66-122 catalog -> services/submittal_package.py:1824-1852 read_origin_rows (openpyxl.load_workbook :1838, no cache) + services/company_library.py:284-302 submittal_folder (is_dir/holds_documents) + ProjectBoqItem query over all projects :111-114. frontend/src/pages/ProjectProposedMaterialsPage.tsx:704 calls it as the user types |
| N7 | Mount POST /projects/{id}/ai-verification/ensure | IN-M1-SNAPSHOT | JOB_ENQUEUE, MODEL_CALL (via job) | frontend/src/components/AiVerificationPanel.tsx:75 (canEdit -> POST on mount; panel used at ProjectBoqPage.tsx:758 and ProjectInfoPage.tsx:79,:148); routers/verification.py:135-153 ensure_verification -> _start :86-125 (jobs.start :123) when ai_verify_auto (default True, core/config.py:350), no prior check exists and the model is available. Not a GET, but M1 counted mount-time POSTs (rows 1 and 3) and missed this one |
| N8 | GET /projects/{id}/drawings/required and /required/export.xlsx | IN-M1-SNAPSHOT | FOLDER_SCAN | routers/drawings.py:534-541 -> services/drawing_requirements.py:80-124 status -> services/required_drawings.py:88-101 _files (os.walk), :105-146. M1 mentions this only as an inference path ('file presence', required_drawings.status@90), not as a read-time producer |
| N9 | Exports that write on GET | IN-M1-SNAPSHOT | WRITES (audit rows), plus the producer each export triggers | activity.record (services/activity.py:45-73) from projects.py:655 and :1166 (BOQ), design.py:717 and :744 (battery), submittal.py:1046, :1080, :1097, compliance.py:812 and :833 (the last two after recheck N5/row 5). M1 excluded exports as explicit actions; they are GET routes |
| N10 | Datasheet proposals scan | IN-M1-SNAPSHOT | PARSES (compute) | routers/design_rules.py:55-78 -> services/datasheet_library.py:392-417 candidate_parts for every sheet of every library on every request (regex over every indexed page text) |
| N11 | On-demand page renders on GET | IN-M1-SNAPSHOT / ADDED-AFTER | PARSES | datasheet thumbnail design_rules.py:522-550 (pymupdf.open :542); BOQ line/candidate evidence boq_review.py:262-281 and extraction.py:199-213 (-> ai/evidence.py:77-94: opens the PDF and rasterises the whole page :82-83 per image; sha256 of the Design Sheet first in boq_review.py:269); drawing-review image review/service.py:1029-1045; redesign change image redesign/service.py:1342-1364. M1 treats evidence renders as explicit; they are GET routes with no stored image |
| N12 | Extraction view hashes source documents | IN-M1-SNAPSHOT | FOLDER_SCAN | routers/extraction.py:165-188 -> ai/sheet_reader.py:266-283 readings_for (SHA-256 of every Design Sheet :274 and the DRF :280, extraction/pipeline.py:60-70) and eval report glob per issue (ai/evaluation.py:308-324 via extraction/issues.py:164-173, ai/evaluation.py:338-342) |
| N13 | Other folder probes | IN-M1-SNAPSHOT | FOLDER_SCAN | design.py:170-190 os.walk of the whole project folder; compliance.py:845 -> compliance/references.py:52-59 os.walk of project + uploads folders; ifc_boq.py:158 -> ifc/dxf/convert.py:69-92 glob of Program Files/Autodesk each call; backups.py:49-50; register.py:105-119 and project_register.py:220-237 (stat + xlsx parse on change); archive.py:93 (stat of archive root); archive search/status conditional commit services/ep_directory.py:180-182 |
| N14 | Read -> change event -> re-read loop | IN-M1-SNAPSHOT (projectChanges.tsx and useOnProjectChange exist at e49c2bf) | WRITES that trigger re-reads | writers inside GETs emit ProjectChange rows (services/project_state.py:51-55 record_change from reconcile_actions :337/:341/:349 and shop_drawings.reconcile :232); frontend/src/lib/projectChanges.tsx:33,:78 polls /changes every 5 s and ProjectHomePage.tsx:72-75 reloads /readiness,/logs,/materials,/state on those events. UNKNOWN whether it converges in practice: not exercised (static audit); each reload re-runs the producers in B1 rows 2, 4, 8, 9 |

## 6. Table C - duplicate producers of the same fact

### C1. M1's nine groups

| # | Fact | Status | Current callers (file:line) | Notes |
|---|---|---|---|---|
| 1 | Document type inference | STILL PRESENT (6 of 6) | services/document_sync.py:172 classify_text; services/document_classification.py:325 hint; services/document_control.py:1284 parse_page; services/content_evidence.py:147 scan_pdf; services/spec_finder.py:136 looks_like_a_spec; ai/submittal_reader.py:254 looks_like_a_form | anchors shifted only |
| 2 | Reference / identity | STILL PRESENT | services/document_control.py:521 reference_candidates, :803 submission_cover; services/submittal_scanner.py:37 _REFERENCE_RE (used :175); ai/submittal_reader.py:335 _reference; services/shop_drawings.py:506 _reference_shape; services/transmittals.py:220 number; services/submittal_identity.py:49 submittal_key; services/boq_provenance.py / part_catalog.py:66 | unchanged |
| 3 | Revision | STILL PRESENT (6 helpers) | services/document_control.py:2410 _revision_number; services/transmittals.py:220 number; services/project_state.py:80 _number; services/drawing_log.py:156 _rev_number; services/submittal_filing.py:158 _revision_number; services/shop_drawings.py:73 _rev | unchanged |
| 4 | System code | STILL PRESENT | services/document_control.py (SYSTEMS + infix rules); services/document_classification.py; services/transmittals.py:84 systems_of; services/submittal_scanner.py (FOLDER_SYSTEMS); ai/submittal_reader.py:431 _system_code; services/system_rules.py:137 effective_code; services/shop_drawings.py:77 reference_system | unchanged |
| 5 | Consultant decision / status | STILL PRESENT | services/document_control.py:1162 read_decision, :1060 boxed_decision, :1070 annotated_decision, :1806 read_open_pdf; services/submittal_replies.py:65 for_revision; ai/submittal_reader.py:666 sync_register; services/project_state.py:86 cell_code, :98 _state_of, :170-203 _documents_by_system; services/drawing_log.py:427 after_approval; services/shop_drawings.py:237 _reconcile_system, :654 _apply_reply; frontend ProjectHomePage.tsx:399 bucket | unchanged; see C2-1 and C2-3 for the read-time copies |
| 6 | Reply linkage | STILL PRESENT | services/document_control.py:2277 combine, :1806 read_open_pdf, :2173 _answers; services/submittal_replies.py:119 apply_to, :190 answers_another_revision, :205 carried_over; services/shop_drawings.py:592 _ai_review, :654 _apply_reply; ai/submittal_reader.py:666 | unchanged |
| 7 | Freshness | STILL PRESENT; more keys | M1's nine keys remain (DocumentDependency; classification freshness services/document_classification.py:806-822; BatteryPanelResult.input_hash design.py:511-513; Project.spec_locations/specs_found_at compliance.py:155-161; drawings_reconciled_at vs documents_synced_at shop_drawings.py:718-723; boq_version/details_version; ProjectFloorSchedule.source_sha256 floor_schedule.py:108-110; AiVerification.stale routers/verification.py:66; statement inputs compliance/service.py:177-181, :1052-1113). Added since: FA interface evidence digest (interfaces/evidence.py digest, interfaces/service.py:833), review geometry version (review/service.py:538-540), datasheet cache mtime/size (datasheet_library.py:336-339), register workbook (mtime,size) cache (services/project_register.py:229-233), evaluation report stamp (ai/evaluation.py:313-316) | each owner still keeps its own; none shared |
| 8 | Drawings register vs legacy logs drawings | STILL PRESENT | services/shop_drawings.py:821 log, :981 register; routers/projects.py:1378-1431 project_logs (drawings via document_sync.py:1578-1642 log_records -> document_control.py:2277 combine); services/drawing_log.py:337 _by_floor | Home still mounts /logs (ProjectHomePage.tsx:57) beside /state (:62) |
| 9 | Material submittal status views | STILL PRESENT | register ProjectSubmittal via routers/submittal.py:445-495 register_items; map overlay routers/submittal.py:824-870 _as_the_register_stands (changed since M1: now overwrites a cell with the register status whenever the register holds the revision, :858-864, 'NS' included); services/project_state.py:393-420 material_log, :122-148 materials_by_system, :151-164 material_approval; ProjectHomePage.tsx:399 | one behavioural change in the overlay (git diff e49c2bf HEAD -- backend/app/routers/submittal.py) |

### C2. Duplicate producers found in this audit (not in M1's nine)

| # | Fact | Producers (file:line) | Read-time consequence |
|---|---|---|---|
| 1 | Drawing status (approved / under review / returned) derived in log code and in drawings code | (a) services/drawing_log.py:427 after_approval (used :622) and services/document_control.py:2277 combine, feeding the legacy /logs drawings (routers/projects.py:1378-1431); (b) services/project_state.py:179-186 re-implements the same after-approval rule inside _documents_by_system (:170-203; comment at :183 names drawing_log.after_approval) and :206-228 _shop_drawings_by_system derives a third state from shop_drawings.summary counts (:215-224); (c) services/shop_drawings.py:237 _reconcile_system / :654 _apply_reply write revision status into ProjectShopDrawingRevision, read by log :821 and summary :870; (d) frontend ProjectHomePage.tsx:399 bucket | Project Home shows the status from (a)+(d) on the Logs tab and from (b) on the system board in the same view; a divergence between the legacy records and the register is visible as two answers |
| 2 | Floors of a building derived in several places | services/floors.py:82 floor_of; services/building_floors.py:180 floors_from_ifc, :134 resolve_aliases, :218 floor_from_shop_drawing; services/drawing_log.py:142 floor_identity, :195 floor_label, :337 _by_floor; ifc/comparison.py:46 floor_key (also used by services/shop_boq.py:68-75); ifc/resolve.py:33 name_floor, :49 floor_sheets; ifc/dxf/sheets.py:212 identify_floor (also review/service.py:1025); interfaces/service.py:695 class Floors; floor names from the workbook in services/floor_schedule.py | Seven independent floor-key rules; the BOQ Floor Wise, the BOQ as per Shop Drawings, the Drawings log, the interface schedule and the review each decide which sheet is which floor. M1 named only drawing_log._by_floor |
| 3 | Submittal status from the consultant's reply: folder-letter scan vs reply sheet vs AI map vs register | folder letter/phrases: services/submittal_replies.py:65-78 for_revision, applied at routers/submittal.py:419 (_filed_in_the_folder), :479-495 (register_items overlay) and services/document_sync.py:1626-1635 (log_records overlay); AI map cell: ai/submittal_reader.py:666 sync_register, overlaid back onto the register at routers/submittal.py:824-870; consultant words: services/submittal_replies.py:43-62 on_file (stored form evidence) vs :89-116 words_of (re-reads the scan) vs the saved SubmittalReply rows (routers/submittal.py:956-985); frontend bucket :399 | Three read-time overlays re-derive a status for the same revision on every /submittals, /logs and /state read; reply words have three sources |
| 4 | Part current figures (battery) kept in two stores | DesignRule PART_CURRENT_CATEGORY (read routers/design.py:436-440 via active_rules; written routers/design_rules.py:160-183 save_part_current -> save_rule_version :115-151) and the EquipmentCurrent table (read routers/design.py:543-549 settled_keys; written by equipment_currents.upsert at design_rules.py:178 and by fill_battery_currents design.py:402) | one save writes both; the battery calculation reads both on every call (and writes BatteryPanelResult) |
| 5 | Specification discovery has two callers | routers/compliance.py:164-206 _specs and routers/submittal.py:1141-1180 _specs_for, sharing compliance._stored_specs :135-152 and services/spec_finder.py:343-439 find_specs | the package plan can start the project-folder search that the compliance page also starts; stored result is shared, uploads are not (uploads re-listed on every compliance GET only) |
| 6 | Which datasheet documents a part | routers/submittal.py:148-172 _attach_datasheets (link first, then library.find); routers/design.py:284-296 _unresolved_reason (library.find); routers/design_rules.py:458-499 find_datasheets (equipment table -> link -> find); services/equipment_currents.py:186-194 mapped_match; services/datasheet_links.py:40-55 lookup; services/submittal_package.py:611 plan (_pdfs_in); design.py:644-662 battery sheets by reading each datasheet | four lookup orders; each re-runs the library refresh (M1 row 8) |
| 7 | 'IFC drawings counted' (in force, answers complete, others pending) | services/shop_boq.py:41-55 drawings_in_force; routers/ifc_boq.py:832-840 (comparison); routers/ifc_boq.py:382-401 (list_drawings 'ready' via review.required) | same split coded three times; shop_boq.py:42-43 says it is 'as the Comparison tab takes them' |
| 8 | Line -> proposed material (settling) and BOQ source for schedules | services/schedule_materials.py:202-238 settle_unambiguous called from routers/floor_schedule.py:81 (on GET), :225 and services/shop_boq.py:195; routers/amplifier.py:101-107 _source chooses ProjectShopBoq else ProjectFloorSchedule; ProjectBoqItem is a third quantity source (floor_schedule.py check :450-503) | the same fact (which part a schedule line is) is written into two tables, and three BOQs feed the amplifier, power, draftsman and comparison reads |
| 9 | 'Is the project ready' / open work lists | services/readiness.py:285-302 evaluate (+ boq_blockers); services/draftsman_assignment.py:205-233 items (re-derives interfaces, review, APS, BPS, required documents); services/project_state.py:323-355 reconcile_actions (actions); services/drawing_issues.py:52 reconcile (drawing issues, called in shop_drawings.py:222); ai/submittal_reader.py build_map actions copied by routers/submittal.py:824-870 | four to-do lists derived from overlapping inputs, two of them (actions, drawing issues) reconciled on read |

## 7. Unknowns

| Item | Reason it is UNKNOWN |
|---|---|
| Whether any GET reaches `document_control.combine` (services/document_control.py:2277-2407) with file I/O | Read as a source segment: no open/stat/commit tokens in its body; its callees (drawing_key, _answers :2173) were not each read. |
| Full transitive cost of `ifc/resolve.py:186-285 resolved_drawing` (called per drawing by ifc_boq.py:388, :833, shop_boq.py:48, battery-independent) | Scanned for commit/IO tokens (none); computation size on large drawings not measured. Static audit only. |
| `interfaces/service.py` `_assemble` :947-1019, `coverage` :2127-2150 and the Floors class :695-796 | Scanned for commit/IO tokens (none); behaviour beyond that not read line by line. |
| Whether Project Home's read -> ProjectChange -> re-read loop converges (Table B2 N14) | Needs a running system; this audit did not call endpoints or run jobs. |
| Exact number of PURE_READ handlers that touch no file at all | The call graph (scratchpad m1r/cg.py) is name-based: method calls on objects resolve only when the name is unique in the codebase, so PURE_READ rows were confirmed by reading the handler and its first-level callees plus an AST token scan of the named helpers (commit/add/flush/open/stat/glob/hashlib), not every transitive method. |
| `services/activity.py:140-272 account` and `knowledge/eligibility.py:58-97`, `:100-142` | AST token scan clean for writes and file I/O; not read in full. |
| Which GET calls are slow in practice (cost ranking in section 3 is by what each chain does, not by measurement) | No timing was taken; code comments (services/schedule_materials.py:106-108 'takes minutes', services/datasheet_library.py:229-231 '86 datasheets ... eleven seconds off a synced drive') are the only cost evidence. |
| Which frontend pages call each GET, and how often | Only the Home, BOQ, Battery, Logs, Compliance, Materials and Info mounts were traced (grep of `api.get`, `setInterval`); the remaining handlers' callers and call frequency were not enumerated. |

## 8. Commands used

All read-only. Working directory /home/user/Design_Platform unless noted.

```
git rev-parse --short HEAD
git log --oneline | wc -l ; git log -1 --format='%h %ad %s' ; git log --diff-filter=A --format='%h %ad %s' --date=short -- <file>
git diff --stat e49c2bf HEAD -- backend/app ; git diff --name-status e49c2bf HEAD -- backend/app/routers backend/app/main.py
git diff e49c2bf HEAD -- backend/app/routers/projects.py ; git diff e49c2bf HEAD -- backend/app/routers/submittal.py
git cat-file -e e49c2bf:<path> (verification.py, AiVerificationPanel.tsx, M1 doc, amplifier.py) ; git show e49c2bf:backend/app/routers/materials.py | grep -n "parts/search" ; git show e49c2bf:backend/app/services/project_state.py | grep -n "shop_drawings.reconcile"
ls backend/app/routers | wc -l
grep -c "@router.get" backend/app/routers/*.py   (summed: 144)
grep -n "@router.get" backend/app/routers/*.py   (via scratchpad list.py: decorator line, path, handler)
grep -rn "api_route\|add_api_route\|@app\.get\|methods=\[" --include=*.py backend/app
grep -rnE "@\w+\.get\(" --include=*.py backend | grep -v "@router.get"      (found admin_router x2, routes x2, @app.get /health)
grep -rn "mount(" backend/app/main.py ; grep -n "include_router" backend/app/main.py
grep -rn "\.complete(" --include=*.py backend/app ; grep -rn "jobs.enqueue\|jobs.start(\|start_background_scan\|start_import(\|threading.Thread(" --include=*.py backend/app/routers
grep -rnE "^\s*(import|from) (fitz|pdfplumber|pypdf|openpyxl|ezdxf|pytesseract|PIL|numpy|anthropic|zipfile)" and grep -rniE "import (pymupdf|fitz)|subprocess" --include=*.py backend/app   (parser inventory)
grep -n for each M1 anchor (function names) in services/, routers/, ai/, frontend/src/pages/*.tsx
grep -rn "ensure\|fill-currents" frontend/src ; grep -rn "api.get" frontend/src (Home mount calls) ; grep -rn "setInterval" frontend/src
sed -n / cat -n of every handler body and of the helpers cited in the tables
python3 -I <scratchpad>/m1r/cg.py        AST call graph over backend/app (effects: commit/add/flush/delete, glob/rglob/iterdir/scandir/walk/stat, open/read_*, pymupdf/openpyxl/ezdxf/zipfile, app.ai entry) -> cg.json, then show.py / reach.py to print chains
python3 -I <scratchpad>/m1r/spans.py ; vtok.py ; sp.py      (checks every cited file:A-B span against the AST function bounds)
python3 -I <scratchpad>/m1r/gen.py ; gen2.py                (builds this file from ann.py)
```

Scratchpad working files (not part of the repository): /tmp/claude-0/-home-user-Design-Platform/32737463-7564-5f1d-b606-2274610299d6/scratchpad/m1r/ (handlers.txt, cg.json, ann.py, notes-raw.md).
