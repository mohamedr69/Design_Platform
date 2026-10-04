# FI-P1 — Concurrent drawing-level agents for the FA Interfaces tab: PLAN

Planning package only. Nothing in this folder changes application code, databases, settings or services, and no
scan, job or model call was run to produce it. Companion files: CONTRACTS.md, PERFORMANCE-AND-BUDGET.md,
VALIDATION.md, OBSIDIAN-AND-UI.md, IMPLEMENTATION-SEQUENCE.md; REVIEW.md and MANIFEST.json are added by the
session orchestrator after the critic.

Labels used throughout: **C** = CONFIRMED by reading code/data in this session (own spot-check or researcher A–D,
cited); **A** = ASSUMPTION; **EXAMPLE** = illustrative number/coordinate/budget, not verified. Paths are relative to
`G:\dev (2)\dev\ep-platform\backend\app\` unless noted. Checkout: `ep-platform` branch `main`, HEAD `13eb73c`,
with many uncommitted changes and `backend/app/interfaces/` untracked (C, BRIEF).

## 0. Who produced this (category A: session agents) — stated honestly

| Role | Requested | Actual | Effort |
|---|---|---|---|
| Session orchestrator | Fable, High | Claude Code session on **Claude Opus 5.5** (the main session model cannot be switched mid-session) | not settable |
| Researchers A–D | Opus, High | Agent tool with model override `opus` | the Agent tool exposes no per-call effort; "High" could not be set or verified |
| Consolidating planner (this package) | Fable, High | Agent tool override `fable` (the override → `claude-fable-5-1` mapping is verified for the CLI alias only; for the Agent tool it is **A**) | same: not settable/verifiable |
| Critic | one fresh Opus review | planned, once | same |

Category B (agents inside the application when a user scans) is a separate question answered in §12 and in
PERFORMANCE-AND-BUDGET.md §6: a desktop session's ability to delegate proves nothing about the backend provider.

## 1. Current state at planning time (2026-10-04)

1. Pipeline: `ifc/services/runners.py::run_interfaces_scan` → `interfaces/service.py::scan_project` (:177) →
   `discover()` (:101, os.walk of six discipline folders, DWG/DXF only, PDFs never read) → per file sha256,
   DWG→DXF via `ifc/dxf/convert.py` into `uploads/EP-n/interfaces/<sha24>.dxf` (:215), `scan.read()` →
   `_read_schedules()` (Excel) → `visual.check()` (damper labels, Opus) → **only then** `row.sources = done;
   db.commit()` (:246-249). `build()` (:423) assembles the schedule deterministically from `row.sources`,
   `row.decisions`, `row.manual`. (C)
2. Live incident, project 5 (EP-30880): jobs 142/144 hung in `visual.check → _picture → Plan.picture` on a
   ~150×60 m `ASE-TILE` pattern HATCH from an architect's xref; ezdxf hit its 30 s hatching timeout twice and a
   single 10 m window rendered >12 min; `Plan()` build ~100 s, ~2 GB RAM; Stop did not stop because all windows
   are rendered inside the submit dict comprehension before any `check()` (visual.py:314-315) (C, BRIEF + A §2).
3. Saved reading degraded: `project_fa_interfaces` for project 5 holds **1 source** (FA IFC, ARCH) and 158
   decisions, 157 of them orphaned; job 139 (folder unreachable, 1 drawing) replaced job 95's 13-source reading
   (C, A, D). 49 damper decisions use whole-metre anchors that current code can never match again (C, A).
4. Every in-app model call fails today: `.env` `AI_CLAUDE_CLI` points at a `claude.exe` under another Windows
   user's folder that does not exist on this PC → `ClaudeCodeProvider._cli=None` → `AiResponse(error="auth")`
   with latency 0 (provider.py:484-485, 529-530) (C). 10 `fa_interfaces_visual` rows today are `auth` (C, C §2).
5. Owner-approved uncommitted change (earlier today): "Received" comes from a stat-only folder listing
   `service.received()` (:1009-1040) with per-file read/failed/superseded/unread and fallback to saved sources when
   the folder is unreachable (C). The IFC worker is **stopped**; jobs 142/144 cancelled; job 146 (fa_redesign_plan)
   queued (C, BRIEF).
6. No evaluation set, no interfaces accuracy metric, no Obsidian code exists in the repo (C, D §1, §3).

## 2. Audit of the existing pipeline (SPEC §1)

| # | Component (C) | Reusable | Demonstrated problem (C unless A) | Proposed change | Callers | Validation |
|---|---|---|---|---|---|---|
| 1 | Discovery/classification `service.discover` :101-146; `_stem/_REVISION` :85-99; FA IFC in force as ARCH :138 | Yes, as work list | Unreachable root → empty walk, no error → FA-only list published (project 5) | Freeze a manifest; abort (no publish) **only when the project root** is unreachable (`os.path.isdir` as `received()` :1018 does); an absent or empty discipline folder (the test project creates only 3 of 6, C) goes through the per-source guard with a banner, never an abort | scan_project, received, coverage | Root renamed mid-scan → prior entries kept; R1 removed + R2 added → counted once |
| 2 | Layout enumeration `ifc/dxf/sheets.read_sheets` :354; `sheet_for` first-match :441 | Yes | A: overlapping key-plan/detail viewport claims a label first | Per-agent per-layout stats; label with ≥2 containing windows → `ambiguous_sheet` flag, never dropped | scan.read, review, BOQ | Fixture with overlapping viewports |
| 3 | Conversion `convert.py` (one per process, 300 s, no cancel); rendering `visual.Plan` :153-213 | Conversion yes; rendering no | Unbounded hatch render (incident); DXF parsed twice (scan.py:82, visual.py:161) | Killable render subprocess, per-window timeout, hatch policy; one parse per drawing per agent | visual.check | SM-104 window under timeout |
| 4 | Text extraction `scan._texts` :31-73, `read` :76-122 | Yes | Paper-space text, MLEADER/LEADER, MINSERT unread; no handles/bboxes stored (B §1) | Extend items with `entity_path`, text bbox, layer, xref flag; read LEADER/MLEADER | service, review/geometry | Existing tests + new fixture |
| 5 | Detection `detect.detect` :177 | Yes | "SD" door-tag ATTRIB → MEDIUM damper (B §2) | Keep as candidate generator; add xref/door-tag evidence flags | scan, schedules | Existing tests |
| 6 | Visual requests `visual.check` :278-348; `_ask` :257 | Prompt/schema yes; loop no | No cancel while rendering; failures dropped silently (:328); SM DXF filed as DXF never looked at (:299-301); gates on `ai_enabled` not `ready` (:286) | Per-window cancellable task (render→ask), readiness gate, persist per window | service.scan_project | Cancel ≤1 window; SM DXF test |
| 7 | Association (model fraction → drawing coords :336-338; `_read_source` :492) | Conservative; keep | Model point never checked against geometry (B §2) | Snap to symbol candidate; hold-all on conflict | redesign | tests :443-534 pinned |
| 8 | Dedup `_clusters` :379; winner/shadow `_equipment_rows` :661; `_once` :794 | Project-level merge yes | 1 % sheet-height clustering merges adjacent equipment; `_once` drops tagged items on typical plans (B §4) | Count by distinct `symbol_candidate_id`; identity includes floor for typical sheets | build | Fixtures per case |
| 9 | Matrix `matrix.RULES` | Yes, authoritative | None | None (model proposals cannot alter rules) | export, pdf, redesign | — |
| 10 | Decisions `row.decisions`, applied in build :443-459 | Storage yes; ids no | 157/158 orphaned; ids built from model coordinates (:719-722) | Re-key to a **sha-independent** `decision_key` (discipline + drawing stem + key + tag identity + floor, or symbol signature/handle path + position); carry forward on a new revision as stale/re-confirm, never auto-applied; show orphaned decisions | router, redesign, export | Decision survives reread and revision |
| 11 | Caching `assist._call` cache key (compliance/assist.py:265-272) | Partly | No `effort`/CLI version in key; alias strings cached; incomplete visual restarts | Key adds effort + CLI version + full model id; keep answered windows | visual.check | Cache-hit test |
| 12 | Publication: single JSON column, commit at end (:246-249); rollback on cancel (jobs.py:224-234) | No | Partial/failed run replaces whole list; one writer | Per-drawing durable readings + one publisher with the guard (`removed`/`stale` statuses, new `generation` column on `project_fa_interfaces`); old scan path routed through the same publisher; one dedup key per project across both job kinds | build, coverage, redesign, draftsman | Kill mid-scan → prior survives |
| 13 | UI progress `InterfacesTab.tsx` :67-131; coverage/received | Mostly | Bar reset per drawing; visual status never surfaced | Per-drawing agent table, run header | api.ts, useJob | Manual check |

Cross-cutting (C): job lane `ifc` limit 2 across workers (jobs.py:67-89); visual pool `drawing_review_parallel=2`
inside a slot (config.py:345); provider semaphore `ai_max_concurrency=2` **per process** (provider.py:488) so API +
two workers can run ~6 CLI processes; heartbeat is process liveness, not progress (jobs.py:441-454), so a hung render
never goes stale (C §5). Drawings Review already saves after every look (review/service.py:229-234) — the pattern to
copy.

## 3. Target architecture

```
 user → POST /fa-interfaces/scan/jobs ─► job fa_interfaces_run (lane ifc, 1 slot = the orchestrator thread)
                                            │
   ┌────────────────────────────────────────┴───────────────────────────────────────┐
   │ RUN ORCHESTRATOR (deterministic Python; app/interfaces/agents/orchestrator.py)  │
   │  1 freeze SourceManifest   2 ReferenceStore (floors, legends, schedules, matrix)│
   │  3 dispatch DrawingAgents via Scheduler leases  4 validate as reports arrive    │
   │  5 reconcile (deterministic) + Fable adjudication of bounded conflict packets   │
   │  6 assemble schedule (build())  7 publish (guarded, idempotent)  8 report/export│
   └───────┬───────────────────────────┬───────────────────────────┬────────────────┘
           ▼                           ▼                           ▼
   DrawingAgent fe304ccf… (SM)   DrawingAgent 8eea8dd6… (HVAC)   DrawingAgent 60de2a37… (ARCH)   (one per distinct file hash)
   enumerate → regions (deterministic, model only off-viewport) → legend → symbol candidates → associate (Opus) → sweep (Opus) → checkpoint → report
           │ one spawn Process per drawing (load, render all windows to the evidence store, exit); model calls = single bounded `claude -p` subprocesses
           ▼
   Scheduler: in-memory pools in the orchestrator process (render 2 · geometry by GB · writer 1/source)
              + ONE cross-process DB lease pool `model` N∈{2,4,6}, taken inside the provider wrapper by EVERY caller
```

Roles (SPEC "Fable coordinates… deterministic code controls…"): the owner's intent is met with a deliberate split —
**deterministic Python** owns assignments, queue, leases, budgets, state transitions, arithmetic, validation
constraints, publication and the per-run summary (templated). **Fable (claude-fable-5-1)** has exactly one in-app
role: adjudicating a bounded, evidence-backed ConflictSet packet during reconciliation, behind
`FA_ADJUDICATION_ENABLED` (default off). Consequence stated plainly: with the default, **Fable does no in-app work**
and the run is Opus + deterministic code; reference excerpts "through Fable" (SPEC §2) are served by the
orchestrator's deterministic ReferenceStore with no model call. Both are owner decision #11 (§13). **Opus
(claude-opus-5-5)** is the drawing agent/reviewer model, each step one schema-constrained call.

New package (proposed) `app/interfaces/agents/`: `manifest.py`, `references.py`, `scheduler.py` (in-memory pools),
`render.py` (per-drawing spawn Process), `agent.py` (state machine), `steps/{regions,legend,symbols,associate,sweep}.py`,
`validate.py`, `reconcile.py`, `publish.py`, `report.py`, `obsidian.py`; plus `app/ai/gate.py` (cross-process `model`
lease inside the provider wrapper, used by all callers). Reused unchanged: `discover`, `read_sheets`,
`scan.read`, `detect`, `matrix`, `build()` and its project-level merge, `export/pdf`, `convert`, `assist.call_task`,
`review._budget`, FA BOQ `ifc/dxf/extract.py` symbol machinery (handles, bbox, signature — B §3).

## 4. Proposed workflow (SPEC target flow → mechanism)

| Step | Mechanism | Persisted in (CONTRACTS.md) |
|---|---|---|
| Discover & freeze | `discover()` + schedules + FA IFC; abort only if the project root is unreachable; sha256 per file; DWG→DXF conversion (cached) and `read_sheets` enumeration **inside the freeze** so `expected_layouts` is in the manifest before extraction (SPEC §2); one `SourceEntry` per distinct hash (paths as aliases) incl. unsupported (PDF, unconvertible) — never silently excluded | `fa_interface_runs.manifest`, `fa_interface_sources` |
| Prepare references | ReferenceStore: floor names/aliases (`Floors`, `drawing_log.floor_identity`), legends (per-drawing legend regions, extracted by agents and merged), equipment schedules (`_read_schedules`), matrix `RULES` version, revision relationships (`revisions.in_force`). Agents start before the snapshot is final; observations carry `reference_version` and are marked `stale` and revalidated when the snapshot changes | `ReferenceSnapshot` |
| Concurrent drawing agents | One `DrawingAgent` per `SourceEntry`; steps are resumable tasks under leases; a 19-layout DWG is one agent with 19 page tasks; fair scheduling across agents | `fa_interface_agent_runs`, `fa_interface_page_results` |
| Validate as they arrive | Deterministic checks on each observation; disputed physical/association findings → fresh-context Opus reviewer (blind-first protocol) | `ValidationRecord` |
| Reconcile | Deterministic identity merge; conflict sets held with all candidates; Fable adjudication only on packets with evidence; unresolved stays held | `ReconciliationRecord`, `ConflictSet` |
| Assemble | `build()` logic re-pointed at per-drawing readings (same deterministic rules, matrix controls counts) | derived, not stored |
| Publish | Single publisher; per-source guard (keep prior only for the same path when the new read failed; gone file in a present folder or older revision → `removed`; whole discipline folder absent → kept + `stale`); generation CAS on a new `project_fa_interfaces.generation` column | `project_fa_interfaces.sources` (compat) + readings table |
| Report + export | Progress dict + run endpoints; Obsidian one-way export job | OBSIDIAN-AND-UI.md |

## 5. Source inventory & shared references (SPEC §2)

- The manifest is frozen **before** any extraction and is immutable for the run; a file that changes on disk during
  the run is detected at agent start (sha mismatch) → that agent ends `coverage=not-attempted`, reason
  `source_changed`, and the run is marked for incremental rerun. Files discovered but not classifiable
  (unknown discipline folder, odd extension) are listed `supported=false, reason=unclassified` — present in counts,
  never dropped.
- "Received" = discovered (stat only). Read/validated/complete are agent states, never inferred from presence.
- One agent per **distinct file hash**: byte-identical copies in one or more discipline folders are one
  `SourceEntry` with several path aliases, counted once (`source_id = sha24`, CONTRACTS §0).
- Schedules (Excel) and the Interface Matrix are `kind: reference`, never physical sources: no agent, no equipment
  rows from them alone (today `_schedule_checks` already only cross-checks (C, B §5); `_pump_room_pumps` :873-916
  invents pumps from room text and schematic names — to be downgraded to a `schematic` observation, B §5).
- Revision basis per entry: `revision` (from `_stem`), `revision_basis: filename|revisions_table|in_force`, and
  `supersedes[]` (older revisions of the same stem seen in the folder).

## 6. Drawing agent: task boundaries (SPEC §3)

One logical agent = one `SourceEntry` = isolated assignment, context, budget, state, report. It is **not** an OS
process; it is a Python state machine whose heavy steps run in leased child processes and whose model steps are
single `claude -p` calls (never the CLI `--agents` feature — no per-subagent budget/cancel/checkpoint, C §1).

Step sequence per agent (each step = resumable task with checkpoint; model steps marked ●):
1. `enumerate`: layouts/pages (`read_sheets`), units, frame; declare `expected_layouts`. Deterministic.
2. `extract`: texts with `entity_path`, bbox, layer, xref flag; symbol candidates from INSERT/loose geometry
   (`extract.py` machinery); LEADER/MLEADER. Deterministic, geometry lease.
3. `regions` (per layout): **deterministic first** — the existing sheet-kind logic (`_sheet_kind`, `_DIAGRAM`,
   `_NOT_READ`, service.py:83-84, :393-400, C) and viewport windows classify paper-space layouts; ● an Opus
   `regions` call is made only for model-space content outside every viewport (or model-space-only drawings) when
   labels were found there, classifying `plan|schematic|detail|schedule|legend|title_block|other` with bounds.
4. ● `legend`: legend region crop → Opus returns symbol conventions (`symbol_class`, description) → stored as agent
   legend; merged into ReferenceStore legends (per source, versioned).
5. ● `associate` (per window, ≤N labels + candidate symbols drawn with stable numbers): Opus returns per label
   `is_equipment`, `symbol_candidate_id|null`, `equipment_class`, `confidence`, `reason`; may also report labels with
   no located symbol and symbols with no label (`unlabelled_candidates`). Free-form points are allowed only as
   `free_point` and are never accepted without snapping to a candidate (CONTRACTS §6).
6. ● `sweep` (per window where unlabelled candidate symbols of an interfaced class exist): Opus confirms/denies
   unlabelled equipment with evidence. Skipped when no candidates — "detect unlabelled equipment where evidence
   supports", never from schedule alone.
7. `checkpoint` per layout: `PageOutcome` committed (own session, like review/service.py:229-234).
8. `report`: deterministic assembly of `DrawingAgentReport` (counts, hashes, usage, unread regions, refusals) with
   a templated summary; no model call.

Steps 5 and 6 repeat per window and step 3/4 per layout, so an agent makes many bounded calls, each one single
and schema-constrained; the per-agent request allowance (PERFORMANCE-AND-BUDGET.md §3) caps them.

Must-not rules → mechanism: no final business rows (agents write only `fa_interface_page_results`); cannot alter
another agent's results (writer lease `writer:<source_id>`); no equipment from schedule alone (schedules are
references); no nearest-label assumption (association needs symbol candidate + evidence; runner-up ratio recorded);
unread region ≠ empty (`PageOutcome.outcome=unread|partial` with reason; `unread_regions[]`); timeout/budget refusal ≠
"no equipment" (`coverage=partial|not-attempted`, finding state untouched).

## 7. Physical location and multiplicity (SPEC §4, §5) — summary

Represented separately (CONTRACTS §4–§6): `label_anchor` (text insertion/alignment point + bbox, entity path),
`symbol_candidate` (block/loose geometry with handle path, bounds, class), `association` (method, distance,
runner-up, ambiguity), `equipment_anchor/bounds` (from the symbol, never the text), `module_placement` (absent at this
stage; later coordination). CAD frames keep native units + `$INSUNITS`, layout viewport signature, nested transforms;
PDF/raster frames keep page, pixel/normalized coordinates, crop transform and `calibration.status` — metric CAD
coordinates only with a verified transform. Files are not assumed aligned; EP-30880's identical viewports for FA 101 /
M-07-V101 / SM-101 (verified, B §1) are an alignment **candidate** that becomes `verified` only after a control-point
residual check (CONTRACTS §3) — identical viewport parameters are not alignment proof.

Multiplicity: counting unit = distinct accepted `symbol_candidate_id`; labels are many-to-one onto symbols; a leader
with N arrowheads yields N associations; schematic/riser labels are `role=schematic` evidence only; same short tag on
different floors is identity `(key, tag, floor)` unless the tag is floor-prefixed; conflicts hold **all** members.
Never dedupe from text proximity alone (today's `_clusters` radius merge is retired for symbol-bearing keys).

Correctness before evaluation: VALIDATION.md §1 defines per-type tolerances (EXAMPLE values) — no single global
distance threshold.

## 8. Reporting to the orchestrator (SPEC §7) — summary

Every agent ends with a `DrawingAgentReport` (machine-readable) plus a templated readable summary; lifecycle is split
into `execution_state` (queued/running/completed/failed/stopped), `coverage_state` (complete/partial/unsupported/
not-attempted) and per-finding `finding_state` (proposed/validated/held/rejected/stale). The run report accounts for
**every** manifest entry: drawings by agent coverage state, schedules/references by `reference_state`
(loaded/failed/unsupported). A run with any agent not `complete` or any reference not `loaded` may publish a
**provisional** schedule labelled as such and can never claim a complete accepted schedule.

## 9. Cross-drawing reconciliation (SPEC §8) — rules

Within one file the identity is the symbol (`symbol_candidate_id`). **Across files** symbol ids are per file and
are never compared; cross-file identity = same `equipment_key` + same `floor_key` + (tagged) same tag identity, or
(untagged) equipment anchors within the per-type tolerance (VALIDATION.md §1) **in a verified common frame**
(`Alignment.verified=true`, CONTRACTS §3). Without a verified alignment, untagged counts per (key, floor) from
different files are compared, never unioned: equal → merged by count with both sources cited; unequal → a
`ConflictSet` holding all members (replaces today's winner/shadow rule, B §5). Deterministic rules: schedule rows
never count; repeated schematic references never add equipment; identical tags across floors are **not** collapsed
(flagged); typical-floor multiplication only with `sheet.multiplier` support from the title (`parse_floors`) and
applicability from the reference snapshot. Fable adjudicates only `ConflictSet`s with ≥2 candidates and evidence
crops/excerpts attached, when enabled; its verdict is a proposal (`finding_state` stays `held` until an engineer or a
deterministic rule accepts). Matrix arithmetic is never delegated.

## 10. Validation & acceptance (SPEC §9) — summary

Deterministic checks on every observation (frame sanity, symbol-class allowed by matrix, point inside bounds, sheet
and floor consistency, xref/door-tag exclusion, duplicate symbol id) then, for physical-symbol and association
findings that are disputed or low-confidence, a **fresh-context Opus reviewer** receives crop + reference excerpt and
answers *before* seeing the extractor's answer; Python compares; disagreement stays held. Confidence strings never
accept anything. Engineer decisions keyed to stable identity survive rereads; a reread can only mark them `stale`
with the reason, never override. Full detail: VALIDATION.md.

## 11. Reliability, budgets, resume (SPEC §10) — summary

One writer per drawing (in-process lock); idempotent publication (generation CAS, content hashes); `ai_usage` row
committed **before** dispatch (status `dispatched`) and finalised after (killed calls stay `dispatched` = usage
unknown); append-only attempt history; cancelling shown as `progress.stage=cancelling` while the job stays `running`
with `cancel_requested` (no new job status), `cancelled` only once child/CLI processes are confirmed gone (Windows Job
Object with kill-on-close + startup reaper); checkpoints per layout/window; cache key bound to
source sha, task, prompt version, full model id, effort, CLI version, policy and reference version; stale marking
when any input changes. Request caps are enforceable before dispatch; token figures are estimates until the provider
reports; post-response breakers are not caps. Detail: PERFORMANCE-AND-BUDGET.md.

## 12. Models and providers (category B) — what the application can run today

| Need | ClaudeCodeProvider (configured, `AI_PROVIDER=claude-code`) | ClaudeProvider (API) |
|---|---|---|
| Any call at all | **No**: `_cli=None` (nonexistent `AI_CLAUDE_CLI` path) → `auth` without a process (C) | Needs an Anthropic credential (not inspected); Fable needs 30-day retention (BRIEF 7) |
| Opus 5.5 `claude-opus-5-5` | With the PATH CLI 2.1.263: rejected, needs ≥2.1.280 (C, BRIEF 5). The `.env` path names a 2.1.286 binary that exists on another PC (A) | Expected to run (**A**: no credential inspected or tested) |
| Fable 5.1 `claude-fable-5-1` | Works on 2.1.263 (C) | **Not clean**: `ClaudeProvider` sends Fable with `betas=[server-side-fallback]`, `fallbacks="default"` (provider.py:251-253; docstring :176 "a decline is answered by an Opus model"), and every return reports the *requested* id (`model=model`, :263-299, never `message.model`) → a fallback answer would be logged as Fable: a **silent substitution** unless disabled or detected (C) |
| Model actually used | first non-haiku `modelUsage` key, else the requested id (:568) (C) | never read from the response (C) |
| Effort "high" | **Never passed** (provider.py:538-541 has no `--effort`); CLI 2.1.263 supports `--effort` (C, C §1) | Honoured, but drawing callers pass none → runs at `AI_EFFORT=low` (config.py:360) (C) |
| Output-token cap | not enforceable: no output limit is passed to the CLI (:538-541) (C) | `max_tokens` enforced |
| Aliases | `opus` → claude-opus-5 (**a substitution**, must not be used); `.env` `AI_MODEL_STANDARD=opus` therefore is one today (C, BRIEF) | n/a |
| Sonnet | `.env` `AI_MODEL_SMALL=sonnet` → IFC symbol review runs on Sonnet — conflicts with "no Sonnet substitution"; **owner decision**, unchanged here | — |
| PDFs | not read by the interfaces pipeline at all (service.py:115) (C) — manifest lists them `unsupported:pdf_not_supported` until a PDF reader exists | — |

Rules adopted: (1) if the configured drawing-agent model is not runnable (provider not ready, CLI too old, model
rejected), agents end `coverage=unsupported` with `reason=model_unavailable:<detail>` and the run says so; nothing is
substituted and no model id is invented. (2) `used_model_id` is always taken from the response (`modelUsage` on the
CLI, `message.model` on the API) — never echoed from the request; FA steps (agent, reviewer, adjudication) are sent
**without** server-side fallbacks, and any response whose model differs from the requested id is recorded
`model_substituted` and the finding is **held**, never accepted. Smallest practical alternative for the owner to
choose: (a) install/pin a CLI ≥2.1.280 under the worker's user and point `AI_CLAUDE_CLI` at it, or (b) switch
`AI_PROVIDER=claude` with a credential, pass `effort="high"` from the drawing callers and apply rule (2) to the API
provider. Both require restarting API and both workers (`get_settings` is `lru_cache`d, config.py:428; provider
built once per process, provider.py:584-603) (C).

## 13. Decisions needed before implementation (owner)

1. Provider path: pinned CLI ≥2.1.280 under the worker user vs API provider with credential (and retention terms for Fable).
2. `AI_MODEL_SMALL=sonnet` for IFC symbol review: keep (documented exception) or move to Fable/Opus.
3. Replace `AI_MODEL_STANDARD=opus` alias with a full id (which one).
4. Concurrency test range: confirm 2/4/6 model slots and the shared PC budget (RAM ~2 GB per loaded 31 MB DXF, C).
5. Per-agent/run call and time caps (EXAMPLE values in PERFORMANCE-AND-BUDGET.md §3).
6. Reconciliation adjudication by Fable: enabled, or engineer-only until the evaluation set exists.
7. Obsidian vault root (dedicated vault recommended, D §3) and what may be exported for restricted projects.
8. Ground-truth annotation effort (≈1–2 engineer-days for two exhaustive drawings, EXAMPLE/A, D §1).
9. Whether the symbol-candidate work (handles/bboxes) may reuse `ifc/dxf/extract.py` as-is or needs a shared module.
10. Decision re-keying migration for the 158 existing decisions: only tagged decisions are auto-mapped; untagged and
    visual-damper decisions go to re-confirmation (CONTRACTS §14).
11. Fable's in-app role: ConflictSet adjudication enabled (`FA_ADJUDICATION_ENABLED=true`) vs engineer-only; and
    reference excerpts served by the deterministic ReferenceStore rather than by a Fable call. With adjudication off
    (the proposed default) Fable does no in-app work at all; the run summary is templated in either case.

## 14. Risks and assumptions to verify early

- Render determinism (PNG-keyed cache hit rate) (A). Handle stability across conversions/revisions (A, B §3).
- Whether `claude -p` children survive pool cancellation (A) — the Popen/kill design assumes they must be killed.
- GIL starvation masking heartbeats during PyMuPDF rasterising (A, C §5) — process isolation removes it.
- Overlapping viewports in real sets (A). Subscription rate limits at 4–6 concurrent CLI processes (A).
- `document_sha256` suffix exceeds `String(64)` (models.py:1459) — fine on SQLite, breaks on Postgres (C).

## FINAL HANDOFF

1. **What the current implementation supports**: deterministic discovery with revision ranking, DWG→DXF conversion
   cache, model-space text extraction with nested blocks, prefix/word detection, per-window damper look with a
   sound prompt/schema, label/equipment anchors kept apart, project-level dedup and matrix arithmetic, engineer
   decisions and manual items, xlsx/pdf export, job lanes with cancel/recover, result cache and usage log, and (since
   today, uncommitted) a stat-only "Received" listing. Drawings Review already shows the save-per-look pattern.
2. **What must change**: publication (single JSON column, end-of-run overwrite, one writer); uncancellable
   unbounded rendering on the job thread; provider readiness/effort/model-id handling; decision ids built from model
   coordinates and paths; text-proximity dedup and winner/shadow undercounts; no symbol/handle/leader geometry; no
   per-drawing progress or visual status in the UI; no evaluation set; no Obsidian export.
3. **One-agent-per-drawing boundaries**: §6 — one agent per distinct source file hash (all its layouts/pages,
   paths as aliases), eight resumable steps; the model steps (regions off-viewport, legend, associate, sweep) are
   single bounded schema-constrained Opus calls **repeated per layout/window** under a per-agent request allowance;
   one writer per source; report per agent.
4. **Global concurrency limits and measurement**: in-memory pools in the orchestrator process (render 2, geometry by
   estimated GB with limit 4 — EXAMPLE, writer 1 per source) plus one cross-process DB lease pool `model` (2|4|6 test
   knob) taken inside the provider wrapper by every caller so nested limits never multiply; per-drawing spawn
   processes with terminate(), Windows Job Objects and a startup reaper; measurement plan in
   PERFORMANCE-AND-BUDGET.md §5 (elapsed from first dispatch, queue wait separately, time-to-first-reviewed-result,
   render time, model latency p50/p95, peak RAM, timeouts/throttles, requests/tokens, accuracy per setting).
5. **How physical location will be proven**: symbol candidates with stable ids and bounds; association evidence with
   runner-up; snapping of any free point to a candidate; per-type tolerances; fresh-context blind reviewer; ground-
   truth annotations with physical handles; location/association metrics (VALIDATION.md).
6. **How every drawing reports**: `DrawingAgentReport` (CONTRACTS §8) with execution/coverage/finding states; the run
   report accounts for every manifest source; provisional publication clearly labelled.
7. **Remaining model/provider limitations**: §12 — no in-app call works today; Opus 5.5 needs CLI ≥2.1.280; effort
   not passed by the CLI provider; no output-token cap enforceable on the CLI provider; `opus` alias is a
   substitution; the API provider sends Fable with server-side fallbacks and reports the requested id (silent
   substitution unless disabled/detected); API readiness untested (no credential inspected); Sonnet configured for
   IFC symbol review (owner); PDFs unsupported by the interfaces pipeline.
8. **Decisions needed**: §13 (eleven items).
9. **Smallest first implementation task**: Stage 0.1 — publication guard in `scan_project`: abort only when the
   project root is unreachable; keep a prior reading only for the same (discipline, relative_path) whose new read
   failed; a file gone from a present discipline folder, or an older revision of the same stem, becomes `removed`
   (excluded by `build()`); a wholly absent discipline folder keeps its readings, flagged `stale`; tests incl. R1-removed + R2-added counted once (IMPLEMENTATION-SEQUENCE.md §1).
10. **Package location and review status**: `docs/milestones/fa-interfaces/FI-P1-DRAWING-AGENTS-PLAN/` — Reviewed
    once by a fresh Opus critic (29 findings); dispositions and fixes in REVIEW.md.

This planning work did not improve the application's accuracy or speed; it only describes how those could be
measured and changed.
