# M1 Refresh: Unknowns Register

- Date: 6 October 2026
- Repository HEAD: 771001e (the snapshot the surveys describe)
- Snapshot statement: static reading. The five surveys ran no code, no test, no endpoint and no database query, and no local database exists in the checkout. This register lists what they could not determine. I did not re-verify any item.

Sources: the section 7 (or section 8) unknowns lists of S1 to S5 in docs/milestones/M1/refresh-2026-10-06/evidence/surveys/, plus UNKNOWN statements the surveys made inside their tables. The surveys' target columns say "UNKNOWN (roadmap)" or "UNKNOWN: not decided in this refresh"; those mark decisions not yet taken, not facts that cannot be found, and they are not listed here.

How to read the "Why" column. static reading: the answer needs a run or a test that was not done. no database: the answer is in stored rows. chain not followed: the call chain was not traced to its end, or lies in another survey's area. configuration not read: the value is in a deployed environment file or setting. outside repository: the answer is in an operational script, a document or a person. source absent: the input document is not in the repository.

Total: 57 unknowns (S1 14, S2 12, S3 13, S4 10, S5 8). Of these, 53 come from the surveys' own numbered unknowns lists (S1 12, S2 11, S3 12, S4 10, S5 8) and 4 are UNKNOWN statements the surveys made inside their tables (S1 two, S2 one, S3 one). Section 6 gives the reconciliation.

## 1. S1: Interfaces, IFC and floors

| ID | Survey reference | What is unknown | Why | What would settle it |
|---|---|---|---|---|
| U-01 | S1 U-1 | Row counts of ifc_device_types, ifc_symbols, ifc_block_aliases, ifc_symbol_reviews, project_ifc_drawings, project_building_floors, project_floor_aliases, project_floor_schedule, project_fa_interfaces, fa_interface_runs; the size of project_fa_interfaces.sources and published JSON (published duplicates every read entry, interfaces/evidence.py:227-229). The CSV's "Zero rows locally" is not re-verified | no database | A read-only COUNT(*) per table and a length query on the JSON columns, run against the database in use |
| U-02 | S1 U-2 | Whether GET /fa-interfaces actually inserts or rewrites project_floor_aliases on a real project. The code path is unconditional; the effect depends on IFC titles that name both a level and a named floor (drawing_log.floor_alias_evidence@124) | static reading | Call the GET on a copy of a project whose IFC titles name a level and a named floor and compare project_floor_aliases before and after; or write a test with such titles |
| U-03 | S1 U-3 | Concurrency and sequencing claims: lost update of decisions or manual items, upload then re-read of edits, description collisions, clear then re-read. Whether any test covers them | static reading | Read backend/tests/test_fa_*.py, test_floor_schedule*.py, test_floor_aliases.py and test_ifc_*.py (listed, not read); add concurrent-request and sequence tests |
| U-04 | S1 U-4 | Whether anything outside frontend/src calls GET /projects/{id}/drawings/floors, /ifc/ai-metrics, the reprocess endpoints or DELETE /ifc/device-types | chain not followed (no caller found in the repository frontend) | Server access logs for those routes; a search of scripts and tools outside the frontend |
| U-05 | S1 U-5 | Whether the HTTP entry points of draftsman_assignment.py:103, 335 and redesign/service.py:509, 532 (callers of interfaces.service.build) are GET handlers. S2 Table C row 26 shows GET /draftsman reaching interfaces.service.build; the redesign callers are not traced to a GET | chain not followed (outside S1) | Trace redesign/service.py:509 and 532 to a route; S2 Table C row 26 already answers the draftsman half |
| U-06 | S1 U-6 | The artifacts and cost of the review and redesign consumption of the same FA IFC drawings; the three-way re-parse of one DXF is noted, not measured | outside survey scope | S2 Table E now lists the review and redesign artifacts; measure the parse count by running one FA IFC drawing through the interface scan, the IFC read and a drawing review and counting ezdxf.readfile calls |
| U-07 | S1 U-7 | Whether ProjectBuildingFloor.source "engineer" and ProjectFloorAlias.source "ai" are intended future writers or dead vocabulary (no writer in backend/app) | static reading | The owner's decision; git history of the two values; a grep after any planned change |
| U-08 | S1 U-8 | Content of interface matrix rows 36 and 38 (matrix.py:136); they are not in the repository | source absent | The consultant's interface matrix document; transcription or a written decision to exclude them |
| U-09 | S1 U-9 | Whether any operational script removes <uploads>/EP-n/interfaces (converted DXFs, pictures, review-case pictures beyond the last two runs); nothing in backend/app does | outside repository | Inspect deployment and maintenance scripts; list the directory on an install after a project deletion |
| U-10 | S1 U-10 | The CSV's SD.floor_registry evidence "query:floors", and the SD.* rows owned by S2, were not re-verified | no database | Run the query against the current database |
| U-11 | S1 U-11 | Consumers of services/symbol_taxonomy.py::canonical@138 (properties and room variants) and symbol_rooms; only device_in, family_of and system_of were traced | chain not followed | Trace callers of canonical and symbol_rooms |
| U-12 | S1 U-12 | Whether the "engineer" source assigned to reprocess carry-over rows (IfcSymbol.source default "engineer", models.py:2004) is intended; the column comment says "engineer = an engineer's answer" | static reading | The owner's decision; a query for rows with reviewed_by_id null and the carry-over note |
| U-13 | S1 Table B (FWS.schedule_row) | Whether the upload-time edits lifecycle is intended: POST /floor-schedule assigns the fresh parse without apply_edits and does not clear edits, so stored edits are neither applied nor discarded until the workbook next changes (routers/floor_schedule.py:211-225) | static reading | The owner's decision; a test that edits a line, uploads a workbook and reads the schedule before and after |
| U-14 | S1 Table E (CAD conversion row) | The third DWG-to-DXF path, used by drawing review and redesign | chain not followed (outside S1) | Read review/render.py and the redesign conversion call; S2 Table E row 7 describes the plot but not the DXF conversion |

Note on S1: the survey's own list has 12 items (U-01 to U-12); U-13 and U-14 are UNKNOWN statements inside its tables.

## 2. S2: Drawings, review, preparation, drawing log, draftsman

| ID | Survey reference | What is unknown | Why | What would settle it |
|---|---|---|---|---|
| U-15 | S2 7.1 item 1 | Real values of AI_ENABLED, DRAWINGS_AI_REVIEW_ENABLED, DRAWING_REVIEW_AI_ENABLED, PREP_AI_ENABLED, EXTRACTION_PROMOTE_OBSERVATIONS and DESKTOP_ACTIONS_ENABLED; only code defaults are cited (core/config.py:248, 257, 333, 405, 425) | configuration not read | Read the deployed .env or settings of the running system |
| U-16 | S2 7.1 item 2 | Stored data: row counts, and whether reply_reference, reply_at, candidate_status = conflict and ProjectBuildingFloor.source = engineer are empty in real data; the CSV's query:* facts are not re-verified | no database | Read-only queries for those columns and counts |
| U-17 | S2 7.1 item 3 | The reference-correction defect: after a corrected reference the next reconcile may create a second ProjectShopDrawing and mark the corrected drawing's revisions source_missing (services/shop_drawings.py:295-335, 461-475). Reasoned, not run | needs runtime | A test: PATCH a drawing's reference, run reconcile, count drawings and source_missing flags |
| U-18 | S2 7.1 item 4 | Whether two simultaneous catch-up GETs (or a GET during a sync's reconcile) collide in reconcile (no lock, services/shop_drawings.py:144-234) and what the unique constraints do; whether a PATCH during a running plan job is lost (redesign/service.py:1180-1248 against routers/redesign.py:120-144) | needs runtime | Concurrent-request tests on a copy of a project |
| U-19 | S2 7.1 item 5 | The interface schedule, evidence listing and calculation chains reached from GET /draftsman (interfaces/service.py:797-830; routers/amplifier.py _out and _power) | chain not followed (other surveyors' areas) | S1 now covers the interface build; S5 N2 covers the draftsman GET at the level of classes; trace the amplifier chain |
| U-20 | S2 7.1 item 6 | Whether the document registry marks OneDrive online-only files REMOVED, in which case every drawing would turn source_missing at once (services/shop_drawings.py:433-475); _was_unavailable in document_sync.py was not traced | chain not followed | Trace _was_unavailable; test with an online-only placeholder file |
| U-21 | S2 7.1 item 7 | Whether AutoCAD plot settings can change under an unchanged file hash (review/render.py keeps the first PDF per hash) | needs runtime | Change the plot settings and re-run the review on the same DWG |
| U-22 | S2 7.1 item 8 | Who can write to uploads/EP-<n>/redesign; its pickle indexes are loaded with pickle.load (redesign/walls.py:195; redesign/coverage.py:170) | static reading | Check filesystem permissions and every route that writes under uploads |
| U-23 | S2 7.1 item 9 | Whether require_role (deps.py) scopes an engineer to their discipline's projects; CREATOR_ROLES is global (routers/projects.py:79). S3 states there is no per-project access control and cites deps.py:44-53 (S3 Table A USR.role_access); the two surveys do not cross-refer | chain not followed | Read deps.py:44-53 and run one request as an engineer of another discipline |
| U-24 | S2 7.1 item 10 | Whether the document sync indexes the redesigned DWG copy filed in 03- Drawings/Redesign (redesign/service.py:1512-1517); DWG files are not parsed by document_control, so probably only registered | chain not followed | Trace the sync's extension rules; place a DWG there and run a sync |
| U-25 | S2 7.1 item 11 | Whether the database columns match models.py (for example every status column length against the longest value written); migrations.py was not read | chain not followed | Compare the alembic or migration schema with models.py |
| U-26 | S2 Table A (DOC.drawing_title_block) | Whether a TITLE_BLOCK_VERSION change without a PARSER_VERSION bump re-reads nothing; reasoned from document_processing.py::parser_current@211, not verified by running | needs runtime | A unit test of parser_current after changing the version |

Note on S2: the survey's own list has 11 items (U-15 to U-25); U-26 is an UNKNOWN statement inside its table.

## 3. S3: Documents, file sync, jobs, caches, archive, users, project state, deletion

| ID | Survey reference | What is unknown | Why | What would settle it |
|---|---|---|---|---|
| U-27 | S3 section 8 item 1 | Every statement about local rows, counts or versions: the accepted M1 cites "890 local rows" and query:* facts | no database | Re-run the accepted M1 queries against the database in use |
| U-28 | S3 section 8 item 2 | Whether deleting a project whose DocumentReading rows another project references (ProjectDocument.reading_id models.py:536, ExtractionRun.reading_id models.py:1385) raises an IntegrityError; foreign keys are enforced (database.py:66), the delete is by first-asker project_id (services/project_deletion.py:94); no cross-project test found | static reading | A test with two projects sharing one content hash, deleting the first asker |
| U-29 | S3 section 8 item 3 | Whether combine() or any consumer ignores the `retained` flags on carried records (services/document_sync.py:371-376); not traced into document_control.combine | chain not followed | Read document_control.combine@2277-2407 and test with a bounded reading that carries records |
| U-30 | S3 section 8 item 4 | Whether any consumer other than File Sync trusts extracted.form after a content change (services/document_sync.py:623-626); classification reads it (services/document_classification.py:425) | chain not followed | Grep and trace every reader of extracted.form |
| U-31 | S3 section 8 item 5 | How the frontend handles a gap in the change feed after 30 days or 500 rows (services/project_state.py:64-77); frontend/src/lib/projectChanges.tsx not read beyond the poll call | chain not followed | Read projectChanges.tsx; test a client that was away for more than 30 days |
| U-32 | S3 section 8 item 6 | Whether an admin can unlock a locked account other than by waiting (routers/users.py has no such route; not searched elsewhere); whether acknowledgement by finding code (services/document_intake.py:325-333) is intended | static reading | Search routes and scripts for unlock; the owner's decision on acknowledgement |
| U-33 | S3 section 8 item 7 | Production values of secret_key (default "dev-secret-key-change-me-in-production", core/config.py:73), cookie_secure (default False, :76) and default_admin_password (seed.py:332) | configuration not read | Inspect the deployed environment file |
| U-34 | S3 section 8 item 8 | Whether HISTORY (routers/users.py:101-107) covers every table that names a user, so that deleting an "unused" account cannot raise | static reading | A test deleting an account that has rows only in tables outside HISTORY (for example ProjectSubmittalEvent.by_id, BoqCorrection.user_id, DocumentReading.created_by_id, BackgroundJob.created_by_id) |
| U-35 | S3 section 8 item 9 | Which scripts consume extracted.observations (backend/scripts/m2_pilot_eval.py and others not opened) | chain not followed | Grep backend/scripts for the key |
| U-36 | S3 section 8 item 10 | The version of the IFC reader or DWG converter that produced `groups` (not stored: ifc/services/processing.py:188-191); whether anything marks IFC reads stale after a reader change | static reading | Read the converter and extractor entry points; the owner's decision on recording a version |
| U-37 | S3 section 8 item 11 | Whether any process removes orphaned uploads/EP-N files, old BackgroundJob rows, BackgroundWorker rows, old submittal_map readings or backups; no pruning code found in this area, none confirmed absent elsewhere | outside survey scope | Search the whole repository and deployment scripts; inspect table and directory sizes on a long-running install |
| U-38 | S3 section 8 item 12 | Tests were not run; no claim rests on a test result | needs runtime | Run the backend test suite and record which survey claims have a covering test |
| U-39 | S3 Table A (AI.budget_limits) | Whether a per-project override of the AI limits exists; none found, settings are server-wide | static reading | Grep for project-level limit settings; the owner's confirmation |

Note on S3: the survey's own list has 12 items (U-27 to U-38); U-39 is an UNKNOWN statement inside its Table A.

## 4. S4: Compliance, knowledge base, datasheet library, submittals, workload inputs

| ID | Survey reference | What is unknown | Why | What would settle it |
|---|---|---|---|---|
| U-40 | S4 U1 | Row counts of ComplianceStatement, ComplianceLearnedAnswer, KnowledgeResponse, DatasheetDocument and ProjectSubmittal where the platform runs. The CSV records zero statements locally; eligibility.py:3 carries a comment "56,533 responses imported and none eligible" from an earlier day | no database | Read-only COUNT(*) queries on the database in use |
| U-41 | S4 U2 | Behaviours inferred and not executed: delete_statement with audit rows (by static reading a statement with any audit row cannot be deleted, foreign keys enforced), words_of on an image-only PDF, the uploaded-spec verification gap, the effect of a forced knowledge re-import on open statements | needs runtime | One test or manual run per behaviour |
| U-42 | S4 U3 | Whether the DRF's "MS" column means Method Statement or Material Submittal. Code reads it as method statement (models.py:376-381; details_check.py:59; ai/verification.py:1156) and nothing consumes it | source absent | The DRF template and the owner's confirmation |
| U-43 | S4 U4 | Where the engineering manager would obtain capacity and contract value today (a spreadsheet, the estimation team, a finance system); nothing in the repository holds them | outside repository | A decision at the M1 ownership step; interview the engineering manager |
| U-44 | S4 U5 | Whether any ProjectSubmittalStatusChange row has source "migrated"; no writer in backend/app or backend/alembic | no database | A query on the source column |
| U-45 | S4 U6 | Whether the datasheet-reference script was ever run, so whether datasheet_documents holds rows (no runtime writer) | no database | A COUNT(*) on datasheet_documents; the script's run record if any |
| U-46 | S4 U7 | Whether provider time-outs are logged: AiUsage.outcome lists ok, transport, rate_limit, invalid_response, refused, auth, rejected (models.py:1477), no timeout; backend/app/ai/provider.py changed by 376 lines since the CSV snapshot and was not read | chain not followed | Read ai/provider.py; query AiUsage outcomes |
| U-47 | S4 U8 | Frontend-side derivations (counts, bucketing) beyond vocabularies, endpoints and approval confirmations were not exhaustively checked in ProjectCompliancePage (2361 lines), ProjectMaterialSubmittalPage, SubmittalReplyPage, DatasheetEnginePage, AdminKnowledgePage, ProjectProposedMaterialsPage | chain not followed | A full read of those pages |
| U-48 | S4 U9 | Cross-area rows touched only for the comparison and not re-verified: SD.*, HOME.*, DOC.* (including page-ledger coverage), document_processing and document_sync call sites of sync_register | outside survey scope | S2 and S3 cover most; trace the remaining call sites |
| U-49 | S4 U10 | Whether M7's page-level stage coverage will cover specification PDFs inside a zip (spec_finder reads zip members, spec_finder.py:381-396) or in the shared uploads folder, both outside the project's ProjectDocument registry | static reading | An M7 design decision; a test of the registry's file discovery on those two sources |

## 5. S5: GET handler side-work audit

| ID | Survey reference | What is unknown | Why | What would settle it |
|---|---|---|---|---|
| U-50 | S5 section 7 row 1 | Whether any GET reaches document_control.combine (services/document_control.py:2277-2407) with file I/O; read as a source segment with no open, stat or commit tokens, but its callees (drawing_key, _answers@2173) were not each read | chain not followed | Read the callees; run a GET under a file-access trace |
| U-51 | S5 section 7 row 2 | The full transitive cost of ifc/resolve.py:186-285 resolved_drawing (called per drawing by ifc_boq.py:388, :833, shop_boq.py:48); no commit or I/O tokens, computation size on large drawings not measured | needs runtime | A timing run with a large drawing and a large library |
| U-52 | S5 section 7 row 3 | Behaviour of interfaces/service.py _assemble :947-1019, coverage :2127-2150 and the Floors class :695-796 beyond a scan for commit and I/O tokens (none) | chain not followed | A line-by-line read |
| U-53 | S5 section 7 row 4 (and Table B2 N14) | Whether Project Home's read, ProjectChange, re-read loop converges in practice | needs runtime | Load Project Home against a project that needs a reconcile and count requests until the change feed is quiet |
| U-54 | S5 section 7 row 5 | The exact number of PURE_READ handlers that touch no file at all; the call graph is name-based and PURE_READ rows were confirmed by reading the handler and its first-level callees plus a token scan of named helpers, not every transitive method | static reading | A traced run of each PURE_READ handler with file-access logging |
| U-55 | S5 section 7 row 6 | Writes and file I/O inside services/activity.py:140-272 account and knowledge/eligibility.py:58-97, 100-142; the token scan was clean but the functions were not read in full | chain not followed | A full read of both |
| U-56 | S5 section 7 row 7 | Which GET calls are slow in practice; the cost ranking in S5 section 3 is by what each chain does, not measured. Only code comments give cost (services/schedule_materials.py:106-108 "takes minutes"; services/datasheet_library.py:229-231 "eleven seconds off a synced drive") | needs runtime | Timings of each handler on a synced drive |
| U-57 | S5 section 7 row 8 | Which frontend pages call each GET and how often; only the Home, BOQ, Battery, Logs, Compliance, Materials and Info mounts were traced | chain not followed | Grep of api.get and polling for the remaining handlers |

## 6. Totals and reconciliation

| Survey | Own numbered list | UNKNOWN statements inside tables, added here | Entries |
|---|---|---|---|
| S1 | 12 (U-1 to U-12) | 2 (U-13, U-14) | 14 |
| S2 | 11 (7.1 items 1 to 11) | 1 (U-26) | 12 |
| S3 | 12 (section 8 items 1 to 12) | 1 (U-39) | 13 |
| S4 | 10 (U1 to U10) | 0 | 10 |
| S5 | 8 (section 7 rows 1 to 8) | 0 | 8 |
| Total | 53 | 4 | 57 |

Not listed: the open policy questions (whether approved-as-noted counts as final; who may set capacity and contract value) are decisions for M3, not unknown facts about the code. The one exception is where capacity and contract value are held today (U-43).

Cross-survey notes. U-05 is partly answered by S2 Table C row 26. U-23 is answered in part by S3 Table A USR.role_access; S2 and S3 do not refer to each other. U-06 is partly answered by S2 Table E rows 7 to 12.
