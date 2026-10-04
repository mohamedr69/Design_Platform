"""runner_r32 / lane_r32 (ORCH-08): preflight refusals; (RC-3) no --auth-path, live refusals before any run folder exists, a
DIRECT live lane invocation refused by the same preflight and guard; (RC-4) one run folder, allowance and capture store per
run key, the two-invocation drill (a fresh run whose lane dies after a response came back, a second fresh run refused, a
same-stamp resume that re-sends nothing, serves the unsaved request as interrupted_charged and never gets fresh caps);
(RC-5) no silent default switches; the dry pipeline on the real reference set (reader 'none', no prediction) and the
application readers' path on SYNTHETIC EP-990001 documents only. ORCH-08: contract-3 declarations, the declared /
parameterised sandbox base (C:/t/r2x/r39-sandbox by default: no test twin), the gating of lanes, the resume rules of a
DEFERRED run, and every run-set document carrying a status in every lane. Temporary declarations and FAKE ledgers only;
no authorization file is ever written. The refusal-by-refusal visibility drills are in test_visibility_r38.py.
Run: python -m pytest -q test_runner_r32.py"""
import hashlib
import json
import pathlib
import sqlite3
import subprocess
import time
import uuid

import pytest

import allowance_r32 as AL
import dispatch_guard_r32 as DG
import model_identity_r38 as MI
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
                                         ledger_path=led, run_set_path=rs, **over)
    return b, sha, rs, T, led, stamp, decl, dsha, rec


def _report(stamp, n=1):
    return json.loads((RN.SANDBOX_BASE / stamp / f"inv-{n}" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))


# ---- preflight refusals ---------------------------------------------------------------------------------------------------
def test_the_default_sandbox_base_is_r38_and_no_twin_is_needed():
    assert RN.SANDBOX_BASE.as_posix() == "C:/t/r2x/r39-sandbox" and RN.SI.SANDBOX_BASE == RN.SANDBOX_BASE


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


@pytest.mark.parametrize("extra", [["--dry-fault", "C:1"], ["--dry-inject", "x.json"], ["--dry-synthetic", "x.json"], ["--sandbox-base", "C:/t/r2x/r39-sandbox"]])
def test_live_mode_refuses_every_dry_drill_and_a_sandbox_base_argument(tmp_path, extra):
    b, sha, rs, T, led, stamp, decl, dsha, rec = _live_setup(tmp_path)
    with pytest.raises(RN.Refused, match="dry-mode drills only"):
        RN.main(_live_args("run", decl, dsha, rs, b, sha) + extra)
    assert not (RN.SANDBOX_BASE / stamp).exists()


@pytest.mark.parametrize("over,match", [({"lane_switches": None}, "does not bind 'lane_switches'"),
                                        ({"provider_env": None}, "does not bind 'provider_env'"),
                                        ({"project_window": {"limit": 120, "window_s": 86400}}, "project_window must be"),
                                        ({"model_identity": None}, "does not bind 'model_identity'")])
def test_live_mode_without_explicit_values_refuses_before_any_folder(tmp_path, over, match):
    """RC-5 and contract 3: no silent default in live mode -- refused before any folder is created."""
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


def test_lane_env_has_no_silent_default(tmp_path):
    app = dict(PF.APPLICATION_ENV)
    with pytest.raises(RN.Refused, match="no switches for lane C"):
        RN.lane_env("live", tmp_path / "C", "C", {"lane_switches": {"B": {}}, "provider_env": {"AI_PROVIDER": "claude-code"}, "application_env": app})
    with pytest.raises(RN.Refused, match="provider environment"):
        RN.lane_env("live", tmp_path / "C", "C", {"lane_switches": H.LIVE_SWITCHES, "provider_env": None, "application_env": app})
    with pytest.raises(RN.Refused, match="no application environment"):          # ORCH-08C: no silent default either
        RN.lane_env("dry", tmp_path / "C", "C", {"lane_switches": RN.DRY_LANE_SWITCHES})
    with pytest.raises(RN.Refused, match="application_env must be exactly"):
        RN.lane_env("dry", tmp_path / "C", "C", {"lane_switches": RN.DRY_LANE_SWITCHES, "application_env": {"DRAWINGS_AI_REVIEW_ENABLED": "true"}})
    env = RN.lane_env("dry", tmp_path / "P", "P", {"lane_switches": RN.DRY_LANE_SWITCHES, "application_env": app})
    assert not [k for k in env if k.startswith("AI_EVIDENCE_")] and env["AI_LEDGER_PATH"] == ""
    env = RN.lane_env("dry", tmp_path / "C", "C", {"lane_switches": RN.DRY_LANE_SWITCHES, "application_env": app})
    assert {k: v for k, v in env.items() if k.startswith("AI_EVIDENCE_")} == RN.DRY_LANE_SWITCHES["C"]
    assert env["DRAWINGS_AI_REVIEW_ENABLED"] == "false", "ORCH-08C: the drawings-AI review is off in every lane" 


# ---- RC-3: a direct live lane invocation runs the same preflight and the same guard ------------------------------------------
def _direct_lane(tmp_path, lane="C", cfg_over=None, env_over=None):
    b, sha, rs, T, led, stamp, decl, dsha, rec = _live_setup(tmp_path)
    v = PF.validate_declaration(rec, decl)
    folder = pathlib.Path(v["run_folder"])
    out = tmp_path / "out"
    out.mkdir()
    (folder / "inv-1").mkdir(parents=True)
    key = dsha
    AL.LaneAllowance(folder / "allowance.sqlite", v["caps"], v["project_window"], parent=v["parent"], run_key=key)
    AL.bind_store(folder / "capture.sqlite", key)
    truth_path = out / "TRUTH-R32.json"
    truth_path.write_text(PF.truth_text(T), encoding="utf-8", newline="\n")
    run_set = PF.load_run_set(rs, T)
    cfg = {"mode": "live", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(truth_path), "run_set": run_set,
           "run_set_path": str(rs), "run_folder": folder.as_posix(), "run_key": key, "stamp": stamp, "invocation": 1, "sandbox_base": v["sandbox_base"],
           "store": (folder / "capture.sqlite").as_posix(), "allowance": (folder / "allowance.sqlite").as_posix(), "caps": v["caps"], "parent": v["parent"],
           "project_window": v["project_window"], "trees": RN.TREES, "sandbox": {k: str(folder / "inv-1" / k) for k in ("B", "C", "R")},
           "binding": str(b), "binding_sha256": sha, "declaration_path": str(decl), "declaration_sha256": dsha, "lane_switches": v["lane_switches"],
           "provider_env": v["provider_env"], "model_identity": v["model_identity"], "cli_version": "2.1.263 (Claude Code)",
           "switch_source": "the declaration's lane_switches", "policies": {"B": "B:accepted-path:evidence-off"},
           "application_env": v["application_env"], "lane_task_kinds": v["lane_task_kinds"], "resume_policy": v["resume_policy"],
           "decision_coverage_gate": v["decision_coverage_gate"], "project_totals": RN.project_totals_of(v["bounds"])} | (cfg_over or {})
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
    ({"parent": {"total": 999, "input_tokens": 1, "output_tokens": 1, "elapsed_s": 1}}, None, "differs from the declaration in \\['parent'\\]"),
    ({"project_window": {"limit": 600, "window_s": 86400}}, None, "differs from the declaration in \\['project_window'\\]"),
    ({"model_identity": {"provider": "claude-code", "small": "sonnet", "standard": "opus", "cli_path": "claude", "cli_version": None}}, None,
     "differs from the declaration in \\['model_identity'\\]"),
    ({"lane_switches": H.LIVE_SWITCHES | {"C": {"AI_EVIDENCE_VARIANT": "EV1"}}}, None, "differs from the declaration in \\['lane_switches'\\]"),
    ({"dry_fault": {"lane": "C", "after_dispatches": 1}}, None, "dry-mode drill only"),
    ({"dry_inject": [{"kind": "provider_timeout", "lane": "C", "calls": [1]}]}, None, "dry-mode drill only"),
    (None, {"AI_EVIDENCE_IDGUARD": None}, "switches differ from the declaration"),
    (None, {"AI_EFFORT": "low"}, "AI_EFFORT in the environment"),
    (None, {"AI_MODEL_SMALL": "sonnet"}, "AI_MODEL_SMALL in the environment"),
    (None, {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": "60"}, "AI_MAX_CALLS_PER_PROJECT_PER_DAY in the environment"),
    # ORCH-08C (R39-04, R39-08, R39-15): the contract-4 values are verified by every live lane before anything is built
    (None, {"DRAWINGS_AI_REVIEW_ENABLED": "true"}, "DRAWINGS_AI_REVIEW_ENABLED in the environment is 'true'"),
    (None, {"DRAWINGS_AI_REVIEW_ENABLED": None}, "DRAWINGS_AI_REVIEW_ENABLED in the environment is None"),
    ({"lane_task_kinds": {"B": ["read_submittal_form", "drawings_reply_match"], "C": [], "R": [], "P": []}}, None,
     "differs from the declaration in \\['lane_task_kinds'\\]"),
    ({"resume_policy": "earliest"}, None, "differs from the declaration in \\['resume_policy'\\]"),
    ({"decision_coverage_gate": "C_GE_B_AND_C_GE_R"}, None, "differs from the declaration in \\['decision_coverage_gate'\\]"),
    ({"application_env": {"DRAWINGS_AI_REVIEW_ENABLED": "false", "OTHER": "x"}}, None, None),
])
def test_a_direct_live_lane_with_a_configuration_or_environment_unlike_the_declaration_is_refused(tmp_path, cfg_over, env_over, match):
    if match is None:                                   # an application_env with another key: refused before the lane starts
        with pytest.raises(RN.Refused, match="application_env must be exactly"):
            _direct_lane(tmp_path, cfg_over=cfg_over, env_over=env_over)
        return
    r, folder, out, led = _direct_lane(tmp_path, cfg_over=cfg_over, env_over=env_over)
    assert r.returncode != 0 and match.replace("\\", "") in r.stderr.replace("'", "'"), r.stderr[-2000:]
    assert not (out / "LANE-C.json").exists()


# ---- RC-4 / ORCH-08: one run folder per run key; the resume rules; the two-invocation drill ---------------------------------
def test_resumable_rules():
    now = 1000.0
    assert RN.resumable({"status": "started"}, now=now)[0] and RN.resumable({"status": "interrupted"}, now=now)[0]
    assert RN.resumable({"status": "refused"}, now=now)[0]
    assert RN.resumable({"status": "finished", "comparison_state": "INCOMPLETE (C: budget stop)"}, now=now)[0]
    for comp, match in (("RESULT: candidate failed", "terminal"), ("INVALID: B", "terminal"), ("PENDING", "complete")):
        ok, why = RN.resumable({"status": "finished", "comparison_state": comp}, now=now)
        assert not ok and match in why
    deferred = {"status": "finished", "comparison_state": "INCOMPLETE", "run_state": "DEFERRED", "earliest_retry": 1100.0}
    ok, why = RN.resumable(deferred, now=now, bound_end=5000)
    assert not ok and "allows a resume at" in why and "nothing was created" in why
    assert RN.resumable(deferred, now=1101.0, bound_end=5000)[0]
    # ORCH-08C (R39-08): the declared resume policy's time governs
    full = deferred | {"resume_policy": "full", "resume_not_before": 1500.0, "retry_at_full": {"structural": 1500.0, "planning": 1200.0}}
    ok, why = RN.resumable(full, now=1101.0, bound_end=5000)
    assert not ok and "'full'" in why, "after the earliest retry but before the full time: refused under 'full'"
    assert RN.resumable(full, now=1501.0, bound_end=5000)[0]
    early = deferred | {"resume_policy": "earliest", "resume_not_before": 1100.0}
    assert RN.resumable(early, now=1101.0, bound_end=5000)[0]
    ok, why = RN.resumable(deferred, now=6000.0, bound_end=5000)
    assert not ok and "elapsed bound ended" in why
    assert not RN.resumable({"status": "closed", "comparison_state": "INCOMPLETE: x"}, now=now)[0]
    assert not RN.resumable({"status": "finished", "comparison_state": "INCOMPLETE", "run_state": "INVALID"}, now=now)[0]


def test_the_two_invocation_drill(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, T = _run_set(tmp_path)
    stamp = _stamp()
    folder = RN.SANDBOX_BASE / stamp
    # 1. a fresh run whose lane C dies right after its 2nd response came back, before it was saved (row reserved, charge recorded)
    with pytest.raises(RuntimeError, match="lane C failed"):
        _dry("run", stamp, rs, b, sha, "--dry-fault", "C:2")
    st = json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8"))
    assert [i["status"] for i in st["invocations"]] == ["interrupted"] and st["caps"] == RN.CAPS and st["parent"] == RN.PARENT
    con = sqlite3.connect(str(folder / "capture.sqlite"))
    c_rows = con.execute("select seq, state from requests where lane = 'C' order by seq").fetchall()
    con.close()
    assert [s for _, s in c_rows] == ["failed", "reserved"]
    allow = AL.LaneAllowance(folder / "allowance.sqlite", RN.CAPS, RN.WINDOW, parent=RN.PARENT, run_key=st["run_key"], create=False)
    assert allow.used("C") == 2 and allow.used("B") == 3
    assert [c["outcome"] for c in allow.audit()["charges"] if c["lane"] == "C"] == ["dry_refused", "dispatched"], "the unsaved request stays charged"
    # 2. a second fresh invocation of the same run is refused
    with pytest.raises(RN.Refused, match="second fresh invocation"):
        _dry("run", stamp, rs, b, sha)
    # 3. the same-stamp resume: nothing re-sent, the unsaved request served once as interrupted_charged, no fresh caps
    assert _dry("resume", stamp, rs, b, sha) == 0
    rep = _report(stamp, 2)
    assert rep["invocation"] == 2 and rep["kind"] == "resume" and rep["status"] == "finished" and rep["ledger_unchanged"]
    lanes = rep["lanes"]
    assert lanes["B"]["dry_stub_calls"] == 0 and lanes["B"]["serves_by_mode"] == {"same_bound_fingerprint": 3}
    assert lanes["C"]["dry_stub_calls"] == 1 and lanes["C"]["serves_by_mode"] == {"same_bound_fingerprint": 2}
    assert lanes["C"]["stats"].get("provider_failure") == 1, "the served interrupted_charged row"
    assert any(e["kind"] == "interrupted_charged" and e["served"] for e in lanes["C"]["limit_events"]), "visible, per document and page"
    assert rep["documents"]["C"]["F051"]["status"] == "INCOMPLETE" and "interrupted_charged" in rep["documents"]["C"]["F051"]["kinds"]
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
    assert [json.loads(x)["cli_version"] for x in (folder / MI.CLI_LOG).read_text(encoding="utf-8").splitlines()] == [RN.DRY_CLI_VERSION] * 2


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
    for lane in ("B", "C", "R"):                                      # ORCH-08: every run-set document has a status
        assert set(r["documents"][lane]) >= {"F045", "F051", "F066"} and all(d["status"] == "COMPLETE" for d in r["documents"][lane].values())
    assert r["scope_limitations"][0]["id"] == "unsupported-control-shortfall" and r["run_state"] == "FINISHED"
    assert r["provider_identity"]["declared_models"] == {"small": "claude-sonnet-5", "standard": "claude-opus-5"}
    assert (RN.SANDBOX_BASE / stamp / "inv-1" / "IDENTITY-LOG-C.jsonl").is_file() and (out / "ALLOWANCE-AUDIT.json").is_file()
    assert r["diagnostics"]["R"]["credit"].startswith("none") and r["diagnostics"]["P"]["credit"].startswith("none")


def _synthetic(tmp_path, truth_spec):
    files = tmp_path / "syn-files"
    T = SY.build(files, truth_spec)
    out = tmp_path / "syn-out"
    out.mkdir()
    tp = out / "TRUTH.json"
    tp.write_text(json.dumps(T), encoding="utf-8", newline="\n")
    sbx = RN.SANDBOX_BASE / _stamp()
    (sbx / "inv-1").mkdir(parents=True)
    rs = [{"pool_id": p, "doc_key": d["doc_key"], "ep": d["ep"]} for p, d in T["documents"].items()]
    cfg = {"mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(tp), "run_set": rs,
           "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"), "caps": RN.CAPS, "parent": RN.PARENT,
           "project_window": RN.WINDOW, "run_key": hashlib.sha256(str(sbx).encode()).hexdigest(), "invocation": 1, "trees": RN.TREES,
           "sandbox": {k: str(sbx / "inv-1" / k) for k in "BCR"}, "sandbox_base": RN.SANDBOX_BASE.as_posix(), "run_folder": sbx.as_posix(),
           "declaration_sha256": None, "lane_switches": RN.DRY_LANE_SWITCHES, "switch_source": PF.DRY_LANE_SWITCHES_LABEL,
           "model_identity": RN.DRY_PINS, "cli_version": RN.DRY_CLI_VERSION, "policies": {"B": "B:accepted-path:evidence-off"},
           "application_env": dict(PF.APPLICATION_ENV), "lane_task_kinds": PF.task_kinds_for(RN.DRY_LANE_SWITCHES), "resume_policy": "full",
           "decision_coverage_gate": "C_GE_B_ONLY", "project_totals": None}
    return T, cfg, rs, out, sbx / "inv-1", files


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
    for lane in ("B", "C", "R"):
        assert set(rep["documents"][lane]) == {"SYN001", "SYN002"}, "every document has a status in every lane"


def test_the_b_tripwire_stops_b_and_c_never_starts(tmp_path):
    T, cfg, rs, out, sbx, files = _synthetic(tmp_path, [
        {"pool_id": "SYN002", "lines": FORM, "truth": {"identity": ("value", "SYN-MAT-999"), "revision": NS, "decision": NS}}])
    rep = RN.execute(cfg, T, rs, out, sbx, stage_files=files)
    assert rep["stop_controller"]["comparison"].startswith("INVALID") and rep["C_not_started"].startswith("INVALID")
    assert "C" not in rep["lanes"] and rep["model_requests"] == 0 and rep["lane_gates"]["C"].startswith("not started")
    assert rep["documents"]["C"]["SYN002"]["status"] == "INCOMPLETE" and rep["documents"]["C"]["SYN002"]["kinds"] == ["not_started"], \
        "a lane that never starts still lists every document"
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
    (sbx / "inv-1").mkdir(parents=True)
    rs = json.loads(rsp.read_text(encoding="utf-8"))["documents"]
    cfg = {"mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(tp), "run_set": rs,
           "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"), "caps": RN.CAPS, "parent": RN.PARENT, "project_window": RN.WINDOW,
           "run_key": "f" * 64, "invocation": 1, "trees": RN.TREES, "sandbox": {k: str(sbx / "inv-1" / k) for k in "BCR"}, "declaration_sha256": None,
           "sandbox_base": RN.SANDBOX_BASE.as_posix(), "run_folder": sbx.as_posix(), "model_identity": RN.DRY_PINS, "cli_version": RN.DRY_CLI_VERSION,
           "lane_switches": RN.DRY_LANE_SWITCHES, "switch_source": PF.DRY_LANE_SWITCHES_LABEL, "policies": {"B": "B:accepted-path:evidence-off"},
           "application_env": dict(PF.APPLICATION_ENV), "lane_task_kinds": PF.task_kinds_for(RN.DRY_LANE_SWITCHES), "resume_policy": "full",
           "decision_coverage_gate": "C_GE_B_ONLY", "project_totals": None}
    with pytest.raises(RuntimeError, match="lane B failed"):
        RN.execute(cfg, T, rs, out, sbx / "inv-1")
    assert "never runs a reader on a cohort document" in (out / "lane-B.log").read_text(encoding="utf-8")


def test_a_synthetic_drill_refuses_any_document_that_is_not_synthetic(tmp_path):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"documents": [{"pool_id": "F045", "lines": SHEET, "truth": {"identity": NS, "revision": NS, "decision": NS}}]}),
                    encoding="utf-8")
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="only SYN"):
        _dry("run", _stamp(), rs, b, sha, "--dry-synthetic", str(spec))


def test_resume_times_take_the_latest_structural_full_time_of_the_deferred_documents():
    docs = {"B": {"F1": {"status": "DEFERRED", "retry_at": 100.0, "retry_at_full": {"planning": 150.0, "structural": 400.0}},
                  "F2": {"status": "DEFERRED", "retry_at": 120.0, "retry_at_full": {"planning": 160.0, "structural": 300.0}},
                  "F3": {"status": "COMPLETE"}}, "C": {"F1": {"status": "DEFERRED", "retry_at": 100.0}}}
    t = RN.resume_times(docs, 100.0)
    assert t == {"earliest": 100.0, "full": 400.0, "full_planning": 160.0, "full_structural": 400.0}
    assert RN.resume_times({"B": {"F1": {"status": "DEFERRED", "retry_at": 100.0}}}, 100.0)["full"] == 100.0, "no totals: the earliest"


def test_project_totals_come_from_the_bounds_file():
    tot = RN.project_totals_of(H.bounds_for())
    assert tot["EP-27331"] == {"planning": 63.0, "structural": 160}
    assert RN.project_totals_of(None) is None


def test_a_dry_drill_may_declare_only_a_known_resume_policy(tmp_path):
    p = tmp_path / "inject.json"
    p.write_text(json.dumps({"resume_policy": "whenever"}), encoding="utf-8")
    with pytest.raises(RN.Refused, match="resume_policy"):
        RN._dry_inject(p)
    p.write_text(json.dumps({"resume_policy": "earliest", "injections": [{"kind": "undeclared_request", "lane": "B", "calls": [1]}]}), encoding="utf-8")
    assert RN._dry_inject(p)["resume_policy"] == "earliest"


def test_no_authorization_file_was_written_by_the_tests():
    roots = [RN.SANDBOX_BASE, pathlib.Path("C:/t/iso/work/r2x/r38"), PF.I.PILOT]
    found = [str(p) for r in roots if r.exists() for p in r.rglob("OWNER-DISPATCH-AUTHORIZATION*.json")]
    assert found == [], found
    time.sleep(0)


def test_the_resume_invocation_model_for_ep27331(tmp_path):
    """ORCH-08C (R39-08): the runbook input -- invocations EP-27331 needs under each policy, planning and structural demand."""
    import resume_invocations_r39 as RI
    bp = tmp_path / "bounds.json"
    bp.write_text(json.dumps(H.bounds_for()), encoding="utf-8")
    assert RI.main(["x", str(bp), str(tmp_path / "out.json")]) == 0
    o = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert o["table"] == {"planning": {"full": 2, "full_burst": 2, "earliest_paced": 2, "earliest_burst": 4},
                          "structural": {"full": 3, "full_burst": 3, "earliest_paced": 3, "earliest_burst": 101}}
    assert all(r["completed"] for r in o["results"].values()) and o["structural_total"] == 160
