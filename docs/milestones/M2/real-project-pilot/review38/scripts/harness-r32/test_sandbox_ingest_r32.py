"""sandbox_ingest_r32 (carried unchanged by hash from review33): registration without processing in an isolated sandbox;
refusals. ORCH-05C / ORCH-08 path-only change of this TEST: sandboxes are created only under <sandbox base>/tests/ (the
module's base is set at import to preflight_r32.sandbox_base() -- by default C:/t/r2x/r38-sandbox -- exactly as runner_r32
sets it to the run's declared base).
Run: python -m pytest -q test_sandbox_ingest_r32.py"""
import copy
import json
import pathlib
import sqlite3
import uuid

import pytest

import inputs_r32 as I
import labels_adapter_r32 as A
import preflight_r32 as PF
import sandbox_ingest_r32 as SI

SI.SANDBOX_BASE = PF.sandbox_base()
BASE = SI.SANDBOX_BASE.as_posix()
TEST_BASE = SI.SANDBOX_BASE / "tests"


@pytest.fixture(scope="module")
def truth():
    x = I.load_all()
    return A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])


def _root():
    return TEST_BASE / f"ingest-{uuid.uuid4().hex[:10]}"


def test_registration_without_processing_and_the_c_from_b_check(truth):
    r = SI.ingest(_root(), ["F001", "F032", "F045", "F043"], truth)
    assert r["ok"] and r["documents"] == 4 and r["registration"]["by_state"] == {"pending": 4}
    assert all(v == 0 for v in r["registration"]["table_counts"].values()), "nothing processed, nothing read, no AI usage"
    assert r["state_check"]["ok"] and r["model_requests"] == 0 and r["processing_run"] is False
    assert all(v["sha256"] == truth["documents"][p]["staged_sha256"] for p, v in r["staged"].items())


def test_a_sandbox_is_never_reused_and_lives_only_under_the_sandbox_base(truth):
    root = _root()
    SI.ingest(root, ["F045"], truth)
    with pytest.raises(RuntimeError, match="never reused"):
        SI.ingest(root, ["F045"], truth)
    with pytest.raises(RuntimeError, match="sandbox lives under"):
        SI.ingest("C:/t/iso/tmp/not-a-sandbox", ["F045"], truth)


def test_a_staged_hash_mismatch_refuses(truth):
    t = copy.deepcopy(truth)
    t["documents"]["F045"]["staged_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="PACKET MISMATCH"):
        SI.ingest(_root(), ["F045"], t)


def test_the_registration_check_detects_a_processed_row(truth):
    root = _root()
    r = SI.ingest(root, ["F045"], truth)
    db = root / "db" / "default.db"
    con = sqlite3.connect(str(db))
    con.execute("update project_documents set state = 'fresh', extracted = ?", (json.dumps({"records": []}),))
    con.commit()
    con.close()
    chk = SI.check_registration(db, r["staged"])
    assert not chk["ok"] and any("not a bare pending registration" in p for p in chk["problems"])


def test_the_environment_confines_every_root_and_disables_ai():
    env = SI.sandbox_env(TEST_BASE / "x")
    assert env["AI_ENABLED"] == "false" and env["AI_LEDGER_PATH"] == "" and env["DATA_ROOT"] == ""
    assert env["DATABASE_URL"].startswith(f"sqlite:///{BASE}/")
    assert all(env[k].replace("\\", "/").startswith(f"{BASE}/") for k in ("CACHE_ROOT", "LIBRARY_ROOT", "UPLOADS_ROOT"))
