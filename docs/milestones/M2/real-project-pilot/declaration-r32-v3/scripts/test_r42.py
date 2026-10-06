"""ORCH-10 (R42PORT-IMPL): tests of the v3 declaration package declaration-r32-v3 (the frozen declaration and its contract-5
values, the RUN procedure in memory, both authorization forms, the scope-creation command and its refusals including the
C1 disk floor and the CLI file, the diff's protected values, the cited review42 tests).

Run: <bound python> -B -m pytest -q -p no:cacheprovider test_r42.py   (run_tests_r42pkg.py writes the junit; R42 audit guard)
Nothing here writes a RUN file, an authorization file, a token or a scope in the AI ledger: the RUN copy and the
authorization text exist in memory only; the one positive scope creation uses a THROWAWAY SQLite file in pytest's tmp_path,
never the AI ledger (asserted). The AI ledger is opened mode=ro only."""
import hashlib
import json
import pathlib
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_declaration_r42 as BD  # noqa: E402
import create_scope_r42 as CSC  # noqa: E402
import r42common as C  # noqa: E402

sys.path.insert(0, str(C.HARNESS42))
import dispatch_guard_r32 as DG  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import runner_r32 as RN  # noqa: E402
import score_bcr_r32 as S  # noqa: E402

FROZEN = (C.PACKAGE / C.DECLARATION_NAME).read_bytes()
FSHA = hashlib.sha256(FROZEN).hexdigest()
DECL = json.loads(FROZEN.decode("utf-8"))
V2 = json.loads((C.V2 / C.V2_NAME).read_text(encoding="utf-8"))
RUN_PATH = C.PACKAGE / C.RUN_NAME
TEST_TOKEN = "r42-test-token-not-the-owners-" + "x" * 16
TEST_DIGEST = hashlib.sha256(TEST_TOKEN.encode("utf-8")).hexdigest()
Disk = namedtuple("Disk", "total used free")


def run_copy(digest=TEST_DIGEST) -> bytes:
    return BD.fill_owner_digest(FROZEN, digest)


def auth_for(run_bytes, digest=TEST_DIGEST, nonces=("test-nonce-0123456789abcdef",), multi=False, named=None):
    return json.loads(BD.authorization_text(named or hashlib.sha256(run_bytes).hexdigest(), digest, list(nonces), frozen_sha=FSHA, multi=multi))


# ---- the frozen declaration --------------------------------------------------------------------------------------------------
def test_declaration_hash_recorded_lf_and_canonical():
    assert (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8") == f"{FSHA}  {C.DECLARATION_NAME}\n"
    assert b"\r" not in FROZEN and FROZEN.endswith(b"\n") and C.json_text(DECL).encode("utf-8") == FROZEN


def test_placeholder_exactly_once_and_status_not_authorized():
    assert FROZEN.count(json.dumps(C.TOKEN_PLACEHOLDER).encode()) == 1 and DECL["authorization"]["owner_token_sha256"] == C.TOKEN_PLACEHOLDER
    assert DECL["executed"] is False and DECL["budget_approved"] is False and DECL["authorization_status"] == "none; owner decision pending"
    assert DECL["standing_status"] == {"M2": "CHANGES STILL REQUIRED", "M3": "not started"}


def test_frozen_declaration_refused_as_written_and_in_memory_copy_passes_contract_5():
    with pytest.raises(PF.Refused, match="binds no owner token digest"):
        PF.validate_declaration(DECL, C.PACKAGE / C.DECLARATION_NAME)
    v = PF.validate_declaration(json.loads(run_copy(C.DUMMY_DIGEST)), RUN_PATH)
    assert v["contract"] == "r42-live-contract-5" and v["global_provider"]["C"] == "refusing" and v["resume_authorization_max"] == 3
    assert not RUN_PATH.exists()


def test_no_desktop_path_and_every_bound_file_rehashes():
    assert C.DESKTOP_EP not in FROZEN.decode("utf-8")
    nodes = BD.bound_nodes(DECL)
    assert len(nodes) > 150 and all(C.sha256_file(p) == s for _jp, p, s in nodes)


def test_supersedes_v2_and_binds_review42():
    assert DECL["supersedes"]["declaration"] == {"path": (C.V2 / C.V2_NAME).as_posix(), "sha256": C.V2_SHA}
    assert DECL["binding_manifest_sha256"] == C.sha256_file(C.BINDING42) and DECL["harness"]["package"] == "PILOT/review42/"
    assert all(m["path"].startswith(C.HARNESS42.as_posix() + "/") for m in DECL["harness"]["modules"].values())


def test_every_number_of_v2_is_carried():
    for k in ("budget", "project_window", "lane_switches", "lane_task_kinds", "application_env", "decision_coverage_gate", "resume_policy", "gates",
              "thresholds_verbatim", "concentration_on_proposal", "estimated_usage", "token_thresholds", "primary_outcomes", "reference_set",
              "run_set_sha256"):
        assert json.loads(json.dumps(V2[k]).replace(C.DESKTOP_EP, C.MERGED_EP)) == DECL[k], k
    for k in ("AI_MAX_CALLS_PER_PROJECT_PER_DAY", "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY", "AI_MAX_CALLS_PER_DOCUMENT", "AI_MAX_ELAPSED_S_PER_JOB",
              "AI_LEDGER_LIMITS", "AI_MODEL_SMALL", "AI_MODEL_STANDARD", "AI_PROVIDER", "AI_EFFORT"):
        assert DECL["provider_env"][k] == V2["provider_env"][k], k
    assert DECL["provider_env"]["AI_MAX_CALLS_PER_PROJECT_PER_DAY"] == "96" and DECL["provider_env"]["AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY"] == "600"
    assert DECL["ledger"]["limits"] == {"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000,
                                        "per_request_output": 20000, "requests": 556}
    assert DECL["budget"]["lane_allowances"] == {"B": 240, "C": 240, "R": 40, "P": 36} and DECL["project_window"] == {"limit": 60, "window_s": 86400}
    assert DECL["decision_coverage_gate"] == S.DECISION_COVERAGE_GATE == "C_GE_B_ONLY"


def test_the_diff_shows_every_protected_value_unchanged():
    diff = json.loads((C.PACKAGE / "DECLARATION-DIFF.json").read_text(encoding="utf-8"))
    assert diff["v3"]["sha256"] == FSHA and diff["v2"]["sha256"] == C.V2_SHA and diff["protected_all_ok"] and diff["ok"]
    assert not diff["unexplained_top_level_changes"] and not diff["desktop_prefix_left_in_v3"]


def test_contract_5_values():
    assert DECL["interpreter"]["path"] == C.PY and DECL["interpreter"]["sha256"] == C.sha256_file(C.PY)
    assert DECL["disk_precondition"] == {"path": "C:/", "min_free_bytes": 2 * 1024 ** 3}
    assert DECL["isolation"] == PF.isolation_binding() and DECL["isolation"]["allowed_under_forbidden"]["harness"] == C.HARNESS42.as_posix()
    assert DECL["global_provider"] == {"B": "harness_chain", "C": "refusing", "R": "refusing", "P": "refusing"}
    assert DECL["resume_authorization"]["max_invocations_per_file"] == 3 and DECL["resume_authorization"]["status"].startswith("PROPOSAL")


def test_the_cli_is_pinned_by_absolute_path_hash_and_line():
    cli = DECL["model_identity"]["cli"]
    assert cli == {"path": C.CLI_EXE.as_posix(), "sha256": C.CLI_EXE_SHA, "version": "2.1.263 (Claude Code)"}
    assert DECL["provider_env"]["AI_CLAUDE_CLI"] == C.CLI_EXE.as_posix() and "2.1.289" not in cli["path"]
    assert PF.verify_cli({"cli_path": cli["path"], "cli_sha256": cli["sha256"]})["executed"] is False


def test_stamp_run_folder_and_scope_are_v3_and_absent():
    assert DECL["run"]["stamp"] == "r32-v3" and DECL["run"]["folder"] == "C:/t/r2x/r42-sandbox/r32-v3" and not C.RUN_FOLDER.exists()
    assert DECL["ledger"]["scope"] == C.SCOPE == DECL["provider_env"]["AI_LEDGER_SCOPE"] == "m2-fresh-validation-r32-v3-2026-10-06"
    assert C.SCOPE not in C.ledger_state()["scope_names"]


def test_r41_statements_corrected():
    dis = "\n".join(DECL["disclosures"])
    assert "NO runbook step checks integer strings" in dis and "the runbook's pre-invocation check refuses non-integer strings" not in dis
    assert "ONE single 24-document dry run AND six per-project dry runs" in dis
    assert set(DECL["verification41_items"]) >= {"R41-09", "R41-10", "R41-11", "R41-12", "R41-13", "R41-14"}
    assert DECL["verification41_items"]["R41-14"]["bound_by_hash"] == {p: {"path": p, "sha256": w} for p, w in C.R40_WORK_RECORDS.items()}


# ---- the RUN procedure and the authorization forms ---------------------------------------------------------------------------------
def test_fill_owner_digest_replaces_only_the_placeholder():
    run = run_copy()
    assert run != FROZEN and run.replace(json.dumps(TEST_DIGEST).encode(), json.dumps(C.TOKEN_PLACEHOLDER).encode()) == FROZEN


@pytest.mark.parametrize("bad", ["", "ABC", "A" * 64, "0" * 63, "g" * 64, C.TOKEN_PLACEHOLDER])
def test_fill_owner_digest_refuses_a_malformed_digest(bad):
    with pytest.raises(ValueError):
        BD.fill_owner_digest(FROZEN, bad)


def test_authorization_text_both_forms_name_the_run_hash_never_a_frozen_hash():
    run = run_copy()
    rsha = hashlib.sha256(run).hexdigest()
    single = auth_for(run)
    assert set(single) == DG.SINGLE_KEYS and single["declaration_sha256"] == rsha
    multi = auth_for(run, nonces=("nonce-aaaaaaaaaaaaaaaa1", "nonce-bbbbbbbbbbbbbbbb2", "nonce-cccccccccccccccc3"), multi=True)
    assert set(multi) == DG.MULTI_KEYS and multi["invocations_authorized"] == 3
    for frozen in (FSHA, C.V2_SHA):
        with pytest.raises(ValueError, match="never a frozen hash"):
            BD.authorization_text(frozen, TEST_DIGEST, ["nonce-0123456789abcdef"], frozen_sha=FSHA)
    with pytest.raises(ValueError, match="1..3"):
        BD.authorization_text(rsha, TEST_DIGEST, [f"nonce-{i}-0123456789abcdef" for i in range(4)], frozen_sha=FSHA, multi=True)


def test_the_guard_accepts_the_in_memory_run_copy_with_its_own_authorization_in_both_forms():
    run = run_copy()
    decl = json.loads(run)
    rsha = hashlib.sha256(run).hexdigest()
    for a in (auth_for(run), auth_for(run, nonces=("nonce-aaaaaaaaaaaaaaaa1", "nonce-bbbbbbbbbbbbbbbb2"), multi=True)):
        v = DG.validate(decl, RUN_PATH, rsha, a, TEST_TOKEN)
        assert v["owner_token_sha256"] == TEST_DIGEST
    with pytest.raises(DG.DispatchRefused):
        DG.validate(decl, RUN_PATH, rsha, auth_for(run), "another-token")


def test_verify_run_file_refuses_without_a_run_file():
    with pytest.raises(C.PacketMismatch, match="no RUN file"):
        BD.verify_run_file(TEST_DIGEST, "0" * 64)


# ---- the scope-creation command -----------------------------------------------------------------------------------------------
def test_scope_preview_creates_nothing():
    before = C.ledger_counts()
    p = CSC.preview()
    assert p["ledger_unchanged"] and C.ledger_counts() == before and p["scope"] == C.SCOPE
    assert p["preconditions_now"]["7 interpreter, CLI file, free disk"]["floor"] == 2 * 1024 ** 3


def test_scope_create_refuses_without_the_authorization_file(capsys):
    assert CSC.main(["create", "--frozen-sha", FSHA, "--run-sha", "0" * 64]) == 3
    assert "no owner dispatch authorization" in capsys.readouterr().out


def _ok_args(run):
    return dict(run_path=RUN_PATH, run_folder=C.SANDBOX_BASE / "r42d-scope-test-absent")


def test_scope_create_refuses_wrong_hashes_tampered_run_and_wrong_token():
    run = run_copy()
    rsha = hashlib.sha256(run).hexdigest()
    a = auth_for(run)
    with pytest.raises(CSC.ScopeRefused, match="frozen declaration hash differs"):
        CSC.check_create(FROZEN, "0" * 64, run, rsha, a, TEST_TOKEN, **_ok_args(run))
    with pytest.raises(CSC.ScopeRefused, match="FROZEN hash"):
        CSC.check_create(FROZEN, FSHA, run, FSHA, a, TEST_TOKEN, **_ok_args(run))
    with pytest.raises(CSC.ScopeRefused, match="FROZEN hash"):
        CSC.check_create(FROZEN, FSHA, run, C.V2_SHA, a, TEST_TOKEN, **_ok_args(run))
    bad = run.replace(b'"r32-v3"', b'"r32-v4"', 1)
    with pytest.raises(CSC.ScopeRefused, match="not the frozen declaration with only the digest"):
        CSC.check_create(FROZEN, FSHA, bad, hashlib.sha256(bad).hexdigest(), a, TEST_TOKEN, **_ok_args(run))
    with pytest.raises(CSC.ScopeRefused, match="does not match the bound digest"):
        CSC.check_create(FROZEN, FSHA, run, rsha, a, "another-token", **_ok_args(run))
    with pytest.raises(CSC.ScopeRefused, match="no RUN declaration"):
        CSC.check_create(FROZEN, FSHA, None, rsha, a, TEST_TOKEN, **_ok_args(run))


def test_scope_create_refuses_below_the_disk_floor_and_when_the_run_folder_exists(tmp_path):
    run = run_copy()
    rsha = hashlib.sha256(run).hexdigest()
    with pytest.raises(CSC.ScopeRefused, match="below the declared floor"):
        CSC.check_create(FROZEN, FSHA, run, rsha, auth_for(run), TEST_TOKEN, verify_bound=False, free_fn=lambda p: 2 * 1024 ** 3 - 1, **_ok_args(run))
    with pytest.raises(CSC.ScopeRefused, match="exists: the scope is created once"):
        CSC.check_create(FROZEN, FSHA, run, rsha, auth_for(run), TEST_TOKEN, run_path=RUN_PATH, run_folder=tmp_path)


def test_scope_create_on_a_throwaway_ledger_creates_exactly_the_declared_scope(tmp_path):
    run = run_copy()
    rsha = hashlib.sha256(run).hexdigest()
    ok = CSC.check_create(FROZEN, FSHA, run, rsha, auth_for(run, nonces=("nonce-aaaaaaaaaaaaaaaa1", "nonce-bbbbbbbbbbbbbbbb2"), multi=True),
                          TEST_TOKEN, verify_bound=False, **_ok_args(run))
    assert ok["authorization_form"] == "multi" and ok["checks"]["cli_file"]["executed"] is False
    import sqlite3
    led = tmp_path / "throwaway-ledger.sqlite"
    con = sqlite3.connect(led)
    con.executescript("""create table scopes (scope text primary key, limits text, created_at real, breaker text, limits_version integer default 1);
        create table entries (id integer primary key autoincrement, scope text, at real, task text, adapter text, model text, state text,
          est_in integer, est_out integer, act_in integer, act_out integer, cached_in integer, turns integer, latency_ms integer,
          outcome text, usage_unknown integer default 0, pid integer, note text);
        create table limit_amendments (id integer primary key autoincrement, scope text, at real, version integer, old text, new text,
          authorized_by text, reason text, pid integer);""")
    con.close()
    assert pathlib.Path(led).resolve() != C.AI_LEDGER.resolve()
    before = C.ledger_counts()
    res = CSC.create_scope(ok, ledger_path=led)
    assert res["created"] and res["scope"] == C.SCOPE and res["limits"] == DECL["ledger"]["limits"] and res["breaker"] is None and res["entries"] == 0
    assert C.ledger_counts() == before, "the AI ledger is untouched"


# ---- the review42 evidence this package relies on ----------------------------------------------------------------------------------
CITED = ("test_global_provider_r42", "test_runner_order_r42", "test_resume_authorization_r42", "test_portability_r42", "test_runner_r32",
         "test_dispatch_guard_r32", "test_preflight_r32", "test_visibility_r38")


@pytest.mark.parametrize("module", CITED)
def test_the_cited_review42_tests_exist_and_passed(module):
    x = C.REVIEW42 / "tests" / f"{module}.xml"
    root = ET.parse(x).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    assert sum(int(s.get("tests", 0)) for s in suites) > 0
    assert sum(int(s.get(k, 0)) for s in suites for k in ("failures", "errors", "skipped")) == 0


def test_the_declared_arms_equal_the_runner_dry_values():
    assert RN.DRY_LANE_SWITCHES == DECL["lane_switches"] and RN.CAPS == DECL["budget"]["lane_allowances"] and RN.PARENT == DECL["budget"]["parent"]
    assert RN.WINDOW == DECL["project_window"] and PF.task_kinds_for(RN.DRY_LANE_SWITCHES) == DECL["lane_task_kinds"]


def test_no_authorization_run_or_token_file_in_this_package_or_sandbox():
    assert C.forbidden_files((C.PACKAGE, C.SANDBOX_BASE, C.REVIEW42)) == []
