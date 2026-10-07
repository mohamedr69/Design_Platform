"""Drawings Redesign: each accepted change placed (what is erased, what is
inserted, where), adjusted by the engineer, and the AutoLISP AutoCAD runs
on the copy. The model and AutoCAD are not called here."""

from app.redesign import ai as A
from app.redesign import cad
from app.redesign import service as R

GEOMETRY = {"v": 1, "a": 0.1, "bx": 0.0, "by": 0.0, "residual": 0.4}      # 1 pt = 0.1 m, page y down
SHEET = {"index": 0, "name": "FA 101", "plan": [0, 0, 2000, 2000], "geometry": GEOMETRY}
SYMBOLS = [{"id": 2, "name": "Heat Detector (Addressable)", "code": "HD", "block": "HEAT DETECTOR", "layer": "-fire alarm",
            "scale": 1.0, "scales": {"FA 101": 1.0}, "count": 9},
           {"id": 17, "name": "Ceiling Speaker", "code": "SPK", "block": "CEILING SPEAKER", "layer": "-SPK",
            "scale": 0.009, "scales": {}, "count": 40}]


def _change(action: str) -> dict:
    occurrences = [
        {"handle": "5DD03", "block": "CEILING SPEAKER", "sheet": "FA 101", "x": 50.0, "y": -50.0, "ix": 49.9, "iy": -50.1,
         "rotation": 0.0, "scale": 0.009, "layer": "-SPK", "type_id": 17, "name": "Ceiling Speaker", "code": "SPK"},
        {"handle": "AAAA", "block": "LIFT", "sheet": "FA 101", "x": 51.0, "y": -51.0, "ix": 51.0, "iy": -51.0,
         "rotation": 0.0, "scale": 1, "layer": "0", "type_id": None, "name": "12", "code": ""},     # a stair's number
    ]
    finding = {"id": f"f-{action}", "page": 0, "sheet": "FA 101", "floor": "GROUND FLOOR", "room": "PUMP ROOM",
               "system": "detection", "system_name": "Detection", "action": action, "device": "heat detector (H)",
               "instruction": "Add heat detector H, centre of pump room", "at": [500.0, 500.0]}
    return R._prepare(finding, SHEET, occurrences, top={"5DD03"})


def test_a_change_is_prepared_with_the_devices_near_it_numbered():
    change = _change("add")
    assert change["status"] == "pending" and change["box"] == [420.0, 420.0, 580.0, 580.0]      # 8 m around
    # the speaker numbered; the stair's number is not a device
    assert [(c["n"], c["name"], c["erasable"]) for c in change["candidates"]] == [(1, "Ceiling Speaker", True)]


def test_an_add_is_placed_where_the_model_points_with_the_drawings_own_symbol():
    change = _change("add")
    answer = A.read_answer({"candidate": 0, "symbol": 2, "x": 0.25, "y": 0.75, "rotation": 87, "confidence": "high",
                            "note": ""}, len(change["candidates"]), {2, 17})
    R._place(change, SHEET, SYMBOLS, answer)
    assert change["status"] == "proposed" and change["remove"] is None
    insert = change["insert"]
    assert (insert["block"], insert["layer"], insert["scale"], insert["rotation"]) == ("HEAT DETECTOR", "-fire alarm", 1.0, 90)
    assert insert["page"] == [460.0, 540.0] and insert["model"] == [46.0, -54.0]


def test_a_replace_takes_the_old_symbols_place_and_a_remove_needs_a_symbol():
    change = _change("replace")
    R._place(change, SHEET, SYMBOLS, {"candidate": 1, "symbol": 2, "x": None, "y": None, "rotation": 0})
    assert change["remove"]["handle"] == "5DD03"
    assert change["insert"]["seen"] == [50.0, -50.0]           # seen where the old symbol was seen
    nothing = _change("remove")
    R._place(nothing, SHEET, SYMBOLS, {"candidate": 0, "symbol": 0, "x": None, "y": None, "rotation": 0})
    assert nothing["status"] == "failed" and nothing["remove"] is None
    # no symbol of the device in the drawing: a marker, the draftsman draws it
    draw = _change("add")
    R._place(draw, SHEET, SYMBOLS, {"candidate": 0, "symbol": 0, "x": 0.5, "y": 0.5, "rotation": 0})
    assert draw["placeholder"] and draw["insert"]["block"] is None


def test_the_answer_is_kept_only_where_it_is_well_formed():
    answer = A.read_answer({"candidate": 9, "symbol": 99, "x": 1.4, "y": 0.2, "rotation": 181, "confidence": "sure",
                            "note": "x"}, 3, {2})
    assert (answer["candidate"], answer["symbol"], answer["x"], answer["rotation"], answer["confidence"]) == (0, 0, None, 180, "low")


def test_the_autocad_script_erases_inserts_at_the_true_scale_and_marks_each_change():
    changes = R.to_cad([
        {"action": "replace", "device": "heat detector", "remove": {"handle": "5DD03", "erasable": True, "model": [1, 2], "name": "CS"},
         "insert": {"block": "HEAT DETECTOR", "layer": "-fire alarm", "scale": 1.0, "rotation": 90, "model": [1, 2], "name": "HD"}},
        {"action": "remove", "device": "speaker", "remove": {"handle": "BEEF", "erasable": False, "model": [3, 4], "name": "CS"},
         "insert": None},
    ])
    assert changes[1]["remove_handle"] is None and "(erase by hand)" in changes[1]["label"]
    script = "\n".join(cad.script_lines(changes, marker=0.6, text_height=0.25))
    assert '(setvar "TILEMODE" 1)' in script                      # model space, not the sheet layout
    assert '(entdel (handent "5DD03"))' in script and "BEEF" not in script
    # inserted once at 1 to learn the block's unit factor, then at the scale wanted divided by it
    assert '"_.-INSERT" "HEAT DETECTOR" "_S" 1.0 (list 1.000000 2.000000 0.0) 90.000000' in script
    assert '(/ 1.000000 ep_f)' in script and '(setvar "CLAYER" "-fire alarm")' in script
    assert script.count('(cons 0 "CIRCLE")') == 2 and '"EP-REDESIGN-REPLACE"' in script
    assert script.rstrip().endswith("_.QSAVE\n_.QUIT\n_Y") or "_.QSAVE" in script


def test_a_block_drawn_away_from_its_base_point_is_inserted_so_it_is_seen_on_the_spot():
    # copies of a block whose graphics sit 900 units right of its base point, at scale 0.8, rotated 90
    copies = [{"x": 10.0, "y": 720.0 + 10.0, "ix": 10.0, "iy": 10.0, "rotation": 90.0, "scale": 0.8}]
    assert [round(v, 3) for v in R._drawn_centre(copies)] == [900.0, 0.0]
    symbols = [{"id": 36, "name": "Sounder Strobe WP", "code": "", "block": "faw", "layer": "-FA", "scale": 0.8,
                "scales": {}, "center": [900.0, 0.0], "count": 90}]
    change = _change("add")
    change["device"] = "heat detector"
    R._place(change, SHEET, symbols, {"candidate": 0, "symbol": 36, "x": 0.5, "y": 0.5, "rotation": 0, "picked": True})
    # seen at the spot; inserted 720 to its left
    assert change["insert"]["seen"] == [50.0, -50.0] and change["insert"]["model"] == [-670.0, -50.0]
    assert R.to_cad([change])[0]["at"] == [50.0, -50.0]           # the marker where it is seen


def test_a_sounder_flasher_is_the_strobe_symbol_and_a_sounder_the_wall_sounder():
    symbols = SYMBOLS + [
        {"id": 36, "name": "Sounder Strobe WP", "code": "", "block": "faw", "layer": "-FA", "scale": 0.8, "scales": {},
         "center": [0.0, 0.0], "count": 90},
        {"id": 44, "name": "Wall mounted sounder", "code": "", "block": "st", "layer": "-FA", "scale": 0.866,
         "scales": {}, "center": [0.0, 0.0], "count": 33}]
    flasher = _change("add")
    flasher["device"] = "addressable fire alarm sounder strobe (weather proof)"
    R._place(flasher, SHEET, symbols, {"candidate": 0, "symbol": 44, "x": 0.5, "y": 0.5, "rotation": 0})
    assert flasher["insert"]["block"] == "faw"
    sounder = _change("add")
    sounder["device"] = "wall mounted sounder"
    R._place(sounder, SHEET, symbols, {"candidate": 0, "symbol": 36, "x": 0.5, "y": 0.5, "rotation": 0})
    assert sounder["insert"]["block"] == "st"
    # the engineer's own pick stands
    R._place(flasher, SHEET, symbols, {"candidate": 0, "symbol": 44, "x": 0.5, "y": 0.5, "rotation": 0, "picked": True})
    assert flasher["insert"]["block"] == "st"


def test_a_block_faces_the_side_its_sound_waves_are_on():
    assert R._facing([922.76, -476.92], {"size": 0.46, "ext": [0, 0, 0.44, 0.46], "strokes": 88.0}) == 90.0
    assert R._facing([0.198, -0.264], {"size": 0.527, "ext": [0, -0.527, 0.397, 0], "strokes": None}) == 270.0
    assert R._facing([922.0, -476.0], {"size": 0.46, "ext": [0, 0, 1, 1], "strokes": None}) is None
    # turned to face right: the flasher (faces up) a quarter turn clockwise, the sounder (faces down) anticlockwise
    assert R._rotation({"facing": 90.0}, {"facing": "right"}) == 270.0
    assert R._rotation({"facing": 270.0}, {"facing": "right"}) == 90.0


def test_a_wall_device_is_fixed_with_its_back_on_the_wall_face():
    from app.redesign.walls import Walls

    # a 200 mm wall: faces at x = 49.0 and 49.2, running north-south across the spot
    walls = Walls({(24, -26): [(49.0, -52.0, 49.0, -48.0), (49.2, -52.0, 49.2, -48.0)],
                   (24, -25): [(49.0, -52.0, 49.0, -48.0), (49.2, -52.0, 49.2, -48.0)]})
    symbols = [{"id": 36, "name": "Sounder Strobe WP", "code": "", "block": "faw", "layer": "-FA", "scale": 0.8,
                "scales": {}, "center": [0.0, 0.0], "facing": 90.0, "depth": 0.15, "count": 90}]
    change = _change("add")
    change["device"] = "sounder strobe (weather proof)"
    # the model's spot is 0.8 m into the room, facing east
    R._place(change, SHEET, symbols, {"candidate": 0, "symbol": 36, "x": 0.5, "y": 0.5, "facing": "right"}, walls)
    assert change["on_wall"] is True
    assert change["insert"]["seen"] == [49.32, -50.0]          # back on the room face (49.2) + half its depth
    assert change["insert"]["rotation"] == 270.0


def test_two_devices_at_one_wall_share_it_side_by_side_without_passing_its_corner():
    from app.redesign.walls import Walls

    # the room's face at x = 49.2 runs y -50.4..-49.6; past its corner the next wall's face is 0.02 m further
    segs = [(49.2, -50.4, 49.2, -49.6), (49.22, -49.4, 49.22, -45.0), (49.2, -49.6, 55.0, -49.6)]
    walls = Walls({(i, j): segs for i in range(23, 28) for j in range(-27, -21)})
    assert walls.face_span(49.4, -50.0, (1.0, 0.0)) == (49.2, -50.4, -49.6)

    def device(cid, y, r):
        return {"id": cid, "status": "approved", "page": 0, "candidates": [],
                "insert": {"block": "B", "seen": [49.4, y], "placed": [49.4, y], "model": [49.4, y], "offset": [0, 0],
                           "radius": r, "facing": [1.0, 0.0]}}

    flasher, call_point = device("a", -50.0, 0.18), device("b", -49.95, 0.1)
    R.coordinate([flasher, call_point], {0: SHEET}, walls)
    ys = sorted(c["insert"]["seen"][1] for c in (flasher, call_point))
    # both still on the room's face, clear of each other, neither past the corner at -49.6
    assert all(c["insert"]["seen"][0] == 49.4 for c in (flasher, call_point))
    assert ys[1] - ys[0] >= 0.18 + 0.1 + R.GAP_M - 1e-6
    for c in (flasher, call_point):
        y, r = c["insert"]["seen"][1], c["insert"]["radius"]
        assert y - r >= -50.4 - 1e-6 and y + r <= -49.6 + 1e-6
    # done afresh each time: the same answer again
    before = [list(c["insert"]["seen"]) for c in (flasher, call_point)]
    R.coordinate([flasher, call_point], {0: SHEET}, walls)
    assert [c["insert"]["seen"] for c in (flasher, call_point)] == before


def test_an_ip_rated_emergency_light_is_the_drawings_e_made_weatherproof_as_a_new_block():
    occurrences = [{"block": "E", "layer": "-EMERGENCY", "sheet": "FA 101", "x": 1.0, "y": 1.0, "ix": 1.0, "iy": 1.0,
                    "rotation": 0.0, "scale": 0.2, "type_id": None, "name": "E", "code": ""} for _ in range(5)]
    occurrences.append({**occurrences[0], "block": "EXT WP", "layer": "Ext", "name": "EXT WP"})
    sizes = {"E": {"size": 2.1, "ext": [-1.27, -1.18, 0.83, 0.85], "strokes": None}}
    symbols = R._symbols(occurrences, {"E", "EXT WP"}, sizes)
    light = next(s for s in symbols if s["name"] == "Emergency Light")
    assert light["block"] == "E" and light["facing"] is None and light["id"] >= 900000
    assert any(s["name"] == "Exit Sign WP" for s in symbols)
    change = _change("add")
    change["device"] = "IP-rated emergency light"
    R._place(change, SHEET, symbols, {"candidate": 0, "symbol": 0, "x": 0.5, "y": 0.5, "rotation": 0})
    insert = change["insert"]
    assert (insert["block"], insert["rotation"], insert["make"]["from"], insert["make"]["text"]) == ("E WP", 0.0, "E", "WP")
    # a plain emergency light stays the drawing's E
    plain = _change("add")
    plain["device"] = "emergency light (E)"
    R._place(plain, SHEET, symbols, {"candidate": 0, "symbol": 0, "x": 0.5, "y": 0.5, "rotation": 0})
    assert plain["insert"]["block"] == "E" and not plain["insert"].get("make")
    # AutoCAD copies E into the new block once, adds the letters, then inserts it
    script = "\n".join(cad.script_lines(R.to_cad([change, dict(change, id="x2")]), marker=0.6, text_height=0.25))
    assert script.count("(defun ep_copy") == 1 and script.count('(ep_copy "E" "E WP")') == 1
    assert script.index('(ep_copy "E" "E WP")') < script.index('"_.-INSERT" "E WP"')
    assert '(cons 1 "WP")' in script


def test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved():
    # 1:175 in metres: a plot point is 0.0617 m; the sample is 1:100 in mm
    sheet = {**SHEET, "geometry": {**GEOMETRY, "a": 0.0617}}
    modules = R._module_symbols({0: sheet}, [{"id": 23, "name": "Control / Output Module", "layer": "fire alarm"}])
    cr = next(m for m in modules if m["code"] == "CR")
    assert cr["block"] == "CR" and cr["layer"] == "fire alarm" and cr["library"].endswith("/library/CR.dwg")
    assert abs(cr["scales"]["FA 101"] - 0.00175) < 1e-5            # ~0.7 m wide: 4 mm on paper, as on the sample
    assert abs(R._note_height(sheet) - 0.306) < 0.002
    # what it is for, as the sample writes it
    assert R._for({"tag": "B3-SEF-3"}, "Tag Not Identified") == "B3-SEF-3"
    assert R._for({"tag": "Tag Not Identified", "description": 'Zone Control Valve (drawn: "\u00d8150 ZCV")',
                   "equipment": "Zone Control Valve"}, "Tag Not Identified") == "ZCV"
    # only what the engineer approved is drawn: a proposed change, review or
    # module, waits for the engineer, as do pending and skipped ones
    placed = {"insert": {"block": "CR"}, "remove": None}
    assert R._drawn({**placed, "status": "approved"})
    assert not R._drawn({**placed, "status": "proposed"})
    assert not R._drawn({**placed, "status": "pending"})
    assert not R._drawn({**placed, "status": "skipped"})
    assert not R._drawn({"insert": None, "remove": None, "status": "approved"})
    assert not R._drawn({**placed, "status": "proposed", "source": "interface"})
    assert R._drawn({**placed, "status": "approved", "source": "interface"})
    # the engineer's word on a module survives bringing the schedule in again
    old = {"id": "if:x:CR1", "status": "skipped", "source": "interface"}
    merged = R._merge_interfaces([{"id": "f1", "status": "proposed"}, old],
                                 [{"id": "if:x:CR1", "status": "proposed", "source": "interface"},
                                  {"id": "if:y:CT21", "status": "proposed", "source": "interface"}], {old["id"]: old})
    assert [(c["id"], c["status"]) for c in merged] == [("f1", "proposed"), ("if:x:CR1", "skipped"), ("if:y:CT21", "proposed")]


def test_a_library_block_is_brought_in_from_its_file_only_by_the_first_insert_and_noted():
    change = {"action": "add", "device": "Control Relay Module (CR) for B3-SEF-3", "remove": None,
              "insert": {"block": "CR", "layer": "fire alarm", "scale": 0.00175, "rotation": 0, "model": [10, 20],
                         "seen": [10, 20.12], "library": "C:/lib/CR.dwg"},
              "interface": {"code": "CR", "for": "B3-SEF-3", "note_height": 0.306, "half": 0.35}}
    cad_change = R.to_cad([change])[0]
    assert cad_change["label"] == "ADD: CR FOR B3-SEF-3"
    assert cad_change["note"]["text"] == "FOR B3-SEF-3" and cad_change["note"]["at"][0] > 10.35
    script = "\n".join(cad.script_lines([cad_change], marker=0.6, text_height=0.25))
    inserts = [line for line in script.splitlines() if '"_.-INSERT"' in line]
    assert '(if (tblsearch "BLOCK" "CR") "CR" "CR=C:/lib/CR.dwg")' in inserts[0]
    assert "CR=" not in inserts[1]                               # never "redefine?": the block is there by then
    assert '(cons 1 "FOR B3-SEF-3")' in script and '(cons 8 "fire alarm")' in script


def test_a_typical_plans_floors_get_one_module_each_item_stacked_and_the_unplaceable_listed(monkeypatch):
    from app.interfaces import service as I

    sheet = {**SHEET, "title": "TYPICAL 3RD TO 4TH FLOOR PLAN", "floor": "TYPICAL 3RD TO 4TH FLOOR",
             "geometry": {**GEOMETRY, "a": 0.0617}}

    def row(floor, anchor, key="smoke_exhaust_fan", tag="SEF-1", mods=None):
        return {"id": f"SM|x|{key}|{tag}|{floor}", "floor_key": floor, "floor": floor, "tag": tag, "key": key,
                "equipment": "Smoke Exhaust Fan", "system": "Smoke Management", "description": "", "location": "",
                "modules": mods or {"CT1": 0, "CT2": 0, "CR": 1}, "anchor": anchor, "source": "SMOKE LAYOUT.dwg"}

    rows = [row("L3", [50.0, -50.0]), row("L4", [50.0, -50.0]),                 # one plan for both floors
            row("L3", [50.0, -50.0], key="fan_status", tag="SEF-1", mods={"CT1": 1, "CT2": 0, "CR": 0}),
            row("L3", None, key="lift", tag="Tag Not Identified")]             # no drawn position
    monkeypatch.setattr(I, "build", lambda db, project: {"rows": rows})

    class Floors:
        def __init__(self, db, project):
            pass

        def of_title(self, title):
            return ["L3", "L4"] if "TYPICAL" in title else []

    monkeypatch.setattr(I, "Floors", Floors)
    symbols = R._module_symbols({0: sheet}, [])
    changes = R._interface_changes(None, None, {0: sheet}, [], set(), symbols)
    placed = [c for c in changes if c.get("insert")]
    assert sorted(c["interface"]["code"] for c in placed) == ["CR", "CT1"]          # L3 and L4: drawn once
    (x1, y1), (x2, y2) = sorted((c["insert"]["seen"] for c in placed), key=lambda p: -p[1])
    assert abs(x1 - 50) < 0.01 and abs(x2 - 50) < 0.01 and y1 - y2 >= 0.69 + R.GAP_M   # one under the other, clear
    lift = [c for c in changes if c["status"] == "failed"]
    assert len(lift) == 1 and "draw it by hand" in lift[0]["error"]


def test_a_module_goes_on_the_nearest_real_wall_turned_to_it_past_an_equipment_outline():
    from app.redesign.walls import Walls

    # the module's spot (50, -50); a pump set's outline (one line) at x 50.1, the room's wall (two faces) at 51.1 / 51.3
    segs = [(50.1, -52.0, 50.1, -48.0), (51.1, -52.0, 51.1, -48.0), (51.3, -52.0, 51.3, -48.0)]
    walls = Walls({(i, j): segs for i in range(22, 28) for j in range(-28, -22)})
    facing, face = R._nearest_wall(walls, 50.0, -50.0)
    assert facing == "left" and abs(face[0] - 51.1) < 1e-6           # the wall, not the outline in front of it
    symbols = R._module_symbols({0: SHEET}, [])
    cr = symbols[0]
    change = _change("add")
    change["device"], change["source"] = "Control Relay Module (CR) for SEF-1", "interface"
    R._place_module(change, SHEET, symbols, {"candidate": 0, "symbol": cr["id"], "x": 0.5, "y": 0.5,
                                             "rotation": 0, "facing": None, "picked": True}, walls)
    insert = change["insert"]
    assert change["on_wall"] and insert["facing"] == [-1.0, 0.0] and insert["rotation"] == 90.0   # back to the wall
    assert abs(insert["seen"][0] - (51.1 - cr["depth"] * insert["scale"])) < 0.01               # its back on the face
    note = R.to_cad([{**change, "interface": {"code": "CR", "for": "SEF-1", "note_height": 0.3, "half": 0.35,
                                              "depth": 0.2167}}])[0]["note"]
    assert note["align"] == "right" and note["at"][0] < insert["seen"][0]                       # into the room


def test_coordination_is_always_done_the_engineers_moves_and_the_modules_notes_included():
    from app.redesign.walls import Walls

    # a long wall up the sheet at x 51.1 (two faces), modules facing left (into the room) on it
    segs = [(51.1, -60.0, 51.1, -40.0), (51.3, -60.0, 51.3, -40.0)]
    walls = Walls({(i, j): segs for i in range(22, 28) for j in range(-32, -18)})

    def module(cid, y, text, moved=True):
        return {"id": cid, "status": "approved", "page": 0, "candidates": [], "moved": moved, "source": "interface",
                "insert": {"block": "CT2", "seen": [50.88, y], "placed": [50.88, y], "model": [50.88, y],
                           "offset": [0, 0], "radius": 0.41, "facing": [-1.0, 0.0], "rotation": 90.0, "layer": "fa"},
                "interface": {"code": "CT2", "for": text, "note_height": 0.306, "half": 0.41, "depth": 0.21}}

    # the engineer clicked both onto (nearly) the same spot
    a, b = module("if:a:CT21", -50.0, "ELECTRIC PUMP"), module("if:b:CT21", -50.17, "DIESEL PUMP")
    R.coordinate([a, b], {0: SHEET}, walls)
    assert not any(R._overlap(x, y, 0) for x in R._footprint(a) for y in R._footprint(b))
    assert a["insert"]["seen"] == [50.88, -50.0] and b.get("coordinated")              # the first keeps its spot
    assert b["insert"]["seen"][0] == 50.88                                              # the other still on the wall
    # the note is part of what must be clear: running from the module into the room
    note = R._footprint(a)[1]
    assert note[2] < 50.88 and note[2] - note[0] > 3.0
