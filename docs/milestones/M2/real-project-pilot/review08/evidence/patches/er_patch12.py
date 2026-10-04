import pathlib

p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_bytes().decode("utf-8").replace("\r\n", "\n")
old = '''    if env is None:
        return {"state": "unavailable", "reason": f"no evidence was read for {key}", "context": context, "history": history}'''
new = '''    if env is None:
        attempted = any(a.get("key") == key for a in ai["attempts"])
        return {"state": "pending" if attempted else "unavailable",
                "reason": f"reading was attempted for {key} and gave no evidence yet" if attempted else f"no evidence was read for {key}",
                "context": context, "history": history}'''
assert s.count(old) == 1
p.write_bytes(s.replace(old, new).replace("\n", "\r\n").encode("utf-8"))
print("ok")
