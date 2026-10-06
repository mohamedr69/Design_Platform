"""The cases the Opus review could not decide, as a PDF for the engineer: each
open item with what remains unclear, what to verify, and the pictures of the
drawing the review was shown -- kept with the run, drawn again (no model asked)
for a review made before they were kept. A scripted provider stands in for the
models: no model is called."""
from __future__ import annotations

from urllib.parse import quote

import pymupdf

from app.interfaces import findings, service
from app.models import Project, ProjectFaInterfaces
from tests.test_fa_opus_review import _lone_item, _view, _with_lone_label  # noqa: F401
from tests.test_fa_workflow import _latest, _run, unresolved_item, w  # noqa: F401  (fixture)

UNCLEAR = "the ringed label has no damper symbol within 2 m"
VERIFY = "check sheet M-07-V101 near the label for a damper"


def _undecided(request):
    return {"items": [{**unresolved_item(), "evidence_refs": ["V1", "C1"], "unclear": UNCLEAR, "engineer_action": VERIFY}]}


def _pdf(w, item=None):
    url = f"/projects/{w.pid}/fa-interfaces/review-cases.pdf" + (f"?item={quote(item, safe='')}" if item else "")
    return w.client.get(url)


def _row(w):
    w.db.expire_all()
    return w.db.query(ProjectFaInterfaces).filter(ProjectFaInterfaces.project_id == w.pid).one()


def test_the_pictures_the_review_was_shown_are_kept_with_the_run(w):
    _with_lone_label(w)
    w.models.finding = _undecided
    _run(w)
    item = _lone_item(_view(w))
    (pic,) = item["review"]["pictures"]
    assert pic["id"] == "V1" and pic["drawing"] == "VENTILATION LAYOUT.dxf" and pic["numbers"]
    folder = findings.case_folder(w.db.get(Project, w.pid), _latest(w)["run_id"])
    assert (folder / pic["file"]).read_bytes()[:4] == b"\x89PNG"


def test_all_cases_pdf_has_a_summary_and_each_case_with_its_pictures(w):
    _with_lone_label(w)
    w.models.finding = _undecided
    _run(w)
    r = _pdf(w)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert "cases to verify" in r.headers["content-disposition"]
    doc = pymupdf.open(stream=r.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    assert "Cases the Opus review could not decide" in text and "Case 1 of 1" in text
    assert UNCLEAR in " ".join(text.split()) and VERIFY in " ".join(text.split())
    assert sum(len(page.get_images()) for page in doc) == 1                    # the drawing view it was shown


def test_one_case_pdf_and_an_unknown_item(w):
    _with_lone_label(w)
    w.models.finding = _undecided
    _run(w)
    item = _lone_item(_view(w))
    r = _pdf(w, item["id"])
    assert r.status_code == 200 and "FA case" in r.headers["content-disposition"]
    doc = pymupdf.open(stream=r.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    assert "Case 1 of 1" in text and "Cases the Opus review could not decide" not in text
    assert _pdf(w, "no|such|item").status_code == 404


def test_a_case_the_review_could_not_run_on_says_so_and_still_shows_its_pictures(w):
    _with_lone_label(w)
    w.models.finding_error = "timeout"
    _run(w)
    doc = pymupdf.open(stream=_pdf(w).content, filetype="pdf")
    text = " ".join(" ".join(page.get_text() for page in doc).split())
    assert "Not reviewed by Opus (failed" in text
    assert sum(len(page.get_images()) for page in doc) == 1


def test_pictures_for_a_review_made_before_they_were_kept_are_drawn_again_without_asking_the_model(w):
    _with_lone_label(w)
    w.models.finding = _undecided
    _run(w)
    row = _row(w)
    items = {k: {kk: vv for kk, vv in v.items() if kk != "pictures"} for k, v in row.reviews["items"].items()}
    row.reviews = {**row.reviews, "items": items}                           # as a review made before 2026-10-05
    w.db.commit()
    asked = len(w.models.requests)
    project = w.db.get(Project, w.pid)
    assert findings.save_case_pictures(w.db, project) == 1
    assert len(w.models.requests) == asked                                  # no model call
    assert _lone_item(_view(w))["review"]["pictures"][0]["id"] == "V1"
    doc = pymupdf.open(stream=_pdf(w).content, filetype="pdf")
    assert sum(len(page.get_images()) for page in doc) == 1


def test_only_the_last_runs_pictures_are_kept(w):
    project = w.db.get(Project, w.pid)
    for run_id in (1, 2, 3):
        folder = findings.case_folder(project, run_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "x.png").write_bytes(b"png")
    findings.prune_cases(project, 3)
    root = findings.case_folder(project, 3).parent
    assert sorted(d.name for d in root.iterdir()) == ["run-2", "run-3"]
    assert service.cache_folder(project).is_dir()
