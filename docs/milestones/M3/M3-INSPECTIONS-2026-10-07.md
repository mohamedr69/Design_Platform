# M3 inspections — 7 October 2026 (owner-authorised, read-only)

Milestone: **M3 - Ownership, Access & Memory Policy**. These three inspections answer Pack open questions 7, 8 and 9 ([M3-DECISION-PACK.md](M3-DECISION-PACK.md) section 7), under the owner's authorisation of 7 October 2026 (afternoon; Pack section 2b, Q-7..Q-9). Performed by the orchestrator on the owner's Windows PC from the clone `G:\dev (2)\dev\ep-platform-merged\ep-platform` at HEAD 0568623 (working tree carries the uncommitted Drawings Assistant and the M3 filings of the same day).

Rules kept: the live database was opened with SQLite's read-only URI mode (`?mode=ro`) while the platform ran; no write, migration, correction, deletion or normalisation was made; no secret value was printed, copied or logged; only setting names and their class (default, overridden, missing, unknown) are recorded here.

## 1. Live database state (open question 7)

Database: `<DATA_ROOT>/ep_platform.db` (DATA_ROOT set in the backend `.env`); Alembic head `e6a8c0b2d4f6`.

| Subject | Count | Breakdown | Bears on |
|---|---|---|---|
| Projects | 11 | status: all 11 `active` (no row is `archived`; the enum has `draft`, `active` and `archived` and no `cancelled` or `on hold` state yet); `ai_policy`: all 11 `allowed` | OD-10 (no migration of existing states is needed), OD-04 (no blocked project today) |
| Compliance learned answers (`compliance_learned_answers`) | 84 | by project: project 1: 1, project 2: 59, project 7: 24; all 84 `active`; all 84 carry an approver (`approved_by_id` set) | OD-03 (d): 84 rows become project-local; three projects hold them; none has promotion provenance |
| Drawing-review rulings (`review_rulings`) | 260 | all 260 on project 5; decision: 236 `accepted`, 24 `dismissed` | OD-12 (c): all rulings stay local to project 5; nothing to re-scope elsewhere |
| IFC symbols (`ifc_symbols`) | 1545 | `source`: all 1545 `engineer`; 47 carry a reviewer (`reviewed_by_id`), 1498 do not; `confidence` is null on every row (no stored AI confidence) | OD-13: no symbol of source `ai` exists today; the 1498 unreviewed engineer-source rows may include machine carry-overs stored with source `engineer` (PB S1-D16), an inference for M12 to establish, not an inspected fact; no 0.97 auto-accepted row to retract |
| IFC symbol AI reviews (`ifc_symbol_reviews`) | 40 | decision `device` with no outcome: 24; `device` → outcome `not_device`: 11; `uncertain`: 5 | OD-13: AI reviews are recorded apart from the library, as the decision requires |
| IFC device types | 48 | all active | — |
| Redesign runs (`project_redesign`) | 1 | project 5, status `planned`, 21 stored changes: 16 `failed`, 4 `skipped`, 1 `approved`; **0 absolute library paths** in the stored changes; `output_relative` empty | OD-17: the six PC-A-path changes are **not** in the live database; they exist only in the RD-M1 snapshot kept outside the repository (HAND, sha256 `b50dfe2b…`). OD-17 (b) therefore changes nothing in the live data |
| Shop drawings (`project_shop_drawings`) | 113 | all active; no absolute `schedule_path` | — |
| Shop BOQ (`project_shop_boq`) | 2 | — | — |

Not inspected: row contents beyond the columns named (no clause text, no ruling text, no symbol images were read).

## 2. Access scoping and state-changing GETs (open question 8)

### 2.1 What `require_role` and `get_current_user` enforce today (fact, from `backend/app/deps.py`)

- `require_role(*roles)` checks only that the user's single role is in the tuple. It carries no discipline, division or project scoping.
- `get_current_user` confines **estimation roles only** to their division's path prefix (`/{area}/projects…`) and `/auth/me`. Design roles and `design_manager`, `admin`, viewer and draftsman roles are not confined to any project or discipline; the code comment says so by design.
- No router performs a project-membership check; `_get_project_or_404` checks existence only (Pack OD-19 row).

UNK U-23 is therefore answered: `require_role` does not scope an engineer to a discipline's projects. Under OD-19 (b) this is the known implementation gap; project access follows central membership authorisation when M7 lands it.

### 2.2 GET handlers that change state

Method: a static scan of every `@router.get` handler body in `backend/app` for direct write statements (`db.commit`, `db.add`, `db.flush`, folder creation, activity or change records, reconcile calls, job starts, scans, file writes), then a read of each flagged handler. Writes made deeper in a called service are listed where the M1 refresh already recorded them (M1R surveys S2, S3); a full call-graph survey is M10's.

| # | Handler (file:line) | What the read changes | Class | Remediation milestone |
|---|---|---|---|---|
| 1 | `routers/drawings.py:115` `drawings_summary`, `:198` `issues`, `:213` `building_floors_view` | `_catch_up` runs `shop_drawings.reconcile` when the records are behind the document index (business write) | business write on read | M10 (Drawings tab), M7 owns the processor; the roadmap M10 gate names "status reconstruction and state mutation" |
| 2 | `routers/logs.py:91` `drawings_register`, `:130` `export_drawings_register` | the same reconcile | business write on read | M10 |
| 3 | `routers/projects.py:471` `get_project` | `_ensure_project_folders` creates the standard folders in the project's archive folder; `activity.record_open` appends an audit row | archive write on read; audit append | M10 for the read; M7 for the archive-write rule (OD-15 consistency, PRJL.archive_writes) |
| 4 | `routers/shop_boq.py:60` `get_shop_boq` | makes the shop BOQ from the IFC BOQ on first read and records it | business write on read | M10 |
| 5 | `routers/fa_interfaces.py:63` `get_schedule` | makes the project's interface row on first read, commits | business write on read | M10 |
| 6 | `routers/drawing_review.py:55` `get_review` | commits in the handler (row made or caught up on read) | business write on read | M10 (M12 owns the review) |
| 7 | `routers/fa_interfaces.py:428` `export`, `:441` `review_cases_pdf`, `:469` `export_pdf` | commit after building the export | write on export | M10; whether an export may record itself is M10's "evidence download may serve bytes" decision |
| 8 | `routers/projects.py:647` `export_project_boq`, `:1158` `export_boq_revision`; `routers/design.py:704`, `:730` battery exports; `routers/submittal.py:1026`, `:1055`, `:1089` submittal exports | `activity.record` appends an audit row for the export | audit append on export | M10 to classify; no M3 gate dependency. Not kept as policy; whether an export may record itself is M10's classification |
| 9 | `routers/knowledge.py:27` `knowledge_status`, `:99` `import_report` | flagged by the scan for naming the importer; both read `importer.status(db)`; no write found in the handler | no mutation found | — |

Owner's rule applied: none of rows 1 to 8 is preserved as policy. Each is a downstream implementation obligation of M10 (the roadmap already assigns read-time production to M10 and no M3 gate depends on them), with M7 owning the processors and the archive-write rule. Rows 1, 3, 4, 5 and 6 are the ones a viewer or draftsman role can trigger today (CSV USR.role_access).

## 3. Production configuration against code defaults (open question 9)

Source: `backend/.env` of the live installation, compared with `backend/app/core/config.py` defaults. Values of secrets were compared in memory and never printed.

| Setting | Class | Implication |
|---|---|---|
| `SECRET_KEY` | overridden, differs from the code default, 32+ characters | sessions are not signed with the public default |
| `DEFAULT_ADMIN_PASSWORD` | **set to the code default** | the seeded admin account's initial password is the one printed in the public source. The seed creates the account only when absent, so whether the live admin still uses it is UNKNOWN from configuration alone. Security implication: the owner should change the admin password in the application and set a non-default value, or remove the key |
| `DEFAULT_ADMIN_EMAIL` | set to the code default | informational |
| `COOKIE_SECURE` | default (`false`) | the session cookie is sent over plain HTTP; acceptable only while the platform is served on localhost, as `CORS_ORIGINS` shows; a networked deployment is an owner decision and must set it |
| `COOKIE_NAME` | overridden | the merged installation's own cookie name |
| `CORS_ORIGINS` | overridden (localhost, port 5175) | matches the owner's port edits |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `MAX_FAILED_LOGIN_ATTEMPTS`, `LOCKOUT_MINUTES` | missing, defaults apply (30 min, 5 attempts, 15 min) | as surveyed in USR.session and USR.login_state |
| `AI_ENABLED` | default (`false`) | platform-wide AI off |
| `FA_AI_ENABLED`, `DRAWING_REVIEW_AI_ENABLED`, `PREP_AI_ENABLED` | overridden (`true`) | three workflows call a model while the platform switch is off; under OD-04 (a) each must honour `ai_policy` (all projects `allowed` today, section 1) |
| `DRAWINGS_AI_REVIEW_ENABLED`, `DRAWINGS_CHAT_ENABLED`, `DRAWINGS_CHAT_AI_ENABLED`, `OPEN_FOLDER_ENABLED` | missing, defaults apply | the sync-time drawings AI review stays bound to `AI_ENABLED` (off); the Drawings Assistant is off until its switch is set |
| `AI_PROVIDER` | default (`claude-code`) | the CLI route; `AI_CLAUDE_CLI` overridden with a path; `AI_API_KEY` empty (not used by this route) |
| `AI_MODEL_SMALL`, `AI_MODEL_STANDARD` | overridden to aliases (`sonnet`, `opus`) | a task that asks for an exact model (`exact_model`) refuses an alias; those tasks need full model ids where they are pinned (FA models are pinned by full id) |
| `FA_ORCHESTRATOR_MODEL`, `FA_FINDINGS_MODEL` | overridden (full ids) | — |
| `AI_DISABLED_TASKS`, `AI_EFFORT`, `AI_MAX_CONCURRENCY`, `AI_CACHE_TTL_DAYS` | missing, defaults apply | no task disabled; 90-day result cache |
| `AI_MAX_CALLS_PER_PROJECT_PER_DAY` | overridden (150; default 60) | wider daily budget per project |
| `AI_COMPLIANCE_BATCH_CLAUSES` (15; default 25), `AI_COMPLIANCE_MAX_CALLS_PER_STATEMENT` (30; default 12), `AI_COMPLIANCE_MAX_OUTPUT_TOKENS` | overridden | smaller batches, more calls per statement |
| `DOCUMENT_CLASSIFICATION_V2` | overridden (`true`; default `false`) | Classification V2 is live here |
| `DATA_ROOT`, `PROJECTS_ROOT` | overridden (set) | the merged installation's data folder and the archive root |
| Per-project `ai_policy` (database) | all `allowed` | no project is blocked today |

Model names appear above only as configuration classes; this file records no secret.

## 4. What these inspections change in M3

- OD-17 has no live-data effect (section 1); it binds the handling of the RD-M1 snapshot only.
- OD-03 (d) and OD-12 (c) act on 84 learned answers in three projects and 260 rulings in one project; no cross-project row exists that the decisions would have to unwind beyond stopping the cross-project reads.
- OD-13: no AI-sourced symbol exists; 1498 engineer-source rows carry no reviewer, which may include machine carry-overs (an inference for M12 to establish).
- OD-10 and OD-11: every project is `active`; no state migration is needed before the new states exist.
- OD-19 and U-23: no project or discipline scoping exists for design roles; the gap is confirmed, not assumed.
- Eight groups of GET handlers change state (row 9 found none), assigned to M10 with M7, none a policy.
- One security finding for the owner, outside M3's gate: the seeded admin password key is at its public default.
