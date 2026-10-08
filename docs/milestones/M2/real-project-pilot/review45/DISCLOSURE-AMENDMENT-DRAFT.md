# DISCLOSURE-AMENDMENT-DRAFT: the text a declaration v5 must carry about the review45 baseline-facts drill

Task R43-42. **A draft for Verification 45 and the owner. It changes no declaration** (declaration v4 is untouched, frozen
and NOT authorized; no v5 exists) **and it authorizes nothing.** Every figure below is from `evidence/drill/` of this
package, bound in `BINDING-MANIFEST-R45-HARNESS.json`.

## 1. Amendment to the first-read disclosure (R34-18)

Replace the disclosure that the application processes the real cohort PDFs for the first time in live B by:

> The application (lane B, baseline `frozen-r13` at `7ec3d2cf`) processes the real run-set PDFs for the first time in live
> B, **except F009, F020 and F030 (EP-27331; staged sha256 `970ddb0f...b415`, `599d36be...91db`, `feec64cd...010a`)**,
> which were processed offline beforehand by the same lane-B code path in the review45 dry baseline-facts drill
> (`runner_r32.py --dry-baseline-facts`, 2026-10-08, AI off, the refusing global provider, 0 model requests), once as the
> evidence run (`r32-drill-r45-evidence-1`) and once inside the harness test suite (`test_dry_baseline_drill_r45`, a test
> sandbox). The other 21 run-set documents were not read by the application before the live run.

## 2. The drill's existence and scope

- **Mode:** an additional, explicitly named dry mode of the review45 harness, refused in live mode, on any other lane
  (C, R, P), tree (only `C:/t/iso/frozen-r13`), document (exactly F009, F020, F030 by pool id AND staged sha256), drill
  flag, resume or output folder. Every other dry rule is unchanged: reader `none` over the real cohort, `--dry-synthetic`
  over SYN* documents only, and the lane's cohort assertion, now extended only for this allow-list.
- **Path:** the lane's own B code path (`document_processing.run` with the lane's `process` / `read_form_or_raise` /
  `apply_form_reading` hooks, `row_dict`, `b_tripwire` -> `tripwire_r32.py` -> `lane_judge_r32`, rule CP-R38),
  `after_document` and `final`, against the resolved truth `4e237a4e...e064`. A profiler trace (`DRILL-TRACE.json`)
  records the calls.
- **What it never touches:** run state, allowance, capture store, AI ledger (or a fake one), ledger scope, authorization,
  nonce, token or RUN file (refusing stand-ins in the runner, `Forbidden` sentinels in the lane; a configuration naming
  any of them is refused). It writes only `<sandbox base>/r32-drill-<stamp>`.

## 3. The criterion and the result

- **Criterion** (`DRILL-CRITERION.md`, sha256 `8b183053cf10e5332f8b198a1d5b1aae5169c47671ad5e35346acf31cca5d918`,
  recorded in the R43 session log row R43-65 before any drill code ran on any document): PASS if and only if, for each
  of F009, F020 and F030, there is no critical acceptance on resolved truth in identity, revision or decision in any
  tripwire evaluation; the v3 stop condition ("INVALID: baseline incomplete (critical acceptance on resolved truth in
  B)") does not fire; each document is exercised; and there are zero requests. Any critical is a FAIL to report, never
  to fix.
- **Result: PASS.** The test-suite execution of the same path gave the same outcome.

  | Document | Lane status / role (application) | Facts (final) | Resolved criticals | Unresolved criticals | Stop condition |
  |---|---|---|---|---|---|
  | F009 | COMPLETE / `submittal_form` | 19 | 0 | 0 | no |
  | F020 | COMPLETE / `submittal_form` | 21 | 0 | 0 | no |
  | F030 | COMPLETE / `document` | 18 | 0 | 0 | no |

  The comparison state stayed PENDING. Requests: 0 refusing-provider calls, 0 dry-stub calls, no live provider reached, no
  `complete()` traced. The AI ledger (`mode=ro`) read 484 / 18 / 0 before and after. The pip freeze was `bd424a5c...bf7f`
  before and after.
- **What the facts show (stated, not interpreted as accuracy).** On page 3 of each document the baseline now accepts the
  full title-block drawing number (`B01-02-ASC_EGTS-P05-SD-FA-0006`, `-0008`, `-0010`), which the judge treats as an
  evidenced cross-page association with page 4 (rule CP-R38: `missed` with `cross_page` 1, not wrong, not critical). In
  v3, the truncated `P05-SD-FA-0006` on F009 page 3 was a resolved-truth critical. Page 4 identity and pages 3-4 revision
  are `recovered_clean` in all three documents. The page-1 identity values are observed, not accepted (no acceptance, no
  critical). No decision is accepted (F020 holds one `approved` on page 4 as `held`).

## 4. Pre-run exposure (R44-12, extended)

- **Already recorded (R44-12):** the R43 grammar work judged identity facts of F009, F020 and F030 (and F021) on pages
  3-4, observed from fixture text layers, against the v3 truth (`R43-REVIEW-PACKAGE/R43-HARNESS-JUDGE-OUTPUT.json`).
- **Added by this drill:** the baseline's complete deterministic facts for the three documents (all pages, identity,
  revision and decision) were judged against the resolved truth, and the per-row outcomes were seen by the implementing
  agent (Claude Opus 5.5) and will be seen by its verifiers. The criterion was fixed before; no code, grammar, label,
  truth or criterion changed after the facts were seen. Label-blindness is preserved in substance only on that basis;
  any later change to the baseline, the labels or the truth would need a new declaration with this disclosure.
- The reference set stays AI-reviewed (Claude agents), not human-signed.

## 5. Limits a declaration v5 must state

1. **AI off.** F009 and F020 are submittal forms to the application: in live B (AI on) the application would also ask
   the model for a form reading after the deterministic reading, and the lane's tripwire would judge that reading too.
   The drill judged the deterministic reading only (the row the live `after_document` tripwire judges first). The
   model's form reading of F009 and F020 is NOT rehearsed.
2. **Three documents, one project.** Only F009, F020 and F030 were registered in EP-27331; the other EP-27331 run-set
   documents were absent, so project-level effects of those siblings are not reproduced. 21 of 24 documents are not
   rehearsed (A-13 item 2 named these three; covering all 24 needs further authority).
3. **Not a result.** No accuracy, coverage or eligibility claim follows from the drill, and it says nothing about C, R
   or P.
4. **OCR.** The installed Tesseract was available (`ocr_available` returned True); no document was UNREAD.

## 6. What still decides a run

The owner's choice among Verification 44's options; Verification 45 of this harness; a declaration v5 (v4 with only the
harness rebind, plus this disclosure); its verification; R44-07 (runbook, scope command, budget card); the pip-freeze
precondition before invocation 1 and every resume; and a new owner D1/D2 naming the v5 hash.
