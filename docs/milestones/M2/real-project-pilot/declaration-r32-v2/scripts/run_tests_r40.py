"""ORCH-09 (R40DECL-IMPL): run test_r40.py once with junit into PILOT/declaration-r32-v2/tests/test_r40.xml.

Usage: run_tests_r40.py <basetemp (new, under C:/t/r2x/r40-sandbox)>
The pytest process loads review39's r38_write_guard plugin (from PILOT/review39/scripts/pytest-plugins, read-only): writes
only to the basetemp, the junit folder and C:/t/r2x/r40-sandbox; no network. AI_* / ANTHROPIC* / OPENAI* / CLAUDE* /
owner-token variables are removed. Writes tests/test_r40.xml, tests/guard/test_r40.json and tests/SUMMARY.json."""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r40common as C  # noqa: E402

PLUGINS = C.REVIEW39 / "scripts" / "pytest-plugins"
STRIP = ("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER", "R36_OWNER", "R38_SANDBOX_BASE")


def main(basetemp):
    basetemp = pathlib.Path(basetemp)
    junit = C.PACKAGE / "tests"
    if basetemp.exists() or (junit / "test_r40.xml").exists():
        raise SystemExit("refused: a basetemp or junit file is never reused")
    assert basetemp.as_posix().startswith(C.SANDBOX_BASE.as_posix() + "/")
    (junit / "guard").mkdir(parents=True, exist_ok=True)
    basetemp.mkdir(parents=True)
    systmp = basetemp / "systmp"
    systmp.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(STRIP)}
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONPATH": str(PLUGINS),
            "R38_GUARD_ALLOW": ";".join([str(junit), str(basetemp), C.SANDBOX_BASE.as_posix()]), "R38_GUARD_REPORT": str(junit / "guard" / "test_r40.json"),
            "TEMP": str(systmp), "TMP": str(systmp), "TMPDIR": str(systmp), "GIT_OPTIONAL_LOCKS": "0"}
    x = junit / "test_r40.xml"
    r = subprocess.run([C.PY, "-B", "-m", "pytest", "-q", "-p", "r38_write_guard", "test_r40.py", f"--junitxml={x}", f"--basetemp={basetemp / 'pt'}"],
                       cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8")
    root = ET.parse(x).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    tot = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    guard = json.loads((junit / "guard" / "test_r40.json").read_text(encoding="utf-8"))
    summary = {"module": "test_r40", "python": C.PY, "returncode": r.returncode, **tot, "guard_refused": guard["refused_count"],
               "guard_network_refused": len(guard["network_refused"]), "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-400:],
               "basetemp": basetemp.as_posix()}
    C.write_json_once(junit / "SUMMARY.json", summary)
    print(json.dumps(summary, indent=1))
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
