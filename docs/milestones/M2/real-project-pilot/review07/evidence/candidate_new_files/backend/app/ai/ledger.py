"""A persistent, shared AI budget ledger (M2 review 07, R7-04).

What it is for: bounded, owner-authorised model use across every track of a run (document variants, BOQ, the
application's own AI paths) -- request, token and time caps that hold across documents, threads, processes and
restarts, without inventing prices.

What it can and cannot guarantee -- stated, not implied:

* **Before a request** it reserves an *estimate* and refuses to dispatch when the reservation would pass a cap, or
  when the circuit breaker is open. This is the only point at which a request can be prevented.
* **After a request** it records the provider's reported usage, reconciles the reservation and detects overshoots.
  A request that used more than estimated cannot be made retroactively smaller; the ledger records it and, when a
  per-request or aggregate cap has been passed, opens the circuit breaker so no *further* request is dispatched.
* **Provider-enforced limits:** the Anthropic API adapter passes `max_tokens`, a hard output limit. The Claude Code
  CLI adapter (`claude -p`) has no output or input limit flag: its outputs (thinking and tool turns included) and
  inputs (its wrapper, the tool call that reads an image, cache reads) are *estimated*, never enforced. Its
  observed usage per task (690 recorded requests, 2026-09-28/29) calibrates the estimate below.
* **Units:** `requests` = application-visible provider requests (one `complete()`); provider-internal turns are
  recorded when the provider reports them (`turns`), never inferred. `input_tokens` = the provider's input total
  including cache creation and cache reads; `cached_input_tokens` = the cache-read part of it (also counted in
  `input_tokens`); `output_tokens` = as reported (thinking included when the provider counts it). A cache hit in the
  application's result cache is no request and no tokens (`cache_hits`). A timeout or transport failure with no
  usage report is charged at its reservation and marked `usage_unknown`.
* **Money:** no price is assumed. Cost stays unknown unless the owner configures trustworthy prices.
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import struct
import threading
import time
from dataclasses import dataclass, field

LEDGER_VERSION = "ai-ledger-2026-09-29.1"
ESTIMATOR_VERSION = "estimator-2026-09-29.1"

# Observed p95 (input, output) tokens per task on the claude-code adapter, from the 690 requests of 2026-09-28/29
# (review 06 experiment, recorded in `review06/evidence`). Used as a floor on the analytic estimate.
CALIBRATION_P95 = {
    "discover_page": (45_544, 10_870), "read_identity": (10_283, 1_102), "read_revision": (8_573, 508),
    "read_decision": (18_171, 6_351), "read_boq_row": (5_523, 628), "read_submittal_form": (25_057, 3_881),
    "read_sheet_page": (7_756, 14_726), "read_sheet_row_close_up": (6_110, 1_722), "read_cell": (5_676, 643),
    "verify_boq_row_crops": (17_143, 16_210),
}
CLI_WRAPPER_TOKENS = 4_500        # the smallest observed claude-code request (a tiny crop) was ~4.5-5.2k input
CLI_IMAGE_TURNS = 2               # with an image, the CLI reads it with a tool: the prompt is sent twice


class LedgerRefused(Exception):
    def __init__(self, limit: str, detail: str = "") -> None:
        super().__init__(f"{limit}: {detail}" if detail else limit)
        self.limit = limit
        self.detail = detail


def _png_size(png: bytes) -> tuple[int, int]:
    if png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) >= 24:
        return struct.unpack(">II", png[16:24])
    try:
        from PIL import Image

        with Image.open(io.BytesIO(png)) as im:
            return im.size
    except Exception:  # noqa: BLE001 -- an unreadable image is estimated at the largest size a provider accepts
        return 1568, 1568


def image_tokens(png: bytes) -> int:
    """Anthropic's published rule of thumb: a vision image costs about width x height / 750 tokens after it is scaled
    to at most 1568 px on the long side and about 1.15 megapixels."""
    w, h = _png_size(png)
    scale = min(1.0, 1568 / max(w, h, 1))
    w, h = w * scale, h * scale
    if w * h > 1_150_000:
        f = (1_150_000 / (w * h)) ** 0.5
        w, h = w * f, h * f
    return int(w * h / 750) + 1


def estimate(request, adapter: str) -> tuple[int, int]:
    """(input, output) tokens to reserve for a request on an adapter: the larger of an analytic estimate and the
    task's calibrated p95. Text ~3.5 characters per token."""
    from app.ai.provider import ImagePart, TextPart

    text = len(request.system) + len(json.dumps(request.schema))
    images = 0
    for part in request.parts:
        if isinstance(part, TextPart):
            text += len(part.text)
        elif isinstance(part, ImagePart):
            images += image_tokens(part.png)
    analytic_in = int(text / 3.5) + images
    analytic_out = int(request.max_output_tokens)
    if adapter in ("claude-code", "claude_code", "subscription"):
        turns = CLI_IMAGE_TURNS if images else 1
        analytic_in = (CLI_WRAPPER_TOKENS + int(text / 3.5)) * turns + images
        task = request.task.split(":")[-1]
        cal_in, cal_out = CALIBRATION_P95.get(task, (0, 0))
        return max(analytic_in, cal_in), max(analytic_out, cal_out)
    return analytic_in, analytic_out


@dataclass
class Limits:
    requests: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    per_request_input: int | None = None
    per_request_output: int | None = None
    elapsed_s: float | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Ledger:
    path: str
    scope: str
    limits: Limits = field(default_factory=Limits)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with self._connect() as con:
            con.executescript("""
                create table if not exists scopes (scope text primary key, limits text, created_at real, breaker text);
                create table if not exists entries (
                    id integer primary key autoincrement, scope text, at real, task text, adapter text, model text,
                    state text, est_in integer, est_out integer, act_in integer, act_out integer, cached_in integer,
                    turns integer, latency_ms integer, outcome text, usage_unknown integer default 0, pid integer, note text);
                create index if not exists entries_scope on entries(scope);
            """)
            row = con.execute("select limits from scopes where scope = ?", (self.scope,)).fetchone()
            if row is None:
                con.execute("insert into scopes values (?, ?, ?, null)", (self.scope, json.dumps(self.limits.as_dict()), time.time()))
            elif not self.limits.as_dict():
                self.limits = Limits(**json.loads(row[0]))

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        con.execute("pragma journal_mode=wal")
        return con

    # --- totals ------------------------------------------------------------------------------------------------------

    def _totals(self, con) -> dict:
        r = con.execute("""
            select count(*) filter (where state != 'cache_hit' and state != 'refused'),
                   coalesce(sum(case when state = 'reserved' then est_in else coalesce(act_in, est_in) end) filter (where state not in ('cache_hit', 'refused')), 0),
                   coalesce(sum(case when state = 'reserved' then est_out else coalesce(act_out, est_out) end) filter (where state not in ('cache_hit', 'refused')), 0),
                   count(*) filter (where state = 'cache_hit'), count(*) filter (where state = 'refused'),
                   count(*) filter (where usage_unknown = 1), count(*) filter (where state = 'reserved')
            from entries where scope = ?""", (self.scope,)).fetchone()
        created, breaker = con.execute("select created_at, breaker from scopes where scope = ?", (self.scope,)).fetchone()
        return {"requests": r[0], "input_tokens": r[1], "output_tokens": r[2], "cache_hits": r[3], "refused": r[4],
                "usage_unknown": r[5], "in_flight": r[6], "elapsed_s": time.time() - created, "breaker": breaker}

    def totals(self) -> dict:
        with self._connect() as con:
            return self._totals(con)

    # --- reserve / settle -----------------------------------------------------------------------------------------

    def reserve(self, task: str, est_in: int, est_out: int, *, adapter: str = "", model: str = "") -> int:
        """Atomically reserve a request, or raise LedgerRefused (and record the refusal)."""
        L = self.limits
        with self._lock, self._connect() as con:
            con.execute("begin immediate")
            t = self._totals(con)
            why = None
            if t["breaker"]:
                why = ("breaker", t["breaker"])
            elif L.requests is not None and t["requests"] + 1 > L.requests:
                why = ("requests", f"{t['requests']} of {L.requests} used")
            elif L.per_request_input is not None and est_in > L.per_request_input:
                why = ("per_request_input", f"estimate {est_in} > {L.per_request_input}")
            elif L.per_request_output is not None and est_out > L.per_request_output:
                why = ("per_request_output", f"estimate {est_out} > {L.per_request_output}")
            elif L.input_tokens is not None and t["input_tokens"] + est_in > L.input_tokens:
                why = ("input_tokens", f"{t['input_tokens']} + {est_in} > {L.input_tokens}")
            elif L.output_tokens is not None and t["output_tokens"] + est_out > L.output_tokens:
                why = ("output_tokens", f"{t['output_tokens']} + {est_out} > {L.output_tokens}")
            elif L.elapsed_s is not None and t["elapsed_s"] > L.elapsed_s:
                why = ("elapsed_s", f"{t['elapsed_s']:.0f} s > {L.elapsed_s:.0f} s")
            if why:
                con.execute("insert into entries (scope, at, task, adapter, model, state, est_in, est_out, outcome, pid, note) "
                            "values (?, ?, ?, ?, ?, 'refused', ?, ?, ?, ?, ?)",
                            (self.scope, time.time(), task, adapter, model, est_in, est_out, why[0], os.getpid(), why[1]))
                con.execute("commit")
                raise LedgerRefused(*why)
            cur = con.execute("insert into entries (scope, at, task, adapter, model, state, est_in, est_out, pid) "
                              "values (?, ?, ?, ?, ?, 'reserved', ?, ?, ?)",
                              (self.scope, time.time(), task, adapter, model, est_in, est_out, os.getpid()))
            con.execute("commit")
            return int(cur.lastrowid)

    def settle(self, entry: int, *, input_tokens: int | None, output_tokens: int | None, cached_input_tokens: int | None = None,
               turns: int | None = None, latency_ms: int | None = None, outcome: str = "ok", model: str = "") -> dict:
        """Record what the request actually used; an unknown usage is charged at the reservation. Detects overshoot
        (per-request actual over a per-request cap, or an aggregate cap passed) and opens the breaker."""
        L = self.limits
        with self._lock, self._connect() as con:
            con.execute("begin immediate")
            est_in, est_out = con.execute("select est_in, est_out from entries where id = ?", (entry,)).fetchone()
            unknown = input_tokens is None and output_tokens is None
            act_in = est_in if input_tokens is None else int(input_tokens)
            act_out = est_out if output_tokens is None else int(output_tokens)
            con.execute("update entries set state = 'settled', act_in = ?, act_out = ?, cached_in = ?, turns = ?, latency_ms = ?, "
                        "outcome = ?, usage_unknown = ?, model = coalesce(nullif(?, ''), model) where id = ?",
                        (act_in, act_out, cached_input_tokens, turns, latency_ms, outcome, int(unknown), model, entry))
            t = self._totals(con)
            breach = []
            if L.per_request_input is not None and act_in > L.per_request_input:
                breach.append(f"request {entry} used {act_in} input tokens > per-request {L.per_request_input}")
            if L.per_request_output is not None and act_out > L.per_request_output:
                breach.append(f"request {entry} used {act_out} output tokens > per-request {L.per_request_output}")
            if L.input_tokens is not None and t["input_tokens"] > L.input_tokens:
                breach.append(f"input tokens {t['input_tokens']} > cap {L.input_tokens}")
            if L.output_tokens is not None and t["output_tokens"] > L.output_tokens:
                breach.append(f"output tokens {t['output_tokens']} > cap {L.output_tokens}")
            if breach and not t["breaker"]:
                con.execute("update scopes set breaker = ? where scope = ?", ("; ".join(breach), self.scope))
            con.execute("commit")
            return {"input": act_in, "output": act_out, "estimate": (est_in, est_out), "under_estimated": act_in > est_in or act_out > est_out,
                    "usage_unknown": unknown, "breach": breach}

    def note_cache_hit(self, task: str) -> None:
        with self._lock, self._connect() as con:
            con.execute("insert into entries (scope, at, task, state, pid) values (?, ?, ?, 'cache_hit', ?)", (self.scope, time.time(), task, os.getpid()))

    def entries(self) -> list[dict]:
        with self._connect() as con:
            con.row_factory = sqlite3.Row
            return [dict(r) for r in con.execute("select * from entries where scope = ? order by id", (self.scope,))]


class LedgerProvider:
    """Any provider behind the ledger: estimate, reserve (or refuse without calling), call, settle. A refusal is an
    `AiResponse` with `error="budget"` and the limit in `error_detail`, so the caller records a budget stop -- never
    a negative reading. `adapter`: the wrapped provider's name, which picks the estimator."""

    def __init__(self, provider, ledger: Ledger) -> None:
        self.inner = provider
        self.ledger = ledger
        self.name = getattr(provider, "name", "provider")

    @property
    def ready(self):
        return getattr(self.inner, "ready", False)

    @property
    def status(self):
        return getattr(self.inner, "status", "")

    def complete(self, request):
        from app.ai.provider import AiResponse

        est_in, est_out = estimate(request, self.name)
        try:
            entry = self.ledger.reserve(request.task, est_in, est_out, adapter=self.name)
        except LedgerRefused as exc:
            return AiResponse(data=None, error="budget", error_detail=f"ledger refused ({exc.limit}): {exc.detail}", model="")
        try:
            response = self.inner.complete(request)
        except Exception as exc:  # noqa: BLE001 -- a provider that raised used an unknown amount: charged at the estimate
            self.ledger.settle(entry, input_tokens=None, output_tokens=None, outcome=f"exception: {type(exc).__name__}")
            raise
        usage = response.usage
        self.ledger.settle(entry, input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                           cached_input_tokens=usage.cached_input_tokens, turns=getattr(usage, "turns", None),
                           latency_ms=response.latency_ms, outcome=response.error or "ok", model=response.model)
        return response
