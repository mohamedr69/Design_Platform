"""Review 12 package: evidence into review12/evidence; EVIDENCE-MANIFEST.json in the layout the reviewer's
verify_package.py reads (`files` relative to evidence/, `package_files` relative to review12/,
`candidate.changed_files_sha256_at_3d5607d` relative to the frozen tree), plus the owner's Candidate C check."""
import hashlib
import json
import shutil
from pathlib import Path

W = Path("C:/t/iso/work/r12")
DOC = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review12")
EV = DOC / "evidence"
FROZEN = Path("C:/t/iso/frozen-r12/backend")
COPY = {
    "COMPATIBILITY-EXPECTATIONS.md": W / "COMPATIBILITY-EXPECTATIONS.md",
    "tests/test_m2_review12.py": FROZEN / "tests/test_m2_review12.py",
    "tests/fixtures/evidence_reader_r11.py": FROZEN / "tests/fixtures/evidence_reader_r11.py",
    "prior/before_fix_on_a977364.txt": W / "prior/before_fix_on_a977364.txt",
    "prior/review12_module_on_a977364.txt": W / "prior/review12_module_on_a977364.txt",
    "prior/r12__review12_module_on_a977364.xml": W / "prior/r12__review12_module_on_a977364.xml",
    "rescore/rescore_r12.py": W / "rescore_r12.py",
    "rescore/make_rescore_r12.py": W / "make_rescore_r12.py",
    "rescore/SUMMARY.json": W / "eval9-reader7/SUMMARY.json",
    "rescore/ASSOCIATIONS.json": W / "eval9-reader7/ASSOCIATIONS.json",
    "rescore/rescore_run.log": W / "rescore_run.log",
    "freeze/FREEZE-R12.json": W / "freeze/FREEZE-R12.json",
    "freeze/candidate-r12.diff": W / "freeze/candidate-r12.diff",
    "freeze/freeze_r12.py": W / "freeze_r12.py",
    "freeze/make_freeze_r12.py": W / "make_freeze_r12.py",
    "patches/er_patch_r12.py": W / "er_patch_r12.py",
    "patches/er_patch_r12b.py": W / "er_patch_r12b.py",
    "package_r12.py": W / "package_r12.py",
    "verify/make_verify_r12.py": W / "make_verify_r12.py",
    "focused/modcounts.py": W / "modcounts.py",
}
for f in sorted((W / "probes").rglob("*")):
    if f.is_file():
        COPY["probes/" + str(f.relative_to(W / "probes")).replace("\\", "/")] = f
for sub in ("suite", "focused", "suite_analysis"):
    for f in sorted((W / sub).glob("*")) if (W / sub).exists() else []:
        COPY[f"{sub}/{f.name}"] = f
for rel, src in COPY.items():
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


freeze = json.loads((W / "freeze/FREEZE-R12.json").read_text(encoding="utf-8"))
owner = Path("C:/Users/moham/Desktop/dev/dev/ep-platform")
cfreeze = json.loads((owner / "docs/milestones/M2/real-project-pilot/review05/CANDIDATE-C-FREEZE.json").read_text(encoding="utf-8-sig"))
files = {str(p.relative_to(EV)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
         for p in sorted(EV.rglob("*")) if p.is_file() and p.name != "EVIDENCE-MANIFEST.json"}
package_files = {str(p.relative_to(DOC)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
                 for p in sorted(DOC.rglob("*")) if p.is_file() and EV not in p.parents}
manifest = {"package": "M2 Review 12 correction", "date": "2026-09-29",
            "candidate": {"commit": freeze["candidate_commit"], "repository": "C:/t/iso/ep-platform", "frozen_tree": "C:/t/iso/frozen-r12",
                          "base": freeze["base"], "commits_since_base": freeze["commits_since_base"],
                          "changed_files_sha256_at_3d5607d": {p: v["sha256"] for p, v in freeze["changed_files"].items()}},
            "owner_candidate_c_freeze": {"files": len(cfreeze["source_sha256"]),
                                         "failures": [n for n, h in cfreeze["source_sha256"].items()
                                                      if (sha(owner / "backend" / n) if (owner / "backend" / n).exists() else None) != h]},
            "copied_from": {rel: str(src) for rel, src in COPY.items()}, "files": files, "package_files": package_files}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(files), "evidence files;", len(package_files), "package files;", sum(v["bytes"] for v in files.values()) // 1024, "KiB;",
      "Candidate C failures:", manifest["owner_candidate_c_freeze"]["failures"])
