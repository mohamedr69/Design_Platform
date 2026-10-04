"""The shared AI budget ledger (M2 review 07, R7-04), with scripted providers only -- no model is called."""
import subprocess
import sys
import textwrap
import threading

import pymupdf
import pytest

from app.ai import ledger as L
from app.ai.provider import AiRequest, AiResponse, ImagePart, RecordingProvider, TextPart, Usage


class Scripted:
    """A provider whose responses (usage included) are scripted; counts what reached it."""
    name = "claude-code"
    ready = True
    status = "scripted"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def ok(inp, out, **kw):
    return AiResponse(data={"value": "x"}, usage=Usage(input_tokens=inp, output_tokens=out, **kw), model="m", latency_ms=5)


def req(task="read_identity", text="read this", png=None, max_output=400):
    parts = [TextPart("task", text)] + ([ImagePart("crop", png)] if png else [])
    return AiRequest(task=task, system="sys", parts=parts, schema={"type": "object"}, max_output_tokens=max_output)


def ledger(tmp_path, scope="run", **limits):
    return L.Ledger(str(tmp_path / "ledger.sqlite"), scope, L.Limits(**limits))


def test_an_underestimated_request_opens_the_breaker_and_stops_further_dispatch(tmp_path):
    led = ledger(tmp_path, per_request_input=50_000)
    inner = Scripted([ok(64_816, 900), ok(10, 10)])
    p = L.LedgerProvider(inner, led)
    first = p.complete(req("discover_page"))
    assert first.ok and inner.calls == 1, "a request already made cannot be made smaller: it is recorded"
    t = led.totals()
    assert t["input_tokens"] == 64_816 and "per-request" in t["breaker"]
    second = p.complete(req())
    assert second.error == "budget" and "breaker" in second.error_detail and inner.calls == 1, "not dispatched"


def test_excessive_output_is_refused_when_estimated_and_detected_when_not(tmp_path):
    led = ledger(tmp_path, per_request_output=2_000)
    inner = Scripted([ok(5_000, 18_024)])
    p = L.LedgerProvider(inner, led)
    # discovery's calibrated output estimate (10,870) is already over the cap: refused before any request
    refused = p.complete(req("discover_page", max_output=800))
    assert refused.error == "budget" and "per_request_output" in refused.error_detail and inner.calls == 0
    # a revision read is estimated small; its actual 18,024 output tokens are caught after the fact
    assert p.complete(req("read_revision", max_output=400)).ok and inner.calls == 1
    assert "output tokens" in led.totals()["breaker"]


def test_a_timeout_with_unknown_usage_is_charged_at_its_reservation(tmp_path):
    led = ledger(tmp_path)
    p = L.LedgerProvider(Scripted([AiResponse(data=None, error="timeout", model="m")]), led)
    r = p.complete(req())
    est_in, est_out = L.estimate(req(), "claude-code")
    e = led.entries()[-1]
    assert r.error == "timeout" and e["usage_unknown"] == 1 and (e["act_in"], e["act_out"]) == (est_in, est_out)


def test_provider_errors_exceptions_and_caller_retries_are_all_accounted(tmp_path):
    led = ledger(tmp_path)
    inner = Scripted([AiResponse(data=None, error="rate_limit", usage=Usage(input_tokens=300, output_tokens=0), model="m"),
                      RuntimeError("boom"), ok(100, 10)])
    p = L.LedgerProvider(inner, led)
    assert p.complete(req()).error == "rate_limit"
    with pytest.raises(RuntimeError):
        p.complete(req())
    assert p.complete(req()).ok
    entries = led.entries()
    assert [e["outcome"] for e in entries] == ["rate_limit", "exception: RuntimeError", "ok"]
    assert led.totals()["requests"] == 3 and entries[1]["usage_unknown"] == 1


def test_the_request_cap_holds_under_concurrency(tmp_path):
    led = ledger(tmp_path, requests=5)
    results = []

    def one():
        try:
            led.reserve("read_identity", 100, 10)
            results.append("ok")
        except L.LedgerRefused:
            results.append("refused")

    threads = [threading.Thread(target=one) for _ in range(16)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert results.count("ok") == 5 and results.count("refused") == 11


def test_the_ledger_survives_a_restart_and_another_process_shares_it(tmp_path):
    path = str(tmp_path / "ledger.sqlite")
    first = L.Ledger(path, "shared", L.Limits(requests=3))
    first.settle(first.reserve("read_identity", 100, 10), input_tokens=120, output_tokens=11)
    code = textwrap.dedent(f"""
        import sys; sys.path.insert(0, {str(__import__('pathlib').Path(L.__file__).parents[2])!r})
        from app.ai import ledger as L
        led = L.Ledger({path!r}, "shared")
        led.settle(led.reserve("read_identity", 100, 10), input_tokens=130, output_tokens=12)
    """)
    subprocess.run([sys.executable, "-c", code], check=True)
    again = L.Ledger(path, "shared")                     # a restart: limits and totals come from the file
    assert again.limits.requests == 3 and again.totals()["requests"] == 2 and again.totals()["input_tokens"] == 250
    again.reserve("read_identity", 1, 1)
    with pytest.raises(L.LedgerRefused):
        again.reserve("read_identity", 1, 1)


def test_one_cap_across_tracks_and_documents(tmp_path):
    led = ledger(tmp_path, input_tokens=30_000)
    documents = L.LedgerProvider(Scripted([ok(12_000, 100)] * 5), led)
    boq = L.LedgerProvider(Scripted([ok(12_000, 100)] * 5), led)
    assert documents.complete(req()).ok and boq.complete(req("read_boq_row")).ok
    refused = documents.complete(req())
    assert refused.error == "budget" and "input_tokens" in refused.error_detail


def test_the_estimate_counts_images_turns_and_the_calibrated_p95():
    doc = pymupdf.open()
    page = doc.new_page(width=1684, height=1190)
    png = page.get_pixmap(matrix=pymupdf.Matrix(1600 / 1684, 1600 / 1684)).tobytes("png")
    est_in, est_out = L.estimate(req("discover_page", png=png, max_output=800), "claude-code")
    assert est_in >= 45_544 and est_out >= 10_870, "the claude-code discovery estimate is not the old constant 4,000"
    small_in, _ = L.estimate(req("read_identity", png=png[:0] or None), "claude")
    assert small_in < 200, "the API adapter has no CLI wrapper overhead"
    assert L.image_tokens(png) > 1_000


def test_an_evidence_run_stops_on_a_ledger_refusal_and_records_it(db_session, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app.ai import evidence_reader as er
    from app.ai import submittal_reader

    monkeypatch.setattr(submittal_reader, "available", lambda project, provider=None: None)
    doc = pymupdf.open()
    for text in ("Drawing No X-SD-1", "Drawing No X-SD-2"):
        pg = doc.new_page(width=1684, height=1190)
        pg.insert_text((1300, 1100), text, fontsize=9)
    path = tmp_path / "two.pdf"
    doc.save(path)
    region = [760, 900, 900, 950]
    disc = lambda v: {"page_kind": "drawing_sheet", "own_identity": v, "own_identity_label": "", "own_identity_region": region,
                      "own_revision": "", "own_revision_label": "", "own_revision_region": [], "decision_options_printed": [],
                      "decision_marked_option": "", "decision_mark_type": "none", "decision_actor": "unknown", "decision_region": [],
                      "other_numbers": [], "notes": ""}
    inner = RecordingProvider([disc("X-SD-1"), {"label_text": "", "value": "X-SD-1", "legible": True, "other_values_in_crop": []}])
    inner.name = "claude-code"
    led = ledger(tmp_path, requests=2)
    row = SimpleNamespace(sha256="5" * 64, extracted={"records": [], "observations": []}, reference=None, status="UR")
    counts = er.evidence_stage(db_session, SimpleNamespace(id=None), [(row, path)], provider=L.LedgerProvider(inner, led),
                               variant="EV1", profile="default")
    assert inner.calls == 2 and counts["budget_stopped"] == 1 and led.totals()["refused"] == 1
    attempt = row.extracted["ai_evidence"]["attempts"][-1]
    assert attempt["outcome"] == "budget" and attempt["pages"]["2"].startswith("budget")
    assert sorted(er.current_evidence(row.extracted["ai_evidence"])["pages"]) == ["1"]
    # the result cache: the same question again is no request, recorded as a cache hit
    again = er.evidence_stage(db_session, SimpleNamespace(id=None), [(row, path)], provider=L.LedgerProvider(RecordingProvider(), led),
                              variant="EV1", profile="default")
    assert again["cache_hits"] >= 1 and led.totals()["cache_hits"] >= 1
