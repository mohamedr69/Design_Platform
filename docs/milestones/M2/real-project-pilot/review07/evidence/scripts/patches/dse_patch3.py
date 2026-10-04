import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\design_sheet_extractor.py")
s = p.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('''PARSER_VERSION = "2026-09-29.1"   # M2 review 06: quantity passes that agree against the strip hold the row (H-06)''',
    '''PARSER_VERSION = "2026-09-29.2"   # M2 review 07: a description's "( n )" count is its own located source fact
# 2026-09-29.1: M2 review 06: quantity passes that agree against the strip hold the row (H-06)''')

sub('''def _is_count(text: str | None) -> bool:''', '''def _inline_count(inline, quantity_text: str | None):
    """A sub-component's count printed in its description ("( 2 ) Dual Input Module") as a source fact of its own
    (M2 review 07): (parsed, quantity, provenance). It stands where the quantity cell is empty or says the same; where
    the cell holds another value, neither is taken -- the row is held with both literals."""
    counted = _parse_quantity(inline.group(1))
    cell = _parse_quantity(quantity_text)
    provenance = {"source": "description_count", "description_literal": inline.group(0).strip(),
                  "cell_literal": quantity_text or None}
    if cell.status != values.EMPTY and cell.text() != counted.text():
        held = {**counted.to_dict(), **provenance, "status": values.AMBIGUOUS,
                "rule": f"the quantity cell read {quantity_text!r} and the description's count read "
                        f"{inline.group(0).strip()!r}: neither is taken"}
        return counted, None, held
    return counted, counted.text(), {**counted.to_dict(), **provenance}


def _is_count(text: str | None) -> bool:''')

sub('''        inline = INLINE_QUANTITY_RE.match(description)
        if inline:
            parsed = _parse_quantity(inline.group(1))
            quantity = parsed.text()
            description = description[inline.end() :].strip()''',
    '''        inline = INLINE_QUANTITY_RE.match(description)
        inline_parse = None
        if inline:
            parsed, quantity, inline_parse = _inline_count(inline, quantity_text)
            description = description[inline.end() :].strip()''')
sub('''                quantity_parse=parsed.to_dict(),
                row_bounds=(row_top, row_bottom),''', '''                quantity_parse=inline_parse or parsed.to_dict(),
                row_bounds=(row_top, row_bottom),''')

sub('''        inline = INLINE_QUANTITY_RE.match(text)
        if inline:
            parsed = _parse_quantity(inline.group(1))
            quantity = parsed.text()
            text = text[inline.end() :].strip()''',
    '''        inline = INLINE_QUANTITY_RE.match(text)
        inline_parse = None
        if inline:
            parsed, quantity, inline_parse = _inline_count(inline, quantity_text)
            text = text[inline.end() :].strip()''')
sub('''                quantity_parse=probe_parse or parsed.to_dict(),''', '''                quantity_parse=probe_parse or inline_parse or parsed.to_dict(),''')
p.write_text(s, encoding="utf-8")
print("ok")
