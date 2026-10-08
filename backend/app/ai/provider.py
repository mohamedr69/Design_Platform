"""The one place a model is called.

Every feature that wants a proposal builds an `AiRequest` and hands it to
`get_provider().complete()`. The provider owns model selection, timeouts,
retries for transport failures, concurrency, in-flight de-duplication,
usage collection and error normalisation. Nothing else imports the SDK.

`ClaudeCodeProvider` (the default) runs the Claude Code CLI on the Claude
subscription signed in on the server -- no API key. `ClaudeProvider`
(Anthropic SDK) and `OpenAiProvider` (OpenAI SDK) call the vendors' APIs with
a key. Each uses JSON-schema output, so what comes back is either a document
matching the task's schema or a normalised error; `AI_PROVIDER` picks one. `NullProvider` answers "insufficient evidence" to everything and
is what runs when AI_ENABLED is false -- the deterministic pipeline must be
complete with it. Tests use `RecordingProvider`.
"""

from __future__ import annotations

import base64
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.ai import guard
from app.core.config import get_settings

log = logging.getLogger(__name__)

# Bumped when the wording of a system prompt changes in a way that could
# change answers; part of every cache key.
PROMPT_VERSION = "2026-09-15.1"

# Reasoning depths both Claude routes accept (CLI `--effort`, API
# `output_config.effort`).
EFFORTS = ("low", "medium", "high", "xhigh", "max")

# The oldest Claude Code that serves a model, where one is known. Checked on
# 2026-10-04: Claude Code 2.1.263 answers claude-opus-5-5 with "version 2.1.280
# or newer is required"; 2.1.288 serves it. A model not listed has no known
# minimum.
CLI_MIN_VERSION: dict[str, tuple[int, int, int]] = {"claude-opus-5-5": (2, 1, 280)}


def is_full_model_id(model: str | None) -> bool:
    """A full model id ("claude-opus-5-5"), not an alias ("opus") that the CLI
    resolves to whatever its version thinks is current (2.1.263: opus ->
    claude-opus-5)."""
    return bool(model) and model.startswith("claude-")


def models_used(model_usage: dict | None, requested: str) -> tuple[str, dict[str, int], list[str]]:
    """What the CLI says actually answered: (the model that answered, output
    tokens per model, the models other than the requested one that took part).

    Claude Code also runs a small Haiku model of its own on every call; that is
    auxiliary, not a substitute, unless Haiku was asked for. Any other model
    in `modelUsage` beside a full requested id is a substitute -- seen once on
    2026-10-04: a claude-fable-5-1 call listing claude-opus-4-8 as well. With
    an alias nothing can be called a substitute: the alias names no one model."""
    per: dict[str, int] = {}
    for name, entry in (model_usage or {}).items():
        per[name] = int((entry or {}).get("outputTokens") or 0) if isinstance(entry, dict) else 0
    wants_haiku = "haiku" in (requested or "")
    main = [n for n in per if wants_haiku or "haiku" not in n]
    counted = any(per[n] for n in main)
    if requested in per:
        used = requested
    elif main:
        used = max(main, key=lambda n: per[n])
    else:
        used = requested
    substitutes = []
    if is_full_model_id(requested):
        substitutes = [n for n in main if n != requested and (per[n] > 0 or not counted)]
    return used, per, substitutes


def model_confirmed(model_usage: dict | None, requested: str) -> bool:
    """Whether the CLI's `modelUsage` shows the requested model itself
    answering (listed, with output). An exact request is accepted only then:
    no usage at all, or only the CLI's auxiliary Haiku, proves nothing."""
    entry = (model_usage or {}).get(requested)
    return isinstance(entry, dict) and int(entry.get("outputTokens") or 0) > 0


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    import re

    found = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(g) for g in found.groups()) if found else None  # type: ignore[return-value]


@dataclass(frozen=True)
class TextPart:
    label: str
    text: str


@dataclass(frozen=True)
class ImagePart:
    label: str
    png: bytes


@dataclass
class AiRequest:
    task: str
    system: str
    parts: list[TextPart | ImagePart]
    schema: dict[str, Any]
    max_output_tokens: int
    tier: str = "small"          # "small" | "standard"
    timeout_s: float | None = None
    idempotency_key: str = ""
    # Reasoning depth for this request (the API provider only): None means
    # the server's AI_EFFORT. Whole-page readings ask for more than a cell.
    effort: str | None = None
    # A model for this request only, overriding the tier's (a task that is
    # configured on its own, e.g. IFC_AI_MODEL). None: the tier's model.
    model: str | None = None
    # The answer counts only from exactly this model: an alias is refused, no
    # server-side fallback is allowed, and a reply that another model took
    # part in is an error (`model_substituted`), never a result.
    exact_model: bool = False
    # Claude Code only: this request's own turn limit (`--max-turns`) and whether its pictures go inside the
    # message; None: the server's AI_CLI_MAX_TURNS / AI_CLI_INLINE_IMAGES.
    max_turns: int | None = None
    inline_images: bool | None = None


@dataclass
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    reasoning_tokens: int | None = None


@dataclass
class AiResponse:
    data: dict[str, Any] | None
    usage: Usage = field(default_factory=Usage)
    model: str = ""
    latency_ms: int = 0
    # "transport" | "timeout" | "rate_limit" | "quota" | "invalid_response" | "refused" | "auth"
    # | "unavailable" (no program/route to call) | "unsupported_model" (the
    # route cannot serve that model) | "model_substituted" (another model
    # answered an exact-model request) | "model_unverified" (the reply does not show
    # the exact model asked for answering) | "invalid_request" | None.
    # A timeout is the provider not answering in time: what the model would
    # have said is unknown, which is not the same as any answer.
    error: str | None = None
    error_detail: str | None = None
    raw_text: str | None = None
    # Output tokens per model that took part, as the route reports it, and
    # whether a model other than the requested one did.
    models_used: dict[str, int] = field(default_factory=dict)
    substituted: bool = False
    route_version: str | None = None
    # The model requests the route made for this one call, when it says
    # (Claude Code's `num_turns`: a Read of each picture is a turn of its own).
    turns: int | None = None
    # What the route says of the call besides (Claude Code's result: subtype, stop reason, durations,
    # its own cost estimate -- an estimate, never a charge): kept for diagnosis, no content.
    route_meta: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None and self.data is not None

    @property
    def retryable(self) -> bool:
        # A spent balance and a bad credential are not worth retrying: they
        # answer the same on the next call and only cost latency.
        return self.error in ("transport", "timeout", "rate_limit")


class AiProvider(Protocol):
    name: str

    def complete(self, request: AiRequest) -> AiResponse: ...

    @property
    def ready(self) -> bool:
        """Whether a call could actually be made. False means the feature is
        on but something it needs -- a credential -- is missing, which the
        pages say plainly rather than discovering at call time."""
        ...

    @property
    def status(self) -> str: ...


def estimate_input_tokens(request: AiRequest) -> int:
    """A pre-call estimate for budget reservation: roughly four characters
    per text token, and a flat allowance per image (a small crop is a few
    hundred tokens; the provider reports the real figure afterwards)."""
    total = len(request.system) // 4 + 200   # schema + framing
    for part in request.parts:
        if isinstance(part, TextPart):
            total += len(part.text) // 4 + 8
        else:
            total += 1_200
    return total


class NullProvider:
    """No model. Every request is answered as insufficient evidence."""

    name = "null"
    ready = False
    status = "AI assistance is disabled (AI_ENABLED=false)"

    def complete(self, request: AiRequest) -> AiResponse:
        return AiResponse(
            data={"task_id": request.task, "status": "insufficient_evidence", "proposed_changes": [],
                  "source_references": [], "unresolved_issues": ["AI assistance is disabled"]},
            model="null",
        )


class RecordingProvider:
    """A scripted provider for tests: answers from a queue, records what it
    was asked, counts calls, and can be told to fail or to sleep."""

    name = "recording"
    ready = True
    status = "a scripted provider (tests)"

    def __init__(self, answers: list[dict | Exception] | None = None, delay_s: float = 0.0):
        self.answers = list(answers or [])
        self.requests: list[AiRequest] = []
        self.calls = 0
        self.delay_s = delay_s
        self._lock = threading.Lock()

    def complete(self, request: AiRequest) -> AiResponse:
        with self._lock:
            self.calls += 1
            self.requests.append(request)
            answer = self.answers.pop(0) if self.answers else {"task_id": request.task, "status": "insufficient_evidence",
                                                               "proposed_changes": [], "source_references": [],
                                                               "unresolved_issues": ["no scripted answer"]}
        if self.delay_s:
            time.sleep(self.delay_s)
        if isinstance(answer, Exception):
            return AiResponse(data=None, error=getattr(answer, "kind", "transport"), error_detail=str(answer), model="recording")
        return AiResponse(data=answer, usage=Usage(input_tokens=500, output_tokens=40), model="recording", latency_ms=1)


class ClaudeProvider:
    """Claude through the official SDK, JSON-schema constrained.

    - Model per tier from settings; no date suffixes are appended.
    - Thinking is left at the model's default (adaptive; always on for
      Claude Fable); depth is `AI_EFFORT`, or the request's own `effort`.
    - Claude Fable runs safety classifiers that can decline a benign scan
      (`stop_reason` "refusal"). Those requests opt into the API's server-side
      fallbacks, so a decline is answered by an Opus model on the same
      request; a refusal that survives that is reported as `refused`.
    - Requests with room for a long answer are streamed, so a whole-page
      reading does not hit the HTTP timeout.
    - Transport and rate-limit errors are retried by the SDK itself
      (`max_retries`); `refusal` stop reasons and unparsable output are
      reported, not retried here -- the caller decides.
    - Usage fields are copied as the SDK reports them; absent ones stay None.
    """

    # Above this the SDK wants streaming to keep the connection alive.
    STREAM_FROM_TOKENS = 8_000
    FALLBACK_BETA = "server-side-fallback-2026-07-01"

    name = "claude"

    def __init__(self) -> None:
        import anthropic  # imported only when the provider is built

        settings = get_settings()
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(timeout=settings.ai_timeout_s, max_retries=settings.ai_max_retries)
        self._models = {"small": settings.ai_model_small, "standard": settings.ai_model_standard}
        self._effort = settings.ai_effort
        self._semaphore = threading.BoundedSemaphore(max(1, settings.ai_max_concurrency))
        # The SDK resolves a credential from the environment (an API key, an
        # auth token, or a signed-in profile) and does not complain until the
        # first call, where it raises a plain TypeError. Ask once, here, so
        # the pages can say "no credential" instead of failing mid-read.
        self._credential = bool(getattr(self._client, "api_key", None) or getattr(self._client, "auth_token", None))

    @property
    def ready(self) -> bool:
        return self._credential

    @property
    def status(self) -> str:
        if self._credential:
            return f"Claude, model {self._models['small']}"
        return "AI is enabled but no credential was found: set ANTHROPIC_API_KEY in the server's environment"

    def _content(self, request: AiRequest) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for part in request.parts:
            if isinstance(part, ImagePart):
                blocks.append({"type": "text", "text": f"[{part.label}]"})
                blocks.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png",
                               "data": base64.standard_b64encode(part.png).decode("ascii")},
                })
            else:
                # Document text is data. It is fenced and labelled so that
                # anything written inside a document reads as content, not
                # as an instruction.
                blocks.append({"type": "text", "text": guard.fence(part.label, part.text)})
        return blocks

    def complete(self, request: AiRequest) -> AiResponse:
        anthropic = self._anthropic
        model = request.model or self._models.get(request.tier, self._models["small"])
        if not self._credential:
            return AiResponse(data=None, error="auth", error_detail=self.status, model=model)
        if request.exact_model and not is_full_model_id(model):
            return AiResponse(data=None, error="unsupported_model", model=model,
                              error_detail=f"{model!r} is an alias; this task needs a full model id")
        effort = request.effort or self._effort
        if effort not in EFFORTS:
            return AiResponse(data=None, error="invalid_request", model=model,
                              error_detail=f"effort {effort!r} is not one of {', '.join(EFFORTS)}")
        started = time.perf_counter()
        client = self._client
        if request.timeout_s:
            client = client.with_options(timeout=request.timeout_s)
        params: dict[str, Any] = dict(
            model=model,
            max_tokens=request.max_output_tokens,
            system=request.system,
            messages=[{"role": "user", "content": self._content(request)}],
            output_config={"format": {"type": "json_schema", "schema": request.schema}, "effort": effort},
        )
        # An exact-model request never opts into server-side fallbacks: an
        # Opus answer to a Fable request would be a silent substitution.
        fable = model.startswith("claude-fable") and not request.exact_model
        if fable:
            params.update(betas=[self.FALLBACK_BETA], fallbacks="default")
        try:
            with self._semaphore:
                messages = client.beta.messages if fable else client.messages
                if request.max_output_tokens >= self.STREAM_FROM_TOKENS:
                    with messages.stream(**params) as stream:
                        message = stream.get_final_message()
                else:
                    message = messages.create(**params)
        except anthropic.AuthenticationError as exc:
            return AiResponse(data=None, error="auth", error_detail=str(exc), model=model)
        except anthropic.RateLimitError as exc:
            return AiResponse(data=None, error="rate_limit", error_detail=str(exc), model=model)
        except anthropic.APIStatusError as exc:
            kind = "transport" if exc.status_code >= 500 else "invalid_response"
            return AiResponse(data=None, error=kind, error_detail=str(exc), model=model)
        except anthropic.APITimeoutError as exc:
            return AiResponse(data=None, error="timeout", error_detail=str(exc), model=model)
        except anthropic.APIConnectionError as exc:
            return AiResponse(data=None, error="transport", error_detail=str(exc), model=model)
        except Exception as exc:  # noqa: BLE001 -- an unreadable request must not take a page down
            return AiResponse(data=None, error="invalid_response", error_detail=str(exc), model=model)

        latency = int((time.perf_counter() - started) * 1000)
        usage = Usage()
        raw_usage = getattr(message, "usage", None)
        if raw_usage is not None:
            usage.input_tokens = getattr(raw_usage, "input_tokens", None)
            usage.output_tokens = getattr(raw_usage, "output_tokens", None)
            usage.cached_input_tokens = getattr(raw_usage, "cache_read_input_tokens", None)
            details = getattr(raw_usage, "output_tokens_details", None)
            usage.reasoning_tokens = getattr(details, "reasoning_tokens", None) if details is not None else None

        # The model that served the reply, as the API says -- after a fallback
        # it is not the one asked for.
        served = getattr(message, "model", None)
        if request.exact_model and not (isinstance(served, str) and served):
            # an exact answer counts only when the reply shows that model answering (R3-7, as F9 for the CLI)
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="model_unverified",
                              error_detail=f"asked for {model}; the reply does not say which model answered")
        served = served if isinstance(served, str) and served else model
        substituted = is_full_model_id(model) and served != model
        if substituted and request.exact_model:
            return AiResponse(data=None, usage=usage, model=served, latency_ms=latency, error="model_substituted",
                              error_detail=f"asked for {model}, answered by {served}",
                              models_used={served: usage.output_tokens or 0}, substituted=True)
        model = served

        if getattr(message, "stop_reason", None) == "refusal":
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="refused",
                              error_detail="the model declined the request")
        text = next((b.text for b in message.content if getattr(b, "type", "") == "text"), None)
        if text is None:
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="invalid_response",
                              error_detail="no text block in the reply")
        try:
            data = json.loads(text)
        except ValueError as exc:
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="invalid_response",
                              error_detail=f"reply is not JSON: {exc}", raw_text=text)
        if getattr(message, "stop_reason", None) == "max_tokens":
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="invalid_response",
                              error_detail="reply was cut off at max_tokens", raw_text=text)
        return AiResponse(data=data, usage=usage, model=model, latency_ms=latency, raw_text=text,
                          models_used={model: usage.output_tokens or 0}, substituted=substituted)


class OpenAiProvider:
    """GPT through the official OpenAI SDK, JSON-schema constrained.

    The same contract as `ClaudeProvider`: a request in, a document matching
    the task's schema or a normalised error out. Two differences the SDK
    forces:

    - **The token parameter moved.** Recent models take
      `max_completion_tokens`; older ones take `max_tokens`. Which one a
      given model wants could not be confirmed against the live API (the
      account had no credits when this was written), so the first call for a
      model tries the newer name and falls back once, remembering the answer.
    - **A spent balance is its own error.** The API reports
      `insufficient_quota` as a 429, which would otherwise be retried as a
      rate limit for as long as the budget allowed. It is reported as
      `quota`, and `quota` is never retried.
    """

    name = "openai"
    base_url: str | None = None

    def __init__(self) -> None:
        import openai  # imported only when the provider is built

        settings = get_settings()
        self._openai = openai
        key = self._key(settings)
        self._models = {"small": settings.ai_model_small, "standard": settings.ai_model_standard}
        self._semaphore = threading.BoundedSemaphore(max(1, settings.ai_max_concurrency))
        # This SDK refuses to build a client at all without a credential,
        # where Anthropic's waits until the first call. Catch that here so
        # "no key" is an answer the pages can show rather than an exception
        # raised while a sheet is being read.
        try:
            self._client = openai.OpenAI(api_key=key, base_url=self.base_url, timeout=settings.ai_timeout_s,
                                         max_retries=settings.ai_max_retries)
            self._credential = bool(key or getattr(self._client, "api_key", None))
        except openai.OpenAIError:
            self._client = None
            self._credential = False
        # model id -> the token parameter it accepts, learned on first use.
        self._token_arg: dict[str, str] = {}

    @staticmethod
    def _key(settings) -> str | None:
        return (settings.ai_api_key or "").strip() or None

    @property
    def ready(self) -> bool:
        return self._credential

    @property
    def status(self) -> str:
        if self._credential:
            return f"OpenAI, model {self._models['small']}"
        return ("AI is enabled but no credential was found: set AI_API_KEY in backend/.env "
                "or OPENAI_API_KEY in the server's environment")

    def _messages(self, request: AiRequest) -> list[dict[str, Any]]:
        content: list[dict[str, Any]] = []
        for part in request.parts:
            if isinstance(part, ImagePart):
                content.append({"type": "text", "text": f"[{part.label}]"})
                url = "data:image/png;base64," + base64.standard_b64encode(part.png).decode("ascii")
                content.append({"type": "image_url", "image_url": {"url": url}})
            else:
                # Document text is data, fenced and labelled so that anything
                # written inside a document reads as content, not instruction.
                content.append({"type": "text", "text": guard.fence(part.label, part.text)})
        return [{"role": "system", "content": request.system}, {"role": "user", "content": content}]

    def _create(self, model: str, request: AiRequest):
        """One call, with the token parameter this model accepts."""
        openai = self._openai
        order = [self._token_arg[model]] if model in self._token_arg else ["max_completion_tokens", "max_tokens"]
        last: Exception | None = None
        for token_arg in order:
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=self._messages(request),
                    response_format={"type": "json_schema",
                                     "json_schema": {"name": "proposal", "schema": request.schema, "strict": True}},
                    **{token_arg: request.max_output_tokens},
                )
                self._token_arg[model] = token_arg
                return response
            except openai.BadRequestError as exc:
                # Only a complaint about the token parameter earns another try.
                if "max_tokens" in str(exc) or "max_completion_tokens" in str(exc):
                    last = exc
                    continue
                raise
        raise last if last is not None else RuntimeError("no call was attempted")

    def complete(self, request: AiRequest) -> AiResponse:
        openai = self._openai
        model = request.model or self._models.get(request.tier, self._models["small"])
        if not self._credential:
            return AiResponse(data=None, error="auth", error_detail=self.status, model=model)
        started = time.perf_counter()
        try:
            with self._semaphore:
                response = self._create(model, request)
        except openai.AuthenticationError as exc:
            return AiResponse(data=None, error="auth", error_detail=str(exc), model=model)
        except openai.RateLimitError as exc:
            spent = "insufficient_quota" in str(exc) or "credit_balance_exhausted" in str(exc)
            detail = ("the account has no credits left; add billing at platform.openai.com and try again"
                      if spent else str(exc))
            return AiResponse(data=None, error="quota" if spent else "rate_limit", error_detail=detail, model=model)
        except openai.APITimeoutError as exc:
            return AiResponse(data=None, error="timeout", error_detail=str(exc), model=model)
        except openai.APIConnectionError as exc:
            return AiResponse(data=None, error="transport", error_detail=str(exc), model=model)
        except openai.APIStatusError as exc:
            kind = "transport" if exc.status_code >= 500 else "invalid_response"
            return AiResponse(data=None, error=kind, error_detail=str(exc), model=model)
        except Exception as exc:  # noqa: BLE001 -- an unreadable request must not take a page down
            return AiResponse(data=None, error="invalid_response", error_detail=str(exc), model=model)

        latency = int((time.perf_counter() - started) * 1000)
        usage = Usage()
        raw = getattr(response, "usage", None)
        if raw is not None:
            usage.input_tokens = getattr(raw, "prompt_tokens", None)
            usage.output_tokens = getattr(raw, "completion_tokens", None)
            prompt_details = getattr(raw, "prompt_tokens_details", None)
            usage.cached_input_tokens = getattr(prompt_details, "cached_tokens", None) if prompt_details else None
            out_details = getattr(raw, "completion_tokens_details", None)
            usage.reasoning_tokens = getattr(out_details, "reasoning_tokens", None) if out_details else None

        choice = response.choices[0] if response.choices else None
        finish = getattr(choice, "finish_reason", None) if choice else None
        if finish == "content_filter":
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="refused",
                              error_detail="the request was filtered")
        text = getattr(getattr(choice, "message", None), "content", None) if choice else None
        if not text:
            detail = "the reply was cut off at the output limit" if finish == "length" else "no content in the reply"
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency,
                              error="invalid_response", error_detail=detail)
        if finish == "length":
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="invalid_response",
                              error_detail="the reply was cut off at the output limit", raw_text=text)
        try:
            data = json.loads(text)
        except ValueError as exc:
            return AiResponse(data=None, usage=usage, model=model, latency_ms=latency, error="invalid_response",
                              error_detail=f"reply is not JSON: {exc}", raw_text=text)
        return AiResponse(data=data, usage=usage, model=model, latency_ms=latency, raw_text=text)


# A call's temporary folder that could not be removed when the call ended,
# to be removed by a later call. On Windows the CLI can still hold an image
# file for a moment after it exits (PermissionError, WinError 32); the
# removal is retried, then deferred -- and never fails the call whose
# result is already in hand (EP-30784, 2026-09-26: a whole sheet "not
# read" and an AI check failed for a folder that could not be deleted).
_deferred_folders: list[str] = []
_deferred_lock = threading.Lock()
FOLDER_RELEASE_ATTEMPTS = 5


def release_folder(folder: str, *, attempts: int = FOLDER_RELEASE_ATTEMPTS) -> bool:
    """Remove a call's temporary folder: retried briefly, then deferred.
    True when it is gone."""
    import shutil

    for attempt in range(attempts):
        try:
            shutil.rmtree(folder)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            time.sleep(0.2 * (attempt + 1))
    log.warning("The temporary folder %s is still in use; it will be removed by a later call", folder)
    with _deferred_lock:
        _deferred_folders.append(folder)
    return False


def sweep_deferred_folders() -> int:
    """Remove the folders earlier calls could not. Returns how many remain."""
    import shutil

    with _deferred_lock:
        pending = list(_deferred_folders)
        _deferred_folders.clear()
    left = []
    for folder in pending:
        try:
            shutil.rmtree(folder)
        except FileNotFoundError:
            continue
        except OSError:
            left.append(folder)
    with _deferred_lock:
        _deferred_folders.extend(left)
        return len(_deferred_folders)


class ClaudeCodeProvider:
    """Claude through the Claude Code CLI, on the subscription it is signed in with.

    No API key: the server runs the `claude` program installed on this machine
    (`AI_CLAUDE_CLI`, default `claude` on the PATH) headless, once per request,
    and Claude Code bills the call to the Claude subscription that is signed in
    there. The same contract as the other providers -- a request in, a document
    matching the task's schema or a normalised error out:

    - The task's JSON schema goes to `--json-schema`; the reply's
      `structured_output` is the document.
    - The task's system prompt replaces Claude Code's own (`--system-prompt`),
      so a call carries only what the task needs.
    - Images are written to a private temporary folder the call runs in, and
      Claude reads them with the Read tool -- the only tool it is given, and
      only when there is an image. With no image it has no tools at all.
    - The prompt goes in on stdin: Windows caps a command line at 32,767
      characters and a batch of clauses is longer than that.
    - `ANTHROPIC_API_KEY` is removed from the call's environment, so the CLI
      uses the subscription even on a machine that also has a key set.
    - Sessions are not saved (`--no-session-persistence`).

    - `--effort` carries the request's reasoning depth when it names one.
    - The CLI's version is read once (`claude --version`) when a model with a
      known minimum (`CLI_MIN_VERSION`) needs it; a CLI too old for the model
      is `unsupported_model` before any call.
    - What answered is read from `modelUsage`; an exact-model request that
      another model took part in is `model_substituted`. `--fallback-model`
      is never passed.
    - No program at the configured path is `unavailable`, not `auth`.

    Checked against Claude Code 2.1.263 on 2026-09-14 and 2.1.288 on 2026-10-04.
    """

    name = "claude-code"

    def __init__(self) -> None:
        import shutil

        settings = get_settings()
        configured = (settings.ai_claude_cli or "claude").strip()
        self._configured = configured
        self._cli = shutil.which(configured) or (configured if Path(configured).is_file() else None)
        self._models = {"small": settings.ai_model_small, "standard": settings.ai_model_standard}
        self._timeout = settings.ai_cli_timeout_s
        self._max_turns = settings.ai_cli_max_turns
        self._semaphore = threading.BoundedSemaphore(max(1, settings.ai_max_concurrency))
        self._version: tuple[int, int, int] | None = None
        self._version_text: str | None = None
        self._version_read = False
        self._version_lock = threading.Lock()

    @property
    def ready(self) -> bool:
        return self._cli is not None

    @property
    def status(self) -> str:
        if self._cli:
            version = f" {self._version_text}" if self._version_text else ""
            return f"Claude subscription through Claude Code{version}, model {self._models['small']}"
        return (f"AI is enabled but Claude Code was not found at {self._configured}: install it and sign in with "
                "`claude` as the user the server runs as, or set AI_CLAUDE_CLI to the path of claude.exe "
                "(%LOCALAPPDATA% and ~ are expanded)")

    def cli_version(self) -> tuple[int, int, int] | None:
        """`claude --version`, read once; None when it cannot be read."""
        import subprocess

        with self._version_lock:
            if not self._version_read and self._cli:
                self._version_read = True
                try:
                    out = subprocess.run([self._cli, "--version"], capture_output=True, text=True, encoding="utf-8",
                                         errors="replace", timeout=30)
                    self._version = parse_version(out.stdout)
                    self._version_text = (out.stdout or "").strip()[:60] or None
                except Exception:  # noqa: BLE001 -- an unreadable version is "unknown", decided by the caller
                    self._version = None
            return self._version

    def supports(self, model: str, *, exact: bool = False) -> tuple[bool, str | None]:
        """Whether this CLI can serve `model`, before any call is made:
        (True, None) or (False, the reason)."""
        if not self._cli:
            return False, self.status
        if exact and not is_full_model_id(model):
            return False, f"{model!r} is an alias; this task needs a full model id"
        minimum = CLI_MIN_VERSION.get(model)
        if minimum is None:
            return True, None
        version = self.cli_version()
        need = ".".join(map(str, minimum))
        if version is None:
            return False, f"the Claude Code version could not be read; {model} needs {need} or newer"
        if version < minimum:
            return False, f"Claude Code {'.'.join(map(str, version))} does not serve {model}; {need} or newer is needed"
        return True, None

    @staticmethod
    def _prompt(request: AiRequest, images: list[tuple[str, str]]) -> str:
        lines = []
        for part in request.parts:
            if isinstance(part, TextPart):
                # Document text is data, fenced and labelled so that anything
                # written inside a document reads as content, not instruction.
                lines.append(guard.fence(part.label, part.text))
        for label, filename in images:
            lines.append(f"[{label}] is the image file {filename} in the current directory: read it with the Read tool.")
        lines.append("Answer through the structured output only.")
        return "\n\n".join(lines)

    @classmethod
    def _message(cls, request: AiRequest, pictures: list) -> str:
        """The request as one stream-json user message, each picture inline
        after its label (AI_CLI_INLINE_IMAGES)."""
        content: list[dict[str, Any]] = [{"type": "text", "text": cls._prompt(request, [])}]
        for part in pictures:
            content.append({"type": "text", "text": f"[{part.label}]:"})
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.b64encode(part.png).decode()}})
        return json.dumps({"type": "user", "message": {"role": "user", "content": content}}) + "\n"

    @staticmethod
    def _result_of_stream(stdout: str) -> dict:
        """The final `result` message of a stream-json reply (the same fields
        as the json output); ValueError when there is none."""
        result = None
        for line in (stdout or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                message = json.loads(line)
            except ValueError:
                continue
            if isinstance(message, dict) and message.get("type") == "result":
                result = message
        if result is None:
            raise ValueError("no result message in the stream")
        return result

    @staticmethod
    def _error_kind(text: str) -> str:
        lowered = text.lower()
        if "max_turns" in lowered or "maximum number of turns" in lowered:
            return "max_turns"
        if any(s in lowered for s in ("does not support this model", "unrecognized_model", "unrecognized model",
                                      "or newer is required")):
            return "unsupported_model"
        if any(s in lowered for s in ("not logged in", "please run /login", "invalid api key", "authentication", "oauth")):
            return "auth"
        if any(s in lowered for s in ("usage limit", "rate limit", "rate_limit", "overloaded", "limit reached")):
            return "rate_limit"
        return "invalid_response"

    def complete(self, request: AiRequest) -> AiResponse:
        import os
        import subprocess
        import tempfile

        model = request.model or self._models.get(request.tier, self._models["small"])
        if not self._cli:
            return AiResponse(data=None, error="unavailable", error_detail=self.status, model=model)
        if request.effort is not None and request.effort not in EFFORTS:
            return AiResponse(data=None, error="invalid_request", model=model,
                              error_detail=f"effort {request.effort!r} is not one of {', '.join(EFFORTS)}")
        able, why = self.supports(model, exact=request.exact_model)
        if not able:
            return AiResponse(data=None, error="unsupported_model", error_detail=why, model=model,
                              route_version=self._version_text)
        started = time.perf_counter()
        sweep_deferred_folders()
        folder = tempfile.mkdtemp(prefix="ep-ai-")
        pictures = [p for p in request.parts if isinstance(p, ImagePart)]
        inline = bool(pictures) and (request.inline_images if request.inline_images is not None
                                     else get_settings().ai_cli_inline_images)
        max_turns = request.max_turns if request.max_turns is not None else self._max_turns
        try:
            images = []
            if not inline:
                for index, part in enumerate(pictures):
                    filename = f"image-{index + 1}.png"
                    (Path(folder) / filename).write_bytes(part.png)
                    images.append((part.label, filename))
            args = [self._cli, "-p", "--output-format", "stream-json" if inline else "json", "--model", model,
                    "--system-prompt", request.system, "--json-schema", json.dumps(request.schema),
                    "--no-session-persistence", "--disable-slash-commands", "--strict-mcp-config"]
            if inline:
                # the pictures inside the message: no Read turn a picture
                args += ["--input-format", "stream-json", "--verbose"]
            if request.effort:
                args += ["--effort", request.effort]
            if max_turns:
                args += ["--max-turns", str(max_turns)]
            args += ["--tools", "Read", "--allowedTools", "Read"] if images else ["--tools", ""]
            env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
            settings = get_settings()
            if settings.ai_cli_disable_nonessential_traffic:
                env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
            if settings.ai_cli_max_retries is not None:
                env["CLAUDE_CODE_MAX_RETRIES"] = str(settings.ai_cli_max_retries)
            stdin = self._message(request, pictures) if inline else self._prompt(request, images)
            try:
                with self._semaphore:
                    completed = subprocess.run(
                        args, input=stdin, capture_output=True, text=True, encoding="utf-8",
                        errors="replace", cwd=folder, env=env, timeout=request.timeout_s or self._timeout,
                    )
            except subprocess.TimeoutExpired:
                return AiResponse(data=None, error="timeout", model=model, route_version=self._version_text,
                                  error_detail=f"Claude Code did not answer within {request.timeout_s or self._timeout:.0f} s")
            except OSError as exc:
                return AiResponse(data=None, error="transport", error_detail=f"Claude Code could not be started: {exc}", model=model)
        finally:
            # The call's result (or its failure) is in hand: removing the
            # folder can neither change it nor fail it.
            release_folder(folder)
        latency = int((time.perf_counter() - started) * 1000)

        try:
            reply = self._result_of_stream(completed.stdout) if inline else json.loads(completed.stdout)
        except ValueError:
            detail = (completed.stderr or completed.stdout or "no output").strip()[:500]
            return AiResponse(data=None, error=self._error_kind(detail), error_detail=detail, model=model, latency_ms=latency)
        raw_usage = reply.get("usage") or {}
        usage = Usage(
            input_tokens=sum(int(raw_usage.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
            output_tokens=raw_usage.get("output_tokens"),
            cached_input_tokens=raw_usage.get("cache_read_input_tokens"),
            reasoning_tokens=(raw_usage.get("output_tokens_details") or {}).get("thinking_tokens"),
        )
        used, per_model, substitutes = models_used(reply.get("modelUsage"), model)
        turns = reply.get("num_turns")
        meta = {k: reply.get(k) for k in ("subtype", "num_turns", "stop_reason", "terminal_reason", "duration_ms",
                                          "duration_api_ms", "total_cost_usd") if k in reply}
        meta["max_turns_configured"] = max_turns
        meta["inline_images"] = inline
        common = dict(usage=usage, model=used, latency_ms=latency, models_used=per_model,
                      substituted=bool(substitutes), route_version=self._version_text,
                      turns=turns if isinstance(turns, int) else None, route_meta=meta)
        if reply.get("is_error") or reply.get("subtype") != "success":
            detail = str(reply.get("result") or reply.get("subtype") or "Claude Code reported an error")[:500]
            return AiResponse(data=None, error=self._error_kind(detail), error_detail=detail, **common)
        if substitutes and request.exact_model:
            return AiResponse(data=None, error="model_substituted", **common,
                              error_detail=f"asked for {model}, but {', '.join(substitutes)} also answered")
        if request.exact_model and not model_confirmed(reply.get("modelUsage"), model):
            # no usage, or only the CLI's own Haiku: nothing shows the model asked for answered
            return AiResponse(data=None, error="model_unverified", **common,
                              error_detail=f"asked for {model}, but the reply does not show it answering "
                                           f"(models listed: {', '.join(sorted(per_model)) or 'none'})")
        data = reply.get("structured_output")
        if not isinstance(data, dict):
            return AiResponse(data=None, error="invalid_response", error_detail="the reply carried no structured output",
                              raw_text=str(reply.get("result"))[:2000], **common)
        return AiResponse(data=data, raw_text=str(reply.get("result"))[:2000], **common)


_provider: AiProvider | None = None
_fa_provider: AiProvider | None = None
_prep_provider: AiProvider | None = None
_review_provider: AiProvider | None = None
_chat_provider: AiProvider | None = None
_provider_lock = threading.Lock()
_BUILDERS = {"claude-code": ClaudeCodeProvider, "claude_code": ClaudeCodeProvider, "subscription": ClaudeCodeProvider,
             "claude": ClaudeProvider, "anthropic": ClaudeProvider, "openai": OpenAiProvider, "gpt": OpenAiProvider}


def _build(settings) -> AiProvider:
    build = _BUILDERS.get(settings.ai_provider.lower())
    if build is None:
        return NullProvider()
    try:
        return build()
    except Exception:  # noqa: BLE001 -- a provider that cannot be built is a disabled one
        return NullProvider()


def get_provider() -> AiProvider:
    """The configured provider, built once. `NullProvider` whenever AI is
    off, so callers never need to check the flag themselves."""
    global _provider
    with _provider_lock:
        if _provider is None:
            settings = get_settings()
            _provider = _build(settings) if settings.ai_enabled else NullProvider()
        return _provider


def fa_ai_on() -> bool:
    """Whether the FA Interfaces drawing workflow's models may be called:
    AI_ENABLED, or FA_AI_ENABLED for this workflow alone."""
    settings = get_settings()
    return bool(settings.ai_enabled or settings.fa_ai_enabled)


def get_fa_provider() -> AiProvider:
    """The FA Interfaces drawing workflow's provider (its Opus drawing agents
    and Opus review): the platform's own when AI_ENABLED is on; when only
    FA_AI_ENABLED is, the same route built for this workflow alone, while
    every other caller keeps the NullProvider."""
    global _fa_provider
    settings = get_settings()
    if settings.ai_enabled or not settings.fa_ai_enabled:
        return get_provider()
    with _provider_lock:
        if _fa_provider is None:
            _fa_provider = _build(settings)
            if hasattr(_fa_provider, "_semaphore"):          # this workflow's own bound on calls at once
                _fa_provider._semaphore = threading.BoundedSemaphore(max(1, settings.fa_max_concurrency))
        return _fa_provider


def prep_ai_on() -> bool:
    """Whether Drawings Preparation's agents may be called: AI_ENABLED, or
    PREP_AI_ENABLED for them alone."""
    settings = get_settings()
    return bool(settings.ai_enabled or settings.prep_ai_enabled)


def get_prep_provider() -> AiProvider:
    """Drawings Preparation's provider (its Opus placement and coordination
    agents and Opus orchestrator): the platform's own when AI_ENABLED is on;
    when only PREP_AI_ENABLED is, the same route built for it alone, with its
    own bound on calls at once."""
    global _prep_provider
    settings = get_settings()
    if settings.ai_enabled or not settings.prep_ai_enabled:
        return get_provider()
    with _provider_lock:
        if _prep_provider is None:
            _prep_provider = _build(settings)
            if hasattr(_prep_provider, "_semaphore"):
                _prep_provider._semaphore = threading.BoundedSemaphore(max(1, settings.prep_max_concurrency))
        return _prep_provider


def review_ai_on() -> bool:
    """Whether the Drawings Review's looks may be called: AI_ENABLED, or
    DRAWING_REVIEW_AI_ENABLED for them alone."""
    settings = get_settings()
    return bool(settings.ai_enabled or settings.drawing_review_ai_enabled)


def get_review_provider() -> AiProvider:
    """The Drawings Review's provider: the platform's own when AI_ENABLED is
    on (or a test swapped it in); when only DRAWING_REVIEW_AI_ENABLED is, the
    same route built for the review alone, with its own bound on calls at
    once, while every other caller keeps the NullProvider."""
    global _review_provider
    settings = get_settings()
    swapped = _provider is not None and not isinstance(_provider, NullProvider)
    if settings.ai_enabled or not settings.drawing_review_ai_enabled or swapped:
        return get_provider()
    with _provider_lock:
        if _review_provider is None:
            _review_provider = _build(settings)
            if hasattr(_review_provider, "_semaphore"):
                _review_provider._semaphore = threading.BoundedSemaphore(max(1, settings.drawing_review_parallel))
        return _review_provider


def chat_ai_on() -> bool:
    """Whether the Drawings Assistant may be called: AI_ENABLED, or
    DRAWINGS_CHAT_AI_ENABLED for it alone."""
    settings = get_settings()
    return bool(settings.ai_enabled or settings.drawings_chat_ai_enabled)


def get_chat_provider() -> AiProvider:
    """The Drawings Assistant's provider: the platform's own when AI_ENABLED
    is on (or a test swapped it in); when only DRAWINGS_CHAT_AI_ENABLED is,
    the same route built for the assistant alone, while every other caller
    keeps the NullProvider."""
    global _chat_provider
    settings = get_settings()
    swapped = _provider is not None and not isinstance(_provider, NullProvider)
    if settings.ai_enabled or not settings.drawings_chat_ai_enabled or swapped:
        return get_provider()
    with _provider_lock:
        if _chat_provider is None:
            _chat_provider = _build(settings)
        return _chat_provider


_classification_provider: AiProvider | None = None


def classification_ai_on() -> bool:
    """Whether the documents' classification may ask the model: AI_ENABLED,
    or DOCUMENT_CLASSIFICATION_AI_ENABLED for it alone."""
    settings = get_settings()
    return bool(settings.ai_enabled or settings.document_classification_ai_enabled)


def get_classification_provider() -> AiProvider:
    """The classification's provider, as `get_chat_provider` is the chat's:
    the platform's own when AI_ENABLED is on (or a test swapped it in); built
    for it alone when only DOCUMENT_CLASSIFICATION_AI_ENABLED is."""
    global _classification_provider
    settings = get_settings()
    swapped = _provider is not None and not isinstance(_provider, NullProvider)
    if settings.ai_enabled or not settings.document_classification_ai_enabled or swapped:
        return get_provider()
    with _provider_lock:
        if _classification_provider is None:
            _classification_provider = _build(settings)
        return _classification_provider


def set_provider(provider: AiProvider | None) -> None:
    """Swap the provider (tests, or a diagnostics switch)."""
    global _provider, _fa_provider, _prep_provider, _review_provider, _chat_provider, _classification_provider
    with _provider_lock:
        _provider = provider
        if provider is None:
            _fa_provider = None
            _prep_provider = None
            _review_provider = None
            _chat_provider = None
            _classification_provider = None
