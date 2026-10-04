"""R25-01 regressions: (a) unit -- every contradictory kind / outcome combination is indeterminate and every combination the
writer produces from real reader-log entries is accepted with unchanged streak semantics (a valid cache hit, budget refusal
or no-result event stays neutral: it neither resets nor extends a failure streak); (b) actual runner -- the reviewer's three
mutations refuse with exit 5, zero sends, no stop, unchanged saved state, and the unmutated control still reconstructs the
stop; (c) legacy -- every existing v4.2 journal loads identically under both validator revisions.
NEUTRAL.json / LEGACY-RECHECK.json are produced by neutral_mutation_probes.py / legacy_journal_recheck.py (R25_RUN_PROBES=1
regenerates them first)."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

import provider_journal as pj

HERE = pathlib.Path(__file__).resolve().parent
EV = HERE.parent / "neutral-evidence"
B = {"run": "unit"}
DOC = "a" * 64
F = {"outcome": "transport", "cache_hit": False, "error_detail": "x"}
LOGGED = {"ok": {"outcome": "ok", "cache_hit": False}, "cache_hit": {"outcome": "ok", "cache_hit": True}, "budget": {"outcome": "budget: calls_per_document", "cache_hit": False},
          "budget-elapsed": {"outcome": "budget: elapsed_time (under the minimum request time)", "cache_hit": False}, "failure": F, "timeout": {"outcome": "timeout", "cache_hit": False}, "none": None}


def journal(tmp_path, entries, name="J.jsonl"):
    j = pj.Journal(tmp_path / name, B)
    j.create(lifecycle="t", pid=1)
    for e in entries:
        s = j.attempt(pid=1, sha256=DOC, task="discover_page", page=1, tier="small")
        j.result(s, pid=1, entry=e)
    return j.path


def rewrite_last_kind(p, kind, outcome=...):
    ls = p.read_text(encoding="utf-8").splitlines()
    r = json.loads(ls[-1])
    r["kind"] = kind
    if outcome is not ...:
        r["outcome"] = outcome
    ls[-1] = json.dumps(r, sort_keys=True)
    p.write_text("\n".join(ls) + "\n", encoding="utf-8")


@pytest.mark.parametrize("kind, outcome", [
    ("budget", "transport"), ("cache_hit", "transport"), ("none", "transport"),            # the reviewer's three
    ("cache_hit", "budget: calls_per_document"), ("cache_hit", None), ("budget", "ok"), ("budget", None), ("none", "ok"), ("none", "budget: x"),
    ("ok", "transport"), ("ok", None), ("failure", "ok"), ("failure", None), ("failure", "budget: x"), ("budget", 7),
])
def test_contradictory_combination_is_indeterminate(tmp_path, kind, outcome):
    p = journal(tmp_path, [F, F, F])
    rewrite_last_kind(p, kind, outcome)
    info = pj.load(p, B, planned_sha256={DOC})
    assert info["state"] == "indeterminate" and "kind and outcome disagree" in info["why"]


@pytest.mark.parametrize("name", list(LOGGED))
def test_every_writer_produced_combination_is_accepted(tmp_path, name):
    p = journal(tmp_path, [LOGGED[name]])
    r = json.loads(p.read_text(encoding="utf-8").splitlines()[-1])
    assert r["kind"] == pj.classify(LOGGED[name]) and pj.outcome_agrees(r["kind"], r["outcome"])
    assert pj.load(p, B, planned_sha256={DOC})["state"] == "ok"


@pytest.mark.parametrize("neutral", ["cache_hit", "budget", "budget-elapsed", "none"])
def test_valid_neutral_neither_resets_nor_extends_the_streak(tmp_path, neutral):
    info = pj.load(journal(tmp_path, [F, LOGGED[neutral], F]), B, planned_sha256={DOC})
    assert info["state"] == "ok" and info["streak"] == 2
    info = pj.load(journal(tmp_path, [F, F, LOGGED[neutral], F], name="J2.jsonl"), B, planned_sha256={DOC})
    assert info["state"] == "ok" and info["streak"] == 3


def test_success_still_resets_and_unresolved_still_neutral(tmp_path):
    assert pj.load(journal(tmp_path, [F, F, LOGGED["ok"], F]), B, planned_sha256={DOC})["streak"] == 1
    j = pj.Journal(tmp_path / "U.jsonl", B)
    j.create(lifecycle="t", pid=1)
    for e in (F, F):
        j.result(j.attempt(pid=1, sha256=DOC, task="discover_page", page=1, tier="small"), pid=1, entry=e)
    j.attempt(pid=2, sha256=DOC, task="discover_page", page=1, tier="small")      # in flight when process 2 ended
    j.result(j.attempt(pid=3, sha256=DOC, task="discover_page", page=1, tier="small"), pid=3, entry=F)
    info = pj.load(j.path, B, planned_sha256={DOC})
    assert info["state"] == "ok" and info["streak"] == 3 and len(info["unresolved"]) == 1


@pytest.fixture(scope="module")
def N():
    if os.environ.get("R25_RUN_PROBES") == "1" or not (EV / "NEUTRAL.json").exists():
        p = subprocess.run([sys.executable, str(HERE / "neutral_mutation_probes.py")], cwd=str(HERE), capture_output=True, text=True, timeout=3000)
        assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    return json.loads((EV / "NEUTRAL.json").read_text(encoding="utf-8"))["scenarios"]


@pytest.mark.parametrize("name", ["m-budget", "m-cache_hit", "m-none"])
def test_actual_runner_mutation_refuses_before_dispatch(N, name):
    c = N[name]["checks"]
    assert all(c.values()), {k: v for k, v in c.items() if not v}


def test_actual_runner_unmutated_control_still_reconstructs(N):
    c = N["m0-unmutated-control"]["checks"]
    assert all(c.values()), {k: v for k, v in c.items() if not v}


def test_legacy_v4_2_journals_load_identically():
    if os.environ.get("R25_RUN_PROBES") == "1" or not (EV / "LEGACY-RECHECK.json").exists():
        p = subprocess.run([sys.executable, str(HERE / "legacy_journal_recheck.py")], cwd=str(HERE), capture_output=True, text=True, timeout=600)
        assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    L = json.loads((EV / "LEGACY-RECHECK.json").read_text(encoding="utf-8"))
    assert L["journals"] >= 20 and L["all_equal"] and all(L["kinds_seen"][k] > 0 for k in ("ok", "failure", "cache_hit", "budget"))
