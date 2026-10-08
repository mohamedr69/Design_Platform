"""literal_compare_r32 with the real tricky literals of r32-labels-reviewed-2. Run: python -m pytest -q test_literal_compare_r32.py"""
import pytest

import literal_compare_r32 as C


def test_f023_wide_spaced_digits_are_whitespace_insensitive():
    assert C.compare("273 / MT / MEP 2 1 7", "273/MT/MEP217", "identity")["match"]
    assert C.compare("273 / MT / MEP 2 1 7", "273 / MT / MEP 217", "identity")["kind"] == "normalised"
    assert not C.compare("273 / MT / MEP 2 1 7", "273/MT/MEP218", "identity")["match"]


def test_f067_cmw_drawing_number_exact_and_case():
    t = "CMW-17045-C001-01-E-0001"
    assert C.compare(t, t, "identity")["kind"] == "exact"
    assert C.compare(t, "cmw-17045-c001-01-e-0001", "identity")["match"]
    assert C.compare(t, "CMW 17045-C001-01-E-0001", "identity")["match"] is False, "a space is not a hyphen"
    assert not C.compare(t, "CMW-17045-C001-01-E-0002", "identity")["match"]


def test_lacasa_r0n_references_whitespace_and_suffix_base_form():
    t = "NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002- R00"
    assert C.compare(t, "NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002-R00", "identity")["match"]
    assert not C.compare(t, "NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002", "identity")["match"], "no alternate given: base form is not accepted"
    r = C.compare(t, "NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002", "identity", alternates=["NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0002"])
    assert r["match"] and r["kind"] == "alternate_form"
    assert not C.compare(t, "NBC-JGH-SCALE-SDS-MEP-ELE-TEL-2025-0004- R00", "identity")["match"]


def test_mat_116_en_dash_and_minus_variants():
    t = "MAT – 116"
    for p in ("MAT-116", "MAT - 116", "MAT−116", "MAT—116", "mat-116", "MAT‑116"):
        assert C.compare(t, p, "identity")["match"], p
    assert not C.compare(t, "MAT116", "identity")["match"], "a missing dash is a different literal"
    assert not C.compare(t, "MAT-117", "identity")["match"]


def test_fa_6001_and_em_104_spacing():
    assert C.compare("FA- 6001", "FA-6001", "identity")["match"]
    assert C.compare("EM- 104", "EM-104", "identity")["match"]


def test_g1_labelled_tail_either_form():
    t, alt = "B01-ASC-SD-ELE-0102", "B01-ASC-SD-ELE-0102-Rev.00"
    assert C.compare(t, t, "identity", alternates=[alt])["match"]
    r = C.compare(t, "B01-ASC-SD-ELE-0102-Rev.00", "identity", alternates=[alt])
    assert r["match"] and r["kind"] == "alternate_form"
    assert C.compare(t, "B01-ASC-SD-ELE-0102 - Rev. 00", "identity", alternates=[alt])["match"]
    assert not C.compare(t, "B01-ASC-SD-ELE-0102-Rev.00", "identity")["match"], "the tail form needs the row's (g)(1) alternate"


def test_revision_numbers_by_value_letters_as_written():
    assert C.compare("Rev. 0", "0", "revision")["match"]
    assert C.compare("00", "R0", "revision")["match"]
    assert C.compare("02", "Rev.2", "revision")["match"]
    assert not C.compare("01", "00", "revision")["match"]
    assert C.compare("A", "a", "revision")["match"]
    assert not C.compare("A", "B", "revision")["match"]
    assert C.compare("01", None, "revision")["kind"] == "no_prediction"


def test_arabic_literals_are_byte_compared_after_whitespace_only():
    t = "ش إ م / عام/٢٠١٤ / ١٣٢٤"
    assert C.compare(t, "ش إ م/عام/٢٠١٤/١٣٢٤", "identity")["kind"] == "arabic_bytes"
    assert not C.compare(t, "ش إ م / عام/2014 / 1324", "identity")["match"], "Arabic-Indic digits are not folded"
    d = "مخططات معتمدة"
    assert C.compare(d, "مخططات  معتمدة", "decision", truth_class="approved")["kind"] == "decision_literal"


def test_decision_vocabulary():
    assert C.compare("APPROVED", "approved", "decision", truth_class="approved")["match"]
    assert C.compare("B - Approved as noted", "ANN", "decision", truth_class="approved as noted")["match"]
    assert not C.compare("B - Approved as noted", "approved", "decision", truth_class="approved as noted")["match"]
    r = C.compare("REVISE & RE-SUBMIT", "rejected", "decision", truth_class="revise and resubmit")
    assert r["match"] and r["kind"] == "class_application_vocabulary"
    assert not C.compare("APPROVED", "rejected", "decision", truth_class="approved")["match"]
    for neg in ("UR", "n/a", "", None, "none"):
        r = C.compare("APPROVED", neg, "decision", truth_class="approved")
        assert not r["match"] and r["kind"] == "no_decision_asserted", neg


@pytest.mark.parametrize("predicted", ["rejected", "revise and resubmit", "Resubmit"])
def test_d1_resubmission_tolerance(predicted):
    r = C.compare("Approved as noted / Resubmit", predicted, "decision", truth_class="approved as noted", resubmission_required=True)
    assert r["match"] and r["kind"] == "d1_resubmission_tolerance"


def test_d1_tolerance_needs_the_flag_and_never_accepts_plain_approved():
    assert not C.compare("APPROVED AS NOTED", "rejected", "decision", truth_class="approved as noted")["match"]
    assert not C.compare("B+R", "approved", "decision", truth_class="approved as noted", resubmission_required=True)["match"]
    assert C.compare("B+R", "ANN", "decision", truth_class="approved as noted", resubmission_required=True)["kind"] == "class"
    assert C.compare("B+R", "B + R", "decision", truth_class="approved as noted", resubmission_required=True)["kind"] == "decision_literal"


# --- ORCH-06C (Independent Verification 36, finding R36-08, H1): whitespace inside a revision value ----------------------
# Appended by R36HARNESS-IMPL; every test above is unchanged byte for byte. The fixtures are the frozen ORCH-06 SYNTHETIC
# predictions (PILOT/evaluator-offline-r32/SYNTHETIC-PREDICTIONS.json): each value is built from the r32 truth strings by
# a fixed rule and is not a prediction of any model. The truth rows are the frozen review34 dry-run/TRUTH-R32.json. Both
# files are read-only and hash-checked here; nothing is written.
import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import re  # noqa: E402

import lane_judge_r32 as J  # noqa: E402

_PILOT = pathlib.Path("G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot")
_FIXTURES = (_PILOT / "evaluator-offline-r32" / "SYNTHETIC-PREDICTIONS.json", "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774")
_TRUTH = (_PILOT / "review34" / "dry-run" / "TRUTH-R32.json", "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064")
_WRONG_VALUE_INTENTS = ("wrong", "page_keyed_wrong")
_STATES = ("accepted", "validated")


def _review34_norm_revision(value) -> str:
    # review34 literal_compare_r32.norm_revision (sha256 ec2221c8...), reproduced verbatim for the parity test below
    s = "" if value is None else str(value).strip()
    if C.is_arabic(s):
        return C.norm_text(s)
    s = C._DASH_RE.sub("-", s).upper()
    s = C._WS_RE.sub(" ", s).strip()
    m = re.fullmatch(r"(?:REVISION|REV\.?|R\.?)?\s*0*(\d+)", s)
    if m:
        return f"R{int(m.group(1))}"
    return C._WS_RE.sub("", s)


def _frozen_json(path_and_sha):
    path, want = path_and_sha
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == want, f"PACKET MISMATCH: {path}"
    return json.loads(raw.decode("utf-8"))


@pytest.fixture(scope="module")
def frozen():
    fx = _frozen_json(_FIXTURES)
    assert fx["kind"] == "SYNTHETIC" and all(f["not_a_model_prediction"] is True for f in fx["fixtures"])
    return fx["fixtures"], _frozen_json(_TRUTH)


def _target(truth, f, value, state):
    jd = J.judge_document(truth, f["pool_id"], {"facts": [] if value is None else [{"page": f["page"], "field": f["field"], "value": value, "state": state}]})
    return next(r for r in jd["rows"] if (r["page"], r["field"]) == (f["page"], f["field"]))


def test_h1_the_task_examples():
    for value, norm in (("0 1", "R1"), ("0 0", "R0"), ("REV 0 1", "R1"), ("R 01", "R1"), ("Rev. 0 2", "R2")):
        assert C.norm_revision(value) == norm, value
    assert C.norm_revision("01") == C.norm_revision("1") == C.norm_revision("Rev. 01") == "R1"


@pytest.mark.parametrize("truth, predicted, norm", [
    ("01", "0 1", "R1"), ("00", "0 0", "R0"), ("01", "REV 0 1", "R1"), ("01", "R 01", "R1"), ("02", "Rev. 0 2", "R2"),
    ("00", "R 0 0", "R0"), ("10", "1 0", "R10"), ("01", "0\u00a01", "R1"), ("01", "0\t1", "R1"), ("03", "0\u20093", "R3"),
    ("1", "Revision 0 1", "R1"), ("Rev. 0", "r. 0 0", "R0"), ("00", " 0  0 ", "R0"), ("12", "1 2", "R12")])
def test_h1_whitespace_inside_a_revision_number_is_removed_before_the_parse(truth, predicted, norm):
    r = C.compare(truth, predicted, "revision")
    assert r["match"] and r["kind"] == "normalised" and r["truth_norm"] == r["predicted_norm"] == norm, r


@pytest.mark.parametrize("truth, predicted", [
    ("01", "0 1 2"),        # a digit inserted with spaces reads R12, not R1
    ("01", "1 0"),          # the digits in another order read R10
    ("00", "0 1"), ("02", "0 2 0"), ("1", "1 1"), ("10", "0 1"),
    ("01", "R EV 01"),      # whitespace inside the prefix: not a prefix (the prefix rule is unchanged) -> 'REV01'
    ("01", "0-1"), ("01", "0 - 1"), ("01", "0 \u2013 1"),   # a dash is not whitespace
    ("01", "01A"), ("01", "0 1 A"), ("A", "A 1")])
def test_h1_adversarial_values_stay_different(truth, predicted):
    r = C.compare(truth, predicted, "revision")
    assert not r["match"] and r["kind"] == "different", r


def test_h1_non_numeric_values_keep_the_fallback():
    assert C.compare("A1", "A 1", "revision")["match"], "the fallback already removed whitespace ('A 1' -> 'A1')"
    assert C.norm_revision("A 1") == C.norm_revision("A1") == "A1"
    assert C.norm_revision("p 0 1") == "P01"
    assert C.norm_revision("R EV 1") == "REV1"
    assert C.norm_revision("0-1") == C.norm_revision("0 \u2013 1") == "0-1", "dash folding unchanged; a dashed value is not a number"
    assert C.compare("A", "a", "revision")["match"] and not C.compare("A1", "A 2", "revision")["match"]
    assert C.norm_revision(None) == C.norm_revision("") == C.norm_revision("   ") == ""


def test_h1_arabic_revision_handling_is_unchanged():
    a = "\u0660 \u0661"                              # Arabic-Indic digits: byte comparison after whitespace removal only
    assert C.norm_revision(a) == "\u0660\u0661" == _review34_norm_revision(a)
    assert C.compare("\u0660\u0661", a, "revision")["kind"] == "arabic_bytes"
    assert not C.compare("01", a, "revision")["match"], "Arabic-Indic digits are not mapped to ASCII digits"


def test_h1_only_values_with_inner_whitespace_change(frozen):
    fixtures, truth = frozen
    values = {f["prediction"]["value"] for f in fixtures if f["field"] == "revision" and f["prediction"]["value"] is not None}
    for rec in truth["rows"].values():
        if rec["field"] == "revision":
            values |= {v for v in [rec.get("literal"), *(rec.get("candidates") or []), *(rec.get("alternates") or [])] if v}
    values |= {"0 1", "0 0", "REV 0 1", "R 01", "Rev. 0 2", "R 0 0", "1 0", "0 1 2", "A 1", "R EV 1", "01", "Rev. 0", "REV.02", "r1"}
    changed = {v for v in values if C.norm_revision(v) != _review34_norm_revision(v)}
    for v in values - changed:
        assert C.norm_revision(v) == _review34_norm_revision(v)
    for v in changed:
        inner = C._WS_RE.sub(" ", str(v).strip())
        assert " " in inner and re.fullmatch(r"R\d+", C.norm_revision(v)), v
    assert {"0 0", "0 1", "0 2", "0 3"} <= changed and len(values) > 40


def test_h1_the_53_ws_inside_number_rows_now_equal_their_truth(frozen):
    fixtures, truth = frozen
    ws = [f for f in fixtures if f["variant"] == "ws_inside_number"]
    assert len(ws) == 53 and {f["field"] for f in ws} == {"revision"} and {f["intent"] for f in ws} == {"correct"}
    assert {f["prediction"]["value"] for f in ws} == {"0 0", "0 1", "0 2", "0 3"}
    for f in ws:
        rec = truth["rows"][f["truth_key"]]
        assert rec["truth_kind"] == "value" and f["expected_harness"]["judge"]["verdict"] == "critical_false_acceptance"
        r = C.compare_row(rec, f["prediction"]["value"])
        assert r["match"] and r["kind"] == "normalised" and r["truth_norm"] == r["predicted_norm"], (f["id"], r)
        for state in _STATES:
            row = _target(truth, f, f["prediction"]["value"], state)
            assert row["outcome"] == "recovered_clean" and not row["critical"] and row["match_kinds"] == ["normalised"], (f["id"], state, row)


def test_h1_every_wrong_value_control_keeps_its_frozen_verdict(frozen):
    fixtures, truth = frozen
    controls = [f for f in fixtures if f["intent"] in _WRONG_VALUE_INTENTS]
    assert len(controls) == 1636
    accepted_before = 0
    forgiven = set()
    for f in controls:
        v, exp = f["prediction"]["value"], f["expected_harness"]
        rec = truth["rows"][f["truth_key"]]
        if exp["literal_compare"].get("applicable"):
            r = C.compare_row(rec, v)
            assert r["match"] == exp["literal_compare"]["match"] and r["kind"] == exp["literal_compare"]["kind"], (f["id"], v, r)
        accepted_before += exp["judge"]["outcome"] in ("recovered_clean", "recovered_mixed")
        for state in _STATES:
            row = _target(truth, f, v, state)
            got = (row["outcome"], len(row["critical"]), row["cross_page"], sorted(row.get("match_kinds") or []))
            want = (exp["judge"]["outcome"], exp["judge"]["critical"], exp["judge"]["cross_page"], sorted(exp["judge"]["match_kinds"]))
            if exp["judge"]["cross_page"]:
                # ORCH-08 (A-09 point 4, CP-R38): a wrong value the frozen judge forgave as a cross-page copy is no longer
                # forgiven without evidence (no source hash is given here, so no association is made at all): it is a
                # critical wrong value. The evidenced verdicts of these fixtures are in CROSS-PAGE-WHATIF.json.
                forgiven.add(f["id"])
                want = ("fp" if rec["truth_kind"] == "absent" else "wrong_only", 1, 0, [])
            assert got == want, (f["id"], state, got, want)
    # the frozen harness accepts 13 decision controls by its declared vocabulary (H2, 'Code D - Rejected'); the fix adds none
    assert accepted_before == 13
    # Verification 36 R36-09: 22 register-channel wrong-value controls were forgiven as cross-page copies; and 3 page-keyed
    # controls on ABSENT pages of compilations (the frozen ABSENT branch did not check the compilation flag)
    assert len(forgiven) == 25 and sum(1 for f in controls if f["id"] in forgiven and f["intent"] == "page_keyed_wrong") == 3


def test_h1_every_revision_wrong_value_control_is_still_a_critical(frozen):
    fixtures, truth = frozen
    controls = [f for f in fixtures if f["intent"] in _WRONG_VALUE_INTENTS and f["field"] == "revision"]
    assert len(controls) == 488
    for f in controls:
        for state in _STATES:
            row = _target(truth, f, f["prediction"]["value"], state)
            assert row["outcome"] in ("wrong_only", "fp") and len(row["critical"]) == 1, (f["id"], state, row["outcome"])


def test_h1_not_scorable_rows_stay_excluded_and_never_read_as_absent(frozen):
    fixtures, truth = frozen
    ns = [f for f in fixtures if f["truth_kind"] == "not_scorable"]
    assert len(ns) == 121
    for f in ns:
        for state in _STATES:
            row = _target(truth, f, f["prediction"]["value"], state)
            assert row["outcome"] == "not_scorable" and row["truth_kind"] == "not_scorable", (f["id"], state)
            assert sorted({u["kind"] for u in row["unresolved"]}) == f["expected_harness"]["judge"]["unresolved_kinds"], (f["id"], state)
