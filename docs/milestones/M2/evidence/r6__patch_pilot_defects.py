"""Pilot defects P-01..P-04 (demonstrated on the regression/exploration cohorts): bounded reader fixes.
P-01 a field label glued to the number by OCR ("Reference25H-S202-...") became the reference (EP-29076 LACASA forms).
P-02 an empty "Drawing No:" field captured the next label ("Reference") as the drawing number (EP-19977 Emaar forms).
P-03 an OCR letter O in a revision suffix ("-RO") left the suffix unread and glued to the reference (EP-29076 scans).
P-04 the "-MAT-" material-submittal code (Emaar/Voltas, EFECO numbering) was not a reference code; a code may follow a
     wrapped hyphen ("...-VL-\\nMAT-ELV-0003"). Parser version bumped: readings by .4 and .5 are distinct identities."""
import pathlib, re, sys

B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend"); p = B / "app" / "services" / "document_control.py"
s = p.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, old[:80]
    s = s.replace(old, new, count)


rep('PARSER_VERSION = "parse-2026-09-28.4"', 'PARSER_VERSION = "parse-2026-09-28.5"')
rep('_CODES = r"(MAS|MAR|SDW|DWG|SD|SAR)"',
    '# MAT: a material submittal in Emaar / Voltas and EFECO numbering ("EBF-DCP-6374-VL-MAT-ELV-0003", "A23-EFE-MAT-E-00033";\n'
    '# real-project pilot, 2026-09-28).\n_CODES = r"(MAS|MAR|MAT|SDW|DWG|SD|SAR)"')
rep('REF = re.compile(r"\\b[A-Z0-9]+" + _SEGMENT + r"*-" + _CODES + r"-[A-Z0-9]+" + _SEGMENT + r"*-?" + _SHEETS, re.I)',
    '# The code itself may follow a wrapped hyphen ("EBF-DCP-6374-VL-" / "MAT-ELV-0003"), like any segment.\n'
    'REF = re.compile(r"\\b[A-Z0-9]+" + _SEGMENT + r"*-\\n?" + _CODES + r"-[A-Z0-9]+" + _SEGMENT + r"*-?" + _SHEETS, re.I)')
rep('_CATEGORY_OF_CODE = {"MAS": "submittals", "MAR": "submittals", "SAR": "samples", "SDW": "drawings", "DWG": "drawings",\n                     "SD": "drawings"}',
    '_CATEGORY_OF_CODE = {"MAS": "submittals", "MAR": "submittals", "MAT": "submittals", "SAR": "samples", "SDW": "drawings",\n                     "DWG": "drawings", "SD": "drawings"}')
rep('''    out = []
    for match in REF.finditer(text):
        raw = match.group()
        reference = raw.replace("-\\n", "-").rstrip("-.")
        if is_date_shaped(reference):
            continue
''', '''    out = []
    for match in REF.finditer(text):
        raw = match.group()
        start = match.start()
        # OCR of a form glues the field's label to its value ("Reference25H-S202-…",
        # "No.R1029-…"): the label is not part of the number (pilot P-01).
        glued = _GLUED_LABEL.match(raw)
        if glued:
            raw = raw[glued.end():]
            start += glued.end()
        reference = raw.replace("-\\n", "-").rstrip("-.")
        # OCR reads the zero of a revision suffix as the letter O ("-RO", "-R0O"):
        # the suffix is a revision, not part of the number (pilot P-03).
        reference = _OCR_REVISION_SUFFIX.sub(lambda m: "-R" + m.group(1).upper().replace("O", "0"), reference)
        if is_date_shaped(reference):
            continue
''')
rep('''        out.append(ReferenceCandidate(reference, match.group(1).upper(), match.start(), match.end(), kind,
                                      incomplete=raw.rstrip(".").endswith("-")))
    return out
''', '''        out.append(ReferenceCandidate(reference, match.group(1).upper(), start, match.end(), kind,
                                      incomplete=raw.rstrip(".").endswith("-")))
    return out


_GLUED_LABEL = re.compile(r"^(?:Reference|Ref\\.?|No\\.?)(?=[A-Z0-9]*\\d)", re.I)
_OCR_REVISION_SUFFIX = re.compile(r"-R([O0]{1,2}\\d{0,2}|\\d{0,2}[O0]{1,2})$", re.I)
# A drawing-number field's value is a number, never the next field's label:
# an empty "Drawing No:" in front of "Reference No: …" read "Reference" as
# the number (pilot P-02).
_FIELD_LABEL = re.compile(r"^(?:Reference|Ref|Rev|Revision|Date|Title|Sheet|Scale|No|Number|Drawn|Checked|Approved)\\b\\.?\\s*(?:No\\.?)?\\s*:?$", re.I)


def drawing_number(text: str):
    """The first drawing-number field whose value holds a digit and is not a
    field label, as a match (group 1 is the number); None for none."""
    for match in DRAW_REF.finditer(text):
        value = match.group(1).strip()
        if re.search(r"\\d", value) and not _FIELD_LABEL.match(value):
            return match
    return None
''')
rep('    drawing_match = DRAW_REF.search(text)\n', '    drawing_match = drawing_number(text)\n')
p.write_text(s, encoding="utf-8")
print("document_control patched; version", re.search(r'PARSER_VERSION = "([^"]+)"', s).group(1))
