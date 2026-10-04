import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\title_block.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)


sub('''    source: str = "text"                       # "text" (the page's text layer) or "ocr" (the title-block strip OCRed)''',
    '''    source: str = "text"                       # "text" (the page's text layer) or "ocr" (the title-block strip OCRed)
    number_region: tuple | None = None         # the number cell's label, display coordinates (x0, y0, x1, y1)
    revision_region: tuple | None = None       # the REV cell's label''')
sub('''"references": list(self.references), "conflict": self.conflict, "title": self.title, "notes": list(self.notes),
                "source": self.source}''',
    '''"references": list(self.references), "conflict": self.conflict, "title": self.title, "notes": list(self.notes),
                "source": self.source, "number_region": list(self.number_region) if self.number_region else None,
                "revision_region": list(self.revision_region) if self.revision_region else None}''')
sub('''        revision, revision_label = value.strip(), label.text
        break''', '''        revision, revision_label = value.strip(), label.text
        revision_box = (round(label.x0, 1), round(label.y0, 1), round(label.x1, 1), round(label.y1, 1))
        break''')
sub('''    revision = revision_label = None''', '''    revision = revision_label = None
    revision_box = None''')
sub('''    return TitleBlock(number, revision, number_label, revision_label, history, latest, _references(lines), conflict,
                      title=_title(lines, width, height, chosen), notes=tuple(notes))''',
    '''    number_box = (round(chosen.x0, 1), round(chosen.y0, 1), round(chosen.x1, 1), round(chosen.y1, 1)) if chosen is not None else None
    return TitleBlock(number, revision, number_label, revision_label, history, latest, _references(lines), conflict,
                      title=_title(lines, width, height, chosen), notes=tuple(notes), number_region=number_box,
                      revision_region=revision_box)''')
p.write_text(s, encoding="utf-8")
print("ok")
