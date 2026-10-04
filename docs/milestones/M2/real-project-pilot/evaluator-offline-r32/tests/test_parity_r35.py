"""ORCH-06: tests of the parity harness (run_evaluator_offline_r32.py) and of the packaged PARITY-MATRIX.json.
No model request: the runner is started as a child process on SYNTHETIC fixtures only, with its own guards; this test
process imports no evaluator. Run from C:/t/iso/work/r2x/r35 with --basetemp under the work folder."""
import collections
import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
PKG = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG / "scripts"))
import common_r35 as C  # noqa: E402
import run_evaluator_offline_r32 as RUN  # noqa: E402  (module import only: no guard, no evaluator is loaded here)

PY = sys.executable
FIXTURES = PKG / "SYNTHETIC-PREDICTIONS.json"
WORK = C.WORK
CASES = [("F001|1|identity", "exact"), ("F001|1|identity", "dash_as_hyphen"), ("F008|3|identity", "g1_labelled_tail_present"),
         ("F003|1|identity", "suffix_base_form"), ("F023|1|identity", "ws_removed_inside_MEP_2_1_7"), ("F067|1|identity", "ws_gap_C001_01"),
         ("F043|1|identity", "arabic_ws_removed"), ("F043|1|identity", "arabic_indic_digits_as_ascii"),
         ("F001|1|revision", "prefix_Rev_dot_space"), ("F001|1|revision", "leading_zero_dropped"), ("F043|2|revision", "prefixed_far_number"),
         ("F043|2|revision", "bare_number"), ("F001|2|decision", "d1:rejected"), ("F001|2|decision", "application_word"),
         ("F001|2|decision", "synonym:approved as noted"), ("F001|1|decision", "no_decision_word:UR"), ("F025|1|decision", "application_word"),
         ("F002|1|identity", "value_of_page_2"), ("F016|1|identity", "identity_of_page_2"), ("F019|1|revision", "candidate_1"),
         ("F069|2|identity", "absent"), ("F069|1|identity", "wrong_value"), ("F024|1|identity", "truth_literal"),
         ("F001|1|identity", "digit_changed"), ("F001|2|identity", "identity_of_page_1")]


def fixture_ids():
    fx = json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]
    idx = {(f["truth_key"], f["variant"]): f["id"] for f in fx}
    return {k: idx[k] for k in CASES}


def run_subset(tmp_path, scope, name):
    ids = fixture_ids()
    out = tmp_path / f"{name}.json"
    env = {k: v for k, v in os.environ.items()}
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([PY, str(PKG / "scripts/run_evaluator_offline_r32.py"), "--fixtures", str(FIXTURES), "--out", str(out),
                        "--scope", scope, "--only", ",".join(sorted(ids.values()))], cwd=str(WORK), env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    by = {(c["truth_key"], c["variant"], c["channel"]): c for c in data["cases"]}
    return data, by


def test_classify_categories():
    assert RUN.classify("value", "correct", "correct") == "parity"
    assert RUN.classify("value", "critical_false_acceptance", "correct") == "a_stricter_critical"
    assert RUN.classify("absent", "critical_false_acceptance", "absent_accepted") == "a_stricter_critical"
    assert RUN.classify("value", "missed", "correct") == "a_stricter_recovery"
    assert RUN.classify("value", "correct", "critical_false_acceptance") == "b_looser_accepts_wrong"
    assert RUN.classify("value", "missed", "critical_false_acceptance") == "b_looser_hides_wrong"
    assert RUN.classify("value", "correct", "missed") == "b_looser_credit"
    assert RUN.classify("not_scorable", "excluded", "excluded") == "c_not_scorable_excluded"
    assert RUN.classify("not_scorable", "absent_accepted", "excluded") == "c_violation_read_as_absent"
    assert RUN.classify("not_scorable", "correct", "excluded") == "c_violation_scored"


def test_application_reachability_rule():
    assert RUN.application_reachable("decision", "ANN") and RUN.application_reachable("decision", "rejected")
    assert not RUN.application_reachable("decision", "approved as noted") and not RUN.application_reachable("decision", "UR")
    assert RUN.application_reachable("identity", "anything") and RUN.application_reachable("revision", "Rev. 01")


def test_synthetic_rows_carry_exactly_one_fact():
    r = RUN.register_row("2", "decision", "ANN", "0" * 64)
    assert r["extracted"]["records"] == [{"page": 2, "reference": None, "status": "ANN"}]
    r = RUN.register_row("1", "revision", "01", "0" * 64)
    assert r["extracted"]["records"] == [{"page": 1, "reference": None, "printed_revision": "01"}]


def test_subset_run_reference_points_and_guards(tmp_path):
    data, by = run_subset(tmp_path, "full", "subset-full")
    g = data["guard"]
    assert g["provider_constructed"] == 0 and g["network_or_process_attempts"] == 0 and g["violations"] == [] and g["refused_writes"] == []
    assert g["sdk_modules_imported"] == [] and g["database_file_created"] is False
    assert data["expected_harness_reproduced"] is True
    assert all(v["verified"] for v in data["code_locations"].values())
    for ch in ("register", "ai_validated"):
        assert by[("F001|1|identity", "exact", ch)]["class_vs_pair"] == "parity"
        c = by[("F001|1|identity", "dash_as_hyphen", ch)]
        assert c["class_vs_pair"] == "a_stricter_critical" and "same_identity=near" in c["evaluator"]["rule"]
        assert by[("F008|3|identity", "g1_labelled_tail_present", ch)]["class_vs_pair"] == "a_stricter_critical"
        assert by[("F003|1|identity", "suffix_base_form", ch)]["evaluator"]["rule"].endswith("same_identity=suffix->correct")
        for k in (("F023|1|identity", "ws_removed_inside_MEP_2_1_7"), ("F067|1|identity", "ws_gap_C001_01"),
                  ("F043|1|identity", "arabic_ws_removed"), ("F001|1|revision", "leading_zero_dropped"),
                  ("F001|2|decision", "application_word"), ("F025|1|decision", "application_word")):
            assert by[(*k, ch)]["class_vs_pair"] == "parity" and by[(*k, ch)]["evaluator"]["verdict"] == "correct", k
        assert by[("F043|1|identity", "arabic_indic_digits_as_ascii", ch)]["class_vs_pair"] == "parity"
        c = by[("F001|1|revision", "prefix_Rev_dot_space", ch)]
        assert c["class_vs_pair"] == "a_stricter_critical" and "norm_rev_differs" in c["evaluator"]["rule"]
        assert by[("F043|2|revision", "prefixed_far_number", ch)]["class_vs_pair"] == "b_looser_accepts_wrong"
        assert by[("F043|2|revision", "bare_number", ch)]["class_vs_pair"] == "a_stricter_critical"
        assert by[("F001|2|decision", "d1:rejected", ch)]["class_vs_pair"] == "a_stricter_critical"
        c = by[("F002|1|identity", "value_of_page_2", ch)]
        assert c["class_vs_pair"] == "b_looser_hides_wrong" and c["evaluator"]["fact"]["how"] == "cross_page"
        assert [s["row"] for s in c["side_rows"] if s["class"] == "b_looser_credit"] == ["F002|2|identity"]
        c = by[("F016|1|identity", "identity_of_page_2", ch)]
        assert c["class_vs_pair"] == "parity" and [s["row"] for s in c["side_rows"]] == ["F016|2|identity"]
        for k in (("F019|1|revision", "candidate_1"), ("F069|2|identity", "absent"), ("F069|1|identity", "wrong_value"),
                  ("F024|1|identity", "truth_literal")):
            assert by[(*k, ch)]["class_vs_pair"] == "c_not_scorable_excluded", k
        assert by[("F001|1|identity", "digit_changed", ch)]["class_vs_pair"] == "parity"
        assert by[("F001|2|identity", "identity_of_page_1", ch)]["evaluator"]["verdict"] == "absent_accepted"
    c = by[("F001|2|decision", "synonym:approved as noted", "register")]
    assert c["evaluator"]["verdict"] == "not_evaluated" and c["evaluator"]["rule"] == "emission:decision_status_not_in_POSITIVE"
    assert c["class_vs_wired"] == "parity" and not c["application_reachable"]
    assert by[("F001|1|decision", "no_decision_word:UR", "register")]["class_vs_pair"] == "parity"
    assert by[("F001|1|decision", "no_decision_word:UR", "ai_validated")]["class_vs_pair"] == "a_stricter_critical"
    reads = [r["path"].lower() for r in g["files_opened_for_reading_outside_python"] if r["exists"]]
    data_reads = {p for p in reads if not p.endswith((".py", ".pyc"))}
    allowed = {str(C.FROZEN[k][0]).replace("\\", "/").lower() for k in ("truth_r32", "labels_eval_input")} | {str(FIXTURES).replace("\\", "/").lower()}
    assert data_reads <= allowed, sorted(data_reads - allowed)


def test_full_and_document_scope_give_identical_verdicts_and_the_run_is_deterministic(tmp_path):
    a, by_a = run_subset(tmp_path, "full", "a")
    b, by_b = run_subset(tmp_path, "document", "b")
    c, by_c = run_subset(tmp_path, "document", "c")
    strip = lambda d: {k: {x: y for x, y in v.items()} for k, v in d.items()}
    assert strip(by_a) == strip(by_b) == strip(by_c)


def test_the_runner_refuses_an_output_outside_the_work_folder(tmp_path):
    r = subprocess.run([PY, str(PKG / "scripts/run_evaluator_offline_r32.py"), "--fixtures", str(FIXTURES), "--out",
                        str(PKG / "evidence" / "should-not-exist.json"), "--limit", "1"], cwd=str(WORK),
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
    assert r.returncode != 0 and not (PKG / "evidence" / "should-not-exist.json").exists()


def test_parity_matrix_is_complete_and_consistent():
    m = json.loads((PKG / "PARITY-MATRIX.json").read_text(encoding="utf-8"))
    fx = json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]
    cases = m["cases"]
    assert len(cases) == 2 * len(fx) == m["summary"]["cases"]
    assert collections.Counter(c["fixture_id"] for c in cases) == collections.Counter({f["id"]: 2 for f in fx})
    for c in cases:
        assert c["evaluator"]["verdict"] in C.VERDICTS and c["harness_pair"]["verdict"] in C.VERDICTS
        assert c["harness_wired"]["verdict"] in C.VERDICTS and c["class_vs_pair"] and c["class_vs_wired"]
    recount = collections.Counter(c["class_vs_pair"] for c in cases)
    assert dict(recount) == m["summary"]["class_vs_pair"]["all"]
    assert m["summary"]["scope_equivalence"]["identical"] is True
    assert all(c["class_vs_pair"] == "c_not_scorable_excluded" for c in cases if c["truth_kind"] == "not_scorable")
    assert m["kind"] == "SYNTHETIC" or "SYNTHETIC" in m["statement"]
