"""ORCH-07 (R37DECL-IMPL): copy the task scripts into the package, the package check, and the evidence manifest (last).

Usage: package_r37.py copy-scripts           scripts -> PILOT/declaration-r32/scripts/ (byte copies; refuses an existing file)
       package_r37.py check [--skip-tests]   evidence/PACKAGE-CHECK.json (written once)
       package_r37.py manifest               evidence/EVIDENCE-MANIFEST.json (written once, LAST)
Read-only on every frozen tree; the AI ledger is opened mode=ro, uri=True."""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
import build_declaration_r37 as BD  # noqa: E402
import r37common as C  # noqa: E402
import snapshot_r37 as SN  # noqa: E402

SCRIPTS = ("r37common.py", "snapshot_r37.py", "estimates_r37.py", "concentration_on_proposal_r37.py", "build_declaration_r37.py", "preflight_r37.py",
           "dry_exercise_r37.py", "package_r37.py", "append_response_r37.py", "run_tests_r37.py", "test_r37.py")
FROZEN_MTIME_LIMIT = "2026-10-03T16:55:00+00:00"
TASK_START = "2026-10-03T16:49:00+00:00"
REQUIRED_DOCS = ("FRESH-VALIDATION-DECLARATION-R32.json", "DECLARATION.sha256", "BUDGET-DECISION-CARD.v3.md", "CONCENTRATION-ON-PROPOSAL.md",
                 "PREFLIGHT-REPORT.md", "DECLARATION-SUMMARY.md", "COMMANDS.md", "COMMANDS-AND-AUDIT-LOG.md", "dry-run/PREFLIGHT-RESULTS.json",
                 "dry-run/DRY-EXERCISE.json", "dry-run/TWIN-RECORD.json", "concentration/CONCENTRATION-ON-PROPOSAL.json", "tests/test_r37.xml",
                 "evidence/SNAPSHOT-BEFORE.json", "evidence/SNAPSHOT-AFTER.json")


def copy_scripts() -> dict:
    out = {}
    for s in SCRIPTS:
        src, dst = C.WORK / s, C.PACKAGE / "scripts" / s
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "xb") as fh:
            fh.write(src.read_bytes())
        out[s] = C.sha256_file(dst)
    return out


def package_listing(exclude=()) -> dict:
    out = {}
    for p in sorted(C.PACKAGE.rglob("*")):
        if p.is_file():
            rel = p.relative_to(C.PACKAGE).as_posix()
            if rel not in exclude:
                out[rel] = {"sha256": C.sha256_file(p), "bytes": p.stat().st_size}
    return out


def frozen_mtime_check(snapshot: dict, limit: str = FROZEN_MTIME_LIMIT) -> dict:
    late = {k: sorted(f for f, v in t["files"].items() if v["mtime_utc"] > limit) for k, t in snapshot["trees"].items()}
    late = {k: v for k, v in late.items() if v}
    singles = sorted(k for k, v in snapshot["single_files"].items() if v["mtime_utc"] > limit)
    return {"limit_utc": limit, "files_modified_after_limit": late, "single_files_modified_after_limit": singles, "ok": not late and not singles}


def junit_summary(path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    t = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    t["names"] = sorted(c.get("name") for s in suites for c in s.iter("testcase"))
    return t


def check(skip_tests: bool) -> int:
    at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    res = {"name": "PACKAGE-CHECK (ORCH-07, declaration-r32)", "at_utc": at, "checks": {}}
    ck = res["checks"]
    ck["frozen_task_inputs"] = C.check_frozen()
    ck["declaration_bound_hashes_recomputed"] = {k: v["sha256"] for k, v in BD.hashes().items()}
    decl_path = C.PACKAGE / C.DECLARATION_NAME
    raw = decl_path.read_bytes()
    sha = C.sha256_bytes(raw)
    recorded = (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]
    decl = json.loads(raw.decode("utf-8"))
    ck["declaration"] = {"sha256": sha, "DECLARATION.sha256": recorded, "equal": sha == recorded, "bytes": len(raw), "lf_only": b"\r" not in raw,
                         "canonical_json": C.json_text(decl).encode("utf-8") == raw, "placeholder_once": raw.count(json.dumps(C.TOKEN_PLACEHOLDER).encode()) == 1,
                         "executed": decl["executed"], "budget_approved": decl["budget_approved"], "authorization_status": decl["authorization_status"],
                         "owner_token_sha256": decl["authorization"]["owner_token_sha256"], "scope": decl["ledger"]["scope"], "stamp": decl["run"]["stamp"]}
    pre = json.loads((C.PACKAGE / "dry-run/PREFLIGHT-RESULTS.json").read_text(encoding="utf-8"))
    dry = json.loads((C.PACKAGE / "dry-run/DRY-EXERCISE.json").read_text(encoding="utf-8"))
    ck["preflight_results"] = {"ok": pre["ok"], "declaration_sha256": pre["declaration"]["sha256"], "results": {k: v.get("result") for k, v in pre["checks"].items()},
                               "invariants": pre["invariants"], "files_verified": pre["checks"]["verify_binding"]["files_verified"]}
    ck["dry_exercise"] = {"declaration_sha256": dry["declaration_sha256"], "returncode": dry["returncode"], "model_requests_total": dry["model_requests_total"],
                          "ai_ledger_unchanged_483_17_0": dry["ai_ledger_unchanged_483_17_0"], "checks_before": dry["checks_before"],
                          "switches_equal_declaration": {k: v["switches_equal_declaration"] for k, v in dry["lanes"].items()},
                          "live_provider_attempts_blocked": {k: v["live_provider_attempts_blocked"] for k, v in dry["lanes"].items()},
                          "exercise_copies_equal": all(C.sha256_file(C.PACKAGE / "dry-run/exercise" / f) == h for f, h in dry["copied"].items())}
    ck["scripts_equal_work_folder"] = {s: C.sha256_file(C.PACKAGE / "scripts" / s) == C.sha256_file(C.WORK / s) for s in SCRIPTS}
    tests = junit_summary(C.PACKAGE / "tests/test_r37.xml")
    ck["tests_packaged"] = {k: tests[k] for k in ("tests", "failures", "errors", "skipped")}
    if not skip_tests:
        tmp = C.SCRATCH / f"check-tests-{datetime.datetime.now().strftime('%H%M%S')}"
        tmp.mkdir(parents=True)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONIOENCODING": "utf-8", "GIT_OPTIONAL_LOCKS": "0"}
        r = subprocess.run([C.PY, "-B", "-m", "pytest", "-q", "test_r37.py", f"--junitxml={tmp / 'test_r37.xml'}", f"--basetemp={tmp / 'bt'}"],
                           cwd=str(C.WORK), env=env, capture_output=True, text=True, timeout=1200)
        rerun = junit_summary(tmp / "test_r37.xml")
        ck["tests_rerun"] = {k: rerun[k] for k in ("tests", "failures", "errors", "skipped")} | {"returncode": r.returncode,
                                                                                               "same_names_as_packaged": rerun["names"] == tests["names"]}
    led = C.ledger_state()
    ck["ai_ledger"] = {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")} | {
        "expected_483_17_0": {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED, "declared_scope_absent": decl["ledger"]["scope"] not in led["scope_names"]}
    ck["no_authorization_file"] = {"pinned_path": (C.PACKAGE / C.AUTH_NAME).as_posix(), "pinned_exists": (C.PACKAGE / C.AUTH_NAME).exists(),
                                   "search_roots": [p.as_posix() for p in SN.AUTH_SEARCH_ROOTS], "files_found": C.authorization_files(SN.AUTH_SEARCH_ROOTS)}
    ck["no_token"] = {"R34_OWNER_DISPATCH_TOKEN_in_environment": "R34_OWNER_DISPATCH_TOKEN" in os.environ,
                      "dummy_digest_in_any_package_file": any(C.DUMMY_DIGEST.encode() in (C.PACKAGE / f).read_bytes() for f in package_listing()),
                      "statement": "no token was generated; the declaration binds the placeholder; the dummy digest of the in-memory checks exists only as code ('0' * 63 + '1') and was never written as a value"}
    ck["run_folder_absent"] = {"path": (C.LIVE_SANDBOX_BASE / BD.STAMP).as_posix(), "exists": (C.LIVE_SANDBOX_BASE / BD.STAMP).exists()}
    ck["git"] = {"candidate": C.git_state(C.CANDIDATE[0]), "baseline": C.git_state(C.BASELINE[0])}
    before = json.loads((C.PACKAGE / "evidence/SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    after = json.loads((C.PACKAGE / "evidence/SNAPSHOT-AFTER.json").read_text(encoding="utf-8"))
    ck["frozen_trees_before_vs_after"] = SN.compare(before, after)
    ck["frozen_mtime_after_limit"] = frozen_mtime_check(after)
    ck["frozen_mtime_after_task_start"] = frozen_mtime_check(after, TASK_START)
    ck["response_ledger"] = {"sha256_now": C.sha256_file(C.RESPONSE_LEDGER), "expected_before_append": C.RESPONSE_BEFORE_SHA256,
                             "unchanged_so_far": C.sha256_file(C.RESPONSE_LEDGER) == C.RESPONSE_BEFORE_SHA256}
    ck["required_documents_present"] = {d: (C.PACKAGE / d).is_file() for d in REQUIRED_DOCS}
    ok = (ck["declaration"]["equal"] and ck["declaration"]["lf_only"] and ck["declaration"]["canonical_json"] and ck["declaration"]["placeholder_once"]
          and ck["declaration"]["executed"] is False and ck["declaration"]["budget_approved"] is False and ck["preflight_results"]["ok"]
          and ck["preflight_results"]["declaration_sha256"] == sha and ck["dry_exercise"]["declaration_sha256"] == sha
          and ck["dry_exercise"]["returncode"] == 0 and ck["dry_exercise"]["model_requests_total"] == 0 and ck["dry_exercise"]["ai_ledger_unchanged_483_17_0"]
          and all(ck["dry_exercise"]["switches_equal_declaration"].values()) and ck["dry_exercise"]["exercise_copies_equal"]
          and all(ck["scripts_equal_work_folder"].values()) and ck["tests_packaged"]["failures"] == 0 and ck["tests_packaged"]["errors"] == 0
          and (skip_tests or (ck["tests_rerun"]["failures"] == 0 and ck["tests_rerun"]["errors"] == 0 and ck["tests_rerun"]["same_names_as_packaged"]))
          and ck["ai_ledger"]["expected_483_17_0"] and ck["ai_ledger"]["declared_scope_absent"] and not ck["no_authorization_file"]["pinned_exists"]
          and not ck["no_authorization_file"]["files_found"] and not ck["no_token"]["R34_OWNER_DISPATCH_TOKEN_in_environment"]
          and not ck["no_token"]["dummy_digest_in_any_package_file"] and not ck["run_folder_absent"]["exists"]
          and ck["git"]["candidate"]["clean"] and ck["git"]["candidate"]["head"] == C.CANDIDATE[1] and ck["git"]["baseline"]["clean"]
          and ck["git"]["baseline"]["head"] == C.BASELINE[1] and ck["frozen_trees_before_vs_after"]["trees_unchanged"]
          and ck["frozen_trees_before_vs_after"]["single_files_unchanged"] and ck["frozen_mtime_after_limit"]["ok"] and ck["frozen_mtime_after_task_start"]["ok"]
          and ck["response_ledger"]["unchanged_so_far"] and all(ck["required_documents_present"].values()))
    res["ok"] = bool(ok)
    res["package_files_at_check"] = package_listing()
    sha_out = C.write_json_once(C.PACKAGE / "evidence/PACKAGE-CHECK.json", res)
    print(json.dumps({"ok": res["ok"], "sha256": sha_out, "declaration": sha, "tests_packaged": ck["tests_packaged"], "tests_rerun": ck.get("tests_rerun"),
                      "ledger": ck["ai_ledger"], "frozen": ck["frozen_trees_before_vs_after"], "mtime": ck["frozen_mtime_after_limit"]["ok"]}, indent=1))
    return 0 if res["ok"] else 1


def manifest() -> int:
    target = C.PACKAGE / "evidence/EVIDENCE-MANIFEST.json"
    files = package_listing(exclude=("evidence/EVIDENCE-MANIFEST.json",))
    man = {"name": "declaration-r32 evidence manifest (ORCH-07, R37DECL-IMPL)", "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "package": C.PACKAGE.as_posix(), "files": files, "file_count": len(files),
           "declaration_sha256": files[C.DECLARATION_NAME]["sha256"], "package_check_sha256": files["evidence/PACKAGE-CHECK.json"]["sha256"],
           "rule": ("written once and last; lists every package file except itself; an OWNER-DISPATCH-AUTHORIZATION.json at the pinned path, or a "
                    "runnable (digest-filled) declaration, written later by the owner in this folder, is not part of this package"),
           "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed"}
    sha = C.write_json_once(target, man)
    print(json.dumps({"manifest": target.as_posix(), "sha256": sha, "file_count": len(files)}))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "copy-scripts":
        print(json.dumps(copy_scripts(), indent=1))
    elif cmd == "check":
        sys.exit(check("--skip-tests" in sys.argv))
    elif cmd == "manifest":
        sys.exit(manifest())
    else:
        raise SystemExit(__doc__)
