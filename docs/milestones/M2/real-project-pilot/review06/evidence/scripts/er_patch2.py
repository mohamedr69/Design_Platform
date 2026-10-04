import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
sub('''    state = "validated" if blind and support else "candidate"
    if deterministic and state == "validated" and norm(deterministic) != norm(chosen):
        return {"state": "conflict", "value": chosen, "reasons": [f"the deterministic reader read {deterministic!r}"],
                "support": support}''', '''    if deterministic and norm(deterministic) != norm(chosen):
        return {"state": "conflict", "value": chosen, "reasons": reasons + [f"the deterministic reader read {deterministic!r}"],
                "support": support}
    state = "validated" if blind and support else "candidate"''')
sub('''reading; candidate = read, but without source support or corroboration (model agreement alone is not proof);
    conflict = readings disagree, or a validated reading disagrees with the deterministic value; unreadable = no legible
    reading."""''', '''reading; candidate = read, but without source support or corroboration (model agreement alone is not proof);
    conflict = readings disagree, or the reading disagrees with the deterministic value (neither side is preferred:
    both are kept for review); unreadable = no legible reading."""''')
p.write_text(s, encoding="utf-8")
print("ok")
