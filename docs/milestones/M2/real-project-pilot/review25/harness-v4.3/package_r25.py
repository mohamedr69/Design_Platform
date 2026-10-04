"""Assemble docs/milestones/M2/real-project-pilot/review25/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json. Run outputs are copied without sandbox databases / caches / crop images (io.jsonl keeps
every prompt, answer and image hash; PROVIDER-OUTCOMES.jsonl and TERMINAL-STOP.json are copied as written)."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review25")
H = R / "harness-v4.3"
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review25")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")
SKIP = ("__pycache__", ".pytest_cache", "io", "db", "cache", "library", "uploads")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst, *, skip=SKIP):
    for p in sorted(pathlib.Path(src).rglob("*")):
        rel = p.relative_to(src)
        if p.is_file() and not any(part in skip for part in rel.parts) and not p.name.endswith((".sqlite", ".lock", ".tmp")):
            cp(p, f"{dst}/{rel.as_posix()}")


def scenario_roots(base, dst):
    for s in sorted(pathlib.Path(base).iterdir()):
        if not s.is_dir():
            continue
        if (s / "logs").exists():
            cptree(s / "logs", f"{dst}/{s.name}/logs")
        for extra in ("DECLARATION.json", "R22-DECLARATION.dry.json"):
            if (s / extra).exists():
                cp(s / extra, f"{dst}/{s.name}/{extra}")
        if (s / "labels").exists():
            cptree(s / "labels", f"{dst}/{s.name}/labels")
        runs = s / "runs"
        for run in sorted(runs.iterdir()) if runs.exists() else []:
            if run.name == "refusals":
                cptree(run, f"{dst}/{s.name}/runs/refusals")
            elif run.name != "r22dry-A" and (run / "out").exists():
                cptree(run / "out", f"{dst}/{s.name}/runs/{run.name}/out")


for f in ("CORRECTION-REPORT.md", "JOURNAL-KIND-OUTCOME-CONTRACT.md", "CHANGE-MAP.md", "STATUS.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
cptree(H, "harness-v4.3")
for d in ("on-v4.2", "on-v4.3", "r24-provider-probe-on-v4.3"):
    cptree(R / "repro" / d, f"repro/{d}")
cp(R / "repro/run_neutral_probe.py", "repro/run_neutral_probe.py")
cp("C:/t/iso/work/r2x/review24/repro/run_provider_probe.py", "repro/run_provider_probe.r24.py")
cp(R / "repro/reviewer-copy/SHA256SUMS.txt", "repro/reviewer-copy-SHA256SUMS.txt")
scenario_roots("C:/t/r2x/dry-runs/r25-repro-v4.2", "repro/scenarios-on-v4.2")
scenario_roots("C:/t/r2x/dry-runs/r25-repro-v4.3", "repro/scenarios-on-v4.3")
scenario_roots("C:/t/r2x/dry-runs/r25-r24probe-v4.3", "repro/scenarios-r24-provider-probe-on-v4.3")
for d in ("bindings", "neutral-evidence", "boundary-evidence", "lifecycle-evidence", "runner-evidence", "logs"):
    if (R / d).exists():
        cptree(R / d, d)
scenario_roots("C:/t/r2x/dry-runs/r25-neutral", "neutral-evidence/scenarios")
scenario_roots("C:/t/r2x/dry-runs/r25-boundary", "boundary-evidence/scenarios")
scenario_roots("C:/t/r2x/dry-runs/r25-lifecycle", "lifecycle-evidence/scenarios")
scenario_roots("C:/t/r2x/dry-runs/r25-probes", "runner-evidence/scenarios")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review25", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
