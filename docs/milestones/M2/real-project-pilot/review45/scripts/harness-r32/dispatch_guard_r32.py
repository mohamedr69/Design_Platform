"""ORCH-05C (Review 34 RC-3 / R34-03): the ONLY path to a provider in the r32 runner -- a pinned, one-run dispatch guard.

The authorization path is PINNED: it is always <the declaration's own folder>/OWNER-DISPATCH-AUTHORIZATION.json (the
package root that holds the ORCH-07 declaration). No function, command-line argument or configuration key can name
another path (runner_r32 has no --auth-path; a lane configuration with "auth_path" is refused), and the declaration must
bind exactly that path under "authorization.path".

authorize(declaration_path, declaration_sha256, run_folder=..., invocation=..., action=preview|consume|verify) refuses
(raises DispatchRefused) unless ALL of the following hold:
  1. the declaration file exists and hashes to declaration_sha256 (64 hex), and it is not a dry exercise;
  2. the declaration binds authorization.path == the pinned path and an owner token DIGEST authorization.owner_token_sha256
     (64 hex); the token itself is never stored in any file;
  3. the pinned authorization file exists and is a JSON object with
       declaration_sha256 == the verified declaration hash        (missing -> refused),
       owner_token_sha256 == the digest the declaration binds     (different -> refused),
       authorized_by == "owner",
       nonce: a one-run nonce, 16-128 characters [A-Za-z0-9_-];
  4. the owner presents the token at run time in the environment variable R34_OWNER_DISPATCH_TOKEN, and its sha256 equals
     that digest (the token is compared by digest only and is never written anywhere by this harness);
  5. one run, one nonce: the nonce is CONSUMED by the runner on first use -- an O_EXCL record
     <run folder>/authorization/consumed-<sha256(nonce)[:32]>.json naming the declaration hash, the authorization file's own
     sha256, the stamp and the invocation number. action 'preview' / 'consume' (the runner, once per invocation) refuse
     a nonce that already has a record (reuse); action 'verify' (every lane, and before EVERY request) requires the record
     of THIS invocation with the same authorization hash (a different, edited or reused authorization is refused). A
     resume is a new invocation and needs the owner's new authorization (a fresh nonce) for the same declaration.
GuardedProvider(build_inner, declaration_path, declaration_sha256, response_cls, run_folder=, invocation=) calls
authorize(action='verify') before EVERY dispatch and builds the real provider only after the first success; a refused
dispatch returns 'dispatch_refused' and never reaches a provider. Dry mode never builds any provider: DryRefusingProvider
answers every request 'dry_refused'. No provider, model, network or ledger is touched by this module, and it never
creates an authorization file (the owner writes it; this task creates none).

ORCH-10 (R42; A-11 section 4): ONE APPROVAL FOR ALL PLANNED RESUMPTIONS -- a separable feature, OFF unless the owner
writes it into the authorization file. Two forms of the pinned file are accepted, each with EXACTLY these keys (any other
key is refused: an authorization can never name, raise, reset or re-create an allowance, the parent budget, the window,
the scope or any limit):
  per-invocation (the v2 behaviour, unchanged):  authorized_by, declaration_sha256, owner_token_sha256, nonce
  multi-invocation:                              authorized_by, declaration_sha256, owner_token_sha256,
                                                 invocations_authorized N, nonces [N distinct one-run nonces]
In the multi form 1 <= N <= the declaration's resume_authorization.max_invocations_per_file (the v3 declaration binds 3;
a declaration that binds no such bound refuses every multi-invocation file). Each invocation consumes EXACTLY ONE nonce,
the first unconsumed one in list order (consumption record as before, now also naming the nonce's index and N); a nonce
consumed out of order, a nonce consumed under another authorization file (reused), a duplicate nonce, or N above the
bound is refused; once all N are consumed, invocation N+1 needs a NEW authorization file. 'verify' finds the record of
THIS invocation under THIS file's hash. A file naming another declaration hash (for example the frozen hash instead of
the RUN hash) is refused exactly as before."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re

AUTH_NAME = "OWNER-DISPATCH-AUTHORIZATION.json"
TOKEN_ENV = "R34_OWNER_DISPATCH_TOKEN"
CONSUMED_DIR = "authorization"
_HEX64 = re.compile(r"[0-9a-f]{64}")
_NONCE = re.compile(r"[A-Za-z0-9_-]{16,128}")
SINGLE_KEYS = frozenset({"authorized_by", "declaration_sha256", "owner_token_sha256", "nonce"})
MULTI_KEYS = frozenset({"authorized_by", "declaration_sha256", "owner_token_sha256", "invocations_authorized", "nonces"})
MULTI_BOUND_HARD_MAX = 3                       # ORCH-10: the v3 declaration binds 3; no declaration may bind more


class DispatchRefused(RuntimeError):
    pass


def _sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _norm(p) -> str:
    return pathlib.Path(p).resolve().as_posix().lower()


def pinned_path(declaration_path) -> pathlib.Path:
    """The one place an authorization may live: beside the declaration, at its package root."""
    return pathlib.Path(declaration_path).resolve().parent / AUTH_NAME


def consumption_path(run_folder, nonce: str) -> pathlib.Path:
    """The nonce's consumption record (named by the first 32 hex of sha256(nonce): short Windows paths; the full digest is inside)."""
    return pathlib.Path(run_folder) / CONSUMED_DIR / f"consumed-{hashlib.sha256(nonce.encode('utf-8')).hexdigest()[:32]}.json"


def _load_declaration(declaration_path, declaration_sha256) -> dict:
    if not declaration_path or not declaration_sha256 or not _HEX64.fullmatch(str(declaration_sha256)):
        raise DispatchRefused("refused: no verified declaration (path and 64-hex sha256 are both required)")
    p = pathlib.Path(declaration_path)
    if not p.is_file() or _sha(p) != declaration_sha256:
        raise DispatchRefused("refused: the declaration is missing or does not hash to the verified sha256")
    try:
        decl = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise DispatchRefused(f"refused: the declaration is not readable JSON ({exc})") from exc
    if not isinstance(decl, dict) or decl.get("dry_exercise"):
        raise DispatchRefused("refused: the declaration is not a live ORCH-07 declaration")
    return decl


def _load_authorization(path: pathlib.Path):
    """(object, sha256) of the pinned authorization file, or refuse."""
    if not path.is_file():
        raise DispatchRefused(f"refused: no owner dispatch authorization ({path} does not exist)")
    raw = path.read_bytes()
    try:
        auth = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise DispatchRefused(f"refused: the authorization is not readable JSON ({exc})") from exc
    return auth, hashlib.sha256(raw).hexdigest()


def validate(decl: dict, declaration_path, declaration_sha256: str, auth, token) -> dict:
    """Pure checks 2-4 on in-memory objects (no file is read or written here)."""
    pinned = pinned_path(declaration_path)
    bound = decl.get("authorization") if isinstance(decl.get("authorization"), dict) else {}
    if not bound.get("path") or _norm(bound["path"]) != _norm(pinned):
        raise DispatchRefused(f"refused: the declaration must bind the pinned authorization path {pinned.as_posix()} (it binds {bound.get('path')!r})")
    digest = str(bound.get("owner_token_sha256") or "")
    if not _HEX64.fullmatch(digest):
        raise DispatchRefused("refused: the declaration binds no owner token digest")
    if not isinstance(auth, dict):
        raise DispatchRefused("refused: the authorization is not a JSON object")
    named = str(auth.get("declaration_sha256") or "")
    if not _HEX64.fullmatch(named):
        raise DispatchRefused("refused: the authorization names no declaration sha256")
    if named != declaration_sha256:
        raise DispatchRefused(f"refused: the authorization names declaration {named[:12]}..., the runner verified {declaration_sha256[:12]}...")
    if str(auth.get("owner_token_sha256") or "") != digest:
        raise DispatchRefused("refused: the authorization's owner token digest differs from the digest the declaration binds")
    if auth.get("authorized_by") != "owner":
        raise DispatchRefused("refused: the authorization is not the owner's")
    nonces, n_auth = _nonces_of(decl, auth)
    if not token:
        raise DispatchRefused(f"refused: the owner token was not presented ({TOKEN_ENV} is not set)")
    if hashlib.sha256(str(token).encode("utf-8")).hexdigest() != digest:
        raise DispatchRefused("refused: the presented owner token does not match the bound digest")
    return {"nonce": nonces[0], "nonce_sha256": hashlib.sha256(nonces[0].encode("utf-8")).hexdigest(), "owner_token_sha256": digest,
            "nonces": nonces, "invocations_authorized": n_auth, "form": "multi" if n_auth is not None else "single"}


def max_invocations_per_file(decl: dict) -> int | None:
    """The declaration's bound for the multi-invocation form (resume_authorization.max_invocations_per_file), or None."""
    ra = decl.get("resume_authorization") if isinstance(decl.get("resume_authorization"), dict) else {}
    v = ra.get("max_invocations_per_file")
    return v if isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= MULTI_BOUND_HARD_MAX else None


def _nonces_of(decl: dict, auth: dict) -> tuple[list, int | None]:
    """(the file's nonces in order, N or None for the per-invocation form); refuses every malformed or widened file."""
    keys = set(auth)
    if "invocations_authorized" in auth or "nonces" in auth:
        extra = sorted(keys - MULTI_KEYS)
        if extra or keys != MULTI_KEYS:
            raise DispatchRefused(f"refused: a multi-invocation authorization holds exactly {sorted(MULTI_KEYS)} "
                                  f"(extra {extra}, missing {sorted(MULTI_KEYS - keys)}); it can never name an allowance, budget, window or scope")
        n = auth["invocations_authorized"]
        bound = max_invocations_per_file(decl)
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise DispatchRefused(f"refused: invocations_authorized must be a positive integer ({n!r})")
        if bound is None:
            raise DispatchRefused("refused: the declaration binds no resume_authorization.max_invocations_per_file; only the per-invocation form is accepted")
        if n > bound:
            raise DispatchRefused(f"refused: invocations_authorized {n} is above the declared bound {bound}")
        nonces = auth["nonces"]
        if not isinstance(nonces, list) or len(nonces) != n or any(not isinstance(x, str) or not _NONCE.fullmatch(x) for x in nonces):
            raise DispatchRefused(f"refused: nonces must be exactly {n} one-run nonces (16-128 characters A-Z a-z 0-9 _ -)")
        if len(set(nonces)) != len(nonces):
            raise DispatchRefused("refused: the authorization repeats a nonce (one nonce is one invocation)")
        return list(nonces), n
    extra = sorted(keys - SINGLE_KEYS)
    if extra:
        raise DispatchRefused(f"refused: an authorization holds exactly {sorted(SINGLE_KEYS)} (extra {extra}); "
                              "it can never name an allowance, budget, window or scope")
    nonce = str(auth.get("nonce") or "")
    if not _NONCE.fullmatch(nonce):
        raise DispatchRefused("refused: the authorization carries no one-run nonce (16-128 characters A-Z a-z 0-9 _ -)")
    return [nonce], None


def _record_of(run_folder, nonce):
    p = consumption_path(run_folder, nonce)
    if not p.is_file():
        return p, None
    try:
        return p, json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return p, {"unreadable": True}


ACTIONS = ("preview", "consume", "verify")


def authorize(declaration_path, declaration_sha256, *, run_folder, invocation: int, action: str = "verify", stamp: str | None = None,
              kind: str = "fresh", token=None) -> dict:
    """action 'preview' (runner, before it creates or opens the run folder: everything except that the nonce must still be
    UNCONSUMED; writes nothing), 'consume' (runner, once per invocation: the same, then the O_EXCL consumption record),
    'verify' (lanes and every request: the record of THIS invocation must exist with the same authorization hash)."""
    if action not in ACTIONS:
        raise DispatchRefused(f"refused: unknown guard action {action!r}")
    decl = _load_declaration(declaration_path, declaration_sha256)
    path = pinned_path(declaration_path)
    auth, auth_sha = _load_authorization(path)
    v = validate(decl, declaration_path, declaration_sha256, auth, token if token is not None else os.environ.get(TOKEN_ENV))
    if not run_folder:
        raise DispatchRefused("refused: no run folder (an authorization is consumed into the declaration's run folder)")
    if v["form"] == "multi":
        return _authorize_multi(v, auth_sha, path, declaration_sha256, run_folder=run_folder, invocation=invocation, action=action, stamp=stamp,
                                kind=kind)
    rec_path = consumption_path(run_folder, v["nonce"])
    record = {"nonce_sha256": v["nonce_sha256"], "authorization_sha256": auth_sha, "authorization_path": path.as_posix(),
              "declaration_sha256": declaration_sha256, "stamp": stamp, "invocation": int(invocation), "kind": kind}
    if action in ("preview", "consume"):
        if rec_path.exists():
            raise DispatchRefused(f"refused: this authorization's nonce was already consumed ({rec_path.name}); one authorization is one run invocation")
    if action == "consume":
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(rec_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise DispatchRefused("refused: this authorization's nonce was already consumed (concurrent use)") from exc
        record["consumed_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        os.write(fd, (json.dumps(record, sort_keys=True, indent=1) + "\n").encode("utf-8"))
        os.close(fd)
    elif action == "verify":
        if not rec_path.is_file():
            raise DispatchRefused("refused: the authorization has not been consumed by a run of this declaration (a lane never consumes one)")
        got = json.loads(rec_path.read_text(encoding="utf-8"))
        if got.get("authorization_sha256") != auth_sha or got.get("declaration_sha256") != declaration_sha256 or int(got.get("invocation", -1)) != int(invocation):
            raise DispatchRefused("refused: the consumed record belongs to another authorization, declaration or invocation")
    return {"authorized": True, "action": action, "declaration_sha256": declaration_sha256, "authorization_sha256": auth_sha, "path": path.as_posix(),
            "nonce_sha256": v["nonce_sha256"], "consumption_record": rec_path.as_posix(), "invocation": int(invocation), "form": "single"}


def _authorize_multi(v, auth_sha, path, declaration_sha256, *, run_folder, invocation, action, stamp, kind) -> dict:
    """ORCH-10: the multi-invocation form -- exactly one nonce per invocation, consumed in list order (module docstring)."""
    nonces, n = v["nonces"], v["invocations_authorized"]
    recs = [(i, x) + _record_of(run_folder, x) for i, x in enumerate(nonces)]
    for i, _x, p, r in recs:
        if r is not None and (r.get("unreadable") or r.get("authorization_sha256") != auth_sha or r.get("declaration_sha256") != declaration_sha256):
            raise DispatchRefused(f"refused: nonce {i + 1} of this authorization was consumed under another authorization or declaration "
                                  f"({p.name}): a consumed nonce is never reusable")
    consumed = [i for i, _x, _p, r in recs if r is not None]
    if consumed != list(range(len(consumed))):
        raise DispatchRefused(f"refused: the nonces of this authorization were consumed out of order (consumed {[i + 1 for i in consumed]}); "
                              "each invocation consumes the next nonce in list order")
    mine = [(i, x, p, r) for i, x, p, r in recs if r is not None and int(r.get("invocation", -1)) == int(invocation)]
    base = {"authorized": True, "action": action, "declaration_sha256": declaration_sha256, "authorization_sha256": auth_sha, "path": path.as_posix(),
            "invocation": int(invocation), "form": "multi", "invocations_authorized": n, "nonces_consumed_before": len(consumed)}
    if action == "verify":
        if len(mine) != 1:
            raise DispatchRefused("refused: the authorization has not been consumed by a run of this declaration for this invocation "
                                  "(a lane never consumes one)")
        i, x, p, _r = mine[0]
        return base | {"nonce_index": i + 1, "nonce_sha256": hashlib.sha256(x.encode("utf-8")).hexdigest(), "consumption_record": p.as_posix()}
    if mine:
        raise DispatchRefused(f"refused: invocation {invocation} already consumed nonce {mine[0][0] + 1} of this authorization "
                              "(one invocation consumes exactly one nonce)")
    k = len(consumed)
    if k >= n:
        raise DispatchRefused(f"refused: all {n} nonces of this authorization were consumed; invocation {invocation} needs a NEW authorization file")
    nonce = nonces[k]
    rec_path = consumption_path(run_folder, nonce)
    out = base | {"nonce_index": k + 1, "nonce_sha256": hashlib.sha256(nonce.encode("utf-8")).hexdigest(), "consumption_record": rec_path.as_posix()}
    if action == "consume":
        record = {"nonce_sha256": out["nonce_sha256"], "authorization_sha256": auth_sha, "authorization_path": path.as_posix(),
                  "declaration_sha256": declaration_sha256, "stamp": stamp, "invocation": int(invocation), "kind": kind,
                  "nonce_index": k + 1, "invocations_authorized": n, "form": "multi",
                  "consumed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(rec_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise DispatchRefused("refused: this nonce was already consumed (concurrent use)") from exc
        os.write(fd, (json.dumps(record, sort_keys=True, indent=1) + "\n").encode("utf-8"))
        os.close(fd)
    return out


def check(declaration_path=None, declaration_sha256=None, **kw) -> dict:
    """authorize() as a report, never raising (preflight and dry-run evidence). Never consumes."""
    if kw.get("action") == "consume":
        kw["action"] = "preview"
    kw.setdefault("run_folder", None)
    kw.setdefault("invocation", 0)
    try:
        return authorize(declaration_path, declaration_sha256, **kw)
    except DispatchRefused as exc:
        return {"authorized": False, "reason": str(exc)}
    except TypeError as exc:
        return {"authorized": False, "reason": f"refused: {exc}"}


class GuardedProvider:
    """The live dispatch path: authorize() before every request; the inner (real) provider is built only after it passes.
    token: the owner token the lane read (and removed) from its environment at start, so the provider's own subprocesses
    never inherit it; None reads R34_OWNER_DISPATCH_TOKEN at each request."""
    name, ready, status = "guarded", True, "r34 pinned one-run dispatch guard"

    def __init__(self, build_inner, declaration_path, declaration_sha256, response_cls, *, run_folder, invocation, token=None):
        self.build_inner, self.declaration_path, self.declaration_sha256, self.response_cls = build_inner, declaration_path, declaration_sha256, response_cls
        self.run_folder, self.invocation, self._token = run_folder, invocation, token
        self.inner = None
        self.refused = 0
        self.dispatched = 0

    def complete(self, request):
        try:
            authorize(self.declaration_path, self.declaration_sha256, run_folder=self.run_folder, invocation=self.invocation, action="verify",
                      token=self._token)
        except DispatchRefused as exc:
            self.refused += 1
            return self.response_cls(data=None, model="guard", error="dispatch_refused", error_detail=str(exc))
        if self.inner is None:
            self.inner = self.build_inner()
        self.dispatched += 1
        return self.inner.complete(request)


class DryRefusingProvider:
    """Dry mode: no provider exists; every request is answered 'dry_refused' (never a model request)."""
    name, ready, status = "dry-refusing", True, "r34 dry run: refuses every request; no provider is built"

    def __init__(self, response_cls):
        self.response_cls = response_cls
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return self.response_cls(data=None, model="dry", error="dry_refused", error_detail="dry run: no provider, no model request")
