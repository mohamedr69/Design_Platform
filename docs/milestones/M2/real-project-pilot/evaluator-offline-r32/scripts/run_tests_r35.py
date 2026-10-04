"""ORCH-06: run the two test modules and write one junit XML per module into <package>/tests/.
Usage: run_tests_r35.py            (cwd C:/t/iso/work/r2x/r35; pytest basetemp under the work folder; no model request)"""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PKG = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path("C:/t/iso/work/r2x/r35")
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
MODULES = ["test_fixtures_r32", "test_parity_r35"]


def counts(xml_path):
    root = ET.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    tot = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for s in suites:
        for k in tot:
            tot[k] += int(s.get(k, 0))
    return tot


def main():
    assert os.path.normcase(os.getcwd()).startswith(os.path.normcase(str(WORK))), "run from the work folder"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AI_", "R34_OWNER"))}
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider", "AI_ENABLED": "false"}
    out = {}
    for i, m in enumerate(MODULES):
        x = PKG / "tests" / f"{m}.xml"
        bt = WORK / "pytest-tmp" / f"m{i:02d}-{m}"
        bt.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([PY, "-m", "pytest", "-q", str(PKG / "tests" / f"{m}.py"), f"--junitxml={x}", f"--basetemp={bt}"],
                           cwd=str(WORK), env=env, capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode}
        if r.returncode != 0:
            print(r.stdout[-4000:], r.stderr[-2000:])
    total = {k: sum(v[k] for v in out.values()) for k in ("tests", "failures", "errors", "skipped")}
    summary = {"modules": out, "total": total,
               "all_passed": all(v["returncode"] == 0 and v["failures"] == 0 and v["errors"] == 0 for v in out.values())}
    print(json.dumps(summary, indent=1, sort_keys=True))
    return summary


if __name__ == "__main__":
    sys.exit(0 if main()["all_passed"] else 1)
