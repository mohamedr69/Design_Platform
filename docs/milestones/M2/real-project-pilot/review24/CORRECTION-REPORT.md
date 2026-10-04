# Review 24 correction: provider-failure stop recovery (2026-10-01)

**Scope:** R24-01 only — three completed provider failures were forgotten when the process was interrupted after the stop was decided but before the stop file was written. Harness runner and tests only, offline: **no provider or model request**; no live schedule, budget reset / increase, new live scope, H-06 rerun, sealed-project access or label edit; **the 688-request proposal remains unapproved**; no application change (`719e8de` / `3d5607d` clean). R22-01 / R22-02 (scorer byte-identical) and the R23 lifecycle paths are preserved. Contract: [LIFECYCLE-CONTRACT.md](LIFECYCLE-CONTRACT.md) (v2). Files: [CHANGE-MAP.md](CHANGE-MAP.md). Commands / exit codes: [COMMANDS.md](COMMANDS.md). Status: [STATUS.md](STATUS.md). **Submission readiness is not milestone acceptance: M2 remains CHANGES STILL REQUIRED.**

## 1. Reproduction on the submitted v4.1 runner (unchanged)

The reviewer's `provider_boundary_probe.py`, its helper `lifecycle_probes_adapted.py` and `test_provider_boundary.py` were staged **byte-identical** beside the unchanged v4.1 runner files, with a new private scenario root ([repro/run_provider_probe.py](repro/run_provider_probe.py)); agreeing synthetic labels, scripted provider only.

| Case (v4.1) | Initial run | Plain resume |
|---|---|---|
| `PILOT_DRY_FAIL_FROM=1` + `KILL_AT_STOP=before_file` | exit 98; 3 recorded `transport` outcomes; no stop file, no manifest stop | **exit 0, 16 new scripted requests, `completed`, no stop** |
| same + `after_file` (control) | exit 98; stop file present | exit 4, 0 new requests, provider stop preserved |

Regressions: **1 failed, 2 controls passed** ([repro/on-v4.1/](repro/on-v4.1/); logs, before / after snapshots and the scenario roots under [repro/scenarios-on-v4.1/](repro/scenarios-on-v4.1/)). The before-file case is a *reached* terminal decision (exit 98 is raised inside `persist_terminal_stop`, after the third failure was counted), not an ordinary interrupted request.

## 2. Correction (harness v4.2)

A small durable **provider-outcome journal** (`out/PROVIDER-OUTCOMES.jsonl`, [harness-v4.2/provider_journal.py](harness-v4.2/provider_journal.py)) is written by the runner: a header with the run binding before any request can leave; an `attempt` before each call that may dispatch; its `result` right after the call returns and **before** the failure-streak decision — each line fsync'd. So a decided provider stop always has its three failures on disk, and an attempt without a result is an unresolved in-flight request. On `--resume` (after the v1 stop-file / manifest / legacy checks, before the critical reconstruction, the startup write and any dispatch), the journal is validated: a trailing streak of ≥ 3 completed failures reconstructs the provider stop (same reason, `reconstructed: true`, the three journalled failures as evidence) and refuses with zero requests (exit 4); an unusable, foreign or missing journal (when the run already recorded work) refuses with zero requests (exit 5) and writes no stop. Otherwise the durable streak is carried into the process, so a restart no longer resets the provider breaker (a deliberate clarification, explained in the contract). The ledger was not used for recovery because it is bound only to the arm scope, not to the sandbox, tag or document; it corroborates the evidence (P2: three settled `transport` entries).

The edits are recorded ([patch_provider_recovery.py](harness-v4.2/patch_provider_recovery.py), [`_2.py`](harness-v4.2/patch_provider_recovery_2.py)) and were applied to a copy of review23's frozen v4.1. The harness was **frozen before the final validation** ([bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json); runner `arm-ev-2026-10-01.v4.2`, contract `runner-lifecycle-2026-10-01.v2`, journal `provider-outcomes.v1`).

## 3. Offline validation through the actual runner (frozen v4.2, scripted provider, isolated roots)

Critical-stop and provider-stop outcomes are reported separately; one path passing is not evidence for the other.

**Critical-acceptance stops** (lifecycle scenarios rerun with v4.2, [lifecycle-evidence/](lifecycle-evidence/); regressions 5 passed): T1 ordinary resume — exit 4, 0 sends, stop and lists preserved; T2 repeated resume — unchanged; T3 stop after the last project — stays `stopped`; T5a killed before the stop file — reconstructed offline from saved evidence, refused, 0 sends; T5b killed after the file — refused on the file.

**Provider-failure stops** ([boundary-evidence/BOUNDARY.json](boundary-evidence/BOUNDARY.json); regressions 7 passed; plus lifecycle T4 / T4b):

| Scenario | Result |
|---|---|
| P1 ordinary (stop persisted in-process) | resume exit 4, 0 new sends, stop file unchanged |
| **P2 killed before the stop file** | journal: 3 `failure` results, none unresolved; resume **exit 4, 0 new sends**, status `stopped`, reason `stop: three consecutive provider failures`, `reconstructed: true`, evidence = journal seqs 1–3 (`transport`); ledger corroborates 3 settled `transport` |
| P3 killed after the stop file | resume exit 4 on the file, 0 new sends, original stop (`reconstructed: false`) |
| P4 repeated resume of P2's recovered stop | exit 4, 0 sends; stop file bytes, allowance charges, journal and `io.jsonl` unchanged; first reason and lists kept; two refusal records |
| P5a two completed failures + one unresolved request (killed in flight) | resume carries streak 2, the unresolved request counted as neither; the run continues and completes (16 requests), no stop; the in-flight request stays charged |
| P5b a success between failures (F F ok F F ok …) | no stop; a plain resume is ordinary (streak 0, no reconstruction, 0 requests needed) |
| P5c F F [in flight] → restart → first resumed request F | terminal in the resumed process (`reconstructed: false`), evidence seqs 1, 2 (first pid) and 4 (second pid); a further resume refuses — plain resume does not reset the breaker |
| P6a torn last record / P6b journal deleted / P6c journal bound to another tag / P6d a result without its attempt | each: **exit 5**, 0 sends, no stop fabricated, run record / io / charges / journal unchanged, one refusal with `requests_sent: 0` |
| T4 / T4b (lifecycle) | three failures terminal and not clearable; a single failure is not terminal |

**Controls:** the eight R22 runner scenarios rerun with v4.2 (**8 passed**): kill / resume uses only the remaining durable allowance (S2), cache hits charge nothing (S5), daily deferral resumes when eligible (S7), S1 / S3 / S4 / S6 / S8 unchanged. Their journals show budget refusals (S2) and ≥ 20 cache hits (S5) recorded and not counted (streak 0) — checked by a boundary regression. Journal unit tests **23 passed** (every streak rule and fail-closed branch). Scorer tests **19 passed** (unchanged scorer).

**Reviewer's probe on v4.2** ([repro/on-v4.2/](repro/on-v4.2/)): before-file resume exit 4, **0 new requests**, `stopped`; after-file control unchanged — **3 passed**.

## 4. Package

[evidence/PACKAGE-CHECK.json](evidence/PACKAGE-CHECK.json): manifest complete, links, clean trees, workspace and packaged harness equal to the hashes frozen before validation, scorer equal to review22's v4, reviewer files unchanged, earlier packages (review13 … review23) and labels unchanged, test counts, separate critical / provider evidence flags, runner controls, reviewer-probe before / after, live ledger 128 settled with no r21–r24 live scope.

## 5. Honest limits

- The evidence is synthetic (scripted provider, synthetic sheets): it proves the lifecycle and accounting contracts, not extraction accuracy or real provider behaviour.
- A stop reconstructed at the boundary leaves the run's project lists as last persisted (in P2 the killed process had written no project entry, so EP-17428 is not listed as `not_attempted`); the refusal adds no fabricated history, and the status is `stopped`.
- A sandbox without a journal that already recorded work (any run started by v4.1 or earlier) refuses with exit 5; no such live run exists.
- A torn final record is treated as indeterminate even when it would have been harmless — fail closed by design.
- Carrying the streak across a restart is a semantic clarification: under v4.1 a restart reset the provider breaker; v2 makes plain resume unable to do that. It is disclosed for the reviewer's judgment.

**Ready for independent review; not self-approved. The four-arm model experiment was not started.**
