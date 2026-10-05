"""A drawing sheet's title block read by position (M2 review 05, R5-01: pilot P-06 / P-07).

A CAD sheet carries several drawing numbers and several revision columns: its own number and REV cell,
a reference-drawings table ("DRAWING NO | REV | DRAWING TITLE" with the architect's sheets it was drawn
over), a revision-history table (one row per issue) and, on the plan itself, callouts to the next sheet
("REFER TO DWG No. ...-00008"). The PDF text layer gives these as unordered runs, so the first number or
the first "REV" in the text is whichever the CAD export wrote first -- on the pilot that was a neighbour
sheet's number on 12 of 13 BK Gulf sheets and the date "10.09.2024" read as revision 10 on JAM-SD-FA-002.

This reads the text runs by their place on the sheet instead. The sheet's own identity is a *cell*: a
"DRAWING NO" label with exactly one value under it (or beside it), nearest the title block's corner,
and the REV label on the same row with exactly one revision under it. A label whose column lists
several values is a table, and a label under a "REFERENCE DRAWINGS" heading is the reference table,
whatever it is called. The revision history is a separate fact: its rows and their dates are read, and
where the row dated latest names another revision than the REV cell, the sheet contradicts itself --
reported as such (`conflict`), never settled by picking one.

Nothing here guesses: no first / last / highest rule, no value borrowed from the file name or the folder.
Where no cell is found the reading is None and the text reader stands, as before.

The date the sheet was issued is read the same way (`issued`, branch g/project-log-and-drawing-scan): the
title block's DATE cell -- one date under its label or beside it, the cell nearest the number cell (or the
corner) -- and, where the block has none, the latest date its revision history records. The history table's
own "DATE" column header is not that cell: its row names DESCRIPTION. It is when the drawing says it was
issued, a fact of the sheet; when it was submitted is the register's, and is not read here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

# titleblock-2: the issue date (`issued`, `issued_source`).
TITLE_BLOCK_VERSION = "titleblock-2"

# A drawing sheet: A2 and larger (the forms, letters and datasheets are A4 / A3).
MIN_SHEET_SIDE_PT = 1300.0

_NUMBER_LABEL = re.compile(
    r"^(?:(?P<qualifier>[A-Z][A-Z.]*)\s+)?(?:DRAWING|DWG)\.?\s*(?:NO|NUMBER|NR)\b\.?\s*:?\s*(?P<inline>[A-Z0-9][A-Z0-9 ./_&()-]{3,})?$",
    re.I)
_REV_LABEL = re.compile(r"^(?:REV(?:ISION)?|Rev)\b\.?\s*(?:NO\b\.?)?\s*:?\s*(?P<inline>[A-Z0-9]{1,4})?$", re.I)
# A revision as printed: "0", "00", "07", "AB", "C1", "P03", "2A". Letters stay letters.
REVISION_VALUE = re.compile(r"^(?:\d{1,3}|[A-Z]{1,2}|[A-Z]{1,2}\d{1,2}|\d{1,2}[A-Z])$")
_DATE = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{2}|\d{4})$")
_REFERENCE_HEADING = re.compile(r"\bREF(?:ERENCE|\.)?\s*(?:DRAWINGS?|DWGS?|DOCUMENTS?)\b", re.I)
_DESCRIPTION = re.compile(r"^DESCRIPTION\b", re.I)
_DATE_LABEL = re.compile(r"^DATE\s*:?$", re.I)
# The DATE cell's label, with its value in the same run where the CAD export wrote them as one ("DATE: 28/08/2024").
_DATE_CELL = re.compile(r"^DATE\s*:?\s*(?P<inline>\d{1,2}[./-]\d{1,2}[./-](?:\d{2}|\d{4}))?$", re.I)
_TITLE_LABEL = re.compile(r"^(?:DRAWING\s+|DWG\.?\s+|SHEET\s+)?TITLE\s*:?$", re.I)


@dataclass(frozen=True)
class Line:
    """One text run in display coordinates (the page as it is shown: rotation applied)."""

    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def h(self) -> float:
        return max(self.y1 - self.y0, 1.0)

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass(frozen=True)
class TitleBlock:
    number: str | None
    revision: str | None                       # the REV cell, as printed
    number_label: str | None = None
    revision_label: str | None = None
    history: tuple = ()                        # ((revision, date as printed), ...) in the sheet's order
    history_latest: str | None = None          # the history row dated latest, where the dates settle it
    references: tuple = ()                     # values of the reference-drawings table(s)
    conflict: bool = False                     # the REV cell and the history's latest row disagree
    title: str | None = None                   # the Drawing Title cell's lines, as printed
    notes: tuple = field(default=())
    issued: date | None = None                 # the date the sheet says it was issued
    issued_source: str | None = None           # "date cell" | "revision history"

    def observation(self) -> dict:
        return {"kind": "title_block", "version": TITLE_BLOCK_VERSION, "number": self.number,
                "revision": self.revision, "number_label": self.number_label, "revision_label": self.revision_label,
                "history": [list(row) for row in self.history], "history_latest": self.history_latest,
                "references": list(self.references), "conflict": self.conflict, "title": self.title, "notes": list(self.notes),
                "issued": self.issued.isoformat() if self.issued else None, "issued_source": self.issued_source}


def page_lines(page) -> list[Line]:
    """The page's horizontal text runs in display coordinates. Runs set at an angle (a rotated callout,
    vertical grid labels) are not title-block cells and are left out."""
    import pymupdf

    matrix = page.rotation_matrix
    out = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            text = " ".join(span["text"] for span in line["spans"]).strip()
            if not text:
                continue
            dx, dy = line["dir"]
            ddx, ddy = dx * matrix.a + dy * matrix.c, dx * matrix.b + dy * matrix.d
            if ddx < 0.95 or abs(ddy) > 0.05:
                continue
            r = pymupdf.Rect(line["bbox"]) * matrix
            out.append(Line(r.x0, r.y0, r.x1, r.y1, " ".join(text.split())))
    return out


def is_drawing_sheet(page) -> bool:
    return max(page.rect.width, page.rect.height) > MIN_SHEET_SIDE_PT


def read_page(page, *, controlled=None) -> TitleBlock | None:
    """The title block of a drawing-sized page with a text layer; None for any other page."""
    if not is_drawing_sheet(page):
        return None
    lines = page_lines(page)
    if len(lines) < 5:
        return None
    return read(lines, page.rect.width, page.rect.height, controlled=controlled)


# --- the geometry -----------------------------------------------------------------------------------


def _same_row(a: Line, b: Line) -> bool:
    return abs(a.cy - b.cy) <= 0.6 * max(a.h, b.h) and 0.5 <= a.h / b.h <= 2.0


def _row(lines: list[Line], label: Line) -> list[Line]:
    return sorted((l for l in lines if l is not label and _same_row(l, label)), key=lambda l: l.x0)


def _is_label(line: Line) -> bool:
    text = line.text
    return bool(_NUMBER_LABEL.match(text) and not _NUMBER_LABEL.match(text).group("inline")) \
        or bool(_REV_LABEL.match(text) and not _REV_LABEL.match(text).group("inline")) \
        or text.endswith(":")


def _column(lines: list[Line], label: Line, *, right_pad: float) -> tuple[float, float]:
    """The x-range of the label's cell: from a little left of the label to the next run on its row."""
    after = [l for l in _row(lines, label) if l.x0 >= label.x1 - 1]
    right = after[0].x0 if after else label.x1 + right_pad
    return label.x0 - 3 * label.h, right


def _below(lines: list[Line], label: Line, span: tuple[float, float], depth: float) -> list[Line]:
    left, right = span
    return sorted((l for l in lines if l is not label and label.y0 + 0.5 * label.h < l.y0 <= label.y1 + depth
                   and left <= l.cx < right and not _is_label(l)), key=lambda l: l.y0)


def _under_reference_heading(lines: list[Line], label: Line) -> bool:
    return any(_REFERENCE_HEADING.search(l.text) and label.y0 - 5 * label.h <= l.y0 < label.y0 - 0.3 * label.h
               and l.x1 > label.x0 - 10 * label.h and l.x0 < label.x1 + 30 * label.h for l in lines)


def _number_shaped(text: str) -> bool:
    return len(text) >= 5 and bool(re.search(r"\d", text)) and bool(re.search(r"[A-Z]", text, re.I)) \
        and bool(re.search(r"[-_/]", text)) and not _DATE.match(text)


def _incomplete(text: str) -> bool:
    """A number whose segments the CAD export set as separate runs comes back with holes in it
    ("R1029- -BSB-DWG- ARC-"): the run is part of the number, never the number."""
    return bool(re.search(r"-\s+-|--|-\s*$|^\s*-", text))


def _in_zone(line: Line, width: float, height: float) -> bool:
    """The title block sits along the right edge or the bottom edge of a sheet."""
    return line.x0 >= 0.55 * width or line.y0 >= 0.8 * height


def _corner_rank(line: Line, width: float, height: float) -> float:
    return line.y1 / height + line.x1 / width


def _cell_value(lines: list[Line], label: Line, inline: str | None, shaped, *, right_pad: float) -> tuple[str | None, str]:
    """(value, why-not). One value, under the label or beside it on its row; a column holding several is a table."""
    if inline:
        return (inline.strip(), "") if shaped(inline.strip()) else (None, "inline value not shaped")
    after = [l for l in _row(lines, label) if l.x0 >= label.x1 - 1]
    if after and not _is_label(after[0]) and shaped(after[0].text) and after[0].x0 - label.x1 < 12 * label.h:
        return after[0].text, ""
    below = _below(lines, label, _column(lines, label, right_pad=right_pad), 4 * label.h)
    if not below:
        return None, "no value"
    value = below[0]
    if not shaped(value.text):
        return None, "value not shaped"
    span = _column(lines, label, right_pad=right_pad)
    # The column ends where the next cell starts: a label under this one (a second numbering scheme's
    # "MUNICIPALITY DRAWING No." under "CLIENT DRAWING No.") opens a cell of its own, not a table row.
    stop = min((l.y0 for l in lines if l is not label and l.y0 > label.y1 and span[0] <= l.cx < span[1]
                and (_is_label(l) or _TITLE_LABEL.match(l.text))), default=float("inf"))
    deeper = [l for l in _below(lines, label, span, 9 * label.h) if l is not value and shaped(l.text) and l.y0 < stop]
    if deeper:
        return None, "a list (table column)"
    return value.text, ""


def _rev_shaped(text: str) -> bool:
    return bool(REVISION_VALUE.match(text.strip())) and not _DATE.match(text.strip())


def _parse_date(text: str) -> date | None:
    found = _DATE.match(text.strip())
    if not found:
        return None
    day, month, year = (int(v) for v in found.groups())
    if year < 100:
        year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return None


def revision_key(value: str | None) -> str | None:
    """A printed revision compared as printed: digits by value ("07" == "7"), letters as they are."""
    if value is None:
        return None
    value = value.strip().upper()
    return str(int(value)) if value.isdigit() else value


def _history(lines: list[Line]) -> tuple[tuple, str | None]:
    """The revision-history table: its REV column's rows with the date on each row. The table's header
    row names DESCRIPTION; its rows run up or down from the header."""
    rows: list[tuple[Line, date | None, str | None]] = []
    for header in lines:
        if not _REV_LABEL.match(header.text) or _REV_LABEL.match(header.text).group("inline"):
            continue
        row = _row(lines, header)
        if not any(_DESCRIPTION.match(l.text) for l in row):
            continue
        date_label = next((l for l in row if _DATE_LABEL.match(l.text)), None)
        column = [l for l in lines if l is not header and abs(l.cx - header.cx) <= max(2.5 * header.h, (header.x1 - header.x0))
                  and abs(l.cy - header.cy) <= 30 * header.h and _rev_shaped(l.text)]
        for value in column:
            printed_date = None
            if date_label is not None:
                printed_date = next((l.text for l in lines if _same_row(l, value) and _parse_date(l.text)
                                     and date_label.x0 - 3 * date_label.h <= l.cx <= date_label.x1 + 6 * date_label.h), None)
            rows.append((value, _parse_date(printed_date) if printed_date else None, printed_date))
    if not rows:
        return (), None
    rows.sort(key=lambda r: r[0].y0)
    history = tuple((r[0].text, r[2]) for r in rows)
    dated = [r for r in rows if r[1] is not None]
    latest = None
    if dated:
        top = max(r[1] for r in dated)
        at_top = {revision_key(r[0].text) for r in dated if r[1] == top}
        latest = next(r[0].text for r in dated if r[1] == top) if len(at_top) == 1 else None
    return history, latest


def _references(lines: list[Line]) -> tuple:
    """The values of the reference-drawings table(s): the sheets this one was drawn over -- facts about
    the sheet, never its identity."""
    out = []
    for heading in lines:
        if not _REFERENCE_HEADING.search(heading.text):
            continue
        for label in lines:
            if _NUMBER_LABEL.match(label.text) and 0 < label.y0 - heading.y0 <= 5 * heading.h \
                    and label.x1 > heading.x0 - 10 * label.h and label.x0 < heading.x1 + 10 * label.h:
                out.extend(l.text for l in _below(lines, label, _column(lines, label, right_pad=30 * label.h), 12 * label.h)
                           if len(l.text) >= 4 and re.search(r"\d", l.text) and not _DATE.match(l.text))
    return tuple(dict.fromkeys(out))


def read(lines: list[Line], width: float, height: float, *, controlled=None) -> TitleBlock | None:
    """`controlled`: whether a value is in the project's controlled-document numbering (the reader's
    reference grammar). A sheet may carry its number in two schemes -- the client's and the
    municipality's (Kling / IBA: "CLIENT DRAWING No." and "MUNICIPALITY DRAWING No.") -- and the register
    is keyed by the controlled one; where neither or both are controlled and they differ, the sheet does
    not say which is its identity and no number is read."""
    notes: list[str] = []
    number = number_label = None
    chosen = None
    candidates = [l for l in lines if _NUMBER_LABEL.match(l.text) and _in_zone(l, width, height)
                  and not re.match(r"^REF", _NUMBER_LABEL.match(l.text).group("qualifier") or "", re.I)]
    cells = []
    for label in sorted(candidates, key=lambda l: -_corner_rank(l, width, height)):
        if _under_reference_heading(lines, label):
            notes.append(f"'{label.text}' is under a reference-drawings heading")
            continue
        value, why = _cell_value(lines, label, _NUMBER_LABEL.match(label.text).group("inline"), _number_shaped,
                                 right_pad=40 * label.h)
        if value is not None and _incomplete(value):
            value, why = None, f"value incomplete ({value!r})"
        if value is None:
            notes.append(f"'{label.text}': {why}")
            continue
        cells.append((label, value))
    # A run that carries its label and its number together ("DWG No. SA-H2-BEST-FA-00104") is a callout on the
    # plan, pointing at another sheet; a title block sets the label and the value as runs of their own. Where
    # the sheet has such a cell, the callouts are not cells (SA-H2-BEST-ICT-00100a, M2 review 05).
    true_cells = [(label, value) for label, value in cells if not _NUMBER_LABEL.match(label.text).group("inline")]
    if true_cells:
        cells = true_cells
    distinct = list(dict.fromkeys(value for _label, value in cells))
    if len(distinct) > 1 and controlled is not None:
        kept = [(label, value) for label, value in cells if controlled(value)]
        if len({value for _label, value in kept}) == 1:
            notes.append("several own-number cells; the controlled number kept: " + ", ".join(distinct))
            cells = kept[:1]
    if len({value for _label, value in cells}) > 1:
        notes.append("several own-number cells disagree: " + ", ".join(distinct))
        cells = []
    if cells:
        chosen, number = cells[0]
        number_label = chosen.text
    # The REV cell: on the number's row where there is a number cell; otherwise the REV label nearest the
    # corner that is neither a history header (its row names DESCRIPTION) nor a reference-table column.
    revision = revision_label = None
    rev_labels = [l for l in lines if _REV_LABEL.match(l.text) and _in_zone(l, width, height)]
    if chosen is not None:
        rev_labels = [l for l in rev_labels if _same_row(l, chosen) and l.x0 > chosen.x0]
        rev_labels.sort(key=lambda l: l.x0)
    else:
        rev_labels.sort(key=lambda l: -_corner_rank(l, width, height))
    for label in rev_labels:
        if any(_DESCRIPTION.match(l.text) for l in _row(lines, label)) or _under_reference_heading(lines, label):
            continue
        value, why = _cell_value(lines, label, _REV_LABEL.match(label.text).group("inline"), _rev_shaped,
                                 right_pad=6 * label.h)
        if value is None:
            notes.append(f"'{label.text}': {why}")
            continue
        revision, revision_label = value.strip(), label.text
        break
    if number is None and revision is None:
        return None
    history, latest = _history(lines)
    conflict = bool(revision and latest and revision_key(revision) != revision_key(latest))
    issued, issued_source = _issued(lines, width, height, chosen, history)
    return TitleBlock(number, revision, number_label, revision_label, history, latest, _references(lines), conflict,
                      title=_title(lines, width, height, chosen), notes=tuple(notes), issued=issued, issued_source=issued_source)


# A date inside a run: the PDF text layer joins runs that sit close on one baseline, so the DATE cell's value can
# come back with its neighbour's ("RAMADAN 06.08.2026": the CHECKED cell's initials, then the date).
_DATE_TOKEN = re.compile(r"(?<![\d./-])\d{1,2}[./-]\d{1,2}[./-](?:\d{4}|\d{2})(?![\d./-])")


def _one_date(text: str) -> date | None:
    """The one date a run holds, or None for none or several (several say nothing about which is the cell's)."""
    found = _DATE_TOKEN.findall(text)
    return _parse_date(found[0]) if len(found) == 1 else None


def _date_shaped(text: str) -> bool:
    return _one_date(text) is not None


def _issued(lines: list[Line], width: float, height: float, near: Line | None, history: tuple) -> tuple[date | None, str | None]:
    """(the date the sheet was issued, where it was read): the title block's DATE cell -- one date under the
    label or beside it on its row, the cell nearest the number cell (or the corner); a revision history's
    "DATE" column header (its row names DESCRIPTION) and a reference table's are not it -- else the latest
    date the revision history records. (None, None) where the sheet gives neither."""
    labels = [l for l in lines if _DATE_CELL.match(l.text) and _in_zone(l, width, height)
              and not any(_DESCRIPTION.match(other.text) for other in _row(lines, l))
              and not _under_reference_heading(lines, l)]
    if near is not None:
        labels.sort(key=lambda l: abs(l.cx - near.cx) + abs(l.cy - near.cy))
    else:
        labels.sort(key=lambda l: -_corner_rank(l, width, height))
    for label in labels:
        value, _why = _cell_value(lines, label, _DATE_CELL.match(label.text).group("inline"), _date_shaped,
                                  right_pad=6 * label.h)
        if value is not None:
            return _one_date(value), "date cell"
    dated = [d for d in (_parse_date(printed) for _revision, printed in history if printed) if d is not None]
    if dated:
        return max(dated), "revision history"
    return None, None


def _title(lines: list[Line], width: float, height: float, near: Line | None) -> str | None:
    """The Drawing Title cell: the lines under its label, one after another, until the next label or a gap
    wider than a line -- the cell nearest the number cell (or the corner). A reference table's DRAWING TITLE
    column is not it."""
    labels = [l for l in lines if _TITLE_LABEL.match(l.text) and _in_zone(l, width, height) and not _under_reference_heading(lines, l)]
    if near is not None:
        labels.sort(key=lambda l: abs(l.cx - near.cx) + abs(l.cy - near.cy))
    else:
        labels.sort(key=lambda l: -_corner_rank(l, width, height))
    for label in labels:
        left, right = _column(lines, label, right_pad=40 * label.h)
        column = sorted((l for l in lines if l is not label and l.y0 > label.y0 + 0.5 * label.h and l.y0 <= label.y1 + 30 * label.h
                         and left <= l.cx < right), key=lambda l: (round(l.y0), l.x0))
        out, previous = [], label
        for line in column:
            limit = 4 * label.h if previous is label else 1.2 * max(previous.h, line.h)
            if line.y0 - previous.y1 > limit or _is_label(line) or _TITLE_LABEL.match(line.text) or _DATE_LABEL.match(line.text):
                break
            out.append(line.text)
            previous = line if line.y1 > previous.y1 else previous
            if len(out) == 4:
                break
        if out:
            return " ".join(" ".join(out).split())
    return None
