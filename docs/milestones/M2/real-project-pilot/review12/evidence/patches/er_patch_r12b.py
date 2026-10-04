"""Review 12: the reconstruction's entry summary must not shadow the BOQ verifier's `_brief(row)` -- renamed."""
import pathlib
import re

p = pathlib.Path("C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_bytes().decode("utf-8").replace("\r\n", "\n")
i = s.index("def _brief(entry: dict | None) -> dict | None:")
head, tail = s[:i], s[i:]
end = tail.index("def _later(")
block = tail[:end].replace("def _brief(entry: dict | None)", "def _entry_brief(entry: dict | None)")
block = re.sub(r"\b_brief\(", "_entry_brief(", block).replace("def _entry_entry_brief(", "def _entry_brief(")
s = head + block + tail[end:]
assert s.count("def _brief(row: dict) -> dict:") == 1 and s.count("def _entry_brief(") == 1
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
