r"""The Fire Alarm Interface Schedule as a document, laid out to be issued:
landscape, the same look as the amplifier and power calculations.

A summary, the drawings it was read from, the schedule floor by floor
(each floor banded, with its totals), the floor and equipment summaries,
what is still to verify and what the engineer is asked to check. Built from
the same view as the page and the workbook (`service.build`), so the three
never disagree.
"""
from __future__ import annotations

from datetime import datetime

import pymupdf

_RED = (0.72, 0.11, 0.11)
_INK = (0.10, 0.13, 0.20)
_GREY = (0.45, 0.45, 0.45)
_RULE = (0.87, 0.87, 0.87)
_BAND = (0.96, 0.97, 0.99)
_FLOOR = (0.87, 0.91, 0.96)
_WARN = (0.99, 0.95, 0.90)
_WHITE = (1, 1, 1)

WIDTH, HEIGHT = 841.92, 595.32          # A4 landscape
LEFT, RIGHT = 30, WIDTH - 30
TOP, BOTTOM = 40, HEIGHT - 40
ROW = 13

# The schedule's columns: (heading, width).
_COLUMNS = [("TAG", 82), ("EQUIPMENT", 132), ("SYSTEM", 92), ("CONTACT", 70), ("MON", 30), ("CTRL", 30),
            ("FUNCTION / THIRD-PARTY ACTION", 196), ("SOURCE DRAWING", 0)]


def _font(bold: bool) -> str:
    return "hebo" if bold else "helv"


def _fit(value, width: float, size: float, bold: bool = False) -> str:
    """The text as much of it as fits the width, with an ellipsis if cut."""
    text = " ".join(str("" if value is None else value).split())
    font = _font(bold)
    if pymupdf.get_text_length(text, fontname=font, fontsize=size) <= width:
        return text
    while text and pymupdf.get_text_length(text + "...", fontname=font, fontsize=size) > width:
        text = text[:-1]
    return text.rstrip() + "..."


def _text(page, x, y, value, *, size=7.5, bold=False, colour=_INK, right=None, width=None):
    text = _fit(value, width, size, bold) if width else str(value)
    if right is not None:
        x = right - pymupdf.get_text_length(text, fontname=_font(bold), fontsize=size)
    page.insert_text((x, y), text, fontname=_font(bold), fontsize=size, color=colour)


def _function(r: dict) -> str:
    parts = []
    if r.get("alarm"):
        parts.append(f"Alarm: {r['alarm']}")
    if r.get("supervisory"):
        parts.append(f"Supervisory: {r['supervisory']}")
    if r.get("action"):
        parts.append(r["action"])
    return " | ".join(parts) or "-"


def build(view: dict) -> pymupdf.Document:
    doc = pymupdf.open()
    p = view["project"]
    t = view["totals"]
    state: dict = {"page": None, "y": 0.0}
    widths = [w for _h, w in _COLUMNS]
    widths[-1] = RIGHT - LEFT - sum(widths[:-1])

    def new_page(title: str) -> None:
        page = doc.new_page(width=WIDTH, height=HEIGHT)
        state["page"] = page
        _text(page, LEFT, TOP, "FIRE ALARM INTERFACE SCHEDULE", size=14, bold=True, colour=_RED)
        _text(page, LEFT, TOP + 14, f"EP-{p['ep_number']} - {p.get('name') or ''}".strip(" -"), size=8,
              colour=_GREY, width=500)
        _text(page, 0, TOP + 14, title, size=8, bold=True, colour=_GREY, right=RIGHT)
        page.draw_line(pymupdf.Point(LEFT, TOP + 20), pymupdf.Point(RIGHT, TOP + 20), color=_RED, width=1)
        state["y"] = TOP + 34

    def room(needed: float, title: str) -> bool:
        """A new page when the next `needed` points do not fit; True if one was started."""
        if state["page"] is None or state["y"] + needed > BOTTOM:
            new_page(title)
            return True
        return False

    def heading(label: str) -> None:
        _text(state["page"], LEFT, state["y"], label, size=9, bold=True)
        state["y"] += 8

    def table_head(cols: list[tuple[str, float]], fill=_RED) -> None:
        page, y = state["page"], state["y"]
        page.draw_rect(pymupdf.Rect(LEFT, y, RIGHT, y + 16), color=None, fill=fill)
        x = LEFT
        for label, width in cols:
            _text(page, x + 3, y + 11, label, size=6.5, bold=True, colour=_WHITE, width=width - 5)
            x += width
        state["y"] = y + 16

    def table_row(values: list, cols: list[tuple[str, float]], *, fill=None, bold=False, size=7.0) -> None:
        page, y = state["page"], state["y"]
        if fill:
            page.draw_rect(pymupdf.Rect(LEFT, y, RIGHT, y + ROW), color=None, fill=fill)
        x = LEFT
        for value, (_label, width) in zip(values, cols):
            _text(page, x + 3, y + 9.5, value, size=size, bold=bold, width=width - 5)
            x += width
        page.draw_line(pymupdf.Point(LEFT, y + ROW), pymupdf.Point(RIGHT, y + ROW), color=_RULE, width=0.4)
        state["y"] = y + ROW

    # --- summary ---------------------------------------------------------------------------
    new_page("Summary")
    scanned = (view.get("scanned_at") or "")[:16].replace("T", " ") or "not read yet"
    from app.interfaces.export import evidence_note

    known = view.get("totals_known", True)

    def num(value) -> str:
        return str(value) if known else "—"

    facts = [
        ("Schedule", evidence_note(view)),
        ("Interface lines (one per item per floor)", num(t["items"])),
        ("Monitoring signals", num(t["monitoring"])),
        ("Control signals", num(t["control"])),
        ("Interface points", num(t["interface_points"])),
        ("FA modules, estimated", (f"{t['module_qty']}  (CT1 {t['modules']['CT1']} · CT2 {t['modules']['CT2']} · "
                                   f"CR {t['modules']['CR']})") if known else "—"),
        ("Items still to verify (not counted)", num(t["to_verify"])),
        ("Drawings read", scanned),
        ("Interface matrix", view["matrix"]["name"]),
    ]
    y = state["y"]
    for index, (label, value) in enumerate(facts):
        if index % 2 == 0:
            state["page"].draw_rect(pymupdf.Rect(LEFT, y, LEFT + 420, y + 16), color=None, fill=_BAND)
        _text(state["page"], LEFT + 6, y + 11, label, size=8, colour=_GREY)
        _text(state["page"], 0, y + 11, value, size=8, bold=True, right=LEFT + 414)
        y += 16
    state["y"] = y + 18

    # --- drawings received ------------------------------------------------------------------
    cols = [("DISCIPLINE", 120), ("STATUS", 70), ("DRAWING / FILE", 330), ("ITEMS", 50),
            ("FOLDER", RIGHT - LEFT - 570)]
    room(60, "Drawings received")
    heading("DRAWINGS RECEIVED")
    table_head(cols)
    status = {"available": "Received", "missing": "Missing", "failed": "Not read", "not_provided": "Not provided"}
    badge = {c.get("discipline"): c.get("badge_text") for c in view["coverage"]}
    for c in view["coverage"]:
        files = c["files"] or [None]
        for i, f in enumerate(files):
            if room(ROW, "Drawings received (continued)"):
                table_head(cols)
            name = "-" if f is None else (f"{f['filename']} {f.get('revision') or ''}".strip()
                                         + (" (superseded)" if f["status"] == "superseded" else "")
                                         + (" (not read)" if f["status"] == "failed" else "")
                                         + (" (not read yet)" if f["status"] == "unread" else "")
                                         + (" (last known, not counted)" if f["status"] == "stale" else ""))
            shown = badge.get(c.get("discipline")) or status.get(c["status"], c["status"])
            table_row([c["name"] if i == 0 else "", shown if i == 0 else "", name,
                       "" if f is None else f["items"], (c["folder"] or c["purpose"]) if i == 0 else ""], cols,
                      fill=_WARN if c["status"] in ("missing", "failed") and i == 0 else None)
    state["y"] += 14

    # --- the schedule, floor by floor ---------------------------------------------------------
    cols = list(zip([h for h, _w in _COLUMNS], widths))
    new_page("Interface schedule")
    heading("INTERFACE SCHEDULE, FLOOR BY FLOOR")
    table_head(cols)
    rows = view["rows"]
    if not rows:
        table_row(["", "Nothing scheduled yet."], cols)
    floor, mine = None, []

    def floor_total() -> None:
        if not mine:
            return
        if room(ROW, "Interface schedule (continued)"):
            table_head(cols)
        m, c = sum(r["monitoring"] for r in mine), sum(r["control"] for r in mine)
        table_row(["", f"{floor} total: {len(mine)} line{'s' if len(mine) != 1 else ''}", "", "", m, c,
                   f"{sum(r['module_qty'] for r in mine)} FA modules"], cols, fill=_BAND, bold=True)

    for r in rows:
        if r["floor"] != floor:
            floor_total()
            floor, mine = r["floor"], []
            if room(ROW * 3, "Interface schedule (continued)"):
                table_head(cols)
            table_row([r["floor"]], [("", RIGHT - LEFT)], fill=_FLOOR, bold=True, size=7.5)
        if room(ROW, "Interface schedule (continued)"):
            table_head(cols)
        mine.append(r)
        source = f"{r['source']} · {r['drawing_ref']}" if r.get("drawing_ref") else r["source"]
        table_row([r["tag"], r["equipment"], r["system"], r["contacts"], r["monitoring"], r["control"],
                   _function(r), source], cols)
    floor_total()
    if rows:
        if room(ROW + 4, "Interface schedule (continued)"):
            table_head(cols)
        table_row(["", f"BUILDING TOTAL: {t['items']} lines", "", "", t["monitoring"], t["control"],
                   f"{t['module_qty']} FA modules (CT1 {t['modules']['CT1']}, CT2 {t['modules']['CT2']}, "
                   f"CR {t['modules']['CR']})"], cols, fill=_FLOOR, bold=True)

    # --- floor and equipment summaries ----------------------------------------------------------
    new_page("Summaries")
    half = (RIGHT - LEFT - 20) / 2
    fcols = [("FLOOR", half - 200), ("LINES", 40), ("MON", 40), ("CTRL", 40), ("TOTAL", 40), ("MODULES", 40)]
    heading("FLOOR SUMMARY")
    table_head(fcols)
    for s in view["floor_summary"]:
        if room(ROW, "Floor summary (continued)"):
            table_head(fcols)
        table_row([s["floor"], s["items"], s["monitoring"], s["control"], s["total"], s["module_qty"]], fcols)
    table_row(["Total", t["items"], t["monitoring"], t["control"], t["interface_points"], t["module_qty"]], fcols,
              fill=_BAND, bold=True)
    state["y"] += 14
    ecols = [("EQUIPMENT", 200), ("CONTACT", 110), ("QTY", 40), ("MON", 40), ("CTRL", 40), ("CT1", 40), ("CT2", 40),
             ("CR", 40), ("MODULES", 50)]
    room(60, "Equipment summary")
    heading("EQUIPMENT SUMMARY")
    table_head(ecols)
    for s in view["type_summary"]:
        if room(ROW, "Equipment summary (continued)"):
            table_head(ecols)
        table_row([s["equipment"], s["contacts"], s["qty"], s["monitoring"], s["control"], s["modules"]["CT1"],
                   s["modules"]["CT2"], s["modules"]["CR"], s["module_qty"]], ecols)

    # --- what is left to verify, and what to check -------------------------------------------------
    vcols = [("POSSIBLE EQUIPMENT", 140), ("PROPOSED FLOOR", 110), ("QTY", 34), ("SOURCE", 190),
             ("ISSUE / EVIDENCE", RIGHT - LEFT - 474)]
    state["y"] += 14
    room(60, "Verification required")
    heading(f"VERIFICATION REQUIRED ({len(view['verification'])}) -- not counted until settled")
    table_head(vcols)
    if not view["verification"]:
        table_row(["Nothing left to verify."], [("", RIGHT - LEFT)])
    for g in view["verification"]:
        if room(ROW, "Verification required (continued)"):
            table_head(vcols)
        table_row([g["equipment"], ", ".join(g["proposed_floors"]) or "Not identified",
                   g["proposed_qty"] if g["proposed_qty"] is not None else "-", g["source"],
                   f"{g['reason']} -- {g['evidence']}"], vcols)

    notes = list(view["conflicts"])
    if view["matrix"]["unclear_rows"]:
        notes.append(f"Rows {', '.join(map(str, view['matrix']['unclear_rows']))} of the interface matrix are not "
                     "legible on the copy transcribed and are not applied.")
    notes += [f"Not an interface (engineer): {r['equipment']} {r['tag']} on {r['floor']} -- {r.get('reason', '')}"
              for r in view["rejected"]]
    if notes:
        state["y"] += 14
        room(40, "For the engineer to check")
        heading("FOR THE ENGINEER TO CHECK")
        for note in notes:
            room(ROW, "For the engineer to check (continued)")
            _text(state["page"], LEFT, state["y"] + 9, "•", size=7)
            # a long note runs onto the next line rather than being cut
            words, line = note.split(), ""
            for word in words:
                trial = f"{line} {word}".strip()
                if pymupdf.get_text_length(trial, fontname="helv", fontsize=7) > RIGHT - LEFT - 14:
                    _text(state["page"], LEFT + 8, state["y"] + 9, line, size=7)
                    state["y"] += 10
                    room(10, "For the engineer to check (continued)")
                    line = word
                else:
                    line = trial
            _text(state["page"], LEFT + 8, state["y"] + 9, line, size=7)
            state["y"] += 12

    # --- page numbers ----------------------------------------------------------------------------
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for index, page in enumerate(doc, 1):
        _text(page, LEFT, HEIGHT - 22, f"EP-{p['ep_number']} Fire Alarm Interface Schedule · issued {stamp}",
              size=6.5, colour=_GREY)
        _text(page, 0, HEIGHT - 22, f"Page {index} of {doc.page_count}", size=6.5, colour=_GREY, right=RIGHT)
    return doc
