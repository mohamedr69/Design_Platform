# Declaration summary: fresh validation R32, declaration v5 (review45 harness; frozen, NOT authorized; R44-07)

| | |
|---|---|
| **Declaration** | `PILOT/declaration-r32-v5/FRESH-VALIDATION-DECLARATION-R32-V5.json`, sha256 **`db72025b2bff28ffaf37b6605edd81cac2a0b9e17ac7f29479ca0aac157485df`**, contract `r42-live-contract-5`, declared 2026-10-08T00:31:25Z |
| **Supersedes** | v4 `e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9` (frozen 2026-10-08, never authorized, never run: condition (b) of A-13 item 3 could not be met in the review43 harness, R44-06; item 3 lapsed). Chain: v3 `9a55fa7b…1b40` (executed 2026-10-07, INVALID / INELIGIBLE, terminal), v2 `f38fb281…25af` |
| **Bound harness** | `PILOT/review45/` (`BINDING-MANIFEST-R45-HARNESS` `9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb`, 629 entries): the review43 harness plus the dry-only baseline-facts drill; Verification 45 VERIFIED WITH CONDITIONS |
| **Run identifiers** | stamp `r32-v5`; run folder `C:/t/r2x/r42-sandbox/r32-v5`; scope `m2-fresh-validation-r32-v5-2026-10-08`; RUN file and authorization file pinned in this package. **None created.** |
| **Status** | `executed: false`, `budget_approved: false`, authorization "none; owner decision pending" |
| **Reference set** | `r32-labels-reviewed-2` (`89c60e9d…b9a6`): independently AI-reviewed (Claude agents), not human-signed |
| **Standing** | M4 (historical M2) CHANGES STILL REQUIRED. M3 accepted. |

## 1. What did not change (DECLARATION-DIFF-V4-V5: protected values all unchanged)

Every number and rule of v4 (and v3): the arms and switches, the task kinds, the run set (`9058f3d6…7ce8`, 24 documents), the truth (`4e237a4e…e064`), the reference set, the trees (frozen-r13 `7ec3d2cf`, cand-r30n `436daef2`), the parent budget 556 / 16,300,000 / 3,260,000 / 604,800 s, the lane allowances B 240 / C 240 / R 40 / P 36, the project window 60 per 86,400 s, the thresholds, the application limits "96" / "600" / "12" / "120", the decision coverage gate C ≥ B only (a change from plan v2, A-10) with C ≥ R a mandatory diagnostic, `resume_policy` `full`, the stop rules, the concentration results, the model pins `claude-sonnet-5` / `claude-opus-5` / `claude-code`, the CLI line `2.1.263 (Claude Code)`, the interpreter and the disk floor.

Leaf counts v4 → v5: 1,281 unchanged, 41 re-pointed (`review43/scripts/harness-r32` → `review45/scripts/harness-r32`), 2 rebound (`lane_r32`, `runner_r32`), 69 changed, 92 added, 12 removed. Top level: 66 unchanged, 4 re-pointed / rebound only, 25 changed, 1 added, 0 removed.

## 2. What changed (each item answers task R43-44 / Verification 45)

| Item | v5 | Answers |
|---|---|---|
| Harness rebind | `binding_manifest_sha256` 9af8e07a…; `isolation` harness = `PILOT/review45/scripts/harness-r32`; `harness.*` (package, manifests, package check, accepted by Verification 45, module hashes incl. the new `drill_r45`); `authorization.invocation` (run command, working directory, harness copy); `request_path_coverage` (review45 junit; the drill files) | V45 §4, §5 item 2 |
| Identifiers | stamp, run folder, scope, `AI_LEDGER_SCOPE`, pinned authorization and RUN paths | new declaration |
| Supersedes | v4 (and its manifest) plus the chain; the review43 binding superseded by the review45 manifest | R43-44 |
| First-read disclosure | corrected: F009/F020/F030 read offline **5** times (2 by R43-42, 2 by Verification 45, 1 by R43-44 on v5's bindings); v3's live B read 15 of 24 documents (14 of the other 21) with one model form reading (F035); only F037, F033, F006, F015, F032, F016, F018 never read | R45-06, R45-07, R34-18 |
| Drill disclosures | the drill, its criterion `8b183053…d918`, its result (PASS, 0 criticals, 0 requests), its limits, pre-run exposure | V45 §4, R44-12 |
| AI-on limit | for F009 and F020 the model's later form reading can set reference, revision or status; the drill does not rehearse it | R45-08 |
| Test exception | R43V-05 carried (R45-10) | R45-10 |
| A-13 item 3 | carried verbatim as history; lapsed; a fresh D1/D2 is required | R44-13 |
| `owner_decision_required` | exactly the six check-8 steps of Verification 45 | V45 §5 |

## 3. Evidence (0 model requests throughout)

- `validate_declaration`: the in-memory copy with a dummy digest PASSES; the file as written is REFUSED ("binds no owner token digest").
- Preflight steps 1–7 from byte copies against review45: **73/73** probes as expected; binding (629 files), bounds, lanes B/C/R/P (drawings AI off, isolation), interpreter, CLI file and disk pass (`dry-run/PREFLIGHT-RESULTS.json`). Steps 8–12 not run.
- Dry exercise: the single 24-document run FINISHED (readers `none`; B's tripwire inputs and rows byte-equal to v4's).
- Demonstrations 8/8 (`rehearsal/demos/DEMOS-R42.json`).
- The review45 drill reproduced on v5's bindings: PASS (F009 19, F020 21, F030 18 facts; 0 criticals; 0 requests; facts equal to the review45 evidence run) (`evidence/drill-v5/`).
- AI ledger 484 / 18 / 0 before and after; pip freeze `bd424a5c…bf7f` before and after.

## 4. Owner decisions (none taken by task R43-44)

1. Option 1 and the restated condition (b) as a new register entry (Verification 45 §5 item 1), knowing the R45-08 limit.
2. Verification 46 of this package.
3. **D1:** served-model identity UNRESOLVED offline — run the probe (RUNBOOK-R32-V5 §1.3) or accept UNRESOLVED identity with the fail-closed runtime check and its two limits.
4. **D2:** the budget authorization (`BUDGET-CARD-V6.md`): 556 requests, 16.3 M input / 3.26 M output tokens, 7 days, the scope with exact limits, the first invocation; naming `db72025b…85df`, the digest, the independently verified RUN hash and the absolute paths. Optionally one approval for all planned resumptions (one file, 3 nonces).
5. The pip-freeze precondition before invocation 1 and every resume; the scope created by the owner alone (`SCOPE-CREATION-COMMAND.md`).

## 5. Statuses, stated separately

- **Declaration readiness:** delivered for Verification 46; not self-approved.
- **Accuracy:** none claimed; no prediction exists. The drill is a deterministic baseline reading on 3 of 24 documents, AI off.
- **Label truth:** AI-reviewed (Claude agents), not human-signed.
- **Permissions and budget:** none. No scope, token, RUN, authorization, nonce or dispatch exists or is authorized. v4 stays frozen and unauthorized.
- **M4 (historical M2):** CHANGES STILL REQUIRED.
