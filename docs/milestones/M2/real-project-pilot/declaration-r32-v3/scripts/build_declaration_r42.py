"""ORCH-10 (R42PORT-IMPL): build and write ONCE the corrected fresh-validation declaration v3
`PILOT/declaration-r32-v3/FRESH-VALIDATION-DECLARATION-R32-V3.json` and `DECLARATION.sha256` beside it, bound to the review42
harness (BINDING-MANIFEST-R42), live declaration contract 5 (preflight_r32.validate_declaration of the review42 copy).

Method: the v2 declaration `f38fb281...25af` (frozen, superseded, never run) is loaded from its exact bytes, every path of
the absent Desktop installation is re-pointed to the merged installation, and ONLY the corrections of ORCH-10 section 2
are applied (portability, the CLI pin, the interpreter, the disk precondition, the isolation, the global-provider boundary,
the invocation order and re-entry, the multi-invocation authorization proposal, stamp / run folder / scope, supersedes, the
R41-12 / R41-13 statements, verification41_items). Every number of v2 is carried (DECLARATION-DIFF proves it). Every bound
file is re-hashed at build time (a {path, sha256} node anywhere in the declaration); a difference is PACKET MISMATCH and
nothing is written.

The declaration is NOT an authorization: executed false, budget_approved false, authorization status "none; owner decision
pending", and authorization.owner_token_sha256 is the explicit placeholder (exactly once in the file).

Usage (this task):   build_declaration_r42.py show | write
Usage (OWNER ONLY, never by this task):
                     build_declaration_r42.py fill_owner_digest --digest <64 lower-case hex>
                     build_declaration_r42.py write_authorization --run-sha <RUN hash> [--nonce N] [--invocations K --nonces N1,N2,...]
                         (K > 1: the separable multi-invocation form, K <= the declared bound 3; default: the per-invocation form)
Usage (anyone, read-only):
                     build_declaration_r42.py verify_run_file --digest <hex> --run-sha <hex>"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import pathlib
import re
import secrets
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

PKG_SCRIPTS = "PILOT/declaration-r32-v3/scripts"
V2_PROOF = C.V2 / "evidence/r40-04-proof"
V2_RECORDS = C.V2 / "evidence/review39-work-records"


# ---- the frozen v2 bytes, re-pointed -------------------------------------------------------------------------------------------
def v2_bytes() -> bytes:
    b = (C.V2 / C.V2_NAME).read_bytes()
    if C.sha256_bytes(b) != C.V2_SHA:
        raise C.PacketMismatch(f"PACKET MISMATCH: the v2 declaration is not {C.V2_SHA}")
    return b


def repoint(o):
    if isinstance(o, dict):
        return {k: repoint(v) for k, v in o.items()}
    if isinstance(o, list):
        return [repoint(v) for v in o]
    if isinstance(o, str):
        return o.replace(C.DESKTOP_EP, C.MERGED_EP)
    return o


def bound_nodes(o, path=""):
    """Every {path, sha256} (and {file, file_sha256}) node of the declaration: (json path, file path, sha256)."""
    out = []
    if isinstance(o, dict):
        p, s = o.get("path"), o.get("sha256")
        if isinstance(p, str) and re.match(r"[A-Za-z]:/", p) and isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s):
            out.append((path, p, s))
        f, fs = o.get("file"), o.get("file_sha256")
        if isinstance(f, str) and isinstance(fs, str) and re.fullmatch(r"[0-9a-f]{64}", fs):
            out.append((path + ".file", f, fs))
        for k, v in o.items():
            out += bound_nodes(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += bound_nodes(v, f"{path}[{i}]")
    return out


def rehash_all(decl) -> dict:
    nodes = bound_nodes(decl)
    bad, seen = [], {}
    for jp, p, s in nodes:
        if p not in seen:
            seen[p] = C.sha256_file(p)
        if seen[p] != s:
            bad.append({"at": jp, "path": p, "declared": s, "file": seen[p]})
    if bad:
        raise C.PacketMismatch(f"PACKET MISMATCH: {len(bad)} bound file(s) differ: {bad[:4]}")
    return {"bound_nodes": len(nodes), "distinct_files": len(seen)}


def ref(path) -> dict:
    p = pathlib.Path(path)
    return {"path": p.as_posix(), "sha256": C.sha256_file(p)}


def lines_between(path, start_heading: str, stop_heading: str = "## ") -> tuple[list, str]:
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")
    i = lines.index(start_heading)
    j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith(stop_heading)), len(lines))
    while j > i and not lines[j - 1].strip():
        j -= 1
    return lines[i:j], f"{i + 1}-{j}"


# ---- owner procedures (pure; same algorithms as v2's build_declaration_r40) ------------------------------------------------------
def fill_owner_digest(frozen: bytes, digest: str) -> bytes:
    """The ONE derivation of the runnable (RUN) declaration: the placeholder value of authorization.owner_token_sha256
    replaced by the owner's 64-hex token digest; nothing else changes. Pure."""
    if not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
        raise ValueError("the owner token digest is 64 lower-case hex characters")
    needle = json.dumps(C.TOKEN_PLACEHOLDER).encode("utf-8")
    if frozen.count(needle) != 1:
        raise ValueError("the frozen declaration must hold the placeholder exactly once")
    filled = frozen.replace(needle, json.dumps(digest).encode("utf-8"))
    a, b = json.loads(frozen.decode("utf-8")), json.loads(filled.decode("utf-8"))
    assert a["authorization"]["owner_token_sha256"] == C.TOKEN_PLACEHOLDER and b["authorization"]["owner_token_sha256"] == digest
    a["authorization"]["owner_token_sha256"] = digest
    assert a == b, "the filled declaration differs from the frozen one in more than the owner token digest"
    return filled


def authorization_text(run_sha: str, digest: str, nonces: list, *, frozen_sha: str, multi: bool = False, bound: int = 3) -> str:
    """The owner's OWNER-DISPATCH-AUTHORIZATION.json content (pure; returned, never written here). Per-invocation form by
    default; the multi-invocation form (A-11 section 4) only when multi is True: exactly the keys the guard accepts."""
    if not re.fullmatch(r"[0-9a-f]{64}", run_sha or "") or not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
        raise ValueError("the RUN hash and the digest are 64 lower-case hex characters")
    if run_sha in (frozen_sha, C.V2_SHA):
        raise ValueError("the authorization names the RUN hash, never a frozen hash")
    if not nonces or any(not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", n or "") for n in nonces) or len(set(nonces)) != len(nonces):
        raise ValueError("every nonce is 16-128 characters [A-Za-z0-9_-], distinct, fresh")
    base = {"authorized_by": "owner", "declaration_sha256": run_sha, "owner_token_sha256": digest}
    if not multi:
        if len(nonces) != 1:
            raise ValueError("the per-invocation form carries exactly one nonce")
        return json.dumps(base | {"nonce": nonces[0]}, sort_keys=True, indent=1) + "\n"
    if not 1 <= len(nonces) <= bound:
        raise ValueError(f"invocations_authorized is 1..{bound}")
    return json.dumps(base | {"invocations_authorized": len(nonces), "nonces": list(nonces)}, sort_keys=True, indent=1) + "\n"


def frozen_bytes_checked() -> tuple[bytes, str]:
    frozen = (C.PACKAGE / C.DECLARATION_NAME).read_bytes()
    sha = C.sha256_bytes(frozen)
    recorded = (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]
    if sha != recorded:
        raise C.PacketMismatch(f"PACKET MISMATCH: the frozen declaration {sha} != DECLARATION.sha256 {recorded}")
    return frozen, sha


def verify_run_file(digest: str, run_sha: str, run_path=None) -> dict:
    frozen, fsha = frozen_bytes_checked()
    run_path = pathlib.Path(run_path or C.PACKAGE / C.RUN_NAME)
    if not run_path.is_file():
        raise C.PacketMismatch(f"no RUN file at {run_path.as_posix()}")
    raw = run_path.read_bytes()
    want = fill_owner_digest(frozen, digest)
    out = {"frozen_sha256": fsha, "run_path": run_path.as_posix(), "run_sha256": C.sha256_bytes(raw), "expected_run_sha256": C.sha256_bytes(want),
           "bytes_equal_to_single_replacement": raw == want, "given_run_sha256": run_sha}
    out["verified"] = out["bytes_equal_to_single_replacement"] and out["run_sha256"] == run_sha == out["expected_run_sha256"] and run_sha != fsha
    return out


# ---- the v3 declaration -------------------------------------------------------------------------------------------------------
def build(declared_at: str, ev: dict) -> dict:
    """ev: the evidence this task produced and binds (paths under the review42 and v3 packages)."""
    sys.path.insert(0, str(C.HARNESS42))
    import dispatch_guard_r32 as DG      # noqa: E402  (the review42 package copy, checked against BINDING-MANIFEST-R42 first)
    import preflight_r32 as PF           # noqa: E402
    v2 = json.loads(v2_bytes().decode("utf-8"))
    d = repoint(copy.deepcopy(v2))
    binding = json.loads(C.BINDING42.read_text(encoding="utf-8"))
    h42 = binding["files"]["harness_r42_package"]
    modules = {pathlib.Path(p).stem: {"path": p, "sha256": s} for p, s in h42.items() if not pathlib.Path(p).name.startswith("test_")}
    run_folder = C.RUN_FOLDER.as_posix()
    pinned = (C.PACKAGE / C.AUTH_NAME).as_posix()
    run_path = (C.PACKAGE / C.RUN_NAME).as_posix()
    contract_v5 = C.REVIEW42 / "LIVE-RUN-CONTRACT.md"
    s3, s3_lines = lines_between(contract_v5, "## 3. The authorization (`dispatch_guard_r32`; ORCH-10 adds the multi-invocation form)")
    s14, s14_lines = lines_between(contract_v5, "## 14. The invocation order, re-entry and the free-disk floor (ORCH-10; R41-09, R41-10, R41-11)")
    s15, s15_lines = lines_between(contract_v5, "## 15. The global-provider boundary of lanes C, R and P (ORCH-10; R40-04, owner decision A-11: option 2)")
    s16, s16_lines = lines_between(contract_v5, "## 16. Portability to the merged installation and isolation from it (ORCH-10 2.1)")
    v4_text = (C.REVIEW39 / "LIVE-RUN-CONTRACT.md").read_text(encoding="utf-8")
    v5_text = contract_v5.read_text(encoding="utf-8")
    carried_sections = {}
    for name in ("section_4", "section_5", "section_6", "section_13"):
        body = "\n".join(d["stop_rules"]["verbatim_review39_resume_rules"][name]["text"])
        carried_sections[name] = body in v4_text and body in v5_text
    if not all(carried_sections.values()):
        raise C.PacketMismatch(f"contract v5 does not carry the cited v4 sections verbatim: {carried_sections}")
    cli_path = C.CLI_EXE.as_posix()

    d["schema"] = "orch10-fresh-validation-declaration-r32-v3.1"
    d["contract"] = PF.CONTRACT
    d["name"] = ("M2 fresh validation R32, corrected declaration v3 (merged installation): accepted baseline B vs Review 29 combined "
                 "candidate C, with reference R and variation probe P")
    d["task"] = "ORCH-10 (orchestrator ledger ORCH-027), implementation agent R42PORT-IMPL, Claude Opus 5.5 (claude-opus-5-5, self-reported), effort High"
    d["supersedes"] = {
        "declaration": ref(C.V2 / C.V2_NAME), "manifest": ref(C.V2 / "evidence/EVIDENCE-MANIFEST.json"),
        "status": ("superseded by owner mission A-11 (orchestrator ledger ORCH-027, 2026-10-06): not runnable as declared -- its bindings name the "
                   "absent Desktop installation and interpreter; never authorized, never run, never to be run"),
        "differences": "DECLARATION-DIFF.md and DECLARATION-DIFF.json in this package list every difference from v2",
        "structure": ("the v2 content is carried; only the ORCH-10 corrections change it (portability, CLI pin, interpreter, disk precondition, "
                      "isolation, global-provider boundary, invocation order and re-entry, the multi-invocation authorization proposal, stamp, run "
                      "folder and scope); every number of v2 is unchanged"),
        "lineage": d["supersedes"]}
    d["declared_at_utc"] = declared_at
    d["status"] = ("FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file, no run file and no dispatch exist; "
                   "Verification 42 and the owner's decision card are pending")
    d["authorities"]["register"] = ref(C.MR / "orchestrator/AUTHORITY-REGISTER.md")
    d["authorities"]["applied"] = ["A-03", "A-06", "A-08", "A-09", "A-10", "A-11"]
    d["authorities"]["summary"]["A-11"] = ("owner mission (2026-10-05): autonomous preparation of M2 closure; the frozen v2 declaration f38fb281...25af "
                                           "cannot be run as declared and is superseded by v3 (never run); R40-04 closed by option 2, 'a fail-closed "
                                           "boundary'; the R41-09 dead-end class closed in the runner; the C1 disk precondition enforced; one approval "
                                           "for all planned resumptions as a bounded, separable proposal; the owner-only decisions stay the owner's")
    d["binding_manifest_sha256"] = C.sha256_file(C.BINDING42)
    d["run"] = {
        "stamp": C.STAMP, "sandbox_base": C.SANDBOX_BASE.as_posix(), "folder": run_folder, "allowance": f"{run_folder}/allowance.sqlite",
        "capture_store": f"{run_folder}/capture.sqlite", "run_state": f"{run_folder}/RUN-STATE.json",
        "rule": ("one run folder, one allowance (parent budget, lane allowances and project window bound in the file) and one capture store per "
                 "declaration, all bound to the RUN declaration's sha256 (the run key); 'run' once -- re-entered only while the folder holds no "
                 "allowance, no consumed nonce and no charged request (REENTRY-<n>.json) -- then 'resume' only, with the same stamp"),
        "never_moved_or_deleted": v2["run"]["never_moved_or_deleted"],
        "base_justification": [
            "C:/t/r2x/r42-sandbox matches the bound preflight's declared-base rule C:/t/r2x/r<NN>-sandbox; it is this task's own sandbox base and the review42 harness's dry / test default; this task's dry runs use stamps beginning 'r42d', never 'r32-v3'",
            "Windows' 260-character path limit: LongPathsEnabled = 0 on this machine; the base and stamp have the same lengths as v2's (20 and 6 characters), so the longest application path of the run, F032's staged PDF <run folder>/inv-<n>/B/s/EP-27331/<208-character relative path>, stays 255 characters (256 from inv-10), below 260 even without the application's own extended-length helper (evidence/PATHLEN-PROBE.json; review42 makes every hash and binding check of the harness open files through the extended-length prefix)",
            "the folder does not exist at declaration time and must not exist before the owner's first invocation (the runner re-enters an existing folder only through reentry_proof; create_scope_r42.py refuses when it exists)"]}
    a = d["authorization"]
    a["path"] = pinned
    a["owner_token_sha256"] = C.TOKEN_PLACEHOLDER
    a["placeholder_rule"] = a["placeholder_rule"].replace("build_declaration_r40.py", "build_declaration_r42.py")
    a["two_hash_procedure"]["run_file"] = run_path
    a["two_hash_procedure"]["independent_verification"] = a["two_hash_procedure"]["independent_verification"].replace("build_declaration_r40.py",
                                                                                                                      "build_declaration_r42.py")
    a["two_hash_procedure"]["budget_authorization_names"] = [
        "the frozen hash", "the digest", "the RUN hash", f"the absolute RUN-file path {run_path}", f"the absolute authorization path {pinned}",
        f"the scope {C.SCOPE} with limits {json.dumps(d['ledger']['limits'], sort_keys=True)}",
        "the first invocation (runner_r32.py run --mode live, RUNBOOK section 5.1)",
        "optionally (A-11 section 4, the owner's choice): one authorization file for up to 3 planned invocations (invocations_authorized, nonces)"]
    a["authorization_rule_v5"] = {"source": contract_v5.as_posix(), "sha256": C.sha256_file(contract_v5), "lines": s3_lines, "text": s3}
    a["one_invocation_per_authorization"] = (
        "run and every resume each consume exactly one nonce into <run folder>/authorization/consumed-<sha256(nonce)[:32]>.json (O_EXCL), "
        "only after the run's capture store is bound and its allowance exists; the per-invocation form (one nonce per file) is the default, "
        "the multi-invocation form (resume_authorization) carries up to 3 nonces consumed in order")
    a["file_fields_multi"] = {"authorized_by": "owner", "declaration_sha256": "the RUN hash", "owner_token_sha256": "the digest the RUN declaration binds",
                              "invocations_authorized": "N, 1..3 (resume_authorization.max_invocations_per_file)",
                              "nonces": "N distinct one-run nonces, consumed one per invocation in list order", "no_other_key": True}
    a["runbook"] = "RUNBOOK.md in this package (exact, ordered, absolute paths, cmd.exe); SCOPE-CREATION-COMMAND.md for the scope"
    a["invocation"] = {
        "working_directory": C.HARNESS42.as_posix(), "python": C.PY,
        "environment": {"PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "R34_OWNER_DISPATCH_TOKEN": "<the owner's token, never written>"},
        "run": (f"\"{C.PY}\" -B runner_r32.py run --mode live --declaration \"{run_path}\" --declaration-sha <RUN hash> --run-set \"{C.RUN_SET.as_posix()}\" "
                f"--binding \"{C.BINDING42.as_posix()}\" --binding-sha {d['binding_manifest_sha256']}"),
        "resume": ("the same with 'resume' instead of 'run' (a new authorization file with a fresh nonce first, or the next nonce of a "
                   "multi-invocation file; not before RUN-STATE.json resume_not_before_utc)"),
        "reentry": "after a failure before the allowance existed (REENTRY rule, contract v5 section 14): the same 'run' command, with the same unconsumed authorization",
        "harness_copy": "PILOT/review42/scripts/harness-r32 is the only harness BINDING-MANIFEST-R42 binds as runnable (harness_r42_package)"}
    d["model_identity"]["cli"] = {"path": cli_path, "sha256": C.CLI_EXE_SHA, "version": C.CLI_VERSION_LINE}
    d["provider_env"]["AI_CLAUDE_CLI"] = cli_path
    d["provider_env"]["AI_LEDGER_SCOPE"] = C.SCOPE
    d["ledger"]["scope"] = C.SCOPE
    mc = d["model_identity_detail"]["cli"]
    mc["path_setting"] = (f"the ABSOLUTE path {cli_path} (AI_CLAUDE_CLI and model_identity.cli.path; contract 5 refuses a name on PATH); the owner "
                          "still confirms with his own `claude --version` before invocation 1 and every resume")
    mc["rule"] = ("the preflight reads the pinned file AS BYTES and refuses another sha256 before anything is created (preflight_r32.verify_cli, "
                  "runner and every live lane); the runner runs `<path> --version` after the guard preview and BEFORE the run folder is created "
                  "or re-opened, and refuses a line other than '2.1.263 (Claude Code)' or the run's first (check_version); the line is recorded "
                  "(CLI-VERSIONS.jsonl, PROVIDER-IDENTITY.json with the file sha256); a CLI change requires a NEW declaration hash")
    mc["bundled_cli_not_used"] = {"path": C.BUNDLED_CLI_NOT_USED.as_posix(), "statement": (
        "the merged installation bundles its own claude.exe 2.1.289 for its FA-interfaces workflow (its .env AI_CLAUDE_CLI); the experiment never "
        "uses it: the declaration pins the WinGet 2.1.263 file by absolute path and sha256, and the merged .env is never read")}
    d["model_identity_detail"]["probe"] = d["model_identity_detail"]["probe"]
    d["ledger_detail"]["creation"] = (
        "created only by the owner, with create_scope_r42.py create (SCOPE-CREATION-COMMAND.md), after the budget authorization, with the "
        "authorization file naming the RUN hash and the token presented, with drive C at or above the 2 GiB floor (condition C1, checked by the "
        "command); new and empty, exactly these limits, closed breaker, immediately before the first invocation; this task created no scope "
        "(AI ledger 483 entries / 17 scopes / 0 amendments before and after); the harness never creates a scope")
    d["project_request_bounds"] = ref(C.BOUNDS42)
    d["project_request_bounds_detail"]["equality_with_review39"] = ev["bounds_equality"]
    d["resume_detail"]["resume_invocations"]["path"] = (C.REVIEW42 / "RESUME-INVOCATIONS-R42.json").as_posix()
    d["resume_detail"]["resume_invocations"]["sha256"] = C.sha256_file(C.REVIEW42 / "RESUME-INVOCATIONS-R42.json")
    d["resume_detail"]["resume_invocations"]["equality_with_review39"] = "byte-identical to review39's RESUME-INVOCATIONS-R39.json (9791fa89...)"
    # ---- contract 5 keys ----------------------------------------------------------------------------------------------------------
    d["interpreter"] = {"path": C.PY, "sha256": C.sha256_file(C.PY), "version": sys.version.split()[0]}
    d["interpreter_detail"] = ev["interpreter_detail"]
    d["disk_precondition"] = {"path": "C:/", "min_free_bytes": C.MIN_FREE_BYTES}
    d["disk_precondition_detail"] = {
        "condition": "Verification 41 condition C1 (R41-10): at least 2 GB free on drive C before the scope creation, invocation 1 and every resume",
        "bound": "2,147,483,648 bytes (2 GiB, which is more than 2 GB); contract 5 refuses a lower value; it may only be raised by a new declaration",
        "enforced_by": ("preflight_r32.verify_free_disk: the runner before anything is created, re-opened or consumed (invocation 1 and every resume), "
                        "every live lane at its start, and create_scope_r42.py create before the scope exists; the owner still stops other heavy "
                        "writers (ep-platform test runs, Codex processes) before each invocation"),
        "why": "every invocation stages the 24 run-set PDFs again (111.7 MB) and the whole run needs about 0.5 GB; a full disk before the allowance existed was a dead-end (R41-09) and a full disk during a lane loses charged requests"}
    d["isolation"] = PF.isolation_binding()
    d["isolation_detail"] = ev["isolation_detail"]
    d["resume_authorization"] = {
        "max_invocations_per_file": 3,
        "status": "PROPOSAL (A-11 section 4): a separable feature the owner may use or not; with invocations_authorized absent the per-invocation behaviour of v2 applies",
        "rules": ["one authorization file may carry invocations_authorized N (1..3) and N distinct nonces",
                  "each invocation consumes exactly one nonce, the first unconsumed one in list order; a consumed nonce is never reusable",
                  "a nonce consumed out of order, a nonce consumed under another file, a repeated nonce or N above the bound is refused",
                  "the file can never name, raise, reset or re-create an allowance, the parent, the window, the scope or any limit (only the five keys are accepted)",
                  "invocation N+1 needs a new authorization file",
                  "a file naming the frozen hash (or any hash other than the RUN hash) is refused"],
        "implementation": {"guard": modules["dispatch_guard_r32"], "tests": "test_resume_authorization_r42.py, test_runner_order_r42.py::test_live_one_approval_for_all_planned_resumptions"},
        "expected_use": "the run needs 2 invocations at the planning estimate and 3 at the structural maximum: one file with 3 nonces covers the planned resumptions"}
    d["global_provider"] = dict(PF.GLOBAL_PROVIDER)
    d["request_path_coverage"] = {
        "finding": "Verification 40 R40-04 (minor), owner decision A-11: option 2 ('a fail-closed boundary')",
        "closed_by": ("lanes C, R and P install run_control_r38.RefusingGlobalProvider as the application's global provider (set_provider) right "
                      "after the provider module is imported, before any application code runs; any get_provider().complete(...) there is refused "
                      "('dispatch_refused': never dispatched, never charged, never reaching the CLI or a ledger), recorded as the contract breach "
                      "'global_provider_request' and makes the run INVALID; lane B keeps the harness chain as its global provider (unchanged)"),
        "static": ev["request_paths"], "dynamic": ev["global_provider_tests"],
        "lane_B": "unchanged: the chain is the global provider, so any request reaches the gate (undeclared kind or missing context: contract breach, run INVALID, never charged)",
        "contract": {"source": contract_v5.as_posix(), "sha256": C.sha256_file(contract_v5), "lines": s15_lines, "text": s15},
        "residual_risk": ("an application path that builds a provider object itself (not through get_provider) and calls it would bypass the chain; "
                          "the static analysis finds no such reached site in either tree (every reached complete() site is the reader's own call "
                          "on the provider the lane passes, or the ledger wrapper), and the declared ledger scope and ledger_live_check still bound "
                          "and expose any request; a provider replaced through set_provider by an application path would be refused at the lane's end "
                          "check (no reached set_provider site exists)"),
        "superseded_v2_coverage": {k: v2["request_path_coverage"][k] for k in ("corrected_claim", "coverage_for_C_R_P", "residual_risk", "owner_options")}
        | {"proof_bound_in_v2": {n: {"path": (V2_PROOF / n).as_posix(), "sha256": C.sha256_file(V2_PROOF / n)} for n in sorted(p.name for p in V2_PROOF.iterdir())}}}
    d["invocation_order"] = {
        "findings": "Verification 41 R41-09 (the dead-end class), R41-10 (C1 disk), R41-11 (CLI updates between invocations)",
        "contract": {"source": contract_v5.as_posix(), "sha256": C.sha256_file(contract_v5), "lines": s14_lines, "text": s14},
        "deadend_cases_closed": ev["deadends"],
        "authorization_consumed": "only after the capture store is bound and the allowance exists; a failure before consumes nothing"}
    d["portability"] = {
        "why": "the Desktop installation (C:/Users/moham/Desktop/dev/dev/...) and its venv are absent; the bindings of v2 name them",
        "repointed": "every Desktop path of v2 is re-pointed to G:/dev (2)/dev/ep-platform-merged/ep-platform/...; every bound file re-hashes equal (bound_files_rehashed)",
        "contract": {"source": contract_v5.as_posix(), "sha256": C.sha256_file(contract_v5), "lines": s16_lines, "text": s16},
        "path_lengths": ev["pathlen"]}
    # ---- the harness ----------------------------------------------------------------------------------------------------------
    hv = d["harness"]
    hv["package"] = "PILOT/review42/"
    hv["package_manifest"] = ref(C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json")
    hv["package_check"] = ref(C.REVIEW42 / "evidence/PACKAGE-CHECK.json")
    hv["binding_manifest"] = ref(C.BINDING42) | {"entries": sum(len(v) for v in binding["files"].values()),
                                                 "supersedes": "review39/BINDING-MANIFEST-R39.json a6f703b4... for the harness code; every carried group re-pointed and re-hashed equal"}
    hv["accepted_by"] = "pending Verification 42 (ORCH-10V); review39 was accepted by Verification 40 and its declaration by Verification 41"
    hv["modules"] = modules
    hv["contracts"] = dict(hv["contracts"]) | {"live_run_contract_v5": ref(contract_v5), "request_paths_r42": ref(C.REVIEW42 / "REQUEST-PATHS.md"),
                                               "request_paths_static_r42": ref(C.REVIEW42 / "REQUEST-PATHS-STATIC.json"),
                                               "change_record_r42": ref(C.REVIEW42 / "CHANGE-RECORD-R42.md")}
    hv["concentration_rule"]["code"] = modules["concentration_r32"]
    hv["lineage"]["review39"] = {"manifest": ref(C.REVIEW39 / "evidence/EVIDENCE-MANIFEST.json"), "binding": ref(C.BINDING39),
                                 "contract_v4": ref(C.REVIEW39 / "LIVE-RUN-CONTRACT.md"), "change_record": ref(C.REVIEW39 / "CHANGE-RECORD-R39.md"),
                                 "accepted_by": "Verification 40 (ORCH-08C VERIFIED); declaration v2 verified with condition C1 by Verification 41"}
    hv["bound_code_used_as_is"] = ("the bound code runs unchanged from PILOT/review42/scripts/harness-r32 under the bound interpreter: the sandbox "
                                   "base is DECLARED (run.sandbox_base), so no relocated copy (twin) is needed; this package's dry exercise ran the "
                                   "same files")
    hv["review39_work_records"] = {n: {"path": (V2_RECORDS / n).as_posix(), "sha256": C.sha256_file(V2_RECORDS / n),
                                       "original": v2["harness"]["review39_work_records"][n]["original"]} for n in ("AUDIT-LOG.md", "PROGRESS.md")}
    d["revision_comparison_rule"]["implementation"] = modules["literal_compare_r32"] | {"function": "norm_revision"}
    d["run_set"]["selector"] = modules["run_set_selector_r32"]
    d["reviews"] = dict(d["reviews"]) | {"verification41": ref(C.MR / "reviews/M2-review-41/INDEPENDENT-VERIFICATION.md"),
                                         "verification41_findings": ref(C.MR / "reviews/M2-review-41/FINDINGS.json"),
                                         "verification41_package_check": ref(C.MR / "reviews/M2-review-41/INDEPENDENT-PACKAGE-CHECK.json"),
                                         "runbook_addendum_r41": ref(C.MR / "orchestrator/RUNBOOK-ADDENDUM-R41.md")}
    d["dispatch_order"] = [
        "owner, before invocation 1: the model-identity probe (RUNBOOK section 1), his own `claude --version` == '2.1.263 (Claude Code)', drive C >= 2 GiB free with no other heavy writer, the two-hash procedure and the scope creation (create_scope_r42.py, which re-checks the CLI file hash and the free disk)",
        "runner checks before anything is created, re-opened or consumed: the binding manifest and every bound file (verify_binding, extended-length opens), the declaration contract 5 (validate_declaration), the bound interpreter, the pinned CLI file's sha256, the free disk (>= 2 GiB), the run set, candidate and baseline HEADs clean, the truth and the population gate, PROJECT-REQUEST-BOUNDS recomputed and equal, the declared ledger scope with exactly the declared limits and a closed breaker, the resume rules or the re-entry proof, the dispatch-guard preview (the pinned authorization, the token digest, an unconsumed nonce), then `<CLI path> --version` compared with the pin and the run's first line",
        "the run folder (invocation 1; or re-entered while it holds no allowance; or re-opened by a resume), the WRITER lock, the version and identity record (CLI-VERSIONS.jsonl, PROVIDER-IDENTITY.json)",
        "the capture store bound to the run key; the allowance created atomically (a resume opens the existing one); ONLY THEN the authorization nonce consumed (O_EXCL record)",
        "B: sandbox_ingest_r32 registers exactly the 24 run-set documents (no processing); lane B processes them with the tripwire after every document; B's final database sha256 recorded",
        "C only when no B document is DEFERRED; C-from-B state check: C's and R's sandboxes are copies of B's final database; state_check.check_c_start must pass (B INVALID means C never starts)",
        "C: the evidence stage on each run-set document with C's switches, the refusing global provider installed; tripwire after every document; unread pages recorded per page",
        "R and P only when no C document is DEFERRED; R: served from C's capture by content key; requests C never made are dispatched once as reference-only",
        "P: the probe over C's answered dispatches as drawn at P's first run (frozen sample)",
        "offline scoring: score_lane_r32 per lane, then score_bcr_r32.evaluate with the candidate-level outcome, the mandatory C >= R diagnostic and the unread pages",
        "a DEFERRED invocation ends with resume_not_before (resume_policy 'full'); every later invocation is a resume with a new authorization (or the next nonce of a multi-invocation file), preceded by the CLI and disk re-checks"]
    d["provider"]["owner_confirmable"]["ledger.scope"] = f"declared {C.SCOPE!r} (a new name; no scope of that name exists)"
    d["provider"]["owner_confirmable"]["cli_version"] = f"pinned {C.CLI_VERSION_LINE!r}, by absolute path {cli_path} and file sha256 {C.CLI_EXE_SHA}"
    d["provider"]["owner_confirmable"]["disk_precondition"] = "declared 2 GiB on drive C (only upward)"
    d["provider"]["owner_confirmable"]["resume_authorization"] = "declared max_invocations_per_file 3 (a proposal; the per-invocation form stays available)"
    d["provider"]["proposed_vs_tree_defaults"]["AI_CLAUDE_CLI"] = {"declared": cli_path, "candidate_and_baseline_tree_default": "claude"}
    d["verification40_items"]["R40-04"] = "request_path_coverage: closed by option 2 (A-11): a fail-closed refusing global provider in C, R and P (review42)"
    d["verification41_items"] = ev["verification41_items"]
    d["bound_files_rehashed"] = {"rule": "every {path, sha256} node of this declaration was re-hashed at build time and equals; v2's carried nodes equal v2's hashes at their merged paths",
                                 "v2_nodes_equal": ev["v2_nodes_equal"]}
    dis = list(d["disclosures"])
    rep = {
        "R40-04: the runtime gate's belt and braces holds for lane B only": ("R40-04 closed by option 2 (A-11): lanes C, R and P install a fail-closed refusing global provider; an application "
                                                                             "get_provider().complete(...) there is refused, recorded as the contract breach 'global_provider_request' and makes "
                                                                             "the run INVALID (request_path_coverage)"),
        "R40-08 / R39-18: the bound validate_declaration still accepts '12.0'": (
            "R40-08 / R39-18 (corrected per R41-12): validate_declaration still accepts '12.0' and '120.0'; such a value would pass the preflight, "
            "consume an owner authorization after the allowance exists and then fail closed in every lane with no request sent; NO runbook step checks "
            "integer strings -- the protection that exists is that this declaration's values are integer strings (checked at build time) and the RUN "
            "file must equal the frozen bytes with only the digest replaced (verify_run_file, create_scope_r42 check_create, the preflight), so no "
            "other value can reach the runner"),
        "the runner records `claude --version` AFTER creating the run folder": (
            "R41-09 closed in the runner (review42): the CLI file hash, the version line, the free disk and every other check run BEFORE the run "
            "folder is created or re-opened; the nonce is consumed only after the capture store and the allowance exist; a folder left by a failure "
            "before the allowance is re-entered by 'run' (REENTRY-<n>.json); no case of Verification 41's dead-end set strands the run or consumes an "
            "authorization (invocation_order.deadend_cases_closed)"),
        "path length: this machine has LongPathsEnabled = 0": (
            "path length: LongPathsEnabled = 0; the merged PILOT prefix is 4 characters longer than the Desktop one; every harness hash and binding "
            "check opens files through the extended-length prefix; the live run paths keep v2's lengths (maximum 255; portability.path_lengths)"),
        "the dry exercise of this declaration ran the bound review39 code unchanged": (
            "the dry exercise of this declaration ran the review42 package code unchanged (declared sandbox base C:/t/r2x/r42-sandbox, no twin) with "
            "reader 'none' and the refusing stub: ONE single 24-document dry run AND six per-project dry runs, the EP-27331 deferral loops under "
            "'full' and a cross-project deferral drill on all 24 documents; it exercises the chain, the deferral / resume loop and the scorer and is "
            "not a result (R41-13: v2's own dry exercise was six per-project runs; Verification 41 ran the single run)")}
    for i, x in enumerate(dis):
        for start, new in rep.items():
            if x.startswith(start):
                dis[i] = new
    missing = [s for s in rep if not any(x == rep[s] for x in dis)]
    if missing:
        raise C.PacketMismatch(f"disclosures not found for replacement: {missing}")
    dis += [
        "portability (A-11 / ORCH-10): v2 is not runnable in the merged installation (its bindings name the absent Desktop installation and venv); v3 carries every number of v2 and is bound to the merged installation (DECLARATION-DIFF)",
        "the interpreter is bound (path, sha256, version); its packages equal both frozen trees' requirements and every application module both trees need imports under it (interpreter_detail)",
        "isolation: every lane refuses an environment value, setting, import path or loaded module under the merged installation except the bound venv and the review42 harness folder; inherited operating-system variables are checked, not replaced (isolation_detail)",
        "the CLI is pinned by absolute path, file sha256 and version line; the merged installation's bundled CLI 2.1.289 is never used; the owner still runs his own `claude --version` before invocation 1 and every resume, and keeps the CLI at 2.1.263 for the run (auto-update off; R41-11)",
        "the disk floor is 2 GiB (2,147,483,648 bytes) on drive C, enforced by the runner and the scope command; it does not protect against another process filling the drive DURING an invocation (the owner stops other heavy writers)",
        "re-entry: a folder left by a failure before the allowance existed is re-entered by 'run' as a new invocation number; its earlier attempt stays recorded in RUN-STATE.json and REENTRY-<n>.json; a partial allowance file is kept aside, never used",
        "the refusing global provider reports itself ready (an application path that asks whether AI is available is told yes and then refused visibly instead of skipping silently)",
        "one approval for all planned resumptions (resume_authorization) is a PROPOSAL the owner may use or not; with one file carrying 3 nonces a compromised token plus that file would allow up to 3 invocations without a further owner action, never more requests than the parent budget",
        "binding counts: BINDING-MANIFEST-R39 has 239 path-keyed bindings, 144 of which named the Desktop installation; v2 held 104 path + sha256 nodes under Desktop paths (123 Desktop string occurrences); the orchestrator's counts 145 / 120 were measured differently; every one is re-pointed"]
    d["disclosures"] = dis
    d["forbidden_after_authorization"] = list(d["forbidden_after_authorization"]) + [
        "using the frozen v2 declaration f38fb281...25af (or any earlier one) for anything but the record",
        "using the merged installation's bundled CLI 2.1.289, its .env, its data or its code in any lane",
        "editing or deleting a run folder's REENTRY-<n>.json, RUN-STATE.json, consumption records or the allowance",
        "lowering the disk floor below 2 GiB or raising resume_authorization.max_invocations_per_file above 3"]
    return d


def evidence() -> dict:
    """The evidence files this task produced, read back (they must exist before the declaration is written)."""
    E = C.PACKAGE / "evidence"
    interp = json.loads((E / "INTERPRETER-CHECK.json").read_text(encoding="utf-8"))
    path = json.loads((E / "PATHLEN-PROBE.json").read_text(encoding="utf-8"))
    outs = json.loads((C.REVIEW42 / "evidence/OUTPUTS-R42.json").read_text(encoding="utf-8"))
    tests = json.loads((C.REVIEW42 / "tests/SUMMARY.json").read_text(encoding="utf-8"))
    demos = json.loads((C.REVIEW42 / "evidence/demos/DEMOS-R42.json").read_text(encoding="utf-8"))
    v2nodes = bound_nodes(repoint(json.loads(v2_bytes().decode("utf-8"))))
    eq = sum(1 for _jp, p, s in v2nodes if C.sha256_file(p) == s)
    return {
        "bounds_equality": {"review39": ref(C.BOUNDS39), "every_verify_bounds_key_equal": outs["bounds"]["verify_bounds_keys_equal"],
                            "differs_only_in": "run_set.path (Desktop -> merged)" if outs["bounds"]["differs_only_in_run_set_path"] else outs["bounds"]["differing_top_level_keys"]},
        "interpreter_detail": {"evidence": ref(E / "INTERPRETER-CHECK.json"), "sys_version": interp["interpreter"]["sys_version"],
                               "base_interpreter": {"path": interp["interpreter"]["base_interpreter"], "sha256": interp["interpreter"]["base_sha256"]},
                               "requirements_differences": {k: v["requirement_differences"] for k, v in interp["trees"].items()},
                               "needed_modules_import": {k: v["needed_modules_import"] for k, v in interp["trees"].items()},
                               "app_resolves_to_tree": {k: v["app_resolves_to_tree"] for k, v in interp["trees"].items()},
                               "other_app_modules_failed": {k: len(v["other_modules_failed"]) for k, v in interp["trees"].items()},
                               "freeze_record_differences": interp["interpreter"]["freeze_record"]["differences"]},
        "isolation_detail": {"rule": "contract v5 section 16; preflight_r32.verify_isolation at every lane's start and end (live and dry)",
                             "lane_env_checks": "dry-run/lane-env/LANE-ENV-<lane>.json (isolation PASSED in all four lanes with the live environment)",
                             "merged_env_file": {"path": C.MERGED_ENV_FILE.as_posix(), "read": False},
                             "inherited_os_environment": "the lanes inherit the operator's operating-system variables (minus AI_*, roots, PWD/OLDPWD) and the isolation check refuses any that names the merged installation"},
        "request_paths": {"static": ref(C.REVIEW42 / "REQUEST-PATHS-STATIC.json"), "summary": outs["request_paths"]["summary"],
                          "reached_sites_equal_to_review39": outs["request_paths"]["reached_sites_equal_to_review39"], "doc": ref(C.REVIEW42 / "REQUEST-PATHS.md")},
        "global_provider_tests": {"junit": ref(C.REVIEW42 / "tests/test_global_provider_r42.xml"), "result": tests["modules"].get("test_global_provider_r42"),
                                  "demo": demos.get("global_provider", {}).get("summary")},
        "deadends": demos.get("deadends", {}).get("summary"),
        "pathlen": {"evidence": ref(E / "PATHLEN-PROBE.json"), "summary": path.get("summary")},
        "verification41_items": {
            "R41-09": "invocation_order (the dead-end class closed in the runner; demos and test_runner_order_r42)",
            "R41-10": "disk_precondition (C1 enforced by the runner and create_scope_r42.py; 2 GiB, only upward)",
            "R41-11": "the CLI file hash and version line re-checked before every resume, before its nonce is consumed (invocation_order; test_runner_order_r42::test_live_E...)",
            "R41-12": "disclosures: the R40-08 / R39-18 statement corrected (no runbook integer-string check exists; the RUN-file equality is the protection)",
            "R41-13": "disclosures and the response entry: the dry exercise named exactly (v2: six per-project runs; v3: the single 24-document run AND six per-project runs)",
            "R41-14": {"bound_by_hash": {p: {"path": p, "sha256": w} for p, w in C.R40_WORK_RECORDS.items()}},
            "R41-15": "record correction: on 2026-10-03 there were two `claude --version` prints (about 16:53Z and 18:38:42Z), not one",
            "R41-18": "record correction: v2's package check, manifest and append times are 12:51:06Z, 12:51:19Z and 12:51:24Z (file times)",
            "condition_C1": "now enforced in code (disk_precondition) in addition to the owner's confirmation"},
        "v2_nodes_equal": f"{eq} of {len(v2nodes)}"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="build_declaration_r42.py")
    ap.add_argument("command", choices=("show", "write", "fill_owner_digest", "verify_run_file", "write_authorization"))
    ap.add_argument("--digest")
    ap.add_argument("--run-sha")
    ap.add_argument("--nonce")
    ap.add_argument("--invocations", type=int, default=1)
    ap.add_argument("--nonces")
    args = ap.parse_args(argv)
    if args.command == "verify_run_file":
        r = verify_run_file(args.digest, args.run_sha)
        print(json.dumps(r, indent=1))
        return 0 if r["verified"] else 1
    if args.command == "fill_owner_digest":            # OWNER ONLY (never run by this task)
        frozen, fsha = frozen_bytes_checked()
        target = C.PACKAGE / C.RUN_NAME
        if target.exists():
            raise SystemExit("refused: the RUN file exists (one RUN file per declaration)")
        run = fill_owner_digest(frozen, args.digest)
        sha = C.write_once(target, run.decode("utf-8"))
        print(json.dumps({"frozen_sha256": fsha, "run_file": target.as_posix(), "run_sha256": sha}, indent=1))
        return 0
    if args.command == "write_authorization":          # OWNER ONLY (never run by this task)
        frozen, fsha = frozen_bytes_checked()
        run_path = C.PACKAGE / C.RUN_NAME
        run_decl = json.loads(run_path.read_text(encoding="utf-8"))
        digest = run_decl["authorization"]["owner_token_sha256"]
        check = verify_run_file(digest, args.run_sha, run_path)
        if not check["verified"]:
            raise SystemExit(f"refused: the RUN file does not verify: {check}")
        if args.invocations > 1:
            nonces = args.nonces.split(",") if args.nonces else [secrets.token_urlsafe(24) for _ in range(args.invocations)]
            text = authorization_text(args.run_sha, digest, nonces, frozen_sha=fsha, multi=True,
                                      bound=run_decl["resume_authorization"]["max_invocations_per_file"])
        else:
            text = authorization_text(args.run_sha, digest, [args.nonce or secrets.token_urlsafe(24)], frozen_sha=fsha)
        C.write_once(C.PACKAGE / C.AUTH_NAME, text)
        print(json.dumps({"authorization": (C.PACKAGE / C.AUTH_NAME).as_posix(), "declaration_sha256": args.run_sha,
                          "invocations_authorized": args.invocations}))
        return 0
    # show / write: the package harness checked against the binding first
    import subprocess  # noqa: F401
    binding_sha = C.sha256_file(C.BINDING42)
    man = json.loads(C.BINDING42.read_text(encoding="utf-8"))
    bad = [p for p, w in man["files"]["harness_r42_package"].items() if C.sha256_file(p) != w]
    if bad:
        raise C.PacketMismatch(f"PACKET MISMATCH: harness files differ from BINDING-MANIFEST-R42: {bad[:3]}")
    led = C.ledger_state()
    if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"]:
        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led['entries']}/{led['scopes']}/{led['limit_amendments']} (expected 483/17/0 and no scope {C.SCOPE!r})")
    if C.RUN_FOLDER.exists():
        raise C.PacketMismatch(f"refused: the run folder {C.RUN_FOLDER.as_posix()} already exists")
    for repo, head in (C.CANDIDATE, C.BASELINE):
        g = C.git_state(repo)
        if g["head"] != head or not g["clean"]:
            raise C.PacketMismatch(f"PACKET MISMATCH: {repo} {g}")
    declared_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    decl = build(declared_at, evidence())
    rh = rehash_all(decl)
    text = C.json_text(decl)
    if text.count(json.dumps(C.TOKEN_PLACEHOLDER)) != 1:
        raise RuntimeError("the placeholder must occur exactly once (as authorization.owner_token_sha256)")
    if C.DESKTOP_EP in text:
        raise RuntimeError("a Desktop path survived the re-pointing")
    import preflight_r32 as PF  # noqa: E402  (review42)
    mem = json.loads(text)
    mem["authorization"]["owner_token_sha256"] = C.DUMMY_DIGEST
    PF.validate_declaration(mem, C.PACKAGE / C.DECLARATION_NAME)        # in memory: every contract-5 key passes
    try:
        PF.validate_declaration(json.loads(text), C.PACKAGE / C.DECLARATION_NAME)
        raise RuntimeError("the frozen declaration as written must be refused (placeholder digest)")
    except PF.Refused as exc:
        assert "binds no owner token digest" in str(exc), exc
    if args.command == "show":
        sys.stdout.flush()
        sys.stdout.buffer.write(text.encode("utf-8"))
        print(json.dumps(rh), file=sys.stderr)
        return 0
    target, shafile = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE / "DECLARATION.sha256"
    if target.exists() or shafile.exists():
        raise SystemExit("refused: the declaration is written once; it exists")
    sha = C.write_once(target, text)
    C.write_once(shafile, f"{sha}  {C.DECLARATION_NAME}\n")
    print(json.dumps({"declaration": target.as_posix(), "sha256": sha, "bytes": len(text.encode("utf-8")), "declared_at_utc": declared_at,
                      "binding_manifest_sha256": binding_sha} | rh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
