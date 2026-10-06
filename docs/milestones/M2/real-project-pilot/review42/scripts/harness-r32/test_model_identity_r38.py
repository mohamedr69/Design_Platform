"""model_identity_r38 (ORCH-08, A-09 point 2, R38-10): full model ids pinned (no aliases), the CLI version recorded and held
equal across a run's invocations, every response's returned provider and model checked, and a mismatch making the run
INVALID with the offending request recorded and every later request refused. No CLI and no provider is started: the
version runner and the inner providers are fakes. Run: python -m pytest -q test_model_identity_r38.py
ORCH-10 (R42, contract 5): the CLI is pinned by ABSOLUTE PATH, file sha256 and exact version line; the pinned path of these
tests is a fake name that is never executed (the version runner is a fake), and verify_cli_file hashes a small text file."""
import json
import subprocess
import types

import pytest

import model_identity_r38 as MI


class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, usage=None, **kw):
        self.data, self.model, self.error, self.error_detail, self.usage = data, model, error, error_detail, usage


class Req:
    def __init__(self, task="discover_page", tier="small", model=None):
        self.task, self.tier, self.model = task, tier, model


CLI = "C:/r42-test/no-such-cli/cli-never-executed.exe"
CLI_SHA = "a" * 64
ENV = {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "claude-sonnet-5", "AI_MODEL_STANDARD": "claude-opus-5", "AI_CLAUDE_CLI": CLI}
MID = {"provider": "claude-code", "models": {"small": "claude-sonnet-5", "standard": "claude-opus-5"},
       "cli": {"path": CLI, "sha256": CLI_SHA, "version": "2.1.263 (Claude Code)"}}
DECLARED = {"provider": "claude-code", "small": "claude-sonnet-5", "standard": "claude-opus-5"}


def test_the_pinned_ids_are_the_ones_the_adapter_records():
    assert MI.PINNED == {"small": "claude-sonnet-5", "standard": "claude-opus-5"} and MI.PROVIDER == "claude-code"
    assert all(MI.is_full_id(v) for v in MI.PINNED.values())
    for alias in ("sonnet", "opus", "haiku", "fable", "default", "best", "opusplan", "claude-sonnet", "Claude-Sonnet-5", ""):
        assert not MI.is_full_id(alias), alias


def test_validate_pins_accepts_the_full_ids_and_refuses_aliases_and_disagreement():
    v = MI.validate_pins(MID, ENV)
    assert v == {"provider": "claude-code", "small": "claude-sonnet-5", "standard": "claude-opus-5", "cli_path": CLI,
                 "cli_version": "2.1.263 (Claude Code)", "cli_sha256": CLI_SHA}
    bad = [({**MID, "models": {"small": "sonnet", "standard": "claude-opus-5"}}, ENV | {"AI_MODEL_SMALL": "sonnet"}, "not an alias"),
           (MID, ENV | {"AI_MODEL_STANDARD": "opus"}, "differs from model_identity"),
           ({**MID, "provider": "openai"}, ENV, "model_identity.provider"),
           ({**MID, "cli": {"path": "C:/other/claude.exe", "sha256": CLI_SHA, "version": "2.1.263 (Claude Code)"}}, ENV, "cli.path"),
           ({**MID, "cli": {"path": CLI, "sha256": CLI_SHA, "version": " "}}, ENV, "exact version line"),
           ({**MID, "cli": {"path": CLI, "sha256": CLI_SHA, "version": None}}, ENV, "never null"),
           ({**MID, "cli": {"path": CLI, "version": "2.1.263 (Claude Code)"}}, ENV, "cli.sha256 must pin"),
           ({**MID, "cli": {"path": CLI, "sha256": "A" * 64, "version": "2.1.263 (Claude Code)"}}, ENV, "cli.sha256 must pin"),
           ({**MID, "cli": {"path": "claude", "sha256": CLI_SHA, "version": "2.1.263 (Claude Code)"}}, ENV | {"AI_CLAUDE_CLI": "claude"}, "ABSOLUTE path"),
           (None, ENV, "no model_identity")]
    for mid, env, match in bad:
        with pytest.raises(MI.IdentityRefused, match=match):
            MI.validate_pins(mid, env)


def _fake_run(stdout, code=0):
    calls = []

    def run(args, **kw):
        calls.append(args)
        return types.SimpleNamespace(stdout=stdout, returncode=code)
    return run, calls


def test_the_cli_version_is_read_with_version_only():
    run, calls = _fake_run("2.1.263 (Claude Code)\n")
    assert MI.cli_version("claude", run=run) == "2.1.263 (Claude Code)" and calls == [["claude", "--version"]]
    with pytest.raises(MI.IdentityRefused):
        MI.cli_version("claude", run=_fake_run("", 1)[0])

    def boom(*a, **k):
        raise subprocess.TimeoutExpired("claude", 1)
    with pytest.raises(MI.IdentityRefused, match="failed"):
        MI.cli_version("claude", run=boom)


def test_every_invocation_records_its_version_and_a_change_during_the_run_is_refused(tmp_path):
    pins = dict(MI.validate_pins(MID, ENV), cli_version=None)     # the run-held rule alone (the declared line is checked below)
    r1 = MI.record_invocation(tmp_path, 1, pins, "2.1.263 (Claude Code)", mode="live")
    assert json.loads((tmp_path / "inv-1" / "PROVIDER-IDENTITY.json").read_text(encoding="utf-8"))["cli_version"] == "2.1.263 (Claude Code)"
    MI.record_invocation(tmp_path, 2, pins, "2.1.263 (Claude Code)", mode="live")
    with pytest.raises(MI.IdentityRefused, match="differs from this run's first invocation"):
        MI.record_invocation(tmp_path, 3, pins, "2.2.0 (Claude Code)", mode="live")
    lines = (tmp_path / MI.CLI_LOG).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and r1["declared_models"] == {"small": "claude-sonnet-5", "standard": "claude-opus-5"}
    pinned = dict(pins, cli_version="2.1.263 (Claude Code)")
    with pytest.raises(MI.IdentityRefused, match="differs from the declared"):
        MI.record_invocation(tmp_path / "other", 1, pinned, "2.1.264 (Claude Code)", mode="live")
    assert json.loads(lines[0])["cli_sha256"] == CLI_SHA, "ORCH-10: the record names the pinned file's sha256"


def test_orch10_check_version_is_pure_and_refuses_before_anything_is_written(tmp_path):
    """ORCH-10 (R41-09 / R41-11): the comparison the runner makes BEFORE it creates or re-opens anything writes nothing."""
    pins = MI.validate_pins(MID, ENV)
    assert MI.check_version(None, pins, "2.1.263 (Claude Code)")["first_recorded"] is None
    with pytest.raises(MI.IdentityRefused, match="differs from the declared"):
        MI.check_version(tmp_path / "absent", pins, "2.1.264 (Claude Code)")
    assert not (tmp_path / "absent").exists() and list(tmp_path.iterdir()) == []
    MI.record_invocation(tmp_path, 1, pins, "2.1.263 (Claude Code)", mode="live")
    with open(tmp_path / MI.CLI_LOG, "a", encoding="utf-8") as fh:
        fh.write('{"cut by a full disk')                  # an interrupted line is no record
    assert MI.check_version(tmp_path, pins, "2.1.263 (Claude Code)")["first_recorded"] == "2.1.263 (Claude Code)"
    unpinned = dict(pins, cli_version=None)
    with pytest.raises(MI.IdentityRefused, match="first invocation"):
        MI.check_version(tmp_path, unpinned, "2.2.0 (Claude Code)")


def test_orch10_verify_cli_file_reads_bytes_only(tmp_path):
    f = tmp_path / "fake-cli.txt"
    f.write_bytes(b"not a program")
    import hashlib
    want = hashlib.sha256(b"not a program").hexdigest()
    assert MI.verify_cli_file(f, want) == {"cli_path": f.as_posix(), "cli_sha256": want, "cli_bytes": 13, "executed": False}
    with pytest.raises(MI.IdentityRefused, match="hashes to"):
        MI.verify_cli_file(f, "0" * 64)
    with pytest.raises(MI.IdentityRefused, match="does not exist"):
        MI.verify_cli_file(tmp_path / "absent.exe", want)


def _guard(tmp_path, inner, lane="C"):
    return MI.IdentityGuard(inner, Resp, declared=DECLARED, run_folder=tmp_path, invocation=1, lane=lane,
                            log_path=tmp_path / "inv-1" / f"IDENTITY-LOG-{lane}.jsonl", ctx_fn=lambda: {"sha256": "abc", "page": 2},
                            provider_name_fn=lambda: "claude-code")


class Inner:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), 0

    def complete(self, request):
        self.calls += 1
        return self.responses.pop(0)


def test_matching_identities_pass_and_every_response_is_logged(tmp_path):
    inner = Inner(Resp(data={}, model="claude-sonnet-5"), Resp(data={}, model="claude-opus-5"), Resp(model="claude-sonnet-5", error="timeout"),
                  Resp(model="", error="budget", error_detail="ledger refused (breaker): x"))
    g = _guard(tmp_path, inner)
    assert g.complete(Req()).data == {} and g.complete(Req(tier="standard")).data == {}
    assert g.complete(Req()).error == "timeout", "a timeout echoes the configured id: checked, equal"
    assert g.complete(Req()).error == "budget", "a ledger refusal never reached a provider: not checked"
    log = [json.loads(x) for x in (tmp_path / "inv-1" / "IDENTITY-LOG-C.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [x["check"] for x in log] == ["ok", "ok", "ok", "not_dispatched"] and log[2]["identity_source"] == "echo_no_reply"
    assert MI.invalid_marker(tmp_path) is None and g.checked == 3


def test_a_returned_model_that_differs_makes_the_run_invalid_and_refuses_the_next_request(tmp_path):
    inner = Inner(Resp(data={"value": "X"}, model="claude-sonnet-5-1"), Resp(data={}, model="claude-sonnet-5"))
    g = _guard(tmp_path, inner)
    r = g.complete(Req(task="read_identity"))
    assert r.error == "identity_mismatch" and r.data is None, "the answer of another model is never used"
    m = MI.invalid_marker(tmp_path)
    assert m["returned_model"] == "claude-sonnet-5-1" and m["expected_model"] == "claude-sonnet-5" and m["task"] == "read_identity"
    assert m["lane"] == "C" and m["page"] == 2 and m["document_sha256"] == "abc"
    nxt = g.complete(Req())
    assert nxt.error == "identity_invalid" and inner.calls == 1, "the next request is refused before it is sent"
    other = _guard(tmp_path, Inner(Resp(data={}, model="claude-sonnet-5")), lane="R")
    assert other.complete(Req()).error == "identity_invalid", "every lane, every later invocation: the marker is never removed"


def test_a_different_provider_is_a_mismatch_too(tmp_path):
    g = MI.IdentityGuard(Inner(Resp(data={}, model="claude-sonnet-5")), Resp, declared=DECLARED, run_folder=tmp_path, invocation=1, lane="B",
                         log_path=tmp_path / "log.jsonl", provider_name_fn=lambda: "openai")
    assert g.complete(Req()).error == "identity_mismatch" and MI.invalid_marker(tmp_path)["returned_provider"] == "openai"


def test_an_explicit_request_model_is_the_expected_identity(tmp_path):
    g = _guard(tmp_path, Inner(Resp(data={}, model="claude-opus-5")))
    assert g.complete(Req(model="claude-opus-5")).data == {}
