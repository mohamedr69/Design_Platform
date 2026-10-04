import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\labelled_fields.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)


sub('''def _identity_shaped(text: str) -> bool:
    text = text.strip()
    return len(text) >= 4 and bool(re.search(r"\\d", text)) and not _DATE_VALUE.match(text) and len(text) <= 60''',
    '''def _identity_shaped(text: str) -> bool:
    """An identifier as printed: a digit, no lower-case words, and either a separator ("/", "-", ".", "_") or at most
    four upper-case tokens ("MTS E 0018"). Not a date, not a sentence."""
    text = text.strip()
    if not (4 <= len(text) <= 60) or not re.search(r"\\d", text) or _DATE_VALUE.match(text):
        return False
    if re.search(r"[a-z]{2,}", text):
        return False
    tokens = text.split()
    return bool(re.search(r"[/._-]", text)) or (len(tokens) <= 4 and all(re.fullmatch(r"[A-Z0-9&]+", t) for t in tokens))''')
sub('''    r"(?P<label>(?:Review|Submitted|Full\\s+Document|AASS|Our)?\\s*(?:Document|Doc|Reference|Ref|Submittal|Transmittal)\\.?\\s*(?:No\\.?|Number)?)"''',
    '''    r"(?P<label>\\b(?:Review|Submitted|Full\\s+Document|AASS|Our)?\\s*(?:Document|Doc|Reference|Ref|Submittal|Transmittal)\\b\\.?\\s*(?:No\\b\\.?|Number)?)"''')
p.write_text(s, encoding="utf-8")
print("ok")
