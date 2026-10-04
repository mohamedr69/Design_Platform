import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/services/design_sheet_extractor.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
sub('''    confidence = f" ({line.quantity_confidence:.0f}%)" if line.quantity_confidence is not None else ""
    _cut_digit(line, strip_value, others, confidence)
''', '''    confidence = f" ({line.quantity_confidence:.0f}%)" if line.quantity_confidence is not None else ""
    if _cut_digit(line, strip_value, others, confidence):
        return
    # Independent passes that agree with each other against the strip, none backing it, are not "the cell pass
    # being the worse reader" (M2 review 06, H-06: EP-8430 "PC+Monitor", printed 2, the strip read "| 9" at 74 %,
    # all three passes read 2 and the 9 was accepted). Neither value is taken: the row goes for review with both.
    agreed = [v for v, n in others.items() if n >= 2]
    if HOLD_ON_PASS_DISAGREEMENT and agreed and strip_value not in valid:
        line.quantity = None
        line.quantity_parse = {**(line.quantity_parse or {}), "status": values.AMBIGUOUS,
                               "rule": f"the column read {strip_value!r}{confidence} but {others[agreed[0]]} independent passes "
                                       f"read {agreed[0]!r} and none read the column's value"}
''')
sub('''CONFIRM_CATALOG_BELOW = RECHECK_QUANTITY_BELOW
''', '''CONFIRM_CATALOG_BELOW = RECHECK_QUANTITY_BELOW
# A confident-enough strip quantity (60-90 %) contradicted by two or more agreeing independent passes, none backing
# it, is held for review rather than accepted (M2 review 06, H-06).
HOLD_ON_PASS_DISAGREEMENT = True
''')
p.write_text(s, encoding="utf-8")
print("ok")
