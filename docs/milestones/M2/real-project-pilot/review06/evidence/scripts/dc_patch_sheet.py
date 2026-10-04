import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\document_control.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


sub('''def _sheet_of(page, text: str, number: int, observations: list):
    """The page's title block read by position, for a drawing-sized page with a text layer; its facts kept
    as an observation of the page. A failure here leaves the page to the text reader, noted."""
    from app.services import title_block

    if len(text.strip()) < 80 or not title_block.is_drawing_sheet(page):
        return None
    try:
        with timed("title_block"):
            sheet = title_block.read_page(page, controlled=_controlled_number)''',
'''TITLE_BLOCK_OCR_VARIANT = "tb-ocr-1"


def _title_block_ocr_lines(sha256: str | None, index: int):
    """The OCR fallback for a title block drawn as graphics or scanned: the strip OCRed once, its lines cached by
    content (page-cache variant `TITLE_BLOCK_OCR_VARIANT`)."""
    from app.services import page_cache, title_block

    def ocr_lines(page, clip):
        cached = page_cache.get_ocr(sha256, index, TITLE_BLOCK_OCR_VARIANT) if sha256 else None
        if cached is not None:
            counted("ocr_cache_hits")
            return [title_block.Line(*row) for row in json.loads(cached)]
        counted("title_block_ocr")
        with timed("ocr_engine"):
            lines = title_block.ocr_word_lines(page, clip)
        if sha256:
            page_cache.put_ocr(sha256, index, json.dumps([[l.x0, l.y0, l.x1, l.y1, l.text] for l in lines]), TITLE_BLOCK_OCR_VARIANT)
        return lines

    return ocr_lines


def _sheet_of(page, text: str, number: int, observations: list, *, use_ocr: bool = False, sha256: str | None = None,
              index: int = 0):
    """The page's title block read by position, for a drawing-sized page; its facts kept as an observation of the
    page. Where the text layer gives no own number -- a title block drawn as graphics, or a scanned sheet -- and OCR
    is on, the title-block strip is OCRed once (M2 review 06, H-01). A failure here leaves the page to the text
    reader, noted."""
    from app.services import title_block

    if not title_block.is_drawing_sheet(page) or (len(text.strip()) < 80 and not use_ocr):
        return None
    try:
        with timed("title_block"):
            sheet = title_block.read_page(page, controlled=_controlled_number,
                                          ocr_lines=_title_block_ocr_lines(sha256, index) if use_ocr else None)''')
sub('''                sheet = _sheet_of(page, text, number, observations)''',
    '''                sheet = _sheet_of(page, text, number, observations, use_ocr=use_ocr, sha256=sha256, index=index)''')
if "\nimport json\n" not in s:
    s = s.replace("\nimport re\n", "\nimport json\nimport re\n", 1)
p.write_text(s, encoding="utf-8")
print("ok")
