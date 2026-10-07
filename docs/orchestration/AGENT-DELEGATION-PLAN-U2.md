# Agent Delegation Plan for the Unified Roadmap M1–M25

Confirmed by the owner on 6 October 2026 (authority entry A-12 in `MR/orchestrator/AUTHORITY-REGISTER.md`; ledger ORCH-033). The agent definition files in section 3 exist at `.claude/agents/` on branch `roadmap/u2`.

`MR` = `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap`. `REPO` = `G:/dev (2)/dev/ep-platform-merged/ep-platform` (shared checkout, branch `merge/candidate`, used by another session). `WT` = `G:/dev (2)/dev/ep-platform-merged/roadmap-u2` (worktree on branch `roadmap/u2`, frozen at `f627f35c3d37e2c64f4fea41b715834d3688a0e4`). Roadmap = `docs/UNIFIED_MASTER_ROADMAP.md` (Revision U2).

## 1. What this plan inherits and what it changes

Inherited unchanged from A-03 and A-11:
- The orchestrator never edits application code, never drafts or reviews labels, never fabricates consent, tokens or authorizations, never bypasses a refusal.
- One write-capable agent per code tree, database or package at a time. Read-only agents may run in parallel.
- Every implementation task runs in a fresh isolated agent on an isolated worktree, never on the live merged installation.
- Frozen packages, declarations and reviews are never edited; new work gets new files and new hashes.
- No provider or model request through the EP Platform or any harness without an explicit owner budget authorization for that exact run.
- Stop points: owner-only permission or budget decision, material authority conflict, missing or corrupted evidence, PREPARATION BLOCKED, readiness for a live-validation declaration.

Changed by the owner (A-12):
- Orchestrator effort: Fable 5.1 at **high** (A-03 said ultracode / highest).
- Non-coding work (surveys, inventories, documentation, test execution and reporting, UI observation) moves to **Sonnet 5.5**.
- The roster is extended from M2-only to the whole M1–M25 sequence.
- All roadmap implementation happens on `roadmap/u2`; merges to `merge/candidate` only on a per-task owner go.

## 2. Roster

| Role | Agent name | Model / effort | Writes to | Runs in parallel? |
|---|---|---|---|---|
| Orchestrator | the session | Fable 5.1 / high | `MR/orchestrator/*`, `WT/docs/orchestration/*`, task cards, ledger | n/a |
| Implementer (code, tests, migrations, frontend) | `ep-implementer` | Opus 5.5 / high | its own git worktree only | **No**, one at a time |
| Independent verifier (acceptance review of a delivered task) | `ep-verifier` | Opus 5.5 / high | new files under `MR/reviews/<id>/` only | Yes, read-only |
| Test runner (executes suites, collects evidence, no edits) | `ep-test-runner` | Sonnet 5.5 / medium | `WT/docs/milestones/M<n>/evidence/` only | Yes |
| Surveyor (read-only code and evidence inventories) | `ep-surveyor` | Sonnet 5.5 / medium | `MR/orchestrator/surveys/` only | Yes |
| Scribe (milestone records, matrices, handoffs) | `ep-scribe` | Sonnet 5.5 / medium | `WT/docs/milestones/M<n>/*.md`, drafts for `MR/orchestrator/` | Yes, one per file set |
| Label reviewer (Golden truth, fresh cohorts) | `ep-label-reviewer` | Opus 5.5 / high | one new response file in the reviews folder | Yes, split by project |
| UI checker (drives the local app in the browser, screenshots, no edits) | `ep-ui-checker` | Sonnet 5.5 / medium | `WT/docs/milestones/M<n>/evidence/ui/` only | Yes |

The verifier stays on Opus 5.5 high because every milestone exit requires an independent acceptance verdict. A task card may lower it to Sonnet for documentation-only or survey-only work.

The test runner is separate because running the 1,801-test suite and the section 5 integration proof is execution and reporting, not coding. Writing or changing tests is implementer work.

The UI checker exists because the frontend has no test framework. An implementer card at M10 may add Playwright or vitest (A-12 item 9).

## 3. Agent definition files

See `.claude/agents/ep-implementer.md`, `ep-verifier.md`, `ep-test-runner.md`, `ep-surveyor.md`, `ep-scribe.md`, `ep-label-reviewer.md`, `ep-ui-checker.md`. Frontmatter keys used: `model` (full id), `effort`, `tools`, `disallowedTools`, `permissionMode`, `isolation: worktree` (implementer only), `memory: project` (implementer only). The implementer and scribe may edit; every other agent is read-only on source and writes only its own output files.

## 4. Milestone-by-milestone delegation

Each milestone runs as a sequence of bounded task cards `ORCH-<n>` written by the orchestrator in `MR/orchestrator/tasks/`.

| Milestone | Agents and order | Gate the verifier certifies |
|---|---|---|
| M1 refresh | surveyor (field/producer/consumer/GET-work matrix) → scribe (updated M1 matrix) → verifier | every critical fact/artifact has one owner, producer and consumer contract |
| M2 refresh | surveyor (delta inventory vs the 35 findings) → test-runner (frozen Golden reproduction) → scribe → verifier | findings traceable to hashes; bounded cases reproducible |
| M3 | scribe drafts the access/retention/authority/reuse contract → **owner decision** → verifier | recorded contract accepted before authoritative memory writes |
| M4 | **blocked on owner decisions D1–D11** (`MR/orchestrator/OWNER-DECISION-CARD-M2.md`). After them: implementer (port of `a8aaced` corrections onto an isolated copy of the current tree) → test-runner (full suite, failure-by-name comparison) → label-reviewer where a cohort needs it → verifier → final independent M2-matrix review | all 17 gates of `MR/orchestrator/M2-ACCEPTANCE-MATRIX.md` |
| M5 | verifier (ORCH-035 disposition) → implementer (port safe Apply onto current preparation code; add `tests/test_redesign_apply.py`; server-enforced approved-only gate; no implicit archive publication) → test-runner → verifier | approved inserts/erases reconcile exactly; stale approvals and commit failure publish nothing; concurrent publication test reproduced |
| M6 | implementer (attribution states, conflict handling, lineage) → test-runner (shadow evaluation with scripted model) → verifier | per-type precision/recall report; no business state changed by classification |
| M7 | surveyor (existing artifacts and jobs) → implementer in 3–4 cards (registry schema; stage/capability status; idempotency and dedup; relationships and outbox) → test-runner → verifier | rerunnable processors produce records once; APIs serve without opening originals |
| M8 | implementer (wall index: effective layers, block transforms, visibility, allow-lists, composition report) → test-runner (simple sheet, rotated view, Golden drawing) → implementer (doors, ceilings, containment, spacing, clash) → verifier | no placement justified by invisible or non-wall geometry |
| M9 | implementer (checkpointed discovery replacing the 2,000-file refusal) → test-runner (2,000 / 5,000 / 10,000 synthetic trees) → verifier | eligible = processed + skipped + failed + unresolved |
| M10 | per tab: surveyor (GET-side work) → implementer (move work to processors/commands) → test-runner (no-read-work check) → ui-checker → verifier; Home last | ordinary reads do no parsing, OCR, model calls, folder scans or writes |
| M11 | implementer (dependency graph, invalidation) → test-runner (concurrency, restart, retry, section 5 zero-call proof) → implementer (PostgreSQL rehearsal scripts) → verifier | no duplicate processing; accurate invalidation; accepted database path |
| M12 | implementer (rendered proposals, separate visual review, bounded repair loop) → ui-checker → verifier | deterministic and visual evidence agree; proposals held when uncertain |
| M13 | **owner decision** on fresh cases and any real-model or real-AutoCAD budget → label-reviewer → test-runner → verifier → engineer sign-off recorded by scribe | predeclared gates pass; no unresolved critical error |
| M14–M16 | implementer (migrations, scoped repository, facts adapters, evidence links) → test-runner → verifier | same-project constraints; fact questions answered without an LLM |
| M17 | implementer (memory tab) → ui-checker → verifier | manual lifecycle works end to end |
| M18–M20 | implementer (durable events, conflicts/authority, versioned summaries) → test-runner (section 10 acceptance examples) → verifier | one applicable truth or explicit conflict; stale summaries never override facts |
| M21–M22 | implementer (project-scoped index over stored extraction; context builder) → test-runner (filter-before-rank, namespace separation, token-pressure cases) → verifier | no duplicate PDF reader; required evidence preserved under budget |
| M23 | implementer (candidate capture, validation, dedup, risk policy) → verifier | critical inference never auto-confirmed |
| M24 | implementer per workflow → test-runner (section 5 proof repeated with Project Memory) → ui-checker → verifier | one context contract across workflows |
| M25 | test-runner (labeled evaluations, recovery gates, metrics) → scribe (final records) → verifier (final independent acceptance) → **owner acceptance** | all section 8 M25 metrics reported with denominators |

## 5. Operating protocol per task card

1. Orchestrator writes `MR/orchestrator/tasks/ORCH-<n>-TASK.md`: milestone, snapshot commit, allowed paths, preserved behaviour, regression cases, completion evidence, forbidden actions.
2. Implementer runs in a fresh worktree branched from the snapshot commit on `roadmap/u2`. No other write-capable agent runs meanwhile.
3. Test runner records the suite results into the milestone evidence folder.
4. Verifier (different fresh agent) returns PASS / CHANGES REQUIRED / BLOCKED BY MISSING EVIDENCE.
5. Orchestrator checks hashes and counts, appends a ledger entry, updates `ORCHESTRATOR-STATE.md` and the milestone record (roadmap section 13), then either issues a correction card or merges the task branch into `roadmap/u2`. Merges from `roadmap/u2` into `merge/candidate` need the owner's go per task.
6. Every delegated agent is reported in chat with its task identity and model (A-03 item 9).

## 6. Owner decisions recorded (A-12)

1. Branch strategy: `roadmap/u2` from freeze commit `f627f35`; merge back only on owner go.
2. Orchestrator effort high; Sonnet for non-coding roles; verifier stays Opus 5.5 high.
3. M1, M2, M3, M5 and M8 proceed in isolation while M4 waits on D1–D11.
4. Each real-model run needs its own authorization when reached.
5. Playwright or vitest may be added at M10 by an implementer card.
6. PostgreSQL (M11), AutoCAD (M5/M13) and fresh cases (M13) are supplied by the owner when reached.
7. Evidence under `docs/milestones/M<n>/` on `roadmap/u2`; governance in `MR/orchestrator/`.
8. Agent files at `.claude/agents/` on `roadmap/u2`.
9. Full-suite baseline before any implementation card.

## 7. First three task cards (issued, not launched)

- `MR/orchestrator/tasks/ORCH-033-TASK.md`: test-runner, full-suite baseline on the freeze commit; evidence to `docs/milestones/M1/evidence/baseline-u2/`.
- `MR/orchestrator/tasks/ORCH-034-TASK.md`: surveyor, M1 refresh inventory.
- `MR/orchestrator/tasks/ORCH-035-TASK.md`: verifier, final disposition of the RD-M2 race correction against the current redesign service, so the M5 implementer card can be written.
