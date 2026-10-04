import pathlib
p = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app\services\document_control.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:80]
    s = s.replace(old, new)
sub('''# real-project pilot, 2026-09-28).
_CODES = r"(MAS|MAR|MAT|SDW|DWG|SD|SAR)"''', '''# real-project pilot, 2026-09-28).
# MTG: a material sample tag in CSCEC numbering ("R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020"), a sample; the tag form
# also prints the material submittal it belongs to ("…-MAR-…-1009"), which is not the tag (M2 review 05).
_CODES = r"(MAS|MAR|MAT|MTG|SDW|DWG|SD|SAR)"''')
sub('''_CATEGORY_OF_CODE = {"MAS": "submittals", "MAR": "submittals", "MAT": "submittals", "SAR": "samples", "SDW": "drawings",''',
    '''_CATEGORY_OF_CODE = {"MAS": "submittals", "MAR": "submittals", "MAT": "submittals", "SAR": "samples", "MTG": "samples", "SDW": "drawings",''')
sub('''else r"sample\s+approval|SAR\s+Reference" if category == "samples"''',
    '''else r"sample\s+(?:approval|tag)|SAR\s+Reference" if category == "samples"''')
p.write_text(s, encoding="utf-8"); print("ok")
