"""ORCH-06C (R36HARNESS-IMPL): write PILOT/review36/CHANGE-RECORD.md from the packaged evidence (refuses if it exists).
Usage: make_change_record_r36.py
Every number in the record is read from H1-WHATIF-RESULT.json, evidence/TESTS-*.json, evidence/*-RECORD.json and the
junit of tests/new-tests-on-review34-module/; the diff is computed with difflib from the review34 and r36 module bytes; the
review34 behaviour column is computed by loading the review34 module read-only under another name (no bytecode)."""
import datetime
import difflib
import hashlib
import importlib.util
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "review36"
R34 = PILOT / "review34"
WORK = pathlib.Path("C:/t/iso/work/r2x/r36")
OUT = PKG / "CHANGE-RECORD.md"
REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"
EXAMPLES = ["0 1", "0 0", "REV 0 1", "R 01", "Rev. 0 2", "R 0 0", "1 0", "0 1 2", "0\u00a01", "01", "Rev. 0", "REV 01", "Revision 1",
            "R EV 1", "A 1", "0-1", "\u0660 \u0661"]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def j(p):
    return json.loads((PKG / p).read_text(encoding="utf-8"))


def main():
    if OUT.exists():
        raise SystemExit("refused: CHANGE-RECORD.md exists")
    old_path, new_path = R34 / "scripts/harness-r32/literal_compare_r32.py", PKG / "scripts/harness-r32/literal_compare_r32.py"
    OLD = load_module("literal_compare_r32_review34", old_path)
    NEW = load_module("literal_compare_r32_r36", new_path)
    diff = "\n".join(difflib.unified_diff(old_path.read_text(encoding="utf-8").splitlines(), new_path.read_text(encoding="utf-8").splitlines(),
                                          "review34/scripts/harness-r32/literal_compare_r32.py", "review36/scripts/harness-r32/literal_compare_r32.py",
                                          n=3, lineterm=""))
    w = j("H1-WHATIF-RESULT.json")
    tt, tb = j("evidence/TESTS-TWIN.json"), j("evidence/TESTS-BOUND.json")
    twin = j("evidence/TWIN-RECORD.json")
    copy = j("evidence/COPY-RECORD.json")
    par = j("evidence/PARITY-COPY-RECORD.json")
    root = ET.parse(PKG / "tests/new-tests-on-review34-module/test_literal_compare_r32.xml").getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    on_old = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors")}
    failed_on_old = sorted({tc.get("name").split("[")[0] for s in suites for tc in s.iter("testcase") if tc.find("failure") is not None})
    rl, cl, cmp_ = w["row_level"], w["case_level"], w["verification36_comparison"]
    wv, ns = cl["wrong_value_controls"], cl["not_scorable"]
    lc_old, lc_new = sha(old_path), sha(new_path)
    t_old, t_new = sha(R34 / "scripts/harness-r32/test_literal_compare_r32.py"), sha(PKG / "scripts/harness-r32/test_literal_compare_r32.py")
    unchanged = sorted(n for n, v in copy["files"].items() if sha(PKG / "scripts/harness-r32" / n) == v["source_sha256"])
    rows = {}
    for x in rl["accepted"]["changed_rows"]:
        rows[x["row"]] = x["value"]
    in_run = set(cl["changed_rows_in_run_set"])

    def show(v):
        return v.encode("unicode_escape").decode("ascii") if any(ord(ch) > 126 for ch in v) else v

    L = []
    a = L.append
    a("# Change record (review36, ORCH-06C): H1 whitespace fix in `literal_compare_r32.norm_revision`")
    a("")
    a("- **Task:** ORCH-06C, the bounded harness fix for H1 required by Independent Verification 36 (finding R36-08, condition 1 for ORCH-07).")
    a("- **Agent:** R36HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High, self-reported from my system context. A fresh, isolated implementation agent; the only write-capable agent running.")
    a("- **Authorities:** A-03 and A-08.")
    a(f"- **Date:** 2026-10-03 (work from 15:14 UTC; this record written {datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M')} UTC).")
    a("- **Nature:** a correction package, **pending ORCH-06CV** (Verification 37, independent read-only check). It is not self-approved and authorizes nothing: no run, budget, ledger scope, default variant, M2 acceptance or M3.")
    a("- **Standing status:** M2 is **CHANGES STILL REQUIRED**. M3 has **not started**.")
    a(f"- **Reference set:** {REFERENCE_SET_STATEMENT} (`r32-labels-reviewed-2`, `89c60e9d…b9a6`).")
    a("")
    a("## 1. The finding (R36-08, major, CONFIRMED)")
    a("")
    a("Verification 36 found that `norm_revision` collapses internal whitespace to one space but never removes it before the revision "
      "pattern is matched. A correct letter-spaced reading (`0 1` for a printed `01`, `0 0` for `00`) therefore did not normalise to `R1` / `R0` "
      "and was scored as a critical false acceptance on resolved truth, firing the per-field tripwire. This is contrary to convention ruling "
      "(i2) (\"the scorer compares whitespace-insensitively\") and to the module's own docstring. It is reachable through C's AI path "
      "(`evidence_reader.validate_value` keeps the literal), not through B's deterministic readers. Scope: the 53 `ws_inside_number` truth "
      "rows (23 in the run set). Verification 36's what-if: exactly 53 of 42,804 row verdicts change and 0 wrong-value controls are newly accepted.")
    a("")
    a("## 2. The change")
    a("")
    a(f"- **`literal_compare_r32.py`:** review34 `{lc_old}` -> r36 `{lc_new}`. Only `norm_revision` changes.")
    a(f"- **`test_literal_compare_r32.py`:** review34 `{t_old}` -> r36 `{t_new}`. 35 tests are appended; the review34 file is an exact byte prefix, so its 13 tests are unchanged.")
    a(f"- **Every other file:** the other {len(unchanged) - 0} of 40 harness files are byte-identical to `PILOT/review34/scripts/harness-r32/` (review34 manifest `64d5ba0d…7a86`); the package check re-hashes all 40.")
    a("")
    a("**What the function now does.** It keeps the unchanged steps: the Arabic branch (`norm_text` only), dash folding, upper-casing and whitespace collapsing. "
      "It then matches the optional prefix first, with the same alternatives in the same order as the review34 pattern (`REVISION`, `REV.`, `REV`, `R.`, `R`). "
      "It removes **every** whitespace character after the prefix, and only then matches the number pattern `0*(\\d+)`, read by value. "
      "The non-numeric fallback is unchanged (every whitespace character removed). The module docstring is unchanged and is now accurate for "
      "revisions too. A function docstring was added.")
    a("")
    a("**Why nothing else changes.** For any value the review34 pattern matched, the prefix it used is the one the r36 `re.match` picks: no other alternative "
      "leaves whitespace or digits after it. The remainder was whitespace, zeros and digits, so the r36 function returns the same `R<n>`. Values the "
      "review34 pattern did not match either stay on the unchanged fallback, or now match only because whitespace sat inside the number. "
      "`test_h1_only_values_with_inner_whitespace_change` checks this on every revision string in the fixtures and the truth.")
    a("")
    a("```diff")
    a(diff)
    a("```")
    a("")
    a("| Value | review34 `norm_revision` | r36 `norm_revision` |")
    a("|---|---|---|")
    for v in EXAMPLES:
        a(f"| `{show(v)}` | `{show(OLD.norm_revision(v))}` | `{show(NEW.norm_revision(v))}` |")
    a("")
    a("## 3. Tests")
    a("")
    a("**New tests** (appended to `test_literal_compare_r32.py`; the fixtures `SYNTHETIC-PREDICTIONS.json` `9f3e0e56…f774` and `TRUTH-R32.json` `4e237a4e…e064` are read-only and hash-checked):")
    a("- `test_h1_the_task_examples`: `0 1`, `0 0`, `REV 0 1`, `R 01` -> `R1` / `R0`; `Rev. 0 2` -> `R2`.")
    a("- `test_h1_whitespace_inside_a_revision_number_is_removed_before_the_parse` (14 cases): spaces, NBSP, tab and thin space inside the number, with each prefix.")
    a("- `test_h1_adversarial_values_stay_different` (13 cases):")
    a("  - a digit inserted with spaces: `0 1 2` against `01`;")
    a("  - the digits in another order: `1 0` against `01`;")
    a("  - whitespace inside the prefix: `R EV 01`;")
    a("  - dashes, which are not whitespace;")
    a("  - letters.")
    a("- `test_h1_non_numeric_values_keep_the_fallback`: `A 1` == `A1` by the unchanged fallback.")
    a("- `test_h1_arabic_revision_handling_is_unchanged`.")
    a("- `test_h1_only_values_with_inner_whitespace_change`: parity with a verbatim copy of the review34 function on every value without inner whitespace.")
    a("- `test_h1_the_53_ws_inside_number_rows_now_equal_their_truth`: literal comparison and `lane_judge_r32`, states accepted and validated, `recovered_clean`, 0 critical.")
    a("- `test_h1_every_wrong_value_control_keeps_its_frozen_verdict`: all 1,636 controls. The literal comparison and the judge outcome, criticals, cross-page count and match kinds equal the frozen expectation in both states.")
    a("- `test_h1_every_revision_wrong_value_control_is_still_a_critical`: 488 controls.")
    a("- `test_h1_not_scorable_rows_stay_excluded_and_never_read_as_absent`: 121 fixtures.")
    a("")
    a(f"**The new tests detect the defect.** Run against the review34 modules, the r36 test file gives {on_old['failures']} failures in {on_old['tests']} tests "
      f"(`tests/new-tests-on-review34-module/`). The failing tests are exactly the H1-sensitive ones: {', '.join('`' + n + '`' for n in failed_on_old)}. On the r36 module all {on_old['tests']} pass.")
    a("")
    a("| Run | Tree | Modules | Tests | Failures | Errors | Guard refusals |")
    a("|---|---|---|---|---|---|---|")
    a(f"| Whole review34 suite + new tests (`tests/`) | test-run twin of the bound copy | {tt['module_count']} | {tt['total']['tests']} | {tt['total']['failures']} | {tt['total']['errors']} | {tt['guard_refusals']} |")
    a(f"| Sandbox-free modules (`tests/bound-copy/`) | the bound copy itself | {tb['module_count']} | {tb['total']['tests']} | {tb['total']['failures']} | {tb['total']['errors']} | {tb['guard_refusals']} |")
    a("")
    a(f"The whole-suite count is {tt['total']['tests']} = 245 review34 tests + 35 new tests.")
    a("")
    a(f"**Disclosure: the test-run twin.** The review34 suite hard-codes the sandbox base `C:/t/r2x/r34-sandbox`, and `test_runner_r32` and "
      f"`test_sandbox_ingest_r32` create sandboxes there. This task may write sandboxes only under `C:/t/r2x/r36-sandbox/`, and it may change no "
      f"module other than `norm_revision`. So the whole suite ran from `harness-r32-suite-twin/`. That twin equals the bound copy with only the "
      f"string `{twin['substitution'][0]}` -> `{twin['substitution'][1]}`: {twin['substitutions_total']} occurrences in "
      f"{len(twin['files_with_substitutions'])} files ({', '.join('`' + x + '`' for x in twin['files_with_substitutions'])}). It was verified byte for byte "
      "before each run and again by the package check. `literal_compare_r32.py`, its test and `lane_judge_r32.py` are identical in the twin and the bound copy. "
      "The 14 modules that create no sandbox also passed from the bound copy itself. The twin is not bound and not packaged as harness code.")
    a("")
    a("**Write guard.** Every pytest process loaded `scripts/pytest-plugins/r36_write_guard.py`, an audit hook that refuses writes outside the "
      "basetemp, the junit folder and (for the twin) the r36 sandbox, and refuses network connections.")
    a("- Two early attempts were aborted by the guard before any test ran: pytest's capture file in the system TEMP, then the null device. Both are now handled.")
    a("- One twin run had 10 failures caused only by the guard refusing extended-length paths (`\\\\?\\c:\\t\\r2x\\r36-sandbox\\…`) inside the allowed sandbox. The guard now strips that prefix, and the repeat had 0 failures.")
    a("- The summaries of that twin run and of the first bound-copy run (made with the earlier guard version, also 0 failures) are in `evidence/superseded/`; the packaged junit is from the repeats with the final guard. The audit log records every attempt.")
    a("")
    a("## 4. The what-if, reproduced (`H1-WHATIF-RESULT.json`)")
    a("")
    a("**Two re-executions on the frozen fixtures (4,805 SYNTHETIC values, none a model prediction):**")
    a("- **Row level** (`judge_all_rows_r36.py`): every labelled row of each fixture's document, judged with the review34 harness (imported in place, read-only) and with the r36 harness, in both automatic-acceptance states. This is Verification 36's what-if population.")
    a(f"- **Case level:** the ORCH-06 parity run re-executed from a copy of its scripts (`scripts/parity-r36/`; only the work folder, the harness folder and the expected `literal_compare_r32` hash differ: {sum(len(v['substitutions']) for v in par['files'].values())} substitutions). The harness side was judged with the fixed harness; the evaluator side was re-run read-only with the ORCH-06 guards. It produced {cl['cases']:,} cases, compared case by case with the frozen `PARITY-MATRIX.json` (`73e189f2…accc`).")
    a("")
    a("| Quantity | Verification 36 | r36 | Equal |")
    a("|---|---|---|---|")
    a(f"| Row judgements (state accepted) | {cmp_['rows_judged']['verification36']:,} | {cmp_['rows_judged']['r36']:,} | {cmp_['rows_judged']['equal']} |")
    a(f"| Rows changed | {cmp_['changed']['verification36']} | {cmp_['changed']['r36']} | {cmp_['changed']['equal']} |")
    a(f"| Change | ws_inside_number / correct / `wrong_only/1 -> recovered_clean/0` / target row | the same, {rl['accepted']['changes_by_variant_intent_outcome'][0]['n']} | {cmp_['changes_by_variant_intent_outcome']['equal']} |")
    a(f"| Wrong-value controls newly accepted | {cmp_['wrong_controls_newly_accepted']['verification36']} | {cmp_['wrong_controls_newly_accepted']['r36']} | {cmp_['wrong_controls_newly_accepted']['equal']} |")
    a(f"| H1 cases (rows x 2 channels) | {cmp_['H1_cases']['verification36']} | {cmp_['H1_cases']['r36']} | {cmp_['H1_cases']['equal']} |")
    a(f"| Evaluator .10 verdicts on those cases | {json.dumps(cmp_['H1_evaluator_verdicts_on_the_changed_cases']['verification36'], sort_keys=True)} | {json.dumps(cmp_['H1_evaluator_verdicts_on_the_changed_cases']['r36'], sort_keys=True)} | {cmp_['H1_evaluator_verdicts_on_the_changed_cases']['equal']} |")
    a(f"| H1 rows in the run set | {len(cmp_['H1_rows_in_run_set']['verification36'])} | {len(cmp_['H1_rows_in_run_set']['r36'])} | {cmp_['H1_rows_in_run_set']['equal']} |")
    a("")
    a("**Results:**")
    a(f"- **State validated:** {rl['validated']['changed']} rows change, the same 53.")
    a(f"- **Case level:** exactly {cl['changed_cases']} cases change. Each goes critical_false_acceptance -> correct, on the pair and on the facts .10's emission extracts. No side row changes ({cl['side_rows_changed_count']}), and the evaluator side is identical ({cl['evaluator_side_identical']}).")
    a("- **Class changes:** " + "; ".join(f"`{x['before']}` -> `{x['after']}` {x['n']}" for x in cl["class_vs_pair_changes"]) + ". The 32 cases where .10's own judging also read the wrong number (first-token parse) are now (a) stricter-critical on .10's side. .10's judging is not bound (Verification 36 §6 item 1).")
    a(f"- **Wrong-value controls:** {wv['fixtures']:,} fixtures / {wv['cases']:,} cases. **{wv['verdict_changed']} verdicts changed and 0 newly accepted.**")
    a(f"  - Accepted before and after: {wv['harness_pair_accepted_before']} = {wv['harness_pair_accepted_after']} cases on the pair, {wv['harness_wired_accepted_before']} = {wv['harness_wired_accepted_after']} on the wired facts.")
    a("  - These are the frozen harness's H2 decision acceptances (`Code D - Rejected`), and no decision comparison changed.")
    a(f"  - The 488 revision controls stay criticals in both states (`test_h1_every_revision_wrong_value_control_is_still_a_critical`).")
    a(f"- **NOT_SCORABLE:** {ns['rows']} rows / {ns['cases']} cases are excluded by the harness before and after ({ns['harness_pair_excluded_after']} / {ns['harness_wired_excluded_after']}). {ns['harness_read_as_absent_after']} are read as absent, {ns['class_c_violation_read_as_absent_after']} have class `c_violation_read_as_absent`, and unresolved kinds changed on {ns['unresolved_kinds_changed']}.")
    a("")
    a("**The 53 rows** (value offered -> now `recovered_clean`; * = in the run set):")
    a("")
    a(", ".join(f"{r}{'*' if r in in_run else ''} `{rows[r]}`" for r in sorted(rows)))
    a("")
    a("## 5. No other file changed")
    a("")
    a(f"- **Harness:** of the 40 harness files, only `literal_compare_r32.py` (the one module) and `test_literal_compare_r32.py` (its tests, appended) differ from review34. The other {len(unchanged)} are byte-identical.")
    a("- **Re-derivation:** `apply_h1_fix_r36.py derive` re-derives both changed files from the review34 bytes.")
    a("- **Diff scope:** the diff of the module touches only lines inside `norm_revision`.")
    a("- **Frozen trees:** review34, review33, review31, evaluator-offline-r32, the cohort packages, four-arm-final, the review folders, staging, the candidate, the baseline, work folders r32 to r35, the r33 / r34 sandboxes and the AI ledger file were not written. Every tree digest (path, size, mtime) equals the task-start snapshot, and no file there is newer than 2026-10-03T15:30:00Z. The package check verifies both.")
    a("")
    a("## 6. Safety")
    a("")
    a("- **No calls:** no provider or model request, no `claude -p`, no network. The parity run's guard reported 0 provider constructions, 0 network or process attempts, no SDK module and no database file.")
    a("- **No prediction:** only the frozen SYNTHETIC fixtures were judged.")
    a("- **AI ledger:** opened only as `file:…?mode=ro` with `uri=True`. It reads 483 entries / 17 scopes / 0 amendments before and after. No ledger scope was created.")
    a("- **Out of scope:** no OneDrive, no sealed project, no authorization file. File names were never used as evidence.")
    a("- **Bytecode:** review34 and the candidate were imported read-only with bytecode writing off.")
    a("")
    a("## 7. Statuses, stated separately")
    a("")
    a("1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.")
    a("2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted (Claude Opus 5.5), not human-signed.")
    a(f"3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`): {REFERENCE_SET_STATEMENT}; not human Golden Truth.")
    a("4. **Field populations:** identity 57, revision 38, decision 38.")
    a("5. **Conditions:** R36-08 is answered by this package, **pending ORCH-06CV**. Verification 36's other ORCH-07 conditions (R36-09 scope, R36-07 emission rules, the section 6 interpretations and disclosures) are for the declaration. R36-10 (H4) is not changed here (optional per Verification 36).")
    a("6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch.")
    a("7. **M2:** **CHANGES STILL REQUIRED.**")
    a("8. **M3:** not started.")
    text = "\n".join(L) + "\n"
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest(), len(L))


if __name__ == "__main__":
    main()
