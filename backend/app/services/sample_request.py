"""Sample board, Request Material: the email asking stores to arrange the
samples for a project's Fire Alarm & Emergency Lighting sample board.

Shown on Logs > Samples while the fire alarm has no sample board among the
project's transmittals (`projects.sample_board_checks`, the platform's own
reading of the transmittal wording). The model drafts the email from the
project's Schedules of Material -- fire alarm and emergency lighting -- and
nothing else; Python then checks every part number it wrote against those
schedules before the engineer sees the draft. Nothing is sent: the draft
opens for the engineer to edit and send.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai import project_policy
from app.ai.provider import AiProvider, TextPart
from app.compliance import assist
from app.models import Project
from app.services import system_rules

TASK = "sample_request_email"
PROMPT_VERSION = "sample-request-2026-09-30.3"
TO = "jaffer.ali@al-majid.com"
FAS, ELS = "FAS", "ELS"

# The prompt as the engineers wrote it, the same for every project and maker.
SYSTEM_PROMPT = """You are a technical office assistant at a fire alarm contracting company in the UAE.
Your only task is to draft an email asking the stores/procurement contact to arrange
material samples for a project's Fire Alarm & Emergency Lighting sample board.

This prompt is used for ALL projects and ALL manufacturers. Never assume a brand or
part number. Work only from the schedules you receive.

INPUTS
- PROJECT_NAME
- EP_NUMBER
- FAS_SCHEDULE  (proposed material schedule – fire alarm system)
- ELS_SCHEDULE  (proposed material schedule – emergency lighting; may be empty)

HARD RULES
1. Take part numbers ONLY from FAS_SCHEDULE and ELS_SCHEDULE. Never invent, guess,
   complete or "correct" a part number. Copy it exactly, including "+" accessories.
2. Match by the item's FUNCTION as described in the DESCRIPTION column, never by its
   position in the list or by brand knowledge.
3. Always output every line of the sample list, in the fixed order below.
4. No match → keep the line and write: (not in schedule – please confirm)
5. More than one match that the tie-break rules cannot settle → list all candidates
   separated by " / " and add: (multiple options – please confirm)
6. A match made only through a fallback rule → add: (please confirm)
7. ELS_SCHEDULE empty or missing → on every EML line write:
   (ELS schedule not provided – please confirm)
8. If a detector's part number already includes its base (one catalogue number for
   head + base), write that number once and do not add a separate base.
9. Output the email only: no explanations, no markdown, nothing before or after.

SAMPLE LIST AND MATCHING RULES

Fire Alarm System (from FAS_SCHEDULE)
- Smoke detector + Sounder base
    Detector: optical/photoelectric smoke detector (not multisensor, not duct,
    not beam, not aspirating).
    Base: the sounder base (e.g. "Sounder Base", "Audible Base", "Sounder/Beacon Base").
- Heat detector + Standard base
    Detector: point heat detector (fixed temperature and/or rate-of-rise).
    Base: the standard/plain detector base, with NO isolator and NO sounder.
- Multi-sensor + Isolator base
    Detector: multisensor / multi-criteria detector (e.g. optical + heat).
    Base: the isolator base (e.g. "Isolator Base", "Base with Isolator").
- Manual call point + single gang back box
    The manual call point / break glass / manual pull station. Do not add covers,
    stoppers, gaskets or keys.
    Back box: the SINGLE GANG back box (see Back boxes).
- Wall mounted speaker + double gang back box
    Wall speaker (not horn, not sounder, not speaker/strobe unless it is the only
    wall speaker; then apply rule 6).
    Back box: the DOUBLE GANG back box (see Back boxes).
- Ceiling speaker
    Ceiling / recessed speaker.
- Fire telephone jack + single gang back box
    Fire telephone jack / handset receptacle / telephone outlet (not the handset,
    not the handset cabinet).
    Back box: the SINGLE GANG back box (see Back boxes).
- Back boxes (for the three lines above)
    Single gang: a back box described as single gang / 1-gang / 2"x4".
    Double gang: a back box described as double gang / 2-gang / 4"x4".
    Prefer the concealed / flush back box over the surface mount box. If only a
    surface mount box of that gang is in the schedule, use it and apply rule 6.
    Never use the weatherproof back box here.
- Weatherproof speaker + back box
    Speaker: the weatherproof / outdoor / IP-rated speaker.
    Fallback: if no speaker is labelled weatherproof, use the speaker (or speaker/
    strobe) intended for the weatherproof box and apply rule 6.
    Back box: the weatherproof / outdoor back box.
- MDF board
    Write "MDF board" with no part number.

Emergency Lighting (EML) (from ELS_SCHEDULE)
- Rounded emergency light
    The ROUND RECESSED emergency fitting (e.g. descriptions or names with "round",
    "recessed round", "downlight", "RTECH / Roundtech").
    Not a surface bulkhead (e.g. Menvier NEXI is NOT the rounded light).
- Surface emergency light
    The surface-mounted emergency light (e.g. "Surface Mounted Emergency Light").
    Not a bulkhead/IP65 round fitting and not an exit sign.
    Tie-break: if the ELS schedule has an emergency lighting panel/controller
    (addressable or central-monitored system), choose the variant that is
    compatible with that panel over the "self-contained" variant.
    Indoor body: the sample is the indoor (IP42 / lowest IP) body of that fitting.
    If the surface light is listed only at IP65 and the same body at the lower IP
    appears in ELS_SCHEDULE only as the base of an exit sign (the catalogue number
    before its "+" accessories, e.g. "SL2-42D3D-CGL-M" in "SL2-42D3D-CGL-M+SL23I"),
    write that base number without the accessories.
- Directional emergency light
    The DIRECTIONAL exit sign ("Exit Directional", "directional", arrow legend).
    Tie-break: prefer the corridor / wall / ceiling type over the hanging, driveway
    or car-park type. Copy the full catalogue number with all "+" accessories.

EMAIL FORMAT (follow exactly)

To: jaffer.ali@al-majid.com
Subject: <EP_NUMBER> <PROJECT_NAME>

Dear Jaffar,

Kindly arrange samples as per below.

Fire Alarm System
- Smoke detector: <detector> + Sounder base <base>
- Heat detector: <detector> + Standard base <base>
- Multi-sensor: <detector> + Isolator base <base>
- Manual call point: <part> + back box <single gang box>
- Wall mounted speaker: <part> + back box <double gang box>
- Ceiling speaker: <part>
- Fire telephone jack: <part> + back box <single gang box>
- Weatherproof speaker: <part> + back box <part>
- MDF board

Emergency Lighting (EML)
- Rounded emergency light: <part>
- Surface emergency light: <part>
- Directional emergency light: <part>
- MDF board

PROJECT_NAME: use the project name only, in title case, without the floor/
configuration text in brackets.
Example: "BINGHATTI TITANIA (3B + G+ 4P + 32 RF + MF+R)" → "Binghatti Titania".
EP_NUMBER: as given, e.g. "EP-30880". Subject example: "EP-30880 Binghatti Titania".
"""
# The platform's calls answer in JSON: the email is its one field.
OUTPUT_NOTE = "\nOUTPUT: put the whole email, exactly as above, in the `email` field of the reply."
SCHEMA = {
    "type": "object",
    "properties": {"email": {"type": "string"}},
    "required": ["email"],
    "additionalProperties": False,
}
# The engineer is asked to look at a line the model marked for confirmation.
_CONFIRM = re.compile(r"\((?:[^)]*please confirm[^)]*)\)", re.I)
_PART = re.compile(r"[A-Z0-9][A-Z0-9./+-]*\d[A-Z0-9./+-]*|\d[A-Z0-9./+-]*", re.I)


class RequestError(Exception):
    pass


@dataclass
class Draft:
    to: str
    subject: str
    body: str
    # Lines the model marked "(please confirm)", and part numbers not in either schedule.
    to_confirm: list[str] = field(default_factory=list)
    not_in_schedule: list[str] = field(default_factory=list)
    els_in_scope: bool = True
    model: str = ""
    from_cache: bool = False


def schedule_text(project: Project, code: str) -> tuple[str, set[str]]:
    """A system's Schedule of Material as the model reads it -- one line a
    part, CAT. NO. | DESCRIPTION | MANUFACTURER under its block's heading --
    and its catalogue numbers, to check the reply against."""
    from app.services.submittal_package import schedule_blocks

    lines: list[str] = ["CAT. NO. | DESCRIPTION | MANUFACTURER"]
    parts: set[str] = set()
    for letter, title, items in schedule_blocks(project, code):
        lines.append(f"[{letter}] {title}")
        for item in items:
            if not item.catalog_no:
                continue
            lines.append(f"{item.catalog_no} | {' '.join((item.description or '').split())} | {item.manufacturer or ''}")
            parts.add(_norm(item.catalog_no))
    return ("\n".join(lines) if parts else ""), parts


def _norm(part: str) -> str:
    return re.sub(r"\s+", "", part or "").upper()


def unavailable(project: Project, provider: AiProvider | None = None) -> str | None:
    """Why the email cannot be drafted, or None."""
    if not assist.available(provider):
        return "AI is not configured on this server"
    if not project_policy.allowed(project):
        return project_policy.BLOCKED_MESSAGE
    return None


def draft(db: Session, project: Project, provider: AiProvider | None = None) -> Draft:
    reason = unavailable(project, provider)
    if reason:
        raise RequestError(reason)
    fas, fas_parts = schedule_text(project, FAS)
    if not fas:
        raise RequestError("The fire alarm Schedule of Material is empty: the BOQ and Proposed Materials give it.")
    codes = set(system_rules.project_codes(project))
    els, els_parts = schedule_text(project, ELS) if ELS in codes else ("", set())
    parts = [TextPart("PROJECT_NAME", project.project_name or ""), TextPart("EP_NUMBER", f"EP-{project.ep_number}"),
             TextPart("FAS_SCHEDULE", fas), TextPart("ELS_SCHEDULE", els)]
    key = hashlib.sha256("\n".join(p.text for p in parts).encode("utf-8")).hexdigest()
    session = assist.open_session(db, project.id, key, provider)
    result = assist.call_task(session, TASK, SYSTEM_PROMPT + OUTPUT_NOTE, parts, SCHEMA, 1500,
                              prompt_version=PROMPT_VERSION, tier="standard")
    email = (result.data or {}).get("email") if isinstance(result.data, dict) else None
    if not email or not str(email).strip():
        raise RequestError(f"The email could not be drafted: {result.error or 'no answer'}")
    out = parse(str(email))
    out.model, out.from_cache, out.els_in_scope = result.model, result.from_cache, bool(els)
    check(out, fas_parts | els_parts)
    return out


def parse(email: str) -> Draft:
    """To / Subject / body off the drafted email. The recipient is the
    stores contact whatever the reply says."""
    text = email.strip().strip("`").strip()
    subject, body_lines = "", []
    lines = text.splitlines()
    i = 0
    while i < len(lines) and (not lines[i].strip() or re.match(r"^\s*(To|Subject)\s*:", lines[i], re.I)):
        m = re.match(r"^\s*Subject\s*:\s*(.*)$", lines[i], re.I)
        if m:
            subject = m.group(1).strip()
        i += 1
    body_lines = [_tags_last(line) for line in lines[i:]]
    return Draft(to=TO, subject=subject, body="\n".join(body_lines).strip())


def _tags_last(line: str) -> str:
    """A sample line's "(… please confirm)" at its end, wherever the model put
    it: "Weatherproof speaker: 757-3A-SS70 + back box 757A-WB (please confirm)"."""
    if not line.lstrip().startswith("-"):
        return line
    tags = _CONFIRM.findall(line)
    if not tags:
        return line
    rest = " ".join(_CONFIRM.sub("", line).split())
    return f"{rest} {' '.join(tags)}"


def check(d: Draft, parts: set[str]) -> None:
    """Python's word on the draft: every part number it names is in a
    schedule, and the lines it asks to confirm are listed for the engineer."""
    for line in d.body.splitlines():
        if not line.lstrip().startswith("-") or ":" not in line:
            continue
        label, value = line.split(":", 1)
        if _CONFIRM.search(value):
            d.to_confirm.append(line.strip("- ").strip())
        value = _CONFIRM.sub("", value)
        # "SL2-42D3D-CGL-M +SL2PPLR+SL2RB" is one catalogue number with its accessories
        joined = re.sub(r"\s*\+\s*(?=[A-Z0-9]*\d)", "+", value, flags=re.I)
        for candidate in (c.strip() for c in re.split(r"\s+/\s+|\s+\+\s+|\s{1,}", joined)):
            if not candidate or not _PART.fullmatch(candidate):
                continue
            n = _norm(candidate)
            if n not in parts and not any(n in p for p in parts):
                d.not_in_schedule.append(f"{label.strip('- ').strip()}: {candidate}")
