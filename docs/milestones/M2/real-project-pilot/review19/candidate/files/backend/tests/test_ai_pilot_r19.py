"""M2 review 19: R19-01 (a located crop never establishes absence outside what it inspected) and the ACTUAL E path --
the real locator (no whole-page shim), the real crop, coordinate-aware scripted answers and the persisted processing
path (evidence_stage -> merge -> reload -> evidence_for). No model, no network.

A coordinate-aware answer is what a reader of the ACTUAL crop could say: a field printed inside the crop is reported with
its region in the crop's 0..1000 frame; a field printed outside it is not visible and is reported empty (no region)."""
import hashlib
import io

import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.ai import evidence_reader as er
from app.models import Project, ProjectDocument, ResultCache, RoleEnum

from ._keyed_provider import KeyedProvider, failure
from .conftest import make_user

LEGEND = ["A = APPROVED", "B = APPROVED AS NOTED", "C = REVISE AND RESUBMIT"]
TB = ["PROJECT EXAMPLE TOWER", "CLIENT EXAMPLE COMPANY", "SCALE 1:100", "DRAWN AB", "CHECKED CD", "DRAWING NO X-SD-1", "REV 02"]


def _flags(monkeypatch):
    monkeypatch.setattr(er, "GUARD_ENABLED", True)
    monkeypatch.setattr(er, "TARGETED_ENABLED", True)
    monkeypatch.setattr(er, "EFFICIENT_ENABLED", True)
    monkeypatch.setattr(er, "PROMPTS", {**er.PROMPTS, "read_field_context": "read-field-context-2026-09-30.1",
                                        "discover_region": "discover-region-2026-09-30.1"})


def _font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _png(lines, size=(600, 160), font=28):
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    for i, t in enumerate(lines):
        d.text((12, 10 + i * (font + 10)), t, fill="black", font=_font(font))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def sheet(*, rotation=0, stamp=None, words_outside=None, decision_in_block=False, runs=TB):
    """An A2 drawing sheet with a text-layer title block in the displayed bottom-right corner (inserted through the
    derotation so it reads horizontally at every rotation); optionally a RASTER stamp or text words at the top-left."""
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    if rotation:
        page.set_rotation(rotation)
    W, H = page.rect.width, page.rect.height
    lines = list(runs) + (LEGEND + ["MARKED: B  CONSULTANT"] if decision_in_block else [])
    for i, t in enumerate(lines):
        p = pymupdf.Point(W * 0.78, H * 0.70 + 16 * i) * page.derotation_matrix
        page.insert_text(p, t, fontsize=8, rotate=rotation)
    if stamp:
        r = pymupdf.Rect(W * 0.06, H * 0.08, W * 0.06 + 420, H * 0.08 + 112) * page.derotation_matrix
        page.insert_image(r, stream=_png(stamp), rotate=rotation)
    if words_outside:
        p = pymupdf.Point(W * 0.06, H * 0.10) * page.derotation_matrix
        page.insert_text(p, words_outside, fontsize=10, rotate=rotation)
    return doc


def scanned_sheet():
    """A wholly scanned A2 sheet: one image, no text layer; the title block is pixels in the bottom-right."""
    img = Image.new("RGB", (1684 * 2, 1190 * 2), "white")
    d = ImageDraw.Draw(img)
    for i, t in enumerate(TB):
        d.text((int(1684 * 2 * 0.78), int(1190 * 2 * 0.70) + i * 40), t, fill="black", font=_font(30))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    page.insert_image(page.rect, stream=buf.getvalue())
    return doc


def _display_rect(page, literal):
    hits = page.search_for(literal)
    return (hits[0] * page.rotation_matrix) if hits else None


def crop_answer(page, clip, *, identity="X-SD-1", revision="02", decision=None):
    """What a reader of the actual crop could answer (regions in the CROP's 0..1000 frame)."""
    def region(literal):
        r = _display_rect(page, literal) if literal else None
        if r is None or not clip.contains(r):
            return None
        return [int((r.x0 - clip.x0) / clip.width * 1000) - 3, int((r.y0 - clip.y0) / clip.height * 1000) - 3,
                int((r.x1 - clip.x0) / clip.width * 1000) + 3, int((r.y1 - clip.y0) / clip.height * 1000) + 3]
    ri, rr = region(f"DRAWING NO {identity}" if identity else None), region(f"REV {revision}" if revision else None)
    d = decision or {}
    rd = region(d.get("anchor")) if d else None
    return {"page_kind": "drawing_sheet", "own_identity": identity if ri else "", "own_identity_label": "DRAWING NO", "own_identity_region": ri or [],
            "own_revision": revision if rr else "", "own_revision_label": "REV", "own_revision_region": rr or [],
            "decision_options_printed": LEGEND if rd else [], "decision_marked_option": d.get("marked", "") if rd else "",
            "decision_mark_type": "tick" if rd else "none", "decision_actor": "consultant" if rd else "unknown",
            "decision_region": rd or [], "other_numbers": [], "notes": ""}


def read(value):
    return {"label_text": "", "value": value, "legible": True, "other_values_in_crop": []}


def decision_read():
    return {"options_printed": LEGEND, "marked_option": "B = APPROVED AS NOTED", "mark_type": "tick", "actor": "consultant", "legible": True}


class Stage:
    """A persisted row read through the real stage entry point; every step reloads from the database."""

    def __init__(self, db, tmp_path, doc, name="sheet"):
        path = tmp_path / f"{name}.pdf"
        doc.save(path)
        user = make_user(db, f"{name}-r19@test.local", RoleEnum.admin)
        project = Project(ep_number=f"R19{name[:6]}", project_name=name, source_folder_path=str(tmp_path), created_by_id=user.id)
        db.add(project)
        db.flush()
        self.sha = hashlib.sha256(name.encode()).hexdigest()
        row = ProjectDocument(project_id=project.id, path=str(path), relative_path=f"{name}.pdf", filename=f"{name}.pdf", role="document",
                              state="fresh", sha256=self.sha, extracted={"records": [], "observations": [], "profile": "default"})
        db.add(row)
        db.commit()
        self.db, self.project, self.id, self.path = db, project, row.id, path

    def run(self, provider):
        self.db.query(ResultCache).delete()
        self.db.commit()
        row = self.db.get(ProjectDocument, self.id)
        er.evidence_stage(self.db, self.project, [(row, self.path)], provider=provider, variant="EV1", profile="default")
        self.db.commit()
        self.db.expire_all()
        return self.db.get(ProjectDocument, self.id).extracted["ai_evidence"]

    def page_fields(self, ai, n=-1):
        return ai["attempts"][n]["pages"]["1"]["fields"]

    def selected(self, ai, key):
        got = er.evidence_for(ai, sha256=self.sha, profile="default", variant="EV1")
        assert got["state"] == "current", got
        entry = got["envelope"]["pages"]["1"]["fields"].get(key)
        return entry and (entry["observations"][0].get("value"), entry["observations"][0].get("state"), entry["provenance"]["attempt"])


@pytest.fixture(autouse=True)
def _no_submittal_reader(monkeypatch):
    from app.ai import submittal_reader
    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)


def _clip(page):
    clip, route = er.locate_title_block(page, None, ocr_timeout=20.0)
    assert clip is not None and clip.get_area() < 0.5 * page.rect.get_area(), (clip, route)    # the real, partial crop
    return clip, route


# --- R19-01 ------------------------------------------------------------------------------------------------------------


def test_raster_stamp_outside_the_real_crop_is_incomplete_not_absent(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = sheet(stamp=["CONSULTANT - CODE B", "APPROVED AS NOTED"])
    page = doc[0]
    clip, route = _clip(page)
    stamp = pymupdf.Rect(page.rect.width * 0.06, page.rect.height * 0.08, page.rect.width * 0.06 + 420, page.rect.height * 0.08 + 112)
    assert not clip.intersects(stamp), "the raster stamp lies outside the located crop"
    assert "APPROVED" not in page.get_text() and len(page.get_text()) >= 80, "the text layer is silent about the (raster) decision"
    s = Stage(db_session, tmp_path, doc, "rasterstamp")
    p = KeyedProvider({("discover_region", None, "small"): crop_answer(page, clip), ("read_identity", "identity", "small"): read("X-SD-1"),
                       ("read_revision", "revision", "small"): read("02")})
    ai = s.run(p)
    f = s.page_fields(ai)
    assert f["own:decision"] == er.LOCATED_ABSENCE, "an uninspected raster stamp leaves the decision unknown, never absent"
    assert f["discovery:route"].startswith("located:labels") and ai["attempts"][-1]["pages"]["1"]["outcome"] == "partial"
    assert s.selected(ai, "own:identity")[:2] == ("X-SD-1", "validated") and s.selected(ai, "own:decision") is None
    assert "read_decision" not in [k[0] for k in p.requests], "no request is spent to settle it"


def test_control_ordinary_text_page_discovered_whole_keeps_absence(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    for i, t in enumerate(["TRANSMITTAL", "DOCUMENT NO TR-001", "REV 00", "Dear Sir, please find attached the documents listed."]):
        page.insert_text((60, 90 + 20 * i), t, fontsize=10)
    s = Stage(db_session, tmp_path, doc, "ordinary")
    ans = {**crop_answer(page, page.rect, identity="", revision=""), "own_identity": "TR-001", "own_identity_region": [80, 120, 400, 140]}
    ai = s.run(KeyedProvider({("discover_page", None, "small"): ans, ("read_identity", "identity", "small"): read("TR-001")}))
    f = s.page_fields(ai)
    assert f["discovery:route"] == "full_page" and f["own:decision"] == "absent_by_discovery" and f["own:revision"] == "absent_by_discovery"


def test_control_wholly_scanned_sheet_is_located_and_leaves_absence_unknown(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = scanned_sheet()
    page = doc[0]
    clip, route = _clip(page)
    assert route.startswith("located:") and "ocr_local" in route, route
    monkeypatch.setattr(er, "cached_ocr", lambda sha, i: "DRAWING NO X-SD-1 REV 02 PROJECT EXAMPLE")    # the processing run's cached OCR text
    s = Stage(db_session, tmp_path, doc, "scanned")
    ans = {**crop_answer(page, clip, identity="", revision=""), "own_identity": "X-SD-1",
           "own_identity_region": [int((page.rect.width * 0.77 - clip.x0) / clip.width * 1000), int((page.rect.height * 0.735 - clip.y0) / clip.height * 1000),
                                   int((page.rect.width * 0.99 - clip.x0) / clip.width * 1000), int((page.rect.height * 0.76 - clip.y0) / clip.height * 1000)]}
    ai = s.run(KeyedProvider({("discover_region", None, "small"): ans, ("read_identity", "identity", "small"): read("X-SD-1"),
                              ("read_field_context", "identity", "small"): {"value": "X-SD-1", "printed_label": "DRAWING NO", "role": "own_identity",
                                                                            "region": [0, 0, 1000, 1000], "legible": True}}))
    f = s.page_fields(ai)
    assert f["own:decision"] == er.LOCATED_ABSENCE and f["own:revision"] == er.LOCATED_ABSENCE
    obs = s.selected(ai, "own:identity")
    assert obs[0] == "X-SD-1" and obs[1] in ("validated", "candidate")


def test_control_decision_words_outside_the_crop_stay_incomplete(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = sheet(words_outside="B = APPROVED AS NOTED   CONSULTANT")
    page = doc[0]
    clip, _ = _clip(page)
    s = Stage(db_session, tmp_path, doc, "wordsout")
    ai = s.run(KeyedProvider({("discover_region", None, "small"): crop_answer(page, clip), ("read_identity", "identity", "small"): read("X-SD-1"),
                              ("read_revision", "revision", "small"): read("02")}))
    assert s.page_fields(ai)["own:decision"] == er.LOCATED_ABSENCE


def _genuine_decision(page, clip):
    return crop_answer(page, clip, decision={"anchor": "B = APPROVED AS NOTED", "marked": "B = APPROVED AS NOTED"})


def test_control_a_completed_genuine_decision_read_inside_the_crop(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = sheet(decision_in_block=True)
    page = doc[0]
    clip, _ = _clip(page)
    ans = _genuine_decision(page, clip)
    assert ans["decision_region"], "the legend is inside the actual crop"
    s = Stage(db_session, tmp_path, doc, "genuine")
    ai = s.run(KeyedProvider({("discover_region", None, "small"): ans, ("read_identity", "identity", "small"): read("X-SD-1"),
                              ("read_revision", "revision", "small"): read("02"), ("read_decision", "decision", "small"): decision_read()}))
    assert s.page_fields(ai)["own:decision"] == "completed"
    assert s.selected(ai, "own:decision")[:2] == ("ANN", "validated")


def test_control_a_failed_reread_and_a_later_crop_keep_the_good_decision(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = sheet(decision_in_block=True)
    page = doc[0]
    clip, _ = _clip(page)
    ans = _genuine_decision(page, clip)
    s = Stage(db_session, tmp_path, doc, "reread")
    s.run(KeyedProvider({("discover_region", None, "small"): ans, ("read_identity", "identity", "small"): read("X-SD-1"),
                         ("read_revision", "revision", "small"): read("02"), ("read_decision", "decision", "small"): decision_read()}))
    # a re-read whose decision request times out
    ai = s.run(KeyedProvider({("discover_region", None, "small"): ans, ("read_identity", "identity", "small"): read("X-SD-1"),
                              ("read_revision", "revision", "small"): read("02"), ("read_decision", "decision", "small"): failure("timeout")}))
    assert s.page_fields(ai)["own:decision"] == "failed:timeout"
    assert s.selected(ai, "own:decision") == ("ANN", "validated", 1), "the failed re-read replaces nothing"
    # a later located read that does not see the decision block: unknown, and the good decision is kept
    ai = s.run(KeyedProvider({("discover_region", None, "small"): crop_answer(page, clip), ("read_identity", "identity", "small"): read("X-SD-1"),
                              ("read_revision", "revision", "small"): read("02")}))
    assert s.page_fields(ai)["own:decision"] == er.LOCATED_ABSENCE
    assert s.selected(ai, "own:decision") == ("ANN", "validated", 1)


# --- the actual E path: rotation, own-field coordinates, missing ROI, timeout ---------------------------------------------


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_actual_crop_coordinates_and_support_at_every_rotation(db_session, tmp_path, monkeypatch, rotation):
    _flags(monkeypatch)
    doc = sheet(rotation=rotation)
    page = doc[0]
    clip, route = _clip(page)
    ans = crop_answer(page, clip)
    assert ans["own_identity_region"] and ans["own_revision_region"], "both own fields are inside the actual crop"
    s = Stage(db_session, tmp_path, doc, f"rot{rotation}")
    p = KeyedProvider({("discover_region", None, "small"): ans, ("read_identity", "identity", "small"): read("X-SD-1"),
                       ("read_revision", "revision", "small"): read("02")})
    ai = s.run(p)
    f = s.page_fields(ai)
    assert f["own:identity"] == f["own:revision"] == "completed" and f["own:decision"] == er.LOCATED_ABSENCE
    assert s.selected(ai, "own:identity")[:2] == ("X-SD-1", "validated") and s.selected(ai, "own:revision")[:2] == ("02", "validated")
    got = er.evidence_for(ai, sha256=s.sha, profile="default", variant="EV1")["envelope"]["pages"]["1"]["fields"]["own:identity"]["observations"][0]
    assert got["support"] == "text"
    target = _display_rect(page, "X-SD-1")
    assert pymupdf.Rect(got["region"]).intersects(target), "the mapped region is the value's place on the displayed page"


class _Images(KeyedProvider):
    def complete(self, request):
        self.sizes = getattr(self, "sizes", []) + [(request.task, [Image.open(io.BytesIO(p.png)).size for p in request.parts if hasattr(p, "png")])]
        return super().complete(request)


def test_missing_roi_gets_a_context_read_on_the_located_crop_not_the_sheet(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = sheet()
    page = doc[0]
    clip, _ = _clip(page)
    ans = {**crop_answer(page, clip), "own_identity_region": []}          # the value is named, its region is not
    s = Stage(db_session, tmp_path, doc, "noroi")
    p = _Images({("discover_region", None, "small"): ans, ("read_revision", "revision", "small"): read("02"),
                 ("read_field_context", "identity", "small"): {"value": "X-SD-1", "printed_label": "DRAWING NO", "role": "own_identity",
                                                               "region": [0, 0, 1000, 1000], "legible": True}})
    ai = s.run(p)
    f = s.page_fields(ai)
    assert f["own:identity:primary"] == "incomplete:no_region" and f["own:identity:targeted"] == "completed" and f["own:identity"] == "completed"
    w, h = dict(p.sizes)["read_field_context"][0]
    assert abs(w / h - clip.width / clip.height) < 0.05, "the context image is the located crop, not the whole sheet"
    assert s.selected(ai, "own:identity")[:2] == ("X-SD-1", "validated")


def test_discovery_and_blind_timeouts_keep_the_last_good_evidence(db_session, tmp_path, monkeypatch):
    _flags(monkeypatch)
    doc = sheet()
    page = doc[0]
    clip, _ = _clip(page)
    s = Stage(db_session, tmp_path, doc, "timeouts")
    good = {("discover_region", None, "small"): crop_answer(page, clip), ("read_identity", "identity", "small"): read("X-SD-1"),
            ("read_revision", "revision", "small"): read("02")}
    s.run(KeyedProvider(good))
    ai = s.run(KeyedProvider({("discover_region", None, "small"): failure("timeout")}))
    assert ai["attempts"][-1]["pages"]["1"]["outcome"] == "failed" and s.selected(ai, "own:identity") == ("X-SD-1", "validated", 1)
    p = KeyedProvider({**good, ("read_identity", "identity", "small"): failure("timeout")})
    ai = s.run(p)
    f = s.page_fields(ai)
    assert f["own:identity"] == "failed:timeout" and f["own:identity:targeted"] == "not_attempted:after_failure"
    assert s.selected(ai, "own:identity") == ("X-SD-1", "validated", 1) and "read_field_context" not in [k[0] for k in p.requests]


def test_the_crop_absence_does_not_supersede_a_completed_revision(db_session, tmp_path, monkeypatch):
    """A cropped read that cannot see the revision leaves the earlier completed revision selected (no absence is claimed)."""
    _flags(monkeypatch)
    doc = sheet()
    page = doc[0]
    clip, _ = _clip(page)
    s = Stage(db_session, tmp_path, doc, "cropabs")
    s.run(KeyedProvider({("discover_region", None, "small"): crop_answer(page, clip), ("read_identity", "identity", "small"): read("X-SD-1"),
                         ("read_revision", "revision", "small"): read("02")}))
    ai = s.run(KeyedProvider({("discover_region", None, "small"): crop_answer(page, clip, revision=""),
                              ("read_identity", "identity", "small"): read("X-SD-1")}))
    assert s.page_fields(ai)["own:revision"] == er.LOCATED_ABSENCE and s.selected(ai, "own:revision") == ("02", "validated", 1)
