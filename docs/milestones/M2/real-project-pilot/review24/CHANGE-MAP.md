# Change map — Review 24 correction (provider-failure stop recovery, harness v4.2)

**Application code: no change.** Frozen R21 candidate `719e8de661b8b10427ef6cff5d2d277a53b64dc6` and accepted baseline `3d5607d` untouched and clean ([bindings/SOURCE-BINDINGS.json](bindings/SOURCE-BINDINGS.json)). Labels, thresholds, prompts, matching policies, the scorer (`coverage_v4.py`, `score_arms_v4.py`, byte-identical to review22's frozen v4), the scheduler and the r16.1 durable-allowance module are unchanged. The critical-stop paths of v4.1 are unchanged. Frozen hashes, written **before** the final validation: [bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json).

| File (`harness-v4.2/`) | Change | Why |
|---|---|---|
| `provider_journal.py` (new) | The provider-outcome journal `provider-outcomes.v1`: writer (`header` / `attempt` / `result`, each line fsync'd), classification, streak computation and fail-closed validation. | R24-01: the durable, bound, ordered record from which a reached provider stop is recovered. |
| `arm_ev.py` (runner `arm-ev-2026-10-01.v4.2`, contract `runner-lifecycle-2026-10-01.v2`) | The journal header at run creation; an `attempt` before a call may leave and its `result` right after it returns, **before** the streak decision; on `--resume`, after the stop-file / manifest / legacy checks and before the critical reconstruction, the startup write and any dispatch: journal validation → a trailing streak ≥ 3 reconstructs the provider stop (same reason, `reconstructed: true`, the three journalled failures) and refuses (exit 4); an indeterminate journal, or none although the run recorded requests or charges, refuses (exit 5, no stop fabricated, run record untouched); otherwise the durable streak is carried into the process. In-process failure evidence now also carries the journal `seq` and `pid`. | R24-01; the carried streak makes plain resume unable to reset the provider breaker. |
| `dry_provider2.py` | `PILOT_DRY_FAIL_AT=i,j,…` (dry only). | A success between failures (P5b) and a failure right after a restart (P5c). |
| `lifecycle_probes.py`, `runner_probes.py` | Output roots `r24-lifecycle` / `r24-probes`; the new dry variable cleared. | The existing lifecycle scenarios and the eight runner controls rerun with v4.2. |
| `provider_boundary_probes.py`, `test_boundary_v4_2.py` (new) | The provider boundary matrix P1–P6 through the actual runner (helpers of `lifecycle_probes.py`, agreeing synthetic labels, isolated roots) and 7 regressions (including the controls' journals: cache hits and budget refusals recorded, not counted). | Required offline validation. |
| `test_provider_journal.py` (new) | 23 unit tests: streak semantics (ok resets, cache hits / budget / unresolved neutral, restart neither resets nor extends) and every fail-closed validation branch. | |
| `patch_provider_recovery.py`, `patch_provider_recovery_2.py` (new) | The recorded edits, applied to a copy of review23's frozen v4.1. | Traceability. |
| `run_r24_chain.sh`, `bindings_r24.py`, `package_r24.py`, `verify_r24_package.py`, `append_response.py` | Packaging (re-pointed / new). | |

## Reproduction of the reviewer's finding

[repro/](repro/): `run_provider_probe.py` stages the reviewer's `provider_boundary_probe.py`, `lifecycle_probes_adapted.py`, `test_provider_boundary.py` and `pytest.ini` **byte-identical** (hashes checked; reviewer folder never written to) beside the runner files of the harness under test, with a new private scenario root; no code substitution was needed. On the submitted v4.1 runner ([repro/on-v4.1/](repro/on-v4.1/)): the before-file case resumes with exit 0, **16 new scripted requests**, `completed`, no stop; the after-file control refuses — **1 failed, 2 controls passed**. On v4.2 ([repro/on-v4.2/](repro/on-v4.2/)): **3 passed**. The only staging difference for v4.2 is that its new `provider_journal.py` is copied beside the runner.

## Not done, on purpose

No override or reopening mechanism; no scorer, extraction, scheduler or allowance change; no application change or application-suite rerun; no model call; failures are never derived from labels or restart counts.
