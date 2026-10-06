"""ORCH-10 (R42; A-11 section 4): one approval for all planned resumptions -- the separable multi-invocation form of the
owner's authorization file, default OFF. NO authorization file is created by any test (the task forbids it): the
authorization contents are in-memory objects returned by a monkeypatched loader; the only files written are temporary
declarations and consumption records under pytest's tmp_path (inside C:/t/r2x/r42-sandbox).
Run: python -m pytest -q test_resume_authorization_r42.py"""
import hashlib
import json

import pytest

import dispatch_guard_r32 as DG

TOKEN = "test-owner-token-not-real"
DIGEST = hashlib.sha256(TOKEN.encode()).hexdigest()
FROZEN = "f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af"      # the frozen v2 hash: never an authorization's target
N1, N2, N3, N4 = "nonce-aaaaaaaaaaaaaaaa1", "nonce-bbbbbbbbbbbbbbbb2", "nonce-cccccccccccccccc3", "nonce-dddddddddddddddd4"


def _decl(tmp_path, bound=3, **over):
    """A temporary declaration (NOT an authorization) with the pinned path, the digest and (default) the bound 3."""
    p = tmp_path / "pkg" / "DECLARATION.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"name": "r42 test declaration", "authorization": {"path": (p.parent / DG.AUTH_NAME).as_posix(), "owner_token_sha256": DIGEST}}
    if bound is not None:
        rec["resume_authorization"] = {"max_invocations_per_file": bound}
    rec |= over
    p.write_text(json.dumps(rec), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest(), rec


def _multi(sha, nonces, n=None, **over):
    return {"declaration_sha256": sha, "owner_token_sha256": DIGEST, "authorized_by": "owner", "invocations_authorized": len(nonces) if n is None else n,
            "nonces": list(nonces)} | over


def _single(sha, nonce=N1, **over):
    return {"declaration_sha256": sha, "owner_token_sha256": DIGEST, "authorized_by": "owner", "nonce": nonce} | over


def _loader(monkeypatch, obj, auth_sha=None):
    sha = auth_sha or hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
    monkeypatch.setattr(DG, "_load_authorization", lambda path: (obj, sha))
    return sha


def _auth(decl, sha, run, inv, action, kind="resume"):
    return DG.authorize(decl, sha, run_folder=run, invocation=inv, action=action, stamp="r42-test", kind=kind, token=TOKEN)


# ---- the per-invocation form (default) is unchanged ----------------------------------------------------------------------
def test_the_per_invocation_form_is_unchanged_one_nonce_one_invocation(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    auth_sha = _loader(monkeypatch, _single(sha))
    run = tmp_path / "run"
    assert _auth(decl, sha, run, 1, "preview")["form"] == "single"
    assert not (run / DG.CONSUMED_DIR).exists(), "a preview writes nothing"
    c = _auth(decl, sha, run, 1, "consume", kind="fresh")
    assert c["authorization_sha256"] == auth_sha and pathlib_exists(c["consumption_record"])
    assert _auth(decl, sha, run, 1, "verify")["form"] == "single"
    with pytest.raises(DG.DispatchRefused, match="already consumed"):
        _auth(decl, sha, run, 2, "preview")
    with pytest.raises(DG.DispatchRefused, match="already consumed"):
        _auth(decl, sha, run, 2, "consume")


def pathlib_exists(p):
    import pathlib
    return pathlib.Path(p).is_file()


def test_the_per_invocation_form_works_without_the_declared_bound(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path, bound=None)
    _loader(monkeypatch, _single(sha))
    assert _auth(decl, sha, tmp_path / "run", 1, "consume", kind="fresh")["form"] == "single"


# ---- the multi-invocation form ----------------------------------------------------------------------------------------------
def test_one_file_authorizes_n_invocations_each_consuming_exactly_one_nonce_in_order(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    obj = _multi(sha, [N1, N2, N3])
    auth_sha = _loader(monkeypatch, obj)
    run = tmp_path / "run"
    for inv in (1, 2, 3):
        pv = _auth(decl, sha, run, inv, "preview")
        assert pv["nonce_index"] == inv and pv["nonces_consumed_before"] == inv - 1
        c = _auth(decl, sha, run, inv, "consume", kind="fresh" if inv == 1 else "resume")
        assert c["nonce_index"] == inv and c["nonce_sha256"] == hashlib.sha256([N1, N2, N3][inv - 1].encode()).hexdigest()
        rec = json.loads(open(c["consumption_record"], encoding="utf-8").read())
        assert rec["invocation"] == inv and rec["nonce_index"] == inv and rec["invocations_authorized"] == 3 and rec["authorization_sha256"] == auth_sha
        v = _auth(decl, sha, run, inv, "verify")
        assert v["nonce_index"] == inv, "every lane and every request of this invocation verify THIS invocation's nonce"
        with pytest.raises(DG.DispatchRefused, match="already consumed nonce"):
            _auth(decl, sha, run, inv, "consume")
    assert len(list((run / DG.CONSUMED_DIR).glob("consumed-*.json"))) == 3
    with pytest.raises(DG.DispatchRefused, match="needs a NEW authorization file"):
        _auth(decl, sha, run, 4, "preview")
    with pytest.raises(DG.DispatchRefused, match="needs a NEW authorization file"):
        _auth(decl, sha, run, 4, "consume")
    with pytest.raises(DG.DispatchRefused, match="has not been consumed"):
        _auth(decl, sha, run, 4, "verify")


def test_invocation_n_plus_1_works_with_a_new_file_and_fresh_nonces(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    run = tmp_path / "run"
    _loader(monkeypatch, _multi(sha, [N1, N2]))
    _auth(decl, sha, run, 1, "consume", kind="fresh")
    _auth(decl, sha, run, 2, "consume")
    _loader(monkeypatch, _single(sha, N3))
    assert _auth(decl, sha, run, 3, "consume")["form"] == "single"


@pytest.mark.parametrize("n", [1, 2, 3])
def test_any_n_from_1_to_the_bound_is_accepted(tmp_path, monkeypatch, n):
    decl, sha, _ = _decl(tmp_path)
    _loader(monkeypatch, _multi(sha, [N1, N2, N3][:n]))
    assert _auth(decl, sha, tmp_path / "run", 1, "preview")["invocations_authorized"] == n


# ---- every refusal ------------------------------------------------------------------------------------------------------------
def test_a_reused_nonce_is_refused(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    run = tmp_path / "run"
    _loader(monkeypatch, _single(sha, N1))
    _auth(decl, sha, run, 1, "consume", kind="fresh")
    _loader(monkeypatch, _multi(sha, [N1, N2]))                    # a new file that carries the consumed nonce again
    with pytest.raises(DG.DispatchRefused, match="consumed under another authorization"):
        _auth(decl, sha, run, 2, "preview")
    with pytest.raises(DG.DispatchRefused, match="consumed under another authorization"):
        _auth(decl, sha, run, 2, "consume")
    _loader(monkeypatch, _single(sha, N1))
    with pytest.raises(DG.DispatchRefused, match="already consumed"):
        _auth(decl, sha, run, 2, "consume")


def test_an_out_of_order_nonce_is_refused(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    run = tmp_path / "run"
    obj = _multi(sha, [N1, N2, N3])
    _loader(monkeypatch, obj, auth_sha="e" * 64)
    _auth(decl, sha, run, 1, "consume", kind="fresh")
    # the owner reorders the nonces of the same authorization (same file hash is impossible after an edit; simulated): the
    # consumed nonce is now second in the list
    _loader(monkeypatch, _multi(sha, [N2, N1, N3]), auth_sha="e" * 64)
    with pytest.raises(DG.DispatchRefused, match="out of order"):
        _auth(decl, sha, run, 2, "consume")


def test_a_count_above_the_declared_bound_is_refused(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path, bound=2)
    _loader(monkeypatch, _multi(sha, [N1, N2, N3]))
    with pytest.raises(DG.DispatchRefused, match="above the declared bound 2"):
        _auth(decl, sha, tmp_path / "run", 1, "preview")
    decl, sha, _ = _decl(tmp_path / "b3")
    _loader(monkeypatch, _multi(sha, [N1, N2, N3, N4]))
    with pytest.raises(DG.DispatchRefused, match="above the declared bound 3"):
        _auth(decl, sha, tmp_path / "run3", 1, "preview")


@pytest.mark.parametrize("bound", [None, 0, 4, "3", True])
def test_a_declaration_without_a_valid_bound_refuses_every_multi_file(tmp_path, monkeypatch, bound):
    decl, sha, rec = _decl(tmp_path, bound=None)
    if bound is not None:
        rec["resume_authorization"] = {"max_invocations_per_file": bound}
        decl.write_text(json.dumps(rec), encoding="utf-8", newline="\n")
        sha = hashlib.sha256(decl.read_bytes()).hexdigest()
    _loader(monkeypatch, _multi(sha, [N1]))
    with pytest.raises(DG.DispatchRefused, match="binds no resume_authorization"):
        _auth(decl, sha, tmp_path / "run", 1, "preview")


def test_a_file_naming_the_frozen_hash_is_refused_in_both_forms(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    for obj in (_multi(FROZEN, [N1, N2]), _single(FROZEN)):
        _loader(monkeypatch, obj)
        with pytest.raises(DG.DispatchRefused, match="the authorization names declaration f38fb281f30b"):
            _auth(decl, sha, tmp_path / "run", 1, "preview")


@pytest.mark.parametrize("extra", [{"parent": {"total": 9999}}, {"lane_allowances": {"C": 999}}, {"project_window": {"limit": 600}},
                                   {"scope": "another-scope"}, {"allowance": "reset"}, {"note": "harmless?"}])
def test_an_authorization_can_never_name_an_allowance_parent_window_or_scope(tmp_path, monkeypatch, extra):
    decl, sha, _ = _decl(tmp_path)
    for obj in (_multi(sha, [N1, N2], **extra), _single(sha, **extra)):
        _loader(monkeypatch, obj)
        with pytest.raises(DG.DispatchRefused, match="holds exactly"):
            _auth(decl, sha, tmp_path / "run", 1, "preview")


@pytest.mark.parametrize("obj_fn,match", [
    (lambda s: _multi(s, [N1, N1]), "repeats a nonce"),
    (lambda s: _multi(s, [N1, N2], n=3), "exactly 3 one-run nonces"),
    (lambda s: _multi(s, [N1, "short"]), "one-run nonces"),
    (lambda s: _multi(s, [N1], n=0), "positive integer"),
    (lambda s: _multi(s, [N1], n=True), "positive integer"),
    (lambda s: {k: v for k, v in _multi(s, [N1]).items() if k != "nonces"}, "holds exactly"),
    (lambda s: _multi(s, [N1]) | {"nonce": N2}, "holds exactly"),
    (lambda s: _multi(s, [N1], authorized_by="orchestrator"), "not the owner's"),
])
def test_malformed_multi_files_are_refused(tmp_path, monkeypatch, obj_fn, match):
    decl, sha, _ = _decl(tmp_path)
    _loader(monkeypatch, obj_fn(sha))
    with pytest.raises(DG.DispatchRefused, match=match):
        _auth(decl, sha, tmp_path / "run", 1, "preview")


def test_the_check_report_never_consumes_and_the_token_is_still_required(tmp_path, monkeypatch):
    decl, sha, _ = _decl(tmp_path)
    _loader(monkeypatch, _multi(sha, [N1, N2]))
    r = DG.check(decl, sha, run_folder=tmp_path / "run", invocation=1, action="consume", token=TOKEN)
    assert r["authorized"] and r["action"] == "preview" and not (tmp_path / "run").exists()
    with pytest.raises(DG.DispatchRefused, match="was not presented"):
        DG.authorize(decl, sha, run_folder=tmp_path / "run", invocation=1, action="preview", token="")
