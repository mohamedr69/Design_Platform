"""One-off patch of the r39 development copy of runner_r32.py (exact string replacements; refuses if any anchor is
missing or not unique). Writes only C:/t/iso/work/r2x/r39/harness-r32/runner_r32.py."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/runner_r32.py")
s = P.read_text(encoding="utf-8")

REPL = [
    # helper: the run is INVALID by an identity mismatch or a contract breach
    ("""def allowance_state(cfg) -> dict:""",
     """def run_invalid(run_folder) -> str | None:
    \"\"\"Why the run is INVALID (a model identity mismatch, A-09 point 2; a contract breach, ORCH-08C R39-04), or None.\"\"\"
    m = MI.invalid_marker(run_folder)
    if m is not None:
        return f"model identity mismatch ({m.get('lane')})"
    b = RC.breach_marker(run_folder)
    if b is not None:
        return f"contract breach ({b.get('lane')}: {b.get('kind')}, task {b.get('task')!r})"
    return None


def allowance_state(cfg) -> dict:"""),
    ("""    invalid = MI.invalid_marker(cfg["run_folder"]) is not None
""", """    invalid = run_invalid(cfg["run_folder"]) is not None
"""),
    ("""                if c_def or MI.invalid_marker(cfg["run_folder"]) is not None:
""", """                if c_def or run_invalid(cfg["run_folder"]) is not None:
"""),
    ("""        elif MI.invalid_marker(cfg["run_folder"]) is not None:
            gates |= {lane: "not started: the run is INVALID (model identity mismatch)" for lane in ("R", "P") if lane not in lanes}
            if "R" not in lanes:
                documents["R"] = _not_started(run_set, "R", "the run is INVALID (model identity mismatch)")
""", """        elif run_invalid(cfg["run_folder"]) is not None:
            why = f"the run is INVALID ({run_invalid(cfg['run_folder'])})"
            gates |= {lane: f"not started: {why}" for lane in ("R", "P") if lane not in lanes}
            if "R" not in lanes:
                documents["R"] = _not_started(run_set, "R", why)
"""),
    ("""        report["C_not_started"] = ctl.comparison if not invalid else "INVALID: model identity mismatch"
""", """        report["C_not_started"] = ctl.comparison if not invalid else f"INVALID: {run_invalid(cfg['run_folder'])}"
"""),
    ("""    if MI.invalid_marker(cfg["run_folder"]) is not None:
        report["comparison_state"], report["candidate_outcome"] = f"INVALID: model identity mismatch ({MI.invalid_marker(cfg['run_folder']).get('lane')})", "INVALID"
        report["identity_invalid"] = MI.invalid_marker(cfg["run_folder"])
""", """    if run_invalid(cfg["run_folder"]) is not None:
        report["comparison_state"], report["candidate_outcome"] = f"INVALID: {run_invalid(cfg['run_folder'])}", "INVALID"
        report["identity_invalid"] = MI.invalid_marker(cfg["run_folder"])
        report["contract_breach"] = RC.breach_marker(cfg["run_folder"])
"""),
    # resume refused after a breach
    ("""        if MI.invalid_marker(run_folder) is not None:
            raise Refused("refused: the run is INVALID (model identity mismatch recorded in IDENTITY-INVALID.json); it is never resumed")
""", """        if MI.invalid_marker(run_folder) is not None:
            raise Refused("refused: the run is INVALID (model identity mismatch recorded in IDENTITY-INVALID.json); it is never resumed")
        if RC.breach_marker(run_folder) is not None:
            raise Refused("refused: the run is INVALID (contract breach recorded in CONTRACT-BREACH.json: an undeclared request path); it is never resumed")
"""),
    # scoring: the bound decision coverage gate
    ("""                         docs={d["pool_id"] for d in run_set}, P=(lanes.get("P") or {}).get("probe"), r_gate=gates.get("R"))
""", """                         docs={d["pool_id"] for d in run_set}, P=(lanes.get("P") or {}).get("probe"), r_gate=gates.get("R"),
                         gate_definition=cfg["decision_coverage_gate"])
"""),
    # deferral times in the report
    ("""    report["earliest_retry_utc"] = _utc(min(retries)) if retries else None
    report["earliest_retry"] = min(retries) if retries else None
""", """    report["earliest_retry_utc"] = _utc(min(retries)) if retries else None
    report["earliest_retry"] = min(retries) if retries else None
    if retries:
        rt = resume_times(documents, min(retries))
        report["retry_at_earliest"], report["retry_at_earliest_utc"] = rt["earliest"], _utc(rt["earliest"])
        report["retry_at_full"] = {"structural": rt["full_structural"], "planning": rt["full_planning"]}
        report["retry_at_full_utc"] = {k: _utc(v) for k, v in report["retry_at_full"].items()}
        report["resume_policy"] = cfg["resume_policy"]
        report["resume_not_before"] = rt["full"] if cfg["resume_policy"] == "full" else rt["earliest"]
        if report["resume_not_before"] > allowance.bound_end():
            report["resume_not_before"] = rt["earliest"]
            report["resume_policy_note"] = "the full-policy time is after the elapsed bound: the resume falls back to the earliest retry"
        report["resume_not_before_utc"] = _utc(report["resume_not_before"])
    report["unread_pages"] = {lane: {pid: {"unread_pages": d.get("unread_pages"), "unread_page_count": d.get("unread_page_count"),
                                           "status": d.get("status")} for pid, d in (docs or {}).items() if d.get("unread_pages")}
                              for lane, docs in documents.items()}
"""),
    # the invocation record carries both retry times and the policy
    ("""                    "earliest_retry": report.get("earliest_retry"), "earliest_retry_utc": report.get("earliest_retry_utc"),
""", """                    "earliest_retry": report.get("earliest_retry"), "earliest_retry_utc": report.get("earliest_retry_utc"),
                    "retry_at_full": report.get("retry_at_full"), "retry_at_full_utc": report.get("retry_at_full_utc"),
                    "resume_policy": report.get("resume_policy"), "resume_not_before": report.get("resume_not_before"),
                    "resume_not_before_utc": report.get("resume_not_before_utc"),
"""),
    # resumable: the policy's time
    ("""    if st == "finished" and rs == "DEFERRED":
        retry = last.get("earliest_retry")
        if retry is not None and now < float(retry):
            return False, f"refused: the project window has not freed yet; the earliest retry is {_utc(retry)} (nothing was created)"
        return True, "the last invocation DEFERRED documents and the project window has freed"
""", """    if st == "finished" and rs == "DEFERRED":
        retry = last.get("resume_not_before", last.get("earliest_retry"))
        policy = last.get("resume_policy") or "earliest"
        if retry is not None and now < float(retry):
            return False, (f"refused: the resume policy '{policy}' allows a resume at {_utc(retry)} (earliest retry {_utc(last.get('earliest_retry'))}, "
                           f"full {(last.get('retry_at_full_utc') or {}).get('structural')}); nothing was created")
        return True, f"the last invocation DEFERRED documents and the resume policy '{policy}' time has come"
"""),
    # configuration: the contract-4 values in every lane configuration
    ("""               "policies": {"B": "B:accepted-path:evidence-off"}}
        if live:
            cfg["ledger"] = v["ledger"]
""", """               "policies": {"B": "B:accepted-path:evidence-off"},
               "application_env": v["application_env"] if live else dict(PF.APPLICATION_ENV),
               "lane_task_kinds": v["lane_task_kinds"] if live else PF.task_kinds_for(switches),
               "resume_policy": v["resume_policy"] if live else inject.get("resume_policy", PF.DEFAULT_RESUME_POLICY),
               "decision_coverage_gate": v["decision_coverage_gate"] if live else S.DECISION_COVERAGE_GATE,
               "project_totals": project_totals_of(v["bounds"]) if live else _dry_totals(run_set, truth, switches, window, parent, caps)}
        if live:
            cfg["ledger"] = v["ledger"]
"""),
    # dry totals helper and the dry inject keys
    ("""def _synthetic_truth(run_folder: pathlib.Path, spec: dict) -> dict:""",
     """def _dry_totals(run_set, truth, switches, window, parent, caps) -> dict | None:
    \"\"\"Dry mode: the project totals for retry_at_full, from the same bounds model over the dry run set (real or synthetic).\"\"\"
    import project_bounds_r32 as PB
    try:
        b = PB.compute(run_set, truth, switches, window_limit=window["limit"], window_s=window["window_s"], elapsed_s=parent["elapsed_s"], caps=caps)
    except Exception as exc:  # noqa: BLE001 -- dry only: no totals means retry_at_full is not computed (recorded)
        return {"_error": f"{type(exc).__name__}: {exc}"}
    return project_totals_of(b)


def _synthetic_truth(run_folder: pathlib.Path, spec: dict) -> dict:"""),
]


def main():
    global s
    for old, new in REPL:
        n = s.count(old)
        if n != 1:
            print(f"ANCHOR NOT UNIQUE ({n}): {old[:120]!r}")
            return 1
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8", newline="\n")
    print("patched", len(REPL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
