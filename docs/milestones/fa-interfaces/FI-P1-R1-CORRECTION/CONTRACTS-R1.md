# FI-P1 r1: testable contracts

These contracts **supersede** the matching parts of `../FI-P1-DRAWING-AGENTS-PLAN/CONTRACTS.md` as listed in CHANGE-MAP.md. Everything not listed stays in force.

Labels:
- **C**: confirmed in this session.
- **A**: assumption.
- **EXAMPLE**: illustrative value that needs owner approval.

Test ids (`T-…`) are acceptance tests the implementation must ship with. Each one is written as given / when / then.

---

## 1. Orchestrator review (Fable): receive, return, unavailable

### 1.1 Roles

| Actor | Owns | Never does |
|---|---|---|
| Deterministic application code | Manifest freeze, dispatch, leases, budgets, locks, state transitions, evidence validation, arithmetic (matrix modules, counts), the coverage ledger, publication | Interpret drawings; adjudicate meaning |
| Opus drawing agent (`claude-opus-5-5`, effort `high`) | One source file: observations, evidence, page outcomes, `DrawingAgentReport` | Write business rows; touch another agent's results |
| **Fable orchestrator** (`claude-fable-5-1`, effort `high`) | Receives every drawing report (per package), checks coverage and conflicts against evidence, requests bounded rework, produces the **ConsolidatedReviewProposal** | Change counts, matrix rules, states or publication; mark coverage complete; accept a finding by itself |

Fable is an **active, mandatory stage** of every run. It is not an optional adjudicator, and it supersedes FI-P1 PLAN §3 and decision #11 ("adjudication only, default off").

### 1.2 Invocation points

There are at most `packages + 2` Fable calls per run, plus at most one retry per call (EXAMPLE).

| Point | Trigger (deterministic) | Input | Output |
|---|---|---|---|
| **FP1 package review** | Every source of package P has reached a terminal `execution_state`. Reports queue in P's inbox as they arrive. | `PackageReviewInput(P)` | `PackageReviewProposal` |
| **FP2 run consolidation** | Every package has an FP1 result (completed, failed or unavailable), **and** deterministic cross-drawing reconciliation has been computed | `RunReviewInput` | `ConsolidatedReviewProposal` |
| **FP3 rework re-consolidation** | FP2 requested rework, the request was approved by the budget check, and the reworked agents reached terminal states. Only one rework round per run (EXAMPLE). | `RunReviewInput` (new digest) | `ConsolidatedReviewProposal` |

### 1.3 What Fable receives (`PackageReviewInput` / `RunReviewInput`)

```
ReviewInputCommon {
  run_id, input_digest: sha256 /* of the canonical JSON below; idempotency key */,
  model_requested: "claude-fable-5-1", effort: "high",
  matrix_version, reference_snapshot_version, task_version, schema_version,
  coverage_ledger: [ { source_id /* sha24 */, paths[], packages[], execution_state, coverage_state,
                       evidence_currency /* §2 */, expected_layouts:int|null, attempted_layouts:int,
                       unread_regions:int, unsupported_reason|null } ]      // computed deterministically
  stale_evidence: [ { source_id|path, package, stale_reason, last_known_at, last_known_counts{key:int} } ],
  budget: { model_calls_used, model_calls_cap, elapsed_s, rework_rounds_left:int }
}
PackageReviewInput  = ReviewInputCommon + {
  package: enum[ARCH, FF, SM, HVAC, ACS, GB, SCHED],
  reports: [ DrawingAgentReport /* FI-P1 CONTRACTS §8, structured fields only */ ],
  observations: [ { observation_id, source_id, layout, key, tag|null, floor_keys[], region_role,
                    finding_state, settled_by_rule|null, evidence_refs[] } ],   // compact rows, no raw drawing text
  conflicts: [ ConflictSet /* intra-package */ ],
  crops: [ { crop_id, conflict_id, png /* <= K per call, K = 8 EXAMPLE */ } ]
}
RunReviewInput = ReviewInputCommon + {
  package_reviews: [ PackageReviewProposal | {package, state:"unavailable"|"failed", reason} ],
  cross_conflicts: [ ConflictSet /* cross-drawing, FI-P1 PLAN §9 */ ],
  current_totals: { by_key_floor: [...], modules: {...} }   // deterministic; for context only
  previous_published: { run_id|null, digest|null, totals|null }
}
```

Untrusted content:
- Any drawing-derived text (labels, titles) appears only inside observation rows. It is truncated to 40 characters and fenced as data by `guard.fence` (C: provider.py `_prompt`).
- The system prompt tells Fable that this content is data, never instructions.
- Raw drawing text dumps, prompts of other agents and credentials are never included.

### 1.4 What Fable returns (schema-constrained)

```
PackageReviewProposal | ConsolidatedReviewProposal {
  run_id, input_digest /* must echo the input */, scope: "package:<P>" | "run",
  coverage_assessment: [ { source_id, verdict: enum[agree, dispute], reason, evidence_refs[] } ],
  conflict_proposals: [ { conflict_id, proposal: enum[select_candidate, keep_held, split, merge, rework],
                          candidate_ids[], reason, evidence_refs[] } ],
  rework_requests: [ { source_id, layouts[], reason } ],          // bounded, see V-F6
  missing_or_suspect: [ { package, issue: enum[source_missing, stale_only, coverage_gap, count_mismatch, other],
                          detail } ],
  publication_recommendation: enum[do_not_publish, provisional, complete_candidate],
  summary: string /* <= 3000 chars, plain text */,
  open_questions: [ string ]
}
```

### 1.5 Deterministic validation of Fable's output (V-F)

| Id | Rule | On failure |
|---|---|---|
| V-F1 | Schema-valid; `input_digest` equals the input | `invalid_output`; one retry, then terminal |
| V-F2 | Every `source_id`, `conflict_id`, `candidate_id` and `evidence_ref` exists in the input | That item is dropped and logged as `unsupported_reference`; the rest is kept |
| V-F3 | `model_used` from the response equals `claude-fable-5-1`. Auxiliary Haiku entries are allowed; any other model with output tokens counts as a substitution. (C: one CLI 2.1.288 probe today listed `claude-opus-4-8` beside Fable, not reproduced.) | `review_state = substituted`; the proposal is stored but **not used** |
| V-F4 | Coverage `dispute` is recorded. `agree` cannot raise `coverage_state`; only page outcomes can. | n/a |
| V-F5 | Numbers in `summary` are never used. Totals are always recomputed deterministically. | n/a |
| V-F6 | Rework requests are accepted only if `rework_rounds_left > 0`, the budget allows them (FI-P1 PERF §3 allowance) and the source is in the manifest | Rejected with a reason; FP3 does not run |
| V-F7 | `conflict_proposals` become `proposed_resolution` on the ConflictSet. `finding_state` stays `held` until an engineer accepts or a deterministic rule settles it. | n/a |
| V-F8 | `publication_recommendation` is advisory. The deterministic gate in §1.7 decides and may only lower it, never raise it. | n/a |

### 1.6 Fable review state machine (per call and per run)

```
not_started → pending → running → completed
                              ↘ failed(reason: transport|timeout|refused|invalid_output)  — 1 retry → terminal
                              ↘ unavailable(reason: provider_not_ready|model_rejected|cli_too_old|budget_exhausted)
                              ↘ substituted(model_used)
run.review_state = completed  iff FP2 (or FP3) completed and every FP1 is completed
                 = partial    if FP2 completed but at least one FP1 is not completed
                 = missing    otherwise (reason list kept)
```

Readiness check before the run (C: Fable 5.1 answers on CLI 2.1.263 and 2.1.288 today; the configured CLI path is missing):
- If Fable is not ready, the run still dispatches drawing agents.
- `review_state = missing(reason=…)` is set **at run start**, and the banner shows from the start.
- No model other than Fable stands in for it, and Opus is never promoted to orchestrator.

### 1.7 When Fable is unavailable or fails: explicit, never silent

1. **Deterministic stages still run:** drawing agents, validation, reconciliation and the coverage ledger.
2. **A `DeterministicReviewDigest` replaces the proposal.** It carries the same `coverage_ledger`, `stale_evidence`, conflict list and totals, and is labelled `orchestrator_review: missing (<reason>)`. It never calls itself a review.
3. **Publication is capped at `provisional`.** The published pointer does not advance (§2.6).
4. **UI.** The run header shows a red badge "Orchestrator review missing: <reason>" and a **Retry orchestrator review** action.
   - The action re-runs FP1/FP2 only, on the frozen inputs.
   - It is idempotent by `input_digest` and does no drawing rework.
5. **Records.** Obsidian and the run report record the state, the reason and the attempt history.
6. **Run status.** The run can be `completed` (execution) but never `complete_reviewed`.

### 1.8 Tests

| Id | Given | When | Then |
|---|---|---|---|
| T-F1 | 2 packages, 3 sources, recording provider returning valid proposals | Run | Exactly 2 FP1 calls and 1 FP2 call; every source appears in `coverage_assessment` input; `review_state=completed` |
| T-F2 | Provider not ready for Fable (fake CLI version 2.1.263 with Fable OK; or path missing) | Run | Agents still run; `review_state=missing(provider_not_ready)` from start; publication `provisional`; banner present in API payload |
| T-F3 | Fable returns `model_used=claude-opus-4-8` with output tokens | FP2 | `review_state=substituted`; proposal stored, not applied; publication `provisional` |
| T-F4 | Fable proposal references an unknown `conflict_id` | FP2 | Item dropped (`unsupported_reference`), others kept |
| T-F5 | Fable says `complete_candidate`, but one source has `coverage=partial` | Gate | Publication `provisional` (V-F8) |
| T-F6 | Fable requests rework with `rework_rounds_left=0` | FP2 | Rejected with reason; no FP3 |
| T-F7 | FP2 times out twice | Run | `review_state=missing(timeout)`; Retry action re-invokes with the same `input_digest`; no drawing agent re-dispatched |
| T-F8 | Observation label text contains "ignore previous instructions" | Build input | Text fenced and truncated; system prompt marks data; test asserts the fence |

---

## 2. Evidence currency: stale is preserved, separate and never counted

This section supersedes FI-P1 CONTRACTS §11 rules 2 and 5b, FI-P1 IMPLEMENTATION-SEQUENCE §1 rules (2) and (5b), and REVIEW R-30's "counted" clause.

### 2.1 Definitions

| Term | Meaning |
|---|---|
| **Present** | The file is in the **current** folder listing. The project root and the file's discipline folder were reachable in this run. |
| **Received** (per file / per package) | At least one file of the package is present now. It is decided **only** from the current listing; saved or stale data never makes anything Received. |
| **Current evidence** | A reading whose content hash equals the hash of a file present now, read by the current scan or task version. It includes an unchanged carry-forward: same sha, still present, same `SCAN_VERSION`/task versions. |
| **Stale evidence** | The last known reading of a source that is not currently verified: its file failed to reread, is absent with its folder missing, or its folder or root was unreachable. It is kept for audit and display only. |

### 2.2 Evidence state per source (`evidence_currency`)

`current | stale | removed | superseded | unread | unsupported`

| From | Event | To | Received? | Counted in current totals? |
|---|---|---|---|---|
| (none) | File appears in the listing | `unread` | yes | no |
| `unread` | Read succeeds | `current` | yes | yes |
| `unread` | Read fails | `unread` + `last_error` | yes, labelled "read failed" | no |
| `current` | Same sha, present, same versions (carry-forward) | `current` | yes | yes |
| `current` | Present, new sha, read succeeds | `current` (new reading); old reading moved to history; decisions re-matched by `decision_key`; changed ones become `needs_reconfirm` | yes | yes |
| `current` | Present, reread **fails** (conversion, scan or open error) | **`stale(read_failed)`** | yes, labelled "read failed, last known shown separately" | **no** |
| `current` | Discipline folder absent or empty, root reachable | **`stale(folder_missing)`** | **no** (Missing) | **no** |
| `current` | File gone from a present, non-empty discipline folder | `removed` | no | no |
| `current` | A newer revision of the same `_stem` is present | `superseded` | yes (as superseded) | no |
| any | Project root unreachable | **no transition**: the run aborts before publication; the display shows `unreachable`, never Received | `unknown` | as last published (§2.6) |
| `stale(*)` | Present again and read succeeds | `current` | yes | yes |
| `stale(folder_missing)` | Folder back, file not in it | `removed` | no | no |
| `stale(*)` | Present again but read fails | `stale(read_failed)` | yes, labelled "read failed" | no |
| any | Model for the required step unavailable | Coverage `unsupported(model_unavailable)`; currency unchanged | per listing | Only the deterministic part of the reading counts. Observations that need the model stay `held`. |

### 2.3 Counting and display rules

- **R-C1.** Current totals (schedule rows, interface lines, monitoring and control signals, FA modules) are computed from observations whose source is `current` **and** whose `finding_state = validated` (accepted usable facts, §3). Nothing else enters them.
- **R-C2.** Stale evidence is shown in a separate **"Last known, not current"** section, per package.
  - It shows its own totals, `last_known_at` and `stale_reason`.
  - It has a grey stale badge and is never mixed into the current table or the current KPI cards.
- **R-C3.** Engineer decisions attached to stale observations are kept. They appear in the stale section, are not applied to current totals, and come back automatically when the source is `current` again with a matching `decision_key`.
- **R-C4.** Package badge on the Drawings strip:
  - `Received`: at least one present file, and all of its present files are `current`.
  - `Received, not read`: at least one present file is `unread` or `stale(read_failed)`.
  - `Missing`: no present file.
  - `Missing, last known kept`: no present file and stale evidence exists.
  - `Unreachable`: the project root is not reachable now.
  - The old `failed` badge is retired.
- **R-C5.** The KPI cards and Excel/PDF exports carry `evidence: current` totals. An export that includes stale data must show it in a separately titled sheet or section.

### 2.4 Duplicate content hashes

- **R-D1.** One `source_id` (sha24) means one drawing agent and one set of observations. A drawing with the same content in several paths or packages is read once.
- **R-D2.** `paths[]` and `packages[]` list every location.
  - Each package's coverage shows the file as `Received (same content as <other path>)`.
  - Observations are attributed to the source once and are never counted twice.
- **R-D3.** Equipment keys searched = the union of `matrix.rules_for(discipline)` over `packages[]`. Each observation records the package rule that made it applicable.
- **R-D4.** If the duplicate copies sit at different revision positions (current in one package, superseded in another), the source is `current` in the package where it is the latest. The ledger lists it, and Fable receives it as a `missing_or_suspect` candidate.
- **R-D5.** If one copy disappears, the remaining paths keep the source present. Currency is decided by "any path present", and each path is listed with its own presence.

### 2.5 Compatibility with today's `project_fa_interfaces.sources` (Stage 0)

- A stale entry is written with `status: "stale"`, not `"read"`. `build()` reads `status == "read"` only (service.py:434, C), so a stale entry is excluded from current totals with no other change. The old reading is kept under `last_known: {...}`.
- `removed` and `superseded` as in FI-P1, and excluded the same way.
- **Received display defect (C).** `service.received()` returns the **saved** sources when the root is unreachable, and `coverage()` then reports `available` ("Received") from saved data. This is today's uncommitted change in `service.py`, `received()`, the `return saved` branch. It violates R-C4 and is fixed in Stage 0.1: an unreachable root gives `Unreachable`, and saved entries are listed as last known.

### 2.6 Publication rules

- **R-P1.** A run produces a **current schedule** from current, validated evidence only.
- **R-P2.** The run's schedule becomes the **published** schedule (the pointer advances) only if all of these hold:
  - every manifest source is terminal;
  - no source is `stale` or `unsupported`;
  - `review_state = completed`;
  - there are no unresolved critical conflicts;
  - an engineer accepts.
- **R-P3.** Otherwise the run's schedule is `provisional`.
  - The previously **published** schedule stays visible as "Last published (run N, date)". It is not replaced, and it is not merged with current evidence.
  - The UI shows both, clearly labelled, with the diff "−k lines from sources now stale/removed".
  - This replaces FI-P1's "keep stale counted" mechanism for SPEC §11 ("do not replace a useful previous result with an apparently empty schedule").
- **R-P4.** An unreachable root aborts the run before publication. Nothing changes, and the display says `Unreachable`.

### 2.7 Tests

| Id | Given | When | Then |
|---|---|---|---|
| T-S1 | Prior: FF file read (`current`, 10 lines) | Reread fails (converter error) | FF entry `stale(read_failed)`, `status:"stale"`; current totals exclude its 10 lines; stale section shows 10 with reason; FF badge `Received, not read`; publication `provisional`; last published still shown |
| T-S2 | Prior: SM read | SM folder renamed (root reachable) | SM `stale(folder_missing)`; badge `Missing, last known kept`; current totals exclude SM; no abort |
| T-S3 | Prior: everything read | Project root unreachable | Job fails before publication; sources unchanged; every badge `Unreachable`; nothing shown as `Received` (regression test for the `received()` defect) |
| T-S4 | T-S1 state | Reread succeeds (same sha) | FF `current`; totals include it; stale section empty; decisions re-applied by `decision_key` |
| T-S5 | T-S1 state | File changed (new sha), read succeeds | `current` with the new reading; changed decisions `needs_reconfirm`; old reading in history |
| T-S6 | Same bytes at `SM/X.dwg` and `HVAC/X.dwg` | Run | One agent and one observation set; SM and HVAC both `Received (same content…)`; damper count equals the single-file count; keys = union of SM and HVAC rules |
| T-S7 | T-S6 | `HVAC/X.dwg` deleted | Source still present via SM; currency unchanged; HVAC package `Missing` (if it has no other file); totals unchanged |
| T-S8 | R1 read; R1 deleted and R2 filed | Run | R2 `current`, R1 `removed`; counted once |
| T-S9 | Folder holds R1 and R2 | Run | R1 `superseded`, not counted |
| T-S10 | Opus not ready | Run | All sources `unsupported(model_unavailable)`; currency unchanged; damper observations `held`; no fallback model used |

---

## 3. Metric populations and formulas

This section supersedes FI-P1 VALIDATION §4's "recovery = published **or held**". Researcher D had recommended published + held; that recommendation is withdrawn.

### 3.1 Populations (per run, per evaluation drawing set)

| Population | Definition | Credited as an interface? |
|---|---|---|
| **O: observed candidates** | Every candidate observation an agent emitted, in any `finding_state`, including rejected ones | No (diagnostic) |
| **H: held facts** | Observations with `finding_state = held`: in conflict, awaiting review, unsettled association, model unavailable | **No** |
| **A: accepted usable facts** | Observations with `finding_state = validated` **and** source `evidence_currency = current` **and** included in the run's current schedule | **Yes, the only credited population** |
| **X: stale facts** | Validated observations of a stale source | No (reported separately) |
| **GT: ground truth** | Annotated physical interface instances (`disposition = interface`) on drawings marked `exhaustive` (FI-P1 VALIDATION GT format) | Reference |

Engineer decisions taken during the run are **not** applied when measuring system output. The metric is computed on the system's own `A`, before human review.

### 3.2 Formulas

Matching: Hungarian assignment of A (or O) items to GT on (same key, same layout, per-type tolerance from FI-P1 VALIDATION §1). Each GT instance is matched at most once.

| Metric | Formula | Gate |
|---|---|---|
| **Accepted precision** | `|A matched to GT with correct key, floor and tag| / |A|` (held and stale items are **absent from numerator and denominator**) | ≥ 0.98 point estimate **and** Wilson 95 % lower bound ≥ 0.95 (EXAMPLE) |
| **Recovery** | `|GT matched by A| / |GT|`, where GT includes instances on layouts the agent failed to cover (uncovered = miss) | ≥ 0.90 |
| Critical false acceptances | Count of A items that are wrong on a safety-critical key (dampers, pumps, valves; owner may extend) and not caught | **= 0** |
| Held rate | `|H| / (|A| + |H|)` | Reported. Ceiling ≤ 0.25 (EXAMPLE) so that "hold everything" cannot pass. |
| Held-recall (diagnostic) | `|GT matched by H| / |GT|` | Reported, **never** added to recovery |
| Candidate recall (diagnostic) | `|GT matched by O| / |GT|` | Reported (detection ceiling) |
| Recovery on covered layouts (diagnostic) | Recovery restricted to GT on layouts with `coverage = complete` | Reported |
| Stale exposure | `|X|` and the GT instances only matched by X | Reported; must be 0 in evaluation runs |
| Location / association correctness | As in FI-P1 VALIDATION, computed on A only | Reported; gate per owner after baseline |

### 3.3 Tests

| Id | Given | Then |
|---|---|---|
| T-M1 | 10 GT; A = 8 correct; H = 2 matching the remaining GT | Recovery = 0.80, not 1.00; held-recall = 0.20 |
| T-M2 | A = 50 with 1 wrong, H = 30 | Precision = 49/50 = 0.98; held items not in the denominator |
| T-M3 | GT on an uncovered layout | Counted as a miss in recovery; present in "covered layouts" diagnostic only as excluded |
| T-M4 | Stale source with validated observations | Excluded from A; appears in X; stale exposure reported |
| T-M5 | Held rate 0.6 with precision 1.0 | Gate fails (held-rate ceiling) |

---

## 4. Baseline and evaluation gates (accuracy and elapsed time)

### 4.1 Baseline record (must exist before any improvement claim)

```
BaselineRecord {
  baseline_id, pipeline: "fa_interfaces_scan@<git commit>+<worktree digest>",
  provider: {name, cli_version|api, models: {drawing:"claude-opus-5-5", orchestrator:"n/a (baseline has none)"}, effort},
  dataset: {dataset_id, sources: [{sha256, path}], gt_files: [{sha256}], exhaustive_drawings:int},
  machine: {hostname_hash, cpu, ram_gb, os, worker_concurrency, ai_max_concurrency},
  runs: [ { mode: cold|warm, started_at, t_total_s, t_first_usable_s, peak_rss_mb, model_calls, tokens|unknown,
            outcome_counts{A,H,O}, metrics{precision, recovery, critical_fa, held_rate} } ],
  summary: { per_mode: {median_t_total_s, min, max, precision, recovery} }
}
```

- **Cold mode:** empty DXF cache and result cache (conversion included). **Warm mode:** DXF cache kept, result cache cleared.
- Three runs per mode (EXAMPLE). The machine must be otherwise idle, and the declared settings must be identical between baseline and candidate except the feature under test.
- **Baseline populations for today's pipeline:** A = scheduled rows backed by `status:"read"` sources; H = verification groups plus pending dampers; O = scan items.
- **Elapsed definitions:**
  - `t_total` runs from job claim to run terminal plus the publication decision.
  - `t_first_usable` runs from job claim to the first validated, current observation persisted. For the baseline it equals `t_total`, because it publishes at the end.
- **Precondition (C, today):** the baseline **cannot be recorded yet**. In-app model calls fail (§5 P1/P4), and no exhaustive GT exists. So no improvement can be claimed until P1–P5 and the GT annotation are done.

### 4.2 Gates

| Gate | Pass condition | Blocks |
|---|---|---|
| **G-BASE** | BaselineRecord frozen (hash in MANIFEST) for the same dataset and machine | Any comparison or claim |
| **G-ACC** | Candidate: accepted precision and recovery meet §3.2 gates; critical false acceptances = 0; non-inferior to baseline on precision and recovery (candidate − baseline ≥ −0.01, EXAMPLE); held rate under the ceiling | Cutover; any accuracy claim |
| **G-TIME** | At the chosen model-slot setting (2, 4 or 6): candidate median `t_total` ≤ 0.8 × baseline median (EXAMPLE), **and** candidate max < baseline min (non-overlapping), in both cold and warm modes. `t_first_usable` is reported. | Any "faster" claim |
| **G-BOTH** | G-ACC and G-TIME at the **same** configuration | Claiming "faster without accuracy loss" |
| **G-NONREG** | Existing test suite green; FI-P1 r1 tests (T-F*, T-S*, T-M*) green | Every stage merge |

- **Rule:** concurrency results are throughput evidence only. An accuracy claim needs G-ACC. A speed claim needs G-TIME. Neither substitutes for the other.

### 4.3 Tests

| Id | Then |
|---|---|
| T-G1 | Comparison tool refuses to report deltas if baseline and candidate dataset digests differ |
| T-G2 | G-TIME computed from medians plus the range check, and fails when ranges overlap |
| T-G3 | Report shows A/H/O counts beside every precision/recovery figure |

---

## 5. Implementation prerequisites: checked 2026-10-04 (this session)

| Id | Prerequisite | Result | Evidence |
|---|---|---|---|
| P1 | Configured Claude CLI path usable | **FAIL** | `.env` `AI_CLAUDE_CLI=C:\Users\ramadan.mohamed\AppData\Local\ep-platform\claude-2.1.286\claude.exe`. The path does not exist, and the user here is `laptop-il4l4uaj\moham`. `ai_claude_cli` is **not** passed through `expand_path()` (app/core/config.py:9-15 vs :332; app/ai/provider.py:484), so `%LOCALAPPDATA%` cannot be used today. (C) |
| P2 | `claude-opus-5-5` runnable | **PASS on CLI 2.1.288** (the only ≥ 2.1.280 version tested): `C:\Users\moham\.vscode\extensions\anthropic.claude-code-2.1.288-win32-x64\resources\native-binary\claude.exe` answered with `modelUsage` `claude-opus-5-5` (+ internal Haiku). **FAIL on the PATH CLI 2.1.263** (WinGet): "requires 2.1.280 or newer". The 2.1.288 binary belongs to the VS Code extension and changes with extension updates, so it is not a stable install. (C) |
| P3 | `claude-fable-5-1` runnable | **PASS** on 2.1.263 and 2.1.288. **WARN:** one of three 2.1.288 probes also listed `claude-opus-4-8` in `modelUsage`; two retries did not. Cause unknown (A: CLI-side routing or fallback). V-F3 / the substitution check must treat it as a substitution. (C) |
| P4 | Effort `high` applied | **FAIL**: `ClaudeCodeProvider` never passes `--effort` (provider.py:538-541). The CLI accepts it. (C) |
| P5 | Model actually used reported | **FAIL**: `used` = first non-Haiku key (provider.py:568). That can mask a substitution such as P3. The API provider reports the requested id (FI-P1 REVIEW R-1). (C) |
| P6 | API provider alternative | **Not available**: no `ANTHROPIC_API_KEY` in the environment and no `AI_API_KEY` in `.env` (presence checked only). (C) |
| P7 | No Sonnet or alias substitution in config | **FAIL**: `.env` `AI_MODEL_SMALL=sonnet`, `AI_MODEL_STANDARD=opus` (→ claude-opus-5 on the CLI). Owner decision. (C) |
| P8 | Services | **FAIL for live runs / baseline**: API, sync worker, web running; IFC worker stopped (by owner request earlier today). (C) |
| P9 | Exhaustive ground truth for at least 2 drawings | **FAIL**: none exists (FI-P1 VALIDATION). Blocks G-BASE, not Stage 0. |
| P10 | Received display honours R-C4 | **FAIL**: the `received()` stale fallback (§2.5). (C) |

Nothing was substituted. Six one-line "reply OK" probes were made, with no project documents. They did not test `--json-schema` or `--effort` behaviour, which the 0.0/0.2 readiness check must cover for both models. Not yet assessed: subscription rate limits at 2, 4 and 6 concurrent CLI calls.
