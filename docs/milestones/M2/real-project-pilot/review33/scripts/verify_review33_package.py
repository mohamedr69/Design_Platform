"""ORCH-05.1: the package checker of review33. Writes <package>/evidence/PACKAGE-CHECK.json. No model request.
Usage: verify_review33_package.py [--skip-tests]
Checks: every frozen input and manifest re-hashed (PACKET OK); the binding manifest and every file it binds; the package's
harness copies equal the bound work-folder files and harness-base equals review31's harness; every test module re-run
(all pass) and the packaged junit files report 0 failures / errors; the AI ledger read-only 483 entries / 17 scopes / 0
amendments; no file under the frozen trees modified after 2026-10-03T10:30:00Z (os.stat); no
OWNER-DISPATCH-AUTHORIZATION.json exists and the dispatch guard refuses; candidate / baseline HEADs clean; the response
ledger still at its pre-append hash; the dry-run facts (0 model requests, ledger unchanged, resume drill, guard refused);
the derived files are reproduced byte for byte by the adapter, converter and selector; every package text file uses LF
(except the byte-identical review31 copies); the required documents exist."""
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

R33 = pathlib.Path("C:/t/iso/work/r2x/r33")
sys.path.insert(0, str(R33 / "harness-r32"))
import converter_r32 as CV  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import inputs_r32 as I  # noqa: E402
import labels_adapter_r32 as A  # noqa: E402
import run_set_selector_r32 as RS  # noqa: E402

PKG = I.PILOT / "review33"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
RESPONSE = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md")
RESPONSE_BEFORE = "da5cc7981f6e65e05e843ee5a3b8e3520b2daa957acb8b1e7981e17abf7997f7"
CUTOFF = datetime.datetime(2026, 10, 3, 10, 30, 0, tzinfo=datetime.timezone.utc)
FROZEN = [I.PILOT / "review31", I.PILOT / "fresh-cohort-r32", I.PILOT / "fresh-cohort-r32-reviewed", I.PILOT / "fresh-cohort-r32-reviewed-2",
          I.MR / "reviews" / "M2-review-33", I.MR / "reviews" / "M2-label-review-r32-draft-1", I.MR / "AI-ACCURACY-POLICY.md",
          I.MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", pathlib.Path("C:/t/r2x/r32-stage"), pathlib.Path("C:/t/iso/cand-r29"),
          pathlib.Path("C:/t/iso/frozen-r12"), pathlib.Path("C:/t/iso/work/r2x/r32"), pathlib.Path("C:/t/iso/work/r2x/r32b"),
          pathlib.Path("C:/t/iso/work/r2x/r32c"), pathlib.Path(I.AI_LEDGER)]
REQUIRED = ["CORRECTION-REPORT.md", "ADAPTER-CONTRACT.md", "SCORER-CHANGES.md", "CONCENTRATION-RULE-R32.md", "RUN-SET-RULE.md", "RUN-SET-PROPOSAL.json",
            "LABELS-R32-EVAL-INPUT.json", "CONVERTER-RECONCILIATION.json", "DRY-RUN-REPORT.md", "COMMANDS.md", "COMMANDS-AND-AUDIT-LOG.md",
            "BINDING-MANIFEST-R33.json", "dry-run/DRY-RUN-REPORT.json", "dry-run/TRUTH-R32.json", "dry-run/INGEST-72.json",
            "dry-run/SCORER-SCENARIOS.json", "dry-run/GUARD-CHECK.json", "dry-run/runner/RUN-REPORT.json", "dry-run/runner/SCORE-BCR-R32.json"]
UNCHANGED_COPIES = {"capture_store.py", "state_check.py", "stop_rules.py", "test_capture_store.py", "test_state_check.py", "test_stop_rules.py"}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def text(obj):
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def main(skip_tests=False):
    c, problems = {}, []
    # 1. frozen inputs and manifests
    pre = subprocess.run([PY, str(R33 / "preflight_inputs.py")], capture_output=True, text=True)
    c["preflight_inputs"] = pre.stdout.strip().splitlines()[-1] if pre.stdout.strip() else pre.stderr[-500:]
    if c["preflight_inputs"] != "PACKET OK":
        problems.append("preflight inputs: " + c["preflight_inputs"])
    # 2. binding manifest
    bm = PKG / "BINDING-MANIFEST-R33.json"
    man = json.loads(bm.read_text(encoding="utf-8"))
    bad = [p for files in man["files"].values() for p, want in files.items() if not pathlib.Path(p).exists() or sha(p) != want]
    dry = json.loads((PKG / "dry-run" / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))
    c["binding"] = {"sha256": sha(bm), "files": sum(len(v) for v in man["files"].values()), "mismatches": bad,
                    "equals_the_dry_run_binding": sha(bm) == dry["runner"]["binding"]["sha256"]}
    if bad or not c["binding"]["equals_the_dry_run_binding"]:
        problems.append("binding manifest")
    # 3. package copies and harness-base
    work = {pathlib.Path(p).name: h for p, h in man["files"]["harness_r32"].items()}
    pkg = {p.name: sha(p) for p in (PKG / "scripts" / "harness-r32").glob("*.py")}
    base = {pathlib.Path(p).name: h for p, h in man["files"]["harness_base"].items()}
    r31 = {p.name: sha(p) for p in (I.PILOT / "review31" / "scripts" / "harness").glob("*.py")}
    c["copies"] = {"package_harness_equals_bound": pkg == work, "harness_base_equals_review31": base == r31,
                   "unchanged_review31_modules": {n: work.get(n) == r31.get(n) for n in sorted(UNCHANGED_COPIES)},
                   "package_scripts_equal_work": {p.name: sha(p) == sha(R33 / p.name) for p in (PKG / "scripts").glob("*.py")}}
    if not (pkg == work and base == r31 and all(c["copies"]["unchanged_review31_modules"].values()) and all(c["copies"]["package_scripts_equal_work"].values())):
        problems.append("copies")
    # 4. tests
    junit = {}
    for x in sorted((PKG / "tests").glob("*.xml")):
        root = ET.parse(x).getroot()
        suites = [root] if root.tag == "testsuite" else list(root)
        junit[x.name] = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    c["junit_packaged"] = {"files": junit, "tests": sum(v["tests"] for v in junit.values()),
                           "failures": sum(v["failures"] for v in junit.values()), "errors": sum(v["errors"] for v in junit.values())}
    if c["junit_packaged"]["failures"] or c["junit_packaged"]["errors"] or len(junit) != 15:
        problems.append("packaged junit")
    if not skip_tests:
        scratch = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r33harness/verify-" +
                               datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S"))
        r = subprocess.run([PY, str(R33 / "run_tests_r33.py"), str(scratch / "junit"), str(scratch / "tmp")], capture_output=True, text=True)
        rerun = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {"all_passed": False, "error": r.stderr[-1000:]}
        c["tests_rerun"] = {"all_passed": rerun.get("all_passed"), "total": rerun.get("total")}
        if not rerun.get("all_passed"):
            problems.append("tests re-run")
    # 5. ledger
    con = sqlite3.connect(f"file:{I.AI_LEDGER}?mode=ro", uri=True)
    c["ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                   "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0]}
    con.close()
    if (c["ledger"]["entries"], c["ledger"]["scopes"], c["ledger"]["limit_amendments"]) != (483, 17, 0):
        problems.append("ledger")
    # 6. frozen trees
    newer = []
    cut = CUTOFF.timestamp()
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
    c["frozen_trees"] = {"cutoff_utc": CUTOFF.isoformat(), "roots": [str(r) for r in FROZEN], "modified_after_cutoff": newer}
    if newer:
        problems.append(f"{len(newer)} frozen file(s) modified after the cutoff")
    # 7. the guard
    class Resp:
        def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
            self.error = error

    def must_not_build():
        raise AssertionError("built")

    g = DG.GuardedProvider(must_not_build, "0" * 64, Resp)
    c["guard"] = {"authorization_file": str(DG.AUTH_PATH), "exists": DG.AUTH_PATH.exists(), "check_none": DG.check(None),
                  "check_fake_hash": DG.check("0" * 64), "guarded_provider_response": g.complete(object()).error, "guarded_provider_built": g.inner is not None}
    if c["guard"]["exists"] or c["guard"]["check_none"]["authorized"] or c["guard"]["check_fake_hash"]["authorized"] or \
            c["guard"]["guarded_provider_response"] != "dispatch_refused" or c["guard"]["guarded_provider_built"]:
        problems.append("guard")
    # 8. heads
    heads = {}
    for repo, want in (("C:/t/iso/cand-r29", I.CANDIDATE_HEAD), ("C:/t/iso/frozen-r12", I.BASELINE_HEAD)):
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        heads[repo] = {"head": head, "clean": not dirty, "expected": want}
        if head != want or dirty:
            problems.append(f"head {repo}")
    c["heads"] = heads
    # 9. response ledger (before the single append)
    c["response_ledger"] = {"sha256": sha(RESPONSE), "expected_before_append": RESPONSE_BEFORE, "unchanged": sha(RESPONSE) == RESPONSE_BEFORE}
    if not c["response_ledger"]["unchanged"]:
        problems.append("response ledger changed before the append")
    # 10. dry-run facts
    rr = dry["runner"]
    c["dry_run"] = {"model_requests": dry["model_requests"], "provider_calls": dry["provider_calls"], "ledger_unchanged": dry["ledger_unchanged"],
                    "ledger_before": dry["ledger_before"], "ledger_after": dry["ledger_after"], "runner_model_requests": rr["model_requests"],
                    "resume_drill_passes": rr["resume_drill"]["passes"], "guard_refused": not rr["dispatch_guard"]["authorized"],
                    "readers": {k: v.get("reader") for k, v in rr["lanes"].items()}, "live_attempts_blocked": {k: v.get("live_provider_attempts_blocked") for k, v in rr["lanes"].items()},
                    "ingest_72_ok": dry["ingest_72"]["ok"], "state_checks": [rr["state_check_C"]["ok"], rr["state_check_R"]["ok"], dry["ingest_72"]["state_check"]["ok"]]}
    d = c["dry_run"]
    if d["model_requests"] or d["provider_calls"] or d["runner_model_requests"] or not d["ledger_unchanged"] or not d["resume_drill_passes"] or \
            not d["guard_refused"] or set(d["readers"].values()) != {"none"} or any(d["live_attempts_blocked"].values()) or not d["ingest_72_ok"] or not all(d["state_checks"]):
        problems.append("dry-run facts")
    # 11. derived files reproduced
    x = I.load_all()
    truth = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    prop = json.loads((PKG / "RUN-SET-PROPOSAL.json").read_text(encoding="utf-8"))
    rec_now = {"totals": CV.reconciliation_totals(CV.convert(truth), truth)}
    c["derived"] = {"truth": hashlib.sha256(text(truth).encode()).hexdigest() == sha(PKG / "dry-run" / "TRUTH-R32.json"),
                    "eval_input": hashlib.sha256(text(CV.convert(truth)).encode()).hexdigest() == sha(PKG / "LABELS-R32-EVAL-INPUT.json"),
                    "run_set": hashlib.sha256(text(RS.build_proposal(truth, inputs=prop["inputs"])).encode()).hexdigest() == sha(PKG / "RUN-SET-PROPOSAL.json"),
                    "reconciliation_totals": rec_now["totals"],
                    "population": {f: len(v) for f, v in A.population(truth).items()}}
    if not (c["derived"]["truth"] and c["derived"]["eval_input"] and c["derived"]["run_set"] and rec_now["totals"]["every_row_once"]):
        problems.append("derived files")
    # 12. LF and required documents
    crlf = [str(p.relative_to(PKG)) for p in PKG.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".py", ".xml")
            and b"\r\n" in p.read_bytes() and p.name not in UNCHANGED_COPIES]
    missing = [r for r in REQUIRED if not (PKG / r).exists()]
    c["format"] = {"crlf_files": crlf, "missing_required": missing, "authorization_file_in_package": (PKG / "OWNER-DISPATCH-AUTHORIZATION.json").exists()}
    if crlf or missing or c["format"]["authorization_file_in_package"]:
        problems.append("format / required files")
    out = {"package": "review33 (ORCH-05.1)", "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "checks": c, "problems": problems, "ok": not problems, "model_requests": 0,
           "reference_set_statement": I.REFERENCE_SET_STATEMENT}
    p = PKG / "evidence" / "PACKAGE-CHECK.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text(out))
    print(json.dumps({"ok": out["ok"], "problems": problems, "sha256": sha(p)}, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main("--skip-tests" in sys.argv))
