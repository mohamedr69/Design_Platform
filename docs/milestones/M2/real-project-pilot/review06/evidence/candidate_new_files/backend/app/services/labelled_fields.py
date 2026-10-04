"""Labelled fields of a form page, as raw evidence (M2 review 06: H-02 / H-03).

A cover sheet, a client's submittal form or a consultant's review form names its own document in a labelled field
("Document No. | Revision | Date" over "EP-28605 /MA/FA/201 | 00 | 20.09.2024"; "Reference No MTS E 0018"; "Review
Reference: CRS-DOC-02006"). The reference grammar of the register (`document_control.REF`) does not recognise most of
these, and before this module the page left no trace. Here the literal identity is kept with its label, the page and
the region it was read from, and the page's stated purpose (its heading) beside it -- as an observation. Nothing here
makes a register record, a business status or a category: what the document *is* is decided later, from the source,
not from the shape of its number ("/MA/" does not mean one document type).

Two readings: by geometry on a page with a text layer (the same cell rules as the title block), and by pattern on OCR
text (a scan), where the value must follow its label on the same line.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services import title_block as tb

FIELDS_VERSION = "fields-2026-09-29.1"

_IDENTITY_LABEL = re.compile(
    r"^(?P<label>(?:(?:DOCUMENT|DOC|REFERENCE|REF|SUBMITTAL|TRANSMITTAL|SERIAL|REVIEW\s+REFERENCE|SUBMITTED\s+REFERENCE|OUR\s+REF|"
    r"AASS\s+REF|FULL\s+DOCUMENT\s+REFERENCE)\.?\s*(?:NO\.?|NUMBER|REF\.?|REFERENCE)?))\s*[:.]?\s*(?P<inline>[A-Z0-9][A-Z0-9 ./_&()-]{3,})?$",
    re.I)
_REVISION_LABEL = re.compile(r"^(?:REVISION|REV)\.?\s*(?:NO\.?)?\s*:?\s*(?P<inline>[A-Z0-9]{1,4})?$", re.I)
_DATE_LABEL = re.compile(r"^DATE\s*:?\s*(?P<inline>\d{1,2}[./-]\d{1,2}[./-]\d{2,4})?$", re.I)
_DATE_VALUE = re.compile(r"^\d{1,2}[./-](?:\d{1,2}|[A-Z]{3})[./-]\d{2,4}$", re.I)
PURPOSES = (
    ("material submittal", r"MATERIAL\s+SUBMITTAL"), ("method statement", r"METHOD\s+STATEMENT"),
    ("shop drawing submittal", r"SHOP\s*DRAWINGS?\s+SUBMITTAL"), ("document transmittal", r"DOCUMENTS?\s+TRANSMIT+AL"),
    ("material sample", r"MATERIAL\s+SAMPLE|SAMPLE\s+APPROVAL"), ("construction review form", r"CONSTRUCTION\s+REVIEW\s+FORM"),
    ("consultant comments", r"CONSULTANT(?:'S)?\s+COMMENTS"), ("technical submittal", r"TECHNICAL\s+SUBMITTAL"),
    ("test certificate", r"TEST\s+CERTIFICATE|CERTIFICATE\s+OF\s+CONFORMITY"), ("design sheet", r"DESIGN\s+SHEET"),
    ("schedule of equipment", r"SCHEDULE\s+OF\s+EQUIPMENT"), ("quotation", r"\bQUOTATION\b"),
    ("testing and commissioning request", r"TESTING\s+AND\s+COMMISSIONING\s+REQUEST"),
)


@dataclass(frozen=True)
class FormFields:
    identity: str | None
    identity_label: str | None
    revision: str | None
    date: str | None
    purpose: str | None
    purpose_text: str | None
    source: str
    region: tuple | None = None
    notes: tuple = field(default=())

    def observation(self, page: int) -> dict:
        return {"page": page, "kind": "form_identity", "version": FIELDS_VERSION, "identity": self.identity,
                "identity_label": self.identity_label, "revision": self.revision, "date": self.date, "purpose": self.purpose,
                "purpose_text": self.purpose_text, "source": self.source, "region": list(self.region) if self.region else None,
                "notes": list(self.notes)}


def _identity_shaped(text: str) -> bool:
    """An identifier as printed: a digit, no lower-case words, and either a separator ("/", "-", ".", "_") or at most
    four upper-case tokens ("MTS E 0018"). Not a date, not a sentence."""
    text = text.strip()
    if not (4 <= len(text) <= 60) or not re.search(r"\d", text) or _DATE_VALUE.match(text):
        return False
    if re.search(r"[a-z]{2,}", text):
        return False
    tokens = text.split()
    return bool(re.search(r"[/._-]", text)) or (len(tokens) <= 4 and all(re.fullmatch(r"[A-Z0-9&]+", t) for t in tokens))


def purpose_of(texts: list[str]) -> tuple[str | None, str | None]:
    for text in texts:
        for name, pattern in PURPOSES:
            if re.search(pattern, text, re.I):
                return name, " ".join(text.split())[:120]
    return None, None


def read_lines(lines: list, width: float, height: float) -> FormFields | None:
    """By geometry, on a page's text runs (`title_block.page_lines`)."""
    identity = label_text = revision = date = None
    region = None
    for label in sorted((l for l in lines if _IDENTITY_LABEL.match(l.text)), key=lambda l: (l.y0, l.x0)):
        match = _IDENTITY_LABEL.match(label.text)
        value, _why = tb._cell_value(lines, label, match.group("inline"), _identity_shaped, right_pad=30 * label.h)
        if value:
            identity, label_text = " ".join(value.split()), match.group("label").strip()
            region = (round(label.x0, 1), round(label.y0, 1), round(label.x1, 1), round(label.y1, 1))
            for rev in (l for l in lines if _REVISION_LABEL.match(l.text) and tb._same_row(l, label)):
                v, _ = tb._cell_value(lines, rev, _REVISION_LABEL.match(rev.text).group("inline"), tb._rev_shaped, right_pad=6 * rev.h)
                if v:
                    revision = v.strip()
                    break
            for dl in (l for l in lines if _DATE_LABEL.match(l.text) and tb._same_row(l, label)):
                v, _ = tb._cell_value(lines, dl, _DATE_LABEL.match(dl.text).group("inline"), lambda t: bool(_DATE_VALUE.match(t.strip())),
                                      right_pad=10 * dl.h)
                if v:
                    date = v.strip()
                    break
            break
    top = sorted((l for l in lines if l.y0 < height * 0.6), key=lambda l: -(l.y1 - l.y0))
    purpose, purpose_text = purpose_of([l.text for l in top[:40]])
    if identity is None and purpose is None:
        return None
    return FormFields(identity, label_text, revision, date, purpose, purpose_text, "text", region)


_OCR_IDENTITY = re.compile(
    r"(?P<label>\b(?:Review|Submitted|Full\s+Document|AASS|Our)?\s*(?:Document|Doc|Reference|Ref|Submittal|Transmittal)\b\.?\s*(?:No\b\.?|Number)?)"
    r"\s*[:|.\]\[]{0,4}\s*(?P<value>[A-Z0-9][A-Z0-9 ./_&-]{3,40})", re.I)


def read_text(text: str) -> FormFields | None:
    """By pattern, on OCR text: a value right after its label on the same line; nothing is joined across lines."""
    identity = label = None
    for line in (text or "").splitlines():
        found = _OCR_IDENTITY.search(line)
        if found:
            value = found.group("value").strip(" .|:-")
            value = re.split(r"\s{2,}|\s\|", value)[0].strip()
            if _identity_shaped(value) and not re.fullmatch(r"(?:No|Number|Date)\b.*", value, re.I):
                identity, label = value, " ".join(found.group("label").split())
                break
    purpose, purpose_text = purpose_of((text or "").splitlines()[:40])
    if identity is None and purpose is None:
        return None
    return FormFields(identity, label, None, None, purpose, purpose_text, "ocr")
