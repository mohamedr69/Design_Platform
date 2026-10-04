import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\title_block.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


sub('TITLE_BLOCK_VERSION = "titleblock-1"',
    'TITLE_BLOCK_VERSION = "titleblock-2"   # M2 review 06: DRG/DOCUMENT labels, sub-label rows, nearest REV cell, OCR fallback\n'
    '# titleblock-1: M2 review 05 (P-06 / P-07)')
sub(r'(?:DRAWING|DWG)\.?\s*(?:NO|NUMBER|NR)\b', r'(?:DRAWING|DWG|DRG|DOCUMENT|DOC)\.?\s*(?:NO|NUMBER|NR)\b')
sub('''    conflict: bool = False                     # the REV cell and the history's latest row disagree''',
    '''    conflict: bool = False                     # the REV cell and the history's latest row disagree
    source: str = "text"                       # "text" (the page's text layer) or "ocr" (the title-block strip OCRed)''')
sub('''"references": list(self.references), "conflict": self.conflict, "title": self.title, "notes": list(self.notes)}''',
    '''"references": list(self.references), "conflict": self.conflict, "title": self.title, "notes": list(self.notes),
                "source": self.source}''')
sub('''def read_page(page, *, controlled=None) -> TitleBlock | None:
    """The title block of a drawing-sized page with a text layer; None for any other page."""
    if not is_drawing_sheet(page):
        return None
    lines = page_lines(page)
    if len(lines) < 5:
        return None
    return read(lines, page.rect.width, page.rect.height, controlled=controlled)''',
r'''def read_page(page, *, controlled=None, ocr_lines=None) -> TitleBlock | None:
    """The title block of a drawing-sized page; None for any other page. `ocr_lines(page, clip)`: where the text
    layer gives no own number (a title block drawn as vector outlines -- EP-8430's Nakheel/Dar sheets, M2 review 06
    H-01), the title-block strip is OCRed once and its word boxes read by the same geometry."""
    if not is_drawing_sheet(page):
        return None
    lines = page_lines(page)
    block = read(lines, page.rect.width, page.rect.height, controlled=controlled) if len(lines) >= 5 else None
    if ocr_lines is not None and (block is None or block.number is None):
        clip = title_block_strip(page)
        found = ocr_lines(page, clip)
        if found:
            ocr_block = read(found, page.rect.width, page.rect.height, controlled=controlled)
            if ocr_block is not None and (ocr_block.number or (block is None and ocr_block.revision)):
                import dataclasses

                return dataclasses.replace(ocr_block, source="ocr",
                                           notes=tuple(block.notes if block else ()) + ("title block read by OCR of its strip",) + ocr_block.notes)
    return block


def title_block_strip(page):
    """The strip of a sheet its title block occupies, in display coordinates: the right 28 % of a landscape sheet,
    the bottom 22 % of a portrait one."""
    import pymupdf

    r = page.rect
    return pymupdf.Rect(r.width * 0.72, 0, r.width, r.height) if r.width >= r.height else pymupdf.Rect(0, r.height * 0.78, r.width, r.height)


def ocr_word_lines(page, clip, *, dpi: int = 250, image_to_data=None) -> list[Line]:
    """The strip's OCR as Lines in display coordinates (Tesseract's own line grouping)."""
    import io

    import pymupdf
    from PIL import Image

    scale = dpi / 72
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip)
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    if image_to_data is None:
        from app.services.document_control import _tesseract

        image_to_data = _tesseract().image_to_data
    data = image_to_data(image, output_type="dict")
    groups: dict = {}
    for i, word in enumerate(data["text"]):
        if not str(word).strip() or float(data["conf"][i]) < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x0, y0 = data["left"][i] / scale + clip.x0, data["top"][i] / scale + clip.y0
        x1, y1 = x0 + data["width"][i] / scale, y0 + data["height"][i] / scale
        g = groups.setdefault(key, [x0, y0, x1, y1, []])
        g[0], g[1], g[2], g[3] = min(g[0], x0), min(g[1], y0), max(g[2], x1), max(g[3], y1)
        g[4].append(str(word).strip())
    return [Line(g[0], g[1], g[2], g[3], " ".join(g[4])) for g in groups.values()]''')
sub('''    below = _below(lines, label, _column(lines, label, right_pad=right_pad), 4 * label.h)
    if not below:
        return None, "no value"
    value = below[0]''',
r'''    below = _below(lines, label, _column(lines, label, right_pad=right_pad), 4 * label.h)
    # A cell may carry sub-labels between its label and its value (ISO 19650's "PROJECT CODE  ORIGINATOR ..." row
    # under "DRAWING CODE"): up to two rows of words with no digit are stepped over, never a row with one.
    skipped = 0
    while below and not shaped(below[0].text) and not re.search(r"\d", below[0].text) and len(below[0].text.split()) <= 5 and skipped < 2:
        below, skipped = below[1:], skipped + 1
    if not below:
        return None, "no value"
    value = below[0]''')
sub('''    for label in rev_labels:
        if any(_DESCRIPTION.match(l.text) for l in _row(lines, label)) or _under_reference_heading(lines, label):
            continue
        value, why = _cell_value(lines, label, _REV_LABEL.match(label.text).group("inline"), _rev_shaped,
                                 right_pad=6 * label.h)
        if value is None:
            notes.append(f"'{label.text}': {why}")
            continue
        revision, revision_label = value.strip(), label.text
        break''',
'''    if chosen is not None:
        # A REV cell off the number's row (a stacked "ORIGINAL SIZE / REV" cell, M2 review 06 H-04): the REV labels
        # of the title block nearest the number cell, after the ones on its row.
        near = [l for l in lines if _REV_LABEL.match(l.text) and _in_zone(l, width, height) and l not in rev_labels
                and abs(l.cy - chosen.cy) <= 0.25 * height]
        rev_labels = rev_labels + sorted(near, key=lambda l: abs(l.cx - chosen.cx) + abs(l.cy - chosen.cy))
    for label in rev_labels:
        if any(_DESCRIPTION.match(l.text) for l in _row(lines, label)) or _under_reference_heading(lines, label):
            continue
        value, why = _cell_value(lines, label, _REV_LABEL.match(label.text).group("inline"), _rev_shaped,
                                 right_pad=6 * label.h)
        if value is None:
            notes.append(f"'{label.text}': {why}")
            continue
        revision, revision_label = value.strip(), label.text
        break''')
p.write_text(s, encoding="utf-8")
print("ok")
