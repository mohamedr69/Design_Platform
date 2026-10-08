"""R31-04: C-from-B state contract. Run: python -m pytest -q test_state_check.py (cwd harness)."""
import json
import sqlite3

import pytest

from state_check import check_c_start, file_sha256

MARK = ["identity-role-guard-2026-10-02.2"]
TASKS = ["discover_page", "read_identity"]


def make(path, extracted=None, cache_task="ifc_classify"):
    con = sqlite3.connect(path)
    con.execute("create table project_documents (id integer primary key, extracted text)")
    con.execute("create table result_cache (key text primary key, task text)")
    con.execute("insert into project_documents (extracted) values (?)", (json.dumps(extracted or {"reference": "X"}),))
    con.execute("insert into result_cache values ('k1', ?)", (cache_task,))
    con.commit()
    con.close()


def copy(src, dst):
    s, d = sqlite3.connect(src), sqlite3.connect(dst)
    s.backup(d)
    s.close()
    d.close()


@pytest.fixture
def b(tmp_path):
    p = tmp_path / "b.db"
    make(p)
    return p, file_sha256(p)


def test_a_faithful_copy_passes(b, tmp_path):
    p, sha = b
    copy(p, tmp_path / "c.db")
    r = check_c_start(p, sha, tmp_path / "c.db", MARK, TASKS)
    assert r["ok"], r


def test_a_changed_b_is_refused(b, tmp_path):
    p, sha = b
    copy(p, tmp_path / "c.db")
    con = sqlite3.connect(p)
    con.execute("insert into result_cache values ('k2', 'x')")
    con.commit()
    con.close()
    r = check_c_start(p, sha, tmp_path / "c.db", MARK, TASKS)
    assert not r["ok"] and "B database changed after it was frozen" in r["problems"]


def test_a_copy_that_differs_is_refused(b, tmp_path):
    p, sha = b
    copy(p, tmp_path / "c.db")
    con = sqlite3.connect(tmp_path / "c.db")
    con.execute("update project_documents set extracted = '{}'")
    con.commit()
    con.close()
    assert "C copy differs from B" in check_c_start(p, sha, tmp_path / "c.db", MARK, TASKS)["problems"]


def test_c_policy_evidence_and_evidence_cache_rows_are_refused(tmp_path):
    ev = {"ai_evidence": {"envelopes": {"default|EV1": {}}, "attempts": [{"policy": "evidence-policy+identity-role-guard-2026-10-02.2", "version": "r"}]}}
    p = tmp_path / "b2.db"
    make(p, extracted=ev, cache_task="read_identity")
    copy(p, tmp_path / "c2.db")
    r = check_c_start(p, file_sha256(p), tmp_path / "c2.db", MARK, TASKS)
    assert not r["ok"] and len(r["problems"]) == 2


def test_an_unattributed_envelope_is_refused(tmp_path):
    p = tmp_path / "b3.db"
    make(p, extracted={"ai_evidence": {"envelopes": {"default|EV1": {"observations": []}}}})
    copy(p, tmp_path / "c3.db")
    r = check_c_start(p, file_sha256(p), tmp_path / "c3.db", MARK, TASKS)
    assert r["checks"]["documents_with_c_policy_evidence"] == [1]
