import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\ai\evidence_reader.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)


sub('''"read_boq_row": "read-boq-row-2026-09-29.1"}''', '''"read_boq_row": "read-boq-row-2026-09-29.2"}''')
sub('''    "read_boq_row": ("This image is one row of a bill-of-quantities / design-sheet table. Read the catalogue / part "
                     "number and the quantity exactly as printed in this row (not the row's item number), and a short "
                     "description. If the row is a heading or note with no quantity, say so. Empty strings where absent."),''',
    '''    # .2 (M2 review 06): the quantity is read from its own cell image -- the reader's column geometry says which cell
    # it is -- instead of asking the model to tell a quantity from an item number (.1 discarded a leading quantity
    # column as an "item number" on the EP-30088 / EP-30784 layout).
    "read_boq_row": ("Two images of one row of a bill-of-quantities / design-sheet table. 'quantity_cell' is the row's "
                     "quantity cell: read the number printed in it exactly (an empty string if the cell is empty). 'row' "
                     "is the whole row: read the catalogue / part number exactly as printed, keeping every character "
                     "(letters, digits, + / . - ( ) and spaces between parts), and a short description. If the row is a "
                     "heading or a note with no quantity, say so. Empty strings where absent."),''')
sub('''def validate_boq_row(row: dict, blind: dict | None) -> dict:''', '''def part_literal(text: str | None) -> str:
    """A part number compared as printed: upper case, whitespace ignored, every other character significant --
    "PT-1S" is not "PT-1S+" (`norm`, which drops punctuation, made them equal in .1)."""
    return re.sub(r"\\s+", "", str(text or "").upper())


def validate_boq_row(row: dict, blind: dict | None) -> dict:''')
sub('''    part_ok = norm(row.get("part_number")) == norm(blind.get("part_number")) or (not row.get("part_number") and not blind.get("part_number"))''',
    '''    part_ok = part_literal(row.get("part_number")) == part_literal(blind.get("part_number")) or (not row.get("part_number") and not blind.get("part_number"))''')
sub('''    spans = {}
    for l in lines:
        if l.get("table_span"):
            spans.setdefault(int(l.get("page") or 1), l["table_span"])''', '''    spans, qspans = {}, {}
    for l in lines:
        if l.get("table_span"):
            spans.setdefault(int(l.get("page") or 1), l["table_span"])
        if l.get("quantity_span"):
            qspans.setdefault(int(l.get("page") or 1), l["quantity_span"])''')
sub('''                     "table_span": spans.get(page) or [region[0], region[2]], "_accepted": False, "_target": issue.get("target")})''',
    '''                     "table_span": spans.get(page) or [region[0], region[2]], "quantity_span": qspans.get(page),
                     "_accepted": False, "_target": issue.get("target")})''')
sub('''        clip = pymupdf.Rect(span[0] * scale, (bounds[0] - 6) * scale, span[1] * scale, (bounds[1] + 6) * scale) & page.rect
        png = page.get_pixmap(matrix=pymupdf.Matrix(CROP_DPI / 72, CROP_DPI / 72), clip=clip).tobytes("png")
        blind = run.call(sha256=sha256, task="read_boq_row", page=page_no, reason=reason,
                         parts=[TextPart("task", READ_TEXTS["read_boq_row"]), ImagePart("row", png)], schema=BOQ_ROW_SCHEMA, max_output=300)''',
    '''        clip = pymupdf.Rect(span[0] * scale, (bounds[0] - 6) * scale, span[1] * scale, (bounds[1] + 6) * scale) & page.rect
        png = page.get_pixmap(matrix=pymupdf.Matrix(CROP_DPI / 72, CROP_DPI / 72), clip=clip).tobytes("png")
        qspan = row.get("quantity_span") or qspans.get(page_no)
        if not qspan:
            results.append({"page": page_no, "reason": reason, "row": _brief(row), "accepted_by_reader": row["_accepted"], "state": "no_geometry"})
            continue
        qclip = pymupdf.Rect(qspan[0] * scale, (bounds[0] - 6) * scale, qspan[1] * scale, (bounds[1] + 6) * scale) & page.rect
        qpng = page.get_pixmap(matrix=pymupdf.Matrix(CROP_DPI / 72, CROP_DPI / 72), clip=qclip).tobytes("png")
        blind = run.call(sha256=sha256, task="read_boq_row", page=page_no, reason=reason,
                         parts=[TextPart("task", READ_TEXTS["read_boq_row"]), ImagePart("quantity_cell", qpng), ImagePart("row", png)],
                         schema=BOQ_ROW_SCHEMA, max_output=300)''')
p.write_text(s, encoding="utf-8")
print("ok")
