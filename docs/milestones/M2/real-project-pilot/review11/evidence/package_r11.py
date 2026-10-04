"""Review 11 package: evidence into review11/evidence; EVIDENCE-MANIFEST.json in the layout the reviewer's
verify_package.py reads (`files` relative to evidence/, `package_files` relative to review11/,
`candidate.changed_files_sha256_at_a977364` relative to the frozen tree), plus the owner's Candidate C check."""
import hashlib
import json
import shutil
from pathlib import Path

W = Path("C:/t/iso/work/r11")
DOC = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review11")
EV = DOC / "evidence"
FROZEN = Path("C:/t/iso/frozen-r11/backend")
COPY = {
    "tests/test_m2_review11.py": FROZEN / "tests/test_m2_review11.py",
    "tests/fixtures/evidence_reader_r10.py": FROZEN / "tests/fixtures/evidence_reader_r10.py",
    "prior/before_fix_on_a34d3f8.txt": W / "prior/before_fix_on_a34d3f8.txt",
    "prior/review11_module_on_a34d3f8.txt": W / "prior/review11_module_on_a34d3f8.txt",
    "prior/r11__review11_module_on_a34d3f8.xml": W / "prior/r11__review11_module_on_a34d3f8.xml",
    "rescore/rescore_r11.py": W / "rescore_r11.py",
    "rescore/make_rescore10.py": W / "make_rescore10.py",
    "rescore/SUMMARY.json": W / "eval9-reader6/SUMMARY.json",
    "rescore/ASSOCIATIONS.json": W / "eval9-reader6/ASSOCIATIONS.json",
    "rescore/rescore_run.log": W / "rescore_run.log",
    "freeze/FREEZE-R11.json": W / "freeze/FREEZE-R11.json",
    "freeze/candidate-r11.diff": W / "freeze/candidate-r11.diff",
    "freeze/freeze_r11.py": W / "freeze_r11.py",
    "freeze/make_freeze_r11.py": W / "make_freeze_r11.py",
    "patches/er_patch_r11.py": W / "er_patch_r11.py",
    "package_r11.py": W / "package_r11.py",
    "verify/make_verify_r11.py": W / "make_verify_r11.py",
    "focused/modcounts.py": W / "modcounts.py",
}
for f in sorted((W / "probes").rglob("*")):
    if f.is_file():
        COPY["probes/" + str(f.relative_to(W / "probes")).replace("\\", "/")] = f
for sub in ("suite", "focused", "investigation"):
    for f in sorted((W / sub).glob("*")) if (W / sub).exists() else []:
        COPY[f"{sub}/{f.name}"] = f
for rel, src in COPY.items():
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


freeze = json.loads((W / "freeze/FREEZE-R11.json").read_text(encoding="utf-8"))
owner = Path("C:/Users/moham/Desktop/dev/dev/ep-platform")
cfreeze = json.loads((owner / "docs/milestones/M2/real-project-pilot/review05/CANDIDATE-C-FREEZE.json").read_text(encoding="utf-8-sig"))
files = {str(p.relative_to(EV)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
         for p in sorted(EV.rglob("*")) if p.is_file() and p.name != "EVIDENCE-MANIFEST.json"}
package_files = {str(p.relative_to(DOC)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
                 for p in sorted(DOC.rglob("*")) if p.is_file() and EV not in p.parents}
manifest = {"package": "M2 Review 11 correction", "date": "2026-09-29",
            "candidate": {"commit": freeze["candidate_commit"], "repository": "C:/t/iso/ep-platform", "frozen_tree": "C:/t/iso/frozen-r11",
                          "base": freeze["base"], "commits_since_base": freeze["commits_since_base"],
                          "changed_files_sha256_at_a977364": {p: v["sha256"] for p, v in freeze["changed_files"].items()}},
            "owner_candidate_c_freeze": {"files": len(cfreeze["source_sha256"]),
                                         "failures": [n for n, h in cfreeze["source_sha256"].items()
                                                      if (sha(owner / "backend" / n) if (owner / "backend" / n).exists() else None) != h]},
            "copied_from": {rel: str(src) for rel, src in COPY.items()}, "files": files, "package_files": package_files}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(files), "evidence files;", len(package_files), "package files;", sum(v["bytes"] for v in files.values()) // 1024, "KiB;",
      "Candidate C failures:", manifest["owner_candidate_c_freeze"]["failures"])
