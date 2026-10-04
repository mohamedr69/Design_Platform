"""One-off patch: r15.1 boq_contract.py (copied) -> r16.1 (join_rows only; version string; value comparisons untouched)."""
import pathlib

H = pathlib.Path(__file__).resolve().parents[1]
p = H / "boq_contract.py"
s = p.read_text(encoding="utf-8")
assert 'CONTRACT_VERSION = "r2x-boq-contract-2026-09-30.r15.1"' in s
s = s.replace('CONTRACT_VERSION = "r2x-boq-contract-2026-09-30.r15.1"', 'CONTRACT_VERSION = "r2x-boq-contract-2026-09-30.r16.1"')
s = s.replace("CONTRACT_VERSION r2x-boq-contract-2026-09-30.r15.1  (r14.1 preserved in the Review 14 package; value comparisons unchanged)",
              "CONTRACT_VERSION r2x-boq-contract-2026-09-30.r16.1  (r15.1 preserved in the Review 15 package; value comparisons unchanged;\n"
              "R16-01: verified rows bound every fallback match -- see join_rows)")
a = s.index("def join_rows(")
b = s.index("# --- the submitted (old) expressions")
s = s[:a] + (H / "dev/join_r16.py.txt").read_text(encoding="utf-8") + s[b:]
p.write_bytes(s.replace("\r\n", "\n").encode("utf-8"))          # LF, like the other modules
print("patched")
