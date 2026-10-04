"""Review 09 package: copy the evidence into review09/evidence and write EVIDENCE-MANIFEST.json in the layout the
reviewer's verify_package.py reads (`files` relative to evidence/, `candidate.changed_files_sha256_at_<commit>`
relative to the scratch repository root), plus the package files and the owner's Candidate C check."""
import hashlib
import json
import shutil
from pathlib import Path

W = Path("C:/t/iso/work/r9")
DOC = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review09")
EV = DOC / "evidence"
FROZEN = Path("C:/t/iso/frozen-r9/backend")
COPY = {
    "tests/test_m2_review09.py": FROZEN / "tests/test_m2_review09.py",
    "tests/test_m2_eval5.py": FROZEN / "tests/test_m2_eval5.py",
    "prior/before_fix_on_e02a8c1.txt": W / "prior/before_fix_on_e02a8c1.txt",
    "prior/review09_module_on_e02a8c1.txt": W / "prior/review09_module_on_e02a8c1.txt",
    "prior/r9__review09_module_on_e02a8c1.xml": W / "prior/r9__review09_module_on_e02a8c1.xml",
    "probes/probes_before.py": W / "probes/probes_before.py",
    "probes/probes_after.py": W / "probes/probes_after.py",
    "probes/before/probe-results.json": W / "probes/before/probe-results.json",
    "probes/before/summary.txt": W / "probes/before/summary.txt",
    "probes/after/probe-results.json": W / "probes/after/probe-results.json",
    "probes/after/summary.txt": W / "probes/after/summary.txt",
    "rescore/rescore8.py": W / "rescore8.py",
    "rescore/make_rescore8.py": W / "make_rescore8.py",
    "rescore/SUMMARY.json": W / "eval8/SUMMARY.json",
    "rescore/ASSOCIATIONS.json": W / "eval8/ASSOCIATIONS.json",
    "rescore/eval8_run.log": W / "eval8_run.log",
    "replay/replay_boq_headings.py": W / "replay_boq_headings.py",
    "replay/replay-boq-headings.json": W / "replay-boq-headings.json",
    "freeze/FREEZE-R9.json": W / "freeze/FREEZE-R9.json",
    "freeze/candidate-r9.diff": W / "freeze/candidate-r9.diff",
    "freeze/freeze_r9.py": W / "freeze_r9.py",
    "patches/er_patch_r9.py": W / "er_patch_r9.py",
    "patches/ev_patch8.py": W / "ev_patch8.py",
    "package_r9.py": W / "package_r9.py",
}
for f in sorted((W / "eval8").glob("matched-AI-EV*.json")):
    COPY[f"rescore/{f.name}"] = f
for sub in ("suite", "focused"):
    for f in sorted((W / sub).glob("*")) if (W / sub).exists() else []:
        COPY[f"{sub}/{f.name}"] = f
for rel, src in COPY.items():
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


freeze = json.loads((W / "freeze/FREEZE-R9.json").read_text(encoding="utf-8"))
owner = Path("C:/Users/moham/Desktop/dev/dev/ep-platform")
cfreeze = json.loads((owner / "docs/milestones/M2/real-project-pilot/review05/CANDIDATE-C-FREEZE.json").read_text(encoding="utf-8-sig"))
files = {str(p.relative_to(EV)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
         for p in sorted(EV.rglob("*")) if p.is_file() and p.name != "EVIDENCE-MANIFEST.json"}
package_files = {str(p.relative_to(DOC)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
                 for p in sorted(DOC.rglob("*")) if p.is_file() and EV not in p.parents}
manifest = {"package": "M2 Review 09 correction", "date": "2026-09-29",
            "candidate": {"commit": freeze["candidate_commit"], "repository": "C:/t/iso/ep-platform", "base": freeze["base"],
                          "commits_since_base": freeze["commits_since_base"],
                          "changed_files_sha256_at_689d95e": {p: v["sha256"] for p, v in freeze["changed_files"].items()}},
            "owner_candidate_c_freeze": {"files": len(cfreeze["source_sha256"]),
                                         "failures": [n for n, h in cfreeze["source_sha256"].items()
                                                      if (sha(owner / "backend" / n) if (owner / "backend" / n).exists() else None) != h]},
            "copied_from": {rel: str(src) for rel, src in COPY.items()}, "files": files, "package_files": package_files}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(files), "evidence files;", len(package_files), "package files;", sum(v["bytes"] for v in files.values()) // 1024, "KiB;",
      "Candidate C failures:", manifest["owner_candidate_c_freeze"]["failures"])
