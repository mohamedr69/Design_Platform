"""ORCH-07 (R37DECL-IMPL): run test_r37.py once with junit into PILOT/declaration-r32/tests/test_r37.xml (refuses an
existing file). Bytecode writing off, no pytest cache, basetemp in the scratchpad, GIT_OPTIONAL_LOCKS=0.
Usage: run_tests_r37.py <new basetemp folder (absolute, in the scratchpad)>"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import r37common as C

if __name__ == "__main__":
    basetemp = pathlib.Path(sys.argv[1])
    assert basetemp.is_absolute() and not basetemp.exists()
    junit = C.PACKAGE / "tests" / "test_r37.xml"
    if junit.exists():
        raise SystemExit(f"refused: {junit} exists")
    junit.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONIOENCODING": "utf-8", "GIT_OPTIONAL_LOCKS": "0"}
    env.pop("R34_OWNER_DISPATCH_TOKEN", None)
    r = subprocess.run([C.PY, "-B", "-m", "pytest", "-q", "test_r37.py", f"--junitxml={junit}", f"--basetemp={basetemp}"], cwd=str(C.WORK), env=env)
    sys.exit(r.returncode)
