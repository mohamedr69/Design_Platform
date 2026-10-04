"""ORCH-06: append ONE entry at the very end of docs/milestones/M2/M2-REVIEW-RESPONSE.md, after verifying its current hash.
Usage: append_response_r35.py          (refuses unless the file is exactly cc1edc4d... and holds no ORCH-06 entry yet)"""
from __future__ import annotations

import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402

BEFORE = "cc1edc4d38d54db3aae951f898106e487df68dc32112d34bd8615ed162873084"
HEADING = "# Offline evaluator .10 parity test against the r32 reference set (ORCH-06, 2026-10-03)"


def c(d, k):
    return d.get(k, 0)


def entry() -> str:
    man_path = C.PACKAGE / "evidence/EVIDENCE-MANIFEST.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man_sha = C.sha256_file(man_path)
    m = json.loads((C.PACKAGE / "PARITY-MATRIX.json").read_text(encoding="utf-8"))
    chk = json.loads((C.PACKAGE / "evidence/PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    S = m["summary"]
    P, R = S["class_vs_pair"]["all"], S["class_vs_pair"]["application_reachable"]
    W = S["class_vs_wired"]["all"]
    bf = S["class_vs_pair"]["by_field_application_reachable"]
    fam = S["families"]
    ns = S["not_scorable"]
    n1, n2 = S["normalisers"]["N1"], S["normalisers"]["N2"]
    tests = chk["checks"]["tests_pass"]["detail"]["total"]
    bm_sha = C.sha256_file(C.PACKAGE / "BINDING-MANIFEST-R35.json")
    fx_sha = C.sha256_file(C.PACKAGE / "SYNTHETIC-PREDICTIONS.json")
    fields = "; ".join(f"{f}: a-critical {c(bf.get(f, {}), 'a_stricter_critical')}, a-recovery {c(bf.get(f, {}), 'a_stricter_recovery')}, "
                       f"b-accepts-wrong {c(bf.get(f, {}), 'b_looser_accepts_wrong')}, b-hides-wrong {c(bf.get(f, {}), 'b_looser_hides_wrong')}"
                       for f in C.FIELDS)
    famline = "; ".join(f"{k} {v['cases']} cases ({v['reachable_cases']} reachable" +
                        (f", {sum(v['side_rows'].values())} side rows" if v.get("side_rows") else "") + ")" for k, v in sorted(fam.items()))
    lines = [
        "",
        HEADING,
        "",
        "**Task:** ORCH-06 (Review 33 condition C-6, finding D4-06; Review 35 section 6 items 1 and 10), agent label R35EVAL-IMPL, "
        "Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03 and A-08. The only write-capable agent. "
        "It is an implementation test package pending the independent read-only verification ORCH-06V. It is not self-approved.",
        "",
        "**Package:** `docs/milestones/M2/real-project-pilot/evaluator-offline-r32/`.",
        f"- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `{man_sha}`, written last, {man['count']} files.",
        f"- **Package check:** `evidence/PACKAGE-CHECK.json` ok, {chk['passed']} of {chk['total']} checks: every frozen input re-hashed "
        f"equal; candidate `a8aacedd` clean and no candidate file modified after the task start; no frozen file modified after "
        f"2026-10-03T13:50:00Z (the running application's own `ep_platform.db` files reported apart); {tests['tests']} tests, "
        f"{tests['failures']} failures, {tests['errors']} errors; AI ledger 483/17 read-only; no provider code path executed; no "
        "authorization file created by this task.",
        f"- **Binding manifest:** `BINDING-MANIFEST-R35.json`, sha256 `{bm_sha}`: candidate HEAD and status, evaluator .10 "
        f"`m2_eval6.py` `{C.EVALUATOR_SHA256}` and every candidate module it imported, the review34 inputs and harness modules, the "
        f"reference set and conventions, Reviews 33-35, and the fixtures `SYNTHETIC-PREDICTIONS.json` `{fx_sha}`.",
        "",
        f"**What was tested:** {S['fixtures']} SYNTHETIC fixtures built from `TRUTH-R32.json` and `LABELS-R32-EVAL-INPUT.json` only "
        f"(every one of the {S['coverage']['canonical_rows']} canonical truth rows covered; whitespace, dash, leading-zero, (g)(1) tail, "
        "suffix-base, Arabic, decision-vocabulary and (d1) variants; wrong-value controls; ABSENT and NOT_SCORABLE rows; page-keyed "
        "compilations F002 / F035 / F043; cross-page identity in drawing sets F014 / F016 / F038 and cover packages), each fed to "
        "evaluator .10 offline through two channels (register record, validated AI evidence) exactly as `score_lane.py` calls it "
        f"(`EV.evaluate(register, page, rows, corrections, ai_context)`, `layers.evidence`): **{S['cases']} cases**, each compared with "
        "the frozen harness verdict (`lane_judge_r32` / `literal_compare_r32`) on the same pair.",
        "",
        "**Results** (evaluator against the harness on the pair):",
        f"- All cases: parity {c(P, 'parity')}; (a) stricter-critical {c(P, 'a_stricter_critical')}; (a) stricter-recovery "
        f"{c(P, 'a_stricter_recovery')}; (b) looser-accepts-wrong {c(P, 'b_looser_accepts_wrong')}; (b) looser-hides-wrong "
        f"{c(P, 'b_looser_hides_wrong')}; (c) NOT_SCORABLE excluded by both {c(P, 'c_not_scorable_excluded')}; side-row recovery "
        f"credits {S['side_rows']['all'].get('b_looser_credit', 0)}.",
        f"- Values the application can emit ({sum(R.values())} cases): parity {c(R, 'parity')}; (a) critical {c(R, 'a_stricter_critical')}; "
        f"(a) recovery {c(R, 'a_stricter_recovery')}; (b) accepts-wrong {c(R, 'b_looser_accepts_wrong')}; (b) hides-wrong "
        f"{c(R, 'b_looser_hides_wrong')}; (c) {c(R, 'c_not_scorable_excluded')}. By field: {fields}.",
        f"- Against the facts .10's own emission extracts (`harness_wired`): {json.dumps(W, sort_keys=True)}.",
        f"- By rule: {famline}.",
        f"- (c) NOT_SCORABLE: {ns['excluded_by_both']} of {ns['cases']} cases on {ns['rows']} rows excluded by .10; {ns['read_as_absent']} read "
        f"as absent; {ns['scored']} scored.",
        "- **Main divergences.** (a) critical: identity dash glyphs not folded (R1), revision 'Rev. 01' / 'REV 01' read by first "
        "token (R2), F043 truth 'Rev. 0' normalised to 'REV.' (R2b), (g)(1) tail form (R3), the application's `rejected` on (d1) rows "
        "(R4). (b): any 'Rev. <n>' accepted on F043 p2-p4 (R2b), another page's identity on a compilation page associated cross-page "
        "and never flagged (R5), cross-page copies credited to the other page (R6). Decision text other than approved / ANN / "
        "rejected (R7) is never emitted by the application.",
        f"- **Normaliser question:** a blind normaliser (N1) leaves (g)(1), (d1), compilation and cross-page divergences; a truth-aware "
        f"one (N2, with compilation split) leaves only two harness departures from the conventions; neither made .10 accept a "
        f"wrong-value control the harness rejects (N1 {n1['wrong_value_controls_accepted_where_harness_rejects']}, N2 "
        f"{n2['wrong_value_controls_accepted_where_harness_rejects']}; without a normaliser "
        f"{S['wrong_value_controls_accepted_as_correct_by_evaluator']['where_harness_rejects']}). Analysis only; not recommended over "
        "binding the frozen judge.",
        "",
        "**Recommendation for ORCH-07:** bind evaluator .10 **as is in its emission role only** (`record_groups`, `observation_groups`, "
        "`ai_groups` through `tripwire_r32.facts_from_row`, as the frozen review34 `score_lane_r32` already does), with every verdict, "
        "metric, tripwire and gate from `lane_judge_r32` + `literal_compare_r32`; do **not** bind .10's own judging. No candidate "
        "correction is needed for that binding. If ORCH-07 wants .10's judging to produce any verdict, a candidate correction (new "
        "commit, own independent review) is required before any live run, changing R1 (dash folding in `norm_ref` / `same_identity`), "
        "R2 / R2b (`norm_rev` whole-value parse), R3 ((g)(1) alternates), R4 ((d1) alternative decision), R5 (no cross-page "
        "association in compilations) and R6 (no cross-page recovery credit, or declare it); R7 optional. List the interpretations of "
        "Review 35 item 10 and disclose the harness departures H1-H5 (`EVALUATOR-TEST-REPORT.md` sections 7 and 10).",
        "",
        "**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; the provider classes were stubbed to "
        "raise and none was constructed; no real prediction exists or was created; the AI ledger was opened read-only only and "
        "reads 483 entries / 17 scopes before and after; no ledger scope; no OneDrive; no sealed project; no authorization file created (the 35 files named `OWNER-DISPATCH-AUTHORIZATION.json` found in the session scratchpad are pytest temporaries of earlier harness tasks, all older than this task). "
        "The candidate `C:/t/iso/cand-r29` was never written (`git status --porcelain` empty before and after).",
        "",
        f"**Reference set:** {C.REFERENCE_SET_STATEMENT} (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.",
        "",
        "**Status, stated separately:**",
        "1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.",
        "2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.",
        "3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents) and not human-signed.",
        "4. **Field populations:** identity 57, revision 38, decision 38.",
        "5. **Conditions:** C-6 answered by this package, **pending ORCH-06V**; C-7 is ORCH-07; C-8 is carried into the declaration.",
        "6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.",
        "7. **M2:** **CHANGES STILL REQUIRED.**",
        "8. **M3:** not started.",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = C.RESPONSE_LEDGER
    got = C.sha256_file(p)
    if got != BEFORE:
        raise SystemExit(f"PACKET MISMATCH: response ledger {got} != {BEFORE}")
    raw = p.read_bytes()
    assert raw.endswith(b"\n") and HEADING.encode("utf-8") not in raw
    text = entry()
    with open(p, "ab") as fh:
        fh.write(text.encode("utf-8"))
    after = C.sha256_file(p)
    print(json.dumps({"before": BEFORE, "after": after, "bytes_before": len(raw), "bytes_appended": len(text.encode("utf-8")),
                      "prefix_unchanged": C.sha256_text(p.read_bytes()[:len(raw)].decode("utf-8")) == BEFORE}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
