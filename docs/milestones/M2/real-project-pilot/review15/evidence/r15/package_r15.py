"""Assemble the review15 package (new folder; earlier packages untouched) and write EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil

H = pathlib.Path("C:/t/iso/work/r2x/r15")
W = pathlib.Path("C:/t/iso/work/r2x")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review15")
R14 = PKG.parent / "review14"
RV = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-15")
EV = PKG / "evidence"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def put(src, rel):
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


for p in sorted(H.glob("*.py")) + sorted((H / "tests").glob("*.py")) + sorted((H / "dev").glob("*")) + sorted((H / "diff").glob("*")) + \
        sorted((H / "regression").glob("*")):
    put(p, f"r15/{p.relative_to(H).as_posix()}")
for n in ("FREEZE-R15.json", "REPLAY-BOQ-r15.json", "REPLAY-BOQ-r15-geometry.json", "R15-SAVED-OUTPUT-CHECK.json"):
    put(H / n, f"r15/{n}")
for p in sorted((H / "probes").glob("*")):
    if p.is_file():
        put(p, f"r15/probes/{p.name}")
for d in ("out-submitted", "out-corrected", "final-submitted", "final-corrected"):
    put(H / "probes" / d / "PROBE-RESULTS.json", f"r15/probes/{d}/PROBE-RESULTS.json")
put(W / "labels/r15/SMALL-BATCH-LABELS.amended-r15.1.json", "labels/r15/SMALL-BATCH-LABELS.amended-r15.1.json")
# historical: byte-identical re-copies from the Review 14 package (the stored runs and the deviation marker)
for p in sorted((R14 / "evidence/historical").rglob("*")):
    if p.is_file():
        put(p, f"historical/{p.relative_to(R14 / 'evidence/historical').as_posix()}")
(EV / "reviewer").mkdir(parents=True, exist_ok=True)
(EV / "reviewer/REVIEWER-FILES-SHA256.json").write_text(json.dumps({"folder": str(RV).replace("\\", "/"), "files": {
    p.relative_to(RV).as_posix(): sha(p) for p in sorted(RV.rglob("*")) if p.is_file() and "probe-" not in p.parts[-2]}}, indent=1) + "\n", encoding="utf-8")
man = {}
for p in sorted(PKG.rglob("*")):
    if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json"):
        man[p.relative_to(PKG).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review15", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
