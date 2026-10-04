"""Review 05 (R5-01) reader changes to document_control.py, applied as exact replacements."""
import pathlib, sys

p = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app\services\document_control.py")
s = p.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:120])
    s = s.replace(old, new)


# 1. parser version
sub('PARSER_VERSION = "parse-2026-09-28.5"', 'PARSER_VERSION = "parse-2026-09-28.6"')

# 2. a wrapped segment is never a field label (P-10)
sub('''_SEGMENT = r"(?:-[A-Z0-9]+|-\\n[A-Z][A-Z0-9]*)"''',
    '''# The wrapped segment is never the next field's label: a scanned form wraps "…-PJW-ZZZ-" over its
# "Rev.01" label, and joining the two read "…-ZZZ-Rev" as the number (M2 review 05, pilot P-10).
_SEGMENT = r"(?:-[A-Z0-9]+|-\\n(?!(?:REV|REVISION|DATE|REF|NO|PAGE|SHEET|TITLE)\\b)[A-Z][A-Z0-9]*)"''')

# 3. candidate roles
sub('''    incomplete: bool = False

    @property
    def category(self) -> str:''', '''    incomplete: bool = False
    # Where the page names this reference as another document's -- "REFER TO DWG No. …", "Refer to …
    # for comments", "see drawing …" -- it is a cross-reference: never the page's own identity (M2
    # review 05, pilot P-07 / P-08).
    cross_reference: bool = False
    # Where the page's own label precedes it on its line ("Ref No : …", "Reference: …").
    labelled: bool = False
    # Where the text right before it on its line is a lone letter or the tail of another hyphenated
    # run ("R 1029-…", "…-CO-EL V-EL-MTG-…"): a scanner's text layer split the number, and where it
    # starts is not known (pilot P-10). Read, and marked so rather than guessed at.
    uncertain_start: bool = False

    @property
    def category(self) -> str:''')

sub('''        base = reference.split("/", 1)[0]
        kind = "sheets" if "/" in reference else "serial" if re.search(r"-\\d{2,}[A-Z]?$", base, re.I) else "other"
        out.append(ReferenceCandidate(reference, match.group(1).upper(), start, match.end(), kind,
                                      incomplete=raw.rstrip(".").endswith("-")))
    return out
''', '''        base = reference.split("/", 1)[0]
        kind = "sheets" if "/" in reference else "serial" if re.search(r"-\\d{2,}[A-Z]?$", base, re.I) else "other"
        before = text[text.rfind("\\n", 0, start) + 1:start]
        out.append(ReferenceCandidate(reference, match.group(1).upper(), start, match.end(), kind,
                                      incomplete=raw.rstrip(".").endswith("-"),
                                      cross_reference=bool(_CROSS_REFERENCE.search(before)),
                                      labelled=bool(_OWN_LABEL.search(before) or glued),
                                      uncertain_start=bool(_SPLIT_START.search(before))))
    return out


_CROSS_REFERENCE = re.compile(r"(?:\\brefer(?:ence)?\\s*(?:to)?|\\bsee|\\bas\\s+per)\\s*(?:the\\s+)?"
                              r"(?:(?:dwg|drawing|sheet|detail)s?\\.?\\s*(?:no\\.?|number)?\\s*[:.]?\\s*)?$", re.I)
_OWN_LABEL = re.compile(r"(?:\\bref(?:erence)?\\.?\\s*(?:no\\.?)?|\\bour\\s+ref\\.?|\\bsubmittal\\s+no\\.?|\\bdoc(?:ument)?\\.?\\s*no\\.?)"
                        r"\\s*[:|.]?\\s*$", re.I)
_SPLIT_START = re.compile(r"(?:^|[\\s|:])[A-Za-z] $|-[A-Z0-9]+ $")
''')

sub('''def first_reference(text: str) -> ReferenceCandidate | None:
    """The first reference on the page that is not a date; None for none."""
    found = reference_candidates(text)
    return found[0] if found else None''', '''def first_reference(text: str) -> ReferenceCandidate | None:
    """The first reference on the page that is not a date and not a cross-reference to another
    document ("REFER TO DWG No. …"); None for none."""
    found = [c for c in reference_candidates(text) if not c.cross_reference]
    return found[0] if found else None''')

# 4. a date is not a revision (P-07)
sub('''REV = re.compile(r"\\b(?:MAS\\s+|MAR\\s+|SDW\\s+|DWG\\s+|SD\\s+|SAR\\s+)?REV(?:ISION)?\\.?\\s*[:.-]?\\s*\\n?\\s*R?\\s*(\\d{1,3})\\b(?!\\s*\\.?\\))", re.I)''',
    '''# The number is not the start of a date: "Rev.\\n10.09.2024" is a date under the label, not revision 10
# (JAM-SD-FA-002, M2 review 05, pilot P-07).
REV = re.compile(r"\\b(?:MAS\\s+|MAR\\s+|SDW\\s+|DWG\\s+|SD\\s+|SAR\\s+)?REV(?:ISION)?\\.?\\s*[:.-]?\\s*\\n?\\s*R?\\s*(\\d{1,3})\\b(?!\\s*\\.?\\))(?![./-]\\d)", re.I)''')

# 5. raw floor (P-05)
sub('''    # Last resort: the whole line, where it is a floor and nothing else
    # ("GROUND FLOOR PLAN"). Never for a file name -- a hundred characters
    # of drawing number and description is not a floor, and printed as one
    # it filled the column.
    return " ".join(title.split()) if whole and "FLOOR" in title.upper() else None''',
    '''    # Last resort: the word the title prints in front of FLOOR, as printed ("FIRST FLOOR", "HC FLOOR",
    # "MEZZANINE FLOOR"). Not the whole line: "FIRST FLOOR FIRE ALARM LAYOUT" kept whole became the
    # floor "FIRST FIRE ALARM" downstream (M2 review 05, pilot P-05); what a floor word means -- its
    # level, its elevation, an alias -- is not read here. Never for a file name -- a hundred characters
    # of drawing number and description is not a floor, and printed as one it filled the column.
    if not whole:
        return None
    found = re.search(r"\\b([A-Z][A-Z.]*|\\d+[A-Z]*)\\s+FLOOR\\b", title, re.I)
    return f"{found.group(1)} FLOOR".upper() if found and found.group(1).upper() not in _NOT_A_FLOOR_WORD else None


# Words a title puts before FLOOR that do not name one ("THE FLOOR", "RAISED FLOOR" is a floor type).
_NOT_A_FLOOR_WORD = {"THE", "EACH", "EVERY", "PER", "ALL", "RAISED", "FALSE", "ACCESS", "ON", "OF", "AND", "TO", "FOR"}''')

# 6. parse_page: title block, reply header, transmittal form, listed items
sub('''def parse_page(text: str, path: str, modified: datetime, page: int) -> list[ControlledDocument]:''',
    '''# A form's listing of what it carries: the numbers under it are the listed items, not the page's own.
_LISTING_HEADER = re.compile(r"Attachment\\s+Details|Shop\\s*drawing\\s+Reference|\\bITEM\\b[^\\n]{0,6}Document\\s+No", re.I)


def _is_transmittal_form(text: str) -> bool:
    """A document transmittal (the scanned acknowledgement of one): its heading and the form's own field
    labels. The numbers it lists are the items it carries (pilot P-09); its own number is the TR number,
    read by `transmittals`, never the first reference on it."""
    from app.services import transmittals

    return bool(transmittals._OCR_HEADING.search(text)) and sum(1 for cue in transmittals._OCR_FORM_CUES if cue.search(text)) >= 2


def _listed(text: str, candidate: ReferenceCandidate) -> bool:
    header = _LISTING_HEADER.search(text)
    return bool(header) and candidate.start > header.start()


def parse_page(text: str, path: str, modified: datetime, page: int, sheet=None) -> list[ControlledDocument]:
    """`sheet`: the page's title block read by position (`title_block.read_page`), for a drawing sheet
    with a text layer; its own number and REV cell stand for the page's (M2 review 05, P-06 / P-07)."""''')

sub('''    if REPLY_SHEET.search(text) and not SUBMISSION_FORM.search(text):
        if candidate is None: return []
        decision, evidence = read_decision(text)''', '''    if REPLY_SHEET.search(text) and not SUBMISSION_FORM.search(text):
        # The reply's own header names the submission it answers ("Ref No : …-010029"); the comments
        # quote others ("Refer to …-010034 for comments"), which are never its reference (pilot P-08).
        # A reply whose only numbers are quoted ones names nothing of its own.
        replies = [c for c in reference_candidates(text) if not c.cross_reference]
        candidate = next((c for c in replies if c.labelled), replies[0] if replies else None)
        if candidate is None: return []
        decision, evidence = read_decision(text)''')

sub('''    match = candidate
    if match:
        reference = candidate.reference''', '''    if _is_transmittal_form(text):
        return []
    own = sheet.number if sheet is not None and sheet.number and not SUBMISSION_FORM.search(text) else None
    drawing_value = drawing_match.group(1).strip() if drawing_match else None
    if own:
        # The title block's own number cell (title_block): the page's identity, whatever the text lists
        # first. In the controlled numbering it is read as a reference; otherwise as a drawing number.
        controlled = [c for c in reference_candidates(own) if c.start == 0 and c.reference.upper() == own.upper().rstrip("-.")]
        candidate = controlled[0] if controlled else None
        drawing_value = None if controlled else own
    elif candidate is not None and _listed(text, candidate):
        # The first number sits in the form's listing of what it carries (an attachment, a listed
        # drawing): the page's own number was not read -- a scanned cover whose reference line OCR lost.
        own_before = [c for c in reference_candidates(text) if not c.cross_reference and not _listed(text, c)]
        candidate = own_before[0] if own_before else None
        if candidate is None:
            return []
    match = candidate
    if match:
        reference = candidate.reference''')

sub('''    elif drawing_match and re.search(r"FIRE\\s*ALARM|EMERGENCY\\s*LIGHT|VOICE\\s*EVACUATION", text, re.I):
        reference, category = drawing_match.group(1).strip(), "drawings"
        if not TITLE.search(text): return []''', '''    elif drawing_value and re.search(r"FIRE\\s*ALARM|EMERGENCY\\s*LIGHT|VOICE\\s*EVACUATION", text, re.I):
        reference, category = drawing_value, "drawings"
        if not TITLE.search(text) and not own: return []''')

sub('''    revision_match = REV.search(text)
    suffix = re.search(r"-R(\\d+)$", reference.split("/", 1)[0], re.I)''', '''    flags: list[str] = []
    # A drawing sheet whose title block was read by position: its REV cell is the printed revision, and
    # the text's REV runs -- the revision history's, the reference table's, a date under the label -- are
    # not read at all (P-06). A sheet whose REV cell and latest revision-history row disagree prints no
    # one revision: both are kept (the observation), the record is flagged, and its revision comes from
    # what else there is (P-06: BBY006 L58 R01 prints REV. NO. 00 over a history whose latest row is 01).
    geometry = sheet is not None and category == "drawings" and not SUBMISSION_FORM.search(text) \\
        and bool(sheet.number or sheet.revision)
    revision_match = None if geometry else REV.search(text)
    if geometry and sheet.revision:
        if sheet.conflict:
            flags.append("revision_conflict")
        elif re.fullmatch(r"\\d{1,3}", sheet.revision):
            revision_match = re.match(r"(\\d+)", sheet.revision)
        else:
            # Printed as letters ("AB", "C1"): kept as printed; the register's R-number is not made of it.
            flags.append("printed_revision_unmapped")
    suffix = re.search(r"-R(\\d+)$", reference.split("/", 1)[0], re.I)''')

sub('''        block_title, layout = title_block(text, reference)
        # The revision the block prints, kept as printed beside the one
        # above: on a sheet filed under R1 that still says 00, both are facts.
        printed = printed_revision(text, reference)''', '''        block_title, layout = title_block(text, reference)
        # The revision the block prints, kept as printed beside the one
        # above: on a sheet filed under R1 that still says 00, both are facts.
        printed = sheet.revision if geometry else printed_revision(text, reference)''')

sub('''    flags = ("reference_incomplete",) if candidate is not None and candidate.incomplete else ()
    return [ControlledDocument(code, title, path, modified, reference, revision, decision, floor, evidence, page, category=category,
                               printed_revision=printed, revision_source=revision_source, flags=flags)]''',
    '''    if candidate is not None and candidate.incomplete:
        flags.append("reference_incomplete")
    if candidate is not None and candidate.uncertain_start and not own:
        flags.append("reference_uncertain")
    return [ControlledDocument(code, title, path, modified, reference, revision, decision, floor, evidence, page, category=category,
                               printed_revision=printed, revision_source=revision_source, flags=tuple(flags))]''')

# 7. read_open_pdf: the title block, and a bounded header re-read for a scanned cover
sub('''                text = page_text(page, index, page_texts)
                with timed("deterministic_extract"):
                    found = parse_page(text, filename, modified, number)''', '''                text = page_text(page, index, page_texts)
                sheet = _sheet_of(page, text, number, observations)
                with timed("deterministic_extract"):
                    found = parse_page(text, filename, modified, number, sheet=sheet)''')

sub('''                            with timed("deterministic_extract"):
                                ocr_found = parse_page(ocr_text, filename, modified, number)
                                decision, evidence = read_decision(ocr_text)''', '''                            with timed("deterministic_extract"):
                                ocr_found = parse_page(ocr_text, filename, modified, number)
                            if not found and not ocr_found and scan and _LISTING_HEADER.search(ocr_text) \\
                                    and not _is_transmittal_form(ocr_text):
                                # A scanned cover whose own reference line the full-page OCR lost, while it
                                # read the attachments listed under it (NCC LACASA covers): the header band
                                # read once more, on its own, at the same scale -- bounded, cached by content.
                                band = _ocr_band_text(page, sha256, index)
                                counted("ocr_band_retries")
                                band_found = parse_page(band + "\\n" + ocr_text, filename, modified, number)
                                observations.append({"page": number, "kind": "ocr_retry", "region": "header band",
                                                     "used": bool(band_found)})
                                if band_found:
                                    ocr_found, ocr_text = band_found, band + "\\n" + ocr_text
                            with timed("deterministic_extract"):
                                decision, evidence = read_decision(ocr_text)''')

sub('''                                    if transmittals.looks_like_transmittal(ocr_text):
                                        sent = transmittals.from_ocr(ocr_text, filename, modified, page=number)
                                        if promote:
                                            ocr_found = sent
                                        elif sent:
                                            observations.append({"page": number, "kind": "transmittal", "records": [observed_record(r) for r in sent]})''',
    '''                                    if transmittals.looks_like_transmittal(ocr_text):
                                        sent = transmittals.from_ocr(ocr_text, filename, modified, page=number)
                                        if promote:
                                            ocr_found = sent
                                        elif sent:
                                            observations.append({"page": number, "kind": "transmittal", "records": [observed_record(r) for r in sent]})
                                    elif _is_transmittal_form(ocr_text):
                                        # A transmittal whose TR number OCR did not read as one ("18/0127/26";
                                        # re-reads gave "7R", "1R", "TR" -- no read settles it): what was read
                                        # is kept as read, and no number is made of it (pilot P-09).
                                        observations.append({"page": number, "kind": "transmittal", "records": [],
                                                             "reference": None, "flags": ["reference_unread"],
                                                             "raw_reference": transmittals.raw_reference(ocr_text)})''')

sub('''def _sheet_numbers(reference: str) -> set[str]:''', '''def _controlled_number(value: str) -> bool:
    found = reference_candidates(value)
    return bool(found) and found[0].start == 0 and found[0].reference.upper() == value.upper().rstrip("-.")


def _sheet_of(page, text: str, number: int, observations: list):
    """The page's title block read by position, for a drawing-sized page with a text layer; its facts kept
    as an observation of the page. A failure here leaves the page to the text reader, noted."""
    from app.services import title_block

    if len(text.strip()) < 80 or not title_block.is_drawing_sheet(page):
        return None
    try:
        with timed("title_block"):
            sheet = title_block.read_page(page, controlled=_controlled_number)
    except Exception as exc:  # noqa: BLE001 -- geometry failed: the text reader stands, as before
        observations.append({"page": number, "kind": "title_block", "version": title_block.TITLE_BLOCK_VERSION,
                             "error": f"{type(exc).__name__}: {exc}"[:200]})
        return None
    if sheet is not None:
        observations.append({"page": number, **sheet.observation()})
    return sheet


OCR_BAND_VARIANT = "band-1"


def _ocr_band_text(page, sha256: str | None, index: int) -> str:
    """The header band of a scanned page (8-32 % of its height, full width), OCRed on its own at the
    reader's render scale; cached by content like the page (variant `OCR_BAND_VARIANT`)."""
    from PIL import Image

    from app.services import page_cache

    cached = page_cache.get_ocr(sha256, index, OCR_BAND_VARIANT) if sha256 else None
    if cached is not None:
        counted("ocr_cache_hits")
        return cached
    rect = page.rect
    scale = _render_scale(page)
    clip = pymupdf.Rect(0, rect.height * 0.08, rect.width, rect.height * 0.32)
    with timed("ocr_render"):
        pixels = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip)
        image = Image.open(io.BytesIO(pixels.tobytes("png")))
    text = _ocr_images(page, [image])[0]
    if sha256:
        page_cache.put_ocr(sha256, index, text, OCR_BAND_VARIANT)
    return text


def _sheet_numbers(reference: str) -> set[str]:''')

p.write_text(s, encoding="utf-8")
print("patched")
