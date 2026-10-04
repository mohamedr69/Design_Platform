# FI-P1 — OBSIDIAN AND UI: tracking, application reports, Obsidian export

Labels: C = confirmed, A = assumption, EXAMPLE = illustrative. Paths relative to `ep-platform/`.

## 1. Tracking tables (new; SQLite, WAL)

| Table | Key columns | Written by |
|---|---|---|
| `fa_interface_runs` | run_id, project_id, job_id, manifest JSON, manifest_sha256, reference_version, **execution_state** enum[running, succeeded, failed, cancelled] (lifecycle, mirrors the job) and **coverage_state** enum[complete, provisional] (content), started/finished, counts JSON `{execution:{…}, coverage:{…}}`, usage JSON | orchestrator (Stage 1) |
| `fa_interface_sources` | run_id, source_id (sha24), sha256, paths JSON (aliases), kind, revision, supported, unsupported_reason, agent_id, expected_layouts JSON, coverage_state / reference_state | orchestrator (Stage 1) |
| `fa_interface_readings` | project_id, discipline, relative_path, source_id, sha256, scan_version, status enum[read, failed, superseded, removed], coverage_state, result JSON, run_id, read_at, stale, kept_from_run | publisher (Stage 1) |
| `project_fa_interfaces.generation` | new integer column for the publisher's CAS | migration (Stage 1) |
| `ai_usage` (extended) | CONTRACTS §13: request_id, job_id, agent_id, step, effort, status (pre-dispatch), pid, process_started_at, used_model, model_substituted, lease_id | provider wrapper (Stage 2) |
| `ai_model_leases` | id, holder, pid, job_id, agent_id, acquired_at, expires_at — the ONLY cross-process pool | `app/ai/gate.py` (Stage 2) |
| `fa_interface_agent_runs` | agent_id, run_id, source_id, attempt, execution_state, coverage_state, stage, layouts_done/total, windows_done/total, proposed/validated/held/rejected, requests, tokens, usage_unknown, started/first_dispatch/last_progress/finished, queue_wait_s, error, report JSON | agent (Stage 4) |
| `fa_interface_page_results` | agent_id, layout, task_key (unique), kind enum[regions, legend, associate, sweep], status, result JSON, attempts, error, prompt_version, model_id, effort, labels_hash, timings JSON | agent (Stage 4) |
| `fa_interface_observations` | observation_id, agent_id, run_id, source_sha256, layout, key, instance_kind, finding_state, decision_key, observation JSON (CONTRACTS §6), validation JSON (§9 incl. ReviewerReading) | agent / validator (Stage 4–5) |
| `fa_interface_conflicts` | conflict_set_id, run_id, kind, state enum[open, adjudicated, decided], members JSON, adjudication JSON, engineer_decision_key — the verification queue's durable rows | reconciler (Stage 6) |

`project_fa_interfaces.sources` (models.py:2379, C) stays the compatibility read model that `build()`, `coverage()`,
`received()`, redesign and draftsman consume; it is rewritten only by the single publisher under the generation CAS
and is derived from `fa_interface_readings`. Reviewer and adjudication calls are recorded in `ai_usage` by `step`;
their results live in the observation/conflict rows. In-memory pools (render, geometry, writer) have no table.

## 2. Application UI (SPEC §11)

Progress (polled 1.5 s by `useJob`, frontend/src/lib/useJob.ts, C) — small additions to the free-form progress dict
(`JobContext.progress`, services/jobs.py:134-155, C):
```
{done, total, message, stage: enum[freezing, references, agents, validating, reconciling, publishing, exporting, cancelling],
 agents: {execution: {queued, running, completed, failed, stopped},            // lifecycle (CONTRACTS §12)
          coverage:  {complete, partial, unsupported, not_attempted}},         // content, kept apart (SPEC §7)
 references: {loaded, failed, unsupported}, removed_sources: int, elapsed_s, queue_wait_s, requests, usage_unknown}
```
`stage: cancelling` is shown while the job status stays `running` with `cancel_requested`; the job becomes
`cancelled` only after children and CLI processes are confirmed gone (no new job status, so `useJob` polling and
lane counting are unchanged).
Endpoints (new, read-only; polled 3–5 s only while the panel is open):
- `GET /projects/{id}/fa-interfaces/runs` — list; `GET …/runs/{run_id}` — run header, per-source rows
  (filename, discipline, revision, execution/coverage chips, stage, layouts x/y, windows x/y, accepted/held/rejected,
  elapsed, requests, error), unresolved coverage.
- `GET …/runs/{run_id}/agents/{agent_id}` — report + page outcomes + observations (paged).
- `GET …/evidence/{sha24}/{window_id}.png` — crops from the evidence store (role-checked; viewer 403 as today, C).
- `POST …/runs/{run_id}/cancel` — the existing job cancel; progress shows `stage: cancelling` until children are gone.

Components (`frontend/src/components/interfaces/`): run header (counts by state, elapsed, requests/tokens vs cap,
provider readiness banner, Stop); per-drawing agent table grouped by package; "Unresolved coverage" (layouts not
inspected, labels not looked at, received-but-unread drawings, unsupported files with reason); Verification queue
shows ConflictSets with all candidates and crops; provenance badge per schedule row (run, complete/provisional, kept
from run N); orphaned-decision list after migration. Existing `CoverageStrip`/`DrawingsTab` (InterfacesTab.tsx:220,
:826, C) keep working from `received()`.

Never-replace rule in the UI: when a run publishes fewer rows than the previous by > X % (EXAMPLE 20 %) or zero while
the previous had rows, the schedule shows a banner "−N lines vs last run; previous result kept for sources
{…}; this run is provisional because …". A drawing missing from a run (folder unreachable) shows its last good
reading flagged stale, never blank. A source marked `removed` (file gone while the root was reachable, or an older
revision after a newer one was filed) is listed with its last reading and the date, excluded from counts.

## 3. Obsidian export (SPEC §11; one-way, generated)

Status: nothing exists in the repo (C, D §3). Vaults found on this PC: `C:\Users\moham\Documents\Obsidian Vault`
(personal engineering notes, not in Obsidian's registry — A: removed from the switcher) and `C:\Users\moham\Documents\New`
(registered, effectively empty, Properties/Bases on). Recommendation: a **dedicated vault** or top-level `EP Platform/`
in "New"; never mix into the personal vault (owner decision #7).

Config: `obsidian_vault_root: str | None = None` (`OBSIDIAN_VAULT_ROOT`) beside `projects_root/uploads_root/backups_root`
(core/config.py:70-158, C); disabled when unset; writes only under `<root>/EP Platform/` with path-traversal checks; the
vault is never inside the archive (config.py:156-157 "reads the archive, never writes to it", C). Runs as job
`fa_interfaces_obsidian_export` (lane `sync`, EXAMPLE) after a run completes or on a button; activity-logged like
xlsx/pdf exports (routers/fa_interfaces.py:198-224, C).

Vault layout (mirrors Project → Run → Drawing Agent → Page/Layout → Observation → Evidence → Validation →
Reconciliation → Published Record):
```
EP Platform/
  _Agents.md                                   # agent registry: models, prompt versions, effort, CLI version per run
  EP-30880 <name>/
    _Project.md
    Runs/<ts> fir-5-151/
      _Run.md                                  # dashboard: counts by state, elapsed, usage, provider readiness, incidents
      Agents/<sha24> <filename> (<disc>)/_Agent.md   # DrawingAgentReport; one folder per distinct file hash, aliases listed
      Agents/<…>/Layouts/<layout>/_Layout.md   # PageOutcome, regions, windows, unread regions
      Observations/OBS-<id>.md                 # one per observation, links to evidence + validation
      Validation.md  Reconciliation.md  Conflicts.md (review queue)  Incidents.md  Decisions.md
      Published/Schedule.md  Published/Records/IF-<id>.md
    _evidence/<sha24>/<layout>/<window_id>.png # small crops only; large renders by sha+size+app link
    Human/                                     # never written by the exporter after creation
```
Frontmatter per note type: run `{type: run, run_id, job_id, started, finished, execution_state, coverage_state,
scan_version, task_version, prompt_versions, model_id, used_models, substituted_calls, effort, cli_version,
agents_execution_{queued,running,completed,failed,stopped}, agents_coverage_{complete,partial,unsupported,not_attempted},
references_{loaded,failed,unsupported}, requests, tokens, usage_unknown, elapsed_s, queue_wait_s, superseded_by}`;
agent `{type: agent, agent_id, source_id, sha256, discipline,
revision, execution_state, coverage_state, layouts_done, layouts_total, proposed, validated, held, rejected, error}`;
layout `{type: layout, layout, title, floor_keys, kind, outcome, windows_done, windows_total}`; observation `{type:
observation, observation_id, key, instance_kind, finding_state, label_ids, symbol_candidate_id, equipment_anchor,
confidence, evidence}`; record `{type: record, record_id, floor, tag, equipment, modules, status, basis, decision,
source_run}`. Every generated note carries `generated: true`, `generator: ep-platform/<version>`, `content_sha256`.
Label texts are fenced, truncated and marked untrusted.

Human-note safety: the exporter writes only files whose `generated: true` body hash matches `.ep-export-manifest.json`;
a hand-edited generated note is left alone and a `<name>.generated-<run>.md` is written beside it; each generated
note links `## Notes → Human/<same-id>.md`, created once empty and never touched; run folders are immutable;
`Published/Records` is the only "latest" view. Human/ is never read back (decisions stay in the platform with roles
and stale-write checks; read-back would turn markdown edits into schedule changes and reintroduce untrusted input).

Never exported: credentials/.env/tokens; raw system prompts or unrestricted prompts with project data (export
`prompt_version` + hash only); raw model responses beyond structured verdict fields; full extracted text dumps;
matrix/DRF contact details; user e-mails (display names/initials only); absolute OneDrive/SharePoint paths (RD-M1 F001
precedent, C); projects with restricted `ai_policy` (A: owner decides). Per-run evidence size cap EXAMPLE 200 MB.
