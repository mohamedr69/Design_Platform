"""What a drawing's words say is there: a label or tag on an IFC drawing
read as a piece of third-party equipment of the interface matrix.

Only what is written is read. "PEF-B4-01" is a parking extract fan tagged
PEF-B4-01; "Ø150 ZCV" is a zone control valve with no tag; "THIS ROOM IS
PROTECTED BY PRE-ACTION SYSTEM" says a pre-action system protects a room --
evidence, not a count. A standard door is never read as a motorized one,
and a bare "EF-01" (an exhaust fan the matrix has no row for) is not read
at all. A text may name several pieces of equipment ("THREE PUMPS : DIESEL
PUMP, ELECTRIC PUMP AND JOCKEY PUMP"); each is a detection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Kinds of detection: a label or tag beside the equipment; a note that a
# room or area is protected by a system (evidence, never a count by itself).
LABEL, NOTE = "label", "note"
# How sure the words are: "high" (a tag), "medium" (the equipment's name,
# no tag), "low" (the words do not say it is interfaced -- a plain sliding
# door, a fire door): low goes to Verification Required, never the schedule.
HIGH, MEDIUM, LOW = "high", "medium", "low"


@dataclass(frozen=True)
class Detection:
    key: str
    kind: str
    confidence: str
    tag: str | None = None
    detail: str = ""       # what else the words say: "Ø150", the room a note names


@dataclass(frozen=True)
class _Words:
    key: str
    pattern: re.Pattern
    confidence: str = MEDIUM
    # Detectors in one group are exclusive: the first that matches a text wins.
    group: str = ""


def _p(s: str) -> re.Pattern:
    return re.compile(s, re.I)


_PRESS = r"PRESSURI[SZ](?:ATION|ING|ED)"

# Tag prefixes: a prefix followed by a numbered code (PEF-B4-01, SPF-01, AHU02,
# FAHU-L3-01). Longer prefixes first, so FAHU is not read as AHU.
_TAG_PREFIXES: tuple[tuple[str, str], ...] = (
    ("FAHU", "fahu"), ("AHU", "ahu"),
    ("CPEF", "parking_extract_fan"), ("PEF", "parking_extract_fan"),
    ("CSEF", "smoke_exhaust_fan"), ("SMEF", "smoke_exhaust_fan"), ("SEF", "smoke_exhaust_fan"),
    ("SXF", "smoke_exhaust_fan"), ("CMAF", "makeup_air_fan"),
    ("SSPF", "staircase_pressurization_fan"), ("SPPF", "staircase_pressurization_fan"),
    ("SPF", "staircase_pressurization_fan"),
    ("LSPF", "lift_pressurization_fan"), ("LPF", "lift_pressurization_fan"),
    ("CPF", "corridor_pressurization_fan"),
    ("MUAF", "makeup_air_fan"), ("MAF", "makeup_air_fan"), ("MUF", "makeup_air_fan"),
    ("FAF", "fresh_air_fan"),
    ("JF", "jet_fan"),
    ("MSFD", "motorized_smoke_fire_damper"), ("MFSD", "motorized_smoke_fire_damper"),
    ("MSCD", "motorized_smoke_fire_damper"), ("MSD", "motorized_smoke_fire_damper"),
    # on smoke management / ventilation drawings (the only ones read for dampers): MD-01, SD-01
    ("MD", "motorized_smoke_fire_damper"), ("SD", "motorized_smoke_fire_damper"),
    ("ZCV", "zone_control_valve"), ("ACV", "alarm_check_valve"),
    ("GCP", "gas_control_panel"), ("ACP", "access_card_control_panel"),
)
_PREFIX_KEY = dict(_TAG_PREFIXES)
_QUANTITY = re.compile(r"\s*(?:NOS?\b|NO\.|PCS\b|SETS?\b|X\b|UNITS?\b)", re.I)
# The code after the prefix: segments of letters and digits (B4-01, R-01, L3-01),
# a digit somewhere in them -- "AHU ROOM" is a room, not a tag.
_TAG = re.compile(
    r"(?<![A-Z0-9-])(" + "|".join(p for p, _ in _TAG_PREFIXES) + r")"
    r"(\s?[-_/.]?\s?[A-Z0-9]{1,5}(?:[-_/.][A-Z0-9]{1,5}){0,3})(?![A-Z0-9])",
    re.I)
# Tags whose prefix says less than the words beside it might: "LPF" is a lift
# (or lobby) pressurization fan -- kept, at medium, with a word to check.
_AMBIGUOUS_PREFIX = {"LPF": "LPF may be a lift or a lobby pressurization fan"}

_WORDS: tuple[_Words, ...] = (
    # --- Fire Fighting
    _Words("electric_fire_pump", _p(r"\bELECTRIC(?:AL)?(?:\s+MOTOR)?(?:\s+DRIVEN)?\s+(?:FIRE\s+)?PUMPS?\b|\bDUTY\s*\(\s*ELECTRIC\s*\)")),
    _Words("diesel_fire_pump", _p(r"\bDIESEL(?:\s+ENGINE)?(?:\s+DRIVEN)?\s+(?:FIRE\s+)?PUMPS?\b|\bSTAND\s*-?BY\s*\(\s*DIESEL\s*\)")),
    _Words("jockey_pump", _p(r"\bJOCKEY\s+PUMPS?\b")),
    _Words("low_water_level", _p(r"\bLOW\s+WATER\s+LEVEL\b|\bWATER\s+LEVEL\s+(?:SWITCH|INDICAT\w*)\b")),
    _Words("alarm_check_valve", _p(r"\bACV\b|\bALARM\s+(?:CHECK\s+)?VALVES?\b")),
    _Words("zone_control_valve", _p(r"\bZCV\b|\bZONE\s+CONTROL\s+VALVES?\b")),
    _Words("gate_valve", _p(r"\bOS\s*&\s*Y\b|\bGATE\s+VALVES?\b")),
    _Words("foam_system", _p(r"\bFOAM\s+(?:SYSTEM|SPRAY|DELUGE)\b|\bDELUGE\s+FOAM\b|\bBY\s+FOAM\b"), group="water_system"),
    _Words("preaction_system", _p(r"\bPRE[\s-]?ACTION\b"), group="water_system"),
    _Words("deluge_system", _p(r"\bDELUGE\b"), group="water_system"),
    _Words("fm200_system", _p(r"\bFM\s*-?\s*200\b|\bHFC\s*-?\s*227"), group="gas_system"),
    _Words("clean_agent_system", _p(r"\bCLEAN\s+AGENT\b|\bNOVEC\b|\bFK\s*-?\s*5\s*-?\s*1\s*-?\s*12\b|\bINERGEN\b"), group="gas_system"),
    _Words("co2_system", _p(r"\bCO2\b|\bCARBON\s+DIOXIDE\b"), group="gas_system"),
    _Words("kitchen_hood", _p(r"\bKITCHEN\s+HOOD\b")),
    # --- Smoke Management / Ventilation
    _Words("parking_extract_fan", _p(r"\b(?:CAR\s*PARK|PARKING)\s+(?:SMOKE\s+)?(?:EXTRACT|EXHAUST)(?:ION)?\s+FANS?\b")),
    _Words("jet_fan", _p(r"\bJET\s*FANS?\b")),
    _Words("smoke_exhaust_fan", _p(r"\bSMOKE\s+(?:EXHAUST|EXTRACT)(?:ION)?\s+FANS?\b")),
    _Words("staircase_pressurization_fan", _p(rf"\bSTAIR\s*(?:CASE|WELL)?\s+{_PRESS}\s+FANS?\b"), group="press"),
    _Words("lift_pressurization_fan", _p(rf"\bLIFT\s*(?:SHAFT|WELL)?\s+{_PRESS}\s+FANS?\b"), group="press"),
    _Words("corridor_pressurization_fan", _p(rf"\bCORRIDOR\s+{_PRESS}\s+FANS?\b"), group="press"),
    _Words("makeup_air_fan", _p(r"\bMAKE[\s-]?UP\s+AIR\s+(?:FAN|UNIT)S?\b")),
    _Words("fahu", _p(r"\bFRESH\s+AIR\s+HANDLING\s+UNITS?\b"), group="ahu"),
    _Words("ahu", _p(r"\bAIR\s+HANDLING\s+UNITS?\b"), group="ahu"),
    _Words("fresh_air_fan", _p(r"\bFRESH\s+AIR\s+FANS?\b")),
    _Words("motorized_smoke_fire_damper",
           _p(r"\bMOTORI[SZ]ED\s+(?!VOLUME\b)(?:(?!VOLUME\b)[A-Z/&]+\s+){0,3}DAMPERS?\b|\bSMOKE\s*(?:/|AND|&)?\s*(?:FIRE\s+)?DAMPERS?\b")),
    # A damper drawn by its code alone, as the smoke management and ventilation drawings label
    # them: MD (motorized), MSD / MSFD / MFSD (motorized smoke / fire), SD (smoke). Never FD (a
    # fire damper on a fusible link) or VCD (volume control): those are not interfaced.
    _Words("motorized_smoke_fire_damper", _p(r"^(?:MSFD|MFSD|MSCD|MSD|SMD|MD|SD|M\.D\.?|S\.D\.?)$")),
    _Words("fire_curtain", _p(r"\b(?:FIRE|SMOKE)\s+CURTAINS?\b")),
    # --- Access Control / Architecture
    _Words("gas_control_panel", _p(r"\bGAS\s+(?:CONTROL|DETECTION|LEAK(?:AGE)?\s+DETECTION)\s+PANEL\b")),
    _Words("access_card_control_panel", _p(r"\bACCESS\s+(?:CARD\s+)?CONTROL\s+PANEL\b")),
    _Words("gate_barrier", _p(r"\b(?:GATE|BOOM|PARKING|VEHICLE|ENTRANCE|EXIT)\s+BARRIERS?\b|\bBARRIER\s+GATE\b")),
    _Words("sliding_door", _p(r"\b(?:AUTOMATIC|AUTO|MOTORI[SZ]ED)\s+SLIDING\s+DOORS?\b"), group="door"),
    _Words("entrance_door", _p(r"\b(?:AUTOMATIC\s+|MAIN\s+)?ENTRANCE\s+DOORS?\b"), group="door"),
    _Words("rolling_shutter", _p(r"\b(?:ROLLING|ROLLER)\s+SHUTTERS?\b"), group="door"),
    _Words("magnetic_door_holder", _p(r"\b(?:ELECTRO[\s-]?)?MAGNETIC\s+DOOR\s+HOLDERS?\b|\bDOOR\s+HOLDERS?\b"), group="door"),
    # The words do not say these are interfaced: a sliding door may be manual,
    # a fire door may have no holder. Asked about, never scheduled as read.
    _Words("sliding_door", _p(r"\bSLIDING\s+DOORS?\b"), LOW, group="door"),
    _Words("fire_door", _p(r"\bFIRE\s+(?:RATED\s+)?DOORS?\b"), LOW, group="door"),
)

# A note that a system protects a room ("LV ROOM IS PROTECTED BY FM200 SYSTEM",
# "FM200 DRAWING SHALL BE SUBMITTED SEPARATELY"): evidence the system is there.
_NOTE = _p(r"\bPROTECTED\s+BY\b|\bSUBMITTED\s+SEPARATELY\b|\bSEPARATE\s+DRAWING\b|\bDETAILED\s+DRAWING\b")
_ROOM_OF_NOTE = _p(r"^\s*(?:THIS\s+)?(.{2,40}?)\s+(?:IS|ARE)\s+PROTECTED\s+BY\b")
# The fire alarm's own words: a legend or note about modules names the
# equipment it serves ("CONTROL MODULE FOR LIFT", "MONITORING MODULE FOR FM 200
# SYSTEM") without being that equipment.
_FIRE_ALARM_WORDS = _p(r"\bMODULE\b|\bDETECTOR\b|\bCALL\s*POINT\b|\bSOUNDER\b|\bINTERFACE\b|\bRELAY\b|\bFIRE\s+ALARM\b|"
                       r"\bFLOW\s+SWITCH\b|\bTAMPER\b|\bPHONE\s+JACK\b|\bFACP\b")
# A numbered or headed note ("1. ALL ZCV SHALL BE ...", "NOTE: ...") is a specification, not a label.
_SPEC_NOTE = _p(r"^\s*(?:\d{1,2}\s*[.)]|NOTES?\s*[:.-]|GENERAL\s+NOTES?)")
# Words that make a text a title or a portable item, not equipment: "ALARM CHECK
# VALVE DETAIL", "FIRE PUMP SCHEDULE (FP)", "10 LBS CO2 FIRE EXTINGUISHER".
_NOT_EQUIPMENT = _p(r"\bEXTINGUISHERS?\b|\bDETAILS?\b|\bSCHEDULE\b|\bSCHEMATIC\b|\bDIAGRAM\b|\bLEGEND\b")
_SIZE = _p(r"(?:Ø|%%C|DIA\.?\s*)\s*(\d{2,3})")
MAX_LABEL = 160

# An architectural lift label: the whole text is the lift ("LIFT 1", "LIFT-A",
# "FIRE LIFT", "PASSENGER LIFT 3"), never a room named for lifts ("LIFT LOBBY").
_LIFT = _p(r"^(?:(PASSENGER|SERVICE|GOODS|FIRE(?:MAN'?S)?|FIRE\s*FIGHTING|FIREFIGHTING|VIP)\s+)?(?:LIFT|ELEVATOR)"
           r"(?:\s*(?:NO\.?|NUMBER)?\s*[-#]?\s*([A-Z]?\d{1,2}[A-Z]?|[A-Z]))?$")
_MACHINE_ROOM = _p(r"\bLIFT\s+MACHINE\s+ROOM\b|\bMACHINE\s+ROOM\b|^\s*L\.?M\.?R\.?\s*$")


def normalize(text: str) -> str:
    return " ".join(str(text or "").replace("%%c", "Ø").replace("%%C", "Ø").split()).upper()


def _tags(text: str, wanted: set[str]) -> list[Detection]:
    out = []
    for m in _TAG.finditer(text):
        prefix = m.group(1).upper()
        key = _PREFIX_KEY[prefix]
        if key not in wanted:
            continue
        if not re.search(r"\d", m.group(2)):
            continue
        # a quantity, not a tag: "ZCV 2 NOS", "JF 3 SETS"
        if re.fullmatch(r"\s+\d+", m.group(2)) and _QUANTITY.match(text, m.end()):
            continue
        tag = " ".join(f"{prefix}{m.group(2)}".upper().split())   # as written
        note = _AMBIGUOUS_PREFIX.get(prefix, "")
        out.append(Detection(key, LABEL, MEDIUM if note else HIGH, tag, note))
    return out


def detect(text: str, wanted: set[str]) -> list[Detection]:
    """The equipment a text names, among `wanted` (the discipline's rows)."""
    t = normalize(text)
    if (not t or len(t) > MAX_LABEL or _SPEC_NOTE.match(t) or _FIRE_ALARM_WORDS.search(t)
            or _NOT_EQUIPMENT.search(t)):
        return []
    found = _tags(t, wanted)
    tagged = {d.key for d in found}
    is_note = bool(_NOTE.search(t))
    size = _SIZE.search(t)
    room = _ROOM_OF_NOTE.match(t)
    # a tagged item's words are its own: "FAHU-01 FRESH AIR HANDLING UNIT" is not also an AHU
    groups: set[str] = {w.group for w in _WORDS if w.group and w.key in tagged}
    for w in _WORDS:
        if w.key not in wanted or w.key in tagged or (w.group and w.group in groups):
            continue
        if not w.pattern.search(t):
            continue
        if w.group:
            groups.add(w.group)
        detail = f"Ø{size.group(1)}" if size else ""
        if is_note and room:
            detail = room.group(1).title()
        found.append(Detection(w.key, NOTE if is_note else LABEL, w.confidence, None, detail))
        tagged.add(w.key)
    return found


def tag_key(tag: str) -> str:
    """A tag as it is compared: "AHU 02", "AHU-02" and "AHU02" are one tag."""
    return re.sub(r"[^A-Z0-9]", "", (tag or "").upper())


def lift_label(text: str) -> str | None:
    """The lift a label names ("LIFT 3" -> "LIFT 3", "FIRE LIFT" -> "FIRE
    LIFT"), or None when the text is not a lift label."""
    t = normalize(text)
    if not _LIFT.match(t):
        return None
    return re.sub(r"\s*[-#]\s*", " ", t).replace("ELEVATOR", "LIFT")


# A pump room: on a fire fighting drawing, where the fire pump set is drawn --
# often as graphics alone, its pumps named nowhere (EP-30880's 3rd basement).
# Not a domestic / irrigation / drainage one.
_PUMP_ROOM = _p(r"\bPUMPS?\s+ROOM\b")
_NOT_FIRE_PUMP_ROOM = _p(r"\bDOMESTIC\b|\bPOTABLE\b|\bIRRIGATION\b|\bTSE\b|\bDRAINAGE\b|\bSUMP\b|\bPOOL\b|\bCHILLED\b")


def is_pump_room(text: str) -> bool:
    t = normalize(text)
    return bool(_PUMP_ROOM.search(t)) and not _NOT_FIRE_PUMP_ROOM.search(t) and len(t) <= 40


def is_machine_room(text: str) -> bool:
    return bool(_MACHINE_ROOM.search(normalize(text)))
