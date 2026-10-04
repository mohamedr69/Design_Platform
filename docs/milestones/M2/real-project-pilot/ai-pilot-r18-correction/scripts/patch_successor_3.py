"""Successor patch 3 (before freeze), from the OFFLINE locator evaluation (locator/LOCATOR-EVAL.before-patch3.json):
  * the label box is built only when a NUMBER label (title_block._NUMBER_LABEL) is found; revision labels alone
    (AR-101 'Sheet Identification:', EML-09 'Sheet No.' are not number labels) give the application's strip instead;
  * a scan (no text layer, no cached OCR) whose orientation strip shows no number label also OCRs the other side of the
    application's title-block zone (right edge / bottom edge: title_block._in_zone), within the same OCR time bound;
    the strip that shows a number label wins, else the one with the most OCR'd text (never the full sheet).
Generic geometry rules only: no values, file names or projects."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai2/backend/app/ai/evidence_reader.py")
s = P.read_bytes().decode("utf-8").replace("\r\n", "\n")
old = s[s.index("def locate_title_block("):s.index("def _norm_to_page(")]
new = '''def locate_title_block(page, ocr_lines: list | None = None, *, ocr_timeout: float = 20.0) -> tuple:
    """(display rect, route) of a drawing sheet's title-block area; (None, 'not_a_drawing_sheet') otherwise."""
    import time as _time

    import pymupdf

    from app.services import title_block as tb

    if not tb.is_drawing_sheet(page):
        return None, "not_a_drawing_sheet"
    w, h = page.rect.width, page.rect.height
    strip = tb.title_block_strip(page)
    lines, source = tb.page_lines(page), "text"
    if len(lines) < 5 and ocr_lines:
        lines, source = [tb.Line(*l[:5]) for l in ocr_lines if len(l) >= 5], "ocr_cached"
    if len(lines) < 5 and ocr_timeout > 0:
        # a scan: OCR the application's strip; if it shows no number label, the other side of the title-block zone
        # (right edge <-> bottom edge) too -- all within the same time bound; never the full sheet
        other = pymupdf.Rect(0, h * 0.78, w, h) if w >= h else pymupdf.Rect(w * 0.72, 0, w, h)
        lines, source, deadline, by_strip = [], "ocr_local", _time.monotonic() + ocr_timeout, []
        for rect in (strip, other):
            left = deadline - _time.monotonic()
            if left <= 1:
                break
            try:
                from functools import partial

                from app.services.document_control import _tesseract
                got = tb.ocr_word_lines(page, rect, dpi=150, image_to_data=partial(_tesseract().image_to_data, timeout=left))
            except Exception:  # noqa: BLE001 -- no OCR: the strip, never the full sheet
                got = []
            by_strip.append((rect, got))
            lines += got
            if any(tb._NUMBER_LABEL.match(l.text) for l in got):
                break
        if by_strip and not any(tb._NUMBER_LABEL.match(l.text) for l in lines):
            strip = max(by_strip, key=lambda x: sum(len(l.text) for l in x[1]))[0]
    numbers = [l for l in lines if tb._in_zone(l, w, h) and tb._NUMBER_LABEL.match(l.text)]
    revisions = [l for l in lines if tb._in_zone(l, w, h) and tb._REV_LABEL.match(l.text)]
    for group in (numbers + revisions, numbers):
        if not numbers:
            break
        x0, y0 = min(l.x0 for l in group) - 0.12 * w, min(l.y0 for l in group) - 0.12 * h
        x1, y1 = max(l.x1 for l in group) + 0.12 * w, max(l.y1 for l in group) + 0.12 * h
        rect = pymupdf.Rect(max(0, x0), max(0, y0), min(w, x1), min(h, y1))
        if rect.width * rect.height <= 0.45 * w * h:
            return rect, f"located:labels:{source}"
    return strip, f"located:strip:{source if lines else 'none'}"


'''
s = s.replace(old, new)
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("patched 3")
