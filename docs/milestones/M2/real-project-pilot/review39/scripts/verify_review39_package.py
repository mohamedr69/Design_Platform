"""ORCH-08C (R39HARNESS-IMPL): the package check of PILOT/review39/ -> evidence/PACKAGE-CHECK.json (written before the
evidence manifest). review38's verify_review38_package.py adapted. Read-only everywhere except the two output files
(PACKAGE-CHECK.json and evidence/SNAPSHOT-AFTER.json, the latter also copied into the work folder).

Usage: verify_review39_package.py <PACKAGE-CHECK.json>
Checks (the package passes only when every one passes):
  inputs            every frozen input of the task recomputes; the review38, review36, declaration-r32 and evaluator-offline-r32
                    manifests re-hash every listed file
  frozen_trees      a fresh read-only snapshot equals SNAPSHOT-BEFORE for every frozen tree, and no file there is newer than the
                    task start (2026-10-04T09:00:00Z); the orchestrator's folder is recorded, not compared
  repos             candidate a8aacedd and baseline 3d5607d9, both clean
  ai_ledger         mode=ro: 483 entries, 17 scopes, 0 amendments; the scope names unchanged
  harness           the package harness equals the work harness and FREEZE-1; the per-file table against review38; every unchanged
                    file equals its review38 hash; the review38 base copy equals the review38 manifest
  binding           preflight_r32.verify_binding(BINDING-MANIFEST-R39.json) re-hashes every bound file
  tests             tests/SUMMARY.json and every junit XML: all passed, 0 failures / errors, 0 guard refusals, 22 modules
  no_authorization  no OWNER-DISPATCH-AUTHORIZATION*, no *.RUN.json, no *token* file under PILOT, the work folder or the r39 sandbox base
  guard_refusals    dispatch_guard_r32.check without a declaration refuses; GuardedProvider refuses without building; dry_exercise never live
  visibility        VISIBILITY-RESULT.json: every injected event visible everywhere it can reach; 0 model requests; ledger unchanged;
                    no bound fingerprint re-sent; contract breaches only where injected
  bounds            PROJECT-REQUEST-BOUNDS.json equals its recomputation; EP-27331 63.0 / 160; minimum 84
  resume_model      RESUME-INVOCATIONS-R39.json equals its recomputation from the bounds file
  probes            DRAWINGS-AI-PROBE-R39.json: off with the declared setting, live when true, 1(d) measured columns unchanged in both
                    trees; UNREAD-PAGES-PROBE-R39.json: scenarios A, B, C give the expected unread pages
  request_paths     REQUEST-PATHS-STATIC.json equals a fresh run of request_paths_r39.py
  gate              the bound gate is C_GE_B_ONLY (A-10), the plan v2 gate is refused, the report template states the change
  model_identity    MODEL-ID-EVIDENCE.json: the CLI file's sha256 and every finding re-located; the CLI was not executed
  response_ledger   M2-REVIEW-RESPONSE.md still hashes to 49b4ca01... (the append happens after the manifest)"""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r39")
PKG = PILOT / "review39"
H = WORK / "harness-r32"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
CUTOFF = "2026-10-04T09:00:00+00:00"
INPUTS = {
    "review38 manifest": (PILOT / "review38/evidence/EVIDENCE-MANIFEST.json", "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9"),
    "BINDING-MANIFEST-R38": (PILOT / "review38/BINDING-MANIFEST-R38.json", "4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d"),
    "review36 manifest": (PILOT / "review36/evidence/EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0"),
    "Verification 39 report": (MR / "reviews/M2-review-39/INDEPENDENT-VERIFICATION.md", "5bb967f278fd331047df3b8026432bc01ac4b678d4cc48286e50dbc6fba46598"),
    "Verification 39 findings": (MR / "reviews/M2-review-39/FINDINGS.json", "5976db3818000242ec32ef16323516ca29270e74027f7b10cef22fe3e2b8028a"),
    "Verification 39 package check": (MR / "reviews/M2-review-39/INDEPENDENT-PACKAGE-CHECK.json", "cd8ec9fdfe222013b2e1e60890e4a56417a9f23f337ca63ad21671b140c8d8d3"),
    "RUN-SET-PROPOSAL": (PILOT / "review34/RUN-SET-PROPOSAL.json", "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"),
    "TRUTH-R32": (PILOT / "review34/dry-run/TRUTH-R32.json", "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"),
    "reviewed-2 labels": (PILOT / "fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json", "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    "evaluator-offline-r32 manifest": (PILOT / "evaluator-offline-r32/evidence/EVIDENCE-MANIFEST.json", "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7"),
}
RESPONSE = (PILOT.parent / "M2-REVIEW-RESPONSE.md", "49b4ca01f4135418129f0b5a1d863f06ba9cf9879d4ed51f579d9bf81fc9ffc7")
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
sys.path.insert(0, str(H))


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(args, cwd=None):
    r = subprocess.run([PY, "-B", *args], cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"})
    return r


def check_inputs():
    got = {k: {"path": p.as_posix(), "sha256": sha(p), "expected": w, "equal": sha(p) == w} for k, (p, w) in INPUTS.items()}
    manifests = {}
    for pkg, n in (("review38", 128), ("review36", 135), ("declaration-r32", 56), ("evaluator-offline-r32", 25)):
        m = json.loads((PILOT / pkg / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
        bad = [k for k, v in m.items() if sha(PILOT / pkg / k) != v["sha256"]]
        manifests[pkg] = {"listed": len(m), "expected": n, "bad": bad, "ok": not bad and len(m) == n}
    return {"ok": all(v["equal"] for v in got.values()) and all(v["ok"] for v in manifests.values()), "inputs": got, "manifests": manifests}


def check_frozen_trees():
    after = WORK / "evidence" / "SNAPSHOT-AFTER.json"
    r = _run([str(WORK / "scripts" / "snapshot_r39.py"), str(after)])
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
                out[name] = {"compared": False, "why": "the orchestrator's own folder (updated by the orchestrator); recorded only",
                             "equal": t["digest"] == a[kind][name]["digest"]}
                continue
            eq = t["digest"] == a[kind][name]["digest"]
            entries = a[kind][name].get("entries")
            newer = sorted(k for k, v in entries.items() if v["mtime_utc"] > CUTOFF) if isinstance(entries, dict) else []
            out[name] = {"files": t["files"], "equal_to_before": eq, "newer_than_task_start": newer[:10], "newer_count": len(newer)}
            ok = ok and eq and not newer
    return {"ok": ok, "task_start_utc": CUTOFF, "before_taken_utc": b["taken_utc"], "after_taken_utc": a["taken_utc"], "trees": out,
            "repos_after": a["repos"], "ledger_after": a["ai_ledger"],
            "note": "SNAPSHOT-BEFORE was taken before packaging (after development); the task-start integrity check is in the audit log (09:00:34Z)"}


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
    import sqlite3
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
    work = {p.name: sha(p) for p in H.iterdir()}
    pkg = {p.name: sha(p) for p in (PKG / "scripts" / "harness-r32").iterdir()}
    freeze = {}
    for line in (WORK / "out" / "FREEZE-1.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, n = line.split(" ", 1)
            freeze[n.strip().lstrip("*")] = h
    table = json.loads((PKG / "evidence" / "HARNESS-FILES-R38-R39.json").read_text(encoding="utf-8"))["files"]
    r38 = {p.name: sha(p) for p in (PILOT / "review38" / "scripts" / "harness-r32").iterdir()}
    carried = {n: {"review38_sha256": r38[n], "review39_sha256": work[n], "equal": r38[n] == work[n]} for n, r in table.items() if r["status"] == "unchanged"}
    table_ok = all((r["r39_sha256"] == work.get(n)) and (r["review38_sha256"] == r38.get(n)) for n, r in table.items())
    copy_rec = json.loads((PKG / "evidence" / "COPY-RECORD.json").read_text(encoding="utf-8"))
    counts = {s: sum(1 for r in table.values() if r["status"] == s) for s in ("unchanged", "changed", "new", "removed")}
    return {"ok": work == pkg == freeze and table_ok and all(v["equal"] for v in carried.values()) and len(work) == 56 and copy_rec["all_equal"]
                  and counts["removed"] == 0,
            "files": len(work), "package_equals_work": work == pkg, "work_equals_freeze_1": work == freeze, "table_ok": table_ok,
            "review38_base_copy_equal": copy_rec["all_equal"], "carried_unchanged": carried, "counts": counts}


def check_binding():
    import preflight_r32 as PF
    b = PKG / "BINDING-MANIFEST-R39.json"
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
    expected = {f"{m}.xml" for m in summ["modules"]}
    return {"ok": summ["all_passed"] and summ["guard_refusals"] == 0 and total["failures"] == 0 and total["errors"] == 0 and total == summ["total"]
                  and set(junit) == expected and len(junit) == 22 and not any(guards.values()),
            "modules": len(junit), "total": total, "per_module": junit, "guard_refused": sum(guards.values()), "no_twin": summ.get("no_twin")}


def check_no_authorization():
    roots = [PILOT, WORK, pathlib.Path("C:/t/r2x/r39-sandbox")]
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
    return {"ok": v["all_visible"] and v["no_resend"] and v["model_requests"] == 0 and v["ai_ledger"]["unchanged"] and v["breaches_only_where_injected"]
                  and len(v["scenarios"]) == 17,
            "scenarios": {k: {"recorded_in": s["recorded_in"], "silent_places": s["silent_places"]} for k, s in v["scenarios"].items()},
            "model_requests": v["model_requests"], "ai_ledger": v["ai_ledger"], "contract_breaches": v["contract_breaches"]}


def check_bounds():
    import preflight_r32 as PF
    import project_bounds_r32 as PB
    import runner_r32 as RN
    b = json.loads((PKG / "PROJECT-REQUEST-BOUNDS.json").read_text(encoding="utf-8"))
    T = PF.build_truth()
    again = PB.compute(PF.load_run_set(PILOT / "review34/RUN-SET-PROPOSAL.json", T), T, RN.DRY_LANE_SWITCHES, window_limit=60, window_s=86400, elapsed_s=604800)
    keys = ("projects", "lanes", "compatible_limits", "per_document", "per_page_maximum", "version", "code_constants", "drawings_ai")
    diff = [k for k in keys if again[k] != b[k]]
    p = b["projects"]["EP-27331"]
    nums = (p["planning"]["all_lanes"], p["structural_maximum"]["all_lanes"], p["drawings_ai"]["if_enabled"]["structural_all_lanes"],
            b["compatible_limits"]["required_minimum"]["AI_MAX_CALLS_PER_PROJECT_PER_DAY"])
    return {"ok": not diff and nums == (63.0, 160, 170, 84), "differs_in": diff, "sha256": sha(PKG / "PROJECT-REQUEST-BOUNDS.json"),
            "EP-27331": {"planning": p["planning"], "structural_maximum": p["structural_maximum"], "drawings_ai_if_enabled": p["drawings_ai"]["if_enabled"],
                         "change_from_r38_model": p["change_from_r38_model"]},
            "required_minimum": b["compatible_limits"]["required_minimum"]}


def check_resume_model():
    tmp = WORK / "out" / "_resume_check.json"
    r = _run(["resume_invocations_r39.py", str(PKG / "PROJECT-REQUEST-BOUNDS.json"), str(tmp)], cwd=str(H))
    if r.returncode:
        return {"ok": False, "error": r.stderr[-800:]}
    a, b = json.loads(tmp.read_text(encoding="utf-8")), json.loads((PKG / "RESUME-INVOCATIONS-R39.json").read_text(encoding="utf-8"))
    tmp.unlink()
    return {"ok": a["table"] == b["table"] and a["results"] == b["results"], "table": b["table"]}


def check_probes():
    d = json.loads((PKG / "DRAWINGS-AI-PROBE-R39.json").read_text(encoding="utf-8"))
    u = json.loads((PKG / "UNREAD-PAGES-PROBE-R39.json").read_text(encoding="utf-8"))
    dok = all(s["declared_false_switches_off"] and s["true_goes_live"] and s["measured_unchanged"] and s["project_documents_flushed"] == []
              and s["feed_provider_asked"] == ["drawings_reply_match"] and s["feed_answer_applied"] == {"source": "ai", "status": "approved"}
              for s in d["summary"].values()) and set(d["summary"]) == {"baseline", "candidate"}
    up = {k: [(x["page"], x["kind"]) for x in v] for k, v in u["derived_unread_pages"].items()}
    uok = up == {"A": [("3", "application_reader_cap"), ("4", "application_reader_cap")],
                 "B": [("3", "application_document_limit"), ("4", "application_document_limit")],
                 "C": [(str(n), "application_reader_exception") for n in range(1, 5)]}
    return {"ok": dok and uok, "drawings": d["summary"], "unread": up}


def check_request_paths():
    tmp = WORK / "out" / "_rp_check.json"
    r = _run(["request_paths_r39.py", str(tmp)], cwd=str(H))
    if r.returncode:
        return {"ok": False, "error": r.stderr[-800:]}
    a, b = json.loads(tmp.read_text(encoding="utf-8")), json.loads((PKG / "REQUEST-PATHS-STATIC.json").read_text(encoding="utf-8"))
    tmp.unlink()
    reached = {lane: sorted({s["function"] for s in v["sites_reached"]}) for lane, v in b["lanes"].items() if "sites_reached" in v}
    return {"ok": a == b, "reached": reached}


def check_gate():
    import preflight_r32 as PF
    import score_bcr_r32 as S
    refused = []
    for bad in ("C_GE_B_AND_C_GE_R", "C_GE_R_ONLY"):
        try:
            S.refuse_r_in_eligibility(bad)
        except ValueError as exc:
            refused.append(str(exc)[:120])
    t = S.report_template({})
    lrc = (PKG / "LIVE-RUN-CONTRACT.md").read_text(encoding="utf-8")
    sc = (PKG / "SCORER-CHANGES.md").read_text(encoding="utf-8")
    cr = (PKG / "CHANGE-RECORD-R39.md").read_text(encoding="utf-8")
    stated = {"report_template": "CHANGED from plan v2" in t and "MANDATORY diagnostic" in t,
              "live_run_contract": "change from plan v2" in lrc and "mandatory diagnostic" in lrc,
              "scorer_changes": "CHANGE FROM PLAN V2" in sc, "change_record": "change from plan v2" in cr.lower()}
    ok = S.DECISION_COVERAGE_GATE == "C_GE_B_ONLY" and len(refused) == 2 and all(stated.values()) and PF.APPLICATION_ENV == {"DRAWINGS_AI_REVIEW_ENABLED": "false"}
    return {"ok": ok, "bound": S.DECISION_COVERAGE_GATE, "refused": refused, "stated_in": stated}


def check_model_identity():
    e = json.loads((PKG / "MODEL-ID-EVIDENCE.json").read_text(encoding="utf-8"))
    p = pathlib.Path(e["cli_file"])
    data = p.read_bytes()
    ok_file = hashlib.sha256(data).hexdigest() == e["sha256"] and len(data) == e["bytes"]
    relocated = {}
    for name, f in e["findings"].items():
        if f["offsets"] and f.get("window_2k_sha256"):
            i = f["offsets"][0]
            relocated[name] = hashlib.sha256(data[max(0, i - 1024): i + 1024]).hexdigest() == f["window_2k_sha256"]
    return {"ok": ok_file and all(relocated.values()) and e["executed"] is False and e["embedded_version"] == "2.1.263",
            "cli_sha256": e["sha256"], "relocated": relocated, "executed": e["executed"]}


def check_response():
    s = sha(RESPONSE[0])
    return {"ok": s == RESPONSE[1], "sha256": s, "expected_before_append": RESPONSE[1]}


def main(out):
    checks = {}
    for name, fn in (("inputs", check_inputs), ("frozen_trees", check_frozen_trees), ("repos", check_repos), ("ai_ledger", check_ledger),
                     ("harness", check_harness), ("binding", check_binding), ("tests", check_tests), ("no_authorization", check_no_authorization),
                     ("guard_refusals", check_guard_refusals), ("visibility", check_visibility), ("bounds", check_bounds),
                     ("resume_model", check_resume_model), ("probes", check_probes), ("request_paths", check_request_paths), ("gate", check_gate),
                     ("model_identity", check_model_identity), ("response_ledger", check_response)):
        try:
            checks[name] = fn()
        except Exception as exc:  # noqa: BLE001 -- a check that cannot run fails
            checks[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print(name, checks[name]["ok"], flush=True)
    res = {"kind": "ORCH-08C review39 package check", "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "package": PKG.as_posix(), "all_ok": all(c["ok"] for c in checks.values()), "checks": checks,
           "statement": "a self-check by the implementer; not an independent verification (Verification 40 follows); it authorizes nothing"}
    pathlib.Path(out).write_text(json.dumps(res, sort_keys=True, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": res["all_ok"]}))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
