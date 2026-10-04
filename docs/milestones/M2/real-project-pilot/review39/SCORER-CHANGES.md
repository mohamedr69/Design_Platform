# Scorer changes, version 4: review38 -> review39 (`score_bcr_r32.py`, `score_lane_r32.py`, `run_state_r38.py`)

**Earlier versions:**
- Version 3 is `review38/SCORER-CHANGES.md` (review36 -> review38). Its Parts A to C still describe every rule this scorer keeps, except where Part B below changes them.
- Version 2 is `review34/SCORER-CHANGES.md`.

**Changed modules:** `run_state_r38.py` is the document-status rule the scorer carries.
**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (`r32-labels-reviewed-2`, `89c60e9d…b9a6`).
**Results:** none. Nothing here is a result, and no prediction exists.

## Part A. Unchanged from review38 (by hash)

These modules are byte-identical to review38: `lane_judge_r32.py` (with rule CP-R38), `page_relations_r38.py`, `tripwire_r32.py`, `literal_compare_r32.py` (with the H1 fix), `labels_adapter_r32.py`, `concentration_r32.py` (with rule v2), `converter_r32.py` and `coverage_v4.py`.

All other review38 scorer rules stay as they were:
- the population gate;
- the document as the unit;
- the bootstrap;
- the request gate at equal caps;
- the thresholds: precision >= 0.98, clean recovery >= 0.90, 0 resolved criticals in C, matched >= 12;
- NOT_SCORABLE exclusion;
- R and P without credit;
- limit refusals and deferrals INCOMPLETE and visible;
- the declared unsupported-control shortfall;
- the candidate-level outcome reading B and C only;
- `default_selected` always None.

**Every safety, accuracy and completeness gate other than the decision coverage gate is unchanged.**

## Part B. review39 changes

| # | Module | Change | Finding / authority |
|---|---|---|---|
| 1 | `score_bcr_r32.py` | **The decision coverage gate is C >= B only. This is a CHANGE FROM PLAN V2, not an unchanged gate.**<br>• Plan v2 (`review31/REVISED-FRESH-VALIDATION-PLAN.v2.md`) gated decision coverage on C >= B **and** C >= R.<br>• review38 removed the C >= R leg from eligibility (version 3, Part B row 6). The owner ruled it on 2026-10-04 (A-10): "Bind decision coverage eligibility to C ≥ B only".<br>• The gate is now one named constant, `DECISION_COVERAGE_GATE = "C_GE_B_ONLY"`, carrying its text, its source and its `change_from_plan_v2` statement (`DECISION_COVERAGE_GATE_DEFINITIONS`).<br>• `PLAN_V2_DECISION_COVERAGE_GATE` keeps plan v2's text for the record.<br>• Any definition that binds R into eligibility (plan v2's `C_GE_B_AND_C_GE_R`, or any other) is **refused**: `refuse_r_in_eligibility`, called by `evaluate()` and `decision_coverage_gate()`, raises.<br>• The declaration contract refuses it too: `decision_coverage_gate` must be `C_GE_B_ONLY`.<br>• The gate result names its definition, its change from plan v2 and `reads_lanes: ["B", "C"]`. | R39-15; owner ruling A-10 item 1 |
| 2 | `score_bcr_r32.py` | **C >= R is a MANDATORY diagnostic in every result** (`result["decision_coverage_C_ge_R"]`, from `c_ge_r_diagnostic`):<br>• `mandatory: true`, `determines_eligibility: false`, `credit: "none"`;<br>• the counts of C and of R (coverage, completed reads, verified and wrong absences, other classes, scorable pages);<br>• both coverages, and `holds` (only when the diagnostic is COMPLETE);<br>• `missing_coverage`: per document, per page, each lane's coverage class, whether it is covered, the reason, and both lanes' document statuses;<br>• `C_missing_where_R_covered`.<br>The diagnostic is **INCOMPLETE** (`holds: null`) when R did not complete its declared population: deferred, refused, INCOMPLETE, absent, or not run. `why_incomplete` lists every reason. `report_template()` renders all of it. | owner ruling A-10 item 1 |
| 3 | `score_bcr_r32.py`, `score_lane_r32.py`, `run_state_r38.py` | **Pages the application did not read under its own per-document limits.**<br>• Covered: the reader's own call cap (`MAX_CALLS_PER_DOCUMENT` 8, checked between pages), the per-document JobBudget (12 calls / 120 s), and a reader exception.<br>• These are class `arm_policy`. The document stays **COMPLETE**, with `unread_pages` ({page: [{kind, reason, partial}]}), `unread_page_count` and `partially_read_pages` carried into every normalised lane.<br>• `result["unread_pages"]` reports, per lane, the documents with unread pages and the pages.<br>• The pages stay in every coverage denominator, where `coverage_v4` classes their fields `budget` / `missing_page` / `not_attempted`, so they count as unread and never as coverage.<br>• **Before (review38):** an `application_document_limit` event turned the document INCOMPLETE, and the reader-cap skips and the reader exceptions were not recorded at all.<br>• Harness and resource refusals (classes `limit` and `failure`) still make a document INCOMPLETE. | R39-06; A-09 point 1 |
| 4 | `run_state_r38.py` | New event kinds:<br>• `undeclared_task_kind`, `missing_context`, `contract_breach_invalid` (class `limit`: a contract breach makes the run INVALID; `classify` returns `contract_breach`, never `provider_failure`, so it never counts toward a failure streak);<br>• `application_reader_cap`, `application_reader_exception` (class `arm_policy`);<br>• `retry_dispatched` (class `retry`: visibility only; it never changes a status).<br>Every normalised document carries `retries`. | R39-04, R39-06, R39-16 |
| 5 | `score_bcr_r32.py` | `report_template()` gains three sections:<br>• the decision coverage gate, stated as changed from plan v2;<br>• the mandatory C >= R diagnostic, with counts and per-document reasons when a result is given, and the field list otherwise;<br>• the unread-pages rule. | A-10; R39-06 |

## Part C. Not changed

- **No accuracy rule changed:** literal comparison, the judge, CP-R38, concentration, thresholds, bootstrap and the request gate are all as before.
- **No fixture verdict changed.** The cross-page what-if of review38 (`review38/CROSS-PAGE-WHATIF.json`, `491f9590e775fa5367569787cbc3394d8db1b82908f5f6111a2a7491da8c6fe6`, bound in `BINDING-MANIFEST-R38.json`) stands; this package does not re-issue it.
