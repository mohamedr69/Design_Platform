"""ORCH-08C (R39HARNESS-IMPL): run the WHOLE r39 harness test suite from the r39 harness itself; one junit XML per module.
(review38's run_tests_r38.py with the r39 paths and the new module test_request_paths_r39.)

Usage: run_tests_r39.py <junit dir (new)> <basetemp dir (new)> [<harness dir>]
The harness's sandbox base is a declared / parameterised value (preflight_r32.sandbox_base(): default C:/t/r2x/r39-sandbox),
so every module runs from the harness itself -- no test twin. Every pytest process loads the r38_write_guard plugin
(refuses writes outside the basetemp, the junit dir and C:/t/r2x/r39-sandbox; refuses network); TEMP / TMP point into the
basetemp; AI_* / ANTHROPIC* / OPENAI* / CLAUDE* / owner-token / R38_SANDBOX_BASE variables are removed.
test_capture_store and test_run_control_r38 run from C:/t/iso/cand-r29/backend (read-only use: they import app.ai.provider).
No model request; nothing is written outside the junit dir, the basetemp and the r39 sandbox base (lane subprocesses are
not covered by the in-process guard; the package check compares the frozen trees before and after)."""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
WORK = pathlib.Path("C:/t/iso/work/r2x/r39")
PLUGINS = WORK / "scripts" / "pytest-plugins"
SANDBOX = "C:/t/r2x/r39-sandbox"
MODULES = ["test_labels_adapter_r32", "test_literal_compare_r32", "test_lane_judge_r32", "test_score_bcr_r32", "test_concentration_r32",
           "test_run_set_selector_r32", "test_converter_r32", "test_dispatch_guard_r32", "test_allowance_r32", "test_preflight_r32",
           "test_sandbox_ingest_r32", "test_tripwire_r32", "test_runner_r32", "test_stop_rules", "test_state_check", "test_project_bounds_r32",
           "test_model_identity_r38", "test_visibility_r38", "test_request_paths_r39", "test_unread_pages_r39"]
CANDIDATE_CWD_MODULES = ["test_capture_store", "test_run_control_r38"]
STRIP = ("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER", "R36_OWNER", "R38_SANDBOX_BASE")


def counts(xml_path):
    if not pathlib.Path(xml_path).exists():
        return {"tests": 0, "failures": 0, "errors": 1, "skipped": 0, "junit_missing": True}
    root = ET.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    tot = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for s in suites:
        for k in tot:
            tot[k] += int(s.get(k, 0))
    return tot


def main(junit_dir, basetemp, harness=None):
    H = pathlib.Path(harness or WORK / "harness-r32")
    junit_dir, basetemp = pathlib.Path(junit_dir), pathlib.Path(basetemp)
    for p in (junit_dir, basetemp):
        assert p.is_absolute(), p
    if junit_dir.exists() or basetemp.exists():
        raise SystemExit("refused: a junit or basetemp folder is never reused")
    guard_dir = junit_dir / "guard"
    guard_dir.mkdir(parents=True)
    basetemp.mkdir(parents=True)
    systmp = basetemp / "systmp"
    systmp.mkdir()
    removed = sorted(k for k in os.environ if k.startswith(STRIP))
    env = {k: v for k, v in os.environ.items() if k not in removed}
    allow = [str(junit_dir), str(basetemp), SANDBOX]
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONPATH": str(PLUGINS),
            "R38_GUARD_ALLOW": ";".join(allow), "TEMP": str(systmp), "TMP": str(systmp), "TMPDIR": str(systmp)}
    out = {}
    for i, m in enumerate(MODULES):
        x = junit_dir / f"{m}.xml"
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "r38_write_guard", f"{m}.py", f"--junitxml={x}", f"--basetemp={basetemp / f'm{i:02d}'}"],
                           cwd=str(H), env={**env, "R38_GUARD_REPORT": str(guard_dir / f"{m}.json")}, capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-300:]}
        print(m, out[m], flush=True)
    for j, m in enumerate(CANDIDATE_CWD_MODULES):
        x = junit_dir / f"{m}.xml"
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "r38_write_guard", str(H / f"{m}.py"), f"--junitxml={x}", "--rootdir", str(H),
                            f"--basetemp={basetemp / f'c{j:02d}'}"], cwd="C:/t/iso/cand-r29/backend",
                           env={**env, "PYTHONPATH": f"{H};{PLUGINS}", "AI_ENABLED": "false", "R38_GUARD_REPORT": str(guard_dir / f"{m}.json")},
                           capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-300:]}
        print(m, out[m], flush=True)
    guard = {}
    for g in sorted(guard_dir.glob("*.json")):
        d = json.loads(g.read_text(encoding="utf-8"))
        guard[g.stem] = {"refused": d["refused_count"], "network_refused": len(d["network_refused"])}
    total = {k: sum(v[k] for v in out.values()) for k in ("tests", "failures", "errors", "skipped")}
    summary = {"tree": H.as_posix(), "modules": out, "module_count": len(out), "total": total,
               "all_passed": all(v["returncode"] == 0 and v["failures"] == 0 and v["errors"] == 0 for v in out.values()),
               "guard": guard, "guard_refusals": sum(v["refused"] + v["network_refused"] for v in guard.values()),
               "guard_reports": len(guard), "environment_removed": removed, "allowed_roots": allow, "no_twin": True}
    (junit_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: summary[k] for k in ("total", "all_passed", "guard_refusals", "module_count")}))
    return summary


if __name__ == "__main__":
    s = main(*sys.argv[1:4])
    sys.exit(0 if s["all_passed"] and not s["guard_refusals"] else 1)
