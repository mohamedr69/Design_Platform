"""ORCH-06 (Review 33 C-6), agent R35EVAL-IMPL: build PARITY-MATRIX.json, EVALUATOR-TEST-REPORT.md and
evidence/RUN-SUMMARY.json + evidence/NORMALISER-EXPERIMENT.json from the work-folder run outputs.

Usage: make_report_r35.py <run full json> <run document-scope json> <normaliser N1 json> <normaliser N2 json>
Reads those four work-folder files, the packaged SYNTHETIC-PREDICTIONS.json and (for the run-set flag only) the frozen
review34/RUN-SET-PROPOSAL.json (9058f3d6...). Writes only inside the package. No model request."""
from __future__ import annotations

import collections
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402

RUN_SET = (C.REVIEW34 / "RUN-SET-PROPOSAL.json", "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8")
CLASSES = ("parity", "a_stricter_critical", "a_stricter_recovery", "b_looser_accepts_wrong", "b_looser_hides_wrong", "b_looser_credit",
           "c_not_scorable_excluded", "c_violation_read_as_absent", "c_violation_scored")
FAMILIES = {
    "R1": "identity: a dash glyph other than the truth's (hyphen / en dash / minus / figure dash / em dash / non-breaking hyphen) is "
          "not folded; norm_ref folds only whitespace and case, and same_identity's 'near' (alphanumerics equal) is not accepted",
    "R2": "revision: norm_rev reads only the FIRST whitespace token, so 'Rev. 01', 'REV 01' and 'Revision 1' parse as 'REV.' / 'REV' / "
          "'REVISION', never as the number",
    "R2b": "revision truth 'Rev. 0' (F043 p2-p4): the encoded truth itself normalises to 'REV.', so the correct '0' / '00' / 'R0' / "
           "'Rev.0' are wrong and ANY 'Rev. <n>' is accepted",
    "R3": "identity (g)(1) either form: the printed number with its labelled 'Rev.' tail is not accepted (evaluator .10 has no "
          "alternates; the tail is not an '-Rn' suffix for split_suffix)",
    "R3b": "identity tail form on a page that prints no tail: the harness forgives it as a cross-page copy of another page's (g)(1) "
           "alternate; .10 judges it wrong",
    "R4": "decision (d1) resubmission tolerance: the application's 'rejected' on a 'approved as noted' + resubmission_required row is "
          "a wrong decision in .10 (word equality 'rejected' != 'ANN')",
    "R5": "compilation (h): an identity of ANOTHER page of the same compilation file is associated cross-page and credited to that "
          "page (associate_group has no page keying); the harness scores it wrong",
    "R6": "cross-page identity credit: a copy of another page's identity is credited as that other page's recovery (correct) in .10; "
          "the harness counts it neither correct nor wrong",
    "R7": "decision vocabulary: .10 compares decision WORDS (approved / ANN / rejected); any other text is dropped by record_groups "
          "(register: status not in POSITIVE) or judged wrong on the AI path, including a negative word such as 'UR' (a false "
          "positive on an ABSENT row). The application never emits such text (only approved / ANN / rejected)",
    "H1": "revision with whitespace inside the number ('0 0', '0 1'): .10 reads the first token, the harness keeps '00' / '01' "
          "unparsed; both depart from (i2) differently",
    "other": "other",
}


def family(c: dict) -> str:
    f, v, g, tk = c["field"], c["variant"], c["group"], c["truth_key"]
    if g == "compilation_page_keyed" and f == "identity":
        return "R5"
    if g == "cross_page_identity":
        return "R6"
    if f == "decision":
        if v == "d1:rejected":
            return "R4"
        return "R7"
    if f == "identity":
        if v.startswith("dash_as_"):
            return "R1"
        if v.startswith("g1_labelled_tail"):
            return "R3"
        if v == "labelled_tail_not_printed_on_this_page":
            return "R3b"
        if v in ("digit_changed", "segment_dropped"):
            return "R6"
    if f == "revision":
        if tk in ("F043|2|revision", "F043|3|revision", "F043|4|revision"):
            return "R2b"
        if v == "ws_inside_number":
            return "H1"
        if v in ("prefix_Rev_dot_space", "prefix_REV_space", "prefix_Revision_word"):
            return "R2"
    return "other"


def load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def counts(cases, key="class_vs_pair"):
    c = collections.Counter(x[key] for x in cases)
    return {k: c[k] for k in CLASSES if c.get(k)} | {k: v for k, v in c.items() if k not in CLASSES}


def build(run_full, run_doc, n1, n2):
    full, doc, N1, N2 = load(run_full), load(run_doc), load(n1), load(n2)
    fixtures_path = C.PACKAGE / "SYNTHETIC-PREDICTIONS.json"
    fx = load(fixtures_path)
    assert C.sha256_file(fixtures_path) == full["fixtures"]["sha256"] == doc["fixtures"]["sha256"]
    assert full["register_scope"] == "full" and doc["register_scope"] == "document" and full["fixtures"]["limit"] is None
    assert C.sha256_file(RUN_SET[0]) == RUN_SET[1], "PACKET MISMATCH: RUN-SET-PROPOSAL.json"
    run_set = {d["pool_id"] for d in load(RUN_SET[0])["documents"]}
    fx_by_id = {f["id"]: f for f in fx["fixtures"]}
    # equivalence of register scope 'full' (as score_lane.py) and 'document', on the untouched run outputs
    dmap = {c["case_id"]: c for c in doc["cases"]}
    diffs = [c["case_id"] for c in full["cases"] if c != dmap.get(c["case_id"])]
    cases = []
    for c in full["cases"]:
        f = fx_by_id[c["fixture_id"]]
        c = dict(c)
        c["side_rows"] = [dict(s) for s in c["side_rows"]]
        c["in_run_set"] = c["pool_id"] in run_set
        c["harness_literal_compare"] = f["expected_harness"]["literal_compare"]
        c["truth_literal"], c["truth_class"] = f["truth_literal"], f["truth_class"]
        c["family"] = family(c) if c["class_vs_pair"] not in ("parity", "c_not_scorable_excluded") else None
        for s in c["side_rows"]:
            s["family"] = "R5" if c["group"] == "compilation_page_keyed" else "R6" if s["class"] == "b_looser_credit" else "other"
        cases.append(c)
    reach = [c for c in cases if c["application_reachable"]]
    div = [c for c in cases if c["class_vs_pair"] not in ("parity", "c_not_scorable_excluded")]
    fam = collections.defaultdict(lambda: {"cases": 0, "reachable_cases": 0, "by_class": collections.Counter(), "rows": set(),
                                           "run_set_rows": set(), "variants": collections.Counter(), "examples": [], "code_locations": set(),
                                           "channels": collections.Counter()})
    for c in div:
        F = fam[c["family"]]
        F["cases"] += 1
        F["reachable_cases"] += c["application_reachable"]
        F["by_class"][c["class_vs_pair"]] += 1
        F["rows"].add(c["truth_key"])
        if c["in_run_set"]:
            F["run_set_rows"].add(c["truth_key"])
        F["variants"][c["variant"]] += 1
        F["channels"][c["channel"]] += 1
        F["code_locations"].update(c["evaluator"]["code_locations"])
        want = (c["channel"] == "register" and c["family"] != "R7") or (c["family"] == "R7" and c["channel"] == "ai_validated")
        if len(F["examples"]) < 4 and want:
            F["examples"].append({"case": c["case_id"], "row": c["truth_key"], "truth": "ABSENT" if c["truth_kind"] == "absent" else
                                  c["truth_literal"] if c["field"] != "decision" else
                                  f"{c['truth_literal']} (class {c['truth_class']})", "value": c["value"], "evaluator": c["evaluator"]["verdict"],
                                  "harness": c["harness_pair"]["verdict"], "rule": c["evaluator"]["rule"], "detail": c["evaluator"]["detail"]})
    side = [dict(s, case=c["case_id"], channel=c["channel"], group=c["group"], in_run_set=c["in_run_set"]) for c in cases for s in c["side_rows"]]
    for s in side:
        F = fam[s["family"]]
        F.setdefault("side_rows", collections.Counter())
        F["side_rows"][s["class"]] += 1
        F.setdefault("side_rows_distinct", set()).add(s["row"])
        if s["in_run_set"]:
            F["run_set_rows"].add(s["row"])
        if len(F["examples"]) < 4 and s["channel"] == "register":
            F["examples"].append({"case": s["case"], "row": s["row"], "side_effect": True, "evaluator": s["evaluator"], "harness": s["harness_pair"]})
    families = {}
    for k in sorted(fam):
        F = fam[k]
        families[k] = {"rule": FAMILIES[k], "cases": F["cases"], "reachable_cases": F["reachable_cases"], "by_class": dict(F["by_class"]),
                       "distinct_rows": len(F["rows"]), "rows": sorted(F["rows"]), "run_set_rows": sorted(F["run_set_rows"]),
                       "variants": dict(F["variants"]), "channels": dict(F["channels"]),
                       "side_rows": dict(F.get("side_rows", {})), "side_rows_distinct": sorted(F.get("side_rows_distinct", set())),
                       "code_locations": sorted(F["code_locations"]), "examples": F["examples"]}
    intent_bad = collections.Counter()
    intent_examples = collections.defaultdict(list)
    expect = {"correct": ("correct",), "wrong": ("critical_false_acceptance",), "page_keyed_wrong": ("critical_false_acceptance",),
              "no_assertion": ("missed", "absent_accepted"), "not_scorable": ("excluded",), "cross_page_copy": ("missed", "absent_accepted")}
    for c in cases:
        if c["channel"] != "register":
            continue
        hv = c["harness_pair"]["verdict"]
        if hv not in expect[c["intent"]]:
            k = (c["intent"], c["variant"] if c["group"] not in ("compilation_page_keyed", "cross_page_identity") else c["group"], hv)
            intent_bad[k] += 1
            if len(intent_examples[k]) < 3:
                intent_examples[k].append({"row": c["truth_key"], "value": c["value"], "harness": hv, "kind": c["harness_literal_compare"].get("kind")})
    harness_vs_intent = [{"intent": k[0], "variant_or_group": k[1], "harness_verdict": k[2], "fixtures": n, "examples": intent_examples[k]}
                         for k, n in sorted(intent_bad.items())]

    def by(cs, attr):
        out = collections.defaultdict(collections.Counter)
        for c in cs:
            out[c[attr]][c["class_vs_pair"]] += 1
        return {k: dict(v) for k, v in sorted(out.items())}

    def norm_summary(N):
        cs = N["cases"]
        res = [c for c in cs if c["class_vs_pair"] not in ("parity", "c_not_scorable_excluded")]
        rr = collections.Counter((c["class_vs_pair"], c["field"], c["variant"] if c["group"] not in ("compilation_page_keyed",) else c["group"])
                                 for c in res if c["application_reachable"])
        wa = [c for c in cs if c["intent"] in ("wrong", "page_keyed_wrong") and c["evaluator_row_verdict"] == "correct"]
        hr = [c["case_id"] for c in wa if c["harness_pair"] != "correct"]
        ha = [c["case_id"] for c in wa if c["harness_pair"] == "correct"]
        return {"counts": N["counts"], "residual_reachable": [{"class": k[0], "field": k[1], "variant_or_group": k[2], "cases": n}
                                                              for k, n in sorted(rr.items())],
                "wrong_value_controls_accepted_where_harness_rejects": len(hr), "cases_harness_rejects": hr[:20],
                "wrong_value_controls_accepted_where_harness_also_accepts": len(ha), "cases_harness_also_accepts": ha[:30],
                "variants_harness_also_accepts": dict(collections.Counter(c["variant"] for c in wa if c["harness_pair"] == "correct")),
                "not_scorable_scored": sum(1 for c in cs if c["truth_kind"] == "not_scorable" and c["evaluator_row_verdict"] != "excluded"),
                "guard": N["guard"]["violations"] + N["guard"]["refused_writes"], "sha256_of_work_file": None}

    n0_wa = [c for c in cases if c["intent"] in ("wrong", "page_keyed_wrong") and c["evaluator"]["row_verdict"] == "correct"]
    summary = {
        "cases": len(cases), "fixtures": len(fx["fixtures"]), "channels": ["register", "ai_validated"], "coverage": fx["coverage"],
        "class_vs_pair": {"all": counts(cases), "application_reachable": counts(reach),
                          "application_reachable_in_run_set": counts([c for c in reach if c["in_run_set"]]),
                          "by_field": by(cases, "field"), "by_field_application_reachable": by(reach, "field"),
                          "by_channel": by(cases, "channel"), "by_group": by(cases, "group")},
        "class_vs_wired": {"all": counts(cases, "class_vs_wired"), "application_reachable": counts(reach, "class_vs_wired")},
        "side_rows": {"all": dict(collections.Counter(s["class"] for s in side)),
                      "application_reachable": dict(collections.Counter(s["class"] for s, c in
                                                                         ((s, c) for c in cases for s in c["side_rows"]) if c["application_reachable"])),
                      "distinct_rows_credited": len({s["row"] for s in side if s["class"] == "b_looser_credit"})},
        "evaluator_verdicts": dict(collections.Counter(c["evaluator"]["verdict"] for c in cases)),
        "harness_pair_verdicts": dict(collections.Counter(c["harness_pair"]["verdict"] for c in cases)),
        "not_scorable": {"cases": sum(1 for c in cases if c["truth_kind"] == "not_scorable"),
                         "excluded_by_both": sum(1 for c in cases if c["class_vs_pair"] == "c_not_scorable_excluded"),
                         "read_as_absent": sum(1 for c in cases if c["class_vs_pair"] == "c_violation_read_as_absent"),
                         "scored": sum(1 for c in cases if c["class_vs_pair"] == "c_violation_scored"),
                         "rows": len({c["truth_key"] for c in cases if c["truth_kind"] == "not_scorable"})},
        "wrong_value_controls_accepted_as_correct_by_evaluator": {
            "where_harness_rejects": len([c for c in n0_wa if c["harness_pair"]["verdict"] != "correct"]),
            "where_harness_also_accepts": len([c for c in n0_wa if c["harness_pair"]["verdict"] == "correct"]),
            "case_ids": [c["case_id"] for c in n0_wa]},
        "scope_equivalence": {"identical": not diffs, "compared": len(full["cases"]), "differences": diffs[:20],
                              "note": "register scope 'full' (the whole frozen register, as score_lane.py) against 'document' (the fixture's document only)"},
        "families": families, "harness_vs_intent": harness_vs_intent,
        "normalisers": {"N1": norm_summary(N1), "N2": norm_summary(N2)},
    }
    matrix = {"kind": "SYNTHETIC", "schema": "r35-parity-matrix-1", "statement": C.SYNTHETIC_STATEMENT,
              "reference_set_statement": C.REFERENCE_SET_STATEMENT,
              "legend": {"verdicts": list(C.VERDICTS), "classes": {
                  "parity": "evaluator row verdict == harness row verdict",
                  "a_stricter_critical": "(a) evaluator stricter: a value the harness accepts (or a non-assertion) becomes a CRITICAL false acceptance in .10 -- it would fire the per-field tripwire on resolved truth",
                  "a_stricter_recovery": "(a) evaluator stricter: a value the harness accepts is missed by .10 (lowers recovery)",
                  "b_looser_accepts_wrong": "(b) evaluator looser: a value the harness rejects as a critical is accepted as correct by .10",
                  "b_looser_hides_wrong": "(b) evaluator looser: a value the harness rejects as a critical is not flagged by .10 (missed / not evaluated)",
                  "b_looser_credit": "(b) side effect: .10 credits another row as recovered where the harness does not",
                  "c_not_scorable_excluded": "(c) NOT_SCORABLE row excluded by both (never read as absent)",
                  "c_violation_read_as_absent": "(c) violation: NOT_SCORABLE row read as absent by .10",
                  "c_violation_scored": "(c) violation: NOT_SCORABLE row scored by .10"},
                  "class_vs_pair": "evaluator against the harness verdict on the offered value itself (literal_compare_r32 via lane_judge_r32)",
                  "class_vs_wired": "evaluator against the harness verdict on the facts .10's emission functions extract from the same row (what score_lane_r32 judges)",
                  "application_reachable": "false only for decision text other than approved / ANN / rejected (never emitted by the application)"},
              "inputs": {"fixtures": {"path": str(fixtures_path).replace("\\", "/"), "sha256": full["fixtures"]["sha256"]},
                         "truth_r32": full["inputs"]["truth_r32"], "labels_eval_input": full["inputs"]["labels_eval_input"],
                         "run_set_proposal": {"path": str(RUN_SET[0]).replace("\\", "/"), "sha256": RUN_SET[1]}},
              "evaluator": full["evaluator"], "code_locations": full["code_locations"], "summary": summary, "cases": cases}
    run_summary = {"kind": "ORCH-06 run summary", "statement": C.SYNTHETIC_STATEMENT,
                   "runs": {"full_scope": {"path": run_full, "sha256": C.sha256_file(run_full), "seconds": full["seconds"], "cases": len(full["cases"])},
                            "document_scope": {"path": run_doc, "sha256": C.sha256_file(run_doc), "seconds": doc["seconds"], "cases": len(doc["cases"])},
                            "normaliser_N1": {"path": n1, "sha256": C.sha256_file(n1), "seconds": N1["seconds"]},
                            "normaliser_N2": {"path": n2, "sha256": C.sha256_file(n2), "seconds": N2["seconds"]}},
                   "guard_full_scope": full["guard"], "guard_document_scope": {k: doc["guard"][k] for k in (
                       "blocked_calls", "violations", "refused_writes", "provider_constructed", "network_or_process_attempts",
                       "sdk_modules_imported", "database_file_created")},
                   "expected_harness_reproduced": {"full": full["expected_harness_reproduced"], "document": doc["expected_harness_reproduced"]},
                   "evaluator": full["evaluator"], "harness_modules": full["harness_modules"]}
    norm = {"kind": "ORCH-06 normaliser experiment (analysis only; not bound code)", "statement": C.SYNTHETIC_STATEMENT,
            "N1": summary["normalisers"]["N1"] | {"work_file": n1, "sha256": C.sha256_file(n1)},
            "N2": summary["normalisers"]["N2"] | {"work_file": n2, "sha256": C.sha256_file(n2)},
            "N0_reference": {"class_vs_pair": summary["class_vs_pair"]["all"], "application_reachable": summary["class_vs_pair"]["application_reachable"]}}
    return matrix, run_summary, norm


def main(argv):
    run_full, run_doc, n1, n2 = argv[1:5]
    matrix, run_summary, norm = build(run_full, run_doc, n1, n2)
    out = {"PARITY-MATRIX.json": C.write_json(matrix, C.PACKAGE / "PARITY-MATRIX.json"),
           "evidence/RUN-SUMMARY.json": C.write_json(run_summary, C.PACKAGE / "evidence/RUN-SUMMARY.json"),
           "evidence/NORMALISER-EXPERIMENT.json": C.write_json(norm, C.PACKAGE / "evidence/NORMALISER-EXPERIMENT.json")}
    import report_text_r35 as RT
    text = RT.render(matrix, run_summary, norm)
    p = C.PACKAGE / "EVALUATOR-TEST-REPORT.md"
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    out["EVALUATOR-TEST-REPORT.md"] = C.sha256_file(p)
    print(json.dumps(out, indent=1))
    print(json.dumps({k: matrix["summary"][k] for k in ("cases", "class_vs_pair", "class_vs_wired", "side_rows", "not_scorable",
                                                         "wrong_value_controls_accepted_as_correct_by_evaluator", "scope_equivalence")},
                     indent=1, default=str)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
