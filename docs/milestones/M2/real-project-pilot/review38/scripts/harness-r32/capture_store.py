"""Review 31 (R31-04): the shared-response capture store and its provider layer.

Keys
  content_key = sha256(doc sha256, page, task, tier, profile, variant, model alias, prompt text, image sha256s, schema sha256)
  bound_key   = sha256(lane, policy, content_key)
Lanes: B (accepted baseline), C (combined candidate), R (reference-only live requests), P (variation probe).

Contract (tested in test_capture_store.py):
  1. one provider dispatch per identical bound fingerprint: a row is RESERVED (unique bound_key, BEGIN IMMEDIATE) before the
     dispatch and settled after it; a second request with the same bound key is served from the row, never dispatched again;
  2. lanes never share: B is served only from lane B, C only from lane C; the probe lane is never served to anyone;
  3. the declared exception -- the offline reference contrast (lane R) may be served C's capture by CONTENT key (the same
     source bytes, page, crop, prompt, tier, profile, variant and model alias; only the policy differs, by design),
     whatever its outcome: an answer, a failure, or an interrupted (charged) dispatch is served to R exactly as C saw it,
     so R never re-sends a request C already sent. A request R makes that C never made is dispatched once in lane R
     (reference-only) and is never served to C or B;
  4. an interrupted dispatch (a reserved row with no answer, e.g. the process died after sending) is charged and NEVER
     dispatched again: it is served as a failure 'interrupted_charged';
  5. every served answer carries its ORIGINAL provenance (lane, policy, dispatch seq, time, model, usage) in the serve log;
  6. the variation probe (lane P) re-sends a seeded sample of C's dispatched payloads once each and writes only lane-P rows.
No model is called by this module; `inner` is whatever provider the caller supplies (a scripted / replay provider in tests
and in the dry run)."""
from __future__ import annotations

import base64
import datetime
import hashlib
import random
import json
import sqlite3
import threading

from app.ai.provider import AiResponse, TextPart, Usage

LANES = ("B", "C", "R", "P")
_ctx = threading.local()


def set_context(**kw):
    _ctx.value = dict(kw)


def get_context() -> dict:
    return dict(getattr(_ctx, "value", {}) or {})


def _h(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()


def content_key(ctx: dict, request, model_alias: str) -> str:
    parts = [[p.label, p.text if isinstance(p, TextPart) else hashlib.sha256(p.png).hexdigest()] for p in request.parts]
    return _h({"doc": ctx.get("sha256"), "page": ctx.get("page"), "task": request.task, "tier": request.tier or "small",
               "profile": ctx.get("profile"), "variant": ctx.get("variant"), "model": model_alias, "model_override": request.model,
               "effort": request.effort, "max_output": request.max_output_tokens, "system": _h(request.system), "parts": parts,
               "schema": _h(request.schema)})


def payload_of(ctx: dict, request) -> str:
    """The exact request (parts with image bytes) and its context, for the variation probe's re-send."""
    return json.dumps({"ctx": ctx, "task": request.task, "system": request.system, "schema": request.schema,
                       "max_output_tokens": request.max_output_tokens, "tier": request.tier, "effort": request.effort, "model": request.model,
                       "parts": [{"label": p.label, "text": p.text} if isinstance(p, TextPart) else {"label": p.label, "png": base64.b64encode(p.png).decode()}
                                 for p in request.parts]}, sort_keys=True)


def request_of(payload: str):
    from app.ai.provider import AiRequest, ImagePart
    x = json.loads(payload)
    parts = [TextPart(p["label"], p["text"]) if "text" in p else ImagePart(p["label"], base64.b64decode(p["png"])) for p in x["parts"]]
    return x["ctx"], AiRequest(task=x["task"], system=x["system"], parts=parts, schema=x["schema"], max_output_tokens=x["max_output_tokens"],
                               tier=x["tier"], effort=x["effort"], model=x["model"])


def bound_key(lane: str, policy: str, ckey: str) -> str:
    return _h({"lane": lane, "policy": policy, "content": ckey})


class CaptureStore:
    def __init__(self, path):
        self.path = str(path)
        con = self._con()
        con.executescript("""
            create table if not exists requests (seq integer primary key autoincrement, bound_key text unique, content_key text, lane text,
              policy text, task text, page integer, doc text, state text, answer text, outcome text, usage text, model text,
              dispatched_at text, settled_at text);
            create table if not exists payloads (content_key text primary key, payload text);
            create table if not exists serves (id integer primary key autoincrement, lane text, policy text, bound_key text, served_seq integer,
              served_lane text, served_policy text, mode text, at text);""")
        con.close()

    def _con(self):
        con = sqlite3.connect(self.path, timeout=60, isolation_level=None)
        con.row_factory = sqlite3.Row
        return con

    def keep_payload(self, ckey, payload):
        con = self._con()
        con.execute("insert or ignore into payloads (content_key, payload) values (?, ?)", (ckey, payload))
        con.close()

    def payload(self, ckey):
        con = self._con()
        row = con.execute("select payload from payloads where content_key = ?", (ckey,)).fetchone()
        con.close()
        return row and row["payload"]

    def reserve(self, lane, policy, ckey, ctx, task):
        """(row, created): the existing row for this bound key, or a new RESERVED row (created=True) -- atomically."""
        bkey = bound_key(lane, policy, ckey)
        con = self._con()
        try:
            con.execute("begin immediate")
            row = con.execute("select * from requests where bound_key = ?", (bkey,)).fetchone()
            if row is None:
                con.execute("insert into requests (bound_key, content_key, lane, policy, task, page, doc, state, dispatched_at) values (?,?,?,?,?,?,?,?,?)",
                            (bkey, ckey, lane, policy, task, ctx.get("page"), ctx.get("sha256"), "reserved", _now()))
                row = con.execute("select * from requests where bound_key = ?", (bkey,)).fetchone()
                con.execute("commit")
                return dict(row), True
            con.execute("commit")
            return dict(row), False
        finally:
            con.close()

    def settle(self, seq, response: AiResponse):
        con = self._con()
        con.execute("update requests set state = ?, answer = ?, outcome = ?, usage = ?, model = ?, settled_at = ? where seq = ?",
                    ("answered" if response.ok else "failed", json.dumps(response.data) if response.ok else None, response.error or "ok",
                     json.dumps({"input": response.usage.input_tokens, "output": response.usage.output_tokens, "cached": response.usage.cached_input_tokens}),
                     response.model, _now(), seq))
        con.close()

    def by_content(self, lane, ckey):
        con = self._con()
        row = con.execute("select * from requests where lane = ? and content_key = ? order by seq limit 1", (lane, ckey)).fetchone()
        con.close()
        return dict(row) if row else None

    def log_serve(self, lane, policy, bkey, row, mode):
        con = self._con()
        con.execute("insert into serves (lane, policy, bound_key, served_seq, served_lane, served_policy, mode, at) values (?,?,?,?,?,?,?,?)",
                    (lane, policy, bkey, row["seq"], row["lane"], row["policy"], mode, _now()))
        con.close()

    def rows(self, sql="select * from requests order by seq", args=()):
        con = self._con()
        out = [dict(r) for r in con.execute(sql, args)]
        con.close()
        return out


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _served(row, mode):
    if row["state"] == "answered":
        return AiResponse(data=json.loads(row["answer"]), usage=Usage(0, 0), model=row["model"] or "", latency_ms=0)
    if row["state"] == "reserved":
        return AiResponse(data=None, model="capture", error="interrupted_charged",
                          error_detail=f"seq {row['seq']} was dispatched and never settled: charged, never dispatched again")
    return AiResponse(data=None, model=row["model"] or "", error=row["outcome"] or "failed", error_detail=f"seq {row['seq']} ({mode})")


class StoreProvider:
    """Provider layer: lane-scoped capture / replay over an inner provider. `policy` is read at call time."""
    name = "capture"
    ready = True
    status = "lane-scoped capture store"

    def __init__(self, store: CaptureStore, lane: str, inner, policy_fn, model_alias_fn, *, reference_from: str | None = None):
        assert lane in LANES
        self.store, self.lane, self.inner, self.policy_fn, self.model_alias_fn, self.reference_from = store, lane, inner, policy_fn, model_alias_fn, reference_from
        self.dispatched = 0

    def complete(self, request):
        ctx, policy = get_context(), self.policy_fn()
        ckey = content_key(ctx, request, self.model_alias_fn(request.tier))
        if self.reference_from:                                       # lane R: the declared content-key exception
            row = self.store.by_content(self.reference_from, ckey)
            if row is not None:
                self.store.log_serve(self.lane, policy, bound_key(self.lane, policy, ckey), row, "reference_from_capture")
                return _served(row, "reference_from_capture")
        row, created = self.store.reserve(self.lane, policy, ckey, ctx, request.task)
        if not created:
            self.store.log_serve(self.lane, policy, row["bound_key"], row, "same_bound_fingerprint")
            return _served(row, "same_bound_fingerprint")
        self.store.keep_payload(ckey, payload_of(ctx, request))
        self.dispatched += 1
        response = self.inner.complete(request)
        self.store.settle(row["seq"], response)
        return response


def install_context(er):
    """Wrap EvidenceRun.call so the provider layer knows the source document and page of every request."""
    original = er.EvidenceRun.call
    if getattr(original, "_r31_context", False):
        return original

    def call(self, **kw):
        set_context(sha256=kw.get("sha256"), page=kw.get("page"), profile=self.profile, variant=self.variant)
        return original(self, **kw)

    call._r31_context = True
    call._original = original
    er.EvidenceRun.call = call
    return original


def probe(store: CaptureStore, inner, policy: str, model_alias_fn, *, rate=0.15, seed="m2-r30-variation-2026-10-02", lane_from="C"):
    """The variation probe: a seeded sample of lane C's ANSWERED dispatches is re-sent once, in lane P (its own bound keys, so
    it is a dispatch, never a serve). The probe reads C's rows and payloads and writes only lane-P rows: C's rows, answers and
    scores are untouched. Returns per-row agreement (exact answer equality) -- reported only, never a score."""
    rows = [r for r in store.rows("select * from requests where lane = ? and state = 'answered' order by seq", (lane_from,))]
    k = round(rate * len(rows))
    sample = sorted(random.Random(seed).sample(rows, k), key=lambda r: r["seq"]) if k else []
    p = StoreProvider(store, "P", inner, lambda: policy, model_alias_fn)
    out = []
    for r in sample:
        payload = store.payload(r["content_key"])
        if payload is None:
            out.append({"seq": r["seq"], "task": r["task"], "probe": "no payload"})
            continue
        ctx, request = request_of(payload)
        set_context(**ctx)
        resp = p.complete(request)
        out.append({"seq": r["seq"], "task": r["task"], "probe": "answered" if resp.ok else resp.error,
                    "agrees": resp.ok and json.dumps(resp.data, sort_keys=True) == json.dumps(json.loads(r["answer"]), sort_keys=True)})
    return {"sampled": k, "of": len(rows), "seed": seed, "rate": rate, "dispatched": p.dispatched, "rows": out}
