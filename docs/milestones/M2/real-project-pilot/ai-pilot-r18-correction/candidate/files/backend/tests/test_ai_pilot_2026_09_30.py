"""AI accuracy pilot (2026-09-30), isolated candidate: G (bare revision token guard) and T (targeted independent
context read + rotation-correct / local-OCR region support). Scripted provider only; synthetic pages.
With both flags off the reader behaves as accepted (the existing modules run unchanged in that mode)."""
import io

import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.ai import evidence_reader as er
from app.ai.budget import open_budget
from app.ai.provider import RecordingProvider

REGION = [760, 900, 900, 950]


def blind(value, source="blind_small"):
    return {"source": source, "value": value, "legible": True}


def _page(text="Drawing No X-SD-1", rotation=0):
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    page.insert_text((1300, 1100), text, fontsize=9)
    if rotation:
        page.set_rotation(rotation)
    return doc, page


def _image_page(text="Drawing No ABC-123"):
    """An image-only (scanned) page: the text is pixels, there is no text layer."""
    img = Image.new("RGB", (1684, 1190), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        font = ImageFont.load_default()
    d.text((1130, 1045), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    page.insert_image(page.rect, stream=buf.getvalue())
    return doc, page


def _run(db, provider, variant="EV1"):
    return er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant=variant, fresh=True)


def _discover(identity="", revision="", region=REGION):
    return {"page_kind": "drawing_sheet", "own_identity": identity, "own_identity_label": "", "own_identity_region": region if identity else [],
            "own_revision": revision, "own_revision_label": "", "own_revision_region": region if revision else [],
            "decision_options_printed": [], "decision_marked_option": "", "decision_mark_type": "none", "decision_actor": "unknown",
            "decision_region": [], "other_numbers": [], "notes": ""}


def _read(value):
    return {"label_text": "", "value": value, "legible": True, "other_values_in_crop": []}


def _ctx(value, role="own_identity", region=(300, 300, 700, 700), legible=True):
    return {"value": value, "printed_label": "Drawing No", "role": role, "region": list(region), "legible": legible}


def _own(out, field="identity"):
    return next(o for o in out["_observations"] if o["field"] == field and o["component"] == "own")


# --- G -------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("value, bare", [("Rev.0", True), ("REV 01", True), ("Rev A", True), ("R1", True), ("rev-2", True),
                                         ("EP-23091 R1", False), ("25H-S202-NCC-SD-MEP-ELE-FA-003-R3", False), ("REVIEW-001", False),
                                         ("R1029-07-W&A-DWG-TYP-GRO-INT-9011-01", False), ("FAS-09", False), ("3105", False), ("P06/TRANS/R1", False)])
def test_bare_revision_token_is_the_whole_value_only(value, bare):
    assert er.bare_revision_token(value) is bare


def test_guard_holds_rev0_as_identity_and_leaves_real_identifiers(monkeypatch):
    texts = [("text", "Submittal No.: Rev.0  Drawing No FAS-09 EP-23091 R1")]
    monkeypatch.setattr(er, "GUARD_ENABLED", False)
    assert er.validate_value("identity", [blind("Rev.0")], texts, None)["state"] == "validated"        # accepted behaviour
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    v = er.validate_value("identity", [blind("Rev.0")], texts, None)
    assert v["state"] == "candidate" and v["guard"] == "bare_revision_token"
    for real in ("FAS-09", "EP-23091 R1"):
        assert er.validate_value("identity", [blind(real)], texts, None)["state"] == "validated"
    assert er.validate_value("revision", [blind("Rev.0")], [("text", "Rev.0")], None)["state"] == "validated"   # revisions untouched


def test_guarded_identity_is_raw_revision_evidence_and_never_a_target(db_session, monkeypatch):
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    doc, page = _page("Submittal No.: Rev.0")
    provider = RecordingProvider([_discover("Rev.0", "Rev.0"), _read("Rev.0"), _read("Rev.0")])
    out = er._read_page(_run(db_session, provider), page, sha256="a" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    ident = _own(out)
    assert ident["state"] == "candidate" and "bare revision token" in " ".join(ident["reasons"])
    rev = _own(out, "revision")
    assert rev.get("target") in (None, "")                                   # no invented target
    tok = [o for o in out["_observations"] if o["component"] == "revtok"]
    assert tok and tok[0]["state"] == "observed_reference" and tok[0]["field"] == "revision"


# --- T: region support ------------------------------------------------------------------------------------------------
def test_rotated_page_region_text_is_clipped_in_unrotated_coordinates():
    doc, page = _page("Drawing No X-SD-1", rotation=270)
    words = page.get_text("words")
    w = next(w for w in words if w[4] == "X-SD-1")
    display = pymupdf.Rect(w[:4]) * page.rotation_matrix                  # where the value appears on the rotated page
    region = (display.x0, display.y0, display.x1, display.y1)
    assert not any("X-SD-1" in t for _s, t in er.region_texts(page, region, []))    # accepted: reads the wrong area
    assert any("X-SD-1" in t for _s, t in er.region_texts_v2(page, region, []))


def test_scanned_region_gets_local_ocr_support():
    doc, page = _image_page("Drawing No ABC-123")
    region = (1120, 1035, 1600, 1100)
    assert er.region_texts(page, region, []) == []
    texts = er.region_texts_v2(page, region, [])
    assert texts and texts[0][0] == "ocr_local" and "ABC-123" in texts[0][1]


# --- T: the targeted read ---------------------------------------------------------------------------------------------
def _t(monkeypatch):
    """T as the environment flags set it at import: guard + targeted + the targeted prompt's identity."""
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    monkeypatch.setattr(er, "TARGETED_ENABLED", True)
    # these T tests script discovery regions in the whole page's frame: E (located discovery) is pinned off here and
    # tested on its own in test_ai_pilot_r18 (M2 review 18)
    monkeypatch.setattr(er, "EFFICIENT_ENABLED", False, raising=False)
    monkeypatch.setattr(er, "PROMPTS", {**er.PROMPTS, "read_field_context": "read-field-context-2026-09-30.1"})


BOX = (int(1120 / 1684 * 1000), int(1035 / 1190 * 1000), int(1600 / 1684 * 1000), int(1100 / 1190 * 1000))


def test_scan_with_agreeing_reads_is_supported_by_local_ocr_without_a_targeted_read(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=list(BOX)), _read("ABC-123")])
    out = er._read_page(_run(db_session, provider), page, sha256="b" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    ident = _own(out)
    assert ident["state"] == "validated" and ident["support"] == "ocr_local"
    assert [r["source"] for r in ident["readings"]] == ["discovery", "blind_small"]
    assert not any(r.task == "read_field_context" for r in provider.requests)


def test_targeted_request_is_blind_to_the_proposed_value(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=[]), _ctx("ABC-123", region=BOX)])
    er._read_page(_run(db_session, provider), page, sha256="c" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    targeted = [r for r in provider.requests if r.task == "read_field_context"]
    assert len(targeted) == 1
    assert all("ABC-123" not in getattr(p, "text", "") for p in targeted[0].parts)


def test_targeted_read_with_another_role_stays_held(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=[]), _ctx("ABC-123", role="referenced_identity", region=BOX)])
    out = er._read_page(_run(db_session, provider), page, sha256="d" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    ident = _own(out)
    # successor (M2 review 18): the wrong-role reading is kept on the observation, excluded from validation, and
    # never completes the field (e5a0a94 appended it to the readings and downgraded a validation afterwards)
    assert ident["state"] == "candidate" and ident["targeted"] == "unusable:wrong_role" and ident["read"] != "completed"
    kept = [r for r in ident["readings"] if r["source"] == "blind_context"]
    assert kept and "referenced_identity" in kept[0]["excluded"]


def test_targeted_disagreement_is_a_conflict_not_a_choice(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=[]), _ctx("ABC-128", region=BOX)])
    out = er._read_page(_run(db_session, provider), page, sha256="e" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    assert _own(out)["state"] == "conflict"


def test_no_region_discovery_gets_a_bounded_page_context_read(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=[]), _ctx("ABC-123", region=BOX)])
    out = er._read_page(_run(db_session, provider), page, sha256="f" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    ident = _own(out)
    assert ident["state"] == "validated" and ident["support"] == "ocr_local" and out["_fields"]["own:identity"] == er.COMPLETED


def test_a_failed_targeted_read_keeps_the_prior_evidence(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=[]), RuntimeError("scripted transport failure")])
    out = er._read_page(_run(db_session, provider), page, sha256="1" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    ident = _own(out)
    assert ident["state"] == "candidate" and ident["value"] == "ABC-123"
    assert out["_requests"]["own:identity:targeted"].startswith("failed")


def test_targeted_reads_count_against_the_document_budget(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _image_page("Drawing No ABC-123")
    provider = RecordingProvider([_discover("ABC-123", region=[])])
    run = _run(db_session, provider)
    run.budget.calls = run.budget.limits.max_calls_per_document - 1        # room for discovery only
    out = er._read_page(run, page, sha256="2" * 64, number=1, facts=er.PageFacts(1, "", [], []), reason="probe")
    assert provider.calls == 1 and out["_requests"]["own:identity:targeted"] == "budget"
    assert _own(out)["state"] == "candidate"


def test_no_targeted_read_when_already_validated(db_session, monkeypatch):
    _t(monkeypatch)
    doc, page = _page("Drawing No X-SD-1")
    provider = RecordingProvider([_discover("X-SD-1"), _read("X-SD-1")])
    out = er._read_page(_run(db_session, provider), page, sha256="3" * 64, number=1, facts=er.PageFacts(1, page.get_text(), [], []), reason="probe")
    assert _own(out)["state"] == "validated" and not any(r.task == "read_field_context" for r in provider.requests)
