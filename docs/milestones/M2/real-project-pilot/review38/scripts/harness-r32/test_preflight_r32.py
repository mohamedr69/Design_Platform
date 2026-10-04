"""preflight_r32: the live declaration contract 3 (ORCH-08: parent budget, lane allowances, project rolling window, request
bounds and COMPATIBLE application limits, pinned model identity, declared sandbox base) with no silent default; the lane
environment check against the declaration; the ledger-scope check (never creates a scope) and the live ledger
difference check. Temporary declarations and FAKE ledgers only (tmp_path); the real AI ledger is never opened here.
Run: python -m pytest -q test_preflight_r32.py"""
import copy
import hashlib
import json
import types

import pytest

import preflight_r32 as PF
import r32_test_helpers as H

B_SHA, RS_SHA = "1" * 64, "2" * 64
RUN_SET = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json"


def _decl(tmp_path, **over):
    led = tmp_path / "ledger.sqlite"
    if not led.exists():
        H.fake_ledger(led, {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0)})
    return H.live_declaration(tmp_path / "pkg", binding_sha=B_SHA, run_set_sha=RS_SHA, stamp="r38-contract-test", ledger_path=led, **over)


# ---- the declaration contract --------------------------------------------------------------------------------------------
def test_a_complete_declaration_passes_and_gives_the_one_run_folder_under_the_declared_base(tmp_path):
    p, sha, rec = _decl(tmp_path)
    v = PF.validate_declaration(rec, p)
    assert v["run_folder"] == "C:/t/r2x/r38-sandbox/r38-contract-test" and v["sandbox_base"] == "C:/t/r2x/r38-sandbox"
    assert v["caps"] == PF.PLAN_CAPS and v["parent"]["total"] == 556 and v["project_window"] == {"limit": 60, "window_s": 86400}
    assert v["model_identity"]["small"] == "claude-sonnet-5" and v["model_identity"]["standard"] == "claude-opus-5"
    assert v["authorization_path"].endswith("/pkg/OWNER-DISPATCH-AUTHORIZATION.json")
    d, v2 = PF.load_declaration(p, sha, binding_sha=B_SHA, run_set_sha=RS_SHA)
    assert v2 == v
    with pytest.raises(PF.Refused, match="does not bind this binding manifest"):
        PF.load_declaration(p, sha, binding_sha="3" * 64, run_set_sha=RS_SHA)
    with pytest.raises(PF.Refused, match="exact sha256"):
        PF.load_declaration(p, "0" * 64, binding_sha=B_SHA, run_set_sha=RS_SHA)


def test_another_declared_sandbox_base_gives_its_own_run_folder(tmp_path):
    p, sha, rec = _decl(tmp_path, run={"stamp": "s-41", "sandbox_base": "C:/t/r2x/r41-sandbox", "folder": "C:/t/r2x/r41-sandbox/s-41"})
    assert PF.validate_declaration(rec, p)["run_folder"] == "C:/t/r2x/r41-sandbox/s-41"


@pytest.mark.parametrize("key", ["contract", "run", "authorization", "budget", "project_window", "project_request_bounds", "lane_switches",
                                 "provider_env", "model_identity", "ledger"])
def test_every_top_level_key_is_required(tmp_path, key):
    p, sha, rec = _decl(tmp_path, **{key: None})
    with pytest.raises(PF.Refused, match=f"does not bind '{key}'"):
        PF.validate_declaration(rec, p)


def _mut(rec, path, value):
    r = copy.deepcopy(rec)
    cur = r
    for k in path[:-1]:
        cur = cur[k]
    if value is KeyError:
        del cur[path[-1]]
    else:
        cur[path[-1]] = value
    return r


@pytest.mark.parametrize("path,value,match", [
    (("contract",), "r34", "is not contract"),
    (("lane_switches", "P"), KeyError, "must name exactly the lanes"),
    (("lane_switches", "P"), {"AI_EVIDENCE_VARIANT": "EV1"}, "takes no switches"),
    (("lane_switches", "C", "AI_EVIDENCE_VARIANT"), KeyError, "must state AI_EVIDENCE_VARIANT"),
    (("lane_switches", "B", "DATABASE_URL"), "x", "AI_EVIDENCE_\\* names"),
    (("provider_env", "AI_EFFORT"), KeyError, "does not bind \\['AI_EFFORT'\\]"),
    (("provider_env", "AI_MAX_CALLS_PER_PROJECT_PER_DAY"), KeyError, "AI_MAX_CALLS_PER_PROJECT_PER_DAY"),
    (("provider_env", "AI_EVIDENCE_GUARD"), "1", "only AI_\\* provider settings"),
    (("provider_env", "DATABASE_URL"), "sqlite:///x", "only AI_\\* provider settings"),
    (("provider_env", "AI_PROVIDER"), "made-up", "unknown AI_PROVIDER"),
    (("provider_env", "AI_LEDGER_SCOPE"), "another-scope", "differ from the declared ledger"),
    (("ledger", "wrap_provider"), False, "wrap_provider true"),
    (("budget", "lane_allowances", "C"), 300, "not the plan's"),
    (("budget", "lane_allowances", "R"), 41, "not the plan's"),
    (("budget", "parent", "total"), 600, "parent total must be 556"),
    (("budget", "parent", "elapsed_s"), KeyError, "budget.parent must bind exactly"),
    (("budget", "parent", "input_tokens"), 0, "budget.parent must bind exactly"),
    (("project_window", "limit"), 61, "project_window must be"),
    (("project_window", "limit"), "60", "project_window must be"),
    (("project_window", "window_s"), 3600, "project_window must be"),
    (("run", "folder"), "C:/t/r2x/r38-sandbox/another", "run folder must be"),
    (("run", "sandbox_base"), "C:/elsewhere", "run.sandbox_base must be declared"),
    (("run", "sandbox_base"), KeyError, "run.sandbox_base must be declared"),
    (("run", "stamp"), "a/b", "a stamp is"),
    (("authorization", "path"), "C:/elsewhere/OWNER-DISPATCH-AUTHORIZATION.json", "pinned authorization path"),
    (("authorization", "owner_token_sha256"), "not-a-digest", "no owner token digest"),
    (("model_identity", "models", "small"), "sonnet", "full model id, not an alias"),
    (("model_identity", "models", "standard"), "opus", "full model id, not an alias"),
    (("model_identity", "models", "small"), "claude-sonnet-5-1", "differs from model_identity"),
    (("model_identity", "provider"), "claude", "model_identity.provider"),
    (("model_identity", "cli", "path"), "claude", "cli.path must equal AI_CLAUDE_CLI"),
    (("project_request_bounds", "sha256"), "0" * 64, "does not hash to the declared sha256"),
])
def test_a_missing_or_different_value_refuses_live_mode(tmp_path, path, value, match):
    p, sha, rec = _decl(tmp_path)
    with pytest.raises(PF.Refused, match=match):
        PF.validate_declaration(_mut(rec, path, value), p)


def test_an_alias_in_provider_env_is_refused_even_when_model_identity_names_it(tmp_path):
    p, sha, rec = _decl(tmp_path)
    r = _mut(_mut(rec, ("provider_env", "AI_MODEL_SMALL"), "sonnet"), ("model_identity", "models", "small"), "sonnet")
    with pytest.raises(PF.Refused, match="not an alias"):
        PF.validate_declaration(r, p)


# ---- A-09 point 1: compatible limits -------------------------------------------------------------------------------------
@pytest.mark.parametrize("key,value", [("AI_MAX_CALLS_PER_PROJECT_PER_DAY", "60"), ("AI_MAX_CALLS_PER_PROJECT_PER_DAY", "83"),
                                       ("AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY", "60"), ("AI_MAX_CALLS_PER_DOCUMENT", "8"),
                                       ("AI_MAX_ELAPSED_S_PER_JOB", "300")])
def test_an_application_limit_that_could_refuse_before_the_harness_is_refused(tmp_path, key, value):
    p, sha, rec = _decl(tmp_path)
    with pytest.raises(PF.Refused, match="incompatible limits"):
        PF.validate_declaration(_mut(rec, ("provider_env", key), value), p)


def test_the_required_minimum_is_the_largest_application_row_count_and_84_passes(tmp_path):
    b = H.bounds_for()
    assert b["compatible_limits"]["required_minimum"] == {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": 84, "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": 84}
    p, sha, rec = _decl(tmp_path)
    assert PF.validate_declaration(_mut(rec, ("provider_env", "AI_MAX_CALLS_PER_PROJECT_PER_DAY"), "84"), p)


def test_bounds_computed_for_another_window_or_elapsed_bound_are_refused(tmp_path):
    p, sha, rec = _decl(tmp_path)
    for change, match in ((lambda b: b["project_window"].update(limit=30), "another project window"),
                          (lambda b: b.update(elapsed_bound_s=1), "another elapsed bound")):
        b = copy.deepcopy(H.bounds_for())
        change(b)
        bp = tmp_path / "pkg" / "OTHER-BOUNDS.json"
        bp.write_text(json.dumps(b), encoding="utf-8", newline="\n")
        r = _mut(rec, ("project_request_bounds",), {"path": bp.as_posix(), "sha256": hashlib.sha256(bp.read_bytes()).hexdigest()})
        with pytest.raises(PF.Refused, match=match):
            PF.validate_declaration(r, p)


def test_the_live_preflight_recomputes_the_bounds_and_refuses_a_difference(tmp_path):
    p, sha, rec = _decl(tmp_path)
    v = PF.validate_declaration(rec, p)
    T = PF.build_truth()
    rs = PF.load_run_set(RUN_SET, T)
    assert PF.verify_bounds(v, rs, T)["verified"]
    v2 = copy.deepcopy(v)
    v2["bounds"]["projects"]["EP-27331"]["structural_maximum"]["C"] = 48
    with pytest.raises(PF.Refused, match="differs from its recomputation"):
        PF.verify_bounds(v2, rs, T)


def test_the_ledger_scope_must_back_the_parent_budget(tmp_path):
    p, sha, rec = _decl(tmp_path)
    lim = dict(H.TEST_LIMITS, elapsed_s=999)
    r = _mut(_mut(rec, ("ledger", "limits"), lim), ("provider_env", "AI_LEDGER_LIMITS"), json.dumps(lim))
    with pytest.raises(PF.Refused, match="backstop of the parent budget"):
        PF.validate_declaration(r, p)


def test_a_dry_exercise_is_never_a_live_declaration(tmp_path):
    p, sha, rec = _decl(tmp_path, dry_exercise=True)
    with pytest.raises(PF.Refused, match="not a live declaration"):
        PF.validate_declaration(rec, p)


def test_the_sandbox_base_is_a_declared_or_parameterised_value(monkeypatch):
    monkeypatch.delenv(PF.SANDBOX_BASE_ENV, raising=False)
    assert PF.sandbox_base().as_posix() == "C:/t/r2x/r38-sandbox" and PF.DEFAULT_SANDBOX_BASE.as_posix() == "C:/t/r2x/r38-sandbox"
    assert PF.sandbox_base("C:/t/r2x/r34-sandbox").as_posix() == "C:/t/r2x/r34-sandbox"
    monkeypatch.setenv(PF.SANDBOX_BASE_ENV, "C:/t/r2x/r39-sandbox")
    assert PF.sandbox_base().as_posix() == "C:/t/r2x/r39-sandbox"
    for bad in ("C:/t/r2x/sandbox", "D:/t/r2x/r38-sandbox", "C:/t/r2x/r38-sandbox/sub", "C:/Users/x"):
        with pytest.raises(PF.Refused, match="a sandbox base is"):
            PF.sandbox_base(bad)


# ---- RC-5: the lane environment against the declaration -------------------------------------------------------------------
def _settings(env):
    return types.SimpleNamespace(ai_enabled=True, ai_provider=env["AI_PROVIDER"], ai_model_standard=env["AI_MODEL_STANDARD"],
                                 ai_model_small=env["AI_MODEL_SMALL"], ai_effort=env["AI_EFFORT"], ai_timeout_s=float(env["AI_TIMEOUT_S"]),
                                 ai_cli_timeout_s=float(env["AI_CLI_TIMEOUT_S"]), ai_claude_cli=env["AI_CLAUDE_CLI"], ai_ledger_path=env["AI_LEDGER_PATH"],
                                 ai_ledger_scope=env["AI_LEDGER_SCOPE"], ai_ledger_limits=env["AI_LEDGER_LIMITS"],
                                 ai_max_calls_per_project_per_day=int(env["AI_MAX_CALLS_PER_PROJECT_PER_DAY"]),
                                 ai_read_max_calls_per_project_per_day=int(env["AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY"]),
                                 ai_max_calls_per_document=int(env["AI_MAX_CALLS_PER_DOCUMENT"]), ai_max_elapsed_s_per_job=float(env["AI_MAX_ELAPSED_S_PER_JOB"]))


def _environ(rec, lane):
    return {"AI_ENABLED": "true", "PATH": "x", **rec["lane_switches"][lane], **rec["provider_env"]}


def test_the_lane_environment_equal_to_the_declaration_passes(tmp_path):
    p, sha, rec = _decl(tmp_path)
    for lane in ("B", "C", "R", "P"):
        env = _environ(rec, lane)
        out = PF.verify_lane_environment(lane, rec["lane_switches"][lane], rec["provider_env"], env, _settings(rec["provider_env"]), mode="live")
        assert out["switches"] == rec["lane_switches"][lane] and sorted(out["provider_env_verified"]) == sorted(rec["provider_env"])


@pytest.mark.parametrize("change,match", [
    (lambda env, s: env.pop("AI_EVIDENCE_IDGUARD"), "switches differ"),
    (lambda env, s: env.update(AI_EVIDENCE_EXTRA="1"), "switches differ"),
    (lambda env, s: env.update(AI_EVIDENCE_GUARD="0"), "switches differ"),
    (lambda env, s: env.update(AI_EFFORT="low"), "AI_EFFORT in the environment"),
    (lambda env, s: env.pop("AI_CLAUDE_CLI"), "AI_CLAUDE_CLI in the environment"),
    (lambda env, s: env.update(AI_ENABLED="false"), "AI_ENABLED is not true"),
    (lambda env, s: setattr(s, "ai_model_small", "sonnet"), "setting ai_model_small"),
    (lambda env, s: setattr(s, "ai_timeout_s", 61.0), "setting ai_timeout_s"),
    (lambda env, s: setattr(s, "ai_max_calls_per_project_per_day", 60), "setting ai_max_calls_per_project_per_day"),
    (lambda env, s: setattr(s, "ai_ledger_limits", "{}"), "ai_ledger_limits differs"),
])
def test_a_missing_or_different_lane_value_refuses(tmp_path, change, match):
    p, sha, rec = _decl(tmp_path)
    env = _environ(rec, "C")
    s = _settings(rec["provider_env"])
    change(env, s)
    with pytest.raises(PF.Refused, match=match):
        PF.verify_lane_environment("C", rec["lane_switches"]["C"], rec["provider_env"], env, s, mode="live")


def test_no_silent_default_switches_or_provider_environment(tmp_path):
    p, sha, rec = _decl(tmp_path)
    with pytest.raises(PF.Refused, match="no declared switches"):
        PF.verify_lane_environment("C", None, rec["provider_env"], _environ(rec, "C"), _settings(rec["provider_env"]), mode="live")
    with pytest.raises(PF.Refused, match="no declared provider environment"):
        PF.verify_lane_environment("C", rec["lane_switches"]["C"], None, _environ(rec, "C"), _settings(rec["provider_env"]), mode="live")
    dry = PF.verify_lane_environment("B", {"AI_EVIDENCE_VARIANT": "off"}, None, {"AI_EVIDENCE_VARIANT": "off"}, None, mode="dry")
    assert dry["provider_env_verified"] == [], "dry mode checks the (labelled) dry switches only"


# ---- RC-4: the ledger scope and the live ledger difference ---------------------------------------------------------------
def test_the_declared_scope_must_exist_with_exactly_the_declared_limits(tmp_path):
    led = {"path": (tmp_path / "l.sqlite").as_posix(), "scope": H.TEST_SCOPE, "limits": H.TEST_LIMITS}
    with pytest.raises(PF.Refused, match="does not exist"):
        PF.verify_ledger_scope(led)
    assert not (tmp_path / "l.sqlite").exists(), "a missing ledger is never created"
    H.fake_ledger(tmp_path / "l.sqlite", {"other": ({"requests": 10}, None, 3)})
    with pytest.raises(PF.Refused, match="does not exist"):
        PF.verify_ledger_scope(led)
    H.fake_ledger(tmp_path / "l2.sqlite", {H.TEST_SCOPE: ({"requests": 100}, None, 0)})
    with pytest.raises(PF.Refused, match="has limits"):
        PF.verify_ledger_scope(led | {"path": (tmp_path / "l2.sqlite").as_posix()})
    H.fake_ledger(tmp_path / "l3.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, "requests cap passed", 0)})
    with pytest.raises(PF.Refused, match="open breaker"):
        PF.verify_ledger_scope(led | {"path": (tmp_path / "l3.sqlite").as_posix()})
    H.fake_ledger(tmp_path / "l4.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 2)})
    assert PF.verify_ledger_scope(led | {"path": (tmp_path / "l4.sqlite").as_posix()})["entries"] == 2


def test_live_ledger_growth_only_inside_the_declared_scope_and_within_the_parent_total(tmp_path):
    import sqlite3

    p = H.fake_ledger(tmp_path / "l.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0), "other": ({"requests": 9}, None, 4)})
    led = {"path": p.as_posix(), "scope": H.TEST_SCOPE, "limits": H.TEST_LIMITS}
    before = PF.ledger_snapshot(p)
    con = sqlite3.connect(str(p))
    for st in ("settled", "settled", "refused", "cache_hit"):
        con.execute("insert into entries (scope, state) values (?, ?)", (H.TEST_SCOPE, st))
    con.commit()
    ok = PF.ledger_live_check(before, PF.ledger_snapshot(p), led)
    assert ok["ok"] and ok["declared_scope_dispatch_entries_added"] == 2
    con.execute("insert into entries (scope, state) values ('other', 'settled')")
    con.execute("insert into scopes (scope, limits) values ('new-scope', '{}')")
    con.execute("insert into limit_amendments (scope) values (?)", (H.TEST_SCOPE,))
    con.commit()
    con.close()
    bad = PF.ledger_live_check(before, PF.ledger_snapshot(p), led)
    assert not bad["ok"] and any("scopes changed" in x for x in bad["problems"]) and any("'other' changed" in x for x in bad["problems"])
    assert any("limit amendment" in x for x in bad["problems"])
    over = PF.ledger_live_check(before, PF.ledger_snapshot(p), led, total=1)
    assert any("grew by 2 dispatch entries > 1" in x for x in over["problems"])
