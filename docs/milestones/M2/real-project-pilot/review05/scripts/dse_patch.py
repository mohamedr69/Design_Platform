import pathlib

p = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app\services\design_sheet_extractor.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('PARSER_VERSION = "2026-09-28.1"   # M2 review 02: band rows, quantity recheck < 90 %, part-number check, heading carry-over',
    'PARSER_VERSION = "2026-09-28.2"   # M2 review 05: correlated part-number agreement is not confirmation; item-number and misassigned columns held\n'
    '# 2026-09-28.1 -- M2 review 02: band rows, quantity recheck < 90 %, part-number check, heading carry-over')

sub('''    agreed = len(others) >= 2 and len(set(_part_key(o) for o in others)) == 1 and whole(others[0])''',
    '''    agreed = len(others) >= 2 and len(set(_part_key(o) for o in others)) == 1 and whole(others[0])
    # The passes read the strip's own pixels again with the same engine, preprocessed two ways: when the
    # strip itself was unsure, their agreeing is the same misreading repeated, not a second witness. On the
    # pilot's frozen sheets, 8 of the 64 strip reads under 90 % that both passes "confirmed" were wrong --
    # KCW019ML-IP65 read KCWO019ML-IP65 at 51 % by the strip and both passes (EP-19977), G1ARN read GIARN,
    # CTR160 read CTRI60 (M2 review 05, R5-04). Agreement stays recorded; it no longer accepts the row.
    correlated = confirmed and line.catalog_confidence is not None and line.catalog_confidence < RECHECK_QUANTITY_BELOW''')

sub('''    else:
        line.catalog_check = {"confirmed": True, "multiline": multiline, "reason": "an independent pass read the same part number"}''',
    '''    elif correlated:
        line.catalog_uncertain = True
        line.catalog_check = {"confirmed": False, "multiline": multiline, "agreement": "correlated",
                              "reason": f"the strip read it at {line.catalog_confidence:.0f}% and the passes that agree read the same "
                                        "pixels with the same engine: repeated, not independent, evidence"}
    else:
        line.catalog_check = {"confirmed": True, "multiline": multiline, "reason": "an independent pass read the same part number"}''')

sub('''        read.extend(page_lines)''', '''        _hold_implausible_columns(page_lines, result.notes)
        read.extend(page_lines)''')

sub('''def settle_identity(read: list[ExtractedBoqLine]) -> list[dict]:''', '''# A run of this many rows whose "quantities" count 1, 2, 3 ... is the item-number column, not quantities.
ITEM_NUMBER_RUN = 5


def _hold_implausible_columns(lines: list[ExtractedBoqLine], notes: list[str]) -> None:
    """Hold rows whose columns do not read as a BOQ's, for the engineer, with the cell and what was read
    (M2 review 05, R5-04). Two checks on what a column holds, never on what a value should be:

    - a quantity column that counts 1, 2, 3 ... down consecutive rows is the item numbers (EP-26369's
      MS FAS BOQ: a merged "1 set" quantity beside items numbered 2-30, read as quantities 2-30);
    - a table whose descriptions are mostly bare numbers has its columns crossed (EP-26082's aspiration
      sheet: part numbers read as quantities, quantities as descriptions).

    Nothing is dropped: each held row's quantity is set aside with the reason, so it becomes a review row
    with its cell (`_dropped_row_issue`)."""
    def hold(line: ExtractedBoqLine, rule: str) -> None:
        line.quantity_parse = {**(line.quantity_parse or {}), "status": values.AMBIGUOUS, "held_quantity": line.quantity, "rule": rule}
        line.quantity = None

    by_table: dict[tuple, list[ExtractedBoqLine]] = {}
    for line in lines:
        by_table.setdefault((line.page, line.table_span), []).append(line)
    for (page, _span), rows in by_table.items():
        rows = sorted(rows, key=lambda l: l.y_px or 0)
        numeric = [l for l in rows if re.fullmatch(r"\\d[\\d.,]*", (l.description or "").strip())]
        if len(rows) >= 3 and len(numeric) >= 0.6 * len(rows):
            for line in rows:
                if line.quantity:
                    hold(line, "the table's description column reads as numbers: its columns do not read as a BOQ's")
            notes.append(f"page {page}: a table of {len(rows)} rows whose descriptions are numbers was held for review")
            continue
        counted = [l for l in rows if l.quantity and l.quantity.isdigit()]
        run: list[ExtractedBoqLine] = []
        for line in counted + [None]:
            if line is not None and run and int(line.quantity) == int(run[-1].quantity) + 1:
                run.append(line)
                continue
            if len(run) >= ITEM_NUMBER_RUN:
                for held in run:
                    hold(held, f"the quantity column counts {run[0].quantity}..{run[-1].quantity} down {len(run)} rows: "
                               "it reads as the item numbers, not quantities")
                notes.append(f"page {page}: {len(run)} rows whose quantities count {run[0].quantity}..{run[-1].quantity} were held for review")
            run = [line] if line is not None else []


def settle_identity(read: list[ExtractedBoqLine]) -> list[dict]:''')

p.write_text(s, encoding="utf-8")
print("ok")
