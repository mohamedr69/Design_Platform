"""R43-44 (new): writes V5-BUILD-DIFF.md (once): every change of this package's scripts against the v4 scripts they were copied from
byte-identically (the copy record evidence/COPY-V4-SCRIPTS.sha256), as a per-file table and a unified diff, the new files, every line
that reads the ledger pin, and the run-time substitutions and work-folder helpers of task R43-44.
Usage: <bound python> -B make_v5_build_diff_r45q.py"""
from __future__ import annotations

import difflib
import pathlib
import re
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r42common as C  # noqa: E402

V4S = C.V4 / "scripts"
V5S = C.PACKAGE / "scripts"
RAN = {"build_declaration_r42.py": "show (twice), write", "diff_declaration_r42.py": "once (main_v5)",
       "preflight_r42.py": "twice with --upto 7 (attempt 1 refused by the lanes' isolation check on the launcher's R43_GUARD_ROOTS: evidence/preflight-attempt-1; attempt 2 is dry-run/PREFLIGHT-RESULTS.json)",
       "lane_env_check_r42.py": "by preflight_r42.py (step 6)", "dry_exercise_r42.py": "new-tag, single, finish-single",
       "runner_r43p.py": "by dry_exercise_r42.py", "r43p_base.py": "imported", "r42common.py": "imported", "demos_r42.py": "once",
       "snapshot_r43p.py": "before and after", "guard_probe_r43p.py": "once", "make_v5_build_diff_r45q.py": "once",
       "manifest_v5_r45q.py": "manifest, self-check 1 and 2", "guard/sitecustomize.py": "loaded by every package process (PYTHONPATH)"}
WHY = [
    "- `r42common.py`: the work folder r45q, the stamp `r32-v5`, the scope `m2-fresh-validation-r32-v5-2026-10-08`, the v5 package and file names, "
    "the review45 harness constants (`REVIEW45`, `HARNESS45`, `BINDING45`, `BINDING45_SHA`, `DRILL_CRITERION_SHA`; `HARNESS_GROUP` = "
    "`harness_r45_package`; `HARNESS42` = the review45 folder or the byte copy named by `R43_HARNESS_RUN`), `check_run_copy()` and "
    "`declared_here()` re-pointed to review45, the v4 record constants (`V4`, `V4_SHA`, `V4_MANIFEST_SHA`, `V4_SCOPE`, `V4_RUN_FOLDER`; "
    "`HARNESS43_GROUP` kept for the record), the task file R43-44. `LEDGER_EXPECTED` stays 484 / 18 / 0.",
    "- `build_declaration_r42.py`: `build_v5()` / `evidence_v5()` build v5 from the frozen v4 bytes (one re-point review43 -> review45 harness "
    "folder, the review45 manifest's hashes, the R43-44 items: stamp / folder / scope / pinned paths, supersedes and chain, corrected and added "
    "disclosures, the carried test exception, A-13 item 3 as history, `owner_decision_required`, the drill request-path coverage); `main()` "
    "checks the review45 group and the run copy, 484 / 18 / 0 with no v4 or v5 scope, no r32-v4 or r32-v5 folder, and calls `build_v5`; the "
    "owner procedures also refuse the v4 hash. `build_v4()` / `build()` kept, not called.",
    "- `diff_declaration_r42.py`: `main_v5()` (v4 -> v5, the same leaf categories with the review45 re-point and rebinding, the same protected "
    "list, the v4-identifier text check, the trees check and a new-identifier check) writes DECLARATION-DIFF-V4-V5.json/.md; `main_v4` kept.",
    "- `preflight_r42.py`: the review45 manifest and group and bound folder; `--upto 7` writes the results after step 7 (`finish_upto`): steps "
    "8-12 are not run (the card).",
    "- `dry_exercise_r42.py`: the review45 manifest, stamps `r45q-*`, `finish-single` (DRY-EXERCISE.json from the single run only).",
    "- `demos_r42.py`: stamps `r45q-*`, the review45 names. `create_scope_r42.py` (owner only; NOT run): the review45 manifest and group, the v5 "
    "pinned path in its text, the v4 hash refused too. `cli_version_drill_r42.py` (not run): the review45 manifest.",
    "- `guard/sitecustomize.py`: review45 and declaration-r32-v4 denied like the other frozen packages; default roots r45q and "
    "PILOT/declaration-r32-v5 (the v4 package is never a root).",
    "- `guard_probe_r43p.py`: probes for the v5 and the never-created v4 run folders, review45, declaration-r32-v4, the v5 package. "
    "`snapshot_r43p.py`: review45 and declaration-r32-v4 hashed; the executed v3 run folder by os.stat only (no file opened); v4/v5 scopes and "
    "folders.",
    "- New: `make_v5_build_diff_r45q.py` (this file), `manifest_v5_r45q.py` (BINDING-MANIFEST-R32-V5.json and its self-check; binds "
    "IMPLEMENTATION-REPORT.md, written before it).",
    "- Unchanged and still carrying v4 wording in docstrings only: `r43p_base.py`, `runner_r43p.py` (they use `C.WORK` / `C.DRY_BASE`, i.e. "
    "r45q), `make_v4_build_diff_r43p.py`, `manifest_v4_r43p.py`, `auth_test_exception_r43p.py` (not run; v4 records)."]
SUBS = [
    "- **S-RUN**: every package script ran from the byte copy `C:/t/r2x/r42-sandbox/r45q/run/v5` (re-synchronised and re-hashed against this "
    "package before every launch by the work helper `r45q/s/v5run.py`; record `r45q/o/RUN-COPY-V5.jsonl`); the harness from the byte copy "
    "`r45q/run/r45/scripts/harness-r32` of `PILOT/review45/scripts/harness-r32` (85 review45 script files copied, 0 differ; `R43_HARNESS_RUN`; "
    "`C.check_run_copy()` before every import).",
    "- **S-HERE**: `preflight_r32.HERE` = `PILOT/review45/scripts/harness-r32` in the build and preflight processes (`C.declared_here`).",
    "- **S-BASE**: dry and demonstration run folders under `C:/t/r2x/r42-sandbox/r45q/sb` (`r43p_base.redirect`, the calling process only).",
    "- **S-GUARD**: `PYTHONPATH` = the guard copy `r45q/run/v5/guard`; `R43_GUARD_LOG` = `r45q/guard-log`; `TEMP` / `TMP` = `r45q/tmp`; "
    "`R43_GUARD_ROOTS` not set (the guard's defaults r45q and this package); `R43_GUARD_OWNER_RECORDS=hash-only` only for the two snapshot "
    "processes. The guard probes ran with `R43_GUARD_ROOTS=r45q;<this package>` (the same roots). Preflight attempt 1 also had it set; the "
    "lanes' isolation check refused that variable (it names a path under the merged installation), so step 6 failed; the attempt is kept in "
    "`evidence/preflight-attempt-1/` and the variable was dropped for every later launch.",
    "- **S-ENV**: lane roots of the preflight's offline lane checks in `r45q/env-<lane>`.",
    "- **S-R45Q-1** (the drill reproduction only): `PILOT/review45/scripts` byte-copied to `r45q/run/r45/scripts` (85 files, 0 differ); in the "
    "copy of `r45/r45common.py` line 21 `WORK = SANDBOX_BASE / \"r45p\"` -> `\"r45q\"` (Verification 45's V45-S1 with r45q); "
    "`r45/r45_drill_run.py` and `r45/r45_launch.py` run unchanged with the review45 guard copy (roots r45q); the binding given was "
    "`PILOT/review45/BINDING-MANIFEST-R45-HARNESS.json` with `9af8e07a...9ffb` (evidence/drill-v5/RUN-COPY-AND-SUBSTITUTIONS.json).",
    "- **Dry exercise trim record**: the single phase trimmed its staged PDF copies, but the append to `r45q/out/TRIMMED.jsonl` failed (the "
    "folder did not exist) after the phase record was written; `r45q/out/TRIMMED-NOTE.json` records it; `finish-single` then ran normally.",
    "- Work helpers outside the package (not package scripts; under `r45q/s`): `logrow.py` (session-log rows), `patch_*.py` and "
    "`block_*.txt` (the edits listed in section 5), `v5run.py` (the launcher), `compare_drill.py` and `pack_drill.py` (the drill comparison and "
    "evidence copy), `difftest.py` (a dry test of the v5 diff on a scratch copy)."]


def files(root: pathlib.Path) -> dict:
    return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def main() -> int:
    out = C.PACKAGE / "V5-BUILD-DIFF.md"
    if out.exists():
        raise SystemExit("refused: V5-BUILD-DIFF.md is written once")
    old, new = files(V4S), files(V5S)
    rec = (C.PACKAGE / "evidence/COPY-V4-SCRIPTS.sha256").read_text(encoding="utf-8")
    rows, diffs, ledger_lines = [], [], []
    for rel in sorted(set(old) | set(new)):
        o, n = old.get(rel), new.get(rel)
        so, sn = (C.sha256_file(o) if o else None), (C.sha256_file(n) if n else None)
        state = "new" if not o else "removed" if not n else "unchanged" if so == sn else "changed"
        added = removed = 0
        if state == "changed":
            a = o.read_text(encoding="utf-8").split("\n")
            b = n.read_text(encoding="utf-8").split("\n")
            d = list(difflib.unified_diff(a, b, f"declaration-r32-v4/scripts/{rel}", f"declaration-r32-v5/scripts/{rel}", n=1, lineterm=""))
            added = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
            removed = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
            diffs.append((rel, d))
        rows.append((rel, state, so, sn, added, removed, RAN.get(rel, "not run by this task")))
        if n and rel.endswith(".py"):
            for i, line in enumerate(n.read_text(encoding="utf-8").split("\n"), 1):
                if re.search(r"LEDGER_EXPECTED|484 / 18 / 0", line):
                    ledger_lines.append((rel, i, line.strip()))
    copied_ok = all(f"*./{rel}" in rec for rel in old)
    L = ["# V5-BUILD-DIFF: the v5 package scripts against the v4 scripts they were copied from (task R43-44)", "",
         "Every v4 script (`PILOT/declaration-r32-v4/scripts/`, 34 files) was first copied byte-identically into `scripts/` of this package "
         "(`evidence/COPY-V4-SCRIPTS.sha256`, checked equal to the v4 files at the copy: 0 differ) and then changed only where listed below. "
         "Nothing in the review45 or review43 harness, review42, or declaration-r32-v2/v3/v4 was changed. It authorizes nothing.", "",
         f"- Copy record covers every v4 script: {copied_ok}.",
         f"- Files: {sum(1 for r in rows if r[1] == 'unchanged')} unchanged, {sum(1 for r in rows if r[1] == 'changed')} changed, "
         f"{sum(1 for r in rows if r[1] == 'new')} new, {sum(1 for r in rows if r[1] == 'removed')} removed.", "",
         "## 1. Per file", "", "| file | state | v4 sha256 | v5 sha256 | +lines | -lines | run by this task |", "|---|---|---|---|---|---|---|"]
    for rel, state, so, sn, a, r, ran in rows:
        L.append(f"| `{rel}` | {state} | `{(so or '-')[:16]}` | `{(sn or '-')[:16]}` | {a} | {r} | {ran} |")
    L += ["", "## 2. What each change answers", ""] + WHY
    L += ["", "## 3. Ledger-baseline lines (every line of the v5 scripts that names or reads the pin; unchanged at 484 / 18 / 0)", "",
          "| file | line | text |", "|---|---|---|"]
    L += [f"| `{rel}` | {i} | `{line[:160].replace('|', '/')}` |" for rel, i, line in ledger_lines]
    L += ["", "## 4. Run-time substitutions and work helpers of this task (no package file changed by them)", ""] + SUBS
    L += ["", "## 5. Unified diffs (v4 -> v5)", ""]
    for rel, d in diffs:
        L += [f"### `{rel}`", "", "```diff"] + d + ["```", ""]
    C.write_once(out, "\n".join(L) + "\n")
    print({"written": out.as_posix(), "changed": len(diffs), "new": sum(1 for r in rows if r[1] == "new"), "ledger_lines": len(ledger_lines),
           "copy_record_covers_v4": copied_ok})
    return 0


if __name__ == "__main__":
    sys.exit(main())
