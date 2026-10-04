import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\transmittals.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)


sub('''def _after(text: str, label: str) -> str | None:
    found = re.search(r"(?im)(?:^|\\|)\\s*" + label + _LABEL_VALUE, text)
    if not found:
        return None
    value = " ".join(found.group(1).split()).strip(" :|_.")
    return value or None''',
'''_NEXT_LABEL = re.compile(r"\\s(?:Date|AASS\\s*Ref|Tel|Attn|Project\\s*ID|Subject|Fax)\\b.*$", re.I)


def _after(text: str, label: str) -> str | None:
    found = re.search(r"(?im)(?:^|\\|)\\s*" + label + _LABEL_VALUE, text)
    if not found:
        return None
    value = _NEXT_LABEL.sub("", " ".join(found.group(1).split())).strip(" :|_.")
    return value or None


_ITEM_INLINE = re.compile(r"\\|\\s*(\\d{1,3})\\s*\\|\\s*([A-Z0-9][A-Z0-9/&._ -]{3,70}?)\\s*\\|\\s*([^|]{3,160}?)\\s*\\|", re.I)


def _document_no_shaped(value: str) -> bool:
    return bool(re.search(r"\\d", value)) and bool(re.search(r"[A-Z]", value, re.I)) and bool(re.search(r"[/-]", value)) \\
        and not re.match(r"(?:document|item|description)", value, re.I)''')
sub('''    items = []
    for line in text.splitlines():
        m = _ITEM_CELLS.match(line.strip()) or _ITEM_OCR.match(line.strip())
        if m and re.search(r"\\d", m.group(2)) and not re.match(r"(?:document|item)", m.group(2), re.I):
            items.append({"item": m.group(1), "document_no": " ".join(m.group(2).split()), "description": " ".join(m.group(3).split())[:160]})''',
'''    items = []
    for line in text.splitlines():
        found = [m for m in [_ITEM_CELLS.match(line.strip()) or _ITEM_OCR.match(line.strip())] if m] or list(_ITEM_INLINE.finditer(line))
        for m in found:
            if _document_no_shaped(m.group(2)):
                item = {"item": m.group(1), "document_no": " ".join(m.group(2).split()), "description": " ".join(m.group(3).split())[:160]}
                if item not in items:
                    items.append(item)''')
p.write_text(s, encoding="utf-8")
print("ok")
