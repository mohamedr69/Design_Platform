"""Task 38 Part B step 5: the NO-REQUEST part of the v3 dry preflight (declaration-r32-v3/scripts/preflight_r42.py, steps 1-7)
run against the RE-POINTED review43 harness (its scratch run copy) and the R43 trees. Run with PYTHONPATH=<run43 guard>.

Recorded substitutions against preflight_r42.py (every other line of steps 1-7 is the same code, and probes() / set_path() are
imported from a BYTE COPY of preflight_r42.py):
  P1 outputs: <run43>/preflight-out (never declaration-r32-v3/dry-run, which is written once and must not be touched)
  P2 harness: the run copy <run43>/scripts/harness-r32, checked byte-equal to PKG/review43/scripts/harness-r32 first
      (preflight_r42.harness_import checked review42's files against BINDING-MANIFEST-R42)
  P3 step 4 binding: a scratch PRE-BINDING manifest whose files section is the one BINDING-MANIFEST-R43-HARNESS.json will
      carry (minus the test / preflight evidence that does not exist yet) -- review43 harness, frozen-r13 and cand-r30n sources
  P4 step 6 lane sandboxes: C:/t/r2x/r42-sandbox/r43p-env-<lane> (not the existing r42d-env-<lane>)
  P5 steps 8-12 are NOT run: they drive the live runner, the dispatch guard and the scope command, and since the v3 run the
      v3 RUN file, OWNER-DISPATCH-AUTHORIZATION.json, the v3 ledger scope and the v3 run folder exist; driving the live paths
      against those real objects is outside a no-request check (and step 12 would call the scope 'create' command)
  P6 invariants: the AI ledger is compared before == after (the fixed 483 / 17 / 0 of 2026-10-05 is reported, not asserted:
      the v3 run added 1 entry and 1 scope); authorization-like files and the run folder are compared before == after
      (they exist since the v3 run) instead of 'absent'
  P7 step 4b added: preflight_r32.heads() (the runner's HEAD and clean check of frozen-r13 / cand-r30n)
  P8 in-memory only: isolation.allowed_under_forbidden.harness = the running harness (v3 binds the review42 folder)
The declaration probed is the frozen v3 declaration (the only one; v4 is not written), as in the review42 preflight."""
from __future__ import annotations

import copy, datetime, hashlib, json, os, pathlib, subprocess, sys

sys.dont_write_bytecode = True
os.environ["GIT_OPTIONAL_LOCKS"] = "0"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ.pop("R34_OWNER_DISPATCH_TOKEN", None)
HERE = pathlib.Path(__file__).resolve().parent            # <run43>/preflight (byte copies + this driver)
RUN = HERE.parent
sys.path.insert(0, str(HERE))
import r42common as C  # noqa: E402  (review43's re-pointed copy)
import build_declaration_r42 as BD  # noqa: E402
import preflight_r42 as P42  # noqa: E402  (byte copy: probes(), set_path(), _DEL, listing())

PKG_H = pathlib.Path(C.PILOT) / "review43" / "scripts" / "harness-r32"
RUN_H = RUN / "scripts" / "harness-r32"
OUT = RUN / "preflight-out"
PRE = OUT / "PRE-BINDING-R43.json"
SCR = RUN.parent
sys.path.insert(0, str(SCR))
import lib43 as L  # noqa: E402


def tree_fp(root):
    items = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            items.append(f"{os.path.relpath(p, root)}\t{L.sha_file(p)}")
    return hashlib.sha256("\n".join(items).encode()).hexdigest()


def invariants():
    return {"ai_ledger": C.ledger_counts(), "run_folder_fingerprint": tree_fp(C.RUN_FOLDER) if C.RUN_FOLDER.exists() else None,
            "harness_listing_sha256": hashlib.sha256(json.dumps(P42.listing(RUN_H), sort_keys=True).encode()).hexdigest(),
            "harness_pycache": [p.as_posix() for p in RUN_H.rglob("__pycache__")],
            "package_listing_sha256": hashlib.sha256(json.dumps(P42.listing(C.PACKAGE), sort_keys=True).encode()).hexdigest(),
            "forbidden_files": C.forbidden_files(), "token_env_present": C.TOKEN_ENV in os.environ}


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    OUT.mkdir(parents=True, exist_ok=False)
    # P2: the run copy must equal the package copy
    pk = {p.relative_to(PKG_H).as_posix(): L.sha_file(p) for p in sorted(PKG_H.rglob("*")) if p.is_file()}
    rc = {p.relative_to(RUN_H).as_posix(): L.sha_file(p) for p in sorted(RUN_H.rglob("*")) if p.is_file()}
    if pk != rc:
        raise SystemExit("PACKET MISMATCH: the run copy differs from PKG/review43/scripts/harness-r32")
    sys.path.insert(0, str(RUN_H))
    import preflight_r32 as PF  # noqa: E402
    import runner_r32 as RN  # noqa: E402
    assert pathlib.Path(PF.__file__).resolve().parent == RUN_H.resolve()
    # P3: the pre-binding
    m37 = L.load(L.M37)
    pre = {"name": "PRE-BINDING-R43 (task 38 preflight step 4 only; the files section BINDING-MANIFEST-R43-HARNESS.json carries, minus the test and preflight evidence)",
           "files": L.files_groups(m37)}
    C.write_json_once(PRE, pre)
    pre_sha = C.sha256_file(PRE)
    frozen, fsha = BD.frozen_bytes_checked()
    decl = json.loads(frozen.decode("utf-8"))
    run_path = C.PACKAGE / C.RUN_NAME
    before = invariants()
    res = {"name": "PREFLIGHT-R43 (task 38: steps 1-7 of the v3 dry preflight, no request) against the re-pointed review43 harness",
           "started_utc": started, "declaration": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(), "sha256": fsha},
           "harness_run_copy": RUN_H.as_posix(), "harness_package": PKG_H.as_posix(), "harness_files_equal": len(pk),
           "trees": {"baseline": RN.TREES["baseline"], "candidate": RN.TREES["candidate"]}, "heads_constant": dict(PF.HEADS),
           "pre_binding": {"path": PRE.as_posix(), "sha256": pre_sha}, "before": before, "checks": {}}
    ck = res["checks"]
    try:
        PF.validate_declaration(decl, C.PACKAGE / C.DECLARATION_NAME)
        ck["1_validate_declaration_as_written"] = {"result": "ACCEPTED (UNEXPECTED)"}
    except PF.Refused as exc:
        ck["1_validate_declaration_as_written"] = {"result": "REFUSED", "reason": str(exc), "expected": "REFUSED (placeholder digest)"}
    run_mem_bytes = BD.fill_owner_digest(frozen, C.DUMMY_DIGEST)
    mem = json.loads(run_mem_bytes.decode("utf-8"))
    # P8: the v3 declaration binds isolation.allowed_under_forbidden.harness = the review42 harness folder, and
    # validate_isolation requires it to be exactly the running harness (PF.HERE); in memory only, it names the run copy
    # (a v4 declaration would bind the review43 harness). Nothing else in the in-memory copy differs from v3 + dummy digest.
    v3_harness = mem["isolation"]["allowed_under_forbidden"]["harness"]
    mem["isolation"]["allowed_under_forbidden"]["harness"] = PF.HERE.as_posix()
    v = PF.validate_declaration(mem, run_path)
    ck["2_validate_declaration_in_memory_dummy_digest"] = {"result": "PASSED", "dummy_digest": "in memory only; never written",
                                                           "sha256_of_the_in_memory_copy_before_P8": C.sha256_bytes(run_mem_bytes),
                                                           "P8_isolation_harness": {"v3": v3_harness, "in_memory": PF.HERE.as_posix()}}
    rows = []
    for name, muts, expected in P42.probes(mem):
        m = copy.deepcopy(mem)
        for path, value in muts:
            P42.set_path(m, path, value)
        try:
            PF.validate_declaration(m, run_path)
            got, why = "ACCEPTED", None
        except PF.Refused as exc:
            got, why = "REFUSED", str(exc)
        except Exception as exc:  # noqa: BLE001
            got, why = f"ERROR {type(exc).__name__}", str(exc)
        rows.append({"probe": name, "expected": expected, "result": got, "as_expected": got == expected, "reason": why})
    ck["3_negative_probes"] = {"count": len(rows), "as_expected": sum(r["as_expected"] for r in rows),
                               "all_as_expected": all(r["as_expected"] for r in rows), "rows": rows}
    try:
        ck["4_verify_binding"] = {"result": "PASSED", **PF.verify_binding(PRE, pre_sha)}
    except PF.Refused as exc:
        ck["4_verify_binding"] = {"result": "REFUSED", "reason": str(exc)}
    try:
        ck["4b_heads"] = {"result": "PASSED", **PF.heads()}
    except PF.Refused as exc:
        ck["4b_heads"] = {"result": "REFUSED", "reason": str(exc)}
    truth = PF.build_truth()
    run_set = PF.load_run_set(str(C.RUN_SET), truth)
    try:
        ck["5_verify_bounds"] = {"result": "PASSED", **PF.verify_bounds(v, run_set, truth), "population_gate": PF.population(truth)["action"],
                                 "truth_sha256": hashlib.sha256(PF.truth_text(truth).encode("utf-8")).hexdigest(), "run_set_documents": len(run_set)}
    except PF.Refused as exc:
        ck["5_verify_bounds"] = {"result": "REFUSED", "reason": str(exc)}
    lane_dir = OUT / "lane-env"
    lane_dir.mkdir(parents=True, exist_ok=True)
    cfg = {"lane_switches": v["lane_switches"], "application_env": v["application_env"], "provider_env": v["provider_env"], "harness": str(RUN_H),
           "interpreter": v["interpreter"]}
    cfgp = lane_dir / "LANE-ENV-CFG.json"
    C.write_json_once(cfgp, cfg)
    lanes = {}
    for lane in ("B", "C", "R", "P"):
        root = C.SANDBOX_BASE / f"r43p-env-{lane}"                                   # P4
        env = RN.lane_env("live", root, lane, cfg)
        env.pop(C.TOKEN_ENV, None)
        env["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")                          # the run-copy guard in the child too
        tree = RN.TREES["baseline" if lane == "B" else "candidate"]
        r = subprocess.run([C.PY, "-B", str(HERE / "lane_env_check_r42.py"), lane, str(cfgp), str(lane_dir / f"LANE-ENV-{lane}.json")], cwd=tree, env=env,
                           capture_output=True, text=True)
        out = json.loads((lane_dir / f"LANE-ENV-{lane}.json").read_text(encoding="utf-8")) if (lane_dir / f"LANE-ENV-{lane}.json").exists() else {}
        lanes[lane] = {"returncode": r.returncode, "ok": out.get("ok"), "checks": {k: x.get("result") for k, x in (out.get("checks") or {}).items()},
                       "tree": tree, "app_module_file": out.get("app_module_file"), "stderr_tail": r.stderr[-800:] if r.returncode else None}
    ck["6_lane_environment_checks_offline"] = {"result": "PASSED" if all(x["ok"] for x in lanes.values()) else "FAILED", "lanes": lanes}
    try:
        ck["7_interpreter_cli_file_disk"] = {"interpreter": PF.verify_interpreter(v["interpreter"]), "cli_file": PF.verify_cli(v["model_identity"]),
                                             "free_disk": PF.verify_free_disk(v["disk_precondition"]), "result": "PASSED",
                                             "note": "the CLI file is read as bytes; `--version` is never run"}
    except PF.Refused as exc:
        ck["7_interpreter_cli_file_disk"] = {"result": "REFUSED", "reason": str(exc)}
    ck["8_to_12_not_run"] = {"result": "NOT RUN", "why": "substitution P5 (module docstring)"}
    after = invariants()
    res["after"] = after
    res["invariants"] = {
        "ai_ledger_before_equals_after": before["ai_ledger"] == after["ai_ledger"],
        "ai_ledger_counts": {k: after["ai_ledger"][k] for k in ("entries", "scopes", "limit_amendments")},
        "ai_ledger_equals_review42_expected_483_17_0": {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
        "run_folder_unchanged": before["run_folder_fingerprint"] == after["run_folder_fingerprint"],
        "harness_unchanged_no_pycache": before["harness_listing_sha256"] == after["harness_listing_sha256"] and not after["harness_pycache"],
        "declaration_package_unchanged": before["package_listing_sha256"] == after["package_listing_sha256"],
        "authorization_like_files_unchanged": before["forbidden_files"] == after["forbidden_files"],
        "no_token_in_the_environment": not before["token_env_present"] and not after["token_env_present"],
        "model_requests": 0}
    res["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    expect = {"1_validate_declaration_as_written": "REFUSED", "2_validate_declaration_in_memory_dummy_digest": "PASSED", "4_verify_binding": "PASSED",
              "4b_heads": "PASSED", "5_verify_bounds": "PASSED", "6_lane_environment_checks_offline": "PASSED", "7_interpreter_cli_file_disk": "PASSED"}
    res["ok"] = all(ck[k]["result"] == want for k, want in expect.items()) and ck["3_negative_probes"]["all_as_expected"] and \
        all(res["invariants"][k] for k in ("ai_ledger_before_equals_after", "run_folder_unchanged", "harness_unchanged_no_pycache",
                                           "declaration_package_unchanged", "authorization_like_files_unchanged", "no_token_in_the_environment"))
    sha = C.write_json_once(OUT / "PREFLIGHT-R43.json", res)
    print(json.dumps({"written": (OUT / "PREFLIGHT-R43.json").as_posix(), "sha256": sha, "ok": res["ok"], "invariants": res["invariants"],
                      "results": {k: x.get("result") for k, x in ck.items()}, "probes": f"{ck['3_negative_probes']['as_expected']}/{len(rows)} as expected",
                      "unexpected": [r["probe"] for r in rows if not r["as_expected"]]}, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
