"""ORCH-08 (R38HARNESS-IMPL): assemble the package PILOT/review38/ from the work folder (copies only; nothing is deleted).

Usage: assemble_review38.py
  scripts/harness-r32/        the frozen r38 harness (byte copies of WORK/harness-r32; must equal out/FREEZE-1.sha256)
  scripts/                    this task's scripts, the pytest guard plugin, the two parity-script copies
  tests/                      the junit XML of the full run (out/tests-1), the guard reports and SUMMARY.json
  top level                   CHANGE-RECORD.md, SCORER-CHANGES.md, LIVE-RUN-CONTRACT.md, COMMANDS.md, COMMANDS-AND-AUDIT-LOG.md,
                              REPORT-TEMPLATE.md (rendered by score_bcr_r32.report_template), PROJECT-REQUEST-BOUNDS.json,
                              CROSS-PAGE-WHATIF.json, VISIBILITY-REPORT.md, VISIBILITY-RESULT.json
  evidence/                   SNAPSHOT-BEFORE.json, COPY-RECORD.json (the review36 base copy), PARITY-COPY-RECORD.json,
                              HARNESS-DIFF-R36-R38.patch, HARNESS-FILES-R36-R38.json, FREEZE-1.sha256, WHATIF-PASSES.json,
                              PROGRESS.md (the work folder's status file, copied)
Writes only under PILOT/review38/."""
import hashlib
import json
import pathlib
import shutil
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
WORK = pathlib.Path("C:/t/iso/work/r2x/r38")
PKG = PILOT / "review38"
R36_MANIFEST = (PILOT / "review36" / "evidence" / "EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0")


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def copy(src, dst):
    dst = pathlib.Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    if sha(src) != sha(dst):
        raise SystemExit(f"copy differs: {src}")


def main():
    freeze = dict(line.split(" ", 1)[::-1] for line in (WORK / "out" / "FREEZE-1.sha256").read_text(encoding="utf-8").splitlines() if line.strip())
    freeze = {k.strip(): v for k, v in freeze.items()}
    for p in sorted((WORK / "harness-r32").iterdir()):
        if freeze.get(p.name) != sha(p):
            raise SystemExit(f"refused: {p.name} changed after FREEZE-1")
        copy(p, PKG / "scripts" / "harness-r32" / p.name)
    for p in sorted((WORK / "scripts").glob("*.py")):
        copy(p, PKG / "scripts" / p.name)
    copy(WORK / "scripts" / "pytest-plugins" / "r38_write_guard.py", PKG / "scripts" / "pytest-plugins" / "r38_write_guard.py")
    for side in ("r36", "r38"):
        for n in ("common_r35.py", "run_evaluator_offline_r32.py"):
            copy(WORK / "parity" / f"{side}-side" / "scripts" / n, PKG / "scripts" / "parity-r38" / f"{side}-side" / n)
    t = WORK / "out" / "tests-1"
    for p in sorted(t.glob("*.xml")) + [t / "SUMMARY.json"]:
        copy(p, PKG / "tests" / p.name)
    for p in sorted((t / "guard").glob("*.json")):
        copy(p, PKG / "tests" / "guard" / p.name)
    for n in ("CHANGE-RECORD.md", "SCORER-CHANGES.md", "LIVE-RUN-CONTRACT.md", "COMMANDS.md"):
        copy(WORK / "docs" / n, PKG / n)
    copy(WORK / "AUDIT-LOG.md", PKG / "COMMANDS-AND-AUDIT-LOG.md")
    for n in ("PROJECT-REQUEST-BOUNDS.json", "CROSS-PAGE-WHATIF.json", "VISIBILITY-REPORT.md", "VISIBILITY-RESULT.json"):
        copy(WORK / "out" / n, PKG / n)
    sys.path.insert(0, str(WORK / "harness-r32"))
    import score_bcr_r32 as S
    head = ("# Report template (review38; A-09 point 5)\n\nEvery comparison report of the r38 harness carries the following text, rendered by "
            "`score_bcr_r32.report_template()` from the module constants `SCOPE_LIMITATIONS` and `NOT_CLAIMED` (every `SCORE-BCR-R32.json` also "
            "carries both fields; no argument of `evaluate` removes them).\n\n")
    (PKG / "REPORT-TEMPLATE.md").write_text(head + S.report_template({}), encoding="utf-8", newline="\n")
    for n in ("SNAPSHOT-BEFORE.json", "PARITY-COPY-RECORD.json", "HARNESS-DIFF-R36-R38.patch", "HARNESS-FILES-R36-R38.json"):
        copy(WORK / "evidence" / n, PKG / "evidence" / n)
    copy(WORK / "out" / "FREEZE-1.sha256", PKG / "evidence" / "FREEZE-1.sha256")
    copy(WORK / "PROGRESS.md", PKG / "evidence" / "PROGRESS.md")
    raw = R36_MANIFEST[0].read_bytes()
    if hashlib.sha256(raw).hexdigest() != R36_MANIFEST[1]:
        raise SystemExit("PACKET MISMATCH: review36 manifest")
    man = json.loads(raw.decode("utf-8"))["files"]
    base = {p.name: {"copy": p.as_posix(), "sha256": sha(p), "review36_manifest_sha256": man[f"scripts/harness-r32/{p.name}"]["sha256"],
                     "equal": sha(p) == man[f"scripts/harness-r32/{p.name}"]["sha256"]} for p in sorted((WORK / "harness-r36-base").iterdir())}
    (PKG / "evidence" / "COPY-RECORD.json").write_text(json.dumps({"source": "PILOT/review36/scripts/harness-r32", "copied_utc": "2026-10-03T18:26Z",
                                                                   "files": base, "all_equal": all(v["equal"] for v in base.values())},
                                                                  sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    passes = {n: {"path": (WORK / "parity" / s / "run" / n).as_posix(), "sha256": sha(WORK / "parity" / s / "run" / n),
                  "bytes": (WORK / "parity" / s / "run" / n).stat().st_size}
              for s, n in (("r36-side", "PASS-R36.json"), ("r38-side", "PASS-R38.json"), ("r38-side", "PASS-R38-NOSOURCE.json"))}
    (PKG / "evidence" / "WHATIF-PASSES.json").write_text(json.dumps({"note": "the three per-case pass files (about 31 MB each) stay in the work folder; their hashes "
                                                                              "are bound here and in CROSS-PAGE-WHATIF.json inputs", "passes": passes},
                                                                    sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"package": PKG.as_posix(), "files": sum(1 for p in PKG.rglob("*") if p.is_file())}))


if __name__ == "__main__":
    main()
