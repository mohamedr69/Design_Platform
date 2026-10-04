# Review 23 correction: terminal experiment stops survive resume (2026-10-01)

**Scope:** the one Review 23 finding, R23-01 — plain `--resume` of the document-arm runner cleared a recorded critical stop and dispatched further requests. Harness runner and tests only; offline; **no provider or model request**; no live schedule, cap increase, budget reset, new live scope or H-06 rerun; **the 688-request proposal remains unapproved**; no application code changed (frozen candidate `719e8de`, accepted `3d5607d`); R22-01 / R22-02 accepted and untouched; scorer, extraction layer and scheduler not rebuilt. Status by item: [STATUS.md](STATUS.md). Contract: [LIFECYCLE-CONTRACT.md](LIFECYCLE-CONTRACT.md). Files: [CHANGE-MAP.md](CHANGE-MAP.md). Commands / exit codes: [COMMANDS.md](COMMANDS.md). M2 remains **CHANGES STILL REQUIRED**.

## 1. Reproduction on the submitted v4 runner (before any change)

An adapted copy of the reviewer's `resume_stop_probe.py` (byte copy hash-checked; only its output directory, private workspace and runner path substituted — `repro/run_stop_probe.py`) was run in this package's own sandbox against the submitted `arm_ev.py` (byte-identical to the reviewer's copy and to review22's frozen v4). It uses only a private copy of the synthetic A baseline, deliberately disagreeing synthetic labels (`X-DRY-1 → X-DRY-9`), rebound hashes and the scripted provider — not a real-source accuracy finding.

| Invocation (v4) | Status | Stop reason | Requests this invocation | Projects | Not attempted |
|---|---|---|---|---|---|
| initial | stopped | critical acceptance … after EP-16830 | 12 (EP-16830) | 16830 | 17428 |
| plain `--resume` | stopped | critical acceptance … after EP-17428 | **8 (EP-17428)** | 16830, 17428 | 17428 (stale) |

The reviewer's three regressions: **1 failed, 2 controls passed** ([repro/on-v4/](repro/on-v4/)). Logs, both manifests, the workspace declaration / labels and exit codes are preserved ([repro/workspace-on-v4/](repro/workspace-on-v4/)).

## 2. The lifecycle contract (defined before the edit)

[LIFECYCLE-CONTRACT.md](LIFECYCLE-CONTRACT.md), `runner-lifecycle-2026-10-01.v1`: daily-cap deferral and genuine process interruption resume with the existing durable allowances and the same binding; a critical-acceptance stop is terminal for ordinary resume, and so is a completed three-consecutive-provider-failure stop; plain `--resume` is never approval to clear a stop, retry a rejected arm or reset the failure breaker. A terminal stop is persisted the moment it is decided (`out/TERMINAL-STOP.json`, atomic, never overwritten, with the initial reason and the triggering evidence); a resume loads and validates persisted state — the stop file, the manifest's stop, a v4 manifest's terminal reason, or an **offline reconstruction** by the same tripwire over the projects already read — before the startup manifest write and before any call can leave, and returns the preserved stopped result with zero requests (exit 4, refusal recorded, lists preserved, status `stopped`). A stopped run is never relabelled `completed`. No override, approval flow, budget scope or amendment mechanism exists; reopening needs a separate explicit decision and binding.

## 3. Correction (harness v4.1, [harness-v4.1/arm_ev.py](harness-v4.1/arm_ev.py), runner `arm-ev-2026-10-01.v4.1`)

The recorded edits ([harness-v4.1/patch_lifecycle.py](harness-v4.1/patch_lifecycle.py), [`_2.py`](harness-v4.1/patch_lifecycle_2.py)) were applied to a copy of review22's frozen v4; the scoring files (`coverage_v4.py`, `score_arms_v4.py`), the scheduler and the r16.1 allowance module are byte-identical to the frozen v4 ([bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json)). The scripted provider gained a failure mode (`PILOT_DRY_FAIL_FROM` / `_COUNT`) and the runner two dry-only kill points around the persistence boundary; both exist only under `PILOT_DRY=1`.

## 4. Offline validation through the actual runner ([lifecycle-evidence/LIFECYCLE.json](lifecycle-evidence/LIFECYCLE.json); regressions [harness-v4.1/test_lifecycle_v4_1.py](harness-v4.1/test_lifecycle_v4_1.py), **5 passed**)

| Scenario | What happened (v4.1) |
|---|---|
| T1 critical stop with pending work, then plain `--resume` | initial: stopped after EP-16830 (12 requests, 1 critical, EP-17428 not attempted, stop file `critical_acceptance`); resume: **exit 4, zero sends** (io unchanged at 12), the same reason / evidence / time / pid in the stop file and manifest, projects / not-attempted / tripwire lists identical, status `stopped`, refusal recorded with `requests_sent: 0`, same declaration / arm / tag / allowance key |
| T2 repeated resume | still exit 4, zero sends, unchanged reason and evidence; two refusal records |
| T3 terminal stop after the last project (labels disagree only for EP-17428) | initial: EP-16830 read, EP-17428 read, critical → `stopped` with no remaining project; resume: exit 4, still `stopped`, zero sends — never relabelled `completed` |
| T4 three consecutive scripted provider failures | 3 requests, all `transport` failures → terminal stop `provider_failures` with the three failed requests as evidence, EP-17428 not attempted; resume: exit 4, zero sends, reason unchanged. **T4b** one scripted failure then normal answers: no stop, run `completed`, ordinary resume not refused (exit 0) — a single failed request is not terminal |
| T5a killed after the stop was decided but **before** the stop file (exit 98) | state indeterminate (no stop file, manifest without the stop or the project); resume **reconstructs the stop offline** from the saved evidence of EP-16830 (`reconstructed: true`, critical evidence kept) and refuses: exit 4, zero sends, io still 12 |
| T5b killed **after** the stop file, before the manifest (exit 98) | the file exists, the manifest does not know; resume refuses on the file: same stop, exit 4, zero sends |
| T6 positive controls — the eight R22 scenarios rerun with the v4.1 runner ([runner-evidence/](runner-evidence/), **8 passed**) | S7 daily deferral (needs 24, capacity 10, zero requests) resumes and completes on the next simulated window; S2 kill / resume uses only the remaining durable allowance (12 cap, interrupted attempt visible, completed document skipped); S1, S3–S6, S8 unchanged |

The reviewer's own probe on v4.1 ([repro/on-v4.1/](repro/on-v4.1/)): initial stopped after EP-16830 with 12 requests and 1 critical; plain `--resume` exit 4, **zero requests**, the same stop reason, `not_attempted` still `17428` — **3 passed**.

## 5. Freeze, tests, package

Frozen hashes: [bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json) (changed vs v4: `arm_ev.py`, `dry_provider2.py`, `runner_probes.py`, `test_runner_v4.py`; new: the lifecycle probes / tests / patches and the packaging scripts). Tests: scoring **19 passed** (unchanged scorer), runner **8 passed**, lifecycle **5 passed**; reviewer's regressions **1 failed / 2 passed on v4** and **3 passed on v4.1**. Not rerun: application suites (no application change), r16.1 controls and the H-06 replay (unchanged since review22). Package check: [evidence/PACKAGE-CHECK.json](evidence/PACKAGE-CHECK.json) (manifest, links, trees, frozen hashes, reviewer files, earlier packages and labels unchanged, tests, evidence flags, live ledger 128 settled with no r21 / r22 / r23 live scope).

## 6. Honest limits

- Evidence is synthetic (scripted provider, synthetic sheets and labels): it proves the lifecycle and accounting contracts, not extraction accuracy.
- The offline reconstruction (T5a) depends on the saved evidence being committed by the reader before the stop was decided (it is: each document's row is committed as it is read); a crash before that commit leaves an ordinary interrupted document, which is resumable by design.
- A legacy v4 run record without a stop file is recognised by its terminal reason string; the two terminal kinds are enumerated in the runner.
- Nothing here changes labels, thresholds, prompts, matching policies, the R19-accepted corrections, the ROI decision-coverage loss, or the M2 status.

**Submitted for independent review; not self-approved. The four-arm model experiment was not started.**
