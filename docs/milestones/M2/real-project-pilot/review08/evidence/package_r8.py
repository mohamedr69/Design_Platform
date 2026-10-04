"""Review 08 package: copy the evidence (scripts, results, tests, freeze, suite) into review08/evidence and write the
evidence manifest (SHA-256 of every file in the package, the packet included)."""
import hashlib
import json
import shutil
from pathlib import Path

R8 = Path("C:/t/iso/work/r8")
DOC = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review08")
EV = DOC / "evidence"
FROZEN = Path("C:/t/iso/frozen-r8/backend")
COPY = {
    "tests/test_m2_review08.py": FROZEN / "tests/test_m2_review08.py",
    "probes/probes_r8.py": R8 / "probes_r8.py",
    "probes/probe-results-r8.json": R8 / "probe-results-r8.json",
    "prior/review08_module_on_1455f8b.txt": R8 / "prior/review08_module_on_1455f8b.txt",
    "prior/r8__review08_module_on_1455f8b.xml": R8 / "prior/r8__review08_module_on_1455f8b.xml",
    "eval7/SUMMARY.json": R8 / "eval7/SUMMARY.json",
    "eval7/ORDER-ONLY-CHECK.json": R8 / "eval7/ORDER-ONLY-CHECK.json",
    "eval7/rescore7.py": R8 / "rescore7.py",
    "metrics/METRICS-R8.json": R8 / "METRICS-R8.json",
    "metrics/metrics_r8.py": R8 / "metrics_r8.py",
    "freeze/FREEZE-R8.json": R8 / "freeze/FREEZE-R8.json",
    "freeze/candidate-r8.diff": R8 / "freeze/candidate-r8.diff",
    "freeze/freeze_r8.py": R8 / "freeze_r8.py",
    "build_packet_v2.py": R8 / "build_packet_v2.py",
    "package_r8.py": R8 / "package_r8.py",
}
for name in ("er_patch9.py", "er_patch10.py", "er_patch11.py", "er_patch12.py", "er_patch13.py", "ledger_patch.py", "ledger_patch2.py",
             "ev_patch7.py", "test_patch_r7_lifecycle.py", "t08_patch1.py", "t08_patch2.py"):
    COPY[f"patches/{name}"] = R8 / name
for f in sorted((R8 / "suite").glob("*")):
    COPY[f"suite/{f.name}"] = f
for f in sorted((R8 / "focused").glob("*")) if (R8 / "focused").exists() else []:
    COPY[f"focused/{f.name}"] = f
for f in sorted((R8 / "eval7").glob("matched-*.json")):
    COPY[f"eval7/{f.name}"] = f

for rel, src in COPY.items():
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


freeze = json.loads((R8 / "freeze/FREEZE-R8.json").read_text(encoding="utf-8"))
owner = Path("C:/Users/moham/Desktop/dev/dev/ep-platform")
cfreeze = json.loads((owner / "docs/milestones/M2/real-project-pilot/review05/CANDIDATE-C-FREEZE.json").read_text(encoding="utf-8-sig"))
# same layout as review07's manifest (the reviewer's verify_package.py): `files` relative to this evidence folder,
# `candidate.changed_files_sha256_at_<commit>` relative to the scratch repository root
files = {str(p.relative_to(EV)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
         for p in sorted(EV.rglob("*")) if p.is_file() and p.name != "EVIDENCE-MANIFEST.json"}
package_files = {str(p.relative_to(DOC)).replace("\\", "/"): {"sha256": sha(p), "bytes": p.stat().st_size}
                 for p in sorted(DOC.rglob("*")) if p.is_file() and EV not in p.parents}
manifest = {"package": "M2 Review 08 correction", "date": "2026-09-29",
            "candidate": {"commit": freeze["candidate_commit"], "repository": "C:/t/iso/ep-platform", "parent": freeze["parent"],
                          "changed_files_sha256_at_e02a8c1": {p: v["sha256"] for p, v in freeze["changed_files"].items()}},
            "owner_candidate_c_freeze": {"files": len(cfreeze["source_sha256"]),
                                         "failures": [n for n, h in cfreeze["source_sha256"].items() if (sha(owner / "backend" / n) if (owner / "backend" / n).exists() else None) != h]},
            "copied_from": {rel: str(src) for rel, src in COPY.items()}, "files": files, "package_files": package_files}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(files), "evidence files;", len(package_files), "package files;", sum(v["bytes"] for v in files.values()) // 1024, "KiB evidence;",
      "Candidate C failures:", manifest["owner_candidate_c_freeze"]["failures"])
