# V5-BUILD-DIFF: the v5 package scripts against the v4 scripts they were copied from (task R43-44)

Every v4 script (`PILOT/declaration-r32-v4/scripts/`, 34 files) was first copied byte-identically into `scripts/` of this package (`evidence/COPY-V4-SCRIPTS.sha256`, checked equal to the v4 files at the copy: 0 differ) and then changed only where listed below. Nothing in the review45 or review43 harness, review42, or declaration-r32-v2/v3/v4 was changed. It authorizes nothing.

- Copy record covers every v4 script: True.
- Files: 23 unchanged, 11 changed, 2 new, 0 removed.

## 1. Per file

| file | state | v4 sha256 | v5 sha256 | +lines | -lines | run by this task |
|---|---|---|---|---|---|---|
| `append_response_r42.py` | unchanged | `25ffc3c3d9bc7560` | `25ffc3c3d9bc7560` | 0 | 0 | not run by this task |
| `auth_test_exception_r43p.py` | unchanged | `76ec713129308a20` | `76ec713129308a20` | 0 | 0 | not run by this task |
| `build_declaration_r42.py` | changed | `ccb2664937a3b72e` | `4cb0284f0dd178ef` | 360 | 12 | show (twice), write |
| `cli_version_drill_r42.py` | changed | `f9d5553575838b0b` | `9ac64277cda856db` | 2 | 2 | not run by this task |
| `create_scope_r42.py` | changed | `e801d50f9a366b6b` | `5f17502d88784d46` | 7 | 7 | not run by this task |
| `demos_r42.py` | changed | `add582223e18d1f9` | `8473f5d02f8fe03d` | 7 | 5 | once |
| `diff_declaration_r42.py` | changed | `1744769efbb0f910` | `b29bccd36b1a6b52` | 142 | 4 | once (main_v5) |
| `dry_exercise_r42.py` | changed | `4540549301254601` | `b785bd29bd557860` | 49 | 11 | new-tag, single, finish-single |
| `facts_r42.py` | unchanged | `be47cc9e4e0d42fe` | `be47cc9e4e0d42fe` | 0 | 0 | not run by this task |
| `guard/sitecustomize.py` | changed | `6488ec7941d1114c` | `6a622719c60d72d0` | 9 | 6 | loaded by every package process (PYTHONPATH) |
| `guard_probe_r43p.py` | changed | `a8cb9dfc2e3bb1cd` | `b60e5848b791ef99` | 9 | 4 | once |
| `interpreter_check_r42.py` | unchanged | `d5fda9139be10c28` | `d5fda9139be10c28` | 0 | 0 | not run by this task |
| `lane_env_check_r42.py` | unchanged | `67ee5ed08ff81286` | `67ee5ed08ff81286` | 0 | 0 | by preflight_r42.py (step 6) |
| `make_binding_r42.py` | unchanged | `36e56876c055bc17` | `36e56876c055bc17` | 0 | 0 | not run by this task |
| `make_contract_v5_r42.py` | unchanged | `477d02493108d8d0` | `477d02493108d8d0` | 0 | 0 | not run by this task |
| `make_outputs_r42.py` | unchanged | `a890904c48ff7eff` | `a890904c48ff7eff` | 0 | 0 | not run by this task |
| `make_report_r42.py` | unchanged | `ba46a61c5c1a4b99` | `ba46a61c5c1a4b99` | 0 | 0 | not run by this task |
| `make_review42_docs.py` | unchanged | `4e84842803cdb123` | `4e84842803cdb123` | 0 | 0 | not run by this task |
| `make_v3_docs_r42.py` | unchanged | `a165196eff87e4c5` | `a165196eff87e4c5` | 0 | 0 | not run by this task |
| `make_v4_build_diff_r43p.py` | unchanged | `6e3be854726636bf` | `6e3be854726636bf` | 0 | 0 | not run by this task |
| `make_v5_build_diff_r45q.py` | new | `-` | `a48cf2d2cb9aab97` | 0 | 0 | once |
| `manifest_v4_r43p.py` | unchanged | `73de5002a7433e6c` | `73de5002a7433e6c` | 0 | 0 | not run by this task |
| `manifest_v5_r45q.py` | new | `-` | `b78d178768112c83` | 0 | 0 | manifest, self-check 1 and 2 |
| `package_r42.py` | unchanged | `cbfa20032bba5ff5` | `cbfa20032bba5ff5` | 0 | 0 | not run by this task |
| `patch_runner_main_r42.py` | unchanged | `d20ea0df697ee609` | `d20ea0df697ee609` | 0 | 0 | not run by this task |
| `pathlen_probe_r42.py` | unchanged | `4763cc2efcdff45c` | `4763cc2efcdff45c` | 0 | 0 | not run by this task |
| `preflight_r42.py` | changed | `edb8660c23d8c462` | `7f935367db2a7f43` | 50 | 12 | twice with --upto 7 (attempt 1 refused by the lanes' isolation check on the launcher's R43_GUARD_ROOTS: evidence/preflight-attempt-1; attempt 2 is dry-run/PREFLIGHT-RESULTS.json) |
| `r42common.py` | changed | `4f05b78c71b54829` | `2a8a7e6aef83dacb` | 41 | 23 | imported |
| `r43p_base.py` | unchanged | `b42b567894847757` | `b42b567894847757` | 0 | 0 | imported |
| `run_tests_r42.py` | unchanged | `bed0672b578d329e` | `bed0672b578d329e` | 0 | 0 | not run by this task |
| `run_tests_r42pkg.py` | unchanged | `d94dd756d3399735` | `d94dd756d3399735` | 0 | 0 | not run by this task |
| `runner_r43p.py` | unchanged | `5ff4376e1a09048b` | `5ff4376e1a09048b` | 0 | 0 | by dry_exercise_r42.py |
| `snapshot_r42.py` | unchanged | `eebeede2a05a89f1` | `eebeede2a05a89f1` | 0 | 0 | not run by this task |
| `snapshot_r43p.py` | changed | `5d44bfaeb1f55794` | `490e07dac5e9c9e0` | 25 | 5 | before and after |
| `test_r42.py` | unchanged | `f5bda56117e435df` | `f5bda56117e435df` | 0 | 0 | not run by this task |
| `trim_sandbox_r42.py` | unchanged | `71bad1201f87a73f` | `71bad1201f87a73f` | 0 | 0 | not run by this task |

## 2. What each change answers

- `r42common.py`: the work folder r45q, the stamp `r32-v5`, the scope `m2-fresh-validation-r32-v5-2026-10-08`, the v5 package and file names, the review45 harness constants (`REVIEW45`, `HARNESS45`, `BINDING45`, `BINDING45_SHA`, `DRILL_CRITERION_SHA`; `HARNESS_GROUP` = `harness_r45_package`; `HARNESS42` = the review45 folder or the byte copy named by `R43_HARNESS_RUN`), `check_run_copy()` and `declared_here()` re-pointed to review45, the v4 record constants (`V4`, `V4_SHA`, `V4_MANIFEST_SHA`, `V4_SCOPE`, `V4_RUN_FOLDER`; `HARNESS43_GROUP` kept for the record), the task file R43-44. `LEDGER_EXPECTED` stays 484 / 18 / 0.
- `build_declaration_r42.py`: `build_v5()` / `evidence_v5()` build v5 from the frozen v4 bytes (one re-point review43 -> review45 harness folder, the review45 manifest's hashes, the R43-44 items: stamp / folder / scope / pinned paths, supersedes and chain, corrected and added disclosures, the carried test exception, A-13 item 3 as history, `owner_decision_required`, the drill request-path coverage); `main()` checks the review45 group and the run copy, 484 / 18 / 0 with no v4 or v5 scope, no r32-v4 or r32-v5 folder, and calls `build_v5`; the owner procedures also refuse the v4 hash. `build_v4()` / `build()` kept, not called.
- `diff_declaration_r42.py`: `main_v5()` (v4 -> v5, the same leaf categories with the review45 re-point and rebinding, the same protected list, the v4-identifier text check, the trees check and a new-identifier check) writes DECLARATION-DIFF-V4-V5.json/.md; `main_v4` kept.
- `preflight_r42.py`: the review45 manifest and group and bound folder; `--upto 7` writes the results after step 7 (`finish_upto`): steps 8-12 are not run (the card).
- `dry_exercise_r42.py`: the review45 manifest, stamps `r45q-*`, `finish-single` (DRY-EXERCISE.json from the single run only).
- `demos_r42.py`: stamps `r45q-*`, the review45 names. `create_scope_r42.py` (owner only; NOT run): the review45 manifest and group, the v5 pinned path in its text, the v4 hash refused too. `cli_version_drill_r42.py` (not run): the review45 manifest.
- `guard/sitecustomize.py`: review45 and declaration-r32-v4 denied like the other frozen packages; default roots r45q and PILOT/declaration-r32-v5 (the v4 package is never a root).
- `guard_probe_r43p.py`: probes for the v5 and the never-created v4 run folders, review45, declaration-r32-v4, the v5 package. `snapshot_r43p.py`: review45 and declaration-r32-v4 hashed; the executed v3 run folder by os.stat only (no file opened); v4/v5 scopes and folders.
- New: `make_v5_build_diff_r45q.py` (this file), `manifest_v5_r45q.py` (BINDING-MANIFEST-R32-V5.json and its self-check; binds IMPLEMENTATION-REPORT.md, written before it).
- Unchanged and still carrying v4 wording in docstrings only: `r43p_base.py`, `runner_r43p.py` (they use `C.WORK` / `C.DRY_BASE`, i.e. r45q), `make_v4_build_diff_r43p.py`, `manifest_v4_r43p.py`, `auth_test_exception_r43p.py` (not run; v4 records).

## 3. Ledger-baseline lines (every line of the v5 scripts that names or reads the pin; unchanged at 484 / 18 / 0)

| file | line | text |
|---|---|---|
| `build_declaration_r42.py` | 631 | `"rule": ("Verification 43 R43V-04: the build, dry-exercise and preflight scripts of this package expect 484 / 18 / 0 (r42common.LEDGER_EXPECTED, "` |
| `build_declaration_r42.py` | 690 | `"ledger_baseline": "ledger_baseline (484 / 18 / 0 at freeze; no v4 scope)",` |
| `build_declaration_r42.py` | 729 | `"ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v4 freeze (the v3 scope present); the runtime harness does not read that pin",` |
| `build_declaration_r42.py` | 757 | `"4_ledger_baseline": "re-pinned to 484 / 18 / 0 in the v4 copies of r42common.py (LEDGER_EXPECTED, read by build_declaration_r42, facts_r42, package_r42, dry_ex` |
| `build_declaration_r42.py` | 929 | `rule=("Verification 43 R43V-04, carried: the build, dry-exercise and preflight scripts of this package expect 484 / 18 / 0 "` |
| `build_declaration_r42.py` | 930 | `"(r42common.LEDGER_EXPECTED, unchanged in the v5 copies; V5-BUILD-DIFF.md) and compare the ledger before and "` |
| `build_declaration_r42.py` | 985 | `pre["ledger_baseline"] = "ledger_baseline (484 / 18 / 0 at freeze; no v4 or v5 scope)"` |
| `build_declaration_r42.py` | 1022 | `"ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v4 freeze": (` |
| `build_declaration_r42.py` | 1023 | `"ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v5 freeze, as at the v4 freeze (the v3 scope present; no v4 "` |
| `build_declaration_r42.py` | 1168 | `if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"] or C.V4_SCOPE in led["scope_names"]:` |
| `diff_declaration_r42.py` | 64 | `"ledger_detail": "the creation sentence names 484 / 18 / 0 (R43V-04)", "isolation": "the review43 harness folder (section 0 item 1)",` |
| `diff_declaration_r42.py` | 75 | `"ledger_baseline": "ADDED (section 0 item 4, R43V-04): 484 / 18 / 0 at freeze",` |
| `diff_declaration_r42.py` | 226 | `"ledger_baseline": "re-read at this freeze (484 / 18 / 0 unchanged; v5 scope absent added; the rule restated for the v5 copies)",` |
| `dry_exercise_r42.py` | 20 | `The AI ledger is read (mode=ro) before and after every phase: 484 / 18 / 0 (R43-40; v3: 483 / 17 / 0). 0 model requests. Staged PDF copies of every` |
| `dry_exercise_r42.py` | 324 | `"ai_ledger_unchanged_484_18_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,` |
| `dry_exercise_r42.py` | 367 | `"ai_ledger_unchanged_484_18_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,` |
| `facts_r42.py` | 101 | `"ai_ledger": {k: f["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and not f["ai_ledger"]["scope_v3_exists"],` |
| `make_v4_build_diff_r43p.py` | 53 | `if re.search(r"LEDGER_EXPECTED/\(483, 17, 0\)/483 / 17 / 0/484 / 18 / 0", line):` |
| `make_v4_build_diff_r43p.py` | 68 | `"`DRY_BASE`, the R43 trees and heads (review43 re-points 1-4), `LEDGER_EXPECTED` 484 / 18 / 0 (R43V-04), the package and file names of v4, the "` |
| `make_v4_build_diff_r43p.py` | 73 | `"BINDING-MANIFEST-R43-HARNESS, the R43-40 items); `main()` checks the review43 group and the run copy, expects 484 / 18 / 0 and calls `build_v4`; "` |
| `make_v4_build_diff_r43p.py` | 76 | `"- `preflight_r42.py`: the review43 manifest and group, the run-copy check, `declared_here`, lane roots in r43p, 484 / 18 / 0, the bound-harness "` |
| `make_v4_build_diff_r43p.py` | 78 | `"- `dry_exercise_r42.py`: runs the runner through `runner_r43p.py` (S-BASE), the dry base, the review43 manifest, stamps `r43d-*`, 484 / 18 / 0, "` |
| `make_v5_build_diff_r45q.py` | 30 | `"`HARNESS43_GROUP` kept for the record), the task file R43-44. `LEDGER_EXPECTED` stays 484 / 18 / 0.",` |
| `make_v5_build_diff_r45q.py` | 34 | `"checks the review45 group and the run copy, 484 / 18 / 0 with no v4 or v5 scope, no r32-v4 or r32-v5 folder, and calls `build_v5`; the "` |
| `make_v5_build_diff_r45q.py` | 102 | `if re.search(r"LEDGER_EXPECTED/484 / 18 / 0", line):` |
| `make_v5_build_diff_r45q.py` | 116 | `L += ["", "## 3. Ledger-baseline lines (every line of the v5 scripts that names or reads the pin; unchanged at 484 / 18 / 0)", "",` |
| `manifest_v4_r43p.py` | 196 | `ck("AI ledger 484 / 18 / 0, no v4 scope", {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and C.SCOPE not in led["scope_names"])` |
| `manifest_v5_r45q.py` | 225 | `ck("AI ledger 484 / 18 / 0, no v4 or v5 scope", {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and C.SCOPE not in led["scope_names"]` |
| `package_r42.py` | 30 | `"ok": (led["entries"], led["scopes"], led["limit_amendments"]) == tuple(C.LEDGER_EXPECTED[k] for k in ("entries", "scopes", "limit_amendments")) and C.SCOPE not` |
| `preflight_r42.py` | 5 | `work folder r43p; the ledger expected 484 / 18 / 0; the authorization-file invariant a before/after comparison, since the` |
| `preflight_r42.py` | 204 | `"ai_ledger_484_18_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,` |
| `preflight_r42.py` | 398 | `"ai_ledger_484_18_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,` |
| `r42common.py` | 48 | `LEDGER_EXPECTED = {"entries": 484, "scopes": 18, "limit_amendments": 0}   # R43-40 (R43V-04): re-pinned to the state at the v4 freeze (v3 scope present)` |

## 4. Run-time substitutions and work helpers of this task (no package file changed by them)

- **S-RUN**: every package script ran from the byte copy `C:/t/r2x/r42-sandbox/r45q/run/v5` (re-synchronised and re-hashed against this package before every launch by the work helper `r45q/s/v5run.py`; record `r45q/o/RUN-COPY-V5.jsonl`); the harness from the byte copy `r45q/run/r45/scripts/harness-r32` of `PILOT/review45/scripts/harness-r32` (85 review45 script files copied, 0 differ; `R43_HARNESS_RUN`; `C.check_run_copy()` before every import).
- **S-HERE**: `preflight_r32.HERE` = `PILOT/review45/scripts/harness-r32` in the build and preflight processes (`C.declared_here`).
- **S-BASE**: dry and demonstration run folders under `C:/t/r2x/r42-sandbox/r45q/sb` (`r43p_base.redirect`, the calling process only).
- **S-GUARD**: `PYTHONPATH` = the guard copy `r45q/run/v5/guard`; `R43_GUARD_LOG` = `r45q/guard-log`; `TEMP` / `TMP` = `r45q/tmp`; `R43_GUARD_ROOTS` not set (the guard's defaults r45q and this package); `R43_GUARD_OWNER_RECORDS=hash-only` only for the two snapshot processes. The guard probes ran with `R43_GUARD_ROOTS=r45q;<this package>` (the same roots). Preflight attempt 1 also had it set; the lanes' isolation check refused that variable (it names a path under the merged installation), so step 6 failed; the attempt is kept in `evidence/preflight-attempt-1/` and the variable was dropped for every later launch.
- **S-ENV**: lane roots of the preflight's offline lane checks in `r45q/env-<lane>`.
- **S-R45Q-1** (the drill reproduction only): `PILOT/review45/scripts` byte-copied to `r45q/run/r45/scripts` (85 files, 0 differ); in the copy of `r45/r45common.py` line 21 `WORK = SANDBOX_BASE / "r45p"` -> `"r45q"` (Verification 45's V45-S1 with r45q); `r45/r45_drill_run.py` and `r45/r45_launch.py` run unchanged with the review45 guard copy (roots r45q); the binding given was `PILOT/review45/BINDING-MANIFEST-R45-HARNESS.json` with `9af8e07a...9ffb` (evidence/drill-v5/RUN-COPY-AND-SUBSTITUTIONS.json).
- **Dry exercise trim record**: the single phase trimmed its staged PDF copies, but the append to `r45q/out/TRIMMED.jsonl` failed (the folder did not exist) after the phase record was written; `r45q/out/TRIMMED-NOTE.json` records it; `finish-single` then ran normally.
- Work helpers outside the package (not package scripts; under `r45q/s`): `logrow.py` (session-log rows), `patch_*.py` and `block_*.txt` (the edits listed in section 5), `v5run.py` (the launcher), `compare_drill.py` and `pack_drill.py` (the drill comparison and evidence copy), `difftest.py` (a dry test of the v5 diff on a scratch copy).

## 5. Unified diffs (v4 -> v5)

### `build_declaration_r42.py`

```diff
--- declaration-r32-v4/scripts/build_declaration_r42.py
+++ declaration-r32-v5/scripts/build_declaration_r42.py
@@ -1,2 +1,5 @@
-"""ORCH-10 (R42PORT-IMPL): build and write ONCE the corrected fresh-validation declaration v3
+"""R43-44: build_v5() / evidence_v5() build and write ONCE declaration v5 (FRESH-VALIDATION-DECLARATION-R32-V5.json) from the frozen
+v4 bytes e0a93c46...fbeb9, bound to the review45 harness (BINDING-MANIFEST-R45-HARNESS 9af8e07a...9ffb); V5-BUILD-DIFF.md.
+R43-40: build_v4() (kept, not called) built v4 from the v3 bytes.
+ORCH-10 (R42PORT-IMPL): build and write ONCE the corrected fresh-validation declaration v3
 `PILOT/declaration-r32-v3/FRESH-VALIDATION-DECLARATION-R32-V3.json` and `DECLARATION.sha256` beside it, bound to the review42
@@ -37,3 +40,3 @@
 
-PKG_SCRIPTS = "PILOT/declaration-r32-v4/scripts"   # R43-40
+PKG_SCRIPTS = "PILOT/declaration-r32-v5/scripts"   # R43-44
 V2_PROOF = C.V2 / "evidence/r40-04-proof"
@@ -127,3 +130,3 @@
         raise ValueError("the RUN hash and the digest are 64 lower-case hex characters")
-    if run_sha in (frozen_sha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA):   # R43-40: never a frozen or the executed v3 hash
+    if run_sha in (frozen_sha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA, C.V4_SHA):   # R43-40 / R43-44: never a frozen or the executed v3 hash
         raise ValueError("the authorization names the RUN hash, never a frozen hash")
@@ -770,2 +773,347 @@
 
+# ---- R43-44: the v5 declaration, built from the frozen v4 bytes -------------------------------------------------------------
+# Method: the v4 declaration e0a93c46...fbeb9 (frozen 2026-10-08, NEVER authorized, NEVER run; superseded under option 1 of
+# Verification 44) is loaded from its exact bytes; ONE re-point is applied to every string (the harness folder
+# review43/scripts/harness-r32 -> review45/scripts/harness-r32); every {path, sha256} node under the review45 harness takes the
+# hash BINDING-MANIFEST-R45-HARNESS binds; then ONLY the items of task R43-44 section 2 are applied (the harness rebind, the
+# stamp / folder / scope / pinned paths, supersedes, the corrected disclosures, the carried test exception, A-13 item 3 as
+# history, owner_decision_required). Every protected number of v4 is unchanged (DECLARATION-DIFF-V4-V5).
+R45_REPOINT = (("/real-project-pilot/review43/scripts/harness-r32", "/real-project-pilot/review45/scripts/harness-r32"),)
+V45 = C.MR / "reviews/M2-review-45"
+V44 = C.MR / "reviews/M2-review-44"
+V3_LIVE_B_READ = ("F043", "F038", "F035", "F051", "F042", "F047", "F040", "F039", "F072", "F057", "F046", "F060", "F066", "F021", "F009")
+DRILL_DOCS = {"F009": "970ddb0f5b59199b41f33bee8356dd87418d9daff26ec9a9b8a72a3538bab415",
+              "F020": "599d36be15e6eded0fcbe4226afdb49c9b282f6bcbbd13c3c3376872da1891db",
+              "F030": "feec64cdcb0b7a95262c9991fd09830d810f88e75d87be05ac308c106047010a"}
+DRILL_READS = (("task R43-42 (implementer)", "the evidence run r32-drill-r45-evidence-1"),
+               ("task R43-42 (implementer)", "the harness test module test_dry_baseline_drill_r45 (one drill run in a test sandbox)"),
+               ("Verification 45 (task R43-43V)", "its reproduction v45-repro-1"),
+               ("Verification 45 (task R43-43V)", "its run of the test module (sandbox r32-drill-t45-03a9c5bdc6)"),
+               ("task R43-44 (implementer)", "the reproduction on v5's bindings r32-drill-r45q-v5bind-1 (evidence/drill-v5 of this package)"))
+V45_CHECK8 = (
+    "1. The owner's choice of option 1 and the restated (b), as a new register entry. A-13 item 3 named \"v4 ... tonight\".",
+    "2. Declaration v5: v4 with only the harness rebind to the review45 manifest, the new stamp, folder and scope, and the corrected disclosure (section 4).",
+    "3. An independent verification of v5 (Verification 46), whose v4->v5 diff is limited to the rebind and the disclosure.",
+    "4. R44-07: the v5 runbook, scope-creation command, summary and budget card.",
+    "5. The pip-freeze precondition (bd424a5c...bf7f) before invocation 1 and before every resume.",
+    "6. A fresh owner D1/D2 naming the v5 hash. The authorization goes at the pinned path; the owner alone creates the scope; then the two-hash "
+    "procedure (the frozen declaration hash and the RUN-file hash carrying the owner-token digest).")
+
+
+def v4_bytes() -> bytes:
+    b = (C.V4 / C.V4_NAME).read_bytes()
+    if C.sha256_bytes(b) != C.V4_SHA:
+        raise C.PacketMismatch(f"PACKET MISMATCH: the v4 declaration is not {C.V4_SHA}")
+    return b
+
+
+def repoint45(o):
+    if isinstance(o, dict):
+        return {k: repoint45(v) for k, v in o.items()}
+    if isinstance(o, list):
+        return [repoint45(v) for v in o]
+    if isinstance(o, str):
+        for a, b in R45_REPOINT:
+            o = o.replace(a, b)
+        return o
+    return o
+
+
+def build_v5(declared_at: str, ev: dict) -> dict:
+    sys.path.insert(0, str(C.HARNESS42))
+    import preflight_r32 as PF           # noqa: E402  (checked against BINDING-MANIFEST-R45-HARNESS first: C.check_run_copy)
+    C.declared_here(PF)
+    v4 = json.loads(v4_bytes().decode("utf-8"))
+    d = repoint45(copy.deepcopy(v4))
+    binding = json.loads(C.BINDING45.read_text(encoding="utf-8"))
+    h45 = binding["files"][C.HARNESS_GROUP]
+    rebound = [{"at": x["at"], "path": x["path"], "v4_sha256": x["v3_sha256"], "v5_sha256": x["v4_sha256"]}
+               for x in rebind_harness(d, h45)]                   # (rebind_harness names its keys for v3 -> v4)
+    modules = {pathlib.Path(p).stem: {"path": p, "sha256": s} for p, s in h45.items()
+               if "/scripts/harness-r32/" in p and not pathlib.Path(p).name.startswith("test_")}
+    run_folder = C.RUN_FOLDER.as_posix()
+    pinned = (C.PACKAGE / C.AUTH_NAME).as_posix()
+    run_path = (C.PACKAGE / C.RUN_NAME).as_posix()
+    if register_item(3) != A13_ITEM3:
+        raise C.PacketMismatch("PACKET MISMATCH: A-13 item 3 in the authority register differs from the text this script records")
+    drill = ev["drill_v5"]
+    if drill["criterion"] != "PASS" or drill["requests_total"] != 0 or drill["resolved_criticals"] != 0 or drill["binding_sha256"] != C.BINDING45_SHA:
+        raise C.PacketMismatch(f"refused: the v5-binding drill reproduction is not a PASS with 0 requests: {drill}")
+
+    d["schema"] = "r43-44-fresh-validation-declaration-r32-v5.1"
+    d["contract"] = PF.CONTRACT
+    d["name"] = ("M2 fresh validation R32, declaration v5 (R43 trees, review45 harness): accepted baseline B (frozen-r13) vs Review 29 combined "
+                 "candidate C (cand-r30n), with reference R and variation probe P")
+    d["task"] = ("R43-44 (label R32-V5-PREP; owner decision A-13 item 2; Verification 44 option 1, Verification 45 section 5 item 2), "
+                 "implementation agent ep-implementer, Claude Opus 5.5 (claude-opus-5-5, self-reported), effort high")
+    d["supersedes"] = {
+        "declaration": ref(C.V4 / C.V4_NAME), "manifest": ref(C.V4 / "BINDING-MANIFEST-R32-V4.json"),
+        "status": ("frozen 2026-10-08, NEVER authorized and NEVER run: condition (b) of A-13 item 3 could not be met inside the review43 harness "
+                   "(Verification 44, R44-06) and item 3 lapsed by its own wording (R44-13); superseded by v5 under option 1 of Verification 44 "
+                   "(the harness rebind to review45); its stamp r32-v4, run folder C:/t/r2x/r42-sandbox/r32-v4 and scope "
+                   "m2-fresh-validation-r32-v4-2026-10-08 were never created and are never used; it stays frozen as a record"),
+        "binding_manifests": {"v4_binding_review43": ref(C.BINDING43), "superseded_by": ref(C.BINDING45),
+                              "rule": ("the review43 harness manifest f35355aa...374a7 (bound by v4) is superseded for the harness-r32 code by the "
+                                       "review45 manifest 9af8e07a...9ffb (review43 plus the dry-only baseline-facts drill; its 479 review43 entries "
+                                       "carried and re-hashed equal), which v5 binds")},
+        "differences": "DECLARATION-DIFF-V4-V5.md and DECLARATION-DIFF-V4-V5.json in this package list every difference from v4",
+        "structure": ("the v4 content is carried; only the R43-44 items change it (the harness rebind to review45, the stamp, run folder, scope "
+                      "and pinned paths, supersedes, the corrected disclosures, the carried test exception, A-13 item 3 as history, "
+                      "owner_decision_required); every number of v4 is unchanged"),
+        "chain": {"v4": C.V4_SHA, "v3": C.V3_SHA, "v3_run_declaration": C.V3_RUN_SHA, "v2": C.V2_SHA,
+                  "rule": "v3 was executed (terminal); v2 and v4 were never run; none is ever run again"},
+        "lineage": v4["supersedes"]}
+    d["declared_at_utc"] = declared_at
+    d["status"] = ("FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file, no run file and no dispatch exist for v5; "
+                   "Verification 46, the owner's choice of option 1 with the restated condition (b), and a fresh owner D1/D2 naming this "
+                   "declaration's hash are pending (owner_decision_required)")
+    d["authorities"]["register"] = ref(C.MR / "orchestrator/AUTHORITY-REGISTER.md")
+    d["owner_conditional_decision"] = dict(d["owner_conditional_decision"], carried_as="HISTORY", status_at_v5_freeze=(
+        "LAPSED: item 3 was worded for 'a v4 live run tonight' (the night of 2026-10-07/08; Verification 44 R44-13) and its condition (b) "
+        "was not met for v4 (R44-06); v4 was never authorized and never run; nothing may run under item 3, for v4 or for v5; a fresh owner "
+        "D1/D2 naming the v5 hash is required (owner_decision_required)"))
+    d["owner_decision_required"] = {
+        "source": ref(V45 / "INDEPENDENT-VERIFICATION.md") | {"section": "5 (check 8: readiness statement for the owner), 'What remains before any D1/D2'"},
+        "steps": list(V45_CHECK8),
+        "steps_note": "the six steps verbatim; 'section 4' in step 2 is section 4 of Verification 45 (the disclosure corrections, carried in disclosures)",
+        "restated_condition_b": ("Verification 45: if the owner restates condition (b) as 'the review45 drill passes on F009/F020/F030', it is MET "
+                                 "(reproduced by Verification 45 and once more by task R43-44 on v5's bindings), with the limit of R45-08: it does "
+                                 "not show that the model's form reading of F009 and F020 is safe"),
+        "status_at_v5_freeze": {
+            "1": "pending (the owner)",
+            "2": "this declaration (frozen, NOT authorized)",
+            "3": "pending (Verification 46)",
+            "4": ("RUNBOOK-R32-V5.md, SCOPE-CREATION-COMMAND.md, SUMMARY-R32-V5.md and BUDGET-CARD-V6.md are written in this package after this "
+                  "declaration (they name its hash) and bound by BINDING-MANIFEST-R32-V5.json; not yet verified"),
+            "5": "held at this freeze (bd424a5c...bf7f); the owner re-checks it before invocation 1 and before every resume",
+            "6": "pending (the owner)"},
+        "rule": ("none of these steps was taken by task R43-44 and nothing in this declaration takes, delegates or authorizes any of them; no "
+                 "scope, token, RUN file, authorization file, nonce or invocation may follow from this record alone")}
+    d["binding_manifest_sha256"] = C.sha256_file(C.BINDING45)
+    if d["binding_manifest_sha256"] != C.BINDING45_SHA:
+        raise C.PacketMismatch("PACKET MISMATCH: the review45 harness manifest")
+    r = d["run"]
+    r.update({"stamp": C.STAMP, "sandbox_base": C.SANDBOX_BASE.as_posix(), "folder": run_folder, "allowance": f"{run_folder}/allowance.sqlite",
+              "capture_store": f"{run_folder}/capture.sqlite", "run_state": f"{run_folder}/RUN-STATE.json"})
+    r["base_justification"] = [
+        "C:/t/r2x/r42-sandbox matches the bound preflight's declared-base rule C:/t/r2x/r<NN>-sandbox (unchanged from v3 and v4); this task's dry runs, demonstrations and drill reproduction use the driver-side dry base C:/t/r2x/r42-sandbox/r45q/sb (r43p_base.py; r45_drill_run.py) and stamps beginning 'r45q', never 'r32-v5'; r32-v3 (executed) is never reused; r32-v4 was never created and is never created",
+        r["base_justification"][1], r["base_justification"][2]]
+    a = d["authorization"]
+    a["path"] = pinned
+    a["two_hash_procedure"]["run_file"] = run_path
+    a["two_hash_procedure"]["budget_authorization_names"] = [
+        "the frozen hash", "the digest", "the RUN hash", f"the absolute RUN-file path {run_path}", f"the absolute authorization path {pinned}",
+        f"the scope {C.SCOPE} with limits {json.dumps(d['ledger']['limits'], sort_keys=True)}",
+        "the first invocation (runner_r32.py run --mode live, RUNBOOK-R32-V5.md section 5.1)",
+        "optionally (A-11 section 4, the owner's choice): one authorization file for up to 3 planned invocations (invocations_authorized, nonces)"]
+    a["runbook"] = ("RUNBOOK-R32-V5.md in this package (R44-07; exact, ordered, absolute paths, cmd.exe; written after this declaration by task "
+                    "R43-44 in the form of v3's RUNBOOK.md, naming this declaration's hash) and SCOPE-CREATION-COMMAND.md for the scope")
+    a["invocation"] = dict(a["invocation"], working_directory=C.HARNESS45.as_posix(),
+                           run=(f"\"{C.PY}\" -B runner_r32.py run --mode live --declaration \"{run_path}\" --declaration-sha <RUN hash> --run-set "
+                                f"\"{C.RUN_SET.as_posix()}\" --binding \"{C.BINDING45.as_posix()}\" --binding-sha {d['binding_manifest_sha256']}"),
+                           harness_copy=("PILOT/review45/scripts/harness-r32 is the only harness BINDING-MANIFEST-R45-HARNESS binds as runnable "
+                                         "(harness_r45_package); neither the review43 nor the review42 harness nor any package script is run for v5; "
+                                         "the live runner refuses --dry-baseline-facts and every other dry drill flag"))
+    d["provider_env"]["AI_LEDGER_SCOPE"] = C.SCOPE
+    d["ledger"]["scope"] = C.SCOPE
+    old_creation = "task R43-40 created no scope (AI ledger 484 entries / 18 scopes / 0 amendments before and after, the v3 scope present, no v4 scope)"
+    if old_creation not in d["ledger_detail"]["creation"]:
+        raise C.PacketMismatch("the v4 ledger creation sentence was not found")
+    d["ledger_detail"]["creation"] = d["ledger_detail"]["creation"].replace(
+        old_creation, "task R43-44 created no scope (AI ledger 484 entries / 18 scopes / 0 amendments before and after, the v3 scope present, no v4 or v5 scope)")
+    led = C.ledger_state()
+    d["ledger_baseline"] = dict(d["ledger_baseline"],
+                                at_freeze={k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")},
+                                v3_scope_present=C.V3_SCOPE in led["scope_names"], v4_scope_present=C.V4_SCOPE in led["scope_names"],
+                                v5_scope_present=C.SCOPE in led["scope_names"],
+                                rule=("Verification 43 R43V-04, carried: the build, dry-exercise and preflight scripts of this package expect 484 / 18 / 0 "
+                                      "(r42common.LEDGER_EXPECTED, unchanged in the v5 copies; V5-BUILD-DIFF.md) and compare the ledger before and "
+                                      "after; the runtime harness never reads that pin; before the scope creation the declared scope must not exist, "
+                                      "and after it only the declared scope may grow (preflight_r32.ledger_live_check, unchanged)"))
+    d["provider"]["owner_confirmable"]["ledger.scope"] = f"declared {C.SCOPE!r} (a new name; no scope of that name exists)"
+    d["isolation"] = PF.isolation_binding()
+    if d["isolation"]["allowed_under_forbidden"]["harness"] != C.HARNESS45.as_posix():
+        raise C.PacketMismatch(f"PACKET MISMATCH: isolation harness {d['isolation']}")
+    hv = d["harness"]
+    hv["package"] = "PILOT/review45/"
+    hv["package_manifest"] = ref(C.BINDING45)
+    hv["package_check"] = ref(V45 / "INDEPENDENT-PACKAGE-CHECK.json")
+    hv["binding_manifest"] = ref(C.BINDING45) | {"entries": sum(len(v) for v in binding["files"].values()),
+                                                 "supersedes": ("review43/BINDING-MANIFEST-R43-HARNESS.json f35355aa...374a7 (bound by v4) for the "
+                                                                "harness-r32 code; its 479 entries are carried and re-hashed equal; it adds the "
+                                                                "dry-only baseline-facts drill, its tests and evidence")}
+    hv["accepted_by"] = ("Verification 45 (task R43-43V): VERIFIED WITH CONDITIONS, 0 blockers, 0 majors; minors R45-06 and R45-07 (the "
+                         "first-read disclosure: corrected in disclosures), R45-08 (the AI-on form reading of F009 and F020 is not rehearsed: "
+                         "disclosed and in owner_decision_required), R45-09 (no v5 and no R44-07 documents: this declaration and the documents "
+                         "of this package); the review43 harness it extends was accepted by Verification 43")
+    hv["modules"] = modules
+    hv["contracts"] = dict(hv["contracts"]) | {"drill_diff_r45": ref(C.REVIEW45 / "DRILL-DIFF.md"),
+                                               "drill_criterion_r45": ref(C.REVIEW45 / "DRILL-CRITERION.md"),
+                                               "disclosure_amendment_draft_r45": ref(C.REVIEW45 / "DISCLOSURE-AMENDMENT-DRAFT.md")}
+    hv["lineage"] = dict(hv["lineage"]) | {"review43": {"binding": ref(C.BINDING43), "repoint_diff": ref(C.REVIEW43 / "HARNESS-REPOINT-DIFF.md"),
+                                                       "accepted_by": "Verification 43 (VERIFIED WITH CONDITIONS); bound by declaration v4 (frozen, never authorized, never run)"}}
+    hv["bound_code_used_as_is"] = ("the bound code runs unchanged from PILOT/review45/scripts/harness-r32 under the bound interpreter (the review43 "
+                                   "harness plus the dry-only baseline-facts drill: runner_r32.py and lane_r32.py changed only in guarded drill "
+                                   "branches, drill_r45.py and its test module new; DRILL-DIFF.md); this package's preflight, dry exercise, "
+                                   "demonstrations and drill reproduction ran byte copies of the same files (C.check_run_copy; the drill from a byte "
+                                   "copy of review45/scripts) with preflight_r32.HERE set to the bound folder for the isolation key only (C.declared_here)")
+    d["request_path_coverage"]["dynamic"] = dict(d["request_path_coverage"]["dynamic"],
+                                                 junit=ref(C.REVIEW45 / "tests/full/test_global_provider_r42.xml"),
+                                                 result=ev["global_provider_tests_r45"])
+    d["request_path_coverage"]["drill_r45"] = {
+        "what": ("the dry-only baseline-facts drill of review45 (runner_r32.py --dry-baseline-facts, drill_r45.py, the lane_r32 drill branch): lane "
+                 "B only, frozen-r13 only, exactly F009, F020 and F030 by pool id and staged sha256, AI off (AI_ENABLED=false), the refusing global "
+                 "provider run_control_r38.RefusingGlobalProvider installed right after app.ai.provider is imported; no allowance, capture store, "
+                 "ledger, scope, authorization, nonce, token or RUN value is consulted or written (refusing stand-ins in the runner, Forbidden "
+                 "sentinels in the lane)"),
+        "files": {"drill_r45": modules["drill_r45"], "runner_r32": modules["runner_r32"], "lane_r32": modules["lane_r32"]},
+        "global_provider_in_the_drill": binding["global_provider"].get("B_in_the_baseline_facts_drill"),
+        "live_mode": "runner_r32.py refuses --dry-baseline-facts (with every other dry drill flag) in live mode before anything is created",
+        "junit": ref(C.REVIEW45 / "tests/new/test_dry_baseline_drill_r45.xml"), "result": ev["drill_tests_r45"],
+        "evidence": ref(C.REVIEW45 / "evidence/drill/out/DRILL-REPORT.json"),
+        "requests": "0 in every drill run (refusing-provider calls 0, dry-stub calls 0, no live provider class reached, no complete() traced)"}
+    d["reviews"] = dict(d["reviews"]) | {
+        "verification44": ref(V44 / "INDEPENDENT-VERIFICATION.md"), "verification44_findings": ref(V44 / "FINDINGS.json"),
+        "verification44_package_check": ref(V44 / "INDEPENDENT-PACKAGE-CHECK.json"),
+        "verification45": ref(V45 / "INDEPENDENT-VERIFICATION.md"), "verification45_findings": ref(V45 / "FINDINGS.json"),
+        "verification45_package_check": ref(V45 / "INDEPENDENT-PACKAGE-CHECK.json")}
+    d["trees_r43"]["corrected_v4_05"] = d["trees_r43"]["corrected_v4_05"].replace(
+        "R32-V4-PREPARATION-LIST-CORRECTED.md in this package", "PILOT/declaration-r32-v4/R32-V4-PREPARATION-LIST-CORRECTED.md")
+    d["v4_preparation_items"]["corrected_copy"] = d["v4_preparation_items"]["corrected_copy"].replace(
+        "R32-V4-PREPARATION-LIST-CORRECTED.md in this package", "PILOT/declaration-r32-v4/R32-V4-PREPARATION-LIST-CORRECTED.md")
+    pre = {k: v for k, v in d["preconditions"].items() if k != "no_v4_run_folder"}
+    pre["ledger_baseline"] = "ledger_baseline (484 / 18 / 0 at freeze; no v4 or v5 scope)"
+    pre["owner_conditional_decision"] = ("owner_conditional_decision (A-13 item 3, verbatim, carried as HISTORY: lapsed; a fresh owner D1/D2 naming "
+                                         "the v5 hash is required: owner_decision_required)")
+    pre["no_v5_run_folder"] = f"{run_folder} must not exist before the owner's first invocation"
+    pre["v4_artifacts_untouched"] = ("the superseded v4 package (PILOT/declaration-r32-v4) is never edited, authorized or run; its stamp r32-v4, run "
+                                     "folder and scope were never created and are never created")
+    d["preconditions"] = pre
+    te = d["test_exceptions"]["test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests"]
+    te["carried_to_v5"] = ("Verification 45 R45-10: the exception persists on the review45 harness (its full suite from a byte copy: 549 run, 548 "
+                           "passed, 1 failed = this test, on the owner's committed v3 file); carried unchanged; any other failure of the test is "
+                           "not covered")
+    d["resume_authorization"]["implementation"]["guard"] = modules["dispatch_guard_r32"]
+    reads = "; ".join(f"{n}. {who}: {what}" for n, (who, what) in enumerate(DRILL_READS, 1))
+    first_read = (
+        "first read (R34-18, amended for v5; Verification 45 R45-06 and R45-07): the application (lane B, baseline frozen-r13 at 7ec3d2cf) "
+        "processes the real run-set PDFs for the first time in a v5 live B run, with two disclosed exceptions. (1) F009, F020 and F030 (EP-27331; "
+        "staged sha256 970ddb0f...b415, 599d36be...91db, feec64cd...010a) were processed offline beforehand by the same lane-B code path in the "
+        f"review45 dry baseline-facts drill (runner_r32.py --dry-baseline-facts; AI off; the refusing global provider; 0 model requests), "
+        f"{len(DRILL_READS)} times before this declaration was frozen: {reads}; any drill run by Verification 46 or later adds to this count and "
+        "must be stated by whoever runs it; the agents that saw the per-row outcomes (the R43-42 implementer, Verification 45 and the R43-44 "
+        "implementer, all Claude Opus 5.5) are exposed agents. (2) The executed v3 live run (2026-10-07; lane B on the earlier baseline "
+        f"frozen-r12) processed {len(V3_LIVE_B_READ)} of the 24 run-set documents before its terminal stop ({', '.join(V3_LIVE_B_READ)}), with "
+        "tripwire outcomes and one model form reading (F035) seen by the owner and agents; 14 of the 21 run-set documents outside the drill were "
+        f"therefore already read by the application (an earlier baseline) before any v5 live run, and only {', '.join(ev['never_read'])} "
+        f"({len(ev['never_read'])} documents) have never been read by the application. Declaration v4's first-read disclosure omitted (2) (R45-06)")
+    dry = (
+        "the dry exercise of this declaration runs byte copies of the review45 harness (dry base C:/t/r2x/r42-sandbox/r45q/sb, driver side) with "
+        "reader 'none' and the refusing stub: it exercises the chain and the scorer and is not a result; the bound harness's dry mode never runs "
+        "an application reader on a cohort document except in the dry-only baseline-facts drill (--dry-baseline-facts: lane B, frozen-r13, "
+        "exactly F009, F020 and F030, AI off, 0 requests; refused in live mode, in C, R and P, and on any other document, tree or flag); the drill "
+        "is the only real-facts rehearsal and is disclosed with its criterion and result")
+    rep = {
+        "the first processing of the real cohort PDFs by the application happens in live B": first_read,
+        "the dry exercise of this declaration runs byte copies of the review43 harness": dry,
+        "isolation: every lane refuses an environment value": (
+            "isolation: every lane refuses an environment value, setting, import path or loaded module under the merged installation except the "
+            "bound venv and the review45 harness folder; inherited operating-system variables are checked, not replaced (isolation_detail)"),
+        "ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v4 freeze": (
+            "ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v5 freeze, as at the v4 freeze (the v3 scope present; no v4 "
+            "or v5 scope); the runtime harness does not read that pin"),
+        "test exception (R43V-05):": (
+            "test exception (R43V-05, carried; Verification 45 R45-10): test_no_authorization_file_was_written_by_the_tests fails on the owner's "
+            "committed v3 authorization file (test_exceptions); declared, not fixed, the file never removed; it persists on the review45 harness")}
+    dis = list(d["disclosures"])
+    done = set()
+    for i, x in enumerate(dis):
+        for start, new in rep.items():
+            if x.startswith(start):
+                dis[i] = new
+                done.add(start)
+    if done != set(rep):
+        raise C.PacketMismatch(f"disclosures not found for replacement: {sorted(set(rep) - done)}")
+    per_doc = drill["per_document"]
+    dis += [
+        ("harness rebind (Verification 44 option 1; Verification 45): v5 binds the review45 harness (BINDING-MANIFEST-R45-HARNESS 9af8e07a...9ffb), "
+         "which is the review43 harness bound by v4 plus a dry-only baseline-facts drill; 71 of 85 script files are byte-identical, runner_r32.py "
+         "(+9/-2) and lane_r32.py (+53/-10) change only in guarded drill branches, drill_r45.py and test_dry_baseline_drill_r45.py are new; the "
+         "judge, tripwire, labels, page relations, preflight, run control, allowance, dispatch guard, stop rules, scoring and model identity are "
+         "byte-identical; live mode refuses the drill flag; v4 (e0a93c46...fbeb9) is superseded, never authorized and never run"),
+        ("the baseline-facts drill (review45): mode runner_r32.py run --mode dry --dry-baseline-facts SPEC.json, lane B only, tree "
+         "C:/t/iso/frozen-r13 only, exactly F009, F020 and F030 by pool id and staged sha256, the lane's own B code path (document_processing.run "
+         "with the lane's process / read_form_or_raise / apply_form_reading hooks, row_dict, b_tripwire -> tripwire_r32 -> lane_judge_r32, rule "
+         "CP-R38), after_document and final against the resolved truth 4e237a4e...e064; AI off and the refusing global provider; it never "
+         "touches run state, allowance, capture store, AI ledger, scope, authorization, nonce, token or RUN file and writes only "
+         "<sandbox base>/r32-drill-<stamp>"),
+        (f"drill criterion and result: DRILL-CRITERION.md sha256 {C.DRILL_CRITERION_SHA} (logged R43-65 before any drill code ran on any "
+         "document): PASS iff, for each of F009, F020 and F030, no critical acceptance on resolved truth in identity, revision or decision in any "
+         "tripwire evaluation, the v3 stop condition does not fire, each document is exercised and zero requests; a FAIL is reported, never "
+         "fixed. Result: PASS, 0 criticals, 0 requests, in the review45 evidence run (F009 COMPLETE submittal_form 19 facts, F020 COMPLETE "
+         "submittal_form 21, F030 COMPLETE document 18), reproduced by Verification 45 and reproduced once more by task R43-44 on v5's bindings "
+         f"(--binding BINDING-MANIFEST-R45-HARNESS, 629 files verified): {drill['criterion']}, F009 {per_doc['F009']['facts_final']}, F020 "
+         f"{per_doc['F020']['facts_final']}, F030 {per_doc['F030']['facts_final']} facts, {drill['resolved_criticals']} resolved and "
+         f"{drill['unresolved_criticals']} unresolved criticals, {drill['requests_total']} requests; facts equal to the review45 evidence run "
+         f"after normalising times and sandbox paths: {'yes' if drill['facts_equal'] else 'NO'}; the comparison stayed PENDING; the result is a "
+         "deterministic baseline reading, not an accuracy figure"),
+        ("AI-on limit (Verification 45 R45-08): for F009 and F020 (role submittal_form) the live application asks the model for the form reading "
+         "after the deterministic pass; apply_form_reading can set the reference, revision or status and add a log record, after which the lane "
+         "re-runs after_document and final; a wrongly read page-1 reference, revision or code would be a resolved critical and the v3 stop rule "
+         "would end the run; the drill judged the deterministic reading only (the row the live after_document tripwire judges first) and does not "
+         "rehearse the model's later form reading, which it cannot do without a model request; F030 (role document) has no form reading"),
+        ("drill limits: three documents of one project (only F009, F020 and F030 were registered in the drill's EP-27331 sandbox; the other "
+         "EP-27331 run-set documents F021, F032 and F037 were absent, so sibling effects are not reproduced); 21 of the 24 run-set documents are "
+         "not rehearsed (covering all 24 needs authority beyond A-13 item 2); AI off; the installed Tesseract was available (no document UNREAD); "
+         "no accuracy, coverage or eligibility claim follows, and nothing is shown about lanes C, R or P"),
+        ("pre-run exposure (R44-12, extended by the drill): the R43 grammar work judged identity facts of F009, F020, F030 and F021 on pages 3-4 "
+         "against the v3 truth (R43-REVIEW-PACKAGE/R43-HARNESS-JUDGE-OUTPUT.json); the drill judged the baseline's complete deterministic facts "
+         "of F009, F020 and F030 (all pages; identity, revision and decision) against the resolved truth and the per-row outcomes were seen by "
+         "the exposed agents named in the first-read disclosure; the criterion was fixed before; no code, grammar, label, truth or criterion "
+         "changed after the facts were seen; label-blindness is preserved in substance only on that basis, and any later change to the "
+         "baseline, the labels or the truth needs a new declaration with this disclosure"),
+        ("A-13 item 3 (owner_conditional_decision) is carried as history only: it named a v4 live run 'tonight', its condition (b) was not met "
+         "for v4, and it lapsed; it is not a precondition that v5 can satisfy; a fresh owner D1/D2 naming the v5 hash is required "
+         "(owner_decision_required, the check-8 steps of Verification 45)")]
+    d["disclosures"] = dis
+    fb = list(d["forbidden_after_authorization"])
+    old_fb = "running the review42 harness or any harness other than PILOT/review43/scripts/harness-r32 for v4"
+    if old_fb not in fb:
+        raise C.PacketMismatch("the v4 harness prohibition was not found")
+    fb[fb.index(old_fb)] = "running the review42 or review43 harness or any harness other than PILOT/review45/scripts/harness-r32 for v5"
+    d["forbidden_after_authorization"] = fb + [
+        "using the superseded declaration v4 e0a93c46...fbeb9, its stamp r32-v4, its run folder or its scope for anything but the record",
+        "passing --dry-baseline-facts or any other dry drill flag to a live invocation (the runner refuses it)"]
+    d["bound_files_rehashed"] = {"rule": ("every {path, sha256} node of this declaration was re-hashed at build time and equals; v4's carried nodes "
+                                          "equal v4's hashes (re-pointed nodes: the review45 harness files at their new paths take "
+                                          "BINDING-MANIFEST-R45-HARNESS's hashes)"),
+                                 "v4_nodes_equal": ev["v4_nodes_equal"], "harness_nodes_rebound": rebound}
+    return d
+
+
+def evidence_v5() -> dict:
+    full = json.loads((C.REVIEW45 / "tests/full/SUMMARY.json").read_text(encoding="utf-8"))
+    new = json.loads((C.REVIEW45 / "tests/new/SUMMARY.json").read_text(encoding="utf-8"))
+    v4nodes = bound_nodes(json.loads(v4_bytes().decode("utf-8")))
+    eq = sum(1 for _jp, p, s in v4nodes if C.sha256_file(p) == s)
+    dv = C.PACKAGE / "evidence/drill-v5"
+    rep = json.loads((dv / "out/DRILL-REPORT.json").read_text(encoding="utf-8"))
+    cmp_ = json.loads((dv / "DRILL-COMPARE-V5.json").read_text(encoding="utf-8"))
+    req = rep["requests"]
+    per = {p: {"facts_final": v.get("facts_final"), "resolved": len(v.get("resolved_criticals") or []), "unresolved": len(v.get("unresolved_criticals") or [])}
+           for p, v in rep["per_document"].items()}
+    run_set = json.loads(C.RUN_SET.read_text(encoding="utf-8"))["documents"]
+    never = [x["pool_id"] for x in run_set if x["pool_id"] not in DRILL_DOCS and x["pool_id"] not in V3_LIVE_B_READ]
+    return {
+        "global_provider_tests_r45": full["modules"].get("test_global_provider_r42"),
+        "drill_tests_r45": new["modules"].get("test_dry_baseline_drill_r45"),
+        "v4_nodes_equal": f"{eq} of {len(v4nodes)} (v4's nodes at v4's paths)",
+        "never_read": never,
+        "drill_v5": {"criterion": rep["criterion"]["result"], "binding_sha256": rep["binding"]["sha256"], "per_document": per,
+                     "resolved_criticals": sum(v["resolved"] for v in per.values()), "unresolved_criticals": sum(v["unresolved"] for v in per.values()),
+                     "requests_total": int(req.get("refusing_provider_calls") or 0) + int(req.get("dry_stub_calls") or 0) + int(req.get("model_requests") or 0)
+                     + int(req.get("provider_complete_calls_traced") or 0) + len(req.get("live_provider_attempts_blocked") or []),
+                     "facts_equal": cmp_["facts_equal_after_normalising"]}}
+
+
 def main(argv=None) -> int:
@@ -812,13 +1160,13 @@
     import subprocess  # noqa: F401
-    binding_sha = C.sha256_file(C.BINDING43)
-    man = json.loads(C.BINDING43.read_text(encoding="utf-8"))
+    binding_sha = C.sha256_file(C.BINDING45)                         # R43-44: the review45 harness manifest and group
+    man = json.loads(C.BINDING45.read_text(encoding="utf-8"))
     bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
     if bad:
-        raise C.PacketMismatch(f"PACKET MISMATCH: harness files differ from BINDING-MANIFEST-R43-HARNESS: {bad[:3]}")
+        raise C.PacketMismatch(f"PACKET MISMATCH: harness files differ from BINDING-MANIFEST-R45-HARNESS: {bad[:3]}")
     C.check_run_copy()
     led = C.ledger_state()
-    if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"]:
-        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led['entries']}/{led['scopes']}/{led['limit_amendments']} (expected 484/18/0 and no scope {C.SCOPE!r})")
-    if C.RUN_FOLDER.exists():
-        raise C.PacketMismatch(f"refused: the run folder {C.RUN_FOLDER.as_posix()} already exists")
+    if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"] or C.V4_SCOPE in led["scope_names"]:
+        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led['entries']}/{led['scopes']}/{led['limit_amendments']} (expected 484/18/0 and no scope {C.SCOPE!r} or {C.V4_SCOPE!r})")
+    if C.RUN_FOLDER.exists() or C.V4_RUN_FOLDER.exists():                # R43-44
+        raise C.PacketMismatch(f"refused: the run folder {C.RUN_FOLDER.as_posix()} (or r32-v4) already exists")
     for repo, head in (C.CANDIDATE, C.BASELINE):
@@ -828,3 +1176,3 @@
     declared_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
-    decl = build_v4(declared_at, evidence_v4())   # R43-40: v4 from the frozen v3 bytes
+    decl = build_v5(declared_at, evidence_v5())   # R43-44: v5 from the frozen v4 bytes (build_v4 kept, not called)
     rh = rehash_all(decl)
@@ -835,3 +1183,3 @@
         raise RuntimeError("a Desktop path survived the re-pointing")
-    import preflight_r32 as PF  # noqa: E402  (review43; R43-40: HERE = the bound folder, C.declared_here)
+    import preflight_r32 as PF  # noqa: E402  (review45; R43-40 / R43-44: HERE = the bound folder, C.declared_here)
     C.declared_here(PF)
```

### `cli_version_drill_r42.py`

```diff
--- declaration-r32-v4/scripts/cli_version_drill_r42.py
+++ declaration-r32-v5/scripts/cli_version_drill_r42.py
@@ -26,4 +26,4 @@
 folder = C.DRY_BASE / stamp                         # R43-40: dry base C:/t/r2x/r42-sandbox/r43p/sb; the review43 harness manifest
-args = ["--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING43.as_posix(),
-        "--binding-sha", C.sha256_file(C.BINDING43)]
+args = ["--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING45.as_posix(),
+        "--binding-sha", C.sha256_file(C.BINDING45)]   # R43-44: the review45 harness manifest
 steps = []
```

### `create_scope_r42.py`

```diff
--- declaration-r32-v4/scripts/create_scope_r42.py
+++ declaration-r32-v5/scripts/create_scope_r42.py
@@ -10,3 +10,3 @@
       R34_OWNER_DISPATCH_TOKEN. Refuses (creating nothing) unless, in this order:
-        1. the owner's authorization file exists at the pinned path PILOT/declaration-r32-v4/OWNER-DISPATCH-AUTHORIZATION.json;
+        1. the owner's authorization file exists at the pinned path PILOT/declaration-r32-v5/OWNER-DISPATCH-AUTHORIZATION.json (R43-44);
         2. --frozen-sha equals the frozen declaration file's sha256 and DECLARATION.sha256;
@@ -18,3 +18,3 @@
         5. the run folder does not exist (the scope is created once, before the first invocation; never for a resume);
-        6. the bound harness verifies (BINDING-MANIFEST-R43-HARNESS, every bound file) and the RUN declaration passes contract 5;
+        6. the bound harness verifies (BINDING-MANIFEST-R45-HARNESS, every bound file; R43-44) and the RUN declaration passes contract 5;
         7. ORCH-10: the bound interpreter runs this command, the pinned CLI FILE hashes to the declared sha256 (read as
@@ -54,3 +54,3 @@
 def harness():
-    man = json.loads(C.BINDING43.read_text(encoding="utf-8"))          # R43-40: the review43 harness manifest and group
+    man = json.loads(C.BINDING45.read_text(encoding="utf-8"))          # R43-44: the review45 harness manifest and group
     bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
@@ -103,3 +103,3 @@
         "5 run folder absent": {"path": C.RUN_FOLDER.as_posix(), "absent": not C.RUN_FOLDER.exists()},
-        "6 bound harness and contract 5": {"state": "checked in create mode (verify_binding R43 harness manifest; validate_declaration on the RUN file)"},
+        "6 bound harness and contract 5": {"state": "checked in create mode (verify_binding R45 harness manifest; validate_declaration on the RUN file)"},
         "7 interpreter, CLI file, free disk": {"interpreter": decl["interpreter"]["path"], "cli_file": decl["model_identity"]["cli"]["path"],
@@ -132,3 +132,3 @@
     rsha = C.sha256_bytes(run_bytes)
-    if run_sha_given in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA):     # R43-40: never a frozen or the executed v3 hash
+    if run_sha_given in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA, C.V4_SHA):     # R43-40 / R43-44: never a frozen or the executed v3 hash
         raise ScopeRefused("refused: the RUN hash given is a FROZEN hash (a frozen declaration is never used with the runner or the scope)")
@@ -145,3 +145,3 @@
     DG, PF = harness()
-    if isinstance(auth, dict) and str(auth.get("declaration_sha256") or "") in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA):   # R43-40
+    if isinstance(auth, dict) and str(auth.get("declaration_sha256") or "") in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA, C.V4_SHA):   # R43-40 / R43-44
         raise ScopeRefused("refused: the authorization names a FROZEN hash; it must name the RUN hash")
@@ -155,3 +155,3 @@
         try:
-            PF.verify_binding(C.BINDING43, run_decl.get("binding_manifest_sha256"))   # R43-40
+            PF.verify_binding(C.BINDING45, run_decl.get("binding_manifest_sha256"))   # R43-44
         except PF.Refused as exc:
```

### `demos_r42.py`

```diff
--- declaration-r32-v4/scripts/demos_r42.py
+++ declaration-r32-v5/scripts/demos_r42.py
@@ -1,2 +1,4 @@
-"""R43-40: the same demonstrations on the review43 harness for declaration-r32-v4 (byte copy checked against its binding;
+"""R43-44: the same demonstrations on the review45 harness for declaration-r32-v5 (byte copy checked against BINDING-MANIFEST-R45-HARNESS;
+run folders under the dry base C:/t/r2x/r42-sandbox/r45q/sb; stamps r45q-*).
+R43-40: the same demonstrations on the review43 harness for declaration-r32-v4 (byte copy checked against its binding;
 run folders under the dry base C:/t/r2x/r42-sandbox/r43p/sb, substitution S-BASE; stamps r43d-*; one more refusal case:
@@ -156,3 +158,3 @@
         rs = run_set(work, ids)
-        self.stamp = f"r43d-demo-{uuid.uuid4().hex[:8]}"
+        self.stamp = f"r45q-demo-{uuid.uuid4().hex[:8]}"
         self.args = ["--mode", "dry", "--stamp", self.stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha]
@@ -184,3 +186,3 @@
         led = H.fake_ledger(work / "fake-ledger.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0)})
-        self.stamp = f"r43d-demo-live-{uuid.uuid4().hex[:8]}"
+        self.stamp = f"r45q-demo-live-{uuid.uuid4().hex[:8]}"
         self.decl, self.dsha, self.rec = H.live_declaration(work / "pkg", binding_sha=sha, run_set_sha=hashlib.sha256(rs.read_bytes()).hexdigest(),
@@ -521,5 +523,5 @@
     OUT.mkdir(parents=True)
-    work = RN.SANDBOX_BASE / f"r43d-demos-{uuid.uuid4().hex[:6]}"
+    work = RN.SANDBOX_BASE / f"r45q-demos-{uuid.uuid4().hex[:6]}"
     led0 = PF.ledger_counts(LEDGER)
-    res = {"name": "DEMOS (R43-40) of the review43 harness for declaration-r32-v4 (the ORCH-10 section 2.6 demonstrations)", "harness": C.HARNESS43.as_posix(),
+    res = {"name": "DEMOS (R43-44) of the review45 harness for declaration-r32-v5 (the ORCH-10 section 2.6 demonstrations)", "harness": C.HARNESS45.as_posix(),
            "imported_from": H_DIR.as_posix(), "run_copy": COPY, "dry_base": BASE, "work": work.as_posix(), "ledger_before": led0,
```

### `diff_declaration_r42.py`

```diff
--- declaration-r32-v4/scripts/diff_declaration_r42.py
+++ declaration-r32-v5/scripts/diff_declaration_r42.py
@@ -1,2 +1,5 @@
-"""R43-40: every difference between the executed v3 declaration (9a55fa7b...1b40) and the v4 declaration of this package,
+"""R43-44: main_v5() -- every difference between the frozen v4 declaration (e0a93c46...fbeb9) and the v5 declaration of this
+package, in the same leaf form, with the one R43-44 re-point (review43/scripts/harness-r32 -> review45/scripts/harness-r32) and the
+review45 manifest's hashes; writes DECLARATION-DIFF-V4-V5.json and DECLARATION-DIFF-V4-V5.md (once each). main_v4 is kept, not run.
+R43-40: every difference between the executed v3 declaration (9a55fa7b...1b40) and the v4 declaration of this package,
 mechanically (the v2 -> v3 method of ORCH-10, below, with the R43 re-point in place of the Desktop re-point). Each leaf is:
@@ -113,3 +116,3 @@
 
-def main(argv=()) -> int:
+def main_v4(argv=()) -> int:
     v4_path, out_dir = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE                 # dev mode: --v4 <file> --out <work dir>
@@ -200,4 +203,139 @@
 
+# ---- R43-44: v4 -> v5 (the R42 leaf-diff form) ------------------------------------------------------------------------------
+REASONS_V5 = {
+    "schema": "the v5 schema id", "name": "names declaration v5 (R43 trees, review45 harness)",
+    "task": "R43-44 (A-13 item 2; Verification 44 option 1; Verification 45 section 5 item 2), ep-implementer",
+    "supersedes": "supersedes v4 e0a93c46...fbeb9 (frozen, never authorized, never run; its manifest named; the review43 binding superseded by the review45 manifest 9af8e07a...) plus the chain (v4, v3, v3 RUN, v2); v4's own supersedes record kept as lineage",
+    "declared_at_utc": "the time of this freeze",
+    "status": "Verification 46, the owner's option-1 choice with the restated (b) and a fresh D1/D2 pending",
+    "authorities": "the authority register re-hashed at its current (append-only) state",
+    "binding_manifest_sha256": "harness rebind: BINDING-MANIFEST-R45-HARNESS (review45, 9af8e07a...9ffb) instead of BINDING-MANIFEST-R43-HARNESS",
+    "run": "new stamp r32-v5 and run folder C:/t/r2x/r42-sandbox/r32-v5 (allowance, capture store, run state under it); the dry-base sentence (r45q)",
+    "authorization": "pinned authorization path, RUN file and scope of v5 in the budget-authorization names; invocation from review45 with its manifest (run, working_directory, harness_copy); runbook pointer RUNBOOK-R32-V5.md",
+    "provider_env": "AI_LEDGER_SCOPE = the v5 scope; every other value unchanged", "ledger": "the v5 scope name; path and limits unchanged",
+    "ledger_detail": "the creation sentence names task R43-44 and 'no v4 or v5 scope'", "isolation": "harness rebind: the review45 harness folder",
+    "harness": "harness rebind: review45 (binding and package manifest, package check, accepted_by Verification 45, modules re-pointed and rebound incl. the new drill_r45, drill contracts, review43 added to the lineage)",
+    "request_path_coverage": "harness rebind: the dynamic proof re-pointed to review45's tests/full junit; the drill files covered (drill_r45)",
+    "reviews": "Verifications 44 and 45 (verification, findings, package check) added",
+    "provider": "owner-confirmable: the v5 scope", "resume_authorization": "the guard module re-pointed to review45 (same bytes)",
+    "disclosures": "corrected first read (R45-06, R45-07, the R34-18 three-document exception, read count 5), dry exercise / isolation / ledger / test-exception disclosures restated for review45 and v5, seven added (harness rebind, drill, criterion and result, AI-on limit R45-08, drill limits, pre-run exposure, A-13 item 3 lapsed)",
+    "forbidden_after_authorization": "the harness prohibition re-pointed to review45; two items added (the superseded v4; a dry drill flag in a live invocation)",
+    "bound_files_rehashed": "the v5 re-hash record (v4 nodes; rebound review45 harness nodes)",
+    "owner_conditional_decision": "A-13 item 3 carried as HISTORY (verbatim unchanged): carried_as and status_at_v5_freeze (lapsed; a fresh D1/D2 required) added",
+    "owner_decision_required": "ADDED: exactly the six check-8 steps of Verification 45 section 5, with their status at this freeze and the restated (b)",
+    "ledger_baseline": "re-read at this freeze (484 / 18 / 0 unchanged; v5 scope absent added; the rule restated for the v5 copies)",
+    "preconditions": "no_v4_run_folder replaced by no_v5_run_folder; v4 artefacts untouched added; ledger and conditional-decision pointers restated; pip freeze unchanged",
+    "test_exceptions": "the R43V-05 exception carried; carried_to_v5 (Verification 45 R45-10) added",
+    "trees_r43": "pointer: the corrected V4-05 list is in PILOT/declaration-r32-v4 (not in this package); commits unchanged",
+    "v4_preparation_items": "pointer: the corrected list is in PILOT/declaration-r32-v4 (not in this package)",
+}
+OLD_IDS_V5 = re.compile(r"review43/scripts/harness-r32|f35355aa|r32-v4|declaration-r32-v4|R32-V4|m2-fresh-validation-r32-v4|r43p|r43d")
+RECORD_KEYS_V5 = RECORD_KEYS + ("v4_preparation_items", "standing_status_at_v4_freeze", "owner_decision_required", "harness.binding_manifest.supersedes",
+                                "harness.accepted_by", "status")
+
+
+def main_v5(argv=()) -> int:
+    v5_path, out_dir = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE
+    names = ("DECLARATION-DIFF-V4-V5.json", "DECLARATION-DIFF-V4-V5.md")
+    for f in names:
+        if (out_dir / f).exists():
+            raise SystemExit(f"refused: {f} is written once")
+    old_b, new_b = BD.v4_bytes(), v5_path.read_bytes()
+    old, new = json.loads(old_b), json.loads(new_b)
+    bound = json.loads(C.BINDING45.read_text(encoding="utf-8"))["files"][C.HARNESS_GROUP]
+    fo, fn = flat(old), flat(new)
+    leaves = {"unchanged": [], "repointed": [], "rebound": [], "changed": [], "added": [], "removed": []}
+    for k in sorted(set(fo) | set(fn)):
+        if k not in fn:
+            leaves["removed"].append(k)
+        elif k not in fo:
+            leaves["added"].append(k)
+        elif fo[k] == fn[k]:
+            leaves["unchanged"].append(k)
+        elif BD.repoint45(fo[k]) == fn[k]:
+            leaves["repointed"].append(k)
+        elif k.endswith(".sha256") and fn.get(k[:-7] + ".path") in bound and bound[fn[k[:-7] + ".path"]] == fn[k] \
+                and BD.repoint45(fo.get(k[:-7] + ".path")) == fn[k[:-7] + ".path"]:
+            leaves["rebound"].append(k)
+        else:
+            leaves["changed"].append(k)
+    tops = {}
+    for k in sorted(set(old) | set(new)):
+        mine = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
+        rep = [x for cat in ("repointed", "rebound") for x in leaves[cat] if x == k or x.startswith(k + ".")]
+        state = ("added" if k not in old else "removed" if k not in new else "changed" if mine else "repointed / rebound only" if rep else "unchanged")
+        tops[k] = {"state": state, "reason": REASONS_V5.get(k, "unchanged" if state == "unchanged" else
+                                                            "only the review45 harness re-point (and the harness manifest's hashes)" if state.startswith("repointed") else "SEE LEAVES"),
+                   "leaves_changed": sorted(mine), "leaves_repointed_or_rebound": len(rep)}
+    prot = {}
+    for k in PROTECTED_KEYS + PROTECTED_LEAVES:
+        bad = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
+        prot[k] = {"ok": not bad, "violations": bad}
+    unexplained = [k for k, v in tops.items() if v["state"] in ("changed", "added", "removed") and k not in REASONS_V5]
+    counts = {s: sum(1 for v in tops.values() if v["state"] == s) for s in ("unchanged", "repointed / rebound only", "changed", "added", "removed")}
+    olds = [(p, sorted(set(OLD_IDS_V5.findall(s)))) for p, s in strings(new) if OLD_IDS_V5.search(s)]
+    outside = [(p, ids) for p, ids in olds if not any(p == r or p.startswith(r + ".") or p.startswith(r + "[") for r in RECORD_KEYS_V5)]
+    tt = {"trees": new["trees"], "lanes": {k: {x: v.get(x) for x in ("tree", "commit")} for k, v in new["lanes"].items()},
+          "evaluator_file": new["evaluator"]["file"]}
+    tt["ok"] = (new["trees"]["baseline"]["tree"] == C.BASELINE[0] and new["trees"]["baseline"]["head"] == C.BASELINE[1]
+                and new["trees"]["candidate"]["tree"] == C.CANDIDATE[0] and new["trees"]["candidate"]["head"] == C.CANDIDATE[1]
+                and all(v.get("tree") in (None, C.BASELINE[0], C.CANDIDATE[0]) for v in new["lanes"].values())
+                and all(v.get("commit") in (None, C.BASELINE[1], C.CANDIDATE[1]) for v in new["lanes"].values())
+                and new["evaluator"]["file"]["path"].startswith(C.CANDIDATE[0] + "/") and new["trees"] == old["trees"] and new["lanes"] == old["lanes"])
+    ident = {"stamp": new["run"]["stamp"], "folder": new["run"]["folder"], "scope": new["ledger"]["scope"],
+             "AI_LEDGER_SCOPE": new["provider_env"]["AI_LEDGER_SCOPE"], "authorization_path": new["authorization"]["path"],
+             "run_file": new["authorization"]["two_hash_procedure"]["run_file"], "binding_manifest_sha256": new["binding_manifest_sha256"],
+             "isolation_harness": new["isolation"]["allowed_under_forbidden"]["harness"]}
+    ident["ok"] = (ident["stamp"] == C.STAMP and ident["folder"] == C.RUN_FOLDER.as_posix() and ident["scope"] == C.SCOPE == ident["AI_LEDGER_SCOPE"]
+                   and ident["authorization_path"] == (C.PACKAGE / C.AUTH_NAME).as_posix() and ident["run_file"] == (C.PACKAGE / C.RUN_NAME).as_posix()
+                   and ident["binding_manifest_sha256"] == C.BINDING45_SHA and ident["isolation_harness"] == C.HARNESS45.as_posix())
+    res = {"v4": {"path": (C.V4 / C.V4_NAME).as_posix(), "sha256": C.V4_SHA}, "v5": {"path": v5_path.as_posix(), "sha256": C.sha256_bytes(new_b)},
+           "method": ("R43-44: both files flattened to leaf paths (dicts recursed, lists compared whole); a leaf is unchanged (byte-equal value), "
+                      "repointed (equal once the one R43-44 re-point review43/scripts/harness-r32 -> review45/scripts/harness-r32 is applied; "
+                      "nothing else), rebound (the sha256 of a {path, sha256} node re-pointed to a review45 harness file, equal to the hash "
+                      "BINDING-MANIFEST-R45-HARNESS binds), changed, added or removed (an item of task R43-44, each top-level key with its "
+                      "reason). The protected values of v4 (the same list as the v3 -> v4 diff) must be unchanged, repointed or rebound only; "
+                      "exit 3 otherwise. Strings of v5 still naming a v4 identifier are listed; outside the record keys none may remain."),
+           "top_level_counts": counts, "leaf_counts": {k: len(v) for k, v in leaves.items()},
+           "top_level": tops, "leaves": leaves, "protected": prot, "protected_all_ok": all(v["ok"] for v in prot.values()),
+           "unexplained_top_level_changes": unexplained,
+           "old_identifiers_in_v5": {"count": len(olds), "in_record_keys": len(olds) - len(outside), "outside_record_keys": outside, "all": olds},
+           "trees_text_check": tt, "new_identifiers_check": ident}
+    res["ok"] = res["protected_all_ok"] and not unexplained and not outside and tt["ok"] and ident["ok"]
+    C.write_json_once(out_dir / names[0], res)
+    L = ["# DECLARATION-DIFF-V4-V5: v4 (`e0a93c46...fbeb9`, frozen, never authorized, never run) -> v5 (this package)", "",
+         f"- v5 sha256: `{res['v5']['sha256']}`.",
+         "- Method (the R42 leaf-diff form): both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the R43-44 re-point "
+         "`review43/scripts/harness-r32`->`review45/scripts/harness-r32`), rebound (the sha256 of a re-pointed review45 harness file, equal to the "
+         "hash BINDING-MANIFEST-R45-HARNESS binds), changed, added or removed.", f"- Top-level keys: {counts}.", f"- Leaves: {res['leaf_counts']}.",
+         f"- **Protected values (every number and rule that must not change): {'ALL UNCHANGED (or re-pointed / rebound only)' if res['protected_all_ok'] else 'VIOLATED'}** "
+         f"({len(prot)} keys and leaves checked).",
+         f"- Trees in text: {'frozen-r13 7ec3d2cf / cand-r30n 436daef2 in trees, lanes and evaluator, equal to v4' if tt['ok'] else 'NOT OK'}.",
+         f"- New identifiers: {'stamp r32-v5, folder, scope, AI_LEDGER_SCOPE, pinned authorization and RUN paths, binding 9af8e07a..., isolation harness review45' if ident['ok'] else 'NOT OK'}.",
+         f"- v4 identifiers left in v5: {len(olds)}, {len(olds) - len(outside)} inside record keys, {len(outside)} outside.",
+         f"- Result: {'OK' if res['ok'] else 'NOT OK'}.", "",
+         "## Top-level keys", "", "| Key | State | Reason |", "|---|---|---|"]
+    for k, v in tops.items():
+        L.append(f"| `{k}` | {v['state']} | {v['reason']} |")
+    L += ["", "## Protected keys and leaves (all must be unchanged, re-pointed or rebound)", ""]
+    L += [f"- `{k}`: {'ok' if v['ok'] else 'VIOLATED ' + ', '.join(v['violations'])}" for k, v in prot.items()]
+    L += ["", "## Changed, added and removed leaves", ""]
+    for cat in ("changed", "added", "removed"):
+        L.append(f"### {cat} ({len(leaves[cat])})")
+        L.append("")
+        L += [f"- `{x}`" for x in leaves[cat]] or ["- none"]
+        L.append("")
+    L += [f"### repointed ({len(leaves['repointed'])}) and rebound ({len(leaves['rebound'])})", ""]
+    L += [f"- `{x}` (rebound)" for x in leaves["rebound"]] + [f"- `{x}`" for x in leaves["repointed"]]
+    L += ["", "## v4 identifiers left in v5 (JSON path: identifiers; all inside record keys)", ""]
+    L += [f"- `{p}`: {', '.join(ids)}" for p, ids in olds] or ["- none"]
+    C.write_once(out_dir / names[1], "\n".join(L) + "\n")
+    print(json.dumps({"ok": res["ok"], "top_level_counts": counts, "leaf_counts": res["leaf_counts"], "protected_all_ok": res["protected_all_ok"],
+                      "violations": {k: v["violations"] for k, v in prot.items() if not v["ok"]}, "unexplained": unexplained,
+                      "old_identifiers_outside_record_keys": outside, "trees_text_ok": tt["ok"], "identifiers_ok": ident["ok"]}, indent=1))
+    return 0 if res["ok"] else 3
+
+
 if __name__ == "__main__":
-    sys.exit(main(sys.argv[1:]))
-
+    sys.exit(main_v5(sys.argv[1:]))
+
```

### `dry_exercise_r42.py`

```diff
--- declaration-r32-v4/scripts/dry_exercise_r42.py
+++ declaration-r32-v5/scripts/dry_exercise_r42.py
@@ -1,2 +1,4 @@
-"""R43-40: the dry-mode exercise of the v4 declaration with the BOUND review43 harness (byte copies; S-BASE dry base).
+"""R43-44: the dry-mode exercise of the v5 declaration with the BOUND review45 harness (byte copies; S-BASE dry base r45q/sb;
+stamps r45q-*); the card reproduces the single 24-document run only: `single <tag>` then `finish-single <tag>`.
+R43-40: the dry-mode exercise of the v4 declaration with the BOUND review43 harness (byte copies; S-BASE dry base).
 ORCH-10 (R42PORT-IMPL): the dry-mode exercise of the v3 declaration with the BOUND review42 harness, unchanged (the
@@ -53,3 +55,3 @@
     argv = [C.PY, "-B", str(HERE / "runner_r43p.py"), cmd, "--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", str(run_set),
-            "--binding", C.BINDING43.as_posix(), "--binding-sha", C.sha256_file(C.BINDING43)] + (["--dry-inject", str(inject)] if inject else [])   # R43-40
+            "--binding", C.BINDING45.as_posix(), "--binding-sha", C.sha256_file(C.BINDING45)] + (["--dry-inject", str(inject)] if inject else [])   # R43-44
     t0 = time.time()
@@ -152,3 +154,3 @@
     led0 = C.ledger_counts()
-    stamp = f"r43d-single-{tag}"
+    stamp = f"r45q-single-{tag}"
     step = runner("run", stamp, C.RUN_SET)
@@ -185,3 +187,3 @@
                                             for d in docs if str(d["ep"]) == ep]})
-        stamp = f"r43d-m{ep}-{tag}"
+        stamp = f"r45q-m{ep}-{tag}"
         step = runner("run", stamp, rs)
@@ -266,3 +268,3 @@
             C.write_json(inj, {"project_window": {"limit": limit, "window_s": 20}, "resume_policy": "full"})
-        loops[name] = deferral_loop(ST, name, f"r43d-{'p' if limit == 10 else 's'}{limit}-{tag}", rs27, inj)
+        loops[name] = deferral_loop(ST, name, f"r45q-{'p' if limit == 10 else 's'}{limit}-{tag}", rs27, inj)
     res = {"checks_before": checks, "declaration_sha256": fsha, "deferral_loops": loops, "ai_ledger_before": led0, "ai_ledger_after": C.ledger_counts(),
@@ -283,3 +285,3 @@
         C.write_json(inj, {"project_window": {"limit": 10, "window_s": 20}, "resume_policy": "full"})
-    lp = deferral_loop(ST, "cross-project-drill-window-10", f"r43d-xp-{tag}", C.RUN_SET, inj)
+    lp = deferral_loop(ST, "cross-project-drill-window-10", f"r45q-xp-{tag}", C.RUN_SET, inj)
     first = json.loads((ST / "cross-project-drill-window-10" / "RUN-REPORT-inv-1.json").read_text(encoding="utf-8"))
@@ -297,6 +299,6 @@
     out = ST / "CLI-VERSION-NOT-A-DEADEND.json"
-    r = subprocess.run([C.PY, "-B", str(HERE / "cli_version_drill_r42.py"), f"r43d-cli-{tag}", str(out)], cwd=str(HERE), env=ENV, capture_output=True,
+    r = subprocess.run([C.PY, "-B", str(HERE / "cli_version_drill_r42.py"), f"r45q-cli-{tag}", str(out)], cwd=str(HERE), env=ENV, capture_output=True,
                        text=True, encoding="utf-8", timeout=3600)
     res = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"error": r.stderr[-2000:]}
-    trim(f"r43d-cli-{tag}")
+    trim(f"r45q-cli-{tag}")
     ok = r.returncode == 0 and res.get("ok") is True
@@ -313,4 +315,4 @@
     leds = [x for p in ph.values() for x in (p["ai_ledger_before"], p["ai_ledger_after"])] + [C.ledger_counts()]
-    res = {"name": "DRY-EXERCISE (R43-40) of declaration-r32-v4 with the bound review43 harness (byte copies)", "tag": tag,
-           "declaration_sha256": ph["single"]["declaration_sha256"], "harness": C.HARNESS43.as_posix(), "imported_from": C.HARNESS42.as_posix(),
+    res = {"name": "DRY-EXERCISE (R43-44) of declaration-r32-v5 with the bound review45 harness (byte copies)", "tag": tag,
+           "declaration_sha256": ph["single"]["declaration_sha256"], "harness": C.HARNESS45.as_posix(), "imported_from": C.HARNESS42.as_posix(),
            "sandbox_base": C.DRY_BASE.as_posix(), "substitution": "S-BASE (r43p_base.py): the dry base inside the work folder",
@@ -350,2 +352,38 @@
 
+def finish_single(tag) -> int:
+    """R43-44: DRY-EXERCISE.json from the single 24-document run only (the split, loop, cross-project and CLI phases are v4's evidence
+    in PILOT/declaration-r32-v4/dry-run and are not re-run: the card asks for the single run)."""
+    if (OUT / "DRY-EXERCISE.json").exists():
+        raise SystemExit("refused: DRY-EXERCISE.json is written once")
+    ST = WORKDRY / f"out-{tag}"
+    single = json.loads((ST / "PHASE-SINGLE.json").read_text(encoding="utf-8"))
+    leds = [single["ai_ledger_before"], single["ai_ledger_after"], C.ledger_counts()]
+    res = {"name": "DRY-EXERCISE (R43-44) of declaration-r32-v5 with the bound review45 harness (byte copies): the single 24-document run",
+           "tag": tag, "declaration_sha256": single["declaration_sha256"], "harness": C.HARNESS45.as_posix(), "imported_from": C.HARNESS42.as_posix(),
+           "sandbox_base": C.DRY_BASE.as_posix(), "substitution": "S-BASE (r43p_base.py): the dry base inside the work folder",
+           "checks_before": single["checks_before"], "single": {k: v for k, v in single.items() if k != "checks_before"},
+           "phases_not_run": {"split, loops, xproject, cli": "not re-run by task R43-44 (card: the single run); v4 evidence, unchanged code paths"},
+           "ai_ledger_snapshots": leds,
+           "ai_ledger_unchanged_484_18_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
+           "model_requests_total": single["model_requests_total"], "live_run_folder_absent": not C.RUN_FOLDER.exists(),
+           "staged_pdf_copies_trimmed": "after the finished dry invocation (WORK out/TRIMMED.jsonl)", "finished_utc": now(),
+           "statement": ("dry exercise only: reader 'none' on the real run set (no application reader touched a cohort document), every request "
+                         "ended at the refusing stub ('dry_refused'), no provider was built, no ledger path, no scope; the scorer figures exercise "
+                         "the scorer and are not results; reference set independently AI-reviewed (Claude agents), not human-signed")}
+    res["ok"] = single["ok"] and res["ai_ledger_unchanged_484_18_0"] and res["model_requests_total"] == 0 and res["live_run_folder_absent"]
+    if not res["ok"]:
+        C.write_json(WORKDRY / f"DRY-EXERCISE-FAILED-{tag}.json", res)
+        raise SystemExit(f"the dry exercise did not complete as expected; see DRY-EXERCISE-FAILED-{tag}.json; nothing was written to the package")
+    for src in sorted(ST.rglob("*")):
+        if src.is_file() and not src.name.startswith("PHASE-"):
+            dst = OUT / src.relative_to(ST)
+            dst.parent.mkdir(parents=True, exist_ok=True)
+            if dst.exists():
+                raise SystemExit(f"refused: {dst} exists")
+            shutil.copyfile(src, dst)
+    sha = C.write_json_once(OUT / "DRY-EXERCISE.json", res)
+    print(json.dumps({"written": sha, "ok": res["ok"], "model_requests_total": res["model_requests_total"]}))
+    return 0
+
+
 if __name__ == "__main__":
@@ -355,3 +393,3 @@
         sys.exit(0)
-    rc = {"single": phase_single, "split": phase_split, "loops": phase_loops, "xproject": phase_xproject, "cli": phase_cli, "finish": finish}[cmd](tag)
+    rc = {"single": phase_single, "split": phase_split, "loops": phase_loops, "xproject": phase_xproject, "cli": phase_cli, "finish": finish, "finish-single": finish_single}[cmd](tag)
     if TRIMMED:
```

### `guard/sitecustomize.py`

```diff
--- declaration-r32-v4/scripts/guard/sitecustomize.py
+++ declaration-r32-v5/scripts/guard/sitecustomize.py
@@ -20,3 +20,6 @@
 the base itself) or be the v4 package folder; anything else is ignored and recorded -- otherwise the defaults
-C:/t/r2x/r42-sandbox/r43p and PILOT/declaration-r32-v4; plus os.devnull. Nothing else is changed in the process."""
+C:/t/r2x/r42-sandbox/r43p and PILOT/declaration-r32-v4; plus os.devnull. Nothing else is changed in the process.
+R43-44 (declaration-r32-v5) copy, three changes: (1) review45 and declaration-r32-v4 are DENIED like the other frozen packages;
+(2) the defaults are C:/t/r2x/r42-sandbox/r45q and PILOT/declaration-r32-v5 (log r45q/guard-log); (3) the package folder accepted
+as a root is the v5 package (the v4 package is never a root). The deny list still applies first."""
 import os
@@ -27,8 +30,8 @@
 _PILOT = "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot"
-_V4 = _PILOT + "/declaration-r32-v4"
-_DEFAULT_ROOTS = [_SANDBOX + "/r43p", _V4]
+_V5 = _PILOT + "/declaration-r32-v5"                                   # R43-44
+_DEFAULT_ROOTS = [_SANDBOX + "/r45q", _V5]
 _ENV_FILE = "g:/dev (2)/dev/ep-platform-merged/ep-platform/backend/.env"
-_LOG = os.environ.get("R43_GUARD_LOG") or "C:/t/r2x/r42-sandbox/r43p/guard-log"
+_LOG = os.environ.get("R43_GUARD_LOG") or "C:/t/r2x/r42-sandbox/r45q/guard-log"
 _DENY = re.compile(r"^(?:c:/t/r2x/r\d{2}-sandbox/r32-v\d+(?:-[^/]*)?(?:/|$)|c:/t/r2x/ledger(?:/|$)|c:/t/iso(?:/|$)|"
-                   + re.escape(_PILOT) + r"/(?:review42|review43|declaration-r32|declaration-r32-v2|declaration-r32-v3)(?:/|$))")
+                   + re.escape(_PILOT) + r"/(?:review42|review43|review45|declaration-r32|declaration-r32-v2|declaration-r32-v3|declaration-r32-v4)(?:/|$))")
 _OWNER_RECORDS = re.compile(r"^c:/t/r2x/r\d{2}-sandbox/r32-v\d+-owner-records(?:/|$)")
@@ -64,3 +67,3 @@
         n = _norm(r.strip()) if r.strip() else ""
-        if n and ((n.startswith(_SANDBOX + "/") and not _DENY.match(n)) or n == _V4):
+        if n and ((n.startswith(_SANDBOX + "/") and not _DENY.match(n)) or n == _V5):
             out.append(n)
```

### `guard_probe_r43p.py`

```diff
--- declaration-r32-v4/scripts/guard_probe_r43p.py
+++ declaration-r32-v5/scripts/guard_probe_r43p.py
@@ -1,2 +1,3 @@
-"""R43-40 (new): probes of the package audit guard (scripts/guard/sitecustomize.py, R43V-10), run under that guard.
+"""R43-44: the v5 guard probes (review45 and declaration-r32-v4 denied, the never-created r32-v4 folder, the v5 package a root).
+R43-40 (new): probes of the package audit guard (scripts/guard/sitecustomize.py, R43V-10), run under that guard.
 Usage: <bound python> -B guard_probe_r43p.py <out json>    (PYTHONPATH = the guard folder; never with R43_GUARD_OWNER_RECORDS)
@@ -38,3 +39,4 @@
         ("write into the executed v3 run folder", lambda: open(C.V3_RUN_FOLDER / "PROBE-NEVER.txt", "w"), "REFUSED"),
-        ("mkdir the future v4 run folder", lambda: os.mkdir(C.RUN_FOLDER), "REFUSED"),
+        ("mkdir the future v5 run folder", lambda: os.mkdir(C.RUN_FOLDER), "REFUSED"),
+        ("mkdir the never-created v4 run folder", lambda: os.mkdir(C.V4_RUN_FOLDER), "REFUSED"),
         ("mkdir another live-shaped run folder r32-v9", lambda: os.mkdir(C.SANDBOX_BASE / "r32-v9"), "REFUSED"),
@@ -46,5 +48,7 @@
         ("write into review43", lambda: open(C.REVIEW43 / "PROBE-NEVER.txt", "w"), "REFUSED"),
+        ("write into review45", lambda: open(C.REVIEW45 / "PROBE-NEVER.txt", "w"), "REFUSED"),
+        ("write into declaration-r32-v4", lambda: open(C.V4 / "PROBE-NEVER.txt", "w"), "REFUSED"),
         ("write into declaration-r32-v3", lambda: open(C.V3 / "PROBE-NEVER.txt", "w"), "REFUSED"),
         ("write into frozen-r13", lambda: open("C:/t/iso/frozen-r13/PROBE-NEVER.txt", "w"), "REFUSED"),
-        ("write at the sandbox base outside r43p", lambda: open(C.SANDBOX_BASE / "PROBE-NEVER.txt", "w"), "REFUSED"),
+        ("write at the sandbox base outside r45q", lambda: open(C.SANDBOX_BASE / "PROBE-NEVER.txt", "w"), "REFUSED"),
         ("open the merged .env", lambda: open(C.MERGED_ENV_FILE, "rb"), "REFUSED"),
@@ -54,3 +58,3 @@
         ("network name lookup", lambda: socket.getaddrinfo("example.com", 443), "REFUSED"),
-        ("write (and remove) a file in the v4 package", lambda: ((C.PACKAGE / "guard-probe.tmp").write_text("x", encoding="utf-8"),
+        ("write (and remove) a file in the v5 package", lambda: ((C.PACKAGE / "guard-probe.tmp").write_text("x", encoding="utf-8"),
                                                                  (C.PACKAGE / "guard-probe.tmp").unlink()), "ALLOWED"),
@@ -64,2 +68,3 @@
                          C.V3_RUN_FOLDER / "PROBE-NEVER.sqlite", C.REVIEW43 / "PROBE-NEVER.txt", C.V3 / "PROBE-NEVER.txt",
+                         C.V4_RUN_FOLDER, C.REVIEW45 / "PROBE-NEVER.txt", C.V4 / "PROBE-NEVER.txt",
                          pathlib.Path("C:/t/iso/frozen-r13/PROBE-NEVER.txt"), C.SANDBOX_BASE / "PROBE-NEVER.txt") if os.path.exists(p)]
```

### `preflight_r42.py`

```diff
--- declaration-r32-v4/scripts/preflight_r42.py
+++ declaration-r32-v5/scripts/preflight_r42.py
@@ -1,2 +1,4 @@
-"""R43-40: the same dry preflight for the frozen v4 declaration against the bound review43 harness (byte copies checked by hash,
+"""R43-44: the same dry preflight for the frozen v5 declaration against the bound review45 harness (BINDING-MANIFEST-R45-HARNESS,
+group harness_r45_package; work folder r45q); `--upto 7` runs steps 1-7 only and writes the results (the card: steps 8-12 NOT run).
+R43-40: the same dry preflight for the frozen v4 declaration against the bound review43 harness (byte copies checked by hash,
 C.check_run_copy; preflight_r32.HERE set to the bound folder for the isolation key, C.declared_here; lane roots inside the
@@ -52,2 +54,3 @@
 OUT = C.PACKAGE / "dry-run"
+UPTO = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else 12   # R43-44
 SCOPE_OUT = C.PACKAGE / "scope"
@@ -58,3 +61,3 @@
 def harness_import():
-    man = json.loads(C.BINDING43.read_text(encoding="utf-8"))          # R43-40: the review43 harness manifest and group
+    man = json.loads(C.BINDING45.read_text(encoding="utf-8"))          # R43-44: the review45 harness manifest and group
     bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
@@ -84,4 +87,4 @@
             "harness_pycache": [p.as_posix() for p in C.HARNESS42.rglob("__pycache__")],
-            "bound_harness_listing_sha256": hashlib.sha256(json.dumps(listing(C.HARNESS43), sort_keys=True).encode()).hexdigest(),   # R43-40
-            "bound_harness_pycache": [p.as_posix() for p in C.HARNESS43.rglob("__pycache__")],
+            "bound_harness_listing_sha256": hashlib.sha256(json.dumps(listing(C.HARNESS45), sort_keys=True).encode()).hexdigest(),   # R43-44
+            "bound_harness_pycache": [p.as_posix() for p in C.HARNESS45.rglob("__pycache__")],
             "package_listing_sha256": hashlib.sha256(json.dumps(listing(C.PACKAGE, skip=("dry-run/", "scope/", "tests/", "evidence/")), sort_keys=True).encode()).hexdigest(),
@@ -190,2 +193,35 @@
 
+def finish_upto(res: dict, ck: dict, rows: list, before: dict) -> int:
+    """R43-44: write PREFLIGHT-RESULTS.json after step 7. Steps 8-12 (the live runner as a subprocess and in process, the guard alone,
+    the scope command) are NOT run: no runner, no guard drill, no scope preview or refusal. The invariants are those of steps 1-7."""
+    after = invariants()
+    res["after"] = after
+    res["steps_run"] = "1-7"
+    res["steps_not_run"] = {"8-12": ("not run by task R43-44 (card R43-44 item 3: preflight steps 1-7 only); the live runner, the dispatch guard "
+                                     "and the scope command are not exercised here")}
+    pkg_bytes = [(C.PACKAGE / f).read_bytes() for f in listing(C.PACKAGE)]
+    res["invariants"] = {
+        "ai_ledger_484_18_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
+        "run_folder_never_created": not before["run_folder_exists"] and not after["run_folder_exists"],
+        "harness_unchanged_no_pycache": before["harness_listing_sha256"] == after["harness_listing_sha256"] and not after["harness_pycache"]
+        and before["bound_harness_listing_sha256"] == after["bound_harness_listing_sha256"] and not after["bound_harness_pycache"],
+        "package_unchanged_by_the_preflight_outside_its_outputs": before["package_listing_sha256"] == after["package_listing_sha256"],
+        "no_authorization_run_or_token_file": before["forbidden_files"] == after["forbidden_files"]
+        and not any(f.startswith(C.PACKAGE.as_posix() + "/") or f.startswith(C.RUN_FOLDER.as_posix() + "/") for f in after["forbidden_files"]),
+        "no_token_in_the_environment": not before["token_env_present"] and not after["token_env_present"],
+        "dummy_digest_never_written": all(C.DUMMY_DIGEST.encode() not in b for b in pkg_bytes),
+        "model_requests": 0}
+    res["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
+    expect = {"1_validate_declaration_as_written": "REFUSED", "2_validate_declaration_in_memory_dummy_digest": "PASSED", "4_verify_binding": "PASSED",
+              "5_verify_bounds": "PASSED", "6_lane_environment_checks_offline": "PASSED", "7_interpreter_cli_file_disk": "PASSED"}
+    res["ok"] = all(ck[k]["result"] == want for k, want in expect.items()) and ck["3_negative_probes"]["all_as_expected"] and \
+        all(x for k, x in res["invariants"].items() if k != "model_requests")
+    sha = C.write_json_once(OUT / "PREFLIGHT-RESULTS.json", res)
+    print(json.dumps({"written": (OUT / "PREFLIGHT-RESULTS.json").as_posix(), "sha256": sha, "ok": res["ok"], "invariants": res["invariants"],
+                      "results": {k: x.get("result") for k, x in ck.items() if isinstance(x, dict) and "result" in x},
+                      "probes": f"{sum(r['as_expected'] for r in rows)}/{len(rows)} as expected",
+                      "unexpected": [r["probe"] for r in rows if not r["as_expected"]]}, indent=1))
+    return 0 if res["ok"] else 1
+
+
 def main() -> int:
@@ -199,3 +235,3 @@
     import runner_r32 as RN  # noqa: E402
-    C.declared_here(PF)                                              # R43-40 (Verification 43 P8)
+    C.declared_here(PF)                                              # R43-40 (Verification 43 P8); R43-44: HERE = review45
     frozen, fsha = BD.frozen_bytes_checked()
@@ -203,8 +239,8 @@
     run_path = C.PACKAGE / C.RUN_NAME
-    binding_sha = C.sha256_file(C.BINDING43)
+    binding_sha = C.sha256_file(C.BINDING45)
     before = invariants()
-    res = {"name": "PREFLIGHT-RESULTS (R43-40 dry preflight of declaration-r32-v4)", "started_utc": started,
-           "declaration": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(), "sha256": fsha}, "harness": C.HARNESS43.as_posix(),
+    res = {"name": "PREFLIGHT-RESULTS (R43-44 dry preflight of declaration-r32-v5, steps 1-7)", "started_utc": started,
+           "declaration": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(), "sha256": fsha}, "harness": C.HARNESS45.as_posix(),
            "imported_from": C.HARNESS42.as_posix(), "run_copy": C.check_run_copy(),
-           "binding_manifest": {"path": C.BINDING43.as_posix(), "sha256": binding_sha}, "before": before, "checks": {}}
+           "binding_manifest": {"path": C.BINDING45.as_posix(), "sha256": binding_sha}, "before": before, "checks": {}}
     ck = res["checks"]
@@ -243,3 +279,3 @@
                                "all_as_expected": all(r["as_expected"] for r in rows), "rows": rows}
-    ck["4_verify_binding"] = {"result": "PASSED", **PF.verify_binding(C.BINDING43, binding_sha)}
+    ck["4_verify_binding"] = {"result": "PASSED", **PF.verify_binding(C.BINDING45, binding_sha)}
     truth = PF.build_truth()
@@ -256,3 +292,3 @@
     for lane in ("B", "C", "R", "P"):
-        root = C.WORK / f"env-{lane}"                                  # R43-40: lane roots in the work folder
+        root = C.WORK / f"env-{lane}"                                  # R43-40 / R43-44: lane roots in the work folder (r45q)
         env = RN.lane_env("live", root, lane, cfg)
@@ -270,5 +306,7 @@
                                         "note": "the CLI file is read as bytes; `--version` is never run by this task"}
+    if UPTO < 8:                                                     # R43-44: steps 8-12 NOT run
+        return finish_upto(res, ck, rows, before)
     env = {k: val for k, val in os.environ.items() if k != C.TOKEN_ENV} | {"PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "PYTHONIOENCODING": "utf-8"}
     argv = ["run", "--mode", "live", "--declaration", run_path.as_posix(), "--declaration-sha", run_mem_sha, "--run-set", C.RUN_SET.as_posix(),
-            "--binding", C.BINDING43.as_posix(), "--binding-sha", binding_sha]
+            "--binding", C.BINDING45.as_posix(), "--binding-sha", binding_sha]
     r = subprocess.run([C.PY, "-B", "runner_r32.py", *argv], cwd=str(C.HARNESS42), env=env, capture_output=True, text=True, encoding="utf-8", timeout=900)
```

### `r42common.py`

```diff
--- declaration-r32-v4/scripts/r42common.py
+++ declaration-r32-v5/scripts/r42common.py
@@ -6,3 +6,5 @@
 model, network, CLI process or ledger scope is touched by this module. The installed claude.exe is only ever READ AS BYTES
-(its sha256); it is never executed."""
+(its sha256); it is never executed.
+R43-44 (declaration-r32-v5): the work folder r45q, the stamp r32-v5 and its scope, the v5 package, the review45 harness
+(BINDING-MANIFEST-R45-HARNESS 9af8e07a...9ffb, group harness_r45_package) and the v4 record constants (V5-BUILD-DIFF.md)."""
 from __future__ import annotations
@@ -24,8 +26,8 @@
 MERGED_EP = EP.as_posix()                                         # "G:/dev (2)/dev/ep-platform-merged/ep-platform"
-WORK = pathlib.Path("C:/t/r2x/r42-sandbox/r43p")                  # R43-40: the one work folder of this task (r42: C:/t/iso/work/r2x/r42)
+WORK = pathlib.Path("C:/t/r2x/r42-sandbox/r45q")                  # R43-44: the one work folder of this task (v4: r43p; r42: C:/t/iso/work/r2x/r42)
 SANDBOX_BASE = pathlib.Path("C:/t/r2x/r42-sandbox")               # this task's dry sandboxes AND the declared live base
-STAMP = "r32-v4"                                                   # R43-40: new stamp (r32-v3 exists, executed)
+STAMP = "r32-v5"                                                   # R43-44: new stamp (r32-v3 executed; r32-v4 never created, v4 superseded)
 RUN_FOLDER = SANDBOX_BASE / STAMP                                  # never created by this task
-DECLARATION_DATE = "2026-10-08"                                    # R43-40: the v4 freeze date (owner's local date, +04)
-SCOPE = f"m2-fresh-validation-r32-v4-{DECLARATION_DATE}"           # R43-40: new scope name (the v3 scope exists)
+DECLARATION_DATE = "2026-10-08"                                    # R43-44: the v5 freeze date (owner's local date, +04)
+SCOPE = f"m2-fresh-validation-r32-v5-{DECLARATION_DATE}"           # R43-44: new scope name (the v3 scope exists; no v4 scope was ever created)
 DRY_BASE = WORK / "sb"                                             # R43-40: dry / demo run folders (driver-side base redirect, r43p_base.py)
@@ -73,7 +75,23 @@
 BINDING43_SHA = "f35355aa8a8bca16803db3576fda8260a470915fee9c905b035f8d8bd9a374a7"
-HARNESS_GROUP = "harness_r43_package"
-HARNESS42 = pathlib.Path(os.environ.get("R43_HARNESS_RUN") or HARNESS43)
-PACKAGE = PILOT / "declaration-r32-v4"                             # R43-40
-DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V4.json"
-RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V4.RUN.json"       # produced ONLY by the owner (fill_owner_digest), never here
+HARNESS43_GROUP = "harness_r43_package"                            # R43-44: the v4 harness group (record only)
+# R43-44: the review45 harness (Verification 45 VERIFIED WITH CONDITIONS) is the bound harness of v5: review43 plus the dry-only
+# baseline-facts drill. HARNESS42 keeps its name and now names the folder the review45 code is IMPORTED from (the bound folder, or a
+# byte copy named by R43_HARNESS_RUN, checked against BINDING-MANIFEST-R45-HARNESS by check_run_copy before any import).
+REVIEW45 = PILOT / "review45"
+HARNESS45 = REVIEW45 / "scripts" / "harness-r32"                  # the bound, declared folder of v5 (isolation.allowed_under_forbidden.harness)
+BINDING45 = REVIEW45 / "BINDING-MANIFEST-R45-HARNESS.json"
+BINDING45_SHA = "9af8e07ade4e0c15d1a04189b654eeabbcba7646ab726ef2c04ffa107b0c9ffb"
+DRILL_CRITERION_SHA = "8b183053cf10e5332f8b198a1d5b1aae5169c47671ad5e35346acf31cca5d918"
+HARNESS_GROUP = "harness_r45_package"                              # R43-44
+HARNESS42 = pathlib.Path(os.environ.get("R43_HARNESS_RUN") or HARNESS45)
+PACKAGE = PILOT / "declaration-r32-v5"                             # R43-44
+DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V5.json"
+RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V5.RUN.json"       # produced ONLY by the owner (fill_owner_digest), never here
+# R43-44: the superseded v4 declaration (frozen, never authorized, never run; read-only; v5 is built from its exact bytes)
+V4 = PILOT / "declaration-r32-v4"
+V4_NAME = "FRESH-VALIDATION-DECLARATION-R32-V4.json"
+V4_SHA = "e0a93c461fee31222098a3b774cd7af25201398925fb67170c49a950394fbeb9"
+V4_MANIFEST_SHA = "4c7285eeea712dde9350dc5e7b1f3068eafea6becad10636bb58ff69665720ab"
+V4_SCOPE = "m2-fresh-validation-r32-v4-2026-10-08"                # never created
+V4_RUN_FOLDER = SANDBOX_BASE / "r32-v4"                            # never created
 # R43-40: the executed v3 declaration (frozen; its RUN and authorization files committed as 7a1bf6f; never edited)
@@ -118,4 +136,4 @@
           "MASTER-ROADMAP.md": "f6dba0b2fce767955aed2b7508cfe7480637b02c44f502c3702c7862116e4c86"}
-TASK_FILE = MR / "orchestrator/tasks/R43-40-TASK.md"               # R43-40
-TASK_FILE_SHA = "a6e54229993d710f13f5191757ba3714128bd1b738abbe46f27e3b4da5bec023"
+TASK_FILE = MR / "orchestrator/tasks/R43-44-TASK.md"               # R43-44
+TASK_FILE_SHA = "1cd72eb3eaed75b8321ae7a201e0f504564137f02f67947e25b710908a6e4d0b"
 
@@ -123,14 +141,14 @@
 def check_run_copy() -> dict:
-    """R43-40 (R43V-09): the folder the harness is imported from (HARNESS42) must hold exactly the bound bytes of the
-    review43 harness: every file of the bound group harness_r43_package under scripts/harness-r32 re-hashed at its bound
+    """R43-40 (R43V-09), R43-44: the folder the harness is imported from (HARNESS42) must hold exactly the bound bytes of the
+    review45 harness: every file of the bound group harness_r45_package under scripts/harness-r32 re-hashed at its bound
     path AND at the run copy. A difference is PACKET MISMATCH."""
-    man = json.loads(BINDING43.read_text(encoding="utf-8"))
-    if sha256_file(BINDING43) != BINDING43_SHA:
-        raise PacketMismatch(f"PACKET MISMATCH: {BINDING43.as_posix()} is not {BINDING43_SHA}")
+    man = json.loads(BINDING45.read_text(encoding="utf-8"))
+    if sha256_file(BINDING45) != BINDING45_SHA:
+        raise PacketMismatch(f"PACKET MISMATCH: {BINDING45.as_posix()} is not {BINDING45_SHA}")
     group = {p: w for p, w in man["files"][HARNESS_GROUP].items() if "/scripts/harness-r32/" in p}
     bad = [p for p, w in group.items() if sha256_file(p) != w]
-    copy_bad = [p for p, w in group.items() if sha256_file(HARNESS42 / pathlib.Path(p).name) != w] if HARNESS42 != HARNESS43 else []
+    copy_bad = [p for p, w in group.items() if sha256_file(HARNESS42 / pathlib.Path(p).name) != w] if HARNESS42 != HARNESS45 else []
     if bad or copy_bad:
         raise PacketMismatch(f"PACKET MISMATCH: bound {bad[:3]} run copy {copy_bad[:3]}")
-    return {"bound_folder": HARNESS43.as_posix(), "imported_from": HARNESS42.as_posix(), "files": len(group), "run_copy": HARNESS42 != HARNESS43}
+    return {"bound_folder": HARNESS45.as_posix(), "imported_from": HARNESS42.as_posix(), "files": len(group), "run_copy": HARNESS42 != HARNESS45}
 
@@ -138,6 +156,6 @@
 def declared_here(PF) -> None:
-    """R43-40 (Verification 43 P8): when the harness is imported from a byte copy, preflight_r32.HERE is set to the bound
-    folder in THIS process only, so isolation_binding() and validate_declaration compare the declaration with the folder
-    the live runner will run from (PILOT/review43/scripts/harness-r32)."""
-    PF.HERE = HARNESS43
+    """R43-40 (Verification 43 P8), R43-44: when the harness is imported from a byte copy, preflight_r32.HERE is set to the
+    bound folder in THIS process only, so isolation_binding() and validate_declaration compare the declaration with the folder
+    the live runner will run from (PILOT/review45/scripts/harness-r32)."""
+    PF.HERE = HARNESS45
 
```

### `snapshot_r43p.py`

```diff
--- declaration-r32-v4/scripts/snapshot_r43p.py
+++ declaration-r32-v5/scripts/snapshot_r43p.py
@@ -1,2 +1,4 @@
-"""R43-40 (new): the before / after snapshot of everything task R43-40 must not change, read-only.
+"""R43-44: the same snapshot for task R43-44: review45 and declaration-r32-v4 added; the executed v3 run folder by os.stat only (names,
+sizes, mtimes; no file opened, as Verification 45); the v4 and v5 scopes and run folders.
+R43-40 (new): the before / after snapshot of everything task R43-40 must not change, read-only.
 Usage: <bound python> -B snapshot_r43p.py <out json>   (with the package guard; R43_GUARD_OWNER_RECORDS=hash-only lets THIS
@@ -24,3 +26,4 @@
 TREES = ("C:/t/iso/frozen-r12", "C:/t/iso/cand-r29", "C:/t/iso/frozen-r13", "C:/t/iso/cand-r30", "C:/t/iso/cand-r30n")
-FOLDERS = {"v3_run_folder": C.V3_RUN_FOLDER, "owner_records": C.OWNER_RECORDS, "review42": C.REVIEW42, "review43": C.REVIEW43,
+FOLDERS = {"owner_records": C.OWNER_RECORDS, "review42": C.REVIEW42, "review43": C.REVIEW43, "review45": C.REVIEW45,
+           "declaration_r32_v4": C.V4,
            "declaration_r32": C.PILOT / "declaration-r32", "declaration_r32_v2": C.V2, "declaration_r32_v3": C.V3,
@@ -38,2 +41,17 @@
     return {"path": root.as_posix(), "files": len(lines), "sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()}
+
+
+def stat_listing(root: pathlib.Path) -> dict:
+    """R43-44: a live run folder by os.stat only (relative path, size, mtime_ns); no file is opened."""
+    if not root.exists():
+        return {"path": root.as_posix(), "exists": False}
+    lines = []
+    for dp, _ds, fs in os.walk(C.long_path(root)):
+        for f in fs:
+            full = os.path.join(dp, f)
+            st = os.stat(full)
+            lines.append(f"{os.path.relpath(full, C.long_path(root)).replace(chr(92), '/')}\t{st.st_size}\t{st.st_mtime_ns}")
+    lines.sort()
+    return {"path": root.as_posix(), "exists": True, "files": len(lines), "stat_sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(),
+            "method": "os.stat only; no file opened"}
 
@@ -66,6 +84,8 @@
            "ai_ledger": {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")},
-           "v3_scope_present": C.V3_SCOPE in led["scope_names"], "v4_scope_present": C.SCOPE in led["scope_names"],
+           "v3_scope_present": C.V3_SCOPE in led["scope_names"], "v4_scope_present": C.V4_SCOPE in led["scope_names"],
+           "v5_scope_present": C.SCOPE in led["scope_names"], "v3_run_folder_stat": stat_listing(C.V3_RUN_FOLDER),
            "pip_freeze": {"sha256": hashlib.sha256(pf.stdout).hexdigest(), "lines": len(pf.stdout.splitlines()), "returncode": pf.returncode},
            "folders": {k: aggregate(v) for k, v in FOLDERS.items()}, "trees": {t: tree(t) for t in TREES},
-           "authorization_run_token_named_files": named_files(), "v4_run_folder_exists": C.RUN_FOLDER.exists(),
+           "authorization_run_token_named_files": named_files(), "v4_run_folder_exists": C.V4_RUN_FOLDER.exists(),
+           "v5_run_folder_exists": C.RUN_FOLDER.exists(), "v5_package_exists": C.PACKAGE.exists(),
            "c_free_bytes": C.free_bytes("C:/")}
@@ -73,3 +93,3 @@
     print(json.dumps({"ai_ledger": res["ai_ledger"], "pip_freeze": res["pip_freeze"]["sha256"], "v4_scope": res["v4_scope_present"],
-                      "v4_run_folder": res["v4_run_folder_exists"], "named_files": len(res["authorization_run_token_named_files"]),
+                      "v5_scope": res["v5_scope_present"], "v4_run_folder": res["v4_run_folder_exists"], "v5_run_folder": res["v5_run_folder_exists"], "named_files": len(res["authorization_run_token_named_files"]),
                       "c_free_bytes": res["c_free_bytes"]}))
```

