"""M2 review 07 (E): a transmittal's listed submittal is not the transmittal's identity. When the form reader's
reference is one of the items a transmittal page lists, the row is not filed under it and no log record is made of
it; the relationship is kept as evidence."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\document_sync.py")
s = p.read_text(encoding="utf-8")
old = '''    stored = submittal_reader.stored(db, row.sha256 or "")
    row.reading_id = stored.id if stored else None
    extracted["form"] = reading
    if reading.get("is_submittal"):'''
new = '''    stored = submittal_reader.stored(db, row.sha256 or "")
    row.reading_id = stored.id if stored else None
    extracted["form"] = reading
    listed = listed_by_transmittal(extracted, reading)
    if reading.get("is_submittal") and listed is not None:
        # The page is a transmittal (or its acknowledgement) and the model's reference is an item it lists
        # (EP-29076 "FA MS & Sam B CBS Ack": its own TR/0127/26, listing 25H-S202-NCC-MAS-MEP-ELE-005-R3). The listed
        # submittal is not this document's identity: the row is not filed under it, and no log record is made of it.
        extracted["submission"] = listed
        return
    if reading.get("is_submittal"):'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''# --- reading files in other processes ----------------------------------------------------'''
new = '''ASSOCIATION_VERSION = "listed-item-2026-09-29.1"


def _doc_key(value) -> str:
    return re.sub(r"\\s+", "", str(value or "")).upper()


def listed_by_transmittal(extracted: dict, reading: dict) -> dict | None:
    """The relationship evidence when the form reader's reference is an item a transmittal page of this document lists
    -- the item's literal matches the reference, or is the reference's beginning cut at a line break (at least 12
    characters) -- else None. Only a transmittal observation's own item table decides it; nothing is inferred from
    the file name or a folder."""
    ref = _doc_key(reading.get("reference"))
    if not ref:
        return None
    for obs in (extracted or {}).get("observations") or []:
        if obs.get("kind") != "transmittal":
            continue
        for item in obs.get("items") or []:
            literal = item.get("document_no") if isinstance(item, dict) else None
            key = _doc_key(literal)
            if key and (key == ref or (len(key) >= 12 and ref.startswith(key))):
                return {"relationship": "transmits", "policy": ASSOCIATION_VERSION, "page": obs.get("page"),
                        "listed_item": reading.get("reference"), "listed_item_literal": literal,
                        "listed_item_revision": reading.get("revision"),
                        "transmittal_reference": obs.get("reference"), "transmittal_raw_reference": obs.get("raw_reference"),
                        "transmittal_reference_unread": not obs.get("reference"), "date": obs.get("date"),
                        "basis": "the form reader's reference is an item listed by this page's transmittal"}
    return None


# --- reading files in other processes ----------------------------------------------------'''
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok")
