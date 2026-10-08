"""ORCH-10 (R42PORT-IMPL): run the WHOLE r42 harness test suite from a harness folder; one junit XML per module.
(review39's run_tests_r39.py with the r42 paths, the merged interpreter and this task's audit guard.)

Usage: run_tests_r42.py <junit dir (new)> <basetemp dir (new, under C:/t/r2x/r42-sandbox)> [<harness dir>] [--only m1,m2]
Every pytest process AND every child it starts (lanes, ingestion, scoring) loads the R42 audit guard
(C:/t/iso/work/r2x/r42/guard/sitecustomize.py through PYTHONPATH): any `claude` process, any network use, any write or
read-write sqlite outside the work folder / the dry sandbox base / the two new packages / the scratchpad is REFUSED and
logged; TEMP / TMP point into the basetemp; AI_* / ANTHROPIC* / OPENAI* / CLAUDE* / owner-token / R38_SANDBOX_BASE
variables are removed. test_capture_store and test_run_control_r38 run from C:/t/iso/cand-r30n/backend (read-only use).
No model request; the AI ledger is opened mode=ro only."""
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"
WORK = pathlib.Path("C:/t/iso/work/r2x/r42")
GUARD = WORK / "guard"
GUARD_LOG = WORK / "out" / "guard"
SANDBOX = "C:/t/r2x/r42-sandbox"
MODULES = ["test_labels_adapter_r32", "test_literal_compare_r32", "test_lane_judge_r32", "test_score_bcr_r32", "test_concentration_r32",
           "test_run_set_selector_r32", "test_converter_r32", "test_dispatch_guard_r32", "test_allowance_r32", "test_preflight_r32",
           "test_sandbox_ingest_r32", "test_tripwire_r32", "test_runner_r32", "test_stop_rules", "test_state_check", "test_project_bounds_r32",
           "test_model_identity_r38", "test_visibility_r38", "test_request_paths_r39", "test_unread_pages_r39",
           "test_portability_r42", "test_runner_order_r42", "test_resume_authorization_r42"]
CANDIDATE_CWD_MODULES = ["test_capture_store", "test_run_control_r38", "test_global_provider_r42"]
STRIP = ("AI_", "ANTHROPIC", "OPENAI", "CLAUDE", "R34_OWNER", "R36_OWNER", "R38_SANDBOX_BASE", "R42_GUARD_ALLOW_EXTRA")


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


def guard_refusals_since(before: set) -> list:
    out = []
    if GUARD_LOG.is_dir():
        for f in sorted(GUARD_LOG.glob("refusals-*.log")):
            if f.name not in before:
                out += [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return out


def main(argv):
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    junit_dir, basetemp = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    H = pathlib.Path(argv[2]) if len(argv) > 2 else WORK / "harness-r32"
    for p in (junit_dir, basetemp):
        assert p.is_absolute(), p
    assert basetemp.as_posix().lower().startswith(SANDBOX.lower() + "/"), basetemp
    if junit_dir.exists() or basetemp.exists():
        raise SystemExit("refused: a junit or basetemp folder is never reused")
    junit_dir.mkdir(parents=True)
    basetemp.mkdir(parents=True)
    systmp = basetemp / "systmp"
    systmp.mkdir()
    removed = sorted(k for k in os.environ if k.startswith(STRIP))
    env = {k: v for k, v in os.environ.items() if k not in removed and k.upper() not in ("PWD", "OLDPWD")}
    env |= {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONPATH": str(GUARD),
            "TEMP": str(systmp), "TMP": str(systmp), "TMPDIR": str(systmp), "GIT_OPTIONAL_LOCKS": "0"}
    before = {f.name for f in GUARD_LOG.glob("refusals-*.log")} if GUARD_LOG.is_dir() else set()
    out = {}
    for i, m in enumerate(MODULES):
        if only and m not in only:
            continue
        if not (H / f"{m}.py").exists():
            out[m] = {"tests": 0, "failures": 0, "errors": 1, "skipped": 0, "missing": True}
            continue
        x = junit_dir / f"{m}.xml"
        r = subprocess.run([PY, "-B", "-m", "pytest", "-q", f"{m}.py", f"--junitxml={x}", f"--basetemp={basetemp / f'm{i:02d}'}"],
                           cwd=str(H), env=env, capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-300:]}
        if r.returncode:
            (junit_dir / f"{m}.stdout.txt").write_text(r.stdout[-20000:] + "\n---stderr---\n" + r.stderr[-5000:], encoding="utf-8", newline="\n")
        print(m, out[m], flush=True)
    for j, m in enumerate(CANDIDATE_CWD_MODULES):
        if only and m not in only:
            continue
        x = junit_dir / f"{m}.xml"
        r = subprocess.run([PY, "-B", "-m", "pytest", "-q", str(H / f"{m}.py"), f"--junitxml={x}", "--rootdir", str(H),
                            f"--basetemp={basetemp / f'c{j:02d}'}"], cwd="C:/t/iso/cand-r30n/backend",
                           env={**env, "PYTHONPATH": f"{H};{GUARD}", "AI_ENABLED": "false"}, capture_output=True, text=True)
        out[m] = counts(x) | {"returncode": r.returncode, "tail": r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else r.stderr[-300:]}
        if r.returncode:
            (junit_dir / f"{m}.stdout.txt").write_text(r.stdout[-20000:] + "\n---stderr---\n" + r.stderr[-5000:], encoding="utf-8", newline="\n")
        print(m, out[m], flush=True)
    refusals = guard_refusals_since(before)
    total = {k: sum(v[k] for v in out.values()) for k in ("tests", "failures", "errors", "skipped")}
    summary = {"tree": H.as_posix(), "interpreter": PY, "modules": out, "module_count": len(out), "total": total,
               "all_passed": all(v.get("returncode") == 0 and v["failures"] == 0 and v["errors"] == 0 for v in out.values()),
               "guard": {"module": (GUARD / "sitecustomize.py").as_posix(), "covers_child_processes": True, "refusals": refusals},
               "guard_refusals": len(refusals), "environment_removed": removed, "basetemp": basetemp.as_posix(), "no_twin": True}
    (junit_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: summary[k] for k in ("total", "all_passed", "guard_refusals", "module_count")}))
    return summary


if __name__ == "__main__":
    s = main(sys.argv[1:])
    sys.exit(0 if s["all_passed"] and not s["guard_refusals"] else 1)
