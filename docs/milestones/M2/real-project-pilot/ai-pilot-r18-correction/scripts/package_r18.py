"""Assemble the Review 18 correction / continuation package (a NEW folder; ai-accuracy-pilot and earlier packages are
not touched) and write evidence/EVIDENCE-MANIFEST.json."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
RUNS = pathlib.Path("C:/t/r2x/runs")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/ai-pilot-r18-correction")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
if PKG.exists():
    sys.exit("the package folder exists; it is never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


def cptree(src, dst, skip=()):
    src = pathlib.Path(src)
    for p in sorted(src.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and not any(s in p.as_posix() for s in skip):
            cp(p, f"{dst}/{p.relative_to(src).as_posix()}")


cp(R / "pkg-src/CORRECTION-AND-CONTINUATION-REPORT.md", "CORRECTION-AND-CONTINUATION-REPORT.md")
cp(R / "pkg-src/CHANGE-MAP.md", "CHANGE-MAP.md")
cptree(R / "pkg-src/candidate", "candidate")
for f in ("backend/app/ai/evidence_reader.py", "backend/tests/_keyed_provider.py", "backend/tests/_e_frame_shim.py", "backend/tests/test_ai_pilot_r18.py",
          "backend/tests/test_ai_pilot_2026_09_30.py", "backend/tests/test_evidence_reader_r7.py", "backend/tests/test_m2_review08.py", "backend/tests/test_m2_review10.py"):
    cp(f"C:/t/iso/cand-ai2/{f}", f"candidate/files/{f}")
for f in ("CONT-DECLARATION.json", "CONT-SHARES.json", "CONT-SHARES.sha256"):
    cp(R / f, f"declaration/{f}")
cp("C:/t/r2x/dry-runs/CONT-DECLARATION.dry.json", "declaration/dry-run/CONT-DECLARATION.dry.json")
cptree("C:/t/r2x/dry-runs/cont-score", "declaration/dry-run/score")
cp(R / "CONTINUATION-SAMPLE.json", "sample/CONTINUATION-SAMPLE.json")
cp("C:/t/r2x/cont-stage/CONT-STAGE.json", "sample/CONT-STAGE.json")
cptree(R / "labels-v2", "labels-v2")
cptree(R / "labels-continuation", "labels-continuation")
cptree(R / "label-renders", "labels-continuation/renders")
cptree(R / "probes", "probes")
cptree(R / "tests-out", "tests")
for d in ("rescore", "locator", "guard", "support", "results", "ledger", "logs"):
    cptree(R / d, d)
for tag in ("cont-A", "cont-S", "cont-T2"):
    cptree(RUNS / tag / "out", f"runs/{tag}/out")
    cptree(RUNS / tag / "db", f"runs/{tag}/db")
for f in ("patch_successor.py", "patch_successor_2.py", "patch_successor_3.py", "repair_tests.py", "labels_v2.py", "rescore_v2.py", "select_continuation.py",
          "label_view.py", "labels_continuation.py", "locator_eval.py", "locator_probe.py", "derive_runners.py", "cont_stage.py", "cont_a.py", "cont_shares.py",
          "cont_ev.py", "cont_boq.py", "declare_continuation.py", "score_cont.py", "guard_replay.py", "support_replay.py", "export_ledger.py",
          "package_r18.py", "verify_r18_package.py"):
    cp(R / f, f"scripts/{f}")
(PKG / "evidence").mkdir(parents=True, exist_ok=True)
rv = MR / "reviews/M2-review-18"
(PKG / "evidence/REVIEWER-FILES-SHA256.json").write_text(json.dumps({"folder": str(rv).replace("\\", "/"), "files": {
    p.name: sha(p) for p in sorted(rv.glob("*")) if p.is_file()}, "permission": sha(MR / "OWNER-AI-PERMISSION-ROUND2.md")}, indent=1) + "\n", encoding="utf-8")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*"))
       if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")}
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "ai-pilot-r18-correction", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 2), "MB")
