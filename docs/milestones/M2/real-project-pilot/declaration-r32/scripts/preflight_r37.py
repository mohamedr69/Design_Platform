"""ORCH-07 (R37DECL-IMPL): the dry preflight of the frozen declaration against the bound harness (no dispatch).

Usage: preflight_r37.py <out json (absolute, new)>
  1. preflight_r32.validate_declaration on the declaration as written (the placeholder digest must be refused) and
     preflight_r32.load_declaration (the runner's own entry, with the binding and run-set hashes);
  2. validate_declaration on an IN-MEMORY copy whose owner_token_sha256 is a syntactically valid dummy digest (never
     written to disk): every other key of the contract must pass;
  3. preflight_r32.verify_binding(BINDING-MANIFEST-R36, 5a1a6aad...): every bound file re-hashed;
  4. runner_r32 run --mode live from the bound copy (C:/t/iso/work/r2x/r36/harness-r32), WITHOUT any authorization file
     and WITHOUT a token: it must refuse before creating any folder; and once more in-process with the in-memory
     dummy-digest copy (patched loader, nothing written): it must refuse at the ledger-scope check (no scope exists);
  5. dispatch_guard_r32.check (preview) and GuardedProvider without an authorization: refused, no provider built;
  6. the AI ledger read-only before and after (483 / 17 / 0), the run folder absent before and after, no authorization
     file anywhere searched, the bound harness folder unchanged.
Imports the bound harness copy with bytecode writing off, after checking every imported module against
BINDING-MANIFEST-R36 (harness_r36). GIT_OPTIONAL_LOCKS=0 for the HEAD checks."""
from __future__ import annotations

import copy
import dataclasses
import datetime
import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
os.environ["GIT_OPTIONAL_LOCKS"] = "0"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import build_declaration_r37 as BD  # noqa: E402
import r37common as C  # noqa: E402

BINDING_SHA = C.FROZEN["binding_manifest_r36"][1]
IMPORTED = ("preflight_r32.py", "dispatch_guard_r32.py", "runner_r32.py", "inputs_r32.py", "labels_adapter_r32.py", "score_bcr_r32.py",
            "concentration_r32.py", "lane_judge_r32.py", "literal_compare_r32.py", "allowance_r32.py", "sandbox_ingest_r32.py",
            "state_check.py", "stop_rules.py")
TOKEN_ENV = "R34_OWNER_DISPATCH_TOKEN"


def listing(root: pathlib.Path) -> dict:
    out = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = C.sha256_file(p)
    return out


def top_listing(root: pathlib.Path) -> list:
    return sorted(p.name for p in root.iterdir()) if root.exists() else []


def verify_imports() -> dict:
    man = json.loads(C.BINDING.read_text(encoding="utf-8"))
    bound = man["files"]["harness_r36"]
    out = {}
    for m in IMPORTED:
        p = (C.HARNESS_BOUND / m).as_posix()
        if C.sha256_file(p) != bound[p]:
            raise C.PacketMismatch(f"PACKET MISMATCH: {p}")
        out[m] = bound[p]
    return out


@dataclasses.dataclass
class _Resp:
    data: object = None
    model: str = ""
    error: str | None = None
    error_detail: str | None = None


def main(target: pathlib.Path) -> int:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    C.check_frozen()
    decl_path = C.PACKAGE / C.DECLARATION_NAME
    sha = C.sha256_file(decl_path)
    recorded = (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]
    if sha != recorded:
        raise C.PacketMismatch(f"PACKET MISMATCH: declaration {sha} != DECLARATION.sha256 {recorded}")
    imports = verify_imports()
    sys.path.insert(0, str(C.HARNESS_BOUND))
    import dispatch_guard_r32 as DG  # noqa: E402
    import preflight_r32 as PF  # noqa: E402

    run_folder = C.LIVE_SANDBOX_BASE / BD.STAMP
    pinned = DG.pinned_path(decl_path)
    search_roots = [C.PILOT, C.MR, pathlib.Path("C:/t/r2x"), C.WORK, C.SCRATCH]
    before = {"ai_ledger": {k: v for k, v in C.ledger_state().items() if k != "scope_names"}, "run_folder_exists": run_folder.exists(),
              "r34_sandbox_top_listing": top_listing(C.LIVE_SANDBOX_BASE), "harness_bound_listing": listing(C.HARNESS_BOUND),
              "package_listing": listing(C.PACKAGE), "pinned_authorization_exists": pinned.exists(),
              "dispatch_authorization_files": C.authorization_files(search_roots), "token_env_present": TOKEN_ENV in os.environ}
    decl = json.loads(decl_path.read_text(encoding="utf-8"))
    res = {"name": "PREFLIGHT-RESULTS (ORCH-07 dry preflight)", "started_utc": started, "declaration": {"path": decl_path.as_posix(), "sha256": sha,
           "DECLARATION.sha256": recorded}, "harness_copy": C.HARNESS_BOUND.as_posix(), "imported_modules_sha256": imports,
           "binding_manifest": {"path": C.BINDING.as_posix(), "sha256": BINDING_SHA}, "before": before, "checks": {}}
    ck = res["checks"]

    # 1. the declaration as written: the placeholder is refused
    try:
        PF.validate_declaration(decl, decl_path)
        ck["validate_declaration_as_written"] = {"result": "ACCEPTED (unexpected)"}
    except PF.Refused as exc:
        ck["validate_declaration_as_written"] = {"result": "REFUSED", "reason": str(exc),
                                                 "expected": "the placeholder owner_token_sha256 is not a 64-hex digest; it is refused until the owner names the digest"}
    try:
        PF.load_declaration(decl_path, sha, binding_sha=BINDING_SHA, run_set_sha=C.FROZEN["run_set_proposal"][1])
        ck["load_declaration_as_written"] = {"result": "ACCEPTED (unexpected)"}
    except PF.Refused as exc:
        ck["load_declaration_as_written"] = {"result": "REFUSED", "reason": str(exc),
                                             "passed_before_refusal": ["file exists and hashes to its sha256", "binding_manifest_sha256 and run_set_sha256 equal the files given",
                                                                       "every required key present", "run.folder == C:/t/r2x/r34-sandbox/<stamp>", "authorization.path == the pinned path"]}

    # 2. an in-memory copy with a syntactically valid dummy digest (never written)
    mem = copy.deepcopy(decl)
    mem["authorization"]["owner_token_sha256"] = C.DUMMY_DIGEST
    v = PF.validate_declaration(mem, decl_path)
    ck["validate_declaration_in_memory_dummy_digest"] = {"result": "PASSED", "dummy_digest": "a fixed 64-hex value (63 zeros and a one) held in memory only; it is no token's digest and was never written",
                                                         "normalised": {k: v[k] for k in ("stamp", "run_folder", "caps", "project_day_limit", "lane_switches", "authorization_path")},
                                                         "ledger": v["ledger"], "provider_env_keys": sorted(v["provider_env"])}

    # 3. the binding manifest
    vb = PF.verify_binding(C.BINDING, BINDING_SHA)
    ck["verify_binding"] = {"result": "PASSED", **vb}

    # 4a. the live runner from the bound copy, as written, without authorization and without a token
    env = {k: val for k, val in os.environ.items() if k != TOKEN_ENV} | {"PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "PYTHONIOENCODING": "utf-8"}
    cmd = [C.PY, "-B", "runner_r32.py", "run", "--mode", "live", "--declaration", decl_path.as_posix(), "--declaration-sha", sha,
           "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING.as_posix(), "--binding-sha", BINDING_SHA]
    r = subprocess.run(cmd, cwd=str(C.HARNESS_BOUND), env=env, capture_output=True, text=True, encoding="utf-8", timeout=900)
    last = [ln for ln in (r.stderr or "").strip().splitlines() if ln.strip()]
    ck["runner_live_run_as_written"] = {"command": " ".join(cmd[1:]), "working_directory": C.HARNESS_BOUND.as_posix(), "token_presented": False,
                                        "authorization_file_present": pinned.exists(), "returncode": r.returncode, "stdout": r.stdout[-2000:],
                                        "stderr_last_line": last[-1] if last else None, "run_folder_created": run_folder.exists(),
                                        "result": "REFUSED" if r.returncode != 0 and "refused" in (last[-1] if last else "").lower() and not run_folder.exists() else "UNEXPECTED"}

    # 4b. the same runner in-process with the in-memory dummy-digest copy (patched loader; nothing written)
    import runner_r32 as RN  # noqa: E402

    original = PF.load_declaration

    def load_in_memory(path, expected_sha, *, binding_sha, run_set_sha):
        if C.sha256_file(path) != expected_sha:
            raise PF.Refused("refused: live mode needs the ORCH-07 declaration and its exact sha256")
        if mem.get("binding_manifest_sha256") != binding_sha or mem.get("run_set_sha256") != run_set_sha:
            raise PF.Refused("refused: the declaration does not bind this binding manifest and this run set")
        return mem, PF.validate_declaration(mem, path)

    PF.load_declaration = load_in_memory
    try:
        RN.main(cmd[3:])
        ck["runner_live_run_in_memory_dummy_digest"] = {"result": "UNEXPECTED: not refused"}
    except PF.Refused as exc:
        ck["runner_live_run_in_memory_dummy_digest"] = {"result": "REFUSED", "reason": str(exc), "run_folder_created": run_folder.exists(),
                                                        "stage": "after the binding, the declaration contract, the HEADs, the truth and population gate and the run set: the declared ledger scope does not exist (it is created only by the owner's budget authorization)"}
    finally:
        PF.load_declaration = original

    # 5. the guard
    g1 = DG.check(decl_path.as_posix(), sha, run_folder=run_folder, invocation=1, action="preview", stamp=BD.STAMP, kind="fresh")
    g2 = DG.check(decl_path.as_posix(), sha, run_folder=run_folder, invocation=1, action="consume", stamp=BD.STAMP, kind="fresh")
    g3 = DG.check(None, None)
    built = []
    gp = DG.GuardedProvider(lambda: built.append("built") or (_ for _ in ()).throw(RuntimeError("a provider was built")), decl_path.as_posix(), sha, _Resp,
                            run_folder=run_folder, invocation=1, token=None)
    resp = gp.complete(object())
    ck["dispatch_guard"] = {"preview": g1, "consume_through_check_is_preview": g2, "no_declaration": g3,
                            "guarded_provider": {"error": resp.error, "detail": resp.error_detail, "refused": gp.refused, "dispatched": gp.dispatched,
                                                 "inner_built": bool(built)},
                            "result": "REFUSED" if not g1["authorized"] and not g2["authorized"] and resp.error == "dispatch_refused" and not built else "UNEXPECTED"}

    after = {"ai_ledger": {k: v for k, v in C.ledger_state().items() if k != "scope_names"}, "run_folder_exists": run_folder.exists(),
             "r34_sandbox_top_listing": top_listing(C.LIVE_SANDBOX_BASE), "harness_bound_listing": listing(C.HARNESS_BOUND),
             "package_listing": listing(C.PACKAGE), "pinned_authorization_exists": pinned.exists(),
             "dispatch_authorization_files": C.authorization_files(search_roots), "token_env_present": TOKEN_ENV in os.environ}
    res["after"] = after
    res["invariants"] = {
        "ai_ledger_483_17_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
        "run_folder_never_created": not before["run_folder_exists"] and not after["run_folder_exists"],
        "r34_sandbox_unchanged": before["r34_sandbox_top_listing"] == after["r34_sandbox_top_listing"],
        "harness_bound_unchanged": before["harness_bound_listing"] == after["harness_bound_listing"],
        "package_unchanged_by_the_preflight": before["package_listing"] == after["package_listing"],
        "no_authorization_file": not before["pinned_authorization_exists"] and not after["pinned_authorization_exists"] and not after["dispatch_authorization_files"],
        "no_token": not before["token_env_present"] and not after["token_env_present"],
        "dummy_digest_never_written": C.DUMMY_DIGEST not in json.dumps(after["package_listing"]) and all(
            C.DUMMY_DIGEST.encode() not in (C.PACKAGE / f).read_bytes() for f in after["package_listing"]),
        "model_requests": 0}
    res["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    res["ok"] = all(v for k, v in res["invariants"].items() if k != "model_requests") and all(
        ck[k]["result"] in ("REFUSED", "PASSED") for k in ck) and ck["validate_declaration_as_written"]["result"] == "REFUSED" \
        and ck["validate_declaration_in_memory_dummy_digest"]["result"] == "PASSED" and ck["verify_binding"]["result"] == "PASSED"
    out_sha = C.write_json_once(target, res)
    print(json.dumps({"written": target.as_posix(), "sha256": out_sha, "ok": res["ok"], "invariants": res["invariants"],
                      "results": {k: v.get("result") for k, v in ck.items()},
                      "reasons": {k: v.get("reason") or v.get("stderr_last_line") for k, v in ck.items() if k != "dispatch_guard"},
                      "guard": ck["dispatch_guard"]["preview"]}, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    p = pathlib.Path(sys.argv[1])
    assert p.is_absolute()
    sys.exit(main(p))
