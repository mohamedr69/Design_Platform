r"""The cases the Opus review could not decide, as a document for the engineer.

Each item still in Verification Required gets its pages: where it was read and
why the reading held it, what the Opus review checked, what remains unclear and
what the engineer needs to verify -- or, when the review did not run on it, that
it did not and why -- and the pictures of the original drawing it was shown,
each point ringed and numbered as the review saw it, with what each number is.
Built from the same view as the page (`service.build`) and the pictures the
review kept with its run (`findings.keep_pictures`); nothing is decided here.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pymupdf

_RED = (0.72, 0.11, 0.11)
_INK = (0.10, 0.13, 0.20)
_GREY = (0.45, 0.45, 0.45)
_RULE = (0.87, 0.87, 0.87)
_SKY = (0.93, 0.96, 0.99)
_WARN = (0.99, 0.95, 0.90)

WIDTH, HEIGHT = 595.32, 841.92          # A4 portrait
LEFT, RIGHT = 36, WIDTH - 36
TOP, BOTTOM = 40, HEIGHT - 40
LABEL_W = 118
PICTURE = (RIGHT - LEFT - 14) / 2       # two pictures a row


def _font(bold: bool) -> str:
    return "hebo" if bold else "helv"


def _clean(value) -> str:
    return " ".join(str("" if value is None else value).replace("—", "-").replace("–", "-").split())


def _wrap(text, width: float, size: float, bold: bool = False) -> list[str]:
    """The text in lines that fit `width` (a word longer than a line is cut)."""
    lines: list[str] = []
    for para in str("" if text is None else text).split("\n"):
        words, line = _clean(para).split(" "), ""
        for word in words:
            trial = f"{line} {word}".strip()
            if pymupdf.get_text_length(trial, fontname=_font(bold), fontsize=size) <= width:
                line = trial
                continue
            if line:
                lines.append(line)
            while pymupdf.get_text_length(word, fontname=_font(bold), fontsize=size) > width and len(word) > 1:
                cut = len(word)
                while cut > 1 and pymupdf.get_text_length(word[:cut], fontname=_font(bold), fontsize=size) > width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        if line or not lines:
            lines.append(line)
    return lines


class _Writer:
    def __init__(self, doc: pymupdf.Document, header: str, sub: str):
        self.doc, self.header, self.sub = doc, header, sub
        self.page = None
        self.y = 0.0

    def new_page(self) -> None:
        self.page = self.doc.new_page(width=WIDTH, height=HEIGHT)
        self.page.insert_text((LEFT, TOP), self.header, fontname="hebo", fontsize=12, color=_RED)
        self.page.insert_text((LEFT, TOP + 13), self.sub, fontname="helv", fontsize=7.5, color=_GREY)
        self.page.draw_line((LEFT, TOP + 19), (RIGHT, TOP + 19), color=_RULE, width=0.8)
        self.y = TOP + 34

    def room(self, needed: float) -> None:
        if self.page is None or self.y + needed > BOTTOM:
            self.new_page()

    def text(self, value, *, size=8.5, bold=False, colour=_INK, x=LEFT, width=RIGHT - LEFT, gap=2.0) -> None:
        for line in _wrap(value, width, size, bold):
            self.room(size + gap)
            self.page.insert_text((x, self.y + size), line, fontname=_font(bold), fontsize=size, color=colour)
            self.y += size + gap

    def field(self, label: str, value, *, fill=None, colour=_INK) -> None:
        """A label and its value beside it, the value wrapped; a coloured band when `fill`."""
        if value in (None, "", []):
            return
        lines = _wrap(value, RIGHT - LEFT - LABEL_W - 8, 8.5)
        height = len(lines) * 10.5 + 4
        self.room(min(height, 60))
        top = self.y
        if fill is not None and top + height <= BOTTOM:
            self.page.draw_rect(pymupdf.Rect(LEFT - 3, top - 1, RIGHT + 3, top + height - 1), color=None, fill=fill)
        self.page.insert_text((LEFT, self.y + 8.5), label, fontname="hebo", fontsize=8, color=_GREY)
        for line in lines:
            self.room(10.5)
            self.page.insert_text((LEFT + LABEL_W, self.y + 8.5), line, fontname="helv", fontsize=8.5, color=colour)
            self.y += 10.5
        self.y += 4

    def rule(self) -> None:
        self.room(8)
        self.page.draw_line((LEFT, self.y + 2), (RIGHT, self.y + 2), color=_RULE, width=0.6)
        self.y += 8


def _outcome(review: dict | None) -> tuple[str, str | None]:
    """What the review did with the item, said in a line, and its band colour."""
    if not review:
        return "Not reviewed by Opus: no review of the readings shown is in force.", "warn"
    if review.get("state") != "completed":
        return (f"Not reviewed by Opus ({str(review.get('state')).replace('_', ' ')}"
                f"{': ' + str(review.get('reason')) if review.get('reason') else ''}). Verify it on the drawings."), "warn"
    said = f"Unresolved: Opus could not decide it from the evidence ({review.get('confidence') or '-'} confidence)."
    if review.get("downgraded"):
        said += (f" Opus said {str(review.get('said') or '').replace('_', ' ')}, which was not accepted: "
                 f"{review['downgraded']}.")
    return said, None


def _pictures(w: _Writer, folder: Path | None, pictures: list[dict]) -> None:
    if not pictures:
        w.field("Drawing views", "No pictures were kept for this item (the review did not draw any, or it was made "
                                 "before pictures were kept). Open the drawing and sheet named above.", fill=_WARN)
        return
    w.room(14)
    w.text("The drawing as the review saw it -- each point read ringed in red and numbered:", size=8.5, bold=True)
    w.y += 2
    for i in range(0, len(pictures), 2):
        row = pictures[i:i + 2]
        captions = []
        for pic in row:
            nums = "; ".join(f"{x['n']}: {x['text']}" for x in pic.get("numbers") or [])
            cap = (f"{pic.get('id')} - {pic.get('drawing') or ''}, {', '.join(pic.get('sheets') or [])}"
                   f"{f', about {pic.get('size_m')} m across' if pic.get('size_m') else ''}. "
                   f"This item's points: {nums or '-'}."
                   + (" Other numbers belong to items reviewed with it." if pic.get("shared") else ""))
            captions.append(_wrap(cap, PICTURE, 7))
        tallest = max(len(c) for c in captions) * 9 + 6
        w.room(PICTURE + tallest)
        for j, (pic, cap) in enumerate(zip(row, captions)):
            x = LEFT + j * (PICTURE + 14)
            rect = pymupdf.Rect(x, w.y, x + PICTURE, w.y + PICTURE)
            path = (folder / pic["file"]) if folder is not None and pic.get("file") else None
            if path is not None and path.is_file():
                w.page.insert_image(rect, filename=str(path), keep_proportion=True)
                w.page.draw_rect(rect, color=_RULE, width=0.6)
            else:
                w.page.draw_rect(rect, color=_RULE, width=0.6, fill=_WARN)
                w.page.insert_text((x + 8, w.y + 18), "picture no longer kept", fontname="helv", fontsize=8,
                                   color=_GREY)
            yy = w.y + PICTURE + 9
            for line in cap:
                w.page.insert_text((x, yy), line, fontname="helv", fontsize=7, color=_INK)
                yy += 9
        w.y += PICTURE + tallest + 6


def _case(w: _Writer, n: int, total: int, g: dict, floors: dict, folder: Path | None) -> None:
    review = g.get("review") or {}
    w.new_page()
    w.text(f"Case {n} of {total}: {g.get('equipment')}", size=13, bold=True)
    w.text(f"{g.get('system') or ''} - {g.get('ref') or ''}", size=8.5, colour=_GREY)
    w.y += 4
    said, band = _outcome(review)
    w.field("Opus review", said, fill=_WARN if band else _SKY)
    w.field("What remains unclear", review.get("unclear"), fill=_SKY)
    w.field("What to verify", review.get("engineer_action"), fill=_SKY)
    w.rule()
    w.field("Drawing", g.get("source"))
    w.field("Where it was read", g.get("ref"))
    w.field("Proposed floors", ", ".join(g.get("proposed_floors") or []) or "not identified")
    w.field("Proposed quantity", g.get("proposed_qty") if g.get("proposed_qty") is not None else "not known")
    w.field("Interface (matrix)", f"{g.get('contacts')} - {g.get('monitoring')} monitoring / {g.get('control')} "
                                  "control each")
    w.field("Why the reading held it", g.get("reason"))
    w.field("What the reading found", g.get("evidence"))
    if g.get("tags"):
        w.field("Tags", ", ".join(g["tags"]))
    w.field("Opus's reasoning", review.get("rationale"))
    w.field("Evidence it checked", review.get("coverage_checked"))
    cited = "; ".join(f"{e.get('id')} ({e.get('what')})" if e.get("what") else str(e.get("id"))
                      for e in review.get("evidence") or [])
    w.field("Evidence it cited", cited)
    not_shown = "; ".join(f"{v.get('id')}: {v.get('why')}" for v in review.get("views_not_shown") or [])
    w.field("Views not drawn", not_shown, fill=_WARN)
    w.field("Item id", g.get("id"), colour=_GREY)
    w.rule()
    _pictures(w, folder, review.get("pictures") or [])


def build(view: dict, folder: Path | None, *, item_id: str | None = None) -> pymupdf.Document:
    """The document: a summary page, then each open item's pages (one item only
    when `item_id`). `folder`: where the review in force kept its pictures."""
    items = [g for g in view.get("verification") or [] if item_id is None or g["id"] == item_id]
    p = view.get("project") or {}
    rv = view.get("review") or {}
    doc = pymupdf.open()
    stamp = datetime.now().strftime("%d %b %Y %H:%M")
    w = _Writer(doc, "FIRE ALARM INTERFACES - CASES FOR ENGINEER VERIFICATION",
                f"EP-{p.get('ep_number')} - {p.get('name') or ''}   |   generated {stamp}"
                + (f"   |   Opus review of run {rv.get('run_id')} ({rv.get('model')}, {rv.get('effort')})"
                   if rv.get("run_id") else ""))
    floors = {f["key"]: f["name"] for f in view.get("floors") or []}
    if item_id is None:
        w.new_page()
        w.text("Cases the Opus review could not decide", size=13, bold=True)
        w.y += 2
        w.text("Every item below is still in Verification Required: the drawings did not settle it, and the Opus "
               "review of the original drawings either could not decide it or did not run on it. Nothing in it is "
               "counted until the engineer says where and how many, or that it is not an interface. Each case "
               "gives what remains unclear, what to verify, and the pictures of the drawing the review was shown.",
               size=8.5)
        w.y += 6
        if rv and not rv.get("applies"):
            w.field("Note", "The Opus review in force was made on other readings than the ones shown: its notes are "
                            "not attached to these items.", fill=_WARN)
        if not items:
            w.text("Nothing is left to verify.", size=9, bold=True)
        for n, g in enumerate(items, 1):
            review = g.get("review") or {}
            state = ("unresolved" if review.get("state") == "completed" else
                     f"not reviewed ({review.get('state')})" if review else "not reviewed")
            w.text(f"{n}. {g.get('equipment')} - {g.get('ref')}  [{state}]", size=8.5, bold=True)
            w.text(review.get("engineer_action") or g.get("reason"), size=8, colour=_GREY, x=LEFT + 12,
                   width=RIGHT - LEFT - 12)
            w.y += 3
    for n, g in enumerate(items, 1):
        _case(w, n, len(items), g, floors, folder)
    for i, page in enumerate(doc, 1):
        page.insert_text((RIGHT - 60, HEIGHT - 22), f"Page {i} of {doc.page_count}", fontname="helv", fontsize=7,
                         color=_GREY)
    return doc
