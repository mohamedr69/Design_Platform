"""The Drawings Assistant: answers from the project's memory, proposes changes checked against the
records, and writes nothing itself (app/services/drawings_chat.py, the drawings router)."""
import json

import pytest

from app.ai import provider as provider_module
from app.ai.provider import RecordingProvider
from app.core.config import get_settings
from app.models import DrawingIssue, Project, ProjectShopDrawing, ShopDrawingCandidate, ShopDrawingRevision
from app.services import drawings_chat

from .conftest import login

settings = get_settings()


@pytest.fixture()
def ai_on(monkeypatch):
    monkeypatch.setattr(settings, "ai_enabled", True)
    yield
    monkeypatch.setattr(settings, "ai_enabled", False)


@pytest.fixture()
def recording():
    provider = RecordingProvider()
    provider_module.set_provider(provider)
    yield provider
    provider_module.set_provider(None)


def _project_with_a_drawing(client, db_session) -> dict:
    """A project with one fire alarm drawing: R0 not approved, an R1 found on
    the drive that nothing proves was submitted, and the review item for it."""
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    project_id = client.post("/projects", json={"ep_number": "91077", "project_name": "Assistant Tower",
                                                "design_sheets": []}).json()["id"]
    drawing = ProjectShopDrawing(project_id=project_id, system_code="FAS", drawing_reference="EP-SDW-FA-002",
                                 floor_keys=["L02"], floor_label="2ND FLOOR")
    db_session.add(drawing)
    db_session.flush()
    db_session.add(ShopDrawingRevision(shop_drawing_id=drawing.id, revision="R0", number=0, status="not_approved",
                                       submitted=True, reply_text="Relocate the sounders"))
    candidate = ShopDrawingCandidate(project_id=project_id, shop_drawing_id=drawing.id, revision="R1",
                                     file_sha256="a" * 64, candidate_status="available", path="SD/FA/R1.pdf")
    db_session.add(candidate)
    db_session.flush()
    issue = DrawingIssue(project_id=project_id, system_code="FAS", shop_drawing_id=drawing.id, floor_key="L02",
                         key=f"revision_candidate:{drawing.id}:R1", kind="revision_candidate", severity="info",
                         source="system", text="R1 found on the drive; nothing proves it was submitted",
                         detail={"candidate_id": candidate.id, "revision": "R1"})
    db_session.add(issue)
    db_session.commit()
    return {"project": project_id, "drawing": drawing.id, "candidate": candidate.id, "issue": issue.id}


def _answer(reply: str, actions: list[dict] | None = None, needs_engineer: bool = False) -> dict:
    blank = {"drawing_id": None, "drawing_reference": None, "revision": None, "status": None, "note": None,
             "candidate_id": None, "issue_id": None, "resolution": None, "remarks": None, "floor_keys": None,
             "alias_key": None, "canonical_key": None, "reason": ""}
    return {"reply": reply, "needs_engineer": needs_engineer, "actions": [{**blank, **a} for a in actions or []]}


def test_with_ai_off_the_assistant_says_so_and_answers_nothing(client, db_session):
    ids = _project_with_a_drawing(client, db_session)
    status = client.get(f"/projects/{ids['project']}/drawings/assistant").json()
    assert status["available"] is False and "AI_ENABLED" in status["reason"]
    asked = client.post(f"/projects/{ids['project']}/drawings/assistant", json={"message": "What is open?"})
    assert asked.status_code == 503 and "AI_ENABLED" in asked.json()["detail"]


def test_the_assistants_own_switch_turns_it_on_while_the_platforms_stays_off(client, db_session, monkeypatch, recording):
    """The live installation runs AI_ENABLED=false with each workflow's switch on: the assistant has one too."""
    ids = _project_with_a_drawing(client, db_session)
    monkeypatch.setattr(settings, "drawings_chat_ai_enabled", True)
    assert settings.ai_enabled is False
    status = client.get(f"/projects/{ids['project']}/drawings/assistant").json()
    assert status["available"] is True
    recording.answers.append(_answer("Nothing is approved yet."))
    asked = client.post(f"/projects/{ids['project']}/drawings/assistant", json={"message": "What is approved?"})
    assert asked.status_code == 200 and asked.json()["reply"] == "Nothing is approved yet." and recording.calls == 1
    monkeypatch.setattr(settings, "drawings_chat_ai_enabled", False)
    assert client.get(f"/projects/{ids['project']}/drawings/assistant").json()["available"] is False


def test_a_project_whose_policy_blocks_ai_gets_no_assistant(client, db_session, ai_on, recording):
    ids = _project_with_a_drawing(client, db_session)
    db_session.get(Project, ids["project"]).ai_policy = "blocked"
    db_session.commit()
    status = client.get(f"/projects/{ids['project']}/drawings/assistant").json()
    assert status["available"] is False and "switched off for this project" in status["reason"]
    asked = client.post(f"/projects/{ids['project']}/drawings/assistant", json={"message": "What is open?"})
    assert asked.status_code == 503
    assert recording.calls == 0


def test_the_memory_is_what_the_page_shows(client, db_session):
    ids = _project_with_a_drawing(client, db_session)
    project = db_session.get(Project, ids["project"])
    mem = drawings_chat.memory(db_session, project, "FAS")
    assert mem["project"]["ep_number"] == "EP-91077" and mem["project"]["name"] == "Assistant Tower"
    (row,) = mem["system"]["rows"]
    assert row["drawing_id"] == ids["drawing"] and row["drawing_reference"] == "EP-SDW-FA-002"
    assert row["revisions"]["R0"]["status"] == "not_approved"
    assert row["revisions"]["R1"]["detected_file"]["candidate_id"] == ids["candidate"]
    assert row["candidates"] == [{"candidate_id": ids["candidate"], "revision": "R1"}]
    (issue,) = mem["issues"]
    assert issue["issue_id"] == ids["issue"] and issue["candidate_id"] == ids["candidate"]
    assert "approved" in mem["vocabulary"]["official_statuses"]
    assert set(mem["vocabulary"]["actions"]) == set(drawings_chat.KINDS)


def test_the_assistant_answers_from_the_memory_and_proposes_only_what_the_records_allow(client, db_session, ai_on,
                                                                                         recording):
    ids = _project_with_a_drawing(client, db_session)
    recording.answers.append(_answer("R0 of EP-SDW-FA-002 was not approved; I propose the changes you asked for.", [
        {"kind": "set_revision_status", "drawing_reference": "ep-sdw-fa-002", "revision": "R0", "status": "approved_as_noted",
         "note": "the consultant's letter", "reason": "you said the reply was approved as noted"},
        {"kind": "confirm_revision", "candidate_id": ids["candidate"], "reason": "the transmittal carried R1"},
        {"kind": "resolve_issue", "issue_id": ids["issue"], "resolution": "R1 confirmed"},
        # Refused by the records: not a drawing of this project, not a status, not an open candidate.
        {"kind": "set_revision_status", "drawing_id": 9999, "revision": "R0", "status": "approved"},
        {"kind": "set_revision_status", "drawing_id": ids["drawing"], "revision": "R0", "status": "done"},
        {"kind": "ignore_revision", "candidate_id": ids["candidate"] + 50},
    ]))
    asked = client.post(f"/projects/{ids['project']}/drawings/assistant", json={
        "message": "Set R0 to approved as noted and confirm the R1 found",
        "history": [{"role": "user", "text": "hello"}, {"role": "assistant", "text": "what do you need?"}],
    })
    assert asked.status_code == 200, asked.text
    out = asked.json()
    assert out["system"] == "FAS" and out["can_apply"] is True and out["from_cache"] is False
    assert out["reply"].startswith("R0 of EP-SDW-FA-002")

    # What the model was given: the project's memory, the conversation and the message, nothing else.
    (request,) = recording.requests
    assert request.task == "drawings_chat"
    labels = [p.label for p in request.parts]
    assert labels == ["project_memory", "conversation", "engineer_message"]
    mem = json.loads(request.parts[0].text)
    assert mem["project"]["name"] == "Assistant Tower" and mem["system"]["rows"][0]["drawing_reference"] == "EP-SDW-FA-002"
    assert json.loads(request.parts[1].text) == [{"role": "engineer", "text": "hello"}, {"role": "assistant", "text": "what do you need?"}]
    assert request.parts[2].text == "Set R0 to approved as noted and confirm the R1 found"

    # The proposals the records allow are the page's own calls; the others are dropped and said.
    base = f"/projects/{ids['project']}/drawings"
    assert [(a["kind"], a["method"], a["path"]) for a in out["actions"]] == [
        ("set_revision_status", "PUT", f"{base}/sd/{ids['drawing']}/revisions/R0"),
        ("confirm_revision", "POST", f"{base}/candidates/{ids['candidate']}/confirm"),
        ("resolve_issue", "POST", f"{base}/issues/{ids['issue']}/resolve"),
    ]
    first = out["actions"][0]
    assert first["body"] == {"status": "approved_as_noted", "note": "the consultant's letter", "submitted": True}
    assert first["label"] == "Set EP-SDW-FA-002 R0 to Approved as Noted" and first["drawing_id"] == ids["drawing"]
    assert out["actions"][2]["body"] == {"resolution": "R1 confirmed"}
    assert [d["reason"] for d in out["dropped"]] == [
        "drawing 9999 is not a FAS drawing of this project",
        "'done' is not a status: one of under_review, approved, approved_as_noted, not_approved, reply_not_found",
        f"detected revision {ids['candidate'] + 50} is not open on this system",
    ]

    # Nothing was written: the proposal is the engineer's to apply.
    db_session.expire_all()
    revision = db_session.query(ShopDrawingRevision).filter_by(shop_drawing_id=ids["drawing"], revision="R0").one()
    assert revision.status == "not_approved" and revision.confirmed_by_id is None
    assert db_session.get(ShopDrawingCandidate, ids["candidate"]).candidate_status == "available"
    assert db_session.get(DrawingIssue, ids["issue"]).resolved_at is None


def test_a_proposal_applied_is_the_engineers_own_call(client, db_session, ai_on, recording):
    ids = _project_with_a_drawing(client, db_session)
    recording.answers.append(_answer("Proposed.", [
        {"kind": "set_revision_status", "drawing_id": ids["drawing"], "revision": "R0", "status": "approved", "note": "per letter"},
        {"kind": "confirm_revision", "candidate_id": ids["candidate"]},
    ]))
    out = client.post(f"/projects/{ids['project']}/drawings/assistant", json={"message": "approve R0, confirm R1"}).json()
    status_call, confirm_call = out["actions"]
    applied = client.put(status_call["path"], json=status_call["body"])
    assert applied.status_code == 200, applied.text
    assert applied.json()["revisions"]["R0"]["status"] == "approved" and applied.json()["revisions"]["R0"]["confirmed"] is True
    confirmed = client.post(confirm_call["path"], json=confirm_call["body"])
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["revisions"]["R1"]["status"] == "under_review"
    # A second confirmation of the same detected revision is refused by the endpoint, as the button's is.
    assert client.post(confirm_call["path"], json=confirm_call["body"]).status_code == 409


def test_a_system_the_project_does_not_have_is_refused(client, db_session, ai_on, recording):
    ids = _project_with_a_drawing(client, db_session)
    asked = client.post(f"/projects/{ids['project']}/drawings/assistant", json={"message": "hi", "system": "PAVA"})
    assert asked.status_code == 404 and recording.calls == 0


def test_a_model_that_fails_is_reported_not_invented(client, db_session, ai_on, recording):
    ids = _project_with_a_drawing(client, db_session)
    recording.answers.append(TimeoutError("no answer in time"))
    asked = client.post(f"/projects/{ids['project']}/drawings/assistant", json={"message": "What is open?"})
    assert asked.status_code == 502 and "could not answer" in asked.json()["detail"]


def test_the_memory_is_cut_to_fit_the_call_floors_with_nothing_to_say_first():
    rows = [{"latest_status": "approved", "candidates": [], "open_issues": 0, "floor": f"L{n}", "pad": "x" * 200}
            for n in range(20)]
    rows.append({"latest_status": "not_approved", "candidates": [], "open_issues": 1, "floor": "L99", "pad": "x" * 200})
    mem = {"system": {"rows": rows, "rows_shown": 21, "rows_total": 21}, "events": [{"text": "y" * 500}]}
    text, truncated = drawings_chat._fit(mem, 1500)
    cut = json.loads(text)
    assert truncated and cut["events"] == []
    assert [r["floor"] for r in cut["system"]["rows"]] == ["L99"] and cut["system"]["rows_shown"] == 1
    whole, kept = drawings_chat._fit(mem, 10 ** 6)
    assert not kept and len(json.loads(whole)["system"]["rows"]) == 21
