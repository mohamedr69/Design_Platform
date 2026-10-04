# FI-P1 r1: correction to the FA Interfaces drawing-agent plan

| | |
|---|---|
| Version | **FI-P1 r1** (2026-10-04), correcting **FI-P1** (`../FI-P1-DRAWING-AGENTS-PLAN/`, frozen by its MANIFEST.json and left unchanged) |
| Scope | Planning-only correction. No application code, settings, databases, drawings or frozen packages were changed. The only model calls were six one-line "reply OK" availability probes in this correction round: Opus 5.5 and Fable 5.1 on each of CLI 2.1.288 and CLI 2.1.263, plus two Fable retries on 2.1.288. None contained project documents. These probes tested plain answering only, not `--json-schema` or the effect of `--effort`. |
| Companion files | CHANGE-MAP.md (what changed, where), CONTRACTS-R1.md (testable contracts), REVIEW-R1.md (independent critical review and verdict), MANIFEST.json |
| Precedence | Where r1 and FI-P1 disagree, **r1 governs**. Everything not superseded in CHANGE-MAP.md stays in force. |

## 1. Why a correction

The owner reviewed FI-P1 and asked for four corrections:

1. **Restore Fable as the active orchestrator.** FI-P1 had reduced Fable to an optional adjudicator (default off) and a templated summary. The owner's architecture is: concurrent Opus drawing agents, one accountable report per drawing and per package, and Fable receiving those reports, checking coverage and conflicts, and producing a consolidated review proposal. Deterministic code still enforces scheduling, locks, budgets, evidence validation, arithmetic and publication.
2. **Fix the stale-evidence contract.** FI-P1 (CONTRACTS §11 rule 2, and the orchestrator's own amendment R-30 / rule 5b) kept a failed reread or a missing folder's last reading as `status: "read"` + `stale`, so it **counted** toward current totals. The current, uncommitted `received()` also shows saved data as "Received" when the root is unreachable. Stale evidence must be preserved and shown, but kept separate and never counted.
3. **Separate the metric populations.** FI-P1 VALIDATION credited **held** facts toward recovery. Only accepted usable facts may be credited. A measurable baseline and gates are also needed for both accuracy and elapsed time.
4. **Re-check the implementation prerequisites** and report failures explicitly.

## 2. Corrected architecture (r1)

```
Freeze manifest (deterministic; one source per content hash; paths[]/packages[])
   │  readiness check: Opus (agents) and Fable (orchestrator), both explicit; nothing substituted
   ▼
Concurrent Opus drawing agents (one per source; effort high) ── each emits DrawingAgentReport
   │  reports stream into per-package inboxes; deterministic validation as they arrive
   ▼
FP1  Fable package review (one per package, when its sources are terminal)  → PackageReviewProposal
   ▼
Deterministic cross-drawing reconciliation + coverage ledger + current totals (arithmetic only here)
   ▼
FP2  Fable run consolidation  → ConsolidatedReviewProposal  (≤ 1 rework round → FP3)
   ▼
Deterministic gate (R-P1..R-P4): current schedule (current + validated only); stale shown separately;
published pointer advances only on complete + reviewed + engineer accept; otherwise provisional
   ▼
Application report + Obsidian export (review_state and stale sections included)
```

What Fable receives, returns and does when unavailable is specified in CONTRACTS-R1 §1:
- Fable is mandatory and visible.
- If unavailable, the run continues deterministically, labelled `orchestrator_review: missing (<reason>)`, with publication capped at provisional and a Retry action.
- No other model stands in for Fable.

## 3. Corrected evidence-currency contract (summary)

The full contract is CONTRACTS-R1 §2.

- **Received** comes only from the current folder listing. **Current evidence** means hash-verified against a file present now.
- **Stale evidence** covers a failed reread, a missing folder or an unreachable root. It is kept under `last_known`, written with `status: "stale"` (excluded by `build()`, which counts `status == "read"` only, service.py:434), and shown in a separate "Last known, not current" section with its own totals.
- Stale evidence never enters current totals, KPI cards or the Received badge.
- SPEC §11 ("do not replace a useful previous result with an apparently empty schedule") is met by keeping the **last published schedule** visible and unreplaced until a complete, reviewed, accepted run supersedes it (R-P3). It is no longer met by counting stale data.
- Duplicate content hashes are read once and attributed once, and every package listing them shows the shared copy (R-D1..R-D5).

## 4. Corrected metrics and gates (summary)

The full definitions are CONTRACTS-R1 §3–§4.

- **Populations.** O = observed candidates, H = held facts, A = accepted usable facts (validated **and** current **and** in the current schedule), X = stale facts.
- **Only A is credited.**
  - Accepted precision = correct A / A.
  - Recovery = GT matched by A / all GT, with uncovered layouts counted as misses.
  - Held-recall and candidate recall are diagnostics only.
  - A held-rate ceiling stops "hold everything" from passing.
- **Baseline.** A frozen `BaselineRecord` of today's `fa_interfaces_scan` on the same dataset, machine and models, cold and warm.
- **Gates.**
  - G-ACC: precision ≥ 0.98 with Wilson lower bound ≥ 0.95, recovery ≥ 0.90, zero critical false acceptances, and non-inferiority to the baseline.
  - G-TIME: median ≤ 0.8 × baseline, with non-overlapping ranges, cold and warm.
  - G-BOTH applies at the same configuration.
  - Threshold numbers marked EXAMPLE need owner approval.
- **Status.** No improvement may be claimed today: the baseline cannot be recorded until P1–P5 and P9 pass.

## 5. Prerequisites: results of the re-check

The full table with evidence is CONTRACTS-R1 §5. Each failure is listed explicitly and nothing was substituted.

- **P1 FAIL:** the configured CLI path belongs to another Windows user (`ramadan.mohamed`) and does not exist. The path setting does not expand `%LOCALAPPDATA%`.
- **P2:** `claude-opus-5-5` **runs on CLI 2.1.288** (the only version ≥ 2.1.280 tested), the binary bundled with the VS Code extension. The PATH CLI 2.1.263 rejects it. The extension binary is not a stable install for a server.
- **P3 PASS with a WARN:** Fable 5.1 runs on both CLIs. One probe listed `claude-opus-4-8` usage beside Fable (not reproduced), so the substitution check is mandatory.
- **P4 FAIL:** effort is not passed. **P5 FAIL:** the model actually used can be masked.
- **P6:** there is no API credential, so the API provider is not an alternative today.
- **P7 FAIL:** the Sonnet and `opus` aliases in `.env`.
- **P8 FAIL for live runs:** the IFC worker is stopped.
- **P9 FAIL:** there is no ground truth.
- **P10 FAIL:** the `received()` stale fallback.

## 6. Corrected implementation sequence (replaces FI-P1 IMPLEMENTATION-SEQUENCE §1–§2)

| Step | Change | Tests | Rollback | Depends on |
|---|---|---|---|---|
| **0.0 Environment (owner/ops, not code)** | Install a **pinned** Claude Code **2.1.288** (the only version ≥ 2.1.280 tested on this PC) for the worker's Windows user at a machine-neutral location. Set `AI_CLAUDE_CLI` to it. Replace the `sonnet`/`opus` aliases with full ids (owner decision D1/D2). Restart API and both workers. | Readiness probe (0.2) reports `ready` for `claude-opus-5-5` and `claude-fable-5-1`, each tested with `--json-schema` structured output and `--effort high` | Restore previous `.env` | Owner D1, D2 |
| **0.1 Evidence currency + publication guard** | `scan_project` per-entry merge per CONTRACTS-R1 §2. Stale entries are written `status:"stale"` with `last_known`. `removed` and `superseded` as before. Abort on an unreachable root. `received()` returns `Unreachable` instead of saved data. Coverage badges per R-C4, and a stale section in the payload. | T-S1…T-S9 (T-S6/T-S7 apply once sources are keyed by hash in Stage 1; in Stage 0 they assert that no double count occurs with today's per-path entries) | Revert function; `status:"stale"` entries are ignored by `build()` | — |
| **0.2 Provider honesty** | `expand_path` for `ai_claude_cli`. `claude --version` at provider build, with a minimum-version table per model. `--effort` pass-through. `used_model` from `modelUsage`: any non-auxiliary model other than the requested one means `model_substituted`. No server-side fallbacks for FA steps on the API provider. `unavailable` reported instead of `auth` when the CLI is missing. | Fake-CLI unit tests: version gate, effort argument, substitution detection (incl. a `claude-opus-4-8` entry), missing path → `unavailable` | Setting flag | 0.0 for live use; code is independent |
| **0.3 Cancellable, time-boxed rendering** | As FI-P1 0.3 | As FI-P1 | As FI-P1 | — |
| **0.4 Honest gating** | As FI-P1 0.4, plus T-S10 behaviour (model unavailable → `unsupported`, held) | T-S10 | revert | 0.2 |
| **0.5 Baseline capture** | Run the BaselineRecord protocol (CONTRACTS-R1 §4.1) on the owner-approved dataset | G-BASE | n/a | 0.0–0.4, GT annotation (P9) |

Stages 1–9 are unchanged from FI-P1, except:
- Stage 4: agents report into package inboxes.
- **Stage 6:** Fable FP1/FP2/FP3, the `review_state` machine, the DeterministicReviewDigest and the Retry action (CONTRACTS-R1 §1). This is a mandatory stage, no longer an optional flag.
- Stage 7: R-C4 badges, the stale section, last-published-versus-provisional display and the review-state banner.
- Stage 9: metrics per CONTRACTS-R1 §3 and gates per §4.

**Smallest first code task: Stage 0.1.** It is unchanged from FI-P1 in purpose (protect existing data) but now follows the corrected contract: stale entries are kept and **not counted**.

## 7. Owner decisions (replaces FI-P1 PLAN §13 items 1, 3 and 11; others stand)

| # | Decision | Options / recommendation |
|---|---|---|
| D1 | CLI installation for the workers | Pinned Claude Code 2.1.288 (tested) copied to e.g. `%LOCALAPPDATA%\ep-platform\claude-<version>\claude.exe` (needs 0.2's `expand_path`), **recommended**. Or temporarily point at the VS Code extension binary (2.1.288), which works today but moves with extension updates. Or an API credential. |
| D2 | Model ids in `.env` | Full ids: drawing agents `claude-opus-5-5`, orchestrator `claude-fable-5-1`. Decide whether IFC symbol review stays on Sonnet (currently `sonnet` alias) or moves. |
| D3 | Fable unavailable policy | **Recommended:** run continues, review `missing`, publication provisional. Alternative: refuse to start a run without Fable. |
| D4 | Gate thresholds marked EXAMPLE | Wilson lower bound 0.95; non-inferiority margin 0.01; held-rate ceiling 0.25; G-TIME factor 0.8; 3 runs per mode |
| D5 | Ground-truth annotation | At least 2 exhaustive drawings before G-BASE (FI-P1 estimate ≈ 1–2 engineer-days, EXAMPLE) |

## 8. Verdict

**CHANGES REQUIRED.** The independent review (REVIEW-R1.md) found 3 critical, 12 major and 3 minor issues. The factual ones (#3, #16) are applied here. The design ones (#1, #2, #4–#15, #17, #18) are accepted and open for r2.

- Stage 0.1 must not start from r1.
- Stages 0.2 and 0.3 are unaffected by the open findings and may start offline, on the owner's explicit instruction only.
- Full reasoning is in REVIEW-R1.md §4.
