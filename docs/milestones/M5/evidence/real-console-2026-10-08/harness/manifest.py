import hashlib
import json
import sys
from pathlib import Path

E = Path(sys.argv[1])


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


files = {p.relative_to(E).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
         for p in sorted(E.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
T = Path(r"C:\t\tmp\m5cad")
outputs = {}
for p in sorted((T / "uploads" / "EP-90880" / "redesign" / "runs").glob("*/redesign.dwg")):
    outputs[f"run copy {p.parent.name}/redesign.dwg (not saved by the console)"] = sha(p)
for p in sorted((T / "uploads" / "EP-90880" / "redesign").glob("*.dwg")):
    outputs[f"seeded earlier copy: {p.name}"] = sha(p)
p6 = T / "probe" / "p6 out dir (spaces)" / "whole copy (p6).dwg"
outputs["probe p6 -WBLOCK * copy (console-written)"] = sha(p6)
data = {
    "task": "ORCH-046 (U2-M5-REAL-AUTOCAD), OD-16 c, owner decision A-14 item 4",
    "date": "2026-10-08",
    "computer_name": "LAPTOP-IL4L4UAJ",
    "console": "DWG TrueView 2026 - English accoreconsole.exe 25.1.164.0.0 (W.164.0.0)",
    "profile": "/isolate m5cad C:\\t\\tmp\\m5cad\\profile",
    "code": "roadmap/u2 37350bc848f9e5ec97dcae0695f52719cc99b6b6 (byte copy, no edits)",
    "source": {"path": "G:/dev (2)/dev/ep-platform-merged/data/uploads/EP-30880/ifc/60de2a377daa.dwg",
               "sha256_before": "66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21",
               "sha256_after": "66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21",
               "unchanged": True},
    "outputs_sha256": outputs,
    "outputs_kept_outside_git": "C:/t/tmp/m5cad (DWGs retained as evidence only, not committed)",
    "verdicts": {"1": "NOT PROVABLE WITH THIS CONSOLE (proposed-not-drawn proven at script level)",
                 "2": "PROVEN in part (library missing block, real script error, marker absence, incomplete script); "
                      "NOT PROVABLE for in-drawing missing block, LISP error, count check, marker presence",
                 "3": "NOT PROVABLE (valid saved DWG); PROVEN (earlier copy stays downloadable)",
                 "4": "PROVEN at script time; NOT PROVABLE for a real -INSERT",
                 "5": "PROVEN (cancel, external console kill, worker kill publishes nothing; finding F1); "
                      ".part in publishing/ not exercised",
                 "6": "PROVEN",
                 "7": "PROVEN on local NTFS C: and G:"},
    "files": files,
}
(E / "MANIFEST.json").write_text(json.dumps(data, indent=1), encoding="utf-8", newline="\n")
print(len(files), "files;", data["files"]["M5-REAL-CONSOLE-VALIDATION.md"])
