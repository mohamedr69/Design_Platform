"""Second (and last pre-freeze) candidate patch: T fires only after a COMPLETED-but-unvalidated read or a missing
region -- never after a failed or budget-refused request (a failure is not a weak reading; the accepted failure /
no-loss semantics stay exactly as they are). Found by the existing review 08-10 modules run with T on."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai/backend/app/ai/evidence_reader.py")
raw = P.read_bytes()
s = raw.decode("utf-8").replace("\r\n", "\n")
old = '''        if TARGETED_ENABLED and (disc_value or det_value) and verdict["state"] != "validated" and not verdict.get("guard"):'''
new = '''        if TARGETED_ENABLED and (disc_value or det_value) and verdict["state"] != "validated" and not verdict.get("guard") \\
                and not str(requests.get(key) or "").startswith(("failed", "budget")):'''
assert s.count(old) == 1
s = s.replace(old, new)
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("patched")
