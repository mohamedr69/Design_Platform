# FI-P1 r1: independent critical review and verdict

| Item | Value |
|---|---|
| Reviewer | Fresh-context critic. Agent tool model override `opus`; effort not settable. Did not write any part of r1. Read-only. Made no model calls. |
| Reviewed | CORRECTION.md, CHANGE-MAP.md, CONTRACTS-R1.md as first written, against the owner's correction request, frozen FI-P1 and the code |
| Reviewer verified in code/environment | `build()` counts `status=="read"` only (service.py:434); `received()` returns saved data on unreachable root (:1018-1019); CLI path not variable-expanded (provider.py:484-485; app/core/config.py:9-15 vs :332); no `--effort` (:538-541); `used` = first non-Haiku key (:568); configured CLI path absent; extension CLI 2.1.288, WinGet CLI 2.1.263; no API credential; `.env` aliases `sonnet`/`opus`; no IFC worker running; services run as `moham` |
| Orchestrator verified | Finding 10: `JobBudget.reserve` raises on `max_input_tokens_per_task` (app/ai/budget.py:86-87), and the default is 6000 (config.py:366), so a Fable package review would hit `budget_exhausted`. Finding 2: `received()` `return saved` (service.py:1018-1019). Finding 1 holds by construction: Stage 0.1 has no published snapshot. |
| Review passes | One. Findings are dispositioned below. No second review loop was run. |

## 1. Findings and dispositions

**Applied in r1** means it was a factual correction made after the review, without changing the design. **Open for r2** means it is accepted, but the design change is not yet written. It is not reviewed and must not be implemented from this package.

| # | Sev. | Finding (short) | Disposition | Status |
|---|---|---|---|---|
| 1 | critical | Stage 0.1 makes stale entries `status:"stale"` (dropped by `build()`) before the "last published" snapshot/display exists (Stage 1/7) → unsynced OneDrive gives an empty live schedule; T-S1's "last published still shown" not implementable in Stage 0 | Accepted: 0.1 must also persist an interim `published` snapshot (last good `build()` output, date, source digest) in the row and serve it beside the live result; T-S1/T-S2 assert it | **Open for r2** |
| 2 | critical | Unreachable root: §2.2 "counted as last published" means Stage 0 KPI cards still show saved data as current | Accepted: totals labelled "Last published, not verified now (date)"; current KPI unknown; T-S3 asserts payload labels | **Open for r2** |
| 3 | critical | REVIEW-R1/MANIFEST cited but absent; probe count wrong (said four, actually six) | Accepted | **Applied in r1**: this file and MANIFEST.json added; CORRECTION header and CONTRACTS-R1 §5 now state six probes and that they did not test `--json-schema`/`--effort` |
| 4 | major | R-P2 unsatisfiable (PDFs always `unsupported`); `reference_state` omitted; legacy job kind scope; no engineer-accept API before Stage 7; pointer seeding; export source unspecified | Accepted: `unsupported` restricted to supported kinds; add `reference_state`; scope per job kind; seed the pointer from current `row.sources` in Stage 1; exports carry the published schedule plus a separately titled provisional section | Open for r2 |
| 5 | major | Duplicate-hash rules contradict each other: per-package currency vs single value; T-S7 keys after a package drops; `decision_key` path-dependent; Stage-0 T-S6 has no mechanism | Accepted: currency per source (never per package); canonical package for `decision_key`; T-S7 states key/total expectations; Stage 0 reads a duplicated sha once with `duplicate_of` | Open for r2 |
| 6 | major | §2.2 table not total (unread→missing/removed, stale→deleted, removed→reappears, superseded→newer deleted; `unsupported` is coverage not currency; empty folder never becomes `removed`) | Accepted: total (state × event) table, one test per row; `unsupported` moved to coverage; an owner-confirmed "folder deliberately emptied" path to `removed` | Open for r2 |
| 7 | major | R-C4 badges incomplete or overlapping; "Received" defined two ways; `received()`/`coverage()` Stage-0 scope unclear | Accepted: ordered badge rule over all states; one definition of Received (present now); explicit Stage-0 changes to both functions | Open for r2 |
| 8 | major | No accountable per-package report when FP1 fails; DeterministicReviewDigest has no schema | Accepted: deterministic `PackageReport` always produced (ledger, stale, conflicts); FP1 annotates it; digest schema defined | Open for r2 |
| 9 | major | FP1 trigger ignores SCHED `reference_state`, empty packages, pending validation, reference snapshot readiness; FP3 leaves FP1 out of date | Accepted: FP1 when agents and validation are terminal and the snapshot is `ready`; skip agent-less packages; re-run FP1 for reworked packages before FP3 | Open for r2 |
| 10 | major | Fable budget/infrastructure missing: input cap 6000 tokens and calls/day would force `budget_exhausted`; no reserved allowance, chunking, ModelGate lease, retry cap, timeout or setting names; FI-P1 PERF §3 not superseded | Accepted (orchestrator-verified): `FA_ORCHESTRATOR_*` limits block with reserved allowance, size cap/chunking, ModelGate lease, Retry cap, timeout; supersede PERF §3 | Open for r2 |
| 11 | major | Injection/exfiltration: other free-text fields not bounded or fenced; crops carry text; CLI `--tools Read` with images can read any file (e.g. `.env`); Fable summary exported; truncation conflicts with FI-P1 field lengths | Accepted: bound and fence every free-text field; restrict Read to the temp directory or send images inline (API); scan outputs with `guard.instruction_flags` plus a secret check before storing/exporting; extend T-F8 to crops | Open for r2 (the Read-scope risk applies to **today's** `ClaudeCodeProvider` too, A) |
| 12 | major | Fable states inconsistent (`invalid_output`); `substituted` retry policy; model echo of `input_digest` fragile; assert no `--fallback-model` | Accepted: wrapper attaches and verifies the digest; `substituted` gets one retry then `missing`; states unified | Open for r2 (the no-`--fallback-model` assertion is part of Stage 0.2) |
| 13 | major | Metric populations unsound: not scoped to exhaustive layouts; engineer-derived validations inflate A; O/H/A/X do not partition (`proposed`, `rejected`); FI-P1 `finding_state=stale` name collision; critical keys changed silently; typical-floor matching unspecified | Accepted: scope to exhaustive layouts; exclude engineer-derived validations; full partition reported; rename FI-P1 finding `stale` → `needs_revalidation`; critical keys restored to dampers, fans, pumps (+ valves if owner agrees); typical-floor matching defined | Open for r2 |
| 14 | major | Baseline not computable: "today's pipeline" vs modified 0.0–0.4; line-level rows vs instance matching; mixed models (Sonnet symbol review) and unstated effort | Accepted: baseline = pipeline at a named commit after 0.0/0.2 only, with a settings snapshot; instance-expansion rule; location-free metric variant for both pipelines | Open for r2 |
| 15 | major | G-TIME gameable: `t_total` may include human time; speed allowed with lower coverage | Accepted: exclude human time; any speed claim requires identical coverage outcomes (G-BOTH) | Open for r2 |
| 16 | minor | Prerequisites overstated (Opus "only" on 2.1.288); D1 should pin the tested 2.1.288; readiness must test `--json-schema`+`--effort`; P8 had no PASS/FAIL; citation path; untracked service.py; rate limits not listed | Accepted | **Applied in r1** (wording, pin 2.1.288, readiness test scope, P8 = FAIL for live runs, `app/core/config.py`, rate limits listed as not yet assessed). `backend/app/interfaces/` is untracked, so "uncommitted" means "not in git", noted here. |
| 17 | minor | FI-P1 text left standing that r1 should supersede (PLAN §4/HANDOFF #9, §9/§13 #6, CONTRACTS §10/§13 `step` enum, IMPL Stage 6 rollback, OBSIDIAN readings fields) | Accepted: add these to CHANGE-MAP in r2 | Open for r2 |
| 18 | minor | Wilson lower bound 0.95 at p̂ = 0.98 needs \|A\| ≳ 120 on exhaustive layouts; pooled vs stratum unstated | Accepted: state minimum n and pooling | Open for r2 |

## 2. What r1 does settle (not disputed by the review)

- Fable is restored as a mandatory, visible orchestrator stage, with defined inputs, outputs, deterministic validation and an explicit unavailable path. Finding 8 asks for a deterministic per-package report underneath it; the principle stands.
- Stale evidence is never counted toward current totals or "Received". The principle is accepted; findings 1, 2, 6 and 7 make it implementable without data-loss regressions.
- Only accepted usable facts (A) are credited. Held facts are never credited. The populations are accepted; finding 13 tightens their scope.
- Prerequisite failures are reported explicitly, and nothing is substituted.

## 3. Implementation prerequisites: final status

| Id | Status | Blocks |
|---|---|---|
| P1 CLI path (other user's path; no variable expansion) | FAIL | Any live in-app model call |
| P2 Opus 5.5 | PASS on CLI 2.1.288 (VS Code extension binary); FAIL on PATH CLI 2.1.263 | Live drawing agents until a pinned 2.1.288 install (D1) |
| P3 Fable 5.1 | PASS on both; WARN: one unexplained `claude-opus-4-8` usage entry | Requires the Stage 0.2 substitution check |
| P4 effort / P5 model actually used | FAIL (code) | Fixed by Stage 0.2 |
| P6 API credential | Absent | API route |
| P7 Sonnet/alias config | FAIL (owner decision D2) | Live runs claiming "no Sonnet substitution" |
| P8 IFC worker | Stopped (FAIL for live runs) | Live runs, baseline |
| P9 ground truth | FAIL | Baseline, any accuracy claim |
| P10 Received shows saved data on unreachable root | FAIL (current uncommitted code) | Fixed by Stage 0.1 (r2) |

## 4. Verdict

**CHANGES REQUIRED: implementation of the corrected plan should not start from r1.**

- Stage 0.1, the planned first code task, is blocked by critical findings 1 and 2 and by majors 6 and 7.
  - As written, it would turn an unsynced OneDrive folder or an unreachable root into an empty or silently stale current schedule.
  - That is the behaviour the owner prohibited.
- Stages 1–9 are blocked by findings 4, 5 and 8–15.
- Live use is blocked by prerequisites P1, P2 (pinned install), P7 and P8. Any baseline or improvement claim is blocked by P9 and finding 14.

**Narrow exception, on the owner's explicit instruction only:**
- Stage 0.2 (provider honesty: `expand_path` for `ai_claude_cli`, a CLI version gate per model, `--effort` pass-through, substitution detection over all `modelUsage` entries, `unavailable` instead of `auth`, no `--fallback-model`, API `no_fallbacks` + `message.model`) and Stage 0.3 (cancellable, time-boxed rendering) are not affected by any open finding.
- They can be built and tested offline with a fake CLI.
- Stage 0.4 follows 0.2.
- Starting them is the owner's call. This package does not start them.

**Next step: r2.** Resolve findings 1, 2 and 4–18 in a revised CONTRACTS, one more independent review, then re-issue the verdict. Owner decisions D1–D5 (CORRECTION §7) can be taken in parallel.

No implementation was started. No claim of improved accuracy or speed is made.
