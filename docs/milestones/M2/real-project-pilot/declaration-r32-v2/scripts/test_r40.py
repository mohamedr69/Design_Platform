"""ORCH-09 (R40DECL-IMPL): tests of the corrected declaration package declaration-r32-v2 (the frozen declaration, the RUN
procedure in memory, the integer strings, the scope-creation command and its refusals, the cited harness refusals).

Run: <venv python> -B -m pytest -q -p no:cacheprovider test_r40.py   (scripts/run_tests_r40.py writes the junit)
Nothing here writes a RUN file, an authorization file, a token or a scope in the AI ledger: the RUN copy and the
authorization text exist in memory only; the one positive scope creation uses a THROWAWAY SQLite file in pytest's tmp_path,
never the AI ledger (asserted). The AI ledger is opened mode=ro only."""
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_declaration_r40 as BD  # noqa: E402
import create_scope_r40 as CS  # noqa: E402
import r40common as C  # noqa: E402

C.harness_import_path()
import dispatch_guard_r32 as DG  # noqa: E402
import model_identity_r38 as MI  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import project_bounds_r32 as PB  # noqa: E402
import runner_r32 as RN  # noqa: E402
import score_bcr_r32 as S  # noqa: E402

FROZEN = (C.PACKAGE / C.DECLARATION_NAME).read_bytes()
FSHA = hashlib.sha256(FROZEN).hexdigest()
DECL = json.loads(FROZEN.decode("utf-8"))
RUN_PATH = C.PACKAGE / C.RUN_NAME
TEST_TOKEN = "r40-test-token-not-the-owners-" + "x" * 16
TEST_DIGEST = hashlib.sha256(TEST_TOKEN.encode("utf-8")).hexdigest()


def run_copy(digest=TEST_DIGEST) -> bytes:
    return BD.fill_owner_digest(FROZEN, digest)


def auth_for(run_bytes, digest=TEST_DIGEST, nonce="test-nonce-0123456789abcdef", named=None):
    return json.loads(BD.authorization_text(named or hashlib.sha256(run_bytes).hexdigest(), digest, nonce, frozen_sha="f" * 64))


# ---- the frozen declaration --------------------------------------------------------------------------------------------
def test_declaration_hash_recorded_lf_and_canonical():
    assert (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8") == f"{FSHA}  {C.DECLARATION_NAME}\n"
    assert b"\r" not in FROZEN and FROZEN.endswith(b"\n")
    assert C.json_text(DECL).encode("utf-8") == FROZEN, "canonical JSON (sort_keys, indent 1, ensure_ascii False, LF)"


def test_placeholder_exactly_once_and_status_not_authorized():
    assert FROZEN.count(json.dumps(C.TOKEN_PLACEHOLDER).encode()) == 1
    assert DECL["authorization"]["owner_token_sha256"] == C.TOKEN_PLACEHOLDER
    assert DECL["executed"] is False and DECL["budget_approved"] is False and DECL["authorization_status"] == "none; owner decision pending"
    assert DECL["standing_status"] == {"M2": "CHANGES STILL REQUIRED", "M3": "not started"}


def test_frozen_declaration_refused_as_written_by_preflight_and_guard():
    with pytest.raises(PF.Refused, match="binds no owner token digest"):
        PF.validate_declaration(DECL, C.PACKAGE / C.DECLARATION_NAME)
    with pytest.raises(DG.DispatchRefused, match="binds no owner token digest"):
        DG.validate(DECL, C.PACKAGE / C.DECLARATION_NAME, FSHA, {}, None)


def test_in_memory_dummy_digest_copy_passes_contract_4_and_is_never_written():
    mem = json.loads(BD.fill_owner_digest(FROZEN, C.DUMMY_DIGEST).decode("utf-8"))
    v = PF.validate_declaration(mem, RUN_PATH)
    assert v["contract"] == "r39-live-contract-4" and v["run_folder"] == "C:/t/r2x/r40-sandbox/r32-v2"
    assert v["caps"] == {"B": 240, "C": 240, "R": 40, "P": 36} and v["parent"]["total"] == 556
    assert not RUN_PATH.exists()
    for p in C.PACKAGE.rglob("*"):
        if p.is_file():
            assert C.DUMMY_DIGEST.encode() not in p.read_bytes(), p


def test_binds_review39_and_the_frozen_inputs():
    assert DECL["binding_manifest_sha256"] == C.BINDING_SHA == C.sha256_file(C.BINDING)
    assert DECL["run_set_sha256"] == C.RUN_SET_SHA == C.sha256_file(C.RUN_SET)
    assert DECL["project_request_bounds"] == {"path": C.BOUNDS.as_posix(), "sha256": C.BOUNDS_SHA}
    assert DECL["harness"]["package_manifest"]["sha256"] == C.REVIEW39_MANIFEST_SHA
    assert DECL["resume_detail"]["resume_invocations"]["sha256"] == "9791fa897587fd83e1a087e302487ce245470a41c32f9aa10b48c1211e7dcf6b"
    assert DECL["harness"]["contracts"]["visibility_result"]["sha256"] == "1811e4561ae2cd157aeb9e7b599ac094b0141743f8113fea0a0944c88638192c"
    assert DECL["reference_set"]["labels"]["sha256"] == "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"
    assert DECL["run_set"]["truth"]["sha256"] == C.TRUTH_SHA


# ---- the RUN procedure (in memory) ------------------------------------------------------------------------------------
def test_fill_owner_digest_replaces_only_the_placeholder():
    run = run_copy()
    a, b = json.loads(FROZEN), json.loads(run)
    assert b["authorization"]["owner_token_sha256"] == TEST_DIGEST
    a["authorization"]["owner_token_sha256"] = TEST_DIGEST
    assert a == b and len(run) == len(FROZEN) - len(C.TOKEN_PLACEHOLDER) + 64


@pytest.mark.parametrize("bad", ["", "ABC", "A" * 64, "0" * 63, "g" * 64, C.TOKEN_PLACEHOLDER])
def test_fill_owner_digest_refuses_a_malformed_digest(bad):
    with pytest.raises(ValueError):
        BD.fill_owner_digest(FROZEN, bad)


def test_fill_owner_digest_refuses_zero_or_two_placeholders():
    with pytest.raises(ValueError, match="exactly once"):
        BD.fill_owner_digest(run_copy(), TEST_DIGEST)
    with pytest.raises(ValueError, match="exactly once"):
        BD.fill_owner_digest(FROZEN + json.dumps(C.TOKEN_PLACEHOLDER).encode(), TEST_DIGEST)


def test_fill_owner_digest_equals_review37s_function_carried_by_hash():
    """The r40 function is a re-implementation; on the same input it gives byte-identical output to the frozen review37 one."""
    d = C.SUPERSEDED / "scripts"
    assert C.sha256_file(d / "build_declaration_r37.py") == C.BUILD_R37_SHA
    assert C.sha256_file(d / "r37common.py") == C.R37COMMON_SHA and C.sha256_file(d / "estimates_r37.py") == C.ESTIMATES_R37_SHA
    sys.path.insert(0, str(d))
    try:
        spec = importlib.util.spec_from_file_location("build_declaration_r37", d / "build_declaration_r37.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.path.remove(str(d))
    assert m.C.TOKEN_PLACEHOLDER == C.TOKEN_PLACEHOLDER
    for digest in (TEST_DIGEST, C.DUMMY_DIGEST, "a" * 64):
        assert m.fill_owner_digest(FROZEN, digest) == BD.fill_owner_digest(FROZEN, digest)


def test_verify_run_file_refuses_without_a_run_file():
    assert not RUN_PATH.exists()
    with pytest.raises(C.PacketMismatch, match="no RUN file"):
        BD.verify_run_file(TEST_DIGEST, hashlib.sha256(run_copy()).hexdigest())


def test_authorization_text_names_the_run_hash_never_the_frozen_hash():
    run = run_copy()
    rsha = hashlib.sha256(run).hexdigest()
    txt = BD.authorization_text(rsha, TEST_DIGEST, "n" * 16, frozen_sha=FSHA)
    assert json.loads(txt) == {"authorized_by": "owner", "declaration_sha256": rsha, "nonce": "n" * 16, "owner_token_sha256": TEST_DIGEST}
    with pytest.raises(ValueError, match="never the frozen hash"):
        BD.authorization_text(FSHA, TEST_DIGEST, "n" * 16, frozen_sha=FSHA)
    for bad in ("short", "x" * 129, "bad nonce with spaces!!"):
        with pytest.raises(ValueError):
            BD.authorization_text(rsha, TEST_DIGEST, bad, frozen_sha=FSHA)


def test_the_guard_accepts_the_in_memory_run_copy_only_with_its_own_authorization_and_token():
    run = run_copy()
    rsha = hashlib.sha256(run).hexdigest()
    rd = json.loads(run)
    g = DG.validate(rd, RUN_PATH, rsha, auth_for(run), TEST_TOKEN)
    assert re.fullmatch(r"[0-9a-f]{64}", g["nonce_sha256"])
    with pytest.raises(DG.DispatchRefused, match="names declaration"):
        DG.validate(rd, RUN_PATH, rsha, auth_for(run, named=FSHA), TEST_TOKEN)
    with pytest.raises(DG.DispatchRefused, match="does not match the bound digest"):
        DG.validate(rd, RUN_PATH, rsha, auth_for(run), "another token")
    with pytest.raises(DG.DispatchRefused, match="was not presented"):
        DG.validate(rd, RUN_PATH, rsha, auth_for(run), None)


# ---- values -------------------------------------------------------------------------------------------------------------
def test_integer_strings_for_every_count_and_time_limit():
    env = DECL["provider_env"]
    assert BD.integer_string_problems(env) == []
    assert (env["AI_MAX_CALLS_PER_PROJECT_PER_DAY"], env["AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY"], env["AI_MAX_CALLS_PER_DOCUMENT"],
            env["AI_MAX_ELAPSED_S_PER_JOB"]) == ("96", "600", "12", "120")
    for k, v in env.items():
        if re.fullmatch(r"[0-9.]+", v):
            assert "." not in v or k == "AI_MAX_COST_PER_JOB", (k, v)
    assert BD.integer_string_problems(dict(env, AI_MAX_CALLS_PER_DOCUMENT="12.0")) == ["AI_MAX_CALLS_PER_DOCUMENT = '12.0' is not an integer string"]


def test_compatible_limits_and_their_margin():
    bounds = json.loads(C.BOUNDS.read_text(encoding="utf-8"))
    assert PB.check_compatible(DECL["provider_env"], bounds) == []
    req = bounds["compatible_limits"]["required_minimum"]
    assert req == {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": 84, "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": 84}
    lim = DECL["application_ai_limits"]["compatible_limits"]
    assert lim["AI_MAX_CALLS_PER_PROJECT_PER_DAY"]["margin"] == 12 and lim["AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY"]["margin"] == 516


def test_the_declared_arms_equal_the_runner_dry_values():
    assert RN.DRY_LANE_SWITCHES == DECL["lane_switches"] and RN.CAPS == DECL["budget"]["lane_allowances"]
    assert RN.PARENT == DECL["budget"]["parent"] and RN.WINDOW == DECL["project_window"]
    assert PF.APPLICATION_ENV == DECL["application_env"] == {"DRAWINGS_AI_REVIEW_ENABLED": "false"}
    assert PF.task_kinds_for(DECL["lane_switches"]) == DECL["lane_task_kinds"]
    assert DECL["resume_policy"] == "full" and DECL["ledger"]["wrap_provider"] is True
    sup = json.loads((C.SUPERSEDED / "FRESH-VALIDATION-DECLARATION-R32.json").read_text(encoding="utf-8"))
    assert DECL["lane_switches"] == sup["lane_switches"] and DECL["budget"]["lane_allowances"] == sup["caps"]
    assert DECL["ledger"]["limits"] == sup["ledger"]["limits"] and DECL["ledger"]["scope"] == C.SCOPE != sup["ledger"]["scope"]


def test_model_identity_pins_full_ids_and_the_exact_cli_version_line():
    pins = MI.validate_pins(DECL["model_identity"], DECL["provider_env"])
    assert (pins["small"], pins["standard"], pins["provider"]) == ("claude-sonnet-5", "claude-opus-5", "claude-code")
    assert pins["cli_version"] == "2.1.263 (Claude Code)" and pins["cli_path"] == "claude"
    det = DECL["model_identity_detail"]
    assert det["served_model_identity"] == "UNRESOLVED" and len(det["runtime_check_limits"]) == 2
    assert det["cli"]["file_sha256"] == C.CLI_EXE_SHA


def test_the_gate_is_c_ge_b_only_and_named_a_change_from_plan_v2():
    assert DECL["decision_coverage_gate"] == S.DECISION_COVERAGE_GATE == "C_GE_B_ONLY"
    det = DECL["decision_coverage_gate_detail"]
    assert "A CHANGE FROM PLAN V2" in det["statement"] and "NOT an unchanged gate" in det["statement"]
    assert "CHANGED from plan v2" in DECL["gates"]["decision_coverage"] and "NOT an unchanged gate" in DECL["gates"]["decision_coverage"]
    with pytest.raises(ValueError):
        S.refuse_r_in_eligibility("C_GE_B_AND_C_GE_R")
    sup = json.loads((C.SUPERSEDED / "FRESH-VALIDATION-DECLARATION-R32.json").read_text(encoding="utf-8"))
    for k in ("per_field", "safety", "request_gate", "concentration", "candidate_outcome", "outcomes", "default_selection"):
        assert DECL["gates"][k] == sup["gates"][k], k


def test_the_retry_rule_is_named_a_change_and_the_review39_rules_replace_review34s():
    rr = DECL["retry_rule"]
    assert rr["change_from_plan_v2"] is True and "CHANGE FROM PLAN V2 section 4" in rr["statement"]
    v = rr["plan_v2_section_4_verbatim"]
    lines = pathlib.Path(v["source"]).read_text(encoding="utf-8").split("\n")
    assert C.sha256_file(v["source"]) == v["sha256"] and lines[v["line"] - 1] == v["text"] and "never re-sends a bound fingerprint" in v["text"]
    sr = DECL["stop_rules"]
    assert "verbatim_review34_resume_rules" not in sr
    src = pathlib.Path(sr["verbatim_review39_resume_rules"]["section_5"]["source"])
    text = src.read_text(encoding="utf-8")
    assert C.sha256_file(src) == sr["verbatim_review39_resume_rules"]["section_5"]["sha256"]
    for sec in ("section_4", "section_5", "section_6", "section_13"):
        assert "\n".join(sr["verbatim_review39_resume_rules"][sec]["text"]) in text, sec
    assert set(sr["terminal_states"]) >= {"INCOMPLETE", "DEFERRED", "INVALID", "CLOSED"}


def test_verification_40_items_are_stated():
    assert "no_trigger" in DECL["unread_page_rule"]["no_trigger_exclusion"] and len(DECL["unread_page_rule"]["unguarded_corners"]) == 2
    pp = DECL["probe_population"]
    assert pp["cap"] == 36 and pp["seed"] == "m2-r30-variation-2026-10-02" and "FIRST RUN" in pp["definition"] and "3 of" in pp["example"]
    rp = DECL["request_path_coverage"]
    assert len(rp["owner_options"]) == 2 and "lane B only" in rp["corrected_claim"] and rp["residual_risk"]
    assert DECL["harness"]["review39_snapshot_before"]["taken_utc"] == "2026-10-04T09:55:49+00:00"
    assert set(DECL["verification40_items"]) == {"R40-04", "R40-08", "R40-10", "R40-12", "R40-13", "R40-15", "R40-16", "R40-19", "R40-20"}
    for name, rec in DECL["request_path_coverage"]["proof_bound"].items():
        if "package_path" in rec:
            assert C.sha256_file(C.PACKAGE / rec["package_path"]) == rec["sha256"], name
    for name, rec in DECL["harness"]["review39_work_records"].items():
        if isinstance(rec, dict):
            assert C.sha256_file(C.PACKAGE / rec["package_path"]) == rec["sha256"], name


def test_the_declared_run_folder_keeps_every_application_path_below_260_characters():
    truth = json.loads(C.TRUTH.read_text(encoding="utf-8"))
    rs = json.loads(C.RUN_SET.read_text(encoding="utf-8"))
    longest = max(len(f"{DECL['run']['folder']}/inv-99/B/s/EP-{truth['documents'][d['pool_id']]['ep']}/{truth['documents'][d['pool_id']]['relative_path']}")
                  for d in rs["documents"])
    assert longest <= 256 < 260


# ---- the scope-creation command ---------------------------------------------------------------------------------------
def test_scope_preview_creates_nothing():
    before = C.ledger_counts()
    pv = CS.preview()
    after = C.ledger_counts()
    assert pv["ledger_unchanged"] and before == after and {k: after[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED
    assert pv["scope"] == C.SCOPE and pv["limits"] == DECL["ledger"]["limits"] and pv["preconditions_now"]["8 no scope of that name"]["exists"] is False
    assert C.SCOPE not in C.ledger_state()["scope_names"]


def test_scope_status_is_read_only_and_reports_no_scope_yet():
    before = C.ledger_counts()
    st = CS.status()
    assert st["exists"] is False and st["limits"] is None and st["scope"] == C.SCOPE
    assert st["ledger_totals"] == {"entries": 483, "scopes": 17, "limit_amendments": 0} and C.ledger_counts() == before


def test_scope_create_refuses_without_the_authorization_file():
    assert not (C.PACKAGE / C.AUTH_NAME).exists()
    before = C.ledger_counts()
    env = {k: v for k, v in os.environ.items() if k != C.TOKEN_ENV} | {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([C.PY, "-B", str(HERE / "create_scope_r40.py"), "create", "--frozen-sha", FSHA, "--run-sha", hashlib.sha256(run_copy()).hexdigest()],
                       cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 3 and "no owner dispatch authorization" in json.loads(r.stdout)["refused"]
    assert C.ledger_counts() == before


def _check(**over):
    run = over.pop("run", run_copy())
    kw = dict(frozen=FROZEN, frozen_sha_given=FSHA, run_bytes=run, run_sha_given=hashlib.sha256(run).hexdigest(), auth=auth_for(run), token=TEST_TOKEN,
              run_path=RUN_PATH, run_folder=C.SANDBOX_BASE / "r40d-test-absent-run-folder", verify_bound=False)
    kw.update(over)
    return CS.check_create(**kw)


def test_scope_create_refuses_a_wrong_declaration_hash():
    with pytest.raises(CS.ScopeRefused, match="frozen declaration hash differs"):
        _check(frozen_sha_given="0" * 64)
    with pytest.raises(CS.ScopeRefused, match="hashes to"):
        _check(run_sha_given="1" * 64)
    with pytest.raises(CS.ScopeRefused, match="is the FROZEN hash"):
        _check(run_sha_given=FSHA)
    with pytest.raises(CS.ScopeRefused, match="names the FROZEN hash"):
        _check(auth=auth_for(run_copy(), named=FSHA))


def test_scope_create_refuses_a_tampered_run_file_a_wrong_token_and_no_run_file():
    run = run_copy()
    tampered = run.replace(b'"stamp": "r32-v2"', b'"stamp": "r32-v3"')
    assert tampered != run
    with pytest.raises(CS.ScopeRefused, match="only the digest filled in"):
        _check(run=tampered, auth=auth_for(tampered))
    with pytest.raises(CS.ScopeRefused, match="does not match the bound digest"):
        _check(token="not the token")
    with pytest.raises(CS.ScopeRefused, match="not presented"):
        _check(token=None)
    with pytest.raises(CS.ScopeRefused, match="no RUN declaration"):
        _check(run_bytes=None)


def test_scope_create_refuses_when_the_run_folder_exists(tmp_path):
    with pytest.raises(CS.ScopeRefused, match="run folder"):
        _check(run_folder=tmp_path)


def test_scope_create_on_a_throwaway_ledger_creates_exactly_the_declared_scope(tmp_path):
    """The positive path, on a THROWAWAY SQLite file in tmp_path (never the AI ledger): the application's Ledger creates the
    scope with exactly the declared limits, a closed breaker and no entry; preflight_r32.verify_ledger_scope accepts it; a
    second creation is refused (the scope is created once)."""
    ai_before = C.ledger_counts()
    sys.path.insert(0, str(C.CANDIDATE_BACKEND))
    from app.ai.ledger import Ledger, Limits
    tl = tmp_path / "throwaway-ledger.sqlite"
    Ledger(str(tl), "some-other-scope", Limits(requests=1))
    ok = _check(verify_bound=True)
    assert pathlib.Path(tl).resolve() != C.AI_LEDGER.resolve()
    res = CS.create_scope(ok, ledger_path=tl)
    assert res["created"] and res["limits"] == DECL["ledger"]["limits"] and res["breaker"] is None and res["entries"] == 0
    assert res["totals_after"]["scopes"] == res["totals_before"]["scopes"] + 1 == 2
    PF.verify_ledger_scope({**DECL["ledger"], "path": str(tl)})
    with pytest.raises(CS.ScopeRefused, match="already exists"):
        CS.create_scope(ok, ledger_path=tl)
    assert C.ledger_counts() == ai_before and C.SCOPE not in C.ledger_state()["scope_names"]


# ---- the cited refusals of the bound harness ----------------------------------------------------------------------------
CITED = {"test_runner_r32": ["test_live_mode_with_a_complete_declaration_and_no_authorization_refuses_before_any_folder_exists",
                             "test_a_direct_live_lane_invocation_is_refused_by_the_guard_without_authorization",
                             "test_live_mode_refuses_a_missing_or_different_ledger_scope", "test_resumable_rules"],
         "test_dispatch_guard_r32": ["test_no_authorization_file_exists_and_the_guard_refuses_without_one",
                                     "test_the_guarded_provider_never_builds_the_real_provider_when_refused",
                                     "test_consumed_nonce_is_refused_and_lanes_need_their_own_invocation"]}


@pytest.mark.parametrize("module", sorted(CITED))
def test_the_runbooks_cited_harness_refusal_tests_exist_and_passed_in_review39(module):
    src = (C.HARNESS / f"{module}.py").read_text(encoding="utf-8")
    root = ET.parse(C.REVIEW39 / "tests" / f"{module}.xml").getroot()
    cases = {c.get("name"): c for c in root.iter("testcase")}
    for name in CITED[module]:
        assert f"def {name}(" in src, name
        hits = [c for n, c in cases.items() if n == name or n.startswith(name + "[")]
        assert hits and all(not list(c) for c in hits), f"{name}: not passed in review39's junit"


def test_no_authorization_run_or_token_file_in_this_package_or_sandbox():
    assert C.forbidden_files((C.PACKAGE, C.SANDBOX_BASE, C.WORK)) == []
    assert C.TOKEN_ENV not in os.environ


def test_the_diff_covers_every_top_level_key():
    d = json.loads((C.PACKAGE / "DECLARATION-DIFF.json").read_text(encoding="utf-8"))
    sup = json.loads((C.SUPERSEDED / "FRESH-VALIDATION-DECLARATION-R32.json").read_text(encoding="utf-8"))
    assert set(d["top_level"]) == set(sup) | set(DECL)
    assert d["superseded"]["sha256"] == C.SUPERSEDED_SHA and d["corrected"]["sha256"] == FSHA
    assert {k for k, v in d["top_level"].items() if v["status"] == "removed"} == {"caps", "caps_detail", "project_day_limit", "project_day_limit_detail"}
