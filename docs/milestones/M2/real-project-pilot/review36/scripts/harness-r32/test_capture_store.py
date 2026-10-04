"""R31-04 capture-store contract, at the provider layer (no database, no model). Run from C:/t/iso/cand-r29/backend with
PYTHONPATH including this folder: python -m pytest -q <this file> -p no:cacheprovider"""
import json

import pytest

from app.ai.provider import AiRequest, AiResponse, ImagePart, TextPart, Usage

import capture_store as CS


class Counting:
    """A scripted inner provider that counts every dispatch and answers by task."""

    def __init__(self, answers=None, fail=None):
        self.calls, self.answers, self.fail = [], answers or {}, fail or set()

    def complete(self, request):
        self.calls.append(request.task)
        if request.task in self.fail:
            return AiResponse(data=None, error="timeout", model="scripted")
        return AiResponse(data=self.answers.get(request.task, {"value": request.task}), usage=Usage(100, 10), model="scripted-model", latency_ms=1)


def req(task="read_identity", png=b"crop-1", text="read the number", tier="small"):
    return AiRequest(task=task, system="s", parts=[TextPart("task", text), ImagePart("crop", png)], schema={"type": "object"}, max_output_tokens=10, tier=tier)


def provider(store, lane, inner, policy="P1", reference_from=None):
    return CS.StoreProvider(store, lane, inner, lambda: policy, lambda tier: f"alias-{tier}", reference_from=reference_from)


@pytest.fixture
def store(tmp_path):
    return CS.CaptureStore(tmp_path / "capture.sqlite")


def ctx(doc="d" * 64, page=1, profile="default", variant="EV1"):
    CS.set_context(sha256=doc, page=page, profile=profile, variant=variant)


def test_one_dispatch_per_identical_bound_fingerprint(store):
    inner = Counting()
    c = provider(store, "C", inner)
    ctx()
    a = c.complete(req())
    b = c.complete(req())
    assert inner.calls == ["read_identity"] and a.data == b.data
    assert len(store.rows()) == 1 and store.rows()[0]["state"] == "answered"


@pytest.mark.parametrize("change", ["doc", "page", "crop", "prompt", "tier", "profile", "variant", "policy"])
def test_any_context_difference_is_a_new_fingerprint(store, change):
    inner = Counting()
    ctx()
    provider(store, "C", inner).complete(req())
    kw = {"doc": "e" * 64} if change == "doc" else {"page": 2} if change == "page" else {"profile": "strict"} if change == "profile" else {"variant": "EV2"} if change == "variant" else {}
    ctx(**kw)
    r = req(png=b"crop-2") if change == "crop" else req(text="another prompt") if change == "prompt" else req(tier="standard") if change == "tier" else req()
    provider(store, "C", inner, policy="P2" if change == "policy" else "P1").complete(r)
    assert len(inner.calls) == 2, f"a different {change} is never served from another request"


def test_lanes_never_share_b_and_c(store):
    inner = Counting()
    ctx()
    provider(store, "B", inner).complete(req())
    provider(store, "C", inner).complete(req())
    assert len(inner.calls) == 2 and {r["lane"] for r in store.rows()} == {"B", "C"}


def test_the_reference_lane_reads_c_by_content_and_its_own_requests_never_reach_c(store):
    inner = Counting()
    ctx()
    provider(store, "C", inner, policy="CPOL").complete(req())
    r = provider(store, "R", inner, policy="RPOL", reference_from="C")
    served = r.complete(req())
    assert inner.calls == ["read_identity"] and served.data == {"value": "read_identity"}, "R reuses C's identical request despite its other policy"
    r.complete(req(task="read_field_context", png=b"other"))
    assert inner.calls == ["read_identity", "read_field_context"], "an R-only request is dispatched once, in lane R"
    c_again = provider(store, "C", inner, policy="CPOL")
    c_again.complete(req(task="read_field_context", png=b"other"))
    assert inner.calls[-1] == "read_field_context" and len(inner.calls) == 3, "C never takes R's reference-only answer"
    assert {(s["lane"], s["mode"]) for s in store.rows("select * from serves")} == {("R", "reference_from_capture")}


def test_the_probe_lane_is_never_served_to_b_or_c(store):
    inner = Counting()
    ctx()
    provider(store, "P", inner).complete(req())
    provider(store, "C", inner).complete(req())
    provider(store, "B", inner).complete(req())
    assert len(inner.calls) == 3


def test_an_interrupted_dispatch_is_charged_and_never_sent_again(store):
    ctx()
    ckey = CS.content_key(CS.get_context(), req(), "alias-small")
    row, created = store.reserve("C", "P1", ckey, CS.get_context(), "read_identity")      # dispatched, process died before settling
    assert created
    inner = Counting()
    got = provider(store, "C", inner).complete(req())
    assert inner.calls == [] and got.error == "interrupted_charged"
    assert store.rows()[0]["state"] == "reserved", "the charged request stays visible"


def test_a_failed_request_is_not_redispatched_and_is_served_as_its_failure(store):
    inner = Counting(fail={"read_identity"})
    ctx()
    c = provider(store, "C", inner)
    assert c.complete(req()).error == "timeout"
    assert c.complete(req()).error == "timeout" and inner.calls == ["read_identity"]


def test_served_answers_keep_their_original_provenance(store):
    inner = Counting()
    ctx()
    provider(store, "C", inner, policy="CPOL").complete(req())
    provider(store, "R", inner, policy="RPOL", reference_from="C").complete(req())
    s = store.rows("select * from serves")[0]
    orig = store.rows()[0]
    assert (s["served_seq"], s["served_lane"], s["served_policy"]) == (orig["seq"], "C", "CPOL") and s["policy"] == "RPOL"
    u = json.loads(orig["usage"])
    assert (u["input"], u["output"]) == (100, 10) and orig["model"] == "scripted-model"


@pytest.mark.parametrize("field,value", [("system", "another system prompt"), ("effort", "high"), ("model", "override"), ("max_output_tokens", 99)])
def test_request_settings_are_part_of_the_fingerprint(store, field, value):
    inner = Counting()
    ctx()
    c = provider(store, "C", inner)
    c.complete(req())
    r = req()
    setattr(r, field, value)
    c.complete(r)
    assert len(inner.calls) == 2


def test_the_probe_resends_a_seeded_sample_in_its_own_lane_and_never_touches_c(store):
    inner = Counting()
    c = provider(store, "C", inner)
    for page in range(1, 21):
        ctx(page=page)
        c.complete(req(png=b"crop-%d" % page))
    before = [dict(r) for r in store.rows("select * from requests where lane = 'C'")]
    probe_inner = Counting(answers={"read_identity": {"value": "different"}})
    got = CS.probe(store, probe_inner, "P1", lambda tier: f"alias-{tier}", rate=0.15, seed="s")
    again = CS.probe(store, probe_inner, "P1", lambda tier: f"alias-{tier}", rate=0.15, seed="s")
    assert got["sampled"] == 3 and len(probe_inner.calls) == 3, "each sampled payload is re-sent once; a repeat probe is served"
    assert again["dispatched"] == 0
    assert all(r["agrees"] is False for r in got["rows"]), "the probe reports disagreement"
    assert [dict(r) for r in store.rows("select * from requests where lane = 'C'")] == before
    assert {r["lane"] for r in store.rows()} == {"C", "P"}
    pages = sorted(json.loads(store.payload(r["content_key"]))["ctx"]["page"] for r in store.rows("select * from requests where lane = 'P'"))
    assert len(pages) == 3


def test_the_reference_is_served_a_failure_of_c_and_never_resends_it(store):
    inner = Counting(fail={"read_identity"})
    ctx()
    provider(store, "C", inner, policy="CPOL").complete(req())
    got = provider(store, "R", inner, policy="RPOL", reference_from="C").complete(req())
    assert got.error == "timeout" and inner.calls == ["read_identity"]
    assert [r["lane"] for r in store.rows()] == ["C"]
