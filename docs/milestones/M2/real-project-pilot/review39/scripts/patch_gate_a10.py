"""One-off patch (owner ruling A-10) of the r39 development copies of score_bcr_r32.py and preflight_r32.py: the decision
coverage gate is C >= B only (a change from plan v2), C >= R a MANDATORY diagnostic with counts, missing coverage per
document and reasons; R is refused as an eligibility input. Exact replacements; refuses on a missing anchor."""
import pathlib
import sys

H = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32")
EDITS = {"score_bcr_r32.py": [
    ('''  (A-09 point 6, R38-09) R and P earn NO accuracy or recovery credit anywhere: R's metrics, its decision controls and the
    C >= R decision-coverage contrast are DIAGNOSTICS (result["diagnostics"]["R"], credit 'none'); the decision coverage
    GATE is C >= B only; the candidate outcome never reads R or P (a full R, a truncated R and no R give the same
    outcome).''',
     '''  (A-09 point 6, R38-09) R and P earn NO accuracy or recovery credit anywhere: R's metrics, its decision controls and the
    C >= R decision-coverage contrast are DIAGNOSTICS (result["diagnostics"]["R"], credit 'none'); the decision coverage
    GATE is C >= B only -- a CHANGE FROM PLAN V2, whose gate was C >= B and C >= R (ruled by the owner, A-10); the
    candidate outcome never reads R or P (a full R, a truncated R and no R give the same outcome).'''),
    ('''  (R39-15) the decision coverage gate is ONE named constant, DECISION_COVERAGE_GATE, whose definition (id and text) is in
    DECISION_COVERAGE_GATE_DEFINITIONS; the current definition is unchanged ('C_GE_B_ONLY': C >= B only; C >= R a reported
    diagnostic), PENDING THE OWNER'S RULING (Verification 39 C3). The alternative ('C_GE_B_AND_C_GE_R': C >= B and C >= R,
    INCOMPLETE when R did not complete its population) is implemented so that a declaration can bind whichever the owner
    rules (contract 4 key decision_coverage_gate); evaluate(..., gate_definition=...) applies the bound one.''',
     '''  (R39-15; owner ruling A-10, 2026-10-04) the decision coverage gate is ONE named constant, DECISION_COVERAGE_GATE =
    'C_GE_B_ONLY', whose definition (id and text) is in DECISION_COVERAGE_GATE_DEFINITIONS: decision coverage eligibility
    is C >= B ONLY. This is a CHANGE FROM PLAN V2 (plan v2's gate was C >= B and C >= R; PLAN_V2_DECISION_COVERAGE_GATE
    keeps its text for the record); it is never an unchanged gate. C >= R is a MANDATORY diagnostic in EVERY result
    (result["decision_coverage_C_ge_R"]): the counts of both lanes, the missing coverage per document with its reasons,
    INCOMPLETE when R did not complete its population; it never determines eligibility. A definition that binds R into
    eligibility (the plan v2 gate, or any other) is REFUSED by evaluate() and by the declaration contract
    (decision_coverage_gate must be 'C_GE_B_ONLY'). Every other safety, accuracy and completeness gate is unchanged.'''),
    ('''# ORCH-08C (R39-15): the decision coverage gate as ONE named constant carrying its text. ORCH-08C changes no gate: the
# current definition is review38's. Pending the owner's ruling (Verification 39 C3); the declaration binds the id.
DECISION_COVERAGE_GATE_DEFINITIONS = {
    "C_GE_B_ONLY": {
        "id": "C_GE_B_ONLY",
        "text": ("decision coverage of C >= decision coverage of B on the resolved decision documents of the run set (completed read or "
                 "verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE rows are never coverage); "
                 "C >= R is a reported diagnostic without credit and never decides anything"),
        "reads_R": False, "source": "review38 (ORCH-08, A-09 point 6 read as: R never decides anything)",
        "status": "current definition, pending owner ruling (Verification 39 C3)"},
    "C_GE_B_AND_C_GE_R": {
        "id": "C_GE_B_AND_C_GE_R",
        "text": ("decision coverage of C >= that of B AND >= that of R on the resolved decision documents of the run set (same coverage "
                 "rule); when R did not complete its declared population (truncated, refused, deferred or not started) the gate is "
                 "INCOMPLETE and the decision field is INCOMPLETE (a truncated R can never make the gate easier to pass)"),
        "reads_R": True, "source": "plan v2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md) with the A-09 point 7 truncation rule",
        "status": "alternative, implemented for binding only if the owner so rules"}}
DECISION_COVERAGE_GATE = "C_GE_B_ONLY"           # the gate in force (pending owner ruling, Verification 39 C3)''',
     '''# ORCH-08C (R39-15) and owner ruling A-10 (2026-10-04): the decision coverage gate as ONE named constant carrying its text.
DECISION_COVERAGE_GATE_DEFINITIONS = {
    "C_GE_B_ONLY": {
        "id": "C_GE_B_ONLY",
        "text": ("decision coverage eligibility: decision coverage of C >= decision coverage of B on the resolved decision documents of "
                 "the run set (completed read or verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE "
                 "rows are never coverage). C >= R is a MANDATORY diagnostic -- reported in every result with both lanes' counts, the "
                 "missing coverage per document and its reasons, INCOMPLETE when R did not complete its population -- and it never "
                 "determines eligibility"),
        "reads_R": False, "source": "review38 (ORCH-08) and the owner's ruling A-10 (2026-10-04)",
        "change_from_plan_v2": ("CHANGED from plan v2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md), whose gate was C >= B AND C >= R: "
                                "the C >= R leg is removed from eligibility and kept as a mandatory diagnostic (owner ruling A-10)"),
        "status": "BOUND by the owner's ruling A-10 (2026-10-04); a change from plan v2, never an unchanged gate"}}
DECISION_COVERAGE_GATE = "C_GE_B_ONLY"           # the gate in force (owner ruling A-10): eligibility reads B and C only
PLAN_V2_DECISION_COVERAGE_GATE = {
    "id": "C_GE_B_AND_C_GE_R", "text": "plan v2: decision coverage of C >= that of B AND >= that of R",
    "status": "SUPERSEDED by the owner's ruling A-10: R never determines eligibility; refused if a declaration or a caller binds it"}
C_GE_R_DIAGNOSTIC_RULE = ("mandatory diagnostic (owner ruling A-10): C >= R decision coverage, reported with both lanes' counts, the missing "
                          "coverage per document and the reasons; INCOMPLETE when R did not complete its declared population (or did not "
                          "run); it never determines eligibility and earns no credit")


def refuse_r_in_eligibility(definition) -> str:
    """The bound gate id, or ValueError when a definition would bind R into eligibility (owner ruling A-10)."""
    if definition == PLAN_V2_DECISION_COVERAGE_GATE["id"]:
        raise ValueError(f"refused: decision coverage gate {definition!r} binds R into eligibility -- superseded by the owner's ruling A-10 "
                         "(C >= B only; C >= R is a mandatory diagnostic)")
    if definition not in DECISION_COVERAGE_GATE_DEFINITIONS or DECISION_COVERAGE_GATE_DEFINITIONS[definition]["reads_R"]:
        raise ValueError(f"refused: unknown decision coverage gate definition {definition!r} (only {DECISION_COVERAGE_GATE!r} is bound, A-10)")
    return definition'''),
    ('''def decision_coverage_gate(B, C, truth, docs=None, *, R=None, definition: str = DECISION_COVERAGE_GATE) -> dict:
    """The GATE, as the named definition says (DECISION_COVERAGE_GATE_DEFINITIONS; default the constant in force):
      C_GE_B_ONLY        C >= B (A-09 point 6: R never decides anything; C >= R is a diagnostic contrast) -- review38's gate;
      C_GE_B_AND_C_GE_R  C >= B and C >= R; INCOMPLETE (passes None) when R did not complete its declared population."""
    d = DECISION_COVERAGE_GATE_DEFINITIONS[definition]
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cb, cc = coverage_counts(B, truth, "decision", res), coverage_counts(C, truth, "decision", res)
    out = {"definition": definition, "text": d["text"], "status": d["status"],
           "rule": "completed read or verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE rows are never coverage; "
                   + ("C >= B (C >= R is a diagnostic contrast without credit)" if not d["reads_R"] else "C >= B and C >= R (INCOMPLETE on a truncated R)"),
           "B": cb, "C": cc, "state": "COMPLETE", "passes": cc["coverage"] >= cb["coverage"]}
    if d["reads_R"]:
        if R is None or r_population_state(R, docs) != "COMPLETE":
            out |= {"state": "INCOMPLETE", "passes": None, "R": None if R is None else coverage_counts(R, truth, "decision", res),
                    "why": "R did not complete its declared population (or did not run): the C >= R leg cannot be decided"}
        else:
            cr = coverage_counts(R, truth, "decision", res)
            out |= {"R": cr, "passes": cc["coverage"] >= cb["coverage"] and cc["coverage"] >= cr["coverage"]}
    return out''',
     '''def decision_coverage_gate(B, C, truth, docs=None, *, definition: str = DECISION_COVERAGE_GATE) -> dict:
    """The GATE (owner ruling A-10): C >= B only -- a change from plan v2 (C >= B and C >= R). A definition binding R into
    eligibility is refused (refuse_r_in_eligibility). C >= R is the mandatory diagnostic c_ge_r_diagnostic()."""
    d = DECISION_COVERAGE_GATE_DEFINITIONS[refuse_r_in_eligibility(definition)]
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cb, cc = coverage_counts(B, truth, "decision", res), coverage_counts(C, truth, "decision", res)
    return {"definition": definition, "text": d["text"], "status": d["status"], "change_from_plan_v2": d["change_from_plan_v2"],
            "rule": "completed read or verified absence on scorable rows; a wrong absence, located_incomplete and NOT_SCORABLE rows are never coverage; "
                    "C >= B (C >= R is the mandatory diagnostic, never an eligibility input)",
            "reads_lanes": ["B", "C"], "B": cb, "C": cc, "state": "COMPLETE", "passes": cc["coverage"] >= cb["coverage"]}


_CLASS_REASON = {"completed_read": "covered: completed read", "located_incomplete": "not covered: the decision area was located but not read to completion",
                 "not_attempted": "not covered: no read was attempted", "budget": "not covered: not read under the application's own budget",
                 "missing_page": "not covered: the page was not read (the attempt failed or the page is missing)",
                 "not_scorable": "not scorable"}


def _cov_class(lane, pid, page, kind):
    cls = ((((lane or {}).get("documents") or {}).get(pid) or {}).get("coverage") or {}).get(str(page), {}).get("decision", "not_attempted")
    if cls == "discovery_absent":
        return cls, kind == "absent", ("covered: verified absence" if kind == "absent" else "not covered: wrong absence (the truth has a decision)")
    return cls, cls == "completed_read", _CLASS_REASON.get(cls, f"not covered: {cls}")


def c_ge_r_diagnostic(C, R, truth, docs=None, r_gate=None) -> dict:
    """The MANDATORY C >= R decision-coverage diagnostic (owner ruling A-10): both lanes' counts, the missing coverage per
    document with its reasons, the documents R did not complete; INCOMPLETE when R did not complete its declared population
    (or did not run). It never determines eligibility and earns no credit."""
    res = {pid for pid in truth["documents"] if A.primary(truth, pid, "decision") and (docs is None or pid in docs)}
    cc = coverage_counts(C, truth, "decision", res)
    cr = coverage_counts(R, truth, "decision", res) if R is not None else None
    if R is None:
        state, why = "INCOMPLETE", [r_gate or "lane R did not run in this invocation"]
    else:
        rs = limit_state(R, docs)
        missing_docs = sorted(pid for pid in (docs or []) if pid not in (R.get("documents") or {}))
        why = [f"{pid}: R {v.get('status', 'DEFERRED') if k != 'deferred' else 'DEFERRED'} ({v.get('reason')})"
               for k in ("deferred", "limit_incomplete", "other_incomplete") for pid, v in sorted(rs[k].items())] + \\
              [f"{pid}: not in lane R" for pid in missing_docs]
        state = "INCOMPLETE" if why else "COMPLETE"
    per_doc = {}
    for r in sorted(truth["rows"].values(), key=lambda x: (x["pool_id"], str(x["page"]))):
        if r["field"] != "decision" or r["pool_id"] not in res or r["truth_kind"] == "not_scorable":
            continue
        c_cls, c_ok, c_why = _cov_class(C, r["pool_id"], r["page"], r["truth_kind"])
        if R is not None:
            r_cls, r_ok, r_why = _cov_class(R, r["pool_id"], r["page"], r["truth_kind"])
        else:
            r_cls, r_ok, r_why = None, False, "R did not run"
        if c_ok and r_ok:
            continue
        d = per_doc.setdefault(r["pool_id"], {"pages": {}, "C_status": ((C.get("documents") or {}).get(r["pool_id"]) or {}).get("status", "COMPLETE"),
                                              "R_status": None if R is None else ((R.get("documents") or {}).get(r["pool_id"]) or {}).get("status", "absent")})
        d["pages"][str(r["page"])] = {"C": c_cls, "C_covered": c_ok, "C_reason": c_why, "R": r_cls, "R_covered": r_ok, "R_reason": r_why,
                                      "C_missing_where_R_covered": (not c_ok) and r_ok}
    holds = (cc["coverage"] >= cr["coverage"]) if (state == "COMPLETE" and cr is not None) else None
    return {"mandatory": True, "determines_eligibility": False, "credit": "none", "rule": C_GE_R_DIAGNOSTIC_RULE,
            "change_from_plan_v2": DECISION_COVERAGE_GATE_DEFINITIONS[DECISION_COVERAGE_GATE]["change_from_plan_v2"],
            "state": state, "why_incomplete": why if state != "COMPLETE" else [], "counts": {"C": cc, "R": cr},
            "coverage": {"C": cc["coverage"], "R": None if cr is None else cr["coverage"]}, "holds": holds,
            "missing_coverage": per_doc,
            "C_missing_where_R_covered": sorted(pid for pid, d in per_doc.items() if any(p["C_missing_where_R_covered"] for p in d["pages"].values()))}'''),
    ('''def evaluate(B, C, R, truth, *, caps, extensions_used, seed=BOOTSTRAP_SEED, stop_state=None, docs=None, P=None, r_gate=None,
             gate_definition: str = DECISION_COVERAGE_GATE) -> dict:
    _check_lane(B, "B")
    _check_lane(C, "C")
    if gate_definition not in DECISION_COVERAGE_GATE_DEFINITIONS:
        raise ValueError(f"unknown decision coverage gate definition {gate_definition!r}")''',
     '''def evaluate(B, C, R, truth, *, caps, extensions_used, seed=BOOTSTRAP_SEED, stop_state=None, docs=None, P=None, r_gate=None,
             gate_definition: str = DECISION_COVERAGE_GATE) -> dict:
    _check_lane(B, "B")
    _check_lane(C, "C")
    refuse_r_in_eligibility(gate_definition)                 # owner ruling A-10: R never determines eligibility'''),
    ('''    result["decision_coverage_gate"] = decision_coverage_gate(B, C, truth, docs, R=R, definition=gate_definition)''',
     '''    result["decision_coverage_gate"] = decision_coverage_gate(B, C, truth, docs, definition=gate_definition)
    result["decision_coverage_C_ge_R"] = c_ge_r_diagnostic(C, R, truth, docs, r_gate)       # MANDATORY diagnostic (A-10)'''),
    ('''        dgate = result["decision_coverage_gate"]
        if f == "decision" and dgate["state"] == "COMPLETE" and not dgate["passes"]:
            reasons.append("decision coverage of C below B" + (" or below R" if DECISION_COVERAGE_GATE_DEFINITIONS[gate_definition]["reads_R"] else ""))
        outcome = state or ("NOT ELIGIBLE" if reasons else OUTCOMES[0])
        if f == "decision" and dgate["state"] == "INCOMPLETE" and state is None and not reasons:
            outcome = "INCOMPLETE"
            reasons.append(f"decision coverage gate INCOMPLETE ({dgate.get('why')})")''',
     '''        if f == "decision" and not result["decision_coverage_gate"]["passes"]:
            reasons.append("decision coverage of C below B")
        outcome = state or ("NOT ELIGIBLE" if reasons else OUTCOMES[0])'''),
    ('''    result["candidate"] = cand | {"rule": CANDIDATE_RULE, "decision_coverage_gate": gate_definition,
                                  "reads_lanes": ["B", "C"] + (["R (decision coverage gate leg only)"] if DECISION_COVERAGE_GATE_DEFINITIONS[gate_definition]["reads_R"] else []),''',
     '''    result["candidate"] = cand | {"rule": CANDIDATE_RULE, "decision_coverage_gate": gate_definition, "reads_lanes": ["B", "C"],'''),
    ('''    gid = (result.get("decision_coverage_gate") or {}).get("definition") or DECISION_COVERAGE_GATE
    g = DECISION_COVERAGE_GATE_DEFINITIONS[gid]
    lines.append("## Decision coverage gate (pending owner ruling, Verification 39 C3)")
    lines.append(f"- {g['id']}: {g['text']}. Status: {g['status']}.")
    if gid == DECISION_COVERAGE_GATE:
        lines.append("- This is the current definition (C >= B only; C >= R is a reported diagnostic). It is pending the owner's ruling "
                     "(Verification 39 C3); the alternative C_GE_B_AND_C_GE_R (C >= B and C >= R, INCOMPLETE on a truncated R) is "
                     "implemented and is applied only if the owner so rules and the declaration binds it.")''',
     '''    g = DECISION_COVERAGE_GATE_DEFINITIONS[DECISION_COVERAGE_GATE]
    lines.append("## Decision coverage gate (CHANGED from plan v2; owner ruling A-10)")
    lines.append(f"- Eligibility: {g['id']} -- C >= B only. {g['change_from_plan_v2']}. This is not an unchanged gate. Every other "
                 "safety, accuracy and completeness gate is unchanged.")
    lines.append("## C >= R decision coverage (MANDATORY diagnostic; never an eligibility input; no credit)")
    dg = result.get("decision_coverage_C_ge_R")
    if not dg:
        lines.append("- Every report states: the state (COMPLETE, or INCOMPLETE when R did not complete its declared population, with "
                     "why), the counts of C and R (coverage, completed reads, verified and wrong absences, other classes, scorable pages), "
                     "whether C >= R holds (only when COMPLETE), and for every document with missing coverage in C or R: the page, each "
                     "lane's coverage class, whether it is covered, and the reason.")
    else:
        lines.append(f"- State: {dg['state']}" + (f" ({'; '.join(dg['why_incomplete'])})" if dg["why_incomplete"] else "") +
                     f". Coverage C {dg['coverage']['C']}, R {dg['coverage']['R']}; holds: {dg['holds']}.")
        lines.append(f"- Counts C: {dg['counts']['C']}; counts R: {dg['counts']['R']}.")
        for pid, d in sorted(dg["missing_coverage"].items()):
            for page, p in sorted(d["pages"].items()):
                lines.append(f"- {pid} p{page}: C {p['C']} ({p['C_reason']}); R {p['R']} ({p['R_reason']}); C status {d['C_status']}, "
                             f"R status {d['R_status']}.")'''),
], "preflight_r32.py": [
    ('''  decision_coverage_gate <id>                (R39-15) one of score_bcr_r32.DECISION_COVERAGE_GATE_DEFINITIONS; the
                                             current definition is score_bcr_r32.DECISION_COVERAGE_GATE ('C >= B only'),
                                             pending the owner's ruling (Verification 39 C3); ORCH-08C changes no gate''',
     '''  decision_coverage_gate "C_GE_B_ONLY"       (R39-15, owner ruling A-10) score_bcr_r32.DECISION_COVERAGE_GATE: decision
                                             coverage eligibility is C >= B only -- a CHANGE from plan v2 (C >= B and
                                             C >= R); C >= R is a mandatory diagnostic; a declaration binding R into
                                             eligibility (plan v2's 'C_GE_B_AND_C_GE_R' or any other) is refused'''),
    ('''    if decl["decision_coverage_gate"] not in S.DECISION_COVERAGE_GATE_DEFINITIONS:
        raise Refused(f"refused: decision_coverage_gate must be one of {sorted(S.DECISION_COVERAGE_GATE_DEFINITIONS)} "
                      f"({decl['decision_coverage_gate']!r})")''',
     '''    try:
        S.refuse_r_in_eligibility(decl["decision_coverage_gate"])
    except ValueError as exc:
        raise Refused(f"refused: decision_coverage_gate must be {S.DECISION_COVERAGE_GATE!r} (owner ruling A-10): {exc}") from exc'''),
]}


def main():
    for name, reps in EDITS.items():
        p = H / name
        s = p.read_text(encoding="utf-8")
        for old, new in reps:
            n = s.count(old)
            if n != 1:
                print(f"{name}: ANCHOR NOT UNIQUE ({n}): {old[:140]!r}")
                return 1
            s = s.replace(old, new)
        p.write_text(s, encoding="utf-8", newline="\n")
        print("patched", name, len(reps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
