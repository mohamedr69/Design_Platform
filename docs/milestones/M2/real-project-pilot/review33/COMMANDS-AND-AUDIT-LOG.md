# Commands and audit log (review33, ORCH-05.1, agent R33HARNESS-IMPL)

**Times.** All times are UTC. The machine's local time is UTC+4.

- Entries marked "(log)" were appended when they happened, by `audit.py`, to `C:/t/iso/work/r2x/r33/COMMANDS-AND-AUDIT-LOG.work.md`.
- The other entries are reconstructed from the session's tool output. They carry the time printed by the command, or the time the file was written.

**Python.** Every command used the backend venv Python with `PYTHONDONTWRITEBYTECODE=1`.

**What never happened:**

- No command sent a provider or model request.
- No command opened the AI ledger other than with `mode=ro`.
- No command wrote under the frozen trees.

**Read-only inputs** (read with `cat`, `sed`, `grep` and the Read tool; they are not repeated per file below):

- NEXT-BOUNDED-TASK.md, AUTHORITY-REGISTER.md, and Review 33 (`INDEPENDENT-REVIEW.md`, `dimensions/D4-report.md`, `D4-findings.json`).
- review31: the plan v2, STOP-AND-SAFETY-RULES, FIELD-POPULATION-FEASIBILITY.v2, COMMANDS, DRY-RUN-REPORT, DRAFT-DECLARATION.v2, BINDING-MANIFEST, and `scripts/harness/*`.
- reviewed-2 labels and FIELD-POPULATION.
- Packet: RENDERS, SOURCE-MANIFEST, FROZEN-SELECTION, PROJECT-VERIFICATION, EVIDENCE-INDEX (structure), LABEL-CONVENTIONS-R32, and the drafting helpers `scripts/lib/*.py`.
- The policy and its amendment, and the tail of the response ledger.
- **Read for format only:**
  - the candidate's `scripts/m2_eval6.py`, `m2_eval4.py` and `m2_pilot_eval.py`, its `app/ai/provider.py`, and the decision vocabulary in `app/ai/evidence_reader.py` and `app/services/document_control.py`;
  - the baseline's `app/models.py`, `app/services/document_sync.py`, `app/services/document_processing.py`, `app/main.py`, `app/database.py` and `app/core/config.py`;
  - the four-arm runner code (`review25/harness-v4.3/arm_a.py`, `arm_ev.py`, `coverage_v4.py`; `review22/harness-v4/dry_provider2.py`; `r16/boq_harness.py`), and `run-final` `final-A/out/RUN.json` (timing and settings keys only).
- **Never opened:** the r26.2 label values, the four-arm arm outputs' values, and `review31/dry-run/LABELS-NORMALISED.json`.

| UTC | Command | Result |
|---|---|---|
| 10:27:08 | `sha256sum` of the 8 frozen inputs; `git rev-parse` / `git status` of cand-r29 and frozen-r12 | all equal to the task's values; cand-r29 `a8aacedd…` clean; frozen-r12 `3d5607d9…` clean |
| 10:27:10 | `mkdir C:/t/iso/work/r2x/r33/{harness-base,harness-r32}` and the scratchpad `r33harness/` | created |
| 10:27:30 | `python -c` (sqlite `mode=ro`) ledger schema | tables entries, scopes, limit_amendments |
| 10:27:40 | `python preflight_inputs.py` (log) | PACKET OK: hashes equal; manifests 58/43/110, 0 mismatches; ledger 483/17; response `da5cc798…` |
| 10:28–10:35 | label and packet structure inspections (`python -c`, `inspect_labels.py` in the scratchpad) | counts only, recorded in ADAPTER-CONTRACT |
| 10:36:12 | `cp -p review31/scripts/harness/* r33/harness-base/`; `sha256sum` (log) | 11 files, hashes equal to review31 BINDING-MANIFEST |
| 10:36–10:46 | wrote `inputs_r32`, `labels_adapter_r32`, `literal_compare_r32`, `lane_judge_r32`, `concentration_r32`, `score_bcr_r32` and their tests | — |
| 10:40–10:46 | `python -m pytest -q test_literal_compare_r32.py` (13), `test_labels_adapter_r32.py` (13), `test_score_bcr_r32.py` (16), `test_concentration_r32.py` (12); two literal-compare test failures fixed (the application word `rejected`) | all pass (log 10:46:48) |
| 10:47–10:51 | wrote `run_set_selector_r32` and `converter_r32` with their tests; `python -m pytest` (8, 7) | pass after two fixes (shortfall semantics; absent kind kept on no-record pages) |
| 10:51:38 | `cp -p harness-base/{capture_store,stop_rules,state_check}.py` and their tests to `harness-r32/` (log) | byte-identical copies |
| 10:52:27 | `sandbox_ingest_r32.ingest('C:/t/r2x/r33-sandbox/try-1', [F001, F032, F045])` | failed: `projects.created_by_id` NOT NULL |
| 10:52:40 | the same after seeding the application's default admin in the child (sandbox `try-1` recreated) | ok: 3 PENDING, 0 processing rows, state check ok; frozen-r12 `git status` clean, no new file |
| 10:53–11:00 | wrote `dispatch_guard_r32`, `allowance_r32`, `tripwire_r32`, `lane_r32`, `score_lane_r32` and `runner_r32`; copied `coverage_v4.py` (harness v4.3, `e260a609…`) | — |
| 11:00 | `python make_binding_r33.py <scratch>/BINDING-DEV.json <scratch>/RUN-SET-DEV.json`; `python runner_r32.py --mode dry --stamp dev-1 … --resume-drill --out <scratch>/runs/dev-1` | dev trial: 0 model requests, ledger 483/17, resume drill passes |
| 11:04 | synthetic application-path trial `syn-1` (`runner_r32.execute`, reader application, generated PDFs of EP-990001) | B processed 2 synthetic documents, the tripwire ran after each, C/R ran, 0 model requests |
| 11:05–11:10 | wrote `synthetic_r32` and the tests for the guard, allowance, ingestion, tripwire and runner; `python -m pytest` (16 + 10 + 8) | all pass |
| 11:07:27 | (log) | modules and trial runs recorded |
| 11:08 | `ls`/`find` on `C:/t/iso/tmp` (background, stopped), then an `os.scandir` check | 0 entries newer than the task start: nothing written there |
| 11:09 | `sandbox_ingest_r32.sandbox_env` TEMP/TMP moved into the sandbox; P lane and scorer databases moved under the sandbox | — |
| 11:10:37 | lane judge: cross-page identity (evaluator .10, not on compilations) and negative decision words; `test_lane_judge_r32.py`; re-ran the copied review31 tests (log) | 7 + 16 + 12 + 5 pass; stop_rules 8, state_check 5, capture_store 21 (from the cand-r29 cwd) pass; cand-r29 clean |
| 11:10:39 | wrote `prepare_r33.py`, `make_binding_r33.py`, `dry_run_r33.py`; scenario preview (log) | S1 to S6 as reported |
| 11:12 | `os.walk` of cand-r29, frozen-r12, r32-stage, r32, r32b and r32c | 0 files newer than 2026-10-03T10:30:00Z |
| 11:14 | `mkdir` of the package `review33/{dry-run,tests,evidence,scripts}`; wrote ADAPTER-CONTRACT, SCORER-CHANGES, CONCENTRATION-RULE-R32 and RUN-SET-RULE | — |
| 11:18:29 | `python prepare_r33.py` (log) | TRUTH `4e237a4e…`, EVAL-INPUT `4b2c73d5…`, RECON `e350d2fe…`, RUN-SET `9058f3d6…` |
| 11:19:14 | copy into `scripts/`; `python make_binding_r33.py` (log) | `03464adf…` (superseded below) |
| 11:19:14–11:19:40 | `python dry_run_r33.py r33dry-20261003a …` | passed, but the runner's JSON files were CRLF: **SUPERSEDED** (log 11:21:58). Its package outputs were removed; the sandboxes `r33dry-20261003a` and `-all72` are kept, unused |
| 11:20–11:21 | fix: LF on every `write_text` (28 calls). A bash heredoc turned the escape into a line break, which was repaired by the scratchpad `fix_newline.py`. `py_compile` created `harness-r32/__pycache__`, which was removed. Full suite re-run: `python -m pytest` (14 modules) | 123 pass |
| 11:21:58 | removed the superseded package outputs and the old binding; re-copied `scripts/`; `python prepare_r33.py` (byte-identical outputs); `python make_binding_r33.py` (log) | BINDING-MANIFEST-R33 `d1a8a401…53936e`, 68 files |
| 11:22:08–11:22:33 | `python dry_run_r33.py r33dry-20261003b <package>/BINDING-MANIFEST-R33.json d1a8a401…` (log) | PACKET OK; ingest 72 ok; runner dry (reader none) ok; resume drill passes; 0 model requests; ledger 483/17/0 before and after |
| 11:22:49 | `python run_tests_r33.py <package>/tests <scratch>/pytest-junit` | SUPERSEDED: the pytest basetemp parent was missing (48 setup errors, no test failure); the XMLs were removed (log) |
| 11:23:33–11:24:45 | `python run_tests_r33.py <package>/tests <scratch>/pytest-junit2` (log) | 15 junit files, 144 tests, 0 failures, 0 errors; cand-r29 clean |
| 11:25–11:35 | wrote DRY-RUN-REPORT.md, COMMANDS.md, CORRECTION-REPORT.md, this log, `verify_review33_package.py`, `package_r33.py` and `append_response_r33.py`; copied them to `scripts/` | — |

**Final steps, after this log was written.** They are recorded in the work log, the package check, the manifest and the response entry:

1. `python verify_review33_package.py`, which writes `evidence/PACKAGE-CHECK.json`.
2. `python package_r33.py`, which writes `evidence/EVIDENCE-MANIFEST.json`, last.
3. `python append_response_r33.py`, which adds one entry at the end of `M2-REVIEW-RESPONSE.md`, after verifying `da5cc798…`.

**Sandboxes created** (all under `C:/t/r2x/r33-sandbox/`):

- `try-1`;
- `dev-1`;
- `syn-1`;
- `r33dry-20261003a` and `r33dry-20261003a-all72` (superseded);
- `r33dry-20261003b` and `r33dry-20261003b-all72`;
- `tests/*` (test runs).

None holds a reading of a cohort document. The synthetic ones hold readings of generated PDFs only.
