"""Run the reviewer's Review 24 provider-boundary probe (byte copies in reviewer-copy/, hash-checked) against a chosen
runner, in THIS package's own staging directory and a NEW private scenario root. Staging: the reviewer's
`lifecycle_probes_adapted.py`, `provider_boundary_probe.py`, `test_provider_boundary.py` and `pytest.ini` byte-identical,
plus the runner files of the harness under test (arm_ev.py, coverage_v4.py, score_arms_v4.py, dry_provider2.py,
xtrack2.py) -- the reviewer's layout. The helper reads its scenario root from R23_LIFECYCLE_ROOT (set here to the new
root) and TEMP/TMP from the environment. No substitution of the reviewer's code is needed.
Usage: run_provider_probe.py <harness_dir> <stage_dir> <scenario_root>"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

harness, stage, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
src = pathlib.Path(__file__).parent / "reviewer-copy"
SHA = {"provider_boundary_probe.py": "3cb228cfb12a27bc3f3f4658e3cf51a56ff1ccb28159ad8ad2d5d7140cffe761",
       "test_provider_boundary.py": "bf4cb1c6486e831500756bf1d52d10390676cae5f4fc5319e2ac1a66fe2aee7a",
       "lifecycle_probes_adapted.py": "a8033dde7a46dc3a564049eed1d903a0b68c3b69d74ebbc9c14a3af9162af345"}
for n, h in SHA.items():
    assert hashlib.sha256((src / n).read_bytes()).hexdigest() == h, n
if stage.exists() or root.exists():
    sys.exit("stage dir / scenario root exist: never rerun in place")
stage.mkdir(parents=True)
for n in ("provider_boundary_probe.py", "test_provider_boundary.py", "lifecycle_probes_adapted.py", "pytest.ini"):
    shutil.copyfile(src / n, stage / n)
RUNNER = ("arm_ev.py", "coverage_v4.py", "score_arms_v4.py", "dry_provider2.py", "xtrack2.py") + (("provider_journal.py",) if (harness / "provider_journal.py").exists() else ())   # v4.2 adds its journal module
for n in RUNNER:
    shutil.copyfile(harness / n, stage / n)
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "R23_LIFECYCLE_ROOT": str(root), "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp", "PYTHONDONTWRITEBYTECODE": "1"}
for k in list(env):
    if k.startswith("AI_EVIDENCE_") or k.startswith("PILOT_DRY") or k == "XTRACK_FAKE_NOW":
        env.pop(k)
r1 = subprocess.run([sys.executable, "provider_boundary_probe.py"], cwd=str(stage), capture_output=True, text=True, env=env, timeout=1800)
(stage / "PROVIDER-BOUNDARY-PROBE.log").write_text(r1.stdout + r1.stderr, encoding="utf-8")
(stage / "PROVIDER-BOUNDARY-PROBE.exit").write_text(f"{r1.returncode}\n")
r2 = subprocess.run([sys.executable, "-m", "pytest", "test_provider_boundary.py", "-q", "-p", "no:cacheprovider", f"--junitxml={stage / 'REVIEW24-REGRESSIONS.xml'}"],
                    cwd=str(stage), capture_output=True, text=True, env=env)
(stage / "REVIEW24-REGRESSIONS.log").write_text(r2.stdout + r2.stderr, encoding="utf-8")
(stage / "REVIEW24-REGRESSIONS.exit").write_text(f"{r2.returncode}\n")
(stage / "RUN.json").write_text(json.dumps({"harness": str(harness), "runner_files_sha256": {n: hashlib.sha256((harness / n).read_bytes()).hexdigest() for n in RUNNER},
                                            "scenario_root": str(root), "reviewer_sha256": SHA, "substitutions": "none (staged byte copies; R23_LIFECYCLE_ROOT / TEMP from env)",
                                            "probe_exit": r1.returncode, "regressions_exit": r2.returncode}, indent=1) + "\n", encoding="utf-8")
print("probe exit", r1.returncode, "| regressions exit", r2.returncode, "|", (r2.stdout.strip().splitlines() or [""])[-1])
