import pathlib
p = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app\services\title_block.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:80]
    s = s.replace(old, new)
sub('_DATE_LABEL = re.compile(r"^DATE\s*:?$", re.I)\n',
    '_DATE_LABEL = re.compile(r"^DATE\s*:?$", re.I)\n_TITLE_LABEL = re.compile(r"^(?:DRAWING\s+|DWG\.?\s+|SHEET\s+)?TITLE\s*:?$", re.I)\n')
sub('    conflict: bool = False                     # the REV cell and the history\'s latest row disagree\n',
    '    conflict: bool = False                     # the REV cell and the history\'s latest row disagree\n'
    '    title: str | None = None                   # the Drawing Title cell\'s lines, as printed\n')
sub('"references": list(self.references), "conflict": self.conflict, "notes": list(self.notes)}',
    '"references": list(self.references), "conflict": self.conflict, "title": self.title, "notes": list(self.notes)}')
sub('''    deeper = [l for l in _below(lines, label, _column(lines, label, right_pad=right_pad), 9 * label.h)
              if l is not value and shaped(l.text)]''',
    '''    span = _column(lines, label, right_pad=right_pad)
    # The column ends where the next cell starts: a label under this one (a second numbering scheme's
    # "MUNICIPALITY DRAWING No." under "CLIENT DRAWING No.") opens a cell of its own, not a table row.
    stop = min((l.y0 for l in lines if l is not label and l.y0 > label.y1 and span[0] <= l.cx < span[1]
                and (_is_label(l) or _TITLE_LABEL.match(l.text))), default=float("inf"))
    deeper = [l for l in _below(lines, label, span, 9 * label.h) if l is not value and shaped(l.text) and l.y0 < stop]''')
sub('''    history, latest = _history(lines)
    conflict = bool(revision and latest and revision_key(revision) != revision_key(latest))
    return TitleBlock(number, revision, number_label, revision_label, history, latest, _references(lines), conflict,
                      tuple(notes))''',
    '''    history, latest = _history(lines)
    conflict = bool(revision and latest and revision_key(revision) != revision_key(latest))
    return TitleBlock(number, revision, number_label, revision_label, history, latest, _references(lines), conflict,
                      tuple(notes), _title(lines, width, height, chosen))


def _title(lines: list[Line], width: float, height: float, near: Line | None) -> str | None:
    """The Drawing Title cell: the lines under its label, one after another, until the next label or a gap
    wider than a line -- the cell nearest the number cell (or the corner). A reference table's DRAWING TITLE
    column is not it."""
    labels = [l for l in lines if _TITLE_LABEL.match(l.text) and _in_zone(l, width, height) and not _under_reference_heading(lines, l)]
    if near is not None:
        labels.sort(key=lambda l: abs(l.cx - near.cx) + abs(l.cy - near.cy))
    else:
        labels.sort(key=lambda l: -_corner_rank(l, width, height))
    for label in labels:
        left, right = _column(lines, label, right_pad=40 * label.h)
        column = sorted((l for l in lines if l is not label and l.y0 > label.y0 + 0.5 * label.h and l.y0 <= label.y1 + 30 * label.h
                         and left <= l.cx < right), key=lambda l: (round(l.y0), l.x0))
        out, previous = [], label
        for line in column:
            limit = 4 * label.h if previous is label else 1.2 * max(previous.h, line.h)
            if line.y0 - previous.y1 > limit or _is_label(line) or _TITLE_LABEL.match(line.text) or _DATE_LABEL.match(line.text):
                break
            out.append(line.text)
            previous = line if line.y1 > previous.y1 else previous
            if len(out) == 4:
                break
        if out:
            return " ".join(" ".join(out).split())
    return None''')
p.write_text(s, encoding="utf-8"); print("ok")
