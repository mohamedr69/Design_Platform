"""Review 10 package: evidence into review10/evidence; EVIDENCE-MANIFEST.json in the layout the reviewer's
verify_package.py reads (`files` relative to evidence/, `package_files` relative to review10/,
`candidate.changed_files_sha256_at_a34d3f8` relative to the frozen tree), plus the owner's Candidate C check."""
import hashlib
import json
import shutil
from pathlib import Path

W = Path("C:/t/iso/work/r10")
DOC = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review10")
EV = DOC / "evidence"
FROZEN = Path("C:/t/iso/frozen-r10/backend")
COPY = {
    "COMPATIBILITY-TABLE.md": W / "COMPATIBILITY-TABLE.md",
    "tests/test_m2_review10.py": FROZEN / "tests/test_m2_review10.py",
    "prior/before_fix_on_689d95e.txt": W / "prior/before_fix_on_689d95e.txt",
    "prior/review10_module_on_689d95e.txt": W / "prior/review10_module_on_689d95e.txt",
    "prior/r10__review10_module_on_689d95e.xml": W / "prior/r10__review10_module_on_689d95e.xml",
    "probes/association_probe_before.py": W / "probes/association_probe_before.py",
    "probes/association_probe_after.py": W / "probes/association_probe_after.py",
    "probes/before/association-probe-results.json": W / "probes/before/association-probe-results.json",
    "probes/after/association-probe-results.json": W / "probes/after/association-probe-results.json",
    "probes/probes_old_before.py": W / "probes/probes_old_before.py",
    "probes/probes_old_after.py": W / "probes/probes_old_after.py",
    "probes/old_before/probe-results.json": W / "probes/old_before/probe-results.json",
    "probes/old_after/probe-results.json": W / "probes/old_after/probe-results.json",
    "rescore/rescore9.py": W / "rescore9.py",
    "rescore/make_rescore9.py": W / "make_rescore9.py",
    "rescore/SUMMARY.json": W / "eval9/SUMMARY.json",
    "rescore/ASSOCIATIONS.json": W / "eval9/ASSOCIATIONS.json",
    "rescore/eval9_run.log": W / "eval9_run.log",
    "rescore/matched-AI-EV1.json": W / "eval9/matched-AI-EV1.json",
    "rescore/matched-AI-EV2.json": W / "eval9/matched-AI-EV2.json",
    "freeze/FREEZE-R10.json": W / "freeze/FREEZE-R10.json",
    "freeze/candidate-r10.diff": W / "freeze/candidate-r10.diff",
    "freeze/freeze_r10.py": W / "freeze_r10.py",
    "freeze/make_freeze_r10.py": W / "make_freeze_r10.py",
    "patches/er_patch_r10.py": W / "er_patch_r10.py",
    "patches/ev_patch9.py": W / "ev_patch9.py",
    "package_r10.py": W / "package_r10.py",
}
for sub in ("suite", "focused"):
    for f in sorted((W / sub).glob("*")) if (W / sub).exists() else []:
        COPY[f"{sub}/{f.name}"] = f
for rel, src in COPY.items():
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


freeze = json.loads((W / "freeze/FREEZE-R10.json").read_text(encoding="utf-8"))
owner = Path("C:/Users/moham/Desktop/dev/dev/ep-platform")
cfreeze = json.loads((owner / "docs/milestones/M2/real-project-pilot/review05/CANDIDATE-C-FREEZE.json").read_text(encoding="utf-8-sig"))
files = {str(p.relative_to(EV)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
         for p in sorted(EV.rglob("*")) if p.is_file() and p.name != "EVIDENCE-MANIFEST.json"}
package_files = {str(p.relative_to(DOC)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
                 for p in sorted(DOC.rglob("*")) if p.is_file() and EV not in p.parents}
manifest = {"package": "M2 Review 10 correction", "date": "2026-09-29",
            "candidate": {"commit": freeze["candidate_commit"], "repository": "C:/t/iso/ep-platform", "frozen_tree": "C:/t/iso/frozen-r10",
                          "base": freeze["base"], "commits_since_base": freeze["commits_since_base"],
                          "changed_files_sha256_at_a34d3f8": {p: v["sha256"] for p, v in freeze["changed_files"].items()}},
            "owner_candidate_c_freeze": {"files": len(cfreeze["source_sha256"]),
                                         "failures": [n for n, h in cfreeze["source_sha256"].items()
                                                      if (sha(owner / "backend" / n) if (owner / "backend" / n).exists() else None) != h]},
            "copied_from": {rel: str(src) for rel, src in COPY.items()}, "files": files, "package_files": package_files}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(files), "evidence files;", len(package_files), "package files;", sum(v["bytes"] for v in files.values()) // 1024, "KiB;",
      "Candidate C failures:", manifest["owner_candidate_c_freeze"]["failures"])
