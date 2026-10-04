"""Package the pilot deliverables under docs/milestones/M2/real-project-pilot/: copy the frozen files, labels, run
outputs (candidate A and B), scenarios, clone workflow, BOQ run, probes, test results and renders (JPEG), then write
RUN-MANIFEST.json with a sha256 of every file and the source identity of both candidates."""
import json, sys, pathlib, shutil, hashlib, datetime, subprocess, glob, os
from PIL import Image

S = pathlib.Path(sys.argv[1]); REPO = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform"); D = REPO / "docs" / "milestones" / "M2" / "real-project-pilot"
OUT = D / "outputs"; (OUT / "candidateA").mkdir(parents=True, exist_ok=True); (OUT / "candidateB").mkdir(exist_ok=True); (D / "inventory").mkdir(exist_ok=True); (D / "crops").mkdir(exist_ok=True)


def sha(p): h = hashlib.sha256(); h.update(pathlib.Path(p).read_bytes()); return h.hexdigest()


def cp(src, dst):
    dst = pathlib.Path(dst); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, dst); return dst


# frozen inputs and labels
for f in ("PROJECT-INVENTORY.json", "FROZEN-SAMPLE.json", "FROZEN-BOQ-SET.json", "GOLDEN-LABELS.json", "REPRODUCIBILITY.json"):
    cp(S / f, D / f if f != "REPRODUCIBILITY.json" else OUT / f)
for f in glob.glob(str(S / "inventory-EP-*.json")): cp(f, D / "inventory" / pathlib.Path(f).name)
# candidate A / B outputs
for f in ("RUN-default.json", "RUN-promoted.json", "rows-default.json", "rows-promoted.json", "ACCURACY.json", "per-document-default.json", "per-document-promoted.json", "run_sandbox_default.log", "run_sandbox_promoted.log"):
    cp(S / "candidateA" / f, OUT / "candidateA" / f); cp(S / f, OUT / "candidateB" / f)
for f in ("SCENARIOS2-default.json", "SCENARIOS2-promoted.json", "BOQ-RUN-default.json", "word_text.json"):
    cp(S / f, OUT / f)
for f in glob.glob(str(S / "clone_default" / "*")):
    if pathlib.Path(f).is_file() and not f.endswith("run_jobs.py"): cp(f, OUT / "clone_default" / pathlib.Path(f).name)
for f in glob.glob(str(S / "probe_r4" / "*")): cp(f, OUT / "probe_r4" / pathlib.Path(f).name)
for f, name in (("junit.xml", "full-suite-junit.xml"), ("submitted.xml", "submitted-set-junit.xml"), ("submitted.log", "submitted-set-pytest.log")):
    p = pathlib.Path("C:/t/m2r/pilot_suite") / f
    if p.is_file(): cp(p, OUT / "tests" / name)
# scripts (the pilot's own tooling, for reproduction)
for f in ("inventory.py", "sample.py", "crops2.py", "tb_sheets.py", "labels_skeleton.py", "assemble_labels.py", "word_text.py", "boq_set.py", "run_sandbox.py", "scenarios2.py", "clone_regression.py", "boq_sandbox.py", "score.py", "render_tables.py", "patch_r4_parser.py", "patch_pilot_defects.py", "reproducibility.py", "package.py"):
    if (S / f).is_file(): cp(S / f, OUT / "scripts" / f)
for f in glob.glob(str(S / "labels" / "*.json")): cp(f, OUT / "labels" / pathlib.Path(f).name)
for f in glob.glob(str(S / "boq_labels" / "*.json")): cp(f, OUT / "boq_labels" / pathlib.Path(f).name)
# renders as JPEG (contact sheets, title-block sheets, BOQ pages)
def jpeg(src, dst, q=55, max_w=None):
    im = Image.open(src).convert("RGB")
    if max_w and im.width > max_w: im.thumbnail((max_w, 100000))
    im.save(dst, "JPEG", quality=q, optimize=True)
for f in sorted(glob.glob(str(S / "crops" / "sheet-*.png"))): jpeg(f, D / "crops" / (pathlib.Path(f).stem + ".jpg"))
for f in sorted(glob.glob(str(S / "tb" / "tb-*.png"))): jpeg(f, D / "crops" / (pathlib.Path(f).stem + ".jpg"))
(D / "crops" / "boq").mkdir(exist_ok=True)
for f in sorted(glob.glob(str(S / "boq_pages" / "*.png"))): jpeg(f, D / "crops" / "boq" / (pathlib.Path(f).stem + ".jpg"), q=60)
cp(S / "crops" / "index.json", D / "crops" / "index.json"); cp(S / "tb" / "index.json", D / "crops" / "tb-index.json"); cp(S / "tiles.json", D / "crops" / "tiles.json")
# large evidence files (per-folder inventories, clone record dumps and snapshots) are stored gzipped
import gzip
for folder in (D / "inventory", OUT / "clone_default"):
    for f in list(folder.glob("*.json")):
        if f.stat().st_size > 1_000_000:
            with open(f, "rb") as src, gzip.open(str(f) + ".gz", "wb", compresslevel=6) as dst: shutil.copyfileobj(src, dst)
            f.unlink()
# source identity
def git(*a): return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()
sources = ["backend/app/services/document_control.py", "backend/app/services/document_sync.py", "backend/app/services/document_processing.py", "backend/app/services/design_sheet_extractor.py", "backend/app/services/transmittals.py", "backend/app/ai/sheet_reader.py", "backend/app/core/config.py", "backend/scripts/repair_extraction.py", "backend/tests/conftest.py", "backend/tests/test_extraction_pilot.py", "backend/tests/test_extraction_m2_review03.py", "backend/tests/test_extraction_m2_review02.py"]
files = {}
for p in sorted(D.rglob("*")):
    if p.is_file() and p.name != "RUN-MANIFEST.json":
        files[p.relative_to(D).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
repro = json.load(open(S / "REPRODUCIBILITY.json", encoding="utf-8"))
manifest = {"assembled_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "head": git("rev-parse", "HEAD"), "git_status": git("status", "--short").splitlines(),
            "candidate_A": {"parser_version": "parse-2026-09-28.4", "source_hashes": repro["source_hashes"], "note": "the frozen candidate: commit 2221b43 + the R4-01 closure (uncommitted); scored on all cohorts including the holdout before any pilot fix"},
            "candidate_B": {"parser_version": "parse-2026-09-28.5", "source_hashes": {s: sha(REPO / s) for s in sources if (REPO / s).is_file()}, "note": "candidate A + pilot fixes P-01..P-04 (backend/app/services/document_control.py) with backend/tests/test_extraction_pilot.py; rerun on the same frozen sample and labels"},
            "versions": repro["versions"], "budgets": repro["budgets"], "settings": repro["settings"], "python": repro["python"], "platform": repro["platform"], "dependencies": repro["dependencies"],
            "sandbox_roots": ["C:/t/pilot/db", "C:/t/pilot/cache", "C:/t/pilot/library", "C:/t/pilot/uploads", "C:/t/pilot/out", "C:/t/pilot/stage"],
            "runs": {"candidateA": {"default": json.load(open(S / "candidateA" / "RUN-default.json"))["at_utc"], "promoted": json.load(open(S / "candidateA" / "RUN-promoted.json"))["at_utc"]},
                     "candidateB": {"default": json.load(open(S / "RUN-default.json"))["at_utc"], "promoted": json.load(open(S / "RUN-promoted.json"))["at_utc"]},
                     "scenarios": {p: json.load(open(S / f"SCENARIOS2-{p}.json"))["at_utc"] for p in ("default", "promoted")},
                     "clone": json.load(open(S / "clone_default" / "clone_run.json"))["clone"]["at"], "boq": json.load(open(S / "BOQ-RUN-default.json"))["at_utc"],
                     "sample_frozen": json.load(open(S / "FROZEN-SAMPLE.json"))["at_utc"], "labels": json.load(open(S / "GOLDEN-LABELS.json"))["at_utc"]},
            "files": files}
json.dump(manifest, open(D / "RUN-MANIFEST.json", "w", encoding="utf-8"), indent=1)
total = sum(v["bytes"] for v in files.values())
print("files", len(files), "MB", round(total / 1e6, 1))
