import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\title_block.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)


sub('''    title: str | None = None                   # the Drawing Title cell's lines, as printed
    notes: tuple = field(default=())
''', '''    title: str | None = None                   # the Drawing Title cell's lines, as printed
    notes: tuple = field(default=())
    # An OCR-read number cell (source "ocr"): the text exactly as OCR gave it, and the one identity-shaped token
    # taken from it when there is exactly one, clean (M2 review 06). `number` is that token only when it is not
    # glyph-ambiguous; otherwise `number` stays None and the literal / candidate are evidence, never a register key.
    number_literal: str | None = None
    number_candidate: str | None = None
''')
sub('''                "source": self.source, "number_region": list(self.number_region) if self.number_region else None,''',
    '''                "source": self.source, "number_literal": self.number_literal, "number_candidate": self.number_candidate,
                "number_region": list(self.number_region) if self.number_region else None,''')
sub('''            if ocr_block is not None and (ocr_block.number or (block is None and ocr_block.revision)):
                import dataclasses

                return dataclasses.replace(ocr_block, source="ocr",
                                           notes=tuple(block.notes if block else ()) + ("title block read by OCR of its strip",) + ocr_block.notes)''',
    '''            if ocr_block is not None and (ocr_block.number or (block is None and ocr_block.revision)):
                import dataclasses

                literal = ocr_block.number
                candidate, why = ocr_number(literal)
                trusted = candidate if candidate and why is None else None
                notes = tuple(block.notes if block else ()) + ("title block read by OCR of its strip",) + ocr_block.notes
                if literal and trusted is None:
                    notes += (f"OCR number {literal!r} not taken: {why}",)
                return dataclasses.replace(ocr_block, source="ocr", number=trusted, number_literal=literal,
                                           number_candidate=candidate, notes=notes)''')
sub('''def title_block_strip(page):''', '''_OCR_TOKEN = re.compile(r"^[A-Z0-9][A-Z0-9&./_-]*[A-Z0-9]$")
_AMBIGUOUS_GLYPH = re.compile(r"(?<=\\d)[OIL]|[OIL](?=\\d)")


def ocr_number(literal: str | None) -> tuple[str | None, str | None]:
    """(candidate, reason it is not trusted) for an OCR-read own number. The candidate is the one token of the
    literal that is identity-shaped (letters / digits with separators, a digit, at least 6 characters); a literal
    with none or several has no candidate. A candidate with O / I / L against a digit ("LO8") is glyph-ambiguous:
    OCR confuses those with 0 / 1, and the page cannot say which was printed (EP-29076 LAC-653 sheets)."""
    if not literal:
        return None, "nothing read"
    tokens = [t.strip(".,;:|") for t in literal.split()]
    shaped = [t for t in tokens if len(t) >= 6 and re.search(r"\\d", t) and re.search(r"[-/._]", t) and _OCR_TOKEN.match(t.upper())]
    if len(shaped) != 1:
        return None, "no single identity-shaped token" if not shaped else "several identity-shaped tokens"
    candidate = shaped[0]
    extra = [t for t in tokens if t and t != candidate]
    if extra:
        return candidate, "other text beside the number: " + " ".join(extra)
    if _AMBIGUOUS_GLYPH.search(candidate.upper()):
        return candidate, "a letter O / I / L against a digit: OCR cannot tell it from 0 / 1"
    return candidate, None


def title_block_strip(page):''')
sub('TITLE_BLOCK_VERSION = "titleblock-2"', 'TITLE_BLOCK_VERSION = "titleblock-3"   # .3: an OCR number is a register key only when clean and unambiguous')
p.write_text(s, encoding="utf-8")
print("ok")
