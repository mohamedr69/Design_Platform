"""R43-42 (review45): the dry-only baseline-facts drill (drill_r45.py; runner_r32 --dry-baseline-facts; lane_r32 drill branch).
(a) refusals: a fourth or a substituted document, lanes C / R / P, the cand-r30n tree, the live flag, a resume, another
drill flag, a stamp naming a live run, an owner token in the environment, a provider that is not the refusing stub, and a
ledger / scope / RUN / allowance / authorization path being consulted (runner: forbid; lane: the configuration check and
the Forbidden sentinels) -- each before anything is created; the other dry rules are unchanged (reader 'none' over the real
cohort, the cohort assertion without the drill, --dry-synthetic SYN* only);
(b) ONE real drill over F009, F020 and F030 (lane B, frozen-r13, AI off): the three documents pass through the lane's own
functions, asserted on the lane's call trace (document_processing.run -> lane process -> document_sync.process ->
b_tripwire 'after_document', and the 'final' tripwire over all three), the tripwire recomputation equals the lane's, 0
requests (refusing provider 0 calls, dry stub 0 calls, no complete() traced), the AI ledger unchanged, and no run state,
allowance, capture store or authorization file in the drill folder;
(c) the criterion evaluation of DRILL-CRITERION.md (PASS, FAIL on a resolved critical or a request, NOT PASS when a
document is not exercised). The drill's RESULT on the real documents is not asserted here: a critical is reported, never
made to pass. Run: python -m pytest -q test_dry_baseline_drill_r45.py"""
import hashlib
import json
import os
import pathlib
import subprocess
import uuid

import pytest

import allowance_r32 as AL
import dispatch_guard_r32 as DG
import drill_r45 as DR
import model_identity_r38 as MI
import preflight_r32 as PF
import request_paths_r42 as RP
import run_control_r38 as RC
import runner_r32 as RN

RUN_SET = "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json"
_T = {}


def _truth():
    if "t" not in _T:
        _T["t"] = PF.build_truth()
    return _T["t"]


def _binding(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    f = tmp_path / "bound.txt"
    f.write_text("bound", encoding="utf-8", newline="\n")
    p = tmp_path / "BINDING.json"
    p.write_text(json.dumps({"files": {"g": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()}}}), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def _spec(tmp_path, **over):
    spec = {"drill": "baseline-facts", "lane": "B", "tree": "C:/t/iso/frozen-r13",
            "documents": [{"pool_id": p, "staged_sha256": s} for p, s in DR.ALLOW.items()]}
    spec |= over
    p = tmp_path / f"SPEC-{uuid.uuid4().hex[:6]}.json"
    p.write_text(json.dumps(spec), encoding="utf-8", newline="\n")
    return p


def _stamp():
    return f"t45-{uuid.uuid4().hex[:10]}"


def _args(tmp_path, spec, stamp=None, mode="dry", command="run", extra=()):
    b, sha = _binding(tmp_path)
    return [command, "--mode", mode, "--dry-baseline-facts", str(spec), "--stamp", stamp or _stamp(), "--run-set", RUN_SET,
            "--binding", str(b), "--binding-sha", sha, *extra]


def _created(stamp):
    return (RN.SANDBOX_BASE / f"{DR.FOLDER_PREFIX}{stamp}").exists() or (RN.SANDBOX_BASE / stamp).exists()


# ---- (a) refusals, runner side: nothing is created ---------------------------------------------------------------------------
@pytest.mark.parametrize("docs,match", [
    (list(DR.ALLOW.items()) + [("F037", "0" * 64)], "exactly"),
    ([("F009", DR.ALLOW["F009"]), ("F020", DR.ALLOW["F020"])], "exactly"),
    ([("F009", DR.ALLOW["F009"]), ("F020", DR.ALLOW["F020"]), ("F033", DR.ALLOW["F030"])], "exactly"),
    ([("F009", DR.ALLOW["F009"]), ("F020", DR.ALLOW["F020"]), ("F030", DR.ALLOW["F020"])], "is not the allowed"),
])
def test_any_other_document_set_is_refused_before_anything_is_created(tmp_path, docs, match):
    stamp = _stamp()
    spec = _spec(tmp_path, documents=[{"pool_id": p, "staged_sha256": s} for p, s in docs])
    with pytest.raises(RN.Refused, match=match):
        RN.main(_args(tmp_path, spec, stamp))
    assert not _created(stamp)


@pytest.mark.parametrize("lane", ["C", "R", "P"])
def test_lanes_c_r_and_p_are_refused(tmp_path, lane):
    stamp = _stamp()
    with pytest.raises(RN.Refused, match="lane B only"):
        RN.main(_args(tmp_path, _spec(tmp_path, lane=lane), stamp))
    assert not _created(stamp)


@pytest.mark.parametrize("tree", ["C:/t/iso/cand-r30n", "C:/t/iso/cand-r30", "C:/t/iso/frozen-r12"])
def test_any_tree_but_frozen_r13_is_refused(tmp_path, tree):
    stamp = _stamp()
    with pytest.raises(RN.Refused, match="frozen-r13 only"):
        RN.main(_args(tmp_path, _spec(tmp_path, tree=tree), stamp))
    assert not _created(stamp)


def test_the_live_flag_is_refused(tmp_path):
    stamp = _stamp()
    with pytest.raises(RN.Refused, match="dry-mode drills only"):
        RN.main(_args(tmp_path, _spec(tmp_path), stamp, mode="live"))
    assert not _created(stamp)


@pytest.mark.parametrize("extra,command,match", [
    ([], "resume", "never resumed"),
    (["--dry-synthetic", "x.json"], "run", "no other drill"),
    (["--dry-inject", "x.json"], "run", "no other drill"),
    (["--dry-fault", "B:1"], "run", "no other drill"),
    (["--out", "C:/t/r2x/r42-sandbox/anywhere"], "run", "no --out"),
])
def test_a_resume_another_drill_or_an_output_folder_is_refused(tmp_path, extra, command, match):
    stamp = _stamp()
    with pytest.raises(RN.Refused, match=match):
        RN.main(_args(tmp_path, _spec(tmp_path), stamp, command=command, extra=extra))
    assert not _created(stamp)


@pytest.mark.parametrize("stamp", ["r32-v4", "x-r32-v5", "R32-V9-b", "a/b", "ab"])
def test_a_stamp_naming_a_live_run_or_a_bad_stamp_is_refused(tmp_path, stamp):
    with pytest.raises(RN.Refused, match="drill stamp"):
        RN.main(_args(tmp_path, _spec(tmp_path), stamp))
    assert not (RN.SANDBOX_BASE / "r32-v4").exists()


def test_an_owner_token_in_the_environment_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv(DG.TOKEN_ENV, "test-token-not-real")
    stamp = _stamp()
    with pytest.raises(RN.Refused, match="never reads an owner token"):
        RN.main(_args(tmp_path, _spec(tmp_path), stamp))
    assert not _created(stamp)


def test_forbid_refuses_every_ledger_scope_run_allowance_and_authorization_function_and_restores_them(tmp_path):
    before = {n: getattr(m, n) for m, n in ((PF, "verify_ledger_scope"), (DG, "authorize"), (AL, "LaneAllowance"), (RN, "ledger_state"))}
    with DR.forbid(RN) as names:
        assert {"preflight_r32.verify_ledger_scope", "preflight_r32.ledger_counts", "dispatch_guard_r32.authorize", "dispatch_guard_r32.check",
                "allowance_r32.LaneAllowance", "allowance_r32.bind_store", "runner_r32.ledger_state", "runner_r32.create_allowance_atomic",
                "runner_r32._state_write", "model_identity_r38.record_invocation"} <= set(names)
        calls = [lambda: PF.verify_ledger_scope({"path": "x", "scope": "y"}), lambda: PF.ledger_counts(), lambda: PF.ledger_snapshot("x"),
                 lambda: DG.authorize("d", "s", run_folder=tmp_path, invocation=1, action="consume"), lambda: DG.check("d", "s"),
                 lambda: AL.LaneAllowance(tmp_path / "a.sqlite", {}, {}), lambda: AL.bind_store(tmp_path / "c.sqlite", "k"),
                 lambda: RN.ledger_state(), lambda: RN.create_allowance_atomic({}, tmp_path), lambda: RN._state_write(tmp_path / "RUN-STATE.json", {}),
                 lambda: MI.record_invocation(tmp_path, 1, {}, "v")]
        for c in calls:
            with pytest.raises(PF.Refused, match="never consults"):
                c()
    assert list(tmp_path.iterdir()) == [], "nothing was written"
    assert {n: getattr(m, n) for m, n in ((PF, "verify_ledger_scope"), (DG, "authorize"), (AL, "LaneAllowance"), (RN, "ledger_state"))} == before


def test_the_forbidden_sentinel_refuses_and_records_every_use():
    DR.VIOLATIONS.clear()
    f = DR.Forbidden("the run's allowance / capture store")
    with pytest.raises(PF.Refused, match="never consults"):
        f.record_refusal("B", "x", "y")
    with pytest.raises(PF.Refused, match="never consults"):
        f.used("B")
    assert len(DR.VIOLATIONS) == 2
    DR.VIOLATIONS.clear()


class _Prov:
    def __init__(self, p):
        self.p = p

    def get_provider(self):
        return self.p


def test_a_provider_that_is_not_the_refusing_stub_is_refused():
    from app.ai.provider import AiResponse, Usage
    good = RC.RefusingGlobalProvider(AiResponse, lane="B", run_folder="C:/t/r2x/r42-sandbox/none", invocation=1)
    other = RC.RefusingGlobalProvider(AiResponse, lane="B", run_folder="C:/t/r2x/r42-sandbox/none", invocation=1)
    stub = RC.DryStub(AiResponse, Usage, "B")
    assert DR.check_provider(_Prov(good), good)["global_provider"] == "RefusingGlobalProvider"
    for installed, expected in ((stub, stub), (other, good), (None, good), (good, None)):
        with pytest.raises(PF.Refused, match="not the refusing global provider"):
            DR.check_provider(_Prov(installed), expected)


# ---- (a) refusals, lane side: a direct lane invocation with a drill configuration ---------------------------------------------
def _lane_cfg(tmp_path, **over):
    T = _truth()
    folder = tmp_path / "r32-drill-direct"
    cfg = {"drill": "baseline-facts", "mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(tmp_path / "out"),
           "truth": str(tmp_path / "TRUTH.json"), "run_folder": folder.as_posix(), "run_key": None, "invocation": 1, "trees": dict(RN.TREES),
           "sandbox": {"B": str(folder / "B")},
           "run_set": [{"pool_id": p, "doc_key": T["documents"][p]["doc_key"], "ep": T["documents"][p]["ep"]} for p in DR.ALLOW]}
    for k, v in over.items():
        if v is None:
            cfg.pop(k, None)
        else:
            cfg[k] = v
    (tmp_path / "out").mkdir(exist_ok=True)
    p = tmp_path / "out" / "DRILL-CONFIG.json"
    p.write_text(json.dumps(cfg), encoding="utf-8", newline="\n")
    return p


@pytest.mark.parametrize("lane,over,match", [
    ("C", {}, "lane B only"), ("R", {}, "lane B only"), ("P", {}, "lane B only"),
    ("B", {"trees": {"baseline": "C:/t/iso/cand-r30n/backend", "candidate": "C:/t/iso/cand-r30n/backend"}}, "frozen-r13/backend only"),
    ("B", {"mode": "live"}, "dry mode only"),
    ("B", {"ledger": {"path": "C:/t/r2x/ledger/r2x-ledger.sqlite", "scope": "x"}}, "never consults or writes \\['ledger'\\]"),
    ("B", {"store": "C:/t/r2x/r42-sandbox/x/capture.sqlite"}, "never consults or writes \\['store'\\]"),
    ("B", {"allowance": "C:/t/r2x/r42-sandbox/x/allowance.sqlite"}, "never consults or writes \\['allowance'\\]"),
    ("B", {"run_key": "k"}, "never consults or writes \\['run_key'\\]"),
    ("B", {"declaration_path": "C:/x/DECLARATION.json"}, "declaration_path"),
    ("B", {"dry_inject": [{"kind": "usage", "lane": "B", "calls": [1]}]}, "dry_inject"),
    ("B", {"run_folder": "C:/t/r2x/r42-sandbox/r32-v4"}, "r32-drill-<stamp>"),
    ("B", {"run_set": [{"pool_id": "F037", "doc_key": "x", "ep": "1"}]}, "takes exactly"),
])
def test_a_direct_lane_invocation_with_a_bad_drill_configuration_is_refused_before_the_application_is_imported(tmp_path, lane, over, match):
    cp = _lane_cfg(tmp_path, **over)
    tree = RN.TREES["candidate" if lane != "B" else "baseline"]
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_")} | {"AI_ENABLED": "false"}
    r = subprocess.run([RN.PY, str(RN.HERE / "lane_r32.py"), lane, str(cp)], cwd=tree, env=env, capture_output=True, text=True)
    assert r.returncode != 0 and f"[lane {lane} drill]" in r.stderr, r.stderr[-1500:]
    import re
    assert re.search(match, r.stderr), r.stderr[-1500:]
    assert not (tmp_path / "out" / f"LANE-{lane}.json").exists() and not (tmp_path / "r32-drill-direct").exists()


def test_without_the_drill_the_dry_cohort_rule_is_unchanged(tmp_path):
    """No 'drill' key: a dry lane with reader 'application' on a cohort document still fails the cohort assertion."""
    T = _truth()
    tp = tmp_path / "TRUTH.json"
    tp.write_text(PF.truth_text(T), encoding="utf-8", newline="\n")
    cp = _lane_cfg(tmp_path, drill=None, truth=str(tp))
    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_")}
    r = subprocess.run([RN.PY, str(RN.HERE / "lane_r32.py"), "B", str(cp)], cwd=RN.TREES["baseline"], env=env, capture_output=True, text=True)
    assert r.returncode != 0 and "dry mode never runs a reader on a cohort document" in r.stderr, r.stderr[-1500:]


def test_static_the_other_dry_rules_and_the_single_application_entry_are_unchanged():
    src = (RN.HERE / "runner_r32.py").read_text(encoding="utf-8")
    assert '"reader": "application" if (live or synthetic is not None) else "none"' in src, "reader 'none' over the real cohort in every other dry mode"
    assert 'raise Refused("refused: a synthetic drill holds only SYN* documents of EP-990001")' in src
    lane = (RN.HERE / "lane_r32.py").read_text(encoding="utf-8")
    assert 'assert not cohort, f"dry mode never runs a reader on a cohort document: {cohort[:5]}"' in lane
    ins = RP.lane_installs()
    assert [e["call"] for e in ins["entries"]["B"]].count("document_processing.run") == 1, "the drill uses the lane's one application entry"
    i_install = lane.index("prov.set_provider(DRILL_GLOBAL)")
    assert i_install < lane.index("from app.core.config import get_settings"), "the refusing provider precedes every other application import"
    assert lane.index("from app.ai import provider as prov  # noqa: E402   (the drill's first application import)") < i_install
    assert RP.global_resolution(ins)["B"]["installed_before_every_application_entry"]


# ---- (b) ONE real drill over F009, F020, F030 ---------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def drill(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("drill45")
    led_before = RN.ledger_state()
    stamp = _stamp()
    rc = RN.main(_args(tmp, _spec(tmp), stamp))
    folder = RN.SANDBOX_BASE / f"{DR.FOLDER_PREFIX}{stamp}"
    out = folder / "out"
    j = lambda n: json.loads((out / n).read_text(encoding="utf-8"))  # noqa: E731
    return {"rc": rc, "folder": folder, "lane": j("LANE-B.json"), "trace": j("DRILL-TRACE.json"), "report": j("DRILL-REPORT.json"),
            "rows": j("rows-B.json"), "led_before": led_before, "led_after": RN.ledger_state()}


def test_the_drill_ran_in_its_own_folder_with_no_run_state_allowance_store_or_authorization(drill):
    f = drill["folder"]
    assert drill["rc"] == 0 and f.name.startswith("r32-drill-") and not DR._LIVE_RUN.search(f.name)
    names = {p.name for p in f.rglob("*")}
    for n in ("RUN-STATE.json", "allowance.sqlite", "capture.sqlite", "WRITER.lock", "FAKE-LEDGER.sqlite", "CONTRACT-BREACH.json",
              "IDENTITY-INVALID.json", "PROVIDER-IDENTITY.json", "CLI-VERSIONS.jsonl"):
        assert n not in names, n
    assert not (f / DG.CONSUMED_DIR).exists() and not any("authorization" in n.lower() for n in names)
    assert set(p.name for p in f.iterdir()) == {"out", "B"}


def test_zero_requests_and_the_ledger_unchanged(drill):
    lane, rep = drill["lane"], drill["report"]
    assert lane["model_requests"] == 0 and lane["dry_stub_calls"] == 0 and lane["live_provider_attempts_blocked"] == []
    assert lane["global_provider"]["requests_refused"] == 0 and lane["global_provider"]["still_installed_at_end"]
    assert lane["global_provider"]["at_end"] == "RefusingGlobalProvider" and lane["violations"] == []
    assert lane["global_provider"]["installed"]["ai_enabled_setting"] is False
    assert set(lane["global_provider"]["installed"]["application_modules_at_installation"]) <= {"app", "app.ai", "app.ai.guard", "app.ai.provider",
                                                                                                "app.core", "app.core.config"}
    assert drill["trace"]["summary"]["provider_complete_calls"] == [] and rep["requests"]["provider_complete_calls_traced"] == 0
    assert drill["led_before"] == drill["led_after"]


def test_the_three_documents_pass_through_the_lanes_own_functions_by_call_trace(drill):
    calls = [c for c in drill["trace"]["calls"] if c["event"] == "call"]
    by = lambda f, fn: [c for c in calls if c["file"] == f and c["function"] == fn]  # noqa: E731
    runs = by("document_processing", "run")
    assert len(runs) == 1 and str(runs[0]["ep"]) == DR.EP and runs[0]["caller"] == "lane_r32:<module>"
    T = _truth()
    rel = {T["documents"][p]["relative_path"].replace("\\", "/"): p for p in DR.ALLOW}
    pid = lambda c: rel[str(c["relative_path"]).replace("\\", "/")]  # noqa: E731
    lane_process = by("lane_r32", "process")
    app_process = by("document_sync", "process")
    assert all(c["caller"] == "document_processing:run" for c in lane_process), "the application calls the lane's hook"
    assert all(c["caller"] == "lane_r32:process" for c in app_process), "the lane's hook calls the application's own process"
    read = {pid(c) for c in lane_process}
    assert read and read <= set(DR.ALLOW) and {pid(c) for c in app_process} == read
    trips = drill["trace"]["tripwire_inputs"]
    after = {p for t in trips if t["when"] == "after_document" for p in t["rows"]}
    assert after == read, "every document the application read was judged by the lane's after_document tripwire"
    finals = [t for t in trips if t["when"] == "final"]
    assert len(finals) == 1 and set(finals[0]["rows"]) == set(DR.ALLOW), "the final tripwire judges all three"
    assert by("lane_r32", "row_dict") and len(by("lane_r32", "b_tripwire")) == len(trips)
    assert all(c["caller"] in ("lane_r32:_after", "lane_r32:<module>") for c in by("lane_r32", "b_tripwire"))
    avail = [c for c in drill["trace"]["calls"] if c["event"] == "return" and c["function"] == "available"]
    assert avail and all("AI_ENABLED=false" in c["returned"] for c in avail), "AI off: no form read can be requested"
    docs = drill["lane"]["documents"]
    for p in set(DR.ALLOW) - read:            # a document not read is visible, never silent (a stop by a critical)
        assert docs[p]["status"] == "INCOMPLETE" and drill["report"]["stop_condition_fired"], docs[p]


def test_the_tripwire_recomputation_equals_the_lanes_and_the_rows_are_the_staged_bytes(drill):
    rep = drill["report"]
    assert rep["tripwire_consistency"]["equal"] and rep["tripwire_consistency"]["lane_entries"] > 0
    for p, v in rep["per_document"].items():
        if v["extracted_present"]:
            assert v["staged_sha_equals_row_sha"], p
    assert rep["criterion"]["result"] in ("PASS", "FAIL", "NOT PASS (incomplete)")
    assert rep["criterion"] == DR.criterion(rep)


# ---- (c) the criterion evaluation -------------------------------------------------------------------------------------------
def _rep(resolved=None, exercised=None, refusing=0, stub=0, blocked=(), traced=0, fired=False):
    per = {p: {"resolved_criticals": (resolved or {}).get(p, []), "exercised": (exercised or {}).get(p, True),
               "unread_reason": None if (exercised or {}).get(p, True) else "UNREAD: needs OCR"} for p in DR.ALLOW}
    return {"per_document": per, "stop_condition_fired": fired,
            "requests": {"refusing_provider_calls": refusing, "dry_stub_calls": stub, "live_provider_attempts_blocked": list(blocked),
                         "provider_complete_calls_traced": traced}}


def test_criterion_pass_fail_and_not_pass():
    assert DR.criterion(_rep())["result"] == "PASS"
    crit = {"F009": [{"pool_id": "F009", "page": "3", "field": "identity", "value": "X", "outcome": "wrong_only", "truth": "Y"}]}
    c = DR.criterion(_rep(resolved=crit, fired=True))
    assert c["result"] == "FAIL" and c["resolved_criticals"] == crit and c["criticals_in_the_three_fields"]
    assert DR.criterion(_rep(resolved={"F030": [{"field": "decision"}]}))["result"] == "FAIL"
    for kw in ({"refusing": 1}, {"stub": 1}, {"blocked": ["ClaudeCodeProvider"]}, {"traced": 1}):
        assert DR.criterion(_rep(**kw))["result"] == "FAIL", kw
    c = DR.criterion(_rep(exercised={"F020": False}))
    assert c["result"] == "NOT PASS (incomplete)" and list(c["not_exercised"]) == ["F020"]
    assert DR.criterion(_rep(exercised={"F020": False}, resolved=crit))["result"] == "FAIL", "a critical outranks an unread document"
