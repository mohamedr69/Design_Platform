"""ORCH-06C (R36HARNESS-IMPL): the H1 what-if RESULT -- exactly which verdicts the norm_revision fix changes.

Usage: h1_whatif_r36.py <out H1-WHATIF-RESULT.json (absolute)>
Inputs (all hash-recorded; the frozen ones hash-checked):
  whatif/ROWS-OLD.json, whatif/ROWS-NEW.json   judge_all_rows_r36.py: every row of each fixture's document, review34 vs r36 harness,
                                                states accepted and validated (Verification 36's what-if population)
  parity/run/RUN-R36-FULL.json                  the ORCH-06 parity run re-executed from a copy (parity/scripts) with the r36 harness:
                                                9,610 cases, harness_pair / harness_wired / side rows with the fixed harness, the
                                                evaluator side re-run read-only
  PILOT/evaluator-offline-r32/PARITY-MATRIX.json (73e189f2...), SYNTHETIC-PREDICTIONS.json (9f3e0e56...)
  MR/reviews/M2-review-36/INDEPENDENT-PACKAGE-CHECK.json (Verification 36's what-if numbers)
Pure comparison; writes only <out>."""
import collections
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r36")
FROZEN = {"fixtures": (PILOT / "evaluator-offline-r32" / "SYNTHETIC-PREDICTIONS.json", "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774"),
          "matrix": (PILOT / "evaluator-offline-r32" / "PARITY-MATRIX.json", "73e189f2d0cfe05e55ba58837e991c008eaaf11fb928c300cf0670ead60aaccc"),
          "verification36": (MR / "reviews" / "M2-review-36" / "INDEPENDENT-VERIFICATION.md", "f698c2ffebc44df0487edce762a3f1bd561b2cbbda7b3d844dbd7d6c15173a00")}
V36_CHECK = MR / "reviews" / "M2-review-36" / "INDEPENDENT-PACKAGE-CHECK.json"
WORK_INPUTS = {"rows_old": WORK / "whatif" / "ROWS-OLD.json", "rows_new": WORK / "whatif" / "ROWS-NEW.json",
               "parity_run_r36": WORK / "parity" / "run" / "RUN-R36-FULL.json"}
WRONG = ("wrong", "page_keyed_wrong")
ACCEPTED_VERDICTS = ("correct", "correct_and_wrong")
REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"
SYNTHETIC_STATEMENT = ("SYNTHETIC: every value judged here is a frozen ORCH-06 fixture built from the r32 truth strings by a fixed rule; "
                       "none is a prediction of any model or of the application; no provider or model request was made.")


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def load(path, want=None):
    raw = pathlib.Path(path).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if want and h != want:
        raise SystemExit(f"PACKET MISMATCH: {path}")
    return json.loads(raw.decode("utf-8")), h


def row_level(old, new, fx_by_id):
    out = {}
    for state in ("accepted", "validated"):
        keys = [k for k in old if k.split("|")[1] == state]
        changed = [k for k in keys if old[k] != new[k]]
        by = collections.Counter()
        listing = []
        newly_accepted_wrong, ns_changed, ns_not_excluded = 0, [], 0
        for k in changed:
            fid, _, pg, fld = k.split("|")
            f = fx_by_id[fid]
            target = (pg, fld) == (f["page"], f["field"])
            b, a = old[k], new[k]
            by[(f["variant"], f["intent"], f"{b[0]}/{b[1]}->{a[0]}/{a[1]}", "target" if target else "side")] += 1
            listing.append({"fixture": fid, "row": f"{f['pool_id']}|{pg}|{fld}", "target_row": target, "variant": f["variant"], "intent": f["intent"],
                            "value": f["prediction"]["value"], "before": b[:5], "after": a[:5]})
            if f["intent"] in WRONG and (a[0] in ("recovered_clean", "recovered_mixed", "tn") or a[1] < b[1]):
                newly_accepted_wrong += 1
            if b[5] == "not_scorable":
                ns_changed.append(k)
        for k in keys:
            if new[k][5] == "not_scorable" and new[k][0] != "not_scorable":
                ns_not_excluded += 1
        wrong_keys = [k for k in keys if fx_by_id[k.split("|")[0]]["intent"] in WRONG and
                      tuple(k.split("|")[2:]) == (fx_by_id[k.split("|")[0]]["page"], fx_by_id[k.split("|")[0]]["field"])]
        out[state] = {"rows_judged": len(keys), "changed": len(changed),
                      "changes_by_variant_intent_outcome": [{"variant": k[0], "intent": k[1], "change": k[2], "row": k[3], "n": n} for k, n in sorted(by.items())],
                      "changed_rows": sorted(listing, key=lambda x: x["fixture"]),
                      "wrong_value_controls": {"target_rows": len(wrong_keys),
                                               "accepted_before": sum(1 for k in wrong_keys if old[k][0] in ("recovered_clean", "recovered_mixed")),
                                               "accepted_after": sum(1 for k in wrong_keys if new[k][0] in ("recovered_clean", "recovered_mixed")),
                                               "newly_accepted_or_less_critical": newly_accepted_wrong},
                      "not_scorable": {"rows": sum(1 for k in keys if old[k][5] == "not_scorable"), "changed": len(ns_changed),
                                       "outcome_other_than_not_scorable_after": ns_not_excluded}}
    return out


def strip(d):
    return {k: v for k, v in (d or {}).items()}


def case_level(matrix_cases, run_cases):
    mc = {c["case_id"]: c for c in matrix_cases}
    rc = {c["case_id"]: c for c in run_cases}
    assert mc.keys() == rc.keys(), "case sets differ"
    changed, ev_diff, side_diff, wired_diff = [], [], [], []
    cls_pair, cls_wired = collections.Counter(), collections.Counter()
    for cid in sorted(mc):
        m, r = mc[cid], rc[cid]
        for k in ("fixture_id", "channel", "truth_key", "value", "variant", "intent", "truth_kind", "application_reachable"):
            assert m[k] == r[k], (cid, k)
        ev_keys = set(m["evaluator"]) & set(r["evaluator"])
        if any(m["evaluator"][k] != r["evaluator"][k] for k in ev_keys):
            ev_diff.append(cid)
        hp_changed = m["harness_pair"] != r["harness_pair"]
        hw_changed = m["harness_wired"] != r["harness_wired"]
        # the matrix's side rows carry one more key ("family", added by the ORCH-06 report step); compare the run's own keys
        m_side = [{k: s[k] for k in s if k != "family"} for s in m["side_rows"]]
        if m_side != r["side_rows"]:
            side_diff.append(cid)
        if hw_changed:
            wired_diff.append(cid)
        cls_pair[(m["class_vs_pair"], r["class_vs_pair"])] += 1
        cls_wired[(m["class_vs_wired"], r["class_vs_wired"])] += 1
        if hp_changed or hw_changed:
            changed.append({"case_id": cid, "truth_key": m["truth_key"], "channel": m["channel"], "value": m["value"], "variant": m["variant"],
                            "intent": m["intent"], "in_run_set": m.get("in_run_set"), "application_reachable": m["application_reachable"],
                            "harness_pair": [m["harness_pair"]["verdict"], r["harness_pair"]["verdict"]],
                            "harness_wired": [m["harness_wired"]["verdict"], r["harness_wired"]["verdict"]],
                            "evaluator_verdict": r["evaluator"]["verdict"],
                            "class_vs_pair": [m["class_vs_pair"], r["class_vs_pair"]], "class_vs_wired": [m["class_vs_wired"], r["class_vs_wired"]]})
    wrong = [c for c in matrix_cases if c["intent"] in WRONG]
    ns = [c for c in matrix_cases if c["truth_kind"] == "not_scorable"]

    def acc(cases, src, key):
        return sum(1 for c in cases if src[c["case_id"]][key]["verdict"] in ACCEPTED_VERDICTS)

    def tally(cnt):
        return [{"before": k[0], "after": k[1], "n": n} for k, n in sorted(cnt.items()) if k[0] != k[1]]

    after_pair = collections.Counter(r["class_vs_pair"] for r in run_cases)
    return {"cases": len(mc), "changed_cases": len(changed), "changed": changed,
            "changed_by": dict(collections.Counter(f"{c['variant']}|{c['intent']}|{c['channel']}|pair {c['harness_pair'][0]}->{c['harness_pair'][1]}|"
                                                   f"wired {c['harness_wired'][0]}->{c['harness_wired'][1]}" for c in changed)),
            "changed_rows": sorted({c["truth_key"] for c in changed}), "changed_rows_in_run_set": sorted({c["truth_key"] for c in changed if c["in_run_set"]}),
            "evaluator_side_identical": not ev_diff, "evaluator_side_differences": ev_diff[:50],
            "side_rows_changed_cases": side_diff[:50], "side_rows_changed_count": len(side_diff),
            "harness_wired_changed_count": len(wired_diff),
            "class_vs_pair_changes": tally(cls_pair), "class_vs_wired_changes": tally(cls_wired),
            "class_vs_pair_totals_after": dict(sorted(after_pair.items())),
            "wrong_value_controls": {"fixtures": len({c["fixture_id"] for c in wrong}), "cases": len(wrong),
                                     "harness_pair_accepted_before": acc(wrong, mc, "harness_pair"), "harness_pair_accepted_after": acc(wrong, rc, "harness_pair"),
                                     "harness_wired_accepted_before": acc(wrong, mc, "harness_wired"), "harness_wired_accepted_after": acc(wrong, rc, "harness_wired"),
                                     "verdict_changed": sum(1 for c in wrong if mc[c["case_id"]]["harness_pair"] != rc[c["case_id"]]["harness_pair"]
                                                            or mc[c["case_id"]]["harness_wired"] != rc[c["case_id"]]["harness_wired"]),
                                     "note": "before and after, the frozen harness accepts 13 decision controls ('Code D - Rejected', the H2 "
                                             "vocabulary): 26 pair cases (13 x 2 channels) and 13 wired cases (the register channel emits no "
                                             "decision fact for 'Code D - Rejected', so only the AI channel's fact is judged); the norm_revision "
                                             "fix touches no decision comparison"},
            "not_scorable": {"cases": len(ns), "rows": len({c["truth_key"] for c in ns}),
                             "harness_pair_excluded_before": sum(1 for c in ns if mc[c["case_id"]]["harness_pair"]["verdict"] == "excluded"),
                             "harness_pair_excluded_after": sum(1 for c in ns if rc[c["case_id"]]["harness_pair"]["verdict"] == "excluded"),
                             "harness_wired_excluded_after": sum(1 for c in ns if rc[c["case_id"]]["harness_wired"]["verdict"] == "excluded"),
                             "harness_read_as_absent_after": sum(1 for c in ns if "absent_accepted" in (rc[c["case_id"]]["harness_pair"]["verdict"],
                                                                                                         rc[c["case_id"]]["harness_wired"]["verdict"])),
                             "class_c_violation_read_as_absent_after": sum(1 for c in ns if rc[c["case_id"]]["class_vs_pair"] == "c_violation_read_as_absent"),
                             "class_c_not_scorable_excluded_after": sum(1 for c in ns if rc[c["case_id"]]["class_vs_pair"] == "c_not_scorable_excluded"),
                             "unresolved_kinds_changed": sum(1 for c in ns if mc[c["case_id"]]["harness_pair"]["unresolved_kinds"] != rc[c["case_id"]]["harness_pair"]["unresolved_kinds"])}}


def main(out):
    out = pathlib.Path(out)
    assert out.is_absolute()
    fx, fx_sha = load(*FROZEN["fixtures"])
    matrix, m_sha = load(*FROZEN["matrix"])
    if sha(FROZEN["verification36"][0]) != FROZEN["verification36"][1]:
        raise SystemExit("PACKET MISMATCH: Verification 36")
    v36, v36_sha = load(V36_CHECK)
    old, old_sha = load(WORK_INPUTS["rows_old"])
    new, new_sha = load(WORK_INPUTS["rows_new"])
    run, run_sha = load(WORK_INPUTS["parity_run_r36"])
    assert old["harness_hashes"]["literal_compare_r32"].startswith("ec2221c8") and new["harness_hashes"]["literal_compare_r32"].startswith("c23ba577")
    fx_by_id = {f["id"]: f for f in fx["fixtures"]}
    rl = row_level(old["rows"], new["rows"], fx_by_id)
    cl = case_level(matrix["cases"], run["cases"])
    ws = [f for f in fx["fixtures"] if f["variant"] == "ws_inside_number"]
    v = v36["8_h1"]["what_if_whitespace_removed_before_parse"]
    h1 = v36["5_classification"]["H1_ws_inside_number"]
    mine_by = rl["accepted"]["changes_by_variant_intent_outcome"]
    ev_on_changed = collections.Counter(c["evaluator_verdict"] for c in cl["changed"])
    comparison = {
        "rows_judged": {"verification36": v["rows_judged"], "r36": rl["accepted"]["rows_judged"], "equal": v["rows_judged"] == rl["accepted"]["rows_judged"]},
        "changed": {"verification36": v["changed"], "r36": rl["accepted"]["changed"], "equal": v["changed"] == rl["accepted"]["changed"]},
        "changes_by_variant_intent_outcome": {"verification36": v["changes_by_variant_intent_outcome"], "r36": mine_by,
                                              "equal": v["changes_by_variant_intent_outcome"] == mine_by},
        "wrong_controls_newly_accepted": {"verification36": v["wrong_controls_newly_accepted"], "r36": rl["accepted"]["wrong_value_controls"]["newly_accepted_or_less_critical"],
                                          "equal": v["wrong_controls_newly_accepted"] == rl["accepted"]["wrong_value_controls"]["newly_accepted_or_less_critical"]},
        "H1_cases": {"verification36": h1["cases"], "r36": cl["changed_cases"], "equal": h1["cases"] == cl["changed_cases"]},
        "H1_rows": {"verification36": h1["rows"], "r36": len(cl["changed_rows"]), "equal": h1["rows"] == len(cl["changed_rows"])},
        "H1_evaluator_verdicts_on_the_changed_cases": {"verification36": h1["evaluator_verdicts"], "r36": dict(sorted(ev_on_changed.items())),
                                                       "equal": h1["evaluator_verdicts"] == dict(sorted(ev_on_changed.items()))},
        "H1_rows_in_run_set": {"verification36": h1["in_run_set_rows"], "r36": cl["changed_rows_in_run_set"],
                               "equal": sorted(h1["in_run_set_rows"]) == cl["changed_rows_in_run_set"]},
    }
    ws_rows = sorted(f["truth_key"] for f in ws)
    checks = {
        "row_level_changes_are_exactly_the_53_ws_inside_number_target_rows_per_state": all(
            rl[s]["changed"] == 53 and sorted(x["row"] for x in rl[s]["changed_rows"]) == ws_rows and all(x["target_row"] for x in rl[s]["changed_rows"])
            for s in ("accepted", "validated")),
        "case_level_changes_are_exactly_the_106_ws_inside_number_cases": cl["changed_cases"] == 106 and cl["changed_rows"] == ws_rows
        and all(c["variant"] == "ws_inside_number" for c in cl["changed"]),
        "every_changed_case_goes_critical_to_correct_on_pair_and_wired": all(c["harness_pair"] == c["harness_wired"] == ["critical_false_acceptance", "correct"]
                                                                            for c in cl["changed"]),
        "no_side_row_changed": cl["side_rows_changed_count"] == 0,
        "evaluator_side_identical": cl["evaluator_side_identical"],
        "wrong_value_controls_newly_accepted_row_level": rl["accepted"]["wrong_value_controls"]["newly_accepted_or_less_critical"]
        + rl["validated"]["wrong_value_controls"]["newly_accepted_or_less_critical"] == 0,
        "wrong_value_controls_verdicts_unchanged_case_level": cl["wrong_value_controls"]["verdict_changed"] == 0,
        "wrong_value_controls_accepted_unchanged": cl["wrong_value_controls"]["harness_pair_accepted_before"] == cl["wrong_value_controls"]["harness_pair_accepted_after"]
        and cl["wrong_value_controls"]["harness_wired_accepted_before"] == cl["wrong_value_controls"]["harness_wired_accepted_after"],
        "not_scorable_rows_never_read_as_absent": cl["not_scorable"]["harness_read_as_absent_after"] == 0
        and cl["not_scorable"]["class_c_violation_read_as_absent_after"] == 0
        and all(rl[s]["not_scorable"]["outcome_other_than_not_scorable_after"] == 0 and rl[s]["not_scorable"]["changed"] == 0 for s in ("accepted", "validated")),
        "not_scorable_cases_all_excluded_by_the_harness": cl["not_scorable"]["harness_pair_excluded_after"] == cl["not_scorable"]["cases"]
        == cl["not_scorable"]["harness_wired_excluded_after"],
        "verification36_numbers_reproduced": all(x["equal"] for x in comparison.values()),
    }
    res = {"kind": "ORCH-06C H1 what-if result (R36-08): the review34 harness against the r36 harness with the norm_revision fix",
           "statement": SYNTHETIC_STATEMENT, "reference_set_statement": REFERENCE_SET_STATEMENT,
           "inputs": {"fixtures": {"path": FROZEN["fixtures"][0].as_posix(), "sha256": fx_sha},
                      "parity_matrix": {"path": FROZEN["matrix"][0].as_posix(), "sha256": m_sha},
                      "verification36": {"path": FROZEN["verification36"][0].as_posix(), "sha256": FROZEN["verification36"][1]},
                      "verification36_package_check": {"path": V36_CHECK.as_posix(), "sha256": v36_sha},
                      "rows_old": {"path": WORK_INPUTS["rows_old"].as_posix(), "sha256": old_sha, "harness": old["harness_hashes"]},
                      "rows_new": {"path": WORK_INPUTS["rows_new"].as_posix(), "sha256": new_sha, "harness": new["harness_hashes"]},
                      "parity_run_r36": {"path": WORK_INPUTS["parity_run_r36"].as_posix(), "sha256": run_sha, "cases": len(run["cases"]),
                                         "register_scope": run.get("register_scope"), "harness_modules": run.get("harness_modules"),
                                         "guard": {k: run["guard"].get(k) for k in ("blocked_calls", "violations", "refused_writes", "provider_constructed",
                                                                                    "network_or_process_attempts", "sdk_modules_imported", "database_file_created")},
                                         "expected_harness_reproduced": run.get("expected_harness_reproduced"),
                                         "expected_harness_mismatches_listed": len(run.get("expected_harness_mismatches") or []),
                                         "seconds": run.get("seconds")}},
           "literal_compare_r32": {"review34_sha256": old["harness_hashes"]["literal_compare_r32"], "r36_sha256": new["harness_hashes"]["literal_compare_r32"]},
           "row_level": rl, "case_level": cl, "ws_inside_number_rows": ws_rows, "verification36_comparison": comparison, "checks": checks,
           "ok": all(checks.values())}
    text = json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"ok": res["ok"], "checks": checks, "comparison_equal": {k: x["equal"] for k, x in comparison.items()},
                      "changed_cases": cl["changed_cases"], "class_vs_pair_changes": cl["class_vs_pair_changes"],
                      "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
