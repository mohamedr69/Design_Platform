"""ORCH-06C (R36HARNESS-IMPL): the package checker of review36. Writes PILOT/review36/evidence/PACKAGE-CHECK.json.
Usage: verify_review36_package.py [--skip-tests]
Checks (no model request; read-only except the output file and, unless --skip-tests, fresh test folders in the scratchpad
and the r36 sandbox):
  1  frozen inputs: the review34 manifest (64d5ba0d...) and all 124 files it lists, the evaluator-offline-r32 manifest
     (86dd81d3...) and its 25 files, the fixtures, the matrix and Verification 36 re-hashed equal (PACKET OK)
  2  the binding manifest and every file it binds re-hashed (the runner's own preflight_r32.verify_binding)
  3  harness: the package copy equals the work copy; against review34 exactly ONE module differs (literal_compare_r32.py,
     ec2221c8... -> c23ba577...) plus its test file; the change is re-derived from the review34 bytes by
     apply_h1_fix_r36.transform; the unified diff of the module touches only lines inside norm_revision; the review34
     test file is an exact byte prefix of the r36 test file; every other file is byte-identical to review34
  4  the test-run twin equals the bound copy with only 'C:/t/r2x/r34-sandbox' -> 'C:/t/r2x/r36-sandbox'
  5  the packaged scripts equal the work-folder scripts; the parity-script copy re-derives from the ORCH-06 scripts
  6  tests: packaged junit (whole suite, 16 modules, from the twin; and the 14 sandbox-free modules from the bound copy),
     0 failures / errors, 0 guard refusals; unless --skip-tests both runs are repeated in fresh folders with equal counts
  7  H1-WHATIF-RESULT.json: ok, 53 rows / 106 cases changed (critical -> correct), 0 wrong-value control newly accepted,
     NOT_SCORABLE never read as absent, Verification 36's what-if numbers reproduced
  8  AI ledger read-only: 483 entries / 17 scopes / 0 amendments, scope names hash unchanged
  9  frozen trees: no file modified after 2026-10-03T15:30:00Z, and every tree digest equal to the task-start snapshot
 10  no authorization file (by name and by content) where this task writes; none named so under the pilot folder
 11  candidate / baseline HEADs clean; the response ledger still at its pre-append hash 44b5ae38...
 12  LF line ends (the review31 CRLF copies exempt; pytest-written junit XML whose failure text carries CRLF is listed, not
     a problem), the required documents, the statuses in CHANGE-RECORD.md"""
import datetime
import difflib
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r36")
PKG = PILOT / "review36"
R34 = PILOT / "review34"
EO = PILOT / "evaluator-offline-r32"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
SCRATCH = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r36harness")
SANDBOX = pathlib.Path("C:/t/r2x/r36-sandbox")
RESPONSE = PILOT.parent / "M2-REVIEW-RESPONSE.md"
RESPONSE_BEFORE = "44b5ae386cc3f993547921cf094ebe6d308b4c1aef851bc6e1cf2b0c99bc1b25"
AI_LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
SCOPE_NAMES_SHA = "a037785aba929442f67a179eff144e06c2777f72a42bc4741f6165f952db663e"
FROZEN_SHA = {R34 / "evidence/EVIDENCE-MANIFEST.json": "64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86",
              EO / "evidence/EVIDENCE-MANIFEST.json": "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7",
              EO / "SYNTHETIC-PREDICTIONS.json": "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774",
              EO / "PARITY-MATRIX.json": "73e189f2d0cfe05e55ba58837e991c008eaaf11fb928c300cf0670ead60aaccc",
              R34 / "scripts/harness-r32/literal_compare_r32.py": "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6",
              MR / "reviews/M2-review-36/INDEPENDENT-VERIFICATION.md": "f698c2ffebc44df0487edce762a3f1bd561b2cbbda7b3d844dbd7d6c15173a00"}
OLD_LC, NEW_LC = "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6", "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"
OLD_T, NEW_T = "1d91cb5443ac5258b3fc60268b80a2815517badb5ebf5c77a3d0bf6b62831e4e", "66e0ddcf92ae4aaf350ca1143ad4f22f62ab777e12700c978652b276fdbb34c6"
CANDIDATE_HEAD, BASELINE_HEAD = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
SCRIPTS = ["audit_r36.py", "copy_harness_r36.py", "apply_h1_fix_r36.py", "h1_test_addition_r36.txt", "make_suite_twin_r36.py", "run_tests_r36.py",
           "snapshot_r36.py", "make_parity_copy_r36.py", "judge_all_rows_r36.py", "h1_whatif_r36.py", "make_binding_r36.py",
           "verify_review36_package.py", "package_r36.py", "append_response_r36.py", "pytest-plugins/r36_write_guard.py",
           "assemble_review36.py", "make_change_record_r36.py"]
REQUIRED = ["CHANGE-RECORD.md", "BINDING-MANIFEST-R36.json", "COMMANDS.md", "COMMANDS-AND-AUDIT-LOG.md", "H1-WHATIF-RESULT.json",
            "evidence/COPY-RECORD.json", "evidence/TWIN-RECORD.json", "evidence/PARITY-COPY-RECORD.json", "evidence/SNAPSHOT-BEFORE.json",
            "evidence/TESTS-TWIN.json", "evidence/TESTS-BOUND.json", "tests/new-tests-on-review34-module/test_literal_compare_r32.xml"]
CRLF_EXEMPT = {"capture_store.py", "state_check.py", "test_capture_store.py", "test_state_check.py"}
AUTH_KEYS = {"declaration_sha256", "owner_token_sha256", "nonce", "authorized_by"}
REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def text(obj):
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def junit(folder):
    out = {}
    for xf in sorted(pathlib.Path(folder).glob("*.xml")):
        root = ET.parse(xf).getroot()
        suites = [root] if root.tag == "testsuite" else list(root)
        out[xf.name] = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    guard = {}
    for g in sorted((pathlib.Path(folder) / "guard").glob("*.json")):
        d = json.loads(g.read_text(encoding="utf-8"))
        guard[g.stem] = d["refused_count"] + len(d["network_refused"])
    return {"files": out, "modules": len(out), "tests": sum(v["tests"] for v in out.values()),
            "failures": sum(v["failures"] for v in out.values()), "errors": sum(v["errors"] for v in out.values()),
            "guard_reports": len(guard), "guard_refusals": sum(guard.values())}


def main(skip_tests=False):
    c, problems = {}, []
    sys.path.insert(0, str(WORK))
    import apply_h1_fix_r36 as AP  # noqa: E402
    import make_parity_copy_r36 as MP  # noqa: E402
    import make_suite_twin_r36 as TW  # noqa: E402
    import snapshot_r36 as SN  # noqa: E402
    # 1. frozen inputs
    bad = [str(p) for p, want in FROZEN_SHA.items() if sha(p) != want]
    listed = {}
    for pkg in (R34, EO):
        m = json.loads((pkg / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
        diff = [rel for rel, info in m.items() if sha(pkg / rel) != info["sha256"] or (pkg / rel).stat().st_size != info["bytes"]]
        actual = {p.relative_to(pkg).as_posix() for p in pkg.rglob("*") if p.is_file()}
        listed[pkg.name] = {"listed": len(m), "mismatches": diff, "unlisted": sorted(actual - set(m) - {"evidence/EVIDENCE-MANIFEST.json"})}
        bad += [f"{pkg.name}/{d}" for d in diff] + [f"{pkg.name}/unlisted/{u}" for u in listed[pkg.name]["unlisted"]]
    c["frozen_inputs"] = {"hashes": {str(p): w for p, w in FROZEN_SHA.items()}, "manifests": listed, "mismatches": bad,
                          "result": "PACKET OK" if not bad else "PACKET MISMATCH"}
    if bad or listed["review34"]["listed"] != 124 or listed["evaluator-offline-r32"]["listed"] != 25:
        problems.append("frozen inputs")
    # 2. binding manifest, re-hashed by the runner's own verify_binding
    bm = PKG / "BINDING-MANIFEST-R36.json"
    sys.path.insert(0, str(WORK / "harness-r32"))
    import preflight_r32 as PF  # noqa: E402
    assert pathlib.Path(PF.__file__).resolve().parent == (WORK / "harness-r32").resolve()
    try:
        vb = PF.verify_binding(bm, sha(bm))
        vb_ok = True
    except Exception as exc:  # noqa: BLE001
        vb, vb_ok = {"error": str(exc)}, False
    man = json.loads(bm.read_text(encoding="utf-8"))
    c["binding"] = {"sha256": sha(bm), "verify_binding": vb, "ok": vb_ok, "groups": {g: len(v) for g, v in man["files"].items()},
                    "changed_modules": man["changed_modules"], "unchanged_modules": len(man["unchanged_modules"])}
    if not vb_ok or len(man["unchanged_modules"]) != 38 or man["changed_modules"]["literal_compare_r32.py"]["r36_sha256"] != NEW_LC:
        problems.append("binding manifest")
    # 3. harness
    work = {p.name: sha(p) for p in (WORK / "harness-r32").iterdir() if p.is_file()}
    pkgh = {p.name: sha(p) for p in (PKG / "scripts/harness-r32").iterdir() if p.is_file()}
    base = {p.name: sha(p) for p in (R34 / "scripts/harness-r32").iterdir() if p.is_file()}
    differ = sorted(n for n in base if work.get(n) != base[n])
    modules_differ = [n for n in differ if not n.startswith("test_")]
    module, test = AP.transform((R34 / "scripts/harness-r32/literal_compare_r32.py").read_bytes(), (R34 / "scripts/harness-r32/test_literal_compare_r32.py").read_bytes())
    old_lines = (R34 / "scripts/harness-r32/literal_compare_r32.py").read_text(encoding="utf-8").splitlines()
    new_lines = (WORK / "harness-r32/literal_compare_r32.py").read_text(encoding="utf-8").splitlines()
    fn_start = old_lines.index("def norm_revision(value) -> str:") + 1
    fn_end = fn_start + next(i for i, l in enumerate(old_lines[fn_start:], 1) if l and not l.startswith(" ")) - 1   # last line of the function
    sm = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    touched = [(tag, i1 + 1, i2) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    inside = all(fn_start <= a and b <= fn_end for _, a, b in touched)
    old_t, new_t = (R34 / "scripts/harness-r32/test_literal_compare_r32.py").read_bytes(), (WORK / "harness-r32/test_literal_compare_r32.py").read_bytes()
    c["harness"] = {"files": len(work), "package_equals_work": pkgh == work, "same_file_list_as_review34": set(work) == set(base),
                    "files_differing_from_review34": differ, "modules_differing_from_review34": modules_differ,
                    "literal_compare_r32": {"review34": base.get("literal_compare_r32.py"), "r36": work.get("literal_compare_r32.py")},
                    "test_literal_compare_r32": {"review34": base.get("test_literal_compare_r32.py"), "r36": work.get("test_literal_compare_r32.py"),
                                                 "review34_file_is_a_byte_prefix": new_t.startswith(old_t)},
                    "rederived_from_review34": hashlib.sha256(module).hexdigest() == work.get("literal_compare_r32.py")
                    and hashlib.sha256(test).hexdigest() == work.get("test_literal_compare_r32.py"),
                    "norm_revision_lines_review34": [fn_start, fn_end], "diff_hunks_review34_lines": touched, "diff_only_inside_norm_revision": inside,
                    "unchanged_files": len([n for n in base if work.get(n) == base[n]])}
    h = c["harness"]
    if not (h["package_equals_work"] and h["same_file_list_as_review34"] and differ == ["literal_compare_r32.py", "test_literal_compare_r32.py"]
            and modules_differ == ["literal_compare_r32.py"] and h["literal_compare_r32"] == {"review34": OLD_LC, "r36": NEW_LC}
            and work["test_literal_compare_r32.py"] == NEW_T and base["test_literal_compare_r32.py"] == OLD_T
            and h["test_literal_compare_r32"]["review34_file_is_a_byte_prefix"] and h["rederived_from_review34"] and inside and h["unchanged_files"] == 38):
        problems.append("harness")
    # 4. twin
    twin = WORK / "harness-r32-suite-twin"
    tw_bad = [n for n in work if TW.twin_bytes(n, (WORK / "harness-r32" / n).read_bytes()) != (twin / n).read_bytes()]
    tw_files = sorted(p.name for p in twin.iterdir() if p.is_file())
    subst = {n: (WORK / "harness-r32" / n).read_bytes().count(TW.SUBST_FROM) for n in work}
    c["twin"] = {"folder": twin.as_posix(), "files": len(tw_files), "same_file_list": tw_files == sorted(work), "mismatches": tw_bad,
                 "substitution": [TW.SUBST_FROM.decode(), TW.SUBST_TO.decode()], "files_with_substitutions": {n: k for n, k in sorted(subst.items()) if k},
                 "literal_compare_files_identical_to_bound": all((twin / n).read_bytes() == (WORK / "harness-r32" / n).read_bytes()
                                                                 for n in ("literal_compare_r32.py", "test_literal_compare_r32.py", "lane_judge_r32.py"))}
    if tw_bad or not c["twin"]["same_file_list"] or not c["twin"]["literal_compare_files_identical_to_bound"]:
        problems.append("twin")
    # 5. scripts
    sc = {s: (PKG / "scripts" / s).exists() and sha(PKG / "scripts" / s) == sha(WORK / s) for s in SCRIPTS}
    par = {}
    for name, subs in MP.SUBST.items():
        t = (EO / "scripts" / name).read_text(encoding="utf-8")
        for old, new, n in subs:
            t = t.replace(old, new)
        par[name] = hashlib.sha256(t.encode("utf-8")).hexdigest() == sha(WORK / "parity/scripts" / name) == sha(PKG / "scripts/parity-r36" / name)
    c["scripts"] = {"package_scripts_equal_work": sc, "parity_copy_rederived_and_packaged": par}
    if not all(sc.values()) or not all(par.values()):
        problems.append("scripts")
    # 6. tests
    jt, jb = junit(PKG / "tests"), junit(PKG / "tests" / "bound-copy")
    c["junit_packaged"] = {"whole_suite_twin": jt, "bound_copy_sandbox_free_modules": jb}
    if (jt["modules"], jt["tests"], jt["failures"], jt["errors"], jt["guard_refusals"], jt["guard_reports"]) != (16, 280, 0, 0, 0, 16) or \
            (jb["modules"], jb["tests"], jb["failures"], jb["errors"], jb["guard_refusals"], jb["guard_reports"]) != (14, 247, 0, 0, 0, 14):
        problems.append("packaged junit")
    if not skip_tests:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S")
        rr = {}
        for mode in ("twin", "bound"):
            r = subprocess.run([PY, str(WORK / "run_tests_r36.py"), mode, str(SCRATCH / f"check-{stamp}" / mode / "junit"), str(SCRATCH / f"check-{stamp}" / mode / "t")],
                               capture_output=True, text=True)
            s = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"all_passed": False, "error": r.stderr[-800:]}
            want = jt if mode == "twin" else jb
            rr[mode] = {"all_passed": s.get("all_passed"), "total": s.get("total"), "guard_refusals": s.get("guard_refusals"),
                        "junit": str(SCRATCH / f"check-{stamp}" / mode / "junit"),
                        "same_counts_as_packaged": {m + ".xml": v["tests"] for m, v in (s.get("modules") or {}).items()} == {k: v["tests"] for k, v in want["files"].items()}}
            if not (rr[mode]["all_passed"] and rr[mode]["same_counts_as_packaged"] and rr[mode]["guard_refusals"] == 0):
                problems.append(f"tests re-run {mode}")
        c["tests_rerun"] = rr
    # 7. what-if
    w = json.loads((PKG / "H1-WHATIF-RESULT.json").read_text(encoding="utf-8"))
    rl, cl = w["row_level"], w["case_level"]
    c["h1_whatif"] = {"sha256": sha(PKG / "H1-WHATIF-RESULT.json"), "ok": w["ok"], "checks": w["checks"],
                      "rows_judged": {s: rl[s]["rows_judged"] for s in rl}, "rows_changed": {s: rl[s]["changed"] for s in rl},
                      "cases_changed": cl["changed_cases"], "changed_rows": len(cl["changed_rows"]), "changed_rows_in_run_set": len(cl["changed_rows_in_run_set"]),
                      "wrong_value_controls": cl["wrong_value_controls"], "not_scorable": cl["not_scorable"],
                      "verification36_reproduced": {k: v["equal"] for k, v in w["verification36_comparison"].items()},
                      "parity_run_guard": w["inputs"]["parity_run_r36"]["guard"],
                      "parity_run_file_equal": sha(w["inputs"]["parity_run_r36"]["path"]) == w["inputs"]["parity_run_r36"]["sha256"]}
    hw = c["h1_whatif"]
    if not (w["ok"] and all(w["checks"].values()) and hw["rows_changed"] == {"accepted": 53, "validated": 53} and hw["cases_changed"] == 106
            and hw["changed_rows"] == 53 and hw["changed_rows_in_run_set"] == 23 and cl["wrong_value_controls"]["verdict_changed"] == 0
            and cl["not_scorable"]["harness_read_as_absent_after"] == 0 and all(hw["verification36_reproduced"].values()) and hw["parity_run_file_equal"]
            and not hw["parity_run_guard"]["violations"] and not hw["parity_run_guard"]["refused_writes"] and hw["parity_run_guard"]["provider_constructed"] == 0
            and hw["parity_run_guard"]["network_or_process_attempts"] == 0 and not hw["parity_run_guard"]["sdk_modules_imported"]
            and not hw["parity_run_guard"]["database_file_created"]):
        problems.append("h1 what-if")
    # 8. ledger
    con = sqlite3.connect(f"file:{AI_LEDGER}?mode=ro", uri=True)
    c["ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                   "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                   "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest(),
                   "opened": "file:...?mode=ro, uri=True"}
    con.close()
    if (c["ledger"]["entries"], c["ledger"]["scopes"], c["ledger"]["limit_amendments"], c["ledger"]["scope_names_sha256"]) != (483, 17, 0, SCOPE_NAMES_SHA):
        problems.append("ledger")
    # 9. frozen trees
    before = json.loads((PKG / "evidence/SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    now = {k: SN.tree(v) for k, v in SN.TREES.items()}
    changed = sorted(k for k in now if now[k]["digest"] != before["trees"][k]["digest"])
    after_cut = {k: v["modified_after_cutoff"] for k, v in now.items() if v["modified_after_cutoff"]}
    led_main = {"sha256": sha(AI_LEDGER), "before": before["files"]["ai_ledger_main_file"]["sha256"]}
    c["frozen_trees"] = {"cutoff_utc": SN.CUTOFF_UTC, "roots": {k: v["root"] for k, v in now.items()}, "files": {k: v["files"] for k, v in now.items()},
                         "modified_after_cutoff": after_cut, "digest_changed_since_task_start": changed,
                         "ai_ledger_main_file": led_main | {"unchanged": led_main["sha256"] == led_main["before"]},
                         "note": ".git folders excluded; the ledger's -shm side file is touched by read-only readers and is not counted"}
    if changed or after_cut or led_main["sha256"] != led_main["before"]:
        problems.append("frozen trees")
    # 10. authorization files
    named = sorted(str(p) for r in (PILOT, WORK, SANDBOX, SCRATCH) if r.exists() for p in r.rglob("*DISPATCH-AUTHORIZATION*"))
    like = []
    for r in (PKG, WORK, SANDBOX, SCRATCH):
        for p in (r.rglob("*.json") if r.exists() else []):
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                obj = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if isinstance(obj, dict) and AUTH_KEYS <= set(obj):
                like.append(str(p))
    c["authorization_files"] = {"named_like_a_dispatch_authorization": named, "json_objects_with_authorization_keys": like,
                                "searched_by_name": [str(PILOT), str(WORK), str(SANDBOX), str(SCRATCH)], "searched_by_content": [str(PKG), str(WORK), str(SANDBOX), str(SCRATCH)]}
    if named or like:
        problems.append("an authorization file exists")
    # 11. heads, response ledger
    heads = {}
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    for repo, want in (("C:/t/iso/cand-r29", CANDIDATE_HEAD), ("C:/t/iso/frozen-r12", BASELINE_HEAD)):
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
        heads[repo] = {"head": head, "clean": not dirty, "expected": want}
        if head != want or dirty:
            problems.append(f"head {repo}")
    c["heads"] = heads
    c["response_ledger"] = {"sha256": sha(RESPONSE), "expected_before_append": RESPONSE_BEFORE, "unchanged": sha(RESPONSE) == RESPONSE_BEFORE}
    if not c["response_ledger"]["unchanged"]:
        problems.append("response ledger changed before the append")
    # 12. format, required documents, statuses
    # pytest's own junit XML is evidence written by pytest, never edited: a FAILING test's traceback text carries the platform
    # line end (tests/new-tests-on-review34-module/); it is listed, not counted as a problem
    crlf_all = [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".py", ".xml", ".txt")
                and b"\r\n" in p.read_bytes() and p.name not in CRLF_EXEMPT]
    pytest_junit = [r for r in crlf_all if r.startswith("tests/") and r.endswith(".xml")]
    crlf = [r for r in crlf_all if r not in pytest_junit]
    missing = [r for r in REQUIRED if not (PKG / r).exists()]
    rep = (PKG / "CHANGE-RECORD.md").read_text(encoding="utf-8") if (PKG / "CHANGE-RECORD.md").exists() else ""
    statuses = {s: s in rep for s in ("CHANGES STILL REQUIRED", "M3:** not started", "pending ORCH-06CV", REFERENCE_SET_STATEMENT, "identity 57, revision 38, decision 38",
                                       "```diff", NEW_LC, OLD_LC)}
    c["format"] = {"crlf_files": crlf, "pytest_junit_with_crlf_in_failure_text": pytest_junit, "missing_required": missing,
                   "change_record_statements": statuses,
                   "authorization_file_in_package": any("AUTHORIZATION" in p.name.upper() for p in PKG.rglob("*") if p.is_file())}
    if crlf or missing or not all(statuses.values()) or c["format"]["authorization_file_in_package"]:
        problems.append("format / required files / statements")
    out = {"package": "review36 (ORCH-06C, R36HARNESS-IMPL)", "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "checks": c, "problems": problems, "ok": not problems, "skip_tests": skip_tests, "model_requests": 0,
           "reference_set_statement": REFERENCE_SET_STATEMENT}
    p = PKG / "evidence" / "PACKAGE-CHECK.json"
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text(out))
    print(json.dumps({"ok": out["ok"], "problems": problems, "sha256": sha(p)}, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main("--skip-tests" in sys.argv))
