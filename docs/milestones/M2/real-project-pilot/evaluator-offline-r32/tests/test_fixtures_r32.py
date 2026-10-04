"""ORCH-06: tests of the SYNTHETIC fixture generator (fixtures_r32.py). No model request; nothing written except pytest's
own junit file. Run from C:/t/iso/work/r2x/r35:  python -m pytest -q <package>/tests/test_fixtures_r32.py"""
import collections
import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True
PKG = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG / "scripts"))
import common_r35 as C  # noqa: E402
import fixtures_r32 as F  # noqa: E402

_OPENED: list = []
_RECORD = {"on": False}


def _hook(event, args):
    if _RECORD["on"] and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        _OPENED.append(os.path.normcase(os.path.abspath(os.fsdecode(args[0]))))


sys.addaudithook(_hook)
_BUILT = {}


def built():
    if "data" not in _BUILT:
        _BUILT["data"] = F.build()
    return _BUILT["data"]


def by_key():
    out = collections.defaultdict(list)
    for fx in built()["fixtures"]:
        out[fx["truth_key"]].append(fx)
    return out


def test_generation_is_deterministic_and_equals_the_packaged_file():
    a = json.dumps(F.build(), sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    b = json.dumps(F.build(), sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    assert a == b
    packaged = PKG / "SYNTHETIC-PREDICTIONS.json"
    assert packaged.read_text(encoding="utf-8") == a, "the packaged SYNTHETIC-PREDICTIONS.json is the generator's output byte for byte"


def test_only_the_two_frozen_inputs_are_read_and_no_prediction_file():
    _OPENED.clear()
    _RECORD["on"] = True
    try:
        F.build()
    finally:
        _RECORD["on"] = False
    data_files = {p for p in _OPENED if not p.endswith((".py", ".pyc"))}
    allowed = {os.path.normcase(os.path.abspath(str(C.FROZEN[k][0]))) for k in ("truth_r32", "labels_eval_input")}
    assert data_files == allowed, sorted(data_files ^ allowed)
    banned = ("four-arm", "r26", "rows-", "lane-", "ai-pilot", "onedrive", "r32-stage", "renders", "crops", "prediction")
    assert not [p for p in _OPENED if any(b in p.lower() for b in banned) and "synthetic" not in p.lower()]


def test_every_fixture_is_synthetic_and_carries_a_computed_harness_verdict():
    d = built()
    assert d["kind"] == "SYNTHETIC" and "None is a prediction of any model" in d["statement"]
    for fx in d["fixtures"]:
        assert fx["kind"] == "SYNTHETIC" and fx["not_a_model_prediction"] is True
        assert fx["truth_key"] == C.row_key(fx["pool_id"], fx["page"], fx["field"])
        assert fx["variant"] and fx["intent"] and fx["expected_harness"]["judge"]["verdict"] in C.VERDICTS
    ids = [fx["id"] for fx in d["fixtures"]]
    assert ids == sorted(ids) and len(set(ids)) == len(ids)


def test_expected_harness_verdicts_are_recomputed_from_the_frozen_harness():
    LC, J, A = C.import_harness()
    truth = C.load_json("truth_r32")
    for fx in built()["fixtures"]:
        v = fx["prediction"]["value"]
        facts = [] if v is None else [{"page": fx["page"], "field": fx["field"], "value": v, "state": "accepted"}]
        got = C.harness_judge(J, truth, fx["pool_id"], facts)[(fx["page"], fx["field"])]
        assert got == fx["expected_harness"]["judge"], fx["id"]
        if v is not None and fx["truth_kind"] == "value":
            assert bool(LC.compare_row(truth["rows"][fx["truth_key"]], v)["match"]) == fx["expected_harness"]["literal_compare"]["match"]


def test_every_canonical_truth_row_is_covered_and_aliases_are_listed():
    d = built()
    truth = C.load_json("truth_r32")
    canon = {k for k, r in truth["rows"].items() if not truth["documents"][r["pool_id"]]["is_alias"]}
    covered = {fx["truth_key"] for fx in d["fixtures"]}
    assert canon == covered
    excluded = {e["truth_key"] for e in d["excluded_rows"]}
    assert excluded == set(truth["rows"]) - canon and {k.split("|")[0] for k in excluded} == {"F031", "F059"}
    assert d["coverage"]["canonical_rows_without_fixture"] == []


def test_every_scorable_value_row_has_its_variants_and_wrong_value_controls():
    truth = C.load_json("truth_r32")
    need = {"identity": [{"exact"}, {"digit_changed"}, {"other_document_value"}, {"project_job_number"}, {"absent"},
                         {"hyphen_moved", "hyphen_inserted", "arabic_indic_digits_as_ascii"}, {"ws_inserted_after_first_separator", "arabic_ws_extra"}],
            "revision": [{"exact"}, {"digit_changed"}, {"other_document_value"}, {"letter_value"}, {"prefixed_wrong_number"},
                         {"leading_zero_added"}, {"absent"}],
            "decision": [{"literal_exact"}, {"application_word"}, {"other_document_value"}, {"code_D_with_legend"}, {"absent"},
                         {"no_decision_word:UR"}]}
    kb = by_key()
    for k, r in truth["rows"].items():
        if truth["documents"][r["pool_id"]]["is_alias"] or r["truth_kind"] != "value":
            continue
        variants = {fx["variant"] for fx in kb[k] if fx["group"] == f"{r['field']}_value"}
        for alternatives in need[r["field"]]:
            assert variants & alternatives, (k, alternatives)
        if r["field"] == "decision":
            assert any(v.startswith("wrong_class:") for v in variants), k
            if r["resubmission_required"]:
                assert {"d1:rejected", "d1:resubmit"} <= variants, k
        wrong = [fx for fx in kb[k] if fx["intent"] == "wrong"]
        assert len(wrong) >= 3, k


def test_absent_and_not_scorable_rows_get_absent_truth_and_wrong_values():
    truth = C.load_json("truth_r32")
    kb = by_key()
    for k, r in truth["rows"].items():
        if truth["documents"][r["pool_id"]]["is_alias"]:
            continue
        fxs = kb[k]
        if r["truth_kind"] == "absent":
            vs = {fx["variant"] for fx in fxs if fx["group"] == "absent_row"}
            assert "absent" in vs and any(fx["intent"] == "wrong" for fx in fxs if fx["group"] == "absent_row"), k
        if r["truth_kind"] == "not_scorable":
            ns = [fx for fx in fxs if fx["group"] == "not_scorable_row"]
            vs = {fx["variant"] for fx in ns}
            assert {"absent", "wrong_value"} <= vs, k
            assert any(fx["prediction"]["value"] is not None and fx["variant"] != "wrong_value" for fx in ns), k
            assert all(fx["expected_harness"]["judge"]["verdict"] == "excluded" for fx in fxs), k


def test_named_cases_of_the_task_are_present():
    fx = built()["fixtures"]

    def find(key, variant):
        return [f for f in fx if f["truth_key"] == key and f["variant"] == variant]

    assert find("F067|1|identity", "ws_gap_C001_01")[0]["prediction"]["value"] == "CMW-17045-C001- 01-E-0001"
    assert find("F023|1|identity", "ws_removed_inside_MEP_2_1_7")[0]["prediction"]["value"] == "273 / MT / MEP217"
    assert find("F001|1|identity", "dash_as_hyphen")[0]["prediction"]["value"] == "MAT - 116"
    assert find("F001|1|identity", "dash_as_minus")[0]["prediction"]["value"] == "MAT \u2212 116"
    assert find("F001|1|identity", "dash_as_figure_dash")[0]["prediction"]["value"] == "MAT \u2012 116"
    assert find("F008|3|identity", "g1_labelled_tail_present")[0]["prediction"]["value"] == "B01-ASC-SD-ELE-0102-Rev.00"
    assert find("F003|1|identity", "suffix_base_form")[0]["prediction"]["value"] == "NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002"
    assert find("F043|1|identity", "arabic_ws_removed") and find("F043|1|identity", "arabic_indic_digits_as_ascii")
    assert find("F014|1|decision", "arabic_literal_ws_extra") and find("F014|1|decision", "arabic_literal_ws_removed")
    assert find("F038|1|decision", "arabic_literal_ws_extra")
    assert find("F001|2|decision", "d1:rejected") and find("F030|1|decision", "d1:B+R")
    assert find("F011|1|decision", "synonym:Code C") and find("F008|1|decision", "synonym:B")
    assert find("F025|1|decision", "literal_exact")[0]["prediction"]["value"] == "Code C"   # equal to the literal: not repeated as a synonym
    assert not find("F025|1|decision", "synonym:Code C")
    assert find("F009|1|revision", "leading_zero_added")[0]["prediction"]["value"] == "00"
    assert find("F001|1|revision", "leading_zero_dropped")[0]["prediction"]["value"] == "2"
    for pid in C.COMPILATIONS_PAGE_KEYED:
        assert any(f["group"] == "compilation_page_keyed" and f["pool_id"] == pid for f in fx), pid
    for pid in C.DRAWING_SETS:
        assert sum(1 for f in fx if f["group"] == "cross_page_identity" and f["pool_id"] == pid) >= 6, pid
    assert any(f["group"] == "cross_page_identity" and f.get("cross_page_subgroup") == "cover_enclosure_package" for f in fx)
    for key in ("F019|1|revision", "F069|1|identity", "F069|2|identity", "F069|3|identity", "F069|4|identity"):
        vs = {f["variant"] for f in fx if f["truth_key"] == key}
        assert {"absent", "wrong_value"} <= vs, key
    assert {f["variant"] for f in fx if f["truth_key"] == "F019|1|revision"} >= {"candidate_1", "candidate_2"}


def test_harness_reference_points():
    fx = built()["fixtures"]
    verdict = {(f["truth_key"], f["variant"]): f["expected_harness"]["judge"]["verdict"] for f in fx}
    assert verdict[("F001|1|identity", "exact")] == "correct"
    assert verdict[("F001|1|identity", "dash_as_hyphen")] == "correct"
    assert verdict[("F001|1|identity", "digit_changed")] == "critical_false_acceptance"
    assert verdict[("F043|2|revision", "prefixed_far_number")] == "critical_false_acceptance"
    assert verdict[("F001|2|decision", "d1:rejected")] == "correct"
    assert verdict[("F001|2|decision", "wrong_class:approved")] == "critical_false_acceptance"
    assert verdict[("F002|1|identity", "value_of_page_2")] == "critical_false_acceptance"
    assert verdict[("F016|1|identity", "identity_of_page_2")] == "missed"
    assert all(f["expected_harness"]["judge"]["verdict"] == "missed" for f in fx if f["variant"] == "absent" and f["truth_kind"] == "value")
    assert all(f["expected_harness"]["judge"]["verdict"] == "absent_accepted" for f in fx if f["variant"] == "absent" and f["truth_kind"] == "absent")
