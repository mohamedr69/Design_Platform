"""A scripted provider keyed by (task, field, tier) -- M2 review 18 (R18-03).

The positional `RecordingProvider` answers the n-th request with the n-th scripted answer, whatever was asked: with the
targeted reader (T) an extra context read took the answer scripted for another field (review 18 reproduced it). Here
every answer is selected by what the request is for:
  task   the request's task; `discover` matches either discovery task (`discover_page`, E's `discover_region`)
  field  identity / revision / decision for the value / decision reads; for `read_field_context` taken from the
         request's own prompt ("OWN identity" / "OWN current revision"); None for discovery
  tier   small / standard
A value is one answer (reused) or a list (consumed in order for repeated requests of the same key); an exception with
`kind` is a provider failure. A request nobody scripted fails the test (AssertionError) instead of receiving an
unrelated answer. `requests` records every key asked, in order."""
from __future__ import annotations

from app.ai.provider import AiResponse, TextPart, Usage

_FIELD = {"read_identity": "identity", "read_revision": "revision", "read_decision": "decision"}


def key_of(request) -> tuple:
    task = request.task
    field = _FIELD.get(task)
    if task == "read_field_context":
        text = " ".join(p.text for p in request.parts if isinstance(p, TextPart))
        field = "identity" if "OWN identity" in text else "revision" if "OWN current revision" in text else None
    return task, field, request.tier


class KeyedProvider:
    name = "keyed"
    ready = True
    status = "a scripted provider keyed by task / field / tier (tests)"

    def __init__(self, answers: dict) -> None:
        self.answers = {k: (list(v) if isinstance(v, list) else v) for k, v in answers.items()}
        self.requests: list[tuple] = []
        self.calls = 0

    def _lookup(self, key: tuple):
        if key in self.answers:
            return key
        task, field, tier = key
        if task.startswith("discover") and ("discover", field, tier) in self.answers:
            return ("discover", field, tier)
        raise AssertionError(f"unscripted request {key}: a keyed test scripts every request it expects")

    def complete(self, request):
        key = key_of(request)
        self.calls += 1
        self.requests.append(key)
        slot = self._lookup(key)
        answer = self.answers[slot]
        if isinstance(answer, list):
            if not answer:
                raise AssertionError(f"no scripted answer left for {slot}")
            answer = answer.pop(0)
        if isinstance(answer, Exception):
            return AiResponse(data=None, error=getattr(answer, "kind", "transport"), error_detail=str(answer), model="keyed")
        return AiResponse(data=answer, usage=Usage(input_tokens=500, output_tokens=40), model="keyed", latency_ms=1)


def failure(kind: str = "timeout") -> Exception:
    e = RuntimeError(f"scripted {kind}")
    e.kind = kind
    return e
