"""Assemble the review16 package (new folder) and write EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil

H = pathlib.Path("C:/t/iso/work/r2x/r16")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review16")
RV = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-16")
EV = PKG / "evidence"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
for p in sorted(H.rglob("*")):
    rel = p.relative_to(H).as_posix()
    if p.is_file() and not rel.startswith("baseline/") and "__pycache__" not in rel:
        dst = EV / "r16" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
for p in sorted((PKG.parent / "review15/evidence/historical").rglob("*")):
    if p.is_file():
        dst = EV / "historical" / p.relative_to(PKG.parent / "review15/evidence/historical")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
(EV / "reviewer").mkdir(parents=True, exist_ok=True)
(EV / "reviewer/REVIEWER-FILES-SHA256.json").write_text(json.dumps({"folder": str(RV).replace("\\", "/"), "files": {
    p.relative_to(RV).as_posix(): sha(p) for p in sorted(RV.glob("*")) if p.is_file()}}, indent=1) + "\n", encoding="utf-8")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review16", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
