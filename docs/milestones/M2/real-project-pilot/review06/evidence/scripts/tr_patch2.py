import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\transmittals.py")
s = p.read_text(encoding="utf-8")
old = '''           "project_id": (re.search(r"EP-\\s?\\d{3,5}", _after(text, r"Project\\s*ID") or "") or re.search(r"$^", "")) and
                         re.search(r"EP-\\s?\\d{3,5}", _after(text, r"Project\\s*ID") or "").group(0),'''
new = '''           "project_id": _project_id(text),'''
assert s.count(old) == 1, "project_id"
s = s.replace(old, new)
s = s.replace('''def observe(text: str, *, source: str, page: int = 1) -> dict:''', '''def _project_id(text: str) -> str | None:
    found = re.search(r"EP-\\s?\\d{3,5}", _after(text, r"Project\\s*ID") or "")
    return found.group(0).replace(" ", "") if found else None


def observe(text: str, *, source: str, page: int = 1) -> dict:''', 1)
p.write_text(s, encoding="utf-8")
print("ok")
