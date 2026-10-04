"""Unit tests of provider_journal.py (the journal module the v4.2 runner writes and recovers from): classification,
streak semantics and fail-closed validation, on journals written through the module's own writer."""
import json

import pytest

import provider_journal as pj

B = {"declaration_sha256": "d" * 64, "arm": "L1", "tag": "L1", "a_tag": "A", "allowance_scope": "s", "allowance_profile": "p", "policy": "pol"}
DOCS = {"a" * 64, "b" * 64}


def write(tmp_path, seq_of_events, *, pids=None):
    """events: 'F' failure, 'S' ok, 'C' cache hit, 'B' budget, 'U' unresolved (attempt only), '|' next process."""
    j = pj.Journal(tmp_path / "J.jsonl", B)
    j.create(lifecycle="t", pid=1)
    pid = 1
    for ev in seq_of_events:
        if ev == "|":
            pid += 1
            continue
        s = j.attempt(pid=pid, sha256="a" * 64, task="discover_page", page=1, tier="small")
        entry = {"F": {"outcome": "transport", "cache_hit": False}, "S": {"outcome": "ok", "cache_hit": False}, "C": {"outcome": "ok", "cache_hit": True},
                 "B": {"outcome": "budget: calls_per_document", "cache_hit": False}}.get(ev)
        if ev != "U":
            j.result(s, pid=pid, entry=entry)
    return j.path


@pytest.mark.parametrize("events, streak", [
    ("FFF", 3), ("FFSFF", 2), ("FCFCF", 3), ("FBFBF", 3), ("FFU|F", 3), ("FF|F", 3), ("FFS", 0), ("F", 1), ("", 0), ("CCC", 0), ("BBB", 0), ("FFU", 2),
], ids=["three", "ok-resets", "cache-hits-neutral", "budget-neutral", "unresolved-neutral-across-restart", "restart-no-reset", "ok-last", "single", "empty", "cache-only", "budget-only", "unresolved-tail"])
def test_streak_semantics(tmp_path, events, streak):
    info = pj.load(write(tmp_path, events), B, planned_sha256=DOCS)
    assert info["state"] == "ok" and info["streak"] == streak
    assert len(info["trailing_failures"]) == streak


def test_classify():
    assert pj.classify(None) == "none" and pj.classify({"cache_hit": True, "outcome": "ok"}) == "cache_hit"
    assert pj.classify({"outcome": "budget: x"}) == "budget" and pj.classify({"outcome": "ok"}) == "ok" and pj.classify({"outcome": "timeout"}) == "failure"


def lines(p):
    return p.read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("damage, why", [
    (lambda p: p.write_bytes(p.read_bytes()[:-7]), "torn"),
    (lambda p: p.write_text("\n".join(lines(p)[:2] + ["{not json"] + lines(p)[2:]) + "\n", encoding="utf-8"), "unparsable"),
    (lambda p: p.write_text("\n".join(lines(p)[1:]) + "\n", encoding="utf-8"), "header"),
    (lambda p: p.write_text("\n".join([json.dumps({**json.loads(lines(p)[0]), "binding": {**B, "tag": "x"}})] + lines(p)[1:]) + "\n", encoding="utf-8"), "another run"),
    (lambda p: p.write_text("\n".join([l for i, l in enumerate(lines(p)) if i != 1]) + "\n", encoding="utf-8"), "without its open attempt"),
    (lambda p: p.write_text("\n".join(lines(p) + [lines(p)[1]]) + "\n", encoding="utf-8"), "seq not increasing"),
    (lambda p: p.write_text("\n".join(lines(p)[:1] + [json.dumps({**json.loads(lines(p)[1]), "b": "zz"})] + lines(p)[2:]) + "\n", encoding="utf-8"), "binding digest"),
    (lambda p: p.write_text("\n".join(lines(p)[:1] + [json.dumps({**json.loads(lines(p)[1]), "sha256": "c" * 64})] + lines(p)[2:]) + "\n", encoding="utf-8"), "outside the declared sources"),
], ids=["torn", "unparsable", "no-header", "other-run", "orphan-result", "seq-reuse", "other-digest", "foreign-document"])
def test_validation_fails_closed(tmp_path, damage, why):
    p = write(tmp_path, "FFF")
    damage(p)
    info = pj.load(p, B, planned_sha256=DOCS)
    assert info["state"] == "indeterminate" and why in info["why"]


def test_interleaved_writers_are_indeterminate(tmp_path):
    p = write(tmp_path, "F|F")
    ls = lines(p)
    extra = json.loads(ls[1])
    extra.update(seq=99)
    res = json.loads(ls[2])
    res.update(seq=99)
    p.write_text("\n".join(ls + [json.dumps(extra), json.dumps(res)]) + "\n", encoding="utf-8")   # pid 1 again after pid 2
    info = pj.load(p, B, planned_sha256=DOCS)
    assert info["state"] == "indeterminate" and "not contiguous" in info["why"]


def test_absent_journal(tmp_path):
    assert pj.load(tmp_path / "none.jsonl", B, planned_sha256=DOCS) == {"state": "absent"}
