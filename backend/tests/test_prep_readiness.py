"""Drawings Preparation, made only when ready (6 October 2026): the drawing
goes to the draftsman only with every engineering check closed -- the review
complete and decided, each placement approved or skipped by the engineer, the
extra coverage detectors approved, nothing placed for a finding no longer
accepted -- and an engineer's change is not taken while a plan is being made.
No model is called: the agents are off."""
from __future__ import annotations

import pytest

from app.ai import provider as ai_provider
from app.ai.provider import RecordingProvider
from app.core.config import get_settings
from tests.test_drawing_prep import _devices_job, _reviewed_drawing


@pytest.fixture
def planned(client, db_session, tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ai_enabled", False)
    monkeypatch.setattr(settings, "prep_ai_enabled", False)
    ai_provider.set_provider(RecordingProvider())
    try:
        pid, did = _reviewed_drawing(client, db_session, tmp_path, "40990")
        job, view, _columns = _devices_job(client, monkeypatch, tmp_path, pid, did)
        assert job["status"] == "succeeded", job.get("error")
        yield pid, did, view
    finally:
        ai_provider.set_provider(None)


def test_proposed_placements_and_coverage_detectors_keep_the_drawing_from_the_draftsman(client, planned):
    pid, did, view = planned
    ready = view["readiness"]
    assert ready["ready"] is False
    assert any("placements the agents proposed to approve or skip" in b or "placement the agents proposed" in b
               for b in ready["blockers"])
    # the output refuses, and says why -- at the server boundary since M5 (ORCH-039): no job is queued
    # (the job itself still refuses too, tests/test_redesign_apply.py)
    from app.models import BackgroundJob
    from app.redesign import service

    refused = client.post(f"/projects/{pid}/redesign/{did}/apply/jobs")
    assert refused.status_code == 422 and "Not ready for the draftsman" in refused.json()["detail"]
    jobs = client.get(f"/projects/{pid}/redesign/{did}").json()
    assert jobs["output"]["status"] == "none"
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        assert db.query(BackgroundJob).filter(BackgroundJob.kind == service.KIND_APPLY).count() == 0
    finally:
        db.close()
    assert not any(c["drawn"] for c in view["changes"] if c["status"] == "proposed")


def test_every_change_settled_makes_the_drawing_ready_and_a_finding_dismissed_since_blocks_it(client, planned):
    pid, did, view = planned
    url = f"/projects/{pid}/redesign/{did}"
    ids = [c["id"] for c in view["changes"] if c["status"] in ("proposed", "pending")]
    after = client.patch(f"{url}/changes", json={"ids": ids, "status": "approved"}).json()
    blockers = after["readiness"]["blockers"]
    # what is left is the platform's own measurement, never an approval still missing
    assert not [b for b in blockers if "to approve or skip" in b]
    # the engineer changes their mind on a finding: its placement is no longer accepted
    review = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    accepted = next(f for f in review["findings"] if f["decision"] == "accepted")
    client.post(f"/projects/{pid}/drawing-review/{did}/decisions", json={"id": accepted["id"], "status": "dismissed",
                                                                          "note": "not needed"})
    again = client.get(url).json()["readiness"]
    assert any("no longer accepted in the review" in b for b in again["blockers"]) and not again["ready"]


def test_an_open_finding_or_an_incomplete_review_is_an_open_check(client, planned):
    pid, did, view = planned
    review = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    accepted = next(f for f in review["findings"] if f["decision"] == "accepted")
    client.post(f"/projects/{pid}/drawing-review/{did}/decisions", json={"id": accepted["id"], "status": "open"})
    ready = client.get(f"/projects/{pid}/redesign/{did}").json()["readiness"]
    assert any("still undecided" in b for b in ready["blockers"])


def test_an_engineers_change_is_refused_while_a_plan_is_being_made(client, db_session, planned):
    from app.models import BackgroundJob
    from app.redesign import service

    pid, did, view = planned
    job = BackgroundJob(kind=service.KIND_PLAN, project_id=pid, status="running", dedup_key=f"{service.KIND_PLAN}:{pid}:{did}",
                        params={"drawing_id": did})
    db_session.add(job)
    db_session.commit()
    change = next(c for c in view["changes"])
    refused = client.patch(f"/projects/{pid}/redesign/{did}/changes/{change['id']}", json={"status": "approved"})
    assert refused.status_code == 409
    refused = client.patch(f"/projects/{pid}/redesign/{did}/changes", json={"ids": [change["id"]], "status": "skipped"})
    assert refused.status_code == 409
    job.status = "succeeded"
    db_session.commit()
    assert client.patch(f"/projects/{pid}/redesign/{did}/changes/{change['id']}",
                        json={"status": "approved"}).status_code == 200
