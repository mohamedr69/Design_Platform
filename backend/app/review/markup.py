"""The draftsman's schedule: every change the engineer accepted, floor by
floor -- what to ADD, REMOVE or REPLACE, the device, the room, the
instruction to follow, and where: the piece of the plan the finding's card
shows, the spot ringed (platform owner, 2 October 2026). No whole plans.

Only accepted changes: an open finding is not the draftsman's business yet,
a dismissed one never is.
"""
from __future__ import annotations

from datetime import datetime

import pymupdf

COLOURS = {"add": (0.86, 0.15, 0.15), "remove": (0.15, 0.39, 0.92), "replace": (0.92, 0.55, 0.05)}
WORDS = {"add": "ADD", "remove": "REMOVE", "replace": "REPLACE"}
_INK = (0.10, 0.13, 0.20)
_GREY = (0.45, 0.45, 0.45)
_RED = (0.72, 0.11, 0.11)
_RULE = (0.87, 0.87, 0.87)

WIDTH, HEIGHT = 841.92, 595.32           # A4 landscape
LEFT, RIGHT, TOP, BOTTOM = 36, 841.92 - 36, 40, 595.32 - 36
SIZE = 9.0
LINE = 11.5
# (heading, width): the instruction takes what is left
COLUMNS = [("#", 26), ("ACTION", 62), ("DEVICE", 150), ("ROOM / WHERE", 140), ("INSTRUCTION", 0), ("LOCATION", 110)]
PICTURE = 100.0          # the location's side, in points: four changes a page
_RING = (0.86, 0.15, 0.15)

_PLAIN = str.maketrans({"≤": "<=", "≥": ">=", "–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "×": "x",
                        "°": " deg", "Ø": "dia "})


def _plain(text) -> str:
    """The PDF's built-in font has no "≤": what it cannot print is spelt out."""
    return str(text or "").translate(_PLAIN)


def _lines(text: str, width: float, size: float = SIZE, font: str = "helv") -> list[str]:
    """The text wrapped to the width, never cut."""
    out, line = [], ""
    for word in _plain(text).split():
        trial = f"{line} {word}".strip()
        if pymupdf.get_text_length(trial, fontname=font, fontsize=size) > width and line:
            out.append(line)
            line = word
        else:
            line = trial
    if line:
        out.append(line)
    return out or [""]


def _location(page, rect: pymupdf.Rect, plot, f: dict) -> None:
    """The finding's piece of the plotted plan, drawn from the plot itself (so
    it stays sharp at any zoom), the spot ringed in red."""
    box = f.get("box")
    if plot is None or not box or not 0 <= f["page"] < plot.page_count:
        page.insert_text((rect.x0 + 4, rect.y0 + 12), "-", fontname="helv", fontsize=SIZE, color=_GREY)
        return
    clip = pymupdf.Rect(box) & plot[f["page"]].rect
    if clip.is_empty:
        return
    page.show_pdf_page(rect, plot, f["page"], clip=clip, keep_proportion=True)
    page.draw_rect(rect, color=_RULE, width=0.5)
    if f.get("mark"):
        # where the mark falls in the picture: the clip is fitted into the rect, centred
        scale = min(rect.width / clip.width, rect.height / clip.height)
        x0 = rect.x0 + (rect.width - clip.width * scale) / 2
        y0 = rect.y0 + (rect.height - clip.height * scale) / 2
        x, y = x0 + (f["mark"][0] - clip.x0) * scale, y0 + (f["mark"][1] - clip.y0) * scale
        if rect.contains(pymupdf.Point(x, y)):
            page.draw_circle((x, y), max(7.0, rect.width / 10), color=_RING, width=1.6)


def build(view: dict, project, pdf_path: str | None = None, *,
          footer: str = "Drawings Review - accepted changes") -> pymupdf.Document:
    doc = pymupdf.open()
    plot = None
    if pdf_path:
        try:
            plot = pymupdf.open(pdf_path)
        except Exception:  # noqa: BLE001 -- the schedule goes out without its pictures rather than not at all
            plot = None
    accepted = [f for f in view["findings"] if f["decision"] == "accepted" and f["action"] in COLOURS]
    by_page: dict[int, list[dict]] = {}
    for f in accepted:
        by_page.setdefault(f["page"], []).append(f)
    title = f"EP-{project.ep_number} {project.project_name or ''}".strip()
    drawing = f"{view['drawing']['filename']} {view['drawing']['revision']}"
    widths = [w for _h, w in COLUMNS]
    widths[4] = RIGHT - LEFT - sum(widths) + widths[4]     # the instruction takes what is left
    state: dict = {"page": None, "y": 0.0}

    def new_page() -> None:
        state["page"] = doc.new_page(width=WIDTH, height=HEIGHT)
        state["y"] = TOP

    def head() -> None:
        page, y = state["page"], state["y"]
        page.draw_rect(pymupdf.Rect(LEFT, y, RIGHT, y + 18), color=None, fill=_RED)
        x = LEFT
        for (label, _w), width in zip(COLUMNS, widths):
            page.insert_text((x + 5, y + 12.5), label, fontname="hebo", fontsize=SIZE, color=(1, 1, 1))
            x += width
        state["y"] = y + 18

    def floor_title(items: list[dict], continued: bool = False) -> None:
        page = state["page"]
        page.insert_text((LEFT, state["y"] + 14), f"{items[0]['floor']} ({items[0]['sheet']}) - changes for the "
                         f"draftsman{' (continued)' if continued else ''}", fontname="hebo", fontsize=13, color=_INK)
        page.insert_text((LEFT, state["y"] + 28), f"{drawing} - {title}", fontname="helv", fontsize=8.5, color=_GREY)
        state["y"] += 38
        head()

    new_page()
    if not by_page:
        state["page"].insert_text((LEFT, TOP + 14), "No change has been accepted yet.", fontname="helv", fontsize=10,
                                  color=_GREY)
    for index in sorted(by_page):
        items = by_page[index]
        if state["y"] > TOP and state["y"] + 38 + 18 + LINE * 3 > BOTTOM:
            new_page()
        elif state["y"] > TOP:
            state["y"] += 18
        floor_title(items)
        for n, f in enumerate(items, 1):
            cells = [[str(n)], [WORDS[f["action"]]],
                     _lines(f["device"] or f["system_name"], widths[2] - 10),
                     _lines(f["room"] or "-", widths[3] - 10),
                     _lines(f["instruction"] or f["issue"], widths[4] - 10), []]
            height = max(6 + LINE * max(len(c) for c in cells), PICTURE + 8)
            if state["y"] + height > BOTTOM:
                new_page()
                floor_title(items, continued=True)
            page, y = state["page"], state["y"]
            x = LEFT
            for col, (lines, width) in enumerate(zip(cells, widths)):
                bold = col in (0, 1)
                colour = COLOURS[f["action"]] if col == 1 else _INK
                for i, line in enumerate(lines):
                    page.insert_text((x + 5, y + 12 + LINE * i), line, fontname="hebo" if bold else "helv",
                                     fontsize=SIZE, color=colour)
                x += width
            _location(page, pymupdf.Rect(RIGHT - widths[5] + 5, y + 4, RIGHT - 5, y + 4 + PICTURE), plot, f)
            state["y"] = y + height
            page.draw_line((LEFT, state["y"]), (RIGHT, state["y"]), color=_RULE, width=0.5)

    if plot is not None:
        plot.close()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for n, page in enumerate(doc, 1):
        page.insert_text((LEFT, HEIGHT - 18), f"{title} - {footer} - issued {stamp}",
                         fontname="helv", fontsize=7, color=_GREY)
        page.insert_text((RIGHT - 60, HEIGHT - 18), f"Page {n} of {doc.page_count}", fontname="helv", fontsize=7,
                         color=_GREY)
    return doc
