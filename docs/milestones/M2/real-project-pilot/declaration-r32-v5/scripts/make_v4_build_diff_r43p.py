"""R43-40 (new): writes V4-BUILD-DIFF.md (once): every change of this package's scripts against the v3 scripts they were copied
from byte-identically (the copy record evidence/COPY-V3-SCRIPTS.sha256), as a per-file table and a unified diff, the new
files, every line that reads the ledger pin (R43V-04), and the run-time substitutions of this task.
Usage: <bound python> -B make_v4_build_diff_r43p.py"""
from __future__ import annotations

import difflib
import pathlib
import re
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r42common as C  # noqa: E402

V3S = C.V3 / "scripts"
V4S = C.PACKAGE / "scripts"
RAN = {"build_declaration_r42.py": "show, write", "diff_declaration_r42.py": "once", "preflight_r42.py": "once (with lane_env_check_r42.py and create_scope_r42.py preview / create-refused as its children)",
       "dry_exercise_r42.py": "new-tag, single, split, loops, xproject, cli (cli_version_drill_r42.py), finish", "demos_r42.py": "once",
       "lane_env_check_r42.py": "by preflight_r42.py", "create_scope_r42.py": "preview and create-refused, by preflight_r42.py",
       "cli_version_drill_r42.py": "by dry_exercise_r42.py cli", "runner_r43p.py": "by dry_exercise_r42.py", "r43p_base.py": "imported",
       "r42common.py": "imported", "snapshot_r43p.py": "before and after", "guard_probe_r43p.py": "once", "make_v4_build_diff_r43p.py": "once",
       "manifest_v4_r43p.py": "manifest, self-check", "auth_test_exception_r43p.py": "once", "guard/sitecustomize.py": "loaded by every process (PYTHONPATH)"}


def files(root: pathlib.Path) -> dict:
    return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def main() -> int:
    out = C.PACKAGE / "V4-BUILD-DIFF.md"
    if out.exists():
        raise SystemExit("refused: V4-BUILD-DIFF.md is written once")
    old, new = files(V3S), files(V4S)
    rec = (C.PACKAGE / "evidence/COPY-V3-SCRIPTS.sha256").read_text(encoding="utf-8")
    rows, diffs, ledger_lines = [], [], []
    for rel in sorted(set(old) | set(new)):
        o, n = old.get(rel), new.get(rel)
        so, sn = (C.sha256_file(o) if o else None), (C.sha256_file(n) if n else None)
        state = "new" if not o else "removed" if not n else "unchanged" if so == sn else "changed"
        added = removed = 0
        if state == "changed":
            a = o.read_text(encoding="utf-8").split("\n")
            b = n.read_text(encoding="utf-8").split("\n")
            d = list(difflib.unified_diff(a, b, f"declaration-r32-v3/scripts/{rel}", f"declaration-r32-v4/scripts/{rel}", n=1, lineterm=""))
            added = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
            removed = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
            diffs.append((rel, d))
        rows.append((rel, state, so, sn, added, removed, RAN.get(rel, "not run by this task")))
        if n and rel.endswith(".py"):
            for i, line in enumerate(n.read_text(encoding="utf-8").split("\n"), 1):
                if re.search(r"LEDGER_EXPECTED|\(483, 17, 0\)|483 / 17 / 0|484 / 18 / 0", line):
                    ledger_lines.append((rel, i, line.strip()))
    copied_ok = all(f"./{rel}" in rec or rel in rec for rel in old)
    L = ["# V4-BUILD-DIFF: the v4 package scripts against the v3 scripts they were copied from (task R43-40)", "",
         "Every v3 script (`PILOT/declaration-r32-v3/scripts/`, 27 files) was first copied byte-identically into `scripts/` of this package "
         "(`evidence/COPY-V3-SCRIPTS.sha256`, checked equal to the v3 files at the copy) and then changed only where listed below. Nothing in "
         "the review43 harness, review42, review43 or declaration-r32-v3 was changed. It authorizes nothing.", "",
         f"- Copy record covers every v3 script: {copied_ok}.",
         f"- Files: {sum(1 for r in rows if r[1] == 'unchanged')} unchanged, {sum(1 for r in rows if r[1] == 'changed')} changed, "
         f"{sum(1 for r in rows if r[1] == 'new')} new, {sum(1 for r in rows if r[1] == 'removed')} removed.", "",
         "## 1. Per file", "", "| file | state | v3 sha256 | v4 sha256 | +lines | -lines | run by this task |", "|---|---|---|---|---|---|---|"]
    for rel, state, so, sn, a, r, ran in rows:
        L.append(f"| `{rel}` | {state} | `{(so or '-')[:16]}` | `{(sn or '-')[:16]}` | {a} | {r} | {ran} |")
    L += ["", "## 2. What each change answers", "",
          "- `r42common.py`: the work folder (r43p), the stamp `r32-v4`, the date and scope `m2-fresh-validation-r32-v4-2026-10-08`, the dry base "
          "`DRY_BASE`, the R43 trees and heads (review43 re-points 1-4), `LEDGER_EXPECTED` 484 / 18 / 0 (R43V-04), the package and file names of v4, the "
          "v3 record constants, the review43 harness constants (`HARNESS43`, `BINDING43`, `HARNESS_GROUP`; `HARNESS42` now names the folder the code is "
          "imported from: the bound folder or the byte copy named by `R43_HARNESS_RUN`), the task file, `check_run_copy()` (R43V-09) and `declared_here()` "
          "(Verification 43 P8: `preflight_r32.HERE` set to the bound folder in the calling process for the isolation key).",
          "- `build_declaration_r42.py`: `build_v4()` / `evidence_v4()` build v4 from the frozen v3 bytes (R43 re-point, harness hashes from "
          "BINDING-MANIFEST-R43-HARNESS, the R43-40 items); `main()` checks the review43 group and the run copy, expects 484 / 18 / 0 and calls `build_v4`; "
          "the owner procedures refuse the v3 frozen and RUN hashes too. v3's `build()` is kept unchanged (not called).",
          "- `diff_declaration_r42.py`: v3 -> v4 with the categories repointed / rebound and the old-identifier text check (R43V-13).",
          "- `preflight_r42.py`: the review43 manifest and group, the run-copy check, `declared_here`, lane roots in r43p, 484 / 18 / 0, the bound-harness "
          "listing, and the authorization-file invariant as a before/after comparison (the v3 RUN and authorization files are committed, 7a1bf6f).",
          "- `dry_exercise_r42.py`: runs the runner through `runner_r43p.py` (S-BASE), the dry base, the review43 manifest, stamps `r43d-*`, 484 / 18 / 0, "
          "the run-copy check and the dry statement.",
          "- `demos_r42.py`: the run-copy check, S-BASE (including the live-shaped declarations' sandbox base), stamps `r43d-*`, one added refusal case "
          "(an authorization naming the executed v3 RUN hash).",
          "- `cli_version_drill_r42.py`: S-BASE, the dry base, the review43 manifest. `create_scope_r42.py`: the review43 manifest and group, the run-copy "
          "check, `declared_here`, the v3 hashes refused, the v4 pinned path in its text. `package_r42.py`: the ledger pin (not run).",
          "- `guard/sitecustomize.py` (R43V-10): rewritten from the R42 guard: deny-first for live run folders r32-v<N>, the owner records (no read either "
          "unless hash-only), the AI ledger folder, the trees and the frozen packages; allowed roots r43p and this package (or R43_GUARD_ROOTS inside "
          "the sandbox base).",
          "- New: `r43p_base.py` (S-BASE), `runner_r43p.py` (dry runner wrapper), `snapshot_r43p.py`, `guard_probe_r43p.py`, "
          "`make_v4_build_diff_r43p.py`, `manifest_v4_r43p.py`.", "",
          "## 3. Ledger-baseline lines (Verification 43 R43V-04; every line of the v4 scripts that reads or names the pin)", "",
          "| file | line | text |", "|---|---|---|"]
    L += [f"| `{rel}` | {i} | `{line[:160].replace('|', '/')}` |" for rel, i, line in ledger_lines]
    L += ["", "## 4. Run-time substitutions of this task (no file changed by them)", "",
          "- **S-RUN**: every script ran from byte copies in `C:/t/r2x/r42-sandbox/r43p/run/` (`v4/` = this package's scripts, `h43/harness-r32` = the "
          "review43 harness); `R43_HARNESS_RUN` names the harness copy; `C.check_run_copy()` re-hashes it against BINDING-MANIFEST-R43-HARNESS before "
          "any import (evidence/RUN-COPY-*.sha256).",
          "- **S-HERE** (Verification 43 P8): `preflight_r32.HERE` = `PILOT/review43/scripts/harness-r32` in the build, preflight and scope processes "
          "(`C.declared_here`), so the isolation key equals the folder the live runner runs from.",
          "- **S-BASE**: dry and demonstration run folders under `C:/t/r2x/r42-sandbox/r43p/sb` (`r43p_base.redirect`, the calling process only).",
          "- **S-GUARD**: `PYTHONPATH` = the guard copy `r43p/run/v4/guard`; `R43_GUARD_LOG` = `r43p/guard-log`; `TEMP` / `TMP` = `r43p/tmp`; "
          "`R43_GUARD_OWNER_RECORDS=hash-only` only for the two snapshot processes.",
          "- **S-ENV**: lane roots of the preflight's offline lane checks in `r43p/env-<lane>` (Verification 43 V-P4).", "",
          "## 5. Unified diffs (v3 -> v4)", ""]
    for rel, d in diffs:
        L += [f"### `{rel}`", "", "```diff"] + d + ["```", ""]
    C.write_once(out, "\n".join(L) + "\n")
    print({"written": out.as_posix(), "changed": len(diffs), "new": sum(1 for r in rows if r[1] == "new"), "ledger_lines": len(ledger_lines)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
