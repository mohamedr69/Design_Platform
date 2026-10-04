# Request paths of every lane (ORCH-08C task item 1(a); Verification 39 R39-04; A-09 points 1 and 3)

- **What this is:** every provider-call site that each lane's entry point can reach in the tree that lane runs, the task kinds it sends, the setting that enables it, its per-call and per-project bound, and whether it is declared and bounded for the run or disabled.
- **Author:** R39HARNESS-IMPL (Claude Opus 5.5, `claude-opus-5-5`, self-reported), 2026-10-04. Not self-approved; pending Verification 40.
- **Trees (read-only):** baseline `C:/t/iso/frozen-r12/backend` (HEAD `3d5607d9…`, clean) for lane B; candidate `C:/t/iso/cand-r29/backend` (HEAD `a8aacedd…`, clean) for C, R and P.
- **Evidence:** `REQUEST-PATHS-STATIC.json` (the static graph, every site with its call path), `scripts/harness-r32/request_paths_r39.py` (the analysis), `scripts/harness-r32/drawings_ai_probe_r39.py` and `test_request_paths_r39.py` (the dynamic probes and tests), `tests/test_request_paths_r39.xml`.
- **Standing status:** M2 CHANGES STILL REQUIRED; M3 not started. No provider or model request was made to produce this.

## 1. Method

1. **Every site.** All `<x>.complete(` calls and all `get_provider()` calls in `app/` of each tree, except the provider classes themselves (`app/ai/provider.py`): 31 sites per tree, 192 modules, about 2,400 functions.
2. **Reachability, over-approximated.** A static call graph from each lane's entry point:
   - B: `app.services.document_processing:run` in the baseline tree. Lane B calls it with `provider=chain`.
   - C and R: `app.ai.evidence_reader:evidence_stage` in the candidate tree. The lane calls it per document with `provider=chain, variant="EV1"`.
   - P runs no application code. `run_control_r38.probe_r38` re-sends a seeded sample of C's dispatched payloads through the harness chain.

   Resolution rules:
   - Names are resolved through each module's imports, including imports inside functions.
   - `self.f` resolves to every method `f` of the same module.
   - `obj.f` resolves to every method `f` of a class in the same module or in an imported module.
   - A function referenced without a call (a callback, `functools.partial(f)`, `task=f`) counts as an edge.
   - A class that is reached brings all its methods.
3. **Each reached site read by hand.** I read every reached site for the setting that enables it, its task kinds and its bounds (section 2). The dynamic probes (section 4) cover what a static graph cannot decide.

## 2. Result: every reached site and its status

### Lane B (baseline `document_processing.run`)

| Site (file:line, function) | Task kinds | Enabled by | Per call / per project (one invocation) | Status for the run |
|---|---|---|---|---|
| `app/compliance/assist.py:293` `_call`, reached by `submittal_reader._Run.call` → `assist.call_task`. The AI-stage form read (`document_sync.read_form_or_raise`) and the reconcile check's repeat (`submittal_reader.check`). | `read_submittal_form` (tier small) | `AI_ENABLED=true`, project policy, a ready provider, the task not switched off (`submittal_reader.available`) | 1 request per call. ≤ 2 per form document: the read, plus its repeat when the read failed (R39-16, change 4). B's per-job budget is `ai_read_max_calls_per_document` 60. | **Declared** (`lane_task_kinds.B`). **Bounded**: `PROJECT-REQUEST-BOUNDS.json` B = 2 per document (EP-27331: 12), B allowance 240, project window. |
| `app/services/drawing_ai_review.py:156` `_ask`, reached by `shop_drawings.reconcile` → `_ai_review` → `review_replies` / `review_reference_conflicts` / `review_floor_duplicates` | `drawings_reply_match`, `drawings_reference_conflict`, `drawings_floor_alias` (tier small) | `DRAWINGS_AI_REVIEW_ENABLED` (default **true**, `config.py` `b4fbc07f…` in both trees), `AI_ENABLED`, a ready provider (`drawing_ai_review.enabled()`) | 1 per question. ≤ `drawings_ai_max_calls_per_sync` = 10 per project per B invocation (cache hits excluded). | **Disabled**. The declared `application_env` sets `DRAWINGS_AI_REVIEW_ENABLED=false`. Every lane verifies the setting in its environment, in the application's settings and through `drawing_ai_review.enabled()` before anything is built. **Not declared**: if a request reached the gate, it would be refused as `undeclared_task_kind` and the run would be INVALID. |
| `app/ai/evidence_reader.py:328` `EvidenceRun.call`; `:1593` `evidence_stage` (the baseline's evidence stage) | the evidence kinds | `AI_EVIDENCE_VARIANT` ≠ `off` | (none in B) | **Disabled**: B declares `AI_EVIDENCE_VARIANT=off`. `document_processing.run` calls the stage only when `configured_variant() != "off"`, and the stage returns at `variant == "off"`. |
| `app/services/document_processing.py:260` `run` (`provider or get_provider()`); `app/ai/submittal_reader.py:203` `available`, `:598` `check`; `app/services/drawing_ai_review.py:124` `enabled` | none | (none) | no request | **Readiness only.** The provider is passed in, or only `.ready` / `.status` is read. `enabled()` reads the flag before the provider. |
| `app/ai/ledger.py:351` `LedgerProvider.complete` | none of its own | live only | (none) | The application's ledger wrapper around the declared provider, inside the dispatch guard. It is not a request path of its own. |

### Lanes C and R (candidate `evidence_reader.evidence_stage`)

| Site | Task kinds | Enabled by | Per call / per document | Status |
|---|---|---|---|---|
| `app/ai/evidence_reader.py:446` `EvidenceRun.call` | **C:** `discover_page`, `read_identity`, `read_revision`, `read_decision`, `locate_decision` (`AI_EVIDENCE_DECISION_REGION=1`), `read_field_context` (`AI_EVIDENCE_TARGETED=1`). **R:** the same without `locate_decision`. **Off under the declared switches:** `discover_region` (needs `AI_EVIDENCE_ROI` or `AI_EVIDENCE_EFFICIENT`) and the EV2 escalations (tier standard). | `AI_EVIDENCE_VARIANT=EV1` plus the lane's switches | 1 per call. Per document: `min(12, per-page maximum × pages read)`, where the JobBudget's 12 counts served and dispatched calls alike. C 9 per page, R 6 per page. | **Declared** (`lane_task_kinds`, derived from the declared switches by `preflight_r32.task_kinds_for`; the declaration must equal it). **Bounded** (`PROJECT-REQUEST-BOUNDS.json`; allowances C 240, R 40; window). |
| `:2673` `evidence_stage` (`provider or get_provider()`); `submittal_reader.available:203` | none | (none) | no request | **Readiness only.** The provider is passed in. Lanes C and R make `submittal_reader.available` return None (available). |
| `app/compliance/assist.py:293` `_call` | (none) | (none) | (none) | **A static false positive.** `evidence_reader._read_page` calls `run.call(...)` on an `EvidenceRun`. The graph cannot type `run`, so it links the name `call` to `submittal_reader._Run.call`. Reading the code: lanes C and R never call `submittal_reader.read_form`. Even if they did, `read_submittal_form` is not declared for C or R and the gate would refuse it. |
| `app/ai/ledger.py:351` | none | live only | (none) | As in lane B. |

### Lane P

- **Code:** harness only.
- **Task kinds:** C's (the probe re-sends C's dispatched payloads with their own document context).
- **Bound:** at most `round(0.15 × C's answered dispatches)` items, capped by P's allowance of 36.
- **Sample:** frozen at P's first run (change 4).

### Sites no lane reaches

Static analysis finds no path from any lane's entry point to the following sites:
- `sheet_reader.available` / `read_design_sheet`
- `verification.available` / `verify_boq` / `verify_details` / `drf_run` / `read_drf`
- `compliance.assist.available` / `open_session`
- `extraction.pipeline.ask` / `assist_project`
- `ifc.services.ai_symbol_review._call` / `enabled`
- `evaluation.run_case`
- the HTTP handlers of `routers/extraction.py`

The test `test_sites_never_reached_by_any_lane` pins this. Any request from these paths would carry a task kind that no lane declares, and the gate would refuse it (contract breach, run INVALID).

### Application settings needed (task item 1(b))

Section 2 shows one reachable request path that the declaration must switch off: the drawings-AI review. The **exact allowlist** of `application_env` is therefore `{"DRAWINGS_AI_REVIEW_ENABLED": "false"}`. Nothing else is needed:
- The baseline evidence stage is already off through the declared `AI_EVIDENCE_VARIANT=off`.
- No other reachable site sends requests.

## 3. What failed in the static request-path step, and how it was resolved (owner decision A-10 item 3)

The task list showed a failed step. The work-folder audit log at first recorded only the final, successful run (09:15:56Z). A correcting audit entry (09:58:00Z) records the following.

**Attempt 1 (exit code 2): nothing created, nothing run.**
- **The attempt:** I tried to write `scripts/request_paths_r39.py` with a Bash quoted heredoc (`cat > … <<'EOF'`). The same command also ran `mkdir -p` for the work folders and then ran the script.
- **The error:** bash refused to parse the command: `/usr/bin/bash: -c: line 15: unexpected EOF while looking for matching '`.
- **The cause:** the script's text (its docstring) contains apostrophes ("lane's", "ledger's"). The tool's heredoc handling broke the quoting. This shell trap is recorded in the project memory.
- **The result:** no file was written, no folder was created and no analysis ran.

**Attempt 2 (exit code 1): the analysis ran, the output could not be written.**
- **The attempt:** I wrote the script with the editor's Write tool, which avoids the shell, and ran it with a relative output path (`../out/REQUEST-PATHS-STATIC.json`).
- **The error:** the analysis completed, then failed on writing: `FileNotFoundError: [Errno 2] No such file or directory: '..\\out\\REQUEST-PATHS-STATIC.json'`.
- **The cause:** the `out/` folder did not exist. Its `mkdir` had been part of the command that never ran in attempt 1.

**Resolution (attempt 3, success):**
- I created the folders and re-ran the script with an absolute output path. It produced `REQUEST-PATHS-STATIC.json`.
- The script was later moved into the harness as `request_paths_r39.py`, so that the test module imports it. It was re-run from there; the output is the same.

No provider request, no `claude` invocation and no write outside the work folder happened in any attempt.

## 4. Limits of the static method, and what the dynamic probes cover

### What the static graph cannot do (limits)

- **It can over-report.** It resolves calls by name and import. An `obj.f` call on an object whose type it cannot infer is linked to every method `f` of the related modules. One such false positive is listed above (C → `assist._call`).
- **It can miss calls.** It does not see:
  - calls through `getattr`, strings or registries;
  - functions stored in data structures;
  - monkeypatching (the harness patches some application functions in lane processes);
  - code at module level;
  - methods called on objects passed in from modules that the caller does not import.

  The provider sites themselves are complete: every `.complete(` call in the trees is listed. A missed edge could only hide **whether** a listed site is reached; it cannot hide a site.
- **It does not evaluate settings or data.** Whether a reachable site actually sends depends on settings (the drawings flag, the evidence variant) and on data (replies that match no drawing, reference conflicts, floor suspects, the cache). Those conditions were read by hand (section 2).

### What the dynamic probes cover

- **`drawings_ai_probe_r39.py`** runs the real application code of **both trees** in a child process, with a sandbox database and a local fake provider. No model is used.
  - `switch` mode, `DRAWINGS_AI_REVIEW_ENABLED=false`, the declared value. The application's settings report `drawings_ai_review_enabled = False`. `drawing_ai_review.enabled()` returns False and names the setting. `shop_drawings._ai_review` returns at once and never asks the provider.
  - `switch` mode, `true`. The path goes past `enabled()` to the database. So the key is the effective switch.
  - `feed` mode (task item 1(d)). The review is enabled in a test sandbox, and the fake provider answers with an accepted match. The provider is asked (`drawings_reply_match`), and its answer is applied: the shop-drawing revision's status goes from `under_review`/`sync` to `approved`/`ai`. Yet every `project_documents` column the scorer reads is byte-equal before and after: `role`, `state`, `error`, `sha256`, `reference`, `revision`, `status`, `system_code`, `extracted`. No `ProjectDocument` was flushed during the review (SQLAlchemy `before_flush`).
  - **Conclusion for 1(d):** the drawings-AI outputs feed no measured field (identity, revision, decision) in either tree. Code reading agrees:
    - the path writes only the shop-drawing tables (revisions, candidates, events, drawing issues) and the AI cache;
    - the lanes' measured fields come only from `lane_r32.dump_rows`, which selects `project_documents` joined to `projects`, and from `score_lane_r32`;
    - lanes C and R never call `shop_drawings`.

    No owner decision is therefore needed on this point.
- **The runtime gate (change 1(c)) catches what static analysis might miss.**
  - Every request of every lane must carry a task kind declared for that lane, and the context of the document the lane is reading. The lane opens a document scope per document and clears the context afterwards.
  - Any undeclared request path that executes at run time is refused at the gate, recorded with its lane, task kind and context, and makes the run INVALID. It is never charged.
  - The visibility drills ran the application paths of B, C and R on SYNTHETIC documents with this check active (`application_path`, `failed_read_retry`, `unread_pages`, `application_project_limit`). Apart from the two injected drills (`undeclared_task_kind`, `missing_context`), no breach was recorded, so the real B, C and R paths sent only declared kinds with their document context.
- **Tests:** `test_request_paths_r39.py` (11 tests):
  - the reached sites equal the table above;
  - the drawings path is reachable from B only;
  - the sites never reached;
  - the task kinds follow the switches;
  - the allowlist equals the drawings switch, and `sandbox_env` sets it;
  - the switch in both trees, off and on;
  - 1(d) in both trees;
  - the scorer reads only `project_documents`;
  - the bounds count the path as disabled and state the alternative.
