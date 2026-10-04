# Offline evaluator .10 parity test against the r32 reference set (ORCH-06, 2026-10-03)

- **Task:** ORCH-06 (Review 33 condition C-6, finding D4-06; Review 35 section 6 items 1 and 10), agent R35EVAL-IMPL, the only write-capable agent. Authorities A-03 and A-08.
- **Model (self-report):** Claude Opus 5.5 (`claude-opus-5-5`), effort High, as stated in my system context.
- **Nature:** an implementation test package. It is **not** a review, approves nothing and authorizes nothing. ORCH-06V (an independent read-only verification) comes next. M2 stays **CHANGES STILL REQUIRED**; M3 has **not started**.
- **Zero calls:** no provider or model request of any kind, no `claude -p`, no network. The evaluator ran offline on **SYNTHETIC** fixtures only: 4805 fixtures built from the r32 truth strings, each run through two channels (9610 cases). No prediction of any cohort document exists or was created; no arm output, page image or earlier label set was read. Provider classes constructed: 0; network or process attempts: 0; SDK modules imported: 0.
- **Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (`r32-labels-reviewed-2`, `89c60e9d…b9a6`), converted by the frozen review34 adapter and converter.

## 1. Answer in brief

1. **Evaluator .10's own judging is not at parity with the frozen r32 harness.** Of 9610 cases, 6301 are at parity and 242 are NOT_SCORABLE rows that both exclude. Restricted to values the application can actually emit (7676 cases): **1448 (a) stricter-critical**, 0 (a) stricter-recovery, **86 (b) looser-accepts-wrong**, **32 (b) looser-hides-wrong**, plus 270 side-row recovery credits on 54 distinct rows.
2. **(a) Stricter, and critical:** a correct identity printed with another dash glyph (R1), a correct revision written 'Rev. 01' / 'REV 01' / 'Revision 1' (R2), the correct value of the F043 'Rev. 0' rows (R2b), the (g)(1) tail form (R3) and the application's 'rejected' on a (d1) row (R4) each become a **critical false acceptance on resolved truth** in .10 -- they would fire the per-field tripwire (B INVALID, C STOP) on a correct reading.
3. **(b) Looser:** .10 accepts any 'Rev. <n>' for the F043 'Rev. 0' truth (R2b), associates an identity of another page of a compilation file cross-page and never flags it (R5), and credits another page's recovery for cross-page identity copies (R6). The other 74 (b) accepts-wrong cases are H1 ('0 0' for a printed '00'): there the harness, not .10, departs from the whitespace rule (i2).
4. **(c) NOT_SCORABLE rows are handled correctly:** 242 of 242 cases on 32 rows are excluded by .10 (the converter's 'ambiguous' is in `m2_eval4.UNSCORABLE`); 0 are read as absent and 0 are scored.
5. **Decision vocabulary (R7):** .10 compares decision **words** (`approved`, `ANN`, `rejected`). Every other text is either dropped at emission (register) or judged wrong (AI path). The application never emits other text, so R7 is not reachable in the r32 lanes; it matters only if non-application text were ever judged.
6. **Recommendation (section 10):** bind evaluator .10 **as is in its emission role only** (the frozen review34 path), with every verdict from the frozen r32 judge; do **not** bind .10's own judging for any metric, tripwire or gate. If ORCH-07 wants .10's judging to produce any verdict, a **candidate correction** (new commit, own independent review) is required first, changing rules R1-R6 (R7 optional).
7. **Normaliser question (section 9):** a declared normaliser before the evaluator can reconcile them without changing the evaluator only if it is truth-aware (N2): the blind normaliser (N1) still leaves R3 / R3b, R4, R5 and R6. Neither N1 nor N2 made .10 accept a wrong-value control that the harness rejects, but N2 is a second implementation of the harness rules placed in front of .10, so it is not recommended over binding the frozen judge directly.

## 2. Frozen inputs (re-hashed before use; all equal)

| Item | Path | sha256 |
| --- | --- | --- |
| converter_reconciliation | `review34/CONVERTER-RECONCILIATION.json` | `e350d2fe78d6062cf59328d1caedfca8f8a72210d2d043c5c37068033b2624f3` |
| label_conventions_r32 | `fresh-cohort-r32/LABEL-CONVENTIONS-R32.md` | `5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570` |
| labels_eval_input | `review34/LABELS-R32-EVAL-INPUT.json` | `4b2c73d59ab852fa45eb46ff58f0ee13242c2ccac4db0221f4b1b607edede5cc` |
| reference_set_reviewed_2 | `fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json` | `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6` |
| review33 | `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-33/INDEPENDENT-REVIEW.md` | `8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804` |
| review34 | `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-34/INDEPENDENT-REVIEW.md` | `75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47` |
| review34_manifest | `review34/evidence/EVIDENCE-MANIFEST.json` | `64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86` |
| review35 | `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-35/INDEPENDENT-REVIEW.md` | `f4f668ac240cfdde229febe03f7a6a1b28a1120ab50c6b8ed04264ed2987fe31` |
| truth_r32 | `review34/dry-run/TRUTH-R32.json` | `4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064` |
| candidate | `C:/t/iso/cand-r29` HEAD | `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d`, `git status --porcelain` empty before and after |
| evaluator .10 | `backend/scripts/m2_eval6.py` | `268d86231260392dc5592a6937803b8fcd15a41e9590b442f3f0a70dc57b4b4f` (m2-pilot-eval-2026-10-02.10) |
| candidate module (imported) | `backend/app/ai/evidence_reader.py` | `d74397b374fc91a69ed6b4d2ba4306e5fe89682144b2cf5275c7c4091c7ca07a` |
| candidate module (imported) | `backend/app/ai/guard.py` | `ae25b75f4f16f3eee76667853eb84cf2f22fc6afb85825d26334697138c44631` |
| candidate module (imported) | `backend/app/ai/provider.py` | `d465961efb07b7f9df2597b37a228735238af433d950bf7095925e8cc43eb5ba` |
| candidate module (imported) | `backend/app/core/config.py` | `b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155` |
| candidate module (imported) | `backend/scripts/m2_eval4.py` | `65f3e096dd8ec93be38f50db445eeb0a9837c1acde605f5569a575f1f31f79b5` |
| candidate module (imported) | `backend/scripts/m2_pilot_eval.py` | `845584b076a42ad26eb576c23034890851d35d386e558437c06501399950fe97` |
| review34 harness module | `scripts/harness-r32/converter_r32.py` | `4095a4967a7e7caa992feec4901e06c1836d263f62ab1ba884db8355c30f9704` |
| review34 harness module | `scripts/harness-r32/labels_adapter_r32.py` | `ff9d2e6b9311bd9ceaaab76f1d3237c1129f8d6c1a70d56d831e11d0e02501ab` |
| review34 harness module | `scripts/harness-r32/lane_judge_r32.py` | `a0b6b7c83262ddb2d1337d5ed17296a5aa6fa26cc6ebbee18afcb3cf48f0ca45` |
| review34 harness module | `scripts/harness-r32/literal_compare_r32.py` | `ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6` |
| review34 harness module | `scripts/harness-r32/score_lane_r32.py` | `c25f4d8994631b0fe5b52c1eb4d5bb0f7227f15a4b26c671e72e9c7e31c3c915` |
| review34 harness module | `scripts/harness-r32/tripwire_r32.py` | `42dc6226700852f84762bdd7759bb7592de72778fe92aaad7f7993db291f14d0` |
| fixtures (this package) | `SYNTHETIC-PREDICTIONS.json` | `9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774` |
| run set (annotation only) | `review34/RUN-SET-PROPOSAL.json` | `9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8` |

## 3. Method

- **Fixtures (`scripts/fixtures_r32.py`).** Built from `TRUTH-R32.json` and `LABELS-R32-EVAL-INPUT.json` only. One synthetic fact (or none) per fixture, offered on one truth row. Groups: every scorable value row (identity, revision, decision) with exact and equivalent variants and wrong-value controls; every ABSENT row; every NOT_SCORABLE row (absent, its literal / candidates / class word, a wrong value); page-keyed compilation cases (F002, F035, F043); cross-page identity cases for the drawing sets (F014, F016, F038) and for cover / enclosure packages. The count-once aliases (F031, F059) are not in the evaluator input and are listed, not fixtured. Each fixture carries kind SYNTHETIC, its truth key, variant, intent and the **expected harness verdict computed by the frozen harness** (`literal_compare_r32.compare_row` and `lane_judge_r32`).
- **Coverage:** 4805 fixtures; every one of the 417 canonical truth rows ({'absent': 140, 'not_scorable': 32, 'value': 245}) has at least one (rows without a fixture: 0); 15 alias rows are listed as excluded; wrong-value controls 1636; fixtures by group {'absent_row': 479, 'compilation_page_keyed': 48, 'cross_page_identity': 104, 'decision_value': 1160, 'identity_value': 1773, 'not_scorable_row': 110, 'revision_value': 1131}. Rows in state illegible: 0, unsupported: 0.
- **Evaluator invocation (`scripts/run_evaluator_offline_r32.py`).** Exactly as `review31/scripts/harness/score_lane.py`: `EV.evaluate(register, page, rows, page['page1_corrections'], ai_context)` on the frozen converter output (`LABELS-R32-EVAL-INPUT.json`, 68 canonical documents, the whole register per call), reading `layers.evidence`. `scripts.m2_eval6` is imported **in place, read-only** from the candidate (no bytecode written; working directory and every output in the work folder). One synthetic application row per call:
  - `register` (B-like): one register record (state `accepted`), `ai_context` None (B's evidence reader is off);
  - `ai_validated` (C-like): one validated AI observation in an `ai-evidence-2` envelope bound to the document's staged sha256, `ai_context` = {variant EV1, profile default, policies [`evidence-policy-2026-09-29.4`]} as `lane_r32.py` builds it.
- **Harness verdicts on the same case:** `harness_pair` = `lane_judge_r32` on the offered value (the fixture's pair); `harness_wired` = `lane_judge_r32` on the facts that `tripwire_r32.facts_from_row(EV, row, ai_context)` extracts through .10's own emission functions (what `score_lane_r32` judges in a live run).
- **Verdicts** (per truth row): correct, correct_and_wrong, critical_false_acceptance (an automatic acceptance judged wrong, or a false positive on an ABSENT row), held, missed, absent_accepted (true negative), excluded, and for .10 only not_evaluated (the offered text never became a fact). Every other labelled row of the document is compared too (side rows).
- **Classification** (evaluator against harness): parity; (a) `a_stricter_critical`, `a_stricter_recovery`; (b) `b_looser_accepts_wrong`, `b_looser_hides_wrong`, `b_looser_credit` (side rows); (c) `c_not_scorable_excluded` or a violation. `application_reachable` is false only for decision text other than approved / ANN / rejected.
- **Scope check:** the same 9610 cases run with only the fixture's document in the register gave identical results (evaluate() judges documents independently).
- **Guards:** AI / provider variables removed, `AI_ENABLED=false`, a non-existent database URL (never created: True); sockets, DNS, subprocesses and `os.system` blocked; the candidate's provider classes and `get_provider` / `set_provider` replaced by raising stubs (stubbed: ClaudeProvider, OpenAiProvider, ClaudeCodeProvider, NullProvider, RecordingProvider); an audit hook refused any write outside the work folder (refused: 0; violations: 0).

## 4. Results

### 4.1 Classes (evaluator against the harness on the pair)

| Class | All cases | Reachable | Reachable, run-set documents | Against harness_wired | Wired, reachable |
| --- | --- | --- | --- | --- | --- |
| parity | 6301 | 5898 | 2596 | 7126 | 5898 |
| a_stricter_critical | 2124 | 1448 | 702 | 2124 | 1448 |
| a_stricter_recovery | 549 | 0 | 0 | 0 | 0 |
| b_looser_accepts_wrong | 86 | 86 | 42 | 86 | 86 |
| b_looser_hides_wrong | 308 | 32 | 24 | 32 | 32 |
| c_not_scorable_excluded | 242 | 212 | 88 | 242 | 212 |
| c_violation_read_as_absent | 0 | 0 | 0 | 0 | 0 |
| c_violation_scored | 0 | 0 | 0 | 0 | 0 |
| **total** | 9610 | 7676 | 3452 | 9610 | 7676 |

Side rows (another labelled row of the same document changed by the offered fact): {'b_looser_credit': 270} on 54 distinct rows.

### 4.2 By field (reachable cases)

| Field | parity | a_stricter_critical | a_stricter_recovery | b_looser_accepts_wrong | b_looser_hides_wrong | c_not_scorable_excluded |
| --- | --- | --- | --- | --- | --- | --- |
| identity | 2938 | 978 | 0 | 0 | 32 | 66 |
| revision | 2076 | 456 | 0 | 86 | 0 | 78 |
| decision | 884 | 14 | 0 | 0 | 0 | 68 |

All cases by field (including decision text the application never emits):

| Field | parity | a_stricter_critical | a_stricter_recovery | b_looser_accepts_wrong | b_looser_hides_wrong | c_not_scorable_excluded |
| --- | --- | --- | --- | --- | --- | --- |
| identity | 2938 | 978 | 0 | 0 | 32 | 66 |
| revision | 2076 | 456 | 0 | 86 | 0 | 78 |
| decision | 1287 | 690 | 549 | 0 | 276 | 98 |

### 4.3 By channel and group

| Channel | parity | a_stricter_critical | a_stricter_recovery | b_looser_accepts_wrong | b_looser_hides_wrong | c_not_scorable_excluded |
| --- | --- | --- | --- | --- | --- | --- |
| ai_validated | 3225 | 1400 | 0 | 43 | 16 | 121 |
| register | 3076 | 724 | 549 | 43 | 292 | 121 |

| Group | parity | a_stricter_critical | a_stricter_recovery | b_looser_accepts_wrong | b_looser_hides_wrong | c_not_scorable_excluded |
| --- | --- | --- | --- | --- | --- | --- |
| absent_row | 899 | 59 | 0 | 0 | 0 | 0 |
| compilation_page_keyed | 37 | 0 | 0 | 0 | 37 | 22 |
| cross_page_identity | 208 | 0 | 0 | 0 | 0 | 0 |
| decision_value | 869 | 631 | 549 | 0 | 271 | 0 |
| identity_value | 2568 | 978 | 0 | 0 | 0 | 0 |
| not_scorable_row | 0 | 0 | 0 | 0 | 0 | 220 |
| revision_value | 1720 | 456 | 0 | 86 | 0 | 0 |

## 5. Divergences by evaluator rule (responsible code in `C:/t/iso/cand-r29/backend`)

### R1. identity: a dash glyph other than the truth's (hyphen / en dash / minus / figure dash / em dash / non-breaking hyphen) is not folded; norm_ref folds only whitespace and case, and same_identity's 'near' (alphanumerics equal) is not accepted

- Cases: 880 (reachable 880); classes {'a_stricter_critical': 880}; channels {'register': 440, 'ai_validated': 440}.
- Distinct truth rows: 88; in the run set (`RUN-SET-PROPOSAL.json`): 42 (F006|1|identity, F006|2|identity, F009|1|identity, F009|3|identity, F009|4|identity, F015|1|identity, F018|1|identity, F020|1|identity, F020|3|identity, F020|4|identity, F021|1|identity, F021|3|identity …).
- Variants: `dash_as_em_dash` 176, `dash_as_figure_dash` 176, `dash_as_minus` 176, `dash_as_nb_hyphen` 176, `dash_as_en_dash` 174, `dash_as_hyphen` 2.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:238-239` (compare.identity_same_identity); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:94-100` (truth.reference_truth); `m2_pilot_eval.py:80-81` (v3.alnum_near); `m2_pilot_eval.py:76-77` (v3.norm_ref_whitespace_and_case_only); `m2_pilot_eval.py:102-113` (v3.same_identity).
  - e.g. `FX-00003/register` `F001|1|identity` truth `MAT – 116`, offered `MAT — 116`: .10 **critical_false_acceptance**, harness correct -- `identity:single_component_wrong_identity:same_identity=near(near is not accepted)->wrong`.
  - e.g. `FX-00004/register` `F001|1|identity` truth `MAT – 116`, offered `MAT ‒ 116`: .10 **critical_false_acceptance**, harness correct -- `identity:single_component_wrong_identity:same_identity=near(near is not accepted)->wrong`.
  - e.g. `FX-00005/register` `F001|1|identity` truth `MAT – 116`, offered `MAT - 116`: .10 **critical_false_acceptance**, harness correct -- `identity:single_component_wrong_identity:same_identity=near(near is not accepted)->wrong`.

### R2. revision: norm_rev reads only the FIRST whitespace token, so 'Rev. 01', 'REV 01' and 'Revision 1' parse as 'REV.' / 'REV' / 'REVISION', never as the number

- Cases: 420 (reachable 420); classes {'a_stricter_critical': 420}; channels {'register': 210, 'ai_validated': 210}.
- Distinct truth rows: 70; in the run set (`RUN-SET-PROPOSAL.json`): 32 (F009|1|revision, F009|3|revision, F009|4|revision, F016|1|revision, F016|2|revision, F016|3|revision, F016|4|revision, F018|1|revision, F020|1|revision, F020|3|revision, F020|4|revision, F021|1|revision …).
- Variants: `prefix_REV_space` 140, `prefix_Rev_dot_space` 140, `prefix_Revision_word` 140.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:240-241` (compare.revision_norm_rev); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:80-91` (truth.revision_truth); `m2_pilot_eval.py:84-93` (v3.norm_rev_first_token).
  - e.g. `FX-00026/register` `F001|1|revision` truth `02`, offered `REV 02`: .10 **critical_false_acceptance**, harness correct -- `revision:single_component:norm_rev_differs->wrong`.
  - e.g. `FX-00028/register` `F001|1|revision` truth `02`, offered `Rev. 02`: .10 **critical_false_acceptance**, harness correct -- `revision:single_component:norm_rev_differs->wrong`.
  - e.g. `FX-00029/register` `F001|1|revision` truth `02`, offered `Revision 2`: .10 **critical_false_acceptance**, harness correct -- `revision:single_component:norm_rev_differs->wrong`.

### R2b. revision truth 'Rev. 0' (F043 p2-p4): the encoded truth itself normalises to 'REV.', so the correct '0' / '00' / 'R0' / 'Rev.0' are wrong and ANY 'Rev. <n>' is accepted

- Cases: 48 (reachable 48); classes {'a_stricter_critical': 36, 'b_looser_accepts_wrong': 12}; channels {'register': 24, 'ai_validated': 24}.
- Distinct truth rows: 3; in the run set (`RUN-SET-PROPOSAL.json`): 3 (F043|2|revision, F043|3|revision, F043|4|revision).
- Variants: `bare_number` 6, `leading_zero_added` 6, `prefix_R` 6, `prefix_REV_space` 6, `prefix_Rev_dot` 6, `prefix_Revision_word` 6, `prefixed_far_number` 6, `prefixed_wrong_number` 6.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:240-241` (compare.revision_norm_rev); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:80-91` (truth.revision_truth); `m2_pilot_eval.py:84-93` (v3.norm_rev_first_token).
  - e.g. `FX-04021/register` `F043|2|revision` truth `Rev. 0`, offered `0`: .10 **critical_false_acceptance**, harness correct -- `revision:single_component:norm_rev_differs->wrong`.
  - e.g. `FX-04024/register` `F043|2|revision` truth `Rev. 0`, offered `00`: .10 **critical_false_acceptance**, harness correct -- `revision:single_component:norm_rev_differs->wrong`.
  - e.g. `FX-04027/register` `F043|2|revision` truth `Rev. 0`, offered `R0`: .10 **critical_false_acceptance**, harness correct -- `revision:single_component:norm_rev_differs->wrong`.

### R3. identity (g)(1) either form: the printed number with its labelled 'Rev.' tail is not accepted (evaluator .10 has no alternates; the tail is not an '-Rn' suffix for split_suffix)

- Cases: 72 (reachable 72); classes {'a_stricter_critical': 72}; channels {'register': 36, 'ai_validated': 36}.
- Distinct truth rows: 12; in the run set (`RUN-SET-PROPOSAL.json`): 6 (F009|3|identity, F020|3|identity, F021|3|identity, F030|3|identity, F032|3|identity, F037|2|identity).
- Variants: `g1_labelled_tail_lower` 24, `g1_labelled_tail_present` 24, `g1_labelled_tail_present_ws` 24.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:238-239` (compare.identity_same_identity); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:94-100` (truth.reference_truth); `m2_pilot_eval.py:80-81` (v3.alnum_near); `m2_pilot_eval.py:76-77` (v3.norm_ref_whitespace_and_case_only); `m2_pilot_eval.py:102-113` (v3.same_identity).
  - e.g. `FX-00606/register` `F008|3|identity` truth `B01-ASC-SD-ELE-0102`, offered `b01-asc-sd-ele-0102-rev.00`: .10 **critical_false_acceptance**, harness correct -- `identity:single_component_wrong_identity:same_identity=different->wrong`.
  - e.g. `FX-00607/register` `F008|3|identity` truth `B01-ASC-SD-ELE-0102`, offered `B01-ASC-SD-ELE-0102-Rev.00`: .10 **critical_false_acceptance**, harness correct -- `identity:single_component_wrong_identity:same_identity=different->wrong`.
  - e.g. `FX-00608/register` `F008|3|identity` truth `B01-ASC-SD-ELE-0102`, offered `B01-ASC-SD-ELE-0102 - Rev. 00`: .10 **critical_false_acceptance**, harness correct -- `identity:single_component_wrong_identity:same_identity=different->wrong`.

### R3b. identity tail form on a page that prints no tail: the harness forgives it as a cross-page copy of another page's (g)(1) alternate; .10 judges it wrong

- Cases: 26 (reachable 26); classes {'a_stricter_critical': 26}; channels {'register': 13, 'ai_validated': 13}.
- Distinct truth rows: 13; in the run set (`RUN-SET-PROPOSAL.json`): 6 (F009|1|identity, F020|1|identity, F021|1|identity, F030|1|identity, F032|1|identity, F037|1|identity).
- Variants: `labelled_tail_not_printed_on_this_page` 26.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:238-239` (compare.identity_same_identity); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:94-100` (truth.reference_truth); `m2_pilot_eval.py:80-81` (v3.alnum_near); `m2_pilot_eval.py:76-77` (v3.norm_ref_whitespace_and_case_only); `m2_pilot_eval.py:102-113` (v3.same_identity).
  - e.g. `FX-00543/register` `F008|1|identity` truth `B01-ASC-SD-ELE-0102`, offered `B01-ASC-SD-ELE-0102-Rev.00`: .10 **critical_false_acceptance**, harness missed -- `identity:single_component_wrong_identity:same_identity=different->wrong`.
  - e.g. `FX-00702/register` `F009|1|identity` truth `B01-ASC-SD-ELE-0034`, offered `B01-ASC-SD-ELE-0034-Rev.00`: .10 **critical_false_acceptance**, harness missed -- `identity:single_component_wrong_identity:same_identity=different->wrong`.
  - e.g. `FX-01055/register` `F013|1|identity` truth `B01-ASC-SD-ELE-0060`, offered `B01-ASC-SD-ELE-0060-Rev.00`: .10 **critical_false_acceptance**, harness missed -- `identity:single_component_wrong_identity:same_identity=different->wrong`.

### R4. decision (d1) resubmission tolerance: the application's 'rejected' on a 'approved as noted' + resubmission_required row is a wrong decision in .10 (word equality 'rejected' != 'ANN')

- Cases: 14 (reachable 14); classes {'a_stricter_critical': 14}; channels {'register': 7, 'ai_validated': 7}.
- Distinct truth rows: 7; in the run set (`RUN-SET-PROPOSAL.json`): 3 (F030|1|decision, F030|4|decision, F033|1|decision).
- Variants: `d1:rejected` 14.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:242-242` (compare.decision_word_equality); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:65-77` (truth.decision_truth); `m2_pilot_eval.py:44-46` (v3.DECISION_WORDS).
  - e.g. `FX-00050/register` `F001|2|decision` truth `Approved as noted / Resubmit (class approved as noted)`, offered `rejected`: .10 **critical_false_acceptance**, harness correct -- `decision:single_component:word_differs->wrong`.
  - e.g. `FX-01626/register` `F017|1|decision` truth `APPROVED AS NOTED / RESUBMIT (class approved as noted)`, offered `rejected`: .10 **critical_false_acceptance**, harness correct -- `decision:single_component:word_differs->wrong`.
  - e.g. `FX-02086/register` `F022|1|decision` truth `APPROVED AS NOTED / RESUBMIT (class approved as noted)`, offered `rejected`: .10 **critical_false_acceptance**, harness correct -- `decision:single_component:word_differs->wrong`.

### R5. compilation (h): an identity of ANOTHER page of the same compilation file is associated cross-page and credited to that page (associate_group has no page keying); the harness scores it wrong

- Cases: 32 (reachable 32); classes {'b_looser_hides_wrong': 32}; channels {'register': 16, 'ai_validated': 16}.
- Side rows: {'b_looser_credit': 44} on 7 distinct rows.
- Distinct truth rows: 7; in the run set (`RUN-SET-PROPOSAL.json`): 5 (F035|1|identity, F035|2|identity, F035|3|identity, F035|4|identity, F043|1|identity).
- Variants: `value_of_page_1` 10, `value_of_page_2` 8, `value_of_page_4` 8, `value_of_page_3` 6.
- Code: `m2_eval6.py:268-271` (association.cross_page_by_identity); `m2_eval6.py:238-239` (compare.identity_same_identity); `m2_eval4.py:94-100` (truth.reference_truth); `m2_pilot_eval.py:76-77` (v3.norm_ref_whitespace_and_case_only); `m2_pilot_eval.py:102-113` (v3.same_identity).
  - e.g. `FX-00083/register` `F002|1|identity` truth `TAK-02041-MCR-EL-013`, offered `SAIFCO-351-MEP-MAR-EL-12`: .10 **missed**, harness critical_false_acceptance -- `identity:cross_page:same_identity=exact->correct`.
  - e.g. `FX-00084/register` `F002|1|identity` truth `TAK-02041-MCR-EL-013`, offered `SAIFCO-351-MEP-MAR-EL-12`: .10 **missed**, harness critical_false_acceptance -- `identity:cross_page:same_identity=exact->correct`.
  - e.g. `FX-00125/register` `F002|2|identity` truth `SAIFCO-351-MEP-MAR-EL-12`, offered `TAK-02041-MCR-EL-013`: .10 **missed**, harness critical_false_acceptance -- `identity:cross_page:same_identity=exact->correct`.

### R6. cross-page identity credit: a copy of another page's identity is credited as that other page's recovery (correct) in .10; the harness counts it neither correct nor wrong

- Cases: 0 (reachable 0); classes {}; channels {}.
- Side rows: {'b_looser_credit': 226} on 47 distinct rows.
- Distinct truth rows: 0; in the run set (`RUN-SET-PROPOSAL.json`): 26 (F006|1|identity, F006|2|identity, F009|1|identity, F009|4|identity, F016|1|identity, F016|2|identity, F016|3|identity, F016|4|identity, F020|1|identity, F020|4|identity, F021|1|identity, F021|4|identity …).
- The offered row itself is at parity (harness: a cross-page copy, missed / absent_accepted; .10: the same on that row); the divergence is the credit .10 gives to the SOURCE page's row (`associate_group` -> `cross_page`, m2_eval6.py:268-271; the fact is judged against the other component in `judge_group` and counted in that component's recovery, `score_layer` lines 369-389).
- Code: see the matrix rows.
  - e.g. `FX-00041/register`: side row `F001|1|identity` .10 **correct**, harness missed.
  - e.g. `FX-00376/register`: side row `F006|2|identity` .10 **correct**, harness missed.
  - e.g. `FX-00418/register`: side row `F006|1|identity` .10 **correct**, harness missed.

### H1. revision with whitespace inside the number ('0 0', '0 1'): .10 reads the first token, the harness keeps '00' / '01' unparsed; both depart from (i2) differently

- Cases: 74 (reachable 74); classes {'b_looser_accepts_wrong': 74}; channels {'register': 37, 'ai_validated': 37}.
- Distinct truth rows: 37; in the run set (`RUN-SET-PROPOSAL.json`): 15 (F009|3|revision, F009|4|revision, F020|3|revision, F020|4|revision, F021|1|revision, F021|3|revision, F021|4|revision, F030|3|revision, F030|4|revision, F032|1|revision, F032|3|revision, F032|4|revision …).
- Variants: `ws_inside_number` 74.
- Code: `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:240-241` (compare.revision_norm_rev); `m2_eval4.py:80-91` (truth.revision_truth); `m2_pilot_eval.py:84-93` (v3.norm_rev_first_token).
  - e.g. `FX-00512/register` `F007|2|revision` truth `00`, offered `0 0`: .10 **correct**, harness critical_false_acceptance -- `revision:single_component:norm_rev_equal->correct`.
  - e.g. `FX-00566/register` `F008|1|revision` truth `00`, offered `0 0`: .10 **correct**, harness critical_false_acceptance -- `revision:single_component:norm_rev_equal->correct`.
  - e.g. `FX-00632/register` `F008|3|revision` truth `00`, offered `0 0`: .10 **correct**, harness critical_false_acceptance -- `revision:single_component:norm_rev_equal->correct`.

### R7. decision vocabulary: .10 compares decision WORDS (approved / ANN / rejected); any other text is dropped by record_groups (register: status not in POSITIVE) or judged wrong on the AI path, including a negative word such as 'UR' (a false positive on an ABSENT row). The application never emits such text (only approved / ANN / rejected)

- Cases: 1501 (reachable 0); classes {'a_stricter_critical': 676, 'a_stricter_recovery': 549, 'b_looser_hides_wrong': 276}; channels {'ai_validated': 676, 'register': 825}.
- Distinct truth rows: 127; in the run set (`RUN-SET-PROPOSAL.json`): 51 (F006|1|decision, F006|2|decision, F009|1|decision, F009|2|decision, F009|3|decision, F009|4|decision, F015|1|decision, F016|1|decision, F016|2|decision, F016|3|decision, F016|4|decision, F018|1|decision …).
- Variants: `literal_exact` 136, `no_decision_word:UR` 127, `literal_case_lower` 112, `literal_ws_extra` 110, `literal_ws_removed` 110, `synonym:No objection with comments` 98, `synonym:approved with comments` 98, `synonym:Approved as Noted` 96, `code_D_with_legend` 81, `synonym:approved as noted` 76.
- Code: `m2_eval6.py:325-330` (association.negative_page); `m2_eval6.py:272-276` (association.single_component); `m2_eval6.py:242-242` (compare.decision_word_equality); `m2_eval4.py:52-52` (constant.POSITIVE); `m2_eval6.py:392-392` (critical.acceptance_outcomes); `m2_eval4.py:65-77` (truth.decision_truth); `m2_pilot_eval.py:44-46` (v3.DECISION_WORDS).
  - e.g. `FX-00037/ai_validated` `F001|1|decision` truth `ABSENT`, offered `UR`: .10 **critical_false_acceptance**, harness absent_accepted -- `truth:decision_negative->fp`.
  - e.g. `FX-00047/ai_validated` `F001|2|decision` truth `Approved as noted / Resubmit (class approved as noted)`, offered `Code D - Rejected`: .10 **critical_false_acceptance**, harness correct -- `decision:single_component:word_differs->wrong`.
  - e.g. `FX-00049/ai_validated` `F001|2|decision` truth `Approved as noted / Resubmit (class approved as noted)`, offered `Revise & Resubmit`: .10 **critical_false_acceptance**, harness correct -- `decision:single_component:word_differs->wrong`.

## 6. NOT_SCORABLE rows (category c)

- 32 NOT_SCORABLE rows, 242 cases: absent, the literal or each candidate, the class word, a wrong value. Excluded by both: 242; read as absent by .10: 0; scored by .10: 0.
- Code: the converter encodes NOT_SCORABLE as `ambiguous`; `m2_eval4.UNSCORABLE` (line 48) makes `reference_truth` / `revision_truth` / `decision_truth` return `unscorable`, and `judge_group` returns `unscorable` for every fact judged against it. Covered: F019 p1 revision (candidates 00 / 01), F069 p1-p4 identity (incl. the job number EP-15744 and the absent p2 / p4), every uncertain-association row (the `- R0n` suffix revisions, the EMAAR register letters, F024 / F029 reply-sheet identities, F002 p1 revision) and every ambiguous row (F035 p2 revision, F035 p3 decision, F043 p2-p4 identity, F067 decision).
- Difference that is not a divergence of verdict: the harness **reports** an automatic acceptance on a NOT_SCORABLE row that contradicts every literal and candidate (`critical_on_unresolved_truth`, never a stop); .10 excludes it silently.

## 7. Where the frozen harness itself departs from the written conventions (for the ORCH-07 disclosure list)

The intent column of each fixture records what the conventions and the declared interpretations say. These register-channel fixtures get a harness verdict different from that intent (they are harness facts, not evaluator divergences):

| Intent | Variant / group | Harness verdict | Fixtures | Examples |
| --- | --- | --- | --- | --- |
| correct | `d1:B+R` | critical_false_acceptance | 7 | F001|2|decision `B+R`; F017|1|decision `B+R` |
| correct | `synonym:B` | critical_false_acceptance | 48 | F001|2|decision `B`; F002|1|decision `B` |
| correct | `synonym:Code B` | critical_false_acceptance | 39 | F001|2|decision `Code B`; F002|1|decision `Code B` |
| correct | `synonym:Code B+R` | critical_false_acceptance | 49 | F001|2|decision `Code B+R`; F002|1|decision `Code B+R` |
| correct | `synonym:Code C` | critical_false_acceptance | 5 | F011|1|decision `Code C`; F011|2|decision `Code C` |
| correct | `ws_inside_number` | critical_false_acceptance | 53 | F001|1|revision `0 2`; F007|2|revision `0 0` |
| page_keyed_wrong | `compilation_page_keyed` | absent_accepted | 3 | F002|3|identity `TAK-02041-MCR-EL-013`; F002|3|identity `SAIFCO-351-MEP-MAR-EL-12` |
| wrong | `code_D_with_legend` | correct | 13 | F001|2|decision `Code D - Rejected`; F011|1|decision `Code D - Rejected` |
| wrong | `digit_changed` | missed | 3 | F025|3|identity `B01-02-ASC_EGTS-T01_SCH-SD-EML-0030.02`; F038|2|identity `F.F-01` |
| wrong | `labelled_tail_not_printed_on_this_page` | missed | 13 | F008|1|identity `B01-ASC-SD-ELE-0102-Rev.00`; F009|1|identity `B01-ASC-SD-ELE-0034-Rev.00` |
| wrong | `segment_dropped` | missed | 6 | F014|2|identity `103`; F014|3|identity `103` |

- **H1** revision with whitespace inside the number ('0 1') is a critical in the harness (`norm_revision` keeps '01' unparsed), contrary to (i2); .10 reads the first token and accepts '0 0' for '00' by accident.
- **H2** 'Code D - Rejected' (class rejected under (e)/D-001) matches a revise-and-resubmit row and a (d1) row because the word 'rejected' maps to both classes (the declared 'application rejected = revise-and-resubmit' interpretation). The application itself emits only `rejected`, so the distinction cannot be scored; disclose.
- **H3** code letters without their legend ('B', 'Code B', 'Code C', 'B+R', 'Code B+R') are unrecognised and scored as a critical (unless equal to the printed literal). Not reachable from the application.
- **H4** on a compilation, an identity of another page offered on a page whose identity is ABSENT (F002 p3) is forgiven as a cross-page copy (`lane_judge_r32.judge_row`, ABSENT branch, has no compilation check, unlike its value branch). F002 is not in the run set.
- **H5** a wrong value that happens to equal another page's identity of the same drawing set (e.g. F038 'F.F-00' with one digit changed = 'F.F-01') is a cross-page copy (missed), never a critical -- the R34-06 rule as declared.

## 8. What a live r32 run would see (evaluator emission + harness judge)

Against `harness_wired` (the facts .10's emission functions extract, judged by the harness), the classes are {'parity': 7126, 'a_stricter_critical': 2124, 'b_looser_accepts_wrong': 86, 'b_looser_hides_wrong': 32, 'c_not_scorable_excluded': 242} (reachable {'parity': 5898, 'a_stricter_critical': 1448, 'b_looser_accepts_wrong': 86, 'b_looser_hides_wrong': 32, 'c_not_scorable_excluded': 212}). The register channel's decision filter (`record_groups`: status in `m2_eval4.POSITIVE`) removes the same text for both, so R7's register cases become parity; every judging divergence remains. In the frozen review34 path the judge is the harness, so these divergences describe what binding .10's judging would change, not what review34 computes.

## 9. Can a declared normaliser before the evaluator reconcile them (without changing the evaluator), and is it safe?

`scripts/normaliser_experiment_r35.py` (analysis only, not bound code) re-ran every fixture through .10 after two hypothetical normalisers, applied to the predicted value and to the converter's truth encoding:

- **N1 (blind):** identity dash glyphs -> '-'; revision through `literal_compare_r32.norm_revision` ('R<n>' -> '<n>'); a decision text that is not an application word -> the application's own `evidence_reader.option_decision` reading.
- **N2 (truth-aware, on top of N1):** a value the harness matches to its own row is replaced by that row's encoding; a copy of another page's identity of the same non-compilation document is dropped; a decision that asserts none is dropped; the compilations F002, F035, F043, F069 are split into one evaluator document per page.

| Normaliser | Parity (reachable) | a critical | a recovery | b accepts wrong | b hides wrong | side credits | wrong-value controls .10 accepts, harness rejects | wrong-value controls both accept (H2) | NOT_SCORABLE scored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N0 (none) | 5898 | 1448 | 0 | 86 | 32 | 270 | 12 | 0 | 0 |
| N1 | 7214 | 112 | 0 | 106 | 32 | 270 | 0 | 12 | 0 |
| N2 | 7352 | 6 | 0 | 106 | 0 | 0 | 0 | 26 | 0 |

Residual reachable divergences:

- **N1:** a_stricter_critical decision `d1:rejected` 14; a_stricter_critical identity `g1_labelled_tail_lower` 24; a_stricter_critical identity `g1_labelled_tail_present` 24; a_stricter_critical identity `g1_labelled_tail_present_ws` 24; a_stricter_critical identity `labelled_tail_not_printed_on_this_page` 26; b_looser_accepts_wrong revision `ws_inside_number` 106; b_looser_hides_wrong identity `compilation_page_keyed` 32.
- **N2:** a_stricter_critical identity `compilation_page_keyed` 6; b_looser_accepts_wrong revision `ws_inside_number` 106.

- **Answer.** Yes, they can be reconciled without changing the evaluator, but only by a **truth-aware** normaliser (N2): the blind N1 removes R1, R2 and R2b but leaves R3 / R3b ((g)(1) tails), R4 ((d1) 'rejected'), R5 (compilation cross-page) and R6 (cross-page credit), because those are row- and page-specific rules, not value spellings (N1 also widens H1). Under N2 the only reachable residuals are where the harness itself departs from the conventions (H1 whitespace inside a revision number, H4 F002 p3).
- **Safety.** In this test neither N1 nor N2 made .10 accept a wrong-value control that the harness rejects, or score a NOT_SCORABLE row, while N0 (no normaliser) accepts 12 (the F043 'Rev. <n>' cases). Both normalisers make .10 accept `Code D - Rejected` where the harness also accepts it (H2: N1 12, N2 26 cases): they inherit the harness's own interpretation. N2 is the harness comparison relocated in front of the evaluator: it needs the truth, it is a second implementation of `literal_compare_r32` / `lane_judge_r32` rules (a second place to freeze, review and keep in step), and after it .10 contributes only accounting. N1 alone accepts no value the harness rejects, but still raises false criticals on (g)(1) tails and (d1) rows and keeps R5 / R6. **Not recommended** over binding the frozen judge directly.

## 10. Recommendation for ORCH-07

**Bind evaluator .10 as is in its EMISSION role only, and do not bind its judging.** Concretely:

1. The scoring path is the frozen review34 path accepted by Review 35: `score_lane_r32.py` / `tripwire_r32.facts_from_row` use .10's `record_groups`, `observation_groups` and `ai_groups` (m2_eval6.py lines 79-215, sha256 `268d8623…`) to extract facts, and **every** verdict -- recovery, precision, criticals and the per-field tripwire, coverage, controls -- comes from `lane_judge_r32` + `literal_compare_r32`. `EV.evaluate`, `associate_group`, `judge_group`, `score_layer` and `_same` are not used for any metric, gate or stop. Plan v2 section 4 step 7 ('evaluator .10') is to be read that way in the declaration.
2. **No candidate correction is required for that binding.** The candidate stays at `a8aacedd…`. Known strictness losses under it: none from .10's judging (not used). The one emission-level filter -- a register record's decision becomes a fact only when its status is `approved` / `ANN` / `rejected` (`record_groups`, m2_eval6.py:90; `m2_eval4.POSITIVE`) -- applies to B and C alike, drops none of the application's decision words, and a negative word such as `UR` asserts no decision in the harness either (section 8: against `harness_wired` the register-channel R7 cases are parity). Binding .10's judging as is would instead carry the false criticals R1-R4 and the hidden or credited values R2b, R5, R6 into the tripwire and the metrics.
3. Interpretations to list (Review 35 item 10, confirmed here at the harness level): the unlabelled `- R0n` suffix base form (8 rows; .10 parity holds, `same_identity` = suffix); the (d1) tolerance including the application's `rejected` (7 scorable rows; .10 does NOT have it, R4); application `rejected` = revise-and-resubmit; the cross-page identity rule for drawing sets F016 / F038 (and F014) -- the harness forgives a copy as neither correct nor wrong, .10 additionally credits the other page (R6); F069 p2 / p4 NOT_SCORABLE (excluded by both); one failure per (document, field).
4. Disclosures to add from this test: H1-H5 (section 7); that .10's own judging differs on R1-R7 (section 5) and therefore earlier .10-scored results (four-arm and before) are not comparable one-to-one with r32 harness scores on dashes, labelled revisions, (g)(1) tails, (d1) rows, compilations and cross-page credit.
5. **If ORCH-07 instead wants .10's judging to produce any verdict, a candidate correction is required before any live run** (a new candidate commit with its own independent review), changing exactly:
   - **R1** `m2_pilot_eval.norm_ref` / `same_identity`: fold the dash variants (U+2010-2015, U+2212, U+FE58, U+FE63, U+FF0D) to '-' for non-Arabic literals (identity), keeping Arabic byte comparison;
   - **R2 / R2b** `m2_pilot_eval.norm_rev`: parse the whole value (`(REVISION|REV.?|R.?)\s*0*(\d+)`), not the first whitespace token, for both the truth and the prediction;
   - **R3** accept the (g)(1) either-form alternates (from the converter sidecar `identity_alternates`);
   - **R4** accept the (d1) alternative decision (`rejected`) on rows with `resubmission_required` (sidecar `decision_alternatives`);
   - **R5** page-key compilations: no cross-page association inside an (h) compilation file;
   - **R6** no recovery credit to another component from a cross-page identity copy (or declare it);
   - **R7** (optional, not reachable) decision text to class mapping on the AI path, and a negative word never an asserted decision.
   A declared truth-aware normaliser (N2, section 9) is an alternative to the commit but is not recommended.

## 11. Limits

- Synthetic facts only: one fact per case, on one page; documents with several facts per page, several components per page or held / observed states were not exercised (every r32 page has at most one component). The `observed` (deterministic observation) channel was not run; it uses the same `_same` comparison and is never critical.
- 'Application reachable' is read from code (`m2_eval4.POSITIVE`, `evidence_reader.option_decision` / `validate_decision`), not from application output; identity and revision text is treated as reachable in any spelling.
- The intent labels are this agent's reading of the conventions and Review 33-35 rulings; they do not change any verdict.
- Nothing here re-reviews the reference set; it is independently AI-reviewed (Claude agents) and not human-signed.

## 12. Statuses, stated separately

1. **Source permission:** A-02 (access, staging, drafting, preparation) and A-06 (eligibility only) unchanged; neither authorizes dispatch.
2. **Drafting:** `r32-labels-draft-1` frozen, AI-drafted (Claude Opus 5.5), not human-signed.
3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents) and **not human-signed**.
4. **Populations:** identity 57, revision 38, decision 38.
5. **Conditions:** C-6 answered by this package, **pending ORCH-06V** (independent read-only verification).
6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch. AI ledger 483 entries / 17 scopes before and after (read-only).
7. **M2:** CHANGES STILL REQUIRED.
8. **M3:** not started.

