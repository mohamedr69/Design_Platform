"""What a plotted sheet shows the review: its rooms, its legend, its plan.

The rooms are the room names printed on the plan ("LOBBY", "LV ROOM",
"ELEC.ROOM"), where they print -- the PDF's own text, so a crop around a
name lands on that room with no coordinate arithmetic. The legend is the
table under "LEGEND" in the title panel: it tells the model what each
symbol is on this project. Lift cars, dimensions, notes, levels and areas
are not rooms.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import pymupdf

ROOM_WORDS = re.compile(
    r"ROOM|LOBBY|CORRIDOR|\bCORR\b|STAIR|STORE|TOILET|\bW\.?C\b|BATH|KITCHEN|PANTRY|OFFICE|SHOP|RETAIL|"
    r"SUBSTATION|ENTRANCE|\bGYM\b|POOL|PARKING|LOUNGE|BEDROOM|LIVING|DINING|BALCONY|MAID|LAUNDRY|DRESS|"
    r"GARBAGE|PUMP|\bTANK\b|MECH|ELEC|\bLV\b|\bRMU\b|GUARD|TELE|SECURITY|RECEPTION|\bHALL\b|\bSPA\b|SAUNA|"
    r"\bCLUB\b|\bPLAY|CHANGING|LOCKER|STAFF|DRIVER|SERVICE|MAJLIS|PRAYER|CAFE|RESTAURANT|MULTI.?PURPOSE|"
    r"\bAHU\b|FAHU|PLANT|FIRE COMMAND|\bFCC\b|STUDY|STORAGE|JANITOR|CLEANER|REFUSE|GENERATOR|TRANSFORMER|"
    r"\bMETER|SERVER|LOADING|\bFOYER\b|\bPOD\b|ATRIUM|MEETING|WAITING|PASSAGE|VESTIBULE", re.I)
NOT_ROOM = re.compile(
    r"^LIFT\s*[-#]?\s*(?:\d{1,2}|[A-Z])$|FFL|SSL|\bLEVEL\b|\bDWG\b|DRAWING|\bPLAN\b|SCALE|NOTES?\b|SHALL|PROVID|"
    r"REFER|ABOVE|BELOW|DOUBLE HEIGHT|EXISTING|PLOT|GATE LEVEL|\d{3,}|SQ\.?\s*M|CONNECT|MODULE|FIRE ALARM|"
    r"SPEAKER|DETECTOR|LIGHT|\bSIGN\b|\bTO\b|\bFROM\b|\bWITH\b|INSIDE|CABLE|DUCT\b|SHAFT|RISER|SLEEVE|"
    r"PROPOSED|EXISTING|ACCESS\b(?!.*ROOM)|LEGEND|DESCRIPTION|APPROVAL|CONSULTANT|PROJECT|OWNER|STATUS|"
    r"MEP SERVICES|^SERVICES$|TOP OF|\bAT EVERY\b|\(TYP\)|NON-PARKING|ANALOGUE|ADDRESSABLE|SCHEMATIC|^PARKING ENT", re.I)
_LEGEND = re.compile(r"^\s*LEGENDS?\s*:?\s*$", re.I)
_TAIL = re.compile(r"^(?:ROOM|AREA|LOBBY|STORE|SPACE|HALL|OFFICE|TANK|PLANT|YARD)$", re.I)
_TAIL_END = re.compile(r"\b(?:ROOM|AREA|LOBBY|STORE|SPACE|HALL|OFFICE)$", re.I)
_TITLE_PANEL = re.compile(r"^\s*(?:LEGENDS?|DRAWING TITLE|APPROVAL STAMP|NOTES?)\s*:?\s*$", re.I)


@dataclass
class Room:
    id: str
    name: str
    x: float          # the name's centre on the page, in points
    y: float


@dataclass
class PageInfo:
    index: int
    width: float
    height: float
    plan: tuple[float, float, float, float]        # the drawing area, the title panel left out
    legend: tuple[float, float, float, float] | None
    rooms: list[Room] = field(default_factory=list)
    text: str = ""


def _lines(page) -> list[tuple[str, tuple]]:
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(span["text"] for span in line["spans"]).strip()
            if text:
                out.append((" ".join(text.split()), tuple(line["bbox"])))
    return out


def _joined(lines: list[tuple[str, tuple]], panel: float) -> list[tuple[str, tuple]]:
    """A name set on two lines is one name: "ELECTRICAL" over "ROOM" is
    ELECTRICAL ROOM -- the lines stacked, centred together, close."""
    used: set[int] = set()
    out = []
    order = sorted(range(len(lines)), key=lambda i: (lines[i][1][1], lines[i][1][0]))
    for i in order:
        if i in used:
            continue
        text, bb = lines[i]
        if bb[0] >= panel:
            out.append((text, bb))
            continue
        height = bb[3] - bb[1]
        for j in order:
            if j == i or j in used:
                continue
            t2, b2 = lines[j]
            # Only a name's last word joins it ("ELECTRICAL" / "ROOM"): a device's
            # letters ("OS", "E") or a window tag ("W4") never do.
            if (-height * 0.3 <= b2[1] - bb[3] <= height * 0.9 and abs((b2[0] + b2[2]) / 2 - (bb[0] + bb[2]) / 2) <= height * 1.5
                    and abs((b2[3] - b2[1]) - height) <= height * 0.3 and len(text) + len(t2) <= 40
                    and _TAIL.match(t2) and len(text) >= 4 and re.fullmatch(r"[A-Z .&/-]+", text.upper())
                    and not _TAIL_END.search(text)):
                text = f"{text} {t2}"
                bb = (min(bb[0], b2[0]), bb[1], max(bb[2], b2[2]), b2[3])
                used.add(j)
                break
        out.append((text, bb))
    return out


def is_room(text: str) -> bool:
    t = text.strip()
    if not (2 <= len(t) <= 40) or not re.search(r"[A-Z]{2}", t.upper()):
        return False
    return bool(ROOM_WORDS.search(t)) and not NOT_ROOM.search(t)


def read(doc: pymupdf.Document, index: int) -> PageInfo:
    page = doc[index]
    w, h = page.rect.width, page.rect.height
    lines = _lines(page)
    # The title panel down the right: where its own headings start, else the last seventh.
    panel = min((bb[0] for t, bb in lines if _TITLE_PANEL.match(t) and bb[0] > w * 0.6), default=w * 0.86) - 6
    plan = (w * 0.02, h * 0.02, panel, h * 0.98)
    legend = None
    head = next(((t, bb) for t, bb in lines if _LEGEND.match(t) and bb[0] > w * 0.6), None)
    if head:
        _t, bb = head
        legend = (panel, bb[1] - 6, w - w * 0.01, min(h, bb[1] + h * 0.32))
    info = PageInfo(index=index, width=w, height=h, plan=plan, legend=legend,
                    text=" ".join(t for t, _bb in lines)[:4000])
    seen: list[Room] = []
    lines = _joined(lines, panel)
    for text, bb in lines:
        x, y = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        if x >= panel or not is_room(text):
            continue
        name = text.upper()
        if any(r.name == name and abs(r.x - x) < 25 and abs(r.y - y) < 25 for r in seen):
            continue
        seen.append(Room(id=f"{index}:{round(x)}:{round(y)}", name=name, x=x, y=y))
    info.rooms = seen
    return info


def crop(doc: pymupdf.Document, index: int, box: tuple[float, float, float, float], dpi: int) -> bytes:
    """A piece of a page as PNG."""
    page = doc[index]
    clip = pymupdf.Rect(*box) & page.rect
    return page.get_pixmap(dpi=dpi, clip=clip).tobytes("png")


def room_box(info: PageInfo, room: Room, half: float = 100.0) -> tuple[float, float, float, float]:
    """The square a room is looked at in: 200 pt around its name (12 m at 1:175 on A1)."""
    return (room.x - half, room.y - half, room.x + half, room.y + half)


def dpi_for(box: tuple[float, float, float, float], pixels: int) -> int:
    """The resolution that makes the box's longer side `pixels` wide."""
    longest = max(box[2] - box[0], box[3] - box[1]) / 72.0
    return max(36, min(400, int(pixels / max(longest, 0.01))))


@dataclass
class Window:
    """A piece of a plan looked at in one image, with the rooms named in it."""
    id: str
    box: tuple[float, float, float, float]
    rooms: list[Room]


def windows(info: PageInfo, cell: float = 360.0, margin: float = 40.0) -> list[Window]:
    """The plan cut into cells of `cell` points (about 13 m at 1:175 on A1),
    each looked at with `margin` around it, so a room near an edge is still
    seen whole; a cell with no room named in it is not looked at."""
    x0, y0, x1, y1 = info.plan
    cells: dict[tuple[int, int], list[Room]] = {}
    for room in info.rooms:
        cells.setdefault((int((room.x - x0) // cell), int((room.y - y0) // cell)), []).append(room)
    out = []
    for (cx, cy), rooms in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        box = (max(x0, x0 + cx * cell - margin), max(y0, y0 + cy * cell - margin),
               min(x1, x0 + (cx + 1) * cell + margin), min(y1, y0 + (cy + 1) * cell + margin))
        out.append(Window(id=f"{info.index}:{cx}:{cy}", box=box, rooms=rooms))
    return out
