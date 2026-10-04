"""The engineers' rulings on the Drawings Review: every change they marked
not needed, and every one they confirmed, kept company-wide.

They make the review better in two ways:
  * every later review gives them to the model with the coverage rules, as
    what this company wants -- "no speaker in an electrical room", "the pump
    room's sounder is a sounder-flasher" -- so it stops proposing what the
    engineers keep turning down;
  * a "not needed" settles the same change in the same kind of room on
    every other floor at once (shown as "by ruling", reopened one by one).

The rulings are part of what the model is asked, so the cache knows them:
a new ruling makes the next review ask again (`prompt`'s version).
"""
from __future__ import annotations

import hashlib
import re

from sqlalchemy.orm import Session

from app.models import ReviewRuling
from app.review import ai as A

MAX_IN_PROMPT = 80


def room_key(name: str) -> str:
    """A room as the rulings compare it: "STAIR-1" and "STAIR 2" are a
    stair, "ELEC.ROOM" an elec room -- numbers and punctuation left out."""
    words = re.sub(r"[^A-Z ]", " ", (name or "").upper()).split()
    return " ".join(w for w in words if len(w) > 1)[:80]


def record(db: Session, project_id: int, drawing_id: int, finding: dict, decision: str, *, note: str = "",
           instruction: str = "", user_id: int | None = None) -> None:
    row = (db.query(ReviewRuling).filter(ReviewRuling.project_id == project_id, ReviewRuling.drawing_id == drawing_id,
                                         ReviewRuling.finding_id == finding["id"]).one_or_none())
    if row is None:
        row = ReviewRuling(project_id=project_id, drawing_id=drawing_id, finding_id=finding["id"])
        db.add(row)
    row.decision = decision
    row.room = (finding.get("room") or "")[:160]
    row.room_key = room_key(finding.get("room") or "")
    row.room_type = (finding.get("room_type") or "")[:80]
    row.system = finding["system"]
    row.action = finding["action"]
    row.device = (finding.get("device") or "")[:120]
    row.instruction = (instruction or finding.get("instruction") or "")[:300]
    row.note = (note or "")[:500]
    row.created_by_id = user_id


def forget(db: Session, project_id: int, drawing_id: int, finding_id: str) -> None:
    (db.query(ReviewRuling).filter(ReviewRuling.project_id == project_id, ReviewRuling.drawing_id == drawing_id,
                                   ReviewRuling.finding_id == finding_id).delete())


def listed(db: Session) -> list[ReviewRuling]:
    return db.query(ReviewRuling).order_by(ReviewRuling.created_at.desc(), ReviewRuling.id.desc()).all()


def _line(r: ReviewRuling) -> str:
    what = f"{r.action.upper()} {r.device or A.SYSTEMS.get(r.system, r.system).lower()}"
    where = r.room or r.room_type or "this kind of space"
    if r.decision == "dismissed":
        return f"- NOT NEEDED: {what} in {where}" + (f' -- the engineer: "{r.note}"' if r.note else "")
    return f"- CONFIRMED: {what} in {where}" + (f' -- "{r.instruction}"' if r.instruction else "")


def prompt(db: Session) -> tuple[str, str]:
    """(the rulings as the model reads them, their version). The latest
    ruling on each kind of change in each kind of room, newest first."""
    seen: set[tuple] = set()
    lines = []
    for r in listed(db):
        key = (r.room_key or r.room_type.upper(), r.system, r.action, r.device.lower())
        if key in seen:
            continue
        seen.add(key)
        lines.append(_line(r))
        if len(lines) >= MAX_IN_PROMPT:
            break
    if not lines:
        return "", "none"
    text = ("\n\nENGINEERS' RULINGS -- the engineers' decisions on changes proposed in earlier reviews. They show "
            "what this company wants: follow them over your own reading. Do not propose again what they marked NOT "
            "NEEDED in that kind of room; propose what they CONFIRMED wherever the same situation occurs.\n"
            + "\n".join(lines))
    return text, hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def not_needed(db: Session) -> dict[tuple[str, str, str], ReviewRuling]:
    """{(room key, system, action): the latest NOT NEEDED ruling}, to settle
    the same change in the same kind of room on every floor."""
    out: dict[tuple[str, str, str], ReviewRuling] = {}
    for r in listed(db):
        if r.decision == "dismissed" and r.room_key:
            out.setdefault((r.room_key, r.system, r.action), r)
    return out
