"""Review 29 C2 -- conflict adjudication (CA) under the written evidence-ordering contract. Synthetic fixtures built from
STRUCTURE (a form number vs a referenced drawing under a reference label; a truncated first read vs a source-bound full
number; two own-labelled numbering systems), with literals invented here -- never the stored documents' strings.
Order / recency invariance, the deterministic reading, revision E5, and the reader path end to end. No model."""
import itertools

import pytest

from app.ai import evidence_reader as er

from ._keyed_provider import KeyedProvider
from ._r29 import configure, context_read, discovery, envelope_obs, no_submittal_reader, norm_region, text_page, value_read  # noqa: F401
from .test_ai_pilot_r19 import Stage


@pytest.fixture(autouse=True)
def _ready(no_submittal_reader):
    yield


def st_of(readings, texts, *, det=None, ctx_texts=None):
    by = {"discovery": texts, "blind_small": texts, "blind_standard": texts}
    if ctx_texts is not None:
        by["blind_context"] = ctx_texts
    return {"readings": readings, "texts": texts, "texts_by_source": by, "det": det}


FORM_TEXT = [("text", "Submittal No. 42   Rev 00\nDwg. Ref. AB-12-345\nProject Code 777")]


def form_readings():
    return [{"source": "discovery", "value": "42", "legible": True, "label": "Submittal No."},
            {"source": "blind_small", "value": "AB-12-345", "legible": True, "label": "Dwg. Ref."},
            {"source": "blind_context", "value": "42", "legible": True, "label": "Submittal No.", "role": "own_identity"}]


FORM_DISC = {"other_numbers": [{"role": "referenced_drawing", "literal": "AB-12-345"}, {"role": "project_or_contract", "literal": "777"}]}


def test_d04_shape_the_own_form_number_resolves_over_a_referenced_drawing():
    res = er.adjudicate_conflict("identity", st_of(form_readings(), FORM_TEXT, ctx_texts=FORM_TEXT), FORM_DISC)
    assert res["record"]["resolved"] and res["verdict"]["value"] == "42" and res["verdict"]["state"] == "validated"
    assert res["record"]["disqualified"] == {"AB-12-345": "role_contradiction"}
    assert {s["value"] for s in res["verdict"]["superseded"]} == {"AB-12-345"}


@pytest.mark.parametrize("order", list(itertools.permutations(range(3))))
def test_order_and_recency_never_matter(order):
    rs = [form_readings()[i] for i in order]
    res = er.adjudicate_conflict("identity", st_of(rs, FORM_TEXT, ctx_texts=FORM_TEXT), FORM_DISC)
    assert res["verdict"]["value"] == "42"


def test_without_a_second_independent_support_nothing_resolves():
    rs = [r for r in form_readings() if r["source"] != "blind_context"]          # the form number read by discovery only
    res = er.adjudicate_conflict("identity", st_of(rs, FORM_TEXT), FORM_DISC)
    assert not res["record"]["resolved"] and "verdict" not in res, "discovery + source text, no blind reading: E4 not met"


def test_a_reference_reading_is_not_disqualified_without_evidence():
    rs = form_readings()
    rs[1] = {**rs[1], "label": "Drawing No."}                   # the competing reading now carries an OWN label
    res = er.adjudicate_conflict("identity", st_of(rs, FORM_TEXT, ctx_texts=FORM_TEXT), {"other_numbers": []})
    assert not res["record"]["resolved"], "a source-bound competitor with an own label keeps the conflict held"


TRUNC_TEXT = [("text", "PROJECT NO. ZZ9\nDOCUMENT NO. XY1_ABC_DEF_MAIN\nREVISION NO. K")]


def test_d12_shape_a_truncated_first_read_is_not_source_bound():
    rs = [{"source": "discovery", "value": "XY1_ABC_DEF_MAIN", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_small", "value": "XY1_ABC_DEF", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_context", "value": "XY1_ABC_DEF_MAIN", "legible": True, "label": "DOCUMENT NO.", "role": "own_identity"}]
    res = er.adjudicate_conflict("identity", st_of(rs, TRUNC_TEXT, ctx_texts=TRUNC_TEXT), {})
    assert res["verdict"]["value"] == "XY1_ABC_DEF_MAIN" and res["record"]["disqualified"] == {"XY1_ABC_DEF": "not_source_bound"}


def test_one_model_reading_never_wins_even_with_source_text():
    """C2 revision 1: three different readings, the full number read once (targeted) and source-bound: E4 needs two
    distinct model readings, so nothing resolves."""
    rs = [{"source": "discovery", "value": "XY1_ABC_DE", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_small", "value": "XY1_ABC_DEF", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_context", "value": "XY1_ABC_DEF_MAIN", "legible": True, "label": "DOCUMENT NO.", "role": "own_identity"}]
    res = er.adjudicate_conflict("identity", st_of(rs, TRUNC_TEXT, ctx_texts=TRUNC_TEXT), {})
    assert not res["record"]["resolved"] and "verdict" not in res


def test_split_text_regression_a_truncation_that_is_a_whole_token_is_never_validated():
    """The offline-regression shape (D12 / D19 in the L1 replay under revision 0): the text layer breaks a long number,
    so the truncated first blind read is a whole token in the source text and the full number read by discovery is not.
    Revision 0 validated the truncation; revision 1 keeps the conflict held."""
    split = [("text", "DOCUMENT NO. XY1_ABC_DEF  REVISION NO. K\nPROJECT NO. ZZ9\n_MAIN")]
    rs = [{"source": "discovery", "value": "XY1_ABC_DEF_MAIN", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_small", "value": "XY1_ABC_DEF", "legible": True, "label": "DOCUMENT NO."}]
    assert er.region_support("identity", "XY1_ABC_DEF", split)[0] == "text" and er.region_support("identity", "XY1_ABC_DEF_MAIN", split)[0] is None
    res = er.adjudicate_conflict("identity", st_of(rs, split), {})
    assert not res["record"]["resolved"] and "verdict" not in res


def test_no_source_text_means_no_resolution():
    rs = [{"source": "discovery", "value": "XY1_ABC_DEF_MAIN", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_small", "value": "XY1_ABC_DEF", "legible": True, "label": "DOCUMENT NO."},
          {"source": "blind_context", "value": "XY1_ABC_DEF_MAIN", "legible": True, "label": "DOCUMENT NO.", "role": "own_identity"}]
    res = er.adjudicate_conflict("identity", st_of(rs, [], ctx_texts=[]), {})
    assert not res["record"]["resolved"], "a scan with no text / OCR: the truncation cannot be shown, both stay held"


TWO_SYSTEMS = [("text", "CLIENT DRAWING No. PQR-M-ZZ-ARC-1122\nMUNICIPALITY DRAWING No. ARC-1122\nREVISION E")]


def test_d06_shape_two_own_labelled_numbering_systems_stay_held():
    rs = [{"source": "discovery", "value": "PQR-M-ZZ-ARC-1122", "legible": True, "label": "CLIENT DRAWING No."},
          {"source": "blind_small", "value": "ARC-1122", "legible": True, "label": "MUNICIPALITY DRAWING No."},
          {"source": "blind_context", "value": "PQR-M-ZZ-ARC-1122", "legible": True, "label": "CLIENT DRAWING No.", "role": "own_identity"}]
    res = er.adjudicate_conflict("identity", st_of(rs, TWO_SYSTEMS, ctx_texts=TWO_SYSTEMS), {"other_numbers": [{"role": "other", "literal": "ARC-1122"}]})
    assert not res["record"]["resolved"] and "verdict" not in res, "the longer value containing the shorter is never a reason"
    lit = res["record"]["literals"]
    assert lit["ARC-1122"]["source_bound_anywhere"] and not lit["ARC-1122"]["role_contradiction"], "the competitor is printed and own-labelled"


def test_a_supported_deterministic_reading_that_disagrees_blocks_resolution():
    res = er.adjudicate_conflict("identity", st_of(form_readings(), FORM_TEXT + [("text", "Form 99")], det="99", ctx_texts=FORM_TEXT + [("text", "Form 99")]),
                                 FORM_DISC)
    assert not res["record"]["resolved"], "the deterministic literal is source-bound and carries no role contradiction"


def test_a_revision_conflict_needs_an_identity_established_on_the_page():
    texts = [("text", "REV C   Revision history B A")]
    rs = [{"source": "discovery", "value": "C", "legible": True, "label": "REV"},
          {"source": "blind_small", "value": "B", "legible": True, "label": "Revision history"},
          {"source": "blind_context", "value": "C", "legible": True, "label": "REV", "role": "own_revision"}]
    assert not er.adjudicate_conflict("revision", st_of(rs, texts, ctx_texts=texts), {}, identity_established=False)["record"]["resolved"]
    res = er.adjudicate_conflict("revision", st_of(rs, texts, ctx_texts=texts), {"other_numbers": [{"role": "revision_history", "literal": "B"}]},
                                 identity_established=True)
    assert res["record"]["resolved"] and res["verdict"]["value"] == "C"


def _form_doc():
    return text_page([(0.10, 0.20, "Submittal No. 42", 11), (0.40, 0.20, "Rev 00", 11), (0.10, 0.24, "Dwg. Ref. AB-12-345", 11),
                      (0.10, 0.28, "Project Code 777", 11), (0.10, 0.60, "Consultant review: A Approved  B Approved with comments", 10)])


@pytest.mark.parametrize("ca,ig,pa", [(False, False, False), (True, False, False), (True, True, False), (True, True, True)])
def test_d04_shape_through_the_reader(db_session, tmp_path, monkeypatch, ca, ig, pa):
    """L3 switch set (+CA, +IG, +PA): discovery reads the form number, the primary blind read lands on the referenced
    drawing under its reference label, the targeted read reads the form number again. CA off: the conflict is held (the
    frozen defect). CA on: the form number is validated under C2, the drawing reference kept as superseded evidence. With
    IG too (C1 revision 2): the conflict's provisional value is not guarded, so the targeted read still happens; the
    resolved value is guarded and passes (own label twice, source-bound)."""
    configure(monkeypatch, x=True, ca=ca, ig=ig, pa=pa)
    doc = _form_doc()
    page = doc[0]
    s = Stage(db_session, tmp_path, doc, f"d04{int(ca)}{int(ig)}{int(pa)}")
    answers = {("discover_page", None, "small"): discovery(page_kind="submittal_form", own_identity="42", own_identity_label="Submittal No.",
                                                           own_identity_region=norm_region(page, "Submittal No. 42"), own_revision="00",
                                                           own_revision_label="Rev", own_revision_region=norm_region(page, "Rev 00"),
                                                           other_numbers=[{"role": "referenced_drawing", "literal": "AB-12-345"}]),
               ("read_identity", "identity", "small"): value_read("AB-12-345", "Dwg. Ref."),
               ("read_revision", "revision", "small"): value_read("00", "Rev"),
               ("read_field_context", "identity", "small"): context_read("42", "Submittal No.", "own_identity", region=norm_region(page, "Submittal No. 42", pad=20))}
    ai = s.run(KeyedProvider(answers))
    ident = envelope_obs(s, ai, field="identity")[0]
    if not ca:
        assert ident["state"] == "conflict" and ident["value"] == "AB-12-345"
    else:
        assert ident["state"] == "validated" and ident["value"] == "42"
        assert ident["adjudication"]["resolved"] and [x["value"] for x in ident["superseded"]] == ["AB-12-345"]
        assert {r["value"] for r in ident["readings"]} == {"42", "AB-12-345"}, "every reading is kept on the observation"
