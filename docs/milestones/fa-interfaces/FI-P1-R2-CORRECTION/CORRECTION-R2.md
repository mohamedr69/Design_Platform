# FI-P1 r2: correction (resolves every open R1 finding)

| | |
|---|---|
| Version | FI-P1 r2 (2026-10-04). Corrects FI-P1 r1 (`../FI-P1-R1-CORRECTION/`, verdict CHANGES REQUIRED). FI-P1 and r1 are unchanged. |
| Precedence | r2 governs over r1 and FI-P1 wherever they disagree (CHANGE-MAP at the end). |
| Already implemented on branch `fi-p1/implementation` (not part of this review) | Stage 0.2 provider honesty (`24d308c`); Stage 0.3 bounded rendering (`a5616a3`) |
| Evidence | CASES.md (the three reported cases, reproduced read-only) |

Labels:
- **C**: confirmed in code or data.
- **A**: assumption.
- **EXAMPLE**: a value that needs owner approval.

Contract clauses are numbered (`S0.1-…`, `W-…`). Every clause has at least one test id (`T-…`).

---

## Part A: Stage 0.1, evidence currency and publication (for review now)

Stage 0.1 changes the **existing** scan (`fa_interfaces_scan`) and its page. It is the first code task, and it must fix findings 1, 2, 6 and 7 without making today's behaviour worse.

### S0.1-1 Per-source record (compat JSON in `project_fa_interfaces.sources`)

```
SourceEntry {
  discipline, kind: folder|fa_ifc|schedule, relative_path, filename, size, mtime, sha256|null,
  status: enum[read, stale, failed, unread, removed, superseded, duplicate, unsupported],
  stale_reason: enum[read_failed, not_synced, folder_missing, ifc_root_missing] | null,   // only when status = stale
  last_known: { result, visual|null, sha256, read_at, scan_version } | null,              // the last good reading, kept for audit/display
  duplicate_of: relative_path | null,        // only when status = duplicate
  error: string|null, removed_at|null, seen_at
}
```

- **Counted:** `build()` counts `status == "read"` only (service.py:434, C). Every other status, including `stale` with a `last_known`, is never counted. That is the whole currency rule in one place.
- **`unsupported`:** files in a discipline folder that the pipeline cannot read (PDF, images, Office files other than the schedule workbooks). They are listed for coverage only (finding 6: `unsupported` is coverage, not currency).

### S0.1-2 Folder states, decided per scan before any reading

| State | Condition (stat only) |
|---|---|
| `root_unreachable` | The project folder is not a reachable directory (`received()`'s test) |
| `ifc_root_missing` | Root reachable, but `03- Drawings/IFC` is absent or contains no entries. This is an **unsynced OneDrive** project. |
| per discipline `present` | The discipline folder exists and lists at least one entry |
| per discipline `absent_or_empty` | Otherwise |

A file is **not synced** when `os.stat(...).st_file_attributes` has `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` (0x400000) or `FILE_ATTRIBUTE_OFFLINE` (0x1000). That is a OneDrive cloud-only placeholder (C: documented Windows attributes; A: OneDrive sets them on this PC). A not-synced file is listed `present` but is **not hashed or read**, because hashing would force a download.

### S0.1-3 State transitions: total over (previous status × event)

Events are evaluated per previous entry (by `(discipline, relative_path)`) and per newly listed file.

| Previous ↓ / Event → | E1 present, read OK | E2 present, read fails | E3 present, not synced | E4 file gone, its folder present | E5 its discipline folder absent/empty | E6 IFC root missing (unsynced) | E7 newer revision of same stem present | E8 same content as an earlier path this scan |
|---|---|---|---|---|---|---|---|---|
| (new file) | `read` | `failed` | `unread` (reason not_synced) | n/a | n/a | n/a | `superseded` | `duplicate` |
| `read` | `read` (carry or reread) | **`stale(read_failed)`**, last_known = old | **`stale(not_synced)`**, last_known = old | `removed`, last_known kept | **`stale(folder_missing)`** | **`stale(ifc_root_missing)`** | `superseded` | `duplicate` |
| `stale(*)` | `read` | `stale(read_failed)` (last_known unchanged) | `stale(not_synced)` | `removed` | `stale(folder_missing)` | `stale(ifc_root_missing)` | `superseded` | `duplicate` |
| `failed` / `unread` | `read` | `failed` | `unread` | `removed` | `stale(folder_missing)`, last_known null | `stale(ifc_root_missing)`, last_known null | `superseded` | `duplicate` |
| `removed` | `read` (file returned) | `failed` | `unread` | stays `removed` | stays `removed` | stays `removed` | `superseded` | `duplicate` |
| `superseded` | `read` (the newer revision is gone, so this is latest again) | `failed` or `stale(read_failed)` if it has a last_known | `unread` | `removed` | `stale(folder_missing)` | `stale(ifc_root_missing)` | stays `superseded` | `duplicate` |
| `duplicate` | `read` (its original is gone or unreadable) | as the `read` row | as the `read` row | `removed` | `stale(folder_missing)` | `stale(ifc_root_missing)` | `superseded` | stays `duplicate` |

Further rules:
- **E0 project root unreachable:** no transition at all. The job fails before anything is written (S0.1-6).
- **Engineer confirmation:** `stale(folder_missing|ifc_root_missing)` becomes `removed` only by an engineer action, `POST /projects/{id}/fa-interfaces/sources/confirm-removed {relative_paths[]}` (creator roles). This is how a deliberately emptied folder is retired (finding 6).
- **Duplicates (E8):** the first path in a fixed order, discipline order `ARCH, FF, SM, HVAC, ACS, GB` then `relative_path`, is read. Later paths with the same sha256 are `duplicate` and are not read again (finding 5, Stage-0 form). If the canonical path disappears, the next one is read in the next scan.
- **Unsupported:** a listed PDF or other unsupported file is `unsupported` on every scan where it is present, and `removed` when gone.

### S0.1-4 "Received": one definition, ordered badges (finding 7)

**Received** (per package) means: at least one file of the package is present in **this** scan's listing. Saved or stale data never makes a package Received.

Badge, first match wins:

| # | Condition | Badge |
|---|---|---|
| 1 | Root unreachable | `Unreachable` (status unknown) |
| 2 | IFC root missing | `Not synced` (status unknown; last known kept) |
| 3 | No present file and the package has stale entries | `Missing, last known kept` |
| 4 | No present file | `Missing` |
| 5 | A present supported file is `failed`, `unread`, or `stale(read_failed\|not_synced)` | `Received, not read` (with count) |
| 6 | Present files are only `unsupported` | `Received, not readable (PDF)` |
| 7 | Otherwise (every present supported file `read`; superseded, duplicate and unsupported files listed but neutral) | `Received` |

Coverage payload per package: `badge`, `received: bool` (true only for badges 5–7), `files[]` with `status`, `stale_reason`, `duplicate_of`, `last_known_at`.

### S0.1-5 The published snapshot and the primary view (findings 1, 2; owner rule "never an empty current schedule")

**Migration.** Add to `project_fa_interfaces`:
- `published` JSON null
- `published_at` DateTime null
- `published_basis` String(24) null (`complete_scan|seeded`)
- `generation` Integer, not null, default 0

**Snapshot.**
- Contents: the deterministic `build()` output that the UI and exports consume (`rows, verification, settled, rejected, floor_summary, type_summary, totals, conflicts, excluded_found`), plus `sources_digest` and `job_id`.
- It is written in the same transaction as `sources`. `generation` is incremented with a compare-and-set: `UPDATE … WHERE generation = :read_generation`. A concurrent writer loses and its job fails with "changed meanwhile".

**Advance rule** (legacy job, interim until Stage 6). After a scan commits its `sources`, the snapshot advances to the new `build()` only if all hold:
- (a) the root and IFC root were reachable;
- (b) no supported present entry is `failed`, `unread` or `stale`;
- (c) every package that had rows in the current snapshot still has ≥ 1 `read` source;
- (d) the new view has at least one row, or the current snapshot has none.

Otherwise the snapshot is unchanged.

**Seeding.**
- On the first `build()` after the migration, if `published` is null and `sources` has ≥ 1 `read` entry, the current `build()` is stored with basis `seeded`.
- C: project 5's saved reading is already degraded to 1 source, so its seed reflects that. The UI states `basis: seeded`.

**View fields** returned by `GET /fa-interfaces` (and used by the exports):

```
view_state: current | provisional | unverified
primary:    current | published
current:    { rows, totals, ... } | null      // from `read` entries; null when the root is unreachable
published:  { ...snapshot, at, basis } | null
last_known: [ { package, relative_path, stale_reason, last_known_at, counts_by_key{key:int} } ]
evidence:   { root: reachable|unreachable|ifc_missing, read, stale, failed, unread, removed, duplicate, unsupported }
```

| Situation | `view_state` | `primary` | KPI cards and schedule table show |
|---|---|---|---|
| Root unreachable | `unverified` | `published` (if any) | Published totals and rows, titled "Last published <date>, **not verified now**: project folder unreachable". `current` is null. No zero cards. |
| IFC root missing (unsynced OneDrive) | `provisional` | `published` | The same, titled "…not verified now: drawings folder not synced". The current partial view is a secondary "Verified now" panel. |
| Any package that has rows in the published snapshot now has only stale/missing evidence, **or** the current view has zero rows while the published snapshot has rows | `provisional` | `published` | Published, titled "not verified now"; "Verified now (partial)" panel with the current totals |
| Root reachable, everything current, and current equals the snapshot (or the snapshot just advanced) | `current` | `current` | Current |
| Root reachable, some sources stale/failed/unread but no package lost (e.g. one of two SM files failed) | `provisional` | `current` | Current totals titled "**provisional**: n source(s) not verified now"; stale section |

- If `primary = published` and no snapshot exists (a project never scanned completely), the table is empty and titled "Not yet read completely", with every count shown as "—", never 0.
- The top-level `rows/totals/...` keys (which today's UI and exports read) carry the **primary** view, with `primary` and `view_state` beside them. Existing consumers therefore never show a stale-free "empty current" schedule. The redesign (`redesign/service.py`) and the draftsman checks read `build()["rows"]`: they get the primary view and its `view_state`, unchanged in shape.

### S0.1-6 Scan behaviour

1. Folder states (S0.1-2).
   - `root_unreachable` raises `SourceUnreachable`: the job **fails** ("project folder unreachable") and nothing is written.
   - `ifc_root_missing` does **not** fail. It transitions entries by E6, keeps the snapshot and completes. The page says "drawings folder not synced".
2. Listing, duplicate detection and hashing as S0.1-3. Not-synced files are not hashed.
3. Reading as today for `unread`, changed or failed files. Unchanged `read` entries carry forward (same sha and `SCAN_VERSION`).
4. Visual look as today (Stage 0.3) for `read` SM/HVAC entries.
5. **One commit** of `sources` plus the snapshot decision, under the `generation` compare-and-set.
   - **Cancel or interrupt** before the commit leaves the row untouched (as today, jobs.py:224-234).
6. `decisions` and `manual` are never modified by a scan (C today; asserted by a test).
7. Decisions attached to stale or removed sources are kept. `build()` lists, per package, how many decisions are "kept, not applied: source not current".

### S0.1-7 Exports

- xlsx and pdf export the **primary** view.
- The header states `view_state`, `primary` and basis/date. "Last published, not verified now" appears verbatim when `primary = published`.
- Stale entries go in a separate sheet/section, "Last known, not current", with their own counts. They are never mixed into the schedule sheet.

### S0.1 tests

| Id | Given | When | Then |
|---|---|---|---|
| T-01 | FF read (10 lines); snapshot complete | FF reread fails (converter error) | FF `stale(read_failed)`, last_known kept; `current` totals exclude FF; FF badge `Received, not read`; `view_state=provisional`; FF had rows in the snapshot, so `primary=published`; stale section lists FF with its counts; decisions untouched |
| T-02 | SM read | SM folder renamed (root reachable) | SM `stale(folder_missing)`; badge `Missing, last known kept`; `received=false`; primary published; no job failure |
| T-03 | All read | Project root unreachable | Job fails; `sources`, snapshot and `generation` unchanged; `GET` gives `view_state=unverified`, `current=null`, primary published, every badge `Unreachable`, `received=false` everywhere; KPI totals = published, labelled |
| T-04 | All read | `03- Drawings/IFC` missing (unsynced OneDrive) | Job completes; every entry `stale(ifc_root_missing)`; badges `Not synced`; primary published with "not verified now"; **never an empty primary schedule** |
| T-05 | T-01 state | Reread succeeds, same sha | FF `read`; totals include it; stale section empty; snapshot advances (complete) |
| T-06 | T-01 state | File changed, new sha, read OK | FF `read` (new); old reading replaced; snapshot advances |
| T-07 | Same bytes at `SM/X.dwg` and `HVAC/X.dwg` | Scan | One read (the SM path, by order); HVAC entry `duplicate` (duplicate_of SM path); damper count = the single-file count; SM and HVAC both `Received` |
| T-08 | T-07 state | `SM/X.dwg` deleted | `HVAC/X.dwg` is read; SM entry `removed`; totals unchanged; SM badge `Missing` if it has no other file |
| T-09 | R1 read | R1 deleted, R2 filed | R2 `read`, R1 `removed`; counted once |
| T-10 | Folder holds R1 and R2 | Scan | R1 `superseded`, not counted |
| T-11 | T-10 state | R2 deleted | R1 `read` again |
| T-12 | SM folder has a DWG and a PDF | Scan | PDF `unsupported`, listed; SM badge `Received` |
| T-13 | Package with only PDFs | Scan | Badge `Received, not readable (PDF)`; `received=true`; no rows |
| T-14 | `stale(folder_missing)` entry | Engineer confirms removal | Entry `removed`; badge `Missing` |
| T-15 | Existing row with read sources, no snapshot (migration) | First `GET` | Snapshot seeded (basis `seeded`); `view_state=current` |
| T-16 | Not-synced placeholder (attribute flag) for a previously read file | Scan | `stale(not_synced)`; the file is not opened (asserted); badge `Received, not read` |
| T-17 | Scan cancelled after reading one file | — | Row and snapshot untouched |
| T-18 | Two scans racing on one row | Both commit | The second fails "changed meanwhile"; `generation` advanced once |
| T-19 | A project never completely scanned | Root unreachable | Primary empty, titled "Not yet read completely"; totals "—" (null in the payload), not 0 |
| T-20 | Any state | Export xlsx/pdf | Header carries `view_state`/`primary`; stale entries only in the separate sheet |
| T-21 | Existing tests (`test_fa_interfaces`, redesign, draftsman) | — | Pass; the shape of `rows`/`totals` is unchanged |

---

## Part B: resolutions for the other open R1 findings (contracts for Stages 1–6)

These govern the drawing workflow (Part C). The finding numbers refer to REVIEW-R1.

| R1 # | Resolution (clause) | Tests |
|---|---|---|
| **4** | **W-PUB.** `unsupported` means unsupported **kinds** (PDF until a reader exists): listed, never blocking publication, never counted, shown as "not read". `reference_state` (schedules: read/failed) is part of the coverage ledger; a failed reference blocks `complete`. The rules are scoped per job kind: the legacy scan uses S0.1-5's interim advance rule; `fa_interfaces_run` uses W-PUB-2 (Fable review completed, every agent terminal with coverage complete or `unsupported` kind, no unresolved critical conflict, **engineer acceptance** through `POST …/runs/{run}/accept`, delivered with the run). The Stage 1 migration seeds the pointer from S0.1's snapshot. Exports carry the primary view as in S0.1-7. | T-W1…T-W4 |
| **5** | **W-DUP.** Currency is per **source** (one sha), never per package. `packages[]` lists every package with a present path. Keys searched = the union of the rule sets of the packages present now. When a package's copy disappears, its exclusive keys stop being searched, and those observations become `needs_revalidation` (not counted). `decision_key` uses the key's **home discipline** from the matrix (`Rule.disciplines[0]`), not the folder, so deleting one copy never orphans decisions. | T-W5, T-W6 |
| **8** | **W-PR.** A deterministic `PackageReport` is **always** produced per package (ledger rows, per-source coverage, accepted/held/stale counts, conflicts, unsupported files). FP1 annotates it. Without Fable, the PackageReport is the accountable per-package record, marked `orchestrator_review: missing(<reason>)`. The digest schema is `RunDigest { run_id, package_reports[], cross_conflicts[], totals, review_state }`. | T-W7 |
| **9** | **W-FP.** FP1(P) fires when (i) every agent of P is terminal, (ii) validation of P's observations is terminal (no `proposed` left), and (iii) the reference snapshot is `ready`. Packages with no agents (no supported source) get their PackageReport only, no FP1. FP2 waits for every FP1 that was due. After rework (FP3 path), FP1 is re-run for the reworked packages before FP2. | T-W8, T-W9 |
| **10** | **W-BUD.** An `FA_ORCHESTRATOR_*` block, all values EXAMPLE: max input tokens per call 150,000; max calls per run `packages + 3`; timeout 900 s; Retry action ≤ 3 per run per day. It is a **reserved** allowance subtracted from the run budget before agents are dispatched, so agents cannot starve it. Inputs carry structured rows for held/conflict/disputed observations and per-key counts for the rest. Over the cap, the input is split by source into ordered chunks; their assessments are merged deterministically, and disagreement between chunks becomes a `dispute`. Fable calls take a ModelGate lease with priority. This supersedes FI-P1 PERF §3's adjudication line. | T-W10, T-W11 |
| **11** | **W-SEC.** Every free-text field going into any model call (labels, titles, reasons, claims) is bounded (labels 160 characters, reasons 300) and fenced per field. CLI calls with images run `--allowedTools "Read(./**)"` scoped to the temp folder (A: path rule syntax, to be verified offline against the CLI's argument validation and once live under owner approval). Model outputs (`summary`, `open_questions`, `reason`) are scanned with `guard.instruction_flags` and a secret pattern check before storage or export. A hit replaces the text with "[withheld: flagged]" and records the flag. | T-W12, T-W13 |
| **12** | **W-FST.** One Fable state set: `not_started, running, completed, failed(transport\|timeout\|refused\|invalid_output), unavailable(reason), substituted`. `substituted` gets one retry, then the review is `missing`. The **wrapper** computes and attaches `input_digest`; the model does not echo it. `--fallback-model` is never passed (asserted in Stage 0.2 tests, done). | T-F1…T-F8 (r1), T-W14 |
| **13** | **W-MET.** All metrics are computed on **exhaustively annotated layouts only**. A excludes engineer-derived validations (`decided_by=engineer`); those are reported separately. O/H/A/R/S/P partition every observation (P = proposed, R = rejected, S = needs_revalidation). FI-P1's finding state `stale` is renamed `needs_revalidation`, so `stale` means evidence currency only. Critical keys: dampers, fans, pumps (valves if the owner adds them). **Typical floors:** a prediction from a typical sheet expands into one prediction per floor key, and each is matched to GT per floor. | T-M1…T-M5 (r1), T-W15 |
| **14** | **W-BASE.** Baseline = `fa_interfaces_scan` at commit `a5616a3` (Stage 0.2 + 0.3 only, no counting change) with a recorded settings snapshot (models as configured, `drawing_review_effort=high`). **Instance expansion:** a line with qty n gives n predictions sharing its anchor. Verification groups give H with their proposed qty. A **location-free** variant (match on key and floor only) is computed for both pipelines. Location metrics are computed only where the pipeline provides symbol-based anchors. | T-W16 |
| **15** | **W-TIME.** `t_total` runs from job claim to run terminal (automated publication decision only; no human time). A speed claim requires identical coverage outcomes (the same sources complete, partial and unsupported) **and** G-BOTH at the same configuration. | T-G1…T-G3 (r1), T-W17 |
| **17** | Superseded FI-P1 text: PLAN §4 Publish row and HANDOFF #9; PLAN §9 and §13 #6; CONTRACTS §10 `FableAdjudication` and the §13 `step` enum (now `package_review`, `run_review`); IMPL Stage 6 rollback; OBSIDIAN readings fields (now `status/stale_reason/last_known/packages[]`). Listed in the CHANGE-MAP. | — |
| **18** | **W-N.** G-ACC needs \|A\| ≥ 150 pooled on exhaustive layouts, with ≥ 30 per critical-key stratum (EXAMPLE). Wilson intervals are reported per stratum; the gate applies to the pooled value plus every critical stratum's point estimate. | T-W18 |

---

## Part C: the drawing workflow and the three reported cases (Stages 1–6)

### W-1 Manifest and discovery (fixes case 1b)

- Every file under a discipline folder is listed: supported (DWG/DXF), `unsupported` (PDF and others) or `schedule`.
- One source per sha. The manifest is frozen per run.
- PDFs appear in the coverage ledger as `unsupported: pdf_not_supported`, under their package.

### W-2 Drawing agents (Opus) and package reports

- **One logical agent per supported source.** Its steps are deterministic extraction (texts with handle paths, symbol candidates, leaders, loops) followed by bounded, schema-constrained Opus calls (`exact_model`, `effort=high`) for label→symbol association on each window.
- **Per-agent concurrency** is bounded by `FA_AGENT_PARALLEL` (EXAMPLE 2). Model calls go through the provider's per-process semaphore.
- **Outputs.**
  - One `DrawingAgentReport` per source.
  - One `PackageReport` per package (W-PR).
  - Observations are persisted per source in `fa_interface_observations`, with one writer per source.

### W-3 Location model (fixes case 2)

Every observation stores the following separately:
- `label_anchor` (text point, handle path);
- `symbol_candidate_id` (`sha24:handle-path`);
- `equipment_anchor` / `equipment_bounds` (from the symbol);
- `association {method, distance, runner_up, ambiguous}`.

Rules:
- The schedule's location is `equipment_anchor`, never the text point.
- A model point counts only when snapped inside a candidate's bounds (tolerance per type, EXAMPLE 0.15 m for dampers).
- Ambiguity (best/runner-up ratio < 1.5, EXAMPLE), or two labels claiming one symbol without compatible text, holds **all** members.

### W-4 Cross-drawing reconciliation (fixes case 1a)

- The per-floor "winner" and "shadow" rules (service.py:686-712) are retired for the workflow.
- **Alignment per floor pair:**
  - ≥ 3 coinciding labels of the same key and text within 0.5 m (EXAMPLE), with a residual ≤ 0.2 m, give `verified`.
  - Identical viewports alone give only a `candidate`.
- **Aligned floors:** the union of the observations, deduplicated by equipment anchor within the type tolerance.
- **Unaligned floors:** compare counts. Equal counts are counted once, with both drawings as evidence. Unequal counts form a ConflictSet that holds every member and is shown to Fable and the engineer.

### W-5 Gate barriers by evidence (fixes case 3)

**Candidate instances.** A gate barrier instance is a **fire-alarm connection point** on a plan sheet of a GB, ACS or ARCH drawing:
- a text matching `FIRE ALARM (CABLE|INTERFACE|CONNECTION)|DRY CONTACT`;
- it is not inside a detail, schematic or legend sheet, and not outside every sheet;
- its leaders, if any, are recorded.

**Merging.** Identical connection texts within 1.0 m (EXAMPLE) are one point (a repeated label). This guards against double counting.

**Roles.** Role labels (`\bENTRY\b|\bENT\.?\b|ENTRANCE` gives `entry`; `\bEXIT\b` gives `exit`) are assigned one-to-one to connection points by minimum total distance within 6 m (EXAMPLE).

**Settlement by rule.** A point with a unique role label (its runner-up role is the other role and at least 1.5× farther), and no other point claiming that role, is settled by rule (`settled_by_rule="gate_role_unique"`). Otherwise all affected points are **held**, and the Opus agent is asked about them (W-2).

**Lane evidence.** Loops on a `LOOP` layer within 3 m add evidence; they do not create instances.

**Interfaces.** Each accepted instance is one gate barrier with matrix rule 30 (CR). Two connection points give two CRs, one gives one, three give three. Nothing is hard-coded.

**Across drawings.** The identity is (floor, `gate_barrier`, role). The shop drawing's two connection points on its own ground floor, in an unaligned frame, match by role if roles are present. Otherwise the counts are compared (W-4).

**Never instances.** Blocks named `ENTRY*`/`EXIT*` outside every sheet viewport, and notes containing "NETWORK", "DATA POINT" or "CAT6", never create instances.

### W-6 Fable orchestration (mandatory) and publication

- r1 §1 as corrected by W-FP, W-BUD, W-FST and W-SEC.
- The run's schedule is `provisional` unless W-PUB-2 holds.
- A missing review keeps it `provisional`, shows the banner, and offers Retry.
- Deterministic code computes every count, from `A` only (validated + current + included).

### W-7 Decisions and history

- Engineer decisions are never deleted or overwritten by a run.
- Readings are kept per source in history: `fa_interface_readings` is append-only, and `last_known` points at the latest good one.
- A decision whose key no longer matches is listed as `kept, not applied` with its reason. It is not orphaned silently.

### Stage plan (implementation order after Stage 0.1 clears review)

| Stage | Scope | Depends |
|---|---|---|
| 1 | Manifest per run (all files, PDFs unsupported), one source per sha, readings history, `fa_interface_runs` + `fa_interface_observations` tables | 0.1 |
| 2 | Deterministic extraction v2: handle paths, symbol candidates (INSERT/loose), leaders, loops; location model W-3 | 1 |
| 3 | Drawing agents (Opus, fake provider in tests) with DrawingAgentReport, PackageReport; bounded concurrency | 2, 0.2 |
| 4 | Reconciliation W-4 (alignment check, union, conflicts); gate barriers W-5 | 2 |
| 5 | Fable FP1/FP2 (mandatory), review states, Retry, deterministic validation of output (V-F*) | 3, 4 |
| 6 | Publication W-PUB-2, accept endpoint, UI panels (agents, packages, stale, review state) | 5 |

---

## CHANGE-MAP r1 → r2

| # | r1 location | r2 |
|---|---|---|
| X1 | CONTRACTS-R1 §2.2 table | Replaced by the total table S0.1-3 (adds not_synced, ifc_root_missing, superseded→read, removed→read, duplicate transitions, engineer confirm-removed) |
| X2 | CONTRACTS-R1 §2.3 R-C4 | Replaced by S0.1-4 (ordered badges, one Received definition) |
| X3 | CONTRACTS-R1 §2.5–§2.6 | Replaced by S0.1-5 (snapshot, primary view, never an empty current schedule) and W-PUB |
| X4 | CONTRACTS-R1 §2.4 | Replaced by S0.1-3 E8 (Stage 0) and W-DUP |
| X5 | CONTRACTS-R1 §1.6–§1.7 | Refined by W-PR, W-FP, W-BUD, W-FST, W-SEC |
| X6 | CONTRACTS-R1 §3 | Refined by W-MET, W-N |
| X7 | CONTRACTS-R1 §4 | Refined by W-BASE, W-TIME |
| X8 | FI-P1 items in finding 17 | Superseded as listed in Part B #17 |
