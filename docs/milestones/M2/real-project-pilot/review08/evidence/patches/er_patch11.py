"""M2 review 08: legacy attempts -- discovery-only candidates never supersede; review 07 attempts keep their context key."""
import pathlib

p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
b = p.read_bytes()
assert b.count(b"\r\n") > 0
s = b.decode("utf-8").replace("\r\n", "\n")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('''        if not outcomes and entry.get("outcome") in ("evidence", "no_components"):
            # an attempt that recorded no field outcomes (before review 08): only what it produced counts as read
            outcomes = {fk: COMPLETED for (pp, fk) in by_field if pp == pno}''',
    '''        if not outcomes and entry.get("outcome") in ("evidence", "no_components"):
            # an attempt that recorded no field outcomes (before review 08): a produced field counts as read only when
            # it carries a verified reading -- a field made only of unverified candidates (e.g. discovery-only, its
            # blind read lost) is incomplete and supersedes nothing
            outcomes = {fk: (COMPLETED if any(o.get("state") != "candidate" for o in obs) else "incomplete:legacy_unverified")
                        for (pp, fk), obs in by_field.items() if pp == pno}''')
sub('''        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": envelopes, "last_written_key": previous.get("current_key"),
                "attempts": list(previous.get("attempts") or []), "superseded": list(previous.get("superseded") or [])}''',
    '''        attempts = [a if a.get("key") else {**a, "key": envelope_key(a.get("profile"), a.get("variant"))}
                    for a in previous.get("attempts") or []]
        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": envelopes, "last_written_key": previous.get("current_key"),
                "attempts": attempts, "superseded": list(previous.get("superseded") or [])}''')
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
