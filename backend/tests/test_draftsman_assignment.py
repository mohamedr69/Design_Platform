"""Drawings > Assign Draftsman: the ten items, each ready, not ready or
skipped; assigning only once none is left not ready; the email an Outlook
draft to the draftsman; every assignment logged."""

import email

from app.core.config import get_settings

from .conftest import login

settings = get_settings()


def _project(client) -> int:
    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    return client.post("/projects", json={"ep_number": "40960", "project_name": "Tower", "design_sheets": []}).json()["id"]


def test_the_project_is_assigned_once_every_item_is_ready_or_skipped(client):
    pid = _project(client)
    url = f"/projects/{pid}/draftsman"
    view = client.get(url).json()
    assert [i["name"] for i in view["items"]][:3] == ["Fire Alarm Interface Schedule", "Drawings Review Instructions",
                                                       "System Legend"]
    assert len(view["items"]) == 10 and not view["ready"]
    assert view["draftsman"] == {"name": "Syed Siraj", "email": "syed.siraj@AL-MAJID.com"}
    # nothing is read or reviewed on a new project: every item is not ready, and says why
    assert all(i["state"] == "missing" and i["reason"] for i in view["items"])

    refused = client.post(f"{url}/assign", json={"name": "Syed Siraj", "email": "syed.siraj@AL-MAJID.com"})
    assert refused.status_code == 409 and "Not ready" in refused.json()["detail"]

    # the platform's own checks cannot be marked ready by hand: skipped instead
    assert client.put(f"{url}/items/interfaces", json={"action": "ready"}).status_code == 422
    for item in view["items"]:
        action = "ready" if item["manual"] else "skip"
        view = client.put(f"{url}/items/{item['key']}", json={"action": action}).json()
    assert view["ready"]
    assert {i["key"]: i["state"] for i in view["items"]}["legend"] == "ready"

    sent = client.post(f"{url}/assign", json={"name": "Syed Siraj", "email": "syed.siraj@AL-MAJID.com"})
    assert sent.status_code == 200 and sent.headers["content-type"].startswith("message/rfc822")
    message = email.message_from_bytes(sent.content)
    assert message["X-Unsent"] == "1" and "syed.siraj@AL-MAJID.com" in message["To"]
    assert message["Subject"].startswith("EP-40960 Tower")
    body = message.get_payload(decode=True).decode() if not message.is_multipart() else \
        next(p for p in message.walk() if p.get_content_type() == "text/plain").get_payload(decode=True).decode()
    assert body.startswith("Dear Syed,") and "Drawings received log:" in body
    assert "1. Fire Alarm Interface Schedule" in body and "Not provided for this project." in body

    log = client.get(url).json()["log"]
    assert len(log) == 1 and log[0]["email"] == "syed.siraj@AL-MAJID.com"
    assert {i["key"]: i["state"] for i in log[0]["items"]}["interfaces"] == "skipped"

    # unskipped, it is not ready again
    view = client.put(f"{url}/items/interfaces", json={"action": "unskip"}).json()
    assert not view["ready"]
