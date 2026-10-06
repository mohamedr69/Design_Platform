"""ORCH-10 (R42PORT-IMPL): the package checks and the evidence manifests of PILOT/review42/ and PILOT/declaration-r32-v3/.

Usage: package_r42.py check review42 | check v3       -> <package>/evidence/PACKAGE-CHECK.json (refuses if it exists)
       package_r42.py manifest review42 | manifest v3 -> <package>/evidence/EVIDENCE-MANIFEST.json, written LAST (refuses unless
                                                         PACKAGE-CHECK is all_ok and the manifest does not exist); lists every
                                                         package file but itself (path, bytes, sha256)
Read-only on everything else; the AI ledger is opened mode=ro only; files are hashed through the extended-length prefix."""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

STATUSES = {"correction_readiness": "delivered for Independent Verification 42 (ORCH-10V); not self-approved",
            "accuracy": "none: no prediction exists; every figure is an estimate, a bound or a dry-run exercise",
            "label_truth": "r32-labels-reviewed-2 (89c60e9d...b9a6): reference set independently AI-reviewed (Claude agents), not human-signed",
            "permissions_and_budget": "eligibility only (A-06): no scope, token, authorization file, RUN file, budget or dispatch exists or is authorized",
            "M2": "CHANGES STILL REQUIRED", "M3": "not started"}


def common(pkg: pathlib.Path) -> dict:
    ck = {}
    led = C.ledger_state()
    ck["ai_ledger"] = {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")} | {
        "ok": (led["entries"], led["scopes"], led["limit_amendments"]) == (483, 17, 0) and C.SCOPE not in led["scope_names"]}
    ck["run_folder_absent"] = not C.RUN_FOLDER.exists()
    hits = C.forbidden_files((C.PILOT, C.MR, pathlib.Path("C:/t")))
    ck["no_authorization_run_or_token_file"] = {"hits": hits, "ok": not hits}
    ck["trees"] = {name: C.git_state(repo) | {"expected": head} for name, (repo, head) in (("candidate", C.CANDIDATE), ("baseline", C.BASELINE))}
    ck["trees"]["ok"] = all(v["head"] == v["expected"] and v["clean"] for k, v in ck["trees"].items() if k != "ok")
    ck["no_pycache"] = {"package": [p.as_posix() for p in pkg.rglob("__pycache__")], "harness": [p.as_posix() for p in C.HARNESS42.rglob("__pycache__")]}
    ck["no_pycache"]["ok"] = not ck["no_pycache"]["package"] and not ck["no_pycache"]["harness"]
    files = [p for p in pkg.rglob("*") if p.is_file()]
    ck["dummy_digest_absent"] = all(C.DUMMY_DIGEST.encode() not in p.read_bytes() for p in files)
    ck["desktop_paths_in_package"] = {"files_naming_it": sorted(p.relative_to(pkg).as_posix() for p in files
                                                                if p.suffix in (".py", ".md", ".json") and C.DESKTOP_EP.encode() in p.read_bytes())}
    lens = sorted(((len(p.as_posix()), p.as_posix()) for p in files), reverse=True)
    ck["path_lengths"] = {"max": lens[0][0] if lens else 0, "longest": lens[0][1] if lens else None, "ok": not lens or lens[0][0] < 260}
    ck["frozen_v2_and_review39"] = {"v2": C.manifest_check(C.V2), "review39": C.manifest_check(C.REVIEW39)}
    ck["frozen_v2_and_review39"]["ok"] = all(not v["differ"] and v["unlisted"] == ["evidence/EVIDENCE-MANIFEST.json"]
                                             for v in ck["frozen_v2_and_review39"].values() if isinstance(v, dict))
    ck["policy"] = {n: C.sha256_file(C.MR / n) == w for n, w in C.POLICY.items()}
    ck["r40_work_records"] = {p: C.sha256_file(p) == w for p, w in C.R40_WORK_RECORDS.items()}
    ck["policy_and_records_ok"] = all(ck["policy"].values()) and all(ck["r40_work_records"].values())
    return ck


def check_review42() -> dict:
    pkg = C.REVIEW42
    ck = common(pkg)
    man = json.loads(C.BINDING42.read_text(encoding="utf-8"))
    sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    vb = PF.verify_binding(C.BINDING42, C.sha256_file(C.BINDING42))
    ck["binding"] = {"sha256": vb["sha256"], "files_verified": vb["files_verified"], "r39_rehash": {k: man["r39_rehash"][k] for k in ("equal", "differ", "missing")},
                     "ok": not man["r39_rehash"]["differ"] and not man["r39_rehash"]["missing"]}
    work = {p.name: C.sha256_file(p) for p in C.WORK_HARNESS.glob("*.py")}
    pk = {p.name: C.sha256_file(p) for p in C.HARNESS42.glob("*.py")}
    ck["harness_copy"] = {"package_files": len(pk), "equal_to_work_copy": work == pk, "bound": set(man["files"]["harness_r42_package"]) ==
                          {(C.HARNESS42 / n).as_posix() for n in pk}}
    ck["harness_copy"]["ok"] = ck["harness_copy"]["equal_to_work_copy"] and ck["harness_copy"]["bound"]
    tests = json.loads((pkg / "tests/SUMMARY.json").read_text(encoding="utf-8"))
    ck["tests"] = {"total": tests["total"], "all_passed": tests["all_passed"], "guard_refusals": tests["guard_refusals"], "tree": tests["tree"],
                   "ok": tests["all_passed"] and tests["guard_refusals"] == 0 and tests["tree"] == C.HARNESS42.as_posix() and tests["total"]["skipped"] == 0}
    outs = json.loads((pkg / "evidence/OUTPUTS-R42.json").read_text(encoding="utf-8"))
    ck["outputs"] = {"ok": outs["ok"], "bounds_differs_only_in_run_set_path": outs["bounds"]["differs_only_in_run_set_path"],
                     "resume_invocations_byte_identical": outs["resume_invocations"]["byte_identical_to_review39"],
                     "request_paths_every_lane_installs_first": outs["request_paths"]["summary"]["every_lane_installs_before_its_application_entry"]}
    demos = json.loads((pkg / "evidence/demos/DEMOS-R42.json").read_text(encoding="utf-8"))
    ck["demos"] = {"ok": demos["ok"], "demos": {k: v["ok"] for k, v in demos["demos"].items()}, "ledger_unchanged": demos["ledger_unchanged"],
                   "authorization_files_written": demos["authorization_files_written"], "harness": demos["harness"]}
    ck["demos"]["ok"] = ck["demos"]["ok"] and demos["harness"] == C.HARNESS42.as_posix()
    docs = ("CHANGE-RECORD-R42.md", "LIVE-RUN-CONTRACT.md", "REQUEST-PATHS.md", "COMMANDS.md", "COMMANDS-AND-AUDIT-LOG.md")
    ck["documents"] = {"present": [d for d in docs if (pkg / d).exists()], "missing": [d for d in docs if not (pkg / d).exists()]}
    ck["documents"]["ok"] = not ck["documents"]["missing"]
    ck["contract_v5_carries_v4_sections"] = json.loads((pkg / "evidence/CONTRACT-V5-RECORD.json").read_text(encoding="utf-8"))
    sb = json.loads((pkg / "evidence/SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    sa = json.loads((pkg / "evidence/SNAPSHOT-AFTER.json").read_text(encoding="utf-8"))
    ck["snapshots"] = snapshots(sb, sa)
    return ck


def snapshots(sb, sa) -> dict:
    hashed = {k: sb["hashed_trees"][k]["digest"] == sa["hashed_trees"][k]["digest"] for k in sb["hashed_trees"]}
    listed = {k: sb["listed_trees"][k]["digest"] == sa["listed_trees"][k]["digest"] for k in sb["listed_trees"]}
    out = {"before_taken_utc": sb["taken_utc"], "after_taken_utc": sa["taken_utc"], "hashed_trees_equal": hashed, "listed_trees_equal": listed,
           "listed_note": "the orchestrator folder (MR-orchestrator) is append-only and updated by the orchestrator; a listed difference there is not a change by this task",
           "ai_ledger_before_after": [sb["ai_ledger"], sa["ai_ledger"]], "repos_after": sa["repos"], "forbidden_hits_after": sa["forbidden_files"]["hits"],
           "response_ledger_before_after": [sb["response_ledger"], sa["response_ledger"]]}
    out["ok"] = all(hashed.values()) and all(v for k, v in listed.items() if k != "MR-orchestrator") and sb["ai_ledger"] == sa["ai_ledger"] \
        and not sa["forbidden_files"]["hits"]
    return out


def check_v3() -> dict:
    pkg = C.PACKAGE
    ck = common(pkg)
    import build_declaration_r42 as BD
    sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    frozen, fsha = BD.frozen_bytes_checked()
    decl = json.loads(frozen.decode("utf-8"))
    ck["declaration"] = {"sha256": fsha, "placeholder_once": frozen.count(json.dumps(C.TOKEN_PLACEHOLDER).encode()) == 1,
                         "canonical_lf": C.json_text(decl).encode() == frozen and b"\r" not in frozen, "desktop_free": C.DESKTOP_EP.encode() not in frozen}
    try:
        PF.validate_declaration(decl, pkg / C.DECLARATION_NAME)
        refused = None
    except PF.Refused as exc:
        refused = str(exc)
    PF.validate_declaration(json.loads(BD.fill_owner_digest(frozen, C.DUMMY_DIGEST)), pkg / C.RUN_NAME)
    ck["contract5"] = {"as_written_refused": refused, "in_memory_dummy_passes": True}
    nodes = BD.bound_nodes(decl)
    bad = [{"at": jp, "path": p} for jp, p, s in nodes if C.sha256_file(p) != s]
    ck["declaration_bindings"] = {"references": len(nodes), "mismatches": bad, "ok": not bad}
    pre = json.loads((pkg / "dry-run/PREFLIGHT-RESULTS.json").read_text(encoding="utf-8"))
    dry = json.loads((pkg / "dry-run/DRY-EXERCISE.json").read_text(encoding="utf-8"))
    tests = json.loads((pkg / "tests/SUMMARY.json").read_text(encoding="utf-8"))
    diff = json.loads((pkg / "DECLARATION-DIFF.json").read_text(encoding="utf-8"))
    ck["preflight"] = {"sha256": C.sha256_file(pkg / "dry-run/PREFLIGHT-RESULTS.json"), "ok": pre["ok"], "invariants": pre["invariants"],
                       "probes": f"{sum(r['as_expected'] for r in pre['checks']['3_negative_probes']['rows'])}/{pre['checks']['3_negative_probes']['count']}"}
    ck["dry_exercise"] = {"sha256": C.sha256_file(pkg / "dry-run/DRY-EXERCISE.json"), "ok": dry["ok"], "model_requests_total": dry["model_requests_total"],
                          "single_run_state": dry["single"]["report"]["run_state"], "split_runs": len(dry["split"]["runs"]),
                          "loops": {k: v["invocations"] for k, v in dry["deferral_loops"].items()},
                          "cross_project_invocations": dry["cross_project_drill"]["loop"]["invocations"], "cli_case_ok": dry["cli_version_case"]["ok"]}
    ck["tests"] = {k: tests[k] for k in ("tests", "failures", "errors", "skipped", "guard_refusals")}
    ck["tests"]["ok"] = tests["tests"] > 0 and not (tests["failures"] or tests["errors"] or tests["skipped"] or tests["guard_refusals"])
    ck["diff"] = {"v3_sha256": diff["v3"]["sha256"], "v2_sha256": diff["v2"]["sha256"], "protected_all_ok": diff["protected_all_ok"],
                  "ok": diff["v3"]["sha256"] == fsha and diff["v2"]["sha256"] == C.V2_SHA and diff["ok"]}
    docs = ("RUNBOOK.md", "SCOPE-CREATION-COMMAND.md", "DECLARATION-SUMMARY.md", "BUDGET-DECISION-CARD.v5.md", "PREFLIGHT-REPORT.md", "DECLARATION-DIFF.md",
            "COMMANDS.md", "COMMANDS-AND-AUDIT-LOG.md", "IMPLEMENTATION-REPORT.md")
    texts = {d: (pkg / d).read_text(encoding="utf-8") for d in docs if (pkg / d).exists()}
    ck["documents"] = {"present": sorted(texts), "missing": [d for d in docs if d not in texts],
                       "gate_change_from_plan_v2_stated": {d: "change from plan v2" in t.lower() for d, t in texts.items()
                                                           if d in ("DECLARATION-SUMMARY.md", "BUDGET-DECISION-CARD.v5.md", "RUNBOOK.md")}}
    ck["documents"]["ok"] = not ck["documents"]["missing"] and all(ck["documents"]["gate_change_from_plan_v2_stated"].values())
    sb = json.loads((pkg / "evidence/SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    sa = json.loads((pkg / "evidence/SNAPSHOT-AFTER.json").read_text(encoding="utf-8"))
    ck["snapshots"] = snapshots(sb, sa)
    resp = C.RESPONSE_LEDGER.read_bytes()
    ck["response_ledger_before_append"] = {"sha256": C.sha256_bytes(resp), "bytes": len(resp), "ok": (C.sha256_bytes(resp), len(resp)) == C.RESPONSE_BEFORE}
    ck["review42_manifest"] = {"sha256": C.sha256_file(C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json"),
                               "bound_by_declaration": decl["harness"]["package_manifest"]["sha256"] == C.sha256_file(C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json")}
    ck["review42_manifest"]["recheck"] = C.manifest_check(C.REVIEW42)
    ck["review42_manifest"]["ok"] = ck["review42_manifest"]["bound_by_declaration"] and not ck["review42_manifest"]["recheck"]["differ"] \
        and ck["review42_manifest"]["recheck"]["unlisted"] == ["evidence/EVIDENCE-MANIFEST.json"]
    return ck


def check(which) -> int:
    pkg = C.REVIEW42 if which == "review42" else C.PACKAGE
    target = pkg / "evidence" / "PACKAGE-CHECK.json"
    if target.exists():
        raise SystemExit("refused: PACKAGE-CHECK.json is written once")
    ck = check_review42() if which == "review42" else check_v3()
    oks = {k: (v.get("ok") if isinstance(v, dict) else v) for k, v in ck.items() if (isinstance(v, dict) and "ok" in v) or isinstance(v, bool)}
    out = {"name": f"PACKAGE-CHECK (ORCH-10, {pkg.name})", "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "checks": ck, "parts": oks, "all_ok": all(bool(x) for x in oks.values()),
           "note": "desktop_paths_in_package lists package files that NAME the absent Desktop installation (historical records and re-pointing code); none binds it"}
    sha = C.write_json_once(target, out)
    print(json.dumps({"sha256": sha, "all_ok": out["all_ok"], "parts": oks, "desktop_named_in": ck["desktop_paths_in_package"]["files_naming_it"]}, indent=1))
    return 0 if out["all_ok"] else 1


def manifest(which) -> int:
    pkg = C.REVIEW42 if which == "review42" else C.PACKAGE
    out = pkg / "evidence" / "EVIDENCE-MANIFEST.json"
    if out.exists():
        raise SystemExit("refused: the evidence manifest is written once")
    chk = json.loads((pkg / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not chk["all_ok"]:
        raise SystemExit("refused: PACKAGE-CHECK.json is not all_ok")
    files = {p.relative_to(pkg).as_posix(): {"bytes": p.stat().st_size, "sha256": C.sha256_file(p)} for p in sorted(pkg.rglob("*")) if p.is_file() and p != out}
    led = chk["checks"]["ai_ledger"]
    man = {"package": (f"PILOT/{pkg.name} (ORCH-10: " + ("the r32 harness corrected for portability and safety in the merged installation)"
                                                       if which == "review42" else "the corrected fresh-validation declaration v3, runbook and scope-creation command)")),
           "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "file_count": len(files),
           "binding_manifest_sha256": C.sha256_file(C.BINDING42), "package_check_sha256": C.sha256_file(pkg / "evidence" / "PACKAGE-CHECK.json"),
           "ai_ledger": {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")}, "statuses": dict(STATUSES),
           "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed", "files": files}
    if which == "v3":
        man["declaration_sha256"] = C.sha256_file(pkg / C.DECLARATION_NAME)
        man["review42_manifest_sha256"] = C.sha256_file(C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json")
        man["supersedes"] = {"declaration": C.V2_SHA, "manifest": C.V2_MANIFEST_SHA}
        man["statuses"]["declaration"] = "FROZEN, NOT AUTHORIZED; pending Verification 42 and the owner's decision card"
    sha = C.write_once(out, json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"sha256": sha, "files": len(files)}))
    return 0


if __name__ == "__main__":
    cmd, which = sys.argv[1], sys.argv[2]
    assert which in ("review42", "v3")
    sys.exit(check(which) if cmd == "check" else manifest(which) if cmd == "manifest" else 2)
