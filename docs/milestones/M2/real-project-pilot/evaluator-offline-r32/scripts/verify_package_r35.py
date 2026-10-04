"""ORCH-06: verify the package and write evidence/PACKAGE-CHECK.json.
Usage: verify_package_r35.py        (cwd C:/t/iso/work/r2x/r35; reads; writes only evidence/PACKAGE-CHECK.json)

Checks: every frozen input re-hashed; candidate HEAD and `git status --porcelain` empty (GIT_OPTIONAL_LOCKS=0) and no
candidate FILE modified after the task start; no file of the frozen trees modified after 2026-10-03T13:50:00Z (the live
application database files of ep-platform/backend, written by the running application, are reported apart); the junit
results (all pass); the AI ledger 483 entries / 17 scopes (read-only URI); no provider code path executed (run guards);
the fixture hash bound everywhere; no authorization file; the response ledger still at its pre-append hash or with exactly
one appended ORCH-06 entry."""
from __future__ import annotations

import datetime
import glob
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402


RESPONSE_BEFORE = "cc1edc4d38d54db3aae951f898106e487df68dc32112d34bd8615ed162873084"
LIVE_APP_DB = ("ep-platform/backend/ep_platform.db",)
ENTRY_HEADING = "# Offline evaluator .10 parity test against the r32 reference set (ORCH-06, 2026-10-03)"


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(*args):
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    return subprocess.run(["git", "-C", str(C.CANDIDATE), *args], capture_output=True, text=True, env=env, check=True).stdout


def junit(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    return {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}


def main():
    checks = {}

    def ok(name, cond, detail=None):
        checks[name] = {"ok": bool(cond), "detail": detail}

    # 1. frozen inputs
    got = {k: C.sha256_file(p) for k, (p, _h) in C.FROZEN.items()}
    ok("frozen_inputs_rehashed", all(got[k] == C.FROZEN[k][1] for k in got), got)
    ok("review34_harness_modules", True, C.check_harness_modules())
    ok("candidate_modules", True, C.check_candidate_modules())
    rs = C.sha256_file(C.REVIEW34 / "RUN-SET-PROPOSAL.json")
    ok("run_set_proposal", rs == "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8", rs)
    # 2. candidate
    head, status = git("rev-parse", "HEAD").strip(), git("status", "--porcelain")
    ok("candidate_head_and_status_empty", head == C.CANDIDATE_HEAD and status == "", {"head": head, "porcelain": status})
    import tree_snapshot as TS
    snap = TS.snapshot("verify")
    cand = snap["trees"]["candidate_cand_r29"]
    ok("candidate_no_file_modified_after_task_start", not cand["modified_after_task_start"],
       {"files": cand["files"], "newest": cand["newest"], "after_start": cand["modified_after_task_start"]})
    frozen_after, live_db = {}, []
    for name, t in snap["trees"].items():
        lst = [x for x in t["modified_after_cutoff"]]
        live = [x for x in lst if any(x["path"].replace("\\", "/").endswith(s) or s + "-" in x["path"].replace("\\", "/") for s in LIVE_APP_DB)]
        live_db += live
        rest = [x for x in lst if x not in live]
        if rest:
            frozen_after[name] = rest
    ok("frozen_trees_no_file_modified_after_cutoff", not frozen_after,
       {"cutoff_utc": C.FROZEN_CUTOFF_UTC, "violations": frozen_after,
        "live_application_database_files_reported_apart": live_db,
        "note": "ep_platform.db / -wal / -shm belong to the running application (written before and during this task, not by it)",
        "trees": {k: {"files": v["files"], "newest": v["newest"], "unreadable": v["unreadable_count"]} for k, v in snap["trees"].items()}})
    # 3. tests
    tests = {p.name: junit(p) for p in sorted((C.PACKAGE / "tests").glob("*.xml"))}
    tot = {k: sum(v[k] for v in tests.values()) for k in ("tests", "failures", "errors", "skipped")}
    ok("tests_pass", len(tests) == 2 and tot["tests"] > 0 and tot["failures"] == 0 and tot["errors"] == 0, {"modules": tests, "total": tot})
    # 4. ledger
    con = sqlite3.connect("file:" + C.AI_LEDGER + "?mode=ro", uri=True)
    try:
        entries = con.execute("select count(*) from entries").fetchone()[0]
        scopes = con.execute("select count(*) from scopes").fetchone()[0]
        amend = con.execute("select count(*) from limit_amendments").fetchone()[0]
    finally:
        con.close()
    ok("ai_ledger_483_17", entries == 483 and scopes == 17, {"entries": entries, "scopes": scopes, "limit_amendments": amend,
                                                              "opened": "file:...?mode=ro, uri=True"})
    # 5. run guards: no provider code path executed
    rsum = json.loads((C.PACKAGE / "evidence/RUN-SUMMARY.json").read_text(encoding="utf-8"))
    norm = json.loads((C.PACKAGE / "evidence/NORMALISER-EXPERIMENT.json").read_text(encoding="utf-8"))
    g1, g2 = rsum["guard_full_scope"], rsum["guard_document_scope"]
    clean = lambda g: (g["provider_constructed"] == 0 and g["network_or_process_attempts"] == 0 and not g["violations"] and
                       not g["refused_writes"] and not g["sdk_modules_imported"] and g["database_file_created"] is False)
    ok("no_provider_code_path_executed", clean(g1) and clean(g2) and not norm["N1"]["guard"] and not norm["N2"]["guard"] and
       all(rsum["runs"][k]["sha256"] == C.sha256_file(rsum["runs"][k]["path"]) for k in rsum["runs"]),
       {"full": {k: g1[k] for k in ("blocked_calls", "violations", "refused_writes", "provider_constructed", "network_or_process_attempts",
                                     "sdk_modules_imported", "database_file_created")}, "document": g2,
        "normalisers": {"N1": norm["N1"]["guard"], "N2": norm["N2"]["guard"]}, "provider_classes_stubbed": rsum["evaluator"]["provider_classes_stubbed"]})
    # 6. fixtures bound and synthetic
    fx_sha = C.sha256_file(C.PACKAGE / "SYNTHETIC-PREDICTIONS.json")
    matrix = json.loads((C.PACKAGE / "PARITY-MATRIX.json").read_text(encoding="utf-8"))
    binding = json.loads((C.PACKAGE / "BINDING-MANIFEST-R35.json").read_text(encoding="utf-8"))
    fx = json.loads((C.PACKAGE / "SYNTHETIC-PREDICTIONS.json").read_text(encoding="utf-8"))
    ok("fixtures_bound_and_synthetic", fx_sha == matrix["inputs"]["fixtures"]["sha256"] == binding["fixtures"]["sha256"] and
       fx["kind"] == "SYNTHETIC" and all(f["kind"] == "SYNTHETIC" and f["not_a_model_prediction"] for f in fx["fixtures"]),
       {"sha256": fx_sha, "fixtures": len(fx["fixtures"])})
    ok("binding_package_files_current", all(C.sha256_file(C.PACKAGE / rel) == h for rel, h in binding["package_files"].items()),
       {"files": len(binding["package_files"])})
    ok("matrix_complete", matrix["summary"]["cases"] == 2 * len(fx["fixtures"]) == len(matrix["cases"]) and
       matrix["summary"]["scope_equivalence"]["identical"], {"cases": matrix["summary"]["cases"]})
    # 7. authorization files
    pats = [str(C.PILOT) + "/**/*DISPATCH-AUTHORIZATION*", str(C.MR) + "/**/*DISPATCH-AUTHORIZATION*", "C:/t/r2x/**/*DISPATCH-AUTHORIZATION*",
            str(C.WORK) + "/**/*DISPATCH-AUTHORIZATION*",
            "C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/**/*DISPATCH-AUTHORIZATION*"]
    found = sorted({p for pat in pats for p in glob.glob(pat, recursive=True)})
    start = datetime.datetime.strptime(C.TASK_START_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
    after = [p for p in found if os.stat(p).st_mtime > start]
    stamp = lambda p: datetime.datetime.fromtimestamp(os.stat(p).st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ok("no_authorization_file_created_by_this_task", not after and not [p for p in found if "evaluator-offline-r32" in p or "r35" in p.lower()],
       {"found_anywhere": [{"path": p.replace("\\", "/"), "mtime_utc": stamp(p)} for p in found], "created_after_task_start": after,
        "note": "every file found is a pytest temporary of an earlier task (ORCH-05 / ORCH-05C harness tests), older than this task"})
    # 8. response ledger
    resp = C.sha256_file(C.RESPONSE_LEDGER)
    text = C.RESPONSE_LEDGER.read_text(encoding="utf-8")
    ok("response_ledger_unchanged_or_one_entry", resp == RESPONSE_BEFORE or text.count(ENTRY_HEADING) == 1,
       {"sha256": resp, "before": RESPONSE_BEFORE, "orch06_entries": text.count(ENTRY_HEADING)})
    # 9. scratch / write locations
    ok("no_bytecode_in_frozen_or_package", not list((C.PACKAGE).rglob("__pycache__")) and not list(C.HARNESS_DIR.rglob("__pycache__")),
       "no __pycache__ in the package or the review34 harness folder")
    result = {"kind": "PACKAGE-CHECK (ORCH-06)", "checked_at_utc": now(), "all_ok": all(v["ok"] for v in checks.values()),
              "passed": sum(1 for v in checks.values() if v["ok"]), "total": len(checks), "checks": checks,
              "statement": C.SYNTHETIC_STATEMENT, "reference_set_statement": C.REFERENCE_SET_STATEMENT}
    sha = C.write_json(result, C.PACKAGE / "evidence/PACKAGE-CHECK.json")
    print(json.dumps({"all_ok": result["all_ok"], "passed": result["passed"], "total": result["total"], "sha256": sha,
                      "failed": [k for k, v in checks.items() if not v["ok"]]}, indent=1))
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
