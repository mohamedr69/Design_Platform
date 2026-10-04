"""The model's part of the drawings review: it reads the plotted plan, room
by room, against the company's coverage rules, and says what the draftsman
must change -- a device to ADD, one to REMOVE, one to REPLACE with another
type -- with where on the plan.

It is shown a window of the plan with every room the plan names numbered
on the image, and the drawing's own legend, so it reads the symbols the way
this drawing draws them. A sheet pass looks at the whole floor for what a
room-by-room look misses: escape-route signage, call points along the
routes, spaces nobody named.

The model proposes; it decides nothing. Every change is the engineer's to
accept before it reaches the draftsman's mark-up.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

SYSTEMS = {
    "detection": "Fire detection (smoke / heat detector)",
    "speaker": "Notification (speaker / sounder-flasher)",
    "fire_telephone": "Fire telephone jack",
    "manual_call_point": "Manual call point",
    "emergency_light": "Emergency light",
    "exit_sign": "Exit / directional sign",
}
STATUSES = ("present", "absent", "not_required", "unclear", "wrong")
ACTIONS = ("none", "add", "remove", "replace")
PROMPT_VERSION = "drawing-review-2026-10-01.3"

# The company's coverage rules, as the engineers set them (1 Oct 2026).
RULES = [
    ("detection", "Every room and space has a detector: smoke by default; HEAT detector in pump rooms, kitchens, "
                  "pantries, garbage and generator rooms. Not required: car-park driveways and parking bays, toilets / "
                  "baths / showers, shafts, open-to-sky areas, open balconies. Staircases and lift lobbies: one smoke "
                  "detector about every 5 floors (about 23 m), not on every floor -- checked across the floors by the "
                  "platform."),
    ("speaker", "A ceiling speaker in every occupied room, corridor and lobby. Car-park driveways: a WALL-MOUNTED "
                "speaker-flasher or a wall-mounted sounder-flasher, not a ceiling speaker. Pump rooms: a "
                "sounder-flasher. Staircases: a WALL-MOUNTED speaker on ALTERNATE floors (one floor yes, the next "
                "no) -- checked across the floors by the platform. Not required: electrical rooms, shafts, small "
                "stores, open balconies."),
    ("fire_telephone", "A fire telephone jack at each stair on every floor, in the fire lift lobby and in the fire "
                       "command room. Not required elsewhere."),
    ("manual_call_point", "A manual call point at every staircase door, at every exit to the outdoors, inside every "
                          "PUMP ROOM (by its door), and along escape routes (driveways included) so that none is more "
                          "than 61 m from the next. Not required inside other rooms."),
    ("emergency_light", "Emergency lighting on escape routes, corridors, stairs, lobbies, plant and electrical rooms "
                        "and toilets; an IP-RATED (weatherproof) emergency light in pump rooms. Not required: small "
                        "stores, the rooms inside residential apartments, GARBAGE / REFUSE rooms, ELV rooms and "
                        "LOCKER rooms -- an emergency light found there is to be REMOVED."),
    ("exit_sign", "An exit sign above every stair door and final exit; a DIRECTIONAL sign at every change of "
                  "direction along the escape routes, car-park driveways included, as the FLS drawings route them. "
                  "Not required inside rooms."),
]


def rules_text() -> str:
    return "\n".join(f"- {SYSTEMS[key]}: {text}" for key, text in RULES)


_ANSWERS = """For each system answer:
- status: PRESENT (the right device is there), ABSENT (the rules require it and none is there), NOT_REQUIRED (the
  rules do not require it here), WRONG (a device is there that the rules do not want here, or of the wrong type --
  e.g. a smoke detector in a pump room, a ceiling speaker in an electrical room or in a driveway, a non-IP emergency
  light in a pump room), UNCLEAR (the image does not let you tell);
- action for the draftsman: ADD (absent), REMOVE (a device not wanted here), REPLACE (the wrong type), NONE.
  A device that IS there where the rules do not require it is WRONG with action REMOVE -- never NOT_REQUIRED --
  so the engineer can confirm deleting it;
- device: the device to add / remove / put in, in the legend's words (e.g. "heat detector (H)", "wall-mounted
  speaker-flasher", "IP-rated emergency light");
- instruction: one short line the draftsman can act on (e.g. "Replace OS with heat detector H, centre of room");
- x, y: where on THAT image to make the change, as fractions of its width and height (0..1, from the top-left):
  for ADD where the device should go, for REMOVE / REPLACE where the existing symbol is; -1, -1 when you cannot say."""

SYSTEM_WINDOW = f"""You review fire alarm IFC drawings for a fire alarm contractor in the UAE, to tell the draftsman
exactly what to add, remove or replace on the plan. You are shown pieces of a plotted floor plan and the drawing's
own legend. Every room the plan names is marked with a blue numbered circle just above its name.

For each numbered room: say what the room is, then answer for each system.
{_ANSWERS}

Staircases and lift lobbies: report their smoke detector as PRESENT or ABSENT as you see it, with action NONE -- the
platform checks the 5-floor spacing across the floors itself. Staircases: report their speaker the same way,
PRESENT or ABSENT with action NONE -- the platform checks that it is on alternate floors.

The rules (this company's, apply them as written):
{rules_text()}

Read the symbols with the legend; never assume a symbol means what the legend does not say. Be conservative: what
you are not sure you see is UNCLEAR. Never invent a room or a symbol. Keep "seen" to at most eight words (the
symbols in the room, e.g. "OS, CS, E") and "room_type" to a few words. Under "other", report changes needed outside
the numbered rooms -- an unnamed space, a driveway turn without a directional sign, a missing call point at an
exit -- each with its image number, action, device, instruction and x, y."""

SYSTEM_SHEET = f"""You review fire alarm IFC drawings for a fire alarm contractor in the UAE, to tell the draftsman
what to add, remove or replace. You are shown one whole floor plan, plotted, and the drawing's legend. Rooms are
reviewed one by one separately; your job is what a room-by-room look misses:
- escape routes: an exit sign above every stair door and final exit; a directional sign at every change of
  direction, car-park driveways included;
- manual call points: at every staircase door, at every exit to the outdoors, inside every pump room, and no more
  than 61 m apart along the escape routes and driveways;
- a fire telephone jack at each stair and in the fire lift lobby;
- car-park driveways: wall-mounted speaker-flashers or sounder-flashers for notification;
- spaces with no name on the plan that lack the devices the rules require.
{_ANSWERS}

The rules (this company's, apply them as written):
{rules_text()}

Report only what you can see. Give x, y on the floor-plan image. If nothing needs changing, return no findings."""

_POS = {"x": {"type": "number"}, "y": {"type": "number"}}
_CHANGE = {"action": {"type": "string", "enum": list(ACTIONS)}, "device": {"type": "string"},
           "instruction": {"type": "string"}, **_POS}
_CHECK = {"type": "object", "properties": {
    "system": {"type": "string", "enum": list(SYSTEMS)}, "status": {"type": "string", "enum": list(STATUSES)},
    "seen": {"type": "string"}, **_CHANGE},
    "required": ["system", "status", "seen", "action", "device", "instruction", "x", "y"], "additionalProperties": False}
WINDOW_SCHEMA = {"type": "object", "properties": {
    "rooms": {"type": "array", "items": {"type": "object", "properties": {
        "n": {"type": "integer"}, "room_type": {"type": "string"},
        "checks": {"type": "array", "items": _CHECK}},
        "required": ["n", "room_type", "checks"], "additionalProperties": False}},
    "other": {"type": "array", "items": {"type": "object", "properties": {
        "image": {"type": "integer"}, "system": {"type": "string", "enum": list(SYSTEMS)},
        "where": {"type": "string"}, "issue": {"type": "string"}, **_CHANGE},
        "required": ["image", "system", "where", "issue", "action", "device", "instruction", "x", "y"],
        "additionalProperties": False}}},
    "required": ["rooms", "other"], "additionalProperties": False}
SHEET_SCHEMA = {"type": "object", "properties": {
    "findings": {"type": "array", "items": {"type": "object", "properties": {
        "system": {"type": "string", "enum": list(SYSTEMS)}, "where": {"type": "string"},
        "issue": {"type": "string"}, "severity": {"type": "string", "enum": ["high", "medium", "low"]}, **_CHANGE},
        "required": ["system", "where", "issue", "severity", "action", "device", "instruction", "x", "y"],
        "additionalProperties": False}}},
    "required": ["findings"], "additionalProperties": False}

# Rooms whose detection is spaced across floors, not required on each.
SPACED = re.compile(r"\bSTAIR|\bLIFT LOBBY\b|\bFIRE LIFT LOBBY\b|\bFIRE LOBBY\b", re.I)


def numbered(png: bytes, marks: list[tuple[int, float, float]]) -> bytes:
    """The image with a blue numbered circle over each room's name:
    (number, x px, y px)."""
    image = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(image)
    size = max(14, image.width // 70)
    try:
        font = ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        font = ImageFont.load_default()
    for n, x, y in marks:
        cx, cy, r = x, y - size * 1.1, size * 0.85
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(29, 78, 216), outline=(255, 255, 255), width=2)
        label = str(n)
        box = draw.textbbox((0, 0), label, font=font)
        draw.text((cx - (box[2] - box[0]) / 2, cy - (box[3] - box[1]) / 2 - box[1]), label, fill=(255, 255, 255),
                  font=font)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _fraction(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return -1.0
    return f if 0.0 <= f <= 1.0 else -1.0


def _change(c: dict) -> dict:
    action = c.get("action") if c.get("action") in ACTIONS else "none"
    return {"action": action, "device": str(c.get("device") or "")[:80],
            "instruction": str(c.get("instruction") or "")[:220], "x": _fraction(c.get("x")), "y": _fraction(c.get("y"))}


@dataclass
class RoomAnswer:
    room_type: str
    checks: dict[str, dict]        # system -> {"status", "seen", "action", "device", "instruction", "x", "y"}


def read_window_answer(data: dict | None, numbers: set[int]) -> tuple[dict[int, RoomAnswer], list[dict]]:
    """The model's answer, kept only where it is well formed: a room number
    it was given, a system, a status and an action of the schema. A system
    it says nothing about is unclear, never assumed. An action that does not
    follow from the status (ADD for a device that is present) is dropped."""
    rooms: dict[int, RoomAnswer] = {}
    for item in (data or {}).get("rooms") or []:
        n = item.get("n")
        if n not in numbers or n in rooms:
            continue
        checks = {}
        for c in item.get("checks") or []:
            if c.get("system") in SYSTEMS and c.get("status") in STATUSES and c["system"] not in checks:
                change = _change(c)
                # the action follows the status: absent is ADD, wrong is REPLACE (or REMOVE), the rest nothing
                if c["status"] == "absent":
                    change["action"] = "add"
                elif c["status"] == "wrong":
                    change["action"] = change["action"] if change["action"] in ("remove", "replace") else "replace"
                else:
                    change["action"] = "none"
                checks[c["system"]] = {"status": c["status"], "seen": str(c.get("seen") or "")[:200], **change}
        for system in SYSTEMS:
            checks.setdefault(system, {"status": "unclear", "seen": "not answered", "action": "none", "device": "",
                                       "instruction": "", "x": -1.0, "y": -1.0})
        rooms[n] = RoomAnswer(str(item.get("room_type") or "")[:60], checks)
    other = [{"image": o.get("image"), "system": o["system"], "where": str(o.get("where") or "")[:160],
              "issue": str(o.get("issue") or "")[:300], **_change(o)}
             for o in (data or {}).get("other") or [] if o.get("system") in SYSTEMS and o.get("issue")]
    return rooms, [o for o in other if o["action"] != "none"]


def read_sheet_answer(data: dict | None) -> list[dict]:
    out = []
    for f in (data or {}).get("findings") or []:
        if f.get("system") not in SYSTEMS or not f.get("issue"):
            continue
        change = _change(f)
        if change["action"] == "none":
            continue
        out.append({"system": f["system"], "where": str(f.get("where") or "")[:160],
                    "issue": str(f.get("issue") or "")[:300],
                    "severity": f.get("severity") if f.get("severity") in ("high", "medium", "low") else "medium",
                    **change})
    return out


SYSTEM_FLS = f"""You check a fire alarm / emergency lighting IFC drawing against the FLS (fire & life safety)
drawing of the same floor, to tell the draftsman what to change. IMAGE 1 is the FLS plan: its escape routes,
exits, travel arrows and exit / directional signage are what the consultant requires. IMAGE 2 is the IFC plan as
drawn now; the legend says what its symbols are.

Follow every FLS escape route (car-park driveways included) and check the IFC plan:
- an exit on the FLS (stair door, final exit, exit to the outdoors) with no EXIT sign above it on the IFC: ADD an
  exit sign;
- a change of direction on an FLS route with no DIRECTIONAL sign on the IFC: ADD a single or double-sided
  directional sign, its arrow as the FLS route goes;
- an IFC directional sign pointing against the FLS route: REPLACE it with one pointing the FLS way;
- an IFC exit or directional sign where the FLS has no exit or route: REMOVE it;
- an FLS exit to the outdoors with no manual call point beside it on the IFC: ADD a manual call point.
{_ANSWERS}
Give x, y on IMAGE 2 (the IFC plan). Use system "exit_sign" for signs and "manual_call_point" for call points.
Report only differences you can see between the two plans; if the IFC follows the FLS, return no findings. Do not
assume the two images are drawn at the same scale or position: match them by the building's walls, stairs and
rooms."""
