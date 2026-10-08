# M2 closure decision — 2026-10-06 (orchestrator: Fable 5.1, under owner mission A-11)

**Verdict: M2 CHANGES STILL REQUIRED. M3 not started. No M3 handoff.**
Independent reviews supporting this verdict: Verification 41 (v2 declaration, VERIFIED WITH CONDITIONS) and Verification 42 (corrected harness `review42/` and declaration v3, **ORCH-10 VERIFIED**, 0 blockers, 0 majors, 1 minor). Both are AI reviews by fresh Claude Opus 5.5 agents, never human sign-off. Reference sets are independently AI-reviewed (Claude agents), not human-signed.

Governance records (append-only, outside the repository): `C:\Users\moham\.codex\visualizations\2026\09\27\01a0e218-6014-77a0-be80-501dcc922424\master-roadmap\orchestrator\` — `DECISION-LEDGER.md` (ORCH-027 … ORCH-032), `AUTHORITY-REGISTER.md` (A-11), `M2-ACCEPTANCE-MATRIX.md`, `M2-CLOSURE-JOURNAL.md`, `OWNER-DECISION-CARD-M2.md`, `RUNBOOK-ADDENDUM-R42.md`, `surveys\`, `tasks\`; reviews in `..\reviews\M2-review-41\` and `M2-review-42\`. Copies of the matrix and the decision card are beside this file.

## 1. The acceptance matrix (summary; full table in `M2-ACCEPTANCE-MATRIX.md`)

| Gate | Requirement | Status | What closes it |
|---|---|---|---|
| G1/G2 | known defects fixed with regression tests | partly: P-01…P-14, B-01…B-03, H-02/04/05, R29 fixes 1–4 fixed and tested; open: H-01 residual, H-03, H-06 residual, B-04 residual, unread decision marks, G-M2-1/1b | engineering after the R32 result (frozen identities preserved until then); H-03 needs an owner eligibility decision |
| G3/G7/G11/G12 | critical fields correct on the Golden set; ≥ 98 % accepted precision, ≥ 90 % recovery, ≥ 12 matched per field; no unsafe association | not measured on fresh data; exposed-corpus results only; four-arm final INCONCLUSIVE | the R32 v3 fresh validation (owner budget authorization D2); dates and sections need a separate scope or descoping (D7) |
| G4 | no silent row/page/document loss | accepted piece by piece (Reviews 01–13, 23–26, 40) | the final acceptance review states it for the accepted tree |
| G5/G13 | measured benefit, cost/latency/review burden, default selected by the predeclared gate | none; "no default" | R32 result, then an owner selection |
| G6 | expanded sealed pilot (30 projects / 1,200 documents / 40 sheets) | not run; still required by the policy and the roadmap; never descoped | owner decision D5 |
| G8 | BOQ part number / quantity / same-row | deterministic critical errors reduced (pilot 4, holdout 3); H-06 control complete; no model-enabled BOQ accuracy result | owner decision D6 |
| G9 | manually verified Golden cases | none human-signed; amendment R32-01 is run-specific | owner decision D8 |
| G10 | policy §10 artifacts incl. promotion/rollback proposal | items 1–6, 8 exist; 7 absent | after an ELIGIBLE result |
| G14 | backward-compatibility on the accepted tree | candidate `a8aaced` full suite 1,824 pass / 35 skip / 2 fail = baseline's 2 failures (Review 30); **but the merged application contains none of the reviewed M2 corrections** (see §4) | owner decision D10, then the port and its compatibility review |
| G15/G16 | open blockers closed or descoped; final independent acceptance | open | after the above |
| G17 | error taxonomy | met | — |

Net: 1 of 17 gates met. The 24-document R32 validation, even if every gate passed, would cover identity, revision and decision on six projects and would leave G3 (dates/sections), G6, G8, G9, G10, G13, G14, G15 and G16 open.

## 2. Final package and code hashes (sha256)

| Item | Hash |
|---|---|
| Declaration v3 `ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3\FRESH-VALIDATION-DECLARATION-R32-V3.json` (frozen, NOT authorized) | `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40` |
| `declaration-r32-v3\evidence\EVIDENCE-MANIFEST.json` (277 files) | `a2df60dca2dfba5ebaff8bdc4b73ef76926cbecd7fd58c8916885e7e709a1a24` |
| `review42\evidence\EVIDENCE-MANIFEST.json` (126 files) | `ab2bc40d6ab5a45b0f7dca710f188b1e9f2a9cb4da80118177c7b1df9658e782` |
| `review42\BINDING-MANIFEST-R42.json` (319 bindings) | `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c` |
| Superseded v2 declaration (never to be run) | `f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af` |
| `docs\milestones\M2\M2-REVIEW-RESPONSE.md` (append-only; one new entry) | `2ccfcd36a233f504b58d0e6b542567fe8218209db6918e26d28d1f9658f3686f` |
| Baseline tree `C:\t\iso\frozen-r12` (clean) | commit `3d5607d99fcebf08ac45f5df937ad615ecc16fb3` |
| Candidate tree `C:\t\iso\cand-r29` (clean) | commit `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` |
| Pinned CLI `…\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe`, `2.1.263 (Claude Code)` | `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03` |
| Bound interpreter `ep-platform\backend\venv\Scripts\python.exe` (3.12.10; 57 distributions in `INTERPRETER-CHECK.json` `96639af9…c504`) | `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14` |
| Policy / amendment / roadmap | `7efa891b…4f47` / `815d43fd…5de6` / `f6dba0b2…4c86` |
| Verification 42 `INDEPENDENT-VERIFICATION.md` | `b0f4ad9998266434a235a37fe7fe307dde243e6e45c9fc2c19d20a2574899b30` |

Git: the two new package folders and the response-ledger append are **uncommitted** in `ep-platform` (branch `merge/candidate`, HEAD `7ecd2d3`); the working tree also carries unrelated FA-interfaces changes. Committing is the owner's call; if done, stage only `docs/milestones/M2/real-project-pilot/review42`, `.../declaration-r32-v3` and `docs/milestones/M2/M2-REVIEW-RESPONSE.md`.

## 3. Reproducible commands (read-only; cmd.exe; nothing dispatches)

```cmd
set PKG=G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot\declaration-r32-v3
set PY=G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe
certutil -hashfile "%PKG%\FRESH-VALIDATION-DECLARATION-R32-V3.json" SHA256
cd /d "%PKG%\scripts"
"%PY%" -B preflight_r42.py
"%PY%" -B create_scope_r42.py preview
"%PY%" -B run_tests_r42.py C:\t\r2x\r42-sandbox\pytest-<new>
```
The owner's dispatch sequence (only after D1 and D2): `declaration-r32-v3\RUNBOOK.md` §1.1 → `RUNBOOK-ADDENDUM-R42.md` §1 (`pip freeze` equality) → §1.2 probe or acceptance of UNRESOLVED identity → §2.1–2.2 token, digest, RUN file → the orchestrator's `verify_run_file` → the owner's authorization message naming the frozen hash, digest, RUN hash, paths, scope and limits → §2.5 authorization file (per invocation, or `--invocations 3`) → §3 `create_scope_r42.py create` → §5.1 `runner_r32.py run --mode live …` → deferral/resume per §5.3 at `retry_at_full`.

## 4. Request and token accounting; unresolved limitations

AI ledger `C:\t\r2x\ledger\r2x-ledger.sqlite` (read-only), unchanged by this task: 483 entries over 17 scopes, 0 limit amendments; 462 ok, 13 timeouts, 8 breaker refusals; actual input tokens 5,311,131 (3,140,200 cached), output 779,765; 13 entries with unknown usage; last entry 2026-10-01T18:17Z. No request was made under A-11 (0 CLI invocations by the orchestrator, the implementer or the verifier). The R32 v3 run, if authorized: ceiling 556 requests (B 240 / C 240 / R 40 / P 36), 16.3 M input / 3.26 M output tokens, 7 days; planning estimate 145 requests (about 1.71 M / 0.26 M tokens), structural maximum 364; cost unknown and never zero (subscription).

Unresolved limitations: served-model identity UNRESOLVED offline; the venv's packages are an owner precondition, not a runtime check (R42-09); isolation compares path text; the live path is shown only live-shaped; the two unsupported-format controls are absent; labels are AI-reviewed from the same model family; results can depend on the number of invocations (R40-13); the expanded sealed pilot, the BOQ track, dates and sections and human Golden truth are outside R32.

## 5. Integration status in the merged installation

- The experiment is **not** integrated and must not be: the merged application's `backend\app` tree at the Desktop snapshot `445ee27` is byte-identical to the frozen trees' root commit `c692f1e` (tree `4c768e91…`), i.e. the state **before** Reviews 06–29. The reviewed corrections (usable-read preservation, anchor reconstruction, uncertain-reference guard, evidence stage, the four R29 switches, `evidence_reader.py`, `ledger.py`, titleblock-3, `m2_eval6.py`, 262 test functions) are absent. The merged tree diverged separately on 2026-10-05 to `parse-2026-10-05.5` / titleblock-2 with rules M2 never evaluated. Neither frozen commit is an object of the merged repository. Details: `master-roadmap\orchestrator\surveys\A2-INTEGRATION-GAP.md`.
- The merged installation's live services (API 8002 and three workers, data `data\ep_platform.db`) were never started, stopped, queried or written; the experiment's sandboxes are under `C:\t\r2x`, its lanes refuse any value under the merged installation except the bound venv, and `AI_ENABLED=false` there.
- No promotion is justified (no accuracy result exists), so no port was prepared. When justified: a 3-way port of `git diff c692f1e a8aaced` onto an isolated copy, expected conflicts in `document_control.py`, `title_block.py`, `provider.py`, `config.py`, new parser/title-block versions, the focused (652/0 reference) and full suites before/after, the R29 suites with switches off and on, and the checks of `M2-COMPATIBILITY-REPORT.md`.

## 6. The smallest concrete next action

The owner answers the decision card `OWNER-DECISION-CARD-M2.md` (D1–D11), at minimum **D1 (served-model identity) and D2 (the 556-request budget authorization for declaration `9a55fa7b…1b40`)**. On D2 = yes, the owner performs RUNBOOK §1.1, the `pip freeze` check, the two-hash procedure and the scope creation, and either runs invocation 1 or sets the token in the orchestrator's environment so the orchestrator runs it under the frozen runner. Until then nothing is dispatched; M2 stays CHANGES STILL REQUIRED and M3 does not start.
