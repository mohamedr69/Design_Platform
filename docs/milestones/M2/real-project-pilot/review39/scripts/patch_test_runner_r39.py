"""One-off patch of the r39 development copy of test_runner_r32.py (exact replacements; refuses on a missing anchor)."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/test_runner_r32.py")
s = P.read_text(encoding="utf-8")
DRY4 = """"application_env": dict(PF.APPLICATION_ENV), "lane_task_kinds": PF.task_kinds_for(RN.DRY_LANE_SWITCHES), "resume_policy": "full",
           "decision_coverage_gate": "C_GE_B_ONLY", """

REPL = [
    ("""def test_lane_env_has_no_silent_default(tmp_path):
    with pytest.raises(RN.Refused, match="no switches for lane C"):
        RN.lane_env("live", tmp_path / "C", "C", {"lane_switches": {"B": {}}, "provider_env": {"AI_PROVIDER": "claude-code"}})
    with pytest.raises(RN.Refused, match="provider environment"):
        RN.lane_env("live", tmp_path / "C", "C", {"lane_switches": H.LIVE_SWITCHES, "provider_env": None})
    env = RN.lane_env("dry", tmp_path / "P", "P", {"lane_switches": RN.DRY_LANE_SWITCHES})
    assert not [k for k in env if k.startswith("AI_EVIDENCE_")] and env["AI_LEDGER_PATH"] == ""
    env = RN.lane_env("dry", tmp_path / "C", "C", {"lane_switches": RN.DRY_LANE_SWITCHES})
    assert {k: v for k, v in env.items() if k.startswith("AI_EVIDENCE_")} == RN.DRY_LANE_SWITCHES["C"]""",
     """def test_lane_env_has_no_silent_default(tmp_path):
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
    assert env["DRAWINGS_AI_REVIEW_ENABLED"] == "false", "ORCH-08C: the drawings-AI review is off in every lane" """),
    ("""           "provider_env": v["provider_env"], "model_identity": v["model_identity"], "cli_version": "2.1.263 (Claude Code)",
           "switch_source": "the declaration's lane_switches", "policies": {"B": "B:accepted-path:evidence-off"}} | (cfg_over or {})""",
     """           "provider_env": v["provider_env"], "model_identity": v["model_identity"], "cli_version": "2.1.263 (Claude Code)",
           "switch_source": "the declaration's lane_switches", "policies": {"B": "B:accepted-path:evidence-off"},
           "application_env": v["application_env"], "lane_task_kinds": v["lane_task_kinds"], "resume_policy": v["resume_policy"],
           "decision_coverage_gate": v["decision_coverage_gate"], "project_totals": RN.project_totals_of(v["bounds"])} | (cfg_over or {})"""),
    ("""    (None, {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": "60"}, "AI_MAX_CALLS_PER_PROJECT_PER_DAY in the environment"),
])""",
     """    (None, {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": "60"}, "AI_MAX_CALLS_PER_PROJECT_PER_DAY in the environment"),
    # ORCH-08C (R39-04, R39-08, R39-15): the contract-4 values are verified by every live lane before anything is built
    (None, {"DRAWINGS_AI_REVIEW_ENABLED": "true"}, "DRAWINGS_AI_REVIEW_ENABLED in the environment is 'true'"),
    (None, {"DRAWINGS_AI_REVIEW_ENABLED": None}, "DRAWINGS_AI_REVIEW_ENABLED in the environment is None"),
    ({"lane_task_kinds": {"B": ["read_submittal_form", "drawings_reply_match"], "C": [], "R": [], "P": []}}, None,
     "differs from the declaration in \\\\['lane_task_kinds'\\\\]"),
    ({"resume_policy": "earliest"}, None, "differs from the declaration in \\\\['resume_policy'\\\\]"),
    ({"decision_coverage_gate": "C_GE_B_AND_C_GE_R"}, None, "differs from the declaration in \\\\['decision_coverage_gate'\\\\]"),
    ({"application_env": {"DRAWINGS_AI_REVIEW_ENABLED": "false", "OTHER": "x"}}, None, None),
])"""),
    ("""def test_a_direct_live_lane_with_a_configuration_or_environment_unlike_the_declaration_is_refused(tmp_path, cfg_over, env_over, match):
    r, folder, out, led = _direct_lane(tmp_path, cfg_over=cfg_over, env_over=env_over)""",
     """def test_a_direct_live_lane_with_a_configuration_or_environment_unlike_the_declaration_is_refused(tmp_path, cfg_over, env_over, match):
    if match is None:                                   # an application_env with another key: refused before the lane starts
        with pytest.raises(RN.Refused, match="application_env must be exactly"):
            _direct_lane(tmp_path, cfg_over=cfg_over, env_over=env_over)
        return
    r, folder, out, led = _direct_lane(tmp_path, cfg_over=cfg_over, env_over=env_over)"""),
    ("""    deferred = {"status": "finished", "comparison_state": "INCOMPLETE", "run_state": "DEFERRED", "earliest_retry": 1100.0}
    ok, why = RN.resumable(deferred, now=now, bound_end=5000)
    assert not ok and "has not freed yet" in why
    assert RN.resumable(deferred, now=1101.0, bound_end=5000)[0]""",
     """    deferred = {"status": "finished", "comparison_state": "INCOMPLETE", "run_state": "DEFERRED", "earliest_retry": 1100.0}
    ok, why = RN.resumable(deferred, now=now, bound_end=5000)
    assert not ok and "allows a resume at" in why and "nothing was created" in why
    assert RN.resumable(deferred, now=1101.0, bound_end=5000)[0]
    # ORCH-08C (R39-08): the declared resume policy's time governs
    full = deferred | {"resume_policy": "full", "resume_not_before": 1500.0, "retry_at_full": {"structural": 1500.0, "planning": 1200.0}}
    ok, why = RN.resumable(full, now=1101.0, bound_end=5000)
    assert not ok and "'full'" in why, "after the earliest retry but before the full time: refused under 'full'"
    assert RN.resumable(full, now=1501.0, bound_end=5000)[0]
    early = deferred | {"resume_policy": "earliest", "resume_not_before": 1100.0}
    assert RN.resumable(early, now=1101.0, bound_end=5000)[0]"""),
    ("""           "model_identity": RN.DRY_PINS, "cli_version": RN.DRY_CLI_VERSION, "policies": {"B": "B:accepted-path:evidence-off"}}
    return T, cfg, rs, out, sbx / "inv-1", files""",
     """           "model_identity": RN.DRY_PINS, "cli_version": RN.DRY_CLI_VERSION, "policies": {"B": "B:accepted-path:evidence-off"},
           """ + DRY4 + """"project_totals": None}
    return T, cfg, rs, out, sbx / "inv-1", files"""),
    ("""           "lane_switches": RN.DRY_LANE_SWITCHES, "switch_source": PF.DRY_LANE_SWITCHES_LABEL, "policies": {"B": "B:accepted-path:evidence-off"}}
    with pytest.raises(RuntimeError, match="lane B failed"):""",
     """           "lane_switches": RN.DRY_LANE_SWITCHES, "switch_source": PF.DRY_LANE_SWITCHES_LABEL, "policies": {"B": "B:accepted-path:evidence-off"},
           """ + DRY4 + """"project_totals": None}
    with pytest.raises(RuntimeError, match="lane B failed"):"""),
    # new tests appended before the last test
    ("""def test_no_authorization_file_was_written_by_the_tests():""",
     """def test_resume_times_take_the_latest_structural_full_time_of_the_deferred_documents():
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


def test_no_authorization_file_was_written_by_the_tests():"""),
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
