"""One-off patch: turn the copied r14.1 boq_contract.py into r15.1 (join section and header only)."""
import pathlib

p = pathlib.Path(__file__).with_name("boq_contract.py")
s = p.read_text(encoding="utf-8")
s = s.replace('CONTRACT_VERSION r2x-boq-contract-2026-09-30.1', 'CONTRACT_VERSION r2x-boq-contract-2026-09-30.r15.1  (r14.1 preserved in the Review 14 package; value comparisons unchanged)')
s = s.replace('CONTRACT_VERSION = "r2x-boq-contract-2026-09-30.1"', 'CONTRACT_VERSION = "r2x-boq-contract-2026-09-30.r15.1"')
start = s.index("Truth join (`join_rows`)")
end = s.index('"""', start)
s = s[:start] + '''Truth join (`join_rows`) -- R15-02: alignment never uses a SCORED value (part number or quantity)
  * per source document hash and page;
  * 1. GEOMETRY first: a truth row that carries a VERIFIED row position ('y', same render scale as the emitted rows)
       is paired with the one emitted row within GEOMETRY_TOLERANCE of it ('matched_geometry'); two candidates on either
       side -> held; a verified truth row with no emitted row near it is MISSED (it is never offered to another row);
  * 2. the rest: truth rows in print order and emitted rows in geometry (y) order, aligned one-to-one and
       order-preserving on DESCRIPTION similarity only (token Jaccard >= 0.5; the description is not a scored field);
  * 3. a pair is HELD ('ambiguous', with every equally good truth candidate listed) when an equally good alignment gives
       the emitted row another truth row -- e.g. a single emitted duplicate of two identical source rows. Held candidates
       are reported, never resolved by a value; unmatched rows on both sides stay visible.
  Consequence: a quantity misread can no longer select the truth row that makes it correct (Review 15 probe).
''' + s[end:]
a = s.index("# --- the join ---")
b = s.index("# --- the submitted (old) expressions")
s = s[:a] + pathlib.Path(__file__).with_name("_join_r15.py.txt").read_text(encoding="utf-8") + s[b:]
p.write_text(s, encoding="utf-8")
print("patched")
