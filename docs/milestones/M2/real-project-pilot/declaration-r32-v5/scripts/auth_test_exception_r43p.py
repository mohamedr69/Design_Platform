"""R43-40 (new): the evidence of the declared test exception (Verification 43 R43V-05). It repeats, by name only, the search of
review43 test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests (OWNER-DISPATCH-AUTHORIZATION*.json under the
sandbox base, C:/t/iso/work/r2x/r38 and PILOT) and records every hit with its sha256; the declared exception holds when the only
hit is the owner's committed v3 file. Nothing is opened but those hits (read as bytes for the hash); the test is not run and
not changed. Usage: <bound python> -B auth_test_exception_r43p.py <out json>"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

TEST = C.HARNESS43 / "test_runner_r32.py"


def main(out: str) -> int:
    lines = TEST.read_text(encoding="utf-8").split("\n")
    at = [i for i, ln in enumerate(lines, 1) if "OWNER-DISPATCH-AUTHORIZATION*.json" in ln]
    roots = [C.SANDBOX_BASE, pathlib.Path("C:/t/iso/work/r2x/r38"), C.PILOT]
    hits = sorted({p.as_posix() for r in roots if r.exists() for p in r.rglob("OWNER-DISPATCH-AUTHORIZATION*.json")})
    v3 = (C.V3 / C.AUTH_NAME).as_posix()
    log = subprocess.run(["git", "-C", str(C.EP), "log", "--format=%h %s", "-1", "--", str(C.V3 / C.AUTH_NAME)], capture_output=True, text=True,
                         env={**__import__("os").environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.strip()
    res = {"test": f"{TEST.as_posix()}::test_no_authorization_file_was_written_by_the_tests", "test_sha256": C.sha256_file(TEST),
           "search_lines": {str(i): lines[i - 1].strip() for i in at}, "roots": [r.as_posix() for r in roots],
           "hits": [{"path": h, "sha256": C.sha256_file(h)} for h in hits], "v3_file": {"path": v3, "sha256": C.sha256_file(v3), "commit": log},
           "finding": "Verification 43 R43V-05 (minor): a test-environment artefact and a v4 precondition, not a harness defect"}
    res["exception_holds"] = hits == [v3] and res["v3_file"]["sha256"] == C.V3_AUTH_SHA
    C.write_json(out, res)
    print(json.dumps({"hits": len(hits), "exception_holds": res["exception_holds"], "commit": log}))
    return 0 if res["exception_holds"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
