# FI-P1 — CONTRACTS: source, drawing-agent, coordinate, observation, report and lifecycle schemas

Schemas are written JSON-schema-like (`field: type` with enums); `?` marks optional. All sample values are
**EXAMPLE** unless marked verified (EP-30880 facts from research B/C). Hashes are lowercase hex sha256; `sha24` is
its first 24 characters (as `uploads/EP-n/interfaces/<sha24>.dxf`, service.py:215, C). Drawing text, extracted text
and model output are **data**: every `text` field is stored truncated and rendered fenced; nothing in a contract is
ever interpreted as an instruction by the orchestrator.

## 0. Identifier conventions

| Id | Format | Example (EXAMPLE unless noted) |
|---|---|---|
| `run_id` | `fir-{project_id}-{job_id}` | `fir-5-151` |
| `source_id` | `{sha24}` — content-bound, path-independent; byte-identical copies in any folder are ONE entry with path aliases, one agent, counted once | `fe304ccf…` (prefix verified, rest truncated) |
| `agent_id` | `DA-{run_id}-{sha24}` | `DA-fir-5-151-fe304ccf…` |
| `frame_id` | `{sha24}:F:model` · `:F:paper:{layout}` · `:F:page:{n}` · `:F:crop:{window_id}` | `8eea8dd6…:F:model` |
| `label_id` | `{sha24}:L:{entity_path}`; fallback `{sha24}:L:@{layout}\|{x:.2f},{y:.2f}\|{text[:40]}` (today's `visual.item_id`, visual.py:89-91, C) | `8eea8dd6…:L:5741C` (handle verified) |
| `symbol_candidate_id` | `{sha24}:S:{handle_path}` (outer INSERT handles `/` inner entity; nested content needs the path, B §3) | `8eea8dd6…:S:5741B` (verified) |
| `window_id` | `{sha24}:W:{layout}:{x0:.1f},{y0:.1f}` | `8eea8dd6…:W:M-07-V101:712.0,150.0` |
| `observation_id` | `OBS-` + sha256(`source_sha256\|layout\|label_id\|symbol_candidate_id\|key`)[:16] | `OBS-3f9a0c…` |
| `record_id` (published) | `IF-` + sha256(`project_id\|floor_key\|key\|identity`)[:16] | `IF-71be…` |
| `decision_key` (new) | **sha-independent** (a re-save, re-bind or new revision must not orphan decisions): tagged `D\|{discipline}\|{stem}\|{key}\|{tag_identity}\|{floor_key}`; untagged physical `D\|{discipline}\|{stem}\|{layout}\|{key}\|{symbol signature or handle_path}\|{cx:.1f},{cy:.1f}` using the **symbol centre** (never the label or a model point); conflict `D\|conflict\|{hash of member decision_keys}`. `stem` from `_stem()` (service.py:92-98, C). Replaces coordinate-based ids (:719-722, C) | `D\|HVAC\|VENTILATION LAYOUT\|M-07-V101\|motorized_smoke_fire_damper\|A$C0e331ec6\|719.5,154.2` |

Versions carried by every stored object: `task_version` (string), `schema_version` (this document, `"fi-p1.1"`),
`prompt_version` (per step, e.g. `interface-dampers-visual-2026-10-04.3` is today's, visual.py:38, C),
`scan_version` (`scan.SCAN_VERSION`), `reference_version`, `model_id` (full id, never alias), `effort`,
`cli_version?`.

## 1. SourceManifest (frozen before extraction; SPEC §2)

```
SourceManifest {
  run_id: string, project_id: int, job_id: int, frozen_at: datetime,
  project_ref: string                         // "EP-30880" (verified)
  source_root_reachable: bool                 // project root; false → run refuses to publish (PLAN §5)
  discipline_roots: [{discipline: enum[SM,FF,HVAC,ACS,GB,ARCH,SCHED], folder: string, state: enum[present, absent, empty]}],  // absent/empty never aborts
  entries: [SourceEntry], reference_snapshot_id: string|null,
  manifest_sha256: string                     // hash of entries, for MANIFEST/Obsidian binding
}
SourceEntry {
  source_id: string /* sha24 */, sha256: string, size: int, mtime: float,
  paths: [{discipline: enum[SM,FF,HVAC,ACS,GB,ARCH,SCHED], relative_path: string, filename: string, package: string}],  // ≥1; aliases of one file
  file_type: enum[dwg, dxf, pdf, xlsx, other],
  kind: enum[folder, fa_ifc, schedule, reference],                   // schedule/reference never get an agent
  revision: string|null, revision_basis: enum[filename, revisions_table, in_force, unknown],
  supersedes: [string], superseded_by: string|null,
  expected_layouts: [string]|null,            // enumerated IN THE FREEZE (conversion + read_sheets, cached) for every supported drawing; null only when unsupported
  expected_pages: int|null,                   // PDF only
  agent_id: string|null,                      // null for kind schedule|reference
  reference_state: enum[loaded, failed, unsupported]|null,           // kind schedule|reference only; a terminal status for the run report
  supported: bool, unsupported_reason: enum[none, pdf_not_supported, no_converter, conversion_failed, unclassified, unreadable]|null,
  links: {legends: [string], schedules: [string], matrix_version: string, revision_group: string|null}
}
```

## 2. ReferenceSnapshot (shared, read-only to agents)

```
ReferenceSnapshot {
  reference_version: string,                  // sha256 of the canonical JSON below [:16]
  floors: [{floor_key: string, names: [string], aliases: [string], source: string}],   // Floors / floor_identity
  legends: [{source_id: string, layout: string, entries: [{symbol_class: string, text: string(≤160), bounds: Bounds?}],
             extracted_by: string /*agent_id*/, status: enum[proposed, validated]}],
  schedules: [{source_id: string, sheet: string, rows: [{key: string, tag: string, floor_keys: [string], qty: int?}]}],
  matrix: {name: string, version: string, rules: int, unclear_rows: [int]},          // matrix.RULES (C)
  revisions: [{stem: string, in_force: string, superseded: [string]}],
  status: enum[preparing, ready]
}
ReferenceExcerptRequest { agent_id, kind: enum[floor, legend, schedule, matrix_rule, revision], key: string }
ReferenceExcerptResponse { reference_version, kind, key, excerpt: object, served_by: "reference_store" }   // deterministic, no model call
```

## 3. Coordinate frames, points, bounds, transforms (SPEC §4)

```
CoordinateFrame {
  frame_id: string, source_sha256: string,
  kind: enum[dxf_model, dxf_paper, pdf_page, raster_px, crop_px],
  units: enum[mm, cm, m, in, ft, unitless, px, normalized],    // scan._UNITS values + px/normalized (C)
  metre: number|null,                       // units per metre; null when unitless/px (today _METRE falls back to 1.0 — must not, B §1)
  layout: string|null, page_index: int|null,
  viewport: {cx,cy,w,h,twist,tx,ty}|null,   // sheets.Window fields (C)
  viewport_signature: string|null,          // sha256 of viewport tuple [:12]; equality ≠ alignment proof
  rotate_deg: int|null, cropbox: Bounds|null,          // PDF
  y_axis: enum[up, down],
  parent_frame_id: string|null,
  to_parent: [[a,b,c],[d,e,f],[0,0,1]]|null,           // affine; null = no verified transform
  calibration: {status: enum[none, viewport, control_points, title_scale, verified_alignment],
                residual_m: number|null, points: int|null, verified_by: string|null}
}
Point  { frame_id: string, x: number, y: number }
Bounds { frame_id: string, x0: number, y0: number, x1: number, y1: number }
Alignment { project_id, a_frame_id, b_frame_id, verified: bool,
            method: enum[identical_viewport_candidate, control_points, none],
            control_points: int|null, residual_m: number|null, verified_by: string|null }
```
Rules: a `Point` in a `crop_px` frame converts to its parent via `to_parent` only; metric coordinates for PDF/raster
exist only when `calibration.status ∈ {control_points, title_scale, verified_alignment}` with `residual_m` recorded
(EXAMPLE acceptance ≤ 0.2 m). `verified=true` **only** with `method=control_points` (≥3 matched features such as grid
bubbles/intersections, EXAMPLE) and `residual_m` within acceptance; identical viewport parameters (EP-30880 FA 101 /
M-07-V101 / SM-101, verified fact B §1) produce an `identical_viewport_candidate` with `verified=false` until that
check — consistent with `viewport_signature` equality not being alignment proof. Cross-file position comparison
requires `verified=true`.

## 4. DrawingAgentAssignment (input; immutable for the attempt)

```
DrawingAgentAssignment {
  agent_id, run_id, source: SourceEntry, source_sha256: string,
  assigned_layouts: [string]|"all", assigned_pages: [int]|"all",
  reference_version: string, task_version: string, schema_version: string,
  prompt_versions: {regions: string, legend: string, associate: string, sweep: string},
  model: {model_id: "claude-opus-5-5", effort: "high", provider: string},   // full id; refused if unavailable
  allowances: {max_requests: int, max_elapsed_s: number /* from first dispatch, queue wait excluded */,
               max_output_tokens_per_call: int /* enforced by the API provider only; informational on the CLI provider, which passes no output limit (provider.py:538-541, C) */,
               request_timeout_s: number, render_timeout_s: number},        // EXAMPLE values: PERFORMANCE §3
  allowed_tools: [enum[read_dxf, render_window, read_pdf_page, reference_excerpt]],   // read/render only
  attempt: int, resume_from: {layouts_done: [string], windows_done: [string]}|null
}
```

## 5. Labels, symbol candidates, associations

```
LabelInstance {
  label_id, source_sha256, layout: string, frame_id: string,
  text: string(≤160, fenced on display), text_sha256: string,
  entity_path: [string],               // DXF handles outer→inner; [] when unavailable
  entity_kind: enum[TEXT, MTEXT, ATTRIB, LEADER_TEXT, MLEADER, PDF_WORD, OCR_WORD],
  layer: string|null, xref_origin: bool,            // "$0$" in chain → architect xref (B §2)
  sibling_attribs: [string]|null,                   // e.g. ["04"] beside "SD" in a DOOR TAG block (verified case)
  label_anchor: Point, label_bounds: Bounds|null, text_height: number|null,
  detected: {key: string, kind: string, confidence: enum[high, medium, low], tag: string|null, detail: string|null}, // detect.detect (C)
  region_role: enum[plan, schematic, detail, schedule, legend, title_block, other, unknown],
  containing_sheets: [string], ambiguous_sheet: bool
}
SymbolCandidate {
  symbol_candidate_id, source_sha256, layout, frame_id,
  origin: enum[insert, nested_insert, loose_geometry, pdf_vector, raster],
  block_name: string|null, anonymous: bool, handle_path: [string], layer: string|null,
  bounds: Bounds, centre: Point, rotation_deg: number|null, scale: [number, number]|null,
  signature: string|null,                           // geometry signature (extract.py G.signature pattern, B §3)
  symbol_class: string|null, class_basis: enum[legend, block_name, signature_match, model, none],
  on_layer_kind: enum[duct, pipe, wall, unknown]
}
Association {
  label_id, symbol_candidate_id: string|null,
  method: enum[same_block, leader, nearest_insert, model, none],
  distance_m: number|null, runner_up_id: string|null, runner_up_distance_m: number|null,
  ratio: number|null,                               // runner_up/best; EXAMPLE accept ≥ 1.5
  leader: {vertices: [Point], arrowheads: [Point]}|null,
  ambiguous: bool, evidence: [EvidenceRef], model_reason: string(≤200)|null
}
EvidenceRef { kind: enum[crop_png, legend_excerpt, schedule_row, text_excerpt], ref: string /* evidence store key */, sha256: string }
```
Verified example (ventilation DXF 8eea8dd6…, B3 pump room, research B): labels `5741C` (719.25,154.40) and `5741E`
(720.07,154.66) m, 0.86 m apart; symbols INSERT `5741B` (719.45,154.23) and `5741D` (720.53,154.72) of anonymous block
`A$C0e331ec6`, 1.10 m apart; each label 0.26/0.46 m from its own symbol → two `Association`s with distinct
`symbol_candidate_id`s → **two** equipment items.

## 6. Observation (the unit every validation and reconciliation acts on)

```
Observation {
  observation_id, agent_id, run_id, source_sha256, layout, page_index: int|null,
  key: string,                                      // matrix equipment key, e.g. motorized_smoke_fire_damper
  instance_kind: enum[physical, schematic_reference, schedule_entry, legend_entry, label_without_symbol, symbol_without_label],
  label_ids: [string],                              // many labels → one physical instance allowed
  symbol_candidate_id: string|null,
  association: Association|null,
  label_anchor: Point|null, equipment_anchor: Point|null, equipment_bounds: Bounds|null,
  free_point: Point|null, free_point_status: enum[none, unsnapped, snapped, rejected],   // never "accepted" unless snapped
  crop: {window_id, bounds_model: Bounds, px_w: int, px_h: int, image_sha256: string, to_source: CoordinateFrame.to_parent}|null,
  floor_keys: [string], floor_basis: enum[sheet_title, filename, typical_title, unknown],
  typical: {source_sheet: string, multiplier: int}|null,
  tag: string|null, tag_identity: string|null, tag_scope: enum[global, per_floor, unknown],
  revision: string|null, interface_applicable: bool|null, interface_rule_ids: [int],
  uncertainty: {model_confidence: enum[high, medium, low]|null, detector_confidence: enum[high, medium, low],
                notes: [string]},
  negative: bool,                                   // true for "label present, no equipment" / "not a damper"
  decision_key: string,                             // §0, sha-independent; what engineer decisions attach to
  settled_by_rule: enum[none, same_block, leader_unique_candidate],   // deterministic geometric settlement; otherwise the blind reviewer is required
  finding_state: enum[proposed, validated, held, rejected, stale], held_reason: string|null,
  validation: ValidationRecord|null, reference_version: string, prompt_version: string, model_id: string, effort: string,
  evidence: [EvidenceRef], created_at: datetime
}
```

## 7. Page/layout outcome and checkpoint

```
PageOutcome {
  agent_id, layout: string, page_index: int|null, attempt: int,
  outcome: enum[inspected, partial, unread, unsupported, skipped_duplicate],
  reason: string|null,                              // e.g. "render_timeout:window 712.0,150.0", "no model-space viewport"
  regions: [{role: enum[plan, schematic, detail, schedule, legend, title_block, other], bounds: Bounds, confidence: enum[high,medium,low]}],
  legend_read: bool, windows_total: int, windows_done: int, unread_regions: [Bounds],
  observations: int, requests: int, duration_s: number, checkpoint_sha256: string, committed_at: datetime
}
```
Committed per layout in the agent's own session (pattern review/service.py:229-234, C). Resume replays only
`windows_done` and `layouts_done` from the last checkpoint; unread windows are retried as new charged attempts.

## 8. DrawingAgentReport (SPEC §7)

```
DrawingAgentReport {
  run_id, agent_id, source_id, source_sha256, reference_version, task_version, schema_version,
  model: {requested_id: string, used_id: string|"unknown" /* always from the response: modelUsage (CLI) or message.model (API), never echoed */,
          substituted_calls: int /* responses whose used id ≠ requested; their findings are held */,
          effort_requested: string, effort_applied: string|"unknown", provider: string, cli_version: string|null},
  execution_state: enum[queued, running, completed, failed, stopped],
  coverage_state: enum[complete, partial, unsupported, not_attempted], coverage_reason: string|null,
  layouts: {expected: [string], attempted: [string], outcomes: [PageOutcome]},
  observations: {proposed: int, validated: int, held: int, rejected: int, stale: int, ids: [string]},
  unresolved_associations: [string], rejected_detections: [string], unread_regions: [{layout, bounds: Bounds, reason}],
  requests: {attempted: int, succeeded: int, failed: int, cancelled: int, usage_unknown: int,
             input_tokens: int|null, output_tokens: int|null, estimated_input_tokens: int},
  duration_s: number /* from first dispatch */, queue_wait_s: number /* reported separately */, started_at, finished_at,
  result_sha256: string, evidence_sha256: string,                  // over observations / evidence refs
  summary_text: string(≤2000)                                       // templated, deterministic; no model call (PLAN §3)
}
```
Invariants checked by the orchestrator: every manifest entry has a terminal status — agent entries a
`coverage_state`, schedule/reference entries a `reference_state` — and the run report lists all of them;
`coverage_state=complete` requires every expected layout `inspected` and zero `unread_regions`.

## 9. Validation (SPEC §9)

```
ValidationRecord {
  observation_id, checks: [{name: string, passed: bool, detail: string}],   // deterministic (VALIDATION.md §2)
  review_required: bool, review_reason: enum[model_proposed, ambiguous, conflict, sample, none],   // required for every model-proposed physical/association finding not settled_by_rule
  reviewer: ReviewerReading|null, comparison: enum[not_reviewed, agree, disagree, reviewer_abstained],
  outcome: enum[validated, held, rejected], decided_by: enum[rule, reviewer_agreement, engineer], at: datetime
}
ReviewerReading {                             // fresh Opus context; crop + reference excerpt only; extractor's answer withheld
  reviewer_call_id: string, model_id, effort, prompt_version,
  reading: {is_equipment: bool, symbol_candidate_id: string|null, equipment_class: string|null,
            count_in_crop: int, reason: string(≤200), confidence: enum[high, medium, low]},
  shown: [EvidenceRef], answered_before_reveal: true
}
```

## 10. Reconciliation (SPEC §8)

```
EquipmentIdentity { project_id, floor_key, key, tag_identity: string|null, aliases: [string],
                    source_role: enum[plan, schematic, schedule, fa_drawing], revision_in_force: string,
                    symbol_evidence: [symbol_candidate_id] /* per-file ids, evidence only, never compared across files */,
                    cross_file_match: enum[tag, position_in_verified_frame, count_only, none], alignment_id: string|null }
// cross-file identity: same key + floor + tag identity, or anchors within the per-type tolerance in a frame with
// Alignment.verified=true; otherwise counts per (key, floor) are compared (equal → merged by count; unequal → ConflictSet).
ReconciliationRecord {
  record_key: string /* EquipmentIdentity hash */, members: [observation_id], sources: [source_id],
  rule_trace: [string],                          // deterministic rules applied, in order
  counts: {by_source: {source_id: int}, agreed: int|null},
  conflict_set_id: string|null, state: enum[merged, conflict, single]
}
ConflictSet {
  conflict_set_id, kind: enum[count_mismatch, association_ambiguous, tag_repeat_across_floors, typical_applicability, schematic_vs_plan, revision],
  candidates: [{observation_id, source_id, claim: string, evidence: [EvidenceRef]}],   // ALL retained
  held_members: [observation_id],                   // every affected observation is held
  adjudication: FableAdjudication|null, engineer_decision_key: string|null
}
FableAdjudication {                                 // one bounded call per ConflictSet; proposal only
  call_id, model_id: "claude-fable-5-1", effort, prompt_version, packet_sha256,
  verdict: enum[prefer_candidate, both_valid, unresolved], preferred: [observation_id], reasoning: string(≤400),
  evidence_cited: [EvidenceRef], applied: false                     // never applied by itself
}
```

## 11. Published record and publication guard (SPEC §10–§11)

```
PublishedRecord {
  record_id, project_id, run_id, floor_key, key, tag: string|null, description: string, location: string,
  modules: object /* matrix.modules */, basis: enum[drawing, schedule_check, engineer, manual],
  observation_ids: [string], decision_key: string, provenance: {source_ids: [string], coverage: enum[complete, provisional]},
  decision: {state: enum[none, confirmed, rejected, resolved, dismissed], by: string|null, at: datetime|null,
             stale: bool, needs_reconfirm: bool /* carried forward across a revision: shown, not applied */}
}
PublicationGuard (deterministic, per (discipline, relative_path) entry; `build()` counts status == "read" only, service.py:434, C):
  0. project root unreachable                                              → ABORT the publish; prior list untouched (absent/empty discipline folder is NOT an abort)
  1. present, new read ok (complete, or partial ⊇ old layouts)             → replace (partial → provisional)
  2. present, same path, new read failed/unreadable/unsupported            → keep old entry as is (still "read"), add {stale: true, kept_from: scanned_at, reason}
  3. present, new visual incomplete, same sha as old complete visual        → keep old visual block inside the new entry
  4. present but superseded by a newer revision of the same _stem           → status "superseded" (as discover marks it today, :135)
  5. absent while the root is reachable AND its discipline folder is present and non-empty (file deleted/moved)
                                                                            → status "removed" (NOT "read": excluded by build(); listed with its last reading for the engineer)
  5b. its whole discipline folder absent or empty while the root is reachable (e.g. OneDrive not yet synced, folder renamed)
                                                                            → keep old entry as "read" + {stale: true, kept_from, reason: "discipline_folder_absent|empty"}; counted, banner
                                                                              (SPEC §11: never replace a useful result because discovery failed; no double count — nothing replaces it)
      [orchestrator amendment after the fix pass; see REVIEW.md R-30]
  6. an older revision of the same _stem no longer present after a newer one was filed → "removed" (never counted beside the newer: R1 removed + R2 added = counted once)
Run-level: removed > 0, or published rows < previous by > X % (EXAMPLE 20 %), or == 0 while previous > 0 → banner + provisional; never silent.
Generation CAS: UPDATE project_fa_interfaces SET sources=?, generation=generation+1 WHERE project_id=? AND generation=?   -- `generation` is a NEW column (Stage 1 migration).
```

## 12. Lifecycle state machines

| Machine | States | Allowed transitions | Terminal |
|---|---|---|---|
| Job | **unchanged** statuses queued → running → succeeded/failed/cancelled (jobs.py:64-66 `ACTIVE/FINISHED`, lane count on `running` :306, C). "Cancelling" is `progress.stage = "cancelling"` while status stays `running` with `cancel_requested=1` | `cancelled` is written only when children and CLI processes are confirmed gone | succeeded, failed, cancelled |
| Agent `execution_state` | queued → running → completed/failed/stopped; stopped → queued (resume, attempt+1) | never running→queued without a checkpoint | completed, failed |
| Agent `coverage_state` | not_attempted → partial → complete; not_attempted/partial → unsupported | set only by the orchestrator from PageOutcomes | — (content, not lifecycle) |
| Finding `finding_state` | proposed → validated/held/rejected; validated/held → stale (input changed); stale → proposed (revalidated) | engineer decisions never auto-reverted; reread marks stale with reason | rejected (unless engineer reopens) |
| Request (`ai_usage.status`) | dispatched → ok/failed/cancelled/timeout; a row left `dispatched` after its holder died = `usage_unknown` | append-only rows in `ai_usage` (one table, pre-dispatch status) | all four |

## 13. Model call envelope (provider-independent; extends `AiRequest`, provider.py:48-62, C)

```
ModelCall {
  request_id, run_id, agent_id, step: enum[regions, legend, associate, sweep, review, adjudicate, summarize],
  model_id: string /* full id */, effort: enum[low, medium, high, xhigh, max], tier: null,
  schema_version, prompt_version, system_sha256: string, parts_sha256: string, images: int,
  max_output_tokens: int, timeout_s: number, idempotency_key: string /* cache key incl. effort+cli_version */,
  budget: {run_cap_remaining: int, agent_cap_remaining: int, reserved_input_estimate: int},
  no_fallbacks: true,                                // FA steps never allow server-side model fallbacks
  cancel_token: string
}
ai_usage row (EXISTING table extended by migration; no separate ai_requests table):
  existing: id, project_id, run_id, task, model, tokens…, cost, latency_ms, cache_hit, escalated, outcome, at
  added:    request_id, job_id, agent_id, step, effort, status: enum[dispatched, ok, failed, cancelled, timeout],
            pid: int|null, process_started_at: datetime|null /* for the startup reaper */, dispatched_at, finished_at,
            estimate_input, used_model: string|null /* from the response */, model_substituted: bool, lease_id
  The row is INSERTed with status=dispatched BEFORE the process starts and UPDATEd after; `outcome` keeps the error kind.
```
Provider mapping: `ClaudeCodeProvider` adds `--effort <effort>` and must use full ids (today: no `--effort`,
provider.py:538-541, C); `ClaudeProvider` already maps `effort` → `output_config.effort` (:248-249, C) but sends Fable
with `fallbacks="default"` (:251-253) and returns `model=model` (the request) on every path (:263-299, C) — it must
(a) omit fallbacks when `no_fallbacks`, and (b) set `AiResponse.model` from `message.model`. The wrapper compares
`used_model` with `model_id`: mismatch → `error="model_substituted"` for FA steps (finding held, never accepted). A
provider that cannot honour `model_id` returns `error="unsupported_model"` (new kind) — never a substitute.

## 14. Decision re-keying

Existing decision ids (service.py:719-722, C) encode `discipline|relative_path|sheet|key|anchor|floor`; the
`%.1f` visual-damper anchors are the **model's answer point**, not the label (:564-566, C). Migration rules:
- **Tagged** decisions (tag identity present in the id): auto-mapped to the new `decision_key` by
  (discipline, stem, key, tag identity, floor) when exactly one match exists.
- **Untagged and visual-damper** decisions (incl. the 49 whole-metre anchors, A §0): **never auto-mapped** — a
  position match would silently change meaning (the confirmed merged count-2 line `…|719,154|B3` lies 0.47 m from
  label 5741C and 1.26 m from 5741E, so a "unique" 1 m match would turn a confirmation of two dampers into a
  confirmation of one). They are listed under `orphaned_decisions[]` with their original id, anchor and reason for
  engineer re-confirmation against the new observations.
- Carry-forward on a new revision (same stem, new sha): matched decisions are shown `needs_reconfirm=true` and are
  **not applied** until re-confirmed; same-sha matches apply directly.
