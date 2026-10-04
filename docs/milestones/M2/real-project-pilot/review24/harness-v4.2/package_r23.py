"""Assemble docs/milestones/M2/real-project-pilot/review23/ (NEW folder; earlier packages untouched) and write
evidence/EVIDENCE-MANIFEST.json. Run outputs are copied without the captured crop images (io.jsonl keeps every prompt,
answer and image hash)."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path("C:/t/iso/work/r2x/review23")
H = R / "harness-v4.1"
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review23")
PROBES = pathlib.Path("C:/t/r2x/dry-runs/r23-probes")
LIFE = pathlib.Path("C:/t/r2x/dry-runs/r23-lifecycle")
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
        if p.is_file() and not any(part in skip for part in rel.parts):
            cp(p, f"{dst}/{rel.as_posix()}")


for f in ("CORRECTION-REPORT.md", "LIFECYCLE-CONTRACT.md", "CHANGE-MAP.md", "STATUS.md", "COMMANDS.md"):
    cp(R / "pkg-src" / f, f)
cptree(H, "harness-v4.1")
cptree(R / "repro", "repro", skip=SKIP + ("reviewer-copy",))
cp(R / "repro/reviewer-copy/SHA256SUMS.txt", "repro/reviewer-copy-SHA256SUMS.txt")
for d in ("bindings", "runner-evidence", "lifecycle-evidence", "logs", "tests-out"):
    if (R / d).exists():
        cptree(R / d, "tests" if d == "tests-out" else d)
for base, dst in ((PROBES, "runner-evidence/scenarios"), (LIFE, "lifecycle-evidence/scenarios")):
    for s in sorted(base.iterdir()):
        if not s.is_dir():
            continue
        cptree(s / "logs", f"{dst}/{s.name}/logs")
        for extra in ("DECLARATION.json", "R22-DECLARATION.dry.json"):
            if (s / extra).exists():
                cp(s / extra, f"{dst}/{s.name}/{extra}")
        if (s / "labels").exists():
            cptree(s / "labels", f"{dst}/{s.name}/labels")
        for run in sorted((s / "runs").iterdir()):
            if run.name == "refusals":
                cptree(run, f"{dst}/{s.name}/runs/refusals")
            elif run.name != "r22dry-A" and (run / "out").exists():
                cptree(run / "out", f"{dst}/{s.name}/runs/{run.name}/out")
# the reviewer's probe workspaces (private sandboxes): manifests and logs only
for ws, dst in (("C:/t/r2x/dry-runs/r23-repro-v4", "repro/workspace-on-v4"), ("C:/t/r2x/dry-runs/r23-repro-v4.1", "repro/workspace-on-v4.1")):
    w = pathlib.Path(ws) / "critical-stop"
    if w.exists():
        cp(w / "DECLARATION.json", f"{dst}/DECLARATION.json")
        cptree(w / "labels", f"{dst}/labels")
        cptree(w / "runs/L1/out", f"{dst}/runs/L1/out")
        if (w / "runs/refusals").exists():
            cptree(w / "runs/refusals", f"{dst}/runs/refusals")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review23", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
