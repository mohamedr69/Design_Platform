"""ORCH-08C (R39HARNESS-IMPL): assemble the package PILOT/review39/ from the work folder (copies only; nothing is deleted).

Usage: assemble_review39.py
  scripts/harness-r32/        the frozen r39 harness (byte copies of WORK/harness-r32; must equal out/FREEZE-1.sha256)
  scripts/                    this task's scripts and the pytest guard plugin
  tests/                      the junit XML of the full run (out/tests-1), the guard reports and SUMMARY.json
  top level                   CHANGE-RECORD-R39.md, SCORER-CHANGES.md (v4), LIVE-RUN-CONTRACT.md (v4), COMMANDS.md, REQUEST-PATHS.md,
                              MODEL-ID-EVIDENCE.md, COMMANDS-AND-AUDIT-LOG.md (the work folder's audit log), REPORT-TEMPLATE.md
                              (rendered by score_bcr_r32.report_template), and the outputs PROJECT-REQUEST-BOUNDS.json,
                              RESUME-INVOCATIONS-R39.json, REQUEST-PATHS-STATIC.json, MODEL-ID-EVIDENCE.json, DRAWINGS-AI-PROBE-R39.json,
                              UNREAD-PAGES-PROBE-R39.json, VISIBILITY-REPORT.md, VISIBILITY-RESULT.json
  evidence/                   SNAPSHOT-BEFORE.json, COPY-RECORD.json (the review38 base copy), HARNESS-DIFF-R38-R39.patch,
                              HARNESS-FILES-R38-R39.json, FREEZE-1.sha256, CARRIED-FROM-REVIEW38.json, PROGRESS.md
Writes only under PILOT/review39/."""
import hashlib
import json
import pathlib
import shutil
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
WORK = pathlib.Path("C:/t/iso/work/r2x/r39")
PKG = PILOT / "review39"
R38 = PILOT / "review38"
R38_MANIFEST = (R38 / "evidence" / "EVIDENCE-MANIFEST.json", "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9")
SUPERSEDED = {"LIVE-RUN-CONTRACT.md": "LIVE-RUN-CONTRACT.md (version 4)", "SCORER-CHANGES.md": "SCORER-CHANGES.md (version 4)",
              "PROJECT-REQUEST-BOUNDS.json": "PROJECT-REQUEST-BOUNDS.json (project-bounds-r39-2026-10-04.1)",
              "REPORT-TEMPLATE.md": "REPORT-TEMPLATE.md (re-rendered)", "VISIBILITY-REPORT.md": "VISIBILITY-REPORT.md (re-run, 17 scenarios)",
              "VISIBILITY-RESULT.json": "VISIBILITY-RESULT.json (re-run)", "COMMANDS.md": "COMMANDS.md", "BINDING-MANIFEST-R38.json": "BINDING-MANIFEST-R39.json"}
IN_FORCE = {"CROSS-PAGE-WHATIF.json": "in force, unchanged: rule CP-R38 is untouched; bound by hash in BINDING-MANIFEST-R39 (group review38)",
            "CHANGE-RECORD.md": "frozen review38 record; its section 11 claim on the reader's 8 is corrected in CHANGE-RECORD-R39.md section 2"}


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def copy(src, dst):
    dst = pathlib.Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    if sha(src) != sha(dst):
        raise SystemExit(f"copy differs: {src}")


def main():
    freeze = {}
    for line in (WORK / "out" / "FREEZE-1.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, n = line.split(" ", 1)
            freeze[n.strip().lstrip("*")] = h
    for p in sorted((WORK / "harness-r32").iterdir()):
        if p.is_dir():
            raise SystemExit(f"refused: a folder in the harness ({p.name})")
        if freeze.get(p.name) != sha(p):
            raise SystemExit(f"refused: {p.name} changed after FREEZE-1")
        copy(p, PKG / "scripts" / "harness-r32" / p.name)
    for p in sorted((WORK / "scripts").glob("*.py")):
        copy(p, PKG / "scripts" / p.name)
    copy(WORK / "scripts" / "pytest-plugins" / "r38_write_guard.py", PKG / "scripts" / "pytest-plugins" / "r38_write_guard.py")
    t = WORK / "out" / "tests-1"
    for p in sorted(t.glob("*.xml")) + [t / "SUMMARY.json"]:
        copy(p, PKG / "tests" / p.name)
    for p in sorted((t / "guard").glob("*.json")):
        copy(p, PKG / "tests" / "guard" / p.name)
    for n in ("CHANGE-RECORD-R39.md", "SCORER-CHANGES.md", "LIVE-RUN-CONTRACT.md", "COMMANDS.md", "REQUEST-PATHS.md", "MODEL-ID-EVIDENCE.md"):
        copy(WORK / "docs" / n, PKG / n)
    copy(WORK / "AUDIT-LOG.md", PKG / "COMMANDS-AND-AUDIT-LOG.md")
    for n in ("PROJECT-REQUEST-BOUNDS.json", "RESUME-INVOCATIONS-R39.json", "REQUEST-PATHS-STATIC.json", "MODEL-ID-EVIDENCE.json",
              "DRAWINGS-AI-PROBE-R39.json", "UNREAD-PAGES-PROBE-R39.json", "VISIBILITY-REPORT.md", "VISIBILITY-RESULT.json"):
        copy(WORK / "out" / n, PKG / n)
    sys.path.insert(0, str(WORK / "harness-r32"))
    import score_bcr_r32 as S
    head = ("# Report template (review39; A-09 point 5; owner ruling A-10)\n\nEvery comparison report of the r39 harness carries the following "
            "text, rendered by `score_bcr_r32.report_template()` from the module constants `SCOPE_LIMITATIONS`, `NOT_CLAIMED`, "
            "`DECISION_COVERAGE_GATE_DEFINITIONS` and `C_GE_R_DIAGNOSTIC_RULE` (every `SCORE-BCR-R32.json` also carries `scope_limitations`, "
            "`not_claimed`, `decision_coverage_gate`, the mandatory `decision_coverage_C_ge_R` and `unread_pages`; no argument of `evaluate` "
            "removes them). With a result, the C >= R section lists the state, both lanes' counts and every document page with missing coverage "
            "and its reasons; this blank rendering lists the fields every report states.\n\n")
    (PKG / "REPORT-TEMPLATE.md").write_text(head + S.report_template({}), encoding="utf-8", newline="\n")
    for n in ("SNAPSHOT-BEFORE.json", "HARNESS-DIFF-R38-R39.patch", "HARNESS-FILES-R38-R39.json"):
        copy(WORK / "evidence" / n, PKG / "evidence" / n)
    copy(WORK / "out" / "FREEZE-1.sha256", PKG / "evidence" / "FREEZE-1.sha256")
    copy(WORK / "PROGRESS.md", PKG / "evidence" / "PROGRESS.md")
    raw = R38_MANIFEST[0].read_bytes()
    if hashlib.sha256(raw).hexdigest() != R38_MANIFEST[1]:
        raise SystemExit("PACKET MISMATCH: review38 manifest")
    man = json.loads(raw.decode("utf-8"))["files"]
    base = {p.name: {"copy": p.as_posix(), "sha256": sha(p), "review38_manifest_sha256": man[f"scripts/harness-r32/{p.name}"]["sha256"],
                     "equal": sha(p) == man[f"scripts/harness-r32/{p.name}"]["sha256"]} for p in sorted((WORK / "harness-r38-base").iterdir())}
    (PKG / "evidence" / "COPY-RECORD.json").write_text(json.dumps({"source": "PILOT/review38/scripts/harness-r32", "copied_utc": "2026-10-04T09:01Z",
                                                                   "files": base, "all_equal": all(v["equal"] for v in base.values())},
                                                                  sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    table = json.loads((WORK / "evidence" / "HARNESS-FILES-R38-R39.json").read_text(encoding="utf-8"))["files"]
    carried = {}
    for rel, v in sorted(man.items()):
        rec = {"review38_sha256": v["sha256"], "bytes": v["bytes"]}
        if rel.startswith("scripts/harness-r32/"):
            n = rel.split("/")[-1]
            st = table[n]["status"]
            rec |= {"status": "re-issued unchanged (byte-identical)" if st == "unchanged" else "re-issued CHANGED (see HARNESS-FILES-R38-R39.json)",
                    "review39_path": rel, "review39_sha256": table[n]["r39_sha256"], "test_file": n.startswith("test_")}
        elif rel in SUPERSEDED:
            rec |= {"status": f"superseded by review39 {SUPERSEDED[rel]}"}
        elif rel in IN_FORCE:
            rec |= {"status": IN_FORCE[rel]}
        elif rel.startswith("tests/"):
            rec |= {"status": "superseded by review39 tests/ (the full suite re-run on the r39 harness)"}
        else:
            rec |= {"status": "not re-issued; stays in review38 under its manifest 07c2fb78... (bound by BINDING-MANIFEST-R39 group review38)"}
        carried[rel] = rec
    summary = {}
    for v in carried.values():
        summary[v["status"].split(" (")[0].split(";")[0]] = summary.get(v["status"].split(" (")[0].split(";")[0], 0) + 1
    (PKG / "evidence" / "CARRIED-FROM-REVIEW38.json").write_text(json.dumps({
        "review38_manifest_sha256": R38_MANIFEST[1], "files": carried, "summary": summary,
        "changed_tests": sorted(n for n, r in table.items() if n.startswith("test_") and r["status"] == "changed"),
        "unchanged_harness_files": sorted(n for n, r in table.items() if r["status"] == "unchanged"),
        "new_harness_files": sorted(n for n, r in table.items() if r["status"] == "new")}, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"package": PKG.as_posix(), "files": sum(1 for p in PKG.rglob("*") if p.is_file())}))


if __name__ == "__main__":
    main()
