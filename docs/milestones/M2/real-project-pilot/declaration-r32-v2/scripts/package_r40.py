"""ORCH-09 (R40DECL-IMPL): the package check and the evidence manifest of PILOT/declaration-r32-v2/.

Usage: package_r40.py check      -> evidence/PACKAGE-CHECK.json (refuses if it exists)
       package_r40.py manifest   -> evidence/EVIDENCE-MANIFEST.json, written LAST (refuses unless PACKAGE-CHECK is all_ok and
                                    the manifest does not exist); lists every package file but itself (path, bytes, sha256)
Read-only on everything else; the AI ledger is opened mode=ro only."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
import build_declaration_r40 as BD  # noqa: E402
import r40common as C  # noqa: E402

DOCS = ("RUNBOOK.md", "SCOPE-CREATION-COMMAND.md", "DECLARATION-SUMMARY.md", "BUDGET-DECISION-CARD.v4.md", "PREFLIGHT-REPORT.md", "DECLARATION-DIFF.md",
        "COMMANDS.md", "COMMANDS-AND-AUDIT-LOG.md")


def bound_refs(obj, path=""):
    """Every {'path': <file>, 'sha256': <64 hex>} object in the declaration (the bindings), with where it sits."""
    out = []
    if isinstance(obj, dict):
        if isinstance(obj.get("path"), str) and isinstance(obj.get("sha256"), str) and len(obj["sha256"]) == 64:
            out.append((path, obj["path"], obj["sha256"]))
        for k, v in obj.items():
            out += bound_refs(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += bound_refs(v, f"{path}[{i}]")
    return out


def check() -> int:
    target = C.PACKAGE / "evidence" / "PACKAGE-CHECK.json"
    if target.exists():
        raise SystemExit("refused: PACKAGE-CHECK.json is written once")
    C.harness_import_path()
    import preflight_r32 as PF  # noqa: E402
    ck = {}
    frozen, fsha = BD.frozen_bytes_checked()
    decl = json.loads(frozen.decode("utf-8"))
    ck["declaration"] = {"sha256": fsha, "equals_DECLARATION.sha256": True, "placeholder_once": frozen.count(json.dumps(C.TOKEN_PLACEHOLDER).encode()) == 1,
                         "canonical_lf": C.json_text(decl).encode() == frozen and b"\r" not in frozen}
    try:
        PF.validate_declaration(decl, C.PACKAGE / C.DECLARATION_NAME)
        refused = None
    except PF.Refused as exc:
        refused = str(exc)
    mem = json.loads(BD.fill_owner_digest(frozen, C.DUMMY_DIGEST))
    PF.validate_declaration(mem, C.PACKAGE / C.RUN_NAME)
    ck["contract4"] = {"as_written_refused": refused, "in_memory_dummy_passes": True, "integer_strings": BD.integer_string_problems(decl["provider_env"]) == []}
    refs = bound_refs(decl)
    bad = []
    for where, p, want in refs:
        q = pathlib.Path(p) if pathlib.Path(p).is_absolute() else C.PACKAGE / p
        if not q.is_file() or C.sha256_file(q) != want:
            bad.append({"where": where, "path": p})
    ck["declaration_bindings"] = {"references": len(refs), "mismatches": bad, "ok": not bad}
    pre = json.loads((C.PACKAGE / "dry-run" / "PREFLIGHT-RESULTS.json").read_text(encoding="utf-8"))
    dry = json.loads((C.PACKAGE / "dry-run" / "DRY-EXERCISE.json").read_text(encoding="utf-8"))
    tests = json.loads((C.PACKAGE / "tests" / "SUMMARY.json").read_text(encoding="utf-8"))
    diff = json.loads((C.PACKAGE / "DECLARATION-DIFF.json").read_text(encoding="utf-8"))
    ck["preflight"] = {"sha256": C.sha256_file(C.PACKAGE / "dry-run" / "PREFLIGHT-RESULTS.json"), "ok": pre["ok"], "invariants": pre["invariants"]}
    ck["dry_exercise"] = {"sha256": C.sha256_file(C.PACKAGE / "dry-run" / "DRY-EXERCISE.json"), "ok": dry["ok"], "model_requests_total": dry["model_requests_total"],
                          "ai_ledger_unchanged": dry["ai_ledger_unchanged_483_17_0"],
                          "loops": {k: v["invocations"] for k, v in dry["deferral_loops"].items()}}
    ck["tests"] = {k: tests[k] for k in ("tests", "failures", "errors", "skipped", "guard_refused", "guard_network_refused")}
    ck["tests"]["ok"] = tests["tests"] > 0 and not (tests["failures"] or tests["errors"] or tests["skipped"] or tests["guard_refused"])
    ck["diff"] = {"corrected_sha256": diff["corrected"]["sha256"], "superseded_sha256": diff["superseded"]["sha256"],
                  "ok": diff["corrected"]["sha256"] == fsha and diff["superseded"]["sha256"] == C.SUPERSEDED_SHA}
    copies = BD.package_copies()
    ck["r40_04_proof_and_work_records"] = {"ok": True, "files": {k: v["sha256"] for g in copies.values() for k, v in g.items()}}
    led = C.ledger_state()
    ck["ai_ledger"] = {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")} | {
        "ok": (led["entries"], led["scopes"], led["limit_amendments"]) == (483, 17, 0) and C.SCOPE not in led["scope_names"], "declared_scope_exists": C.SCOPE in led["scope_names"]}
    ck["run_folder_absent"] = not C.RUN_FOLDER.exists()
    hits = C.forbidden_files()
    ck["no_authorization_run_or_token_file"] = {"roots": ["PILOT", "MR", "C:/t", "the scratchpad"], "hits": hits, "ok": not hits}
    ck["trees"] = {name: C.git_state(repo) | {"expected": head} for name, (repo, head) in (("candidate", C.CANDIDATE), ("baseline", C.BASELINE))}
    ck["trees"]["ok"] = all(v["head"] == v["expected"] and v["clean"] for k, v in ck["trees"].items() if k != "ok")
    ck["no_pycache"] = {"package": [p.as_posix() for p in C.PACKAGE.rglob("__pycache__")], "harness": [p.as_posix() for p in C.HARNESS.rglob("__pycache__")]}
    ck["no_pycache"]["ok"] = not ck["no_pycache"]["package"] and not ck["no_pycache"]["harness"]
    pkg_files = [p for p in C.PACKAGE.rglob("*") if p.is_file()]
    ck["dummy_digest_absent"] = all(C.DUMMY_DIGEST.encode() not in p.read_bytes() for p in pkg_files)
    gate_docs = {d: (C.PACKAGE / d).read_text(encoding="utf-8") for d in DOCS if (C.PACKAGE / d).exists()}
    ck["documents"] = {"present": sorted(gate_docs), "missing": [d for d in DOCS if d not in gate_docs],
                       "state_gate_change_from_plan_v2": {d: ("change from plan v2" in t.lower() or "changed from plan v2" in t.lower()) for d, t in gate_docs.items()},
                       "never_call_the_gate_unchanged": {d: not any(("unchanged gate" in ln.lower() and "not an unchanged gate" not in ln.lower()
                                                                     and "never an unchanged gate" not in ln.lower() and "not unchanged" not in ln.lower())
                                                                    for ln in t.splitlines()) for d, t in gate_docs.items()}}
    ck["documents"]["ok"] = not ck["documents"]["missing"] and all(ck["documents"]["state_gate_change_from_plan_v2"].values()) and \
        all(ck["documents"]["never_call_the_gate_unchanged"].values())
    fi = C.PACKAGE / "evidence" / "FROZEN-INPUTS-END.json"
    r = subprocess.run([C.PY, "-B", str(pathlib.Path(__file__).parent / "check_frozen_inputs_r40.py"), str(fi)], capture_output=True, text=True, encoding="utf-8")
    ck["frozen_inputs_end"] = {"returncode": r.returncode, "verdict": json.loads(fi.read_text(encoding="utf-8"))["verdict"], "sha256": C.sha256_file(fi)}
    sb = json.loads((C.PACKAGE / "evidence" / "SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    sa = json.loads((C.PACKAGE / "evidence" / "SNAPSHOT-AFTER.json").read_text(encoding="utf-8"))
    hashed = {k: sb["hashed_trees"][k]["digest"] == sa["hashed_trees"][k]["digest"] for k in sb["hashed_trees"]}
    listed = {k: sb["listed_trees"][k]["digest"] == sa["listed_trees"][k]["digest"] for k in sb["listed_trees"]}
    ck["snapshots"] = {"before_taken_utc": sb["taken_utc"], "after_taken_utc": sa["taken_utc"], "hashed_trees_equal": hashed, "listed_trees_equal": listed,
                       "listed_note": "the orchestrator folder (MR-orchestrator) is append-only and updated by the orchestrator; a listed difference there is not a change by this task",
                       "ai_ledger_before_after": [sb["ai_ledger"], sa["ai_ledger"]], "repos_after": sa["repos"], "forbidden_hits_after": sa["forbidden_files"]["hits"]}
    ck["snapshots"]["ok"] = all(hashed.values()) and all(v for k, v in listed.items() if k != "MR-orchestrator") and sb["ai_ledger"] == sa["ai_ledger"] \
        and not sa["forbidden_files"]["hits"]
    resp = C.RESPONSE_LEDGER.read_bytes()
    ck["response_ledger_before_append"] = {"sha256": hashlib.sha256(resp).hexdigest(), "bytes": len(resp),
                                           "ok": (hashlib.sha256(resp).hexdigest(), len(resp)) == C.RESPONSE_BEFORE}
    parts = [ck["declaration"]["placeholder_once"], ck["declaration"]["canonical_lf"], ck["contract4"]["as_written_refused"] is not None,
             ck["contract4"]["integer_strings"], ck["declaration_bindings"]["ok"], ck["preflight"]["ok"], ck["dry_exercise"]["ok"], ck["tests"]["ok"],
             ck["diff"]["ok"], ck["ai_ledger"]["ok"], ck["run_folder_absent"], ck["no_authorization_run_or_token_file"]["ok"], ck["trees"]["ok"],
             ck["no_pycache"]["ok"], ck["dummy_digest_absent"], ck["documents"]["ok"], ck["frozen_inputs_end"]["verdict"] == "PACKET MATCH",
             ck["snapshots"]["ok"], ck["response_ledger_before_append"]["ok"]]
    out = {"name": "PACKAGE-CHECK (ORCH-09, declaration-r32-v2)", "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "checks": ck, "all_ok": all(parts)}
    sha = C.write_json_once(target, out)
    print(json.dumps({"sha256": sha, "all_ok": out["all_ok"], "parts": parts}, indent=1))
    return 0 if out["all_ok"] else 1


def manifest() -> int:
    out = C.PACKAGE / "evidence" / "EVIDENCE-MANIFEST.json"
    if out.exists():
        raise SystemExit("refused: the evidence manifest is written once")
    chk = json.loads((C.PACKAGE / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not chk["all_ok"]:
        raise SystemExit("refused: PACKAGE-CHECK.json is not all_ok")
    files = {p.relative_to(C.PACKAGE).as_posix(): {"bytes": p.stat().st_size, "sha256": C.sha256_file(p)}
             for p in sorted(C.PACKAGE.rglob("*")) if p.is_file() and p != out}
    fsha = C.sha256_file(C.PACKAGE / C.DECLARATION_NAME)
    man = {"package": "PILOT/declaration-r32-v2 (ORCH-09: the corrected fresh-validation declaration, runbook and scope-creation command)",
           "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "file_count": len(files),
           "declaration_sha256": fsha, "binding_manifest_sha256": C.BINDING_SHA, "review39_manifest_sha256": C.REVIEW39_MANIFEST_SHA,
           "superseded_declaration_sha256": C.SUPERSEDED_SHA, "package_check_sha256": C.sha256_file(C.PACKAGE / "evidence" / "PACKAGE-CHECK.json"),
           "ai_ledger": {k: chk["checks"]["ai_ledger"][k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")},
           "statuses": {"declaration": "FROZEN, NOT AUTHORIZED; pending Verification 41 and the owner's decisions",
                        "decision_coverage_gate": "C >= B only, a change from plan v2 (A-10); C >= R a mandatory diagnostic",
                        "model_identity": "served-model identity UNRESOLVED; runtime check fail-closed (two stated limits); the owner's probe not run",
                        "live_run_authorization_and_budget": "none: no scope, token, authorization file, RUN file, budget or dispatch",
                        "reference_set": "r32-labels-reviewed-2 (89c60e9d...b9a6): reference set independently AI-reviewed (Claude agents), not human-signed",
                        "M2": "CHANGES STILL REQUIRED", "M3": "not started"},
           "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed", "files": files}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    sha = C.write_once(out, text)
    print(json.dumps({"sha256": sha, "files": len(files)}))
    return 0


if __name__ == "__main__":
    sys.exit(check() if sys.argv[1] == "check" else manifest() if sys.argv[1] == "manifest" else 2)
