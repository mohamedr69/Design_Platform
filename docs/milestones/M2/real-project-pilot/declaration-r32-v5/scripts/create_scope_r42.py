"""ORCH-10 (R42PORT-IMPL; v2's create_scope_r40.py for the v3 declaration): the ONE command that creates the experiment's
ledger scope, with limits equal to the parent budget, and its PREVIEW and STATUS modes. Reviewed with the declaration; NOT
executed by this task (only 'preview' and the refusals were run).

  create_scope_r42.py preview
      read-only: prints the ledger, the scope name, the exact limits, the exact application call it would make, and every
      precondition with its current state; creates nothing (the AI ledger is opened file:...?mode=ro only).
  create_scope_r42.py create --frozen-sha <frozen declaration sha256> --run-sha <RUN declaration sha256>
      OWNER ONLY, after the budget authorization, immediately before the first invocation, with the token in
      R34_OWNER_DISPATCH_TOKEN. Refuses (creating nothing) unless, in this order:
        1. the owner's authorization file exists at the pinned path PILOT/declaration-r32-v5/OWNER-DISPATCH-AUTHORIZATION.json (R43-44);
        2. --frozen-sha equals the frozen declaration file's sha256 and DECLARATION.sha256;
        3. the RUN file exists, hashes to --run-sha (which is not the frozen hash) and equals the frozen bytes with ONLY the
           placeholder replaced by the digest it binds (build_declaration_r42.fill_owner_digest);
        4. the authorization names the RUN hash (never a frozen hash), the same digest, authorized_by owner and its nonce(s)
           in either accepted form, and the presented token's sha256 equals the digest (dispatch_guard_r32.validate, pure;
           nothing is consumed here -- the runner consumes one nonce per invocation);
        5. the run folder does not exist (the scope is created once, before the first invocation; never for a resume);
        6. the bound harness verifies (BINDING-MANIFEST-R45-HARNESS, every bound file; R43-44) and the RUN declaration passes contract 5;
        7. ORCH-10: the bound interpreter runs this command, the pinned CLI FILE hashes to the declared sha256 (read as
           bytes, never executed) and drive C holds at least the declared floor (2 GiB; condition C1, R41-10) -- the scope's
           7-day clock is never started on a machine that cannot run the invocation;
        8. the application's ledger module is the bound one (ledger.py d9f92297..., equal in both trees);
        9. the AI ledger exists and holds NO scope of that name;
      then it creates the scope through the application's own code -- app.ai.ledger.Ledger(path, scope, Limits(**limits)) of
      the candidate tree -- and verifies read-only: one more scope, the same entries and amendments, the scope's limits equal,
      breaker null, 0 entries, and preflight_r32.verify_ledger_scope passes. It prints the result (no file is written).
  create_scope_r42.py status
      read-only: the declared scope's state -- after the creation and before every resume.
The token is never printed or written. No provider, model or network is touched."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import sqlite3
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_declaration_r42 as BD  # noqa: E402
import r42common as C  # noqa: E402

APPLICATION_LEDGER_PY = C.CANDIDATE_BACKEND / "app" / "ai" / "ledger.py"
APPLICATION_LEDGER_PY_SHA = "d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca"


class ScopeRefused(RuntimeError):
    pass


def harness():
    man = json.loads(C.BINDING45.read_text(encoding="utf-8"))          # R43-44: the review45 harness manifest and group
    bad = [p for p, w in man["files"][C.HARNESS_GROUP].items() if C.sha256_file(p) != w]
    if bad:
        raise ScopeRefused(f"refused: PACKET MISMATCH: harness files differ: {bad[:3]}")
    C.check_run_copy()
    if str(C.HARNESS42) not in sys.path:
        sys.path.insert(0, str(C.HARNESS42))
    import dispatch_guard_r32 as DG  # noqa: E402
    import preflight_r32 as PF  # noqa: E402
    C.declared_here(PF)                                                # R43-40
    return DG, PF


def _ro_scope(ledger_path, scope) -> dict:
    p = pathlib.Path(ledger_path)
    if not p.is_file():
        raise ScopeRefused(f"refused: the ledger {p.as_posix()} does not exist")
    con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    try:
        row = con.execute("select limits, breaker, created_at from scopes where scope = ?", (scope,)).fetchone()
        entries = con.execute("select count(*) from entries where scope = ?", (scope,)).fetchone()[0]
        return {"exists": row is not None, "limits": json.loads(row[0]) if row else None, "breaker": row[1] if row else None,
                "created_at": row[2] if row else None, "entries": entries,
                "totals": {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                           "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0]}}
    finally:
        con.close()


def frozen_declaration() -> tuple[bytes, str, dict]:
    frozen, fsha = BD.frozen_bytes_checked()
    return frozen, fsha, json.loads(frozen.decode("utf-8"))


def preview() -> dict:
    frozen, fsha, decl = frozen_declaration()
    led = decl["ledger"]
    before = C.ledger_counts(led["path"])
    sc = _ro_scope(led["path"], led["scope"])
    run_path, auth_path = C.PACKAGE / C.RUN_NAME, C.PACKAGE / C.AUTH_NAME
    free = C.free_bytes(decl["disk_precondition"]["path"])
    pre = {
        "1 authorization file at the pinned path": {"path": auth_path.as_posix(), "exists": auth_path.exists(),
                                                     "state": "NOT YET (the owner writes it after the budget authorization)" if not auth_path.exists() else "present"},
        "2 frozen declaration hash": {"sha256": fsha, "equals_DECLARATION.sha256": True},
        "3 RUN file": {"path": run_path.as_posix(), "exists": run_path.exists(),
                       "state": "NOT YET (the owner writes it with build_declaration_r42.py fill_owner_digest)" if not run_path.exists() else "present"},
        "4 authorization names the RUN hash, the digest, the owner, its nonce(s); the token matches": {"state": "checked in create mode only"},
        "5 run folder absent": {"path": C.RUN_FOLDER.as_posix(), "absent": not C.RUN_FOLDER.exists()},
        "6 bound harness and contract 5": {"state": "checked in create mode (verify_binding R45 harness manifest; validate_declaration on the RUN file)"},
        "7 interpreter, CLI file, free disk": {"interpreter": decl["interpreter"]["path"], "cli_file": decl["model_identity"]["cli"]["path"],
                                               "cli_sha256": decl["model_identity"]["cli"]["sha256"], "free_bytes_now": free,
                                               "floor": decl["disk_precondition"]["min_free_bytes"], "floor_met_now": free >= decl["disk_precondition"]["min_free_bytes"],
                                               "state": "all three checked in create mode"},
        "8 application ledger module": {"path": APPLICATION_LEDGER_PY.as_posix(), "sha256": C.sha256_file(APPLICATION_LEDGER_PY),
                                        "equals_bound": C.sha256_file(APPLICATION_LEDGER_PY) == APPLICATION_LEDGER_PY_SHA},
        "9 no scope of that name": {"scope": led["scope"], "exists": sc["exists"]}}
    after = C.ledger_counts(led["path"])
    return {"mode": "preview (read-only; nothing created)", "ledger": led["path"], "scope": led["scope"], "limits": led["limits"],
            "would_call": (f"sys.path.insert(0, '{C.CANDIDATE_BACKEND.as_posix()}'); from app.ai.ledger import Ledger, Limits; "
                           f"Ledger({led['path']!r}, {led['scope']!r}, Limits(**{json.dumps(led['limits'], sort_keys=True)}))"),
            "would_create": {"scopes": f"{before['scopes']} -> {before['scopes'] + 1}", "entries": f"{before['entries']} (unchanged)",
                             "limit_amendments": f"{before['limit_amendments']} (unchanged)", "new_scope": {"limits": led["limits"], "breaker": None, "entries": 0}},
            "preconditions_now": pre, "ledger_before": before, "ledger_after": after, "ledger_unchanged": before == after,
            "frozen_declaration_sha256": fsha, "create_command": ("create_scope_r42.py create --frozen-sha <frozen hash> --run-sha <RUN hash>  "
                                                                  "(owner only; token in R34_OWNER_DISPATCH_TOKEN)")}


def check_create(frozen: bytes, frozen_sha_given: str, run_bytes: bytes | None, run_sha_given: str, auth, token, *, run_path, run_folder,
                 verify_bound: bool = True, free_fn=None) -> dict:
    """Preconditions 2-8 on in-memory objects (precondition 1, the file's existence, is the caller's). Raises ScopeRefused."""
    fsha = C.sha256_bytes(frozen)
    recorded = (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]
    if frozen_sha_given != fsha or fsha != recorded:
        raise ScopeRefused(f"refused: the frozen declaration hash differs (given {str(frozen_sha_given)[:12]}..., file {fsha[:12]}..., DECLARATION.sha256 {recorded[:12]}...)")
    if run_bytes is None:
        raise ScopeRefused(f"refused: no RUN declaration at {pathlib.Path(run_path).as_posix()}")
    rsha = C.sha256_bytes(run_bytes)
    if run_sha_given in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA, C.V4_SHA):     # R43-40 / R43-44: never a frozen or the executed v3 hash
        raise ScopeRefused("refused: the RUN hash given is a FROZEN hash (a frozen declaration is never used with the runner or the scope)")
    if rsha != run_sha_given:
        raise ScopeRefused(f"refused: the RUN declaration hashes to {rsha[:12]}..., not the given {str(run_sha_given)[:12]}...")
    run_decl = json.loads(run_bytes.decode("utf-8"))
    digest = str((run_decl.get("authorization") or {}).get("owner_token_sha256") or "")
    try:
        want = BD.fill_owner_digest(frozen, digest)
    except ValueError as exc:
        raise ScopeRefused(f"refused: the RUN declaration binds no valid digest ({exc})") from exc
    if run_bytes != want:
        raise ScopeRefused("refused: the RUN declaration is not the frozen declaration with only the digest filled in")
    DG, PF = harness()
    if isinstance(auth, dict) and str(auth.get("declaration_sha256") or "") in (fsha, C.V2_SHA, C.V3_SHA, C.V3_RUN_SHA, C.V4_SHA):   # R43-40 / R43-44
        raise ScopeRefused("refused: the authorization names a FROZEN hash; it must name the RUN hash")
    try:
        g = DG.validate(run_decl, run_path, rsha, auth, token)
    except DG.DispatchRefused as exc:
        raise ScopeRefused(str(exc)) from exc
    if pathlib.Path(run_folder).exists():
        raise ScopeRefused(f"refused: the run folder {pathlib.Path(run_folder).as_posix()} exists: the scope is created once, before the first invocation")
    if verify_bound:
        try:
            PF.verify_binding(C.BINDING45, run_decl.get("binding_manifest_sha256"))   # R43-44
        except PF.Refused as exc:
            raise ScopeRefused(str(exc)) from exc
    try:
        v = PF.validate_declaration(run_decl, run_path)
        checks = {"interpreter": PF.verify_interpreter(v["interpreter"]), "cli_file": PF.verify_cli(v["model_identity"]),
                  "free_disk": PF.verify_free_disk(v["disk_precondition"], free_fn=free_fn)}
    except PF.Refused as exc:
        raise ScopeRefused(str(exc)) from exc
    if C.sha256_file(APPLICATION_LEDGER_PY) != APPLICATION_LEDGER_PY_SHA:
        raise ScopeRefused("refused: the application's ledger module is not the bound one (PACKET MISMATCH)")
    return {"frozen_sha256": fsha, "run_sha256": rsha, "digest": digest, "nonce_sha256": g["nonce_sha256"], "ledger": v["ledger"],
            "authorization_form": g.get("form"), "checks": checks}


def create_scope(ok: dict, *, ledger_path=None) -> dict:
    """Create the scope through the application's own Ledger, then verify it read-only. ledger_path defaults to the
    declared ledger (tests pass a throwaway file, never the AI ledger)."""
    led = ok["ledger"]
    path = str(ledger_path or led["path"])
    before = _ro_scope(path, led["scope"])
    if before["exists"]:
        raise ScopeRefused(f"refused: a scope named {led['scope']!r} already exists in {path} (it is created once)")
    if str(C.CANDIDATE_BACKEND) not in sys.path:
        sys.path.insert(0, str(C.CANDIDATE_BACKEND))
    from app.ai.ledger import Ledger, Limits  # noqa: E402  (the bound application module, d9f92297...)
    Ledger(path, led["scope"], Limits(**led["limits"]))
    after = _ro_scope(path, led["scope"])
    problems = []
    if not after["exists"]:
        problems.append("the scope was not created")
    if after["limits"] != led["limits"]:
        problems.append(f"limits {after['limits']} != {led['limits']}")
    if after["breaker"] is not None:
        problems.append("the breaker is not closed")
    if after["entries"] != 0:
        problems.append("the new scope has entries")
    if after["totals"]["scopes"] != before["totals"]["scopes"] + 1 or after["totals"]["entries"] != before["totals"]["entries"] \
            or after["totals"]["limit_amendments"] != before["totals"]["limit_amendments"]:
        problems.append(f"the ledger changed beyond one new scope: {before['totals']} -> {after['totals']}")
    _DG, PF = harness()
    try:
        PF.verify_ledger_scope({**led, "path": path})
    except PF.Refused as exc:
        problems.append(str(exc))
    return {"created": not problems, "ledger": path, "scope": led["scope"], "limits": after["limits"], "breaker": after["breaker"], "entries": after["entries"],
            "created_at": after["created_at"], "totals_before": before["totals"], "totals_after": after["totals"], "problems": problems,
            "next": "start the first invocation now (RUNBOOK section 5.1): the scope's elapsed_s counts from its creation"}


def status() -> dict:
    _frozen, fsha, decl = frozen_declaration()
    led = decl["ledger"]
    sc = _ro_scope(led["path"], led["scope"])
    return {"mode": "status (read-only)", "frozen_declaration_sha256": fsha, "ledger": led["path"], "scope": led["scope"], "exists": sc["exists"],
            "limits_equal_declared": sc["limits"] == led["limits"], "limits": sc["limits"], "breaker": sc["breaker"], "scope_entries": sc["entries"],
            "ledger_totals": sc["totals"], "created_at_utc": None if sc["created_at"] is None else
            datetime.datetime.fromtimestamp(sc["created_at"], datetime.timezone.utc).isoformat(timespec="seconds"),
            "free_bytes_now": C.free_bytes(decl["disk_precondition"]["path"]), "disk_floor": decl["disk_precondition"]["min_free_bytes"]}


def main(argv=None) -> int:
    a = argparse.ArgumentParser(prog="create_scope_r42.py")
    a.add_argument("command", choices=("preview", "create", "status"))
    a.add_argument("--frozen-sha")
    a.add_argument("--run-sha")
    args = a.parse_args(argv)
    if args.command == "preview":
        print(json.dumps(preview(), indent=1, sort_keys=True))
        return 0
    if args.command == "status":
        print(json.dumps(status(), indent=1, sort_keys=True))
        return 0
    auth_path = C.PACKAGE / C.AUTH_NAME
    try:
        if not auth_path.is_file():
            raise ScopeRefused(f"refused: no owner dispatch authorization ({auth_path.as_posix()} does not exist)")
        if not args.frozen_sha or not args.run_sha:
            raise ScopeRefused("refused: create needs --frozen-sha and --run-sha")
        try:
            auth = json.loads(auth_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ScopeRefused(f"refused: the authorization is not readable JSON ({exc})") from exc
        frozen = (C.PACKAGE / C.DECLARATION_NAME).read_bytes()
        run_path = C.PACKAGE / C.RUN_NAME
        run_bytes = run_path.read_bytes() if run_path.is_file() else None
        ok = check_create(frozen, args.frozen_sha, run_bytes, args.run_sha, auth, os.environ.get(C.TOKEN_ENV), run_path=run_path, run_folder=C.RUN_FOLDER)
        res = create_scope(ok)
    except ScopeRefused as exc:
        print(json.dumps({"created": False, "refused": str(exc)}, indent=1))
        return 3
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0 if res["created"] else 4


if __name__ == "__main__":
    sys.exit(main())
