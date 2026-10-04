"""Logs > Samples, Request Material: the email asking stores for a sample
board's samples, drafted from the Schedules of Material and checked against
them (app.services.sample_request)."""
from __future__ import annotations

import pytest

from app.ai.provider import RecordingProvider, set_provider
from app.core.config import get_settings
from app.services import sample_request as S
from tests.conftest import login

settings = get_settings()

# EP-30880's schedules, as the Schedule of Material lists them (the QA case of the feature).
FAS = """CAT. NO. | DESCRIPTION | MANUFACTURER
[E] Initiating Devices
SIGA-SD | SuperDuct | Edwards
SIGA-OSD-FCN | Intelligent Photoelectric Smoke Detector | Edwards
SIGA-HRD-FCN | Intelligent Fixed Temperature / Rate-of-Rise Heat Detector | Edwards
SIGA-OSHD-FCN | Intelligent 3D Multisensor Detector - Photoelectric, Heat | Edwards
SIGA-SB | Signature Detector Base | Edwards
SIGA-IB | Detector Base with Isolator | Edwards
SIGA-LPS | Audible (Sounder) Base | Edwards
SIGA-278 | Manual Pull Station - Double Action, 1-stage | Edwards
[F] Notification Appliances
G4SRN | Wall Speaker, Red, No Marking | Edwards
EST-S186C | Ceiling speaker, ABS fire dome (diameter 17,5 cm) | Edwards
757-3A-SS70 | 30cd Speaker/Strobe - 70V, RED. | Edwards
[G] Fire Telephone
6833-4 | Four-state Portable Telephone Handset Receptacle | Edwards
[J] Back Boxes
TP606 | 2"x4" GI Concealed Back Box Single Gange | Edwards
TP434 | 4"x4" GI Concealed Back Box Double Gange | Edwards
27193-11 | Surface Mount Box - Indoor, RED, 1-gang | Edwards
27193-21 | Surface Mount Box - Indoor, RED, 2-gang | Edwards
757A-WB | Weatherproof Box, Cast - RED | Edwards"""
ELS = """CAT. NO. | DESCRIPTION | MANUFACTURER
[B] Emergency Light
SL2-65D3D-CGL-M | Surface Mounted Emergency Light | MENVIER
RT2RHEO200CGL3HIPM | RTECH MR HEO CGL+ 200 MNM 3H IP65 M | MENVIER
[C] Exit Light
SL2-42D3D-CGL-M+SL23I | Wall Mounted Exit, 20 metre viewing distance, IP42 | MENVIER
SL2-42D3D-CGL-M +SL2PPLR+SL2RB | Exit Directional, Corridor Recessed, 20 metre viewing distance | MENVIER"""

EXPECTED = """Dear Jaffar,

Kindly arrange samples as per below.

Fire Alarm System
- Smoke detector: SIGA-OSD-FCN + Sounder base SIGA-LPS
- Heat detector: SIGA-HRD-FCN + Standard base SIGA-SB
- Multi-sensor: SIGA-OSHD-FCN + Isolator base SIGA-IB
- Manual call point: SIGA-278 + back box TP606
- Wall mounted speaker: G4SRN + back box TP434
- Ceiling speaker: EST-S186C
- Fire telephone jack: 6833-4 + back box TP606
- Weatherproof speaker: 757-3A-SS70 + back box 757A-WB (please confirm)
- MDF board

Emergency Lighting (EML)
- Rounded emergency light: RT2RHEO200CGL3HIPM
- Surface emergency light: SL2-42D3D-CGL-M
- Directional emergency light: SL2-42D3D-CGL-M +SL2PPLR+SL2RB
- MDF board"""


def _parts(text: str) -> set[str]:
    return {S._norm(line.split(" | ")[0]) for line in text.splitlines()[1:] if " | " in line}


@pytest.fixture()
def schedules(monkeypatch):
    texts = {S.FAS: FAS, S.ELS: ELS}
    monkeypatch.setattr(S, "schedule_text", lambda project, code: (texts[code], _parts(texts[code])))
    monkeypatch.setattr(S.system_rules, "project_codes", lambda project: ["FAS", "ELS", "FRC"])


def _reply(body: str) -> dict:
    return {"email": f"To: someone@else.example\nSubject: EP-30880 Binghatti Titania\n\n{body}"}


def test_the_qa_case_drafts_the_expected_email(client, db_session, schedules):
    from app.models import Project

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "30880", "project_name": "BINGHATTI TITANIA (3B + G+ 4P + 32 RF + MF+R)",
                                         "design_sheets": []}).json()["id"]
    # the model puts the confirm tag mid-line (as the real one did): the platform moves it to the end
    reply = EXPECTED.replace("757-3A-SS70 + back box 757A-WB (please confirm)", "757-3A-SS70 (please confirm) + back box 757A-WB")
    provider = RecordingProvider([_reply(reply)])
    d = S.draft(db_session, db_session.get(Project, pid), provider)
    assert (d.to, d.subject, d.body) == ("jaffer.ali@al-majid.com", "EP-30880 Binghatti Titania", EXPECTED)
    assert d.to_confirm == ["Weatherproof speaker: 757-3A-SS70 + back box 757A-WB (please confirm)"]
    assert d.not_in_schedule == []
    # the model is given the prompt as written, and the project's two schedules
    request = provider.requests[0]
    assert request.system.startswith(S.SYSTEM_PROMPT) and "Never assume a brand" in request.system
    assert {p.label: p.text for p in request.parts}["FAS_SCHEDULE"] == FAS
    assert {p.label: p.text for p in request.parts}["PROJECT_NAME"] == "BINGHATTI TITANIA (3B + G+ 4P + 32 RF + MF+R)"


def test_a_part_number_the_schedules_do_not_have_is_flagged(client, db_session, schedules):
    from app.models import Project

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "30881", "project_name": "Tower", "design_sheets": []}).json()["id"]
    invented = EXPECTED.replace("SIGA-278", "SIGA-270").replace("G4SRN", "G4SRN / G1ARN (multiple options – please confirm)")
    d = S.draft(db_session, db_session.get(Project, pid), RecordingProvider([_reply(invented)]))
    assert d.not_in_schedule == ["Manual call point: SIGA-270", "Wall mounted speaker: G1ARN"]
    assert "Wall mounted speaker: G4SRN / G1ARN + back box TP434 (multiple options – please confirm)" in d.to_confirm


def test_the_request_is_refused_without_ai_and_for_a_viewer(client, db_session):
    from app.models import RoleEnum
    from tests.conftest import make_user

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "30882", "project_name": "Tower", "design_sheets": []}).json()["id"]
    set_provider(None)
    refused = client.post(f"/projects/{pid}/samples/request-material")
    assert refused.status_code == 422 and "AI" in refused.json()["detail"]
    make_user(db_session, "viewer@example.com", RoleEnum.viewer)
    client.post("/auth/logout")
    assert login(client, "viewer@example.com", "Password123!").status_code == 200
    assert client.post(f"/projects/{pid}/samples/request-material").status_code == 403
