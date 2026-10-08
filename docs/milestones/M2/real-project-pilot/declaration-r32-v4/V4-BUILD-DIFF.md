# V4-BUILD-DIFF: the v4 package scripts against the v3 scripts they were copied from (task R43-40)

Every v3 script (`PILOT/declaration-r32-v3/scripts/`, 27 files) was first copied byte-identically into `scripts/` of this package (`evidence/COPY-V3-SCRIPTS.sha256`, checked equal to the v3 files at the copy) and then changed only where listed below. Nothing in the review43 harness, review42, review43 or declaration-r32-v3 was changed. It authorizes nothing.

- Copy record covers every v3 script: True.
- Files: 17 unchanged, 10 changed, 7 new, 0 removed.

## 1. Per file

| file | state | v3 sha256 | v4 sha256 | +lines | -lines | run by this task |
|---|---|---|---|---|---|---|
| `append_response_r42.py` | unchanged | `25ffc3c3d9bc7560` | `25ffc3c3d9bc7560` | 0 | 0 | not run by this task |
| `auth_test_exception_r43p.py` | new | `-` | `76ec713129308a20` | 0 | 0 | once |
| `build_declaration_r42.py` | changed | `4a67f377d4f193f9` | `ccb2664937a3b72e` | 307 | 9 | show, write |
| `cli_version_drill_r42.py` | changed | `977edd099a5f801e` | `f9d5553575838b0b` | 9 | 3 | by dry_exercise_r42.py cli |
| `create_scope_r42.py` | changed | `83cf93136d967cb6` | `e801d50f9a366b6b` | 10 | 8 | preview and create-refused, by preflight_r42.py |
| `demos_r42.py` | changed | `2f9f79333197f254` | `add582223e18d1f9` | 23 | 6 | once |
| `diff_declaration_r42.py` | changed | `2abe17744576f2eb` | `1744769efbb0f910` | 107 | 54 | once |
| `dry_exercise_r42.py` | changed | `ea2cdc5ee613697b` | `4540549301254601` | 27 | 23 | new-tag, single, split, loops, xproject, cli (cli_version_drill_r42.py), finish |
| `facts_r42.py` | unchanged | `be47cc9e4e0d42fe` | `be47cc9e4e0d42fe` | 0 | 0 | not run by this task |
| `guard/sitecustomize.py` | changed | `ded6102eab38c804` | `6488ec7941d1114c` | 64 | 24 | loaded by every process (PYTHONPATH) |
| `guard_probe_r43p.py` | new | `-` | `a8cb9dfc2e3bb1cd` | 0 | 0 | once |
| `interpreter_check_r42.py` | unchanged | `d5fda9139be10c28` | `d5fda9139be10c28` | 0 | 0 | not run by this task |
| `lane_env_check_r42.py` | unchanged | `67ee5ed08ff81286` | `67ee5ed08ff81286` | 0 | 0 | by preflight_r42.py |
| `make_binding_r42.py` | unchanged | `36e56876c055bc17` | `36e56876c055bc17` | 0 | 0 | not run by this task |
| `make_contract_v5_r42.py` | unchanged | `477d02493108d8d0` | `477d02493108d8d0` | 0 | 0 | not run by this task |
| `make_outputs_r42.py` | unchanged | `a890904c48ff7eff` | `a890904c48ff7eff` | 0 | 0 | not run by this task |
| `make_report_r42.py` | unchanged | `ba46a61c5c1a4b99` | `ba46a61c5c1a4b99` | 0 | 0 | not run by this task |
| `make_review42_docs.py` | unchanged | `4e84842803cdb123` | `4e84842803cdb123` | 0 | 0 | not run by this task |
| `make_v3_docs_r42.py` | unchanged | `a165196eff87e4c5` | `a165196eff87e4c5` | 0 | 0 | not run by this task |
| `make_v4_build_diff_r43p.py` | new | `-` | `6e3be854726636bf` | 0 | 0 | once |
| `manifest_v4_r43p.py` | new | `-` | `73de5002a7433e6c` | 0 | 0 | manifest, self-check |
| `package_r42.py` | changed | `fbea3715d07d3bd5` | `cbfa20032bba5ff5` | 1 | 1 | not run by this task |
| `patch_runner_main_r42.py` | unchanged | `d20ea0df697ee609` | `d20ea0df697ee609` | 0 | 0 | not run by this task |
| `pathlen_probe_r42.py` | unchanged | `4763cc2efcdff45c` | `4763cc2efcdff45c` | 0 | 0 | not run by this task |
| `preflight_r42.py` | changed | `775f3312f9de1809` | `edb8660c23d8c462` | 25 | 13 | once (with lane_env_check_r42.py and create_scope_r42.py preview / create-refused as its children) |
| `r42common.py` | changed | `68f12396e9bb97a7` | `4f05b78c71b54829` | 58 | 15 | imported |
| `r43p_base.py` | new | `-` | `b42b567894847757` | 0 | 0 | imported |
| `run_tests_r42.py` | unchanged | `bed0672b578d329e` | `bed0672b578d329e` | 0 | 0 | not run by this task |
| `run_tests_r42pkg.py` | unchanged | `d94dd756d3399735` | `d94dd756d3399735` | 0 | 0 | not run by this task |
| `runner_r43p.py` | new | `-` | `5ff4376e1a09048b` | 0 | 0 | by dry_exercise_r42.py |
| `snapshot_r42.py` | unchanged | `eebeede2a05a89f1` | `eebeede2a05a89f1` | 0 | 0 | not run by this task |
| `snapshot_r43p.py` | new | `-` | `5d44bfaeb1f55794` | 0 | 0 | before and after |
| `test_r42.py` | unchanged | `f5bda56117e435df` | `f5bda56117e435df` | 0 | 0 | not run by this task |
| `trim_sandbox_r42.py` | unchanged | `71bad1201f87a73f` | `71bad1201f87a73f` | 0 | 0 | not run by this task |

## 2. What each change answers

- `r42common.py`: the work folder (r43p), the stamp `r32-v4`, the date and scope `m2-fresh-validation-r32-v4-2026-10-08`, the dry base `DRY_BASE`, the R43 trees and heads (review43 re-points 1-4), `LEDGER_EXPECTED` 484 / 18 / 0 (R43V-04), the package and file names of v4, the v3 record constants, the review43 harness constants (`HARNESS43`, `BINDING43`, `HARNESS_GROUP`; `HARNESS42` now names the folder the code is imported from: the bound folder or the byte copy named by `R43_HARNESS_RUN`), the task file, `check_run_copy()` (R43V-09) and `declared_here()` (Verification 43 P8: `preflight_r32.HERE` set to the bound folder in the calling process for the isolation key).
- `build_declaration_r42.py`: `build_v4()` / `evidence_v4()` build v4 from the frozen v3 bytes (R43 re-point, harness hashes from BINDING-MANIFEST-R43-HARNESS, the R43-40 items); `main()` checks the review43 group and the run copy, expects 484 / 18 / 0 and calls `build_v4`; the owner procedures refuse the v3 frozen and RUN hashes too. v3's `build()` is kept unchanged (not called).
- `diff_declaration_r42.py`: v3 -> v4 with the categories repointed / rebound and the old-identifier text check (R43V-13).
- `preflight_r42.py`: the review43 manifest and group, the run-copy check, `declared_here`, lane roots in r43p, 484 / 18 / 0, the bound-harness listing, and the authorization-file invariant as a before/after comparison (the v3 RUN and authorization files are committed, 7a1bf6f).
- `dry_exercise_r42.py`: runs the runner through `runner_r43p.py` (S-BASE), the dry base, the review43 manifest, stamps `r43d-*`, 484 / 18 / 0, the run-copy check and the dry statement.
- `demos_r42.py`: the run-copy check, S-BASE (including the live-shaped declarations' sandbox base), stamps `r43d-*`, one added refusal case (an authorization naming the executed v3 RUN hash).
- `cli_version_drill_r42.py`: S-BASE, the dry base, the review43 manifest. `create_scope_r42.py`: the review43 manifest and group, the run-copy check, `declared_here`, the v3 hashes refused, the v4 pinned path in its text. `package_r42.py`: the ledger pin (not run).
- `guard/sitecustomize.py` (R43V-10): rewritten from the R42 guard: deny-first for live run folders r32-v<N>, the owner records (no read either unless hash-only), the AI ledger folder, the trees and the frozen packages; allowed roots r43p and this package (or R43_GUARD_ROOTS inside the sandbox base).
- New: `r43p_base.py` (S-BASE), `runner_r43p.py` (dry runner wrapper), `snapshot_r43p.py`, `guard_probe_r43p.py`, `make_v4_build_diff_r43p.py`, `manifest_v4_r43p.py`.

## 3. Ledger-baseline lines (Verification 43 R43V-04; every line of the v4 scripts that reads or names the pin)

| file | line | text |
|---|---|---|
| `append_response_r42.py` | 50 | `"**Zero calls:** no provider or model request, no `claude` process of any kind (the installed binary read as bytes only; every process ran under an audit guard ` |
| `build_declaration_r42.py` | 628 | `"rule": ("Verification 43 R43V-04: the build, dry-exercise and preflight scripts of this package expect 484 / 18 / 0 (r42common.LEDGER_EXPECTED, "` |
| `build_declaration_r42.py` | 687 | `"ledger_baseline": "ledger_baseline (484 / 18 / 0 at freeze; no v4 scope)",` |
| `build_declaration_r42.py` | 726 | `"ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v4 freeze (the v3 scope present); the runtime harness does not read that pin",` |
| `build_declaration_r42.py` | 754 | `"4_ledger_baseline": "re-pinned to 484 / 18 / 0 in the v4 copies of r42common.py (LEDGER_EXPECTED, read by build_declaration_r42, facts_r42, package_r42, dry_ex` |
| `build_declaration_r42.py` | 820 | `if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"]:` |
| `diff_declaration_r42.py` | 61 | `"ledger_detail": "the creation sentence names 484 / 18 / 0 (R43V-04)", "isolation": "the review43 harness folder (section 0 item 1)",` |
| `diff_declaration_r42.py` | 72 | `"ledger_baseline": "ADDED (section 0 item 4, R43V-04): 484 / 18 / 0 at freeze",` |
| `dry_exercise_r42.py` | 18 | `The AI ledger is read (mode=ro) before and after every phase: 484 / 18 / 0 (R43-40; v3: 483 / 17 / 0). 0 model requests. Staged PDF copies of every` |
| `dry_exercise_r42.py` | 322 | `"ai_ledger_unchanged_484_18_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,` |
| `facts_r42.py` | 101 | `"ai_ledger": {k: f["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and not f["ai_ledger"]["scope_v3_exists"],` |
| `make_v3_docs_r42.py` | 293 | `- Dry exercise: the single 24-document run {dry['single']['report']['run_state']}; six per-project runs; EP-27331 loops {list(loops.values())} invocations; the ` |
| `make_v3_docs_r42.py` | 398 | `- Model requests {dry['model_requests_total']}; AI ledger 483 / 17 / 0 throughout ({dry['ai_ledger_unchanged_483_17_0']}); the live run folder absent ({dry['liv` |
| `make_v4_build_diff_r43p.py` | 53 | `if re.search(r"LEDGER_EXPECTED/\(483, 17, 0\)/483 / 17 / 0/484 / 18 / 0", line):` |
| `make_v4_build_diff_r43p.py` | 68 | `"`DRY_BASE`, the R43 trees and heads (review43 re-points 1-4), `LEDGER_EXPECTED` 484 / 18 / 0 (R43V-04), the package and file names of v4, the "` |
| `make_v4_build_diff_r43p.py` | 73 | `"BINDING-MANIFEST-R43-HARNESS, the R43-40 items); `main()` checks the review43 group and the run copy, expects 484 / 18 / 0 and calls `build_v4`; "` |
| `make_v4_build_diff_r43p.py` | 76 | `"- `preflight_r42.py`: the review43 manifest and group, the run-copy check, `declared_here`, lane roots in r43p, 484 / 18 / 0, the bound-harness "` |
| `make_v4_build_diff_r43p.py` | 78 | `"- `dry_exercise_r42.py`: runs the runner through `runner_r43p.py` (S-BASE), the dry base, the review43 manifest, stamps `r43d-*`, 484 / 18 / 0, "` |
| `manifest_v4_r43p.py` | 196 | `ck("AI ledger 484 / 18 / 0, no v4 scope", {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and C.SCOPE not in led["scope_names"])` |
| `package_r42.py` | 30 | `"ok": (led["entries"], led["scopes"], led["limit_amendments"]) == tuple(C.LEDGER_EXPECTED[k] for k in ("entries", "scopes", "limit_amendments")) and C.SCOPE not` |
| `preflight_r42.py` | 3 | `work folder r43p; the ledger expected 484 / 18 / 0; the authorization-file invariant a before/after comparison, since the` |
| `preflight_r42.py` | 28 | `Invariants before and after: AI ledger 483 / 17 / 0; run folder never created; the review42 harness unchanged with no` |
| `preflight_r42.py` | 360 | `"ai_ledger_484_18_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,` |
| `r42common.py` | 46 | `LEDGER_EXPECTED = {"entries": 484, "scopes": 18, "limit_amendments": 0}   # R43-40 (R43V-04): re-pinned to the state at the v4 freeze (v3 scope present)` |

## 4. Run-time substitutions of this task (no file changed by them)

- **S-RUN**: every script ran from byte copies in `C:/t/r2x/r42-sandbox/r43p/run/` (`v4/` = this package's scripts, `h43/harness-r32` = the review43 harness); `R43_HARNESS_RUN` names the harness copy; `C.check_run_copy()` re-hashes it against BINDING-MANIFEST-R43-HARNESS before any import (evidence/RUN-COPY-*.sha256).
- **S-HERE** (Verification 43 P8): `preflight_r32.HERE` = `PILOT/review43/scripts/harness-r32` in the build, preflight and scope processes (`C.declared_here`), so the isolation key equals the folder the live runner runs from.
- **S-BASE**: dry and demonstration run folders under `C:/t/r2x/r42-sandbox/r43p/sb` (`r43p_base.redirect`, the calling process only).
- **S-GUARD**: `PYTHONPATH` = the guard copy `r43p/run/v4/guard`; `R43_GUARD_LOG` = `r43p/guard-log`; `TEMP` / `TMP` = `r43p/tmp`; `R43_GUARD_OWNER_RECORDS=hash-only` only for the two snapshot processes.
- **S-ENV**: lane roots of the preflight's offline lane checks in `r43p/env-<lane>` (Verification 43 V-P4).

## 5. Unified diffs (v3 -> v4)

### `build_declaration_r42.py`

```diff
--- declaration-r32-v3/scripts/build_declaration_r42.py
+++ declaration-r32-v4/scripts/build_declaration_r42.py
@@ -37,3 +37,3 @@
 
-PKG_SCRIPTS = "PILOT/declaration-r32-v3/scripts"
+PKG_SCRIPTS = "PILOT/declaration-r32-v4/scripts"   # R43-40
 V2_PROOF = C.V2 / "evidence/r40-04-proof"
@@ -127,3 +127,3 @@
         raise ValueError("the RUN hash and the digest are 64 lower-case hex characters")
-    if run_sha in (frozen_sha, C.V2_SHA):
+    if run_sha in (frozen_sha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA):   # R43-40: never a frozen or the executed v3 hash
         raise ValueError("the authorization names the RUN hash, never a frozen hash")
@@ -474,2 +474,298 @@
 
+# ---- R43-40: the v4 declaration, built from the frozen v3 bytes -------------------------------------------------------------
+# Method: the v3 declaration 9a55fa7b...1b40 (frozen, executed 2026-10-07: INVALID / INELIGIBLE, terminal) is loaded from its
+# exact bytes; the R43 tree re-point (the same four re-points as review43) and the harness re-point review42 -> review43 are
+# applied to every string; every {path, sha256} node under the review43 harness takes the hash BINDING-MANIFEST-R43-HARNESS
+# binds; then ONLY the items of task R43-40 sections 0 and 2 are applied. Every number of v3 is carried (DECLARATION-DIFF).
+R43_REPOINT = (("C:/t/iso/frozen-r12", "C:/t/iso/frozen-r13"), ("C:/t/iso/cand-r29", "C:/t/iso/cand-r30n"),
+               ("3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "7ec3d2cf983b70a604844beda8eb6b1ec6173d34"),
+               ("a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "436daef215c72fbe2429dcd783e087bf39756ad7"),
+               ("/real-project-pilot/review42/scripts/harness-r32", "/real-project-pilot/review43/scripts/harness-r32"))
+A13_ITEM3 = ("3. **Conditional D1/D2 for a v4 live run tonight: YES**, only if all three hold: (a) Verification 43 of the harness reports no "
+             "blocker; (b) the dry rehearsal exercises F009/F020/F030 and passes; (c) the `pip freeze` equality precondition of "
+             "`RUNBOOK-ADDENDUM-R42.md` holds before invocation 1 and every resume. Budget: the same request ceiling as v3 (556 requests). "
+             "Served-model identity: handled as in v3. The owner's runbook steps are delegated to the session as they were for v3. If any "
+             "condition fails, nothing runs and the session stops at the v4 declaration.")
+PIP_FREEZE_SHA = "bd424a5c4692ab4c1f634705e59ded3784549a6f6c9072ffea9860fbf611bf7f"
+
+
+def v3_bytes() -> bytes:
+    b = (C.V3 / C.V3_NAME).read_bytes()
+    if C.sha256_bytes(b) != C.V3_SHA:
+        raise C.PacketMismatch(f"PACKET MISMATCH: the v3 declaration is not {C.V3_SHA}")
+    return b
+
+
+def repoint43(o):
+    if isinstance(o, dict):
+        return {k: repoint43(v) for k, v in o.items()}
+    if isinstance(o, list):
+        return [repoint43(v) for v in o]
+    if isinstance(o, str):
+        for a, b in R43_REPOINT:
+            o = o.replace(a, b)
+        return o
+    return o
+
+
+def rebind_harness(o, bound: dict, path="", out=None) -> list:
+    """Every {path, sha256} node naming a review43 harness file takes the hash the harness manifest binds (in place)."""
+    out = [] if out is None else out
+    if isinstance(o, dict):
+        p, s = o.get("path"), o.get("sha256")
+        if isinstance(p, str) and p in bound and isinstance(s, str):
+            if s != bound[p]:
+                out.append({"at": path, "path": p, "v3_sha256": s, "v4_sha256": bound[p]})
+            o["sha256"] = bound[p]
+        for k, v in o.items():
+            rebind_harness(v, bound, f"{path}.{k}" if path else k, out)
+    elif isinstance(o, list):
+        for i, v in enumerate(o):
+            rebind_harness(v, bound, f"{path}[{i}]", out)
+    return out
+
+
+def register_item(n: int) -> str:
+    """The text of item n of A-13 in the authority register, verbatim (one line)."""
+    text = (C.MR / "orchestrator/AUTHORITY-REGISTER.md").read_text(encoding="utf-8")
+    sec = text[text.index("## A-13"):]
+    line = next(ln.strip() for ln in sec.split("\n") if ln.strip().startswith(f"{n}. "))
+    return line
+
+
+def build_v4(declared_at: str, ev: dict) -> dict:
+    sys.path.insert(0, str(C.HARNESS42))
+    import preflight_r32 as PF           # noqa: E402  (checked against BINDING-MANIFEST-R43-HARNESS first: C.check_run_copy)
+    C.declared_here(PF)
+    v3 = json.loads(v3_bytes().decode("utf-8"))
+    d = repoint43(copy.deepcopy(v3))
+    binding = json.loads(C.BINDING43.read_text(encoding="utf-8"))
+    h43 = binding["files"][C.HARNESS_GROUP]
+    rebound = rebind_harness(d, h43)
+    modules = {pathlib.Path(p).stem: {"path": p, "sha256": s} for p, s in h43.items()
+               if "/scripts/harness-r32/" in p and not pathlib.Path(p).name.startswith("test_")}
+    run_folder = C.RUN_FOLDER.as_posix()
+    pinned = (C.PACKAGE / C.AUTH_NAME).as_posix()
+    run_path = (C.PACKAGE / C.RUN_NAME).as_posix()
+    item3 = register_item(3)
+    if item3 != A13_ITEM3:
+        raise C.PacketMismatch("PACKET MISMATCH: A-13 item 3 in the authority register differs from the text this script records")
+
+    d["schema"] = "r43-40-fresh-validation-declaration-r32-v4.1"
+    d["contract"] = PF.CONTRACT
+    d["name"] = ("M2 fresh validation R32, declaration v4 (R43 trees, review43 harness): accepted baseline B (frozen-r13) vs Review 29 combined "
+                 "candidate C (cand-r30n), with reference R and variation probe P")
+    d["task"] = ("R43-40 (label R32-V4-PREP; owner decision A-13 item 2), implementation agent ep-implementer, Claude Opus 5.5 "
+                 "(claude-opus-5-5, self-reported), effort high")
+    d["supersedes"] = {
+        "declaration": ref(C.V3 / C.V3_NAME), "manifest": ref(C.V3 / "evidence/EVIDENCE-MANIFEST.json"),
+        "run_declaration": ref(C.V3 / "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json"),
+        "authorization_file": ref(C.V3 / C.AUTH_NAME) | {"committed_as": "7a1bf6f (owner decision A-13 item 6)", "never_removed": True},
+        "status": ("executed 2026-10-07 (invocation 1, 1 request): INVALID and INELIGIBLE, terminal (a resolved-truth critical in B on F009 page 3, "
+                   "ruled BASELINE_PROCESSING_DEFECT by the owner on 2026-10-07); never resumed, never re-run; its run folder "
+                   f"{C.V3_RUN_FOLDER.as_posix()}, scope {C.V3_SCOPE} and nonces 2-3 are never reused"),
+        "binding_manifests": {"v3_binding_review42": ref(C.BINDING42), "task37_r43": ref(C.REVIEW43 / "BINDING-MANIFEST-R43.json"),
+                              "superseded_by": ref(C.BINDING43),
+                              "rule": "the task-37 manifest e1735093...83c1 is superseded for the harness code and the candidate tree by the harness manifest f35355aa...374a7, which v4 binds"},
+        "differences": "DECLARATION-DIFF.md and DECLARATION-DIFF.json in this package list every difference from v3",
+        "structure": ("the v3 content is carried; only the R43-40 items change it (the R43 trees and the review43 harness, the stamp, run folder, "
+                      "scope and pinned paths, the ledger baseline, the Verification 43 conditions, the v4 preparation items, the owner's "
+                      "conditional decision as a precondition); every number of v3 is unchanged"),
+        "lineage": v3["supersedes"]}
+    d["declared_at_utc"] = declared_at
+    d["status"] = ("FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file, no run file and no dispatch exist for v4; "
+                   "Verification 44 and the owner's conditional decision (A-13 item 3) are pending")
+    d["authorities"]["register"] = ref(C.MR / "orchestrator/AUTHORITY-REGISTER.md")
+    d["authorities"]["applied"] = list(v3["authorities"]["applied"]) + ["A-13"]
+    d["authorities"]["summary"]["A-13"] = ("owner decisions of 2026-10-07 for the overnight run: item 2 authorizes the v4 declaration preparation and "
+                                           "the offline dry rehearsal after Verification 43 (new stamp, folder, scope name and hash; scripted provider "
+                                           "only; the rehearsal must exercise real baseline facts on F009, F020 and F030); item 3 (verbatim in "
+                                           "owner_conditional_decision) is a precondition, not an authorization; item 6 commits the v3 RUN and "
+                                           "authorization files as the record")
+    d["owner_conditional_decision"] = {
+        "source": ref(C.MR / "orchestrator/AUTHORITY-REGISTER.md") | {"entry": "A-13", "item": 3},
+        "verbatim": item3,
+        "kind": ("PRECONDITION, NOT AN AUTHORIZATION: this declaration authorizes nothing; whether conditions (a), (b) and (c) hold is "
+                 "decided outside this file (Verification 44, the orchestrator, the owner); no scope, token, RUN file, authorization file or "
+                 "invocation may follow from this record alone"),
+        "conditions_as_named": {"a": "Verification 43 of the harness reports no blocker",
+                                "b": "the dry rehearsal exercises F009/F020/F030 and passes",
+                                "c": "the pip freeze equality precondition of RUNBOOK-ADDENDUM-R42.md before invocation 1 and every resume"}}
+    d["binding_manifest_sha256"] = C.sha256_file(C.BINDING43)
+    if d["binding_manifest_sha256"] != C.BINDING43_SHA:
+        raise C.PacketMismatch("PACKET MISMATCH: the review43 harness manifest")
+    r = d["run"]
+    r.update({"stamp": C.STAMP, "sandbox_base": C.SANDBOX_BASE.as_posix(), "folder": run_folder, "allowance": f"{run_folder}/allowance.sqlite",
+              "capture_store": f"{run_folder}/capture.sqlite", "run_state": f"{run_folder}/RUN-STATE.json"})
+    r["base_justification"] = [
+        "C:/t/r2x/r42-sandbox matches the bound preflight's declared-base rule C:/t/r2x/r<NN>-sandbox (unchanged from v3); this task's dry runs and demonstrations use the driver-side dry base C:/t/r2x/r42-sandbox/r43p/sb (r43p_base.py) and stamps beginning 'r43d', never 'r32-v4'; r32-v3 (executed) is never reused",
+        r["base_justification"][1].replace("the same lengths as v2's", "the same lengths as v3's and v2's"),
+        r["base_justification"][2]]
+    a = d["authorization"]
+    a["path"] = pinned
+    a["two_hash_procedure"]["run_file"] = run_path
+    a["two_hash_procedure"]["budget_authorization_names"] = [
+        "the frozen hash", "the digest", "the RUN hash", f"the absolute RUN-file path {run_path}", f"the absolute authorization path {pinned}",
+        f"the scope {C.SCOPE} with limits {json.dumps(d['ledger']['limits'], sort_keys=True)}",
+        "the first invocation (runner_r32.py run --mode live, RUNBOOK section 5.1)",
+        "optionally (A-11 section 4, the owner's choice): one authorization file for up to 3 planned invocations (invocations_authorized, nonces)"]
+    a["runbook"] = ("RUNBOOK.md in this package (exact, ordered, absolute paths, cmd.exe; not written by task R43-40: it is written before any D1/D2 "
+                    "step, with v3's RUNBOOK.md as the model) and SCOPE-CREATION-COMMAND.md for the scope")
+    a["invocation"] = dict(a["invocation"], working_directory=C.HARNESS43.as_posix(),
+                           run=(f"\"{C.PY}\" -B runner_r32.py run --mode live --declaration \"{run_path}\" --declaration-sha <RUN hash> --run-set "
+                                f"\"{C.RUN_SET.as_posix()}\" --binding \"{C.BINDING43.as_posix()}\" --binding-sha {d['binding_manifest_sha256']}"),
+                           harness_copy=("PILOT/review43/scripts/harness-r32 is the only harness BINDING-MANIFEST-R43-HARNESS binds as runnable "
+                                         "(harness_r43_package); neither the review42 harness nor the v3 package scripts are run for v4"))
+    d["provider_env"]["AI_LEDGER_SCOPE"] = C.SCOPE
+    d["ledger"]["scope"] = C.SCOPE
+    d["ledger_detail"]["creation"] = v3["ledger_detail"]["creation"].replace(
+        "this task created no scope (AI ledger 483 entries / 17 scopes / 0 amendments before and after)",
+        "task R43-40 created no scope (AI ledger 484 entries / 18 scopes / 0 amendments before and after, the v3 scope present, no v4 scope)")
+    led = C.ledger_state()
+    d["ledger_baseline"] = {
+        "at_freeze": {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")},
+        "v3_scope_present": C.V3_SCOPE in led["scope_names"], "v4_scope_present": C.SCOPE in led["scope_names"],
+        "rule": ("Verification 43 R43V-04: the build, dry-exercise and preflight scripts of this package expect 484 / 18 / 0 (r42common.LEDGER_EXPECTED, "
+                 "re-pinned in the v4 copies only; V4-BUILD-DIFF.md) and compare the ledger before and after; the runtime harness never reads "
+                 "that pin; before the scope creation the declared scope must not exist, and after it only the declared scope may grow "
+                 "(preflight_r32.ledger_live_check, unchanged)")}
+    d["provider"]["owner_confirmable"]["ledger.scope"] = f"declared {C.SCOPE!r} (a new name; no scope of that name exists)"
+    d["isolation"] = PF.isolation_binding()
+    if d["isolation"]["allowed_under_forbidden"]["harness"] != C.HARNESS43.as_posix():
+        raise C.PacketMismatch(f"PACKET MISMATCH: isolation harness {d['isolation']}")
+    d["isolation_detail"]["lane_env_checks"] = "dry-run/lane-env/LANE-ENV-<lane>.json of this package (the four lanes' live environment checked offline)"
+    hv = d["harness"]
+    hv["package"] = "PILOT/review43/"
+    hv["package_manifest"] = ref(C.BINDING43)
+    hv["package_check"] = ref(C.MR / "reviews/M2-review-43-harness/INDEPENDENT-PACKAGE-CHECK.json")
+    hv["binding_manifest"] = ref(C.BINDING43) | {"entries": sum(len(v) for v in binding["files"].values()),
+                                                 "supersedes": "review43/BINDING-MANIFEST-R43.json e1735093... (task 37) for the harness code and the candidate tree; it carries BINDING-MANIFEST-R42 00ae5f98... (v3's) and the R43 trees"}
+    hv["accepted_by"] = ("Verification 43 (task R43-39V): VERIFIED WITH CONDITIONS, 0 blockers, 0 majors; minors R43V-04, R43V-05, R43V-09, "
+                         "R43V-10 answered by this package (verification43_items); review42 was accepted by Verification 42 (ORCH-10 VERIFIED)")
+    hv["modules"] = modules
+    hv["contracts"] = dict(hv["contracts"]) | {"harness_repoint_diff_r43": ref(C.REVIEW43 / "HARNESS-REPOINT-DIFF.md")}
+    hv["lineage"] = dict(hv["lineage"]) | {"review42": {"binding": ref(C.BINDING42), "manifest": ref(C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json"),
+                                                       "contract_v5": ref(C.REVIEW42 / "LIVE-RUN-CONTRACT.md"),
+                                                       "change_record": ref(C.REVIEW42 / "CHANGE-RECORD-R42.md"),
+                                                       "accepted_by": "Verification 42 (ORCH-10 VERIFIED); declaration v3 ran on it (2026-10-07)"}}
+    hv["bound_code_used_as_is"] = ("the bound code runs unchanged from PILOT/review43/scripts/harness-r32 under the bound interpreter (the review42 "
+                                   "harness with only its application-tree paths and HEAD hashes re-pointed: HARNESS-REPOINT-DIFF.md); this "
+                                   "package's preflight, dry exercise and demonstrations ran byte copies of the same files (C.check_run_copy) "
+                                   "with preflight_r32.HERE set to the bound folder for the isolation key only (C.declared_here)")
+    d["request_path_coverage"]["dynamic"] = dict(d["request_path_coverage"]["dynamic"],
+                                                 junit=ref(C.REVIEW43 / "tests/test_global_provider_r42.xml"),
+                                                 result=ev["global_provider_tests_r43"])
+    d["reviews"] = dict(d["reviews"]) | {
+        "verification42": ref(C.MR / "reviews/M2-review-42/INDEPENDENT-VERIFICATION.md"),
+        "verification42_findings": ref(C.MR / "reviews/M2-review-42/FINDINGS.json"),
+        "runbook_addendum_r42": ref(C.MR / "orchestrator/RUNBOOK-ADDENDUM-R42.md"),
+        "review43_report": ref(pathlib.Path("C:/t/r2x/r42-sandbox/REVIEW-43-REPORT-2026-10-07.md")),
+        "verification43": ref(C.MR / "reviews/M2-review-43-harness/INDEPENDENT-VERIFICATION.md"),
+        "verification43_findings": ref(C.MR / "reviews/M2-review-43-harness/FINDINGS.json"),
+        "verification43_package_check": ref(C.MR / "reviews/M2-review-43-harness/INDEPENDENT-PACKAGE-CHECK.json")}
+    d["trees_r43"] = {
+        "baseline": {"tree": C.BASELINE[0], "commit": C.BASELINE[1], "parent": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3",
+                     "branch": "r43/grammar-remediation"},
+        "candidate": {"tree": C.CANDIDATE[0], "commit": C.CANDIDATE[1], "parent": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d",
+                      "branch": "r43/grammar-remediation",
+                      "checkout": "cand-r30n: the line-ending-normalized clone of cand-r30 (same commit and tree; core.autocrlf false; Verification 43 check 4)"},
+        "patch_id": "2aa4c0b7a22c9df16286337e5d92cc77379a8bc3",
+        "document_control_py": ref(C.BASELINE_BACKEND / "app/services/document_control.py"),
+        "parser_version": "parse-2026-10-07.10 (the underscore joiner in a reference's prefix: ASC_EGTS; the owner's F009 ruling of 2026-10-07)",
+        "corrected_v4_05": ("V4-05 of docs/R32-V4-PREPARATION-LIST.md names cand-r30; the runnable candidate is cand-r30n (the same commit "
+                            "436daef2, line endings normalized); R32-V4-PREPARATION-LIST-CORRECTED.md in this package carries the correction (the "
+                            "owner's file is not edited)"),
+        "requirements_equal": ev["requirements_equal"]}
+    d["interpreter_detail"] = dict(d["interpreter_detail"], r43_trees=(
+        "the R43 change set touches only document_control.py, one test, one test file and fixtures; backend/requirements.txt is byte-equal in "
+        "frozen-r12, frozen-r13, cand-r29 and cand-r30n (requirements_equal in trees_r43); the four lanes import app from frozen-r13 and cand-r30n "
+        "under the bound interpreter (Verification 43 check 6 and this package's dry-run/lane-env)"))
+    d["preconditions"] = {
+        "pip_freeze": {"sha256": PIP_FREEZE_SHA, "command": f"\"{C.PY}\" -B -m pip freeze", "source": ref(C.MR / "orchestrator/RUNBOOK-ADDENDUM-R42.md") | {"section": 1},
+                       "distributions_record": ref(C.V3 / "evidence/INTERPRETER-CHECK.json"),
+                       "rule": "R42-09: before invocation 1 and before every resume the output's sha256 equals this value (57 distributions); any difference: stop; nothing is installed, upgraded or removed in the venv while the experiment is open"},
+        "ledger_baseline": "ledger_baseline (484 / 18 / 0 at freeze; no v4 scope)",
+        "owner_conditional_decision": "owner_conditional_decision (A-13 item 3, verbatim; a precondition, not an authorization)",
+        "no_v4_run_folder": f"{run_folder} must not exist before the owner's first invocation",
+        "v3_artifacts_untouched": "the v3 run folder, scope, owner records, RUN and authorization files are never edited, moved, deleted or reused"}
+    d["test_exceptions"] = {"test_runner_r32.py::test_no_authorization_file_was_written_by_the_tests": {
+        "finding": "Verification 43 R43V-05 (minor; ruled a test-environment artefact and v4 precondition, not a harness defect)",
+        "cause": ref(C.V3 / C.AUTH_NAME) | {"committed_as": "7a1bf6f"},
+        "declared_exception": ("the test searches the sandbox base, C:/t/iso/work/r2x/r38 and PILOT for OWNER-DISPATCH-AUTHORIZATION*.json and finds "
+                               "the owner's committed v3 file; it fails in every run while that file exists; the file is never removed and the "
+                               "test is not changed by this task; any other failure of the test (another file) is not covered by this exception")}}
+    d["verification43_items"] = ev["verification43_items"]
+    d["v4_preparation_items"] = ev["v4_preparation_items"]
+    d["standing_status_at_v4_freeze"] = {"M4 (historical M2)": "CHANGES STILL REQUIRED", "M3": "accepted (7 October 2026)",
+                                         "note": "standing_status is carried from v3 unchanged as the record of v3's freeze"}
+    d["resume_authorization"]["implementation"]["guard"] = modules["dispatch_guard_r32"]
+    dis = list(d["disclosures"])
+    rep = {
+        "the dry exercise of this declaration ran the review42 package code unchanged": (
+            "the dry exercise of this declaration runs byte copies of the review43 harness (dry base C:/t/r2x/r42-sandbox/r43p/sb, driver side) with "
+            "reader 'none' and the refusing stub: it exercises the chain, the deferral / resume loop and the scorer and is not a result; the "
+            "bound harness's dry mode never runs an application reader on a cohort document (runner_r32.py: reader 'application' only live or "
+            "with --dry-synthetic; lane_r32.py asserts it), so no dry run of this package produces real baseline facts (the R43-40 rehearsal "
+            "finding, reported to Verification 44)"),
+        "isolation: every lane refuses an environment value": (
+            "isolation: every lane refuses an environment value, setting, import path or loaded module under the merged installation except the "
+            "bound venv and the review43 harness folder; inherited operating-system variables are checked, not replaced (isolation_detail)")}
+    for i, x in enumerate(dis):
+        for start, new in rep.items():
+            if x.startswith(start):
+                dis[i] = new
+    missing = [s for s in rep if not any(x == rep[s] for x in dis)]
+    if missing:
+        raise C.PacketMismatch(f"disclosures not found for replacement: {missing}")
+    dis += [
+        "v3 was executed on 2026-10-07 and is terminal: INVALID and INELIGIBLE after 1 request (a resolved-truth critical in B on F009 page 3: the frozen-r12 baseline accepted P05-SD-FA-0006 against the resolved truth B01-ASC-SD-ELE-0034); the owner ruled F009 a BASELINE_PROCESSING_DEFECT (the reference grammar rejected '_' in ASC_EGTS); v4 runs the corrected baseline frozen-r13 and candidate cand-r30n (trees_r43)",
+        "V4-01 (R43-RESIDUAL-F021-P4, verbatim as to trigger and observed exposure): trigger -- document_control.parse_page is called for a drawing sheet without a sheet (the title-block reader title_block.read_page returned no block, or a block without a number), so the page's identity falls back to the first identity candidate of the text layer in reading order; on the EMAAR / Al Sahel sheets the drawing-references table (three fire-alarm sheets, e.g. B01-02-ASC_EGTS-P03_P04-SD-FA-0005-01) precedes the sheet's own DRAWING NO. cell in the text layer; under the corrected grammar the first table row is taken; the _CROSS_REFERENCE guard does not fire. Observed exposure -- in the R32 v3 run every F021 sheet (pages 4 to 7) had a title-block observation (titleblock-3, number read), so no F021 sheet reached the fallback path; cohort re-check: 246 pages, 90 with a text layer, 24 pages changed, all in the six EMAAR documents of EP-27331 (0034, 0037, 0047, 0052, 0075, 0084), none elsewhere; the 156 scanned pages go through the application's OCR and are not covered; before the correction the same fallback path on F009-shaped sheets recorded a truncated own number (P05-SD-FA-0006): the class of error pre-exists (an F021-shaped sheet whose title block yields no number takes the first drawing-references row as its identity)",
+        "V4-02: the R43 residuals addendum C:/t/r2x/r42-sandbox/R43-RESIDUALS-ADDENDUM-2026-10-07.md (F1, F2, F3; record only) is cited beside R43-RESIDUAL-F021-P4",
+        "V4-03: the ratification of the parser-identity assertion update is cited as R43-35 in docs/R43-SESSION-LOG.md",
+        "V4-04: DRAWINGS_AI_REVIEW_ENABLED=false in every lane's environment and in the application's settings is checked by every lane (application_env, unchanged) and in this package's preflight; the live installation's Drawings Assistant (DRAWINGS_CHAT_AI_ENABLED=true in the merged installation's .env) is outside the lanes",
+        "ledger baseline (R43V-04): the package scripts expect 484 / 18 / 0 at the v4 freeze (the v3 scope present); the runtime harness does not read that pin",
+        "test exception (R43V-05): test_no_authorization_file_was_written_by_the_tests fails on the owner's committed v3 authorization file (test_exceptions); declared, not fixed, the file never removed",
+        "reproducible preflight (R43V-09): this package's preflight driver imports only bound package scripts and the bound harness (byte copies checked by hash); no scratch helper",
+        "audit guard (R43V-10): the package guard used by this package's tests, dry runs and demonstrations denies every live run folder r32-v<N>, the owner records (no read either), the AI ledger folder, the trees and the frozen packages; its allowed roots are this task's work folder and this package",
+        "the R42-09 pip-freeze precondition is carried (preconditions.pip_freeze)"]
+    d["disclosures"] = dis
+    d["forbidden_after_authorization"] = list(d["forbidden_after_authorization"]) + [
+        "using the executed v3 declaration 9a55fa7b...1b40, its RUN file c31cccd4...2b6a, its run folder, its scope or its nonces for anything but the record",
+        "running the review42 harness or any harness other than PILOT/review43/scripts/harness-r32 for v4"]
+    d["bound_files_rehashed"] = {"rule": "every {path, sha256} node of this declaration was re-hashed at build time and equals; v3's carried nodes equal v3's hashes "
+                                         "(re-pointed nodes: the R43 trees at their new paths; review43 harness nodes take BINDING-MANIFEST-R43-HARNESS's hashes)",
+                                 "v3_nodes_equal": ev["v3_nodes_equal"], "harness_nodes_rebound": rebound}
+    return d
+
+
+def evidence_v4() -> dict:
+    tests43 = json.loads((C.REVIEW43 / "tests/SUMMARY.json").read_text(encoding="utf-8"))
+    v3nodes = bound_nodes(json.loads(v3_bytes().decode("utf-8")))
+    eq = sum(1 for _jp, p, s in v3nodes if C.sha256_file(p) == s)
+    req = {t: C.sha256_file(pathlib.Path(t) / "backend/requirements.txt") for t in ("C:/t/iso/frozen-r12", "C:/t/iso/frozen-r13", "C:/t/iso/cand-r29", "C:/t/iso/cand-r30n")}
+    return {
+        "global_provider_tests_r43": tests43["modules"].get("test_global_provider_r42"),
+        "v3_nodes_equal": f"{eq} of {len(v3nodes)} (v3's nodes at v3's paths)",
+        "requirements_equal": {"sha256": req, "all_equal": len(set(req.values())) == 1},
+        "verification43_items": {
+            "1_isolation_harness": "isolation.allowed_under_forbidden.harness = PILOT/review43/scripts/harness-r32 (preflight_r32.isolation_binding of the bound folder)",
+            "2_binding_and_trees": "binding_manifest_sha256 f35355aa...374a7; harness.*, authorization.invocation.harness_copy and working_directory name review43; trees, lanes and evaluator re-pointed to frozen-r13 7ec3d2cf / cand-r30n 436daef2 and checked in text by DECLARATION-DIFF (validate_declaration does not check trees); V4-05 corrected in R32-V4-PREPARATION-LIST-CORRECTED.md",
+            "3_new_stamp_folder_scope_paths": f"stamp {C.STAMP}, folder {C.RUN_FOLDER.as_posix()}, scope {C.SCOPE}, pinned authorization {(C.PACKAGE / C.AUTH_NAME).as_posix()}, RUN file {(C.PACKAGE / C.RUN_NAME).as_posix()}; none created",
+            "4_ledger_baseline": "re-pinned to 484 / 18 / 0 in the v4 copies of r42common.py (LEDGER_EXPECTED, read by build_declaration_r42, facts_r42, package_r42, dry_exercise_r42, preflight_r42); the no-run-folder and no-authorization-file invariants are before/after comparisons in the v4 preflight (V4-BUILD-DIFF.md)",
+            "5_authorization_file_test": "declared exception (test_exceptions), path and sha256 of the v3 file; no harness test change",
+            "6_dry_rehearsal_real_facts": "attempted in task R43-40: the bound harness's dry mode cannot process a cohort document (finding reported to Verification 44); see the package's REHEARSAL record",
+            "7_reproducible_preflight": "preflight_r42.py of this package imports only r42common / build_declaration_r42 / create_scope_r42 of the package and the bound review43 harness (checked byte copies); all bound by the v4 manifest",
+            "8_guard": "scripts/guard/sitecustomize.py (R43V-10): live run folders and owner records denied",
+            "9_carried": "V4-01..V4-04 in disclosures and v4_preparation_items; the R42-09 pip-freeze precondition in preconditions.pip_freeze"},
+        "v4_preparation_items": {
+            "source": ref(C.EP / "docs/R32-V4-PREPARATION-LIST.md"),
+            "corrected_copy": "R32-V4-PREPARATION-LIST-CORRECTED.md in this package (V4-05: cand-r30 -> cand-r30n)",
+            "V4-01": "disclosures (R43-RESIDUAL-F021-P4 verbatim as to trigger and observed exposure)",
+            "V4-01_entry": ref(pathlib.Path("C:/t/r2x/r42-sandbox/R43-REVIEW-PACKAGE/R43-RESIDUAL-F021-P4.md")),
+            "V4-02": ref(pathlib.Path("C:/t/r2x/r42-sandbox/R43-RESIDUALS-ADDENDUM-2026-10-07.md")),
+            "V4-03": "R43-35 in docs/R43-SESSION-LOG.md",
+            "V4-04": "application_env DRAWINGS_AI_REVIEW_ENABLED=false (unchanged) checked in every lane and in the v4 preflight's lane checks",
+            "V4-05": "trees_r43: frozen-r13 7ec3d2cf (parent 3d5607d) and cand-r30n 436daef2 (parent a8aaced), patch-id 2aa4c0b7"}}
+
+
 def main(argv=None) -> int:
@@ -516,10 +812,11 @@
     import subprocess  # noqa: F401
-    binding_sha = C.sha256_file(C.BINDING42)
-    man = json.loads(C.BINDING42.read_text(encoding="utf-8"))
-    bad = [p for p, w in man["files"]["harness_r42_package"].items() if C.sha256_file(p) != w]
+    binding_sha = C.sha256_file(C.BINDING43)
+    man = json.loads(C.BINDING43.read_text(encoding="utf-8"))
+    bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
     if bad:
-        raise C.PacketMismatch(f"PACKET MISMATCH: harness files differ from BINDING-MANIFEST-R42: {bad[:3]}")
+        raise C.PacketMismatch(f"PACKET MISMATCH: harness files differ from BINDING-MANIFEST-R43-HARNESS: {bad[:3]}")
+    C.check_run_copy()
     led = C.ledger_state()
     if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"]:
-        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led['entries']}/{led['scopes']}/{led['limit_amendments']} (expected 483/17/0 and no scope {C.SCOPE!r})")
+        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led['entries']}/{led['scopes']}/{led['limit_amendments']} (expected 484/18/0 and no scope {C.SCOPE!r})")
     if C.RUN_FOLDER.exists():
@@ -531,3 +828,3 @@
     declared_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
-    decl = build(declared_at, evidence())
+    decl = build_v4(declared_at, evidence_v4())   # R43-40: v4 from the frozen v3 bytes
     rh = rehash_all(decl)
@@ -538,3 +835,4 @@
         raise RuntimeError("a Desktop path survived the re-pointing")
-    import preflight_r32 as PF  # noqa: E402  (review42)
+    import preflight_r32 as PF  # noqa: E402  (review43; R43-40: HERE = the bound folder, C.declared_here)
+    C.declared_here(PF)
     mem = json.loads(text)
```

### `cli_version_drill_r42.py`

```diff
--- declaration-r32-v3/scripts/cli_version_drill_r42.py
+++ declaration-r32-v4/scripts/cli_version_drill_r42.py
@@ -14,2 +14,3 @@
 
+C.check_run_copy()                                  # R43-40: the review43 harness (run copy checked against its binding)
 sys.path.insert(0, str(C.HARNESS42))
@@ -17,7 +18,12 @@
 import runner_r32 as RN  # noqa: E402
+import preflight_r32 as PF  # noqa: E402  (R43-40)
+import sandbox_ingest_r32 as SI  # noqa: E402  (R43-40)
+import r43p_base as B  # noqa: E402  (R43-40: substitution S-BASE, the dry base inside the work folder)
+
+B.redirect(PF, RN, SI)
 
 stamp, out = sys.argv[1], pathlib.Path(sys.argv[2])
-folder = C.SANDBOX_BASE / stamp
-args = ["--mode", "dry", "--stamp", stamp, "--sandbox-base", C.SANDBOX_BASE.as_posix(), "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING42.as_posix(),
-        "--binding-sha", C.sha256_file(C.BINDING42)]
+folder = C.DRY_BASE / stamp                         # R43-40: dry base C:/t/r2x/r42-sandbox/r43p/sb; the review43 harness manifest
+args = ["--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING43.as_posix(),
+        "--binding-sha", C.sha256_file(C.BINDING43)]
 steps = []
```

### `create_scope_r42.py`

```diff
--- declaration-r32-v3/scripts/create_scope_r42.py
+++ declaration-r32-v4/scripts/create_scope_r42.py
@@ -10,3 +10,3 @@
       R34_OWNER_DISPATCH_TOKEN. Refuses (creating nothing) unless, in this order:
-        1. the owner's authorization file exists at the pinned path PILOT/declaration-r32-v3/OWNER-DISPATCH-AUTHORIZATION.json;
+        1. the owner's authorization file exists at the pinned path PILOT/declaration-r32-v4/OWNER-DISPATCH-AUTHORIZATION.json;
         2. --frozen-sha equals the frozen declaration file's sha256 and DECLARATION.sha256;
@@ -18,3 +18,3 @@
         5. the run folder does not exist (the scope is created once, before the first invocation; never for a resume);
-        6. the bound harness verifies (BINDING-MANIFEST-R42, every bound file) and the RUN declaration passes contract 5;
+        6. the bound harness verifies (BINDING-MANIFEST-R43-HARNESS, every bound file) and the RUN declaration passes contract 5;
         7. ORCH-10: the bound interpreter runs this command, the pinned CLI FILE hashes to the declared sha256 (read as
@@ -54,6 +54,7 @@
 def harness():
-    man = json.loads(C.BINDING42.read_text(encoding="utf-8"))
-    bad = [p for p, w in man["files"]["harness_r42_package"].items() if C.sha256_file(p) != w]
+    man = json.loads(C.BINDING43.read_text(encoding="utf-8"))          # R43-40: the review43 harness manifest and group
+    bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
     if bad:
         raise ScopeRefused(f"refused: PACKET MISMATCH: harness files differ: {bad[:3]}")
+    C.check_run_copy()
     if str(C.HARNESS42) not in sys.path:
@@ -62,2 +63,3 @@
     import preflight_r32 as PF  # noqa: E402
+    C.declared_here(PF)                                                # R43-40
     return DG, PF
@@ -101,3 +103,3 @@
         "5 run folder absent": {"path": C.RUN_FOLDER.as_posix(), "absent": not C.RUN_FOLDER.exists()},
-        "6 bound harness and contract 5": {"state": "checked in create mode (verify_binding R42; validate_declaration on the RUN file)"},
+        "6 bound harness and contract 5": {"state": "checked in create mode (verify_binding R43 harness manifest; validate_declaration on the RUN file)"},
         "7 interpreter, CLI file, free disk": {"interpreter": decl["interpreter"]["path"], "cli_file": decl["model_identity"]["cli"]["path"],
@@ -130,3 +132,3 @@
     rsha = C.sha256_bytes(run_bytes)
-    if run_sha_given in (fsha, C.V2_SHA):
+    if run_sha_given in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA):     # R43-40: never a frozen or the executed v3 hash
         raise ScopeRefused("refused: the RUN hash given is a FROZEN hash (a frozen declaration is never used with the runner or the scope)")
@@ -143,3 +145,3 @@
     DG, PF = harness()
-    if isinstance(auth, dict) and str(auth.get("declaration_sha256") or "") in (fsha, C.V2_SHA):
+    if isinstance(auth, dict) and str(auth.get("declaration_sha256") or "") in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA):   # R43-40
         raise ScopeRefused("refused: the authorization names a FROZEN hash; it must name the RUN hash")
@@ -153,3 +155,3 @@
         try:
-            PF.verify_binding(C.BINDING42, run_decl.get("binding_manifest_sha256"))
+            PF.verify_binding(C.BINDING43, run_decl.get("binding_manifest_sha256"))   # R43-40
         except PF.Refused as exc:
```

### `demos_r42.py`

```diff
--- declaration-r32-v3/scripts/demos_r42.py
+++ declaration-r32-v4/scripts/demos_r42.py
@@ -1,2 +1,5 @@
-"""ORCH-10 section 2.6 (R42PORT-IMPL): the scripted-provider demonstrations of the corrected harness. DRY / synthetic
+"""R43-40: the same demonstrations on the review43 harness for declaration-r32-v4 (byte copy checked against its binding;
+run folders under the dry base C:/t/r2x/r42-sandbox/r43p/sb, substitution S-BASE; stamps r43d-*; one more refusal case:
+an authorization naming the executed v3 RUN hash).
+ORCH-10 section 2.6 (R42PORT-IMPL): the scripted-provider demonstrations of the corrected harness. DRY / synthetic
 providers only: the refusing DryStub (dry mode) or, for the authorization drills, an in-process live-SHAPED runner with
@@ -35,2 +38,9 @@
 OUT = pathlib.Path(sys.argv[2])
+sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # R43-40: the package scripts
+import r42common as C  # noqa: E402
+import r43p_base as B  # noqa: E402
+
+if H_DIR != C.HARNESS42.resolve():
+    raise SystemExit(f"refused: the demonstrations run the checked harness folder {C.HARNESS42} only")
+COPY = C.check_run_copy()
 sys.path.insert(0, str(H_DIR))
@@ -44,2 +54,5 @@
 import visibility_r38 as V  # noqa: E402
+import sandbox_ingest_r32 as SI  # noqa: E402
+
+BASE = B.redirect(PF, RN, SI)                                         # R43-40: S-BASE
 
@@ -143,3 +156,3 @@
         rs = run_set(work, ids)
-        self.stamp = f"r42d-demo-{uuid.uuid4().hex[:8]}"
+        self.stamp = f"r43d-demo-{uuid.uuid4().hex[:8]}"
         self.args = ["--mode", "dry", "--stamp", self.stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha]
@@ -171,5 +184,6 @@
         led = H.fake_ledger(work / "fake-ledger.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0)})
-        self.stamp = f"r42d-demo-live-{uuid.uuid4().hex[:8]}"
+        self.stamp = f"r43d-demo-live-{uuid.uuid4().hex[:8]}"
         self.decl, self.dsha, self.rec = H.live_declaration(work / "pkg", binding_sha=sha, run_set_sha=hashlib.sha256(rs.read_bytes()).hexdigest(),
-                                                           stamp=self.stamp, ledger_path=led, run_set_path=rs)
+                                                           stamp=self.stamp, ledger_path=led, run_set_path=rs,
+                                                           sandbox_base=RN.SANDBOX_BASE.as_posix())   # R43-40: S-BASE
         self.args = ["--mode", "live", "--declaration", str(self.decl), "--declaration-sha", self.dsha, "--run-set", str(rs), "--binding", str(b),
@@ -238,2 +252,4 @@
         out["authorization_names_the_frozen_v2_hash"] = lv.run() | {"facts": lv.facts()}
+        lv.authorize(["nonce-demo-0123456789-e"], named=C.V3_RUN_SHA)      # R43-40: the executed v3 RUN hash
+        out["authorization_names_the_executed_v3_run_hash"] = lv.run() | {"facts": lv.facts()}
         lv.authorize(["nonce-demo-0123456789-d"])
@@ -505,5 +521,6 @@
     OUT.mkdir(parents=True)
-    work = RN.SANDBOX_BASE / f"r42d-demos-{uuid.uuid4().hex[:6]}"
+    work = RN.SANDBOX_BASE / f"r43d-demos-{uuid.uuid4().hex[:6]}"
     led0 = PF.ledger_counts(LEDGER)
-    res = {"name": "DEMOS-R42 (ORCH-10 section 2.6)", "harness": H_DIR.as_posix(), "work": work.as_posix(), "ledger_before": led0,
+    res = {"name": "DEMOS (R43-40) of the review43 harness for declaration-r32-v4 (the ORCH-10 section 2.6 demonstrations)", "harness": C.HARNESS43.as_posix(),
+           "imported_from": H_DIR.as_posix(), "run_copy": COPY, "dry_base": BASE, "work": work.as_posix(), "ledger_before": led0,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "demos": {}}
```

### `diff_declaration_r42.py`

```diff
--- declaration-r32-v3/scripts/diff_declaration_r42.py
+++ declaration-r32-v4/scripts/diff_declaration_r42.py
@@ -1,2 +1,16 @@
-"""ORCH-10 (R42PORT-IMPL): every difference between the frozen v2 declaration (f38fb281...25af) and the v3 declaration of
+"""R43-40: every difference between the executed v3 declaration (9a55fa7b...1b40) and the v4 declaration of this package,
+mechanically (the v2 -> v3 method of ORCH-10, below, with the R43 re-point in place of the Desktop re-point). Each leaf is:
+  unchanged            byte-equal value
+  repointed            equal once the R43 re-point is applied (frozen-r12 -> frozen-r13, cand-r29 -> cand-r30n, their HEADs, and
+                       the harness folder review42/scripts/harness-r32 -> review43/scripts/harness-r32; nothing else)
+  rebound              the sha256 of a {path, sha256} node whose path was re-pointed to a review43 harness file, equal to the hash
+                       BINDING-MANIFEST-R43-HARNESS binds for it (the 20 re-pointed harness files have new bytes)
+  changed / added / removed   an item of task R43-40 (each top-level key carries its reason)
+The PROTECTED values (as in v3) must be unchanged, repointed or rebound only; the script exits 3 otherwise. It also lists
+every string of v4 that still names an old identifier (frozen-r12, cand-r29, 3d5607d, a8aaced, the review42 harness folder,
+r32-v3, declaration-r32-v3) with its JSON path; outside the record keys (supersedes, lineage, reviews, disclosures, ...) none
+may remain (Verification 43 R43V-13: validate_declaration does not check trees). Writes DECLARATION-DIFF.json and
+DECLARATION-DIFF.md (once each). Usage: diff_declaration_r42.py
+
+ORCH-10 (R42PORT-IMPL): every difference between the frozen v2 declaration (f38fb281...25af) and the v3 declaration of
 this package, mechanically. Both files are flattened to leaf paths (dicts recursed, lists compared whole). Each leaf is:
@@ -13,2 +27,3 @@
 import pathlib
+import re
 import sys
@@ -17,2 +32,3 @@
 sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
+import build_declaration_r42 as BD  # noqa: E402  (R43-40: the R43 re-point map)
 import r42common as C  # noqa: E402
@@ -36,29 +52,36 @@
 REASONS = {
-    "schema": "the v3 schema id", "contract": "contract 5 (review42 preflight_r32.CONTRACT 'r42-live-contract-5')", "name": "names declaration v3 (merged installation)",
-    "task": "ORCH-10 / R42PORT-IMPL", "supersedes": "supersedes v2 f38fb281...25af (A-11; never to be run); v2's own supersedes record kept as lineage",
-    "declared_at_utc": "the time of this freeze", "status": "Verification 42 and the owner's decision card pending",
-    "authorities": "A-11 applied and summarised; the authority register re-hashed at its current (append-only) state",
-    "binding_manifest_sha256": "BINDING-MANIFEST-R42 (review42) instead of R39",
-    "run": "stamp r32-v3, base C:/t/r2x/r42-sandbox, folder C:/t/r2x/r42-sandbox/r32-v3 (same lengths as v2); the re-entry rule",
-    "authorization": "pinned path beside v3; the RUN file v3; the scope v3; invocation from review42 with the bound interpreter; contract v5 section 3 cited; the multi-invocation file fields (A-11 section 4)",
-    "model_identity": "the CLI pinned by ABSOLUTE PATH and file sha256 (contract 5); models, provider and version line unchanged",
-    "model_identity_detail": "the CLI rule (file hash before anything, version before the folder); the bundled 2.1.289 named as not used",
-    "provider_env": "AI_CLAUDE_CLI = the absolute CLI path; AI_LEDGER_SCOPE = the v3 scope; every other value unchanged",
-    "ledger": "the v3 scope name; path and limits unchanged", "ledger_detail": "create_scope_r42.py; the C1 disk check",
-    "project_request_bounds": "review42 PROJECT-REQUEST-BOUNDS.json (recomputed; equal to review39's in every verified key, the run-set path re-pointed)",
-    "project_request_bounds_detail": "adds the equality record with review39", "resume_detail": "review42 RESUME-INVOCATIONS-R42.json (byte-identical to R39's)",
-    "interpreter": "ADDED (contract 5): the bound interpreter", "interpreter_detail": "ADDED: requirements and import check of both trees",
-    "disk_precondition": "ADDED (contract 5): 2 GiB on C:, only upward (R41-10, C1)", "disk_precondition_detail": "ADDED",
-    "isolation": "ADDED (contract 5): the merged installation is forbidden except the venv and the review42 harness", "isolation_detail": "ADDED",
-    "resume_authorization": "ADDED (contract 5; A-11 section 4): the separable multi-invocation proposal, max 3",
-    "global_provider": "ADDED (contract 5; R40-04 option 2)", "request_path_coverage": "R40-04 closed by option 2: the refusing global provider; static and dynamic proof; v2's proof-based text kept as superseded",
-    "invocation_order": "ADDED (R41-09, R41-10, R41-11): the reordered invocation, re-entry and the dead-end cases", "portability": "ADDED: the re-pointing and the path lengths",
-    "harness": "review42 (manifest, binding, modules, contracts v5); review39 added to the lineage; the work records referenced in the v2 package",
-    "revision_comparison_rule": "implementation re-bound to the review42 copy (same hash)", "run_set": "selector re-bound to the review42 copy (same hash)",
-    "reviews": "Verification 41 (and its findings and package check) and RUNBOOK-ADDENDUM-R41 added", "dispatch_order": "the reordered invocation (contract v5 section 14)",
-    "provider": "owner-confirmable: the v3 scope, the CLI pin, the disk floor, the resume authorization; AI_CLAUDE_CLI declared absolute",
-    "verification40_items": "R40-04 now closed by option 2", "verification41_items": "ADDED: R41-09 to R41-15, R41-18, C1; the four r40 records bound by hash",
-    "bound_files_rehashed": "ADDED: the build-time re-hash record", "disclosures": "R40-04, R40-08 (R41-12 correction), the CLI dead-end (R41-09 closed), path length, the dry exercise (R41-13) restated; nine ORCH-10 disclosures added",
-    "forbidden_after_authorization": "four items added (v2, the merged installation's CLI / .env / data / code, run-folder records, the floor and the bound)",
+    "schema": "the v4 schema id", "name": "names declaration v4 (R43 trees, review43 harness)", "task": "R43-40 (A-13 item 2), ep-implementer",
+    "supersedes": "supersedes the executed v3 9a55fa7b...1b40 (its RUN file, authorization file and manifest named; the v3 binding R42 and the task-37 manifest named, superseded by the harness manifest f35355aa...); v3's own supersedes record kept as lineage",
+    "declared_at_utc": "the time of this freeze", "status": "Verification 44 and the owner's conditional decision pending",
+    "authorities": "A-13 applied and summarised; the authority register re-hashed at its current (append-only) state",
+    "binding_manifest_sha256": "BINDING-MANIFEST-R43-HARNESS (review43, f35355aa...374a7) instead of BINDING-MANIFEST-R42 (section 0 item 2)",
+    "run": "stamp r32-v4, folder C:/t/r2x/r42-sandbox/r32-v4 (same lengths as v3); the dry-base sentence (section 0 item 3)",
+    "authorization": "pinned path, RUN file and scope of v4; invocation from review43 with its manifest (harness_copy, working_directory); runbook pointer (section 0 items 2, 3)",
+    "provider_env": "AI_LEDGER_SCOPE = the v4 scope; every other value unchanged", "ledger": "the v4 scope name; path and limits unchanged",
+    "ledger_detail": "the creation sentence names 484 / 18 / 0 (R43V-04)", "isolation": "the review43 harness folder (section 0 item 1)",
+    "isolation_detail": "the lane checks of this package",
+    "harness": "review43 (binding manifest, modules re-pointed and rebound, accepted by Verification 43); review42 added to the lineage; the re-point diff added to the contracts",
+    "request_path_coverage": "the dynamic proof re-pointed to review43's test_global_provider_r42 junit and result",
+    "reviews": "Verification 42 and 43 (with findings and package check), RUNBOOK-ADDENDUM-R42 and the review-43 report added",
+    "provider": "owner-confirmable: the v4 scope", "resume_authorization": "the guard module re-pointed to review43 (rebound)",
+    "interpreter_detail": "a sentence on the R43 trees added (requirements equal)",
+    "disclosures": "the dry-exercise and isolation disclosures restated for review43; ten R43-40 disclosures added (v3 result, V4-01..V4-04, R43V-04/05/09/10, pip freeze)",
+    "forbidden_after_authorization": "two items added (the executed v3 artifacts; any harness but review43)",
+    "bound_files_rehashed": "the v4 re-hash record (v3 nodes; rebound harness nodes)",
+    "owner_conditional_decision": "ADDED (section 2 item 6): A-13 item 3 verbatim, a precondition, not an authorization",
+    "ledger_baseline": "ADDED (section 0 item 4, R43V-04): 484 / 18 / 0 at freeze",
+    "preconditions": "ADDED (section 0 item 9): pip freeze (R42-09), ledger, conditional decision",
+    "test_exceptions": "ADDED (section 0 item 5, R43V-05): the authorization-file test",
+    "trees_r43": "ADDED (section 0 item 2, V4-05 corrected): commits, parents, patch-id",
+    "verification43_items": "ADDED: the nine readiness items of Verification 43 check 8",
+    "v4_preparation_items": "ADDED (section 0 item 9): V4-01..V4-05",
+    "standing_status_at_v4_freeze": "ADDED: M4 CHANGES STILL REQUIRED, M3 accepted (standing_status carried unchanged as v3's record)",
 }
+OLD_IDS = re.compile(r"frozen-r12|cand-r29|3d5607d|a8aaced|review42/scripts/harness-r32|r32-v3|declaration-r32-v3")
+RECORD_KEYS = ("supersedes", "harness.lineage", "harness.contracts", "harness.review39_snapshot_before", "harness.review39_work_records", "reviews",
+               "disclosures", "forbidden_after_authorization", "authorities", "verification43_items", "verification40_items", "verification41_items",
+               "trees_r43", "ledger_baseline", "test_exceptions", "bound_files_rehashed", "preconditions", "v4_preparation_items", "interpreter_detail",
+               "portability", "request_path_coverage", "invocation_order", "owner_conditional_decision", "harness.package_check",
+               "project_request_bounds_detail", "resume_detail", "run.base_justification", "isolation_detail", "dispatch_order", "model_identity_detail",
+               "authorization.authorization_rule_v5", "authorization.placeholder_rule", "authorization.two_hash_procedure.independent_verification")
 
@@ -76,3 +99,14 @@
 def repoint(v):
-    return json.loads(json.dumps(v).replace(C.DESKTOP_EP, C.MERGED_EP))
+    return BD.repoint43(v)
+
+
+def strings(o, path=""):
+    if isinstance(o, dict):
+        for k, v in o.items():
+            yield from strings(v, f"{path}.{k}" if path else k)
+    elif isinstance(o, list):
+        for i, v in enumerate(o):
+            yield from strings(v, f"{path}[{i}]")
+    elif isinstance(o, str):
+        yield path, o
 
@@ -80,5 +114,5 @@
 def main(argv=()) -> int:
-    v3_path, out_dir = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE                 # dev mode: --v3 <file> --out <work dir>
-    if "--v3" in argv:
-        v3_path, out_dir = pathlib.Path(argv[argv.index("--v3") + 1]), pathlib.Path(argv[argv.index("--out") + 1])
+    v4_path, out_dir = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE                 # dev mode: --v4 <file> --out <work dir>
+    if "--v4" in argv:
+        v4_path, out_dir = pathlib.Path(argv[argv.index("--v4") + 1]), pathlib.Path(argv[argv.index("--out") + 1])
     for f in ("DECLARATION-DIFF.json", "DECLARATION-DIFF.md"):
@@ -86,8 +120,7 @@
             raise SystemExit(f"refused: {f} is written once")
-    old_b, new_b = (C.V2 / C.V2_NAME).read_bytes(), v3_path.read_bytes()
-    if C.sha256_bytes(old_b) != C.V2_SHA:
-        raise SystemExit("PACKET MISMATCH: v2")
+    old_b, new_b = BD.v3_bytes(), v4_path.read_bytes()
     old, new = json.loads(old_b), json.loads(new_b)
+    bound = json.loads(C.BINDING43.read_text(encoding="utf-8"))["files"][C.HARNESS_GROUP]
     fo, fn = flat(old), flat(new)
-    leaves = {"unchanged": [], "repointed": [], "changed": [], "added": [], "removed": []}
+    leaves = {"unchanged": [], "repointed": [], "rebound": [], "changed": [], "added": [], "removed": []}
     for k in sorted(set(fo) | set(fn)):
@@ -101,2 +134,5 @@
             leaves["repointed"].append(k)
+        elif k.endswith(".sha256") and fn.get(k[:-7] + ".path") in bound and bound[fn[k[:-7] + ".path"]] == fn[k] \
+                and repoint(fo.get(k[:-7] + ".path")) == fn[k[:-7] + ".path"]:
+            leaves["rebound"].append(k)
         else:
@@ -106,12 +142,9 @@
         mine = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
-        rep = [x for x in leaves["repointed"] if x == k or x.startswith(k + ".")]
-        state = ("added" if k not in old else "removed" if k not in new else "changed" if mine else "repointed only" if rep else "unchanged")
+        rep = [x for cat in ("repointed", "rebound") for x in leaves[cat] if x == k or x.startswith(k + ".")]
+        state = ("added" if k not in old else "removed" if k not in new else "changed" if mine else "repointed / rebound only" if rep else "unchanged")
         tops[k] = {"state": state, "reason": REASONS.get(k, "unchanged" if state == "unchanged" else
-                                                         "only the Desktop paths re-pointed" if state == "repointed only" else "SEE LEAVES"),
-                   "leaves_changed": sorted(mine), "leaves_repointed": len(rep)}
+                                                         "only the R43 re-point (and the harness manifest's hashes)" if state.startswith("repointed") else "SEE LEAVES"),
+                   "leaves_changed": sorted(mine), "leaves_repointed_or_rebound": len(rep)}
     prot = {}
-    for k in PROTECTED_KEYS:
-        bad = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
-        prot[k] = {"ok": not bad, "violations": bad}
-    for k in PROTECTED_LEAVES:
+    for k in PROTECTED_KEYS + PROTECTED_LEAVES:
         bad = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
@@ -119,4 +152,13 @@
     unexplained = [k for k, v in tops.items() if v["state"] in ("changed", "added", "removed") and k not in REASONS]
-    counts = {s: sum(1 for v in tops.values() if v["state"] == s) for s in ("unchanged", "repointed only", "changed", "added", "removed")}
-    res = {"v2": {"path": (C.V2 / C.V2_NAME).as_posix(), "sha256": C.V2_SHA}, "v3": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(),
+    counts = {s: sum(1 for v in tops.values() if v["state"] == s) for s in ("unchanged", "repointed / rebound only", "changed", "added", "removed")}
+    olds = [(p, sorted(set(OLD_IDS.findall(s)))) for p, s in strings(new) if OLD_IDS.search(s)]
+    outside = [(p, ids) for p, ids in olds if not any(p == r or p.startswith(r + ".") or p.startswith(r + "[") for r in RECORD_KEYS)]
+    tt = {"trees": new["trees"], "lanes": {k: {x: v.get(x) for x in ("tree", "commit")} for k, v in new["lanes"].items()},
+          "evaluator_file": new["evaluator"]["file"]}
+    tt["ok"] = (new["trees"]["baseline"]["tree"] == C.BASELINE[0] and new["trees"]["baseline"]["head"] == C.BASELINE[1]
+                and new["trees"]["candidate"]["tree"] == C.CANDIDATE[0] and new["trees"]["candidate"]["head"] == C.CANDIDATE[1]
+                and all(v.get("tree") in (None, C.BASELINE[0], C.CANDIDATE[0]) for v in new["lanes"].values())
+                and all(v.get("commit") in (None, C.BASELINE[1], C.CANDIDATE[1]) for v in new["lanes"].values())
+                and new["evaluator"]["file"]["path"].startswith(C.CANDIDATE[0] + "/"))
+    res = {"v3": {"path": (C.V3 / C.V3_NAME).as_posix(), "sha256": C.V3_SHA}, "v4": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(),
                                                                                     "sha256": C.sha256_bytes(new_b)},
@@ -124,11 +166,17 @@
            "top_level": tops, "leaves": leaves, "protected": prot, "protected_all_ok": all(v["ok"] for v in prot.values()),
-           "unexplained_top_level_changes": unexplained, "desktop_prefix_left_in_v3": C.DESKTOP_EP in new_b.decode("utf-8")}
-    res["ok"] = res["protected_all_ok"] and not unexplained and not res["desktop_prefix_left_in_v3"]
+           "unexplained_top_level_changes": unexplained,
+           "old_identifiers_in_v4": {"count": len(olds), "in_record_keys": len(olds) - len(outside), "outside_record_keys": outside, "all": olds},
+           "trees_text_check": tt}
+    res["ok"] = res["protected_all_ok"] and not unexplained and not outside and tt["ok"]
     C.write_json_once(out_dir / "DECLARATION-DIFF.json", res)
-    L = ["# DECLARATION-DIFF: v2 (`f38fb281…25af`, frozen, superseded, never run) → v3 (this package)", "",
-         f"- v3 sha256: `{res['v3']['sha256']}`.", "- Method: both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the absent Desktop "
-         "installation's prefix `C:/Users/moham/Desktop/dev/dev/ep-platform` replaced by `G:/dev (2)/dev/ep-platform-merged/ep-platform`), changed, added "
-         "or removed.", f"- Top-level keys: {counts}.", f"- Leaves: {res['leaf_counts']}.",
-         f"- **Protected values (every number and rule that must not change): {'ALL UNCHANGED (or re-pointed only)' if res['protected_all_ok'] else 'VIOLATED'}** "
-         f"({len(prot)} keys and leaves checked: {', '.join(sorted(prot))}).", "", "## Top-level keys", "", "| Key | State | Reason |", "|---|---|---|"]
+    L = ["# DECLARATION-DIFF: v3 (`9a55fa7b...1b40`, executed 2026-10-07, terminal) -> v4 (this package)", "",
+         f"- v4 sha256: `{res['v4']['sha256']}`.", "- Method: both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the R43 re-point: "
+         "`frozen-r12`->`frozen-r13`, `cand-r29`->`cand-r30n`, `3d5607d...`->`7ec3d2cf...`, `a8aaced...`->`436daef2...`, `review42/scripts/harness-r32`->"
+         "`review43/scripts/harness-r32`), rebound (the sha256 of a re-pointed review43 harness file, equal to the hash BINDING-MANIFEST-R43-HARNESS "
+         "binds), changed, added or removed.", f"- Top-level keys: {counts}.", f"- Leaves: {res['leaf_counts']}.",
+         f"- **Protected values (every number and rule that must not change): {'ALL UNCHANGED (or re-pointed / rebound only)' if res['protected_all_ok'] else 'VIOLATED'}** "
+         f"({len(prot)} keys and leaves checked).",
+         f"- Trees in text (R43V-13): {'frozen-r13 7ec3d2cf / cand-r30n 436daef2 in trees, lanes and evaluator' if tt['ok'] else 'NOT OK'}.",
+         f"- Old identifiers left in v4: {len(olds)}, {len(olds) - len(outside)} inside record keys, {len(outside)} outside.", "",
+         "## Top-level keys", "", "| Key | State | Reason |", "|---|---|---|"]
     for k, v in tops.items():
@@ -141,5 +189,10 @@
         L.append("")
+    L += [f"### repointed ({len(leaves['repointed'])}) and rebound ({len(leaves['rebound'])})", ""]
+    L += [f"- `{x}` (rebound)" for x in leaves["rebound"]] + [f"- `{x}`" for x in leaves["repointed"]]
+    L += ["", "## Old identifiers left in v4 (JSON path: identifiers)", ""]
+    L += [f"- `{p}`: {', '.join(ids)}" for p, ids in olds] or ["- none"]
     C.write_once(out_dir / "DECLARATION-DIFF.md", "\n".join(L) + "\n")
     print(json.dumps({"ok": res["ok"], "top_level_counts": counts, "leaf_counts": res["leaf_counts"], "protected_all_ok": res["protected_all_ok"],
-                      "violations": {k: v["violations"] for k, v in prot.items() if not v["ok"]}, "unexplained": unexplained}, indent=1))
+                      "violations": {k: v["violations"] for k, v in prot.items() if not v["ok"]}, "unexplained": unexplained,
+                      "old_identifiers_outside_record_keys": outside, "trees_text_ok": tt["ok"]}, indent=1))
     return 0 if res["ok"] else 3
```

### `dry_exercise_r42.py`

```diff
--- declaration-r32-v3/scripts/dry_exercise_r42.py
+++ declaration-r32-v4/scripts/dry_exercise_r42.py
@@ -1,2 +1,3 @@
-"""ORCH-10 (R42PORT-IMPL): the dry-mode exercise of the v3 declaration with the BOUND review42 harness, unchanged (the
+"""R43-40: the dry-mode exercise of the v4 declaration with the BOUND review43 harness (byte copies; S-BASE dry base).
+ORCH-10 (R42PORT-IMPL): the dry-mode exercise of the v3 declaration with the BOUND review42 harness, unchanged (the
 sandbox base is a declared parameter: C:/t/r2x/r42-sandbox; no twin), the refusing stub and reader 'none'.
@@ -16,3 +17,3 @@
            'run' then finishes -- Verification 41's dead-end no longer exists
-The AI ledger is read (mode=ro) before and after every phase: 483 / 17 / 0. 0 model requests. Staged PDF copies of every
+The AI ledger is read (mode=ro) before and after every phase: 484 / 18 / 0 (R43-40; v3: 483 / 17 / 0). 0 model requests. Staged PDF copies of every
 finished dry invocation are removed after it (scripts/trim_sandbox_r42.py rule); run records are kept."""
@@ -51,4 +52,4 @@
 def runner(cmd, stamp, run_set, inject=None) -> dict:
-    argv = [C.PY, "-B", "runner_r32.py", cmd, "--mode", "dry", "--stamp", stamp, "--sandbox-base", C.SANDBOX_BASE.as_posix(), "--run-set", str(run_set),
-            "--binding", C.BINDING42.as_posix(), "--binding-sha", C.sha256_file(C.BINDING42)] + (["--dry-inject", str(inject)] if inject else [])
+    argv = [C.PY, "-B", str(HERE / "runner_r43p.py"), cmd, "--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", str(run_set),
+            "--binding", C.BINDING43.as_posix(), "--binding-sha", C.sha256_file(C.BINDING43)] + (["--dry-inject", str(inject)] if inject else [])   # R43-40
     t0 = time.time()
@@ -70,3 +71,3 @@
 def trim(stamp):
-    for inv in sorted((C.SANDBOX_BASE / stamp).glob("inv-*")):
+    for inv in sorted((C.DRY_BASE / stamp).glob("inv-*")):
         sub = inv / "B" / "s"
@@ -79,3 +80,3 @@
 def state(stamp):
-    p = C.SANDBOX_BASE / stamp / "RUN-STATE.json"
+    p = C.DRY_BASE / stamp / "RUN-STATE.json"
     return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
@@ -100,2 +101,3 @@
 def checks_equal() -> tuple[dict, str]:
+    C.check_run_copy()                                              # R43-40
     sys.path.insert(0, str(C.HARNESS42))
@@ -132,3 +134,3 @@
             copied[p.name] = C.sha256_file(dest / p.name)
-    shutil.copyfile(C.SANDBOX_BASE / stamp / "RUN-STATE.json", dest / "RUN-STATE.json")
+    shutil.copyfile(C.DRY_BASE / stamp / "RUN-STATE.json", dest / "RUN-STATE.json")
     copied["RUN-STATE.json"] = C.sha256_file(dest / "RUN-STATE.json")
@@ -138,3 +140,3 @@
 def report_of(stamp, n=1):
-    return json.loads((C.SANDBOX_BASE / stamp / f"inv-{n}" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))
+    return json.loads((C.DRY_BASE / stamp / f"inv-{n}" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))
 
@@ -150,5 +152,5 @@
     led0 = C.ledger_counts()
-    stamp = f"r42d-single-{tag}"
+    stamp = f"r43d-single-{tag}"
     step = runner("run", stamp, C.RUN_SET)
-    out_dir = C.SANDBOX_BASE / stamp / "inv-1" / "out"
+    out_dir = C.DRY_BASE / stamp / "inv-1" / "out"
     rep = report_of(stamp)
@@ -183,5 +185,5 @@
                                             for d in docs if str(d["ep"]) == ep]})
-        stamp = f"r42d-m{ep}-{tag}"
+        stamp = f"r43d-m{ep}-{tag}"
         step = runner("run", stamp, rs)
-        out_dir = C.SANDBOX_BASE / stamp / "inv-1" / "out"
+        out_dir = C.DRY_BASE / stamp / "inv-1" / "out"
         rep = report_of(stamp)
@@ -228,6 +230,6 @@
     ldir.mkdir(parents=True, exist_ok=True)
-    shutil.copyfile(C.SANDBOX_BASE / stamp / "RUN-STATE.json", ldir / "RUN-STATE.json")
+    shutil.copyfile(C.DRY_BASE / stamp / "RUN-STATE.json", ldir / "RUN-STATE.json")
     per_inv = []
     for i in invs:
-        od = C.SANDBOX_BASE / stamp / f"inv-{i['n']}" / "out"
+        od = C.DRY_BASE / stamp / f"inv-{i['n']}" / "out"
         if (od / "RUN-REPORT.json").exists():
@@ -264,3 +266,3 @@
             C.write_json(inj, {"project_window": {"limit": limit, "window_s": 20}, "resume_policy": "full"})
-        loops[name] = deferral_loop(ST, name, f"r42d-{'p' if limit == 10 else 's'}{limit}-{tag}", rs27, inj)
+        loops[name] = deferral_loop(ST, name, f"r43d-{'p' if limit == 10 else 's'}{limit}-{tag}", rs27, inj)
     res = {"checks_before": checks, "declaration_sha256": fsha, "deferral_loops": loops, "ai_ledger_before": led0, "ai_ledger_after": C.ledger_counts(),
@@ -281,3 +283,3 @@
         C.write_json(inj, {"project_window": {"limit": 10, "window_s": 20}, "resume_policy": "full"})
-    lp = deferral_loop(ST, "cross-project-drill-window-10", f"r42d-xp-{tag}", C.RUN_SET, inj)
+    lp = deferral_loop(ST, "cross-project-drill-window-10", f"r43d-xp-{tag}", C.RUN_SET, inj)
     first = json.loads((ST / "cross-project-drill-window-10" / "RUN-REPORT-inv-1.json").read_text(encoding="utf-8"))
@@ -295,6 +297,6 @@
     out = ST / "CLI-VERSION-NOT-A-DEADEND.json"
-    r = subprocess.run([C.PY, "-B", str(HERE / "cli_version_drill_r42.py"), f"r42d-cli-{tag}", str(out)], cwd=str(HERE), env=ENV, capture_output=True,
+    r = subprocess.run([C.PY, "-B", str(HERE / "cli_version_drill_r42.py"), f"r43d-cli-{tag}", str(out)], cwd=str(HERE), env=ENV, capture_output=True,
                        text=True, encoding="utf-8", timeout=3600)
     res = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"error": r.stderr[-2000:]}
-    trim(f"r42d-cli-{tag}")
+    trim(f"r43d-cli-{tag}")
     ok = r.returncode == 0 and res.get("ok") is True
@@ -311,4 +313,5 @@
     leds = [x for p in ph.values() for x in (p["ai_ledger_before"], p["ai_ledger_after"])] + [C.ledger_counts()]
-    res = {"name": "DRY-EXERCISE (ORCH-10) of declaration-r32-v3 with the bound review42 harness", "tag": tag,
-           "declaration_sha256": ph["single"]["declaration_sha256"], "harness": C.HARNESS42.as_posix(), "sandbox_base": C.SANDBOX_BASE.as_posix(),
+    res = {"name": "DRY-EXERCISE (R43-40) of declaration-r32-v4 with the bound review43 harness (byte copies)", "tag": tag,
+           "declaration_sha256": ph["single"]["declaration_sha256"], "harness": C.HARNESS43.as_posix(), "imported_from": C.HARNESS42.as_posix(),
+           "sandbox_base": C.DRY_BASE.as_posix(), "substitution": "S-BASE (r43p_base.py): the dry base inside the work folder",
            "checks_before": ph["single"]["checks_before"],
@@ -318,3 +321,3 @@
            "cli_version_case": cli, "ai_ledger_snapshots": leds,
-           "ai_ledger_unchanged_483_17_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
+           "ai_ledger_unchanged_484_18_0": all(x == leds[0] for x in leds) and {k: leds[0][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
            "model_requests_total": ph["single"]["model_requests_total"] + ph["split"]["model_requests_total"]
@@ -325,3 +328,4 @@
            "finished_utc": now(),
-           "statement": ("dry exercise only: reader 'none' on the real run set (no application reader touched a cohort document), every request ended at "
+           "statement": ("dry exercise only: reader 'none' on the real run set (no application reader touched a cohort document: the bound harness runs a "
+                         "reader in dry mode on synthetic documents only, so no lane-B fact of a cohort document exists here), every request ended at "
                          "the refusing stub ('dry_refused'), no provider was built, no ledger path, no scope; the loops and the cross-project drill use "
@@ -329,3 +333,3 @@
                          "are not results; reference set independently AI-reviewed (Claude agents), not human-signed")}
-    res["ok"] = all(p["ok"] for p in ph.values()) and cli.get("ok") is True and res["ai_ledger_unchanged_483_17_0"] and res["model_requests_total"] == 0 \
+    res["ok"] = all(p["ok"] for p in ph.values()) and cli.get("ok") is True and res["ai_ledger_unchanged_484_18_0"] and res["model_requests_total"] == 0 \
         and res["live_run_folder_absent"]
```

### `guard/sitecustomize.py`

```diff
--- declaration-r32-v3/scripts/guard/sitecustomize.py
+++ declaration-r32-v4/scripts/guard/sitecustomize.py
@@ -1,24 +1,37 @@
-"""ORCH-10 (R42PORT-IMPL) audit guard, loaded by every Python process of this task through PYTHONPATH (the lanes, the
-ingestion and scoring children inherit it). It REFUSES, by raising PermissionError, and logs to <work>/out/guard/:
+"""R43-40 (declaration-r32-v4) audit guard for tests, dry runs, demonstrations and package builds, loaded by every Python
+process through PYTHONPATH (the lanes, the ingestion and scoring children inherit it). It answers Verification 43 R43V-10:
+the v3 (R42) guard allowed writes to the whole sandbox base (including the live run folder r32-v3 and the owner records),
+the R42 work folder, review42 and declaration-r32-v3. This guard REFUSES, by raising PermissionError, and logs to
+R43_GUARD_LOG (default C:/t/r2x/r42-sandbox/r43p/guard-log):
   * any process whose program or arguments name a `claude` executable (by name, full path, shell or os.system);
-  * every socket connect / name lookup (no network);
+  * every socket connect / name lookup / bind (no network);
+  * DENIED FIRST, whatever the allowed roots say: any write, mkdir, rename, remove, rmdir, chmod, utime, copy target or
+    read-write sqlite3 connection inside
+      - every live run folder <C:/t/r2x/r<NN>-sandbox>/r32-v<N> (and r32-v<N>-<anything>, e.g. the owner records),
+      - the AI ledger folder C:/t/r2x/ledger,
+      - every application tree under C:/t/iso,
+      - the frozen packages review42, review43, declaration-r32, declaration-r32-v2 and declaration-r32-v3;
+  * ANY open (read included) inside an owner-records folder (r32-v<N>-owner-records), unless the process was started
+    with R43_GUARD_OWNER_RECORDS=hash-only (the before/after snapshot hashes that folder as a whole; nothing else may);
   * a write, mkdir, rename, remove, rmdir, chmod or utime outside the allowed roots;
-  * a read-write sqlite3 connection outside the allowed roots (mode=ro URIs are allowed anywhere);
+  * a read-write sqlite3 connection outside the allowed roots (mode=ro URIs are allowed outside the denied set);
   * any open of the merged installation's .env.
-Allowed write roots: the work folder, the dry sandbox base, the two new packages, the session scratchpad, the process'
-own TEMP when it lies under one of those, and os.devnull. R42_GUARD_ALLOW_EXTRA may add ONE extra file (used only by the
-response-ledger append, which writes that one file). Nothing else is changed in the process."""
+Allowed write roots: R43_GUARD_ROOTS (';'-separated) when set -- each must lie strictly inside C:/t/r2x/r42-sandbox (not
+the base itself) or be the v4 package folder; anything else is ignored and recorded -- otherwise the defaults
+C:/t/r2x/r42-sandbox/r43p and PILOT/declaration-r32-v4; plus os.devnull. Nothing else is changed in the process."""
 import os
+import re
 import sys
 
-_ROOTS = [
-    "c:/t/iso/work/r2x/r42",
-    "c:/t/r2x/r42-sandbox",
-    "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot/review42",
-    "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot/declaration-r32-v3",
-    "c:/users/moham/appdata/local/temp/claude/g--dev--2--dev-ep-platform-merged/a76bec7b-2218-48de-b634-4b877ef21099/scratchpad",
-]
-_EXTRA = (os.environ.get("R42_GUARD_ALLOW_EXTRA") or "").replace("\\", "/").lower()
+_SANDBOX = "c:/t/r2x/r42-sandbox"
+_PILOT = "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot"
+_V4 = _PILOT + "/declaration-r32-v4"
+_DEFAULT_ROOTS = [_SANDBOX + "/r43p", _V4]
 _ENV_FILE = "g:/dev (2)/dev/ep-platform-merged/ep-platform/backend/.env"
-_LOG = "C:/t/iso/work/r2x/r42/out/guard"
+_LOG = os.environ.get("R43_GUARD_LOG") or "C:/t/r2x/r42-sandbox/r43p/guard-log"
+_DENY = re.compile(r"^(?:c:/t/r2x/r\d{2}-sandbox/r32-v\d+(?:-[^/]*)?(?:/|$)|c:/t/r2x/ledger(?:/|$)|c:/t/iso(?:/|$)|"
+                   + re.escape(_PILOT) + r"/(?:review42|review43|declaration-r32|declaration-r32-v2|declaration-r32-v3)(?:/|$))")
+_OWNER_RECORDS = re.compile(r"^c:/t/r2x/r\d{2}-sandbox/r32-v\d+-owner-records(?:/|$)")
+_OWNER_HASH_ONLY = os.environ.get("R43_GUARD_OWNER_RECORDS") == "hash-only"
+_IGNORED = []
 
@@ -38,6 +51,23 @@
     try:
-        lp = os.path.realpath(p).replace("\\", "/")      # resolves 8.3 short names where possible
+        lp = os.path.realpath(p).replace("\\", "/")      # resolves 8.3 short names and junctions where possible
     except (OSError, ValueError):
         lp = p
-    return lp.lower()
+    return lp.lower().rstrip("/")
+
+
+def _roots():
+    raw = os.environ.get("R43_GUARD_ROOTS")
+    if not raw:
+        return list(_DEFAULT_ROOTS)
+    out = []
+    for r in raw.split(";"):
+        n = _norm(r.strip()) if r.strip() else ""
+        if n and ((n.startswith(_SANDBOX + "/") and not _DENY.match(n)) or n == _V4):
+            out.append(n)
+        elif n:
+            _IGNORED.append(n)
+    return out
+
+
+_ROOTS = _roots()
 
@@ -48,4 +78,4 @@
         return True
-    if _EXTRA and n == _norm(_EXTRA):
-        return True
+    if _DENY.match(n):
+        return False
     return any(n == r or n.startswith(r + "/") for r in _ROOTS)
@@ -64,3 +94,3 @@
     _record(kind, detail)
-    raise PermissionError(f"R42 guard refused {kind}: {detail}")
+    raise PermissionError(f"R43 guard refused {kind}: {detail}")
 
@@ -92,5 +122,8 @@
             return
-        if _norm(path) == _ENV_FILE:
+        n = _norm(path)
+        if n == _ENV_FILE:
             _refuse("open .env", path)
         writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & _WRITE_FLAGS)
+        if _OWNER_RECORDS.match(n) and (writing or not _OWNER_HASH_ONLY):
+            _refuse("open owner records", path)
         if writing and not _allowed(path):
@@ -112,6 +145,11 @@
             return
+        ro = False
         if s.startswith("file:"):
-            if "mode=ro" in s:
-                return
+            ro = "mode=ro" in s
             s = s[5:].split("?", 1)[0]
+        n = _norm(s)
+        if _OWNER_RECORDS.match(n):
+            _refuse("sqlite3 owner records", s)
+        if ro:
+            return
         if not _allowed(s):
@@ -126,2 +164,4 @@
 
+if _IGNORED:
+    _record("ignored R43_GUARD_ROOTS entries", repr(_IGNORED))
 sys.addaudithook(_hook)
```

### `package_r42.py`

```diff
--- declaration-r32-v3/scripts/package_r42.py
+++ declaration-r32-v4/scripts/package_r42.py
@@ -29,3 +29,3 @@
     ck["ai_ledger"] = {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")} | {
-        "ok": (led["entries"], led["scopes"], led["limit_amendments"]) == (483, 17, 0) and C.SCOPE not in led["scope_names"]}
+        "ok": (led["entries"], led["scopes"], led["limit_amendments"]) == tuple(C.LEDGER_EXPECTED[k] for k in ("entries", "scopes", "limit_amendments")) and C.SCOPE not in led["scope_names"]}   # R43-40 (R43V-04): 484 / 18 / 0
     ck["run_folder_absent"] = not C.RUN_FOLDER.exists()
```

### `preflight_r42.py`

```diff
--- declaration-r32-v3/scripts/preflight_r42.py
+++ declaration-r32-v4/scripts/preflight_r42.py
@@ -1,2 +1,7 @@
-"""ORCH-10 (R42PORT-IMPL): the dry preflight of the frozen v3 declaration against the bound review42 harness (no dispatch, no
+"""R43-40: the same dry preflight for the frozen v4 declaration against the bound review43 harness (byte copies checked by hash,
+C.check_run_copy; preflight_r32.HERE set to the bound folder for the isolation key, C.declared_here; lane roots inside the
+work folder r43p; the ledger expected 484 / 18 / 0; the authorization-file invariant a before/after comparison, since the
+owner's committed v3 RUN and authorization files exist). Self-contained (R43V-09): it imports only r42common,
+build_declaration_r42 and create_scope_r42 of this package and the bound harness.
+ORCH-10 (R42PORT-IMPL): the dry preflight of the frozen v3 declaration against the bound review42 harness (no dispatch, no
 model request, no `claude` invocation, no scope, no token, no authorization file, no RUN file). v2's preflight_r40.py
@@ -53,6 +58,7 @@
 def harness_import():
-    man = json.loads(C.BINDING42.read_text(encoding="utf-8"))
-    bad = [p for p, w in man["files"]["harness_r42_package"].items() if C.sha256_file(p) != w]
+    man = json.loads(C.BINDING43.read_text(encoding="utf-8"))          # R43-40: the review43 harness manifest and group
+    bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
     if bad:
         raise C.PacketMismatch(f"PACKET MISMATCH: harness files differ: {bad[:3]}")
+    C.check_run_copy()
     if str(C.HARNESS42) not in sys.path:
@@ -78,2 +84,4 @@
             "harness_pycache": [p.as_posix() for p in C.HARNESS42.rglob("__pycache__")],
+            "bound_harness_listing_sha256": hashlib.sha256(json.dumps(listing(C.HARNESS43), sort_keys=True).encode()).hexdigest(),   # R43-40
+            "bound_harness_pycache": [p.as_posix() for p in C.HARNESS43.rglob("__pycache__")],
             "package_listing_sha256": hashlib.sha256(json.dumps(listing(C.PACKAGE, skip=("dry-run/", "scope/", "tests/", "evidence/")), sort_keys=True).encode()).hexdigest(),
@@ -191,2 +199,3 @@
     import runner_r32 as RN  # noqa: E402
+    C.declared_here(PF)                                              # R43-40 (Verification 43 P8)
     frozen, fsha = BD.frozen_bytes_checked()
@@ -194,7 +203,8 @@
     run_path = C.PACKAGE / C.RUN_NAME
-    binding_sha = C.sha256_file(C.BINDING42)
+    binding_sha = C.sha256_file(C.BINDING43)
     before = invariants()
-    res = {"name": "PREFLIGHT-RESULTS (ORCH-10 dry preflight of declaration-r32-v3)", "started_utc": started,
-           "declaration": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(), "sha256": fsha}, "harness": C.HARNESS42.as_posix(),
-           "binding_manifest": {"path": C.BINDING42.as_posix(), "sha256": binding_sha}, "before": before, "checks": {}}
+    res = {"name": "PREFLIGHT-RESULTS (R43-40 dry preflight of declaration-r32-v4)", "started_utc": started,
+           "declaration": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(), "sha256": fsha}, "harness": C.HARNESS43.as_posix(),
+           "imported_from": C.HARNESS42.as_posix(), "run_copy": C.check_run_copy(),
+           "binding_manifest": {"path": C.BINDING43.as_posix(), "sha256": binding_sha}, "before": before, "checks": {}}
     ck = res["checks"]
@@ -233,3 +243,3 @@
                                "all_as_expected": all(r["as_expected"] for r in rows), "rows": rows}
-    ck["4_verify_binding"] = {"result": "PASSED", **PF.verify_binding(C.BINDING42, binding_sha)}
+    ck["4_verify_binding"] = {"result": "PASSED", **PF.verify_binding(C.BINDING43, binding_sha)}
     truth = PF.build_truth()
@@ -246,3 +256,3 @@
     for lane in ("B", "C", "R", "P"):
-        root = C.SANDBOX_BASE / f"r42d-env-{lane}"
+        root = C.WORK / f"env-{lane}"                                  # R43-40: lane roots in the work folder
         env = RN.lane_env("live", root, lane, cfg)
@@ -262,3 +272,3 @@
     argv = ["run", "--mode", "live", "--declaration", run_path.as_posix(), "--declaration-sha", run_mem_sha, "--run-set", C.RUN_SET.as_posix(),
-            "--binding", C.BINDING42.as_posix(), "--binding-sha", binding_sha]
+            "--binding", C.BINDING43.as_posix(), "--binding-sha", binding_sha]
     r = subprocess.run([C.PY, "-B", "runner_r32.py", *argv], cwd=str(C.HARNESS42), env=env, capture_output=True, text=True, encoding="utf-8", timeout=900)
@@ -349,7 +359,9 @@
     res["invariants"] = {
-        "ai_ledger_483_17_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
+        "ai_ledger_484_18_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
         "run_folder_never_created": not before["run_folder_exists"] and not after["run_folder_exists"],
-        "harness_unchanged_no_pycache": before["harness_listing_sha256"] == after["harness_listing_sha256"] and not after["harness_pycache"],
+        "harness_unchanged_no_pycache": before["harness_listing_sha256"] == after["harness_listing_sha256"] and not after["harness_pycache"]
+        and before["bound_harness_listing_sha256"] == after["bound_harness_listing_sha256"] and not after["bound_harness_pycache"],
         "package_unchanged_by_the_preflight_outside_its_outputs": before["package_listing_sha256"] == after["package_listing_sha256"],
-        "no_authorization_run_or_token_file": not before["forbidden_files"] and not after["forbidden_files"],
+        "no_authorization_run_or_token_file": before["forbidden_files"] == after["forbidden_files"]          # R43-40: before/after (the v3 record exists)
+        and not any(f.startswith(C.PACKAGE.as_posix() + "/") or f.startswith(C.RUN_FOLDER.as_posix() + "/") for f in after["forbidden_files"]),
         "no_token_in_the_environment": not before["token_env_present"] and not after["token_env_present"],
```

### `r42common.py`

```diff
--- declaration-r32-v3/scripts/r42common.py
+++ declaration-r32-v4/scripts/r42common.py
@@ -24,8 +24,9 @@
 MERGED_EP = EP.as_posix()                                         # "G:/dev (2)/dev/ep-platform-merged/ep-platform"
-WORK = pathlib.Path("C:/t/iso/work/r2x/r42")
+WORK = pathlib.Path("C:/t/r2x/r42-sandbox/r43p")                  # R43-40: the one work folder of this task (r42: C:/t/iso/work/r2x/r42)
 SANDBOX_BASE = pathlib.Path("C:/t/r2x/r42-sandbox")               # this task's dry sandboxes AND the declared live base
-STAMP = "r32-v3"
+STAMP = "r32-v4"                                                   # R43-40: new stamp (r32-v3 exists, executed)
 RUN_FOLDER = SANDBOX_BASE / STAMP                                  # never created by this task
-DECLARATION_DATE = "2026-10-06"                                    # the ORCH-10 issue date (owner's local date, +04)
-SCOPE = f"m2-fresh-validation-r32-v3-{DECLARATION_DATE}"
+DECLARATION_DATE = "2026-10-08"                                    # R43-40: the v4 freeze date (owner's local date, +04)
+SCOPE = f"m2-fresh-validation-r32-v4-{DECLARATION_DATE}"           # R43-40: new scope name (the v3 scope exists)
+DRY_BASE = WORK / "sb"                                             # R43-40: dry / demo run folders (driver-side base redirect, r43p_base.py)
 AI_LEDGER = pathlib.Path("C:/t/r2x/ledger/r2x-ledger.sqlite")
@@ -40,7 +41,7 @@
 
-CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r29/backend")
-BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r12/backend")
-CANDIDATE = ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d")
-BASELINE = ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")
-LEDGER_EXPECTED = {"entries": 483, "scopes": 17, "limit_amendments": 0}
+CANDIDATE_BACKEND = pathlib.Path("C:/t/iso/cand-r30n/backend")   # R43-40: the R43 trees (review43 re-points 1-4)
+BASELINE_BACKEND = pathlib.Path("C:/t/iso/frozen-r13/backend")
+CANDIDATE = ("C:/t/iso/cand-r30n", "436daef215c72fbe2429dcd783e087bf39756ad7")
+BASELINE = ("C:/t/iso/frozen-r13", "7ec3d2cf983b70a604844beda8eb6b1ec6173d34")
+LEDGER_EXPECTED = {"entries": 484, "scopes": 18, "limit_amendments": 0}   # R43-40 (R43V-04): re-pinned to the state at the v4 freeze (v3 scope present)
 
@@ -61,3 +62,3 @@
 REVIEW42 = PILOT / "review42"
-HARNESS42 = REVIEW42 / "scripts" / "harness-r32"
+HARNESS42_PACKAGE = REVIEW42 / "scripts" / "harness-r32"          # R43-40: review42's own harness (record only; v3 ran it)
 WORK_HARNESS = WORK / "harness-r32"
@@ -65,5 +66,25 @@
 BOUNDS42 = REVIEW42 / "PROJECT-REQUEST-BOUNDS.json"
-PACKAGE = PILOT / "declaration-r32-v3"
-DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V3.json"
-RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json"       # produced ONLY by the owner (fill_owner_digest), never here
+# R43-40: the review43 harness (Verification 43 VERIFIED WITH CONDITIONS) is the bound harness of v4. HARNESS42 keeps its
+# name so the carried scripts run unchanged, and now names the folder the code is IMPORTED from: the bound folder, or a
+# byte copy named by R43_HARNESS_RUN (checked against the bound hashes by check_run_copy before any import).
+REVIEW43 = PILOT / "review43"
+HARNESS43 = REVIEW43 / "scripts" / "harness-r32"                  # the bound, declared folder (isolation.allowed_under_forbidden.harness)
+BINDING43 = REVIEW43 / "BINDING-MANIFEST-R43-HARNESS.json"
+BINDING43_SHA = "f35355aa8a8bca16803db3576fda8260a470915fee9c905b035f8d8bd9a374a7"
+HARNESS_GROUP = "harness_r43_package"
+HARNESS42 = pathlib.Path(os.environ.get("R43_HARNESS_RUN") or HARNESS43)
+PACKAGE = PILOT / "declaration-r32-v4"                             # R43-40
+DECLARATION_NAME = "FRESH-VALIDATION-DECLARATION-R32-V4.json"
+RUN_NAME = "FRESH-VALIDATION-DECLARATION-R32-V4.RUN.json"       # produced ONLY by the owner (fill_owner_digest), never here
+# R43-40: the executed v3 declaration (frozen; its RUN and authorization files committed as 7a1bf6f; never edited)
+V3 = PILOT / "declaration-r32-v3"
+V3_NAME = "FRESH-VALIDATION-DECLARATION-R32-V3.json"
+V3_SHA = "9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40"
+V3_MANIFEST_SHA = "a2df60dca2dfba5ebaff8bdc4b73ef76926cbecd7fd58c8916885e7e709a1a24"
+V3_RUN_SHA = "c31cccd4eab844d738b40b07e191e064221ea3dd3a7697c01c2fc998763a2b6a"
+V3_AUTH_SHA = "f2546c91912e4fefc5516158327a54c4c05776286310f61d6bea10f09b84425f"
+V3_SCOPE = "m2-fresh-validation-r32-v3-2026-10-06"
+V3_RUN_FOLDER = SANDBOX_BASE / "r32-v3"
+OWNER_RECORDS = SANDBOX_BASE / "r32-v3-owner-records"
+TASK37_BINDING_SHA = "e1735093c3852f060977b675cafcd0f78696f5e48fee2c7a3bb05d08225d83c1"
 AUTH_NAME = "OWNER-DISPATCH-AUTHORIZATION.json"                 # written ONLY by the owner, never here
@@ -97,4 +118,26 @@
           "MASTER-ROADMAP.md": "f6dba0b2fce767955aed2b7508cfe7480637b02c44f502c3702c7862116e4c86"}
-TASK_FILE = MR / "orchestrator/NEXT-BOUNDED-TASK.md"
-TASK_FILE_SHA = "4ee96b8a42289c3c70f2f5075eb98dbfaeee3b119dae5a604107abd85fc59b89"
+TASK_FILE = MR / "orchestrator/tasks/R43-40-TASK.md"               # R43-40
+TASK_FILE_SHA = "a6e54229993d710f13f5191757ba3714128bd1b738abbe46f27e3b4da5bec023"
+
+
+def check_run_copy() -> dict:
+    """R43-40 (R43V-09): the folder the harness is imported from (HARNESS42) must hold exactly the bound bytes of the
+    review43 harness: every file of the bound group harness_r43_package under scripts/harness-r32 re-hashed at its bound
+    path AND at the run copy. A difference is PACKET MISMATCH."""
+    man = json.loads(BINDING43.read_text(encoding="utf-8"))
+    if sha256_file(BINDING43) != BINDING43_SHA:
+        raise PacketMismatch(f"PACKET MISMATCH: {BINDING43.as_posix()} is not {BINDING43_SHA}")
+    group = {p: w for p, w in man["files"][HARNESS_GROUP].items() if "/scripts/harness-r32/" in p}
+    bad = [p for p, w in group.items() if sha256_file(p) != w]
+    copy_bad = [p for p, w in group.items() if sha256_file(HARNESS42 / pathlib.Path(p).name) != w] if HARNESS42 != HARNESS43 else []
+    if bad or copy_bad:
+        raise PacketMismatch(f"PACKET MISMATCH: bound {bad[:3]} run copy {copy_bad[:3]}")
+    return {"bound_folder": HARNESS43.as_posix(), "imported_from": HARNESS42.as_posix(), "files": len(group), "run_copy": HARNESS42 != HARNESS43}
+
+
+def declared_here(PF) -> None:
+    """R43-40 (Verification 43 P8): when the harness is imported from a byte copy, preflight_r32.HERE is set to the bound
+    folder in THIS process only, so isolation_binding() and validate_declaration compare the declaration with the folder
+    the live runner will run from (PILOT/review43/scripts/harness-r32)."""
+    PF.HERE = HARNESS43
 
```

