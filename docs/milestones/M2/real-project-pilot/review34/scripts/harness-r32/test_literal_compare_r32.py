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
