import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\transmittals.py")
s = p.read_text(encoding="utf-8")
s += r'''


# --- every transmittal as raw evidence (M2 review 06, H-05) ------------------------------------------------------

OBSERVE_VERSION = "transmittal-observe-2026-09-29.1"
_ITEM_CELLS = re.compile(r"^\|?\s*(\d{1,3})\s*\|\s*([A-Z0-9][^|]{3,70}?)\s*\|\s*([^|]{3,160}?)\s*(?:\|\s*([^|]{0,40}))?\|?\s*$", re.I)
_ITEM_OCR = re.compile(r"^\W{0,3}(\d{1,2})\s*\|?\s*([A-Z0-9][A-Z0-9/&._-]{5,}(?:\s*[-/][A-Z0-9/&._-]+)*)\s+\|?\s*(.{3,160})$", re.I)
_LABEL_VALUE = r"\W{0,8}([^\n|]{2,120})"


def _after(text: str, label: str) -> str | None:
    found = re.search(r"(?im)(?:^|\|)\s*" + label + _LABEL_VALUE, text)
    if not found:
        return None
    value = " ".join(found.group(1).split()).strip(" :|_.")
    return value or None


def observe(text: str, *, source: str, page: int = 1) -> dict:
    """What a transmittal says, whatever it carries: its own number (a TR number, or the literal token its reference
    field was read as when no TR number reads), date, recipient, attention, subject, the documents it lists and the
    receipt evidence on it. A receipt (a RECEIVED stamp, a signed "Received By") is a receipt: never an approval.
    Kept as an observation; the register's sample records are read by `read_transmittal` / `from_ocr` as before."""
    text = text or ""
    found = _OCR_REF.search(text)
    reference = f"TR/{found.group(1)}/{found.group(2)}" if found else None
    items = []
    for line in text.splitlines():
        m = _ITEM_CELLS.match(line.strip()) or _ITEM_OCR.match(line.strip())
        if m and re.search(r"\d", m.group(2)) and not re.match(r"(?:document|item)", m.group(2), re.I):
            items.append({"item": m.group(1), "document_no": " ".join(m.group(2).split()), "description": " ".join(m.group(3).split())[:160]})
    date = None
    date_label = re.search(r"\bDate\b", text, re.I)
    for d in _OCR_DATE.finditer(text, date_label.end() if date_label else 0):
        date = f"{d.group(1)}/{d.group(2)}/{d.group(3)}"
        break
    upper = text.upper()
    receipt = {"received_by_field": bool(re.search(r"RECEIVED\s*BY", upper)),
               "received_stamp": bool(re.search(r"\bRECEIVED\b(?!\s*BY)", upper)),
               "signature_field": bool(re.search(r"\bSIGNATURE\b", upper))}
    out = {"kind": "transmittal", "version": OBSERVE_VERSION, "page": page, "source": source, "reference": reference,
           "raw_reference": None if reference else raw_reference(text), "date": date,
           "to": _after(text, r"To\b"), "attn": _after(text, r"Att(?:n|entio)n?\.?"), "subject": _after(text, r"Subject"),
           "project_id": (re.search(r"EP-\s?\d{3,5}", _after(text, r"Project\s*ID") or "") or re.search(r"$^", "")) and
                         re.search(r"EP-\s?\d{3,5}", _after(text, r"Project\s*ID") or "").group(0),
           "items": items, "receipt": receipt, "records": []}
    if reference is None:
        out["flags"] = ["reference_unread"]
    return out


def looks_like_transmittal_form(text: str) -> bool:
    """A document transmittal by its heading and at least two of the form's own labels, with or without a TR
    number that OCR could read."""
    text = text or ""
    return bool(_OCR_HEADING.search(text)) and sum(1 for cue in _OCR_FORM_CUES if cue.search(text)) >= 2
'''
p.write_text(s, encoding="utf-8")
print("ok")
