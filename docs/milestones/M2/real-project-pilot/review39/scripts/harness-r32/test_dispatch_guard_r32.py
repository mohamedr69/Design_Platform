"""dispatch_guard_r32 (Review 34 RC-3 / R34-03): the pinned, one-run dispatch guard. NO authorization file is created by any
test (the task forbids it): authorization contents are in-memory objects, given to validate() or returned by a
monkeypatched loader; the only files written are temporary declarations and consumption records under pytest's tmp_path.
Run: python -m pytest -q test_dispatch_guard_r32.py"""
import hashlib
import inspect
import json
import pathlib

import pytest

import dispatch_guard_r32 as DG

TOKEN = "test-owner-token-not-real"
DIGEST = hashlib.sha256(TOKEN.encode()).hexdigest()
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")


class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
        self.data, self.model, self.error, self.error_detail = data, model, error, error_detail

    @property
    def ok(self):
        return self.error is None


def _decl(tmp_path, **over):
    """A temporary declaration (NOT an authorization) binding the pinned path and the token digest."""
    p = tmp_path / "pkg" / "DECLARATION.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"name": "test declaration", "authorization": {"path": (p.parent / DG.AUTH_NAME).as_posix(), "owner_token_sha256": DIGEST}} | over
    p.write_text(json.dumps(rec), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest(), rec


def _auth(sha, **over):
    """An in-memory authorization object (never written to a file)."""
    return {"declaration_sha256": sha, "owner_token_sha256": DIGEST, "authorized_by": "owner", "nonce": "nonce-0123456789abcdef"} | over


def _patch_loader(monkeypatch, obj, auth_sha="e" * 64):
    monkeypatch.setattr(DG, "_load_authorization", lambda path: (obj, auth_sha))


# ---- pinned path ------------------------------------------------------------------------------------------------------------
def test_no_authorization_file_exists_and_the_guard_refuses_without_one(tmp_path):
    for p in (PILOT / "review33" / DG.AUTH_NAME, PILOT / "review34" / DG.AUTH_NAME):
        assert not p.exists(), "ORCH-05C must never create the owner's authorization"
    decl, sha, _ = _decl(tmp_path)
    with pytest.raises(DG.DispatchRefused, match="no owner dispatch authorization"):
        DG.authorize(decl, sha, run_folder=tmp_path / "run", invocation=1, token=TOKEN)
    assert DG.check(None, None)["authorized"] is False


def test_the_authorization_path_is_pinned_and_cannot_be_given(tmp_path):
    decl, sha, _ = _decl(tmp_path)
    assert DG.pinned_path(decl) == decl.resolve().parent / "OWNER-DISPATCH-AUTHORIZATION.json"
    for fn in (DG.authorize, DG.check, DG.GuardedProvider.__init__):
        assert not any("path" in name and name != "declaration_path" for name in inspect.signature(fn).parameters), fn
    with pytest.raises(TypeError):
        DG.authorize(decl, sha, run_folder=tmp_path, invocation=1, auth_path=tmp_path / "elsewhere.json")


def test_wrong_path_bound_by_the_declaration_is_refused(tmp_path):
    decl, sha, rec = _decl(tmp_path, authorization={"path": (tmp_path / "elsewhere" / DG.AUTH_NAME).as_posix(), "owner_token_sha256": DIGEST})
    with pytest.raises(DG.DispatchRefused, match="must bind the pinned authorization path"):
        DG.validate(rec, decl, sha, _auth(sha), TOKEN)


# ---- content -----------------------------------------------------------------------------------------------------------------
def test_missing_declaration_hash_is_refused(tmp_path):
    decl, sha, rec = _decl(tmp_path)
    a = _auth(sha)
    del a["declaration_sha256"]
    with pytest.raises(DG.DispatchRefused, match="names no declaration sha256"):
        DG.validate(rec, decl, sha, a, TOKEN)
    with pytest.raises(DG.DispatchRefused, match="no verified declaration"):
        DG.authorize(decl, None, run_folder=tmp_path, invocation=1)


def test_a_different_declaration_hash_is_refused(tmp_path):
    decl, sha, rec = _decl(tmp_path)
    with pytest.raises(DG.DispatchRefused, match="names declaration"):
        DG.validate(rec, decl, sha, _auth("f" * 64), TOKEN)
    decl.write_text('{"changed": true}', encoding="utf-8", newline="\n")
    with pytest.raises(DG.DispatchRefused, match="does not hash to the verified sha256"):
        DG.authorize(decl, sha, run_folder=tmp_path, invocation=1, token=TOKEN)


def test_wrong_digest_is_refused(tmp_path):
    decl, sha, rec = _decl(tmp_path)
    with pytest.raises(DG.DispatchRefused, match="digest differs from the digest the declaration binds"):
        DG.validate(rec, decl, sha, _auth(sha, owner_token_sha256="0" * 64), TOKEN)
    decl2, sha2, rec2 = _decl(tmp_path / "x", authorization={"path": (tmp_path / "x" / "pkg" / DG.AUTH_NAME).as_posix()})
    with pytest.raises(DG.DispatchRefused, match="binds no owner token digest"):
        DG.validate(rec2, decl2, sha2, _auth(sha2), TOKEN)


def test_a_missing_or_wrong_owner_token_is_refused(tmp_path):
    decl, sha, rec = _decl(tmp_path)
    with pytest.raises(DG.DispatchRefused, match="was not presented"):
        DG.validate(rec, decl, sha, _auth(sha), None)
    with pytest.raises(DG.DispatchRefused, match="does not match the bound digest"):
        DG.validate(rec, decl, sha, _auth(sha), "another-token")
    assert DG.validate(rec, decl, sha, _auth(sha), TOKEN)["owner_token_sha256"] == DIGEST


@pytest.mark.parametrize("over,match", [({"authorized_by": "assistant"}, "not the owner's"), ({"nonce": ""}, "no one-run nonce"),
                                        ({"nonce": "short"}, "no one-run nonce")])
def test_not_the_owner_or_no_nonce_is_refused(tmp_path, over, match):
    decl, sha, rec = _decl(tmp_path)
    with pytest.raises(DG.DispatchRefused, match=match):
        DG.validate(rec, decl, sha, _auth(sha, **over), TOKEN)


def test_a_dry_exercise_declaration_never_authorizes(tmp_path):
    decl, sha, _ = _decl(tmp_path, dry_exercise=True)
    with pytest.raises(DG.DispatchRefused, match="not a live ORCH-07 declaration"):
        DG.authorize(decl, sha, run_folder=tmp_path, invocation=1, token=TOKEN)


# ---- one run, one nonce ------------------------------------------------------------------------------------------------------
def test_consumed_nonce_is_refused_and_lanes_need_their_own_invocation(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    run = tmp_path / "run"
    _patch_loader(monkeypatch, _auth(sha))
    assert DG.authorize(decl, sha, run_folder=run, invocation=1, action="preview", token=TOKEN)["authorized"]
    assert not list(run.glob("**/*")), "preview writes nothing"
    with pytest.raises(DG.DispatchRefused, match="has not been consumed"):
        DG.authorize(decl, sha, run_folder=run, invocation=1, action="verify", token=TOKEN)
    rec = DG.authorize(decl, sha, run_folder=run, invocation=1, action="consume", stamp="s1", token=TOKEN)
    assert pathlib.Path(rec["consumption_record"]).is_file() and rec["authorization_sha256"] == "e" * 64
    stored = json.loads(pathlib.Path(rec["consumption_record"]).read_text(encoding="utf-8"))
    assert stored["authorization_sha256"] == "e" * 64 and stored["declaration_sha256"] == sha and stored["invocation"] == 1
    assert "nonce-0123456789abcdef" not in json.dumps(stored) and TOKEN not in json.dumps(stored), "only digests are recorded"
    for action in ("consume", "preview"):
        with pytest.raises(DG.DispatchRefused, match="already consumed"):
            DG.authorize(decl, sha, run_folder=run, invocation=2, action=action, token=TOKEN)
    assert DG.authorize(decl, sha, run_folder=run, invocation=1, action="verify", token=TOKEN)["authorized"]
    with pytest.raises(DG.DispatchRefused, match="another authorization, declaration or invocation"):
        DG.authorize(decl, sha, run_folder=run, invocation=2, action="verify", token=TOKEN)
    _patch_loader(monkeypatch, _auth(sha), auth_sha="d" * 64)            # the same nonce in an edited authorization file
    with pytest.raises(DG.DispatchRefused, match="another authorization"):
        DG.authorize(decl, sha, run_folder=run, invocation=1, action="verify", token=TOKEN)
    _patch_loader(monkeypatch, _auth(sha, nonce="fresh-nonce-for-a-resume-0002"))
    assert DG.authorize(decl, sha, run_folder=run, invocation=2, action="consume", kind="resume", token=TOKEN)["authorized"], \
        "a resume consumes a NEW nonce for the same declaration"


def test_the_guarded_provider_never_builds_the_real_provider_when_refused(tmp_path):
    decl, sha, _ = _decl(tmp_path)

    def build():
        raise AssertionError("the real provider must not be built")

    g = DG.GuardedProvider(build, decl, sha, Resp, run_folder=tmp_path / "run", invocation=1)
    r = g.complete(object())
    assert r.error == "dispatch_refused" and g.refused == 1 and g.dispatched == 0 and g.inner is None


def test_the_guarded_provider_authorizes_before_every_request(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    monkeypatch.setenv(DG.TOKEN_ENV, TOKEN)
    _patch_loader(monkeypatch, _auth(sha))
    DG.authorize(decl, sha, run_folder=tmp_path / "run", invocation=1, action="consume")
    calls = []

    class Inner:
        def complete(self, request):
            calls.append(request)
            return Resp(data={"ok": True})

    g = DG.GuardedProvider(Inner, decl, sha, Resp, run_folder=tmp_path / "run", invocation=1)
    assert g.complete("r1").ok and calls == ["r1"]

    def withdrawn(path):
        raise DG.DispatchRefused("refused: no owner dispatch authorization (withdrawn)")

    monkeypatch.setattr(DG, "_load_authorization", withdrawn)
    assert g.complete("r2").error == "dispatch_refused" and calls == ["r1"], "a withdrawn authorization stops the next request"
    monkeypatch.delenv(DG.TOKEN_ENV)
    _patch_loader(monkeypatch, _auth(sha))
    assert g.complete("r3").error == "dispatch_refused" and calls == ["r1"], "without the owner token the next request is refused"


def test_the_dry_stub_never_answers():
    d = DG.DryRefusingProvider(Resp)
    assert d.complete("x").error == "dry_refused" and d.calls == 1
