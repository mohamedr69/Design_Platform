"""Synthetic r32 truth and lanes for the scorer and concentration tests (no real label value is used); temporary live
declarations (ORCH-08C: contract 4 with its PROJECT-REQUEST-BOUNDS.json beside it, the declared sandbox base
C:/t/r2x/r39-sandbox by default) and FAKE ledgers for the refusal tests -- never an authorization file."""
from __future__ import annotations

FIELDS = ("identity", "revision", "decision")


def row(pid, page, field, kind, literal=None, cls=None, reasons=None, resub=False, alternates=(), candidates=()):
    return {"pool_id": pid, "page": str(page), "field": field, "state": {"value": "present", "absent": "absent", "not_scorable": "ambiguous"}[kind],
            "association": "resolved" if kind != "absent" else None, "literal": literal, "class": cls if field == "decision" else None,
            "actor": None, "actor_state": None, "absent_kind": "no_decision_area" if kind == "absent" and field == "decision" else None,
            "location": None, "printed_label": None, "semantic_role": None, "resubmission_required": resub, "excluded_from_scoring": False,
            "review_status": "accepted", "candidates": list(candidates), "doc_resolved_for_scoring": "yes", "doc_carries_fact": "yes",
            "truth_kind": kind, "scorable": kind != "not_scorable", "not_scorable_reasons": list(reasons or ([] if kind != "not_scorable" else ["ambiguous"])),
            "alternates": list(alternates), "alternate_kinds": {}, "count_once_alias_of": None}


def doc(pid, project="p0", contractor=None, layout="L0", stratum="review_signal", decision=True, identity=True, revision=True,
        decision_resolved=True, alias_of=None, dtype=None):
    has = {"identity": identity, "revision": revision, "decision": decision}
    fields = {f: {"resolved_for_scoring": "yes" if (f != "decision" or decision_resolved) else "no",
                  "carries_fact": "yes" if has[f] else "no", "primary": f != "decision" or decision_resolved,
                  "has_fact": has[f] and (f != "decision" or decision_resolved)} for f in FIELDS}
    return {"pool_id": pid, "canonical_id": alias_of or pid, "is_alias": alias_of is not None, "alias_kind": None, "ep": project,
            "project": project, "contractor": contractor or f"contractor-{project}", "doc_key": f"{project}/{pid}.pdf", "relative_path": f"{pid}.pdf",
            "staged_sha256": pid * 4, "stratum": stratum, "how": stratum, "selection_order": 1, "in_scope_pages": 1, "page_count": 1,
            "labelled_pages": ["1"], "compilation": False, "layout_key": layout, "layout_rule": "test", "kind": "test", "independent_review": True,
            "fields": fields, "decision_type": dtype or ("approved" if decision else "none"),
            "decision_control": "positive" if decision and decision_resolved else ("negative" if decision_resolved else "none")}


def truth(n=16, projects=4, layouts=None, negatives=0, contractors=None):
    docs, rows = {}, {}
    for i in range(n):
        pid = f"D{i:02d}"
        p = f"p{i % projects}"
        lay = layouts[i] if layouts else f"L{i % projects}"
        docs[pid] = doc(pid, project=p, layout=lay, contractor=(contractors[i] if contractors else None))
        rows[f"{pid}|1|identity"] = row(pid, 1, "identity", "value", f"ID-{i}")
        rows[f"{pid}|1|revision"] = row(pid, 1, "revision", "value", "01")
        rows[f"{pid}|1|decision"] = row(pid, 1, "decision", "value", "APPROVED", cls="approved")
    for j in range(negatives):
        pid = f"N{j:02d}"
        docs[pid] = doc(pid, project=f"p{j % projects}", layout="LN", decision=False, revision=False, stratum="drawing_signal")
        rows[f"{pid}|1|identity"] = row(pid, 1, "identity", "value", f"NID-{j}")
        rows[f"{pid}|1|revision"] = row(pid, 1, "revision", "absent")
        rows[f"{pid}|1|decision"] = row(pid, 1, "decision", "absent")
    return {"schema": "r32-truth-1", "aliases": {}, "compilations": [], "documents": docs, "rows": rows}


def facts_for(T, pid, *, correct=(), wrong=(), state="accepted"):
    out = []
    for f in FIELDS:
        r = T["rows"].get(f"{pid}|1|{f}")
        if f in correct and r and r["truth_kind"] == "value":
            out.append({"page": "1", "field": f, "value": r["literal"] if f != "decision" else "approved", "state": state})
        if f in wrong:
            out.append({"page": "1", "field": f, "value": "WRONG-1" if f != "decision" else "rejected", "state": state})
    return out


def lane(name, T, *, correct=None, wrong=None, extra_facts=None, requests=0, inherited=0, cov=None, attempted=None):
    """correct / wrong: {pid: set(fields)}; every truth document is in the lane (attempted unless attempted excludes it)."""
    docs = {}
    for pid in T["documents"]:
        fs = facts_for(T, pid, correct=(correct or {}).get(pid, ()), wrong=(wrong or {}).get(pid, ()))
        fs += (extra_facts or {}).get(pid, [])
        docs[pid] = {"attempted": attempted is None or pid in attempted, "unsupported": False, "facts": fs,
                     "coverage": {"1": (cov or {}).get(pid, {"decision": "completed_read"})}}
    return {"lane": name, "documents": docs, "requests": {"own_dispatched": requests, "inherited_from_b": inherited}}


def all_fields(T, ids=None):
    return {pid: set(FIELDS) for pid in T["documents"] if ids is None or pid in ids}


# ---- ORCH-05C (RC-3 / RC-4 / RC-5): temporary live declarations and FAKE ledgers for refusal tests ---------------------------
# Only files under pytest's tmp_path are written: a declaration (never an authorization) and a fake ledger with the
# application's ledger schema (never the real AI ledger, never a scope in it).
TEST_TOKEN = "test-owner-token-not-real"
TEST_SCOPE = "r38-test-scope"
TEST_PARENT = {"total": 556, "input_tokens": 16300000, "output_tokens": 3260000, "elapsed_s": 604800}
TEST_LIMITS = {"requests": 556, "input_tokens": 16300000, "output_tokens": 3260000, "elapsed_s": 604800}
TEST_WINDOW = {"limit": 60, "window_s": 86400}
DEFAULT_SANDBOX_BASE = "C:/t/r2x/r39-sandbox"
LIVE_SWITCHES = {
    "B": {"AI_EVIDENCE_VARIANT": "off"},
    "C": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1", "AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1",
          "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"},
    "R": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1"},
    "P": {},
}


def fake_ledger(path, scopes=None):
    """A fake ledger file with the application's ledger tables; scopes: {name: (limits dict, breaker or None, n entries)}."""
    import json
    import sqlite3

    con = sqlite3.connect(str(path))
    con.executescript("""create table scopes (scope text primary key, limits text, created_at real, breaker text, limits_version integer default 1);
        create table entries (id integer primary key autoincrement, scope text, at real, task text, adapter text, model text, state text,
          est_in integer, est_out integer, act_in integer, act_out integer, cached_in integer, turns integer, latency_ms integer,
          outcome text, usage_unknown integer default 0, pid integer, note text);
        create table limit_amendments (id integer primary key autoincrement, scope text, at real, version integer, old text, new text,
          authorized_by text, reason text, pid integer);""")
    for name, (limits, breaker, n) in (scopes or {}).items():
        con.execute("insert into scopes (scope, limits, created_at, breaker) values (?, ?, 0, ?)", (name, json.dumps(limits, sort_keys=True), breaker))
        for _ in range(n):
            con.execute("insert into entries (scope, state) values (?, 'settled')", (name,))
    con.commit()
    con.close()
    return path


_BOUNDS = {}


def bounds_for(run_set_path=None, window=None, elapsed_s=None):
    """PROJECT-REQUEST-BOUNDS content for a run-set file (default: the frozen review34 RUN-SET-PROPOSAL.json)."""
    import pathlib

    import preflight_r32 as PF
    import project_bounds_r32 as PB

    rs = str(run_set_path or "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json")
    w = dict(window or TEST_WINDOW)
    el = int(elapsed_s or TEST_PARENT["elapsed_s"])
    key = (rs, pathlib.Path(rs).read_bytes(), w["limit"], w["window_s"], el)
    if key not in _BOUNDS:
        if "truth" not in _BOUNDS:
            _BOUNDS["truth"] = PF.build_truth()
        T = _BOUNDS["truth"]
        _BOUNDS[key] = PB.compute(PF.load_run_set(rs, T), T, LIVE_SWITCHES, window_limit=w["limit"], window_s=w["window_s"], elapsed_s=el)
    return _BOUNDS[key]


def live_declaration(folder, *, binding_sha, run_set_sha, stamp, ledger_path, sandbox_base=DEFAULT_SANDBOX_BASE, run_set_path=None, **over):
    """A temporary live declaration (NOT an authorization) that satisfies preflight_r32.validate_declaration (contract 4),
    with its PROJECT-REQUEST-BOUNDS.json written beside it (computed for run_set_path, default the frozen proposal)."""
    import hashlib
    import json
    import pathlib

    import preflight_r32 as PF

    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / "DECLARATION.json"
    bounds = bounds_for(run_set_path)
    bp = folder / "PROJECT-REQUEST-BOUNDS.json"
    bp.write_text(json.dumps(bounds, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    cli = "C:/r38-test/no-such-cli/claude.exe"
    env = {"AI_PROVIDER": "claude-code", "AI_MODEL_STANDARD": "claude-opus-5", "AI_MODEL_SMALL": "claude-sonnet-5", "AI_EFFORT": "high",
           "AI_TIMEOUT_S": "60", "AI_CLI_TIMEOUT_S": "300", "AI_CLAUDE_CLI": cli,
           "AI_LEDGER_PATH": pathlib.Path(ledger_path).as_posix(), "AI_LEDGER_SCOPE": TEST_SCOPE, "AI_LEDGER_LIMITS": json.dumps(TEST_LIMITS, sort_keys=True),
           "AI_MAX_CALLS_PER_PROJECT_PER_DAY": "120", "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": "600", "AI_MAX_CALLS_PER_DOCUMENT": "12",
           "AI_MAX_ELAPSED_S_PER_JOB": "120"}
    rec = {"name": "r39 test declaration (not an ORCH-09 declaration)", "contract": "r39-live-contract-4",
           "binding_manifest_sha256": binding_sha, "run_set_sha256": run_set_sha,
           "run": {"stamp": stamp, "sandbox_base": sandbox_base, "folder": f"{sandbox_base}/{stamp}"},
           "authorization": {"path": (folder / "OWNER-DISPATCH-AUTHORIZATION.json").as_posix(),
                             "owner_token_sha256": hashlib.sha256(TEST_TOKEN.encode()).hexdigest()},
           "budget": {"parent": dict(TEST_PARENT), "lane_allowances": {"B": 240, "C": 240, "R": 40, "P": 36}},
           "project_window": dict(TEST_WINDOW),
           "project_request_bounds": {"path": bp.as_posix(), "sha256": hashlib.sha256(bp.read_bytes()).hexdigest()},
           "lane_switches": LIVE_SWITCHES, "provider_env": env,
           "model_identity": {"provider": "claude-code", "models": {"small": "claude-sonnet-5", "standard": "claude-opus-5"},
                              "cli": {"path": cli, "version": None}},
           "ledger": {"path": pathlib.Path(ledger_path).as_posix(), "scope": TEST_SCOPE, "limits": TEST_LIMITS, "wrap_provider": True},
           "application_env": {"DRAWINGS_AI_REVIEW_ENABLED": "false"}, "lane_task_kinds": PF.task_kinds_for(LIVE_SWITCHES),
           "resume_policy": "full", "decision_coverage_gate": "C_GE_B_ONLY"}
    for k, v in over.items():
        if v is None:
            rec.pop(k, None)
        else:
            rec[k] = v
    p.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest(), rec
