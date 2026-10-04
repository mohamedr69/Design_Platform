import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\document_control.py")
s = p.read_text(encoding="utf-8")
old = '''        if not re.search(required, text, re.I) and not re.search(r"consultant.*(?:reply|comment|status)|review\\s*status", text, re.I): return []'''
new = '''        # A sheet whose title block gave its own number is a drawing sheet by that evidence: the text layer may carry
        # no "drawing title" words at all (a title block drawn as graphics and read by OCR, M2 review 06 H-01).
        if not own and not re.search(required, text, re.I) and not re.search(r"consultant.*(?:reply|comment|status)|review\\s*status", text, re.I): return []'''
assert s.count(old) == 1, "gate"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok")
