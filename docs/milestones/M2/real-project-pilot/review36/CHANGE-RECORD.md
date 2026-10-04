# Change record (review36, ORCH-06C): H1 whitespace fix in `literal_compare_r32.norm_revision`

- **Task:** ORCH-06C, the bounded harness fix for H1 required by Independent Verification 36 (finding R36-08, condition 1 for ORCH-07).
- **Agent:** R36HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High, self-reported from my system context. A fresh, isolated implementation agent; the only write-capable agent running.
- **Authorities:** A-03 and A-08.
- **Date:** 2026-10-03 (work from 15:14 UTC; this record written 15:56 UTC).
- **Nature:** a correction package, **pending ORCH-06CV** (Verification 37, independent read-only check). It is not self-approved and authorizes nothing: no run, budget, ledger scope, default variant, M2 acceptance or M3.
- **Standing status:** M2 is **CHANGES STILL REQUIRED**. M3 has **not started**.
- **Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (`r32-labels-reviewed-2`, `89c60e9d…b9a6`).

## 1. The finding (R36-08, major, CONFIRMED)

Verification 36 found that `norm_revision` collapses internal whitespace to one space but never removes it before the revision pattern is matched. A correct letter-spaced reading (`0 1` for a printed `01`, `0 0` for `00`) therefore did not normalise to `R1` / `R0` and was scored as a critical false acceptance on resolved truth, firing the per-field tripwire. This is contrary to convention ruling (i2) ("the scorer compares whitespace-insensitively") and to the module's own docstring. It is reachable through C's AI path (`evidence_reader.validate_value` keeps the literal), not through B's deterministic readers. Scope: the 53 `ws_inside_number` truth rows (23 in the run set). Verification 36's what-if: exactly 53 of 42,804 row verdicts change and 0 wrong-value controls are newly accepted.

## 2. The change

- **`literal_compare_r32.py`:** review34 `ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6` -> r36 `c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09`. Only `norm_revision` changes.
- **`test_literal_compare_r32.py`:** review34 `1d91cb5443ac5258b3fc60268b80a2815517badb5ebf5c77a3d0bf6b62831e4e` -> r36 `66e0ddcf92ae4aaf350ca1143ad4f22f62ab777e12700c978652b276fdbb34c6`. 35 tests are appended; the review34 file is an exact byte prefix, so its 13 tests are unchanged.
- **Every other file:** the other 38 of 40 harness files are byte-identical to `PILOT/review34/scripts/harness-r32/` (review34 manifest `64d5ba0d…7a86`); the package check re-hashes all 40.

**What the function now does.** It keeps the unchanged steps: the Arabic branch (`norm_text` only), dash folding, upper-casing and whitespace collapsing. It then matches the optional prefix first, with the same alternatives in the same order as the review34 pattern (`REVISION`, `REV.`, `REV`, `R.`, `R`). It removes **every** whitespace character after the prefix, and only then matches the number pattern `0*(\d+)`, read by value. The non-numeric fallback is unchanged (every whitespace character removed). The module docstring is unchanged and is now accurate for revisions too. A function docstring was added.

**Why nothing else changes.** For any value the review34 pattern matched, the prefix it used is the one the r36 `re.match` picks: no other alternative leaves whitespace or digits after it. The remainder was whitespace, zeros and digits, so the r36 function returns the same `R<n>`. Values the review34 pattern did not match either stay on the unchanged fallback, or now match only because whitespace sat inside the number. `test_h1_only_values_with_inner_whitespace_change` checks this on every revision string in the fixtures and the truth.

```diff
--- review34/scripts/harness-r32/literal_compare_r32.py
+++ review36/scripts/harness-r32/literal_compare_r32.py
@@ -66,12 +66,19 @@
 
 
 def norm_revision(value) -> str:
+    """A revision compared by value. Arabic literals: norm_text only (whitespace removed; no case or dash folding).
+    Otherwise dash variants are read as '-' and the value is upper-cased; then, after an optional REVISION / REV /
+    REV. / R / R. prefix, EVERY whitespace character inside the value is removed before the number is matched ((i2);
+    ORCH-06C, Verification 36 R36-08), and a number is read by value: '0 1' == '01' == 'REV 0 1' == 'R 01' -> 'R1',
+    '0 0' -> 'R0', 'Rev. 0 2' -> 'R2'. A value that is not a number keeps its own characters with every whitespace
+    character removed ('A 1' -> 'A1')."""
     s = "" if value is None else str(value).strip()
     if is_arabic(s):
         return norm_text(s)
     s = _DASH_RE.sub("-", s).upper()
     s = _WS_RE.sub(" ", s).strip()
-    m = re.fullmatch(r"(?:REVISION|REV\.?|R\.?)?\s*0*(\d+)", s)
+    prefix = re.match(r"(?:REVISION|REV\.?|R\.?)?", s)
+    m = re.fullmatch(r"0*(\d+)", _WS_RE.sub("", s[prefix.end():]))
     if m:
         return f"R{int(m.group(1))}"
     return _WS_RE.sub("", s)
```

| Value | review34 `norm_revision` | r36 `norm_revision` |
|---|---|---|
| `0 1` | `01` | `R1` |
| `0 0` | `00` | `R0` |
| `REV 0 1` | `REV01` | `R1` |
| `R 01` | `R1` | `R1` |
| `Rev. 0 2` | `REV.02` | `R2` |
| `R 0 0` | `R00` | `R0` |
| `1 0` | `10` | `R10` |
| `0 1 2` | `012` | `R12` |
| `0\xa01` | `01` | `R1` |
| `01` | `R1` | `R1` |
| `Rev. 0` | `R0` | `R0` |
| `REV 01` | `R1` | `R1` |
| `Revision 1` | `R1` | `R1` |
| `R EV 1` | `REV1` | `REV1` |
| `A 1` | `A1` | `A1` |
| `0-1` | `0-1` | `0-1` |
| `\u0660 \u0661` | `\u0660\u0661` | `\u0660\u0661` |

## 3. Tests

**New tests** (appended to `test_literal_compare_r32.py`; the fixtures `SYNTHETIC-PREDICTIONS.json` `9f3e0e56…f774` and `TRUTH-R32.json` `4e237a4e…e064` are read-only and hash-checked):
- `test_h1_the_task_examples`: `0 1`, `0 0`, `REV 0 1`, `R 01` -> `R1` / `R0`; `Rev. 0 2` -> `R2`.
- `test_h1_whitespace_inside_a_revision_number_is_removed_before_the_parse` (14 cases): spaces, NBSP, tab and thin space inside the number, with each prefix.
- `test_h1_adversarial_values_stay_different` (13 cases):
  - a digit inserted with spaces: `0 1 2` against `01`;
  - the digits in another order: `1 0` against `01`;
  - whitespace inside the prefix: `R EV 01`;
  - dashes, which are not whitespace;
  - letters.
- `test_h1_non_numeric_values_keep_the_fallback`: `A 1` == `A1` by the unchanged fallback.
- `test_h1_arabic_revision_handling_is_unchanged`.
- `test_h1_only_values_with_inner_whitespace_change`: parity with a verbatim copy of the review34 function on every value without inner whitespace.
- `test_h1_the_53_ws_inside_number_rows_now_equal_their_truth`: literal comparison and `lane_judge_r32`, states accepted and validated, `recovered_clean`, 0 critical.
- `test_h1_every_wrong_value_control_keeps_its_frozen_verdict`: all 1,636 controls. The literal comparison and the judge outcome, criticals, cross-page count and match kinds equal the frozen expectation in both states.
- `test_h1_every_revision_wrong_value_control_is_still_a_critical`: 488 controls.
- `test_h1_not_scorable_rows_stay_excluded_and_never_read_as_absent`: 121 fixtures.

**The new tests detect the defect.** Run against the review34 modules, the r36 test file gives 16 failures in 48 tests (`tests/new-tests-on-review34-module/`). The failing tests are exactly the H1-sensitive ones: `test_h1_only_values_with_inner_whitespace_change`, `test_h1_the_53_ws_inside_number_rows_now_equal_their_truth`, `test_h1_the_task_examples`, `test_h1_whitespace_inside_a_revision_number_is_removed_before_the_parse`. On the r36 module all 48 pass.

| Run | Tree | Modules | Tests | Failures | Errors | Guard refusals |
|---|---|---|---|---|---|---|
| Whole review34 suite + new tests (`tests/`) | test-run twin of the bound copy | 16 | 280 | 0 | 0 | 0 |
| Sandbox-free modules (`tests/bound-copy/`) | the bound copy itself | 14 | 247 | 0 | 0 | 0 |

The whole-suite count is 280 = 245 review34 tests + 35 new tests.

**Disclosure: the test-run twin.** The review34 suite hard-codes the sandbox base `C:/t/r2x/r34-sandbox`, and `test_runner_r32` and `test_sandbox_ingest_r32` create sandboxes there. This task may write sandboxes only under `C:/t/r2x/r36-sandbox/`, and it may change no module other than `norm_revision`. So the whole suite ran from `harness-r32-suite-twin/`. That twin equals the bound copy with only the string `C:/t/r2x/r34-sandbox` -> `C:/t/r2x/r36-sandbox`: 15 occurrences in 8 files (`lane_r32.py`, `preflight_r32.py`, `r32_test_helpers.py`, `runner_r32.py`, `sandbox_child_r32.py`, `test_preflight_r32.py`, `test_runner_r32.py`, `test_sandbox_ingest_r32.py`). It was verified byte for byte before each run and again by the package check. `literal_compare_r32.py`, its test and `lane_judge_r32.py` are identical in the twin and the bound copy. The 14 modules that create no sandbox also passed from the bound copy itself. The twin is not bound and not packaged as harness code.

**Write guard.** Every pytest process loaded `scripts/pytest-plugins/r36_write_guard.py`, an audit hook that refuses writes outside the basetemp, the junit folder and (for the twin) the r36 sandbox, and refuses network connections.
- Two early attempts were aborted by the guard before any test ran: pytest's capture file in the system TEMP, then the null device. Both are now handled.
- One twin run had 10 failures caused only by the guard refusing extended-length paths (`\\?\c:\t\r2x\r36-sandbox\…`) inside the allowed sandbox. The guard now strips that prefix, and the repeat had 0 failures.
- The summaries of that twin run and of the first bound-copy run (made with the earlier guard version, also 0 failures) are in `evidence/superseded/`; the packaged junit is from the repeats with the final guard. The audit log records every attempt.

## 4. The what-if, reproduced (`H1-WHATIF-RESULT.json`)

**Two re-executions on the frozen fixtures (4,805 SYNTHETIC values, none a model prediction):**
- **Row level** (`judge_all_rows_r36.py`): every labelled row of each fixture's document, judged with the review34 harness (imported in place, read-only) and with the r36 harness, in both automatic-acceptance states. This is Verification 36's what-if population.
- **Case level:** the ORCH-06 parity run re-executed from a copy of its scripts (`scripts/parity-r36/`; only the work folder, the harness folder and the expected `literal_compare_r32` hash differ: 4 substitutions). The harness side was judged with the fixed harness; the evaluator side was re-run read-only with the ORCH-06 guards. It produced 9,610 cases, compared case by case with the frozen `PARITY-MATRIX.json` (`73e189f2…accc`).

| Quantity | Verification 36 | r36 | Equal |
|---|---|---|---|
| Row judgements (state accepted) | 42,804 | 42,804 | True |
| Rows changed | 53 | 53 | True |
| Change | ws_inside_number / correct / `wrong_only/1 -> recovered_clean/0` / target row | the same, 53 | True |
| Wrong-value controls newly accepted | 0 | 0 | True |
| H1 cases (rows x 2 channels) | 106 | 106 | True |
| Evaluator .10 verdicts on those cases | {"correct": 74, "critical_false_acceptance": 32} | {"correct": 74, "critical_false_acceptance": 32} | True |
| H1 rows in the run set | 23 | 23 | True |

**Results:**
- **State validated:** 53 rows change, the same 53.
- **Case level:** exactly 106 cases change. Each goes critical_false_acceptance -> correct, on the pair and on the facts .10's emission extracts. No side row changes (0), and the evaluator side is identical (True).
- **Class changes:** `b_looser_accepts_wrong` -> `parity` 74; `parity` -> `a_stricter_critical` 32. The 32 cases where .10's own judging also read the wrong number (first-token parse) are now (a) stricter-critical on .10's side. .10's judging is not bound (Verification 36 §6 item 1).
- **Wrong-value controls:** 1,636 fixtures / 3,272 cases. **0 verdicts changed and 0 newly accepted.**
  - Accepted before and after: 26 = 26 cases on the pair, 13 = 13 on the wired facts.
  - These are the frozen harness's H2 decision acceptances (`Code D - Rejected`), and no decision comparison changed.
  - The 488 revision controls stay criticals in both states (`test_h1_every_revision_wrong_value_control_is_still_a_critical`).
- **NOT_SCORABLE:** 32 rows / 242 cases are excluded by the harness before and after (242 / 242). 0 are read as absent, 0 have class `c_violation_read_as_absent`, and unresolved kinds changed on 0.

**The 53 rows** (value offered -> now `recovered_clean`; * = in the run set):

F001|1|revision `0 2`, F007|2|revision `0 0`, F008|1|revision `0 0`, F008|3|revision `0 0`, F008|4|revision `0 0`, F009|3|revision* `0 0`, F009|4|revision* `0 0`, F010|1|revision `0 2`, F011|2|revision `0 0`, F012|1|revision `0 1`, F013|3|revision `0 0`, F013|4|revision `0 0`, F014|1|revision `0 1`, F014|2|revision `0 1`, F014|3|revision `0 1`, F014|4|revision `0 1`, F016|1|revision* `0 1`, F016|2|revision* `0 1`, F016|3|revision* `0 1`, F016|4|revision* `0 1`, F017|1|revision `0 0`, F018|1|revision* `0 1`, F020|3|revision* `0 0`, F020|4|revision* `0 0`, F021|1|revision* `0 0`, F021|3|revision* `0 0`, F021|4|revision* `0 0`, F022|1|revision `0 0`, F023|1|revision `0 0`, F025|1|revision `0 0`, F025|2|revision `0 0`, F025|3|revision `0 0`, F025|4|revision `0 0`, F026|1|revision `0 0`, F028|3|revision `0 1`, F030|3|revision* `0 0`, F030|4|revision* `0 0`, F032|1|revision* `0 0`, F032|3|revision* `0 0`, F032|4|revision* `0 0`, F033|1|revision* `0 1`, F034|1|revision `0 0`, F034|3|revision `0 0`, F034|4|revision `0 0`, F035|1|revision* `0 3`, F035|3|revision* `0 0`, F035|4|revision* `0 1`, F036|1|revision `0 0`, F036|3|revision `0 0`, F036|4|revision `0 0`, F037|2|revision* `0 0`, F037|3|revision* `0 0`, F067|1|revision `0 0`

## 5. No other file changed

- **Harness:** of the 40 harness files, only `literal_compare_r32.py` (the one module) and `test_literal_compare_r32.py` (its tests, appended) differ from review34. The other 38 are byte-identical.
- **Re-derivation:** `apply_h1_fix_r36.py derive` re-derives both changed files from the review34 bytes.
- **Diff scope:** the diff of the module touches only lines inside `norm_revision`.
- **Frozen trees:** review34, review33, review31, evaluator-offline-r32, the cohort packages, four-arm-final, the review folders, staging, the candidate, the baseline, work folders r32 to r35, the r33 / r34 sandboxes and the AI ledger file were not written. Every tree digest (path, size, mtime) equals the task-start snapshot, and no file there is newer than 2026-10-03T15:30:00Z. The package check verifies both.

## 6. Safety

- **No calls:** no provider or model request, no `claude -p`, no network. The parity run's guard reported 0 provider constructions, 0 network or process attempts, no SDK module and no database file.
- **No prediction:** only the frozen SYNTHETIC fixtures were judged.
- **AI ledger:** opened only as `file:…?mode=ro` with `uri=True`. It reads 483 entries / 17 scopes / 0 amendments before and after. No ledger scope was created.
- **Out of scope:** no OneDrive, no sealed project, no authorization file. File names were never used as evidence.
- **Bytecode:** review34 and the candidate were imported read-only with bytecode writing off.

## 7. Statuses, stated separately

1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.
2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted (Claude Opus 5.5), not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`): reference set independently AI-reviewed (Claude agents), not human-signed; not human Golden Truth.
4. **Field populations:** identity 57, revision 38, decision 38.
5. **Conditions:** R36-08 is answered by this package, **pending ORCH-06CV**. Verification 36's other ORCH-07 conditions (R36-09 scope, R36-07 emission rules, the section 6 interpretations and disclosures) are for the declaration. R36-10 (H4) is not changed here (optional per Verification 36).
6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch.
7. **M2:** **CHANGES STILL REQUIRED.**
8. **M3:** not started.
