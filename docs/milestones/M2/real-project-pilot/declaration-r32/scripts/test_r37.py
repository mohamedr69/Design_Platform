"""ORCH-07 (R37DECL-IMPL): tests for the new scripts of the declaration package (no model call, no network, no ledger
write, no authorization file, no token; a syntactically valid dummy digest exists only in memory and is never written)."""
from __future__ import annotations

import ast
import copy
import json
import os
import pathlib
import subprocess
import sys

import pytest

sys.dont_write_bytecode = True
import append_response_r37 as AR  # noqa: E402
import build_declaration_r37 as BD  # noqa: E402
import concentration_on_proposal_r37 as CP  # noqa: E402
import estimates_r37 as E  # noqa: E402
import package_r37 as PK  # noqa: E402
import r37common as C  # noqa: E402
import snapshot_r37 as SN  # noqa: E402

if str(C.HARNESS_PACKAGE) not in sys.path:
    sys.path.insert(0, str(C.HARNESS_PACKAGE))
import dispatch_guard_r32 as DG  # noqa: E402
import preflight_r32 as PF  # noqa: E402

TREES = {"candidate": "C:/t/iso/cand-r29/backend", "baseline": "C:/t/iso/frozen-r12/backend"}


@pytest.fixture(scope="module")
def built():
    h = BD.hashes()
    est = E.estimate(E.load_run_set(), E.ledger_averages())
    decl = BD.build(est, h, "2026-10-03T00:00:00+00:00")
    return {"h": h, "est": est, "decl": decl, "text": C.json_text(decl)}


# ---- estimates ----------------------------------------------------------------------------------------------------------
def test_estimates_cover_the_24_documents_and_stay_inside_the_caps(built):
    est = built["est"]
    assert est["documents"] == 24
    assert sum(v["documents"] for v in est["projects"].values()) == 24
    lanes = est["lanes"]
    assert lanes["C"]["planning"] == sum(v["C_planning"] for v in est["projects"].values()) == 112
    assert lanes["C"]["conservative"] == 8 * 24 == 192 <= 240
    assert lanes["B"]["planning"] == 6 and lanes["B"]["conservative"] == 16
    assert lanes["R"]["conservative"] == 40 and lanes["P"]["conservative"] <= 36
    assert lanes["total"]["conservative"] <= 556 and lanes["total"]["cap"] == 556
    for x in ("B", "C", "R", "P"):
        assert lanes[x]["planning"] <= lanes[x]["conservative"] <= lanes[x]["cap"]


def test_ep27331_is_the_binding_project_for_b_plus_c_and_stays_below_60(built):
    p = built["est"]["projects"]
    assert list(p)[0] == "EP-27331"
    assert p["EP-27331"]["documents"] == 6 and p["EP-27331"]["pages_read_by_c"] == 23 and p["EP-27331"]["decision_bearing"] == 6
    assert p["EP-27331"]["B_plus_C_planning"] == 52 and p["EP-27331"]["B_plus_C_max"] == 54
    assert max(v["B_plus_C_planning"] for v in p.values()) == p["EP-27331"]["B_plus_C_planning"]
    a = E.day_limit_assessment(built["est"], 60)
    assert not any(v["b_or_c_refusal_possible_at_planning"] or v["b_or_c_refusal_possible_at_maximum"] for v in a.values())
    assert a["EP-27331"]["r_or_p_refusal_possible_at_planning"] is True


def test_token_planning_is_far_below_the_scope_totals(built):
    t = built["est"]["tokens"]["total"]
    lim = BD.LEDGER_LIMITS
    assert t["planning_input"] < lim["input_tokens"] and t["planning_output"] < lim["output_tokens"]
    assert t["conservative_input"] < lim["input_tokens"] and t["conservative_output"] < lim["output_tokens"]


# ---- the declaration -----------------------------------------------------------------------------------------------------
def test_the_placeholder_is_refused_by_the_frozen_preflight(built):
    path = C.PACKAGE / C.DECLARATION_NAME
    with pytest.raises(PF.Refused, match="binds no owner token digest"):
        PF.validate_declaration(built["decl"], path)


def test_an_in_memory_copy_with_a_dummy_digest_passes_every_other_check(built):
    path = C.PACKAGE / C.DECLARATION_NAME
    m = copy.deepcopy(built["decl"])
    m["authorization"]["owner_token_sha256"] = C.DUMMY_DIGEST
    v = PF.validate_declaration(m, path)
    assert v["stamp"] == BD.STAMP and v["run_folder"] == f"C:/t/r2x/r34-sandbox/{BD.STAMP}"
    assert v["caps"] == {"B": 240, "C": 240, "R": 40, "P": 36} and v["project_day_limit"] == 60
    assert v["authorization_path"].lower() == DG.pinned_path(path).as_posix().lower()
    assert v["ledger"]["limits"]["requests"] == 556


def test_the_declaration_binds_every_required_key_and_its_status(built):
    d = built["decl"]
    for k in ("binding_manifest_sha256", "run_set_sha256", "run", "authorization", "caps", "project_day_limit", "lane_switches", "provider_env", "ledger"):
        assert d[k] not in (None, "", {})
    assert d["executed"] is False and d["budget_approved"] is False
    assert d["authorization_status"] == "none; owner decision pending" and d["authorization"]["status"] == "none; owner decision pending"
    assert d["binding_manifest_sha256"] == C.FROZEN["binding_manifest_r36"][1] and d["run_set_sha256"] == C.FROZEN["run_set_proposal"][1]
    assert d["policy"]["policy"]["sha256"] == C.FROZEN["policy"][1] and d["policy"]["amendment_r32_01"]["sha256"] == C.FROZEN["policy_amendment_r32_01"][1]
    assert d["evaluator"]["file"]["sha256"] == C.FROZEN["evaluator_10"][1] and d["evaluator"]["role"].startswith("EMISSION ONLY")
    assert d["standing_status"] == {"M2": "CHANGES STILL REQUIRED", "M3": "not started"}


def test_the_placeholder_occurs_once_and_the_fill_changes_only_that_field(built):
    raw = built["text"].encode("utf-8")
    assert raw.count(json.dumps(C.TOKEN_PLACEHOLDER).encode()) == 1
    filled = BD.fill_owner_digest(raw, C.DUMMY_DIGEST)           # in memory only
    a, b = json.loads(raw), json.loads(filled)
    assert b["authorization"]["owner_token_sha256"] == C.DUMMY_DIGEST
    a["authorization"]["owner_token_sha256"] = C.DUMMY_DIGEST
    assert a == b and len(filled) == len(raw) - len(C.TOKEN_PLACEHOLDER) + 64


@pytest.mark.parametrize("bad", ["", "ABC", "g" * 64, "0" * 63, C.DUMMY_DIGEST.upper().replace("0", "A")])
def test_the_fill_refuses_anything_but_a_64_hex_digest(built, bad):
    with pytest.raises(ValueError):
        BD.fill_owner_digest(built["text"].encode("utf-8"), bad)


def test_lane_switches_restate_the_draft_v2_arms_and_equal_the_runner_dry_defaults(built):
    sw = built["decl"]["lane_switches"]
    draft = json.loads((C.PILOT / "review31/DRAFT-DECLARATION.v2.json").read_text(encoding="utf-8"))["arms"]
    assert sw["C"] == draft["C"]["switches"] and sw["R"] == draft["R"]["switches"] and sw["P"] == {}
    assert sw["B"] == {"AI_EVIDENCE_VARIANT": "off"} and draft["B"]["switches"] == {}
    tree = ast.parse((C.HARNESS_PACKAGE / "runner_r32.py").read_text(encoding="utf-8"))
    dry = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DRY_LANE_SWITCHES")
    assert dry == sw
    assert set(sw["C"]) - set(sw["R"]) == {"AI_EVIDENCE_IDGUARD", "AI_EVIDENCE_ADJUDICATE", "AI_EVIDENCE_DECISION_REGION", "AI_EVIDENCE_ASSOC"}


def test_ledger_limits_are_ledger_fields_sum_the_lane_thresholds_and_match_provider_env(built):
    d = built["decl"]
    lim = d["ledger"]["limits"]
    src = pathlib.Path("C:/t/iso/cand-r29/backend/app/ai/ledger.py").read_text(encoding="utf-8")
    cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "Limits")
    fields = {s.target.id for s in cls.body if isinstance(s, ast.AnnAssign)}
    assert set(lim) == fields == {"requests", "input_tokens", "output_tokens", "per_request_input", "per_request_output", "elapsed_s"}
    assert lim["requests"] == 556 and lim["per_request_input"] == 90_000 and lim["per_request_output"] == 20_000
    assert lim["input_tokens"] == 16_300_000 and lim["output_tokens"] == 3_260_000 and lim["elapsed_s"] == 168 * 3600
    assert json.loads(d["provider_env"]["AI_LEDGER_LIMITS"]) == lim
    assert d["provider_env"]["AI_LEDGER_SCOPE"] == d["ledger"]["scope"] and d["ledger"]["wrap_provider"] is True


def test_the_scope_is_new_and_the_run_folder_does_not_exist(built):
    led = C.ledger_state()
    assert BD.SCOPE not in led["scope_names"]
    assert {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED
    assert not (C.LIVE_SANDBOX_BASE / BD.STAMP).exists()


def test_thresholds_and_stop_rules_are_carried_verbatim(built):
    d = built["decl"]
    for item in d["thresholds_verbatim"]:
        text = pathlib.Path(item["path"]).read_text(encoding="utf-8")
        assert C.sha256_file(item["path"]) == item["sha256"]
        for t in (item["text"] if isinstance(item["text"], list) else [item["text"]]):
            assert t in text
    for key in ("verbatim_stop_and_safety_rules", "verbatim_review34_resume_rules"):
        v = d["stop_rules"][key]
        assert "\n".join(v["text"]) in pathlib.Path(v["source"]).read_text(encoding="utf-8")
    assert any("Three consecutive provider failures" in line for line in d["stop_rules"]["verbatim_stop_and_safety_rules"]["text"])
    assert any("Budget stops are not undone by a resume" in line for line in d["stop_rules"]["verbatim_review34_resume_rules"]["text"])


def _settings_in(tree: str, env_extra: dict) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AI_", "DATABASE_", "DATA_ROOT", "PROJECTS_ROOT", "COMPLIANCE_"))}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "DATA_ROOT": "", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "DATABASE_URL": "sqlite:///./not-opened.db"} | env_extra)
    code = ("import json; from app.core.config import Settings; s = Settings(); "
            "print(json.dumps({k: getattr(s, k) for k in s.model_fields if k.startswith('ai_')}, default=str))")
    r = subprocess.run([C.PY, "-B", "-c", code], cwd=tree, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("tree", sorted(TREES))
def test_every_provider_env_value_reaches_the_application_settings(built, tree):
    pe = built["decl"]["provider_env"]
    s = _settings_in(TREES[tree], dict(pe) | {"AI_ENABLED": "true"})
    for k, v in pe.items():
        name = k.lower()
        assert name in s, f"{k} is not an application setting in {tree}"
        got = s[name]
        if k == "AI_LEDGER_LIMITS":
            assert json.loads(got) == json.loads(v)
        elif isinstance(got, float):
            assert got == float(v), (k, got, v)
        elif isinstance(got, int):
            assert got == int(v), (k, got, v)
        else:
            assert str(got).replace("\\", "/") == v, (k, got, v)


@pytest.mark.parametrize("tree", sorted(TREES))
def test_the_bound_application_limits_equal_the_tree_defaults(built, tree):
    s = _settings_in(TREES[tree], {})
    for k, v in BD.APPLICATION_LIMITS.items():
        got = s[k.lower()]
        assert (got == type(got)(v)) if not isinstance(got, str) else got == v, (tree, k, got, v)
    for k, v in BD.TREE_DEFAULTS.items():
        assert str(s[k.lower()]) == v, (tree, k, s[k.lower()], v)


# ---- concentration on the proposal (pure parts) -------------------------------------------------------------------------
META = {"a1": {"project": "P1", "contractor": "K1", "layout_key": "L1"}, "a2": {"project": "P1", "contractor": "K1", "layout_key": "L2"},
        "b1": {"project": "P2", "contractor": "K2", "layout_key": "L1"}, "c1": {"project": "P3", "contractor": "K3", "layout_key": "L3"}}


@pytest.mark.parametrize("gain,want", [((), "UNDETERMINED"), (("a1",), "NOT ELIGIBLE"), (("a1", "a2"), "NOT ELIGIBLE"),
                                       (("a1", "b1"), "NOT ELIGIBLE"), (("a2", "b1"), "ELIGIBLE"), (("a1", "a2", "b1"), "NOT ELIGIBLE"),
                                       (("a1", "b1", "c1"), "NOT ELIGIBLE"), (("a2", "b1", "c1"), "ELIGIBLE")])
def test_the_oracle_is_more_than_half_in_one_project_contractor_or_layout(gain, want):
    assert CP.oracle(list(gain), META) == want


def test_the_structure_counts_every_gain_set_once():
    import math

    docs = ["F1", "F2", "F3", "F4"]
    meta = {"F1": META["a1"], "F2": META["a2"], "F3": META["b1"], "F4": META["c1"]}
    s = CP.structure(docs, meta)
    for size, v in s["gain_sets_by_size"].items():
        assert v["total"] == math.comb(4, int(size))
    assert s["gain_sets_by_size"]["1"]["eligible"] == 0 and s["smallest_eligible_net_gain"] == 2
    # pairs: F1+F2 share P1 and F1+F3 share L1 (NOT ELIGIBLE); F1+F4, F2+F3, F2+F4, F3+F4 differ in both (ELIGIBLE)
    assert s["gain_sets_by_size"]["2"]["eligible"] == 4
    assert s["gain_sets_by_size"]["4"]["eligible"] == 1           # P1 holds 2 of 4 and L1 2 of 4: exactly half is not more than half


# ---- writing, snapshot, package check and the ledger append (pure parts; temporary files only) -------------------------
def test_write_once_refuses_an_existing_file_and_writes_lf_only(tmp_path):
    p = tmp_path / "x.json"
    sha = C.write_json_once(p, {"b": "line\nnext", "a": 1})
    raw = p.read_bytes()
    assert b"\r" not in raw and C.sha256_bytes(raw) == sha and raw.endswith(b"\n") and raw.index(b'"a"') < raw.index(b'"b"')
    with pytest.raises(FileExistsError):
        C.write_once(p, "again")


def _snap(files, singles=None):
    return {"trees": {"t": {"files": files}}, "single_files": singles or {"s": {"sha256": "1", "mtime_utc": "2026-10-03T10:00:00+00:00"}}}


def test_snapshot_compare_flags_any_changed_added_or_removed_file():
    a = {"f": {"sha256": "1", "mtime_utc": "2026-10-03T10:00:00+00:00"}}
    assert SN.compare(_snap(a), _snap(dict(a)))["trees_unchanged"] is True
    assert SN.compare(_snap(a), _snap({"f": {"sha256": "2", "mtime_utc": a["f"]["mtime_utc"]}}))["tree_differences"] == {"t": ["f"]}
    assert SN.compare(_snap(a), _snap({"f": {"sha256": "1", "mtime_utc": "2026-10-03T11:00:00+00:00"}}))["trees_unchanged"] is False
    assert SN.compare(_snap(a), _snap(a | {"g": {"sha256": "3", "mtime_utc": "x"}}))["tree_differences"] == {"t": ["g"]}
    assert SN.compare(_snap(a), _snap({}))["tree_differences"] == {"t": ["f"]}


def test_the_frozen_mtime_check_uses_the_task_limit():
    ok = _snap({"f": {"sha256": "1", "mtime_utc": "2026-10-03T16:54:59+00:00"}})
    late = _snap({"f": {"sha256": "1", "mtime_utc": "2026-10-03T16:55:01+00:00"}})
    assert PK.FROZEN_MTIME_LIMIT == "2026-10-03T16:55:00+00:00"
    assert PK.frozen_mtime_check(ok)["ok"] is True
    assert PK.frozen_mtime_check(late)["files_modified_after_limit"] == {"t": ["f"]}


def test_junit_summary_counts_tests_failures_and_names(tmp_path):
    x = tmp_path / "j.xml"
    x.write_text('<testsuites><testsuite tests="2" failures="1" errors="0" skipped="0"><testcase name="a"/><testcase name="b"><failure/></testcase>'
                 '</testsuite></testsuites>', encoding="utf-8")
    s = PK.junit_summary(x)
    assert (s["tests"], s["failures"], s["errors"], s["names"]) == (2, 1, 0, ["a", "b"])


def test_the_ledger_append_heading_is_the_task_heading_and_the_before_hash_is_pinned():
    assert AR.HEADING == ("# Fresh-validation declaration R32 and budget decision card v3 (ORCH-07, 2026-10-03): frozen, NOT authorized, NO dispatch")
    assert C.RESPONSE_BEFORE_SHA256 == "b055b6a67cbad7e0abef195c68422551129ddffc26c2d1c1ec18b2557a1872e8"
