"""Run the Review 22 reviewer artifacts (byte copies in reviewer-copy/, hash-checked) against the v4 harness, writing into
THIS package only. Substitutions (recorded in RUN.json): the reviewer's own sys.path / output dir as in
run_reviewer_probes.py, plus the module names coverage_v3 / score_arms_v3 -> coverage_v4 / score_arms_v4 and the metrics
file name ARMS-METRICS.v3.json -> ARMS-METRICS.v4.json. The reviewer's assertions are untouched.
Usage: run_reviewer_probes_v4.py <harness_dir> <out_dir>"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

harness, out = sys.argv[1], pathlib.Path(sys.argv[2])
src = pathlib.Path(__file__).parent / "reviewer-copy"
SHA = {"scorer_probes.py": "ee6e8166ad5d8c9a3ed52987234ce826acdcfe1681359117a46f9803af483d27",
       "test_review22_scoring.py": "b981b468ba3eaa1835e231b4becff63b92753508e30d1b3467dad8a85a17ba46",
       "final_checks.py": "953ba2ad1ce10d0c588ce399f1710eaac0d59f43ef5e60ed6cfc57bd1521d4bc"}
for n, h in SHA.items():
    assert hashlib.sha256((src / n).read_bytes()).hexdigest() == h, n
out.mkdir(parents=True, exist_ok=True)
probe = (src / "scorer_probes.py").read_text(encoding="utf-8")
subs = [("sys.path.insert(0,str(R))", f"sys.path.insert(0,{harness!r})"), ("R=Path(__file__).parent", f"R=Path({str(out)!r})"),
        ("import coverage_v3 as cv", "import coverage_v4 as cv"), ("import score_arms_v3 as scorer", "import score_arms_v4 as scorer")]
for a, b in subs:
    assert probe.count(a) == 1, a
    probe = probe.replace(a, b)
(out / "scorer_probes.py").write_text(probe, encoding="utf-8")
test = (src / "test_review22_scoring.py").read_text(encoding="utf-8")
tsubs = [("import coverage_v3 as cv", f"import sys; sys.path.insert(0, {harness!r})" + chr(10) + "import coverage_v4 as cv"), ("ARMS-METRICS.v3.json", "ARMS-METRICS.v4.json")]
for a, b in tsubs:
    assert test.count(a) >= 1, a
    test = test.replace(a, b)
(out / "test_review22_scoring.py").write_text(test, encoding="utf-8")
if (src / "pytest.ini").exists():
    shutil.copyfile(src / "pytest.ini", out / "pytest.ini")
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "AI_ENABLED": "false"}
for k in list(env):
    if k.startswith("AI_EVIDENCE_"):
        env.pop(k)
r1 = subprocess.run([sys.executable, "scorer_probes.py"], cwd=str(out), capture_output=True, text=True, env=env)
(out / "SCORER-PROBES.log").write_text(r1.stdout + r1.stderr, encoding="utf-8")
(out / "SCORER-PROBES.exit").write_text(f"{r1.returncode}\n")
r2 = subprocess.run([sys.executable, "-m", "pytest", "test_review22_scoring.py", "-q", "-p", "no:cacheprovider", f"--junitxml={out / 'REVIEW22-REGRESSIONS.xml'}"],
                    cwd=str(out), capture_output=True, text=True, env=env)
(out / "REVIEW22-REGRESSIONS.log").write_text(r2.stdout + r2.stderr, encoding="utf-8")
(out / "REVIEW22-REGRESSIONS.exit").write_text(f"{r2.returncode}\n")
(out / "RUN.json").write_text(json.dumps({"harness": harness, "v4": True, "reviewer_sha256": SHA, "substitutions": subs + [("test: " + a, b) for a, b in tsubs],
                                          "probes_exit": r1.returncode, "regressions_exit": r2.returncode}, indent=1) + "\n", encoding="utf-8")
print("probes exit", r1.returncode, "| regressions exit", r2.returncode, "|", (r2.stdout.strip().splitlines() or [""])[-1])
