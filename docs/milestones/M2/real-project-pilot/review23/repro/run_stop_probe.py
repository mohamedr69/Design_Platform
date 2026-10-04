"""Run the reviewer's Review 23 resume-stop probe (byte copy in reviewer-copy/, hash-checked) against a chosen runner, in
THIS package's own output directory and a private workspace. Substitutions (recorded in RUN.json): the probe's
`R=Path(__file__).parent` -> the output dir; `R/'arm_ev.py'` -> the harness under test; the workspace path from a
WORKSPACE.json written here. Then the reviewer's three regressions run in the output dir.
Usage: run_stop_probe.py <harness_dir> <out_dir> <workspace_dir>"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

harness, out, ws = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
src = pathlib.Path(__file__).parent / "reviewer-copy"
SHA = {"resume_stop_probe.py": "a0d75e29716ffec24c1e147c39256c0a54c2dc58f5f06b3eb5288982e84e1cff",
       "test_review23_terminal_stop.py": "f3e8d6a0e641e57b5d7e4c3a797b60317c437e7efeb4239407673549812f5c05"}
for n, h in SHA.items():
    assert hashlib.sha256((src / n).read_bytes()).hexdigest() == h, n
if out.exists() or ws.exists():
    sys.exit("output dir / workspace exist: never rerun in place")
out.mkdir(parents=True)
ws.mkdir(parents=True)
(out / "WORKSPACE.json").write_text(json.dumps({"workspace": str(ws)}), encoding="utf-8")
probe = (src / "resume_stop_probe.py").read_text(encoding="utf-8")
subs = [("R=Path(__file__).parent", f"R=Path({str(out)!r})"), ("str(R/'arm_ev.py')", f"str(Path({harness!r})/'arm_ev.py')")]
for a, b in subs:
    assert probe.count(a) == 1, a
    probe = probe.replace(a, b)
(out / "resume_stop_probe.py").write_text(probe, encoding="utf-8")
shutil.copyfile(src / "test_review23_terminal_stop.py", out / "test_review23_terminal_stop.py")
if (src / "pytest.ini").exists():
    shutil.copyfile(src / "pytest.ini", out / "pytest.ini")
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
for k in list(env):
    if k.startswith("AI_EVIDENCE_") or k in ("PILOT_DRY_KILL_AFTER", "PILOT_DRY_LATENCY_S", "PILOT_DRY_NEW_TAG_OVERRIDE", "XTRACK_FAKE_NOW", "PILOT_DRY_FAIL_FROM", "PILOT_DRY_KILL_AT_STOP"):
        env.pop(k)
r1 = subprocess.run([sys.executable, "resume_stop_probe.py"], cwd=str(out), capture_output=True, text=True, env=env)
(out / "CRITICAL-STOP-PROBE.log").write_text(r1.stdout + r1.stderr, encoding="utf-8")
(out / "CRITICAL-STOP-PROBE.exit").write_text(f"{r1.returncode}\n")
r2 = subprocess.run([sys.executable, "-m", "pytest", "test_review23_terminal_stop.py", "-q", "-p", "no:cacheprovider", f"--junitxml={out / 'REVIEW23-REGRESSIONS.xml'}"],
                    cwd=str(out), capture_output=True, text=True, env=env)
(out / "REVIEW23-REGRESSIONS.log").write_text(r2.stdout + r2.stderr, encoding="utf-8")
(out / "REVIEW23-REGRESSIONS.exit").write_text(f"{r2.returncode}\n")
(out / "RUN.json").write_text(json.dumps({"harness": harness, "arm_ev_sha256": hashlib.sha256(pathlib.Path(harness, "arm_ev.py").read_bytes()).hexdigest(), "workspace": str(ws),
                                          "reviewer_sha256": SHA, "substitutions": subs, "probe_exit": r1.returncode, "regressions_exit": r2.returncode}, indent=1) + "\n", encoding="utf-8")
print("probe exit", r1.returncode, "| regressions exit", r2.returncode, "|", (r2.stdout.strip().splitlines() or [""])[-1])
