# Correction report: review33 (ORCH-05.1). r32 harness adapter, per-field scorer, C-4 concentration rule, run-set selector, guarded runner

| | |
|---|---|
| **Task** | ORCH-05.1 (NEXT-BOUNDED-TASK ORCH-05) |
| **Agent** | R33HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High. A fresh, isolated agent, and the only write-capable agent running |
| **Authorities** | A-03 (Claude-only workflow), A-05 (owner decision C-4) and A-08 (the authorized sequence) |
| **Date** | 2026-10-03 |
| **Answers** | Review 33 (`8d20baec…7804`) conditions **C-4** (findings R33-01 and D4-07) and **C-5** (R33-05, R33-06 and R33-07; D4-04, D4-05 and D4-08) |
| **Approval** | Nothing here is self-approved. The package goes to the independent read-only review **ORCH-05R** |
| **Reference set** | Independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01) |

## 1. Index

| File | What it is |
|---|---|
| `ADAPTER-CONTRACT.md` | The schema and every mapping decision of `labels_adapter_r32` (reviewed-2 → per (pool id, page, field) truth, the NOT_SCORABLE sentinel, the layout-key rule) |
| `SCORER-CHANGES.md` | Every difference between review31 `score_bcr.py` (unchanged) and `score_bcr_r32.py` and its helpers, each with its reason and finding (17 rows) |
| `CONCENTRATION-RULE-R32.md` | The C-4 replacement rule (A-05): what it measures, its thresholds and their justification, and reachability |
| `RUN-SET-RULE.md`, `RUN-SET-PROPOSAL.json` | The executable plan v2 §2.3 rule, and the proposal (24 documents; unsupported controls short by 2). It is frozen only by ORCH-07 |
| `LABELS-R32-EVAL-INPUT.json`, `CONVERTER-RECONCILIATION.json` | reviewed-2 in the evaluator .10 input format (register, page, uncertainty, planned, sidecar), and the row reconciliation (432 = 417 mapped + 15 excluded) |
| `DRY-RUN-REPORT.md`, `dry-run/` | The dry run: TRUTH-R32, ingestion of 72, runner dry with the resume drill, synthetic scorer scenarios, the guard check, and the ledger before and after |
| `BINDING-MANIFEST-R33.json` | The binding (68 files: inputs, harness-base, harness-r32 sources and tests, the run-set proposal), plus HEADs, policy and amendment |
| `scripts/harness-r32/` | The new and copied harness code (37 files). It is byte-identical to the bound work-folder copy |
| `scripts/*.py` | Preflight, prepare, binding, dry run, tests, package check, manifest and response append |
| `tests/*.xml` | junit, one file per module: 15 files, 144 tests, 0 failures |
| `COMMANDS.md`, `COMMANDS-AND-AUDIT-LOG.md` | How to re-run everything, and every command in UTC |
| `evidence/PACKAGE-CHECK.json`, `evidence/EVIDENCE-MANIFEST.json` | The package checker's result, and the manifest, which is written last |

**Modules and tests:**

| Module | Purpose | Tests |
|---|---|---|
| `labels_adapter_r32.py` | truth per (pool id, page, field); NOT_SCORABLE / ABSENT / None; aliases; compilations; document attributes | 13 |
| `literal_compare_r32.py` | whitespace, dashes, either-form tails, decision vocabulary and (d1) tolerance, Arabic bytes, revision by value | 13 |
| `lane_judge_r32.py` | per-row judgement, cross-page identity, unresolved findings, coverage | 7 |
| `score_bcr_r32.py` | the Review 31 rules per field, with the per-field tripwire and per-field outcomes | 16 |
| `concentration_r32.py` | the C-4 rule (A-05) | 12 |
| `run_set_selector_r32.py` | plan v2 §2.3 | 8 |
| `converter_r32.py` | evaluator .10 input, round trip and reconciliation | 7 |
| `dispatch_guard_r32.py` | the only provider path; refuses without the owner's authorization | 11 |
| `allowance_r32.py` | the durable lane caps (240/240/40/36) and the project-day limit (60) | 5 |
| `sandbox_ingest_r32.py`, `sandbox_child_r32.py` | B sandbox, registration without processing, state check | 5 |
| `tripwire_r32.py` | fact extraction by the frozen evaluator .10 emission functions; per-field criticals | 5 |
| `runner_r32.py`, `lane_r32.py`, `score_lane_r32.py`, `synthetic_r32.py` | the guarded runner B/C/R/P, the lane subprocesses, the offline lane scorer | 8 |
| `capture_store.py`, `stop_rules.py`, `state_check.py` (unchanged review31 copies), `coverage_v4.py` (an unchanged harness v4.3 copy) | the capture contract, the stop rules and the C-from-B check | 21 + 8 + 5 |

## 2. What changed compared with review31

**review31 itself is unchanged.** Its 58-file manifest re-verifies. Its harness is copied byte for byte to the work folder's `harness-base/`, and the hashes equal review31's BINDING-MANIFEST.

**New:**

- **Per-field truth and exclusion (R33-05).** The adapter gives per-field `resolved_for_scoring`, a NOT_SCORABLE sentinel distinct from None and from ABSENT, and an exclusion for each page-field.
- **Scoring (R33-01, R33-05).** There is a per-field scorer and tripwire. Outcomes are per field. Comparison-level states and candidate-level gates are applied to every field; field-level gates only to their own field.
- **Concentration (C-4, A-05).** The stratum leg is replaced by the project, contractor, layout, failure and negative-control legs. Decision type and stratum are reported only.
- **Run set (R33-07).** The run-set selector uses canonical ids only, with executable negative and unsupported controls and a recorded shortfall.
- **Converter.** reviewed-2 is converted into the evaluator .10 format, with a reconciliation. What .10 cannot express goes in a sidecar for ORCH-06.
- **Ingestion.** The B sandbox is ingested by the baseline tree's own discovery, without processing.
- **The guarded runner (R33-06).** It is not bound to the four-arm run, and it runs B/C/R/P per plan §4. It has:
  - preflight against the binding manifest and the declaration hash;
  - the per-field tripwire after every B and C document;
  - C-from-B and R-from-B state checks;
  - capture store, durable allowance and stop rules;
  - P probe;
  - offline scoring.
  - The provider path is reachable only through `dispatch_guard_r32.authorize()`.
- **The resume contract.** A reserved request without an answer is charged, served `interrupted_charged`, and never re-sent. The resume drill shows 0 re-sends.

**Interpretations recorded for ORCH-05R** (each is reversible in one place):

- **The unlabelled `- R0n` suffix base form** is accepted as a correct identity. This carries the evaluator .10 `suffix` equivalence (ADAPTER-CONTRACT §4.5).
- **Candidate-level gates** apply to every field. These are a C critical on resolved truth and the request gate.
- **Cross-page identity** follows evaluator .10, except on compilations.
- **F069 p2 and p4 identity** are NOT_SCORABLE because the document field is unresolved. That gives 32 rows, against Review 33's count of 30.

## 3. Explicitly out of scope

- **Evaluator .10 changes and its offline zero-call test (ORCH-06, C-6).** The converter's sidecar lists what .10 cannot express: 7 (d1) decision alternatives, 20 identity alternates, and 0 suffix-revision divergences.
- **The declaration (ORCH-07, C-7).** The lane switches and provider environment for live mode come from it. The defaults here are the DRAFT-DECLARATION.v2 arms, and the run set is frozen only by it.
- **Any dispatch.** No provider or model request, prediction, ledger scope or budget. `OWNER-DISPATCH-AUTHORIZATION.json` was **not** created.
- **Any change** to the labels, the frozen packages, the candidate or baseline trees, the application or production data.

## 4. Statuses, stated separately

1. **Source permission and verification.**
   - A-02 (access, staging, drafting and preparation) and A-06 (project and provider **eligibility** for EP-3563, 22349, 27331, 15744, 26687 and 29255) are unchanged. Neither authorizes dispatch.
   - Verification stands at 10 of 10, with no replacement. The 72 staged files re-hash to SOURCE-MANIFEST.
2. **Label drafting.** `r32-labels-draft-1` (`ebd1e24d…a334`) is frozen. It is AI-drafted (Claude Opus 5.5) and not human-signed.
3. **Independent label review and reference-set status.**
   - The review is the owner-delegated independent Claude AI review, with the Review 33 rulings applied as `r32-labels-reviewed-2` (`89c60e9d…b9a6`; package manifest `1f27a544…db76`).
   - Under AI-ACCURACY-POLICY-AMENDMENT-R32-01 (`815d43fd…5de6`; policy `7efa891b…4f47` unchanged) it is an **AI-reviewed reference set**: independently AI-reviewed and not human-signed. It is not human Golden Truth.
4. **Field populations.** Identity 57, revision 38, decision 38. The adapter reproduces them with identical ids. 0 extensions were used.
5. **Preparation gate and Review 33 conditions.**
   - The pool gate (each field ≥ 12) is met.
   - **C-4 and C-5 are answered by this package, pending the independent review ORCH-05R.**
   - C-1, C-2, C-3 (A-04) and C-9 (A-06) are recorded by earlier tasks or owner decisions.
   - C-6 is ORCH-06, C-7 is ORCH-07, and C-8 is carried into the declaration.
6. **Live-run authorization and budget.**
   - **None.** No owner dispatch authorization exists, and the guard refuses.
   - No budget, ledger scope or dispatch.
   - The AI ledger was opened read-only only and reads 483 entries, 17 scopes and 0 amendments, before and after.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.
