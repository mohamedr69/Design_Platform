"""ORCH-05.1 (Review 33 C-5): the ONLY path to a provider in the r32 runner.

authorize(declaration_sha256) refuses (raises DispatchRefused) unless ALL of the following hold:
  1. PILOT/review33/OWNER-DISPATCH-AUTHORIZATION.json exists (this task never creates it);
  2. it is a JSON object whose "declaration_sha256" is a 64-hex sha256 EQUAL to the declaration hash the runner verified
     (the ORCH-07 declaration), and the runner was given that hash;
  3. it carries a non-empty "owner_budget_token" and "authorized_by" == "owner";
  4. the declaration file named in it ("declaration_path") exists and still hashes to that sha256.
GuardedProvider(build_inner, declaration_sha256) calls authorize() before EVERY dispatch and builds the real provider only
after the first successful authorization; a refused dispatch returns a failure 'dispatch_refused' and never reaches a
provider. Dry mode never builds any provider: DryRefusingProvider answers every request with 'dry_refused' and counts it.
No provider, model, network or ledger is touched by this module."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

AUTH_PATH = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review33/OWNER-DISPATCH-AUTHORIZATION.json")
_HEX64 = re.compile(r"[0-9a-f]{64}")


class DispatchRefused(RuntimeError):
    pass


def _sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def authorize(declaration_sha256: str | None, *, auth_path=None) -> dict:
    path = pathlib.Path(auth_path) if auth_path is not None else AUTH_PATH
    if not path.exists():
        raise DispatchRefused(f"refused: no owner dispatch authorization ({path} does not exist)")
    try:
        auth = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise DispatchRefused(f"refused: the authorization is not readable JSON ({exc})") from exc
    if not isinstance(auth, dict):
        raise DispatchRefused("refused: the authorization is not a JSON object")
    named = str(auth.get("declaration_sha256") or "")
    if not _HEX64.fullmatch(named):
        raise DispatchRefused("refused: the authorization names no declaration sha256")
    if not declaration_sha256 or named != declaration_sha256:
        raise DispatchRefused(f"refused: the authorization names declaration {named[:12]}..., the runner verified {str(declaration_sha256)[:12]}...")
    if not str(auth.get("owner_budget_token") or "").strip():
        raise DispatchRefused("refused: no owner budget token")
    if auth.get("authorized_by") != "owner":
        raise DispatchRefused("refused: the authorization is not the owner's")
    decl = auth.get("declaration_path")
    if not decl or not pathlib.Path(decl).exists() or _sha(decl) != named:
        raise DispatchRefused("refused: the declaration named by the authorization is missing or changed")
    return {"authorized": True, "declaration_sha256": named, "authorization_sha256": _sha(path), "path": str(path)}


def check(declaration_sha256: str | None, *, auth_path=None) -> dict:
    """authorize() as a report, never raising (preflight and dry-run evidence)."""
    try:
        return authorize(declaration_sha256, auth_path=auth_path)
    except DispatchRefused as exc:
        return {"authorized": False, "reason": str(exc)}


class GuardedProvider:
    """The live dispatch path: authorize() before every request; the inner (real) provider is built only after it passes."""
    name, ready, status = "guarded", True, "r33 dispatch guard"

    def __init__(self, build_inner, declaration_sha256, response_cls, *, auth_path=None):
        self.build_inner, self.declaration_sha256, self.response_cls, self.auth_path = build_inner, declaration_sha256, response_cls, auth_path
        self.inner = None
        self.refused = 0
        self.dispatched = 0

    def complete(self, request):
        try:
            authorize(self.declaration_sha256, auth_path=self.auth_path)
        except DispatchRefused as exc:
            self.refused += 1
            return self.response_cls(data=None, model="guard", error="dispatch_refused", error_detail=str(exc))
        if self.inner is None:
            self.inner = self.build_inner()
        self.dispatched += 1
        return self.inner.complete(request)


class DryRefusingProvider:
    """Dry mode: no provider exists; every request is answered 'dry_refused' (never a model request)."""
    name, ready, status = "dry-refusing", True, "r33 dry run: refuses every request; no provider is built"

    def __init__(self, response_cls):
        self.response_cls = response_cls
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return self.response_cls(data=None, model="dry", error="dry_refused", error_detail="dry run: no provider, no model request")
