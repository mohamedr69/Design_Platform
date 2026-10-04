"""ORCH-09 (R40DECL-IMPL): the dry preflight of the frozen corrected declaration against the bound review39 harness (no
dispatch, no model request, no `claude` invocation, no scope, no token, no authorization file, no RUN file).

Usage: preflight_r40.py
Writes (once each): dry-run/PREFLIGHT-RESULTS.json, dry-run/lane-env/LANE-ENV-<lane>.json (+ LANE-ENV-CFG.json),
scope/SCOPE-PREVIEW-OUTPUT.json, scope/SCOPE-CREATE-REFUSED-OUTPUT.json; sandboxes only under C:/t/r2x/r40-sandbox/r40d-*.
  1. validate_declaration on the frozen file as written: REFUSED (placeholder digest)
  2. validate_declaration on an IN-MEMORY copy with a syntactically valid dummy digest (never written): PASSED
  3. negative probes on in-memory copies (contract 4), each with its expected result; and the integer-string check (R40-08)
  4. verify_binding(BINDING-MANIFEST-R39, a6f703b4...): every bound file
  5. verify_bounds: PROJECT-REQUEST-BOUNDS recomputed from the run set, the truth and the bound code with the declared switches
  6. the four lanes' live environment checks offline (lane_env_check_r40.py; R39-18 class)
  7. the live runner as a subprocess, as the owner would type it, without the RUN file and without a token: refused, no folder
  8. the live runner in-process with the in-memory RUN copy (patched loader; nothing written): refused at the ledger scope
  9. the same with the scope check and the guard's declaration loader patched to the in-memory copy: refused by the guard
     ('no owner dispatch authorization') before any folder exists
 10. the guard alone: preview, consume-through-check, no declaration, GuardedProvider (inner never built), validate()
 11. the scope command: preview (creates nothing) and create (refused: no authorization file)
 Invariants before and after: AI ledger 483 / 17 / 0; run folder never created; the review39 harness unchanged with no
 __pycache__; no authorization / RUN / token file anywhere searched; no token in the environment; the dummy digest in no
 package file; 0 model requests."""
from __future__ import annotations

import copy
import dataclasses
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
os.environ["GIT_OPTIONAL_LOCKS"] = "0"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ.pop("R34_OWNER_DISPATCH_TOKEN", None)
import build_declaration_r40 as BD  # noqa: E402
import create_scope_r40 as CS  # noqa: E402
import r40common as C  # noqa: E402

OUT = C.PACKAGE / "dry-run"
SCOPE_OUT = C.PACKAGE / "scope"
HERE = pathlib.Path(__file__).resolve().parent


def listing(root: pathlib.Path, skip=()) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(p.relative_to(root).as_posix().startswith(s) for s in skip):
            out[p.relative_to(root).as_posix()] = C.sha256_file(p)
    return out


@dataclasses.dataclass
class _Resp:
    data: object = None
    model: str = ""
    error: str | None = None
    error_detail: str | None = None


def invariants() -> dict:
    return {"ai_ledger": C.ledger_counts(), "run_folder_exists": C.RUN_FOLDER.exists(),
            "harness_listing_sha256": hashlib.sha256(json.dumps(listing(C.HARNESS), sort_keys=True).encode()).hexdigest(),
            "harness_pycache": [p.as_posix() for p in C.HARNESS.rglob("__pycache__")],
            "package_listing_sha256": hashlib.sha256(json.dumps(listing(C.PACKAGE, skip=("dry-run/", "scope/", "tests/", "evidence/")), sort_keys=True).encode()).hexdigest(),
            "forbidden_files": C.forbidden_files(), "token_env_present": C.TOKEN_ENV in os.environ}


def set_path(d: dict, path: str, value):
    keys = path.split(".")
    for k in keys[:-1]:
        d = d[k]
    if value is _DEL:
        d.pop(keys[-1], None)
    else:
        d[keys[-1]] = value


_DEL = object()


def probes(mem: dict) -> list:
    """(name, [(path, value), ...], expected) -- expected 'REFUSED' or 'ACCEPTED' by validate_declaration (contract 4)."""
    led = mem["ledger"]
    other_limits = dict(led["limits"], requests=555)
    out_lim = dict(led["limits"], output_tokens=3_000_000)
    return [
        ("lane allowance B 241", [("budget.lane_allowances", {"B": 241, "C": 240, "R": 40, "P": 36})], "REFUSED"),
        ("lane allowances without P", [("budget.lane_allowances", {"B": 240, "C": 240, "R": 40})], "REFUSED"),
        ("parent total 600 (parent / lane inconsistency)", [("budget.parent", dict(mem["budget"]["parent"], total=600))], "REFUSED"),
        ("parent missing elapsed_s", [("budget.parent", {k: v for k, v in mem["budget"]["parent"].items() if k != "elapsed_s"})], "REFUSED"),
        ("parent elapsed 600000 with the ledger equal (bounds computed for another elapsed bound)",
         [("budget.parent", dict(mem["budget"]["parent"], elapsed_s=600000)), ("ledger.limits", dict(led["limits"], elapsed_s=600000)),
          ("provider_env.AI_LEDGER_LIMITS", json.dumps(dict(led["limits"], elapsed_s=600000), sort_keys=True))], "REFUSED"),
        ("ledger output_tokens differs from the parent", [("ledger.limits", out_lim), ("provider_env.AI_LEDGER_LIMITS", json.dumps(out_lim, sort_keys=True))], "REFUSED"),
        ("ledger requests 555 (not the parent total)", [("ledger.limits", other_limits), ("provider_env.AI_LEDGER_LIMITS", json.dumps(other_limits, sort_keys=True))], "REFUSED"),
        ("project window limit 61", [("project_window", {"limit": 61, "window_s": 86400})], "REFUSED"),
        ("project window 3600 s", [("project_window", {"limit": 60, "window_s": 3600})], "REFUSED"),
        ("project window limit 30 (bounds computed for another window)", [("project_window", {"limit": 30, "window_s": 86400})], "REFUSED"),
        ("AI_MAX_CALLS_PER_PROJECT_PER_DAY 83 (below the minimum 84)", [("provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY", "83")], "REFUSED"),
        ("AI_MAX_CALLS_PER_PROJECT_PER_DAY 60 (the tree default)", [("provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY", "60")], "REFUSED"),
        ("AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY 83", [("provider_env.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY", "83")], "REFUSED"),
        ("AI_MAX_CALLS_PER_PROJECT_PER_DAY '96.0' (float string)", [("provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY", "96.0")], "REFUSED"),
        ("AI_MAX_CALLS_PER_PROJECT_PER_DAY '84' (the minimum)", [("provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY", "84")], "ACCEPTED"),
        ("AI_MAX_CALLS_PER_DOCUMENT '12.0' (float string; R39-18 / R40-08: the harness accepts it)", [("provider_env.AI_MAX_CALLS_PER_DOCUMENT", "12.0")], "ACCEPTED"),
        ("AI_MAX_ELAPSED_S_PER_JOB '120.0' (float string; R39-18 / R40-08: the harness accepts it)", [("provider_env.AI_MAX_ELAPSED_S_PER_JOB", "120.0")], "ACCEPTED"),
        ("AI_MAX_CALLS_PER_DOCUMENT 11 (per-document limit)", [("provider_env.AI_MAX_CALLS_PER_DOCUMENT", "11")], "REFUSED"),
        ("AI_MAX_CALLS_PER_DOCUMENT 13 (per-document limit)", [("provider_env.AI_MAX_CALLS_PER_DOCUMENT", "13")], "REFUSED"),
        ("AI_MAX_ELAPSED_S_PER_JOB 119 (per-document limit)", [("provider_env.AI_MAX_ELAPSED_S_PER_JOB", "119")], "REFUSED"),
        ("alias 'sonnet' pinned and configured", [("model_identity.models.small", "sonnet"), ("provider_env.AI_MODEL_SMALL", "sonnet")], "REFUSED"),
        ("alias 'opus' pinned and configured", [("model_identity.models.standard", "opus"), ("provider_env.AI_MODEL_STANDARD", "opus")], "REFUSED"),
        ("AI_MODEL_SMALL 'sonnet' against the pin claude-sonnet-5", [("provider_env.AI_MODEL_SMALL", "sonnet")], "REFUSED"),
        ("provider 'claude' in model_identity", [("model_identity.provider", "claude")], "REFUSED"),
        ("CLI path differs from AI_CLAUDE_CLI", [("model_identity.cli.path", "C:/other/claude.exe")], "REFUSED"),
        ("CLI version '2.1.263' (not the exact version line; the contract accepts any non-empty line, the runner compares it with `claude --version` at every invocation)",
         [("model_identity.cli.version", "2.1.263")], "ACCEPTED"),
        ("AI_LEDGER_SCOPE differs from ledger.scope (scope mismatch)", [("provider_env.AI_LEDGER_SCOPE", "m2-other-scope")], "REFUSED"),
        ("ledger.scope differs from AI_LEDGER_SCOPE (scope mismatch)", [("ledger.scope", "m2-other-scope")], "REFUSED"),
        ("run folder elsewhere", [("run.folder", "C:/t/r2x/r40-sandbox/another")], "REFUSED"),
        ("sandbox base not C:/t/r2x/r<NN>-sandbox", [("run.sandbox_base", "C:/t/r2x/sandbox"), ("run.folder", "C:/t/r2x/sandbox/r32-v2")], "REFUSED"),
        ("stamp 'a' (too short)", [("run.stamp", "a"), ("run.folder", "C:/t/r2x/r40-sandbox/a")], "REFUSED"),
        ("authorization path elsewhere", [("authorization.path", "C:/t/OWNER-DISPATCH-AUTHORIZATION.json")], "REFUSED"),
        ("digest upper-case hex", [("authorization.owner_token_sha256", "A" * 64)], "REFUSED"),
        ("digest 63 characters", [("authorization.owner_token_sha256", "0" * 63)], "REFUSED"),
        ("digest = the placeholder", [("authorization.owner_token_sha256", C.TOKEN_PLACEHOLDER)], "REFUSED"),
        ("wrap_provider false", [("ledger.wrap_provider", False)], "REFUSED"),
        ("application_env missing", [("application_env", _DEL)], "REFUSED"),
        ("application_env DRAWINGS_AI_REVIEW_ENABLED true", [("application_env", {"DRAWINGS_AI_REVIEW_ENABLED": "true"})], "REFUSED"),
        ("application_env with an extra key", [("application_env", {"DRAWINGS_AI_REVIEW_ENABLED": "false", "OTHER": "x"})], "REFUSED"),
        ("decision coverage gate binding R (plan v2 C_GE_B_AND_C_GE_R)", [("decision_coverage_gate", "C_GE_B_AND_C_GE_R")], "REFUSED"),
        ("decision coverage gate unknown id", [("decision_coverage_gate", "C_GE_R")], "REFUSED"),
        ("resume_policy 'soonest'", [("resume_policy", "soonest")], "REFUSED"),
        ("resume_policy 'earliest' (allowed by contract 4; this declaration binds 'full')", [("resume_policy", "earliest")], "ACCEPTED"),
        ("lane_task_kinds widened (B + drawings_reply_match)", [("lane_task_kinds.B", ["read_submittal_form", "drawings_reply_match"])], "REFUSED"),
        ("lane P with switches", [("lane_switches.P", {"AI_EVIDENCE_VARIANT": "EV1"})], "REFUSED"),
        ("provider_env with an AI_EVIDENCE_* key", [("provider_env.AI_EVIDENCE_VARIANT", "EV1")], "REFUSED"),
        ("contract 3", [("contract", "r38-live-contract-3")], "REFUSED"),
        ("a dry exercise flag", [("dry_exercise", True)], "REFUSED"),
    ]


def main() -> int:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    if (OUT / "PREFLIGHT-RESULTS.json").exists():
        raise SystemExit("refused: PREFLIGHT-RESULTS.json is written once")
    C.harness_import_path()
    import dispatch_guard_r32 as DG  # noqa: E402
    import preflight_r32 as PF  # noqa: E402
    import runner_r32 as RN  # noqa: E402
    frozen, fsha = BD.frozen_bytes_checked()
    decl = json.loads(frozen.decode("utf-8"))
    run_path = C.PACKAGE / C.RUN_NAME
    before = invariants()
    res = {"name": "PREFLIGHT-RESULTS (ORCH-09 dry preflight of declaration-r32-v2)", "started_utc": started,
           "declaration": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(), "sha256": fsha}, "harness": C.HARNESS.as_posix(),
           "binding_manifest": {"path": C.BINDING.as_posix(), "sha256": C.BINDING_SHA}, "before": before, "checks": {}}
    ck = res["checks"]
    # 1. as written
    try:
        PF.validate_declaration(decl, C.PACKAGE / C.DECLARATION_NAME)
        ck["1_validate_declaration_as_written"] = {"result": "ACCEPTED (UNEXPECTED)"}
    except PF.Refused as exc:
        ck["1_validate_declaration_as_written"] = {"result": "REFUSED", "reason": str(exc), "expected": "REFUSED (placeholder digest)"}
    # 2. in-memory dummy digest (the RUN procedure on an in-memory copy; never written)
    run_mem_bytes = BD.fill_owner_digest(frozen, C.DUMMY_DIGEST)
    run_mem_sha = C.sha256_bytes(run_mem_bytes)
    mem = json.loads(run_mem_bytes.decode("utf-8"))
    v = PF.validate_declaration(mem, run_path)
    ck["2_validate_declaration_in_memory_dummy_digest"] = {
        "result": "PASSED", "dummy_digest": "63 zeros and a one, held in memory only; no token's digest; never written",
        "in_memory_run_copy": {"bytes_differ_only_in_the_digest": True, "sha256_of_the_in_memory_copy": run_mem_sha,
                               "note": "the procedure the owner follows (fill_owner_digest), on an in-memory copy; no RUN file was written"},
        "normalised": {k: v[k] for k in ("contract", "stamp", "sandbox_base", "run_folder", "caps", "parent", "project_window", "lane_switches",
                                         "authorization_path", "model_identity", "application_env", "lane_task_kinds", "resume_policy",
                                         "decision_coverage_gate", "bounds_ref")},
        "ledger": v["ledger"], "provider_env_keys": sorted(v["provider_env"])}
    # 3. negative probes + the integer-string check
    rows = []
    for name, muts, expected in probes(mem):
        m = copy.deepcopy(mem)
        for path, value in muts:
            set_path(m, path, value)
        try:
            PF.validate_declaration(m, run_path)
            got, why = "ACCEPTED", None
        except PF.Refused as exc:
            got, why = "REFUSED", str(exc)
        except Exception as exc:  # noqa: BLE001  -- recorded, counts as a failed expectation
            got, why = f"ERROR {type(exc).__name__}", str(exc)
        ints = BD.integer_string_problems(m.get("provider_env") or {})
        rows.append({"probe": name, "mutations": [[p, (None if val is _DEL else val)] for p, val in muts], "expected": expected, "result": got,
                     "as_expected": got == expected, "reason": why, "integer_string_check": ints or "ok"})
    ck["3_negative_probes"] = {"count": len(rows), "all_as_expected": all(r["as_expected"] for r in rows),
                               "float_strings_refused_by_integer_string_check": all(
                                   r["integer_string_check"] != "ok" for r in rows if "float string" in r["probe"]),
                               "rows": rows}
    ck["3b_integer_strings_of_the_declaration"] = {"problems": BD.integer_string_problems(decl["provider_env"]), "result": "PASSED"
                                                   if not BD.integer_string_problems(decl["provider_env"]) else "FAILED"}
    # 4. binding
    vb = PF.verify_binding(C.BINDING, C.BINDING_SHA)
    ck["4_verify_binding"] = {"result": "PASSED", **vb}
    # 5. bounds
    truth = PF.build_truth()
    run_set = PF.load_run_set(str(C.RUN_SET), truth)
    ck["5_verify_bounds"] = {"result": "PASSED", **PF.verify_bounds(v, run_set, truth), "population_gate": PF.population(truth)["action"],
                             "truth_sha256": hashlib.sha256(PF.truth_text(truth).encode("utf-8")).hexdigest(), "run_set_documents": len(run_set)}
    # 6. lanes' live environment checks, offline
    lane_dir = OUT / "lane-env"
    lane_dir.mkdir(parents=True, exist_ok=True)
    cfg = {"lane_switches": v["lane_switches"], "application_env": v["application_env"], "provider_env": v["provider_env"], "harness": str(C.HARNESS)}
    cfgp = lane_dir / "LANE-ENV-CFG.json"
    C.write_json_once(cfgp, cfg)
    lanes = {}
    for lane in ("B", "C", "R", "P"):
        root = C.SANDBOX_BASE / f"r40d-env-{lane}"
        env = RN.lane_env("live", root, lane, cfg)
        env.pop(C.TOKEN_ENV, None)
        tree = RN.TREES["baseline" if lane == "B" else "candidate"]
        r = subprocess.run([C.PY, "-B", str(HERE / "lane_env_check_r40.py"), lane, str(cfgp), str(lane_dir / f"LANE-ENV-{lane}.json")], cwd=tree, env=env,
                           capture_output=True, text=True)
        out = json.loads((lane_dir / f"LANE-ENV-{lane}.json").read_text(encoding="utf-8")) if (lane_dir / f"LANE-ENV-{lane}.json").exists() else {}
        lanes[lane] = {"returncode": r.returncode, "ok": out.get("ok"), "checks": {k: x.get("result") for k, x in (out.get("checks") or {}).items()},
                       "tree": tree, "sandbox_tmp": root.as_posix()}
    ck["6_lane_environment_checks_offline"] = {"result": "PASSED" if all(x["ok"] for x in lanes.values()) else "FAILED", "lanes": lanes,
                                               "what": "the live lane's own checks (verify_lane_environment mode live, verify_application_env, drawing_ai_review.enabled()) with the environment runner_r32.lane_env('live') builds from the declaration: every declared value parses into the application's settings (R39-18 class)"}
    # 7. the live runner as a subprocess, as the owner would type it, without the RUN file and without a token
    env = {k: val for k, val in os.environ.items() if k != C.TOKEN_ENV} | {"PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "PYTHONIOENCODING": "utf-8"}
    argv = ["run", "--mode", "live", "--declaration", run_path.as_posix(), "--declaration-sha", run_mem_sha, "--run-set", C.RUN_SET.as_posix(),
            "--binding", C.BINDING.as_posix(), "--binding-sha", C.BINDING_SHA]
    r = subprocess.run([C.PY, "-B", "runner_r32.py", *argv], cwd=str(C.HARNESS), env=env, capture_output=True, text=True, encoding="utf-8", timeout=900)
    last = [ln for ln in (r.stderr or "").strip().splitlines() if ln.strip()]
    ck["7_runner_live_subprocess_without_run_file_or_token"] = {
        "command": "python -B runner_r32.py " + " ".join(argv), "working_directory": C.HARNESS.as_posix(), "run_file_exists": run_path.exists(),
        "token_presented": False, "returncode": r.returncode, "stderr_last_line": last[-1] if last else None, "run_folder_created": C.RUN_FOLDER.exists(),
        "result": "REFUSED" if r.returncode != 0 and last and "refused" in last[-1].lower() and not C.RUN_FOLDER.exists() else "UNEXPECTED",
        "note": "the frozen hash is never given to the runner; the sha given is that of the in-memory RUN copy, whose file does not exist"}
    # 8 / 9. the live runner in-process with the in-memory RUN copy (patched loaders; nothing written)
    original_load, original_scope, original_dg_load = PF.load_declaration, PF.verify_ledger_scope, DG._load_declaration

    def load_in_memory(path, expected_sha, *, binding_sha, run_set_sha):
        if expected_sha != run_mem_sha:
            raise PF.Refused("refused: live mode needs the declaration and its exact sha256")
        if mem.get("binding_manifest_sha256") != binding_sha or mem.get("run_set_sha256") != run_set_sha:
            raise PF.Refused("refused: the declaration does not bind this binding manifest and this run set")
        return mem, PF.validate_declaration(mem, path)

    def dg_load_in_memory(declaration_path, declaration_sha256):
        if declaration_sha256 != run_mem_sha:
            raise DG.DispatchRefused("refused: the declaration is missing or does not hash to the verified sha256")
        return mem

    PF.load_declaration = load_in_memory
    try:
        try:
            RN.main(argv)
            ck["8_runner_live_in_process_in_memory_run_copy"] = {"result": "UNEXPECTED: not refused"}
        except PF.Refused as exc:
            ck["8_runner_live_in_process_in_memory_run_copy"] = {
                "result": "REFUSED", "reason": str(exc), "run_folder_created": C.RUN_FOLDER.exists(),
                "stage": "after the binding (239 files), the declaration contract 4, the HEADs, the truth and population gate, the run set and the bounds recomputation: the declared ledger scope does not exist (created only by the owner, create_scope_r40.py)"}
        PF.verify_ledger_scope = lambda led: {"scope": led["scope"], "limits": led["limits"], "entries": 0, "breaker": None, "patched": "pretend the scope exists (in-process only)"}
        DG._load_declaration = dg_load_in_memory
        try:
            RN.main(argv)
            ck["9_runner_live_in_process_scope_pretended"] = {"result": "UNEXPECTED: not refused"}
        except PF.Refused as exc:
            ck["9_runner_live_in_process_scope_pretended"] = {
                "result": "REFUSED" if "no owner dispatch authorization" in str(exc) and not C.RUN_FOLDER.exists() else "UNEXPECTED", "reason": str(exc),
                "run_folder_created": C.RUN_FOLDER.exists(),
                "stage": "every preflight step passed (the scope check patched to pretend the scope exists); the guard preview refused: no authorization file at the pinned path; before the run folder, the WRITER lock, the CLI version check and any consumption"}
        # 10. the guard
        g1 = DG.check(run_path.as_posix(), run_mem_sha, run_folder=C.RUN_FOLDER, invocation=1, action="preview", stamp=C.STAMP, kind="fresh")
        g2 = DG.check(run_path.as_posix(), run_mem_sha, run_folder=C.RUN_FOLDER, invocation=1, action="consume", stamp=C.STAMP, kind="fresh")
        built = []
        gp = DG.GuardedProvider(lambda: built.append("built") or (_ for _ in ()).throw(RuntimeError("a provider was built")), run_path.as_posix(),
                                run_mem_sha, _Resp, run_folder=C.RUN_FOLDER, invocation=1, token=None)
        resp = gp.complete(object())
    finally:
        PF.load_declaration, PF.verify_ledger_scope, DG._load_declaration = original_load, original_scope, original_dg_load
    g3 = DG.check(None, None)
    g4 = DG.check(run_path.as_posix(), run_mem_sha, run_folder=C.RUN_FOLDER, invocation=1, action="preview")
    try:
        DG.validate(mem, run_path, run_mem_sha, None, None)
        g5 = {"authorized": True}
    except DG.DispatchRefused as exc:
        g5 = {"authorized": False, "reason": str(exc)}
    ck["10_dispatch_guard"] = {"preview_in_memory_declaration": g1, "consume_through_check_is_preview": g2, "no_declaration": g3,
                               "run_file_absent": g4, "validate_without_authorization": g5,
                               "guarded_provider": {"error": resp.error, "detail": resp.error_detail, "refused": gp.refused, "dispatched": gp.dispatched,
                                                    "inner_built": bool(built)},
                               "result": "REFUSED" if not any(x["authorized"] for x in (g1, g2, g3, g4, g5)) and resp.error == "dispatch_refused" and not built
                               else "UNEXPECTED"}
    # 11. the scope command
    SCOPE_OUT.mkdir(parents=True, exist_ok=True)
    led_b = C.ledger_counts()
    pv = subprocess.run([C.PY, "-B", str(HERE / "create_scope_r40.py"), "preview"], cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8")
    C.write_once(SCOPE_OUT / "SCOPE-PREVIEW-OUTPUT.json", pv.stdout)
    cr = subprocess.run([C.PY, "-B", str(HERE / "create_scope_r40.py"), "create", "--frozen-sha", fsha, "--run-sha", run_mem_sha], cwd=str(HERE), env=env,
                        capture_output=True, text=True, encoding="utf-8")
    C.write_once(SCOPE_OUT / "SCOPE-CREATE-REFUSED-OUTPUT.json", cr.stdout)
    led_a = C.ledger_counts()
    ck["11_scope_command"] = {"preview": {"returncode": pv.returncode, "output": "scope/SCOPE-PREVIEW-OUTPUT.json", "ledger_unchanged": json.loads(pv.stdout)["ledger_unchanged"]},
                              "create_without_authorization": {"returncode": cr.returncode, "output": "scope/SCOPE-CREATE-REFUSED-OUTPUT.json",
                                                               "refused": json.loads(cr.stdout).get("refused")},
                              "ledger_before": led_b, "ledger_after": led_a,
                              "result": "PASSED" if pv.returncode == 0 and cr.returncode == 3 and led_a == led_b and
                              "no owner dispatch authorization" in (json.loads(cr.stdout).get("refused") or "") else "FAILED"}
    after = invariants()
    res["after"] = after
    pkg_bytes = [(C.PACKAGE / f).read_bytes() for f in listing(C.PACKAGE)]
    res["invariants"] = {
        "ai_ledger_483_17_0_before_and_after": before["ai_ledger"] == after["ai_ledger"] and {k: after["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED,
        "run_folder_never_created": not before["run_folder_exists"] and not after["run_folder_exists"],
        "harness_unchanged_no_pycache": before["harness_listing_sha256"] == after["harness_listing_sha256"] and not after["harness_pycache"],
        "package_unchanged_by_the_preflight_outside_its_outputs": before["package_listing_sha256"] == after["package_listing_sha256"],
        "no_authorization_run_or_token_file": not before["forbidden_files"] and not after["forbidden_files"],
        "no_token_in_the_environment": not before["token_env_present"] and not after["token_env_present"],
        "dummy_digest_never_written": all(C.DUMMY_DIGEST.encode() not in b for b in pkg_bytes),
        "model_requests": 0}
    res["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    expect = {"1_validate_declaration_as_written": "REFUSED", "2_validate_declaration_in_memory_dummy_digest": "PASSED", "4_verify_binding": "PASSED",
              "5_verify_bounds": "PASSED", "6_lane_environment_checks_offline": "PASSED", "7_runner_live_subprocess_without_run_file_or_token": "REFUSED",
              "8_runner_live_in_process_in_memory_run_copy": "REFUSED", "9_runner_live_in_process_scope_pretended": "REFUSED", "10_dispatch_guard": "REFUSED",
              "11_scope_command": "PASSED", "3b_integer_strings_of_the_declaration": "PASSED"}
    res["ok"] = all(ck[k]["result"] == want for k, want in expect.items()) and ck["3_negative_probes"]["all_as_expected"] and \
        ck["3_negative_probes"]["float_strings_refused_by_integer_string_check"] and all(x for k, x in res["invariants"].items() if k != "model_requests")
    sha = C.write_json_once(OUT / "PREFLIGHT-RESULTS.json", res)
    print(json.dumps({"written": (OUT / "PREFLIGHT-RESULTS.json").as_posix(), "sha256": sha, "ok": res["ok"], "invariants": res["invariants"],
                      "results": {k: x.get("result") for k, x in ck.items() if isinstance(x, dict) and "result" in x},
                      "probes": f"{sum(r['as_expected'] for r in rows)}/{len(rows)} as expected"}, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
