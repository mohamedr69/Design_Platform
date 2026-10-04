"""Assemble docs/milestones/M2/real-project-pilot/review22/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json. Run outputs are copied without the captured crop images (io.jsonl keeps every prompt,
answer and image hash)."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review22")
H = R / "harness-v4"
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review22")
DRY = pathlib.Path("C:/t/r2x/dry-runs/r22")
PROBES = pathlib.Path("C:/t/r2x/dry-runs/r22-probes")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")
SKIP_PARTS = ("__pycache__", ".pytest_cache", "io")          # io/: the PNG crops (hashes are in io.jsonl)


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst, *, skip=SKIP_PARTS, only=None):
    for p in sorted(pathlib.Path(src).rglob("*")):
        rel = p.relative_to(src)
        if p.is_file() and not any(part in skip for part in rel.parts) and (only is None or p.suffix in only):
            cp(p, f"{dst}/{rel.as_posix()}")


for f in ("CORRECTION-REPORT.md", "CHANGE-MAP.md", "STATUS.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
cptree(H, "harness-v4", skip=SKIP_PARTS)
cptree(R / "harness-r21", "harness-r21-submitted", skip=SKIP_PARTS)
cptree(R / "repro", "repro", skip=SKIP_PARTS + ("reviewer-copy", "score-control", "score-mismatch"))
for d in ("on-r21", "on-v4"):                                   # the scorer outputs of the reviewer's two main() calls
    cptree(R / "repro" / d / "score-control", f"repro/{d}/score-control")
    cptree(R / "repro" / d / "score-mismatch", f"repro/{d}/score-mismatch")
for d in ("bindings", "labels-dry-r22", "workload", "replays", "h06-replay", "runner-evidence", "tests-out"):
    cptree(R / d, "tests" if d == "tests-out" else d)
cp(R / "R22-DECLARATION.draft.json", "declaration/R22-DECLARATION.draft.json")
cp("C:/t/r2x/r21-stage/R21-STAGE.json", "declaration/R21-STAGE.json")
cp("C:/t/iso/work/r2x/review21/R21-SAMPLE.json", "declaration/R21-SAMPLE.json")
cp(DRY / "R22-DECLARATION.dry.json", "dry/R22-DECLARATION.dry.json")
cp("C:/t/r2x/dry-runs/r22-stage/R22-DRY-STAGE.json", "dry/R22-DRY-STAGE.json")
cptree(DRY / "score", "dry/score")
for tag in ("r22dry-A", "r22dry-L1", "r22dry-L2", "r22dry-L3", "r22dry-L4"):
    cptree(DRY / "runs" / tag / "out", f"dry/runs/{tag}/out")
if (DRY / "runs/refusals").exists():
    cptree(DRY / "runs/refusals", "dry/runs/refusals")
for s in sorted(PROBES.iterdir()):
    if not s.is_dir():
        continue
    cptree(s / "logs", f"runner-evidence/scenarios/{s.name}/logs")
    for run in sorted((s / "runs").iterdir()):
        if run.name == "refusals":
            cptree(run, f"runner-evidence/scenarios/{s.name}/runs/refusals")
        elif run.name != "r22dry-A" and (run / "out").exists():
            cptree(run / "out", f"runner-evidence/scenarios/{s.name}/runs/{run.name}/out")
    if (s / "R22-DECLARATION.dry.json").exists():
        cp(s / "R22-DECLARATION.dry.json", f"runner-evidence/scenarios/{s.name}/R22-DECLARATION.dry.json")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review22", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
