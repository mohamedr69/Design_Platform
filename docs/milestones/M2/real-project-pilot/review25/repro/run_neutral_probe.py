"""Run the reviewer's Review 25 neutral-kind probe and regressions (byte copies in reviewer-copy/, hash-checked) against a
chosen runner, in THIS package's own staging directory and a NEW private scenario root -- the reviewer's layout: the
reviewer's `neutral_kind_probe.py`, `lifecycle_probes_adapted.py`, `test_neutral_kind.py` and `pytest.ini` byte-identical,
beside the runner files of the harness under test (arm_ev.py, coverage_v4.py, score_arms_v4.py, dry_provider2.py,
xtrack2.py, provider_journal.py). Explicit environment adaptations: R23_LIFECYCLE_ROOT = the new scenario root (the
helper's documented override), TEMP / TMP = C:/t/iso/tmp, PYTHONDONTWRITEBYTECODE=1, every PILOT_DRY* / XTRACK_FAKE_NOW /
AI_EVIDENCE_* variable cleared from the parent environment. No code substitution.
Usage: run_neutral_probe.py <harness_dir> <stage_dir> <scenario_root>"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

harness, stage, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
src = pathlib.Path(__file__).parent / "reviewer-copy"
SHA = {"neutral_kind_probe.py": "c97707d4d4799785c136ecbb19c12d675370c840ac8e6c3985b63cb2602910e5",
       "test_neutral_kind.py": "896a1960ab083fe57348fe94e9351e517abbf28b95110046175ef391a79ab182",
       "lifecycle_probes_adapted.py": "1b1076bc6bbc33c34685b6be5279b303c2b306558b89e32317f19cc622e894d5"}
for n, h in SHA.items():
    assert hashlib.sha256((src / n).read_bytes()).hexdigest() == h, n
if stage.exists() or root.exists():
    sys.exit("stage dir / scenario root exist: never rerun in place")
stage.mkdir(parents=True)
for n in ("neutral_kind_probe.py", "test_neutral_kind.py", "lifecycle_probes_adapted.py", "pytest.ini"):
    shutil.copyfile(src / n, stage / n)
RUNNER = ("arm_ev.py", "coverage_v4.py", "score_arms_v4.py", "dry_provider2.py", "xtrack2.py", "provider_journal.py")
for n in RUNNER:
    shutil.copyfile(harness / n, stage / n)
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "R23_LIFECYCLE_ROOT": str(root), "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp", "PYTHONDONTWRITEBYTECODE": "1"}
for k in list(env):
    if k.startswith("AI_EVIDENCE_") or k.startswith("PILOT_DRY") or k == "XTRACK_FAKE_NOW":
        env.pop(k)
r1 = subprocess.run([sys.executable, "neutral_kind_probe.py"], cwd=str(stage), capture_output=True, text=True, env=env, timeout=1800)
(stage / "NEUTRAL-KIND-PROBE.log").write_text(r1.stdout + r1.stderr, encoding="utf-8")
(stage / "NEUTRAL-KIND-PROBE.exit").write_text(f"{r1.returncode}\n")
r2 = subprocess.run([sys.executable, "-m", "pytest", "test_neutral_kind.py", "-q", "-p", "no:cacheprovider", f"--junitxml={stage / 'NEUTRAL-REGRESSIONS.xml'}"],
                    cwd=str(stage), capture_output=True, text=True, env=env)
(stage / "NEUTRAL-REGRESSIONS.log").write_text(r2.stdout + r2.stderr, encoding="utf-8")
(stage / "NEUTRAL-REGRESSIONS.exit").write_text(f"{r2.returncode}\n")
(stage / "RUN.json").write_text(json.dumps({"harness": str(harness), "runner_files_sha256": {n: hashlib.sha256((harness / n).read_bytes()).hexdigest() for n in RUNNER},
                                            "scenario_root": str(root), "reviewer_sha256": SHA, "substitutions": "none (staged byte copies)",
                                            "environment": {"R23_LIFECYCLE_ROOT": str(root), "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp", "PYTHONDONTWRITEBYTECODE": "1", "cleared": "PILOT_DRY*, XTRACK_FAKE_NOW, AI_EVIDENCE_*"},
                                            "probe_exit": r1.returncode, "regressions_exit": r2.returncode}, indent=1) + "\n", encoding="utf-8")
print("probe exit", r1.returncode, "| regressions exit", r2.returncode, "|", (r2.stdout.strip().splitlines() or [""])[-1])
