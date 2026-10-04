import pathlib

p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_bytes().decode("utf-8").replace("\r\n", "\n")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('''    if not pages:
        attempted = any(a.get("key") == key for a in ai["attempts"])
        return {"state": "pending" if attempted and not (policies and env.get("pages")) else "unavailable",
                "reason": ("reading was attempted for this context; no evidence yet" if attempted else "no evidence under a compatible policy"),
                "context": context, "history": history}''',
    '''    if not pages:
        # an envelope exists only because an attempt for this context was merged into it
        incompatible = bool(policies and env.get("pages"))
        return {"state": "unavailable" if incompatible else "pending",
                "reason": "no evidence under a compatible policy" if incompatible else "reading was attempted for this context; no evidence yet",
                "context": context, "history": history}''')
sub('''        attempts = [a if a.get("key") else {**a, "key": envelope_key(a.get("profile"), a.get("variant"))}
                    for a in previous.get("attempts") or []]''',
    '''        attempts = [{**a, "key": envelope_key(a.get("profile"), a.get("variant"))} if not a.get("key") and (a.get("profile") or a.get("variant")) else a
                    for a in previous.get("attempts") or []]''')
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
