# FI-P1 — IMPLEMENTATION SEQUENCE: small stages with components, tests, rollback, dependencies

Labels: C = confirmed, A = assumption, EXAMPLE = illustrative. Paths relative to `backend/`. Every stage ships
behind a setting or a new job kind so the current `fa_interfaces_scan` path keeps working until G3/G4
(VALIDATION.md §7) are met. No stage is started here; this is the order proposed.

## 1. The smallest first implementation task — Stage 0.1 publication guard

**Task.** In `app/interfaces/service.py::scan_project` (:177-253, C), replace `row.sources = done` (:246) with a
per-entry merge implementing the PublicationGuard (CONTRACTS §11):
- (0) if the **project root** is unreachable (`os.path.isdir(document_control._os_path(root))`, exactly the test
  `received()` already makes, :1018) raise a named error → the job fails, the previous `row.sources` is untouched. An
  absent or empty **discipline** folder is not an abort (`discover()` just yields nothing for it, :113; the test
  project creates only 3 of 6 folders, C).
- (1) same `(discipline, relative_path)`, new read ok → replace (as today).
- (2) same path, new entry `failed` (unopenable, no converter, conversion/scan error) → keep the old `read` entry,
  add `stale: true, kept_from: <old scanned_at>, reason`.
- (3) same path and sha, new `visual.status == "incomplete"` while the old visual was `complete` → keep the old
  `visual` block.
- (4) present but superseded → `superseded` (unchanged, :135).
- (5) old entry whose path is **absent** from `found` while the root is reachable **and its discipline folder is
  present and non-empty** → `status: "removed"` with the old reading kept inside the entry for display.
  (5b) if the whole discipline folder is absent or empty (OneDrive not synced, folder renamed) → keep the old entry
  `read` + `stale: true, reason: "discipline_folder_absent"` (counted, banner) — discovery trouble never removes a
  useful result (SPEC §11); nothing replaces it, so nothing is double counted (REVIEW.md R-30). `build()` reads `status == "read"` only (:434, C), so a removed
  entry is excluded — no double count when R1 was deleted after R2 was filed (R2 is `read`, R1 is `removed`; today
  R1 would simply vanish, and a naive "keep as read + stale" would count both).
- (6) if any entry became `removed`, or `read` count fell to 0 while it was > 0, add `row_notes` (JSON key inside
  the same row) for the UI banner (Stage 7 renders it; until then it is inert).
~50–60 lines in one function, no schema change (`stale`, `kept_from`, `reason`, `removed` are keys inside the
existing JSON entries). `received()` iterates the folder listing, so `removed` entries never reach `coverage()` and
the frontend's status union is unaffected.

**Why this one.** It is the only change that protects value that already exists (engineer decisions and complete
readings — project 5 lost 12 sources this way, C), it is independent of the provider decision the owner still has
to make, it touches one function with tests around it (`tests/test_fa_interfaces.py:162, :316, :374`, C), and it is
reversible by reverting the function. It is larger than the first draft (six cases instead of two) but still one
function and one test file; it remains the smallest task that is also *correct* — a two-case version would double
count removed revisions. Runner-up: the `assist.available()` gate before `Plan()` (0.4) — three lines, but it only
saves wasted rendering, not data.

**Tests.** (1) prior reading with 3 read sources; project root unreachable → job fails, sources unchanged; (2) one
discipline folder absent → scan succeeds, other disciplines updated, absent discipline's prior entries kept `read` + `stale` (rule 5b) and a file deleted from a present folder becomes `removed`;
(3) one file now fails to convert → entry kept `read` + `stale`, others updated; (4) **R1 read in the prior
reading; R1 deleted and R2 filed** → R2 `read`, R1 `removed`, `build()` counts the drawing once; (5) scan cancelled
after one file (raise `Cancelled` from `check`) → rollback as today, prior preserved; (6) existing tests unchanged.
**Rollback:** revert the function; the new JSON keys are ignored by `build()`. **Dependencies:** none.

## 2. Stage 0 — make it safe and honest (before any agent architecture)

| Step | Components | Tests | Rollback | Depends on |
|---|---|---|---|---|
| 0.1 Publication guard | `interfaces/service.py::scan_project` | §1 | revert | — |
| 0.2 Provider readiness, effort, full ids, **used model** | `ai/provider.py`: `ProviderCapabilities` (`claude --version` at build, min-version table, `--effort` pass-through in `ClaudeCodeProvider.complete` :538-541, `error="unsupported_model"`); `AiRequest.no_fallbacks` honoured by `ClaudeProvider` (omit the fallback beta, :251-253) and `AiResponse.model` set from `message.model` (today `model=model` on every return, :263-299); CLI `used` from `modelUsage` (:568) kept; wrapper check used ≠ requested → `error="model_substituted"`; `compliance/assist.py::_call` cache key adds effort + cli_version (:265-272); settings `FA_AGENT_MODEL/EFFORT`; `.env` tiers to full ids (owner) | fake CLI versions → ready/unsupported; cache key differs by effort; API provider receives effort and no fallback beta; a stubbed response with a different `model` → `model_substituted`, never logged as the requested id | setting off → old behaviour | — |
| 0.3 Cancellable, time-boxed rendering | `interfaces/visual.py::check` loop instead of comprehension (:314-315) with `check()` between windows; `Plan` with `HatchPolicy.SHOW_OUTLINE`, `hatching_timeout` 5 s, oversized-HATCH pre-filter; render in a terminable spawn child with `RENDER_TIMEOUT_S`; window marked `unread:render_timeout` | reproduce SM-104 window offline → bounded; cancel during render ≤ 1 window; PNG determinism check (A) | setting `RENDER_IN_PROCESS=true` | — |
| 0.4 Honest gating and labels | `visual.check` gates on `assist.available()` before `Plan()`; "CLI not found" reported as `unavailable`, not `auth`; DXF path resolved from the source (SM DXF case :299-301); failed windows recorded in `visual.missing_reason` | SM filed as DXF gets looked at; readiness false → no render, status `unsupported` | revert | 0.2 |

Exit: gate G0 (VALIDATION.md §7). Owner decisions #1–#3 (PLAN §13) can be taken in parallel; nothing in Stage 0
needs them.

## 3. Stages 1–9

| Stage | Scope | Components | Tests | Rollback | Depends on |
|---|---|---|---|---|---|
| 1 Manifest + readings + publisher | Freeze `SourceManifest` (incl. conversion + `read_sheets` enumeration so `expected_layouts` is frozen; one entry per sha with path aliases); migration: `fa_interface_runs`, `fa_interface_sources`, `fa_interface_readings`, **`project_fa_interfaces.generation`**; `agents/publish.py` with the guard and generation CAS; **old `scan_project` routed through the same publisher**; one dedup key `fa_interfaces:{project_id}` for both job kinds (routers/fa_interfaces.py:62) | migration up/down; root unreachable → no publish; two publishers → one wins (CAS); old and new kind cannot run together for one project; duplicate copies → one entry | job kind `fa_interfaces_run` unused; tables inert | 0.1 |
| 2 Model gate + process isolation + accounting | `ai/gate.py` (`ai_model_leases`, BEGIN IMMEDIATE + retry, taken inside the provider wrapper for all callers; `ai_max_concurrency` unchanged); `agents/render.py` `DrawingProcess` (spawn, queues, `terminate()`, render-all-then-exit, evidence store); `ai_usage` migration (status, request_id, job_id, agent_id, step, effort, pid, process_started_at, used_model, model_substituted, lease_id) with pre-dispatch insert; killable Popen calls; Windows Job Object kill-on-close; startup reaper; `progress.stage=cancelling`; lease-held stall watchdog | lease limit holds across two processes; crashed holder freed at TTL; kill mid-call → `usage_unknown`; Stop ends with no orphan `claude`/render process; reaper finalises a fake dispatched row; queued agent is never "stalled" | gate off → per-process semaphores; `RENDER_IN_PROCESS` | 1, 0.2, 0.3 |
| 3 Geometry + stable ids | `scan._texts` emits `entity_path`, bbox, layer, xref flag, siblings; LEADER/MLEADER read; symbol candidates from `ifc/dxf/extract.py` machinery (shared module per decision #9); `label_id/symbol_candidate_id`; sha-independent `decision_key`; migration maps **tagged** decisions only, lists untagged/visual ones as `orphaned_decisions`; carry-forward matcher (`needs_reconfirm`) | cases 1, 2, 3, 5, 12 fixtures; handle-stability check (convert one DWG twice, A); the merged two-MSD decision `…\|719,154\|B3` is NOT auto-mapped; a decision survives a new revision as `needs_reconfirm` | `SCAN_VERSION` bump reverted; old ids still accepted | 1 |
| 4 Drawing agent steps | `agents/agent.py` state machine; `regions` deterministic (`_sheet_kind`, viewports) with the Opus call only off-viewport; `legend`, `associate`, `sweep` as schema-constrained Opus calls; `PageOutcome` checkpoints; migration `fa_interface_agent_runs`, `fa_interface_page_results`, **`fa_interface_observations`**; `DrawingAgentReport` with templated summary; coverage + reference_state invariant | RecordingProvider replays; resume after kill (case 10); unread page never empty (case 9); report accounts for every manifest entry incl. schedules; `regions` call count 0 for a fully-viewported drawing | run kind off → old scan | 2, 3 |
| 5 Validation + reviewer | `agents/validate.py` deterministic checks 1–12; blind-first reviewer for every model-proposed physical/association finding not settled by rule; `ValidationRecord` stored in the observation row; decision preservation by `decision_key` | checks unit-tested; reviewer sees no extractor answer (prompt assert); disagreement → held; a low-confidence item and a high-confidence item are both reviewed | reviewer disabled → rules only (findings stay `proposed`, never auto-validated) | 4 |
| 6 Reconciliation + adjudication | `agents/reconcile.py` identities, cross-file matching only in a verified frame (Alignment with control points), count comparison otherwise, ConflictSets, typical-floor fix for `_once`; migration `fa_interface_conflicts`; Fable adjudication packets (`FA_ADJUDICATION_ENABLED`, `no_fallbacks`) | cases 6, 7, 8; identical viewports alone never yield `verified=true`; conflict holds all members; adjudication never applied automatically; substituted adjudication response → ignored and logged | adjudication off (default) | 5 |
| 7 UI | progress dict (`execution`/`coverage` objects, `cancelling` stage), run endpoints, agent table, unresolved coverage, provenance badges, orphaned/needs-reconfirm decisions, never-replace banner incl. `removed` sources | API tests; manual UI check | feature flag | 1, 4 |
| 8 Obsidian | `agents/obsidian.py`, `OBSIDIAN_VAULT_ROOT`, export job, manifest-protected writes | export twice → idempotent; hand-edited note untouched; no secrets in output (grep test) | root unset | 4, 6 |
| 9 Evaluation (starts with Stage 1, in parallel) | GT JSONL format + click-to-annotate helper; harness computing VALIDATION §4 metrics; concurrency measurement runner (2/4/6) with the stated request cost | harness on fixtures; metrics reproducible | n/a | GT annotation (owner #8) |

Cutover: the new run kind replaces `fa_interfaces_scan` in the UI only after G3 and G4; the old kind stays
available for one release for rollback (both already publish through the same guard from Stage 1).

## 4. Test files affected (C, research A §5)

`tests/test_fa_interfaces.py` (:162 inline scan must still succeed; :443/:484/:510 call `_read_source` with `visual`
embedded in sources — keep that shape in `fa_interface_readings.result` or adapt the tests with reasons);
`tests/test_redesign.py:240+` (row shape id/anchor/modules); `tests/test_draftsman_assignment.py:34-56`
(`build()["rows"]`). New tests: cancel/partial/unreachable root/absent discipline folder/removed revision/orphaned
and carried-forward decisions/model substitution (none exist today, C).
