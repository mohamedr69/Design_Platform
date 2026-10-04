"""runner_r32 / lane_r32: preflight refusals; (Review 34 RC-3) no --auth-path, live refusals before any run folder exists,
a DIRECT live lane invocation refused by the same preflight and guard; (RC-4) one run folder, allowance and capture store
per run key, the two-invocation drill (a fresh run interrupted by a crash after a send, a second fresh run refused, a
same-stamp resume that re-sends nothing, serves the reserved request as interrupted_charged and never gets fresh caps,
then no further resume); (RC-5) no silent default switches; the dry pipeline on the real reference set (reader 'none',
no prediction) and the application readers' path on SYNTHETIC documents only. Sandboxes only under
C:/t/r2x/r34-sandbox/; temporary declarations and FAKE ledgers only; no authorization file is ever written.
Run: python -m pytest -q test_runner_r32.py"""
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import uuid

import pytest

import allowance_r32 as AL
import dispatch_guard_r32 as DG
import preflight_r32 as PF
import r32_test_helpers as H
import runner_r32 as RN
import synthetic_r32 as SY


def _stamp():
    return f"tests-run-{uuid.uuid4().hex[:10]}"


def _binding(tmp_path, files=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    f = tmp_path / "bound.txt"
    f.write_text("bound", encoding="utf-8", newline="\n")
    man = {"files": {"g": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()} | (files or {})}}
    p = tmp_path / "BINDING.json"
    p.write_text(json.dumps(man), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest(), f


_TRUTH = {}


def _truth():
    if "t" not in _TRUTH:
        _TRUTH["t"] = PF.build_truth()
    return _TRUTH["t"]


def _run_set(tmp_path, ids=("F045", "F051", "F066")):
    T = _truth()
    rs = {"documents": [{"pool_id": p, "doc_key": T["documents"][p]["doc_key"], "ep": T["documents"][p]["ep"]} for p in ids]}
    p = tmp_path / "RUN-SET.json"
    p.write_text(json.dumps(rs), encoding="utf-8", newline="\n")
    return p, T


def _dry(cmd, stamp, rs, b, sha, *extra):
    return RN.main([cmd, "--mode", "dry", "--stamp", stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, *extra])


def _live_args(cmd, decl, dsha, rs, b, sha):
    return [cmd, "--mode", "live", "--declaration", str(decl), "--declaration-sha", dsha, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha]


def _live_setup(tmp_path, **over):
    b, sha, _ = _binding(tmp_path)
    rs, T = _run_set(tmp_path)
    led = H.fake_ledger(tmp_path / "fake-ledger.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0)})
    stamp = _stamp()
    decl, dsha, rec = H.live_declaration(tmp_path / "pkg", binding_sha=sha, run_set_sha=hashlib.sha256(rs.read_bytes()).hexdigest(), stamp=stamp,
                                         ledger_path=led, **over)
    return b, sha, rs, T, led, stamp, decl, dsha, rec


# ---- preflight refusals ---------------------------------------------------------------------------------------------------
def test_a_wrong_binding_hash_refuses(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="binding manifest"):
        _dry("run", _stamp(), rs, b, "0" * 64)


def test_a_changed_bound_file_refuses(tmp_path):
    b, sha, f = _binding(tmp_path)
    f.write_text("changed", encoding="utf-8", newline="\n")
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="bound file"):
        _dry("run", _stamp(), rs, b, sha)


@pytest.mark.parametrize("mode", ["dry", "live"])
def test_there_is_no_auth_path_argument(tmp_path, mode):
    """RC-3: the authorization location cannot be given on the command line."""
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(SystemExit):
        RN.main(["run", "--mode", mode, "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha,
                 "--auth-path", str(tmp_path / "anywhere.json")])


def test_live_mode_without_the_declaration_refuses(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="declaration"):
        RN.main(["run", "--mode", "live", "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha])
    with pytest.raises(RN.Refused, match="dry mode takes no declaration"):
        RN.main(["run", "--mode", "dry", "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha,
                 "--declaration", str(b), "--declaration-sha", sha])


@pytest.mark.parametrize("over,match", [({"lane_switches": None}, "does not bind 'lane_switches'"),
                                        ({"provider_env": None}, "does not bind 'provider_env'"),
                                        ({"project_day_limit": 120}, "integer 1..60")])
def test_live_mode_without_explicit_switches_or_provider_environment_refuses(tmp_path, over, match):
    """RC-5: no silent default in live mode -- refused before any folder is created."""
    b, sha, rs, T, led, stamp, decl, dsha, rec = _live_setup(tmp_path, **over)
    with pytest.raises(RN.Refused, match=match):
        RN.main(_live_args("run", decl, dsha, rs, b, sha))
    assert not (RN.SANDBOX_BASE / stamp).exists()


def test_live_mode_refuses_a_missing_or_different_ledger_scope(tmp_path):
    """RC-4: the runner verifies the declared scope (name and limits) before dispatch and never creates one."""
    b, sha, rs, T, led, stamp, decl, dsha, rec = _live_setup(tmp_path)
    led.unlink()
    H.fake_ledger(led, {"some-other-scope": (H.TEST_LIMITS, None, 1)})
    with pytest.raises(RN.Refused, match="does not exist"):
        RN.main(_live_args("run", decl, dsha, rs, b, sha))
    con = sqlite3.connect(str(led))
    assert [r[0] for r in con.execute("select scope from scopes")] == ["some-other-scope"], "no scope was created"
    con.close()
    led.unlink()
    H.fake_ledger(led, {H.TEST_SCOPE: ({"requests": 10}, None, 0)})
    with pytest.raises(RN.Refused, match="has limits"):
        RN.main(_live_args("run", decl, dsha, rs, b, sha))
    assert not (RN.SANDBOX_BASE / stamp).exists()


def test_live_mode_with_a_complete_declaration_and_no_authorization_refuses_before_any_folder_exists(tmp_path):
    b, sha, rs, T, led, stamp, decl, dsha, rec = _live_setup(tmp_path)
    assert not DG.pinned_path(decl).exists()
    with pytest.raises(RN.Refused, match="no owner dispatch authorization"):
        RN.main(_live_args("run", decl, dsha, rs, b, sha))
    assert not (RN.SANDBOX_BASE / stamp).exists(), "a refused live run leaves no run folder (a later authorized run is not blocked)"
    with pytest.raises(RN.Refused, match="nothing to resume"):
        RN.main(_live_args("resume", decl, dsha, rs, b, sha))
    with pytest.raises(RN.Refused, match="the stamp is the declaration's"):
        RN.main(_live_args("run", decl, dsha, rs, b, sha) + ["--stamp", "another-stamp"])
    with pytest.raises(RN.Refused, match="dry-mode drill only"):
        RN.main(_live_args("run", decl, dsha, rs, b, sha) + ["--dry-fault", "C:1"])


def test_lane_env_has_no_silent_default(tmp_path):
    with pytest.raises(RN.Refused, match="no switches for lane C"):
        RN.lane_env("live", tmp_path / "C", "C", {"lane_switches": {"B": {}}, "provider_env": {"AI_PROVIDER": "claude-code"}})
    with pytest.raises(RN.Refused, match="provider environment"):
        RN.lane_env("live", tmp_path / "C", "C", {"lane_switches": H.LIVE_SWITCHES, "provider_env": None})
    env = RN.lane_env("dry", tmp_path / "P", "P", {"lane_switches": RN.DRY_LANE_SWITCHES})
    assert not [k for k in env if k.startswith("AI_EVIDENCE_")] and env["AI_LEDGER_PATH"] == ""
    env = RN.lane_env("dry", tmp_path / "C", "C", {"lane_switches": RN.DRY_LANE_SWITCHES})
    assert {k: v for k, v in env.items() if k.startswith("AI_EVIDENCE_")} == RN.DRY_LANE_SWITCHES["C"]


# ---- RC-3: a direct live lane invocation runs the same preflight and the same guard ------------------------------------------
def _direct_lane(tmp_path, lane="C", cfg_over=None, env_over=None):
    b, sha, rs, T, led, stamp, decl, dsha, rec = _live_setup(tmp_path)
    v = PF.validate_declaration(rec, decl)
    folder = pathlib.Path(v["run_folder"])
    out = tmp_path / "out"
    out.mkdir()
    (folder / "inv-1").mkdir(parents=True)
    key = dsha
    AL.LaneAllowance(folder / "allowance.sqlite", v["caps"], v["project_day_limit"], run_key=key)
    AL.bind_store(folder / "capture.sqlite", key)
    truth_path = out / "TRUTH-R32.json"
    truth_path.write_text(PF.truth_text(T), encoding="utf-8", newline="\n")
    run_set = PF.load_run_set(rs, T)
    cfg = {"mode": "live", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(truth_path), "run_set": run_set,
           "run_set_path": str(rs), "run_folder": folder.as_posix(), "run_key": key, "stamp": stamp, "invocation": 1,
           "store": (folder / "capture.sqlite").as_posix(), "allowance": (folder / "allowance.sqlite").as_posix(), "caps": v["caps"],
           "project_day_limit": v["project_day_limit"], "trees": RN.TREES, "sandbox": {k: str(folder / "inv-1" / k) for k in ("B", "C", "R")},
           "binding": str(b), "binding_sha256": sha, "declaration_path": str(decl), "declaration_sha256": dsha,
           "lane_switches": v["lane_switches"], "provider_env": v["provider_env"], "switch_source": "the declaration's lane_switches",
           "policies": {"B": "B:accepted-path:evidence-off"}} | (cfg_over or {})
    cp = out / "RUN-CONFIG.json"
    cp.write_text(json.dumps(cfg), encoding="utf-8", newline="\n")
    env = RN.lane_env("live", folder / "inv-1" / lane, lane, cfg) | {DG.TOKEN_ENV: H.TEST_TOKEN} | (env_over or {})
    for k in [k for k, val in env.items() if val is None]:
        del env[k]
    tree = RN.TREES["baseline" if lane == "B" else "candidate"]
    r = subprocess.run([RN.PY, str(RN.HERE / "lane_r32.py"), lane, str(cp)], cwd=tree, env=env, capture_output=True, text=True)
    return r, folder, out, led


def test_a_direct_live_lane_invocation_is_refused_by_the_guard_without_authorization(tmp_path):
    r, folder, out, led = _direct_lane(tmp_path)
    assert r.returncode != 0 and "no owner dispatch authorization" in r.stderr and "[lane C guard]" in r.stderr, r.stderr[-2000:]
    assert not (out / "LANE-C.json").exists() and not (folder / "authorization").exists()
    con = sqlite3.connect(str(folder / "capture.sqlite"))
    assert con.execute("select count(*) from sqlite_master where name = 'requests'").fetchone()[0] == 0, "nothing reached the capture store"
    con.close()


@pytest.mark.parametrize("cfg_over,env_over,match", [
    ({"auth_path": "C:/anywhere/OWNER-DISPATCH-AUTHORIZATION.json"}, None, "authorization path cannot be configured"),
    ({"caps": {"B": 999, "C": 999, "R": 40, "P": 36}}, None, "differs from the declaration in \\['caps'\\]"),
    ({"lane_switches": H.LIVE_SWITCHES | {"C": {"AI_EVIDENCE_VARIANT": "EV1"}}}, None, "differs from the declaration in \\['lane_switches'\\]"),
    ({"dry_fault": {"lane": "C", "after_dispatches": 1}}, None, "dry-mode drill only"),
    (None, {"AI_EVIDENCE_IDGUARD": None}, "switches differ from the declaration"),
    (None, {"AI_EFFORT": "low"}, "AI_EFFORT in the environment"),
    (None, {"AI_MODEL_SMALL": "a-silent-default"}, "AI_MODEL_SMALL in the environment"),
])
def test_a_direct_live_lane_with_a_configuration_or_environment_unlike_the_declaration_is_refused(tmp_path, cfg_over, env_over, match):
    r, folder, out, led = _direct_lane(tmp_path, cfg_over=cfg_over, env_over=env_over)
    assert r.returncode != 0 and match.replace("\\", "") in r.stderr.replace("'", "'"), r.stderr[-2000:]
    assert not (out / "LANE-C.json").exists()


# ---- RC-4: one run folder per run key; the two-invocation drill ----------------------------------------------------------
def test_resumable_rules():
    assert RN.resumable({"status": "started"})[0] and RN.resumable({"status": "interrupted"})[0] and RN.resumable({"status": "refused"})[0]
    assert RN.resumable({"status": "finished", "comparison_state": "INCOMPLETE (C: budget stop)"})[0]
    for comp, match in (("RESULT: candidate failed", "terminal"), ("INVALID: B", "terminal"), ("PENDING", "complete")):
        ok, why = RN.resumable({"status": "finished", "comparison_state": comp})
        assert not ok and match in why


def test_the_two_invocation_drill(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, T = _run_set(tmp_path)
    stamp = _stamp()
    folder = RN.SANDBOX_BASE / stamp
    # 1. a fresh run whose lane C dies right after its 2nd dispatch was sent (row reserved, charge recorded)
    with pytest.raises(RuntimeError, match="lane C failed"):
        _dry("run", stamp, rs, b, sha, "--dry-fault", "C:2")
    st = json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8"))
    assert [i["status"] for i in st["invocations"]] == ["interrupted"] and st["caps"] == RN.CAPS and st["project_day_limit"] == 60
    con = sqlite3.connect(str(folder / "capture.sqlite"))
    c_rows = con.execute("select seq, state from requests where lane = 'C' order by seq").fetchall()
    con.close()
    assert [s for _, s in c_rows] == ["failed", "reserved"]
    allow = AL.LaneAllowance(folder / "allowance.sqlite", RN.CAPS, 60, run_key=st["run_key"], create=False)
    assert allow.used("C") == 2 and allow.used("B") == 3
    # 2. a second fresh invocation of the same run is refused
    with pytest.raises(RN.Refused, match="second fresh invocation"):
        _dry("run", stamp, rs, b, sha)
    # 3. the same-stamp resume: nothing re-sent, the reserved request served once as interrupted_charged, no fresh caps
    assert _dry("resume", stamp, rs, b, sha) == 0
    rep = json.loads((folder / "inv-2" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))
    assert rep["invocation"] == 2 and rep["kind"] == "resume" and rep["status"] == "finished" and rep["ledger_unchanged"]
    lanes = rep["lanes"]
    assert lanes["B"]["dry_stub_calls"] == 0 and lanes["B"]["serves_by_mode"] == {"same_bound_fingerprint": 3}
    assert lanes["C"]["dry_stub_calls"] == 1 and lanes["C"]["serves_by_mode"] == {"same_bound_fingerprint": 2}
    assert lanes["C"]["stats"].get("interrupted_charged") == 1
    assert lanes["R"]["serves_by_mode"] == {"reference_from_capture": 3} and lanes["R"]["dry_stub_calls"] == 1
    store = rep["store"]
    assert store["duplicate_bound_keys"] == [] and store["reserved_without_answer"] == 1
    con = sqlite3.connect(str(folder / "capture.sqlite"))
    assert con.execute("select state from requests where seq = ?", (c_rows[1][0],)).fetchone()[0] == "reserved", "the interrupted row is never re-sent"
    assert con.execute("select count(*) from requests where lane = 'C'").fetchone()[0] == 3
    con.close()
    assert rep["allowance"]["caps_fixed"] == RN.CAPS, "never fresh caps"
    assert rep["allowance"]["used"] == {"B": 3, "C": 3, "R": 1, "P": 0}, "every charge was a first dispatch; nothing charged twice"
    # 4. no further invocation: the run is complete
    with pytest.raises(RN.Refused, match="complete"):
        _dry("resume", stamp, rs, b, sha)
    with pytest.raises(RN.Refused, match="second fresh invocation"):
        _dry("run", stamp, rs, b, sha)
    st = json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8"))
    assert [(i["n"], i["kind"], i["status"]) for i in st["invocations"]] == [(1, "fresh", "interrupted"), (2, "resume", "finished")]
    assert not (folder / "WRITER.lock").exists()


def test_a_resume_of_another_run_or_with_another_binding_is_refused(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="nothing to resume"):
        _dry("resume", _stamp(), rs, b, sha)
    stamp = _stamp()
    with pytest.raises(RuntimeError):
        _dry("run", stamp, rs, b, sha, "--dry-fault", "B:1")
    b2, sha2, _ = _binding(tmp_path / "other")
    with pytest.raises(RN.Refused, match="same run"):
        _dry("resume", stamp, rs, b2, sha2)


def test_a_second_writer_is_refused(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    stamp = _stamp()
    with pytest.raises(RuntimeError):
        _dry("run", stamp, rs, b, sha, "--dry-fault", "B:1")
    lock = RN.SANDBOX_BASE / stamp / "WRITER.lock"
    lock.write_text("4242", encoding="utf-8")
    with pytest.raises(RN.Refused, match="another writer"):
        _dry("resume", stamp, rs, b, sha)
    lock.unlink()


# ---- the dry pipeline and the application path on synthetic documents ------------------------------------------------------
def test_the_dry_pipeline_on_the_reference_set_reads_no_document_and_sends_nothing(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    stamp = _stamp()
    assert _dry("run", stamp, rs, b, sha) == 0
    out = RN.SANDBOX_BASE / stamp / "inv-1" / "out"
    r = json.loads((out / "RUN-REPORT.json").read_text(encoding="utf-8"))
    assert r["model_requests"] == 0 and r["ledger_unchanged"] and r["dispatch_guard"]["authorized"] is False
    assert all(v["reader"] == "none" and not v["live_provider_attempts_blocked"] for v in r["lanes"].values())
    assert r["lanes"]["B"]["application_processing_run"] is False and r["lanes"]["C"]["application_reader_run"] is False
    assert r["state_check_C"]["ok"] and r["state_check_R"]["ok"] and r["candidate_outcome"] == "NOT ELIGIBLE"
    assert r["store"]["reference_serves"] == 3 and r["store"]["duplicate_bound_keys"] == []
    assert all(v["switch_source"].startswith("dry defaults") for v in r["lanes"].values())
    assert r["lanes"]["C"]["environment_check"]["switches"] == RN.DRY_LANE_SWITCHES["C"]
    rows = json.loads((out / "rows-B.json").read_text(encoding="utf-8"))
    assert all(v["state"] == "pending" and v["extracted"] is None for v in rows.values()), "no cohort document was read"


def _synthetic(tmp_path, truth_spec):
    files = tmp_path / "syn-files"
    T = SY.build(files, truth_spec)
    out = tmp_path / "syn-out"
    out.mkdir()
    tp = out / "TRUTH.json"
    tp.write_text(json.dumps(T), encoding="utf-8", newline="\n")
    sbx = RN.SANDBOX_BASE / _stamp()
    sbx.mkdir(parents=True)
    rs = [{"pool_id": p, "doc_key": d["doc_key"], "ep": d["ep"]} for p, d in T["documents"].items()]
    cfg = {"mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(tp), "run_set": rs,
           "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"), "caps": RN.CAPS, "project_day_limit": 60,
           "run_key": hashlib.sha256(str(sbx).encode()).hexdigest(), "invocation": 1, "trees": RN.TREES,
           "sandbox": {k: str(sbx / k) for k in "BCR"}, "declaration_sha256": None, "lane_switches": RN.DRY_LANE_SWITCHES,
           "switch_source": PF.DRY_LANE_SWITCHES_LABEL, "policies": {"B": "B:accepted-path:evidence-off"}}
    return T, cfg, rs, out, sbx, files


SHEET = ["SHOP DRAWING", "DRAWING NO: SYN-0001", "REV: 00", "TITLE: SYNTHETIC TEST SHEET ONE"]
FORM = ["MATERIAL SUBMITTAL", "SUBMITTAL NO: SYN-MAT-002", "REVISION: 01", "APPROVED AS NOTED"]
NS = ("not_scorable", None)


def test_application_path_on_synthetic_documents_b_then_c_from_b_then_r(tmp_path):
    T, cfg, rs, out, sbx, files = _synthetic(tmp_path, [
        {"pool_id": "SYN001", "lines": SHEET, "truth": {"identity": NS, "revision": NS, "decision": NS}},
        {"pool_id": "SYN002", "lines": FORM, "truth": {"identity": ("value", "SYN-MAT-002"), "revision": ("value", "01"), "decision": ("absent", None)}}])
    rep = RN.execute(cfg, T, rs, out, sbx, stage_files=files)
    assert rep["lanes"]["B"]["application_processing_run"] is True and rep["lanes"]["C"]["application_reader_run"] is True
    assert rep["model_requests"] == 0 and all(not v["live_provider_attempts_blocked"] for v in rep["lanes"].values())
    lb = json.loads((out / "LANE-B.json").read_text(encoding="utf-8"))
    assert {t["when"] for t in lb["tripwire"]} >= {"after_document", "final"}
    assert rep["stop_controller"]["comparison"] == "PENDING" and rep["state_check_C"]["ok"]
    assert "SCORE-BCR-R32.json" in {p.name for p in out.iterdir()}
    assert rep["candidate_outcome"] == "NOT DISPATCHABLE (EXTEND:extension-1)", "two synthetic documents never pass the population gate"


def test_the_b_tripwire_stops_b_and_c_never_starts(tmp_path):
    T, cfg, rs, out, sbx, files = _synthetic(tmp_path, [
        {"pool_id": "SYN002", "lines": FORM, "truth": {"identity": ("value", "SYN-MAT-999"), "revision": NS, "decision": NS}}])
    rep = RN.execute(cfg, T, rs, out, sbx, stage_files=files)
    assert rep["stop_controller"]["comparison"].startswith("INVALID") and rep["C_not_started"].startswith("INVALID")
    assert "C" not in rep["lanes"] and rep["model_requests"] == 0
    lb = json.loads((out / "LANE-B.json").read_text(encoding="utf-8"))
    hit = [c for t in lb["tripwire"] for c in t["resolved"]]
    assert hit and hit[0]["pool_id"] == "SYN002" and hit[0]["field"] == "identity"


def test_dry_mode_refuses_to_run_a_reader_on_a_cohort_document(tmp_path):
    rsp, T = _run_set(tmp_path, ("F045",))
    out = tmp_path / "coh"
    out.mkdir()
    tp = out / "TRUTH.json"
    tp.write_text(json.dumps(T), encoding="utf-8", newline="\n")
    sbx = RN.SANDBOX_BASE / _stamp()
    sbx.mkdir(parents=True)
    rs = json.loads(rsp.read_text(encoding="utf-8"))["documents"]
    cfg = {"mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(tp), "run_set": rs,
           "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"), "caps": RN.CAPS, "project_day_limit": 60,
           "run_key": "f" * 64, "invocation": 1, "trees": RN.TREES, "sandbox": {k: str(sbx / k) for k in "BCR"}, "declaration_sha256": None,
           "lane_switches": RN.DRY_LANE_SWITCHES, "switch_source": PF.DRY_LANE_SWITCHES_LABEL, "policies": {"B": "B:accepted-path:evidence-off"}}
    with pytest.raises(RuntimeError, match="lane B failed"):
        RN.execute(cfg, T, rs, out, sbx)
    assert "never runs a reader on a cohort document" in (out / "lane-B.log").read_text(encoding="utf-8")


def test_no_authorization_file_was_written_by_the_tests():
    roots = [RN.SANDBOX_BASE, pathlib.Path("C:/t/iso/work/r2x/r34"), PF.I.PILOT]
    found = [str(p) for r in roots if r.exists() for p in r.rglob("OWNER-DISPATCH-AUTHORIZATION*.json")]
    assert found == [], found
