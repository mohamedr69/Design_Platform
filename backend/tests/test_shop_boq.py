"""The BOQ as per Shop Drawings: made from the IFC BOQ, edited by hand, and
the source of the amplifier and power schedules."""

from app.services import shop_boq

from .test_amplifier_calculation import _login, _upload_schedule


def _speaker(per_floor, qty, id_=17, name="Ceiling Speaker", code="SPK"):
    return {"device_type": {"id": id_, "code": code, "name": name, "category": "fire_alarm", "unit": "Nos"},
            "per_floor": per_floor, "qty": qty}


def _drawing(rows_gf, rows_typical, floors=(1, 2, 3)):
    return {
        "id": 1, "filename": "FIRE ALARM LAYOUT.dwg", "revision": "R2",
        "floor_boq": {"fire_alarm": {"floors": [
            {"sheet": "FA 101", "title": "GROUND FLOOR PLAN", "floor_name": "GROUND FLOOR", "floors": [],
             "multiplier": 1, "rows": rows_gf},
            {"sheet": "FA 102", "title": "TYPICAL FLOOR PLAN", "floor_name": "TYPICAL", "floors": list(floors),
             "multiplier": len(floors), "rows": rows_typical},
        ]}},
    }


def test_a_line_per_ifc_device_type_on_the_floor_wise_floors():
    floor_wise = {
        "floors": ["Ground floor", "Level 1", "Level 2", "Level 3"],
        "items": [{"description": "Ceiling Speaker", "device": "Speaker", "material": {"part_no": "EST-S186C"}},
                  {"description": "Wall Speaker", "device": "Speaker", "material": {"part_no": "G4SRN"}},
                  {"description": "Smoke for every 23 m", "device": "Smoke detector",
                   "material": {"part_no": "SIGA-OSD-FCN"}}],
    }
    smoke = {"device_type": {"id": 1, "code": "SD", "name": "Smoke Detector (Addressable)",
                             "category": "fire_alarm", "unit": "Nos"}, "per_floor": 4, "qty": 4}
    result = shop_boq.build([_drawing([_speaker(5, 5), smoke], [_speaker(7, 21)])], floor_wise)

    assert result["floors"] == ["Ground floor", "Level 1", "Level 2", "Level 3"]
    speaker = next(i for i in result["items"] if i["description"] == "Ceiling Speaker")
    # a typical plan's count is put on each floor it stands for
    assert speaker["per_floor"] == {"Ground floor": 5, "Level 1": 7, "Level 2": 7, "Level 3": 7}
    assert speaker["total"] == 26 and speaker["system"] == "FAS"
    # the part: the floor-wise line of the same name; else the one part its device is ordered as
    assert speaker["material"]["part_no"] == "EST-S186C"
    assert next(i for i in result["items"] if i["ifc_code"] == "SD")["material"]["part_no"] == "SIGA-OSD-FCN"
    assert result["grand_total"] == 30


def test_a_typical_plan_whose_floors_are_unknown_is_its_own_column():
    drawing = _drawing([_speaker(5, 5)], [_speaker(7, 21)], floors=())
    drawing["floor_boq"]["fire_alarm"]["floors"][1]["multiplier"] = 3
    result = shop_boq.build([drawing])
    assert "TYPICAL (x3)" in result["floors"]
    assert result["items"][0]["per_floor"]["TYPICAL (x3)"] == 21
    assert result["warnings"] and "stands for 3 floors" in result["warnings"][0]


def test_made_from_ifc_edited_and_read_by_the_amplifier(client, tmp_path, monkeypatch):
    _login(client)
    project_id = client.post("/projects", json={"ep_number": "30990", "project_name": "T",
                                                "design_sheets": []}).json()["id"]
    assert _upload_schedule(client, project_id, tmp_path).status_code == 200

    # No IFC drawing counted yet: nothing is made, and the amplifier says it reads the floor-wise BOQ.
    monkeypatch.setattr(shop_boq, "drawings_in_force", lambda db, project: ([], []))
    body = client.get(f"/projects/{project_id}/shop-boq").json()
    assert body["result"] is None and "No IFC drawing" in body["filed_note"]
    amp = client.get(f"/projects/{project_id}/design/amplifier").json()
    assert amp["schedule_file"] == "floors.xlsx"
    assert any("BOQ Floor Wise's" in w for w in amp["result"]["warnings"])

    # The first look makes it from the IFC BOQ.
    monkeypatch.setattr(shop_boq, "drawings_in_force",
                        lambda db, project: ([_drawing([_speaker(5, 5)], [_speaker(7, 21)])], []))
    body = client.get(f"/projects/{project_id}/shop-boq").json()
    assert body["file_name"] == "BOQ as per Shop Drawings"
    assert body["result"]["grand_total"] == 26
    assert "FIRE ALARM LAYOUT.dwg (R2)" in body["source_path"]

    # Edited by hand ...
    floors = body["result"]["floors"]
    body = client.patch(f"/projects/{project_id}/shop-boq/items/1",
                        json={"floor": floors[0], "quantity": 9}).json()
    assert body["result"]["grand_total"] == 30

    # ... and the amplifier and power schedules read it, not the floor-wise BOQ (10 + 3 x 14).
    amp = client.get(f"/projects/{project_id}/design/amplifier").json()
    assert amp["schedule_file"] == "BOQ as per Shop Drawings"
    assert amp["result"]["total_speakers"] == 30
    assert not any("BOQ Floor Wise's" in w for w in amp["result"]["warnings"])
    power = client.get(f"/projects/{project_id}/design/power").json()
    assert power["schedule_file"] == "BOQ as per Shop Drawings"

    # A speaker count changed on the amplifier tab lands on the shop drawings BOQ.
    part = amp["result"]["columns"][0]["key"]
    assert client.patch(f"/projects/{project_id}/design/amplifier/counts",
                        json={"part_no": part, "floor": floors[0], "count": 4}).status_code == 200
    assert client.get(f"/projects/{project_id}/shop-boq").json()["result"]["grand_total"] == 25

    # Made again from the IFC BOQ: the hand edits go.
    body = client.post(f"/projects/{project_id}/shop-boq/make").json()
    assert body["result"]["grand_total"] == 26

    pdf = client.get(f"/projects/{project_id}/shop-boq/export.pdf")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"

    assert client.delete(f"/projects/{project_id}/shop-boq").status_code == 204
