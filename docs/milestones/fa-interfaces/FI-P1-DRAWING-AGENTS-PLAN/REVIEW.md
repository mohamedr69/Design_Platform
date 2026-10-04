# FI-P1 — REVIEW: critic findings and dispositions

One review pass, as the owner's workflow requires (SPEC §13: "one fresh Opus critic reviews the consolidated design
once; resolve concrete findings; no unlimited review loops").

| Item | Value |
|---|---|
| Critic | Fresh-context agent, Agent tool model override `opus`; effort not settable/verifiable (PLAN §0). Read-only; spot-checked ~35 code citations. |
| Reviewed | The six files as first consolidated (Fable consolidator, Agent tool override `fable`). |
| Verdict as delivered | **Not implementation-ready as written**: Stage 0.1 double-counted removed revisions (R-2) and used the wrong reachability rule (R-3); the API-provider option hid a Fable→Opus silent substitution (R-1). |
| Disposition | All 29 findings **accepted**. Fixed in one pass by the consolidator; the session orchestrator verified R-1 and R-18 in code, spot-checked the fixes, and added R-30 and R-31. No second review loop. |
| Status after fixes | Stage 0 (0.1–0.4) is specified to an implementable level. Stages 1–9 are designed but depend on the owner decisions in PLAN §13 and on ground truth (VALIDATION.md). |

Orchestrator verification of the critical items:
- **R-1:** `provider.py:173-176` (docstring: Fable declines "answered by an Opus model"); `:251-253` (`fallbacks="default"`); every `AiResponse(... model=model ...)` at `:238-299` reports the requested id. CONFIRMED.
- **R-18:** `ai/cache.py` is 128 lines, and `class InFlight` is at `:102`. CONFIRMED.
- **R-3:** the existing test project creates only 3 of the 6 discipline folders (`tests/test_fa_interfaces.py` `_project`). Found independently by the orchestrator.

## Dispositions

| # | Sev. | Finding (short) | Disposition | Where fixed |
|---|---|---|---|---|
| 1 | critical | API provider sends Fable with server-side fallbacks and logs the requested id: silent Fable→Opus substitution | Accepted | PLAN §12 (Fable row "Not clean", new "Model actually used" row, rule 2), HANDOFF #7; PERF §6 probe (`fallbacks_disableable`, `reports_used_model`); CONTRACTS §8 `model.used_id`/`substituted_calls`, §13 `no_fallbacks`/`model_substituted`; VALIDATION §2 check 12; IMPL Stage 0.2 |
| 2 | critical | Stage 0.1 keeps "missing" sources as `read`+`stale`, so `build()` double-counts removed revisions | Accepted | CONTRACTS §11 PublicationGuard rules 0–6 (`removed` excluded by `build()` :434); IMPL §1 with test "R1 removed + R2 added counted once"; PLAN §2 rows 1/12, §4, HANDOFF #9. Amended by R-30. |
| 3 | major | Abort on "any discipline root unreachable" is wrong; only the project root | Accepted | IMPL §1 rule (0) + test (2); PLAN §2 row 1; CONTRACTS §1 `discipline_roots.state` |
| 4 | major | Raising `ai_max_concurrency` multiplies the model limit across processes | Accepted (see R-31) | PERF §2 one cross-process `model` pool in `ModelGate`, used by all callers; PERF §7; PLAN §3, HANDOFF #4; IMPL Stage 2 |
| 5 | major | Two writers of `row.sources`; undefined `generation` column | Accepted | PERF §2 shared dedup key `fa_interfaces:{project_id}`; IMPL Stage 1 (old path through the publisher; `generation` added by migration); CONTRACTS §11; OBSIDIAN §1; PLAN §2 row 12 |
| 6 | major | Decision ids embed the sha, so every re-save orphans decisions | Accepted | CONTRACTS §0/§6 sha-independent `decision_key`, §11 `needs_reconfirm`; VALIDATION check 11; PLAN §2 row 10; IMPL Stage 3 |
| 7 | major | Migration would map the merged two-MSD confirmation onto one damper | Accepted | CONTRACTS §14 (tagged-only auto-map; untagged/visual → `orphaned_decisions`; 0.47 m / 1.26 m example); PLAN §13 #10; IMPL Stage 3 test |
| 8 | major | `duplicate_symbol` auto-merge reproduces the two-MSD failure | Accepted | VALIDATION §2 check 7 (merge only for compatible labels, else held ConflictSet with all members) |
| 9 | major | Reviewer trigger lets self-reported confidence decide who escapes review | Accepted | VALIDATION §3 (every model-proposed physical/association finding not settled by a geometric rule; confidence only orders the queue); CONTRACTS §6 `settled_by_rule`, §9 `review_required`; PERF §3; IMPL Stage 5 |
| 10 | major | Cross-file union-by-symbol double-counts; identical viewport is not alignment proof | Accepted | PLAN §7/§9; CONTRACTS §3 `identical_viewport_candidate` / `control_points` + residual, §10 `cross_file_match`; IMPL Stage 6 |
| 11 | major | `ProcessPoolExecutor` can't keep a Plan or be killed per task; the geometry lease starves the 2/4/6 test | Accepted | PERF §2 spawn `Process` per drawing with queues + `terminate()`, render windows to the evidence store, then release; PLAN §3; IMPL Stage 2 |
| 12 | major | Orphaned `claude.exe`/render children on Windows when the worker dies | Accepted | PERF §2 Job Object `KILL_ON_JOB_CLOSE` + startup reaper (`ai_usage.pid`, `process_started_at`); CONTRACTS §13; IMPL Stage 2. Job Object availability on worker PCs is marked A. |
| 13 | major | New `cancelling` job status breaks lanes/recovery/frontend | Accepted | CONTRACTS §12 (statuses unchanged; `progress.stage="cancelling"`); PERF §4; OBSIDIAN §2; PLAN §11 |
| 14 | major | DB leases for every pool: SQLite contention, over-machinery | Accepted | PERF §2: render/geometry/writer/convert pools are in memory in the orchestrator; only `model` uses the DB (`ai_model_leases`, `BEGIN IMMEDIATE` + retry); OBSIDIAN §1 |
| 15 | major | Queue wait counted as stall and as elapsed time | Accepted | PERF §3/§4 (stall only while holding a lease; elapsed from first dispatch); CONTRACTS §4/§8 `queue_wait_s`; IMPL Stage 2 test |
| 16 | major | `max_output_tokens_per_call` unenforced on the CLI provider | Accepted | CONTRACTS §4 note; PERF §3; PLAN §12 row, HANDOFF #7 |
| 17 | major | No durable storage for observations/validations/conflicts | Accepted | OBSIDIAN §1 `fa_interface_observations` (Stages 4–5), `fa_interface_conflicts` (Stage 6); IMPL Stages 4/6 migrations |
| 18 | minor | Wrong cite `cache.py:221-251` | Accepted | PERF §2/§4 → `ai/cache.py:102` |
| 19 | minor | API "Yes" cells unlabelled although untested | Accepted | PLAN §12 and PERF §6 marked A |
| 20 | minor | Lifecycle and coverage mixed in run status/progress | Accepted | OBSIDIAN §1/§2/§3 split `execution`/`coverage`; "stopped", not "cancelled" |
| 21 | minor | Accounting invariant differs between files; references need terminal state | Accepted | CONTRACTS §1 `reference_state`, §8 invariant over every manifest entry; PLAN §8; OBSIDIAN §2; IMPL Stage 4 |
| 22 | minor | Request allowance formula ignores per-layout calls | Accepted | PERF §3 `2×layouts + 2×windows + reviews + retries`, cap 200 (EXAMPLE), 19-layout worked example |
| 23 | minor | `expected_layouts` null at freeze | Accepted | CONTRACTS §1 (enumerated in the freeze step after conversion; null only when unsupported); PLAN §4; IMPL Stage 1 |
| 24 | minor | Handoff #3/#7 wording and omissions | Accepted | PLAN HANDOFF #3, #7 |
| 25 | minor | Fable's in-app role inconsistent; needs an owner decision | Accepted | PLAN §3 (Fable = adjudication only, default off ⇒ no in-app Fable work; summary templated), §13 decision #11; CONTRACTS §8; PERF §7 |
| 26 | minor | `source_id` collides for byte-identical copies | Accepted | CONTRACTS §0/§1 `source_id = sha24` + `paths[]` aliases, one agent per hash; PLAN §3/§5; OBSIDIAN §1/§3 |
| 27 | minor | Measurement protocol contradictory; request cost unstated | Accepted | PERF §5: two runs per setting, six runs, request cost ≤ ~4,800 (EXAMPLE) stated for owner approval |
| 28 | minor | Over-scope: `regions` model call duplicates deterministic sheet kind; `ai_requests` duplicates `ai_usage` | Accepted | PLAN §6 step 3 (deterministic first, Opus only for model-space regions outside viewports); `ai_requests` merged into an extended `ai_usage` (CONTRACTS §13, OBSIDIAN §1, PERF §3/§5, VALIDATION §4) |
| 29 | minor | Agent-tool `fable` → `claude-fable-5-1` mapping unverified | Accepted | PLAN §0 marked A |

## Orchestrator amendments after the fix pass

| # | Issue | Decision | Where |
|---|---|---|---|
| R-30 | The fix for R-2/R-3 applied the critic's rule literally: a wholly absent or empty **discipline folder** (project root reachable) turned that discipline's prior readings into `removed`. That is the failure SPEC §11 forbids ("do not replace a useful previous result … because discovery … failed"), e.g. a OneDrive folder not yet synced, or renamed. | `removed` only when the file is gone **from a present, non-empty discipline folder** (deleted/moved), or when an older revision is replaced by a newer one. A wholly absent/empty discipline folder keeps its readings `read` + `stale` (counted, banner). Nothing replaces them, so there is no double count. | CONTRACTS §11 rule 5/5b; IMPL §1 rule (5)/(5b) and test (2); PLAN §4 publish row, HANDOFF #9 |
| R-31 | R-4 fix: to let the 2/4/6 knob bind, the IFC worker's process environment raises `AI_MAX_CONCURRENCY` only during the experiment, while the global `ModelGate` caps the sum. | Accepted as an **experiment-only** setting. The production design remains: `ModelGate` is the binding cross-process limit, and `ai_max_concurrency` is an inner per-process cap left at its configured value. If the owner prefers no environment change, `ModelGate` replaces the semaphore inside `complete()` (a Stage 2 implementation choice). | PERF §2/§7 (unchanged text; this note governs) |

## Not resolved by this review (open, owner-dependent)

- **Model availability in the application** (PLAN §12, §13 #1–#3). No in-app model call works on this PC today (`AI_CLAUDE_CLI` path missing). `claude-opus-5-5` needs CLI ≥ 2.1.280. The `opus` alias means Opus 5. Sonnet is configured for IFC symbol review. The plan refuses substitution: agents end `unsupported`. It does not choose a provider.
- **Accuracy targets** (VALIDATION.md): 98 % / 90 % cannot be measured until exhaustive ground truth exists for at least two drawings.
- **Assumptions to verify early** (PLAN §14): handle stability across conversions, render determinism, Job Object availability, subscription rate limits at 4–6 concurrent CLI processes.

This review improved the plan's correctness. It did not change the application, and no claim is made that accuracy or speed has improved.
