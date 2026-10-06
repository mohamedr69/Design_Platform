"""ORCH-10 (R42; Verification 40 R40-04, owner decision A-11 option 2): the fail-closed global-provider boundary of lanes
C, R and P. (a) the static analysis shows every get_provider() site resolved to a refusing provider (C, R, P) or to the
harness chain (B), installed before any application entry; (b) dry runs in which an injected APPLICATION path calls
get_provider().complete(...) in C, R and P: refused, recorded as the contract breach 'global_provider_request', the run
INVALID, 0 model requests, 0 CLI processes (this suite runs under the R42 audit guard), the AI ledger unchanged; (c) lane
B unchanged: the same injected call reaches the harness chain (the gate) and no breach is written.
Run: python -m pytest -q test_global_provider_r42.py"""
import hashlib
import json
import pathlib
import uuid

import pytest

import allowance_r32 as AL
import capture_store as CS
import preflight_r32 as PF
import request_paths_r42 as RP
import run_control_r38 as RC
import run_state_r38 as RS
import runner_r32 as RN

IDS = ("F045", "F051")
_T = {}


def _truth():
    if "t" not in _T:
        _T["t"] = PF.build_truth()
    return _T["t"]


def _binding(tmp_path):
    f = tmp_path / "bound.txt"
    f.write_text("bound", encoding="utf-8", newline="\n")
    p = tmp_path / "BINDING.json"
    p.write_text(json.dumps({"files": {"g": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()}}}), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def _run_set(tmp_path):
    T = _truth()
    p = tmp_path / "RUN-SET.json"
    p.write_text(json.dumps({"documents": [{"pool_id": i, "doc_key": T["documents"][i]["doc_key"], "ep": T["documents"][i]["ep"]} for i in IDS]}),
                 encoding="utf-8", newline="\n")
    return p


def _dry(tmp_path, injections):
    b, sha = _binding(tmp_path)
    rs = _run_set(tmp_path)
    inj = tmp_path / "INJECT.json"
    inj.write_text(json.dumps({"injections": injections}), encoding="utf-8", newline="\n")
    stamp = f"r42d-gp-{uuid.uuid4().hex[:8]}"
    args = ["--mode", "dry", "--stamp", stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, "--dry-inject", str(inj)]
    RN.main(["run"] + args)
    folder = RN.SANDBOX_BASE / stamp
    rep = json.loads((folder / "inv-1" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))
    _ARGS[str(folder)] = args
    return folder, rep


_ARGS = {}


def _lane(folder, lane):
    p = folder / "inv-1" / "out" / f"LANE-{lane}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ---- (a) static -------------------------------------------------------------------------------------------------------------------
def test_static_every_lane_installs_its_global_provider_before_any_application_entry():
    ins = RP.lane_installs()
    res = RP.global_resolution(ins)
    for lane in ("B", "C", "R", "P"):
        assert res[lane]["installed_before_every_application_entry"], (lane, res[lane])
    assert "RefusingGlobalProvider" in res["C"]["global_provider"] and "harness chain" in res["B"]["global_provider"]
    assert res["C"]["installed_at_line"] < res["B"]["installed_at_line"], "the refusing provider is installed right after the provider import"


def test_static_full_analysis_resolves_every_get_provider_site(tmp_path):
    out = tmp_path / "REQUEST-PATHS-STATIC-R42.json"
    assert RP.main(["x", str(out)]) == 0
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["summary"]["every_site_guarded"] and r["summary"]["every_lane_installs_before_its_application_entry"]
    assert r["summary"]["get_provider_sites"] > 0
    cand = [x for x in r["get_provider_sites"] if x["tree"] == "candidate"]
    assert {x["lane"] for x in cand} == {"C", "R", "P"} and all("RefusingGlobalProvider" in x["resolves_to"] for x in cand)
    assert all(x["resolves_to"].startswith("the harness chain") for x in r["get_provider_sites"] if x["tree"] == "baseline")
    assert r["summary"]["application_set_provider_sites_reached"] == [], "no application path a lane reaches replaces the global provider"


# ---- the refusing provider itself -------------------------------------------------------------------------------------------------
class Resp:
    def __init__(self, data=None, model="", error=None, error_detail=None, **kw):
        self.data, self.model, self.error, self.error_detail = data, model, error, error_detail


class Req:
    task, tier = "discover_page", "small"


def test_the_refusing_provider_refuses_records_and_invalidates(tmp_path):
    rec = RS.LaneRecorder("C", [{"pool_id": "F045"}])
    alw = AL.LaneAllowance(tmp_path / "allowance.sqlite", run_key="k" * 64)
    ctl = RC.ControllerR38()
    g = RC.RefusingGlobalProvider(Resp, lane="C", run_folder=tmp_path, invocation=1).attach(recorder=rec, allowance=alw, ctl=ctl,
                                                                                            ep_of=lambda: "27331", page_of=lambda: 2)
    CS.set_context(sha256="abc", page=2)
    rec.begin("F045", "abc")
    r = g.complete(Req())
    assert r.error == "dispatch_refused" and r.error_detail.startswith("global_provider_request") and r.data is None
    m = RS.breach_marker(tmp_path)
    assert m["kind"] == "global_provider_request" and m["lane"] == "C" and m["task"] == "discover_page" and m["document"] == "F045"
    assert ctl.comparison.startswith("INVALID") and all(v["state"] != "running" for v in ctl.lanes.values())
    assert alw.used() == 0, "never charged"
    assert [e["kind"] for e in rec.events] == ["global_provider_request"] and rec.events[0]["class"] == "limit"
    assert rec.documents()["F045"]["status"] == "INCOMPLETE"
    assert g.events == [{"lane": "C", "kind": "contract_breach", "task": "discover_page", "error": "global_provider_request", "pool_id": "F045"}]
    assert RS.event_kind(Resp(error="contract_breach", error_detail="global_provider_request: x")) == "global_provider_request"
    CS.set_context()


# ---- (b) dynamic: C, R and P refuse an application path's get_provider().complete(...) ---------------------------------------------
@pytest.mark.parametrize("lane,calls", [("C", [1]), ("R", [1]), ("P", [0])])
def test_an_application_get_provider_call_in_c_r_or_p_is_refused_breached_and_invalidates_the_run(tmp_path, lane, calls):
    folder, rep = _dry(tmp_path, [{"kind": "global_provider_request", "lane": lane, "calls": calls}])
    m = RS.breach_marker(folder)
    assert m is not None and m["kind"] == "global_provider_request" and m["lane"] == lane
    assert rep["comparison_state"].startswith("INVALID") and rep["candidate_outcome"] == "INVALID" and rep["run_state"] == "INVALID"
    assert rep["model_requests"] == 0 and rep["ledger_unchanged"] is True
    lm = _lane(folder, lane)
    gp = lm["global_provider"]
    assert gp["lane_kind"] == "refusing" and gp["at_start"] == "RefusingGlobalProvider" and gp["still_installed_at_end"] is True
    assert gp["requests_refused"] == 1 and gp["drill"][0]["error"] == "dispatch_refused" and gp["drill"][0]["provider"] == "RefusingGlobalProvider"
    import sqlite3
    c = sqlite3.connect(f"file:{(folder / 'allowance.sqlite').as_posix()}?mode=ro", uri=True)
    try:
        kinds = [r[0] for r in c.execute("select kind from refusals where lane = ?", (lane,))]
        charges = c.execute("select count(*) from charges where lane = ?", (lane,)).fetchone()[0]
    finally:
        c.close()
    assert "global_provider_request" in kinds
    assert charges == lm["dry_stub_calls"], "every charge is a dispatch through the chain to the stub; the refused global request is never charged"
    assert any(e["kind"] == "global_provider_request" for e in lm["limit_events"])
    with pytest.raises(RN.Refused, match="contract breach recorded in CONTRACT-BREACH.json"):
        RN.main(["resume"] + _ARGS[str(folder)])


def test_lane_b_is_unchanged_the_same_call_reaches_the_harness_chain(tmp_path):
    folder, rep = _dry(tmp_path, [{"kind": "global_provider_request", "lane": "B", "calls": [1]}])
    assert RS.breach_marker(folder) is None, "in B the global provider is the chain: a declared request with its context passes the gate"
    lb = _lane(folder, "B")
    gp = lb["global_provider"]
    assert gp["lane_kind"] == "harness_chain" and gp["at_end"] == "StopGuardR38" and gp["requests_refused"] == 0
    assert gp["drill"][0]["provider"] == "StopGuardR38" and gp["drill"][0]["error"] == "dry_refused", "reached the dry stub through the chain"
    assert rep["run_state"] == "FINISHED" and rep["model_requests"] == 0 and rep["ledger_unchanged"] is True
    for lane in ("C", "R", "P"):
        lm = _lane(folder, lane)
        assert lm["global_provider"]["at_start"] == "RefusingGlobalProvider" and lm["global_provider"]["requests_refused"] == 0
