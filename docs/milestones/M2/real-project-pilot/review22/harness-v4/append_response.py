"""Append the Review 22 response entry to docs/milestones/M2/M2-REVIEW-RESPONSE.md in binary, after checking the file's
current sha256 (the value recorded when this task started), and verify afterwards that the earlier content is a
byte-identical prefix of the new file. Never rewrites earlier entries. Usage: append_response.py <expected_sha256_before>"""
import hashlib
import pathlib
import sys

DOC = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md")
ENTRY = pathlib.Path("C:/t/iso/work/r2x/review22/pkg-src/RESPONSE-APPEND.md")
before = DOC.read_bytes()
assert hashlib.sha256(before).hexdigest() == sys.argv[1], "the response file changed since the task started; not appending"
entry = ENTRY.read_bytes().replace(b"\r\n", b"\n")
if not before.endswith(b"\n"):
    entry = b"\n" + entry
with open(DOC, "ab") as f:
    f.write(entry)
after = DOC.read_bytes()
assert after[: len(before)] == before and after[len(before):] == entry, "prefix check failed"
print("appended", len(entry), "bytes; before", hashlib.sha256(before).hexdigest(), "after", hashlib.sha256(after).hexdigest())
