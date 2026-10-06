# Live-run contract of the r42 runner, version 5 (ORCH-10; Verifications 40 and 41; owner decisions A-09, A-10 and A-11)

**What it covers.** What `runner_r32.py`, `lane_r32.py`, `preflight_r32.py`, `allowance_r32.py`, `run_control_r38.py`, `run_state_r38.py`, `model_identity_r38.py`, `project_bounds_r32.py`, `sandbox_ingest_r32.py` and `dispatch_guard_r32.py` require and do before and during a live run. These are the files bound in `BINDING-MANIFEST-R42.json` (review42), run only from `PILOT/review42/scripts/harness-r32/` in the merged installation.

**It authorizes nothing.**
- No declaration, authorization, token, run file, ledger scope or budget exists, and this task created none.
- Versions 3 (`review38/LIVE-RUN-CONTRACT.md`) and 4 (`review39/LIVE-RUN-CONTRACT.md`) stay frozen. This version replaces version 4 for the r42 harness.
- M2 is CHANGES STILL REQUIRED. M3 has not started.
- Reference set: reference set independently AI-reviewed (Claude agents), not human-signed.

**What changed since version 4 (ORCH-10; each section names its finding):**
- §2: contract 5 (`interpreter`, `disk_precondition`, `isolation`, `resume_authorization`, `global_provider`; the CLI pinned by absolute path, file sha256 and version line).
- §3: the separable multi-invocation authorization form (A-11 §4), default off; the nonce is consumed only after the allowance and the capture store exist.
- §7: the CLI pin.
- §10: the dry and test sandbox base `C:/t/r2x/r42-sandbox`.
- §14 (new): the invocation order, re-entry of a folder without an allowance, the free-disk floor (R41-09, R41-10, R41-11).
- §15 (new): the fail-closed global provider of lanes C, R and P (R40-04, owner option 2).
- §16 (new): portability to the merged installation and isolation from it.

**What changed from version 3 to version 4 (carried for the record; each section names its finding):**
- §2: contract 4.
- §4 and §13: the capture store serves answers only; failed reads are retried.
- §5: `retry_at_full` and the declared `resume_policy`, with the EP-27331 invocation numbers.
- §6: the unread-page rule and the contract-breach events.
- §9: the bounds model: the drawings path disabled; B 2 per document.
- §10: `application_env`, task kinds and document context are verified.
- §12: the decision coverage gate. It is a change from plan v2, and C >= R is a mandatory diagnostic.

## 1. Entry points

```text
runner_r32.py run    --mode live --declaration <DECL> --declaration-sha <SHA> --run-set <RUN-SET> --binding <BINDING> --binding-sha <SHA>
runner_r32.py resume --mode live --declaration <DECL> --declaration-sha <SHA> --run-set <RUN-SET> --binding <BINDING> --binding-sha <SHA>
```

- **Refused arguments in live mode:** `--auth-path` (argparse rejects it), a `--stamp` other than the declaration's, and `--sandbox-base`.
- **Dry drills only.** Each is refused in live mode, by the runner and again by every lane:
  - `--dry-fault L:N`;
  - `--dry-inject FILE`: timeouts, an identity mismatch, interruptions, unsaved responses, ledger usage; small caps, window or parent; a FAKE ledger; lowered application limits; and, new in ORCH-08C, `undeclared_request`, `context_free_request`, `reader_exception` and a `resume_policy`;
  - `--dry-synthetic SPEC` (SYNTHETIC EP-990001 documents only; a spec may give `pages`);
  - `--sandbox-base`.

## 2. The declaration contract 5 (`preflight_r32.validate_declaration`, then `verify_bounds` in the live preflight)

Every key is required. A missing or different value refuses the run before any folder exists. Contract 5 is contract 4 (the rows below) with `contract` = `"r42-live-contract-5"`, the CLI pin of `model_identity` and the five new keys at the end of the table.

| Key | Required value | Finding / authority |
|---|---|---|
| `contract` | `"r42-live-contract-5"` | ORCH-10 |
| `binding_manifest_sha256`, `run_set_sha256` | The binding manifest and run-set file of this run (both re-hashed). | R33-06 |
| `run.stamp`, `run.sandbox_base`, `run.folder` | • `run.stamp`: 3–64 characters from `[A-Za-z0-9._-]`.<br>• `run.sandbox_base`: the declared base `C:/t/r2x/r<NN>-sandbox`.<br>• `run.folder` = base/stamp. | ORCH-08 |
| `authorization.path`, `.owner_token_sha256` | The pinned path beside the declaration, and the token digest (64 hex). | R34-03 |
| `budget.parent`, `budget.lane_allowances` | • Parent: exactly `{total 556, input_tokens, output_tokens, elapsed_s}`.<br>• Lane allowances: exactly `{B 240, C 240, R 40, P 36}`, summing to the parent total. | A-09; R35-10 |
| `project_window` | `{limit 1..60, window_s 86400}`: the rolling per-project window over all lanes. | A-09; R35-09, R38-08 |
| `project_request_bounds` | `{path, sha256}` of `PROJECT-REQUEST-BOUNDS.json`. The live preflight recomputes it and refuses any difference. | R38-08 |
| `lane_switches` | B, C and R state `AI_EVIDENCE_VARIANT`; P is `{}`. | R34-05 |
| `provider_env` | The ten provider keys, plus the four application limits. The limits must be compatible (§9). Only `AI_*` keys are allowed. | A-09 |
| `model_identity` | Full ids (no alias), equal to `AI_MODEL_SMALL` / `AI_MODEL_STANDARD`; provider; **the CLI by absolute path (= `AI_CLAUDE_CLI`), the file's sha256 and the exact version line** (a name on PATH or a null version is refused). | R38-10; **ORCH-10** |
| `ledger` | `{path, scope, limits, wrap_provider: true}`. The limits equal the parent's. | A-09 |
| **`application_env`** | **Exactly** `{"DRAWINGS_AI_REVIEW_ENABLED": "false"}`.<br>• This is the exact allowlist of non-`AI_*` application settings, and the only one the request paths need (`REQUEST-PATHS.md`).<br>• It switches off the baseline's drawings-AI review in every lane: `document_processing.run` → `shop_drawings.reconcile` → `drawing_ai_review`, enabled by default, up to 10 requests per project per B invocation.<br>• Refused: any other key, any other value, and any `AI_*` key. | **R39-04 (new)** |
| **`lane_task_kinds`** | Equal to `task_kinds_for(lane_switches)`:<br>• B `["read_submittal_form"]`;<br>• C `["discover_page","locate_decision","read_decision","read_field_context","read_identity","read_revision"]`;<br>• R: the same without `locate_decision`;<br>• P = C.<br>A declaration cannot widen them. | **R39-04 (new)** |
| **`resume_policy`** | `"full"` (the default a declaration should state) or `"earliest"` (§5). | **R39-08 (new)** |
| **`decision_coverage_gate`** | `"C_GE_B_ONLY"` (§12). A declaration that binds R into eligibility, such as plan v2's `C_GE_B_AND_C_GE_R` or any other id, is refused. | **R39-15; A-10 (new)** |
| **`interpreter`** | `{path, sha256, version}` of the bound interpreter `G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe`. The runner and every live lane refuse another `sys.executable`, file hash or `sys.version`. | **ORCH-10 2.1.1** |
| **`disk_precondition`** | `{path: the sandbox base's drive, min_free_bytes ≥ 2147483648}` (2 GiB; configurable only upward). Checked before invocation 1 and every resume, before any folder is created or re-opened and before any nonce is consumed (§14). | **R41-10 (C1)** |
| **`isolation`** | Exactly `{forbidden_root: "G:/dev (2)/dev/ep-platform-merged", allowed_under_forbidden: {interpreter: <the venv>, harness: <this harness folder>}, env_file_never_read: <the merged .env>}` (§16). | **ORCH-10 2.1.5** |
| **`resume_authorization`** | `{max_invocations_per_file: 1..3, …}`: the bound of the multi-invocation authorization form (§3). | **A-11 §4** |
| **`global_provider`** | Exactly `{"B": "harness_chain", "C": "refusing", "R": "refusing", "P": "refusing"}` (§15). | **R40-04; A-11** |

A declaration with `dry_exercise` set is never a live declaration.

## 3. The authorization (`dispatch_guard_r32`; ORCH-10 adds the multi-invocation form)

As in contract 2, section 3:
- the pinned `OWNER-DISPATCH-AUTHORIZATION.json`;
- the token compared by digest;
- one consumed nonce per invocation;
- every lane and every request verifies its own invocation's record.

A resume is a new invocation with a new authorization.

ORCH-10 (A-11 §4), a separable feature, off unless the owner writes it:
- The file has exactly the keys `authorized_by`, `declaration_sha256`, `owner_token_sha256` and either `nonce` (the per-invocation form, unchanged) or `invocations_authorized` N with `nonces` (N distinct one-run nonces), 1 ≤ N ≤ the declared `resume_authorization.max_invocations_per_file` (3). Any other key is refused: an authorization can never name, raise, reset or re-create an allowance, the parent budget, the window, the scope or any limit.
- Each invocation consumes exactly one nonce, the first unconsumed one in list order. A nonce consumed out of order, a nonce consumed under another authorization file, a repeated nonce or N above the bound is refused. After N invocations, invocation N+1 needs a new file.
- A file naming any hash other than the RUN hash the runner verified (for example the frozen hash) is refused, as before.
- The nonce of an invocation is consumed only after the run's capture store is bound and its allowance exists (§14), so a failure before that consumes nothing and the same authorization serves the next attempt.

## 4. One run folder, one parent budget, one capture store

The folder layout is the same as version 3, section 4. `capture.sqlite` gains two tables:
- `retries`: one row per retry of a failed fingerprint;
- `probe_sample`: P's frozen sample.

A run that breached the contract also holds `CONTRACT-BREACH.json` and `CONTRACT-BREACH-LOG.jsonl`.

- **Parent budget and lane allowances (unchanged).** Both are immutable. No lane borrows from another. Charges are never refunded. Stops are durable.
- **The capture store (changed, R39-16):**
  - A bound **answer** is served, never re-sent.
  - In dry mode the stub's `dry_refused` stands for an answer and is served.
  - A reserved row without an outcome (an interrupted dispatch: the provider may have received it) is served `interrupted_charged` and never re-sent.
  - **A fingerprint whose dispatches all FAILED is never served its failure.** The repeat is dispatched again, on the application's own retry path.
  - Each repeat is a new reserved row under `retry_key(base bound key, ordinal)`, recorded in `retries`: ordinal, previous seq, previous outcome, lane, invocation.
  - Each repeat is charged (the charge's note is `retry N of <bound key> …`), never refunded, and visible:
    - lane rows: `retry_dispatched`, with `retry_ordinal`;
    - the audit: `ALLOWANCE-AUDIT.json` `retries`;
    - `RUN-REPORT.json` `store.retries`.
  - The repeat passes the same gate as any request: the identity and breach markers, the durable stop, the lane allowance, the parent and the window.
  - The rule is identical for B and C. review38's per-document attribution of B's form reads is kept.
  - Consequences: §13.
- **R (contract 3, kept).** R is served C's capture by content key: C's answer when C holds one, including an answer from a C retry; otherwise C's latest state, exactly as C saw it. R never re-sends a request C already sent. A request C never made is dispatched once in lane R and follows the same rules.
- **P.** The seeded 15 % sample of C's answered dispatches is drawn once, at P's first run, and kept in `probe_sample`. C's retries in a later invocation can never change P's population.

## 5. The project rolling window, deferral and resume (A-09; R39-08)

- **The window (unchanged).** It counts the charges of every lane for a project within the last `window_s` seconds. A request that would exceed the limit is not charged and not permanent: `DeferDocument`. The document is DEFERRED, the lane continues, and the lane gating is unchanged.
- **The DEFERRED record carries two times** (in lane rows, `RUN-REPORT.json` and `RUN-STATE.json`):
  - `retry_at_earliest`: the first freed slot, as before;
  - `retry_at_full = {planning, structural}`: the time at which the project's **remaining** requests fit the window. "Remaining" is the project's all-lane total from `PROJECT-REQUEST-BOUNDS.json` (planning estimate, and structural maximum, separately) minus the charges it already received. When the remaining requests exceed one window, the time is when the window is empty (`allowance_r32.full_retry_time`).
- **The declared `resume_policy` decides when a resume is allowed:**
  - `full` (default): at the **latest structural-basis** `retry_at_full` over the deferred documents. The structural basis is the conservative choice: the window then has room for everything the project can still ask, or is empty.
  - `earliest`: at the first freed slot.
  - If the `full` time falls after the elapsed bound, the policy falls back to the earliest retry (recorded).
- **The resume gate.** A resume before the policy's time is refused, and nothing is created. The refusal names both times. After the elapsed bound a deferred run is CLOSED, as before.
- **Runbook input: invocations EP-27331 needs.** The table comes from `RESUME-INVOCATIONS-R39.json` (`resume_invocations_r39.py`, a deterministic model of these rules; window 60 per 24 h).

| EP-27331 demand | `full` (default) | `earliest`, resumes as paced as the first invocation | `earliest`, resumes dispatching faster than earlier charges age (worst case) |
|---|---|---|---|
| Planning estimate 63 (B 6, C 46, R 4, P 7) | **2** (finishes about 24.3 h after the start) | 2 | 4 |
| Structural maximum 160 (B 12, C 72, R 40, P 36) | **3** (about 48.5 h) | 3 | 101 |

  - Each invocation after the first is a resume with its **own owner authorization**: one nonce per invocation.
  - Under `full`, the structural case needs at most 3 invocations within the 7-day elapsed bound.
  - Under `earliest`, the number depends on timing. In the worst case each resume finds exactly one freed slot, which was the behaviour seen in the drill (R39-08).
  - The model assumes no failed requests. Retries of failed requests on resumes (§13) add charges and can add invocations.
  - With review38's model (154), the worst `earliest` case was 95 invocations.

## 6. Visibility: every event is recorded per document and page

- **Where (unchanged).**
  - Lane rows: `LANE-<lane>.json` `limit_events` and `documents`.
  - Run state: `RUN-REPORT.json` `documents`, `unread_pages`, `retry_at_*`, `contract_breach`, and `RUN-STATE.json`.
  - Scorer: every `lane-<lane>.r32.json`, and `SCORE-BCR-R32.json` (`limit_incomplete`, `unread_pages`, `decision_coverage_C_ge_R`).
  - Audit view: `ALLOWANCE-AUDIT.json` refusals, charges, retries and stops.
- **Kinds.**
  - Class `limit`:
    - lane_allowance, parent_ceiling, parent_input_tokens, parent_output_tokens, parent_elapsed;
    - project_window, deferral_beyond_bound, unattributed, terminal_stop;
    - breaker, ledger, guard;
    - identity_mismatch, identity_invalid;
    - lane_stopped, not_started, waiting;
    - application_project_limit;
    - **undeclared_task_kind, missing_context, contract_breach_invalid**.
  - Class `failure`: provider_timeout, provider_failure, interrupted_charged, prerequisite_failed.
  - Class `arm_policy`: application_document_limit, **application_reader_cap, application_reader_exception**.
  - Class `retry`: **retry_dispatched**.
  - Unknown kinds count as limits.
- **The document-status rule (R39-06; the ORCH-021 ruling):**
  - **Harness and resource refusals make the document INCOMPLETE.** That covers the lane allowance, the parent ceiling, tokens and elapsed bound, the window, the breaker, the ledger, the guard, identity, a timeout, a provider failure, an interruption, and the application's per-project rolling limit (classes `limit` and `failure`).
  - A B or C document INCOMPLETE by a limit, or DEFERRED, makes the comparison INCOMPLETE. It stays in every denominator, and it is excluded from the matched sets with each exclusion listed.
  - **Application-internal per-document behaviour under the declared limits leaves the document COMPLETE, with `unread_pages` listed.** That covers the reader's own call cap (`MAX_CALLS_PER_DOCUMENT` 8, checked between pages), the per-document JobBudget (12 calls / 120 s), and a reader exception (class `arm_policy`).
  - Every page not read is recorded per page: its kind, its reason, whether it was read in part. It appears in the lane rows, `RUN-REPORT.json`, the scorer and the audit.
  - Those pages are counted as unread in every denominator. Their fields are never coverage.
  - The lane derives the pages from the attempt the application itself stored (`extracted.ai_evidence.attempts[-1]`: a page outcome `budget: …`, a request outcome `budget`, or the attempt outcome `failed`).
  - For B, a form read refused by the application's own per-document budget is listed as unread page `*`.
  - The review38 change record's claim that "the reader's 8 is recorded per page" was wrong. `CHANGE-RECORD-R39.md` corrects it; review38's record stays frozen.
- **Contract breaches (R39-04).**
  - Every request must carry a task kind declared for its lane (`lane_task_kinds`), and the context of the document the lane is reading. The lane opens a document scope per document and clears the context after it.
  - A request with an undeclared task kind, or with no or a stale context, is refused at the gate before anything is served or reserved. It is never charged.
  - It is recorded with the lane, the task kind, the context it carried and the context expected: lane rows, the allowance's refusals, and `CONTRACT-BREACH.json` (the first breach) plus `CONTRACT-BREACH-LOG.jsonl` (every breach).
  - It makes the run **INVALID**: every lane becomes terminal, and every later request is refused (`contract_breach_invalid`). The run is never resumed.
  - Such a request is classified `contract_breach`, never `provider_failure`, so it never counts toward any document's failure stop.
- **Silent skipping is a test failure.**

## 7. Model identity (ORCH-10: the CLI pinned by absolute path, file sha256 and version line; see `MODEL-ID-EVIDENCE.md`)

- **What is pinned.** The full ids `claude-sonnet-5` and `claude-opus-5`, and the provider `claude-code`.
- **What is checked.** The pinned CLI file's sha256 (read as bytes) and its `--version` line, before anything is created or re-opened (§14), and recorded before any lane. Every response's reported model and provider are checked.
- **On a mismatch.** `IDENTITY-INVALID.json` is written, the run is INVALID, the next request is refused, and every resume is refused.
- **Limits** (from the read-only CLI investigation):
  - The key the adapter reads (`modelUsage`) is the CLI's **requested** model, so the check verifies the CLI's resolution and the absence of a fallback, not the served model.
  - An absent non-haiku key echoes the configured id.
  - The served-model identity remains **UNRESOLVED** until the owner's probe; the command, the expected evidence and the interpretation are in `MODEL-ID-EVIDENCE.md`.
  - Any verifiable mismatch stays fail-closed.

## 8. The ledger: the single scope is the backstop (unchanged)

- Every charge precedes at most one ledger reservation: ledger dispatch entries ≤ charges ≤ parent total = the scope's `requests` limit.
- Retries of failed requests are charges like any other. Each one passes the ledger and is counted against the scope.

## 9. Compatible limits and the request bounds (`project_bounds_r32`, `PROJECT-REQUEST-BOUNDS.json`)

- **The harness project window governs.**
- **The application's per-project counters** count `AiUsage` rows in one lane database per invocation:
  - B: 2 per document;
  - C and R: B's rows plus their own (≤ 12 per document).
  - The declaration must bind `AI_MAX_CALLS_PER_PROJECT_PER_DAY` and `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` **≥ 84** (EP-27331: 12 + 72; unchanged), together with `AI_MAX_CALLS_PER_DOCUMENT` 12 and `AI_MAX_ELAPSED_S_PER_JOB` 120.
  - The drawings path writes no `AiUsage` row.
- **The bounds (project-bounds-r39-2026-10-04.1).** EP-27331:
  - planning **63.0** (unchanged);
  - structural **160**: B 12, C 72, R 40, P 36; 3 windows.
- **This is not the expected 154.** Change 4 dispatches B's reconcile-check repeat of a failed form read again. B is therefore bounded at 2 per document per invocation (review38: 1, because the repeat was served its failure). That accounts for the +6. All six projects: EP-3563 90, EP-15744 38, EP-22349 137, EP-26687 159, EP-27331 160, EP-29255 64.
- **The drawings-AI path** is counted 0 (disabled by `application_env`). The enabled alternative is stated for the record: +10 per project per B invocation, EP-27331 170. On review38's model that is 164, the figure Verification 39 gave. It is still 3 windows.
- **Retries across resumes** (§13) are not in these totals. They are bounded by the lane allowances, the parent total and the window.

## 10. Lane verification and the sandbox base

Every live lane does the following before anything is built:
- re-runs the live preflight, including the bounds recomputation, the model identity and the contract-4 values;
- verifies its `AI_EVIDENCE_*` environment, and every declared provider value in its environment and in the application's settings.

New in ORCH-08C, every lane, **live and dry**, at every invocation and resume:
- verifies the declared `application_env` in its environment **and** in the application's settings (`drawings_ai_review_enabled` must be False);
- checks that `drawing_ai_review.enabled()` reports the review off;
- refuses to start otherwise.

`sandbox_env()` sets `DRAWINGS_AI_REVIEW_ENABLED=false` in every application process the harness starts: lanes, the ingestion child and scoring.

The gate is given the lane's declared task kinds. In dry mode with reader `none`, the exercise's synthetic probe task `r33_dry_probe` is added. The gate is also given the current document's sha256 as the expected context.

The sandbox base defaults to `C:/t/r2x/r42-sandbox` for dry runs and tests (ORCH-10). Live runs use the declaration's.

## 11. Dry mode

- No provider exists: the refusing `DryStub`.
- There is no ledger path. A FAKE ledger is used only with `dry_ledger`.
- No CLI is run, and 0 model requests are made.
- The AI ledger must read the same before and after.
- Injections apply to the invocations they name.
- The application environment is applied and verified in dry mode too.

## 12. The decision coverage gate (R39-15; the owner's ruling A-10, 2026-10-04)

- **Eligibility: C >= B only.** The constant is `score_bcr_r32.DECISION_COVERAGE_GATE = "C_GE_B_ONLY"`. Its text and source are in `DECISION_COVERAGE_GATE_DEFINITIONS`, and the declaration binds it as `decision_coverage_gate`.
- **This is a change from plan v2.** Plan v2's gate was C >= B **and** C >= R. It is not an unchanged gate. The owner ruled it explicitly: "Bind decision coverage eligibility to C ≥ B only".
- **C >= R is a mandatory diagnostic.** It appears in every scorer result (`decision_coverage_C_ge_R`) and in every report (`REPORT-TEMPLATE.md`). It carries:
  - both lanes' counts;
  - `holds`;
  - the missing coverage per document and page, with each lane's class and the reason;
  - its state: INCOMPLETE when R did not complete its declared population, with why.
- **R never determines eligibility.** The scorer and the declaration contract refuse any definition that binds R into it.
- **Every other safety, accuracy and completeness gate is unchanged.**

## 13. Failed reads and the capture store: behaviour and its accuracy implication (R39-16)

- **Within one invocation.**
  - Lane B's AI stage reads each new form once. When that read fails, the application's reconcile check (`submittal_reader.check`) reads the form again.
  - In review38 the repeat was the same bound fingerprint and was **served the failure**. Before that, in review36, it was re-sent under a wrong context.
  - Now the repeat is **dispatched again**: charged, recorded as retry 2, attributed to its own document.
  - The candidate reader never repeats an identical request inside a document, so for C and R the JobBudget's 12 per document still bounds all calls, served or dispatched.
- **Across resumes.**
  - A resume re-runs every lane on new sandboxes. Every request with a bound answer is served. Every request whose dispatches all failed is dispatched again, as retry `n + 1`.
  - These retries are charged and pass the window, the allowances and the durable stops.
  - A lane already terminal (for example after three consecutive failures) refuses them visibly (`terminal_stop`).
  - Their number is bounded by the lane allowances, the parent total and the window, not by `PROJECT-REQUEST-BOUNDS.json`.
- **Accuracy implication, stated plainly.**
  - B and C can now obtain an answer on the application's retry where review38 gave them the stored failure.
  - Their results can therefore differ from review38's for exactly the requests that failed. The difference can only turn a failure into an answer, and the answer is judged like any other.
  - The results depend on the number of invocations: a run that needed resumes gives failed requests more attempts than one that did not.
  - The rule is identical for B and C, but the two lanes can have different numbers of failures, so the exposure is symmetric in rule, not necessarily in count.
  - When a B form read is answered only on the reconcile repeat, the reading is stored and drawn on the submittal map. The B row stays in the state the application gave it after the failed first read. Whether the repeat's answer reaches the row's measured fields is the application's own reconcile behaviour, unchanged here.
- **Interrupted dispatches.** A reserved row without an outcome is still never re-sent. It is served `interrupted_charged`, because the provider may have answered. A failure is retried; an unknown outcome is not.

## 14. The invocation order, re-entry and the free-disk floor (ORCH-10; R41-09, R41-10, R41-11)

`runner_r32.main` now orders every invocation so that a failure before the run's allowance exists can never strand the run or consume an authorization:

1. **Every check, nothing created, re-opened or consumed:** the binding; (live) contract 5, the bound interpreter, the pinned CLI file's sha256; the free space of the sandbox base's drive (≥ the declared floor, 2 GiB; dry mode uses the same floor); the HEADs; the truth and the population gate; the run set; (live) the bounds and the ledger scope; the resume rules (a resume) or the re-entry proof (a `run` on an existing folder); the guard preview; then `claude --version`, the only process this step starts, compared with the pin and with the run's first recorded line.
2. The run folder (invocation 1), or the re-entered or re-opened folder; `RUN-STATE.json`; the `WRITER.lock`; the output folder; the version and provider-identity record.
3. The capture store bound to the run key; then the ONE allowance, created atomically (built as `allowance.sqlite.new` and renamed into place only once its binding is committed; a resume opens the existing one and never re-creates it).
4. (live) **Only now** the authorization nonce is consumed (the O_EXCL consumption record).
5. The lanes, the allowance audit, the scoring.

**Re-entry.** A failure in steps 2–3 leaves a folder that `run` may re-enter. `reentry_proof` requires, from the folder's own records, that no allowance was ever created (`allowance.sqlite` absent), no nonce was consumed (no consumption record) and no request was charged (the capture store, if bound, is bound to this run key and holds no request). It writes `REENTRY-<n>.json`; the re-entry is a new invocation number; nothing existing is reset or re-created (an unreadable `RUN-STATE.json` and a partial allowance file are kept aside under new names, never used). With an allowance present, `run` is refused (`use 'resume'`).

**Resume.** A resume re-checks the CLI file, the version line and the free disk before it consumes its nonce (R41-11). A failure after the allowance exists but before the consumption is resumed with the same, still unconsumed authorization.

**Refusals that stay.** A second `run` with an allowance present; a resume without an allowance (now with the hint that `run` re-enters); `WRITER.lock`; an identity mismatch or a contract breach (INVALID, never resumed); a terminal comparison; a resume before the resume policy's time; after the elapsed bound (CLOSED).

## 15. The global-provider boundary of lanes C, R and P (ORCH-10; R40-04, owner decision A-11: option 2)

- Lane B keeps the harness chain as the application's global provider (unchanged).
- Lanes C, R and P install `run_control_r38.RefusingGlobalProvider` as the application's global provider (`app.ai.provider.set_provider`) right after the provider module is imported, before any application code runs; the lane checks at the end that it is still installed.
- An application path that calls `get_provider().complete(...)` in C, R or P is refused (`dispatch_refused`): never dispatched, never charged, never reaching the CLI or a ledger. It is recorded as the contract breach `global_provider_request` (`CONTRACT-BREACH.json`, the lane's events per document and page, the allowance's refusals) and makes the run INVALID under the undeclared-request rule; the lane's stop controller makes every lane terminal.
- `REQUEST-PATHS-STATIC.json` (request_paths_r42) resolves every `get_provider()` site of both trees to the refusing provider (C, R, P) or the chain (B), installed before every application entry; `test_global_provider_r42.py` shows the dynamic refusal in C, R and P and lane B unchanged.

## 16. Portability to the merged installation and isolation from it (ORCH-10 2.1)

- Every binding names the merged installation (`G:/dev (2)/dev/ep-platform-merged/ep-platform/…`); every bound file hashes as before (`BINDING-MANIFEST-R42.json`).
- The interpreter is bound (§2): the merged venv's `python.exe`, its sha256 and `sys.version`; lanes, ingestion and scoring run under it.
- `sha256` of bound files and the binding check open files through the extended-length prefix (`\\?\`): `LongPathsEnabled` is 0 on this machine.
- Isolation: every lane, live and dry, at its start and again at its end, refuses any environment value, application setting, `sys.path` entry or loaded module under `G:/dev (2)/dev/ep-platform-merged/` except the bound venv and this harness folder, and refuses an application env file that is the merged `.env` (the frozen trees read only their own, absent, `.env`). `sandbox_env` drops the shell's `PWD` / `OLDPWD`. The lanes' application settings come only from the declaration and the sandbox; the merged installation's `.env`, data and code are never read, and its bundled CLI 2.1.289 is never used.
