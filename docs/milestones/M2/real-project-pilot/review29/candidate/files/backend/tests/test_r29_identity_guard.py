"""Review 29 C1 -- the identity role guard (IG). Structural classes from the literal, the readings' printed labels, the
field region's geometry and discovery's roles; positive controls for short / unusual real identifiers; the D03 shape end
to end (a datasheet whose legible section heading was validated as its identity). No model, no network."""
import pytest

from app.ai import evidence_reader as er

from ._keyed_provider import KeyedProvider
from ._r29 import configure, context_read, discovery, envelope_obs, no_submittal_reader, norm_region, text_page, value_read  # noqa: F401
from .test_ai_pilot_r19 import Stage

POSITIVE = ["17", "3561", "0284", "101", "A1", "X", "FLS-107", "SK-01", "E-101", "EP-23091/AS/MS-EM /101", "TES/1343/NTH-MID-3B/SD/TEL-04",
            "BH2031_DIB_AMB_ID_MAIN", "DCH-M-BSB-DWG-ZZ-ARC-41034", "MEC/SD/PR56/0284", "ID-01 / ED-01", "DJ-295-P-EN-SFD-01-ASY-0001-00",
            "MEC/SD/PR56/0284 Rev. 00", "QQ-77-01"]
NEGATIVE = {"2.4 Accessories": "structural_heading", "1.1 Summary": "structural_heading", "PART 1 GENERAL": "structural_heading",
            "3.2.1 Installation": "structural_heading", "Page 2 of 52": "structural_heading", "Detector and Base": "structural_heading",
            "ELECTRICAL": "generic_label", "GENERAL NOTES": "generic_label", "FIRE ALARM LAYOUT": "generic_label",
            "Rev. 0": "revision_token", "REV 01": "revision_token", "R1": "revision_token"}


@pytest.mark.parametrize("value", POSITIVE)
def test_positive_controls_are_not_structural(value):
    assert er.identity_structure(value, []) is None


def test_a_section_number_read_under_its_label_is_not_a_heading_but_the_section_title_is():
    assert er.identity_structure("SECTION 28 20 00", ["SECTION"]) is None
    assert er.identity_structure("28 20 00", ["SECTION"]) is None
    assert er.identity_structure("Section 28 20 00 Video Surveillance System", ["Section"]) == "structural_heading"
    assert er.identity_structure("Section 28 20 00 Video Surveillance System", []) == "structural_heading"


@pytest.mark.parametrize("value,cls", sorted(NEGATIVE.items()))
def test_negative_controls_are_classified(value, cls):
    assert er.identity_structure(value, []) == cls


def _a4(lines):
    return text_page(lines)[0]


def test_running_footer_on_an_a4_page_is_guarded_but_not_on_a_drawing_sheet():
    page = _a4([(0.1, 0.96, "CODE-ABC-9", 8), (0.1, 0.30, "Document No. CODE-ABC-9", 10)])
    footer = tuple(page.search_for("CODE-ABC-9")[0])
    readings = [{"source": "discovery", "value": "CODE-ABC-9", "legible": True, "label": ""}]
    g = er.identity_role_guard("CODE-ABC-9", readings, {}, [("text", "CODE-ABC-9")], page=page, region=footer)
    assert g and g["guard"] == "identity_role:running_header_footer"
    sheet = text_page([(0.80, 0.96, "QQ-77-01", 8)], width=2384, height=1684)[0]
    box = tuple(sheet.search_for("QQ-77-01")[0])
    assert er.identity_role_guard("QQ-77-01", readings, {}, [("text", "QQ-77-01")], page=sheet, region=box) is None, \
        "a drawing sheet's title block sits at the bottom edge: no footer class there"


def test_a_form_number_in_the_top_band_is_lifted_by_two_own_labels_and_source_text():
    page = _a4([(0.1, 0.04, "DOCUMENT NO. FRM-0042", 9)])
    region = tuple(page.search_for("FRM-0042")[0])
    texts = [("text", "DOCUMENT NO. FRM-0042")]
    one = [{"source": "discovery", "value": "FRM-0042", "legible": True, "label": "DOCUMENT NO."}]
    assert er.identity_role_guard("FRM-0042", one, {}, texts, page=page, region=region)["guard"] == "identity_role:running_header_footer"
    two = one + [{"source": "blind_small", "value": "FRM-0042", "legible": True, "label": "DOCUMENT NO."}]
    assert er.identity_role_guard("FRM-0042", two, {}, texts, page=page, region=region) is None
    assert er.identity_role_guard("FRM-0042", two, {}, [], page=page, region=region) is not None, "no source text: no lift"


def test_reference_role_from_a_reference_label_or_discovery_role_or_targeted_role():
    texts = [("text", "Dwg. Ref. AB-12-345")]
    by_label = [{"source": "blind_small", "value": "AB-12-345", "legible": True, "label": "Dwg. Ref."}]
    assert er.identity_role_guard("AB-12-345", by_label, {}, texts)["guard"] == "identity_role:reference_role"
    by_discovery = [{"source": "blind_small", "value": "AB-12-345", "legible": True, "label": ""}]
    disc = {"other_numbers": [{"role": "referenced_drawing", "literal": "AB-12-345"}]}
    assert er.identity_role_guard("AB-12-345", by_discovery, disc, texts)["guard"] == "identity_role:reference_role"
    by_target = [{"source": "blind_context", "value": "AB-12-345", "legible": True, "label": "", "role": "referenced_identity"}]
    assert er.identity_role_guard("AB-12-345", by_target, {}, texts)["guard"] == "identity_role:reference_role"
    own = [{"source": "blind_small", "value": "AB-12-345", "legible": True, "label": "Drawing No."},
           {"source": "discovery", "value": "AB-12-345", "legible": True, "label": "Drawing No."}]
    assert er.identity_role_guard("AB-12-345", own, {}, texts) is None


def test_a_heading_is_never_lifted_by_a_model_role_claim():
    texts = [("text", "2.4 Accessories")]
    claims = [{"source": "discovery", "value": "2.4 Accessories", "legible": True, "label": ""},
              {"source": "blind_context", "value": "2.4 Accessories", "legible": True, "label": "", "role": "own_identity"}]
    assert er.identity_role_guard("2.4 Accessories", claims, {}, texts)["guard"] == "identity_role:structural_heading"


def test_a_bare_revision_token_is_never_lifted():
    texts = [("text", "DRAWING NO. REV 01")]
    rs = [{"source": s, "value": "REV 01", "legible": True, "label": "DRAWING NO."} for s in ("discovery", "blind_small")]
    assert er.identity_role_guard("REV 01", rs, {}, texts)["guard"] == "identity_role:revision_token"


def test_guard_off_is_validate_value_itself(monkeypatch):
    monkeypatch.setattr(er, "IDGUARD_ENABLED", False)
    readings = [{"source": "discovery", "value": "2.4 Accessories", "legible": True}, {"source": "blind_small", "value": "2.4 Accessories", "legible": True}]
    texts = [("text", "2.4 Accessories")]
    assert er._value_verdict("identity", readings, texts, None) == er.validate_value("identity", readings, texts, None)
    monkeypatch.setattr(er, "IDGUARD_ENABLED", True)
    v = er._value_verdict("identity", readings, texts, None)
    assert v["state"] == "candidate" and v["guard"] == "identity_role:structural_heading" and v["value"] == "2.4 Accessories"


@pytest.fixture(autouse=True)
def _ready(no_submittal_reader):
    yield


def _datasheet():
    return text_page([(0.40, 0.10, "2.4 Accessories", 14), (0.1, 0.30, "CAP320 addressable sensor", 10),
                      (0.1, 0.35, "CAPT340 sensor", 10), (0.1, 0.96, "SGTEXT February 2015", 7)])


@pytest.mark.parametrize("ig", [False, True])
def test_d03_shape_heading_on_a_datasheet_is_held_with_its_region_and_never_read_again(db_session, tmp_path, monkeypatch, ig):
    """Whole-page discovery reports a section heading as the page's identity; the primary blind read is illegible; L3's
    targeted read then claims the heading's role. IG off reproduces the defect (validated); IG on holds it before any
    targeted read, keeps its value and region, and leaves the page with no established identity."""
    configure(monkeypatch, x=True, ig=ig)
    doc = _datasheet()
    page = doc[0]
    s = Stage(db_session, tmp_path, doc, f"d03{int(ig)}")
    answers = {("discover_page", None, "small"): discovery(page_kind="datasheet", own_identity="2.4 Accessories", own_identity_label="",
                                                           own_identity_region=norm_region(page, "2.4 Accessories"),
                                                           other_numbers=[{"role": "listed_item", "literal": "CAP320"}]),
               ("read_identity", "identity", "small"): value_read("", "", legible=False),
               ("read_field_context", "identity", "small"): context_read("2.4 Accessories", "", "own_identity", region=(0, 0, 1000, 1000))}
    p = KeyedProvider(answers)
    ai = s.run(p)
    obs = envelope_obs(s, ai, field="identity")
    assert len(obs) == 1 and obs[0]["value"] == "2.4 Accessories" and obs[0]["region"]
    if not ig:
        assert obs[0]["state"] == "validated", "the frozen defect reproduces with IG off"
        assert ("read_field_context", "identity", "small") in p.requests
    else:
        assert obs[0]["state"] == "candidate" and "identity role guard" in " ".join(obs[0]["reasons"])
        assert ("read_field_context", "identity", "small") not in p.requests, "a guarded identity gets no targeted read"
        assert s.page_fields(ai).get("own:identity:targeted") is None


def test_c1_revision_2_a_conflict_is_not_guarded_and_keeps_its_readings(monkeypatch):
    monkeypatch.setattr(er, "IDGUARD_ENABLED", True)
    readings = [{"source": "discovery", "value": "42", "legible": True, "label": "Submittal No."},
                {"source": "blind_small", "value": "AB-12-345", "legible": True, "label": "Dwg. Ref."}]
    v = er._value_verdict("identity", readings, [("text", "Submittal No. 42 Dwg. Ref. AB-12-345")], None)
    assert v["state"] == "conflict" and "guard" not in v, "a held conflict keeps its targeted read; the final verdict is guarded"
