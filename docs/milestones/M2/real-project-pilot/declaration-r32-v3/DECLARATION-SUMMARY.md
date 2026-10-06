# Declaration summary: fresh validation R32, corrected declaration v3 (ORCH-10; frozen, NOT authorized)

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v3/FRESH-VALIDATION-DECLARATION-R32-V3.json`, sha256 **`9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`**, contract `r42-live-contract-5` |
| **Supersedes** | v2 `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` (A-11: not runnable as declared -- its bindings name the absent Desktop installation and venv; never authorized, never run, never to be run) |
| **Bound harness** | `PILOT/review42/` (`BINDING-MANIFEST-R42` `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`; manifest `ab2bc40d6ab5a45b0f7dca710f188b1e9f2a9cb4da80118177c7b1df9658e782`); pending Verification 42 |
| **Status** | `executed: false`, `budget_approved: false`, authorization "none; owner decision pending" |
| **Reference set** | `r32-labels-reviewed-2` (`89c60e9d…b9a6`): reference set independently AI-reviewed (Claude agents), not human-signed |
| **Standing** | M2 CHANGES STILL REQUIRED. M3 not started. |

## 1. What did not change (DECLARATION-DIFF: protected values all unchanged: True)

Every number and rule of v2: the arms and switches, the task kinds, the run set (`9058f3d6…7ce8`, 24 documents), the truth (`4e237a4e…e064`), the reference set, the parent budget 556 / 16,300,000 / 3,260,000 / 604,800 s, the lane allowances B 240 / C 240 / R 40 / P 36, the project window 60 per 86,400 s, the thresholds, the application limits "96" / "600" / "12" / "120", **the decision coverage gate C ≥ B only -- a change from plan v2 (A-10)** with C ≥ R a mandatory diagnostic, `resume_policy` `full`, the stop rules, the concentration results, the model pins `claude-sonnet-5` / `claude-opus-5` / `claude-code` and the CLI line `2.1.263 (Claude Code)`.

## 2. What changed (ORCH-10; each item answers a finding or an owner decision)

| Item | v3 | Answers |
|---|---|---|
| Portability | every binding re-pointed to the merged installation; every bound file re-hashes equal | A-11 |
| Interpreter | bound: `G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe` (path, sha256, version) | 2.1.1 |
| CLI | pinned by absolute path, file sha256 `0b35df94c130…` and the exact line; the bundled 2.1.289 never used | 2.1.4 |
| Isolation | no lane value, setting, import path or module under the merged installation except the venv and the harness; the merged `.env` never read | 2.1.5 |
| Global provider | a fail-closed refusing provider in C, R and P; B unchanged | R40-04 (option 2) |
| Invocation order | every check (CLI file, version, disk) before the run folder; the nonce consumed only after the allowance and the capture store exist; re-entry of a folder without an allowance; resume re-checks | R41-09, R41-11 |
| Disk precondition | 2 GiB on C, enforced by the runner and the scope command, only upward | R41-10 (C1) |
| Authorization | the multi-invocation form as a **proposal** (max 3 per file); the per-invocation form unchanged | A-11 §4 |
| Stamp / folder / scope | `r32-v3` / `C:/t/r2x/r42-sandbox/r32-v3` / `m2-fresh-validation-r32-v3-2026-10-06` | new declaration |
| Statements | R41-12 (no runbook integer-string check; the RUN-file equality is the protection) and R41-13 (the dry exercise named exactly) corrected | R41-12, R41-13 |

## 3. Evidence

- Preflight: 73 negative probes (48 carried, 25 new), all as expected: True; binding, bounds, lane environments (with isolation), interpreter, CLI file and disk pass; the runner and the guard refuse with no folder and no `--version` (`PREFLIGHT-REPORT.md`).
- Dry exercise: the single 24-document run FINISHED; six per-project runs; EP-27331 loops [2, 3] invocations; the cross-project drill 2 invocations; the CLI-version case no longer a dead-end; 0 model requests; AI ledger 483 / 17 / 0 throughout.
- review42: 549 tests, 0 failures; 8/8 scripted-provider demonstrations passed.

## 4. Owner decisions (unchanged in substance; none taken by this task)

1. **Served-model identity:** UNRESOLVED offline. Run the probe (RUNBOOK 1.2) or accept UNRESOLVED identity with the fail-closed runtime check and its two limits.
2. **R40-04:** closed in code by option 2 (A-11); the owner may note the stated residual risk (`REQUEST-PATHS.md` §5).
3. **Condition C1:** now enforced in code; the owner still stops other heavy writers before every invocation.
4. **One approval for all planned resumptions:** use it (one file, 3 nonces) or keep one file per invocation.
5. **Acknowledgements:** R40-15 (application-internal page limits leave a document COMPLETE with unread pages), R40-13 (the failed-read retry is a change from plan v2 §4), the output-token bound location, keeping the CLI at 2.1.263.
6. **Owner-confirmable values** (a change means a new hash): the per-project limit "96", the scope name, the run folder, `AI_EFFORT` low, `resume_policy` `full`, the disk floor, the bound 3.
7. **The budget authorization itself:** 556 requests, 16.3 M input / 3.26 M output tokens, 7 days, the scope with exact limits, the first invocation; it names the frozen hash `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`, the digest, the independently verified RUN hash and the absolute paths. Cost: unknown (subscription), never zero.

## 5. Statuses, stated separately

- **Correction readiness:** delivered for Verification 42; not self-approved.
- **Accuracy:** none; no prediction exists.
- **Label truth:** reference set independently AI-reviewed (Claude agents), not human-signed.
- **Permissions and budget:** eligibility only (A-06); nothing authorized.
- **M2:** CHANGES STILL REQUIRED. **M3:** not started.
