# VISIBILITY-REPORT (ORCH-08C re-run over the r39 harness; ORCH-08 task item 8; A-09 point 7)

- **Exercise:** `scripts/visibility_exercise_r39.py`, 2026-10-04T10:11:43+00:00 to 2026-10-04T10:18:30+00:00 (UTC); raw evidence `VISIBILITY-RESULT.json`.
- **Nature:** dry runs only: the refusing stub (run_control_r38.DryStub) answers nothing usable, no provider is built, no model request is made; the application path reads only SYNTHETIC EP-990001 documents; the real reviewed-2 labels are read only by the adapter (reader 'none' runs read no document); FAKE ledgers live inside the dry run folders.
- **AI ledger (mode=ro):** before 483 entries / 17 scopes, after 483 / 17; unchanged: True.
- **Model requests:** 0 (every invocation of every scenario).
- **Every injected event visible in every place it can reach:** True. **No bound fingerprint re-sent:** True.
- **Contract breaches (CONTRACT-BREACH.json) recorded:** {'undeclared_task_kind': 'undeclared_task_kind', 'missing_context': 'missing_context'}; only where injected: True (the application paths of B, C and R on SYNTHETIC documents sent only declared task kinds with their document context).
- **Where:** run state = `RUN-STATE.json` + `inv-<n>/out/RUN-REPORT.json` (documents per lane with status, kinds, pages); lane rows = `inv-<n>/out/LANE-<lane>.json` `limit_events`; scorer = `lane-<lane>.r32.json` document status / classes / pages and `SCORE-BCR-R32.json` `limit_incomplete` and coverage `status_rows` (the documents stay in every denominator); audit = `inv-<n>/out/ALLOWANCE-AUDIT.json` refusals, charges (outcome, ledger entry) and durable stops.
- This report authorizes nothing; M2 is CHANGES STILL REQUIRED; M3 has not started.

| Scenario | Injected | Status shown | Run state | Lane rows | Scorer (denominators) | Audit view |
|---|---|---|---|---|---|---|
| `lane_allowance` | C's own allowance is 1: its 2nd request is refused (C budget-stopped); the resume re-opens the stop | INCOMPLETE | 2 | 2 | 14 | 5 |
| `project_window` | 3 EP-27331 documents, a rolling window of 2 per 12 s, resume policy 'earliest': deferrals, retry times, resumes until finished | DEFERRED | 19 | 4 | 8 | 12 |
| `retry_policy_full` | the same 3 EP-27331 documents under the 'full' resume policy: every DEFERRED record carries retry_at_earliest and retry_at_full (planning / structural); a resume before the policy's time is refused and creates nothing | DEFERRED (retry_at_earliest and retry_at_full; resume refused before the 'full' time), then FINISHED | 19 | 4 | 8 | 12 |
| `undeclared_task_kind` | after its 1st document B sends a 'drawings_reply_match' request (the drawings-AI task, undeclared for B): refused at the gate, recorded with the lane, task and context, CONTRACT-BREACH.json written, the run INVALID, the resume refused | INVALID (contract breach; never charged; never resumed) | 2 | 1 | 2 | 2 |
| `missing_context` | after its 1st document C sends a DECLARED task kind with no document context (the context is cleared after each document): refused at the gate as a contract breach, never charged, the run INVALID | INVALID (contract breach; never charged) | 1 | 1 | 7 | 2 |
| `unread_pages` | SYNTHETIC 4-page documents, the per-document JobBudget lowered to 2 (dry only): pages left unread or read in part by the application's own budget, and an evidence-reader exception on the 2nd document -- every such page recorded per page; the documents stay COMPLETE with unread_pages | COMPLETE with unread_pages (application-internal); limit refusals stay INCOMPLETE | 4 | 13 | 13 | 13 |
| `failed_read_retry` | SYNTHETIC: B's first form read times out; the application's reconcile check repeats the read: it is dispatched again (a retry with its ordinal, charged), never served the failure | retry dispatched and charged (ordinal 2); the B row stays INCOMPLETE (failure) | 1 | 2 | 6 | 2 |
| `deferral_beyond_bound` | the window frees after the elapsed bound: the deferral cannot complete, the document is INCOMPLETE | INCOMPLETE | 3 | 3 | 9 | 6 |
| `bound_passed_while_deferred` | deferred, then resumed only after the elapsed bound: the run is CLOSED INCOMPLETE | DEFERRED, then CLOSED INCOMPLETE | 9 | 1 | 1 | 1 |
| `breaker` | C's 1st response reports 200,000 input tokens to the FAKE ledger (per-request 100,000): its breaker opens; the next request is refused | INCOMPLETE | 1 | 1 | 7 | 3 |
| `ledger` | the FAKE ledger scope allows 5 requests: B takes 4, C's 2nd request is refused by the ledger | INCOMPLETE | 2 | 2 | 8 | 3 |
| `provider_timeout` | C's first three requests time out: three consecutive failures make C terminal | INCOMPLETE | 9 | 9 | 23 | 10 |
| `interrupted` | C's process dies inside its 2nd dispatch (no response): the row stays reserved, the charge 'dispatched' | INCOMPLETE (served interrupted_charged) | 2 | 2 | 6 | 1 |
| `unsaved` | C's 2nd response came back (identity logged) and the process died before saving it | INCOMPLETE (served interrupted_charged) | 2 | 2 | 6 | 1 |
| `identity_mismatch` | C's 1st response names claude-sonnet-5-1, not the pinned claude-sonnet-5: the run is INVALID | INVALID | 1 | 1 | 8 | 2 |
| `application_path` | SYNTHETIC EP-990001 documents through the application readers: a timeout on a page, then C's allowance | INCOMPLETE | 3 | 3 | 10 | 3 |
| `application_project_limit` | SYNTHETIC EP-990001: the application's own per-project limit lowered to 1 (dry drill only) refuses C before the harness -- the R38-08 failure mode -- and is recorded, never silent | INCOMPLETE | 4 | 4 | 11 | 4 |

Counts are the number of records found in each place (0 would be a silent loss; none is 0).

## `lane_allowance`

- **Injected:** C's own allowance is 1: its 2nd request is refused (C budget-stopped); the resume re-opens the stop. **Kinds located:** lane_allowance, terminal_stop.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-lane-allowance-8d04ea`; steps: run -> finished; resume -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE, _reference_only COMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 6}.
- **Invocation 2 (resume, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE, _reference_only COMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 6}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.F009`; status=INCOMPLETE, pages={'1': ['lane_allowance']} (+1 more)
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=lane_allowance, pool_id=F009, page=1 (+1 more)
- **scorer:** `inv-1/out/lane-C.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['limit'] (+11 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=lane_allowance, page=1 (+4 more)

## `project_window`

- **Injected:** 3 EP-27331 documents, a rolling window of 2 per 12 s, resume policy 'earliest': deferrals, retry times, resumes until finished. **Kinds located:** project_window.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-project-window-ecbe30`; steps: run -> finished; resume -> refused (refused: the resume policy 'earliest' allows a resume at 2026-10-04T10:12:27+00:00 (earlie); resume -> finished; resume -> refused (refused: the resume policy 'earliest' allows a resume at 2026-10-04T10:12:47+00:00 (earlie); resume -> finished; resume -> refused (refused: the resume policy 'earliest' allows a resume at 2026-10-04T10:13:13+00:00 (earlie); resume -> finished.
- **Invocation 1 (fresh, finished):** run state DEFERRED; comparison DEFERRED: B documents deferred by the project window; C not started (earliest retry 2026-10-04T10:12:27+00:00); candidate outcome INCOMPLETE; earliest retry 2026-10-04T10:12:27+00:00; retry_at_full {'planning': '2026-10-04T10:12:27+00:00', 'structural': '2026-10-04T10:12:27+00:00'}; resume policy earliest (not before 2026-10-04T10:12:27+00:00); model requests 0; documents [B: F009 COMPLETE, F032 DEFERRED, F037 COMPLETE; C: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED; P: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED; R: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED].
- **Invocation 2 (resume, finished):** run state DEFERRED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry 2026-10-04T10:12:47+00:00; retry_at_full {'planning': '2026-10-04T10:12:49+00:00', 'structural': '2026-10-04T10:12:49+00:00'}; resume policy earliest (not before 2026-10-04T10:12:47+00:00); model requests 0; documents [B: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; C: F009 DEFERRED, F032 DEFERRED, F037 COMPLETE; R: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED]; C decision coverage denominator 9 pages, status rows {'deferred_document_rows': 7}.
- **Invocation 3 (resume, finished):** run state DEFERRED; comparison PENDING; candidate outcome NOT ELIGIBLE; earliest retry 2026-10-04T10:13:13+00:00; retry_at_full {'planning': '2026-10-04T10:13:13+00:00', 'structural': '2026-10-04T10:13:13+00:00'}; resume policy earliest (not before 2026-10-04T10:13:13+00:00); model requests 0; documents [B: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; C: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; R: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE, _reference_only DEFERRED]; C decision coverage denominator 9 pages, status rows {}.
- **Invocation 4 (resume, finished):** run state FINISHED; comparison PENDING; candidate outcome NOT ELIGIBLE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; C: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; R: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE, _reference_only COMPLETE]; C decision coverage denominator 9 pages, status rows {}.
- **run_state:** `inv-1/out/RUN-REPORT.json retry_at_earliest / retry_at_full / resume_not_before` (+11 more)
- **lane_rows:** `inv-1/out/LANE-B.json limit_events`; kind=project_window, pool_id=F032, page=1, retry_at_utc=2026-10-04T10:12:27+00:00 (+3 more)
- **scorer:** `inv-1/out/lane-B.r32.json documents.F032`; status=DEFERRED, pages=['1'], classes=['limit'] (+7 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=project_window, page=1, retry_at_utc=2026-10-04T10:12:27+00:00 (+11 more)

## `retry_policy_full`

- **Injected:** the same 3 EP-27331 documents under the 'full' resume policy: every DEFERRED record carries retry_at_earliest and retry_at_full (planning / structural); a resume before the policy's time is refused and creates nothing. **Kinds located:** project_window.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-retry-policy-full-52b0b2`; steps: run -> finished; resume -> refused (refused: the resume policy 'full' allows a resume at 2026-10-04T10:13:46+00:00 (earliest r); resume -> finished; resume -> refused (refused: the resume policy 'full' allows a resume at 2026-10-04T10:14:07+00:00 (earliest r); resume -> refused (refused: the resume policy 'full' allows a resume at 2026-10-04T10:14:07+00:00 (earliest r); resume -> finished; resume -> refused (refused: the resume policy 'full' allows a resume at 2026-10-04T10:14:28+00:00 (earliest r); resume -> finished.
- **Invocation 1 (fresh, finished):** run state DEFERRED; comparison DEFERRED: B documents deferred by the project window; C not started (earliest retry 2026-10-04T10:13:46+00:00); candidate outcome INCOMPLETE; earliest retry 2026-10-04T10:13:46+00:00; retry_at_full {'planning': '2026-10-04T10:13:46+00:00', 'structural': '2026-10-04T10:13:46+00:00'}; resume policy full (not before 2026-10-04T10:13:46+00:00); model requests 0; documents [B: F009 COMPLETE, F032 DEFERRED, F037 COMPLETE; C: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED; P: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED; R: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED].
- **Invocation 2 (resume, finished):** run state DEFERRED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry 2026-10-04T10:14:05+00:00; retry_at_full {'planning': '2026-10-04T10:14:07+00:00', 'structural': '2026-10-04T10:14:07+00:00'}; resume policy full (not before 2026-10-04T10:14:07+00:00); model requests 0; documents [B: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; C: F009 DEFERRED, F032 DEFERRED, F037 COMPLETE; R: F009 DEFERRED, F032 DEFERRED, F037 DEFERRED]; C decision coverage denominator 9 pages, status rows {'deferred_document_rows': 7}.
- **Invocation 3 (resume, finished):** run state DEFERRED; comparison PENDING; candidate outcome NOT ELIGIBLE; earliest retry 2026-10-04T10:14:28+00:00; retry_at_full {'planning': '2026-10-04T10:14:28+00:00', 'structural': '2026-10-04T10:14:28+00:00'}; resume policy full (not before 2026-10-04T10:14:28+00:00); model requests 0; documents [B: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; C: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; R: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE, _reference_only DEFERRED]; C decision coverage denominator 9 pages, status rows {}.
- **Invocation 4 (resume, finished):** run state FINISHED; comparison PENDING; candidate outcome NOT ELIGIBLE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; C: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE; R: F009 COMPLETE, F032 COMPLETE, F037 COMPLETE, _reference_only COMPLETE]; C decision coverage denominator 9 pages, status rows {}.
- **run_state:** `inv-1/out/RUN-REPORT.json retry_at_earliest / retry_at_full / resume_not_before` (+11 more)
- **lane_rows:** `inv-1/out/LANE-B.json limit_events`; kind=project_window, pool_id=F032, page=1, retry_at_utc=2026-10-04T10:13:46+00:00 (+3 more)
- **scorer:** `inv-1/out/lane-B.r32.json documents.F032`; status=DEFERRED, pages=['1'], classes=['limit'] (+7 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=project_window, page=1, retry_at_utc=2026-10-04T10:13:46+00:00 (+11 more)

## `undeclared_task_kind`

- **Injected:** after its 1st document B sends a 'drawings_reply_match' request (the drawings-AI task, undeclared for B): refused at the gate, recorded with the lane, task and context, CONTRACT-BREACH.json written, the run INVALID, the resume refused. **Kinds located:** undeclared_task_kind, contract_breach_invalid.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-undeclared-task-kind-9cb5b9`; steps: run -> finished; resume -> refused (refused: the run is INVALID (contract breach recorded in CONTRACT-BREACH.json: an undeclar).
- **Invocation 1 (fresh, finished):** run state INVALID; comparison INVALID: contract breach (B: undeclared_task_kind, task 'drawings_reply_match'); candidate outcome INVALID; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; C: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE].
- **CONTRACT-BREACH.json:** kind undeclared_task_kind, lane B, task 'drawings_reply_match', context {'page': None, 'profile': 'drill', 'sha256': '009717871f15d1021291f77ecf0b29a4e2e7362e8087e89a11bc48e02c84cf34', 'variant': 'drill'}, expected 009717871f15d1021291f77ecf0b29a4e2e7362e8087e89a11bc48e02c84cf34.
- **run_state:** `inv-1/out/RUN-REPORT.json contract_breach (and RUN-STATE / CONTRACT-BREACH.json)`; kind=undeclared_task_kind, comparison_state=INVALID: contract breach (B: undeclared_task_kind, task 'drawings_reply_match') (+1 more)
- **lane_rows:** `inv-1/out/LANE-B.json limit_events`; kind=undeclared_task_kind, pool_id=F037
- **scorer:** `inv-1/out/lane-B.r32.json documents.F037`; status=INCOMPLETE, pages=['*'], classes=['limit'] (+1 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=undeclared_task_kind (+1 more)

## `missing_context`

- **Injected:** after its 1st document C sends a DECLARED task kind with no document context (the context is cleared after each document): refused at the gate as a contract breach, never charged, the run INVALID. **Kinds located:** missing_context.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-missing-context-9955b9`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state INVALID; comparison INVALID: contract breach (C: missing_context, task 'discover_page'); candidate outcome INVALID; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 6}.
- **CONTRACT-BREACH.json:** kind missing_context, lane C, task 'discover_page', context {'page': None, 'profile': None, 'sha256': None, 'variant': None}, expected None.
- **run_state:** `inv-1/out/RUN-REPORT.json contract_breach (and RUN-STATE / CONTRACT-BREACH.json)`; kind=missing_context, comparison_state=INVALID: contract breach (C: missing_context, task 'discover_page')
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=missing_context
- **scorer:** `inv-1/out/SCORE-BCR-R32.json comparison_state`; comparison_state=INVALID (+6 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=missing_context (+1 more)

## `unread_pages`

- **Injected:** SYNTHETIC 4-page documents, the per-document JobBudget lowered to 2 (dry only): pages left unread or read in part by the application's own budget, and an evidence-reader exception on the 2nd document -- every such page recorded per page; the documents stay COMPLETE with unread_pages. **Kinds located:** application_document_limit, application_reader_exception, application_reader_cap.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-unread-pages-86a266`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison NOT DISPATCHABLE (EXTEND:extension-1); candidate outcome NOT DISPATCHABLE (EXTEND:extension-1); earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE; C: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE; R: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE]; C decision coverage denominator 3 pages, status rows {'incomplete_document_rows': 1}; unread pages {'B': {}, 'C': {'SYN001': {'status': 'COMPLETE', 'unread_page_count': 2, 'unread_pages': {'3': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_document'}], '4': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_document'}]}}, 'SYN003': {'status': 'COMPLETE', 'unread_page_count': 4, 'unread_pages': {'1': [{'kind': 'application_reader_exception', 'partial': False, 'reason': 'the evidence reader raised: RuntimeError: r39 drill: injected evidence-reader exception (dry only)'}], '2': [{'kind': 'application_reader_exception', 'partial': False, 'reason': 'the evidence reader raised: RuntimeError: r39 drill: injected evidence-reader exception (dry only)'}], '3': [{'kind': 'application_reader_exception', 'partial': False, 'reason': 'the evidence reader raised: RuntimeError: r39 drill: injected evidence-reader exception (dry only)'}], '4': [{'kind': 'application_reader_exception', 'partial': False, 'reason': 'the evidence reader raised: RuntimeError: r39 drill: injected evidence-reader exception (dry only)'}]}}}, 'R': {'SYN001': {'status': 'COMPLETE', 'unread_page_count': 2, 'unread_pages': {'3': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_document'}], '4': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_document'}]}}, 'SYN003': {'status': 'COMPLETE', 'unread_page_count': 2, 'unread_pages': {'3': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_document'}], '4': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_document'}]}}}}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.SYN001`; status=COMPLETE, pages={'3': ['application_document_limit'], '4': ['application_document_limit']} (+3 more)
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=application_document_limit, pool_id=SYN001, page=3 (+11 more)
- **scorer:** `inv-1/out/lane-C.r32.json documents.SYN001`; status=COMPLETE, pages=['3', '4'], classes=['arm_policy'] (+11 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=application_document_limit, page=3 (+11 more)

## `failed_read_retry`

- **Injected:** SYNTHETIC: B's first form read times out; the application's reconcile check repeats the read: it is dispatched again (a retry with its ordinal, charged), never served the failure. **Kinds located:** retry_dispatched, provider_timeout.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-failed-read-retry-55e904`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison NOT DISPATCHABLE (EXTEND:extension-1); candidate outcome NOT DISPATCHABLE (EXTEND:extension-1); earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE; C: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE; R: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE]; C decision coverage denominator 3 pages, status rows {'incomplete_document_rows': 1}; capture-store retries [{'lane': 'B', 'n': 1, 'ordinal': 2, 'previous_outcome': 'timeout'}].
- **run_state:** `inv-1/out/RUN-REPORT.json documents.B.SYN002`; status=INCOMPLETE, pages={'*': ['prerequisite_failed', 'provider_timeout', 'retry_dispatched']}
- **lane_rows:** `inv-1/out/LANE-B.json limit_events`; kind=provider_timeout, pool_id=SYN002 (+1 more)
- **scorer:** `inv-1/out/lane-B.r32.json documents.SYN002`; status=INCOMPLETE, pages=['*'], classes=['failure', 'retry'] (+5 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json retries[2]`; outcome=dry_refused (+1 more)

## `deferral_beyond_bound`

- **Injected:** the window frees after the elapsed bound: the deferral cannot complete, the document is INCOMPLETE. **Kinds located:** deferral_beyond_bound.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-deferral-beyond-boun-699e9f`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 INCOMPLETE, F037 COMPLETE; C: F009 INCOMPLETE, F037 INCOMPLETE; R: F009 INCOMPLETE, F037 INCOMPLETE, _reference_only INCOMPLETE]; C decision coverage denominator 6 pages, status rows {'incomplete_document_rows': 6}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.B.F009`; status=INCOMPLETE, pages={'1': ['deferral_beyond_bound']} (+2 more)
- **lane_rows:** `inv-1/out/LANE-B.json limit_events`; kind=deferral_beyond_bound, pool_id=F009, page=1, retry_at_utc=2026-10-04T11:15:37+00:00 (+2 more)
- **scorer:** `inv-1/out/lane-B.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['limit'] (+8 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=deferral_beyond_bound, page=1, retry_at_utc=2026-10-04T11:15:37+00:00 (+5 more)

## `bound_passed_while_deferred`

- **Injected:** deferred, then resumed only after the elapsed bound: the run is CLOSED INCOMPLETE. **Kinds located:** project_window.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-bound-passed-while-d-ec7355`; steps: run -> finished; resume -> refused (refused: the elapsed bound ended at 2026-10-04T10:16:23+00:00); resume -> refused (refused: the run was closed (INCOMPLETE: the deferral could not complete within the elapse).
- **Invocation 1 (fresh, finished):** run state DEFERRED; comparison DEFERRED: B documents deferred by the project window; C not started (earliest retry 2026-10-04T10:15:52+00:00); candidate outcome INCOMPLETE; earliest retry 2026-10-04T10:15:52+00:00; retry_at_full {'planning': '2026-10-04T10:15:52+00:00', 'structural': '2026-10-04T10:15:52+00:00'}; resume policy full (not before 2026-10-04T10:15:52+00:00); model requests 0; documents [B: F009 DEFERRED, F037 COMPLETE; C: F009 DEFERRED, F037 DEFERRED; P: F009 DEFERRED, F037 DEFERRED; R: F009 DEFERRED, F037 DEFERRED].
- **Invocation 2 (close, closed):** run state INCOMPLETE; comparison INCOMPLETE: the deferral could not complete within the elapsed bound; candidate outcome None; earliest retry None; retry_at_full None; resume policy None (not before None); model requests None; documents [].
- **run_state:** `inv-1/out/RUN-REPORT.json retry_at_earliest / retry_at_full / resume_not_before` (+8 more)
- **lane_rows:** `inv-1/out/LANE-B.json limit_events`; kind=project_window, pool_id=F009, page=1, retry_at_utc=2026-10-04T10:15:52+00:00
- **scorer:** `inv-1/out/lane-B.r32.json documents.F009`; status=DEFERRED, pages=['1'], classes=['limit']
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=project_window, page=1, retry_at_utc=2026-10-04T10:15:52+00:00

## `breaker`

- **Injected:** C's 1st response reports 200,000 input tokens to the FAKE ledger (per-request 100,000): its breaker opens; the next request is refused. **Kinds located:** breaker.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-breaker-1601fd`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE, _reference_only INCOMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 6}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.F009`; status=INCOMPLETE, pages={'1': ['breaker']}
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=breaker, pool_id=F009, page=1
- **scorer:** `inv-1/out/lane-C.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['limit'] (+6 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json charges[6]`; outcome=budget, page=1, ledger_entry=6 (+2 more)

## `ledger`

- **Injected:** the FAKE ledger scope allows 5 requests: B takes 4, C's 2nd request is refused by the ledger. **Kinds located:** ledger.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-ledger-5153a8`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 COMPLETE, F051 INCOMPLETE, F066 INCOMPLETE, _reference_only INCOMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 6}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.F009`; status=INCOMPLETE, pages={'1': ['ledger']} (+1 more)
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=ledger, pool_id=F009, page=1 (+1 more)
- **scorer:** `inv-1/out/lane-C.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['limit'] (+7 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json charges[6]`; outcome=budget, page=1, ledger_entry=6 (+2 more)

## `provider_timeout`

- **Injected:** C's first three requests time out: three consecutive failures make C terminal. **Kinds located:** provider_timeout.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-provider-timeout-87e2d2`; steps: run -> finished; resume -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE, _reference_only INCOMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 8}.
- **Invocation 2 (resume, finished):** run state FINISHED; comparison INCOMPLETE; candidate outcome INCOMPLETE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE, _reference_only INCOMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 8}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.F009`; status=INCOMPLETE, pages={'1': ['provider_timeout']} (+8 more)
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=provider_timeout, pool_id=F037, page=1 (+8 more)
- **scorer:** `inv-1/out/lane-C.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['failure'] (+11 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json charges[5]`; outcome=timeout, page=1 (+9 more)

## `interrupted`

- **Injected:** C's process dies inside its 2nd dispatch (no response): the row stays reserved, the charge 'dispatched'. **Kinds located:** interrupted_charged.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-interrupted-e88390`; steps: run -> error (lane C failed (75); see C:\t\r2x\r39-sandbox\vis-interrupted-e88390\inv-1\out\lane-C.log); resume -> finished.
- **Invocation 1 (fresh, interrupted):** run state None; comparison None; candidate outcome None; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [].
- **Invocation 2 (resume, finished):** run state FINISHED; comparison PENDING; candidate outcome NOT ELIGIBLE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; R: F009 INCOMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE, _reference_only COMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 4}.
- **run_state:** `inv-2/out/RUN-REPORT.json documents.C.F009`; status=INCOMPLETE, pages={'1': ['interrupted_charged']} (+1 more)
- **lane_rows:** `inv-2/out/LANE-C.json limit_events`; kind=interrupted_charged, pool_id=F009, page=1 (+1 more)
- **scorer:** `inv-2/out/lane-C.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['failure'] (+5 more)
- **audit:** `inv-2/out/ALLOWANCE-AUDIT.json charges[6]`; outcome=dispatched, page=1

## `unsaved`

- **Injected:** C's 2nd response came back (identity logged) and the process died before saving it. **Kinds located:** interrupted_charged.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-unsaved-5cbfea`; steps: run -> error (lane C failed (76); see C:\t\r2x\r39-sandbox\vis-unsaved-5cbfea\inv-1\out\lane-C.log); resume -> finished.
- **Invocation 1 (fresh, interrupted):** run state None; comparison None; candidate outcome None; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [].
- **Invocation 2 (resume, finished):** run state FINISHED; comparison PENDING; candidate outcome NOT ELIGIBLE; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; R: F009 INCOMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE, _reference_only COMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 4}.
- **run_state:** `inv-2/out/RUN-REPORT.json documents.C.F009`; status=INCOMPLETE, pages={'1': ['interrupted_charged']} (+1 more)
- **lane_rows:** `inv-2/out/LANE-C.json limit_events`; kind=interrupted_charged, pool_id=F009, page=1 (+1 more)
- **scorer:** `inv-2/out/lane-C.r32.json documents.F009`; status=INCOMPLETE, pages=['1'], classes=['failure'] (+5 more)
- **audit:** `inv-2/out/ALLOWANCE-AUDIT.json charges[6]`; outcome=dispatched, page=1

## `identity_mismatch`

- **Injected:** C's 1st response names claude-sonnet-5-1, not the pinned claude-sonnet-5: the run is INVALID. **Kinds located:** identity_mismatch, identity_invalid.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-identity-mismatch-db5b3d`; steps: run -> finished; resume -> refused (refused: the run is INVALID (model identity mismatch recorded in IDENTITY-INVALID.json); i).
- **Invocation 1 (fresh, finished):** run state INVALID; comparison INVALID: model identity mismatch (C); candidate outcome INVALID; earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: F009 COMPLETE, F037 COMPLETE, F051 COMPLETE, F066 COMPLETE; C: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE; R: F009 INCOMPLETE, F037 INCOMPLETE, F051 INCOMPLETE, F066 INCOMPLETE]; C decision coverage denominator 8 pages, status rows {'incomplete_document_rows': 8}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.F037`; status=INCOMPLETE, pages={'1': ['identity_mismatch']}
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=identity_mismatch, pool_id=F037, page=1
- **scorer:** `inv-1/out/lane-C.r32.json documents.F037`; status=INCOMPLETE, pages=['1'], classes=['limit'] (+7 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json charges[5]`; outcome=identity_mismatch, page=1 (+1 more)

## `application_path`

- **Injected:** SYNTHETIC EP-990001 documents through the application readers: a timeout on a page, then C's allowance. **Kinds located:** provider_timeout, lane_allowance.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-application-path-82d9fc`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison NOT DISPATCHABLE (EXTEND:extension-1); candidate outcome NOT DISPATCHABLE (EXTEND:extension-1); earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE; C: SYN001 INCOMPLETE, SYN002 INCOMPLETE, SYN003 INCOMPLETE; R: SYN001 INCOMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE]; C decision coverage denominator 3 pages, status rows {'incomplete_document_rows': 3}; unread pages {'B': {}, 'C': {'SYN003': {'status': 'INCOMPLETE', 'unread_page_count': 1, 'unread_pages': {'1': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: harness allowance refused (lane_allowance): lane C: its own allowance 1 is used (lanes never borrow)'}]}}}, 'R': {}}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.SYN001`; status=INCOMPLETE, pages={'1': ['provider_timeout']} (+2 more)
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=provider_timeout, pool_id=SYN001, page=1 (+2 more)
- **scorer:** `inv-1/out/lane-C.r32.json documents.SYN001`; status=INCOMPLETE, pages=['1'], classes=['failure'] (+9 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=lane_allowance, page=1 (+2 more)

## `application_project_limit`

- **Injected:** SYNTHETIC EP-990001: the application's own per-project limit lowered to 1 (dry drill only) refuses C before the harness -- the R38-08 failure mode -- and is recorded, never silent. **Kinds located:** application_project_limit.
- **Run folder:** `C:/t/r2x/r39-sandbox/vis-application-project--2a1000`; steps: run -> finished.
- **Invocation 1 (fresh, finished):** run state FINISHED; comparison NOT DISPATCHABLE (EXTEND:extension-1); candidate outcome NOT DISPATCHABLE (EXTEND:extension-1); earliest retry None; retry_at_full None; resume policy None (not before None); model requests 0; documents [B: SYN001 COMPLETE, SYN002 INCOMPLETE, SYN003 COMPLETE; C: SYN001 INCOMPLETE, SYN002 INCOMPLETE, SYN003 INCOMPLETE; R: SYN001 INCOMPLETE, SYN002 INCOMPLETE, SYN003 INCOMPLETE]; C decision coverage denominator 3 pages, status rows {'incomplete_document_rows': 3}; unread pages {'B': {}, 'C': {'SYN001': {'status': 'INCOMPLETE', 'unread_page_count': 1, 'unread_pages': {'1': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_project_per_day'}]}}, 'SYN003': {'status': 'INCOMPLETE', 'unread_page_count': 1, 'unread_pages': {'1': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_project_per_day'}]}}}, 'R': {'SYN001': {'status': 'INCOMPLETE', 'unread_page_count': 1, 'unread_pages': {'1': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_project_per_day'}]}}, 'SYN003': {'status': 'INCOMPLETE', 'unread_page_count': 1, 'unread_pages': {'1': [{'kind': 'application_document_limit', 'partial': False, 'reason': 'not read: budget: calls_per_project_per_day'}]}}}}.
- **run_state:** `inv-1/out/RUN-REPORT.json documents.C.SYN001`; status=INCOMPLETE, pages={'1': ['application_document_limit', 'application_project_limit']} (+3 more)
- **lane_rows:** `inv-1/out/LANE-C.json limit_events`; kind=application_project_limit, pool_id=SYN001, page=1 (+3 more)
- **scorer:** `inv-1/out/lane-C.r32.json documents.SYN001`; status=INCOMPLETE, pages=['1'], classes=['arm_policy', 'limit'] (+10 more)
- **audit:** `inv-1/out/ALLOWANCE-AUDIT.json refusals[1]`; kind=application_project_limit, page=1 (+3 more)

