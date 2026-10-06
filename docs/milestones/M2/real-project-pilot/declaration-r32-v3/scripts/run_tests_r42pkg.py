"""ORCH-10 (R42PORT-IMPL): run test_r42.py (the v3 declaration package's own tests) once with junit into
PILOT/declaration-r32-v3/tests/test_r42.xml.

Usage: run_tests_r42pkg.py <basetemp (new, under C:/t/r2x/r42-sandbox)>
The pytest process and its children load the R42 audit guard (C:/t/iso/work/r2x/r42/guard/sitecustomize.py via
PYTHONPATH): no `claude` process, no network, no write outside the work folder, the dry sandbox base, the two new packages
and the scratchpad. AI_* / ANTHROPIC* / OPENAI* / CLAUDE* / owner-token variables are removed. Writes tests/test_r42.xml and
tests/SUMMARY.json."""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r42common as C  # noqa: E402

GUARD = C.WORK / "guard"
STRIP = ("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER", "R36_OWNER", "R38_SANDBOX_BASE", "R42_GUARD_ALLOW_EXTRA")


def main(basetemp):
    basetemp = pathlib.Path(basetemp)
    junit = C.PACKAGE / "tests"
    if basetemp.exists() or (junit / "test_r42.xml").exists():
        raise SystemExit("refused: a basetemp or junit file is never reused")
    assert basetemp.as_posix().startswith(C.SANDBOX_BASE.as_posix() + "/")
    junit.mkdir(parents=True, exist_ok=True)
    basetemp.mkdir(parents=True)
    systmp = basetemp / "systmp"
    systmp.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith(STRIP) and k.upper() not in ("PWD", "OLDPWD")}
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONPATH": str(GUARD),
            "TEMP": str(systmp), "TMP": str(systmp), "TMPDIR": str(systmp), "GIT_OPTIONAL_LOCKS": "0"}
    log = C.WORK / "out" / "guard"
    before = {f.name for f in log.glob("refusals-*.log")} if log.is_dir() else set()
    x = junit / "test_r42.xml"
    r = subprocess.run([C.PY, "-B", "-m", "pytest", "-q", "test_r42.py", f"--junitxml={x}", f"--basetemp={basetemp / 'pt'}"],
                       cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8")
    root = ET.parse(x).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    tot = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    refusals = [ln for f in (log.glob("refusals-*.log") if log.is_dir() else []) if f.name not in before
                for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    summary = {"module": "test_r42", "python": C.PY, "returncode": r.returncode, **tot, "guard_refusals": len(refusals), "guard_refusal_lines": refusals,
               "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-400:], "basetemp": basetemp.as_posix(),
               "scripts_folder": HERE.as_posix()}
    if r.returncode:
        summary["stdout_tail"] = r.stdout[-6000:]
    C.write_json_once(junit / "SUMMARY.json", summary)
    print(json.dumps({k: summary[k] for k in ("tests", "failures", "errors", "skipped", "guard_refusals", "tail")}, indent=1))
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
