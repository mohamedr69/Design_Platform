# Scorer changes: Review 31 `score_bcr.py` → r32 `score_bcr_r32.py` (with `lane_judge_r32.py`, `literal_compare_r32.py`, `score_lane_r32.py`)

The Review 31 file is **unchanged**:

- `review31/scripts/harness/score_bcr.py`, sha256 `5a3828a57eefe8268d32c4d4a64dd03befcbcd212355ee8906088bdfa3de7d1a`, copied byte for byte to the work folder's `harness-base/`.
- `review31/scripts/harness/score_lane.py` (`17ed2ba3…`) is also unchanged. It stays bound to the four-arm run, and the r32 run does not use it.

The r32 scorer is new code in `scripts/harness-r32/`. Every difference is listed below with its reason and the Review 33 finding it answers.

## Kept exactly from Review 31

These are the same constants, the same rule text and the same code shape:

- `MINIMUM = 12`.
- `EXTENSIONS` (extension-1, extension-2) and the population-gate actions (`DISPATCH_ELIGIBLE`, `EXTEND:…`, `PREPARATION BLOCKED`). There is no partial closure run.
- `THRESHOLDS`:
  - accepted precision ≥ 0.98;
  - clean recovery ≥ 0.90;
  - 0 critical acceptances on resolved truth in C;
  - 1 fact per 8 extra requests.
- **The unit:** the document. y(doc, f) = 1 iff there is a clean recovery (a correct asserted value and no wrong one), with `y = recovered_clean > 0 and not recovered_mixed and not wrong_only`.
- **The paired difference:** a document-cluster bootstrap stratified by project, with 2,000 resamples and seed `m2-r30-bootstrap-2026-10-02`. It uses the same `bootstrap()` code and the same verdict wording.
- **The request gate:**
  - It is defined only at equal caps. Unequal caps return `applicable: False` with the R31-03 reason.
  - Extra requests are C's total (own plus inherited from B) minus B's total.
  - It passes when `net × 8 ≥ extra`, the interval excludes zero, and there is no new false acceptance.
- **The decision coverage gate:**
  - Coverage is a completed read, or a verified absence where the truth has no decision.
  - A wrong absence and `located_incomplete` are never coverage.
  - The gate needs C ≥ B and C ≥ R.
- **The outcomes:** ELIGIBLE FOR A SEPARATE SELECTION DECISION, NOT ELIGIBLE, INCOMPLETE, INVALID and PREPARATION BLOCKED. `default_selected` is always `None`.
- **Caps for the request gate:** B 240 and C 240.

## Differences

| # | Review 31 (`score_bcr.py`) | r32 (`score_bcr_r32.py` and helpers) | Reason | Answers |
|---|---|---|---|---|
| 1 | One document-level `resolved` flag (`primary(labels, doc)`) | `primary(truth, pool, f)` per **field**: that field's `resolved_for_scoring == "yes"`, and the document is canonical and independently reviewed | F019 (revision unresolved, identity and decision resolved), F069 and F067 mix resolutions inside one document. The document-level mappings would give 57/38/38, 56/38/37 or 50/37/32 | R33-05, D4-04 |
| 2 | Page facts `{field: value or None}`, with None read as "truth absent" | A row for each (pool id, page, field) whose truth is a literal, `ABSENT` or `NOT_SCORABLE`. A missing row is `None` and means "not labelled" (`labels_adapter_r32`) | Without it, 30+ ambiguous, uncertain or excluded rows read as verified absences, and an accepted value is scored against "absent" | R33-05 |
| 3 | `has_fact`: any non-empty page value | `has_fact(truth, pool, f)`: the document review's `resolved_for_scoring` yes **and** `carries_fact` yes. This reproduces `FIELD-POPULATION.json` (57/38/38, the same ids) | A present page value can be uncertain or excluded. F069 would have been counted (D4-03) | R33-05, D4-03 |
| 4 | `coverage_counts` over every labelled page | NOT_SCORABLE rows are counted apart (`not_scorable`) and never enter coverage. `discovery_absent` on an ABSENT row is a verified absence; on a value row it is a wrong absence | "Otherwise a C `discovery_absent` counts as a verified absence" (§5.1) | R33-05 |
| 5 | The lane input is per-document counters taken from evaluator .10 (`recovery`, `accepted`, `critical`) | The lane input is a **list of emitted facts** (page, field, value, state), from the frozen evaluator .10 emission functions (`record_groups`, `observation_groups`, `ai_groups`). Each fact is judged per (pool id, page, field) by `lane_judge_r32`, using the evaluator's states (ASSERTED: accepted, observed, validated; ACCEPTANCE: accepted, validated) | The per-field truth and the NOT_SCORABLE exclusion cannot be expressed in evaluator .10's document counters. The comparison rules of the reviewed conventions have to be applied by the scorer (§4.3, C-6) | R33-05, R33-06, R33-09 |
| 6 | Value comparison inside evaluator .10 (`norm_ref`, `same_identity`, `norm_rev`, decision equality) | `literal_compare_r32.compare`, which is: whitespace-insensitive; folds hyphen, en-dash and minus variants; makes identity case-insensitive; accepts the row's either-form alternates ((g)(1) labelled tail, and the unlabelled-suffix base form carried from evaluator .10's `suffix`); compares revision numbers by value (evaluator .10 `norm_rev` parity); compares decisions by **class**, with the application vocabulary (`rejected` = revise-and-resubmit or rejected) and the (d1) resubmission tolerance; and byte-compares Arabic literals after whitespace removal only | Review 33 §4.3: "Whitespace-insensitive literals … Comparison is a scorer rule"; (d1) "define the scorer tolerance"; (g)(1) "a scorer accepts either form" | R33-09, C-6 (tested here; the evaluator itself is ORCH-06) |
| 7 | Association by evaluator .10 (identity on page, cross-page copy, single component) | Truth keyed by (pool id, page). Evaluator .10's cross-page identity copy is kept, and is neither wrong nor correct for that page, **except on compilations**, whose pages are different documents ((h)): there it is wrong. A copy of the document's identity on a page whose identity is ABSENT is never a false positive. Dependent facts (revision, decision) are judged on their own page (as in .10) | (h): "A scorer must key on (pool id, page) and never score one file-level value against a compilation" | R33-05, §5.1 Compilations |
| 8 | `critical_split`: resolved or unresolved **per document** | Per **row**. A wrong or false-positive automatic acceptance on a scorable row is a critical on **resolved** truth, attributed to (pool id, page, field). An acceptance on a NOT_SCORABLE row that matches no literal or candidate is a critical on **unresolved** truth: reported, never a stop. One that matches is reported as `not_scorable_matching`. One with no reference is `not_scorable_unjudgeable` | "The critical tripwire must classify per field, keyed by pool id. F019 revision and F069 identity must count as unresolved truth" (§5.1) | R33-05, D4-11 (stop_rules) |
| 9 | One outcome for the whole comparison, built from one `reasons_not_eligible` list | **Per-field outcomes** (`fields[f].outcome`, `outcome_by_field`), each with its own reasons. Comparison-level states (PREPARATION BLOCKED, INVALID, INCOMPLETE) apply to every field. Candidate-level gates apply to every field: a C critical acceptance on resolved truth in **any** field, a RESULT stop, and the request gate (a policy cost that cannot be split by field). Field-level gates apply only to their field: precision, recovery, matched ≥ 12 and concentration. The decision coverage gate binds only the decision field | "a concentrated gain in any field makes the **whole comparison** NOT ELIGIBLE" (R33-01, C-006) | R33-01, R33-05 |
| 10 | `concentration()`: more than half of the net gain from one project **or one stratum** | `concentration_r32` (A-05). The blocking legs are: project, contractor and layout key at net gain ≥ 4; failure concentration with a negative group net; and any false acceptance on a negative decision control. Stratum and decision type are measured and reported only. UNDETERMINED below net 4 does not block. See CONCENTRATION-RULE-R32.md | The stratum leg is unreachable for decision (37 of 38 documents are review_signal) | R33-01, C-4 |
| 11 | Every labels document counts | Canonical ids only: count-once aliases are never primary, never matched and never counted | "an alias could be drawn twice" | R33-07 |
| 12 | Metrics over every labelled document | `docs=` restricts the metrics, the matched sets and the controls to the run set | The run set is ≤ 30 documents of the 68 canonical ones | R33-06 |
| 13 | `request_gate`: per-document gain over fields with `has_fact` | Per-document gain summed over the fields **for which the document is matched** | This follows from per-field resolution (#1) | R33-05 |
| 14 | New false acceptances: criticals of C not in B (resolved and unresolved) | The same, with "unresolved" meaning only acceptances on NOT_SCORABLE rows that contradict every literal and candidate (#8) | This keeps parity with Review 31, which counted unresolved criticals | R33-05 |
| 15 | The output has no reference-set statement | Every output carries "reference set independently AI-reviewed (Claude agents), not human-signed" | AI-ACCURACY-POLICY-AMENDMENT-R32-01 requires the statement on every metric | C-3 (A-04) |
| 16 | `primary_outcomes.critical` per lane | Adds `critical_by_field` per lane | The per-field tripwire attribution | R33-05 |
| 17 | `score_lane.py`: bound to `r27/FINAL-DECLARATION.v2.json`, r26.2, `documents_planned` and final-A/L3; B always "attempted" | `score_lane_r32.py`: driven by the r32 truth and the run set (planned = `doc_key`, `staged_sha256` and `page_count`); `coverage_v4` (a harness v4.3 copy, `e260a609…`) for C and R; B is attempted when its row exists in B's sandbox. No four-arm file is read | "score_lane and run_lane are bound to the four-arm run and r26.2" | R33-06, D4-05 |

## Interpretation choices for the independent review (ORCH-05R)

These are recorded so that a reviewer can reverse each of them in one place.

- **The unlabelled-suffix base form** (#6, and ADAPTER-CONTRACT §4.5).
  - It is accepted as a correct identity, following evaluator .10.
  - Reversing it changes `labels_adapter_r32._suffix_base`.
- **Candidate-level gates apply to all fields** (#9).
  - A C critical on resolved truth in one field makes every field NOT ELIGIBLE. It is a safety gate on the candidate as a whole, and the stop rule ends C at the first one anyway.
  - The request gate is also comparison-wide.
- **Cross-page identity** (#7) is kept from evaluator .10 except on compilations.
- **The decision vocabulary** (#6): an application `rejected` matches truth `revise and resubmit` as well as `rejected`, because the application has no separate code for revise-and-resubmit.
