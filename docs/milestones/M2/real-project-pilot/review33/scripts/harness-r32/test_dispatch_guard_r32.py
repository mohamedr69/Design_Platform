"""dispatch_guard_r32: the provider path refuses unless the owner's authorization names the ORCH-07 declaration hash and a
budget token. The real authorization file is never created; positive cases use a temporary file only.
Run: python -m pytest -q test_dispatch_guard_r32.py"""
import hashlib
import json

import pytest

import dispatch_guard_r32 as DG


class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
        self.data, self.model, self.error, self.error_detail = data, model, error, error_detail

    @property
    def ok(self):
        return self.error is None


def _auth(tmp_path, **over):
    decl = tmp_path / "DECLARATION.json"
    decl.write_text('{"name": "test declaration"}', encoding="utf-8", newline="\n")
    sha = hashlib.sha256(decl.read_bytes()).hexdigest()
    rec = {"declaration_sha256": sha, "declaration_path": str(decl), "owner_budget_token": "owner-token-test", "authorized_by": "owner"} | over
    p = tmp_path / "OWNER-DISPATCH-AUTHORIZATION.json"
    p.write_text(json.dumps(rec), encoding="utf-8", newline="\n")
    return p, sha, decl


def test_the_real_authorization_file_does_not_exist_and_the_guard_refuses():
    assert not DG.AUTH_PATH.exists(), "ORCH-05.1 must never create the owner's authorization"
    with pytest.raises(DG.DispatchRefused, match="no owner dispatch authorization"):
        DG.authorize("0" * 64)
    assert DG.check(None)["authorized"] is False


@pytest.mark.parametrize("over,given,match", [
    ({}, "f" * 64, "names declaration"),
    ({"owner_budget_token": ""}, None, "no owner budget token"),
    ({"authorized_by": "assistant"}, None, "not the owner's"),
    ({"declaration_sha256": "not-a-hash"}, None, "names no declaration"),
])
def test_every_incomplete_or_mismatched_authorization_is_refused(tmp_path, over, given, match):
    p, sha, _ = _auth(tmp_path, **over)
    with pytest.raises(DG.DispatchRefused, match=match):
        DG.authorize(given or sha, auth_path=p)


def test_no_declaration_hash_given_is_refused(tmp_path):
    p, sha, _ = _auth(tmp_path)
    with pytest.raises(DG.DispatchRefused):
        DG.authorize(None, auth_path=p)


def test_a_changed_declaration_is_refused(tmp_path):
    p, sha, decl = _auth(tmp_path)
    decl.write_text('{"name": "changed"}', encoding="utf-8", newline="\n")
    with pytest.raises(DG.DispatchRefused, match="missing or changed"):
        DG.authorize(sha, auth_path=p)


def test_a_complete_temporary_authorization_passes(tmp_path):
    p, sha, _ = _auth(tmp_path)
    assert DG.authorize(sha, auth_path=p)["authorized"] is True


def test_the_guarded_provider_never_builds_the_real_provider_when_refused(tmp_path):
    def build():
        raise AssertionError("the real provider must not be built")

    g = DG.GuardedProvider(build, "a" * 64, Resp, auth_path=tmp_path / "missing.json")
    r = g.complete(object())
    assert r.error == "dispatch_refused" and g.refused == 1 and g.dispatched == 0 and g.inner is None


def test_the_guarded_provider_authorizes_before_every_request(tmp_path):
    p, sha, _ = _auth(tmp_path)
    calls = []

    class Inner:
        def complete(self, request):
            calls.append(request)
            return Resp(data={"ok": True})

    g = DG.GuardedProvider(Inner, sha, Resp, auth_path=p)
    assert g.complete("r1").ok and calls == ["r1"]
    p.unlink()
    assert g.complete("r2").error == "dispatch_refused" and calls == ["r1"], "a withdrawn authorization stops the next request"


def test_the_dry_stub_never_answers():
    d = DG.DryRefusingProvider(Resp)
    assert d.complete("x").error == "dry_refused" and d.calls == 1
