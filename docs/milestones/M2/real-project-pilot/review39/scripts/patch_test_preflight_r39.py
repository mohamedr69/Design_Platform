"""One-off patch of the r39 development copy of test_preflight_r32.py (exact replacements; refuses on a missing anchor)."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/test_preflight_r32.py")
s = P.read_text(encoding="utf-8")

NEW = '''

# ---- ORCH-08C: contract 4 (application_env, lane_task_kinds, resume_policy, decision_coverage_gate) ------------------------------
@pytest.mark.parametrize("value,match", [
    ({"DRAWINGS_AI_REVIEW_ENABLED": "true"}, "must be exactly"),
    ({"DRAWINGS_AI_REVIEW_ENABLED": "False"}, "must be exactly"),
    ({"DRAWINGS_AI_REVIEW_ENABLED": "false", "DOCUMENT_CLASSIFICATION_V2": "false"}, "must be exactly"),
    ({"DRAWINGS_AI_REVIEW_ENABLED": "false", "AI_ENABLED": "true"}, "non-AI_"),
    ({"IFC_AI_SYMBOL_REVIEW_ENABLED": "false"}, "must be exactly"),
    ({"DRAWINGS_AI_REVIEW_ENABLED": False}, "map setting names to strings"),
])
def test_application_env_must_be_exactly_the_allowlist(tmp_path, value, match):
    p, sha, rec = _decl(tmp_path, application_env=value)
    with pytest.raises(PF.Refused, match=match):
        PF.validate_declaration(rec, p)


def test_a_declaration_without_the_contract_4_blocks_is_refused(tmp_path):
    for key in ("application_env", "lane_task_kinds", "resume_policy", "decision_coverage_gate"):
        p, sha, rec = _decl(tmp_path / key, **{key: None})
        with pytest.raises(PF.Refused, match=f"does not bind '{key}'"):
            PF.validate_declaration(rec, p)
    p, sha, rec = _decl(tmp_path / "c3", contract="r38-live-contract-3")
    with pytest.raises(PF.Refused, match="is not contract r39-live-contract-4"):
        PF.validate_declaration(rec, p)


def test_the_declared_task_kinds_must_equal_those_of_the_declared_switches(tmp_path):
    p, sha, rec = _decl(tmp_path)
    v = PF.validate_declaration(rec, p)
    assert v["lane_task_kinds"] == PF.task_kinds_for(H.LIVE_SWITCHES) and v["application_env"] == {"DRAWINGS_AI_REVIEW_ENABLED": "false"}
    assert v["resume_policy"] == "full" and v["decision_coverage_gate"] == "C_GE_B_ONLY"
    wider = copy.deepcopy(rec["lane_task_kinds"])
    wider["B"] = wider["B"] + ["drawings_reply_match"]
    for bad in (wider, {k: v for k, v in rec["lane_task_kinds"].items() if k != "P"}, dict(rec["lane_task_kinds"], C=["discover_page"])):
        p2, sha2, rec2 = _decl(tmp_path / f"k{len(str(bad))}", lane_task_kinds=bad)
        with pytest.raises(PF.Refused, match="lane_task_kinds must equal"):
            PF.validate_declaration(rec2, p2)


@pytest.mark.parametrize("key,value,match", [("resume_policy", "soonest", "resume_policy must be one of"),
                                             ("decision_coverage_gate", "C_GE_R_ONLY", "decision_coverage_gate must be one of")])
def test_resume_policy_and_gate_ids_are_closed_sets(tmp_path, key, value, match):
    p, sha, rec = _decl(tmp_path, **{key: value})
    with pytest.raises(PF.Refused, match=match):
        PF.validate_declaration(rec, p)
    p, sha, rec = _decl(tmp_path / "ok", resume_policy="earliest", decision_coverage_gate="C_GE_B_AND_C_GE_R")
    v = PF.validate_declaration(rec, p)
    assert v["resume_policy"] == "earliest" and v["decision_coverage_gate"] == "C_GE_B_AND_C_GE_R", "both are declarable; the owner rules"


def test_every_lane_verifies_the_application_env_in_its_environment_and_settings():
    ok = types.SimpleNamespace(drawings_ai_review_enabled=False)
    env = {"DRAWINGS_AI_REVIEW_ENABLED": "false"}
    out = PF.verify_application_env("B", dict(PF.APPLICATION_ENV), env, ok)
    assert out["application_env_verified"][0]["setting"] == "drawings_ai_review_enabled"
    with pytest.raises(PF.Refused, match="in the environment is None"):
        PF.verify_application_env("B", dict(PF.APPLICATION_ENV), {}, ok)
    with pytest.raises(PF.Refused, match="setting drawings_ai_review_enabled is True"):
        PF.verify_application_env("C", dict(PF.APPLICATION_ENV), env, types.SimpleNamespace(drawings_ai_review_enabled=True))
    with pytest.raises(PF.Refused, match="has no setting drawings_ai_review_enabled"):
        PF.verify_application_env("R", dict(PF.APPLICATION_ENV), env, types.SimpleNamespace())
    with pytest.raises(PF.Refused, match="no declared application environment"):
        PF.verify_application_env("P", None, env, ok)
'''

REPL = [
    ('''"""preflight_r32: the live declaration contract 3 (ORCH-08: parent budget, lane allowances, project rolling window, request''',
     '''"""preflight_r32: the live declaration contract 4 (ORCH-08C adds application_env, lane_task_kinds, resume_policy and
decision_coverage_gate to contract 3; ORCH-08: parent budget, lane allowances, project rolling window, request'''),
    ('''def test_live_ledger_growth_only_inside_the_declared_scope_and_within_the_parent_total(tmp_path):''',
     NEW.lstrip("\n") + '''

def test_live_ledger_growth_only_inside_the_declared_scope_and_within_the_parent_total(tmp_path):'''),
]


def main():
    global s
    for old, new in REPL:
        n = s.count(old)
        if n != 1:
            print(f"ANCHOR NOT UNIQUE ({n}): {old[:160]!r}")
            return 1
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8", newline="\n")
    print("patched", len(REPL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
