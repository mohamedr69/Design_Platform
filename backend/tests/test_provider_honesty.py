"""FI-P1 Stage 0.2 -- provider honesty, offline.

The configured CLI path, the CLI version a model needs, the exact model and
effort asked for, and what actually answered are checked here against a fake
Claude Code program and a fake API client. No model is called.
"""
import json
import subprocess
from types import SimpleNamespace

import pytest

from app.ai import provider as P
from app.ai.provider import AiRequest, ClaudeCodeProvider, ClaudeProvider, ImagePart, TextPart
from app.core.config import Settings, get_settings

settings = get_settings()


def _reply(model_usage, *, data=None, is_error=False, result=None):
    return {"type": "result", "subtype": "success", "is_error": is_error,
            "structured_output": data if data is not None else {"answer": "ok"},
            "result": result or json.dumps(data or {"answer": "ok"}),
            "usage": {"input_tokens": 3, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                      "output_tokens": 7},
            "modelUsage": model_usage}


class FakeCli:
    """subprocess.run stand-in: answers `--version`, records every real call."""

    def __init__(self, version="2.1.288 (Claude Code)", reply=None, version_raises=False):
        self.version = version
        self.reply = reply if reply is not None else _reply({"claude-opus-5-5": {"outputTokens": 7}})
        self.version_raises = version_raises
        self.calls: list[list[str]] = []
        self.version_calls = 0

    def __call__(self, args, **kwargs):
        if args[1:] == ["--version"]:
            self.version_calls += 1
            if self.version_raises:
                raise OSError("cannot run")
            return subprocess.CompletedProcess(args, 0, stdout=self.version + "\n", stderr="")
        self.calls.append(list(args))
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(self.reply), stderr="")


@pytest.fixture
def cli(monkeypatch, tmp_path):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    fake = FakeCli()
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def _req(model="claude-opus-5-5", **kw):
    return AiRequest(task="t", system="s", parts=[TextPart("a", "b")], schema={"type": "object"},
                     max_output_tokens=100, model=model, **kw)


# --- the configured path ---------------------------------------------------------------------------------------


def test_the_cli_path_expands_the_users_own_folders(monkeypatch, tmp_path):
    """The .env carried C:\\Users\\ramadan.mohamed\\... -- another Windows user's
    folder. %LOCALAPPDATA%-style paths now serve every user."""
    monkeypatch.setenv("EP_TEST_CLI_ROOT", str(tmp_path))
    s = Settings(ai_claude_cli="%EP_TEST_CLI_ROOT%\\ep-platform\\claude.exe")
    assert s.ai_claude_cli == str(tmp_path) + "\\ep-platform\\claude.exe"
    assert Settings(ai_claude_cli="  ").ai_claude_cli == "claude"


def test_a_missing_cli_is_unavailable_not_an_auth_failure(monkeypatch, tmp_path):
    missing = tmp_path / "nobody" / "claude.exe"
    monkeypatch.setattr(settings, "ai_claude_cli", str(missing))
    called = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: called.append(a))
    provider = ClaudeCodeProvider()
    assert provider.ready is False and str(missing) in provider.status
    response = provider.complete(_req())
    assert response.error == "unavailable" and str(missing) in response.error_detail
    assert called == []


# --- the version a model needs ----------------------------------------------------------------------------------


def test_opus_5_5_on_a_cli_too_old_is_refused_before_any_call(cli):
    cli.version = "2.1.263 (Claude Code)"
    response = ClaudeCodeProvider().complete(_req("claude-opus-5-5", exact_model=True))
    assert response.error == "unsupported_model"
    assert "2.1.263" in response.error_detail and "2.1.280" in response.error_detail
    assert cli.calls == []


def test_opus_5_5_on_a_new_enough_cli_is_called(cli):
    provider = ClaudeCodeProvider()
    response = provider.complete(_req("claude-opus-5-5", exact_model=True))
    assert response.ok and response.model == "claude-opus-5-5" and response.route_version.startswith("2.1.288")
    assert len(cli.calls) == 1
    provider.complete(_req("claude-opus-5-5", exact_model=True))
    assert cli.version_calls == 1          # the version is read once per provider


def test_an_unreadable_version_blocks_only_models_that_need_one(cli):
    cli.version_raises = True
    cli.reply = _reply({"claude-fable-5-1": {"outputTokens": 7}})
    provider = ClaudeCodeProvider()
    assert provider.complete(_req("claude-opus-5-5")).error == "unsupported_model"
    assert provider.complete(_req("claude-fable-5-1")).ok          # no known minimum for Fable 5.1


def test_the_clis_own_model_refusal_is_reported_as_unsupported_model(cli):
    cli.version = "9.9.9"
    cli.reply = _reply({}, is_error=True, result="API Error: 400 Claude Code 2.1.263 does not support this model; "
                                                  "version 2.1.280 or newer is required.")
    assert ClaudeCodeProvider().complete(_req()).error == "unsupported_model"


# --- exact model and effort ---------------------------------------------------------------------------------------


def test_effort_goes_to_the_cli_and_an_unknown_effort_is_refused(cli):
    provider = ClaudeCodeProvider()
    provider.complete(_req(effort="high"))
    args = cli.calls[-1]
    assert args[args.index("--effort") + 1] == "high"
    provider.complete(_req())
    assert "--effort" not in cli.calls[-1]
    calls = len(cli.calls)
    bad = provider.complete(_req(effort="extreme"))
    assert bad.error == "invalid_request" and len(cli.calls) == calls
    assert all("--fallback-model" not in a for a in cli.calls)


def test_an_alias_is_refused_for_an_exact_model_task_but_allowed_otherwise(cli):
    cli.reply = _reply({"claude-opus-5": {"outputTokens": 7}})
    provider = ClaudeCodeProvider()
    refused = provider.complete(_req("opus", exact_model=True))
    assert refused.error == "unsupported_model" and "alias" in refused.error_detail and cli.calls == []
    tier = provider.complete(_req("opus"))
    assert tier.ok and tier.model == "claude-opus-5" and tier.substituted is False


# --- what actually answered ----------------------------------------------------------------------------------------


def test_another_model_answering_an_exact_request_is_an_error_not_a_result(cli):
    """Seen live on 2026-10-04: a claude-fable-5-1 call whose modelUsage also
    listed claude-opus-4-8."""
    cli.reply = _reply({"claude-haiku-4-5-20251001": {"outputTokens": 11}, "claude-fable-5-1": {"outputTokens": 4},
                        "claude-opus-4-8": {"outputTokens": 3}})
    provider = ClaudeCodeProvider()
    exact = provider.complete(_req("claude-fable-5-1", exact_model=True))
    assert exact.error == "model_substituted" and exact.data is None and exact.substituted
    assert "claude-opus-4-8" in exact.error_detail and exact.models_used["claude-opus-4-8"] == 3
    loose = provider.complete(_req("claude-fable-5-1"))
    assert loose.ok and loose.substituted                      # reported, not hidden


def test_claude_codes_own_haiku_is_auxiliary_not_a_substitute(cli):
    cli.reply = _reply({"claude-haiku-4-5-20251001": {"outputTokens": 11}, "claude-opus-5-5": {"outputTokens": 9}})
    response = ClaudeCodeProvider().complete(_req("claude-opus-5-5", exact_model=True))
    assert response.ok and response.model == "claude-opus-5-5" and not response.substituted


def test_images_still_use_the_read_tool_with_effort(cli):
    request = AiRequest(task="t", system="s", parts=[ImagePart("page", b"png")], schema={}, max_output_tokens=10,
                        model="claude-opus-5-5", effort="high", exact_model=True)
    ClaudeCodeProvider().complete(request)
    args = cli.calls[-1]
    assert args[args.index("--tools") + 1] == "Read" and args[args.index("--effort") + 1] == "high"


# --- the API route --------------------------------------------------------------------------------------------------


class FakeMessages:
    def __init__(self, served):
        self.served = served
        self.params = None

    def create(self, **params):
        self.params = params
        return SimpleNamespace(model=self.served, stop_reason="end_turn",
                               usage=SimpleNamespace(input_tokens=5, output_tokens=6, cache_read_input_tokens=0,
                                                     output_tokens_details=None),
                               content=[SimpleNamespace(type="text", text='{"answer": "ok"}')])


def _api(monkeypatch, served):
    provider = ClaudeProvider.__new__(ClaudeProvider)
    plain, beta = FakeMessages(served), FakeMessages(served)
    import anthropic

    provider._anthropic = anthropic
    provider._client = SimpleNamespace(messages=plain, beta=SimpleNamespace(messages=beta))
    provider._models = {"small": "claude-fable-5-1", "standard": "claude-fable-5-1"}
    provider._effort = "low"
    provider._semaphore = P.threading.BoundedSemaphore(2)
    provider._credential = True
    return provider, plain, beta


def test_api_exact_requests_never_use_server_side_fallbacks_and_check_the_served_model(monkeypatch):
    provider, plain, beta = _api(monkeypatch, served="claude-opus-4-8")
    response = provider.complete(_req("claude-fable-5-1", exact_model=True, effort="high"))
    assert response.error == "model_substituted" and response.model == "claude-opus-4-8"
    assert beta.params is None and "fallbacks" not in plain.params
    assert plain.params["output_config"]["effort"] == "high"


def test_api_tier_requests_keep_fallbacks_but_report_who_served(monkeypatch):
    provider, plain, beta = _api(monkeypatch, served="claude-opus-4-8")
    response = provider.complete(_req("claude-fable-5-1"))
    assert response.ok and response.model == "claude-opus-4-8" and response.substituted
    assert beta.params["fallbacks"] == "default"


def test_api_effort_defaults_to_ai_effort_and_is_validated(monkeypatch):
    provider, plain, _ = _api(monkeypatch, served="claude-opus-5-5")
    assert provider.complete(_req("claude-opus-5-5")).ok
    assert plain.params["output_config"]["effort"] == "low"
    assert provider.complete(_req("claude-opus-5-5", effort="huge")).error == "invalid_request"


# --- through assist: cache and usage log -------------------------------------------------------------------------


def test_a_substituted_answer_is_logged_and_never_cached(db_session):
    from app.ai.budget import JobBudget, Limits
    from app.compliance import assist
    from app.models import AiUsage, ResultCache

    class Substituting:
        name, ready, status = "fake", True, "fake"
        calls = 0

        def complete(self, request):
            Substituting.calls += 1
            assert request.exact_model and request.effort == "high" and request.model == "claude-opus-5-5"
            return P.AiResponse(data=None, error="model_substituted", error_detail="asked for x", model="claude-opus-4-8",
                                substituted=True)

    session = assist.AssistSession(db=db_session, project_id=None, document_sha256="d" * 64,
                                   budget=JobBudget(limits=Limits.from_settings(), calls_today_before=0), provider=Substituting())
    for _ in range(2):
        result = assist.call_task(session, "fa_interfaces_visual", "s", [TextPart("a", "b")], {"type": "object"}, 100,
                                  model="claude-opus-5-5", effort="high", exact_model=True)
        assert result.data is None
    assert Substituting.calls == 2                                  # not served from a cache
    assert db_session.query(ResultCache).count() == 0
    assert {u.outcome for u in db_session.query(AiUsage).all()} == {"model_substituted"}


def test_effort_and_exactness_are_in_the_cache_key_only_when_set(db_session):
    from app.ai.budget import JobBudget, Limits
    from app.compliance import assist

    keys = []

    class Recording:
        name, ready, status = "fake", True, "fake"

        def complete(self, request):
            keys.append(request.idempotency_key)
            return P.AiResponse(data=None, error="transport", model="m")

    session = assist.AssistSession(db=db_session, project_id=None, document_sha256="e" * 64,
                                   budget=JobBudget(limits=Limits.from_settings(), calls_today_before=0), provider=Recording())
    parts = [TextPart("a", "b")]
    assist.call_task(session, "t1", "s", parts, {}, 10, model="claude-opus-5-5")
    assist.call_task(session, "t1", "s", parts, {}, 10, model="claude-opus-5-5", effort="high")
    assist.call_task(session, "t1", "s", parts, {}, 10, model="claude-opus-5-5", effort="high", exact_model=True)
    assert len(set(keys)) == 3
    from app.ai import cache as result_cache

    unchanged = result_cache.cache_key(scope=assist.SCOPE, document_sha256="e" * 64,
                                       evidence_fingerprint=__import__("hashlib").sha256(
                                           json.dumps([["a", "b"]]).encode()).hexdigest(),
                                       task="t1", context={}, parser_version=assist.PARSER_VERSION,
                                       prompt_version=assist.PROMPT_VERSION, schema_version=assist.SCHEMA_VERSION,
                                       model="claude-opus-5-5")
    assert keys[0] == unchanged                                      # tasks without effort keep their old keys


def test_the_damper_look_asks_for_the_configured_model_exactly_at_high_effort(monkeypatch):
    from app.interfaces import visual

    seen = {}

    def fake_call_task(session, task, system, parts, schema, max_output, **kw):
        seen.update(kw)
        return SimpleNamespace(data={"labels": []}, error=None)

    monkeypatch.setattr(visual.assist, "call_task", fake_call_task)
    monkeypatch.setattr(visual.assist, "AssistSession", lambda **kw: SimpleNamespace(**kw))
    visual._ask(1, [{"png": b"png", "window": {"box": (0, 0, 10, 10), "labels": [("SM-1|1.00,1.00|MSD", 1, 1)]},
                     "start": 1}], "f" * 64, None, "X.dwg")
    assert seen["model"] == settings.drawing_review_model == "claude-opus-5-5"
    assert seen["effort"] == settings.drawing_review_effort == "high" and seen["exact_model"] is True
