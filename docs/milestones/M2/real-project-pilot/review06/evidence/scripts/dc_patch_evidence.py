import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\document_control.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


sub('PARSER_VERSION = "parse-2026-09-28.6"',
    'PARSER_VERSION = "parse-2026-09-28.7"   # M2 review 06: raw evidence of transmittals and labelled form fields; OCR title blocks\n'
    '# parse-2026-09-28.6: M2 review 05 (title block by position, reference roles)')
sub('''                if not found and not scan:
                    sheet = untracked_sheet_observation(text)
                    if sheet is not None:
                        observations.append({"page": number, **sheet})''',
    '''                if not found and not scan:
                    untracked = untracked_sheet_observation(text)
                    if untracked is not None:
                        observations.append({"page": number, **untracked})
                # Raw evidence the register's grammar does not carry (M2 review 06, H-02 / H-03 / H-05): a
                # transmittal's own number, parties and listed documents; a form's labelled identity and stated
                # purpose. Observations only: no register record, status or category is made of them.
                observations.extend(page_evidence(page, text, number, scan=scan, found=found, sheet=sheet,
                                                  observations=observations))''')
sub('''def _controlled_number(value: str) -> bool:''', '''EVIDENCE_PAGE_LIMIT = 4


def page_evidence(page, text: str, number: int, *, scan: bool, found: list, sheet, observations: list) -> list[dict]:
    """The page's raw evidence beyond the records (M2 review 06): every transmittal as one (`transmittals.observe`,
    merged into a transmittal observation the reader already made), and a form's labelled identity and purpose on
    a page that gave no record (`labelled_fields`), on the first EVIDENCE_PAGE_LIMIT pages."""
    from app.services import labelled_fields, title_block, transmittals

    out = []
    if transmittals.looks_like_transmittal_form(text):
        seen = transmittals.observe(text, source="ocr" if scan else "text", page=number)
        existing = next((o for o in observations if o.get("page") == number and o.get("kind") == "transmittal"), None)
        if existing is not None:
            existing.update({k: v for k, v in seen.items() if k not in ("records",) and (v or k not in existing)})
            if existing.get("reference"):
                existing.pop("flags", None) if existing.get("flags") == ["reference_unread"] else None
        else:
            out.append(seen)
        return out
    if found or sheet is not None or number > EVIDENCE_PAGE_LIMIT:
        return out
    try:
        fields = (labelled_fields.read_text(text) if scan else
                  labelled_fields.read_lines(title_block.page_lines(page), page.rect.width, page.rect.height))
    except Exception as exc:  # noqa: BLE001 -- evidence is best effort: the page's reading stands without it
        return [{"page": number, "kind": "form_identity", "version": labelled_fields.FIELDS_VERSION, "error": f"{type(exc).__name__}: {exc}"[:200]}]
    if fields is not None:
        out.append(fields.observation(number))
    return out


def _controlled_number(value: str) -> bool:''')
p.write_text(s, encoding="utf-8")

q = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\document_sync.py")
t = q.read_text(encoding="utf-8")
old = '''        records = transmittals.read_transmittal(read_word_text(path), relative,
                                                datetime.fromtimestamp(stat.st_mtime_ns / 1e9, timezone.utc))
        notes = ()'''
new = '''        word = read_word_text(path)
        records = transmittals.read_transmittal(word, relative, datetime.fromtimestamp(stat.st_mtime_ns / 1e9, timezone.utc))
        # Every transmittal as raw evidence (M2 review 06, H-05): its number, parties and listed documents, whether
        # or not it carries a sample the register records.
        observations = [transmittals.observe(word, source="word")]
        notes = ()'''
assert t.count(old) == 1, "word branch"
t = t.replace(old, new)
q.write_text(t, encoding="utf-8")
print("ok")
