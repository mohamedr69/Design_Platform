"""ORCH-06C (R36HARNESS-IMPL): run the review34 harness test suite from the r36 copy; one junit XML per module.

Usage: run_tests_r36.py twin  <junit dir> <basetemp dir>    the WHOLE suite (16 modules) from the test-run twin
       run_tests_r36.py bound <junit dir> <basetemp dir>    the 14 modules that create no sandbox, from the bound copy itself

twin  = C:/t/iso/work/r2x/r36/harness-r32-suite-twin: the bound copy with only 'C:/t/r2x/r34-sandbox' -> 'C:/t/r2x/r36-sandbox'
        (make_suite_twin_r36.py; re-verified byte for byte before the run, refused otherwise). Sandboxes: C:/t/r2x/r36-sandbox/.
bound = C:/t/iso/work/r2x/r36/harness-r32 (the bound copy). test_runner_r32 and test_sandbox_ingest_r32 are not run here:
        they create sandboxes under the review34 base C:/t/r2x/r34-sandbox, which this task may not write.
Every pytest process loads the r36_write_guard plugin (refuses writes outside the basetemp, the junit dir and, for the
twin, C:/t/r2x/r36-sandbox; refuses network); TEMP / TMP point into the basetemp. AI_* / ANTHROPIC* / OPENAI* / CLAUDE* /
owner-token variables are removed.
The capture-store test runs from C:/t/iso/cand-r29/backend (read-only use), as review34's run_tests_r34.py runs it.
No model request; nothing is written outside the junit dir, the basetemp and (twin) the r36 sandbox."""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
WORK = pathlib.Path("C:/t/iso/work/r2x/r36")
BOUND = WORK / "harness-r32"
TWIN = WORK / "harness-r32-suite-twin"
PLUGINS = WORK / "pytest-plugins"
SANDBOX = "C:/t/r2x/r36-sandbox"
MODULES = ["test_labels_adapter_r32", "test_literal_compare_r32", "test_lane_judge_r32", "test_score_bcr_r32", "test_concentration_r32",
           "test_run_set_selector_r32", "test_converter_r32", "test_dispatch_guard_r32", "test_allowance_r32", "test_preflight_r32",
           "test_sandbox_ingest_r32", "test_tripwire_r32", "test_runner_r32", "test_stop_rules", "test_state_check"]
SANDBOX_MODULES = ("test_runner_r32", "test_sandbox_ingest_r32")
STRIP = ("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER", "R36_OWNER")


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


def verify_twin():
    sys.path.insert(0, str(WORK))
    import make_suite_twin_r36 as T  # noqa: E402
    bound = sorted(p.name for p in BOUND.iterdir() if p.is_file())
    twin = sorted(p.name for p in TWIN.iterdir() if p.is_file())
    bad = [n for n in bound if n not in twin or T.twin_bytes(n, (BOUND / n).read_bytes()) != (TWIN / n).read_bytes()]
    if bound != twin or bad:
        raise SystemExit(f"refused: the twin differs from the substituted bound copy: {bad or sorted(set(bound) ^ set(twin))}")
    return len(bound)


def main(mode, junit_dir, basetemp):
    assert mode in ("twin", "bound"), mode
    H = TWIN if mode == "twin" else BOUND
    junit_dir, basetemp = pathlib.Path(junit_dir), pathlib.Path(basetemp)
    for p in (junit_dir, basetemp):
        assert p.is_absolute(), p
    if junit_dir.exists() or basetemp.exists():
        raise SystemExit("refused: a junit or basetemp folder is never reused")
    twin_files = verify_twin() if mode == "twin" else None
    guard_dir = junit_dir / "guard"
    guard_dir.mkdir(parents=True)
    basetemp.mkdir(parents=True)
    systmp = basetemp / "systmp"                  # pytest's capture files and any tempfile use: inside an allowed root
    systmp.mkdir()
    removed = sorted(k for k in os.environ if k.startswith(STRIP))
    env = {k: v for k, v in os.environ.items() if k not in removed}
    allow = [str(junit_dir), str(basetemp)] + ([SANDBOX] if mode == "twin" else [])
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider",
            "PYTHONPATH": str(PLUGINS), "R36_GUARD_ALLOW": ";".join(allow), "TEMP": str(systmp), "TMP": str(systmp), "TMPDIR": str(systmp)}
    modules = [m for m in MODULES if mode == "twin" or m not in SANDBOX_MODULES]
    out = {}
    for i, m in enumerate(modules):
        x = junit_dir / f"{m}.xml"
        r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "r36_write_guard", f"{m}.py", f"--junitxml={x}", f"--basetemp={basetemp / f'm{i:02d}'}"],
                           cwd=str(H), env={**env, "R36_GUARD_REPORT": str(guard_dir / f"{m}.json")}, capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-300:]}
    x = junit_dir / "test_capture_store.xml"
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "r36_write_guard", str(H / "test_capture_store.py"), f"--junitxml={x}", "--rootdir", str(H),
                        f"--basetemp={basetemp / 'cs'}"], cwd="C:/t/iso/cand-r29/backend",
                       env={**env, "PYTHONPATH": f"{H};{PLUGINS}", "AI_ENABLED": "false", "R36_GUARD_REPORT": str(guard_dir / "test_capture_store.json")},
                       capture_output=True, text=True)
    out["test_capture_store"] = counts(x) | {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-300:]}
    guard = {}
    for g in sorted(guard_dir.glob("*.json")):
        d = json.loads(g.read_text(encoding="utf-8"))
        guard[g.stem] = {"refused": d["refused_count"], "network_refused": len(d["network_refused"])}
    total = {k: sum(v[k] for v in out.values()) for k in ("tests", "failures", "errors", "skipped")}
    summary = {"mode": mode, "tree": H.as_posix(), "twin_files_verified": twin_files, "modules": out, "module_count": len(out), "total": total,
               "all_passed": all(v["returncode"] == 0 and v["failures"] == 0 and v["errors"] == 0 for v in out.values()),
               "guard": guard, "guard_refusals": sum(v["refused"] + v["network_refused"] for v in guard.values()),
               "guard_reports": len(guard), "environment_removed": removed, "allowed_roots": allow,
               "not_run_here": [] if mode == "twin" else list(SANDBOX_MODULES)}
    print(json.dumps(summary, indent=1, sort_keys=True))
    return summary


if __name__ == "__main__":
    s = main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if s["all_passed"] and not s["guard_refusals"] else 1)
