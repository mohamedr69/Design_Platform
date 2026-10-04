"""Run the Review 19 reviewer contracts (reviewer-copy/test_review19.py + efficiency_probes.py, byte copies, hash-checked)
against a chosen candidate tree, writing into THIS package's folder (never the reviewer's). The copy placed in <out_dir>
differs from the reviewer's only by these recorded substitutions in efficiency_probes.py:
  1. sys.path 'C:/t/iso/cand-ai2/backend' -> <tree>/backend
  2. (optional, --scorer) the score_cont.py whose `stop_of` is replayed -> <scorer> ; --metrics -> <metrics json>
Then pytest runs with JUnit output. Usage: run_reviewer_contracts.py <tree> <out_dir> [--scorer PATH] [--metrics PATH]"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

tree, out = sys.argv[1], pathlib.Path(sys.argv[2])
extra = dict(zip(sys.argv[3::2], sys.argv[4::2]))
src = pathlib.Path(__file__).parent / "reviewer-copy"
SHA = {"test_review19.py": "d48cf0d796684ce3e664880e0b0ede23c127b675eef86e6d8c9df0d88ce7882b",
       "efficiency_probes.py": "ef2efe704e04e82f59fe0d2f3b45699c3ec31cd4cbbd87aa234a1b5cbabbc4ca"}
for n, h in SHA.items():
    assert hashlib.sha256((src / n).read_bytes()).hexdigest() == h, n
out.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src / "test_review19.py", out / "test_review19.py")
shutil.copyfile(src / "pytest.ini", out / "pytest.ini")
probe = (src / "efficiency_probes.py").read_text(encoding="utf-8")
subs = [("'C:/t/iso/cand-ai2/backend'", repr(f"{tree}/backend"))]
if "--scorer" in extra:
    subs.append(("(PKG/'scripts/score_cont.py')", f"pathlib_Path({extra['--scorer']!r})"))
if "--metrics" in extra:
    subs.append(("(PKG/'results/CONT-METRICS.json')", f"pathlib_Path({extra['--metrics']!r})"))
for a, b in subs:
    assert probe.count(a) == 1, a
    probe = probe.replace(a, b)
probe = probe.replace("from pathlib import Path", "from pathlib import Path\nfrom pathlib import Path as pathlib_Path", 1)
(out / "efficiency_probes.py").write_text(probe, encoding="utf-8")
(out / "RUN.json").write_text(json.dumps({"tree": tree, "reviewer_sha256": SHA, "substitutions": subs}, indent=1) + "\n", encoding="utf-8")
py = sys.executable
r = subprocess.run([py, "-m", "pytest", "test_review19.py", "-q", "-p", "no:cacheprovider", f"--junitxml={out / 'REVIEW19-CONTRACTS.xml'}"],
                   cwd=str(out), capture_output=True, text=True, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
(out / "REVIEW19-CONTRACTS.log").write_text(r.stdout + r.stderr, encoding="utf-8")
(out / "REVIEW19-CONTRACTS.exit").write_text(f"{r.returncode}\n")
print("exit", r.returncode, "|", (r.stdout.strip().splitlines() or [""])[-1])
