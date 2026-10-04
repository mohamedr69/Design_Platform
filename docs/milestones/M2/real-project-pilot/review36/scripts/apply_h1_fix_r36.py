"""ORCH-06C (R36HARNESS-IMPL), Verification 36 finding R36-08 (H1): the one bounded change to the r32 harness.

Usage: apply_h1_fix_r36.py apply <harness dir>      change the copy in place (refuses unless both files hold their review34 bytes)
       apply_h1_fix_r36.py derive <out dir>        re-derive both changed files from PILOT/review34 into <out dir> (a check)

What it does, and nothing else:
  1. literal_compare_r32.py: the body of norm_revision (review34 lines 68-77) is replaced by NEW_NORM_REVISION. After the
     unchanged Arabic branch, dash folding, upper-casing and whitespace collapsing, the optional REVISION / REV / REV. /
     R / R. prefix is matched first (the same alternatives, in the same order, as the review34 pattern) and EVERY
     whitespace character after it is removed before the number pattern 0*(\\d+) is matched; the non-numeric fallback is
     unchanged. Every other byte of the module is unchanged (checked: the file is the review34 file with exactly that
     one block replaced).
  2. test_literal_compare_r32.py: TEST_ADDITION_FILE is appended at the end; the review34 file is an exact byte prefix of
     the new file (every existing test unchanged).
Both review34 hashes are checked first ("PACKET MISMATCH" otherwise)."""
import hashlib
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
R34_HARNESS = PILOT / "review34" / "scripts" / "harness-r32"
OLD_SHA = {"literal_compare_r32.py": "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6",
           "test_literal_compare_r32.py": "1d91cb5443ac5258b3fc60268b80a2815517badb5ebf5c77a3d0bf6b62831e4e"}
TEST_ADDITION_FILE = pathlib.Path(__file__).resolve().parent / "h1_test_addition_r36.txt"

OLD_NORM_REVISION = r'''def norm_revision(value) -> str:
    s = "" if value is None else str(value).strip()
    if is_arabic(s):
        return norm_text(s)
    s = _DASH_RE.sub("-", s).upper()
    s = _WS_RE.sub(" ", s).strip()
    m = re.fullmatch(r"(?:REVISION|REV\.?|R\.?)?\s*0*(\d+)", s)
    if m:
        return f"R{int(m.group(1))}"
    return _WS_RE.sub("", s)
'''

NEW_NORM_REVISION = r'''def norm_revision(value) -> str:
    """A revision compared by value. Arabic literals: norm_text only (whitespace removed; no case or dash folding).
    Otherwise dash variants are read as '-' and the value is upper-cased; then, after an optional REVISION / REV /
    REV. / R / R. prefix, EVERY whitespace character inside the value is removed before the number is matched ((i2);
    ORCH-06C, Verification 36 R36-08), and a number is read by value: '0 1' == '01' == 'REV 0 1' == 'R 01' -> 'R1',
    '0 0' -> 'R0', 'Rev. 0 2' -> 'R2'. A value that is not a number keeps its own characters with every whitespace
    character removed ('A 1' -> 'A1')."""
    s = "" if value is None else str(value).strip()
    if is_arabic(s):
        return norm_text(s)
    s = _DASH_RE.sub("-", s).upper()
    s = _WS_RE.sub(" ", s).strip()
    prefix = re.match(r"(?:REVISION|REV\.?|R\.?)?", s)
    m = re.fullmatch(r"0*(\d+)", _WS_RE.sub("", s[prefix.end():]))
    if m:
        return f"R{int(m.group(1))}"
    return _WS_RE.sub("", s)
'''


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def transform(old_module: bytes, old_test: bytes) -> tuple:
    if sha(old_module) != OLD_SHA["literal_compare_r32.py"] or sha(old_test) != OLD_SHA["test_literal_compare_r32.py"]:
        raise SystemExit("PACKET MISMATCH: the input files are not the review34 bytes")
    old_b, new_b = OLD_NORM_REVISION.encode("utf-8"), NEW_NORM_REVISION.encode("utf-8")
    if old_module.count(old_b) != 1:
        raise SystemExit("the review34 norm_revision block was not found exactly once")
    module = old_module.replace(old_b, new_b)
    i = old_module.index(old_b)
    assert module[:i] == old_module[:i] and module[i + len(new_b):] == old_module[i + len(old_b):]
    addition = TEST_ADDITION_FILE.read_bytes()
    assert b"\r" not in addition and addition.startswith(b"\n")
    test = old_test + addition
    return module, test


def main(cmd, folder):
    folder = pathlib.Path(folder)
    if cmd == "apply":
        mp, tp = folder / "literal_compare_r32.py", folder / "test_literal_compare_r32.py"
        module, test = transform(mp.read_bytes(), tp.read_bytes())
        mp.write_bytes(module)
        tp.write_bytes(test)
    elif cmd == "derive":
        module, test = transform((R34_HARNESS / "literal_compare_r32.py").read_bytes(), (R34_HARNESS / "test_literal_compare_r32.py").read_bytes())
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "literal_compare_r32.py").write_bytes(module)
        (folder / "test_literal_compare_r32.py").write_bytes(test)
    else:
        raise SystemExit(__doc__)
    print(f"literal_compare_r32.py {OLD_SHA['literal_compare_r32.py']} -> {sha(module)}")
    print(f"test_literal_compare_r32.py {OLD_SHA['test_literal_compare_r32.py']} -> {sha(test)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
