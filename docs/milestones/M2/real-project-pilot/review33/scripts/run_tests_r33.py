"""ORCH-05.1: run every harness-r32 test module and write one junit XML per module.
Usage: run_tests_r33.py <junit dir> <pytest basetemp dir>
The capture-store test (a copy of review31's) runs from the candidate tree, read-only, as review31/COMMANDS.md says.
No model request; sandboxes only under C:/t/r2x/r33-sandbox/tests/."""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
H = pathlib.Path("C:/t/iso/work/r2x/r33/harness-r32")
MODULES = ["test_labels_adapter_r32", "test_literal_compare_r32", "test_lane_judge_r32", "test_score_bcr_r32", "test_concentration_r32",
           "test_run_set_selector_r32", "test_converter_r32", "test_dispatch_guard_r32", "test_allowance_r32", "test_sandbox_ingest_r32",
           "test_tripwire_r32", "test_runner_r32", "test_stop_rules", "test_state_check"]


def counts(xml_path):
    root = ET.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    tot = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for s in suites:
        for k in tot:
            tot[k] += int(s.get(k, 0))
    return tot


def main(junit_dir, basetemp):
    junit_dir, basetemp = pathlib.Path(junit_dir), pathlib.Path(basetemp)
    junit_dir.mkdir(parents=True, exist_ok=True)
    basetemp.mkdir(parents=True, exist_ok=True)          # pytest creates <basetemp>/<module> without parents
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider"}
    out = {}
    for m in MODULES:
        x = junit_dir / f"{m}.xml"
        r = subprocess.run([PY, "-m", "pytest", "-q", f"{m}.py", f"--junitxml={x}", f"--basetemp={basetemp / m}"], cwd=str(H), env=env,
                           capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode}
    x = junit_dir / "test_capture_store.xml"
    r = subprocess.run([PY, "-m", "pytest", "-q", str(H / "test_capture_store.py"), f"--junitxml={x}", "--rootdir", str(H),
                        f"--basetemp={basetemp / 'test_capture_store'}"], cwd="C:/t/iso/cand-r29/backend",
                       env={**env, "PYTHONPATH": str(H), "AI_ENABLED": "false"}, capture_output=True, text=True)
    out["test_capture_store"] = counts(x) | {"returncode": r.returncode}
    total = {k: sum(v[k] for v in out.values()) for k in ("tests", "failures", "errors", "skipped")}
    summary = {"modules": out, "total": total, "all_passed": all(v["returncode"] == 0 and v["failures"] == 0 and v["errors"] == 0 for v in out.values())}
    print(json.dumps(summary, indent=1, sort_keys=True))
    return summary


if __name__ == "__main__":
    s = main(sys.argv[1], sys.argv[2])
    sys.exit(0 if s["all_passed"] else 1)
