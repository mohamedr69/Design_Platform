"""The Fire Alarm Interface Matrix: what the fire alarm system does with
each kind of third-party equipment -- the contacts it needs, how many
signals it monitors and controls, and the action the other trade takes.

Transcribed from the company's "Fire Alarm Interface Contacts" sheet (40
rows). This is Stage 2 of the interface schedule: the drawings say WHAT
exists and WHERE (app.interfaces.scan); only this table says what the fire
alarm system must DO with it. Nothing here is inferred from a drawing, and
nothing on a drawing is scheduled without a row here.

Rows 36 and 38 of the sheet are not legible on the copy transcribed and are
left out rather than guessed; `UNCLEAR_ROWS` says so on the page and in the
workbook, so the engineer can supply them.

`contacts` keeps the sheet's own naming (CT1, CT2, CR, "2 NOS CT2", ...):
CT1 is a single-input monitor module, CT2 a dual-input monitor module and
CR a relay (control) module, so the modules a line needs are read off it
(`modules`) -- one CT2 carries both of a valve's signals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# The disciplines whose IFC drawings the schedule reads.
FF, SM, HVAC, ACS, GB, ARCH = "FF", "SM", "HVAC", "ACS", "GB", "ARCH"
DISCIPLINE_NAMES = {FF: "Fire Fighting", SM: "Smoke Management", HVAC: "Ventilation / HVAC", ACS: "Access Control",
                    GB: "Gate Barrier", ARCH: "Architecture"}


@dataclass(frozen=True)
class Rule:
    no: int
    key: str
    name: str
    contacts: str                # as the sheet writes it
    monitoring: int
    control: int
    alarm: str = ""
    supervisory: str = ""
    action: str = ""
    # The disciplines whose drawings show this equipment.
    disciplines: tuple[str, ...] = ()
    # Out of scope for the schedule (CO2, kitchen hood, PA/BGM, BMS, escalators).
    excluded: bool = False
    # Scheduled once per lift, not per floor.
    per_lift: bool = False

    @property
    def signals(self) -> int:
        return self.monitoring + self.control

    def to_dict(self) -> dict:
        return {"no": self.no, "key": self.key, "name": self.name, "contacts": self.contacts,
                "monitoring": self.monitoring, "control": self.control, "alarm": self.alarm,
                "supervisory": self.supervisory, "action": self.action, "disciplines": list(self.disciplines),
                "excluded": self.excluded, "modules": modules(self.contacts)}


_TROUBLE_BV = "Butterfly Valve Trouble Signal other than fully opened Condition - Connected to Butterfly Valve"
_TAMPER = "Tamper Switch Trouble Signal other than fully opened Condition - Connected to Tamper Switch"
_WATER_RELEASE = "Pressure Switch Activation - Water Release"

RULES: tuple[Rule, ...] = (
    Rule(1, "electric_fire_pump", "Electric Fire Pump", "CT2", 2, 0,
         "Pump Running Connected to the controller", "Pump Trip/Fault Connected to the controller", disciplines=(FF,)),
    Rule(2, "diesel_fire_pump", "Diesel Fire Pump", "CT2", 2, 0,
         "Pump Running Connected to the controller", "Pump Trip/Fault Connected to the controller", disciplines=(FF,)),
    Rule(3, "jockey_pump", "Jockey Pump", "CT1", 1, 0,
         "", "Pump Trip/Fault Connected to the controller", disciplines=(FF,)),
    Rule(4, "low_water_level", "Low Water Level Indication", "CT1", 1, 0,
         "", "Low Water Level Indication", disciplines=(FF,)),
    Rule(5, "alarm_check_valve", "Alarm Check Valve", "CT2", 2, 0,
         f"{_WATER_RELEASE} - Connected to the Alarm Pressure Switch", _TAMPER, disciplines=(FF,)),
    Rule(6, "gate_valve", "Gate Valve", "CT1", 1, 0, "", _TAMPER, disciplines=(FF,)),
    Rule(7, "zone_control_valve", "Zone Control Valve", "CT2", 2, 0,
         "Flow Switch Activation - Connected to Water Flow Switch/Detector",
         "Butterfly valve Trouble Signal other than fully opened Condition - Connected to Butterfly Valve",
         disciplines=(FF,)),
    Rule(8, "co2_system", "CO2 System", "CT2", 2, 0, "Panel alarm", "Panel Trouble", disciplines=(FF,), excluded=True),
    Rule(9, "foam_system", "Foam System", "2 NOS CT2", 4, 0,
         f"1. Panel Alarm - Connected to Panel 2. {_WATER_RELEASE} - Connected to the Flow Switch",
         f"1. Panel Trouble - Connected to Panel 2. {_TROUBLE_BV}", disciplines=(FF,)),
    Rule(10, "fm200_system", "FM 200 System", "CT2,CT1", 3, 0,
         "1. Panel alarm - Connected to Panel 2. Gas Discharge - Discharge Pressure Switch - Connected to Panel",
         "Panel Trouble - Connected to Panel", disciplines=(FF,)),
    Rule(11, "deluge_system", "Deluge System", "CT2", 2, 0,
         f"{_WATER_RELEASE} - Connected to Pressure Switch", _TROUBLE_BV, disciplines=(FF,)),
    Rule(12, "clean_agent_system", "Clean Agent System", "CT2,CT1", 3, 0,
         "1. Panel alarm - Connected to Panel 2. Gas Discharge - Discharge Pressure Switch - Connected to Panel",
         "Panel Trouble - Connected to Panel", disciplines=(FF,)),
    Rule(13, "preaction_system", "Preaction System", "2 NOS CT2", 4, 0,
         f"1. Panel Alarm - Connected to Panel 2. {_WATER_RELEASE} - Connected to the Flow Switch",
         f"1. Panel Trouble - Connected to Panel 2. {_TROUBLE_BV}", disciplines=(FF,)),
    Rule(14, "kitchen_hood", "Kitchenhood System", "CT2", 2, 0, "Panel alarm", "Panel Trouble", disciplines=(FF,),
         excluded=True),
    Rule(15, "ahu", "AHU", "CR", 0, 1, action="To Shut Down AHU", disciplines=(HVAC,)),
    Rule(16, "fahu", "FAHU", "CR", 0, 1, action="To Shut Down FAHU", disciplines=(HVAC,)),
    Rule(17, "motorized_smoke_fire_damper", "Motorized Smoke Fire Dampers", "CR", 0, 1,
         action="To open or To Close Motorized Smoke Fire Dampers", disciplines=(SM, HVAC)),
    Rule(18, "makeup_air_fan", "Makeup Air Fans", "CR", 0, 1, action="To Start Makeup Air Fan", disciplines=(SM, HVAC)),
    Rule(19, "corridor_pressurization_fan", "Corridor Pressurization Fans", "CR", 0, 1,
         action="To Start Corridor Pressurization Fan", disciplines=(SM, HVAC)),
    Rule(20, "lift_pressurization_fan", "Lift Pressurization Fans", "CR", 0, 1,
         action="To Start Lift Pressurization Fan", disciplines=(SM, HVAC)),
    Rule(21, "parking_extract_fan", "Parking Extract Fans", "CR", 0, 1, action="To Start Parking Extract Fan",
         disciplines=(SM, HVAC)),
    Rule(22, "fresh_air_fan", "Fresh Air Fan", "CR", 0, 1, action="To Stop Fresh Air Fan", disciplines=(HVAC, SM)),
    Rule(23, "jet_fan", "Jetfans", "CR", 0, 1, action="To Start Jetfan", disciplines=(SM, HVAC)),
    Rule(24, "smoke_exhaust_fan", "Smoke Exhaust Fan", "CR", 0, 1, action="To Start Smoke Extract Fan",
         disciplines=(SM, HVAC)),
    Rule(25, "staircase_pressurization_fan", "Staircase Pressurization Fan", "CR", 0, 1,
         action="To Start Stair Case Pressurization Fan", disciplines=(SM, HVAC)),
    Rule(26, "lift_system", "Lift System", "2NO.CR FOR EACH LIFT", 0, 2,
         action="1. To recall lift to the Ground floor if there is fire in any of other floors "
                "2. To recall the lift to the Alternate Floor if there is a fire in the GF",
         disciplines=(ARCH,), per_lift=True),
    Rule(27, "gas_control_panel", "Gas Control Panel", "CT2,CR", 2, 1, "Panel Alarm", "Panel Trouble",
         "To Close Solenoid Valve", disciplines=(ARCH, FF)),
    Rule(28, "access_card_control_panel", "Access Card Control Panel", "CR", 0, 1, action="To open all exit doors",
         disciplines=(ACS, GB)),
    Rule(29, "entrance_door", "Entrance Doors", "CR", 0, 1, action="To closed Entrance door", disciplines=(ACS, GB, ARCH)),
    Rule(30, "gate_barrier", "Gate Barrier", "CR", 0, 1,
         action="To open exit gate barrier and additional control module shall be provided to close Entrance Gate Barrier",
         disciplines=(GB, ACS, ARCH)),
    Rule(31, "sliding_door", "Sliding Doors", "CR", 0, 1, disciplines=(ARCH, ACS)),
    Rule(32, "rolling_shutter", "Rolling Shutters", "CR", 0, 1, disciplines=(ARCH, ACS)),
    Rule(33, "fire_curtain", "Fire Curtains", "CR", 0, 1, disciplines=(SM, HVAC)),
    Rule(34, "fire_door", "Fire Doors", "CR", 0, 1, disciplines=(ARCH, ACS)),
    Rule(35, "magnetic_door_holder", "Magnetic Door Holders", "CR", 0, 1, disciplines=(ARCH, ACS)),
    Rule(37, "public_address", "Public Address System", "CR", 0, 1, action="To mute BGM system", excluded=True),
    Rule(39, "bms", "Building Management System", "CR", 0, 1, excluded=True),
    Rule(40, "escalator", "Escalators", "CR", 0, 1, excluded=True),
)
BY_KEY: dict[str, Rule] = {r.key: r for r in RULES}
UNCLEAR_ROWS = (36, 38)
MATRIX_NAME = "Fire Alarm Interface Contacts (company standard)"


def rules_for(discipline: str) -> set[str]:
    """The equipment a discipline's drawings are read for."""
    return {r.key for r in RULES if discipline in r.disciplines}


_COUNTED = re.compile(r"(\d+)\s*NO'?S?\.?\s*(CT1|CT2|CR)\b|\b(CT1|CT2|CR)\b", re.I)


def modules(contacts: str) -> dict[str, int]:
    """The modules a line needs, off the sheet's contact naming: "CT2" is
    one dual-input module, "2 NOS CT2" two, "CT2,CR" one of each, "2NO.CR
    FOR EACH LIFT" two relays."""
    out = {"CT1": 0, "CT2": 0, "CR": 0}
    for m in _COUNTED.finditer(contacts or ""):
        if m.group(2):
            out[m.group(2).upper()] += int(m.group(1))
        else:
            out[m.group(3).upper()] += 1
    return out
