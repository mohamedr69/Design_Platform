import pathlib
p = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app\services\design_sheet_extractor.py")
s = p.read_text(encoding="utf-8")
start = s.index("def _hold_implausible_columns(")
end = s.index("def settle_identity(")
new = '''def _hold_implausible_columns(lines: list[ExtractedBoqLine], notes: list[str]) -> None:
    """Hold rows whose columns do not read as a BOQ's, for the engineer, with the cell and what was read
    (M2 review 05, R5-04). Two checks on what a column holds, never on what a value should be:

    - a quantity column that counts 1, 2, 3 ... down consecutive rows is the item numbers (EP-26369's
      MS FAS BOQ, laid out Item | Model | Description | Quantity: items 1-13 read as quantities 1-13).
      Once a run shows it, every row the same column layout gives is held, on every page: the column
      is the item column throughout, whatever the shorter sections happen to count;
    - a table whose descriptions are mostly bare numbers has its columns crossed (EP-26082's aspiration
      sheet: part numbers read as quantities, quantities as descriptions).

    Nothing is dropped: each held row's quantity is set aside with the reason, so it becomes a review row
    with its cell (`_dropped_row_issue`). Runs over the whole sheet, after every page is read."""
    def hold(line: ExtractedBoqLine, rule: str) -> None:
        line.quantity_parse = {**(line.quantity_parse or {}), "status": values.AMBIGUOUS, "held_quantity": line.quantity, "rule": rule}
        line.quantity = None

    def counted(line: ExtractedBoqLine) -> str | None:
        value = line.quantity or line.raw_quantity
        value = (value or "").strip()
        return value if value.isdigit() else None

    by_table: dict[tuple, list[ExtractedBoqLine]] = {}
    for line in lines:
        by_table.setdefault((line.page, line.table_span), []).append(line)
    item_columns: dict[tuple | None, str] = {}
    for (page, span), rows in by_table.items():
        rows = sorted(rows, key=lambda l: l.y_px or 0)
        numeric = [l for l in rows if re.fullmatch(r"\d[\d.,]*", (l.description or "").strip())]
        if len(rows) >= 3 and len(numeric) >= 0.6 * len(rows):
            for line in rows:
                if line.quantity:
                    hold(line, "the table's description column reads as numbers: its columns do not read as a BOQ's")
            notes.append(f"page {page}: a table of {len(rows)} rows whose descriptions are numbers was held for review")
            continue
        run: list[ExtractedBoqLine] = []
        for line in [l for l in rows if counted(l)] + [None]:
            if line is not None and run and int(counted(line)) == int(counted(run[-1])) + 1:
                run.append(line)
                continue
            if len(run) >= ITEM_NUMBER_RUN and span not in item_columns:
                item_columns[span] = f"page {page}: the quantity column counts {counted(run[0])}..{counted(run[-1])} down {len(run)} rows"
            run = [line] if line is not None else []
    for span, why in item_columns.items():
        held = [l for l in lines if l.table_span == span and l.quantity]
        for line in held:
            hold(line, f"{why}: it reads as the item numbers, not quantities, wherever this column layout is read")
        notes.append(f"{why}; {len(held)} rows read in that column layout were held for review")


'''
s = s[:start] + new + s[end:]
s = s.replace("        _hold_implausible_columns(page_lines, result.notes)\n        read.extend(page_lines)", "        read.extend(page_lines)")
old = "    result.buildings = settle_identity(read)"
assert s.count(old) == 1
s = s.replace(old, "    _hold_implausible_columns(read, result.notes)\n    result.buildings = settle_identity(read)")
p.write_text(s, encoding="utf-8"); print("ok")
