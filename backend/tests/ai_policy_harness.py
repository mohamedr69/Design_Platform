"""The forced-blocked harness (ORCH-051, made permanent by ORCH-053): a pytest
plugin, loaded with `-p tests.ai_policy_harness` in a child pytest run by
tests/test_ai_policy_enforcement.py (never on its own in the suite).

It records, per test,

- every `AiRequest` built by the application (the moment content becomes a
  request: task, the module that built it, each part's label, kind and size),
- every input a `RecordingProvider` or `NullProvider` was given,
- every real provider dispatch (ClaudeProvider / OpenAiProvider /
  ClaudeCodeProvider `.complete`), `claude` subprocess and non-local socket
  connect -- each blocked and counted,

and writes them to EP_AI_POLICY_HARNESS_OUT. With EP_AI_POLICY_FORCE_BLOCKED=1
every project row inserted gets `ai_policy = "blocked"`, so a test that still
puts project content into a request shows a path with no policy gate. The
child's tests are expected to fail in that mode (they assert on answers that
are now refused); the record is the evidence.
"""
from __future__ import annotations

import inspect
import json
import os
import socket
import subprocess

import pytest

OUT = os.environ.get("EP_AI_POLICY_HARNESS_OUT", "ai-policy-harness.json")
FORCE_BLOCKED = os.environ.get("EP_AI_POLICY_FORCE_BLOCKED") == "1"
RECORD = {"force_blocked": FORCE_BLOCKED, "real_complete": 0, "claude_subprocess": 0, "socket_connect_non_local": 0,
          "real_dispatches": [], "requests": [], "provider_inputs": [], "tests": 0, "outcomes": {}}
_current = {"id": None}
_orig_run, _orig_popen_init, _orig_connect = subprocess.run, subprocess.Popen.__init__, socket.socket.connect


def _is_claude(args) -> bool:
    first = args[0] if isinstance(args, (list, tuple)) and args else args
    return "claude" in os.path.basename(str(first)).lower()


def _run(*a, **k):
    if a and _is_claude(a[0]):
        RECORD["claude_subprocess"] += 1
        raise RuntimeError("ai policy harness: claude subprocess blocked")
    return _orig_run(*a, **k)


def _popen_init(self, *a, **k):
    if a and _is_claude(a[0]):
        RECORD["claude_subprocess"] += 1
        raise RuntimeError("ai policy harness: claude subprocess blocked")
    return _orig_popen_init(self, *a, **k)


def _connect(self, address):
    host = address[0] if isinstance(address, tuple) else str(address)
    if host not in ("127.0.0.1", "localhost", "::1"):
        RECORD["socket_connect_non_local"] += 1
        raise OSError("ai policy harness: outbound connection blocked")
    return _orig_connect(self, address)


subprocess.run = _run
subprocess.Popen.__init__ = _popen_init
socket.socket.connect = _connect


def _parts(request) -> list[list]:
    out = []
    for p in getattr(request, "parts", None) or []:
        if hasattr(p, "png"):
            out.append([p.label, "image", len(p.png or b"")])
        else:
            out.append([p.label, "text", len(getattr(p, "text", "") or "")])
    return out


def pytest_configure(config):
    from app.ai import provider as P

    def blocked(name):
        def complete(self, request, **_kw):
            RECORD["real_complete"] += 1
            # who built the request: a provider's own unit test (tests.*) or the application (app.*)
            RECORD["real_dispatches"].append({"test": _current["id"], "provider": name,
                                              "task": getattr(request, "task", None),
                                              "origin": getattr(request, "_harness_origin", "?")})
            raise RuntimeError(f"ai policy harness: real provider {name}.complete blocked")
        return complete

    for name in ("ClaudeProvider", "OpenAiProvider", "ClaudeCodeProvider"):
        setattr(getattr(P, name), "complete", blocked(name))

    original_init = P.AiRequest.__init__

    def init(self, *a, **k):
        original_init(self, *a, **k)
        frame = inspect.currentframe().f_back
        while frame is not None and frame.f_globals.get("__name__", "").startswith("dataclasses"):
            frame = frame.f_back
        origin = frame.f_globals.get("__name__", "?") if frame is not None else "?"
        self._harness_origin = origin
        RECORD["requests"].append({"test": _current["id"], "task": self.task, "origin": origin,
                                   "parts": _parts(self)})

    P.AiRequest.__init__ = init

    def recorded(cls):
        original = cls.complete

        def complete(self, request, **kw):
            RECORD["provider_inputs"].append({"test": _current["id"], "provider": cls.__name__,
                                              "task": getattr(request, "task", None), "parts": _parts(request),
                                              "origin": getattr(request, "_harness_origin", "?")})
            return original(self, request, **kw)
        cls.complete = complete

    recorded(P.RecordingProvider)
    recorded(P.NullProvider)

    if FORCE_BLOCKED:
        from sqlalchemy import event

        from app.models import Project

        @event.listens_for(Project, "before_insert")
        def _blocked(_mapper, _connection, target):
            target.ai_policy = "blocked"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    _current["id"] = item.nodeid
    RECORD["tests"] += 1
    yield
    _current["id"] = None


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        RECORD["outcomes"][report.outcome] = RECORD["outcomes"].get(report.outcome, 0) + 1


def pytest_unconfigure(config):
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(RECORD, fh, indent=1)
