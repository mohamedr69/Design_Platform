# AI policy remediation: central, fail-closed project AI-policy enforcement (ORCH-053)

Task card `MR/orchestrator/tasks/ORCH-053-TASK.md` (label U2-AI-POLICY-REMEDIATION; owner decisions A-18 item 3, A-19 item 4). Defect: ORCH-051 `MR/reviews/U2-live-control-checks/` LC-02..LC-13. Contract clauses: M3 B-04 (the project AI policy applies to every path that sends project content to an external provider), P-10 (no model confidence grants authority; untouched, and refusals never create AI rows), P-14 (shared bytes do not share project approval: a stored answer is not served to a blocked project).

Isolated implementation and tests only: branch `task/ai-policy-enforcement` from `roadmap/u2` at `94af35aa558c705f290d483cb10d6bd0b8ae34dd` (ccc92ed code lineage), worktree `wt-sec`. No merge, no push, no deployment, no `.env` or `ai_policy` change, no provider request, no `claude` CLI, no network, no `pip install`. While this ran, `roadmap/u2` advanced (the M6 merge 4c6cff0, then c715c35); this branch is not rebased on it (see Open items).

## Design

- **One rule, two questions** (`backend/app/ai/project_policy.py`). `allowed(project)` keeps its read-model meaning (None counts as allowed, for pages only). `require(project)` and `enforce(db, project_id, task=...)` fail closed: a request is authorised only for a project row that exists with `ai_policy == "allowed"`; missing, unknown (no row, or not a positive int), ambiguous (any other value) and blocked raise `AiPolicyRefused(reason)` (a subclass of the old `AiBlocked`). `enforce` re-reads the policy from the database on every call and takes the stricter of that and the session's own copy. Every refusal writes an `ai_usage` audit row: task, project (NULL when unknown, the id then named in `model`), `outcome = policy_<reason>`, model `none`, no tokens, no content; `budget.calls_today` and the FA per-day counts exclude these rows (`not_a_refusal`).
- **Central path**: `assist._call` opens with `project_policy.enforce(session.db, session.project_id, task=task)`, before the parts are hashed, scanned, looked up in the cache or put into an `AiRequest`. Every `assist.call_task` caller (review, FA, preparation, chat, classification, compliance, verification, sheet and submittal readers, sample requests, details check) is therefore checked per call, per project; a stored answer is never served to a blocked project.
- **Direct-provider paths**: `extraction.pipeline.ask` (per call), `ai_symbol_review._call` (per call) and per batch, `drawing_ai_review._ask` (per call), the scoped CLI (preflight refuses before the provider factory, so `--live`'s `_build` is never reached). Exempt, with reasons in the guard test: `scripts/ai_selftest.py` (synthetic cell) and `evaluation.run_case` (operator harness, no project on a case; open item).
- **Entry points**: refused before any work (routes answer 409 with the reason, nothing queued; jobs fail with the reason through `ReadError`, nothing changed).
- **Mid-run**: the review re-checks per look and stops the run; classification and the IFC symbol review re-check per batch and stop; FA, preparation and the rest are refused per call.

## Changes (file:line on the branch)

| Where | What |
|---|---|
| `app/ai/project_policy.py:58-166` | `AiPolicyRefused`, `refusal`, `require` (fail closed), `refusal_for` (DB re-read), `audit`, `enforce`, `check`; module docstring documents `allowed` vs `require` |
| `app/compliance/assist.py:279` | central gate, first statement of `_call` |
| `app/ai/budget.py:126-142` | `not_a_refusal`; `calls_today(..., tasks=)` excludes refusals |
| `app/routers/drawing_review.py:80` | review start: 409 before queueing |
| `app/review/service.py:65-80, 169, 245-253, 712` | daily caps per feature; `run` gate before plotting; stop on refusal mid-run; per-look gate in `_ask` |
| `app/ifc/services/runners.py` | refusals become a plain job failure (review, preparation, FA run, FA retry) |
| `app/routers/fa_interfaces.py:114, 193` | FA run and Retry review: 409 before queueing |
| `app/interfaces/workflow.py:721, 969` | `run_workflow`, `run_retry` gates; orchestrator day count excludes refusals |
| `app/interfaces/visual.py:245, 279` | `visual.check` gate; own daily cap |
| `app/interfaces/findings.py:699` | `review_all` gate; day count excludes refusals |
| `app/routers/redesign.py:104`, `app/redesign/service.py:1298, 1375` | preparation plan: route 409, `plan` gate, own daily cap |
| `app/review/scoped.py:93` | scoped preflight: `Refused` before any provider is built |
| `app/ifc/services/ai_symbol_review.py:295, 325, 383` | per-call gate, entry check (as if AI were off), per-batch re-check |
| `app/services/drawing_ai_review.py:140`, `app/services/shop_drawings.py:603` | drawings AI review: per call and at entry |
| `app/ai/verification.py:1308` | DRF read outside a job (project creation): refused, `missing` |
| `app/extraction/pipeline.py:201` | extraction call gated per call |
| `app/services/document_classification_ai.py:421, 447` | run-level refusal audited; policy re-read before every batch (the only change to that file; `document_classification.py` untouched) |
| `app/services/drawings_chat.py:340` | the existing refusal now audited |
| `app/core/config.py:458-460` | `DRAWING_REVIEW_/FA_VISUAL_/PREP_MAX_CALLS_PER_PROJECT_PER_DAY` (600 each; owner sets) |
| `app/main.py` `/health` | flags gain chat, classification, IFC symbol/visual, drawings AI review, assistant and verify-auto switches; new `ai` block: provider, disabled tasks, `policy_enforcement: fail_closed`, every per-project daily cap |

Tests: new `tests/test_ai_policy_guard.py` (static guard, 6), `tests/test_ai_policy_enforcement.py` (27, including the forced-blocked harness), `tests/ai_policy_harness.py` (plugin). Changed, because a request naming no project is now refused, `visual.check` with no database now fails closed, or `/health` grew: `test_provider_honesty.py` (2 tests name an allowed project), `test_ai_assist.py` (2), `test_ai_evaluation.py` (2), `test_render_bounds.py` (stand-in allowed project), `test_worker_runtime.py` (the flag set). No assertion on behaviour was weakened.

## Results

Details in `evidence/ai-policy-remediation/README.md`.

- New tests: 33 (guard 6, enforcement 27), all pass on the branch; on the base the guard fails 4 of 6 and the enforcement module cannot import (the API it tests does not exist).
- Forced-blocked harness (301 tests, 19 modules): base 403 application-built requests (335 image parts) and 49 scripted-provider inputs on blocked projects; branch 0 and 0; control 469 and 110. Real dispatches of application requests, `claude` processes and outbound sockets: 0 throughout. Mid-run: review stops at the next look; classification at the next batch; the IFC symbol review at the next batch; everything else per call.
- Full suite: base 1926 / 1890 passed / 1 failed / 35 skipped, identical by name to ORCH-047 (1926 / 1890 / 1 / 35); branch 1959 / 1923 / 1 / 35 (the same pre-existing `test_proposed_materials` failure), confirmed by a clean final run on commit 8a47d7c (`full-suite-final.*`): no test changed state.

## Open items

1. Not rebased on `roadmap/u2` (now c715c35, M6 merged meanwhile). A dry-run `git merge-tree` against it is clean; both sides touch `config.py` and `document_classification_ai.py` (`evidence/ai-policy-remediation/merge-check.txt`). The suites should be run again on the merged tree before acceptance.
2. The project-creation DRF read and resolve-time suggestions are now refused (no project exists yet): the engineer fills the form, or the AI check runs once the project exists and is allowed. Owner may want a creation-time policy choice.
3. Blocked projects now get no review, FA workflow or preparation plan at all, including the preparation's deterministic placement (the owner's interim containment rule); a deterministic-only mode for blocked projects is a possible later option.
4. `evaluation.run_case` (operator harness) cannot be gated per project: cases carry no project. `cases_from_reviews` should exclude blocked projects.
5. Daily-cap defaults (600/600/600) are placeholders for the owner.
6. Live deployment needs separate owner approval and a restart; nothing here changes the running platform.
