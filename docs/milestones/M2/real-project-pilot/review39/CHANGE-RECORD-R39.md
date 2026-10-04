# Change record (review39, ORCH-08C): the harness correction after Verification 39

**Task and agent**
- **Task:** ORCH-08C (orchestrator ledger ORCH-021).
- **Owner decision A-10:** relayed by the coordinator during the task (2026-10-04, about 09:52Z) and checked in `AUTHORITY-REGISTER.md` (sha256 `346597d3…ffcfd`). It amends change 5 (the gate), change 6 (model identity) and the reporting of the failed static step.
- **Agent:** R39HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High, self-reported from my system context. A fresh, isolated implementation agent; the only write-capable agent running.
- **Authorities:** A-03, A-06, A-09, A-10.
- **Dates:** 2026-10-04, from 09:00Z. Times are in `COMMANDS-AND-AUDIT-LOG.md`.

**Nature and standing**
- **Nature:** a correction package, **pending Verification 40**. Not self-approved. It authorizes nothing: no declaration (ORCH-09 writes it), no ledger scope, token, authorization file, run file, budget, provider request, default, M2 acceptance or M3.
- **Standing status:** M2 **CHANGES STILL REQUIRED**; M3 **not started**.
- **Reference set:** independently AI-reviewed (Claude agents), not human-signed (`r32-labels-reviewed-2`, `89c60e9d…b9a6`). Populations: identity 57, revision 38, decision 38.

**Base and diff**
- **Base:** `PILOT/review38/scripts/harness-r32` (50 files; review38 manifest `07c2fb78…8ce9`, binding `4c2904cd…398bcf7fee…f314d`).
  - It was byte-copied to `C:/t/iso/work/r2x/r39/harness-r38-base/` and checked against the review38 manifest (`evidence/COPY-RECORD.json`).
  - The r39 harness is `C:/t/iso/work/r2x/r39/harness-r32/` (56 files), with its package copy at `scripts/harness-r32/`.
- **Diff:** `evidence/HARNESS-DIFF-R38-R39.patch`, with per-file hashes in `evidence/HARNESS-FILES-R38-R39.json`.
  - **29 files unchanged, 21 changed, 6 new, 0 removed.**
  - Every review38 package file is listed with its review38 hash and its status in `evidence/CARRIED-FROM-REVIEW38.json`.
  - The diff was made with the Write tool, the Edit tool and the one-off patch scripts kept in `scripts/patch_*.py`.

## Files: before and after (review38 -> review39)

| File | Status | review38 sha256 | review39 sha256 | Lines |
|---|---|---|---|---|
| `allowance_r32.py` | changed | `2868e8ee1476f466a22374a11b2592bc4ae774a7c7178c8e5661ca3681c4e30c` | `6231b238654150cb1c193db4d7ef4319254a1ad885906ec7b6249e4459d55e19` | +48 / -8 |
| `lane_r32.py` | changed | `2c4aa742a6469045d7670bb1bd7450bd9d2f13ef4ab77062e7ca312e3405ecf9` | `493c0a9f248a9ceeba0ab2089a86ffed1c0bc142acdde9117012960a36088e6f` | +143 / -33 |
| `preflight_r32.py` | changed | `2bfba6a10a4c04207ce4e9139f9c0fa3c1aa21f0086c9d312df90af223619e91` | `0e59dbff5e87c1f5a9df2520bc82db7cf01b7086a314a9cefb56bcff47ea442f` | +128 / -13 |
| `project_bounds_r32.py` | changed | `33053d8ff3351424618f303d4f1c0d2d01768222bafce8f9e10706043d58efdb` | `6abbf5eb04a72e55feb3883cb50730006f2caf1224c2e0edc63a23ef978c859b` | +58 / -10 |
| `run_control_r38.py` | changed | `d226e1733be1861eecf6211906e53bbf5677731194c9fcb4458c3c69304c2715` | `d30de813c1092d46e3af940a4b0e3b03b9820c2b96c28b81ca71f40981bc42d1` | +211 / -31 |
| `run_state_r38.py` | changed | `ca47ad48fdc6fa3c14f06425db560618fac0fcefa67b843ee3b7291de8cbad35` | `5e789b05a23beae15195590ae0497739f87a493ea06acae3e8a798d054e653f8` | +136 / -18 |
| `runner_r32.py` | changed | `5475f2918bb234db87c2bdaa2241a41d9bb624c56569a54f07e15278fded9407` | `b290dd1c8ddda1b8d16117789f2f7691e792830e5a99e6b3b5a0963780027108` | +117 / -25 |
| `sandbox_ingest_r32.py` | changed | `3e0e906df9aa1d387bc8a018142e122c1c9545f54f6d2aa311718c75e45e92a6` | `8fb5c891a41bba5f86c6426fb4784ec4dd0b029cc2733893b17a23712aa56ef5` | +7 / -1 |
| `score_bcr_r32.py` | changed | `77b226e30412b4dd2d29af8932a3b748504597ba204bd00a873e6d5a4374c6d2` | `ccfc7200ca8906bc1383986cefc44b2ca134b7de5d5cfcda0268253da20f8524` | +150 / -10 |
| `score_lane_r32.py` | changed | `79530a3013cac748df7887db6ee9a038c17f0450abe438f2dcfc7bf3e272eec3` | `33a102d04bac562add88638008cd4561347225347115a3ad647b264a8a83832c` | +10 / -1 |
| `synthetic_r32.py` | changed | `cc125b2725a525e0b5629e948cfb77ca8394d13adca3d649334e8dcdf60e2cf7` | `9248cbf72e5a0033c1753bd9867591adf41de6c4ccaff9947323d16d450be65c` | +13 / -9 |
| `visibility_r38.py` | changed | `4f4066e0b073666348f4f4964c0e2344a7421bdaa09d7ce7c388e24cfa1c2e8a` | `4dcfff3777acbe4eb5c8ca861f3ea4e4e221f7242e21c1e47c93807c005cb156` | +66 / -9 |
| `r32_test_helpers.py` | changed (test helper) | `15e5d82de7fd2183b8eaf2e2911bafd3fad1e6ad09c38314112299c9f0bc8eb9` | `64c9ffcd341570d83e4cff272c16882dee0a6991537423bffc76ccdcfd7edf09` | +10 / -6 |
| `test_allowance_r32.py` | changed (test) | `354fd032a22b746862a574847eda025ad3f6d15833e2825d3c766bd9c7d664c9` | `283009dbc86f224b0a83f1b91202cdb92154e78813977b05ddd17ea4132a9fee` | +36 / -0 |
| `test_preflight_r32.py` | changed (test) | `76399aef5c15507cb4d245b3eeb8a1601b6d1ee4175fbfdc57dc9191b2bc0bfa` | `096535e0c6d75060493dfab472c8f12c9c2b21faaa15b4d7c8342953b2747ba4` | +76 / -4 |
| `test_project_bounds_r32.py` | changed (test) | `e8e54cf48e3f8f51a2eaebc19f67e064776c03a28e1e46a5a13e163b67309cad` | `8a47c286c2de3ba41f78d03cb6c809df8c4e8877df143663185f2eaefca58ac4` | +8 / -3 |
| `test_run_control_r38.py` | changed (test) | `f83ee0a65da7304eebe023dd7dd71bfba4eff2981c537a627f0b752132d2f059` | `43ef8d0e1571ed6665854b7dd79de55ca37e2e767fbf2a92941619b572e81768` | +147 / -4 |
| `test_runner_r32.py` | changed (test) | `f8b6ef55b15def470235ceac0267cf25c1699b2833675c51e0233fad015382aa` | `6897891a35cdad75d2f48fc9dea70821c6308e05dd4bd0f1aced9f90ddb82605` | +77 / -10 |
| `test_sandbox_ingest_r32.py` | changed (test; docstring path only) | `e4f67c701923b6a5e29e9db201829c55563b4cfc252abd65071ab2a9550a0b0f` | `0da051961c548f35733bf69ca3d21440f1ea3697ea0b4ad62ffaf7f5ce60d16c` | +1 / -1 |
| `test_score_bcr_r32.py` | changed (test) | `e090cf4a8d07c345a78b7e56bbb78cefb25270340f488b3f722f8badf55f5fba` | `605be29132412bc6d96a84ccd1e25df3d4ca7d52248fad41b94d2b9a5a90b942` | +63 / -0 |
| `test_visibility_r38.py` | changed (test) | `e19b7afdf600a782e5eab3f3610c655150db2b5cbcbb7ec1e997b84f170cab7f` | `47e1a4f291fb61cb2ce44d753832cd6828863d0f44250025b37886055004f6ad` | +90 / -2 |
| `drawings_ai_probe_r39.py` | new | — | `510ac22b5498850dd7851ea674d35f821df96d2fd4b080e787e309aac5d8da93` | +142 |
| `request_paths_r39.py` | new | — | `0ee519859cca6921b57f082cd8b58b91cd429521a47ecf0f7066fd7a1950aee0` | +178 |
| `resume_invocations_r39.py` | new | — | `b217b053f69213e7320469584e748d2b15679ed39d4345e0e95cfce6ebf36864` | +83 |
| `unread_pages_probe_r39.py` | new | — | `f326c362a0920e9c7f58d237d2cc41b4b5fc0525c5cb64f979f3c9166bbaf2cd` | +100 |
| `test_request_paths_r39.py` | new (test) | — | `ed1bc99df9f8b9bbdd02534602919b99d1c8a8d6eefb68dfe22de3c357707c76` | +149 |
| `test_unread_pages_r39.py` | new (test) | — | `329208bca4b4e03ccaf2eb0e9c5a28407e0b35bf31402fdfabe41e9489fb7604` | +114 |

**Carried unchanged by hash (29; review38 hash = review39 hash, listed in `evidence/HARNESS-FILES-R38-R39.json`):**
- Modules: `capture_store.py`, `concentration_r32.py`, `converter_r32.py`, `coverage_v4.py`, `dispatch_guard_r32.py`, `inputs_r32.py`, `labels_adapter_r32.py`, `lane_judge_r32.py`, `literal_compare_r32.py`, `model_identity_r38.py`, `page_relations_r38.py`, `r34_scenarios.py`, `run_set_selector_r32.py`, `sandbox_child_r32.py`, `state_check.py`, `stop_rules.py`, `tripwire_r32.py`.
- Tests: `test_capture_store.py`, `test_concentration_r32.py`, `test_converter_r32.py`, `test_dispatch_guard_r32.py`, `test_labels_adapter_r32.py`, `test_lane_judge_r32.py`, `test_literal_compare_r32.py`, `test_model_identity_r38.py`, `test_run_set_selector_r32.py`, `test_state_check.py`, `test_stop_rules.py`, `test_tripwire_r32.py`.

**Changed tests, listed as changed:** `test_allowance_r32.py`, `test_preflight_r32.py`, `test_project_bounds_r32.py`, `test_run_control_r38.py`, `test_runner_r32.py`, `test_sandbox_ingest_r32.py`, `test_score_bcr_r32.py`, `test_visibility_r38.py`.

## 1. Undeclared request paths (R39-04 major; A-09 points 1 and 3)

**(a) `REQUEST-PATHS.md` and `REQUEST-PATHS-STATIC.json`** enumerate every provider-call site reachable from each lane's entry point, with its status:

| Lane | Entry point | Declared and bounded | Disabled | Readiness only | Other |
|---|---|---|---|---|---|
| B | `document_processing.run` | `read_submittal_form` | the baseline evidence stage (`AI_EVIDENCE_VARIANT=off`); the drawings-AI review (`DRAWINGS_AI_REVIEW_ENABLED=false`) | `get_provider` checks | the ledger wrapper |
| C, R | `evidence_stage` | the evidence kinds under their switches | — | — | one static false positive, explained |
| P | harness only | — | — | — | — |

No lane reaches any other site.

**(b) Contract 4.** The declaration contract now has these keys:
- `application_env`: exactly `{"DRAWINGS_AI_REVIEW_ENABLED": "false"}`. This key and value were verified in both `config.py` files (`b4fbc07f…`, setting `drawings_ai_review_enabled`, no env prefix). Any other key or value is refused, and so is any `AI_*` key.
- `lane_task_kinds`
- `resume_policy`
- `decision_coverage_gate`

`sandbox_env()` sets the application environment. Every lane, live and dry, at every invocation and resume, verifies three things before anything is built:
- the setting in its environment;
- the setting in the application's settings;
- that `drawing_ai_review.enabled()` reports the review off.

The runner's `lane_env` refuses a configuration without the block.

**(c) The gate (belt and braces).** `GateStoreProvider` takes the lane's declared task kinds and the expected document context. The lane opens a document scope per document (`doc_scope`, `LaneRecorder.begin/end`) and clears the context afterwards.

A request is refused **before anything is served or reserved** in two cases:
- its task kind is undeclared for the lane (`undeclared_task_kind`);
- it has no context, or a context that is not the current document's (`missing_context`).

The refusal is recorded with the lane, the task, the context it carried and the context expected, in three places: the lane rows, the allowance's refusals, and `CONTRACT-BREACH.json` plus `CONTRACT-BREACH-LOG.jsonl`. It is never charged.

The run becomes INVALID:
- `ControllerR38` makes every lane terminal;
- every later request is refused with `contract_breach_invalid`;
- the runner reports INVALID and refuses every resume.

`classify()` returns `contract_breach`, never `provider_failure`, so such a request never counts toward any document's failure stop.

**(d) Proof that the drawings-AI outputs feed no measured field.**
- **Code reading:** the path writes only the shop-drawing tables and the cache. The lanes' measured inputs are `project_documents` rows only. Lanes C and R never call `shop_drawings`.
- **Dynamic test** in both trees (`drawings_ai_probe_r39.py` feed mode; `test_drawings_ai_outputs_feed_no_measured_field`; `DRAWINGS-AI-PROBE-R39.json`): the review is enabled with an answering fake. The answer is applied (the revision goes to `approved`/`ai`), and every scored `project_documents` column is unchanged. No `ProjectDocument` was flushed. **No owner decision is needed.**

**(e) `PROJECT-REQUEST-BOUNDS.json` regenerated** (version `project-bounds-r39-2026-10-04.1`, sha256 in `BINDING-MANIFEST-R39.json`).
- **EP-27331:** planning **63.0** (unchanged). Structural **160**, not the expected 154: **+6 from change 4**, because B's reconcile repeat of a failed form read is now dispatched, so B is 2 per document. 3 windows. The drawings-AI path is counted 0.
- **Alternative, stated for the record:** with the path enabled, EP-27331 would be 170. On review38's model that is 164, Verification 39's figure.
- **Compatible-limit minimum:** 84, unchanged. The derivation (`B_database` 2 per document; C and R add ≤ 12 per document) is kept.

**Tests:**
- `test_request_paths_r39.py` (11);
- `test_preflight_r32.py`: the contract-4 refusals, and `verify_application_env`;
- `test_runner_r32.py`: `lane_env` has no silent default, and a direct live lane is refused with `DRAWINGS_AI_REVIEW_ENABLED=true`, with it missing, or with the task kinds / resume policy / gate differing from the declaration;
- `test_run_control_r38.py`: undeclared kind; missing or stale context; no failure streak counted; INVALID;
- `test_visibility_r38.py`: the `undeclared_task_kind` and `missing_context` drills.

## 2. Unread pages under application-internal limits (R39-06; A-09 point 1)

**The rule** (`LIVE-RUN-CONTRACT.md` §6; `run_state_r38.py`):
- **Harness and resource refusals make a document INCOMPLETE.** Classes `limit` and `failure`: lane allowance, parent ceiling, window, breaker, ledger, guard, identity, timeout, interruption, and the application's per-project rolling limit.
- **Application-internal per-document behaviour under the declared limits leaves it COMPLETE.** Class `arm_policy`: the reader's own cap 8, the JobBudget 12 / 120 s, a reader exception.
  - `unread_pages` (per page: kind, reason, partial), `unread_page_count` and `partially_read_pages` are carried into the lane rows, `RUN-REPORT.json`, every `lane-<lane>.r32.json` and `SCORE-BCR-R32.json` `unread_pages`. That last field reports, per lane, the documents with unread pages and the pages.
  - Each page is also an event and an allowance refusal record (the audit view).
  - The pages are counted as unread in every denominator.

**How the lane finds the pages.** After each C or R document, the lane derives the pages from the attempt the application itself stored (`unread_pages_of_attempt`):
- page outcome `budget: calls per document` → reader cap;
- `budget: <limit>` → JobBudget;
- a request refused by the budget → partially read;
- attempt outcome `failed` → every in-scope page, reader exception.

For B, a form read refused by the application's own per-document budget is listed as unread page `*`, and the document stays COMPLETE.

**Correction of a review38 claim.** `review38/CHANGE-RECORD.md` section 11 states that "the application's own per-document job limits (12 calls, 120 s, the reader's 8) are recorded per page as `application_document_limit`". **That was wrong for the reader's 8, and for reader exceptions.** The review38 lane recorded an event only when the JobBudget's exhaustion changed. Skips under the reader's own cap set no exhaustion and left no event, and an exception left none either (Verification 39 R39-06). review38's record stays frozen; this record corrects it.

**Tests:**
- `test_unread_pages_r39.py` (17): Verification 39's scenarios with the candidate's own reader and budget. **A** (4 + 4) → pages 3 and 4 `application_reader_cap`. **B** (7 + 5) → pages 3 and 4 `application_document_limit`. **C** (exception) → pages 1 to 4 `application_reader_exception`. All COMPLETE. The test also covers the partial-page case, every refusal kind still giving INCOMPLETE, the scorer report and the template text.
- `test_run_control_r38.py`: the recorder rule.
- `test_visibility_r38.py`: the `unread_pages` drill (SYNTHETIC 4-page documents, JobBudget lowered to 2, an injected reader exception).
- `UNREAD-PAGES-PROBE-R39.json`.

## 3. Deferral retry policy (R39-08)

- **Two times on every DEFERRED record:** `retry_at_earliest` (the first freed slot) and `retry_at_full` (`{planning, structural}`). The latter is the time at which the project's remaining requests (its `PROJECT-REQUEST-BOUNDS.json` total minus its charges) fit the window, or the window is empty when they exceed it (`allowance_r32.full_retry_time`).
- **Where they appear:** the refusal detail, the lane rows, `RUN-REPORT.json` and `RUN-STATE.json`.
- **The declaration's `resume_policy`:** `full` (default) uses the latest structural-basis full time; `earliest` uses the first slot.
- **The resume gate** (`runner_r32.resumable`) refuses a resume before the policy's time, and nothing is created.
- **Invocations EP-27331 needs** (`RESUME-INVOCATIONS-R39.json`, `resume_invocations_r39.py`; the runbook input in `LIVE-RUN-CONTRACT.md` §5):

| Demand | `full` | `earliest` |
|---|---|---|
| Planning estimate 63 | 2 | 2 to 4 |
| Structural maximum 160 | 3 | 3 to 101 |

  The worst `earliest` case is when each resume finds one freed slot. Each invocation after the first needs its own owner authorization.
- **Tests:**
  - `test_allowance_r32.py`: `full_retry_time`, and the deferral carries both times;
  - `test_run_control_r38.py`: the gate passes both times on;
  - `test_runner_r32.py`: `resumable` per policy, `resume_times`, the dry drill's policy validation, the EP-27331 model;
  - `test_visibility_r38.py`: the `retry_policy_full` drill, where an early resume and a resume between the earliest and the full time are both refused.

## 4. Failed reads and the capture store (R39-16)

**The new rule** (`run_control_r38.GateStoreProvider`; `capture_store.py` is unchanged by hash):
- The store serves only bound answers. In dry mode the stub's `dry_refused` stands for an answer.
- A reserved row without an outcome (interrupted) is still served `interrupted_charged` and never re-sent.
- **A fingerprint whose dispatches all failed is never served its failure.** The repeat is dispatched again:
  - as a new row under `retry_key(base, ordinal)`, recorded in the store's `retries` table;
  - charged, with the note `retry N of <bound key>`, and never refunded;
  - recorded as `retry_dispatched` with `retry_ordinal`;
  - listed in `ALLOWANCE-AUDIT.json` `retries`.
- The rule is identical for B and C. review38's per-document attribution of B's form reads is kept.
- R is still served C's capture by content key: C's answer when it holds one, otherwise C's latest state. R never re-sends a request C already sent.
- P's sample is frozen at P's first run (table `probe_sample`), so C's later retries cannot change P's population.

**The behaviour and its accuracy implication** are stated in `LIVE-RUN-CONTRACT.md` §13:
- Within an invocation, B's reconcile repeat of a failed read is dispatched. Across resumes, every failed fingerprint is dispatched again.
- B and C can now get an answer where review38 served the failure.
- Results depend on the number of invocations. The rule is symmetric; the exposure need not be.

**Tests:**
- `test_run_control_r38.py`:
  - first read failed → the repeat is dispatched and charged, with ordinal 2;
  - first read answered → the repeat is served;
  - a resume never re-sends a request with a bound answer, and retries a failed one;
  - interrupted is never re-sent, and `dry_refused` is bound;
  - R is served C's answer after C's retry;
  - the frozen probe sample.
- `test_visibility_r38.py`: the `failed_read_retry` drill (B's timed-out form read is retried on the reconcile path, charged, recorded).

## 5. The decision coverage gate (R39-15; owner ruling A-10)

**Eligibility is C >= B only.** This is **a change from plan v2**, whose gate was C >= B and C >= R. **It is not an unchanged gate.** The owner ruled it on 2026-10-04 (A-10).
- **The constant:** `score_bcr_r32.DECISION_COVERAGE_GATE = "C_GE_B_ONLY"`, a single named constant carrying its text, source and `change_from_plan_v2`. The declaration binds it as `decision_coverage_gate`.
- **The refusal:** the scorer (`refuse_r_in_eligibility`) and the declaration contract refuse any definition that binds R into eligibility, including plan v2's `C_GE_B_AND_C_GE_R`.
- **The mandatory diagnostic:** C >= R appears in every scorer result (`decision_coverage_C_ge_R`) and in `REPORT-TEMPLATE.md`, with both lanes' counts, the missing coverage per document and page with each lane's class and the reason, and INCOMPLETE (`holds: null`) when R did not complete its population.
- **Every other safety, accuracy and completeness gate is unchanged.**
- **Where it is stated:** `LIVE-RUN-CONTRACT.md` §12, `SCORER-CHANGES.md` v4, `REPORT-TEMPLATE.md` and the response entry.

**History.** The original ORCH-08C text asked for the definition as a constant "pending owner ruling", with both definitions computable. A-10 replaced that: the plan v2 definition is kept only as `PLAN_V2_DECISION_COVERAGE_GATE`, for the record, and is refused.

**Tests** (`test_score_bcr_r32.py`):
- the bound constant and its plan v2 statement;
- R refused as an eligibility input; the gate never reads R;
- the mandatory diagnostic with counts, missing coverage per document and reasons, INCOMPLETE when R is truncated or absent, and rendered by the template;
- the diagnostic present in every result, with the other gates unchanged.

`test_preflight_r32.py`: a declaration binding plan v2's gate is refused.

## 6. Model-identity evidence (R39-09, Q1; A-10 item 2)

`MODEL-ID-EVIDENCE.md` and `MODEL-ID-EVIDENCE.json` record a read-only byte search of the installed CLI. **The CLI was not executed in any form.**
- **The file:** `claude.exe` from winget, 218,746,016 bytes, sha256 `0b35df94…5b03`. Embedded version 2.1.263, build 2026-09-06T01:08:56Z.
- **Findings:**
  - `claude-sonnet-5` and `claude-opus-5` are catalog ids.
  - A full id passes `--model` unchanged.
  - Aliases resolve through a catalog that can change at runtime.
  - The `json` output's `modelUsage` keys are the **requested** model.
  - Only `stream-json`'s `message.model` carries the server's statement.
- **Outcome:** a more specific (dated) id is **not** exposed. The served-model identity is **UNRESOLVED** offline.
- **For the owner:** the probe command (4.1 json, as asked; 4.2 stream-json, recommended), the expected evidence and the interpretation. Not run.
- **The runtime check stays fail-closed** under the declared INVALID rule for any verifiable mismatch. Its limits are stated: it compares the requested id, and an echoed id passes.

## 7. Records (R39-02, R39-17) and the failed static step (A-10 item 3)

**R39-02.** The review38 binding manifest is `4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d`. It is bound here by that value, with review38's manifest `07c2fb78…`, review36's manifest `5e950813…` and binding `5a1a6aad…`.

**R39-17.** The review38 response entry said the carried modules "and their tests" were unchanged by hash. **Two carried tests had changed:**
- `test_literal_compare_r32.py`: one judge-level expectation, for the 25 formerly forgiven controls;
- `test_sandbox_ingest_r32.py`: a path-only change.

It gave "R1 30, R2 24, R3 26" beside "40 fixtures". Those are **case counts**. The fixtures are **R1 15, R2 12, R3 13**. This package's response entry states both corrections.

**The failed static request-path step** (`REQUEST-PATHS.md` §3; audit entry 09:58:00Z). The audit log's 09:15:56Z entry recorded only the final, successful run. The step had failed twice first:
1. **A shell parse error, exit 2.** The script was written in a Bash quoted heredoc together with `mkdir` and the run. Bash refused to parse it: `unexpected EOF while looking for matching '`, because the script text contains apostrophes. Nothing was created or run.
2. **A missing output folder, exit 1.** The script was then written with the Write tool and run with a relative output path. It computed the graph, then failed on writing: `FileNotFoundError` for `..\out\REQUEST-PATHS-STATIC.json`. The folder had never been created, because its `mkdir` was part of the failed command.

**Resolution:** the folders were created and the script re-run with an absolute output path. It succeeded.

**Limits of the final static method:** name-based over-approximation. It can list false positives, and one is listed. It cannot follow `getattr`, registries, monkeypatching or module-level code. It does not evaluate settings or data.

**How the dynamic probes cover what the static method cannot:**
- `drawings_ai_probe_r39.py` runs the real code of both trees: the declared setting switches the path off, and `true` switches it on.
- 1(d) runs that path with an answering fake.
- The runtime gate refuses any undeclared or context-less request that a missed static edge might produce. The visibility drills ran B, C and R on SYNTHETIC documents with the gate active, and the only breaches were the two injected ones.

## 8. Not done, and deviations, stated plainly

- **R39-18's optional suggestion was not implemented:** integer strings for the integer limit keys in `validate_declaration`. A value like `"12.0"` still passes validation and fails closed later in the lane.
- **Deviations from the task's expectations, each stated in its section:**
  - the structural bound is 160, not 154 (change 4);
  - P's sample is now frozen at its first run (a consequence of change 4);
  - synthetic specs may give a page count, a dry-drill aid in `synthetic_r32.py`;
  - the gate change follows A-10 instead of "pending owner ruling".
- **Not established:** the served-model identity. It is UNRESOLVED until the owner's probe, and even then it is a server self-report.
- **Snapshot timing:** `evidence/SNAPSHOT-BEFORE.json` was taken before packaging (about 10:13Z), not at the task's start. The task-start integrity check is the 09:00:34Z audit entry: every frozen input recomputed and equal.

## 9. Test run (junit in `tests/`)

- **Command:** `scripts/run_tests_r39.py`, from the frozen harness (`evidence/FREEZE-1.sha256`, 56 files).
- **Guard:** every pytest process ran under the `r38_write_guard` plugin, which allows writes only to the basetemp, the junit folder and `C:/t/r2x/r39-sandbox`, and allows no network.
- **Candidate-tree modules:** `test_capture_store` and `test_run_control_r38` run from `C:/t/iso/cand-r29/backend` (read-only use).
- **Result:** 22 modules, **466 tests, 0 failures, 0 errors, 0 skipped, 0 guard refusals** (`tests/SUMMARY.json`; review38: 392 in 20). Per module: test_allowance_r32 19, test_capture_store 21, test_concentration_r32 28, test_converter_r32 7, test_dispatch_guard_r32 15, test_labels_adapter_r32 13, test_lane_judge_r32 23, test_literal_compare_r32 48, test_model_identity_r38 8, test_preflight_r32 82, test_project_bounds_r32 9, test_request_paths_r39 11, test_run_control_r38 22, test_run_set_selector_r32 9, test_runner_r32 50, test_sandbox_ingest_r32 5, test_score_bcr_r32 43, test_state_check 5, test_stop_rules 8, test_tripwire_r32 5, test_unread_pages_r39 17, test_visibility_r38 18. Development runs (scratchpad, before the freeze) are not packaged; the dry runs and test sandboxes they created remain under `C:/t/r2x/r39-sandbox` (dry, 0 model requests).
