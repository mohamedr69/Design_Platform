"""ORCH-08 (R38HARNESS-IMPL): the package check of PILOT/review38/ -> evidence/PACKAGE-CHECK.json (written before the
evidence manifest). Read-only everywhere except the two output files (PACKAGE-CHECK.json and evidence/SNAPSHOT-AFTER.json).

Usage: verify_review38_package.py <PACKAGE-CHECK.json>
Checks (each recorded with its evidence; the package passes only when every one passes):
  inputs            every frozen input of the task recomputes (PACKET MISMATCH otherwise); the review36, declaration-r32 and
                    evaluator-offline-r32 manifests re-hash every listed file
  frozen_trees      a fresh read-only snapshot equals SNAPSHOT-BEFORE (taken 2026-10-03T18:40Z) for every frozen tree, and no file
                    there is newer than 2026-10-03T18:45:00Z
  repos             candidate a8aacedd and baseline 3d5607d9, both clean
  ai_ledger         mode=ro: 483 entries, 17 scopes, 0 amendments; no scope created
  harness           the package harness equals the work harness and FREEZE-1; the per-file table; every carried file equals its
                    review36 hash
  binding           preflight_r32.verify_binding(BINDING-MANIFEST-R38.json) re-hashes every bound file
  tests             tests/SUMMARY.json and every junit XML: all passed, 0 failures / errors, 0 guard refusals
  no_authorization  no OWNER-DISPATCH-AUTHORIZATION*, no *.RUN.json declaration, no token file under PILOT, the work folder or the
                    r38 sandbox base
  guard_refusals    dispatch_guard_r32.check without a declaration refuses; GuardedProvider refuses without building the provider;
                    a dry_exercise declaration is never live
  visibility        VISIBILITY-RESULT.json: every injected event visible in every reachable place, 0 model requests, AI ledger
                    unchanged, no bound fingerprint re-sent
  whatif            CROSS-PAGE-WHATIF.json: the r36 copy reproduces the frozen matrix except the H1 cases; its pass files hash as bound
  bounds            PROJECT-REQUEST-BOUNDS.json equals its recomputation
  response_ledger   M2-REVIEW-RESPONSE.md still hashes to 664fc295... (the append happens after the manifest)"""
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r38")
PKG = PILOT / "review38"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
CUTOFF = "2026-10-03T18:45:00+00:00"
INPUTS = {
    "review36 manifest": (PILOT / "review36/evidence/EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0"),
    "BINDING-MANIFEST-R36": (PILOT / "review36/BINDING-MANIFEST-R36.json", "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568"),
    "declaration-r32 manifest": (PILOT / "declaration-r32/evidence/EVIDENCE-MANIFEST.json", "59361b9331cf3d28979129dfa1749b10f345e5ad24f26b9691012423fd1be2c8"),
    "declaration-r32 (superseded)": (PILOT / "declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json", "38e08df9bed5582bcf171129654fe93984caab4251f8ddbd3dd2e164a3d876b0"),
    "RUN-SET-PROPOSAL": (PILOT / "review34/RUN-SET-PROPOSAL.json", "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"),
    "TRUTH-R32": (PILOT / "review34/dry-run/TRUTH-R32.json", "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"),
    "reviewed-2 labels": (PILOT / "fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json", "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    "SYNTHETIC-PREDICTIONS": (PILOT / "evaluator-offline-r32/SYNTHETIC-PREDICTIONS.json", "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774"),
    "evaluator-offline-r32 manifest": (PILOT / "evaluator-offline-r32/evidence/EVIDENCE-MANIFEST.json", "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7"),
    "Verification 38": (MR / "reviews/M2-review-38/INDEPENDENT-VERIFICATION.md", "006d0203aaa98a9973de140ab73ac2e127df06f827c686b1f2629c1ae607f5c7"),
}
RESPONSE = (PILOT.parent / "M2-REVIEW-RESPONSE.md", "664fc295e4f8239b70cbec51a5a573e7e9943d60ee8ac1c255e6fe3426c55652")
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_inputs():
    got = {k: {"path": p.as_posix(), "sha256": sha(p), "expected": w, "equal": sha(p) == w} for k, (p, w) in INPUTS.items()}
    manifests = {}
    for pkg, n in (("review36", 135), ("declaration-r32", 56), ("evaluator-offline-r32", 25)):
        m = json.loads((PILOT / pkg / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
        bad = [k for k, v in m.items() if sha(PILOT / pkg / k) != v["sha256"]]
        manifests[pkg] = {"listed": len(m), "expected": n, "bad": bad, "ok": not bad and len(m) == n}
    return {"ok": all(v["equal"] for v in got.values()) and all(v["ok"] for v in manifests.values()), "inputs": got, "manifests": manifests}


def check_frozen_trees():
    after = WORK / "evidence" / "SNAPSHOT-AFTER.json"
    r = subprocess.run([PY, "-B", str(WORK / "scripts" / "snapshot_r38.py"), str(after)], capture_output=True, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"})
    if r.returncode:
        return {"ok": False, "error": r.stderr[-1000:]}
    b = json.loads((WORK / "evidence" / "SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    a = json.loads(after.read_text(encoding="utf-8"))
    (PKG / "evidence").mkdir(parents=True, exist_ok=True)
    (PKG / "evidence" / "SNAPSHOT-AFTER.json").write_bytes(after.read_bytes())
    out, ok = {}, True
    for kind in ("hashed_trees", "listed_trees"):
        for name, t in b[kind].items():
            if name == "MR-orchestrator":
                out[name] = {"compared": False, "why": "the orchestrator's own folder (not a frozen tree of this task); recorded only",
                             "equal": t["digest"] == a[kind][name]["digest"]}
                continue
            eq = t["digest"] == a[kind][name]["digest"]
            newer = sorted(k for k, v in a[kind][name]["entries"].items() if v["mtime_utc"] > CUTOFF) if isinstance(a[kind][name].get("entries"), dict) else []
            out[name] = {"files": t["files"], "equal_to_before": eq, "newer_than_cutoff": newer[:10], "newer_count": len(newer)}
            ok = ok and eq and not newer
    return {"ok": ok, "cutoff_utc": CUTOFF, "before_taken_utc": b["taken_utc"], "after_taken_utc": a["taken_utc"], "trees": out,
            "repos_after": a["repos"], "ledger_after": a["ai_ledger"]}


def check_repos():
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    out = {}
    for name, (repo, want) in {"candidate": ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"),
                               "baseline": ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")}.items():
        h = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
        d = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
        out[name] = {"head": h, "expected": want, "clean": not d, "ok": h == want and not d}
    return {"ok": all(v["ok"] for v in out.values()), "repos": out}


def check_ledger():
    con = sqlite3.connect(f"file:{LEDGER}?mode=ro", uri=True)
    try:
        c = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
             "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
             "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest()}
    finally:
        con.close()
    return {"ok": (c["entries"], c["scopes"], c["limit_amendments"]) == (483, 17, 0)
                  and c["scope_names_sha256"] == "a037785aba929442f67a179eff144e06c2777f72a42bc4741f6165f952db663e",
            "opened": "file:...?mode=ro, uri=True", **c}


def check_harness():
    work = {p.name: sha(p) for p in (WORK / "harness-r32").iterdir()}
    pkg = {p.name: sha(p) for p in (PKG / "scripts" / "harness-r32").iterdir()}
    freeze = {}
    for line in (WORK / "out" / "FREEZE-1.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, n = line.split(" ", 1)
            freeze[n.strip()] = h
    table = json.loads((PKG / "evidence" / "HARNESS-FILES-R36-R38.json").read_text(encoding="utf-8"))["files"]
    r36 = {p.name: sha(p) for p in (PILOT / "review36" / "scripts" / "harness-r32").iterdir()}
    carried = {n: {"review36_sha256": r36[n], "review38_sha256": work[n], "equal": r36[n] == work[n]} for n, r in table.items() if r["status"] == "unchanged"}
    table_ok = all((r["r38_sha256"] == work.get(n)) and (r["review36_sha256"] == r36.get(n)) for n, r in table.items())
    return {"ok": work == pkg == freeze and table_ok and all(v["equal"] for v in carried.values()) and len(work) == 50,
            "files": len(work), "package_equals_work": work == pkg, "work_equals_freeze_1": work == freeze, "table_ok": table_ok,
            "carried_unchanged": carried, "counts": {s: sum(1 for r in table.values() if r["status"] == s) for s in ("unchanged", "changed", "new", "removed")}}


def check_binding():
    sys.path.insert(0, str(WORK / "harness-r32"))
    import preflight_r32 as PF
    b = PKG / "BINDING-MANIFEST-R38.json"
    s = sha(b)
    try:
        v = PF.verify_binding(b, s)
        return {"ok": True, "sha256": s, **v}
    except PF.Refused as exc:
        return {"ok": False, "sha256": s, "refused": str(exc)}


def check_tests():
    summ = json.loads((PKG / "tests" / "SUMMARY.json").read_text(encoding="utf-8"))
    junit = {}
    for x in sorted((PKG / "tests").glob("*.xml")):
        root = ET.parse(x).getroot()
        suites = [root] if root.tag == "testsuite" else list(root)
        junit[x.name] = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    total = {k: sum(v[k] for v in junit.values()) for k in ("tests", "failures", "errors", "skipped")}
    guards = {g.name: json.loads(g.read_text(encoding="utf-8"))["refused_count"] for g in sorted((PKG / "tests" / "guard").glob("*.json"))}
    expected = {f"{m}.xml" for m in json.loads(json.dumps(summ["modules"]))}
    return {"ok": summ["all_passed"] and summ["guard_refusals"] == 0 and total["failures"] == 0 and total["errors"] == 0 and total == summ["total"]
                  and set(junit) == expected and len(junit) == 20 and not any(guards.values()),
            "modules": len(junit), "total": total, "per_module": junit, "guard_refused": sum(guards.values()), "no_twin": summ.get("no_twin")}


def check_no_authorization():
    roots = [PILOT, WORK, pathlib.Path("C:/t/r2x/r38-sandbox")]
    found = []
    for r in roots:
        for dirpath, _dirs, files in os.walk(r):
            for f in files:
                low = f.lower()
                if low.startswith("owner-dispatch-authorization") or low.endswith(".run.json") or "token" in low:
                    found.append(os.path.join(dirpath, f).replace("\\", "/"))
    return {"ok": not found, "roots": [r.as_posix() for r in roots], "found": found,
            "rule": "no OWNER-DISPATCH-AUTHORIZATION*, no *.RUN.json declaration, no file named *token*"}


def check_guard_refusals():
    sys.path.insert(0, str(WORK / "harness-r32"))
    import dispatch_guard_r32 as DG
    import preflight_r32 as PF
    c = DG.check(None, None, run_folder=None, invocation=1)
    built = []

    class Resp:
        def __init__(self, **k):
            self.__dict__.update(k)
    g = DG.GuardedProvider(lambda: built.append(1), None, None, Resp, run_folder=None, invocation=1)
    r = g.complete(object())
    try:
        PF.validate_declaration({"dry_exercise": True}, "x.json")
        dry = "accepted"
    except PF.Refused as exc:
        dry = str(exc)
    ok = c["authorized"] is False and r.error == "dispatch_refused" and not built and dry.startswith("refused")
    return {"ok": ok, "check_without_declaration": c, "guarded_provider": {"error": r.error, "inner_built": bool(built)}, "dry_exercise_declaration": dry}


def check_visibility():
    v = json.loads((PKG / "VISIBILITY-RESULT.json").read_text(encoding="utf-8"))
    return {"ok": v["all_visible"] and v["no_resend"] and v["model_requests"] == 0 and v["ai_ledger"]["unchanged"],
            "scenarios": {k: {"recorded_in": s["recorded_in"], "silent_places": s["silent_places"]} for k, s in v["scenarios"].items()},
            "model_requests": v["model_requests"], "ai_ledger": v["ai_ledger"]}


def check_whatif():
    w = json.loads((PKG / "CROSS-PAGE-WHATIF.json").read_text(encoding="utf-8"))
    passes = json.loads((PKG / "evidence" / "WHATIF-PASSES.json").read_text(encoding="utf-8"))["passes"]
    pass_ok = all(sha(p["path"]) == p["sha256"] for p in passes.values()) and \
        [passes[n]["sha256"] for n in ("PASS-R36.json", "PASS-R38.json", "PASS-R38-NOSOURCE.json")] == \
        [w["inputs"][k] for k in ("r36_pass", "r38_pass", "r38_nosource_pass")]
    rep = w["reproduction_of_frozen_matrix_by_the_r36_copy"]
    return {"ok": pass_ok and rep["differing_are_exactly_the_h1_cases"] and w["side_rows_changed"] == 0,
            "changed_target_verdicts": w["changed_target_verdicts"], "changed_fixtures": len(w["changed_fixtures"]),
            "kept": w["associations_kept_with_evidence"]["by_relationship"], "reproduction": rep, "pass_files_ok": pass_ok}


def check_bounds():
    sys.path.insert(0, str(WORK / "harness-r32"))
    import preflight_r32 as PF
    import project_bounds_r32 as PB
    import runner_r32 as RN
    b = json.loads((PKG / "PROJECT-REQUEST-BOUNDS.json").read_text(encoding="utf-8"))
    T = PF.build_truth()
    again = PB.compute(PF.load_run_set(PILOT / "review34/RUN-SET-PROPOSAL.json", T), T, RN.DRY_LANE_SWITCHES, window_limit=60, window_s=86400, elapsed_s=604800)
    keys = ("projects", "lanes", "compatible_limits", "per_document", "per_page_maximum", "version", "code_constants")
    diff = [k for k in keys if again[k] != b[k]]
    return {"ok": not diff, "differs_in": diff, "sha256": sha(PKG / "PROJECT-REQUEST-BOUNDS.json"),
            "EP-27331": {"planning": b["projects"]["EP-27331"]["planning"], "structural_maximum": b["projects"]["EP-27331"]["structural_maximum"]},
            "required_minimum": b["compatible_limits"]["required_minimum"]}


def check_response():
    s = sha(RESPONSE[0])
    return {"ok": s == RESPONSE[1], "sha256": s, "expected_before_append": RESPONSE[1]}


def main(out):
    checks = {}
    for name, fn in (("inputs", check_inputs), ("frozen_trees", check_frozen_trees), ("repos", check_repos), ("ai_ledger", check_ledger),
                     ("harness", check_harness), ("binding", check_binding), ("tests", check_tests), ("no_authorization", check_no_authorization),
                     ("guard_refusals", check_guard_refusals), ("visibility", check_visibility), ("whatif", check_whatif), ("bounds", check_bounds),
                     ("response_ledger", check_response)):
        try:
            checks[name] = fn()
        except Exception as exc:  # noqa: BLE001 -- a check that cannot run fails
            checks[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print(name, checks[name]["ok"], flush=True)
    res = {"kind": "ORCH-08 review38 package check", "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "package": PKG.as_posix(), "all_ok": all(c["ok"] for c in checks.values()), "checks": checks,
           "statement": "a self-check by the implementer; not an independent verification (ORCH-08V follows); it authorizes nothing"}
    pathlib.Path(out).write_text(json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": res["all_ok"]}))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
