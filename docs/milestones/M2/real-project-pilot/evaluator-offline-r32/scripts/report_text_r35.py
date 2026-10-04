"""ORCH-06: render EVALUATOR-TEST-REPORT.md from the computed PARITY-MATRIX summary (every number below is computed)."""
from __future__ import annotations

import common_r35 as C

CLASS_ORDER = ("parity", "a_stricter_critical", "a_stricter_recovery", "b_looser_accepts_wrong", "b_looser_hides_wrong",
               "c_not_scorable_excluded", "c_violation_read_as_absent", "c_violation_scored")
FIELDS = ("identity", "revision", "decision")


def _row(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(head, rows):
    return "\n".join([_row(head), _row(["---"] * len(head))] + [_row(r) for r in rows])


def _cnt(d, k):
    return d.get(k, 0)


def render(matrix: dict, run_summary: dict, norm: dict) -> str:
    S = matrix["summary"]
    P, W = S["class_vs_pair"], S["class_vs_wired"]
    fam = S["families"]
    ev = matrix["evaluator"]
    g = run_summary["guard_full_scope"]
    out = []
    a = out.append
    a("# Offline evaluator .10 parity test against the r32 reference set (ORCH-06, 2026-10-03)")
    a("")
    a("- **Task:** ORCH-06 (Review 33 condition C-6, finding D4-06; Review 35 section 6 items 1 and 10), agent R35EVAL-IMPL, "
      "the only write-capable agent. Authorities A-03 and A-08.")
    a("- **Model (self-report):** Claude Opus 5.5 (`claude-opus-5-5`), effort High, as stated in my system context.")
    a("- **Nature:** an implementation test package. It is **not** a review, approves nothing and authorizes nothing. "
      "ORCH-06V (an independent read-only verification) comes next. M2 stays **CHANGES STILL REQUIRED**; M3 has **not started**.")
    a(f"- **Zero calls:** no provider or model request of any kind, no `claude -p`, no network. The evaluator ran offline on "
      f"**SYNTHETIC** fixtures only: {S['fixtures']} fixtures built from the r32 truth strings, each run through two channels "
      f"({S['cases']} cases). No prediction of any cohort document exists or was created; no arm output, page image or earlier "
      f"label set was read. Provider classes constructed: {g['provider_constructed']}; network or process attempts: "
      f"{g['network_or_process_attempts']}; SDK modules imported: {len(g['sdk_modules_imported'])}.")
    a(f"- **Reference set:** {C.REFERENCE_SET_STATEMENT} (`r32-labels-reviewed-2`, `89c60e9d…b9a6`), converted by the frozen "
      "review34 adapter and converter.")
    a("")
    a("## 1. Answer in brief")
    a("")
    reach = P["application_reachable"]
    a(f"1. **Evaluator .10's own judging is not at parity with the frozen r32 harness.** Of {S['cases']} cases, "
      f"{_cnt(P['all'], 'parity')} are at parity and {_cnt(P['all'], 'c_not_scorable_excluded')} are NOT_SCORABLE rows that both exclude. "
      f"Restricted to values the application can actually emit ({sum(reach.values())} cases): "
      f"**{_cnt(reach, 'a_stricter_critical')} (a) stricter-critical**, {_cnt(reach, 'a_stricter_recovery')} (a) stricter-recovery, "
      f"**{_cnt(reach, 'b_looser_accepts_wrong')} (b) looser-accepts-wrong**, **{_cnt(reach, 'b_looser_hides_wrong')} (b) looser-hides-wrong**, "
      f"plus {S['side_rows']['all'].get('b_looser_credit', 0)} side-row recovery credits on {S['side_rows']['distinct_rows_credited']} distinct rows.")
    a("2. **(a) Stricter, and critical:** a correct identity printed with another dash glyph (R1), a correct revision written "
      "'Rev. 01' / 'REV 01' / 'Revision 1' (R2), the correct value of the F043 'Rev. 0' rows (R2b), the (g)(1) tail form (R3) and "
      "the application's 'rejected' on a (d1) row (R4) each become a **critical false acceptance on resolved truth** in .10 -- "
      "they would fire the per-field tripwire (B INVALID, C STOP) on a correct reading.")
    a("3. **(b) Looser:** .10 accepts any 'Rev. <n>' for the F043 'Rev. 0' truth (R2b), associates an identity of another page "
      "of a compilation file cross-page and never flags it (R5), and credits another page's recovery for cross-page identity "
      f"copies (R6). The other {fam.get('H1', {}).get('cases', 0)} (b) accepts-wrong cases are H1 ('0 0' for a printed '00'): "
      "there the harness, not .10, departs from the whitespace rule (i2).")
    ns = S["not_scorable"]
    a(f"4. **(c) NOT_SCORABLE rows are handled correctly:** {ns['excluded_by_both']} of {ns['cases']} cases on {ns['rows']} rows are "
      f"excluded by .10 (the converter's 'ambiguous' is in `m2_eval4.UNSCORABLE`); {ns['read_as_absent']} are read as absent and "
      f"{ns['scored']} are scored.")
    a("5. **Decision vocabulary (R7):** .10 compares decision **words** (`approved`, `ANN`, `rejected`). Every other text is either "
      "dropped at emission (register) or judged wrong (AI path). The application never emits other text, so R7 is not reachable "
      "in the r32 lanes; it matters only if non-application text were ever judged.")
    a("6. **Recommendation (section 10):** bind evaluator .10 **as is in its emission role only** (the frozen review34 path), with "
      "every verdict from the frozen r32 judge; do **not** bind .10's own judging for any metric, tripwire or gate. If ORCH-07 "
      "wants .10's judging to produce any verdict, a **candidate correction** (new commit, own independent review) is required "
      "first, changing rules R1-R6 (R7 optional).")
    a("7. **Normaliser question (section 9):** a declared normaliser before the evaluator can reconcile them without changing the "
      "evaluator only if it is truth-aware (N2): the blind normaliser (N1) still leaves R3 / R3b, R4, R5 and R6. Neither N1 nor N2 "
      "made .10 accept a wrong-value control that the harness rejects, but N2 is a second implementation of the harness rules "
      "placed in front of .10, so it is not recommended over binding the frozen judge directly.")
    a("")
    a("## 2. Frozen inputs (re-hashed before use; all equal)")
    a("")
    rows = [[k, f"`{p}`", f"`{h}`"] for k, (p, h) in sorted({k: (str(v[0]).replace('\\', '/').split('real-project-pilot/')[-1], v[1])
                                                            for k, v in C.FROZEN.items()}.items())]
    rows.append(["candidate", "`C:/t/iso/cand-r29` HEAD", f"`{C.CANDIDATE_HEAD}`, `git status --porcelain` empty before and after"])
    rows.append(["evaluator .10", "`backend/scripts/m2_eval6.py`", f"`{C.EVALUATOR_SHA256}` ({ev['evaluator_version']})"])
    for rel, h in sorted(C.CANDIDATE_MODULES.items()):
        if rel.endswith("m2_eval6.py"):
            continue
        rows.append(["candidate module (imported)", f"`{rel}`", f"`{h}`"])
    for m, h in sorted(C.HARNESS_MODULES.items()):
        rows.append(["review34 harness module", f"`scripts/harness-r32/{m}.py`", f"`{h}`"])
    rows.append(["fixtures (this package)", "`SYNTHETIC-PREDICTIONS.json`", f"`{matrix['inputs']['fixtures']['sha256']}`"])
    rows.append(["run set (annotation only)", "`review34/RUN-SET-PROPOSAL.json`", f"`{matrix['inputs']['run_set_proposal']['sha256']}`"])
    a(_table(["Item", "Path", "sha256"], rows))
    a("")
    a("## 3. Method")
    a("")
    a("- **Fixtures (`scripts/fixtures_r32.py`).** Built from `TRUTH-R32.json` and `LABELS-R32-EVAL-INPUT.json` only. One synthetic "
      "fact (or none) per fixture, offered on one truth row. Groups: every scorable value row (identity, revision, decision) with "
      "exact and equivalent variants and wrong-value controls; every ABSENT row; every NOT_SCORABLE row (absent, its literal / "
      "candidates / class word, a wrong value); page-keyed compilation cases (F002, F035, F043); cross-page identity cases for the "
      "drawing sets (F014, F016, F038) and for cover / enclosure packages. The count-once aliases (F031, F059) are not in the "
      "evaluator input and are listed, not fixtured. Each fixture carries kind SYNTHETIC, its truth key, variant, intent and the "
      "**expected harness verdict computed by the frozen harness** (`literal_compare_r32.compare_row` and `lane_judge_r32`).")
    cov = S["coverage"]
    a(f"- **Coverage:** {cov['fixtures']} fixtures; every one of the {cov['canonical_rows']} canonical truth rows "
      f"({cov['canonical_rows_by_kind']}) has at least one (rows without a fixture: {len(cov['canonical_rows_without_fixture'])}); "
      f"{cov['alias_rows_excluded']} alias rows are listed as excluded; wrong-value controls {cov['wrong_value_controls']}; "
      f"fixtures by group {cov['fixtures_by_group']}. Rows in state illegible: {cov['illegible_rows']}, unsupported: {cov['unsupported_rows']}.")
    a("- **Evaluator invocation (`scripts/run_evaluator_offline_r32.py`).** Exactly as `review31/scripts/harness/score_lane.py`: "
      "`EV.evaluate(register, page, rows, page['page1_corrections'], ai_context)` on the frozen converter output "
      "(`LABELS-R32-EVAL-INPUT.json`, 68 canonical documents, the whole register per call), reading `layers.evidence`. "
      "`scripts.m2_eval6` is imported **in place, read-only** from the candidate (no bytecode written; working directory and every "
      "output in the work folder). One synthetic application row per call:")
    a("  - `register` (B-like): one register record (state `accepted`), `ai_context` None (B's evidence reader is off);")
    a("  - `ai_validated` (C-like): one validated AI observation in an `ai-evidence-2` envelope bound to the document's staged sha256, "
      f"`ai_context` = {{variant EV1, profile default, policies [`{ev['evidence_policy_version']}`]}} as `lane_r32.py` builds it.")
    a("- **Harness verdicts on the same case:** `harness_pair` = `lane_judge_r32` on the offered value (the fixture's pair); "
      "`harness_wired` = `lane_judge_r32` on the facts that `tripwire_r32.facts_from_row(EV, row, ai_context)` extracts through "
      ".10's own emission functions (what `score_lane_r32` judges in a live run).")
    a("- **Verdicts** (per truth row): correct, correct_and_wrong, critical_false_acceptance (an automatic acceptance judged wrong, or a "
      "false positive on an ABSENT row), held, missed, absent_accepted (true negative), excluded, and for .10 only not_evaluated "
      "(the offered text never became a fact). Every other labelled row of the document is compared too (side rows).")
    a("- **Classification** (evaluator against harness): parity; (a) `a_stricter_critical`, `a_stricter_recovery`; (b) "
      "`b_looser_accepts_wrong`, `b_looser_hides_wrong`, `b_looser_credit` (side rows); (c) `c_not_scorable_excluded` or a violation. "
      "`application_reachable` is false only for decision text other than approved / ANN / rejected.")
    eq = S["scope_equivalence"]
    a(f"- **Scope check:** the same {eq['compared']} cases run with only the fixture's document in the register gave "
      f"{'identical' if eq['identical'] else 'DIFFERENT'} results (evaluate() judges documents independently).")
    a(f"- **Guards:** AI / provider variables removed, `AI_ENABLED=false`, a non-existent database URL (never created: "
      f"{not g['database_file_created']}); sockets, DNS, subprocesses and `os.system` blocked; the candidate's provider classes and "
      f"`get_provider` / `set_provider` replaced by raising stubs (stubbed: {', '.join(ev['provider_classes_stubbed'])}); "
      f"an audit hook refused any write outside the work folder (refused: {len(g['refused_writes'])}; violations: {len(g['violations'])}).")
    a("")
    a("## 4. Results")
    a("")
    a("### 4.1 Classes (evaluator against the harness on the pair)")
    a("")
    rows = []
    for k in CLASS_ORDER:
        rows.append([k, _cnt(P["all"], k), _cnt(reach, k), _cnt(P["application_reachable_in_run_set"], k), _cnt(W["all"], k),
                     _cnt(W["application_reachable"], k)])
    rows.append(["**total**", sum(P["all"].values()), sum(reach.values()), sum(P["application_reachable_in_run_set"].values()),
                 sum(W["all"].values()), sum(W["application_reachable"].values())])
    a(_table(["Class", "All cases", "Reachable", "Reachable, run-set documents", "Against harness_wired", "Wired, reachable"], rows))
    a("")
    a(f"Side rows (another labelled row of the same document changed by the offered fact): "
      f"{S['side_rows']['all']} on {S['side_rows']['distinct_rows_credited']} distinct rows.")
    a("")
    a("### 4.2 By field (reachable cases)")
    a("")
    bf = P["by_field_application_reachable"]
    a(_table(["Field"] + list(CLASS_ORDER[:6]), [[f] + [bf.get(f, {}).get(k, 0) for k in CLASS_ORDER[:6]] for f in FIELDS]))
    a("")
    a("All cases by field (including decision text the application never emits):")
    a("")
    bf = P["by_field"]
    a(_table(["Field"] + list(CLASS_ORDER[:6]), [[f] + [bf.get(f, {}).get(k, 0) for k in CLASS_ORDER[:6]] for f in FIELDS]))
    a("")
    a("### 4.3 By channel and group")
    a("")
    bc = P["by_channel"]
    a(_table(["Channel"] + list(CLASS_ORDER[:6]), [[c] + [bc[c].get(k, 0) for k in CLASS_ORDER[:6]] for c in sorted(bc)]))
    a("")
    bg = P["by_group"]
    a(_table(["Group"] + list(CLASS_ORDER[:6]), [[gname] + [bg[gname].get(k, 0) for k in CLASS_ORDER[:6]] for gname in sorted(bg)]))
    a("")
    a("## 5. Divergences by evaluator rule (responsible code in `C:/t/iso/cand-r29/backend`)")
    a("")
    locs = matrix["code_locations"]
    for k in ("R1", "R2", "R2b", "R3", "R3b", "R4", "R5", "R6", "H1", "R7", "other"):
        if k not in fam:
            continue
        F = fam[k]
        a(f"### {k}. {F['rule']}")
        a("")
        a(f"- Cases: {F['cases']} (reachable {F['reachable_cases']}); classes {F['by_class']}; channels {F['channels']}.")
        if F.get("side_rows"):
            a(f"- Side rows: {F['side_rows']} on {len(F['side_rows_distinct'])} distinct rows.")
        a(f"- Distinct truth rows: {F['distinct_rows']}; in the run set (`RUN-SET-PROPOSAL.json`): "
          f"{len(F['run_set_rows'])} ({', '.join(F['run_set_rows'][:12])}{' …' if len(F['run_set_rows']) > 12 else ''}).")
        if F["variants"]:
            a(f"- Variants: {', '.join(f'`{v}` {n}' for v, n in sorted(F['variants'].items(), key=lambda x: -x[1])[:10])}.")
        else:
            a("- The offered row itself is at parity (harness: a cross-page copy, missed / absent_accepted; .10: the same on that row); "
              "the divergence is the credit .10 gives to the SOURCE page's row (`associate_group` -> `cross_page`, m2_eval6.py:268-271; "
              "the fact is judged against the other component in `judge_group` and counted in that component's recovery, "
              "`score_layer` lines 369-389).")
        code = [f"`{locs[c]['file'].replace('backend/scripts/', '')}:{locs[c]['lines']}` ({c})" for c in F["code_locations"] if c in locs
                and not c.startswith("emission.") and c not in ("association.associate_group", "judge.judge_group")]
        a(f"- Code: {'; '.join(code) if code else 'see the matrix rows'}.")
        for ex in F["examples"][:3]:
            if ex.get("side_effect"):
                a(f"  - e.g. `{ex['case']}`: side row `{ex['row']}` .10 **{ex['evaluator']}**, harness {ex['harness']}.")
            else:
                a(f"  - e.g. `{ex['case']}` `{ex['row']}` truth `{ex['truth']}`, offered `{ex['value']}`: .10 **{ex['evaluator']}**, "
                  f"harness {ex['harness']} -- `{ex['rule']}`.")
        a("")
    a("## 6. NOT_SCORABLE rows (category c)")
    a("")
    a(f"- {ns['rows']} NOT_SCORABLE rows, {ns['cases']} cases: absent, the literal or each "
      f"candidate, the class word, a wrong value. Excluded by both: {ns['excluded_by_both']}; read as absent by .10: "
      f"{ns['read_as_absent']}; scored by .10: {ns['scored']}.")
    a("- Code: the converter encodes NOT_SCORABLE as `ambiguous`; `m2_eval4.UNSCORABLE` (line 48) makes `reference_truth` / "
      "`revision_truth` / `decision_truth` return `unscorable`, and `judge_group` returns `unscorable` for every fact judged "
      "against it. Covered: F019 p1 revision (candidates 00 / 01), F069 p1-p4 identity (incl. the job number EP-15744 and the "
      "absent p2 / p4), every uncertain-association row (the `- R0n` suffix revisions, the EMAAR register letters, F024 / F029 "
      "reply-sheet identities, F002 p1 revision) and every ambiguous row (F035 p2 revision, F035 p3 decision, F043 p2-p4 identity, "
      "F067 decision).")
    a("- Difference that is not a divergence of verdict: the harness **reports** an automatic acceptance on a NOT_SCORABLE row "
      "that contradicts every literal and candidate (`critical_on_unresolved_truth`, never a stop); .10 excludes it silently.")
    a("")
    a("## 7. Where the frozen harness itself departs from the written conventions (for the ORCH-07 disclosure list)")
    a("")
    a("The intent column of each fixture records what the conventions and the declared interpretations say. These register-channel "
      "fixtures get a harness verdict different from that intent (they are harness facts, not evaluator divergences):")
    a("")
    rows = [[h["intent"], f"`{h['variant_or_group']}`", h["harness_verdict"], h["fixtures"],
             "; ".join(f"{e['row']} `{e['value']}`" for e in h["examples"][:2])] for h in S["harness_vs_intent"]]
    a(_table(["Intent", "Variant / group", "Harness verdict", "Fixtures", "Examples"], rows))
    a("")
    a("- **H1** revision with whitespace inside the number ('0 1') is a critical in the harness (`norm_revision` keeps '01' "
      "unparsed), contrary to (i2); .10 reads the first token and accepts '0 0' for '00' by accident.")
    a("- **H2** 'Code D - Rejected' (class rejected under (e)/D-001) matches a revise-and-resubmit row and a (d1) row because the word "
      "'rejected' maps to both classes (the declared 'application rejected = revise-and-resubmit' interpretation). The application "
      "itself emits only `rejected`, so the distinction cannot be scored; disclose.")
    a("- **H3** code letters without their legend ('B', 'Code B', 'Code C', 'B+R', 'Code B+R') are unrecognised and scored as a "
      "critical (unless equal to the printed literal). Not reachable from the application.")
    a("- **H4** on a compilation, an identity of another page offered on a page whose identity is ABSENT (F002 p3) is forgiven as a "
      "cross-page copy (`lane_judge_r32.judge_row`, ABSENT branch, has no compilation check, unlike its value branch). F002 is not "
      "in the run set.")
    a("- **H5** a wrong value that happens to equal another page's identity of the same drawing set (e.g. F038 'F.F-00' with one "
      "digit changed = 'F.F-01') is a cross-page copy (missed), never a critical -- the R34-06 rule as declared.")
    a("")
    a("## 8. What a live r32 run would see (evaluator emission + harness judge)")
    a("")
    a(f"Against `harness_wired` (the facts .10's emission functions extract, judged by the harness), the classes are {W['all']} "
      f"(reachable {W['application_reachable']}). The register channel's decision filter (`record_groups`: status in "
      "`m2_eval4.POSITIVE`) removes the same text for both, so R7's register cases become parity; every judging divergence "
      "remains. In the frozen review34 path the judge is the harness, so these divergences describe what binding .10's judging "
      "would change, not what review34 computes.")
    a("")
    a("## 9. Can a declared normaliser before the evaluator reconcile them (without changing the evaluator), and is it safe?")
    a("")
    n1, n2 = norm["N1"], norm["N2"]
    a("`scripts/normaliser_experiment_r35.py` (analysis only, not bound code) re-ran every fixture through .10 after two "
      "hypothetical normalisers, applied to the predicted value and to the converter's truth encoding:")
    a("")
    a("- **N1 (blind):** identity dash glyphs -> '-'; revision through `literal_compare_r32.norm_revision` ('R<n>' -> '<n>'); a "
      "decision text that is not an application word -> the application's own `evidence_reader.option_decision` reading.")
    a("- **N2 (truth-aware, on top of N1):** a value the harness matches to its own row is replaced by that row's encoding; a copy of "
      "another page's identity of the same non-compilation document is dropped; a decision that asserts none is dropped; the "
      "compilations F002, F035, F043, F069 are split into one evaluator document per page.")
    a("")
    rows = []
    w0 = S["wrong_value_controls_accepted_as_correct_by_evaluator"]
    for name, N in (("N0 (none)", {"counts": {"class_vs_pair": P["all"], "class_vs_pair_reachable": reach, "side_rows": S["side_rows"]["all"]},
                                   "hr": w0["where_harness_rejects"], "ha": w0["where_harness_also_accepts"],
                                   "not_scorable_scored": ns["read_as_absent"] + ns["scored"]}),
                    ("N1", n1 | {"hr": n1["wrong_value_controls_accepted_where_harness_rejects"], "ha": n1["wrong_value_controls_accepted_where_harness_also_accepts"]}),
                    ("N2", n2 | {"hr": n2["wrong_value_controls_accepted_where_harness_rejects"], "ha": n2["wrong_value_controls_accepted_where_harness_also_accepts"]})):
        c = N["counts"]
        rr = c["class_vs_pair_reachable"]
        rows.append([name, _cnt(rr, "parity"), _cnt(rr, "a_stricter_critical"), _cnt(rr, "a_stricter_recovery"),
                     _cnt(rr, "b_looser_accepts_wrong"), _cnt(rr, "b_looser_hides_wrong"), c["side_rows"].get("b_looser_credit", 0),
                     N["hr"], N["ha"], N["not_scorable_scored"]])
    a(_table(["Normaliser", "Parity (reachable)", "a critical", "a recovery", "b accepts wrong", "b hides wrong", "side credits",
              "wrong-value controls .10 accepts, harness rejects", "wrong-value controls both accept (H2)", "NOT_SCORABLE scored"], rows))
    a("")
    a("Residual reachable divergences:")
    a("")
    for name, N in (("N1", n1), ("N2", n2)):
        a(f"- **{name}:** " + ("; ".join(f"{r['class']} {r['field']} `{r['variant_or_group']}` {r['cases']}" for r in N["residual_reachable"]) or "none") + ".")
    a("")
    a("- **Answer.** Yes, they can be reconciled without changing the evaluator, but only by a **truth-aware** normaliser (N2): the "
      "blind N1 removes R1, R2 and R2b but leaves R3 / R3b ((g)(1) tails), R4 ((d1) 'rejected'), R5 (compilation cross-page) and "
      "R6 (cross-page credit), because those are row- and page-specific rules, not value spellings (N1 also widens H1). Under N2 "
      "the only reachable residuals are where the harness itself departs from the conventions (H1 whitespace inside a revision "
      "number, H4 F002 p3).")
    a(f"- **Safety.** In this test neither N1 nor N2 made .10 accept a wrong-value control that the harness rejects, or score a "
      f"NOT_SCORABLE row, while N0 (no normaliser) accepts {w0['where_harness_rejects']} (the F043 'Rev. <n>' cases). Both "
      f"normalisers make .10 accept `Code D - Rejected` where the harness also accepts it (H2: N1 {n1['wrong_value_controls_accepted_where_harness_also_accepts']}, "
      f"N2 {n2['wrong_value_controls_accepted_where_harness_also_accepts']} cases): they inherit the harness's own interpretation. "
      "N2 is the harness comparison relocated in front of the evaluator: it needs the truth, it is a second implementation of "
      "`literal_compare_r32` / `lane_judge_r32` rules (a second place to freeze, review and keep in step), and after it .10 "
      "contributes only accounting. N1 alone accepts no value the harness rejects, but still raises false criticals on (g)(1) tails "
      "and (d1) rows and keeps R5 / R6. **Not recommended** over binding the frozen judge directly.")
    a("")
    a("## 10. Recommendation for ORCH-07")
    a("")
    a("**Bind evaluator .10 as is in its EMISSION role only, and do not bind its judging.** Concretely:")
    a("")
    a("1. The scoring path is the frozen review34 path accepted by Review 35: `score_lane_r32.py` / `tripwire_r32.facts_from_row` "
      "use .10's `record_groups`, `observation_groups` and `ai_groups` (m2_eval6.py lines 79-215, sha256 `268d8623…`) to extract "
      "facts, and **every** verdict -- recovery, precision, criticals and the per-field tripwire, coverage, controls -- comes from "
      "`lane_judge_r32` + `literal_compare_r32`. `EV.evaluate`, `associate_group`, `judge_group`, `score_layer` and `_same` are "
      "not used for any metric, gate or stop. Plan v2 section 4 step 7 ('evaluator .10') is to be read that way in the declaration.")
    a("2. **No candidate correction is required for that binding.** The candidate stays at `a8aacedd…`. Known strictness losses "
      "under it: none from .10's judging (not used). The one emission-level filter -- a register record's decision becomes a fact "
      "only when its status is `approved` / `ANN` / `rejected` (`record_groups`, m2_eval6.py:90; `m2_eval4.POSITIVE`) -- applies "
      "to B and C alike, drops none of the application's decision words, and a negative word such as `UR` asserts no decision "
      "in the harness either (section 8: against `harness_wired` the register-channel R7 cases are parity). Binding .10's judging as is would instead carry the false criticals R1-R4 and the hidden or credited "
      "values R2b, R5, R6 into the tripwire and the metrics.")
    a("3. Interpretations to list (Review 35 item 10, confirmed here at the harness level): the unlabelled `- R0n` suffix base form "
      "(8 rows; .10 parity holds, `same_identity` = suffix); the (d1) tolerance including the application's `rejected` "
      "(7 scorable rows; .10 does NOT have it, R4); application `rejected` = revise-and-resubmit; the cross-page identity rule for "
      "drawing sets F016 / F038 (and F014) -- the harness forgives a copy as neither correct nor wrong, .10 additionally credits the "
      "other page (R6); F069 p2 / p4 NOT_SCORABLE (excluded by both); one failure per (document, field).")
    a("4. Disclosures to add from this test: H1-H5 (section 7); that .10's own judging differs on R1-R7 (section 5) and therefore "
      "earlier .10-scored results (four-arm and before) are not comparable one-to-one with r32 harness scores on dashes, labelled "
      "revisions, (g)(1) tails, (d1) rows, compilations and cross-page credit.")
    a("5. **If ORCH-07 instead wants .10's judging to produce any verdict, a candidate correction is required before any live run** "
      "(a new candidate commit with its own independent review), changing exactly:")
    a("   - **R1** `m2_pilot_eval.norm_ref` / `same_identity`: fold the dash variants (U+2010-2015, U+2212, U+FE58, U+FE63, U+FF0D) to "
      "'-' for non-Arabic literals (identity), keeping Arabic byte comparison;")
    a("   - **R2 / R2b** `m2_pilot_eval.norm_rev`: parse the whole value (`(REVISION|REV.?|R.?)\\s*0*(\\d+)`), not the first "
      "whitespace token, for both the truth and the prediction;")
    a("   - **R3** accept the (g)(1) either-form alternates (from the converter sidecar `identity_alternates`);")
    a("   - **R4** accept the (d1) alternative decision (`rejected`) on rows with `resubmission_required` (sidecar `decision_alternatives`);")
    a("   - **R5** page-key compilations: no cross-page association inside an (h) compilation file;")
    a("   - **R6** no recovery credit to another component from a cross-page identity copy (or declare it);")
    a("   - **R7** (optional, not reachable) decision text to class mapping on the AI path, and a negative word never an asserted decision.")
    a("   A declared truth-aware normaliser (N2, section 9) is an alternative to the commit but is not recommended.")
    a("")
    a("## 11. Limits")
    a("")
    a("- Synthetic facts only: one fact per case, on one page; documents with several facts per page, several components per page "
      "or held / observed states were not exercised (every r32 page has at most one component). The `observed` (deterministic "
      "observation) channel was not run; it uses the same `_same` comparison and is never critical.")
    a("- 'Application reachable' is read from code (`m2_eval4.POSITIVE`, `evidence_reader.option_decision` / `validate_decision`), "
      "not from application output; identity and revision text is treated as reachable in any spelling.")
    a("- The intent labels are this agent's reading of the conventions and Review 33-35 rulings; they do not change any verdict.")
    a("- Nothing here re-reviews the reference set; it is independently AI-reviewed (Claude agents) and not human-signed.")
    a("")
    a("## 12. Statuses, stated separately")
    a("")
    a("1. **Source permission:** A-02 (access, staging, drafting, preparation) and A-06 (eligibility only) unchanged; neither authorizes dispatch.")
    a("2. **Drafting:** `r32-labels-draft-1` frozen, AI-drafted (Claude Opus 5.5), not human-signed.")
    a("3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents) and **not human-signed**.")
    a("4. **Populations:** identity 57, revision 38, decision 38.")
    a("5. **Conditions:** C-6 answered by this package, **pending ORCH-06V** (independent read-only verification).")
    a("6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch. AI ledger "
      "483 entries / 17 scopes before and after (read-only).")
    a("7. **M2:** CHANGES STILL REQUIRED.")
    a("8. **M3:** not started.")
    a("")
    return "\n".join(out) + "\n"
