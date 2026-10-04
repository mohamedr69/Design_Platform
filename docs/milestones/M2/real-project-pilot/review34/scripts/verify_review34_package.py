"""ORCH-05C: the package checker of review34. Writes <package>/evidence/PACKAGE-CHECK.json. No model request.
Usage: verify_review34_package.py [--skip-tests]
Checks: every frozen input and manifest re-hashed (PACKET OK); the binding manifest and every file it binds; the package's
harness and script copies equal the bound work-folder files; harness-r33-base equals review33's harness; every module carried
unchanged equals its review33 hash and the review31 copies equal review31; the carried files equal review33 and are
re-derived byte for byte (adapter, converter, selector); every test module re-run (all pass) and the packaged junit report
0 failures / errors; the AI ledger read-only 483 / 17 / 0; no file under the frozen trees modified after
2026-10-03T12:10:00Z (os.stat; .git excluded); no authorization file anywhere (by name under the pilot folder, the work
folders, the r34 sandbox and the scratchpad; by content under every folder this task writes to); the guard's refusals
(no declaration, made-up hash, the review34 pinned path absent, GuardedProvider never built, runner --auth-path rejected);
candidate / baseline HEADs clean; the response ledger still at its pre-append hash; the dry-run facts; Review 34 section 9
carried verbatim into CORRECTION-REPORT.md; the rule version in the documents; LF; the required documents."""
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

R34 = pathlib.Path("C:/t/iso/work/r2x/r34")
sys.path.insert(0, str(R34 / "harness-r32"))
import concentration_r32 as K  # noqa: E402
import converter_r32 as CV  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import labels_adapter_r32 as A  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import run_set_selector_r32 as RS  # noqa: E402

PKG = I.PILOT / "review34"
R33PKG = I.PILOT / "review33"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
RESPONSE = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md")
RESPONSE_BEFORE = "500d55f559f157a8ebbe695157d6c6cd3b83dac5c31e58820f871a4615d690ac"
BINDING_SHA = "3d0f8bfe37d55a4c0490e054c0d710f4bb1d2ac839dffd08daaafca19063ea27"
SCRATCH = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r34harness")
CUTOFF = datetime.datetime(2026, 10, 3, 12, 10, 0, tzinfo=datetime.timezone.utc)
FROZEN = [I.PILOT / "review31", R33PKG, I.PILOT / "fresh-cohort-r32", I.PILOT / "fresh-cohort-r32-reviewed", I.PILOT / "fresh-cohort-r32-reviewed-2",
          I.MR / "reviews", I.MR / "AI-ACCURACY-POLICY.md", I.MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", pathlib.Path("C:/t/r2x/r32-stage"),
          pathlib.Path("C:/t/iso/cand-r29"), pathlib.Path("C:/t/iso/frozen-r12"), pathlib.Path("C:/t/iso/work/r2x/r32"), pathlib.Path("C:/t/iso/work/r2x/r32b"),
          pathlib.Path("C:/t/iso/work/r2x/r32c"), pathlib.Path("C:/t/iso/work/r2x/r33"), pathlib.Path("C:/t/r2x/r33-sandbox"), pathlib.Path(I.AI_LEDGER)]
REQUIRED = ["CORRECTION-REPORT.md", "SCORER-CHANGES.md", "CONCENTRATION-RULE-R32.md", "LIVE-RUN-CONTRACT.md", "DRY-RUN-REPORT.md", "COMMANDS.md",
            "COMMANDS-AND-AUDIT-LOG.md", "BINDING-MANIFEST-R34.json", "ADAPTER-CONTRACT.md", "RUN-SET-RULE.md", "RUN-SET-PROPOSAL.json",
            "LABELS-R32-EVAL-INPUT.json", "CONVERTER-RECONCILIATION.json", "dry-run/DRY-RUN-REPORT.json", "dry-run/TRUTH-R32.json",
            "dry-run/INGEST-72.json", "dry-run/SCORER-SCENARIOS.json", "dry-run/GUARD-CHECK.json", "dry-run/runner/DRILL.json",
            "dry-run/runner/RUN-STATE.json", "dry-run/runner/inv-1/RUN-REPORT.json", "dry-run/runner/inv-2/RUN-REPORT.json",
            "dry-run/runner/inv-2/SCORE-BCR-R32.json"]
CRLF_EXEMPT = {"capture_store.py", "state_check.py", "stop_rules.py", "test_capture_store.py", "test_state_check.py", "test_stop_rules.py"}
REVIEW31_COPIES = ("capture_store.py", "state_check.py", "stop_rules.py", "test_capture_store.py", "test_state_check.py", "test_stop_rules.py")
AUTH_KEYS = {"declaration_sha256", "owner_token_sha256", "nonce", "authorized_by"}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def text(obj):
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def authorization_search():
    named = sorted(str(p) for r in (I.PILOT, pathlib.Path("C:/t/iso/work/r2x"), PF.SANDBOX_BASE, SCRATCH) if r.exists()
                   for p in r.rglob("*DISPATCH-AUTHORIZATION*"))
    like = []
    for r in (PKG, R34, PF.SANDBOX_BASE, SCRATCH):
        for p in (r.rglob("*.json") if r.exists() else []):
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                obj = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if isinstance(obj, dict) and AUTH_KEYS <= set(obj):
                like.append(str(p))
    return {"named_like_a_dispatch_authorization": named, "json_objects_with_authorization_keys": like}


def main(skip_tests=False):
    c, problems = {}, []
    # 1. frozen inputs and manifests
    pre = subprocess.run([PY, str(R34 / "preflight_inputs.py")], capture_output=True, text=True)
    c["preflight_inputs"] = pre.stdout.strip().splitlines()[-1] if pre.stdout.strip() else pre.stderr[-500:]
    if c["preflight_inputs"] != "PACKET OK":
        problems.append("preflight inputs: " + c["preflight_inputs"])
    # 2. binding manifest
    bm = PKG / "BINDING-MANIFEST-R34.json"
    man = json.loads(bm.read_text(encoding="utf-8"))
    bad = [p for files in man["files"].values() for p, want in files.items() if not pathlib.Path(p).exists() or sha(p) != want]
    dry = json.loads((PKG / "dry-run" / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))
    c["binding"] = {"sha256": sha(bm), "expected": BINDING_SHA, "files": sum(len(v) for v in man["files"].values()), "mismatches": bad,
                    "equals_the_dry_run_binding": sha(bm) == dry["runner_invocation_2"]["binding"]["sha256"],
                    "concentration_rule_version": man["concentration_rule_version"]}
    if bad or sha(bm) != BINDING_SHA or not c["binding"]["equals_the_dry_run_binding"] or man["concentration_rule_version"] != K.RULE_VERSION:
        problems.append("binding manifest")
    # 3. copies
    work = {pathlib.Path(p).name: h for p, h in man["files"]["harness_r32"].items()}
    pkg = {p.name: sha(p) for p in (PKG / "scripts" / "harness-r32").glob("*.py")}
    base = {pathlib.Path(p).name: h for p, h in man["files"]["harness_r33_base"].items()}
    r33 = {p.name: sha(p) for p in (R33PKG / "scripts" / "harness-r32").glob("*.py")}
    r31 = {p.name: sha(p) for p in (I.PILOT / "review31" / "scripts" / "harness").glob("*.py")}
    carried_mod = {n: {"sha256": work.get(n), "review33": r33.get(n), "unchanged": work.get(n) == r33.get(n) == v["sha256"]}
                   for n, v in man["unchanged_modules"].items()}
    c["copies"] = {"package_harness_equals_bound_work_copy": pkg == work, "harness_r33_base_equals_review33": base == r33,
                   "unchanged_modules_equal_review33": all(v["unchanged"] for v in carried_mod.values()),
                   "review31_copies_equal_review31": {n: work.get(n) == r31.get(n) for n in REVIEW31_COPIES},
                   "package_scripts_equal_work": {p.name: sha(p) == sha(R34 / p.name) for p in (PKG / "scripts").glob("*.py")},
                   "unchanged_modules": carried_mod,
                   "changed_modules": {n: {"review33": v["review33_sha256"], "review34": v["review34_sha256"], "answers": v["answers"]}
                                       for n, v in man["changed_modules"].items()}}
    if not (pkg == work and base == r33 and c["copies"]["unchanged_modules_equal_review33"] and all(c["copies"]["review31_copies_equal_review31"].values())
            and all(c["copies"]["package_scripts_equal_work"].values()) and len(c["copies"]["package_scripts_equal_work"]) >= 8):
        problems.append("copies")
    # 4. carried files and their re-derivation
    carried = {rel: {"sha256": sha(PKG / rel), "review33": sha(R33PKG / rel)} for rel in man["carried_files"]}
    x = I.load_all()
    truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    prop = json.loads((PKG / "RUN-SET-PROPOSAL.json").read_text(encoding="utf-8"))
    c["carried"] = {"files": carried, "all_equal_review33": all(v["sha256"] == v["review33"] for v in carried.values()),
                    "truth_rederived": hashlib.sha256(text(truth).encode()).hexdigest() == sha(PKG / "dry-run" / "TRUTH-R32.json") == "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064",
                    "eval_input_rederived": hashlib.sha256(text(CV.convert(truth)).encode()).hexdigest() == sha(PKG / "LABELS-R32-EVAL-INPUT.json"),
                    "run_set_rederived": hashlib.sha256(text(RS.build_proposal(truth, inputs=prop["inputs"])).encode()).hexdigest() == sha(PKG / "RUN-SET-PROPOSAL.json") == "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8",
                    "population": {f: len(v) for f, v in A.population(truth).items()}}
    if not (c["carried"]["all_equal_review33"] and c["carried"]["truth_rederived"] and c["carried"]["eval_input_rederived"] and c["carried"]["run_set_rederived"]
            and c["carried"]["population"] == {"identity": 57, "revision": 38, "decision": 38}):
        problems.append("carried files")
    # 5. tests
    junit = {}
    for xf in sorted((PKG / "tests").glob("*.xml")):
        root = ET.parse(xf).getroot()
        suites = [root] if root.tag == "testsuite" else list(root)
        junit[xf.name] = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    c["junit_packaged"] = {"files": junit, "tests": sum(v["tests"] for v in junit.values()),
                           "failures": sum(v["failures"] for v in junit.values()), "errors": sum(v["errors"] for v in junit.values())}
    if c["junit_packaged"]["failures"] or c["junit_packaged"]["errors"] or len(junit) != 16:
        problems.append("packaged junit")
    if not skip_tests:
        scratch = SCRATCH / ("v-" + datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S"))
        r = subprocess.run([PY, str(R34 / "run_tests_r34.py"), str(scratch / "junit"), str(scratch / "t")], capture_output=True, text=True)
        rerun = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"all_passed": False, "error": r.stderr[-1000:]}
        c["tests_rerun"] = {"all_passed": rerun.get("all_passed"), "total": rerun.get("total"),
                            "same_counts_as_packaged": {m + ".xml": v["tests"] for m, v in (rerun.get("modules") or {}).items()} == {k: v["tests"] for k, v in junit.items()}}
        if not rerun.get("all_passed") or not c["tests_rerun"]["same_counts_as_packaged"]:
            problems.append("tests re-run")
    # 6. ledger
    con = sqlite3.connect(f"file:{I.AI_LEDGER}?mode=ro", uri=True)
    c["ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                   "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                   "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest()}
    con.close()
    if (c["ledger"]["entries"], c["ledger"]["scopes"], c["ledger"]["limit_amendments"]) != (483, 17, 0) or \
            c["ledger"]["scope_names_sha256"] != "a037785aba929442f67a179eff144e06c2777f72a42bc4741f6165f952db663e":
        problems.append("ledger")
    # 7. frozen trees
    newer, cut = [], CUTOFF.timestamp()
    for root in FROZEN:
        if root.is_file():
            if os.stat(root).st_mtime > cut:
                newer.append(str(root))
            continue
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d != ".git"]
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    if os.stat(p).st_mtime > cut:
                        newer.append(p)
                except OSError:
                    pass
    c["frozen_trees"] = {"cutoff_utc": CUTOFF.isoformat(), "roots": [str(r) for r in FROZEN], "modified_after_cutoff": newer,
                         "note": "the ledger is checked as its main file; SQLite's -shm side file is touched by read-only readers; .git folders are excluded"}
    if newer:
        problems.append(f"{len(newer)} frozen file(s) modified after the cutoff")
    # 8. authorization files
    c["authorization_files"] = authorization_search()
    if c["authorization_files"]["named_like_a_dispatch_authorization"] or c["authorization_files"]["json_objects_with_authorization_keys"]:
        problems.append("an authorization file exists")
    # 9. the guard

    class Resp:
        def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
            self.error = error

    def must_not_build():
        raise AssertionError("built")

    g = DG.GuardedProvider(must_not_build, PKG / "DECLARATION.json", "0" * 64, Resp, run_folder=PF.SANDBOX_BASE / "no-run", invocation=1)
    cli = subprocess.run([PY, str(R34 / "harness-r32" / "runner_r32.py"), "run", "--mode", "live", "--run-set", str(PKG / "RUN-SET-PROPOSAL.json"),
                          "--binding", str(bm), "--binding-sha", BINDING_SHA, "--auth-path", str(PKG / "x.json")], capture_output=True, text=True,
                         env={"PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": "C:/Windows", "PATH": "C:/Windows/system32"})
    c["guard"] = {"pinned_path_for_review34": DG.pinned_path(PKG / "DECLARATION.json").as_posix(), "exists": DG.pinned_path(PKG / "DECLARATION.json").exists(),
                  "check_none": DG.check(None, None), "check_fake_hash": DG.check(PKG / "DECLARATION.json", "0" * 64),
                  "guarded_provider_response": g.complete(object()).error, "guarded_provider_built": g.inner is not None,
                  "runner_auth_path": {"returncode": cli.returncode, "rejected": "unrecognized arguments: --auth-path" in cli.stderr}}
    gd = c["guard"]
    if gd["exists"] or gd["check_none"]["authorized"] or gd["check_fake_hash"]["authorized"] or gd["guarded_provider_response"] != "dispatch_refused" \
            or gd["guarded_provider_built"] or gd["runner_auth_path"] != {"returncode": 2, "rejected": True}:
        problems.append("guard")
    # 10. heads
    heads = {}
    for repo, want in (("C:/t/iso/cand-r29", I.CANDIDATE_HEAD), ("C:/t/iso/frozen-r12", I.BASELINE_HEAD)):
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        heads[repo] = {"head": head, "clean": not dirty, "expected": want}
        if head != want or dirty:
            problems.append(f"head {repo}")
    c["heads"] = heads
    # 11. response ledger (before the single append)
    c["response_ledger"] = {"sha256": sha(RESPONSE), "expected_before_append": RESPONSE_BEFORE, "unchanged": sha(RESPONSE) == RESPONSE_BEFORE}
    if not c["response_ledger"]["unchanged"]:
        problems.append("response ledger changed before the append")
    # 12. dry-run facts
    ri = dry["runner_invocation_2"]
    c["dry_run"] = {"model_requests": dry["model_requests"], "provider_calls": dry["provider_calls"], "ledger_unchanged": dry["ledger_unchanged"],
                    "ledger_before": dry["ledger_before"], "ledger_after": dry["ledger_after"], "drill_passes": dry["drill"]["passes"],
                    "drill_checks": dry["drill"]["checks"], "guard_ok": dry["guard"]["ok"], "ingest_72_ok": dry["ingest_72"]["ok"],
                    "readers": {k: v.get("reader") for k, v in ri["lanes"].items()}, "live_attempts_blocked": {k: v.get("live_provider_attempts_blocked") for k, v in ri["lanes"].items()},
                    "state_checks": [ri["state_check_C"]["ok"], ri["state_check_R"]["ok"], dry["ingest_72"]["state_check"]["ok"]],
                    "authorization_files_found": dry["authorization_files_found"], "scenario_outcomes": {k: v["candidate"] for k, v in dry["scenario_outcomes"].items()}}
    d = c["dry_run"]
    if d["model_requests"] or d["provider_calls"] or not d["ledger_unchanged"] or not d["drill_passes"] or not d["guard_ok"] or not d["ingest_72_ok"] \
            or set(d["readers"].values()) != {"none"} or any(d["live_attempts_blocked"].values()) or not all(d["state_checks"]) or d["authorization_files_found"] \
            or d["scenario_outcomes"]["S3b decision gain 3 inside EP-27331"] != "NOT ELIGIBLE" \
            or d["scenario_outcomes"]["S5 identity gain 8 and decision recovery below 0.90"] != "NOT ELIGIBLE":
        problems.append("dry-run facts")
    # 13. Review 34 section 9 carried verbatim; rule version in the documents
    rev = (I.MR / "reviews" / "M2-review-34" / "INDEPENDENT-REVIEW.md").read_text(encoding="utf-8")
    s9 = rev[rev.index("## 9. What the ORCH-07 declaration must bind and decide"):rev.index("## 10. ")].rstrip("\n")
    body9 = s9.split("\n", 1)[1].strip("\n")
    report = (PKG / "CORRECTION-REPORT.md").read_text(encoding="utf-8")
    rule_doc = (PKG / "CONCENTRATION-RULE-R32.md").read_text(encoding="utf-8")
    c["documents"] = {"review34_section9_verbatim": body9 in report, "rule_version_in_rule_doc": K.RULE_VERSION in rule_doc,
                      "rule_version_in_report": K.RULE_VERSION in report, "statuses": all(s in report for s in ("CHANGES STILL REQUIRED", "M3:** not started"))}
    if not all(c["documents"].values()):
        problems.append("documents")
    # 14. LF and required documents
    crlf = [str(p.relative_to(PKG)) for p in PKG.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".py", ".xml")
            and b"\r\n" in p.read_bytes() and p.name not in CRLF_EXEMPT]
    missing = [r for r in REQUIRED if not (PKG / r).exists()]
    c["format"] = {"crlf_files": crlf, "missing_required": missing, "authorization_file_in_package": (PKG / "OWNER-DISPATCH-AUTHORIZATION.json").exists()}
    if crlf or missing or c["format"]["authorization_file_in_package"]:
        problems.append("format / required files")
    out = {"package": "review34 (ORCH-05C)", "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "checks": c, "problems": problems, "ok": not problems, "model_requests": 0, "reference_set_statement": I.REFERENCE_SET_STATEMENT}
    p = PKG / "evidence" / "PACKAGE-CHECK.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text(out))
    print(json.dumps({"ok": out["ok"], "problems": problems, "sha256": sha(p)}, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main("--skip-tests" in sys.argv))
